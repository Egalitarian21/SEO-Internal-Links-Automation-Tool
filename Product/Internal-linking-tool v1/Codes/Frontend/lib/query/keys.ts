export const queryKeys = {
  dashboard: ["dashboard"] as const,
  projects: ["projects"] as const,
  project: (projectId: string) => ["project", projectId] as const,
  articles: (projectId: string) => ["articles", projectId] as const,
  cards: (projectId: string) => ["cards", projectId] as const,
  suggestions: (projectId: string, articleId?: string) => ["suggestions", projectId, articleId ?? "all"] as const,
  reviewQueue: (projectId: string) => ["review-queue", projectId] as const,
  reverseLinks: (projectId: string) => ["reverse-links", projectId] as const,
  tasks: (projectId: string) => ["tasks", projectId] as const,
  task: (taskId: string) => ["task", taskId] as const,
  publishChecklist: (projectId: string, articleIds?: string[]) => ["publish-checklist", projectId, ...(articleIds ?? [])] as const,
};
