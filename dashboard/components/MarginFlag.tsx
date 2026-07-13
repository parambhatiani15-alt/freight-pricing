import type { MarginFlag as MarginFlagType } from "@/lib/types";

const STYLES: Record<MarginFlagType, { bg: string; text: string; dot: string; label: string }> = {
  ok: { bg: "bg-pine-soft", text: "text-pine", dot: "bg-pine", label: "On target" },
  warning: { bg: "bg-amber-soft", text: "text-amber", dot: "bg-amber", label: "Warning" },
  breach: { bg: "bg-rust-soft", text: "text-rust", dot: "bg-rust", label: "Breach" },
};

export default function MarginFlag({ flag, compact = false }: { flag: MarginFlagType; compact?: boolean }) {
  const s = STYLES[flag];
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-sm px-2 py-0.5 text-xs font-medium ${s.bg} ${s.text}`}
    >
      <span className={`w-1.5 h-1.5 rounded-full ${s.dot}`} />
      {compact ? s.label.split(" ")[0] : s.label}
    </span>
  );
}
