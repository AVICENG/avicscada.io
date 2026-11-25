"""Point List View acceptance matrix derived from IQVISION User Manual §5."""
from itertools import product
import pytest
from avic_core.domain.point_views import PointViewService

QUALITIES = ["GOOD", "UNCERTAIN", "BAD", "COMM_LOST", "STALE"]
SORTS = ["name", "data_type", "value", "unit", "quality", "native_identity"]
SCENARIOS = range(34)


def records_for(case):
    rows=[]
    for i in range(8):
        quality=QUALITIES[(i+case)%len(QUALITIES)]
        station=f"station-{(i+case)%3}"
        payload={"name":f"Point {i:02d} scenario {case}","data_type":["BOOLEAN","NUMERIC","ENUM","STRING"][i%4],
                 "unit":["°C","%","Pa","rpm"][i%4],"value":float((i*7+case)%19),
                 "quality":quality,"native_identity":f"bacnet:analog-input:{i+case*10}",
                 "device":{"station_id":station}}
        rows.append({"entity_id":f"p-{case}-{i}","name":payload["name"],"version":1,"payload":payload})
    return rows


@pytest.mark.parametrize("quality,sort_by,sort_dir,favorites_only,case", product(QUALITIES,SORTS,["asc","desc"],[False,True],SCENARIOS))
def test_iqvision_point_list_filter_sort_favorites_and_station_scope(quality,sort_by,sort_dir,favorites_only,case):
    rows=records_for(case)
    favorites={f"p-{case}-{i}" for i in range(0,8,2)}
    result=PointViewService.query(rows,favorite_ids=favorites,quality=quality,
        favorites_only=favorites_only,sort_by=sort_by,sort_dir=sort_dir,limit=50)
    expected=[r for r in rows if r["payload"]["quality"]==quality and
              (not favorites_only or r["entity_id"] in favorites)]
    assert result["total"]==len(expected)
    assert all(x["quality"]==quality for x in result["points"])
    assert all((not favorites_only) or x["favorite"] for x in result["points"])
    vals=[x[sort_by] for x in result["points"]]
    assert vals==sorted(vals,key=lambda v:(v is None,str(v).casefold() if not isinstance(v,(int,float)) else v),reverse=sort_dir=="desc")
    assert result["favorite_count"]==sum(r["entity_id"] in favorites for r in expected)


@pytest.mark.parametrize("search_mode,offset,limit,case", product(["match","miss","empty","native"],[0,1,3,7],[1,2,5,8],[*range(40)]))
def test_iqvision_point_list_search_pagination_and_total_are_consistent(search_mode,offset,limit,case):
    rows=records_for(case)
    search={"match":f"point 0{case}","miss":"not-present-token","empty":"","native":f"analog-input:{case*10}"}[search_mode]
    result=PointViewService.query(rows,search=search,offset=offset,limit=limit,sort_by="name")
    assert result["total"]==len([r for r in rows if search.casefold() in (r["name"]+" "+r["payload"]["native_identity"]).casefold()])
    assert len(result["points"])<=limit
    assert result["offset"]==offset and result["limit"]==limit
    assert result["points"]==PointViewService.query(rows,search=search,offset=offset,limit=limit,sort_by="name")["points"]


@pytest.mark.parametrize("user,point,station", product([f"user-{i}" for i in range(4)],[f"point-{i}" for i in range(4)],[None,"station-a","station-b","station-c"]))
def test_point_favorites_persist_and_are_isolated_by_user_and_station(tmp_path,user,point,station):
    path=tmp_path/"point-views.sqlite3"
    service=PointViewService(path)
    assert service.add_favorite(point,user_id=user,station_id=station)["favorite"] is True
    reopened=PointViewService(path)
    assert point in reopened.favorite_ids(user_id=user)
    assert point not in reopened.favorite_ids(user_id="another-user")
    if station:
        assert point in reopened.favorite_ids(user_id=user,station_id=station)
        assert point not in reopened.favorite_ids(user_id=user,station_id="other-station")
    reopened.remove_favorite(point,user_id=user)
    assert point not in PointViewService(path).favorite_ids(user_id=user)


@pytest.mark.parametrize("sort_by",["", "created_at", "__dict__", "payload", "sql;drop", "name desc"])
def test_point_view_rejects_unapproved_sort_fields(sort_by):
    with pytest.raises(ValueError):
        PointViewService.query([],sort_by=sort_by)


@pytest.mark.parametrize("sort_dir",["", "ascending", "DESC; DROP", "random", "up"])
def test_point_view_rejects_unapproved_sort_direction(sort_dir):
    with pytest.raises(ValueError):
        PointViewService.query([],sort_dir=sort_dir)


@pytest.mark.parametrize("quality",["", "OFFLINE", "UNKNOWN", "GOOD ", "alarm"])
def test_point_view_rejects_unknown_quality(quality):
    if quality=="":
        assert PointViewService.query([],quality=quality)["total"]==0
    else:
        with pytest.raises(ValueError): PointViewService.query([],quality=quality)


@pytest.mark.parametrize("offset,limit",[(-1,1),(0,0),(0,5001),(1,-1),(-10,5000)])
def test_point_view_rejects_invalid_pagination(offset,limit):
    with pytest.raises(ValueError): PointViewService.query([],offset=offset,limit=limit)


def test_point_favorites_and_csv_api_are_persistent_and_scoped(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui import create_ui_app
    from avic_core.domain.models import Project, Station, Device, Point, PointQuality
    app=create_ui_app(data_dir=str(tmp_path)); client=TestClient(app)
    project=Project(name="Проект")
    station=Station(name="Станция",project_id=project.id)
    device=Device(name="Контроллер",station_id=station.id,protocol="BACnet/IP")
    point=Point(name="Температура",device_id=device.id,data_type="float",unit="°C",value=22.5,
                quality=PointQuality.GOOD,native_identity="bacnet:analog-input:1")
    for entity in (project,station,device,point): app.state.core.repository.save(entity)
    result=client.get("/api/engineering/points")
    assert result.status_code==200 and result.json()["total"]==1
    row=result.json()["points"][0]
    assert row["station_id"]==station.id and row["quality"]=="GOOD" and row["favorite"] is False
    assert client.post(f"/api/engineering/points/{point.id}/favorite").json()["favorite"] is True
    filtered=client.get("/api/engineering/points",params={"favorites_only":"true"}).json()
    assert filtered["total"]==1 and filtered["points"][0]["favorite"] is True
    csv=client.get("/api/engineering/points/export.csv")
    assert csv.status_code==200 and "Температура" in csv.text and "Native identity" in csv.text
    assert client.delete(f"/api/engineering/points/{point.id}/favorite").json()["favorite"] is False
    app.state.core.close()


def test_point_favorite_api_rejects_non_point_and_missing_point(tmp_path):
    from fastapi.testclient import TestClient
    from avic_core.ui import create_ui_app
    from avic_core.domain.models import Project
    app=create_ui_app(data_dir=str(tmp_path)); client=TestClient(app)
    non_point=Project(name="Не точка"); app.state.core.repository.save(non_point)
    assert client.post(f"/api/engineering/points/{non_point.id}/favorite").status_code==404
    assert client.post("/api/engineering/points/00000000-0000-0000-0000-000000000000/favorite").status_code==404
    app.state.core.close()
