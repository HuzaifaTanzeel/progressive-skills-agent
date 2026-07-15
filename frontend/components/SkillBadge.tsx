import type { SkillTier } from "@/lib/api";

type SkillBadgeProps = {
  skillName: string;
  tier?: SkillTier;
};

export function SkillBadge({ skillName, tier }: SkillBadgeProps) {
  const tierClass =
    tier === "draft-only"
      ? "bg-badge-draft-bg text-badge-draft-fg"
      : tier === "read-only"
        ? "bg-badge-readonly-bg text-badge-readonly-fg"
        : "bg-ink-muted text-sand-dim";

  const label =
    tier === "draft-only"
      ? "draft"
      : tier === "read-only"
        ? "read"
        : null;

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded px-2 py-0.5 text-xs font-medium tracking-wide ${tierClass}`}
      title={tier ? `${skillName} (${tier})` : skillName}
    >
      <span className="font-mono">{skillName}</span>
      {label ? (
        <span className="opacity-70 uppercase text-[0.65rem]">{label}</span>
      ) : null}
    </span>
  );
}
