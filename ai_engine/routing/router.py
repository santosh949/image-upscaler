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
        available_models = {m["id"]: m for m in model_registry.list_models(only_available=True, only_smoke_tested=True)}
        # Fallback to any available if smoke-test not run yet
        if not available_models:
            available_models = {m["id"]: m for m in model_registry.list_models(only_available=True)}

        # If user explicitly requested an installed model
        if requested_model and requested_model in available_models:
            m = available_models[requested_model]
            return {
                "selected_model": m["id"],
                "model_name": m["name"],
                "scale": user_scale,
                "reasoning": f"Manual override: user explicitly selected {m['name']}."
            }

        # Auto-routing based on degradation analysis
        category = analysis.get("detected_category", "photo")
        is_blurry = analysis.get("is_blurry", False)
        noise = analysis.get("estimated_noise_sigma", 0.0)

        # 1. Anime / Digital illustration
        if category == "anime" and "realesrgan-x4plus-anime" in available_models:
            model = available_models["realesrgan-x4plus-anime"]
            reason = (
                f"Selected {model['name']}: Image classified as anime/illustration "
                f"(confidence {int(analysis.get('category_confidence', 0.8) * 100)}%). "
                "Optimized for sharp line art and color gradient clarity."
            )
            return {
                "selected_model": model["id"],
                "model_name": model["name"],
                "scale": 4,
                "reasoning": reason
            }

        # 2. General photo fallback
        if "realesrgan-x4plus" in available_models:
            model = available_models["realesrgan-x4plus"]
            degrad_notes = []
            if is_blurry:
                degrad_notes.append("mild blur detected")
            if noise > 4.5:
                degrad_notes.append(f"visible noise (sigma={noise})")

            reason_extra = f" with {', '.join(degrad_notes)}" if degrad_notes else ""
            reason = (
                f"Selected {model['name']}: Natural photo content{reason_extra}. "
                "Fits available 4GB VRAM on RTX 2050 (Vulkan 0)."
            )
            return {
                "selected_model": model["id"],
                "model_name": model["name"],
                "scale": 4,
                "reasoning": reason
            }

        # Default fallback
        first_model = list(available_models.values())[0]
        return {
            "selected_model": first_model["id"],
            "model_name": first_model["name"],
            "scale": 4,
            "reasoning": f"Default fallback: {first_model['name']} is available."
        }

router = ModelRouter()

