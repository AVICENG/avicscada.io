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
