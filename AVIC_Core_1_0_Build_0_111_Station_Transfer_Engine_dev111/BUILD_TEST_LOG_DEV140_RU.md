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
  - та же точка доступна в Graphics catalog, получает PointBinding и отображается в Web Pages через value binding;
  - BACnet analog/binary data types и явное направление точки;
  - диапазоны Modbus uint16/int16 и scalar float types в Point Runtime;
  - проверка station/driver/protocol isolation;
  - отказ при дублировании native identity;
  - HTTP API preview и commit.

## Статус
<badge>Код добавлен, CI ещё не подтверждён</badge>

Тесты добавлены в репозиторий. GitHub Actions запущен для ветки dev113; первый запуск был прерван последующими push-коммитами до получения итогового отчёта. Окончательный результат матрицы для текущего HEAD ожидается. Локальный Windows acceptance run не выполнялся. Не считать DEV140 принятым до зелёной матрицы GitHub Actions и локальной Windows проверки.

## Не закрыто
- Автоматическая передача реальных результатов BACnet/Modbus discovery в общий normalized contract.
- Инженерный UI для выбора точек и массового импорта.
- Автоматическая передача живых BACnet/Modbus discovery results в общий importer; текущий E2E использует нормализованный discovery snapshot.
- Параметрические adapter contract tests для всех адаптеров; текущие проверки сквозного пути начинаются с нормализованной точки.
- Trend IP протокол и реальные аппаратные тесты.
