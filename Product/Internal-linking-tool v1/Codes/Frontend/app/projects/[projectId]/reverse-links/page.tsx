"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import { EmptyState } from "@/components/shared/empty-state";
import { endpoints } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query/keys";


export default function ReverseLinksPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;
  const { data } = useQuery({
    queryKey: queryKeys.reverseLinks(projectId),
    queryFn: () => endpoints.reverseLinks(projectId),
  });

  return (
    <div className="space-y-6">
      <section>
        <h2 className="text-xl font-semibold">反向内链分布</h2>
        <p className="mt-2 text-sm text-muted">按目标页聚合已通过建议，便于团队快速发现是否有页面被过度链接。</p>
      </section>
      {data?.length ? (
        <div className="grid gap-4 md:grid-cols-2">
          {data.map((item) => (
            <div key={item.target_url} className="rounded-lg border border-border bg-panel px-5 py-5 shadow-panel">
              <div className="text-lg font-semibold">{item.target_title}</div>
              <div className="mt-1 break-all text-sm text-muted">{item.target_url}</div>
              <div className="mt-5 text-3xl font-semibold">{item.approved_links}</div>
              <div className="mt-1 text-sm text-muted">条已通过的进入链接</div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="暂无反向内链" description="至少通过一条建议后，这里才会出现目标页聚合结果。" />
      )}
    </div>
  );
}
