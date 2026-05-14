"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { endpoints } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/query/keys";


const schema = z.object({
  name: z.string().min(2),
  domain: z.string().min(3),
  owner: z.string().min(2),
  description: z.string().min(10),
});

type FormValues = z.infer<typeof schema>;

export default function NewProjectPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: "Hydra Expansion",
      domain: "hydrafitness.com",
      owner: "Content Ops",
      description: "用于验证多项目 SEO 运营流程的新 Demo 项目。",
    },
  });

  const mutation = useMutation({
    mutationFn: (values: FormValues) => endpoints.createProject(values),
    onSuccess: (project) => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      router.push(`/projects/${project.id}/import`);
    },
  });

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <section>
        <h1 className="text-3xl font-semibold">新建项目</h1>
        <p className="mt-2 text-sm text-muted">先创建项目，再进入导入、推荐、审核和发布链路，和实施方案中的信息架构保持一致。</p>
      </section>
      <form
        onSubmit={form.handleSubmit((values) => mutation.mutate(values))}
        className="rounded-lg border border-border bg-panel px-6 py-6 shadow-panel"
      >
        <div className="grid gap-4 md:grid-cols-2">
          <label className="text-sm text-muted">
            项目名称
            <input {...form.register("name")} className="mt-2 w-full rounded-md border border-border bg-panelAlt px-4 py-3 text-sm text-foreground" />
          </label>
          <label className="text-sm text-muted">
            站点域名
            <input {...form.register("domain")} className="mt-2 w-full rounded-md border border-border bg-panelAlt px-4 py-3 text-sm text-foreground" />
          </label>
          <label className="text-sm text-muted">
            负责人
            <input {...form.register("owner")} className="mt-2 w-full rounded-md border border-border bg-panelAlt px-4 py-3 text-sm text-foreground" />
          </label>
        </div>
        <label className="mt-4 block text-sm text-muted">
          项目说明
          <textarea {...form.register("description")} rows={5} className="mt-2 w-full rounded-md border border-border bg-panelAlt px-4 py-3 text-sm text-foreground" />
        </label>
        <div className="mt-6 flex items-center gap-3">
          <button type="submit" disabled={mutation.isPending} className="rounded-md bg-accent px-4 py-2.5 text-sm font-semibold text-white disabled:opacity-60">
            {mutation.isPending ? "创建中..." : "创建工作台"}
          </button>
          {mutation.error ? <p className="text-sm text-rose-700">{mutation.error.message}</p> : null}
        </div>
      </form>
    </div>
  );
}
