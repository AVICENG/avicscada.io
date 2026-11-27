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
| BACnet/IP | Steve Karg BACnet Stack | C Worker | Основной кандидат для POC. Зафиксирован upstream commit 45f9831996f1a17504a790da91a4113f2974595c; проверен license/readme.txt: GPL-2.0-or-later WITH GCC-exception-2.0 разрешает link с proprietary code; в репозитории также MIT/Apache-2.0 файлы. Выборочно проверены Win32/Linux BIP и MS/TP порты; перед production обязателен полный SPDX/SBOM только по реально компилируемому source set. Функционально: сначала ReadProperty, RPM, Who-Is/I-Am, segmentation, BBMD и Trend. |
| BACnet MS/TP | Steve Karg BACnet Stack | C Worker + serial | Тот же стек и закреплённый commit; Linux/Win32 port files включают GCC exception и MIT файлы. Требуется полноценный MS/TP token-passing, serial timing и реальные RS-485 тесты. Не считать готовым вслед за BACnet/IP. |
| BACnet/SC | Сначала отдельная проверка Steve Karg / CAS BACnet Stack | Изолированный C Worker | Не включать в первую поставку без проверки полноценного TLS, сертификатов, Hub/Node, failover и лицензии. CAS v6 заявляет BACnet/SC, MS/TP и IP в одной C/C++ библиотеке, но это платный/коммерческий кандидат, не обязательная покупка. |
| KNX | KNX Falcon .NET SDK | .NET Worker | Официальный публичный SDK доступен через NuGet; проверить runtime, redistributable, ETS-интеграцию, лицензирование и Windows deployment. Текущий Rust KNX путь сохраняется до parity. |
| OPC UA Client/Server | open62541 | C Worker | Основной открытый кандидат; MPL-2.0. Развести client и server профили, security policies, certificates, subscriptions, browse и namespace mapping. |
| MQTT 3.1.1/5.0 | Eclipse Paho C | C Worker | Основной кандидат; TLS, reconnect, persistent sessions, QoS, retained/LWT, bounded queues и SecretStore credential broker обязательны. |
| Siemens S7 classic | python-snap7 3.6.0 | Python Worker | MIT, pure Python, stable. Основной путь для S7-300/400. Для S7-1200/1500 — только compatibility PUT/GET, который отключён по умолчанию, неаутентифицирован и не даёт optimized DB. Не включать автоматически. |
| Siemens S7-1200/1500 | s7commplus 0.7.0 | Python Worker | MIT package, Beta; S7CommPlus V1/V2 TLS/V3, symbolic/optimized DB. 19 zlib dictionaries имеют LGPL-3.0 notice. Реальная совместимость зависит от CPU/firmware/project security; нужны точные hardware acceptance tests. См. SIEMENS_S7_DRIVER_SELECTION_AND_SECURITY_RU.md. |
| Siemens S7 alternative | S7.Net Plus | .NET Worker candidate | MIT; оставить compatibility option, не основной движок, пока не проверены secure S7CommPlus paths. |
| Trend | BACnet общий стек + отдельный Trend adapter | C/ .NET по интерфейсу | Если контроллер предоставляет BACnet — использовать общий BACnet. Для IQ/vCNC/проприетарного интерфейса — отдельный протокольный адаптер, не подменять его BACnet. |

## Очерёдность внедрения

### DEV223 — C Worker foundation + Modbus TCP
- C Worker с AVIC IPC v1, ограничением размера кадра, корреляцией, scope и generation.
- Динамическое подключение libmodbus.
- Только чтение FC01/02/03/04 на первом этапе.
- Супервизор Core повторно использует существующие правила IPC; адаптер остаётся владельцем binding, quality mapping и Point Runtime publish.
- Windows/Linux CMake build, SBOM и notices.

### DEV224 — Modbus production parity
- Реализован общий batch planner в адаптере Rust/C: сортировка по FC и адресу, объединение только смежных/перекрывающихся диапазонов одного FC; разрывы адресов не читаются.
- Соблюдаются пределы Modbus: FC01/02 — до 2 000 бит, FC03/04 — до 125 регистров; слишком большие диапазоны разбиваются на отдельные запросы.
- Результат одного диапазонного чтения раскладывается по bindings и проходит индивидуальное декодирование типа, byte/word order, scale и offset.
- Диагностика показывает число batch-запросов за последний poll и накопленное число batch-запросов.
- Добавлены регрессионные тесты планировщика: смежность, разные FC, адресные разрывы, лимиты, ошибочные диапазоны и фактическое сокращение числа transport reads.
- Следующий подэтап: локальный Modbus TCP simulator, fault injection и измерение Python/Rust/C на одинаковом наборе точек; затем reconnect/backoff и RTU serial manager.
- Fault injection и сравнение Python/Rust/C на одинаковых сценариях.

### DEV225 — BACnet C evaluation / integration
- Лицензионный аудит Steve Karg выполнен: см. BACNET_STACK_LICENSE_AND_INTEGRATION_AUDIT_RU.md.
- Добавлен pinned upstream CMake build probe на Windows/Linux с BACDL_BIP; CI пока ожидает выполнения. Это проверка сборки библиотеки, не готовый BACnet Worker.
- После зелёной сборки — минимальный Worker discovery + ReadProperty.
- Сначала discovery + ReadProperty, затем RPM; COV только после тестов подписок и восстановления.
- Сравнение с существующим BACnet/IP путем на Trend-контроллере.

### DEV226 — Siemens S7 open engines
- Лицензии и версии проверены: python-snap7 3.6.0 (MIT, stable) и s7commplus 0.7.0 (MIT package, Beta; LGPL-3.0 notice для bundled dictionaries).
- Classic S7 и S7CommPlus остаются разными protocol IDs и отдельными workers.
- Следующий кодовый шаг: Python Worker IPC wrapper, сначала read-only classic S7; затем S7CommPlus TLS/symbolic browse и optimized DB.
- Не включать PUT/GET автоматически; TLS certificate validation fail-closed.
- См. SIEMENS_S7_DRIVER_SELECTION_AND_SECURITY_RU.md.

### DEV227 — OPC UA и MQTT
- Два самостоятельных Worker, общий IPC.
- OPC UA security/certificates/subscriptions.
- MQTT TLS/QoS/session/reconnect/credential handling.

### DEV228+ — KNX Falcon, BACnet/SC, MS/TP, Trend proprietary
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
| Steve Karg BACnet Stack | GPL-2.0-or-later WITH GCC-exception-2.0 core; отдельные MIT/Apache files | Pin + file-level audit; до production полный SPDX/SBOM и notices. См. BACNET_STACK_LICENSE_AND_INTEGRATION_AUDIT_RU.md. |
| python-snap7 3.6.0 | MIT | Pinned upstream audit commit 2aca5459cba0ce21d65f255882bcd562d86392f1; pure Python classic S7. Сохранять MIT notice. |
| s7commplus 0.7.0 | MIT package; bundled zlib dictionaries LGPL-3.0-or-later; HarpoS7 helper MIT | Pinned upstream audit commit 5295810835095d90b103430e809a47b63a0b3438; сохранить LICENSE, NOTICE-S7CommPlusDriver и LICENSE-HarpoS7; учитывать Beta status и firmware matrix. |
| S7.Net Plus | MIT | Secondary .NET compatibility candidate; сохранять License.txt; не считать его S7CommPlus/TLS implementation. |

Матрица не является утверждением о завершённой интеграции. Статус каждого драйвера определяется кодом, тестами и аппаратной приёмкой, а не наличием строки в каталоге.
