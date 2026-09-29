"""Verify C05 conceptual examples against the actual supplied service locally."""
from pathlib import Path
from datetime import datetime, timezone
import json
import shutil
import tempfile

import httpx
from module_b.contracts import inspect_contract
from module_b.fieldcare import demo_service
from module_b.workspace import prepare_example

ROOT=Path(__file__).resolve().parents[1]
VALID={'question':'What filter checks are documented?','equipment_id':'EQ-FC-1002'}
INCOMPLETE={'question':'The unit runs hot after service.'}
UNSUPPORTED={'answer':'The equipment is safe and the repair is complete.',
             'status':'ready','citations':[],'mode':'live'}
EXAMPLES={
    'schema_valid_unsupported_claim':UNSUPPORTED,
    'malformed_citations':dict(UNSUPPORTED,citations='DOC-FC-TS-001'),
    'wording_variant_one':dict(UNSUPPORTED,answer='A technician must verify the documented filter checks.'),
    'wording_variant_two':dict(UNSUPPORTED,answer='Verify the filter checks described in the supplied documents.'),
}

def main():
    record={'verified_at':datetime.now(timezone.utc).isoformat(),'external_provider_calls':0,'routes':{}}
    with tempfile.TemporaryDirectory(prefix='contract-note-') as folder:
        project=prepare_example(destination=Path(folder)/'service',repo_root=ROOT)
        reference=ROOT/'instructor/sprint_1/04_dispatch_handover'
        for name in ['main.py','handover_routes.py']:
            shutil.copy2(reference/name,project/'app'/name)
        for route,module in [('/v1/diagnose','app.routes'),('/v1/dispatch-handover','app.handover_routes')]:
            result=inspect_contract(project,route=route,route_module=module,max_length=2000,
                accepted_payload=VALID,incomplete_payload=INCOMPLETE,output_examples=EXAMPLES)
            assert result['passed'],result
            assert result['output_examples']['schema_valid_unsupported_claim']['schema_valid']
            assert not result['output_examples']['malformed_citations']['schema_valid']
            assert all(result['output_examples'][name]['schema_valid'] for name in ['wording_variant_one','wording_variant_two'])
            record['routes'][route]=result
        with demo_service(project) as service:
            health=httpx.get(service.base_url+'/health')
            assert health.status_code==200 and health.json()=={'status':'ok','mode':'demo'}
            missing=httpx.post(service.base_url+'/v1/dispatch-handover',json=INCOMPLETE)
            assert missing.status_code==200
            expected={'answer':'Please provide the equipment_id and recent service details before model-specific guidance.',
                      'status':'needs_clarification','citations':[],'mode':'demo'}
            assert missing.json()==expected
            record['clarification_response']=expected
            record['health_response']=health.json()
            # Valid service output cannot satisfy the proposed client's wrong keys.
            assert 'summary' not in expected and 'source' not in expected
            record['caller_mismatch']={'service_shape_valid':True,'client_requested_absent_fields':['summary','source']}
    record['limitations']=['Synthetic output examples are authored fixtures, not model results.',
                          'Fault injection is isolated from production files; adapter work is demo only.',
                          'No external provider, hosted Colab or answer-quality evaluation performed.']
    out=ROOT/'docs/contract-note-verification.json'
    out.write_text(json.dumps(record,indent=2)+'\n')
    print('C05 contract examples verified; external provider calls: 0.')

if __name__=='__main__':main()
