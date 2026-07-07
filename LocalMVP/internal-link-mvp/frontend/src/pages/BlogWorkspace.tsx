import { useEffect, useState } from "react";

import { generateAnchors, generateRecommendations, getPage, listAnchors, listBlocks, parseArticle } from "../api";
import AnchorCandidateCard from "../components/AnchorCandidateCard";
import type { AnchorCandidate, ArticleBlock, Page } from "../types";

export default function BlogWorkspace({ pageId }: { pageId: string }) {
  const [page, setPage] = useState<Page | null>(null);
  const [blocks, setBlocks] = useState<ArticleBlock[]>([]);
  const [anchors, setAnchors] = useState<AnchorCandidate[]>([]);
  const [message, setMessage] = useState("");

  async function load() {
    const nextPage = await getPage(pageId);
    setPage(nextPage);
    setBlocks((await listBlocks(pageId)).items);
    setAnchors((await listAnchors(pageId)).items);
  }

  async function run(action: () => Promise<unknown>, success: string) {
    try {
      await action();
      await load();
      setMessage(success);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "操作失败。");
    }
  }

  useEffect(() => {
    void load().catch((error) => setMessage(error instanceof Error ? error.message : "加载失败。"));
  }, [pageId]);

  if (!page) return <main className="app-shell"><p>正在加载页面...</p></main>;

  return (
    <main className="app-shell">
      <a className="text-link" href="/pages">返回页面库</a>
      <section className="panel">
        <div className="panel-header">
          <div>
            <h1>{page.title}</h1>
            <p>{page.url}</p>
          </div>
          <a className="button-secondary" href={`/snapshots/${page.id}`}>快照</a>
        </div>
        <div className="detail-grid">
          <span>H1：{page.h1 || "-"}</span>
          <span>主题集群：{page.cluster_name || "-"}</span>
          <span>关键词：{page.keyword || "-"}</span>
          <span>Meta：{page.meta_description || "-"}</span>
        </div>
        <pre className="html-preview">{page.raw_html}</pre>
        <div className="action-row">
          <button className="button-primary" onClick={() => run(() => parseArticle(page.id), "正文解析完成。")}>解析正文</button>
          <button className="button-primary" onClick={() => run(() => generateAnchors(page.id), "候选锚文本已生成。")}>生成候选锚文本</button>
          <button className="button-primary" onClick={() => run(() => generateRecommendations(page.id), "候选链接已生成。")}>生成候选链接</button>
          <a className="button-secondary" href={`/review/${page.id}`}>进入审核页</a>
        </div>
        {message ? <p className="notice">{message}</p> : null}
      </section>

      <section className="workspace-grid">
        <div className="panel">
          <h2>正文块</h2>
          <div className="list-stack">
            {blocks.map((block) => (
              <div className="item-card" key={block.id}>
                <div className="item-card-header">
                  <strong>{block.block_index}. {block.block_type}</strong>
                  <span className="tag">{block.has_existing_link ? "已有链接" : block.is_first_paragraph ? "首段" : "可候选"}</span>
                </div>
                <p>{block.content}</p>
              </div>
            ))}
          </div>
        </div>
        <div className="panel">
          <h2>候选锚文本</h2>
          <div className="list-stack">
            {anchors.map((item) => <AnchorCandidateCard key={item.id} item={item} />)}
          </div>
        </div>
      </section>
    </main>
  );
}
