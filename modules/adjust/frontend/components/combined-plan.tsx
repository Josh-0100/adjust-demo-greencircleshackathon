import type { CombinedPlan as Plan, PlanItem } from '@/lib/case-api';
import { friendlyDate } from '@/lib/api';
import { BrandLogo } from './brand-logo';

function Items({ items }: { items: PlanItem[] }) {
  return <ul className="joint-plan-items">{items.map(item => <li key={item.id}><strong>{item.title}</strong><p>{item.detail} <a href={item.url} target="_blank" rel="noreferrer">Official guidance ↗</a></p></li>)}</ul>;
}
export function CombinedPlan({ plan, embedded = false }: { plan: Plan; embedded?: boolean }) {
  return <article id="adjustment-plan" className="plan-document joint-plan" aria-label="Printable combined plan">
    <header className="plan-heading"><div><BrandLogo embedded={embedded} variant="plan" /><span className="eyebrow">Adjust AI / BETTER WORK, TOGETHER</span><h2>{plan.title}</h2></div><span className="pill">Discussion draft</span></header>
    <div className="plan-meta"><span>Prepared {friendlyDate(plan.created_on)} · Both sides contributed</span><strong>Review {friendlyDate(plan.review_date)}</strong></div>
    <section><h3>1. Start now, at no cost</h3><p className="small">Agree safe changes using existing resources and staffing, with no additional spending. If cover or equipment costs extra, move it to options to discuss.</p><Items items={plan.start_now} /></section>
    <section id="adjustment-suggestions"><h3>2. Options to discuss</h3><Items items={plan.options} /></section>
    <section id="conversation-guide" className="joint-agenda"><h3>3. Your conversation agenda</h3><p className="joint-opening">“{plan.conversation.opening}”</p><ul>{plan.conversation.questions.map(question => <li key={question}>{question}</li>)}</ul><p><strong>Agree and write down: </strong>{plan.conversation.agree.join(' ')}</p></section>
    <section><h3>4. Help available</h3><Items items={plan.help} /></section>
    <section><h3>5. Check in together</h3><p>{friendlyDate(plan.review_date)}. Review what helped, what needs to change and the next check-in. Meet earlier if needed.</p></section>
    <footer><p>{plan.legal_note}</p><p>{plan.disclaimer}</p><p>Fictional demo · Private descriptions and employer cost figures are excluded. ADJUST has not saved this plan.</p></footer>
  </article>;
}
