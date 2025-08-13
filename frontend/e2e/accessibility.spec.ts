import { test, expect } from '@playwright/test';
import { AxeBuilder } from '@axe-core/playwright';

test.describe('Delegation Accessibility Compliance', () => {
  test('Delegation components meet WCAG AA standards', async ({ page }) => {
    // Test data
    const testUser = {
      username: `testuser_accessibility_${Date.now()}`,
      email: `test_accessibility_${Date.now()}@example.com`,
      password: 'TestPassword123!'
    };

    // Register and login
    await test.step('Setup test user', async () => {
      await page.goto('/auth');
      await page.click('text=New here? Create an account');
      await page.fill('input[type="email"]', testUser.email);
      await page.fill('input[placeholder*="username"]', testUser.username);
      await page.fill('input[type="password"]', testUser.password);
      await page.fill('input[placeholder*="Confirm"]', testUser.password);
      await page.click('button[type="submit"]');
      
      await expect(page.locator('text=Account created — you\'re in!')).toBeVisible();
      await expect(page).toHaveURL(/\/proposals/);
    });

    // Test 1: Delegation status in header
    await test.step('Check delegation status accessibility', async () => {
      const delegationStatus = page.locator('[role="button"][aria-label="Manage delegation"]');
      await expect(delegationStatus).toBeVisible();

      // Run axe-core on the delegation status component
      const accessibilityScanResults = await new AxeBuilder({ page })
        .include('[role="button"][aria-label="Manage delegation"]')
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      // Fail if there are any violations
      expect(accessibilityScanResults.violations).toEqual([]);
    });

    // Test 2: Delegation modal
    await test.step('Check delegation modal accessibility', async () => {
      // Open delegation modal
      const delegationStatus = page.locator('[role="button"][aria-label="Manage delegation"]');
      await delegationStatus.click();
      
      // Wait for modal to open
      await expect(page.locator('text=Manage Delegation')).toBeVisible();
      await expect(page.locator('input[placeholder="Search people…"]')).toBeVisible();

      // Run axe-core on the modal
      const accessibilityScanResults = await new AxeBuilder({ page })
        .include('[role="dialog"]')
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      // Fail if there are any violations
      expect(accessibilityScanResults.violations).toEqual([]);

      // Close modal
      await page.keyboard.press('Escape');
      await expect(page.locator('text=Manage Delegation')).not.toBeVisible();
    });

    // Test 3: Poll page with delegation banner
    await test.step('Check poll delegation banner accessibility', async () => {
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

      // Navigate to a poll
      await page.goto('/proposals');
      const firstProposal = page.locator('a[href*="/proposals/"]').first();
      
      if (await firstProposal.isVisible()) {
        await firstProposal.click();
        await expect(page).toHaveURL(/\/proposals\/[^/]+$/);

        // Check for delegation banner
        const delegationBanner = page.locator('text=You are delegating this poll to Alice Smith');
        if (await delegationBanner.isVisible()) {
          // Run axe-core on the delegation banner area
          const accessibilityScanResults = await new AxeBuilder({ page })
            .include('text=You are delegating this poll to Alice Smith')
            .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
            .analyze();

          // Fail if there are any violations
          expect(accessibilityScanResults.violations).toEqual([]);
        }
      }
    });

    // Test 4: Overall page accessibility with delegation components
    await test.step('Check overall page accessibility with delegation', async () => {
      await page.goto('/proposals');
      
      // Run axe-core on the entire page
      const accessibilityScanResults = await new AxeBuilder({ page })
        .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
        .analyze();

      // Fail if there are any violations
      expect(accessibilityScanResults.violations).toEqual([]);
    });
  });

  test('Delegation components have proper ARIA attributes', async ({ page }) => {
    // Test data
    const testUser = {
      username: `testuser_aria_${Date.now()}`,
      email: `test_aria_${Date.now()}@example.com`,
      password: 'TestPassword123!'
    };

    // Register and login
    await test.step('Setup test user', async () => {
      await page.goto('/auth');
      await page.click('text=New here? Create an account');
      await page.fill('input[type="email"]', testUser.email);
      await page.fill('input[placeholder*="username"]', testUser.username);
      await page.fill('input[type="password"]', testUser.password);
      await page.fill('input[placeholder*="Confirm"]', testUser.password);
      await page.click('button[type="submit"]');
      
      await expect(page.locator('text=Account created — you\'re in!')).toBeVisible();
      await expect(page).toHaveURL(/\/proposals/);
    });

    // Check delegation status ARIA attributes
    await test.step('Verify delegation status ARIA attributes', async () => {
      const delegationStatus = page.locator('[role="button"][aria-label="Manage delegation"]');
      await expect(delegationStatus).toBeVisible();
      
      // Check for proper ARIA attributes
      await expect(delegationStatus).toHaveAttribute('role', 'button');
      await expect(delegationStatus).toHaveAttribute('aria-label', 'Manage delegation');
      await expect(delegationStatus).toHaveAttribute('tabindex', '0');
    });

    // Check delegation modal ARIA attributes
    await test.step('Verify delegation modal ARIA attributes', async () => {
      // Open delegation modal
      const delegationStatus = page.locator('[role="button"][aria-label="Manage delegation"]');
      await delegationStatus.click();
      
      // Wait for modal to open
      await expect(page.locator('text=Manage Delegation')).toBeVisible();
      
      // Check modal ARIA attributes
      const modal = page.locator('[role="dialog"]').first();
      if (await modal.isVisible()) {
        await expect(modal).toHaveAttribute('role', 'dialog');
        await expect(modal).toHaveAttribute('aria-modal', 'true');
      }
      
      // Close modal
      await page.keyboard.press('Escape');
    });
  });
});
