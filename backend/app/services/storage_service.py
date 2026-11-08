import os
import stat
import json
import shutil
import hashlib
from typing import Dict, Any, Optional, Callable
from PIL import Image

from backend.app.core.config import settings

class StorageService:
    """
    Manages immutable artifact storage, atomic file operations,
    cryptographic SHA-256 verification, and startup orphan reconciliation per Part E.
    """

    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = root_dir or settings.STORAGE_ROOT
        self.versions_dir = os.path.join(self.root_dir, "versions")
        self.manifests_dir = os.path.join(self.root_dir, "manifests")
        self.tiles_dir = os.path.join(self.root_dir, "tiles")
        self.temp_dir = os.path.join(self.root_dir, "temp")
        self.previews_dir = os.path.join(self.root_dir, "previews")
        self.uploads_dir = os.path.join(self.root_dir, "uploads")
        self._ensure_directories()

    def _ensure_directories(self):
        for d in (self.versions_dir, self.manifests_dir, self.tiles_dir,
                  self.temp_dir, self.previews_dir, self.uploads_dir):
            os.makedirs(d, exist_ok=True)

    @staticmethod
    def compute_sha256(file_path: str) -> str:
        h = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()

    def check_disk_space(self, estimated_bytes: int) -> bool:
        """Enforces Part C3: free disk >= required * 1.25."""
        usage = shutil.disk_usage(self.root_dir)
        required = estimated_bytes * 1.25
        if usage.free < required:
            raise RuntimeError(
                f"Insufficient disk space: {usage.free / (1024**2):.1f} MB free, "
                f"requires {required / (1024**2):.1f} MB (including 25% safety margin)."
            )
        return True

    def write_atomic_image(
        self,
        target_path: str,
        image_obj: Image.Image,
        format_name: str = "PNG",
        quality: int = 95
    ) -> str:
        """
        Atomic Write Protocol (Part C2.7 & E2.3):
        1. Write to *.partial
        2. Flush & fsync
        3. Compute SHA256
        4. Atomic rename via os.replace
        5. Set read-only
        """
        os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
        partial_path = f"{target_path}.partial"

        if os.path.exists(partial_path):
            try:
                os.remove(partial_path)
            except Exception:
                pass

        # Write to partial file
        with open(partial_path, "wb") as f:
            if format_name.upper() == "PNG":
                image_obj.save(f, format="PNG")
            elif format_name.upper() in ("JPG", "JPEG"):
                image_obj.convert("RGB").save(f, format="JPEG", quality=quality)
            elif format_name.upper() == "WEBP":
                image_obj.save(f, format="WEBP", quality=quality)
            else:
                image_obj.save(f, format=format_name)
            f.flush()
            os.fsync(f.fileno())

        # Compute hash
        sha256_hash = self.compute_sha256(partial_path)

        # Atomic move
        os.replace(partial_path, target_path)

        # Invariant E2.1: Mark file read-only once ready
        try:
            os.chmod(target_path, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)
        except Exception:
            pass

        return sha256_hash

    def write_manifest(self, version_id: str, manifest_data: Dict[str, Any]) -> str:
        """Writes authoritative provenance manifest JSON (Part E4)."""
        manifest_path = os.path.join(self.manifests_dir, f"{version_id}.json")
        partial_path = f"{manifest_path}.partial"

        with open(partial_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f, indent=2)
            f.flush()
            os.fsync(f.fileno())

        os.replace(partial_path, manifest_path)
        return manifest_path

    def reconcile_startup(self, verify_version_fn: Optional[Callable[[str], bool]] = None) -> Dict[str, int]:
        """
        Startup Reconciliation (Part E2.3):
        - Deletes *.partial orphans in all storage directories.
        - Never deletes valid files referenced by DB.
        """
        deleted_partials = 0
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if file.endswith(".partial"):
                    try:
                        p = os.path.join(root, file)
                        # Remove read-only attribute if set so it can be unlinked
                        os.chmod(p, stat.S_IWRITE)
                        os.remove(p)
                        deleted_partials += 1
                    except Exception:
                        pass
        return {"deleted_partials": deleted_partials}

storage_service = StorageService()

