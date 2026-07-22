import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const html = await readFile(new URL("./index.html", import.meta.url), "utf8").catch(() => "");
const css = await readFile(new URL("./styles.css", import.meta.url), "utf8").catch(() => "");
const app = await readFile(new URL("./app.js", import.meta.url), "utf8").catch(() => "");

test("classroom shell has atlas, reading stage, and model observatory landmarks", () => {
  for (const id of [
    "atlasView", "chapterRegion", "moduleDestinations", "classroomStage",
    "lessonContent", "modelDock", "modelRoot", "backToAtlas", "fullscreenModel",
    "modelControls",
  ]) {
    assert.match(html, new RegExp(`id="${id}"`));
  }
});

test("application uses only Classroom Runtime and wires continuity interactions", () => {
  assert.match(app, /\/api\/classroom\/v1/);
  assert.match(app, /IntersectionObserver/);
  assert.match(app, /detail_branch_open/);
  assert.match(app, /classroom_scene_v1/);
  assert.match(app, /dispose/);
  assert.match(app, /mountModelControls/);
  assert.doesNotMatch(app.toLowerCase(), /api\/challenge|submitanswer|mastery|diagnosis|score|boss/);
});

test("package-specific learner entry selects the requested published classroom", () => {
  assert.match(app, /new URLSearchParams\(window\.location\.search\)/);
  assert.match(app, /\.get\("package_id"\)/);
  assert.match(app, /catalog\.packages\.find/);
});

test("visual system prioritizes reading, responsive model dock, and reduced motion", () => {
  assert.match(css, /\.classroom-grid/);
  assert.match(css, /position:\s*sticky/);
  assert.match(css, /@media\s*\(max-width:\s*860px\)/);
  assert.match(css, /prefers-reduced-motion/);
  assert.match(css, /\.model-dock\.is-fullscreen/);
  assert.match(app, /fullscreenScrollTop/);
  assert.match(app, /window\.scrollTo\(\{ top: restoreTop, behavior: "instant" \}\)/);
});

test("learning stage distinguishes stable baseline from GPT detailed expansion", () => {
  assert.match(app, /createSessionClient/);
  assert.match(app, /renderLearningSession/);
  assert.match(app, /watchLearningSession/);
  assert.match(app, /sessionClient\.focus[\s\S]+renderSessionContent\(\);[\s\S]+watchLearningSession\(\);/);
  assert.match(css, /\.baseline-step/);
  assert.match(css, /\.primary-learning-action/);
  assert.match(css, /\.live-expansion/);
  assert.match(css, /\.return-connection/);
  assert.match(css, /\.gpt-learning-handoff/);
  assert.match(css, /\.module-contract/);
  assert.match(css, /\.segment-mechanism/);
  assert.match(css, /\.detail-obstacle/);
  assert.match(css, /\.expansion-bridge/);
});

test("classroom uses a real mathematics engine with readable fallback", () => {
  assert.match(html, /\/classroom-vendor\/mathjax\/tex-mml-chtml-mathjax-tex\.js/);
  assert.doesNotMatch(html, /<script[^>]+https?:\/\//);
  assert.match(app, /typesetMath/);
  assert.match(css, /\.math-typeset/);
  assert.match(css, /\.math-render-fallback/);
});
