import { test, expect } from "@playwright/test";

for (const viewport of [
  { width: 1440, height: 900 },
  { width: 390, height: 844 },
]) {
  test(`landing and sign-in composition, assets and navigation at ${viewport.width}px`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);

    await page.emulateMedia({ reducedMotion: "no-preference" });

    await page.route("**/health", (r) => r.fulfill({ json: { status: "ok" } }));

    await page.goto("/");

    await expect(page.locator("#landing-title")).toHaveText(
      "EventOpsIntelligence",
    );
    const head = page.getByAltText("EventOps mascot", { exact: true });
    await expect(head).toBeVisible();
    expect(
      await head.evaluate((img) => img.complete && img.naturalWidth > 0),
    ).toBe(true);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: `/tmp/eventops-landing-${viewport.width}.png`,
      animations: "disabled",
    });
    await page.getByRole("link", { name: "Start" }).click();
    await expect(page).toHaveURL(/\/signin$/);
    await expect(
      page.getByRole("heading", { name: "Welcome to EventOps" }),
    ).toBeVisible();
    const full = page.getByAltText(
      "EventOps mascot welcoming you to the workspace",
    );
    await expect(full).toBeVisible();
    expect(
      await full.evaluate((img) => img.complete && img.naturalWidth > 0),
    ).toBe(true);
    const action = page.getByRole("button", { name: "Enter workspace" });
    await expect(action).toBeInViewport();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await page.screenshot({
      path: `/tmp/eventops-signin-${viewport.width}.png`,
      animations: "disabled",
    });
    await page.reload();
    await expect(action).toBeVisible();
    await page.getByRole("link", { name: "Back", exact: true }).click();
    await expect(page).toHaveURL(/\/$/);
    await page.goBack();
    await expect(page).toHaveURL(/\/signin$/);
  });
}

test("session failure is reported and entry can be retried", async ({
  page,
}) => {
  await page.route("**/health", (r) => r.fulfill({ json: { status: "ok" } }));
  await page.route("**/api/demo/session", (r) =>
    r.fulfill({
      status: 503,
      json: { detail: "Reviewer access is temporarily unavailable." },
    }),
  );
  await page.goto("/signin");
  await page.getByRole("button", { name: "Enter workspace" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "The backend could not complete this request.",
  );
  await expect(
    page.getByRole("button", { name: "Enter workspace" }),
  ).toBeEnabled();
  await expect(page).toHaveURL(/\/signin$/);
});

test("real reviewer API creates a session and opens the existing workspace", async ({
  page,
}) => {
  test.skip(
    process.env.RUN_LIVE_ENTRY !== "true",
    "Opt in to a real reviewer session; no provider calls.",
  );
  await page.goto("/");
  await page.getByRole("link", { name: "Start" }).click();
  const response = page.waitForResponse(
    (r) =>
      new URL(r.url()).pathname === "/api/demo/session" &&
      r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Enter workspace" }).click();
  expect((await response).ok()).toBe(true);
  await expect(page).toHaveURL(/\/workspace$/);
  await expect(
    page.getByRole("heading", { name: "What would you like to know?" }),
  ).toBeVisible();
  expect(
    await page.evaluate(() =>
      Boolean(sessionStorage.getItem("eventops-demo-token")),
    ),
  ).toBe(true);
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "What would you like to know?" }),
  ).toBeVisible();
  await page.goBack();
  await expect(
    page.getByRole("heading", { name: "Welcome to EventOps" }),
  ).toBeVisible();
});
