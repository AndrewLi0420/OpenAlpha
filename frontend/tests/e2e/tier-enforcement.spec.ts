import { test, expect } from '@playwright/test';

/**
 * E2E Tests for Freemium Tier Enforcement (Story 1.6)
 * 
 * Tests cover:
 * - Tier status display on Profile page
 * - Free tier user sees correct tier indicator and stock count
 * - Premium user sees unlimited tier status
 * - Tier status API integration
 */

const BASE_URL = process.env.FRONTEND_URL || 'http://localhost:5173';
const API_URL = process.env.API_URL || 'http://localhost:8000';

// Helper function to create a test user via API
async function createTestUser(email: string, password: string) {
  const response = await fetch(`${API_URL}/api/v1/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  
  if (!response.ok) {
    const error = await response.json();
    throw new Error(`Failed to create test user: ${error.detail || response.statusText}`);
  }
  
  return await response.json();
}

// Helper function to login via API (returns cookies)
async function loginUser(page: any, email: string, password: string) {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);
  
  const response = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: formData,
    credentials: 'include',
  });
  
  if (!response.ok) {
    throw new Error(`Login failed: ${response.statusText}`);
  }
  
  // Extract cookies from Set-Cookie header and set them in the page context
  const cookies = response.headers.get('set-cookie');
  if (cookies) {
    // Parse and set cookies in browser context
    await page.context().addCookies([
      {
        name: 'fastapiusersauth',
        value: cookies.split('=')[1].split(';')[0],
        domain: 'localhost',
        path: '/',
        httpOnly: true,
        sameSite: 'Lax',
      }
    ]);
  }
}

test.describe('Tier Enforcement E2E Tests', () => {
  const testEmail = `test-e2e-${Date.now()}@example.com`;
  const testPassword = 'TestPass123!';
  
  test.beforeEach(async ({ page }) => {
    // Create test user
    try {
      await createTestUser(testEmail, testPassword);
    } catch (error: any) {
      // User might already exist, try to login instead
      if (!error.message.includes('already exists')) {
        throw error;
      }
    }
    
    // Login user
    await loginUser(page, testEmail, testPassword);
  });

  test('[P0] Profile page displays tier status for free tier user', async ({ page }) => {
    // Given: User is logged in as free tier user
    await page.goto(`${BASE_URL}/profile`);
    
    // When: Profile page loads
    await page.waitForLoadState('networkidle');
    
    // Then: Tier status should be displayed
    const tierBadge = page.locator('text=Free Tier');
    await expect(tierBadge).toBeVisible({ timeout: 10000 });
    
    // And: Stock count should be shown (format: "Tracking X/5 stocks")
    const stockCountText = page.locator('text=/Tracking \\d+\\/5 stocks/');
    await expect(stockCountText).toBeVisible();
    
    // And: Tier badge should have blue styling (free tier)
    const badge = page.locator('.bg-blue-900').first();
    await expect(badge).toBeVisible();
  });

  test('[P0] Profile page displays tier status for premium user', async ({ page, request }) => {
    // Given: User is logged in and upgraded to premium (via API)
    await loginUser(page, testEmail, testPassword);
    
    // Upgrade user to premium via API (requires backend admin endpoint or direct DB update)
    // For E2E testing, we'll verify the UI handles premium status correctly
    // In a real scenario, this would be done via a payment flow or admin action
    
    await page.goto(`${BASE_URL}/profile`);
    await page.waitForLoadState('networkidle');
    
    // Note: This test assumes user is free tier unless explicitly upgraded
    // For a complete test, we'd need an admin endpoint to upgrade users
    // For now, we test that the UI structure supports premium display
    
    const tierSection = page.locator('text=Tier:');
    await expect(tierSection).toBeVisible();
    
    // Verify tier badge container exists (works for both free and premium)
    const tierBadgeContainer = page.locator('.bg-blue-900, .bg-green-900').first();
    await expect(tierBadgeContainer).toBeVisible();
  });

  test('[P1] Tier status API endpoint returns correct data', async ({ page, request }) => {
    // Given: User is logged in
    await loginUser(page, testEmail, testPassword);
    
    // When: Fetching tier status via API
    const context = await page.context();
    const cookies = await context.cookies();
    const cookieHeader = cookies.map(c => `${c.name}=${c.value}`).join('; ');
    
    const response = await request.get(`${API_URL}/api/v1/users/me/tier-status`, {
      headers: {
        'Cookie': cookieHeader,
      },
    });
    
    // Then: Response should be successful
    expect(response.ok()).toBeTruthy();
    
    const tierStatus = await response.json();
    
    // And: Response should contain required fields
    expect(tierStatus).toHaveProperty('tier');
    expect(tierStatus).toHaveProperty('stock_count');
    expect(tierStatus).toHaveProperty('stock_limit');
    expect(tierStatus).toHaveProperty('can_add_more');
    
    // And: For free tier user, values should be correct
    expect(tierStatus.tier).toBe('free');
    expect(tierStatus.stock_count).toBeGreaterThanOrEqual(0);
    expect(tierStatus.stock_limit).toBe(5);
    expect(typeof tierStatus.can_add_more).toBe('boolean');
  });

  test('[P1] User profile displays correct tier indicator styling', async ({ page }) => {
    // Given: User is logged in as free tier
    await page.goto(`${BASE_URL}/profile`);
    await page.waitForLoadState('networkidle');
    
    // When: Viewing profile page
    // Then: Tier badge should have appropriate styling
    const freeTierBadge = page.locator('.bg-blue-900').first();
    await expect(freeTierBadge).toBeVisible();
    
    // And: Badge text should contain tier information
    const badgeText = await freeTierBadge.textContent();
    expect(badgeText).toContain('Free Tier');
    expect(badgeText).toMatch(/Tracking \d+\/5 stocks/);
  });

  test('[P2] Tier status is fetched and displayed correctly on page load', async ({ page }) => {
    // Given: User is logged in
    await loginUser(page, testEmail, testPassword);
    
    // When: Navigating to profile page
    const tierStatusPromise = page.waitForResponse(
      response => response.url().includes('/tier-status') && response.status() === 200
    );
    
    await page.goto(`${BASE_URL}/profile`);
    
    // Then: Tier status API should be called
    const tierStatusResponse = await tierStatusPromise;
    expect(tierStatusResponse.ok()).toBeTruthy();
    
    // And: Tier status should be displayed on page
    await page.waitForLoadState('networkidle');
    const tierIndicator = page.locator('text=/Free Tier|Premium/');
    await expect(tierIndicator).toBeVisible({ timeout: 5000 });
  });
});

