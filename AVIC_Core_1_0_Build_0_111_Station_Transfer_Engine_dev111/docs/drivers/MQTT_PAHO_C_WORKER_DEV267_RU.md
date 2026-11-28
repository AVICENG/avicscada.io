# MQTT Paho C Worker — DEV267

## Назначение

Отдельный C-процесс на Eclipse Paho MQTT C 1.3.16. Он принимает MQTT-телеметрию по подпискам и передаёт события в AVIC через Driver SDK v1 IPC. Python остаётся Supervisor и владельцем Point Runtime.

## Реализовано в DEV267

- Paho MQTT Async C client, отдельный executable.
- AVIC IPC handshake, scope identity, generation fencing, входная sequence validation и correlated responses.
- MQTT 3.1.1 anonymous TCP connect, подписки по настроенным topic filters, QoS 0/1/2.
- Automatic reconnect и повторные подписки после успешного соединения.
- Callback копирует topic/payload в JSON event и освобождает память Paho.
- Callback не пишет в IPC stdout: события идут через bounded queue (256 событий, 8 MiB) и отдельный writer thread.
- Максимальный MQTT payload 256 KiB; начальный профиль принимает только UTF-8 text.
- Один сериализованный IPC stdout writer для ответов и событий; общий monotonic sequence.
- Ответы получают собственный UTC `sent_at`, а не копируют время запроса.
- Состояние подключения синхронизируется отдельной блокировкой между Paho callbacks и IPC-потоком.
- Ошибки выделения памяти, сериализации и отправки критических IPC-событий приводят к fail-closed завершению процесса; протокольные ошибки main loop возвращают ненулевой exit code.
- MQTT publish/write команды отвергаются.
- Linux Mosquitto round-trip test target: C Worker → IPC → MqttCWorkerPointAdapter → Point Runtime.
- Windows build target переведён на MSVC; worker использует Windows-native critical sections/condition variables/thread, Linux — pthread.

## Ограничения

- MQTT 5.0 пока не включён в C Worker; Driver Manager явно отклоняет MQTT 5.0 для C engine, а Python fallback остаётся доступен.
- TLS и credential broker handoff не реализованы. tls_ca_file с C engine отклоняется. Пароли, токены и ключи не принимаются в worker config.
- Anonymous TCP only; TLS/username/password не поддерживаются.
- Бинарные MQTT payloads не публикуются в Point Runtime; требуется UTF-8 текст.
- Discovery и MQTT publish/control отсутствуют.
- Reconnect/queue overflow fault injection, TLS, broker soak и hardware broker acceptance остаются незакрыты.
- Завершение Paho disconnect lifecycle под интенсивным трафиком требует отдельного soak/fault-injection подтверждения.
- Наличие сборки не означает готовность драйвера; MQTT остаётся 🟧 до завершения CI и дополнительных негативных тестов.

## CI gates

Linux job строит Worker и запускает Mosquitto round-trip до Point Runtime. Windows job строит MSVC executable и проверяет IPC handshake/shutdown. Полные результаты фиксируются в DEV267 build test log после завершения workflow.
