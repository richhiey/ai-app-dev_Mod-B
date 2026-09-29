"""Reuse the frozen Module A evaluator on the same design loaded by the service."""
import hashlib
import json
from pathlib import Path
from ._module_a import project as module_a


def load_pipeline(design_path):
    design=json.loads(Path(design_path).read_text())
    return module_a.build_fieldcare_pipeline(module_a.load_fieldcare_environment(),design)


def design_revision(design_path):
    return hashlib.sha256(Path(design_path).read_bytes()).hexdigest()


def run_case(pipeline, case_id, question=None):
    case=module_a.eval_case_by_id(pipeline.env,case_id)
    request=module_a.request_for_eval_case(pipeline,case)
    if question is not None:
        request['request_text']=question
    context=module_a.assemble_fieldcare_context(pipeline,request)
    response=module_a.draft_fieldcare_response(pipeline,context)
    return context,response


def evaluate_selected(design_path, case_ids):
    """Original criteria and evaluator, no substitute score and no live-wording claim."""
    pipeline=load_pipeline(design_path)
    return {'evidence_kind':'original_module_a_deterministic_evaluator',
        'design_revision':design_revision(design_path),
        'rows':[module_a.evaluate_case(pipeline,module_a.eval_case_by_id(pipeline.env,c)) for c in case_ids]}
