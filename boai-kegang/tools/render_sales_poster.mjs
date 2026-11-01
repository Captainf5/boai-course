import { createRequire } from "node:module";
import path from "node:path";
import { pathToFileURL } from "node:url";

const [inputArg, outputArg] = process.argv.slice(2);
const require = createRequire(import.meta.url);
const modulesRoot = process.env.CODEX_NODE_MODULES;
const scale = Number(process.env.POSTER_SCALE || 2);
const playwrightPackage = modulesRoot
  ? path.join(modulesRoot, "playwright")
  : "playwright";
const { chromium } = require(playwrightPackage);

if (!inputArg || !outputArg) {
  console.error("Usage: node render_sales_poster.mjs <input.html> <output.png>");
  process.exit(2);
}

const input = path.resolve(inputArg);
const output = path.resolve(outputArg);
const browser = await chromium.launch({
  headless: true,
  executablePath: process.env.CODEX_BROWSER_EXECUTABLE || undefined,
});

try {
  const page = await browser.newPage({
    viewport: { width: 1920, height: 1080 },
    deviceScaleFactor: scale,
  });
  await page.goto(pathToFileURL(input).href, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  const qa = await page.evaluate(() => {
    const tolerance = 1;
    const overflows = [];
    const checkBounds = (root, children) => {
      const outer = root.getBoundingClientRect();
      for (const child of children) {
        const inner = child.getBoundingClientRect();
        if (
          inner.left < outer.left - tolerance ||
          inner.top < outer.top - tolerance ||
          inner.right > outer.right + tolerance ||
          inner.bottom > outer.bottom + tolerance
        ) {
          overflows.push({
            root: root.className || root.tagName,
            child: child.className || child.tagName,
            outer: [outer.left, outer.top, outer.right, outer.bottom],
            inner: [inner.left, inner.top, inner.right, inner.bottom],
          });
        }
      }
    };
    const header = document.querySelector(".header");
    checkBounds(header, header.querySelectorAll(".eyebrow, h1, .subtitle, .proof, .quote-chip, .value-grid"));
    for (const card of document.querySelectorAll(".card")) {
      checkBounds(card, card.querySelectorAll(".card-head, .course-name, .version, .problem, .software"));
      const problem = card.querySelector(".problem")?.getBoundingClientRect();
      const software = card.querySelector(".software")?.getBoundingClientRect();
      if (problem && software && problem.bottom > software.top - 3) {
        overflows.push({
          root: "card",
          child: "problem-software-overlap",
          outer: [problem.top, problem.bottom],
          inner: [software.top, software.bottom],
        });
      }
    }
    const footer = document.querySelector(".footer");
    checkBounds(footer, footer.querySelectorAll(".quote-title, .quote-copy, .cta"));
    return {
      cards: document.querySelectorAll(".card").length,
      overflows,
      canvas: [document.documentElement.scrollWidth, document.documentElement.scrollHeight],
    };
  });
  if (qa.cards !== 9 || qa.overflows.length > 0 || qa.canvas[0] !== 1920 || qa.canvas[1] !== 1080) {
    throw new Error(`Poster layout QA failed: ${JSON.stringify(qa)}`);
  }
  await page.screenshot({ path: output, fullPage: false });
  console.log(JSON.stringify({
    input,
    output,
    width: 1920 * scale,
    height: 1080 * scale,
    qa,
  }));
} finally {
  await browser.close();
}
