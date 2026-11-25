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
