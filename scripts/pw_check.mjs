import { chromium } from "C:/Users/jvrincon/AppData/Roaming/npm/node_modules/@playwright/cli/node_modules/playwright-core/index.mjs";

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await ctx.newPage();

// 1. Login
await page.goto("http://localhost:5173");
await page.waitForTimeout(1500);
console.log("TITLE:", await page.title());

// Check if login form exists
const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="mail"]').first();
if (await emailInput.isVisible({ timeout: 3000 }).catch(() => false)) {
  await emailInput.fill("prueba3");
  const passInput = page.locator('input[type="password"]').first();
  await passInput.fill("holamundo123");
  const submitBtn = page.locator('button[type="submit"]').first();
  await submitBtn.click();
  await page.waitForTimeout(3000);
  console.log("AFTER LOGIN TITLE:", await page.title());
} else {
  console.log("NO LOGIN FORM - already logged in or different flow");
}

// 2. Navigate to Projects
await page.goto("http://localhost:5173");
await page.waitForTimeout(2000);

// 3. Take snapshot
await page.screenshot({ path: "scripts/pw_projects.png", fullPage: true });
console.log("Screenshot saved to scripts/pw_projects.png");

// 4. Get the HTML of the projects panel
const html = await page.evaluate(() => {
  const panel = document.querySelector('[aria-label="Proyectos"]') || document.querySelector('.panel');
  return panel ? panel.outerHTML : document.body.innerHTML.substring(0, 5000);
});
console.log("PANEL HTML:\n", html);

// 5. Check what CSS classes are applied
const styles = await page.evaluate(() => {
  const cards = document.querySelectorAll('.project-card, .ui-list-item, .ui-list-card');
  return Array.from(cards).map(el => ({
    tag: el.tagName,
    classes: el.className,
    computed: {
      display: getComputedStyle(el).display,
      border: getComputedStyle(el).border,
      borderRadius: getComputedStyle(el).borderRadius,
      background: getComputedStyle(el).background,
    }
  }));
});
console.log("CARD STYLES:", JSON.stringify(styles, null, 2));

await browser.close();
