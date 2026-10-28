import { expect, test } from "@playwright/test";

const email = process.env.E2E_EMAIL ?? "admin@example.com";
const password = process.env.E2E_PASSWORD ?? "change-me-please-123";
const shots = process.env.E2E_SCREENSHOTS;

/** Monday of a far-future week so the test never collides with real planning data. */
function testWeek() {
  const d = new Date(Date.UTC(2030, 0, 7 + Math.floor(Math.random() * 300) * 7));
  return d.toISOString().slice(0, 10);
}

test("login → weekly plan → review → approve (documented)", async ({ page }) => {
  await page.goto("/login");
  await page.getByLabel("E-Mail").fill(email);
  await page.getByLabel("Passwort").fill(password);
  await page.getByRole("button", { name: "Anmelden" }).click();
  await expect(page.getByRole("heading", { name: "Übersicht" })).toBeVisible();
  if (shots) await page.screenshot({ path: `${shots}/01-dashboard.png`, fullPage: true });

  const week = testWeek();
  await page.goto(`/calendar?week=${week}`);
  await page.getByRole("button", { name: "Plan für diese Woche erzeugen" }).click();
  await expect(page.getByText("Wochenplan wird generiert")).toBeVisible();

  // Worker generates the plan and drafts; the page auto-refreshes.
  await expect(page.locator("a[href^='/content/']").filter({ hasText: "Reel" })).toHaveCount(5, { timeout: 120_000 });
  await expect(page.locator("a[href^='/content/']").filter({ hasText: "Carousel" })).toHaveCount(2);
  await expect(page.getByText("Planned").or(page.getByText("Geplant (ohne Entwurf)"))).toHaveCount(0, { timeout: 120_000 });
  if (shots) await page.screenshot({ path: `${shots}/02-calendar.png`, fullPage: true });

  await page.locator("a[href^='/content/']").filter({ hasText: "Carousel" }).first().click();
  await expect(page.getByText("Inhalt · Version 1 (KI)")).toBeVisible();
  await page.getByRole("button", { name: "Slides rendern (1080×1350)" }).click();
  await expect(page.locator("img[src^='/api/media/']").first()).toBeVisible({ timeout: 60_000 });
  await page.getByRole("button", { name: "Zur Freigabe einreichen" }).click();
  await expect(page.getByText("Zur Freigabe eingereicht.")).toBeVisible();
  if (shots) await page.screenshot({ path: `${shots}/03-content.png`, fullPage: true });

  await page.getByPlaceholder("Kommentar").fill("E2E: geprüft");
  const ack = page.getByText("Ich habe den Inhalt fachlich/regulatorisch geprüft");
  if (await ack.isVisible()) await ack.click();
  await page.getByRole("button", { name: "Freigeben" }).click();
  await expect(page.getByText("Freigegeben und dokumentiert.")).toBeVisible();
  await expect(page.getByText("E2E: geprüft")).toBeVisible();
  if (shots) await page.screenshot({ path: `${shots}/04-approved.png`, fullPage: true });
});

test("public application form creates an attributed lead", async ({ page }) => {
  await page.goto("/apply/partner");
  await page.getByRole("textbox", { name: "Name", exact: true }).fill("E2E Partner");
  await page.getByRole("textbox", { name: "E-Mail", exact: true }).fill(`e2e-${Date.now()}@example.com`);
  await page.getByLabel("Größe der Community").selectOption("10kto50k");
  await page.getByLabel("Monatliches Handelsvolumen der Community (geschätzt)").selectOption("1mto10m");
  await page.getByLabel("Bestehende Börsen-Partnerschaft").selectOption("none");
  await page.getByRole("checkbox").last().check();
  await page.getByRole("button", { name: "Absenden" }).click();
  await expect(page.getByRole("heading", { name: "Danke für deine Anfrage." })).toBeVisible();
});
