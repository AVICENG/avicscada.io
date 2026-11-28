# AVIC Core — журнал DEV267 (Paho MQTT C Worker)

Дата: 28.11.2026  
PR: #11 — drivers/modbus-rtu-c-worker-dev249

## Состав DEV267

- Создан rust/avic-communication-engine/mqtt-c-worker — отдельный C executable на Eclipse Paho MQTT C 1.3.16.
- Добавлен IPC handshake и lifecycle для AVIC Driver SDK v1.
- Добавлены asynchronous sample/status/fault events, bounded event queue, отдельный IPC writer thread и единая sequence.
- Поддержаны anonymous MQTT 3.1.1 connect, QoS 0/1/2 subscriptions, wildcard filters и automatic reconnect.
- Добавлен Mosquitto → C Worker → IPC → Point Runtime integration test.
- Добавлены Linux/Windows native CI jobs.

## Подтверждённые промежуточные CI результаты

- DEV267 исходная Linux C сборка Worker прошла.
- Python 3.11/3.12/3.13 Linux compile и полный pytest matrix прошли на исправленном source snapshot.
- Первый Mosquitto round-trip не запустился: workflow env path содержал лишний обратный слэш перед абсолютным путём. Исправлено в последующем workflow commit.
- Первый Windows native build в MSYS2 UCRT64 упал внутри upstream Paho v1.3.16: несовместимый тип DWORD* / int* в Windows thread API. Windows job переведён на MSVC, а worker synchronization адаптирован к Win32 API.
- Эти результаты не являются успешной приёмкой DEV267; повторный CI обязателен.

## Ограничения

- MQTT C Worker поддерживает только anonymous MQTT 3.1.1 over TCP.
- MQTT 5.0, TLS и credential broker handoff пока не реализованы; Driver Manager отклоняет эти параметры для C engine.
- Payload только UTF-8 text, до 256 KiB.
- MQTT publish/control выключены.
- Не завершены TLS, reconnect/queue overflow fault injection, long soak и реальная промышленная broker acceptance.
- MQTT остаётся 🟧.

## Критерий следующего решения

Не повышать статус до 🟨, пока новый Windows MSVC build, Linux Mosquitto-to-Point-Runtime round-trip, полный Python Windows/Linux matrix и negative/lifecycle tests не пройдут на одном HEAD.


## Дополнение DEV267e — CI run 46130256822

На HEAD `72ef85462f1bfd07246e201d38b55eb263fcf0c1` выявлено:
- Linux CMake configure и Windows MSVC configure остановились на Jansson 2.14.1: upstream CMakeLists начинается с legacy minimum version 2.8, а CMake 4.x больше не поддерживает compatibility level ниже 3.5.
- Linux Python 3.11/3.12/3.13: по 31 548 passed, 10 skipped и 1 failed. Единственный failure — прежний unit test ожидал MQTT 5.0 на C Worker, тогда как DEV267 явно ограничил native C engine MQTT 3.1.1. Исправлен тест: 3.1.1 проверяется как положительный путь, 5.0 — как ожидаемый отказ.
- Windows Python jobs на момент дополнения ещё выполнялись; их результаты не приписываются этому журналу.

Исправления:
- В CMake добавлен `CMAKE_POLICY_VERSION_MINIMUM=3.5`, чтобы использовать Jansson 2.14.1 без патча стороннего исходного кода.
- Обновлены manager regression tests для действительной границы MQTT 3.1.1 / 5.0.

Повторный CI на новом HEAD обязателен. До его завершения MQTT остаётся 🟧.


## Дополнение DEV268 — IPC hardening и результаты DEV267 CI

Предыдущий run `46130256822` завершился с ошибками на HEAD `72ef85462f1bfd07246e201d38b55eb263fcf0c1`:
- Linux Python 3.11/3.12/3.13: по 31 548 passed, 10 skipped, 1 failed — старый тест ожидал MQTT 5.0 для native C engine.
- Windows Python 3.11/3.12/3.13: по 31 545 passed, 13 skipped, 1 failed — тот же устаревший тест. JUnit artifact Windows Python 3.11 подтверждает точную причину.
- Linux Mosquitto C Worker и Windows MSVC C Worker не дошли до компиляции worker: CMake 4.x отверг legacy `cmake_minimum_required(VERSION 2.8)` в Jansson 2.14.1.
- OPC UA open62541 probes, Modbus C Workers, Rust Communication Engine, BACnet POC/codec и S7 C-only policy jobs прошли.

В DEV268/DEV268a/DEV268b:
- Добавлена блокировка состояния connected для синхронизации callback-потоков Paho с IPC-потоком.
- Добавлен fail-closed путь при отказе сериализации/выделения памяти и ошибке IPC writer.
- Невалидный IPC frame и ошибка обработки/ответа теперь дают ненулевой exit code.
- IPC response получает собственный актуальный UTC sent_at.
- Исправлена проверка connected во всех callback/close/status путях.
- Добавлен regression gate для свежести response sent_at, состояния connected и корректного завершения worker.

Эти изменения пока не имеют подтверждённого CI на новом HEAD. MQTT остаётся 🟧.


## Дополнение DEV267f CI — run 46130918095

На HEAD `71559b899fa60dde12282d2118ebd116ef526a50`:
- Linux Python 3.11/3.12/3.13 завершились успешно.
- Linux Paho MQTT C Worker build и Mosquitto → C Worker → IPC → Point Runtime: **2 passed**.
- Windows MSVC configure и сборка Paho/Jansson зависимостей прошли; Worker compile остановился на `fatal error C1083: jansson.h: No such file or directory`.
- Windows Python 3.11: **31 547 passed, 13 skipped**; Python 3.13: **31 547 passed, 13 skipped**. Python 3.12 ещё выполнялся на момент записи. В этих jobs уже проверялась исправленная граница MQTT 3.1.1/5.0.

Исправление DEV268d:
- Явно добавлены `jansson_BINARY_DIR/include` и `jansson_SOURCE_DIR/src` в include path Worker target.
- Отключена сборка тестового набора Jansson внутри product build (`JANSSON_WITHOUT_TESTS=ON`).

Новый HEAD содержит также DEV268 IPC hardening и проверки актуального response timestamp/worker shutdown. Статус MQTT остаётся 🟧 до завершения нового Linux+Windows CI.


## Дополнение DEV268d — Windows broker acceptance

Windows MQTT CI расширен: после MSVC build устанавливается Mosquitto, поднимается локальный broker на 127.0.0.1:18883, затем выполняются оба native test: IPC handshake/shutdown и broker-to-Point-Runtime round-trip. Это изменение ещё ожидает CI; результат будет записан после прогона.


## Дополнение DEV268g — negative config и reconnect acceptance

Добавлены тесты нативного C Worker: отказ от MQTT 5.0/TLS/недопустимого QoS/порта с проверкой завершения процесса; перезапуск Mosquitto с проверкой connection-lost, automatic reconnect, повторной подписки и доставки нового sample в Point Runtime. Эти тесты запускаются в Linux и Windows native broker jobs и пока ожидают CI.


## DEV268g CI finding — reconnect test broker startup

В run `46132872138` Linux Worker build и основной Mosquitto-to-Point-Runtime тест прошли, но новый reconnect test завершился до запуска Worker: отдельный Mosquitto с временным конфигурационным файлом завершился с exit code 3. Тестовый broker helper переведён на тот же проверенный CLI режим `mosquitto -p <port> -v`, который уже используется основным Linux CI broker. Повторный Linux/Windows reconnect acceptance обязателен.


## DEV268l — Windows Mosquitto provisioning

Chocolatey Community feed не содержит пакета `mosquitto` (`package was not found`). CI переведён на официальный Windows installer Mosquitto 2.1.4 с pinned URL и обязательной SHA-256 проверкой `034017C8F8E3B5B86BDBD971F6C5184370311058E4DE7B96A0F10204BBB9E7C8`. Установка выполняется в silent mode; затем `C:\Program Files\mosquitto` добавляется в PATH для broker и publisher acceptance.


## DEV268m — результаты повторной broker acceptance (run 46133101378)

На HEAD `f8936d495404ac468bbba7b336f48e3776d32b2d`:
- Полная Python matrix (Windows/Linux, Python 3.11/3.12/3.13) прошла.
- Modbus C Worker, OPC UA native probes, BACnet Stack POC и Rust Communication Engine jobs прошли.
- MQTT Linux native job: 6 тестов прошли, reconnect/resubscribe завершился ошибкой — после рестарта брокера Paho не восстановил connected за 25 секунд.
- MQTT Windows native job: MSVC сборка и установка Mosquitto 2.1.4 прошли; reconnect не восстановился, а основной C Worker не подключился к брокеру, хотя readiness-проверка через mosquitto_pub прошла.
- DEV268l не является успешной MQTT acceptance.

Исправления DEV268m:
- Добавлен отдельный Paho `MQTTAsync_setConnected` callback: автоматическое восстановление соединения обрабатывается отдельно от первоначального connect success; при reconnect повторно отправляются все topic subscriptions.
- В connect-failure callback добавлен диагностический вывод кода и текста ошибки Paho в stderr.
- При отказе round-trip/reconnect тест выводит полную диагностику adapter/worker.
- Linux и Windows CI переходят на одинаковую явную конфигурацию Mosquitto: loopback listener, anonymous access только для изолированного тестового брокера, persistence off.

Проверка DEV268m ожидает новый Linux+Windows CI. До успешного round-trip, reconnect/resubscribe и lifecycle/negative tests MQTT остаётся 🟧.


## DEV268n — исправление формата Linux broker config

Во время ревью DEV268m до завершения CI обнаружено, что shell `printf` получил экранированные последовательности `\\n` как буквальные символы, а не как переводы строк. Это могло сформировать некорректный однострочный Mosquitto config. Исправлено на однозначный heredoc с отдельными строками директив. Также нормализованы newline escape в диагностических строках C Worker. DEV268m CI не считать итоговой проверкой этой корректировки; новый HEAD должен пройти повторный прогон.


## DEV268o — broker diagnostics and deterministic CI listener

Результаты DEV268n (run 46147345856):
- Linux: native C Worker configure/build прошли; broker startup failed до запуска MQTT tests. Mosquitto сообщил `Unable to open config file /tmp/avic-mosquitto.conf`; первопричина — путь/доступность конфигурационного файла в job, не протокольный тест.
- Windows: MSVC build и Mosquitto startup/readiness прошли; 6 tests passed, Point Runtime round-trip failed. Paho stderr: `TCP/TLS connect failure` (code -1). Это реальная нерешённая интеграционная ошибка; readiness через mosquitto_pub не доказывает доступность того же listener для C Worker.
- DEV268o меняет Linux config path на GITHUB_WORKSPACE, выставляет mode 0644, проверяет читаемость, PID и сохраняет broker log.
- Вторичный broker в reconnect test запускается с тем же явным listener/anonymous/persistence config, лог сохраняется; добавлен прямой TCP preflight.
- При Windows round-trip failure тест приложит broker log к AssertionError, чтобы отличить отказ TCP listener от отказа Paho-клиента.

Эта версия диагностическая. Ни MQTT reconnect, ни round-trip не считаются принятыми до успешного CI на обеих ОС.


## DEV268p — исправление жизненного цикла CI Mosquitto

Run `46148774566`, HEAD `5d2cb5e5f1f8c9f517459e16c611c349ef7ca4cf` выявил две инфраструктурные причины, из-за которых MQTT acceptance не доходил до протокольной проверки:

- Linux: Mosquitto не смог открыть конфигурацию из каталога workspace. Лог: `Unable to open config file /home/runner/work/avicscada.io/avicscada.io/.avic-mosquitto-ci.conf`. Следующая версия переносит config в `/etc/mosquitto/avic-ci.conf` и выставляет читаемые права.
- Windows: broker readiness через `mosquitto_pub` прошёл, но следующий pytest получил `ConnectionRefusedError [WinError 10061]` на TCP preflight 127.0.0.1:18883. Причина — broker был запущен в отдельном workflow step; GitHub Runner завершает оставшиеся фоновые процессы после шага. Запуск broker, readiness, pytest и гарантированное завершение перенесены в один step.

В этом run Linux/Windows native MQTT acceptance не прошла; на Windows 6 тестов прошли, один round-trip остановился до запуска Worker из-за отсутствующего listener. Это не является доказательством дефекта Paho protocol path, но и не подтверждает работоспособность Worker.

Linux Python 3.12 на этом HEAD: `31550 passed, 15 skipped`. Полная Windows Python matrix на момент подготовки дополнения ещё выполнялась; её итог будет записан отдельно.

MQTT остаётся 🟧. Повторный Linux+Windows native acceptance обязателен.
