"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { EmptyState } from "@/components/shared/empty-state";
import { SmartTable } from "@/components/shared/smart-table";
import { StatusBadge } from "@/components/shared/status-badge";
import { endpoints } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query/keys";
import { localizePageType, localizeStatus } from "@/lib/utils/format";
import type { Card } from "@/types/api";


const schema = z.object({
  summary: z.string().min(12),
  keywords: z.string().min(2),
  status: z.string(),
});

type FormValues = z.infer<typeof schema>;

export default function CardsPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const queryClient = useQueryClient();
  const { data: cards } = useQuery({
    queryKey: queryKeys.cards(projectId),
    queryFn: () => endpoints.cards(projectId),
  });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const selectedCard = useMemo(() => cards?.find((card) => card.id === selectedId) ?? cards?.[0], [cards, selectedId]);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { summary: "", keywords: "", status: "draft" },
  });

  useEffect(() => {
    if (selectedCard) {
      setSelectedId(selectedCard.id);
      form.reset({
        summary: selectedCard.summary,
        keywords: selectedCard.keywords.join(", "),
        status: selectedCard.status,
      });
    }
  }, [form, selectedCard]);

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      endpoints.updateCard(selectedCard!.id, {
        summary: values.summary,
        keywords: values.keywords.split(",").map((keyword) => keyword.trim()).filter(Boolean),
        status: values.status,
      }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.cards(projectId) });
    },
  });

  const columns = [
    {
      header: "卡片",
      cell: ({ row }: { row: { original: Card } }) => (
        <button type="button" onClick={() => setSelectedId(row.original.id)} className="text-left">
          <div className="font-medium">{row.original.title}</div>
          <div className="mt-1 text-xs text-muted">{row.original.target_url}</div>
        </button>
      ),
    },
    { header: "类型", cell: ({ row }: { row: { original: Card } }) => localizePageType(row.original.page_type) },
    { header: "Status", cell: ({ row }: { row: { original: Card } }) => <StatusBadge status={row.original.status} /> },
  ];

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_420px]">
      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold">知识卡片</h2>
          <p className="mt-2 text-sm text-muted">卡片是推荐生成和反向内链分析背后的可复用目标层。</p>
        </div>
        <SmartTable data={cards ?? []} columns={columns} />
      </section>

      <section className="rounded-lg border border-border bg-panel px-5 py-5 shadow-panel">
        {selectedCard ? (
          <>
            <h3 className="text-lg font-semibold">{selectedCard.title}</h3>
            <p className="mt-1 text-sm text-muted">{selectedCard.target_url}</p>
            <form className="mt-5 space-y-4" onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
              <label className="block text-sm text-muted">
                摘要
                <textarea {...form.register("summary")} rows={6} className="mt-2 w-full rounded-md border border-border bg-panelAlt px-4 py-3 text-sm text-foreground" />
              </label>
              <label className="block text-sm text-muted">
                关键词
                <input {...form.register("keywords")} className="mt-2 w-full rounded-md border border-border bg-panelAlt px-4 py-3 text-sm text-foreground" />
              </label>
              <label className="block text-sm text-muted">
                状态
                <select {...form.register("status")} className="mt-2 w-full rounded-md border border-border bg-panelAlt px-4 py-3 text-sm text-foreground">
                  <option value="draft">草稿</option>
                  <option value="published">已发布</option>
                  <option value="review_needed">待复核</option>
                </select>
              </label>
              <button type="submit" className="rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-white">
                保存卡片
              </button>
            </form>
          </>
        ) : (
          <EmptyState title="暂无卡片" description="请先导入 URL，系统会生成用于知识层演示的卡片。" />
        )}
      </section>
    </div>
  );
}
