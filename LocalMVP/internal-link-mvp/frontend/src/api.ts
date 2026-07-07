import type {
  AnchorCandidate,
  ArticleBlock,
  DashboardStats,
  HealthResponse,
  ImportJob,
  LlmSettings,
  Page,
  RecommendationGroup,
  Snapshot,
} from "./types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function getHealth(): Promise<HealthResponse> {
  return request<HealthResponse>("/api/health");
}

export async function getDashboardStats(): Promise<DashboardStats> {
  return request<DashboardStats>("/api/dashboard/stats");
}

export async function importPages(items: unknown[]) {
  return request<{ created: number; updated: number; skipped: number }>("/api/pages/import", {
    method: "POST",
    body: JSON.stringify({ items }),
  });
}

export async function importUrls(urls: string[]) {
  return request<ImportJob>("/api/pages/import-urls", {
    method: "POST",
    body: JSON.stringify({ urls }),
  });
}

export async function getImportJob(jobId: string) {
  return request<ImportJob>(`/api/pages/import-url-jobs/${jobId}`);
}

export async function getLatestImportJob() {
  return request<ImportJob | null>("/api/pages/import-url-jobs/latest");
}

export async function listPages(params: { page_type?: string; status?: string; query?: string } = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  const suffix = query.toString() ? `?${query.toString()}` : "";
  return request<{ items: Page[] }>(`/api/pages${suffix}`);
}

export async function getPage(pageId: string) {
  return request<Page>(`/api/pages/${pageId}`);
}

export async function parseArticle(pageId: string) {
  return request<{ page_id: string; block_count: number; blocks: ArticleBlock[] }>(`/api/articles/${pageId}/parse`, { method: "POST" });
}

export async function listBlocks(pageId: string) {
  return request<{ items: ArticleBlock[] }>(`/api/articles/${pageId}/blocks`);
}

export async function generateAnchors(pageId: string) {
  return request<{ source_page_id: string; created: number; items: AnchorCandidate[] }>(
    `/api/internal-linking/${pageId}/anchor-candidates/generate`,
    { method: "POST" },
  );
}

export async function listAnchors(pageId: string) {
  return request<{ items: AnchorCandidate[] }>(`/api/internal-linking/${pageId}/anchor-candidates`);
}

export async function generateRecommendations(pageId: string) {
  return request<{ source_page_id: string; created: number }>(`/api/internal-linking/${pageId}/recommendations/generate`, { method: "POST" });
}

export async function listRecommendations(pageId: string) {
  return request<{ items: RecommendationGroup[] }>(`/api/internal-linking/${pageId}/recommendations`);
}

export async function saveDecisions(pageId: string, decisions: unknown[]) {
  return request<{ created: number }>(`/api/internal-linking/${pageId}/decisions`, {
    method: "POST",
    body: JSON.stringify({ decisions }),
  });
}

export async function createPreview(pageId: string) {
  return request<{ preview_id: string; preview_html: string; rule_check: { passed: boolean; errors: string[]; warnings: string[] } }>(
    `/api/internal-linking/${pageId}/preview`,
    { method: "POST" },
  );
}

export async function localWrite(pageId: string, previewId: string) {
  return request<{ snapshot_id: string; status: string }>(`/api/internal-linking/${pageId}/local-write`, {
    method: "POST",
    body: JSON.stringify({ preview_id: previewId }),
  });
}

export async function listSnapshots(pageId: string) {
  return request<{ items: Snapshot[] }>(`/api/snapshots?source_page_id=${pageId}`);
}

export async function rollbackSnapshot(snapshotId: string) {
  return request<{ snapshot_id: string; rollback_snapshot_id: string; status: string }>(`/api/snapshots/${snapshotId}/rollback`, { method: "POST" });
}

export async function getLlmSettings() {
  return request<LlmSettings>("/api/internal-linking/settings/llm");
}

export async function saveLlmSettings(settings: LlmSettings) {
  return request<LlmSettings>("/api/internal-linking/settings/llm", {
    method: "POST",
    body: JSON.stringify(settings),
  });
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
    ...options,
  });
  if (!response.ok) {
    let detail = `请求失败，状态码 ${response.status}`;
    try {
      const payload = await response.json();
      detail = typeof payload.detail === "string" ? payload.detail : detail;
    } catch {
      // 保留默认错误。
    }
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}
