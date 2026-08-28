const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const page = await ctx.newPage();

  // Navigate
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
  console.log('TITLE:', await page.title());

  // Login
  const emailInput = page.locator('input[type="email"], input[name="email"], input[placeholder*="mail"], input[placeholder*="usuario"]').first();
  const visible = await emailInput.isVisible({ timeout: 5000 }).catch(() => false);
  if (visible) {
    await emailInput.fill('prueba3');
    const passInput = page.locator('input[type="password"]').first();
    await passInput.fill('holamundo123');
    const submitBtn = page.locator('button[type="submit"]').first();
    await submitBtn.click();
    await page.waitForTimeout(3000);
    console.log('AFTER LOGIN URL:', page.url());
  } else {
    console.log('No login form found');
  }

  // Check for project cards
  const cards = await page.locator('button.project-card, .project-card, .ui-list-item').count();
  console.log('PROJECT CARDS FOUND:', cards);

  // Take screenshot
  await page.screenshot({ path: 'scripts/pw_projects.png', fullPage: true });
  console.log('Screenshot saved to scripts/pw_projects.png');

  // Check CSS classes applied
  const styles = await page.evaluate(() => {
    const els = document.querySelectorAll('button.project-card, .ui-list-item');
    return Array.from(els).map(el => ({
      classes: el.className,
      bg: getComputedStyle(el).background,
      border: getComputedStyle(el).border,
      borderLeft: getComputedStyle(el).borderLeft,
    }));
  });
  console.log('STYLES:', JSON.stringify(styles, null, 2));

  await browser.close();
})();
