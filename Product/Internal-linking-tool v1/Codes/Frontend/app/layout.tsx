import type { Metadata } from "next";
import { ReactNode } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { Providers } from "@/app/providers";
import "@/app/globals.css";


export const metadata: Metadata = {
  title: "SEO 内链自动化 Demo",
  description: "面向 SEO 团队的内链推荐、审核与发布工作台",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>
        <Providers>
          <AppShell>{children}</AppShell>
        </Providers>
      </body>
    </html>
  );
}
