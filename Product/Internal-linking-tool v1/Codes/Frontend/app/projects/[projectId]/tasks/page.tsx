"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { AsyncTaskTimeline } from "@/components/domain/async-task-timeline";
import { endpoints } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query/keys";


export default function TasksPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const { data: tasks } = useQuery({
    queryKey: queryKeys.tasks(projectId),
    queryFn: () => endpoints.tasks(projectId),
    refetchInterval: (query) => {
      const current = query.state.data ?? [];
      return current.some((task) => task.status === "queued" || task.status === "running") ? 2000 : false;
    },
  });

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold">任务中心</h2>
        <p className="mt-2 text-sm text-muted">所有长任务都在这里可观测，包含当前进度、执行阶段和失败原因。</p>
      </section>
      <AsyncTaskTimeline tasks={tasks ?? []} />
    </div>
  );
}
