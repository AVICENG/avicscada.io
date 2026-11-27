# Siemens S7 — C-only implementation policy and library audit

Дата пересмотра: 27.11.2026  
Статус: **PLANNED / BLOCKED BY C ENGINE SELECTION**.

## Обязательное решение AVIC

Siemens S7 реализуется в AVIC только как нативный C Worker. Не допускаются:
- Rust S7 protocol engine;
- Python S7 protocol engine;
- автоматический fallback на старую реализацию;
- смешение S7comm и S7CommPlus в один неразличимый режим.

Существующий общий Worker supervisor и AVIC IPC contract сохраняются как инфраструктура. Старый S7 transport удаляется только после замены, регрессионных тестов и отдельной проверки путей запуска.

## Проверка открытых библиотек

### Snap7 — сильный кандидат, но не pure C

Upstream: https://github.com/davenardella/snap7

- Официальный upstream заявляет поддержку Windows и Unix-подобных платформ.
- Проект прямо указывает необходимость C++ toolchain для сборки.
- В репозитории отдельно хранятся GPL и LGPL-3.0 license texts; C/C++ client API и фактические условия поставки должны быть проверены по закреплённой ревизии и каждому включаемому компоненту.
- Поэтому Snap7 нельзя обозначать как чистую C-библиотеку без оговорок. Он может рассматриваться только как отдельный кандидат на C ABI boundary после технического и лицензионного решения.

### libnodave — pure C, но не принят

Upstream: https://libnodave.sourceforge.io/  
Публичный исходный код: https://github.com/netdata-be/libnodave

- Реализация на C; заявлены Windows/Linux и S7-200/300/400/1200/1500 через ISO-on-TCP/совместимые интерфейсы.
- Лицензирование в исходниках — LGPL-2.0-or-later для библиотеки; GPL-компоненты и инструменты требуют отдельного исключения из поставки или инвентаризации.
- Upstream прямо предупреждает, что код beta, требует самостоятельной оценки безопасности и может ошибочно выполнять записи при дефектах драйвера.
- Историческая база кода и ограниченная доказанная совместимость не позволяют объявить его промышленной основой AVIC без форка, аудита, fuzzing и аппаратных испытаний.

**Вывод:** на текущем этапе нет утверждённой зрелой pure-C библиотеки, которую можно безоговорочно принять в промышленный AVIC. Не подменять этот пробел Python или Rust. Сначала провести полный аудит Snap7 C ABI / C++ core и libnodave; если ни один кандидат не проходит критерии, отдельно принять решение о разработке изолированного C transport/codec на основе проверяемой спецификации и тестовых векторов.

## Целевая архитектура Worker

- Worker source: C; единый AVIC Driver IPC v1.
- Отдельные capabilities: classic S7comm и S7CommPlus; не заявлять S7CommPlus/TLS без подтверждённой реализации.
- Read-only first; все записи, загрузка блоков, CPU mode changes и административные операции запрещены.
- Пакетное чтение только совместимых и непрерывных диапазонов; не читать через незаданные адресные промежутки.
- Ограничение PDU/размера пакета, timeout, bounded retry, reconnect с backoff.
- Sequence, generation и station-scope fencing обязательны.
- Секреты — только через AVIC SecretStore; запрет plaintext credentials в конфиге, IPC, логах и экспортируемых пакетах.
- Quality/timestamp/connection state передаются раздельно; после обрыва устаревшие значения не остаются GOOD.
- Windows и Linux builds обязательны.

## Приёмочные этапы

1. Зафиксировать upstream commit, SBOM, license inventory и build reproducibility.
2. Подтвердить, что выбранный protocol engine действительно доступен из C Worker без скрытого Python/Rust процесса.
3. Собрать C Worker под Windows и Linux.
4. Добавить protocol unit tests и golden packet vectors.
5. Добавить simulator/emulator IPC tests: connect, read, batch, invalid range, timeout, disconnect, reconnect, malformed frames, generation fencing.
6. Добавить fuzzing и soak tests; отдельно проверить отсутствие write-capable API в read-only сборке.
7. Провести hardware acceptance на точных моделях и версиях прошивки S7-300/400/1200/1500, для каждого заявленного семейства отдельно.
8. Только после прохождения критериев разрешить S7 в Driver Manager и удалить старый Rust/Python transport path.

## Текущий фактический статус

- Python Snap7 / S7CommPlus package smoke tests ранее проходили CI, но они больше не считаются доказательством целевой реализации и удалены из активного S7 пути.
- Старый Rust S7 код — legacy, не целевая реализация.
- C S7 Worker отсутствует.
- Реальное PLC подключение и hardware acceptance не выполнены.
- Driver Catalog обязан держать S7 в PLANNED и не рекламировать runtime start/read/discovery.
