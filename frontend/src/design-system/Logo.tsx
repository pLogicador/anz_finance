/**
 * ANZ Finance's own mark -- same visual grammar confirmed across the
 * Syncron ecosystem (rounded-square badge, one accent color, one simple
 * stroke glyph tied to the product), built fresh for ANZ, not copied from
 * any sibling app. See public/favicon.svg for the browser-tab version of
 * the same mark (that one needs its own filled badge since a tab icon
 * can't assume any page background; this one is transparent so it sits
 * naturally on the app's own dark surface).
 */
export function LogoMark({ size = 28, className }: { size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" role="img" aria-label="ANZ Finance" className={className}>
      <rect x="1" y="1" width="30" height="30" rx="8" stroke="#34d399" strokeWidth="1.5" fill="#0a0d0c" />
      <path
        d="M7 23 L13 17.5 L17 20 L22 12.5 L25 9"
        stroke="#34d399"
        strokeWidth="2.4"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      <circle cx="25" cy="9" r="2.4" fill="#34d399" />
    </svg>
  )
}

/** Mark + wordmark, for the header/landing page. Just the mark alone (`LogoMark`) is enough at small sizes (e.g. a tab bar). */
export function Logo({ size = 28, className }: { size?: number; className?: string }) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className ?? ''}`}>
      <LogoMark size={size} />
      <span className="text-base font-semibold tracking-tight text-neutral-50">ANZ Finance</span>
    </span>
  )
}
