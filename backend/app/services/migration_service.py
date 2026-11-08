import os
import shutil
import sqlite3
import time
from backend.app.core.config import settings

class MigrationService:
    """
    Applies forward-only database schema migrations with automated pre-migration backup.
    Guarantees legacy jobs and existing records continue functioning seamlessly (Part E2a).
    """

    @staticmethod
    def migrate(db_path: str):
        if not os.path.exists(db_path):
            return

        # Step 1: Automated backup before migration
        backup_path = f"{db_path}.bak"
        try:
            shutil.copy2(db_path, backup_path)
        except Exception as e:
            print(f"Warning: Failed to create database backup: {e}")

        conn = sqlite3.connect(db_path, timeout=10)
        conn.row_factory = sqlite3.Row
        try:
            # Step 2: Check schema_version
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at REAL NOT NULL
                );
            """)
            cur_row = conn.execute("SELECT MAX(version) as cur_ver FROM schema_version").fetchone()
            current_version = cur_row["cur_ver"] if cur_row and cur_row["cur_ver"] is not None else 1

            if current_version < 2:
                # Migration 2: Version Graph Architecture
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        source_image_id TEXT NOT NULL,
                        created_at REAL NOT NULL,
                        settings TEXT
                    );
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS versions (
                        id TEXT PRIMARY KEY,
                        parent_version_id TEXT,
                        project_id TEXT NOT NULL,
                        storage_ref TEXT NOT NULL,
                        width INTEGER NOT NULL,
                        height INTEGER NOT NULL,
                        megapixels REAL NOT NULL,
                        pixel_format TEXT DEFAULT 'RGB',
                        bit_depth INTEGER DEFAULT 8,
                        has_alpha INTEGER DEFAULT 0,
                        color_profile TEXT DEFAULT 'sRGB',
                        operation TEXT NOT NULL,
                        mode TEXT,
                        model_id TEXT,
                        checkpoint_hash TEXT,
                        parameters TEXT,
                        tile_size INTEGER DEFAULT 256,
                        overlap INTEGER DEFAULT 32,
                        backend TEXT DEFAULT 'ncnn-vulkan',
                        device TEXT DEFAULT 'GPU 0',
                        runtime_s REAL,
                        peak_ram REAL,
                        peak_vram REAL,
                        sha256 TEXT,
                        quality_eval TEXT,
                        state TEXT NOT NULL DEFAULT 'ready',
                        decision TEXT NOT NULL DEFAULT 'accepted',
                        created_at REAL NOT NULL,
                        FOREIGN KEY (project_id) REFERENCES projects(id)
                    );
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS stages (
                        stage_id TEXT PRIMARY KEY,
                        job_id TEXT NOT NULL,
                        stage_index INTEGER NOT NULL,
                        operation TEXT NOT NULL,
                        model TEXT,
                        from_size TEXT,
                        to_size TEXT,
                        status TEXT NOT NULL,
                        tile_grid TEXT,
                        resume_state TEXT,
                        output_version_id TEXT
                    );
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS tiles (
                        stage_id TEXT NOT NULL,
                        grid_x INTEGER NOT NULL,
                        grid_y INTEGER NOT NULL,
                        status TEXT NOT NULL,
                        file_ref TEXT,
                        sha256 TEXT,
                        PRIMARY KEY (stage_id, grid_x, grid_y)
                    );
                """)

                # Step 3: Wrap legacy images and jobs into version graph
                images = conn.execute("SELECT * FROM images").fetchall()
                for img in images:
                    proj_id = f"proj_{img['id']}"
                    # Check if project already exists
                    has_proj = conn.execute("SELECT id FROM projects WHERE id = ?", (proj_id,)).fetchone()
                    if not has_proj:
                        conn.execute("""
                            INSERT INTO projects (id, name, source_image_id, created_at, settings)
                            VALUES (?, ?, ?, ?, '{}')
                        """, (proj_id, img["original_filename"], img["id"], img["created_at"]))

                    orig_ver_id = f"v_orig_{img['id']}"
                    has_ver = conn.execute("SELECT id FROM versions WHERE id = ?", (orig_ver_id,)).fetchone()
                    if not has_ver:
                        mp = round((img["width"] * img["height"]) / 1_000_000.0, 2)
                        conn.execute("""
                            INSERT INTO versions (
                                id, parent_version_id, project_id, storage_ref,
                                width, height, megapixels, pixel_format, bit_depth,
                                has_alpha, operation, state, decision, created_at
                            ) VALUES (?, NULL, ?, ?, ?, ?, ?, ?, 8, 0, 'original', 'ready', 'accepted', ?)
                        """, (orig_ver_id, proj_id, img["storage_path"], img["width"], img["height"], mp, img["format"], img["created_at"]))

                # Wrap completed jobs as child versions
                jobs = conn.execute("SELECT * FROM jobs WHERE status = 'completed' AND output_path IS NOT NULL").fetchall()
                for j in jobs:
                    ver_id = f"v_job_{j['id']}"
                    has_ver = conn.execute("SELECT id FROM versions WHERE id = ?", (ver_id,)).fetchone()
                    if not has_ver and os.path.isfile(j["output_path"]):
                        proj_id = f"proj_{j['image_id']}"
                        parent_ver_id = f"v_orig_{j['image_id']}"
                        scale = j["scale"] or 4
                        # Extract dimensions or compute
                        img_row = conn.execute("SELECT width, height FROM images WHERE id = ?", (j["image_id"],)).fetchone()
                        w = (img_row["width"] * scale) if img_row else 1024
                        h = (img_row["height"] * scale) if img_row else 1024
                        mp = round((w * h) / 1_000_000.0, 2)
                        conn.execute("""
                            INSERT INTO versions (
                                id, parent_version_id, project_id, storage_ref,
                                width, height, megapixels, pixel_format, bit_depth,
                                has_alpha, operation, mode, model_id, state, decision, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'RGB', 8, 0, 'upscale', ?, ?, 'ready', 'accepted', ?)
                        """, (ver_id, parent_ver_id, proj_id, j["output_path"], w, h, mp, j["mode"], j["model"], j["updated_at"]))

                conn.execute("INSERT OR REPLACE INTO schema_version (version, applied_at) VALUES (2, ?)", (time.time(),))
                conn.commit()
                print("Database migrated successfully to Version Graph schema v2.")

        finally:
            conn.close()

migration_service = MigrationService()

