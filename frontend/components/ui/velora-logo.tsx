interface VeloraIconProps {
  size?: number;
  className?: string;
}

export function VeloraIcon({ size = 28, className }: VeloraIconProps) {
  const id = "vl-grad";
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 28 28"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      aria-hidden="true"
    >
      <defs>
        <linearGradient id={id} x1="0" y1="0" x2="28" y2="28" gradientUnits="userSpaceOnUse">
          <stop stopColor="#6366f1" />
          <stop offset="1" stopColor="#7c3aed" />
        </linearGradient>
      </defs>
      {/* Background */}
      <rect width="28" height="28" rx="6.5" fill={`url(#${id})`} />
      {/* Left input extension */}
      <line x1="4.5" y1="10" x2="8" y2="10" stroke="white" strokeWidth="1.25" strokeLinecap="round" strokeOpacity="0.45" />
      {/* Right input extension */}
      <line x1="20" y1="10" x2="23.5" y2="10" stroke="white" strokeWidth="1.25" strokeLinecap="round" strokeOpacity="0.45" />
      {/* Left V arm */}
      <line x1="8" y1="10" x2="14" y2="19" stroke="white" strokeWidth="1.75" strokeLinecap="round" />
      {/* Right V arm */}
      <line x1="20" y1="10" x2="14" y2="19" stroke="white" strokeWidth="1.75" strokeLinecap="round" />
      {/* Left node */}
      <circle cx="8" cy="10" r="2" fill="white" />
      {/* Right node */}
      <circle cx="20" cy="10" r="2" fill="white" />
      {/* Output node (slightly larger = gateway) */}
      <circle cx="14" cy="19" r="2.5" fill="white" />
    </svg>
  );
}

interface VeloraLogoProps {
  showTagline?: boolean;
  className?: string;
}

export function VeloraLogo({ showTagline = false, className }: VeloraLogoProps) {
  return (
    <div className={className}>
      <div className="flex items-center gap-2.5">
        <VeloraIcon size={28} />
        <div className={showTagline ? "flex flex-col" : undefined}>
          <span className="text-sm font-bold tracking-tight leading-none">Velora</span>
          {showTagline && (
            <span className="text-[9px] font-medium uppercase tracking-[0.12em] text-muted-foreground/50 mt-0.5 leading-none">
              AI Inference
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
