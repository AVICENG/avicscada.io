# AVIC Core 1.0 — DEV52

## Цель
Начать пораздельную реализацию IQVISION 2.30 с пользовательского руководства, раздел 5 «Points List View».

## Реализовано в DEV52
- Служба `PointViewService` с постоянным хранением избранных точек в отдельной SQLite БД.
- Изоляция избранного по `user_id`; хранение station scope.
- Поиск по имени, описанию, source reference и native identity.
- Фильтр по станции и качеству, режим «только избранное».
- Сортировка по name/data_type/value/unit/quality/native_identity, asc/desc.
- Пагинация с валидацией limit/offset.
- CSV экспорт списка с UTF-8 BOM и разделителем `;`.
- Workbench Point Manager: фильтры, сортировка, избранное, счётчик, CSV и переход к History.
- API: GET points, POST/DELETE favorite, GET export.csv.

## Ограничения
- DEV52 не реализует изменение/override значений точек. Это намеренно оставлено до Command Manager, RBAC, подтверждений, quality interlocks, read-back и аудита.
- Не реализованы Live/Engineering mode, группировка точек и настройка списка, описанные в расширенном разделе 19 Configuration Manual.
- История открывается по существующим station/point ID; автоматическое построение полной истории по всем протоколам ещё не подключено.
- Пользовательский идентификатор в локальном API пока имеет локальное значение по умолчанию; полноценная аутентифицированная user session/RBAC ещё не интегрирована. Поэтому это не считать готовой многопользовательской системой.
- Полный IQVISION parity не достигнут.

## Проверки DEV52 на текущем этапе
- Базовая DEV51: 1424 теста.
- DEV52 Point List View: 6727 тестов в targeted run, включая 4080 независимых комбинаций фильтра/сортировки/избранного и дополнительные сценарии пагинации, persistence, API, ошибок.
- `compileall` и `node --check` — успешно.
- Раздельная регрессия: базовые тесты DEV51 — 1424 passed; новый набор Point List View — 6727 passed; всего подтверждено 8151 passed при двух отдельных запусках. Единый запуск полного набора в текущей Linux-среде дважды не завершился в лимит времени около 98% прогресса; поэтому не заявляем единый полный прогон как успешный. Windows acceptance пользователя ещё впереди.

## Критерии завершения §5
- Все режимы списка и группировка.
- Безопасная корректировка и override с reason, permissions, audit, interlocks и read-back.
- Журнал adjustment/change details.
- История и schedule из контекста точки.
- CSV round-trip/encoding/large-list checks.
- Windows browser acceptance.
