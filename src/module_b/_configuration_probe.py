"""Verify registered route/prompt bindings with a mocked provider, not live AI."""
import json
import os
from pathlib import Path
import sys
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(ROOT))


def main() -> None:
    # Synthetic configuration exists only inside this process; no .env is read.
    with patch.dict(os.environ, {"FIELDCARE_MODE": "live", "OPENROUTER_MODEL": "mock/model",
                                 "OPENROUTER_API_KEY": "synthetic-not-a-real-key"}, clear=True):
        import httpx
        from fastapi.testclient import TestClient
        from app.main import app
        from app import model, routes, practice_routes

        posted_prompts = []

        def fake_post(url, *, headers, json, timeout):
            assert url == "https://openrouter.ai/api/v1/chat/completions"
            assert json["model"] == "mock/model"
            posted_prompts.append(json["messages"][0]["content"])
            return httpx.Response(200, request=httpx.Request("POST", url), json={"choices": [{
                "finish_reason": "stop", "message": {"content": "MOCK: provider wording was not tested."}
            }]})

        valid = json.loads((ROOT / "fixtures" / "valid-request.json").read_text())
        with patch.object(model.httpx, "post", side_effect=fake_post) as provider:
            with TestClient(app) as client:
                for path, expected_prompt in [("/v1/diagnose", routes.SYSTEM_PROMPT),
                                              ("/practice/diagnose-brief", practice_routes.SYSTEM_PROMPT)]:
                    before = provider.call_count
                    response = client.post(path, json=valid)
                    assert response.status_code == 200, (path, response.text)
                    assert provider.call_count == before + 1
                    assert posted_prompts[-1] == expected_prompt
                    assert response.json()["answer"].startswith("MOCK:")
                    bad = client.post(path, json={"equipment_id": "EQ-FC-1002"})
                    assert bad.status_code == 422 and provider.call_count == before + 1
                    incomplete = client.post(path, json={"question": "The unit runs hot after service."})
                    assert incomplete.status_code == 200
                    assert incomplete.json()["status"] == "needs_clarification"
                    assert provider.call_count == before + 1
        assert routes.SYSTEM_PROMPT != practice_routes.SYSTEM_PROMPT
        assert "short paragraph" in posted_prompts[0]
        assert "three short bullet points" in posted_prompts[1]
        print("Original and practice routes: registered; fixed schema retained.")
        print("Prompt bindings: distinct and verified at the mocked provider HTTP boundary.")
        print("Invalid input: 422 before provider; incomplete context: clarification before provider.")
        print("External provider calls: 0. Generated wording has not been tested.")


if __name__ == "__main__":
    main()
