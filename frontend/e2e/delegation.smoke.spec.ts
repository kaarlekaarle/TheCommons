import { test, expect } from '@playwright/test';
import { AxeBuilder } from '@axe-core/playwright';

// Extend Window interface for test mocks
declare global {
  interface Window {
    __FLAGS__?: {
      delegationEnabled: boolean;
      delegationBetaAllowlist: string[];
    };
  }
}

test.describe('Delegation System Smoke Test', () => {
  test('Complete delegation flow with accessibility check', async ({ page }) => {
    // Test data - create unique user for each test run
    const testUser = {
      username: `testuser_delegation_${Date.now()}`,
      email: `test_delegation_${Date.now()}@example.com`,
      password: 'TestPassword123!'
    };

    // Track console errors
    const consoleErrors: string[] = [];
    page.on('console', msg => {
      if (msg.type() === 'error') {
        consoleErrors.push(msg.text());
      }
    });

    // Step 1: Register and login
    await test.step('Register and login to the application', async () => {
      await page.goto('/auth');
      await expect(page).toHaveTitle(/The Commons/);
      
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

    // Step 2: Verify header delegation status renders (compact)
    await test.step('Verify header delegation status', async () => {
      // Wait for the delegation status to be visible in header
      const delegationStatus = page.locator('[role="button"][aria-label="Manage delegation"]');
      await expect(delegationStatus).toBeVisible();
      
      // Verify it shows "No delegation" initially
      await expect(delegationStatus).toContainText('No delegation');
      
      // Verify it's in compact mode (small text)
      await expect(delegationStatus).toHaveClass(/text-xs/);
    });

    // Step 3: Open delegation modal via keyboard (Enter)
    await test.step('Open delegation modal via keyboard', async () => {
      const delegationStatus = page.locator('[role="button"][aria-label="Manage delegation"]');
      
      // Focus and press Enter
      await delegationStatus.focus();
      await page.keyboard.press('Enter');
      
      // Verify modal opens
      await expect(page.locator('text=Manage Delegation')).toBeVisible();
      await expect(page.locator('input[placeholder="Search people…"]')).toBeVisible();
    });

    // Step 4: Accessibility check on modal
    await test.step('Run accessibility check on modal', async () => {
      // Run axe-core accessibility check
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      // Assert no serious violations
      expect(accessibilityScanResults.violations).toEqual([]);
      
      // Log any minor issues for awareness
      if (accessibilityScanResults.incomplete.length > 0) {
        console.log('Accessibility incomplete checks:', accessibilityScanResults.incomplete);
      }
    });

    // Step 5: Mock search and create delegation
    await test.step('Search and create delegation', async () => {
      // Mock the search API response
      await page.route('**/api/users/search**', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify([
            { id: 'user-123', name: 'Alice Smith' },
            { id: 'user-456', name: 'Bob Johnson' }
          ])
        });
      });

      // Type in search
      const searchInput = page.locator('input[placeholder="Search people…"]');
      await searchInput.fill('alice');
      await searchInput.press('Enter');
      
      // Wait for search results
      await expect(page.locator('text=Alice Smith')).toBeVisible();
      
      // Select Alice
      await page.click('text=Alice Smith');
      
      // Verify delegate button is enabled
      const delegateButton = page.locator('button:has-text("Delegate")');
      await expect(delegateButton).toBeEnabled();
      
      // Mock the delegation creation API
      await page.route('**/api/delegations/**', async route => {
        if (route.request().method() === 'POST') {
          await route.fulfill({ status: 200 });
        } else {
          await route.continue();
        }
      });
      
      // Create delegation
      await delegateButton.click();
      
      // Wait for modal to close
      await expect(page.locator('text=Manage Delegation')).not.toBeVisible();
    });

    // Step 6: Verify compact summary updates
    await test.step('Verify delegation status updates', async () => {
      // Wait for the status to update
      const delegationStatus = page.locator('[role="button"][aria-label="Manage delegation"]');
      
      // Should show delegation to Alice
      await expect(delegationStatus).toContainText('Delegating to Alice');
      
      // Verify it's still in compact mode
      await expect(delegationStatus).toHaveClass(/text-xs/);
    });

    // Step 7: Navigate to a poll and verify banner
    await test.step('Navigate to poll and verify delegation banner', async () => {
      // Mock delegation data for poll
      await page.route('**/api/delegations/me**', async route => {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            poll: {
              poll_id: 'poll-123',
              to_user_id: 'user-123',
              to_user_name: 'Alice Smith',
              active: true,
              chain: []
            }
          })
        });
      });

      // Navigate to a poll (assuming there's a poll available)
      await page.goto('/proposals');
      
      // Click on first proposal
      const firstProposal = page.locator('a[href*="/proposals/"]').first();
      if (await firstProposal.isVisible()) {
        await firstProposal.click();
        
        // Wait for poll page to load
        await expect(page).toHaveURL(/\/proposals\/[^\/]+$/);
        
        // Verify delegation banner appears
        await expect(page.locator('text=You are delegating this poll to Alice Smith')).toBeVisible();
        await expect(page.locator('text=You can vote yourself or change your delegation.')).toBeVisible();
      }
    });

    // Step 8: Revoke delegation and verify optimistic update
    await test.step('Revoke delegation and verify optimistic update', async () => {
      // Open delegation modal again
      const delegationStatus = page.locator('[role="button"][aria-label="Manage delegation"]');
      await delegationStatus.click();
      
      // Wait for modal to open in revoke mode
      await expect(page.locator('text=Manage Delegation')).toBeVisible();
      await expect(page.locator('text=You currently delegate globally to Alice Smith')).toBeVisible();
      
      // Mock the revocation API
      await page.route('**/api/delegations/**', async route => {
        if (route.request().method() === 'DELETE') {
          await route.fulfill({ status: 200 });
        } else {
          await route.continue();
        }
      });
      
      // Click revoke button
      const revokeButton = page.locator('button:has-text("Revoke delegation")');
      await revokeButton.click();
      
      // Wait for modal to close
      await expect(page.locator('text=Manage Delegation')).not.toBeVisible();
      
      // Verify immediate optimistic update
      await expect(delegationStatus).toContainText('No delegation');
    });

    // Step 9: Verify no console errors
    await test.step('Verify no console errors', async () => {
      expect(consoleErrors).toEqual([]);
    });
  });

  test('Delegation feature flag disabled', async ({ page }) => {
    // Test that delegation UI is hidden when feature flag is disabled
    // This would require setting VITE_DELEGATION_ENABLED=false in the test environment
    
    // Create unique test user
    const testUser = {
      username: `testuser_flag_${Date.now()}`,
      email: `test_flag_${Date.now()}@example.com`,
      password: 'TestPassword123!'
    };
    
    await page.goto('/auth');
    
    // Register user first
    await page.click('text=New here? Create an account');
    await page.fill('input[type="email"]', testUser.email);
    await page.fill('input[placeholder*="username"]', testUser.username);
    await page.fill('input[type="password"]', testUser.password);
    await page.fill('input[placeholder*="Confirm"]', testUser.password);
    await page.click('button[type="submit"]');
    
    // Wait for successful registration and redirect
    await expect(page.locator('text=Account created — you\'re in!')).toBeVisible();
    await expect(page).toHaveURL(/\/proposals/);
    
    // Verify delegation status is not visible in header
    const delegationStatus = page.locator('[role="button"][aria-label="Manage delegation"]');
    await expect(delegationStatus).not.toBeVisible();
  });

  test('Beta allowlist functionality', async ({ page }) => {
    // Test that delegation UI is shown for beta allowlist users
    // Mock the beta allowlist and user email
    
    // Create unique test user
    const testUser = {
      username: `testuser_beta_${Date.now()}`,
      email: `alice_${Date.now()}@example.com`,
      password: 'TestPassword123!'
    };
    
    await page.addInitScript(() => {
      // Set user email in localStorage to simulate logged-in user
      localStorage.setItem('user_email', testUser.email);
      // Mock the flags to simulate beta allowlist check
      window.__FLAGS__ = {
        delegationEnabled: true,
        delegationBetaAllowlist: [testUser.email, 'bob@example.com']
      };
    });

    await page.goto('/auth');
    
    // Register user first
    await page.click('text=New here? Create an account');
    await page.fill('input[type="email"]', testUser.email);
    await page.fill('input[placeholder*="username"]', testUser.username);
    await page.fill('input[type="password"]', testUser.password);
    await page.fill('input[placeholder*="Confirm"]', testUser.password);
    await page.click('button[type="submit"]');
    
    // Wait for successful registration and redirect
    await expect(page.locator('text=Account created — you\'re in!')).toBeVisible();
    await expect(page).toHaveURL(/\/proposals/);
    
    // Verify delegation status is visible for allowlist user
    const delegationStatus = page.locator('[role="button"][aria-label="Manage delegation"]');
    await expect(delegationStatus).toBeVisible();
  });
});
