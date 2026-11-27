# ADR-003 — Canonical Quality, Time и порядок Sample

Статус: **PROPOSED**  
Дата: 27.11.2026  
Связанные решения: ADR-001 Point Definition / State / Sample; ADR-002 Station Runtime; ADR-005 Data Ownership.

## 1. Причина

В текущих слоях встречаются несовпадающие значения качества:
- Point domain: GOOD, UNCERTAIN, STALE, BAD_COMMUNICATION, BAD_CONFIGURATION, DISABLED;
- Historian: GOOD, UNCERTAIN, STALE, BAD, COMM_LOST, DISABLED;
- FBD exposed point: GOOD, UNCERTAIN, BAD, STALE, COMM_LOST, BAD_COMMUNICATION, BAD_CONFIGURATION;
- BACnet adapter отображает protocol status flags в свой PointQuality.

TimeManagementService сохраняет timezone/NTP policy и per-device permission для синхронизации, но сам по себе не является NTP client и не доказывает фактическую синхронизацию часов. PointRuntime принимает один timestamp и сравнивает его с сохранённым timestamp точки. В едином Sample contract нужно разделить время источника, приёма и обработки.

## 2. Каноническая модель качества

Quality описывает достоверность измерения, а не состояние аварии, доступность устройства или административный запрет.

| Quality | Семантика | Можно использовать для управления |
|---|---|---|
| GOOD | Sample прошёл валидацию, источник и временная политика допустимы | Да, если отдельно выполнены RBAC, interlocks, lease и command policy |
| UNCERTAIN | Значение есть, но достоверность ограничена или не подтверждена | Нет |
| BAD | Значение невалидно, повреждено или не может быть интерпретировано | Нет |
| STALE | Нет достаточно свежего sample в установленном freshness window | Нет |
| COMM_LOST | Потеря связи/источника; последнее значение может сохраняться, но не считается актуальным | Нет |
| CONFIGURATION_ERROR | Ошибка конфигурации точки/драйвера/декодирования | Нет |

Дополнительные состояния, которые не должны быть Quality:
- `enabled/out_of_service` — административное состояние точки;
- `alarm_state` — NORMAL/ACTIVE/ACKNOWLEDGED/RETURNED_TO_NORMAL;
- `device_connection_state` — ONLINE/DEGRADED/OFFLINE;
- `source_diagnostics` — protocol-specific status flags, error codes и детали;
- `freshness` — вычисляемая характеристика по timestamp и policy.

Маппинг от BACnet Status_Flags, Modbus transport errors и внутренних FBD ошибок должен быть явным и тестируемым. Неизвестное значение Quality всегда отклоняется или переводится в UNCERTAIN по явному compatibility rule; никогда не повышается до GOOD.

## 3. Модель времени

Для каждого Sample отдельно хранятся:
- `source_timestamp`: время, сообщённое контроллером/устройством, может отсутствовать;
- `received_at`: UTC время приёма локальной станцией;
- `processed_at`: UTC время принятия pipeline;
- `clock_quality`: SYNCED / HOLDOVER / UNSYNCED / UNKNOWN либо расширяемый эквивалент;
- `source_sequence`: счётчик источника, если протокол/драйвер его предоставляет;
- `runtime_epoch`: поколение владельца Station Runtime.

Правила:
1. UTC хранится в данных и API; timezone применяется только для отображения и календарных расписаний.
2. Монотонные часы используются для timeout, heartbeat, длительностей и freshness timer внутри процесса; wall-clock UTC не используется для измерения интервалов.
3. Устройство без доверенного clock sync может присылать source_timestamp, но pipeline не принимает его как единственный критерий порядка.
4. Время приёма станции всегда записывается отдельно от времени устройства.
5. Отрицательное/аномальное смещение, отсутствие timezone и резкий скачок часов не должны незаметно превращать sample в GOOD.
6. Коррекция часов не переписывает исторические source timestamps задним числом.
7. История хранит source_timestamp и received_at; запросы могут явно выбирать временную ось.

## 4. Порядок, дубликаты и запоздавшие данные

- Идемпотентность определяется event_id, а sequence применяется в scope конкретного source/point.
- Новый sample не принимается в текущее Point State, если он имеет устаревший runtime_epoch или definition_revision.
- При наличии надёжного sequence он является первичным порядковым сигналом; source_timestamp используется совместно с clock_quality и протокольной семантикой.
- При отсутствии sequence применяется документированная timestamp policy с ограниченным допустимым skew.
- Out-of-order sample не заменяет последнее оперативное состояние.
- Historian может принять поздний sample в архив, если его event_id уникален и исходное время достоверно; это не меняет Point State.
- Duplicate event_id безопасно возвращает прежний результат и не дублирует alarm/history side effects.

## 5. Time Manager: зона ответственности

Time Manager владеет:
- timezone и календарной политикой станции;
- NTP configuration, статусом источников времени и диагностикой синхронизации;
- разрешениями на clock-write к конкретному устройству;
- журналом кто, когда и почему разрешил/отозвал синхронизацию;
- расписанием и результатом разрешённой операции.

Time Manager не владеет:
- оперативным значением Point State;
- историческим временем измерения;
- монотонными часами ОС;
- неявным правом менять часы любого BACnet устройства.

Любая команда clock-write проходит тот же security/command boundary: authenticated Principal, station/device scope, explicit permission, audit, protocol acknowledgement и последующая проверка фактического состояния. Поле `approved_by` из HTTP payload не является доказательством личности.

## 6. Acceptance tests

- единый enum и round-trip mapping Python/Rust/History/FBD;
- неизвестный Quality не становится GOOD;
- GOOD/UNCERTAIN/BAD/STALE/COMM_LOST/CONFIGURATION_ERROR имеют одинаковую семантику во всех слоях;
- disabled/out-of-service не смешивается с quality;
- alarm state не смешивается с quality;
- source_timestamp, received_at и processed_at сохраняются независимо;
- freshness и timeout используют monotonic clock;
- DST/timezone changes не изменяют UTC sample timeline;
- source clock jump и UNSYNCED не создают ложный порядок;
- duplicate event_id и sequence повторно не создают history/alarm effects;
- stale runtime_epoch/definition_revision отклоняются;
- clock-write без explicit device permission отклоняется;
- clock-write permission нельзя выдать по подставному actor_id из тела запроса;
- NTP configured и NTP actually synchronized — разные состояния и UI статусы.

## 7. Проверка по трём системам

- **Niagara:** сохраняем явную работу с quality/status и временными метками точек, не смешивая качество с alarm lifecycle.
- **Trend IQVision:** инженер должен видеть значение, качество, источник и время без неоднозначных кодов; диагностика должна объяснять причину BAD/STALE/COMM_LOST.
- **Siemens Desigo CC:** учитываем системную синхронизацию времени, distributed operation, журналирование событий и корректную работу календарей/расписаний.
- **AVIC:** один контракт качества и времени для всех драйверов, Python/Rust, Station Runtime, Edge, Historian, FBD, Alarm Manager и API.

## 8. Критерий принятия

ADR принимается только после определения конкретного cross-language enum/schema, проверенных mapping tables для BACnet и Modbus, работающего time-sync executor с permission enforcement, интеграционных тестов и миграции существующих значений.
