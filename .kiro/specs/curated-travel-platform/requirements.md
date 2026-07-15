# Requirements Document

## Introduction

A premium curated travel platform backend (Flask API) serving Varanasi and Mirzapur, India. The platform's promise is: "Just reach Varanasi or Mirzapur. We take care of everything else." A trained scout receives travellers at arrival points and the platform manages end-to-end travel experiences including hotels, transportation, local guides, hidden places, food, temples, ghats, waterfalls, cultural experiences, shopping, safety, and drop back services.

The backend provides a RESTful, versioned API (/api/v1/) built with Flask, PostgreSQL, SQLAlchemy, Alembic, JWT authentication, and enterprise-grade architecture. It supports multiple user roles and serves solo travellers, couples, families, friend groups, college trips, corporate trips, foreign tourists, NRIs, pilgrims, backpackers, and luxury travellers.

## Glossary

- **Platform**: The curated travel platform Flask backend application
- **API**: The RESTful HTTP interface exposed by the Platform at /api/v1/
- **Guest**: An unauthenticated user browsing public endpoints
- **Customer**: A registered and authenticated traveller using the platform
- **Scout**: A trained field agent who receives and guides travellers at arrival points
- **Driver**: A transportation provider assigned to trips
- **Vendor**: A third-party service provider (food, activities, shopping)
- **Hotel_Partner**: A hotel owner or manager with property listed on the platform
- **Admin**: A platform administrator with management privileges
- **Super_Admin**: A platform administrator with full system access including role management
- **Auth_Service**: The authentication and authorization subsystem handling JWT, sessions, and access control
- **Booking_Service**: The subsystem managing booking lifecycle from creation to completion
- **Package_Service**: The subsystem managing travel packages, itineraries, and pricing
- **Payment_Service**: The subsystem handling payment processing, invoices, and refunds
- **Notification_Service**: The subsystem handling in-app and email notifications
- **Access_Token**: A short-lived JWT token used for API authentication
- **Refresh_Token**: A long-lived token used to obtain new access tokens without re-authentication
- **Soft_Delete**: A deletion strategy that marks records as deleted (via deleted_at timestamp) without removing data from the database

## Requirements

### Requirement 1: User Registration

**User Story:** As a traveller, I want to register an account on the platform, so that I can book curated travel packages.

#### Acceptance Criteria

1. WHEN a registration request is received with valid email, password, full name, and phone number, THE Auth_Service SHALL create a new Customer account and return an Access_Token and Refresh_Token pair.
2. WHEN a registration request is received with an email that already exists in the database, THE Auth_Service SHALL reject the request with HTTP 409 status and a descriptive error message.
3. WHEN a registration request is received, THE Auth_Service SHALL hash the password using bcrypt before storing it in the database.
4. WHEN a registration request is received with missing or invalid fields, THE Auth_Service SHALL reject the request with HTTP 422 status and field-level validation errors.
5. THE Auth_Service SHALL enforce a minimum password length of 8 characters for all registration requests.

### Requirement 2: User Authentication

**User Story:** As a registered user, I want to log in securely, so that I can access protected platform features.

#### Acceptance Criteria

1. WHEN a login request is received with valid email and password, THE Auth_Service SHALL return an Access_Token (short-lived) and a Refresh_Token (long-lived).
2. WHEN a login request is received with incorrect credentials, THE Auth_Service SHALL reject the request with HTTP 401 status and a generic error message that does not reveal whether the email or password is incorrect.
3. WHEN a valid Refresh_Token is submitted to the token refresh endpoint, THE Auth_Service SHALL issue a new Access_Token and a new Refresh_Token, and invalidate the old Refresh_Token.
4. WHEN an expired or invalid Refresh_Token is submitted, THE Auth_Service SHALL reject the request with HTTP 401 status.
5. WHEN a logout request is received, THE Auth_Service SHALL invalidate the current Refresh_Token.

### Requirement 3: Rate Limiting

**User Story:** As a platform operator, I want authentication endpoints to be rate-limited, so that brute-force attacks are mitigated.

#### Acceptance Criteria

1. THE Auth_Service SHALL enforce rate limiting on the login endpoint, restricting requests to a configurable threshold per IP address within a configurable time window.
2. WHEN the rate limit is exceeded, THE Auth_Service SHALL reject subsequent requests with HTTP 429 status and include a Retry-After header.
3. THE Auth_Service SHALL enforce rate limiting on the registration endpoint, restricting requests to a configurable threshold per IP address within a configurable time window.

### Requirement 4: Role-Based Access Control

**User Story:** As an administrator, I want the platform to enforce role-based access, so that users can only perform actions appropriate to their role.

#### Acceptance Criteria

1. THE Platform SHALL support the following roles: Guest, Customer, Scout, Driver, Vendor, Hotel_Partner, Admin, and Super_Admin.
2. WHEN an authenticated request is received, THE Platform SHALL extract the user role from the Access_Token and enforce endpoint-level authorization.
3. WHEN a user attempts to access an endpoint without the required role, THE Platform SHALL reject the request with HTTP 403 status.
4. WHEN an unauthenticated request is received for a protected endpoint, THE Platform SHALL reject the request with HTTP 401 status.
5. THE Super_Admin SHALL have the ability to assign and revoke roles for any user account.

### Requirement 5: Package Management

**User Story:** As an admin, I want to create and manage curated travel packages, so that customers can browse and book them.

#### Acceptance Criteria

1. WHEN an Admin or Super_Admin submits a valid package creation request, THE Package_Service SHALL create the package with title, description, destination, duration, pricing tiers, itinerary, inclusions, and exclusions.
2. WHEN a Customer or Guest requests the package listing endpoint, THE Package_Service SHALL return a paginated list of active packages with support for filtering by destination, duration, price range, and traveller type.
3. WHEN an Admin submits a package update request, THE Package_Service SHALL update the specified fields and record the updated_at timestamp.
4. WHEN an Admin submits a package deletion request, THE Package_Service SHALL perform a Soft_Delete on the package record.
5. THE Package_Service SHALL support multiple pricing tiers per package (per-person, couple, family, group).
6. WHEN a package detail request is received, THE Package_Service SHALL return the full package data including day-wise itinerary breakdown.

### Requirement 6: Destination Management

**User Story:** As an admin, I want to manage destinations and sub-destinations, so that packages and content are organized geographically.

#### Acceptance Criteria

1. THE Platform SHALL support two primary destinations: Varanasi and Mirzapur, each with configurable sub-destinations (ghats, temples, waterfalls, hidden places).
2. WHEN an Admin creates a sub-destination, THE Platform SHALL associate the sub-destination with a parent destination and store name, description, location coordinates, category, and media references.
3. WHEN a destination listing request is received, THE Platform SHALL return destinations with their associated sub-destinations in a hierarchical structure.
4. WHEN an Admin submits a destination deletion request, THE Platform SHALL perform a Soft_Delete on the destination and all associated sub-destinations.

### Requirement 7: Booking Management

**User Story:** As a customer, I want to book a travel package through a guided multi-step flow, so that I can customize and confirm my trip.

#### Acceptance Criteria

1. WHEN a Customer initiates a booking, THE Booking_Service SHALL create a booking record with status "draft" and associate the selected package, travel dates, number of travellers, and traveller type.
2. WHEN a Customer submits booking details (hotel preference, transport preferences, add-ons), THE Booking_Service SHALL update the booking to status "pending_payment" and calculate the total price.
3. WHEN payment confirmation is received for a booking, THE Booking_Service SHALL update the booking status to "confirmed" and trigger a confirmation notification.
4. THE Booking_Service SHALL support the following booking statuses: draft, pending_payment, confirmed, in_progress, completed, cancelled, and refunded.
5. WHEN a Customer requests cancellation of a booking with status "confirmed", THE Booking_Service SHALL update the status to "cancelled" and initiate the refund process according to the cancellation policy.
6. WHEN an Admin or Scout updates a booking status to "in_progress", THE Booking_Service SHALL record the status change with a timestamp and the acting user.
7. WHEN a booking listing request is received by a Customer, THE Booking_Service SHALL return only bookings belonging to that Customer, with pagination and filtering by status.

### Requirement 8: Hotel Partner Management

**User Story:** As a hotel partner, I want to manage my property listing and room availability, so that the platform can include my hotel in packages.

#### Acceptance Criteria

1. WHEN an Admin registers a new hotel partner, THE Platform SHALL create the hotel record with name, address, star rating, amenities, contact details, and partner user association.
2. WHEN a Hotel_Partner submits room type details, THE Platform SHALL store room type name, capacity, base price, description, and amenities for that hotel.
3. WHEN a Hotel_Partner updates room availability for a date range, THE Platform SHALL record the available room count per room type for the specified dates.
4. WHEN the Booking_Service requests hotel availability for a destination and date range, THE Platform SHALL return hotels with available rooms matching the criteria.
5. IF a Hotel_Partner attempts to set availability for a past date, THEN THE Platform SHALL reject the request with HTTP 422 status and a descriptive error message.

### Requirement 9: Scout Management

**User Story:** As an admin, I want to assign scouts to bookings, so that travellers receive personal guidance upon arrival.

#### Acceptance Criteria

1. WHEN an Admin creates a scout profile, THE Platform SHALL store the scout's name, phone number, languages spoken, specializations, operating area (Varanasi or Mirzapur), and availability status.
2. WHEN a booking is confirmed, THE Platform SHALL allow an Admin to assign an available scout to the booking based on destination and date.
3. WHEN a scout is assigned to a booking, THE Platform SHALL update the scout's availability for the booking dates and record the assignment.
4. WHEN a Customer submits a rating for a scout after trip completion, THE Platform SHALL store the rating (1-5) and optional review text.
5. WHEN a scout listing request is received by an Admin, THE Platform SHALL return scouts with their current availability, average rating, and assignment count.

### Requirement 10: Driver Management

**User Story:** As an admin, I want to manage drivers and assign them to bookings, so that travellers have reliable transportation.

#### Acceptance Criteria

1. WHEN an Admin creates a driver profile, THE Platform SHALL store the driver's name, phone number, vehicle type, vehicle number, license details, operating area, and availability status.
2. WHEN an Admin assigns a driver to a booking, THE Platform SHALL update the driver's availability for the booking dates and record the assignment.
3. WHEN a Customer submits a rating for a driver after trip completion, THE Platform SHALL store the rating (1-5) and optional review text.
4. IF a driver assignment is requested for dates where the driver is already assigned, THEN THE Platform SHALL reject the request with HTTP 409 status and indicate the scheduling conflict.

### Requirement 11: Payment Processing

**User Story:** As a customer, I want to make payments for my bookings, so that I can confirm my trip.

#### Acceptance Criteria

1. WHEN a Customer initiates payment for a booking, THE Payment_Service SHALL create a payment record with amount, currency (INR), payment method, and status "pending".
2. WHEN a payment gateway callback confirms successful payment, THE Payment_Service SHALL update the payment status to "completed" and trigger booking confirmation.
3. IF a payment gateway callback indicates failure, THEN THE Payment_Service SHALL update the payment status to "failed" and notify the Customer.
4. THE Payment_Service SHALL support partial payments and record each payment transaction against the booking total.
5. WHEN a refund is initiated, THE Payment_Service SHALL create a refund record with original payment reference, refund amount, and status "processing".

### Requirement 12: Invoice Generation

**User Story:** As a customer, I want to receive invoices for my bookings, so that I have documentation of my payments.

#### Acceptance Criteria

1. WHEN a booking payment is completed, THE Platform SHALL generate an invoice record with unique invoice number, customer details, booking details, itemized charges, taxes, and total amount.
2. WHEN a Customer requests an invoice, THE Platform SHALL return the invoice data in a format suitable for PDF generation.
3. THE Platform SHALL assign sequential invoice numbers following the pattern INV-YYYYMM-XXXXX where XXXXX is a zero-padded sequential number.

### Requirement 13: Review and Rating System

**User Story:** As a customer, I want to leave reviews for packages and services, so that other travellers can make informed decisions.

#### Acceptance Criteria

1. WHEN a Customer with a completed booking submits a review, THE Platform SHALL store the review with rating (1-5), title, body text, associated package, and creation timestamp.
2. WHEN a review is submitted, THE Platform SHALL set the review status to "pending_moderation".
3. WHEN an Admin approves a review, THE Platform SHALL set the review status to "published" and update the package's average rating.
4. WHEN an Admin rejects a review, THE Platform SHALL set the review status to "rejected" and record the rejection reason.
5. IF a Customer attempts to submit a review for a booking that is not in "completed" status, THEN THE Platform SHALL reject the request with HTTP 403 status.

### Requirement 14: Gallery and Image Management

**User Story:** As an admin, I want to manage images for packages, destinations, and hotels, so that the platform has rich visual content.

#### Acceptance Criteria

1. WHEN an Admin uploads an image, THE Platform SHALL store the image metadata including filename, file size, MIME type, dimensions, associated entity (package, destination, or hotel), display order, and alt text.
2. THE Platform SHALL validate uploaded images to accept only JPEG, PNG, and WebP formats with a maximum file size of 10 MB.
3. WHEN an image listing request is received for an entity, THE Platform SHALL return images sorted by display order.
4. WHEN an Admin deletes an image, THE Platform SHALL remove the image metadata record and mark the associated file for cleanup.

### Requirement 15: Blog and Content Management

**User Story:** As an admin, I want to publish blog posts about destinations, so that the platform attracts organic traffic and informs travellers.

#### Acceptance Criteria

1. WHEN an Admin creates a blog post, THE Platform SHALL store title, slug (URL-friendly), body content, author, category, tags, featured image reference, SEO title, SEO description, and publication status (draft or published).
2. WHEN a blog listing request is received, THE Platform SHALL return paginated blog posts with filtering by category, tag, and publication status.
3. WHEN a blog post is published, THE Platform SHALL record the published_at timestamp.
4. THE Platform SHALL enforce unique slugs across all blog posts.

### Requirement 16: Enterprise and Corporate Bookings

**User Story:** As a corporate client, I want to make bulk bookings for group trips, so that my organization's travel is managed efficiently.

#### Acceptance Criteria

1. WHEN a Customer or Admin creates an enterprise booking, THE Platform SHALL store company name, contact person, group size, travel dates, special requirements, and budget range.
2. THE Platform SHALL support enterprise bookings for group sizes ranging from 5 to 500 travellers.
3. WHEN an enterprise booking is submitted, THE Booking_Service SHALL set its status to "pending_review" for Admin approval before confirmation.
4. WHEN an Admin approves an enterprise booking, THE Booking_Service SHALL generate an itemized quotation and update the status to "quotation_sent".

### Requirement 17: Coupon and Discount Management

**User Story:** As an admin, I want to create discount coupons, so that the platform can run promotions and reward customers.

#### Acceptance Criteria

1. WHEN an Admin creates a coupon, THE Platform SHALL store coupon code, discount type (percentage or fixed amount), discount value, minimum booking amount, maximum discount cap, validity start date, validity end date, and usage limit.
2. WHEN a Customer applies a coupon code to a booking, THE Platform SHALL validate the coupon against expiry date, usage limit, and minimum booking amount, and apply the discount if valid.
3. IF a Customer applies an expired, fully-used, or invalid coupon, THEN THE Platform SHALL reject the application with HTTP 422 status and a descriptive error message.
4. THE Platform SHALL enforce unique coupon codes across all coupons.
5. WHEN a coupon is successfully applied to a booking, THE Platform SHALL increment the coupon's usage count.

### Requirement 18: Wishlist Management

**User Story:** As a customer, I want to save packages to a wishlist, so that I can review and book them later.

#### Acceptance Criteria

1. WHEN a Customer adds a package to the wishlist, THE Platform SHALL create a wishlist entry associating the Customer with the package and recording the timestamp.
2. WHEN a Customer removes a package from the wishlist, THE Platform SHALL delete the wishlist entry.
3. WHEN a Customer requests the wishlist, THE Platform SHALL return all wishlisted packages with current pricing and availability status.
4. IF a Customer attempts to add a package that already exists in the wishlist, THEN THE Platform SHALL reject the request with HTTP 409 status.

### Requirement 19: Notification System

**User Story:** As a user, I want to receive notifications about my bookings and platform updates, so that I stay informed.

#### Acceptance Criteria

1. WHEN a booking status changes, THE Notification_Service SHALL create an in-app notification for the associated Customer with notification type, title, body, and reference to the booking.
2. WHEN a notification listing request is received, THE Notification_Service SHALL return paginated notifications for the authenticated user, sorted by creation date descending.
3. WHEN a user marks a notification as read, THE Notification_Service SHALL update the notification's read status and record the read timestamp.
4. THE Notification_Service SHALL store a delivery_channel field (in_app, email) for each notification to support future email delivery.

### Requirement 20: Support Ticket System

**User Story:** As a customer, I want to raise support tickets, so that I can get help with issues during my trip.

#### Acceptance Criteria

1. WHEN a Customer creates a support ticket, THE Platform SHALL store subject, description, priority (low, medium, high, urgent), associated booking reference (optional), and set status to "open".
2. WHEN an Admin or the ticket owner adds a reply to a ticket, THE Platform SHALL store the reply with author, body text, and timestamp.
3. WHEN an Admin updates a ticket status, THE Platform SHALL record the new status (open, in_progress, resolved, closed) and the status change timestamp.
4. WHEN a Customer requests their support tickets, THE Platform SHALL return tickets belonging to that Customer with pagination and filtering by status.

### Requirement 21: API Response Format and Error Handling

**User Story:** As a frontend developer, I want consistent API responses, so that I can build reliable client applications.

#### Acceptance Criteria

1. THE API SHALL return all successful responses in the format: `{"success": true, "data": <response_data>, "message": <string>}`.
2. THE API SHALL return all error responses in the format: `{"success": false, "error": {"code": <string>, "message": <string>, "details": <object|null>}}`.
3. THE API SHALL use appropriate HTTP status codes: 200 for success, 201 for creation, 204 for deletion, 400 for bad request, 401 for unauthorized, 403 for forbidden, 404 for not found, 409 for conflict, 422 for validation error, 429 for rate limit exceeded, and 500 for server error.
4. WHEN an unhandled exception occurs, THE API SHALL log the full error details and return HTTP 500 with a generic error message that does not expose internal implementation details.

### Requirement 22: Pagination, Filtering, and Sorting

**User Story:** As a frontend developer, I want consistent pagination and filtering across list endpoints, so that I can efficiently display large datasets.

#### Acceptance Criteria

1. THE API SHALL support pagination on all list endpoints using `page` and `per_page` query parameters with a default page size of 20 and a maximum page size of 100.
2. THE API SHALL include pagination metadata in list responses: `{"total": <int>, "page": <int>, "per_page": <int>, "total_pages": <int>}`.
3. THE API SHALL support sorting on list endpoints using a `sort_by` query parameter with format `field_name` (ascending) or `-field_name` (descending).
4. THE API SHALL support text search on applicable list endpoints using a `search` query parameter.

### Requirement 23: Database Design and Audit

**User Story:** As a platform operator, I want proper database design with audit capabilities, so that data integrity is maintained and changes are traceable.

#### Acceptance Criteria

1. THE Platform SHALL include `created_at` and `updated_at` timestamp columns on all database tables.
2. THE Platform SHALL implement Soft_Delete on the following entities: users, packages, bookings, hotels, destinations, blog posts, and reviews.
3. THE Platform SHALL enforce referential integrity through foreign key constraints on all related tables.
4. THE Platform SHALL maintain proper database indexes on foreign key columns, frequently queried columns, and unique constraint columns.

### Requirement 24: Health Check and Monitoring

**User Story:** As a DevOps engineer, I want health check endpoints, so that I can monitor the platform's operational status.

#### Acceptance Criteria

1. THE API SHALL expose a `/health` endpoint that returns HTTP 200 with service status, database connectivity status, and application version.
2. THE API SHALL expose the `/health` endpoint without requiring authentication.
3. IF the database connection is unavailable, THEN THE API SHALL return HTTP 503 on the `/health` endpoint with a status indicating database connectivity failure.

### Requirement 25: Logging and Audit Trail

**User Story:** As a platform operator, I want structured logging and audit trails, so that I can debug issues and track user actions.

#### Acceptance Criteria

1. THE Platform SHALL log all API requests with request method, path, authenticated user identifier (if applicable), response status code, and response time in milliseconds.
2. THE Platform SHALL use structured JSON logging format for all log output.
3. WHEN an Admin or Super_Admin performs a create, update, or delete operation, THE Platform SHALL record an audit log entry with actor, action, target entity, target identifier, and timestamp.

### Requirement 26: Security and Input Validation

**User Story:** As a platform operator, I want robust security measures, so that the platform is protected against common attacks.

#### Acceptance Criteria

1. THE Platform SHALL validate all request inputs using schema-based validation (Marshmallow) before processing business logic.
2. THE Platform SHALL use parameterized queries (via SQLAlchemy ORM) for all database operations to prevent SQL injection.
3. THE Platform SHALL include CORS headers configured to allow only specified frontend origins.
4. THE Platform SHALL store all secrets (database credentials, JWT secret, API keys) in environment variables and never in source code.
5. THE Platform SHALL set secure, httpOnly flags on any cookies used for authentication.

### Requirement 27: API Versioning and Documentation

**User Story:** As a frontend developer, I want versioned and documented APIs, so that I can integrate reliably and handle API evolution.

#### Acceptance Criteria

1. THE API SHALL prefix all endpoints with `/api/v1/` to support future versioning.
2. THE API SHALL provide OpenAPI/Swagger documentation accessible at a designated documentation endpoint.
3. THE API SHALL include descriptive endpoint summaries, request/response schemas, and authentication requirements in the OpenAPI specification.
