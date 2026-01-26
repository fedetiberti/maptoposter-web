# API Documentation

Base URL: `https://your-backend-url.com/api`

## Endpoints

### GET /themes

Get all available themes with their colors.

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

---

### GET /presets

Get available dimension presets.

**Response:**
```json
{
  "presets": [
    {
      "id": "poster",
      "name": "Standard Poster",
      "width": 12,
      "height": 16,
      "description": "3600 x 4800 px at 300 DPI"
    }
  ]
}
```

---

### POST /generate

Submit a poster generation job.

**Request Body:**
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

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `city` | string | Yes | City name |
| `country` | string | Yes | Country name |
| `theme` | string | No | Theme ID (default: "feature_based") |
| `preview` | boolean | No | Generate low-res preview (default: false) |
| `options.distance` | integer | No | Map radius in meters (4000-30000, default: 15000) |
| `options.width` | float | No | Image width in inches (3-20, default: 12) |
| `options.height` | float | No | Image height in inches (3-24, default: 16) |
| `options.format` | string | No | Output format: "png", "svg", "pdf" (default: "png") |
| `options.city_label` | string | No | Override city text on poster |
| `options.country_label` | string | No | Override country text on poster |

**Response:**
```json
{
  "job_id": "abc12345",
  "status": "pending",
  "estimated_wait": 30
}
```

**Errors:**
- `400 Bad Request`: Invalid theme or parameters
- `429 Too Many Requests`: Rate limit exceeded

---

### GET /job/{job_id}

Check the status of a generation job.

**Response (pending/processing):**
```json
{
  "job_id": "abc12345",
  "status": "processing",
  "progress": 50
}
```

**Response (complete):**
```json
{
  "job_id": "abc12345",
  "status": "complete",
  "progress": 100,
  "download_url": "/api/download/abc12345",
  "expires_at": "2024-01-26T13:00:00Z"
}
```

**Response (error):**
```json
{
  "job_id": "abc12345",
  "status": "error",
  "progress": 0,
  "error": "Could not find coordinates for 'Unknown City, Country'"
}
```

| Status | Description |
|--------|-------------|
| `pending` | Job queued, not yet started |
| `processing` | Job running, check `progress` for completion % |
| `complete` | Job finished, use `download_url` to get file |
| `error` | Job failed, check `error` message |

**Progress stages:**
- 0-20%: Looking up coordinates
- 20-50%: Fetching street network
- 50-70%: Fetching water/parks features
- 70-90%: Rendering map
- 90-100%: Saving file

---

### GET /download/{job_id}

Download a completed poster file.

**Response:** Binary file

| Format | Content-Type |
|--------|--------------|
| PNG | `image/png` |
| SVG | `image/svg+xml` |
| PDF | `application/pdf` |

**Errors:**
- `404 Not Found`: Job not found or file expired
- `400 Bad Request`: Job not complete

---

## Rate Limiting

The API enforces rate limiting to prevent abuse:
- **Default**: 10 requests per minute per IP address
- **Response when exceeded**: `429 Too Many Requests`

```json
{
  "error": "Rate limit exceeded",
  "detail": "10 per 1 minute"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `400`: Bad request (invalid parameters)
- `404`: Resource not found
- `429`: Rate limit exceeded
- `500`: Internal server error

---

## Examples

### Generate a preview

```bash
curl -X POST https://api.example.com/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "city": "Paris",
    "country": "France",
    "theme": "noir",
    "preview": true
  }'
```

### Poll for completion

```bash
curl https://api.example.com/api/job/abc12345
```

### Download the result

```bash
curl -o paris_noir.png https://api.example.com/api/download/abc12345
```

### Full flow in JavaScript

```javascript
async function generatePoster(city, country, theme) {
  // 1. Submit job
  const submitResponse = await fetch('/api/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ city, country, theme, preview: false })
  });
  const { job_id } = await submitResponse.json();

  // 2. Poll for completion
  while (true) {
    const statusResponse = await fetch(`/api/job/${job_id}`);
    const status = await statusResponse.json();

    if (status.status === 'complete') {
      // 3. Download
      window.location.href = `/api/download/${job_id}`;
      break;
    } else if (status.status === 'error') {
      throw new Error(status.error);
    }

    await new Promise(r => setTimeout(r, 2000));
  }
}
```
