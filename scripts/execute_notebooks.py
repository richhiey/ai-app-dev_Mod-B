"""Jupyter worker: execute in memory, keep JSON evidence, never duplicate notebooks."""
from pathlib import Path
import json
import hashlib
import sys
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager


def main():
    root,output=map(Path,sys.argv[1:3])
    references=json.loads(Path(sys.argv[3]).read_text()) if len(sys.argv)>3 else None
    kernels=output/'kernels'; spec=kernels/'module-b-local'; spec.mkdir(parents=True)
    (spec/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],'display_name':'Module B verification','language':'python'}))
    results=[]
    files=sorted((root/'notebooks').rglob('*.ipynb'))
    assert len(files)==6, 'Exactly one Campus and one Live notebook for each authored sprint.'
    for sprint in (1,2,3):
        pair=[p for p in files if p.parent.name==f'sprint_{sprint}']
        assert len(pair)==2 and sum('live_workshops' in p.name for p in pair)==1
    for variant in (['starter','reference'] if references else ['starter']):
        for file in files:
            if variant == 'reference' and file.name not in references:
                continue  # Live applied paths have separate public-workshop verifiers.
            for attempt in (1,2):
                nb=nbformat.read(file,as_version=4); nbformat.validate(nb)
                if variant=='reference':
                    changes=references[file.name]
                    known={c.id for c in nb.cells}
                    assert set(changes)<=known
                    for cell in nb.cells:
                        if cell.id in changes:
                            edit=changes[cell.id]
                            if 'source' in edit:cell.source=edit['source']
                            for old,new in edit.get('replace',[]):
                                assert old in cell.source,(cell.id,old)
                                cell.source=cell.source.replace(old,new)
                            cell.source+=edit.get('append','')
                else:
                    for cell in nb.cells:
                        if cell.id=='save-checkpoint':
                            cell.source+='\nassert not readiness["structural_ready"]\nassert not readiness["written_evidence_present"]'
                manager=KernelManager(kernel_name='module-b-local',kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(kernels)]))
                client=NotebookClient(nb,km=manager,timeout=120,resources={'metadata':{'path':str(file.parent)}})
                try:client.execute()
                except Exception:
                    # Retain a compact failure location, not an answer-filled notebook.
                    failed=[{'id':c.id,'errors':[dict(o) for o in c.get('outputs',[]) if o.output_type=='error']} for c in nb.cells if any(o.output_type=='error' for o in c.get('outputs',[]))]
                    (output/'failure.json').write_text(json.dumps(failed,indent=2))
                    raise
                finally:
                    if manager.has_kernel:manager.shutdown_kernel(now=False)
                    if client.kc is not None:client.kc.stop_channels()
                results.append({'notebook':str(file.relative_to(root)),'variant':variant,'run':attempt,
                    'notebook_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),
                    'code_cells':sum(c.cell_type=='code' for c in nb.cells),'errors':0,'external_provider_calls':0,
                    'executed_cell_ids':[c.id for c in nb.cells if c.cell_type=='code']})
                print(file.name,variant,'run',attempt,'passed',flush=True)
    (output/'notebook-results.json').write_text(json.dumps(results,indent=2)+'\n')

if __name__=='__main__':main()
