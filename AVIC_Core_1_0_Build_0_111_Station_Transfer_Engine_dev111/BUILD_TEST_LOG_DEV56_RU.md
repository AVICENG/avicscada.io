# Журнал проверок AVIC Core DEV56

## Новая функциональность DEV56

`tests/test_engineering_workflow_dev56.py` — **12 passed**. Проверены:
- пустая станция и все пять незакрытых этапов;
- отказ для Project вместо Station;
- физическая сеть без протокольного канала не засчитывается;
- успешная связка сеть → канал;
- устройство без драйвера;
- четыре некорректных/неопределённых режима драйвера;
- неожиданное состояние драйвера;
- учёт точек только выбранной станции;
- полная offline-цепочка из пяти этапов;
- HTTP endpoint, 404 и наличие UI entry point.

## Отдельные целевые прогоны

| Набор | Результат |
|---|---:|
| FBD DEV55 `test_fbd_iqvision_dev55.py` | 12 513 passed |
| Graphics DEV54 `test_iqvision_graphics_authoring_dev54.py` | 10 008 passed |
| Point List DEV52 `test_point_views_iqvision_dev52.py` | 6 727 passed |
| Regression matrix DEV50 `test_iqvision_matrix_1000_dev50.py` | 1 164 passed |
| Alarm Console DEV53 `test_iqvision_alarm_console_dev53.py` | 247 passed |
| Engineering Workflow DEV56 | 12 passed |
| Graphics Workbench DEV35 + UI Workbench + combined FBD/workflow/alarm regression run | Включены в combined прогон ниже; отдельно к сумме не прибавляются |

Сумма пяти отдельных функциональных матриц выше: **30 671 passed**. Это сумма результатов отдельных целевых запусков, а не единый запуск всего репозитория. В FBD матрице 12 500 кейсов — параметризованные проверки координатных границ; оставшиеся 13 — функциональные/интеграционные сценарии. Большой счётчик не равен числу уникальных инженерных сценариев.

Дополнительный combined regression run:
`pytest -q tests/test_iqvision_alarm_console_dev53.py tests/test_ui_workbench.py tests/test_fbd_iqvision_dev55.py tests/test_graphics_workbench_dev35.py tests/test_engineering_workflow_dev56.py` — **12 781 passed**.

## Статические проверки

- `python -m compileall -q avic_core tests` — passed.
- `node --check` для JavaScript из `avic_core/ui/static/index.html` — passed.
- `pytest --collect-only -q` — 30 931 тест собран.

## Неполные прогоны и внешняя приёмка

- Полный `pytest -q` в общей среде не завершился в лимит 120 секунд (прерван примерно на 75%); unified full-suite pass не заявляется.
- Дополнительный широкий запуск с исключением четырёх крупных матриц также упёрся в лимит среды почти в конце; он не засчитан как полный pass. Вместо этого критичные матрицы запускались отдельно и завершились успешно.
- Windows acceptance пользователем не выполнен.
- Browser automation/реальный интерактивный smoke в Chromium не засчитан; проверены JS syntax, UI entry point через TestClient и HTTP API.
- Реальный BACnet/Modbus/Trend/TONN контроллер и OT field test не подключались.
- Production deploy/publish не тестировался и в DEV56 отсутствует.

## Итог

DEV56 имеет подтверждённые целевые прогоны и статические проверки. Полный непрерывный regression suite, Windows UI acceptance и OT acceptance остаются открытыми.
