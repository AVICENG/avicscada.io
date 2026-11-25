# Журнал сборки DEV110

## Изменения

- Добавлен `avic_core.deployment.DeploymentManager`.
- Реализован экспорт `.avicpkg` с манифестом и SHA-256 каждого файла.
- Реализованы preview, проверки версии Core и required modules, staged import.
- Встроено исключение типовых secret-файлов; Site Profile отделён от пакета.
- Добавлены проверки целостности, traversal, symlink, дублирующихся записей и лимитов размера.
- Существующий `ProjectBackupManager` сохранён отдельно: backup/restore не смешан с проектным deployment.
- Каталог Platform обновлён: Deployment отмечен как partial, не как законченный.

## Тестирование

- `pytest -q tests/test_deployment_manager.py tests/test_dev109_fbd_graphics_page_flow.py tests/test_network_planning_deployment_dev92.py` — **20 passed** (повторный запуск после дополнительной проверки Site Profile).
- `python -m compileall -q avic_core` — успешно.
- Wheel `avic_core-1.0.0.dev110-py3-none-any.whl` собран с `--no-build-isolation`; SHA-256: `589d995a8338fded5031987eae30a4045731fbb3753a4826cdceb06e45db723e`.
- `pip check` в текущем Linux окружении выявил конфликт уже установленного окружения: `moviepy 2.2.1` требует `pillow<12`, установлена `pillow 12.3.0`. Это не ошибка зависимости AVIC по результату этой проверки, но окружение не чистое.
- Полный `pytest -q -rs` запущен, но достиг тайм-лимита среды примерно на 40% выполнения; полного результата нет. Полный Windows acceptance DEV110 не проводился.

## Известные ограничения

Нет UI/API upload workflow, извлечения проекта из внутренних БД, цифровой подписи, межверсионных миграций, сетевого сопоставления устройств, запуска/активации станции и rollback активной версии. Физические команды не включаются.
