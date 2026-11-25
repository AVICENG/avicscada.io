# Журнал сборки AVIC Core 1.0 — DEV44

Дата: 19.11.2026
База: присланный пользователем архив DEV43 Bottom Inspector / Engineering Tree.
Версия пакета: `1.0.0.dev44`.

## Реализовано
- Web Pages module: `WebPageNode`, `WebPagesService`.
- Персистентное дерево Site / Folder / Page на существующем SQLite Repository.
- CRUD, переименование, перемещение, drag-and-drop, рекурсивное удаление.
- Slug и URL, транслитерация русских названий папок, проверка дубликатов и циклического перемещения.
- Сохранение HTML/CSS/JS и visual layout, optimistic concurrency.
- Привязка мнемосхем к страницам с проверкой station scope.
- Новый UI `/pages`, ссылка из меню инженерного Workbench.
- Исправлен выбор узлов и видимость `···` в основном инженерном дереве.
- Документация DEV44 и сценарий использования.

## Проверки
- Новые тесты Web Pages: 6 passed.
- Полный набор: 223 passed.
- `compileall`: успешно.
- `node --check` для обоих UI JavaScript: успешно.
- `pip check`: обнаружен внешний конфликт `moviepy 2.2.1` ↔ `pillow 12.3.0`.

## Не завершено
- Windows UI acceptance (нужна проверка пользователем на реальном браузере/Windows).
- Production publishing, customer authentication, TLS/domain/IP binding, RBAC/MFA.
- Полноценная responsive layout система, полноценное визуальное редактирование всех типов компонентов, live widgets и runtime point rendering.
- Веб-команды управления оборудованием выключены.

## Readiness
Функциональная dev-сборка для инженерного создания и организации страниц. Не production-ready. Не открывать публичный доступ.
