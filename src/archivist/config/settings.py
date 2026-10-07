from pathlib import Path
import json

# Project root
PROJECT_ROOT = Path(__file__).resolve().parents[3]

# Data paths
DATA_PATH = PROJECT_ROOT / "data"
CONV_PATH = DATA_PATH / "conversations"
LOG_PATH = DATA_PATH / "logs"

CONFIG_PATH = DATA_PATH / "config.json"

class Settings:
    REQUIRED_KEYS = [
        "llama_cpp_dir",
        "llms_dir"
    ]

    def __init__(self):
        self.config = self._load_config()
        # self._validate()

        self.LLMS_DIR = Path(self.config["llms_dir"])
        self.LLAMA_CPP_DIR = Path(self.config["llama_cpp_dir"])

    def _load_config(self):
        if not CONFIG_PATH.exists():
            raise FileNotFoundError(
                f"Config file not found: {CONFIG_PATH}"
                )
        
        with open(CONFIG_PATH, "r", encoding="utf-8") as file:
            return json.load(file)
        
    # def _validate(self):
    #     missing = []

    #     for key in self.REQUIRED_KEYS:
    #         if key not in self.config:
    #             missing.append(key)

    #     if missing:
    #         raise ValueError(
    #             f"Missing config keys: {', '.join(missing)}"
            # )
        
    def edit_config(self, key, value):
        if key not in self.config:
            raise KeyError(
                f"Key does not exist in config file: {key}"
            )
        
        self.config[key] = value

        with open(CONFIG_PATH, "w", encoding="utf-8") as file:
            json.dump(self.config, file, indent=4)


settings = Settings()