import type { Metadata } from 'next';
import { AppShell } from '@/components/app-shell';
import './globals.css';
export const metadata: Metadata = { title: 'Adjust AI — Practical help to keep people in work', description: 'Practical workplace and resident support with sourced ideas, clear next steps and human review. Fictional demonstration.' };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en" suppressHydrationWarning><body><a className="skip-link" href="#main-content">Skip to main content</a><AppShell>{children}</AppShell></body></html>; }
