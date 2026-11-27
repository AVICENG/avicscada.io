# AVIC — выбор протокольных библиотек и план внедрения

Дата: 27.11.2026  
Статус: **рабочая матрица выбора; интеграция и аппаратная приёмка выполняются поэтапно**.

## Принципы

1. AVIC Core владеет объектной моделью, точками, качеством, лицензированием, RBAC, командами, аудитом и публикацией.
2. Сторонняя библиотека реализует протокольный транспорт/кодек. Она не получает прямой доступ к БД AVIC и не публикует значения в Point Runtime.
3. Каждый движок подключается через общий AVIC Driver SDK/IPC и заменяемый Worker. Язык не определяет права и семантику.
4. Приоритет — зрелая библиотека, подтверждённая лицензия, Windows + Linux, отказоустойчивость и проверка реальным оборудованием.
5. Все полевые записи остаются выключенными, пока отдельный Command Gateway не обеспечивает права, арбитраж, interlocks, идемпотентность и подтверждение фактического состояния.

## Матрица

| Протокол | Основной кандидат | Исполнение | Текущее решение / ограничения |
|---|---|---|---|
| Modbus TCP | libmodbus | C Worker, динамическая библиотека | Первый C-порт. Сначала FC01/02/03/04, batching, reconnect и diagnostics; RTU — отдельный этап с serial manager. |
| Modbus RTU | libmodbus | C Worker | Использовать ту же библиотеку, но отдельные тесты RS-485, таймингов, parity, stop bits, bus contention и recovery. |
| BACnet/IP | Steve Karg BACnet Stack | C Worker | Кандидат №1; проверить ReadProperty, RPM, Who-Is/I-Am, segmentation, BBMD, vendor/device behavior и совместимость с текущими профилями. Репозиторий содержит каталог нескольких лицензий: обязательна проверка SPDX/лицензии каждого используемого исходного файла, а не только примеров. |
| BACnet MS/TP | Steve Karg BACnet Stack | C Worker + serial | Кандидат; требуется полноценный MS/TP token-passing, serial timing и реальные RS-485 тесты. Не считать готовым вслед за BACnet/IP. Лицензии исходных файлов проверять поштучно. |
| BACnet/SC | Сначала отдельная проверка Steve Karg / CAS BACnet Stack | Изолированный C Worker | Не включать в первую поставку без проверки полноценного TLS, сертификатов, Hub/Node, failover и лицензии. CAS v6 заявляет BACnet/SC, MS/TP и IP в одной C/C++ библиотеке, но это платный/коммерческий кандидат, не обязательная покупка. |
| KNX | KNX Falcon .NET SDK | .NET Worker | Официальный публичный SDK доступен через NuGet; проверить runtime, redistributable, ETS-интеграцию, лицензирование и Windows deployment. Текущий Rust KNX путь сохраняется до parity. |
| OPC UA Client/Server | open62541 | C Worker | Основной открытый кандидат; MPL-2.0. Развести client и server профили, security policies, certificates, subscriptions, browse и namespace mapping. |
| MQTT 3.1.1/5.0 | Eclipse Paho C | C Worker | Основной кандидат; TLS, reconnect, persistent sessions, QoS, retained/LWT, bounded queues и SecretStore credential broker обязательны. |
| Siemens S7 | Snap7 / альтернативный SDK — оценка | Отдельный Worker | Не утверждать выбор до проверки актуального upstream, лицензии, поддерживаемых CPU/семейств и реального PLC. S7-1200/1500 security режимы требуют отдельной проверки. |
| Trend | BACnet общий стек + отдельный Trend adapter | C/ .NET по интерфейсу | Если контроллер предоставляет BACnet — использовать общий BACnet. Для IQ/vCNC/проприетарного интерфейса — отдельный протокольный адаптер, не подменять его BACnet. |

## Очерёдность внедрения

### DEV223 — C Worker foundation + Modbus TCP
- C Worker с AVIC IPC v1, ограничением размера кадра, корреляцией, scope и generation.
- Динамическое подключение libmodbus.
- Только чтение FC01/02/03/04 на первом этапе.
- Супервизор Core повторно использует существующие правила IPC; адаптер остаётся владельцем binding, quality mapping и Point Runtime publish.
- Windows/Linux CMake build, SBOM и notices.

### DEV224 — Modbus production parity
- Batch planner: объединение совместимых соседних адресов в один запрос с учётом лимитов функций.
- Переиспользование соединений, таймауты, reconnect, backoff, отмена, ограниченные очереди.
- RTU serial transport после отдельного тестирования.
- Fault injection и сравнение Python/Rust/C на одинаковых сценариях.

### DEV225 — BACnet C evaluation / integration
- Проверка стека Steve Karg и минимальный прототип Worker.
- Сначала discovery + ReadProperty, затем RPM; COV только после тестов подписок и восстановления.
- Сравнение с существующим BACnet/IP путем на Trend-контроллере.

### DEV226 — OPC UA и MQTT
- Два самостоятельных Worker, общий IPC.
- OPC UA security/certificates/subscriptions.
- MQTT TLS/QoS/session/reconnect/credential handling.

### DEV227+ — KNX Falcon, S7, BACnet/SC, MS/TP
- Отдельные acceptance gates и аппаратные стенды.
- Не включать экспериментальный backend в production каталог как READY.

## Обязательные критерии «готово»

- Сборка на Windows и Linux для поддерживаемых архитектур.
- Протокольные unit/contract tests и тесты malformed frames.
- Реальное устройство плюс симулятор; тесты потери связи, неверного ответа, перегрузки, рестарта Worker и stale generation.
- Нет обхода Point Runtime и Command Gateway.
- Нет утечки секретов в IPC, crash logs и diagnostics.
- Профиль нагрузки на 1k/5k/10k точек; публиковать только фактически измеренные результаты.
- Указаны версия и лицензия каждой внешней зависимости; сохранены license texts, notices, SBOM и исходники изменённых copyleft-компонентов.
- Документация конфигурации, установки, диагностики и восстановления обновлена вместе с кодом.

## Лицензионный реестр — начальные записи

| Компонент | Лицензия / режим | Действие AVIC |
|---|---|---|
| libmodbus | LGPL-2.1-or-later | Динамическая библиотека; включать LGPL notice и исходники точной версии/изменений. Коммерческая лицензия — только при отдельном бизнес-решении. |
| open62541 | MPL-2.0 | Сохранять notices; изменения файлов MPL публиковать под MPL при распространении. |
| Eclipse Paho C | EPL-2.0 (проверить выбранный релиз и файлы) | Проверить применимые условия EPL и комплект notices перед распространением. |
| KNX Falcon public SDK | Публичный SDK бесплатен для загрузки через NuGet; полный текст условий доступен через KNX account | До распространения проверить право redistributable, notices и условия коммерческого продукта по выбранной версии. Бесплатность загрузки не равна отсутствию лицензионных условий. |
| Steve Karg BACnet Stack | Проверить LICENSE выбранного commit/release | До интеграции зафиксировать точный upstream, commit, лицензию и все third-party файлы. |
| S7 SDK | Не выбран | Никакой зависимости до проверки лицензии и технической совместимости. |

Матрица не является утверждением о завершённой интеграции. Статус каждого драйвера определяется кодом, тестами и аппаратной приёмкой, а не наличием строки в каталоге.
