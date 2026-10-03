# Endpoint versioning support

Use section 5 of the Sprint 1 Campus notebook after learners have read B-C06. Its worked `POST /v2/diagnose` operation has a separate 600-character input model and prompt while `/v1/diagnose` retains the original 2,000-character contract.

The cell registers and calls a real FastAPI operation in the notebook runtime. The longer request succeeds on v1 and is rejected by v2. The changed paths show separate input agreements; source inspection shows the prompt and model-setting choices. Demo responses are fixed and cannot demonstrate prompt quality.

The worked route is a pattern for reasoning about compatibility. Do not substitute it for the independent supervisor task in B-C07. A deprecated route remains callable; it should not be removed while a caller still depends on it.
