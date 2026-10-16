import { ModuleFrame } from '@/components/module-frame';
const sections = { assessment: 'employer-assessment', suggestions: 'adjustment-suggestions', conversation: 'conversation-guide', plan: 'adjustment-plan' };
export default function WorkplaceAdjustmentsPage() {
  return <><div className="integration-heading"><div><div className="eyebrow">ADJUST AI</div><h1>Workplace Adjustments</h1></div><p>Both people review their contribution before creating a shared plan.</p></div><ModuleFrame src="/modules/adjust" title="Adjust AI workplace adjustments" sections={sections} allowHandoff prerequisite="Start the employer assessment in Adjust AI. Suggestions, the conversation guide and the plan become available after both contributions are reviewed." /></>;
}
