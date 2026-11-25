# AVIC Core 1.0 — DEV113. Журнал сборки и проверок

## Назначение

DEV113 начинает нормализацию сетевой архитектуры для трёх самостоятельных драйверов: Trend IP / IQ Network, BACnet/IP и Modbus TCP. Основа ветки — DEV112.

## Реализовано в первом инкременте

- Создана отдельная рабочая ветка `dev113-network-drivers` от `dev112-station-transfer-reliability`. DEV112 и main не изменялись.
- Добавлен `docs/NETWORK_DRIVERS_AUDIT_DEV113_RU.md` с аудитом фактических исходников, материалов IQVISION/SET/963, требованиями к BACnet/Modbus и планом Trend IP.
- Каталог драйверов приведён к целевой продуктовой модели:
  - `trend-ip` — отдельный Trend vCNC over TCP, пока PLANNED без ложных read/discovery capabilities;
  - `bacnet-ip` — общий BACnet/IP, включая Trend-контроллеры с BACnet;
  - `modbus-tcp` — общий Modbus TCP.
- Удалена отдельная запись `trend-iq3-bacnet`: это профиль/инспекция внутри общего BACnet, а не самостоятельный сетевой драйвер.
- Добавлены/обновлены тесты точного состава каталога и честных capability states.
- Версия пакета изменена на `1.0.0.dev113`.

## Что ещё не реализовано

- Trend TCP vCNC codec, session negotiation и secure vCNC.
- Реальное Trend Site/LAN/device/point discovery.
- BACnet polling/COV, ReadPropertyMultiple, segmentation, BBMD/Foreign Device Registration, PointRuntime adapter.
- Modbus register-map import, polling scheduler, PointRuntime adapter.
- Общий Command Manager и безопасная запись в полевые устройства.
- SET XML migration и 963 schematic migration.
- Реальная приёмка на Trend vCNC, BACnet и Modbus оборудовании.

## Проверки

- В этом инкременте локальные pytest / compileall / pip check не запускались.
- GitHub Actions для DEV113: ожидается запуск/результат CI после коммитов.
- Предыдущий DEV112 CI завершился с одной Windows-only ошибкой в тестовом ожидании ACL (ожидалось 3 ACE, Windows runner вернул 4: OW, SY, BA, LA); Linux matrix прошла. Этот DEV112 результат не переносится на DEV113.

## Статус готовности

**DEV113-A — подготовка каталога и аудит выполнены в коде/документации. Не является готовым Trend/BACnet/Modbus production driver и не готов к полевой эксплуатации.**

Для полноценного Trend IP codec требуется официальная протокольная спецификация/SDK либо разрешённый тестовый интерфейс с проверенными test vectors. Нельзя выдумывать формат кадров или обходить secure vCNC.
