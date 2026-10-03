# Preserved evaluation implementation

This package carries the existing Module A FieldCare evaluator into the separate Module B repository so Sprint 3 can reuse its original criteria without installing or cloning Module A. It is an evaluation compatibility snapshot, not the Module B service runtime.

The evaluation uses the original request cases, retrieval/tool rules, response flags, and scoring function. Its generated response path uses the vendored, pinned OpenRouter client and requires the same runtime OpenRouter key. All input assets are bundled under the data directory; no Module A repository or remote asset lookup is used at runtime.

provenance.json records the source notebook digest, helper commit, and hashes of the bundled files. The snapshot is licensed under the included license. Keep changes to this compatibility package limited to security or reproducibility fixes and preserve the original evaluation criteria.
