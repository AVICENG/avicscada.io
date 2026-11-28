# AVIC — план завершения нативных C-движков протоколов

Дата: 28.11.2026

## Жёсткое правило реализации

Протокольные стеки и транспортные операции перечисленных ниже драйверов выполняются нативными C Worker. Python/Rust не являются fallback и не дублируют протокольную реализацию. Python может оставаться только в общей оболочке AVIC: запуск/остановка процесса, IPC, Driver Manager, Point Runtime и тестовая оркестрация. Папка `rust/avic-communication-engine` исторически названа так; каталог `c-worker` и его исходник `main.c` — C11, это не разрешение переносить протокол в Rust.

## Очерёдность и статус

| Порядок | Драйвер | Целевая открытая библиотека | Язык | Фактическое состояние на дату документа |
|---:|---|---|---|---|
| 1 | Modbus TCP | libmodbus | C11 | 🟨 C Worker и read-only FC01/02/03/04 интегрированы. CI run `46153350062`: Linux native suite — 10 passed; Windows native suite — 9 passed, 1 skipped (Linux PTY-only). Нужны расширенная negative/soak матрица, полная проверка Point Runtime и hardware acceptance. |
| 2 | Modbus RTU | libmodbus | C11 | 🟨 RTU transport в том же C Worker, serial settings/RTS и эксклюзивная serial lease интегрированы. В run `46153350062` Linux native suite — 10 passed, включая PTY FC03 round-trip и CRC; Windows native suite — 9 passed, 1 skipped. COM alias normalization скомпилирована на Windows. Остаются прямые unit tests нормализатора, Windows virtual-COM round-trip, negative CRC/timeout/late-response, reconnect/soak и hardware acceptance. |
| 3 | BACnet/IP | Steve Karg BACnet Stack | C11 | 🟧 Native C probe собран на Windows и Linux в run `46153350062`; CTest codec suite прошёл на обеих ОС. На Linux upstream `bacserv` simulator подтвердил ReadProperty ACK и Error, I-Am/ReadProperty codec negative cases и прямой endpoint validation. Это ещё probe, не AVIC IPC Worker: нет общего Worker lifecycle, AVIC discovery result stream, Point Runtime polling/quality, RPM/segmentation и reconnect acceptance. Python стек остаётся legacy/regression reference. |
| 4 | BACnet MS/TP | Steve Karg BACnet Stack | C11 | ⬜ C Worker отсутствует. Использовать тот же upstream stack; нужны serial datalink, token lifecycle, RS-485 timing, diagnostics, Windows/Linux serial tests и hardware acceptance. |
| 5 | Siemens S7 / S7comm | Кандидат не утверждён | строго чистый C | C Worker отсутствует. Snap7 требует C++ toolchain; libnodave — beta/legacy и не принят для промышленного runtime. Не включать драйвер до отдельного технического решения. |
| 6 | MQTT | Eclipse Paho MQTT C | C | 🟨 Нативный Paho C Worker подключён к AVIC IPC и Point Runtime. Run `46153350062`: Windows MSVC и Linux native broker jobs — по 7 passed; проверены handshake/shutdown, отказ от неподдерживаемой конфигурации, reconnect/resubscribe и Mosquitto → Worker → Point Runtime round-trip. Текущий scope ограничен MQTT 3.1.1 anonymous TCP и UTF-8 payload; MQTT 5, TLS, SecretStore credentials, ACL/QoS policy hardening, soak и hardware broker acceptance остаются открыты. |
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

Работа идёт циклически по всей C-очереди. Если конкретный протокол блокируется внешней зависимостью, отсутствующим оборудованием или неготовым тестовым стендом, фиксируем точную причину/тест/статус и переходим к следующему драйверу; к отложенному gate возвращаемся в следующем цикле. Не терять незавершённый код и не понижать требования безопасности. Программные gates Windows/Linux закрываются независимо от hardware acceptance; 🟦 присваивается только после реального оборудования. Не заявлять «промышленно готов» без hardware acceptance.
