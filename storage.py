import json
import os

DATA_FILE = "data.json"

_default = {"companies": [], "contacts": [], "deals": []}


def load():
    if not os.path.exists(DATA_FILE):
        return {k: list(v) for k, v in _default.items()}
    with open(DATA_FILE) as f:
        return json.load(f)


def save(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)
