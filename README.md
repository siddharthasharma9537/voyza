# 🚗 Voyza - Modern Car Rental Platform

A full-stack car rental application built with **Next.js 16**, **FastAPI**, **PostgreSQL**, and **Docker**. Perfect for launching a ride-sharing or vehicle rental business.

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Status](https://img.shields.io/badge/status-Production%20Ready-brightgreen)

## ✨ Features

### 👥 For Customers
- 🔍 Browse available cars with advanced filters (price, fuel type, transmission, etc.)
- 📅 Book cars with flexible date/time selection
- 💰 Real-time pricing calculation
- 💳 Secure payment via Razorpay
- ⭐ Rate and review vehicles
- 📱 Responsive mobile-friendly interface

### 🚗 For Car Owners
- ➕ List vehicles with multiple photos
- 📊 Manage availability and pricing
- 📈 Track bookings and earnings
- 👁️ Monitor customer reviews
- 💵 Withdraw earnings

## 🏗️ Tech Stack

### Frontend
- **Next.js 16.2** - React 19 framework with Turbopack
- **Tailwind CSS 3.4** - Utility-first styling
- **TypeScript** - Type-safe JavaScript
- **Responsive Design** - Mobile-first approach

### Backend
- **FastAPI 0.111** - Modern Python web framework
- **SQLAlchemy 2.0** - ORM for database queries
- **PostgreSQL 16** - Reliable relational database
- **Redis 7** - Caching layer
- **Alembic** - Database migrations
- **Pydantic** - Data validation

### Infrastructure
- **Docker & Docker Compose** - Containerization
- **Nginx** - Reverse proxy
- **JWT** - Secure authentication

### External Services
- **Razorpay** - Payment processing
- **AWS S3** - Image storage
- **SendGrid** - Email notifications
- **Twilio** - SMS/OTP delivery (ready)

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose (or Node.js 18+ & Python 3.10+)
- Git

### Local Development

```bash
# Clone the repository
git clone https://github.com/siddharthasharma9537/voyza.git
cd voyza

# Start services with Docker
docker-compose up

# Services will be available at:
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Manual Setup (Without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend-web
npm install
npm run dev
```

## 📁 Project Structure

```
voyza/
├── frontend-web/                 # Next.js application
│   ├── app/                     # App directory (pages, layouts)
│   ├── components/              # Reusable React components
│   ├── lib/                     # Utilities (API client, auth)
│   ├── public/                  # Static assets
│   ├── package.json
│   └── tailwind.config.ts       # Tailwind configuration
│
├── backend/                      # FastAPI application
│   ├── app/
│   │   ├── main.py              # Application factory
│   │   ├── api/v1/endpoints/    # Route handlers
│   │   ├── models/              # SQLAlchemy ORM models
│   │   ├── schemas/             # Pydantic request/response models
│   │   ├── services/            # Business logic
│   │   ├── core/                # Configuration
│   │   └── db/                  # Database setup
│   ├── alembic/                 # Database migrations
│   └── requirements.txt
│
├── docker-compose.yml           # Local development setup
├── docker-compose.prod.yml      # Production setup (optional)
├── .env.example                 # Environment variables template
└── README.md                     # This file
```

## 🔧 Configuration

### Environment Variables

Copy `.env.example` files to `.env` and fill in your values:

**Backend** (`backend/.env`):
```bash
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/voyza_db
REDIS_HOST=localhost
JWT_SECRET=your-secret-key-here
RAZORPAY_KEY_ID=your_key_id
RAZORPAY_KEY_SECRET=your_secret
```

**Frontend** (`frontend-web/.env.local`):
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

## 📚 API Documentation

Auto-generated API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

```
# Authentication
POST   /api/v1/auth/register          - Register new user
POST   /api/v1/auth/login             - Login with phone & password
POST   /api/v1/auth/verify-otp        - Verify OTP for login
GET    /api/v1/auth/me                - Get current user

# Vehicles (Public)
GET    /api/v1/vehicles               - Browse vehicles
GET    /api/v1/vehicles/{id}          - Get vehicle details
GET    /api/v1/vehicles/{id}/reviews  - Get vehicle reviews

# Bookings (Authenticated)
GET    /api/v1/bookings               - Get user's bookings
POST   /api/v1/bookings               - Create booking
POST   /api/v1/bookings/{id}/cancel   - Cancel booking
POST   /api/v1/bookings/preview       - Calculate pricing

# Owner Dashboard (Owner Role)
GET    /api/v1/owner/cars             - List owner's vehicles
POST   /api/v1/owner/cars             - Add new vehicle
PATCH  /api/v1/owner/cars/{id}        - Update vehicle
GET    /api/v1/owner/earnings         - View earnings

# Reviews
POST   /api/v1/reviews                - Submit review
PATCH  /api/v1/reviews/{id}           - Add owner reply
```

## 🔐 Security Features

- ✅ JWT-based authentication
- ✅ Password hashing with bcrypt
- ✅ CORS protection
- ✅ Rate limiting (60 requests/minute)
- ✅ SQL injection prevention (SQLAlchemy)
- ✅ HTTPS ready with Let's Encrypt

## 📊 Database Schema

### Core Tables
- **users** - User accounts (customers & owners)
- **vehicles** - Car listings
- **vehicle_images** - Photos for each vehicle
- **bookings** - Rental reservations
- **payments** - Payment records
- **reviews** - User reviews
- **availability** - Blocked/booked time slots
- **refresh_tokens** - Session management

## 🚢 Deployment

### Quick Deploy to DigitalOcean

```bash
# 1. Create Ubuntu 22.04 droplet ($12/month)
# 2. SSH into server
ssh root@your_server_ip

# 3. Clone repository and configure
git clone https://github.com/yourusername/voyza.git
cd voyza
cp backend/.env.example backend/.env
cp frontend-web/.env.example frontend-web/.env.local

# 4. Update .env with production values
nano backend/.env

# 5. Deploy with Docker
docker-compose -f docker-compose.prod.yml up -d
docker-compose -f docker-compose.prod.yml exec api alembic upgrade head
```

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for detailed production deployment steps.

## 📈 Monthly Cost Estimate

| Service | Cost | Notes |
|---------|------|-------|
| Server (2GB) | $12 | DigitalOcean |
| Domain | $10-15/yr | GoDaddy, Namecheap |
| SSL | Free | Let's Encrypt |
| S3 Storage | ~$5 | AWS (50GB) |
| Email | Free-$30 | SendGrid |
| SMS | Pay-per-use | Twilio |
| Payment | 2% + ₹3 | Razorpay commission |
| **Estimated Total** | **~$50-80/month** | (excl. transactions) |

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend-web
npm run test
```

## 🐛 Troubleshooting

### "Cannot validate credentials" error
- Clear browser localStorage: `localStorage.clear()`
- Sign up again with a new account
- Check JWT_SECRET matches between frontend & backend

### Database connection failed
- Verify PostgreSQL is running: `docker-compose ps`
- Check DATABASE_URL in `.env`
- Ensure port 5432 is not blocked

### CORS errors
- Update `BACKEND_CORS_ORIGINS` in `backend/.env`
- Must match your frontend URL exactly
- Restart API after changes

### API returning 500 errors
- Check logs: `docker-compose logs api`
- Verify all required environment variables are set
- Ensure database migrations ran: `alembic upgrade head`

## 📝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines.

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Siddharta Sharma**
- GitHub: [@siddharthasharma9537](https://github.com/siddharthasharma9537)
- Email: your.email@example.com

## 🙏 Acknowledgments

- Built with [Next.js](https://nextjs.org/)
- Backend powered by [FastAPI](https://fastapi.tiangolo.com/)
- Database with [PostgreSQL](https://www.postgresql.org/)
- Payments via [Razorpay](https://razorpay.com/)

## 📧 Support

Have questions or need help? 
- 📝 Create an [issue](https://github.com/siddharthasharma9537/voyza/issues)
- 💬 Start a [discussion](https://github.com/siddharthasharma9537/voyza/discussions)
- 📧 Email: your.email@example.com

---

**Built with ❤️ for the open-source community**
