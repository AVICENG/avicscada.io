# Журнал DEV154 — согласование каталога KNX с реализованным runtime

## Изменения
- Обновлён общий regression test каталога: KNXnet/IP теперь включён в перечень поддерживаемых read-only transports.
- Добавлен отдельный тест, подтверждающий READ_ONLY_TRANSPORT и отсутствие discovery/write capability в каталоге.
- Это не расширяет возможности KNX за пределы passive group monitor из DEV152.

## Проверки
- Проверка каталога синхронизирована с runtime factory и Point Runtime adapter.
- Полный CI DEV154 остаётся обязательным; результаты предыдущих отменённых запусков не засчитываются.
