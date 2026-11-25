# AVIC Core 1.0 — DEV109

DEV109 — следующая инженерная сборка после DEV108.

## Основной сценарий

`FBD Studio → Compile → Core Point Runtime → Engineering Tree → Graphics Workbench → Point Bindings → Repository Page Builder → Publish → Operator Runtime`

## Проверенное поведение

- FBD-выход компилируется и регистрируется как виртуальная точка с устойчивым ID.
- Значение и качество точки доступны в инженерном дереве и Graphics Point Catalog.
- Графический элемент вентилятора сохраняет отдельные привязки обратной связи и качества.
- Страница включает значение точки и мнемосхему, сохраняется и публикуется.
- Опубликованная мнемосхема возвращает runtime-значение и качество точки.
- Сохранённые страница, графика и привязки доступны после повторного открытия приложения с тем же каталогом данных.

## Ограничения

- Автоматизированный тест не имитирует реальные действия мышью в браузере; он проверяет backend flow и статические UI-контракты drag-and-drop.
- Физические записи BACnet/Modbus не включены.
- Публикация не означает автоматического разрешения команд управления.

## Установка

```cmd
python -m pip install -e ".[dev]"
python -m avic_core --help
```

## Проверка

```cmd
python -m compileall -q avic_core
python -m pytest -q tests\test_dev109_fbd_graphics_page_flow.py
python -m pytest -q -rs > pytest_dev109.txt 2>&1
```
