# Карта репозитория AVIC SCADA

> **Назначение:** единая навигационная карта репозитория, веток и инженерных материалов.  
> **Срез инвентаризации:** 26 ноября 2026 года.  
> **Проверенная рабочая ветка:** `dev113-network-drivers`  
> **HEAD на момент составления:** `f3f2d5bc7fbda5d1467eb1228f2c33d3f09430a4`  
> **Важно:** это карта структуры Git-репозитория, а не заявление, что все перечисленные функции завершены или готовы к эксплуатации.

## 1. Быстрый переход

- [Текущая сборка AVIC Core (исходники)](AVIC_Core_1_0_Build_0_111_Station_Transfer_Engine_dev111/)
- [Документация AVIC Core](AVIC_Core_1_0_Build_0_111_Station_Transfer_Engine_dev111/docs/)
- [Журнал сборки DEV182](AVIC_Core_1_0_Build_0_111_Station_Transfer_Engine_dev111/docs/BUILD_TEST_LOG_DEV182_RU.md)
- [Аудит сетевых драйверов DEV113](AVIC_Core_1_0_Build_0_111_Station_Transfer_Engine_dev111/docs/NETWORK_DRIVERS_AUDIT_DEV113_RU.md)
- [Спецификация паритета FBD с Niagara и Trend](AVIC_Core_1_0_Build_0_111_Station_Transfer_Engine_dev111/docs/FBD_NIAGARA_TREND_PARITY_SPEC_DEV176_RU.md)
- [Архитектурная граница Field Runtime](AVIC_Core_1_0_Build_0_111_Station_Transfer_Engine_dev111/docs/architecture/FIELD_RUNTIME_BOUNDARY_RU.md)
- [Журнал тестов Field Runtime DEV181](AVIC_Core_1_0_Build_0_111_Station_Transfer_Engine_dev111/docs/BUILD_TEST_LOG_DEV181_RU.md)
- [Документация переноса Station](AVIC_Core_1_0_Build_0_111_Station_Transfer_Engine_dev111/docs/STATION_TRANSFER_DEV111_RU.md)
- [Документация менеджера драйверов](AVIC_Core_1_0_Build_0_111_Station_Transfer_Engine_dev111/docs/DRIVER_MANAGER_DEV57_RU.md)
- [Тесты проекта]( AVIC_Core_1_0_Build_0_111_Station_Transfer_Engine_dev111/tests/ )
- [Исходный пакет]( AVIC_Core_1_0_Build_0_111_Station_Transfer_Engine_dev111/avic_core/ )
- [Настройка проекта и зависимостей](AVIC_Core_1_0_Build_0_111_Station_Transfer_Engine_dev111/pyproject.toml)
- [CI workflow] (.github/workflows/avic-core-ci.yml)

## 2. Карта веток

На момент проверки в репозитории обнаружено **6 веток**.

| Ветка | HEAD | Роль и состояние |
|---|---|---|
| `main` | `8569598` | Основная ветка. Дерево содержит пакет AVIC Core; не использовать для повседневной разработки. |
| `dev112-station-transfer-reliability` | `ad44c29` | Стабильная базовая линия DEV112; база открытого PR №2. |
| `dev113-network-drivers` | `f3f2d5b` | Текущая рабочая ветка. DEV182; на 158 коммитов впереди DEV112. |
| `trend` | `b03a17e` | Справочный архив Trend SET / IQ и сопутствующих файлов. Не смешивать с исходниками AVIC. |
| `reference/niagara-materials-archive` | `872acd2` | Отдельная справочная ветка с каталогом `niagara/`. |
| `security/remove-niagara-from-current-tree` | `55f7e17` | Ветка удаления лицензированных Niagara-материалов из рабочего дерева. На момент снимка дерево **совпадает с main** (одинаковый tree SHA `6698702`). |

### Ссылки на деревья веток

- [main](https://github.com/AVICENG/avicscada.io/tree/main)
- [dev112-station-transfer-reliability](https://github.com/AVICENG/avicscada.io/tree/dev112-station-transfer-reliability)
- [dev113-network-drivers](https://github.com/AVICENG/avicscada.io/tree/dev113-network-drivers)
- [trend](https://github.com/AVICENG/avicscada.io/tree/trend)
- [reference/niagara-materials-archive](https://github.com/AVICENG/avicscada.io/tree/reference/niagara-materials-archive)
- [security/remove-niagara-from-current-tree](https://github.com/AVICENG/avicscada.io/tree/security/remove-niagara-from-current-tree)

### Правила работы с ветками

1. Разработка продолжается в `dev113-network-drivers`, пока отдельно не принято решение сменить рабочую ветку.
2. `main` и `dev112-station-transfer-reliability` не переписывать и не обновлять случайными экспериментальными изменениями.
3. `trend` и `reference/niagara-materials-archive` — только справочные источники. Не копировать в продукт лицензированные бинарные файлы или материалы без проверки прав.
4. Ветка `security/remove-niagara-from-current-tree` сохраняется как история/контрольная точка; её текущее дерево совпадает с `main`.
5. Перед каждым изменением: заново прочитать HEAD ветки, получить tree SHA именно этого HEAD, проверить PR и только затем создавать коммит.
6. Не использовать устаревший tree SHA при создании дерева: это может удалить файлы, добавленные после соответствующего снимка.
7. Не объединять PR и не удалять ветки без явного решения владельца проекта.

## 3. Текущий PR

[PR №2 — DEV113: Network drivers: Trend IP / BACnet / Modbus audit](https://github.com/AVICENG/avicscada.io/pull/2)

- Состояние на момент инвентаризации: **OPEN, DRAFT, не объединён**.
- База: `dev112-station-transfer-reliability`.
- Ветка изменений: `dev113-network-drivers`.
- В PR на момент проверки: 158 коммитов, 128 изменённых файлов.
- `main` не является базой этого PR и не изменяется данным документом.
- PR не объединять без отдельного разрешения владельца.

## 4. Структура текущей рабочей ветки

Корневой уровень `dev113-network-drivers`:

| Путь | Назначение |
|---|---|
| `.github/workflows/` | Автоматизация CI GitHub Actions. |
| `AVIC_Core_1_0_Build_0_111_Station_Transfer_Engine_dev111/` | Текущая папка исходного пакета AVIC Core. |
| `AVIC_Core_1_0_Build_0_111_Station_Transfer_Engine_dev111.zip` | Архивная копия пакета, размещённая в репозитории. |

Инвентаризация дерева DEV182: **921 запись Git** (файлы и каталоги); внутри папки пакета — 235 записей верхнего уровня и вложенных объектов в сумме по первому уровню подсчёта: `avic_core` — 228, `build` — 212, `docs` — 126, `tests` — 110, `dist` — 1, `tools` — 4; ещё 235 объектов расположены непосредственно в корне пакета. Числа описывают дерево на дату снимка и будут меняться.

### 4.1. Исходный код `avic_core/`

Основные подсистемы, обнаруженные в дереве DEV182:

| Путь | Область |
|---|---|
| `application/` | Композиция приложения и сборка сервисов. |
| `alarm/`, `events/`, `notifications/` | События, тревоги и уведомления. |
| `api/`, `web_pages/`, `ui/` | API, веб-страницы и инженерный интерфейс. |
| `audit/`, `security/` | Аудит, безопасность и контроль доступа. |
| `backup.py`, `repository/`, `transfer/` | Резервное копирование, хранилище и перенос станций. |
| `config/`, `contracts/`, `domain/` | Конфигурация, контракты и доменная модель. |
| `drivers/`, `network/` | Драйверы и сетевые протоколы. |
| `engineering/`, `engineering_intelligence/` | Инженерные операции и инженерная аналитика. |
| `field_runtime/`, `runtime/` | Полевой процесс исполнения и runtime. |
| `graphics/`, `logic_fbd.py`, `logic_fbd_studio.py` | Графика и FBD. |
| `history/`, `analytics/` | История и аналитика. |
| `licensing/` | Лицензирование и идентичность узла. |
| `points/` | Точки и их runtime-представление. |
| `scheduling/`, `time_management/` | Расписания и управление временем. |
| `platform/`, `deployment/`, `dependencies/` | Платформа, развёртывание и зависимости. |
| `commands/`, `transactions/` | Команды и транзакционные операции. |

Наличие каталога или файла означает, что соответствующий код присутствует в дереве. Оно само по себе не подтверждает полноту реализации, производственную готовность или прохождение испытаний.

### 4.2. Документация `docs/`

Ключевые документы сгруппированы по темам:

- **Архитектура и эксплуатация:** `ARCHITECTURE_RU.md`, `ENGINEERING_WORKBENCH_RU.md`, `SECURITY_RU.md`, `TONN_LINUX_CONTROLLER_DIRECTION_RU.md`.
- **FBD:** `FBD_BLOCKS_DEV96_RU.md`, `FBD_BLOCKS_DEV97_RU.md`, `FBD_STUDIO_COMPILER_DEV95_RU.md`, `FBD_RUNTIME_DEV146_RU.md`, `FBD_NIAGARA_TREND_PARITY_SPEC_DEV176_RU.md`.
- **Сеть и драйверы:** `NETWORK_MANAGER_RU.md`, `DRIVER_MANAGER_DEV57_RU.md`, `DRIVER_AUDIT_DEV128_RU.md`, `NETWORK_DRIVERS_AUDIT_DEV113_RU.md`, `DRIVER_POINT_INTEGRATION_DEV139_RU.md`.
- **Точки и протоколы:** `POINT_RUNTIME_CONTRACT_DEV85_RU.md`, `PROTOCOL_NEUTRAL_POINT_IMPORT_DEV140_RU.md`, `KNX_INTEGRATION_PLAN_DEV142_RU.md`.
- **Станции и данные:** `STATION_TRANSFER_DEV111_RU.md`, `STATION_TRANSFER_WORKBENCH_DEV148_RU.md`, `SYSTEM_BACKUP_DEV145_RU.md`, `STATION_TRANSFER_HARDENING_DEV161_RU.md`.
- **Графика и страницы:** `SVG_LIBRARY_DEV64_RU.md`, `SVG_LIBRARY_ISO3D_RU.md`, `WEB_APPLICATION_PAGE_BUILDER_DEV104_RU.md`, `REPOSITORY_PAGE_BUILDER_DEV107_RU.md`.
- **История сборок:** `BUILD_TEST_LOG_DEV*_RU.md`, `BUILD_*.md`, `CHANGELOG_DEV*_RU.md`.

Полный перечень документов доступен непосредственно в [каталоге docs]( AVIC_Core_1_0_Build_0_111_Station_Transfer_Engine_dev111/docs/ ).

### 4.3. Тесты `tests/`

В текущем дереве обнаружено 110 тестовых файлов. Основные группы по именам файлов:

- базовая архитектура и композиция приложения;
- UI / Engineering Workbench / навигационное дерево;
- FBD, компилятор, граф, расписания и runtime;
- драйверы BACnet/IP, Modbus TCP, MQTT, KNX и привязка точек;
- импорт и идентификация устройств;
- безопасность, лицензирование, секреты и Host Identity;
- резервное копирование и перенос станций;
- графика, SVG, страницы и AHU;
- Field Runtime и его процессная изоляция.

См. [полный каталог tests]( AVIC_Core_1_0_Build_0_111_Station_Transfer_Engine_dev111/tests/ ). Фактический результат тестирования фиксируется в соответствующем журнале сборки, а не выводится из количества тестовых файлов.

### 4.4. Сборочные материалы

- `pyproject.toml` — метаданные пакета, зависимости и настройки сборки.
- `build/` и `dist/` — сборочные каталоги, присутствующие в репозитории.
- `tools/` — вспомогательные инструменты.
- `BUILD_TEST_LOG_DEV*_RU.md` — журналы приёмки/проверок сборок в корне пакета.
- `docs/BUILD_TEST_LOG_DEV*_RU.md` — журналы документации и архитектурных проверок.

## 5. Справочные ветки

### Trend — `trend`

На дату снимка дерево содержит 6 548 записей. Основные каталоги верхнего уровня:

- `963/` — 5 295 записей, включая документацию/материалы 963.
- `Applets/` — 31 запись.
- `Documentation/` — 45 записей.
- `System Engineering Tool/` — 241 запись.
- `Tcc Suite/` — 57 записей.
- `ToolSET/` — 64 записи.
- Также присутствует копия дерева AVIC Core.

Использование: исследование поведения Trend SET/IQ, сопоставление функций и формирование требований к совместимости. Не считать содержимое этой ветки исходным кодом AVIC.

### Niagara — `reference/niagara-materials-archive`

На дату снимка дерево содержит 1 528 записей, включая отдельный верхнеуровневый каталог `niagara/` и копию дерева AVIC Core. Использование: справочная архитектурная инвентаризация и анализ концепций. Лицензированные материалы и бинарные дистрибутивы не переносить в продукт без подтверждённых прав.

## 6. Контроль различий и сохранности

На дату снимка подтверждено:

- `dev113-network-drivers` содержит 158 коммитов сверх `dev112-station-transfer-reliability`; DEV112 является базовым предком DEV113.
- `main` и `security/remove-niagara-from-current-tree` имеют одинаковый tree SHA `6698702a883a2b40f7d958b8c85b8f4db9b6d771`, то есть одинаковое содержимое дерева на момент проверки.
- Дерево DEV112: 823 записи.
- Дерево DEV113: 921 запись.
- Дерево main и security: по 815 записей.
- Дерево Niagara archive: 1 528 записей.
- Дерево Trend: 6 548 записей.

Это инвентарные размеры Git-деревьев, не число исходных строк и не число уникальных файлов между ветками. Для принятия решения о переносе конкретных изменений требуется отдельное сравнение commit ancestry и diff по файлам.

## 7. Обязательный порядок перед следующей разработкой

1. Проверить, что репозиторий — `AVICENG/avicscada.io`.
2. Получить свежий список веток и их HEAD.
3. Проверить открытые PR и их base/head.
4. Получить commit и tree текущего HEAD рабочей ветки.
5. Сравнить нужные ветки по Git history и diff.
6. Проверить, что создаваемое дерево строится от tree SHA актуального HEAD.
7. Внести минимальные целевые изменения и создать коммит.
8. Обновить ветку с проверкой ожидаемого старого SHA.
9. Проверить итоговый HEAD, состав дерева и PR.
10. Не выполнять merge без явного разрешения владельца.

## 8. История актуальности карты

Эта карта — снимок состояния на 26.11.2026. При добавлении/удалении ветки, изменении назначения ветки, переносе папки или изменении структуры основных подсистем обновлять этот документ отдельным изменением и указывать дату и HEAD, по которому сделана повторная инвентаризация.
