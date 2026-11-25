# DEV140 — общий импорт точек протоколов в AVIC Core

## Цель

Свести результаты обнаружения BACnet/IP, Modbus TCP и следующих драйверов к единому контракту импорта. Импорт создаёт обычные сущности AVIC `Device` и `Point`; протокол не меняет способ подключения точки к Point Runtime, FBD, Graphics и Web Pages.

## Что добавлено

- `ProtocolDeviceImportService` — общий сервис предварительной проверки и транзакционного импорта.
- Нормализованный вход: `protocol`, `network_id`, `device`, `points[]`.
- Проверка экземпляра драйвера и принадлежности целевой станции.
- Проверка уникальности native identity, типа данных, явно заданного направления, длины метаданных и выбранных точек. Поддержаны BACnet analog/binary/multi-state и Modbus scalar-типы (uint16/int16/uint32/int32/float32/float64 и др.).
- Предпросмотр новых и уже импортированных точек без записи в БД.
- Импорт Device + Point в одной SQLite-транзакции.
- Идемпотентный повторный импорт: существующие точки пропускаются, новые добавляются.
- HTTP API:
  - `POST /api/stations/{station_id}/protocol-devices/import-preview`
  - `POST /api/stations/{station_id}/protocol-devices/import`

## Контракт discovery

```json
{
  "protocol": "modbus/tcp",
  "network_id": "lan-01",
  "device": {
    "native_identity": "modbus/tcp:device:10.20.0.15",
    "address": "10.20.0.15:502",
    "name": "Controller",
    "manufacturer": "Vendor",
    "model": "Model",
    "identity_sources": {"manufacturer": "discovery response"}
  },
  "points": [
    {
      "native_identity": "modbus:holding-register:40001",
      "name": "Supply temperature",
      "data_type": "float",
      "unit": "°C",
      "direction": "input",
      "object_type": "holding-register"
    }
  ]
}
```

BACnet использует `bacnet/ip`, Modbus TCP — `modbus/tcp`. Идентификаторы устройств и точек формирует discovery/mapper соответствующего протокола; общий импорт не выдумывает адреса или типы.

## Инварианты безопасности

- Сервис импорта не открывает сокеты и не выполняет discovery.
- Сервис не отправляет команды полевому оборудованию.
- Импорт возможен только в станцию, которой принадлежит выбранный DriverInstance.
- Протокол inspection обязан совпасть с протоколом DriverInstance.
- Направление каждой точки обязательно задаётся discovery/profile mapper; сервис не угадывает INPUT/OUTPUT по адресу. Выходные точки сохраняются с направлением OUTPUT, но это не включает запись в контроллер.
- Новые точки получают качество UNCERTAIN до первого корректного измерения.
- Импорт не подменяет и не переносит существующий Device между экземплярами драйвера.
- Существующая BACnet-специализированная операция сохранена для обратной совместимости.

## Ограничения DEV140

- Нормализатор результатов discovery пока не подключён автоматически к каждому сетевому мастеру; текущий API принимает уже подготовленный inspection. Для Modbus TCP карта регистров формируется инженером/профилем: протокол не предоставляет универсальный перечень тегов.
- Реальные Modbus register maps должны быть созданы инженером/профилем устройства. Нельзя угадывать единицы, scale, data type или направление из номера регистра.
- Trend IP остаётся PLANNED: общий импорт не реализует Trend vCNC wire codec.
- MQTT, OPC UA, SNMP, KNX и другие протоколы не становятся реализованными от наличия общего контракта; для каждого нужны собственные discovery/adapter и end-to-end тесты.
- Автоматический запуск драйвера после импорта запрещён. Runtime стартует отдельно после проверки конфигурации.

## Проверки

Новый набор `tests/test_protocol_point_import_dev140.py` проверяет preview без мутаций, идемпотентность, BACnet и Modbus типы, изоляцию станции, отказ при неверном протоколе/дублирующемся native identity/неуказанном направлении, API, а также путь одной импортированной точки через Point Runtime → FBD → Graphics binding → Web Page value binding. Дополнительно проверяются диапазоны Modbus integer-типа в Point Runtime.
