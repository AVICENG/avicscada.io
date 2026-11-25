# KNX в AVIC — план интеграции DEV142

KNXnet/IP — приоритетный протокол автоматизации зданий. Реализация независимая, по открытым спецификациям KNXnet/IP и DPT; закрытый код Niagara не используется.

## Этапы
1. KNXnet/IP framing, HPAI, CONNECT_REQ/RES, TUNNELING_ACK, адреса групп и DPT.
2. UDP tunnelling lifecycle: channel, sequence, ACK/retry, connection-state, disconnect/reconnect, endpoint validation.
3. cEMI GroupValueRead/Response/Write и мониторинг групповых адресов.
4. DPT профили: 1, 5, 7, 9, 12, 13, 14, 16; неизвестные типы не угадывать.
5. ETS group-address import, preview, stable native identity, Point Runtime.
6. Engineering UI, диагностика и hardware acceptance.
7. Управление — только после RBAC, явных разрешений, аудита, quality guards и подтверждения на оборудовании.

## DEV152 — Point Runtime / Driver Manager
- KNX read-only passive group monitor подключён к Driver Manager и публикует значения в общий Point Runtime.
- Качество связи и конфигурации переводится в BAD_COMMUNICATION/BAD_CONFIGURATION без подмены последнего значения.
- Каталог показывает KNX как READ_ONLY_TRANSPORT, field writes запрещены.
- DPT 9.001 corrected to signed 11-bit two's-complement; invalid 0x7FFF rejected.

## DEV151 — cEMI parser
- Добавлен строгий парсер cEMI L_Data.req/con/ind, GroupValueRead/Response/Write, адресов, TPCI/APCI, короткого значения и payload.
- DPT metadata ещё не связывается автоматически: DPT берётся из инженерного проекта/ETS, не из самого telegram.

## DEV150 — UDP Tunnelling transport
- Добавлен отдельный UDP tunnelling transport: CONNECT lifecycle, endpoint validation, TX TUNNELING_REQ/ACK, RX TUNNELING_REQ/ACK, sequence checks, duplicate suppression, heartbeat и disconnect.
- Транспорт пока не интегрирован с Driver Manager и Point Runtime; cEMI/APDU decode, ETS import, Routing и аппаратная проверка остаются следующими этапами.

## DEV142
Добавлены протокольные codec primitives и DPT decode для 1.001, 5.001, 9.001, 14.000. Это ещё не live KNX driver: UDP session, cEMI/APDU, group monitor, ETS import, runtime factory, UI и аппаратные испытания не готовы.
