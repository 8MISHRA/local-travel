# YatraFlow — Curated Travel Platform

> "Just reach Varanasi or Mirzapur. We take care of everything else."

A premium curated travel platform serving Varanasi and Mirzapur, India. The platform manages end-to-end travel experiences including hotels, transportation, local scouts, hidden places, food, temples, ghats, waterfalls, cultural experiences, and more.

## Tech Stack

### Backend (Flask API)
- **Framework:** Flask with Blueprints
- **Database:** PostgreSQL with SQLAlchemy ORM
- **Migrations:** Alembic (via Flask-Migrate)
- **Validation:** Marshmallow schemas
- **Authentication:** JWT (PyJWT) with bcrypt password hashing
- **Rate Limiting:** Flask-Limiter with Redis
- **Background Tasks:** Celery (Redis broker)
- **WSGI Server:** Gunicorn
- **Containerization:** Docker + Docker Compose

### Frontend (React SPA)
- **Framework:** React 19 with Vite
- **Styling:** TailwindCSS with custom design system
- **Components:** shadcn/ui-style (Radix UI primitives)
- **Animations:** Framer Motion
- **Routing:** React Router
- **Icons:** Lucide React

## Project Structure

```
local_travel/
├── app/                          # Flask backend
│   ├── __init__.py               # App factory
│   ├── config.py                 # Environment configs
│   ├── extensions.py             # SQLAlchemy, Marshmallow, etc.
│   ├── api/v1/                   # API routes (15 resource groups)
│   ├── models/                   # SQLAlchemy models (22 tables)
│   ├── services/                 # Business logic layer
│   ├── repositories/             # Data access layer
│   ├── middleware/               # Auth, RBAC, rate limiting, logging
│   └── utils/                    # Response helpers, exceptions, pagination
├── frontend/                     # React frontend
│   ├── src/
│   │   ├── pages/                # 9 pages (Home, Packages, etc.)
│   │   ├── components/           # UI, layout, shared components
│   │   ├── data/                 # Mock data
│   │   └── lib/                  # Utilities
│   └── package.json
├── migrations/                   # Alembic migration files
├── tests/                        # Property-based & unit tests
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── .env.example
```

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or use Docker)
- Redis 7+ (or use Docker)

### Backend Setup

```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your database credentials

# Start PostgreSQL & Redis (Docker)
docker-compose up -d db redis

# Run database migrations
flask db upgrade

# Start the API server
flask run
# Server runs at http://localhost:5000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start dev server
npm run dev
# Frontend runs at http://localhost:5173
```

### Full Stack with Docker

```bash
docker-compose up --build
# API: http://localhost:5000
# Frontend: http://localhost:5173
```

## API Endpoints

All endpoints are prefixed with `/api/v1/`.

| Resource | Methods | Auth Required |
|----------|---------|---------------|
| `/auth/register` | POST | No |
| `/auth/login` | POST | No |
| `/auth/refresh` | POST | No |
| `/auth/logout` | POST | No |
| `/auth/me` | GET | Yes |
| `/packages` | GET, POST | Public / Admin |
| `/packages/:id` | GET, PUT, DELETE | Public / Admin |
| `/destinations` | GET, POST | Public / Admin |
| `/bookings` | GET, POST | Customer |
| `/bookings/:id/status` | PATCH | Admin/Scout |
| `/hotels` | GET, POST | Public / Admin |
| `/hotels/availability` | GET | Public |
| `/scouts` | GET, POST | Admin |
| `/drivers` | GET, POST | Admin |
| `/payments` | POST | Customer |
| `/payments/callback` | POST | Webhook |
| `/invoices` | GET | Customer/Admin |
| `/reviews` | GET, POST | Public / Customer |
| `/coupons` | GET, POST | Admin |
| `/wishlist` | GET, POST, DELETE | Customer |
| `/notifications` | GET, PATCH | Authenticated |
| `/support-tickets` | GET, POST | Customer/Admin |
| `/health` | GET | No |

## User Roles

| Role | Access Level |
|------|-------------|
| Guest | Public endpoints only |
| Customer | Bookings, reviews, wishlist, support |
| Scout | Trip management, booking updates |
| Driver | Trip assignments |
| Vendor | Service listings |
| Hotel Partner | Hotel & room management |
| Admin | Full management access |
| Super Admin | Role management, system config |

## Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| Home | `/` | Hero, featured packages, destinations, testimonials |
| Packages | `/packages` | Browse & filter packages grid |
| Package Detail | `/packages/:id` | Itinerary, pricing tiers, book CTA |
| Destinations | `/destinations` | Varanasi & Mirzapur with sub-destinations |
| Login | `/login` | Authentication |
| Register | `/register` | New account creation |
| Dashboard | `/dashboard` | Customer booking overview |
| Booking Flow | `/book/:id` | Multi-step booking wizard |
| Support | `/support` | Support ticket form |

## Design System

- **Colors:** Deep Saffron (#FF6B35), Temple Gold (#FFB800), River Blue (#1E3A5F), Warm Cream (#FFF8F0), Dark Charcoal (#1A1A2E)
- **Typography:** Inter (body), Playfair Display (headings)
- **Components:** Card-based, rounded corners, subtle shadows, smooth animations

## Testing

```bash
# Run all tests
pytest

# Run property-based tests only
pytest tests/property/ -v

# Run with coverage
pytest --cov=app
```

## Environment Variables

See `.env.example` for all required variables:
- `SECRET_KEY` — Flask secret key
- `JWT_SECRET` — JWT signing key
- `DATABASE_URL` — PostgreSQL connection string
- `REDIS_URL` — Redis connection string
- `ALLOWED_ORIGINS` — CORS allowed origins

## License

Private — All rights reserved.
