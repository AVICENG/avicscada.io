# DEV99 — объединение Repository Manager DEV23 с Core dev98

## Что объединено в этой сборке

DEV23 изучен из переданного архива. Его назначение сопоставлено с уже существующими сервисами Core dev98.

- Repository branch добавлен в существующее инженерное дерево как `repository` у каждого Station.
- Ветвь имеет стабильный id `avic.repository`, ссылается на существующий Station и объявляет `owns_core_objects=false`.
- Добавлена точка входа `/repository` в общий Workbench; она использует общий shell и существующий `pages.html`.
- Существующие Core `WebPagesService`, `GraphicsService`, `PointRuntime`, `SecurityGateway`, `GraphicsSecurityPolicy` и `EngineeringTreeService` остаются владельцами данных и операций.
- Добавлены регрессионные тесты: единый Workbench, ветвь в дереве, отсутствие второго владельца Core-объектов.

## Почему не перенесён сервер DEV23 целиком

DEV23 — отдельное WSGI-приложение с собственным `RepositoryService`, хранилищем, `AuthStore` и собственными API. Его прямое встраивание создало бы вторую систему хранения и аутентификации рядом с Core, что нарушает требование единого Core и единых прав. Поэтому его сервер и отдельную модель пользователей не подключали.

Функции DEV23 сопоставляются с Core так:

| DEV23 | Основной владелец после объединения |
|---|---|
| Pages / assets / styles / scripts | Core `WebPagesService` и Core repository |
| Graphics objects / bindings | Core `GraphicsService` и `PointBinding` |
| Point values / quality | Core `PointRuntime` |
| Alarm/event/history | Core alarm/event/historian services |
| Station access / RBAC | Core `SecurityGateway` + `GraphicsSecurityPolicy` |
| Repository tree contribution | Core `EngineeringTreeService` |

## Ограничения DEV99

- Это первый интеграционный слой дерева и навигации, а не полная миграция всех экранов DEV23.
- `/repository` пока открывает общий Pages workspace; отдельный полнофункциональный Repository workspace с переносом функций редактора DEV23 ещё требуется.
- В текущем Core Workbench локальные мутации по-прежнему ограничены loopback-проверкой в `require_local_operator`; полная сессионная RBAC-проверка каждого API-маршрута остаётся обязательной следующей работой.
- Не заявляется интеграция реального Core Adapter из DEV23: его контрактные адаптеры заменены прямым использованием Core-сервисов там, где они уже существуют.
- Windows/Python 3.15.2 приёмка не проводилась.

## Новые проверки

`tests/test_repository_dev23_core_merge_dev99.py` проверяет общий Workbench route и ветвь Repository под существующей станцией.
