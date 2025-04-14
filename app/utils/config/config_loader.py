import logging
from pathlib import Path
from typing import Dict, Any

import yaml

logger = logging.getLogger(__name__)  # Local module logger


class ConfigLoader:
    def __init__(self, env: str = "prod", config_filename: str = "config.yaml"):
        """
        Initialize config loader for a given environment.

        Args:
            env (str): Environment name (e.g., 'prod', 'stage', 'dev').
            config_filename (str): Configuration file name. Defaults to 'config.yaml'.
        """
        self.env = env.lower()
        self.config_filename = config_filename
        self.config_path = self._resolve_path()

    def _resolve_path(self) -> Path:
        """
        Resolve full path to YAML config based on environment.

        Returns:
            Path: Path object pointing to the configuration YAML file.

        Raises:
            FileNotFoundError: If the configuration file does not exist.
        """
        current_dir = Path(__file__).resolve()
        for parent in current_dir.parents:
            config_candidate = parent / "config" / self.env / self.config_filename
            if config_candidate.exists():
                return config_candidate

        raise FileNotFoundError(
            f"❌ Config file not found for environment '{self.env}'. "
            f"Searched path: 'config/{self.env}/{self.config_filename}'. "
            f"Please ensure the config file exists."
        )

    def load_config(self) -> Dict[str, Any]:
        """
        Load YAML configuration as a dictionary.

        Returns:
            dict: Configuration dictionary.

        Usage:
            config_loader = ConfigLoader(env="prod")
            config = config_loader.load_config()
        """
        try:
            with open(self.config_path, "r") as file:
                config = yaml.load(file, Loader=yaml.FullLoader)

            logger.info(f"✅ Loaded configuration from: {self.config_path}")
            return config

        except yaml.YAMLError as e:
            raise RuntimeError(f"❌ Failed to parse YAML config: {e}") from e

        except Exception as e:
            raise RuntimeError(f"❌ Unexpected error loading config: {e}") from e