/** The supplied logo stays unchanged; only its displayed size varies. */
export function BrandLogo({ embedded = false, variant = 'sidebar' }: { embedded?: boolean; variant?: 'sidebar' | 'topbar' | 'footer' | 'plan' }) {
  return <span className={`adjust-logo adjust-logo--${variant}`}>
    <img src={`${embedded ? '/modules/adjust' : ''}/adjust-logo.png`} width={1354} height={390} alt="Adjust AI logo" />
    <span className="adjust-logo-ai" aria-hidden="true">AI</span>
  </span>;
}
