"""Private child-process probe; called through module_b.fieldcare.trace_paths."""
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

sys.dont_write_bytecode = True

def trace(root: Path) -> list[dict]:
    sys.path.insert(0, str(root))
    observations = []
    # No .env is loaded, and live settings/credentials are not inherited.
    with patch.dict(os.environ, {"FIELDCARE_MODE": "demo"}, clear=True):
        from fastapi.testclient import TestClient
        from app.main import app
        from app import model, routes, service

        with patch.object(model.httpx, "post", side_effect=AssertionError("External provider call forbidden")) as provider:
            with TestClient(app) as client:
                for case, expected in [("valid", (200, 1, 1)), ("invalid", (422, 0, 0)), ("incomplete", (200, 1, 0))]:
                    payload = json.loads((root / "fixtures" / f"{case}-request.json").read_text())
                    with patch.object(routes, "run_diagnosis", wraps=service.run_diagnosis) as service_call:
                        with patch.object(service, "generate_answer", wraps=model.generate_answer) as adapter:
                            response = client.post("/v1/diagnose", json=payload)
                    actual = (response.status_code, service_call.call_count, adapter.call_count)
                    assert actual == expected, (case, actual, expected)
                    provider.assert_not_called()
                    data = response.json()
                    if case == "valid":
                        assert data["mode"] == "demo" and data["status"] == "ready"
                        assert data["answer"].startswith("DEMO: No model was called.")
                    elif case == "incomplete":
                        assert data["status"] == "needs_clarification" and not data["citations"]
                    else:
                        assert any(item["loc"] == ["body", "question"] and item["type"] == "missing" for item in data["detail"])
                    observations.append({"case": case, "status_code": actual[0], "handler_service_calls": actual[1],
                                         "adapter_calls": actual[2], "provider_calls": 0, "response_json": data})
    return observations


if __name__ == "__main__":
    print(json.dumps(trace(Path(sys.argv[1]))))
