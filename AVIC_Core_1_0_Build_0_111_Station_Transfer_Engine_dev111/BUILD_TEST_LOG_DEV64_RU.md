# Журнал проверок DEV64

Дата: 19.11.2026  
Версия: `1.0.0.dev64`  
База: DEV63

## Итог единого прогона

```text
python -m pytest -q --tb=short
30967 passed in 56.50s
```

Единый полный pytest завершился с кодом `0`: **30 967 passed, 0 failed, 0 skipped**.

## Целевые тесты DEV64

```text
python -m pytest -q tests/test_graphics_svg_library_dev64.py tests/test_dev63_release_guards.py tests/test_dev62_integrated_workflows.py
30 passed in 4.36s
```

Новые проверки покрывают:

- наличие 28 настоящих SVG-файлов в пакете и каталог из 7 категорий;
- API выдачи библиотеки и SVG, проверку Content-Type/nosniff и неизвестного ID;
- сохранение/повторное открытие Graphics документа с новым SVG symbol key;
- выбор станции и существующего документа в FBD;
- тестовый fan FBD workflow: создать → открыть → симулировать офлайн;
- пункт верхнего меню SVG-библиотеки и перенос dropdown в body для защиты от clipping;
- контракт Project Tree с отдельными массивами projects/stations и drag-and-drop в Graphics.

## Дополнительные проверки

- `python -m compileall -q avic_core tests` — успешно.
- Node.js `--check` для inline JavaScript в `index.html`, `graphics.html`, `logic.html`, `pages.html` — синтаксических ошибок нет (5 script blocks).
- Wheel `avic_core-1.0.0.dev64-py3-none-any.whl` собран; проверка содержимого wheel подтвердила наличие Graphics/FBD HTML и 28 SVG-ресурсов.
- API smoke через FastAPI TestClient: `/`, `/api/ui/manifest`, `/api/ui/health`, `/api/graphics/library`, `/api/fbd/library`, `/api/projects/tree` вернули успешные ответы; каталог вернул 28 символов, FBD library — 12 типов блоков.

## Не пройдена / не выполнена приёмка

- Chromium в среде сборки запрещает переход и на localhost, и на file URL: `ERR_BLOCKED_BY_ADMINISTRATOR`. Поэтому визуальная браузерная приёмка, клики мышью и screenshot acceptance **не заявляются**.
- Windows acceptance пользователем для DEV64 ещё не выполнена.
- Реальные BACnet/Modbus контроллеры и OT-сеть не проверялись.
- Полевые записи и Runtime execution остаются отключёнными.

## Окружение сборки

`python -m pip check` в общей среде сборки сообщил внешний конфликт: `moviepy 2.2.1` требует `pillow<12`, установлена `pillow 12.3.0`. Это конфликт посторонних пакетов общей среды, не зависимостей AVIC, перечисленных в `pyproject.toml`. Wheel успешно собран через локальный build backend без изолированной загрузки build-зависимостей из сети.

## Заключение

DEV64 улучшает редакторский слой: добавляет встроенную SVG-библиотеку и доводит базовые Graphics/FBD authoring flows до сохранения/повторного открытия и офлайн-симуляции FBD. Единый pytest пройден. Сборка **не считается промышленно готовой и не заявляется как полная IQVISION/Niagara parity**: обязательны визуальная приёмка на Windows, дальнейшая редакторская работа и проверка реальных драйверов/Runtime.
