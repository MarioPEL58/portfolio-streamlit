from pathlib import Path
import tomllib

def load_config():
    config_path = Path(__file__).resolve().parent.parent / "app_config.toml"
    with open(config_path, "rb") as f:
        return tomllib.load(f)
