# DEV64 → DEV65: сохранность и состав файлов

Сравнение выполнено по содержимому ZIP исходной сборки DEV64 и рабочей директории DEV65. В расчёт включены файлы проекта; `.pytest_cache`, `__pycache__`, `.pyc` исключены.

До добавления этого manifest:

- DEV64: 260 файлов;
- DEV65 рабочее дерево: 267 файлов;
- новых: 7;
- изменённых: 12;
- удалённых: 0.

После включения manifest, README и собранного wheel DEV65 содержит 269 файлов: 9 новых, 13 изменённых и 0 удалённых.

## Новые файлы

- `avic_core/graphics/custom_svg_library.py`
- `tests/test_svg_import_dev65.py`
- `tests/test_web_pages_authoring_dev65.py`
- `docs/BUILD_065_RU.md`
- `BUILD_TEST_LOG_DEV65_RU.md`
- `CHANGELOG_DEV65_RU.md`
- `INSTALL_DEV65_RU.txt`
- `docs/DEV65_MANIFEST_DIFF_RU.md` (этот файл)
- `dist/avic_core-1.0.0.dev65-py3-none-any.whl` — собранный wheel

## Изменённые файлы

- `avic_core/application/container.py` — регистрация сервиса пользовательских SVG.
- `avic_core/graphics/models.py` — поддержка custom symbol key.
- `avic_core/graphics/service.py` — каталог и сохранение station-scoped SVG symbols.
- `avic_core/ui/app.py` — API импорта/выдачи/удаления SVG, API сортировки страниц, аудит, версия DEV65.
- `avic_core/ui/static/graphics.html` — импорт, поиск, фильтрация и вставка пользовательских SVG.
- `avic_core/ui/static/pages.html` — визуальная разработка страниц, инспектор и операции над деревом.
- `avic_core/ui/static/index.html` — общая версия DEV65.
- `avic_core/ui/static/logic.html` — общая версия DEV65.
- `avic_core/web_pages/service.py` — layout validation, url validation, reorder, collision checks и очистка graphic references.
- `pyproject.toml` — версия 1.0.0.dev65.
- `tests/test_dev62_integrated_workflows.py` — ожидаемая версия.
- `tests/test_dev63_release_guards.py` — проверки версии/темы DEV65.
- `README_RU.md` — актуальное описание DEV65 и ограничения.

## Неизменённые важные области

FBD/Runtime, Project/Station, BACnet/Modbus, Security, Licensing и прежние тестовые файлы DEV64 сохранены в исходном виде, если не указаны выше.
