# MapToPoster Web

A web application for creating beautiful, minimalist map posters on demand.

![MapToPoster Web](https://raw.githubusercontent.com/fedetiberti/maptoposter/main/posters/tokyo_japanese_ink_20260118_142446.png)

## Features

- Generate map posters for any city in the world
- 17 beautiful themes to choose from
- Low-resolution preview before full generation
- Multiple output formats: PNG, SVG, PDF
- Customizable dimensions and zoom level
- Clean, minimal interface

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <your-repo-url>
cd maptoposter-web

# Start both services
docker-compose up --build

# Access the app at http://localhost:3000
```

### Local Development

**Backend:**
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Access at http://localhost:5173
```

## Project Structure

```
maptoposter-web/
├── SPEC.md                 # Technical specification
├── README.md               # This file
├── docker-compose.yml      # Docker Compose configuration
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py             # FastAPI entry point
│   ├── api/                # API routes and schemas
│   ├── core/               # Business logic
│   ├── themes/             # Theme JSON files
│   └── fonts/              # Roboto fonts
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── src/
│   │   ├── App.tsx         # Main application
│   │   ├── api/            # API client
│   │   ├── components/     # React components
│   │   └── hooks/          # Custom hooks
│   └── public/
│
└── docs/
    ├── DEPLOYMENT.md       # Deployment guide
    └── API.md              # API documentation
```

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detailed deployment instructions for:
- Vercel (frontend) + Render (backend)
- Docker on VPS

## API Documentation

See [docs/API.md](docs/API.md) for API endpoint documentation.

## Environment Variables

### Backend
| Variable | Description | Default |
|----------|-------------|---------|
| `CORS_ORIGINS` | Allowed CORS origins | `http://localhost:5173` |
| `MAX_WORKERS` | Thread pool size | `2` |
| `JOB_EXPIRY_HOURS` | Hours before job cleanup | `1` |
| `CACHE_DIR` | OSM data cache directory | `/tmp/maptoposter-cache` |
| `OUTPUT_DIR` | Generated poster directory | `/tmp/maptoposter-output` |

### Frontend
| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API URL | (empty, uses proxy) |

## Credits

- Map data from [OpenStreetMap](https://www.openstreetmap.org/)
- Street network processing by [OSMnx](https://github.com/gboeing/osmnx)
- Original CLI tool: [maptoposter](https://github.com/fedetiberti/maptoposter)

## License

MIT License - see LICENSE file
