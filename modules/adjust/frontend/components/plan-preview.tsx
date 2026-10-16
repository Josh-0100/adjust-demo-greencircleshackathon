import { friendlyDate } from '@/lib/api';
import type { Plan } from '@/lib/types';
import { BrandLogo } from './brand-logo';

export function PlanPreview({ plan, embedded = false }: { plan: Plan; embedded?: boolean }) {
  const uniqueSources = plan.sources.filter((source, index, all) => all.findIndex(s => s.official_url === source.official_url) === index);
  return <article className="plan-document" id="adjustment-plan" aria-label="Printable adjustment plan">
    <header className="plan-heading"><div><BrandLogo embedded={embedded} variant="plan" /><span className="eyebrow">Adjust AI / BOLTON</span><h2>{plan.title}</h2></div><span className="pill">{plan.status}</span></header>
    <div className="plan-meta"><span>Prepared {friendlyDate(plan.created_on)}</span><strong>Review together: {friendlyDate(plan.review_date)}</strong></div>
    <section><h3>1. Workplace situation</h3><p>{plan.workplace_situation}</p></section>
    <section><h3>2. Identified barriers</h3><ul>{plan.barriers.map((barrier, i) => <li key={i}>{barrier}</li>)}</ul></section>
    <section><h3>3. Options selected for discussion</h3><ol className="plan-options">{plan.adjustments.map(item => <li key={item.id}><strong>{item.title}</strong><span> · {item.source_ids.join(', ')}</span><p>{item.steps.join(' ')}</p><small>{item.limitations}</small></li>)}</ol></section>
    <section><h3>4. Employee discussion questions</h3><ul>{plan.discussion_questions.map(q => <li key={q}>{q}</li>)}</ul></section>
    <div className="plan-pair"><section><h3>5. Next steps recorded by manager</h3><p className="preserve-lines">{plan.agreed_next_steps}</p><small>Confirm the employee’s agreement before implementation.</small></section><section><h3>6. External support</h3><p>Acas: acas.org.uk/contact · Occupational health: discuss a suitable referral.</p><p>Access to Work: gov.uk/access-to-work. Eligibility and funding are not guaranteed.</p><p>WorkWell Bolton: confirm current availability with the provider.</p></section></div>
    <section><h3>7. Review date</h3><p>{friendlyDate(plan.review_date)} — agree an earlier check-in if the changes are not helping.</p></section>
    <section className="plan-sources"><h3>8. Sources</h3>{uniqueSources.map(source => <p key={source.id}><strong>{plan.sources.filter(s => s.official_url === source.official_url).map(s => s.id).join(', ')} · {source.publisher}</strong> — reviewed {source.last_reviewed}<br /><a href={source.official_url} target="_blank" rel="noreferrer">{source.official_url}</a></p>)}</section>
    <footer><h3>9. Professional guidance</h3><p>{plan.disclaimer}</p><p>Human review confirmed by the manager. This is not confirmation of employee agreement. No copy is saved by ADJUST.</p></footer>
  </article>;
}
