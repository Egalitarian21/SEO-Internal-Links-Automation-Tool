import { Clock3, LoaderCircle, OctagonAlert, PartyPopper } from "lucide-react";

import { formatDate } from "@/lib/utils/format";
import { localizeStatus, localizeTaskType } from "@/lib/utils/format";
import type { TaskRecord } from "@/types/api";


const iconMap = {
  queued: <Clock3 className="h-4 w-4" />,
  running: <LoaderCircle className="h-4 w-4 animate-spin" />,
  success: <PartyPopper className="h-4 w-4" />,
  failed: <OctagonAlert className="h-4 w-4" />,
};

export function AsyncTaskTimeline({ tasks }: { tasks: TaskRecord[] }) {
  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <div key={task.id} className="rounded-lg border border-border bg-panel px-4 py-4 shadow-panel">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 text-sm text-muted">
                <span>{iconMap[task.status]}</span>
                <span>{localizeTaskType(task.task_type)}</span>
                <span>{formatDate(task.updated_at)}</span>
              </div>
              <h3 className="mt-2 text-base font-semibold">{task.title}</h3>
              <p className="mt-1 text-sm text-muted">{task.detail}</p>
            </div>
            <div className="min-w-36">
              <div className="flex items-center justify-between text-xs text-muted">
                <span>{localizeStatus(task.status)}</span>
                <span>{task.progress}%</span>
              </div>
              <div className="mt-2 h-2 rounded-full bg-slate-200">
                <div
                  className={`h-2 rounded-full ${
                    task.status === "failed" ? "bg-rose-500" : task.status === "success" ? "bg-emerald-500" : "bg-cyan-500"
                  }`}
                  style={{ width: `${task.progress}%` }}
                />
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
