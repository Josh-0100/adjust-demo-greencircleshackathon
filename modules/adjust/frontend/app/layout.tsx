import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Adjust AI · Better work, together',
  description: 'Bring employee and employer perspectives together in one private, practical workplace conversation plan. A fictional Bolton demo.',
  robots: { index: false, follow: false },
};
export default function Layout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en-GB"><body><a className="skip-link" href="#main-content">Skip to main content</a>{children}</body></html>;
}
