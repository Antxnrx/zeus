/* ──────────────────────────────────────────────────────────
 * §11.3 — Score Breakdown Panel
 * base, speed_bonus, efficiency_penalty, total (visual)
 * ────────────────────────────────────────────────────────── */
import { Trophy, TrendingUp, TrendingDown, Minus } from "lucide-react";
import { useRunContext } from "@/context/RunContext";
import Card from "@/components/Card";
import ScoreGauge from "@/components/ScoreGauge";

export default function ScoreBreakdownPanel() {
  const { state } = useRunContext();
  const score = state.results?.score ?? state.completionEvent?.score ?? null;

  if (!score) {
    return (
      <Card title="Score Breakdown" icon={<Trophy className="h-4 w-4 text-yellow-400" />}>
        <div className="flex items-center justify-center h-40 text-sm text-[var(--color-text-muted)]">
          Score will appear when the run completes.
        </div>
      </Card>
    );
  }

  const rows = [
    {
      label: "Base Score",
      value: score.base,
      icon: <Minus className="h-3.5 w-3.5 text-blue-400" />,
      color: "text-blue-400",
    },
    {
      label: "Speed Bonus",
      value: score.speed_bonus,
      icon: <TrendingUp className="h-3.5 w-3.5 text-green-400" />,
      color: "text-green-400",
      prefix: "+",
    },
    {
      label: "Efficiency Penalty",
      value: score.efficiency_penalty,
      icon: <TrendingDown className="h-3.5 w-3.5 text-red-400" />,
      color: "text-red-400",
      prefix: score.efficiency_penalty <= 0 ? "" : "-",
    },
  ];

  return (
    <Card title="Score Breakdown" icon={<Trophy className="h-4 w-4 text-yellow-400" />}>
      <div className="flex items-center gap-6">
        {/* Gauge */}
        <ScoreGauge total={score.total} />

        {/* Breakdown table */}
        <div className="flex-1 space-y-3">
          {rows.map((r) => (
            <div key={r.label} className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                {r.icon}
                <span className="text-[var(--color-text-muted)]">{r.label}</span>
              </div>
              <span className={`font-mono font-semibold ${r.color}`}>
                {r.prefix ?? ""}
                {r.value.toFixed(1)}
              </span>
            </div>
          ))}

          <div className="border-t border-[var(--color-border)] pt-2 flex items-center justify-between text-sm">
            <span className="font-semibold">Total</span>
            <span className="font-mono font-bold text-lg">{score.total.toFixed(1)}</span>
          </div>
        </div>
      </div>
    </Card>
  );
}
