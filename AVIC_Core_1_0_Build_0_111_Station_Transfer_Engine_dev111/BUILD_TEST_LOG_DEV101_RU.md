# Журнал сборки DEV101

## Исправление
- Убран переход Repository в старый `pages.html` / Web Pages workspace.
- `/repository` и legacy `/pages` открывают Core Graphics Workbench (`graphics.html`), который содержит собственную SVG-библиотеку и станционный импорт SVG.
- Ветка Repository развернута по согласованной структуре: Web Application, Graphics (Pages, Components, Symbols, Assets, Templates), Documentation.
- Сохранена авторитетность Core для устройств, драйверов, точек, FBD и прав; Repository не владеет Core-объектами.

## Ограничения
- Это исправление дерева и точки входа, а не завершённый перенос DEV23 Repository Manager.
- Web Application, Documentation и CRUD/редактор страниц-компонентов-ресурсов ещё требуют отдельной интеграции с Core-хранилищем и Core RBAC.
- Полный pytest не объявляется пройденным до отдельного полного запуска.

## Фактические проверки DEV101
- `python -m compileall -q avic_core`: успешно.
- Выборочные тесты: **27 passed** (Repository/tree, shared navigation, Graphics Binding Engine, SVG library, ISO 3D library).
- Полный pytest не запускался.
- Wheel: `avic_core-1.0.0.dev101-py3-none-any.whl`, SHA256 `ef8c53e13ae7460ae5d9e889c35dd919467f09b50f7e99d663539b3160073646`.
- `pip check` не прошёл из-за внешнего конфликта среды: `moviepy 2.2.1` требует `pillow<12`, установлен `pillow 12.3.0`.
- Первая попытка wheel build с изоляцией не смогла скачать setuptools из-за отсутствия сетевого доступа; повторная сборка с `--no-build-isolation` прошла успешно.
