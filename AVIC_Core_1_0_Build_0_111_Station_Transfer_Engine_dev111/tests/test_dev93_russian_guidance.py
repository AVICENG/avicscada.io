from pathlib import Path


def test_network_workspace_contains_plain_language_guidance():
    source = (Path(__file__).parents[1] / "avic_core/ui/static/index.html").read_text(encoding="utf-8")
    assert "Словарь простыми словами" in source
    assert "Шлюз протоколов" in source
    assert "Пинг проверяет, отвечает ли сетевой адрес" in source
    assert "не доказывает, что контроллер поддерживает BACnet или Modbus" in source
    assert "Если оборудование находится в другой подсети" in source


def test_time_manager_uses_station_picker_and_localized_timezones():
    source = (Path(__file__).parents[1] / "avic_core/ui/static/index.html").read_text(encoding="utf-8")
    assert 'id="timeStation"' in source and "Загрузка списка станций" in source
    assert 'value="Europe/Moscow"' in source
    assert 'value="Asia/Vladivostok"' in source
    assert "Единое время UTC" in source
    assert "Местное время объекта" in source
    assert "Фактическая отправка времени в контроллер пока не выполняется" in source


def test_manual_network_form_explains_gateway_and_dns():
    source = (Path(__file__).parents[1] / "avic_core/ui/static/index.html").read_text(encoding="utf-8")
    assert "Адрес всей сети (с маской)" in source
    assert "Шлюз / маршрутизатор (если известен)" in source
    assert "DNS помогает находить компьютеры по именам" in source
    assert "не вводите случайные значения" in source


def test_time_manager_station_policy_and_device_permission_api(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui.app import create_ui_app

    with TestClient(create_ui_app(data_dir=str(tmp_path))) as client:
        project = client.post('/api/projects', json={'name': 'Дальний объект'}).json()
        station = client.post('/api/stations', json={'project_id': project['id'], 'name': 'Владивосток'}).json()
        saved = client.put(f"/api/stations/{station['id']}/time", json={
            'timezone': 'Asia/Vladivostok', 'ntp_enabled': False, 'ntp_servers': []
        })
        assert saved.status_code == 200
        current = client.get(f"/api/stations/{station['id']}/time").json()
        assert current['timezone'] == 'Asia/Vladivostok'
        assert '+10:00' in current['local_now']
        permission = client.put(
            f"/api/stations/{station['id']}/devices/controller-1/time-sync-permission",
            json={'allowed': False, 'approved_by': 'engineer', 'reason': 'По умолчанию запрещено'}
        )
        assert permission.status_code == 200
        assert permission.json()['allowed'] is False


def test_new_schedules_inherit_station_timezone_instead_of_manual_text_entry():
    source = (Path(__file__).parents[1] / "avic_core/ui/static/index.html").read_text(encoding="utf-8")
    assert 'id="schTimezone"' in source
    assert "readonly" in source[source.index('id="schTimezone"') - 120:source.index('id="schTimezone"') + 180]
    assert "schedulerSyncTimezone" in source
    assert "Часовой пояс взят из Time Manager станции" in source
