import { useEffect, useState } from "react";

import { getDashboardStats, getHealth, getLlmSettings, saveLlmSettings } from "../api";
import type { DashboardStats, LlmSettings } from "../types";

type HealthState = "checking" | "online" | "offline";

export default function Dashboard() {
  const [health, setHealth] = useState<HealthState>("checking");
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [settings, setSettings] = useState<LlmSettings>({ enabled: false, base_url: "", api_key: "", model: "" });
  const [message, setMessage] = useState("");

  useEffect(() => {
    let isMounted = true;

    getHealth()
      .then((result) => {
        if (isMounted) {
          setHealth(result.status === "ok" ? "online" : "offline");
        }
      })
      .catch(() => {
        if (isMounted) {
          setHealth("offline");
        }
      });

    getDashboardStats()
      .then((result) => {
        if (isMounted) setStats(result);
      })
      .catch(() => undefined);

    getLlmSettings()
      .then((result) => {
        if (isMounted) setSettings(result);
      })
      .catch(() => undefined);

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">本机 MVP</p>
          <h1>内链审核工作台</h1>
        </div>
        <span className={`status-pill status-${health}`}>{labelForHealth(health)}</span>
      </section>

      <section className="metrics-grid" aria-label="页面概览">
        <Metric label="页面总数" value={String(stats?.total_pages ?? 0)} />
        <Metric label="博客" value={String(stats?.blog_count ?? 0)} />
        <Metric label="集合页" value={String(stats?.collection_count ?? 0)} />
        <Metric label="产品页" value={String(stats?.product_count ?? 0)} />
      </section>

      <section className="workspace-grid">
        <div className="panel">
          <div className="panel-header">
            <h2>快捷操作</h2>
          </div>
          <div className="action-row">
            <a className="button-primary" href="/import">
              导入页面
            </a>
            <a className="button-secondary" href="/pages">
              打开页面库
            </a>
          </div>
        </div>

        <div className="panel">
          <div className="panel-header">
            <h2>最近快照</h2>
          </div>
          {stats?.recent_snapshots.length ? (
            <div className="list-stack">
              {stats.recent_snapshots.map((item) => (
                <div className="compact-row" key={item.id}>
                  <span>{item.snapshot_type}</span>
                  <span>{new Date(item.created_at).toLocaleString()}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="empty-state">暂无本地写回快照。</div>
          )}
        </div>
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>LLM 配置</h2>
          <button
            className="button-primary"
            type="button"
            onClick={() =>
              saveLlmSettings(settings)
                .then(() => setMessage("LLM 配置已保存到本地数据库。"))
                .catch((error) => setMessage(error instanceof Error ? error.message : "保存失败。"))
            }
          >
            保存配置
          </button>
        </div>
        <div className="settings-grid">
          <label>
            <span>启用 LLM</span>
            <input type="checkbox" checked={settings.enabled} onChange={(event) => setSettings({ ...settings, enabled: event.target.checked })} />
          </label>
          <label>
            <span>接口地址</span>
            <input value={settings.base_url} onChange={(event) => setSettings({ ...settings, base_url: event.target.value })} />
          </label>
          <label>
            <span>API Key</span>
            <input value={settings.api_key} onChange={(event) => setSettings({ ...settings, api_key: event.target.value })} />
          </label>
          <label>
            <span>模型</span>
            <input value={settings.model} onChange={(event) => setSettings({ ...settings, model: event.target.value })} />
          </label>
        </div>
        {message ? <p className="notice">{message}</p> : null}
      </section>
    </main>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function labelForHealth(health: HealthState) {
  if (health === "checking") {
    return "正在检查 API";
  }

  if (health === "online") {
    return "API 在线";
  }

  return "API 离线";
}
