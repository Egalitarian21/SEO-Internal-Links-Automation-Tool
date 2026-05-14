import type { Suggestion } from "@/types/api";


export function RelevanceScoreTriple({ relevance }: { relevance: Suggestion["relevance"] }) {
  const entries = [
    { label: "锚文本", value: relevance.anchor_target },
    { label: "段落语义", value: relevance.paragraph_target },
    { label: "上下文连续性", value: relevance.continuity },
  ];

  return (
    <div className="grid gap-3 md:grid-cols-3">
      {entries.map((entry) => (
        <div key={entry.label} className="rounded-md border border-border bg-panelAlt px-3 py-3">
          <div className="text-xs uppercase tracking-wide text-muted">{entry.label}</div>
          <div className="mt-2 flex items-center gap-3">
            <div className="h-2 flex-1 rounded-full bg-slate-200">
              <div className="h-2 rounded-full bg-accent" style={{ width: `${entry.value}%` }} />
            </div>
            <span className="w-10 text-right text-sm font-medium">{entry.value}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
