from pathlib import Path

from fastapi.testclient import TestClient

from app.main import STATIC_DIR, app

client = TestClient(app)


def test_index_serves_html():
    response = client.get("/")
    assert response.status_code == 200
    assert "SAP Guide" in response.text


def test_security_headers_are_set():
    headers = client.get("/").headers
    assert "default-src 'self'" in headers["content-security-policy"]
    assert headers["x-content-type-options"] == "nosniff"


def test_static_assets_are_served():
    assert client.get("/static/app.js").status_code == 200
    assert client.get("/static/style.css").status_code == 200


def test_page_has_no_inline_script():
    assert "<script>" not in client.get("/").text  # the CSP would block it anyway


def test_script_never_uses_innerhtml():
    js = Path(STATIC_DIR / "app.js").read_text()
    assert "innerHTML" not in js  # model output must only be inserted as text


def test_api_docs_are_disabled():
    assert client.get("/docs").status_code == 404
    assert client.get("/openapi.json").status_code == 404