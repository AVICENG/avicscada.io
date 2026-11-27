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


## KNX follow-up: active GroupValueRead and scene datapoints

- Добавлен явный режим `read_mode="poll"` в Python KNX adapter и Driver Manager. В этом режиме за один polling tick отправляется один cEMI L_Data.req / GroupValueRead к следующему групповому адресу; пассивный мониторинг остаётся режимом по умолчанию.
- Тайм-аут или ошибка отправки активного запроса переводит именно запрошенную точку в BAD_COMMUNICATION; счётчик отказов и last_errors обновляются.
- Для Rust KNX engine активный режим пока fail-closed: factory отказывает вместо молчаливого игнорирования `read_mode="poll"`.
- Исправлен DPT 16.000: padding удаляется по реальным NULL-байтам.
- DPT 17.001 исправлен по KNX wire format: значение 0..63, старшие два бита зарезервированы и должны быть нулевыми. DPT 18.001 добавлен как scene activate/learn + номер сцены 0..63, зарезервированный бит проверяется.
- Regression tests дополнены реальными бинарными byte literals, активным GroupValueRead и DPT 17/18.

## Дополнительные CI результаты и текущая очередь

- Run `46019312841` (commit до последних KNX изменений): Linux C Worker configure/build/IPC handshake — SUCCESS; BACnet Stack probe — SUCCESS на Ubuntu и Windows; Rust unit tests и synthetic Modbus benchmark — SUCCESS на Ubuntu и Windows; S7 optional library smoke tests — SUCCESS.
- В том же run Python Linux matrix выявил устаревшее ожидание каталога: MQTT теперь также read-supported. Исправлен тест `test_driver_catalog_dev26.py`; функциональность каталога не откатывалась.
- Windows UCRT64 C Worker job в run `46019312841` всё ещё завершился ошибкой: процесс C Worker закрывал stdout до IPC handshake. В `main.c` добавлена диагностика результата `_setmode` stdin/stdout; нужно получить вывод нового Windows run, прежде чем менять бинарный IPC ещё раз.
- Полный Windows Python 3.11 job в run `46019312841` ещё выполнялся при последней проверке.
- Run `46021185409` (после исправления KNX DPT 17/18 и тестов) был создан как pending; jobs пока не опубликованы, поскольку предыдущий workflow run ещё не освободил общую concurrency group.
- Никакие новые KNX/Modbus/BACnet regression tests не объявляются пройденными до фактического завершения актуального run.


## 27.11.2026 — дополнительная отладка Modbus C Worker и KNX

- Windows UCRT64 build C Worker проходит, но прежний CI run обнаружил, что скомпилированный процесс закрывает IPC stdout до handshake. Код ошибки `_setmode` и ошибка чтения кадра теперь диагностируются в stderr.
- Обнаружен вероятный deployment-фактор Windows: C Worker линкуется с libmodbus/Jansson из MSYS2, тогда как изолированный DriverManager запускает процесс с ограниченным environment. Для MinGW добавлена статическая линковка (`-static -static-libgcc`), чтобы исключить зависимость от внешнего MSYS2/UCRT DLL search path. Это исправление ещё не подтверждено новым CI.
- RustWorker теперь включает exit code процесса в диагностическое сообщение при EOF IPC stdout.
- KNX active polling теперь не принимает первый попавшийся GroupValueResponse: после GroupValueRead он ждёт ответ именно для запрошенного group address, пропуская посторонние телеграммы до тайм-аута. Добавлен regression test «посторонняя группа перед ожидаемым ответом».
- Новые тесты и статическая линковка пока не объявляются пройденными. CI runs, созданные для промежуточных commits, отменялись concurrency-механизмом GitHub при новых push. Последний commit документации: `e87759d8326a92962740af0e76676b2e8486804a`; требуется дождаться прогона на HEAD ветки.


## Дополнительный CI разбор (run 46021295444)

- Linux full-suite на Python 3.11/3.12/3.13: по 31 449 passed и 1 failed. Единственное падение — устаревший `test_driver_manager_requires_registered_runtime_for_mqtt`: тест ожидал отсутствие MQTT factory после того, как MQTT runtime уже был зарегистрирован. Тест заменён проверкой регистрации factory и сохранения read-only capability.
- BACnet Stack POC, Rust communication engine и C Worker Ubuntu прошли; Windows BACnet Stack POC и Rust engine прошли. S7 optional dependency smoke tests прошли.
- Windows C Worker UCRT64 всё ещё падал до IPC handshake. Добавлена статическая линковка Windows binary и диагностика раннего завершения процесса; новая сборка должна подтвердить или опровергнуть гипотезу о DLL search path.
- Текущий следующий gate: новый полный run после последнего тестового исправления и завершение Windows Python matrix. Не сливать PR до зелёного результата.


## DEV224 follow-up — Windows CI path and BACnet RPM

- Разбор run \`46026237032\` показал, что Windows C Worker успешно конфигурируется и компилируется; job падал не на бинарнике, а на проверке окружения: workflow жёстко искал \`C:\\msys64\\ucrt64\\bin\\objdump.exe\`, тогда как setup-msys2 размещает MSYS2 во временном каталоге runner.
- Workflow исправлен: \`objdump.exe\` теперь разрешается через \`Get-Command\`; найденный UCRT64 bin-каталог используется и при запуске Python IPC/Modbus acceptance tests.
- Добавлен \`BacnetIpClient.read_property_multiple\`: одна confirmed RPM-транзакция читает до 64 свойств одного объекта; проверяются Invoke ID, BVLC length, object identity, уникальность/принадлежность property IDs и полнота ответа. Per-property BACnet Error возвращается как структурированное значение, а не теряется вместе с успешными свойствами.
- Безопасные ограничения RPM: только чтение; один объект на запрос; array-index результаты и segmented ComplexACK пока явно не поддерживаются; лимит 64 свойства ограничивает размер запроса. Для таких случаев вызывающая сторона должна использовать отдельный ReadProperty либо получить явную ошибку.
- Добавлены тесты \`tests/test_bacnet_rpm_dev224.py\` на несколько значений в одной транзакции, частичный BACnet Error, правильное формирование запроса, неверную идентичность объекта и ограничения размера/дубликатов.
- **Статус проверки:** код и тесты отправлены в ветку, но CI run на актуальном HEAD ещё ожидает запуска из-за общей concurrency queue. Ни прохождение RPM tests, ни исправление Windows IPC пока не подтверждены. Аппаратная BACnet приёмка не выполнялась.
