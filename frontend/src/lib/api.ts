import { type ChatRunResponse, type CreateChatResponse, type TraceEvent, isTraceEvent } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number
  ) {
    super(message);
  }
}

export async function createChat(
  question: string,
  accountId: string,
  pin: string
): Promise<CreateChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ question, account_id: accountId, pin }),
  });
  if (!response.ok) {
    throw new ApiError(`Failed to start chat (${response.status})`, response.status);
  }
  return response.json() as Promise<CreateChatResponse>;
}

export async function getChat(id: string): Promise<ChatRunResponse> {
  const response = await fetch(`${API_BASE}/chat/${id}`);
  if (!response.ok) {
    throw new ApiError(`Failed to fetch chat (${response.status})`, response.status);
  }
  return response.json() as Promise<ChatRunResponse>;
}

export type TraceEventHandlers = {
  onEvent: (event: TraceEvent) => void;
  onEnd: () => void;
  onError: () => void;
};

/** Subscribes to GET /chat/{id}/events (SSE). Returns a cleanup function
 * that closes the connection — call it on unmount. */
export function streamChatEvents(id: string, handlers: TraceEventHandlers): () => void {
  const source = new EventSource(`${API_BASE}/chat/${id}/events`);
  source.onmessage = (message) => {
    let parsed: unknown;
    try {
      parsed = JSON.parse(message.data as string);
    } catch {
      handlers.onError();
      return;
    }
    if (!isTraceEvent(parsed)) {
      handlers.onError();
      return;
    }
    handlers.onEvent(parsed);
    if (parsed.node === "__end__") {
      source.close();
      handlers.onEnd();
    }
  };
  source.onerror = () => {
    source.close();
    handlers.onError();
  };
  return () => source.close();
}
