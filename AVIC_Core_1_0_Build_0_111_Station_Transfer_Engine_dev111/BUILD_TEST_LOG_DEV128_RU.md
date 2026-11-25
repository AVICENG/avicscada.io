# AVIC Core 1.0 — DEV128: Driver Audit and Lifecycle Corrections

## Изменения
- Исправлена остановка драйверов при остановке отдельной станции.
- Диагностика показывает фактическое состояние polling worker, а не только устаревшее сохранённое состояние.
- Осиротевший после рестарта процессный runtime отображается как ORPHANED.
- Разделены признаки field_read_enabled и field_write_enabled; команды записи не добавлены.
- MQTT снят с уровня реализованных драйверов до завершения runtime factory, SecretStore wiring и TLS-политики.

## Тесты
- Добавлены тесты на DEGRADED, ORPHANED и station-scoped driver shutdown.
- CI для DEV128 запускается после публикации коммита; результаты будут указаны только после завершения всех матриц Python/OS.

## Ограничения
- Нет hardware acceptance для BACnet/IP и Modbus TCP.
- Нет production runtime для MQTT, OPC UA, SNMP, KNXnet/IP, LonWorks, oBIX и Haystack.
- Trend IP/vCNC требует подтверждённого описания wire protocol и испытаний на контроллере Trend.
- См. docs/DRIVER_AUDIT_DEV128_RU.md.

## Дополнительная проверка CI DEV127
- Linux Python 3.11/3.12/3.13: полный набор прошёл.
- Windows Python 3.13: 31 178 passed, 1 skipped, 1 failed. Причина — ACL для HostIdentity: комбинированный icacls grant не создавал ACE текущего SID и оставлял Local Account. Исправление включено в DEV128; повторный Windows CI обязателен.

## DEV129 — дополнительное усиление безопасности
- Расширена нормализация ключей в рекурсивном фильтре секретов конфигурации драйверов.
- Добавлены тесты для api_key, mqtt_password, oauth_refresh_token, tls_private_key и clientKey.
- Результаты CI DEV128 ещё ожидаются; DEV129 будет проверяться отдельным запуском.

## DEV130 — API runtime управления
- Добавлены API-маршруты POST start/stop и GET diagnostics для экземпляров драйверов.
- Добавлены проверки Origin guard, успешного запуска, диагностики и остановки fake adapter.
- CI DEV130 должен подтвердить результат на Windows и Linux; до завершения матрицы зелёный статус не заявляется.

## DEV131 — Modbus TCP grouped polling
- Реализовано объединение соседних bindings по FC01/02/03/04 с соблюдением лимитов протокола.
- Добавлен регрессионный тест: два смежных holding registers читаются одним запросом.
- Полная CI-матрица DEV131 ожидается; результат не заявлен до завершения.

## DEV132 — BACnet/IP protocol hardening
- Добавлена сериализация операций одного BACnet/IP client.
- Ужесточена проверка источника ReadProperty response до точного IP:port.
- Добавлена явная ошибка для сегментированного ComplexACK и два регрессионных теста.
- CI DEV132 ожидается.

## DEV133 — согласование Driver Manager
- Восстановлена единая версия manager.py с DEV128 state diagnostics, station stop и DEV129 secret filter.
- Исправлена совместимость остановки runtime station, не имеющей предварительной inventory-записи.
- Factory registration блокируется только для того driver_id, чья сессия активна.
- Добавлены регрессионные тесты на factory scope и секретные aliases.

## DEV134 — проверка содержимого Git tree
- Проверены не только пути, но и фактическое содержимое Git blob по SHA.
- Исправлены некорректные blob-объекты DEV133 для manager.py и test_driver_manager_dev57.py; в DEV134 восстановлены полные файлы.
- Обязательная проверка CI DEV134 остаётся открытой.

## DEV135 — polling state and secret aliases
- PollingSession.start ждёт фактического запуска worker.
- list_instances показывает эффективный runtime state и persisted_state отдельно.
- Дополнены aliases фильтра секретов и тесты.
- CI DEV135 ожидается.

## DEV136 — исправления CI DEV134
- DEV134 Linux Python 3.12/3.13 выявил 3 тестовые ошибки: 2 BACnet теста имели двойное экранирование байтовых литералов; каталог-тест ожидал MQTT как read_supported после перевода MQTT в PLANNED.
- Исправлены литералы и ожидание read-capability. Реальный MQTT runtime не рекламируется.
- Повторная CI DEV136 обязательна; результат ещё не получен.
