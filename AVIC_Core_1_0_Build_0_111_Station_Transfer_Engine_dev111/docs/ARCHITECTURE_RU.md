# AVIC Core 1.0 — Архитектурные решения DEV47

## Базовая позиция
AVIC — инженерная платформа, а не коллекция HTML-страниц. Доменная модель, службы Core, хранилища, API и Workbench должны иметь общие идентификаторы объектов и единые правила доступа/аудита.

## Слои
1. Domain / Contracts — инженерные объекты и типизированные контракты.
2. Repository — транзакционное хранение и optimistic concurrency.
3. Core Services — проекты, станции, сети, графика, Web Pages, аварии, расписания, аудит.
4. Runtime / Drivers — отдельные управляемые процессы; не запускаются автоматически при создании Core.
5. API — интерфейс взаимодействия с Core; проверки безопасности должны выполняться на сервере.
6. Unified Workbench — одна оболочка, дерево, вкладки, центральная рабочая область и инспектор.

## Что доказано в DEV47
- `CoreApplication` владеет `ScheduleService` и его жизненным циклом.
- Scheduler хранит данные отдельно от объектного репозитория в собственном SQLite-файле, но использует те же station/point IDs.
- Scheduler API подключён к FastAPI Workbench.
- UI Scheduler встроен в центральную область `/`, без отдельной страницы и iframe.
- Аудит операций Scheduler записывается в существующую hash-chain AuditService.

## Что пока не является единой моделью
- GraphicDocument и WebPage остаются отдельными типами документов.
- Службы Scheduler, Alarm и Web Pages используют специализированные хранилища; единой транзакции между всеми подсистемами пока нет.
- Event Manager и History Manager ещё не реализованы как законченные самостоятельные службы.
- Полноценный граф зависимостей между всеми объектами отсутствует.
- Production authentication/RBAC и пользовательские сессии не завершены; текущие mutating Workbench endpoints ограничены loopback/local origin.

## Правило архитектурного развития
Новая подсистема не должна заводить дублирующий объект, если уже существует канонический Project/Station/Device/Point ID. Межстанционные ссылки запрещены, если отдельный межстанционный контракт не разрешает их явно. Любая команда в OT-среду должна идти через отдельный Command Manager, а не напрямую из UI или Scheduler.

## DEV48: атомарные операции недельного Scheduler

Массовое копирование недельных событий выполняется на уровне ScheduleService, а не набором последовательных HTTP-запросов из браузера. Это обеспечивает атомарность замены целевых дней, единое увеличение revision и одну запись аудита. UI передаёт expected_revision; устаревший клиент не может молча перезаписать более новую конфигурацию.

Scheduler остаётся источником schedule intent. Он не является владельцем физической команды и не должен напрямую обращаться к BACnet/Modbus write path. Будущий Command Manager будет единственной точкой арбитража и исполнения команд.

## DEV49 — расширение по IQVISION parity

DEV49 добавляет отдельные persistent services: EventService, HistoryService, DependencyService, AnalyticsService, NotificationService, TimeManagementService и ModuleCatalog. AlarmService публикует переходы в operational event stream через durable outbox. Alarm History, Event Journal, Audit Chain и point History остаются разными потоками.

Workbench имеет 49 навигационных направлений и отдельный каталог из 37 подсистем. Каталог не маскирует незавершённость: статусы `implemented`, `partial`, `interface`, `planned` различаются и имеют описание источника требований.

Новые API mutations используют локальный development guard и пишут значимые действия в AuditService. Это не заменяет production RBAC. Notification outbox не имеет transport sender. Time Manager сохраняет timezone/NTP и explicit per-device sync permission, но не выполняет запись времени в контроллер.
