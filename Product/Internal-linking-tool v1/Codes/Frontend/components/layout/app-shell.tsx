"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { FolderKanban, LayoutDashboard, Link2, Settings } from "lucide-react";
import { ReactNode } from "react";

import { cn } from "@/lib/utils/cn";


const navItems = [
  { href: "/dashboard", label: "总览", icon: LayoutDashboard },
  { href: "/projects", label: "项目", icon: FolderKanban },
  { href: "/settings", label: "设置", icon: Settings },
];

const workflowSteps = [
  {
    label: "数据入库",
    description: "导入 URL、抽取正文、保留原始 HTML 快照。",
    match: ["/import", "/projects", "/dashboard"],
  },
  {
    label: "语义召回",
    description: "向量检索候选页，再用 SEO 规则做首轮过滤。",
    match: ["/articles", "/cards", "/recommend"],
  },
  {
    label: "锚文本建议",
    description: "生成可解释的候选建议，优先暴露低风险项。",
    match: ["/recommend", "/review"],
  },
  {
    label: "审核发布",
    description: "人工确认、发布前检查、保留回滚入口。",
    match: ["/review", "/tasks", "/reverse-links"],
  },
];

const policyRows = [
  { label: "同篇新增", value: "最多 3 条" },
  { label: "同段冲突", value: "禁止自动发布" },
  { label: "锚文本", value: "避免完全重复" },
  { label: "目标页", value: "仅同域 200 页面" },
  { label: "发布策略", value: "先保存快照" },
];

export function AppShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const isAuth = pathname.startsWith("/login");

  if (isAuth) {
    return <>{children}</>;
  }

  return (
    <div className="min-h-screen bg-background">
      <header className="sticky top-0 z-20 border-b border-border bg-panel">
        <div className="mx-auto flex h-[68px] max-w-[1600px] items-center justify-between gap-5 px-4 md:px-6">
          <Link href="/dashboard" className="flex min-w-[260px] items-center gap-3">
            <div className="grid h-10 w-10 place-items-center rounded-lg bg-slate-900 text-sm font-extrabold text-white">SEO</div>
            <div>
              <div className="text-[18px] font-semibold leading-tight">内链自动化审阅台</div>
              <div className="mt-0.5 text-xs text-muted">语义召回、规则过滤、人工确认、发布前可回滚</div>
            </div>
          </Link>
          <div className="hidden flex-wrap items-center gap-2 lg:flex">
            <span className="rounded-full border border-border bg-panel px-3 py-2 text-xs text-muted">模型：Qwen3-32B-Instruct</span>
            <span className="rounded-full border border-border bg-panel px-3 py-2 text-xs text-muted">向量库：pgvector</span>
            <span className="rounded-full border border-border bg-panel px-3 py-2 text-xs text-muted">状态：Demo Sandbox</span>
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-[1600px] grid-cols-1 gap-4 px-4 py-4 lg:grid-cols-[252px_minmax(0,1fr)] lg:px-6">
        <aside className="self-start rounded-lg border border-border bg-panel p-4 shadow-panel lg:sticky lg:top-[84px]">
          <p className="mb-3 text-xs font-extrabold uppercase tracking-wide text-muted">导航</p>
          <nav className="mb-5 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const active = pathname.startsWith(item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition",
                    active ? "border border-border bg-accentSoft text-accent" : "text-slate-700 hover:bg-panelAlt",
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <p className="mb-3 text-xs font-extrabold uppercase tracking-wide text-muted">工作流</p>
          <div className="space-y-2">
            {workflowSteps.map((step, index) => {
              const active = step.match.some((segment) => pathname.includes(segment));
              return (
                <div key={step.label} className={cn("grid grid-cols-[30px_1fr] gap-3 rounded-lg border border-border bg-panel p-3", active && "border-emerald-200 bg-accentSoft")}>
                  <div className={cn("grid h-7 w-7 place-items-center rounded-lg bg-panelAlt text-xs font-extrabold text-slate-600", active && "bg-accent text-white")}>
                    {index + 1}
                  </div>
                  <div>
                    <div className="text-sm font-semibold">{step.label}</div>
                    <div className="mt-1 text-xs leading-5 text-muted">{step.description}</div>
                  </div>
                </div>
              );
            })}
          </div>

          <p className="mb-3 mt-5 text-xs font-extrabold uppercase tracking-wide text-muted">SEO 约束</p>
          <div className="space-y-2">
            {policyRows.map((row) => (
              <div key={row.label} className="flex items-start justify-between gap-3 border-b border-slate-100 pb-2 text-xs">
                <span className="font-semibold text-slate-700">{row.label}</span>
                <span className="text-right text-muted">{row.value}</span>
              </div>
            ))}
          </div>
        </aside>

        <div className="min-w-0">{children}</div>
      </main>
    </div>
  );
}
