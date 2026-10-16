import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, expect, it, vi } from 'vitest';
import { AdjustWorkspace } from '@/components/adjust-workspace';
import { api } from '@/lib/api';

vi.mock('@/lib/api', async original => {
  const actual = await original<typeof import('@/lib/api')>();
  return { ...actual, api: { health: vi.fn(), knowledge: vi.fn(), support: vi.fn(), scenarios: vi.fn(), analyse: vi.fn(), plan: vi.fn() } };
});
beforeEach(() => {
  vi.mocked(api.health).mockResolvedValue({ status: 'ok', module: 'adjust', provider: 'local-rules', data_persisted: false, ai_configured: false, knowledge_entries: 32, professional_review: 'pending' });
  vi.mocked(api.knowledge).mockResolvedValue({ entries: [] });
  vi.mocked(api.support).mockResolvedValue({ referrals: [] });
  vi.mocked(api.scenarios).mockRejectedValue(new Error('Use bundled examples'));
});

it('provides a labelled form and keeps model calls off by default', async () => {
  const user = userEvent.setup();
  render(<AdjustWorkspace />);
  await user.click(screen.getByRole('button', { name: 'Explore a workplace situation' }));
  expect(screen.getByRole('textbox', { name: /Describe the workplace situation/ })).toHaveAttribute('maxLength', '4000');
  expect(screen.getByLabelText(/Job role/)).toBeVisible();
  expect(screen.queryByText(/Use the configured AI/)).not.toBeInTheDocument();
  expect(document.activeElement).toBe(screen.getByRole('heading', { name: 'What’s getting in the way?' }));
});

it('shows a recoverable submission error and preserves the description', async () => {
  const user = userEvent.setup();
  vi.mocked(api.analyse).mockRejectedValue(new Error('Local service is unavailable.'));
  render(<AdjustWorkspace />);
  await user.click(screen.getByRole('button', { name: /Lifting and back pain/ }));
  const description = screen.getByRole('textbox', { name: /Describe the workplace situation/ });
  expect((description as HTMLTextAreaElement).value).toContain('warehouse');
  await user.click(screen.getByRole('button', { name: 'Explore possible adjustments' }));
  expect(await screen.findByRole('alert')).toHaveTextContent('Local service is unavailable.');
  expect((description as HTMLTextAreaElement).value).toContain('warehouse');
  expect(api.analyse).toHaveBeenCalledWith(expect.objectContaining({ use_ai: false }));
});

it('clear session removes the entered description', async () => {
  const user = userEvent.setup();
  render(<AdjustWorkspace />);
  await user.click(screen.getByRole('button', { name: 'Explore a workplace situation' }));
  fireEvent.change(screen.getByLabelText(/Describe the workplace situation/), { target: { value: 'A private draft description about workplace tasks.' } });
  await user.click(screen.getByRole('button', { name: 'Clear this session' }));
  await user.click(screen.getByRole('button', { name: 'Explore a workplace situation' }));
  expect(screen.getByLabelText(/Describe the workplace situation/)).toHaveValue('');
});

it('announces service unavailability without inventing evidence counts', async () => {
  vi.mocked(api.health).mockRejectedValue(new Error('offline'));
  render(<AdjustWorkspace />);
  await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('The ADJUST service is not available.'));
  expect(screen.getByRole('button', { name: 'Guidance library —' })).toHaveTextContent('—');
});
