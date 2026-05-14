"use client";

import { LogIn } from "lucide-react";


export default function LoginPage() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="w-full max-w-md rounded-xl border border-border bg-panel px-8 py-10 shadow-panel">
        <div className="w-fit rounded-full bg-accentSoft p-3 text-accent">
          <LogIn className="h-6 w-6" />
        </div>
        <h1 className="mt-6 text-3xl font-semibold">内链自动化审阅台</h1>
        <p className="mt-2 text-sm text-muted">这里保留给后续 Auth.js 接入使用，当前 Demo 默认直达工作台。</p>
        <form className="mt-8 space-y-4">
          <input className="w-full rounded-md border border-border bg-panelAlt px-4 py-3 text-sm" defaultValue="seo.ops@hydrafitness.com" />
          <input type="password" className="w-full rounded-md border border-border bg-panelAlt px-4 py-3 text-sm" defaultValue="demo-password" />
          <button type="button" className="w-full rounded-md bg-accent px-4 py-3 text-sm font-semibold text-white">
            进入工作台
          </button>
        </form>
      </div>
    </div>
  );
}
