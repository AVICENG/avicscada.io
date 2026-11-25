# AVIC Core 1.0 DEV99 — журнал сборки и проверок

Основа: переданный AVIC Core DEV98 + переданный AVIC Repository Manager DEV23.

## Реализовано
- В существующий Engineering Tree добавлена единственная ветвь `Репозиторий` под каждой Station.
- Ветка имеет стабильный id `avic.repository`, не владеет физическими объектами Core.
- Добавлена точка входа `/repository` в общий Workbench, повторно использующая существующий Pages workspace.
- Core WebPagesService, GraphicsService, PointRuntime и SecurityGateway остаются авторитетными сервисами.
- Добавлены тесты интеграционного слоя и документация сопоставления.

## Проверки
- Новые тесты + shared navigation + graphics binding regression: **15 passed**.
- Compileall: успешно.
- Wheel build: успешно (`avic_core-1.0.0.dev99-py3-none-any.whl`).
- Полный pytest прогон прерван автоматическим ограничением времени среды примерно через 60 секунд. Полный результат не подтверждён.
- Windows/Python 3.15.2 и браузерный E2E не выполнялись.

## Важные ограничения
- Это первый слой объединения дерева и навигации, а не полная миграция редактора DEV23.
- WSGI-сервер и AuthStore DEV23 намеренно не перенесены: они создали бы второе хранилище и вторую модель аутентификации.
- `/repository` пока использует существующий Pages workspace; отдельный Repository UI ещё предстоит портировать на Core WebPagesService.
- В Core Workbench остаётся loopback guard для локальных мутаций; полноценное подключение RBAC/SecurityGateway ко всем API-маршрутам — обязательная следующая задача.
