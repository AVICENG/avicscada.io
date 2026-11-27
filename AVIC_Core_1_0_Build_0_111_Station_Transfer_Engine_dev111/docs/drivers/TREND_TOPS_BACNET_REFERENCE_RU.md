# Trend TOPS и BACnet: инженерные выводы для AVIC

Дата исследования: 27.11.2026

## 1. Краткий вывод

Предоставленный пользователем учебный материал **IQ-BACnet Module 3 – 963v3.01 and TOPS** подтверждает важную архитектурную идею: TOPS — не просто BACnet-драйвер. Это шлюз-посредник, который обнаруживает BACnet-устройства и их объекты, отображает их в виртуальные Trend-устройства, группирует их в виртуальные Trend LAN и публикует их через Trend vCNC так, чтобы 963 видел их как обычные Trend-устройства.

Для AVIC это даёт два самостоятельных направления:

1. **BACnet как полноценный нативный протокол AVIC** — обнаружение, объекты/точки, чтение, запись через защищённый Command Gateway, COV, тревоги, расписания и Trend Log.
2. **Trend IP/vCNC driver** — отдельный драйвер для подключения к Trend IQ LAN и чтения/обмена с Trend-контроллерами по Trend-протоколу.

Не следует смешивать эти два направления. TOPS использует BACnet на южной стороне, но его интерфейс к 963 — Trend vCNC/Trend addressing, а не BACnet.

## 2. Что подтверждает учебный материал пользователя

В презентации Trend, редакция курса 2008 года, описан следующий поток:

- TOPS устанавливается на Windows PC; 963 может запускать и останавливать локальный TOPS либо подключаться к TOPS на отдельном PC по IP.
- В 963 TOPS добавляется как Remote Site с IP Connection; в примере Start Port и End Port равны 10101.
- TOPS настраивает BACnet network driver: сетевой адаптер, IP, уникальный BACnet Device Instance и BACnet Network Number.
- TOPS выполняет BACnet discovery сторонних устройств.
- Инженер создаёт Virtual Trend LANs, назначает найденные BACnet-устройства в LAN и задаёт каждому Trend-адрес/метку.
- После этого 963 учит TOPS site и получает устройства/метки как Trend-объекты.
- В курсе приведено соответствие: BV→Switch, BI→Digital Input, BO→Digital Driver, AV→Knob, AI→Sensor, AO→Analog Driver.
- TOPS schedules могут быть переданы в 963 и связаны с Diary groups; для тревог TOPS должен быть добавлен получателем в BACnet Notification Class устройства.
- В самом учебном материале есть оговорка: IQ3 BACnet controllers не обнаруживаются на этапе discovery «non-IQ» устройств. Это не следует трактовать как отсутствие BACnet в Trend IQ3; это особенность описанного сценария обнаружения и разделения IQ/third-party устройств.

Презентация содержит уведомление о copyright Honeywell/Trend. Она используется здесь как источник требований и терминов, а не как разрешение копировать программную реализацию или закрытые материалы.

## 3. Что добавляет публичная документация TOPS

Публичный Data Sheet **TA201049 Issue 8, 16-May-2016, applies to TOPS 3.21** подтверждает:

- TOPS поддерживает Standalone и Bound modes.
- В Standalone режиме доступ идёт через собственный vCNC TOPS; в Bound режиме TOPS включается в существующую Trend IQ network.
- BACnet objects отображаются в Trend modules; mapping можно редактировать.
- AI→Sensor; AO→Analogue Driver; AV→Knob; BI→Digital Input; BO→Digital Driver; BV→Switch.
- BACnet Schedule→Trend Time Zone; TOPS в этой версии поддерживает только Boolean schedules.
- BACnet Trend Log→Trend Plot, с чтением Buffer_Size, Record_Count, Total_Record_Count, Log_Buffer, Log_Interval и полей уведомлений.
- BACnet alarms из Notification Classes преобразуются в Trend alarms.
- В TOPS описан обмен IC comms между IQ3/IQ4 и сторонними BACnet-устройствами.
- Возможность чтения/записи в TOPS не означает, что AVIC должен включать запись по умолчанию: для AVIC записи остаются только через Command Gateway, RBAC, аудит, проверку качества и явную политику устройства.

Важно учитывать версии: учебный материал 963v3.01 старше Data Sheet TOPS 3.21 и раннего PICS. Утверждения о Trending и конкретных BIBB нельзя переносить между версиями без проверки.

## 4. Архитектура AVIC: два драйвера

### A. AVIC BACnet/IP Driver

Это нативный BACnet драйвер, который общается напрямую с BACnet/IP устройствами и маршрутизаторами:

- Who-Is / I-Am discovery, Device Object, Vendor ID, Model Name, Firmware Revision.
- Object_List и типизированная инвентаризация объектов.
- ReadProperty и ReadPropertyMultiple с корректной обработкой сегментации, ошибок, массива и качества данных.
- COV Subscribe/Unsubscribe и обработка уведомлений — следующий этап после устойчивого polling.
- Notification Class / Event Enrollment / Event Notifications — тревоги.
- Schedule / Calendar / Weekly_Schedule / Exception_Schedule — расписания с типами и календарными исключениями.
- Trend Log / Trend Log Multiple — архивы, буферы, временные метки, rollover и чтение по диапазону.
- WriteProperty — только отдельным этапом через Command Gateway; приоритет BACnet, feedback readback, подтверждение и аудит обязательны.
- BACnet/IP, BBMD/Foreign Device и маршрутизация должны проектироваться отдельно от локального broadcast discovery.

Текущий AVIC BACnet код уже содержит BVLC/NPDU/APDU разбор, Who-Is/I-Am и безопасный read-only путь. Это хорошая основа, но ещё не эквивалент TOPS: требуется полный object/property model, полноценный RPM, COV, alarms, schedules, Trend Log и отдельный управляемый write path.

### B. AVIC Trend IP / vCNC Driver

Это самостоятельный транспорт и протокол для Trend IQ network:

- Конфигурация: IP/hostname контроллера или устройства с vCNC, TCP port, LAN, vCNC address/outstation, тип/поколение контроллера.
- Подключение к vCNC и поддержание сессии, reconnect/backoff, response timeout, диагностика и журнал сырых кадров для инженерного режима.
- Discovery устройств, LAN, outstation и доступных адресов/модулей.
- Чтение Trend modules/parameters и нормализация в AVIC Point Runtime.
- Обработка unsolicited messages и alarm delivery.
- Secure vCNC — отдельный обязательный режим для поддерживаемых контроллеров; не понижать автоматически до незашифрованного режима.
- Транспортный порт нельзя жёстко зашивать как 10101: это пример TOPS/одного vCNC. В IP Tool описаны пользовательские vCNC ports и соглашение 10000 + network address для автонумерации.

Публичная документация стороннего коннектора Desigo Optic раскрывает формат Trend URI:
`trend-tcp://deviceAddress/deviceType/deviceOutstation/vcncPort/vcncOutstation/lan`.
Пример: `trend-tcp://192.168.64.121/4/71/10101/101/1`.
Это полезно как подтверждение полей адресации, но не раскрывает бинарный wire protocol и не является спецификацией реализации.

### C. Совместимость с TOPS как отдельный режим

Позже AVIC может поддержать два сценария:

1. AVIC напрямую подключается к BACnet сети — без TOPS.
2. AVIC Trend driver подключается к TOPS vCNC и видит BACnet-объекты, которые TOPS уже отобразил в виртуальные Trend devices.

Второй сценарий позволит AVIC использовать существующую установленную инфраструктуру TOPS/963 и сравнивать результаты Trend mapping с нативным BACnet драйвером. Но это не заменяет прямой BACnet driver и не даёт автоматически доступ к исходным BACnet объектам/сервисам за пределами отображения TOPS.

## 5. Сопоставление BACnet object → AVIC point

| BACnet object | TOPS/Trend представление | Рекомендуемая AVIC модель |
|---|---|---|
| AI | Sensor | Analog Input, read-only |
| AO | Analog Driver | Analog Output, commandable |
| AV | Knob | Analog Value, commandable |
| BI | Digital Input | Binary Input, read-only |
| BO | Digital Driver | Binary Output, commandable |
| BV | Switch | Binary Value, commandable |
| MSI | Sensor | Multi-state Input, read-only |
| MSO | Analogue Driver | Multi-state Output, commandable |
| MSV | Knob | Multi-state Value, commandable |
| Schedule | Time Zone | Schedule object + weekly/exception schedule |
| Trend Log | Plot | Historian source / log buffer |

Mapping не должен терять исходный BACnet Object Identifier, Property Identifier, device instance, units, state text, priority array, relinquish default и статус качества. Trend-модуль — представление, а не замена нативной BACnet identity.

## 6. PICS и сервисы: не копировать упрощённую матрицу

В публичном PICS 963 + TOPS TP201011 (2009, TOPS Iss 2.00, BACnet protocol revision 4) перечислены DS-RP-A, DS-RPM-A, DS-WP-A, DS-WPM-A, AE-N-A, SCHED-A, T_ATR_A и DM-DDB-A.

В IQVISION PICS TP201384 (2018, protocol revision 14) перечислены более широкие профили: DS-RP/RPM/WP/WPM, COV, device/network management, alarm/event, trending и scheduling. Это другой продукт и более поздний стек; использовать как целевую матрицу AVIC, но не приписывать эти функции старому TOPS.

## 7. План разработки драйвера

Приоритеты:

1. **BACnet object inventory**: Object_List, все основные object types, свойства и metadata, стабильная идентичность и vendor/model provenance.
2. **Point binding engine**: выбор BACnet object/property → AVIC point type, единицы, state text, engineering limits; импорт/экспорт bindings.
3. **RPM reliability**: сегментация, invoke ID, тайм-ауты, partial results, Error/Reject/Abort, fallback на RP без потери данных.
4. **COV**: subscribe lifetime, renewal, confirmed/unconfirmed notifications, resubscribe after reconnect, fallback polling.
5. **Alarms**: Notification Class recipients, Event Notification, ack/transition, event timestamps, source and priority.
6. **Schedules**: weekly schedule, exception schedule, calendar, priority and readback; не ограничиваться Boolean schedules TOPS 3.21.
7. **Trend Log**: readRange, buffer handling, record timestamps, rollover, notification thresholds.
8. **Command Gateway**: только после тестов и аудита; BACnet priority array/relinquish, command feedback и explicit permissions.
9. **Trend vCNC**: отдельный протокольный research spike с packet capture на разрешённой лабораторной сети и тестом против реального Trend controller/TOPS. Не писать протокол по догадкам.

## 8. Безопасность и ограничения

- Старый TOPS учебный материал указывает default admin/blank password для web UI — это историческая настройка учебной версии, не использовать как безопасный default AVIC.
- Trend security guidance требует Secure Mode для vCNC там, где он поддерживается; не публиковать IQ controllers напрямую в Internet, использовать VPN и сетевые ACL.
- AVIC discovery должен быть ограниченным и наблюдаемым; никакого автоматического BACnet WriteProperty, time sync, reinitialize или device configuration во время обнаружения.
- Все источники/версии и уверенность определения устройства должны храниться отдельно. Не угадывать vendor/model.
- Нельзя считать TOPS PICS подтверждением совместимости AVIC: это требования/референс для собственного набора испытаний.

## 9. Источники

1. Пользовательский файл: *IQ-BACnet Module 3 – 963v3.01 and TOPS features and enhancements*, Trend Control Systems, course revision 001 (2008), передан пользователем в этой беседе.
2. Honeywell/Trend, TOPS Open Protocol Server product page: https://buildings.honeywell.com/ca/en/products/by-category/software/building-control-software/building-control-drivers/tops-open-protocol-server
3. Trend TOPS Data Sheet TA201049 Issue 8 (16-May-2016, TOPS 3.21), публичная копия: https://studylibfr.com/doc/10072153/en-ta201049-uk0yr0516h--1-
4. 963 and TOPS BACnet PICS TP201011 Issue 2 (19-Jan-2009): https://www.manualsdir.com/manuals/353991/trend-963-and-tops.html
5. IQVISION BACnet PICS TP201384 Issue 1 (28-Aug-2018): https://www.bacnetinternational.net/catalog/manu/trend%20control%20systems/en-tp201384-uk8pr0818a.pdf
6. Trend IP Tool Manual TE200638 Issue 7 (25-Nov-2024): https://device.report/m/ccc7d5e3ac5218e93e7ec1a82477e1a1ea29745af2cff46896df658ae6678b99_optim.pdf
7. Siemens Desigo Optic Trend VCNC URI reference: https://sid.siemens.com/r/A6V11890771/16318755339___en-US_31687616907?contentId=QEA60hQqvFkoNi_btcLhFQ
8. Trend Security Best Practice TP201331: https://prod-edam.honeywell.com/content/dam/honeywell-edam/hbt/en-us/documents/manuals-and-guides/cyber-security-manuals/trends/hon-ba-bms-en-tp201331-uk8pr1224n.pdf?download=false
9. Trend IQVISION Configuration Manual TE201382 Issue 4 (13-Feb-2017): https://autorem.fr/Docs/Trend/IqVision/En_Conf_IQVISION.pdf

---
Статус: исследование и архитектурные требования. Это не утверждение о реализации Trend vCNC в AVIC и не подтверждение аппаратной совместимости.
