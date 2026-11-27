# DEV203 — Point Runtime: порядок измерений и восстановление качества

## Реализовано
- Point Runtime отклоняет sample, timestamp которого старше последнего принятого timestamp.
- Отклонение выполняется до записи в репозиторий и до вызова подписчиков.
- Если timestamp не передан, используется текущее UTC-время, которое также проверяется на монотонность.
- Timestamp сохранённого значения обязан содержать часовой пояс.
- `mark_quality()` не заменяет последнее значение и timestamp измерения.
- Сценарий потери связи использует `BAD_COMMUNICATION`; восстановление `GOOD` происходит только после нового sample.

## Регрессионные тесты
- `test_point_runtime_rejects_out_of_order_sample_without_mutation`
- `test_point_runtime_quality_loss_and_recovery_preserve_last_sample_until_new_good_sample`

## Проверки
- Код и тесты добавлены в ветку `ci/fbd-connective-compiler`.
- Локальный pytest здесь не запускался.
- GitHub Actions run `45941638646` был `in_progress` на момент начала DEV203; результат матрицы Linux/Windows не подтверждён.
- Физический BACnet-контроллер не проверялся.

## Ограничения
- Это защита от out-of-order sample по timestamp, а не полноценный sequence-number/replay protocol.
- Нельзя объявлять качество или физическую совместимость подтверждёнными до завершения CI и аппаратной приёмки.
