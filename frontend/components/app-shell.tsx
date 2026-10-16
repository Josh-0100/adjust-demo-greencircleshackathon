'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { createContext, useContext, useEffect, useState, useRef, type ReactNode } from 'react';
import { ArrowUpRight, BookOpen, Building2, ChevronRight, Compass, Fingerprint, FlaskConical, LayoutDashboard, Menu, Moon, PanelLeftClose, Play, ShieldCheck, Sparkles, Sun, TrendingUp, X } from 'lucide-react';
import type { Config, Module } from '@/lib/types';
import { useApi } from '@/hooks/use-api';
import { Badge, Button, ErrorState } from './ui';
import { BrandLogo } from './brand-logo';
const WorkspaceContext = createContext<{ config: Config | null; modules: Module[]; reload: () => void; loading: boolean; error: string | null }>({ config: null, modules: [], reload: () => {}, loading: true, error: null });
export const useWorkspace = () => useContext(WorkspaceContext);
const nav = [
  { href: '/portal', title: 'Resident portal', icon: Compass, label: 'Discover support' },
  { href: '/operations', title: 'Council operations', icon: LayoutDashboard, label: 'Manage enquiries' },
  { href: '/intelligence', title: 'Intelligence', icon: Sparkles, label: 'Evidence & workflows' },
  { href: '/impact', title: 'Impact', icon: TrendingUp, label: 'Measure what matters' },
  { href: '/admin', title: 'Configuration', icon: Building2, label: 'Adapt your challenge' },
];
const integratedNav = [
  { href: '/resident-support', title: 'Resident Support', icon: Compass, children: [
    ['assessment', 'Assessment'], ['local-services', 'Local Services'], ['training', 'Training'], ['employment-pathways', 'Employment Pathways'], ['action-plan', 'Action Plan'],
  ] },
  { href: '/workplace-adjustments', title: 'Workplace Adjustments', icon: Fingerprint, children: [
    ['assessment', 'Employer Assessment'], ['suggestions', 'Adjustment Suggestions'], ['conversation', 'Conversation Guide'], ['plan', 'Adjustment Plan'],
  ] },
  { href: '/council', title: 'Council Dashboard', icon: LayoutDashboard, children: [
    ['review', 'Case Review'], ['referrals', 'Referrals'], ['insights', 'Aggregated Insights'],
  ] },
];
export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const landing = pathname === '/';
  const modulePage = ['/resident-support', '/workplace-adjustments', '/council'].includes(pathname);
  const configuration = useApi<Config>('/config');
  const moduleData = useApi<{ modules: Module[] }>('/modules');
  const [mobileOpen, setMobileOpen] = useState(false);
  const menuButton = useRef<HTMLButtonElement>(null);
  const sidebar = useRef<HTMLElement>(null);
  const [dark, setDark] = useState(false);
  useEffect(() => { const preference = localStorage.getItem('civicforge-theme'); const isDark = preference === 'dark'; setDark(isDark); document.documentElement.classList.toggle('dark', isDark); }, []);
  useEffect(() => { setMobileOpen(false); }, [pathname]);
  function toggleTheme() { const next = !dark; setDark(next); document.documentElement.classList.toggle('dark', next); localStorage.setItem('civicforge-theme', next ? 'dark' : 'light'); }
  const config = configuration.data;
  const integrated = pathname === '/' || integratedNav.some(item => item.href === pathname);
  const workspaceBorough = integrated ? 'Bolton' : config?.challenge.borough || 'Greater Manchester';
  const workspaceTitle = integrated ? 'Adjust AI support hub' : config?.challenge.title || 'Adjust AI workspace';
  const active = [...integratedNav, ...nav].find(item => item.href === pathname);
  useEffect(() => {
    if (!mobileOpen) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    sidebar.current?.querySelector<HTMLElement>('a, button')?.focus();
    function keyboard(event: KeyboardEvent) {
      if (event.key === 'Escape') { setMobileOpen(false); menuButton.current?.focus(); }
      if (event.key !== 'Tab') return;
      const items = sidebar.current?.querySelectorAll<HTMLElement>('a, button');
      if (!items?.length) return;
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    document.addEventListener('keydown', keyboard);
    return () => { document.body.style.overflow = previousOverflow; document.removeEventListener('keydown', keyboard); };
  }, [mobileOpen]);
  function closeMenu() { setMobileOpen(false); menuButton.current?.focus(); }
  const reload = () => { void configuration.reload(); void moduleData.reload(); };
  return <WorkspaceContext.Provider value={{ config, modules: moduleData.data?.modules || [], reload, loading: configuration.loading || moduleData.loading, error: configuration.error || moduleData.error }}>
    <div className={`app-shell${landing ? ' is-home' : ''}${modulePage ? ' is-module' : ''}`}>
      {mobileOpen && <button className="sidebar-backdrop" aria-label="Close navigation" onClick={closeMenu} />}
      <aside id="workspace-navigation" ref={sidebar} hidden={!mobileOpen} className={`sidebar ${mobileOpen ? 'is-open' : ''}`} aria-label="Main navigation">
        <Link className="brand" href="/" aria-label="Adjust AI home"><BrandLogo /></Link>
        <Button className="mobile-close" variant="ghost" size="icon" aria-label="Close menu" onClick={closeMenu}><X size={20} /></Button>
        <div className="workspace-switch"><div className="workspace-avatar">{workspaceBorough.slice(0, 1)}</div><div><strong>{workspaceBorough}</strong><span title={workspaceTitle}>{workspaceTitle}</span></div><ChevronRight size={15} /></div>
        <nav aria-label="Adjust AI modules" onClick={event => { if ((event.target as HTMLElement).closest('a')) closeMenu(); }}><Link href="/" className="nav-item">Home</Link>{integratedNav.map(group => <div className="integration-nav-group" key={group.href}><Link href={group.href} className={`nav-item ${pathname === group.href ? 'active' : ''}`} aria-current={pathname === group.href ? 'page' : undefined}><group.icon size={19} /><span>{group.title}</span></Link><ul>{group.children.map(([hash, label]) => <li key={hash}><Link href={`${group.href}#${hash}`}>{label}</Link></li>)}</ul></div>)}</nav>
        <div className="nav-label">EXISTING WORKSPACE</div>
        <nav aria-label="Existing workspace" onClick={event => { if ((event.target as HTMLElement).closest('a')) closeMenu(); }}>{nav.map(item => <Link key={item.href} href={item.href} aria-current={pathname === item.href ? 'page' : undefined} className={`nav-item ${pathname === item.href ? 'active' : ''}`}><item.icon size={19} /><span>{item.title}</span>{pathname === item.href && <span className="nav-active-dot" />}</Link>)}</nav>
        <div className="sidebar-note" hidden><div className="mini-orbit"><Fingerprint size={25} /></div><strong>Built for public value.</strong><p>Evidence-led assistance.<br />People stay in control.</p><Link href="/intelligence">Explore the safeguards <ArrowUpRight size={13} /></Link></div>
        <Link href="/demo" className={`demo-nav ${pathname === '/demo' ? 'active' : ''}`}><Play size={17} /><span>Launch live demonstration</span><ArrowUpRight size={16} /></Link>
        <Button variant="ghost" className="drawer-theme" aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggleTheme}>{dark ? <Sun size={18} /> : <Moon size={18} />}Appearance</Button>
        <div className="sidebar-bottom"><span className="status-dot" /><span>{config?.demo_mode ? 'Synthetic demo workspace' : config ? 'Configured workspace' : 'Connecting to service'}</span><PanelLeftClose size={15} /></div>
      </aside>
      <div className="main-column">
        <header className="topbar"><div className="breadcrumb"><Link href="/" className="topbar-brand" aria-label="Adjust AI home"><BrandLogo /></Link><Button variant="ghost" size="icon" ref={menuButton} className="mobile-menu" aria-label={mobileOpen ? "Close menu" : "Open menu"} aria-expanded={mobileOpen} aria-controls="workspace-navigation" onClick={() => setMobileOpen(!mobileOpen)}><Menu size={20} /></Button>{!landing && <><ChevronRight size={14} /><strong className="route-title">{active?.title || 'Live demonstration'}</strong></>}</div><div className="topbar-actions">{!landing && <><Badge tone="lime"><FlaskConical size={12} />{config?.demo_mode ? 'DEMO MODE' : config ? 'WORKSPACE' : 'CONNECTING'}</Badge><Button variant="ghost" size="icon" aria-label={dark ? 'Switch to light mode' : 'Switch to dark mode'} onClick={toggleTheme}>{dark ? <Sun size={18} /> : <Moon size={18} />}</Button></>}<Link href={landing ? '#talk' : '/#talk'} className="advisor-link">Talk to an advisor</Link></div></header>
        <div className="demo-banner"><ShieldCheck size={15} /><span>{process.env.NEXT_PUBLIC_HOSTED_DEMO === '1' ? 'Fictional demonstration. Saved demo records may reset. AI guidance requires human verification.' : config?.demo_mode ? 'Safe to explore. This workspace uses fictional records; AI guidance requires human verification.' : 'Evidence-led assistance with human review. Confirm deployment access controls before using personal data.'}</span><span className="banner-end">Prototype · v1.0</span></div>
        <main id="main-content" className="page-content">{configuration.error && <ErrorState message={configuration.error} retry={reload} />}{moduleData.error && !configuration.error && <ErrorState message={moduleData.error} retry={reload} />}{children}</main>
        <footer className="footer"><span><BrandLogo className="footer-logo" />Adjust AI <span className="footer-dot">•</span> {workspaceBorough}</span><span><BookOpen size={13} />Transparent by design <span className="footer-dot">•</span> Human review first</span></footer>
      </div>
    </div>
  </WorkspaceContext.Provider>;
}
