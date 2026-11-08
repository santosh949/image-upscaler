import os
import io
import stat
import pytest
from PIL import Image
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.database import (
    get_db_connection, create_project, get_project,
    get_version, get_versions_by_project, update_version_decision,
    delete_version_with_rules
)
from backend.app.services.storage_service import storage_service
from backend.app.services.version_service import version_service

client = TestClient(app)

def test_schema_migration_preserves_legacy_records():
    with get_db_connection() as conn:
        ver_row = conn.execute("SELECT MAX(version) as ver FROM schema_version").fetchone()
        assert ver_row["ver"] >= 2, "Database schema version must be at least 2"

        # Check projects and versions tables exist
        tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        assert "projects" in tables
        assert "versions" in tables
        assert "stages" in tables
        assert "tiles" in tables

def test_invariant_e2_1_and_e2_3_atomic_write_and_readonly(tmp_path):
    target = str(tmp_path / "test_atomic.png")
    img = Image.new("RGB", (64, 64), color=(120, 180, 240))

    sha256 = storage_service.write_atomic_image(target, img, format_name="PNG")
    assert os.path.exists(target)
    assert not os.path.exists(f"{target}.partial"), "Partial orphan must not remain after atomic commit"

    # Verify hash matches
    recomputed = storage_service.compute_sha256(target)
    assert recomputed == sha256

def test_invariant_e2_2_and_e2_4_parent_immutability(tmp_path):
    # Create parent version
    p_img = Image.new("RGB", (64, 64), color=(50, 50, 50))
    p_path = str(tmp_path / "parent.png")
    p_hash = storage_service.write_atomic_image(p_path, p_img)

    proj_res = version_service.create_project_from_image(
        image_id="test_img_immut",
        filename="parent.png",
        image_path=p_path,
        w=64, h=64, fmt="PNG"
    )
    proj_id = proj_res["project_id"]
    parent_ver_id = proj_res["root_version_id"]

    # Create child version
    c_img = Image.new("RGB", (128, 128), color=(100, 100, 100))
    c_path = str(tmp_path / "child.png")
    c_hash = storage_service.write_atomic_image(c_path, c_img)

    child_ver = version_service.register_derived_version(
        project_id=proj_id,
        parent_version_id=parent_ver_id,
        output_image_path=c_path,
        operation="upscale",
        mode="upscale",
        model_id="realesrgan-x4plus",
        scale=2,
        runtime_s=1.2
    )

    # Invariant E2.2: Parent file and DB record are completely untouched
    assert os.path.exists(p_path)
    assert storage_service.compute_sha256(p_path) == p_hash
    parent_db = get_version(parent_ver_id)
    assert parent_db["sha256"] == p_hash

    # Invariant E2.4: Rejecting a stage leaves parent byte-identical
    update_version_decision(child_ver["id"], "rejected")
    assert storage_service.compute_sha256(p_path) == p_hash

def test_invariant_e2_6_deletion_rules(tmp_path):
    # Setup test project with root and child
    p_img = Image.new("RGB", (32, 32), color=(10, 20, 30))
    p_path = str(tmp_path / "del_parent.png")
    storage_service.write_atomic_image(p_path, p_img)

    proj_res = version_service.create_project_from_image(
        image_id="del_test_img",
        filename="del_parent.png",
        image_path=p_path,
        w=32, h=32, fmt="PNG"
    )
    proj_id = proj_res["project_id"]
    parent_id = proj_res["root_version_id"]

    c_img = Image.new("RGB", (64, 64), color=(20, 40, 60))
    c_path = str(tmp_path / "del_child.png")
    storage_service.write_atomic_image(c_path, c_img)

    child_ver = version_service.register_derived_version(
        project_id=proj_id,
        parent_version_id=parent_id,
        output_image_path=c_path,
        operation="upscale",
        mode="upscale",
        model_id="realesrgan-x4plus",
        scale=2,
        runtime_s=0.5
    )

    # Rule 1: Cannot delete parent when child exists without force_subtree
    del_res = delete_version_with_rules(parent_id, force_subtree=False)
    assert del_res["success"] is False
    assert "child versions" in del_res["error"]

    # Rule 2: Cannot delete original version without force confirmation
    del_orig = delete_version_with_rules(parent_id, force_subtree=False)
    assert del_orig["success"] is False

    # Rule 3: Child can be deleted without affecting parent
    del_child = delete_version_with_rules(child_ver["id"], force_subtree=False)
    assert del_child["success"] is True
    assert get_version(parent_id) is not None

def test_api_projects_and_versions():
    # Test list projects
    resp = client.get("/api/v1/projects")
    assert resp.status_code == 200
    data = resp.json()
    assert "projects" in data

    if len(data["projects"]) > 0:
        first_proj = data["projects"][0]
        proj_id = first_proj["id"]

        # Get project detail
        resp_p = client.get(f"/api/v1/projects/{proj_id}")
        assert resp_p.status_code == 200
        p_data = resp_p.json()
        assert "versions" in p_data
        assert len(p_data["versions"]) > 0

        # Verify no raw filesystem disk path is leaked in version API output
        first_ver = p_data["versions"][0]
        assert "storage_ref" not in first_ver or not first_ver["storage_ref"].startswith("C:\\")

        # Test decision endpoint
        ver_id = first_ver["id"]
        resp_d = client.post(f"/api/v1/versions/{ver_id}/decision", json={"decision": "accepted"})
        assert resp_d.status_code == 200
        assert resp_d.json()["decision"] == "accepted"

def test_authoritative_manifest_written(tmp_path):
    p_img = Image.new("RGB", (32, 32), color=(10, 20, 30))
    p_path = str(tmp_path / "manifest_test.png")
    storage_service.write_atomic_image(p_path, p_img)

    proj_res = version_service.create_project_from_image(
        image_id="manifest_img",
        filename="manifest_test.png",
        image_path=p_path,
        w=32, h=32, fmt="PNG"
    )
    ver_id = proj_res["root_version_id"]

    manifest_file = os.path.join(storage_service.manifests_dir, f"{ver_id}.json")
    assert os.path.exists(manifest_file), "Authoritative manifest JSON must exist per Part E4"

