# AVIC Core — журнал сборки DEV191

Дата: 26.11.2026

## Изменения
- Добавлен Core SWITCH: optional bool Status source/constant, bool Destination, PIN level metadata.
- Добавлен Core TIME с 21 именованным выходом, привязанный к TimeManagementService и timezone станции.
- Реализованы calendar values, weekday bits и 13 pulse outputs с one-second pulse hold.
- Обновлены UI block definitions, per-port signal types, local preview simulation и properties SWITCH.
- Обновлены FBD Studio compiler mapping/validation.
- Clock writes и Time Master network synchronization из FBD не выполняются; управление временем остаётся в Core Time Manager.

## Регрессия
- Добавлены тесты календарных выходов, минутного импульса, SWITCH source/constant и переопределения в симуляции.
- Добавлен сквозной Studio → compile-preview → Core compile → Core simulation для TIME и SWITCH.
- CI не завершён; статус DEV191 — НЕ ПОДТВЕРЖДЁН.

## Покрытие
29/29 типов редактора имеют Core contract, compiler mapping и simulation path. Остаются ограничения по operator RBAC control для SWITCH и распределению времени Time Master.
