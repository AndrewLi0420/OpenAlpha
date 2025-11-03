# Epic Technical Specification: Foundation & User Authentication

Date: 2025-10-30
Author: Andrew
Epic ID: 1
Status: Draft

---

## Overview

Epic 1 establishes the foundational infrastructure for OpenAlpha, as outlined in the PRD (FR001-FR004, FR026). This epic creates the core platform that enables secure user authentication, preference management, and freemium tier enforcement. The foundation supports all subsequent ML-powered recommendation features by establishing user accounts, session management, and the base UI framework. Per the PRD goals, this enables users to personalize their experience and validates the freemium business model from launch by enforcing tier limits.

The epic delivers seven sequentially-ordered stories covering project infrastructure setup, database schema design, user registration and authentication, profile management, tier enforcement, and responsive UI foundation. This epic has no forward dependencies and serves as the prerequisite for Epic 2 (Data Pipeline & ML Engine) and Epic 3 (Recommendations & Dashboard).

## Objectives and Scope

**In-Scope:**
- React + TypeScript frontend project initialization with Vite
- FastAPI backend project initialization with Python
- PostgreSQL database schema design and implementation for core tables (users, user_preferences, stocks, market_data, sentiment_data, recommendations)
- User registration with email/password validation and email verification flow
- Secure authentication using JWT tokens via FastAPI Users with session persistence
- User profile management for holding period (daily/weekly/monthly) and risk tolerance (low/medium/high) preferences
- Freemium tier enforcement: free tier limited to 5 stocks, premium tier unlimited (per PRD FR003)
- Responsive UI foundation with Tailwind CSS, black background, financial blue/green accents
- Docker Compose setup for local development (PostgreSQL, Redis)
- Free-tier deployment configuration documentation (Render, Vercel, Supabase)
- Navigation structure and basic layout components (header, sidebar/nav, main content area)

**Out-of-Scope:**
- ML model implementation (deferred to Epic 2)
- Recommendation generation (deferred to Epic 2)
- Market data collection (deferred to Epic 2)
- Sentiment analysis (deferred to Epic 2)
- Payment integration for premium upgrades (UI prompts only, payment processing deferred)
- Advanced analytics or portfolio tracking
- Social features or user communities
- Native mobile apps (web-first responsive only)

## System Architecture Alignment

This epic aligns with the architecture document's foundation decisions: React 18+ with TypeScript frontend on Vercel, FastAPI backend on Render, PostgreSQL 15+ database, and Tailwind CSS 3.x styling framework. The implementation follows the project structure patterns defined in architecture.md with `backend/app/models/user.py`, `backend/app/api/v1/endpoints/auth.py`, and `frontend/src/pages/Login.tsx` organizational patterns.

Key architecture constraints applied: FastAPI Users for authentication (ADR-002), SQLAlchemy 2.0.x ORM with Alembic migrations, JWT tokens via HTTP-only cookies for security, and free-tier infrastructure deployment (Vercel + Render per ADR-004). The database schema implements the `users` and `user_preferences` tables as specified in the Data Architecture section, with proper indexing for `users.email` (unique) and foreign key relationships. Frontend uses React Query 5.x for server state management and Axios for HTTP client, aligned with the Technology Stack Details.

## Detailed Design

### Services and Modules

| Service/Module | Responsibility | Inputs | Outputs | Owner/Component |
|---------------|---------------|--------|---------|-----------------|
| **User Registration Service** | Handles new user account creation with email validation, password hashing, and duplicate detection | Email, password | User record, verification token | `backend/app/api/v1/endpoints/auth.py` (POST /register) |
| **Authentication Service** | Manages user login, JWT token generation, session validation | Email, password | JWT access token, user session | `backend/app/api/v1/endpoints/auth.py` (POST /login), FastAPI Users |
| **User Profile Service** | Manages user preferences (holding period, risk tolerance) and profile updates | User ID, preferences object | Updated preferences record | `backend/app/api/v1/endpoints/users.py` (PUT /users/me/preferences) |
| **Tier Enforcement Service** | Validates user tier (free/premium) and enforces 5-stock limit for free tier | User ID, requested action | Tier status, access permission | `backend/app/crud/users.py`, middleware in API endpoints |
| **Frontend Auth Hook** | React hook managing authentication state, token storage, protected route logic | Login/register actions | Auth state (user, isAuthenticated, token) | `frontend/src/hooks/useAuth.ts` |
| **Frontend API Client** | Axios-based HTTP client with auth headers, base URL configuration, error handling | API requests | HTTP responses, error objects | `frontend/src/services/api.ts` |
| **UI Layout Components** | Responsive navigation, header, sidebar, main content area with Tailwind styling | Navigation state | Rendered UI layout | `frontend/src/components/common/` (Header, Sidebar, Layout) |

### Data Models and Contracts

**Database Schema (PostgreSQL via SQLAlchemy):**

**Users Table** (`users`)
- `id`: UUID (primary key)
- `email`: VARCHAR(255), unique, indexed
- `password_hash`: VARCHAR(255) (bcrypt via FastAPI Users)
- `tier`: ENUM('free', 'premium'), default 'free'
- `is_verified`: BOOLEAN, default false
- `created_at`: TIMESTAMP, default now()
- `updated_at`: TIMESTAMP, default now(), on update now()

**User Preferences Table** (`user_preferences`)
- `id`: UUID (primary key)
- `user_id`: UUID (foreign key → users.id), unique (1:1 relationship)
- `holding_period`: ENUM('daily', 'weekly', 'monthly'), default 'daily'
- `risk_tolerance`: ENUM('low', 'medium', 'high'), default 'medium'
- `updated_at`: TIMESTAMP, default now(), on update now()

**Stocks Table** (`stocks`) - Referenced but populated in Epic 2
- `id`: UUID (primary key)
- `symbol`: VARCHAR(10), unique, indexed
- `company_name`: VARCHAR(255)
- `sector`: VARCHAR(100)
- `fortune_500_rank`: INTEGER

**TypeScript Types (Frontend):**

```typescript
interface User {
  id: string;
  email: string;
  tier: 'free' | 'premium';
  is_verified: boolean;
  created_at: string;
}

interface UserPreferences {
  holding_period: 'daily' | 'weekly' | 'monthly';
  risk_tolerance: 'low' | 'medium' | 'high';
}

interface RegisterRequest {
  email: string;
  password: string;
}

interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  token_type: 'bearer';
}
```

### APIs and Interfaces

**Authentication Endpoints:**

`POST /api/v1/auth/register`
- Request Body: `{ "email": "user@example.com", "password": "securepass" }`
- Response 201: `{ "id": "uuid", "email": "user@example.com", "is_verified": false }`
- Response 400: `{ "error": { "type": "ValidationError", "message": "Email already exists" } }`
- Validation: Email format check, password requirements (min length 8, complexity)

`POST /api/v1/auth/login`
- Request Body: `{ "email": "user@example.com", "password": "securepass" }`
- Response 200: `{ "access_token": "jwt-token", "token_type": "bearer" }`
- Response 401: `{ "error": { "type": "AuthenticationError", "message": "Invalid credentials" } }`
- Sets HTTP-only cookie with JWT token

**User Endpoints:**

`GET /api/v1/users/me`
- Headers: `Authorization: Bearer {token}`
- Response 200: `{ "id": "uuid", "email": "user@example.com", "tier": "free", "preferences": {...} }`
- Response 401: Unauthorized if token invalid

`PUT /api/v1/users/me/preferences`
- Headers: `Authorization: Bearer {token}`
- Request Body: `{ "holding_period": "daily", "risk_tolerance": "medium" }`
- Response 200: Updated preferences object
- Validation: Enum values only (daily/weekly/monthly, low/medium/high)

**Frontend Components:**

`Login.tsx` - Login page component
- Props: None
- State: email, password, error message
- Actions: submit login form, redirect on success

`Register.tsx` - Registration page component
- Props: None
- State: email, password, confirmPassword, error message
- Actions: submit registration, validate password match

`Profile.tsx` - User profile and preferences page
- Props: None
- State: preferences (holding_period, risk_tolerance), loading, error
- Actions: update preferences, display tier status

### Workflows and Sequencing

**User Registration Flow:**
1. User navigates to `/register` page
2. User enters email and password, submits form
3. Frontend validates email format and password requirements client-side
4. Frontend sends POST `/api/v1/auth/register` request
5. Backend validates email uniqueness, hashes password with bcrypt
6. Backend creates user record with `tier='free'`, `is_verified=false`
7. Backend generates email verification token (via Resend)
8. Backend returns user object (201 Created)
9. Frontend redirects to login page or shows verification email sent message
10. User clicks verification link in email (future enhancement)

**User Login Flow:**
1. User navigates to `/login` page
2. User enters email and password, submits form
3. Frontend sends POST `/api/v1/auth/login` request
4. Backend validates credentials using FastAPI Users (password hash comparison)
5. Backend generates JWT token with user ID and tier
6. Backend sets HTTP-only cookie with JWT token
7. Backend returns `{ access_token, token_type }` (200 OK)
8. Frontend stores token reference in memory/React Query state
9. Frontend redirects to `/dashboard` (protected route)
10. Protected routes check auth state via `useAuth` hook

**Preferences Update Flow:**
1. User navigates to `/profile` page (requires authentication)
2. Frontend loads current preferences via GET `/api/v1/users/me`
3. User selects new holding period and/or risk tolerance from dropdowns
4. User clicks "Save Preferences" button
5. Frontend sends PUT `/api/v1/users/me/preferences` with updated values
6. Backend validates enum values, updates `user_preferences` table
7. Backend returns updated preferences (200 OK)
8. Frontend updates React Query cache, displays success message
9. Preferences persist for recommendation filtering (used in Epic 3)

**Tier Enforcement Flow:**
1. User attempts to track a stock (UI action in Epic 3)
2. Frontend sends request to backend endpoint
3. Backend middleware checks user tier via `GET /api/v1/users/me`
4. If tier is 'free', backend queries `user_stock_tracking` count
5. If count >= 5, backend returns 403 Forbidden with message: "Free tier limit reached. Upgrade for unlimited access."
6. If count < 5 or tier is 'premium', backend processes request
7. Frontend displays tier status indicator: "Tracking X/5 stocks (Free tier)" or "Premium - Unlimited"

## Non-Functional Requirements

### Performance

**Target Metrics (per PRD NFR001):**
- User registration endpoint: <500ms response time
- User login endpoint: <500ms response time (including password hash verification)
- User profile/preferences endpoints: <300ms response time
- Dashboard page load: <3 seconds (includes initial authentication check)
- Database queries: <200ms for user lookups (indexed email field)

**Optimization Strategies:**
- Database indexes on `users.email` (unique index for fast lookups)
- Database indexes on `user_preferences.user_id` (foreign key index)
- React Query caching of user profile data to minimize API calls
- Lazy loading of routes (code splitting) for Login/Register pages
- Efficient JWT token validation (stateless, no database lookup per request after initial validation)

### Security

**Authentication & Authorization (per PRD NFR004, Architecture Security section):**
- Password hashing: bcrypt with salt rounds (via FastAPI Users, default 12 rounds)
- JWT tokens: HTTP-only cookies (not localStorage) to prevent XSS attacks
- Token expiration: 24-hour access tokens with refresh token mechanism (FastAPI Users default)
- Password requirements: Minimum 8 characters, complexity validation (client and server-side)
- Email validation: Format validation on frontend and backend

**Data Protection:**
- User data encryption: At rest (PostgreSQL), in transit (HTTPS required in production)
- Password storage: Never stored in plaintext, only bcrypt hashes
- Sensitive data handling: No credit card/PII beyond email (freemium model, no payments in MVP)
- API keys: Stored in environment variables (never committed to repository)

**API Security:**
- CORS: Configured for Vercel frontend domain + localhost for development
- Input validation: Pydantic schemas validate all request bodies
- SQL injection prevention: SQLAlchemy ORM parameterized queries (no raw SQL)
- Error messages: Generic error messages for authentication failures (don't reveal if email exists)

### Reliability/Availability

**Availability Targets (per PRD NFR002):**
- System availability: 95%+ during business hours (free-tier infrastructure constraints)
- Deployment: Vercel (frontend) + Render (backend) with automatic failover
- Database: Render PostgreSQL managed service with automatic backups

**Error Handling:**
- Registration failures: Graceful handling of duplicate email errors with user-friendly messages
- Login failures: Generic error messages ("Invalid credentials") to prevent user enumeration
- Database connection failures: Connection pooling with retry logic (SQLAlchemy)
- Network failures: Frontend retry logic via React Query (3 retries with exponential backoff)

**Degradation Behavior:**
- If authentication service unavailable: Frontend shows maintenance message
- If database unavailable: API returns 503 Service Unavailable with retry-after header
- Session persistence: JWT tokens remain valid even if backend temporarily unavailable (stateless auth)

### Observability

**Logging Requirements (per Architecture Logging Strategy):**
- Backend: Structured JSON logs for Render log aggregation
  - Log API requests: `logger.info("User registered", extra={"user_id": user_id, "email": email})`
  - Log authentication events: `logger.info("User logged in", extra={"user_id": user_id})`
  - Log errors: `logger.error("Registration failed", extra={"error": str(e), "email": email})`
- Frontend: Console logging for development, error boundary for production error tracking
- Log levels: DEBUG (development), INFO (production events), ERROR (production errors)

**Metrics to Track:**
- User registration success rate
- User login success/failure rate
- API endpoint response times (p50, p95, p99)
- Database query performance (slow query logging)
- Authentication token validation failures

**Monitoring:**
- Render dashboard: Backend logs and metrics visible in Render dashboard
- Vercel dashboard: Frontend build logs and deployment status
- Error tracking: Frontend error boundaries log to console (can integrate Sentry later if needed)

## Dependencies and Integrations

**Note:** Dependency manifests (package.json, requirements.txt, pyproject.toml) are not yet created as project infrastructure is part of Story 1.1. The following dependencies are required per architecture.md specifications.

**Backend Dependencies (Python/FastAPI):**
- `fastapi` (latest) - Web framework
- `fastapi-users[sqlalchemy]` (latest) - Authentication and user management
- `sqlalchemy` (2.0.x) - ORM for database operations
- `alembic` (latest) - Database migrations
- `pydantic` (latest) - Data validation and settings management
- `psycopg2-binary` (latest) - PostgreSQL database adapter
- `python-jose[cryptography]` (latest) - JWT token handling (included via FastAPI Users)
- `passlib[bcrypt]` (latest) - Password hashing (included via FastAPI Users)
- `resend` (latest) - Email service for verification emails
- `python-multipart` (latest) - Form data parsing
- `uvicorn[standard]` (latest) - ASGI server for production

**Frontend Dependencies (React/TypeScript):**
- `react` (18+) - UI framework
- `react-dom` (18+) - React DOM bindings
- `typescript` (5.x) - Type safety
- `vite` (latest) - Build tool and dev server
- `@tanstack/react-query` (5.x) - Server state management and caching
- `axios` (latest) - HTTP client for API requests
- `react-router-dom` (latest) - Client-side routing
- `tailwindcss` (3.x) - Utility-first CSS framework
- `postcss` (latest) - CSS processing (required for Tailwind)
- `autoprefixer` (latest) - CSS vendor prefixing

**Development Dependencies:**
- `eslint` - Frontend linting
- `@types/react` - TypeScript types for React
- `@types/react-dom` - TypeScript types for React DOM
- `pytest` - Backend testing framework
- `pytest-asyncio` - Async test support for FastAPI
- `black` - Python code formatting
- `ruff` - Python linting

**Infrastructure Dependencies:**
- `docker` - Local development containerization
- `docker-compose` - Multi-container orchestration
- `postgresql` (15+) - Database (via Docker Compose for local, Render PostgreSQL for production)
- `redis` (optional) - Caching/session storage (via Docker Compose, not used in Epic 1 but infrastructure prepared)

**External Integrations:**
- **Resend API** - Email service for user verification emails
  - Integration point: `backend/app/core/config.py` (API key from environment variable)
  - Used in: User registration flow (Story 1.3)
  - Rate limits: Resend free tier (3,000 emails/month)

**Version Constraints:**
- Python: 3.11+ (required for FastAPI async support)
- Node.js: 18+ (required for React 18 and Vite)
- PostgreSQL: 15+ (required for database features)

**Integration Points:**
1. Frontend ↔ Backend: REST API via Axios, base URL from `VITE_API_URL` environment variable
2. Backend ↔ Database: SQLAlchemy ORM with async support, connection string from `DATABASE_URL`
3. Backend ↔ Resend: HTTP API calls for email verification (async requests)
4. Frontend ↔ React Router: Client-side routing with protected route components

## Acceptance Criteria (Authoritative)

**Story 1.1: Project Infrastructure Setup**
1. React + TypeScript frontend project initialized with Vite
2. FastAPI backend project initialized with Python
3. PostgreSQL and Redis containers configured via Docker Compose
4. Frontend and backend can communicate via API
5. Environment variables configured for development and deployment
6. Free-tier deployment configuration documented (Render, Supabase, Vercel)

**Story 1.2: Database Schema Design**
1. Users table with: id, email, password_hash, tier (free/premium), created_at, updated_at
2. User_preferences table with: user_id, holding_period, risk_tolerance, updated_at
3. Stocks table with: symbol, company_name, sector, fortune_500_rank
4. Market_data table with: stock_id, price, volume, timestamp
5. Sentiment_data table with: stock_id, sentiment_score, source, timestamp
6. Recommendations table with: id, user_id, stock_id, signal, confidence_score, risk_level, explanation, created_at
7. All tables have appropriate indexes for query performance
8. Foreign key relationships properly defined

**Story 1.3: User Registration**
1. Registration page with email and password fields
2. Email validation (format check)
3. Password requirements enforced (minimum length, complexity)
4. Password securely hashed before storage
5. Duplicate email detection with user-friendly error message
6. Successful registration redirects to login or onboarding
7. Email verification flow (basic - can be enhanced later)

**Story 1.4: User Authentication & Session Management**
1. Login page with email and password fields
2. Secure authentication using password hashing
3. Session management (JWT tokens or session cookies)
4. Protected routes require authentication
5. Logout functionality clears session
6. Session persists across browser refreshes
7. Error messages for invalid credentials (without revealing if email exists)

**Story 1.5: User Profile & Preferences Management**
1. User profile page displays current preferences
2. Holding period dropdown: Daily, Weekly, Monthly
3. Risk tolerance dropdown: Low, Medium, High
4. Preferences save to database on update
5. Preferences persist across sessions
6. Preferences are used to filter recommendations (will be implemented in Epic 3)
7. UI clearly shows saved preferences

**Story 1.6: Freemium Tier Enforcement**
1. User tier field (free/premium) in database
2. Default tier is "free" for new users
3. API endpoints check tier status before allowing actions
4. Free tier users limited to tracking/configuring up to 5 stocks
5. Premium tier check returns unlimited access
6. UI displays tier status (free/premium indicator)
7. Upgrade prompts shown when free tier limit reached (UI only, payment integration deferred)

**Story 1.7: Responsive UI Foundation with Tailwind CSS**
1. Tailwind CSS configured and integrated
2. Black background color scheme with financial blue/green accents applied
3. Responsive design works on desktop (1920px, 1280px) and mobile (375px, 414px)
4. Navigation structure established (Dashboard, Historical, Profile)
5. Basic layout components created (header, sidebar/nav, main content area)
6. Typography optimized for numerical data display
7. Color scheme accessible (WCAG contrast requirements met)

## Traceability Mapping

| Acceptance Criteria | PRD Reference | Architecture Reference | Component/API | Test Idea |
|-------------------|---------------|------------------------|---------------|-----------|
| AC 1.1.1: React + TypeScript frontend initialized | FR026 | Frontend Framework decision, Project Structure | `frontend/` directory, `vite.config.ts` | Verify Vite project structure exists, TypeScript compilation works |
| AC 1.1.2: FastAPI backend initialized | FR026 | Backend Framework decision, Project Structure | `backend/app/main.py` | Verify FastAPI app starts, health check endpoint responds |
| AC 1.1.3: Docker Compose configured | - | Development Environment section | `docker-compose.yml` | Verify PostgreSQL and Redis containers start successfully |
| AC 1.2.1-1.2.8: Database schema implemented | FR001-FR004 | Data Architecture section | `backend/app/models/user.py`, Alembic migrations | Verify migration creates all tables with correct columns and indexes |
| AC 1.3.1-1.3.7: User registration | FR001 | Authentication Endpoints, User Registration Flow | `POST /api/v1/auth/register`, `Register.tsx` | Test registration with valid/invalid email, duplicate email, password validation |
| AC 1.4.1-1.4.7: Authentication & session | FR001 | Authentication Endpoints, User Login Flow | `POST /api/v1/auth/login`, `Login.tsx`, `useAuth.ts` | Test login with valid/invalid credentials, JWT token generation, protected route access |
| AC 1.5.1-1.5.7: Preferences management | FR002 | User Endpoints, Preferences Update Flow | `PUT /api/v1/users/me/preferences`, `Profile.tsx` | Test preference updates, enum validation, persistence across sessions |
| AC 1.6.1-1.6.7: Tier enforcement | FR003 | Tier-Aware Pattern, Tier Enforcement Flow | `backend/app/crud/users.py`, middleware | Test free tier 5-stock limit, premium unlimited access, tier status display |
| AC 1.7.1-1.7.7: Responsive UI foundation | FR026 | UI Design Goals, Tailwind CSS decision | `frontend/src/components/common/`, Tailwind config | Test responsive breakpoints, color scheme, navigation structure, WCAG contrast |

## Risks, Assumptions, Open Questions

**Risks:**
1. **Risk: FastAPI Users library compatibility issues** - FastAPI Users may have breaking changes or compatibility issues with latest FastAPI versions
   - Mitigation: Pin FastAPI Users to stable version, test thoroughly in development environment
   - Next step: Verify FastAPI Users compatibility before Story 1.3 implementation

2. **Risk: Free-tier infrastructure limitations** - Render free tier may have cold starts or resource constraints affecting authentication latency
   - Mitigation: Monitor Render dashboard metrics, optimize JWT validation to be stateless, consider Render paid tier if needed
   - Next step: Test authentication endpoints under load to identify bottlenecks

3. **Risk: Email verification delivery failures** - Resend free tier (3,000 emails/month) may be insufficient or emails may be marked as spam
   - Mitigation: Monitor email delivery rates, implement email verification retry logic, consider upgrade to Resend paid tier if needed
   - Next step: Test email delivery to various email providers during Story 1.3

4. **Risk: JWT token security vulnerabilities** - Token expiration or refresh token logic may have security gaps
   - Mitigation: Use FastAPI Users' built-in token management (HTTP-only cookies), follow security best practices from architecture document
   - Next step: Security review of JWT token implementation before production deployment

**Assumptions:**
1. **Assumption: PostgreSQL 15+ compatibility** - Assume Render PostgreSQL instance supports all required features (ENUM types, JSON fields)
   - Validation: Test database schema migrations on Render PostgreSQL before Story 1.2 completion

2. **Assumption: React Query caching behavior** - Assume React Query's default caching strategy is sufficient for user profile data
   - Validation: Monitor cache hit rates, adjust cache TTL if needed during Story 1.5 implementation

3. **Assumption: Tailwind CSS configuration** - Assume Tailwind CSS custom color scheme (black background, blue/green accents) meets WCAG contrast requirements
   - Validation: Run WCAG contrast checker during Story 1.7 implementation

4. **Assumption: User tier enforcement logic** - Assume 5-stock limit for free tier is sufficient for MVP validation (per PRD)
   - Validation: Monitor user feedback during Epic 3, adjust limit if needed

**Open Questions:**
1. **Question: Email verification required for MVP?** - PRD states "basic - can be enhanced later" for email verification. Should verification be mandatory for login, or optional?
   - Resolution needed: Clarify with product owner before Story 1.3 implementation
   - Current approach: Implement basic verification flow, allow unverified users to login (can enforce later)

2. **Question: Session timeout duration?** - JWT tokens should expire, but what duration? Architecture mentions 24-hour default, is this acceptable for MVP?
   - Resolution needed: Confirm security requirements (24-hour default seems reasonable for MVP)
   - Current approach: Use FastAPI Users default (24-hour access token with refresh token)

3. **Question: Password complexity requirements?** - Minimum length is specified (8 characters), but what complexity rules? (uppercase, numbers, symbols?)
   - Resolution needed: Define password requirements before Story 1.3 implementation
   - Current approach: Minimum 8 characters, allow basic complexity validation (can enhance later)

4. **Question: User tier upgrade mechanism?** - UI shows upgrade prompts, but how do users actually upgrade? (Manual admin change? Payment integration deferred?)
   - Resolution needed: Clarify tier upgrade process for MVP (likely manual admin change)
   - Current approach: Manual admin update to premium tier, payment integration deferred per PRD

## Test Strategy Summary

**Test Levels:**

1. **Unit Tests (Backend)**
   - Password hashing: Verify bcrypt hashing produces different hashes for same password
   - Email validation: Test email format validation (valid/invalid formats)
   - Tier enforcement logic: Test free tier 5-stock limit calculation, premium unlimited access
   - Database models: Test SQLAlchemy model definitions, enum validations
   - Framework: pytest, pytest-asyncio

2. **Unit Tests (Frontend)**
   - Form validation: Test email/password validation in Register and Login components
   - Auth hook: Test useAuth hook state management (login, logout, token storage)
   - Protected routes: Test route protection logic (redirect to login if unauthenticated)
   - Framework: React Testing Library, Jest

3. **Integration Tests (API)**
   - Registration flow: Test POST /api/v1/auth/register with valid/invalid inputs, duplicate email handling
   - Login flow: Test POST /api/v1/auth/login with valid/invalid credentials, JWT token generation
   - Preferences update: Test PUT /api/v1/users/me/preferences with authentication, enum validation
   - Tier enforcement: Test tier checks in API endpoints (free tier limit, premium access)
   - Framework: pytest with TestClient (FastAPI), verify database state changes

4. **End-to-End Tests (UI)**
   - User registration journey: Navigate to /register, fill form, submit, verify redirect
   - User login journey: Navigate to /login, enter credentials, verify dashboard access
   - Preferences update journey: Navigate to /profile, update preferences, verify persistence
   - Protected route access: Attempt to access /profile without login, verify redirect
   - Framework: Playwright or Cypress (optional for MVP, manual testing acceptable)

**Test Coverage Targets:**
- Backend API endpoints: 80%+ coverage (critical paths: authentication, preferences, tier enforcement)
- Frontend components: 60%+ coverage (critical paths: Login, Register, Profile)
- Database migrations: 100% coverage (verify all tables/columns/indexes created correctly)

**Edge Cases to Test:**
- Registration with existing email (duplicate handling)
- Login with invalid credentials (error message doesn't reveal if email exists)
- Preferences update with invalid enum values (validation)
- Free tier user attempting to track 6th stock (limit enforcement)
- Session expiration (JWT token expiry, refresh logic)
- Network failures during registration/login (error handling, retry logic)
- Database connection failures (graceful degradation)

**Performance Tests:**
- API endpoint response times: Verify <500ms for authentication endpoints (per NFR001)
- Database query performance: Verify indexed queries (email lookup, user preferences) <200ms
- Frontend page load: Verify dashboard loads <3 seconds (includes auth check)

**Security Tests:**
- Password hashing: Verify passwords never stored in plaintext
- JWT token validation: Verify token tampering is rejected
- SQL injection prevention: Verify SQLAlchemy ORM prevents injection attacks
- XSS prevention: Verify React escapes user input properly
- CORS configuration: Verify only allowed origins can access API

