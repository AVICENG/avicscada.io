# Журнал сборки и тестирования DEV107

Дата: 23.11.2026  
База: загруженный пользователем архив DEV106 (`AVIC_Core_1_0_Build_0_106_Command_Manager_Simulation_dev106.zip`).

## Что изменено

- Исправлен переход из общего инженерного дерева: корневой узел «Репозиторий» станции теперь открывает `Web Application` Page Builder с сохранением `station_id`.
- Отдельная ветка `Graphics` продолжает открывать Graphics Workbench; поведение не смешано с Web Application.
- Старый `pages.html` по-прежнему не используется в маршрутах Repository.
- Версия приложения и `/api/ui/health` синхронизированы с `1.0.0.dev107` (в DEV106 health endpoint ошибочно сообщал `dev105`).
- Добавлена русская инструкция по созданию сайта/страницы, компоновке, загрузке изображений, привязке Core Points, добавлению мнемосхем и публикации.
- Добавлены регрессионные тесты для маршрута из общего дерева и версии health endpoint.

## Проверки

Среда: Linux x86_64, Python 3.13.5.

| Проверка | Результат |
|---|---|
| Фокусные Web Pages / Repository / navigation / FBD runtime / Command Manager тесты | **37 passed** (включая отдельный end-to-end сценарий AHU) |
| `python -m compileall -q avic_core` | OK |
| `node --check` для inline JS `repository.html` | OK |
| `python -m pip wheel . --no-deps --no-build-isolation` | OK, wheel 529 447 байт |
| Установка wheel в отдельный target | OK |
| Smoke test установленного wheel: import, `/api/ui/health`, Web Application и Graphics routes | OK |
| `python -m pip check` | Внешнее предупреждение окружения: `moviepy 2.2.1` требует `pillow<12`, в окружении `pillow 12.3.0`; AVIC не добавляет Pillow в зависимости |

## Полный набор

- `pytest --collect-only`: **31 137 тестовых случаев**.
- Полный `pytest -q --disable-warnings` запускался 15 минут; прогресс дошёл примерно до 40%, команда остановлена лимитом времени. Итогового полного результата нет.
- Дополнительный прогон после исключения четырёх крупнейших параметризованных наборов собрал 725 тестов; за 10 минут дошёл примерно до 79%, затем остановлен лимитом времени. Итогового результата для этого набора также нет.
- Это ограничения времени прогона в данной Linux-среде, а не зафиксированные ошибки тестов. Полный Windows acceptance на целевой машине пользователя не выполнялся.

## Известные ограничения, не закрытые DEV107

- Кнопка в Page Builder остаётся декоративной; интеграции опубликованной страницы с Command Manager нет.
- Command Manager DEV106 — строго `SIMULATION_ONLY`; физические BACnet/Modbus записи не выполняются.
- Нет полноценной пользовательской session/authentication, server-side RBAC, station/equipment scopes и MFA. Мутации Workbench защищены loopback-only development guard.
- Предпросмотр в редакторе не заменяет отдельное браузерное acceptance-тестирование на Windows.
- Нет production deployment profile с TLS/reverse proxy и эксплуатационным hardening.

## Статус

**DEV107 — исправлена точка входа из инженерного дерева в Page Builder, подтверждена совместимость с Graphics Workbench и проверена установка wheel.** Это промежуточная инженерная сборка, а не завершённый AVIC SCADA и не разрешение физического управления.
