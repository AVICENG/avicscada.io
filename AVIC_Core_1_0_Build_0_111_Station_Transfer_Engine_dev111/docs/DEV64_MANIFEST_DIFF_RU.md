# DEV64 — сохранность исходников и diff относительно DEV63

База сравнения: архив `AVIC_Core_1_0_Build_0_63_Parity30_Regression_UI_dev63 (4).zip`, восстановленный из библиотеки предыдущих файлов. Сравнивались относительные пути и SHA-256 содержимого файлов; `.pytest_cache` и `__pycache__` исключены.

| Показатель | Количество |
|---|---:|
| Файлов в DEV63 | 224 |
| Файлов в DEV64 | 260 |
| Добавлено | 36 |
| Изменено | 12 |
| Удалено | 0 |

## Добавлено — 36 файлов

- `avic_core/graphics/svg_library.py`
- `avic_core/ui/static/svg-library/` — 28 отдельных SVG-файлов
- `tests/test_graphics_svg_library_dev64.py`
- `dist/avic_core-1.0.0.dev64-py3-none-any.whl`
- `docs/BUILD_064_RU.md`, `docs/SVG_LIBRARY_DEV64_RU.md`, `docs/DEV64_MANIFEST_DIFF_RU.md`
- `BUILD_TEST_LOG_DEV64_RU.md`, `INSTALL_DEV64_RU.txt`

## Изменено — 12 файлов

- `avic_core/application/container.py`
- `avic_core/graphics/models.py`
- `avic_core/graphics/service.py`
- `avic_core/ui/app.py`
- `avic_core/ui/static/graphics.html`
- `avic_core/ui/static/index.html`
- `avic_core/ui/static/logic.html`
- `avic_core/ui/static/pages.html`
- `pyproject.toml`
- `tests/test_dev62_integrated_workflows.py`
- `tests/test_dev63_release_guards.py`
- `README_RU.md`

## Удалено

Удалённых файлов DEV63 нет. Старые тесты, пакеты, документация, HTML-страницы и исходники сохранены. Старые regression/release-guard тесты скорректированы под актуальную версию DEV64 (номер версии и theme id), поскольку они проверяют текущие API и Workbench.

## Состав SVG-пакета

В wheel включено 28 файлов `avic_core/ui/static/svg-library/*.svg`. Их наличие в собранном wheel проверено чтением ZIP-контейнера wheel.
