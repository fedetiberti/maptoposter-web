# MapToPoster Web App - Technical Specification

## Overview

A web application that allows users to generate minimalist map posters on-demand, powered by the [maptoposter](https://github.com/fedetiberti/maptoposter) Python library.

## Tech Stack

| Component | Technology | Deployment |
|-----------|------------|------------|
| Frontend | React (Vite) | Vercel (free tier) |
| Backend | FastAPI (Python) | Render (free tier) |
| Job Queue | In-memory with polling | - |
| Storage | Temporary file storage | Render disk |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Vercel)                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    React Application                      │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │  │
│  │  │ City Input  │  │Theme Picker │  │ Advanced Options│  │  │
│  │  │  (Search)   │  │  (Swatches) │  │    (Toggle)     │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │              Preview & Download Panel               │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ HTTPS API
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         BACKEND (Render)                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    FastAPI Application                    │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │  │
│  │  │  /themes    │  │  /generate  │  │  /job/{id}      │  │  │
│  │  │  (GET)      │  │  (POST)     │  │  (GET/status)   │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐ │  │
│  │  │           Background Job Processor                  │ │  │
│  │  │  (ThreadPoolExecutor for map generation)            │ │  │
│  │  └─────────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  maptoposter library (OSMnx, matplotlib, geopy)          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## User Flow

```
1. User enters city + country
           │
           ▼
2. User selects theme (color swatches)
           │
           ▼
3. [Optional] User expands "Advanced Options"
   - Distance/zoom (slider)
   - Dimensions (presets or custom)
   - Custom city/country labels
           │
           ▼
4. User clicks "Preview"
           │
           ▼
5. Backend generates low-res preview
   (smaller dimensions, lower DPI)
           │
           ▼
6. User sees preview, can adjust settings
           │
           ▼
7. User clicks "Download" + selects format (PNG/SVG/PDF)
           │
           ▼
8. Backend generates full-resolution poster
           │
           ▼
9. User downloads file
```

## API Endpoints

### GET /api/themes
Returns list of available themes with metadata.

**Response:**
```json
{
  "themes": [
    {
      "id": "noir",
      "name": "Noir",
      "description": "Pure black background, white roads",
      "colors": {
        "bg": "#000000",
        "text": "#FFFFFF",
        "road_primary": "#FFFFFF",
        "water": "#1A1A1A",
        "parks": "#0A0A0A"
      }
    }
  ]
}
```

### POST /api/generate
Submit a poster generation job.

**Request:**
```json
{
  "city": "Tokyo",
  "country": "Japan",
  "theme": "japanese_ink",
  "preview": true,
  "options": {
    "distance": 15000,
    "width": 12,
    "height": 16,
    "format": "png",
    "city_label": null,
    "country_label": null
  }
}
```

**Response:**
```json
{
  "job_id": "abc123",
  "status": "pending",
  "estimated_wait": 30
}
```

### GET /api/job/{job_id}
Check job status and get download URL.

**Response (pending):**
```json
{
  "job_id": "abc123",
  "status": "processing",
  "progress": 50
}
```

**Response (complete):**
```json
{
  "job_id": "abc123",
  "status": "complete",
  "download_url": "/api/download/abc123",
  "expires_at": "2024-01-26T12:00:00Z"
}
```

**Response (error):**
```json
{
  "job_id": "abc123",
  "status": "error",
  "error": "Could not find coordinates for 'Unknown City, Country'"
}
```

### GET /api/download/{job_id}
Download the generated poster file.

**Response:** Binary file (image/png, image/svg+xml, or application/pdf)

## Frontend Components

### 1. LocationInput
- Text input for city name
- Text input for country name
- Optional: autocomplete using geocoding API

### 2. ThemePicker
- Grid of clickable theme swatches
- Each swatch shows background color + primary road color
- Selected state with border highlight
- Theme name on hover/below

### 3. AdvancedOptions (collapsible)
- **Distance slider**: 4,000m - 30,000m (with recommended presets)
- **Dimensions dropdown**:
  - Instagram Post (1080×1080)
  - Mobile Wallpaper (1080×1920)
  - A4 Print (2480×3508)
  - Custom (width/height inputs)
- **Custom labels**: Override city/country text on poster

### 4. PreviewPanel
- Shows loading spinner during generation
- Displays low-res preview image
- "Regenerate Preview" button
- Format selector (PNG/SVG/PDF)
- "Download Full Resolution" button

### 5. ProgressIndicator
- Polling-based status updates
- Progress bar or spinner
- Estimated time remaining (optional)

## Backend Implementation

### Job Management
```python
# In-memory job store (sufficient for free tier)
jobs: Dict[str, Job] = {}

class Job:
    id: str
    status: Literal["pending", "processing", "complete", "error"]
    progress: int  # 0-100
    result_path: Optional[str]
    error: Optional[str]
    created_at: datetime
    expires_at: datetime
```

### Background Processing
- Use `ThreadPoolExecutor` with max 2 workers (Render free tier has limited CPU)
- Preview generation: 3.6×4.8 inches at 72 DPI (~260×346px)
- Full resolution: User-selected dimensions at 300 DPI

### File Cleanup
- Generated files expire after 1 hour
- Background task cleans up expired files every 15 minutes

### Rate Limiting
- Basic rate limiting: 10 requests per minute per IP
- Nominatim compliance: 1 geocoding request per second (already in maptoposter)

## Project Structure

```
maptoposter-web/
├── SPEC.md                 # This file
├── README.md               # Setup and usage instructions
├── docker-compose.yml      # Local development
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py             # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py       # API endpoints
│   │   └── schemas.py      # Pydantic models
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py       # Settings
│   │   ├── jobs.py         # Job management
│   │   └── generator.py    # Poster generation wrapper
│   ├── themes/             # Theme JSON files (copied from original repo)
│   └── fonts/              # Roboto fonts (copied from original repo)
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── index.html
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/
│   │   │   └── client.ts   # API client
│   │   ├── components/
│   │   │   ├── LocationInput.tsx
│   │   │   ├── ThemePicker.tsx
│   │   │   ├── AdvancedOptions.tsx
│   │   │   ├── PreviewPanel.tsx
│   │   │   └── ProgressIndicator.tsx
│   │   ├── hooks/
│   │   │   └── useJob.ts   # Polling hook
│   │   └── styles/
│   │       └── index.css
│   └── public/
│       └── favicon.ico
│
└── docs/
    ├── DEPLOYMENT.md       # Vercel + Render setup guide
    └── API.md              # API documentation
```

## Configuration

### Backend Environment Variables
```env
# Required
CORS_ORIGINS=https://your-app.vercel.app

# Optional
MAX_WORKERS=2
JOB_EXPIRY_HOURS=1
RATE_LIMIT_PER_MINUTE=10
CACHE_DIR=/tmp/maptoposter-cache
OUTPUT_DIR=/tmp/maptoposter-output
```

### Frontend Environment Variables
```env
VITE_API_URL=https://your-backend.onrender.com
```

## Deployment

### Frontend (Vercel)
1. Connect GitHub repo to Vercel
2. Set root directory to `frontend/`
3. Build command: `npm run build`
4. Output directory: `dist`
5. Set `VITE_API_URL` environment variable

### Backend (Render)
1. Create new Web Service from GitHub repo
2. Set root directory to `backend/`
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Set environment variables
6. Note: Free tier sleeps after 15 min inactivity (cold starts ~30-50s)

## Performance Considerations

### Preview Generation
- Use smaller dimensions: 3.6×4.8 inches
- Use lower DPI: 72 instead of 300
- Result: ~5-15 second generation vs 30-60 seconds for full res

### Caching
- Cache geocoding results (already in maptoposter)
- Cache OSM data by coordinates (already in maptoposter)
- Consider Redis for production scale (future enhancement)

### Render Free Tier Limits
- 512 MB RAM
- 0.1 CPU (shared)
- Sleeps after 15 minutes of inactivity
- 750 hours/month free

## Future Enhancements (Out of Scope for MVP)

1. **User accounts** - Save generation history
2. **Custom themes** - Let users create their own color schemes
3. **Batch generation** - Generate multiple themes at once
4. **Email delivery** - Send poster to email
5. **Payment integration** - Premium features, higher resolution
6. **CDN for downloads** - Faster global delivery
7. **WebSocket progress** - Real-time generation updates
8. **Map preview before generation** - Show approximate area coverage

## Development Workflow

### Local Development
```bash
# Start both services
docker-compose up

# Or run separately:
# Backend
cd backend && uvicorn main:app --reload

# Frontend
cd frontend && npm run dev
```

### Testing
```bash
# Backend tests
cd backend && pytest

# Frontend tests
cd frontend && npm test
```

## Open Questions / Decisions Made

| Question | Decision |
|----------|----------|
| User authentication? | No - anonymous usage |
| How to deliver files? | Direct download |
| Real-time updates? | Polling (simpler than WebSocket) |
| Theme selection UI? | Color swatches |
| Advanced options? | Hidden by default, toggle to show |
| Output formats? | PNG, SVG, PDF (all supported) |
| Deployment? | Vercel (frontend) + Render (backend) |
