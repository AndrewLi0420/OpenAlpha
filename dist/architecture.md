# Decision Architecture - OpenAlpha

## Executive Summary

OpenAlpha uses a modern full-stack architecture with React/TypeScript frontend on Vercel and FastAPI/Python backend on Render. The architecture supports hourly data processing for Fortune 500 stocks, ML-powered recommendations with confidence scoring, and a freemium tier model. Key patterns include multi-source sentiment aggregation, confidence-scored recommendation generation, and tier-aware filtering to ensure consistent AI agent implementation.

## Project Initialization

First implementation story should execute:

**Frontend Setup:**
```bash
npm create vite@latest openalpha-frontend -- --template react-ts
cd openalpha-frontend
npm install
npm install tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

**Backend Setup:**
```bash
pip install cookiecutter
cookiecutter https://github.com/Tobi-De/cookiecutter-fastapi
# Follow prompts to configure project
cd openalpha-backend
pip install -r requirements.txt
```

This establishes the base architecture with these decisions:
- **Frontend:** React 18+, TypeScript, Vite build tooling, ESLint
- **Backend:** FastAPI framework, Python 3.x, project structure
- **Additional Setup Required:** Tailwind CSS, SQLAlchemy, FastAPI Users, APScheduler

## Decision Summary

| Category | Decision | Version | Affects Epics | Rationale |
| -------- | -------- | ------- | ------------- | --------- |
| Frontend Framework | React + TypeScript | React 18+, TS 5.x | All | Modern, type-safe, excellent ecosystem |
| Build Tool | Vite | Latest | All | Fast HMR, optimal dev experience |
| Backend Framework | FastAPI | Latest | All | Async, fast, Python-native, great docs |
| Database | PostgreSQL | 15+ | All | Relational data, complex queries, migrations |
| ORM | SQLAlchemy | 2.0.x | All | Mature, relationship support, Alembic migrations |
| Authentication | FastAPI Users | Latest | Epic 1 | Async, email verification, session management |
| Background Jobs | APScheduler | 3.x | Epic 2 | Simple, in-process, PostgreSQL persistence |
| Email Service | Resend | Latest | Epic 1 | Good free tier, modern API |
| Search | PostgreSQL FTS | Built-in | Epic 3 | Simple for 500 stocks, no extra service |
| Deployment (Frontend) | Vercel | Latest | All | Excellent for React/Vite, free tier |
| Deployment (Backend) | Render | Latest | All | FastAPI support, PostgreSQL, free tier |
| Styling | Tailwind CSS | 3.x | Epic 1, 3, 4 | Utility-first, responsive, black/blue/green theme |
| State Management | React Query | 5.x | Epic 3, 4 | Server state, caching, optimistic updates |
| HTTP Client | Axios | Latest | Epic 3, 4 | Reliable, interceptors, error handling |
| Chart Library | Recharts or Chart.js | Latest | Epic 4 | React-friendly, time series support |

## Project Structure

```
openalpha/
├── frontend/                    # Vite + React + TypeScript
│   ├── public/
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   │   ├── dashboard/
│   │   │   ├── recommendations/
│   │   │   ├── charts/
│   │   │   └── common/
│   │   ├── pages/               # Route pages
│   │   │   ├── Dashboard.tsx
│   │   │   ├── RecommendationDetail.tsx
│   │   │   ├── Historical.tsx
│   │   │   ├── Search.tsx
│   │   │   ├── Profile.tsx
│   │   │   ├── Login.tsx
│   │   │   └── Register.tsx
│   │   ├── hooks/               # Custom React hooks
│   │   │   ├── useAuth.ts
│   │   │   ├── useRecommendations.ts
│   │   │   └── useStockSearch.ts
│   │   ├── services/            # API client
│   │   │   ├── api.ts           # Axios/fetch wrapper
│   │   │   ├── auth.ts
│   │   │   ├── recommendations.ts
│   │   │   └── stocks.ts
│   │   ├── store/               # State management (React Query)
│   │   │   └── queryClient.ts
│   │   ├── types/               # TypeScript types
│   │   │   ├── user.ts
│   │   │   ├── stock.ts
│   │   │   └── recommendation.ts
│   │   ├── utils/               # Utility functions
│   │   │   ├── date.ts
│   │   │   └── format.ts
│   │   ├── App.tsx
│   │   ├── main.tsx
│   │   └── vite-env.d.ts
│   ├── .env.local
│   ├── .env.production
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── README.md
│
├── backend/                     # FastAPI (cookiecutter structure)
│   ├── app/
│   │   ├── api/                 # API routes
│   │   │   ├── v1/
│   │   │   │   ├── endpoints/
│   │   │   │   │   ├── auth.py
│   │   │   │   │   ├── users.py
│   │   │   │   │   ├── recommendations.py
│   │   │   │   │   ├── stocks.py
│   │   │   │   │   └── search.py
│   │   │   │   └── __init__.py
│   │   │   └── deps.py          # Dependencies (auth, DB)
│   │   ├── core/                # Core configuration
│   │   │   ├── config.py        # Settings (Pydantic)
│   │   │   ├── security.py     # Password hashing, JWT
│   │   │   └── logging.py       # Logging setup
│   │   ├── crud/                # Database operations
│   │   │   ├── users.py
│   │   │   ├── stocks.py
│   │   │   ├── recommendations.py
│   │   │   ├── market_data.py
│   │   │   └── sentiment_data.py
│   │   ├── db/                  # Database setup
│   │   │   ├── base.py          # SQLAlchemy Base
│   │   │   ├── session.py       # Database session
│   │   │   └── init_db.py       # Initialization
│   │   ├── models/              # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── stock.py
│   │   │   ├── recommendation.py
│   │   │   ├── market_data.py
│   │   │   └── sentiment_data.py
│   │   ├── schemas/             # Pydantic schemas
│   │   │   ├── user.py
│   │   │   ├── stock.py
│   │   │   ├── recommendation.py
│   │   │   └── common.py
│   │   ├── services/            # Business logic
│   │   │   ├── ml_service.py    # ML model inference
│   │   │   ├── sentiment_service.py
│   │   │   ├── recommendation_service.py
│   │   │   └── data_collection.py
│   │   ├── tasks/               # Background jobs (APScheduler)
│   │   │   ├── market_data.py  # Hourly market data collection
│   │   │   ├── sentiment.py   # Hourly sentiment collection
│   │   │   └── recommendations.py  # Daily recommendation generation
│   │   ├── utils/               # Utility functions
│   │   │   ├── date_utils.py
│   │   │   └── errors.py
│   │   ├── main.py              # FastAPI app
│   │   └── __init__.py
│   ├── alembic/                 # Database migrations
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   ├── tests/                   # Pytest tests
│   │   ├── api/
│   │   ├── crud/
│   │   ├── services/
│   │   └── conftest.py
│   ├── .env
│   ├── .env.example
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   ├── README.md
│   └── start.sh                 # Render start script
│
├── ml-models/                   # ML model artifacts (optional)
│   ├── neural_network/
│   ├── random_forest/
│   └── README.md
│
├── docker-compose.yml           # Local development (PostgreSQL + Redis)
├── .gitignore
├── README.md
└── docs/                        # Documentation
    ├── api/
    ├── deployment/
    └── development.md
```

## Epic to Architecture Mapping

**Epic 1: Foundation & User Authentication**
- **Backend:** `backend/app/models/user.py`, `backend/app/api/v1/endpoints/auth.py`, `backend/app/api/v1/endpoints/users.py`
- **Frontend:** `frontend/src/pages/Login.tsx`, `frontend/src/pages/Register.tsx`, `frontend/src/pages/Profile.tsx`
- **Database:** `users`, `user_preferences` tables
- **Key Technologies:** FastAPI Users, SQLAlchemy, JWT authentication

**Epic 2: Data Pipeline & ML Engine**
- **Backend:** `backend/app/services/ml_service.py`, `backend/app/tasks/`, `backend/app/models/` (market_data, sentiment_data, stock)
- **Database:** `stocks`, `market_data`, `sentiment_data`, `recommendations` tables
- **Integration:** APScheduler runs hourly tasks
- **Key Technologies:** APScheduler, SQLAlchemy, ML models (PyTorch/TensorFlow + scikit-learn)

**Epic 3: Recommendations & Dashboard**
- **Backend:** `backend/app/api/v1/endpoints/recommendations.py`, `backend/app/api/v1/endpoints/search.py`
- **Frontend:** `frontend/src/pages/Dashboard.tsx`, `frontend/src/pages/RecommendationDetail.tsx`, `frontend/src/pages/Search.tsx`
- **Components:** `frontend/src/components/recommendations/`, `frontend/src/components/charts/`
- **Key Technologies:** React Query, Axios, PostgreSQL FTS

**Epic 4: Historical Data & Visualization**
- **Backend:** `backend/app/api/v1/endpoints/recommendations.py` (historical endpoint)
- **Frontend:** `frontend/src/pages/Historical.tsx`, `frontend/src/components/charts/`
- **Database:** Historical queries from `recommendations`, `market_data` tables
- **Key Technologies:** Recharts/Chart.js, React Query

## Technology Stack Details

### Core Technologies

**Frontend Stack:**
- React 18+ with TypeScript
- Vite (build tool, HMR)
- Tailwind CSS 3.x (styling)
- React Query 5.x (server state management)
- Axios (HTTP client)
- React Router (routing)
- Recharts or Chart.js (data visualization)

**Backend Stack:**
- FastAPI (async web framework)
- Python 3.11+
- SQLAlchemy 2.0.x (ORM)
- Alembic (database migrations)
- FastAPI Users (authentication)
- APScheduler 3.x (background jobs)
- Pydantic (data validation)
- Resend (email service)

**Database & Infrastructure:**
- PostgreSQL 15+ (primary database)
- Redis (optional, for caching/sessions if needed)

### Integration Points

1. **Frontend ↔ Backend:** REST API via Axios, base URL from `VITE_API_URL` environment variable
2. **Backend ↔ Database:** SQLAlchemy ORM with async support
3. **Tasks ↔ Services:** APScheduler triggers background jobs calling service functions
4. **ML Service ↔ Models:** Loads model artifacts from `ml-models/` directory
5. **External APIs:** Twitter API, financial data APIs (Alpha Vantage/Yahoo Finance), web scraping sources

## Novel Pattern Designs

### Pattern 1: Multi-Source Sentiment Aggregation with Transparency

**Purpose:** Aggregate sentiment from multiple sources (Twitter API, web scraping) into unified scores while maintaining source attribution and freshness tracking.

**Components:**
- **Sentiment Collection Service** (`backend/app/services/sentiment_service.py`)
  - Individual collectors for each source (Twitter, news sites)
  - Rate limiting per source
  - Error handling and retry logic
  - Source attribution storage

- **Sentiment Aggregator**
  - Weighted combination of multiple sources
  - Timestamp tracking per source
  - Missing source handling (partial data OK)

**Data Flow:**
```
Twitter API → Sentiment Score + Timestamp
Web Scraping → Sentiment Score + Timestamp
    ↓
Aggregator (weighted average or majority)
    ↓
Unified Sentiment Score (with source metadata)
    ↓
Displayed with transparency: "Sentiment from Twitter (updated 5 min ago), News sources (updated 10 min ago)"
```

**Implementation Guide:**
- Each source collector should be independent and fail gracefully
- Aggregator should handle missing sources (don't fail entire pipeline)
- Frontend should display source attribution and freshness
- Store raw source data for audit/debugging

**Affects Epics:** Epic 2 (Data Pipeline), Epic 3 (Dashboard transparency)

### Pattern 2: Confidence-Scored Recommendation Generation with Explanation Synthesis

**Purpose:** Generate recommendations that combine ML predictions, sentiment scores, risk assessment, and user preferences, with explanations that reference all data sources transparently.

**Components:**
1. **Recommendation Generator** (`backend/app/services/recommendation_service.py`)
   - Inputs: ML prediction, sentiment, risk, user preferences
   - Logic: Filters by holding period, prioritizes by confidence
   - Output: Ranked recommendations with all metadata

2. **Explanation Synthesizer**
   - Combines multiple signals into readable explanations
   - References specific data sources with timestamps
   - Educational tone, avoids jargon

**Data Flow:**
```
ML Model → Prediction Signal + Confidence Score (R²)
Sentiment Data → Aggregated Sentiment Score
Risk Calculator → Risk Level (Low/Medium/High)
User Preferences → Holding Period Filter
    ↓
Recommendation Generator (combines + filters)
    ↓
Explanation Synthesizer (creates human-readable explanation)
    ↓
Final Recommendation: {stock, signal, confidence, sentiment, risk, explanation}
```

**Example Explanation Pattern:**
> "Positive sentiment trending on Twitter (updated 5 min ago), ML model indicates strong buy signal with 0.85 R² confidence. Medium risk due to recent volatility. Data sources: Twitter API, Alpha Vantage market data, neural network model v1.2"

**Implementation Guide:**
- Explanation template with placeholders for dynamic values
- Always reference data sources and freshness
- Keep explanations to 2-3 sentences
- Store full explanation in database (don't regenerate on every request)

**Affects Epics:** Epic 2 (ML Engine), Epic 3 (Dashboard)

### Pattern 3: Tier-Aware Recommendation Pre-Filtering

**Purpose:** Filter recommendations at generation/retrieval time based on user's tier and tracked stocks (free tier limited to 5 stocks).

**Components:**
1. **User Stock Tracking** (`backend/app/models/user_stock_tracking.py`)
   - Tracks which stocks user is following
   - Enforced limit: 5 for free tier, unlimited for premium

2. **Recommendation Filter**
   - Before returning recommendations, filter to user's tracked stocks only
   - If user has < 5 tracked stocks, show recommendations only for those
   - Premium users see all recommendations

**Data Flow:**
```
Global Recommendations (generated for all Fortune 500)
    ↓
User Tier Check (free/premium)
    ↓
If Free: Filter by user_stock_tracking table (max 5 stocks)
If Premium: Return all recommendations
    ↓
Filtered Recommendations
```

**Implementation Guide:**
- Filter at API endpoint level (`backend/app/api/v1/endpoints/recommendations.py`)
- Use SQL JOIN to filter efficiently
- Return clear messaging: "Tracking 3/5 stocks (Free tier)"
- UI should prevent adding more stocks when limit reached

**Affects Epics:** Epic 1 (Freemium Tier), Epic 3 (Dashboard)

### Pattern 4: Hourly Batch Processing with Graceful Degradation

**Purpose:** Process 500 stocks hourly (market data + sentiment) within time constraints, handling API rate limits, failures, and partial completion gracefully.

**Components:**
1. **Batch Processor** (`backend/app/tasks/market_data.py`, `backend/app/tasks/sentiment.py`)
   - Processes stocks in batches (e.g., 50 at a time)
   - Respects rate limits per API
   - Retry logic with exponential backoff

2. **Progress Tracking**
   - Track which stocks were processed successfully
   - Log failures without stopping entire batch
   - Partial success is acceptable (e.g., 450/500 stocks updated)

3. **Scheduler Configuration**
   - APScheduler triggers hourly
   - Overlap handling (if previous run still running)
   - Error recovery (retry failed stocks next cycle)

**Data Flow:**
```
APScheduler (hourly trigger)
    ↓
Batch Processor (500 stocks → batches of 50)
    ↓
For each batch:
  - Collect market data (with rate limiting)
  - Collect sentiment (with rate limiting)
  - Store successes, log failures
    ↓
Report: "Processed 487/500 stocks successfully"
Failed stocks retry on next cycle
```

**Implementation Guide:**
- Use async/await for concurrent processing within rate limits
- Store processing status per stock (last_updated, success/failure)
- Don't fail entire pipeline if some stocks fail
- Log aggregate metrics for monitoring

**Affects Epics:** Epic 2 (Data Pipeline)

## Implementation Patterns

These patterns ensure consistent implementation across all AI agents:

### 1. Naming Patterns

**Backend (Python/FastAPI):**
- **API Routes:** Plural nouns, lowercase with hyphens (`/api/v1/recommendations`, `/api/v1/stocks`)
- **Path Parameters:** `{id}` format (`/api/v1/stocks/{stock_id}`)
- **Database Tables:** Plural, lowercase with underscores (`users`, `stocks`, `market_data`)
- **Table Columns:** Lowercase with underscores (`created_at`, `user_id`)
- **Python Files:** `snake_case.py` (`recommendation_service.py`)
- **Python Functions:** `snake_case` (`get_recommendations`, `create_user`)
- **Python Classes:** `PascalCase` (`RecommendationService`, `StockModel`)

**Frontend (TypeScript/React):**
- **React Components:** `PascalCase.tsx` (`RecommendationCard.tsx`)
- **Component Files:** `frontend/src/components/{category}/{ComponentName}.tsx`
- **TypeScript Types:** `PascalCase` (`Recommendation`, `Stock`)
- **Hooks:** `use` prefix, `PascalCase` (`useAuth.ts`, `useRecommendations.ts`)
- **API Service Functions:** `camelCase` (`getRecommendations`, `createUser`)

### 2. Structure Patterns

**Backend:**
- **Test Files:** `backend/tests/test_{module_name}.py` (all tests in `tests/` directory)
- **Organization:** By feature/domain (not by type)
- **Shared Utilities:** `backend/app/utils/`

**Frontend:**
- **Test Files:** Co-located `{ComponentName}.test.tsx`
- **Organization:** By feature/page, then by type within feature
- **Shared Utilities:** `frontend/src/utils/`

### 3. Format Patterns

**API Response Format:**
- **Success:** Direct data object (no wrapper)
- **List:** Array of objects (no wrapper)
- **Pagination:** `{ "data": [...], "page": 1, "total": 100 }`
- **Error:** `{ "error": { "type": "ValidationError", "message": "...", "detail": "..." } }`

**Date Format:**
- **API:** ISO 8601 strings (`"2024-10-30T14:30:00Z"`)
- **Database:** UTC timestamps
- **Frontend Display:** Convert to user's local timezone

**Status Codes:**
- `200` - Success, `201` - Created
- `400` - Bad Request, `401` - Unauthorized, `403` - Forbidden, `404` - Not Found, `500` - Internal Error

### 4. Communication Patterns

**Frontend ↔ Backend:**
- **HTTP Client:** Axios (configured in `frontend/src/services/api.ts`)
- **Base URL:** Environment variable `VITE_API_URL`
- **Headers:** `Authorization: Bearer {token}` for authenticated requests

**Background Jobs (APScheduler):**
- **Job Naming:** `{action}_{resource}` (`collect_market_data`, `aggregate_sentiment`)
- **Location:** `backend/app/tasks/{resource}.py`

### 5. Lifecycle Patterns

**Loading States:**
- Frontend: React Query `isLoading` pattern
- Backend: Log all async operations

**Error Recovery:**
- Frontend: React Query handles retries (3 retries, exponential backoff)
- Backend: Retry logic in services (3 retries, exponential backoff), graceful degradation

### 6. Location Patterns

**API Route Structure:** `/api/v1/{resource}/{id?}`

**Examples:**
- `GET /api/v1/recommendations` - List recommendations
- `GET /api/v1/recommendations/{id}` - Get single recommendation
- `GET /api/v1/stocks` - List stocks
- `GET /api/v1/stocks/{symbol}` - Get stock by symbol
- `POST /api/v1/auth/register` - Register user
- `POST /api/v1/auth/login` - Login

### 7. Consistency Patterns

**Date Formatting:**
- Backend Storage: UTC, ISO 8601 strings in API
- Frontend Display: Convert UTC to user's local timezone, format: "Oct 30, 2024, 2:30 PM"

**Logging Format:**
- Backend: Structured JSON logs for Render log aggregation
- Example: `logger.info("Market data collected", extra={"stock_id": stock_id, "price": price})`

**User-Facing Errors:**
- Simple, actionable messages
- Bad: "Database constraint violation: users_email_key"
- Good: "An account with this email already exists. Please log in or use a different email."

## Consistency Rules

### Naming Conventions

See Implementation Patterns section above for detailed naming rules. All agents must follow these exactly.

### Code Organization

**Backend:**
- Organize by feature/domain, not by type
- Structure: `api/endpoints/`, `crud/`, `models/`, `schemas/`, `services/`, `tasks/`

**Frontend:**
- Organize by feature/page, then by type within feature
- Structure: `components/{feature}/`, `pages/`, `hooks/`, `services/`, `types/`

### Error Handling

**Backend:**
- Use FastAPI `HTTPException` with consistent format
- Structured error responses: `{ "error": { "type": "...", "message": "...", "detail": "..." } }`
- Standard HTTP status codes

**Frontend:**
- Axios interceptor in `api.ts` handles 401/403 globally
- React Query handles retries automatically
- User-facing error messages from API `error.message`

### Logging Strategy

**Backend:**
- Python `logging` with structured JSON logs
- Levels: DEBUG (dev), INFO (production), ERROR (production)
- Log API requests, errors, scheduled job execution, ML inference results
- Format: Structured JSON for Render log aggregation

**Frontend:**
- Console logging for development
- Error service for production (if needed)

## Data Architecture

### Database Schema Overview

**Core Tables:**
- `users` - User accounts (via FastAPI Users, extended with preferences)
- `user_preferences` - Holding period, risk tolerance
- `stocks` - Fortune 500 stock metadata (symbol, name, sector, rank)
- `market_data` - Hourly price/volume data with timestamps
- `sentiment_data` - Sentiment scores with source attribution and timestamps
- `recommendations` - Generated recommendations with confidence scores, risk levels, explanations
- `user_stock_tracking` - Tracks which stocks user follows (enforces 5-stock limit for free tier)

### Key Relationships

- `users` → `user_preferences` (1:1)
- `users` → `user_stock_tracking` (1:many, max 5 for free tier)
- `users` → `recommendations` (1:many, filtered by preferences)
- `stocks` → `market_data` (1:many, hourly data points)
- `stocks` → `sentiment_data` (1:many, hourly sentiment scores)
- `stocks` → `recommendations` (1:many)
- `recommendations` → `users` (many:many via user preferences filtering)

### Indexing Strategy

- Foreign keys indexed automatically
- `stocks.symbol` - unique index for lookups
- `market_data.timestamp` - indexed for time-series queries
- `sentiment_data.timestamp` - indexed for time-series queries
- `recommendations.created_at` - indexed for sorting/filtering
- `user_stock_tracking.user_id` - indexed for filtering recommendations

## API Contracts

### Authentication Endpoints

**POST /api/v1/auth/register**
- Request: `{ "email": "user@example.com", "password": "securepass" }`
- Response: `{ "id": 1, "email": "user@example.com", "is_verified": false }`

**POST /api/v1/auth/login**
- Request: `{ "email": "user@example.com", "password": "securepass" }`
- Response: `{ "access_token": "...", "token_type": "bearer" }`

### Recommendations Endpoints

**GET /api/v1/recommendations**
- Query Params: `?holding_period=daily&risk_level=low&confidence_min=0.7`
- Response: `[{ "id": 1, "stock": {...}, "signal": "buy", "confidence": 0.85, "sentiment": 0.7, "risk": "medium", "explanation": "..." }]`
- Filtered by user tier (free: 5 stocks max, premium: all)

**GET /api/v1/recommendations/{id}**
- Response: Full recommendation object with historical context

**GET /api/v1/recommendations/historical**
- Query Params: `?start_date=2024-10-01&end_date=2024-10-30&stock_symbol=AAPL`
- Response: Array of historical recommendations with outcomes

### Stock Endpoints

**GET /api/v1/stocks**
- Response: `[{ "symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology", "fortune_500_rank": 3 }]`

**GET /api/v1/stocks/{symbol}**
- Response: Full stock object with current market data and sentiment

**GET /api/v1/stocks/search?q=apple**
- Response: Array of matching stocks (PostgreSQL FTS)

### User Endpoints

**GET /api/v1/users/me**
- Response: Current user with preferences and tier status

**PUT /api/v1/users/me/preferences**
- Request: `{ "holding_period": "daily", "risk_tolerance": "medium" }`
- Response: Updated preferences

## Security Architecture

### Authentication & Authorization

- **Method:** JWT tokens via FastAPI Users
- **Storage:** HTTP-only cookies (more secure than localStorage)
- **Token Refresh:** Handled by FastAPI Users
- **Password Hashing:** bcrypt (via FastAPI Users)

### API Security

- **CORS:** Configured for Vercel frontend domain + localhost for dev
- **HTTPS:** Required in production (Vercel and Render provide)
- **Rate Limiting:** Per endpoint (defer to later if needed)
- **Input Validation:** Pydantic schemas validate all inputs

### Data Protection

- **User Data:** Encrypted at rest (PostgreSQL), transmitted over HTTPS
- **Sensitive Data:** No credit card/PII storage (freemium model, no payments in MVP)
- **API Keys:** Stored in environment variables, never committed

### Tier Enforcement

- **Free Tier:** 5 stock limit enforced at API level
- **Premium Tier:** Unlimited access
- **Enforcement:** SQL-level filtering in recommendation endpoints

## Performance Considerations

### API Performance

- **Target:** <500ms for data retrieval endpoints
- **Optimization:** Database indexes on foreign keys and timestamps
- **Caching:** React Query caches API responses (frontend)
- **Database Queries:** Use SQLAlchemy eager loading for relationships

### Background Jobs

- **Hourly Processing:** Process 500 stocks in batches (50 at a time)
- **Rate Limiting:** Respect external API limits (Twitter, financial data APIs)
- **Graceful Degradation:** Partial success acceptable (e.g., 450/500 stocks updated)
- **Monitoring:** Log processing metrics (success rate, duration)

### ML Inference

- **Target:** <1 minute per stock prediction
- **Optimization:** Batch inference where possible
- **Model Caching:** Load models once at startup, reuse for inference
- **Async Processing:** Use FastAPI async for non-blocking inference

### Frontend Performance

- **Target:** Dashboard loads within 3 seconds
- **Optimization:** Code splitting, lazy loading routes
- **Caching:** React Query handles caching and refetching
- **Image Optimization:** Use Vite asset handling

## Deployment Architecture

### Frontend (Vercel)

- **Platform:** Vercel
- **Build Command:** `npm run build`
- **Output Directory:** `dist`
- **Environment Variables:** `VITE_API_URL` (points to Render backend)
- **Free Tier:** Sufficient for MVP, scales automatically

### Backend (Render)

- **Platform:** Render
- **Runtime:** Python 3.11+
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Database:** Render PostgreSQL (free tier)
- **Environment Variables:** `DATABASE_URL`, `SECRET_KEY`, `RESEND_API_KEY`, etc.
- **Free Tier:** Limited hours, sufficient for MVP validation

### Database

- **Platform:** Render PostgreSQL (managed)
- **Backup:** Automatic backups (Render managed)
- **Connection:** Internal URL for backend, no external access

### Background Jobs

- **Execution:** APScheduler runs within FastAPI process
- **Scheduling:** Hourly triggers for data collection
- **Monitoring:** Logs visible in Render dashboard
- **Scaling:** Single instance for MVP, can scale horizontally later if needed

## Development Environment

### Prerequisites

- **Node.js:** 18+ (for frontend)
- **Python:** 3.11+ (for backend)
- **PostgreSQL:** 15+ (local development via Docker Compose)
- **Git:** Latest version
- **Docker & Docker Compose:** For local database (optional)

### Setup Commands

**Initial Setup:**
```bash
# Frontend
npm create vite@latest openalpha-frontend -- --template react-ts
cd openalpha-frontend
npm install
npm install tailwindcss postcss autoprefixer react-router-dom axios @tanstack/react-query recharts
npx tailwindcss init -p

# Backend
pip install cookiecutter
cookiecutter https://github.com/Tobi-De/cookiecutter-fastapi
cd openalpha-backend
pip install -r requirements.txt
pip install fastapi-users[sqlalchemy] apscheduler[sqlalchemy] resend psycopg2-binary alembic

# Database Setup (local)
docker-compose up -d  # Starts PostgreSQL and Redis
alembic upgrade head  # Run migrations
```

**Development:**
```bash
# Frontend (terminal 1)
cd frontend
npm run dev

# Backend (terminal 2)
cd backend
uvicorn app.main:app --reload

# Background jobs run automatically via APScheduler
```

**Environment Variables:**
- Frontend `.env.local`: `VITE_API_URL=http://localhost:8000`
- Backend `.env`: `DATABASE_URL=postgresql://...`, `SECRET_KEY=...`, etc.

## Architecture Decision Records (ADRs)

### ADR-001: Separate Frontend and Backend

**Decision:** Use separate Vite frontend and FastAPI backend (not full-stack framework)

**Context:** OpenAlpha needs React for rich UI, FastAPI for ML/data processing. Separate deployments allow independent scaling.

**Consequences:**
- Need to configure CORS
- Separate deployment pipelines (Vercel + Render)
- API contract must be well-defined (this document)

### ADR-002: PostgreSQL for Primary Database

**Decision:** Use PostgreSQL instead of NoSQL database

**Context:** Relational data (users, stocks, recommendations with foreign keys), need for complex queries, ACID transactions for financial data.

**Consequences:**
- Need SQLAlchemy ORM
- Need Alembic for migrations
- Excellent for relational queries, may need optimization for time-series (can use TimescaleDB later if needed)

### ADR-003: APScheduler for Background Jobs

**Decision:** Use APScheduler instead of Celery for background jobs

**Context:** MVP needs simple hourly tasks, single instance deployment initially, minimize infrastructure complexity.

**Consequences:**
- Simpler setup (no Redis broker needed initially)
- In-process scheduling (single instance limitation)
- Can migrate to Celery later if distributed processing needed

### ADR-004: Free-Tier Infrastructure for MVP

**Decision:** Deploy on Vercel (frontend) + Render (backend) free tiers

**Context:** Validate product-market fit before investing in infrastructure, MVP needs cost-effective deployment.

**Consequences:**
- May hit rate limits or resource constraints
- Need to monitor usage
- Can scale to paid tiers when needed

### ADR-005: PostgreSQL FTS for Search

**Decision:** Use PostgreSQL full-text search instead of Algolia/Elasticsearch

**Context:** Only 500 stocks (Fortune 500), simple search requirements (symbol/name), minimize external dependencies.

**Consequences:**
- Simpler architecture (no external service)
- Good enough for 500 stocks
- Can upgrade to Algolia later if search requirements grow

### ADR-006: Defer Twitter Sentiment Collection to v2

**Decision:** Skip Twitter API sentiment collection in MVP, focus on free web scraping sources (Story 2.4) instead

**Context:** Twitter API Basic tier costs $200/month (as of 2024), which is cost-prohibitive for MVP validation. For MVP/prototype phase, prioritize free sentiment sources via web scraping (financial news sites, forums) to validate product-market fit before investing in paid API access.

**Consequences:**
- Story 2.3 (Twitter Sentiment Collection) deferred to v2
- Story 2.4 (Web Scraping Sentiment) becomes primary sentiment source for MVP
- Can add Twitter API integration later when product-market fit validated and budget allows
- Reduces MVP costs and complexity
- Web scraping sources provide good initial sentiment data quality

**Migration Path:**
- Implement Story 2.4 first as primary sentiment source
- Add Twitter API sentiment collection in v2 when ready (can reuse sentiment_service.py structure)
- Multi-source aggregation pattern already designed to handle Twitter + web scraping

---

_Generated by BMAD Decision Architecture Workflow v1.3.2_  
_Date: 2025-10-30_  
_For: Andrew_

