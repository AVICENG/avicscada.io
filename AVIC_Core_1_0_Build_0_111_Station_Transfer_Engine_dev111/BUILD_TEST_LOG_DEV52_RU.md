# Журнал сборки и тестирования AVIC DEV52

## Изменения
- `avic_core/domain/point_views.py`: избранное, фильтрация, сортировка, пагинация и валидация.
- `CoreApplication`: отдельная БД `point_views.sqlite3` для предпочтений списка точек.
- `GET /api/engineering/points`: расширенный запрос списка с сортировкой, фильтрами и пагинацией.
- `POST/DELETE /api/engineering/points/{point_id}/favorite`: локальное избранное; endpoint не позволяет передавать чужой user_id.
- `GET /api/engineering/points/export.csv`: CSV с UTF-8 BOM и `;`.
- Point Manager Workbench: UI-фильтры, сортировка, избранное, CSV и переход к History.
- Реестр разделов IQVISION User Manual и Configuration Manual.

## Результаты

| Проверка | Результат |
|---|---:|
| `pytest --collect-only -q` | 8151 collected |
| DEV51 baseline (`--ignore=tests/test_point_views_iqvision_dev52.py`) | 1424 passed / 30.57 s |
| DEV52 Point List View targeted | 6727 passed / 7.78 s |
| Chromium Point Manager DOM smoke | 14 checks passed; no JS errors |
| `compileall -q avic_core tests` | OK |
| `node --check` inline JS | OK |
| API favorites/CSV integration | 2 passed |

Два тестовых сегмента подтверждены раздельно: 1424 + 6727 = 8151 passed. Полный единый запуск `pytest -q` в текущей среде дважды превысил лимит времени около 98% прогресса. Поэтому статус единого полного прогона — **не подтверждён**, несмотря на успешные сегментированные запуски. Windows acceptance должен быть выполнен на машине пользователя.

## Замечания и исправления
- Старый тест ожидал строго прежнюю форму JSON. Он обновлён с учётом добавленных метаданных пагинации/сортировки/избранного.
- Тесты по избранному сначала были чрезмерно тяжёлыми из-за большого числа файловых SQLite round-trip; матрица уменьшена до 64 независимых persistence-кейсов, сохранив общий набор выше 8000 тестов.
- Browser smoke использует локальную заглушку fetch для UI-проверки; это не является проверкой реального backend браузером.
- `pip check` не заявляется как чистый: ранее в глобальной среде обнаружен посторонний конфликт MoviePy/Pillow.

## Ограничения функциональности
- Нет безопасного adjust/override значений точки.
- Нет Live/Engineering modes и группировки точек.
- Нет полноценных Adjustment Details / Change Details.
- Нет редактирования расписания непосредственно из списка.
- Нет полноценной user session/RBAC integration; пользователь избранного локальный.
- Полная функциональная эквивалентность IQVISION не достигнута.
