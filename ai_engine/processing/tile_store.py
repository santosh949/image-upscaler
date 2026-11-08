import os
import shutil
import hashlib
from typing import Dict, Any, Optional, Tuple, List
from PIL import Image
from backend.app.database import get_db_connection
from backend.app.core.config import settings

class TileStore:
    """
    Manages persistent intermediate tile storage on disk and in SQLite
    for pause, resume, and checkpoint recovery.
    """

    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = base_dir or os.path.join(settings.STORAGE_PATH, "tiles")
        os.makedirs(self.base_dir, exist_ok=True)

    def get_stage_dir(self, stage_id: str) -> str:
        s_dir = os.path.join(self.base_dir, stage_id)
        os.makedirs(s_dir, exist_ok=True)
        return s_dir

    def init_stage(
        self,
        stage_id: str,
        job_id: str,
        stage_index: int,
        operation: str,
        model: str,
        from_size: Tuple[int, int],
        to_size: Tuple[int, int],
        tile_grid: List[Dict[str, Any]]
    ) -> None:
        """Initializes stage and creates pending tile tracking entries."""
        stage_dir = self.get_stage_dir(stage_id)
        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO stages (
                    stage_id, job_id, stage_index, operation, model,
                    from_size, to_size, status, tile_grid, resume_state
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                stage_id,
                job_id,
                stage_index,
                operation,
                model,
                f"{from_size[0]}x{from_size[1]}",
                f"{to_size[0]}x{to_size[1]}",
                "running",
                str(len(tile_grid)),
                None
            ))

            for idx, t in enumerate(tile_grid):
                conn.execute("""
                    INSERT OR IGNORE INTO tiles (stage_id, grid_x, grid_y, status, file_ref, sha256)
                    VALUES (?, ?, ?, 'pending', NULL, NULL)
                """, (stage_id, t.get("gx", idx), t.get("gy", 0)))
            conn.commit()

    def get_completed_tiles(self, stage_id: str) -> Dict[Tuple[int, int], str]:
        """
        Returns map of (gx, gy) -> file_path for tiles that exist on disk
        and match their recorded SHA-256 hash.
        """
        completed = {}
        with get_db_connection() as conn:
            rows = conn.execute("""
                SELECT grid_x, grid_y, file_ref, sha256
                FROM tiles
                WHERE stage_id = ? AND status = 'completed'
            """, (stage_id,)).fetchall()

            for r in rows:
                gx, gy, path, expected_hash = r["grid_x"], r["grid_y"], r["file_ref"], r["sha256"]
                if path and os.path.exists(path):
                    # Verify integrity
                    hasher = hashlib.sha256()
                    with open(path, "rb") as f:
                        for chunk in iter(lambda: f.read(65536), b""):
                            hasher.update(chunk)
                    if hasher.hexdigest() == expected_hash:
                        completed[(gx, gy)] = path
                    else:
                        # Corrupted tile, reset status
                        conn.execute("""
                            UPDATE tiles SET status = 'pending', file_ref = NULL, sha256 = NULL
                            WHERE stage_id = ? AND grid_x = ? AND grid_y = ?
                        """, (stage_id, gx, gy))
            conn.commit()
        return completed

    def save_tile(self, stage_id: str, grid_x: int, grid_y: int, tile_img: Image.Image) -> str:
        """Saves a processed tile to disk and updates SQLite record."""
        stage_dir = self.get_stage_dir(stage_id)
        filename = f"tile_{grid_x}_{grid_y}.png"
        filepath = os.path.join(stage_dir, filename)

        tile_img.save(filepath, format="PNG", compress_level=1)

        hasher = hashlib.sha256()
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        tile_hash = hasher.hexdigest()

        with get_db_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO tiles (stage_id, grid_x, grid_y, status, file_ref, sha256)
                VALUES (?, ?, ?, 'completed', ?, ?)
            """, (stage_id, grid_x, grid_y, filepath, tile_hash))
            conn.commit()

        return filepath

    def load_tile(self, filepath: str) -> Image.Image:
        """Loads tile image from disk into memory."""
        img = Image.open(filepath)
        img.load()
        return img

    def update_stage_status(self, stage_id: str, status: str, output_version_id: Optional[str] = None) -> None:
        with get_db_connection() as conn:
            conn.execute("""
                UPDATE stages
                SET status = ?, output_version_id = COALESCE(?, output_version_id)
                WHERE stage_id = ?
            """, (status, output_version_id, stage_id))
            conn.commit()

    def cleanup_stage(self, stage_id: str) -> None:
        """Cleans up on-disk tiles after stage completion or cancellation."""
        stage_dir = os.path.join(self.base_dir, stage_id)
        if os.path.exists(stage_dir):
            try:
                shutil.rmtree(stage_dir, ignore_errors=True)
            except Exception:
                pass
        with get_db_connection() as conn:
            conn.execute("DELETE FROM tiles WHERE stage_id = ?", (stage_id,))
            conn.commit()

tile_store = TileStore()

