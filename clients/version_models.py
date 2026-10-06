"""Inspect approved version settings without invoking either provider graph."""
import json
from fieldcare.config import openrouter_model, openrouter_model_v2

if __name__ == "__main__":
    print(json.dumps({"OPENROUTER_MODEL": openrouter_model(),
                      "OPENROUTER_MODEL_V2": openrouter_model_v2()}, indent=2))
