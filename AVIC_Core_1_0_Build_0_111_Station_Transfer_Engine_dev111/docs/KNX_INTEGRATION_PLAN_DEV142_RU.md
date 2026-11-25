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

## DEV142
Добавлены протокольные codec primitives и DPT decode для 1.001, 5.001, 9.001, 14.000. Это ещё не live KNX driver: UDP session, cEMI/APDU, group monitor, ETS import, runtime factory, UI и аппаратные испытания не готовы.
