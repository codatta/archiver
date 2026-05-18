import type { Metadata } from "next";
import { RootProvider } from "fumadocs-ui/provider/next";
import { Inter } from "next/font/google";
import "fumadocs-ui/style.css";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: {
    template: "%s — Humanbased Docs",
    default: "Humanbased Developer Docs",
  },
  description: "Documentation for the Humanbased Data API, CLI, and developer portal.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.className} suppressHydrationWarning>
      <body className="flex flex-col min-h-screen">
        <RootProvider>{children}</RootProvider>
      </body>
    </html>
  );
}
