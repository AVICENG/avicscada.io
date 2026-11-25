# Карта функционального соответствия IQVISION → AVIC

**Исходный материал:** IQVISION Configuration Manual TE201382, Issue 7, 22-Nov-2019; IQVISION User Manual; Point Database Manager Manual; IQVISION 2.30 package; предоставленный архив конфигурации Niagara. Документы описывают продукт IQVISION на Niagara Framework. Карта фиксирует именно функциональные процессы, а не копирование исходного кода или защищённых компонентов.

**Срез:** DEV52 (раздел 5 User Manual доработан частично). UI smoke проверяет только явно перечисленные сценарии в `BUILD_051_RU.md`; полный Windows acceptance ещё не выполнен.

**Статусы:**
- `Есть частично` — в DEV49 присутствует ограниченная реализация, но нет полного сценария IQVISION.
- `Нет` — реализация не обнаружена в коде/проверенных API.
- `Требует приёмки` — код/страницы есть, но сквозной сценарий в браузере Windows не подтверждён.

| Область IQVISION | Что требуется воспроизвести | Фактическое состояние DEV52 после проверки кода и локального Chromium smoke | Разрыв / критерий готовности |
|---|---|---|---|
| Workbench shell | Nav Tree, Palette, Locator Bar, View Pane, View Changer, tabs, инспектор | Есть частично: единая оболочка `index.html`, дерево, вкладки, инспектор; DEV51 добавил Locator Bar, навигацию назад/вперёд, View Changer и переключаемую стартовую Palette | Нужны полная модель component views, path parser/autocomplete, реальная Palette с drag/drop, bindings и сквозные object workflows |
| Platform / Station | Запуск платформы, создание/открытие станции, конфигурация и жизненный цикл | Есть частично: Project/Station API, runtime и CLI | Нет полноценного Platform Administration, управления сервисами и процесса station start/stop/restart из UI |
| Навигационное дерево | Иерархия, фильтр, контекстные действия, открытие объектов и view | Есть частично: tree APIs, project/station/device tree; DEV51 добавил контекстные меню для статических разделов и текущих типов инженерных объектов | Нужна полная матрица команд/представлений IQVISION, права на каждую команду, dependency preview и открытие каждого типа в его полноценном редакторе |
| Palette | TrendN4, Alarm, Schedule, History, KitPx; поиск, добавление компонентов | Есть стартовая панель Palette DEV51 с категориями и фильтром; фактическая вставка компонентов не реализована | Нужны реальные категории, drag/drop, typed ports/bindings, версии библиотек, валидатор и документация |
| Points List View (IQVISION User Manual §5 / Configuration Manual §19) | Режимы, сортировка, группы, фильтр статуса/метки, избранное, adjust/override, CSV, history, schedule, свойства и setup options | DEV52: persistence избранного, фильтр, сортировка, пагинация, CSV, переход к истории; adjust/override намеренно не включены | Нет live/engineering modes, группировки, adjustment/override с audit и interlocks, schedule editing из списка, настроек режима; не считать §5 закрытым |
| Third-party drivers | Установка/конфигурация драйверов, добавление точек | Есть частично: BACnet/IP, Modbus TCP, driver catalog | Нет полноценного Driver Manager, жизненного цикла драйверов, пакетов/версий и безопасного подключения |
| Trend discovery | Добавить Trend System, Discovery Wizard, импорт точек | Есть частично: Trend IQ3 integration contracts | Нет полного мастера Trend System/Module Discovery и Windows acceptance с реальным контроллером |
| BACnet | Настройка сети, Who-Is/I-Am, инспекция, импорт объектов/точек | Есть частично: BACnet/IP discovery, property reader, device import | Нужны устойчивые discovery jobs, pagination, фильтры, повторный опрос, импорт/сопоставление, безопасные ограничения |
| TONN / TONN8 | Добавление TONN, allowed hosts, импорт точек | Не обнаружено | Отдельный драйвер/адаптер и сценарии подключения; не подменять BACnet-поддержкой |
| Point Database Manager | Поиск неиспользуемых точек, критерии, ссылки из PX/Wiresheet/alarms/history, preview, backup | Есть частично: Point Manager API и явный DependencyService | Автоматический сбор ссылок из всех редакторов не реализован; нужен безопасный полный scan и отчёт о неиспользуемых точках |
| PX Pages | Папки, создание страниц, шаблон, размер/фон, элементы, ссылки, dashboard | Есть частично: Web Pages CRUD и отдельная graphics страница | Нет полноценного единого PX редактора, layout canvas, widget tree, привязок, preview и runtime rendering |
| PX widgets | Static text/image, dynamic text, animated image, slider, buttons, links, history graph, schedule | Есть частично: graphics models/service | Нет полноценной палитры виджетов и исполняемой системы binding/action/animation |
| Graphics palettes | HVAC символы, изображения, Easy Widgets, Easy Palette Builder | Есть частично: SVG assets и graphics API | Нужны каталоги/метаданные символов, варианты состояний, импорт/экспорт и редактор палитры |
| Relativisation | Повторное использование общей PX-страницы с относительными bindings | Не обнаружено | Нужны шаблоны и контекстная подстановка точки/устройства/станции с проверкой типов |
| Scheduler | Boolean/Numeric/Enum/String; недельная сетка, несколько событий в день, copy day, M-F | Есть частично: Schedule API, weekly events, copy day | Нужен полноценный графический редактор 24h-grid с drag/resize/move, валидацией и undo/redo |
| Master Schedule | Управление множеством расписаний, импорт/экспорт, разрыв/восстановление связей | Есть частично: расписание и привязки к точкам | Нет законченного Master Schedule и управления группой расписаний |
| Calendar Schedule | Календарь, исключения, диапазон дат, приоритет и экспорт | Есть частично: special events | Нужны календарный UI, повторения/диапазоны, экспорт/импорт и конфликт-резолвер |
| Execution Time | Отложенное применение расписания/ручной экспорт | Не подтверждено | Нужен исполнитель расписаний, безопасное применение, аудит и simulation/live separation |
| Time Management | Часовой пояс, NTP, синхронизация устройств | Есть частично: station policy и device permission | Нет реального sync adapter; запрет записи без явного разрешения должен сохраняться |
| Alarm handling | Trend/BACnet alarms, listener, classes, priorities, filters, recipients, email | Есть частично: Alarm API, acknowledgement, transitions, history | Нет Alarm Classes, modification filters, recipients/routing engine, network alarm ingestion и alarm sounds |
| Alarm Console | Сортировка, фильтры, acknowledge, комментарии, история | Есть частично: Console UI/API | Нужны массовые операции, фильтры по классам/источнику, shelve/suppress если требуется, сквозной UX |
| Alarm Portal | Межстанционный просмотр/подтверждение аварий | Не обнаружено | Нужны федерация станций, область видимости, права и аудит действий |
| Event journal | Операционные события отдельно от аварий и аудита | Есть частично: EventService + UI | Нужны фильтры/экспорт/retention и связка всех компонентов через единый event contract |
| History archive | On-change/interval, quality, archive, graph/table, retention | Есть частично: HistoryService, query/rollup | Нет полноценного collector/archiver, конфигурирования history extensions, retention policies и chart UI parity |
| History export | SQL/CSV export | Не обнаружено законченного export workflow | Нужны экспорт по диапазону, расписание выгрузки, контроль доступа и аудит |
| Security | Пользователи, PIN levels, категории, зоны, роли/права | Есть частично: RBAC/security services, UI role selector не является защитой | Нужны полноценные user/group management UI, server-side enforcement на всех endpoints, secured zones/points |
| E-Signature | Customer, reason sets, secure zones, Level 2 users, secure alarms/histories, approvals | Не обнаружен полный workflow | Нужны двухстороннее подтверждение, причины, неизменяемая запись, повторная аутентификация; не заявлять Part 11 compliance без IQ/OQ/PQ |
| Certificate management | Сертификаты, trust store, TLS identity | Не обнаружено законченного UI | Нужны выпуск/импорт/ротация/отзыв, проверка цепочек и предупреждения об истечении |
| Application Director | Start/stop/restart station, сервисный статус | Есть частично: CLI health/init | Нужен UI управления процессами, restart policy, журналы запуска и права администратора |
| Backup / disaster recovery | Резервное копирование станции/проектов и восстановление | Есть частично: project backup/config services | Нужны сквозные backup/restore, проверка целостности, расписание и recovery drill |
| SNMP | Driver, recipient, MIB export | Не обнаружено | Необходимо добавить отдельный SNMP scope или явно зафиксировать как исключение только после решения владельца продукта |
| Analytics | Tagging, aggregations, missing data | Есть частично: AnalyticsService и API | Нет полной инженерной библиотеки алгоритмов, конфигурации аналитики, визуализации и правил оповещения |

## Порядок реализации для достижения функционального сходства

1. **Единая Workbench-модель:** типы объектов, дерево, locator, tabs, palette, view changer, инспектор, контекстные действия.
2. **Инженерная база:** Driver Manager, Discovery Wizard, Point Database Manager, автоматический Dependency Scanner.
3. **Графика:** полноценный PX Editor, palette builder, typed bindings, runtime rendering, шаблоны/relativisation.
4. **Логика:** Wiresheet/FBD, блоки, типизированные связи, simulation, онлайн-мониторинг, безопасная публикация.
5. **Расписания:** недельная сетка, Calendar, Master Schedule, Execution Time, импорт/экспорт и приоритет источников.
6. **Аварии/события/история:** классы и фильтры аварий, routing, Alarm Portal, History Archive и экспорт.
7. **Безопасность и платформа:** пользователи/категории/зоны, e-signature workflow, сертификаты, Application Director, backup/restore.
8. **Сквозная приёмка:** Windows install, запуск, браузер, реальные BACnet/Modbus устройства, отказ сети, восстановление, роли и аудит.

## Принцип приёмки

Функция считается реализованной только если есть: (1) модель/сервис с сохранением данных, (2) API/права доступа, (3) рабочий интерфейс и сквозной сценарий, (4) негативные и граничные тесты, (5) русская инструкция инженера/администратора. Наличие пункта меню, каталожной карточки, контракта или тестового заглушечного объекта не является реализацией.

## DEV56 — сквозной контроль инженерного маршрута (§4; связанные §8–10)

Добавлен `EngineeringWorkflowService`, API `GET /api/stations/{station_id}/engineering-workflow` и UI-страница «Пусконаладка → Инженерный маршрут станции». Проверяются реальные записи пяти этапов: сеть/каналы, драйверы/устройства, точки, FBD, PX-мнемосхемы. Проверка учитывает станционную принадлежность и сообщает о потерянной связи драйвера, неподдерживаемом режиме/состоянии, отсутствии интерфейса или связи протокольного канала с физической сетью.

**Статус §4:** теперь есть диагностический сквозной маршрут и список пробелов, но нет полноценного управляющего мастера с автоматизированными шагами discovery/import, commissioning, sign-off и отчётами. Раздел остаётся частично закрытым.

**Статус §8:** Trend IQ3 остаётся частичной read-only интеграцией. Полноценный Trend System/Module Discovery, импорт/повторное подключение и аппаратная приёмка не выполнены.

**Статус §9:** TONN/TONN8 адаптер не реализован. BACnet не подменяет TONN.

**Статус §10:** BACnet/IP и Modbus TCP foundations остаются частичными. DEV56 добавляет проверку связности объектов и режима read-only, но не реализует полный Driver Manager, установку/обновление/подпись пакетов, Driver SDK и lifecycle. Ни один драйвер не стартует автоматически.

Readiness `100%` в API означает только наличие проверяемых инженерных артефактов в пяти стадиях. `publish_ready` остаётся `false`; это не commissioning acceptance и не разрешение на запись в OT.

## DEV57 — уточнение приоритетов и Driver Manager foundation

Владелец продукта подтвердил, что полная интеграция Trend не является обязательной целью. Trend IQ3 сохраняется как необязательный интеграционный профиль; разработка Trend Site migration/discovery не должна блокировать независимые сценарии AVIC.

TONN/TONN8 рассматривается как архитектурный ориентир для будущих собственных Linux-контроллеров AVIC. Это не означает поддержку TONN-протокола. Требования к Linux Controller Agent и northbound-протоколу описаны в `TONN_LINUX_CONTROLLER_DIRECTION_RU.md`.

DEV57 добавляет persistent Driver Manager foundation: каталог, создание экземпляров в станции, сохранение конфигурации, остановленное состояние по умолчанию, запрет секретов в открытом config и read-only API. Новые экземпляры не запускают polling, discovery или полевой I/O. §10 остаётся частичным; Driver SDK, пакетная установка/подпись, discovery jobs и runtime отсутствуют.

## DEV62 — Integrated Engineering Workflows (19.11.2026)

DEV62 consolidates the engineering capabilities already present in DEV57 and earlier builds and adds persistent Discovery history, non-mutating point-import preview, three FBD blocks (LIMIT/SCALE/COMPARE_LT) and a Platform Status API.

| Глава Configuration Manual | Текущий статус AVIC | Уточнение приоритета |
|---|---|---|
| §2 About IQVISION | Частично | Workbench, дерево, редакторы и сервисы есть; полный Platform Manager и runtime lifecycle ещё не закрыты |
| §3 Securing IQVISION | Частично | Security primitives есть; обязательная интеграция RBAC на каждом API ещё не завершена |
| §4 Engineering Procedure | Частично | Инженерные этапы связаны, но полный wizard/commissioning sign-off и acceptance не завершены |
| §5 Install IQVISION | Частично | CLI/package есть; Windows installer/service/upgrade/rollback не завершены |
| §6 License IQVISION | Частично | AVIC Host-ID/licensing foundation есть; полноценная эксплуатационная активация и transfer workflow не завершены |
| §7 Initial Setup | Частично | Project/Station и CLI init есть; полноценный first-run wizard не завершён |
| §8 Build a Trend Site | Не является обязательной целью | Trend migration/system discovery отложены; AVIC строится как самостоятельная платформа, общие сетевые функции развиваются независимо |
| §9 Connect to TONNs | Запланировано | TONN/TONN8 не реализуется сейчас; сохранено направление будущего AVIC Linux Controller Agent |
| §10 Connect to Third Party Systems | Частично | BACnet/IP, Modbus TCP, Discovery, inspect, import preview/import и Driver Manager foundation; полный SDK/package lifecycle и production adapters не закрыты |
| §11 Configure Time Schedule Control | Частично | Сервис/API расписаний есть; полный визуальный календарь и production runtime execution не закрыты |
| §12 Configure Alarm Handling | Частично | Состояния, подтверждения, заметки, история переходов; полный operator portal, routing/escalation и notification delivery не закрыты |
| §13 Create Schematics (PX Pages) | Частично | Graphics editor, HVAC symbols, point/FBD bindings; полный PX widget set, custom SVG library и runtime widgets не закрыты |
| §14 Set Up IQVISION Users | Частично | Auth/RBAC/MFA primitives есть; полный UI управления пользователями и повсеместное enforcement не закрыты |
| §15 Backup and Restore | Частично | Archive, integrity preview и restore primitives; полный DR UI/acceptance не закрыты |
| §16 Using IQVISION | Частично | Добавлена русская сквозная инструкция DEV62; полное руководство оператора и все сценарии ещё не завершены |
| §17 Access IQVISION | Частично | Локальный Workbench и security foundations; полноценный production login/session integration не закрыты |
| §18 Use IQVISION | Частично | Инженерные редакторы и сервисы есть; production runtime/operator command lifecycle не закрыт |
| §19 Points List View | Частично | Point inventory, фильтрация/представления и import preview; полный operator override/edit workflow не закрыт |
| §20 Viewing Alarms | Частично | Alarm API/state machine/history есть; полноценный операторский Alarm Portal и role enforcement не закрыты |

**Правило:** §8 Trend не блокирует готовность самостоятельной AVIC. §9 TONN — стратегическое направление для будущего Linux Agent, но до реализации протокола/агента не считается закрытой главой. Главы с частичным статусом нельзя считать завершёнными только на основании API-контракта или тестового шаблона.
