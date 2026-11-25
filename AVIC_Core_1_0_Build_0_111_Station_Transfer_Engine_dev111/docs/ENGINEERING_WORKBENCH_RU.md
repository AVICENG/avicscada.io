# Unified Engineering Workbench — DEV47

## Общая оболочка
Основная оболочка находится в `avic_core/ui/static/index.html`. Она содержит левую навигацию, центральную рабочую область, вкладки и инспектор. Scheduler в DEV47 открывается в центральной области через штатную навигацию и не использует отдельный HTML-документ.

## Интегрированные рабочие пространства
- Engineering Tree: Project → Station → Physical Network → Protocol Channel → Device → Point.
- Network onboarding: BACnet/IP discovery и отдельные read-only операции.
- Web Pages: отдельный редактор страниц `/pages`.
- Graphics: отдельный редактор `/graphics`, который DEV46 встраивал через iframe в Web Pages Editor.
- Scheduler: центральное рабочее место Workbench в DEV47.

## Важная архитектурная оговорка
Единая оболочка ещё не означает единую модель всех документов. DEV47 устраняет изоляцию только для Scheduler UI. Web Pages и Graphics пока сохраняют отдельные модели и отдельные редакторы; iframe-интеграция DEV46 не считается окончательным решением.

## Дальнейшая цель
Перевести все редакторы на общий document host: единые вкладки, unsaved-state, autosave/recovery, undo/redo, shared selection, property inspector, command palette, object bindings и единые серверные права.

## DEV51 — Locator, View Changer и Palette

В DEV51 левую панель можно переключать между Навигатором и Палитрой. Locator Bar принимает название раздела либо видимое имя/ID объекта из текущего дерева. Кнопки «назад/вперёд» и Alt+Left/Alt+Right перемещают по истории открытых страниц. View Changer направляет к доступным представлениям: свойства, список точек, Wiresheet/FBD, PX/мнемосхема, Scheduler, Alarm Console и History/Trend. Правый клик по разделу дерева открывает команды навигации; правый клик по инженерному объекту — объектное меню.

Палитра DEV51 пока является каталогом-навигатором, а не полноценным drag-and-drop Palette IQVISION. Фактическая вставка блоков/символов и bindings будет приниматься только после реализации редактора и сохранения модели.
