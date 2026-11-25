# Driver Manager DEV57 — инвентаризация и безопасное создание экземпляров

## Что реализовано
- Каталог встроенных профилей BACnet/IP, Modbus TCP и необязательного Trend IQ3.
- Просмотр каталога через `GET /api/drivers/catalog`.
- Создание и хранение экземпляра драйвера в конкретной станции: `POST /api/stations/{station_id}/drivers`.
- Просмотр списка: `GET /api/stations/{station_id}/drivers`; карточка: `GET /api/driver-instances/{instance_id}`.
- Экземпляр создаётся только в состоянии `STOPPED`, `enabled=false`; полевая связь и запуск не включаются.
- Проверяется принадлежность станции и наличие драйвера в доверенном встроенном каталоге.
- Секреты запрещено помещать в обычный config; для них предназначен SecretStore.
- Мутации API проходят локальный Origin/loopback guard.

## Как проверить через HTTP
1. Откройте `GET /api/drivers/catalog` и выберите `driver_id`.
2. Создайте экземпляр POST-запросом на `/api/stations/{station_id}/drivers` с JSON `{"driver_id":"bacnet-ip","name":"BACnet LAN","config":{"interface_id":"eth0"}}`.
3. Убедитесь, что ответ содержит `state=STOPPED`, `enabled=false`, `field_io_enabled=false`.
4. Откройте список экземпляров станции и убедитесь, что запись сохраняется.

## Ограничения
Это пока не полноценный пакетный менеджер и не исполняемый драйверный runtime. Нет установки сторонних пакетов, проверки цифровой подписи модулей, dependency resolver, конфигурационных схем драйверов, polling/subscriptions, активного discovery, reconnect и команд записи. Trend оставлен необязательным профилем. TONN не реализован: для будущих Linux-контроллеров AVIC предусмотрено направление отдельного адаптера/протокола, но текущий код не заявляет совместимость с TONN.


## DEV124 — runtime lifecycle Driver Manager

- DriverManagerService теперь владеет зарегистрированными adapter factories, PollingSession, стартом/остановкой и диагностикой экземпляров.
- Встроены безопасные фабрики BACnet/IP и Modbus TCP: создание клиента и адаптера выполняется только при явном start_instance; конфигурация валидируется, binding создаётся из явно заданного списка.
- Состояния экземпляра персистентны: STARTING/RUNNING/ERROR/STOPPED; optimistic version check при изменениях. CoreApplication останавливает активные драйверы при shutdown.
- UI использует единственный CoreApplication.driver_manager, а не создаёт отдельный менеджер с независимым состоянием.
- MQTT остаётся подписочным адаптером; его Paho factory пока должна быть зарегистрирована отдельным runtime-пакетом с TLS/SecretStore wiring. Каталог показывает runtime_start_supported отдельно от read_supported.
- Вложенные секреты запрещены рекурсивно.
- Добавлены тесты lifecycle/factory, persisted state, close и secret rejection.
- Это первый runtime lifecycle слой, не финальный промышленный Driver Manager: пока нет recovery после аварийного завершения процесса, лицензирования пакетов, heartbeat/watchdog и UI настройки параметров.
