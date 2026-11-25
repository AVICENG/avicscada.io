# Журнал сборки DEV104 — Web Application Page Builder

Дата: 2026-11-23  
База: пользовательский DEV103 (FBD Virtual Points / Tree / Graphics Integration).

## Реализовано

- Отдельный Web Application Page Builder (`repository.html`) для ветки Repository → Web Application. Graphics branch по-прежнему открывает Graphics Workbench; старый `pages.html` не подключён.
- Динамическая проекция сайтов, папок и страниц в общее инженерное дерево станции; выбор узла дерева открывает редактор с выбранной страницей.
- Создание одного корневого сайта на станцию, папок и страниц; slug и URL; station-scoped дерево.
- Визуальная палитра: heading, text, image, value, graphic-link, divider, card, decorative button.
- Перетаскивание элементов палитры на холст и перемещение блоков мышью; инспектор свойств.
- Загрузка PNG/JPEG/GIF/WebP с компьютера (до 3 МБ) в существующий Core SQLite Repository как RepositoryAsset; проверка MIME по сигнатуре, SHA-256, станционная область.
- Привязка value-компонентов к физическим/FBD Core points по постоянному ID; проверка существования и принадлежности станции.
- Публикация immutable layout snapshot, отдельная от черновика; runtime route `/published/...`.
- Обновление значений опубликованной страницы из общего Point Runtime одним запросом раз в 2 секунды; не-GOOD качество отображается как недостоверное.
- История до 50 опубликованных снимков и API rollback/unpublish.
- Экранирование текстов, проверка URL, CSP nonce, отсутствие пользовательского JS на опубликованной странице, защита загруженных ресурсов.
- Русское руководство `docs/WEB_APPLICATION_PAGE_BUILDER_DEV104_RU.md`.

## Проверки

- `python -m compileall -q avic_core` — выполнено после изменений.
- `node --check /tmp/avic_repository_editor.js` — выполнено для клиентского кода редактора до последних небольших UI-правок; требуется повторная проверка итогового файла перед релизом.
- Итоговый связанный регрессионный набор (Web Pages DEV44/DEV65, Unified Editor DEV46, Repository DEV99, UI Workbench, Engineering Tree DEV39, Graphics Binding DEV98, AHU/FBD DEV102, FBD Exposed Runtime DEV103) — **46 passed** за 6.82 секунды. Включены публикация, immutable snapshot, повторная публикация, rollback, загрузка растрового изображения, проверка runtime точки и проекция страниц в общее инженерное дерево.
- `python -m compileall -q avic_core` — OK.
- `node --check` для итогового JavaScript редактора — OK.
- Wheel собран с `--no-build-isolation`, установлен в отдельный target-каталог; импорт приложения и наличие `repository.html` внутри wheel — OK.

## Не подтверждено / ограничения

- Полный тестовый набор проекта не запускался в DEV104; проверен связанный регрессионный набор из 46 тестов.
- Windows acceptance не выполнялся; текущая среда сборки Linux.
- Нет полноценного файлового Web IDE с пользовательскими index.html/style.css/script.js и SPA routing.
- Graphics component пока является ссылкой на Graphics Workbench, не полноценным embedded Graphics Runtime.
- Кнопка декоративная; команды оборудования не подключены.
- RBAC publish/runtime, HTTPS reverse proxy и production deployment ещё не завершены.

## Артефакты

- `avic_core-1.0.0.dev104-py3-none-any.whl` — 522 652 байта; SHA256 `797caa175bc9e8711ed63a897d027a5d2a2e42d4aa7572719937ab7f0b71918e`.
- Сборка wheel в изолированном режиме сначала не удалась из-за отсутствия сетевого доступа для build dependencies; повторная сборка с `--no-build-isolation` успешна.
- `pip check` общей среды сообщает внешний конфликт: `moviepy 2.2.1` требует `pillow<12.0`, установлен `pillow 12.3.0`; это не зависимость AVIC Core.

## Статус

**DEV104 — функциональный прототип визуального Web Page Builder и публикации для локальной инженерной среды. Не считать готовой production-публикацией и не использовать как подтверждение готовности команд управления оборудованием.**
