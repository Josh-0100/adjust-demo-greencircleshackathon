import { test, expect } from '@playwright/test';
import { mkdir } from 'node:fs/promises';

test('landing, source catalogue and local status', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByRole('heading', { name: /Small changes/ })).toBeVisible();
  await expect(page.getByText('Local service connected')).toBeVisible();
  await page.screenshot({ path: 'test-results/adjust-home.png', fullPage: true });
  await page.getByRole('button', { name: /Guidance library/ }).click();
  await expect(page.getByRole('status')).toHaveText('32 reviewed passages');
  await page.getByRole('searchbox', { name: 'Search guidance' }).fill('handling');
  const summaries = page.locator('.library-card');
  await expect(summaries.first()).toBeVisible();
  await summaries.first().locator('summary').click();
  await expect(summaries.first().getByRole('link', { name: /Read official guidance/ })).toHaveAttribute('href', /^https:\/\/www.hse.gov.uk\//);
});

test('warehouse to reviewed discussion draft and one-page PDF', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /Lifting and back pain/ }).click();
  await page.getByRole('button', { name: 'Explore possible adjustments' }).click();
  await expect(page.getByRole('heading', { name: 'Options worth a conversation.' })).toBeVisible();
  for (const checkbox of await page.locator('.selection-row input').all()) await checkbox.check();
  await expect(page.getByRole('status')).toHaveText('3 of 3 options selected');
  await page.getByRole('button', { name: 'Prepare the conversation' }).click();
  await expect(page.getByRole('heading', { name: 'Make space for a good conversation.' })).toBeVisible();
  await page.getByRole('button', { name: 'Find further support', exact: true }).click();
  await expect(page.getByText('Confirm availability', { exact: true })).toBeVisible();
  await expect(page.getByText(/original council notice funded the scheme only until March 2026/)).toBeVisible();
  await page.getByRole('button', { name: 'Prepare your plan' }).click();
  await page.getByLabel(/Next steps to record/).fill('Proposed — manager and employee to review the handling task with a competent assessor this week. Confirm the changes to trial together and review after two weeks.');
  await page.getByLabel('I have reviewed the options, sources and limitations.', { exact: false }).check();
  await page.getByRole('button', { name: 'Create discussion draft' }).click();
  await expect(page.getByRole('article', { name: 'Printable adjustment plan' })).toBeVisible();
  await expect(page.locator('.plan-document')).toContainText('Discussion draft');
  await expect(page.locator('.plan-document')).toContainText('9. Professional guidance');
  await page.emulateMedia({ media: 'print' });
  await mkdir('test-results', { recursive: true });
  const pdf = await page.pdf({ path: 'test-results/adjust-plan.pdf', preferCSSPageSize: true, printBackground: true });
  expect(pdf.subarray(0, 4).toString()).toBe('%PDF');
  const pages = pdf.toString('latin1').match(/\/Type\s*\/Page\b/g) || [];
  expect(pages.length).toBe(1);
});

test('vague descriptions ask for workplace details', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /Not sure where to start/ }).click();
  await page.getByRole('button', { name: 'Explore possible adjustments' }).click();
  await expect(page.getByRole('heading', { name: 'A little more context would help.' })).toBeVisible();
  await page.getByLabel(/What is the employee's job role/).fill('Warehouse picker');
  await page.getByLabel(/Which tasks are part of their work/).fill('lifting and picking stock');
  await page.getByRole('button', { name: 'Review with this context' }).click();
  await expect(page.getByRole('heading', { name: 'Options worth a conversation.' })).toBeVisible();
});

test('unsupported specialist situation gets no invented recommendation', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /Specialist evidence needed/ }).click();
  await page.getByRole('button', { name: 'Explore possible adjustments' }).click();
  await expect(page.getByRole('heading', { name: 'This needs specialist guidance.' })).toBeVisible();
  await expect(page.locator('.recommendation-card')).toHaveCount(0);
  await expect(page.getByRole('button', { name: /Your adjustment plan/ })).toBeDisabled();
});

test('emergency stops recommendations and plan creation', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Explore a workplace situation' }).click();
  await page.getByLabel(/Describe the workplace situation/).fill('A warehouse employee is unconscious and not breathing at the workplace right now.');
  await page.getByRole('button', { name: 'Explore possible adjustments' }).click();
  await expect(page.getByRole('alert', { name: 'Urgent safety guidance' })).toContainText('call 999');
  await expect(page.locator('.recommendation-card')).toHaveCount(0);
  await expect(page.getByRole('button', { name: /Your adjustment plan/ })).toBeDisabled();
});

test('keyboard entry, focus, mobile reflow and privacy after reload', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to main content' })).toBeFocused();
  await page.keyboard.press('Enter');
  await page.getByRole('button', { name: 'Explore a workplace situation' }).click();
  await expect(page.getByRole('heading', { name: 'What’s getting in the way?' })).toBeFocused();
  await page.getByLabel(/Describe the workplace situation/).fill('A warehouse picker struggles with repeated lifting.');
  await page.screenshot({ path: 'test-results/adjust-mobile.png', fullPage: true });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  expect(await page.evaluate(() => localStorage.length)).toBe(0);
  expect(await page.evaluate(() => sessionStorage.length)).toBe(0);
  await page.reload();
  await page.getByRole('button', { name: 'Explore a workplace situation' }).click();
  await expect(page.getByLabel(/Describe the workplace situation/)).toBeEmpty();
});

test('multiple barriers show practical options and enforce the three-option draft limit', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: /Several barriers at work/ }).click();
  await page.getByRole('button', { name: 'Explore possible adjustments' }).click();
  await expect(page.getByRole('heading', { name: 'Options worth a conversation.' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Explore access and task arrangements' })).toBeVisible();
  const checkboxes = page.locator('.selection-row input');
  for (let i = 0; i < 3; i++) await checkboxes.nth(i).check();
  await expect(checkboxes.nth(3)).toBeDisabled();
});
