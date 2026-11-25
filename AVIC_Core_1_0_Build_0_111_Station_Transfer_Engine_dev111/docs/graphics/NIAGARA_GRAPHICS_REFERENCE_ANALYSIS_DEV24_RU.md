# Анализ пользовательских Niagara Graphics JAR — DEV24

## Проверенные исходные архивы

- `kitPxN4svg-wb.jar` — модуль `kitPxN4svg`, Tridium, vendorVersion 4.0.22.16.3; 973 SVG.
- `kitPxGraphics-wb.jar` — 1 073 PNG/GIF-графических ресурса.
- `kitPxHvac-wb.jar` — 278 GIF HVAC.
- `kitPxBuilding-wb.jar` — 618 GIF building/equipment.
- `kitPx-wb.jar` — `module.palette` с компонентами привязок и управляющими виджетами.
- `kitPx-ux.jar` — JS-ресурсы SetPoint Editor.

## Что подтверждает module.palette

### 1. Динамическая смена изображения по Boolean

В `kitPxN4svg-wb.jar/module.palette` у Boiler/Chiller используется `ui:ValueBinding` с преобразователем `IBooleanToSimple`. Для true и false назначаются разные SVG-файлы `*_On.svg` и `*_Off.svg`. Это прямой пример, почему AVIC нужен не только текстовый binding, но и привязка к свойству `image`/состоянию символа.

### 2. Числовые диапазоны

Для cooling coils и 2-/3-way coil symbols используется `INumericToSimple` и `NumericToSimpleMap`: разные SVG выбираются по числовым диапазонам, например `-inf:20`, `20:40`, `40:60`, `60:80`, `80:+inf`, плюс default. В AVIC это переносится в типизированный Spectrum/Range binding с проверкой пересечений, явными границами и цветом/состоянием.

### 3. Отдельные виджеты, а не один универсальный binding

`kitPx-wb.jar/module.palette` показывает BoundLabel, ActionButton, HyperlinkButton, Popup/Action binding, AnalogMeter, Bargraph, SetPointSlider, SetPointToggleButton, SetPointCheckBox, Increment/Decrement SetPoint Button, Field Editor, MouseOver Binding и ButtonGroup. Это подтверждает разделение read-only отображения, навигации, popup и пользовательских действий.

### 4. Права и разделение операций

Наличие отдельных SetPoint/Action компонентов не означает, что графический объект должен сам выполнять полевую запись. В AVIC эти типы должны проходить отдельный Command Manager, RBAC, scope, interlock, подтверждение и аудит. DEV98 пока намеренно оставляет Setpoint/Action неисполняемыми.

## Что заимствуем в AVIC

- Boolean true/false image-state mapping.
- Numeric range-to-state/image mapping.
- Bound label с конвертерами.
- Отдельные типы popup, hyperlink, action и setpoint.
- Analog meter / bargraph как будущие reusable widgets.
- Явные состояния качества и degrade behavior, которых нельзя подменять последним удачным значением без маркировки.
- Переиспользуемые symbol palette и шаблоны оборудования.

## Что не копируем буквально

- Niagara ORD: в AVIC используем стабильный Core Point ID и контекст станции/оборудования; отображаемое имя не является ключом.
- Не делаем binding-объект источником полномочий: пользовательские действия авторизуются отдельно.
- Не исполняем команды непосредственно из SVG/страницы.
- Не включаем проприетарные Tridium SVG/GIF/PNG в коммерческий AVIC build без подтверждения лицензии.

## Библиотека ресурсов

Полный отдельный пакет `AVIC_Graphics_Reference_Library_DEV24.zip` содержит 3 008 ресурсов: 886 SVG, прошедших нормализацию и AVIC sanitizer; 87 SVG помещены в карантин; остальные PNG/GIF доступны для справочного просмотра. Дополнительно включены 66 нативных SVG Core dev97. Пакет не подключается к Core Runtime.
