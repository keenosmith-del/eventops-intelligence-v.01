import { afterEach, describe, expect, it, vi } from "vitest";
import { api, request, validationMessage } from "../src/api.js";

afterEach(() => {
  vi.unstubAllGlobals();
  vi.useRealTimers();
});

describe("API compatibility and failures", () => {
  it("sends the exact conversation message contract", async () => {
    const fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        generation_status: "not_requested",
        messages: [],
      }),
    });
    vi.stubGlobal("fetch", fetch);
    await api.ask("abc", {
      question: "Where is EVT-101?",
      top_k: 5,
      generate_answer: false,
    });
    expect(fetch.mock.calls[0][0]).toBe("/api/conversations/abc/messages");
    expect(JSON.parse(fetch.mock.calls[0][1].body)).toEqual({
      question: "Where is EVT-101?",
      top_k: 5,
      generate_answer: false,
    });
    expect(fetch.mock.calls[0][1].method).toBe("POST");
  });
  it("creates a conversation with an optional title", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValue({ ok: true, json: async () => ({ id: "uuid" }) });
    vi.stubGlobal("fetch", fetch);
    await api.create("");
    expect(fetch.mock.calls[0][1].body).toBe("{}");
  });
  it("renders Pydantic validation detail without losing fields", () => {
    expect(
      validationMessage([
        {
          loc: ["body", "top_k"],
          msg: "Input should be less than or equal to 20",
        },
      ]),
    ).toBe("top_k: Input should be less than or equal to 20");
  });
  it("reports a missing conversation", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: async () => ({ detail: "Conversation not found" }),
      }),
    );
    await expect(api.detail("missing")).rejects.toThrow(
      "Conversation not found",
    );
  });
  it("does not expose internal server error text", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: async () => ({ detail: "internal connection string" }),
      }),
    );
    await expect(api.list()).rejects.toThrow("Check the API and PostgreSQL");
  });
  it("reports a network outage", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch")),
    );
    await expect(api.health()).rejects.toThrow("Cannot reach the backend");
  });
  it("times out without automatically retrying a write", async () => {
    vi.useFakeTimers();
    const fetch = vi.fn(
      (url, options) =>
        new Promise((resolve, reject) =>
          options.signal.addEventListener("abort", () =>
            reject(new DOMException("Aborted", "AbortError")),
          ),
        ),
    );
    vi.stubGlobal("fetch", fetch);
    const pending = expect(
      request("/api/conversations", { body: {}, timeout: 10 }),
    ).rejects.toThrow("Reload the conversation before submitting again");
    await vi.advanceTimersByTimeAsync(11);
    await pending;
    expect(fetch).toHaveBeenCalledTimes(1);
  });
  it("cancels a stale read through the caller signal", async () => {
    const controller = new AbortController();
    vi.stubGlobal(
      "fetch",
      vi.fn(
        (url, options) =>
          new Promise((resolve, reject) =>
            options.signal.addEventListener("abort", () =>
              reject(new DOMException("Aborted", "AbortError")),
            ),
          ),
      ),
    );
    const pending = expect(
      api.detail("abc", controller.signal),
    ).rejects.toMatchObject({ name: "AbortError" });
    controller.abort();
    await pending;
  });
});
