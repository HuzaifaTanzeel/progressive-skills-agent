"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { SkillBadge } from "@/components/SkillBadge";
import {
  fetchEvalSummary,
  type AdversarialCase,
  type EvalSkillSummary,
  type SkillTier,
  type TokenBudgetReport,
} from "@/lib/api";

function metricPassRate(
  skill: EvalSkillSummary,
  metricName: string,
): { passed: number; total: number } {
  let passed = 0;
  let total = 0;
  for (const c of skill.cases ?? []) {
    const m = c.metrics?.find((x) => x.metric_name === metricName);
    if (!m) continue;
    total += 1;
    if (m.eval_status === "PASS") passed += 1;
  }
  return { passed, total };
}

function StatusPill({ status }: { status: string }) {
  const ok = status === "PASS";
  const unknown = status === "UNKNOWN" || !status;
  return (
    <span
      className={
        ok
          ? "font-mono text-xs font-semibold uppercase tracking-wide text-teal-bright"
          : unknown
            ? "font-mono text-xs font-semibold uppercase tracking-wide text-sand-dim"
            : "font-mono text-xs font-semibold uppercase tracking-wide text-danger"
      }
    >
      {status || "UNKNOWN"}
    </span>
  );
}

function SkillCard({ skill }: { skill: EvalSkillSummary }) {
  const trajectory = metricPassRate(skill, "tool_trajectory_avg_score");
  const response = metricPassRate(skill, "final_response_match_v2");
  const tier =
    skill.tier === "read-only" || skill.tier === "draft-only"
      ? (skill.tier as SkillTier)
      : undefined;

  return (
    <article className="rounded-xl border border-ink-muted bg-ink-raised/60 p-4">
      <div className="flex flex-wrap items-start justify-between gap-2">
        <SkillBadge skillName={skill.skill_id} tier={tier} />
        <StatusPill status={skill.last_result} />
      </div>

      <dl className="mt-4 grid grid-cols-2 gap-x-3 gap-y-2 text-sm">
        <div>
          <dt className="text-xs text-sand-dim">Tier</dt>
          <dd className="font-mono text-sand">{skill.tier}</dd>
        </div>
        <div>
          <dt className="text-xs text-sand-dim">Owner</dt>
          <dd className="truncate font-mono text-xs text-sand" title={skill.owner}>
            {skill.owner || "—"}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-sand-dim">Trajectory mode</dt>
          <dd className="font-mono text-sand">
            {skill.trajectory_mode ?? "—"}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-sand-dim">Cases</dt>
          <dd className="font-mono text-sand">
            {skill.passed}/{skill.total} (
            {Math.round((skill.accuracy ?? 0) * 100)}%)
          </dd>
        </div>
      </dl>

      <div className="mt-4 space-y-2 border-t border-ink-muted pt-3">
        <p className="text-xs font-medium uppercase tracking-wide text-sand-dim">
          Trigger / trajectory
        </p>
        <div className="flex flex-wrap gap-x-4 gap-y-1 text-sm">
          <span>
            <span className="text-sand-dim">Response match: </span>
            <span className="font-mono text-sand">
              {response.total
                ? `${response.passed}/${response.total}`
                : "—"}
            </span>
          </span>
          <span>
            <span className="text-sand-dim">Trajectory: </span>
            <span className="font-mono text-sand">
              {trajectory.total
                ? `${trajectory.passed}/${trajectory.total}`
                : "—"}
            </span>
          </span>
        </div>
      </div>
    </article>
  );
}

function TokenBudgetSection({ report }: { report: TokenBudgetReport }) {
  const c = report.comparison;
  const max = Math.max(c.monolithic, c.progressive, 1);
  const progressivePct = Math.round((c.progressive / max) * 100);
  const monolithicPct = Math.round((c.monolithic / max) * 100);

  return (
    <section>
      <h2 className="font-display text-xl font-semibold text-sand">
        Token budget
      </h2>
      <p className="mt-1 text-sm text-sand-dim">
        Progressive disclosure vs monolithic prompt ({report.encoding},{" "}
        {report.run_date})
      </p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <div className="rounded-xl border border-teal/40 bg-ink-raised/80 px-5 py-6">
          <p className="text-xs uppercase tracking-wide text-sand-dim">
            Progressive (L1 + largest L2)
          </p>
          <p className="mt-2 font-display text-4xl font-semibold tabular-nums text-teal-bright sm:text-5xl">
            {c.progressive.toLocaleString()}
          </p>
          <p className="mt-1 text-sm text-sand-dim">tokens / typical turn</p>
        </div>
        <div className="rounded-xl border border-ink-muted bg-ink-raised/40 px-5 py-6">
          <p className="text-xs uppercase tracking-wide text-sand-dim">
            Monolithic baseline
          </p>
          <p className="mt-2 font-display text-4xl font-semibold tabular-nums text-sand sm:text-5xl">
            {c.monolithic.toLocaleString()}
          </p>
          <p className="mt-1 text-sm text-sand-dim">
            all L2 bodies + references
          </p>
        </div>
      </div>

      <p className="mt-4 text-center font-display text-2xl font-semibold text-teal-bright">
        {c.reduction_pct}% fewer tokens
      </p>

      <div className="mt-6 space-y-3" role="img" aria-label="Token comparison bars">
        <div>
          <div className="mb-1 flex justify-between text-xs text-sand-dim">
            <span>Progressive</span>
            <span className="font-mono">{c.progressive}</span>
          </div>
          <div className="h-3 overflow-hidden rounded bg-ink-muted">
            <div
              className="h-full rounded bg-teal transition-[width] duration-700"
              style={{ width: `${progressivePct}%` }}
            />
          </div>
        </div>
        <div>
          <div className="mb-1 flex justify-between text-xs text-sand-dim">
            <span>Monolithic</span>
            <span className="font-mono">{c.monolithic}</span>
          </div>
          <div className="h-3 overflow-hidden rounded bg-ink-muted">
            <div
              className="h-full rounded bg-sand-dim/70 transition-[width] duration-700"
              style={{ width: `${monolithicPct}%` }}
            />
          </div>
        </div>
      </div>

      <p className="mt-4 text-xs leading-relaxed text-sand-dim">
        At only 4 skills, savings look modest vs a ~50-skill catalog. Progressive
        disclosure savings scale with library size — this demo proves the
        mechanism, not production magnitude.
      </p>
    </section>
  );
}

function AdversarialTable({ cases }: { cases: AdversarialCase[] }) {
  return (
    <section>
      <h2 className="font-display text-xl font-semibold text-sand">
        Adversarial boundary cases
      </h2>
      <p className="mt-1 text-sm text-sand-dim">
        Explicit pass/fail checks for cross-skill routing and draft-only
        boundaries (read-only).
      </p>

      <div className="mt-4 overflow-x-auto rounded-xl border border-ink-muted">
        <table className="w-full min-w-[40rem] border-collapse text-left text-sm">
          <thead>
            <tr className="border-b border-ink-muted bg-ink-raised text-xs uppercase tracking-wide text-sand-dim">
              <th className="px-3 py-2.5 font-medium">Case</th>
              <th className="px-3 py-2.5 font-medium">Prompt</th>
              <th className="px-3 py-2.5 font-medium">Boundary</th>
              <th className="px-3 py-2.5 font-medium">Result</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((c) => {
              const boundary = [
                c.expected_skill ? `expect ${c.expected_skill}` : null,
                c.must_not_load_skill
                  ? `must not load ${c.must_not_load_skill}`
                  : null,
                c.must_call_tool ? `must call ${c.must_call_tool}` : null,
                c.must_not_call_tool
                  ? `must not call ${c.must_not_call_tool}`
                  : null,
              ]
                .filter(Boolean)
                .join(" · ");

              return (
                <tr
                  key={`${c.eval_set_id}:${c.eval_id}`}
                  className="border-b border-ink-muted/70 last:border-0"
                >
                  <td className="px-3 py-2.5 align-top">
                    <span className="font-mono text-xs text-sand">
                      {c.eval_id}
                    </span>
                    <span className="mt-0.5 block font-mono text-[0.65rem] text-sand-dim">
                      {c.eval_set_id}
                    </span>
                  </td>
                  <td className="px-3 py-2.5 align-top text-sand">
                    {c.prompt_summary}
                  </td>
                  <td className="px-3 py-2.5 align-top font-mono text-xs text-sand-dim">
                    {boundary || "—"}
                  </td>
                  <td className="px-3 py-2.5 align-top">
                    <StatusPill status={c.last_result} />
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<Awaited<
    ReturnType<typeof fetchEvalSummary>
  > | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    void fetchEvalSummary()
      .then((data) => {
        if (!cancelled) {
          setSummary(data);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Failed to load eval summary",
          );
          setSummary(null);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="flex min-h-screen flex-col bg-ink">
      <header className="border-b border-ink-muted px-4 py-5 sm:px-6">
        <div className="mx-auto flex max-w-5xl flex-wrap items-end justify-between gap-3">
          <div>
            <p className="font-display text-2xl font-semibold tracking-tight text-sand sm:text-3xl">
              Eval dashboard
            </p>
            <p className="mt-1 text-sm text-sand-dim">
              Read-only view of harness reports — no editing
            </p>
          </div>
          <nav className="flex gap-4 text-sm">
            <Link
              href="/"
              className="text-sand-dim transition-colors hover:text-teal-bright"
            >
              Chat
            </Link>
            <span className="text-teal-bright" aria-current="page">
              Dashboard
            </span>
          </nav>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 space-y-10 px-4 py-8 sm:px-6">
        {loading ? (
          <p className="text-sm text-sand-dim">Loading eval summary…</p>
        ) : null}

        {error ? (
          <p className="text-sm text-danger" role="alert">
            {error}
          </p>
        ) : null}

        {summary ? (
          <>
            <section>
              <h2 className="font-display text-xl font-semibold text-sand">
                Skills
              </h2>
              <p className="mt-1 text-sm text-sand-dim">
                Per-skill tier, owner, and trigger/trajectory results from the
                latest Phase 5 summary
                {typeof summary.sources?.phase5_run_date === "string"
                  ? ` (${summary.sources.phase5_run_date})`
                  : ""}
                .
              </p>
              <div className="mt-4 grid gap-4 sm:grid-cols-2">
                {summary.skills.map((skill) => (
                  <SkillCard key={skill.skill_id} skill={skill} />
                ))}
              </div>
            </section>

            {summary.token_budget?.comparison ? (
              <TokenBudgetSection report={summary.token_budget} />
            ) : null}

            {summary.adversarial?.length ? (
              <AdversarialTable cases={summary.adversarial} />
            ) : null}
          </>
        ) : null}
      </main>
    </div>
  );
}
