# Eclipse Paho MQTT C — native integration gate

## Выбор библиотеки

- Upstream: https://github.com/eclipse-paho/paho.mqtt.c
- Закреплённая версия: `v1.3.16`
- API: `MQTTAsync`, асинхронный C client.
- Лицензии upstream: Eclipse Public License 2.0 и Eclipse Distribution License 1.0; перед коммерческим релизом нужен inventory фактически собранных файлов, NOTICE и SBOM.
- Начальная нативная сборка использует static async client без TLS только для проверки C API и lifecycle. Это не production-ready конфигурация.

## DEV255 — native Paho probe

Проба проверяет:
- создание MQTTAsync client handle;
- регистрацию connection-lost, message-arrived и delivery-complete callbacks;
- освобождение сообщения callback-ом;
- уничтожение client handle и проверку его сброса;
- версии MQTT 3.1.1 и 5.0, объявленные upstream API.

Проверка не соединяется с брокером и не доказывает subscribe/receive, reconnect, TLS, credentials или нагрузочную устойчивость.

## Следующий этап

1. Добавить TLS-enabled Paho build на Windows/Linux с проверкой CA/hostname.
2. Создать read-only MQTT C Worker с AVIC IPC framing и secret handoff вне JSON/argv/env.
3. Подписки QoS 0/1/2, wildcard topics, retained/LWT, MQTT 3.1.1/5.
4. Ограничение payload, bounded callback queue, backpressure, reconnect/backoff.
5. Mosquitto/EMQX integration tests и сопоставление статусов с Point Runtime.
6. Удалять Python Paho runtime только после parity, regression и rollback acceptance.


## DEV262 — callback ownership correction

Paho `MQTTAsync_messageArrived` transfers ownership of both callback arguments to the application. The callback now releases both resources:
- `MQTTAsync_freeMessage(&message)`;
- `MQTTAsync_free(topic_name)`.

Upstream header v1.3.16 explicitly documents these release functions. When the full Worker is implemented, it must first copy topic and payload bytes into a bounded internal queue, then release both Paho allocations. The callback must not write IPC stdout or block on Point Runtime.
