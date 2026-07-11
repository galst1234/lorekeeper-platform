import { chromium } from "playwright";
import { mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const OUT_DIR = path.resolve(__dirname, "../.github/pr-screenshots/pr-16");
const BASE_URL = process.env.SCREENSHOT_BASE_URL ?? "http://localhost:5173";
const SLUG = process.env.SCREENSHOT_CAMPAIGN_SLUG ?? "whisperwood-chronicles-demo0001";
const EMAIL = process.env.SCREENSHOT_EMAIL ?? "demo@lorekeeper.test";
const PASSWORD = process.env.SCREENSHOT_PASSWORD ?? "DemoPassword123!";

async function login(page) {
  await page.goto(`${BASE_URL}/login`, { waitUntil: "networkidle" });
  await page.locator('input[name="email"]').fill(EMAIL);
  await page.locator('input[name="password"]').fill(PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL((url) => !url.pathname.startsWith("/login"), { timeout: 15000 });
}

async function screenshot(page, name) {
  await page.screenshot({ path: path.join(OUT_DIR, name), fullPage: true });
}

async function main() {
  await mkdir(OUT_DIR, { recursive: true });

  const browser = await chromium.launch();
  const context = await browser.newContext({
    viewport: { width: 1280, height: 900 },
    colorScheme: "dark",
  });
  const page = await context.newPage();

  await login(page);

  await page.goto(`${BASE_URL}/campaigns/${SLUG}/locations`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  await screenshot(page, "locations-list.png");

  await page.goto(`${BASE_URL}/campaigns/${SLUG}/locations/new`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  await screenshot(page, "locations-create.png");

  await page.goto(`${BASE_URL}/campaigns/${SLUG}/locations/moonlit-tavern`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  await screenshot(page, "locations-detail.png");

  await page.goto(`${BASE_URL}/campaigns/${SLUG}/locations/moonlit-tavern/edit`, { waitUntil: "networkidle" });
  await page.waitForTimeout(1500);
  await screenshot(page, "locations-edit.png");

  await browser.close();
  console.log(`Screenshots saved to ${OUT_DIR}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
