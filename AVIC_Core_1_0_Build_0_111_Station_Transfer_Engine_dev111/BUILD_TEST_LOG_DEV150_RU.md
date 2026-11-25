# Журнал DEV150 — KNXnet/IP UDP Tunnelling

## Изменения
- Добавлен отдельный транспортный слой KNXnet/IP UDP Tunnelling с явным connect/disconnect.
- Реализованы CONNECT_REQ/RES, проверка статуса, channel ID и индивидуального адреса.
- Проверяется адрес data endpoint: клиент не принимает перенаправление на произвольный IP из UDP-ответа.
- Реализованы отправка cEMI через TUNNELING_REQ, проверка ACK, повторы и последовательность TX.
- Реализован приём TUNNELING_REQ, ACK входящих кадров, контроль channel/reserved/sequence и подавление дубликатов.
- Добавлен CONNECTIONSTATE heartbeat и best-effort DISCONNECT с обязательным закрытием локального UDP socket.
- Транспорт не открывает сокет при создании объекта; подключение выполняется только явным connect().

## Проверки
- Добавлены fake-UDP тесты CONNECT, TX/ACK, RX/ACK, duplicate suppression, endpoint validation, закрытие socket и запрет операций без соединения.
- CI DEV150 должен подтвердить совместимость на Python 3.11/3.12/3.13 и Windows.
- Реальная совместимость с KNX IP Interface/Router ещё не подтверждена аппаратно.

## Ограничения
- Это транспортный слой, не полный KNX драйвер и не cEMI/APDU decoder.
- Нет Driver Manager factory, Point Runtime adapter, ETS import, Routing, KNX Secure и инженерного UI.
- Приём cEMI пока синхронный, без фонового отдельного receive worker.
- KNX Tunnelling control остаётся только транспортом; запись в групповые адреса не предоставляется.
