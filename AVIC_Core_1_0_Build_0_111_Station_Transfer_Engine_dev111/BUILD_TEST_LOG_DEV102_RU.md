# Журнал сборки AVIC Core DEV102

Дата: 23.11.2026  
База: предоставленная пользователем DEV101, собранная поверх Core DEV98.  
Версия пакета: `1.0.0.dev102`.

## Реализовано

1. Разрешена связь FBD BOOL-output с `ahu_section_supply_fan`.
2. `GraphicsService.save()` сохраняет `LogicGraphicsBinding` для универсального `fan` и модульной секции `ahu_section_supply_fan`.
3. Добавлена read-only оценка FBD-привязок к графическим элементам. Расчёт использует FBD `POINT_INPUT`, который читает authoritative Core Point Runtime. Некачественный сигнал или ошибка расчёта возвращает BAD и не включает анимацию.
4. Graphics Workbench получает результат FBD и применяет его к бинарному состоянию вентилятора.
5. Исправлено перекрытие SVG-символов прозрачным hitbox-элементом; текстовые подписи больше не растягиваются вместе с SVG.
6. Сохранение времени анимаций при перерисовке предотвращает сброс CSS rotor animation при опросе значений.

## Проверки

- `tests/test_ahu_fbd_to_fan_animation_dev102.py`: 3 passed.
- Совместная регрессия AHU DEV67 + FBD point binding DEV69 + Point Runtime DEV85 + FBD/Graphics binding DEV55 + DEV102 + навигационные проверки Repository: **12 543 passed in 16.35s**.
- `node --check` для inline JavaScript Graphics Workbench: успешно.
- Headless Chromium: 7 SVG-секций отображены; в DOM найден `fan-rotor`; CSS `animationName=avicFanSpin`, `animationDuration=0.72s`; animation currentTime продвинулся с ~1.1s до ~2.3s за 1.2s наблюдения с промежуточной перерисовкой.
- Headless Chromium: при смене результата FBD с GOOD/TRUE на BAD вращающийся класс удалён (`state-fan-running` count = 0).
- Backend TestClient: точка → POINT_INPUT → AND → AHU fan binding даёт GOOD/TRUE; GOOD/FALSE выключает; UNCERTAIN блокирует расчёт и возвращает BAD.
- `python -m compileall -q avic_core`: успешно.
- Полный `pytest -x -q` не завершился за 120 секунд: процесс дошёл примерно до 40% набора и был остановлен лимитом времени. Полный набор не объявляется пройденным. В начальном полном запуске были обнаружены устаревшие проверки навигации, ожидавшие `/pages`; они обновлены на новый `/repository`. После обновления повторный `-x` не обнаружил новых ошибок до остановки по времени.

## Безопасность и ограничения

- `field_writes_performed=False`; endpoint не посылает команд контроллеру.
- FBD результат сейчас вычисляется в режиме SIMULATION_ONLY/preview. Это не deployed/cyclic runtime и не подтверждение физического пуска вентилятора.
- `pip check` в общей среде разработки сообщает внешний конфликт: `moviepy 2.2.1` требует `pillow<12`, установлен `pillow 12.3.0`; это не зависимость AVIC Core.
- Реальный BACnet-контроллер, Windows acceptance и полная тестовая матрица всех модулей не проверялись.
