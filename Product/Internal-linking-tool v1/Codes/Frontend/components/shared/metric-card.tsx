import { ReactNode } from "react";


export function MetricCard({
  label,
  value,
  hint,
  icon,
}: {
  label: string;
  value: string | number;
  hint: string;
  icon: ReactNode;
}) {
  return (
    <div className="rounded-lg border border-border bg-panel px-4 py-4 shadow-panel">
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted">{label}</span>
        <span className="rounded-full bg-panelAlt p-2 text-accent">{icon}</span>
      </div>
      <div className="mt-4 text-3xl font-semibold">{value}</div>
      <p className="mt-2 text-sm text-muted">{hint}</p>
    </div>
  );
}
