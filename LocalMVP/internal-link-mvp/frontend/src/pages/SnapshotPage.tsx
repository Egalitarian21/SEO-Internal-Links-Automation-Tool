import { useEffect, useState } from "react";

import { listSnapshots, rollbackSnapshot } from "../api";
import type { Snapshot } from "../types";

export default function SnapshotPage({ pageId }: { pageId: string }) {
  const [items, setItems] = useState<Snapshot[]>([]);
  const [message, setMessage] = useState("");

  async function load() {
    const result = await listSnapshots(pageId);
    setItems(result.items);
  }

  useEffect(() => {
    void load().catch((error) => setMessage(error instanceof Error ? error.message : "加载失败。"));
  }, [pageId]);

  async function handleRollback(snapshotId: string) {
    try {
      const result = await rollbackSnapshot(snapshotId);
      await load();
      setMessage(`已回滚，rollback_snapshot_id=${result.rollback_snapshot_id}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "回滚失败。");
    }
  }

  return (
    <main className="app-shell">
      <a className="text-link" href={`/workspace/${pageId}`}>返回工作台</a>
      <section className="panel">
        <div className="panel-header">
          <h1>写回快照</h1>
        </div>
        {message ? <p className="notice">{message}</p> : null}
        <div className="list-stack">
          {items.map((item) => (
            <div className="item-card" key={item.id}>
              <div className="item-card-header">
                <strong>{item.snapshot_type}</strong>
                <span className="tag">{new Date(item.created_at).toLocaleString()}</span>
              </div>
              <details>
                <summary>查看 before / after</summary>
                <h3>Before</h3>
                <pre className="html-preview">{item.before_html}</pre>
                <h3>After</h3>
                <pre className="html-preview">{item.after_html}</pre>
              </details>
              <button className="button-secondary" type="button" onClick={() => handleRollback(item.id)}>回滚到 before_html</button>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
