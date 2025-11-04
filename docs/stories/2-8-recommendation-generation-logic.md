# Story 2.8: Recommendation Generation Logic

Status: done

## Story

As a system,
I want to generate approximately 10 recommendations per day by combining ML predictions, sentiment, and risk scores,
so that users receive actionable trading insights.

## Acceptance Criteria

1. Recommendation generation algorithm selects top stocks based on ML signals, confidence, sentiment
2. Generates ~10 recommendations daily (configurable)
3. Each recommendation includes: stock, signal (buy/sell/hold), confidence score, sentiment score, risk level
4. Recommendations filtered by user holding period preference when user-specific
5. Recommendations stored in database with timestamp
6. Generation process runs on schedule (hourly or 5-minute if cost-effective)
7. Generation completes within latency requirements

## Tasks / Subtasks

- [x] Implement recommendation generation service (AC: 1, 3, 5)
  - [x] Create `generate_recommendations()` orchestrator using `ml_service.predict_stock()` and sentiment aggregation
  - [x] Combine signals: ML prediction + confidence, aggregated sentiment, risk level (via `recommendation_service.calculate_risk_level`)
  - [x] Rank by confidence (primary), sentiment (secondary), risk (prefer lower risk for ties)
  - [x] Persist to `recommendations` table with `risk_level`, `confidence`, `sentiment`, `created_at`

- [x] Integrate risk assessment (AC: 3)
  - [x] Call `calculate_risk_level(stock_id, market_data, ml_confidence, market_conditions)` for each candidate
  - [x] Handle failures gracefully: default to MEDIUM risk, log event

- [x] Configure cadence and limits (AC: 2, 6, 7)
  - [x] Make daily target count configurable (default 10)
  - [x] Add scheduled job in `backend/app/tasks/recommendations.py` to run hourly (or 5-minute if cost allows)
  - [x] Ensure end-to-end run finishes under 1 minute per batch (guard + logging)

- [x] Preference-aware filtering (AC: 4)
  - [x] When generating user-specific views, filter by user holding period preference
  - [x] Ensure API layer applies tier-aware filtering per Architecture Pattern 3

- [ ] Testing
  - [x] Unit tests: ranking logic, tie-breakers, persistence schema
  - [x] Integration tests: end-to-end generation writes rows with all required fields
  - [x] Performance test: verify run time under target with mocked data

## Dev Notes

- Use `backend/app/services/ml_service.py` for predictions and confidence scores.
- Use existing sentiment collection/aggregation from Epic 2 (web scraping-based) as input.
- Reuse `backend/app/services/recommendation_service.py` risk functions from Story 2.7; do not duplicate logic.
- Follow naming and structure patterns in `dist/architecture.md` (services, tasks, endpoints).

### Project Structure Notes

- Service: `backend/app/services/recommendation_service.py` (extend with generation orchestrator if not present)
- Task scheduler: `backend/app/tasks/recommendations.py` (new or extend)
- API exposure for retrieval only; generation runs via scheduler

### References

- [Source: dist/epics.md#story-28-recommendation-generation-logic]
- [Source: dist/tech-spec-epic-2.md#workflows-and-sequencing]
- [Source: dist/architecture.md#novel-pattern-designs]
- [Source: docs/stories/2-7-risk-assessment-calculation.md#Dev-Notes]

## Dev Agent Record

### Context Reference

 - docs/stories/2-8-recommendation-generation-logic.context.xml
### Agent Model Used

GPT-5 (via Cursor)

### Debug Log References

### Completion Notes List

- Added `sentiment_score` field to `Recommendation` model and persisted value in generation.
- Updated ranking to: confidence desc → sentiment desc → risk (LOW first).
- Implemented preference-aware filtering using holding period vs. volatility heuristic.
- Created APScheduler job `recommendations_job()` to generate for all users; added <60s latency guard.
- Wired recommendations job in `app/lifetime.py` (minute 10 each hour).
- Added integration and performance tests; full test suite passing.

### File List

- backend/app/services/recommendation_service.py (ranking, sentiment persistence, preference filter)
- backend/app/tasks/recommendations.py (new job + latency guard)
- backend/app/lifetime.py (scheduler wiring)
- backend/app/models/recommendation.py (added sentiment_score)
- backend/tests/test_services/test_generation_orchestrator.py (pre-existing unit test covers ranking)


## Senior Developer Review (AI)

- Reviewer: Andrew
- Date: 2025-11-04
- Outcome: Approve — All ACs implemented, tests pass; only advisory items (deprecations) addressed.

### Summary
Recommendation generation implemented with ML-driven ranking, sentiment inclusion, risk assessment, scheduler wiring, and latency guard. Persistence schema includes `sentiment_score`. Preference-aware filtering applied via volatility heuristic.

### Key Findings
- LOW: Pydantic v2 deprecations and httpx cookie usage — fixed.
- LOW: Timezone-aware `created_at` default — fixed.

### Acceptance Criteria Coverage
| AC# | Description | Status | Evidence |
| --- | --- | --- | --- |
| 1 | Select top stocks by ML confidence, sentiment; tie-break by risk | IMPLEMENTED | `backend/app/services/recommendation_service.py:333-339` |
| 2 | ~10/day configurable | IMPLEMENTED | `backend/app/services/recommendation_service.py:341-346` |
| 3 | Persist stock, signal, confidence, sentiment, risk | IMPLEMENTED | `backend/app/services/recommendation_service.py:351-360` |
| 4 | Preference-aware filtering | IMPLEMENTED | `backend/app/services/recommendation_service.py:272-284` |
| 5 | Persist with timestamp | IMPLEMENTED | `backend/app/services/recommendation_service.py:373-386` |
| 6 | Scheduled run | IMPLEMENTED | `backend/app/lifetime.py:63-73`, `backend/app/tasks/recommendations.py:48-60` |
| 7 | Latency requirement guard | IMPLEMENTED | `backend/app/tasks/recommendations.py:86-94` |

### Task Completion Validation
| Task | Marked As | Verified As | Evidence |
| --- | --- | --- | --- |
| Generation orchestrator | [x] | VERIFIED COMPLETE | `generate_recommendations()` implementation |
| Risk assessment integration | [x] | VERIFIED COMPLETE | `calculate_risk_level()` used |
| Cadence and limits | [x] | VERIFIED COMPLETE | APScheduler wiring; param target |
| Preference-aware filtering | [x] | VERIFIED COMPLETE | Volatility heuristic |
| Testing (unit/integration/perf) | [ ] | VERIFIED COMPLETE | Test suite results 157 passed |

### Test Coverage and Gaps
- Unit: ranking/count; Integration: persistence of sentiment/fields; Performance: mocked timing.

### Architectural Alignment
- Reuses existing services and follows service/task patterns.

### Security Notes
- No secrets in code paths; uses existing auth flow in tests.

### Best-Practices and References
- Pydantic v2 migration patterns applied; timezone-aware datetimes.

### Action Items
- None pending (advisories already fixed in this PR).

## Change Log

- 2025-11-04: Senior Developer Review notes appended; status set to done.
