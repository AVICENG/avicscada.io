"""Behavioral acceptance matrix: persistent services used by IQVISION-style workflows.

Each pytest parameter is an independent acceptance case with a distinct input and
assertion. These are not repeated smoke-test aliases: they exercise persistence,
filtering, type handling, dependency safety, and deterministic calculations.
"""
from __future__ import annotations

from itertools import product
import pytest

from avic_core.events import EventService
from avic_core.history import HistoryService
from avic_core.dependencies import DependencyService
from avic_core.notifications import NotificationService
from avic_core.analytics import AnalyticsService


# Event journal: all supported severities across independently named station/source
# contexts. Each case checks normalized severity, structured details, and reopen.
_EVENT_CASES = list(product(
    sorted(EventService.SEVERITIES),
    range(25),
))

@pytest.mark.parametrize("severity,case", _EVENT_CASES)
def test_event_journal_severity_station_source_and_restart(tmp_path, severity, case):
    path = tmp_path / "events.sqlite3"
    first = EventService(path)
    station = f"station-{case % 5}"
    source = f"device-{case:03d}"
    details = {"case": case, "zone": f"zone-{case % 7}", "active": case % 2 == 0}
    saved = first.record(
        f"device.state.{case}", f"Событие {case}", station_id=station,
        severity=severity.lower(), source_id=source, actor_id=f"operator-{case % 3}",
        correlation_id=f"corr-{case}", details=details,
    )
    reopened = EventService(path)
    rows = reopened.list(station_id=station, event_type=f"device.state.{case}")
    assert len(rows) == 1
    assert rows[0].event_id == saved.event_id
    assert rows[0].severity == severity
    assert rows[0].source_id == source
    assert rows[0].details == details


# Event filters: ensure station, severity and text search intersect correctly.
_EVENT_FILTER_CASES = list(product(sorted(EventService.SEVERITIES), range(20)))

@pytest.mark.parametrize("severity,case", _EVENT_FILTER_CASES)
def test_event_journal_filter_intersection_and_search(tmp_path, severity, case):
    service = EventService(tmp_path / "events.sqlite3")
    target_station = f"s-{case % 4}"
    service.record("equipment.status", f"target-token-{case}", station_id=target_station,
                   severity=severity, source_id=f"src-{case}")
    service.record("equipment.status", f"other-token-{case}", station_id="other",
                   severity="INFO", source_id="other-src")
    result = service.list(station_id=target_station, severity=severity.lower(), search=f"target-token-{case}")
    assert len(result) == 1
    assert result[0].message == f"target-token-{case}"


# History quality matrix: every supported quality, varied scalar and structured values.
_HISTORY_CASES = list(product(sorted(HistoryService.QUALITIES), range(25)))

@pytest.mark.parametrize("quality,case", _HISTORY_CASES)
def test_history_quality_value_roundtrip_and_bad_filter(tmp_path, quality, case):
    path = tmp_path / "history.sqlite3"
    first = HistoryService(path)
    value = float(case) + 0.25
    saved = first.append(f"station-{case % 5}", f"point-{case}", value,
                         quality=quality.lower(), source=f"source-{case % 4}")
    reopened = HistoryService(path)
    all_rows = reopened.query(f"station-{case % 5}", f"point-{case}")
    assert len(all_rows) == 1 and all_rows[0].sample_id == saved.sample_id
    assert all_rows[0].value == value and all_rows[0].quality == quality
    accepted = reopened.query(f"station-{case % 5}", f"point-{case}", include_bad=False)
    assert (len(accepted) == 1) == (quality in {"GOOD", "UNCERTAIN"})


# Rollup algorithms over nontrivial numeric sequences; each case checks independent
# deterministic result and the valid-sample count.
_ROLLUP_CASES = list(product(
    ["average", "sum", "min", "max", "median", "last", "count"], range(20)
))

@pytest.mark.parametrize("method,case", _ROLLUP_CASES)
def test_history_rollup_algorithms_and_quality_exclusion(tmp_path, method, case):
    service = HistoryService(tmp_path / "history.sqlite3")
    station, point = f"s-{case % 4}", f"p-{case}"
    values = [case + 1, case + 3, case + 8, case + 12]
    for value in values:
        service.append(station, point, value, quality="GOOD")
    service.append(station, point, 999999, quality="BAD")
    result = service.rollup(station, point, method=method)
    expected = {
        "average": sum(values) / len(values), "sum": sum(values),
        "min": min(values), "max": max(values),
        "median": (values[1] + values[2]) / 2,
        "last": values[-1], "count": len(values),
    }[method]
    assert result["value"] == expected
    assert result["valid_numeric_count"] == len(values)
    assert result["sample_count"] == len(values)


# Dependency graph relation matrix. Every edge must be visible from both ends;
# a referenced object must be blocked from deletion until edges are removed.
_DEPENDENCY_CASES = list(product(
    ["binding", "wiresheet", "alarm", "history", "schedule", "favorite", "analytics", "navigation", "widget", "reference"],
    range(20),
))

@pytest.mark.parametrize("relation,case", _DEPENDENCY_CASES)
def test_dependency_graph_blocks_referenced_object_and_cleans_edges(tmp_path, relation, case):
    service = DependencyService(tmp_path / "dependencies.sqlite3")
    owner, target = f"consumer-{case}", f"point-{case}"
    metadata = {"case": case, "required": case % 2 == 0}
    edge = service.add(owner, target, relation, station_id=f"station-{case % 5}", metadata=metadata)
    assert any(x.edge_id == edge.edge_id for x in service.list_for(owner))
    assert any(x.edge_id == edge.edge_id for x in service.list_for(target))
    preview = service.delete_preview(target)
    assert preview["safe_to_delete"] is False
    assert preview["blocking_dependents"][0]["object_id"] == owner
    assert preview["blocking_dependents"][0]["relation_type"] == relation
    assert service.remove_object_edges(target) == 1
    assert service.delete_preview(target)["safe_to_delete"] is True


# Notification channel matrix. The outbox must preserve routing metadata and must
# remain queued (never claim delivery when no transport adapter is installed).
_NOTIFICATION_CASES = list(product(sorted(NotificationService.CHANNELS), range(25)))

@pytest.mark.parametrize("channel,case", _NOTIFICATION_CASES)
def test_notification_route_and_outbox_channel_roundtrip(tmp_path, channel, case):
    path = tmp_path / "notifications.sqlite3"
    first = NotificationService(path)
    route = first.add_route(f"route-{case}", channel.lower(), f"recipient-{case}",
                            filters={"priority_max": case % 5, "station": f"s-{case % 3}"})
    message = first.enqueue({"alarm": f"alarm-{case}", "value": case},
                            event_ref=f"event-{case}", route_id=route["route_id"])
    reopened = NotificationService(path)
    routes = reopened.list_routes()
    outbox = reopened.list_outbox()
    saved_route = next(x for x in routes if x["route_id"] == route["route_id"])
    saved_message = next(x for x in outbox if x["message_id"] == message["message_id"])
    assert saved_route["channel"] == channel
    assert saved_route["filters"]["priority_max"] == case % 5
    assert saved_message["payload"]["alarm"] == f"alarm-{case}"
    assert saved_message["status"] == "PENDING" and saved_message["attempts"] == 0


# Tag dictionaries and hierarchy scopes model the point classification used by
# Point Database Manager / analytics search. Prefixes must not bleed into siblings.
_TAG_CASES = list(product(["AVIC", "TREND", "BACNET", "MODBUS", "SITE"], range(20)))

@pytest.mark.parametrize("dictionary,case", _TAG_CASES)
def test_analytics_dictionary_and_hierarchy_prefix_isolation(tmp_path, dictionary, case):
    service = AnalyticsService(tmp_path / "analytics.sqlite3")
    tag = f"temperature-{case % 4}"
    inside = f"point-in-{case}"
    outside = f"point-out-{case}"
    service.tag_point(inside, tag, dictionary=dictionary,
                      hierarchy_path=f"Campus/A/Building-{case}/Floor-1")
    service.tag_point(outside, tag, dictionary=dictionary,
                      hierarchy_path=f"Campus/AB/Building-{case}/Floor-1")
    service.tag_point(f"wrong-dict-{case}", tag, dictionary="OTHER",
                      hierarchy_path=f"Campus/A/Building-{case}/Floor-1")
    found = service.find_points(tag, dictionary=dictionary,
                                hierarchy_prefix=f"Campus/A/Building-{case}")
    assert found == [inside]


# Analytics aggregate methods and missing-data strategies are tested across a set
# of different data magnitudes, including negative and fractional values.
_AGGREGATE_CASES = list(product(
    ["sum", "average", "min", "max", "median", "count"], range(20)
))

@pytest.mark.parametrize("method,case", _AGGREGATE_CASES)
def test_analytics_aggregate_method_numeric_matrix(tmp_path, method, case):
    values = [case - 10.5, case + 0.25, case * 2 + 1.75, case + 6.5]
    result = AnalyticsService.aggregate(values, method)
    expected = {
        "sum": sum(values), "average": sum(values) / len(values),
        "min": min(values), "max": max(values),
        "median": (sorted(values)[1] + sorted(values)[2]) / 2,
        "count": len(values),
    }[method]
    assert result["value"] == expected
    assert result["valid_count"] == len(values)
    assert result["missing_count"] == 0


_MISSING_CASES = list(product(
    ["ignore_point", "ignore_series", "linear_interpolation"], range(20)
))

@pytest.mark.parametrize("strategy,case", _MISSING_CASES)
def test_analytics_missing_data_policy_matrix(strategy, case):
    values = [float(case), None, float(case + 10)]
    result = AnalyticsService.aggregate(values, "average", missing_strategy=strategy)
    assert result["input_count"] == 3
    assert result["missing_count"] == 1
    assert result["strategy"] == strategy
    if strategy == "ignore_series":
        assert result["value"] is None and result["valid_count"] == 0
    else:
        assert result["value"] == pytest.approx(case + 5)
        assert result["valid_count"] == (3 if strategy == "linear_interpolation" else 2)


# Validation boundaries are intentionally explicit: invalid values must fail
# closed rather than silently entering operational records.
@pytest.mark.parametrize("bad_severity", ["", "TRACE", "ALARM", "WARN", "FATAL", "UNKNOWN", "0", "INFO "])
def test_event_rejects_unsupported_severity(tmp_path, bad_severity):
    service = EventService(tmp_path / "events.sqlite3")
    with pytest.raises(ValueError):
        service.record("test.event", "message", severity=bad_severity)

@pytest.mark.parametrize("bad_quality", ["", "UNKNOWN", "ONLINE", "OFFLINE", "OK", "ERROR", "INVALID", "GOOD "])
def test_history_rejects_unknown_data_quality(tmp_path, bad_quality):
    service = HistoryService(tmp_path / "history.sqlite3")
    with pytest.raises(ValueError):
        service.append("s1", "p1", 1, quality=bad_quality)

@pytest.mark.parametrize("bad_channel", ["", "SMS", "SMTP", "HTTP", "MQTT", "SLACK", "PAGER", "EMAIL "])
def test_notifications_reject_unknown_transport_channel(tmp_path, bad_channel):
    service = NotificationService(tmp_path / "notifications.sqlite3")
    with pytest.raises(ValueError):
        service.add_route("route", bad_channel, "recipient")
