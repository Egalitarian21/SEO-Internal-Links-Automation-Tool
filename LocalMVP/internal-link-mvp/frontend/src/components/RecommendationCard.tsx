import type { Recommendation } from "../types";

export default function RecommendationCard({
  recommendation,
  selected,
  onSelect,
}: {
  recommendation: Recommendation;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <button className={`recommendation-card ${selected ? "selected" : ""}`} type="button" onClick={onSelect}>
      <div className="item-card-header">
        <strong>{recommendation.rank}. {recommendation.title}</strong>
        <span className="score">{recommendation.score_total.toFixed(1)}</span>
      </div>
      <p>{recommendation.url}</p>
      <p>{recommendation.meta_description || "暂无描述"}</p>
      <div className="score-grid">
        <span>集群 {recommendation.score_cluster}</span>
        <span>关键词 {recommendation.score_keyword}</span>
        <span>类型 {recommendation.score_page_type}</span>
        <span>语义 {recommendation.score_semantic}</span>
        <span>标题 {recommendation.score_title}</span>
        <span>质量 {recommendation.score_quality}</span>
      </div>
      <p>{recommendation.reason_json.summary}</p>
    </button>
  );
}
