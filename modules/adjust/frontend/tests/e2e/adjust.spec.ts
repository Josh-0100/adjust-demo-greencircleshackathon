import { test, expect, type Page, type TestInfo } from '@playwright/test';

const employeeIds = ['later-start', 'breaks', 'standing', 'lifting', 'quiet', 'written', 'workload', 'flexibility', 'appointments', 'discuss-needs'];
const employerIds = ['cover', 'core-tasks', 'fixed-hours', 'limited-budget', 'small-space', 'tried-flexible', 'discuss-practicalities'];
const privateEmployee = 'Private fictional marker violet-cupboard-384. My condition is fibromyalgia, and my medical dosage is fictional.';
const privateEmployer = 'Private fictional marker amber-drawer-792. Our internal contract notes are confidential.';
type Handoff = {
  v: number; starter: string; review_date?: string;
  employee?: { reviewed: boolean; need_ids: string[]; support_kind: string };
  employer?: { reviewed: boolean; need_ids: string[]; business_size: string };
};

async function start(page: Page, role: 'employee' | 'employer') {
  await page.goto('/');
  await page.getByRole('button', { name: role === 'employee' ? /I’m an employee/ : /I’m an employer/ }).click();
  await expect(page.getByRole('heading', { name: role === 'employee' ? 'What’s getting in the way?' : 'Tell us about your workplace.' })).toBeVisible();
}

async function example(page: Page, role: 'employee' | 'employer', carer = false) {
  await page.getByRole('button', { name: carer ? 'Unpaid caring' : 'Work and energy', exact: true }).click();
  const description = page.locator('#private-description');
  await description.fill(`${await description.inputValue()} ${role === 'employee' ? privateEmployee : privateEmployer}`);
  if (role === 'employer') {
    await expect(page.getByLabel(/^Business size/)).toHaveValue('under_50');
    await expect(page.getByLabel('What does the role involve, and what can’t change?')).not.toBeEmpty();
    await expect(page.getByLabel('What’s practical for the business?')).not.toBeEmpty();
    await expect(page.getByLabel('Anything already tried?')).not.toBeEmpty();
  }
}

async function review(page: Page) {
  await page.getByRole('button', { name: 'Review what will be shared' }).click();
  await expect(page.getByRole('heading', { name: 'Your words. Your choice.' })).toBeVisible();
  await expect(page.locator('#private-description')).toHaveCount(0);
}

async function confirm(page: Page, complete = false) {
  await page.getByRole('checkbox', { name: /I’ve reviewed these items/ }).check();
  await page.getByRole('button', { name: complete ? 'Create our combined plan' : 'Create invitation link', exact: true }).click();
  if (complete) await expect(page.getByRole('article', { name: 'Printable combined plan' })).toBeVisible();
  else await expect(page.getByRole('heading', { name: 'Your side is ready.' })).toBeVisible();
  return await page.locator('#case-link').inputValue();
}

function decoded(link: string): Handoff {
  const url = new URL(link);
  expect(url.search).toBe('');
  expect(url.hash).toMatch(/^#case=/);
  const value = JSON.parse(Buffer.from(url.hash.slice(6), 'base64').toString('utf8')) as Handoff;
  expect(Object.keys(value)).toEqual(expect.arrayContaining(['starter', 'v']));
  expect(Object.keys(value).every(key => ['v', 'starter', 'employee', 'employer', 'review_date'].includes(key))).toBe(true);
  expect(value.v).toBe(1);
  if (value.employee) {
    expect(Object.keys(value.employee).sort()).toEqual(['need_ids', 'reviewed', 'support_kind']);
    expect(value.employee.reviewed).toBe(true);
    expect(value.employee.need_ids.every(id => employeeIds.includes(id))).toBe(true);
    expect(new Set(value.employee.need_ids).size).toBe(value.employee.need_ids.length);
    expect(['health', 'carer', 'both']).toContain(value.employee.support_kind);
  }
  if (value.employer) {
    expect(Object.keys(value.employer).sort()).toEqual(['business_size', 'need_ids', 'reviewed']);
    expect(value.employer.reviewed).toBe(true);
    expect(value.employer.need_ids.every(id => employerIds.includes(id))).toBe(true);
    expect(new Set(value.employer.need_ids).size).toBe(value.employer.need_ids.length);
    expect(['under_50', '50_249', '250_plus']).toContain(value.employer.business_size);
  }
  const text = JSON.stringify(value);
  for (const privateText of [privateEmployee, privateEmployer, 'fibromyalgia', 'violet-cupboard', 'amber-drawer', 'description', 'role_context', 'private-funding']) expect(text).not.toContain(privateText);
  return value;
}

async function noStorage(page: Page) {
  expect(await page.evaluate(() => ({ local: localStorage.length, session: sessionStorage.length }))).toEqual({ local: 0, session: 0 });
}

async function strippedHash(page: Page) {
  await expect.poll(() => page.evaluate(() => window.location.hash)).toBe('');
}

async function privateWordsAbsent(page: Page) {
  const text = await page.locator('body').innerText();
  for (const privateText of ['fibromyalgia', 'violet-cupboard', 'amber-drawer', 'medical dosage', 'internal contract notes']) expect(text).not.toContain(privateText);
}

async function onePagePdf(page: Page, testInfo: TestInfo, filename: string) {
  await page.emulateMedia({ media: 'print' });
  await expect(page.getByRole('article', { name: 'Printable combined plan' })).toBeVisible();
  await expect(page.locator('.case-link-panel')).toBeHidden();
  const pdf = await page.pdf({ path: testInfo.outputPath(filename), preferCSSPageSize: true, printBackground: true });
  expect(pdf.subarray(0, 4).toString()).toBe('%PDF');
  expect(pdf.toString('latin1').match(/\/Type\s*\/Page\b/g) || []).toHaveLength(1);
  await page.emulateMedia({ media: 'screen' });
}

async function selectAllNeeds(page: Page, count: number) {
  const add = page.getByRole('button', { name: '+ Add a work need', exact: true });
  while (await page.locator('.case-needs-list select').count() < count) await add.click();
  await expect(add).toBeDisabled();
  await expect(page.locator('.case-needs-list select')).toHaveCount(count);
}

test('employee starts, reviews and removes needs, then both sides receive the same private one-page plan', async ({ page, context }, testInfo) => {
  const employeePlanRequests: string[] = [];
  page.on('request', request => { if (request.url().endsWith('/case/plan')) employeePlanRequests.push(request.postData() || ''); });
  await start(page, 'employee');
  await example(page, 'employee');
  await review(page);
  const needs = page.locator('.case-needs-list select');
  await expect(needs).toHaveCount(3);
  await needs.nth(0).selectOption('quiet');
  await page.getByRole('button', { name: 'Remove work need 2', exact: true }).click();
  await expect(needs).toHaveCount(2);
  const invitation = await confirm(page);
  const shared = decoded(invitation);
  expect(shared.employee?.need_ids).toEqual(['quiet', 'standing']);
  expect(shared.employer).toBeUndefined();
  expect(employeePlanRequests).toHaveLength(0);
  await expect(page.getByRole('article')).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Private cost comparison' })).toHaveCount(0);
  await noStorage(page);

  const employer = await context.newPage();
  await employer.goto(invitation);
  await expect(employer.getByRole('heading', { name: 'Tell us about your workplace.' })).toBeVisible();
  await strippedHash(employer);
  const received = employer.locator('.case-received');
  await expect(received).toContainText('I need a quieter place for focused work.');
  await expect(received).toContainText('Standing for long periods is hard.');
  await expect(received.locator('input, textarea, select, button')).toHaveCount(0);
  await privateWordsAbsent(employer);
  await example(employer, 'employer');
  await employer.getByLabel(/^Business size/).selectOption('50_249');
  await review(employer);
  const returnLink = await confirm(employer, true);
  const complete = decoded(returnLink);
  expect(complete.employee).toEqual(shared.employee);
  expect(complete.employer?.business_size).toBe('50_249');
  expect(complete.review_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  const employerPlan = employer.getByRole('article', { name: 'Printable combined plan' });
  await expect(employerPlan).toContainText('50–249 employees');
  await expect(employerPlan).toContainText('1. Start now, at no cost');
  await expect(employerPlan).toContainText('3. Your conversation agenda');
  await expect(employerPlan).toContainText('5. Check in together');
  await privateWordsAbsent(employer);
  await noStorage(employer);

  await page.goto(returnLink);
  const employeePlan = page.getByRole('article', { name: 'Printable combined plan' });
  await expect(employeePlan).toBeVisible();
  await strippedHash(page);
  expect(await employeePlan.innerText()).toBe(await employerPlan.innerText());
  await expect(page.getByRole('button', { name: 'Private cost comparison' })).toHaveCount(0);
  const reopened = await context.newPage();
  await reopened.goto(returnLink);
  await expect(reopened.getByRole('article', { name: 'Printable combined plan' })).toHaveText(await employeePlan.textContent() || '');
  await strippedHash(reopened);
  await noStorage(reopened);
  await reopened.close();
  for (const href of await employeePlan.getByRole('link', { name: /Official guidance/ }).evaluateAll(links => links.map(link => link.getAttribute('href')))) {
    expect(href).toMatch(/^https:\/\/(?:www\.)?(?:gov\.uk|acas\.org\.uk|hse\.gov\.uk|bolton\.gov\.uk|letskeepboltonmoving\.co\.uk)\//);
  }
  await onePagePdf(page, testInfo, 'combined-health-plan.pdf');
  await noStorage(page);
  await page.reload();
  await expect(page.getByRole('button', { name: /I’m an employee/ })).toBeVisible();
  await expect(page.getByRole('article')).toHaveCount(0);
  await employer.close();
});

test('employer starts and an unpaid carer adds their side, with separate verified carer rights', async ({ page, context }) => {
  await start(page, 'employer');
  await example(page, 'employer');
  await page.getByLabel(/^Business size/).selectOption('250_plus');
  await review(page);
  const invitation = await confirm(page);
  expect(decoded(invitation).employee).toBeUndefined();
  await expect(page.getByRole('article')).toHaveCount(0);

  const employee = await context.newPage();
  await employee.goto(invitation);
  await expect(employee.getByRole('heading', { name: 'What’s getting in the way?' })).toBeVisible();
  await strippedHash(employee);
  await expect(employee.locator('.case-received')).toContainText('250+ employees');
  await privateWordsAbsent(employee);
  await example(employee, 'employee', true);
  await expect(employee.getByLabel('What would you like support with?')).toHaveValue('carer');
  await review(employee);
  const returnLink = await confirm(employee, true);
  expect(decoded(returnLink).employee?.support_kind).toBe('carer');
  const plan = employee.getByRole('article', { name: 'Printable combined plan' });
  await expect(plan).toContainText('Right to request flexible working');
  await expect(plan).toContainText('from their first day');
  await expect(plan).toContainText("Unpaid Carer's Leave");
  await expect(plan).toContainText("Carer's assessment: Bolton Council");
  await expect(plan).toContainText("Check Carer's Allowance");
  await expect(plan).toContainText('Caring alone does not create a duty to make reasonable adjustments.');
  const links = await plan.locator('a').evaluateAll(items => items.map(link => link.getAttribute('href')));
  expect(links).toContain('https://www.gov.uk/flexible-working');
  expect(links).toContain('https://www.gov.uk/carers-leave');
  expect(links).toContain('https://www.bolton.gov.uk/carers');
  expect(links).toContain('https://www.gov.uk/carers-allowance/eligibility');
  await expect(employee.getByRole('button', { name: 'Private cost comparison' })).toHaveCount(0);
  await page.goto(returnLink);
  await expect(page.getByRole('article', { name: 'Printable combined plan' })).toHaveText(await plan.textContent() || '');
  await privateWordsAbsent(page);
  await noStorage(page);
  await employee.close();
});

test('employer figures remain private, do not enter either link, and are excluded from print', async ({ page, context }) => {
  const requests: string[] = [];
  await start(page, 'employer');
  await example(page, 'employer');
  page.on('request', request => { if (request.url().includes('/api/adjust/')) requests.push(request.postData() || request.url()); });
  await page.getByRole('button', { name: 'Private cost comparison', exact: true }).click();
  const costs = page.locator('.cc-private');
  await expect(costs).toContainText('Private to the employer. Not included in the link or combined plan.');
  await expect(costs.getByRole('spinbutton')).toHaveCount(8);
  for (const input of await costs.getByRole('spinbutton').all()) await expect(input).toBeEmpty();
  for (const [label, value] of [[/^Total cost of adjustments/, '4321.19'], [/^Confirmed Access to Work contribution/, '321.17'], [/^Recruitment/, '8765.43'], [/^Cover while/, '1000'], [/^Training/, '500'], [/^Time to reach/, '750']] as const) {
    await costs.getByRole('spinbutton', { name: label }).fill(value);
  }
  await expect(costs).toContainText('£4,000.02');
  await expect(costs).toContainText('legal risk unquantified');
  await costs.getByRole('spinbutton', { name: /^Available adjustment budget/ }).fill('1000');
  await expect(costs.getByRole('status')).toContainText('above the budget you entered');
  expect(requests).toHaveLength(0);
  await noStorage(page);
  await page.emulateMedia({ media: 'print' });
  await expect(costs).toBeHidden();
  await page.emulateMedia({ media: 'screen' });
  await page.getByRole('button', { name: 'Back to the shared flow' }).click();
  await page.getByRole('button', { name: 'Private cost comparison', exact: true }).click();
  for (const input of await costs.getByRole('spinbutton').all()) await expect(input).toBeEmpty();
  await page.getByRole('button', { name: 'Back to the shared flow' }).click();
  await review(page);
  const invitation = await confirm(page);
  decoded(invitation);
  const employee = await context.newPage();
  await employee.goto(invitation);
  await expect(employee.getByRole('heading', { name: 'What’s getting in the way?' })).toBeVisible();
  await example(employee, 'employee');
  await review(employee);
  const returnLink = await confirm(employee, true);
  decoded(returnLink);
  for (const amount of ['4321.19', '321.17', '8765.43', '£4,000.02']) {
    expect(JSON.stringify(decoded(returnLink))).not.toContain(amount);
    await expect(employee.getByRole('article')).not.toContainText(amount);
    expect(requests.join(' ')).not.toContain(amount);
  }
  await expect(employee.locator('.cc-private')).toHaveCount(0);
  await employee.close();
});

for (const role of ['employee', 'employer'] as const) {
  test(`${role} crisis language stops the shared flow and exposes all urgent support routes`, async ({ page }) => {
    const planRequests: string[] = [];
    page.on('request', request => { if (request.url().endsWith('/case/plan')) planRequests.push(request.url()); });
    await start(page, role);
    await example(page, role);
    await page.locator('#private-description').fill('Fictional urgent example: I cannot keep myself safe and I might hurt myself right now.');
    await page.getByRole('button', { name: 'Review what will be shared' }).click();
    const safety = page.getByRole('alert', { name: 'Urgent safety guidance' });
    await expect(safety).toBeVisible();
    await expect(safety.getByRole('link', { name: '999 · immediate danger' })).toHaveAttribute('href', 'tel:999');
    await expect(safety.getByRole('link', { name: 'NHS 111 · urgent help' })).toHaveAttribute('href', 'tel:111');
    await expect(safety.getByRole('link', { name: 'Samaritans · 116 123' })).toHaveAttribute('href', 'tel:116123');
    await expect(page.locator('#case-link')).toHaveCount(0);
    await expect(page.getByRole('article')).toHaveCount(0);
    await expect(page.getByRole('button', { name: /Create our combined plan|Private cost comparison/ })).toHaveCount(0);
    expect(planRequests).toHaveLength(0);
    await noStorage(page);
  });
}

test('keyboard and mobile flow remain usable and reload clears an opened invitation', async ({ page, context }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await page.keyboard.press('Tab');
  await expect(page.getByRole('link', { name: 'Skip to main content' })).toBeFocused();
  await page.keyboard.press('Enter');
  await page.getByRole('button', { name: /I’m an employee/ }).click();
  await expect(page.getByRole('heading', { name: 'What’s getting in the way?' })).toBeFocused();
  await example(page, 'employee');
  await review(page);
  const invitation = await confirm(page);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await noStorage(page);

  const employer = await context.newPage();
  await employer.setViewportSize({ width: 390, height: 844 });
  await employer.goto(invitation);
  await expect(employer.locator('.case-received')).toBeVisible();
  await strippedHash(employer);
  await example(employer, 'employer');
  expect(await employer.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await employer.reload();
  await expect(employer.getByRole('button', { name: /I’m an employer/ })).toBeVisible();
  await expect(employer.locator('.case-received')).toHaveCount(0);
  await employer.getByRole('button', { name: /I’m an employer/ }).click();
  await expect(employer.locator('#private-description')).toBeEmpty();
  await expect(employer.getByLabel(/^Business size/)).toHaveValue('');
  await noStorage(employer);
  await employer.close();
});

test('all reviewed needs with both health and caring support still produce a real one-page PDF', async ({ page, context }, testInfo) => {
  await start(page, 'employee');
  await example(page, 'employee', true);
  await page.getByLabel('What would you like support with?').selectOption('both');
  await review(page);
  await selectAllNeeds(page, employeeIds.length);
  const invitation = await confirm(page);
  expect(decoded(invitation).employee?.need_ids).toHaveLength(employeeIds.length);
  const employer = await context.newPage();
  await employer.goto(invitation);
  await expect(employer.locator('.case-received li')).toHaveCount(employeeIds.length);
  await example(employer, 'employer');
  await employer.getByLabel(/^Business size/).selectOption('250_plus');
  await review(employer);
  await selectAllNeeds(employer, employerIds.length);
  const returnLink = await confirm(employer, true);
  const shared = decoded(returnLink);
  expect(shared.employee?.need_ids).toHaveLength(employeeIds.length);
  expect(shared.employer?.need_ids).toHaveLength(employerIds.length);
  const plan = employer.getByRole('article', { name: 'Printable combined plan' });
  await expect(plan).toContainText('Working hours need to stay fixed.');
  await expect(plan).toContainText("Unpaid Carer's Leave");
  await expect(plan).toContainText("Carer's assessment: Bolton Council");
  await expect(plan).toContainText('Caring alone does not create that duty');
  await privateWordsAbsent(employer);
  await onePagePdf(employer, testInfo, 'combined-all-needs-health-and-carer-plan.pdf');
  await noStorage(employer);
  await employer.close();
});

test('a return link with a past review date can be renewed in the original tab', async ({ page, context }) => {
  await start(page, 'employee');
  await example(page, 'employee');
  await review(page);
  const invitation = await confirm(page);
  const employer = await context.newPage();
  await employer.goto(invitation);
  await expect(employer.getByRole('heading', { name: 'Tell us about your workplace.' })).toBeVisible();
  await example(employer, 'employer');
  await review(employer);
  const returnLink = await confirm(employer, true);
  const due = decoded(returnLink);
  due.review_date = await page.evaluate(() => {
    const date = new Date();
    date.setDate(date.getDate() - 1);
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  });
  const oldLink = new URL(returnLink);
  oldLink.hash = `case=${Buffer.from(JSON.stringify(due)).toString('base64')}`;
  await page.goto(oldLink.toString());
  await expect(page.getByRole('heading', { name: 'Time for a fresh check-in.' })).toBeVisible();
  await expect(page.getByRole('article')).toHaveCount(0);
  await strippedHash(page);
  const newDate = await page.getByLabel('New review date').inputValue();
  expect(newDate > due.review_date).toBe(true);
  await page.getByRole('button', { name: 'Prepare updated plan' }).click();
  await expect(page.getByRole('article', { name: 'Printable combined plan' })).toBeVisible();
  const renewed = decoded(await page.locator('#case-link').inputValue());
  expect(renewed.review_date).toBe(newDate);
  expect(renewed.employee).toEqual(due.employee);
  expect(renewed.employer).toEqual(due.employer);
  await privateWordsAbsent(page);
  await noStorage(page);
  await employer.close();
});
