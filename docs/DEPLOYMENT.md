# Deployment Guide

This guide covers deploying MapToPoster Web using free-tier services.

## Option 1: Vercel + Render (Recommended Free Option)

### Frontend on Vercel

1. **Create a Vercel account** at [vercel.com](https://vercel.com)

2. **Connect your GitHub repository**
   - Click "New Project"
   - Import your repository

3. **Configure the project**
   - **Root Directory**: `frontend`
   - **Framework Preset**: Vite
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

4. **Set environment variables**
   - `VITE_API_URL`: Your Render backend URL (e.g., `https://maptoposter-api.onrender.com`)

5. **Deploy**
   - Click "Deploy"
   - Vercel will build and deploy automatically on every push

### Backend on Render

1. **Create a Render account** at [render.com](https://render.com)

2. **Create a new Web Service**
   - Click "New" → "Web Service"
   - Connect your repository

3. **Configure the service**
   - **Name**: `maptoposter-api`
   - **Root Directory**: `backend`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. **Set environment variables**
   ```
   CORS_ORIGINS=https://your-app.vercel.app
   MAX_WORKERS=2
   JOB_EXPIRY_HOURS=1
   CACHE_DIR=/tmp/maptoposter-cache
   OUTPUT_DIR=/tmp/maptoposter-output
   ```

5. **Deploy**
   - Click "Create Web Service"
   - Wait for the first deploy to complete

### Important Notes

- **Free tier limitations**: Render free tier spins down after 15 minutes of inactivity, causing 30-50 second cold starts
- **Memory**: Free tier has 512MB RAM, which is sufficient for most cities
- **Update frontend**: After getting your Render URL, update the `VITE_API_URL` in Vercel

---

## Option 2: Docker on VPS

For better performance and no cold starts, deploy on a VPS.

### Providers
- **DigitalOcean**: $6/month droplet
- **Linode**: $5/month nanode
- **Vultr**: $6/month

### Setup

1. **Create a VPS** with Ubuntu 22.04

2. **Install Docker and Docker Compose**
   ```bash
   # Update system
   sudo apt update && sudo apt upgrade -y

   # Install Docker
   curl -fsSL https://get.docker.com | sh
   sudo usermod -aG docker $USER

   # Install Docker Compose
   sudo apt install docker-compose-plugin
   ```

3. **Clone and deploy**
   ```bash
   git clone <your-repo-url>
   cd maptoposter-web

   # Build and start
   docker compose up -d --build
   ```

4. **Configure Nginx (optional, for custom domain)**
   ```bash
   sudo apt install nginx certbot python3-certbot-nginx

   # Create Nginx config
   sudo nano /etc/nginx/sites-available/maptoposter
   ```

   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       location / {
           proxy_pass http://localhost:3000;
           proxy_http_version 1.1;
           proxy_set_header Upgrade $http_upgrade;
           proxy_set_header Connection 'upgrade';
           proxy_set_header Host $host;
           proxy_cache_bypass $http_upgrade;
       }
   }
   ```

   ```bash
   # Enable and get SSL
   sudo ln -s /etc/nginx/sites-available/maptoposter /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   sudo certbot --nginx -d yourdomain.com
   ```

---

## Environment Configuration

### Production Environment Variables

Create a `.env` file for production:

```env
# Backend
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
MAX_WORKERS=2
JOB_EXPIRY_HOURS=1
CACHE_DIR=/tmp/maptoposter-cache
OUTPUT_DIR=/tmp/maptoposter-output

# Frontend (build-time)
VITE_API_URL=https://api.yourdomain.com
```

### docker-compose.prod.yml

For production with Traefik:

```yaml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
    environment:
      - CORS_ORIGINS=${CORS_ORIGINS}
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.yourdomain.com`)"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"

  frontend:
    build:
      context: ./frontend
      args:
        - VITE_API_URL=https://api.yourdomain.com
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.web.rule=Host(`yourdomain.com`)"
      - "traefik.http.routers.web.tls.certresolver=letsencrypt"

  traefik:
    image: traefik:v2.10
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=you@email.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - letsencrypt:/letsencrypt

volumes:
  letsencrypt:
```

---

## Monitoring

### Health Checks

The backend exposes health endpoints:
- `GET /` - Basic health check
- `GET /health` - Detailed health status

### Logs

```bash
# Docker Compose
docker compose logs -f backend
docker compose logs -f frontend

# Render
# Use the Render dashboard logs tab
```

---

## Troubleshooting

### Cold Start Issues (Render)

If users experience long waits:
1. Consider upgrading to a paid Render plan
2. Set up an external ping service (e.g., UptimeRobot) to keep the service warm
3. Add a loading indicator explaining the first request may take longer

### Memory Issues

If poster generation fails for large cities:
1. Reduce the `distance` parameter
2. Increase server memory (upgrade plan)
3. Add swap space on VPS:
   ```bash
   sudo fallocate -l 2G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

### CORS Errors

Ensure `CORS_ORIGINS` includes your frontend URL exactly as accessed:
- Include both `https://` and `http://` if needed
- Include both `www` and non-`www` versions
- No trailing slashes
