export function formatDate(value: string | null | undefined) {
  if (!value) {
    return "未开始";
  }

  return new Intl.DateTimeFormat("zh-CN", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(value));
}

export function formatPercent(value: number) {
  return `${value}%`;
}

export function localizeStatus(value: string) {
  const map: Record<string, string> = {
    active: "进行中",
    ready: "就绪",
    pending: "待处理",
    approved: "已通过",
    rejected: "已拒绝",
    failed: "失败",
    success: "成功",
    queued: "排队中",
    running: "执行中",
    draft: "草稿",
    published: "已发布",
    needs_review: "待复核",
    review_needed: "待复核",
  };

  return map[value] ?? value.replace(/_/g, " ");
}

export function localizePageType(value: string) {
  const map: Record<string, string> = {
    product: "商品页",
    collection: "集合页",
    blog: "博客页",
  };

  return map[value] ?? value;
}

export function localizeTaskType(value: string) {
  const map: Record<string, string> = {
    import: "导入任务",
    recommend: "推荐任务",
    publish: "发布任务",
  };

  return map[value] ?? value;
}
