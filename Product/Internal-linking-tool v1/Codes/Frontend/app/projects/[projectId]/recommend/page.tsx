"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { AsyncTaskTimeline } from "@/components/domain/async-task-timeline";
import { EmptyState } from "@/components/shared/empty-state";
import { SuggestionReviewCard } from "@/components/domain/suggestion-review-card";
import { endpoints } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query/keys";
import { useGenerateSuggestions } from "@/lib/query/mutations";


export default function RecommendPage() {
  const params = useParams<{ projectId: string }>();
  const searchParams = useSearchParams();
  const projectId = params.projectId;
  const suggestedArticleId = searchParams.get("articleId");

  const { data: articles } = useQuery({
    queryKey: queryKeys.articles(projectId),
    queryFn: () => endpoints.articles(projectId),
  });
  const [articleId, setArticleId] = useState<string>("");

  useEffect(() => {
    if (suggestedArticleId) {
      setArticleId(suggestedArticleId);
    } else if (!articleId && articles?.length) {
      setArticleId(articles[0].id);
    }
  }, [articleId, articles, suggestedArticleId]);

  const generateMutation = useGenerateSuggestions(projectId);
  const { data: suggestions } = useQuery({
    queryKey: queryKeys.suggestions(projectId, articleId),
    queryFn: () => endpoints.suggestions(projectId, articleId),
    enabled: Boolean(articleId),
  });
  const { data: tasks } = useQuery({
    queryKey: queryKeys.tasks(projectId),
    queryFn: () => endpoints.tasks(projectId),
    refetchInterval: (query) => {
      const current = query.state.data ?? [];
      return current.some((task) => task.status === "queued" || task.status === "running") ? 2000 : false;
    },
  });

  const recommendTasks = useMemo(() => (tasks ?? []).filter((task) => task.task_type === "recommend"), [tasks]);

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-border bg-panel px-5 py-5 shadow-panel">
        <div className="flex flex-wrap items-end gap-4">
          <label className="min-w-72 text-sm text-muted">
            选择文章
            <select value={articleId} onChange={(event) => setArticleId(event.target.value)} className="mt-2 w-full rounded-md border border-border bg-panelAlt px-4 py-3 text-sm text-foreground">
              {articles?.map((article) => (
                <option key={article.id} value={article.id}>
                  {article.title}
                </option>
              ))}
            </select>
          </label>
          <button
            type="button"
            disabled={!articleId || generateMutation.isPending}
            onClick={() => generateMutation.mutate(articleId)}
            className="rounded-md bg-accent px-4 py-3 text-sm font-semibold text-white disabled:opacity-60"
          >
            {generateMutation.isPending ? "提交中..." : "生成内链建议"}
          </button>
          {generateMutation.data ? <span className="text-sm text-accent">任务 {generateMutation.data.task_id}</span> : null}
        </div>
      </section>

      {recommendTasks.length ? (
        <section>
          <h2 className="mb-4 text-xl font-semibold">推荐任务</h2>
          <AsyncTaskTimeline tasks={recommendTasks} />
        </section>
      ) : null}

      <section className="space-y-4">
        <div>
          <h2 className="text-xl font-semibold">建议流</h2>
          <p className="mt-2 text-sm text-muted">默认优先暴露规则风险和相关性得分，方便编辑快速筛掉高风险建议。</p>
        </div>
        {suggestions?.length ? (
          suggestions.map((suggestion) => <SuggestionReviewCard key={suggestion.id} suggestion={suggestion} />)
        ) : (
          <EmptyState title="暂时还没有建议" description="先为某篇文章触发推荐任务，建议卡片流就会出现在这里。" />
        )}
      </section>
    </div>
  );
}
