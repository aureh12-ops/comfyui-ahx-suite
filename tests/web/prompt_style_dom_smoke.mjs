// Browser smoke test of web/prompt_style.js against a STUB of ComfyUI's frontend: adding, changing, moving and
// removing rows, the cycle step after a run, the last run text, refreshed style files and key isolation.
// Not ComfyUI integration. Needs playwright (or playwright-core with an installed Chrome); skips if unavailable.
//
//   node tests/web/prompt_style_dom_smoke.mjs [screenshot.png]

import { createServer } from "node:http";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";
import assert from "node:assert/strict";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..", "..");
const require = createRequire(import.meta.url);
let chromium;
try {
  ({ chromium } = (() => { try { return require("playwright"); } catch { return require("playwright-core"); } })());
} catch {
  console.log("SKIP: playwright not available");
  process.exit(0);
}

const LIBRARY = {
  Lighting: [["Soft", "soft diffused light"], ["Neon", "neon {pink|blue} glow"]],
  Location: [["Forest", "in a forest"], ["Beach", "on a beach"], ["Desert", "in a desert"]],
};

const APP_STUB = `export const app = { exts: [], registerExtension(e) { this.exts.push(e); } };`;

const PAGE = `<!doctype html><html><head><style>
:root { --comfy-input-bg: #222; --input-text: #ddd; --border-color: #4e4e4e; --descrip-text: #999; }
body { margin: 0; background: #353535; }
#host { width: 432px; padding: 4px; background: #353535; }
</style></head><body><div id="host"></div>
<script type="module">
import { app } from "/scripts/app.js";
await import("/extensions/ahx/prompt_style.js");
const ext = app.exts.find((e) => e.name === "ahx.prompt_style");
const node = { type: "AHX_PromptStyle", size: [440, 200], widgets: [],
  addDOMWidget(name, type, element, options) {
    const w = { name, type, element, options, get value() { return options.getValue(); }, set value(v) { options.setValue(v); } };
    this.widgets.push(w);
    element.style.height = "auto";
    document.getElementById("host").append(element);
    return w;
  },
  setSize(size) { this.size = size; },
  computeSize() { return [this.size[0], this.widgets[0].options.getMinHeight()]; },
  setDirtyCanvas() {},
};
const made = ext.getCustomWidgets().AHX_STYLE_STACK(node, "styles", ["AHX_STYLE_STACK", { library: ${JSON.stringify(LIBRARY)} }]);
window.node = node;
window.widget = made.widget;
window.minWidth = made.minWidth;
window.leaked = [];
document.addEventListener("keydown", (e) => window.leaked.push(e.key));
window.ready = true;
</script></body></html>`;

const server = createServer((req, res) => {
  const url = req.url.split("?")[0];
  const send = (type, body) => { res.writeHead(200, { "Content-Type": type }); res.end(body); };
  if (url === "/") return send("text/html", PAGE);
  if (url === "/scripts/app.js") return send("text/javascript", APP_STUB);
  if (url.startsWith("/extensions/ahx/")) return send("text/javascript", readFileSync(join(ROOT, "web", url.slice(16))));
  res.writeHead(404);
  res.end();
});
await new Promise((resolve) => server.listen(0, resolve));

const browser = await chromium.launch({ headless: true, channel: process.env.PW_CHANNEL ?? "chrome" });
try {
  const page = await browser.newPage({ viewport: { width: 460, height: 700 }, deviceScaleFactor: 2 });
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  await page.goto(`http://localhost:${server.address().port}/`);
  await page.waitForFunction(() => window.ready);

  const value = () => page.evaluate(() => window.widget.value);
  const rows = page.locator(".ahx-stack-row");
  const hints = () => page.locator(".ahx-stack-hint").allTextContents();

  // A new node holds only your prompt, has no input socket and is wide enough for its lists.
  assert.deepEqual(await value(), [{ type: "(prompt)" }]);
  assert.equal(await page.evaluate(() => window.widget.options.socketless), true);
  assert.equal(await page.evaluate(() => window.minWidth), 360);
  assert.equal(await page.locator(".ahx-stack-row button[title=Remove]").count(), 0);

  // + adds a row of the first type not in the stack yet, and grows the node.
  const height = await page.evaluate(() => window.node.size[1]);
  await page.getByText("+ Add style").click();
  await page.getByText("+ Add style").click();
  assert.deepEqual(await value(), [
    { type: "(prompt)" }, { type: "Lighting", style: "Soft" }, { type: "Location", style: "Forest" }]);
  assert.ok((await page.evaluate(() => window.node.size[1])) > height);
  assert.deepEqual(await hints(), ["soft diffused light", "in a forest"]);

  // The style list: random, cycle, then the type's styles. Picking one shows its text at once.
  const styleList = rows.nth(1).locator("select").nth(1);
  assert.deepEqual(await styleList.locator("option").allTextContents(), ["(random)", "(cycle)", "Soft", "Neon"]);
  await styleList.selectOption("Neon");
  assert.deepEqual((await hints())[0], "neon {pink|blue} glow");

  // A cycle row shows the style of the next run and steps once the run is queued.
  await rows.nth(2).locator("select").nth(1).selectOption("(cycle)");
  assert.equal((await hints())[1], "Next run: 1/3 Forest: in a forest");
  await page.evaluate(() => window.widget.afterQueued());
  assert.equal((await hints())[1], "Next run: 2/3 Beach: on a beach");
  assert.deepEqual((await value())[2], { type: "Location", style: "(cycle)", index: 1 });

  // Another type keeps (cycle) but starts it over.
  await rows.nth(2).locator("select").first().selectOption("Lighting");
  assert.deepEqual((await value())[2], { type: "Lighting", style: "(cycle)" });

  // Arrows move rows, the top one can't go up, and the prompt row moves like the others.
  assert.equal(await rows.nth(0).locator("button[title='Move up']").isDisabled(), true);
  await rows.nth(0).locator("button[title='Move down']").click();
  assert.deepEqual((await value()).map((r) => r.type), ["Lighting", "(prompt)", "Lighting"]);
  await rows.nth(2).locator("button[title='Move up']").click();
  assert.deepEqual((await value()).map((r) => r.style ?? r.type), ["Neon", "(cycle)", "(prompt)"]);

  // × removes the row.
  await rows.nth(0).locator("button[title=Remove]").click();
  assert.deepEqual(await value(), [{ type: "Lighting", style: "(cycle)" }, { type: "(prompt)" }]);

  // A run shows its style text at the bottom.
  await page.evaluate(() => window.node.onExecuted({ text: ["soft diffused light\nin a desert"] }));
  assert.equal(await page.locator(".ahx-stack-last").textContent(), "soft diffused light\nin a desert");

  // Refreshed style files: new types are listed; a type that is gone stays on its row, marked in the hint.
  await page.evaluate(() => window.widget.value = [{ type: "Location", style: "Beach" }, { type: "(prompt)" }]);
  await page.evaluate(() => window.node.refreshComboInNode({ AHX_PromptStyle: { input: { required: {
    styles: ["AHX_STYLE_STACK", { library: { Era: [["1920s", "1920s photo"]], Lighting: [["Soft", "soft"]] } }],
  } } } }));
  assert.deepEqual(await rows.nth(0).locator("select").first().locator("option").allTextContents(), ["Location", "Era", "Lighting"]);
  assert.equal((await hints())[0], '"Location" is not in the style library.');
  assert.equal(await page.locator(".ahx-stack-missing").count(), 1);
  await rows.nth(0).locator("select").first().selectOption("Era");
  assert.equal(await page.locator(".ahx-stack-missing").count(), 0);
  await page.evaluate(() => window.widget.value = [{ type: "Location", style: "Beach" }, { type: "(prompt)" }]);

  // Keys typed in a list stay out of ComfyUI's shortcuts.
  await rows.nth(0).locator("select").first().press("Delete");
  assert.deepEqual(await page.evaluate(() => window.leaked), []);

  if (process.argv[2]) {
    await page.evaluate(() => {
      window.widget.value = [
        { type: "Lighting", style: "Neon" }, { type: "(prompt)" }, { type: "Era", style: "(random)" }, { type: "Lighting", style: "(cycle)" }];
      window.node.onExecuted({ text: ["neon pink glow\n1920s photo\nsoft"] });
    });
    await page.locator("#host").screenshot({ path: process.argv[2] });
  }
  assert.deepEqual(errors, []);
  console.log("OK: prompt style stack smoke test passed");
} finally {
  await browser.close();
  server.close();
}
