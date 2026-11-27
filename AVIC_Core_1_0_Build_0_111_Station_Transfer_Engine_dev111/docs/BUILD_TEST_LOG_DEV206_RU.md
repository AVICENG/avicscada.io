# DEV206 — FBD: защита межстанционных границ

## Найденные дефекты
- `POINT_INPUT` мог читать Point другой станции, поскольку FBD simulation не сверяла station ID документа и Device точки.
- FBD virtual output мог получить значение или новое quality от стратегии другой станции, если метаданные ссылки были повреждены.

## Реализовано
- FBD `POINT_INPUT` проверяет корректный Device и точное совпадение `Device.station_id` со станцией LogicDocument.
- `publish_fbd()` и `mark_fbd_quality()` требуют station ID вызывающей стратегии.
- Проверяются и `FBDExposedPoint.station_id`, и station ID связанного `LogicDocument`.
- FBD cyclic runtime передаёт свою станцию в публикацию/смену качества.

## Регрессионные тесты
- `test_fbd_point_input_rejects_point_from_another_station`
- `test_fbd_runtime_cannot_publish_or_change_quality_of_foreign_station_virtual_point`

## Проверки и ограничения
- Изменения кода, тестов и документации добавлены в PR.
- Локальный pytest не запускался; требуется полная CI-матрица Linux/Windows.
- Физическая BACnet-приёмка не выполнялась.
