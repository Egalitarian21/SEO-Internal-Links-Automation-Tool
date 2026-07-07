export type HealthResponse = {
  status: "ok";
};

export type Page = {
  id: string;
  page_type: "blog" | "collection" | "product";
  url: string;
  canonical_url: string;
  handle?: string | null;
  title: string;
  meta_title?: string | null;
  meta_description?: string | null;
  h1?: string | null;
  excerpt?: string | null;
  status: "published" | "draft" | "archived";
  cluster_name?: string | null;
  keyword?: string | null;
  raw_html?: string | null;
  content_hash?: string | null;
};

export type ArticleBlock = {
  id: string;
  block_index: number;
  block_type: string;
  heading_level?: string | null;
  section_title?: string | null;
  content: string;
  raw_html?: string | null;
  has_existing_link: boolean;
  link_count: number;
  is_first_paragraph: boolean;
};

export type AnchorCandidate = {
  id: string;
  source_page_id: string;
  article_block_id: string;
  anchor_text: string;
  context_text: string;
  link_type_suggestion: string;
  start_offset: number;
  end_offset: number;
  reason?: string | null;
  confidence_score: number;
  status: string;
};

export type Recommendation = {
  id: string;
  target_page_id: string;
  rank: number;
  url: string;
  title: string;
  page_type: string;
  meta_description?: string | null;
  score_total: number;
  score_cluster: number;
  score_keyword: number;
  score_page_type: number;
  score_semantic: number;
  score_title: number;
  score_quality: number;
  reason_json: { summary?: string; matched_fields?: string[] };
};

export type RecommendationGroup = {
  anchor_candidate_id: string;
  anchor_text: string;
  context_text: string;
  link_type_suggestion: string;
  reason?: string | null;
  status: string;
  recommendations: Recommendation[];
};

export type Snapshot = {
  id: string;
  source_page_id: string;
  snapshot_type: string;
  before_html: string;
  after_html: string;
  preview_id?: string | null;
  created_at: string;
};

export type DashboardStats = {
  total_pages: number;
  blog_count: number;
  collection_count: number;
  product_count: number;
  recent_snapshots: Array<{ id: string; source_page_id: string; snapshot_type: string; created_at: string }>;
};

export type LlmSettings = {
  enabled: boolean;
  base_url: string;
  api_key: string;
  model: string;
};

export type UrlImportItem = {
  url: string;
  status: "created" | "updated" | "skipped" | "failed" | string;
  page_type?: "blog" | "collection" | "product" | null;
  title?: string | null;
  reason?: string | null;
};

export type UrlImportResponse = {
  created: number;
  updated: number;
  skipped: number;
  failed: number;
  items: UrlImportItem[];
};

export type ImportJobItem = UrlImportItem & {
  id: string;
  created_at: string;
  updated_at: string;
};

export type ImportJob = {
  id: string;
  status: "queued" | "running" | "completed" | "failed" | string;
  total: number;
  processed: number;
  created: number;
  updated: number;
  skipped: number;
  failed: number;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
  completed_at?: string | null;
  items: ImportJobItem[];
};
