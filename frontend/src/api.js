const base = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "");
export const UUID_PATTERN =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export function validationMessage(detail) {
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail))
    return detail
      .map(
        (item) =>
          `${(item.loc || []).filter((x) => x !== "body").join(".")}: ${item.msg}`,
      )
      .join("; ");
  return "The request could not be completed.";
}

export async function request(
  path,
  { body, signal, timeout = 90000, blob = false } = {},
) {
  const controller = new AbortController();
  let timedOut = false;
  const abort = () => controller.abort();
  if (signal?.aborted) abort();
  signal?.addEventListener("abort", abort, { once: true });
  const timer = setTimeout(() => {
    timedOut = true;
    controller.abort();
  }, timeout);
  try {
    const response = await fetch(`${base}${path}`, {
      method: body === undefined ? "GET" : "POST",
      headers: {
        Accept: blob ? "text/csv" : "application/json",
        ...(body === undefined ? {} : { "Content-Type": "application/json" }),
        ...(typeof window !== "undefined" &&
        sessionStorage.getItem("eventops-demo-token")
          ? { "X-Demo-Session": sessionStorage.getItem("eventops-demo-token") }
          : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
    if (!response.ok) {
      if (response.status >= 500)
        throw new Error(
          "The backend could not complete this request. Check the API and PostgreSQL, then try again.",
        );
      const payload = await response.json().catch(() => ({}));
      if (response.status === 401 && typeof window !== "undefined")
        window.dispatchEvent(new Event("eventops-session-expired"));
      throw new Error(
        response.status === 404
          ? path.includes("conversations")
            ? "Conversation not found. Check the UUID or create a new conversation."
            : "Execution not found in this demonstration session."
          : validationMessage(payload.detail),
      );
    }
    return blob ? await response.blob() : await response.json();
  } catch (error) {
    if (timedOut)
      throw new Error(
        "The request timed out. It may still finish on the server. Reload the conversation before submitting again.",
      );
    if (controller.signal.aborted) throw error;
    if (error instanceof TypeError)
      throw new Error(
        "Cannot reach the backend. Check your connection and that the API is running on port 5050.",
      );
    throw error;
  } finally {
    clearTimeout(timer);
    signal?.removeEventListener("abort", abort);
  }
}

export const api = {
  startDemo: () => request("/api/demo/session", { body: {} }),
  connections: (signal) => request("/api/agents/connections", { signal }),
  sources: (signal) => request("/api/knowledge/sources", { signal }),
  runs: (signal) => request("/api/agents/runs", { signal }),
  run: (id, signal) =>
    request(`/api/agents/runs/${encodeURIComponent(id)}`, { signal }),
  startRun: (body) => request("/api/agents/runs", { body }),
  exportRun: (id, verifiedOnly = false) =>
    request(
      `/api/agents/runs/${encodeURIComponent(id)}/export.csv?verified_only=${verifiedOnly}`,
      { blob: true },
    ),
  health: (signal) => request("/health", { signal, timeout: 8000 }),
  list: (signal) =>
    request("/api/conversations?limit=30", { signal, timeout: 15000 }),
  create: (title) =>
    request("/api/conversations", { body: title ? { title } : {} }),
  detail: (id, signal) =>
    request(`/api/conversations/${encodeURIComponent(id)}`, { signal }),
  ask: (id, body) =>
    request(`/api/conversations/${encodeURIComponent(id)}/messages`, { body }),
  retrieve: (body) => request("/api/rag/retrieve", { body }),
};
