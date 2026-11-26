# AVIC Core — журнал сборки DEV192

Дата: 26.11.2026

## Изменения
- KNOB расширен до инженерного контракта: value, bottom_range, top_range, cov_increment, units, user_level.
- Добавлена строгая проверка конечности, диапазона значения, COV increment, единиц и PIN level 0–99.
- Core simulation отклоняет KNOB override вне диапазона.
- UI показывает параметры KNOB и явно сообщает, что runtime RBAC для операторского изменения ещё не подключён.
- Обновлены pyproject и runtime/backup version metadata до 1.0.0.dev192.
- Добавлен тест точного соответствия 29 UI block types, Core contracts, compiler map и именованных портов.

## Регрессия
- Обновлены тесты KNOB range/PIN.
- Добавлен catalog parity test DEV192.
- CI jobs переведены на ручной запуск и в этой серии не выполнялись. Результаты DEV186–DEV192 не подтверждены CI.

## Покрытие
29/29 UI block types имеют Core contract и compiler mapping. Port-name parity проверяется отдельным тестом. Ограничения:
- PIN/user_level для KNOB/SWITCH пока хранится как metadata, runtime RBAC command path не подключён.
- TIME использует Core TimeManager; Trend Time Master distribution не выполняется из FBD.
- физические записи остаются запрещёнными в симуляции; публикация отдельна.

## Готовность
DEV192 — исходники и документация обновлены; статус **НЕ ПОДТВЕРЖДЁН** до ручного Windows/Linux CI.

- Добавлен отрицательный тест миграции: старый TIME.OCC placeholder отклоняется с явным сообщением, автоматическое опасное переподключение не выполняется.
