# 🐳 Running Voyza with Docker

Complete Docker setup for local development and production.

## Prerequisites

- Docker Desktop installed ([download](https://www.docker.com/products/docker-desktop))
- Docker Compose (included with Docker Desktop)

## Quick Start

### Development Mode (with hot-reload)

```bash
docker compose up
```

This starts all services:
- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:8000
- **Database:** localhost:5432
- **Redis:** localhost:6379

### First Time Setup

The database will be empty. Run migrations:

```bash
docker compose exec api alembic upgrade head
```

### Stopping Services

```bash
docker compose down
```

To also remove volumes (clears database):
```bash
docker compose down -v
```

---

## Services

| Service | Port | Image |
|---------|------|-------|
| **Frontend** | 3000 | Node.js 20 (Next.js) |
| **Backend** | 8000 | Python 3.12 (FastAPI) |
| **Database** | 5432 | PostgreSQL 16 |
| **Cache** | 6379 | Redis 7 |

---

## Viewing Logs

All services:
```bash
docker compose logs -f
```

Specific service:
```bash
docker compose logs -f api
docker compose logs -f web
docker compose logs -f db
```

---

## Common Tasks

### Access Database Shell
```bash
docker compose exec db psql -U voyza -d voyza_db
```

### Rebuild After Changes
```bash
docker compose build
docker compose up
```

### Fresh Start (reset everything)
```bash
docker compose down -v
docker compose up
```

---

## Environment Variables

### Backend (.env in backend/)
- `POSTGRES_SERVER=db` (Docker hostname)
- `REDIS_HOST=redis` (Docker hostname)
- Other configs in `backend/.env`

### Frontend
- `NEXT_PUBLIC_API_URL=http://api:8000/api/v1` (internal Docker network)

---

## Production Deployment

For production, use `docker-compose.prod.yml`:

```bash
docker compose -f docker-compose.prod.yml up -d
```

---

## Troubleshooting

**Port already in use?**
```bash
# Change ports in docker-compose.yml
# Or free the port:
lsof -ti:3000 | xargs kill -9  # Port 3000
lsof -ti:8000 | xargs kill -9  # Port 8000
```

**Database won't start?**
```bash
# Check logs
docker compose logs db

# Reset database
docker compose down -v
docker compose up
```

**Frontend can't connect to backend?**
- Ensure both containers are on the same Docker network (automatic with compose)
- Check `NEXT_PUBLIC_API_URL` — should be `http://api:8000/api/v1` inside Docker

**Build issues?**
```bash
# Clean rebuild
docker compose down
docker system prune -a
docker compose up --build
```

---

## Performance Tips

- First run takes longer (downloading images, installing deps)
- Subsequent runs are fast (cached layers)
- Hot-reload works automatically for both frontend and backend
- Database persists across container restarts (unless `-v` flag used)
