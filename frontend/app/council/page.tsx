import { ModuleFrame } from '@/components/module-frame';
const sections = { review: 'queue-title', referrals: 'detail', insights: 'summary-title' };
export default function CouncilPage() {
  return <ModuleFrame src="/module-assets/bolton-connect/adviser.html" title="Adjust AI council dashboard" sections={sections} prerequisite="Open a consent-shared case in Case Review to inspect its service and referral guidance." />;
}
