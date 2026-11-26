# AVIC Core DEV182 — CI workload and trigger correction

Версия: 1.0.0.dev182  
Базовый commit: ea3b5b754041049699e95942324f5601e70d6b1a

## Диагностика CI
- Путь пакета и pyproject.toml в workflow корректны.
- Найден старый Windows-дефект DEV145: SQLite context manager не закрывал соединение перед os.replace, из-за чего Windows блокировала файл .config-locks.sqlite3 (WinError 5/32).
- Исправление уже находится в DEV156 (commit 3aab285a7ebab14928071499ce7374b8e2ff9e88): явный db.close() в finally.
- Последний запуск DEV181 имеет runner_id=0, пустой runner_name и steps=[] на всех четырёх заданиях. Повторный запуск дал тот же результат. Это отказ до старта runner, а не ошибка команды pytest или пути.
- Ранее на DEV154 runner назначался; Linux прошёл, Windows упал только на указанной SQLite-блокировке.
- Ветку dev113 запускали одновременно по push и pull_request. Каждый commit создавал два одинаковых четырёхзаданных workflow запуска. DEV182 убирает дублирующий push trigger для dev113; изменения этой ветки продолжают проверяться PR #2 по pull_request.

## Изменения
- CI запускается на push стабильной dev112, на PR в main/dev112 и вручную через workflow_dispatch.
- Для PR concurrency group привязан к номеру PR.
- Полная матрица Python 3.11/3.12/3.13 Linux и Python 3.13 Windows сохранена.
- Версия пакета обновлена до 1.0.0.dev182.

## Проверки
- Workflow YAML и пути проверены по содержимому репозитория.
- Полный CI DEV182 ещё не подтверждён.
- GitHub Actions jobs на DEV181 не получили runner (runner_id=0); причину на уровне аккаунта/платформы нельзя достоверно установить из доступных API-данных.

## Следующее действие
Если свежий DEV182 PR run снова завершится с runner_id=0 и без шагов, проверить GitHub Settings → Billing and licensing → Actions usage/budget и Settings → Actions → General/Runner groups. При чистом бюджете это обращение в GitHub Support с run ID и UTC timestamp.
