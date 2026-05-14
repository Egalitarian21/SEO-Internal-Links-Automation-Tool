import type { Violation } from "@/types/api";


export function RuleViolationBadgeGroup({ violations }: { violations: Violation[] }) {
  if (!violations.length) {
    return <span className="text-sm text-success">无规则风险</span>;
  }

  return (
    <div className="flex flex-wrap gap-2">
      {violations.map((violation) => (
        <span
          key={`${violation.rule_id}-${violation.message}`}
          className={`inline-flex items-center rounded-md border px-2 py-1 text-xs ${
            violation.severity === "blocker"
              ? "border-rose-200 bg-rose-50 text-rose-700"
              : "border-amber-200 bg-amber-50 text-amber-700"
          }`}
          title={violation.message}
        >
          {violation.rule_id} · {violation.severity === "blocker" ? "阻断" : "警告"}
        </span>
      ))}
    </div>
  );
}
