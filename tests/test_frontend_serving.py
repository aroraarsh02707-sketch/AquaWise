from app import create_app


def _enable_test_frontend(app, tmp_path):
    dist = tmp_path / "dist"
    assets = dist / "assets"
    assets.mkdir(parents=True)
    (dist / "index.html").write_text(
        "<!doctype html><html><body><div id=\"root\"></div></body></html>",
        encoding="utf-8",
    )
    (assets / "app.js").write_text("console.log('AquaWise');", encoding="utf-8")
    (dist / "robots.txt").write_text("User-agent: *\nDisallow:\n", encoding="utf-8")
    app.config["FRONTEND_DIST"] = str(dist)
    app.config["SERVE_FRONTEND"] = True


def test_frontend_root_serves_built_index(tmp_path):
    app = create_app("testing")
    _enable_test_frontend(app, tmp_path)

    response = app.test_client().get("/")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b'<div id="root"></div>' in response.data


def test_frontend_assets_and_public_files_are_served(tmp_path):
    app = create_app("testing")
    _enable_test_frontend(app, tmp_path)
    client = app.test_client()

    asset_response = client.get("/assets/app.js")
    public_response = client.get("/robots.txt")

    assert asset_response.status_code == 200
    assert b"AquaWise" in asset_response.data
    assert public_response.status_code == 200
    assert public_response.mimetype == "text/plain"


def test_spa_path_refresh_falls_back_to_index(tmp_path):
    app = create_app("testing")
    _enable_test_frontend(app, tmp_path)

    response = app.test_client().get("/recommendations/42")

    assert response.status_code == 200
    assert response.mimetype == "text/html"
    assert b'<div id="root"></div>' in response.data


def test_unknown_api_path_stays_json_404_with_frontend_enabled(tmp_path):
    app = create_app("testing")
    _enable_test_frontend(app, tmp_path)

    response = app.test_client().get("/api/not-a-real-endpoint")

    assert response.status_code == 404
    assert response.is_json
    assert response.get_json()["error"]["code"] == "NOT_FOUND"


def test_csrf_api_route_remains_json_with_frontend_enabled(tmp_path):
    app = create_app("testing")
    _enable_test_frontend(app, tmp_path)

    response = app.test_client().get("/api/auth/csrf")

    assert response.status_code == 200
    assert response.is_json
    assert response.get_json()["success"] is True
    assert response.get_json()["data"]["csrf_token"]
