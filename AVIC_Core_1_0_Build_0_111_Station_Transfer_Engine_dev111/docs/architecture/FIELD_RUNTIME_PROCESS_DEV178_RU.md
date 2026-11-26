# DEV178 — отдельная граница процесса Field Runtime

## Назначение

Добавлена первая исполняемая граница отдельного ОС-процесса AVIC Field Runtime. Это инфраструктурный этап по образцу разделения Platform Daemon и station execution в Niagara. Supervisor общается с дочерним процессом через отдельный IPC-канал.

## Реализовано

- отдельный процесс с именем AVIC-FieldRuntime, создаваемый через multiprocessing spawn (Windows/Linux);
- startup handshake и PID процесса;
- версионированный IPC envelope, request ID, последовательность команд, timeout и проверка корреляции ответа;
- status/ping с heartbeat и временем работы;
- разрыв IPC Supervisor не отправляет команду остановки полевому процессу;
- отдельная команда maintenance_stop требует точную фразу STOP FIELD RUNTIME и секрет авторизации;
- статус явно сообщает PROCESS_HOST_ONLY, execution_engine_attached=false и active_strategies=0.

## Чего пока нет — это важно

FBDExecutionService ещё не перенесён в этот процесс. Процесс DEV178 доказывает отдельную границу ОС и независимость от IPC disconnect, но не исполняет управляющие стратегии и не доказывает продолжение управления оборудованием при падении Supervisor. Не подключать этот host к производственному управлению до переноса движка, данных и безопасного интерфейса I/O.

## Следующий этап

1. Определить владельца постоянных опубликованных стратегий и runtime state на Field Runtime узле.
2. Вынести чистый FBD evaluator из Core-обвязки: graph input -> values + quality + timestamps + runtime state.
3. Передавать опубликованные неизменяемые пакеты стратегий в Field Runtime; не передавать открытые engineering drafts.
4. Реализовать локальное чтение входов и отдельный Output Dispatcher/Command Manager с локальными interlocks.
5. Добавить supervisor reconnect, epoch/TTL, replay protection, watchdog и bounded restart.
6. Только затем проверить закрытие/kill Supervisor при работающем FBD цикле.

## Тесты

Добавлены тесты отдельного PID, IPC status/ping, сохранения процесса после разрыва IPC и обязательной авторизации maintenance stop. До прохождения CI и локальной Windows-проверки тесты считаются добавленными, но не подтверждёнными.