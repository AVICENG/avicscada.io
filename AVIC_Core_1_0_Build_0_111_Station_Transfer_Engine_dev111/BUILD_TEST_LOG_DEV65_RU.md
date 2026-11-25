# Журнал проверок DEV65

Дата: 20.11.2026  
Версия: `1.0.0.dev65`  
База исходников: DEV64

## Состав тестового набора

`python -m pytest --collect-only -q`:

```text
30976 tests collected
```

### Единый прогон

Первый полный запуск `python -m pytest -q` не завершился в доступный временной лимит и остановился примерно на 74%. Повторный общий прогон остаточной группы также превысил лимит около 95%. Поэтому **единый полный pytest с exit code 0 не заявляется**.

### Сегментированное покрытие

Все собранные тестовые модули были выполнены полностью отдельными группами. Результаты групп:

| Группа | Результат |
|---|---:|
| `tests/test_fbd_iqvision_dev55.py` | 12 513 passed |
| `tests/test_iqvision_graphics_authoring_dev54.py` | 10 008 passed |
| `tests/test_point_views_iqvision_dev52.py` | 6 727 passed |
| `tests/test_iqvision_matrix_1000_dev50.py` + `test_iqvision_alarm_console_dev53.py` | 1 411 passed |
| 35 оставшихся малых модулей | 208 passed |
| `test_network_onboarding_contracts`, `test_network_topology`, `test_project_station_delete`, `test_project_station_manager` | 18 passed |
| Остальные scheduler/security/trend/UI/page модули | 75 passed; 17 тестов повторно покрывают уже учтённые SVG/Web Pages тесты |
| Дополнительные DEV65/DEV64 Graphics/SVG/Web Pages/release guard тесты | включены в 10 041 targeted-group run; 33 уникальных теста сверх Graphics authoring |

Уникальное покрытие по всему набору: **30 976/30 976 test cases**, 0 известных failed. Количество не суммирует повторные целевые прогоны дважды.

### Целевые DEV65 проверки

```text
python -m pytest -q tests/test_svg_import_dev65.py tests/test_web_pages_authoring_dev65.py
9 passed
```

Расширенный редакторский набор (SVG import, Web Pages Authoring, встроенная SVG library, прежние Web Pages и Graphics authoring, release guards):

```text
10041 passed
```

Проверены: безопасный SVG import, запрет активного/внешнего содержимого, station isolation, persistence, выдача SVG с `nosniff`, запрет удаления используемого SVG, использование custom symbol в Graphics document, сохранение/повторное открытие страницы с 8 типами компонентов, divider 3 px, проверка небезопасных ссылок, slug collision между папкой/страницей, reorder и удаление привязки графики.

### Статические проверки

- `python -m compileall -q avic_core` — успешно.
- Node.js `--check` inline scripts: `index.html`, `graphics.html` (2 блока), `logic.html`, `pages.html` — успешно, `NODE_SYNTAX_OK`.
- `python -m pytest --collect-only -q` — 30 976 tests collected.
- `python -m pip check` — обнаружен один внешний конфликт в общем Python-окружении: `moviepy 2.2.1` требует `pillow<12`, установлен `pillow 12.3.0`. AVIC Core не зависит от `moviepy` или `pillow`; конфликт не связан с зависимостями из `pyproject.toml`.
- `python -m pip wheel . --no-deps --no-build-isolation -w dist` — успешно; изолированная сборка без `--no-build-isolation` не смогла загрузить build-зависимости из-за отсутствия доступа к сети.
- Wheel: `dist/avic_core-1.0.0.dev65-py3-none-any.whl`, 281 197 bytes.
- SHA256 wheel: `ee97e4b57e22996e4c8c4daec6124175887ead23fff59f6587d73fbaf9c01f65`.
- Содержимое wheel проверено: custom SVG library module, Web Pages service, UI editor assets и 28 встроенных SVG-ресурсов присутствуют.
- Сравнение манифеста с DEV64: 9 новых файлов (включая wheel и документацию), 13 изменённых, 0 удалённых; исходная база тестов сохранена.

## Ограничения приёмки

- Chromium заблокирован системной политикой (`ERR_BLOCKED_BY_ADMINISTRATOR`); визуальная приёмка, mouse/browser acceptance и скриншот не заявляются.
- Windows acceptance DEV65 пользователем ещё не выполнена.
- Импортированные SVG очищаются и хранятся на уровне станции, но полноценный графический asset versioning и импорт коллекций/ZIP отсутствуют.
- Web Pages сохраняют дерево/layout и поддерживают визуальный и исходный редакторы. Публикация отключена; компонент Value пока placeholder без Runtime point binding.
- Динамические страницы, production routing, responsive breakpoints и полноценный CSS layout builder не реализованы.
- Runtime и field writes отключены.

## Итог

DEV65 реализует пользовательский импорт безопасных SVG-символов и расширяет Web Pages до сохраняемого визуального конструктора с восемью типами компонентов. Все 30 976 тестовых случаев охвачены сегментированными прогонами без известных отказов; единый полный pytest-процесс по временной причине не был завершён с кодом 0. До признания редакторов готовыми обязательны Windows/browser acceptance и проверка мышиных сценариев у пользователя.
