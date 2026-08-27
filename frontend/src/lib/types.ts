// Plain hand-written types mirroring `sentinel/api/schemas.py` — no
// generated-types tooling for a frontend this small (docs/PLAN.md Phase 5).

export type TraceEvent = {
  node: string;
  output: unknown;
};

// Mirrors `sentinel/schemas/guardrail.py::GuardrailVerdict` and
// `sentinel/schemas/identity.py::IdentityResult` — the two shapes
// GuardrailStrip reads out of the trace events it's already displaying.
export type GuardrailVerdict = {
  blocked: boolean;
  layer: "deterministic" | "llm";
  rule_id: string | null;
  reason: string;
};

export type IdentityResult = {
  verified: boolean;
  locked: boolean;
  attempts_remaining: number;
};

export type CreateChatResponse = {
  id: string;
  status: string;
};

export type CostSummaryEntry = {
  node: string;
  model: string;
  prompt_tokens: number;
  completion_tokens: number;
  cost_usd: number;
};

export type ChatRunResponse = {
  id: string;
  question: string;
  account_id: string;
  status: string;
  created_at: string;
  updated_at: string;
  response: string | null;
  error: string | null;
  total_cost_usd: number;
  costs: CostSummaryEntry[];
};

export function isTraceEvent(value: unknown): value is TraceEvent {
  return (
    typeof value === "object" &&
    value !== null &&
    "node" in value &&
    typeof (value as { node: unknown }).node === "string"
  );
}
