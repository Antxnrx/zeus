/* ──────────────────────────────────────────────────────────
 * §11.1 — Input Section
 * The judge-facing form: repo_url, team_name, leader_name
 * ────────────────────────────────────────────────────────── */
import { useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { Rocket, Loader2 } from "lucide-react";
import { startRun, ApiError } from "@/lib/api";
import { useRunContext } from "@/context/RunContext";
import Card from "@/components/Card";

export default function InputSection() {
  const navigate = useNavigate();
  const { initRun } = useRunContext();

  const [repoUrl, setRepoUrl] = useState("");
  const [teamName, setTeamName] = useState("");
  const [leaderName, setLeaderName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canSubmit = repoUrl.trim() && teamName.trim() && leaderName.trim() && !loading;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!canSubmit) return;

    setLoading(true);
    setError(null);

    try {
      const res = await startRun({
        repo_url: repoUrl.trim(),
        team_name: teamName.trim(),
        leader_name: leaderName.trim(),
      });

      // Duplicate (409)
      if ("message" in res) {
        initRun(res.run_id, `/run/${res.run_id}`);
        navigate(`/run/${res.run_id}`);
        return;
      }

      // Success (202)
      initRun(res.run_id, res.socket_room);
      navigate(`/run/${res.run_id}`);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`[${err.code}] ${err.message}`);
      } else {
        setError("Unexpected error — please try again.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-7rem)]">
      <Card className="w-full max-w-lg" title="Launch Healing Run" icon={<Rocket className="h-5 w-5 text-[var(--color-accent)]" />}>
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Repo URL */}
          <div>
            <label htmlFor="repo_url" className="block text-xs font-medium text-[var(--color-text-muted)] mb-1.5">
              Repository URL
            </label>
            <input
              id="repo_url"
              type="url"
              required
              placeholder="https://github.com/org/repo"
              value={repoUrl}
              onChange={(e) => setRepoUrl(e.target.value)}
              className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]/50 focus:border-[var(--color-accent)] transition"
            />
          </div>

          {/* Team Name */}
          <div>
            <label htmlFor="team_name" className="block text-xs font-medium text-[var(--color-text-muted)] mb-1.5">
              Team Name
            </label>
            <input
              id="team_name"
              type="text"
              required
              placeholder="Team Alpha"
              value={teamName}
              onChange={(e) => setTeamName(e.target.value)}
              className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]/50 focus:border-[var(--color-accent)] transition"
            />
          </div>

          {/* Leader Name */}
          <div>
            <label htmlFor="leader_name" className="block text-xs font-medium text-[var(--color-text-muted)] mb-1.5">
              Leader Name
            </label>
            <input
              id="leader_name"
              type="text"
              required
              placeholder="Jane Smith"
              value={leaderName}
              onChange={(e) => setLeaderName(e.target.value)}
              className="w-full rounded-lg border border-[var(--color-border)] bg-[var(--color-bg)] px-3 py-2 text-sm placeholder:text-gray-600 focus:outline-none focus:ring-2 focus:ring-[var(--color-accent)]/50 focus:border-[var(--color-accent)] transition"
            />
          </div>

          {/* Error */}
          {error && (
            <div className="rounded-lg bg-red-500/10 border border-red-500/30 px-3 py-2 text-sm text-red-400">
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            type="submit"
            disabled={!canSubmit}
            className="w-full flex items-center justify-center gap-2 rounded-lg bg-[var(--color-accent)] hover:bg-indigo-500 disabled:opacity-40 disabled:cursor-not-allowed px-4 py-2.5 text-sm font-medium text-white transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Starting…
              </>
            ) : (
              <>
                <Rocket className="h-4 w-4" />
                Start Run
              </>
            )}
          </button>
        </form>
      </Card>
    </div>
  );
}
