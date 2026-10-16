'use client';

import { useEffect, useRef, useState, type FormEvent, type ReactNode } from 'react';
import { ArrowDown, ArrowLeft, ArrowRight, BookOpen, Check, CheckCheck, ChevronDown, ClipboardCheck, Clock3, ExternalLink, FileText, HeartHandshake, HelpCircle, LayoutDashboard, Leaf, LifeBuoy, LoaderCircle, LockKeyhole, MapPin, MessageCircle, Plus, Printer, RotateCcw, Search, ShieldCheck, SlidersHorizontal, Sparkles, Users, X } from 'lucide-react';
import { api, friendlyDate, localDate } from '@/lib/api';
import type { Health, Plan, Referral, Result, Scenario, Situation, Source } from '@/lib/types';
import { PlanPreview } from './plan-preview';

type Page = 'home' | 'situation' | 'clarify' | 'options' | 'conversation' | 'support' | 'plan' | 'library';
const EMPTY: Situation = { description: '', role: '', constraints: '', answers: {}, use_ai: false };
const STEPS: { page: Page; title: string; icon: typeof FileText }[] = [
  { page: 'situation', title: 'Describe the situation', icon: FileText },
  { page: 'clarify', title: 'Fill in the gaps', icon: HelpCircle },
  { page: 'options', title: 'Explore adjustments', icon: SlidersHorizontal },
  { page: 'conversation', title: 'Plan the conversation', icon: MessageCircle },
  { page: 'support', title: 'Find further support', icon: LifeBuoy },
  { page: 'plan', title: 'Your adjustment plan', icon: ClipboardCheck },
];
const EXAMPLES: Scenario[] = [
  { id: 'warehouse', label: 'Lifting and back pain', role: 'Warehouse picker', description: 'One of our warehouse pickers reports back pain and struggles with repeated lifting and picking. We want to understand which changes to the work might help.', constraints: 'Small team; limited space for new equipment.', expected: 'Source-supported handling options' },
  { id: 'office', label: 'Anxiety and office work', role: 'Office administrator', description: 'An office employee reports anxiety and struggles with computer work, competing deadlines and spontaneous phone calls in a noisy office. They would like clearer priorities.', constraints: 'No dedicated HR team; customer cover is needed.', expected: 'Workload, environment and communication options' },
  { id: 'multiple', label: 'Several barriers at work', role: 'Retail worker', description: 'A retail worker reports fatigue when standing for long periods, difficulty concentrating on written instructions and stress during busy customer calls. They would like to discuss changes.', constraints: 'Small shop with limited floor space.', expected: 'Options spanning several workplace barriers' },
  { id: 'vague', label: 'Not sure where to start', role: '', description: 'An employee is finding work difficult and we are not sure how to help.', constraints: '', expected: 'Clarification before recommendations' },
  { id: 'evidence-gap', label: 'Specialist evidence needed', role: 'Underwater technician', description: 'An underwater technician reports difficulty with pressure equalisation during saturation diving. We need specialist guidance about the diving task.', constraints: 'Specialist offshore equipment.', expected: 'No unsupported task-specific recommendations' },
];

function Button({ children, secondary = false, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement> & { secondary?: boolean }) {
  return <button {...props} className={`button ${secondary ? 'secondary' : 'primary'} ${props.className || ''}`}>{children}</button>;
}
function Heading({ eyebrow, title, children }: { eyebrow: string; title: string; children: ReactNode }) {
  return <div className="page-title"><span className="eyebrow">{eyebrow}</span><h1 tabIndex={-1}>{title}</h1><p>{children}</p></div>;
}
function Notice({ children, warning = false }: { children: ReactNode; warning?: boolean }) {
  return <div className={`notice ${warning ? 'warning' : ''}`}><ShieldCheck size={19} aria-hidden="true" /><div>{children}</div></div>;
}
function SourceList({ sources, ids }: { sources: Source[]; ids?: string[] }) {
  const selected = ids ? sources.filter(source => ids.includes(source.id)) : sources;
  return <div className="source-list">{selected.map(source => <details className="source" key={source.id}><summary><span className="source-label">{source.id}</span><span>{source.topic}<small>{source.publisher} · checked {friendlyDate(source.last_reviewed)}</small></span><ChevronDown size={16} aria-hidden="true" /></summary><div><p>{source.summary}</p><p className="small">Section: {source.evidence_locator}<br />Owner: {source.content_owner}<br />Review due: {friendlyDate(source.review_due)} · Editorial check only</p><a className="text-link" href={source.official_url} target="_blank" rel="noreferrer">Read official guidance <ExternalLink size={13} aria-hidden="true" /><span className="sr-only"> (opens in a new tab)</span></a></div></details>)}</div>;
}
function SupportCards({ referrals }: { referrals: Referral[] }) {
  return <div className="support-grid">{referrals.map(item => <article className="support-card" key={item.id}><div className="card-topline"><span className={`pill ${item.status === 'confirm_availability' ? 'amber' : ''}`}>{item.status === 'confirm_availability' ? 'Confirm availability' : 'Guidance checked'}</span><LifeBuoy size={20} aria-hidden="true" /></div><h2>{item.name}</h2><p>{item.provides}</p><h3>Who it may help</h3><p>{item.eligibility}</p><h3>How to access it</h3><p>{item.access}</p><div className="support-limitation">{item.limitations}</div><a className="text-link" href={item.official_url} target="_blank" rel="noreferrer">Visit official information <ExternalLink size={14} aria-hidden="true" /><span className="sr-only"> (opens in a new tab)</span></a><small>{item.publisher} · checked {friendlyDate(item.verified_on)}</small></article>)}</div>;
}

export function AdjustWorkspace() {
  const [page, setPage] = useState<Page>('home');
  const [situation, setSituation] = useState<Situation>(EMPTY);
  const [result, setResult] = useState<Result | null>(null);
  const [submitted, setSubmitted] = useState<Situation | null>(null);
  const [selected, setSelected] = useState<string[]>([]);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [reviewDate, setReviewDate] = useState('');
  const [nextSteps, setNextSteps] = useState('');
  const [reviewed, setReviewed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [health, setHealth] = useState<Health | null>(null);
  const [serviceError, setServiceError] = useState(false);
  const [sources, setSources] = useState<Source[]>([]);
  const [referrals, setReferrals] = useState<Referral[]>([]);
  const [examples, setExamples] = useState<Scenario[]>(EXAMPLES);
  const [query, setQuery] = useState('');
  const main = useRef<HTMLElement>(null);
  const activeRequest = useRef(0);
  const initiallyMounted = useRef(false);

  useEffect(() => {
    let active = true;
    Promise.allSettled([api.health(), api.knowledge(), api.support(), api.scenarios()]).then(items => {
      if (!active) return;
      const [h, k, s, e] = items;
      if (h.status === 'fulfilled') setHealth(h.value); else setServiceError(true);
      if (k.status === 'fulfilled') setSources(k.value.entries);
      if (s.status === 'fulfilled') setReferrals(s.value.referrals);
      if (e.status === 'fulfilled') setExamples(e.value.scenarios);
    });
    setReviewDate(localDate(14));
    return () => { active = false; };
  }, []);
  useEffect(() => {
    if (initiallyMounted.current) main.current?.querySelector('h1')?.focus();
    initiallyMounted.current = true;
  }, [page]);

  function navigate(next: Page) { if (busy) return; setPage(next); setError(''); window.scrollTo({ top: 0, behavior: 'instant' }); }
  function invalidate() { activeRequest.current++; setResult(null); setSubmitted(null); setSelected([]); setPlan(null); setReviewed(false); setNextSteps(''); setBusy(false); setError(''); }
  function edit(patch: Partial<Situation>) { invalidate(); setSituation(old => ({ ...old, ...patch, answers: {} })); }
  function example(scenario: Scenario) { invalidate(); setSituation({ ...EMPTY, description: scenario.description, role: scenario.role, constraints: scenario.constraints }); navigate('situation'); }
  function reset() { invalidate(); setSituation(EMPTY); setReviewDate(localDate(14)); navigate('home'); }
  async function analyse(event: FormEvent) {
    event.preventDefault(); setError(''); setBusy(true); setPlan(null);
    const id = ++activeRequest.current;
    try {
      const response = await api.analyse(situation);
      if (id !== activeRequest.current) return;
      setResult(response); setSubmitted(structuredClone(situation)); setSelected([]); setReviewed(false);
      setPage(response.status === 'clarification' ? 'clarify' : 'options');
      main.current?.focus();
    } catch (err) { if (id === activeRequest.current) setError(err instanceof Error ? err.message : 'Please try again.'); }
    finally { if (id === activeRequest.current) setBusy(false); }
  }
  async function generatePlan(event: FormEvent) {
    event.preventDefault();
    if (!submitted || !selected.length) { setError('Select at least one adjustment to discuss before making a plan.'); return; }
    setBusy(true); setError('');
    try { setPlan(await api.plan({ situation: submitted, selected_ids: selected, next_steps: nextSteps, review_date: reviewDate, human_reviewed: reviewed })); }
    catch (err) { setError(err instanceof Error ? err.message : 'Please try again.'); }
    finally { setBusy(false); }
  }
  function select(id: string) { setPlan(null); setReviewed(false); setSelected(old => old.includes(id) ? old.filter(value => value !== id) : old.length < 3 ? [...old, id] : old); }
  const isSafety = result?.status === 'emergency' || result?.status === 'urgent';
  const canExplore = !!result && !isSafety && result.status !== 'clarification';
  const currentStep = STEPS.findIndex(step => step.page === page);
  const filteredSources = sources.filter(source => `${source.topic} ${source.summary} ${source.publisher}`.toLowerCase().includes(query.toLowerCase()));

  return <div className="workspace">
    <aside className="sidebar" aria-label="ADJUST workspace navigation">
      <button className="brand" onClick={() => navigate('home')} aria-label="ADJUST home" disabled={busy}><span className="brand-mark"><SlidersHorizontal size={24} aria-hidden="true" /></span><span>ADJUST<span className="brand-sub">by CIVICFORGE AI</span></span></button>
      <div className="workspace-label"><span className="location-icon"><MapPin size={16} aria-hidden="true" /></span><div>Bolton workplace hub<small>For small employers</small></div></div>
      <div className="nav-label">YOUR WORKSPACE</div>
      <nav aria-label="Main"><button className={`nav-item ${page === 'home' ? 'active' : ''}`} aria-current={page === 'home' ? 'page' : undefined} onClick={() => navigate('home')} disabled={busy}><LayoutDashboard size={18} aria-hidden="true" />Overview</button>
        <button className={`nav-item ${page === 'situation' ? 'active' : ''}`} aria-current={page === 'situation' ? 'page' : undefined} onClick={() => navigate('situation')} disabled={busy}><Plus size={18} aria-hidden="true" />Explore a situation</button>
      </nav>
      <div className="nav-label journey-label">YOUR ADJUSTMENT JOURNEY</div>
      <nav aria-label="Adjustment journey" className="journey-nav">{STEPS.map((step, index) => {
        const enabled = !busy && (index === 0 || index === 1 && !!result && !isSafety || index >= 2 && index <= 3 && canExplore || index === 4 && !isSafety || index === 5 && result?.status === 'ready');
        return <button key={step.page} className={`journey-item ${page === step.page ? 'active' : ''}`} onClick={() => navigate(step.page)} disabled={!enabled} aria-current={page === step.page ? 'step' : undefined}><span className={`step-number ${index < currentStep && canExplore ? 'completed' : ''}`}>{index < currentStep && canExplore ? <Check size={12} aria-hidden="true" /> : String(index + 1).padStart(2, '0')}</span>{step.title}</button>;
      })}</nav>
      <nav aria-label="Resources" className="resource-nav"><button className={`nav-item ${page === 'library' ? 'active' : ''}`} aria-current={page === 'library' ? 'page' : undefined} onClick={() => navigate('library')} disabled={busy}><BookOpen size={18} aria-hidden="true" />Guidance library<span className="nav-count">{sources.length || '—'}</span></button></nav>
      <div className="sidebar-bottom"><span className="leaf-icon"><Leaf size={18} aria-hidden="true" /></span><strong>Better work, together.</strong><p>Practical changes start with listening.</p><span className="prototype-label"><span /> HACKATHON PROTOTYPE</span></div>
    </aside>

    <div className="main-shell"><header className="topbar"><div className="breadcrumbs">Workplace hub <span>/</span> <strong>{page === 'home' ? 'Overview' : page === 'library' ? 'Guidance library' : STEPS.find(step => step.page === page)?.title}</strong></div><div className="topbar-right"><span className="privacy-label"><LockKeyhole size={14} aria-hidden="true" />No details saved</span><span className="profile" aria-label="Employer workspace">E</span></div></header>
    <nav className="mobile-resources" aria-label="Mobile resources"><button onClick={() => navigate('library')} disabled={busy}><BookOpen size={15} aria-hidden="true" />Guidance library</button><button onClick={() => navigate('support')} disabled={busy || isSafety}><LifeBuoy size={15} aria-hidden="true" />Further support</button></nav><main id="main-content" ref={main} tabIndex={-1}>
      {serviceError && <div className="error-banner" role="alert"><strong>The ADJUST service is not available.</strong><span>Start the module using its launcher, then reload this page.</span><button onClick={() => window.location.reload()}>Reload</button></div>}
      {error && <div className="error-banner" role="alert"><strong>We couldn’t complete that step</strong><span>{error}</span><button onClick={() => setError('')} aria-label="Dismiss error"><X size={18} /></button></div>}
      {busy && <div className="busy-banner" role="status"><LoaderCircle size={17} className="spin" aria-hidden="true" />{page === 'plan' ? 'Preparing your discussion draft…' : 'Reviewing the situation and checking source references…'}</div>}

      {page === 'home' && <>
        <div className="welcome-line"><span className="eyebrow">A LITTLE SUPPORT. A MEANINGFUL DIFFERENCE.</span><span className="pill location-pill"><MapPin size={12} aria-hidden="true" /> Made for Bolton</span></div>
        <section className="hero"><div className="hero-copy"><span className="hero-kicker"><span /> WORKPLACE ADJUSTMENTS, MADE APPROACHABLE</span><h1 tabIndex={-1}>Small changes.<br /><span>A better day<br className="desktop-break" /> at work.</span></h1><p>Help your people do their best work. Explore practical adjustments, prepare a supportive conversation, and take the next step together.</p><div className="hero-actions"><Button onClick={() => navigate('situation')}>Explore a workplace situation <ArrowRight size={17} aria-hidden="true" /></Button><button className="text-button" onClick={() => document.getElementById('demo-scenarios')?.scrollIntoView({ behavior: 'smooth', block: 'center' })}>Try an example <ArrowDown size={15} aria-hidden="true" /></button></div><div className="hero-footnote"><CheckCheck size={16} aria-hidden="true" />No HR expertise needed <span>·</span> No employee names required</div></div>
          <div className="hero-illustration" aria-hidden="true"><div className="orbit orbit-one" /><div className="orbit orbit-two" /><div className="illustration-caption">EVERY WORKPLACE IS DIFFERENT.<br />SO IS EVERY PERSON.</div><div className="illustration-card illustration-understand"><span className="illustration-icon"><Users size={21} /></span><div><small>START WITH LISTENING</small><strong>Understand the person</strong></div><span className="mini-check"><Check size={12} /></span></div><div className="connecting-line" /><div className="illustration-card illustration-adjust"><span className="illustration-icon"><SlidersHorizontal size={22} /></span><div><small>MAKE ROOM FOR CHANGE</small><strong>Find what could help</strong></div><span className="adjust-dot" /></div><div className="connecting-line second" /><div className="illustration-card illustration-together"><span className="illustration-icon"><HeartHandshake size={22} /></span><div><small>TAKE THE NEXT STEP</small><strong>Move forward together</strong></div></div><div className="little-spark"><Sparkles size={25} /></div><span className="illustration-note">A conversation can change a working day.</span></div>
        </section>
        <section className="how-it-works" aria-labelledby="how-heading"><div className="section-heading"><h2 id="how-heading">From “where do I start?” to a practical next step.</h2><span>YOU BRING THE CONTEXT. WE HELP WITH THE NEXT STEP.</span></div><div className="process-grid">{[
          { icon: FileText, title: 'Tell us about the work', copy: 'Describe the role, the tasks and what is getting in the way. Start with what you know.' },
          { icon: SlidersHorizontal, title: 'Explore what could help', copy: 'Consider practical options linked to official guidance, with their limits made clear.' },
          { icon: MessageCircle, title: 'Make a plan, together', copy: 'Have the conversation. Agree what to try, who will help and when to review it.' },
        ].map((item, i) => <article className="process-card" key={item.title}><div className="process-top"><item.icon size={22} aria-hidden="true" /><span>0{i + 1}</span></div><h3>{item.title}</h3><p>{item.copy}</p></article>)}</div></section>
        <section id="demo-scenarios" className="examples-section" aria-labelledby="examples-heading"><div className="section-heading"><div><span className="eyebrow">NOT SURE WHAT TO WRITE?</span><h2 id="examples-heading">Start with an example</h2></div><span className="pill">Fictional demo situations</span></div><div className="examples-grid">{examples.map((item, i) => <button className="example-card" key={item.id} onClick={() => example(item)}><span className="example-icon">{i === 0 ? <SlidersHorizontal size={19} aria-hidden="true" /> : i === 1 ? <MessageCircle size={19} aria-hidden="true" /> : <FileText size={19} aria-hidden="true" />}</span><span><strong>{item.label}</strong><small>{item.expected}</small></span><ArrowRight size={17} aria-hidden="true" /></button>)}</div></section>
        <div className="source-strip"><div><ShieldCheck size={23} aria-hidden="true" /><span><strong>Grounded in official guidance</strong><small>Editorially checked sources. Individual professional review still matters.</small></span></div><div className="publisher-list"><span>Acas</span><span>HSE</span><span>GOV.UK</span><button onClick={() => navigate('library')} aria-label="Browse guidance library"><ArrowRight size={18} /></button></div></div>
        <Notice><strong>A starting point for a conversation.</strong> ADJUST offers options for human review. It does not diagnose, decide legal disability or fitness for work, or make employment decisions.</Notice>
      </>}

      {page === 'situation' && <>
        <Heading eyebrow="STEP 01 / UNDERSTAND THE WORK" title="What’s getting in the way?">You don’t need the perfect words. Tell us about the work and the barriers the employee has described.</Heading>
        <div className="form-layout"><form className="form-card" onSubmit={analyse}><fieldset disabled={busy}><legend className="sr-only">Workplace situation</legend><label htmlFor="description">Describe the workplace situation <span className="required-label">Required</span></label><p className="field-hint" id="description-help">Include the main tasks and what the employee finds difficult. Leave out names, contact details and unnecessary medical information.</p><textarea id="description" name="description" required minLength={20} maxLength={4000} rows={7} value={situation.description} onChange={e => edit({ description: e.target.value })} aria-describedby="description-help description-count" placeholder="For example: A warehouse picker reports back pain and finds repeated lifting difficult. We’re a small team and want to explore changes to the work." /><div className="character-count" id="description-count">{situation.description.length.toLocaleString()} / 4,000 characters</div>
          <label htmlFor="role">Job role <span className="optional">Optional</span></label><input id="role" maxLength={120} value={situation.role} onChange={e => edit({ role: e.target.value })} placeholder="For example: warehouse picker" />
          <label htmlFor="constraints">Anything we should take into account? <span className="optional">Optional</span></label><textarea id="constraints" rows={3} maxLength={500} value={situation.constraints} onChange={e => edit({ constraints: e.target.value })} placeholder="For example: team cover, budget, workspace or working hours" />
          {health?.ai_configured && <label className="checkbox-row"><input type="checkbox" checked={situation.use_ai} onChange={e => edit({ use_ai: e.target.checked })} /><span>Use the configured AI extraction service<small>This sends the description to that provider. Leave off to use local rules only.</small></span></label>}
          <div className="form-footer"><span><LockKeyhole size={14} aria-hidden="true" />Kept only in this session</span><Button type="submit">Explore possible adjustments <ArrowRight size={17} aria-hidden="true" /></Button></div></fieldset></form>
          <aside className="tips-column"><div className="tips-card"><span className="icon-tile"><MessageCircle size={23} aria-hidden="true" /></span><h2>Start with the person,<br />and the work.</h2><ul className="check-list"><li><Check size={16} aria-hidden="true" />What tasks do they do?</li><li><Check size={16} aria-hidden="true" />Which parts are difficult?</li><li><Check size={16} aria-hidden="true" />What have they said could help?</li></ul><p>A diagnosis isn’t needed to start this conversation.</p></div><div className="sample-picker"><h3>Or use a demo situation</h3>{examples.map(item => <button key={item.id} type="button" disabled={busy} onClick={() => example(item)}>{item.label}<ArrowRight size={14} aria-hidden="true" /></button>)}</div><div className="small emergency-hint"><strong>Immediate danger?</strong><p>Call 999 if someone’s life is at risk or they cannot be kept safe. ADJUST is not an emergency service.</p><a href="https://www.nhs.uk/nhs-services/mental-health-services/where-to-get-urgent-help-for-mental-health/" target="_blank" rel="noreferrer">NHS urgent support information</a></div></aside></div>
      </>}

      {page === 'clarify' && result && !isSafety && <>
        <Heading eyebrow="STEP 02 / FILL IN THE GAPS" title={result.status === 'clarification' ? 'A little more context would help.' : 'Check what we’ve understood.'}>Focus on the role and the work. Share only what is needed to explore useful changes.</Heading>
        <div className="form-layout"><form className="form-card" onSubmit={analyse}><fieldset disabled={busy}><legend className="sr-only">Clarification questions</legend>{result.questions.map(q => <div className="question-field" key={q.id}><label htmlFor={`question-${q.id}`}>{q.question}<span className={q.required ? 'required-label' : 'optional'}>{q.required ? 'Required' : 'Optional'}</span></label><p className="field-hint" id={`hint-${q.id}`}>{q.hint}</p><textarea id={`question-${q.id}`} rows={q.id === 'role' ? 2 : 3} required={q.required} maxLength={q.id === 'role' ? 120 : 500} aria-describedby={`hint-${q.id}`} value={situation.answers[q.id] || ''} onChange={e => { setSituation(old => ({ ...old, answers: { ...old.answers, [q.id]: e.target.value } })); setPlan(null); }} /></div>)}<div className="form-footer"><Button type="button" secondary onClick={() => navigate('situation')}><ArrowLeft size={16} aria-hidden="true" />Edit situation</Button><Button type="submit">{result.status === 'clarification' ? 'Review with this context' : 'Update options'}<ArrowRight size={16} aria-hidden="true" /></Button></div></fieldset></form><div className="tips-card"><h2>What we’ve picked up</h2><dl className="analysis-list"><dt>Role</dt><dd>{result.analysis.role || 'Not yet provided'}</dd><dt>Main tasks</dt><dd>{result.analysis.tasks.join(', ') || 'Not yet clear'}</dd><dt>Barriers described</dt><dd>{result.analysis.barriers.join(' ') || 'More context needed'}</dd></dl><p>This is extracted context for you to check, not an assessment of the employee.</p></div></div>
      </>}

      {page === 'options' && result && <>
        {isSafety ? <><Heading eyebrow="SAFETY FIRST" title={result.safety.title}>Get appropriate support before continuing with workplace adjustments.</Heading><div className="safety-card" role="alert" aria-label="Urgent safety guidance"><ShieldCheck size={32} aria-hidden="true" /><h2>{result.status === 'emergency' ? 'Seek immediate help' : 'Seek urgent professional help'}</h2><p>{result.safety.message}</p><ul>{result.safety.actions.map(action => <li key={action}>{action}</li>)}</ul>{result.safety.official_url && <a className="button primary" href={result.safety.official_url} target="_blank" rel="noreferrer">Read NHS support guidance <ExternalLink size={16} aria-hidden="true" /></a>}</div><Button secondary onClick={() => navigate('situation')}>Return to the situation</Button></> : <>
        <Heading eyebrow="STEP 03 / EXPLORE THE POSSIBILITIES" title={result.status === 'insufficient_evidence' ? 'This needs specialist guidance.' : 'Options worth a conversation.'}>{result.status === 'insufficient_evidence' ? 'The reviewed library does not have enough task-specific evidence. No adjustment recommendations have been generated.' : 'Every option links to reviewed guidance. Choose up to three to include in your discussion draft.'}</Heading>
        <div className="result-context"><div><span className="eyebrow">YOUR WORKPLACE CONTEXT</span><h2>{result.analysis.role || 'Role to confirm'}</h2><p>{result.analysis.tasks.join(' · ')}</p></div><button className="text-button" onClick={() => navigate('clarify')}>Review context <ArrowRight size={14} aria-hidden="true" /></button></div>
        <Notice warning={result.status === 'insufficient_evidence'}>{result.status === 'insufficient_evidence' ? 'Discuss the barriers with the employee and seek advice from a relevant competent professional. General conversation and referral guidance is available below.' : 'These are possible changes to discuss, not instructions. Check suitability, the employee’s preferences and any health and safety implications before implementation.'}</Notice>
        {result.analysis.constraints.length > 0 && <div className="constraint-note"><strong>Practical considerations:</strong> {result.analysis.constraints.join(' ')} <span>Check each option against these constraints and explore alternatives.</span></div>}
        <div className="recommendation-grid">{result.recommendations.map((item, i) => <article className={`recommendation-card ${selected.includes(item.id) ? 'selected' : ''}`} key={item.id}><div className="card-topline"><span className="option-number">OPTION {String(i + 1).padStart(2, '0')}</span><span className="pill">{item.effort}</span></div><h2>{item.title}</h2><p className="barrier-label">{item.barrier_addressed}</p><h3>What you could do</h3><ol>{item.steps.map(step => <li key={step}>{step}</li>)}</ol><div className="employee-question"><MessageCircle size={17} aria-hidden="true" /><p>{item.employee_questions[0]}</p></div><details className="limits"><summary>Limits and when to get advice<ChevronDown size={15} aria-hidden="true" /></summary><p>{item.limitations}</p><p>{item.referral_guidance}</p></details><SourceList sources={result.sources} ids={item.source_ids} /><label className="selection-row"><input type="checkbox" checked={selected.includes(item.id)} disabled={!selected.includes(item.id) && selected.length >= 3} onChange={() => select(item.id)} /><span>{selected.includes(item.id) ? 'Selected for discussion' : `Select for discussion: ${item.title}`}<small>Include in your draft plan</small></span></label></article>)}</div>
        <div className="step-actions"><Button secondary onClick={() => navigate('situation')}><ArrowLeft size={16} aria-hidden="true" />Edit situation</Button><span role="status">{selected.length} of 3 options selected</span><Button onClick={() => navigate('conversation')}>Prepare the conversation<ArrowRight size={17} aria-hidden="true" /></Button></div>
        <div className="analysis-note"><Sparkles size={15} aria-hidden="true" /><span>{result.provider} · {result.simulated ? 'Simulated analysis, no model call' : 'Exact input excerpts'} · Human review required{result.provider_note && <small>{result.provider_note}</small>}</span></div>
        </>}
      </>}

      {page === 'conversation' && result && !isSafety && <>
        <Heading eyebrow="STEP 04 / LISTEN, THEN AGREE" title="Make space for a good conversation.">Use this as a starting point. Let the employee guide what they share and what feels useful.</Heading>
        {result.conversation ? <><section className="conversation-opening"><span className="eyebrow">AN OPENING YOU CAN MAKE YOUR OWN</span><MessageCircle size={26} aria-hidden="true" /><blockquote>“{result.conversation.opening}”</blockquote><span className="small">Suggested wording · adapt it to your relationship and workplace</span></section><div className="conversation-grid"><section className="form-card"><h2>Ask. Listen. Understand.</h2><ol className="conversation-questions">{result.conversation.questions.map((q, i) => <li key={q}><span>0{i + 1}</span><p>{q}</p></li>)}</ol></section><section className="form-card"><h2>Explore, then agree</h2>{selected.length ? <ul className="selected-options">{result.recommendations.filter(r => selected.includes(r.id)).map(r => <li key={r.id}><Check size={16} aria-hidden="true" />{r.title}</li>)}</ul> : <p>No options selected. You can still start by understanding the barriers and what would help.</p>}<p className="agreement-quote">{result.conversation.agreement_summary}</p><h3>After the conversation</h3><ul>{result.conversation.follow_up.map(step => <li key={step}>{step}</li>)}</ul></section></div><details className="evidence-panel"><summary><BookOpen size={17} aria-hidden="true" />Sources behind this conversation guide<ChevronDown size={16} aria-hidden="true" /></summary><SourceList sources={result.sources} ids={result.conversation.source_ids} /></details></> : <Notice warning>The conversation sources are due for review or unavailable. Read current Acas guidance or seek professional advice before using a generated guide.</Notice>}
        <div className="step-actions"><Button secondary onClick={() => navigate('options')}><ArrowLeft size={16} aria-hidden="true" />Back to options</Button><Button onClick={() => navigate('support')}>Find further support<ArrowRight size={16} aria-hidden="true" /></Button></div>
      </>}

      {page === 'support' && <>
        <Heading eyebrow="STEP 05 / YOU DON’T HAVE TO WORK IT OUT ALONE" title="The right support for the next step.">Official routes for further advice, specialist input and local support. The employee should be involved in any referral.</Heading>
        <Notice>Availability, eligibility and funding depend on individual circumstances. These links do not submit an application or share employee information.</Notice><SupportCards referrals={result?.referrals.length ? result.referrals : referrals} />
        {!referrals.length && <p role="status">Support information is unavailable. Check the local service and reload this page.</p>}
        {result && canExplore && <div className="step-actions"><Button secondary onClick={() => navigate('conversation')}><ArrowLeft size={16} aria-hidden="true" />Conversation guide</Button>{result.status === 'ready' && <Button onClick={() => navigate('plan')}>Prepare your plan<ArrowRight size={16} aria-hidden="true" /></Button>}</div>}
      </>}

      {page === 'plan' && result?.status === 'ready' && <>
        <Heading eyebrow="STEP 06 / A PRACTICAL NEXT STEP" title={plan ? 'Your conversation, made actionable.' : 'Bring the next steps together.'}>{plan ? 'Review the discussion draft, then print it or save it as a PDF using your browser.' : 'Choose what to discuss, record next steps and set a review date. The employee’s agreement still needs to be confirmed.'}</Heading>
        {!plan ? <div className="form-layout"><form className="form-card" onSubmit={generatePlan}><fieldset disabled={busy}><legend className="sr-only">Adjustment plan details</legend><h2>Options for your draft</h2><p>Select one to three. Keep the first plan focused and practical.</p><div className="plan-selection">{result.recommendations.map(item => <label className="checkbox-row" key={item.id}><input type="checkbox" checked={selected.includes(item.id)} disabled={!selected.includes(item.id) && selected.length >= 3} onChange={() => select(item.id)} /><span>{item.title}</span></label>)}</div><label htmlFor="next-steps">Next steps to record <span className="required-label">Required</span></label><p className="field-hint" id="next-steps-help">Record what has been agreed, or mark actions as proposed. Include who will arrange them and when. Do not add names or medical details.</p><textarea id="next-steps" rows={5} minLength={5} maxLength={500} required aria-describedby="next-steps-help" value={nextSteps} onChange={e => { setNextSteps(e.target.value); setReviewed(false); }} placeholder="For example: Proposed — manager and employee to review the task together this week, then discuss suitable changes with the assessor." /><label htmlFor="review-date">Review date <span className="required-label">Required</span></label><input id="review-date" type="date" required min={localDate()} value={reviewDate} onChange={e => { setReviewDate(e.target.value); setReviewed(false); }} /><label className="checkbox-row human-review"><input type="checkbox" required checked={reviewed} onChange={e => setReviewed(e.target.checked)} /><span>I have reviewed the options, sources and limitations.<small>This creates a discussion draft. It does not confirm the employee has agreed or that changes are safe to implement.</small></span></label><div className="form-footer"><span>{selected.length} of 3 options selected</span><Button type="submit">Create discussion draft<FileText size={17} aria-hidden="true" /></Button></div></fieldset></form><aside className="tips-card"><ClipboardCheck size={28} aria-hidden="true" /><h2>A plan to work on together.</h2><p>Keep it focused on the work, the changes you will try, and how you will know they help.</p><ul className="check-list"><li><Check size={16} aria-hidden="true" />Employee participation</li><li><Check size={16} aria-hidden="true" />Clear next steps</li><li><Check size={16} aria-hidden="true" />A date to review</li><li><Check size={16} aria-hidden="true" />Sources and limitations</li></ul><p>Nothing is saved by ADJUST. Your browser’s PDF export creates a file on your device.</p></aside></div> : <><div className="export-toolbar"><span><CheckCheck size={19} aria-hidden="true" />Discussion draft ready · not saved</span><div><Button secondary onClick={() => { setPlan(null); setReviewed(false); }}>Edit draft</Button><Button onClick={() => window.print()}><Printer size={17} aria-hidden="true" />Print / save PDF</Button></div></div><PlanPreview plan={plan} /><Notice>Keep exported copies secure and share only with the people who need them. Printing or saving a PDF creates a copy outside ADJUST.</Notice></>}
      </>}

      {page === 'library' && <>
        <Heading eyebrow="THE EVIDENCE BEHIND THE OPTIONS" title="Guidance you can go back to.">A curated library of official workplace guidance. Every passage includes its publisher, source section, content owner and review dates.</Heading><div className="library-toolbar"><label className="search-field"><Search size={19} aria-hidden="true" /><span className="sr-only">Search guidance</span><input type="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search topics or publishers" /></label><span role="status">{filteredSources.length} reviewed passages</span></div><Notice>“Checked” means the page was inspected and the summary linked to a source section. It is an editorial check, not a guarantee of legal accuracy or an independent professional review. Out-of-date entries are excluded from recommendations.</Notice><div className="library-grid">{filteredSources.map(source => <article className="library-card" key={source.id}><div className="card-topline"><span className="source-label">{source.id}</span><span className="small">{source.publisher}</span></div><h2>{source.topic}</h2><p>{source.summary}</p><SourceList sources={[source]} /></article>)}</div>{!filteredSources.length && <div className="empty-state"><BookOpen size={27} aria-hidden="true" /><h2>No passages found</h2><p>Try a different topic, or check that the local service is running.</p></div>}
      </>}
    </main><footer className="app-footer"><span>ADJUST <span>·</span> Better work, together.</span><div><span className={`service-dot ${health ? 'online' : ''}`} />{health ? 'Local service connected' : 'Connecting to local service'}<span>·</span><button disabled={busy} onClick={reset}><RotateCcw size={12} aria-hidden="true" />Clear this session</button></div></footer></div>
  </div>;
}
