/* ──────────────────────────────────────────────────────────
 * ThoughtStream — scrollable list of thought events
 * ────────────────────────────────────────────────────────── */
import { useEffect, useRef } from "react";
import { Brain, GitBranch, Bug, TestTube, CheckCircle, AlertTriangle, Terminal } from "lucide-react";
import type { ThoughtEvent } from "@/types";

const nodeIcons: Record<string, React.ReactNode> = {
  repo_scanner: <GitBranch className="h-3.5 w-3.5 text-blue-400" />,
  test_runner:  <TestTube className="h-3.5 w-3.5 text-yellow-400" />,
  ast_analyzer: <Brain className="h-3.5 w-3.5 text-purple-400" />,
  fix_generator:<Bug className="h-3.5 w-3.5 text-orange-400" />,
  commit_push:  <CheckCircle className="h-3.5 w-3.5 text-green-400" />,
  ci_monitor:   <AlertTriangle className="h-3.5 w-3.5 text-cyan-400" />,
  scorer:       <Terminal className="h-3.5 w-3.5 text-pink-400" />,
};

interface ThoughtStreamProps {
  thoughts: ThoughtEvent[];
  maxHeight?: string;
}

export default function ThoughtStream({ thoughts, maxHeight = "320px" }: ThoughtStreamProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thoughts.length]);

  if (thoughts.length === 0) {
    return (
      <div className="flex items-center justify-center h-32 text-sm text-[var(--color-text-muted)]">
        Waiting for agent thoughts…
      </div>
    );
  }

  return (
    <div className="thought-stream overflow-y-auto space-y-1 pr-1" style={{ maxHeight }}>
      {thoughts.map((t, i) => (
        <div
          key={`${t.step_index}-${i}`}
          className="flex items-start gap-2 px-3 py-1.5 rounded-md hover:bg-[var(--color-surface-2)] transition-colors"
        >
          <div className="mt-0.5 flex-shrink-0">
            {nodeIcons[t.node] ?? <Terminal className="h-3.5 w-3.5 text-gray-400" />}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex items-center gap-2 text-[10px] text-[var(--color-text-muted)]">
              <span className="font-mono uppercase">{t.node}</span>
              <span>·</span>
              <span>step {t.step_index}</span>
              <span>·</span>
              <time>{new Date(t.timestamp).toLocaleTimeString()}</time>
            </div>
            <p className="text-sm leading-snug text-[var(--color-text)]">{t.message}</p>
          </div>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}
