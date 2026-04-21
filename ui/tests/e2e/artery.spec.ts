import { test, expect } from '@playwright/test';

test('Artery page loads and accepts commands', async ({ page }) => {
  await page.goto('/artery');
  await expect(page.locator('header')).toContainText('Artery');

  const input = page.locator('input[placeholder="ENTER COMMAND..."]');
  await input.fill('status');
  await page.keyboard.press('Enter');

  await expect(page.locator('.font-artery')).toBeVisible();
});
