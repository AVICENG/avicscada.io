# AVIC Core — журнал DEV223 (обновление 27.11.2026)

## Что изменено в этой итерации

1. **Modbus TCP / C Worker**
   - В Windows C Worker включён бинарный режим stdin/stdout через `_setmode(..., _O_BINARY)`. IPC использует length-prefixed binary frames; текстовая трансляция Windows недопустима.
   - Исправлен Modbus TCP simulator в тесте: MBAP Protocol ID теперь передаётся двумя нулевыми байтами, а не буквальными символами `\\x00`.
   - Сам факт отправки исправления не считается подтверждением прохождения: требуется новый CI run на актуальном HEAD.

2. **BACnet/IP — сборка upstream stack**
   - В BACnet Stack probe явно выключен upstream option `BAC_ROUTING`.
   - Причина Linux build failure установлена по compiler log и исходникам pinned upstream: при включённом routing `datalink_get_my_address` переопределяется на `Routed_Device_Get_My_Address`, но routing endpoint не входит в этот single-datalink BACnet/IP probe.
   - AVIC probe — обычный BACnet/IP endpoint, не маршрутизатор. Поэтому выключение routing соответствует назначению текущего worker/probe; это не отключение BACnet/IP.

3. **MQTT — runtime integration**
   - MQTT добавлен во встроенный Driver Manager factory registry.
   - Добавлен `EventDrivenSession`: он управляет start/stop callback-driven транспорта без искусственного polling loop; состояние остаётся DEGRADED, пока брокер не подключён.
   - Factory использует Paho MQTT 2.x; поддерживает MQTT 3.1.1/5.0, JSON/raw bindings и CA-validated TLS.
   - Каталог теперь корректно обозначает MQTT как READ_ONLY_TRANSPORT, а не PLANNED.
   - Секреты по-прежнему запрещены в DriverInstance config. Username/password и клиентский private key ещё не подключены к SecretStore; не передавать их через config.
   - Добавлены fake-client тесты подписки/QoS, JSON decode/scale, ошибочного payload и lifecycle.

4. **Документация**
   - Добавлена инструкция `docs/drivers/MQTT_RUNTIME_DEV223_RU.md`.
   - Этот журнал фиксирует изменения и незакрытые критерии приёмки.

## Проверки и CI

- Исходный CI run `46013538196` выявил:
  - C Modbus Worker Linux simulator test: MBAP Protocol ID mismatch в fake peer;
  - Windows C Worker IPC: binary stream mode не включён;
  - BACnet Stack Linux: undefined `Routed_Device_Get_My_Address`;
  - BACnet Stack Windows probe прошёл;
  - Siemens S7 optional library smoke jobs прошли на Linux и Windows.
- Исправления Modbus отправлены отдельными коммитами; BACnet Linux build fix также отправлен.
- Новый CI run `46016020126` на commit `513d6917d4be078fce59ce636c2075743e73a69f` на момент записи находится в состоянии pending, jobs ещё не опубликованы. Поэтому тесты текущего HEAD НЕ объявляются пройденными.
- MQTT fake-client tests включены в тот же PR head; их результат пока не подтверждён.
- Hardware acceptance на реальном Modbus/BACnet/MQTT/S7/KNX оборудовании не выполнялась.

## Состояние шести целевых протоколов

| Протокол | Реальный статус этой ветки | Что ещё обязательно |
|---|---|---|
| Modbus TCP | Python/Rust read-only пути; C libmodbus Worker с IPC и тестовым simulator | Зелёный актуальный Linux/Windows CI, fault/reconnect tests, реальное устройство |
| BACnet/IP | Python discovery/ReadProperty и point adapter; pinned Steve Karg stack probe | Подтвердить Linux build после фикса, полноценный C Worker, RPM/COV, hardware acceptance |
| KNXnet/IP | Python tunnelling/passive GroupValue monitor, ограниченный набор DPT | ETS import, расширение DPT, reconnect/timeout tests и KNX IP interface |
| MQTT | Paho subscribe-only factory + event-driven lifecycle | Зелёный fake tests, SecretStore credentials, TLS broker acceptance, reconnect soak |
| Siemens S7 | Snap7/S7CommPlus optional packages; library smoke tests проходили на Linux/Windows | Изолированные read-only workers, security/firmware matrix, реальный PLC acceptance |
| OPC UA | Не реализован; выбран open62541 как кандидат | Зафиксировать версию/лицензию, C client worker, certificates, browse/read/subscriptions и server simulator tests |

## Ограничения и решение по готовности

- Шесть протоколов НЕ являются шестью завершёнными промышленными драйверами.
- На этой итерации продвинуты Modbus C Worker, BACnet build portability и MQTT runtime.
- OPC UA и полноценный Siemens S7 worker остаются незавершёнными; KNX остаётся ограниченной read-only реализацией.
- Запись в оборудование остаётся запрещённой. Все будущие команды должны проходить через Core Command Gateway.
- PR #9 остаётся Draft. Не объединять до зелёного CI, code review и hardware acceptance по соответствующим протоколам.


## Дополнительная регрессия S7 в базовом Python matrix

- При разборе полного pytest-лога обнаружены ровно две ошибки в трёх Linux Python matrix jobs: тесты optional S7 зависимостей импортировали `s7` и `s7commplus` без проверки наличия extra.
- Исправлено через `pytest.importorskip`: базовая установка Core не обязана включать опциональные S7 библиотеки; dedicated S7 jobs продолжают устанавливать `.[s7]` и выполняют реальные import/version smoke checks.
- Это исправление тестового контракта, а не ослабление S7 acceptance.
- Требуется повторный полный CI на актуальном HEAD; зелёный результат пока не получен.


## Фокус DEV223 follow-up: Modbus TCP / BACnet/IP / KNXnet/IP

### Modbus TCP
- Выделение MBAP transaction ID переведено на потокобезопасный allocator. Это устраняет гонку между параллельными запросами одного Modbus client до открытия TCP-соединения.
- Добавлены regression tests на coalescing смежных диапазонов без чтения через gap, публикацию GOOD, BAD_COMMUNICATION при timeout и параллельное выделение 2 000 transaction IDs.
- Остаются: RTU/RS-485, fault/reconnect soak, реальное устройство и актуальный CI.

### BACnet/IP
- Добавлены regression tests для ReadProperty binding, array index, scale/offset и BAD_COMMUNICATION на timeout.
- Существующий сетевой клиент реализует discovery, ReadProperty, Device.Object_List и чтение Object_Name/identity properties; это пока не заменяет RPM/COV/segmentation/BBMD.
- Linux CMake fix upstream probe ожидает подтверждения на новом полном CI.

### KNXnet/IP
- Расширен строгий decoder common DPT: 1.xxx, 5.001/5.003/5.004, 6.001, 7.001, 8.001, 9.001, 12.001, 13.001, 14.000, 16.000 и 17.001.
- KNX adapter теперь извлекает short APDU для всех разрешённых DPT 1.xxx, а не только DPT 1.001.
- Добавлены positive/negative DPT tests, adapter short-APDU routing test и binding coverage.
- Создана инструкция `docs/drivers/MODBUS_BACNET_KNX_DEV223_RU.md`.
- Остаются ETS import, GroupValueRead polling, Command Gateway write path, routing и физическая приёмка.

### CI status
- Новые Modbus/BACnet/KNX regression tests добавлены в ветку после предыдущего CI run. Для последующих commits GitHub connector пока не вернул связанный pull_request workflow run; локальный pytest здесь не запускался.
- Следовательно, новые тесты НЕ объявляются пройденными. Перед следующим статусом требуется проверить фактический workflow run актуального PR HEAD и исправить все найденные падения.
