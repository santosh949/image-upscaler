import sqlite3
import os
import time
import json
from typing import Dict, Any, Optional, List
from backend.app.core.config import settings
from backend.app.services.migration_service import migration_service
from backend.app.services.storage_service import storage_service

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(settings.DATABASE_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_db() -> None:
    os.makedirs(os.path.dirname(os.path.abspath(settings.DATABASE_PATH)), exist_ok=True)
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                image_id TEXT NOT NULL,
                input_path TEXT NOT NULL,
                output_path TEXT,
                mode TEXT NOT NULL,
                scale INTEGER NOT NULL,
                model TEXT NOT NULL,
                status TEXT NOT NULL,
                stage TEXT NOT NULL,
                progress REAL,
                message TEXT,
                error TEXT,
                crop_region TEXT,
                output_format TEXT DEFAULT 'png',
                quality INTEGER DEFAULT 95,
                created_at REAL NOT NULL,
                updated_at REAL NOT NULL
            );
        """)

        existing_cols = [r[1] for r in conn.execute("PRAGMA table_info(jobs)").fetchall()]
        if "crop_region" not in existing_cols:
            conn.execute("ALTER TABLE jobs ADD COLUMN crop_region TEXT")
        if "output_format" not in existing_cols:
            conn.execute("ALTER TABLE jobs ADD COLUMN output_format TEXT DEFAULT 'png'")
        if "quality" not in existing_cols:
            conn.execute("ALTER TABLE jobs ADD COLUMN quality INTEGER DEFAULT 95")
        if "plan_json" not in existing_cols:
            conn.execute("ALTER TABLE jobs ADD COLUMN plan_json TEXT")
        if "preset" not in existing_cols:
            conn.execute("ALTER TABLE jobs ADD COLUMN preset TEXT")

        conn.execute("""
            CREATE TABLE IF NOT EXISTS images (
                id TEXT PRIMARY KEY,
                original_filename TEXT NOT NULL,
                storage_path TEXT NOT NULL,
                width INTEGER NOT NULL,
                height INTEGER NOT NULL,
                format TEXT NOT NULL,
                size_bytes INTEGER NOT NULL,
                created_at REAL NOT NULL
            );
        """)
        conn.execute("UPDATE jobs SET status = 'failed', error = 'Server restarted while job was in progress' WHERE status = 'processing'")
        conn.commit()

    # Apply forward migrations to Version Graph
    migration_service.migrate(settings.DATABASE_PATH)
    # Startup reconciliation of storage
    storage_service.reconcile_startup()

# --- Legacy Image & Job Helpers (Preserved for 100% Backward Compatibility) ---

def create_image_record(img_id: str, filename: str, path: str, w: int, h: int, fmt: str, size: int) -> None:
    now = time.time()
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO images (id, original_filename, storage_path, width, height, format, size_bytes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (img_id, filename, path, w, h, fmt, size, now))

        # Automatically register into Version Graph (Project + Original Version)
        proj_id = f"proj_{img_id}"
        orig_ver_id = f"v_orig_{img_id}"
        mp = round((w * h) / 1_000_000.0, 2)

        conn.execute("""
            INSERT OR IGNORE INTO projects (id, name, source_image_id, created_at, settings)
            VALUES (?, ?, ?, ?, '{}')
        """, (proj_id, filename, img_id, now))

        conn.execute("""
            INSERT OR IGNORE INTO versions (
                id, parent_version_id, project_id, storage_ref,
                width, height, megapixels, pixel_format, bit_depth,
                has_alpha, operation, state, decision, created_at
            ) VALUES (?, NULL, ?, ?, ?, ?, ?, ?, 8, 0, 'original', 'ready', 'accepted', ?)
        """, (orig_ver_id, proj_id, path, w, h, mp, fmt, now))
        conn.commit()

def get_image_record(img_id: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM images WHERE id = ?", (img_id,)).fetchone()
        return dict(row) if row else None

def create_job(
    job_id: str,
    image_id: str,
    input_path: str,
    mode: str,
    scale: int,
    model: str,
    crop_region: Optional[str] = None,
    output_format: str = "png",
    quality: int = 95,
    plan_json: Optional[str] = None,
    preset: Optional[str] = None
) -> None:
    now = time.time()
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO jobs (id, image_id, input_path, output_path, mode, scale, model, status, stage, progress, message, error, crop_region, output_format, quality, plan_json, preset, created_at, updated_at)
            VALUES (?, ?, ?, NULL, ?, ?, ?, 'queued', 'waiting', 0.0, 'Job queued', NULL, ?, ?, ?, ?, ?, ?, ?)
        """, (job_id, image_id, input_path, mode, scale, model, crop_region, output_format, quality, plan_json, preset, now, now))
        conn.commit()

def get_stages_for_job(job_id: str) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        stages = conn.execute("SELECT * FROM stages WHERE job_id = ? ORDER BY stage_index ASC", (job_id,)).fetchall()
        result = []
        for s in stages:
            s_dict = dict(s)
            sid = s["stage_id"]
            tot = conn.execute("SELECT COUNT(*) as c FROM tiles WHERE stage_id = ?", (sid,)).fetchone()["c"]
            done = conn.execute("SELECT COUNT(*) as c FROM tiles WHERE stage_id = ? AND status = 'completed'", (sid,)).fetchone()["c"]
            s_dict["total_tiles"] = tot
            s_dict["completed_tiles"] = done
            result.append(s_dict)
        return result

def update_job_status(job_id: str, status: str, stage: str, progress: Optional[float] = None, message: Optional[str] = None, output_path: Optional[str] = None, error: Optional[str] = None) -> None:
    now = time.time()
    with get_db_connection() as conn:
        conn.execute("""
            UPDATE jobs
            SET status = ?, stage = ?, progress = COALESCE(?, progress), message = COALESCE(?, message), output_path = COALESCE(?, output_path), error = COALESCE(?, error), updated_at = ?
            WHERE id = ?
        """, (status, stage, progress, message, output_path, error, now, job_id))
        conn.commit()

def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return dict(row) if row else None

def get_all_jobs(limit: int = 30) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

def delete_job(job_id: str) -> bool:
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        conn.commit()
        return True

def get_next_queued_job() -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        row = conn.execute("""
            SELECT * FROM jobs
            WHERE status = 'queued'
            ORDER BY created_at ASC
            LIMIT 1
        """).fetchone()
        return dict(row) if row else None

def get_queued_jobs() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute("""
            SELECT * FROM jobs
            WHERE status IN ('queued', 'processing')
            ORDER BY created_at ASC
        """).fetchall()
        return [dict(r) for r in rows]

def clear_queued_jobs() -> int:
    with get_db_connection() as conn:
        cur = conn.execute("""
            UPDATE jobs SET status = 'cancelled', message = 'Cancelled from batch queue'
            WHERE status = 'queued'
        """)
        conn.commit()
        return cur.rowcount

# --- Version Graph Database Operations ---

def create_project(project_id: str, name: str, source_image_id: str, settings_dict: Optional[Dict[str, Any]] = None) -> None:
    now = time.time()
    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO projects (id, name, source_image_id, created_at, settings)
            VALUES (?, ?, ?, ?, ?)
        """, (project_id, name, source_image_id, now, json.dumps(settings_dict or {})))
        conn.commit()

def get_project(project_id: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return dict(row) if row else None

def list_projects(limit: int = 50) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM projects ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

def create_version(version_data: Dict[str, Any]) -> None:
    """Enforces Invariant E2.2: A job never writes into a version it reads from."""
    now = time.time()
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO versions (
                id, parent_version_id, project_id, storage_ref,
                width, height, megapixels, pixel_format, bit_depth,
                has_alpha, color_profile, operation, mode, model_id,
                checkpoint_hash, parameters, tile_size, overlap,
                backend, device, runtime_s, peak_ram, peak_vram,
                sha256, quality_eval, state, decision, created_at
            ) VALUES (
                :id, :parent_version_id, :project_id, :storage_ref,
                :width, :height, :megapixels, :pixel_format, :bit_depth,
                :has_alpha, :color_profile, :operation, :mode, :model_id,
                :checkpoint_hash, :parameters, :tile_size, :overlap,
                :backend, :device, :runtime_s, :peak_ram, :peak_vram,
                :sha256, :quality_eval, :state, :decision, :created_at
            )
        """, {
            "id": version_data["id"],
            "parent_version_id": version_data.get("parent_version_id"),
            "project_id": version_data["project_id"],
            "storage_ref": version_data["storage_ref"],
            "width": version_data["width"],
            "height": version_data["height"],
            "megapixels": version_data["megapixels"],
            "pixel_format": version_data.get("pixel_format", "RGB"),
            "bit_depth": version_data.get("bit_depth", 8),
            "has_alpha": 1 if version_data.get("has_alpha") else 0,
            "color_profile": version_data.get("color_profile", "sRGB"),
            "operation": version_data["operation"],
            "mode": version_data.get("mode"),
            "model_id": version_data.get("model_id"),
            "checkpoint_hash": version_data.get("checkpoint_hash"),
            "parameters": json.dumps(version_data.get("parameters") or {}),
            "tile_size": version_data.get("tile_size", 256),
            "overlap": version_data.get("overlap", 32),
            "backend": version_data.get("backend", "ncnn-vulkan"),
            "device": version_data.get("device", "GPU 0"),
            "runtime_s": version_data.get("runtime_s"),
            "peak_ram": version_data.get("peak_ram"),
            "peak_vram": version_data.get("peak_vram"),
            "sha256": version_data.get("sha256"),
            "quality_eval": json.dumps(version_data.get("quality_eval") or {}),
            "state": version_data.get("state", "ready"),
            "decision": version_data.get("decision", "pending"),
            "created_at": version_data.get("created_at", now)
        })
        conn.commit()

def get_version(version_id: str) -> Optional[Dict[str, Any]]:
    with get_db_connection() as conn:
        row = conn.execute("SELECT * FROM versions WHERE id = ?", (version_id,)).fetchone()
        return dict(row) if row else None

def get_versions_by_project(project_id: str) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM versions WHERE project_id = ? ORDER BY created_at ASC", (project_id,)).fetchall()
        return [dict(r) for r in rows]

def get_child_versions(parent_version_id: str) -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM versions WHERE parent_version_id = ?", (parent_version_id,)).fetchall()
        return [dict(r) for r in rows]

def update_version_decision(version_id: str, decision: str) -> bool:
    """Invariant E2.4 & E2.5: accept or reject."""
    if decision not in ("accepted", "rejected", "pending"):
        raise ValueError(f"Invalid decision: {decision}")
    with get_db_connection() as conn:
        res = conn.execute("UPDATE versions SET decision = ? WHERE id = ?", (decision, version_id))
        conn.commit()
        return res.rowcount > 0

def delete_version_with_rules(version_id: str, force_subtree: bool = False) -> Dict[str, Any]:
    """
    Invariant E2.6:
    - Deleting a version that has children is blocked unless force_subtree=True.
    - The original version is protected: deleting it requires explicit confirmation and cannot have children unless subtree deleted.
    """
    with get_db_connection() as conn:
        v = conn.execute("SELECT * FROM versions WHERE id = ?", (version_id,)).fetchone()
        if not v:
            return {"success": False, "error": "Version not found"}

        children = conn.execute("SELECT id FROM versions WHERE parent_version_id = ?", (version_id,)).fetchall()
        if children and not force_subtree:
            return {
                "success": False,
                "error": f"Cannot delete version {version_id}: it has {len(children)} child versions. Deletion of entire subtree required.",
                "child_count": len(children)
            }

        # Check if original
        if v["parent_version_id"] is None and not force_subtree:
            return {
                "success": False,
                "error": "Protected: Original source version requires explicit subtree confirmation to delete."
            }

        # Collect all descendants if subtree
        to_delete = [version_id]
        if force_subtree:
            def find_descendants(pid):
                kids = conn.execute("SELECT id FROM versions WHERE parent_version_id = ?", (pid,)).fetchall()
                for k in kids:
                    to_delete.append(k["id"])
                    find_descendants(k["id"])
            find_descendants(version_id)

        # Delete database records
        placeholders = ",".join("?" for _ in to_delete)
        conn.execute(f"DELETE FROM versions WHERE id IN ({placeholders})", to_delete)
        conn.commit()

        return {"success": True, "deleted_version_ids": to_delete}
