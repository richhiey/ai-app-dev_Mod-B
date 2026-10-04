"""Select original Module A cases; this does not score generated stream wording."""

import json
import sys
from fieldcare.config import DATA
from module_b.evaluation import evaluate_selected
from module_b._module_a import project as module_a


def main():
    case_ids = sys.argv[1:]
    if not case_ids:
        raise SystemExit("Usage: python -m clients.evaluate CASE_ID COMPANION_CASE_ID")
    pipeline = module_a.build_fieldcare_pipeline(
        module_a.load_fieldcare_environment(),
        json.loads((DATA / "pipeline_design.json").read_text()),
    )
    for case_id in case_ids:
        print(
            "Original case:",
            json.dumps(module_a.eval_case_by_id(pipeline.env, case_id), indent=2),
        )
    print(
        json.dumps(evaluate_selected(DATA / "pipeline_design.json", case_ids), indent=2)
    )


if __name__ == "__main__":
    main()
