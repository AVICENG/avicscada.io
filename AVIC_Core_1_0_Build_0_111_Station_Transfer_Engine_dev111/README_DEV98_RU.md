# AVIC Core 1.0 — DEV98 (Graphics Binding / RBAC preparation)

DEV98 продолжает базу Core DEV97 и готовит фундамент для объединения отдельного Repository Manager с основным Core.

## Ключевые изменения
- Типизированные привязки к стабильным Core Point ID и runtime evaluator.
- Форматирование значений, конвертеры, Spectrum thresholds и Degrade Behavior.
- Множественные привязки к разным свойствам одного графического объекта.
- Новые granular RBAC templates и station-scoped policy helper.
- Отдельный справочный каталог Niagara SVG/PNG/GIF, не включённый в Core Runtime.

## Ограничения
Команды и уставки не выполняются до подключения Command Manager. Полная защита всех API маршрутов и Access Lease интеграция остаются обязательными этапами. DEV98 не является объединённой сборкой Repository Manager + Core; это подготовительная ветка на основе предоставленного DEV97.

Подробности: `BUILD_TEST_LOG_DEV98_RU.md`, `docs/graphics/GRAPHICS_BINDING_ENGINE_DEV98_RU.md`, `docs/security/RBAC_ROLE_MATRIX_DEV98_RU.md`.

Дополнительный анализ Niagara JAR: `docs/graphics/NIAGARA_GRAPHICS_REFERENCE_ANALYSIS_DEV24_RU.md`. Отдельная офлайн-библиотека ресурсов: `AVIC_Graphics_Reference_Library_DEV24.zip` (не включена в Core Runtime).
