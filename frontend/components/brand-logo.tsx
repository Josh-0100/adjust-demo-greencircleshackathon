/** The user's original transparent logo, displayed without recolouring/cropping. */
export function BrandLogo({ className = '' }: { className?: string }) {
  return <span className={`brand-logo ${className}`}><span className="brand-logo-art"><img src="/adjust-logo.png" width={1354} height={390} alt="Adjust" /><span className="logo-ai">AI</span></span></span>;
}
