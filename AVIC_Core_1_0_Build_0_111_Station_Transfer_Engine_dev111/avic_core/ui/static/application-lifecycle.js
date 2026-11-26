(() => {
  "use strict";
  let dialog, message, prepareButton, closeButton, discardButton;
  let working = false;

  function ensureDialog() {
    if (dialog) return dialog;
    const style = document.createElement("style");
    style.textContent = `
      #avic-exit-backdrop{position:fixed;inset:0;z-index:110000;background:rgba(25,42,56,.36);display:flex;align-items:center;justify-content:center;padding:18px}
      #avic-exit-dialog{width:min(520px,96vw);background:#fff;border:1px solid #dbe3e8;border-radius:12px;box-shadow:0 18px 60px rgba(20,40,55,.24);font:13px/1.5 "Segoe UI",Arial,sans-serif;color:#263746}
      #avic-exit-dialog header{padding:17px 19px;border-bottom:1px solid #e8edf0}
      #avic-exit-dialog header strong{font-size:16px;color:#243e54}
      #avic-exit-dialog .body{padding:18px 19px}
      #avic-exit-dialog .message{padding:11px 12px;border:1px solid #e3e9ed;border-radius:8px;background:#f8fafb;color:#536777;min-height:48px}
      #avic-exit-dialog .actions{display:flex;justify-content:flex-end;gap:8px;flex-wrap:wrap;padding:13px 19px;border-top:1px solid #e8edf0}
      #avic-exit-dialog button{border:1px solid #d7e0e6;border-radius:7px;padding:8px 11px;background:#fff;color:#40586a;cursor:pointer}
      #avic-exit-dialog button.primary{background:#243e54;border-color:#243e54;color:#fff}
      #avic-exit-dialog button.danger{border-color:#e3b9b9;color:#a23e3e}
      #avic-exit-dialog button:disabled{opacity:.55;cursor:wait}
      #avic-exit-dialog .hint{margin-top:10px;color:#81909b;font-size:11px}
    `;
    document.head.append(style);
    const backdrop = document.createElement("div");
    backdrop.id = "avic-exit-backdrop";
    backdrop.hidden = true;
    backdrop.innerHTML = `
      <section id="avic-exit-dialog" role="dialog" aria-modal="true" aria-labelledby="avic-exit-title">
        <header><strong id="avic-exit-title">Выход из AVIC Workbench</strong></header>
        <div class="body">
          <div class="message" id="avic-exit-message">Проверка открытых черновиков…</div>
          <div class="hint">Закрывается только интерфейс Workbench. Core и работающий Runtime не останавливаются; их остановка — отдельная инженерная операция. Публикация и применение конфигурации при выходе не выполняются.</div>
        </div>
        <div class="actions">
          <button type="button" id="avic-exit-stay">Остаться</button>
          <button type="button" id="avic-exit-discard" class="danger" hidden>Выйти с потерей изменений</button>
          <button type="button" id="avic-exit-prepare" class="primary">Сохранить черновики</button>
          <button type="button" id="avic-exit-close" class="primary" hidden>Закрыть Workbench</button>
        </div>
      </section>`;
    document.body.append(backdrop);
    dialog = backdrop;
    message = backdrop.querySelector("#avic-exit-message");
    prepareButton = backdrop.querySelector("#avic-exit-prepare");
    closeButton = backdrop.querySelector("#avic-exit-close");
    discardButton = backdrop.querySelector("#avic-exit-discard");
    const hide = () => { if (!working) backdrop.hidden = true; };
    backdrop.querySelector("#avic-exit-stay").addEventListener("click", hide);
    backdrop.addEventListener("click", e => { if (e.target === backdrop) hide(); });
    document.addEventListener("keydown", e => { if (e.key === "Escape" && !backdrop.hidden) hide(); });
    prepareButton.addEventListener("click", prepare);
    closeButton.addEventListener("click", closeAfterConfirmation);
    discardButton.addEventListener("click", leaveWithLoss);
    return dialog;
  }

  function show() {
    const d = ensureDialog();
    d.hidden = false;
    message.textContent = "Проверяем изменения и готовим черновики к закрытию…";
    prepareButton.hidden = false;
    closeButton.hidden = true;
    discardButton.hidden = true;
    prepareButton.disabled = false;
    prepareButton.textContent = "Сохранить черновики";
    prepareButton.focus();
  }

  async function prepare() {
    if (working) return;
    working = true;
    prepareButton.disabled = true;
    closeButton.hidden = true;
    discardButton.hidden = true;
    message.textContent = "Сохраняем последние изменения локально и в Core. Это может занять несколько секунд…";
    try {
      const manager = window.__avicDraftManager;
      const result = manager && typeof manager.prepareForExit === "function"
        ? await manager.prepareForExit(8000)
        : { safeToClose: true, noActiveEditor: true };
      if (result.safeToClose) {
        message.textContent = result.noActiveEditor
          ? "Открытых инженерных редакторов с несохранёнными изменениями нет."
          : result.coreSaved
            ? "Все изменения текущего редактора сохранены как черновик в Core. Можно закрыть Workbench."
            : result.localSaved
              ? "Последние изменения сохранены в локальном хранилище браузера. Core пока недоступен или обнаружен конфликт; локальный черновик сохранён и может быть восстановлен."
              : "Активных несохранённых изменений нет. Можно закрыть Workbench.";
        prepareButton.hidden = true;
        closeButton.hidden = false;
      } else {
        message.textContent = "Не удалось подтвердить сохранение последних изменений. Оставайтесь в AVIC и повторите попытку. Если всё же выйти, последние изменения могут быть потеряны.";
        prepareButton.disabled = false;
        prepareButton.textContent = "Повторить сохранение";
        discardButton.hidden = false;
      }
    } catch (error) {
      message.textContent = "Ошибка при подготовке к выходу: " + error.message + ". Можно повторить сохранение или остаться в приложении.";
      prepareButton.disabled = false;
      prepareButton.textContent = "Повторить сохранение";
      discardButton.hidden = false;
    } finally {
      working = false;
    }
  }

  function closeAfterConfirmation() {
    window.__avicExitConfirmed = true;
    window.close();
    setTimeout(() => {
      if (!window.closed) {
        message.textContent = "Черновики сохранены. Браузер не разрешает странице закрыть вкладку программно. Закройте вкладку или окно обычной кнопкой браузера.";
        closeButton.hidden = true;
      }
    }, 250);
  }

  function leaveWithLoss() {
    if (!window.confirm("Выйти без подтверждённого сохранения последних изменений? Часть работы может быть потеряна.")) return;
    window.__avicExitConfirmed = true;
    window.close();
    setTimeout(() => {
      if (!window.closed) {
        message.textContent = "Вы подтвердили выход с риском потери изменений. Браузер не разрешает закрыть эту вкладку программно; закройте её обычной кнопкой.";
        discardButton.hidden = true;
      }
    }, 250);
  }

  async function stopCore() {
    if (!window.confirm("Остановить AVIC Core? Будут остановлены все работающие FBD-стратегии, драйверы и Runtime всех станций. Управление оборудованием прекратится. Workbench также завершит работу.")) return;
    try {
      const previewResponse = await fetch("/api/core/shutdown-preview", { credentials: "same-origin" });
      if (!previewResponse.ok) throw new Error((await previewResponse.json()).detail || "Не удалось проверить состояние Core");
      const preview = await previewResponse.json();
      if (!["RUNNING", "SHUTDOWN_BLOCKED"].includes(preview.core_state) || !preview.can_shutdown) {
        throw new Error("Core уже остановлен или остановка ещё выполняется.");
      }
      const stations = (preview.active_stations || []).map(x => x.station_id + " [" + x.state + "]");
      const drivers = (preview.active_drivers || []).map(x => x.driver_id + " [" + x.state + "]");
      const strategies = (preview.active_fbd_strategies || []).map(x => x.document_id + " [" + x.state + "]");
      const driverIssues = (preview.driver_issues || []).map(x => x.driver_id + " [" + x.state + "]");
      const details = [
        "Состояние Core: " + preview.core_state,
        "Активные станции: " + (stations.length ? stations.join(", ") : "нет"),
        "Активные драйверы: " + (drivers.length ? drivers.join(", ") : "нет"),
        "Драйверы с диагностическими проблемами: " + (driverIssues.length ? driverIssues.join(", ") : "нет"),
        "Активные FBD: " + (strategies.length ? strategies.join(", ") : "нет"),
        "Ошибки FBD: " + ((preview.fbd_errors || []).length)
      ].join("\\n");
      if (!window.confirm("Состояние перед остановкой:\\n" + details + "\\n\\nОстановить все перечисленные службы?")) return;
      const typed = window.prompt("Для подтверждения введите точно: STOP AVIC CORE");
      if (typed !== "STOP AVIC CORE") return;
      const response = await fetch("/api/core/shutdown", {
        method: "POST", credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ confirmation: typed })
      });
      const result = await response.json();
      if (!response.ok) throw new Error(result.detail || "Безопасная остановка не подтверждена");
      window.alert(result.message || "AVIC Core остановлен.");
    } catch (error) {
      window.alert("AVIC Core не остановлен: " + error.message);
    }
  }

  window.addEventListener("beforeunload", event => {
    if (window.__avicExitConfirmed) return;
    const manager = window.__avicDraftManager;
    if (manager && typeof manager.shouldWarnBeforeUnload === "function" && manager.shouldWarnBeforeUnload()) {
      event.preventDefault();
      event.returnValue = "";
    }
  });

  document.addEventListener("click", event => {
    if (event.target.closest("#avicApplicationExit")) {
      event.preventDefault();
      show();
    }
    if (event.target.closest("#avicCoreStop")) {
      event.preventDefault();
      stopCore();
    }
  });
  window.AVICApplicationExit = { show };
})();