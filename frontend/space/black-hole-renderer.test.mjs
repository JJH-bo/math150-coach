import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const moduleUrl = new URL("./black-hole-renderer.js", import.meta.url);

async function loadRenderer() {
  let source = null;
  try {
    source = await readFile(moduleUrl, "utf8");
  } catch {
    // The first TDD run intentionally reaches the assertion before the module exists.
  }
  assert.equal(typeof source, "string", "black-hole-renderer.js must exist");
  const renderer = await import(`data:text/javascript;base64,${Buffer.from(source).toString("base64")}`);
  return { renderer, source };
}

test("boss black hole is built from physical layers instead of portal internals", async () => {
  const { source } = await loadRenderer();

  assert.match(source, /createBossBlackHole/);
  assert.match(source, /createEventHorizon/);
  assert.match(source, /createPhotonRing/);
  assert.match(source, /createAccretionDisc/);
  assert.match(source, /createInfallField/);
  assert.match(source, /createGravitationalStorm/);
  assert.match(source, /updateBossBlackHole/);
  assert.doesNotMatch(source, /createPortalThroat|createPortalAperture/);
  assert.match(source, /color:\s*0x000000/);
  assert.match(source, /depthWrite:\s*true/);
  assert.match(source, /userData\.blackHole = true/);
});

test("black hole profile preserves horizon scale while balanced mode reduces cost", async () => {
  const { renderer } = await loadRenderer();
  const definition = { id: "ode_separable.macro_challenge", radius: 196 };
  const high = renderer.blackHoleProfileFor(definition, "high");
  const balanced = renderer.blackHoleProfileFor(definition, "balanced");

  assert.equal(high.horizonRadius, 196);
  assert.equal(balanced.horizonRadius, high.horizonRadius);
  assert.ok(high.photonRadius > high.horizonRadius);
  assert.ok(high.photonWidth <= 0.008);
  assert.ok(high.discOuterRadius >= high.horizonRadius * 1.8);
  assert.ok(high.stormOuterRadius >= high.discOuterRadius * 1.25);
  assert.ok(high.infallCount > balanced.infallCount);
  assert.ok(high.stormLayers > balanced.stormLayers);
  assert.ok(high.discTurbulenceOctaves > balanced.discTurbulenceOctaves);
});

test("event horizon remains opaque while emissive layers stay independently animated", async () => {
  const { source } = await loadRenderer();

  assert.match(source, /MeshBasicMaterial/);
  assert.match(source, /transparent:\s*false/);
  assert.match(source, /PHOTON_RING_FRAGMENT_SHADER/);
  assert.match(source, /ACCRETION_FRAGMENT_SHADER/);
  assert.match(source, /INFALL_VERTEX_SHADER/);
  assert.match(source, /GRAVITY_STORM_FRAGMENT_SHADER/);
  assert.match(source, /frontDisc/);
  assert.match(source, /backDisc/);
  assert.match(source, /valueNoise2D/);
  assert.match(source, /fbm/);
  assert.match(source, /float frontHalf = 1\.0 - split/);
  assert.match(source, /backDisc\.rotation\.x = 1\.08/);
  assert.match(source, /frontDisc\.rotation\.x = -1\.08/);
  assert.doesNotMatch(source, /hash21\(floor/);
});
