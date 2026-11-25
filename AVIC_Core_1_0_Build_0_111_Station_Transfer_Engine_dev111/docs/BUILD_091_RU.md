# DEV91 — FBD Project Package и Schedule Block

## Реализовано в этой сборке
- FBD JSON package `.avicfbd.json`, manifest `avic.fbd.project-package`, schema version 1.
- SHA-256 контроль целостности `project` payload.
- Открытие нового package и legacy JSON.
- Валидация структуры страниц, блоков и ссылок до подтверждения замены текущего документа.
- Новый блок `SCHEDULE`: BOOL/числовой выход, недельные интервалы, исключения по датам, приоритет, timezone IANA, default value, ручное override с expiry в модели конфигурации.
- Расписание учитывает интервалы через полночь и локальное время указанного часового пояса.

## Сверка предоставленных Trend материалов
- `12345.TSET`: файл имеет сигнатуру `Standard Jet DB`; содержимое бинарное, не разобрано на таблицы/поля в этой сборке.
- `Meridian.TSITE`: читаемый XML `TrendProject`; описывает несколько Site/LAN/Device и сетевые адреса, не содержит расписаний FBD.
- `ToolSET.zip`: содержит в основном бинарные OCX/DLL/EXE и `spidData.xml`; исходный код UI/алгоритма Schedule не предоставлен.
- `SET_Meridian_26.01.21.rar`: список архива содержит TSET/backup-файлы, TSITE, контроллерные IQ/IQBak и IQTool-шаблоны. Архив не декодирован в этой сборке.
- Поэтому Schedule UI и поведение в DEV91 сделаны как собственная реализация AVIC по инженерным требованиям; не заявляется точное побитовое/визуальное копирование Trend SET.

## Ограничения
- Пакет пока JSON с manifest и checksum, не ZIP с набором зависимостей.
- Импорт `.TSET` и `.TSITE` как FBD-проект не реализован.
- Schedule блок пока исполняется только в локальной симуляции редактора. Нет связи с Core ScheduleService, FBD cyclic Runtime, PointRuntime, Historian или Command Manager.
- Ручной override поддерживается в модели блока с expiration timestamp, но пользовательский UI для временного override в отдельном runtime faceplate ещё не сделан.
- Физические записи в контроллеры отсутствуют.

## Проверки DEV91
- 12 549 выбранных regression tests passed.
- Python compileall passed.
- Node syntax check для всех встроенных JS в logic.html passed.
- Wheel собран.
- Полная регрессия репозитория, Windows acceptance и браузерная визуальная проверка не выполнялись.
