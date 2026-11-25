# Изменения DEV111

- Добавлен отдельный `StationTransferManager` и формат `.avicstation`.
- Реализован station-scoped export из репозитория Core с разрешением Point → Device и дочерних графов FBD/Graphics/Web Pages.
- Добавлены конфигурационные переносы SVG, dependencies, schedules, time policy, device-time permissions и point tags/hierarchy.
- Сохранение инженерных ID; импорт Station в выбранный целевой Project.
- Добавлены site sanitization и fail-safe состояния: каналы выключены/read-only, драйверы/runtime остановлены, точки без live value, NTP и device clock permissions сброшены.
- Добавлены preview, SHA-256, staging integrity check, collision/reference validation и commit с компенсирующими SQLite snapshots.
- Добавлены Audit/Event события для успешных операций.
- Обновлён Platform Module Catalog: Deployment & Updates остаётся `partial`; Backup & Restore остаётся отдельным `partial`.
- Универсальный `.avicpkg` DEV110 сохранён для обратной совместимости; он не считается Station Copier.
