# AVIC Core 1.0 — журнал сборки DEV202

## Область
Point Runtime / ownership boundary для публикации значений и качества от протокольных адаптеров.

## Реализовано
- Ужесточена проверка принадлежности точки драйверу: при заданном `source_driver_id` он должен точно совпасть с `Device.driver_instance_id`.
- Отсутствующий владелец Device больше не трактуется как wildcard.
- Одинаковая проверка применяется к `publish()` и `mark_quality()`.
- Внутренний Core путь без adapter identity остаётся допустимым только при явном `source_driver_id=None`.
- Добавлен регрессионный тест: unowned/legacy Device отвергает sample и quality от драйвера; Core publication без driver identity остаётся рабочей.

## Изменённые файлы
- `avic_core/points/runtime.py`
- `tests/test_driver_binding_dev141.py`
- `docs/AVIC_CLOSED_LOOP_PRODUCT_READINESS_RU.md`

## Проверки
- Локальный pytest в этой среде не запускался; изменения внесены через GitHub.
- CI DEV202: ожидает запуска после глобального последовательного workflow.
- CI DEV201 #532: на момент начала DEV202 находился в pending; новые коммиты могли заменить ожидающий run согласно concurrency policy.
- Физический BACnet acceptance: не выполнялся.

## Ограничения и статус
- Вызов Core publication с `source_driver_id=None` остаётся доверенным внутренним интерфейсом; он не предназначен для внешнего протокольного адаптера.
- Это исправление закрывает подмену владельца точки, но не заменяет общую проверку доверия/подписи сторонних драйверных пакетов.
- DEV202 реализован, но не считать проверенным до зелёного CI Linux/Windows.
