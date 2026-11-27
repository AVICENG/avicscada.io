# DEV245 — Решение по KNX и добавление M-Bus в каталог

Дата: 27.11.2026
Ветка: drivers/multi-engine-c-worker-dev223

## Изменения
- KNX оставлен в текущем Python runtime path. XKNX определён как кандидат зрелой библиотеки для последующей замены самописного KNXnet/IP transport после parity и compatibility tests; xknxproject — кандидат для ETS import.
- В каталог добавлен mbus — Wired M-Bus EN 13757-2/-3, категория Building Automation, feature key driver.mbus.
- M-Bus честно помечен PLANNED: read/discovery capabilities не рекламируются, записи в поле нет.
- Wireless M-Bus выделен за пределы wired M-Bus первого этапа.
- Добавлен документ docs/drivers/MBUS_DEV245_RU.md с архитектурой, scope, безопасностью, тестовой матрицей и этапами реализации.
- Обновлены дерево драйверов и регрессионный тест каталога.

## Проверки
- Добавлены проверки каталога: идентификатор M-Bus, протокол, lifecycle, отсутствие read/discovery/write capabilities, явное разделение Wireless M-Bus.
- Локальный pytest и сборка в этой операции не запускались.
- GitHub Actions для нового HEAD должны подтвердить каталог и общую регрессию.
- Сборка libmbus, Windows/Linux Worker и hardware acceptance не выполнялись.

## Готовность
- KNX: существующая read-only Python реализация сохранена; XKNX ещё не интегрирован.
- Wired M-Bus: только каталог и проектная спецификация; рабочего драйвера нет.
- Ни один из этих пунктов не объявляется промышленно готовым.

## Следующий этап
1. Проверить CI DEV245.
2. Интегрировать XKNX через текущую границу AVIC adapter/Worker, не ломая Point Runtime; отдельно проверить Python 3.15.2.
3. Провести upstream/license/build audit libmbus, затем разработать C Worker по существующему IPC contract.
