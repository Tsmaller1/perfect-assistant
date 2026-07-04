# 🐳 Docker Setup Guide - Phase 5

## Quick Start

### Prerequisites
- Docker & Docker Compose installed
- Environment variables configured

### Local Development Setup

1. **Build and run with docker-compose:**
```bash
cd pine-sales-ai
docker-compose up --build
```

2. **Access services:**
   - Backend: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - PostgreSQL: localhost:5432

3. **Run tests in container:**
```bash
docker-compose exec backend pytest tests/ -v
```

4. **Stop services:**
```bash
docker-compose down
```

---

## Production Deployment

### Build Image for Production

```bash
cd backend
docker build -t pine-sales-ai-backend:latest .
docker tag pine-sales-ai-backend:latest <your-registry>/pine-sales-ai-backend:latest
docker push <your-registry>/pine-sales-ai-backend:latest
```

### Run Container with Supabase

```bash
docker run -d \
  --name pine-sales-ai \
  -p 8000:8000 \
  -e DATABASE_URL="postgresql+asyncpg://postgres:PASSWORD@HOST:5432/postgres" \
  -e ENV=production \
  pine-sales-ai-backend:latest
```

---

## Multi-Stage Dockerfile Details

The Dockerfile uses a **two-stage build** for optimized image size:

1. **Builder Stage**: Compiles dependencies
2. **Runtime Stage**: Lean production image with only runtime dependencies

### Key Features
- ✅ Security: Non-root user (appuser)
- ✅ Health checks: Automated container monitoring
- ✅ Optimization: Multi-stage build reduces image size
- ✅ Dependencies: libpq for PostgreSQL, asyncpg driver

---

## Docker Compose Services

### Backend Service
- Port: 8000
- Health check: /health endpoint
- Auto-reload: Enabled for development
- Volume: Local code mounted for live editing

### PostgreSQL Service (Local Dev)
- Port: 5432
- Auto-initialization: SQL migrations run on startup
- Health check: pg_isready command
- Data persistence: postgres_data volume

---

## Environment Variables

Copy `.env.example` to `.env` and update:

```bash
# Local development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/pine_sales_ai

# Production (Supabase)
DATABASE_URL=postgresql+asyncpg://postgres:PASSWORD@PROJECT.supabase.co:5432/postgres
```

---

## Troubleshooting

### Container exits immediately
```bash
docker-compose logs backend
```

### PostgreSQL connection refused
- Ensure `depends_on` service is healthy
- Check port 5432 is available
- Verify password matches POSTGRES_PASSWORD env var

### Port already in use
```bash
# Change in docker-compose.yml
ports:
  - "8001:8000"  # Map to different host port
```

### Clean rebuild
```bash
docker-compose down -v
docker-compose up --build
```

---

## Next Steps: Phase 6 (CI/CD Pipeline)

Once Phase 5 is complete:
1. Push to container registry (Docker Hub, ACR, ECR)
2. Set up GitHub Actions for automated builds
3. Add deployment pipeline

See PHASE_5_CHECKLIST.md for detailed tasks.
