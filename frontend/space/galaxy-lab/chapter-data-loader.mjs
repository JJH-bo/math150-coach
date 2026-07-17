export function resolveChapterRequest(search = '') {
  const params = new URLSearchParams(search);
  const draftId = params.get('draft');
  if (draftId) {
    const parsedRevision = Number.parseInt(params.get('revision') || '', 10);
    return {
      kind: 'draft',
      draftId,
      revision: Number.isInteger(parsedRevision) && parsedRevision > 0
        ? parsedRevision
        : null,
    };
  }
  return {
    kind: 'published',
    chapterId: params.get('chapter') || 'infinite_series',
  };
}


export async function loadChapterData({
  search = '',
  fetchImpl = globalThis.fetch,
  fallbackChapter = null,
} = {}) {
  const request = resolveChapterRequest(search);
  const url = request.kind === 'draft'
    ? `/api/chapter-review/${encodeURIComponent(request.draftId)}/galaxy${
      request.revision ? `?revision=${request.revision}` : ''
    }`
    : `/api/challenge/v1/chapters/${encodeURIComponent(request.chapterId)}/galaxy`;
  const response = await fetchImpl(url, { credentials: 'same-origin' });
  if (response.ok) return response.json();
  if (
    request.kind === 'published'
    && request.chapterId === 'infinite_series'
    && fallbackChapter
  ) {
    return fallbackChapter;
  }
  throw new Error(`chapter_load_failed:${response.status}`);
}
