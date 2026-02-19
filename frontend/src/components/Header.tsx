/* ──────────────────────────────────────────────────────────
 * Header — top navigation bar
 * ────────────────────────────────────────────────────────── */
import { Link } from "react-router-dom";
import { Zap } from "lucide-react";

export default function Header() {
  return (
    <header className="sticky top-0 z-50 border-b border-[var(--color-border)] bg-[var(--color-bg)]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between h-14">
        <Link to="/" className="flex items-center gap-2 group">
          <Zap className="h-5 w-5 text-[var(--color-accent)] group-hover:text-indigo-300 transition-colors" />
          <span className="font-bold text-lg tracking-tight">
            RIFT<span className="text-[var(--color-accent)]">·</span>Agent
          </span>
        </Link>

        <nav className="flex items-center gap-4 text-sm text-[var(--color-text-muted)]">
          <Link to="/" className="hover:text-[var(--color-text)] transition-colors">
            New Run
          </Link>
          <a
            href="https://github.com"
            target="_blank"
            rel="noopener noreferrer"
            className="hover:text-[var(--color-text)] transition-colors"
          >
            Docs
          </a>
        </nav>
      </div>
    </header>
  );
}
