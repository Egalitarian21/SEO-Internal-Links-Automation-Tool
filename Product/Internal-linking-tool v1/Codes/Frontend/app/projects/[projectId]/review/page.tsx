"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { useMemo } from "react";

import { PrePublishChecklistPanel } from "@/components/domain/pre-publish-checklist-panel";
import { SuggestionReviewCard } from "@/components/domain/suggestion-review-card";
import { EmptyState } from "@/components/shared/empty-state";
import { endpoints } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query/keys";
import { useBatchReview, usePublish, useReviewSuggestion } from "@/lib/query/mutations";
import { useProjectStore } from "@/lib/store/project-store";


export default function ReviewPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const { selectedSuggestionIds, toggleSuggestion, clearSelection } = useProjectStore();

  const { data: queue } = useQuery({
    queryKey: queryKeys.reviewQueue(projectId),
    queryFn: () => endpoints.reviewQueue(projectId),
  });
  const articleIds = useMemo(
    () => Array.from(new Set((queue ?? []).filter((suggestion) => suggestion.status === "approved").map((suggestion) => suggestion.article_id))),
    [queue],
  );
  const { data: checklist } = useQuery({
    queryKey: queryKeys.publishChecklist(projectId, articleIds),
    queryFn: () => endpoints.publishChecklist(projectId, articleIds),
  });

  const reviewMutation = useReviewSuggestion(projectId);
  const batchMutation = useBatchReview(projectId);
  const publishMutation = usePublish(projectId);

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <div className="space-y-6">
      <section className="rounded-lg border border-border bg-panel px-5 py-5 shadow-panel">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">人工审核队列</h2>
            <p className="mt-2 text-sm text-muted">编辑可逐条通过、编辑、拒绝，或对低风险建议做批量处理。</p>
          </div>
          <div className="flex flex-wrap items-center gap-3">
            <span className="rounded-full border border-border bg-panelAlt px-3 py-2 text-sm text-muted">已选：{selectedSuggestionIds.length}</span>
            <button
              type="button"
              disabled={!selectedSuggestionIds.length || batchMutation.isPending}
              onClick={() => batchMutation.mutate({ suggestionIds: selectedSuggestionIds, action: "approved" }, { onSuccess: clearSelection })}
              className="rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60"
            >
              批量通过
            </button>
            <button
              type="button"
              disabled={!selectedSuggestionIds.length || batchMutation.isPending}
              onClick={() => batchMutation.mutate({ suggestionIds: selectedSuggestionIds, action: "rejected" }, { onSuccess: clearSelection })}
              className="rounded-md border border-rose-200 bg-rose-50 px-4 py-2.5 text-sm font-semibold text-rose-700 disabled:opacity-60"
            >
              批量拒绝
            </button>
          </div>
        </div>
      </section>

      <section className="space-y-4">
        {queue?.length ? (
          queue.map((suggestion) => (
            <SuggestionReviewCard
              key={suggestion.id}
              suggestion={suggestion}
              selected={selectedSuggestionIds.includes(suggestion.id)}
              onToggle={toggleSuggestion}
              onAction={({ suggestionId, action, editedAnchorText }) =>
                reviewMutation.mutate({ suggestionId, action, editedAnchorText })
              }
            />
          ))
        ) : (
          <EmptyState title="审核队列为空" description="请先生成内链建议，再回到这里做人工审核和发布检查。" />
        )}
      </section>
      </div>

      <aside className="space-y-6 xl:sticky xl:top-[84px] xl:self-start">
        {checklist ? <PrePublishChecklistPanel checklist={checklist} /> : null}

        <section className="rounded-lg border border-border bg-panel px-5 py-5 shadow-panel">
          <h3 className="text-lg font-semibold">发布动作</h3>
          <p className="mt-2 text-sm text-muted">只有全部阻断项清零后，才能将已通过建议送入发布任务。</p>
          <button
            type="button"
            disabled={!articleIds.length || Boolean(checklist?.blockers) || publishMutation.isPending}
            onClick={() => publishMutation.mutate(articleIds)}
            className="mt-4 w-full rounded-md bg-accent px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
          >
            {publishMutation.isPending ? "发布任务入队中..." : "确认发布"}
          </button>
          {publishMutation.data ? <div className="mt-3 text-sm text-success">任务 {publishMutation.data.task_id} 已入队</div> : null}
        </section>
      </aside>
    </div>
  );
}
