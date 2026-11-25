# Graphics Binding Engine 1.0 — DEV98

## Назначение

DEV98 расширяет существующую модель `GraphicDocument → GraphicElement → PointBinding`. Привязка остаётся ссылкой на стабильный `Point.id` AVIC Core, а не на имя точки, сетевой адрес или текстовую подпись.

Один объект может иметь несколько привязок к одной роли, если они направлены в разные свойства графического объекта. Например, одна аналоговая точка может одновременно выводить форматированное значение в `text` и задавать цвет в `color` через Spectrum.

## Типы привязок

- `value` — базовое значение;
- `bound_label` — форматированная подпись;
- `spectrum` — цвет по непересекающимся числовым диапазонам;
- `status` — булево/состояние и разрешение индикации;
- `popup` — ссылка на контекстную карточку (контракт);
- `hyperlink` — внутренний переход AVIC;
- `historian` — диапазон истории (контракт).

Контракты `setpoint` и `action` распознаются evaluator, но возвращают `COMMAND_MANAGER_NOT_CONNECTED`. Они не выполняют запись и не дают интерактивного разрешения. Это намеренное fail-closed поведение.

## Целевые свойства

`text`, `value`, `color`, `visible`, `rotation`, `animation`, `image`, `status`, `tooltip`.

## Параметры преобразования

- `converter`: `auto`, `numeric`, `boolean`, `enum`, `string`;
- `decimals`: 0–8;
- `unit`, `prefix`, `suffix`;
- `scale`, `offset`, `min_value`, `max_value`;
- `true_text`, `false_text`, `enum_map`;
- `thresholds`: до 64 непересекающихся диапазонов `{min,max,color}`;
- `degrade_behavior`: `show_quality`, `hide`, `safe_default`.

Числовое преобразование выполняется как `value * scale + offset`, затем ограничивается min/max, после чего форматируется. Цветовой диапазон использует нижнюю включённую и верхнюю исключённую границу.

## Качество и деградация

Только `GOOD` допускает применение значения к динамическому состоянию. Для `BAD`, `UNCERTAIN`, `STALE`, `COMM_LOST`, `NOT_CONNECTED` и неизвестного качества evaluator не разрешает анимацию и интерактивное действие. `show_quality` показывает код качества; `hide` скрывает целевой элемент; `safe_default` возвращает настроенное безопасное значение.

Система не должна сохранять видимость состояния «работает» как подтверждённое, если обратная связь устарела или потеряна. Команда и фактическая обратная связь — разные источники.

## Runtime/API

`GraphicsService.evaluate_bindings(document_id)` читает значения только через `CoreApplication.point_runtime` и возвращает результат по ID привязки. HTTP endpoint: `GET /api/graphics/{document_id}/bindings/evaluate`.

В DEV98 редактор сохраняет тип, целевое свойство и настройки привязки; runtime API вычисляет преобразования. Полное применение всех свойств SVG (rotation/image/visibility/tooltip), popup и Historian chart — дальнейшая работа. На текущем этапе текстовое значение отображается в редакторе, а остальные target properties доступны через контракт evaluator.

## Ограничения

- Нет записи в полевые устройства из Graphics Binding Engine.
- Setpoint/Action не выполняются до отдельного Command Manager с серверной авторизацией, подтверждением, interlock-проверками и аудитом.
- UI API в текущем Workbench остаётся development/loopback интерфейсом; наличие каталога ролей само по себе не означает, что каждый HTTP route уже защищён. Production API должен проводить каждую операцию через `SecurityGateway` и `GraphicsSecurityPolicy`.
