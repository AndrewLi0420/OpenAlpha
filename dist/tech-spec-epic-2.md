# Epic Technical Specification: Data Pipeline & ML Engine

Date: 2025-01-31
Author: Andrew
Epic ID: 2
Status: Draft

---

## Overview

Epic 2 builds the data collection infrastructure and ML prediction engine that powers OpenAlpha's recommendations, as outlined in the PRD (FR005-FR014, FR023-FR025). This epic establishes hourly (or 5-minute if cost-effective) data processing pipelines for market data and sentiment analysis from multiple sources, trains and deploys ML models (neural networks and Random Forest), and generates predictions with confidence scores based on R² analysis. Per the PRD goals, this epic delivers the core intelligence engine that transforms raw data into actionable recommendations with statistical backing, enabling users to make informed trading decisions rather than emotional trades.

**MVP Scope Adjustment:** Story 2.3 (Twitter Sentiment Collection) is deferred to v2 due to Twitter API costs ($200/month). Story 2.4 (Web Scraping Sentiment) becomes the primary sentiment source for MVP. See ADR-006 in architecture.md for full rationale.

The epic delivers seven stories for MVP (eight including deferred Story 2.3) covering Fortune 500 stock data setup, market data collection, sentiment collection from web scraping sources, ML model training infrastructure, inference service, risk assessment, and recommendation generation. This epic builds on Epic 1 (Foundation & User Authentication) foundation and serves as the prerequisite for Epic 3 (Recommendations & Dashboard) which displays these recommendations to users.

## Objectives and Scope

**In-Scope:**
- Fortune 500 stock list loaded into database with metadata (symbol, company_name, sector, fortune_500_rank)
- Market data collection pipeline using free financial APIs (Alpha Vantage, Yahoo Finance, or similar)
- Hourly (or configurable interval) scheduled jobs for market data and sentiment collection
- Twitter API integration for sentiment collection with rate limiting and error handling
- Additional sentiment sources via web scraping (news sites, financial forums) with ethical practices
- Multi-source sentiment aggregation with source attribution and freshness tracking
- ML model training infrastructure with PyTorch/TensorFlow and scikit-learn
- Neural network and Random Forest model architectures for stock predictions
- ML model inference service generating buy/sell/hold signals with confidence scores
- Confidence score calculation based on R² analysis of model performance
- Risk assessment calculation (low/medium/high) based on volatility, ML uncertainty, market conditions
- Recommendation generation algorithm combining ML predictions, sentiment, risk scores, and user preferences
- Batch processing for 500 stocks with graceful degradation (partial success acceptable)
- Model performance tracking (R² metrics, accuracy) and logging
- Historical data storage for market data, sentiment, and recommendations

**Out-of-Scope:**
- User-facing dashboard and recommendation display (deferred to Epic 3)
- Payment integration or premium tier enforcement logic (established in Epic 1)
- Advanced ML model features (hyperparameter tuning, model selection algorithms beyond basic architectures)
- Real-time streaming data processing (hourly batch processing only)
- Portfolio tracking or transaction management
- Social features or user communities
- Mobile app development (web-first only)

## System Architecture Alignment

This epic aligns with the architecture document's data pipeline and ML engine decisions: FastAPI backend on Render with APScheduler 3.x for background jobs, PostgreSQL 15+ database for time-series data storage, and ML models (PyTorch/TensorFlow + scikit-learn) for predictions. The implementation follows the project structure patterns defined in architecture.md with `backend/app/services/ml_service.py`, `backend/app/tasks/market_data.py`, `backend/app/tasks/sentiment.py`, and `backend/app/models/` (market_data, sentiment_data, stock) organizational patterns.

Key architecture patterns applied: Multi-Source Sentiment Aggregation with Transparency (Pattern 1) for combining Twitter and web scraping sentiment while maintaining source attribution, Confidence-Scored Recommendation Generation with Explanation Synthesis (Pattern 2) for generating recommendations with transparent explanations, and Hourly Batch Processing with Graceful Degradation (Pattern 4) for processing 500 stocks hourly within time constraints. The database schema implements the `stocks`, `market_data`, `sentiment_data`, and `recommendations` tables as specified in the Data Architecture section, with proper indexing for time-series queries (`market_data.timestamp`, `sentiment_data.timestamp`) and foreign key relationships.

## Detailed Design

### Services and Modules

| Service/Module | Responsibility | Inputs | Outputs | Owner/Component |
|---------------|---------------|--------|---------|-----------------|
| **Stock Import Service** | Imports Fortune 500 stock list from CSV/data source into database | CSV file or API data | Stock records in `stocks` table | `backend/app/services/stock_import_service.py` or `backend/app/scripts/import_stocks.py` |
| **Market Data Collection Service** | Collects hourly market data (price, volume) from free financial APIs | Stock symbols, API credentials | Market data records in `market_data` table | `backend/app/services/data_collection.py` |
| **Market Data Task** | APScheduler job that triggers hourly market data collection for all 500 stocks | Scheduled trigger | Updated market_data records | `backend/app/tasks/market_data.py` |
| **Twitter Sentiment Collector** | Collects sentiment data from Twitter API for Fortune 500 stocks (DEFERRED TO V2) | Stock symbols/company names, Twitter API credentials | Sentiment scores in `sentiment_data` table | `backend/app/services/sentiment_service.py` (Twitter collector) |
| **Web Scraping Sentiment Collector** | Collects sentiment from news sites and financial forums via scraping | Stock symbols, target URLs | Sentiment scores in `sentiment_data` table | `backend/app/services/sentiment_service.py` (web scraping collector) |
| **Sentiment Aggregation Service** | Aggregates sentiment from multiple web scraping sources (MVP: web scraping only; v2: will add Twitter) into unified scores | Sentiment scores from multiple sources | Unified sentiment score with source attribution | `backend/app/services/sentiment_service.py` (aggregator) |
| **Sentiment Collection Task** | APScheduler job that triggers hourly sentiment collection | Scheduled trigger | Updated sentiment_data records | `backend/app/tasks/sentiment.py` |
| **ML Model Training Service** | Trains neural network and Random Forest models on historical data | Historical market data, sentiment data | Trained model artifacts | `backend/app/services/ml_service.py` (training functions) |
| **ML Model Inference Service** | Generates predictions (buy/sell/hold) with confidence scores using trained models | Current market data, sentiment scores for a stock | Prediction signal, confidence score | `backend/app/services/ml_service.py` (inference functions) |
| **Risk Assessment Service** | Calculates risk indicators (low/medium/high) for recommendations | Market volatility, ML model uncertainty, market conditions | Risk level (Low/Medium/High) | `backend/app/services/recommendation_service.py` (risk calculation) |
| **Recommendation Generation Service** | Generates recommendations by combining ML predictions, sentiment, risk, and user preferences | ML predictions, sentiment scores, risk levels, user preferences | Ranked recommendations with explanations | `backend/app/services/recommendation_service.py` (generator) |
| **Recommendation Generation Task** | APScheduler job that generates ~10 daily recommendations | Scheduled trigger (hourly or 5-minute) | New recommendation records in `recommendations` table | `backend/app/tasks/recommendations.py` |

### Data Models and Contracts

**Database Schema (PostgreSQL via SQLAlchemy):**

**Stocks Table** (`stocks`) - Populated in Story 2.1
- `id`: UUID (primary key)
- `symbol`: VARCHAR(10), unique, indexed
- `company_name`: VARCHAR(255)
- `sector`: VARCHAR(100)
- `fortune_500_rank`: INTEGER
- `created_at`: TIMESTAMP, default now()
- `updated_at`: TIMESTAMP, default now(), on update now()

**Market Data Table** (`market_data`) - Populated in Story 2.2
- `id`: UUID (primary key)
- `stock_id`: UUID (foreign key → stocks.id), indexed
- `price`: DECIMAL(10, 2)
- `volume`: BIGINT
- `timestamp`: TIMESTAMP, indexed (for time-series queries)
- `created_at`: TIMESTAMP, default now()

**Sentiment Data Table** (`sentiment_data`) - Populated in Stories 2.3-2.4
- `id`: UUID (primary key)
- `stock_id`: UUID (foreign key → stocks.id), indexed
- `sentiment_score`: DECIMAL(3, 2) (normalized -1.0 to 1.0)
- `source`: VARCHAR(50) (e.g., "twitter", "news_site_1", "news_site_2")
- `timestamp`: TIMESTAMP, indexed (for time-series queries)
- `created_at`: TIMESTAMP, default now()

**Recommendations Table** (`recommendations`) - Populated in Story 2.8
- `id`: UUID (primary key)
- `stock_id`: UUID (foreign key → stocks.id), indexed
- `signal`: ENUM('buy', 'sell', 'hold')
- `confidence_score`: DECIMAL(3, 2) (0.0 to 1.0, based on R²)
- `sentiment_score`: DECIMAL(3, 2) (aggregated sentiment)
- `risk_level`: ENUM('low', 'medium', 'high')
- `explanation`: TEXT (human-readable explanation)
- `created_at`: TIMESTAMP, indexed (for sorting/filtering)
- `updated_at`: TIMESTAMP, default now(), on update now()

**TypeScript Types (Frontend - for Epic 3):**

```typescript
interface Stock {
  id: string;
  symbol: string;
  company_name: string;
  sector: string;
  fortune_500_rank: number;
}

interface MarketData {
  id: string;
  stock_id: string;
  price: number;
  volume: number;
  timestamp: string;
}

interface SentimentData {
  id: string;
  stock_id: string;
  sentiment_score: number; // -1.0 to 1.0
  source: string;
  timestamp: string;
}

interface Recommendation {
  id: string;
  stock: Stock;
  signal: 'buy' | 'sell' | 'hold';
  confidence_score: number; // 0.0 to 1.0
  sentiment_score: number;
  risk_level: 'low' | 'medium' | 'high';
  explanation: string;
  created_at: string;
}
```

### APIs and Interfaces

**Stock Endpoints:**

`GET /api/v1/stocks`
- Response 200: `[{ "id": "uuid", "symbol": "AAPL", "company_name": "Apple Inc.", "sector": "Technology", "fortune_500_rank": 3 }]`
- Returns all Fortune 500 stocks

`GET /api/v1/stocks/{symbol}`
- Response 200: Full stock object with current market data and sentiment
- Response 404: Stock not found

`GET /api/v1/stocks/search?q=apple`
- Query Params: `q` (search query)
- Response 200: Array of matching stocks (PostgreSQL FTS)
- Used in Epic 3 for stock search functionality

**Market Data Endpoints (Internal/Admin):**

`GET /api/v1/market-data/{stock_id}/latest`
- Response 200: Latest market data for a stock
- Response 404: No market data found

`GET /api/v1/market-data/{stock_id}/history`
- Query Params: `?start_date=2024-10-01&end_date=2024-10-30`
- Response 200: Historical market data array

**Sentiment Data Endpoints (Internal/Admin):**

`GET /api/v1/sentiment/{stock_id}/latest`
- Response 200: Latest aggregated sentiment score with source attribution
- Response 404: No sentiment data found

**Recommendation Endpoints:**

`POST /api/v1/recommendations/generate` (Admin/Internal - triggered by scheduled task)
- Request Body: `{ "max_recommendations": 10 }`
- Response 201: `{ "count": 10, "recommendations": [...] }`
- Generates new recommendations (called by APScheduler task)

`GET /api/v1/recommendations` (Used in Epic 3)
- Query Params: `?holding_period=daily&risk_level=low&confidence_min=0.7`
- Response 200: `[{ "id": 1, "stock": {...}, "signal": "buy", "confidence": 0.85, "sentiment": 0.7, "risk": "medium", "explanation": "..." }]`
- Filtered by user tier (free: 5 stocks max, premium: all)

**Background Job Configuration (APScheduler):**

Jobs defined in `backend/app/tasks/`:
- `collect_market_data()` - Hourly trigger, collects market data for all 500 stocks
- `collect_sentiment()` - Hourly trigger, collects sentiment from Twitter and web sources
- `generate_recommendations()` - Hourly trigger (or 5-minute), generates ~10 daily recommendations

Job scheduling configured in `backend/app/main.py` or `backend/app/lifetime.py`:
```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.add_job(collect_market_data, 'cron', hour='*', minute=0)  # Every hour
scheduler.add_job(collect_sentiment, 'cron', hour='*', minute=5)  # Every hour at :05
scheduler.add_job(generate_recommendations, 'cron', hour='*', minute=10)  # Every hour at :10
```

### Workflows and Sequencing

**Market Data Collection Workflow:**
1. APScheduler triggers `collect_market_data()` job hourly (or configurable interval)
2. Task queries all stocks from `stocks` table (500 stocks)
3. Batch processor splits stocks into batches (50 stocks per batch)
4. For each batch:
   - Calls market data API (Alpha Vantage, Yahoo Finance) with rate limiting
   - Parses response (price, volume, timestamp)
   - Stores in `market_data` table
   - Logs success/failure per stock
5. Reports aggregate results: "Processed 487/500 stocks successfully"
6. Failed stocks retry on next cycle (graceful degradation)

**Sentiment Collection Workflow:**
1. APScheduler triggers `collect_sentiment()` job hourly (or configurable interval)
2. Task queries all stocks from `stocks` table
3. For each stock:
   - Twitter Collector: Searches Twitter API for tweets mentioning stock symbol/company name
   - Web Scraping Collector: Scrapes news sites/financial forums for stock mentions
   - Each collector calculates sentiment score (positive/negative/neutral) and normalizes
   - Stores individual source sentiment in `sentiment_data` table with source attribution
4. Sentiment Aggregator combines multiple sources into unified sentiment score
5. Logs collection progress and handles rate limits per source
6. Failed sources don't stop entire pipeline (graceful degradation)

**ML Model Training Workflow (One-time or periodic):**
1. Developer/admin triggers training script: `python -m backend.app.services.ml_service train`
2. Training pipeline loads historical market data and sentiment data
3. Feature engineering: Combines market data + sentiment → feature vectors
4. Train neural network model on historical data
5. Train Random Forest classifier model on historical data
6. Evaluate models: Calculate R², accuracy metrics
7. Save model artifacts to `ml-models/` directory (versioned)
8. Log model performance metrics for tracking

**ML Inference Workflow (Per Recommendation Generation):**
1. Recommendation generation task calls ML inference service
2. For each stock candidate:
   - Load current market data (latest price, volume)
   - Load latest aggregated sentiment score
   - Prepare feature vector: [price, volume, sentiment, historical_features]
   - Neural network model inference → prediction signal + confidence score
   - Random Forest model inference → prediction signal + confidence score
   - Combine model outputs (ensemble or majority vote)
   - Calculate confidence score from R² analysis
3. Return predictions for all stocks

**Recommendation Generation Workflow:**
1. APScheduler triggers `generate_recommendations()` job hourly (or 5-minute)
2. Service queries ML inference service for predictions on all 500 stocks
3. For each stock:
   - Get ML prediction (signal, confidence)
   - Get latest aggregated sentiment score
   - Calculate risk level (low/medium/high) based on volatility, ML uncertainty
   - Filter by user preferences (holding period) - applied when generating user-specific recommendations in Epic 3
4. Rank stocks by: confidence score (highest first), sentiment (most positive first)
5. Select top ~10 stocks for recommendations
6. Generate explanations: Synthesize ML signals, sentiment, risk into human-readable explanations
7. Store recommendations in `recommendations` table with all metadata
8. Log generation results and model performance metrics

## Non-Functional Requirements

### Performance

**Target Metrics (per PRD NFR001, Architecture Performance Considerations):**
- ML model inference: <1 minute per stock prediction (per PRD FR011)
- Market data collection: Process 500 stocks hourly within processing window (target: <30 minutes for full batch)
- Sentiment collection: Process 500 stocks hourly within processing window (target: <30 minutes for full batch)
- Recommendation generation: Complete within 1 minute of request (per PRD NFR001)
- API endpoints: <500ms for data retrieval endpoints (per Architecture)
- Batch processing: Partial success acceptable (e.g., 450/500 stocks updated successfully)

**Optimization Strategies:**
- Batch processing: Process stocks in batches of 50 to manage API rate limits efficiently
- Async/await: Use async processing for concurrent API calls within rate limits
- Database indexes: Index `market_data.timestamp`, `sentiment_data.timestamp` for time-series queries
- Model caching: Load ML models once at startup, reuse for inference (per Architecture)
- Retry logic: Exponential backoff for API failures to minimize retry overhead
- Graceful degradation: Partial success acceptable (don't fail entire pipeline if some stocks fail)

[Source: dist/PRD.md#nfr001-performance-requirements, dist/architecture.md#performance-considerations]

### Security

**API Security (per PRD NFR004, Architecture Security):**
- External API credentials: Stored in environment variables (never committed)
- Twitter API rate limiting: Respect free-tier limits (prevent API key revocation)
- Web scraping ethics: Rate limiting, robots.txt respect, ethical practices
- Data source validation: Validate API responses to prevent injection attacks
- HTTPS: All external API calls use HTTPS (Twitter API, financial data APIs)

**Data Protection:**
- Financial data: Market data and sentiment data encrypted at rest (PostgreSQL)
- Model artifacts: ML model files stored securely (GitHub LFS or cloud storage)
- API keys: Rotate credentials periodically if compromised
- Input validation: Pydantic schemas validate all ML model inputs

**ML Model Security:**
- Model versioning: Track model versions to prevent model poisoning attacks
- Input sanitization: Validate feature vectors before model inference
- Output validation: Validate model predictions (confidence scores in valid range)

[Source: dist/PRD.md#nfr004-security--privacy, dist/architecture.md#security-architecture]

### Reliability/Availability

**Availability Targets (per PRD NFR002):**
- System availability: 95%+ during business hours (free-tier infrastructure constraints)
- Data pipeline reliability: Hourly pipeline runs with <5% failure rate (per PRD NFR002)
- Graceful degradation: Partial success acceptable (450/500 stocks updated is OK)
- Scheduled jobs: APScheduler jobs continue running even if individual stocks fail

**Error Handling:**
- API failures: Retry logic with exponential backoff (3 retries)
- Missing data: Handle gracefully (skip stocks with missing data, log warnings)
- Model inference failures: Log errors, continue with remaining stocks
- Database connection failures: Connection pooling with retry logic (SQLAlchemy)

**Recovery Behavior:**
- Failed stocks retry on next cycle (don't block entire pipeline)
- Model inference failures: Use fallback prediction or skip stock
- Data source unavailability: Continue with available sources (e.g., if Twitter API down, use web scraping only)

**Job Overlap Handling:**
- APScheduler: Prevent overlapping job runs (if previous run still running, skip or queue)
- Idempotent operations: Re-running jobs doesn't create duplicates

[Source: dist/PRD.md#nfr002-reliability--availability, dist/architecture.md#pattern-4-hourly-batch-processing]

### Observability

**Logging Requirements (per Architecture Logging Strategy):**
- Backend: Structured JSON logs for Render log aggregation
  - Log API requests: `logger.info("Market data collected", extra={"stock_id": stock_id, "price": price})`
  - Log scheduled jobs: `logger.info("Market data collection completed", extra={"success_count": 487, "failure_count": 13})`
  - Log ML inference: `logger.info("ML prediction generated", extra={"stock_id": stock_id, "signal": "buy", "confidence": 0.85})`
  - Log errors: `logger.error("API call failed", extra={"stock_id": stock_id, "error": str(e)})`
- Log levels: DEBUG (development), INFO (production events), ERROR (production errors)

**Metrics to Track:**
- Data collection success rate: Market data (target: >95%), sentiment (target: >95%)
- ML model performance: R² metrics, accuracy over time
- Recommendation generation: Count generated per day, confidence score distribution
- API response times: Market data API latency, sentiment API latency
- Job execution time: Time to process all 500 stocks (market data, sentiment)
- Data freshness: Timestamp of last update per stock (track staleness)

**Monitoring:**
- Render dashboard: Backend logs and metrics visible in Render dashboard
- Job execution status: Track scheduled job completion/failure
- Model performance degradation: Alert if R² drops below threshold
- Data source health: Monitor API availability (Twitter API, financial data APIs)

[Source: dist/architecture.md#logging-strategy, dist/PRD.md#fr024-model-performance-tracking]

## Dependencies and Integrations

**Backend Dependencies (Python/FastAPI):**
- `fastapi` (latest) - Web framework (already installed)
- `sqlalchemy` (2.0.x) - ORM for database operations (already installed)
- `alembic` (latest) - Database migrations (already installed)
- `apscheduler[sqlalchemy]` (3.x) - Background job scheduling (NEW - required for Epic 2)
- `pydantic` (latest) - Data validation (already installed)
- `httpx` (latest) - HTTP client for external API calls (already installed)
- `pytorch` (latest) - Neural network ML framework (NEW - required for Story 2.5)
- `tensorflow` (latest) - Alternative neural network framework (NEW - optional, can use PyTorch only)
- `scikit-learn` (latest) - Random Forest classifier (NEW - required for Story 2.5)
- `pandas` (latest) - Data processing for training pipeline (NEW - required for Story 2.5)
- `numpy` (latest) - Numerical computing (NEW - required for ML models)
- `beautifulsoup4` (latest) - Web scraping (NEW - required for Story 2.4)
- `requests` (latest) - HTTP library for web scraping (NEW - required for Story 2.4)
- `python-dotenv` (latest) - Environment variable management (already installed via pydantic[dotenv])
- `python-twitter` or `tweepy` (latest) - Twitter API client (NEW - required for Story 2.3)

**External Integrations:**
- **Twitter API** - Sentiment collection (Story 2.3)
  - Integration point: `backend/app/services/sentiment_service.py`
  - API key from environment variable: `TWITTER_API_KEY`, `TWITTER_API_SECRET`
  - Rate limits: Free tier or basic tier limits (respect rate limits)
- **Financial Data APIs** - Market data collection (Story 2.2)
  - Alpha Vantage API (free tier) or Yahoo Finance API
  - Integration point: `backend/app/services/data_collection.py`
  - API key from environment variable: `ALPHA_VANTAGE_API_KEY` or similar
  - Rate limits: Free tier limits (5 calls/minute for Alpha Vantage free tier)
- **Web Scraping Sources** - Additional sentiment (Story 2.4)
  - Target sources: Financial news sites, financial forums
  - Integration point: `backend/app/services/sentiment_service.py`
  - Ethical practices: Rate limiting, robots.txt respect

**Version Constraints:**
- Python: 3.11+ (required for FastAPI async support)
- PostgreSQL: 15+ (required for database features)
- APScheduler: 3.x (required for background jobs)

**Integration Points:**
1. Backend ↔ External APIs: HTTP API calls (httpx/requests) with async support
2. Tasks ↔ Services: APScheduler triggers background jobs calling service functions
3. ML Service ↔ Models: Loads model artifacts from `ml-models/` directory
4. Database ↔ Services: SQLAlchemy ORM with async support for data storage

[Source: dist/architecture.md#technology-stack-details, dist/architecture.md#integration-points]

## Acceptance Criteria (Authoritative)

**Story 2.1: Fortune 500 Stock Data Setup**
1. Fortune 500 stock list imported into stocks table
2. Each stock has: symbol, company_name, sector, fortune_500_rank
3. Data validated for completeness (all 500 stocks present)
4. Stock lookup by symbol or name works efficiently
5. Admin script/endpoint to refresh stock list if needed

**Story 2.2: Market Data Collection Pipeline**
1. Market data collection script/service using free APIs (Alpha Vantage, Yahoo Finance, or similar)
2. Hourly (or configurable interval) scheduled job runs automatically
3. Data collected: stock price, volume, timestamp
4. Data stored in market_data table with proper timestamps
5. Error handling for API failures (retry logic, logging)
6. Rate limiting respected for free API tiers
7. Data freshness tracked (last_update timestamp per stock)

**Story 2.3: Twitter Sentiment Collection** ⚠️ **DEFERRED TO V2**

**Status:** Deferred to v2 due to Twitter API cost ($200/month). See ADR-006 in architecture.md.

1. Twitter API integration configured (free tier or basic tier)
2. Sentiment collection script searches for tweets mentioning stock symbols or company names
3. Hourly (or configurable) scheduled job collects sentiment data
4. Sentiment scores calculated (positive/negative/neutral) and normalized
5. Data stored in sentiment_data table: stock_id, sentiment_score, source, timestamp
6. Rate limiting handled (Twitter API limits respected)
7. Error handling for API failures with retry logic

**Story 2.4: Additional Sentiment Sources (Web Scraping)** ⭐ **PRIMARY SENTIMENT SOURCE FOR MVP**
1. Web scraping infrastructure (BeautifulSoup/Scrapy) configured
2. Sentiment collected from 2-3 additional sources (e.g., financial news sites)
3. Ethical scraping practices: rate limiting, robots.txt respect
4. Sentiment aggregation: multiple sources combined into unified sentiment score
5. Sentiment data stored with source attribution
6. Error handling for scraping failures (sites down, structure changes)

**Story 2.5: ML Model Training Infrastructure**
1. Python ML environment configured with PyTorch, TensorFlow, scikit-learn
2. Training data pipeline: historical market data + sentiment → feature vectors
3. Neural network model architecture defined (can be simple initially)
4. Random Forest classifier model defined
5. Training script can run locally or in cloud
6. Model artifacts saved (can use GitHub LFS or cloud storage)
7. Model versioning system in place

**Story 2.6: ML Model Inference Service**
1. Model inference service/endpoint in FastAPI
2. Input: current market data + sentiment scores for a stock
3. Models generate: prediction signal (buy/sell/hold) + confidence score
4. Confidence score calculated from R² analysis of model performance
5. Inference completes within <1 minute latency requirement
6. Both neural network and Random Forest models used (ensemble or separate)
7. Model performance metrics logged (R², accuracy)

**Story 2.7: Risk Assessment Calculation**
1. Risk calculation algorithm defined (based on volatility, ML model uncertainty, market conditions)
2. Risk level assigned: Low, Medium, High
3. Risk calculation integrated into recommendation generation
4. Risk indicators stored with recommendations
5. Risk calculation uses recent market volatility data

**Story 2.8: Recommendation Generation Logic**
1. Recommendation generation algorithm: selects top stocks based on ML signals, confidence, sentiment
2. Generates ~10 recommendations daily (configurable)
3. Recommendations include: stock, signal (buy/sell/hold), confidence score, sentiment score, risk level
4. Recommendations filtered by user holding period preference (when user-specific)
5. Recommendations stored in database with timestamp
6. Generation process runs on schedule (hourly or 5-minute if cost-effective)
7. Generation completes within latency requirements

[Source: dist/epics.md#epic-2-data-pipeline--ml-engine]

## Traceability Mapping

| Acceptance Criteria | PRD Reference | Architecture Reference | Component/API | Test Idea |
|-------------------|---------------|------------------------|---------------|-----------|
| AC 2.1.1-2.1.5: Fortune 500 stock data setup | FR005 | Data Architecture section | `backend/app/services/stock_import_service.py`, `stocks` table | Verify all 500 stocks imported, symbol lookup works |
| AC 2.2.1-2.2.7: Market data collection | FR006 | Pattern 4 (Hourly Batch Processing) | `backend/app/tasks/market_data.py`, `backend/app/services/data_collection.py` | Test hourly job execution, API rate limiting, graceful degradation |
| AC 2.3.1-2.3.7: Twitter sentiment collection | FR008 | Pattern 1 (Multi-Source Sentiment Aggregation) | `backend/app/services/sentiment_service.py` (Twitter collector), `backend/app/tasks/sentiment.py` | Test Twitter API integration, sentiment calculation, rate limiting |
| AC 2.4.1-2.4.6: Web scraping sentiment | FR010 | Pattern 1 (Multi-Source Sentiment Aggregation) | `backend/app/services/sentiment_service.py` (web scraping collector) | Test scraping from news sites, ethical practices, aggregation |
| AC 2.5.1-2.5.7: ML model training | FR011 | ML Service section | `backend/app/services/ml_service.py` (training), `ml-models/` directory | Test model training pipeline, feature engineering, model artifacts |
| AC 2.6.1-2.6.7: ML model inference | FR011, FR012 | ML Service section, Performance Considerations | `backend/app/services/ml_service.py` (inference) | Test inference latency <1 minute, confidence score calculation |
| AC 2.7.1-2.7.5: Risk assessment | FR013 | Recommendation Service section | `backend/app/services/recommendation_service.py` (risk calculation) | Test risk calculation algorithm, risk level assignment |
| AC 2.8.1-2.8.7: Recommendation generation | FR014 | Pattern 2 (Confidence-Scored Recommendation Generation) | `backend/app/tasks/recommendations.py`, `backend/app/services/recommendation_service.py` | Test recommendation generation, explanation synthesis, scheduling |

## Risks, Assumptions, Open Questions

**Risks:**
1. **Risk: Twitter API rate limits insufficient for 500 stocks** - Twitter free tier may have rate limits that prevent collecting sentiment for all 500 stocks hourly
   - Mitigation: Use batch processing, respect rate limits, consider Twitter API basic tier upgrade if needed
   - Next step: Test Twitter API rate limits during Story 2.3, adjust batch size if needed

2. **Risk: Financial data API rate limits** - Alpha Vantage free tier (5 calls/minute) may be insufficient for 500 stocks hourly
   - Mitigation: Use batch processing with delays, consider multiple API keys or alternative APIs (Yahoo Finance), graceful degradation
   - Next step: Evaluate API options during Story 2.2, implement batch processing with rate limiting

3. **Risk: ML model training data insufficient** - Historical data may be limited initially, affecting model accuracy
   - Mitigation: Start with simple model architectures, collect historical data over time, retrain models periodically
   - Next step: Begin with basic models in Story 2.5, enhance as data accumulates

4. **Risk: ML inference latency exceeds 1 minute** - Model inference on 500 stocks may take longer than target latency
   - Mitigation: Use model caching, batch inference where possible, optimize model architectures
   - Next step: Monitor inference latency during Story 2.6, optimize models if needed

5. **Risk: Web scraping sites change structure** - News sites may change HTML structure, breaking scrapers
   - Mitigation: Implement robust error handling, use multiple sources, monitor scraping failures
   - Next step: Design flexible scraping architecture in Story 2.4, test with multiple sites

6. **Risk: APScheduler job overlap** - If hourly jobs take longer than 1 hour, overlapping runs may cause issues
   - Mitigation: Implement job locking, prevent overlap, or queue jobs
   - Next step: Configure APScheduler overlap handling in Story 2.2

**Assumptions:**
1. **Assumption: Free-tier APIs sufficient for MVP** - Assume Alpha Vantage free tier and Twitter free/basic tier sufficient for initial data collection
   - Validation: Test API limits during Stories 2.2-2.3, upgrade if needed

2. **Assumption: Historical data accumulates over time** - Assume historical market data and sentiment accumulate as pipeline runs, enabling ML model training
   - Validation: Monitor data accumulation, adjust model training schedule if needed

3. **Assumption: Simple ML models sufficient for MVP** - Assume basic neural network and Random Forest architectures sufficient for initial predictions
   - Validation: Monitor model performance (R² metrics), enhance models if accuracy insufficient

4. **Assumption: Batch processing handles 500 stocks** - Assume batch processing (50 stocks per batch) completes within hourly window
   - Validation: Monitor job execution times during Stories 2.2-2.3, adjust batch size if needed

**Open Questions:**
1. **Question: ML model ensemble strategy?** - Should neural network and Random Forest models be combined (ensemble) or used separately?
   - Resolution needed: Decide ensemble strategy during Story 2.6 implementation
   - Current approach: Use ensemble (majority vote or weighted average) for improved accuracy

2. **Question: Sentiment aggregation weights?** - How should multiple sentiment sources be weighted (Twitter vs web scraping)?
   - Resolution needed: Define weighting strategy during Story 2.4 implementation
   - Current approach: Equal weights initially, adjust based on source reliability

3. **Question: Recommendation count per day?** - PRD specifies ~10 recommendations daily, but generation runs hourly. How many per hour?
   - Resolution needed: Clarify recommendation generation strategy (10 total per day vs 10 per generation cycle)
   - Current approach: Generate top 10 recommendations hourly, user sees latest (Epic 3 dashboard shows most recent)

4. **Question: Model retraining frequency?** - How often should ML models be retrained as new data accumulates?
   - Resolution needed: Define retraining schedule (weekly, monthly, or on-demand)
   - Current approach: Retrain monthly initially, adjust based on model performance

## Test Strategy Summary

**Test Levels:**

1. **Unit Tests (Backend):**
   - Stock import: Test CSV parsing, database insertion, validation logic
   - Market data collection: Test API call handling, rate limiting, error retry logic
   - Sentiment calculation: Test sentiment score normalization, aggregation logic
   - ML model inference: Test feature vector preparation, prediction generation
   - Risk calculation: Test risk level assignment algorithm
   - Recommendation ranking: Test ranking algorithm (confidence, sentiment)
   - Framework: pytest, pytest-asyncio

2. **Integration Tests (API/Service):**
   - Market data collection: Test hourly job execution, database storage, graceful degradation
   - Sentiment collection: Test Twitter API integration, web scraping, aggregation
   - ML inference: Test model loading, inference service, confidence score calculation
   - Recommendation generation: Test end-to-end generation workflow
   - Framework: pytest with FastAPI TestClient (AsyncClient), mock external APIs

3. **Performance Tests:**
   - Batch processing: Verify 500 stocks processed within time constraints (<30 minutes)
   - ML inference: Verify inference latency <1 minute per stock
   - API rate limiting: Verify rate limits respected (Twitter API, financial data APIs)
   - Database queries: Verify time-series queries use indexes efficiently

4. **End-to-End Tests (Pipeline):**
   - Full data pipeline: Test hourly job execution from start to finish
   - Recommendation generation: Test complete workflow from data collection → ML inference → recommendations
   - Graceful degradation: Test pipeline continues with partial failures
   - Framework: Manual testing or pytest with real/mocked external APIs

**Test Coverage Targets:**
- Backend services: 80%+ coverage (critical paths: data collection, ML inference, recommendation generation)
- APScheduler tasks: 70%+ coverage (critical paths: job execution, error handling)
- ML model training/inference: 60%+ coverage (critical paths: feature engineering, prediction generation)

**Edge Cases to Test:**
- API rate limit exceeded (handle gracefully, retry later)
- External API unavailable (continue with available sources, graceful degradation)
- Missing historical data for ML training (handle gracefully, use available data)
- ML model inference failure (log error, skip stock, continue)
- Scraping site structure changed (robust error handling, log failure)
- Batch processing partial failure (continue with successful stocks, retry failures next cycle)
- Database connection failure (retry logic, graceful degradation)

**Security Tests:**
- API key validation: Verify credentials stored securely (environment variables)
- Input validation: Verify ML model inputs validated (prevent injection attacks)
- Model artifact security: Verify model files stored securely

[Source: dist/tech-spec-epic-1.md#test-strategy-summary, dist/architecture.md#performance-considerations]

