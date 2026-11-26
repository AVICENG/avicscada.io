# AVIC Core — журнал сборки DEV193

Дата: 26.11.2026

## Изменения
- Исправлена интеграция FBD SCHEDULE с Core Scheduler Manager.
- В свойствах блока выбирается сохранённое расписание текущей станции.
- В FBD документе сохраняются schedule_id, schedule_value_type и schedule_name; приватный календарь блока удаляется после выбора Core Schedule.
- Выходной порт получает тип из value_type расписания.
- Локальная FBD симуляция обновляет значения SCHEDULE через Core evaluate API; ошибка/отсутствующая ссылка не подменяется фиктивным значением.
- SCHEDULE вынесен в отдельную группу палитры «Расписания».
- Добавлены тесты для отказа старого локального расписания, компиляции по Core schedule_id и UI-интеграции.
- Версия пакета и runtime metadata обновлены до 1.0.0.dev193.
- Добавлен аудит Trend SET parity: 26 Function Modules, 8 Logic Modules, Schedule H, Time Zone/OSS и прочие семейства.

## Исправление предыдущего заявления
Наличие 29 типов AVIC в UI/Core/Compiler не означает полного набора Trend SET. Аудит DEV193 перечисляет конкретные отсутствующие и частично совпадающие функции. Trend H Schedule Module не равен Core Scheduler SCHEDULE block.

## Проверки
- Тесты добавлены, но DEV193 пока не запускался в Windows/Linux CI.
- Статус сборки: НЕ ПОДТВЕРЖДЁН.

## Известные ограничения
- Scheduler weekly grid без drag/resize; события можно добавлять/удалять, но не редактировать на месте.
- Нет полного schedule CRUD, Calendar Manager, отдельного Scheduler Runtime journal и Trend schedule import/export.
- Нет Command Manager для реальных field writes; физические записи по расписанию запрещены.
- Trend H / Z / OSS и значительная часть Trend Function/Logic Modules ещё не реализованы.
- PIN/RBAC runtime path не подключён.

## Готовность
DEV193 — исправление интеграции и уточнение parity scope; не готовый parity release.

- SCHEDULE переименован в палитре в Core Schedule, чтобы не путать с Trend Schedule Module H.
- Если у импортированного SCHEDULE отсутствует schedule_value_type, порт помечается unknown до явного выбора расписания; BOOL не угадывается.
