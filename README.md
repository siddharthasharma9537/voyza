# Voyza — Complete Setup Guide

## Prerequisites
- Docker + Docker Compose
- Python 3.12 (for local dev without Docker)
- Node.js 18+ (for frontend)

---

## 1. Quick Start (Docker — recommended)

```bash
# Clone and enter project
cd voyza

# Copy environment file
cp backend/.env.example backend/.env

# Edit backend/.env — fill in real values for:
#   SECRET_KEY, RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET
#   RAZORPAY_WEBHOOK_SECRET, TWILIO_ACCOUNT_SID etc.
# For local dev, the defaults work for DB + Redis

# Start all services
docker-compose up -d

# Run migrations
docker-compose exec api alembic upgrade head

# Seed with sample data
docker-compose exec api python scripts/seed.py

# API is live at:
#   http://localhost:8000
#   http://localhost:8000/docs  (Swagger UI — dev only)
```

---

## 2. Local Dev (without Docker)

```bash
cd backend

# Create virtualenv
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install deps
pip install -r requirements.txt

# Start PostgreSQL + Redis (using Docker just for these)
docker-compose up -d db redis

# Copy and configure .env
cp .env.example .env

# Run migrations
alembic upgrade head

# Seed database
python scripts/seed.py

# Start server (hot reload)
uvicorn app.main:app --reload --port 8000
```

---

## 3. Run Tests

```bash
cd backend

# All tests
pytest

# Unit tests only (fast, no DB)
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# With coverage
pytest --cov=app --cov-report=html
# Open htmlcov/index.html to view coverage report

# Run specific test file
pytest tests/unit/test_booking_service.py -v
```

---

## 4. Postman Setup

1. Open Postman → Import → select `voyza_postman_collection.json`
2. Collection variables are pre-configured
3. Run requests in this order:
   - **Auth / Send OTP** → note the OTP in response (dev mode)
   - **Auth / Verify OTP** → token auto-saved to `{{access_token}}`
   - **Cars / Browse Cars** → `car_id` auto-saved
   - **Bookings / Create Booking** → `booking_id` auto-saved
   - **Payments / Create Razorpay Order** → test the payment flow

---

## 5. Test Credentials (after seeding)

| Role     | Phone          | Password        |
|----------|----------------|-----------------|
| Admin    | +919000000001  | Admin@1234      |
| Owner    | +919876543210  | Owner@1234      |
| Customer | +919834567890  | Customer@1234   |

**Dev OTP:** In DEBUG mode, OTP is returned in the API response. Use it directly.

---

## 6. Key URLs

| Service         | URL                                    |
|-----------------|----------------------------------------|
| API             | http://localhost:8000                  |
| Swagger UI      | http://localhost:8000/docs             |
| Health check    | http://localhost:8000/health           |
| Flower (Celery) | http://localhost:5555                  |

---

## 7. Start Celery Worker + Beat

```bash
# Worker (background tasks)
celery -A app.tasks.celery_app worker --loglevel=info

# Beat scheduler (reminders, cleanup)
celery -A app.tasks.celery_app beat --loglevel=info

# Both together (dev only)
celery -A app.tasks.celery_app worker --beat --loglevel=info
```

---

## 8. WebSocket Testing

```bash
# Install wscat
npm install -g wscat

# Get your access token first via /auth/login
TOKEN="your_access_token_here"
BOOKING_ID="your_booking_id_here"
USER_ID="your_user_id_here"

# Track a booking (customer view)
wscat -c "ws://localhost:8000/ws/track/$BOOKING_ID?token=$TOKEN"

# Personal notifications
wscat -c "ws://localhost:8000/ws/notify/$USER_ID?token=$TOKEN"

# Send GPS update as owner
# After connecting to tracking ws, paste this JSON:
# {"lat": 17.385, "lng": 78.486, "speed_kmph": 45, "heading": 270}
```

---

## 9. Production Deployment

```bash
# Build production image
docker build -t voyza-api:latest backend/

# Run production stack
docker-compose -f docker-compose.prod.yml up -d

# Run migrations before swapping
docker-compose -f docker-compose.prod.yml run --rm api alembic upgrade head

# Check logs
docker-compose -f docker-compose.prod.yml logs -f api
```

---

## 10. Promo Codes (Test)

| Code       | Discount           | Conditions                    |
|------------|--------------------|-------------------------------|
| WELCOME10  | ₹100 flat off      | First use, min booking ₹500   |
| HYDLOVE20  | 20% off            | Hyderabad only, max 2 uses    |
| EV2026     | ₹200 off           | Electric vehicles only        |
| WEEKEND25  | 25% off            | Min booking ₹1,200            |

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────┐
│                    Clients                          │
│  Customer Web (Next.js) │ Owner App │ Admin Panel   │
└──────────────┬──────────────────────────────────────┘
               │ HTTP + WebSocket
┌──────────────▼──────────────────────────────────────┐
│              Nginx (SSL, rate limiting)              │
└──────────────┬──────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────┐
│           FastAPI Backend (2 replicas)               │
│                                                     │
│  Auth │ Cars │ Bookings │ Owner │ Admin             │
│  Payments │ Reviews │ Realtime (WS)                 │
└──────┬───────────────────────────────────┬──────────┘
       │                                   │
┌──────▼──────┐                    ┌───────▼───────┐
│ PostgreSQL  │                    │     Redis     │
│  (primary   │                    │  (cache, WS,  │
│   + read    │                    │   Celery)     │
│   replica)  │                    └───────────────┘
└─────────────┘
                    ┌──────────────────────────┐
                    │   Celery Worker + Beat   │
                    │  SMS │ Push │ Reminders  │
                    └──────────────────────────┘
```
