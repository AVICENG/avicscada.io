# DEV114 — дерево драйверов и модель лицензирования AVIC

Дата: 2026-11-25  
Основа: DEV113, ветка `dev113-network-drivers`  
Статус: реестр и проектная структура; кроме отмеченных read-only основ, реализации не завершены.

## 1. Исключённые семейства

По решению владельца продукта не разрабатываются и не включаются в каталог:
- Niagara Fox;
- CCN;
- Andover;
- N2.

Наличие одноимённых модулей в архиве Niagara не является основанием для разработки.

## 2. Дерево Network & Drivers в AVIC Engineering Workbench

```text
Network & Drivers
├── Trend
│   └── Trend IP / IQ Network (vCNC)
├── Building Automation
│   ├── BACnet
│   │   ├── BACnet/IP
│   │   └── BACnet MS/TP
│   ├── LonWorks
│   │   └── Manufacturer / Device Profiles
│   └── KNX
│       └── KNXnet/IP (EIB)
├── Industrial
│   ├── Modbus
│   │   ├── Modbus TCP
│   │   └── Modbus RTU
│   └── SNMP
├── Integration
│   ├── MQTT
│   ├── OPC
│   │   ├── OPC UA Client
│   │   ├── OPC UA Server
│   │   └── OPC Classic DA Gateway (legacy / Windows)
│   ├── oBIX
│   └── AVIC REST API
└── Semantic & Metadata
    └── Project Haystack
```

Это логическое дерево каталога. Встраивание его в видимый UI Tree — отдельная задача интерфейса; данный коммит не заявляет, что экран уже реализован.

## 3. Реестр и фактический статус

| Драйвер | Статус на DEV114 | Лицензионный ключ |
|---|---|---|
| Trend IP / vCNC | Planned; приоритет №1 | `driver.trend-ip` |
| BACnet/IP | Read-only transport foundation | `driver.bacnet-ip` |
| BACnet MS/TP | Planned | `driver.bacnet-mstp` |
| Modbus TCP | Read-only transport foundation | `driver.modbus-tcp` |
| Modbus RTU | Planned | `driver.modbus-rtu` |
| LonWorks | Planned; единый драйвер + профили производителей | `driver.lonworks` |
| KNXnet/IP | Planned | `driver.knxnet-ip` |
| MQTT | Planned | `driver.mqtt` |
| OPC UA Client | Planned | `driver.opc-ua-client` |
| OPC UA Server | Planned | `driver.opc-ua-server` |
| OPC Classic DA Gateway | Planned; legacy Windows bridge | `driver.opc-da-gateway` |
| oBIX | Planned | `driver.obix` |
| SNMP | Planned | `driver.snmp` |
| Project Haystack | Planned semantic integration | `driver.haystack` |
| AVIC REST Integration | Planned | `driver.rest-api` |

В каталоге только BACnet/IP и Modbus TCP сохраняют ограниченные read-only транспортные возможности, которые уже существуют в коде. Ни один драйвер не рекламирует запись. Trend IP пока не реализован.

## 4. Правила дерева и профилей

- Один протокол — один драйверный движок; производители и модели представлены профилями, а не копиями транспортного драйвера.
- LonWorks vendor modules из Niagara не превращаются в сотни отдельных драйверов AVIC.
- KNXnet/IP и EIBnet/IP рассматриваются как одна ветвь KNX/IP, не дублируются.
- Haystack — семантический слой и модель тегирования, а не транспорт.
- OPC Classic DA изолируется в отдельном Windows gateway process; не встраивать COM/DCOM в ядро.
- MQTT Sparkplug B может быть отдельным профилем поверх MQTT, а не дублирующим транспортом.
- Каждый адаптер публикует точки в общий Point Runtime с неизменяемым UID.
- Потеря связи меняет качество точки; последнее значение не превращается в GOOD.
- Все команды записи — только через отдельный Command Manager, RBAC, разрешения, диапазоны, interlocks, read-back и аудит.

## 5. Лицензирование

Каждая запись имеет стабильный feature key `driver.<driver-id>`. Это ключ для будущей интеграции с AVIC License Manager, а не действующая проверка лицензии в этом коммите.

Предлагаемая модель:
- базовая поставка содержит AVIC Core и каталог;
- лицензия включает конкретные драйверы или пакеты;
- лицензия привязана к установке / Host ID согласно общей модели AVIC;
- лицензия определяет право активировать драйвер, но не изменяет данные проекта и UID точек;
- инженер видит драйверы, статус, причину недоступности и требуемую лицензию;
- обнаружение и неиспользуемые точки сами по себе не должны расходовать лимит точек;
- режим trial/evaluation, срок действия, обновление, отзыв и офлайн-подпись должны проверяться License Manager;
- отключение/истечение лицензии не должно молча удалять устройства, конфигурацию или историю.

Нельзя считать коммерческую блокировку реализованной до интеграции с License Manager и тестов обхода/отказа/истечения/переноса лицензии.

## 6. Правовой и технический периметр

AVIC реализует протоколы независимо по опубликованным стандартам, открытым спецификациям и разрешённой документации. Не переносим исходный код, бинарные компоненты, внутренние классы, ключи, сертификаты или закрытые алгоритмы Niagara. Для каждого протокола ведём список нормативных источников, версий, обязательных профилей и тестовых векторов.

## 7. Порядок реализации

1. Trend IP / vCNC — выяснение доступной спецификации и read-only испытание на IQ3.
2. Доведение BACnet/IP и Modbus TCP до polling + Point Runtime adapter + reconnect/quality.
3. BACnet MS/TP и Modbus RTU — общий Serial Bus Manager.
4. LonWorks и KNXnet/IP.
5. MQTT, OPC UA Client/Server.
6. SNMP, oBIX, Haystack и REST.
7. OPC DA gateway — отдельный Windows compatibility package.

Готовность каждого драйвера подтверждается протокольными тестами, тестами ошибок, нагрузкой, безопасностью, документацией и испытанием с независимым сервером или реальным устройством.

## 8. Границы DEV114

DEV114 добавляет дерево/реестр, категории, license feature keys и тесты каталога. Он не реализует протокольные клиенты, пользовательский экран дерева, выдачу лицензий или реальное коммерческое ограничение.
