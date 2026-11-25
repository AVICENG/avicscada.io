# Журнал сборки и испытаний DEV81

## Сборка
- База: AVIC Core 1.0 DEV80.
- Версия пакета: 1.0.0.dev81.
- Изменения исходников: `avic_core/ui/static/logic.html`, `avic_core/logic_fbd_studio.py`, `avic_core/ui/app.py`.
- Новые тесты: `tests/test_fbd_editing_dev81.py`; расширен `tests/test_fbd_studio_persistence_dev77.py`.

## Проверки
- `python -m compileall -q avic_core` — OK.
- `node --check` для всех 3 inline JavaScript блоков `logic.html` — OK.
- Целевые pytest: **19 passed** за 4.47 s.
- ZIP integrity — будет записан после упаковки.
- Wheel: `avic_core-1.0.0.dev81-py3-none-any.whl`, SHA256 `5959ee01599291adaf0111dcb1a71596510221e3807909fceccdce6fa5461a70`.

## Что не проверено
- Полный pytest всего репозитория не запускался.
- Реальный браузерный Windows acceptance (мышь, hit-testing SVG, перетаскивание, диалоги) не выполнен в этой среде.
- Печать через Windows print preview не проверена.
- Следовательно, не заявляется полная визуальная приёмка DEV81.

## Ограничения
- FBD Studio documents остаются authoring-only; компиляция графа в исполняемый Core Logic ещё не реализована.
- Требуется ручная приёмка на Windows: провести линию, выбрать именно её, удалить клавишей и контекстным меню; проверить перенос блока за тело/текст/порт; создать, переместить, изменить и удалить заметку; создать повторные имена проектов/страниц и убедиться в отказе; удалить проект из дерева.
