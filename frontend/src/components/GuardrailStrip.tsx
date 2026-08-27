import type { GuardrailVerdict, IdentityResult, TraceEvent } from "@/lib/types";

// The security envelope as graph structure (docs/PLAN.md): the input
// guardrail, the identity gate, and the output guardrail are each a real
// node with its own verdict, not a system-prompt disclaimer. This strip
// reads those verdicts straight out of the trace events already streaming
// in — the audit log (D-A4-7) doubling as the UI's own data source.

function findOutput<T>(events: TraceEvent[], node: string, key: string): T | null {
  const event = events.find((e) => e.node === node);
  if (!event || typeof event.output !== "object" || event.output === null) return null;
  const value = (event.output as Record<string, unknown>)[key];
  return (value as T) ?? null;
}

export function GuardrailStrip({ events }: { events: TraceEvent[] }) {
  const inputVerdict = findOutput<GuardrailVerdict>(events, "guardrail", "input_verdict");
  const identity = findOutput<IdentityResult>(events, "identity_gate", "identity");
  const outputVerdict = findOutput<GuardrailVerdict>(events, "output_guardrail", "output_verdict");

  if (!inputVerdict && !identity && !outputVerdict) return null;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "0.375rem" }}>
      {inputVerdict && (
        <Line
          ok={!inputVerdict.blocked}
          text={
            inputVerdict.blocked
              ? `Input guardrail blocked this message (${inputVerdict.layer} layer).`
              : "Input guardrail: no injection or manipulation detected."
          }
        />
      )}
      {identity && (
        <Line
          ok={identity.verified}
          text={
            identity.locked
              ? "Identity gate: account locked after too many failed PIN attempts."
              : identity.verified
                ? "Identity gate: PIN verified."
                : `Identity gate: PIN not verified (${identity.attempts_remaining} attempt(s) remaining).`
          }
        />
      )}
      {outputVerdict && (
        <Line
          ok={!outputVerdict.blocked}
          text={
            outputVerdict.blocked
              ? `Output guardrail blocked the drafted response (${outputVerdict.layer} layer) — it was discarded, not shown.`
              : "Output guardrail: response cleared for delivery."
          }
        />
      )}
    </div>
  );
}

function Line({ ok, text }: { ok: boolean; text: string }) {
  return (
    <div
      role="status"
      style={{
        borderRadius: "0.25rem",
        padding: "0.5rem",
        fontSize: "0.75rem",
        background: ok ? "#f0fdf4" : "#fef2f2",
        color: ok ? "#166534" : "#991b1b",
      }}
    >
      {text}
    </div>
  );
}
