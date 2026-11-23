import io

import pytest
from fastapi.testclient import TestClient
import numpy as np
from PIL import Image

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import database, main
from app.database import Base
from app.services.pipelines import ModelRunner, RUNNERS, TASKS


@pytest.fixture()
def client(tmp_path, monkeypatch):
    test_engine = create_engine(f"sqlite:///{tmp_path / 'test.db'}", connect_args={"check_same_thread": False})
    monkeypatch.setattr(database, "SessionLocal", sessionmaker(bind=test_engine, autoflush=False, autocommit=False))
    monkeypatch.setattr(main, "engine", test_engine)
    with TestClient(main.app) as c:
        yield c
    test_engine.dispose()


def image_bytes(size=(320, 320)):
    checker = ((np.indices(size).sum(axis=0) // 8) % 2 * 150 + 50).astype("uint8")
    img = Image.fromarray(np.stack([checker * .8, checker, checker * .72], axis=2).astype("uint8"), "RGB")
    out = io.BytesIO()
    img.save(out, format="JPEG")
    return out.getvalue()


def test_health_and_model_status(client):
    assert client.get("/api/health").json()["status"] == "ok"
    models = client.get("/api/models").json()["models"]
    assert {x["task"] for x in models} == {"tb_screening", "dr_grading"}
    assert all(not x["ready"] for x in models)


def test_protected_host_requires_credentials_for_api_data(client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "auth_required", True)
    monkeypatch.setattr(settings, "access_username", "researcher")
    monkeypatch.setattr(settings, "access_password", "a-strong-test-password-123")
    assert client.get("/api/health").status_code == 200
    assert client.get("/api/models").status_code == 401
    assert client.get("/api/cases", auth=("researcher", "a-strong-test-password-123")).status_code == 200


@pytest.mark.parametrize(("path", "task"), [("/api/screen/tb", "tb_screening"), ("/api/screen/dr", "dr_grading")])
def test_screening_is_indeterminate_without_checkpoint(client, path, task):
    response = client.post(path, files={"file": ("synthetic-not-medical.jpg", image_bytes(), "image/jpeg")})
    assert response.status_code == 200
    payload = response.json()
    assert payload["task"] == task
    assert payload["uncertainty"]["abstain"] is True
    assert payload["prediction"]["label"] == "indeterminate"
    assert "not a diagnosis" in payload["disclaimer"]
    assert client.get("/api/cases").json()[0]["case_id"] == payload["case_id"]


def test_invalid_and_corrupt_uploads_are_rejected(client):
    assert client.post("/api/screen/tb", files={"file": ("x.txt", b"not an image", "text/plain")}).status_code == 422
    assert client.post("/api/screen/dr", files={"file": ("x.jpg", b"broken", "image/jpeg")}).status_code == 422
    assert client.post("/api/screen/tb", files={"file": ("mismatch.png", image_bytes(), "image/png")}).status_code == 422


def test_case_records_do_not_retain_image_hashes(client):
    case_id = client.post("/api/screen/tb", files={"file": ("synthetic.jpg", image_bytes(), "image/jpeg")}).json()["case_id"]
    detail = client.get(f"/api/cases/{case_id}").json()
    assert "image_sha256" not in detail


def test_oversized_upload_is_rejected(client):
    from app.config import settings
    too_large = b"0" * (settings.max_upload_bytes + 1)
    response = client.post("/api/screen/tb", files={"file": ("oversized.jpg", too_large, "image/jpeg")})
    assert response.status_code == 413


def test_low_resolution_image_is_rejected_as_poor_quality(client):
    response = client.post("/api/screen/tb", files={"file": ("tiny.jpg", image_bytes((64, 64)), "image/jpeg")})
    payload = response.json()
    assert response.status_code == 200
    assert payload["quality"]["status"] == "poor"
    assert payload["uncertainty"]["reason"] == "image_quality_rejection"


def test_checkpoint_without_provenance_is_not_loaded(tmp_path, monkeypatch):
    checkpoint = tmp_path / "unreviewed.pt"
    checkpoint.write_bytes(b"synthetic checkpoint")
    monkeypatch.setitem(TASKS["tb_screening"], "path", str(checkpoint))
    runner = ModelRunner("tb_screening")
    assert not runner.ready
    assert runner.error and "valueerror" in runner.error.lower()


def test_inference_exception_safely_abstains(client, monkeypatch):
    class BrokenRunner:
        def predict(self, _image):
            raise RuntimeError("synthetic failure")

    monkeypatch.setitem(RUNNERS, "tb_screening", BrokenRunner())
    response = client.post("/api/screen/tb", files={"file": ("synthetic.jpg", image_bytes(), "image/jpeg")})
    assert response.status_code == 200
    assert response.json()["prediction"]["label"] == "indeterminate"
    assert response.json()["uncertainty"]["reason"] == "inference_error"


def test_review_delete_and_report(client):
    case_id = client.post("/api/screen/tb", files={"file": ("sample.jpg", image_bytes(), "image/jpeg")}).json()["case_id"]
    assert client.post(f"/api/review/{case_id}", json={"status": "indeterminate", "note": "synthetic test"}).status_code == 200
    detail = client.get(f"/api/cases/{case_id}").json()
    assert detail["review"]["status"] == "indeterminate"
    report = client.post("/api/export/report", json={"case_id": case_id})
    assert report.status_code == 200 and report.headers["content-type"] == "application/pdf"
    assert client.delete(f"/api/cases/{case_id}").status_code == 204
    assert client.get(f"/api/cases/{case_id}").status_code == 404
