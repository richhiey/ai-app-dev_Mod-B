# Module B authoring rules

- All practical notebooks target Google Colab and must also execute in a fresh local Linux/macOS Jupyter environment before release.
- Put reusable helpers in src/module_b. Do not duplicate helper function bodies or whole service implementations in notebook cells. The initial source-install bootstrap is the minimal exception.
- Preserve visible teaching operations: routes, schemas, prompt bindings, HTTP calls, auth/limit attachment, streaming yields, log fields and evaluator calls.
- Read the lesson's exact outcome/type and applicable Masterschool skill before drafting. The schedule in docs/curriculum.md covers all 23 Campus and 16 live rows.
- Use one cumulative module repository, with FieldCare as a teaching example and stable checkpoint references. Do not silently replace learner workspaces or completed lesson behaviour.
- Keep demo, mocked-provider, in-process test and actual HTTP evidence distinct. Never imply generated output/provider/hosted-Colab verification that did not happen.
- No provider credentials, private assessment answers or student work in the published course repository. No remote publication without user authorization.
- Later evaluation reuses the authentic Module A framework; no replacement scorer. Later UI credentials stay in a trusted connector.
- Run affected helper/service tests and execute changed notebooks. Preserve output-free learner notebooks and separate executed evidence.

## Two Colab notebooks per sprint — current author requirement

Maintain exactly two canonical `.ipynb` files per authored sprint: one Campus notebook reused by every Campus lesson, and one Live notebook reused by all four live sessions. The user clarified this on 29 September 2026, superseding the previous combined-notebook rule. Use one setup and one final export in each notebook. Keep Campus project state separate from Live practice; explicitly import checkpoints and verify any apply-back changes. Preserve asynchronous guided support in Campus. Keep worked examples separate from independent/assessment decisions. Execute verification variants in memory and save JSON/HTML evidence, never additional executed/reference notebooks.

## GitHub source delivery

The six learner notebooks clone the separate Module B repository with `git clone --depth 1 --branch main` and install that checkout with the repository's `requirements.lock`. Do not add a pinned commit checkout, separate source ZIP, or repeated package setup to student notebooks. The Colab launch links may reference the reviewed delivery commit so students open the intended notebook, while setup intentionally installs the current `main` branch. Keep personal project checkpoint exports for learner work and carrying changes between sprints.
