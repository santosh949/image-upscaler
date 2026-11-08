import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "AETHER UPSCALE API"
    VERSION: str = "0.1.0"
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    VULKAN_DEVICE_INDEX: int = 0
    VULKAN_DEVICE_NAME: str = "NVIDIA GeForce RTX 2050"
    STORAGE_ROOT: str = "./storage"
    STORAGE_PATH: str = "./storage"
    MAX_OUTPUT_MEGAPIXELS: int = 100
    CORS_ORIGINS: List[str] = [
        "http://127.0.0.1:5173",
        "http://localhost:5173"
    ]
    DATABASE_PATH: str = "./storage/aether.db"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()

# Ensure directories exist
for sub in ["uploads", "outputs", "previews", "temp"]:
    os.makedirs(os.path.join(settings.STORAGE_ROOT, sub), exist_ok=True)
