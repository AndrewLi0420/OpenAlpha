# Manual Testing Guide: Tier Enforcement (Story 1.6)

This guide provides step-by-step instructions for manually testing tier enforcement functionality using browser DevTools to verify API calls and database queries.

## Prerequisites

- Backend server running on `http://localhost:8000`
- Frontend server running on `http://localhost:5173`
- Browser with DevTools (Chrome/Edge/Firefox)
- Database access (optional, for direct verification)

## Test Scenarios

### Scenario 1: Free Tier User - Tier Status Display

**Objective:** Verify free tier user sees correct tier status on Profile page.

**Steps:**

1. **Register a new user:**
   - Navigate to `http://localhost:5173/register`
   - Enter email: `test-free@example.com`
   - Enter password: `TestPass123!`
   - Submit registration

2. **Login:**
   - Navigate to `http://localhost:5173/login`
   - Login with credentials from step 1
   - Should redirect to dashboard

3. **Open DevTools:**
   - Press `F12` or right-click → Inspect
   - Go to **Network** tab
   - Filter by `Fetch/XHR`

4. **Navigate to Profile:**
   - Click Profile link or navigate to `/profile`
   - Observe network requests

5. **Verify API Calls:**
   - **Request:** `GET /api/v1/users/me/tier-status`
   - **Status:** `200 OK`
   - **Response Body:** Should contain:
     ```json
     {
       "tier": "free",
       "stock_count": 0,
       "stock_limit": 5,
       "can_add_more": true
     }
     ```

6. **Verify UI Display:**
   - Profile page should show tier badge
   - Badge text: "Free Tier - Tracking 0/5 stocks"
   - Badge should have blue styling (`bg-blue-900`)

### Scenario 2: Free Tier User - Track Stocks Up to Limit

**Objective:** Verify tier status updates as stocks are tracked (simulated via API/database).

**Note:** Since stock tracking UI is in Epic 3, we'll simulate by directly adding tracking records.

**Steps:**

1. **Check initial tier status:**
   - Login as free tier user
   - Open DevTools → Network tab
   - Navigate to Profile page
   - Verify `GET /api/v1/users/me/tier-status` shows `stock_count: 0`

2. **Add stock tracking (via API or database):**
   - **Option A (API - if endpoint exists):** Use Postman/curl to add stock tracking
   - **Option B (Database):** Direct SQL insert into `user_stock_tracking` table:
     ```sql
     INSERT INTO user_stock_tracking (id, user_id, stock_id, created_at)
     VALUES (gen_random_uuid(), '<user_id>', '<stock_id>', NOW());
     ```
   - Add 3 tracking records (should have 3 stocks)

3. **Verify tier status updates:**
   - Refresh Profile page
   - Check network request: `GET /api/v1/users/me/tier-status`
   - Verify response: `stock_count: 3`, `can_add_more: true`

4. **Add 2 more stocks (total 5):**
   - Add 2 more tracking records
   - Refresh Profile page
   - Verify: `stock_count: 5`, `can_add_more: false`

5. **Verify limit reached:**
   - Profile should still show "Free Tier - Tracking 5/5 stocks"
   - Badge indicates limit reached

### Scenario 3: Premium User - Unlimited Access

**Objective:** Verify premium user bypasses tier limits.

**Steps:**

1. **Upgrade user to premium:**
   - **Option A (Database):** Direct SQL update:
     ```sql
     UPDATE users SET tier = 'premium' WHERE email = 'test-premium@example.com';
     ```
   - **Option B (Backend admin endpoint):** If available, use API to upgrade user

2. **Login as premium user:**
   - Navigate to `/login`
   - Login with premium user credentials

3. **Verify tier status:**
   - Navigate to Profile page
   - Open DevTools → Network tab
   - Check `GET /api/v1/users/me/tier-status` request
   - **Response should be:**
     ```json
     {
       "tier": "premium",
       "stock_count": <any_number>,
       "stock_limit": null,
       "can_add_more": true
     }
     ```

4. **Verify UI display:**
   - Profile should show: "Premium - Unlimited"
   - Badge should have green styling (`bg-green-900`)
   - Should show ✨ emoji indicator

5. **Verify unlimited tracking:**
   - Add 10+ stock tracking records
   - Refresh Profile page
   - Verify `can_add_more: true` remains true
   - Tier status shows unlimited access

### Scenario 4: Database Query Verification

**Objective:** Verify tier enforcement queries database correctly.

**Steps:**

1. **Check user tier in database:**
   ```sql
   SELECT id, email, tier FROM users WHERE email = 'test-free@example.com';
   ```
   - Verify `tier` column is `'free'` (not `'premium'`)

2. **Check stock count query:**
   ```sql
   SELECT COUNT(*) as stock_count
   FROM user_stock_tracking
   WHERE user_id = '<user_id>';
   ```
   - Compare with API response `stock_count` field
   - Should match exactly

3. **Verify tier limit calculation:**
   - For free tier user with 3 stocks:
     - Query should return `stock_count: 3`
     - API should return `can_add_more: true` (3 < 5)
   - For free tier user with 5 stocks:
     - Query should return `stock_count: 5`
     - API should return `can_add_more: false` (5 >= 5)

### Scenario 5: API Error Handling

**Objective:** Verify API handles edge cases correctly.

**Steps:**

1. **Unauthenticated request:**
   - Open new incognito/private window
   - Navigate to `http://localhost:8000/api/v1/users/me/tier-status`
   - **Expected:** `401 Unauthorized`

2. **Check CORS headers:**
   - In DevTools → Network tab
   - Select `tier-status` request
   - Check **Headers** → **Response Headers**
   - Should include `Access-Control-Allow-Origin` header

3. **Verify error response format:**
   - Make unauthenticated request
   - Response should be JSON with error details

## DevTools Inspection Checklist

### Network Tab

- [ ] `GET /api/v1/users/me` includes `tier` field in response
- [ ] `GET /api/v1/users/me/tier-status` returns correct tier status
- [ ] Request includes authentication cookie (`fastapiusersauth`)
- [ ] Response includes CORS headers
- [ ] Request/response timing is reasonable (< 500ms)

### Application Tab (Storage)

- [ ] Authentication cookie is set (HTTP-only, not visible in JavaScript)
- [ ] Cookie has correct domain (`localhost`)
- [ ] Cookie has secure flag if using HTTPS

### Console Tab

- [ ] No JavaScript errors related to tier status
- [ ] React Query cache working (no unnecessary refetches)
- [ ] Tier status updates reflected in UI

### Performance Tab (Optional)

- [ ] Tier status API call completes in < 200ms
- [ ] No unnecessary duplicate requests
- [ ] React Query caching working (check refetch behavior)

## Database Verification Queries

```sql
-- Check user tier
SELECT id, email, tier, created_at
FROM users
WHERE email = 'test-user@example.com';

-- Check stock tracking count
SELECT user_id, COUNT(*) as tracked_stocks
FROM user_stock_tracking
WHERE user_id = '<user_id>'
GROUP BY user_id;

-- Verify tier enforcement logic
SELECT 
    u.id,
    u.email,
    u.tier,
    COUNT(ust.id) as stock_count,
    CASE 
        WHEN u.tier = 'premium' THEN NULL
        ELSE 5
    END as stock_limit,
    CASE
        WHEN u.tier = 'premium' THEN true
        WHEN COUNT(ust.id) >= 5 THEN false
        ELSE true
    END as can_add_more
FROM users u
LEFT JOIN user_stock_tracking ust ON u.id = ust.user_id
WHERE u.email = 'test-user@example.com'
GROUP BY u.id, u.email, u.tier;
```

## Expected Results Summary

| Test | Free Tier (0 stocks) | Free Tier (5 stocks) | Premium (any) |
|------|---------------------|---------------------|---------------|
| `tier` | `"free"` | `"free"` | `"premium"` |
| `stock_count` | `0` | `5` | `any_number` |
| `stock_limit` | `5` | `5` | `null` |
| `can_add_more` | `true` | `false` | `true` |
| UI Badge | "Free Tier - Tracking 0/5 stocks" | "Free Tier - Tracking 5/5 stocks" | "Premium - Unlimited ✨" |
| Badge Color | Blue | Blue | Green |

## Notes

- Stock tracking UI endpoints will be implemented in Epic 3
- Current tests verify infrastructure (tier status API, Profile display)
- Manual testing can simulate stock tracking via direct database inserts or API calls
- E2E tests in `frontend/tests/e2e/tier-enforcement.spec.ts` cover automated scenarios
- Integration tests in `backend/tests/test_api/test_tier_enforcement_flow.py` cover API flow

