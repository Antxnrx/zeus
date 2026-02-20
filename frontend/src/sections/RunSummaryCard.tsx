/* ──────────────────────────────────────────────────────────
 * §11.2 — Run Summary Card
 * run_id, status, branch, team, timing, progress
 * ────────────────────────────────────────────────────────── */
import { useRunContext } from "@/context/RunContext";
import Card from "@/components/Card";
import StatusBadge from "@/components/StatusBadge";
import ProgressBar from "@/components/ProgressBar";

export default function RunSummaryCard() {
  const { state } = useRunContext();
  const { runId, status, currentNode, iteration, maxIterations, progressPct, results } = state;

  const totalTime = results?.total_time_secs;
  const branchName = results?.branch_name;
  const teamName = results?.team_name;

  const isRunning = status === "running" || status === "queued";

  return (
    <Card
      title="Run Summary"
      glow={isRunning ? "running" : status === "passed" ? "passed" : status === "failed" ? "failed" : null}
    >
      <div className="space-y-4">
        {/* Top row: Run ID + Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm">
            <span className="text-xs text-[var(--color-text-muted)]">Run ID</span>
            <span className="font-mono text-xs text-[var(--color-text)] border border-black/10 px-2 py-0.5">{runId ?? "—"}</span>
          </div>
          <StatusBadge status={status} pulse={isRunning} />
        </div>

        {/* Info grid */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          {branchName && (
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase font-mono text-[var(--color-text-muted)]">Branch</span>
              <span className="truncate text-xs">{branchName}</span>
            </div>
          )}
          {teamName && (
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase font-mono text-[var(--color-text-muted)]">Team</span>
              <span className="truncate text-xs">{teamName}</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <span className="text-[10px] uppercase font-mono text-[var(--color-text-muted)]">Step</span>
            <span className="text-xs">
              Iter {iteration}/{maxIterations}
              {currentNode ? ` · ${currentNode}` : ""}
            </span>
          </div>
          {totalTime != null && (
            <div className="flex items-center gap-2">
              <span className="text-[10px] uppercase font-mono text-[var(--color-text-muted)]">Total</span>
              <span className="text-xs">{totalTime.toFixed(1)}s</span>
            </div>
          )}
        </div>

        {/* Progress */}
        <ProgressBar value={progressPct} />
      </div>
    </Card>
  );
}
