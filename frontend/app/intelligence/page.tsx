'use client';
import { FileSearch, GitBranch, ShieldCheck } from 'lucide-react';
import { EnquiryComposer } from '@/components/enquiry-composer';
import { Badge, Card, PageHeading } from '@/components/ui';
export default function IntelligencePage() { return <><PageHeading eyebrow="INTELLIGENCE WORKSPACE" title="Evidence before answers." description="Inspect classification, retrieved passages and uncertainty in one auditable workflow." action={<Badge tone="teal">Demonstration staff role</Badge>} /><div className="principles-row"><Card><FileSearch size={20} /><div><strong>Grounded in approved sources</strong><span>Passages and provenance stay visible.</span></div></Card><Card><GitBranch size={20} /><div><strong>One shared workflow</strong><span>Deterministic rules where they work best.</span></div></Card><Card><ShieldCheck size={20} /><div><strong>People make the decisions</strong><span>Uncertainty triggers a review.</span></div></Card></div><EnquiryComposer mode="staff" /></>; }
