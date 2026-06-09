# AI Restaurant Direct Ordering Platform — Technical Specification

> **Status:** Draft — awaiting approval before implementation  
> **Version:** 1.2.0  
> **Date:** 2026-06-08  
> **Source PRD:** `AI_Restaurant_Direct_Ordering_Platform_PRD.md`

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Scope & Exclusions](#2-scope--exclusions)
3. [Current State Assessment](#3-current-state-assessment)
4. [Technology Stack](#4-technology-stack)
5. [User Roles & Access Control](#5-user-roles--access-control)
6. [Feature Specifications](#6-feature-specifications)
7. [Data Architecture (SQL Database)](#7-data-architecture-sql-database)
8. [Entity Schema Definitions (SQL)](#8-entity-schema-definitions-sql)
9. [API Specification](#9-api-specification)
10. [Frontend Specification](#10-frontend-specification)
11. [Security](#11-security)
12. [Migration from Current Application](#12-migration-from-current-application)
13. [Implementation Phases](#13-implementation-phases)
14. [Future Enhancements (Out of Scope)](#14-future-enhancements-out-of-scope)
15. [Success Metrics](#15-success-metrics)
16. [Approval Checklist](#16-approval-checklist)

---

## 1. Executive Summary

This specification defines the evolution of the existing **Restaurant Ordering & Daily Order Tracking System** into a **multi-role SaaS direct ordering platform** aligned with the PRD. Restaurants will receive direct orders via web (and future WhatsApp/mobile channels), manage menus and branches, track deliveries, run marketing campaigns, and retain customer relationships — without marketplace commission dependency.

**Key architectural decision:** All persistent data is stored in a **SQL database** (SQLite for local/dev; PostgreSQL for production per PRD). Table structure is the **single source of truth** in **raw `.sql` DDL files** under `schema/`. The backend uses **raw SQL queries** (no ORM, no SQLAlchemy models). Clean Architecture is preserved: Routes → Services → Repositories (parameterized SQL) → Database.

**Preserved from current app:** Razorpay payment integration, JWT authentication, admin dashboard, order tracking, menu management, SQLite database, and the React + FastAPI stack.

---

## 2. Scope & Exclusions

### In Scope (This Implementation)

| Area | Details |
|------|---------|
| Authentication & RBAC | Multi-role JWT auth (5 roles) |
| Restaurant Management | Onboarding, profile, branch management |
| Menu Management | Categories, items, pricing, availability |
| Customer Management | Profiles, order history, loyalty points (data model + CRUD) |
| Ordering | Cart, checkout, order lifecycle, Razorpay payments |
| Delivery Management | Partner registry, assignment, status tracking |
| Marketing Automation | Campaign creation, segmentation (data + admin UI) |
| Reviews | Customer reviews linked to orders |
| Analytics Dashboard | Revenue, orders, customer metrics |
| SQL Database | All entities in SQL tables via raw SQL queries |
| Schema Definitions | Raw `.sql` DDL files in `schema/` folder (no ORM layer) |

### Explicitly Out of Scope (Deferred)

| Feature | Reason |
|---------|--------|
| AI Ordering Assistant (chat, NL ordering) | Per project directive — Phase 2+ |
| AI Recommendations (personalized dishes, upselling) | Per project directive — Phase 2+ |
| AI Marketing Agent | Deferred with AI layer |
| AI Analytics Agent | Deferred with AI layer |
| Vector Database (Qdrant/Pinecone) | Requires AI layer |
| LangGraph / LangChain integration | Requires AI layer |
| WhatsApp AI Agent | Future enhancement |
| Voice Ordering | Future enhancement |
| Redis caching | Not required for MVP |

---

## 3. Current State Assessment

### What Exists Today

| Capability | Status | Storage |
|------------|--------|---------|
| Single-restaurant ordering (Dine In / Pickup) | ✅ Implemented | SQLite |
| Menu CRUD (30 items, 6 categories) | ✅ Implemented | `menu.json` (to migrate → SQL) |
| Admin auth (single admin user) | ✅ Implemented | `users.json` (to migrate → SQL) |
| Order placement & tracking | ✅ Implemented | SQLite (`orders`, `order_items`) |
| Order status workflow | ✅ Implemented | SQLite |
| Razorpay payments | ✅ Implemented | SQLite + `payments.json` (to migrate → SQL) |
| Admin dashboard (stats, revenue chart) | ✅ Implemented | Derived from SQLite |
| Restaurant settings (name, hero, hours) | ✅ Implemented | `settings.json` (to migrate → SQL) |
| Audit logs | ✅ Partial | SQLite |
| Customer registration/login | ❌ Missing | — |
| Multi-restaurant support | ❌ Missing | — |
| Branch management | ❌ Missing | — |
| Delivery partners & assignment | ❌ Missing | — |
| Loyalty points | ❌ Missing | — |
| Campaigns & segmentation | ❌ Missing | — |
| Reviews | ❌ Missing | — |
| Role-based access (5 roles) | ❌ Missing (admin only) | — |
| Customer dashboard | ❌ Missing | — |

### Gap Summary

The current app is a **single-restaurant MVP** with admin-only access and **hybrid SQLite + JSON storage**. The PRD target is a **multi-entity platform** with five user roles and fifteen SQL tables. This spec consolidates all data into SQL and bridges the gap incrementally while preserving working features (especially Razorpay and order tracking).

---

## 4. Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | React 18, Vite, Tailwind CSS, React Router, Axios, Context API | Existing stack retained |
| Backend | Python 3.12+, FastAPI, Pydantic v2 | Existing stack retained |
| Database | **SQLite** (dev) / **PostgreSQL** (production) | `sqlite3` / `psycopg2` — raw SQL only |
| Schema Definitions | **Raw SQL DDL** (`.sql` files) in `schema/` | Single source of truth — no ORM models |
| Data Access | Parameterized SQL in repositories | `SELECT` / `INSERT` / `UPDATE` / `DELETE` |
| Runtime Validation | Pydantic models for API request/response only | Not mapped to DB tables |
| Payments | Razorpay Checkout | Existing integration retained |
| Auth | JWT (access + refresh tokens) | Extended for multi-role |
| Deployment | Docker + Nginx (backend), Vercel/Netlify (frontend) | As PRD |

### Project Structure (Target)

```
restaurant-app/
├── schema/                          # SQL DDL definitions (NEW)
│   ├── 00_init.sql                  # Master init script (runs all in order)
│   ├── users.sql
│   ├── restaurants.sql
│   ├── branches.sql
│   ├── menus.sql
│   ├── menu_items.sql
│   ├── customers.sql
│   ├── customer_addresses.sql
│   ├── orders.sql
│   ├── order_items.sql
│   ├── delivery_partners.sql
│   ├── loyalty_points.sql
│   ├── campaigns.sql
│   ├── reviews.sql
│   ├── payments.sql
│   ├── audit_logs.sql
│   ├── platform_settings.sql
│   └── indexes.sql
├── backend/
│   ├── database/
│   │   └── restaurant.db            # SQLite database file (dev)
│   ├── app/
│   │   ├── api/                     # Route handlers
│   │   ├── services/                # Business logic
│   │   ├── repositories/            # Raw SQL queries (parameterized)
│   │   ├── schemas/                 # Pydantic request/response models
│   │   └── database/
│   │       ├── connection.py        # DB connection pool / context manager
│   │       └── query.py             # Shared query helpers (fetch_one, fetch_all, execute)
│   └── scripts/
│       ├── seed_data.py
│       └── apply_schema.py          # Apply schema/*.sql to database
├── frontend/
│   └── src/
│       ├── pages/                   # Role-specific dashboards
│       ├── components/
│       └── ...
├── docs/
│   └── SPECIFICATION.md             # This document
└── README.md
```

---

## 5. User Roles & Access Control

| Role | Code | Description | Key Permissions |
|------|------|-------------|-----------------|
| Customer | `customer` | End user placing orders | Browse menu, place orders, track orders, write reviews, view loyalty points |
| Restaurant Owner | `restaurant_owner` | Business owner | Full restaurant/branch/menu management, view analytics, manage staff, campaigns |
| Restaurant Staff | `restaurant_staff` | Kitchen/front-of-house | View/update orders, update menu availability |
| Delivery Partner | `delivery_partner` | Driver/courier | View assigned deliveries, update delivery status |
| Platform Administrator | `platform_admin` | SaaS operator | Manage all restaurants, users, platform settings |

### RBAC Matrix

| Resource | Customer | Staff | Owner | Delivery | Platform Admin |
|----------|----------|-------|-------|----------|----------------|
| Menu (read) | ✅ Public | ✅ | ✅ | ❌ | ✅ |
| Menu (write) | ❌ | ✅ Availability only | ✅ Full | ❌ | ✅ |
| Orders (create) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Orders (read own) | ✅ | ❌ | ❌ | ❌ | ❌ |
| Orders (read restaurant) | ❌ | ✅ | ✅ | ✅ Assigned | ✅ |
| Orders (update status) | ❌ | ✅ | ✅ | ✅ Delivery only | ✅ |
| Restaurants | ❌ | ❌ | ✅ Own | ❌ | ✅ All |
| Branches | ❌ | ❌ | ✅ Own | ❌ | ✅ All |
| Customers | ✅ Own profile | ❌ | ✅ Read | ❌ | ✅ |
| Delivery Partners | ❌ | ❌ | ✅ Manage | ✅ Own profile | ✅ |
| Campaigns | ❌ View active | ❌ | ✅ CRUD | ❌ | ✅ |
| Reviews | ✅ Create/read | ❌ Read | ✅ Read/respond | ❌ | ✅ |
| Analytics | ❌ | ❌ | ✅ | ❌ | ✅ |
| Loyalty Points | ✅ Own | ❌ | ✅ Read/adjust | ❌ | ✅ |
| Payments | ✅ Own checkout | ❌ | ✅ Read | ❌ | ✅ |

### Backward Compatibility

The existing `admin` role maps to `restaurant_owner` during migration. Login credentials (`admin` / `admin123`) remain valid.

---

## 6. Feature Specifications

### 6.1 Restaurant Management

**Onboarding**
- Platform admin or self-service registration creates a restaurant record.
- Owner account is linked to the restaurant via `restaurant_id` on the user record.
- Default branch is auto-created from restaurant address.

**Profile Management**
- Restaurant name, tagline, logo, hero images, about text, contact info, working hours.
- Migrates existing `settings.json` fields into `restaurants` table + `platform_settings` table.

**Branch Management**
- A restaurant can have multiple branches (locations).
- Each branch has its own address, phone, working hours, and active/inactive status.
- Menu items can be branch-specific or shared (via `branch_id` on `menus`).

**Pricing Management**
- Menu item prices are managed per item; optional branch-level price overrides via a future `branch_menu_prices` table (deferred to Phase 2).

### 6.2 Menu Management

- Categories are defined per restaurant (migrated from current flat category list).
- Menu items: name, description, price, image, category, dietary tags, availability.
- CRUD via restaurant owner/staff with role checks.
- Public menu endpoint filtered by restaurant/branch.

**Migration note:** Current `menu.json` structure (`{ items, categories }`) migrates into `menus` + `menu_items` SQL tables.

### 6.3 Customer Management

- Customer registration (name, email, phone, password).
- Customer profile with delivery addresses (`customer_addresses` table).
- Order history linked via `customer_id` on orders.
- Loyalty points balance and transaction history.

**Guest ordering:** Orders without registration remain supported (phone + name only), matching current behavior.

### 6.4 Ordering

**Order Types:** `Dine In`, `Pickup`, `Delivery` (new — PRD delivery management).

**Order Lifecycle:**

```
Pending → Accepted → Preparing → Ready → Out for Delivery → Delivered
                                              ↓
                                          Cancelled (any stage before Delivered)
```

**Payment:** Razorpay flow unchanged. Payment records stored in `payments` SQL table.

**Order ID format:** `ORD-{YEAR}{SEQUENCE}` (e.g., `ORD-20260001`) — preserved.

### 6.5 Delivery Management

- Delivery partner registry (name, phone, vehicle, availability status).
- Order assignment: owner/staff assigns a delivery partner to a delivery order.
- Status updates: `assigned → picked_up → in_transit → delivered`.
- Customer tracking page shows delivery status when order type is `Delivery`.

### 6.6 Marketing Automation

- Campaign entity: title, description, discount type (% or flat), target segment, schedule, status.
- Customer segmentation: by order count, last order date, loyalty tier, or manual list.
- Campaign display on customer-facing pages (banner/promo code).
- WhatsApp promotion sending is **deferred** (requires WhatsApp Business API integration).

### 6.7 Reviews

- Customers can submit a review (1–5 rating + text) for completed orders.
- One review per order (enforced by `UNIQUE(order_id)` constraint).
- Restaurant owner can view and optionally respond.

### 6.8 Analytics Dashboard

**Restaurant Owner Dashboard:**
- Today's orders, revenue, average order value.
- Orders by status (chart).
- Revenue trend (daily/weekly).
- Top-selling items.
- Customer count and repeat rate.

**Platform Admin Dashboard:**
- Active restaurants, total GMV, order volume across platform.

Existing dashboard endpoints are extended, not replaced.

### 6.9 Loyalty Program

- Points earned: configurable rate (e.g., 1 point per ₹10 spent).
- Points redeemed: discount at checkout (future) or manual adjustment by owner.
- Transaction log: earn, redeem, expire, adjust.

---

## 7. Data Architecture (SQL Database)

### Design Principles

1. **Relational normalization** — Foreign keys enforce referential integrity between tables.
2. **Schema-as-code** — Every table is defined in a raw `.sql` file under `schema/`; `apply_schema.py` applies DDL on startup or via migration script.
3. **Raw SQL only** — Repositories execute parameterized SQL (`?` placeholders for SQLite, `%s` for PostgreSQL). No ORM, no SQLAlchemy models, no `backend/app/models/` layer.
4. **SQLite for dev, PostgreSQL for prod** — DDL is written to be compatible with both (avoid DB-specific features in MVP).
5. **JSON columns as TEXT** — Complex nested data (hero slides, dietary tags, campaign targets) stored as JSON-encoded `TEXT` in SQLite; `JSONB` in PostgreSQL migration.
6. **Timestamps** — All tables use `created_at` / `updated_at` with UTC defaults.
7. **Soft deletes** — `is_active` boolean on user-facing entities; no hard deletes on orders.

### Data Access Pattern

```
API Request
  → Pydantic schema (validate input)
  → Service (business rules)
  → Repository (raw SQL)
      e.g.  SELECT * FROM orders WHERE restaurant_id = ? AND status = ?
            INSERT INTO menu_items (menu_id, restaurant_id, name, ...) VALUES (?, ?, ?, ...)
  → sqlite3 / psycopg2 connection
  → Row dict → Pydantic response schema
```

Repositories return plain Python `dict` or `list[dict]` from `cursor.fetchone()` / `fetchall()`. Services map rows to Pydantic response models. The `schema/*.sql` files are the **only** database structure definition — there is no parallel Python model layer.

### Database Connection

| Environment | Engine | Connection String |
|-------------|--------|-------------------|
| Development | SQLite | `sqlite:///./database/restaurant.db` |
| Production | PostgreSQL | `postgresql://user:pass@host:5432/restaurant_db` |

Configured via `DATABASE_URL` in `backend/.env` (existing pattern).

### Schema Application Flow

```
schema/00_init.sql
  → runs users.sql, restaurants.sql, branches.sql, ... in dependency order
  → creates all tables + indexes
  → apply_schema.py executes on app startup
  → seed_data.py populates initial records
```

### Entity Relationship Diagram

```
users ──────────────┐
                    ├── restaurants ──── branches
customers ──────────┤         │
  └── customer_addresses      ├── menus ──── menu_items
                    │         │
orders ─────────────┤         ├── campaigns
  ├── order_items   │         │
  ├── payments      │         └── reviews
  ├── reviews       │
  └── delivery ─────┘── delivery_partners
         │
loyalty_points ───── customers
audit_logs ───────── (all entities)
platform_settings ── platform config
```

### Index Strategy

Indexes are defined in `schema/indexes.sql` and applied after table creation:

| Table | Index | Purpose |
|-------|-------|---------|
| `users` | `UNIQUE(username)`, `UNIQUE(email)` | Login lookups |
| `restaurants` | `UNIQUE(slug)` | URL routing |
| `orders` | `UNIQUE(order_id)`, `INDEX(restaurant_id, status)` | Tracking + dashboard |
| `order_items` | `INDEX(order_id)` | Order detail joins |
| `menu_items` | `INDEX(restaurant_id, category)` | Menu filtering |
| `customers` | `INDEX(phone)`, `INDEX(user_id)` | Customer lookup |
| `loyalty_points` | `INDEX(customer_id, restaurant_id)` | Balance queries |
| `campaigns` | `INDEX(restaurant_id, status)` | Active campaign lookup |
| `reviews` | `UNIQUE(order_id)`, `INDEX(restaurant_id)` | One review per order |
| `payments` | `INDEX(restaurant_order_id)`, `INDEX(order_id)` | Payment reconciliation |
| `audit_logs` | `INDEX(entity_type, entity_id)` | Audit trail queries |

---

## 8. Entity Schema Definitions (Raw SQL)

> **Single source of truth:** Each block below becomes a `.sql` file in `schema/`.  
> File naming: `{table_name}.sql`  
> All DDL uses SQLite-compatible syntax; PostgreSQL variants noted where different.  
> **No SQLAlchemy models** — repositories query these tables directly with raw SQL.

### 8.1 users

**Table:** `users`  
**Schema file:** `schema/users.sql`

```sql
CREATE TABLE IF NOT EXISTS users (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    username        VARCHAR(50)  NOT NULL UNIQUE,
    email           VARCHAR(120) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    full_name       VARCHAR(120) NOT NULL,
    phone           VARCHAR(20),
    role            VARCHAR(30)  NOT NULL DEFAULT 'customer'
                    CHECK (role IN ('customer', 'restaurant_owner', 'restaurant_staff',
                                    'delivery_partner', 'platform_admin')),
    restaurant_id   INTEGER REFERENCES restaurants(id) ON DELETE SET NULL,
    branch_id       INTEGER REFERENCES branches(id) ON DELETE SET NULL,
    is_active       BOOLEAN      NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL DEFAULT (datetime('now')),
    updated_at      DATETIME     NOT NULL DEFAULT (datetime('now'))
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Auto-increment PK |
| `username` | VARCHAR(50) | NO | Unique login identifier |
| `email` | VARCHAR(120) | NO | Unique email |
| `password_hash` | VARCHAR(255) | NO | bcrypt hash |
| `full_name` | VARCHAR(120) | NO | Display name |
| `phone` | VARCHAR(20) | YES | Contact phone |
| `role` | VARCHAR(30) | NO | One of 5 platform roles |
| `restaurant_id` | INTEGER | YES | FK → restaurants (owner/staff) |
| `branch_id` | INTEGER | YES | FK → branches (staff) |
| `is_active` | BOOLEAN | NO | Account status (default: true) |
| `created_at` | DATETIME | NO | UTC timestamp |
| `updated_at` | DATETIME | NO | UTC timestamp |

---

### 8.2 restaurants

**Table:** `restaurants`  
**Schema file:** `schema/restaurants.sql`

```sql
CREATE TABLE IF NOT EXISTS restaurants (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    name            VARCHAR(120) NOT NULL,
    slug            VARCHAR(80)  NOT NULL UNIQUE,
    tagline         VARCHAR(200),
    description     TEXT,
    logo            VARCHAR(200),
    hero_image      VARCHAR(200),
    hero_slides     TEXT,         -- JSON array of slide objects
    email           VARCHAR(120) NOT NULL,
    phone           VARCHAR(20)  NOT NULL,
    address         TEXT,
    cuisine_type    VARCHAR(80),
    working_hours   TEXT,
    owner_user_id   INTEGER      NOT NULL REFERENCES users(id),
    is_active       BOOLEAN      NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL DEFAULT (datetime('now')),
    updated_at      DATETIME     NOT NULL DEFAULT (datetime('now'))
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Auto-increment PK |
| `name` | VARCHAR(120) | NO | Restaurant name |
| `slug` | VARCHAR(80) | NO | URL-friendly unique identifier |
| `tagline` | VARCHAR(200) | YES | Short tagline |
| `description` | TEXT | YES | About text |
| `logo` | VARCHAR(200) | YES | Logo URL/path |
| `hero_image` | VARCHAR(200) | YES | Default hero image |
| `hero_slides` | TEXT (JSON) | YES | Hero carousel slides |
| `email` | VARCHAR(120) | NO | Contact email |
| `phone` | VARCHAR(20) | NO | Contact phone |
| `address` | TEXT | YES | Primary address |
| `cuisine_type` | VARCHAR(80) | YES | e.g., "Andhra" |
| `working_hours` | TEXT | YES | Free-text hours |
| `owner_user_id` | INTEGER | NO | FK → users |
| `is_active` | BOOLEAN | NO | Default: true |
| `created_at` | DATETIME | NO | |
| `updated_at` | DATETIME | NO | |

---

### 8.3 branches

**Table:** `branches`  
**Schema file:** `schema/branches.sql`

```sql
CREATE TABLE IF NOT EXISTS branches (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id   INTEGER      NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name            VARCHAR(120) NOT NULL,
    address         TEXT         NOT NULL,
    phone           VARCHAR(20),
    email           VARCHAR(120),
    working_hours   TEXT,
    latitude        REAL,
    longitude       REAL,
    is_active       BOOLEAN      NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL DEFAULT (datetime('now')),
    updated_at      DATETIME     NOT NULL DEFAULT (datetime('now'))
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Auto-increment PK |
| `restaurant_id` | INTEGER | NO | FK → restaurants |
| `name` | VARCHAR(120) | NO | Branch name |
| `address` | TEXT | NO | Full address |
| `phone` | VARCHAR(20) | YES | Branch phone |
| `email` | VARCHAR(120) | YES | Branch email |
| `working_hours` | TEXT | YES | Free-text hours |
| `latitude` | REAL | YES | Geo coordinate |
| `longitude` | REAL | YES | Geo coordinate |
| `is_active` | BOOLEAN | NO | Default: true |
| `created_at` | DATETIME | NO | |
| `updated_at` | DATETIME | NO | |

---

### 8.4 menus

**Table:** `menus`  
**Schema file:** `schema/menus.sql`

```sql
CREATE TABLE IF NOT EXISTS menus (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id   INTEGER      NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    branch_id       INTEGER      REFERENCES branches(id) ON DELETE SET NULL,
    name            VARCHAR(120) NOT NULL DEFAULT 'Main Menu',
    categories      TEXT         NOT NULL,  -- JSON array of category name strings
    is_active       BOOLEAN      NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL DEFAULT (datetime('now')),
    updated_at      DATETIME     NOT NULL DEFAULT (datetime('now'))
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Auto-increment PK |
| `restaurant_id` | INTEGER | NO | FK → restaurants |
| `branch_id` | INTEGER | YES | FK → branches (NULL = all branches) |
| `name` | VARCHAR(120) | NO | Menu name |
| `categories` | TEXT (JSON) | NO | Category names array |
| `is_active` | BOOLEAN | NO | Default: true |
| `created_at` | DATETIME | NO | |
| `updated_at` | DATETIME | NO | |

---

### 8.5 menu_items

**Table:** `menu_items`  
**Schema file:** `schema/menu_items.sql`

```sql
CREATE TABLE IF NOT EXISTS menu_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    menu_id         INTEGER      NOT NULL REFERENCES menus(id) ON DELETE CASCADE,
    restaurant_id   INTEGER      NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name            VARCHAR(120) NOT NULL,
    description     TEXT         NOT NULL,
    price           REAL         NOT NULL CHECK (price > 0),
    image           VARCHAR(200) DEFAULT 'default.jpg',
    category        VARCHAR(80)  NOT NULL,
    dietary_tags    TEXT,         -- JSON array e.g. ["vegetarian","spicy"]
    available       BOOLEAN      NOT NULL DEFAULT 1,
    is_featured     BOOLEAN      NOT NULL DEFAULT 0,
    created_at      DATETIME     NOT NULL DEFAULT (datetime('now')),
    updated_at      DATETIME     NOT NULL DEFAULT (datetime('now'))
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Auto-increment PK |
| `menu_id` | INTEGER | NO | FK → menus |
| `restaurant_id` | INTEGER | NO | FK → restaurants (denormalized) |
| `name` | VARCHAR(120) | NO | Item name |
| `description` | TEXT | NO | Item description |
| `price` | REAL | NO | Price in INR (> 0) |
| `image` | VARCHAR(200) | YES | Image filename/URL |
| `category` | VARCHAR(80) | NO | Category within menu |
| `dietary_tags` | TEXT (JSON) | YES | Dietary labels |
| `available` | BOOLEAN | NO | Default: true |
| `is_featured` | BOOLEAN | NO | Featured on homepage |
| `created_at` | DATETIME | NO | |
| `updated_at` | DATETIME | NO | |

---

### 8.6 customers

**Table:** `customers`  
**Schema file:** `schema/customers.sql`

```sql
CREATE TABLE IF NOT EXISTS customers (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id                 INTEGER      REFERENCES users(id) ON DELETE SET NULL,
    name                    VARCHAR(120) NOT NULL,
    email                   VARCHAR(120),
    phone                   VARCHAR(20)  NOT NULL,
    loyalty_points_balance  INTEGER      NOT NULL DEFAULT 0,
    created_at              DATETIME     NOT NULL DEFAULT (datetime('now')),
    updated_at              DATETIME     NOT NULL DEFAULT (datetime('now'))
);
```

**Table:** `customer_addresses`  
**Schema file:** `schema/customer_addresses.sql`

```sql
CREATE TABLE IF NOT EXISTS customer_addresses (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER      NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    label           VARCHAR(50)  NOT NULL,
    line1           TEXT         NOT NULL,
    city            VARCHAR(80)  NOT NULL,
    pincode         VARCHAR(10)  NOT NULL,
    is_default      BOOLEAN      NOT NULL DEFAULT 0,
    created_at      DATETIME     NOT NULL DEFAULT (datetime('now'))
);
```

| Column (customers) | Type | Nullable | Description |
|------------------|------|----------|-------------|
| `id` | INTEGER | NO | Auto-increment PK |
| `user_id` | INTEGER | YES | FK → users (NULL for guest-only) |
| `name` | VARCHAR(120) | NO | Customer name |
| `email` | VARCHAR(120) | YES | Email |
| `phone` | VARCHAR(20) | NO | Phone |
| `loyalty_points_balance` | INTEGER | NO | Current balance (default: 0) |
| `created_at` | DATETIME | NO | |
| `updated_at` | DATETIME | NO | |

---

### 8.7 orders

**Table:** `orders`  
**Schema file:** `schema/orders.sql`

```sql
CREATE TABLE IF NOT EXISTS orders (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id                VARCHAR(32)  NOT NULL UNIQUE,
    restaurant_id           INTEGER      NOT NULL REFERENCES restaurants(id),
    branch_id               INTEGER      REFERENCES branches(id) ON DELETE SET NULL,
    customer_id             INTEGER      REFERENCES customers(id) ON DELETE SET NULL,
    customer_name           VARCHAR(120) NOT NULL,
    phone                   VARCHAR(20)  NOT NULL,
    table_number            VARCHAR(20),
    delivery_address        TEXT,         -- JSON object for delivery orders
    order_type              VARCHAR(20)  NOT NULL
                            CHECK (order_type IN ('Dine In', 'Pickup', 'Delivery')),
    notes                   TEXT,
    status                  VARCHAR(30)  NOT NULL DEFAULT 'Pending'
                            CHECK (status IN ('Pending','Accepted','Preparing','Ready',
                                              'Out for Delivery','Delivered','Cancelled')),
    payment_status          VARCHAR(20)  NOT NULL DEFAULT 'unpaid'
                            CHECK (payment_status IN ('unpaid','pending','paid',
                                                      'failed','cancelled','refunded')),
    razorpay_order_id       VARCHAR(64),
    delivery_partner_id     INTEGER      REFERENCES delivery_partners(id) ON DELETE SET NULL,
    delivery_status         VARCHAR(20)
                            CHECK (delivery_status IN ('assigned','picked_up',
                                                       'in_transit','delivered')),
    campaign_id             INTEGER      REFERENCES campaigns(id) ON DELETE SET NULL,
    discount_amount         REAL         DEFAULT 0.0,
    subtotal                REAL         NOT NULL DEFAULT 0.0,
    tax                     REAL         NOT NULL DEFAULT 0.0,
    total                   REAL         NOT NULL DEFAULT 0.0,
    created_at              DATETIME     NOT NULL DEFAULT (datetime('now')),
    updated_at              DATETIME     NOT NULL DEFAULT (datetime('now'))
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Auto-increment PK |
| `order_id` | VARCHAR(32) | NO | Human-readable ID (ORD-20260001) |
| `restaurant_id` | INTEGER | NO | FK → restaurants |
| `branch_id` | INTEGER | YES | FK → branches |
| `customer_id` | INTEGER | YES | FK → customers (NULL for guest) |
| `customer_name` | VARCHAR(120) | NO | Denormalized name |
| `phone` | VARCHAR(20) | NO | Denormalized phone |
| `table_number` | VARCHAR(20) | YES | For dine-in |
| `delivery_address` | TEXT (JSON) | YES | For delivery orders |
| `order_type` | VARCHAR(20) | NO | Dine In / Pickup / Delivery |
| `notes` | TEXT | YES | Special instructions |
| `status` | VARCHAR(30) | NO | Order lifecycle status |
| `payment_status` | VARCHAR(20) | NO | Payment state |
| `razorpay_order_id` | VARCHAR(64) | YES | Razorpay reference |
| `delivery_partner_id` | INTEGER | YES | FK → delivery_partners |
| `delivery_status` | VARCHAR(20) | YES | Delivery tracking status |
| `campaign_id` | INTEGER | YES | FK → campaigns |
| `discount_amount` | REAL | YES | Discount applied |
| `subtotal` | REAL | NO | Pre-tax subtotal |
| `tax` | REAL | NO | Tax amount |
| `total` | REAL | NO | Final total |
| `created_at` | DATETIME | NO | |
| `updated_at` | DATETIME | NO | |

---

### 8.8 order_items

**Table:** `order_items`  
**Schema file:** `schema/order_items.sql`

```sql
CREATE TABLE IF NOT EXISTS order_items (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER      NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    menu_item_id    INTEGER      NOT NULL REFERENCES menu_items(id),
    name            VARCHAR(120) NOT NULL,
    price           REAL         NOT NULL,
    quantity        INTEGER      NOT NULL DEFAULT 1 CHECK (quantity >= 1),
    line_total      REAL         NOT NULL DEFAULT 0.0
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Auto-increment PK |
| `order_id` | INTEGER | NO | FK → orders.id |
| `menu_item_id` | INTEGER | NO | FK → menu_items |
| `name` | VARCHAR(120) | NO | Snapshot of item name |
| `price` | REAL | NO | Snapshot of unit price |
| `quantity` | INTEGER | NO | Quantity (≥ 1) |
| `line_total` | REAL | NO | price × quantity |

---

### 8.9 delivery_partners

**Table:** `delivery_partners`  
**Schema file:** `schema/delivery_partners.sql`

```sql
CREATE TABLE IF NOT EXISTS delivery_partners (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER      REFERENCES users(id) ON DELETE SET NULL,
    restaurant_id   INTEGER      NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    name            VARCHAR(120) NOT NULL,
    phone           VARCHAR(20)  NOT NULL,
    vehicle_type    VARCHAR(20)  CHECK (vehicle_type IN ('bike','scooter','car','bicycle')),
    vehicle_number  VARCHAR(30),
    status          VARCHAR(20)  NOT NULL DEFAULT 'offline'
                    CHECK (status IN ('available','busy','offline')),
    is_active       BOOLEAN      NOT NULL DEFAULT 1,
    created_at      DATETIME     NOT NULL DEFAULT (datetime('now')),
    updated_at      DATETIME     NOT NULL DEFAULT (datetime('now'))
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Auto-increment PK |
| `user_id` | INTEGER | YES | FK → users |
| `restaurant_id` | INTEGER | NO | FK → restaurants |
| `name` | VARCHAR(120) | NO | Partner name |
| `phone` | VARCHAR(20) | NO | Contact phone |
| `vehicle_type` | VARCHAR(20) | YES | bike / scooter / car / bicycle |
| `vehicle_number` | VARCHAR(30) | YES | Registration number |
| `status` | VARCHAR(20) | NO | available / busy / offline |
| `is_active` | BOOLEAN | NO | Default: true |
| `created_at` | DATETIME | NO | |
| `updated_at` | DATETIME | NO | |

---

### 8.10 loyalty_points

**Table:** `loyalty_points`  
**Schema file:** `schema/loyalty_points.sql`

```sql
CREATE TABLE IF NOT EXISTS loyalty_points (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id     INTEGER      NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    restaurant_id   INTEGER      NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    order_id        INTEGER      REFERENCES orders(id) ON DELETE SET NULL,
    type            VARCHAR(20)  NOT NULL
                    CHECK (type IN ('earn','redeem','expire','adjust')),
    points          INTEGER      NOT NULL,
    balance_after   INTEGER      NOT NULL,
    description     TEXT,
    created_at      DATETIME     NOT NULL DEFAULT (datetime('now'))
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Auto-increment PK |
| `customer_id` | INTEGER | NO | FK → customers |
| `restaurant_id` | INTEGER | NO | FK → restaurants |
| `order_id` | INTEGER | YES | FK → orders (earn transactions) |
| `type` | VARCHAR(20) | NO | earn / redeem / expire / adjust |
| `points` | INTEGER | NO | Positive for earn, negative for redeem |
| `balance_after` | INTEGER | NO | Running balance |
| `description` | TEXT | YES | Transaction note |
| `created_at` | DATETIME | NO | |

---

### 8.11 campaigns

**Table:** `campaigns`  
**Schema file:** `schema/campaigns.sql`

```sql
CREATE TABLE IF NOT EXISTS campaigns (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    restaurant_id           INTEGER      NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    title                   VARCHAR(200) NOT NULL,
    description             TEXT,
    discount_type           VARCHAR(20)  NOT NULL CHECK (discount_type IN ('percentage','flat')),
    discount_value          REAL         NOT NULL CHECK (discount_value > 0),
    promo_code              VARCHAR(50),
    target_segment          VARCHAR(30)  NOT NULL DEFAULT 'all'
                            CHECK (target_segment IN ('all','new_customers','returning',
                                                      'loyalty_tier','manual')),
    target_customer_ids     TEXT,         -- JSON array of customer IDs for manual segment
    min_order_amount        REAL,
    start_date              DATETIME     NOT NULL,
    end_date                DATETIME     NOT NULL,
    status                  VARCHAR(20)  NOT NULL DEFAULT 'draft'
                            CHECK (status IN ('draft','active','paused','completed')),
    created_at              DATETIME     NOT NULL DEFAULT (datetime('now')),
    updated_at              DATETIME     NOT NULL DEFAULT (datetime('now'))
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Auto-increment PK |
| `restaurant_id` | INTEGER | NO | FK → restaurants |
| `title` | VARCHAR(200) | NO | Campaign title |
| `description` | TEXT | YES | Campaign description |
| `discount_type` | VARCHAR(20) | NO | percentage / flat |
| `discount_value` | REAL | NO | Discount amount |
| `promo_code` | VARCHAR(50) | YES | Optional promo code |
| `target_segment` | VARCHAR(30) | NO | Segmentation rule |
| `target_customer_ids` | TEXT (JSON) | YES | Manual segment IDs |
| `min_order_amount` | REAL | YES | Minimum order to apply |
| `start_date` | DATETIME | NO | Campaign start |
| `end_date` | DATETIME | NO | Campaign end |
| `status` | VARCHAR(20) | NO | draft / active / paused / completed |
| `created_at` | DATETIME | NO | |
| `updated_at` | DATETIME | NO | |

---

### 8.12 reviews

**Table:** `reviews`  
**Schema file:** `schema/reviews.sql`

```sql
CREATE TABLE IF NOT EXISTS reviews (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id        INTEGER      NOT NULL UNIQUE REFERENCES orders(id) ON DELETE CASCADE,
    restaurant_id   INTEGER      NOT NULL REFERENCES restaurants(id) ON DELETE CASCADE,
    customer_id     INTEGER      REFERENCES customers(id) ON DELETE SET NULL,
    rating          INTEGER      NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment         TEXT,
    owner_response  TEXT,
    created_at      DATETIME     NOT NULL DEFAULT (datetime('now')),
    updated_at      DATETIME     NOT NULL DEFAULT (datetime('now'))
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Auto-increment PK |
| `order_id` | INTEGER | NO | FK → orders (one review per order) |
| `restaurant_id` | INTEGER | NO | FK → restaurants |
| `customer_id` | INTEGER | YES | FK → customers |
| `rating` | INTEGER | NO | 1–5 |
| `comment` | TEXT | YES | Review text (max 1000 chars) |
| `owner_response` | TEXT | YES | Restaurant reply |
| `created_at` | DATETIME | NO | |
| `updated_at` | DATETIME | NO | |

---

### 8.13 payments

**Table:** `payments`  
**Schema file:** `schema/payments.sql`

```sql
CREATE TABLE IF NOT EXISTS payments (
    id                  VARCHAR(64)  PRIMARY KEY,
    restaurant_order_id VARCHAR(32)  NOT NULL,
    order_id            INTEGER      REFERENCES orders(id) ON DELETE SET NULL,
    razorpay_order_id   VARCHAR(64),
    razorpay_payment_id VARCHAR(64),
    amount              REAL         NOT NULL,
    currency            VARCHAR(10)  NOT NULL DEFAULT 'INR',
    status              VARCHAR(20)  NOT NULL DEFAULT 'created'
                        CHECK (status IN ('created','paid','failed','cancelled')),
    method              VARCHAR(30),
    created_at          DATETIME     NOT NULL DEFAULT (datetime('now')),
    updated_at          DATETIME     NOT NULL DEFAULT (datetime('now'))
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | VARCHAR(64) | NO | Payment record ID (pay_xxx) |
| `restaurant_order_id` | VARCHAR(32) | NO | FK → orders.order_id |
| `order_id` | INTEGER | YES | FK → orders.id |
| `razorpay_order_id` | VARCHAR(64) | YES | Razorpay order ID |
| `razorpay_payment_id` | VARCHAR(64) | YES | Razorpay payment ID |
| `amount` | REAL | NO | Amount in INR |
| `currency` | VARCHAR(10) | NO | Default: INR |
| `status` | VARCHAR(20) | NO | created / paid / failed / cancelled |
| `method` | VARCHAR(30) | YES | upi, card, netbanking, wallet |
| `created_at` | DATETIME | NO | |
| `updated_at` | DATETIME | NO | |

---

### 8.14 audit_logs

**Table:** `audit_logs`  
**Schema file:** `schema/audit_logs.sql`

```sql
CREATE TABLE IF NOT EXISTS audit_logs (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER      REFERENCES users(id) ON DELETE SET NULL,
    action          VARCHAR(80)  NOT NULL,
    entity_type     VARCHAR(50)  NOT NULL,
    entity_id       VARCHAR(50)  NOT NULL,
    details         TEXT,         -- JSON change payload
    ip_address      VARCHAR(45),
    created_at      DATETIME     NOT NULL DEFAULT (datetime('now'))
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Auto-increment PK |
| `user_id` | INTEGER | YES | FK → users |
| `action` | VARCHAR(80) | NO | e.g., `order.status_update` |
| `entity_type` | VARCHAR(50) | NO | e.g., `order`, `menu_item` |
| `entity_id` | VARCHAR(50) | NO | ID of affected entity |
| `details` | TEXT (JSON) | YES | Change payload |
| `ip_address` | VARCHAR(45) | YES | Request IP |
| `created_at` | DATETIME | NO | |

---

### 8.15 platform_settings

**Table:** `platform_settings`  
**Schema file:** `schema/platform_settings.sql`

```sql
CREATE TABLE IF NOT EXISTS platform_settings (
    id                      INTEGER PRIMARY KEY AUTOINCREMENT,
    platform_name           VARCHAR(120) NOT NULL DEFAULT 'Restaurant Platform',
    default_tax_rate        REAL         NOT NULL DEFAULT 0.05,
    loyalty_points_per_rupee REAL,
    order_id_prefix         VARCHAR(10)  NOT NULL DEFAULT 'ORD',
    featured_restaurant_ids TEXT,         -- JSON array of restaurant IDs
    maintenance_mode        BOOLEAN      NOT NULL DEFAULT 0,
    updated_at              DATETIME     NOT NULL DEFAULT (datetime('now'))
);
```

| Column | Type | Nullable | Description |
|--------|------|----------|-------------|
| `id` | INTEGER | NO | Single-row config (id = 1) |
| `platform_name` | VARCHAR(120) | NO | SaaS platform name |
| `default_tax_rate` | REAL | NO | e.g., 0.05 |
| `loyalty_points_per_rupee` | REAL | YES | Points earning rate |
| `order_id_prefix` | VARCHAR(10) | NO | Default: ORD |
| `featured_restaurant_ids` | TEXT (JSON) | YES | Platform homepage |
| `maintenance_mode` | BOOLEAN | NO | Default: false |
| `updated_at` | DATETIME | NO | |

Restaurant-specific settings (working hours, hero slides, featured dishes) live on the `restaurants` table. Platform-wide settings live in `platform_settings`.

---

### 8.16 Schema Init Script

**File:** `schema/00_init.sql`

```sql
-- Master init: run all table DDL in dependency order
-- Applied by scripts/apply_schema.py or init_db()

.read schema/users.sql          -- Note: users FK to restaurants deferred; see circular FK note below
.read schema/restaurants.sql
.read schema/branches.sql
.read schema/menus.sql
.read schema/menu_items.sql
.read schema/customers.sql
.read schema/customer_addresses.sql
.read schema/delivery_partners.sql
.read schema/campaigns.sql
.read schema/orders.sql
.read schema/order_items.sql
.read schema/loyalty_points.sql
.read schema/reviews.sql
.read schema/payments.sql
.read schema/audit_logs.sql
.read schema/platform_settings.sql
.read schema/indexes.sql
```

**Circular FK note:** `users.restaurant_id` references `restaurants`, and `restaurants.owner_user_id` references `users`. Resolution: create `users` table first without FK constraints, create `restaurants`, then `ALTER TABLE users ADD CONSTRAINT ...` — or use deferred constraint checking. The `apply_schema.py` script handles this ordering.

---

### 8.17 Indexes

**File:** `schema/indexes.sql`

```sql
CREATE INDEX IF NOT EXISTS idx_users_restaurant_id     ON users(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_branches_restaurant_id  ON branches(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_menus_restaurant_id     ON menus(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_menu_items_restaurant   ON menu_items(restaurant_id, category);
CREATE INDEX IF NOT EXISTS idx_menu_items_menu_id      ON menu_items(menu_id);
CREATE INDEX IF NOT EXISTS idx_customers_phone         ON customers(phone);
CREATE INDEX IF NOT EXISTS idx_customers_user_id       ON customers(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_restaurant_status ON orders(restaurant_id, status);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id      ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id    ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_delivery_restaurant_id  ON delivery_partners(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_loyalty_customer        ON loyalty_points(customer_id, restaurant_id);
CREATE INDEX IF NOT EXISTS idx_campaigns_restaurant    ON campaigns(restaurant_id, status);
CREATE INDEX IF NOT EXISTS idx_reviews_restaurant_id   ON reviews(restaurant_id);
CREATE INDEX IF NOT EXISTS idx_payments_order_id       ON payments(order_id);
CREATE INDEX IF NOT EXISTS idx_payments_rest_order_id  ON payments(restaurant_order_id);
CREATE INDEX IF NOT EXISTS idx_audit_entity            ON audit_logs(entity_type, entity_id);
```

---

## 9. API Specification

All endpoints are prefixed with `/api`. Existing endpoints are marked with ✅.

### 9.1 Authentication

| Method | Endpoint | Auth | Status | Description |
|--------|----------|------|--------|-------------|
| POST | `/auth/register` | Public | **NEW** | Register customer account |
| POST | `/auth/login` | Public | ✅ Extend | Login (all roles) |
| POST | `/auth/refresh` | Public | ✅ | Refresh access token |
| GET | `/auth/me` | JWT | ✅ Extend | Current user profile |
| POST | `/auth/register/restaurant` | Public/Admin | **NEW** | Restaurant owner registration |

### 9.2 Restaurants

| Method | Endpoint | Auth | Status | Description |
|--------|----------|------|--------|-------------|
| GET | `/restaurants` | Public | **NEW** | List active restaurants |
| GET | `/restaurants/{id}` | Public | **NEW** | Restaurant details |
| POST | `/restaurants` | Platform Admin | **NEW** | Create restaurant |
| PUT | `/restaurants/{id}` | Owner/Admin | **NEW** | Update restaurant |
| GET | `/restaurants/{id}/branches` | Public | **NEW** | List branches |

### 9.3 Branches

| Method | Endpoint | Auth | Status | Description |
|--------|----------|------|--------|-------------|
| GET | `/branches/{id}` | Public | **NEW** | Branch details |
| POST | `/restaurants/{restaurant_id}/branches` | Owner | **NEW** | Create branch |
| PUT | `/branches/{id}` | Owner | **NEW** | Update branch |
| DELETE | `/branches/{id}` | Owner | **NEW** | Deactivate branch |

### 9.4 Menu

| Method | Endpoint | Auth | Status | Description |
|--------|----------|------|--------|-------------|
| GET | `/menu` | Public | ✅ Extend | List menu (filter by restaurant/branch) |
| GET | `/menu/{id}` | Public | ✅ | Get menu item |
| POST | `/menu` | Owner/Staff | ✅ Extend | Create menu item |
| PUT | `/menu/{id}` | Owner/Staff | ✅ Extend | Update menu item |
| DELETE | `/menu/{id}` | Owner | ✅ Extend | Delete menu item |
| GET | `/menu/categories` | Public | **NEW** | List categories for restaurant |

### 9.5 Orders

| Method | Endpoint | Auth | Status | Description |
|--------|----------|------|--------|-------------|
| POST | `/orders` | Public/Customer | ✅ Extend | Place order |
| GET | `/orders` | Owner/Staff/Admin | ✅ Extend | List orders (paginated, filtered) |
| GET | `/orders/{id}` | Owner/Staff/Customer | ✅ Extend | Order details |
| PUT | `/orders/{id}/status` | Owner/Staff | ✅ Extend | Update order status |
| GET | `/orders/track/{order_id}` | Public | ✅ | Track order (public) |
| PUT | `/orders/{id}/assign-delivery` | Owner/Staff | **NEW** | Assign delivery partner |
| GET | `/orders/my` | Customer | **NEW** | Customer order history |

### 9.6 Customers

| Method | Endpoint | Auth | Status | Description |
|--------|----------|------|--------|-------------|
| GET | `/customers/me` | Customer | **NEW** | Own profile |
| PUT | `/customers/me` | Customer | **NEW** | Update profile |
| GET | `/customers/me/orders` | Customer | **NEW** | Order history |
| GET | `/customers/me/loyalty` | Customer | **NEW** | Loyalty points balance & history |

### 9.7 Delivery

| Method | Endpoint | Auth | Status | Description |
|--------|----------|------|--------|-------------|
| GET | `/delivery/partners` | Owner | **NEW** | List delivery partners |
| POST | `/delivery/partners` | Owner | **NEW** | Register delivery partner |
| PUT | `/delivery/partners/{id}` | Owner/Partner | **NEW** | Update partner |
| GET | `/delivery/assignments` | Partner | **NEW** | Partner's active deliveries |
| PUT | `/delivery/assignments/{order_id}/status` | Partner | **NEW** | Update delivery status |

### 9.8 Campaigns

| Method | Endpoint | Auth | Status | Description |
|--------|----------|------|--------|-------------|
| GET | `/campaigns` | Owner | **NEW** | List campaigns |
| POST | `/campaigns` | Owner | **NEW** | Create campaign |
| PUT | `/campaigns/{id}` | Owner | **NEW** | Update campaign |
| GET | `/campaigns/active` | Public | **NEW** | Active campaigns for restaurant |

### 9.9 Reviews

| Method | Endpoint | Auth | Status | Description |
|--------|----------|------|--------|-------------|
| POST | `/reviews` | Customer | **NEW** | Submit review |
| GET | `/reviews/restaurant/{id}` | Public | **NEW** | Restaurant reviews |
| PUT | `/reviews/{id}/respond` | Owner | **NEW** | Owner response |

### 9.10 Dashboard & Analytics

| Method | Endpoint | Auth | Status | Description |
|--------|----------|------|--------|-------------|
| GET | `/dashboard/stats` | Owner/Staff | ✅ Extend | Today's statistics |
| GET | `/dashboard/revenue` | Owner | ✅ Extend | Revenue chart data |
| GET | `/dashboard/orders` | Owner/Staff | ✅ Extend | Orders by status |
| GET | `/dashboard/top-items` | Owner | **NEW** | Top-selling items |
| GET | `/dashboard/customers` | Owner | **NEW** | Customer metrics |
| GET | `/admin/platform-stats` | Platform Admin | **NEW** | Platform-wide stats |

### 9.11 Payments (Razorpay — Unchanged)

| Method | Endpoint | Auth | Status | Description |
|--------|----------|------|--------|-------------|
| GET | `/payments/config` | Public | ✅ | Razorpay public config |
| POST | `/payments/checkout` | Public | ✅ | Create checkout session |
| POST | `/payments/verify` | Public | ✅ | Verify payment signature |
| POST | `/payments/failed` | Public | ✅ | Record failed payment |
| GET | `/payments` | Owner/Admin | ✅ | List payment records |

### 9.12 Settings

| Method | Endpoint | Auth | Status | Description |
|--------|----------|------|--------|-------------|
| GET | `/settings` | Public | ✅ Extend | Restaurant/platform settings |
| PUT | `/settings` | Owner/Admin | **NEW** | Update settings |

### 9.13 AI Endpoints (Deferred — Stub Only)

| Method | Endpoint | Status | Description |
|--------|----------|--------|-------------|
| POST | `/ai/recommend` | **STUB** | Returns 501 Not Implemented |
| POST | `/ai/chat` | **STUB** | Returns 501 Not Implemented |

Stub endpoints return `{ "detail": "AI features are not yet available" }` with HTTP 501.

---

## 10. Frontend Specification

### 10.1 Pages

| Route | Page | Role | Status |
|-------|------|------|--------|
| `/` | Landing Page | Public | ✅ Exists (extend for multi-restaurant) |
| `/login` | Login | Public | **NEW** (customer + role-based redirect) |
| `/register` | Register | Public | **NEW** |
| `/menu` | Menu | Public | ✅ Exists |
| `/cart` | Cart | Public | ✅ Exists |
| `/checkout` | Checkout | Public | ✅ Exists (add delivery option) |
| `/order-success` | Order Success | Public | ✅ Exists |
| `/payment-failed` | Payment Failed | Public | ✅ Exists |
| `/payment-cancelled` | Payment Cancelled | Public | ✅ Exists |
| `/track-order/:id` | Order Tracker | Public | ✅ Exists (extend for delivery) |
| `/customer/dashboard` | Customer Dashboard | Customer | **NEW** |
| `/customer/orders` | Order History | Customer | **NEW** |
| `/customer/loyalty` | Loyalty Points | Customer | **NEW** |
| `/admin/login` | Admin Login | Public | ✅ Exists (extend for all roles) |
| `/admin/dashboard` | Restaurant Dashboard | Owner/Staff | ✅ Exists |
| `/admin/menu` | Menu Management | Owner/Staff | ✅ Exists |
| `/admin/orders` | Orders Dashboard | Owner/Staff | ✅ Exists |
| `/admin/branches` | Branch Management | Owner | **NEW** |
| `/admin/delivery` | Delivery Management | Owner | **NEW** |
| `/admin/campaigns` | Campaign Management | Owner | **NEW** |
| `/admin/reviews` | Reviews | Owner | **NEW** |
| `/admin/analytics` | Analytics Dashboard | Owner | **NEW** (extend dashboard) |
| `/admin/settings` | Settings | Owner | **NEW** |
| `/delivery/dashboard` | Delivery Dashboard | Delivery Partner | **NEW** |
| `/platform/dashboard` | Platform Admin Dashboard | Platform Admin | **NEW** |
| `/platform/restaurants` | Restaurant Management | Platform Admin | **NEW** |

### 10.2 Components

| Component | Status | Notes |
|-----------|--------|-------|
| Navbar | ✅ Exists | Add role-aware navigation |
| Menu Cards | ✅ Exists | |
| Cart | ✅ Exists | |
| Order Tracker | ✅ Exists | Extend for delivery stages |
| Analytics Charts | ✅ Exists | Extend with new metrics |
| Chat Widget | **STUB** | Placeholder UI, no AI backend |
| StatusBadge | ✅ Exists | |
| Breadcrumbs | ✅ Exists | |
| CampaignBanner | **NEW** | Display active campaigns |
| ReviewForm | **NEW** | Post-order review |
| ReviewList | **NEW** | Restaurant reviews display |
| BranchSelector | **NEW** | Branch picker on menu/checkout |
| DeliveryAssignment | **NEW** | Admin delivery assignment panel |
| LoyaltyPointsCard | **NEW** | Customer loyalty display |

### 10.3 Role-Based Routing

After login, redirect based on role:
- `customer` → `/customer/dashboard`
- `restaurant_owner` / `restaurant_staff` → `/admin/dashboard`
- `delivery_partner` → `/delivery/dashboard`
- `platform_admin` → `/platform/dashboard`

Existing `/admin/login` continues to work; unified `/login` page added for all roles.

---

## 11. Security

| Requirement | Implementation |
|-------------|---------------|
| JWT Authentication | Access token (60 min) + refresh token — existing |
| Role-Based Access Control | Middleware checks `role` claim against endpoint permissions |
| Password Hashing | bcrypt — existing |
| Rate Limiting | Add per-IP rate limiting on auth and order endpoints (Phase 1) |
| Audit Logging | All write operations logged to `audit_logs` SQL table |
| Input Validation | Pydantic models (API) + SQL constraints (DB) |
| CORS | Configurable origins — existing |
| Payment Security | Razorpay server-side signature verification — existing |
| Data Isolation | Restaurant-scoped queries enforce `restaurant_id` filter for owner/staff |

---

## 12. Migration from Current Application

### Phase 0: Schema & Data Migration (First Implementation Step)

1. Create `schema/` folder with all `.sql` DDL files (§8).
2. Create `scripts/apply_schema.py` to execute schema files against SQLite.
3. Migrate `menu.json` → `menus` + `menu_items` SQL tables.
4. Migrate `settings.json` → `restaurants` table + `platform_settings` table.
5. Migrate `users.json` → `users` SQL table (role `admin` → `restaurant_owner`).
6. Migrate `payments.json` → `payments` SQL table.
7. Extend existing SQLite `orders` / `order_items` tables with new columns (`restaurant_id`, `branch_id`, `customer_id`, `delivery_*`, `campaign_id`, `discount_amount`).
8. Extend existing `audit_logs` table with `user_id`, `ip_address` columns.
9. Create new tables: `branches`, `customers`, `customer_addresses`, `delivery_partners`, `loyalty_points`, `campaigns`, `reviews`.
10. Replace JSON-file repositories with raw SQL repositories (parameterized queries against `schema/` tables).
11. Remove `backend/app/models/` SQLAlchemy layer; use `database/connection.py` + repository SQL only.
12. Update seed script to insert via raw SQL.
13. Remove unused JSON data files from `backend/data/` after migration verified.

### Data Mapping

| Current Source | Target SQL Table | Action |
|----------------|------------------|--------|
| `menu.json` → `items[]` | `menu_items` | Import; add `menu_id`, `restaurant_id` |
| `menu.json` → `categories[]` | `menus.categories` (JSON column) | Wrap in menu row |
| `settings.json` | `restaurants` + `platform_settings` | Split platform vs restaurant fields |
| `users.json` (role: admin) | `users` (role: restaurant_owner) | Import; add `restaurant_id` FK |
| SQLite `orders` | `orders` (extended) | ALTER TABLE + backfill `restaurant_id` |
| SQLite `order_items` | `order_items` | Retain; add FK to `menu_items` |
| SQLite `audit_logs` | `audit_logs` (extended) | ALTER TABLE |
| `payments.json` | `payments` | Import into SQL table |

### Backward Compatibility Guarantees

- All existing API endpoints remain functional (same paths, extended response shapes).
- Existing frontend pages continue to work without changes in Phase 1.
- Razorpay payment flow is untouched.
- Default restaurant ("Hotel Abhi ruchi") is auto-created from current settings.
- Admin credentials remain valid.
- SQLite database file path unchanged (`backend/database/restaurant.db`).

---

## 13. Implementation Phases

### Phase 1 — Foundation (MVP)

**Goal:** Full SQL schema, multi-role auth, restaurant entity, backward-compatible ordering.

- [ ] Create `schema/` folder with all `.sql` DDL files
- [ ] Create `scripts/apply_schema.py`
- [ ] Migrate JSON data files → SQL tables
- [ ] Extend existing SQLite tables with new columns
- [ ] Implement raw SQL repositories for all 16 tables (no ORM models)
- [ ] Add `database/connection.py` and shared query helpers
- [ ] Remove existing SQLAlchemy `models/` layer
- [ ] Extend auth for 5 roles + customer registration
- [ ] Update seed data script
- [ ] Preserve all existing endpoints and Razorpay flow
- [ ] Add stub AI endpoints (501)
- [ ] Update README

### Phase 2 — Customer & Delivery

- [ ] Customer registration, profile, order history
- [ ] Customer dashboard (frontend)
- [ ] Delivery order type + delivery partner management
- [ ] Delivery assignment and tracking
- [ ] Delivery partner dashboard (frontend)

### Phase 3 — Loyalty & Marketing

- [ ] Loyalty points earn on order completion
- [ ] Loyalty points display (customer dashboard)
- [ ] Campaign CRUD (owner admin)
- [ ] Active campaign display (customer-facing)
- [ ] Promo code application at checkout

### Phase 4 — Reviews & Analytics

- [ ] Review submission and display
- [ ] Owner review response
- [ ] Extended analytics (top items, customer metrics)
- [ ] Platform admin dashboard

### Phase 5 — AI Layer (Future — Not This Project)

- AI Ordering Assistant
- AI Recommendations
- Vector database integration
- WhatsApp AI Agent

---

## 14. Future Enhancements (Out of Scope)

- Voice ordering
- WhatsApp AI agent and promotions
- Multi-restaurant marketplace (customer browses multiple restaurants)
- Demand forecasting
- Autonomous marketing agent
- Redis caching layer
- PostgreSQL production deployment (schema files are forward-compatible)

---

## 15. Success Metrics

| KPI | Target | Measurement |
|-----|--------|-------------|
| Direct order percentage | Track baseline → growth | Orders via platform / total orders |
| Repeat customer rate | > 30% within 3 months | Unique customers with 2+ orders |
| Order completion rate | > 95% | Delivered / total placed |
| Payment success rate | > 90% | Paid / checkout initiated |
| API response time | < 200ms p95 | Health endpoint + order placement |
| Platform uptime | 99.5% | Health check monitoring |

---

## 16. Approval Checklist

Before implementation begins, please confirm:

- [ ] **Scope** — Feature set in §2 and §6 is acceptable
- [ ] **Exclusions** — AI features deferred; stub endpoints only
- [ ] **Data model** — All 16 SQL tables in §8 are correct
- [ ] **SQL storage** — SQLite (dev) / PostgreSQL (prod) approach is approved
- [ ] **Schema folder** — `.sql` DDL files in `schema/` as specified
- [ ] **API design** — Endpoints in §9 cover requirements
- [ ] **Frontend pages** — Routes in §10 are sufficient
- [ ] **Migration plan** — §12 backward compatibility approach is acceptable
- [ ] **Implementation phases** — §13 priority order is correct
- [ ] **No ORM** — Raw SQL schema + repositories only; no SQLAlchemy models
- [ ] **Preserved features** — Razorpay, existing admin flow, order tracking remain intact

---

**Next step after approval:** Implement Phase 1 — create `schema/` folder with raw `.sql` files, run migrations, implement raw SQL repositories (no ORM).
