import type { TraceEvent } from "@/lib/types";

// Node filename == node name == span name (docs/HARVEST.md #9). These labels
// are the customer-facing names for each node in sentinel.graph — the same
// fifteen names api/run_executor.py's _GRAPH_NODE_NAMES allowlists.
const NODE_LABELS: Record<string, string> = {
  guardrail: "Screening your message",
  identity_gate: "Verifying your PIN",
  context_loader: "Loading your prior contact history",
  supervisor: "Routing to the right specialist",
  network_agent: "Network specialist reviewing your issue",
  billing_agent: "Billing specialist reviewing your issue",
  account_agent: "Account specialist reviewing your issue",
  escalation_agent: "Building a handoff to a human specialist",
  supervisor_review: "Checking the draft is grounded and in scope",
  output_guardrail: "Screening the response before you see it",
  publish: "Publishing the response",
  blocked_input_response: "Blocked at the input guardrail",
  verification_required: "Stopped — PIN verification required",
  give_up: "Could not produce a safe grounded answer",
  blocked_output_response: "Blocked at the output guardrail",
};

export function TraceTimeline({ events }: { events: TraceEvent[] }) {
  // __end__ is a stream-termination marker, not a graph step.
  const steps = events.filter((event) => event.node !== "__end__");
  if (steps.length === 0) {
    return <p style={{ fontSize: "0.875rem", color: "#737373" }}>Waiting for the first step…</p>;
  }
  return (
    <ol style={{ display: "flex", flexDirection: "column", gap: "0.5rem", padding: 0, listStyle: "none" }}>
      {steps.map((event, i) => (
        <li key={i} style={stepStyle}>
          <span style={{ fontFamily: "monospace", fontSize: "0.75rem", color: "#a3a3a3" }}>
            {i + 1}
          </span>
          <div>
            <div style={{ fontWeight: 600 }}>{NODE_LABELS[event.node] ?? event.node}</div>
            <div style={{ fontFamily: "monospace", fontSize: "0.75rem", color: "#737373" }}>
              {event.node}
            </div>
          </div>
        </li>
      ))}
    </ol>
  );
}

const stepStyle = {
  display: "flex",
  alignItems: "baseline",
  gap: "0.75rem",
  border: "1px solid #e5e5e5",
  borderRadius: "0.25rem",
  padding: "0.75rem",
  fontSize: "0.875rem",
} as const;
