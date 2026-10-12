"""Deterministic interface rehearsal. No network, provider or service record."""
import time
from fieldcare_client import FieldCareError


def stream_demo(payload, scenario="Success"):
    time.sleep(0.15)
    if scenario == "Unavailable":
        raise FieldCareError("Demo service unavailable. Your inputs are kept; try another demo scenario.")
    if scenario == "Clarification" or not payload.get("equipment_id"):
        yield {"type": "response", "request_id": "demo-clarify", "response": {
            "status": "needs_clarification", "mode": "mock", "citations": [],
            "answer": "Which equipment are you asking about? Add its ID or more context."}}
        return
    yield {"type": "metadata", "mode": "mock", "request_id": "demo-001", "citations": ["DEMO-SOURCE-01"]}
    for text in ["MOCK ONLY — ", "this text tests your interface. ", "No model or service was called."]:
        time.sleep(0.1)
        yield {"type": "delta", "text": text}
        if scenario == "Interrupted":
            raise FieldCareError("Demo stream interrupted. The partial text is incomplete.", request_id="demo-001")
    yield {"type": "complete", "request_id": "demo-001"}
