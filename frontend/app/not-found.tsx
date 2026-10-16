import Link from 'next/link';
import { ArrowRight } from 'lucide-react';
import { Button, Card } from '@/components/ui';
export default function NotFound() { return <Card className="empty"><div className="eyebrow">PAGE NOT FOUND</div><h1>Let’s find your way back.</h1><p>This workspace page does not exist. The resident portal can help you find support or choose your next step.</p><Button asChild style={{ marginTop: 24 }}><Link href="/">Return to the resident portal<ArrowRight size={16} /></Link></Button></Card>; }
