import { DocsLayout } from "fumadocs-ui/layouts/docs";
import type { ReactNode } from "react";
import { source } from "../source";

export default function Layout({ children }: { children: ReactNode }) {
  return (
    <DocsLayout
      tree={source.pageTree}
      nav={{
        title: (
          <span className="font-semibold text-base">Humanbased Docs</span>
        ),
        url: "/docs",
      }}
    >
      {children}
    </DocsLayout>
  );
}
