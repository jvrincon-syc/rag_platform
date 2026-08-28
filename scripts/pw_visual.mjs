import { chromium } from 'file:///C:/Users/jvrincon/AppData/Roaming/npm/node_modules/@playwright/cli/node_modules/playwright/index.mjs';

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
const page = await ctx.newPage();
page.setDefaultTimeout(10000);

await page.goto('http://localhost:5173', { waitUntil: 'domcontentloaded', timeout: 10000 });
await page.waitForTimeout(1000);
await page.locator('#operator-username').fill('prueba3');
await page.locator('#operator-password').fill('holamundo123');
await page.locator('.operator-auth-submit').click({ force: true });
await page.waitForTimeout(3000);

// Verify card styles
const cardData = await page.evaluate(() => {
  const cards = document.querySelectorAll('button.project-card');
  return Array.from(cards).map(b => {
    const cs = getComputedStyle(b);
    const badge = b.querySelector('.project-state');
    return {
      text: b.textContent.substring(0, 40).trim(),
      bg: cs.backgroundColor,
      border: cs.border,
      borderLeft: cs.borderLeft,
      boxShadow: cs.boxShadow,
      borderRadius: cs.borderRadius,
      badge: badge ? { text: badge.textContent, bg: getComputedStyle(badge).backgroundColor, color: getComputedStyle(badge).color } : null,
    };
  });
});
console.log('CARDS:', JSON.stringify(cardData, null, 2));

// Check panel background vs card background
const bgCheck = await page.evaluate(() => {
  const panel = document.querySelector('.panel');
  const card = document.querySelector('button.project-card');
  return {
    panelBg: panel ? getComputedStyle(panel).backgroundColor : 'no panel',
    cardBg: card ? getComputedStyle(card).backgroundColor : 'no card',
    different: panel && card ? getComputedStyle(panel).backgroundColor !== getComputedStyle(card).backgroundColor : false,
  };
});
console.log('BG CHECK:', JSON.stringify(bgCheck));

// Check config form fieldsets
const fieldsets = await page.evaluate(() => {
  const fs = document.querySelectorAll('.platform-fieldset');
  return Array.from(fs).map(f => {
    const cs = getComputedStyle(f);
    return { bg: cs.backgroundColor, border: cs.border, borderRadius: cs.borderRadius };
  });
});
console.log('FIELDSETS:', JSON.stringify(fieldsets));

// Check bindings section
const bindings = await page.evaluate(() => {
  const b = document.querySelector('.platform-bindings');
  if (!b) return null;
  const cs = getComputedStyle(b);
  return { bg: cs.backgroundColor, border: cs.border, borderRadius: cs.borderRadius };
});
console.log('BINDINGS:', JSON.stringify(bindings));

// Screenshot
await page.screenshot({ path: 'scripts/pw_redesign.png', fullPage: true });
console.log('Screenshot saved');

// Click first card, screenshot detail
if (await page.locator('button.project-card').count() > 0) {
  await page.locator('button.project-card').first().click();
  await page.waitForTimeout(2000);
  await page.screenshot({ path: 'scripts/pw_redesign_detail.png', fullPage: true });
  console.log('Detail screenshot saved');
}

await browser.close();
process.exit(0);
