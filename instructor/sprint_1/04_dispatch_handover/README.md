# Dispatch handover facilitator reference

This folder contains a reference implementation for facilitator use. Keep it out of the learner checkpoint and do not paste the completed route into the independent-practice notebook.

The Sprint 1 Campus notebook runs the actual FastAPI app. To review this reference, copy its route and entry-point files into a separate example workspace, set the OpenRouter key in the runtime environment, and send the requests in `examples/patterns/handover_requests.json` to both `/v1/diagnose` and `/v1/dispatch-handover`. Supported requests use the route prompt, Chroma retrieval, LangGraph, and a real OpenRouter call.

Demo mode checks route and application behavior with fixed output. It does not test generated wording. The notebook’s optional provider section makes real calls only after a learner enters an approved model and hidden key.
