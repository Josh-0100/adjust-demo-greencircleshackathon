'use client';
export default function Error({ reset }: { reset: () => void }) {
  return <main className="recovery"><h1>We couldn’t open ADJUST</h1><p>Please try again. This module does not save workplace descriptions.</p><button className="button primary" onClick={reset}>Try again</button></main>;
}
