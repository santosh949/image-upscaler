import subprocess
import sys
import os
import time
import threading
from typing import Dict, Optional, List, Any
from backend.app.core.config import settings
from backend.app.database import (
    update_job_status, get_job, get_stages_for_job,
    get_next_queued_job, get_queued_jobs
)

class JobManager:
    def __init__(self):
        self.active_processes: Dict[str, subprocess.Popen] = {}
        self.control_dir = os.path.join(settings.STORAGE_PATH, "control")
        os.makedirs(self.control_dir, exist_ok=True)
        self._lock = threading.Lock()
        self._dispatcher_running = False
        self._dispatcher_thread: Optional[threading.Thread] = None

    def start_dispatcher(self) -> None:
        with self._lock:
            if self._dispatcher_running:
                return
            self._dispatcher_running = True
            self._dispatcher_thread = threading.Thread(target=self._dispatch_loop, daemon=True)
            self._dispatcher_thread.start()

    def stop_dispatcher(self) -> None:
        with self._lock:
            self._dispatcher_running = False

    def _dispatch_loop(self) -> None:
        while self._dispatcher_running:
            try:
                self._check_and_dispatch()
            except Exception as e:
                print(f"Queue Dispatcher Warning: {e}", file=sys.stderr)
            time.sleep(0.5)

    def _check_and_dispatch(self) -> None:
        with self._lock:
            # Clean up finished/exited processes
            finished = []
            for jid, proc in list(self.active_processes.items()):
                if proc.poll() is not None:
                    finished.append(jid)
            for jid in finished:
                self.active_processes.pop(jid, None)

            # Sequential single GPU worker guarantee (Profile A / VRAM safety)
            if len(self.active_processes) == 0:
                next_job = get_next_queued_job()
                if next_job:
                    jid = next_job["id"]
                    self._spawn_worker_internal(jid)

    def _get_pause_file(self, job_id: str) -> str:
        return os.path.join(self.control_dir, f"{job_id}.pause")

    def _get_cancel_file(self, job_id: str) -> str:
        return os.path.join(self.control_dir, f"{job_id}.cancel")

    def is_paused(self, job_id: str) -> bool:
        return os.path.exists(self._get_pause_file(job_id))

    def is_cancelled(self, job_id: str) -> bool:
        return os.path.exists(self._get_cancel_file(job_id))

    def _spawn_worker_internal(self, job_id: str) -> None:
        cmd = [sys.executable, "-m", "backend.app.workers.job_worker", job_id]
        worker_env = os.environ.copy()
        worker_env["DATABASE_PATH"] = str(settings.DATABASE_PATH)
        proc = subprocess.Popen(
            cmd,
            env=worker_env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        self.active_processes[job_id] = proc

    def spawn_worker(self, job_id: str) -> None:
        """Enqueues and ensures dispatcher runs."""
        self.start_dispatcher()
        # Immediate dispatch check
        self._check_and_dispatch()

    def get_queue_status(self) -> Dict[str, Any]:
        with self._lock:
            active_ids = list(self.active_processes.keys())
            queued_rows = get_queued_jobs()
            return {
                "active_job_id": active_ids[0] if active_ids else None,
                "active_count": len(active_ids),
                "total_queued": len(queued_rows),
                "queue": queued_rows
            }

    def pause_job(self, job_id: str) -> bool:
        """Sets pause flag so worker exits cleanly after current tile."""
        job = get_job(job_id)
        if not job or job["status"] not in ("processing", "queued"):
            return False

        pause_file = self._get_pause_file(job_id)
        with open(pause_file, "w") as f:
            f.write("pause")

        proc = self.active_processes.get(job_id)
        if proc:
            # Give worker 2 seconds to complete tile and exit cleanly
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                proc.terminate()
            self.active_processes.pop(job_id, None)

        update_job_status(job_id, status="paused", stage="paused", message="Job paused at tile checkpoint")
        return True

    def resume_job(self, job_id: str) -> bool:
        """Removes pause flag and re-spawns worker from saved checkpoint."""
        job = get_job(job_id)
        if not job or job["status"] != "paused":
            return False

        pause_file = self._get_pause_file(job_id)
        if os.path.exists(pause_file):
            try:
                os.remove(pause_file)
            except Exception:
                pass

        update_job_status(job_id, status="queued", stage="resumed", message="Resumed from checkpoint, queued for execution...")
        self.spawn_worker(job_id)
        return True

    def cancel_job(self, job_id: str) -> bool:
        cancel_file = self._get_cancel_file(job_id)
        with open(cancel_file, "w") as f:
            f.write("cancel")

        pause_file = self._get_pause_file(job_id)
        if os.path.exists(pause_file):
            try:
                os.remove(pause_file)
            except Exception:
                pass

        proc = self.active_processes.get(job_id)
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                proc.kill()
            self.active_processes.pop(job_id, None)

        # Cleanup output if partial
        job = get_job(job_id)
        if job and job.get("output_path") and os.path.isfile(job["output_path"]):
            try:
                os.remove(job["output_path"])
            except Exception:
                pass

        update_job_status(job_id, status="cancelled", stage="cancelled", message="Job cancelled by user")

        if os.path.exists(cancel_file):
            try:
                os.remove(cancel_file)
            except Exception:
                pass
        return True

    def get_stages(self, job_id: str) -> List[Dict[str, Any]]:
        return get_stages_for_job(job_id)

job_manager = JobManager()
