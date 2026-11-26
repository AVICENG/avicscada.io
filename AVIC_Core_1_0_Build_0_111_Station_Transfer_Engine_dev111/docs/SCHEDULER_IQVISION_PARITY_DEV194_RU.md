# AVIC Scheduler ↔ Trend IQVISION — parity audit DEV194

Дата: 26.11.2026  
Эталонные учебные материалы в библиотеке проекта:
- `IQVision Module - 6 Time Schedules v1.2.pptx`
- `IQVision Module - 7 Master Time Schedules v1.3.pptx`
- `7 BACnet V3 IQVISION Schedules.pptx`

## 1. Не путать три разных механизма

1. **IQVISION Supervisor Time Schedule** — Niagara component с Boolean/Numeric/Enum/Digital schedule, weekly time scheme и special events. Это главный ориентир для AVIC Scheduler Manager.
2. **Trend IQ3 Schedule Module H** — отдельный FBD/strategy модуль контроллера с аналоговыми входами Manual Select, Non-Occupied, Warm-Up, Occupied, Cool-Down, Manual Level и выбором OTP/OSS. Это не Supervisor Time Schedule.
3. **AVIC FBD SCHEDULE** в DEV193/194 — ссылка на Core Scheduler object станции. Это consumer расписания, но не Trend IQ3 H и пока не полный эквивалент IQVISION Niagara component.

## 2. Возможности IQVISION из учебного курса

### 2.1 Time Schedule
- Schedule component можно разместить в любой части базы, но рекомендуется центральное управление.
- Boolean schedule: неделя Sunday–Saturday; интервалы расположены сверху вниз.
- Special Events: исключения с собственными time schemes; для замещения полного дня нужно явно задавать false-периоды до/после активного интервала.
- Properties: facets/text representation для состояния и effective period.
- Summary tab позволяет проверить фактическое действие special event на выбранную дату.
- Типы Schedule включают Boolean, Numeric, Enum и Digital.

### 2.2 Calendar Schedule
- Отдельный Calendar Schedule хранит календарные исключения централизованно.
- Calendar Schedule не хранит недельную/суточную time scheme: временные интервалы задаются внутри целевых Time Schedules.
- Один Calendar Schedule можно связать с несколькими Time Schedules через Reference Special Event.
- Изменение общего календаря автоматически применяется ко всем связанным расписаниям.

### 2.3 Master Schedule Import / Export
- Import Manager обнаруживает/импортирует расписания; импортированные schedules read-only, но к ним можно добавлять local special events.
- Export Manager связывает Master Schedule / Calendar Schedule с расписаниями Trend и сторонних устройств.
- Учебный пример содержит несколько профилей: Time Scheme 1–4, Shutdown, Halfday, Allday и Calendar Schedules.
- Экспорт можно выполнить немедленно; execution time задаёт периодическую отправку (в курсе default 02:00 daily).
- Несколько экспортов можно выбрать и связать пакетно.

### 2.4 BACnet Schedule Manager
- Расписания BACnet B-BC обнаруживаются с устройства через BACnet Schedule Manager.
- При импорте IQVISION подбирает подходящий тип schedule.
- Для экспорта Supervisor schedule на controller schedule создаётся binding через BACnet Schedule Export Manager.
- Режимы отправки: Daily, Interval, Manual; расписание отправки настраивается по конкретным дням.
- Успешность отправки проверяется на web page контроллера.

## 3. AVIC Scheduler в DEV194

| Функция | Состояние AVIC |
|---|---|
| Boolean / Numeric / Enum / String values | Есть в Core Schedule Service |
| Weekly events | Есть |
| Special events / date exceptions | Есть |
| IANA timezone / DST through timezone database | Есть |
| Effective start/end | Есть |
| Temporary manual override | Есть |
| Current value / source / next change | Есть |
| Central Calendar Schedule entity | Нет |
| Reference Special Event linking many schedules to one calendar | Нет |
| Summary view by selected date | Частично; нет полноценного календарного аудита/preview |
| Facets / text state mapping | Частично; нет полноценной Niagara-style facets editor |
| Edit event in-place / drag / resize | Нет |
| Full schedule CRUD / revision-safe delete | Нет |
| Import Manager for discovered controller schedules | Нет |
| Imported read-only schedule with local exceptions | Нет |
| Master Schedule / Export Manager | Нет |
| Bulk binding of many schedules | Нет |
| BACnet Schedule Manager discovery | Нет |
| BACnet schedule import/export binding | Нет |
| Daily / Interval / Manual controller schedule synchronization | Нет |
| Per-target schedule sync calendar | Нет |
| Safe staged export with approval, read-back and rollback | Нет |

Текущая привязка Core schedule к point хранится как engineering intent only. Она не запускает запись в BACnet или иной контроллер.

## 4. Что нужно реализовать для полноценного паритета

### P0 — Schedule authoring
1. Недельная 7-дневная сетка с drag/resize и точным редактированием времени/значения.
2. Полноценные edit/delete для weekly/special events с optimistic concurrency и audit history.
3. Properties/Facets: enum state labels, text output, units, effective dates.
4. Summary/preview на произвольную дату с объяснением выбранного источника значения и приоритета.

### P1 — Calendar Schedule
1. Самостоятельная сущность Calendar Schedule.
2. Повторяющиеся ежегодные и многодневные события.
3. Reference Special Event с привязкой к календарю.
4. Один календарь — много расписаний; обновление календаря не должно копировать события в каждый schedule.
5. Версионирование, аудит изменений и отображение влияния на связанные schedules.

### P1 — Import Manager
1. BACnet device discovery для Schedule objects.
2. Определение BACnet Schedule / Calendar типизации и object identity.
3. Импорт как read-only source; локальные exceptions остаются отдельно.
4. Сопоставление чужого расписания с локальным Schedule без потери оригинальных значений.
5. Повторное обнаружение и diff изменений контроллера.

### P1 — Master Schedule Export Manager
1. Явная связь Master Schedule ↔ target schedule object.
2. Bulk binding нескольких target schedules.
3. Режимы Daily / Interval / Manual и разрешённые дни/время отправки.
4. Dry-run diff перед экспортом.
5. Approval, staged publish, read-back verification, retry/backoff, audit и rollback.
6. Разрешение на запись задаётся отдельно для каждого устройства и протокола; без разрешения только read-only.

### P2 — Runtime
1. Отдельный Scheduler Runtime и execution journal.
2. Обнаружение пропущенных переходов после рестарта/потери связи.
3. Повторная оценка текущего значения без ложного импульса или небезопасного скачка.
4. Арбитраж с ручным override, interlocks, аварийными блокировками и другими источниками команд.

## 5. Приоритеты безопасности AVIC

- Никакой автоматической записи на контроллер только потому, что schedule point binding существует.
- Сначала импорт и read-only diff; экспорт отдельно разрешается оператором/инженером.
- Для BACnet нужны per-device permissions, target object identity, read-back и audit.
- Временный override обязан иметь actor, reason, expiry и историю.
- При невалидном timezone, неизвестном типе или конфликте событий schedule должен выдавать явную ошибку/quality, а не случайное значение.

## 6. Статус

DEV194 закрывает связь FBD Studio SCHEDULE ↔ Core Scheduler и station-time outputs. Он **не закрывает** IQVISION Scheduler parity. Главные отсутствующие элементы — Calendar Schedule references, Import Manager, Master Schedule Export Manager и BACnet schedule discovery/export.
