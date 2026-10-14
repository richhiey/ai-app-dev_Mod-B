"""Worked chat reference. Hand-authored support, not a student's AI output."""
import json
from pathlib import Path
from time import perf_counter
import streamlit as st
from fieldcare_client import FieldCareError, load_settings, make_input, stream_diagnosis
from mock_client import stream_demo

st.set_page_config(page_title="FieldCare chat", page_icon="🔧", layout="centered")
st.session_state.setdefault("turns", [])
st.session_state.setdefault("input_error", "")


def load_reference_catalog():
    """Summarize the public starter records and current docs for dispatchers."""
    data_dir = Path(__file__).resolve().parents[2] / "service" / "data"
    try:
        equipment = json.loads((data_dir / "equipment_records.json").read_text())
        documents = json.loads((data_dir / "service_docs.json").read_text())
    except (OSError, json.JSONDecodeError):
        return None
    current_docs = [row for row in documents if row.get("current")]
    return [
        {
            "equipment_id": item["equipment_id"],
            "model": item["model"],
            "topics": list(dict.fromkeys(
                topic
                for document in current_docs
                if item["model"] in document.get("applies_to_models", [])
                for topic in document.get("topics", [])
            )),
        }
        for item in equipment
    ]


reference_catalog = load_reference_catalog()
# A widget rerun can interrupt an active script. Never leave that turn "replying".
for saved_turn in st.session_state.turns:
    if saved_turn["result"]["status"] in ("Loading", "Receiving…"):
        saved_turn["result"].update(status="Error", error="This reply was interrupted. Retry explicitly when ready.")

with st.sidebar:
    st.header("Your workspace")
    equipment = st.text_input("Equipment ID (optional)", max_chars=64, key="equipment",
                             placeholder="EQ-FC-1002", help="Saved with each message. Leave blank if unknown.")
    connection = st.radio("Connection", ["Demo", "Local service"], key="connection")
    scenario = st.selectbox("Demo scenario", ["Success", "Clarification", "Unavailable", "Interrupted"],
                            key="scenario", disabled=connection != "Demo")
    with st.expander("Known equipment & topics"):
        if reference_catalog is None:
            st.caption("The reference knowledge catalog is unavailable in this checkout.")
        else:
            st.caption("Reference starter records and current service documents:")
            for item in reference_catalog:
                st.markdown(f'**{item["equipment_id"]} · {item["model"]}**')
                if item["topics"]:
                    st.caption("Ask about: " + ", ".join(item["topics"]))
                else:
                    st.caption("No current service topics are listed for this model.")
            st.caption("No live ticket or maintenance history, warranty status, or repair approval is available.")
            st.caption("For smoke, burning smells, electrical damage, or breaker trips, stop routine checks and escalate for safety review.")
    if st.button("New chat", use_container_width=True):
        st.session_state.turns = []
        st.session_state.input_error = ""
    if st.checkbox("Show request help", key="show_help"):
        st.caption("Open a reply's Sources & request details when reporting an issue. Never share keys or private questions.")
    st.caption("History lasts for this browser session. Each request sends only its question and equipment, not earlier messages.")

st.caption("HELIODESK / EQUIPMENT SUPPORT")
st.title("Ask FieldCare")
st.caption("A place to work through your equipment questions.")
if connection == "Demo":
    st.info("Demo · mock replies, no network or model calls.")
else:
    st.caption("Local service · each reply shows its actual source mode in its details.")
    try:
        configured_url, _ = load_settings()
        st.caption(f"Configured target: {configured_url}/v1/diagnose-stream")
    except FieldCareError as error:
        st.warning(str(error))


def show_result(result):
    if result["status"] in ("Loading", "Receiving…"):
        st.caption("FieldCare is replying…")
    elif result["status"] == "Error":
        st.error(result["error"])
        if result["answer"]:
            st.warning("Incomplete response — do not treat partial text as a finished answer.")
    elif result["status"] == "Needs clarification":
        st.caption("More context needed · send a new, self-contained question with the equipment ID.")
    else:
        st.caption(result["status"])
    if result["answer"]:
        st.markdown(result["answer"])
    with st.expander("Sources & request details"):
        st.caption("Source mode: " + result["mode"])
        st.caption("Target: " + result.get("target", "Not recorded"))
        first = result.get("first_text_ms")
        elapsed = result.get("elapsed_ms")
        tokens = result.get("tokens")
        st.table([
            {"Signal": "UI elapsed", "Observed": f"{elapsed:.0f} ms" if elapsed is not None else "Not recorded"},
            {"Signal": "First text at UI", "Observed": f"{first:.0f} ms" if first is not None else ("No streamed text" if "first_text_ms" in result else "Not recorded")},
            {"Signal": "Text chunks", "Observed": str(result["chunks"]) if "chunks" in result else "Not recorded"},
            {"Signal": "Reported model", "Observed": result.get("model") or "Not reported"},
            {"Signal": "Reported total tokens", "Observed": str(tokens) if tokens is not None else "Not reported"},
            {"Signal": "HTTP rejection", "Observed": str(result["http_status"]) if result.get("http_status") else "None recorded"},
        ])
        st.caption("UI timings include client and service work; they are not the service log's timings. Chunks are not tokens.")
        st.caption("Events: " + (" → ".join(result.get("events", [])) or "No response event received"))
        for citation in result["citations"]:
            st.text(str(citation))
        if result["request_id"]:
            st.code(result["request_id"], language=None)
        else:
            st.caption("No request reference received.")


def show_question(turn):
    with st.chat_message("user"):
        st.markdown(turn["payload"]["question"])
        st.caption(f'{turn["connection"]} · Equipment: {turn["payload"].get("equipment_id", "not specified")}'
                   + (" · Retry" if turn.get("retry") else ""))


retry_turn = None
retry_slot = None
if not st.session_state.turns:
    with st.chat_message("assistant"):
        st.write("What equipment are you working on?")
        st.write("Add an equipment ID in the sidebar, then ask a question below.")
        st.caption("Try: Which filter and airflow checks are documented?")
else:
    for index, turn in enumerate(st.session_state.turns):
        show_question(turn)
        with st.chat_message("assistant"):
            show_result(turn["result"])
            if index == len(st.session_state.turns) - 1 and turn["result"]["status"] == "Error":
                retry_slot = st.empty()
                if retry_slot.button("Retry this message", key=f"retry_{index}",
                                     help="Repeats this question with its original equipment, connection and demo scenario."):
                    retry_turn = turn

if st.session_state.input_error:
    st.error(st.session_state.input_error)
prompt = st.chat_input("Ask about your equipment…", max_chars=2000, submit_mode="disable", key="chat_prompt")

# Rendering saved messages never calls the service. Only these two actions do.
if prompt is not None or retry_turn is not None:
    st.session_state.input_error = ""
    if retry_slot is not None:
        retry_slot.empty()  # Remove repeat retry while this attempt runs.
    try:
        payload = dict(retry_turn["payload"]) if retry_turn else make_input(prompt, equipment)
    except FieldCareError as error:
        st.session_state.input_error = str(error)
        st.rerun()
    result = dict(status="Loading", answer="", citations=[], request_id="", mode="No response yet", error="",
                  events=[], chunks=0, first_text_ms=None, elapsed_ms=None, model=None, tokens=None,
                  http_status=None, target="Not connected")
    started = perf_counter()
    turn = dict(payload=payload, connection=retry_turn["connection"] if retry_turn else connection,
                scenario=retry_turn["scenario"] if retry_turn else scenario, result=result, retry=retry_turn is not None)
    st.session_state.turns.append(turn)
    show_question(turn)
    with st.chat_message("assistant"):
        slot = st.empty()
        with slot.container():
            show_result(result)
        try:
            if turn["connection"] == "Demo":
                result["target"] = "Demo — no HTTP request"
                events = stream_demo(payload, turn["scenario"])
            else:
                base_url, caller_key = load_settings()
                result["target"] = base_url + "/v1/diagnose-stream"
                events = stream_diagnosis(payload, base_url=base_url, caller_key=caller_key)
            for event in events:
                kind = event["type"]
                result["elapsed_ms"] = (perf_counter() - started) * 1000
                if not result["events"] or result["events"][-1] != kind:
                    result["events"].append(kind)  # Collapse repeated delta labels, not text.
                if kind == "metadata":
                    result.update(request_id=str(event.get("request_id", "")), mode=str(event.get("mode", "unknown")),
                                  citations=[str(c) for c in event.get("citations", [])])
                elif kind == "delta":
                    text = str(event.get("text", ""))
                    result["answer"] += text
                    result["chunks"] += 1
                    if text and result["first_text_ms"] is None:
                        result["first_text_ms"] = result["elapsed_ms"]
                    result["status"] = "Receiving…"
                elif kind == "usage":
                    count = event.get("tokens")
                    result["tokens"] = count if type(count) is int and count >= 0 else None
                    result["model"] = event.get("model") if isinstance(event.get("model"), str) else None
                elif kind == "complete":
                    result["status"] = "Complete"
                elif kind == "response":
                    body = event["response"]
                    result.update(answer=body.get("answer", ""), mode=body.get("mode", "unknown"),
                                  citations=body.get("citations", []), request_id=event.get("request_id", ""),
                                  status="Needs clarification" if body.get("status") == "needs_clarification" else "Response received")
                elif kind == "error":
                    raise FieldCareError("FieldCare could not finish the stream. Retry explicitly when ready.",
                                         request_id=event.get("request_id", result["request_id"]))
                with slot.container():
                    show_result(result)
        except FieldCareError as error:
            result.update(status="Error", error=str(error), http_status=error.status_code)
            if error.request_id:
                result["request_id"] = error.request_id
            if error.retry_after is not None:
                result["error"] += f" Wait at least {error.retry_after} seconds; keep the service running."
        finally:
            result["elapsed_ms"] = (perf_counter() - started) * 1000
    st.rerun()  # Render the saved turn and any retry control; no new submission.
