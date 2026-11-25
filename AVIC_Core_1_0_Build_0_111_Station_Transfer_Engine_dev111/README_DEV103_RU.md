# AVIC Core DEV103 — FBD Virtual Points + Tree + Graphics

DEV103 соединяет Core FBD Runtime с общим Point Runtime: опубликованные выходы FBD становятся виртуальными read-only точками AVIC с постоянными ID, значениями и качеством. Точки отображаются в инженерном дереве и доступны редактору мнемосхем для привязки через drag-and-drop.

**Важно:** DEV103 позволяет проверять расчёт FBD и обновление индикации, но не посылает команды в BACnet/Modbus. Операторская публикация мнемосхемы и Command Manager для физического управления остаются следующими этапами.

См. `docs/BUILD_103_FBD_VIRTUAL_POINTS_TREE_GRAPHICS_RU.md` и `BUILD_TEST_LOG_DEV103_RU.md`.
