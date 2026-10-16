'use client';

import { useId, useState } from 'react';

type BusinessSize = 'under_50' | '50_249' | '250_plus' | null;
type CostField = 'adjustments' | 'funding' | 'recruitment' | 'cover' | 'training' | 'productivity' | 'legal' | 'budget';
type Figures = Record<CostField, string>;

const emptyFigures: Figures = { adjustments: '', funding: '', recruitment: '', cover: '', training: '', productivity: '', legal: '', budget: '' };
const fields: Record<CostField, { label: string; hint: string; optional?: boolean }> = {
  adjustments: { label: 'Total cost of adjustments (£)', hint: 'Include the changes you are considering over the period you choose.' },
  funding: { label: 'Confirmed Access to Work contribution (£)', hint: 'Enter only funding already confirmed for these costs. Enter 0 if none is confirmed. Do not enter an estimated grant.' },
  recruitment: { label: 'Recruitment (£)', hint: 'Your estimated recruitment costs.' },
  cover: { label: 'Cover while the role is vacant (£)', hint: 'Your estimated cover or overtime costs.' },
  training: { label: 'Training (£)', hint: 'Your estimated training costs, including staff time.' },
  productivity: { label: 'Time to reach the same level (£)', hint: 'Your estimated cost while a new starter learns the role.' },
  legal: { label: 'Legal risk estimate (£, optional)', hint: 'Only enter your own quantified estimate. Leaving this blank means unquantified, not zero. Any figure is not a cap on liability.', optional: true },
  budget: { label: 'Available adjustment budget (£, optional)', hint: 'Your stated budget, used only to point you towards support if the net adjustment cost is higher.', optional: true },
};

// Work in whole pence. A blank entry is unknown; it must never silently become £0.
function pence(value: string): number | null {
  if (!/^\d+(?:\.\d{1,2})?$/.test(value)) return null;
  const [pounds, fraction = ''] = value.split('.');
  const amount = Number(pounds) * 100 + Number(fraction.padEnd(2, '0'));
  return Number.isSafeInteger(amount) ? amount : null;
}

const money = (amount: number) => new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'GBP' }).format(amount / 100);

export function CostComparison({ businessSize }: { businessSize: BusinessSize }) {
  const id = useId();
  const [figures, setFigures] = useState<Figures>({ ...emptyFigures });
  const amounts = Object.fromEntries(Object.entries(figures).map(([key, value]) => [key, pence(value)])) as Record<CostField, number | null>;
  const invalidFields = (Object.keys(figures) as CostField[]).filter(key => figures[key] !== '' && amounts[key] === null);
  const fundingTooHigh = amounts.adjustments !== null && amounts.funding !== null && amounts.funding > amounts.adjustments;
  const required: CostField[] = ['adjustments', 'funding', 'recruitment', 'cover', 'training', 'productivity'];
  const ready = required.every(key => amounts[key] !== null) && invalidFields.length === 0 && !fundingTooHigh;
  const keeping = ready ? amounts.adjustments! - amounts.funding! : null;
  const replacementCosts = ready ? amounts.recruitment! + amounts.cover! + amounts.training! + amounts.productivity! : null;
  const replacing = replacementCosts !== null ? replacementCosts + (amounts.legal ?? 0) : null;
  const totalTooLarge = replacing !== null && !Number.isSafeInteger(replacing);
  const overBudget = keeping !== null && amounts.budget !== null && keeping > amounts.budget;
  const sizeLabel = businessSize === 'under_50' ? 'under 50 employees' : businessSize === '50_249' ? '50–249 employees' : businessSize === '250_plus' ? '250+ employees' : 'not provided';

  function field(key: CostField) {
    const details = fields[key];
    const invalid = invalidFields.includes(key) || (key === 'funding' && fundingTooHigh);
    return <div className="cc-field" key={key}>
      <label htmlFor={`${id}-${key}`}>{details.label} {!details.optional && <span className="required-label">Required</span>}</label>
      <p className="field-hint" id={`${id}-${key}-help`}>{details.hint}</p>
      <input id={`${id}-${key}`} name={`private-${key}`} type="number" inputMode="decimal" min="0" step="0.01" required={!details.optional} autoComplete="off" value={figures[key]} aria-invalid={invalid || undefined} aria-describedby={`${id}-${key}-help${invalid ? ` ${id}-errors` : ''}`} onChange={event => setFigures(current => ({ ...current, [key]: event.target.value }))} />
    </div>;
  }

  return <section className="cc-private no-print" aria-labelledby={`${id}-heading`}>
    <h2 id={`${id}-heading`}>Employer cost comparison</h2>
    <div className="notice"><div><strong>Private to the employer. Not included in the link or combined plan.</strong><p>Use fictional figures for this demo. Figures stay in this screen and are cleared when you leave it or close the page.</p></div></div>
    <div className="notice warning"><div><strong>Your legal duties come first.</strong><p>If a condition may be a disability, you must consider and make reasonable adjustments required by law. Dismissing someone because of their disability risks a discrimination claim. Compensation for discrimination has no statutory cap.</p><p>Caring for someone does not itself create the disability reasonable adjustment duty. Carers have separate rights.</p><p><a href="https://www.acas.org.uk/reasonable-adjustments" target="_blank" rel="noreferrer">Acas: reasonable adjustments</a> · <a href="https://www.gov.uk/being-taken-to-employment-tribunal-by-employee/lose-the-case" target="_blank" rel="noreferrer">GOV.UK: tribunal compensation</a></p></div></div>
    <form className="form-card cc-form" onSubmit={event => event.preventDefault()} autoComplete="off">
      <p>Enter your own figures for the same time period in both columns. Enter 0 where you expect no cost. No costs or funding are assumed.</p>
      <div className="cc-columns">
        <fieldset><legend>Keeping them</legend>{field('adjustments')}{field('funding')}<p className="field-hint">Business size: {sizeLabel}. Only a confirmed contribution is deducted here. Access to Work does not pay for adjustments the employer is legally required to make.</p><a href="https://www.gov.uk/government/publications/access-to-work-guide-for-employers/access-to-work-factsheet-for-employers" target="_blank" rel="noreferrer">GOV.UK: Access to Work for employers</a></fieldset>
        <fieldset><legend>Replacing them</legend>{field('recruitment')}{field('cover')}{field('training')}{field('productivity')}{field('legal')}</fieldset>
      </div>
      {field('budget')}
      {(invalidFields.length > 0 || fundingTooHigh) && <p id={`${id}-errors`} role="alert">{invalidFields.length > 0 ? 'Enter non-negative amounts with no more than 2 decimal places.' : ''}{invalidFields.length > 0 && fundingTooHigh ? ' ' : ''}{fundingTooHigh ? 'The confirmed contribution cannot exceed the adjustment cost. Check the figures.' : ''}</p>}
      <div className="form-footer"><button type="button" className="button secondary" onClick={() => setFigures({ ...emptyFigures })}>Clear private figures</button></div>
    </form>
    <div className="form-card cc-result" aria-live="polite" aria-atomic="true">
      <h3>Your cost comparison</h3>
      {ready && !totalTooLarge ? <>
        <dl className="cc-totals"><div><dt>Keeping them — net adjustment cost</dt><dd>{money(keeping!)}</dd></div><div><dt>Replacing them — {amounts.legal === null ? 'entered costs, legal risk unquantified' : 'including your legal risk estimate'}</dt><dd>{money(replacing!)}</dd></div></dl>
        <p>{money(amounts.adjustments!)} adjustments − {money(amounts.funding!)} confirmed funding = {money(keeping!)} net adjustment cost.</p>
        <p>{amounts.legal === null ? 'Legal risk is unquantified and excluded from the replacement subtotal. It is not treated as zero.' : `Your legal risk estimate of ${money(amounts.legal)} is included. It is not a cap on liability.`} Actual discrimination compensation is uncapped.</p>
        <p>These are your figures for a conversation about support. A cost comparison does not decide what is reasonable or remove legal duties.</p>
      </> : <p>{totalTooLarge ? 'The combined amount is too large to calculate accurately. Check the figures.' : 'Complete the required amounts to see the comparison. Leave optional estimates blank when unknown.'}</p>}
    </div>
    {overBudget && <div className="notice warning" role="status"><div><strong>The net adjustment cost is above the budget you entered.</strong><p>Explore alternative adjustments and available support, and speak to Acas about your duties and a full and fair process. This comparison does not recommend dismissal.</p><a href="https://www.acas.org.uk/supporting-disabled-people/capability-and-performance-when-someone-is-disabled" target="_blank" rel="noreferrer">Acas: supporting disabled people and a fair process</a> · <a href="https://www.acas.org.uk/contact" target="_blank" rel="noreferrer">Contact Acas</a></div></div>}
  </section>;
}
