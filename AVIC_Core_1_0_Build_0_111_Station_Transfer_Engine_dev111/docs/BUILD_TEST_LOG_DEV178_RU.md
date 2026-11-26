# AVIC Core DEV178 — Field Runtime process boundary

Дата: 2026-11-26  
Базовый commit: db2414bff7b9047b0399de56ff4e3d6735ff51cd  
Версия: 1.0.0.dev178

## Изменения

- Добавлен пакет avic_core.field_runtime.
- Создаётся отдельный OS process через multiprocessing spawn.
- Добавлены IPC status/ping, startup handshake, request ID, sequence, timeout.
- Разрыв IPC не вызывает остановку процесса.
- Остановка процесса вынесена в отдельную maintenance-команду с подтверждением и секретом.
- Добавлены тесты процесса, IPC disconnect и maintenance authorization.
- Добавлена спецификация следующего этапа.

## Ограничения

FBDExecutionService ещё не перенесён. Процесс сообщает PROCESS_HOST_ONLY, execution_engine_attached=false, active_strategies=0. Это не автономное полевое управление и не основание запускать оборудование.

## Проверки

Тесты добавлены, но фактический запуск pytest, Windows acceptance и CI ещё не подтверждены. Предыдущие workflow runs завершались failure без шагов и логов; причина не установлена.