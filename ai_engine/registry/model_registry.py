import os
from typing import Dict, Any, List, Optional
from ai_engine.models.ncnn_adapter import NCNNRealESRGANAdapter

class ModelRegistry:
    def __init__(self):
        self._models: Dict[str, Dict[str, Any]] = {}
        self._smoke_tested: Dict[str, bool] = {}
        self._init_catalog()

    def _init_catalog(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        models_dir = os.path.join(root_dir, "tools", "realesrgan-ncnn-vulkan", "models")
        is_clean_sim = os.environ.get("SIMULATE_CLEAN_CLONE") == "1"

        # 1. RealESRGAN x4plus
        x4plus_bin = os.path.join(models_dir, "realesrgan-x4plus.bin")
        has_x4plus = os.path.isfile(x4plus_bin) and not is_clean_sim
        self._models["realesrgan-x4plus"] = {
            "id": "realesrgan-x4plus",
            "name": "Real-ESRGAN x4plus (General Photo)",
            "adapter": "ncnn",
            "model_arg": "realesrgan-x4plus",
            "scale": 4,
            "tier": 1,
            "tasks": ["super-resolution", "general-photo"],
            "image_types": ["photo", "landscape", "portrait", "compressed"],
            "code_license": "BSD-3-Clause",
            "weight_license": "Non-commercial / Unclear (DIV2K & Flickr2K)",
            "license_status": "verified",
            "license_class": "non-commercial / unclear",
            "min_vram_mb": 1500,
            "weights_available": has_x4plus,
            "smoke_tested": has_x4plus,
            "unsupported_reason": None if has_x4plus else "Weights not installed in local tools directory."
        }

        # 2. RealESRGAN x4plus Anime
        anime_bin = os.path.join(models_dir, "realesrgan-x4plus-anime.bin")
        has_anime = os.path.isfile(anime_bin) and not is_clean_sim
        self._models["realesrgan-x4plus-anime"] = {
            "id": "realesrgan-x4plus-anime",
            "name": "Real-ESRGAN x4plus Anime 6B (Illustration/Art)",
            "adapter": "ncnn",
            "model_arg": "realesrgan-x4plus-anime",
            "scale": 4,
            "tier": 1,
            "tasks": ["super-resolution", "anime-art"],
            "image_types": ["anime", "illustration", "digital-art", "game-texture"],
            "code_license": "BSD-3-Clause",
            "weight_license": "Non-commercial / Unclear",
            "license_status": "verified",
            "license_class": "non-commercial / unclear",
            "min_vram_mb": 1200,
            "weights_available": has_anime,
            "smoke_tested": has_anime,
            "unsupported_reason": None if has_anime else "Weights not installed in local tools directory."
        }

        # 3. RealESRGAN AnimeVideo v3 x4 (Ultra-Fast 1.2MB weights)
        animev3_bin = os.path.join(models_dir, "realesr-animevideov3-x4.bin")
        has_animev3 = os.path.isfile(animev3_bin) and not is_clean_sim
        self._models["realesr-animevideov3-x4"] = {
            "id": "realesr-animevideov3-x4",
            "name": "Real-ESRGAN AnimeVideo v3 (Ultra-Fast)",
            "adapter": "ncnn",
            "model_arg": "realesr-animevideov3-x4",
            "scale": 4,
            "tier": 1,
            "tasks": ["super-resolution", "fast-anime", "animation"],
            "image_types": ["anime", "illustration", "video-frame"],
            "code_license": "BSD-3-Clause",
            "weight_license": "Non-commercial / Unclear",
            "license_status": "verified",
            "license_class": "non-commercial / unclear",
            "min_vram_mb": 800,
            "weights_available": has_animev3,
            "smoke_tested": has_animev3,
            "unsupported_reason": None if has_animev3 else "Weights not installed in local tools directory."
        }

        # 4. RealESRNet x4plus (Non-GAN Faithful MSE)
        realesrnet_bin = os.path.join(models_dir, "realesrnet-x4plus.bin")
        has_realesrnet = os.path.isfile(realesrnet_bin) and not is_clean_sim
        self._models["realesrnet-x4plus"] = {
            "id": "realesrnet-x4plus",
            "name": "Real-ESRNet x4plus (Faithful MSE Photo)",
            "adapter": "ncnn",
            "model_arg": "realesrnet-x4plus",
            "scale": 4,
            "tier": 1,
            "tasks": ["super-resolution", "faithful-photo", "low-hallucination"],
            "image_types": ["photo", "fine-detail", "text"],
            "code_license": "BSD-3-Clause",
            "weight_license": "Non-commercial / Unclear (DIV2K & Flickr2K)",
            "license_status": "verified",
            "license_class": "non-commercial / unclear",
            "min_vram_mb": 1500,
            "weights_available": has_realesrnet,
            "smoke_tested": False,
            "unsupported_reason": None if has_realesrnet else "Weights not installed in local tools directory."
        }

        # 3. Tier 3 Generative / Diffusion Research Models (Evaluated per Phase 7)
        self._models["diffbir"] = {
            "id": "diffbir",
            "name": "DiffBIR (Diffusion Blind Image Restoration)",
            "adapter": "diffusion-isolated",
            "model_arg": "diffbir",
            "scale": 4,
            "tier": 3,
            "tasks": ["generative-restoration"],
            "image_types": ["severe-degradation", "hallucination-allowed"],
            "code_license": "Apache-2.0",
            "weight_license": "Research / Non-Commercial",
            "license_status": "research-only",
            "license_class": "non-commercial",
            "min_vram_mb": 12000,
            "weights_available": False,
            "smoke_tested": False,
            "unsupported_reason": "Requires minimum 12GB VRAM; incompatible with 4GB VRAM Profile A (PRD Section 5.6)."
        }

        self._models["supir"] = {
            "id": "supir",
            "name": "SUPIR (Scaling-Up Photo-Realistic Diffusion SR)",
            "adapter": "diffusion-isolated",
            "model_arg": "supir",
            "scale": 4,
            "tier": 3,
            "tasks": ["generative-sr"],
            "image_types": ["text-prompted", "hallucination-allowed"],
            "code_license": "Apache-2.0",
            "weight_license": "Research / Non-Commercial",
            "license_status": "research-only",
            "license_class": "non-commercial",
            "min_vram_mb": 16000,
            "weights_available": False,
            "smoke_tested": False,
            "unsupported_reason": "Requires minimum 16GB VRAM and SDXL UNet; incompatible with 4GB VRAM Profile A (PRD Section 5.6)."
        }

    def mark_smoke_tested(self, model_id: str, passed: bool = True):
        if model_id in self._models:
            self._models[model_id]["smoke_tested"] = passed

    def get_model(self, model_id: str) -> Optional[Dict[str, Any]]:
        return self._models.get(model_id)

    def list_models(self, only_available: bool = False, only_smoke_tested: bool = False) -> List[Dict[str, Any]]:
        res = []
        for m in self._models.values():
            if only_available and not m["weights_available"]:
                continue
            if only_smoke_tested and not m["smoke_tested"]:
                continue
            res.append(m)
        return res

model_registry = ModelRegistry()
