# AVIC Core 1.0 — DEV83

DEV83 развивает DEV82. Основной фокус — стандарт именования и нумерации FBD-блоков и точек, а также дополнительная защита SVG-соединений от заливки.

Установка в отдельную папку Windows:

```bat
python -m pip install -e ".[dev]"
python -m pip check
python -m compileall -q avic_core
python -m pytest -q --tb=short tests/test_fbd*.py tests/test_engineering_tree*.py tests/test_ui_workbench.py
python -m avic_core.ui --host 127.0.0.1 --port 8001 --data-dir .\\avic_data
```

Перед заменой рабочей папки сделайте резервную копию проекта и данных. Не распаковывайте DEV83 поверх DEV82.
