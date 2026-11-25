# Журнал сборки и тестирования DEV108

Дата: 24.11.2026  
База: пользовательский архив AVIC Core 1.0 DEV107.

## Причина корректировки

В Windows full-suite журнале DEV107 было зафиксировано `1 failed, 31136 passed, 1 skipped`. Единственный упавший тест `test_graphics_symbol_catalog_includes_station_imports_and_page_editor_has_visual_components` ожидал, что `GET /pages` вернёт старый `pages.html` с атрибутами `data-add-block`.

Это ожидание противоречило более позднему контракту DEV99 и документации DEV107: `/pages` является совместимым адресом Graphics Workbench, а действующий Web Application Page Builder открывается через `/repository?section=WebApplication`. В актуальном `repository.html` компоненты размечены атрибутом `data-add`, а не `data-add-block`.

## Изменения

- Исправлен только устаревший тест; продуктовая маршрутизация не менялась.
- Проверяется, что `/pages` возвращает Graphics Workbench.
- Проверяется, что Repository Web Application предоставляет восемь типов компонентов: heading, text, card, button, image, divider, value, graphic.
- Дополнительно проверяются холст, панель свойств и кнопка публикации.
- Версия приложения обновлена до `1.0.0.dev108`.

## Дополнительная корректировка тестов

- Обновлена проверка `/api/ui/health`, чтобы она ожидала версию DEV108, а не зафиксированную в DEV107.

## Проверки

| Проверка | Результат |
|---|---|
| Фокусные тесты SVG import, Repository, Page Builder, navigation и release guards | **31 passed** |
| Полный набор pytest в текущей Linux-среде | Не завершён: ограничение времени выполнения инструмента; это не результат тестирования всего набора |
| Windows full-suite DEV107 из пользовательского журнала | **1 failed, 31136 passed, 1 skipped**; падение соответствует устаревшему ожиданию маршрута `/pages` |

## Ограничения

- Windows full-suite DEV108 должен быть подтверждён на целевой Windows-машине пользователя.
- Эта корректирующая сборка не добавляет новую функциональность Web Application или Graphics.
- Физические BACnet/Modbus записи не выполняются; Command Manager остаётся SIMULATION_ONLY.

## Статус

**DEV108: локальная причина единственного известного падения исправлена в тестовом контракте; фокусный набор пройден. Полный Windows acceptance DEV108 ожидает подтверждения.**

## Дополнительные локальные проверки DEV108

| Проверка | Результат |
|---|---|
| `python -m compileall -q avic_core` | OK |
| Фокусный набор Repository / Page Builder / SVG / navigation | **31 passed** |
| Smoke: `/api/ui/health`, `/pages`, `/repository?section=WebApplication` | OK |
| `node --check` для inline JavaScript `repository.html` | OK |
| Сборка wheel `avic_core-1.0.0.dev108-py3-none-any.whl` | OK, 529 449 байт |
| Установка wheel в отдельный target и smoke test установленного пакета | OK |
| `pip check` | В окружении есть внешнее несоответствие: `moviepy 2.2.1` требует `pillow<12`, установлена `pillow 12.3.0`; AVIC не объявляет Pillow как зависимость |

SHA256 wheel: `1acabe1673c1d262f843f00ff9d06736c8279559fa77c912b416ceeaf0d7d228`.
