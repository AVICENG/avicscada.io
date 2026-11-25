# Журнал проверок DEV63

Дата: 19.11.2026

## Состав тестирования

- `pytest --collect-only -q`: **30 960 тестов собрано**.
- Workbench/UI + DEV63 release guards + DEV62 workflows + DEV57 Driver Manager + DEV56 Engineering Workflow: **45 passed**.
- Graphics DEV54 + FBD DEV55 + Alarm Console DEV53 + Point Views DEV52: **29 495 passed**.
- Остальные 47 файлов тестов: **1 420 passed**.
- Итого: **30 960 passed в трёх непересекающихся запусках**, без зарегистрированных падений в этих группах.
- `python -m compileall -q avic_core tests`: успешно.
- Node.js `--check`: все inline scripts в `index.html`, `pages.html`, `logic.html`, `graphics.html` синтаксически корректны (5 script blocks).

## Release guards и обнаруженный дефект

DEV63 проверяет все 4 HTML entrypoints, общую тему, внутренние ссылки редакторов, наличие ключевых пакетов, ключевые API endpoints, все 45 GET API route paths и все 55 изменяющих API method paths в безопасном probe-режиме.

Проверка некорректного ID выявила дефект: `GET /api/web-pages/{node_id}` передавал невалидный UUID в Repository, где возникал `ValueError` и HTTP 500. Исправлено: endpoint теперь возвращает HTTP 400 с понятным сообщением. Добавлен отдельный регрессионный тест.

## Ограничения и честный статус

- Единый запуск `pytest -q` в этой среде дважды не завершился в лимите времени (600 секунд; около 74% прогресса). Поэтому он **не засчитывается как единый полный прогон**. Все 30 960 собранных тестов прошли в трёх непересекающихся группах. Причину зависания/накопления ресурсов при объединённом запуске необходимо отдельно диагностировать.
- Реальный Chromium smoke заблокирован средой (`ERR_BLOCKED_BY_ADMINISTRATOR`) и для localhost, и для file URL. Поэтому визуальная интерактивная приёмка браузером не подтверждена; проверены TestClient routes и JS syntax.
- Windows acceptance на пользовательском ПК не выполнен.
- Реальные BACnet/Modbus контроллеры и OT field writes не проверялись; полевые команды остаются отключёнными.
- `pip check` показывает внешний конфликт установленной среды: `moviepy 2.2.1` требует `pillow<12`, установлена `pillow 12.3.0`. Это не конфликт зависимостей AVIC из `pyproject.toml`.

## Готовность

DEV63 — development-сборка с матрицей первых 30 разделов/приложений, общей темой UI, регрессионными release guards и исправлением некорректного UUID path. Она **не является промышленно принятой**: остаются обязательные Windows/browser/OT acceptance и диагностика единого полного pytest запуска.
