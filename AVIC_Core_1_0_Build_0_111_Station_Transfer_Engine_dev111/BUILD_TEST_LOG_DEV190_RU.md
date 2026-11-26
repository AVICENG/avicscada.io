# AVIC Core — журнал сборки DEV190

Дата: 26.11.2026

## Изменения
- Добавлен Core PID_LOOP с шестью входами и четырьмя FLOAT-выходами OUT/P/I/D.
- Реализованы P/I/D, direct/reverse, deadband, derivative filter, anti-windup, выходные/интегральные ограничения, output rate limit.
- Реализованы ENABLE/DISABLED, AUTO/MANUAL, tracking integrator, bumpless transfer и RESET.
- Параметры нормализуются и проверяются на конечность/допустимые диапазоны.
- Core simulation теперь сохраняет все именованные выходные порты много-выходных блоков.
- Studio compiler сохраняет PID config и подключает все выходы в Core graph.

## Регрессия
- Добавлены тесты AUTO → MANUAL → AUTO, RESET и значения OUT/P.
- Добавлен сквозной тест Studio → compile-preview → Core compile → Core simulation.
- CI не завершён; статус DEV190 — НЕ ПОДТВЕРЖДЁН.

## Покрытие
27 из 29 типов редактора имеют Core-контракт и путь компиляции. Остаются SWITCH и TIME.
