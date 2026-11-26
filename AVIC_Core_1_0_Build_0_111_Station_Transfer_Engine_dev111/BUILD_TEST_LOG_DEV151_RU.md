# Журнал DEV151 — KNX cEMI L_Data и групповые APDU

## Изменения
- Добавлен строгий разбор cEMI L_Data.req / L_Data.con / L_Data.ind.
- Разбираются Additional Information, Control Fields, source/destination, тип адреса, hop count и приоритет.
- Разбираются TPCI/APCI и групповые сервисы GroupValueRead, GroupValueResponse, GroupValueWrite.
- Для короткого APDU сохраняется шестибитное значение; для длинного APDU — массив data bytes.
- Неизвестные APCI сохраняются как OTHER, а не угадываются.
- Проверяются reserved bit, границы Additional Information, длина NPDU и усечённые кадры.

## Проверки
- Добавлены тесты короткого boolean write/read, DPT9-совместимого payload, индивидуального назначения, Additional Information, неверной длины и malformed frames.
- CI DEV151 должен пройти матрицу Python 3.11/3.12/3.13 и Windows.
- Аппаратная совместимость ещё не проверена.

## Ограничения
- Нет ещё сопоставления cEMI GroupValueResponse/Write с DPT из ETS и общей Point Runtime.
- GroupValueRead parsing implemented, но запросы на шину не отправляются.
- Нет ETS import, KNX Routing и KNX Secure.
