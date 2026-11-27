# Wired M-Bus — проектный план DEV245

Дата: 27.11.2026

Статус: **PLANNED**. В этой версии добавлена запись в каталог и зафиксирована архитектура. Исполняемый M-Bus драйвер, C Worker, сборка libmbus и аппаратные испытания ещё не реализованы.

## 1. Цель и границы первого этапа

Первый этап — read-only сбор данных с проводных M-Bus счётчиков по EN 13757-2/-3.

В область входят:
- последовательный порт через совместимый M-Bus master/converter (USB/RS-232/RS-485 адаптеры — в зависимости от оборудования);
- TCP M-Bus gateways;
- primary address scan и secondary address selection/read;
- запрос и декодирование meter data records;
- передача измерений в AVIC Point Runtime;
- единое качество точки, диагностика, reconnect и журналирование.

Не входят в первый этап:
- Wireless M-Bus (отдельный радиопротокол и отдельный engine);
- изменение конфигурации счётчика, тарифа, адреса и часов;
- запись/управляющие команды;
- vendor-specific команды без отдельного профиля и тестовых векторов.

## 2. Библиотека и языковая стратегия

Основной кандидат — открытая C-библиотека libmbus (upstream: https://github.com/rscada/libmbus). Перед включением в поставку требуется проверить актуальный LICENSE и зависимости непосредственно в выбранном upstream commit.

AVIC не должен переписывать M-Bus codec, если библиотека покрывает нужные link/application layer функции. Наша собственная часть ограничивается:
- C Worker process;
- IPC по существующему Driver SDK contract;
- конфигурацией транспорта и безопасными лимитами;
- переводом M-Bus records в AVIC point values/units/quality;
- диагностикой и lifecycle.

Python-обвязку можно использовать для инженерных сервисов и тестовых инструментов, но полевой wired M-Bus transport предпочтительно изолировать в C Worker на libmbus. Никакого скрытого fallback на самописный Python stack.

## 3. Требования к Worker

### Transport
- serial: порт, baud rate, parity/stop bits — только параметры, реально поддержанные master/converter и библиотекой;
- TCP: host/port, connect/read timeout, reconnect policy;
- bounded frame length, bounded retries и rate limits;
- один владелец serial port на экземпляр шины; конфликтующие процессы/экземпляры должны блокироваться;
- shutdown должен освобождать порт/сокет без зависания.

### Discovery
- primary addressing: ограниченный диапазон и регулируемый темп запросов;
- secondary addressing: поиск только при явном действии инженера и с ограничениями времени/нагрузки;
- обнаруженное устройство не получает выдуманные manufacturer/model значения;
- manufacturer, идентификатор, версия, medium, access number и source/confidence хранятся раздельно;
- повторяющиеся/коллидирующие ответы фиксируются как неоднозначность, а не сливаются.

### Decode
- поддержка форматов и data record functions, которые подтверждены тестовыми векторами;
- корректная обработка BCD, signed/unsigned integers, IEEE float (если заявлен форматом), variable length, storage number, tariff, subunit, unit и multiplier;
- проверка DIF/DIFE и VIF/VIFE цепочек, длины, границ и неизвестных кодов;
- raw record сохраняется в диагностическом контексте, но неизвестный формат не превращается в инженерное число;
- timestamps/access number/status передаются отдельно от значения;
- единицы и множители не угадываются.

## 4. AVIC contracts и безопасность

- driver_id: mbus; protocol: EN 13757-2/-3 wired Meter-Bus.
- Catalog lifecycle остаётся PLANNED, пока Worker, adapter, тесты и сборка не приняты.
- Любые credentials/секреты — только через SecretStore/защищённый механизм SDK; не в driver config и не в IPC payload открытым текстом.
- Все операции первого этапа read-only.
- Ошибка связи переводит затронутые точки в BAD_COMMUNICATION; неверный/неподдержанный record — в BAD_CONFIGURATION либо отдельное диагностическое состояние, если оно будет согласовано с PointQuality contract.
- Последнее известное значение не должно сохранять GOOD после потери связи.
- Нет прямого доступа к физическим командам в обход Core Command Gateway.

## 5. Обязательные тесты до повышения статуса

1. Unit tests для framing, checksums, control/info frames и address encoding.
2. Decoder golden vectors для DIF/DIFE, VIF/VIFE, BCD, integer, signed, variable length, units/multipliers, tariffs и timestamps.
3. Negative tests: truncated frame, invalid checksum, malformed length, unsupported DIF/VIF, duplicate records, bad BCD, overflow.
4. Simulator tests: primary scan, secondary select, timeout, NAK, retry, reconnect, gateway disconnect.
5. IPC tests: lifecycle, sequence/replay rejection, malformed payload, bounded frame, shutdown.
6. Concurrency tests: один serial owner, запрет двойного открытия порта, изоляция разных станций.
7. Build matrix: Linux и Windows (реальные поддерживаемые toolchains), dependency/license audit.
8. Hardware acceptance на нескольких счётчиках разных производителей и минимум одном TCP gateway.
9. Soak test на длительном опросе, проверка потерь/дубликатов и памяти.

## 6. Этапы

- M1 — upstream audit: закрепить commit libmbus, license, API coverage, build prerequisites.
- M2 — standalone C Worker: initialize/configure/start/read/stop и IPC contract.
- M3 — serial + TCP transport tests и emulator fixtures.
- M4 — decoder и normalized meter records.
- M5 — AVIC Point Runtime adapter, quality, discovery and diagnostics.
- M6 — Windows/Linux CI, fault/soak tests, hardware acceptance.
- M7 — только после всех критериев сменить catalog lifecycle с PLANNED на READ_ONLY_TRANSPORT.

## 7. Ссылки

- libmbus upstream: https://github.com/rscada/libmbus
- Каталог протоколов AVIC: avic_core/drivers/catalog.py
- Общий драйверный IPC contract: docs/architecture/DRIVER_SDK_V1_IPC_CONTRACT_RU.md

Наличие библиотеки upstream не является доказательством того, что AVIC драйвер готов. Готовность подтверждается сборкой, тестами, безопасным lifecycle и работой с реальными счётчиками.
