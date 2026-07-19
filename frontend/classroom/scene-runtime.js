export function projectRevealedSteps(session) {
  const revealed = new Set(session?.revealed_step_ids || []);
  return (session?.baseline_steps || []).filter((step) => revealed.has(step.id));
}

export function expansionChildren(session, contentId) {
  return (session?.expansions || []).filter(
    (expansion) => expansion.parent_content_id === contentId,
  );
}

export function activeExpansion(session) {
  const stack = session?.expansion_stack || [];
  if (!stack.length) return null;
  const activeId = stack[stack.length - 1];
  return (session?.expansions || []).find((item) => item.id === activeId) || null;
}

export function sessionProgress(session) {
  const total = session?.baseline_steps?.length || 0;
  const revealed = projectRevealedSteps(session).length;
  return {
    total,
    revealed,
    hasNext: revealed < total,
  };
}
