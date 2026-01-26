# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/claude-code) when working with this repository.

## Project Overview

MapToPoster Web is a web application that generates minimalist map posters on demand. It wraps the original [maptoposter](https://github.com/fedetiberti/maptoposter) Python CLI tool with a FastAPI backend and React frontend.

Users can:
- Enter a city and country
- Select from 17 color themes
- Choose dimensions (presets or custom)
- Generate low-res previews before full renders
- Download in PNG, SVG, or PDF format

## Architecture

```
maptoposter/
├── backend/           # FastAPI Python backend
│   ├── api/          # Routes and schemas
│   ├── core/         # Config, jobs, generator
│   ├── fonts/        # Roboto font files
│   ├── themes/       # JSON theme definitions
│   └── main.py       # Entry point
├── frontend/         # React + Vite + TypeScript
│   ├── src/
│   │   ├── components/   # UI components
│   │   ├── hooks/        # useJob polling hook
│   │   ├── services/     # API client
│   │   └── styles/       # CSS
│   └── index.html
└── docker-compose.yml
```

## Common Commands

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Note: Do NOT use `--reload` flag as WatchFiles monitors the venv directory and causes infinite reloads.

### Frontend

```bash
cd frontend
npm install
npm run dev          # Development server on port 5173
npm run build        # Production build to dist/
npm run preview      # Preview production build
```

### Docker

```bash
docker-compose up --build    # Run both services
```

## Key Technical Details

### SSL Certificate Handling (Development)

The backend includes SSL certificate bypass for development environments with corporate proxies that intercept HTTPS with self-signed certificates. This is implemented in `backend/core/generator.py`:

- Monkey-patches `requests.Session.request` to set `verify=False`
- Configures OSMnx with `ox.settings.requests_kwargs = {"verify": False}`
- Uses custom `ssl_context` for geopy Nominatim

**Important:** These bypasses should be removed or made conditional for production deployment.

### Job Processing

- Jobs run in a `ThreadPoolExecutor` (background threads)
- In-memory job store with 1-hour expiration
- Frontend polls `/api/job/{id}` every 2 seconds for status updates
- Progress reported in 10% increments during generation

### API Endpoints

- `GET /api/themes` - List available themes with colors
- `GET /api/presets` - List dimension presets
- `POST /api/generate` - Submit generation job (returns job_id)
- `GET /api/job/{id}` - Check job status and progress
- `GET /api/download/{id}` - Download completed poster

### Theme Structure

Themes are JSON files in `backend/themes/`. Each theme defines:
- `name`, `description`
- `bg` (background), `text`, `gradient_color`
- `water`, `parks`
- `road_motorway`, `road_primary`, `road_secondary`, `road_tertiary`, `road_residential`, `road_default`

### Preview vs Full Generation

- Preview: 3.6" x 4.8" at 72 DPI (fast, ~15s)
- Full: User-specified dimensions at 300 DPI (~45s)

## Deployment

Designed for:
- **Frontend:** Vercel (static hosting)
- **Backend:** Render (free tier Docker container)

Update `frontend/src/services/api.ts` with the production backend URL before deploying.

## Dependencies

### Backend (Python 3.12+)
- FastAPI, uvicorn
- OSMnx (OpenStreetMap data)
- matplotlib (rendering)
- geopy (geocoding)
- shapely, numpy

### Frontend
- React 18
- TypeScript
- Vite

## Common Issues

1. **Port 8000 in use:** Kill existing process with `lsof -ti:8000 | xargs kill -9`
2. **Python 3.14 compatibility:** Use Python 3.12 (pydantic-core build issues with 3.14)
3. **Theme swatches not visible:** Check CSS has explicit dimensions on `.theme-swatch`
4. **SSL errors:** Corporate proxy may require the SSL bypass code in generator.py
