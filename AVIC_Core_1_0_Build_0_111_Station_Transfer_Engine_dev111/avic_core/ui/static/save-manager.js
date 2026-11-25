(() => {
  "use strict";
  const DB_NAME = "avic-engineering-drafts";
  const DB_VERSION = 1;
  const STORE = "drafts";
  const encode = value => JSON.stringify(value);
  let dbPromise;

  function openDb() {
    if (dbPromise) return dbPromise;
    dbPromise = new Promise((resolve, reject) => {
      if (!("indexedDB" in window)) return reject(new Error("IndexedDB недоступен"));
      const request = indexedDB.open(DB_NAME, DB_VERSION);
      request.onupgradeneeded = () => {
        const db = request.result;
        if (!db.objectStoreNames.contains(STORE)) db.createObjectStore(STORE, { keyPath: "key" });
      };
      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error || new Error("Не удалось открыть локальное хранилище черновиков"));
    });
    return dbPromise;
  }

  async function localGet(key) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const request = db.transaction(STORE, "readonly").objectStore(STORE).get(key);
      request.onsuccess = () => resolve(request.result || null);
      request.onerror = () => reject(request.error);
    });
  }

  async function localPut(value) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const request = db.transaction(STORE, "readwrite").objectStore(STORE).put(value);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async function localDelete(key) {
    const db = await openDb();
    return new Promise((resolve, reject) => {
      const request = db.transaction(STORE, "readwrite").objectStore(STORE).delete(key);
      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async function requestJson(url, options) {
    const response = await fetch(url, {
      headers: { "Content-Type": "application/json", ...(options && options.headers || {}) },
      ...options
    });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
      const error = new Error(body.detail || ("HTTP " + response.status));
      error.status = response.status;
      throw error;
    }
    return body;
  }

  function register(config) {
    if (window.__avicDraftManager && window.__avicDraftManager.dispose) window.__avicDraftManager.dispose();
    const editor = config.editor;
    const stationId = config.stationId;
    const resourceId = config.resourceId;
    if (!["fbd", "graphics", "web-page"].includes(editor) || !stationId || !resourceId) {
      return { schedule() {}, flush: async () => false, restore: async () => false, clear: async () => false };
    }
    const key = [editor, stationId, resourceId].join(":");
    const endpoint = "/api/engineering-drafts/" +
      [editor, stationId, resourceId].map(encodeURIComponent).join("/");
    let draftRevision = 0;
    let timer = null;
    let busy = false;
    let pending = false;
    let conflict = false;
    let recovered = false;
    const bar = document.createElement("div");
    bar.id = "avic-save-manager";
    bar.setAttribute("role", "status");
    bar.style.cssText = "position:fixed;z-index:99999;right:14px;bottom:14px;display:flex;align-items:center;gap:9px;max-width:min(720px,calc(100vw - 28px));padding:8px 11px;border:1px solid #cbd5dc;border-radius:8px;background:#fff;color:#263746;box-shadow:0 3px 18px #1b34401c;font:12px Segoe UI,Arial,sans-serif";
    const label = document.createElement("span");
    label.textContent = "Черновик готов";
    bar.append(label);
    document.body.append(bar);

    function state(value) {
      label.textContent = value;
      if (typeof config.onState === "function") config.onState(value);
    }

    function action(text, fn) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = text;
      button.style.cssText = "border:1px solid #cbd5dc;border-radius:5px;background:#f7f9fa;padding:5px 8px;cursor:pointer;color:#263746";
      button.addEventListener("click", fn);
      bar.append(button);
      return button;
    }

    async function loadRecovery() {
      let local = null, remote = null;
      try { local = await localGet(key); } catch (_) {}
      try {
        remote = await requestJson(endpoint);
        draftRevision = remote.draft_revision || 0;
      } catch (error) {
        if (error.status !== 404) state("Черновик: сервер временно недоступен");
      }
      const localTime = Date.parse(local?.updatedAt || "") || 0;
      const remoteTime = Date.parse(remote?.updated_at || "") || 0;
      const candidate = local && localTime > remoteTime ? local : (remote || local);
      if (!candidate || recovered) return;
      const content = candidate.content;
      if (!content || encode(content) === encode(config.getContent())) return;
      state("Найден черновик · " + new Date(candidate.updated_at || local?.updatedAt || Date.now()).toLocaleString());
      const restoreButton = action("Восстановить", async () => {
        try {
          await config.applyContent(content);
          recovered = true;
          state("Черновик восстановлен · ещё не опубликован");
          restoreButton.remove();
          discardButton.remove();
          schedule();
        } catch (error) { state("Ошибка восстановления: " + error.message); }
      });
      const discardButton = action("Отклонить", async () => {
        try {
          if (remote && remote.draft_revision) {
            await requestJson(endpoint + "?expected_draft_revision=" + remote.draft_revision, { method: "DELETE" });
          }
          await localDelete(key).catch(() => {});
          restoreButton.remove();
          discardButton.remove();
          state("Черновик отклонён");
        } catch (error) { state("Не удалось отклонить черновик: " + error.message); }
      });
    }

    async function persistLocal(snapshot) {
      const record = {
        key, editor, stationId, resourceId, content: snapshot,
        base_revision: Number(config.getBaseRevision() || 0),
        updatedAt: new Date().toISOString()
      };
      await localPut(record);
      return record;
    }

    async function flush() {
      if (timer) { clearTimeout(timer); timer = null; }
      if (busy) { pending = true; return false; }
      busy = true;
      try {
        const snapshot = config.getContent();
        const local = await persistLocal(snapshot);
        state("Локальный черновик сохранён · синхронизация с Core…");
        try {
          const saved = await requestJson(endpoint, {
            method: "PUT",
            body: encode({
              base_revision: local.base_revision,
              expected_draft_revision: draftRevision,
              content: snapshot
            })
          });
          draftRevision = saved.draft_revision;
          conflict = false;
          state("Черновик сохранён в Core · ревизия " + draftRevision);
          return true;
        } catch (error) {
          if (error.status === 409) {
            conflict = true;
            state("Конфликт черновиков · локальная копия сохранена, Core не перезаписан");
          } else {
            state("Локальный черновик сохранён · Core недоступен, будет повтор");
          }
          return false;
        }
      } catch (error) {
        state("Не удалось сохранить локальный черновик: " + error.message);
        return false;
      } finally {
        busy = false;
        if (pending) { pending = false; flush(); }
      }
    }

    function schedule() {
      if (timer) clearTimeout(timer);
      state("Есть изменения · сохранение черновика…");
      timer = setTimeout(() => { timer = null; flush(); }, 350);
    }

    async function clear() {
      if (timer) { clearTimeout(timer); timer = null; }
      await localDelete(key).catch(() => {});
      if (draftRevision) {
        await requestJson(endpoint + "?expected_draft_revision=" + draftRevision, { method: "DELETE" }).catch(() => {});
        draftRevision = 0;
      }
      state("Основная конфигурация сохранена");
      return true;
    }

    const handleOnline = () => { if (!conflict) flush(); };
    const handlePageHide = () => {
      // Best effort only. Durable local writes happen continuously; browsers do not
      // guarantee completion of asynchronous writes started during pagehide.
      if (timer) { clearTimeout(timer); timer = null; }
      flush();
    };
    window.addEventListener("online", handleOnline);
    window.addEventListener("pagehide", handlePageHide);
    loadRecovery();
    const manager = {
      schedule, flush, clear,
      dispose() {
        if (timer) { clearTimeout(timer); timer = null; flush(); }
        window.removeEventListener("online", handleOnline);
        window.removeEventListener("pagehide", handlePageHide);
        bar.remove();
      },
      get conflict() { return conflict; }
    };
    window.__avicDraftManager = manager;
    return manager;
  }

  window.AVICSaveManager = { register };
})();
