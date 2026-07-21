# YatraFlow — Product Roadmap & User Flow

## Vision

YatraFlow is a premium curated travel platform for Varanasi and Mirzapur. The core promise: **"Just reach Varanasi or Mirzapur. We take care of everything else."**

---

## User Flow — Complete Journey

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          LANDING PAGE (Home)                              │
│                                                                          │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │   Hero   │  │   Featured   │  │ Destinations │  │ Testimonials  │   │
│  │  Banner  │  │   Packages   │  │  Highlights  │  │   Carousel    │   │
│  └─────┬────┘  └──────┬───────┘  └──────┬───────┘  └───────────────┘   │
│        │               │                 │                               │
└────────┼───────────────┼─────────────────┼───────────────────────────────┘
         │               │                 │
         ▼               ▼                 ▼
┌─────────────┐  ┌──────────────┐  ┌──────────────┐
│  Packages   │  │   Package    │  │ Destinations │
│   Listing   │  │    Detail    │  │     Page     │
│ (Browse All)│  │  (Itinerary) │  │ (Sub-spots)  │
└──────┬──────┘  └──────┬───────┘  └──────────────┘
       │                │
       │                ▼
       │        ┌──────────────┐
       │        │  Book Now    │──── Requires Login
       │        │    (CTA)     │
       │        └──────┬───────┘
       │               │
       ▼               ▼
┌──────────────────────────────────────────┐
│           AUTH GATE                        │
│                                           │
│   ┌──────────┐       ┌───────────┐       │
│   │  Login   │◄─────►│ Register  │       │
│   │  (Email) │       │(Email/Pwd)│       │
│   │  Google  │       │  Google   │       │
│   └────┬─────┘       └─────┬─────┘       │
│        │                    │             │
└────────┼────────────────────┼─────────────┘
         │                    │
         ▼                    ▼
┌──────────────────────────────────────────┐
│         AUTHENTICATED USER AREA           │
│                                           │
│  ┌─────────────────────────────────────┐  │
│  │           DASHBOARD                  │  │
│  │                                      │  │
│  │  ┌─────────┐ ┌────────┐ ┌────────┐  │  │
│  │  │ My Stats│ │Upcoming│ │Completed│  │  │
│  │  │ Overview│ │ Trips  │ │  Trips  │  │  │
│  │  └─────────┘ └────────┘ └────────┘  │  │
│  │                                      │  │
│  │  ┌──────────────────────────────┐    │  │
│  │  │      Booking Cards           │    │  │
│  │  │  [View] [Cancel] [Complete]  │    │  │
│  │  └──────────────────────────────┘    │  │
│  └─────────────────────────────────────┘  │
│                                           │
│  ┌─────────────────────────────────────┐  │
│  │       BOOKING FLOW (3 Steps)        │  │
│  │                                      │  │
│  │  Step 1         Step 2       Step 3  │  │
│  │  ┌────────┐   ┌────────┐  ┌──────┐  │  │
│  │  │ Dates &│──►│Hotel & │─►│Review│  │  │
│  │  │Travellr│   │Transpt │  │& Pay │  │  │
│  │  └────────┘   └────────┘  └──┬───┘  │  │
│  │                               │      │  │
│  │                               ▼      │  │
│  │                        ┌──────────┐  │  │
│  │                        │ Booking  │  │  │
│  │                        │Confirmed!│  │  │
│  │                        └──────────┘  │  │
│  └─────────────────────────────────────┘  │
│                                           │
│  ┌─────────────────────────────────────┐  │
│  │         SUPPORT TICKET               │  │
│  │  Subject + Priority + Description    │  │
│  │  → Ticket Submitted ✓               │  │
│  └─────────────────────────────────────┘  │
│                                           │
└───────────────────────────────────────────┘
```

---

## Page-by-Page User Interaction

### 1. Home Page (`/`)

**Purpose:** First impression, build trust, drive exploration.

| Section | User Action | Result |
|---------|-------------|--------|
| Hero Banner | Click "Explore Packages" | → Packages page |
| Hero Banner | Click "View Destinations" | → Destinations page |
| Stats Bar | View (no click) | Builds trust (2500+ travellers, 4.8★) |
| Features Row | View (no click) | Safe, Hassle-Free, Curated, Local Experts |
| Featured Packages (3 cards) | Click card | → Package Detail page |
| Featured Packages | Click "View All Packages" | → Packages listing |
| Destinations (2 cards) | Click Varanasi/Mirzapur | → Destinations page |
| Testimonials (3 cards) | Read reviews | Social proof |
| CTA Section | Click "Browse Packages" | → Packages page |
| CTA Section | Click "Talk to Us" | → Support page |

**Test Checklist:**
- [ ] Hero images load correctly
- [ ] CTA buttons navigate to correct pages
- [ ] Package cards are clickable
- [ ] Animations are smooth on scroll
- [ ] Mobile responsive (hamburger menu works)

---

### 2. Packages Page (`/packages`)

**Purpose:** Browse and filter all available travel packages.

| Element | User Action | Result |
|---------|-------------|--------|
| Filter: Destination | Select Varanasi/Mirzapur/All | Grid filters live |
| Filter: Duration | Select range (1-2 days, 3-5 days, etc.) | Grid filters |
| Filter: Traveller Type | Select solo/couple/family/group | Grid filters |
| Filter: Price Range | Slide min-max | Grid filters |
| Search Box | Type keywords | Filters by title/description |
| Package Card | Click anywhere | → Package Detail page |
| Package Card | View rating, price, duration badges | Information scan |
| Pagination | Click next/prev | Load more packages |

**Test Checklist:**
- [ ] Filters work independently and combined
- [ ] Cards show correct price, rating, destination badge
- [ ] Clicking a card navigates to detail page with correct ID
- [ ] Empty state shown when no packages match filters
- [ ] Mobile: filters collapse into sheet/modal

---

### 3. Package Detail (`/packages/:id`)

**Purpose:** Convince user to book — show full experience.

| Section | User Action | Result |
|---------|-------------|--------|
| Hero Image | View large destination image | Visual appeal |
| Package Title + Meta | View duration, rating, destination | Quick info |
| Pricing Tiers (3 cards) | Compare Budget/Comfort/Luxury | Tier selection |
| "Book Now" Button | Click | → Booking Flow (if logged in) OR → Login |
| Day-wise Itinerary | Click accordion day | Expands activities list |
| Inclusions List | View ✓ items | Set expectations |
| Exclusions List | View ✗ items | Transparency |

**Test Checklist:**
- [ ] Correct package loads based on URL ID
- [ ] All 3 pricing tiers display with prices
- [ ] Itinerary accordion expands/collapses
- [ ] "Book Now" redirects to login if not authenticated
- [ ] "Book Now" goes to booking flow if authenticated
- [ ] Back button returns to packages listing

---

### 4. Destinations (`/destinations`)

**Purpose:** Showcase Varanasi & Mirzapur's highlights.

| Section | User Action | Result |
|---------|-------------|--------|
| Varanasi Section | View sub-destination cards | See ghats, temples, lanes, food, silk, sarnath |
| Mirzapur Section | View sub-destination cards | See waterfalls, forts, temples, caves, nature, carpets |
| Sub-destination Card | Click | Could navigate to filtered packages (future) |
| Image Gallery | View photos | Visual exploration |

**Test Checklist:**
- [ ] Both destinations render with 6 sub-destinations each
- [ ] Images load (from Unsplash)
- [ ] Cards have hover effects
- [ ] Mobile: cards stack vertically

---

### 5. Login (`/login`)

**Purpose:** Authenticate returning users.

| Element | User Action | Result |
|---------|-------------|--------|
| Email Input | Type email | Validates format |
| Password Input | Type password | Validates length (6+) |
| Eye Icon | Toggle | Show/hide password |
| "Log In" Button | Click (valid) | API call → Dashboard redirect |
| "Log In" Button | Click (invalid) | Error message shown |
| "Sign in with Google" | Click | Google OAuth (future) |
| "Sign up" Link | Click | → Register page |
| "Forgot password" Link | Click | → (Future feature) |
| Remember Me Checkbox | Toggle | (Future: persist session longer) |

**Test Checklist:**
- [ ] Valid login → navigates to `/dashboard`
- [ ] Invalid credentials → shows "Invalid email or password"
- [ ] Duplicate login attempt → proper error
- [ ] Navbar updates to show user name + Logout
- [ ] Empty fields show validation errors

---

### 6. Register (`/register`)

**Purpose:** Create new customer account.

| Element | User Action | Result |
|---------|-------------|--------|
| Full Name Input | Type name | Required validation |
| Email Input | Type email | Format validation |
| Phone Input | Type 10-digit number | Pattern validation |
| Password Input | Type 8+ chars | Length validation |
| Confirm Password | Must match password | Match validation |
| "Create Account" Button | Click (valid) | API call → Dashboard redirect |
| "Sign up with Google" | Click | Google OAuth (future) |
| "Log in" Link | Click | → Login page |
| Terms Checkbox | Toggle | (Future: required) |

**Test Checklist:**
- [ ] Valid registration → auto-login → navigates to `/dashboard`
- [ ] Duplicate email → shows "An account with this email already exists"
- [ ] Short password → shows validation error
- [ ] Phone format validation works
- [ ] Navbar updates after successful registration

---

### 7. Dashboard (`/dashboard`)

**Purpose:** Overview of user's bookings and trips.

| Element | User Action | Result |
|---------|-------------|--------|
| Stats Cards (4) | View | Total bookings, upcoming, completed, spent |
| "Book New Trip" Button | Click | → Packages page |
| Booking Card | View status badge | Draft/Confirmed/In Progress/Completed/Cancelled |
| "View" Button | Click | Shows booking details (alert for now) |
| "Complete Booking" Button | Click (draft) | → Booking flow to finish |
| "View Details" Button | Click (confirmed) | Shows trip details |

**Test Checklist:**
- [ ] Dashboard only accessible when logged in
- [ ] Shows correct number of bookings
- [ ] Status badges have correct colors
- [ ] "Book New Trip" navigates to packages
- [ ] "View" shows booking info

---

### 8. Booking Flow (`/book/:packageId`)

**Purpose:** Multi-step wizard to book a package.

| Step | Elements | User Action |
|------|----------|-------------|
| **Step 1: Dates & Travellers** | Date picker (start/end), Number of travellers, Traveller type dropdown | Fill in → Click "Next" |
| **Step 2: Preferences** | Hotel selection, Transport preference, Add-ons checkboxes | Select options → Click "Next" |
| **Step 3: Review & Pay** | Summary of all selections, Price breakdown, "Confirm Booking" button | Review → Click "Confirm" |
| **Success** | Confirmation message, Booking ID, "Go to Dashboard" button | View confirmation → Navigate |

**Test Checklist:**
- [ ] Step navigation (Next/Back) works
- [ ] Step indicators show progress
- [ ] Required fields validated before advancing
- [ ] Price updates based on selections
- [ ] Confirm creates booking via API
- [ ] Success state shows booking number
- [ ] Redirects to dashboard after confirmation

---

### 9. Support (`/support`)

**Purpose:** Raise issues and get help.

| Element | User Action | Result |
|---------|-------------|--------|
| Contact Info Cards | View phone, email, address, hours | Reference info |
| Name Input | Type full name | Required |
| Email Input | Type email | Required, validated |
| Subject Input | Type issue summary | Required |
| Priority Dropdown | Select Low/Medium/High/Urgent | Sets priority |
| Description Textarea | Type detailed issue | Required |
| "Submit Ticket" Button | Click (valid) | Shows success confirmation |
| Success State | View ticket confirmation | "Submit Another" option |

**Test Checklist:**
- [ ] All fields validate on submit
- [ ] Success state displays after submission
- [ ] "Submit Another" resets the form
- [ ] Contact info is visible and correct

---

## Navigation Map

```
                    ┌──── NAVBAR (always visible) ────┐
                    │                                  │
                    │  Logo  Home  Packages  Dests     │
                    │  Support  [Dashboard] [Login]    │
                    │                                  │
                    └─────────────┬────────────────────┘
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        │                         │                         │
        ▼                         ▼                         ▼
   Public Pages            Auth Pages              Protected Pages
   ─────────────           ──────────              ───────────────
   • Home /                • Login /login          • Dashboard /dashboard
   • Packages /packages    • Register /register    • Booking Flow /book/:id
   • Package /:id                                  • (Future: Profile)
   • Destinations                                  • (Future: My Reviews)
   • Support /support
```

---

## Product Roadmap

### Phase 1 — MVP ✅ (Current)

| Feature | Status | Notes |
|---------|--------|-------|
| Landing page with hero, packages, destinations, testimonials | ✅ Done | Static content |
| Package browsing with filters | ✅ Done | Mock data |
| Package detail with itinerary | ✅ Done | Mock data |
| Destinations page | ✅ Done | Mock data |
| User registration (email/password) | ✅ Done | Connected to API |
| User login (email/password) | ✅ Done | Connected to API |
| JWT authentication with refresh | ✅ Done | Auto-refresh on expiry |
| Dashboard with booking cards | ✅ Done | Mock bookings |
| Multi-step booking wizard | ✅ Done | UI only (mock) |
| Support ticket form | ✅ Done | UI only |
| Backend API deployed on Render | ✅ Done | https://yatraflow-api.onrender.com |
| Frontend deployed on GitHub Pages | ✅ Done | https://8mishra.github.io/local-travel |

### Phase 2 — Full API Integration (Next)

| Feature | Priority | Effort |
|---------|----------|--------|
| Seed database with real packages & destinations | High | 1 hr |
| Connect Packages page to API (replace mock data) | High | 2 hr |
| Connect Destinations page to API | High | 1 hr |
| Connect Dashboard to real bookings API | High | 2 hr |
| Booking flow creates real bookings in DB | High | 3 hr |
| Support ticket creates real tickets in DB | Medium | 1 hr |
| Admin panel (manage packages, view bookings) | Medium | 8 hr |

### Phase 3 — Enhanced Features

| Feature | Priority | Effort |
|---------|----------|--------|
| Google OAuth (login/register) | High | 4 hr |
| Payment gateway integration (Razorpay) | High | 8 hr |
| Email notifications (booking confirmed, etc.) | Medium | 4 hr |
| Image upload for packages/destinations | Medium | 4 hr |
| Review & rating system (post-trip) | Medium | 4 hr |
| Coupon/discount code at checkout | Medium | 2 hr |
| Wishlist (save packages for later) | Low | 2 hr |
| Blog page with real CMS content | Low | 4 hr |

### Phase 4 — Operations & Scale

| Feature | Priority | Effort |
|---------|----------|--------|
| Scout/Driver assignment system | High | 6 hr |
| Hotel partner portal | Medium | 8 hr |
| Real-time notifications (WebSocket) | Medium | 6 hr |
| Analytics dashboard (admin) | Medium | 6 hr |
| Multi-language support (Hindi) | Low | 8 hr |
| Mobile app (React Native) | Low | 40 hr |
| SEO optimization + sitemap | Low | 2 hr |

---

## User Personas & Journeys

### Persona 1: Priya (Weekend Traveller, 28, Mumbai)
```
Google search "Varanasi trip package"
  → Lands on Home page
  → Scrolls featured packages
  → Clicks "Weekend Getaway: Varanasi Express"
  → Reads itinerary, checks pricing
  → Clicks "Book Now"
  → Redirected to Register (new user)
  → Signs up with email
  → Booking flow: selects dates, 2 travellers, couple
  → Selects Comfort tier, boutique hotel
  → Reviews & confirms
  → Gets booking confirmation
  → Checks Dashboard for status
```

### Persona 2: Vikram (Family Trip, 45, Jaipur)
```
Friend recommends YatraFlow link
  → Lands on Home page
  → Clicks "View Destinations"
  → Explores Varanasi sub-destinations
  → Goes to Packages, filters: Family + 5 days
  → Clicks "Complete Kashi Darshan"
  → Compares pricing tiers (picks Comfort)
  → Clicks "Book Now"
  → Logs in (existing account)
  → Booking: 5 travellers, family, dates in March
  → Selects 4-star hotel, AC sedan
  → Confirms booking
  → Receives confirmation on dashboard
```

### Persona 3: Rahul (Adventure Group, 24, Delhi)
```
Sees Instagram ad about Mirzapur waterfalls
  → Visits YatraFlow directly
  → Goes to Packages, filters: Mirzapur + Adventure
  → Clicks "Mirzapur Adventure Trail"
  → Reads about waterfalls, forts
  → Books for 4 friends, group tier
  → Has a question → goes to Support
  → Submits ticket: "Can we add rappelling?"
  → Gets response within 24 hours
  → Confirms the booking
```

---

## Manual Testing Checklist

### Critical Path (Must Work)
- [ ] Home page loads fully (hero, packages, destinations, footer)
- [ ] Navigate to Packages from Home
- [ ] Filter packages by destination
- [ ] Open a package detail page
- [ ] Click "Book Now" → redirected to Login
- [ ] Register a new account
- [ ] Navbar updates to show user name
- [ ] Navigate to Dashboard
- [ ] Dashboard shows stats and booking cards
- [ ] Logout → navbar reverts to Login/Signup
- [ ] Login with existing account → Dashboard
- [ ] Submit a support ticket → success message

### Edge Cases
- [ ] Register with existing email → 409 error shown
- [ ] Login with wrong password → generic error
- [ ] Access Dashboard without login → redirect to Login
- [ ] Refresh page while logged in → stays logged in
- [ ] Token expires → auto-refresh works
- [ ] Mobile: all pages responsive
- [ ] Mobile: hamburger menu works
- [ ] All images load (Unsplash CDN)
- [ ] 404 page for unknown routes

---

## Tech Architecture (Deployed)

```
┌───────────────────────────────────────────────────────────┐
│                      USERS (Browser)                       │
└───────────────────────────┬───────────────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │                           │
              ▼                           ▼
┌──────────────────────┐    ┌──────────────────────────┐
│   GitHub Pages       │    │   Render.com             │
│   (Frontend)         │    │   (Backend API)          │
│                      │    │                          │
│ React + Vite + TW    │───►│ Flask + Gunicorn         │
│ 8mishra.github.io/   │    │ yatraflow-api.onrender   │
│ local-travel         │    │ .com/api/v1/             │
└──────────────────────┘    └────────────┬─────────────┘
                                         │
                                         ▼
                            ┌──────────────────────────┐
                            │   Render PostgreSQL      │
                            │   (Database)             │
                            │   yatraflowdb            │
                            │   Singapore region       │
                            └──────────────────────────┘
```

---

*Last updated: July 2026*
