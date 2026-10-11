import { test, expect } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    if (!sessionStorage.getItem("eventops-demo-token")) {
      sessionStorage.setItem("eventops-demo-token", "test-reviewer-token");
    }
  });
});
const id = "11111111-1111-4111-8111-111111111111";
const conversation = {
  id,
  title: "EVT-101 briefing",
  created_at: "2026-10-10T08:00:00Z",
  updated_at: "2026-10-10T08:00:00Z",
};
const evidence = {
  document_id: "policies.csv",
  record_id: "POL-003",
  record_type: "policy",
  event_id: "EVT-101",
  content: "Check-in for EVT-101 closes at 08:45 South Africa Standard Time.",
  score: 0.78,
  source_reference: "data/structured/policies.csv#policy_id=POL-003",
  metadata: { record_type: "policy" },
};
const question = {
  id: 1,
  conversation_id: id,
  role: "user",
  kind: "question",
  content: "What time does its check-in close?",
  created_at: conversation.created_at,
  evidence: [],
};
const retrieval = {
  id: 2,
  conversation_id: id,
  role: "assistant",
  kind: "retrieval",
  content: "Retrieved 1 evidence record.",
  evidence: [evidence],
  query_plan: {
    event_id: "EVT-101",
    context_resolution: { used_context: true, inherited_event_id: "EVT-101" },
  },
  created_at: conversation.created_at,
};
const answer = {
  id: 3,
  conversation_id: id,
  role: "assistant",
  kind: "answer",
  content: "Check-in closes at 08:45.",
  evidence: [
    {
      record_id: evidence.record_id,
      source_reference: evidence.source_reference,
    },
  ],
  query_plan: { generation: { model: "test-provider" } },
  created_at: conversation.created_at,
};

async function fixtureApi(page, status = "not_requested") {
  let submitted = false;
  await page.route("**/api/demo/session", (route) =>
    route.fulfill({
      json: { session_token: "test-reviewer-token", demo_mode: false },
    }),
  );
  await page.route("**/health", (route) =>
    route.fulfill({ json: { status: "ok" } }),
  );
  await page.route("**/api/conversations**", async (route) => {
    const req = route.request();
    const path = new URL(req.url()).pathname;
    if (path.endsWith("/messages")) {
      submitted = true;
      expect(req.postDataJSON()).toEqual({
        question: "What time does its check-in close?",
        top_k: 5,
        generate_answer: status !== "not_requested",
      });
      await route.fulfill({
        json: {
          conversation_id: id,
          messages:
            status === "generated"
              ? [question, retrieval, answer]
              : [question, retrieval],
          generation_status: status,
        },
      });
    } else if (path.endsWith(id))
      await route.fulfill({ json: { conversation, messages: submitted ? (status === "generated" ? [question, retrieval, answer] : [question, retrieval]) : [] } });
    else if (req.method() === "POST")
      await route.fulfill({ status: 201, json: conversation });
    else await route.fulfill({ json: [] });
  });
}

for (const [status, text] of [
  ["not_requested", "AI generation was not requested"],
  ["generated", "AI answer generated"],
  ["unavailable", "AI answer unavailable"],
  ["insufficient_evidence", "Insufficient evidence"],
]) {
  test(`shows ${status} honestly with source evidence`, async ({ page }) => {
    await fixtureApi(page, status);
    await page.goto("/workspace");
    await expect(page.getByText("No conversations yet.")).toBeVisible();
    await page.getByLabel("Ask your first question").fill(question.content);
    if (status !== "not_requested") {
      await page.getByText("Answer options", { exact: true }).click();
      await page.getByLabel("Request Gemini answer").check();
    }
    await page.getByRole("button", { name: "Ask question" }).click();
    await expect(page.getByText(text, { exact: false })).toBeVisible();
    await expect(
      page.getByText("Context carried forward: EVT-101.", { exact: false }),
    ).toBeVisible();
    await expect(
      page.getByText(evidence.content, { exact: true }),
    ).toBeVisible();
    await expect(
      page.getByText(evidence.source_reference, { exact: true }).first(),
    ).toBeVisible();
    if (status === "generated") {
      await expect(
        page.getByText(answer.content, { exact: true }),
      ).toBeVisible();
      await page.getByRole("link", { name: "POL-003" }).click();
      await expect(page.locator("#evidence-2-0")).toHaveAttribute("open", "");
    } else
      await expect(page.getByText(answer.content, { exact: true })).toHaveCount(
        0,
      );
  });
}

test("restores original question and citations without inventing historical outcomes", async ({
  page,
}) => {
  await fixtureApi(page);
  await page.route(`**/api/conversations/${id}`, (route) =>
    route.fulfill({
      json: { conversation, messages: [question, retrieval, answer] },
    }),
  );
  await page.goto("/workspace");
  await page.getByText("Open saved chat", { exact: true }).click();
  await page.getByLabel("Open by UUID").fill(id);
  await page.getByRole("button", { name: "Open conversation by UUID" }).click();
  await expect(
    page.getByRole("heading", { name: question.content }),
  ).toBeVisible();
  await expect(page.getByRole("link", { name: "POL-003" })).toBeVisible();
  await page.reload();
  await expect(page.getByText(answer.content, { exact: true })).toBeVisible();
});

test("backend unavailable and agent preview on mobile", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.route("**/health", (route) => route.abort());
  await page.route("**/api/conversations**", (route) => route.abort());
  await page.goto("/workspace");
  await expect(
    page.getByText("Connection unavailable.", { exact: false }).first(),
  ).toBeVisible();
  await expect(
    page.getByText("Connection unavailable.", { exact: false }).first(),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Ask question" }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.route("**/api/agents/connections", (route) =>
    route.fulfill({
      json: [
        {
          id: "email",
          label: "Mailtrap Email Sandbox (read only)",
          status: "not_connected",
          note: "Server-side credentials required.",
        },
      ],
    }),
  );
  await page.route("**/api/agents/runs", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.getByRole("button", { name: "Open navigation" }).click();
  await page.getByRole("link", { name: "Agent workspace", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: "Agent workspace" }),
  ).toBeVisible();
  await expect(page.getByText("not connected", { exact: true })).toBeVisible();
});

test("validation error preserves question and permits recovery", async ({
  page,
}) => {
  await fixtureApi(page);
  await page.route(`**/api/conversations/${id}/messages`, (route) =>
    route.fulfill({
      status: 422,
      json: { detail: "The question requires event context." },
    }),
  );
  await page.goto(`/conversations/${id}`);
  await page.getByLabel("Ask your first question").fill(question.content);
  await page.getByRole("button", { name: "Ask question" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "The question requires event context.",
  );
  await expect(page.getByLabel("Ask your first question")).toHaveValue(
    question.content,
  );
});

test("unknown generation outcome on historical retrieval is explicit", async ({
  page,
}) => {
  await fixtureApi(page);
  await page.route(`**/api/conversations/${id}`, (route) =>
    route.fulfill({ json: { conversation, messages: [question, retrieval] } }),
  );
  await page.goto(`/conversations/${id}`);
  await expect(
    page.getByText("No AI answer stored.", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByText("AI generation was not requested", { exact: false }),
  ).toHaveCount(0);
});

test("real API: create, retrieve, follow up, restore original wording and source citations", async ({
  page,
  request,
}) => {
  test.skip(
    process.env.RUN_LIVE_API !== "true",
    "Opt in with RUN_LIVE_API=true; requires PostgreSQL and indexed sources.",
  );
  await page.goto("/signin");
  await page.getByRole("button", { name: "Enter workspace" }).click();
  await page.getByRole("heading", { name: "What would you like to know?" }).waitFor();
  const demoHeaders = {
    "X-Demo-Session": await page.evaluate(() =>
      sessionStorage.getItem("eventops-demo-token"),
    ),
  };
  const config = await (
    await request.get("/api/demo/config", { headers: demoHeaders })
  ).json();
  expect(
    config.generation_enabled,
    "Live browser regression requires GEMINI_ENABLED=false",
  ).toBe(false);
  await page.getByLabel("Ask your first question").fill("Where is EVT-101 being held?");
  await page.getByRole("button", { name: "Ask question" }).click();
  await expect(page).toHaveURL(/\/conversations\/[0-9a-f-]+/);
  const realId = page.url().split("/").at(-1);
  await expect(
    page.getByText("AI generation was not requested", { exact: false }),
  ).toBeVisible({ timeout: 90000 });
  await page.getByLabel("Continue the conversation").fill(question.content);
  await page.getByText("Answer options", { exact: true }).click();
  await page.getByLabel("Request Gemini answer").check();
  const exchangeResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith(`/api/conversations/${realId}/messages`) &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Ask question" }).click();
  const response = await exchangeResponse;
  let exchange = await response.json();
  if (response.status() === 429) {
    expect(exchange.detail).toContain("budget");
    await expect(page.getByRole("alert")).toContainText("budget");
    await page.getByLabel("Request Gemini answer").uncheck();
    const retry = page.waitForResponse(r => r.url().endsWith(`/conversations/${realId}/messages`) && r.request().method() === "POST");
    await page.getByRole("button", { name: "Ask question" }).click();
    const retried = await retry;
    expect(retried.status()).toBe(200);
    exchange = await retried.json();
    expect(exchange.generation_status).toBe("not_requested");
  } else {
    expect(response.status()).toBe(200);
    expect(exchange.generation_status).toBe("unavailable");
  }
  console.log(`LIVE_GENERATION_STATUS=${exchange.generation_status}`);
  await expect(
    page.getByText("Context carried forward: EVT-101.", { exact: false }),
  ).toBeVisible({ timeout: 90000 });
  const headers = {
    "X-Demo-Session": await page.evaluate(() =>
      sessionStorage.getItem("eventops-demo-token"),
    ),
  };
  const beforeResponse = await request.get(`/api/conversations/${realId}`, {
    headers,
  });
  expect(beforeResponse.ok()).toBe(true);
  const before = await beforeResponse.json();
  expect(before.conversation.title).toBe("Where is EVT-101 being held?");
  expect(
    before.messages
      .filter((message) => message.kind === "question")
      .map((message) => message.content),
  ).toEqual(["Where is EVT-101 being held?", question.content]);
  expect(
    before.messages.filter((message) => message.kind === "retrieval").at(-1)
      .evidence,
  ).toEqual(
    expect.arrayContaining([
      expect.objectContaining({
        record_id: "POL-003",
        source_reference: evidence.source_reference,
      }),
    ]),
  );
  const answers = before.messages.filter(
    (message) => message.kind === "answer",
  );
  if (answers.length)
    expect(answers.at(-1).evidence).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          record_id: "POL-003",
          source_reference: evidence.source_reference,
        }),
      ]),
    );
  console.log(
    `LIVE_VERIFICATION conversation=${realId} messages=${before.messages.length} generated_answers=${answers.length}`,
  );
  await page.reload();
  await expect(
    page.getByRole("heading", { name: question.content }),
  ).toBeVisible();
  await expect(
    page.getByText(evidence.source_reference, { exact: true }).first(),
  ).toBeVisible();
  const after = await (
    await request.get(`/api/conversations/${realId}`, { headers })
  ).json();
  expect(after.messages).toEqual(before.messages);
  await page.getByRole("link", { name: "Knowledge assistant" }).click();
  await page.locator(".chat-history-item").filter({ hasText: "Where is EVT-101 being held?" }).click();
  await expect(page.getByRole("heading", { name: question.content })).toBeVisible();
  await page.getByRole("link", { name: "Knowledge assistant" }).click();
  await page.getByText("Open saved chat", { exact: true }).click();
  await page.getByLabel("Open by UUID").fill(realId);
  await page.getByRole("button", { name: "Open conversation by UUID" }).click();
  await expect(
    page.getByRole("heading", { name: question.content }),
  ).toBeVisible();
  await page.screenshot({
    path: "/tmp/eventops-workspace-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "/tmp/eventops-workspace-mobile.png",
    fullPage: true,
  });
});

test("automatic first-message failure keeps the created chat and draft for retry", async ({ page }) => {
  await fixtureApi(page);
  let creates = 0, attempts = 0, submitted = false;
  await page.route("**/api/conversations**", async route => {
    const request = route.request(), path = new URL(request.url()).pathname;
    if (path.endsWith("/messages")) {
      attempts += 1;
      if (attempts === 1) return route.fulfill({ status: 422, json: { detail: "The question requires event context." } });
      submitted = true;
      return route.fulfill({ json: { conversation_id: id, messages: [question, retrieval], generation_status: "not_requested" } });
    }
    if (path.endsWith(id)) return route.fulfill({ json: { conversation, messages: submitted ? [question, retrieval] : [] } });
    if (request.method() === "POST") {
      creates += 1;
      expect(request.postDataJSON()).toEqual({ title: question.content });
      return route.fulfill({ status: 201, json: conversation });
    }
    return route.fulfill({ json: [conversation] });
  });
  await page.goto("/workspace");
  await page.getByLabel("Ask your first question").fill(question.content);
  await page.getByLabel("Ask your first question").press("Enter");
  await expect(page).toHaveURL(new RegExp(id));
  await expect(page.getByRole("alert")).toContainText("The question requires event context.");
  await expect(page.getByLabel("Ask your first question")).toHaveValue(question.content);
  await page.getByRole("button", { name: "Ask question" }).click();
  await expect(page.getByText("AI generation was not requested", { exact: false })).toBeVisible();
  expect(creates).toBe(1);
  expect(attempts).toBe(2);
});

test("composer source menu, multiline input, navigation rail and mobile drawer", async ({ page }) => {
  await fixtureApi(page);
  await page.route("**/api/knowledge/sources", route => route.fulfill({ json: { total_records: 3, sources: [{ document_id: "events.csv", record_count: 3 }] } }));
  await page.goto("/workspace");
  await expect(page.getByRole("heading", { name: "What would you like to know?" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Ask question" })).toBeDisabled();
  await expect(page.getByRole("complementary", { name: "Conversation context" })).toHaveCount(0);
  await page.getByLabel("Ask your first question").fill("First line");
  await page.getByLabel("Ask your first question").press("Shift+Enter");
  await expect(page.getByLabel("Ask your first question")).toHaveValue("First line\n");
  await page.getByRole("button", { name: "Knowledge documents" }).click();
  await expect(page.getByRole("link", { name: /events.csv/ })).toBeVisible();
  await expect(page.getByText("Document uploads are unavailable.")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.locator(".source-menu")).toHaveCount(0);
  await page.getByRole("button", { name: "Collapse sidebar" }).click();
  const nav = page.getByRole("link", { name: "Agent workspace", exact: true });
  await expect(nav.locator("svg")).toBeVisible();
  await nav.hover();
  await expect(page.getByRole("tooltip", { name: "Agent workspace", exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByRole("button", { name: "Expand sidebar" })).toBeVisible();
  await page.getByRole("button", { name: "Expand sidebar" }).click();
  await page.setViewportSize({ width: 390, height: 844 });
  await page.getByRole("button", { name: "Open navigation" }).click();
  await expect(page.getByRole("dialog", { name: "Workspace navigation" })).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(page.getByRole("button", { name: "Open navigation" })).toBeFocused();
  await expect(page.getByRole("dialog", { name: "Workspace navigation" })).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

test("thinking mascot follows successful and failed API requests", async ({ page }) => {
  await fixtureApi(page);
  let release;
  let gate = new Promise(resolve => { release = resolve; });
  let fail = false;
  await page.route("**/api/conversations/*/messages", async route => {
    await gate;
    await route.fulfill(fail ? { status: 503, json: { detail: "Verification service unavailable." } } : {
      json: { conversation_id: id, messages: [question, retrieval], generation_status: "not_requested" },
    });
  });
  await page.goto(`/conversations/${id}`);
  await expect(page.getByAltText("EventOps assistant")).toHaveAttribute("src", "/mascot-thinking.png");
  await expect(page.locator(".sidebar-avatar")).toHaveAttribute("src", "/mascot-head.png");
  await page.getByLabel("Ask your first question").fill(question.content);
  await page.getByRole("button", { name: "Ask question" }).click();
  await expect(page.locator(".chat-welcome .mascot-presence")).toHaveClass(/is-thinking/);
  await page.screenshot({ path: "/tmp/eventops-phase1-thinking-fixture.png", fullPage: true });
  await expect(page.getByRole("status", { name: "" }).filter({ hasText: "Reviewing sources" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Ask question" })).toBeDisabled();
  expect(await page.locator(".chat-mascot").evaluate(element => getComputedStyle(element).animationName)).toBe("none");
  release();
  await expect(page.getByRole("heading", { name: question.content })).toBeVisible();
  await expect(page.locator(".is-thinking")).toHaveCount(0);
  fail = true;
  gate = new Promise(resolve => { release = resolve; });
  await page.getByLabel("Continue the conversation").fill("Which policy supports that?");
  await page.getByRole("button", { name: "Ask question" }).click();
  await expect(page.locator(".pending-mascot.is-thinking")).toBeVisible();
  release();
  await expect(page.getByRole("alert")).toContainText("This request could not be completed. Please try again.");
  await expect(page.locator(".is-thinking")).toHaveCount(0);
  await expect(page.getByRole("button", { name: "Ask question" })).toBeEnabled();
});

test("frosted rail tooltips, shared credits and reviewer session exit", async ({ page }) => {
  await fixtureApi(page);
  await page.goto("/workspace");
  const footer = page.getByRole("contentinfo", { name: "Application credits" });
  await expect(footer).toHaveText("October 2026 © EventOps Intelligence v.01");
  await expect(footer.locator("svg")).toHaveCount(0);
  await page.getByRole("button", { name: "Collapse sidebar" }).click();
  await expect(page.getByRole("button", { name: "Expand sidebar" }).locator("svg")).toHaveClass(/lucide-arrow-right/);
  await page.keyboard.press("Tab");
  for (const name of ["Knowledge assistant", "Agent workspace", "Verification results", "Execution history", "Knowledge sources"]) {
    await page.getByRole("link", { name, exact: true }).focus();
    await expect(page.getByRole("tooltip", { name, exact: true })).toBeVisible();
  }
  for (const [label, tooltip] of [["Settings", "Settings"], ["Leave reviewer session", "Leave session"]]) {
    await page.getByRole("button", { name: label, exact: true }).focus();
    const tip = page.getByRole("tooltip", { name: tooltip, exact: true });
    await expect(tip).toBeVisible();
    expect(await tip.evaluate(element => getComputedStyle(element).backdropFilter)).toBe("blur(12px)");
  }
  await page.getByRole("button", { name: "Leave reviewer session" }).click();
  await expect(page).toHaveURL(/\/signin$/);
  expect(await page.evaluate(() => sessionStorage.getItem("eventops-demo-token"))).toBeNull();
  await expect(page.getByRole("button", { name: "Enter workspace" })).toBeVisible();
});


test("sidebar tooltips dismiss on leave, every click and navigation", async ({ page }) => {
  await fixtureApi(page);
  await page.route("**/api/agents/**", route => route.fulfill({ json: [] }));
  await page.goto("/workspace");
  await page.getByRole("button", { name: "Collapse sidebar" }).click();
  const agent = page.getByRole("link", { name: "Agent workspace", exact: true });
  const knowledge = page.getByRole("link", { name: "Knowledge assistant", exact: true });
  const tips = page.locator(".rail-tooltip:visible");
  await agent.hover();
  await expect(tips).toHaveCount(1);
  await knowledge.hover();
  await expect(tips).toHaveCount(1);
  await expect(tips).toHaveText("Knowledge assistant");
  await page.locator("main").hover();
  await expect(tips).toHaveCount(0);
  await knowledge.hover();
  await knowledge.click();
  await expect(tips).toHaveCount(0);
  await page.locator("main").hover();
  await knowledge.hover();
  await page.locator("main").click({ position: { x: 400, y: 10 } });
  await expect(tips).toHaveCount(0);
  await knowledge.hover();
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await expect(tips).toHaveCount(0);
  await agent.hover();
  await agent.click();
  await expect(page).toHaveURL(/\/agents$/);
  await expect(tips).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Agent workspace", exact: true })).toBeVisible();
  await knowledge.focus();
  await page.keyboard.press("Tab");
  await expect(agent).toBeFocused();
  await expect(tips).toHaveText("Agent workspace");
  await page.keyboard.press("Escape");
  await expect(tips).toHaveCount(0);
});


test("shared footer, collapsed-only hints, outside settings dismissal and examples", async ({ page }) => {
  await fixtureApi(page);
  let footerStyle;
  for (const path of ["/", "/signin", "/workspace"]) {
    await page.goto(path);
    const footer = page.getByRole("contentinfo", { name: "Application credits" });
    await expect(footer).toHaveText("October 2026 © EventOps Intelligence v.01");
    await expect(footer.locator("svg")).toHaveCount(0);
    const style = await footer.evaluate(element => { const s = getComputedStyle(element); return [s.fontSize, s.fontWeight, s.lineHeight, s.color, s.fontFamily]; });
    if (footerStyle) expect(style).toEqual(footerStyle);
    footerStyle = style;
  }
  await page.getByRole("button", { name: "Settings", exact: true }).hover();
  await expect(page.locator(".rail-tooltip:visible")).toHaveCount(0);
  await page.getByRole("button", { name: "Leave reviewer session" }).hover();
  await expect(page.locator(".rail-tooltip:visible")).toHaveCount(0);
  await page.getByRole("button", { name: "Settings", exact: true }).click();
  await expect(page.getByRole("region", { name: "Settings", exact: true })).toBeVisible();
  await page.getByRole("heading", { name: "What would you like to know?" }).click();
  await expect(page.getByRole("region", { name: "Settings", exact: true })).toHaveCount(0);
  const example = "What time does check-in close for EVT-101?";
  await page.getByRole("button", { name: example, exact: true }).click();
  await expect(page.getByLabel("Ask your first question")).toHaveValue(example);
  await expect(page.getByLabel("Ask your first question")).toBeFocused();
  await page.getByRole("button", { name: "Collapse sidebar" }).click();
  await page.getByRole("button", { name: "Settings", exact: true }).hover();
  await expect(page.getByRole("tooltip", { name: "Settings", exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Expand sidebar" }).click();
  await page.getByRole("button", { name: "Settings", exact: true }).hover();
  await expect(page.locator(".rail-tooltip:visible")).toHaveCount(0);
  await page.route("**/api/knowledge/sources", route => route.fulfill({ json: { total_records: 0, sources: [] } }));
  await page.getByRole("link", { name: "Knowledge sources", exact: true }).click();
  await page.getByRole("link", { name: "Return to assistant", exact: true }).click();
  await expect(page).toHaveURL(/\/workspace$/);
  for (const width of [390, 820]) {
    await page.setViewportSize({ width, height: 900 });
    const open = page.getByRole("button", { name: "Open navigation", exact: true });
    await expect(open.locator("img")).toHaveAttribute("src", "/mascot-head.png");
    await open.click();
    await expect(page.getByRole("dialog", { name: "Workspace navigation" })).toBeVisible();
    await page.getByRole("link", { name: "Return to assistant" }).click();
    await expect(open).toHaveAttribute("aria-expanded", "false");
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  }
});
