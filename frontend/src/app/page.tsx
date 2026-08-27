"use client";

import { useState } from "react";
import { RunConsole } from "@/components/RunConsole";

type Submitted = { question: string; accountId: string; pin: string };

export default function Home() {
  const [accountId, setAccountId] = useState("");
  const [pin, setPin] = useState("");
  const [question, setQuestion] = useState("");
  const [submitted, setSubmitted] = useState<Submitted | null>(null);

  return (
    <main style={{ maxWidth: "48rem", margin: "0 auto", padding: "2rem", fontFamily: "inherit" }}>
      <h1 style={{ fontSize: "1.5rem", fontWeight: 700 }}>Secure Service Agent</h1>
      <p style={{ marginTop: "0.5rem", fontSize: "0.875rem", color: "#737373" }}>
        Telecom customer support behind a full security envelope. Every message
        passes an input guardrail, a PIN identity gate, specialist routing, a
        grounding/scope review, and an output guardrail — streamed node by
        node so you can watch it happen. Run <code>make data</code> and check
        the console output for a synthetic demo account and PIN to try.
      </p>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          setSubmitted({ question, accountId, pin });
        }}
        style={{ marginTop: "1.5rem", display: "flex", flexDirection: "column", gap: "0.75rem" }}
      >
        <label style={labelStyle}>
          Account ID
          <input
            value={accountId}
            onChange={(e) => setAccountId(e.target.value)}
            placeholder="ACCT_2000"
            required
            style={inputStyle}
          />
        </label>
        <label style={labelStyle}>
          PIN
          <input
            value={pin}
            onChange={(e) => setPin(e.target.value)}
            type="password"
            required
            style={inputStyle}
          />
        </label>
        <label style={labelStyle}>
          Question
          <textarea
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Why is my bill higher this month?"
            required
            rows={3}
            style={{ ...inputStyle, resize: "vertical" }}
          />
        </label>
        <button type="submit" style={buttonStyle}>
          Ask
        </button>
      </form>

      <div style={{ marginTop: "2rem" }}>
        {submitted && (
          <RunConsole
            key={`${submitted.accountId}-${submitted.question}-${Date.now()}`}
            question={submitted.question}
            accountId={submitted.accountId}
            pin={submitted.pin}
          />
        )}
      </div>
    </main>
  );
}

const labelStyle = {
  display: "flex",
  flexDirection: "column",
  gap: "0.25rem",
  fontSize: "0.875rem",
  fontWeight: 600,
} as const;

const inputStyle = {
  padding: "0.5rem",
  border: "1px solid #d4d4d4",
  borderRadius: "0.25rem",
  font: "inherit",
};

const buttonStyle = {
  alignSelf: "flex-start",
  padding: "0.5rem 1.25rem",
  border: "none",
  borderRadius: "0.25rem",
  background: "#171717",
  color: "#fff",
  fontWeight: 600,
  cursor: "pointer",
} as const;
