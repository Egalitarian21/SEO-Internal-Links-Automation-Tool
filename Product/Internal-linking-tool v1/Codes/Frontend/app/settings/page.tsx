import { EmptyState } from "@/components/shared/empty-state";


export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <section>
        <h1 className="text-3xl font-semibold">设置</h1>
        <p className="mt-2 text-sm text-muted">预留给后续规则配置、客户级策略包和仪表盘观测项扩展。</p>
      </section>
      <EmptyState title="配置区已预留" description="实施方案里提到的多客户规则配置和健康度仪表盘，会从这里继续往下长。" />
    </div>
  );
}
