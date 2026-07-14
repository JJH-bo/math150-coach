import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const moduleUrl = new URL("./stellar-renderer.js", import.meta.url);

async function loadRenderer() {
  let source = null;
  try {
    source = await readFile(moduleUrl, "utf8");
  } catch {
    // The first TDD run intentionally reaches the assertion before the module exists.
  }
  assert.equal(typeof source, "string", "stellar-renderer.js must exist");
  const renderer = await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
  return { renderer, source };
}

test("only the separable concept node enters the material proof", async () => {
  const { renderer } = await loadRenderer();
  assert.equal(renderer.isStellarMaterialPilotNode({ id: "ode_separable.concept", role: "training" }), true);
  assert.equal(renderer.isStellarMaterialPilotNode({ id: "ode_separable.method", role: "training" }), false);
  assert.equal(renderer.isStellarMaterialPilotNode({ id: "ode_separable.macro_challenge", role: "boss" }), false);
});

test("stellar profiles are deterministic and balanced mode reduces cost without changing identity", async () => {
  const { renderer } = await loadRenderer();
  const definition = { id: "ode_separable.concept", radius: 14, difficulty: 0.24 };
  const highA = renderer.stellarProfileFor(definition, "high");
  const highB = renderer.stellarProfileFor(definition, "high");
  const balanced = renderer.stellarProfileFor(definition, "balanced");

  assert.deepEqual(highA, highB);
  assert.equal(highA.radius, 23.8);
  assert.ok(highA.activity >= 0.55 && highA.activity <= 0.9);
  assert.equal(highA.noiseOctaves, 5);
  assert.equal(highA.surfaceDetail, 5);
  assert.equal(highA.coronaLayers, 3);
  assert.equal(highA.prominenceCount, 4);
  assert.equal(balanced.noiseOctaves, 3);
  assert.equal(balanced.surfaceDetail, 4);
  assert.equal(balanced.coronaLayers, 2);
  assert.equal(balanced.prominenceCount, 2);
  assert.equal(balanced.coreColor, highA.coreColor);
  assert.equal(balanced.midColor, highA.midColor);
  assert.equal(balanced.edgeColor, highA.edgeColor);
});

test("stellar renderer forbids conventional glossy or bitmap star materials", async () => {
  const { source } = await loadRenderer();
  assert.match(source, /ShaderMaterial/);
  assert.doesNotMatch(source, /MeshStandardMaterial|MeshPhysicalMaterial|MeshPhongMaterial|MeshLambertMaterial/);
  assert.doesNotMatch(source, /TextureLoader|CanvasTexture/);
});

test("living star contains independent photosphere, chromosphere, corona, prominences, and local light", async () => {
  const { source } = await loadRenderer();
  assert.match(source, /createKnowledgeStar/);
  assert.match(source, /createPhotosphere/);
  assert.match(source, /createChromosphere/);
  assert.match(source, /createCoronaLayers/);
  assert.match(source, /createRadiativeHalo/);
  assert.match(source, /createProminences/);
  assert.match(source, /PointLight/);
  assert.match(source, /limb/);
  assert.match(source, /granulation/);
  assert.match(source, /convection/);
  assert.match(source, /radialGlow/);
  assert.match(source, /userData\.stellar = true/);
});

test("visual safeguards preserve surface contrast and prevent concentric-shell corona", async () => {
  const { renderer, source } = await loadRenderer();
  const profile = renderer.stellarProfileFor(
    { id: "ode_separable.concept", radius: 14, difficulty: 0.24 },
    "high",
  );

  assert.ok(profile.surfaceExposure >= 0.8 && profile.surfaceExposure <= 0.92);
  assert.ok(profile.limbDarkening >= 0.45 && profile.limbDarkening <= 0.75);
  assert.ok(profile.coronaAsymmetry >= 0.65);
  assert.ok(profile.granulationScale >= 10);
  assert.match(source, /sectorMask/);
  assert.match(source, /limbDarkening/);
  assert.match(source, /surfaceExposure/);
});
