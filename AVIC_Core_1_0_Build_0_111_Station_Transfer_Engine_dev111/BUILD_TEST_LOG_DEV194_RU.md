# AVIC Core — журнал сборки DEV194

Дата: 26.11.2026

## Изменения
- В Core TIME добавлен числовой выход UTC_OFFSET (смещение локального station timezone относительно UTC в часах).
- UI FBD TIME catalog синхронизирован с Core: 22 именованных выхода.
- FBD Studio local simulation теперь получает station time/timezone из Core API и вычисляет time/calendar outputs в часовом поясе станции, а не в timezone браузера.
- При недоступности Core time service симуляция сообщает TIME_NOT_AVAILABLE, не подменяя время локальным временем ПК.
- Добавлен тест Europe/Moscow UTC+3 на фиксированном UTC instant.
- Добавлена проверка контракта UI simulation station-time.
- Версия пакета/runtime metadata обновлена до 1.0.0.dev194.

## Проверки
- Тесты добавлены, DEV194 ещё не запускался.
- GitHub Actions оставлен в ручном opt-in режиме; не запускать compute jobs без проверки Billing и согласия.
- Статус: НЕ ПОДТВЕРЖДЁН.

## Ограничения
- Полная семантика Trend Time Master, его конфигурационные входы DST/Change By и синхронизация устройств остаются в Time Manager/отдельном scope; DEV194 добавляет только отсутствовавший UTC_OFFSET и согласование локальной симуляции со станцией.
- FBD Trend parity gaps перечислены в FBD_TREND_SET_PARITY_GAP_AUDIT_DEV193_RU.md.
