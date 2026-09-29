"""Teaching replay API; retains the original buffered diagnostic API unchanged."""
import os
import time
from pathlib import Path
from typing import Literal
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field
from module_b.evaluation import load_pipeline, run_case, design_revision
from module_b.streaming import fixture_events, provider_events, StreamFailure, encode_event

router=APIRouter()
DESIGN=Path(__file__).resolve().parents[1]/'data/pipeline_design.json'
pipeline=load_pipeline(DESIGN)
PIPELINE_REVISION=design_revision(DESIGN)

class ReplayRequest(BaseModel):
    model_config=ConfigDict(extra='forbid')
    case_id: str=Field(pattern=r'^EVAL-FC-0(?:0[1-9]|1[0-6])$')
    question: str | None=Field(default=None,min_length=1,max_length=1000)
    fault: Literal['none','interrupt']='none'

async def events(body,request):
    started=time.perf_counter()
    context,response=run_case(pipeline,body.case_id,body.question)
    mode=os.environ.get('FIELDCARE_STREAM_MODE','fixture')
    observation=request.state.observation
    observation.update(source='live_provider' if mode=='live' else 'transport_fixture',case_id=body.case_id,
                       model=None if mode=='live' else 'transport-fixture')
    source=provider_events(context) if mode=='live' else fixture_events(interrupted=body.fault=='interrupt')
    first=True
    try:
        async for event in source:
            if event['type']=='delta':
                if first:observation['first_content_ms']=(time.perf_counter()-started)*1000;first=False
                yield event
            elif event['type']=='usage':observation.update(model=event['model'],tokens=event['tokens'])
        yield {'type':'complete','request_id':request.state.request_id,
               'design_revision':PIPELINE_REVISION,'decision_flags':response['decision_flags']}
    except StreamFailure as exc:
        observation['error_category']=str(exc)
        yield {'type':'error','category':str(exc),'request_id':request.state.request_id}
    finally:
        await source.aclose()

@router.post('/v1/fieldcare-stream')
async def stream(body:ReplayRequest,request:Request):
    async def lines():
        async for event in events(body,request):
            yield encode_event(event)
    return StreamingResponse(lines(),media_type='application/x-ndjson',headers={'Cache-Control':'no-store'})

@router.post('/v1/fieldcare-buffered')
async def buffered(body:ReplayRequest,request:Request):
    # Exact same source as streaming, fully collected before returning JSON.
    return {'events':[event async for event in events(body,request)]}

@router.post('/v1/fieldcare-evidence')
async def evidence(body:ReplayRequest,request:Request):
    context,response=run_case(pipeline,body.case_id,body.question)
    request.state.observation.update(source='module_a_deterministic',model='module-a-rules',case_id=body.case_id)
    return {'response':response,'design_revision':PIPELINE_REVISION}
