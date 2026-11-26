"""Deterministic projection over already sanitized context; no provider calls."""
from __future__ import annotations

import copy
import re
from typing import Any

from .context_builder import ContextBuilderError, _canonical_digest, render_context_packet

DERIVED_CONTEXT_CATEGORIES = frozenset({'ContextSummary', 'ContextHandoff'})
SUMMARY_PRESSURE_BYTES = 65536


def scope_digest(packet: dict) -> str:
    goal = packet['goal']
    return _canonical_digest({'task_id':packet['task']['id'], 'repository':packet['task']['repository'],
        'execution_id':packet['task']['execution_id'], 'goal':None if goal is None else
        {key:goal[key] for key in ('id','revision','artifact_digest')}, 'git':packet['git'],
        'visible_tasks':sorted(task['id'] for task in packet['tasks']),
        'visibility_digest':packet.get('visibility_digest')})


def context_catalog(packet: dict) -> list[dict]:
    """Stable opaque references; original rows remain in the existing store."""
    entries = [{'kind':'history', 'ref':item['id'], 'digest':_canonical_digest(item), 'content':item}
               for item in packet['history']]
    entries += [{'kind':item['kind'], 'ref':item['ref'], 'digest':item['digest'], 'content':item}
                for item in packet['sources']]
    if packet['goal'] is not None:
        entries.append({'kind':'goal_text','ref':packet['goal']['id'],
                        'digest':_canonical_digest(packet['goal']), 'content':packet['goal']})
    return sorted(entries, key=lambda item:(item['kind'],item['ref'],item['digest']))


def snapshot_digest(packet: dict) -> str:
    return _canonical_digest({'scope':scope_digest(packet), 'catalog':context_catalog(packet),
                              'tasks':packet['tasks']})


def _clip(text: str, maximum: int) -> str:
    return text.encode('utf-8')[:maximum].decode('utf-8',errors='ignore')


def retrieve_context(packet: dict, *, expected_snapshot: str, query: str = '',
                     refs: tuple[str, ...] = (), budget_bytes: int = 4096, limit: int = 8) -> dict:
    """Read only caller-visible projection; never open evidence or hidden rows."""
    if expected_snapshot != snapshot_digest(packet):
        raise ContextBuilderError('context_snapshot_stale')
    if (not isinstance(query,str) or len(query.encode()) > 1024 or type(limit) is not int
            or not 1 <= limit <= 32 or type(budget_bytes) is not int or not 512 <= budget_bytes <= 65536
            or not isinstance(refs,tuple) or len(refs)>32 or any(not isinstance(ref,str) for ref in refs)):
        raise ContextBuilderError('context_invalid_argument')
    catalog = context_catalog(packet)
    if not set(refs) <= {item['ref'] for item in catalog}:
        raise ContextBuilderError('context_reference_unavailable')
    terms = sorted(set(re.findall(r'\w+',query.casefold())))
    candidates=[]
    for item in catalog:
        text=render_context_packet(item['content']).casefold()
        score=sum(text.count(term) for term in terms)
        if item['ref'] in refs or (terms and score) or (not terms and not refs):
            candidates.append((0 if item['ref'] in refs else 1,-score,item))
    candidates.sort(key=lambda row:(row[0],row[1],row[2]['kind'],row[2]['ref'],row[2]['digest']))
    result={'authority':'NONE','snapshot_digest':expected_snapshot,'matches':[], 'omitted_matches':len(candidates)}
    for _,_,item in candidates[:limit]:
        proposed={**result,'matches':[*result['matches'],copy.deepcopy(item)]}
        proposed['omitted_matches']=len(candidates)-len(proposed['matches'])
        if len(render_context_packet(proposed).encode()) <= budget_bytes:
            result=proposed
        elif not result['matches']:
            # A bounded excerpt remains discoverable even when one row is huge.
            excerpt={key:item[key] for key in ('kind','ref','digest')}
            excerpt['truncated']=True
            excerpt['content_excerpt']=''
            proposed={**result,'matches':[excerpt],'omitted_matches':len(candidates)-1}
            available=budget_bytes-len(render_context_packet(proposed).encode())
            excerpt['content_excerpt']=_clip(render_context_packet(item['content']), max(0,available//2))
            if len(render_context_packet(proposed).encode()) <= budget_bytes:
                result=proposed
    return result


def compact_context(packet: dict, *, budget_bytes: int) -> dict:
    """Fit by explicit priority and indexed omission, never by model summarization."""
    if type(budget_bytes) is not int or not 1024 <= budget_bytes <= 262144:
        raise ContextBuilderError('context_budget_invalid')
    snapshot=snapshot_digest(packet)
    original_bytes=len(render_context_packet(packet).encode())
    catalog=context_catalog(packet)
    compact=copy.deepcopy(packet)
    compact['schema_version']=2
    compact['retrieval']={'snapshot_digest':snapshot,'scope_digest':scope_digest(packet),
                          'catalog_digest':_canonical_digest(catalog),'item_count':len(catalog)}
    compact['compression']={'algorithm':'priority_utf8_v1','original_bytes':original_bytes,
        'history_omitted':0,'sources_omitted':0,'goal_text_omitted':False,'descriptions_clipped':0}
    # Triggering is deterministic guidance; provider-free execution cannot initiate a job.
    compact['summary_trigger']={'needed':original_bytes > SUMMARY_PRESSURE_BYTES and len(packet['history'])>=32,
        'reason':'history_pressure' if original_bytes > SUMMARY_PRESSURE_BYTES and len(packet['history'])>=32 else 'below_threshold',
        'automatic_model_calls':False,'input_snapshot_digest':snapshot}
    if len(render_context_packet(compact).encode()) <= budget_bytes:
        return compact
    retained=[source for source in compact['sources'] if source['kind'] in {'goal','checkpoint','git'}
              or (source['kind']=='task' and source['ref']==compact['task']['id'])]
    compact['compression']['sources_omitted']=len(compact['sources'])-len(retained)
    compact['sources']=retained
    history=compact['history']
    for event in history:
        shortened=_clip(event['description'],128)
        compact['compression']['descriptions_clipped']+=shortened!=event['description']
        event['description']=shortened
        event['title']=_clip(event['title'],64)
    if len(render_context_packet(compact).encode()) <= budget_bytes:
        return compact
    # Deterministic recent critical events first. Every omitted event is in catalog.
    critical=re.compile(r'FAIL|BLOCK|INTERRUPT|CANCEL|ERROR|REJECT|ESCALAT|DECISION',re.I)
    priority=sorted(enumerate(history),key=lambda pair:
        (0 if critical.search(pair[1]['type']+' '+pair[1]['title']) else 1,-pair[0]))
    # The Goal's requirements and plan outrank activity history: shed history
    # (keeping critical and recent events) before any goal text is dropped.
    compact['history']=[]
    compact['compression']['history_omitted']=len(history)
    if len(render_context_packet(compact).encode()) <= budget_bytes:
        return _fill_history(compact, history, priority, budget_bytes)
    if compact['goal']:
        had_md=False
        for key in ('spec_markdown','plan_markdown'):
            if compact['goal'].get(key):
                had_md=True
            if key in compact['goal']:
                compact['goal'][key]=''
        if had_md:
            compact['compression']['goal_text_omitted']=True
    compact['history']=[]
    compact['compression']['history_omitted']=len(history)
    if len(render_context_packet(compact).encode())>budget_bytes:
        for task in [compact['task'],*compact['tasks']]:task['title']=_clip(task['title'],64)
        if len(render_context_packet(compact).encode())>budget_bytes and compact['goal'] and compact['goal'].get('objective'):
            raw_obj=compact['goal']['objective']
            prior_goal_omitted=compact['compression']['goal_text_omitted']
            compact['goal']['objective']=''
            compact['compression']['goal_text_omitted']=True
            base_bytes=len(render_context_packet(compact).encode())
            slack=budget_bytes-base_bytes
            obj_restored=False
            if slack<=0:
                for task in [compact['task'],*compact['tasks']]:task['title']=''
                base_bytes=len(render_context_packet(compact).encode())
                slack=budget_bytes-base_bytes
                if slack>0:
                    compact['goal']['objective']=raw_obj
                    compact['compression']['goal_text_omitted']=prior_goal_omitted
                    if len(render_context_packet(compact).encode())<=budget_bytes:
                        obj_restored=True
                    else:
                        compact['goal']['objective']=''
                        compact['compression']['goal_text_omitted']=True
            if slack>0 and not obj_restored:
                crit_pairs=[(i,e) for i,e in priority if critical.search(e['type']+' '+e['title'])]
                reserved_critical=0
                if crit_pairs:
                    compact['history']=[e for _,e in sorted(crit_pairs)]
                    with_crit_bytes=len(render_context_packet(compact).encode())
                    compact['history']=[]
                    crit_bytes=max(0,with_crit_bytes-base_bytes)
                    reserved_critical=min(slack//3,crit_bytes)
                target_limit=budget_bytes-reserved_critical
                lo,hi,best=1,len(raw_obj.encode('utf-8'))-1,''
                while lo<=hi:
                    mid=(lo+hi)//2
                    cand=_clip(raw_obj,mid)
                    compact['goal']['objective']=cand
                    if len(render_context_packet(compact).encode())<=target_limit:
                        best=cand
                        lo=mid+1
                    else:
                        hi=mid-1
                compact['goal']['objective']=best
        if len(render_context_packet(compact).encode())>budget_bytes:
            for task in [compact['task'],*compact['tasks']]:task['title']=''
        if len(render_context_packet(compact).encode())>budget_bytes:
            raise ContextBuilderError('context_budget_insufficient')
    return _fill_history(compact, history, priority, budget_bytes)


def _fill_history(compact: dict, history: list, priority: list, budget_bytes: int) -> dict:
    """Greedily re-add events in priority order while the packet fits."""
    selected=[]
    for index,event in priority:
        selected.append((index,event))
        compact['history']=[e for _,e in sorted(selected)]
        compact['compression']['history_omitted']=len(history)-len(selected)
        if len(render_context_packet(compact).encode())>budget_bytes:
            selected.pop()
    compact['history']=[e for _,e in sorted(selected)]
    compact['compression']['history_omitted']=len(history)-len(selected)
    return compact
