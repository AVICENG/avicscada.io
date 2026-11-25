# AVIC Core 1.0 · DEV101

DEV101 исправляет ошибочную интеграцию DEV99/DEV100: ветка Repository больше не открывает старый Web Pages workspace. Она открывает Core Graphics Workbench с библиотекой встроенных и пользовательских SVG-символов, привязанной к выбранной станции.

Структура дерева под каждой станцией:

- Repository
  - Web Application
  - Graphics
    - Pages
    - Components
    - Symbols
    - Assets
    - Templates
  - Documentation

Devices, Drivers, Points, Logic/FBD, Schedules, Alarms и Security остаются объектами/службами Core. Репозиторий не создаёт их копий и должен ссылаться на Core IDs.

DEV101 не заявляет, что Web Application, Documentation и все подузлы Graphics уже имеют отдельные CRUD-процессы: на этом этапе реализованы согласованная навигационная структура и открытие нового Graphics Workbench. Полноценная миграция DEV23 Repository UI/API остаётся отдельной задачей.
