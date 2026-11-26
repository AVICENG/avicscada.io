# AVIC Core DEV180 — Field Runtime heartbeat

Версия: 1.0.0.dev180  
Базовый commit: d80db9e0a390e17a39ace89c3244c4725e6847e2

- Добавлен независимый периодический heartbeat внутри отдельного процесса.
- Добавлен тест, подтверждающий продвижение heartbeat без команд Supervisor.
- Остальные ограничения DEV179 сохраняются: FBD engine не подключён; нет системного watchdog/service installation; нет подтверждения полевого управления.
- Тесты добавлены, фактический pytest/Windows acceptance/CI не подтверждены.