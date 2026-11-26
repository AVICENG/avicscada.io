# Журнал DEV152 — KNX Point Runtime и Driver Manager

## Изменения
- Добавлен KnxPointAdapter: пассивный мониторинг GroupValueResponse/GroupValueWrite по явно заданным group address и DPT.
- KNX adapter публикует значения через общий PointRuntimeService.publish с owner driver_instance_id.
- При потере транспорта точки получают BAD_COMMUNICATION без затирания последнего значения/времени.
- При некорректном payload конкретной привязки выставляется BAD_CONFIGURATION.
- Driver Manager получил KNX runtime factory; сетевое соединение открывается только при явном старте драйвера.
- Каталог KNX переведён в READ_ONLY_TRANSPORT; запись остаётся запрещённой.
- Исправлен DPT 9.001: 11-битная мантисса обрабатывается как signed two's-complement; 0x7FFF считается invalid pattern.

## Проверки
- Добавлены adapter tests: DPT1, DPT9, неизвестная группа, transport failure, bad payload, DPT/binding validation.
- Обновлён тест каталога Driver Manager: KNX read runtime factory доступна, write запрещён.
- CI DEV152 должен пройти Python 3.11/3.12/3.13 и Windows.
- Реальное KNX IP interface/router hardware acceptance ещё не выполнено.

## Ограничения
- Пассивный мониторинг принимает только GroupValueResponse и GroupValueWrite; GroupValueRead распознаётся, но не инициирует запросы.
- DPT 1.001, 5.001, 9.001 и 14.000; остальные DPT не поддерживаются.
- Нет ETS import, автоматического создания Device/Point, Routing, Secure, COV-like group monitor UI и write operations.
