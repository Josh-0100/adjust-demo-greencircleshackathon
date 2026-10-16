import { ModuleFrame } from '@/components/module-frame';
const sections = { assessment: 'assess-form', 'local-services': 'local-services', training: 'training', 'employment-pathways': 'employment-pathways', 'action-plan': 'result' };
export default function ResidentSupportPage() {
  return <ModuleFrame src="/module-assets/bolton-connect/index.html" title="Adjust AI resident support" sections={sections} />;
}
