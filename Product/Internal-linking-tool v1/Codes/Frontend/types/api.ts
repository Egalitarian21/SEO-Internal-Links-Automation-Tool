export type Status = "active" | "ready" | "pending" | "approved" | "rejected" | "failed" | "success" | "queued" | "running" | "draft" | "published" | "needs_review" | "review_needed";

export interface ApiResponse<T> {
  data: T;
}

export interface Project {
  id: string;
  name: string;
  domain: string;
  owner: string;
  status: string;
  created_at: string;
  last_activity_at: string;
  health_score: number;
  imported_urls: number;
  wiki_cards: number;
  approved_suggestions: number;
  publish_success_rate: number;
  description: string;
  metrics?: {
    articles: number;
    pending_review: number;
    approved: number;
    tasks_today: number;
  };
}

export interface Article {
  id: string;
  project_id: string;
  title: string;
  url: string;
  category: string;
  status: string;
  imported_at: string;
  last_recommendation_at: string | null;
  excerpt: string;
  paragraphs: string[];
  existing_links: number;
}

export interface Card {
  id: string;
  project_id: string;
  title: string;
  page_type: "product" | "collection" | "blog";
  target_url: string;
  source_article_id: string | null;
  summary: string;
  keywords: string[];
  last_updated_at: string;
  status: string;
}

export interface Violation {
  severity: "blocker" | "warning";
  rule_id: string;
  message: string;
}

export interface Suggestion {
  id: string;
  project_id: string;
  article_id: string;
  anchor_text: string;
  context_before: string;
  context_after: string;
  target_title: string;
  target_url: string;
  page_type: "product" | "collection" | "blog";
  status: "pending" | "approved" | "rejected";
  edited_anchor_text: string | null;
  relevance: {
    anchor_target: number;
    paragraph_target: number;
    continuity: number;
    total: number;
  };
  rule_violations: Violation[];
  created_at: string;
}

export interface TaskRecord {
  id: string;
  project_id: string;
  task_type: string;
  status: "queued" | "running" | "success" | "failed";
  title: string;
  created_at: string;
  updated_at: string;
  progress: number;
  detail: string;
  result: Record<string, unknown>;
}

export interface DashboardData {
  summary: {
    projects: number;
    articles: number;
    wiki_cards: number;
    approved_suggestions: number;
    active_tasks: number;
  };
  recent_tasks: TaskRecord[];
}

export interface ChecklistItem {
  id: string;
  label: string;
  severity: "blocker" | "warning";
  passed: boolean;
  detail: string;
}

export interface PublishChecklist {
  items: ChecklistItem[];
  blockers: number;
  warnings: number;
}

export interface ReverseLinkSummary {
  target_url: string;
  target_title: string;
  approved_links: number;
}
