/* ──────────────────────────────────────────────────────────
 * Card — reusable surface card
 * ────────────────────────────────────────────────────────── */
import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface CardProps {
  title?: string;
  subtitle?: string;
  icon?: ReactNode;
  children: ReactNode;
  className?: string;
  glow?: "running" | "passed" | "failed" | null;
}

export default function Card({ title, subtitle, icon, children, className, glow }: CardProps) {
  const glowCls =
    glow === "running"
      ? "status-glow-running"
      : glow === "passed"
        ? "status-glow-passed"
        : glow === "failed"
          ? "status-glow-failed"
          : "";

  return (
    <div
      className={cn(
        "rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5",
        glowCls,
        className,
      )}
    >
      {(title || icon) && (
        <div className="flex items-center gap-2 mb-4">
          {icon}
          <div>
            {title && <h3 className="text-sm font-semibold">{title}</h3>}
            {subtitle && (
              <p className="text-xs text-[var(--color-text-muted)]">{subtitle}</p>
            )}
          </div>
        </div>
      )}
      {children}
    </div>
  );
}
