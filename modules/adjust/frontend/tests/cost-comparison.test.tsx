import { fireEvent, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { expect, it, vi } from 'vitest';
import { CostComparison } from '@/components/cost-comparison';

function amount(label: RegExp, value: string) {
  fireEvent.change(screen.getByRole('spinbutton', { name: label }), { target: { value } });
}

function completeRequired() {
  amount(/^Total cost of adjustments/, '1200.20');
  amount(/^Confirmed Access to Work contribution/, '200.10');
  amount(/^Recruitment/, '2500.20');
  amount(/^Cover while/, '1000.10');
  amount(/^Training/, '300');
  amount(/^Time to reach/, '700');
}

it('starts with blank private figures, no comparison and the fixed legal notice', () => {
  const { container } = render(<CostComparison businessSize="under_50" />);
  expect(container.firstElementChild).toHaveClass('no-print');
  expect(screen.getByText('Private to the employer. Not included in the link or combined plan.')).toBeVisible();
  for (const input of screen.getAllByRole('spinbutton')) expect(input).toHaveValue(null);
  expect(screen.getByText(/Complete the required amounts/)).toBeVisible();
  expect(screen.getByText(/Compensation for discrimination has no statutory cap/)).toBeVisible();
  expect(screen.getByText(/Caring for someone does not itself create/)).toBeVisible();
  expect(screen.getByText(/Business size: under 50 employees/)).toBeVisible();
});

it('subtracts only confirmed funding and shows a replacement subtotal with unquantified legal risk', () => {
  render(<CostComparison businessSize="50_249" />);
  completeRequired();
  expect(screen.getByText('£1,000.10')).toBeVisible();
  expect(screen.getByText('£4,500.30')).toBeVisible();
  expect(screen.getByText('Replacing them — entered costs, legal risk unquantified')).toBeVisible();
  expect(screen.getByText(/Legal risk is unquantified and excluded/)).toBeVisible();
  amount(/^Legal risk estimate/, '500.05');
  expect(screen.getByText('£5,000.35')).toBeVisible();
  expect(screen.getByText(/Your legal risk estimate of £500.05 is included/)).toBeVisible();
});

it('does not treat missing required funding or replacement costs as zero', () => {
  render(<CostComparison businessSize={null} />);
  completeRequired();
  amount(/^Confirmed Access to Work contribution/, '');
  expect(screen.getByText(/Complete the required amounts/)).toBeVisible();
  expect(screen.queryByText('£4,500.30')).not.toBeInTheDocument();
  amount(/^Confirmed Access to Work contribution/, '0');
  expect(screen.getByText('£4,500.30')).toBeVisible();
  amount(/^Training/, '');
  expect(screen.getByText(/Complete the required amounts/)).toBeVisible();
});

it('rejects funding above adjustments and invalid negative or fractional costs', () => {
  render(<CostComparison businessSize="250_plus" />);
  completeRequired();
  amount(/^Confirmed Access to Work contribution/, '1300');
  expect(screen.getByRole('alert')).toHaveTextContent('The confirmed contribution cannot exceed the adjustment cost.');
  expect(screen.queryByText('£4,500.30')).not.toBeInTheDocument();
  amount(/^Confirmed Access to Work contribution/, '100');
  amount(/^Recruitment/, '-1');
  expect(screen.getByRole('alert')).toHaveTextContent('Enter non-negative amounts');
  amount(/^Recruitment/, '100.001');
  expect(screen.getByRole('alert')).toBeVisible();
});

it('uses only the employer budget for the support signpost and clears all figures', async () => {
  const user = userEvent.setup();
  render(<CostComparison businessSize="under_50" />);
  completeRequired();
  expect(screen.queryByRole('status')).not.toBeInTheDocument();
  amount(/^Available adjustment budget/, '1000');
  const support = screen.getByRole('status');
  expect(support).toHaveTextContent('above the budget you entered');
  expect(within(support).getByRole('link', { name: /Acas: supporting/ })).toHaveAttribute('href', 'https://www.acas.org.uk/supporting-disabled-people/capability-and-performance-when-someone-is-disabled');
  amount(/^Available adjustment budget/, '1000.10');
  expect(screen.queryByRole('status')).not.toBeInTheDocument();
  await user.click(screen.getByRole('button', { name: 'Clear private figures' }));
  for (const input of screen.getAllByRole('spinbutton')) expect(input).toHaveValue(null);
  expect(screen.getByText(/Complete the required amounts/)).toBeVisible();
});

it('keeps financial entries out of network and browser storage and discards them on remount', () => {
  const fetchSpy = vi.spyOn(globalThis, 'fetch');
  const storageSpy = vi.spyOn(Storage.prototype, 'setItem');
  const { unmount } = render(<CostComparison businessSize="under_50" />);
  completeRequired();
  unmount();
  render(<CostComparison businessSize="under_50" />);
  for (const input of screen.getAllByRole('spinbutton')) expect(input).toHaveValue(null);
  expect(fetchSpy).not.toHaveBeenCalled();
  expect(storageSpy).not.toHaveBeenCalled();
});
