const params = new URLSearchParams(window.location.search);
const draftId = params.get('draft') || '';
const requestedRevision = Number.parseInt(params.get('revision') || '', 10);

const loginForm = document.querySelector('#review-login');
const reviewKey = document.querySelector('#review-key');
const loginResult = document.querySelector('#login-result');
const workspace = document.querySelector('#review-workspace');
const preview = document.querySelector('#galaxy-preview');
const title = document.querySelector('#draft-title');
const revisionText = document.querySelector('#draft-revision');
const metrics = document.querySelector('#draft-metrics');
const issues = document.querySelector('#draft-issues');
const rejectReason = document.querySelector('#reject-reason');
const approveButton = document.querySelector('#approve-draft');
const rejectButton = document.querySelector('#reject-draft');
const reviewResult = document.querySelector('#review-result');
const formalLink = document.querySelector('#formal-link');

let currentDraft = null;


async function request(url, options = {}) {
  const response = await fetch(url, {
    credentials: 'same-origin',
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {}),
    },
  });
  if (response.status === 204) return null;
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload.detail || payload.error || {};
    const error = new Error(detail.message || `请求失败：${response.status}`);
    error.code = detail.error_code || 'request_failed';
    error.payload = payload;
    throw error;
  }
  return payload;
}


function previewRevision() {
  if (Number.isInteger(requestedRevision) && requestedRevision > 0) {
    return requestedRevision;
  }
  return currentDraft?.revision || 1;
}


function renderDraft(payload) {
  currentDraft = payload;
  const selectedRevision = previewRevision();
  const stale = selectedRevision !== payload.revision;
  title.textContent = payload.title;
  revisionText.textContent =
    `草稿 ${payload.draft_id} · 预览版本 ${selectedRevision} · 当前版本 ${payload.revision}`;
  metrics.textContent =
    `${payload.metrics.systemCount || 0} 个核心星系 · `
    + `${payload.metrics.planetCount || 0} 颗训练星球 · `
    + `${payload.metrics.bossCount || 0} 个 Boss`;
  issues.replaceChildren();
  const reportIssues = Array.isArray(payload.issues) ? payload.issues : [];
  if (!reportIssues.length) {
    const item = document.createElement('li');
    item.className = 'pass';
    item.textContent = '结构与知识网校验通过';
    issues.append(item);
  } else {
    reportIssues.forEach((issue) => {
      const item = document.createElement('li');
      item.textContent = `${issue.code || issue.severity || 'issue'}：${issue.message || issue.target || ''}`;
      issues.append(item);
    });
  }
  preview.src =
    `/trainer/space/galaxy-lab/?draft=${encodeURIComponent(draftId)}`
    + `&revision=${selectedRevision}`;
  approveButton.disabled =
    stale
    || payload.status !== 'preview_ready'
    || payload.approval_ready !== true;
  if (stale) {
    reviewResult.textContent = '该链接不是最新版本，请让GPT返回新的预览链接。';
  } else if (payload.approval_ready !== true) {
    reviewResult.textContent =
      '画面可以预览，但内容尚未通过最终就绪检查。请先让GPT修复上方问题。';
  } else {
    reviewResult.textContent = '当前画面与待发布内容已绑定，可以直接批准。';
  }
}


async function loadWorkspace() {
  if (!draftId) {
    throw new Error('预览地址缺少 draft 参数。');
  }
  const payload = await request(
    `/api/chapter-review/${encodeURIComponent(draftId)}/metadata`,
  );
  loginForm.hidden = true;
  workspace.hidden = false;
  renderDraft(payload);
}


loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  loginResult.textContent = '正在建立审核会话…';
  try {
    await request('/api/chapter-review/session', {
      method: 'POST',
      body: JSON.stringify({ review_key: reviewKey.value }),
    });
    reviewKey.value = '';
    await loadWorkspace();
  } catch (error) {
    reviewKey.value = '';
    loginResult.textContent = error.message;
  }
});


approveButton.addEventListener('click', async () => {
  if (!currentDraft || approveButton.disabled) return;
  approveButton.disabled = true;
  rejectButton.disabled = true;
  reviewResult.textContent = '正在发布当前预览版本…';
  try {
    const payload = await request(
      `/api/chapter-review/${encodeURIComponent(draftId)}/approve`,
      {
        method: 'POST',
        body: JSON.stringify({
          revision: currentDraft.revision,
          content_hash: currentDraft.content_hash,
        }),
      },
    );
    reviewResult.textContent = '发布完成，正式章节与刚才预览完全一致。';
    formalLink.href = payload.formal_url;
    formalLink.hidden = false;
  } catch (error) {
    reviewResult.textContent = error.message;
    approveButton.disabled = currentDraft?.approval_ready !== true;
    rejectButton.disabled = false;
  }
});


rejectButton.addEventListener('click', async () => {
  if (!currentDraft) return;
  const reason = rejectReason.value.trim();
  if (!reason) {
    reviewResult.textContent = '退回前请填写需要修改的原因。';
    rejectReason.focus();
    return;
  }
  approveButton.disabled = true;
  rejectButton.disabled = true;
  try {
    await request(
      `/api/chapter-review/${encodeURIComponent(draftId)}/reject`,
      {
        method: 'POST',
        body: JSON.stringify({
          revision: currentDraft.revision,
          reason,
        }),
      },
    );
    reviewResult.textContent = '已退回GPT修改。';
  } catch (error) {
    reviewResult.textContent = error.message;
    approveButton.disabled = false;
    rejectButton.disabled = false;
  }
});


loadWorkspace().catch((error) => {
  if (error.code !== 'review_auth_required') {
    loginResult.textContent = error.message;
  }
});
