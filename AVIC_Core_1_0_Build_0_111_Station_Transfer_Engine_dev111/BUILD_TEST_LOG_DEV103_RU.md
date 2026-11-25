# Журнал сборки DEV103

Дата: 2026-11-23
База: пользовательский архив AVIC Core DEV102.

## Изменения
- Добавлена сущность `FBDExposedPoint` и поддержка в общем `PointRuntimeService`.
- FBD Studio compiler сохраняет `studio_module_id` в скомпилированных узлах и регистрирует выходные виртуальные точки.
- Циклический FBD Runtime публикует значения в виртуальные точки, а при остановке/ошибке маркирует качество `STALE`/`BAD_CONFIGURATION`.
- Добавлены FBD Runtime HTTP endpoints start/stop/status/tick; `background: false` обеспечивает детерминированный ручной tick в приёмке.
- Engineering Tree, Engineering Points API и Graphics Point Catalog показывают виртуальные точки и их live values.
- Engineering Tree обновляет значения без полного перерисовывания дерева каждые 2 секунды, пока панель открыта.
- Graphics Service принимает виртуальные FBD-точки в read-only bindings; Graphics Workbench принимает drag-and-drop физических/FBD точек из общего дерева.

## Тесты
- `pytest -q tests/test_dev103_fbd_exposed_runtime_points.py tests/test_dev85_point_runtime.py tests/test_dev90_fbd_cyclic_runtime.py tests/test_dev95_fbd_studio_compiler.py tests/test_engineering_tree_values_dev39.py tests/test_graphics_binding_engine_dev98.py tests/test_ahu_fbd_to_fan_animation_dev102.py` — 35 passed.
- `python -m compileall -q avic_core` — OK.
- Node.js `node --check` — OK.
- Полный `pytest -q`: 31 125 тестовых случаев собрано; запуск достиг 40% и остановлен по лимиту 300 секунд. Это не полный проход.

## Не подтверждено
- Полный тестовый набор.
- Windows acceptance.
- Физическое управление BACnet/Modbus.
- Публикация Graphics Page для оператора.
- Полная RBAC интеграция для runtime/publish API.

## Артефакты
- Wheel: `avic_core-1.0.0.dev103-py3-none-any.whl`, SHA256 `6a6e9f5aad6135b77459137f3d727be22fced6d27e60425399c8263e6e2c25b7`.
- Wheel установлен в отдельный target-каталог без зависимостей; импорт `avic_core`, `FBDExposedPoint` и создание UI приложения (141 маршрут) проверены.
- `pip check` в общей среде сообщает внешний конфликт: `moviepy 2.2.1` требует `pillow<12.0`, но установлен `pillow 12.3.0`. Это не объявленная зависимость AVIC Core.
- ZIP прошёл `unzip -t` без ошибок.
- ZIP SHA256: `b4f85e44f4bc79ff98fe4d5069ee194b0d125f77595c4d22d52390d0e49d7679`.
