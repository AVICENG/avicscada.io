# DEV115 — BACnet/IP и Modbus TCP Point Runtime adapters

Дата: 2026-11-25  
Ветка: `dev113-network-drivers`  
Статус: реализации добавлены; CI ожидается.

## Реализовано
- BACnet/IP: `BacnetIpPointBinding` + `BacnetIpPointAdapter`, чтение Present_Value через существующий ReadProperty, публикация в общий Point Runtime.
- Modbus TCP: `ModbusTcpPointBinding` + `ModbusTcpPointAdapter`, чтение FC01/02/03/04, декодирование, scale/offset и публикация в Point Runtime.
- Для обоих адаптеров ошибки изолируются по точкам, сохраняется последнее значение, качество переводится в BAD_COMMUNICATION, время последнего успешного образца сохраняется.
- PointRuntime.mark_quality добавлен для корректного изменения качества без подмены значения/времени образца.
- Экспортированы адаптеры из `avic_core.drivers`.
- Добавлены тесты успешного опроса, scaling, потери связи, ownership и валидации адресов.

## Ограничения
- Это однократный polling adapter; полноценный background scheduler, оптимизированная группировка чтения, UI import map, COV, BACnet segmentation/BBMD/FDR и Command Manager не завершены.
- Реальное оборудование не подключалось; используются fake clients в тестах.
- Оба адаптера строго read-only.
- Trend IP/vCNC и остальные семейства ещё не реализованы.

## Проверки
GitHub Actions CI запущен после коммита. Результаты будут внесены после завершения.
