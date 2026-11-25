# Журнал сборки AVIC Core 1.0 — DEV111

Дата сборки: 24.11.2026

## Что реализовано

- Отдельный `StationTransferManager`, доступный как `CoreApplication.station_transfer`.
- Формат `.avicstation` с manifest, инвентарём станции и SHA-256 payload.
- Выбор Station-scoped записей из `objects.sqlite3`; разрешение Point через Device; включение PropertyDefinition по owner reference.
- Перенос конфигурационных данных из allow-listed таблиц: custom SVG, dependencies, time policy/device permissions, schedules + weekly/special events + point bindings, point tags/hierarchy.
- Перенос ID без изменений; при импорте Station перепривязывается к выбранному целевому Project.
- Очистка сетевых endpoint-полей, остановка драйверов/runtime, отключение протокольных каналов и перевод в read-only, очистка текущих значений точек, сброс Alarm в NORMAL.
- NTP-серверы удаляются, device clock-sync permissions сбрасываются в deny.
- Экспорт блокируется при обнаружении типовых секретов и частных IPv4 в свободном тексте.
- Preview → stage → commit; collision/reference checks; SQLite snapshots вспомогательных хранилищ и компенсация при ошибках.
- Event/Audit следы успешного экспорта и импорта.
- Обновлён Platform Module Catalog; функции остаются `partial`.

## Проверки, выполненные в этой среде

| Проверка | Результат |
|---|---|
| Новый Station Transfer suite | 7 passed |
| Расширенный regression suite (12 файлов тестов) | **6 785 passed** |
| `python -m compileall -q avic_core` | успешно |
| Wheel build `pip wheel --no-deps --no-build-isolation` | успешно |
| Установка wheel в отдельный target-каталог | успешно |
| Импорт `StationTransferManager` из wheel | успешно |
| Создание `CoreApplication` из установленного wheel и доступ к `app.station_transfer` | успешно |

Wheel: `avic_core-1.0.0.dev111-py3-none-any.whl`

SHA-256: `db1b52df5640ea05acedb9726fc16566cb619e1cd35eb279d1ef11c3b4dcafd6`

## Ограничения и честный статус

- Полный набор всех тестов репозитория в этой сборке не запускался; приведён результат целевого расширенного регрессионного набора.
- Windows acceptance на Python 3.15.2 не проводился. Linux-проверка не заменяет Windows acceptance.
- `pip check` завершился с конфликтом внешнего окружения: `moviepy 2.2.1` требует `pillow<12`, но установлен `pillow 12.3.0`. В самом `pyproject.toml` AVIC Pillow не заявлен.
- Нет UI/Workbench workflow и удалённого транспортного протокола.
- Нет подписи издателя пакета, автоматической межверсионной миграции, site-binding wizard, проверки связи с контроллерами, активации Station, запуска драйверов и rollback активной версии.
- Согласованного глобального snapshot всех SQLite-хранилищ нет. Экспорт требует остановить инженерные изменения на время операции.
- Компенсация транзакций вспомогательных БД не является crash-atomic восстановлением при отключении питания в любой точке процесса.
- Свободнотекстовая проверка не является DLP; инженер должен просмотреть пакет перед передачей.
- История, оперативные события, audit, notification outbox, пользовательские избранные точки и активные alarm-state журналы намеренно не переносятся.

**Статус:** DEV111 — проверяемый инженерный Station Transfer foundation, не готовая промышленная функция Station Copier и не Windows acceptance release.
