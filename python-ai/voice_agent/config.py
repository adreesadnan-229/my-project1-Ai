import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")


def load_config():
    if not os.path.exists(CONFIG_PATH):
        return {}
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data):
    existing = load_config()
    existing.update(data)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)
