# Synthetic UI testing mismatch fixture

**Teaching fixture: all IDs, events and observations below are constructed for practice. They are not results from a real student app or a provider call.**

Use this only to rehearse comparing a prediction with evidence. Do not copy it into your project test notes as an observed result.

## Case `SYNTHETIC-TEST-01`

Starting state: the Streamlit app targets FieldCare. A supported equipment question is submitted once.

| Evidence | Expected | Fixture observation |
|---|---|---|
| UI state | A complete answer with its own citations and request ID. | Partial text is labelled incomplete; the turn shows a provider error. |
| Event sequence | `metadata` → `delta` → `complete` | `metadata` → `delta` → `error` with category `provider_incomplete` |
| Safe service record | `outcome=completed` | `status_code=200`, `outcome=failed`, `source=live_provider`, `error_category=provider_incomplete` |
| Request reference | Same unique identifier in UI and record. | `11111111-1111-4111-8111-111111111111` (synthetic placeholder) |

## Worked diagnosis

The last confirmed boundary is FieldCare's stream: the service returned metadata and partial text, then an error event. The matching record confirms that the request reached the provider path, but `outcome=failed` and `provider_incomplete` show that the answer did not finish. The UI is correct to keep the text unfinished. This evidence does not establish a successful answer or answer quality.

For a real test, keep the actual request ID, app revision, source mode and safe record. Find the first boundary your own evidence confirms, make one targeted correction only when a real mismatch exists, and rerun that case.
