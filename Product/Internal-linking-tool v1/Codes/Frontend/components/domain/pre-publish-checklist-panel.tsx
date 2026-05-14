import { AlertTriangle, CheckCircle2 } from "lucide-react";

import type { PublishChecklist } from "@/types/api";


export function PrePublishChecklistPanel({ checklist }: { checklist: PublishChecklist }) {
  return (
    <section className="rounded-lg border border-border bg-panel px-5 py-5 shadow-panel">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold">发布前检查清单</h2>
          <p className="mt-1 text-sm text-muted">阻断项未清零前，不允许进入发布流程。</p>
        </div>
        <div className="flex gap-3 text-sm">
          <span className="rounded-full border border-rose-200 bg-rose-50 px-3 py-1 text-rose-700">
            阻断项：{checklist.blockers}
          </span>
          <span className="rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-amber-700">
            警告项：{checklist.warnings}
          </span>
        </div>
      </div>
      <div className="mt-4 space-y-3">
        {checklist.items.map((item) => (
          <div
            key={item.id}
            className={`rounded-md border px-4 py-3 ${
              item.passed
                ? "border-emerald-200 bg-emerald-50/70"
                : item.severity === "blocker"
                  ? "border-rose-200 bg-rose-50/70"
                  : "border-amber-200 bg-amber-50/70"
            }`}
          >
            <div className="flex items-start gap-3">
              <span className={item.passed ? "text-emerald-700" : item.severity === "blocker" ? "text-rose-700" : "text-amber-700"}>
                {item.passed ? <CheckCircle2 className="mt-0.5 h-4 w-4" /> : <AlertTriangle className="mt-0.5 h-4 w-4" />}
              </span>
              <div>
                <div className="text-sm font-medium">{item.label}</div>
                <div className="mt-1 text-sm text-muted">{item.detail}</div>
              </div>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
