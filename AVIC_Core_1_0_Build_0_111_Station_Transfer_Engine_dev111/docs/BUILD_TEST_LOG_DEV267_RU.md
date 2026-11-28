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
- Windows Python 3.11/3.12/3.13 на этом коммите проверяют старый вариант MQTT 5.0 unit test; исправленный тест включён в следующий HEAD.

Исправление DEV268d:
- Явно добавлены `jansson_BINARY_DIR/include` и `jansson_SOURCE_DIR/src` в include path Worker target.
- Отключена сборка тестового набора Jansson внутри product build (`JANSSON_WITHOUT_TESTS=ON`).

Новый HEAD содержит также DEV268 IPC hardening и проверки актуального response timestamp/worker shutdown. Статус MQTT остаётся 🟧 до завершения нового Linux+Windows CI.
