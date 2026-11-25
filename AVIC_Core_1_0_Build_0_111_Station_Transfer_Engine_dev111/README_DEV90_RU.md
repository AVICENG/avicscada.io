# AVIC Core 1.0 — DEV90

## FBD Cyclic Runtime

DEV90 добавляет `FBDExecutionService` — управляемый циклический исполнитель FBD-стратегий.

### Возможности
- Независимое состояние каждой стратегии: `STOPPED`, `RUNNING`, `STOPPING`, `ERROR`.
- Настраиваемый период 100–60000 мс.
- Отдельный daemon-worker и stop-сигнал на каждую стратегию.
- `tick_once()` для детерминированной диагностики и тестирования.
- Счётчик циклов, длительность последнего расчёта, последняя ошибка и ограниченный журнал событий.
- Проверка неизменности привязки стратегии к станции.
- При ошибке вычисления стратегия переходит в `ERROR` и прекращает цикл.
- Конфигурирование периода работающей стратегии запрещено.

### Границы безопасности
DEV90 вызывает только DEV89 `FBDService.simulate()`. Это периодическая локальная оценка графа, а не production publish pipeline. Вычисленные выходы не записываются в `PointRuntime`, не отправляются драйверам и не управляют полевым оборудованием. `runtime_published=false`, `field_writes_performed=false`.

### Пример
```python
from avic_core.runtime import FBDExecutionService

execution = FBDExecutionService(core)
execution.start(document_id, interval_ms=1000)  # фоновый цикл
status = execution.status(document_id)
execution.stop(document_id)
execution.close()
```

Для теста без фонового потока:
```python
execution.start(document_id, background=False)
result = execution.tick_once(document_id)
```

## Что пока не реализовано
- Публикация результатов в точки и запись OUTPUT.
- BACnet/Modbus polling или field writes.
- Watchdog / автоматический restart / recovery policy.
- Persisted runtime configuration и восстановление после перезапуска процесса.
- Гарантии hard real-time; Python scheduler не является PLC.
- Интеграция циклического runtime с UI start/stop controls.
