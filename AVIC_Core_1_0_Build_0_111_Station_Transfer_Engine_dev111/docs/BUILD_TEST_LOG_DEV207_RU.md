# AVIC Core — журнал сборки DEV207

Дата: 27.11.2026

## Основание
Полный CI run DEV206 (45943059925) завершился ошибкой. Установка зависимостей, pip check и compileall прошли; упали только тесты. Linux/Python 3.12: 12 failed, 31 358 passed. Windows/Python 3.12: 13 failed, 31 356 passed, 1 skipped. Остальные четыре matrix jobs также завершились ошибкой на шаге полного pytest.

## Исправления
- BACnet/IP и Modbus TCP тестовые стенды теперь создают сохранённые DriverInstance, принадлежащие той же станции, что и Device.
- MQTT adapter-level тест использует сохранённый station-owned DriverInstance; при этом production lifecycle MQTT остаётся PLANNED и не выдаётся за реализованный.
- Исправлена неопределённая переменная device в AHU → FBD → Graphics regression test.
- Исправлено ожидание текста исключения в тесте межстанционного FBD POINT_INPUT; защитный контракт кода не ослаблялся.
- License test double дополнен методом assert_feature_enabled().
- Historian API test переведён с фиктивных ID на реальные сохранённые Station, Device и Point.
- Windows ACL test корректно распознаёт SDDL alias LA как built-in Administrator RID 500 только при точном совпадении с SID из whoami; broad Local Account SID S-1-5-113 остаётся запрещённым.

## Безопасность и архитектурные ограничения
- Проверки принадлежности DriverInstance станции сохранены.
- Исторические записи и чтение по-прежнему требуют совпадения Station → Point → Device.
- MQTT не объявляется готовым к запуску через Driver Manager.
- BACnet/IP остаётся READ-ONLY; никаких команд записи в контроллеры не добавлено.

## Проверки
- pip install, pip check, compileall: в предыдущем CI прошли.
- Полный pytest после DEV207: ожидает новый CI run; результат НЕ ПОДТВЕРЖДЁН.
- Аппаратная приёмка BACnet на Trend-контроллере: НЕ ВЫПОЛНЕНА.

## Готовность
DEV207 — исправление тестовых фикстур и совместимости регрессионного набора с усиленными контрактами. Готовность не повышается до завершения всех Linux/Windows jobs и дальнейшей аппаратной приёмки.
