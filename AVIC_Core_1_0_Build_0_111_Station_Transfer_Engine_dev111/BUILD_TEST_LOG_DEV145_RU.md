# Журнал сборки DEV145 — резервирование AVIC

## Изменения

- Добавлена avic_core.backup.SystemBackupManager.
- Добавлены методы CoreApplication.create_system_backup, inspect_system_backup, restore_system_backup, list_system_backups, prune_system_backups.
- Добавлено шифрование системного архива AES-256-GCM + Scrypt.
- Для SQLite используется Online Backup API и PRAGMA integrity_check.
- Добавлены проверки состава архива, SHA-256, безопасных путей, размеров и целостности.
- Добавлены тесты tests/test_system_backup_dev145.py, включая каталог и retention.
- Исправлена проверка SID Windows в HostIdentity: регулярное выражение ранее искало буквальную последовательность \d, а не цифры SID.

## Проверки

- Автоматические тесты DEV145 добавлены (создание/inspect/restore, неверный пароль, запрет работающей станции, защита непустой цели, минимальная длина пароля, retention). Результат CI ожидается.
- CI DEV143 ранее завершился ошибкой Windows: SID regex не принимал корректный SID. В DEV145 исправлен regex; требуется подтверждение новым Windows CI.
- Локальный запуск на Windows в этой итерации не выполнялся.
- Не заявляется готовность автоматического расписания, retention, удалённого provisioning или полной сквозной проверки восстановления.

## Известные ограничения

- Снимки SQLite согласованы отдельно, но нет единого межбазового write barrier.
- Полный backup требует остановки всех станций и драйверных сессий.
- Restore выполняется только в новый или пустой каталог.
- Station Transfer UI и remote deployment ещё не готовы.
