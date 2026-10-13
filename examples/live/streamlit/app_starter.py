"""Learner starting state: controls render, but no request is made yet."""
import streamlit as st

from client import CONTEXT, apply_event, demo_events, make_input, new_turn, service_events

st.title("Ask about supplied notes")
if "turns" not in st.session_state:
    st.session_state.turns = []
origin = st.sidebar.selectbox("Request path", ["Demo", "Local service"])
scenario = st.sidebar.selectbox("Demo example", ["Success", "Interrupted"])
context = st.sidebar.text_area("Context for the next question", value=CONTEXT)
show_details = st.sidebar.checkbox("Show reply details", value=True)
if st.sidebar.button("New chat"):
    st.session_state.turns = []


def show_turn(turn):
    st.markdown(turn["text"] or "Waiting for content…")
    st.caption(f"{turn['origin']} · {turn['state']}")
    if turn["error"]:
        st.warning(f"Request ended: {turn['error']}")
    if turn["retry_after"]:
        st.info(f"Wait at least {turn['retry_after']} seconds before a new attempt.")
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

question = st.chat_input("Ask one question about these notes")
if question is not None:
    st.info("Starting state: the composer works. The guided build connects this submission to the client.")
