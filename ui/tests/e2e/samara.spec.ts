import { test, expect } from '@playwright/test';

test('Samara page loads and sends message', async ({ page }) => {
  await page.goto('/samara');
  await expect(page.locator('h2')).toContainText('Samara');

  const input = page.locator('input[placeholder="Type your message..."]');
  await input.fill('Hello');
  await page.click('button[aria-label="Send"]');

  await expect(page.locator('.chat-bubble-samara')).toBeVisible();
});
