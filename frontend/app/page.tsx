import { ModuleFrame } from '@/components/module-frame';
const sections = { talk: 'talk' };
export default function LandingPage() {
  return <ModuleFrame src="/modules/adjust?entry=landing" title="Adjust AI workplace adjustments" sections={sections} allowHandoff prerequisite="Advice and support links are below the form." />;
}
