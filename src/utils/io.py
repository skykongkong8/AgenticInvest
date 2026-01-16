import json
import os
from pathlib import Path
from typing import Any, Dict

def ensure_dir(path: str):
    Path(path).mkdir(parents=True, exist_ok=True)

def write_json(path: str, data: Any):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

def write_text(path: str, content: str):
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def write_jsonl(path: str, event: Dict[str, Any]):
    ensure_dir(os.path.dirname(path))
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, default=str) + "\n")
