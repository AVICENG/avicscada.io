# Пересборка SVG секций ПВУ DEV67

Генератор: `tools/create_modular_ahu_assets.py`.

Он создаёт семь самостоятельных SVG, растровые preview и общую assembly preview. Скрипт использует CairoSVG и Pillow только для preview; сами SVG создаются как текстовые векторные ресурсы.

Для запуска из корня проекта:

```cmd
python -m pip install cairosvg pillow
python tools\create_modular_ahu_assets.py
```

После изменения геометрии проверьте общие стыки, `viewBox="35 62 317 185"`, затем выполните целевые DEV67 tests. Не меняйте ID без миграции сохранённых GraphicElement: `symbol_key` является постоянным ключом ресурса.

Анимация остаётся CSS/SVG:
- `.state-damper-open .damper-blades`
- `.state-fan-running .fan-rotor`
- `.state-airflow .ahu-air-dash`

Runtime state classes добавляются редактором на встроенный SVG-корень; сами SVG не содержат скриптов.
