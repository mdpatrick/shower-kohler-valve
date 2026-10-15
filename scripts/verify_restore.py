"""Restore the committed snapshot and rebuild with a fresh venv from cached wheels."""
from pathlib import Path
import argparse, subprocess, json, os, hashlib, datetime, sys
ROOT=Path(__file__).resolve().parents[1]

def run(args,cwd=ROOT,env=None,log=None):
    if log:
        log.parent.mkdir(parents=True,exist_ok=True)
        with log.open('w') as f:subprocess.run(args,cwd=cwd,env=env,check=True,stdout=f,stderr=subprocess.STDOUT)
    else:subprocess.run(args,cwd=cwd,env=env,check=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle');p.add_argument('--rebuild',action='store_true');p.add_argument('--report',help='Optional receipt path outside the committed snapshot');a=p.parse_args()
    kind='bundle' if a.bundle else 'clone';destination=ROOT/'build'/('restore-'+kind+'-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S'))
    source=Path(a.bundle).resolve() if a.bundle else ROOT
    run(['git','clone','--no-hardlinks',str(source),str(destination)])
    run(['git','fsck','--full'],cwd=destination)
    inputs=json.loads((destination/'canon/inputs.json').read_text());archive_results=[]
    for i in inputs['inputs']:
        blob=subprocess.check_output(['git','show','HEAD:'+i['repository_path']],cwd=destination)
        disk=(destination/i['repository_path']).read_bytes()
        assert len(blob)==len(disk)==i['size_bytes'] and hashlib.sha256(blob).hexdigest()==hashlib.sha256(disk).hexdigest()==i['sha256']
        archive_results.append({'id':i['id'],'sha256':i['sha256'],'full_blob_bytes':len(blob),'status':'PASS'})
    manifest=json.loads((destination/'deliverables/current/manifest.json').read_text())
    for entry in manifest['files']:assert hashlib.sha256((destination/entry['path']).read_bytes()).hexdigest()==entry['sha256'],entry['path']
    canon_before={str(f.relative_to(destination)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (destination/'canon').rglob('*') if f.is_file()}
    fit_path=destination/'deliverables/current/fabrication/fit-trial/design_report.json'
    fit_before=json.loads(fit_path.read_text()) if fit_path.exists() else None
    run([sys.executable,str(destination/'scripts/ingest.py')],cwd=destination)
    rebuild=False;fit_rebuild=None
    if a.rebuild:
        env=dict(os.environ);env['UV_CACHE_DIR']=str(ROOT/'build/uv-cache');env['XDG_CACHE_HOME']=str(destination/'build/cache')
        base_python=subprocess.check_output([str(ROOT/'.venv/bin/python'),'-c','import sys; print(sys._base_executable)'],text=True).strip()
        run(['uv','venv','--python',base_python,str(destination/'.venv')],env=env)
        run(['uv','pip','install','--offline','--python',str(destination/'.venv/bin/python'),'--only-binary=:all:','-r',str(destination/'environment/requirements.lock')],env=env)
        run([str(destination/'project'),'build'],cwd=destination,env=env,log=destination/'build/full-rebuild.log')
        if fit_before:
            run([str(destination/'project'),'prepare-fit-trial'],cwd=destination,env=env,log=destination/'build/fit-trial-rebuild.log')
            fit_after=json.loads(fit_path.read_text())
            assert fit_after['design']==fit_before['design'],'Restored fit-trial dimensions changed'
            old_parts={p['id']:p for p in fit_before['parts']}
            assert set(old_parts)=={p['id'] for p in fit_after['parts']},'Restored part set changed'
            for part in fit_after['parts']:
                assert part['sha256']['stl']==old_parts[part['id']]['sha256']['stl'],part['id']+' STL geometry changed'
            fit_rebuild={'revision':fit_after['revision'],'part_sets':len(old_parts),'STLs_byte_identical':True,
                         'stages':['analysis','blender','documents','audit'],
                         'audit_status':json.loads((fit_path.parent/'audit.json').read_text())['status']}
        run([str(destination/'project'),'validate','--git-objects'],cwd=destination,env=env)
        original=json.loads((ROOT/'deliverables/current/analysis/resolved.json').read_text())
        restored=json.loads((destination/'deliverables/current/analysis/resolved.json').read_text())
        assert original==restored,'Resolved geometry changed in restored checkout'
        assert (destination/'canon/measurements.json').read_bytes()==(ROOT/'canon/measurements.json').read_bytes()
        canon_after={str(f.relative_to(destination)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (destination/'canon').rglob('*') if f.is_file()}
        assert canon_after==canon_before,'Rebuild changed accepted canon'
        rebuild=True
    report={'status':'PASS','kind':kind,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=destination,text=True).strip(),
        'destination':str(destination.relative_to(ROOT)),'archives':archive_results,'snapshot_files_checked':len(manifest['files']),
        'extraction_from_repository_only':True,'Downloads_accessed':False,'fresh_environment_and_full_rebuild':rebuild,
        'current_fit_trial_rebuild':fit_rebuild,'all_canon_unchanged':True if rebuild else None,
        'resolved_geometry_agrees':True if rebuild else None,'physical_fit':'NOT PERFORMED','off_machine_backup':False,
        'bundle_sha256':hashlib.sha256(source.read_bytes()).hexdigest() if a.bundle else None}
    out=ROOT/(a.report or 'docs/validation/restore_check.json');out.parent.mkdir(parents=True,exist_ok=True)
    reports=json.loads(out.read_text()) if out.exists() else {'runs':[]};reports['runs'].append(report)
    out.write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
