# Журнал сборки и тестирования AVIC Core DEV77

Дата: 22.11.2026  
Версия: `1.0.0.dev77`  
База: DEV69 + AVIC FBD Studio 1.1.1

## Выполнено
- Заменён старый экран FBD `/logic` на FBD Studio 1.1.1.
- Добавлено единое инженерное дерево AVIC с проектами, станциями, сетями, протоколами, устройствами и точками.
- Добавлены FBD-проект, страницы и FBD Points в ветку выбранной станции.
- Добавлена серверная модель авторского FBD Studio документа с привязкой к станции и optimistic concurrency.
- Каталог Core Points запрашивает данные выбранной станции; в модель точки передаются тип и направление.
- Стиль меню/панелей FBD согласован со светлой темой AVIC Workbench.

## Результаты
| Проверка | Результат |
|---|---:|
| Целевой набор (FBD + Engineering Tree + UI + DEV62/63 release contracts + DEV77) | **12 560 passed** |
| `compileall -q avic_core` | OK |
| `node --check` — 3 JS-блока logic.html | OK |
| FastAPI `/logic` | HTTP 200 |
| FastAPI `/api/engineering/tree` | HTTP 200 |
| FastAPI `/api/engineering/points` | HTTP 200 |
| FBD Studio create/get/save/revision conflict | OK |
| Wheel build (`--no-build-isolation`) | OK |

## Неполные проверки
- Полный `pytest -q`: остановлен лимитом 300 секунд около 74%; успешный итог не получен.
- Полный набор без `test_iqvision_matrix_1000_dev50.py`: остановлен лимитом 300 секунд около 73%; успешный итог не получен.
- Playwright Chromium отсутствует; реальный браузерный drag/drop визуально не проверен.
- Windows acceptance не выполнена.

## Известные ограничения
- FBD Studio документ хранится в Core как `authoring-only`; это ещё не компилируемый Core runtime graph.
- Все формулы блоков и точное поведение Trend SET 6.3 не подтверждены.
- Контроллеры BACnet/Modbus не изменяются; полевая запись отключена.
