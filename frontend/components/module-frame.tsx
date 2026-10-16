'use client';
import { useEffect, useRef, useState } from 'react';

type ModuleFrameProps = { src: string; title: string; sections: Record<string, string>; prerequisite?: string; allowHandoff?: boolean };
type FrameSource = { url: string; generation: number };
export function ModuleFrame({ src, title, sections, prerequisite = 'Complete the assessment to open this section.', allowHandoff = false }: ModuleFrameProps) {
  const frame = useRef<HTMLIFrameElement>(null);
  const [message, setMessage] = useState('');
  const [loaded, setLoaded] = useState(false);
  const [height, setHeight] = useState(640);
  const [documentRevision, setDocumentRevision] = useState(0);
  // Resolve an Adjust invitation before creating its document. Loading the bare
  // URL first races the module's existing one-time private-fragment capture.
  const [source, setSource] = useState<FrameSource | null>(allowHandoff ? null : { url: src, generation: 0 });
  useEffect(() => {
    if (!allowHandoff) return;
    function handoff() {
      const hash = window.location.hash;
      if (hash.startsWith('#case=')) {
        const fragment = hash.length <= 4100 ? hash : '#case=invalid';
        setLoaded(false);
        // A fresh document also lets a cleared session reopen the same link.
        setSource(previous => ({ url: `${src}${fragment}`, generation: (previous?.generation || 0) + 1 }));
        window.history.replaceState(null, '', window.location.pathname + window.location.search);
      } else setSource(previous => previous || { url: src, generation: 0 });
    }
    handoff();
    window.addEventListener('hashchange', handoff);
    return () => window.removeEventListener('hashchange', handoff);
  }, [allowHandoff, src]);
  useEffect(() => {
    const element = frame.current;
    if (!element) return;
    function ready() {
      // Static documents can finish loading before React attaches its handlers.
      if (element?.contentDocument?.readyState === 'complete' && element.contentWindow?.location.href !== 'about:blank') {
        setLoaded(true); setDocumentRevision(value => value + 1);
      }
    }
    element.addEventListener('load', ready);
    ready();
    return () => element.removeEventListener('load', ready);
  }, [source?.generation, source?.url]);
  useEffect(() => {
    if (!loaded) return;
    const document = frame.current?.contentDocument;
    if (!document?.body) return;
    let pending = 0;
    function measure() {
      cancelAnimationFrame(pending);
      pending = requestAnimationFrame(() => {
        if (!document?.body) return;
        // Measure layout only. Module input and case content never leave its document.
        const body = document.body;
        const next = Math.max(320, Math.ceil(Math.max(body.offsetHeight, body.scrollHeight)));
        setHeight(previous => Math.abs(previous - next) > 1 ? next : previous);
      });
    }
    const observer = new ResizeObserver(measure);
    observer.observe(document.body);
    document.addEventListener('load', measure, true);
    document.fonts?.ready.then(measure);
    measure();
    return () => { observer.disconnect(); document.removeEventListener('load', measure, true); cancelAnimationFrame(pending); };
  }, [loaded, source?.generation, documentRevision]);
  useEffect(() => {
    let located = false;
    let scheduled = 0;
    function navigate(section = window.location.hash.slice(1)) {
      const target = sections[section];
      if (!target) { setMessage(''); return; }
      // Only section identifiers and layout state are inspected. No form or
      // case data is read or transferred by the shared navigation.
      const element = frame.current?.contentDocument?.getElementById(target);
      if (element && !element.closest('[hidden], .hidden')) {
        if (!located && frame.current) {
          const top = window.scrollY + frame.current.getBoundingClientRect().top + element.getBoundingClientRect().top;
          window.scrollTo({ top: Math.max(0, top - 24) });
        }
        located = true; setMessage('');
      } else { located = false; setMessage(prerequisite); }
    }
    function schedule(section?: string) {
      cancelAnimationFrame(scheduled);
      // Give intrinsic iframe sizing time to commit before scrolling its host.
      scheduled = requestAnimationFrame(() => { scheduled = requestAnimationFrame(() => navigate(section)); });
    }
    function onHashChange() { located = false; schedule(); }
    function onSectionClick(event: MouseEvent) {
      const anchor = event.target instanceof Element ? event.target.closest('a[href]') : null;
      if (!anchor) return;
      const url = new URL(anchor.getAttribute('href') || '', window.location.href);
      const section = url.hash.slice(1);
      if (url.origin === window.location.origin && url.pathname === window.location.pathname && sections[section]) {
        located = false; schedule(section);
      }
    }
    window.addEventListener('hashchange', onHashChange);
    window.document.addEventListener('click', onSectionClick);
    const document = loaded ? frame.current?.contentDocument : null;
    const observer = document ? new MutationObserver(() => schedule()) : null;
    if (document) {
      observer?.observe(document, { subtree: true, childList: true, attributes: true, attributeFilter: ['class', 'hidden'] });
      schedule();
    }
    return () => { window.removeEventListener('hashchange', onHashChange); window.document.removeEventListener('click', onSectionClick); observer?.disconnect(); cancelAnimationFrame(scheduled); };
  }, [loaded, sections, prerequisite, documentRevision]);
  return <div className="module-container">{message && <p role="status" className="integration-note">{message}</p>}{source ? <iframe key={source.generation} ref={frame} src={source.url} title={title} className="module-frame" style={{ height }} scrolling="no" referrerPolicy="no-referrer" /> : <p role="status">Opening Adjust AI…</p>}</div>;
}
