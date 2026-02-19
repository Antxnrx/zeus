/* ──────────────────────────────────────────────────────────
 * StatusBadge — colored pill for run/ci status
 * ────────────────────────────────────────────────────────── */
import { cn } from "@/lib/utils";

const statusConfig: Record<string, { bg: string; text: string; label: string }> = {
  queued:       { bg: "bg-yellow-500/15", text: "text-yellow-400", label: "Queued" },
  running:      { bg: "bg-blue-500/15",   text: "text-blue-400",   label: "Running" },
  passed:       { bg: "bg-green-500/15",  text: "text-green-400",  label: "Passed" },
  failed:       { bg: "bg-red-500/15",    text: "text-red-400",    label: "Failed" },
  quarantined:  { bg: "bg-orange-500/15", text: "text-orange-400", label: "Quarantined" },
  pending:      { bg: "bg-gray-500/15",   text: "text-gray-400",   label: "Pending" },
  applied:      { bg: "bg-green-500/15",  text: "text-green-400",  label: "Applied" },
  rolled_back:  { bg: "bg-orange-500/15", text: "text-orange-400", label: "Rolled Back" },
  skipped:      { bg: "bg-gray-500/15",   text: "text-gray-400",   label: "Skipped" },
  FIXED:        { bg: "bg-green-500/15",  text: "text-green-400",  label: "Fixed" },
  FAILED:       { bg: "bg-red-500/15",    text: "text-red-400",    label: "Failed" },
  PASSED:       { bg: "bg-green-500/15",  text: "text-green-400",  label: "Passed" },
  QUARANTINED:  { bg: "bg-orange-500/15", text: "text-orange-400", label: "Quarantined" },
};

interface StatusBadgeProps {
  status: string;
  className?: string;
  pulse?: boolean;
}

export default function StatusBadge({ status, className, pulse }: StatusBadgeProps) {
  const cfg = statusConfig[status] ?? { bg: "bg-gray-500/15", text: "text-gray-400", label: status };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium",
        cfg.bg,
        cfg.text,
        className,
      )}
    >
      {pulse && (
        <span className="relative flex h-2 w-2">
          <span className={cn("animate-ping absolute inline-flex h-full w-full rounded-full opacity-75", cfg.bg)} />
          <span className={cn("relative inline-flex rounded-full h-2 w-2", cfg.bg.replace("/15", "/60"))} />
        </span>
      )}
      {cfg.label}
    </span>
  );
}
