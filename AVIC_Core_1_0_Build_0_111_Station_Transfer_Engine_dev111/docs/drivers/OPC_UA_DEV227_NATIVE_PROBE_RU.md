# AVIC OPC UA — нативный клиентский пробник DEV227

## Назначение

DEV227 добавляет отдельную сборку нативного OPC UA клиента на open62541 1.4.21. Это следующий проверяемый слой после Python-контрактов DEV225: компиляция C-библиотеки, криптография OpenSSL, строгий набор SecurityPolicy и чтение одного NodeId по защищённому OPC UA соединению.

## Безопасность

- SecurityPolicy None запрещена; режимы допускаются только Sign и SignAndEncrypt.
- Допускаются только Basic256Sha256, Aes128_Sha256_RsaOaep и Aes256_Sha256_RsaPss.
- Клиент требует сертификат приложения, закрытый ключ и явно переданный доверенный сертификат сервера.
- Endpoint должен быть opc.tcp://; URL credentials, query и fragment запрещены.
- Пробник не реализует запись значений.
- Закрытый ключ читается из временного файла, переданного доверенным оператором запуска. Для промышленного Worker требуется отдельный защищённый канал выдачи секрета из SecretStore; передавать ключ через обычный IPC JSON запрещено.

## Сборка

Из корня проекта:

    cmake -S rust/avic-communication-engine/opcua-native-probe -B build/opcua-native-probe -DCMAKE_BUILD_TYPE=Release
    cmake --build build/opcua-native-probe --config Release --parallel 2
    ctest --test-dir build/opcua-native-probe -C Release --output-on-failure

CMake получает open62541 по тегу v1.4.21, включает OpenSSL и отключает upstream examples/tools/tests. Тег и используемая версия должны быть отражены в SBOM при выпуске.

## Проверка NodeId

    build/opcua-native-probe/avic-opcua-native-probe.exe --self-test

Проверяются numeric, string, GUID и ByteString NodeId, а также отказ для некорректных форм и диапазонов.

## Защищённое чтение

    avic-opcua-native-probe.exe --connect opc.tcp://controller:4840 client.der client-key.der trusted-server.der urn:avic:opcua:client http://opcfoundation.org/UA/SecurityPolicy#Basic256Sha256 SignAndEncrypt ns=2;s=AHU.SupplyAirTemp

Сертификаты должны быть DER и соответствовать ApplicationUri/доверенной цепочке сервера. Команда не подменяет сертификаты, не отключает проверку доверия и не переключается на None.

## Статус и ограничения

**Статус: нативный C-клиент и build/self-test probe; ещё не промышленный OPC UA Driver.**

Не реализованы: AVIC Driver IPC v1 интеграция, Browse/namespace URI resolution, подписки DataChange/COV, reconnect/session renewal policy AVIC, безопасная передача секрета из SecretStore без временного файла, multi-server нагрузочные тесты, Windows/Linux независимый сервер acceptance. Не включать этот пробник в каталог как готовый драйвер. Чтение — только через отдельный процесс; запись остаётся запрещённой до интеграции с Command Gateway.
