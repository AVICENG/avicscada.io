# DEV63 — контроль сохранности файлов

- Файлов исходного дерева DEV62 (без кэшей и build-метаданных): 218
- Файлов DEV63 до release artifacts: 223
- Удалённых исходных файлов относительно DEV62: 0
- Новых файлов: 5
- Изменённых файлов: 8

## Удалённые файлы
- Нет.

## Новые файлы
- BUILD_TEST_LOG_DEV63_RU.md
- docs/BUILD_063_RU.md
- docs/DEV63_FILE_PRESERVATION_RU.md
- docs/IQVISION_FIRST_30_PARITY_RU.md
- tests/test_dev63_release_guards.py

## Изменённые файлы
- avic_core/application/container.py
- avic_core/ui/app.py
- avic_core/ui/static/graphics.html
- avic_core/ui/static/index.html
- avic_core/ui/static/logic.html
- avic_core/ui/static/pages.html
- pyproject.toml
- tests/test_dev62_integrated_workflows.py

## Сопоставление release archive

В ZIP DEV62 дополнительно лежал wheel `dist/avic_core-1.0.0.dev62-py3-none-any.whl` (241 169 байт). В DEV63 wheel также включён внутрь ZIP и отдельно приложен для удобства. Поэтому разница размеров архива не связана с удалением исходного кода; DEV63 содержит все 218 файлов исходного дерева DEV62, без удалений.
