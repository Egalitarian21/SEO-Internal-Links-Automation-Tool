"use client";

import Link from "next/link";
import { ColumnDef } from "@tanstack/react-table";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { SmartTable } from "@/components/shared/smart-table";
import { StatusBadge } from "@/components/shared/status-badge";
import { endpoints } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query/keys";
import { formatDate } from "@/lib/utils/format";
import type { Article } from "@/types/api";


export default function ArticlesPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const { data: articles } = useQuery({
    queryKey: queryKeys.articles(projectId),
    queryFn: () => endpoints.articles(projectId),
  });

  const columns: ColumnDef<Article>[] = [
    {
      header: "文章",
      cell: ({ row }) => (
        <div>
          <div className="font-medium">{row.original.title}</div>
          <div className="mt-1 text-xs text-muted">{row.original.url}</div>
        </div>
      ),
    },
    { header: "分类", accessorKey: "category" },
    { header: "状态", cell: ({ row }) => <StatusBadge status={row.original.status} /> },
    { header: "现有链接", accessorKey: "existing_links" },
    { header: "导入时间", cell: ({ row }) => <span>{formatDate(row.original.imported_at)}</span> },
    {
      header: "操作",
      cell: ({ row }) => (
        <Link href={`/projects/${projectId}/recommend?articleId=${row.original.id}`} className="rounded-md border border-border px-3 py-2 text-xs hover:bg-panelAlt">
          生成推荐
        </Link>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold">文章草稿列表</h2>
        <p className="mt-2 text-sm text-muted">文章以草稿视图保留，便于编辑选择在哪一篇上触发内链推荐。</p>
      </section>
      <SmartTable data={articles ?? []} columns={columns} />
    </div>
  );
}
