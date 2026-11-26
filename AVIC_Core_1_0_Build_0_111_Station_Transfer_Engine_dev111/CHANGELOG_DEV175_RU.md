# DEV175 — безопасная остановка AVIC Core

- Разделены «Выход из Workbench» и «Остановить AVIC Core».
- CoreApplication теперь владеет FBDExecutionService.
- Добавлен preview активных станций, драйверов и FBD workers.
- Добавлено двойное подтверждение остановки и локальная защита API.
- Добавлен порядок graceful shutdown: FBD → драйверы → station Runtime.
- При неподтверждённом завершении worker процесс не должен завершаться.
- CLI Workbench получил управляемый graceful shutdown через Uvicorn Server.
- Добавлены тесты и русская документация; CI и E2E ещё требуют подтверждения.
