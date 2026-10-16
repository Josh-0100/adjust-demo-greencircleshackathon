import { forwardRef, type ButtonHTMLAttributes, type HTMLAttributes, type InputHTMLAttributes, type ReactNode, type TextareaHTMLAttributes } from 'react';
import { Slot } from '@radix-ui/react-slot';
import { cva, type VariantProps } from 'class-variance-authority';
import { AlertCircle, ArrowRight, Loader2, RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';
const buttonVariants = cva('button', { variants: { variant: { default: 'button-primary', secondary: 'button-secondary', ghost: 'button-ghost', danger: 'button-danger' }, size: { default: '', sm: 'button-sm', icon: 'button-icon' } }, defaultVariants: { variant: 'default', size: 'default' } });
export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement>, VariantProps<typeof buttonVariants> { asChild?: boolean }
export const Button = forwardRef<HTMLButtonElement, ButtonProps>(({ className, variant, size, asChild = false, ...props }, ref) => { const Comp = asChild ? Slot : 'button'; return <Comp ref={ref} className={cn(buttonVariants({ variant, size }), className)} {...props} />; });
Button.displayName = 'Button';
export function Badge({ children, tone = 'neutral', className }: { children: ReactNode; tone?: 'neutral' | 'teal' | 'lime' | 'amber' | 'red'; className?: string }) { return <span className={cn('badge', `badge-${tone}`, className)}>{children}</span>; }
export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) { return <div className={cn('card', className)} {...props} />; }
export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(({ className, ...props }, ref) => <input ref={ref} className={cn('input', className)} {...props} />);
Input.displayName = 'Input';
export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(({ className, ...props }, ref) => <textarea ref={ref} className={cn('input textarea', className)} {...props} />);
Textarea.displayName = 'Textarea';
export function Field({ label, htmlFor, hint, children }: { label: string; htmlFor: string; hint?: string; children: ReactNode }) { return <div className="field"><label htmlFor={htmlFor}>{label}</label>{children}{hint && <p className="field-hint">{hint}</p>}</div>; }
export function PageHeading({ eyebrow, title, description, action }: { eyebrow: string; title: string; description: string; action?: ReactNode }) { return <div className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{description}</p></div>{action && <div className="heading-action">{action}</div>}</div>; }
export function Loading({ label = 'Loading your workspace…' }: { label?: string }) { return <div className="loading" role="status"><Loader2 size={22} className="spin" /><span>{label}</span></div>; }
export function ErrorState({ message, retry }: { message: string; retry?: () => void }) { return <div className="error-state" role="alert"><AlertCircle size={21} /><div><strong>We couldn’t complete that request</strong><p>{message}</p>{retry && <Button variant="secondary" size="sm" onClick={retry}><RefreshCw size={14} />Try again</Button>}</div></div>; }
export function Empty({ title, description }: { title: string; description: string }) { return <Card className="empty"><ArrowRight size={26} /><h3>{title}</h3><p>{description}</p></Card>; }
export function Stat({ label, value, detail, icon, tone = '' }: { label: string; value: ReactNode; detail: string; icon?: ReactNode; tone?: string }) { return <Card className={cn('stat', tone)}><div className="stat-label">{label}{icon}</div><div className="stat-value">{value}</div><p>{detail}</p></Card>; }
