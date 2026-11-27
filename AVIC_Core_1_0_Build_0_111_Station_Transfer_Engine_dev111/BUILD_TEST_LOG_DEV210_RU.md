# DEV210 — Интеграция общего Debounce в Point Runtime

Дата: 27.11.2026

## Реализовано

- Добавлены сохраняемые в объекте Point параметры `debounce_on_ms` и `debounce_off_ms`. Ноль отключает соответствующее направление фильтра.
- `DebouncedPointRuntimeService` подключён как основной Point Runtime в composition root через публичный пакет `avic_core.points`.
- BACnet/IP, Modbus TCP, KNXnet/IP и MQTT продолжают использовать общий контракт публикации; фильтрация выполняется после общей проверки значения/качества и до общей рассылки подписчикам.
- Короткий бинарный импульс не записывается в Point Runtime и не передаётся подписчикам.
- Устойчивый переход публикуется после выдержки ON/OFF времени.
- Потеря качества отменяет ожидающий переход, но сохраняет последнее принятое значение и исходный timestamp.
- Добавлен отдельный `PointRuntimeScheduler`: один bounded worker с интервалом 25 мс обслуживает все точки и станции, не выполняя сетевой I/O или field writes.
- Scheduler явно запускается Driver Manager при старте первого polling-драйвера и останавливается после остановки последнего. Ошибка запуска драйвера также очищает scheduler.
- Добавлены диагностика scheduler и тесты фильтрации, bounce cancellation, due-time commit без нового измерения, quality-loss cancellation, persistence конфигурации, запрета аналоговых/OUTPUT точек и защиты от отмены чужим DriverInstance.

## Важные инварианты

- Дребезг — только для бинарных INPUT/INOUT точек. Аналоговые deadband/hysteresis — отдельные механизмы и не смешиваются с debounce.
- При первом достоверном измерении исходное состояние принимается сразу, без задержки запуска.
- Некорректное качество не превращается в GOOD и не меняет значение.
- Источник, станция и тип точки по-прежнему проверяются исходным PointRuntime перед изменением.
- Scheduler не создаёт скрытый поток внутри DebounceEngine; его жизненным циклом управляет Driver Manager.
- Rust transport не обходит фильтр: Rust pilot пока не подключён к production Driver SDK/IPC; при подключении должен публиковать через тот же Core Point Runtime контракт.

## Ограничения

- Конфигурация уже сохраняется в модели Point и доступна через `point_runtime.configure_debounce(point_id, on_ms=..., off_ms=...)`, но отдельная форма/REST API в Point Manager пока не добавлена.
- Scheduler обслуживает активные polling driver sessions. COV/event-driven источники должны подключаться к тому же жизненному циклу scheduler при реализации.
- Не заявляется аппаратная приёмка дребезга на реальных контроллерах.
- PR #6 остаётся Draft; CI должен проверить DEV210 на Windows/Linux и Python 3.11/3.12/3.13. До завершения CI статус — **ожидает проверки**, а не принято.

## Проверки, добавленные в DEV210

Файл: `tests/test_dev210_point_runtime_debounce.py`

1. Импульс короче ON delay отменяется.
2. Переход фиксируется scheduler после deadline без следующего sample.
3. Возврат к устойчивому значению отменяет pending transition.
4. Потеря качества отменяет pending transition и сохраняет last-good value.
5. Настройки сохраняются через перезапуск Core.
6. Аналоговые и OUTPUT точки не принимают debounce config.
7. Чужой DriverInstance не может отменить pending transition другого драйвера.
8. Явный PointRuntimeScheduler обслуживает due transitions и корректно останавливается.

Результат CI будет внесён после получения фактических workflow logs.
