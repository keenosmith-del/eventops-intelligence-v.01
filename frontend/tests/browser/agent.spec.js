import { test, expect } from "@playwright/test";

const id = "22222222-2222-4222-8222-222222222222";
const nodes = [
  "trigger",
  "calendar",
  "email",
  "web",
  "extraction",
  "normalization",
  "deduplication",
  "verification",
  "discrepancy",
  "persistence",
  "export",
];
const fixtureRun = {
  id,
  event_id: "EVT-101",
  status: "partial",
  created_at: "2026-10-10T12:00:00Z",
  finished_at: "2026-10-10T12:01:00Z",
  summary: {
    total: 1,
    verified: 0,
    flagged: 1,
    duplicates_merged: 0,
    tools: { calendar: "completed", email: "skipped", web: "completed" },
  },
  steps: nodes.map((node, i) => ({
    node_id: node,
    position: i,
    status:
      node === "email"
        ? "skipped"
        : node === "export"
          ? "pending"
          : "completed",
    inputs: { max_records: 10 },
    outputs: { test_fixture: true },
    error: node === "email" ? "Mailtrap not configured." : null,
  })),
  results: [
    {
      id: "claim-1",
      status: "review_required",
      event_id: "",
      title: "Holiday observation",
      email: "",
      full_name: "",
      starts_at: "2026-01-01",
      venue: "",
      duplicate_count: 0,
      issues: ["missing_event_id"],
      evidence: [
        {
          source_type: "calendar",
          source_reference: "https://example.com/fixture.ics",
          source_record_id: "holiday-1",
          excerpt: "Test fixture only",
        },
      ],
      matches: [],
    },
  ],
};

async function seed(page) {
  await page.addInitScript(() =>
    sessionStorage.setItem("eventops-demo-token", "test-token"),
  );
  await page.route("**/health", (r) => r.fulfill({ json: { status: "ok" } }));
  await page.route("**/api/agents/connections", (r) =>
    r.fulfill({
      json: [
        {
          id: "email",
          label: "Mailtrap Email Sandbox",
          status: "not_connected",
          note: "Configure server credentials.",
        },
      ],
    }),
  );
  await page.route("**/api/agents/runs**", (r) => {
    const path = new URL(r.request().url()).pathname;
    if (path.endsWith("/export.csv"))
      return r.fulfill({
        contentType: "text/csv",
        body: "id,status\nclaim-1,review_required\n",
      });
    if (path.endsWith(id)) return r.fulfill({ json: fixtureRun });
    return r.fulfill({
      status: r.request().method() === "POST" ? 202 : 200,
      json: r.request().method() === "POST" ? fixtureRun : [fixtureRun],
    });
  });
}

test("reviewer entry is explicit and sidebar collapse works", async ({
  page,
}) => {
  await page.route("**/api/demo/session", (r) =>
    r.fulfill({ json: { session_token: "fixture-session" } }),
  );
  await page.route("**/health", (r) => r.fulfill({ json: { status: "ok" } }));
  await page.route("**/api/conversations**", (r) => r.fulfill({ json: [] }));
  await page.goto("/signin");
  await expect(
    page.getByText("Demonstration access, not account authentication.", {
      exact: false,
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Continue as reviewer" }).click();
  await expect(
    page.getByRole("heading", { name: "Ask with confidence." }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Collapse sidebar" }).click();
  await expect(
    page.getByRole("button", { name: "Expand sidebar" }),
  ).toHaveAttribute("aria-expanded", "false");
});

test("persisted graph, discrepancy evidence and CSV export", async ({
  page,
}) => {
  await seed(page);
  await page.goto("/agents");
  await page.getByRole("button", { name: "Run verification" }).click();
  await expect(page).toHaveURL(new RegExp(id));
  await expect(
    page.getByRole("heading", { name: "Execution · partial" }),
  ).toBeVisible();
  await page
    .getByRole("button", { name: "Email sandbox · skipped", exact: true })
    .click();
  await expect(
    page.getByText("Mailtrap not configured.", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Inspect record" }).click();
  await expect(
    page.getByText("Test fixture only", { exact: true }),
  ).toBeVisible();
  const downloaded = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export all CSV" }).click();
  expect((await downloaded).suggestedFilename()).toContain(id);
  await page.getByRole("link", { name: "Execution History" }).click();
  await page.getByRole("button", { name: /EVT-101 · partial/ }).click();
  await expect(
    page.getByRole("heading", { name: "Execution · partial" }),
  ).toBeVisible();
});

test("knowledge sources show live counts without an upload action", async ({
  page,
}) => {
  await seed(page);
  await page.route("**/api/knowledge/sources", (r) =>
    r.fulfill({
      json: {
        total_records: 19,
        sources: [
          {
            document_id: "events.csv",
            record_count: 3,
            indexed_count: 3,
            records: [
              {
                record_id: "EVT-101",
                record_type: "event",
                indexed: true,
                content: "Fixture event",
                metadata: {
                  source_reference:
                    "data/structured/events.csv#event_id=EVT-101",
                  source_sha256: "a".repeat(64),
                },
              },
            ],
          },
        ],
      },
    }),
  );
  await page.goto("/sources");
  await expect(
    page.getByText("19 total records", { exact: false }),
  ).toBeVisible();
  await page.getByText("EVT-101", { exact: true }).click();
  await expect(
    page.getByText("data/structured/events.csv#event_id=EVT-101", {
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.getByRole("button", { name: /Upload/ })).toHaveCount(0);
});

test("live Journey B: real tools, graph, persisted flags, export and history", async ({
  page,
}) => {
  test.skip(
    process.env.RUN_LIVE_API !== "true",
    "Opt in to real read-only HTTPS tools.",
  );
  await page.goto("/signin");
  await page.getByRole("button", { name: "Continue as reviewer" }).click();
  await page.getByRole("link", { name: "Agent Workspace" }).click();
  await page.getByRole("button", { name: "Run verification" }).click();
  await expect(page).toHaveURL(/\/agents\/runs\/[a-f0-9-]+/);
  const runId = page.url().split("/").at(-1);
  await expect(
    page.getByRole("heading", { name: "Execution · partial" }),
  ).toBeVisible({ timeout: 90000 });
  await page
    .getByRole("button", { name: "Email sandbox · skipped", exact: true })
    .click();
  await expect(
    page.getByText("Mailtrap sandbox is not connected.", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Calendar feed · completed",
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", {
      name: "Web reference · completed",
      exact: true,
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Inspect record" }).first().click();
  await expect(
    page.getByRole("heading", { name: "Observed evidence" }),
  ).toBeVisible();
  const downloaded = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export all CSV" }).click();
  const download = await downloaded;
  expect(download.suggestedFilename()).toContain(runId);
  await download.saveAs("../docs/submission/sample-verification.csv");
  await page.getByRole("link", { name: "Execution History" }).click();
  await page
    .getByRole("button", { name: new RegExp(runId.slice(0, 8)) })
    .click();
  await expect(
    page.getByRole("heading", { name: "Execution · partial" }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("button", { name: "CSV export · completed", exact: true }),
  ).toBeVisible();
  console.log("LIVE_AGENT_RUN=" + runId);
  await page.screenshot({
    path: "../docs/submission/screenshots/agent-execution-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "../docs/submission/screenshots/agent-execution-mobile.png",
    fullPage: true,
  });
});
