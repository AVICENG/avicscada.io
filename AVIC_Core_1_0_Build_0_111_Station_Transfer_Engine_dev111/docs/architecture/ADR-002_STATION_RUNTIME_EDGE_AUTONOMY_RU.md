# ADR-002 — Station Runtime, deployment bundle и автономность AVIC Edge

Статус: **PROPOSED**  
Дата: 27.11.2026  
Область: Station Runtime, Field Runtime, Core Workbench, AVIC Edge Runtime, AVIC Edge Manager, AVIC Edge Controller.

## 1. Цель

Станция AVIC должна быть самостоятельной исполняемой единицей. Центральная инженерная среда создаёт и проверяет конфигурацию, но после контролируемой публикации локальная станция должна выполнять разрешённую версию логики, расписаний и драйверов без постоянного подключения Workbench или Central.

AVIC Edge Runtime — программная среда исполнения на Linux/Windows.  
AVIC Edge Manager — центральное управление множеством Edge узлов и станций.  
AVIC Edge Controller — аппаратная платформа, на которой может работать Edge Runtime.

Эти термины не взаимозаменяемы. Наличие отдельного OS process не означает готовый Edge Runtime.

## 2. Текущее состояние

В текущем коде Field Runtime Process запускает отдельный процесс и поддерживает loopback TCP control/heartbeat. Agent отвечает на status/ping и maintenance_stop. Его собственный status сообщает:
- `active_strategies: 0`;
- `execution_engine_attached: false`;
- `capability_state: PROCESS_HOST_ONLY`.

FBDExecutionService сейчас является сервисом Core/Application и не присоединён к Field Runtime process. Документация DEV181 отдельно фиксирует, что persistent rediscovery/auth recovery после перезапуска Supervisor ещё не завершены.

Поэтому текущий результат — **Field Runtime Process Host Prototype**, не автономная станция и не Edge Controller.

## 3. Целевая граница компонентов

### Platform / Central Manager
- управление установкой, лицензиями, пользователями, сертификатами и обновлениями;
- каталог Edge nodes и их идентичности;
- проектирование, тестирование, Simulation и staged publish;
- управление версиями deployment bundles;
- глобальный мониторинг и агрегированные отчёты;
- доставка конфигураций и синхронизация опубликованных данных.

### Station Runtime (локальный владелец исполнения)
- локальный scheduler и execution cycle;
- FBD/logic runtime;
- локальные drivers и Point Ingestion/State;
- локальные Alarm Manager, Historian и Notification Manager;
- локальная политика доступа/команд и audit;
- локальный Web HMI/API;
- watchdog, health, recovery и disk/resource budget;
- выполнение последнего разрешённого deployment bundle без Central.

### Workbench / Engineering Host
- редакторы, дерево объектов, FBD/Graphics/Page Builder;
- конфигурационные use cases и валидация;
- не является владельцем полевого цикла и не должен останавливать Station Runtime при потере браузера/ASGI host.

## 4. Immutable Deployment Bundle

Каждая публикация создаёт подписанный неизменяемый bundle. Минимальное содержимое:
- `bundle_id`, `station_id`, `project_id`, `bundle_revision`;
- минимальная/максимальная совместимая версия Runtime и API contracts;
- FBD/logic graph и execution settings;
- bindings к Point Definition и внешним объектам;
- расписания, timezone policy references;
- driver instances, protocol settings и secrets references (не секреты в открытом виде);
- graphics/pages/assets и presentation bindings;
- alarm definitions, event rules и notification routing references;
- license capabilities/point usage manifest;
- dependency graph snapshot;
- checksums каждого payload, total manifest hash;
- publisher Principal, approval/change reference, created_at;
- rollback target и deployment policy.

Bundle подписывается ключом издателя, который проверяется на станции. SHA-256 без подписи доказывает целостность файла, но не авторство. Секреты доставляются отдельно через SecretStore/secure channel и привязываются к secret references.

## 5. Staged publish lifecycle

1. Draft — инженерная конфигурация редактируется, Runtime её не исполняет.
2. Validate — schema, object references, dependency graph, license, driver capabilities, station ownership и compatibility.
3. Simulate — логика выполняется в Simulation/Offline; физические записи запрещены.
4. Approve — отдельный разрешённый Principal подтверждает change set, если политика требует.
5. Package — формируется immutable signed bundle.
6. Stage — станция получает пакет во временную область, проверяет подпись, хэши, версии и свободные ресурсы.
7. Prepare — Runtime загружает конфигурацию в неактивный slot и выполняет preflight.
8. Activate — атомарное переключение на новую revision с generation increment.
9. Observe — health checks и проверка фактических сигналов/ошибок.
10. Commit — новая revision становится текущей.
11. Rollback — при failed health/explicit abort возвращается последняя подтверждённая revision.

Нельзя перезаписывать активную конфигурацию на месте. Нельзя объявлять публикацию успешной только потому, что ZIP загружен.

## 6. Автономность и reconnect

- Потеря Central/Workbench не останавливает локальную логику, драйверы, локальные alarms, scheduler и HMI.
- Станция сохраняет последнюю подтверждённую bundle revision и runtime state, необходимый для безопасного восстановления.
- Reconnect не перепубликует конфигурацию автоматически и не перезапускает активную логику без согласованного lifecycle.
- Central получает фактическую активную revision, локальный health, backlog и sequence/offset синхронизации.
- При расхождении версий Central и Edge требуется explicit conflict policy; последнее изменение не побеждает автоматически.
- Edge сохраняет локальные события и alarm transitions при потере связи; после восстановления отправляет их с event_id/sequence и идемпотентностью.
- Global Historian получает только опубликованные данные и не подменяет локальный Historian станции.

## 7. Runtime identity, IPC и fencing

- У каждого узла постоянный cryptographic node identity, созданный при provisioning.
- IPC между Supervisor и Station Runtime аутентифицирован; случайный loopback port и краткоживущий bootstrap token не являются производственным identity protocol.
- Все control messages имеют protocol_version, request_id, sequence, issued_at, expiry, sender identity, target station, bundle revision и runtime_epoch.
- Replay, expired commands и устаревшие epoch отклоняются.
- Supervisor рестартует без потери регистрации узла и не принимает чужой process как свой.
- Смена владельца/leader увеличивает fencing epoch; старый writer не может публиковать Point State, Alarm transitions или команды.

## 8. Process lifecycle и safety

- Station Runtime имеет независимые startup/shutdown/restart policies.
- Watchdog отличает медленный цикл, зависший процесс, потерю driver connection и потерю Central.
- Restart ограничен exponential backoff, rate limits и circuit breaker; бесконечный crash loop запрещён.
- Состояние оборудования при restart не угадывается: входы до свежего sample имеют stale/uncertain quality.
- Система не отправляет автоматический START/STOP только потому, что процесс перезапустился.
- Независимые safety functions остаются в сертифицированных PLC/контроллерах; AVIC не заменяет их.
- При ошибке ресурса/диска Runtime переходит в документированный degraded mode и сохраняет критические события.

## 9. Профили Edge

Один Runtime contract, разные hardware/resource profiles:
- Compact: целевой класс N100/N150, 16 GB RAM, SSD, dual Ethernet, isolated RS-485; ориентир до 1k points.
- Industrial: ориентир до 5k points.
- Performance: ориентир 10k+ points.

Это цели проектирования, не подтверждённые пределы. Реальные профили фиксируются отдельными benchmark/thermal/power/network/soak tests с точными sample rates, driver mix, logic cycle и retention.

Минимальный профиль Edge не должен требовать отдельной урезанной модели проекта: формат объектов, FBD, Graphics, drivers, bindings и API contracts общие; capability profile может запрещать конкретные модули по ресурсам/лицензии.

## 10. Acceptance tests

- Runtime исполняет bundle после полного отключения Central/Workbench.
- reboot устройства поднимает последнюю committed revision;
- частично загруженный/повреждённый/неподписанный bundle не активируется;
- несовместимая версия API/runtime блокирует publish;
- crash на каждом этапе Stage/Prepare/Activate/Commit восстанавливается без split-brain;
- rollback возвращает точную предыдущую revision;
- reconnect не дублирует alarms/history/notifications;
- повторная доставка событий идемпотентна;
- supervisor restart повторно обнаруживает и аутентифицирует тот же node identity;
- fencing блокирует старый процесс и устаревшие commands;
- отсутствие Central не останавливает локальную логику и scheduler;
- остановка Workbench не влияет на Station Runtime;
- resource exhaustion, disk full, CPU overload и driver flood дают bounded behavior;
- длительный soak test и power-loss test подтверждают recovery;
- профили 1k/5k/10k points подтверждаются отдельными измерениями, не extrapolation.

## 11. Проверка по трём системам

- **Niagara:** используем station-centric модель, локальные сервисы, driver/point graph и инженерный lifecycle.
- **Trend IQVision:** проверяем удобство загрузки проекта, FBD/графики, сервисных операций и восстановления для инженера.
- **Siemens Desigo CC:** берём как ориентир distributed client/server, mobile/central operations и интеграцию, но сохраняем автономность нижнего уровня; Siemens подчёркивает, что plant controllers продолжают автономную работу при потере management layer.
- **AVIC:** одна модель проекта и Runtime contracts для Core/Edge, offline autonomy, signed immutable deployment, fencing, local alarms/history/notifications и контролируемая синхронизация.

## 12. Критерий принятия

ADR принимается после появления реального attached execution engine, signed bundle, persistent node identity, authenticated IPC, restart/recovery/rollback, disconnected-operation acceptance tests и длительных испытаний на целевом Edge hardware.
