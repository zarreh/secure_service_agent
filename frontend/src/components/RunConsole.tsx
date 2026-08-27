"use client";

import { useEffect, useRef, useState } from "react";
import { createChat, getChat, streamChatEvents } from "@/lib/api";
import type { ChatRunResponse, TraceEvent } from "@/lib/types";
import { TraceTimeline } from "./TraceTimeline";
import { GuardrailStrip } from "./GuardrailStrip";
import { CostMeter } from "./CostMeter";

type Phase = "loading" | "streaming" | "success" | "error";

export function RunConsole({
  question,
  accountId,
  pin,
}: {
  question: string;
  accountId: string;
  pin: string;
}) {
  const [phase, setPhase] = useState<Phase>("loading");
  const [events, setEvents] = useState<TraceEvent[]>([]);
  const [chat, setChat] = useState<ChatRunResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const cleanupRef = useRef<() => void>(() => {});

  useEffect(() => {
    let cancelled = false;

    async function finish(id: string) {
      try {
        const result = await getChat(id);
        if (cancelled) return;
        setChat(result);
        setPhase(result.status === "failed" ? "error" : "success");
        if (result.status === "failed") {
          setErrorMessage(result.error ?? "The run failed.");
        }
      } catch {
        if (!cancelled) {
          setPhase("error");
          setErrorMessage("Could not fetch the finished run.");
        }
      }
    }

    async function start() {
      setPhase("loading");
      setEvents([]);
      setChat(null);
      setErrorMessage(null);
      try {
        const created = await createChat(question, accountId, pin);
        if (cancelled) return;
        setPhase("streaming");
        cleanupRef.current = streamChatEvents(created.id, {
          onEvent: (event) => {
            if (cancelled) return;
            setEvents((prev) => [...prev, event]);
          },
          onEnd: () => {
            if (cancelled) return;
            void finish(created.id);
          },
          onError: () => {
            if (cancelled) return;
            setPhase("error");
            setErrorMessage("Lost connection to the run stream.");
          },
        });
      } catch {
        if (!cancelled) {
          setPhase("error");
          setErrorMessage("Could not start the run.");
        }
      }
    }

    void start();
    return () => {
      cancelled = true;
      cleanupRef.current();
    };
  }, [question, accountId, pin]);

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "1.5rem" }}>
      <p style={{ borderRadius: "0.25rem", background: "#f5f5f5", padding: "0.5rem", fontSize: "0.75rem", color: "#525252" }}>
        You asked: <strong>{question}</strong> (account {accountId})
      </p>

      {phase === "loading" && <p role="status" style={{ fontSize: "0.875rem", color: "#737373" }}>Starting the run…</p>}

      {phase === "error" && (
        <p role="alert" style={{ borderRadius: "0.25rem", background: "#fef2f2", padding: "0.75rem", fontSize: "0.875rem", color: "#991b1b" }}>
          {errorMessage}
        </p>
      )}

      {(phase === "streaming" || phase === "success") && <TraceTimeline events={events} />}

      {(phase === "streaming" || phase === "success") && <GuardrailStrip events={events} />}

      {phase === "success" && chat?.response && (
        <div style={{ borderRadius: "0.25rem", border: "1px solid #e5e5e5", padding: "1rem" }}>
          <h3 style={{ fontSize: "0.75rem", fontWeight: 600, textTransform: "uppercase", color: "#737373", marginTop: 0 }}>
            Response
          </h3>
          <p style={{ whiteSpace: "pre-wrap", margin: 0 }}>{chat.response}</p>
        </div>
      )}

      {chat && phase === "success" && <CostMeter chat={chat} />}
    </div>
  );
}
