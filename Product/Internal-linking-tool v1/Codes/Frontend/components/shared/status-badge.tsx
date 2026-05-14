import { cn } from "@/lib/utils/cn";
import { localizeStatus } from "@/lib/utils/format";


const toneMap: Record<string, string> = {
  active: "border-emerald-200 bg-emerald-50 text-emerald-700",
  ready: "border-blue-200 bg-blue-50 text-blue-700",
  pending: "border-amber-200 bg-amber-50 text-amber-700",
  approved: "border-emerald-200 bg-emerald-50 text-emerald-700",
  rejected: "border-rose-200 bg-rose-50 text-rose-700",
  failed: "border-rose-200 bg-rose-50 text-rose-700",
  success: "border-emerald-200 bg-emerald-50 text-emerald-700",
  queued: "border-slate-200 bg-slate-100 text-slate-700",
  running: "border-cyan-200 bg-cyan-50 text-cyan-700",
  draft: "border-violet-200 bg-violet-50 text-violet-700",
  published: "border-emerald-200 bg-emerald-50 text-emerald-700",
  needs_review: "border-orange-200 bg-orange-50 text-orange-700",
  review_needed: "border-orange-200 bg-orange-50 text-orange-700",
};

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md border px-2.5 py-1 text-xs font-medium tracking-wide",
        toneMap[status] ?? "border-border bg-panelAlt text-foreground",
        className,
      )}
    >
      {localizeStatus(status)}
    </span>
  );
}
