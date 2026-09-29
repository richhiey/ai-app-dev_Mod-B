"""Incremental provider adapter and explicitly simulated transport fixture."""
import asyncio
import json
import os
import httpx


class StreamFailure(RuntimeError):
    """Safe fixed error; provider payloads never become exception/log text."""


async def fixture_events(*, interrupted=False):
    """Scripted transport data, NOT measured LLM generation or real token usage."""
    for index,text in enumerate(['Review the service evidence. ', 'Confirm the equipment context. ', 'Follow the supported next checks.']):
        await asyncio.sleep(0.08)
        if interrupted and index==1:
            raise StreamFailure('provider_interrupted')
        yield {'type':'delta','text':text}
    yield {'type':'usage','model':'transport-fixture','tokens':None}


async def sse_data(response):
    """SSE framing: join data lines, ignore comments, dispatch at blank lines."""
    data=[]
    async for line in response.aiter_lines():
        if line=='':
            if data:yield '\n'.join(data);data=[]
        elif line.startswith('data:'):
            value=line[5:]
            data.append(value[1:] if value.startswith(' ') else value)
    # A final partial frame is not a complete SSE event.


async def provider_events(context, *, transport=None):
    """OpenRouter SSE to typed events; requires a clean stop and protocol terminator.

    No buffering/slicing of a completed generation. Usage can be absent. Injectable
    HTTP transport exists for tests only and never implies a live provider result.
    """
    key=os.environ.get('OPENROUTER_API_KEY','')
    model=os.environ.get('OPENROUTER_MODEL','')
    if not key or not model:
        raise StreamFailure('provider_not_configured')
    ended=False; stopped=False; content=False
    try:
        async with httpx.AsyncClient(timeout=40,transport=transport) as client:
            async with client.stream('POST','https://openrouter.ai/api/v1/chat/completions',
                headers={'Authorization':'Bearer '+key},json={'model':model,'stream':True,
                'stream_options':{'include_usage':True},'temperature':0.2,'max_tokens':350,
                'messages':[{'role':'system','content':'Explain the supplied FieldCare evidence to a technician. Preserve limitations; do not invent checks or coverage.'},
                            {'role':'user','content':json.dumps(context)}]}) as response:
                if response.status_code!=200:raise StreamFailure('provider_rejected')
                async for raw in sse_data(response):
                    if raw=='[DONE]':ended=True;break
                    event=json.loads(raw)
                    if event.get('error'):raise StreamFailure('provider_interrupted')
                    for choice in event.get('choices',[]):
                        reason=choice.get('finish_reason')
                        if reason and reason!='stop':raise StreamFailure('provider_incomplete')
                        if reason=='stop':stopped=True
                        delta=choice.get('delta',{}).get('content')
                        if isinstance(delta,str) and delta:
                            content=True
                            yield {'type':'delta','text':delta}
                    usage=event.get('usage')
                    if isinstance(usage,dict):
                        count=usage.get('total_tokens')
                        yield {'type':'usage','model':event.get('model',model),
                            'tokens':count if type(count) is int and count>=0 else None}
        if not (ended and stopped and content):raise StreamFailure('provider_incomplete')
    except StreamFailure:raise
    except Exception:
        raise StreamFailure('provider_unavailable') from None


def encode_event(event):
    return json.dumps(event,ensure_ascii=False)+'\n'
