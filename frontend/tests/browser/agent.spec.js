import { test, expect } from "@playwright/test";
import { readFile } from "node:fs/promises";

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
    page.getByText("Reviewer demonstration access", {
      exact: false,
    }),
  ).toBeVisible();

  await page.getByRole("button", { name: "Enter workspace" }).click();

  await expect(
    page.getByRole("heading", { name: "What would you like to know?" }),
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
  await expect(page.locator(".react-flow__node")).toHaveCount(11);
  await page
    .locator('.react-flow__node[data-id="email"]')
    .scrollIntoViewIfNeeded();

  await expect(
    page.locator('.react-flow__node[data-id="email"]'),
  ).toBeInViewport();

  await page.locator('.react-flow__node[data-id="email"]').click();
  for (const node of nodes)
    await expect(
      page.locator(`.react-flow__node[data-id="${node}"]`),
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

  await page
    .getByRole("link", { name: "Execution history", exact: true })
    .click();
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

  await expect(page.getByText("csv source", { exact: true })).toBeVisible();

  await expect(
    page.getByText("All records indexed · event", { exact: true }),
  ).toBeVisible();
});

test("operational views share credits and fit mobile layouts", async ({
  page,
}) => {
  await seed(page);

  await page.route("**/api/knowledge/sources", (route) =>
    route.fulfill({ json: { total_records: 0, sources: [] } }),
  );

  for (const path of [
    "/agents",
    `/verification/${id}`,
    `/history/${id}`,
    "/sources",
  ]) {
    await page.goto(path);

    await expect(
      page.getByRole("contentinfo", { name: "Application credits" }),
    ).toBeVisible();

    await expect(page.getByRole("contentinfo")).toContainText(
      "October 2026 © EventOps Intelligence v.01",
    );

    await page.setViewportSize({ width: 390, height: 844 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);

    await page.getByRole("button", { name: "Open navigation" }).click();

    await page.keyboard.press("Tab");

    await page.getByRole("button", { name: "Settings", exact: true }).focus();

    await expect(
      page.getByRole("tooltip", { name: "Settings", exact: true }),
    ).toHaveCount(0);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.keyboard.press("Escape");
    await page.setViewportSize({ width: 1280, height: 900 });
  }
});

test("live Journey B: real tools, graph, persisted flags, export and history", async ({
  page,
}) => {
  test.skip(
    process.env.RUN_LIVE_API !== "true",
    "Opt in to real read-only HTTPS tools.",
  );
  await page.goto("/signin");
  await page.getByRole("button", { name: "Enter workspace" }).click();
  await page
    .getByRole("link", { name: "Agent workspace", exact: true })
    .click();
  await page.getByRole("button", { name: "Run verification" }).click();
  await expect(page).toHaveURL(/\/agents\/runs\/[a-f0-9-]+/);
  const runId = page.url().split("/").at(-1);
  await expect(
    page.getByRole("heading", { name: /Execution · (partial|completed)/ }),
  ).toBeVisible({ timeout: 90000 });
  await page
    .getByRole("button", {
      name: /Email sandbox · (completed|skipped|failed)/,
      exact: true,
    })
    .click();

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

  await download.saveAs("/tmp/eventops-redesigned-verification.csv");

  const stored = await page.evaluate(
    async (id) =>
      (
        await fetch(`/api/agents/runs/${id}`, {
          headers: {
            "X-Demo-Session": sessionStorage.getItem("eventops-demo-token"),
          },
        })
      ).json(),
    runId,
  );

  expect(stored.results.length).toBe(stored.summary.total);

  expect(stored.results.every((record) => record.checks?.length > 0)).toBe(
    true,
  );

  for (const verifiedOnly of [false, true]) {
    const actualCsv = await page.evaluate(
      async ({ id, verifiedOnly }) =>
        (
          await fetch(
            `/api/agents/runs/${id}/export.csv?verified_only=${verifiedOnly}`,
            {
              headers: {
                "X-Demo-Session": sessionStorage.getItem("eventops-demo-token"),
              },
            },
          )
        ).text(),
      { id: runId, verifiedOnly },
    );

    if (!verifiedOnly)
      expect(
        (
          await readFile("/tmp/eventops-redesigned-verification.csv", "utf8")
        ).replace(/^\uFEFF/, ""),
      ).toBe(actualCsv.replace(/^\uFEFF/, ""));
    else {
      const verifiedDownload = page.waitForEvent("download");
      await page.getByRole("button", { name: "Export verified CSV" }).click();
      await (await verifiedDownload).saveAs("/tmp/eventops-part2-verified.csv");
      expect(
        (await readFile("/tmp/eventops-part2-verified.csv", "utf8")).replace(
          /^\uFEFF/,
          "",
        ),
      ).toBe(actualCsv.replace(/^\uFEFF/, ""));
    }
  }
  await expect(
    page.getByRole("heading", { name: "Field-level verification decisions" }),
  ).toBeVisible();

  await expect(
    page.getByRole("heading", { name: "Raw extracted values" }),
  ).toBeVisible();

  await expect(
    page.getByRole("region", { name: "CSV analysis" }),
  ).toContainText(
    `${stored.results.filter((record) => record.issues.some((issue) => issue.startsWith("missing_"))).length} records with missing fields`,
  );

  await page.locator(".flow-surface").scrollIntoViewIfNeeded();

  for (const node of nodes)
    await expect(
      page.locator(`.react-flow__node[data-id="${node}"]`),
    ).toBeVisible();

  await expect(
    page.locator('.react-flow__node[data-id="email"]'),
  ).toBeInViewport();
  await page.locator(".flow-surface").screenshot({
    path: "../docs/iterations/post-submission/evidence/consolidation/part2-graph-desktop.png",
  });

  await page.screenshot({
    path: "../docs/iterations/post-submission/evidence/consolidation/part2-agent-desktop.png",
    fullPage: true,
  });

  await page.setViewportSize({ width: 390, height: 844 });

  await page.locator(".flow-surface").scrollIntoViewIfNeeded();

  for (const node of nodes)
    await expect(
      page.locator(`.react-flow__node[data-id="${node}"]`),
    ).toBeVisible();

  await expect(
    page.locator('.react-flow__node[data-id="email"]'),
  ).toBeInViewport();

  await page.locator(".flow-surface").screenshot({
    path: "../docs/iterations/post-submission/evidence/consolidation/part2-graph-mobile.png",
  });

  await page.screenshot({
    path: "../docs/iterations/post-submission/evidence/consolidation/part2-agent-mobile.png",
    fullPage: true,
  });

  await page.setViewportSize({ width: 1280, height: 900 });

  await page.goto(`/verification/${runId}`);

  await expect(
    page.getByRole("button", { name: "Inspect record" }).first(),
  ).toBeVisible();

  await page.screenshot({
    path: "../docs/iterations/post-submission/evidence/consolidation/part2-results-desktop.png",
    fullPage: true,
  });

  await page.getByRole("link", { name: "Knowledge sources" }).click();

  await expect(
    page.getByText("19 total records", { exact: false }),
  ).toBeVisible();
  await page.screenshot({
    path: "../docs/iterations/post-submission/evidence/consolidation/part2-sources-desktop.png",
    fullPage: true,
  });

  await page
    .getByRole("link", { name: "Execution history", exact: true })
    .click();
  await page
    .getByRole("button", { name: new RegExp(runId.slice(0, 8)) })
    .click();
  await expect(
    page.getByRole("heading", { name: /Execution · (partial|completed)/ }),
  ).toBeVisible();
  await page.reload();
  const restored = await page.evaluate(
    async (id) =>
      (
        await fetch(`/api/agents/runs/${id}`, {
          headers: {
            "X-Demo-Session": sessionStorage.getItem("eventops-demo-token"),
          },
        })
      ).json(),
    runId,
  );

  expect(restored.steps).toEqual(stored.steps);

  expect(restored.results).toEqual(stored.results);

  console.log("LIVE_AGENT_RUN=" + runId);
  await page.screenshot({
    path: "../docs/iterations/post-submission/evidence/consolidation/part2-history-desktop.png",
    fullPage: true,
  });

  await page.setViewportSize({ width: 390, height: 844 });

  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: "../docs/iterations/post-submission/evidence/consolidation/part2-history-mobile.png",
    fullPage: true,
  });
});

test("real polling follows persisted stages and allows manual inspection", async ({
  page,
}) => {
  await seed(page);
  let stage = "calendar";
  let finished = false;
  const snapshot = () => ({
    ...fixtureRun,
    status: finished ? "partial" : "running",
    results: finished ? fixtureRun.results : [],
    steps: fixtureRun.steps.map((step, index) => ({
      ...step,
      status: finished
        ? step.status
        : index < nodes.indexOf(stage)
          ? "completed"
          : step.node_id === stage
            ? "running"
            : "pending",
      started_at: "2026-10-10T12:00:00Z",
      finished_at: finished ? "2026-10-10T12:00:01Z" : null,
    })),
  });

  await page.route(`**/api/agents/runs/${id}`, (route) =>
    route.fulfill({ json: snapshot() }),
  );

  await page.goto(`/agents/runs/${id}`);

  await expect(page.locator(".step-detail h2")).toHaveText("Calendar feed");

  await expect(page.locator(".flow-stage.running")).toHaveCount(1);

  await page
    .getByRole("button", { name: "Run trigger · completed", exact: true })
    .click();
  stage = "email";

  await expect(
    page.getByRole("button", { name: "Email sandbox · running", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".step-detail h2")).toHaveText("Run trigger");
  await page.getByRole("button", { name: "Follow progress" }).click();
  await expect(page.locator(".step-detail h2")).toHaveText("Email sandbox");
  stage = "web";
  await expect(page.locator(".step-detail h2")).toHaveText("Web reference");
  await expect(page.locator(".react-flow__edge.animated")).toHaveCount(1);
  finished = true;
  await expect(
    page.getByRole("heading", { name: "Execution · partial" }),
  ).toBeVisible();
  await expect(page.locator(".flow-stage.running")).toHaveCount(0);
  await expect(page.locator(".react-flow__edge.animated")).toHaveCount(0);
});

test("recorded replay uses timestamps, pauses and never starts another run", async ({
  page,
}) => {
  await seed(page);
  let requests = 0;
  const saved = {
    ...fixtureRun,
    summary: {
      ...fixtureRun.summary,
      execution_mode: "controlled_assessment_fixture",
    },
    steps: fixtureRun.steps.map((step, index) => ({
      ...step,
      started_at:
        step.node_id === "export"
          ? "2026-10-10T12:07:00Z"
          : new Date(
              Date.parse("2026-10-10T12:00:00Z") + index * 2000,
            ).toISOString(),
      finished_at:
        step.node_id === "export"
          ? "2026-10-10T12:07:01Z"
          : new Date(
              Date.parse("2026-10-10T12:00:00Z") + index * 2000 + 1000,
            ).toISOString(),
      outputs: { record_count: 1 },
    })),
  };
  await page.route(`**/api/agents/runs/${id}`, (route) => {
    requests++;

    return route.fulfill({ json: saved });
  });

  await page.goto(`/history/${id}`);

  await page
    .getByRole("button", { name: "Replay execution", exact: true })
    .click();

  const replay = page.getByRole("region", {
    name: "Recorded execution replay",
  });
  await expect(replay).toContainText("No new run or tool calls");

  await page.getByRole("button", { name: "Pause replay" }).click();

  await expect(replay).toContainText("Paused");

  const timeline = page.getByLabel("Recorded timeline");

  await expect(timeline).toHaveAttribute("max", "19000");

  await timeline.fill("2500");

  await expect(
    page.getByRole("button", { name: "Calendar feed · running", exact: true }),
  ).toBeVisible();

  await expect(
    page.getByRole("button", { name: "Web reference · pending", exact: true }),
  ).toBeVisible();

  await expect(
    page.locator('.react-flow__node[data-id="extraction"]'),
  ).not.toContainText("1 records");
  await expect(timeline).toHaveValue("2500");

  await page
    .getByRole("button", { name: "Return to complete execution" })
    .click();
  await expect(
    page.getByRole("button", {
      name: "Calendar feed · completed",
      exact: true,
    }),
  ).toBeVisible();

  await expect(
    page.getByRole("button", { name: "Email sandbox · skipped", exact: true }),
  ).toBeVisible();

  expect(requests).toBe(1);
});

test("minimal controls, inspection focus and closing saved history", async ({
  page,
}) => {
  await seed(page);

  await page.goto("/agents");

  for (const label of ["Reference event", "Records per source"]) {
    const input = page.getByLabel(label);
    await input.click();
    expect(
      await input.evaluate(
        (element) => getComputedStyle(element).borderTopWidth,
      ),
    ).toBe("0px");
    expect(
      await input.evaluate((element) =>
        parseFloat(getComputedStyle(element).outlineWidth),
      ),
    ).toBeLessThanOrEqual(1);
  }
  const button = page.getByRole("button", { name: "Run verification" });

  const normal = await button.evaluate(
    (element) => getComputedStyle(element).backgroundColor,
  );

  await button.hover();

  await expect(button).toHaveCSS("background-color", "rgb(45, 54, 56)");

  expect(normal).not.toBe("rgb(45, 54, 56)");

  await expect(button).toHaveCSS("transform", "matrix(1, 0, 0, 1, 0, -2)");

  await page.goto(`/verification/${id}`);

  await page
    .getByRole("button", { name: "Inspect record", exact: true })
    .click();

  await expect(
    page.getByRole("region", { name: "Record evidence" }),
  ).toBeFocused();

  await expect(
    page.getByRole("heading", { name: "Normalized fields" }),
  ).toBeInViewport();

  await page.goto(`/history/${id}`);
  await expect(
    page.getByRole("heading", { name: "Execution · partial" }),
  ).toBeVisible();

  await page
    .getByRole("button", { name: "Close execution", exact: true })
    .click();

  await expect(page).toHaveURL(/\/history$/);

  await expect(
    page.getByRole("heading", { name: "Execution · partial" }),
  ).toHaveCount(0);

  await expect(
    page.getByRole("button", { name: /EVT-101 · partial/ }),
  ).toBeVisible();
});

test("a missing selected execution does not turn successful empty history into a list failure", async ({
  page,
}) => {
  await seed(page);
  await page.route(`**/api/agents/runs/${id}`, (route) =>
    route.fulfill({ status: 404, json: { detail: "Execution not found" } }),
  );

  await page.route("**/api/agents/runs", (route) =>
    route.fulfill({ json: [] }),
  );
  await page.goto(`/verification/${id}`);

  await expect(page.getByRole("alert")).toContainText("Execution not found");
  await expect(
    page.getByText("No executions saved yet.", { exact: false }),
  ).toBeVisible();

  await expect(
    page.getByText("Saved executions are unavailable.", { exact: false }),
  ).toHaveCount(0);
});

test("rounded dropdown menus support keyboard selection and real run configuration", async ({
  page,
}) => {
  await seed(page);

  let config;

  await page.route("**/api/agents/runs", (route) => {
    if (route.request().method() === "POST") {
      config = route.request().postDataJSON();
      return route.fulfill({
        status: 202,
        json: { ...fixtureRun, event_id: config.event_id },
      });
    }
    return route.fulfill({ json: [fixtureRun] });
  });

  await page.goto("/agents");

  const event = page.getByRole("combobox", { name: "Reference event" });

  await event.click();

  const menu = page.getByRole("listbox");

  await expect(menu).toBeVisible();

  await expect(menu).toHaveCSS("border-radius", "20px");

  await expect(menu).toHaveCSS("border-top-width", "0px");

  await event.press("ArrowDown");

  await event.press("Enter");

  await expect(event).toHaveText("EVT-102");

  await expect(menu).toHaveCount(0);

  await event.click();

  await event.press("Escape");

  await expect(event).toBeFocused();

  await expect(menu).toHaveCount(0);

  await page.getByRole("button", { name: "Run verification" }).click();

  await expect(page).toHaveURL(new RegExp(id));

  expect(config).toEqual({ event_id: "EVT-102", max_records: 20 });

  await page.goto(`/verification/${id}`);

  await page.getByRole("combobox", { name: "Show" }).click();

  await page.getByRole("option", { name: "Verified", exact: true }).click();

  await expect(
    page.getByRole("button", { name: "Inspect record" }),
  ).toHaveCount(0);

  await page.getByRole("combobox", { name: "Show" }).click();

  await page.getByRole("option", { name: "All records", exact: true }).click();

  await expect(
    page.getByRole("button", { name: "Inspect record" }),
  ).toBeVisible();

  await page.setViewportSize({ width: 390, height: 844 });

  await page.getByRole("combobox", { name: "Show" }).click();

  const bounds = await menu.boundingBox();

  expect(bounds.x).toBeGreaterThanOrEqual(0);

  expect(bounds.x + bounds.width).toBeLessThanOrEqual(390);

  await page.screenshot({ path: "/tmp/eventops-rounded-picker-mobile.png" });
});

test("saved executions stay bounded and older runs remain reachable on desktop and mobile", async ({
  page,
}) => {
  await seed(page);

  const runs = Array.from({ length: 20 }, (_, index) => ({
    ...fixtureRun,
    id: `22222222-2222-4222-8222-${String(index).padStart(12, "0")}`,
  }));

  await page.route("**/api/agents/runs", (route) =>
    route.fulfill({ json: runs }),
  );

  await page.route(`**/api/agents/runs/${runs.at(-1).id}`, (route) =>
    route.fulfill({ json: runs.at(-1) }),
  );

  for (const width of [1280, 390]) {
    await page.setViewportSize({ width, height: 844 });
    await page.goto("/history");

    const list = page.getByRole("region", { name: "Saved execution list" });

    await expect(list.getByRole("button")).toHaveCount(20);

    const size = await list.evaluate((element) => ({
      client: element.clientHeight,
      full: element.scrollHeight,
    }));

    expect(size.client).toBeLessThanOrEqual(330);

    expect(size.full).toBeGreaterThan(size.client);

    await expect(
      page.getByText("20 saved · Scroll for older executions"),
    ).toBeVisible();

    await list.focus();

    await list.press("End");

    await list.getByRole("button").last().click();

    await expect(page).toHaveURL(new RegExp(runs.at(-1).id));

    await expect(
      page.getByRole("heading", { name: "Execution · partial" }),
    ).toBeVisible();

    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
});
