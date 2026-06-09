# Food Buddy — Backend

FastAPI REST API for the restaurant ordering platform.

## Tech stack

- Python 3.12+, FastAPI, Pydantic v2, SQLAlchemy
- JWT authentication, bcrypt
- SQLite (orders, audit logs) + JSON files (menu, users, settings, etc.)
- Razorpay Checkout

## Architecture

```
Routes → Services → Repositories → Storage (SQLite / JSON)
```

## Project structure

```
├── app/
│   ├── api/           Route handlers
│   ├── core/          Config, security, dependencies
│   ├── database/      SQLite setup
│   ├── middleware/    Logging & error handling
│   ├── models/        SQLAlchemy models
│   ├── repositories/  Data access (JSON + SQLite)
│   ├── schemas/       Pydantic request/response models
│   ├── services/      Business logic
│   └── utils/         Helpers (geocode, tenant, bootstrap)
├── data/              JSON storage (seed data; persistent disk on Render)
├── docs/              Platform specification (planning)
├── schema/            JSON Schema docs for `data/*.json`
├── scripts/           Dev seed script
├── tests/             Pytest suite
├── .env.example       Local env template
├── .env.production    Render env template
├── render.yaml        Render Blueprint
├── requirements.txt   Python dependencies
└── runtime.txt        Python version for Render
```

## Prerequisites

- Python 3.12+
- pip

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
copy .env.example .env
python scripts/seed_data.py
```

## Environment variables

| Variable | Description | Production |
|----------|-------------|------------|
| `APP_ENV` | `development` or `production` | Yes |
| `DEBUG` | Enable `/docs` Swagger UI | Set `false` |
| `SECRET_KEY` | JWT signing key (min 32 chars) | **Required** |
| `CORS_ORIGINS` | Comma-separated frontend URLs | **Required** |
| `DATABASE_URL` | SQLite connection string | Yes |
| `DATA_DIR` | JSON data directory | Yes |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | Payment keys | If using payments |
| `RAZORPAY_COMPANY_NAME` | Checkout display name | Recommended |

See `.env.example` for the full list including geocoding and token expiry settings.

## Run locally

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8080
```

Or `.\start.ps1` (seeds data if missing, then starts the server).

- Health: http://127.0.0.1:8080/api/health
- Swagger (dev): http://127.0.0.1:8080/docs

## Deploy to Render

This is a **standalone backend project** — deploy the repository root directly to Render (no subdirectory / root-directory setting required).

1. Push this repo to GitHub.
2. Create a **Web Service** or **Blueprint** from `render.yaml`.
3. Set environment variables — see `.env.production` for the full list.
4. Attach a **1 GB persistent disk** at `/var/data`.
5. Set `CORS_ORIGINS` to your Vercel frontend URL (e.g. `https://your-app.vercel.app`).
6. Verify: `https://your-api.onrender.com/api/health`

On first production start, bundled JSON from `data/` is copied to the persistent disk automatically.

## Tests

```bash
pytest tests/
```

## Key API groups

| Prefix | Description |
|--------|-------------|
| `/api/auth` | Login, refresh, current user |
| `/api/menu` | Menu CRUD |
| `/api/orders` | Place & manage orders |
| `/api/payments` | Razorpay checkout & verify |
| `/api/delivery` | Driver assignments & live tracking |
| `/api/dashboard` | Admin statistics |
| `/api/platform` | Super-admin settings |
| `/api/restaurants` | Multi-tenant restaurants |

## Razorpay

1. Add test/live keys to `.env` (never commit secrets).
2. Enable UPI in the [Razorpay Dashboard](https://dashboard.razorpay.com/) under Payment Methods.
3. Optional: set `RAZORPAY_CHECKOUT_CONFIG_ID` for custom payment method config.

Payment flow: `POST /api/payments/checkout` → Razorpay modal → `POST /api/payments/verify`.

## Seed data

```bash
python scripts/seed_data.py
```

Creates 30 menu items, admin users, restaurant settings, and sample SQLite orders. Refuses to run when `APP_ENV=production`.

## Default credentials (development)

| Role | Username | Password |
|------|----------|----------|
| Restaurant admin | `admin` | `admin123` |
| Super admin | `superadmin` | `superadmin123` |
| Delivery partner | `driver1` | `driver123` |
