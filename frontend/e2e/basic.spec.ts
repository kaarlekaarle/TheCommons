import { test, expect } from '@playwright/test';

test.describe('Basic User Flow', () => {
  test('Complete user journey - register, create proposal, vote, comment', async ({ page }) => {
    // Test data
    const testUser = {
      username: `testuser_${Date.now()}`,
      email: `test_${Date.now()}@example.com`,
      password: 'TestPassword123!'
    };
    
    const testProposal = {
      title: 'Test Proposal for E2E Testing',
      description: 'This is a test proposal created during E2E testing to verify the complete user flow.',
      options: ['Option A', 'Option B', 'Option C']
    };

    // Step 1: Navigate to the application
    await page.goto('/');
    await expect(page).toHaveTitle(/The Commons/);
    
    // Step 2: Register a new user
    await test.step('Register new user', async () => {
      // Navigate to auth page
      await page.goto('/auth');
      
      // Click on "New here? Create an account"
      await page.click('text=New here? Create an account');
      
      // Fill in registration form
      await page.fill('input[type="email"]', testUser.email);
      await page.fill('input[placeholder*="username"]', testUser.username);
      await page.fill('input[type="password"]', testUser.password);
      await page.fill('input[placeholder*="Confirm"]', testUser.password);
      
      // Submit registration
      await page.click('button[type="submit"]');
      
      // Wait for successful registration and automatic login
      await expect(page.locator('text=Account created — you\'re in!')).toBeVisible();
      
      // Wait for redirect to proposals page
      await expect(page).toHaveURL(/\/proposals/);
    });

    // Step 3: Create a new proposal
    await test.step('Create new proposal', async () => {
      // Navigate to create proposal page
      await page.click('a[href="/proposals/new"]');
      await expect(page).toHaveURL(/\/proposals\/new/);
      
      // Fill in proposal form
      await page.fill('input[placeholder*="title"]', testProposal.title);
      await page.fill('textarea[placeholder*="description"]', testProposal.description);
      
      // Add options
      for (let i = 0; i < testProposal.options.length; i++) {
        await page.fill(`input[placeholder*="Option ${i + 1}"]`, testProposal.options[i]);
      }
      
      // Submit proposal
      await page.click('button[type="submit"]');
      
      // Wait for successful creation and redirect
              await expect(page).toHaveURL(/\/proposals\/[^/]+$/);
      
      // Verify proposal details are displayed
      await expect(page.locator(`text=${testProposal.title}`)).toBeVisible();
      await expect(page.locator(`text=${testProposal.description}`)).toBeVisible();
      
      for (const option of testProposal.options) {
        await expect(page.locator(`text=${option}`)).toBeVisible();
      }
    });

    // Step 4: Vote on the proposal
    await test.step('Vote on proposal', async () => {
      // Click on the first option to vote
      const firstOption = page.locator('.vote-option').first();
      await firstOption.click();
      
      // Wait for vote to be recorded
      await expect(firstOption.locator('.voted')).toBeVisible();
      
      // Verify vote count is updated
      await expect(page.locator('.vote-count')).toContainText('1');
    });

    // Step 5: Add a comment
    await test.step('Add comment to proposal', async () => {
      // Scroll to comment section
      await page.locator('.comments-section').scrollIntoViewIfNeeded();
      
      // Fill in comment
      const commentText = 'This is a test comment from E2E testing!';
      await page.fill('textarea[placeholder*="comment"]', commentText);
      
      // Submit comment
      await page.click('button:has-text("Post Comment")');
      
      // Wait for comment to appear
      await expect(page.locator(`text=${commentText}`)).toBeVisible();
      await expect(page.locator(`text=${testUser.username}`)).toBeVisible();
    });

    // Step 6: Verify proposal results
    await test.step('Verify proposal results', async () => {
      // Check that the proposal shows in the list
      await page.goto('/proposals');
      await expect(page.locator(`text=${testProposal.title}`)).toBeVisible();
      
      // Click on the proposal to view details
      await page.click(`text=${testProposal.title}`);
      
      // Verify vote results are displayed
      await expect(page.locator('.vote-results')).toBeVisible();
      await expect(page.locator('.comment')).toBeVisible();
    });

    // Step 7: Test logout
    await test.step('Logout and verify', async () => {
      // Click logout (assuming there's a logout button in the layout)
      await page.click('button:has-text("Logout")');
      
      // Verify we're back to the login page
      await expect(page).toHaveURL('/');
      await expect(page.locator('text=Login')).toBeVisible();
    });
  });

  test('Login with existing user', async ({ page }) => {
    // Test data for existing user
    const existingUser = {
      username: 'testuser_existing',
      password: 'TestPassword123!'
    };

    await page.goto('/auth');
    
    // Fill in login form
    await page.fill('input[placeholder*="username"]', existingUser.username);
    await page.fill('input[type="password"]', existingUser.password);
    
    // Submit login
    await page.click('button[type="submit"]');
    
    // Wait for successful login
    await expect(page).toHaveURL(/\/proposals/);
    await expect(page.locator(`text=${existingUser.username}`)).toBeVisible();
  });

  test('View activity feed', async ({ page }) => {
    // Login first
    await page.goto('/auth');
    await page.fill('input[placeholder*="username"]', 'testuser_existing');
    await page.fill('input[type="password"]', 'TestPassword123!');
    await page.click('button[type="submit"]');
    
    // Navigate to activity feed
    await page.click('a[href="/activity"]');
    await expect(page).toHaveURL(/\/activity/);
    
    // Verify activity feed is displayed
    await expect(page.locator('.activity-feed')).toBeVisible();
  });

  test('Search and filter proposals', async ({ page }) => {
    // Login first
    await page.goto('/auth');
    await page.fill('input[placeholder*="username"]', 'testuser_existing');
    await page.fill('input[type="password"]', 'TestPassword123!');
    await page.click('button[type="submit"]');
    
    // Navigate to proposals
    await page.goto('/proposals');
    
    // Test search functionality (if available)
    const searchInput = page.locator('input[placeholder*="search"]');
    if (await searchInput.isVisible()) {
      await searchInput.fill('Test Proposal');
      await page.keyboard.press('Enter');
      
      // Verify search results
      await expect(page.locator('text=Test Proposal')).toBeVisible();
    }
  });
});

test.describe('Error Handling', () => {
  test('Invalid login credentials', async ({ page }) => {
    await page.goto('/auth');
    
    // Try to login with invalid credentials
    await page.fill('input[placeholder*="username"]', 'nonexistent_user');
    await page.fill('input[type="password"]', 'wrong_password');
    await page.click('button[type="submit"]');
    
    // Verify error message is displayed
    await expect(page.locator('.error-message')).toBeVisible();
  });

  test('Form validation', async ({ page }) => {
    await page.goto('/auth');
    
    // Click register without filling required fields
    await page.click('text=New here? Create an account');
    await page.click('button[type="submit"]');
    
    // Verify validation errors are displayed
    await expect(page.locator('.error-message')).toBeVisible();
  });
});

test.describe('Responsive Design', () => {
  test('Mobile viewport', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    await page.goto('/auth');
    
    // Verify the page is usable on mobile
    await expect(page.locator('input[placeholder*="username"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });
});
