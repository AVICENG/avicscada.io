# AVIC Core 1.0 — DEV57 Driver Manager Foundation

## Цель
Начать закрывать главы 1–20 по приоритету пользователя: Trend необязателен; TONN — только ориентир для будущих собственных Linux-контроллеров; остальные инженерные и эксплуатационные разделы продолжают развиваться.

## Изменения DEV57
- Добавлен `DriverManagerService` и сохраняемая сущность `DriverInstance`.
- Каталог доступен через `GET /api/drivers/catalog`.
- Список экземпляров станции: `GET /api/stations/{station_id}/drivers`.
- Создание экземпляра: `POST /api/stations/{station_id}/drivers`.
- Просмотр экземпляра: `GET /api/driver-instances/{instance_id}`.
- Встроенные профили: BACnet/IP, Modbus TCP, необязательный Trend IQ3.
- Каждый новый экземпляр остаётся `STOPPED`, `enabled=false`; запуск и field I/O не реализованы.
- Проверяется доверенный каталог и тип целевого объекта; конфигурация не принимает секреты, для них используется SecretStore.
- Добавлен документ архитектурного направления будущего Linux Controller Agent.

## Проверки
- `python -m compileall -q avic_core tests` — успешно.
- `python -m pytest -q tests/test_driver_manager_dev57.py tests/test_driver_catalog_dev26.py tests/test_graphics_workbench_dev35.py` — **16 passed**.

## Ограничения
DEV57 — первый фундамент Driver Manager, а не завершённый раздел §10. Нет установки внешних пакетов, подписи/верификации модулей, SDK, dependency resolver, форм конфигурации по схемам, polling, subscriptions, discovery jobs, reconnect и полевого управления. Не выполнены полный pytest, Windows acceptance, браузерная приёмка и тесты с физическими контроллерами. TONN и Linux Agent не реализованы. Trend migration/discovery не является приоритетом.

## Готовность
**Частично.** API и сохранение экземпляров работают в целевых тестах. Ни один новый экземпляр не запускается и не связывается с оборудованием автоматически.
