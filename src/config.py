import json
import os
from typing import Dict, Any


def load_config() -> Dict[str, Any]:
    config_path = os.path.join(
        'config',
        'config.json'
    )
    config_path = os.path.abspath(config_path)

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as file:
        config_data = json.load(file)
    return config_data
