# AVIC Core DEV179 — detached Field Runtime process

Базовый commit: cc0f30e45ef8c7a85d2ac496f4d45e5edb5fb8d8  
Версия: 1.0.0.dev179

## Изменения

- Исправлена модель процесса: multiprocessing заменён на самостоятельный subprocess.
- Добавлен отдельный агент-модуль avic_core.field_runtime.agent.
- Windows: DETACHED_PROCESS + CREATE_NEW_PROCESS_GROUP; POSIX: start_new_session.
- Loopback IPC, секрет через stdin, JSON-lines, request ID, sequence, timeout.
- Агент продолжает работать и переподключается после разрыва IPC; разрыв не является Stop.
- Maintenance stop требует точной фразы и токена.
- Добавлены тесты PID, IPC disconnect/reconnect и авторизованной остановки.
- Версия 1.0.0.dev179.

## Ограничения

FBD engine не подключён. PROCESS_HOST_ONLY, execution_engine_attached=false, active_strategies=0. Полевая автономность не реализована. Endpoint/credential persistence, watchdog и service manager integration ещё впереди.

## Проверки

Тесты добавлены, но не выполнены локально. GitHub Actions на DEV178 завершился failure без шагов и доступных журналов; причина не установлена. DEV179 не объявляется принятым.