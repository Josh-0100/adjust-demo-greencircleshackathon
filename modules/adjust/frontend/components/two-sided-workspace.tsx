'use client';

import { useEffect, useRef, useState, type FormEvent } from 'react';
import { ArrowLeft, ArrowRight, Check, CheckCheck, Copy, ExternalLink, HeartHandshake, Leaf, LoaderCircle, LockKeyhole, MapPin, Menu, MessageCircle, Printer, RotateCcw, ShieldCheck, Users, Wallet } from 'lucide-react';
import { localDate } from '@/lib/api';
import { caseApi, decodeHandoff, encodeHandoff, type BusinessSize, type CaseHandoff, type CaseRole, type Catalogue, type CombinedPlan as Plan, type PreparedSide, type SupportKind } from '@/lib/case-api';
import { CombinedPlan } from './combined-plan';
import { BrandLogo } from './brand-logo';
import { CostComparison } from './cost-comparison';

type Stage = 'home' | 'describe' | 'review' | 'share' | 'plan' | 'safety' | 'cost';
const SIZES: { value: BusinessSize; label: string }[] = [{ value: 'under_50', label: 'Under 50 employees' }, { value: '50_249', label: '50–249 employees' }, { value: '250_plus', label: '250+ employees' }];
const EMPLOYEE_EXAMPLE = 'Fictional example: I work in a shop. Mornings are difficult and standing all day leaves me tired. A later start and regular breaks might help.';
const EMPLOYER_EXAMPLE = 'Fictional example: A member of our shop team finds standing all day difficult. We need customer cover at opening time and want to discuss what could help.';
const LANDING_EXAMPLES = {
  employee: [
    { label: 'Work and energy', description: EMPLOYEE_EXAMPLE, kind: 'health' },
    { label: 'A quieter workspace', description: 'Fictional example: I find it hard to concentrate in a busy office. A quieter space and time for focused work might help.', kind: 'health' },
    { label: 'Caring responsibilities', description: 'Fictional example: I care for my father without pay. Flexibility for appointments and unexpected changes to the morning routine might help.', kind: 'carer' },
  ],
  employer: [
    { label: 'Supporting a team member', description: EMPLOYER_EXAMPLE, kind: 'health' },
    { label: 'Flexible working', description: 'Fictional example: A member of our team needs more flexible hours. We need reliable cover during agreed opening hours and want to discuss a practical trial.', kind: 'health' },
    { label: 'Working within a budget', description: 'Fictional example: We want to support a team member who finds some tasks difficult. Our budget is limited, but we may be able to change tasks or breaks.', kind: 'health' },
  ],
} satisfies Record<CaseRole, { label: string; description: string; kind: SupportKind }[]>;

export function TwoSidedWorkspace({ embedded = false, landing = false }: { embedded?: boolean; landing?: boolean }) {
  const [sidebarOpen, setSidebarOpen] = useState(!embedded);
  const [stage, setStage] = useState<Stage>('home');
  const [landingRole, setLandingRole] = useState<CaseRole>('employer');
  const [role, setRole] = useState<CaseRole | null>(null);
  const [handoff, setHandoff] = useState<CaseHandoff | null>(null);
  const [catalogue, setCatalogue] = useState<Catalogue | null>(null);
  const [description, setDescription] = useState('');
  const [supportKind, setSupportKind] = useState<SupportKind>('health');
  const [businessSize, setBusinessSize] = useState<BusinessSize | null>(null);
  const [roleContext, setRoleContext] = useState('');
  const [practicalities, setPracticalities] = useState('');
  const [tried, setTried] = useState('');
  const [fictional, setFictional] = useState(false);
  const [reviewed, setReviewed] = useState(false);
  const [needs, setNeeds] = useState<string[]>([]);
  const [prepared, setPrepared] = useState<PreparedSide | null>(null);
  const [plan, setPlan] = useState<Plan | null>(null);
  const [reviewDate, setReviewDate] = useState('');
  const [shareUrl, setShareUrl] = useState('');
  const [copied, setCopied] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [returnStage, setReturnStage] = useState<Stage>('share');
  const incoming = useRef<string | null>(null);
  const captured = useRef(false);
  const operation = useRef(0);
  const main = useRef<HTMLElement>(null);
  const focused = useRef(false);

  useEffect(() => {
    let active = true;
    if (!captured.current) {
      captured.current = true;
      incoming.current = window.location.hash.startsWith('#case=') ? window.location.hash.slice(6) || 'invalid' : null;
      if (window.location.hash) window.history.replaceState(null, '', window.location.pathname + window.location.search);
    }
    setReviewDate(localDate(14));
    caseApi.catalogue().then(data => {
      if (!active) return;
      setCatalogue(data);
    }).catch(err => { if (active) setError(message(err)); });
    return () => { active = false; };
  }, []);

  useEffect(() => {
    if (!catalogue) return;
    let active = true;
    const known = catalogue;
    async function loadHandoff(encoded: string) {
      const id = ++operation.current;
      clearPrivate(); setPrepared(null); setNeeds([]); setHandoff(null); setPlan(null); setShareUrl(''); setRole(null); setBusinessSize(null); setSupportKind('health'); setReviewDate(localDate(14)); setReviewed(false); setCopied(false); setError(''); setBusy(true);
      try {
        const value = decodeHandoff(encoded, known);
        if (!active || id !== operation.current) return;
        setHandoff(value);
        const nextRole = value.employee && value.employer ? value.starter : value.employee ? 'employer' : 'employee';
        setRole(nextRole);
        if (nextRole === 'employer' && value.employer) setBusinessSize(value.employer.business_size);
        if (value.employee && value.employer) {
          setBusy(true);
          const date = value.review_date || localDate(14);
          if (date <= localDate()) {
            setError('The review date in this link is due. Choose a new date to prepare an updated discussion draft.');
            setReviewDate(localDate(14)); setStage('plan');
            return;
          }
          const result = await caseApi.plan({ employee: value.employee, employer: value.employer, review_date: date });
          if (!active || id !== operation.current) return;
          setReviewDate(date); setPlan(result); setStage('plan');
          setShareUrl(linkFor(value, known));
        } else setStage('describe');
      } catch (err) { if (active && id === operation.current) { setError(message(err)); setStage('home'); } }
      finally { if (active && id === operation.current) setBusy(false); }
    }
    function onHashChange() {
      if (!window.location.hash.startsWith('#case=')) return;
      const encoded = window.location.hash.slice(6) || 'invalid';
      window.history.replaceState(null, '', window.location.pathname + window.location.search);
      void loadHandoff(encoded);
    }
    if (incoming.current) { const encoded = incoming.current; incoming.current = null; void loadHandoff(encoded); }
    window.addEventListener('hashchange', onHashChange);
    return () => { active = false; window.removeEventListener('hashchange', onHashChange); };
  }, [catalogue]);

  useEffect(() => {
    if (focused.current) { main.current?.querySelector('h1')?.focus(); window.scrollTo({ top: 0, behavior: 'instant' }); }
    focused.current = true;
  }, [stage]);

  useEffect(() => {
    // Also clear memory if the browser keeps this page in its back/forward cache.
    const clear = () => { operation.current++; setDescription(''); setRoleContext(''); setPracticalities(''); setTried(''); setPrepared(null); setNeeds([]); setHandoff(null); setPlan(null); setShareUrl(''); setRole(null); setStage('home'); setBusinessSize(null); setSupportKind('health'); setFictional(false); setReviewed(false); setError(''); setBusy(false); incoming.current = null; };
    window.addEventListener('pagehide', clear);
    return () => window.removeEventListener('pagehide', clear);
  }, []);

  function message(err: unknown) { return err instanceof Error ? err.message : 'Please try again.'; }
  function linkFor(value: CaseHandoff, known = catalogue) {
    if (!known) throw new Error('Work needs are still loading. Please retry.');
    const path = embedded ? '/workplace-adjustments' : window.location.pathname;
    return `${window.location.origin}${path}#case=${encodeHandoff(value, known)}`;
  }
  function clearPrivate() { setDescription(''); setRoleContext(''); setPracticalities(''); setTried(''); setFictional(false); }
  function reset() {
    operation.current++; clearPrivate(); setPrepared(null); setNeeds([]); setHandoff(null); setPlan(null); setShareUrl(''); setRole(null); setStage('home'); setBusinessSize(null); setSupportKind('health'); setReviewed(false); setError(''); setBusy(false); setCopied(false); incoming.current = null;
  }
  function start(nextRole: CaseRole) { setRole(nextRole); setHandoff({ v: 1, starter: nextRole }); setStage('describe'); setError(''); }
  function useExample(carer = false) {
    setDescription(carer ? 'Fictional example: I care for my father without pay. I need flexibility for caring responsibilities, appointments and unexpected changes to the morning routine.' : role === 'employee' ? EMPLOYEE_EXAMPLE : EMPLOYER_EXAMPLE);
    if (role === 'employee') setSupportKind(carer ? 'carer' : 'health');
    if (role === 'employer') { setBusinessSize('under_50'); setRoleContext('Customer cover is needed during fixed opening hours.'); setPracticalities('We can swap some tasks, but have a limited budget.'); setTried('We have tried flexible breaks.'); }
    setFictional(true);
  }
  async function prepare(event: FormEvent) {
    event.preventDefault(); if (!role || !fictional) return;
    const id = ++operation.current; setBusy(true); setError('');
    try {
      const result = await caseApi.prepare({ role, description, support_kind: supportKind, business_size: role === 'employer' ? businessSize : null, role_context: roleContext, practicalities, tried });
      if (id !== operation.current) return;
      setPrepared(result); setReviewed(false); setNeeds(result.needs.map(need => need.id));
      setStage(result.status === 'review' ? 'review' : 'safety');
      if (result.status !== 'review') clearPrivate();
    } catch (err) { if (id === operation.current) setError(message(err)); }
    finally { if (id === operation.current) setBusy(false); }
  }
  async function confirmReview(event: FormEvent) {
    event.preventDefault(); if (!role || !handoff || !reviewed || (role === 'employer' && !businessSize)) return;
    const next: CaseHandoff = { ...handoff };
    if (role === 'employee') next.employee = { reviewed: true, need_ids: needs, support_kind: supportKind };
    else next.employer = { reviewed: true, need_ids: needs, business_size: businessSize! };
    const id = ++operation.current; setBusy(true); setError('');
    try {
      if (next.employee && next.employer) {
        next.review_date = reviewDate || localDate(14);
        const result = await caseApi.plan({ employee: next.employee, employer: next.employer, review_date: next.review_date });
        if (id !== operation.current) return;
        setPlan(result); setStage('plan');
      } else setStage('share');
      setHandoff(next); setShareUrl(linkFor(next)); clearPrivate(); setPrepared(null); setCopied(false);
    } catch (err) { if (id === operation.current) setError(message(err)); }
    finally { if (id === operation.current) setBusy(false); }
  }
  async function updateDate(date: string) {
    setReviewDate(date);
    if (!handoff?.employee || !handoff.employer || !date) return;
    const id = ++operation.current; setBusy(true); setError('');
    try {
      const result = await caseApi.plan({ employee: handoff.employee, employer: handoff.employer, review_date: date });
      if (id !== operation.current) return;
      const next = { ...handoff, review_date: date }; setPlan(result); setHandoff(next); setShareUrl(linkFor(next)); setCopied(false);
    } catch (err) { if (id === operation.current) setError(message(err)); }
    finally { if (id === operation.current) setBusy(false); }
  }
  async function copyLink() {
    try { await navigator.clipboard.writeText(shareUrl); setCopied(true); }
    catch { setError('Copy the link from the field below. Your browser did not allow automatic copying.'); }
  }
  const otherRole = role === 'employee' ? 'employer' : 'employee';
  const options = role === 'employee' ? catalogue?.employee_needs : catalogue?.employer_needs;
  const otherIds = role === 'employee' ? handoff?.employer?.need_ids : handoff?.employee?.need_ids;
  const otherOptions = role === 'employee' ? catalogue?.employer_needs : catalogue?.employee_needs;
  const progress = stage === 'describe' || stage === 'safety' ? 0 : stage === 'review' ? 1 : stage === 'share' ? 2 : stage === 'plan' ? 3 : -1;
  const onLanding = landing && stage === 'home';
  const adviserFooter = <footer id="talk" className="reference-footer no-print"><p>Adjust gives practical ideas for discussion, not a diagnosis or a legal decision.</p><p>For workplace advice, <a href="https://www.acas.org.uk/contact" target="_blank" rel="noreferrer">contact Acas<span className="sr-only"> (opens in a new tab)</span></a>.</p><p><LockKeyhole size={14} aria-hidden="true" />Nothing you type is saved by Adjust. You review work needs before sharing.</p><p>Fictional demo only. If someone may be at risk: Samaritans 116 123, NHS 111, or 999 in an emergency.</p></footer>;

  const linkPanel = (complete: boolean) => <section className="case-link-panel no-print" aria-label={complete ? 'Return link' : 'Invitation link'}>
    <div className="case-link-icon">{complete ? <CheckCheck size={26} aria-hidden="true" /> : <Users size={26} aria-hidden="true" />}</div>
    <h2>{complete ? `Send this plan back to your ${otherRole}` : `Invite your ${otherRole} to add their side`}</h2>
    <p>{complete ? 'Both contributions are in. This return link opens the same combined plan for the person who started.' : 'They’ll see only your reviewed work needs and add their own perspective. The plan is made when both sides are in.'}</p>
    <label htmlFor="case-link">{complete ? 'Combined plan return link' : 'Link to send yourself'}</label>
    <div className="case-link-row"><input id="case-link" readOnly value={shareUrl} onFocus={event => event.target.select()} /><button className="button primary" onClick={copyLink}><Copy size={16} aria-hidden="true" />{copied ? 'Copied' : 'Copy link'}</button></div>
    {copied && <p role="status">Link copied. Share it only with the other person.</p>}
    <p className="case-share-note"><LockKeyhole size={14} aria-hidden="true" />The link contains reviewed selections{handoff?.employer ? ' and business size' : ''}. Keep medical details out of your message. Treat the link as private.</p>
    {!complete && <a className="text-link" href={shareUrl} target="_blank" rel="noreferrer">Try the other side in a new tab <ExternalLink size={14} aria-hidden="true" /><span className="sr-only">(opens in a new tab)</span></a>}
  </section>;

  return <div className={`workspace case-workspace${embedded ? ' embedded-workspace' : ''}${onLanding ? ' reference-landing' : ''}${sidebarOpen && !onLanding ? '' : ' sidebar-collapsed'}`}>
    <aside id="adjust-workspace-sidebar" className="sidebar no-print" aria-label="ADJUST workspace navigation" hidden={!sidebarOpen || onLanding}>
      <button className="brand" onClick={reset} disabled={busy} aria-label="ADJUST home"><span><BrandLogo embedded={embedded} /></span></button>
      <div className="workspace-label"><span className="location-icon"><MapPin size={16} aria-hidden="true" /></span><div>Bolton workplace hub<small>For employees & employers</small></div></div>
      <div className="nav-label">BETTER WORK, TOGETHER</div>
      <nav aria-label="Your shared journey" className="case-journey">{['Describe your side', 'Review what you share', 'Invite the other person', 'One combined plan'].map((text, index) => <div key={text} className={`case-step ${index === progress ? 'active' : ''} ${index < progress ? 'complete' : ''}`} aria-current={index === progress ? 'step' : undefined}><span>{index < progress ? <Check size={14} aria-hidden="true" /> : `0${index + 1}`}</span>{text}</div>)}</nav>
      {role && <div className="case-contributions"><span className="nav-label">TWO PERSPECTIVES</span><p><span className={handoff?.employee ? 'done' : ''}>{handoff?.employee ? <Check size={14} /> : <Users size={14} />} Employee</span><small>{handoff?.employee ? 'Reviewed and shared' : 'Contribution pending'}</small></p><p><span className={handoff?.employer ? 'done' : ''}>{handoff?.employer ? <Check size={14} /> : <Users size={14} />} Employer</span><small>{handoff?.employer ? 'Reviewed and shared' : 'Contribution pending'}</small></p></div>}
      {role === 'employer' && businessSize && stage !== 'safety' && <button className={`nav-item case-cost-button ${stage === 'cost' ? 'active' : ''}`} disabled={busy} onClick={() => { if (stage !== 'cost') setReturnStage(stage); setStage('cost'); }}><Wallet size={18} aria-hidden="true" />Private cost comparison</button>}
      <div className="sidebar-bottom"><ShieldCheck size={20} aria-hidden="true" /><strong>Your words stay private.</strong><p>Only reviewed work needs are shared. No diagnosis, original description or private cost figures.</p><span className="pill">Fictional demo only</span></div>
    </aside>
    <div className="main-shell">
      {!onLanding && <header className="topbar no-print"><div className="workspace-toolbar"><button type="button" className="sidebar-toggle" aria-controls="adjust-workspace-sidebar" aria-expanded={sidebarOpen} aria-label={sidebarOpen ? 'Close Adjust AI sidebar' : 'Open Adjust AI sidebar'} onClick={() => setSidebarOpen(open => !open)}><Menu size={19} aria-hidden="true" /></button><BrandLogo embedded={embedded} variant="topbar" /><div className="breadcrumbs">{embedded ? 'Adjust AI' : 'Your workplace'} <span>/</span><strong>{stage === 'home' ? 'Welcome' : stage === 'plan' ? 'Combined plan' : stage === 'cost' ? 'Employer only' : role === 'employee' ? 'Employee perspective' : 'Employer perspective'}</strong></div></div><div className="privacy-label"><LockKeyhole size={13} aria-hidden="true" />Nothing saved by ADJUST</div></header>}
      <main id="main-content" tabIndex={-1} ref={main}>
        {error && <div className="error-banner no-print" role="alert"><ShieldCheck size={18} aria-hidden="true" /><span>{error}</span><button onClick={() => setError('')} aria-label="Dismiss error">×</button>{!catalogue && <button onClick={() => window.location.reload()}>Retry connection</button>}</div>}
        {busy && <div className="busy-banner no-print" role="status"><LoaderCircle className="spin" size={18} aria-hidden="true" />{stage === 'describe' ? 'Checking safety and preparing work needs…' : 'Preparing your sourced conversation plan…'}</div>}

        {onLanding && <div className="reference-content">
          <section className="reference-hero" aria-labelledby="reference-title">
            <p className="reference-eyebrow">Built for Greater Manchester · Bolton</p>
            <h1 id="reference-title" tabIndex={-1}>Practical help to keep people in work</h1>
            <p className="reference-subtitle">Describe the situation in your own words. Adjust helps you review work needs and prepare a practical conversation plan together.</p>
          </section>
          <form className="reference-card" autoComplete="off" onSubmit={event => { event.preventDefault(); start(landingRole); }}>
            <label htmlFor="landing-description">Describe the situation</label>
            <p id="landing-description-hint" className="reference-form-hint">Use fictional details for this demo. Leave out names and identifying details.</p>
            <textarea id="landing-description" aria-describedby="landing-description-hint" rows={5} required minLength={20} maxLength={4000} value={description} onChange={event => setDescription(event.target.value)} placeholder={landingRole === 'employee' ? 'What is making work difficult, and what might help?' : 'What would help you support someone at work?'} />
            <div className="reference-chips" aria-label="Try a fictional situation">{LANDING_EXAMPLES[landingRole].map(example => <button key={example.label} type="button" onClick={() => { setDescription(example.description); setSupportKind(example.kind); }}>{example.label}</button>)}</div>
            <button className="reference-go" type="submit" disabled={!catalogue || busy}>Get my plan <ArrowRight size={19} aria-hidden="true" /></button>
            <p className="reference-next-step">Next: check your details and choose what to share. A combined plan needs both perspectives.</p>
          </form>
          <fieldset className="reference-mode"><legend>I am an</legend><div className="reference-segment">{([{ value: 'employee', label: 'Employee' }, { value: 'employer', label: 'Business' }] as const).map(option => <button key={option.value} type="button" aria-pressed={landingRole === option.value} onClick={() => setLandingRole(option.value)}>{option.label}</button>)}</div></fieldset>
          {adviserFooter}
        </div>}

        {stage === 'home' && !landing && <>
          <div className="welcome-line"><span className="eyebrow">A BETTER WORKING DAY STARTS WITH A CONVERSATION</span><span className="location-pill"><MapPin size={11} aria-hidden="true" />Made for Bolton</span></div>
          <section className="case-hero"><div><span className="hero-kicker"><Leaf size={12} aria-hidden="true" />PRACTICAL CHANGES. SHARED UNDERSTANDING.</span><h1 tabIndex={-1}>Two perspectives.<br />One way forward.</h1><p>When work feels difficult, a good conversation can change things. Bring both sides together to find a practical plan that works for you.</p><div className="case-hero-note"><ShieldCheck size={17} aria-hidden="true" />Your health details stay yours. You choose what to share.</div></div><div className="case-visual" aria-hidden="true"><div className="case-orbit" /><div className="case-person employee-person"><Users size={25} /><strong>Your experience</strong><span>What would help at work?</span></div><div className="case-person employer-person"><MessageCircle size={25} /><strong>Your workplace</strong><span>What can we make possible?</span></div><div className="case-joint"><HeartHandshake size={22} /><span>A plan to discuss together</span><CheckCheck size={16} /></div></div></section>
          <div className="section-heading case-start-heading"><h2>Where would you like to start?</h2><span>Either person can take the first step.</span></div>
          <div className="case-role-grid"><button className="case-role-card" disabled={!catalogue || busy} onClick={() => start('employee')}><span className="icon-tile"><Users size={23} aria-hidden="true" /></span><h2>I’m an employee</h2><p>Share what’s hard at work and what might help, including if you’re an unpaid carer.</p><span className="case-card-action">Start with my experience <ArrowRight size={18} aria-hidden="true" /></span></button><button className="case-role-card" disabled={!catalogue || busy} onClick={() => start('employer')}><span className="icon-tile"><MessageCircle size={23} aria-hidden="true" /></span><h2>I’m an employer</h2><p>Set out what the role needs and what’s practical. Invite your employee to add their side.</p><span className="case-card-action">Start with my workplace <ArrowRight size={18} aria-hidden="true" /></span></button></div>
          <div className="case-how"><div><span>01</span><h3>Speak freely</h3><p>Describe your side in your own words.</p></div><div><span>02</span><h3>Choose what to share</h3><p>Edit plain-language work needs before inviting anyone.</p></div><div><span>03</span><h3>Make a plan, together</h3><p>Both sides contribute before a plan is created.</p></div></div>
          <div className="notice"><LockKeyhole size={18} aria-hidden="true" /><div>Fictional examples only. No account, saved cases or external AI. Closing or reloading clears this page. A copied link retains the reviewed selections it contains.</div></div>
        </>}

        {stage === 'describe' && role && <>
          <div className="page-title" id={role === 'employer' ? 'employer-assessment' : 'employee-assessment'}><span className="eyebrow">01 / YOUR PERSPECTIVE</span><h1 tabIndex={-1}>{role === 'employee' ? 'What’s getting in the way?' : 'Tell us about your workplace.'}</h1><p>{role === 'employee' ? 'Use your own words. You can mention a condition if you want to. Your original words will never be shown to your employer.' : 'Describe the situation, the role and what’s practical. Your original words will never be shown to the employee.'}</p></div>
          {otherIds && <section className="case-received"><span className="eyebrow">YOUR {otherRole.toUpperCase()} HAS SHARED</span><h2>Their reviewed work needs</h2>{otherIds.length ? <ul>{otherIds.map(id => <li key={id}>{otherOptions?.find(item => item.id === id)?.text}</li>)}</ul> : <p>They chose to share no specific work needs. You can still add your perspective.</p>}<p className="small">Read-only. Their private description is never shared.{role === 'employee' && handoff?.employer && ` Business size: ${SIZES.find(item => item.value === handoff.employer!.business_size)?.label}.`}</p></section>}
          <div className="form-layout"><form className="form-card" onSubmit={prepare} autoComplete="off"><fieldset disabled={busy}><legend className="sr-only">Your private description</legend>
            <label htmlFor="private-description">{role === 'employee' ? 'What’s happening and what’s hard at work?' : 'Describe the situation'} <span className="required-label">Required</span></label><p className="field-hint" id="private-hint">Use a fictional example. Leave out names, addresses and identifying details. 20–4,000 characters.</p><textarea id="private-description" aria-describedby="private-hint" rows={6} required minLength={20} maxLength={4000} value={description} onChange={event => setDescription(event.target.value)} placeholder={role === 'employee' ? 'For example: I find mornings difficult and standing all day is hard. A later start might help…' : 'For example: A team member is finding parts of the role difficult. We would like to understand what would help…'} />
            {role === 'employee' ? <><label htmlFor="support-kind">What would you like support with?</label><select id="support-kind" value={supportKind} onChange={event => setSupportKind(event.target.value as SupportKind)}><option value="health">My own health or work needs</option><option value="carer">Unpaid caring responsibilities</option><option value="both">Both</option></select><p className="field-hint">The plan includes different rights for carers. This choice is included in your reviewed handoff.</p></> : <><label htmlFor="business-size">Business size <span className="required-label">Required</span></label><select id="business-size" required value={businessSize || ''} onChange={event => setBusinessSize(event.target.value as BusinessSize)}><option value="" disabled>Select number of employees</option>{SIZES.map(size => <option key={size.value} value={size.value}>{size.label}</option>)}</select><label htmlFor="role-context">What does the role involve, and what can’t change?</label><textarea id="role-context" rows={3} maxLength={700} value={roleContext} onChange={event => setRoleContext(event.target.value)} placeholder="For example: customer cover, essential tasks or fixed opening hours" /><label htmlFor="practicalities">What’s practical for the business?</label><textarea id="practicalities" rows={3} maxLength={700} value={practicalities} onChange={event => setPracticalities(event.target.value)} placeholder="For example: flexibility available, budget or space" /><label htmlFor="already-tried">Anything already tried?</label><textarea id="already-tried" rows={2} maxLength={700} value={tried} onChange={event => setTried(event.target.value)} placeholder="For example: flexible breaks or a task swap" /></>}
            <label className="checkbox-row"><input type="checkbox" required checked={fictional} onChange={event => setFictional(event.target.checked)} /><span>I’m using fictional details for this demo.</span></label>
            <div className="form-footer"><span><LockKeyhole size={14} aria-hidden="true" />Your words stay private</span><button className="button primary" type="submit">Review what will be shared <ArrowRight size={17} aria-hidden="true" /></button></div>
          </fieldset></form><aside className="tips-column"><div className="tips-card"><MessageCircle size={26} aria-hidden="true" /><h2>Start with the work.</h2><p>{role === 'employee' ? 'What parts of your day are hard? What would make them easier? You don’t need a diagnosis to start.' : 'What needs to get done? Where is there room to change how, where or when it happens?'}</p><p>ADJUST turns this into suggested work needs. Check them carefully before sharing.</p><span className="pill">Local rules · no model call</span></div><div className="sample-picker"><h3>Try a fictional example</h3><button type="button" disabled={busy} onClick={() => useExample()}>Work and energy <ArrowRight size={14} aria-hidden="true" /></button>{role === 'employee' && <button type="button" disabled={busy} onClick={() => useExample(true)}>Unpaid caring <ArrowRight size={14} aria-hidden="true" /></button>}</div><div className="small emergency-hint"><strong>Need urgent support?</strong><p>Immediate danger: 999. Urgent mental health help in England: NHS 111, mental health option. To talk: Samaritans 116 123, free, day or night.</p><a href="https://www.nhs.uk/nhs-services/mental-health-services/where-to-get-urgent-help-for-mental-health/" target="_blank" rel="noreferrer">NHS urgent support</a></div></aside></div>
        </>}

        {stage === 'review' && role && <>
          <div className="page-title"><span className="eyebrow">02 / YOU CHOOSE WHAT’S SHARED</span><h1 tabIndex={-1}>Your words. Your choice.</h1><p>Only the work needs below will be shared. Change any item or remove it. Your original description and any medical details stay private.</p></div>
          <div className="form-layout"><form className="form-card" onSubmit={confirmReview}><fieldset disabled={busy}><legend className="sr-only">Review shared work needs</legend><div className="card-topline"><h2>{role === 'employee' ? 'My work needs' : 'Workplace needs and constraints'}</h2><span className="pill">Shared after review</span></div><p className="field-hint">Suggestions come from a fixed set of plain-language work statements. Use the list to edit them; no private text can enter the link.</p>
            <div className="case-needs-list">{needs.map((id, index) => <div className="case-need" key={`${index}-${id}`}><label htmlFor={`need-${index}`}>Work need {index + 1}</label><div><select id={`need-${index}`} value={id} onChange={event => { setNeeds(old => old.map((item, i) => i === index ? event.target.value : item)); setReviewed(false); }}>{options?.map(option => <option key={option.id} value={option.id} disabled={needs.includes(option.id) && option.id !== id}>{option.text}</option>)}</select><button className="case-remove" type="button" onClick={() => { setNeeds(old => old.filter((_, i) => i !== index)); setReviewed(false); }} aria-label={`Remove work need ${index + 1}`}>Remove</button></div></div>)}</div>
            {!needs.length && <p className="case-empty">No specific needs selected. You can continue with a general conversation or add a work need.</p>}
            <button className="text-button case-add" type="button" disabled={needs.length >= (options?.length || 0)} onClick={() => { const next = options?.find(option => !needs.includes(option.id)); if (next) setNeeds(old => [...old, next.id]); setReviewed(false); }}>+ Add a work need</button>
            {role === 'employee' ? <p className="case-reviewed-extra"><strong>Support to include:</strong> {supportKind === 'carer' ? 'Unpaid caring responsibilities' : supportKind === 'both' ? 'Own work needs and unpaid caring responsibilities' : 'Own health or work needs'}. No condition name is included.</p> : <p className="case-reviewed-extra"><strong>Business size to share:</strong> {SIZES.find(size => size.value === businessSize)?.label}</p>}
            <label className="checkbox-row human-review"><input required type="checkbox" checked={reviewed} onChange={event => setReviewed(event.target.checked)} /><span>I’ve reviewed these items and I’m happy to share them with my {otherRole}.<small>Reviewing these items does not mean agreeing to any adjustment.</small></span></label><div className="form-footer"><button className="button secondary" type="button" onClick={() => setStage('describe')}><ArrowLeft size={16} aria-hidden="true" />Edit my description</button><button className="button primary" type="submit">{otherIds ? 'Create our combined plan' : 'Create invitation link'}<ArrowRight size={17} aria-hidden="true" /></button></div>
          </fieldset></form><aside className="tips-card"><LockKeyhole size={26} aria-hidden="true" /><h2>Shared needs.<br />Private details.</h2><ul className="check-list"><li><Check size={16} aria-hidden="true" />Only the items you review</li><li><Check size={16} aria-hidden="true" />No original description</li><li><Check size={16} aria-hidden="true" />No condition or medical details</li><li><Check size={16} aria-hidden="true" />No employer cost figures</li></ul><p>The matching is a demo using local rules. It can miss what matters. Edit the list until it reflects what you want to discuss.</p></aside></div>
        </>}

        {stage === 'share' && <><div className="page-title"><span className="eyebrow">03 / MAKE SPACE FOR BOTH SIDES</span><h1 tabIndex={-1}>Your side is ready.</h1><p>Now invite your {otherRole}. No plan is produced until you have both contributed.</p></div>{linkPanel(false)}<div className="notice"><MessageCircle size={18} aria-hidden="true" /><div>There’s no saved case or automatic update. After adding their side, the other person sends a return link so you can open the plan too. Keep this invitation until then.</div></div></>}

        {stage === 'plan' && !plan && handoff?.employee && handoff.employer && <><div className="page-title"><span className="eyebrow">REVIEW TOGETHER</span><h1 tabIndex={-1}>Time for a fresh check-in.</h1><p>Both reviewed contributions are available. Set a new review date to prepare an updated discussion draft.</p></div><form className="form-card" onSubmit={event => { event.preventDefault(); void updateDate(reviewDate); }}><label htmlFor="renew-review-date">New review date</label><input id="renew-review-date" type="date" required min={localDate(1)} value={reviewDate} disabled={busy} onChange={event => setReviewDate(event.target.value)} /><div className="form-footer"><button className="button primary" type="submit" disabled={busy}>Prepare updated plan <ArrowRight size={16} aria-hidden="true" /></button></div></form></>}

        {stage === 'plan' && plan && <>
          <div className="page-title no-print"><span className="eyebrow">04 / TWO PERSPECTIVES, ONE PLAN</span><h1 tabIndex={-1}>Ready for a better conversation.</h1><p>Both sides have contributed. These are proposed changes to discuss and agree together.</p></div>
          <div className="export-toolbar no-print"><label className="case-review-date" htmlFor="joint-review-date">Review together on<input id="joint-review-date" type="date" min={localDate(1)} max={`${new Date().getFullYear() + 1}-12-31`} value={reviewDate} disabled={busy} onChange={event => void updateDate(event.target.value)} /></label><button className="button primary" disabled={busy || reviewDate !== plan.review_date} onClick={() => window.print()}><Printer size={17} aria-hidden="true" />Print / save one-page PDF</button></div>
          <CombinedPlan plan={plan} embedded={embedded} />
          {linkPanel(true)}<div className="notice no-print"><ShieldCheck size={18} aria-hidden="true" /><div>Saving a PDF creates a copy on your device. Keep it and the return link private. No original descriptions or employer cost figures are included.</div></div>
        </>}

        {stage === 'safety' && prepared && <><div className="page-title"><span className="eyebrow">SAFETY FIRST</span><h1 tabIndex={-1}>{prepared.safety.title}</h1><p>Pause the work adjustment flow and get support now.</p></div><section className="safety-card" role="alert" aria-label="Urgent safety guidance"><ShieldCheck size={32} aria-hidden="true" /><h2>Support is available</h2><p>{prepared.safety.message}</p><ul>{prepared.safety.actions.map(action => <li key={action}>{action}</li>)}</ul><div className="case-crisis-links"><a href="tel:999">999 · immediate danger</a><a href="tel:111">NHS 111 · urgent help</a><a href="tel:116123">Samaritans · 116 123</a></div><a className="text-link" href={prepared.safety.official_url || 'https://www.nhs.uk/nhs-services/mental-health-services/where-to-get-urgent-help-for-mental-health/'} target="_blank" rel="noreferrer">NHS urgent support guidance <ExternalLink size={15} aria-hidden="true" /></a><p className="small">These phrase checks are limited and can miss a crisis. Use the support routes whenever you need them.</p></section><button className="button secondary" onClick={reset}>Clear and return home</button></>}

        {stage === 'cost' && role === 'employer' && <div className="no-print"><div className="page-title"><span className="eyebrow">EMPLOYER ONLY / PRIVATE FIGURES</span><h1 tabIndex={-1}>Understand the costs.</h1><p>Use your own figures to compare costs and prepare for a fair conversation.</p></div><CostComparison businessSize={businessSize} /><button className="button secondary" onClick={() => setStage(returnStage)}><ArrowLeft size={16} aria-hidden="true" />Back to the shared flow</button></div>}
        {landing && !onLanding && adviserFooter}
      </main>
      {!onLanding && <footer className="app-footer no-print"><span className="footer-brand"><BrandLogo embedded={embedded} variant="footer" /><span>Better work, together.</span></span><div><span className={`service-dot ${catalogue ? 'online' : ''}`} />{catalogue ? 'Local rules ready' : 'Connecting to guidance'}<span>·</span><button onClick={reset} disabled={busy}><RotateCcw size={12} aria-hidden="true" />Clear this session</button></div></footer>}
    </div>
  </div>;
}
