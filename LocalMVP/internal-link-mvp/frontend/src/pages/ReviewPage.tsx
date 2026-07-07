import { useEffect, useState } from "react";

import { listRecommendations, saveDecisions } from "../api";
import DecisionPanel, { type DecisionDraft } from "../components/DecisionPanel";
import RecommendationCard from "../components/RecommendationCard";
import type { RecommendationGroup } from "../types";

export default function ReviewPage({ pageId }: { pageId: string }) {
  const [groups, setGroups] = useState<RecommendationGroup[]>([]);
  const [drafts, setDrafts] = useState<Record<string, DecisionDraft>>({});
  const [message, setMessage] = useState("");

  async function load() {
    const result = await listRecommendations(pageId);
    setGroups(result.items);
    const next: Record<string, DecisionDraft> = {};
    result.items.forEach((group) => {
      next[group.anchor_candidate_id] = {
        decision: group.recommendations[0] ? "approve" : "skip",
        selected_target_page_id: group.recommendations[0]?.target_page_id,
      };
    });
    setDrafts(next);
  }

  useEffect(() => {
    void load().catch((error) => setMessage(error instanceof Error ? error.message : "加载失败。"));
  }, [pageId]);

  async function handleSave() {
    try {
      const decisions = Object.entries(drafts).map(([anchor_candidate_id, draft]) => ({ anchor_candidate_id, ...draft }));
      const result = await saveDecisions(pageId, decisions);
      setMessage(`已保存 ${result.created} 条审核结果。`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "保存失败。");
    }
  }

  return (
    <main className="app-shell">
      <a className="text-link" href={`/workspace/${pageId}`}>返回工作台</a>
      <section className="panel">
        <div className="panel-header">
          <h1>人工审核</h1>
          <div className="action-row">
            <button className="button-primary" type="button" onClick={handleSave}>保存审核结果</button>
            <a className="button-secondary" href={`/preview/${pageId}`}>进入预览页</a>
          </div>
        </div>
        {message ? <p className="notice">{message}</p> : null}
      </section>
      <div className="list-stack">
        {groups.map((group) => (
          <section className="panel" key={group.anchor_candidate_id}>
            <div className="panel-header">
              <div>
                <h2>{group.anchor_text}</h2>
                <p>{group.context_text}</p>
                <div className="muted-row">
                  <span>建议类型：{group.link_type_suggestion}</span>
                  <span>状态：{statusLabel(group.status)}</span>
                </div>
                <p>{group.reason}</p>
              </div>
            </div>
            <div className="recommendation-list">
              {group.recommendations.map((recommendation) => (
                <RecommendationCard
                  key={recommendation.id}
                  recommendation={recommendation}
                  selected={drafts[group.anchor_candidate_id]?.selected_target_page_id === recommendation.target_page_id}
                  onSelect={() =>
                    setDrafts({
                      ...drafts,
                      [group.anchor_candidate_id]: {
                        ...(drafts[group.anchor_candidate_id] || { decision: "approve" }),
                        decision: "approve",
                        selected_target_page_id: recommendation.target_page_id,
                      },
                    })
                  }
                />
              ))}
            </div>
            <DecisionPanel
              value={drafts[group.anchor_candidate_id] || { decision: "skip" }}
              onChange={(next) => setDrafts({ ...drafts, [group.anchor_candidate_id]: next })}
            />
          </section>
        ))}
      </div>
    </main>
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
