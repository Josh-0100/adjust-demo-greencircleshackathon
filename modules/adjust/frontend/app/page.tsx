import { TwoSidedWorkspace } from '@/components/two-sided-workspace';

export default async function Page({ searchParams }: { searchParams: Promise<{ entry?: string | string[] }> }) {
  const query = await searchParams;
  return <TwoSidedWorkspace embedded={process.env.ADJUST_EMBEDDED === '1'} landing={query.entry === 'landing'} />;
}
