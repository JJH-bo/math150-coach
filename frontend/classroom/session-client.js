export function createSessionClient({
  apiBase = "/api/classroom/v1",
  fetch = globalThis.fetch?.bind(globalThis),
  EventSource = globalThis.EventSource,
} = {}) {
  if (!fetch) throw new Error("Learning session client requires fetch.");

  async function request(path, options = {}) {
    const response = await fetch(`${apiBase}${path}`, {
      headers: { "Content-Type": "application/json", ...(options.headers || {}) },
      ...options,
    });
    if (!response.ok) {
      let detail;
      try {
        detail = await response.json();
      } catch {
        detail = null;
      }
      const error = new Error(
        detail?.detail?.message
          || detail?.detail
          || `学习会话请求失败：${response.status}`,
      );
      error.status = response.status;
      error.detail = detail;
      throw error;
    }
    return response.json();
  }

  return {
    async create({ packageId, moduleId }) {
      const payload = await request("/learning-sessions", {
        method: "POST",
        body: JSON.stringify({
          package_id: packageId,
          module_id: moduleId,
        }),
      });
      return {
        sessionId: payload.session.session_id,
        accessToken: payload.access_token,
        session: payload.session,
      };
    },

    async get(access) {
      const query = new URLSearchParams({ access_token: access.accessToken });
      return request(
        `/learning-sessions/${encodeURIComponent(access.sessionId)}?${query}`,
      );
    },

    async reveal(access, expectedRevision) {
      return request(
        `/learning-sessions/${encodeURIComponent(access.sessionId)}/reveal`,
        {
          method: "POST",
          body: JSON.stringify({
            access_token: access.accessToken,
            expected_revision: expectedRevision,
          }),
        },
      );
    },

    async focus(access, expectedRevision, contentId) {
      return request(
        `/learning-sessions/${encodeURIComponent(access.sessionId)}/interactions`,
        {
          method: "POST",
          body: JSON.stringify({
            access_token: access.accessToken,
            expected_revision: expectedRevision,
            active_content_id: contentId,
          }),
        },
      );
    },

    async returnToParent(access, expectedRevision, idempotencyKey) {
      return request(
        `/learning-sessions/${encodeURIComponent(access.sessionId)}/return`,
        {
          method: "POST",
          body: JSON.stringify({
            access_token: access.accessToken,
            expected_revision: expectedRevision,
            idempotency_key: idempotencyKey,
          }),
        },
      );
    },

    watch(access, afterRevision, onUpdate, onError = () => {}) {
      if (!EventSource) return { close() {} };
      const query = new URLSearchParams({
        access_token: access.accessToken,
        after_revision: String(afterRevision || 0),
      });
      const source = new EventSource(
        `${apiBase}/learning-sessions/${encodeURIComponent(access.sessionId)}/events?${query}`,
      );
      const receive = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.revision > afterRevision) onUpdate(payload);
        } catch (error) {
          onError(error);
        }
      };
      for (const kind of [
        "session.created",
        "baseline.revealed",
        "scene.expanded",
        "scene.returned",
        "focus.changed",
      ]) {
        source.addEventListener(kind, receive);
      }
      source.onerror = onError;
      return source;
    },
  };
}
