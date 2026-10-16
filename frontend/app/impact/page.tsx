'use client';
import { RefreshCw } from 'lucide-react';
import { useApi } from '@/hooks/use-api';
import { useWorkspace } from '@/components/app-shell';
import { ImpactReport } from '@/components/impact-report';
import { Badge, Button, Card, ErrorState, Loading, PageHeading } from '@/components/ui';
import type { Impact } from '@/lib/types';
export default function ImpactPage() {
  const { config } = useWorkspace();
  const impact = useApi<Impact>('/impact', 'staff');
  return <><PageHeading eyebrow="PUBLIC VALUE, MEASURED" title="See what changes. Know what counts." description="A transparent view of activity, human review and potential operational value." action={<Button variant="secondary" onClick={impact.reload}><RefreshCw size={15} />Refresh measurements</Button>} /><div className="impact-context"><Badge tone="amber">Synthetic demonstration data</Badge><span>Measurement types stay visible. Estimates are never claimed as realised savings.</span></div>{impact.loading ? <Loading label="Measuring workspace activity…" /> : impact.error ? <ErrorState message={impact.error} retry={impact.reload} /> : impact.data && <ImpactReport data={impact.data} />}{config?.challenge.success_metrics.length ? <Card className="success-metrics"><div className="eyebrow">CONFIGURED CHALLENGE OUTCOMES</div><h2>What your borough wants to improve</h2><div>{config.challenge.success_metrics.map(metric => <Badge key={metric}>{metric}</Badge>)}</div><p className="muted small">These are target measures from challenge configuration. They are not measured achievements.</p></Card> : null}</>;
}
