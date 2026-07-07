import { useState } from "react";

import { createPreview, localWrite } from "../api";
import RuleCheckPanel from "../components/RuleCheckPanel";

export default function PreviewPage({ pageId }: { pageId: string }) {
  const [previewId, setPreviewId] = useState("");
  const [previewHtml, setPreviewHtml] = useState("");
  const [ruleCheck, setRuleCheck] = useState<{ passed: boolean; errors: string[]; warnings: string[] }>();
  const [message, setMessage] = useState("");

  async function handlePreview() {
    try {
      const result = await createPreview(pageId);
      setPreviewId(result.preview_id);
      setPreviewHtml(result.preview_html);
      setRuleCheck(result.rule_check);
      setMessage("预览已生成。");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "生成预览失败。");
    }
  }

  async function handleWrite() {
    try {
      const result = await localWrite(pageId, previewId);
      setMessage(`本地写回已保存，snapshot_id=${result.snapshot_id}`);
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "保存本地写回失败。");
    }
  }

  return (
    <main className="app-shell">
      <a className="text-link" href={`/review/${pageId}`}>返回审核页</a>
      <section className="panel">
        <div className="panel-header">
          <h1>插入预览</h1>
          <div className="action-row">
            <button className="button-primary" type="button" onClick={handlePreview}>生成预览</button>
            <button className="button-primary" type="button" onClick={handleWrite} disabled={!ruleCheck?.passed || !previewId}>
              保存本地写回
            </button>
            <a className="button-secondary" href={`/snapshots/${pageId}`}>查看快照</a>
          </div>
        </div>
        {message ? <p className="notice">{message}</p> : null}
        <RuleCheckPanel ruleCheck={ruleCheck} />
      </section>
      <section className="workspace-grid">
        <div className="panel">
          <h2>渲染效果</h2>
          <div className="rendered-preview" dangerouslySetInnerHTML={{ __html: previewHtml }} />
        </div>
        <div className="panel">
          <h2>HTML 源码</h2>
          <pre className="html-preview">{previewHtml}</pre>
        </div>
      </section>
    </main>
  );
}
