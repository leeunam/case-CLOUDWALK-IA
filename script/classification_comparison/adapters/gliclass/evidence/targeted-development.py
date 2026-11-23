"""Pilotos isolados de duas máscaras de desenvolvimento, usando APIs C02 intactas."""
import copy,json,os,shutil,subprocess,sys,time,uuid
from pathlib import Path
ROOT=Path.cwd()
BASE=ROOT/'script/classification_comparison/adapters/gliclass'
sys.path.insert(0,str(ROOT/'script/classification_comparison'))
import run as runner
from common import preflight,project,encode,injected_inventory,c01
from journal import Journal,inventory

os.sched_setaffinity(0,{0,2})
validation,protocol,split,catalog,cases,example=preflight()
dev={i for group in split['development'].values() for i in group}
config_path=BASE/'real-dev-d.json';config=c01.read(config_path)
matrix=c01.read(BASE/'development-matrix.json')['profiles']['D']
assert c01.digest(config_path)==matrix['config_sha256']
assert config['identity']['mode']=='real' and config['identity']['provider']=='knowledgator-local'
policy=c01.read(c01.source_path(protocol['control_policy']))
for case_id in ('jev-002','jev-003'):
    assert case_id in dev
    output=BASE/'evidence'/f'targeted-D-{case_id}-{time.time_ns()}'
    output.mkdir()
    report=copy.deepcopy(example['report'])
    report.update(identity=config['identity'],sources=dict(report['sources'],prompt=config['prompt'],policy=config['policy']),split='development',planned_ids=[case_id],completed_ids=[case_id],run_id='c04-targeted-'+uuid.uuid4().hex,eligibility='inconclusive',git_revision=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip())
    report['environment'].update(concurrency=1,timeout_ms=5000,peak_memory_bytes=None)
    controls=example['inputs'];reserved=[item['id'] for item in controls if item['id'] in policy['controls']]
    report['injected_controls']=injected_inventory(reserved,protocol['control_policy'],policy)
    inputs=[project(cases[case_id],catalog)]+controls
    c01.structure(validation,'report',report);c01.verify_sources(report,protocol,split)
    path=output/'inputs.jsonl'
    with path.open('x',encoding='utf-8') as stream:
        stream.writelines(encode(item)+'\n' for item in inputs);stream.flush();os.fsync(stream.fileno())
    runner.write_json(output/'invocation.json',dict(script='script/classification_comparison/adapters/gliclass/evidence/targeted-development.py',script_sha256=c01.digest(Path(__file__)),config_sha256=c01.digest(config_path),selected_id=case_id,concurrency=1,attempts=1,timeout_ms=5000,cpu_affinity=sorted(os.sched_getaffinity(0)),scope='development_only',reason='Isolate masks after earlier prefix timeout; do not pool with previous batches'))
    runner.write_json(output/'plan.json',dict(run_id=report['run_id'],identity=report['identity'],sources=report['sources'],planned_ids=[case_id],selected_ids=[case_id],control_ids=report['control_ids'],injected_controls=report['injected_controls'],contract_version=report['contract_version'],input=inventory(path),concurrency=1,attempts=1))
    def publish(items,obs,decisions,prefix=False):
        runner.write_report(output,report.copy(),items,obs,decisions,validation,protocol,split,catalog,cases,policy,prefix)
    with Journal(output,report['run_id'],inputs,report['injected_controls'],publish) as journal:
        obs,decisions=runner.run_batch(inputs,config,report,catalog,validation,journal,policy)
        publish(inputs,obs,decisions);journal.event('finished',decisions=len(decisions))
    for name in ('snapshot.json','runtime-freeze.txt'):
        shutil.copyfile(BASE/'.cache'/name,output/name)
    r=c01.read(output/'report.json');main=next(o for o in obs if o['id']==case_id)
    print(json.dumps(dict(output=str(output.relative_to(ROOT)),id=case_id,choices=main['choices'],elapsed_ms=main['elapsed_ms'],temperature=main['temperature_state'],requests=main['requests'],questions=main['questions'],eligibility=r['eligibility'])),flush=True)
