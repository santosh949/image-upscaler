from typing import Dict, Any, Optional
from ai_engine.registry.model_registry import model_registry

class ModelRouter:
    """Intelligent degradation-aware routing engine mapping images to verified models."""

    def route(
        self,
        analysis: Dict[str, Any],
        user_mode: str = "upscale",
        user_scale: int = 4,
        requested_model: Optional[str] = None
    ) -> Dict[str, Any]:
        all_catalog = {m["id"]: m for m in model_registry.list_models(only_available=False)}
        available_models = {m["id"]: m for m in model_registry.list_models(only_available=True, only_smoke_tested=True)}
        # Fallback to any available if smoke-test not run yet
        if not available_models:
            available_models = {m["id"]: m for m in model_registry.list_models(only_available=True)}

        # Active models for decision: prefer installed, fall back gracefully to catalog
        active_models = available_models if available_models else all_catalog

        # If user explicitly requested a model
        if requested_model and requested_model in active_models:
            m = active_models[requested_model]
            has_w = m["id"] in available_models
            extra = "" if has_w else " [Notice: Weights not installed; run scripts/setup_environment.py]"
            return {
                "selected_model": m["id"],
                "model_name": m["name"],
                "scale": user_scale,
                "weights_available": has_w,
                "reasoning": f"Manual override: user explicitly selected {m['name']}.{extra}"
            }

        # Auto-routing based on degradation analysis
        category = analysis.get("detected_category", "photo")
        confidence = int(analysis.get("category_confidence", 0.8) * 100)
        is_blurry = analysis.get("is_blurry", False)
        noise = analysis.get("estimated_noise_sigma", 0.0)
        jpeg_q = analysis.get("jpeg_quality_estimate", 90)

        # Build processing parameter overrides based on degradation analysis
        recommended_params = {}
        if noise > 4.5:
            recommended_params["pre_denoise"] = "medium"
            recommended_params["denoise_strength"] = min(10.0, round(noise * 0.5, 1))
        if is_blurry:
            recommended_params["post_sharpen"] = "low"
            recommended_params["sharpen_amount"] = 0.35
        if jpeg_q < 75:
            recommended_params["deblock_jpeg"] = True

        def format_result(model: Dict[str, Any], preset: str, reason: str) -> Dict[str, Any]:
            has_w = model["id"] in available_models
            extra = "" if has_w else " [Notice: Weights not installed; run scripts/setup_environment.py]"
            res = {
                "selected_model": model["id"],
                "model_name": model["name"],
                "scale": 4,
                "preset": preset,
                "weights_available": has_w,
                "reasoning": f"{reason}{extra}"
            }
            if recommended_params:
                res["recommended_parameters"] = recommended_params
            return res

        # 1. Manga / Monochrome Line Art
        if category == "manga":
            model_key = "realesrgan-x4plus-anime" if "realesrgan-x4plus-anime" in active_models else "realesr-animevideov3-x4"
            if model_key in active_models:
                model = active_models[model_key]
                recommended_params["preset"] = "manga_crisp"
                recommended_params["outline_engine"] = True
                recommended_params["clean_paper"] = True
                recommended_params["deep_ink"] = True
                recommended_params["protect_screentones"] = True
                return format_result(
                    model,
                    "manga_crisp",
                    f"Selected {model['name']}: Detected black-and-white manga / line art "
                    f"({confidence}% confidence). Activating 4-pillar outline engine with "
                    "screentone protection and paper purification."
                )

        # 2. Anime / Digital illustration
        if category == "anime":
            model_key = "realesrgan-x4plus-anime" if "realesrgan-x4plus-anime" in active_models else "realesr-animevideov3-x4"
            if model_key in active_models:
                model = active_models[model_key]
                recommended_params["preset"] = "artwork"
                return format_result(
                    model,
                    "artwork",
                    f"Selected {model['name']}: Image classified as anime/illustration "
                    f"({confidence}% confidence). Preserving cel lines and color fills without photo smoothing."
                )

        # 3. Scanned text / Document
        if category == "document" and "realesrgan-x4plus" in active_models:
            model = active_models["realesrgan-x4plus"]
            recommended_params["preset"] = "faithful"
            return format_result(
                model,
                "faithful",
                f"Selected {model['name']}: Scanned text / document detected "
                f"({confidence}% confidence). Using faithful reconstruction without outline hallucination."
            )

        # 4. General photo fallback
        if "realesrgan-x4plus" in active_models:
            model = active_models["realesrgan-x4plus"]
            degrad_notes = []
            if is_blurry:
                degrad_notes.append("mild blur")
            if noise > 4.5:
                degrad_notes.append(f"noise (sigma={noise})")

            reason_extra = f" with {', '.join(degrad_notes)}" if degrad_notes else ""
            return format_result(
                model,
                "natural",
                f"Selected {model['name']}: Natural photo content{reason_extra}. Standard neural restoration."
            )

        # Default fallback
        first_model = list(active_models.values())[0] if active_models else list(all_catalog.values())[0]
        return format_result(
            first_model,
            "natural",
            f"Default fallback: {first_model['name']} selected."
        )

router = ModelRouter()

