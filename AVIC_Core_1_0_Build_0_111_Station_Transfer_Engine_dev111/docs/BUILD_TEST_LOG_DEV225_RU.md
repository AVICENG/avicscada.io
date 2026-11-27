# DEV225 — BACnet Stack POC: license audit and build probe

Дата: 27.11.2026  
Статус: **лицензионный аудит и build scaffold добавлены; CI ещё не завершён; BACnet protocol worker не реализован**.

## Что сделано

- Проверен upstream Steve Karg BACnet Stack.
- Зафиксирована ревизия `45f9831996f1a17504a790da91a4113f2974595c`.
- Прочитан upstream `license/readme.txt`: core stack использует GPL with GCC exception; upstream README прямо разрешает linking с proprietary application. Отдельные файлы используют MIT и Apache-2.0.
- Выборочно проверены SPDX headers для Windows/Linux BACnet/IP и MS/TP ports и POSIX file helpers. Результаты и ограничения зафиксированы в `docs/architecture/BACNET_STACK_LICENSE_AND_INTEGRATION_AUDIT_RU.md`.
- В репозитории сохранены тексты GPL-2.0, GCC-exception-2.0, MIT и Apache-2.0 и third-party notice с commit pin.
- Добавлен CMake build probe, который скачивает строго закреплённую upstream ревизию, выключает demo apps, включает BACnet/IP и отключает пока не проверенные IPv6/MS/TP/BACnet/SC/Zigbee.
- Добавлен CTest version probe.
- Добавлен CI job для Windows и Linux.

## Что пока НЕ сделано

- Это не BACnet Worker и не BACnet driver.
- Нет Who-Is/I-Am, ReadProperty, ReadPropertyMultiple, COV, BBMD или vendor/model mapping в AVIC.
- Нет BACnet/SC TLS/certificate flow.
- Нет MS/TP serial manager и RS-485 acceptance.
- Нет теста с Trend controller.
- Полный SPDX/SBOM по фактическому source set CMake ещё не создан.
- CI build probe ещё не подтверждён зелёным результатом.

## Лицензионные ограничения

- Нельзя приписывать всему репозиторию одну лицензию.
- Нельзя менять upstream license headers или удалять notices.
- Изменения GPL-covered upstream files должны проходить отдельный review и соблюдение условий upstream GPL.
- Перед коммерческой дистрибуцией требуется полный source-set SPDX/SBOM и юридическая проверка.

## Следующий этап

1. Получить зелёный Windows/Linux build probe.
2. Сгенерировать SPDX inventory по реально собранным файлам CMake target.
3. Добавить BACnet/IP Worker IPC skeleton и отдельные contract tests.
4. Реализовать Who-Is/I-Am discovery и ReadProperty, затем ReadPropertyMultiple.
5. Проверить на локальном BACnet simulator, после этого на Trend и стороннем BACnet controller.
