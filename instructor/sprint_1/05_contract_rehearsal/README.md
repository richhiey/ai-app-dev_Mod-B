# Contract concept support

Use section 4 of the Sprint 1 Campus notebook alongside B-C05. The notebook applies the actual `DiagnosticRequest` and `DiagnosticResponse` models to valid, invalid, and valid-shaped-but-unsupported values.

Debrief the boundary precisely: input validation rejects malformed requests before the route; a clarification is a valid response; output schema validation checks fields and types, not whether a factual claim is supported by the equipment record or service documents.

The notebook does not inject a malformed response or use a hidden contract probe. The supported request, model validation, and observed service response are visible in their cells.
