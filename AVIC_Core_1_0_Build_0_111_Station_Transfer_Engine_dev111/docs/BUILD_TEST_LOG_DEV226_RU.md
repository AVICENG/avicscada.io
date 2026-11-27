# DEV226 — Siemens S7 open libraries

Дата: 27.11.2026  
Статус: **выбор библиотек, license inventory, optional dependencies и CI smoke tests добавлены; S7 Worker ещё не реализован**.

## Принятое решение

- Classic S7: `python-snap7 3.6.x`, MIT, pure Python, stable. Целевой путь — S7-300/400. S7-1200/1500 — только при явно включённом PUT/GET compatibility access; этот режим по умолчанию выключен, неаутентифицирован и не поддерживает optimized DB.
- Modern S7: `s7commplus 0.7.x`, MIT package, Beta. Реализует S7CommPlus V1/V2 TLS/V3, symbolic browsing и optimized DB. Встроенные zlib dictionaries содержат LGPL-3.0-or-later notice; HarpoS7 V1 SessionKey helper — отдельный MIT notice.
- S7.Net Plus проверен как MIT .NET alternative, но не выбран основным движком: не подменяет S7CommPlus secure protocol path.

## Изменения

- Добавлен optional extra `.[s7]`:
  - `python-snap7>=3.6,<4`
  - `s7commplus>=0.7,<0.8`
- Добавлены smoke tests импорта обеих библиотек.
- Добавлен Windows/Linux CI matrix для Python 3.11 и 3.13: установка optional extra, `pip check`, library smoke tests.
- Сохранены upstream license texts и notices в `third_party/licenses/siemens-s7/`.
- Добавлена архитектурная записка `docs/architecture/SIEMENS_S7_DRIVER_SELECTION_AND_SECURITY_RU.md`.
- Обновлена общая матрица выбора протоколов.

## Security gates

- Не включать PUT/GET на PLC автоматически.
- Для S7CommPlus TLS — fail-closed, обязательная проверка CA/сертификата в secure profile; запрет downgrade в plaintext после ошибки сертификата или авторизации.
- Не логировать password, session key, challenge, private key и TLS key material.
- До отдельного Command Gateway acceptance все записи, загрузка блоков и CPU mode changes выключены.

## Результат тестирования

CI job `Siemens S7 optional libraries` добавлен, но на момент создания отчёта ещё не завершён. Успешная установка библиотек не является тестом реального подключения к PLC.

## Следующий кодовый этап

1. Реализовать отдельный Python Worker process для classic S7 через AVIC IPC v1.
2. Реализовать S7CommPlus Worker process отдельно от classic S7.
3. Добавить emulator/simulator contract tests, read-only browsing и batch reads.
4. Добавить Windows/Linux process lifecycle, timeout, reconnect, sequence/generation fencing.
5. Аппаратная приёмка на точных S7-1200 и S7-1500 model/firmware; отдельно legacy SessionKey и TLS.
