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
  assert.doesNotMatch(app.toLowerCase(), /api\/challenge|submitanswer|mastery|diagnosis|score|boss/);
});

test("visual system prioritizes reading, responsive model dock, and reduced motion", () => {
  assert.match(css, /\.classroom-grid/);
  assert.match(css, /position:\s*sticky/);
  assert.match(css, /@media\s*\(max-width:\s*860px\)/);
  assert.match(css, /prefers-reduced-motion/);
  assert.match(css, /\.model-dock\.is-fullscreen/);
});
