# ADR-001 — Разделение Point Definition, Point State и Sample

Статус: **PROPOSED — обязательное архитектурное решение до реализации масштабируемого Point Runtime**  
Дата: 27.11.2026  
Область: AVIC Core, AVIC Edge Runtime, драйверы Python/Rust, FBD, HMI, Alarm Manager, Historian, API и Central/Edge.

## 1. Контекст и проблема

Текущий `PointRuntimeService.publish()` загружает объект Point из инженерного SQLite Repository, валидирует sample, изменяет runtime-поля объекта и сохраняет его обратно на каждое принятое измерение. В том же объекте смешаны инженерное определение точки и её текущее значение. Один общий lock защищает чтение, проверку и запись.

Это создаёт неправильную зависимость: частота полевых измерений определяет нагрузку на инженерный Object Repository. При росте количества точек, частоты опроса и числа станций это связывает Driver Runtime, FBD, HMI, Alarms и Engineering CRUD через одну транзакционную границу.

**Решение:** инженерное определение точки, текущее оперативное состояние и поток измерений — три разных контракта и три разных ответственности.

## 2. Термины и владельцы

| Сущность | Назначение | Единственный владелец записи |
|---|---|---|
| Point Definition | Инженерная конфигурация, идентичность, тип, единицы, адрес/источник, принадлежность станции, права и настройки | Engineering/Object Service |
| Point State | Последнее принятое оперативное значение и актуальное качество | Station Point Runtime |
| Point Sample | Неизменяемый факт измерения/изменения состояния с метаданными источника и времени | Ingestion Pipeline; далее потребляется Historian/Alarm/FBD |
| Historical Record | Долговременный ряд значений, архивные интервалы, агрегаты и retention | Historian |
| Point View/Projection | Представление для HMI/API/аналитики, не являющееся источником истины | Проекция соответствующего потребителя |

Ни HMI, ни Historian, ни FBD, ни API не изменяют Point Definition или Point State напрямую. Они используют публичные контракты соответствующих сервисов.

## 3. Point Definition

Point Definition содержит только конфигурацию:
- `point_id` — стабильный UUID, не меняется при переименовании;
- `station_id`, `device_id`, `driver_instance_id` — явная область владения;
- имя, описание, тип данных, единицы, направление и допустимый диапазон;
- адрес протокола/объекта и параметры декодирования;
- источник/происхождение, vendor/model только из подтверждённых данных;
- инженерные настройки: deadband, polling/COV policy, alarm references, historian policy;
- `definition_revision` и статус конфигурации.

Определение изменяется только через Engineering Lifecycle / Configuration Publish. Runtime sample не увеличивает `definition_revision` и не записывает объект через Object Repository.

Изменение адреса, типа, единиц, владельца или направления — конфигурационное изменение с валидацией и публикацией, а не обновление состояния.

## 4. Point Sample — неизменяемый контракт

Минимальный логический envelope:

| Поле | Тип/смысл |
|---|---|
| `event_id` | UUID события для идемпотентности |
| `point_id` | Стабильная идентичность точки |
| `station_id` | Станция-источник |
| `value` | Типизированное значение |
| `quality` | Canonical Quality enum |
| `source_timestamp` | Время, заявленное устройством/драйвером |
| `received_at` | Время приёма станцией |
| `processed_at` | Время принятия Runtime |
| `sequence` | Монотонный sequence в области конкретного источника/точки |
| `source_id` | Driver/device/virtual producer |
| `runtime_epoch` | Эпоха владельца Runtime для fencing |
| `definition_revision` | Версия определения, по которой sample проверен |
| `clock_quality` | Достоверность/состояние часов источника |
| `diagnostics` | Необязательные коды протокольной диагностики |

Sample после принятия не переписывается. Исправление или уточнение создаёт новое событие с явной связью с исходным, если это необходимо.

## 5. Point State

Point State — оперативный снимок последнего принятого состояния:
- `point_id`, `station_id`;
- последнее значение и quality;
- source/receive/process timestamps;
- sequence, runtime_epoch и definition_revision;
- признаки stale/disabled вычисляются по определённым правилам, а не угадываются UI.

Point State не является архивом и не заменяет Historian. Состояние может быть восстановлено из последнего checkpoint и журнала принятых событий; после перезапуска источник может быть помечен STALE/UNCERTAIN до получения нового валидного sample. Нельзя объявлять старое сохранённое значение свежим только потому, что оно восстановлено из БД.

## 6. Ingestion Pipeline и порядок обработки

1. Driver Adapter или внутренний producer отправляет Sample через единый Point Ingestion API.
2. Pipeline проверяет аутентичность/владение источника, station scope, существование Point Definition, направление, тип и диапазон значения.
3. Проверяется `definition_revision`, `runtime_epoch`, sequence и временная политика.
4. Неизвестное или недопустимое качество не преобразуется в GOOD.
5. Out-of-order sample не заменяет более новое состояние. Политика допуска для архивирования отдельно определяется Historian; отклонение/карантин фиксируется диагностикой.
6. Принятое событие обновляет Point State и durable outbox в одной локальной транзакционной границе.
7. Подписчики получают событие асинхронно и идемпотентно. Ошибка одного потребителя не откатывает уже принятое измерение и не блокирует других.
8. Historian, Alarm Manager, FBD и аналитика подтверждают собственную обработку по event_id/offset. Повторная доставка безопасна.

## 7. Хранилище и производительность

- Engineering Object Repository не используется для записи runtime samples.
- Для каждой станции существует отдельная логическая область Point State и outbox; границы изоляции станции обязательны.
- Начальный backend может использовать локальное транзакционное хранилище с WAL и пакетной записью, но потребители зависят от интерфейса Store, а не от SQLite API.
- Горячий read path обслуживается из state cache; массовый snapshot не должен выполнять N последовательных чтений инженерных сущностей.
- Ingestion имеет bounded memory queue, явные лимиты, метрики backlog/latency/drops и backpressure к polling producers.
- Нельзя молча терять quality transitions, alarm-relevant samples или события смены режима. При исчерпании ресурсов система должна перейти в явный деградированный режим и сообщить об этом.
- Пакетная запись и flush policy должны иметь документированные пределы потери при аварийном отключении питания.
- Historian хранит историю и агрегаты по своей политике retention; Point State хранит только оперативный снимок и необходимый outbox/checkpoint.

## 8. Fencing, изоляция и отказоустойчивость

- Один активный writer на Point State области станции.
- Каждая активация Runtime получает монотонную `runtime_epoch`/fencing token; старый процесс после перезапуска/переключения не может публиковать значения.
- Source identity и station ownership обязательны; пустой owner не является wildcard.
- Потеря Central не останавливает локальный Station Runtime.
- Потеря Historian не блокирует безопасное обновление Point State, пока durable outbox не достигнет установленного дискового лимита; далее включается явная backpressure/degraded policy.
- Повторная доставка outbox и восстановление после аварии идемпотентны.
- Разделение/слияние станций и перенос точек выполняются через versioned deployment/transfer, а не произвольное копирование записей.

## 9. Потребители и запреты

- **Drivers (Python/Rust):** публикуют Sample; не пишут в Object Repository.
- **FBD:** читает Point State через API; виртуальные выходы публикуются тем же контрактом с типом producer=FBD и station scope.
- **HMI/Graphics/Web Pages:** только читают state snapshot/subscribe; не являются владельцем значения.
- **Alarm Manager:** подписывается на принятые samples/state transitions; хранит alarm lifecycle отдельно.
- **Historian:** потребляет durable stream/outbox и владеет только историческими рядами.
- **Analytics/AI:** строят проекции/рекомендации; AI не может напрямую изменять Point State или отправлять field command.
- **API/SDK/Plugins:** используют стабильные публичные интерфейсы; не получают прямой доступ к внутренним таблицам/репозиториям.

## 10. Совместимость и миграция

1. Существующие `Point.value/quality/timestamp` считаются legacy runtime fields до завершения миграции.
2. Вводятся Point State API и Store рядом с текущим сервисом; прежний API временно делегирует новому.
3. Однократная миграция извлекает текущие значения в state store, сохраняя Point Definition и UUID.
4. Сверяются количество точек, типы, значения, quality, timestamp, station/device/driver ownership.
5. На переходном этапе допускается dual-read для сравнения, но не dual-write без формально определённого reconciliation.
6. Удаление runtime-полей из Point Definition — отдельная миграция после проверки всех импортов, transfer formats, SDK и тестовых fixtures.
7. Версия контракта Sample/State должна поддерживать forward/backward compatibility и явную схему миграции.

## 11. Обязательные acceptance tests

### Контракт и корректность
- стабильность point_id при переименовании;
- невозможность изменения Point Definition через publish sample;
- валидация типов, диапазонов, направления, driver/device/station ownership;
- unknown quality не становится GOOD;
- отсутствие timezone в source timestamp корректно обрабатывается согласно политике;
- out-of-order и duplicate event_id не откатывают state;
- sequence и runtime_epoch fencing блокируют устаревшего producer.

### Надёжность
- crash до/после state+outbox commit;
- повторная доставка outbox;
- падение одного subscriber не блокирует другие;
- восстановление после рестарта и перевод quality в STALE до нового подтверждения;
- заполнение очереди и диска вызывает backpressure/degraded state, а не скрытую потерю;
- потеря Central не останавливает автономную станцию.

### Масштаб и изоляция
- 1k / 5k / 10k points с заданными профилями частоты и размера payload;
- параллельная публикация из нескольких drivers;
- разные станции не блокируют друг друга;
- read snapshot не выполняет N запросов к Object Repository;
- p50/p95/p99 ingestion latency, backlog, CPU, memory, disk writes и recovery time фиксируются в отчёте;
- результаты на Linux и Windows, включая Edge Linux profile.

### Интеграция
- FBD, Graphics/HMI, Alarm Manager и Historian используют только публичные Point State/Sample contracts;
- запрет прямой записи runtime sample в Object Repository проверяется архитектурным тестом;
- Python и Rust producer дают идентичную семантику sample/quality/timestamp;
- transfer/publish не нарушает station ownership и fencing.

## 12. Критерий принятия ADR

ADR может получить статус **ACCEPTED** только после:
1. согласования canonical Quality/Time semantics (связанные ADR);
2. определения точных интерфейсов и ошибок Point State API;
3. выбора первого backend и crash-consistency guarantees;
4. прототипа ingestion + durable outbox с интеграционными тестами;
5. подтверждения нагрузочными испытаниями на Linux и Windows;
6. проверки миграции старых Point entities и всех потребителей.

До этого документ задаёт обязательное направление проектирования, но не означает, что реализация завершена.

## 13. Проверка по трём архитектурным ориентирам

- **Niagara:** сохраняем единый объектный граф, устойчивую идентичность объектов, typed points и подписки; не копируем смешение инженерного объекта с high-frequency persistence.
- **Trend IQVision:** сохраняем инженерную практичность — понятную точку, её значение, качество, источник, графики и диагностику в одном рабочем сценарии; реализация не должна заставлять инженера управлять внутренними БД.
- **Siemens Desigo CC:** учитываем распределённую работу, системную интеграцию, масштабирование, серверные интерфейсы и автономность нижнего уровня. Point State должен быть станционным и работать без постоянного Central.
- **AVIC:** один контракт для Python/Rust, Core/Edge, FBD/HMI/Alarms/Historian/API; строгая изоляция станции, отсутствие скрытой потери данных и доказуемая производительность.

## 14. Связанные решения

- ADR-002 — Station Runtime, deployment bundle и Edge autonomy.
- ADR-003 — Canonical Quality, Time and Sample ordering.
- ADR-004 — Command arbitration и физические записи.
- ADR-005 — Data ownership, outbox/inbox, backup/restore и cross-store consistency.
