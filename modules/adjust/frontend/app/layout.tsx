import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'ADJUST · Better work, together',
  description: 'A workplace adjustments assistant for Bolton employers. Practical options, official sources, and an employee-led conversation.',
  robots: { index: false, follow: false },
};
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en-GB"><body><a className="skip-link" href="#main-content">Skip to main content</a>{children}</body></html>;
}
