# FBD-проект: пакетирование и Schedule

## Формат пакета
`.avicfbd.json` — JSON-документ со следующими полями:
- `schema`: `avic.fbd.project-package`
- `schemaVersion`: `1`
- `createdAt`
- `project`: данные редактора (страницы, блоки, связи, ссылки, FBD-точки)
- `integrity.algorithm`: `SHA-256`
- `integrity.digest`: SHA-256 от компактного `JSON.stringify(project)`.

Это проверка целостности, не цифровая подпись и не подтверждение доверенного автора.

## Открытие
1. File → Open FBD file…
2. Прочитать пакет.
3. Проверить SHA-256 для нового формата.
4. Проверить страницы, ID блоков и ссылок.
5. Подтвердить замену текущего документа.
6. Импортировать структуру; прежний legacy JSON остаётся поддержан.

## Блок SCHEDULE и Scheduler Manager

Начиная с DEV193 блок `SCHEDULE` не хранит собственный недельный календарь. Он ссылается на объект Scheduler Manager текущей станции через `schedule_id`.

- В свойствах блока выбирается существующее расписание станции.
- Выходной тип берётся из Core `value_type`: BOOLEAN, NUMERIC, STRING или ENUM.
- Компилятор проверяет существование расписания и принадлежность той же станции.
- Локальная FBD-симуляция получает значение через Core Scheduler evaluate API.
- Недельные интервалы, исключения, часовой пояс, effective dates и override редактируются в Scheduler Manager.
- Старые пакеты с локальным `params.schedule` требуют ручного выбора Core Schedule. Автоматический перенос не выполняется, потому что нельзя безопасно угадать соответствие и ревизию объекта.
- Симуляция и компиляция не выполняют физические записи; публикация остаётся отдельной операцией.

**Важно:** AVIC FBD `SCHEDULE` — потребитель Core Schedule Service. Это не Trend IQ3 Schedule Module H с аналоговыми входами Manual/Non-Occupied/Warm-Up/Occupied/Cool-Down/Manual Level и не реализация Trend OSS/OTP.
