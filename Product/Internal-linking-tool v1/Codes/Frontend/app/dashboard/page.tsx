"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Activity, BookCopy, CheckCircle2, FolderOpenDot, Sparkles } from "lucide-react";

import { AsyncTaskTimeline } from "@/components/domain/async-task-timeline";
import { MetricCard } from "@/components/shared/metric-card";
import { endpoints } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query/keys";


export default function DashboardPage() {
  const { data: dashboard } = useQuery({
    queryKey: queryKeys.dashboard,
    queryFn: endpoints.dashboard,
  });
  const { data: projects } = useQuery({
    queryKey: queryKeys.projects,
    queryFn: endpoints.projects,
  });

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-border bg-panel px-6 py-6 shadow-panel">
        <p className="text-sm text-muted">工作台总览</p>
        <h1 className="mt-2 text-3xl font-semibold">SEO 内链自动化控制台</h1>
        <p className="mt-3 max-w-3xl text-sm leading-7 text-muted">
          当前 Demo 已按实施方案打通“项目管理、URL 导入、知识卡片、推荐审核、发布检查、任务监控”主链路，并把长任务状态和规则风险显式呈现。
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-5">
        <MetricCard label="项目数" value={dashboard?.summary.projects ?? 0} hint="已纳入管理的站点项目" icon={<FolderOpenDot className="h-5 w-5" />} />
        <MetricCard label="文章草稿" value={dashboard?.summary.articles ?? 0} hint="已导入待处理的正文" icon={<BookCopy className="h-5 w-5" />} />
        <MetricCard label="知识卡片" value={dashboard?.summary.wiki_cards ?? 0} hint="可复用的页面知识层" icon={<Sparkles className="h-5 w-5" />} />
        <MetricCard label="已通过建议" value={dashboard?.summary.approved_suggestions ?? 0} hint="可进入发布检查的建议" icon={<CheckCircle2 className="h-5 w-5" />} />
        <MetricCard label="活动任务" value={dashboard?.summary.active_tasks ?? 0} hint="执行中或排队中的任务" icon={<Activity className="h-5 w-5" />} />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]">
        <div className="rounded-lg border border-border bg-panel px-5 py-5 shadow-panel">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold">项目列表</h2>
              <p className="mt-1 text-sm text-muted">可以直接跳到当前团队最常用的工作阶段。</p>
            </div>
            <Link href="/projects" className="rounded-md border border-border px-3 py-2 text-sm hover:bg-panelAlt">
              查看全部
            </Link>
          </div>
          <div className="mt-5 space-y-3">
            {projects?.map((project) => (
              <Link key={project.id} href={`/projects/${project.id}/import`} className="block rounded-lg border border-border bg-panelAlt px-4 py-4 hover:bg-white">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <div className="font-medium">{project.name}</div>
                    <div className="mt-1 text-sm text-muted">{project.domain}</div>
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-xs text-muted">
                    <div>
                      <div className="text-foreground">{project.imported_urls}</div>
                      <div>URL</div>
                    </div>
                    <div>
                      <div className="text-foreground">{project.wiki_cards}</div>
                      <div>卡片</div>
                    </div>
                    <div>
                      <div className="text-foreground">{project.approved_suggestions}</div>
                      <div>已通过</div>
                    </div>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        </div>

        <div>
          <h2 className="mb-4 text-lg font-semibold">最近任务</h2>
          <AsyncTaskTimeline tasks={dashboard?.recent_tasks ?? []} />
        </div>
      </section>
    </div>
  );
}
