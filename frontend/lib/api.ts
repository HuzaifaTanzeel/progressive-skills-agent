export type SkillTier = "read-only" | "draft-only";

export type ToolCall = {
  name: string;
  args: Record<string, unknown>;
};

export type ChatRequest = {
  message: string;
  user_id?: string;
  session_id?: string | null;
};

export type ChatResponse = {
  response: string;
  skill_used: string | null;
  tool_trajectory: ToolCall[];
  session_id: string;
};

export type EvalMetric = {
  metric_name: string;
  score: number | null;
  threshold: number | null;
  eval_status: string;
  match_type: string | null;
};

export type EvalCase = {
  eval_id: string;
  status: string;
  metrics: EvalMetric[];
  source_file: string | null;
};

export type EvalSkillSummary = {
  skill_id: string;
  tier: SkillTier | string;
  owner: string;
  trajectory_mode: string | null;
  accuracy: number;
  passed: number;
  total: number;
  last_result: string;
  cases: EvalCase[];
};

export type AdversarialCase = {
  eval_set_id: string;
  eval_id: string;
  prompt_summary: string;
  expected_skill: string;
  must_not_load_skill?: string;
  must_not_call_tool?: string;
  must_call_tool?: string;
  last_result: string;
  source_file: string | null;
};

export type TokenBudgetComparison = {
  l1_index: number;
  largest_l2_skill: string;
  largest_l2: number;
  progressive: number;
  monolithic: number;
  reduction_pct: number;
  system_instruction: number;
};

export type TokenBudgetReport = {
  run_date: string;
  encoding: string;
  comparison: TokenBudgetComparison;
  body_by_skill?: Record<string, number>;
  ref_by_skill?: Record<string, number>;
  per_skill?: Record<
    string,
    { l2_body: number; references: number; combined: number }
  >;
};

export type EvalSummary = {
  skills: EvalSkillSummary[];
  adversarial: AdversarialCase[];
  token_budget: TokenBudgetReport;
  regression: Record<string, unknown>;
  sources: Record<string, unknown>;
};

function apiBase(): string {
  const base = process.env.NEXT_PUBLIC_API_URL;
  if (!base) {
    throw new Error(
      "NEXT_PUBLIC_API_URL is not set. Copy .env.local.example to .env.local.",
    );
  }
  return base.replace(/\/$/, "");
}

export async function sendChat(body: ChatRequest): Promise<ChatResponse> {
  const res = await fetch(`${apiBase()}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: body.message,
      user_id: body.user_id ?? "demo_user",
      session_id: body.session_id ?? null,
    }),
  });

  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(
      detail || `Chat request failed (${res.status} ${res.statusText})`,
    );
  }

  return res.json() as Promise<ChatResponse>;
}

export async function fetchEvalSummary(): Promise<EvalSummary> {
  const res = await fetch(`${apiBase()}/api/admin/eval-summary`);

  if (!res.ok) {
    const detail = await res.text().catch(() => "");
    throw new Error(
      detail || `Eval summary failed (${res.status} ${res.statusText})`,
    );
  }

  return res.json() as Promise<EvalSummary>;
}

/** Build skill_id → tier map; returns empty map on failure. */
export async function fetchSkillTiers(): Promise<
  Record<string, SkillTier>
> {
  try {
    const summary = await fetchEvalSummary();
    const map: Record<string, SkillTier> = {};
    for (const skill of summary.skills ?? []) {
      if (
        skill.skill_id &&
        (skill.tier === "read-only" || skill.tier === "draft-only")
      ) {
        map[skill.skill_id] = skill.tier;
      }
    }
    return map;
  } catch {
    return {};
  }
}
