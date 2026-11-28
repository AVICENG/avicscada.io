# AVIC Core — журнал DEV266 (MQTT topic filters)

Дата: 28.11.2026  
Базовый HEAD: DEV265 `d739c33b0f3cf1cc0ab4f7fa1955a29cf65a2bed`  
Текущий HEAD: DEV266b `df7219672b7caa7d59cc9d761060e038024a4818`  
PR: #11

## Реализовано

1. Добавлен общий matcher MQTT Topic Filter для MQTT 3.1.1/5.0:
   - односегментный wildcard `+`;
   - завершающий многоуровневый wildcard `#`;
   - корректное совпадение `plant/#` с темой `plant`;
   - сохранение пустых уровней темы;
   - правило системных тем `$`: фильтр, начинающийся с `+` или `#`, не совпадает с `$SYS/...`.
2. Валидация фильтра запрещает wildcard внутри сегмента и `#` не в последнем сегменте.
3. Оба пути приёма — Python MQTT adapter и MQTT C Worker Point Runtime adapter — используют один matcher.
4. Driver Manager теперь валидирует port (1..65535) и keepalive (10..3600 секунд) до выбора Python/C engine; bool и строковые значения не принимаются как целые числа.
5. Добавлены параметризованные тесты правил MQTT filter и тест wildcard-маршрутизации через C event adapter.
6. Исправлен тест DEV265 выбора C engine: тест должен вызывать метод с экземпляром DriverManagerService, а не с голым object(), иначе проверка падает до проверки выбора движка.

## Проверки и CI

- Для исходного DEV265 CI run `46127777069` нативные Paho probe Ubuntu/Windows прошли.
- Три Linux Python jobs DEV265 завершились failure на одном дефекте тестового harness: `AttributeError: 'object' object has no attribute '_build_mqtt_c_worker_adapter'`. Причина локализована и исправлена в DEV266b.
- Rust Communication Engine, libmodbus C Worker Windows/Linux, OPC UA native probe Windows/Linux и Siemens C-only policy jobs DEV265 прошли.
- Полный результат DEV266 ещё не подтверждён: workflow для HEAD `df721967...` создан как run `46128163771`, на момент записи ожидает старта (jobs ещё не опубликованы).

## Ограничения

- Этот этап не добавляет исполняемый MQTT Paho C Worker. В репозитории по-прежнему есть только native Paho lifecycle probe и Python-side C event adapter.
- Не проверены реальные подписки/приём MQTT сообщений из Mosquitto через AVIC IPC.
- TLS, MQTT reconnect, broker integration, queue saturation и cleanup end-to-end остаются открытыми.
- MQTT статус остаётся 🟧. DEV266 не является основанием для повышения статуса драйвера.

## Следующий этап

Реализовать отдельный Paho MQTT C Worker executable с AVIC IPC, callback-to-bounded-queue передачей, одним IPC stdout writer, read-only subscribe QoS 0/1/2, reconnect и реальным Mosquitto integration в Windows/Linux CI. Секреты не передавать через argv, environment или обычный JSON IPC.
