# AVIC Core 1.0 — DEV108

DEV108 — корректирующая сборка поверх DEV107. Исправлена регрессионная проверка, которая продолжала требовать от `/pages` старый редактор `pages.html`, хотя начиная с DEV99 этот маршрут намеренно оставлен совместимым входом в Graphics Workbench.

## Актуальные точки входа

- `/repository?section=WebApplication` — Web Application Page Builder: создание сайта/папок/страниц, палитра из восьми компонентов, редактирование, сохранение и публикация.
- `/repository?section=GraphicsRepository` — Graphics Workbench с библиотекой SVG и импортом пользовательских символов станции.
- `/graphics` и совместимый `/pages` — Graphics Workbench.
- `pages.html` — исторический статический редактор; не является активной точкой входа Repository.

## Что исправлено

Тест `tests/test_svg_import_dev65.py` больше не смешивает старый контракт DEV65 с новой архитектурой DEV99+. Он проверяет импорт SVG, совместимость `/pages` и фактическую палитру Web Application Page Builder на маршруте Repository.

## Ограничения продукта

DEV108 не добавляет физические BACnet/Modbus записи. Command Manager остаётся `SIMULATION_ONLY`; операторская кнопка Page Builder декоративная. Полноценные пользовательские сессии, server-side RBAC и MFA ещё не реализованы.

Результаты проверок см. `BUILD_TEST_LOG_DEV108_RU.md`.
