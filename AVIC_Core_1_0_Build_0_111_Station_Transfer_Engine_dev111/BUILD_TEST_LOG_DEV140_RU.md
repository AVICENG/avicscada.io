# DEV140 — журнал сборки и тестирования

Дата: 25.11.2026

## Изменения
- Добавлен общий `ProtocolDeviceImportService`.
- Добавлены API preview/import для нормализованных discovery-результатов.
- Сохранён прежний BACnet import API.
- Импорт Device и Point выполняется одной SQLite-транзакцией.
- Входные данные проверяются до записи; runtime и полевые устройства не запускаются.

## Новые тесты
- `tests/test_protocol_point_import_dev140.py`
  - preview не меняет БД;
  - импорт и повторный импорт;
  - импортированная точка читается из Point Runtime и FBD;
  - проверка station/driver/protocol isolation;
  - отказ при дублировании native identity;
  - HTTP API preview и commit.

## Статус
<badge>Код добавлен, CI ещё не подтверждён</badge>

Тесты в этой среде не запускались: доступ к репозиторию выполнен через GitHub API без локального checkout и без исполнения проекта. Не считать DEV140 принятым до зелёной матрицы GitHub Actions и локального Windows acceptance run.

## Не закрыто
- Автоматическая передача реальных результатов BACnet/Modbus discovery в общий normalized contract.
- Инженерный UI для выбора точек и массового импорта.
- Параметрические adapter contract tests и полные BACnet/Modbus → Runtime → FBD → Graphics → Web Page E2E.
- Trend IP протокол и реальные аппаратные тесты.
