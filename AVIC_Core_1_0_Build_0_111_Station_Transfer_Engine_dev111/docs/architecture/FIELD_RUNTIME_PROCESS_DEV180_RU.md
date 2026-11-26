# DEV180 — локальный heartbeat Field Runtime

DEV180 устраняет зависимость heartbeat от команд Supervisor. Агент использует короткий socket receive timeout и обновляет внутренний heartbeat даже когда Supervisor не посылает запросов. При разрыве TCP агент продолжает цикл heartbeat и переподключается.

Это heartbeat процесса, а не watchdog FBD-циклов и не подтверждение работоспособности оборудования. FBD engine по-прежнему не подключён.