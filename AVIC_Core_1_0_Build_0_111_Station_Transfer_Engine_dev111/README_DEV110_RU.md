# AVIC Core 1.0 — DEV110

Сборка продолжает DEV109 и добавляет первый слой Deployment Manager для переносимых инженерных пакетов `.avicpkg`.

## Установка

```powershell
python -m pip install avic_core-1.0.0.dev110-py3-none-any.whl
```

## Документация

- `docs/DEPLOYMENT_MANAGER_DEV110_RU.md` — формат пакета, экспорт, проверка и staged import.
- `BUILD_TEST_LOG_DEV110_RU.md` — результаты и ограничения тестирования.
- `CHANGELOG_DEV110_RU.md` — изменения DEV110.

## Статус

Deployment Manager частично реализован как Core service. Это ещё не законченный UI-процесс переноса и не готовая активация на промышленной станции. Полная Windows acceptance проверка должна быть выполнена на компьютере разработчика.
