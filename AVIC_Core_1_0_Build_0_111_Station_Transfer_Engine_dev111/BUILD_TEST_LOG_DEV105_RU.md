# Журнал сборки DEV105 — Embedded Graphics Runtime

Дата: 2026-11-23  
База: DEV104 Web Application Page Builder.

## Реализовано

- Компонент `graphic` на опубликованной Web Application странице теперь отображает мнемосхему во встроенном iframe runtime.
- Публикация страницы фиксирует snapshot каждого включённого GraphicDocument: элементы, символы, геометрия и конфигурация привязок.
- Изменения исходного документа Graphics после публикации не меняют ранее опубликованную страницу.
- Embedded runtime получает символы из локальной AVIC SVG-библиотеки; для custom SVG использует защищённый endpoint.
- Read-only bindings вычисляются из snapshot привязок и актуальных значений общего Core Point Runtime.
- Значения обновляются каждые 2 секунды; анимация допускается только при GOOD качестве и активном boolean feedback.
- Проверяется, что страница опубликована, относится к указанной станции и действительно содержит эту мнемосхему в опубликованном snapshot.
- CSP для встроенной мнемосхемы использует nonce для runtime script; произвольный пользовательский JavaScript не выполняется.

## Проверки

- `python -m compileall -q avic_core` — OK.
- `node --check` embedded Graphics Runtime JS — OK.
- `pytest -q tests/test_web_pages_authoring_dev65.py tests/test_graphics_binding_engine_dev98.py tests/test_web_pages_dev44.py tests/test_graphics_security_roles_dev98.py tests/test_dev103_fbd_exposed_runtime_points.py` — **50 passed**.
- Новый регрессионный тест проверяет embedded runtime, live point feedback, запрет просмотра неопубликованной графики и неизменность опубликованного снимка после редактирования исходной мнемосхемы.

## Ограничения

- Полный набор тестов проекта не запускался.
- Windows acceptance не выполнялся.
- Runtime остаётся read-only: запуск/остановка, уставки и ручной режим не подключены.
- RBAC publish/runtime и промышленное HTTPS deployment не завершены.
- Отображение проверено через FastAPI TestClient и синтаксис JavaScript; отдельный браузерный acceptance embedded iframe ещё требуется.

## Статус

**DEV105 — проверенная интеграция опубликованной Web Application страницы с read-only Graphics Runtime. Не является завершённым Command Manager и не разрешает полевые записи.**
