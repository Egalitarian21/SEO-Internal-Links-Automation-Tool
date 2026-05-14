import { apiGet, apiPatch, apiPost } from "@/lib/api/client";
import type {
  Article,
  Card,
  DashboardData,
  Project,
  PublishChecklist,
  ReverseLinkSummary,
  Suggestion,
  TaskRecord,
} from "@/types/api";

export const endpoints = {
  dashboard: () => apiGet<DashboardData>("/dashboard"),
  projects: () => apiGet<Project[]>("/projects"),
  project: (projectId: string) => apiGet<Project>(`/projects/${projectId}`),
  createProject: (payload: { name: string; domain: string; owner: string; description: string }) =>
    apiPost<Project>("/projects", payload),
  importUrls: (projectId: string, urls: string[]) => apiPost<{ task_id: string; message: string }>(`/projects/${projectId}/import`, { urls }),
  articles: (projectId: string) => apiGet<Article[]>(`/projects/${projectId}/articles`),
  cards: (projectId: string) => apiGet<Card[]>(`/projects/${projectId}/cards`),
  updateCard: (cardId: string, payload: { summary: string; keywords: string[]; status: string }) =>
    apiPatch<Card>(`/cards/${cardId}`, payload),
  generateSuggestions: (projectId: string, articleId: string) =>
    apiPost<{ task_id: string; message: string }>(`/projects/${projectId}/suggestions/generate`, { article_id: articleId }),
  suggestions: (projectId: string, articleId?: string) =>
    apiGet<Suggestion[]>(`/projects/${projectId}/suggestions`, articleId ? { article_id: articleId } : undefined),
  reviewQueue: (projectId: string) => apiGet<Suggestion[]>(`/projects/${projectId}/review-queue`),
  reverseLinks: (projectId: string) => apiGet<ReverseLinkSummary[]>(`/projects/${projectId}/reverse-links`),
  reviewSuggestion: (suggestionId: string, payload: { action: string; edited_anchor_text?: string | null }) =>
    apiPost<Suggestion>(`/review/suggestions/${suggestionId}`, payload),
  batchReview: (payload: { suggestion_ids: string[]; action: string }) =>
    apiPost<{ updated: Suggestion[]; count: number }>("/review/batch", payload),
  publishChecklist: (projectId: string, articleIds?: string[]) =>
    apiGet<PublishChecklist>(`/projects/${projectId}/publish/checklist`, articleIds?.length ? { article_ids: articleIds.join(",") } : undefined),
  publish: (projectId: string, articleIds: string[]) =>
    apiPost<{ task_id: string; message: string }>(`/projects/${projectId}/publish`, { article_ids: articleIds }),
  tasks: (projectId: string) => apiGet<TaskRecord[]>(`/projects/${projectId}/tasks`),
  task: (taskId: string) => apiGet<TaskRecord>(`/tasks/${taskId}`),
};
