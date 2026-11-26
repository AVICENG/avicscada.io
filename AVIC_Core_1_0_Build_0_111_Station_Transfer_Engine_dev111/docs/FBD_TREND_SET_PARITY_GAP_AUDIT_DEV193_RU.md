# AVIC FBD / Trend SET — аудит полноты блоков и Scheduler (DEV193)

Дата: 26.11.2026  
Ветка: `ci/fbd-connective-compiler`  
Базовая версия: AVIC Core `1.0.0.dev193`

## 1. Исправление прежнего вывода

Ранее формулировка «все 29 блоков сделаны» была неверной. В коде присутствуют 29 зарегистрированных типов AVIC FBD Editor/Core/Compiler. Это **не означает**, что реализован полный набор модулей Trend SET/IQ3 и что обеспечен функциональный паритет.

DEV193 устраняет конкретный разрыв: FBD `SCHEDULE` больше не хранит отдельный частный календарь в параметрах блока. Инженер выбирает существующее расписание Core Scheduler своей станции; блок сохраняет `schedule_id`, тип выхода определяется объектом расписания, компилятор проверяет станцию и тип, а локальная симуляция получает значение через Core Schedule API. Старые локальные расписания не переносятся автоматически.

## 2. Текущие 29 типов AVIC FBD

`BOOL_INPUT`, `FLOAT_INPUT`, `POINT_INPUT`, `ANALOG_INPUT`, `EXTERNAL_SENSOR`, `BOOL_OUTPUT`, `FLOAT_OUTPUT`, `COMBINATION`, `PID_LOOP`, `AND`, `OR`, `NOT`, `ADD`, `SUB`, `MUL`, `DIV`, `COMPARE_GT`, `COMPARE_LT`, `LIMIT`, `SCALE`, `SELECT`, `HYSTERESIS`, `DELAY`, `LATCH`, `SWITCH`, `KNOB`, `TIME`, `SCHEDULE`, `CONSTANT`.

Эти типы присутствуют в UI-каталоге, Core block contract и Studio compiler mapping. Проверка точного набора/портов ведётся тестом `test_fbd_catalog_parity_dev192.py`. Это внутренняя матрица AVIC, а не каталог всех типов Trend.

## 3. Сверка с Trend IQ3 Configuration Manual

В руководстве Trend IQ3 Configuration Manual, Issue 3 (28.01.2009), перечислены отдельные семейства модулей. Сверка ниже нужна как инженерный ориентир; она не утверждает, что все поколения Trend/IQVISION имеют одинаковые модули.

### 3.1 Function Modules — 26 типов Trend

| Trend type | Функция | Состояние AVIC |
|---:|---|---|
| 1 | Filter | Нет отдельного эквивалента |
| 2 | Rescale From | Частично: SCALE/LIMIT, не эквивалентный контракт |
| 3 | Rescale To | Частично: SCALE/LIMIT, не эквивалентный контракт |
| 4 | Limit At | Частично: LIMIT |
| 5 | Limit To | Частично: LIMIT |
| 6 | Log | Нет |
| 7 | Square Root | Нет |
| 8 | Adder/Scaler, `D=(E×G)+(F×H)` | Нет точного четырёхвходового эквивалента |
| 9 | Multiplier (3 inputs) | Частично: MUL только с двумя входами |
| 10 | Divider | Частично: DIV; требуется сверка поведения divide-by-zero |
| 11 | Minimum (up to 4 inputs) | Нет |
| 12 | Maximum (up to 4 inputs) | Нет |
| 13 | Average (up to 4 inputs) | Нет |
| 14 | Analogue Gate | Частично: SELECT |
| 15 | Comparator | Частично: COMPARE_GT / COMPARE_LT |
| 16 | Enthalpy | Нет |
| 17 | Hysteresis Band | Частично: HYSTERESIS; требуется точная сверка семантики |
| 18 | Analogue-to-Digital Converter (8 bits) | Нет |
| 19 | Lookup | Нет |
| 20 | Adder (4 inputs) | Частично: ADD только с двумя входами |
| 21 | Hysteresis Limits | Частично: HYSTERESIS; отдельный контракт отсутствует |
| 22 | Proximity | Нет |
| 23 | Power | Нет |
| 24 | Absolute | Нет |
| 25 | Truncate | Нет |
| 26 | Trigonometric (sin/cos/tan, degrees/radians) | Нет |

### 3.2 Logic Modules — 8 типов Trend

| Trend type | Функция | Состояние AVIC |
|---:|---|---|
| 1 | Combination | Есть COMBINATION; необходима полная проверка формул/таблиц |
| 2 | Timer | Нет точного отдельного блока |
| 3 | Readback | Нет |
| 4 | Counter (count + rate) | Нет |
| 5 | Delay (сравнение двух входов и grace time) | Текущий AVIC DELAY — другая функция (on/off delay одного BOOL входа); не считать эквивалентом |
| 6 | Hours Run | Нет |
| 7 | Fan Out (1 вход → до 6 выходов) | Нет |
| 8 | D to A (до 8 BOOL входов → числовое значение) | Нет |

AVIC LATCH, AND/OR/NOT не заменяют отсутствующие Trend Logic Modules.

### 3.3 Schedule H, Time Zone Z и OSS

- Trend Schedule Module H — отдельный аналоговый селектор: Manual Select, Non-Occupied, Warm-Up, Occupied, Cool-Down, Manual Level; параметры Type (OSS/OTP), Zone, Start Deviation, Stop Deviation; аналоговый выход. AVIC `SCHEDULE` в DEV193 — ссылка на Core Schedule Service и **не является** эквивалентом Trend H.
- Trend Time Zone / Occupation Time Profile и Optimum Start/Stop (OSS) — отдельные сущности/алгоритмы. AVIC `TIME` (часы и импульсы) и Scheduler Manager не реализуют полный Trend Z/OSS модульный контракт.
- AVIC PID_LOOP покрывает часть loop-регулирования, но не заявляется как полная копия Trend Loop Module: требуется отдельная сверка всех входов, режимов, alarm/readback, reschedule и OSS setpoint selection.

### 3.4 Прочие семейства, которые не входят в 29 типов AVIC

Trend SET также описывает Sensors, Knobs, Switches, Drivers, I/O modules, Sequence Table, Plot, Program, IC Comms, Network, OSS и другие типы. В AVIC часть задач покрывается сервисами Core, POINT_INPUT/OUTPUT и сетевыми драйверами, но это не означает один-в-один соответствие символов, параметров и runtime-семантики Trend.

## 4. Scheduler Manager — что уже есть

- Типизированные расписания BOOLEAN / NUMERIC / ENUM / STRING.
- IANA timezone, default value, effective start/end, enabled.
- Недельные интервалы и календарные special events с приоритетом.
- Временный manual override с оператором, причиной и сроком.
- Вычисление текущего значения, источника и следующего изменения.
- Копирование дней недели, список совместимых выходных точек.
- Привязка точек только как намерение; результат явно `INTENT_ONLY_NO_FIELD_WRITE`.
- FBD SCHEDULE ссылается на тот же Core schedule object, не создавая частную копию.

## 5. Scheduler Manager — незакрытые задачи

1. Недельная сетка пока обзорная, без drag/resize.
2. Нет полноценного редактирования события на месте; UI позволяет добавлять и удалять.
3. Нет полноценного CRUD расписания (изменение свойств и безопасное удаление).
4. Нет Calendar Manager с ежегодными/повторяющимися правилами, календарями объектов/площадок и многодневными событиями.
5. Нет отдельного Scheduler Runtime с журналом фактического исполнения, контролем пропусков и восстановлением runtime-состояния.
6. Нет Trend Schedule Import/Export для чтения/записи расписаний контроллеров.
7. Нет Command Manager, который арбитрирует ручные команды, расписания, interlocks, аварийные защиты, approval и read-back.
8. Нет полного runtime RBAC для PIN/user level. Текущая локальная защита API не является готовой многопользовательской моделью доступа.

## 6. Следующая очередь реализации

Приоритеты:
1. Trend H Schedule Module и совместная модель с Core Scheduler без дублирования календарей.
2. Trend Logic Modules: Timer, Readback, Counter, Hours Run, Fan Out, D-to-A; затем точная семантика Delay.
3. Отсутствующие Function Modules с отдельными контрактами, параметрами, типами портов и тестами.
4. Time Zone / OTP / OSS и интеграция с Time Manager.
5. Расширение Loop Module и полноценная проверка PID/alarms/manual/reschedule.
6. Полный Scheduler Manager: CRUD, редактирование сетки, Calendar Manager, runtime journal и safe command arbitration.
7. Импорт/экспорт Trend schedule data только после проверки формата на реальных эталонных файлах.

## 7. Статус DEV193

**Частично завершено; не принимать как Trend parity release.** DEV193 исправляет связь FBD SCHEDULE ↔ Core Scheduler и добавляет регрессионные тесты. Остальной список — подтверждённые пробелы, которые нельзя скрывать за цифрой «29 блоков». До успешного CI и выполнения очереди выше готовность не подтверждена.

Дополнительный FBD типовой пробел: Core Scheduler допускает STRING/ENUM, но текущая палитра не содержит отдельного `STRING_OUTPUT`/универсального output sink. Такие значения могут быть прочитаны и показаны в Scheduler Manager, но полноценная сквозная FBD-цепочка до выходного sink требует отдельного блока и тестов. При отсутствии `schedule_value_type` у старого блока UI теперь показывает неизвестный тип порта, а не угадывает BOOL.


## DEV194 — дополнительный выход Trend TIME

В Trend IQ3 TIME module среди выходов есть `UTC Offset`. AVIC TIME ранее имел 21 выход и не предоставлял явный offset. DEV194 добавляет числовой `UTC_OFFSET`, вычисляемый из station timezone через ZoneInfo. Регрессионный тест проверяет Europe/Moscow на фиксированном UTC timestamp (UTC+3).

Локальная FBD Studio simulation TIME теперь читает station time/timezone через Core API и рассчитывает календарные поля/UTC offset в часовом поясе станции; браузерный timezone не используется. При недоступности Core station time блок получает TIME_NOT_AVAILABLE вместо перехода на системное время браузера.

TIME теперь имеет 22 выхода в AVIC: 21 ранее существовавший + UTC_OFFSET. Это покрывает перечисленный в руководстве Trend TIME output, но не заявляет полного паритета по настройке Time Master / DST input parameters и распространению времени на устройства.
