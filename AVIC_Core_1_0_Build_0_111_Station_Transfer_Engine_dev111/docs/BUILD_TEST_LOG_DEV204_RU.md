# DEV204 — Point Runtime: станционная изоляция драйверов

## Найденный пробел
Проверка ownership сравнивала ID драйвера с `Device.driver_instance_id`, но не подтверждала, что DriverInstance и Device принадлежат одной станции. Подмена/повреждение owner metadata могла пересечь межстанционную границу.

## Реализовано
- Adapter-originated `publish()` и `mark_quality()` требуют зарегистрированный `DriverInstance`.
- `DriverInstance.station_id` должен совпадать с `Device.station_id`.
- Сохранена независимая проверка точного совпадения `source_driver_id` и Device owner.
- Доверенный внутренний путь без `source_driver_id` оставлен без изменений.

## Регрессионные тесты
- `test_point_runtime_rejects_driver_from_another_station_for_value_and_quality`
- Point Runtime fixtures теперь сохраняют реальный DriverInstance, соответствующий station/device.

## Проверки и ограничения
- Изменения кода и тестов внесены в ветку `ci/fbd-connective-compiler`.
- Локальный pytest не запускался; CI для нового commit должен подтвердить Linux/Windows.
- Физическая BACnet-приёмка не выполнялась.
- Это enforcement на границе публикации Point Runtime; отдельный аудит FBD/Graphics/Historian межстанционных ссылок продолжается.
