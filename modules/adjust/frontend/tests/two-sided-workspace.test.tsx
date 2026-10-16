import { act, fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';
import { TwoSidedWorkspace } from '@/components/two-sided-workspace';
import { caseApi, decodeHandoff, encodeHandoff, type CaseHandoff, type Catalogue, type CombinedPlan, type PreparedSide } from '@/lib/case-api';

vi.mock('@/lib/case-api', async original => {
  const actual = await original<typeof import('@/lib/case-api')>();
  return { ...actual, caseApi: { catalogue: vi.fn(), prepare: vi.fn(), plan: vi.fn() } };
});

const catalogue: Catalogue = {
  employee_needs: [
    { id: 'later-start', text: 'Mornings are hard; I would like to discuss a later start.' },
    { id: 'breaks', text: 'I need regular breaks during the working day.' },
    { id: 'quiet', text: 'I need a quieter place for focused work.' },
  ],
  employer_needs: [
    { id: 'cover', text: 'We need reliable cover during agreed working hours.' },
    { id: 'fixed-hours', text: 'Working hours need to stay fixed.' },
    { id: 'limited-budget', text: 'We need to work within a limited budget.' },
  ],
};
const employee = { reviewed: true as const, need_ids: ['later-start'], support_kind: 'health' as const };
const employer = { reviewed: true as const, need_ids: ['cover'], business_size: 'under_50' as const };
const plan: CombinedPlan = {
  title: 'Our workplace conversation plan', created_on: '2026-10-16', review_date: '2026-10-30',
  start_now: [], options: [], conversation: { opening: 'Let us agree a practical trial together.', questions: ['What would help at work?'], agree: ['Agree a review date.'] },
  help: [], legal_note: 'Discuss the applicable rights.', disclaimer: 'Fictional demo discussion draft.',
};

function prepared(role: 'employee' | 'employer'): PreparedSide {
  return { status: 'review', needs: (role === 'employee' ? catalogue.employee_needs : catalogue.employer_needs).slice(0, 2),
    safety: { level: 'routine', title: 'Review your work needs', message: 'These are suggestions to review.', actions: [], official_url: null } };
}

function openHandoff(value: CaseHandoff) {
  window.history.replaceState(null, '', `/#case=${encodeHandoff(value, catalogue)}`);
}

beforeEach(() => {
  vi.clearAllMocks();
  window.history.replaceState(null, '', '/');
  vi.mocked(caseApi.catalogue).mockResolvedValue(catalogue);
  vi.mocked(caseApi.prepare).mockResolvedValue(prepared('employee'));
  vi.mocked(caseApi.plan).mockImplementation(async body => ({ ...plan, review_date: body.review_date }));
});

it.each(['employee', 'employer'] as const)('keeps a landing %s situation in memory and requires the existing confirmation before preparing it', async role => {
  const user = userEvent.setup();
  const localSave = vi.spyOn(Storage.prototype, 'setItem');
  vi.mocked(caseApi.prepare).mockResolvedValue(prepared(role));
  render(<TwoSidedWorkspace embedded landing />);
  expect(screen.getByRole('heading', { name: 'Practical help to keep people in work' })).toBeVisible();
  expect(screen.queryByRole('button', { name: 'Open Adjust AI sidebar' })).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: role === 'employee' ? 'Employee' : 'Business' }));
  expect(screen.getByRole('button', { name: role === 'employee' ? 'Employee' : 'Business' })).toHaveAttribute('aria-pressed', 'true');
  const privateWords = 'Fictional PRIVATE_LANDING situation: flexible hours and regular breaks would help with work.';
  fireEvent.change(screen.getByRole('textbox', { name: 'Describe the situation' }), { target: { value: privateWords } });
  await user.click(screen.getByRole('button', { name: 'Get my plan' }));
  expect(screen.getByRole('heading', { name: role === 'employee' ? 'What’s getting in the way?' : 'Tell us about your workplace.' })).toBeVisible();
  expect(screen.getByRole('textbox', { name: role === 'employee' ? /What’s happening and what’s hard at work/ : /Describe the situation/ })).toHaveValue(privateWords);
  expect(screen.getByRole('checkbox', { name: /I’m using fictional details/ })).not.toBeChecked();
  expect(screen.getByRole('link', { name: /contact Acas/ }).closest('footer')).toHaveAttribute('id', 'talk');
  expect(caseApi.prepare).not.toHaveBeenCalled();
  expect(localSave).not.toHaveBeenCalled();
  expect(window.location.href).not.toContain('PRIVATE_LANDING');
  if (role === 'employer') await user.selectOptions(screen.getByLabelText(/Business size/), 'under_50');
  await user.click(screen.getByRole('checkbox', { name: /I’m using fictional details/ }));
  await user.click(screen.getByRole('button', { name: /Review what will be shared/ }));
  await screen.findByRole('heading', { name: 'Your words. Your choice.' });
  expect(caseApi.prepare).toHaveBeenCalledWith(expect.objectContaining({ role, description: privateWords }));
  expect(screen.getByRole('checkbox', { name: /I’ve reviewed these items/ })).not.toBeChecked();
  localSave.mockRestore();
});

it('uses landing examples without selecting either confirmation and restores the landing after clearing', async () => {
  const user = userEvent.setup();
  render(<TwoSidedWorkspace embedded landing />);
  await user.click(screen.getByRole('button', { name: 'Employee' }));
  await user.click(screen.getByRole('button', { name: 'Caring responsibilities' }));
  expect(screen.getByRole('textbox', { name: 'Describe the situation' })).toHaveValue('Fictional example: I care for my father without pay. Flexibility for appointments and unexpected changes to the morning routine might help.');
  await user.click(screen.getByRole('button', { name: 'Get my plan' }));
  expect(screen.getByLabelText('What would you like support with?')).toHaveValue('carer');
  expect(screen.getByRole('checkbox', { name: /I’m using fictional details/ })).not.toBeChecked();
  await user.click(screen.getByRole('button', { name: 'Clear this session' }));
  expect(screen.getByRole('heading', { name: 'Practical help to keep people in work' })).toBeVisible();
  expect(screen.getByRole('textbox', { name: 'Describe the situation' })).toHaveValue('');
  expect(caseApi.prepare).not.toHaveBeenCalled();
});

it('does not restore an incoming plan when its pending request completes after pagehide', async () => {
  let complete!: (value: CombinedPlan) => void;
  vi.mocked(caseApi.plan).mockReturnValue(new Promise(resolve => { complete = resolve; }));
  openHandoff({ v: 1, starter: 'employee', employee, employer, review_date: '2026-10-30' });
  render(<TwoSidedWorkspace />);
  await waitFor(() => expect(caseApi.plan).toHaveBeenCalledOnce());
  expect(window.location.hash).toBe('');
  fireEvent(window, new Event('pagehide'));
  await act(async () => complete(plan));
  expect(screen.getByRole('heading', { name: /Two perspectives/ })).toBeVisible();
  expect(screen.queryByRole('article', { name: 'Printable combined plan' })).not.toBeInTheDocument();
  expect(screen.queryByLabelText('Combined plan return link')).not.toBeInTheDocument();
  expect(screen.queryByRole('button', { name: 'Private cost comparison' })).not.toBeInTheDocument();
});

it('keeps reviewed embedded handoffs within unified navigation and retains sidebar tools', async () => {
  const user = userEvent.setup();
  const shared: CaseHandoff = { v: 1, starter: 'employer', employee, employer, review_date: '2026-10-30' };
  window.history.replaceState(null, '', `/modules/adjust#case=${encodeHandoff(shared, catalogue)}`);
  render(<TwoSidedWorkspace embedded />);
  const outgoing = (await screen.findByLabelText('Combined plan return link') as HTMLInputElement).value;
  expect(new URL(outgoing).pathname).toBe('/workplace-adjustments');
  expect(decodeHandoff(new URL(outgoing).hash.slice(6), catalogue)).toEqual(shared);
  expect(window.location.hash).toBe('');
  expect(screen.getByRole('button', { name: 'Open Adjust AI sidebar' })).toHaveAttribute('aria-expanded', 'false');
  await user.click(screen.getByRole('button', { name: 'Open Adjust AI sidebar' }));
  expect(screen.getByRole('button', { name: 'Close Adjust AI sidebar' })).toHaveAttribute('aria-expanded', 'true');
  expect(screen.getByRole('button', { name: 'Private cost comparison' })).toBeVisible();
});

it('requires another review after editing or removing needs and shares only those selections', async () => {
  const user = userEvent.setup();
  render(<TwoSidedWorkspace />);
  await user.click(await screen.findByRole('button', { name: /I.m an employee/ }));
  const privateWords = 'Fictional PRIVATE_ALPHA has Parkinson disease and finds mornings and long standing hard at work.';
  fireEvent.change(screen.getByRole('textbox', { name: /What’s happening and what’s hard at work/ }), { target: { value: privateWords } });
  await user.click(screen.getByRole('checkbox', { name: /I’m using fictional details/ }));
  await user.click(screen.getByRole('button', { name: /Review what will be shared/ }));
  const review = await screen.findByRole('checkbox', { name: /I’ve reviewed these items/ });
  await user.click(review);
  expect(review).toBeChecked();
  await user.selectOptions(screen.getByLabelText('Work need 1'), 'quiet');
  expect(review).not.toBeChecked();
  await user.click(review);
  await user.click(screen.getByRole('button', { name: 'Remove work need 2' }));
  expect(review).not.toBeChecked();
  await user.click(review);
  await user.click(screen.getByRole('button', { name: /Create invitation link/ }));
  const link = (await screen.findByLabelText('Link to send yourself') as HTMLInputElement).value;
  const encoded = new URL(link).hash.slice(6);
  expect(decodeHandoff(encoded, catalogue)).toEqual({ v: 1, starter: 'employee', employee: { ...employee, need_ids: ['quiet'] } });
  expect(atob(encoded)).not.toMatch(/PRIVATE_ALPHA|Parkinson|description/);
  expect(caseApi.plan).not.toHaveBeenCalled();
  expect(caseApi.prepare).toHaveBeenCalledWith(expect.objectContaining({ description: privateWords }));
  await user.click(screen.getByRole('button', { name: 'Clear this session' }));
  await user.click(screen.getByRole('button', { name: /I.m an employee/ }));
  expect(screen.getByRole('textbox', { name: /What’s happening and what’s hard at work/ })).toHaveValue('');
});

it.each(['employee', 'employer'] as const)('adds the %s side to an invitation and returns only the two reviewed contributions', async role => {
  const user = userEvent.setup();
  const starter = role === 'employee' ? 'employer' : 'employee';
  openHandoff({ v: 1, starter, ...(starter === 'employee' ? { employee } : { employer }) });
  vi.mocked(caseApi.prepare).mockResolvedValue(prepared(role));
  render(<TwoSidedWorkspace />);
  await screen.findByRole('heading', { name: role === 'employee' ? 'What’s getting in the way?' : 'Tell us about your workplace.' });
  expect(screen.getByRole('heading', { name: 'Their reviewed work needs' })).toBeVisible();
  expect(screen.getByText(starter === 'employee' ? catalogue.employee_needs[0].text : catalogue.employer_needs[0].text)).toBeVisible();
  const privateWords = 'Fictional PRIVATE_BETA has a private medical condition and wants to discuss workplace needs.';
  fireEvent.change(screen.getByRole('textbox', { name: role === 'employee' ? /What’s happening and what’s hard at work/ : /Describe the situation/ }), { target: { value: privateWords } });
  if (role === 'employer') {
    await user.selectOptions(screen.getByLabelText(/Business size/), '50_249');
    fireEvent.change(screen.getByLabelText(/What does the role involve/), { target: { value: 'PRIVATE_CORE_TASK_WORDS' } });
    fireEvent.change(screen.getByLabelText(/What’s practical for the business/), { target: { value: 'PRIVATE_BUDGET_WORDS' } });
    fireEvent.change(screen.getByLabelText(/Anything already tried/), { target: { value: 'PRIVATE_TRIAL_WORDS' } });
    expect(screen.getByRole('button', { name: 'Private cost comparison' })).toBeVisible();
  } else expect(screen.queryByRole('button', { name: 'Private cost comparison' })).not.toBeInTheDocument();
  await user.click(screen.getByRole('checkbox', { name: /I’m using fictional details/ }));
  await user.click(screen.getByRole('button', { name: /Review what will be shared/ }));
  await user.click(await screen.findByRole('checkbox', { name: /I’ve reviewed these items/ }));
  await user.click(screen.getByRole('button', { name: 'Create our combined plan' }));
  const outgoing = (await screen.findByLabelText('Combined plan return link') as HTMLInputElement).value;
  const payload = decodeHandoff(new URL(outgoing).hash.slice(6), catalogue);
  expect(payload.employee?.reviewed).toBe(true);
  expect(payload.employer?.reviewed).toBe(true);
  expect(payload.starter).toBe(starter);
  expect(caseApi.plan).toHaveBeenCalledOnce();
  expect(caseApi.plan).toHaveBeenCalledWith({ employee: payload.employee, employer: payload.employer, review_date: payload.review_date });
  expect(JSON.stringify(payload)).not.toMatch(/PRIVATE_|medical condition|description|practicalities|tried|role_context/);
  expect(screen.getByRole('article', { name: 'Printable combined plan' })).not.toHaveTextContent('PRIVATE_');
});
