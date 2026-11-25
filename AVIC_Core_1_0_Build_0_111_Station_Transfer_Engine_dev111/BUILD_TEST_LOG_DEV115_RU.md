# DEV115 — Modbus TCP Point Runtime Adapter

Дата: 2026-11-25  
Ветка: `dev113-network-drivers`  
Статус: реализация добавлена; CI ещё не завершён.

## Реализовано
- `ModbusTcpPointBinding`: строгая карта Modbus read points, функции 01/02/03/04, адреса, типы, byte/word order, scale/offset.
- `ModbusTcpPointAdapter`: однократный опрос набора точек, публикация GOOD в общий Point Runtime, изоляция ошибок по точкам.
- При ошибке обмена сохраняется последнее значение, качество переводится в BAD_COMMUNICATION; timestamp последнего успешного образца сохраняется.
- Диагностика успешных/неуспешных опросов.
- PointRuntime.mark_quality для изменения качества без подмены последнего значения.
- Тесты на публикацию, масштабирование, ошибки связи, принадлежность точки драйверу и запрет функций записи.

## Ограничения
- Это polling adapter, не полный lifecycle runtime: нет фонового scheduler, connection pooling, массовой оптимизации диапазонов, UI map importer и field command manager.
- Реальный Modbus TCP endpoint не подключался; проверка идёт на fake transport.
- Никакие write function codes не реализованы.
- BACnet, Trend IP, остальные протоколы пока не доведены до полноценного polling + Runtime adapter.

## Проверки
Ожидается GitHub Actions CI. До завершения CI нельзя считать тесты пройденными.
