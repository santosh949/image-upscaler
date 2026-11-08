import json
from datetime import datetime, timezone
from PIL import Image, PngImagePlugin
from typing import Dict, Any, Optional

class MetadataEmbedder:
    """
    Embeds provenance and execution audit trails into image headers.
    Ensures full transparency regarding models, processing stages, and license classes.
    """

    @staticmethod
    def build_provenance_dict(
        mode: str,
        model_name: str,
        scale: int,
        stages: list,
        hardware: str = "NVIDIA GeForce RTX 2050 (Vulkan GPU 0)",
        license_class: str = "non-commercial / research",
        consistency: Optional[Dict[str, Any]] = None
    ) -> Dict[str, str]:
        info = {
            "Aether-Software": "AETHER UPSCALE v1.0.0",
            "Aether-Mode": mode,
            "Aether-Model": model_name,
            "Aether-Scale": f"{scale}x",
            "Aether-Stages": ", ".join(stages),
            "Aether-Hardware": hardware,
            "Aether-License": license_class,
            "Aether-Timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if consistency:
            info["Aether-Consistency-PSNR"] = f"{consistency.get('psnr_db', 0)} dB"
            info["Aether-Consistency-MAE"] = str(consistency.get('mae', 0))
        return info

    @classmethod
    def embed_provenance(cls, img: Image.Image, meta_dict: Dict[str, Any]) -> Image.Image:
        """Attaches provenance metadata dictionary to image object."""
        png_info = PngImagePlugin.PngInfo()
        for k, v in meta_dict.items():
            png_info.add_text(k, str(v))
            img.info[k] = str(v)
        img.info["pnginfo"] = png_info
        return img

    @classmethod
    def save_with_metadata(
        cls,
        img: Image.Image,
        output_path: str,
        format_name: str = "PNG",
        metadata: Optional[Dict[str, str]] = None,
        quality: int = 95
    ) -> None:
        """Saves image with embedded provenance metadata."""
        meta = metadata or {}
        fmt = format_name.upper()

        if fmt == "PNG":
            png_info = PngImagePlugin.PngInfo()
            for k, v in meta.items():
                png_info.add_text(k, str(v))
            img.save(output_path, format="PNG", pnginfo=png_info)
        elif fmt in ("JPEG", "JPG"):
            rgb_img = img.convert("RGB")
            rgb_img.save(output_path, format="JPEG", quality=quality, optimize=True)
        elif fmt == "WEBP":
            img.save(output_path, format="WEBP", quality=quality)
        else:
            img.save(output_path, format=fmt)

        # Write sidecar provenance JSON manifest for all formats (PNG, JPEG, WebP per V3 Addendum §1.7)
        sidecar_path = f"{output_path}.manifest.json"
        try:
            with open(sidecar_path, "w", encoding="utf-8") as sf:
                json.dump(meta, sf, indent=2)
        except Exception:
            pass

