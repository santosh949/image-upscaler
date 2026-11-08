"""
AETHER UPSCALE — Automated Environment & Model Weights Setup Script
Downloads official Real-ESRGAN NCNN Vulkan binary and models for Windows, Linux, and macOS.
"""

import os
import sys
import platform
import zipfile
import urllib.request
import shutil

SYSTEM_NAME = platform.system().lower()
if "windows" in SYSTEM_NAME:
    ZIP_NAME = "realesrgan-ncnn-vulkan-20220424-windows.zip"
    BINARY_NAME = "realesrgan-ncnn-vulkan.exe"
elif "darwin" in SYSTEM_NAME:
    ZIP_NAME = "realesrgan-ncnn-vulkan-20220424-macos.zip"
    BINARY_NAME = "realesrgan-ncnn-vulkan"
else:
    ZIP_NAME = "realesrgan-ncnn-vulkan-20220424-ubuntu.zip"
    BINARY_NAME = "realesrgan-ncnn-vulkan"

NCNN_ZIP_URL = f"https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.5.0/{ZIP_NAME}"
TOOLS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "tools", "realesrgan-ncnn-vulkan"))
WEIGHTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "weights"))
STORAGE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "storage"))

def setup():
    print("==================================================")
    print("   AETHER UPSCALE — Automated Environment Setup   ")
    print("==================================================")
    print(f"Detected Platform: {platform.system()} ({platform.machine()})")

    # 1. Ensure storage subdirectories
    for sub in ["uploads", "outputs", "previews", "temp", "control"]:
        d = os.path.join(STORAGE_DIR, sub)
        os.makedirs(d, exist_ok=True)
        gitkeep = os.path.join(d, ".gitkeep")
        if not os.path.exists(gitkeep):
            with open(gitkeep, "w") as f:
                pass
    print("✔ Storage directories initialized.")

    os.makedirs(TOOLS_DIR, exist_ok=True)
    os.makedirs(WEIGHTS_DIR, exist_ok=True)

    exe_path = os.path.join(TOOLS_DIR, BINARY_NAME)
    if os.path.isfile(exe_path):
        print(f"✔ Real-ESRGAN NCNN Vulkan binary already present: {exe_path}")
        return

    # 2. Download official NCNN release
    temp_zip = os.path.join(TOOLS_DIR, "ncnn_release.zip")
    print(f"Downloading official Real-ESRGAN NCNN Vulkan release for {platform.system()}...")
    print(f"Source: {NCNN_ZIP_URL}")

    try:
        def progress(count, block_size, total_size):
            if total_size > 0:
                pct = int(count * block_size * 100 / total_size)
                sys.stdout.write(f"\rDownloading: {pct}%")
                sys.stdout.flush()

        urllib.request.urlretrieve(NCNN_ZIP_URL, temp_zip, progress)
        print("\n✔ Download complete. Extracting files...")

        with zipfile.ZipFile(temp_zip, "r") as z:
            for member in z.infolist():
                filename = os.path.basename(member.filename)
                if not filename:
                    continue
                # Extract exe, dll, so, dylib, and models into tools dir
                target_path = os.path.join(TOOLS_DIR, filename)
                with z.open(member) as source, open(target_path, "wb") as target:
                    shutil.copyfileobj(source, target)
                
                # Copy model files to weights/
                if filename.endswith(".bin") or filename.endswith(".param"):
                    shutil.copy(target_path, os.path.join(WEIGHTS_DIR, filename))

        if os.path.exists(temp_zip):
            os.remove(temp_zip)

        if os.path.isfile(exe_path) and not sys.platform.startswith("win"):
            os.chmod(exe_path, 0o755)

        print(f"✔ Successfully installed Real-ESRGAN NCNN Vulkan binaries and weights.")
        print("Setup complete! You can now start the server:")
        print("  python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000")

    except Exception as e:
        print(f"\n❌ Error during download/extraction: {e}")
        print("Please download manually from:")
        print(f"  {NCNN_ZIP_URL}")
        print(f"and place files into {TOOLS_DIR}")

if __name__ == "__main__":
    setup()

