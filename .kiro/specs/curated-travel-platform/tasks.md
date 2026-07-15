# Implementation Plan: Curated Travel Platform

## Overview

Implement the Curated Travel Platform Flask backend with a layered architecture (Routes → Services → Repositories → Models), JWT authentication, RBAC, PostgreSQL database with 22 tables, 15 API resource groups, and comprehensive property-based testing for 31 correctness properties. The implementation proceeds from foundational scaffolding through core features to auxiliary systems, ensuring each phase builds on the previous one.

## Tasks

- [x] 1. Project scaffolding and core infrastructure
  - [x] 1.1 Create project directory structure and configuration
    - Create the `app/` directory structure as defined in the design (api/v1/, models/, services/, repositories/, middleware/, utils/)
    - Create `app/config.py` with `Config`, `DevelopmentConfig`, `TestingConfig`, `ProductionConfig` classes
    - Create `requirements.txt` with Flask, SQLAlchemy, Marshmallow, PyJWT, bcrypt, flask-limiter, flask-cors, gunicorn, alembic, psycopg2-binary, celery, hypothesis, pytest, factory-boy, flasgger
    - Create `.env.example` with all required environment variables
    - _Requirements: 26.4, 27.1_

  - [x] 1.2 Create Flask app factory and extensions
    - Create `app/extensions.py` with SQLAlchemy, Marshmallow, Migrate, Limiter instances
    - Create `app/__init__.py` with `create_app()` factory function that loads config, initializes extensions, registers blueprints, and sets up error handlers
    - Create `app/celery_app.py` with Celery configuration
    - _Requirements: 27.1_

  - [x] 1.3 Create Docker and deployment configuration
    - Create `Dockerfile` with Python 3.11 base, pip install, gunicorn entrypoint
    - Create `docker-compose.yml` with api, db (postgres:15-alpine), redis (redis:7-alpine), celery_worker services
    - Create `gunicorn.conf.py` with bind, workers, timeout settings
    - _Requirements: 24.1_

  - [x] 1.4 Create utility modules and error handling
    - Create `app/utils/response.py` with `success_response`, `error_response`, `paginated_response` helpers
    - Create `app/utils/exceptions.py` with custom exception hierarchy (AppError, NotFoundError, ValidationError, ConflictError, UnauthorizedError, ForbiddenError, RateLimitError, InvalidStateTransitionError)
    - Create `app/utils/pagination.py` with pagination helper for query params parsing
    - Create `app/errors.py` with global error handlers for AppError and unhandled exceptions
    - _Requirements: 21.1, 21.2, 21.3, 21.4_

  - [x] 1.5 Write property tests for API response format and error handling
    - **Property 26: API response format consistency**
    - **Property 31: Unhandled exceptions return generic 500**
    - **Validates: Requirements 21.1, 21.2, 21.4**

- [x] 2. Database models and base repository
  - [x] 2.1 Create base model mixin and base repository
    - Create `app/models/base.py` with `AuditMixin` (id UUID, created_at, updated_at, deleted_at, is_deleted property, soft_delete method)
    - Create `app/repositories/base_repository.py` with `BaseRepository` class (get_by_id, list_paginated, create, update, soft_delete, _apply_filters, _apply_sorting)
    - _Requirements: 23.1, 23.2, 22.1, 22.2, 22.3_

  - [x] 2.2 Write property tests for audit timestamps and pagination
    - **Property 29: Audit timestamps are always present and monotonic**
    - **Property 27: Pagination metadata consistency**
    - **Property 28: Sorting correctness**
    - **Validates: Requirements 23.1, 22.1, 22.2, 22.3**

  - [x] 2.3 Create User and RefreshToken models
    - Create `app/models/user.py` with User model (email, password_hash, full_name, phone, role enum, is_active, soft delete)
    - Create `app/models/user.py` with RefreshToken model (user_id FK, token_hash, expires_at, is_revoked)
    - Define relationships between User and RefreshToken
    - _Requirements: 1.1, 2.1, 4.1_

  - [x] 2.4 Create Package, PricingTier, and Itinerary models
    - Create `app/models/package.py` with Package model (title, slug, description, destination_id FK, duration_days/nights, traveller_type enum, inclusions/exclusions JSONB, average_rating, total_reviews, soft delete)
    - Create PricingTier model (package_id FK, tier_name, price, max_persons, unique constraint on package_id+tier_name)
    - Create Itinerary model (package_id FK, day_number, title, description, activities JSONB, unique constraint on package_id+day_number)
    - _Requirements: 5.1, 5.5, 5.6_

  - [x] 2.5 Create Destination and SubDestination models
    - Create `app/models/destination.py` with Destination model (name unique, description, is_primary, soft delete)
    - Create SubDestination model (destination_id FK, name, description, latitude, longitude, category enum, media_urls JSONB, soft delete)
    - _Requirements: 6.1, 6.2_

  - [x] 2.6 Create Booking, BookingStatusHistory, BookingScout, and BookingDriver models
    - Create `app/models/booking.py` with Booking model (booking_number unique, customer_id FK, package_id FK, status enum, travel dates, num_travellers, hotel/room FK, pricing fields, coupon_id FK, soft delete)
    - Create BookingStatusHistory model (booking_id FK, from_status, to_status, changed_by FK, notes)
    - Create BookingScout model (booking_id FK, scout_id FK, assigned_at, assigned_by FK, unique constraint)
    - Create BookingDriver model (booking_id FK, driver_id FK, assigned_at, assigned_by FK, unique constraint)
    - _Requirements: 7.1, 7.4, 7.6, 9.3, 10.2_

  - [x] 2.7 Create Hotel, RoomType, and RoomAvailability models
    - Create `app/models/hotel.py` with Hotel model (partner_user_id FK, name, address, destination_id FK, star_rating, amenities JSONB, soft delete)
    - Create RoomType model (hotel_id FK, name, capacity, base_price, amenities JSONB)
    - Create RoomAvailability model (room_type_id FK, date, available_count, unique constraint on room_type_id+date)
    - _Requirements: 8.1, 8.2, 8.3_

  - [x] 2.8 Create Scout, ScoutAvailability, Driver, and DriverAvailability models
    - Create `app/models/scout.py` with Scout model (user_id FK unique, languages JSONB, specializations JSONB, operating_area enum, is_available, average_rating, total_assignments)
    - Create ScoutAvailability model (scout_id FK, date, is_available, unique constraint)
    - Create `app/models/driver.py` with Driver model (user_id FK unique, vehicle_type, vehicle_number, license_number, operating_area enum, is_available, average_rating, total_assignments)
    - Create DriverAvailability model (driver_id FK, date, is_available, unique constraint)
    - _Requirements: 9.1, 10.1_

  - [x] 2.9 Create Payment, Refund, and Invoice models
    - Create `app/models/payment.py` with Payment model (booking_id FK, amount, currency, payment_method, gateway_transaction_id, status enum, gateway_response JSONB)
    - Create Refund model (payment_id FK, booking_id FK, amount, reason, status enum)
    - Create `app/models/invoice.py` with Invoice model (invoice_number unique, booking_id FK, customer_id FK, items JSONB, subtotal, tax_amount, discount_amount, total_amount, issued_at)
    - _Requirements: 11.1, 11.5, 12.1, 12.3_

  - [x] 2.10 Create Review, GalleryImage, BlogPost models
    - Create `app/models/review.py` with Review model (customer_id FK, booking_id FK, package_id FK, entity_type enum, entity_id, rating 1-5, title, body, status enum, rejection_reason, soft delete)
    - Create `app/models/gallery.py` with GalleryImage model (entity_type enum, entity_id, filename, file_size, mime_type, dimensions, alt_text, display_order, storage_url)
    - Create `app/models/blog.py` with BlogPost model (title, slug unique, body, author_id FK, category, tags JSONB, featured_image_url, seo fields, status enum, published_at, soft delete)
    - _Requirements: 13.1, 14.1, 15.1_

  - [x] 2.11 Create EnterpriseBooking, Coupon, Wishlist, Notification, SupportTicket, TicketReply, and AuditLog models
    - Create `app/models/enterprise.py` with EnterpriseBooking model (customer_id FK, company_name, contact details, group_size 5-500, travel dates, destination_id FK, budget range, status enum, quotation JSONB)
    - Create `app/models/coupon.py` with Coupon model (code unique, discount_type enum, discount_value, min_booking_amount, max_discount_cap, validity dates, usage_limit, usage_count, is_active)
    - Create `app/models/wishlist.py` with Wishlist model (customer_id FK, package_id FK, unique constraint)
    - Create `app/models/notification.py` with Notification model (user_id FK, type, title, body, reference_type/id, delivery_channel enum, is_read, read_at)
    - Create `app/models/support.py` with SupportTicket model (customer_id FK, booking_id FK optional, subject, description, priority enum, status enum) and TicketReply model (ticket_id FK, author_id FK, body)
    - Create `app/models/audit_log.py` with AuditLog model (actor_id FK, action, target_entity, target_id, changes JSONB)
    - _Requirements: 16.1, 17.1, 18.1, 19.1, 20.1, 25.3_

  - [x] 2.12 Create models __init__.py and register all models, set up Alembic migrations
    - Create `app/models/__init__.py` importing all models for Alembic auto-detection
    - Initialize Alembic with `flask db init`
    - Generate initial migration with all 22 tables, indexes, and constraints
    - _Requirements: 23.3, 23.4_

- [x] 3. Checkpoint - Verify database models and migrations
  - Ensure all models are correctly defined and migration generates without errors, ask the user if questions arise.

- [x] 4. Authentication system
  - [x] 4.1 Create auth service with registration and login
    - Create `app/repositories/user_repository.py` with methods: get_by_email, create_user, get_by_id
    - Create `app/services/auth_service.py` with register (validate, hash password with bcrypt, create user, generate tokens), login (find user, verify password, generate tokens), generate_access_token, generate_refresh_token, store_refresh_token
    - Create `app/api/v1/auth/schemas.py` with RegisterSchema (email, password min 8, full_name, phone), LoginSchema (email, password), TokenRefreshSchema
    - _Requirements: 1.1, 1.3, 1.5, 2.1_

  - [x] 4.2 Create auth routes (register, login, refresh, logout, me)
    - Create `app/api/v1/auth/routes.py` with POST /register, POST /login, POST /refresh, POST /logout, GET /me
    - Register auth blueprint in `app/api/v1/__init__.py`
    - Handle HTTP 409 for duplicate email, 422 for validation errors, 401 for incorrect credentials
    - _Requirements: 1.1, 1.2, 1.4, 2.1, 2.2, 2.3, 2.4, 2.5_

  - [x] 4.3 Create token refresh and logout functionality
    - Implement refresh_token endpoint: validate refresh token hash, check expiry/revoked, issue new pair, revoke old token
    - Implement logout endpoint: revoke current refresh token
    - _Requirements: 2.3, 2.4, 2.5_

  - [x] 4.4 Write property tests for auth system
    - **Property 1: Password is never stored in plaintext**
    - **Property 2: Registration input validation rejects invalid payloads**
    - **Property 3: Duplicate email registration rejection**
    - **Property 4: Login with incorrect credentials returns generic error**
    - **Property 5: Refresh token rotation invalidates old token**
    - **Property 6: Logout invalidates refresh token**
    - **Validates: Requirements 1.2, 1.3, 1.4, 1.5, 2.2, 2.3, 2.4, 2.5**

- [x] 5. Middleware (Auth, RBAC, Rate Limiting, Request Logging)
  - [x] 5.1 Create auth middleware and RBAC decorators
    - Create `app/middleware/auth_middleware.py` with `auth_required(roles=None)` decorator that validates JWT, extracts user_id and role into `g`, and enforces role-based access
    - Create `app/middleware/rbac_middleware.py` with role checking utility functions
    - _Requirements: 4.2, 4.3, 4.4_

  - [x] 5.2 Create rate limiting middleware
    - Create `app/middleware/rate_limiter.py` integrating flask-limiter with Redis backend
    - Configure auth-specific rate limits: login (5/min), registration (3/min), global default (200/min)
    - Ensure HTTP 429 response includes Retry-After header
    - _Requirements: 3.1, 3.2, 3.3_

  - [x] 5.3 Create request logging and audit middleware
    - Create `app/middleware/request_logger.py` with before_request/after_request hooks for structured JSON logging (method, path, status, duration_ms, user_id, IP, timestamp)
    - Create `app/utils/audit.py` with `audit_action` decorator for recording admin operations to audit_logs table
    - _Requirements: 25.1, 25.2, 25.3_

  - [x] 5.4 Configure CORS and security settings
    - Configure flask-cors in app factory with ALLOWED_ORIGINS from config
    - Set up MAX_CONTENT_LENGTH (10MB) for upload limiting
    - _Requirements: 26.3, 26.5_

  - [x] 5.5 Write property tests for RBAC and audit
    - **Property 7: Role-based access enforcement**
    - **Property 30: Audit log creation for admin operations**
    - **Validates: Requirements 4.2, 4.3, 4.4, 25.3**

- [x] 6. Checkpoint - Verify auth system and middleware
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Package management
  - [x] 7.1 Create package repository and service
    - Create `app/repositories/package_repository.py` with filtering (destination, duration, price range, traveller_type), text search, and sorting
    - Create `app/services/package_service.py` with create_package (with pricing tiers and itinerary), list_packages, get_detail, update_package, soft_delete_package, add_pricing_tier, add_itinerary_day
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 7.2 Create package schemas and routes
    - Create `app/api/v1/packages/schemas.py` with PackageCreateSchema, PackageUpdateSchema, PackageListSchema, PricingTierSchema, ItinerarySchema
    - Create `app/api/v1/packages/routes.py` with GET /packages (public, paginated, filtered), GET /packages/{id}, POST /packages (admin), PUT /packages/{id} (admin), DELETE /packages/{id} (admin), POST /packages/{id}/pricing-tiers, POST /packages/{id}/itineraries
    - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

  - [x] 7.3 Write property tests for package filtering and soft delete
    - **Property 9: Package filtering returns only matching results**
    - **Property 8: Soft-deleted entities are excluded from listings**
    - **Validates: Requirements 5.2, 5.4, 23.2**

- [x] 8. Destination management
  - [x] 8.1 Create destination repository, service, schemas, and routes
    - Create `app/repositories/destination_repository.py` with hierarchical listing (destinations with sub-destinations)
    - Create `app/services/destination_service.py` with create_destination, create_sub_destination, list_hierarchical, update, soft_delete (cascading to sub-destinations)
    - Create `app/api/v1/destinations/schemas.py` and `app/api/v1/destinations/routes.py` with GET /destinations (hierarchical), GET /destinations/{id}, POST /destinations, POST /destinations/{id}/sub-destinations, PUT /destinations/{id}, DELETE /destinations/{id}
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 9. Booking engine
  - [x] 9.1 Create booking repository and state machine service
    - Create `app/repositories/booking_repository.py` with customer-scoped listing, status filtering, booking number generation
    - Create `app/services/booking_service.py` with BookingStateMachine (TRANSITIONS dict, can_transition, transition methods), create_draft, submit_details (calculate price), confirm, cancel (initiate refund), update_status, list_for_customer
    - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7_

  - [x] 9.2 Create booking schemas and routes
    - Create `app/api/v1/bookings/schemas.py` with BookingCreateSchema, BookingUpdateSchema, BookingStatusSchema
    - Create `app/api/v1/bookings/routes.py` with GET /bookings (customer-scoped), GET /bookings/{id}, POST /bookings (create draft), PATCH /bookings/{id} (update details), POST /bookings/{id}/submit (move to pending_payment), POST /bookings/{id}/cancel, PATCH /bookings/{id}/status (admin/scout status update)
    - _Requirements: 7.1, 7.2, 7.3, 7.5, 7.6, 7.7_

  - [x] 9.3 Write property tests for booking state machine and data isolation
    - **Property 10: Booking state machine allows only valid transitions**
    - **Property 11: Booking status history records every transition**
    - **Property 12: Customer data isolation for bookings**
    - **Validates: Requirements 7.3, 7.4, 7.5, 7.6, 7.7**

- [x] 10. Hotel management
  - [x] 10.1 Create hotel repository, service, schemas, and routes
    - Create `app/repositories/hotel_repository.py` with availability query (destination, date range, room capacity)
    - Create `app/services/hotel_service.py` with register_hotel, add_room_type, set_availability (reject past dates), query_availability
    - Create `app/api/v1/hotels/schemas.py` and `app/api/v1/hotels/routes.py` with GET /hotels, GET /hotels/{id}, POST /hotels (admin), PUT /hotels/{id} (admin/partner), POST /hotels/{id}/room-types, PUT /hotels/{id}/room-types/{room_type_id}, POST /hotels/{id}/availability (reject past dates), GET /hotels/availability
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

  - [x] 10.2 Write property test for hotel availability past date rejection
    - **Property 13: Hotel availability rejects past dates**
    - **Validates: Requirements 8.5**

- [x] 11. Scout management
  - [x] 11.1 Create scout repository, service, schemas, and routes
    - Create `app/repositories/scout_repository.py` with availability checks, listing with ratings and assignment counts
    - Create `app/services/scout_service.py` with create_scout, assign_to_booking (update availability, create BookingScout record), rate_scout (update average_rating), list_with_availability
    - Create `app/api/v1/scouts/schemas.py` and `app/api/v1/scouts/routes.py` with GET /scouts (admin), POST /scouts (admin), PUT /scouts/{id} (admin), POST /bookings/{id}/assign-scout (admin), POST /scouts/{id}/ratings (customer)
    - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 12. Driver management
  - [x] 12.1 Create driver repository, service, schemas, and routes
    - Create `app/repositories/driver_repository.py` with availability checks and conflict detection for date ranges
    - Create `app/services/driver_service.py` with create_driver, assign_to_booking (check conflicts, update availability, create BookingDriver record), rate_driver (update average_rating), check_conflicts
    - Create `app/api/v1/drivers/schemas.py` and `app/api/v1/drivers/routes.py` with GET /drivers (admin), POST /drivers (admin), PUT /drivers/{id} (admin), POST /bookings/{id}/assign-driver (admin), POST /drivers/{id}/ratings (customer)
    - Return HTTP 409 if driver has overlapping assignment
    - _Requirements: 10.1, 10.2, 10.3, 10.4_

  - [x] 12.2 Write property test for driver scheduling conflict detection
    - **Property 14: Driver scheduling conflict detection**
    - **Validates: Requirements 10.4**

- [x] 13. Checkpoint - Verify core booking flow (packages, bookings, hotels, scouts, drivers)
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Payment processing
  - [x] 14.1 Create payment repository, service, schemas, and routes
    - Create `app/repositories/payment_repository.py` with listing by booking, tracking partial payments
    - Create `app/services/payment_service.py` with initiate_payment (create pending record), process_callback (update status, trigger booking confirmation on success, notify on failure), list_for_booking, initiate_refund (create refund record with status processing)
    - Create `app/api/v1/payments/schemas.py` and `app/api/v1/payments/routes.py` with POST /payments (customer), POST /payments/callback (webhook, no auth), GET /bookings/{id}/payments, POST /payments/{id}/refund (admin)
    - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

  - [x] 14.2 Write property test for partial payment tracking
    - **Property 15: Partial payments sum tracking**
    - **Validates: Requirements 11.4**

- [x] 15. Invoice generation
  - [x] 15.1 Create invoice repository, service, schemas, and routes
    - Create `app/repositories/invoice_repository.py` with get_last_for_month for sequential numbering
    - Create `app/services/invoice_service.py` with generate_invoice (create record with sequential number INV-YYYYMM-XXXXX, itemized charges, taxes, total), get_by_booking
    - Create `app/api/v1/invoices/schemas.py` and `app/api/v1/invoices/routes.py` with GET /bookings/{id}/invoice (customer/admin), GET /invoices (admin)
    - _Requirements: 12.1, 12.2, 12.3_

  - [x] 15.2 Write property test for invoice number sequential ordering
    - **Property 16: Invoice number sequential ordering**
    - **Validates: Requirements 12.3**

- [x] 16. Review system
  - [x] 16.1 Create review repository, service, schemas, and routes
    - Create `app/repositories/review_repository.py` with listing by package (published only), pending reviews listing
    - Create `app/services/review_service.py` with submit_review (check booking is completed, set pending_moderation), moderate_review (approve → recalculate package average_rating, reject → store reason), list_for_package, update_package_rating
    - Create `app/api/v1/reviews/schemas.py` and `app/api/v1/reviews/routes.py` with GET /packages/{id}/reviews (public), POST /reviews (customer), PATCH /reviews/{id}/moderate (admin), GET /reviews/pending (admin)
    - _Requirements: 13.1, 13.2, 13.3, 13.4, 13.5_

  - [x] 16.2 Write property tests for review eligibility and rating update
    - **Property 17: Review eligibility requires completed booking**
    - **Property 18: Review moderation updates package rating**
    - **Validates: Requirements 13.3, 13.5**

- [x] 17. Gallery and image management
  - [x] 17.1 Create gallery service, schemas, and routes
    - Create `app/services/gallery_service.py` with upload_image (validate MIME type ∈ {jpeg, png, webp} and file size ≤ 10MB, store metadata), list_for_entity (sorted by display_order), delete_image, update_display_order
    - Create `app/api/v1/gallery/schemas.py` and `app/api/v1/gallery/routes.py` with GET /{entity_type}/{id}/images (public), POST /{entity_type}/{id}/images (admin), DELETE /images/{id} (admin), PATCH /images/{id}/order (admin)
    - _Requirements: 14.1, 14.2, 14.3, 14.4_

  - [x] 17.2 Write property test for image validation
    - **Property 19: Image validation accepts only allowed formats and sizes**
    - **Validates: Requirements 14.2**

- [x] 18. Blog and CMS
  - [x] 18.1 Create blog repository, service, schemas, and routes
    - Create `app/repositories/blog_repository.py` with slug-based lookup, filtering by category/tag/status
    - Create `app/services/blog_service.py` with create_post (generate slug, set draft), update_post, publish_post (set published_at), soft_delete, list_published
    - Create `app/api/v1/blog/schemas.py` and `app/api/v1/blog/routes.py` with GET /blog (public, paginated), GET /blog/{slug} (public), POST /blog (admin), PUT /blog/{id} (admin), DELETE /blog/{id} (admin), POST /blog/{id}/publish (admin)
    - _Requirements: 15.1, 15.2, 15.3, 15.4_

  - [x] 18.2 Write property test for blog slug uniqueness
    - **Property 20: Blog slug uniqueness enforcement**
    - **Validates: Requirements 15.4**

- [x] 19. Enterprise bookings
  - [x] 19.1 Create enterprise booking service, schemas, and routes
    - Create `app/services/enterprise_service.py` with create_enterprise_booking (validate group_size 5-500, set status pending_review), approve_and_send_quotation (update status to quotation_sent, store quotation JSONB), list, get_detail
    - Create `app/api/v1/enterprise/schemas.py` and `app/api/v1/enterprise/routes.py` with GET /enterprise-bookings (customer/admin), POST /enterprise-bookings (customer/admin), PATCH /enterprise-bookings/{id}/approve (admin), GET /enterprise-bookings/{id}
    - _Requirements: 16.1, 16.2, 16.3, 16.4_

  - [x] 19.2 Write property test for enterprise booking group size constraint
    - **Property 21: Enterprise booking group size constraint**
    - **Validates: Requirements 16.2**

- [x] 20. Coupon system
  - [x] 20.1 Create coupon repository, service, schemas, and routes
    - Create `app/repositories/coupon_repository.py` with get_by_code, listing
    - Create `app/services/coupon_service.py` with create_coupon, validate_coupon (check active, expiry, usage_limit, min_booking_amount), calculate_discount (percentage vs fixed, apply max_discount_cap), apply_to_booking (validate + increment usage_count + update booking discount_amount)
    - Create `app/api/v1/coupons/schemas.py` and `app/api/v1/coupons/routes.py` with GET /coupons (admin), POST /coupons (admin), PUT /coupons/{id} (admin), POST /coupons/validate (customer), POST /bookings/{id}/apply-coupon (customer)
    - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

  - [x] 20.2 Write property tests for coupon validation and discount calculation
    - **Property 22: Coupon validation and discount calculation**
    - **Property 23: Coupon usage count increment**
    - **Validates: Requirements 17.2, 17.3, 17.5**

- [x] 21. Wishlist management
  - [x] 21.1 Create wishlist service, schemas, and routes
    - Create `app/services/wishlist_service.py` with add_to_wishlist (check unique constraint, return 409 on duplicate), remove_from_wishlist, list_wishlist (with package details and current pricing)
    - Create `app/api/v1/wishlist/schemas.py` and `app/api/v1/wishlist/routes.py` with GET /wishlist (customer), POST /wishlist (customer), DELETE /wishlist/{package_id} (customer)
    - _Requirements: 18.1, 18.2, 18.3, 18.4_

  - [x] 21.2 Write property test for wishlist idempotent add
    - **Property 24: Wishlist idempotent add and duplicate rejection**
    - **Validates: Requirements 18.1, 18.4**

- [x] 22. Checkpoint - Verify secondary features (payments, invoices, reviews, gallery, blog, enterprise, coupons, wishlist)
  - Ensure all tests pass, ask the user if questions arise.

- [x] 23. Notification system
  - [x] 23.1 Create notification service, schemas, and routes
    - Create `app/services/notification_service.py` with create_notification (type, title, body, reference, channel), list_for_user (paginated, sorted by created_at desc), mark_read (set is_read=true, record read_at), mark_all_read
    - Create `app/api/v1/notifications/schemas.py` and `app/api/v1/notifications/routes.py` with GET /notifications (any auth user, paginated), PATCH /notifications/{id}/read, POST /notifications/mark-all-read
    - Wire notification triggers in booking_service (booking_confirmed, booking_cancelled), payment_service (payment_success, payment_failed), scout_service (scout_assigned), driver_service (driver_assigned), review_service (review_published), support_service (ticket_reply)
    - _Requirements: 19.1, 19.2, 19.3, 19.4_

- [x] 24. Support ticket system
  - [x] 24.1 Create support ticket service, schemas, and routes
    - Create `app/services/support_service.py` with create_ticket (set status open), add_reply (store reply, trigger notification), update_status (open → in_progress → resolved → closed), list_for_customer (customer-scoped)
    - Create `app/api/v1/support/schemas.py` and `app/api/v1/support/routes.py` with GET /support-tickets (customer/admin), POST /support-tickets (customer), GET /support-tickets/{id}, POST /support-tickets/{id}/replies (customer/admin), PATCH /support-tickets/{id}/status (admin)
    - _Requirements: 20.1, 20.2, 20.3, 20.4_

  - [x] 24.2 Write property test for customer data isolation on support tickets
    - **Property 25: Customer data isolation for support tickets**
    - **Validates: Requirements 20.4**

- [x] 25. Health check and API documentation
  - [x] 25.1 Create health check endpoint
    - Create `app/api/v1/health/routes.py` with GET /health (no auth) returning service status, database connectivity check (attempt DB query), and application version
    - Return HTTP 200 on healthy, HTTP 503 if database is unreachable
    - _Requirements: 24.1, 24.2, 24.3_

  - [x] 25.2 Create Swagger/OpenAPI documentation
    - Integrate Flasgger or flask-apispec for OpenAPI documentation
    - Create `app/api/v1/docs/` with Swagger UI at GET /api/v1/docs
    - Add endpoint summaries, request/response schemas, and auth requirements to spec
    - _Requirements: 27.2, 27.3_

- [x] 26. User management (admin endpoints)
  - [x] 26.1 Create user management routes for admin
    - Create `app/api/v1/users/routes.py` with GET /users (admin, paginated), GET /users/{id} (admin), PATCH /users/{id}/role (super_admin), DELETE /users/{id} (super_admin, soft delete)
    - _Requirements: 4.1, 4.5_

- [x] 27. Test infrastructure and remaining property tests
  - [x] 27.1 Set up test infrastructure
    - Create `tests/conftest.py` with TestingConfig, test database setup/teardown, Flask test client fixture, authenticated client fixtures (customer, admin, super_admin), factory-boy factories for all models
    - Create `tests/property/conftest.py` with Hypothesis settings (min 100 examples)
    - _Requirements: 26.1, 26.2_

  - [x] 27.2 Write integration tests for complete booking workflow
    - Test full flow: register → login → browse packages → create booking → submit → payment callback → confirm → assign scout → assign driver → complete → review
    - Test cancellation and refund flow
    - _Requirements: 7.1, 7.2, 7.3, 7.5, 11.2, 11.5_

- [x] 28. Final checkpoint - Full integration verification
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document (31 properties total)
- Unit tests validate specific examples and edge cases
- The implementation uses Python with Flask, SQLAlchemy, Marshmallow, PyJWT, and Hypothesis
- All property tests use Hypothesis library with minimum 100 examples per property
- Database uses PostgreSQL with Alembic for migrations
- Redis is used for rate limiting and caching
- Docker Compose orchestrates all services (API, DB, Redis, Celery)

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["1.2", "1.3"] },
    { "id": 2, "tasks": ["1.4", "2.1"] },
    { "id": 3, "tasks": ["1.5", "2.2", "2.3", "2.4", "2.5"] },
    { "id": 4, "tasks": ["2.6", "2.7", "2.8", "2.9", "2.10", "2.11"] },
    { "id": 5, "tasks": ["2.12"] },
    { "id": 6, "tasks": ["4.1", "5.1", "5.4"] },
    { "id": 7, "tasks": ["4.2", "4.3", "5.2", "5.3"] },
    { "id": 8, "tasks": ["4.4", "5.5"] },
    { "id": 9, "tasks": ["7.1", "8.1"] },
    { "id": 10, "tasks": ["7.2", "9.1"] },
    { "id": 11, "tasks": ["7.3", "9.2", "10.1"] },
    { "id": 12, "tasks": ["9.3", "10.2", "11.1", "12.1"] },
    { "id": 13, "tasks": ["12.2", "14.1"] },
    { "id": 14, "tasks": ["14.2", "15.1"] },
    { "id": 15, "tasks": ["15.2", "16.1"] },
    { "id": 16, "tasks": ["16.2", "17.1", "18.1"] },
    { "id": 17, "tasks": ["17.2", "18.2", "19.1"] },
    { "id": 18, "tasks": ["19.2", "20.1", "21.1"] },
    { "id": 19, "tasks": ["20.2", "21.2", "23.1", "24.1"] },
    { "id": 20, "tasks": ["24.2", "25.1", "25.2", "26.1"] },
    { "id": 21, "tasks": ["27.1"] },
    { "id": 22, "tasks": ["27.2"] }
  ]
}
```
