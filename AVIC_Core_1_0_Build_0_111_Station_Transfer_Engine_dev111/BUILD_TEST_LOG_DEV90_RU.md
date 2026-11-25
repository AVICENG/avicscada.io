# Журнал сборки и испытаний DEV90

## Изменения
1. Добавлен `FBDExecutionService` с циклическим исполнением стратегии через существующий evaluator DEV89.
2. Добавлены настраиваемый период 100–60000 мс, независимый worker на стратегию, `start/stop`, ручной `tick_once`.
3. Добавлены статусы, generation, tick counter, длительность цикла, last error и ограниченный event log.
4. Добавлена проверка привязки стратегии к станции и запрет изменения периода во время исполнения.
5. Ошибка вычисления переводит стратегию в `ERROR`, выставляет stop event и прекращает циклическое выполнение.
6. `FBDExecutionService` подключён к `app.state.fbd_execution`.
7. Безопасность сохранена: никаких записей в OUTPUT, публикаций в PointRuntime или сетевых операций.

## Проверки текущей среды
- `pytest -q tests/test_dev90_fbd_cyclic_runtime.py tests/test_dev89_fbd_runtime_evaluation.py tests/test_dev85_point_runtime.py`: **14 passed**.
- Проверены ручные циклы, start/stop, фоновый worker, интервал, запрет перенастройки на ходу, fault-to-ERROR, отсутствие field writes/runtime publish.
- FBD-регрессия (DEV90, DEV89, DEV82, DEV81, DEV55, DEV69, DEV88, DEV68, DEV77, DEV78, DEV86, DEV80): **12 565 passed in 14.29s**.
- `python -m compileall -q avic_core tests`: успешно.
- `python -m avic_core --help`: успешно.
- Wheel собран без build isolation; SHA256 указан в `DEV90_SHA256_RU.txt`.
- ZIP integrity test: успешно.

## Не подтверждено
- Полный набор регрессии (~31 тыс. тестов) DEV90 не запускался.
- Windows-приёмка и визуальная браузерная приёмка не проводились.
- Реальные контроллеры BACnet/Modbus не подключались.
- Нет hard real-time гарантий, persisted restart/recovery, полевой записи или публикации.

## Важное
DEV85 остаётся подтверждённой пользователем Windows-базой: 31 041 passed, 1 skipped. DEV90 не наследует этот статус автоматически.
