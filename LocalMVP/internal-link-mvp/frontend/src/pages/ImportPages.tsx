import { useEffect, useState } from "react";

import { getImportJob, getLatestImportJob, importPages, importUrls } from "../api";
import type { ImportJob } from "../types";

const emptySinglePage = {
  page_type: "blog",
  url: "",
  title: "",
  meta_description: "",
  h1: "",
  excerpt: "",
  status: "published",
  cluster_name: "",
  keyword: "",
  raw_html: "",
};

export default function ImportPages() {
  const [text, setText] = useState("");
  const [singlePage, setSinglePage] = useState(emptySinglePage);
  const [message, setMessage] = useState("");
  const [importJob, setImportJob] = useState<ImportJob | null>(null);
  const [isImporting, setIsImporting] = useState(false);

  useEffect(() => {
    void getLatestImportJob()
      .then((job) => {
        if (job) {
          setImportJob(job);
          setIsImporting(isActiveJob(job));
        }
      })
      .catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!importJob || !isActiveJob(importJob)) {
      setIsImporting(false);
      return;
    }

    setIsImporting(true);
    const timer = window.setInterval(() => {
      void getImportJob(importJob.id)
        .then((job) => {
          setImportJob(job);
          setIsImporting(isActiveJob(job));
          if (!isActiveJob(job)) {
            setMessage(`导入完成：新增 ${job.created}，更新 ${job.updated}，跳过 ${job.skipped}，失败 ${job.failed}`);
          }
        })
        .catch((error) => setMessage(error instanceof Error ? error.message : "导入进度刷新失败。"));
    }, 1500);

    return () => window.clearInterval(timer);
  }, [importJob?.id, importJob?.status]);

  async function handleImport() {
    try {
      const urls = text
        .split(/\r?\n/)
        .map((item) => item.trim())
        .filter(Boolean);
      if (!urls.length) {
        setMessage("请先输入至少 1 个 URL。");
        setImportJob(null);
        return;
      }
      setIsImporting(true);
      setImportJob(null);
      setMessage(`正在抓取并导入 ${urls.length} 个 URL，请稍候。`);
      const job = await importUrls(urls);
      setImportJob(job);
      setIsImporting(isActiveJob(job));
      setMessage(`导入任务已启动：共 ${job.total} 个 URL。`);
    } catch (error) {
      setImportJob(null);
      setMessage(error instanceof Error ? error.message : "导入失败。");
      setIsImporting(false);
    } finally {
      // 任务型导入完成前由轮询控制 loading 状态。
    }
  }

  return (
    <main className="app-shell">
      <Nav />
      <section className="panel">
        <div className="panel-header">
          <h1>导入页面</h1>
          <button className="button-secondary" type="button" onClick={() => setText(exampleUrls)}>
            填入示例 URL
          </button>
        </div>
        <textarea
          className="json-box"
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="每行输入一个公开 URL，例如 https://example.com/blogs/news/how-to-choose"
        />
        <div className="action-row">
          <button className="button-primary" type="button" onClick={handleImport} disabled={isImporting}>
            {isImporting ? "正在抓取..." : "抓取并导入"}
          </button>
          <a className="button-secondary" href="/pages">进入页面库</a>
        </div>
        {message ? <p className="notice">{message}</p> : null}
        {importJob ? <UrlImportProgress job={importJob} /> : null}
      </section>

      <section className="panel">
        <div className="panel-header">
          <h1>手动创建单个页面</h1>
        </div>
        <div className="settings-grid">
          <label>
            <span>页面类型</span>
            <select value={singlePage.page_type} onChange={(event) => setSinglePage({ ...singlePage, page_type: event.target.value })}>
              <option value="blog">博客</option>
              <option value="collection">集合页</option>
              <option value="product">产品页</option>
            </select>
          </label>
          <label>
            <span>URL</span>
            <input value={singlePage.url} onChange={(event) => setSinglePage({ ...singlePage, url: event.target.value })} />
          </label>
          <label>
            <span>标题</span>
            <input value={singlePage.title} onChange={(event) => setSinglePage({ ...singlePage, title: event.target.value })} />
          </label>
          <label>
            <span>H1</span>
            <input value={singlePage.h1} onChange={(event) => setSinglePage({ ...singlePage, h1: event.target.value })} />
          </label>
          <label>
            <span>主题集群</span>
            <input value={singlePage.cluster_name} onChange={(event) => setSinglePage({ ...singlePage, cluster_name: event.target.value })} />
          </label>
          <label>
            <span>关键词</span>
            <input value={singlePage.keyword} onChange={(event) => setSinglePage({ ...singlePage, keyword: event.target.value })} />
          </label>
          <label>
            <span>Meta Description</span>
            <input value={singlePage.meta_description} onChange={(event) => setSinglePage({ ...singlePage, meta_description: event.target.value })} />
          </label>
          <label>
            <span>摘要</span>
            <input value={singlePage.excerpt} onChange={(event) => setSinglePage({ ...singlePage, excerpt: event.target.value })} />
          </label>
        </div>
        <textarea
          className="json-box"
          value={singlePage.raw_html}
          onChange={(event) => setSinglePage({ ...singlePage, raw_html: event.target.value })}
          placeholder="博客正文 HTML 或 Markdown；collection/product 可留空"
        />
        <div className="action-row">
          <button
            className="button-primary"
            type="button"
            onClick={() =>
              importPages([singlePage])
                .then((result) => setMessage(`单页保存完成：新增 ${result.created}，更新 ${result.updated}，跳过 ${result.skipped}`))
                .catch((error) => setMessage(error instanceof Error ? error.message : "保存失败。"))
            }
          >
            保存单页
          </button>
        </div>
      </section>
    </main>
  );
}

function Nav() {
  return <a className="text-link" href="/">返回仪表盘</a>;
}

function UrlImportProgress({ job }: { job: ImportJob }) {
  const percent = job.total ? Math.round((job.processed / job.total) * 100) : 100;

  return (
    <div className="import-progress">
      <div className="progress-header">
        <strong>{jobStatusLabel(job.status)}</strong>
        <span>{job.processed}/{job.total}，{percent}%</span>
      </div>
      <div className="progress-track">
        <div className="progress-fill" style={{ width: `${percent}%` }} />
      </div>
      <div className="muted-row">
        <span>新增 {job.created}</span>
        <span>更新 {job.updated}</span>
        <span>跳过 {job.skipped}</span>
        <span>失败 {job.failed}</span>
      </div>
      {job.error_message ? <p className="error-text">{job.error_message}</p> : null}
      <div className="list-stack">
      {job.items.map((item) => (
        <div className="compact-row" key={`${item.url}-${item.status}`}>
          <span>{statusLabel(item.status)}</span>
          <span>{item.page_type ? pageTypeLabel(item.page_type) : "未入库"}</span>
          <span>{item.title || item.reason || item.url}</span>
        </div>
      ))}
      </div>
    </div>
  );
}

function isActiveJob(job: ImportJob) {
  return job.status === "queued" || job.status === "running";
}

function jobStatusLabel(status: string) {
  const labels: Record<string, string> = {
    queued: "等待导入",
    running: "正在导入",
    completed: "导入完成",
    failed: "导入失败",
  };
  return labels[status] ?? status;
}

function statusLabel(status: string) {
  const labels: Record<string, string> = {
    created: "新增",
    updated: "更新",
    skipped: "跳过",
    failed: "失败",
    queued: "等待",
    running: "抓取中",
  };
  return labels[status] ?? status;
}

function pageTypeLabel(pageType: string) {
  const labels: Record<string, string> = {
    blog: "博客",
    collection: "集合页",
    product: "产品页",
  };
  return labels[pageType] ?? pageType;
}

const exampleUrls = [
  "https://example.com/blogs/news/how-to-choose-a-glider-recliner",
  "https://example.com/collections/glider-recliners",
  "https://example.com/products/rocking-chair",
].join("\n");
