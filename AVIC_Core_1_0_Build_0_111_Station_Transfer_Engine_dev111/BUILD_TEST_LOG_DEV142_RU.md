# DEV142 — журнал сборки и тестирования

- Добавлен `avic_core.network.knxnet_ip`: строгая упаковка/разбор KNXnet/IP frame, HPAI IPv4, CONNECT_REQ/RES, TUNNELING_ACK.
- Добавлены 2-/3-level group address encode/decode.
- Добавлены DPT 1.001, 5.001, 9.001, 14.000.
- Добавлены тесты границ пакетов, адресов, статусов и значений.
- Не заявляется готовый KNX runtime: UDP lifecycle, cEMI/APDU, ACK/retry, ETS import, Point Runtime adapter, Driver Manager factory, UI и hardware acceptance остаются следующими этапами.
- CI DEV142 должен пройти до принятия сборки.
