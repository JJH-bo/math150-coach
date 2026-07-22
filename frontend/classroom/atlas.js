function hash(value) {
  let result = 2166136261;
  for (const character of value) {
    result ^= character.charCodeAt(0);
    result = Math.imul(result, 16777619);
  }
  return result >>> 0;
}

function destination(module, index, total) {
  const seed = hash(module.id);
  const angle = (Math.PI * 2 * index) / Math.max(total, 1) - Math.PI / 2;
  const radius = 30 + (seed % 13);
  return {
    id: module.id,
    kind: "core_module",
    title: module.title,
    summary: module.summary || "",
    x: 50 + Math.cos(angle) * radius,
    y: 52 + Math.sin(angle) * radius * 0.72,
    scale: 0.88 + ((seed >>> 8) % 22) / 100,
  };
}

export function projectAtlas(packageValue) {
  const courses = (packageValue.courses || []).map((course) => ({
    id: course.id,
    title: course.title,
    chapters: (course.chapters || []).map((chapter) => ({
      id: chapter.id,
      title: chapter.title,
      overview: chapter.overview ? {
        essentialQuestion: chapter.overview.essential_question,
        learningRouteSummary: chapter.overview.learning_route_summary,
        moduleOrder: chapter.overview.module_order || [],
      } : null,
      destinations: (chapter.modules || []).map((module, index, modules) =>
        destination(module, index, modules.length)
      ),
      routes: (chapter.relations || []).map((relation) => ({
        id: relation.id,
        kind: relation.kind,
        sourceId: relation.source_module_id,
        targetId: relation.target_module_id,
        label: relation.label || "",
      })),
    })),
  }));
  const decorations = Array.from({ length: 42 }, (_, index) => {
    const seed = hash(`${packageValue.package_id}:${index}`);
    return {
      id: `decoration-${index}`,
      interactive: false,
      x: seed % 100,
      y: (seed >>> 8) % 100,
      opacity: 0.12 + ((seed >>> 16) % 28) / 100,
    };
  });
  return {
    packageId: packageValue.package_id,
    title: packageValue.title,
    courses,
    decorations,
  };
}
