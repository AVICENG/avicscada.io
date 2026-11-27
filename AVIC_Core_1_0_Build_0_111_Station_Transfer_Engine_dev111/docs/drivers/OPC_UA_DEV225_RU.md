# OPC UA Client — DEV225 (foundation)

Дата: 27.11.2026
Реализация: контракт конфигурации и NodeId; транспорт open62541 ещё не подключён.
Статус: **PLANNED / transport not available**. Это не заявление о готовом OPC UA драйвере.

## 1. Архитектурное решение
- Четвёртый протокол после Modbus TCP, BACnet/IP и KNXnet/IP.
- Клиентская реализация на open62541 в отдельном изолированном worker process; не встраивать OPC UA event loop в Core.
- На первом этапе только чтение. Любые записи остаются запрещёнными и в будущем должны идти через Command Gateway, RBAC, interlocks, read-back и аудит.
- Один endpoint / secure channel на экземпляр драйвера; reconnect и session recreation будут отдельными состояниями runtime.
- AVIC Point UID остаётся внутренним ключом; OPC UA NodeId хранится как внешний адрес binding.

## 2. Контракт, реализованный в DEV225
OpcUaNetworkConfig проверяет:
- только opc.tcp://host:port/path;
- URL не может содержать userinfo, query или fragment;
- обязательные application URI, client certificate, ссылка на private key в SecretStore и trust store;
- режим Sign или SignAndEncrypt; None запрещён;
- только secure policy URIs из allowlist: Basic256Sha256, Aes128_Sha256_RsaOaep, Aes256_Sha256_RsaPss;
- ограниченные timeout, максимальный размер сообщения и число chunks.

parse_node_id поддерживает стандартные формы:
- ns=0;i=2258 — numeric;
- ns=2;s=Plant.AHU-01.SupplyTemp — string;
- ns=3;g=<uuid> — GUID;
- ns=4;b=<base64> — ByteString.

Проверяются namespace range, UInt32 numeric range, GUID/base64 validity, пустые идентификаторы и управляющие символы.
OpcUaNodeBinding связывает один AVIC point с NodeId и допускает только access=read. Поддерживаются boolean, signed/unsigned integers, float/double, string, datetime и auto. Scale/offset разрешены только для числовых типов и должны быть конечными числами.

## 3. Что пока НЕ реализовано
- Native open62541 C client worker и AVIC IPC integration.
- Endpoint discovery / GetEndpoints и выбор согласованного secure endpoint.
- Проверка server certificate trust, hostname/application URI и revocation policy на реальном соединении.
- Browse и безопасная навигация по address space; импорт NodeId в bindings.
- Read / ReadMultiple, DataChange subscriptions, deadband и timestamp/status-code mapping.
- Reconnect, secure-channel renewal, session recreation, subscription transfer.
- Namespace URI resolution (текущий NodeId contract сохраняет namespace index; стабильный импорт должен сохранять namespace URI и повторно разрешать индекс).
- Server-side OPC UA, methods, writes, history read и alarms/events.
- Независимый OPC UA server interoperability tests, нагрузка, fault injection и полевая приёмка.

## 4. Security invariants
- Запрещено по умолчанию подключаться к SecurityPolicy None.
- Сертификаты и приватные ключи не помещаются в обычный JSON config; private key передаётся только через SecretStore reference и будет загружаться worker deployment layer.
- Нельзя автоматически доверять любому новому сертификату сервера (TOFU запрещён для production).
- Нельзя публиковать значение с Bad status code как GOOD.
- Неизвестные NodeId, namespace и DataType не угадываются.
- Discovery и browse не должны автоматически активировать полевые точки или инициировать записи.

## 5. Проверки
Добавлен tests/test_opc_ua_contract_dev225.py: четыре формы NodeId, malformed/range cases, secure endpoint URL validation, запрет SecurityPolicy None, обязательные certificate/SecretStore references, read-only binding и numeric scaling validation.

**CI ещё не подтвердил тесты DEV225.** OPC UA не включается в список operational/read-capable драйверов до интеграции open62541 worker и независимой приёмки.