from typing import Dict, Any, List, Optional
from backend.app.database import get_version
from backend.app.services.resource_estimator import resource_estimator

class ResolutionPlanner:
    """
    Computes intelligent resolution plans (Plans A, B, C) per Part F:
    - Plan A: Direct from earliest ancestor (Single-pass, high faithfulness)
    - Plan B: Progressive continuation from current version (with same-model-repeat guards)
    - Plan C: Traditional anti-aliased resampling (No invented detail)
    """

    @staticmethod
    def get_root_ancestor(version_id: str) -> Dict[str, Any]:
        """Walks up the version graph to the root original ancestor."""
        cur = get_version(version_id)
        if not cur:
            raise ValueError(f"Version {version_id} not found.")
        while cur.get("parent_version_id"):
            parent = get_version(cur["parent_version_id"])
            if not parent:
                break
            cur = parent
        return cur

    @classmethod
    def create_plan(
        cls,
        version_id: str,
        target_w: int,
        target_h: int,
        preferred_model: str = "realesrgan-x4plus",
        allow_same_model_repeat: bool = False
    ) -> Dict[str, Any]:
        cur_ver = get_version(version_id)
        if not cur_ver:
            raise ValueError(f"Version {version_id} not found.")

        src_w, src_h = cur_ver["width"], cur_ver["height"]
        src_aspect = src_w / max(1, src_h)
        target_aspect = target_w / max(1, target_h)

        if abs(src_aspect - target_aspect) > 0.05:
            raise ValueError(
                f"Target aspect ratio ({target_w}x{target_h}) does not match source "
                f"({src_w}x{src_h}). Aspect ratio distortion is prohibited per Part A3.11."
            )

        linear_scale = target_w / src_w
        root_ver = cls.get_root_ancestor(version_id)
        root_w, root_h = root_ver["width"], root_ver["height"]
        root_linear_scale = target_w / root_w

        plans = []

        # --- Plan A: Direct from best ancestor (Default Recommendation) ---
        # If reachable from original in a single 4x pass
        is_plan_a_single_pass = abs(root_linear_scale - 4.0) < 0.05
        plan_a_est = resource_estimator.estimate(root_w, root_h, target_w, target_h, preferred_model)
        plans.append({
            "plan_type": "A",
            "name": "Direct from Original (Recommended Faithful Path)",
            "description": f"Upscales directly from the original source ({root_w}x{root_h}) in a single neural pass.",
            "source_version_id": root_ver["id"],
            "source_dimensions": [root_w, root_h],
            "target_dimensions": [target_w, target_h],
            "scale_factor": round(root_linear_scale, 2),
            "stages": [
                {
                    "stage_index": 1,
                    "operation": "upscale",
                    "model": preferred_model,
                    "input_size": [root_w, root_h],
                    "output_size": [target_w, target_h]
                }
            ],
            "recommended": True,
            "resource_estimate": plan_a_est
        })

        # --- Plan B: Continue from selected version (Flagship 4K->8K) ---
        same_model_repeated = (cur_ver.get("model_id") == preferred_model)
        plan_b_warning = None
        if same_model_repeated and not allow_same_model_repeat:
            plan_b_warning = (
                "Notice: Applying the same neural model to an already-upscaled image "
                "yields diminishing returns and may exaggerate hallucinated textures. "
                "Explicit confirmation required."
            )

        # Handle 4K -> 8K (linear_scale == 2.0)
        # Uses Per-Tile Scale Adaptation (F4 #2)
        plan_b_est = resource_estimator.estimate(src_w, src_h, target_w, target_h, preferred_model)
        plans.append({
            "plan_type": "B",
            "name": "Continue from Selected Version (Progressive Continuation)",
            "description": f"Continues from current version ({src_w}x{src_h}) without re-uploading.",
            "source_version_id": cur_ver["id"],
            "source_dimensions": [src_w, src_h],
            "target_dimensions": [target_w, target_h],
            "scale_factor": round(linear_scale, 2),
            "same_model_repeated": same_model_repeated,
            "warning": plan_b_warning,
            "stages": [
                {
                    "stage_index": 1,
                    "operation": "per_tile_scale_adaptation" if abs(linear_scale - 2.0) < 0.05 else "upscale",
                    "model": preferred_model,
                    "input_size": [src_w, src_h],
                    "output_size": [target_w, target_h]
                }
            ],
            "recommended": False if is_plan_a_single_pass and cur_ver["id"] != root_ver["id"] else True,
            "resource_estimate": plan_b_est
        })

        # --- Plan C: Traditional / Classical Resample ---
        plan_c_est = resource_estimator.estimate(src_w, src_h, target_w, target_h, "classical")
        plans.append({
            "plan_type": "C",
            "name": "Traditional Resample (No Invented Detail)",
            "description": "High-fidelity Lanczos anti-aliased interpolation. Preserves pure source data without neural hallucination.",
            "source_version_id": cur_ver["id"],
            "source_dimensions": [src_w, src_h],
            "target_dimensions": [target_w, target_h],
            "scale_factor": round(linear_scale, 2),
            "stages": [
                {
                    "stage_index": 1,
                    "operation": "classical_resample",
                    "model": "lanczos",
                    "input_size": [src_w, src_h],
                    "output_size": [target_w, target_h]
                }
            ],
            "recommended": False,
            "resource_estimate": plan_c_est
        })

        return {
            "source_version_id": version_id,
            "target_dimensions": [target_w, target_h],
            "linear_scale": round(linear_scale, 2),
            "plans": plans
        }

    @classmethod
    def generate_plan(
        cls,
        project_id: str,
        source_version_id: str,
        target_width: int,
        target_height: int,
        preset: Optional[str] = None,
        preferred_model: Optional[str] = None,
        plan_choice: Optional[str] = None
    ) -> Dict[str, Any]:
        """Convenience method returning selected executable plan with full engine metadata."""
        from backend.app.services.preset_service import preset_service
        resolved_preset = preset_service.get_preset(preset)
        chosen_model = preferred_model or resolved_preset.get("model", "realesrgan-x4plus")
        blend_weight = resolved_preset.get("texture_blend_weight", 0.0)

        res = cls.create_plan(
            version_id=source_version_id,
            target_w=target_width,
            target_h=target_height,
            preferred_model=chosen_model
        )
        root_ancestor = cls.get_root_ancestor(source_version_id)
        is_orig = (root_ancestor["id"] == source_version_id)
        plan_a = next((p for p in res["plans"] if p["plan_type"] == "A"), res["plans"][0])
        plan_b = next((p for p in res["plans"] if p["plan_type"] == "B"), plan_a)
        plan_c = next((p for p in res["plans"] if p["plan_type"] == "C"), plan_b)

        if plan_choice:
            req_type = plan_choice.strip().upper()[-1]
            matched = [p for p in res["plans"] if p["plan_type"].upper() == req_type]
            chosen = matched[0] if matched else (plan_a if is_orig else plan_b)
        else:
            chosen = plan_a if is_orig else plan_b

        stages = []
        for s in chosen["stages"]:
            is_classical = (s["operation"] == "classical_resample")
            stages.append({
                "stage_index": s["stage_index"],
                "operation": s["operation"],
                "model_name": s["model"],
                "from_res": s["input_size"],
                "to_res": s["output_size"],
                "model_scale": 1 if is_classical else 4,
                "target_scale": float(s["output_size"][0]) / float(s["input_size"][0])
            })

        warnings = []
        if chosen.get("warning"):
            warnings.append(chosen["warning"])

        plan_type_slug = f"plan_{chosen['plan_type'].lower()}"

        return {
            "project_id": project_id,
            "source_version_id": source_version_id,
            "target_width": target_width,
            "target_height": target_height,
            "plan_type": plan_type_slug,
            "name": chosen["name"],
            "stages": stages,
            "warnings": warnings,
            "resource_estimate": chosen["resource_estimate"],
            "all_plans": res["plans"],
            "preset": preset or "natural",
            "texture_blend_weight": blend_weight,
            "manga_clean_ink": resolved_preset.get("manga_clean_ink", False),
            "outline_engine": resolved_preset.get("outline_engine", False),
            "outline_strength": resolved_preset.get("outline_strength", 1.0),
            "clean_paper": resolved_preset.get("clean_paper", True),
            "deep_ink": resolved_preset.get("deep_ink", True),
            "protect_screentones": resolved_preset.get("protect_screentones", True),
            "neutralize_chromatic": resolved_preset.get("neutralize_chromatic", True)
        }

resolution_planner = ResolutionPlanner()
