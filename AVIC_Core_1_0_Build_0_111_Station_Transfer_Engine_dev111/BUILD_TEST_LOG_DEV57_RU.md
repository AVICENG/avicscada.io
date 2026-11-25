# Журнал проверок DEV57

Дата: 2026-11-19

| Проверка | Результат |
|---|---:|
| `python -m compileall -q avic_core tests` | PASS |
| Driver Manager DEV57 + Driver Catalog DEV26 + Graphics DEV35 | 16 passed |
| Полный pytest | Не запускался в этом цикле; full-suite pass не заявляется |
| Windows acceptance | Не выполнен |
| Browser interactive acceptance | Не выполнена |
| BACnet/Modbus физическое оборудование | Не проверено |
| TONN/TONN8 | Не реализовано/не проверено |
| Linux Controller Agent | Архитектурный документ; реализации нет |

Тесты DEV57 проверяют каталог, создание и сохранение экземпляра, запрет неизвестного драйвера, запрет секретов в обычной конфигурации, запрет создания включённого экземпляра, HTTP-маршруты и Origin guard.
