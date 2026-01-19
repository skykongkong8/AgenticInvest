from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml
from crewai import LLM

DEFAULT_MODEL = "gpt-4-turbo-preview"
DEFAULT_TEMPERATURE = 0.0


def _load_model_config() -> Dict[str, Any]:
    config_path = Path("configs/model.yaml")
    if not config_path.exists():
        return {
            "smart_model": DEFAULT_MODEL,
            "temperature": DEFAULT_TEMPERATURE,
        }
    with config_path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@lru_cache(maxsize=1)
def get_llm() -> LLM:
    config = _load_model_config()
    return LLM(
        model=str(config.get("smart_model", DEFAULT_MODEL)),
        temperature=float(config.get("temperature", DEFAULT_TEMPERATURE)),
    )


def generate_text(llm: LLM, prompt: str, fallback: str) -> str:
    try:
        if hasattr(llm, "call"):
            response = llm.call(prompt)
        elif hasattr(llm, "invoke"):
            response = llm.invoke(prompt)
        elif hasattr(llm, "generate"):
            response = llm.generate(prompt)
        else:
            return fallback
        return str(response).strip() or fallback
    except Exception:
        return fallback
