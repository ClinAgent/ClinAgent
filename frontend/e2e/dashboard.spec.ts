import { test, expect } from "@playwright/test";

test("intake validates before sending and clears results when edited", async ({
  page,
}) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto("/");
  await expect(
    page.getByRole("heading", {
      name: "Cardiovascular assessment",
    }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Analyze case", exact: true }).click();
  await expect(page.locator("#age")).toBeFocused();
  await page.getByRole("button", { name: "Load example" }).click();
  await expect(page.locator("#age")).toHaveValue("63");
  await page.locator("#age").fill("200");
  await page.getByRole("button", { name: "Analyze case", exact: true }).click();
  expect(
    await page
      .locator("#age")
      .evaluate((el: HTMLInputElement) => el.validity.rangeOverflow),
  ).toBeTruthy();
  await page.locator("#age").fill("63");
  await page.getByRole("button", { name: "Analyze case", exact: true }).click();
  await expect(page.locator("blockquote")).toHaveCount(2, { timeout: 25000 });
  await expect(
    page.getByRole("img", { name: /Model probability/ }),
  ).toBeVisible();
  await page.screenshot({
    path: "../artifacts/dashboard-desktop.png",
    fullPage: true,
  });
  await page.setViewportSize({ width: 390, height: 844 });
  await page.screenshot({
    path: "../artifacts/dashboard-mobile.png",
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
  await page.locator("#age").fill("64");
  await expect(page.locator("blockquote")).toHaveCount(0);
  expect(errors).toEqual([]);
});

test("network failures do not leave stale or fabricated results", async ({
  page,
}) => {
  await page.route("**/analyze", (route) => route.abort());
  await page.goto("/");
  await page.getByRole("button", { name: "Load example" }).click();
  await page.getByRole("button", { name: "Analyze case", exact: true }).click();
  await expect(page.getByRole("alert")).toBeVisible();
  await expect(page.locator("blockquote")).toHaveCount(0);
  await expect(
    page.getByRole("button", { name: "Analyze case", exact: true }),
  ).toBeEnabled();
});

test("renders a complete synthesis response from a test-only provider fixture", async ({
  page,
  request,
}) => {
  const response = await request.post("http://127.0.0.1:8000/analyze", {
    data: {
      age: 63,
      sex: 1,
      cp: 4,
      trestbps: 145,
      chol: 233,
      fbs: 1,
      restecg: 2,
      thalach: 150,
      exang: 1,
      oldpeak: 2.3,
      slope: 2,
      ca: 0,
      thal: 7,
    },
  });
  expect(response.ok()).toBeTruthy();
  const result = await response.json();
  const summary =
    "This is a test-only research summary. Contributors are associations. Review evidence with a clinician [E1].";
  await page.route("**/analyze", (route) =>
    route.fulfill({
      json: {
        ...result,
        status: "complete",
        synthesis: {
          ...result.synthesis,
          status: "complete",
          reason: null,
          text: summary,
        },
      },
    }),
  );
  await page.goto("/");
  await page.getByRole("button", { name: "Load example" }).click();
  await page.getByRole("button", { name: "Analyze case", exact: true }).click();
  await expect(page.getByText(summary, { exact: true })).toBeVisible();
  await expect(page.getByText("Complete", { exact: true })).toBeVisible();
});

test("evidence renders Markdown and sanitizes source HTML", async ({
  page,
}) => {
  const source =
    '### Guideline excerpt\n\n| Class | Recommendation |\n| --- | --- |\n| I | **Review** the evidence. |\n\n- First point\n- Second point\n\nReference<sup>1</sup>\n<script>window.evidenceInjected = true</script>\n<a href="javascript:alert(1)">Unsafe link</a>';
  await page.route("**/analyze", async (route) => {
    const response = await route.fetch();
    const result = await response.json();
    result.evidence[0].text = source;
    await route.fulfill({ json: result });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Load example" }).click();
  await page.getByRole("button", { name: "Analyze case", exact: true }).click();
  const evidence = page.locator(".formatted-evidence").first();
  await expect(
    evidence.getByRole("heading", { name: "Guideline excerpt" }),
  ).toBeVisible();
  await expect(evidence.getByRole("table")).toBeVisible();
  await expect(evidence.locator("strong")).toHaveText("Review");
  await expect(evidence.locator("li")).toHaveCount(2);
  await expect(evidence.locator("sup")).toHaveText("1");
  await expect(evidence.locator("script")).toHaveCount(0);
  await expect(evidence.locator('a[href^="javascript:"]')).toHaveCount(0);
  expect(await page.evaluate(() => "evidenceInjected" in window)).toBeFalsy();
  await page
    .getByRole("button", { name: "View exact source text" })
    .first()
    .click();
  await expect(page.locator(".source-detail pre").first()).toHaveText(source);
});
