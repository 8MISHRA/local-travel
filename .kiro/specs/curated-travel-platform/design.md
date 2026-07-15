# Design Document: Curated Travel Platform

## Overview

This document defines the architecture and technical design for the Curated Travel Platform Flask backend. The system provides a RESTful API serving Varanasi and Mirzapur travel experiences with end-to-end trip management including scouts, drivers, hotels, packages, bookings, and payments.

## Tech Stack

- **Framework**: Flask with Blueprints
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Migrations**: Alembic
- **Serialization/Validation**: Marshmallow
- **Authentication**: PyJWT (access + refresh tokens)
- **Caching/Rate Limiting**: Redis-ready (flask-limiter)
- **Background Tasks**: Celery-ready
- **WSGI Server**: Gunicorn
- **Containerization**: Docker + Docker Compose

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway / Nginx                        │
└────────────────────────────────┬────────────────────────────────┘
                                 │
┌────────────────────────────────▼────────────────────────────────┐
│                     Flask Application (Gunicorn)                  │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────────┐  │
│  │  Routes   │→ │ Services  │→ │   Repos   │→ │   Models    │  │
│  │(Blueprints│  │(Biz Logic)│  │(Data Layer│  │(SQLAlchemy) │  │
│  └───────────┘  └───────────┘  └───────────┘  └─────────────┘  │
│        ↑              ↑                                          │
│  ┌─────┴────┐   ┌────┴─────┐                                   │
│  │Middleware │   │ Schemas  │                                   │
│  │(Auth,CORS)│   │(Marshmallow)                                 │
│  └──────────┘   └──────────┘                                   │
└──────────┬──────────────┬───────────────┬───────────────────────┘
           │              │               │
    ┌──────▼──────┐ ┌────▼────┐   ┌──────▼──────┐
    │ PostgreSQL  │ │  Redis  │   │   Celery    │
    │  Database   │ │ (Cache/ │   │  (Async     │
    │             │ │  Rate)  │   │   Tasks)    │
    └─────────────┘ └─────────┘   └─────────────┘
```


## Project Structure

```
app/
├── __init__.py                 # Flask app factory
├── config.py                   # Configuration classes (dev, test, prod)
├── extensions.py               # SQLAlchemy, Marshmallow, JWT, Migrate instances
├── api/
│   └── v1/
│       ├── __init__.py         # v1 blueprint registration
│       ├── auth/
│       │   ├── __init__.py
│       │   ├── routes.py       # /api/v1/auth/* endpoints
│       │   └── schemas.py      # Registration/login schemas
│       ├── packages/
│       │   ├── __init__.py
│       │   ├── routes.py
│       │   └── schemas.py
│       ├── bookings/
│       │   ├── __init__.py
│       │   ├── routes.py
│       │   └── schemas.py
│       ├── destinations/
│       ├── hotels/
│       ├── scouts/
│       ├── drivers/
│       ├── payments/
│       ├── invoices/
│       ├── reviews/
│       ├── gallery/
│       ├── blog/
│       ├── enterprise/
│       ├── coupons/
│       ├── wishlist/
│       ├── notifications/
│       ├── support/
│       └── health/
├── models/
│   ├── __init__.py
│   ├── base.py                 # Base model with audit columns
│   ├── user.py
│   ├── package.py
│   ├── booking.py
│   ├── hotel.py
│   ├── scout.py
│   ├── driver.py
│   ├── payment.py
│   ├── invoice.py
│   ├── review.py
│   ├── gallery.py
│   ├── blog.py
│   ├── enterprise.py
│   ├── coupon.py
│   ├── wishlist.py
│   ├── notification.py
│   ├── support.py
│   └── audit_log.py
├── services/
│   ├── __init__.py
│   ├── auth_service.py
│   ├── package_service.py
│   ├── booking_service.py
│   ├── hotel_service.py
│   ├── scout_service.py
│   ├── driver_service.py
│   ├── payment_service.py
│   ├── invoice_service.py
│   ├── review_service.py
│   ├── gallery_service.py
│   ├── blog_service.py
│   ├── enterprise_service.py
│   ├── coupon_service.py
│   ├── wishlist_service.py
│   ├── notification_service.py
│   └── support_service.py
├── repositories/
│   ├── __init__.py
│   ├── base_repository.py     # Generic CRUD + soft delete + pagination
│   ├── user_repository.py
│   ├── package_repository.py
│   ├── booking_repository.py
│   ├── hotel_repository.py
│   ├── scout_repository.py
│   ├── driver_repository.py
│   ├── payment_repository.py
│   ├── invoice_repository.py
│   ├── review_repository.py
│   └── ...
├── middleware/
│   ├── __init__.py
│   ├── auth_middleware.py      # JWT validation decorator
│   ├── rbac_middleware.py      # Role-based access decorator
│   ├── rate_limiter.py         # Rate limiting middleware
│   └── request_logger.py      # Structured request logging
├── utils/
│   ├── __init__.py
│   ├── response.py            # Standard API response helpers
│   ├── pagination.py          # Pagination helper
│   ├── exceptions.py          # Custom exception classes
│   └── audit.py               # Audit log helper
├── celery_app.py              # Celery configuration
└── errors.py                  # Global error handlers
migrations/                    # Alembic migration files
tests/
├── conftest.py
├── unit/
├── integration/
└── property/
docker-compose.yml
Dockerfile
gunicorn.conf.py
requirements.txt
.env.example
```


## Components and Interfaces

### Layer Responsibilities

| Layer | Responsibility | Rules |
|-------|---------------|-------|
| Routes (Blueprints) | HTTP handling, request parsing, response formatting | No business logic. Delegates to services. |
| Schemas (Marshmallow) | Input validation, serialization, deserialization | Defines field constraints and nested relationships. |
| Services | Business logic, orchestration, workflow rules | Stateless. Raises domain exceptions. |
| Repositories | Data access, query building, pagination | Encapsulates SQLAlchemy queries. Returns models. |
| Models (SQLAlchemy) | ORM mapping, relationships, column definitions | No business logic. Audit columns via mixin. |
| Middleware | Cross-cutting concerns (auth, logging, rate limiting) | Decorators or before/after request hooks. |

### Base Model Mixin

```python
from app.extensions import db
from datetime import datetime, timezone
import uuid

class AuditMixin:
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    deleted_at = db.Column(db.DateTime, nullable=True)

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    def soft_delete(self):
        self.deleted_at = datetime.now(timezone.utc)
```

### Base Repository

```python
class BaseRepository:
    model_class = None

    def __init__(self, session):
        self.session = session

    def get_by_id(self, entity_id):
        return self.session.query(self.model_class).filter(
            self.model_class.id == entity_id,
            self.model_class.deleted_at.is_(None)
        ).first()

    def list_paginated(self, page=1, per_page=20, filters=None, sort_by=None):
        query = self.session.query(self.model_class).filter(
            self.model_class.deleted_at.is_(None)
        )
        if filters:
            query = self._apply_filters(query, filters)
        if sort_by:
            query = self._apply_sorting(query, sort_by)
        total = query.count()
        items = query.offset((page - 1) * per_page).limit(per_page).all()
        return items, total

    def create(self, **kwargs):
        instance = self.model_class(**kwargs)
        self.session.add(instance)
        self.session.flush()
        return instance

    def soft_delete(self, entity_id):
        entity = self.get_by_id(entity_id)
        if entity:
            entity.soft_delete()
        return entity
```


### Standard API Response Helpers

```python
def success_response(data, message="Success", status_code=200):
    return {"success": True, "data": data, "message": message}, status_code

def error_response(code, message, details=None, status_code=400):
    return {
        "success": False,
        "error": {"code": code, "message": message, "details": details}
    }, status_code

def paginated_response(items, total, page, per_page, schema):
    return {
        "success": True,
        "data": schema.dump(items, many=True),
        "pagination": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": (total + per_page - 1) // per_page
        },
        "message": "Success"
    }, 200
```

## Data Models

### Entity Relationship Overview

```
Users ─────┬──── Bookings ──── Payments ──── Invoices
           │         │
           │         ├──── BookingScouts
           │         ├──── BookingDrivers
           │         └──── BookingStatusHistory
           │
           ├──── Reviews
           ├──── Wishlists
           ├──── Notifications
           ├──── SupportTickets ──── TicketReplies
           │
Packages ──┼──── PricingTiers
           ├──── Itineraries
           └──── PackageImages (Gallery)

Destinations ──── SubDestinations

Hotels ──── RoomTypes ──── RoomAvailability

Scouts (extends Users)
Drivers (extends Users)

Coupons ──── CouponUsage
BlogPosts
EnterpriseBookings
AuditLogs
```


### Table Definitions

#### users

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID (String 36) | PK |
| email | String(255) | UNIQUE, NOT NULL, INDEX |
| password_hash | String(255) | NOT NULL |
| full_name | String(150) | NOT NULL |
| phone | String(20) | NOT NULL |
| role | Enum(guest,customer,scout,driver,vendor,hotel_partner,admin,super_admin) | NOT NULL, DEFAULT 'customer', INDEX |
| is_active | Boolean | DEFAULT true |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |
| deleted_at | DateTime | NULL, INDEX |

#### refresh_tokens

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK(users.id), NOT NULL, INDEX |
| token_hash | String(255) | UNIQUE, NOT NULL |
| expires_at | DateTime | NOT NULL |
| is_revoked | Boolean | DEFAULT false |
| created_at | DateTime | NOT NULL |

#### packages

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| title | String(255) | NOT NULL |
| slug | String(255) | UNIQUE, NOT NULL, INDEX |
| description | Text | NOT NULL |
| destination_id | UUID | FK(destinations.id), NOT NULL, INDEX |
| duration_days | Integer | NOT NULL |
| duration_nights | Integer | NOT NULL |
| traveller_type | Enum(solo,couple,family,group,corporate) | NOT NULL, INDEX |
| inclusions | JSONB | NOT NULL |
| exclusions | JSONB | NOT NULL |
| is_active | Boolean | DEFAULT true, INDEX |
| featured_image_url | String(500) | NULL |
| average_rating | Decimal(3,2) | DEFAULT 0.00 |
| total_reviews | Integer | DEFAULT 0 |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |
| deleted_at | DateTime | NULL |

#### pricing_tiers

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| package_id | UUID | FK(packages.id), NOT NULL, INDEX |
| tier_name | String(50) | NOT NULL (per_person, couple, family, group) |
| price | Decimal(10,2) | NOT NULL |
| max_persons | Integer | NULL |
| description | String(255) | NULL |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |

**Unique constraint**: (package_id, tier_name)


#### itineraries

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| package_id | UUID | FK(packages.id), NOT NULL, INDEX |
| day_number | Integer | NOT NULL |
| title | String(255) | NOT NULL |
| description | Text | NOT NULL |
| activities | JSONB | NOT NULL |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |

**Unique constraint**: (package_id, day_number)

#### destinations

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| name | String(100) | NOT NULL, UNIQUE |
| description | Text | NULL |
| is_primary | Boolean | DEFAULT false |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |
| deleted_at | DateTime | NULL |

#### sub_destinations

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| destination_id | UUID | FK(destinations.id), NOT NULL, INDEX |
| name | String(150) | NOT NULL |
| description | Text | NULL |
| latitude | Decimal(10,8) | NULL |
| longitude | Decimal(11,8) | NULL |
| category | Enum(ghat,temple,waterfall,hidden_place,market,food_spot,cultural_site) | NOT NULL, INDEX |
| media_urls | JSONB | NULL |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |
| deleted_at | DateTime | NULL |

#### bookings

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| booking_number | String(20) | UNIQUE, NOT NULL, INDEX |
| customer_id | UUID | FK(users.id), NOT NULL, INDEX |
| package_id | UUID | FK(packages.id), NOT NULL, INDEX |
| status | Enum(draft,pending_payment,confirmed,in_progress,completed,cancelled,refunded) | NOT NULL, INDEX |
| travel_start_date | Date | NOT NULL |
| travel_end_date | Date | NOT NULL |
| num_travellers | Integer | NOT NULL |
| traveller_type | String(50) | NOT NULL |
| hotel_preference_id | UUID | FK(hotels.id), NULL |
| room_type_id | UUID | FK(room_types.id), NULL |
| transport_preferences | JSONB | NULL |
| add_ons | JSONB | NULL |
| subtotal | Decimal(12,2) | NULL |
| discount_amount | Decimal(12,2) | DEFAULT 0.00 |
| tax_amount | Decimal(12,2) | NULL |
| total_amount | Decimal(12,2) | NULL |
| coupon_id | UUID | FK(coupons.id), NULL |
| special_requests | Text | NULL |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |
| deleted_at | DateTime | NULL |


#### booking_status_history

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| booking_id | UUID | FK(bookings.id), NOT NULL, INDEX |
| from_status | String(30) | NULL |
| to_status | String(30) | NOT NULL |
| changed_by | UUID | FK(users.id), NOT NULL |
| notes | Text | NULL |
| created_at | DateTime | NOT NULL |

#### booking_scouts

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| booking_id | UUID | FK(bookings.id), NOT NULL, INDEX |
| scout_id | UUID | FK(scouts.id), NOT NULL, INDEX |
| assigned_at | DateTime | NOT NULL |
| assigned_by | UUID | FK(users.id), NOT NULL |

**Unique constraint**: (booking_id, scout_id)

#### booking_drivers

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| booking_id | UUID | FK(bookings.id), NOT NULL, INDEX |
| driver_id | UUID | FK(drivers.id), NOT NULL, INDEX |
| assigned_at | DateTime | NOT NULL |
| assigned_by | UUID | FK(users.id), NOT NULL |

**Unique constraint**: (booking_id, driver_id)

#### hotels

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| partner_user_id | UUID | FK(users.id), NOT NULL, INDEX |
| name | String(255) | NOT NULL |
| address | Text | NOT NULL |
| destination_id | UUID | FK(destinations.id), NOT NULL, INDEX |
| star_rating | Integer | NOT NULL (1-5) |
| amenities | JSONB | NULL |
| contact_email | String(255) | NULL |
| contact_phone | String(20) | NULL |
| description | Text | NULL |
| is_active | Boolean | DEFAULT true |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |
| deleted_at | DateTime | NULL |

#### room_types

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| hotel_id | UUID | FK(hotels.id), NOT NULL, INDEX |
| name | String(100) | NOT NULL |
| capacity | Integer | NOT NULL |
| base_price | Decimal(10,2) | NOT NULL |
| description | Text | NULL |
| amenities | JSONB | NULL |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |

#### room_availability

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| room_type_id | UUID | FK(room_types.id), NOT NULL, INDEX |
| date | Date | NOT NULL |
| available_count | Integer | NOT NULL |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |

**Unique constraint**: (room_type_id, date)


#### scouts

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK(users.id), NOT NULL, UNIQUE |
| languages | JSONB | NOT NULL |
| specializations | JSONB | NULL |
| operating_area | Enum(varanasi, mirzapur) | NOT NULL, INDEX |
| is_available | Boolean | DEFAULT true, INDEX |
| average_rating | Decimal(3,2) | DEFAULT 0.00 |
| total_assignments | Integer | DEFAULT 0 |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |

#### scout_availability

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| scout_id | UUID | FK(scouts.id), NOT NULL, INDEX |
| date | Date | NOT NULL |
| is_available | Boolean | DEFAULT true |

**Unique constraint**: (scout_id, date)

#### drivers

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK(users.id), NOT NULL, UNIQUE |
| vehicle_type | String(50) | NOT NULL |
| vehicle_number | String(20) | NOT NULL |
| license_number | String(50) | NOT NULL |
| operating_area | Enum(varanasi, mirzapur) | NOT NULL, INDEX |
| is_available | Boolean | DEFAULT true, INDEX |
| average_rating | Decimal(3,2) | DEFAULT 0.00 |
| total_assignments | Integer | DEFAULT 0 |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |

#### driver_availability

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| driver_id | UUID | FK(drivers.id), NOT NULL, INDEX |
| date | Date | NOT NULL |
| is_available | Boolean | DEFAULT true |

**Unique constraint**: (driver_id, date)

#### payments

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| booking_id | UUID | FK(bookings.id), NOT NULL, INDEX |
| amount | Decimal(12,2) | NOT NULL |
| currency | String(3) | NOT NULL, DEFAULT 'INR' |
| payment_method | String(50) | NULL |
| gateway_transaction_id | String(255) | NULL, INDEX |
| status | Enum(pending, completed, failed, refunded) | NOT NULL, INDEX |
| gateway_response | JSONB | NULL |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |

#### refunds

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| payment_id | UUID | FK(payments.id), NOT NULL, INDEX |
| booking_id | UUID | FK(bookings.id), NOT NULL, INDEX |
| amount | Decimal(12,2) | NOT NULL |
| reason | Text | NULL |
| status | Enum(processing, completed, failed) | NOT NULL |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |


#### invoices

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| invoice_number | String(20) | UNIQUE, NOT NULL, INDEX |
| booking_id | UUID | FK(bookings.id), NOT NULL, INDEX |
| customer_id | UUID | FK(users.id), NOT NULL, INDEX |
| items | JSONB | NOT NULL |
| subtotal | Decimal(12,2) | NOT NULL |
| tax_amount | Decimal(12,2) | NOT NULL |
| discount_amount | Decimal(12,2) | DEFAULT 0.00 |
| total_amount | Decimal(12,2) | NOT NULL |
| issued_at | DateTime | NOT NULL |
| created_at | DateTime | NOT NULL |

#### reviews

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| customer_id | UUID | FK(users.id), NOT NULL, INDEX |
| booking_id | UUID | FK(bookings.id), NOT NULL, INDEX |
| package_id | UUID | FK(packages.id), NOT NULL, INDEX |
| entity_type | Enum(package, scout, driver) | NOT NULL |
| entity_id | UUID | NOT NULL, INDEX |
| rating | Integer | NOT NULL (1-5) |
| title | String(255) | NULL |
| body | Text | NULL |
| status | Enum(pending_moderation, published, rejected) | NOT NULL, DEFAULT 'pending_moderation', INDEX |
| rejection_reason | Text | NULL |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |
| deleted_at | DateTime | NULL |

#### gallery_images

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| entity_type | Enum(package, destination, hotel) | NOT NULL, INDEX |
| entity_id | UUID | NOT NULL, INDEX |
| filename | String(255) | NOT NULL |
| file_size | Integer | NOT NULL |
| mime_type | String(50) | NOT NULL |
| width | Integer | NULL |
| height | Integer | NULL |
| alt_text | String(255) | NULL |
| display_order | Integer | NOT NULL, DEFAULT 0 |
| storage_url | String(500) | NOT NULL |
| created_at | DateTime | NOT NULL |

#### blog_posts

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| title | String(255) | NOT NULL |
| slug | String(255) | UNIQUE, NOT NULL, INDEX |
| body | Text | NOT NULL |
| author_id | UUID | FK(users.id), NOT NULL, INDEX |
| category | String(100) | NOT NULL, INDEX |
| tags | JSONB | NULL |
| featured_image_url | String(500) | NULL |
| seo_title | String(255) | NULL |
| seo_description | String(500) | NULL |
| status | Enum(draft, published) | NOT NULL, DEFAULT 'draft', INDEX |
| published_at | DateTime | NULL |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |
| deleted_at | DateTime | NULL |


#### enterprise_bookings

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| customer_id | UUID | FK(users.id), NOT NULL, INDEX |
| company_name | String(255) | NOT NULL |
| contact_person | String(150) | NOT NULL |
| contact_email | String(255) | NOT NULL |
| contact_phone | String(20) | NOT NULL |
| group_size | Integer | NOT NULL (5-500) |
| travel_start_date | Date | NOT NULL |
| travel_end_date | Date | NOT NULL |
| destination_id | UUID | FK(destinations.id), NOT NULL |
| special_requirements | Text | NULL |
| budget_min | Decimal(12,2) | NULL |
| budget_max | Decimal(12,2) | NULL |
| status | Enum(pending_review, quotation_sent, confirmed, in_progress, completed, cancelled) | NOT NULL, DEFAULT 'pending_review' |
| quotation | JSONB | NULL |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |

#### coupons

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| code | String(50) | UNIQUE, NOT NULL, INDEX |
| discount_type | Enum(percentage, fixed) | NOT NULL |
| discount_value | Decimal(10,2) | NOT NULL |
| min_booking_amount | Decimal(12,2) | NULL |
| max_discount_cap | Decimal(12,2) | NULL |
| valid_from | DateTime | NOT NULL |
| valid_until | DateTime | NOT NULL |
| usage_limit | Integer | NULL |
| usage_count | Integer | DEFAULT 0 |
| is_active | Boolean | DEFAULT true |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |

#### wishlists

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| customer_id | UUID | FK(users.id), NOT NULL, INDEX |
| package_id | UUID | FK(packages.id), NOT NULL, INDEX |
| created_at | DateTime | NOT NULL |

**Unique constraint**: (customer_id, package_id)

#### notifications

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| user_id | UUID | FK(users.id), NOT NULL, INDEX |
| notification_type | String(50) | NOT NULL |
| title | String(255) | NOT NULL |
| body | Text | NOT NULL |
| reference_type | String(50) | NULL |
| reference_id | UUID | NULL |
| delivery_channel | Enum(in_app, email) | NOT NULL, DEFAULT 'in_app' |
| is_read | Boolean | DEFAULT false, INDEX |
| read_at | DateTime | NULL |
| created_at | DateTime | NOT NULL |

#### support_tickets

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| customer_id | UUID | FK(users.id), NOT NULL, INDEX |
| booking_id | UUID | FK(bookings.id), NULL, INDEX |
| subject | String(255) | NOT NULL |
| description | Text | NOT NULL |
| priority | Enum(low, medium, high, urgent) | NOT NULL, DEFAULT 'medium' |
| status | Enum(open, in_progress, resolved, closed) | NOT NULL, DEFAULT 'open', INDEX |
| created_at | DateTime | NOT NULL |
| updated_at | DateTime | NOT NULL |


#### ticket_replies

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| ticket_id | UUID | FK(support_tickets.id), NOT NULL, INDEX |
| author_id | UUID | FK(users.id), NOT NULL |
| body | Text | NOT NULL |
| created_at | DateTime | NOT NULL |

#### audit_logs

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| actor_id | UUID | FK(users.id), NOT NULL, INDEX |
| action | String(50) | NOT NULL (create, update, delete) |
| target_entity | String(100) | NOT NULL, INDEX |
| target_id | UUID | NOT NULL |
| changes | JSONB | NULL |
| created_at | DateTime | NOT NULL |

### Key Indexes

```sql
-- Performance indexes
CREATE INDEX idx_users_email ON users(email) WHERE deleted_at IS NULL;
CREATE INDEX idx_users_role ON users(role) WHERE deleted_at IS NULL;
CREATE INDEX idx_packages_destination ON packages(destination_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_packages_active ON packages(is_active) WHERE deleted_at IS NULL;
CREATE INDEX idx_bookings_customer ON bookings(customer_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_bookings_status ON bookings(status) WHERE deleted_at IS NULL;
CREATE INDEX idx_bookings_dates ON bookings(travel_start_date, travel_end_date);
CREATE INDEX idx_room_availability_lookup ON room_availability(room_type_id, date);
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = false;
CREATE INDEX idx_reviews_entity ON reviews(entity_type, entity_id) WHERE deleted_at IS NULL;
CREATE INDEX idx_audit_logs_actor ON audit_logs(actor_id, created_at);
CREATE INDEX idx_audit_logs_target ON audit_logs(target_entity, target_id);
```


## Authentication Flow

### Registration Flow

```
Client                    Auth Route              Auth Service             User Repo
  │                          │                        │                       │
  │─POST /api/v1/auth/register→                       │                       │
  │                          │──validate schema──→    │                       │
  │                          │                   check email exists──────────→│
  │                          │                        │←── user or None ──────│
  │                          │                   hash password (bcrypt)       │
  │                          │                   create user─────────────────→│
  │                          │                        │←── new user ──────────│
  │                          │                   generate access_token (JWT)  │
  │                          │                   generate refresh_token       │
  │                          │                   store refresh_token_hash     │
  │←─── 201 {tokens, user}──│                        │                       │
```

### Login Flow

```
Client                    Auth Route              Auth Service             User Repo
  │                          │                        │                       │
  │─POST /api/v1/auth/login──→                        │                       │
  │                          │──validate schema──→    │                       │
  │                          │                   find user by email──────────→│
  │                          │                        │←── user or None ──────│
  │                          │                   verify password (bcrypt)     │
  │                          │                   generate access_token        │
  │                          │                   generate refresh_token       │
  │                          │                   store refresh_token_hash     │
  │←─── 200 {tokens, user}──│                        │                       │
```

### Token Refresh Flow

```
Client                    Auth Route              Auth Service           Token Repo
  │                          │                        │                       │
  │─POST /api/v1/auth/refresh→                        │                       │
  │  {refresh_token}         │──validate──→           │                       │
  │                          │                   find token by hash──────────→│
  │                          │                        │←── token record ──────│
  │                          │                   verify not expired/revoked   │
  │                          │                   revoke old token────────────→│
  │                          │                   generate new pair            │
  │                          │                   store new refresh_token      │
  │←─── 200 {new tokens}────│                        │                       │
```

### JWT Token Structure

```python
# Access Token Payload (15 min TTL)
{
    "sub": "user_uuid",
    "role": "customer",
    "iat": 1700000000,
    "exp": 1700000900,
    "type": "access"
}

# Refresh Token Payload (7 day TTL)
{
    "sub": "user_uuid",
    "jti": "unique_token_id",
    "iat": 1700000000,
    "exp": 1700604800,
    "type": "refresh"
}
```

### Auth Middleware Decorator

```python
from functools import wraps
from flask import request, g
import jwt

def auth_required(roles=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = request.headers.get("Authorization", "").replace("Bearer ", "")
            if not token:
                return error_response("UNAUTHORIZED", "Missing authentication token", status_code=401)
            try:
                payload = jwt.decode(token, current_app.config["JWT_SECRET"], algorithms=["HS256"])
                if payload.get("type") != "access":
                    raise jwt.InvalidTokenError()
                g.current_user_id = payload["sub"]
                g.current_user_role = payload["role"]
            except jwt.ExpiredSignatureError:
                return error_response("TOKEN_EXPIRED", "Access token has expired", status_code=401)
            except jwt.InvalidTokenError:
                return error_response("INVALID_TOKEN", "Invalid access token", status_code=401)

            if roles and g.current_user_role not in roles:
                return error_response("FORBIDDEN", "Insufficient permissions", status_code=403)

            return f(*args, **kwargs)
        return decorated_function
    return decorator
```


## Booking Workflow State Machine

```
                    ┌──────────┐
                    │  DRAFT   │ (Customer initiates)
                    └─────┬────┘
                          │ submit details
                          ▼
               ┌──────────────────┐
               │ PENDING_PAYMENT  │ (Price calculated)
               └────────┬─────┬──┘
                        │     │
            payment ok  │     │ cancel
                        ▼     ▼
              ┌──────────┐  ┌───────────┐
              │CONFIRMED │  │ CANCELLED │
              └─────┬────┘  └───────────┘
                    │
                    │ scout/admin starts trip
                    ▼
             ┌─────────────┐
             │ IN_PROGRESS │
             └──────┬──────┘
                    │
                    │ trip ends
                    ▼
             ┌───────────┐
             │ COMPLETED │
             └───────────┘

  CONFIRMED ───cancel──→ CANCELLED ───refund processed──→ REFUNDED
```

### Valid State Transitions

| From | To | Actor | Trigger |
|------|----|-------|---------|
| draft | pending_payment | Customer | Submit booking details |
| draft | cancelled | Customer | Cancel draft |
| pending_payment | confirmed | System | Payment success callback |
| pending_payment | cancelled | Customer | Cancel before payment |
| confirmed | in_progress | Admin/Scout | Trip begins |
| confirmed | cancelled | Customer/Admin | Cancel with refund |
| in_progress | completed | Admin/Scout | Trip ends |
| cancelled | refunded | System | Refund processed |

### Booking Service State Machine Logic

```python
class BookingStateMachine:
    TRANSITIONS = {
        "draft": ["pending_payment", "cancelled"],
        "pending_payment": ["confirmed", "cancelled"],
        "confirmed": ["in_progress", "cancelled"],
        "in_progress": ["completed"],
        "cancelled": ["refunded"],
        "completed": [],
        "refunded": [],
    }

    @classmethod
    def can_transition(cls, from_status: str, to_status: str) -> bool:
        return to_status in cls.TRANSITIONS.get(from_status, [])

    @classmethod
    def transition(cls, booking, to_status: str, actor_id: str):
        if not cls.can_transition(booking.status, to_status):
            raise InvalidStateTransitionError(
                f"Cannot transition from {booking.status} to {to_status}"
            )
        from_status = booking.status
        booking.status = to_status
        # Record history
        return BookingStatusHistory(
            booking_id=booking.id,
            from_status=from_status,
            to_status=to_status,
            changed_by=actor_id,
        )
```


## API Endpoint Specifications

### Auth Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| POST | /api/v1/auth/register | No | - | Register new customer |
| POST | /api/v1/auth/login | No | - | Login and get tokens |
| POST | /api/v1/auth/refresh | No | - | Refresh access token |
| POST | /api/v1/auth/logout | Yes | Any | Logout and invalidate refresh token |
| GET | /api/v1/auth/me | Yes | Any | Get current user profile |

### User Management Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /api/v1/users | Yes | Admin, Super_Admin | List users (paginated) |
| GET | /api/v1/users/{id} | Yes | Admin, Super_Admin | Get user detail |
| PATCH | /api/v1/users/{id}/role | Yes | Super_Admin | Assign/revoke role |
| DELETE | /api/v1/users/{id} | Yes | Super_Admin | Soft delete user |

### Package Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /api/v1/packages | No | - | List packages (paginated, filtered) |
| GET | /api/v1/packages/{id} | No | - | Get package detail with itinerary |
| POST | /api/v1/packages | Yes | Admin, Super_Admin | Create package |
| PUT | /api/v1/packages/{id} | Yes | Admin, Super_Admin | Update package |
| DELETE | /api/v1/packages/{id} | Yes | Admin, Super_Admin | Soft delete package |
| POST | /api/v1/packages/{id}/pricing-tiers | Yes | Admin, Super_Admin | Add pricing tier |
| POST | /api/v1/packages/{id}/itineraries | Yes | Admin, Super_Admin | Add itinerary day |

### Destination Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /api/v1/destinations | No | - | List destinations (hierarchical) |
| GET | /api/v1/destinations/{id} | No | - | Get destination detail |
| POST | /api/v1/destinations | Yes | Admin, Super_Admin | Create destination |
| POST | /api/v1/destinations/{id}/sub-destinations | Yes | Admin, Super_Admin | Create sub-destination |
| PUT | /api/v1/destinations/{id} | Yes | Admin, Super_Admin | Update destination |
| DELETE | /api/v1/destinations/{id} | Yes | Admin, Super_Admin | Soft delete destination |

### Booking Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /api/v1/bookings | Yes | Customer, Admin, Super_Admin | List bookings |
| GET | /api/v1/bookings/{id} | Yes | Customer, Admin, Super_Admin | Get booking detail |
| POST | /api/v1/bookings | Yes | Customer | Create draft booking |
| PATCH | /api/v1/bookings/{id} | Yes | Customer | Update booking details |
| POST | /api/v1/bookings/{id}/submit | Yes | Customer | Submit for payment |
| POST | /api/v1/bookings/{id}/cancel | Yes | Customer, Admin | Cancel booking |
| PATCH | /api/v1/bookings/{id}/status | Yes | Admin, Scout | Update booking status |


### Hotel Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /api/v1/hotels | Yes | Admin, Super_Admin | List hotels |
| GET | /api/v1/hotels/{id} | Yes | Any | Get hotel detail |
| POST | /api/v1/hotels | Yes | Admin, Super_Admin | Register hotel |
| PUT | /api/v1/hotels/{id} | Yes | Admin, Hotel_Partner | Update hotel |
| POST | /api/v1/hotels/{id}/room-types | Yes | Admin, Hotel_Partner | Add room type |
| PUT | /api/v1/hotels/{id}/room-types/{room_type_id} | Yes | Hotel_Partner | Update room type |
| POST | /api/v1/hotels/{id}/availability | Yes | Hotel_Partner | Set room availability |
| GET | /api/v1/hotels/availability | Yes | Admin, Customer | Query availability |

### Scout Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /api/v1/scouts | Yes | Admin, Super_Admin | List scouts |
| POST | /api/v1/scouts | Yes | Admin, Super_Admin | Create scout profile |
| PUT | /api/v1/scouts/{id} | Yes | Admin, Super_Admin | Update scout |
| POST | /api/v1/bookings/{id}/assign-scout | Yes | Admin | Assign scout to booking |
| POST | /api/v1/scouts/{id}/ratings | Yes | Customer | Rate a scout |

### Driver Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /api/v1/drivers | Yes | Admin, Super_Admin | List drivers |
| POST | /api/v1/drivers | Yes | Admin, Super_Admin | Create driver profile |
| PUT | /api/v1/drivers/{id} | Yes | Admin, Super_Admin | Update driver |
| POST | /api/v1/bookings/{id}/assign-driver | Yes | Admin | Assign driver to booking |
| POST | /api/v1/drivers/{id}/ratings | Yes | Customer | Rate a driver |

### Payment Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| POST | /api/v1/payments | Yes | Customer | Initiate payment |
| POST | /api/v1/payments/callback | No | - | Payment gateway callback (webhook) |
| GET | /api/v1/bookings/{id}/payments | Yes | Customer, Admin | List payments for booking |
| POST | /api/v1/payments/{id}/refund | Yes | Admin | Initiate refund |

### Invoice Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /api/v1/bookings/{id}/invoice | Yes | Customer, Admin | Get invoice for booking |
| GET | /api/v1/invoices | Yes | Admin | List all invoices |

### Review Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /api/v1/packages/{id}/reviews | No | - | List published reviews for package |
| POST | /api/v1/reviews | Yes | Customer | Submit review |
| PATCH | /api/v1/reviews/{id}/moderate | Yes | Admin | Approve or reject review |
| GET | /api/v1/reviews/pending | Yes | Admin | List pending reviews |

### Gallery Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /api/v1/{entity_type}/{id}/images | No | - | List images for entity |
| POST | /api/v1/{entity_type}/{id}/images | Yes | Admin | Upload image |
| DELETE | /api/v1/images/{id} | Yes | Admin | Delete image |
| PATCH | /api/v1/images/{id}/order | Yes | Admin | Update display order |


### Blog Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /api/v1/blog | No | - | List published posts |
| GET | /api/v1/blog/{slug} | No | - | Get post by slug |
| POST | /api/v1/blog | Yes | Admin | Create blog post |
| PUT | /api/v1/blog/{id} | Yes | Admin | Update blog post |
| DELETE | /api/v1/blog/{id} | Yes | Admin | Soft delete blog post |
| POST | /api/v1/blog/{id}/publish | Yes | Admin | Publish blog post |

### Enterprise Booking Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /api/v1/enterprise-bookings | Yes | Customer, Admin | List enterprise bookings |
| POST | /api/v1/enterprise-bookings | Yes | Customer, Admin | Create enterprise booking |
| PATCH | /api/v1/enterprise-bookings/{id}/approve | Yes | Admin | Approve and send quotation |
| GET | /api/v1/enterprise-bookings/{id} | Yes | Customer, Admin | Get detail |

### Coupon Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /api/v1/coupons | Yes | Admin | List coupons |
| POST | /api/v1/coupons | Yes | Admin | Create coupon |
| PUT | /api/v1/coupons/{id} | Yes | Admin | Update coupon |
| POST | /api/v1/coupons/validate | Yes | Customer | Validate and preview discount |
| POST | /api/v1/bookings/{id}/apply-coupon | Yes | Customer | Apply coupon to booking |

### Wishlist Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /api/v1/wishlist | Yes | Customer | List wishlist |
| POST | /api/v1/wishlist | Yes | Customer | Add package to wishlist |
| DELETE | /api/v1/wishlist/{package_id} | Yes | Customer | Remove from wishlist |

### Notification Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /api/v1/notifications | Yes | Any | List notifications (paginated) |
| PATCH | /api/v1/notifications/{id}/read | Yes | Any | Mark notification as read |
| POST | /api/v1/notifications/mark-all-read | Yes | Any | Mark all as read |

### Support Ticket Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /api/v1/support-tickets | Yes | Customer, Admin | List tickets |
| POST | /api/v1/support-tickets | Yes | Customer | Create ticket |
| GET | /api/v1/support-tickets/{id} | Yes | Customer, Admin | Get ticket detail |
| POST | /api/v1/support-tickets/{id}/replies | Yes | Customer, Admin | Add reply |
| PATCH | /api/v1/support-tickets/{id}/status | Yes | Admin | Update ticket status |

### Health & Docs Endpoints

| Method | Path | Auth | Roles | Description |
|--------|------|------|-------|-------------|
| GET | /health | No | - | Health check |
| GET | /api/v1/docs | No | - | Swagger/OpenAPI docs |


## Service Layer Design

### Service Pattern

Each service follows a consistent pattern: receives validated data from routes, applies business logic, uses repositories for persistence, and raises domain-specific exceptions.

```python
class PackageService:
    def __init__(self, package_repo, pricing_repo, itinerary_repo):
        self.package_repo = package_repo
        self.pricing_repo = pricing_repo
        self.itinerary_repo = itinerary_repo

    def create_package(self, data: dict) -> Package:
        """Create a new package with pricing tiers and itinerary."""
        package = self.package_repo.create(**data["package"])
        for tier in data.get("pricing_tiers", []):
            self.pricing_repo.create(package_id=package.id, **tier)
        for day in data.get("itinerary", []):
            self.itinerary_repo.create(package_id=package.id, **day)
        return package

    def list_packages(self, filters: dict, page: int, per_page: int, sort_by: str):
        """List packages with filtering, pagination, and sorting."""
        return self.package_repo.list_paginated(
            page=page, per_page=per_page, filters=filters, sort_by=sort_by
        )

    def soft_delete_package(self, package_id: str):
        """Soft delete a package."""
        package = self.package_repo.get_by_id(package_id)
        if not package:
            raise NotFoundError("Package not found")
        package.soft_delete()
        return package
```

### Key Service Contracts

| Service | Key Methods |
|---------|-------------|
| AuthService | register, login, refresh_token, logout, get_current_user |
| PackageService | create, list, get_detail, update, soft_delete, add_pricing_tier, add_itinerary_day |
| BookingService | create_draft, submit_details, confirm, cancel, update_status, list_for_customer |
| HotelService | register, add_room_type, set_availability, query_availability |
| ScoutService | create, assign_to_booking, rate, list_with_availability |
| DriverService | create, assign_to_booking, rate, check_conflicts |
| PaymentService | initiate, process_callback, list_for_booking, initiate_refund |
| InvoiceService | generate, get_by_booking, generate_invoice_number |
| ReviewService | submit, moderate, list_for_package, update_package_rating |
| CouponService | create, validate, apply_to_booking |
| NotificationService | create, list_for_user, mark_read, mark_all_read |
| SupportService | create_ticket, add_reply, update_status, list_for_customer |

### Coupon Discount Calculation

```python
class CouponService:
    def calculate_discount(self, coupon: Coupon, booking_amount: Decimal) -> Decimal:
        """Pure function: calculate discount amount for a given coupon and booking."""
        if coupon.discount_type == "percentage":
            discount = booking_amount * (coupon.discount_value / Decimal("100"))
        else:  # fixed
            discount = coupon.discount_value

        # Apply cap if set
        if coupon.max_discount_cap and discount > coupon.max_discount_cap:
            discount = coupon.max_discount_cap

        return discount

    def validate_coupon(self, code: str, booking_amount: Decimal) -> Coupon:
        """Validate coupon eligibility."""
        coupon = self.coupon_repo.get_by_code(code)
        if not coupon or not coupon.is_active:
            raise ValidationError("Invalid coupon code")
        now = datetime.now(timezone.utc)
        if now < coupon.valid_from or now > coupon.valid_until:
            raise ValidationError("Coupon has expired")
        if coupon.usage_limit and coupon.usage_count >= coupon.usage_limit:
            raise ValidationError("Coupon usage limit reached")
        if coupon.min_booking_amount and booking_amount < coupon.min_booking_amount:
            raise ValidationError(f"Minimum booking amount of {coupon.min_booking_amount} required")
        return coupon
```


### Invoice Number Generation

```python
class InvoiceService:
    def generate_invoice_number(self) -> str:
        """Generate sequential invoice number: INV-YYYYMM-XXXXX"""
        now = datetime.now(timezone.utc)
        prefix = f"INV-{now.strftime('%Y%m')}-"
        last_invoice = self.invoice_repo.get_last_for_month(now.year, now.month)
        if last_invoice:
            last_seq = int(last_invoice.invoice_number.split("-")[-1])
            next_seq = last_seq + 1
        else:
            next_seq = 1
        return f"{prefix}{next_seq:05d}"
```

### Notification Triggers

| Event | Notification Type | Recipients |
|-------|-------------------|------------|
| Booking confirmed | booking_confirmed | Customer |
| Booking cancelled | booking_cancelled | Customer |
| Payment successful | payment_success | Customer |
| Payment failed | payment_failed | Customer |
| Scout assigned | scout_assigned | Customer |
| Driver assigned | driver_assigned | Customer |
| Review approved | review_published | Customer |
| Support ticket reply | ticket_reply | Customer/Admin |
| Enterprise booking approved | enterprise_approved | Customer |

## Error Handling

### Custom Exception Hierarchy

```python
class AppError(Exception):
    """Base application error."""
    status_code = 500
    error_code = "INTERNAL_ERROR"
    message = "An internal error occurred"

class NotFoundError(AppError):
    status_code = 404
    error_code = "NOT_FOUND"

class ValidationError(AppError):
    status_code = 422
    error_code = "VALIDATION_ERROR"

class ConflictError(AppError):
    status_code = 409
    error_code = "CONFLICT"

class UnauthorizedError(AppError):
    status_code = 401
    error_code = "UNAUTHORIZED"

class ForbiddenError(AppError):
    status_code = 403
    error_code = "FORBIDDEN"

class RateLimitError(AppError):
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"

class InvalidStateTransitionError(AppError):
    status_code = 422
    error_code = "INVALID_STATE_TRANSITION"
```

### Global Error Handler

```python
@app.errorhandler(AppError)
def handle_app_error(error):
    return error_response(
        code=error.error_code,
        message=error.message,
        details=getattr(error, "details", None),
        status_code=error.status_code
    )

@app.errorhandler(Exception)
def handle_unexpected_error(error):
    app.logger.exception("Unhandled exception")
    return error_response(
        code="INTERNAL_ERROR",
        message="An unexpected error occurred",
        status_code=500
    )
```


## Request Logging and Audit Trail

### Structured Request Logger

```python
import time
import json
from flask import request, g

@app.before_request
def start_timer():
    g.start_time = time.time()

@app.after_request
def log_request(response):
    duration_ms = (time.time() - g.start_time) * 1000
    log_entry = {
        "method": request.method,
        "path": request.path,
        "status": response.status_code,
        "duration_ms": round(duration_ms, 2),
        "user_id": getattr(g, "current_user_id", None),
        "ip": request.remote_addr,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    app.logger.info(json.dumps(log_entry))
    return response
```

### Audit Trail Decorator

```python
def audit_action(action: str, entity_type: str):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            result = f(*args, **kwargs)
            if g.current_user_role in ("admin", "super_admin"):
                audit_log = AuditLog(
                    actor_id=g.current_user_id,
                    action=action,
                    target_entity=entity_type,
                    target_id=kwargs.get("id") or getattr(result, "id", None),
                )
                db.session.add(audit_log)
            return result
        return wrapper
    return decorator
```

## Security Configuration

### CORS Configuration

```python
from flask_cors import CORS

CORS(app, resources={
    r"/api/*": {
        "origins": app.config["ALLOWED_ORIGINS"].split(","),
        "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "expose_headers": ["X-Request-Id", "Retry-After"],
        "max_age": 600
    }
})
```

### Rate Limiting Configuration

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri=app.config["REDIS_URL"],
    default_limits=["200 per minute"]
)

# Auth-specific limits
@auth_bp.route("/login", methods=["POST"])
@limiter.limit("5 per minute")
def login():
    ...

@auth_bp.route("/register", methods=["POST"])
@limiter.limit("3 per minute")
def register():
    ...
```

## Configuration Management

```python
import os

class Config:
    SECRET_KEY = os.environ["SECRET_KEY"]
    JWT_SECRET = os.environ["JWT_SECRET"]
    JWT_ACCESS_TOKEN_EXPIRES = 900  # 15 minutes
    JWT_REFRESH_TOKEN_EXPIRES = 604800  # 7 days
    SQLALCHEMY_DATABASE_URI = os.environ["DATABASE_URL"]
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10MB upload limit
    PAGINATION_DEFAULT_SIZE = 20
    PAGINATION_MAX_SIZE = 100

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get("TEST_DATABASE_URL", "postgresql://localhost/travel_test")

class ProductionConfig(Config):
    DEBUG = False
```


## Docker and Deployment

### Docker Compose Architecture

```yaml
services:
  api:
    build: .
    command: gunicorn -c gunicorn.conf.py "app:create_app()"
    ports:
      - "5000:5000"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/travel
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET=${JWT_SECRET}
      - SECRET_KEY=${SECRET_KEY}
    depends_on:
      - db
      - redis

  db:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=travel
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  celery_worker:
    build: .
    command: celery -A app.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/travel
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
```

### Gunicorn Configuration

```python
# gunicorn.conf.py
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
timeout = 120
accesslog = "-"
errorlog = "-"
loglevel = "info"
```


## Testing Strategy

### Dual Testing Approach

- **Property-based tests** (Hypothesis library): Verify universal properties across randomized inputs with 100+ iterations per property. Focused on pure logic: state machine transitions, discount calculations, pagination math, input validation, data isolation, and format consistency.
- **Unit tests** (pytest): Verify specific examples, integration points, and edge cases. Focused on specific scenarios like rate limiting thresholds, health check responses, and CORS configuration.
- **Integration tests** (pytest + test client): Verify end-to-end API flows with a real test database. Focused on complete booking workflows, payment callbacks, and multi-service interactions.

### Test Configuration

- Minimum 100 iterations per property test
- Use `TestingConfig` with isolated test database
- Factory Boy for test data generation
- Each property test references its design document property number

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Password is never stored in plaintext

For any registration request with a valid password, the stored password_hash SHALL NOT equal the plaintext password, and SHALL be a valid bcrypt hash.

**Validates: Requirements 1.3**

### Property 2: Registration input validation rejects invalid payloads

For any registration payload where any required field is missing, the email format is invalid, or the password is fewer than 8 characters, the Auth_Service SHALL reject the request with HTTP 422 and return field-level error details.

**Validates: Requirements 1.4, 1.5**

### Property 3: Duplicate email registration rejection

For any email that already exists in the users table, a subsequent registration attempt with that same email SHALL be rejected with HTTP 409.

**Validates: Requirements 1.2**

### Property 4: Login with incorrect credentials returns generic error

For any login attempt where the email does not exist or the password does not match, the Auth_Service SHALL return HTTP 401 with an error message that does not distinguish between invalid email and invalid password.

**Validates: Requirements 2.2**

### Property 5: Refresh token rotation invalidates old token

For any valid refresh token that is submitted to the refresh endpoint, after a new token pair is issued, the original refresh token SHALL no longer be accepted for subsequent refresh requests.

**Validates: Requirements 2.3, 2.4**

### Property 6: Logout invalidates refresh token

For any authenticated session, after logout is called, the associated refresh token SHALL no longer be usable to obtain new access tokens.

**Validates: Requirements 2.5**

### Property 7: Role-based access enforcement

For any authenticated request where the user's role is not in the endpoint's allowed roles list, the Platform SHALL return HTTP 403. For any unauthenticated request to a protected endpoint, the Platform SHALL return HTTP 401.

**Validates: Requirements 4.2, 4.3, 4.4**

### Property 8: Soft-deleted entities are excluded from listings

For any entity (user, package, booking, hotel, destination, blog post, review) that has a non-null deleted_at timestamp, standard list queries SHALL NOT include that entity in results.

**Validates: Requirements 5.4, 6.4, 23.2**

### Property 9: Package filtering returns only matching results

For any combination of filters (destination, duration range, price range, traveller type) applied to the package listing, every returned package SHALL satisfy all specified filter criteria.

**Validates: Requirements 5.2**


### Property 10: Booking state machine allows only valid transitions

For any booking in status S, a transition to status T SHALL succeed only if T is in the set of valid transitions from S (as defined by the state machine). Any attempt to transition to an invalid status SHALL be rejected.

**Validates: Requirements 7.3, 7.4, 7.5, 7.6**

### Property 11: Booking status history records every transition

For any booking status change, a booking_status_history record SHALL be created with the from_status, to_status, actor, and timestamp. The history SHALL be append-only and reflect the complete lifecycle.

**Validates: Requirements 7.6**

### Property 12: Customer data isolation for bookings

For any customer requesting the bookings list endpoint, every returned booking SHALL have a customer_id matching the requesting user's ID. No bookings belonging to other customers SHALL appear.

**Validates: Requirements 7.7**

### Property 13: Hotel availability rejects past dates

For any room availability update request where any date in the range is in the past (before today), the Platform SHALL reject the request with HTTP 422.

**Validates: Requirements 8.5**

### Property 14: Driver scheduling conflict detection

For any driver who already has an assignment for a given date range, a new assignment request for overlapping dates SHALL be rejected with HTTP 409.

**Validates: Requirements 10.4**

### Property 15: Partial payments sum tracking

For any booking with multiple partial payments all in status "completed", the sum of payment amounts SHALL be tracked against the booking total. Each payment record SHALL correctly reference the booking.

**Validates: Requirements 11.4**

### Property 16: Invoice number sequential ordering

For any two invoices generated in the same calendar month, their sequential suffixes SHALL differ by exactly 1 when generated consecutively, and no two invoices SHALL share the same invoice_number.

**Validates: Requirements 12.3**

### Property 17: Review eligibility requires completed booking

For any customer attempting to submit a review, if the associated booking status is not "completed", the Platform SHALL reject the review with HTTP 403.

**Validates: Requirements 13.5**

### Property 18: Review moderation updates package rating

For any review that transitions from "pending_moderation" to "published", the associated package's average_rating SHALL be recalculated to include the new review's rating.

**Validates: Requirements 13.3**


### Property 19: Image validation accepts only allowed formats and sizes

For any file upload where the MIME type is not in {image/jpeg, image/png, image/webp} or the file size exceeds 10 MB, the Platform SHALL reject the upload. For any valid file, metadata SHALL be stored correctly.

**Validates: Requirements 14.2**

### Property 20: Blog slug uniqueness enforcement

For any two blog posts, they SHALL NOT have the same slug. An attempt to create or update a blog post with a slug that already exists SHALL be rejected.

**Validates: Requirements 15.4**

### Property 21: Enterprise booking group size constraint

For any enterprise booking request where the group_size is less than 5 or greater than 500, the Platform SHALL reject the request with a validation error.

**Validates: Requirements 16.2**

### Property 22: Coupon validation and discount calculation

For any coupon application to a booking: if the coupon is expired, fully used, or the booking amount is below the minimum, the Platform SHALL reject with HTTP 422. If valid, the calculated discount SHALL equal min(computed_discount, max_discount_cap) where computed_discount is either a percentage of booking amount or a fixed value.

**Validates: Requirements 17.2, 17.3**

### Property 23: Coupon usage count increment

For any successful coupon application to a booking, the coupon's usage_count SHALL increase by exactly 1.

**Validates: Requirements 17.5**

### Property 24: Wishlist idempotent add and duplicate rejection

For any customer-package pair, the first add to wishlist SHALL succeed. Any subsequent add of the same package for the same customer SHALL be rejected with HTTP 409. After removal, re-adding SHALL succeed.

**Validates: Requirements 18.1, 18.4**

### Property 25: Customer data isolation for support tickets

For any customer requesting the support tickets list, every returned ticket SHALL have a customer_id matching the requesting user's ID.

**Validates: Requirements 20.4**

### Property 26: API response format consistency

For any API response with HTTP status 2xx, the body SHALL contain `{"success": true, "data": ..., "message": ...}`. For any response with HTTP status 4xx or 5xx, the body SHALL contain `{"success": false, "error": {"code": ..., "message": ..., "details": ...}}`.

**Validates: Requirements 21.1, 21.2**

### Property 27: Pagination metadata consistency

For any paginated list response, the pagination metadata SHALL satisfy: total_pages == ceil(total / per_page), page <= total_pages (when total > 0), and the number of items returned SHALL be <= per_page.

**Validates: Requirements 22.1, 22.2**

### Property 28: Sorting correctness

For any list endpoint with a sort_by parameter, if sort_by is "field_name" the results SHALL be in ascending order by that field, and if sort_by is "-field_name" the results SHALL be in descending order.

**Validates: Requirements 22.3**

### Property 29: Audit timestamps are always present and monotonic

For any record in the database, created_at SHALL be non-null and <= updated_at. For any update operation, updated_at SHALL be strictly greater than or equal to the previous updated_at value.

**Validates: Requirements 23.1**

### Property 30: Audit log creation for admin operations

For any create, update, or delete operation performed by an Admin or Super_Admin, an audit_log entry SHALL be created with the correct actor_id, action, target_entity, and target_id.

**Validates: Requirements 25.3**

### Property 31: Unhandled exceptions return generic 500

For any unhandled exception in the application, the API SHALL return HTTP 500 with a generic error message and SHALL NOT expose stack traces, file paths, or internal implementation details in the response body.

**Validates: Requirements 21.4**
