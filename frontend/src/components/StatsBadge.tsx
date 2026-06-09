import React from "react";

// ─── Types ────────────────────────────────────────────────────────────────────

type BadgeVariant = "stars" | "forks" | "issues" | "watchers" | "default";

interface StatsBadgeProps {
  /** The numeric value to display */
  value: number;
  /** Label shown below or beside the number */
  label: string;
  /** Controls the pill's accent color — maps to GitFit palette */
  variant?: BadgeVariant;
  /** Optional icon (React node / emoji / SVG) */
  icon?: React.ReactNode;
  /** Additional Tailwind classes */
  className?: string;
}

// ─── Color map — GitFit palette ───────────────────────────────────────────────
//
//  navy   #1B2A4A   — primary brand dark
//  red    #C0392B   — accent red (brush stroke)
//  blue   #3A6BC8   — mid blue (brush stroke)
//  muted  #6B7A99   — secondary text / subtle variant
//
const VARIANT_STYLES: Record<
  BadgeVariant,
  {
    pill: string;       // pill background + border
    dot: string;        // left accent dot
    value: string;      // large number color
    label: string;      // small label color
  }
> = {
  stars: {
    pill:  "bg-[#EEF1F8] border border-[#3A6BC8]/20",
    dot:   "bg-[#3A6BC8]",
    value: "text-[#1B2A4A]",
    label: "text-[#3A6BC8]",
  },
  forks: {
    pill:  "bg-[#F8EEEE] border border-[#C0392B]/20",
    dot:   "bg-[#C0392B]",
    value: "text-[#1B2A4A]",
    label: "text-[#C0392B]",
  },
  issues: {
    pill:  "bg-[#F0EEF8] border border-[#6B4FA8]/20",
    dot:   "bg-[#6B4FA8]",
    value: "text-[#1B2A4A]",
    label: "text-[#6B4FA8]",
  },
  watchers: {
    pill:  "bg-[#EEF5F8] border border-[#1B8A9A]/20",
    dot:   "bg-[#1B8A9A]",
    value: "text-[#1B2A4A]",
    label: "text-[#1B8A9A]",
  },
  default: {
    pill:  "bg-[#F2F4F7] border border-[#1B2A4A]/15",
    dot:   "bg-[#6B7A99]",
    value: "text-[#1B2A4A]",
    label: "text-[#6B7A99]",
  },
};

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Compact number formatter: 1234 → "1.2k", 1200000 → "1.2M" */
function formatCount(n: number): string {
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000)     return `${(n / 1_000).toFixed(1)}k`;
  return String(n);
}

// ─── Default icons per variant ────────────────────────────────────────────────

const DEFAULT_ICONS: Record<BadgeVariant, string> = {
  stars:    "★",
  forks:    "⑂",
  issues:   "⊙",
  watchers: "◎",
  default:  "·",
};

// ─── Component ────────────────────────────────────────────────────────────────

export const StatsBadge: React.FC<StatsBadgeProps> = ({
  value,
  label,
  variant = "default",
  icon,
  className = "",
}) => {
  const styles = VARIANT_STYLES[variant];
  const displayIcon = icon ?? DEFAULT_ICONS[variant];

  return (
    <span
      className={[
        // pill shape
        "inline-flex items-center gap-2",
        "rounded-full px-3.5 py-1.5",
        "font-mono text-sm",
        "select-none whitespace-nowrap",
        // subtle shadow matching the frosted-card aesthetic
        "shadow-sm",
        styles.pill,
        className,
      ].join(" ")}
      role="status"
      aria-label={`${label}: ${value}`}
    >
      {/* Accent dot */}
      <span
        className={[
          "inline-block w-[7px] h-[7px] rounded-full flex-shrink-0",
          styles.dot,
        ].join(" ")}
        aria-hidden="true"
      />

      {/* Icon */}
      <span
        className={["text-[13px] leading-none", styles.value].join(" ")}
        aria-hidden="true"
      >
        {displayIcon}
      </span>

      {/* Value */}
      <span
        className={[
          "font-semibold text-[13px] leading-none tracking-tight",
          styles.value,
        ].join(" ")}
      >
        {formatCount(value)}
      </span>

      {/* Divider */}
      <span className="text-[#1B2A4A]/20 text-[11px]" aria-hidden="true">
        ·
      </span>

      {/* Label */}
      <span
        className={[
          "text-[11px] uppercase tracking-widest font-medium leading-none",
          styles.label,
        ].join(" ")}
      >
        {label}
      </span>
    </span>
  );
};

// ─── Convenience group component ─────────────────────────────────────────────
//
//  <StatsBadgeGroup stars={1200} forks={340} issues={12} />
//

interface StatsBadgeGroupProps {
  stars?:    number;
  forks?:    number;
  issues?:   number;
  watchers?: number;
  className?: string;
}

export const StatsBadgeGroup: React.FC<StatsBadgeGroupProps> = ({
  stars,
  forks,
  issues,
  watchers,
  className = "",
}) => (
  <div className={["flex flex-wrap gap-2", className].join(" ")}>
    {stars    != null && <StatsBadge value={stars}    label="stars"    variant="stars"    />}
    {forks    != null && <StatsBadge value={forks}    label="forks"    variant="forks"    />}
    {issues   != null && <StatsBadge value={issues}   label="issues"   variant="issues"   />}
    {watchers != null && <StatsBadge value={watchers} label="watchers" variant="watchers" />}
  </div>
);

export default StatsBadge;