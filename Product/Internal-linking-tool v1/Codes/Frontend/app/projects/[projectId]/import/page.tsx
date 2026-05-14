"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useMemo } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AsyncTaskTimeline } from "@/components/domain/async-task-timeline";
import { useImportUrls } from "@/lib/query/mutations";
import { endpoints } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query/keys";


const schema = z.object({
  urls: z.string().min(10),
});

type FormValues = z.infer<typeof schema>;

export default function ImportPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const importMutation = useImportUrls(projectId);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      urls: [
        "https://hydrafitness.com/blogs/training/desk-worker-warm-up",
        "https://hydrafitness.com/blogs/equipment/compact-rack-buying-guide",
      ].join("\n"),
    },
  });

  const { data: tasks } = useQuery({
    queryKey: queryKeys.tasks(projectId),
    queryFn: () => endpoints.tasks(projectId),
    refetchInterval: (query) => {
      const current = query.state.data ?? [];
      return current.some((task) => task.status === "queued" || task.status === "running") ? 2000 : false;
    },
  });

  const importTasks = useMemo(() => (tasks ?? []).filter((task) => task.task_type === "import"), [tasks]);

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
      <section className="rounded-lg border border-border bg-panel px-6 py-6 shadow-panel">
        <h2 className="text-xl font-semibold">批量 URL 导入</h2>
        <p className="mt-2 text-sm text-muted">每行粘贴一个 URL。提交后立即进入任务队列，右侧展示执行进度。</p>
        <form
          className="mt-5 space-y-4"
          onSubmit={form.handleSubmit((values) => {
            const urls = values.urls.split("\n").map((item) => item.trim()).filter(Boolean);
            importMutation.mutate(urls);
          })}
        >
          <textarea
            {...form.register("urls")}
            rows={12}
            className="w-full rounded-md border border-border bg-panelAlt px-4 py-3 text-sm leading-7 text-foreground"
          />
          <div className="flex items-center gap-3">
            <button type="submit" disabled={importMutation.isPending} className="rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60">
              {importMutation.isPending ? "提交中..." : "开始导入"}
            </button>
            {importMutation.data ? <span className="text-sm text-accent">任务 {importMutation.data.task_id} 已入队</span> : null}
            {importMutation.error ? <span className="text-sm text-rose-700">{importMutation.error.message}</span> : null}
          </div>
        </form>
      </section>

      <section>
        <h2 className="mb-4 text-xl font-semibold">导入时间线</h2>
        <AsyncTaskTimeline tasks={importTasks} />
      </section>
    </div>
  );
}
