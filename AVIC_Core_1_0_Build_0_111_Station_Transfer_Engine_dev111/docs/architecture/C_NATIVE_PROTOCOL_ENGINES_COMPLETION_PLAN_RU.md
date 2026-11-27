# AVIC — план завершения нативных C-движков протоколов

Дата: 27.11.2026

## Жёсткое правило реализации

Протокольные стеки и транспортные операции перечисленных ниже драйверов выполняются нативными C Worker. Python/Rust не являются fallback и не дублируют протокольную реализацию. Python может оставаться только в общей оболочке AVIC: запуск/остановка процесса, IPC, Driver Manager, Point Runtime и тестовая оркестрация. Папка `rust/avic-communication-engine` исторически названа так; каталог `c-worker` и его исходник `main.c` — C11, это не разрешение переносить протокол в Rust.

## Очерёдность и статус

| Порядок | Драйвер | Целевая открытая библиотека | Язык | Фактическое состояние на дату документа |
|---:|---|---|---|---|
| 1 | Modbus TCP | libmodbus | C11 | C Worker существует; read-only FC01/02/03/04. TCP/RTU общий runtime. Приёмка не завершена: Linux PTY round-trip ранее падал с ETIMEDOUT; свежий CI для актуального HEAD ещё не дал зелёного результата. |
| 2 | Modbus RTU | libmodbus | C11 | RTU transport добавлен в тот же C Worker; параметры serial/RTS и serial lease добавлены. Нужны подтверждённые Windows/Linux CI, отрицательные RTU тесты, reconnect/ownership и аппаратные испытания. |
| 3 | BACnet/IP | Steve Karg BACnet Stack | C11 | В репозитории только stack probe (версия и имя Device object), не AVIC driver. C Worker отсутствует. Существующий Python стек — legacy/regression reference, не целевой runtime. |
| 4 | BACnet MS/TP | Steve Karg BACnet Stack | C11 | Полноценного C Worker нет. Нужны serial datalink, token lifecycle, RS-485, timing, diagnostics и аппаратные тесты. |
| 5 | Siemens S7 / S7comm | Кандидат не утверждён | строго чистый C | C Worker отсутствует. Snap7 требует C++ toolchain; libnodave — beta/legacy и не принят для промышленного runtime. Не включать драйвер до отдельного технического решения. |
| 6 | MQTT | Eclipse Paho MQTT C | C | Есть Python runtime; C Worker отсутствует. |
| 7 | OPC UA Client | open62541 | C | Native C probe существует; полноценного AVIC IPC Worker, paging/subscriptions/reconnect и SecretStore lifecycle нет. |
| 8 | Wired M-Bus | libmbus | C | Спецификация есть; Worker отсутствует. Только проводной M-Bus, не Wireless M-Bus. |

KNXnet/IP (XKNX/Python) не относится к списку C-драйверов и ведётся отдельно после завершения согласованной C-очереди.

## Общие критерии завершения каждого C-драйвера

1. Зафиксировать upstream commit, лицензию каждого реально компилируемого компонента, SBOM/notices и воспроизводимую сборку.
2. Worker на C11 (или версия C, требуемая upstream), без скрытого Python/Rust протокольного процесса; строгие предупреждения компилятора как ошибки.
3. Windows и Linux сборки; проверка DLL/shared-library deployment и корректного завершения процесса.
4. Единый AVIC Driver IPC: framing, schema validation, max frame, identity, sequence, generation fencing, bounded memory, отсутствие секретов в argv/env/IPC/logs.
5. Протокольная матрица: positive/negative frames, malformed packets, timeout, late response, exception, reconnect, cancellation, resource cleanup.
6. Интеграция с Driver Manager и Point Runtime; quality/timestamp/status раздельны; устаревшие значения не остаются GOOD после потери связи.
7. Fuzzing парсеров/кадров, ASan/UBSan где применимо, leak checks, soak, latency p50/p95/p99 и ограничение памяти.
8. Симулятор и golden vectors не заменяют реальные контроллеры/шлюзы/приборы. Hardware acceptance фиксирует модель, firmware, конфигурацию, физический интерфейс и журнал.
9. Русская документация, эксплуатационные ограничения, troubleshooting, журнал сборки и тестов обновляются в том же цикле.
10. Удаление старого Python/Rust протокольного кода — только после parity, регрессии и проверки всех путей запуска.

## Правило статусов

- 🟦 Подтверждено на реальном оборудовании с моделью/firmware и журналом.
- 🟩 Заявленный программный объём реализован и целевые тесты Windows/Linux пройдены.
- 🟨 Частичная AVIC интеграция / ограниченный read-only runtime.
- 🟧 Библиотека/probe/POC или неполный Worker.
- 🟥 Актуальный CI/test failure.
- ⬜ Не реализовано или не проверено.

Цвет ставится отдельно для каждого протокола и каждого gate. Старый успешный CI не доказывает новый HEAD. Ни один C-драйвер не получает 🟦 без аппаратного подтверждения.

## Рабочий порядок

Закрываем Modbus TCP+RTU полностью, затем BACnet/IP, затем BACnet MS/TP, S7, MQTT, OPC UA Client и Wired M-Bus. Не начинаем полноценный следующий Worker, пока предыдущий не прошёл все программные gates и не зафиксированы отдельно оставшиеся аппаратные gates. Не заявлять «промышленно готов» при отсутствии hardware acceptance.
