import os
import yaml
from pathlib import Path
from typing import Optional

class Config:
    def __init__(self):
        self.memory_root = self._get_memory_root()
        self.memories_dir = self.memory_root / "memories"
        self.index_path = self.memory_root / "index.yaml"
        self.config_path = self.memory_root / "config.yaml"
        self.logs_dir = self.memory_root / "logs"

        self._ensure_directories()

    def _get_memory_root(self) -> Path:
        # Priority: Env var -> config.yaml (if exists) -> default
        env_root = os.environ.get("MEMORY_ROOT")
        if env_root:
            return Path(env_root).resolve()
        
        # Default to current directory if not specified
        return Path.cwd().resolve()

    def _ensure_directories(self):
        self.memories_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def load_config_file(self) -> dict:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f) or {}
            except Exception:
                return {}
        return {}

config = Config()
