# KNX в AVIC — актуальный статус после DEV154

KNXnet/IP реализуется независимо по открытым спецификациям KNXnet/IP, cEMI и DPT. Закрытый код Niagara не используется.

## Реализовано в коде

1. **DEV142 — codec primitives:** KNXnet/IP framing, HPAI, CONNECT_REQ/RES, tunnelling ACK, адреса групп и базовые DPT decode.
2. **DEV150 — UDP tunnelling:** явный CONNECT/disconnect lifecycle, проверка адресов и endpoint, ACK/retry, контроль последовательностей, duplicate suppression, heartbeat.
3. **DEV151 — cEMI:** строгий разбор L_Data и групповых сервисов, source/destination, TPCI/APCI и payload.
4. **DEV152 — Driver Manager / Point Runtime:** runtime factory для `knxnet-ip`, passive group monitor и публикация выбранных адресов в общий Point Runtime; BAD_COMMUNICATION и BAD_CONFIGURATION без подмены последнего значения.
5. **DEV153 — DPT 9.001:** знаковая 11-битная мантисса и проверка недопустимого шаблона.
6. **DEV154 — каталог:** KNX отражён как `READ_ONLY_TRANSPORT`; field writes запрещены, capability tests соответствуют реализации.

## Поддерживаемые возможности

- Явная UDP tunnelling сесcия KNXnet/IP.
- Пассивное получение групповых телеграмм через tunnelling.
- Явная привязка group address → AVIC point → DPT.
- DPT: 1.001, 5.001, 9.001, 14.000.
- Публикация значений и качества в общий Point Runtime.
- Диагностика счётчиков успешных, ошибочных, проигнорированных и некорректных сообщений.

## Не реализовано / не подтверждено

- ETS project/group-address import и автоматическое создание точек.
- KNX Routing / multicast routing.
- Исходящие GroupValueRead и GroupValueWrite; KNX adapter остаётся read-only.
- DPT 7, 12, 13, 16 и прочие профили.
- Автоматическое обнаружение и сопоставление всех устройств/групп.
- Аппаратная приёмка на физических KNX IP интерфейсах и реальных KNX линиях.
- Управление оборудованием. Оно не должно добавляться до RBAC, явных разрешений, quality guards, command audit и испытаний.

## Проверки

Полный CI DEV158:
- Windows / Python 3.13: 31 261 passed, 1 skipped.
- Ubuntu / Python 3.11, 3.12 и 3.13: 31 262 passed на каждой версии.

Тесты используют fake UDP sockets и тестовые cEMI frames. Это проверяет кодовые сценарии, но не заменяет аппаратную приёмку и межвендорные испытания.

## Следующие этапы

1. ETS import с preview, проверкой дублей, native identity и явным подтверждением инженера.
2. Расширение DPT по таблицам типов с тестовыми векторами.
3. Аппаратная приёмка на нескольких KNX/IP интерфейсах и реальных устройствах.
4. Только после отдельного проекта безопасности — обсуждение контролируемой передачи команд.
