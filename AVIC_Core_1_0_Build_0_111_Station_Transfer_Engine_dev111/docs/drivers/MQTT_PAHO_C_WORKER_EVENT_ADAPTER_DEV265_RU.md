# MQTT Paho C Worker — AVIC event adapter DEV265

## Что добавлено

- `MqttCWorkerPointAdapter` — отдельный event-driven consumer для будущего нативного Paho C Worker.
- MQTT C Worker имеет отдельную регистрацию бинарного файла в Driver Manager; бинарник Modbus не может быть случайно использован для MQTT.
- Конфигурация MQTT допускает явный выбор `engine="c"`; Python/Paho остаётся режимом по умолчанию и fallback.
- Каталог драйверов сообщает о C engine для MQTT отдельно от факта, что бинарник уже зарегистрирован.
- Consumer использует общий `RustDriverWorker` supervisor как транспорт AVIC IPC: worker identity, generation, sequence, bounded event queue и fail-closed при критическом overflow проверяются на общей границе.
- Event adapter маршрутизирует только точные настроенные topic bindings, валидирует UTF-8 payload, QoS и UTC timestamp, применяет существующую JSON/raw decoding/scaling логику и публикует только через Point Runtime.
- Disconnect/fault переводит точки в BAD_COMMUNICATION; остановка переводит их в STALE. Запись/публикация в MQTT брокер отсутствует.

## IPC event schema, ожидаемая от C Worker

Асинхронный sample:
- `kind="sample"`, `correlation_id=null`;
- `payload.event_class="sample"`;
- `payload.topic` — исходная MQTT тема;
- `payload.payload` — UTF-8 текст тела сообщения;
- `payload.qos` — 0, 1 или 2;
- `payload.received_at` — UTC RFC3339 с суффиксом Z;
- envelope identity/generation/sequence должны совпадать с инициализированным Worker.

Connection status:
- `kind="status"`, `correlation_id=null`;
- `payload.connected` — boolean.

Worker должен копировать данные из callback Paho в bounded queue и освобождать `MQTTAsync_message` и `topic_name` в callback. Только основной поток Worker пишет IPC stdout.

## Ограничения — не считать C Worker готовым

На DEV265 реализована Python-side AVIC event adapter и выбор C engine, но **сам исполняемый Paho MQTT C Worker ещё не создан**. Пока нет:
- CMake target и нативного executable для MQTT IPC;
- Paho connect/subscribe/reconnect lifecycle;
- реализации IPC command/event loop на C;
- тестового Mosquitto broker в Linux/Windows CI;
- end-to-end доказательства MQTT publish → C Worker → IPC → Point Runtime;
- фактических проверок QoS 0/1/2, MQTT 3.1.1/5.0, TLS CA, reconnect, queue limits и cleanup.

Поэтому engine `c` не следует включать в эксплуатационной конфигурации до сборки и регистрации принятого executable. Python adapter остаётся безопасным текущим рабочим путём. Пароли и токены не передаются в конфигурации или IPC; username/password пока не реализованы в C Worker.

## Приёмочные тесты адаптера

Добавлены unit tests с поддельным IPC worker:
- две точки на одной теме, разные JSON paths/scaling;
- timestamp UTC validation;
- unknown topic не маршрутизируется;
- STOP переводит точки в STALE;
- duplicate point binding отклоняется;
- Driver Manager выбирает C adapter без импорта Paho Python клиента.

Эти тесты проверяют Python-side event contract, а не сетевую работу нативного C Worker. Статус MQTT остаётся 🟧.
