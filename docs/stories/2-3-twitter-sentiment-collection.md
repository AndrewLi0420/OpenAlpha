# Story 2.3: Twitter Sentiment Collection

**Status: deferred-to-v2**

**Note:** This story is deferred to v2. Twitter API Basic tier costs $200/month, which is cost-prohibitive for MVP. For MVP, we're focusing on free sentiment sources via web scraping (Story 2.4). This story can be implemented in v2 when product-market fit is validated and budget allows. See ADR-006 in architecture.md for full decision rationale.

## Story

As a system,
I want to collect sentiment data from Twitter API for Fortune 500 stocks hourly (or configurable interval),
so that sentiment scores can inform ML predictions.

## Acceptance Criteria

1. Twitter API integration configured (free tier or basic tier)
2. Sentiment collection script searches for tweets mentioning stock symbols or company names
3. Hourly (or configurable) scheduled job collects sentiment data
4. Sentiment scores calculated (positive/negative/neutral) and normalized
5. Data stored in sentiment_data table: stock_id, sentiment_score, source, timestamp
6. Rate limiting handled (Twitter API limits respected)
7. Error handling for API failures with retry logic

## Tasks / Subtasks

- [ ] Create Twitter sentiment collection service (AC: 1, 2, 4)
  - [ ] Create `backend/app/services/sentiment_service.py` following service pattern from Story 2.2
  - [ ] Implement Twitter API client: Configure API credentials (TWITTER_API_KEY, TWITTER_API_SECRET) from environment variables
  - [ ] Implement function: `collect_twitter_sentiment(stock_symbol: str, company_name: str)` → searches tweets, returns sentiment score
  - [ ] Add tweet search logic: Search for tweets mentioning stock symbol or company name using Twitter API v2 search endpoint
  - [ ] Implement sentiment calculation: Analyze tweet text (positive/negative/neutral) using simple keyword-based approach or sentiment analysis library (vaderSentiment, textblob)
  - [ ] Normalize sentiment scores: Convert to -1.0 to 1.0 scale (-1.0 = negative, 0.0 = neutral, 1.0 = positive)
  - [ ] Add error handling: Handle API failures, invalid responses, missing data, authentication errors
  - [ ] Add rate limiting: Respect Twitter API rate limits (free tier: 500 tweets/month, basic tier: varies - check API limits)
  - [ ] Validate response data: Ensure sentiment score is valid numeric value in range [-1.0, 1.0]
  - [ ] Parse timestamp: Convert tweet timestamps to UTC datetime for storage

- [ ] Create sentiment data CRUD operations (AC: 5)
  - [ ] Create `backend/app/crud/sentiment_data.py` following CRUD pattern from Story 2.2
  - [ ] Implement `create_sentiment_data()` - Insert new sentiment data record with source attribution
  - [ ] Implement `get_latest_sentiment_data(stock_id)` - Get most recent sentiment score for a stock
  - [ ] Implement `get_sentiment_data_history(stock_id, start_date, end_date)` - Get historical sentiment data
  - [ ] Implement `get_aggregated_sentiment(stock_id)` - Aggregate sentiment from multiple sources (for future use with Story 2.4)
  - [ ] Verify database model exists: `backend/app/models/sentiment_data.py` from Story 1.2 (verify fields: id, stock_id, sentiment_score, source, timestamp, created_at)
  - [ ] Use async SQLAlchemy patterns following Story 2.2 patterns
  - [ ] Ensure source field stores "twitter" for Twitter API data

- [ ] Create APScheduler scheduled task (AC: 3)
  - [ ] Create or extend `backend/app/tasks/sentiment.py` following task pattern from Story 2.2
  - [ ] Implement `collect_twitter_sentiment()` async function - Triggers Twitter sentiment collection for all 500 stocks
  - [ ] Implement batch processing: Process stocks in batches of 50 (manage API rate limits similar to market data collection)
  - [ ] Integrate with APScheduler: Add job to scheduler in `backend/app/lifetime.py` (alongside market data collection job)
  - [ ] Configure hourly trigger: `scheduler.add_job(collect_twitter_sentiment, 'cron', hour='*', minute=5)` (offset from market data job at minute 0)
  - [ ] Add overlap handling: Prevent overlapping job runs (use APScheduler coalesce/max_instances)
  - [ ] Make job idempotent: Re-running doesn't create duplicate records

- [ ] Implement batch processing with graceful degradation (AC: 2, 3, 7)
  - [ ] Process 500 stocks in batches of 50 stocks per batch (or smaller if Twitter API rate limits are stricter)
  - [ ] For each batch: Call Twitter API with rate limiting delays between calls
  - [ ] Track success/failure per stock: Log which stocks succeeded/failed
  - [ ] Continue processing on partial failures: Don't stop entire pipeline if some stocks fail
  - [ ] Log aggregate results: "Processed 487/500 stocks successfully"
  - [ ] Use async/await for concurrent processing within rate limits
  - [ ] Handle Twitter API rate limit errors gracefully: Retry after rate limit window resets

- [ ] Implement retry logic for API failures (AC: 7)
  - [ ] Add exponential backoff retry logic: 3 retries with increasing delays (1s, 2s, 4s) following Story 2.2 pattern
  - [ ] Handle specific error types: API rate limit exceeded (429), API unavailable (503), authentication errors (401), timeout errors
  - [ ] Log retry attempts: Include stock symbol and attempt number in logs
  - [ ] Fail gracefully after max retries: Log failure and continue with next stock
  - [ ] Handle Twitter-specific errors: Invalid request, malformed queries, API version changes

- [ ] Implement rate limiting (AC: 6)
  - [ ] Add rate limiting logic: Track Twitter API calls per minute/hour/day (respect free/basic tier limits)
  - [ ] Add delays between API calls: Respect Twitter API rate limits (check actual limits for tier used)
  - [ ] Add batch delays: Wait between batches to stay within rate limits
  - [ ] Handle rate limit exceeded errors: Log and retry after rate limit window resets (Twitter API provides reset time in headers)
  - [ ] Consider monthly limits for free tier: Track usage across month, skip collection if limit reached

- [ ] Track sentiment data freshness (AC: 3, 5)
  - [ ] Add sentiment freshness tracking: Query last successful sentiment collection timestamp per stock
  - [ ] Update freshness tracking after successful sentiment collection
  - [ ] Query stale sentiment: Identify stocks with sentiment data older than 1 hour
  - [ ] Log data freshness: Report stocks with stale sentiment data

- [ ] Install Twitter API dependency (AC: 1)
  - [ ] Add Twitter API client library to `backend/requirements.txt` (tweepy or python-twitter or twitter-api-v2)
  - [ ] Install library and verify version compatibility (Python 3.11+, async support if available)
  - [ ] Configure Twitter API credentials: Add TWITTER_API_KEY, TWITTER_API_SECRET to environment variables
  - [ ] Add credentials to `backend/app/core/config.py` settings

- [ ] Testing: Unit tests for Twitter sentiment collection service (AC: 1, 2, 4, 6, 7)
  - [ ] Test Twitter API client: Mock API responses, test authentication, test tweet search logic
  - [ ] Test sentiment calculation: Test positive/negative/neutral classification, test normalization to [-1.0, 1.0]
  - [ ] Test rate limiting: Verify delays between calls, rate limit handling, monthly limit tracking
  - [ ] Test retry logic: Mock API failures, verify exponential backoff
  - [ ] Test error handling: Invalid responses, missing data, authentication errors, API errors
  - [ ] Use pytest with async support (`pytest-asyncio`)
  - [ ] Mock Twitter API calls using `responses` library or `httpx` AsyncClient
  - [ ] Test sentiment normalization edge cases: All positive, all negative, mixed sentiment

- [ ] Testing: Integration tests for scheduled task (AC: 3, 7)
  - [ ] Test APScheduler job execution: Verify job runs on schedule (hourly at minute 5)
  - [ ] Test batch processing: Verify 500 stocks processed in batches (50 per batch or appropriate size)
  - [ ] Test graceful degradation: Verify pipeline continues with partial failures
  - [ ] Test database storage: Verify sentiment_data records created correctly with source="twitter"
  - [ ] Use pytest with FastAPI TestClient (AsyncClient)
  - [ ] Mock Twitter API but test real database operations
  - [ ] Test job overlap prevention: Verify max_instances=1 prevents concurrent runs

- [ ] Testing: Performance tests for batch processing (AC: 2, 3, 6)
  - [ ] Test batch processing time: Verify 500 stocks processed within time constraints (considering Twitter API rate limits)
  - [ ] Test rate limiting: Verify Twitter API calls respect rate limits
  - [ ] Test database query performance: Verify time-series queries use indexes efficiently
  - [ ] Test concurrent processing: Verify async processing doesn't exceed rate limits

## Dev Notes

### MVP Decision: Deferred to v2

**Decision (2025-01-31):** Twitter sentiment collection deferred to v2. Focus on free sentiment sources (Story 2.4 - web scraping) for MVP to validate product-market fit before investing in paid API access.

**Rationale:**
- Twitter API Basic tier: $200/month (cost-prohibitive for MVP validation)
- Free alternatives via web scraping provide good sentiment data quality
- Can add Twitter integration later when product-market fit validated
- Multi-source aggregation pattern already designed to support both sources

**References:**
- [ADR-006: Defer Twitter Sentiment Collection to v2](dist/architecture.md#adr-006-defer-twitter-sentiment-collection-to-v2)
- Story 2.4 becomes primary sentiment source for MVP

### Learnings from Previous Story

**From Story 2-2-market-data-collection-pipeline (Status: done)**

- **Service and CRUD Pattern**: Market data collection service established pattern at `backend/app/services/data_collection.py` with rate limiting (`RateLimiter` class), exponential backoff retry logic (3 retries: 1s, 2s, 4s delays), and error handling. Follow same patterns for Twitter sentiment collection service. Market data CRUD available at `backend/app/crud/market_data.py` - use as template for sentiment_data CRUD operations.

- **APScheduler Task Pattern**: Market data task established pattern at `backend/app/tasks/market_data.py` with batch processing (50 stocks per batch), graceful degradation, and overlap prevention (max_instances=1, coalesce=True). APScheduler integrated in `backend/app/lifetime.py` with startup/shutdown hooks. Use same pattern for sentiment collection task but offset trigger time (minute 5 vs minute 0) to avoid resource contention.

- **Rate Limiting Implementation**: Rate limiter class pattern from `backend/app/services/data_collection.py:25-47` enforces delays between API calls. Twitter API rate limits may differ from Alpha Vantage - check actual limits for tier used (free tier: 500 tweets/month, basic tier: higher limits). May need to process smaller batches or longer delays if Twitter limits are stricter.

- **Data Freshness Tracking**: Pattern established at `backend/app/crud/market_data.py:122-160` with `get_stocks_with_stale_data()` function. Reuse same pattern for sentiment data freshness tracking.

- **Testing Patterns**: Comprehensive test suite from Story 2.2:
  - Unit tests: `backend/tests/test_crud/test_market_data.py` - Follow pattern for sentiment_data tests
  - Integration tests: `backend/tests/test_api/test_market_data_collection.py` - Follow pattern for Twitter sentiment collection tests
  - Mock external APIs, test real database operations, use async test patterns

- **File Organization**: Follow established patterns:
  - Services: `backend/app/services/sentiment_service.py` (create, may extend later for web scraping in Story 2.4)
  - CRUD: `backend/app/crud/sentiment_data.py` (create)
  - Tasks: `backend/app/tasks/sentiment.py` (create, may extend for web scraping in Story 2.4)
  - Models: `backend/app/models/sentiment_data.py` (verify exists from Story 1.2)

- **Async Patterns**: Use async SQLAlchemy patterns throughout: `AsyncSession`, `select()` statements, async functions. Follow patterns from `backend/app/crud/market_data.py` and `backend/app/services/data_collection.py`.

- **Dependencies**: Twitter API client library required (tweepy, python-twitter, or twitter-api-v2). Choose library with async support if available. APScheduler already installed from Story 2.2.

- **Architectural Decisions**:
  - SQLAlchemy 2.0.x for ORM (async support)
  - PostgreSQL 15+ database
  - UUID primary keys
  - Batch processing with graceful degradation (Pattern 4)
  - Exponential backoff retry (3 attempts: 1s, 2s, 4s)

- **Configuration**: Add Twitter API credentials to `backend/app/core/config.py` similar to ALPHA_VANTAGE_API_KEY. Consider startup validation to fail fast if credentials missing.

- **Logging**: Follow structured logging pattern from market data collection: `logger.info("Twitter sentiment collected", extra={"stock_id": stock_id, "sentiment_score": score})`. Log batch processing results, rate limit events, and errors.

[Source: docs/stories/2-2-market-data-collection-pipeline.md#Dev-Agent-Record, dist/architecture.md#data-architecture]

### Architecture Alignment

This story implements the Twitter sentiment collection component of the sentiment data collection pipeline as defined in the [Epic 2 Tech Spec](dist/tech-spec-epic-2.md), [Architecture document](dist/architecture.md#data-architecture), and [Epic Breakdown](dist/epics.md#story-23-twitter-sentiment-collection). This story establishes the first sentiment data source for Epic 2 (Data Pipeline & ML Engine), providing sentiment scores that will be aggregated with additional sources in Story 2.4.

**Service Definition (per Tech Spec):**
- **Twitter Sentiment Collector**: Collects sentiment data from Twitter API for Fortune 500 stocks
  - Location: `backend/app/services/sentiment_service.py` (Twitter collector component)
  - Inputs: Stock symbols/company names, Twitter API credentials (environment variables)
  - Outputs: Sentiment scores in `sentiment_data` table with source="twitter"
  - Responsibilities: Tweet search, sentiment calculation, rate limiting, error handling

- **Sentiment Collection Task**: APScheduler job that triggers hourly Twitter sentiment collection
  - Location: `backend/app/tasks/sentiment.py`
  - Trigger: Hourly scheduled job (cron: `hour='*', minute=5` offset from market data job)
  - Responsibilities: Batch processing, graceful degradation, job scheduling

[Source: dist/tech-spec-epic-2.md#services-and-modules]

**Database Schema (per Tech Spec):**
- Sentiment Data table populated in Stories 2.3-2.4 with exact schema:
  - `id`: UUID (primary key)
  - `stock_id`: UUID (foreign key → stocks.id), indexed
  - `sentiment_score`: DECIMAL(3, 2) (normalized -1.0 to 1.0)
  - `source`: VARCHAR(50) (e.g., "twitter", "news_site_1", "news_site_2")
  - `timestamp`: TIMESTAMP, indexed (for time-series queries)
  - `created_at`: TIMESTAMP, default now()
- Indexes: `sentiment_data.stock_id` foreign key indexed, `sentiment_data.timestamp` indexed for time-series queries

[Source: dist/tech-spec-epic-2.md#data-models-and-contracts, dist/architecture.md#database-schema-overview]

**Pattern 1: Multi-Source Sentiment Aggregation (per Architecture):**
This story implements the Twitter source component of Pattern 1. Story 2.4 will add web scraping sources, and sentiment aggregation will combine multiple sources. For this story, store sentiment with source="twitter" and prepare for future aggregation in Story 2.4.

[Source: dist/architecture.md#pattern-1-multi-source-sentiment-aggregation-with-transparency]

**Technology Stack:**
- Twitter API client library (tweepy, python-twitter, or twitter-api-v2) for API integration (NEW dependency)
- APScheduler 3.x for background job scheduling (already installed from Story 2.2)
- SQLAlchemy 2.0.x for ORM (async support)
- PostgreSQL 15+ for database storage
- httpx for HTTP client if library uses it (async support for API calls)
- Sentiment analysis library (vaderSentiment or textblob) for sentiment calculation (NEW dependency)

[Source: dist/architecture.md#technology-stack-details, dist/tech-spec-epic-2.md#dependencies-and-integrations]

**Project Structure:**
- Sentiment service: `backend/app/services/sentiment_service.py` (create, extendable for Story 2.4)
- Sentiment CRUD: `backend/app/crud/sentiment_data.py` (create)
- Sentiment task: `backend/app/tasks/sentiment.py` (create, extendable for Story 2.4)
- Sentiment model: `backend/app/models/sentiment_data.py` (verify exists from Story 1.2)

[Source: dist/architecture.md#project-structure, dist/tech-spec-epic-2.md#services-and-modules]

**Sentiment Collection Workflow (per Tech Spec):**
1. APScheduler triggers `collect_twitter_sentiment()` job hourly (minute 5)
2. Task queries all stocks from `stocks` table (500 stocks)
3. Batch processor splits stocks into batches (50 or smaller if Twitter rate limits require)
4. For each stock:
   - Twitter Collector: Searches Twitter API for tweets mentioning stock symbol/company name
   - Calculates sentiment score (positive/negative/neutral) and normalizes to [-1.0, 1.0]
   - Stores individual source sentiment in `sentiment_data` table with source="twitter"
5. Logs collection progress and handles rate limits
6. Failed sources don't stop entire pipeline (graceful degradation)

[Source: dist/tech-spec-epic-2.md#workflows-and-sequencing]

**Performance Requirements (per Tech Spec):**
- Sentiment collection: Process 500 stocks hourly within processing window (target: <30 minutes for full batch, but may vary based on Twitter API rate limits)
- Batch processing: Partial success acceptable (e.g., 450/500 stocks updated successfully)
- API rate limiting: Respect Twitter API rate limits (free tier: 500 tweets/month, basic tier: varies)
- Note: Twitter API rate limits may require smaller batches or longer delays than market data collection

[Source: dist/tech-spec-epic-2.md#performance]

### Technology Stack

**Backend:**
- Python 3.11+
- Twitter API client library: tweepy, python-twitter, or twitter-api-v2 (NEW - required for Story 2.3)
- Sentiment analysis library: vaderSentiment or textblob (NEW - for sentiment calculation)
- APScheduler 3.x: Background job scheduling (already installed from Story 2.2)
- SQLAlchemy 2.0.x: ORM for database operations (async support)
- PostgreSQL 15+: Database storage
- httpx: HTTP client for external API calls (if library uses it, async support)
- Python logging: Structured logging for job execution

**External Integrations:**
- **Twitter API**: Sentiment collection (Story 2.3)
  - Integration point: `backend/app/services/sentiment_service.py`
  - API credentials from environment variables: `TWITTER_API_KEY`, `TWITTER_API_SECRET`
  - Rate limits: Free tier (500 tweets/month) or basic tier (higher limits) - check actual limits
  - Use free tier initially, upgrade if needed
  - API version: Twitter API v2 recommended (v1.1 deprecated)

[Source: dist/architecture.md#technology-stack-details, dist/tech-spec-epic-2.md#dependencies-and-integrations]

### Project Structure Notes

**Backend File Organization:**
- Sentiment service: `backend/app/services/sentiment_service.py` (create, will extend for web scraping in Story 2.4)
- Sentiment CRUD: `backend/app/crud/sentiment_data.py` (create)
- Sentiment task: `backend/app/tasks/sentiment.py` (create, will extend for web scraping in Story 2.4)
- Sentiment model: `backend/app/models/sentiment_data.py` (verify exists from Story 1.2)
- Tests: `backend/tests/test_crud/test_sentiment_data.py`, `backend/tests/test_api/test_twitter_sentiment_collection.py`, `backend/tests/test_api/test_twitter_sentiment_performance.py`

[Source: dist/architecture.md#project-structure]

**Database Schema:**
- Verify sentiment_data table exists from Story 1.2: `backend/app/models/sentiment_data.py`
- Schema should include: id (UUID), stock_id (UUID foreign key indexed), sentiment_score (DECIMAL(3, 2) range [-1.0, 1.0]), source (VARCHAR(50)), timestamp (TIMESTAMP indexed), created_at (TIMESTAMP)
- Indexes: stock_id foreign key index, timestamp index for time-series queries

**Naming Conventions:**
- Python files: `snake_case.py` (`sentiment_service.py`, `sentiment_data.py`)
- Python functions: `snake_case` (`collect_twitter_sentiment`, `get_latest_sentiment_data`)
- Python classes: `PascalCase` (`SentimentService`, `SentimentDataModel`)
- Database tables: Plural, lowercase with underscores (`sentiment_data`)
- Database columns: Lowercase with underscores (`stock_id`, `created_at`)

[Source: dist/architecture.md#implementation-patterns]

### Testing Standards

**Unit Tests (Backend):**
- Test Twitter sentiment collection service: Test API client, tweet search, sentiment calculation, rate limiting, retry logic, error handling
- Test sentiment data CRUD operations: Create, read, historical queries, aggregation queries
- Test sentiment calculation: Test positive/negative/neutral classification, test normalization to [-1.0, 1.0] range
- Test rate limiting: Verify delays between calls, rate limit handling, monthly limit tracking (for free tier)
- Test retry logic: Mock API failures, verify exponential backoff
- Use pytest with async support (`pytest-asyncio`)
- Mock Twitter API calls using `responses` library or `httpx` AsyncClient
- Coverage target: 80%+ for backend services (per Tech Spec)

**Integration Tests (API/Service):**
- Test APScheduler job execution: Verify job runs on schedule (hourly at minute 5), batch processing
- Test graceful degradation: Verify pipeline continues with partial failures
- Test database storage: Verify sentiment_data records created correctly with source="twitter"
- Use pytest with FastAPI TestClient (AsyncClient)
- Mock Twitter API but test real database operations

**Performance Tests (per Tech Spec):**
- Test batch processing: Verify 500 stocks processed within time constraints (considering Twitter API rate limits)
- Test rate limiting: Verify Twitter API calls respect rate limits (free tier: 500 tweets/month or basic tier limits)
- Test database query performance: Verify time-series queries use timestamp index efficiently
- Test concurrent processing: Verify async processing doesn't exceed rate limits

**Edge Cases to Test:**
- Twitter API rate limit exceeded (handle gracefully, retry after reset window)
- External API unavailable (continue with available stocks, graceful degradation)
- Missing or invalid data in API response (handle gracefully, log error)
- No tweets found for stock (return neutral sentiment or skip)
- Sentiment calculation edge cases: All positive tweets, all negative tweets, mixed sentiment
- Authentication errors (401) - fail fast with clear error message
- Batch processing partial failure (continue with successful stocks, retry failures next cycle)
- Database connection failure (retry logic, graceful degradation)
- Job overlap handling (prevent overlapping runs)

[Source: dist/tech-spec-epic-2.md#test-strategy-summary, dist/tech-spec-epic-2.md#performance]

### References

- [Epic 2 Tech Spec: Story 2.3](dist/tech-spec-epic-2.md#story-23-twitter-sentiment-collection) - **Primary technical specification for this story**
- [Epic 2 Tech Spec: Services and Modules](dist/tech-spec-epic-2.md#services-and-modules) - Twitter Sentiment Collector and Sentiment Collection Task definitions
- [Epic 2 Tech Spec: Data Models](dist/tech-spec-epic-2.md#data-models-and-contracts) - Sentiment Data table schema specification
- [Epic 2 Tech Spec: Workflows and Sequencing](dist/tech-spec-epic-2.md#workflows-and-sequencing) - Sentiment Collection Workflow
- [Epic 2 Tech Spec: Acceptance Criteria](dist/tech-spec-epic-2.md#acceptance-criteria-authoritative) - Authoritative AC list
- [Epic 2 Tech Spec: Traceability Mapping](dist/tech-spec-epic-2.md#traceability-mapping) - AC → Component mapping
- [Epic Breakdown: Story 2.3](dist/epics.md#story-23-twitter-sentiment-collection)
- [PRD: Twitter Sentiment Collection (FR008)](dist/PRD.md#fr008-twitter-sentiment-collection)
- [Architecture: Data Architecture](dist/architecture.md#data-architecture)
- [Architecture: Pattern 1 - Multi-Source Sentiment Aggregation](dist/architecture.md#pattern-1-multi-source-sentiment-aggregation-with-transparency)
- [Architecture: Database Schema Overview](dist/architecture.md#database-schema-overview)
- [Architecture: Project Structure](dist/architecture.md#project-structure)
- [Architecture: Background Jobs](dist/architecture.md#deployment-architecture)
- [Previous Story: 2-2 Market Data Collection Pipeline](docs/stories/2-2-market-data-collection-pipeline.md)

## Dev Agent Record

### Context Reference

- `docs/stories/2-3-twitter-sentiment-collection.context.xml`

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

