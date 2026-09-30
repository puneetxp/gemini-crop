#!/usr/bin/env node
/**
 * CropSense AI — Playwright End-to-End Action Test Suite
 *
 * Supports Headed and Headless execution:
 *   node scripts/playwright_test_suite.cjs --headless
 *   node scripts/playwright_test_suite.cjs --head --slowmo 500
 *   node scripts/playwright_test_suite.cjs --url https://cropsense-frontend-243152035508.us-central1.run.app
 */

const fs = require('fs');
const path = require('path');
const { chromium } = require('../solidjs/node_modules/playwright');

// Parse CLI flags
const args = process.argv.slice(2);
const isHeaded = args.includes('--head') || args.includes('--headed');
const slowMoArg = args.find((a, i) => args[i - 1] === '--slowmo');
const slowMo = slowMoArg ? parseInt(slowMoArg, 10) : (isHeaded ? 300 : 0);
const urlIndex = args.indexOf('--url');
const targetUrl = (urlIndex !== -1 && args[urlIndex + 1])
  ? args[urlIndex + 1].replace(/\/+$/, '')
  : 'https://cropsense-frontend-243152035508.us-central1.run.app';

const screenshotsDir = path.resolve(__dirname, '../artifacts/screenshots');
if (!fs.existsSync(screenshotsDir)) {
  fs.mkdirSync(screenshotsDir, { recursive: true });
}

const executablePath = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const results = [];
const consoleErrors = [];
const networkErrors = [];

function logPass(name, duration) {
  console.log(`  \x1b[32m✓\x1b[0m [PASS] ${name} (${duration}ms)`);
  results.push({ name, status: 'PASS', duration });
}

function logFail(name, error, duration) {
  console.log(`  \x1b[31m✗\x1b[0m [FAIL] ${name} (${duration}ms): ${error.message || error}`);
  results.push({ name, status: 'FAIL', duration, error: error.message || String(error) });
}

async function runTestSuite() {
  console.log('\n======================================================');
  console.log('  CropSense AI — Playwright E2E Action Suite');
  console.log('======================================================');
  console.log(`  Target URL  : ${targetUrl}`);
  console.log(`  Mode        : ${isHeaded ? 'HEADED (Visible Window)' : 'HEADLESS'}`);
  console.log(`  SlowMo      : ${slowMo}ms`);
  console.log(`  Executable  : ${executablePath}`);
  console.log('------------------------------------------------------\n');

  let browser;
  try {
    browser = await chromium.launch({
      executablePath: fs.existsSync(executablePath) ? executablePath : undefined,
      headless: !isHeaded,
      slowMo,
      args: ['--no-sandbox', '--disable-dev-shm-usage', '--window-size=1440,900']
    });
  } catch (launchErr) {
    console.error('\x1b[31mFailed to launch browser:\x1b[0m', launchErr.message);
    process.exit(1);
  }

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    userAgent: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36 CropSenseE2E/1.0'
  });

  const page = await context.newPage();

  // Listen to console and network
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    if (type === 'error') {
      consoleErrors.push({ url: page.url(), text });
    }
  });

  page.on('response', resp => {
    const status = resp.status();
    const url = resp.url();
    if (status >= 400 && !url.includes('/favicon.ico')) {
      networkErrors.push({ status, url });
    }
  });

  // Action 1: Load Home Page & Title
  {
    const start = Date.now();
    try {
      await page.goto(`${targetUrl}/`, { waitUntil: 'networkidle', timeout: 30000 });
      const title = await page.title();
      if (!title.includes('CropSense')) {
        throw new Error(`Unexpected page title: "${title}"`);
      }
      await page.screenshot({ path: path.join(screenshotsDir, '01_home_page.png') });
      logPass('Action 1: Visit Home Page & Verify Shell', Date.now() - start);
    } catch (err) {
      logFail('Action 1: Visit Home Page & Verify Shell', err, Date.now() - start);
    }
  }

  // Action 2: Trigger Instant Demo Sign-In
  {
    const start = Date.now();
    try {
      await page.goto(`${targetUrl}/auth/signin`, { waitUntil: 'networkidle', timeout: 20000 });
      const demoBtn = page.locator('button:has-text("Instant Demo Sign-In"), button:has-text("Demo Auto-Login")').first();
      await demoBtn.waitFor({ state: 'visible', timeout: 10000 });
      await demoBtn.click();
      await page.waitForSelector('text=Krishi Command Center', { timeout: 15000 });
      await page.screenshot({ path: path.join(screenshotsDir, '02_dashboard_after_login.png') });
      logPass('Action 2: Execute Instant Demo Sign-In', Date.now() - start);
    } catch (err) {
      logFail('Action 2: Execute Instant Demo Sign-In', err, Date.now() - start);
    }
  }

  // Action 3: Verify Dashboard Krishi Command Center Telemetry
  {
    const start = Date.now();
    try {
      await page.waitForSelector('text=Krishi Command Center', { timeout: 10000 });
      const welcome = await page.textContent('body');
      if (!welcome.includes('FARMER')) {
        throw new Error('Authenticated user profile banner not detected');
      }
      logPass('Action 3: Krishi Command Center Telemetry & Profile', Date.now() - start);
    } catch (err) {
      logFail('Action 3: Krishi Command Center Telemetry & Profile', err, Date.now() - start);
    }
  }

  // Action 4: Navigate to AI Crop Pathology Doctor (/diagnose)
  {
    const start = Date.now();
    try {
      const docLink = page.locator('a[href="/diagnose"]').first();
      await docLink.click();
      await page.waitForSelector('text=AI Crop Pathology Doctor', { timeout: 10000 });
      await page.screenshot({ path: path.join(screenshotsDir, '03_ai_doctor.png') });
      logPass('Action 4: AI Crop Pathology Doctor Interface', Date.now() - start);
    } catch (err) {
      logFail('Action 4: AI Crop Pathology Doctor Interface', err, Date.now() - start);
    }
  }

  // Action 5: Navigate to Forward Marketplace & Contract Bookings
  {
    const start = Date.now();
    try {
      const mktLink = page.locator('a[href="/marketplace"]').first();
      await mktLink.click();
      await page.waitForSelector('text=Mandi Forward Marketplace', { timeout: 10000 });

      // Click contract detail link
      const viewContract = page.locator('a[href*="/marketplace/bookings/"]').first();
      await viewContract.waitFor({ state: 'visible', timeout: 8000 });
      await viewContract.click();
      await page.waitForSelector('text=Escrow', { timeout: 10000 });
      await page.screenshot({ path: path.join(screenshotsDir, '04_marketplace_booking.png') });
      logPass('Action 5: Forward Marketplace & Escrow Contract', Date.now() - start);
    } catch (err) {
      logFail('Action 5: Forward Marketplace & Escrow Contract', err, Date.now() - start);
    }
  }

  // Action 6: Navigate to Soil & Satellite Hub (/soil/hub)
  {
    const start = Date.now();
    try {
      const soilLink = page.locator('aside a[href="/soil/hub"]').first();
      await soilLink.click();
      await page.waitForSelector('text=Soil Health & Satellite GIS Hub', { timeout: 10000 });
      await page.screenshot({ path: path.join(screenshotsDir, '05_soil_satellite.png') });
      logPass('Action 6: Soil & Satellite Telemetry Hub', Date.now() - start);
    } catch (err) {
      logFail('Action 6: Soil & Satellite Telemetry Hub', err, Date.now() - start);
    }
  }

  // Action 7: Navigate to Livestock & Pashu Hub (/livestock)
  {
    const start = Date.now();
    try {
      const pashuLink = page.locator('aside a[href="/livestock"]').first();
      await pashuLink.click();
      await page.waitForSelector('text=Pashu Hub (Livestock)', { timeout: 10000 });
      await page.screenshot({ path: path.join(screenshotsDir, '06_livestock_hub.png') });
      logPass('Action 7: Pashu Livestock Health Hub', Date.now() - start);
    } catch (err) {
      logFail('Action 7: Pashu Livestock Health Hub', err, Date.now() - start);
    }
  }

  // Action 8: AI Krishi Assistant
  {
    const start = Date.now();
    try {
      const assistLink = page.locator('aside a[href="/assistant"]').first();
      await assistLink.click();
      await page.waitForSelector('text=CropSense AI Voice & Text Agronomist', { timeout: 10000 });
      
      const input = page.locator('input[placeholder*="Ask"], input[type="text"]').first();
      await input.fill('What is the optimal fertilizer for wheat crop?');
      const sendBtn = page.locator('button:has-text("Ask Krishi AI"), button[type="submit"]').first();
      if (await sendBtn.isVisible()) {
        await sendBtn.click();
        await page.waitForTimeout(1000);
      }
      await page.screenshot({ path: path.join(screenshotsDir, '07_ai_assistant.png') });
      logPass('Action 8: AI Krishi Assistant Interaction', Date.now() - start);
    } catch (err) {
      logFail('Action 8: AI Krishi Assistant Interaction', err, Date.now() - start);
    }
  }

  // Action 9: Platform Analytics (/admin/analytics)
  {
    const start = Date.now();
    try {
      // Use client-side router navigation
      await page.evaluate(() => {
        window.history.pushState({}, '', '/admin/analytics');
        window.dispatchEvent(new PopStateEvent('popstate'));
      });
      await page.waitForSelector('text=Executive Platform Analytics', { timeout: 10000 });
      await page.screenshot({ path: path.join(screenshotsDir, '08_admin_analytics.png') });
      logPass('Action 9: Admin Platform Analytics', Date.now() - start);
    } catch (err) {
      logFail('Action 9: Admin Platform Analytics', err, Date.now() - start);
    }
  }

  // Action 10: Multi-language Switcher
  {
    const start = Date.now();
    try {
      await page.goto(`${targetUrl}/dashboard`, { waitUntil: 'networkidle', timeout: 15000 });
      const select = page.locator('select').first();
      if (await select.isVisible()) {
        await select.selectOption('hi'); // Hindi
        await page.waitForTimeout(500);
        await select.selectOption('mr'); // Marathi
        await page.waitForTimeout(500);
        await select.selectOption('en'); // Back to English
      }
      logPass('Action 10: Multilingual Localization Switching', Date.now() - start);
    } catch (err) {
      logFail('Action 10: Multilingual Localization Switching', err, Date.now() - start);
    }
  }

  await browser.close();

  console.log('\n------------------------------------------------------');
  console.log('Playwright E2E Execution Summary:');
  const passCount = results.filter(r => r.status === 'PASS').length;
  const failCount = results.filter(r => r.status === 'FAIL').length;
  console.log(`  Total Actions : ${results.length}`);
  console.log(`  Passed        : \x1b[32m${passCount}\x1b[0m`);
  console.log(`  Failed        : \x1b[31m${failCount}\x1b[0m`);
  console.log(`  Screenshots   : ${screenshotsDir}`);
  console.log('------------------------------------------------------');

  if (consoleErrors.length > 0) {
    console.log(`\n\x1b[33mConsole Errors Detected (${consoleErrors.length}):\x1b[0m`);
    consoleErrors.slice(0, 10).forEach(e => console.log(`  - [${e.url}] ${e.text}`));
  } else {
    console.log('\n\x1b[32mZero Critical Console Errors.\x1b[0m');
  }

  if (networkErrors.length > 0) {
    console.log(`\n\x1b[33mNetwork Status 4xx/5xx Detected (${networkErrors.length}):\x1b[0m`);
    networkErrors.slice(0, 10).forEach(e => console.log(`  - HTTP ${e.status}: ${e.url}`));
  } else {
    console.log('\x1b[32mZero Network 4xx/5xx Failures.\x1b[0m');
  }

  if (failCount > 0) {
    process.exit(1);
  }
}

runTestSuite().catch(err => {
  console.error('Fatal Test Suite Error:', err);
  process.exit(1);
});
