"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { BarChart3, BookOpenText, Boxes, CheckCheck, Files, Route, TimerReset } from "lucide-react";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

import { StatusBadge } from "@/components/shared/status-badge";
import { endpoints } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query/keys";
import { cn } from "@/lib/utils/cn";


const subNav = [
  { slug: "import", label: "URL 导入", icon: Files },
  { slug: "articles", label: "文章草稿", icon: BookOpenText },
  { slug: "cards", label: "知识卡片", icon: Boxes },
  { slug: "recommend", label: "内链推荐", icon: BarChart3 },
  { slug: "review", label: "审核发布", icon: CheckCheck },
  { slug: "reverse-links", label: "反向内链", icon: Route },
  { slug: "tasks", label: "任务中心", icon: TimerReset },
];

export function ProjectShell({ projectId, children }: { projectId: string; children: ReactNode }) {
  const pathname = usePathname();
  const { data: project } = useQuery({
    queryKey: queryKeys.project(projectId),
    queryFn: () => endpoints.project(projectId),
  });

  const metrics = [
    { label: "文章数", value: project?.metrics?.articles ?? 0 },
    { label: "待审核", value: project?.metrics?.pending_review ?? 0 },
    { label: "已通过", value: project?.metrics?.approved ?? 0 },
    { label: "今日任务", value: project?.metrics?.tasks_today ?? 0 },
  ];

  return (
    <div className="space-y-4">
      <section className="overflow-hidden rounded-lg border border-border bg-panel shadow-panel">
        <div className="flex flex-wrap items-start justify-between gap-4 border-b border-border px-5 py-5">
          <div>
            <p className="text-xs font-extrabold uppercase tracking-wide text-muted">项目工作台</p>
            <h1 className="mt-2 text-[28px] font-semibold leading-tight">{project?.name ?? "项目加载中..."}</h1>
            <p className="mt-3 max-w-3xl text-sm leading-7 text-muted">{project?.description}</p>
            <div className="mt-3 flex flex-wrap gap-2 text-xs text-muted">
              <span className="rounded-full bg-panelAlt px-3 py-1.5">{project?.domain}</span>
              <span className="rounded-full bg-panelAlt px-3 py-1.5">负责人：{project?.owner ?? "SEO 团队"}</span>
            </div>
          </div>
          <div className="space-y-2 text-right">
            {project ? <StatusBadge status={project.status} /> : null}
            <div className="text-sm text-muted">健康度 {project?.health_score ?? 0}%</div>
          </div>
        </div>

        <div className="grid gap-3 border-b border-border bg-slate-50 px-5 py-4 md:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => (
            <div key={metric.label} className="rounded-lg border border-border bg-panel px-4 py-4">
              <div className="text-xs text-muted">{metric.label}</div>
              <div className="mt-2 text-2xl font-semibold">{metric.value}</div>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap gap-2 px-5 py-4">
          {subNav.map((item) => {
            const Icon = item.icon;
            const href = `/projects/${projectId}/${item.slug}`;
            const active = pathname === href;
            return (
              <Link
                key={item.slug}
                href={href}
                className={cn(
                  "inline-flex items-center gap-2 rounded-full border px-3 py-2 text-sm transition",
                  active ? "border-emerald-200 bg-accentSoft text-accent" : "border-border bg-panel text-slate-700 hover:bg-panelAlt",
                )}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </div>
      </section>
      {children}
    </div>
  );
}
