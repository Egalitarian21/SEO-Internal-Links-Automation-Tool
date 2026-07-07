export type DecisionDraft = {
  decision: "approve" | "reject_anchor" | "reject_target" | "replace_target" | "skip";
  selected_target_page_id?: string;
  manual_target_url?: string;
  reviewer_note?: string;
};

export default function DecisionPanel({
  value,
  onChange,
}: {
  value: DecisionDraft;
  onChange: (next: DecisionDraft) => void;
}) {
  return (
    <div className="decision-panel">
      <select value={value.decision} onChange={(event) => onChange({ ...value, decision: event.target.value as DecisionDraft["decision"] })}>
        <option value="approve">通过推荐目标</option>
        <option value="reject_anchor">拒绝锚文本</option>
        <option value="reject_target">拒绝目标页</option>
        <option value="replace_target">手动替换目标</option>
        <option value="skip">跳过</option>
      </select>
      {value.decision === "replace_target" ? (
        <input
          value={value.manual_target_url || ""}
          onChange={(event) => onChange({ ...value, manual_target_url: event.target.value })}
          placeholder="手动目标 URL"
        />
      ) : null}
      <input
        value={value.reviewer_note || ""}
        onChange={(event) => onChange({ ...value, reviewer_note: event.target.value })}
        placeholder="审核备注"
      />
    </div>
  );
}
