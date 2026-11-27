# DEV205 — Historian: защита межстанционной принадлежности

## Найденный дефект
`HistoryService.append()` принимал произвольные `station_id` и `point_id`. Неверный вызов мог записать измерение точки одной станции в архив другой станции.

## Реализовано
- При наличии Core repository проверяется, что station ID указывает на Station.
- Проверяется, что point ID указывает на Point и связан с существующим Device.
- `Device.station_id` должен точно совпадать с переданным station ID.
- Автономный режим HistoryService без repository оставлен совместимым.

## Регрессионные тесты
- `test_history_append_rejects_cross_station_point_and_accepts_owner_station`
- `test_history_append_rejects_non_point_entity`

## Проверки и ограничения
- Код, тесты и русская документация добавлены в PR.
- Локальный pytest не запускался; требуется CI Linux/Windows.
- Физическая BACnet-приёмка не выполнялась.
