"""Strict, history-preserving observation import. Never interprets silence as confirmation."""
from pathlib import Path
import json,datetime,copy,statistics,sys,hashlib,math
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'src/review'))
from requests import requests

def import_response(path,root=ROOT,dry_run=False):
    payload=json.loads(Path(path).read_text());canonpath=root/'canon/measurements.json';canon=json.loads(canonpath.read_text())
    if payload.get('project_id')!=canon['project_id']:raise ValueError('Wrong project_id')
    if payload.get('review_revision')!=canon['revision']:raise ValueError('Stale/wrong review_revision; use the current worksheet')
    resolved=json.loads((root/'data/derived/resolved.json').read_text());definitions={f['id']:f for g in requests(resolved) for f in g['fields']}
    observations=payload.get('observations',[])
    if not isinstance(observations,list):raise ValueError('observations must be a list')
    seen=set();validated=[]
    for obs in observations:
        id=obs.get('measurement_id')
        if id not in definitions or id in seen:raise ValueError('Unknown/duplicate measurement ID: '+str(id))
        seen.add(id);unit=obs.get('unit');factors={'mm':1,'cm':10,'in':25.4}
        if unit not in factors:raise ValueError('Unsupported unit for '+id)
        raw=obs.get('raw_readings')
        if not isinstance(raw,list) or not raw or any(isinstance(x,bool) or not isinstance(x,(int,float)) or not 0<=x*factors[unit]<5000 for x in raw):raise ValueError('Invalid raw_readings for '+id)
        if not obs.get('method','').strip() or not obs.get('date'):raise ValueError('Date and method required for '+id)
        datetime.date.fromisoformat(obs['date'])
        values=[x*factors[unit] for x in raw];value=statistics.median(values);span=max(values)-min(values)
        conflict=span>2*definitions[id]['useful_accuracy_mm']
        bound=obs.get('uncertainty_mm')
        if not isinstance(obs.get('approximate',False),bool):raise ValueError('approximate must be a boolean')
        if bound is not None and (isinstance(bound,bool) or not isinstance(bound,(int,float)) or not math.isfinite(bound) or bound<0):raise ValueError('Invalid uncertainty bound')
        validated.append(dict(id=id,component='see worksheet',state='current_physical_observation',datum=definitions[id]['contacts'],purpose=definitions[id]['label'],
            raw_readings=raw,raw_unit=unit,values_mm=values,value_mm=value,method=obs['method'],source='user measurement response',date=obs['date'],photo_ref=obs.get('photo_ref',''),
            date_basis=obs.get('date_basis','measurement date'),notes=obs.get('notes',''),approximate=obs.get('approximate',False),source_ref=obs.get('source_ref',''),uncertainty_mm=bound,repeat_span_mm=span,status='conflicting' if conflict else 'user-confirmed',
            reduction='median of repeat readings; repeat span does not establish measurement accuracy',role=definitions[id]['role'],correction_reason=obs.get('correction_reason')))
    out=copy.deepcopy(canon);accepted={m['id']:m for m in out['measurements'] if m['status']=='user-confirmed'};added=[];conflicts=[]
    for m in validated:
        old=accepted.get(m['id'])
        if old and abs(old['value_mm']-m['value_mm'])>1e-9:
            if not m.get('correction_reason'):
                m['status']='conflicting';m['conflicts_with_accepted_value_mm']=old['value_mm'];conflicts.append(m['id'])
            elif m['status']=='user-confirmed':old['status']='superseded';old['superseded_reason']=m['correction_reason']
        elif old and m['status']=='user-confirmed':continue
        if m['status']=='conflicting' and m['id'] not in conflicts:conflicts.append(m['id'])
        out['measurements'].append(m);added.append(m['id'])
        if m['status']=='user-confirmed':accepted[m['id']]=m
    def derived(id,value,inputs,formula,role='fitting input'):
        old=accepted.get(id)
        if old and abs(old['value_mm']-value)<1e-9:return
        if old:old['status']='superseded';old['superseded_reason']='Derived inputs revised'
        record=dict(id=id,component='derived',state='current_physical_observation',status='user-confirmed',value_mm=value,raw_unit='mm',raw_readings=[],
            source='derived from accepted raw observations',inputs=inputs,method=formula,date=max(accepted[x]['date'] for x in inputs),uncertainty_mm=None,
            note='Derived relation, not an independent second piece of evidence',role=role)
        out['measurements'].append(record);accepted[id]=record;added.append(id)
    if all(x in accepted for x in ['M01-O','M01-I']):
        if accepted['M01-O']['value_mm']<=accepted['M01-I']['value_mm']:raise ValueError('Outer tip span must exceed inner gap')
        derived('M01',(accepted['M01-O']['value_mm']+accepted['M01-I']['value_mm'])/2,['M01-O','M01-I'],'(outside span + inside gap)/2')
    if all(x in accepted for x in ['M11-G','M11-SWD','M11-NED']):
        derived('M11-CC',accepted['M11-G']['value_mm']+(accepted['M11-SWD']['value_mm']+accepted['M11-NED']['value_mm'])/2,
                ['M11-G','M11-SWD','M11-NED'],'nearest-edge gap + (SW diameter + NE diameter)/2')
    if all(x in accepted for x in ['M11-R','M11-NED']):
        derived('M11-NERC',accepted['M11-R']['value_mm']+accepted['M11-NED']['value_mm']/2,
                ['M11-R','M11-NED'],'right hole-edge gap + NE diameter/2')
    if all(x in accepted for x in ['M11-UT','M11-UD']):
        derived('M11-UC',accepted['M11-UT']['value_mm']+accepted['M11-UD']['value_mm']/2,
                ['M11-UT','M11-UD'],'top edge gap + upper opening diameter/2')
    if all(x in accepted for x in ['M12-G','M12-UD','M12-LD']):
        derived('M12-CCY',accepted['M12-G']['value_mm']+(accepted['M12-UD']['value_mm']+accepted['M12-LD']['value_mm'])/2,
                ['M12-G','M12-UD','M12-LD'],'vertical inside-edge gap + (upper diameter + lower diameter)/2')
    if all(x in accepted for x in ['M06-YN','M12-LD']):
        derived('M12-LCB',accepted['M06-YN']['value_mm']+accepted['M12-LD']['value_mm']/2,
                ['M06-YN','M12-LD'],'bottom rim to lower bore inside edge + lower diameter/2')
    for which in ['SW','NE']:
        if all(x in accepted for x in ['M07-H','M07-G'+which]):
            z=accepted['M07-H']['value_mm']-accepted['M07-G'+which]['value_mm']
            if z<0:raise ValueError('Tip behind reference wall; verify block/gap measurement before import')
            derived('M07-'+which,z,['M07-H','M07-G'+which],'block height - underside-to-tip gap')
    for which,gap in [('UPPER','M10-GU'),('LOWER','M10-GL')]:
        if all(x in accepted for x in ['M10-H',gap]):
            z=accepted['M10-H']['value_mm']-accepted[gap]['value_mm']
            # A control tip can legitimately be recessed; its identity remains a separate check.
            derived('M10-'+which,z,['M10-H',gap],'block height - underside-to-as-found-tip gap',role='diagnostic cross-check; tip identity required')
    for prefix in ['M03-SW','M03-NE','M06']:
        for axis in ['X','Y']:
            near=prefix+'-'+axis+'N';far=prefix+'-'+axis+'F'
            if near in accepted and far in accepted and accepted[far]['value_mm']<=accepted[near]['value_mm']:raise ValueError('Far edge must exceed near edge: '+prefix+' '+axis)
    if not added and not payload.get('current_state_note') and not payload.get('group_notes'):return {'status':'no changes','revision':canon['revision']}
    newrev='R'+str(int(canon['revision'][1:])+1).zfill(3);out['revision']=newrev
    if added:out['note']='User-confirmed readings retain source units, endpoints and unknown uncertainty. Derived values are not independent evidence. Remaining assumptions are in design_decisions.json.'
    out['history'].append({'from_revision':canon['revision'],'to_revision':newrev,'accepted_or_recorded_ids':added,'conflicting_ids':conflicts,
        'response_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest(),'current_state_note':payload.get('current_state_note',''),'group_notes':payload.get('group_notes',{}),
        'date_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'physical_fit':'not established by measurement import'})
    if not dry_run:
        archive=root/'canon/measurement_responses';archive.mkdir(parents=True,exist_ok=True);(archive/(newrev+'.json')).write_text(json.dumps(payload,indent=2)+'\n')
        tmp=canonpath.with_suffix('.tmp');tmp.write_text(json.dumps(out,indent=2)+'\n');tmp.replace(canonpath)
        statepath=root/'canon/project_state.json';state=json.loads(statepath.read_text());state['revision']=newrev
        state['readiness'].update(geometric_fit='STALE - rebuild required',physical_fit='NOT PERFORMED',fabrication_approval='NOT GIVEN',installed_leak_test='NOT PERFORMED')
        state['latest_user_state_note']=payload.get('current_state_note','');statepath.write_text(json.dumps(state,indent=2)+'\n')
    return {'status':'validated dry run' if dry_run else 'imported; rebuild required','revision':newrev,'recorded_ids':added,'conflicts':conflicts}

if __name__=='__main__':print(json.dumps(import_response(sys.argv[1]),indent=2))
