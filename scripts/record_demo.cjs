#!/usr/bin/env node
/**
 * CropSense AI — demo video recorder (1920×1080, headed Chromium).
 *
 * One browser context (= one .webm) per video segment, saved to artifacts/video/NN-<segment>.webm,
 * plus one 1920×1080 still per segment in artifacts/video/stills/.
 *
 * Nothing is mocked: every segment drives the real app against the real backend. A segment whose
 * step fails, or whose page shows hardcoded sample data (no API call), is marked in the summary.
 *
 * Usage:
 *   node scripts/record_demo.cjs [--url http://localhost:3000] [--api http://localhost:8000] [--only 04,06]
 */
const fs = require("fs");
const path = require("path");
const { chromium } = require(path.join(__dirname, "..", "solidjs", "node_modules", "playwright"));

const argv = process.argv.slice(2);
const flag = (name, fallback) => {
  const i = argv.indexOf(`--${name}`);
  return i >= 0 && argv[i + 1] ? argv[i + 1] : fallback;
};
const BASE = flag("url", "http://localhost:3000").replace(/\/$/, "");
const API = flag("api", "http://localhost:8000").replace(/\/$/, "") + "/api/v1";
const ONLY = (flag("only", "") || "").split(",").map((s) => s.trim()).filter(Boolean);

const ROOT = path.join(__dirname, "..");
const OUT = path.join(ROOT, "artifacts", "video");
const STILLS = path.join(OUT, "stills");
const TMP = path.join(OUT, ".tmp");
const LEAF = path.join(OUT, "leaf.jpg");
const SIZE = { width: 1920, height: 1080 };

const DEMO_EMAIL = "farmer@cropsense.ai";
const DEMO_TOKEN = `mock-token-${DEMO_EMAIL}`;
const FARM_NAME = "Udaipur Farm – Plot 1";
const HINDI_QUESTION = "Is rabi mein kaunsi fasal lagaun?";

const pause = (ms) => new Promise((r) => setTimeout(r, ms));

// ---------------------------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------------------------

/** A visible cursor dot, because Playwright's screencast does not draw the OS pointer. */
function cursorOverlay() {
  const install = () => {
    if (document.getElementById("__demo_cursor")) return;
    const d = document.createElement("div");
    d.id = "__demo_cursor";
    Object.assign(d.style, {
      position: "fixed", left: "-50px", top: "-50px", width: "22px", height: "22px",
      borderRadius: "50%", background: "rgba(255, 193, 7, 0.55)", border: "2px solid rgba(0,0,0,0.65)",
      pointerEvents: "none", zIndex: "2147483647", transform: "translate(-50%, -50%)",
      transition: "transform 80ms ease-out",
    });
    document.body.appendChild(d);
    document.addEventListener("mousemove", (e) => { d.style.left = e.clientX + "px"; d.style.top = e.clientY + "px"; }, true);
    document.addEventListener("mousedown", () => { d.style.transform = "translate(-50%, -50%) scale(0.7)"; }, true);
    document.addEventListener("mouseup", () => { d.style.transform = "translate(-50%, -50%)"; }, true);
  };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", install);
  else install();
}

/** Signed-in state the "Instant Demo Sign-In" button would create. */
function seedDemoSession({ token, email }) {
  if (localStorage.getItem("__demo_seeded")) return;
  localStorage.setItem("__demo_seeded", "1");
  localStorage.setItem("access_token", token);
  localStorage.setItem("username", email);
  localStorage.setItem("user_data", JSON.stringify({
    id: 1, name: email.split("@")[0].toUpperCase(), email, role: "farmer", roles: ["farmer"], enable: 1,
  }));
}

async function glide(page, locator) {
  await locator.scrollIntoViewIfNeeded();
  const box = await locator.boundingBox();
  if (!box) throw new Error(`element not visible: ${locator}`);
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2, { steps: 30 });
  await pause(450);
}

async function hoverClick(page, locator) {
  await glide(page, locator);
  await locator.click();
}

async function typeInto(page, locator, text, delay = 70) {
  await hoverClick(page, locator);
  await page.keyboard.press(process.platform === "darwin" ? "Meta+A" : "Control+A");
  await page.keyboard.press("Backspace");
  await locator.pressSequentially(text, { delay });
}

async function slowScroll(page, totalPx, stepPx = 90, stepMs = 110) {
  await page.mouse.move(SIZE.width / 2 + 150, SIZE.height / 2, { steps: 10 });
  const steps = Math.ceil(Math.abs(totalPx) / stepPx);
  for (let i = 0; i < steps; i++) {
    await page.mouse.wheel(0, Math.sign(totalPx) * stepPx);
    await pause(stepMs);
  }
}

async function still(page, file) {
  await page.evaluate(() => { const c = document.getElementById("__demo_cursor"); if (c) c.style.visibility = "hidden"; });
  await page.screenshot({ path: path.join(STILLS, file), fullPage: false });
  await page.evaluate(() => { const c = document.getElementById("__demo_cursor"); if (c) c.style.visibility = "visible"; });
}

const byLabel = (page, text) => page.locator(`xpath=//label[contains(normalize-space(.), "${text}")]/following-sibling::input`);

async function api(method, pathname, body) {
  const res = await fetch(API + pathname, {
    method,
    headers: { Authorization: `Bearer ${DEMO_TOKEN}`, "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  let data = null;
  try { data = await res.json(); } catch { /* empty body */ }
  return { status: res.status, data };
}

/** Remove the demo farm left by an earlier run so the farm list shows it exactly once. */
async function resetDemoFarm() {
  const res = await api("GET", "/farms");
  for (const farm of res.data?.farms || []) {
    if (farm.name === FARM_NAME) await api("DELETE", `/farms/${farm.id}`);
  }
}

// ---------------------------------------------------------------------------------------------
// Segments
// ---------------------------------------------------------------------------------------------
// Each returns { status: "ready" | "sample-data" | "fail", note }. A thrown error = fail.

const SEGMENTS = [
  {
    id: "02", name: "landing", auth: false,
    async run(page) {
      await page.goto(BASE + "/", { waitUntil: "networkidle" });
      await pause(1500);
      await still(page, "02-landing.png");
      await slowScroll(page, 2200);
      await pause(1200);
      await slowScroll(page, -2200, 140, 60);
      return { status: "ready", note: "" };
    },
  },
  {
    id: "03", name: "signin-language", auth: false,
    async run(page) {
      await page.goto(BASE + "/auth/signin", { waitUntil: "networkidle" });
      await pause(1500);
      await hoverClick(page, page.getByRole("button", { name: /Instant Demo Sign-In/ }));
      await page.waitForURL(/\/dashboard/, { timeout: 15000 });
      await page.waitForLoadState("networkidle");
      await pause(2000);

      const lang = page.locator("aside select").first();
      await glide(page, lang);
      await lang.selectOption("hi");
      await pause(2500);
      const hindi = await page.evaluate(() => /[ऀ-ॿ]/.test(document.body.innerText));
      await still(page, "03-signin-language.png");
      await pause(1000);
      await lang.selectOption("en");
      await pause(1500);
      if (!hindi) return { status: "fail", note: "switching to Hindi did not change any page text" };
      return {
        status: "ready",
        note: 'Button reads "Instant Demo Sign-In (Dev/E2E)"; narration says "sign in with Google". Crop or re-word.',
      };
    },
  },
  {
    id: "04", name: "register-farm", auth: true,
    async before() { await resetDemoFarm(); },
    async run(page, seg) {
      await page.goto(BASE + "/farm/register", { waitUntil: "networkidle" });
      await pause(1500);
      await typeInto(page, byLabel(page, "Farm / Plot Nickname"), FARM_NAME, 60);
      await pause(400);
      await typeInto(page, byLabel(page, "PIN / Postal Code"), "313001", 160);
      await page.getByText("✓ Udaipur, Rajasthan").waitFor({ timeout: 20000 });
      await glide(page, byLabel(page, "State & District"));
      await pause(1800);
      await still(page, "04-register-farm.png");
      await typeInto(page, byLabel(page, "Total Area (Acres)"), "2.5", 150);
      await typeInto(
        page,
        page.locator(`xpath=//label[contains(normalize-space(.), "Survey No.")]/following-sibling::div//input`),
        "Khasra No. 214",
        60
      );
      await pause(600);

      const submit = page.getByRole("button", { name: /Confirm & Register/ });
      const posted = page.waitForResponse((r) => r.url().endsWith("/api/v1/farms") && r.request().method() === "POST", { timeout: 30000 });
      await hoverClick(page, submit);
      const res = await posted;
      if (res.status() !== 201) {
        await pause(2500);
        return { status: "fail", note: `POST /farms returned ${res.status()}` };
      }
      await page.waitForURL(/\/farm$/, { timeout: 15000 });
      await page.getByText(FARM_NAME).first().waitFor({ timeout: 15000 });
      await glide(page, page.getByText(FARM_NAME).first());
      await pause(2500);
      return {
        status: "ready",
        note: "Soil Health Card / SLUSI nutrients are not shown on screen; narration mentions them.",
      };
    },
  },
  {
    id: "05", name: "crop-plan", auth: true,
    async run(page, seg) {
      await page.goto(BASE + "/strategy/select-farm", { waitUntil: "networkidle" });
      await pause(1500);
      const listsDemoFarm = await page.getByText(FARM_NAME).count();
      await hoverClick(page, page.getByRole("button", { name: /Select & Configure/ }).first());
      await page.waitForURL(/\/strategy\/request/, { timeout: 15000 });
      await pause(1500);
      await slowScroll(page, 600);
      await pause(800);
      await hoverClick(page, page.getByRole("button", { name: /Generate 365-Day Strategy/ }));
      await page.waitForURL(/\/crops\/annual-strategy\//, { timeout: 60000 });
      await page.waitForLoadState("networkidle");
      await pause(2500);
      await still(page, "05-crop-plan.png");
      await slowScroll(page, 700);
      await pause(1500);

      const called = seg.apiCalls.some((c) => c.includes("/annual-strategy"));
      if (!called) {
        return {
          status: "sample-data",
          note:
            "Generate never calls POST /annual-strategy (1.2 s timer, then a hardcoded page)." +
            (listsDemoFarm ? "" : ` The farm picker is hardcoded too; "${FARM_NAME}" is not listed.`),
        };
      }
      return { status: "ready", note: "" };
    },
  },
  {
    id: "06", name: "diagnose", auth: true,
    skip: () => (fs.existsSync(LEAF) ? null : "artifacts/video/leaf.jpg is missing (add a real diseased-leaf photo)"),
    async run(page) {
      await page.goto(BASE + "/diagnose", { waitUntil: "networkidle" });
      await pause(1500);
      await glide(page, page.locator("label:has(input[type=file])").first());
      await page.locator("input[type=file]").setInputFiles(LEAF);
      await pause(1500);
      const done = page.waitForResponse((r) => r.url().includes("/vision/diagnose-crop"), { timeout: 95000 });
      await hoverClick(page, page.getByRole("button", { name: /Pathology Scan/ }));
      const res = await done;
      await pause(1200);
      await still(page, "06-diagnose.png");
      await pause(2500);
      if (!res.ok()) {
        const msg = await page.locator("[role=alert]").first().innerText().catch(() => "");
        return { status: "fail", note: `POST /vision/diagnose-crop returned ${res.status()}. ${msg.slice(0, 160)}` };
      }
      return { status: "ready", note: "" };
    },
  },
  {
    id: "07", name: "voice", auth: true,
    async run(page) {
      await page.goto(BASE + "/assistant", { waitUntil: "networkidle" });
      await pause(1500);
      const input = page.locator("form input[type=text]");
      await typeInto(page, input, HINDI_QUESTION, 80);
      await pause(700);
      const done = page.waitForResponse((r) => r.url().includes("/voice/assist"), { timeout: 60000 });
      await hoverClick(page, page.locator("form button[type=submit]"));
      const res = await done;
      let body = null;
      try { body = await res.json(); } catch { /* not json */ }
      await page.waitForFunction(() => !document.body.innerText.includes("Agronomist is analyzing"), null, { timeout: 60000 });
      await pause(1500);
      await still(page, "07-voice.png");
      await pause(2500);
      if (!res.ok()) return { status: "fail", note: `POST /voice/assist returned ${res.status()}` };
      if (body?.data?.fallback || !body?.data?.reply) {
        return { status: "fail", note: "assistant returned fallback (no Gemini reply); needs Google credentials" };
      }
      return { status: "ready", note: "Typed, not spoken. Re-record by hand if the mic should be on screen." };
    },
  },
  {
    id: "08", name: "alerts-market", auth: true,
    async run(page, seg) {
      await page.goto(BASE + "/climate/hub", { waitUntil: "networkidle" });
      await pause(1500);
      await still(page, "08-alerts-market.png");
      await slowScroll(page, 900);
      await pause(1200);
      const climateCalls = seg.apiCalls.length;
      await page.goto(BASE + "/marketplace", { waitUntil: "networkidle" });
      await pause(1500);
      await slowScroll(page, 900);
      await pause(1500);
      const marketCalls = seg.apiCalls.length - climateCalls;
      if (!climateCalls || !marketCalls) {
        return {
          status: "sample-data",
          note: `No API calls on ${[!climateCalls && "/climate/hub", !marketCalls && "/marketplace"].filter(Boolean).join(" or ")}; content is hardcoded.`,
        };
      }
      return { status: "ready", note: "" };
    },
  },
];

// ---------------------------------------------------------------------------------------------
// Runner
// ---------------------------------------------------------------------------------------------

async function recordSegment(browser, seg) {
  const file = `${seg.id}-${seg.name}.webm`;
  const skipReason = seg.skip && seg.skip();
  if (skipReason) return { seg, file: "—", seconds: 0, status: "skipped", note: skipReason, errors: [] };
  if (seg.before) await seg.before();

  const context = await browser.newContext({
    viewport: SIZE,
    deviceScaleFactor: 1,
    recordVideo: { dir: TMP, size: SIZE },
  });
  await context.addInitScript(cursorOverlay);
  if (seg.auth) await context.addInitScript(seedDemoSession, { token: DEMO_TOKEN, email: DEMO_EMAIL });

  const page = await context.newPage();
  const state = { apiCalls: [], errors: [] };
  page.on("request", (r) => { if (r.url().includes("/api/v1/")) state.apiCalls.push(`${r.method()} ${new URL(r.url()).pathname}`); });
  page.on("response", (r) => {
    if (r.status() >= 400) state.errors.push(`${r.status()} ${r.request().method()} ${new URL(r.url()).pathname}`);
  });

  const started = Date.now();
  let outcome;
  try {
    outcome = await seg.run(page, state);
  } catch (err) {
    outcome = { status: "fail", note: String(err.message || err).split("\n")[0].slice(0, 200) };
    await still(page, `${seg.id}-${seg.name}-FAILED.png`).catch(() => {});
  }
  await pause(1500);
  const seconds = (Date.now() - started) / 1000;

  const video = page.video();
  await context.close();
  if (video) await video.saveAs(path.join(OUT, file));
  if (video) await video.delete().catch(() => {});

  return { seg, file, seconds, ...outcome, errors: [...new Set(state.errors)] };
}

(async () => {
  fs.mkdirSync(STILLS, { recursive: true });
  fs.mkdirSync(TMP, { recursive: true });

  console.log(`Recording CropSense demo  base=${BASE}  api=${API}`);
  const browser = await chromium.launch({
    headless: false,
    slowMo: 250,
    args: [`--window-size=${SIZE.width},${SIZE.height + 90}`],
  });

  const results = [];
  for (const seg of SEGMENTS) {
    if (ONLY.length && !ONLY.includes(seg.id)) continue;
    process.stdout.write(`  ${seg.id} ${seg.name} … `);
    const r = await recordSegment(browser, seg);
    console.log(r.status);
    results.push(r);
  }
  await browser.close();
  fs.rmSync(TMP, { recursive: true, force: true });

  const rows = results.map((r) => ({
    segment: `${r.seg.id} ${r.seg.name}`,
    file: r.file,
    duration: r.seconds ? `${r.seconds.toFixed(1)} s` : "—",
    result: r.status === "ready" ? "PASS" : r.status === "sample-data" ? "PASS (sample data)" : r.status.toUpperCase(),
    "4xx/5xx": r.errors.join(", ") || "none",
    note: r.note || "",
  }));
  console.log("\nSummary");
  console.table(rows);
  fs.writeFileSync(path.join(OUT, "summary.json"), JSON.stringify({ base: BASE, recordedAt: new Date().toISOString(), rows }, null, 2));
  process.exit(results.some((r) => r.status === "fail") ? 1 : 0);
})().catch((err) => {
  console.error(err);
  process.exit(2);
});
