# Жёсткий аудит драйверной подсистемы AVIC — DEV128

Дата: 25.11.2026  
Базовая ветка: `dev113-network-drivers`  
Базовый проверенный HEAD: `e6d0081cf3b1c48e6af2c71128ed62f74b425ba0`

## Критические замечания аудита

1. **Ложное обещание MQTT в каталоге.** Код подписочного адаптера существовал, но Driver Manager не имел встроенной factory, безопасной интеграции SecretStore и завершённой TLS-политики. Ранее каталог всё же объявлял MQTT читающим транспортом. В DEV128 MQTT переведён в PLANNED до появления полного runtime wiring.
2. **Состояние драйвера расходилось с polling worker.** Worker мог перейти в DEGRADED, а API продолжал показывать сохранённый RUNNING. Диагностика теперь показывает эффективное состояние worker отдельно от persisted_state.
3. **Осиротевший runtime после перезапуска процесса.** В БД мог сохраниться RUNNING, хотя worker в новом процессе не существует. Теперь такой экземпляр диагностируется как ORPHANED и не выдаётся за работающий.
4. **Неверный признак field I/O.** Поле field_io_enabled всегда было False и не объясняло разницу чтения и записи. Добавлены field_read_enabled и field_write_enabled; запись остаётся запрещённой.
5. **Остановка станции не останавливала принадлежащие ей драйверы.** DEV128 добавляет DriverManagerService.stop_station и вызывает его из CoreApplication.stop_station. Даже при ошибке остановки драйвера остановка Station Runtime всё равно предпринимается, после чего вызывающая сторона получает явную ошибку.
6. **Отсутствовали регрессионные тесты на деградацию, orphaned state и stop station.** Добавлены тесты на эти сценарии.

## Подтверждённые возможности на момент аудита

- Modbus TCP: ограниченные FC01/02/03/04, чтение через MBAP, декодирование 16/32/64-bit integer и float, byte/word order, scale/offset, общий Point Runtime, BAD_COMMUNICATION при ошибке.
- BACnet/IP: Who-Is/I-Am discovery, ReadProperty, чтение Object_List и Device identity, общий Point Runtime, BAD_COMMUNICATION при ошибке.
- Оба адаптера не реализуют команды записи. Нельзя путать read-only транспорт с полноценной поддержкой всех функций протокола.
- PollingSession выполняет один последовательный worker без параллельных catch-up циклов; это не гарантирует bounded shutdown, если сетевой вызов не возвращается до socket timeout.

## Ограничения, которые остаются открытыми

- Нет автоматического восстановления/перезапуска активных драйверов после аварийного завершения процесса; теперь состояние честно обозначается ORPHANED, но recovery workflow ещё нужен.
- Нет общего watchdog/health policy с persisted transitions и политикой retry/backoff.
- MQTT адаптер пока не включён как production runtime: нет factory, SecretStore wiring и broker acceptance.
- Нет OPC UA Client/Server, SNMP, KNXnet/IP, LonWorks, oBIX, Haystack production adapters.
- Trend IP/vCNC не реализован: доступные материалы недостаточны для достоверной реализации framing, reconnect и Secure vCNC.
- BACnet/IP требует дальнейшей проверки APDU/NPDU маршрутизации, сегментации, BBMD/foreign-device сценариев, COV и межвендорной совместимости.
- Modbus TCP требует дополнительных проверок hostname/IPv6, persistent connection strategy, device profiles, map import, exception handling interoperability и реальных контроллеров.
- Не проверены физические контроллеры в этой CI-сессии; unit/fake-server тесты не заменяют hardware acceptance.
- Каталог Niagara не является доказательством совместимости. Исключены Niagara Fox, CCN, Andover и N2 по решению проекта.

## Протоколы и источники

- Modbus Organization: Application Protocol V1.1b3 и Modbus TCP Messaging Implementation Guide. Официальный список: https://www.modbus.org/modbus-specifications
- OPC Foundation: OPC UA Part 2 Security Model, Application Authentication и TrustLists: https://reference.opcfoundation.org/specs/OPC-10000-2/4.10
- OPC Foundation: OPC UA Part 4 SecureChannel/Session sequence: https://reference.opcfoundation.org/specs/OPC-10000-4/6.1
- Niagara JAR-файлы не декомпилировались. Семейства модулей используются только как ориентир для независимой реализации по открытым спецификациям.

## Статус

DEV128 исправляет конкретные ошибки жизненного цикла и каталогизации. Это не означает, что вся драйверная линейка готова к эксплуатации или продаже. Готовность должна подтверждаться отдельными протокольными, нагрузочными, security и hardware acceptance тестами для каждого драйвера.


## Дополнительная находка DEV127: Windows ACL

Предыдущая CI-матрица DEV127 завершилась на Windows Python 3.13: 31 178 тестов прошли, 1 пропущен, 1 упал в `test_installation_identity_is_uuid_and_private`. Анализ лога показал, что объединённый вызов `icacls /grant:r` не применил ACE точного SID текущего пользователя; вместо него в SDDL оставался Local Account. DEV128 меняет настройку ACL на последовательные отдельные операции `icacls`: отключение наследования, удаление Local Account, отдельная выдача прав точному SID, SYSTEM и Administrators. Это исправление ещё должно пройти повторную Windows CI.

## Дополнительная корректировка

Регистрация новой factory больше не блокируется произвольно из-за активной сессии другого протокола. Замена factory запрещена только пока работает экземпляр именно этого driver_id.


## DEV129 — усиление фильтра секретов конфигурации

Повторная проверка показала, что рекурсивный фильтр конфигурации распознавал только несколько точных имён ключей. В DEV129 проверка нормализует имена полей и блокирует распространённые варианты и суффиксы секретов: `api_key`, `mqtt_password`, `oauth_refresh_token`, `tls_private_key`, `clientKey` и вложенные аналоги. Это снижает риск сохранения секретов в обычной конфигурации драйвера. Фильтр не заменяет SecretStore и не является полноценным DLP-сканером произвольных значений.


## DEV131 — производительность Modbus TCP polling

Modbus TCP адаптер теперь объединяет соседние и перекрывающиеся read-only bindings с одинаковым function code в один ограниченный запрос (FC01/02 до 2000 бит, FC03/04 до 125 регистров). Значения отдельных точек декодируются из общего ответа; ошибка группового чтения переводит все затронутые точки в BAD_COMMUNICATION, сохраняя последние значения. Добавлен тест, подтверждающий, что два соседних регистра читаются одним запросом. Это базовая оптимизация; адаптивный scan class, deadband, приоритеты, rate limiting и профили устройств ещё не реализованы.


## DEV132 — безопасность BACnet/IP transaction handling

- Доступ к UDP socket и Invoke ID теперь сериализован на уровне одного BacnetIpClient; параллельные операции discovery/ReadProperty не должны перехватывать ответы друг друга.
- ReadProperty принимает ответ только от точного IP:UDP endpoint, которому был отправлен запрос, а не от любого порта того же IP.
- Сегментированный ComplexACK теперь явно отклоняется диагностической ошибкой вместо молчаливого ожидания timeout. Реassembly сегментов ещё не реализован.
- Добавлены тесты на чужой UDP source port и явную диагностику неподдерживаемого сегментированного ответа.


## DEV133 — согласование Driver Manager и Core runtime

- Восстановлена и сохранена единая версия Driver Manager, содержащая все исправления DEV128–DEV132; обновления секретного фильтра и factory guard больше не перезаписывают более ранние lifecycle исправления.
- Остановка станции не требует, чтобы Station уже существовала в инженерном репозитории: Core может зарегистрировать runtime station до создания inventory record. Остановка по-прежнему останавливает все DriverInstance, найденные по station_id.
- Регистрация factory блокируется только при активной сессии того же driver_id; независимые протоколы не блокируют друг друга.
- Добавлены тесты на runtime-only station shutdown, alias secret keys и точечную блокировку factory.


## DEV134 — проверка целостности commit tree

- Повторно проверено содержимое Git blob по SHA из текущего commit tree. Исправлены две записи, которые в DEV133 содержали текстовые SHA вместо содержимого исходников: Driver Manager и его тестовый файл. DEV134 возвращает полные исходники и тесты; проверка содержимого выполняется чтением blob по SHA, а не только наличием пути в дереве.


## DEV135 — согласование статусов и запуск polling worker

- PollingSession.start теперь ожидает подтверждения перехода worker в RUNNING, поэтому API запуска не должен возвращать промежуточный STARTING как завершённый старт.
- Список экземпляров станции теперь использует эффективное состояние runtime; сохранённое состояние показывается отдельно как persisted_state. Состояние DEGRADED больше не скрывается в списке за устаревшим RUNNING.
- Фильтр конфигурации дополнен токенами, secret_key, signing_key, access_key, shared_secret, session_key и JWT aliases.
- Добавлены тесты на ожидание старта worker и согласованность list/get/diagnostics.


## Сопоставление семейств Niagara с целевым деревом AVIC

| Семейство/модуль из материалов Niagara | Цель AVIC | Текущее состояние по коду |
|---|---|---|
| `bacnet-rt` | BACnet/IP client | Частичная read-only реализация: Who-Is/I-Am, ReadProperty, Object_List/identity и Point Runtime; без RPM/COV/segmented APDU/BBMD полного уровня |
| `modbusTcp-rt` | Modbus TCP client | Частичная read-only реализация FC01/02/03/04, типы 16/32/64 bit, scale/offset, grouped polling |
| `modbusCore-rt`, `modbusAsync-rt` | Общая модель Modbus и Modbus RTU | Не реализовано; RTU требует serial bus manager, timing, CRC и arbitration |
| `modbusSlave-rt` | Modbus TCP/RTU Server (Slave) | В AVIC отсутствует; требуется отдельный безопасный server driver с ACL на адреса/регистры и аудитом внешних записей |
| `abstractMqttDriver` | MQTT client | Парсер/subscribe adapter есть, но нет production factory, SecretStore wiring, TLS policy и acceptance; каталог переведён в PLANNED |
| `opcUaClient` | OPC UA Client | Не реализовано |
| `opcUaServer` | OPC UA Server | Не реализовано |
| `snmp` | SNMP monitoring | Не реализовано; проектировать SNMPv3 authPriv, GET/WALK и trap/inform с read-only профилем |
| `eibnetIp`, `knxnetIp` | KNXnet/IP | Не реализовано; нужны tunnelling/routing, group addresses и datapoint type profiles |
| `lonworks`, `lonTrend-rt` | LonWorks / Trend LON profile | Не реализовано; нужен отдельный интерфейсный/транспортный слой и device profiles |
| `obix` | oBIX HTTP(S) | Не реализовано |
| `haystack` | Project Haystack | Не реализовано; это семантическая модель/интеграция, а не замена полевого транспорта |
| `TrendN4-rt` | Trend IP / vCNC | Не реализовано; известны TCP endpoint/port conventions, но wire codec и Secure vCNC handshake не подтверждены |
| `trendMigration-*` | Migration/import tooling | Не полевой драйвер; отдельный миграционный инструмент, не включать в Driver Manager как transport |
| `TrendEasyBindingGraphics-rt`, `themeIQVision-ux`, `docIQVision-*` | Graphics/theme/docs | Не драйверы полевого протокола; учитывать в отдельных подсистемах графики, темы и документации |

**Исключения проекта:** Niagara Fox, CCN, Andover и N2 не включаются. Название JAR/модуля доказывает только наличие семейства в поставке, но не раскрывает точный wire protocol, внутренние функции или качество реализации. JAR не декомпилируются.

## Коммерческая активация — отдельный незакрытый пробел

В каталоге есть поле `license_feature`, однако DriverManager пока не связывает его с подписанным LicenseStatus и EditionAccessPolicy при создании/запуске экземпляра. Кроме того, текущая Capability enum не содержит driver-specific capability keys. Следовательно, наличие license_feature в каталоге пока является метаданными, а не реальным ограничением платного доступа. До продажи драйверных пакетов необходима серверная проверка подписи лицензии, Host-ID, edition, RBAC и feature key на каждой операции create/start; UI-скрытия недостаточно.


## DEV136 — исправление тестовых сценариев BACnet и каталога

DEV134 CI выявил три тестовые ошибки: два новых BACnet теста содержали литералы с двойным экранированием, поэтому тестовый пакет фактически передавал символы `\\xNN`, а не байты; третий тест продолжал ожидать MQTT в списке реально работающих read transports после обоснованного перевода MQTT в PLANNED. DEV136 исправляет байтовые литералы и ожидание каталога. Это тестовые исправления; они не расширяют протокольные возможности.


## DEV137 — восстановление Git blob-содержимого

Повторная проверка DEV136 обнаружила, что пять путей исходников/тестов в tree были связаны с blob-объектами, содержащими текстовые SHA вместо самих файлов. DEV137 напрямую связывает эти пути с проверенными полными blob SHA: Driver Manager, PollingSession и три тестовых файла. В CI должны проверяться именно эти полные файлы; наличие пути без проверки содержимого не считается достаточным.


## DEV138 — верификация BACnet ReadProperty ComplexACK

- До DEV138 клиент проверял BVLC/APDU и Invoke ID, но не сверял возвращённые Object Identifier, Property Identifier и Array Index с запросом. Это создавало риск принять значение от неправильного объекта/свойства при корректном источнике и совпавшем Invoke ID.
- DEV138 проверяет все три идентификатора до декодирования значения; пустой application payload считается ошибкой.
- Обновлены тестовые ACK builders и добавлен тест отказа при несовпадении object identity.


## DEV137 CI finding

- Linux Python 3.12: 31,188 passed, 1 failed. Единственный отказ — ещё один двойной escape в тестовом BVLC prefix сегментированного ACK (`b"\\\\x81\\\\x0a"` вместо байтов `b"\\x81\\x0a"`). Исправлено в DEV138; это не отказ production parser.
