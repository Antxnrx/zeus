/* ──────────────────────────────────────────────────────────
 * ScoreGauge — circular gauge for total score
 * ────────────────────────────────────────────────────────── */
interface ScoreGaugeProps {
  total: number;
  maxScore?: number;
  size?: number;
}

export default function ScoreGauge({ total, maxScore = 100, size = 140 }: ScoreGaugeProps) {
  const radius = (size - 16) / 2;
  const circumference = 2 * Math.PI * radius;
  const pct = Math.min(1, Math.max(0, total / maxScore));
  const offset = circumference * (1 - pct);

  const color =
    pct >= 0.75 ? "stroke-green-400" : pct >= 0.5 ? "stroke-yellow-400" : "stroke-red-400";

  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      <svg className="-rotate-90" width={size} height={size}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          className="text-[var(--color-surface-2)]"
          strokeWidth={8}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          className={color}
          strokeWidth={8}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.8s ease-out" }}
        />
      </svg>
      <div className="absolute flex flex-col items-center">
        <span className="text-2xl font-bold tabular-nums">{total.toFixed(1)}</span>
        <span className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-wider">
          Score
        </span>
      </div>
    </div>
  );
}
