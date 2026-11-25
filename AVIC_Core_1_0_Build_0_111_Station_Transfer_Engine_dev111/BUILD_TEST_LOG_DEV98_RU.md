# Журнал разработки и испытаний — AVIC Core DEV98 (подготовка Graphics/RBAC)

Дата: 23.11.2026
База: пользовательская сборка AVIC Core 1.0 DEV97
Версия пакета: `1.0.0.dev98`

## Изменения

- Добавлен типизированный Graphics Binding Engine: Value, Bound Label, Spectrum, Status, Popup, Hyperlink, Historian; контракты Setpoint/Action fail-closed.
- Добавлены целевые свойства text/value/color/visible/rotation/animation/image/status/tooltip.
- Добавлены числовые/булевы/enum/string преобразования, decimals, unit, prefix/suffix, scale/offset, min/max и непересекающиеся Spectrum thresholds.
- Добавлены Degrade Behavior: show_quality, hide, safe_default. Для любого качества, кроме GOOD, запрещены анимация и интерактивность.
- `PointBinding` сохраняет тип, целевое свойство и настройки. На одном объекте разрешены несколько привязок одной роли к разным свойствам.
- `GraphicsService.evaluate_bindings` читает только из Core Point Runtime; добавлен GET `/api/graphics/{document_id}/bindings/evaluate`.
- Graphics Workbench получил настройки типа/свойства/конвертера/точности/единицы/масштаба/смещения/качества/Spectrum.
- Добавлены шаблоны ролей `avic_viewer`, `avic_operator`, `avic_senior_operator`, `avic_engineer`, `avic_security_admin` и station-scoped `GraphicsSecurityPolicy`.
- SVG sanitizer расширен безопасными presentation-параметрами `stroke-miterlimit`, `stop-color`, `stop-opacity`.
- Подготовлена отдельная справочная библиотека из пользовательских JAR: 3 008 визуальных ресурсов, включая 886 безопасно нормализованных SVG. Она не подключена к runtime и не входит в Core wheel.

## Проверки

- Новые/связанные тесты Graphics Binding + RBAC + текущая графика/SVG/Security: **59 passed**.
- Регрессионные тесты DEV97 SCALE/HYSTERESIS, FBD Math/Studio и соседние FBD Runtime/Compiler: **32 passed**.
- `node --check` встроенного JS Graphics Workbench: OK.
- `python -m compileall -q avic_core tests`: OK.
- `node --check` для встроенных JS-блоков Graphics, Logic и Pages: OK.
- Полный `pytest -q` до изменений запускался на DEV97, но не завершился за 300 секунд (около 41%); не считается полным проходом. DEV98 не заявляет полный регрессионный проход.
- Windows/Python 3.15.2 и браузерный E2E не выполнялись.

## Ограничения и открытые работы

- Setpoint/Action не исполняют записи; требуется Command Manager.
- Не все target properties ещё применяются к DOM/SVG Runtime; evaluator и настройки уже доступны.
- Popup и Historian пока контракты без полноценного UI/графика.
- RBAC templates и policy helper добавлены, но не все HTTP endpoints Workbench уже проходят через SecurityGateway. Текущий Workbench остаётся development/loopback интерфейсом.
- Access Lease ещё не интегрирован в команды Graphics.
- Niagara JAR graphics — справочные пользовательские материалы. Право коммерческого включения в AVIC не подтверждено; они исключены из пакета AVIC Core.
- Интеграция с отдельным Repository Manager DEV23 пока не выполнена; для точного объединения требуется его исходный архив/папка. DEV97 используется как базовая ветка Core.

## Артефакты

- Wheel: `avic_core-1.0.0.dev98-py3-none-any.whl` — SHA-256 `c8edbd1045c3b27f02af0e8e2b9c4e9281af1b873bafdd8a54bab7d363a33ca6`.
- Wheel собран через `pip wheel --no-deps --no-build-isolation`, установлен в отдельный target и импортирован вне каталога исходников; Graphics HTML, Binding Engine и GraphicsSecurityPolicy доступны.
- `python -m avic_core --help` — OK.
- `pip check` сохраняет внешний конфликт окружения: moviepy 2.2.1 требует Pillow <12, установлена Pillow 12.3.0.

- По `module.palette` изучены фактические Niagara patterns: Boolean On/Off image binding, Numeric range-to-image mapping, BoundLabel, Action/Hyperlink/Popup, AnalogMeter/Bargraph, SetPoint widgets и increment/decrement. Подробности: `docs/graphics/NIAGARA_GRAPHICS_REFERENCE_ANALYSIS_DEV24_RU.md`.
- Перед финальной упаковкой оптимизировано чтение графики: привязки и FBD-связи группируются одним проходом, Point Runtime samples кэшируются на время оценки документа, чтобы повторные привязки к одной точке не вызывали повторное чтение.
- Итоговый wheel SHA-256: `c8edbd1045c3b27f02af0e8e2b9c4e9281af1b873bafdd8a54bab7d363a33ca6`.
