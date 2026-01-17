/**
 * Epic D: Settings & Configuration (P1)
 *
 * Tests the settings dialog and configuration options:
 * - Theme toggle (dark/light)
 * - Settings dialog navigation
 * - Keyboard shortcuts modal
 * - Tab navigation within settings
 */

import { test, expect } from '../fixtures/test-fixtures';

test.describe('Epic D: Settings & Configuration', () => {
  test.describe('Theme Toggle', () => {
    test('displays theme toggle button', async ({ homePage }) => {
      await homePage.goto();
      await expect(homePage.themeToggle).toBeVisible();
    });

    test('toggles from dark to light mode', async ({ page, homePage }) => {
      await homePage.goto();

      // Get initial theme
      const initialTheme = await homePage.getCurrentTheme();

      // Toggle theme
      await homePage.toggleTheme();

      // Wait for theme change
      await page.waitForTimeout(300);

      // Get new theme
      const newTheme = await homePage.getCurrentTheme();

      // Theme should have changed
      expect(newTheme).not.toBe(initialTheme);
    });

    test('toggles back to original mode', async ({ page, homePage }) => {
      await homePage.goto();

      const initialTheme = await homePage.getCurrentTheme();

      // Toggle twice
      await homePage.toggleTheme();
      await page.waitForTimeout(300);
      await homePage.toggleTheme();
      await page.waitForTimeout(300);

      const finalTheme = await homePage.getCurrentTheme();
      expect(finalTheme).toBe(initialTheme);
    });

    test('persists theme across page reload', async ({ page, homePage }) => {
      await homePage.goto();

      // Set to specific theme
      const initialTheme = await homePage.getCurrentTheme();
      await homePage.toggleTheme();
      await page.waitForTimeout(300);

      const changedTheme = await homePage.getCurrentTheme();

      // Reload page
      await page.reload();
      await expect(homePage.themeToggle).toBeVisible();

      // Theme should persist
      const reloadedTheme = await homePage.getCurrentTheme();
      expect(reloadedTheme).toBe(changedTheme);
    });
  });

  test.describe('Settings Dialog', () => {
    test('opens settings dialog', async ({ homePage, settingsDialog }) => {
      await homePage.goto();
      await homePage.openSettings();
      await settingsDialog.waitForOpen();
      await expect(settingsDialog.dialog).toBeVisible();
    });

    test('closes settings with close button', async ({
      homePage,
      settingsDialog,
    }) => {
      await homePage.goto();
      await homePage.openSettings();
      await settingsDialog.waitForOpen();
      await settingsDialog.close();
      await expect(settingsDialog.dialog).toHaveCount(0);
    });

    test('closes settings with Escape key', async ({
      homePage,
      settingsDialog,
    }) => {
      await homePage.goto();
      await homePage.openSettings();
      await settingsDialog.waitForOpen();
      await settingsDialog.closeWithEscape();
      await expect(settingsDialog.dialog).toHaveCount(0);
    });

    test('shows preferences tab by default', async ({
      page,
      homePage,
      settingsDialog,
    }) => {
      await homePage.goto();
      await homePage.openSettings();
      await settingsDialog.waitForOpen();

      // Preferences tab should be active
      const preferencesTab = page.getByTestId('settings-tab-preferences');
      await expect(preferencesTab).toHaveClass(/bg-light-200|bg-dark-200/);
    });

    test('switches to models tab', async ({
      page,
      homePage,
      settingsDialog,
    }) => {
      await homePage.goto();
      await homePage.openSettings();
      await settingsDialog.waitForOpen();

      await settingsDialog.switchToTab('models');

      // Models tab should now be active
      const modelsTab = page.getByTestId('settings-tab-models');
      await expect(modelsTab).toHaveClass(/bg-light-200|bg-dark-200/);
    });

    test('switches to search tab', async ({
      page,
      homePage,
      settingsDialog,
    }) => {
      await homePage.goto();
      await homePage.openSettings();
      await settingsDialog.waitForOpen();

      await settingsDialog.switchToTab('search');

      // Search tab should now be active
      const searchTab = page.getByTestId('settings-tab-search');
      await expect(searchTab).toHaveClass(/bg-light-200|bg-dark-200/);
    });

    test('switches to personalization tab', async ({
      page,
      homePage,
      settingsDialog,
    }) => {
      await homePage.goto();
      await homePage.openSettings();
      await settingsDialog.waitForOpen();

      await settingsDialog.switchToTab('personalization');

      // Personalization tab should now be active
      const personalizationTab = page.getByTestId(
        'settings-tab-personalization',
      );
      await expect(personalizationTab).toHaveClass(/bg-light-200|bg-dark-200/);
    });
  });

  test.describe('Keyboard Shortcuts Modal', () => {
    test('opens keyboard shortcuts with ? key', async ({ page, homePage }) => {
      await homePage.goto();

      // Press ? key to open shortcuts
      await page.keyboard.press('?');

      // Modal should be visible
      const modal = page.getByTestId('keyboard-shortcuts-modal');
      await expect(modal).toBeVisible();
    });

    test('shows shortcut categories', async ({ page, homePage }) => {
      await homePage.goto();
      await page.keyboard.press('?');

      const modal = page.getByTestId('keyboard-shortcuts-modal');
      await expect(modal).toBeVisible();

      // Should show category headers
      await expect(modal.getByText('Navigation')).toBeVisible();
      await expect(modal.getByText('Actions')).toBeVisible();
    });

    test('closes keyboard shortcuts with Escape', async ({
      page,
      homePage,
    }) => {
      await homePage.goto();
      await page.keyboard.press('?');

      const modal = page.getByTestId('keyboard-shortcuts-modal');
      await expect(modal).toBeVisible();

      await page.keyboard.press('Escape');
      await expect(modal).toHaveCount(0);
    });

    test('closes keyboard shortcuts with close button', async ({
      page,
      homePage,
    }) => {
      await homePage.goto();
      await page.keyboard.press('?');

      const modal = page.getByTestId('keyboard-shortcuts-modal');
      await expect(modal).toBeVisible();

      // Click close button (X icon)
      await modal.locator('button').first().click();
      await expect(modal).toHaveCount(0);
    });
  });

  test.describe('Keyboard Navigation', () => {
    test('focuses search with Ctrl+K', async ({ page, homePage }) => {
      await homePage.goto();

      // Click somewhere else first
      await page.click('body');

      // Press Ctrl+K
      await page.keyboard.press('Control+k');

      // Search input should be focused
      const isFocused = await homePage.isSearchFocused();
      expect(isFocused).toBe(true);
    });

    test('theme toggle with T key', async ({ page, homePage }) => {
      await homePage.goto();

      const initialTheme = await homePage.getCurrentTheme();

      // Press T key
      await page.keyboard.press('t');
      await page.waitForTimeout(300);

      const newTheme = await homePage.getCurrentTheme();
      expect(newTheme).not.toBe(initialTheme);
    });
  });
});
