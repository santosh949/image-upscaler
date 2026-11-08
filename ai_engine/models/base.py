from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class ModelAdapter(ABC):
    """Abstract base adapter for super-resolution and restoration models."""

    @abstractmethod
    def capabilities(self) -> Dict[str, Any]:
        """Return model metadata, supported scales, tasks, and requirements."""
        pass

    @abstractmethod
    def load(self, device: str = "cuda", precision: str = "fp16") -> None:
        """Prepare model for inference."""
        pass

    @abstractmethod
    def enhance(
        self,
        input_path: str,
        output_path: str,
        scale: int = 4,
        tile_size: int = 0,
        gpu_id: int = 0,
        cancel_token: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Run inference on input image file and write to output_path.
        Returns execution metadata (runtime, dimensions, backend).
        """
        pass

    @abstractmethod
    def unload(self) -> None:
        """Release GPU and memory resources."""
        pass

