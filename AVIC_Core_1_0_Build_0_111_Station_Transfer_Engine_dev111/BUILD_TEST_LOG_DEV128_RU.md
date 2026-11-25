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
