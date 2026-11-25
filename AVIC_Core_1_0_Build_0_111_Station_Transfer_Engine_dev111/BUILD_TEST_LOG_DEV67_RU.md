# Журнал проверок AVIC DEV67

**Версия:** `1.0.0.dev67`  
**База:** DEV66  
**Дата:** 20.11.2026

## Сводка

- `pytest --collect-only -q`: **30 986 тестовых случаев**.
- Все 30 986 случаев прошли в завершённых групповых запусках.
- Единый непрерывный `python -m pytest -q --tb=short` в этой среде не завершился в пределах 600 секунд (остановлен около 74%); поэтому статус единого прогона — **не завершён**, не «passed».
- Дополнительный запуск остаточной группы 58 файлов также превысил лимит; файлы хвостовой группы были затем прогнаны отдельно и прошли.

## Завершённые группы (без пересечения)

| Группа | Команда/состав | Passed |
|---|---|---:|
| FBD / IQVISION | `tests/test_fbd_iqvision_dev55.py` | 12 513 |
| Graphics Authoring | `tests/test_iqvision_graphics_authoring_dev54.py` | 10 008 |
| Point Manager | `tests/test_point_views_iqvision_dev52.py` | 6 727 |
| IQVISION matrix | `tests/test_iqvision_matrix_1000_dev50.py` | 1 164 |
| Alarm Console | `tests/test_iqvision_alarm_console_dev53.py` | 247 |
| Остальные 56 test-файлов, включая DEV67 | все остальные файлы `tests/test_*.py` | 327 |
| **Всего уникальных случаев** | | **30 986** |

Дополнительная перекрёстная графическая регрессия:
`tests/test_graphics_iso3d_library_dev66.py tests/test_graphics_workbench_dev35.py tests/test_iqvision_graphics_authoring_dev54.py` — **10 017 passed**. Эта группа включает 9 проверок, которые также входят в группу «Остальные»; поэтому в уникальный итог они повторно не прибавляются.

## Целевые DEV67

Команда:
`python -m pytest -q tests/test_modular_ahu_sections_dev67.py tests/test_graphics_svg_library_dev64.py tests/test_graphics_iso3d_library_dev66.py`

Результат: **17 passed**. Включая:
- 7 SVG-секций и единый viewBox;
- XML-разбор/отсутствие script и foreignObject;
- классы состояний заслонки, вентилятора и воздушного потока;
- отсутствие глухой боковой стенки у выходного короба;
- binding slots для feedback/value;
- создание и повторное открытие семисекционной схемы через API;
- UI-интеграцию и локальный предпросмотр без полевых команд;
- признаки возможностей в API manifest.

## Дополнительные проверки

- `python -m compileall -q avic_core tests` — успешно.
- Node.js `--check` для 2 inline script блоков `graphics.html` — успешно.
- Все 7 новых SVG сгенерированы CairoSVG в PNG preview; SVG XML разбирается.
- API `/api/graphics/library` проверяется тестами; старые 59 символов сохранены, общий каталог — 66.
- Манифест и platform status сообщают `1.0.0.dev67`.
- `field_commands_enabled` остаётся `false`.

## Непроведённые приёмки / ограничения

- Визуальный браузерный тест Chromium недоступен в среде сборки из-за блокировки администратора.
- Установка/запуск на целевом Windows-ПК не проверены в этой сессии; нужен пользовательский приёмочный тест.
- Единый непрерывный pytest не получил итогового exit code в среде сборки.
- `pip check` среды сборки содержит посторонний конфликт `moviepy`/`Pillow`, не относящийся к зависимостям AVIC; wheel проверяется отдельно.
- Реальная live-анимация зависит от обновления point snapshot драйвером/Runtime. Физическая запись команд не реализована.

## Приёмочная проверка API и wheel

- `python -m pip wheel . --no-deps --no-build-isolation --wheel-dir dist` — wheel `avic_core-1.0.0.dev67-py3-none-any.whl` успешно создан (405 968 bytes).
- ZIP-контейнер wheel проверен; включено **66 SVG-ресурсов**, в том числе все 7 новых `ahu_section_*.svg`.
- Wheel установлен в отдельный target-каталог без перезаписи текущего окружения; импорт `avic_core.graphics.svg_library` и чтение каждого нового SVG из установленного wheel успешны.
- API smoke через FastAPI TestClient: UI health сообщает DEV67, библиотека возвращает 66 символов, создание проекта/станции и `POST /api/stations/{station_id}/graphics/ahu-demo` успешны, создано 7 секций с X-позициями `[18, 304, 590, 876, 1162, 1448, 1734]`, SVG охладителя возвращается как `image/svg+xml`.
- Новые SVG проверены XML parser; единый viewBox и `data-avic-style="iso3d"` подтверждены для 7/7 ресурсов.

## Контроль состава ZIP

Перед упаковкой удалены генерируемые `build/` и `avic_core.egg-info/`; в архив включаются исходный пакет и wheel из `dist/`, без дублирующегося `build/lib`. Итоговая проверка ZIP выполняется после пересоздания архива: `ZipFile.testzip()`, проверка 66 исходных SVG в `avic_core/ui/static/svg-library/`, 7 новых `ahu_section_*.svg` и наличие wheel `avic_core-1.0.0.dev67-py3-none-any.whl`.

Финальная проверка архива после удаления временной папки `build/` и старых промежуточных wheel:

- ZIP: `AVIC_Core_1_0_Build_0_67_AHU_Modular_Animation_dev67.zip` — **2 640 502 байта**, 339 файловых элементов; `ZipFile.testzip()` вернул `None`.
- В корневом исходном пакете архива: **66 SVG**, из них **7 новых модульных секций ПВУ**. Дубликатов из `build/lib` нет.
- В `dist/` включён только wheel DEV67 (`avic_core-1.0.0.dev67-py3-none-any.whl`, 405 968 байт).
- SHA-256 ZIP указан в отдельном файле `.zip.sha256.txt`.
