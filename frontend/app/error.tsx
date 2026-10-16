'use client';
import { ErrorState } from '@/components/ui';
export default function PageError({ reset }: { error: Error & { digest?: string }; reset: () => void }) { return <ErrorState message="This page could not be displayed. Your saved cases are still available. Reload the page to continue." retry={reset} />; }
