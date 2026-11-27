from datetime import datetime, timedelta, timezone
import time

import pytest

from avic_core.domain.models import Device, Point, PointDirection, PointQuality
from avic_core.drivers.manager import DriverInstance
from avic_core.ui import create_ui_app
from avic_core.runtime.point_scheduler import PointRuntimeScheduler


DRIVER_ID = "00000000-0000-4000-8000-000000000210"
T0 = datetime(2026, 11, 27, 8, 0, tzinfo=timezone.utc)


def _setup(tmp_path, *, data_type="binary-input", direction=PointDirection.INPUT):
    app = create_ui_app(data_dir=str(tmp_path))
    project = app.state.project_station.create_project("DEV210 Project")
    station = app.state.project_station.create_station(project["id"], "DEV210 Station")
    app.state.core.repository.save(DriverInstance(
        name="DEV210 Modbus", station_id=station["id"], driver_id="modbus-tcp",
        protocol="Modbus TCP", id=DRIVER_ID,
    ))
    device = Device(
        name="Binary test controller", station_id=station["id"],
        protocol="modbus/tcp", address="127.0.0.1:502",
        driver_instance_id=DRIVER_ID,
    )
    app.state.core.repository.save(device)
    point = Point(
        name="Fan proof", device_id=device.id, data_type=data_type,
        direction=direction, value=None, quality=PointQuality.UNCERTAIN,
        native_identity="modbus:discrete-input:0",
    )
    app.state.core.repository.save(point)
    return app, point


def test_binary_debounce_filters_short_pulse_and_flushes_without_next_sample(tmp_path):
    app, point = _setup(tmp_path)
    runtime = app.state.core.point_runtime
    seen = []
    runtime.subscribe(point.id, seen.append)
    runtime.configure_debounce(point.id, on_ms=100, off_ms=250)

    initial = runtime.publish(
        point.id, False, timestamp=T0, source_driver_id=DRIVER_ID
    )
    assert initial.value is False
    assert initial.quality == "GOOD"
    assert len(seen) == 1

    pending = runtime.publish(
        point.id, True, timestamp=T0 + timedelta(milliseconds=10),
        source_driver_id=DRIVER_ID,
    )
    assert pending.value is False
    assert runtime.read(point.id).value is False
    assert len(seen) == 1

    assert runtime.flush_debounce(now=T0 + timedelta(milliseconds=109)) == ()
    committed = runtime.flush_debounce(now=T0 + timedelta(milliseconds=110))
    assert len(committed) == 1
    assert committed[0].value is True
    assert committed[0].quality == "GOOD"
    assert runtime.read(point.id).value is True
    assert len(seen) == 2
    app.state.core.close()


def test_binary_debounce_cancels_bounce_and_keeps_last_stable_value(tmp_path):
    app, point = _setup(tmp_path)
    runtime = app.state.core.point_runtime
    runtime.configure_debounce(point.id, on_ms=100, off_ms=100)
    runtime.publish(point.id, False, timestamp=T0, source_driver_id=DRIVER_ID)

    runtime.publish(
        point.id, True, timestamp=T0 + timedelta(milliseconds=10),
        source_driver_id=DRIVER_ID,
    )
    bounced = runtime.publish(
        point.id, False, timestamp=T0 + timedelta(milliseconds=40),
        source_driver_id=DRIVER_ID,
    )
    assert bounced.value is False
    assert runtime.flush_debounce(now=T0 + timedelta(seconds=1)) == ()
    assert runtime.read(point.id).value is False
    app.state.core.close()


def test_quality_loss_cancels_pending_debounce_and_preserves_last_sample(tmp_path):
    app, point = _setup(tmp_path)
    runtime = app.state.core.point_runtime
    runtime.configure_debounce(point.id, on_ms=100, off_ms=100)
    first = runtime.publish(
        point.id, False, timestamp=T0, source_driver_id=DRIVER_ID
    )
    runtime.publish(
        point.id, True, timestamp=T0 + timedelta(milliseconds=10),
        source_driver_id=DRIVER_ID,
    )

    lost = runtime.mark_quality(
        point.id, PointQuality.BAD_COMMUNICATION, source_driver_id=DRIVER_ID
    )
    assert lost.value == first.value is False
    assert lost.quality == "BAD_COMMUNICATION"
    assert runtime.flush_debounce(now=T0 + timedelta(seconds=1)) == ()
    assert runtime.read(point.id).value is False
    app.state.core.close()


def test_debounce_configuration_is_persisted_and_rejects_analog_or_output_points(tmp_path):
    app, point = _setup(tmp_path)
    runtime = app.state.core.point_runtime
    runtime.configure_debounce(point.id, on_ms=35, off_ms=80)
    stored, _ = app.state.core.repository.get(point.id, Point)
    assert stored.debounce_on_ms == 35
    assert stored.debounce_off_ms == 80

    with pytest.raises(ValueError, match="non-negative"):
        runtime.configure_debounce(point.id, on_ms=-1)
    app.state.core.close()

    app2 = create_ui_app(data_dir=str(tmp_path))
    stored_again, _ = app2.state.core.repository.get(point.id, Point)
    assert stored_again.debounce_on_ms == 35
    assert stored_again.debounce_off_ms == 80
    app2.state.core.close()


def test_debounce_is_rejected_for_analog_and_output_points(tmp_path):
    app, point = _setup(tmp_path, data_type="analog-input")
    with pytest.raises(ValueError, match="бинарной"):
        app.state.core.point_runtime.configure_debounce(point.id, on_ms=10)

    project = app.state.project_station.create_project("Output Project")
    station = app.state.project_station.create_station(project["id"], "Output Station")
    device = Device(
        name="Output controller", station_id=station["id"], protocol="modbus/tcp",
        address="127.0.0.2:502", driver_instance_id=DRIVER_ID,
    )
    app.state.core.repository.save(device)
    output = Point(
        name="Fan command", device_id=device.id, data_type="binary-output",
        direction=PointDirection.OUTPUT,
    )
    app.state.core.repository.save(output)
    with pytest.raises(ValueError, match="OUTPUT"):
        app.state.core.point_runtime.configure_debounce(output.id, on_ms=10)
    app.state.core.close()



def test_wrong_driver_cannot_cancel_another_drivers_pending_debounce(tmp_path):
    app, point = _setup(tmp_path)
    runtime = app.state.core.point_runtime
    runtime.configure_debounce(point.id, on_ms=100, off_ms=100)
    runtime.publish(point.id, False, timestamp=T0, source_driver_id=DRIVER_ID)
    runtime.publish(
        point.id, True, timestamp=T0 + timedelta(milliseconds=10),
        source_driver_id=DRIVER_ID,
    )

    with pytest.raises(ValueError, match="не совпадает"):
        runtime.mark_quality(
            point.id, PointQuality.BAD_COMMUNICATION,
            source_driver_id="00000000-0000-4000-8000-000000000999",
        )

    committed = runtime.flush_debounce(now=T0 + timedelta(milliseconds=110))
    assert len(committed) == 1
    assert committed[0].value is True
    app.state.core.close()



def test_explicit_point_runtime_scheduler_commits_due_transition(tmp_path):
    app, point = _setup(tmp_path)
    runtime = app.state.core.point_runtime
    runtime.configure_debounce(point.id, on_ms=60, off_ms=60)
    runtime.publish(point.id, False, source_driver_id=DRIVER_ID)
    runtime.publish(point.id, True, source_driver_id=DRIVER_ID)

    scheduler = PointRuntimeScheduler(runtime, interval_seconds=0.01)
    scheduler.start()
    deadline = time.monotonic() + 1.0
    try:
        while time.monotonic() < deadline and runtime.read(point.id).value is not True:
            time.sleep(0.01)
        assert runtime.read(point.id).value is True
        assert scheduler.diagnostics()["tick_count"] > 0
        assert scheduler.diagnostics()["failure_count"] == 0
    finally:
        scheduler.stop()
        app.state.core.close()


def test_driver_manager_owns_shared_scheduler_lifecycle(tmp_path):
    app, _ = _setup(tmp_path)

    class FakeAdapter:
        def poll_once(self):
            return {"results": []}

    app.state.core.driver_manager.register_adapter_factory(
        "modbus-tcp", lambda core, instance: FakeAdapter()
    )
    started = app.state.core.driver_manager.start_instance(
        DRIVER_ID, poll_interval_seconds=0.1
    )
    assert started["point_runtime_scheduler"]["state"] == "RUNNING"
    stopped = app.state.core.driver_manager.stop_instance(DRIVER_ID)
    assert stopped["point_runtime_scheduler"]["state"] == "STOPPED"
    app.state.core.close()
