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
    const recoveryKey = key + ":recovery";
    const initialContent = encode(config.getContent());
    const endpoint = "/api/engineering-drafts/" +
      [editor, stationId, resourceId].map(encodeURIComponent).join("/");
    let draftRevision = 0;
    let remoteContent = null;
    let timer = null;
    let localTimer = null;
    let localWrite = Promise.resolve();
    let busy = false;
    let pending = false;
    let pendingSnapshot = null;
    let conflict = false;
    let recovered = false;
    let recoveryPending = false;
    let recoveryReady = Promise.resolve();
    let dirty = false;
    let localDurable = false;
    let coreSynced = false;
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
      let local = null, preserved = null, remote = null;
      try { local = await localGet(key); } catch (_) {}
      try { preserved = await localGet(recoveryKey); } catch (_) {}
      try {
        remote = await requestJson(endpoint);
        draftRevision = remote.draft_revision || 0;
        remoteContent = remote.content || null;
      } catch (error) {
        if (error.status !== 404) state("Черновик: сервер временно недоступен");
      }
      const candidates = [local, preserved, remote].filter(Boolean);
      candidates.sort((a, b) =>
        (Date.parse(a.updatedAt || a.updated_at || "") || 0)
        - (Date.parse(b.updatedAt || b.updated_at || "") || 0));
      const candidate = candidates[candidates.length - 1];
      if (!candidate || recovered) return;
      const content = candidate.content;
      if (!content || encode(content) === initialContent) return;
      recoveryPending = true;
      // Preserve the found local recovery copy before new edits can replace the
      // primary local key. The server copy is already durable when it exists.
      if (candidate === local) await localPut({ ...local, key: recoveryKey }).catch(() => {});
      state("Найден черновик · " + new Date(candidate.updated_at || candidate.updatedAt || Date.now()).toLocaleString());
      const restoreButton = action("Восстановить", async () => {
        try {
          await config.applyContent(content);
          recovered = true;
          recoveryPending = false;
          await localDelete(recoveryKey).catch(() => {});
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
            draftRevision = 0;
            remoteContent = null;
          }
          await localDelete(recoveryKey).catch(() => {});
          recoveryPending = false;
          if (encode(config.getContent()) === initialContent) {
            await localDelete(key).catch(() => {});
          } else {
            schedule();
          }
          restoreButton.remove();
          discardButton.remove();
          state("Черновик отклонён");
        } catch (error) { state("Не удалось отклонить черновик: " + error.message); }
      });
    }

    async function persistLocal(snapshot, baseRevision = Number(config.getBaseRevision() || 0)) {
      const record = {
        key, editor, stationId, resourceId, content: snapshot,
        base_revision: baseRevision,
        updatedAt: new Date().toISOString()
      };
      await localPut(record);
      return record;
    }

    async function flush(snapshotOverride = null, baseRevisionOverride = null) {
      const snapshot = JSON.parse(encode(snapshotOverride === null ? config.getContent() : snapshotOverride));
      const baseRevision = baseRevisionOverride === null
        ? Number(config.getBaseRevision() || 0) : baseRevisionOverride;
      if (timer) { clearTimeout(timer); timer = null; }
      if (localTimer) { clearTimeout(localTimer); localTimer = null; }
      if (busy) {
        pending = true;
        pendingSnapshot = { snapshot, baseRevision };
        return false;
      }
      busy = true;
      try {
        // Persist this exact editor snapshot locally before waiting for any network
        // recovery lookup. pagehide must not wait on Core availability.
        await localWrite.catch(() => {});
        const local = await persistLocal(snapshot, baseRevision);
        await recoveryReady.catch(() => {});
        if (recoveryPending && !recovered) {
          state("Найден существующий черновик · выберите восстановление или отклонение; новые изменения сохранены локально");
          return false;
        }
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
          remoteContent = snapshot;
          conflict = false;
          if (encode(config.getContent()) === encode(snapshot)) {
            coreSynced = true;
            dirty = false;
          }
          state("Черновик сохранён в Core · ревизия " + draftRevision);
          return true;
        } catch (error) {
          coreSynced = false;
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
        if (pending) {
          const next = pendingSnapshot;
          pending = false;
          pendingSnapshot = null;
          flush(next?.snapshot ?? null, next?.baseRevision ?? null);
        }
      }
    }

    function schedule() {
      if (timer) clearTimeout(timer);
      if (localTimer) clearTimeout(localTimer);
      dirty = true;
      localDurable = false;
      coreSynced = false;
      state("Есть изменения · сохранение черновика…");
      const snapshot = JSON.parse(encode(config.getContent()));
      const baseRevision = Number(config.getBaseRevision() || 0);
      localTimer = setTimeout(() => {
        localTimer = null;
        localWrite = persistLocal(snapshot, baseRevision).then(() => {
          if (encode(config.getContent()) === encode(snapshot)) {
            localDurable = true;
            state("Локальный черновик надёжно сохранён · синхронизация с Core…");
          }
        }).catch(error => {
          localDurable = false;
          state("Не удалось сохранить локальный черновик: " + error.message);
        });
      }, 80);
      timer = setTimeout(() => { timer = null; flush(); }, 350);
    }

    async function clear(savedContent) {
      await recoveryReady.catch(() => {});
      if (timer) { clearTimeout(timer); timer = null; }
      if (localTimer) { clearTimeout(localTimer); localTimer = null; }
      await localWrite.catch(() => {});
      // Do not discard edits made while the primary save request was in flight.
      if (savedContent && encode(config.getContent()) !== encode(savedContent)) {
        schedule();
        return false;
      }
      while (busy) await new Promise(resolve => setTimeout(resolve, 20));
      if (pending) { pending = false; await flush(); }
      if (savedContent && encode(config.getContent()) !== encode(savedContent)) {
        schedule();
        return false;
      }
      const local = await localGet(key).catch(() => null);
      const preserved = await localGet(recoveryKey).catch(() => null);
      const localMatches = !local || !savedContent || encode(local.content) === encode(savedContent);
      const preservedMatches = !preserved || !savedContent || encode(preserved.content) === encode(savedContent);
      const remoteMatches = !draftRevision || (savedContent && remoteContent
        && encode(remoteContent) === encode(savedContent));
      // A draft from another tab/session may be newer or different from the content
      // just saved to the primary document. Never delete it as a side effect.
      if (!localMatches || !preservedMatches || !remoteMatches) {
        state("Основная конфигурация сохранена, но найден другой черновик · он оставлен для восстановления");
        return false;
      }
      if (draftRevision) {
        await requestJson(endpoint + "?expected_draft_revision=" + draftRevision, { method: "DELETE" });
        draftRevision = 0;
        remoteContent = null;
      }
      if (local) await localDelete(key);
      if (preserved) await localDelete(recoveryKey);
      dirty = false;
      localDurable = true;
      coreSynced = true;
      state("Основная конфигурация сохранена");
      return true;
    }

    async function prepareForExit(timeoutMs = 8000) {
      await recoveryReady.catch(() => {});
      if (!dirty && !timer && !localTimer && !busy && !pending) {
        return { safeToClose: true, localSaved: localDurable, coreSaved: coreSynced, conflict };
      }
      const started = Date.now();
      const target = JSON.parse(encode(config.getContent()));
      const targetEncoded = encode(target);
      if (timer) { clearTimeout(timer); timer = null; }
      if (localTimer) { clearTimeout(localTimer); localTimer = null; }
      const operation = flush(target, Number(config.getBaseRevision() || 0));
      await Promise.race([
        operation.catch(() => false),
        new Promise(resolve => setTimeout(resolve, timeoutMs))
      ]);
      while ((busy || pending) && Date.now() - started < timeoutMs) {
        await new Promise(resolve => setTimeout(resolve, 25));
      }
      await localWrite.catch(() => {});
      let record = null;
      try { record = await localGet(key); } catch (_) {}
      const localSaved = Boolean(record && encode(record.content) === targetEncoded);
      const currentMatches = encode(config.getContent()) === targetEncoded;
      if (localSaved && currentMatches) localDurable = true;
      const coreSaved = Boolean(coreSynced && currentMatches && !conflict);
      const safeToClose = currentMatches && (localSaved || coreSaved);
      if (safeToClose) {
        state(coreSaved
          ? "Черновик синхронизирован с Core · можно закрыть AVIC"
          : "Черновик сохранён локально · Core недоступен или есть конфликт; можно закрыть без потери локальной копии");
      } else {
        state("Не удалось подтвердить сохранение последних изменений · оставайтесь в AVIC и повторите попытку");
      }
      return { safeToClose, localSaved, coreSaved, conflict, currentMatches };
    }

    function getExitStatus() {
      return {
        dirty, localDurable, coreSynced, conflict,
        pending: Boolean(timer || localTimer || busy || pending),
        safeToClose: !dirty || localDurable || coreSynced
      };
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
    recoveryReady = loadRecovery().catch(error => {
      state("Не удалось проверить черновики: " + error.message);
    });
    const manager = {
      schedule, flush, clear, prepareForExit, getExitStatus,
      shouldWarnBeforeUnload() { return dirty && !localDurable && !coreSynced; },
      dispose() {
        if (timer) { clearTimeout(timer); timer = null; flush(); }
        else if (localTimer) {
          clearTimeout(localTimer); localTimer = null;
          persistLocal(config.getContent(), Number(config.getBaseRevision() || 0)).catch(() => {});
        }
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
