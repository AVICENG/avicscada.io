# AVIC Security — состояние и требования

## Текущие механизмы
В DEV46/47 сохранены существующие модули RBAC, Security Gateway, SecretStore, HostIdentity, лицензирования, recovery/break-glass и hash-chain AuditService. Их наличие в коде не означает завершённую production security acceptance.

## Требования
- Серверная авторизация каждой операции, включая прямые API-запросы.
- Object-level scopes: project/station/network/device/point/graphic/page/schedule.
- Platform Security, Station Security и Operational Security — разные уровни полномочий.
- Никакого скрытого универсального developer backdoor в клиентской установке.
- OT-команды только через Command Manager; UI не является границей безопасности.
- MFA/двойное подтверждение и Electronic Approval для выбранных критичных операций.
- Причина изменения, подтверждение исполнителя, при необходимости второго лица.
- Secrets не попадают в браузер, export package и обычные логи.
- CSRF, XSS/CSP, secure cookies, rate limits, session revocation, audit.

## DEV47
Все изменяющие Scheduler API используют текущую локальную защиту Workbench `require_local_operator`. Это ограничение loopback/Origin, а не production authentication. Реальный пользовательский login/session/RBAC enforcement остаётся обязательным этапом.
