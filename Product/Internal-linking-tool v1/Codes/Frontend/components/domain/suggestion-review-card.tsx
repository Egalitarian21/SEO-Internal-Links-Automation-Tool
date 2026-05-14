"use client";

import { useState } from "react";
import { Check, PencilLine, X } from "lucide-react";

import { RelevanceScoreTriple } from "@/components/domain/relevance-score-triple";
import { RuleViolationBadgeGroup } from "@/components/domain/rule-violation-badges";
import { StatusBadge } from "@/components/shared/status-badge";
import { localizePageType } from "@/lib/utils/format";
import type { Suggestion } from "@/types/api";


export function SuggestionReviewCard({
  suggestion,
  selected,
  onToggle,
  onAction,
}: {
  suggestion: Suggestion;
  selected?: boolean;
  onToggle?: (id: string) => void;
  onAction?: (payload: { suggestionId: string; action: "approved" | "rejected"; editedAnchorText?: string }) => void;
}) {
  const [editedAnchor, setEditedAnchor] = useState(suggestion.edited_anchor_text ?? suggestion.anchor_text);

  return (
    <article className="rounded-lg border border-border bg-panel px-5 py-5 shadow-panel">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="space-y-2">
          <div className="flex flex-wrap items-center gap-2">
            {onToggle ? (
              <input
                type="checkbox"
                checked={selected ?? false}
                onChange={() => onToggle(suggestion.id)}
                className="h-4 w-4 rounded border-border bg-panelAlt text-accent"
              />
            ) : null}
            <StatusBadge status={suggestion.status} />
            <span className="rounded-full bg-panelAlt px-2.5 py-1 text-xs text-muted">{localizePageType(suggestion.page_type)}</span>
            <span className="rounded-full bg-accentSoft px-2.5 py-1 text-xs font-semibold text-accent">综合分 {suggestion.relevance.total}</span>
          </div>
          <h3 className="text-lg font-semibold">{suggestion.target_title}</h3>
          <p className="text-sm text-muted">{suggestion.target_url}</p>
        </div>
        <RuleViolationBadgeGroup violations={suggestion.rule_violations} />
      </div>

      <div className="mt-5 rounded-md border border-border bg-panelAlt px-4 py-4">
        <div className="text-xs uppercase tracking-wide text-muted">锚文本上下文</div>
        <p className="mt-2 text-sm leading-7 text-slate-700">
          {suggestion.context_before}{" "}
          <span className="rounded bg-accentSoft px-1.5 py-0.5 text-accent">{suggestion.anchor_text}</span>{" "}
          {suggestion.context_after}
        </p>
      </div>

      <div className="mt-5">
        <RelevanceScoreTriple relevance={suggestion.relevance} />
      </div>

      {onAction ? (
        <div className="mt-5 flex flex-col gap-3 border-t border-border pt-4">
          <label className="text-sm text-muted">
            编辑后锚文本
            <div className="mt-2 flex items-center gap-2 rounded-md border border-border bg-panelAlt px-3 py-2">
              <PencilLine className="h-4 w-4 text-muted" />
              <input
                value={editedAnchor}
                onChange={(event) => setEditedAnchor(event.target.value)}
                className="w-full bg-transparent text-sm"
              />
            </div>
          </label>
          <div className="flex flex-wrap gap-3">
            <button
              type="button"
              onClick={() => onAction({ suggestionId: suggestion.id, action: "approved", editedAnchorText: editedAnchor })}
              className="inline-flex items-center gap-2 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white"
            >
              <Check className="h-4 w-4" />
              通过
            </button>
            <button
              type="button"
              onClick={() => onAction({ suggestionId: suggestion.id, action: "rejected" })}
              className="inline-flex items-center gap-2 rounded-md border border-rose-200 bg-rose-50 px-4 py-2 text-sm font-medium text-rose-700"
            >
              <X className="h-4 w-4" />
              拒绝
            </button>
          </div>
        </div>
      ) : null}
    </article>
  );
}
