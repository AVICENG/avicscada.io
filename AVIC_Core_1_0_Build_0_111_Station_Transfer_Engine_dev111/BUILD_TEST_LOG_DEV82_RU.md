# Журнал сборки и испытаний DEV82

## Состав
- База: AVIC Core DEV81.
- Версия пакета: 1.0.0.dev82.
- Обновлены: `avic_core/ui/app.py`, `avic_core/ui/engineering_tree.py`, `avic_core/logic_fbd_studio.py`, `avic_core/ui/static/logic.html`.
- Добавлены тесты: `tests/test_fbd_contract_dev82.py`, `tests/test_pid_engine_dev82.py`.
- Обновлены регрессионные тесты DEV78/DEV81 и проверка старого FBD route test под действующую модель дерева.

## Проверки в Linux-среде разработки
- `python -m compileall -q avic_core` — OK.
- Node.js `--check` для трёх inline JS-блоков FBD — OK.
- Целевой набор FBD / Engineering Tree / Workbench / Graphics: **12 569 passed** (финальный прогон после последних изменений).
- PID runtime sanity (Node.js): Direct при PV↑ увеличивает OUT; Reverse при PV↑ уменьшает OUT; переход MANUAL→AUTO без скачка на тестовом наборе — OK.
- Полный набор репозитория: 31 028 тестов обнаружено; полный прогон остановлен по лимиту времени на 56%. Полную регрессию не объявляем пройденной.
- `pip check` в общей среде разработки выявил сторонний конфликт `moviepy 2.2.1` ↔ `Pillow 12.3.0`; он не связан с зависимостями AVIC, но чистый `pip check` в этой среде не подтверждён. На машине пользователя нужно повторить `pip check` после установки.
- Wheel собран: `avic_core-1.0.0.dev82-py3-none-any.whl`, SHA256 `0300431354b00ac88384ccafc1a211b59bf8a524ba334e8add78d11ac60cf4c2`.
- Windows browser acceptance, реальные мышиные события, печать и проверка экранов 1366×768 / 1920×1080 — не выполнены в этой среде.

## Принятые стандарты
- BACnet: ANSI/ASHRAE 135 — Object Type + Object Instance в контексте устройства; UI label не заменяет native identity.
- Modbus: Application Protocol V1.1b3 — PDU address zero-based; legacy 3xxxx/4xxxx representation хранится отдельно.
- FBD: IEC 61131-3:2025 — FBD как сеть экземпляров FB/функций/переменных/литералов/меток; AVIC symbolic address документирован как соглашение AVIC, не как обязательная адресация IEC.

## Ограничения и открытые пункты
- FBD остаётся authoring-only, Runtime compiler отсутствует.
- `pending_core_registration` пока метаданные ожидания; полноценный License Manager handshake ещё не подключён.
- Общая верхняя навигация связывает четыре существующих workspace: Dashboard, Pages, FBD, Graphics. Это не означает наличие отдельного редактора для каждого типа объекта.
- BACnet/Modbus point storage contract задокументирован; аппаратная проверка каждого драйвера отдельно.
- Нужна ручная приёмка в Windows перед признанием DEV82 визуально принятой.
