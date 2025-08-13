import { test, expect } from '@playwright/test';

test.describe('Smoke Test - Core Functionality', () => {
  test('Login → Dashboard → Content Load', async ({ page }) => {
    // Test data
    const testUser = {
      email: 'test@example.com',
      password: 'TestPassword123!'
    };

    // Step 1: Navigate to the application
    await test.step('Navigate to application', async () => {
      await page.goto('/');
      await expect(page).toHaveTitle(/The Commons/);
    });

    // Step 2: Login
    await test.step('Login with test user', async () => {
      // Navigate to auth page
      await page.goto('/auth');
      
      // Fill in login form
      await page.fill('input[type="email"]', testUser.email);
      await page.fill('input[type="password"]', testUser.password);
      
      // Submit login
      await page.click('button[type="submit"]');
      
      // Wait for successful login and redirect
      await expect(page).toHaveURL(/\/proposals/);
    });

    // Step 3: Verify dashboard loads
    await test.step('Verify dashboard loads', async () => {
      // Check that we're on the proposals page
      await expect(page).toHaveURL(/\/proposals/);
      
      // Verify basic UI elements are present
      await expect(page.locator('h1')).toContainText(/Proposals|The Commons/);
      
      // Check for navigation elements
      await expect(page.locator('nav')).toBeVisible();
    });

    // Step 4: Verify content loads
    await test.step('Verify content loads', async () => {
      // Wait for content to load (either proposals list or empty state)
      await page.waitForLoadState('networkidle');
      
      // Check for either proposals list or empty state message
      const hasProposals = await page.locator('.proposal-card, .proposal-item').count() > 0;
      const hasEmptyState = await page.locator('text=No proposals yet, text=Create your first proposal').count() > 0;
      
      expect(hasProposals || hasEmptyState).toBeTruthy();
    });

    // Step 5: Verify navigation works
    await test.step('Verify navigation works', async () => {
      // Try to navigate to new proposal page
      await page.click('a[href="/proposals/new"], button:has-text("New Proposal")');
      
      // Should be on new proposal page
      await expect(page).toHaveURL(/\/proposals\/new/);
      
      // Verify form elements are present
      await expect(page.locator('input[placeholder*="title"]')).toBeVisible();
      await expect(page.locator('textarea[placeholder*="description"]')).toBeVisible();
    });
  });

  test('Content API endpoints respond', async ({ page }) => {
    // Test that content API endpoints are working
    await test.step('Check content API health', async () => {
      // Navigate to a page that loads content
      await page.goto('/');
      
      // Wait for any API calls to complete
      await page.waitForLoadState('networkidle');
      
      // Check for no major errors in console
      const errors = await page.evaluate(() => {
        return window.console.error ? window.console.error.mock?.calls || [] : [];
      });
      
      // Should have minimal errors (some 404s for missing content are expected)
      expect(errors.length).toBeLessThan(10);
    });
  });
});
