export default function RuleCheckPanel({ ruleCheck }: { ruleCheck?: { passed: boolean; errors: string[]; warnings: string[] } }) {
  if (!ruleCheck) return <div className="empty-state">尚未生成预览。</div>;

  return (
    <div className={`rule-panel ${ruleCheck.passed ? "passed" : "failed"}`}>
      <strong>{ruleCheck.passed ? "规则检查通过" : "规则检查未通过"}</strong>
      {ruleCheck.errors.map((item) => (
        <p key={item} className="error-text">{item}</p>
      ))}
      {ruleCheck.warnings.map((item) => (
        <p key={item} className="warning-text">{item}</p>
      ))}
    </div>
  );
}
