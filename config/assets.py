import yaml
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "assets.yaml"


def load_assets():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    return cfg["assets"]
