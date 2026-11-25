from fastapi.testclient import TestClient
from avic_core.ui import create_ui_app


def test_repository_opens_new_graphics_workbench_not_legacy_pages(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    response = client.get("/repository")
    assert response.status_code == 200
    assert "Repository · Graphics Workbench" in response.text
    assert "Объёмная SVG-библиотека" in response.text
    assert "Импортировать в библиотеку станции" in response.text
    assert "Web Pages · Unified Editor" not in response.text


def test_repository_branch_has_agreed_hierarchy_and_core_ownership(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    project = client.post("/api/projects", json={"name": "P", "description": ""}).json()
    station = client.post("/api/stations", json={"project_id": project["id"], "name": "S", "description": ""}).json()
    tree = client.get("/api/engineering/tree").json()
    branch = tree["projects"][0]["stations"][0]["repository"]
    assert branch["id"] == "avic.repository"
    assert branch["parent_id"] == station["id"]
    assert branch["owns_core_objects"] is False
    assert branch["core_authoritative"] is True
    assert [x["name"] for x in branch["children"]] == ["Web Application", "Graphics", "Documentation"]
    graphics = branch["children"][1]
    assert [x["name"] for x in graphics["children"]] == ["Pages", "Components", "Symbols", "Assets", "Templates"]


def test_shared_tree_routes_repository_items_to_new_editor_with_station_scope(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    project = client.post("/api/projects", json={"name": "P", "description": ""}).json()
    station = client.post("/api/stations", json={"project_id": project["id"], "name": "S", "description": ""}).json()
    tree = client.get("/").text
    assert 'data-kind="repository-item"' in tree
    assert "repository-item" in tree
    workspace = client.get(f"/repository?station={station['id']}&section=GraphicsRepository")
    assert workspace.status_code == 200
    assert "Repository · Graphics Workbench" in workspace.text
    legacy = client.get("/pages")
    assert legacy.status_code == 200
    assert "Repository · Graphics Workbench" in legacy.text


def test_repository_root_in_shared_tree_opens_web_application_page_builder(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    project = client.post("/api/projects", json={"name": "P", "description": ""}).json()
    station = client.post("/api/stations", json={"project_id": project["id"], "name": "S", "description": ""}).json()

    home = client.get("/")
    assert home.status_code == 200
    assert "section:'WebApplication'" in home.text

    page_builder = client.get(f"/repository?station={station['id']}&section=WebApplication")
    assert page_builder.status_code == 200
    assert "Библиотека элементов" in page_builder.text
    assert "Загрузить изображение с компьютера" in page_builder.text
    assert "Опубликовать" in page_builder.text
    assert "pages.html" not in page_builder.text

    graphics = client.get(f"/repository?station={station['id']}&section=GraphicsRepository")
    assert graphics.status_code == 200
    assert "Repository · Graphics Workbench" in graphics.text


def test_ui_health_reports_actual_dev109_version(tmp_path):
    client = TestClient(create_ui_app(data_dir=str(tmp_path)))
    response = client.get("/api/ui/health")
    assert response.status_code == 200
    assert response.json()["version"] == "1.0.0.dev109"
