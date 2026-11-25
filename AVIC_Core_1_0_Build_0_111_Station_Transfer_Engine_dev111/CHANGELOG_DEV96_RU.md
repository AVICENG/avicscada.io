# Изменения DEV96

## Добавлено
- Core FBD: блоки SUB, MUL, DIV, SELECT с типизированными контрактами.
- Симуляция: вычисление арифметических блоков и выбор входа по SEL.
- DIV: безопасная диагностика деления на ноль.
- FBD Studio compiler: компиляция новых блоков после проверки портов.
- Регрессионные и сквозные тесты Studio → Core → Simulation.

## Не включено
- Stateful блоки (HYSTERESIS, DELAY, LATCH), PID, SWITCH и SCALE Studio.
- Публикация FBD Points, межстраничные Connective и staged publish.
- Автоматический запуск и физические записи.
