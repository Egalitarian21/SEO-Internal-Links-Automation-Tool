import { useEffect, useState } from "react";

import { listPages } from "../api";
import PageCard from "../components/PageCard";
import type { Page } from "../types";

export default function PageLibrary() {
  const [items, setItems] = useState<Page[]>([]);
  const [pageType, setPageType] = useState("");
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");

  async function load(options: { silent?: boolean } = {}) {
    try {
      const result = await listPages({ page_type: pageType, query, status: "published" });
      setItems(result.items);
      setMessage("");
    } catch (error) {
      if (!options.silent) {
        setMessage(error instanceof Error ? error.message : "加载失败。");
      }
    }
  }

  useEffect(() => {
    void load();
    const timer = window.setInterval(() => {
      void load({ silent: true });
    }, 3000);

    return () => window.clearInterval(timer);
  }, [pageType, query]);

  return (
    <main className="app-shell">
      <div className="nav-row">
        <a className="text-link" href="/">返回仪表盘</a>
        <a className="text-link" href="/import">返回导入页面</a>
      </div>
      <section className="panel">
        <div className="panel-header">
          <h1>页面库</h1>
          <span className="tag">自动刷新</span>
        </div>
        <div className="toolbar">
          <select value={pageType} onChange={(event) => setPageType(event.target.value)}>
            <option value="">全部类型</option>
            <option value="blog">博客</option>
            <option value="collection">集合页</option>
            <option value="product">产品页</option>
          </select>
          <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="搜索标题、URL、关键词" />
          <button className="button-primary" type="button" onClick={() => load()}>搜索</button>
        </div>
        {message ? <p className="error-text">{message}</p> : null}
        <div className="list-stack">
          {items.map((page) => (
            <div key={page.id} className="library-row">
              <PageCard page={page} />
              {page.page_type === "blog" ? <a className="button-primary" href={`/workspace/${page.id}`}>进入工作台</a> : null}
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
