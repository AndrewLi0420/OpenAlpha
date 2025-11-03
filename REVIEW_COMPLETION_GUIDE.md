# Story 1.3: User Registration - Completion Guide

## Overview
You have 3 remaining tasks before the story can be marked as "review". Here's what to do:

---

## Task 1: Manual Testing (Quick - ~10 minutes)

**What:** Test the registration endpoint manually to verify it works end-to-end.

### Steps:

1. **Start the backend server:**
   ```bash
   cd backend
   # Make sure your .env file is configured
   uvicorn app.main:app --reload
   ```
   Server should start on `http://localhost:8000`

2. **Test registration with curl (in a new terminal):**

   **Test 1: Valid Registration (should return 201)**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "SecurePass123!"
     }'
   ```
   Expected: `201 Created` with JSON: `{"id": "...", "email": "test@example.com", "is_verified": false}`

   **Test 2: Invalid Email (should return 400)**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "notanemail",
       "password": "SecurePass123!"
     }'
   ```
   Expected: `400 Bad Request` with error message

   **Test 3: Weak Password (should return 400)**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test2@example.com",
       "password": "short"
     }'
   ```
   Expected: `400 Bad Request` with password validation error

   **Test 4: Duplicate Email (should return 400)**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "AnotherPass123!"
     }'
   ```
   Expected: `400 Bad Request` with message: "An account with this email already exists"

3. **If all tests pass, mark the task complete:**
   - Open `docs/stories/1-3-user-registration.md`
   - Find line 70: `- [ ] Test registration endpoint with Postman/curl (manual testing pending)`
   - Change to: `- [x] Test registration endpoint with Postman/curl (manual testing pending)`

---

## Task 2: Complete Integration Tests (Medium - ~30-60 minutes)

**What:** Fix the integration tests that need FastAPI Users test setup.

### Current Status:
- Test structure exists in `backend/tests/test_api/test_registration_endpoint.py`
- Need to properly set up FastAPI Users test dependencies and fixtures

### Steps:

1. **Review existing test file:**
   ```bash
   # Look at the test file
   cat backend/tests/test_api/test_registration_endpoint.py
   ```

2. **Fix the test setup to work with FastAPI Users:**
   - The test needs to properly override the FastAPI Users dependencies
   - May need to create test fixtures that work with the actual UserManager
   - Reference: FastAPI Users documentation for testing

3. **Run the tests:**
   ```bash
   cd backend
   pytest tests/test_api/test_registration_endpoint.py -v
   ```

4. **If tests pass, mark tasks complete:**
   - Line 81: `- [ ] Testing: Integration tests...` → `- [x]`
   - Line 82: `- [ ] Test POST /api/v1/auth/register with valid data...` → `- [x]`
   - Line 86: `- [ ] Verify database state...` → `- [x]`

**Note:** If FastAPI Users test setup is too complex, you can mark these as "deferred" or create simplified integration tests that at least verify the endpoint responds correctly.

---

## Task 3: Create Frontend Component Tests (Medium - ~30-60 minutes)

**What:** Write React Testing Library tests for the Register component.

### Steps:

1. **Install testing dependencies (if not already installed):**
   ```bash
   cd frontend
   npm install --save-dev @testing-library/react @testing-library/jest-dom @testing-library/user-event jest-environment-jsdom
   ```

2. **Create test file:**
   ```bash
   touch frontend/src/pages/Register.test.tsx
   ```

3. **Write tests covering:**
   - Component renders form fields
   - Email validation on input change
   - Password validation on input change
   - Form submission with valid data (mocked API)
   - Error handling displays API errors
   - Successful registration redirects to /login

4. **Example test structure:**
   ```typescript
   import { render, screen, fireEvent, waitFor } from '@testing-library/react';
   import { BrowserRouter } from 'react-router-dom';
   import Register from './Register';
   import * as authService from '../services/auth';
   
   jest.mock('../services/auth');
   
   describe('Register Component', () => {
     it('renders form fields', () => {
       render(<BrowserRouter><Register /></BrowserRouter>);
       expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
       expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
     });
     
     // Add more tests...
   });
   ```

5. **Run tests:**
   ```bash
   npm test
   ```

6. **If tests pass, mark tasks complete:**
   - Line 90: `- [ ] Testing: Frontend component tests...` → `- [x]`
   - Mark all 7 subtasks (lines 91-97) as complete

---

## Task 4: Mark Story as Review-Ready

**After completing all 3 tasks above:**

1. **Update story status:**
   - Open `docs/stories/1-3-user-registration.md`
   - Line 3: Change `Status: in-progress` to `Status: review`

2. **Update sprint status:**
   - Open `dist/sprint-status.yaml`
   - Line 42: Change `1-3-user-registration: in-progress` to `1-3-user-registration: review`

3. **Verify all tasks are checked:**
   - Re-read the story file to ensure ALL tasks/subtasks have `[x]`

4. **Then run code-review:**
   ```bash
   # In Cursor, use the dev agent menu:
   *code-review
   ```

---

## Quick Path: Minimum Viable Review

**If you want to get to review faster, you can:**

1. ✅ **Do Task 1** (Manual Testing) - This is quick and proves the endpoint works
2. ⚠️ **Skip Task 2** (Integration Tests) - Mark as "deferred" or "manual testing covers this"
3. ⚠️ **Skip Task 3** (Frontend Tests) - Mark as "manual testing covers this" or "deferred to later story"

Then mark story as "review" and run code-review. The review will identify gaps, but you'll at least have the core functionality tested manually.

---

## Questions or Issues?

- If integration tests are too complex: Consider simpler smoke tests or defer to code-review to identify what's needed
- If frontend tests take too long: Can defer or create minimal smoke tests
- If manual testing fails: Fix the bugs first, then proceed

The goal is to have working code with reasonable test coverage. Perfect test coverage can be iterated on.

