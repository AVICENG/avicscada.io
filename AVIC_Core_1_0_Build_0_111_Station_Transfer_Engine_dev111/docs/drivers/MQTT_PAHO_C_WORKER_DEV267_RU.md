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
- Добавлены native negative-config checks (MQTT 5.0, TLS, QoS/port range) и Mosquitto broker restart → automatic reconnect → resubscribe → Point Runtime sample acceptance для Linux/Windows CI.
- Queue overflow fault injection, TLS, long broker soak и hardware broker acceptance остаются незакрыты.
- Завершение Paho disconnect lifecycle под интенсивным трафиком требует отдельного soak/fault-injection подтверждения.
- Наличие сборки не означает готовность драйвера; MQTT остаётся 🟧 до завершения CI и дополнительных негативных тестов.

## Дополнение по DEV267f CI

- Linux CMake configure/build прошёл; Mosquitto-to-Point-Runtime integration: **2 passed**.
- Windows MSVC configure прошёл, но компиляция Worker остановилась: `jansson.h` не найден в include path цели. В CMake добавлены публичный generated include и source include каталоги Jansson.
- Отключена ненужная сборка upstream Jansson test suite в составе Worker build.
- Новый CI на DEV268c должен подтвердить Windows build и свежие IPC lifecycle/timestamp checks.

## DEV268d — расширение Windows acceptance

Windows CI теперь устанавливает закреплённый Mosquitto 2.1.4 из официального Windows installer с SHA-256 verification, запускает изолированный localhost broker и выполняет полный `tests/test_mqtt_c_worker_dev267.py`, включая MQTT publish → native C Worker → IPC → Point Runtime. Это закрывает разрыв, при котором Windows ранее проверял только handshake.

## CI gates

Linux job строит Worker и запускает Mosquitto round-trip до Point Runtime. Windows job строит MSVC executable и проверяет IPC handshake/shutdown. Полные результаты фиксируются в DEV267 build test log после завершения workflow.


## DEV268p — CI broker lifecycle correction

The DEV268o CI attempt exposed that a background Mosquitto process cannot be started in one workflow step and relied upon in a later step: GitHub-hosted runner cleanup terminates orphan processes between steps. Windows readiness passed, but the following TCP preflight failed with connection refused. Linux also could not open a broker config stored under the workspace path.

The workflow now keeps broker startup, readiness checks, native Worker tests, log collection and broker shutdown in one step on both operating systems. Linux broker config is moved to `/etc/mosquitto/avic-ci.conf` with readable permissions. This is a CI harness correction, not a promotion of MQTT driver status. Reconnect, subscription rejection and soak/fault-injection gates remain open.
