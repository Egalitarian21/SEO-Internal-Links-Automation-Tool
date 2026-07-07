import type { AnchorCandidate } from "../types";

export default function AnchorCandidateCard({ item }: { item: AnchorCandidate }) {
  return (
    <div className="item-card">
      <div className="item-card-header">
        <strong>{item.anchor_text}</strong>
        <span className="tag">{statusLabel(item.status)}</span>
      </div>
      <p>{item.context_text}</p>
      <div className="muted-row">
        <span>建议类型：{item.link_type_suggestion}</span>
        <span>offset：{item.start_offset}-{item.end_offset}</span>
      </div>
      <p>{item.reason}</p>
    </div>
  );
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    pending: "待审核",
    accepted: "已通过",
    rejected: "已拒绝",
    skipped: "已跳过",
  };

  return labels[status] ?? status;
}
