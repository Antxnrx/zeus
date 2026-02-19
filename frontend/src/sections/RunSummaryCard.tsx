/* ──────────────────────────────────────────────────────────
 * §11.2 — Run Summary Card
 * run_id, status, branch, team, timing, progress
 * ────────────────────────────────────────────────────────── */
import {
  Clock,
  GitBranch,
  Hash,
  Users,
  Activity,
} from "lucide-react";
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
      icon={<Activity className="h-4 w-4 text-[var(--color-accent)]" />}
      glow={isRunning ? "running" : status === "passed" ? "passed" : status === "failed" ? "failed" : null}
    >
      <div className="space-y-4">
        {/* Top row: Run ID + Status */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm">
            <Hash className="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
            <span className="font-mono text-xs text-[var(--color-text-muted)]">{runId ?? "—"}</span>
          </div>
          <StatusBadge status={status} pulse={isRunning} />
        </div>

        {/* Info grid */}
        <div className="grid grid-cols-2 gap-3 text-sm">
          {branchName && (
            <div className="flex items-center gap-2">
              <GitBranch className="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
              <span className="truncate text-xs">{branchName}</span>
            </div>
          )}
          {teamName && (
            <div className="flex items-center gap-2">
              <Users className="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
              <span className="truncate text-xs">{teamName}</span>
            </div>
          )}
          <div className="flex items-center gap-2">
            <Activity className="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
            <span className="text-xs">
              Iter {iteration}/{maxIterations}
              {currentNode ? ` · ${currentNode}` : ""}
            </span>
          </div>
          {totalTime != null && (
            <div className="flex items-center gap-2">
              <Clock className="h-3.5 w-3.5 text-[var(--color-text-muted)]" />
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
