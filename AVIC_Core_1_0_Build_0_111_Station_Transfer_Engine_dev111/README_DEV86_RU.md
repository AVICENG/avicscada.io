# AVIC Core 1.0 — DEV86

Сборка DEV86 продолжает DEV84 и добавляет общий инженерный tree drawer и единый Point Runtime.

## Основные файлы
- `CHANGELOG_DEV86_RU.md` — изменения.
- `BUILD_TEST_LOG_DEV86_RU.md` — фактические результаты тестов.
- `INSTALL_DEV86_RU.txt` — установка Windows.
- `docs/BUILD_085_RU.md` — описание сборки.
- `docs/POINT_RUNTIME_CONTRACT_DEV86_RU.md` — контракт Live Point Engine.

## Важно
DEV86 обеспечивает единый внутренний механизм значений и качества точек и показывает опубликованные значения в FBD. Это ещё не готовый сетевой polling BACnet/Modbus, не FBD execution runtime и не command/write path. См. ограничения в документации.


## DEV86 — FBD Wiring Hardening

В DEV86 добавлены ортогональная маршрутизация проводов с обходом блоков, выделение выбранного соединения и улучшенная компоновка подписей. Подробности и ограничения см. `BUILD_TEST_LOG_DEV86_RU.md`.
