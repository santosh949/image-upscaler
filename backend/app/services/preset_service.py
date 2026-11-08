import os
import yaml
from typing import Dict, Any, Optional

class PresetService:
    """
    Loads authoritative presets configuration (Part K4 & V3 Addendum §6).
    Couples plain-language presets to concrete backend execution parameters.
    """

    def __init__(self, config_path: Optional[str] = None):
        if not config_path:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            config_path = os.path.join(base_dir, "core", "presets.yaml")
        self.config_path = config_path
        self._presets: Dict[str, Any] = {}
        self.load_presets()

    def load_presets(self) -> None:
        if os.path.isfile(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                self._presets = data.get("presets", {})

    def list_presets(self) -> Dict[str, Any]:
        return self._presets

    def get_preset(self, preset_id: Optional[str]) -> Dict[str, Any]:
        if not preset_id or preset_id not in self._presets:
            preset_id = "natural"
        return self._presets[preset_id].copy()

    def resolve(self, preset_id: Optional[str], overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        preset = self.get_preset(preset_id)
        if overrides:
            for k, v in overrides.items():
                if v is not None:
                    preset[k] = v
        return preset

preset_service = PresetService()

