# AVIC FBD — сводный аудит сквозного покрытия DEV192

Дата: 26.11.2026  
Ветка: `ci/fbd-connective-compiler`  
База PR: `dev183-linux-cli-test-fix`  
PR: https://github.com/AVICENG/avicscada.io/pull/5

## Итог

В DEV192 все 29 типов блоков, отображаемых редактором FBD, имеют Core-контракт, серверный compiler mapping и путь Core simulation. CONNECTIVE и TO_CONNECTIVE рассматриваются отдельно как межстраничные reference/navigation primitives, а не вычислительные блоки.

**Важно:** 29/29 означает наличие сквозного пути в исходном коде, но не означает, что DEV192 принят тестами. Полный Windows/Linux CI после изменений ещё не запускался. Все compute jobs GitHub Actions переведены в ручной режим, чтобы не создавать несанкционированные расходы.

## Матрица блоков

| Тип | Core контракт | Компилятор | Core simulation | Примечание |
|---|---|---|---|---|
| BOOL_INPUT | Да | Да | Да | Виртуальный BOOL источник |
| FLOAT_INPUT | Да | Да | Да | Виртуальный FLOAT источник |
| POINT_INPUT | Да | Да | Да | Реальная точка станции; ownership/type/quality checks |
| ANALOG_INPUT | Да | Да | Да | Виртуальный датчик с rawValue/scalingPoints |
| EXTERNAL_SENSOR | Да | Да | Да | Виртуальный внешний датчик; явная калибровочная таблица |
| BOOL_OUTPUT | Да | Да | Да | BOOL результат стратегии |
| FLOAT_OUTPUT | Да | Да | Да | FLOAT результат стратегии |
| COMBINATION | Да | Да | Да | E/F/G/H; AND в строке, OR между включёнными строками |
| PID_LOOP | Да | Да | Да | OUT/P/I/D; AUTO/MANUAL, anti-windup, reset, bumpless transfer |
| AND | Да | Да | Да | Логическое И |
| OR | Да | Да | Да | Логическое ИЛИ |
| NOT | Да | Да | Да | Логическое НЕ |
| ADD | Да | Да | Да | Сложение |
| SUB | Да | Да | Да | Вычитание |
| MUL | Да | Да | Да | Умножение |
| DIV | Да | Да | Да | Деление с защитой от нуля |
| COMPARE_GT | Да | Да | Да | Сравнение больше |
| COMPARE_LT | Да | Да | Да | Сравнение меньше |
| LIMIT | Да | Да | Да | Ограничение диапазона |
| SCALE | Да | Да | Да | Масштабирование |
| SELECT | Да | Да | Да | Выбор A/B по BOOL SEL |
| HYSTERESIS | Да | Да | Да | Состояние изолировано по стратегии |
| DELAY | Да | Да | Да | On/off задержки по реальному интервалу FBD tick |
| LATCH | Да | Да | Да | SET/RESET, настраиваемый приоритет |
| SWITCH | Да | Да | Да | Status source/constant → Destination; PIN level сохраняется |
| KNOB | Да | Да | Да | Числовой источник; test override только в симуляции |
| TIME | Да | Да | Да | 21 выход станции; Core TimeManagementService |
| SCHEDULE | Да | Да | Да | Тип результата соответствует конфигурации Scheduler |
| CONSTANT | Да | Да | Да | Конечная числовая константа |

## Семантика межстраничных ссылок

- CONNECTIVE переносит значение с конкретного именованного выхода исходного блока.
- TO_CONNECTIVE остаётся маркером назначения/навигации и не исполняется как блок.
- Проверяются уникальность reference ID, принадлежность страницам, source/proxy ownership, port index/name, signal type, отсутствие orphan proxy/marker и дубликатов.
- Все сохранённые wire links валидируются: endpoint, направление, страница, порт, единственный вход и совместимость типов.
- Циклы проверяются без рекурсивного обхода; длинные графы не зависят от Python recursion limit.

## Состояние и Runtime

- DELAY получает фактическую длительность тика из FBDExecutionService.
- LATCH и PID сохраняют состояние на стратегию; состояние коммитится только после успешного прохода графа.
- TIME читает часовой пояс станции из Core TimeManagementService. Пульсы формируются на границах периода и удерживаются одну секунду.
- TIME не устанавливает системные часы и не запускает синхронизацию устройств. NTP/timezone/DST принадлежат Core Time Manager; разрешение синхронизации каждого устройства должно быть отдельным.
- Симуляция не выполняет физические записи; компиляция не означает публикацию.

## Ограничения, которые не следует скрывать

1. **SWITCH и KNOB:** поле `user_level` сохраняется как PIN-level metadata (0–99), но отдельный runtime API изменения статуса/значения с проверкой пользователя/роли ещё не включён. Изменение через инженерный редактор не считается операторской командой.
2. **TIME:** поддерживаются time outputs, calendar values и pulses. Trend Time Master distribution не реализован как скрытая функция FBD; это отдельная функция Core Time Manager/Network Time policy.
3. **ANALOG_INPUT / EXTERNAL_SENSOR:** являются виртуальными/симуляционными источниками с явной калибровкой. Физические BACnet/Modbus датчики подключаются через POINT_INPUT и драйверы.
4. **Trend parity:** PID и блоки воспроизводят задокументированную/локальную AVIC семантику. Нельзя заявлять побитовую идентичность закрытой прошивке Trend без испытания на реальном контроллере и эталонных сценариев.
5. **CI:** тесты DEV186–DEV192 добавлены, но не выполнены в рамках этой серии изменений. Не помечать DEV192 как ACCEPTED до полного Windows и Linux прогона.

## Добавленные регрессионные тесты

- `tests/test_fbd_core_knob_constant_dev186.py`
- `tests/test_fbd_combination_dev187.py`
- `tests/test_fbd_stateful_delay_latch_dev188.py`
- `tests/test_fbd_analog_sensor_sources_dev189.py`
- `tests/test_fbd_pid_loop_dev190.py`
- `tests/test_fbd_switch_time_dev191.py`
- Существующие regression suites DEV185 для cross-page dynamic signal types, reference markers, port index validation и connective integrity.

## Источники и ориентиры

Trend IQ3 Configuration Manual TE200768, Part 2 Section 31 описывает Switch как Status source/constant и Destination output, а Section 32 — Time Module outputs, timing pulses и time synchronization. В AVIC эти функции разделены с учётом Core Time Manager и RBAC boundary:
https://autorem.fr/Docs/Trend/iq3_config_EN.pdf

## Статус DEV192

**НЕ ПОДТВЕРЖДЁН CI**

Исходный код и документация внесены в ветку `ci/fbd-connective-compiler`. PR #5 остаётся Draft. Автоматические compute jobs выключены; для приёмки требуется явный запуск тестов с согласованным бюджетом.


## DEV192 — KNOB completeness and catalog contract test

DEV192 extends KNOB from a bare numeric source to the documented engineering contract:
- `value`, `bottom_range`, `top_range`, `cov_increment`, `units`, `user_level`;
- finite values only; bottom ≤ value ≤ top; COV increment nonnegative; PIN level 0–99;
- simulation overrides are rejected outside the configured range;
- UI exposes the range, units and PIN metadata.

Added `tests/test_fbd_catalog_parity_dev192.py`, which asserts exact equality of the 29 UI type IDs, Core block contracts, compiler mappings and named input/output port sets.

PIN level for KNOB and SWITCH remains metadata until the runtime operator command path is connected to AVIC RBAC. The blocks can be compiled and simulated; this must not be interpreted as operator write authorization.

- Legacy `TIME.OCC` placeholder documents are rejected with an explicit migration instruction. No automatic mapping to a time output is attempted because OCC is not a Trend Time Module output.

- `SCALE` намеренно имеет в Studio один signal input IN; compiler материализует IN_MIN/IN_MAX/OUT_MIN/OUT_MAX как отдельные Core FLOAT_INPUT nodes, сохраняя canonical Core-контракт. Catalog parity test учитывает это проектное отображение.
