# AVIC Core 1.0 — DEV111

DEV111 добавляет первый отдельный инженерный Station Transfer Engine.

## Главное

- Новый сервис `CoreApplication.station_transfer`.
- Формат пакета `.avicstation` для одной Station.
- Сохранение ID объектов и перепривязка к Project на целевой установке.
- Перенос явного набора station-scoped SQLite configuration records.
- Сброс сетевых адресов, NTP endpoints, device time permissions, runtime state и текущих значений точек.
- Preview, staged import, commit с проверками ID/reference collisions.
- Audit/Event записи успешных export/import.

## Документация

- `docs/STATION_TRANSFER_DEV111_RU.md` — назначение, workflow, состав, безопасность и ограничения.
- `BUILD_TEST_LOG_DEV111_RU.md` — проверенные тесты и результаты сборки.
- `CHANGELOG_DEV111_RU.md` — изменения DEV111.

## Важно

DEV111 не активирует Station, не запускает драйверы, не выполняет физические команды, не подписывает пакеты и не выполняет миграцию между версиями Core. Полная Windows acceptance должна быть выполнена на целевой машине заказчика.
