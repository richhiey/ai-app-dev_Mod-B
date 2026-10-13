"""Worked reference. Copy to app.py for the bounded independent UI improvement."""
import streamlit as st

from client import CONTEXT, apply_event, demo_events, make_input, new_turn, service_events

st.set_page_config(page_title="Live concept chat", layout="centered")
st.title("Ask about supplied notes")
st.caption("One question and its context. Earlier turns stay on screen; they are not sent to the service.")
if "turns" not in st.session_state:
    st.session_state.turns = []

origin = st.sidebar.selectbox("Request path", ["Demo", "Local service"])
scenario = st.sidebar.selectbox("Demo example", ["Success", "Interrupted"])
context = st.sidebar.text_area("Context for the next question", value=CONTEXT)
show_details = st.sidebar.checkbox("Show reply details", value=True)
if st.sidebar.button("New chat"):
    st.session_state.turns = []


def show_turn(turn):
    st.markdown(turn["text"] or ("No answer received." if turn["state"] == "Failed" else "Waiting for content…"))
    st.caption(f"{turn['origin']} · {turn['state']}")
    if turn["error"]:
        st.warning(f"Request ended: {turn['error']}")
    if turn["retry_after"]:
        st.info(f"Wait at least {turn['retry_after']} seconds before making a new attempt.")
    if show_details:
        st.json({key: turn[key] for key in (
            "origin", "state", "target", "mode", "http_status", "request_id",
            "references", "events", "model", "tokens"
        )})


for saved in st.session_state.turns:
    with st.chat_message("user"):
        st.write(saved["body"]["question"])
    with st.chat_message("assistant"):
        show_turn(saved)

# Only an explicit submit reaches the client. Sidebar reruns only redisplay turns.
question = st.chat_input("Ask one question about these notes")
if question is not None:
    try:
        body = make_input(question, context)
    except ValueError as error:
        st.warning(str(error))
    else:
        turn = new_turn(body, origin)
        st.session_state.turns.append(turn)
        with st.chat_message("user"):
            st.write(body["question"])
        with st.chat_message("assistant"):
            panel = st.empty()
            events = demo_events(body, scenario) if origin == "Demo" else service_events(body)
            for event in events:
                apply_event(turn, event)
                with panel.container():
                    show_turn(turn)
