import { ApiError } from "./client";
import { ApiResponse, Message, Source } from "./types";

export interface StreamMessageHandlers {
  onSources?: (sources: Source[]) => void;
  onToken?: (token: string) => void;
  onDone?: (message: Message) => void;
  onError?: (error: ApiError) => void;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api/v1";

export async function streamMessage(
  conversationId: number,
  content: string,
  handlers: StreamMessageHandlers,
  signal?: AbortSignal
): Promise<void> {
  const token = localStorage.getItem("accessToken");

  let response: Response;
  try {
    response = await fetch(
      `${API_BASE_URL}/conversations/${conversationId}/messages`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({ content }),
        signal,
      }
    );
  } catch (fetchErr: unknown) {
    if (signal?.aborted) {
      return;
    }
    const err = new ApiError(
      "Network connection failed during chat stream",
      0
    );
    handlers.onError?.(err);
    throw err;
  }

  // If initial response is not OK (e.g. 404, 409, 401, 429), parse error JSON envelope
  if (!response.ok) {
    let errorData: ApiResponse<null> | null = null;
    try {
      errorData = (await response.json()) as ApiResponse<null>;
    } catch {
      // Body not JSON
    }

    const apiError = new ApiError(
      errorData?.message || `HTTP ${response.status}: Request failed`,
      response.status,
      errorData?.errorCode,
      errorData?.errors
    );
    handlers.onError?.(apiError);
    throw apiError;
  }

  const reader = response.body?.getReader();
  if (!reader) {
    const err = new ApiError("Streaming not supported by browser", 500);
    handlers.onError?.(err);
    throw err;
  }

  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // SSE frames are separated by double newlines (\n\n or \r\n\r\n)
      const events = buffer.split(/\r?\n\r?\n/);
      buffer = events.pop() || "";

      for (const eventBlock of events) {
        if (!eventBlock.trim()) continue;

        let eventType = "message";
        let eventData = "";

        const lines = eventBlock.split(/\r?\n/);
        for (const line of lines) {
          if (line.startsWith("event:")) {
            eventType = line.replace(/^event:\s*/, "").trim();
          } else if (line.startsWith("data:")) {
            eventData += (eventData ? "\n" : "") + line.replace(/^data:\s*/, "");
          }
        }

        if (!eventData) continue;

        try {
          if (eventType === "sources") {
            const sources: Source[] = JSON.parse(eventData);
            handlers.onSources?.(sources);
          } else if (eventType === "token") {
            const tokenPayload = JSON.parse(eventData);
            handlers.onToken?.(tokenPayload.text || "");
          } else if (eventType === "done") {
            const doneEnvelope: ApiResponse<Message> = JSON.parse(eventData);
            handlers.onDone?.(doneEnvelope.data);
          } else if (eventType === "error") {
            const errorEnvelope: ApiResponse<null> = JSON.parse(eventData);
            const streamErr = new ApiError(
              errorEnvelope.message || "An error occurred during generation",
              500,
              errorEnvelope.errorCode,
              errorEnvelope.errors
            );
            handlers.onError?.(streamErr);
            return;
          }
        } catch (parseErr) {
          console.warn("Failed to parse SSE event data:", eventData, parseErr);
        }
      }
    }
  } catch (err: unknown) {
    if (signal?.aborted) {
      return;
    }
    const apiError =
      err instanceof ApiError
        ? err
        : new ApiError(
            err instanceof Error ? err.message : "Stream connection broken",
            500
          );
    handlers.onError?.(apiError);
    throw apiError;
  } finally {
    reader.releaseLock();
  }
}
