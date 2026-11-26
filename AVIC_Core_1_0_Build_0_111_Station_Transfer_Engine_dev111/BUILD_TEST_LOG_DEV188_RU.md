# AVIC Core — журнал сборки DEV188

Дата: 26.11.2026

## Изменения
- Добавлены Core блоки DELAY и LATCH с BOOL/FLOAT портами и строгой проверкой параметров.
- DELAY учитывает on/off задержки и фактическую длительность FBD-тика.
- LATCH удерживает состояние с настраиваемым приоритетом RESET/SET.
- FBDExecutionService передаёт dt_seconds из interval_ms в Core simulation.
- Добавлены compiler mapping, compile-preview validation и перенос параметров из Studio.
- Публикация и физические записи не включены.

## Регрессия
- Добавлены тесты DELAY on/off timing и LATCH retention/priority.
- Добавлен сквозной тест Studio → compiler → Core simulation для обоих блоков.
- Результаты CI ожидают фактического выполнения; статус НЕ ПОДТВЕРЖДЁН.

## Покрытие
24 из 29 типов редактора имеют Core-контракт и путь компиляции. Остаются ANALOG_INPUT, EXTERNAL_SENSOR, PID_LOOP, SWITCH, TIME.

## Известные ограничения
- Sensor inputs, PID, SWITCH и TIME ещё не имеют подтверждённого сквозного Core-пути.
- Полная приёмка требует Windows и Linux регрессии, Linux запускается только вручную.
