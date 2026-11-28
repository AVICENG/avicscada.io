# AVIC Core — журнал сборки DEV272

Дата: 28.11.2026
Ветка: `drivers/modbus-rtu-c-worker-dev249`
Предыдущий commit: `b53b7b1fce3abe12e35ba7f530cc6b876e1b322e`

## Основание

DEV271 CI #969 / run `46156935321` завершился успешно: 22 jobs success, 0 failures. Rust Communication Engine — Windows и Ubuntu; полная Python матрица Linux/Windows Python 3.11/3.12/3.13; нативные C jobs — успешны.

Повторная ревизия выявила дополнительные окна гонки в Python Supervisor вокруг состояния Rust Worker. DEV272 усиливает синхронизацию жизненного цикла.

## Изменения

1. Введена отдельная `_lifecycle_lock`: `start`, `read` и `close` сериализуются. Команда чтения не может вклиниться между `stop` и `shutdown`.
2. Неожиданный EOF немедленно fenced: `reader_failed=True`, `started=False` устанавливаются до ожидания завершения процесса.
3. Штатный EOF после `shutdown` не считается ошибкой, если процесс действительно завершается в установленный срок. Если канал закрыт, а процесс остаётся жив, включается fail-closed terminate/kill.
4. Состояние, счётчики событий, последовательности и stderr tail читаются/обновляются под state lock.
5. Диагностика показывает `closing`, `reader_failed`, `started` и состояние процесса согласованным snapshot.
6. EOF fault-injection тест проверяет немедленный fencing и запрет последующего read. Тест штатного завершения проверяет, что clean shutdown не помечается как reader failure.

## Принцип надёжности

- Ни одна команда read не выполняется после начала закрытия Worker.
- Потеря IPC немедленно запрещает дальнейшее использование Worker.
- Устаревший процесс не должен оставаться незамеченным после EOF.
- Нормальный shutdown отделён от аварийного EOF.
- Ошибка/тайм-аут не превращается в «успешный» статус.

## Статус

DEV272 отправлен на Windows/Linux CI. Сам DEV272 не считается проверенным до нового полного прогона. PR не объединять автоматически.

## Следующие проверки

- Одновременные read/close/start fault-injection с барьерами и повторениями.
- Reader EOF одновременно с start ACK.
- Timeout и terminate/kill на Windows/Linux.
- Rust Modbus TCP: delayed response, truncated MBAP, wrong Unit ID/byte count, reconnect.
- Soak 24h и нагрузка 1 000 устройств / 100 000 точек — обязательные отдельные gates.
