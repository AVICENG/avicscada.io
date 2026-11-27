# Modbus TCP, BACnet/IP и KNXnet/IP — DEV223

Дата: 27.11.2026

Документ описывает фактический read-only объём трёх полевых драйверов в ветке `drivers/multi-engine-c-worker-dev223`. Отправка кода в GitHub не означает успешное прохождение CI или аппаратную совместимость.

## 1. Общая граница безопасности

- Драйверы читают поле и передают данные в общий AVIC Point Runtime.
- Потеря связи отражается качеством `BAD_COMMUNICATION`; ошибочная конфигурация декодирования — `BAD_CONFIGURATION`.
- Ни один из трёх адаптеров в текущем состоянии не реализует запись в физическое оборудование.
- Будущие команды должны проходить через Core Command Gateway с RBAC, проверкой качества, блокировками, аудитом и явным разрешением записи на конкретном устройстве.
- Значение, отправленное в сеть, нельзя автоматически считать подтверждённым состоянием объекта.

## 2. Modbus TCP

### Реализовано
- FC01 Read Coils, FC02 Read Discrete Inputs, FC03 Read Holding Registers, FC04 Read Input Registers.
- Проверка MBAP transaction ID, Protocol ID, Unit ID, длины и функции ответа; Modbus exception response преобразуется в диагностическую ошибку.
- Декодирование BOOL, UINT/INT 16/32/64 и FLOAT 32/64; byte order, word order, scale и offset.
- Объединение смежных и пересекающихся адресов с одинаковой функцией; чтение не пересекает адресные разрывы.
- Ограничения запроса: 2 000 бит для FC01/02 и 125 регистров для FC03/04.
- Чтение Device Identification MEI 0x0E для производителя/модели и других доступных стандартных идентификаторов.
- Python, Rust и C libmodbus Worker выбираются явно; автоматического fallback нет.
- Идентификатор MBAP теперь резервируется потокобезопасно при параллельном опросе групп.

### Новые регрессионные тесты
- Слияние смежных групп и раздельное чтение адресных разрывов.
- Публикация GOOD и перевод точек в BAD_COMMUNICATION при тайм-ауте.
- Уникальность 2 000 transaction ID при параллельном выделении.

### Не завершено
- Modbus RTU/RS-485: serial port lifecycle, parity/stop bits, bus arbitration и тесты на физической линии.
- Переподключение/устойчивость на реальных шлюзах, длинный soak, диагностика конкретных vendor deviations.
- Полноценная проверка C Worker на Windows и Linux по актуальному CI.
- Аппаратная приёмка на реальном контроллере.

## 3. BACnet/IP

### Реализовано
- Безопасное BACnet/IP discovery через Who-Is/I-Am с BVLC/NPDU/APDU разбором.
- ReadProperty, включая array index, проверку Invoke ID, object identifier и property identifier в ComplexACK.
- Чтение Device.Object_List с ограничением количества объектов; чтение Object_Name и стандартных свойств идентичности.
- Разделение manufacturer/model/source/confidence; неизвестная модель не угадывается.
- Read-only политика запрещает WriteProperty, reboot и конфигурационные сервисы.
- Исправлена конфигурация Linux probe для upstream BACnet Stack: routing выключен, поскольку текущий probe — single-datalink BACnet/IP endpoint, не BACnet router.

### Новые регрессионные тесты
- ReadProperty binding с array index и scale/offset.
- Timeout переводит качество точки в BAD_COMMUNICATION.

### Не завершено
- ReadPropertyMultiple (RPM), COV subscriptions, полноценная обработка segmentation.
- BBMD/Foreign Device registration и routed BACnet networks.
- Полноценный AVIC BACnet C Worker; наличие upstream stack probe само по себе не означает готовность драйвера.
- Проверка на реальном Trend/BACnet контроллере и длительная проверка сети.

## 4. KNXnet/IP

### Реализовано
- KNXnet/IP UDP tunnelling: CONNECT, TUNNELING, ACK, receive sequence, duplicate suppression, CONNECTIONSTATE heartbeat и DISCONNECT.
- Проверка доверенного адреса gateway/data endpoint; клиент не принимает произвольный адрес из UDP-ответа.
- cEMI L_Data indication parsing и passive GroupValue monitor.
- Публикация GroupValueResponse/GroupValueWrite в Point Runtime; GroupValueRead не интерпретируется как значение.
- Строгая проверка длины cEMI и APDU; malformed frame не публикуется как GOOD.
- Расширен набор DPT: 1.xxx (однобитные типы из разрешённого списка), 5.001/5.003/5.004, 6.001, 7.001, 8.001, 9.001, 12.001, 13.001, 14.000, 16.000, 17.001, 18.001.
- Для DPT 1.xxx адаптер извлекает короткое значение из short APDU; остальные типы используют payload.
- DPT 17.001 декодируется по wire-диапазону 0..63 с проверкой двух зарезервированных старших битов; отображение сцен 1..64 выполняется на уровне инженерного UI.
- DPT 18.001 декодируется как команда activate/learn и номер сцены 0..63 с проверкой зарезервированного бита.
- Добавлен режим `read_mode="poll"`: адаптер циклически отправляет GroupValueRead для одной привязки за один опрос и принимает ответ. Режим `passive` остаётся значением по умолчанию.

### Новые регрессионные тесты
- Декодирование типовых DPT: boolean, percent, angle, unsigned/signed integers, KNX float16, IEEE float32, string и scene number.
- Негативные тесты длины, invalid float pattern и некорректного scene number.
- Передача short APDU через KNX adapter в точку с качеством GOOD.
- Проверка принятия расширенного списка DPT при создании binding.

### Не завершено
- ETS project import (групповые адреса, описания, DPT, структура и связи).
- Пакетный/параллельный GroupValueRead, очередь и строгая корреляция ответов при большом числе групповых адресов.
- Запись GroupValueWrite только после интеграции Command Gateway и отдельной приёмки.
- Расширение DPT каталога и профильные типы времени/даты/составных значений.
- KNX IP Routing, multiple tunnelling sessions и физическая приёмка на KNX IP interface.

## 5. Команды проверки

Из корня пакета AVIC Core:

```powershell
python -m pip install -e ".[dev]"
python -m compileall -q avic_core
python -m pytest -q tests/test_knx_extended_dpt_dev223.py tests/test_modbus_bacnet_adapter_regression_dev223.py
python -m pytest -q
python -m pip check
```

Для Modbus C Worker дополнительно требуется Linux CMake/CTest и Windows UCRT64/MSYS2 job из GitHub Actions.

## 6. Готовность

| Протокол | Уровень реализации | Промышленная готовность |
|---|---|---|
| Modbus TCP | Read-only функциональный стек + альтернативные worker engines | Не подтверждена: CI head/hardware/soak ещё нужны |
| BACnet/IP | Discovery + ReadProperty + Object_List + read-only adapter | Не подтверждена: RPM/COV/segmentation/BBMD и hardware ещё нужны |
| KNXnet/IP | Tunnelling + passive group monitor + расширенный DPT decoder | Не подтверждена: ETS import, active read polling, command gateway и hardware ещё нужны |

Все три драйвера остаются read-only. PR #9 остаётся Draft. Ни один не объявляется промышленно готовым до зелёного CI на актуальном HEAD, fault/reconnect/soak tests и аппаратной приёмки.
