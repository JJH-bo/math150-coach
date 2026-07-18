export const SCENE_KEY = "math150-classroom-scene-v1";
const ALLOWED_KEYS = Object.freeze([
  "schema_version",
  "package_id",
  "release_version",
  "course_id",
  "chapter_id",
  "module_id",
  "content_id",
  "scroll_top",
  "open_detail_ids",
  "model_instance_id",
  "model_snapshot",
  "viewport_mode",
  "quality",
  "reduced_motion",
]);

export function sanitizeSceneSnapshot(value = {}) {
  const result = { schema_version: "classroom_scene_v1" };
  for (const key of ALLOWED_KEYS) {
    if (key === "schema_version" || value[key] === undefined) continue;
    result[key] = value[key];
  }
  return result;
}

export function createSceneStore(storage = globalThis.localStorage) {
  return {
    save(value) {
      const snapshot = sanitizeSceneSnapshot(value);
      storage.setItem(SCENE_KEY, JSON.stringify(snapshot));
      return snapshot;
    },
    load({ packageId, releaseVersion } = {}) {
      const raw = storage.getItem(SCENE_KEY);
      if (!raw) return null;
      try {
        const snapshot = sanitizeSceneSnapshot(JSON.parse(raw));
        if (
          (packageId && snapshot.package_id !== packageId)
          || (releaseVersion && snapshot.release_version !== releaseVersion)
        ) {
          storage.removeItem(SCENE_KEY);
          return null;
        }
        return snapshot;
      } catch {
        storage.removeItem(SCENE_KEY);
        return null;
      }
    },
    clear() {
      storage.removeItem(SCENE_KEY);
    },
  };
}
