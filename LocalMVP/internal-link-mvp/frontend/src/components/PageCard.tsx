import type { Page } from "../types";

export default function PageCard({ page }: { page: Page }) {
  return (
    <div className="item-card">
      <div className="item-card-header">
        <strong>{page.title}</strong>
        <span className="tag">{page.page_type}</span>
      </div>
      <p>{page.url}</p>
      <p>{page.meta_description || "暂无 Meta Description"}</p>
      <div className="muted-row">
        <span>主题集群：{page.cluster_name || "-"}</span>
        <span>关键词：{page.keyword || "-"}</span>
      </div>
    </div>
  );
}
