# DEV179 — Detached Field Runtime process

## Исправление архитектуры процесса

DEV178 использовал multiprocessing.Process. Хотя он создаёт отдельный PID, lifecycle multiprocessing связан с интерпретатором Supervisor: при завершении Python родительский процесс может ждать завершения non-daemon child. Для строгой границы управления это недостаточно.

DEV179 заменяет его на отдельный subprocess, запущенный как самостоятельный модуль Python. На Windows он запускается detached/new process group; на POSIX — в новой session. Supervisor не владеет его завершением через multiprocessing finalizer.

## IPC и поведение при разрыве связи

- Агент подключается к loopback TCP listener Supervisor; порт выбирается ОС.
- Секрет передаётся через stdin при запуске, а не аргументом командной строки.
- Агент аутентифицирует подключение; сообщения JSON-lines ограничены 64 KiB.
- Каждая команда имеет protocol version, request ID и возрастающий sequence; повтор/устаревшая последовательность отклоняется.
- При потере IPC агент продолжает собственный процесс и пытается переподключиться. Разрыв связи не является командой Stop.
- Остановка агента доступна отдельной maintenance-командой с точной фразой и секретом.

## Честная граница возможностей

Как и в DEV178, FBDExecutionService пока не подключён. Агент явно возвращает PROCESS_HOST_ONLY, execution_engine_attached=false и active_strategies=0. DEV179 доказывает только отдельный OS process и устойчивость к IPC disconnect, а не продолжение управления оборудованием при падении Supervisor.

Порт и секрет пока живут в памяти текущего Supervisor. Для reconnect после полного перезапуска Supervisor нужны постоянный защищённый endpoint/credential store и восстановление регистрации агента. Watchdog/autostart через системный Service Manager также следующий этап.

## Следующий этап

1. Постоянная регистрация агента и безопасное переподключение после рестарта Supervisor.
2. Отдельное хранилище опубликованных неизменяемых стратегий и runtime state.
3. Отвязка FBD evaluator от CoreApplication и перенос циклического исполнения в агент.
4. Локальный драйверный I/O и Output Dispatcher с interlocks, readback и аудитом.
5. Watchdog, bounded restart, service install/autostart и отказные испытания.