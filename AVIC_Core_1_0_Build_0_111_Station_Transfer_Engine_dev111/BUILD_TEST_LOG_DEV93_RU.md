# Журнал испытаний DEV93

## Объём изменений

Изменены `avic_core/ui/static/index.html`, русскоязычные руководства и версия пакета. Core сетевые контракты и TimeManagementService не переписывались.

## План проверок

- Целевые тесты Network Planning DEV92, Network Onboarding, Time Manager API и UI Workbench.
- Проверка синтаксиса всех встроенных JavaScript-блоков страницы Workbench через Node.js.
- `compileall` для пакета и тестов.
- Сборка wheel и проверка ZIP.

## Фактические результаты

Будут записаны после выполнения проверок в этой среде. Полная регрессия репозитория и Windows-приёмка не должны считаться пройденными без соответствующего запуска.

## Результаты

- Целевой набор тестов: **65 passed** за 8,95 секунды.
- В набор включены DEV93 UI guidance, DEV92 Network Planning, Network Onboarding, Network API/topology/hierarchy, Scheduler Manager, Project/Station Manager, UI Workbench и Secret Store.
- `node --check` встроенного JavaScript Workbench: успешно.
- `python -m compileall -q avic_core tests`: успешно.
- `python -m avic_core --help`: успешно.
- Полный набор всех тестов репозитория не запускался в этой сборке.
- Проверка на Windows и визуальная приёмка в браузере пользователем ещё не выполнены.
