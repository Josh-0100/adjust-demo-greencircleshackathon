'use client';
import { ArrowUpRight, Compass, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { useWorkspace } from '@/components/app-shell';
import { EnquiryComposer } from '@/components/enquiry-composer';
import { Badge } from '@/components/ui';
export default function ResidentPortal() {
  const { config, modules } = useWorkspace();
  return <><section className="resident-hero"><div className="hero-copy"><div className="eyebrow"><span className="eyebrow-dot" />YOUR BOROUGH. YOUR NEXT STEP.</div><h1>Good support starts<br />with <em>being understood.</em></h1><p>{config?.challenge.description || 'From local services to new opportunities, find the support that fits your life — with clear guidance and evidence behind every step.'}</p><div className="hero-tags"><Badge tone="teal"><Compass size={12} />{config?.challenge.borough || 'Greater Manchester'}</Badge><span>{modules.filter(m => m.enabled).length} active support modules</span><span className="hero-dot">·</span><span>People first, always</span></div></div><div className="hero-visual" aria-hidden="true"><div className="orbit-ring orbit-one" /><div className="orbit-ring orbit-two" /><div className="orbit-ring orbit-three" /><div className="orbit-center"><Compass size={46} strokeWidth={1.2} /></div><div className="orbit-label label-one"><span className="tiny-dot" />Local knowledge</div><div className="orbit-label label-two"><Sparkles size={13} />Clear next steps</div><div className="orbit-point point-one" /><div className="orbit-point point-two" /><div className="hero-grid" /></div></section><EnquiryComposer /><div className="portal-bottom"><p>Built to adapt to the challenges that matter to {config?.challenge.borough || 'your borough'}.</p><Link href="/demo">See the complete civic workflow <ArrowUpRight size={15} /></Link></div></>;
}
