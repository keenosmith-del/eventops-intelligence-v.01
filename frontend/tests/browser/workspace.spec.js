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
      await route.fulfill({ json: { conversation, messages: [] } });
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
    await page.goto("/");
    await page
      .getByText("Conversation history", { exact: false })
      .first()
      .click();
    await expect(page.getByText("No conversations yet.")).toBeVisible();
    await page.getByLabel("Conversation title").fill("EVT-101 briefing");
    await page.getByRole("button", { name: "Create conversation" }).click();
    await page.getByLabel("Ask your first question").fill(question.content);
    if (status !== "not_requested")
      await page.getByLabel("Request Gemini answer").check();
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
  await page.goto("/");
  await page
    .getByText("Conversation history", { exact: false })
    .first()
    .click();
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
  await page.goto("/");
  await expect(
    page.getByText("API unreachable", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("The backend is unreachable.", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Create conversation" }),
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
  await page.getByRole("link", { name: "Agent Workspace" }).click();
  await expect(
    page.getByRole("heading", { name: "From sources to decisions." }),
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
  await page.getByRole("button", { name: "Continue as reviewer" }).click();
  await page.getByRole("heading", { name: "Ask with confidence." }).waitFor();
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
  await page
    .getByLabel("Conversation title")
    .fill(`Frontend verification ${new Date().toISOString()}`);
  await page.getByRole("button", { name: "Create conversation" }).click();
  await expect(page).toHaveURL(/\/conversations\/[0-9a-f-]+/);
  const realId = page.url().split("/").at(-1);
  await page
    .getByLabel("Ask your first question")
    .fill("Where is EVT-101 being held?");
  await page.getByRole("button", { name: "Ask question" }).click();
  await expect(
    page.getByText("AI generation was not requested", { exact: false }),
  ).toBeVisible({ timeout: 90000 });
  await page.getByLabel("Continue the conversation").fill(question.content);
  await page.getByLabel("Request Gemini answer").check();
  const exchangeResponse = page.waitForResponse(
    (response) =>
      response.url().endsWith(`/api/conversations/${realId}/messages`) &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Ask question" }).click();
  const exchange = await (await exchangeResponse).json();
  expect(exchange.generation_status).toBe("unavailable");
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
  await page.getByRole("link", { name: "Knowledge Assistant" }).click();
  await page
    .getByText("Conversation history", { exact: false })
    .first()
    .click();
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
