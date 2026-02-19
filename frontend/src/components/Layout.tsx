/* ──────────────────────────────────────────────────────────
 * Layout — persistent chrome around pages
 * ────────────────────────────────────────────────────────── */
import type { ReactNode } from "react";
import Header from "./Header";

interface LayoutProps {
  children: ReactNode;
}

export default function Layout({ children }: LayoutProps) {
  return (
    <div className="min-h-screen bg-[var(--color-bg)] text-[var(--color-text)] flex flex-col">
      <Header />
      <main className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {children}
      </main>
      <footer className="border-t border-[var(--color-border)] py-4 text-center text-xs text-[var(--color-text-muted)]">
        RIFT 2026 — Autonomous CI/CD Healing Agent
      </footer>
    </div>
  );
}
