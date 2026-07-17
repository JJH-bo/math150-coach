import assert from 'node:assert/strict';
import test from 'node:test';

import {
  loadChapterData,
  resolveChapterRequest,
} from './chapter-data-loader.mjs';


test('resolves a formal chapter request', () => {
  assert.deepEqual(resolveChapterRequest('?chapter=power_series'), {
    kind: 'published',
    chapterId: 'power_series',
  });
});


test('resolves an immutable draft preview request', () => {
  assert.deepEqual(resolveChapterRequest('?draft=demo-abc&revision=2'), {
    kind: 'draft',
    draftId: 'demo-abc',
    revision: 2,
  });
});


test('loads the selected published chapter from the API', async () => {
  const calls = [];
  const chapter = await loadChapterData({
    search: '?chapter=power_series',
    fallbackChapter: null,
    fetchImpl: async (url, options) => {
      calls.push([url, options]);
      return {
        ok: true,
        json: async () => ({ chapterId: 'power_series' }),
      };
    },
  });

  assert.equal(chapter.chapterId, 'power_series');
  assert.deepEqual(calls, [[
    '/api/challenge/v1/chapters/power_series/galaxy',
    { credentials: 'same-origin' },
  ]]);
});


test('loads an authenticated draft preview revision', async () => {
  const calls = [];
  await loadChapterData({
    search: '?draft=demo-abc&revision=2',
    fetchImpl: async (url, options) => {
      calls.push([url, options]);
      return { ok: true, json: async () => ({ chapterId: 'demo' }) };
    },
  });

  assert.deepEqual(calls, [[
    '/api/chapter-review/demo-abc/galaxy?revision=2',
    { credentials: 'same-origin' },
  ]]);
});


test('uses the checked-in infinite-series fallback only for the legacy chapter', async () => {
  const fallback = { chapterId: 'infinite_series' };
  const chapter = await loadChapterData({
    search: '',
    fallbackChapter: fallback,
    fetchImpl: async () => ({ ok: false, status: 404 }),
  });

  assert.equal(chapter, fallback);
});
