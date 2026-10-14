"""Real authenticated Task API + managed GPT context projection after process exit."""
from pathlib import Path
from datetime import datetime,timezone,timedelta
import json,os,subprocess,sys,time
from urllib.request import Request,urlopen
from urllib.error import HTTPError
SOURCE=Path(os.environ.get('NERELAN_CONTEXT_PROBE_SOURCE',str(Path.cwd())))
ROOT=Path(os.environ['NERELAN_CONTEXT_PROBE_ROOT'])
sys.path.insert(0,str(SOURCE if sys.argv[1]=='prepare' else ROOT/'source'))
from reverse_agent.platform_v1.run_store import TaskStore
from reverse_agent.platform_v1.task_service import _default_task_db_path
from reverse_agent.platform_v1.codex_executor import CodexExecutor,probe_codex_readiness
from reverse_agent.platform_v1.trusted_host import CombinedTrustedHost,_resolve_trusted_authority_sha,_resolve_trusted_planning_sha
from reverse_agent.platform_v1.control_store import PlatformControlStore
from reverse_agent.model_access.store import ModelProfileStore
from reverse_agent.model_access.os_vault import default_vault_adapter

def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],text=True).strip()
phase=sys.argv[1]
ROOT.mkdir(exist_ok=True)
head=git(SOURCE,'rev-parse','HEAD')
if phase=='prepare' and git(SOURCE,'status','--porcelain'):raise RuntimeError('probe_requires_frozen_host_head')
repo=ROOT/'source'
if phase=='prepare':
    if repo.exists():raise RuntimeError('probe_identity_exists')
    subprocess.run(['git','clone','--quiet','--no-local','--no-checkout',str(SOURCE),str(repo)],check=True)
    subprocess.run(['git','-C',str(repo),'config','core.longpaths','true'],check=True)
    subprocess.run(['git','-C',str(repo),'checkout','--quiet','--detach',head],check=True)
    subprocess.run(['git','-C',str(repo),'remote','set-url','origin','https://github.com/dddd2024/Nerelan.git'],check=True)
os.environ['REVERSE_AGENT_REPO_DIR']=str(repo)
os.environ['REVERSE_AGENT_TASK_WORKSPACE_ROOT']=str(ROOT/'workspaces')
os.environ['REVERSE_AGENT_AUTONOMOUS']='0'
store=TaskStore(str(ROOT/'tasks.sqlite3'))
models=ModelProfileStore(state_path=Path(_default_task_db_path()).with_name('model_setup_state.json'),vault=default_vault_adapter())
host=CombinedTrustedHost(store=models,task_store=store,codex_readiness_probe=lambda:probe_codex_readiness(),
                         model_control_port=0,task_api_port=0,
                         execution_authority_sha=_resolve_trusted_authority_sha(),planning_sha=_resolve_trusted_planning_sha())
def factory(**kwargs):
    kwargs.update(timeout=90,sandbox='read-only')
    return CodexExecutor(**kwargs)
host._router.replace('codex',factory)
started=time.time()
host.start()
cap=[]
host._local_client_session.deliver(cap.append)
def request(path,payload=None):
    req=Request(host.task_api_url+path,data=json.dumps(payload).encode() if payload is not None else None,
                headers={'Content-Type':'application/json','X-Nerelan-Client-Capability':cap[0]})
    try:
        with urlopen(req,timeout=180) as response:return json.loads(response.read())
    except HTTPError as error:
        from reverse_agent.platform_v1.codex_protocol import public_text
        fault=json.loads(error.read(8192))
        record={'http_status':error.code,'code':public_text(str(fault.get('code') or fault.get('error')),500),'phase':phase}
        (ROOT/'http-rejection.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
        print(json.dumps(record),flush=True)
        raise
try:
    if phase=='prepare':
        goal=request('/api/goals',{'title':'Context restart live probe','objective':'Read persisted, newly generated Goal and Run identities after process restart.',
            'repository':'dddd2024/Nerelan','idempotency_key':'context-optimization-live-v1','executor_kind':'codex',
            'orchestration_mode':'single','binding_ref':'chatgpt-gpt'})
        goal=request('/api/goals/'+goal['id']+'/plan',{'expected_revision':goal['revision'],'tasks':[
            {'id':'T001','title':'Report context identities','instruction':'Do not edit files or use tools. Read only the appended Durable Context Packet. Return exactly one JSON object with goal_id, goal_revision, artifact_digest, checkpoint_run_id and git_head. For checkpoint_run_id use ref of the checkpoint source. Include no extra text.'}]})
        goal=request('/api/goals/'+goal['id']+'/approve',{'expected_revision':goal['revision']})
        now=datetime.now(timezone.utc)
        window=request('/api/windows/activate',{'policy_id':'context-restart-live','policy_revision':1,'owner_identity':'dddd2024',
            'starts_at':(now-timedelta(seconds=1)).isoformat(),'expires_at':(now+timedelta(minutes=30)).isoformat(),
            'repositories':['dddd2024/Nerelan'],'capabilities':['execute_task','validate_task'],
            'max_concurrent_tasks':1,'max_tasks':1,'max_retries':0,'confirmation':'ACTIVATE'})
        goal=request('/api/goals/'+goal['id']+'/launch',{'expected_revision':goal['revision'],'window_id':window['id']})
        links=PlatformControlStore(store).list_goal_tasks(goal['id'])
        record={'host_head':head,'source_head':git(repo,'rev-parse','HEAD'),'goal_id':goal['id'],'goal_revision':goal['revision'],
                'artifact_digest':goal['artifact_digest'],'task_id':links[0]['task_id'],'window_id':window['id'],
                'prepare_pid':os.getpid(),'status':'PREPARED_NO_MODEL_CALL','cash_cost':None,'quota_remaining':None}
        for index in range(80):
            store.add_event(record['task_id'],event_type='VALIDATED',title=f'Controlled historical fixture {index}',
                description=(f'Fixture decision {index}: retain source references and independently verify acceptance. ' * 60))
        record['history_origin']='CONTROLLED_STRESS_FIXTURE_NOT_REAL_PAST_MODEL_WORK'
        (ROOT/'prepared.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
    else:
        record=json.loads((ROOT/'prepared.json').read_text(encoding='utf-8'))
        if record['host_head']!=head or record['prepare_pid']==os.getpid():raise RuntimeError('probe_restart_identity_invalid')
        base='/api/tasks/'+record['task_id']+'/context/'
        packet=request(base+'packet',{})
        snapshot=packet['retrieval']['snapshot_digest']
        if phase=='summarize':
            summary=request(base+'summary',{'expected_snapshot':snapshot,'timeout':90})
            record.update(summary_status=summary['status'],summary_error=summary.get('error'),
                summary_usage=summary.get('usage'),summary_executor=summary.get('executor_kind'),
                summary_model=summary.get('model_id'),summary_pid=os.getpid(),
                summary_digest=__import__('hashlib').sha256(str(summary.get('summary','')).encode()).hexdigest())
            if summary['status']!='COMPLETED':
                (ROOT/'summary-failure.json').write_text(json.dumps(record,indent=2),encoding='utf-8',newline='\n')
                raise RuntimeError('live_summary_not_completed')
            handoff=request(base+'handoff',{'expected_snapshot':snapshot,'from_agent':'planner-summary','to_agent':'gpt-reviewer'})
            record['handoff_id']=handoff['handoff_id']
            record['summary_wall_seconds']=time.time()-started
            (ROOT/'summarized.json').write_text(json.dumps(record,indent=2),encoding='utf-8',newline='\n')
        elif phase=='recover':
            previous=json.loads((ROOT/'summarized.json').read_text(encoding='utf-8'))
            if previous['summary_pid']==os.getpid():raise RuntimeError('requires_new_process')
            restored=request(base+'recover',{'handoff_id':previous['handoff_id'],'agent_id':'gpt-reviewer'})
            restored_packet=restored['packet']
            if 'advisory_summary' not in restored_packet:raise RuntimeError('summary_not_recovered')
            from reverse_agent.platform_v1.agent_planner import run_planner_cli
            binding=models.get_binding_public('chatgpt-gpt')
            output=run_planner_cli(executor_kind='codex',model_id=binding['model_id'],repo_dir=str(repo),timeout=90,
                prompt='Do not use tools or edit files. Read only this fresh non-authoritative recovered context. '
                'Return exactly one JSON object with task_id, goal_id, goal_revision, git_head, authority. '
                'Include no markdown.\n'+json.dumps(restored_packet,ensure_ascii=False))
            supplied=json.loads(output.text)
            expected={'task_id':record['task_id'],'goal_id':record['goal_id'],
                'goal_revision':record['goal_revision'],'git_head':record['source_head'],'authority':'NONE'}
            found=request(base+'retrieve',{'expected_snapshot':restored_packet['retrieval']['snapshot_digest'],
                'query':'Fixture decision 79','budget_bytes':4096})
            record={**previous,'recover_pid':os.getpid(),'reply':supplied,'expected':expected,
                'matched_context_facts':supplied==expected,'recovered_summary':True,
                'packet_bytes':len(__import__('reverse_agent.platform_v1.context_builder',fromlist=['render_context_packet']).render_context_packet(restored_packet).encode()),
                'retrieval_matches':len(found['matches']),'retrieval_bytes':len(__import__('reverse_agent.platform_v1.context_builder',fromlist=['render_context_packet']).render_context_packet(found).encode()),
                'recover_usage':output.usage,'status':'LIVE_NATIVE_SUMMARY_AND_CROSS_AGENT_PROCESS_RECOVERY',
                'recover_wall_seconds':time.time()-started,'cash_cost':None,'quota_remaining':None}
            request('/api/windows/'+record['window_id']+'/stop',{'reason':'bounded optimization probe finished'})
            (ROOT/'result.json').write_text(json.dumps(record,indent=2),encoding='utf-8',newline='\n')
            if supplied!=expected:raise RuntimeError('context_fact_mismatch')
    print(json.dumps({k:record.get(k) for k in ('status','host_head','summary_status','matched_context_facts','packet_bytes','summary_wall_seconds')}))
finally:
    host.stop()
    store._conn.close()
