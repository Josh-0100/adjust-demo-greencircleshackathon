import { expect, test, type APIRequestContext, type FrameLocator, type Page } from '@playwright/test';

type UI = Page | FrameLocator;
const staff = { 'X-Demo-Role': 'staff' };
const residentMarker = 'fictional-resident-saffron-416';
const privateEmployer = 'fictional-employer-copper-683';
const privateEmployee = 'fictional-employee-indigo-274';
const residentText = `I've worked in retail for ten years as a sales assistant and I'm good with customers and work well in a team. I'd like to retrain and get into IT, maybe start with a digital skills course. I'd prefer face to face support near me. ${residentMarker}`;
const residentFrame = (page: Page) => page.frameLocator('iframe[title="Adjust AI resident support"]');
const adjustFrame = (page: Page) => page.frameLocator('iframe[title="Adjust AI workplace adjustments"]');
const adviserFrame = (page: Page) => page.frameLocator('iframe[title="Adjust AI council dashboard"]');

async function stats(request: APIRequestContext) {
  const response = await request.get('/api/bolton-connect/stats', { headers: staff });
  expect(response.ok()).toBeTruthy();
  return response.json() as Promise<{ total_cases: number; sessions_saved: number }>;
}

async function checkResidentPlan(ui: UI) {
  await expect(ui.getByRole('heading', { name: 'Your plan', exact: true })).toBeVisible();
  for (const name of ['What we understood from your words', 'Suggested support services', 'Training ideas', 'Exploring employment', 'Things to do soon', 'Longer-term ideas', 'People who can help']) {
    await expect(ui.getByRole('heading', { name, exact: true })).toBeVisible();
  }
  await expect(ui.locator('#result')).toContainText('Skills that could help:');
  await expect(ui.locator('#result')).toContainText('Demonstration');
  await expect(ui.getByRole('button', { name: 'Print this plan', exact: true })).toBeVisible();
  await expect(ui.getByRole('button', { name: 'Download (JSON)', exact: true })).toBeVisible();
}

async function openMenu(page: Page) {
  const open = page.getByRole('button', { name: 'Open menu', exact: true });
  if (await open.isVisible()) await open.click();
}

async function navigate(page: Page, name: string) {
  await openMenu(page);
  await page.getByRole('link', { name, exact: true }).click();
}

async function reviewAdjust(ui: UI, complete: boolean) {
  await ui.getByRole('button', { name: 'Review what will be shared', exact: true }).click();
  await expect(ui.getByRole('heading', { name: 'Your words. Your choice.', exact: true })).toBeVisible();
  await expect(ui.locator('#private-description')).toHaveCount(0);
  const consent = ui.getByRole('checkbox', { name: /I’ve reviewed these items/ });
  await expect(consent).not.toBeChecked();
  await expect(consent).toHaveAttribute('required', '');
  await ui.getByRole('button', { name: complete ? 'Create our combined plan' : 'Create invitation link', exact: true }).click();
  await expect(ui.getByRole('heading', { name: 'Your words. Your choice.', exact: true })).toBeVisible();
  await expect(ui.locator('#case-link')).toHaveCount(0);
  await consent.check();
  await ui.getByRole('button', { name: complete ? 'Create our combined plan' : 'Create invitation link', exact: true }).click();
  if (complete) await expect(ui.getByRole('article', { name: 'Printable combined plan' })).toBeVisible();
  else await expect(ui.getByRole('heading', { name: 'Your side is ready.', exact: true })).toBeVisible();
  return ui.locator('#case-link').inputValue();
}

function reviewedHandoff(link: string) {
  const url = new URL(link);
  expect(url.pathname).toBe('/workplace-adjustments');
  expect(url.search).toBe('');
  expect(url.hash).toMatch(/^#case=/);
  const payload = JSON.parse(Buffer.from(url.hash.slice(6), 'base64').toString('utf8'));
  expect(Object.keys(payload).every(key => ['v', 'starter', 'employee', 'employer', 'review_date'].includes(key))).toBe(true);
  for (const side of [payload.employee, payload.employer].filter(Boolean)) {
    expect(side.reviewed).toBe(true);
    expect(Array.isArray(side.need_ids)).toBe(true);
  }
  for (const marker of [residentMarker, privateEmployer, privateEmployee, 'description', 'role_context']) expect(JSON.stringify(payload)).not.toContain(marker);
  return payload;
}

async function noHorizontalOverflow(page: Page, ui?: FrameLocator) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  if (ui) {
    expect(await ui.locator('html').evaluate(element => element.scrollWidth <= element.ownerDocument.defaultView!.innerWidth)).toBe(true);
    // Cached module documents must expand their host frame as well as fresh loads.
    await expect.poll(() => ui.locator('body').evaluate(element => Math.max((element as HTMLElement).offsetHeight, element.scrollHeight) <= element.ownerDocument.defaultView!.innerHeight + 2)).toBe(true);
  }
}

test.beforeEach(async ({ request }) => {
  const health = await request.get('/api/health');
  expect(health.ok()).toBeTruthy();
  test.skip(!(await health.json()).demo_mode, 'Journey tests use fictional data and may run only in demo mode.');
});

for (const integrated of [false, true]) {
  test(`resident completes assessment, support, training, employment and adviser handoff ${integrated ? 'through unified navigation' : 'independently'}`, async ({ page, request }) => {
    let savedSession: string | undefined;
    const adjustRequests: string[] = [];
    page.on('request', item => {
      const path = new URL(item.url()).pathname;
      // The shared landing reads the public work-needs catalogue before a
      // visitor chooses resident support. It sends no personal information.
      if (path.startsWith('/api/adjust/') && !(path === '/api/adjust/case/catalogue' && item.method() === 'GET')) adjustRequests.push(`${item.url()} ${item.postData() || ''}`);
    });
    const initial = await stats(request);
    try {
      if (integrated) {
        await page.goto('/');
        await expect(adjustFrame(page).getByRole('heading', { name: 'Practical help to keep people in work', exact: true })).toBeVisible();
        await navigate(page, 'Assessment');
        await expect(page).toHaveURL(/\/resident-support#assessment$/);
      } else {
        await page.goto('/module-assets/bolton-connect/index.html');
      }
      const ui = integrated ? residentFrame(page) : page;
      await expect(ui.locator('#consent_save')).not.toBeChecked();
      await expect(ui.locator('#consent_share')).not.toBeChecked();
      await ui.getByLabel(/In your own words, what's your situation/).fill(residentText);
      await ui.getByLabel('Your first name (optional)', { exact: true }).fill('Fictional Priya');
      await ui.getByLabel('How confident are you using computers? (optional)', { exact: true }).selectOption('low');
      const unsaved = page.waitForResponse(response => response.url().endsWith('/api/bolton-connect/plan') && response.request().method() === 'POST');
      await ui.getByRole('button', { name: 'Create my plan', exact: true }).click();
      const unsavedResponse = await unsaved;
      expect(unsavedResponse.ok()).toBe(true);
      const unsavedPlan = await unsavedResponse.json();
      expect(unsavedPlan.session_id).toBeNull();
      expect(unsavedPlan.case_id).toBeNull();
      await checkResidentPlan(ui);
      if (integrated) {
        for (const [name, hash, target] of [['Local Services', 'local-services', 'local-services'], ['Training', 'training', 'training'], ['Employment Pathways', 'employment-pathways', 'employment-pathways'], ['Action Plan', 'action-plan', 'result']] as const) {
          await navigate(page, name);
          await expect(page).toHaveURL(new RegExp(`/resident-support#${hash}$`));
          await expect(ui.locator(`#${target}`)).toBeVisible();
          await expect(ui.locator('#result')).toContainText("Fictional Priya's plan");
        }
      }
      expect(await stats(request)).toEqual(initial);
      expect(adjustRequests).toHaveLength(0);

      await ui.locator('#consent_save').check();
      await ui.locator('#consent_share').check();
      const shared = page.waitForResponse(response => response.url().endsWith('/api/bolton-connect/plan') && response.request().method() === 'POST');
      await ui.getByRole('button', { name: 'Create my plan', exact: true }).click();
      const sharedResponse = await shared;
      expect(sharedResponse.ok()).toBe(true);
      const sharedPlan = await sharedResponse.json();
      savedSession = sharedPlan.session_id;
      expect(savedSession).toBeTruthy();
      expect(sharedPlan.case_id).toBeTruthy();
      expect(sharedResponse.request().postDataJSON()).toMatchObject({ consent_save: true, consent_share: true });
      await expect(ui.locator('#result')).toContainText('Shared with an adviser.');
      await expect(ui.locator('#result')).toContainText(sharedPlan.case_id);
      expect(await stats(request)).toMatchObject({ total_cases: initial.total_cases + 1, sessions_saved: initial.sessions_saved + 1 });
      const savedLink = await ui.locator('#result a').filter({ hasText: 'session=' }).getAttribute('href');
      expect(savedLink).toContain(`session=${savedSession}`);
      const resumed = await request.get(`/api/bolton-connect/sessions/${savedSession}`);
      expect((await resumed.json()).result).toEqual(sharedPlan.plan);
      expect((await request.get('/api/bolton-connect/cases')).status()).toBe(403);

      if (integrated) await navigate(page, 'Case Review');
      else await page.goto('/module-assets/bolton-connect/adviser.html');
      const adviser = integrated ? adviserFrame(page) : page;
      await expect(adviser.getByRole('heading', { name: 'Case queue', exact: true })).toBeVisible();
      const casesResponse = await request.get('/api/bolton-connect/cases', { headers: staff });
      const cases = (await casesResponse.json()).cases as { id: string }[];
      const position = cases.findIndex(item => item.id === sharedPlan.case_id);
      expect(position).toBeGreaterThanOrEqual(0);
      await expect(adviser.locator('#cases-body tr')).toHaveCount(cases.length);
      await adviser.locator('#cases-body tr').nth(position).getByRole('button', { name: 'Open', exact: true }).click();
      await expect(adviser.locator('#detail')).toContainText(sharedPlan.case_id);
      await expect(adviser.locator('#detail')).not.toContainText(residentMarker);
      await expect(adviser.locator('#detail')).not.toContainText('Fictional Priya');
      await adviser.getByRole('textbox', { name: 'Add a note', exact: true }).fill('Fictional review: confirm training availability and resident preferences before referral.');
      await adviser.getByRole('button', { name: 'Add note', exact: true }).click();
      await expect(adviser.locator('#detail')).toContainText('Fictional review: confirm training availability');
      await adviser.getByRole('combobox', { name: 'Case status', exact: true }).selectOption('in_review');
      await adviser.getByRole('button', { name: 'Update case', exact: true }).click();
      await expect.poll(async () => (await (await request.get(`/api/bolton-connect/cases/${sharedPlan.case_id}`, { headers: staff })).json()).status).toBe('in_review');
      expect(adjustRequests).toHaveLength(0);

      if (integrated) {
        await navigate(page, 'Employer Assessment');
        const adjust = adjustFrame(page);
        await expect(adjust.getByRole('button', { name: /I’m an employer/ })).toBeVisible();
        await adjust.getByRole('button', { name: /I’m an employer/ }).click();
        await expect(adjust.locator('#private-description')).toBeEmpty();
        await expect(adjust.locator('body')).not.toContainText(residentMarker);
        const source = await page.locator('iframe[title="Adjust AI workplace adjustments"]').getAttribute('src');
        expect(source).not.toContain('session=');
        expect(source).not.toContain(sharedPlan.case_id);
        for (const payload of adjustRequests) {
          expect(payload).not.toContain(residentMarker);
          expect(payload).not.toContain(savedSession);
          expect(payload).not.toContain(sharedPlan.case_id);
        }
      }
    } finally {
      if (savedSession) expect((await request.delete(`/api/bolton-connect/sessions/${savedSession}`)).ok()).toBeTruthy();
    }
  });
}

test('employer and employee independently review their contributions and complete the same plan through unified navigation', async ({ page, context, request }) => {
  const initial = await stats(request);
  const transmitted: string[] = [];
  const planBodies: string[] = [];
  context.on('request', item => {
    const path = new URL(item.url()).pathname;
    if (path.startsWith('/api/adjust/')) transmitted.push(`${item.url()} ${item.postData() || ''}`);
    if (path === '/api/adjust/case/plan') planBodies.push(item.postData() || '');
  });
  await page.goto('/');
  await navigate(page, 'Employer Assessment');
  await expect(page).toHaveURL(/\/workplace-adjustments#assessment$/);
  const employer = adjustFrame(page);
  await employer.getByRole('button', { name: /I’m an employer/ }).click();
  await employer.getByRole('button', { name: 'Work and energy', exact: true }).click();
  await employer.locator('#private-description').fill(`${await employer.locator('#private-description').inputValue()} ${privateEmployer}`);
  await employer.getByLabel(/^Business size/).selectOption('50_249');
  const invitation = await reviewAdjust(employer, false);
  const employerContribution = reviewedHandoff(invitation);
  expect(employerContribution.employee).toBeUndefined();
  expect(employerContribution.employer.business_size).toBe('50_249');
  await expect(employer.getByRole('article')).toHaveCount(0);

  const colleague = await context.newPage();
  try {
    await colleague.goto(`/workplace-adjustments${new URL(invitation).hash}`);
    const employee = adjustFrame(colleague);
    await expect(employee.getByRole('heading', { name: 'What’s getting in the way?', exact: true })).toBeVisible();
    await expect(employee.locator('.case-received')).toContainText('50–249 employees');
    await expect(employee.locator('body')).not.toContainText(privateEmployer);
    await employee.getByRole('button', { name: 'Work and energy', exact: true }).click();
    await employee.locator('#private-description').fill(`${await employee.locator('#private-description').inputValue()} ${privateEmployee}`);
    const returnLink = await reviewAdjust(employee, true);
    const completed = reviewedHandoff(returnLink);
    expect(completed.employer).toEqual(employerContribution.employer);
    expect(completed.employee.reviewed).toBe(true);
    const employeePlan = employee.getByRole('article', { name: 'Printable combined plan' });
    for (const text of ['1. Start now, at no cost', '3. Your conversation agenda', '5. Check in together']) await expect(employeePlan).toContainText(text);
    await expect(employeePlan.getByRole('link', { name: /Official guidance/ }).first()).toBeVisible();
    const planText = await employeePlan.innerText();
    await page.goto(`/workplace-adjustments${new URL(returnLink).hash}`);
    const employerPlan = adjustFrame(page).getByRole('article', { name: 'Printable combined plan' });
    await expect(employerPlan).toHaveText(await employeePlan.textContent() || '');
    expect(await employerPlan.innerText()).toBe(planText);
    for (const [name, hash, target] of [['Adjustment Suggestions', 'suggestions', 'adjustment-suggestions'], ['Conversation Guide', 'conversation', 'conversation-guide'], ['Adjustment Plan', 'plan', 'adjustment-plan']] as const) {
      await navigate(page, name);
      await expect(page).toHaveURL(new RegExp(`/workplace-adjustments#${hash}$`));
      await expect(adjustFrame(page).locator(`#${target}`)).toBeVisible();
      expect(await employerPlan.innerText()).toBe(planText);
    }
    await expect.poll(() => adjustFrame(page).locator('html').evaluate(element => element.ownerDocument.defaultView!.location.hash)).toBe('');
    await adjustFrame(page).getByRole('button', { name: 'Clear this session', exact: true }).click();
    await expect(adjustFrame(page).getByRole('heading', { name: /Two perspectives/ })).toBeVisible();
    await expect(employerPlan).toHaveCount(0);
    await page.evaluate(hash => { window.location.hash = hash; }, new URL(returnLink).hash);
    await expect(employerPlan).toBeVisible();
    expect(await employerPlan.innerText()).toBe(planText);
    await expect.poll(() => page.evaluate(() => window.location.hash)).toBe('');
    await expect.poll(() => adjustFrame(page).locator('html').evaluate(element => element.ownerDocument.defaultView!.location.hash)).toBe('');
    await expect(employerPlan).not.toContainText(privateEmployee);
    await expect(employerPlan).not.toContainText(privateEmployer);
    for (const payload of transmitted) expect(payload).not.toContain(residentMarker);
    expect(planBodies.length).toBeGreaterThan(0);
    for (const payload of planBodies) for (const marker of [privateEmployee, privateEmployer]) expect(payload).not.toContain(marker);
    expect(await stats(request)).toEqual(initial);
  } finally {
    await colleague.close();
  }
});

test('all navigation children, original portal and mobile layouts remain accessible with Adjust AI branding', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  await expect(adjustFrame(page).getByRole('heading', { name: 'Practical help to keep people in work', exact: true })).toBeVisible();
  await expect(page.locator('.topbar-brand')).toHaveAttribute('aria-label', 'Adjust AI home');
  await expect(page.getByRole('link', { name: 'Talk to an advisor', exact: true })).toBeVisible();
  await expect(page.locator('body')).not.toContainText(/CIVICFORGE|Bolton Connect/i);
  await noHorizontalOverflow(page);
  await openMenu(page);
  for (const name of ['Assessment', 'Local Services', 'Training', 'Employment Pathways', 'Action Plan', 'Employer Assessment', 'Adjustment Suggestions', 'Conversation Guide', 'Adjustment Plan', 'Case Review', 'Referrals', 'Aggregated Insights']) {
    await expect(page.getByRole('link', { name, exact: true })).toBeVisible();
  }
  for (const name of ['Resident Support', 'Workplace Adjustments', 'Council Dashboard']) await expect(page.getByText(name, { exact: true }).first()).toBeVisible();
  await page.getByRole('link', { name: 'Assessment', exact: true }).click();
  await expect(residentFrame(page).getByRole('button', { name: 'Create my plan', exact: true })).toBeVisible();
  await expect(residentFrame(page).locator('body')).not.toContainText(/CIVICFORGE|Bolton Connect/i);
  await noHorizontalOverflow(page, residentFrame(page));
  await navigate(page, 'Employer Assessment');
  const employer = adjustFrame(page);
  await employer.getByRole('button', { name: /I’m an employer/ }).click();
  await employer.getByRole('button', { name: 'Work and energy', exact: true }).click();
  await noHorizontalOverflow(page, employer);
  await navigate(page, 'Case Review');
  await expect(adviserFrame(page).getByRole('heading', { name: 'Case queue', exact: true })).toBeVisible();
  await expect(adviserFrame(page).locator('body')).not.toContainText(/CIVICFORGE|Bolton Connect/i);
  await noHorizontalOverflow(page, adviserFrame(page));
  await page.goto('/portal');
  await expect(page.getByLabel('Tell us a little about your situation')).toBeVisible();
  await noHorizontalOverflow(page);
});

test('reference landing opens both existing assessments without losing private text or bypassing review', async ({ page }) => {
  const prepared: string[] = [];
  page.on('request', item => {
    if (new URL(item.url()).pathname === '/api/adjust/case/prepare' && item.method() === 'POST') prepared.push(item.postData() || '');
  });
  for (const role of ['employer', 'employee'] as const) {
    await page.goto('/');
    const ui = adjustFrame(page);
    await expect(page.locator('iframe[title="Adjust AI workplace adjustments"]')).toHaveAttribute('src', '/modules/adjust?entry=landing');
    await expect(ui.getByRole('heading', { name: 'Practical help to keep people in work', exact: true })).toBeVisible();
    await expect(ui.getByRole('button', { name: 'Business', exact: true })).toHaveAttribute('aria-pressed', 'true');
    await expect(ui.getByRole('button', { name: 'Employee', exact: true })).toHaveAttribute('aria-pressed', 'false');
    const logo = await page.locator('.topbar-brand').boundingBox();
    const adviserLink = page.getByRole('link', { name: 'Talk to an advisor', exact: true });
    const adviser = await adviserLink.boundingBox();
    expect(logo && adviser && logo.x < adviser.x).toBeTruthy();
    await adviserLink.click();
    await expect(page).toHaveURL(/\/#talk$/);
    await expect(ui.locator('#talk')).toBeInViewport();
    await expect(ui.locator('#talk').getByRole('link', { name: /contact Acas/ })).toHaveAttribute('href', 'https://www.acas.org.uk/contact');

    if (role === 'employee') await ui.getByRole('button', { name: 'Employee', exact: true }).click();
    const description = `Fictional ${role} scenario: standing all day is difficult and regular breaks or a task change could help. landing-private-${role}-842`;
    await ui.getByRole('textbox', { name: 'Describe the situation', exact: true }).fill(description);
    const before = prepared.length;
    await ui.getByRole('button', { name: 'Get my plan', exact: true }).click();
    await expect(ui.getByRole('heading', { name: role === 'employee' ? 'What’s getting in the way?' : 'Tell us about your workplace.', exact: true })).toBeVisible();
    await expect(ui.locator('#private-description')).toHaveValue(description);
    await adviserLink.click();
    await expect(ui.locator('#talk')).toBeInViewport();
    await expect(ui.locator('#private-description')).toHaveValue(description);
    const fictional = ui.getByRole('checkbox', { name: 'I’m using fictional details for this demo.', exact: true });
    await expect(fictional).not.toBeChecked();
    if (role === 'employer') await ui.getByLabel(/^Business size/).selectOption('under_50');
    await ui.getByRole('button', { name: 'Review what will be shared', exact: true }).click();
    await expect(ui.locator('#private-description')).toHaveValue(description);
    expect(prepared.length).toBe(before);
    await expect(ui.locator('#case-link')).toHaveCount(0);

    await fictional.check();
    await ui.getByRole('button', { name: 'Review what will be shared', exact: true }).click();
    await expect(ui.getByRole('heading', { name: 'Your words. Your choice.', exact: true })).toBeVisible();
    expect(prepared.length).toBe(before + 1);
    expect(JSON.parse(prepared[before])).toMatchObject({ role, description });
    await expect(ui.getByRole('checkbox', { name: /I’ve reviewed these items/ })).not.toBeChecked();
    await expect(ui.locator('#case-link')).toHaveCount(0);
    await expect(ui.locator('#private-description')).toHaveCount(0);
    expect(await page.locator('iframe[title="Adjust AI workplace adjustments"]').getAttribute('src')).not.toContain('landing-private');
    await noHorizontalOverflow(page, ui);
  }
});

