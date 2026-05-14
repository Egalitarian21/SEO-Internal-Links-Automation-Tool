"use client";

import Link from "next/link";
import { ColumnDef } from "@tanstack/react-table";
import { useQuery } from "@tanstack/react-query";

import { SmartTable } from "@/components/shared/smart-table";
import { StatusBadge } from "@/components/shared/status-badge";
import { endpoints } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query/keys";
import { formatDate, formatPercent } from "@/lib/utils/format";
import type { Project } from "@/types/api";


const columns: ColumnDef<Project>[] = [
  {
    header: "项目",
    cell: ({ row }) => (
      <div>
        <div className="font-medium">{row.original.name}</div>
        <div className="mt-1 text-xs text-muted">{row.original.domain}</div>
      </div>
    ),
  },
  { header: "负责人", accessorKey: "owner" },
  { header: "状态", cell: ({ row }) => <StatusBadge status={row.original.status} /> },
  { header: "健康度", cell: ({ row }) => <span>{formatPercent(row.original.health_score)}</span> },
  { header: "最近活动", cell: ({ row }) => <span>{formatDate(row.original.last_activity_at)}</span> },
  {
    header: "操作",
    cell: ({ row }) => (
      <div className="flex gap-2">
        <Link href={`/projects/${row.original.id}/import`} className="rounded-md border border-border px-3 py-2 text-xs hover:bg-panelAlt">
          导入
        </Link>
        <Link href={`/projects/${row.original.id}/review`} className="rounded-md border border-border px-3 py-2 text-xs hover:bg-panelAlt">
          审核
        </Link>
      </div>
    ),
  },
];

export default function ProjectsPage() {
  const { data: projects } = useQuery({
    queryKey: queryKeys.projects,
    queryFn: endpoints.projects,
  });

  return (
    <div className="space-y-6">
      <section className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-semibold">项目管理</h1>
          <p className="mt-2 text-sm text-muted">每个项目都承接从批量导入到发布回滚的完整工作流。</p>
        </div>
        <Link href="/projects/new" className="rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-white">
          新建项目
        </Link>
      </section>
      <SmartTable data={projects ?? []} columns={columns} />
    </div>
  );
}
