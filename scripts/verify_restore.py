"""Restore the committed snapshot and rebuild with a fresh venv from cached wheels."""
from pathlib import Path
import argparse, subprocess, json, os, hashlib, datetime, sys
ROOT=Path(__file__).resolve().parents[1]

def run(args,cwd=ROOT,env=None,log=None):
    if log:
        with log.open('w') as f:subprocess.run(args,cwd=cwd,env=env,check=True,stdout=f,stderr=subprocess.STDOUT)
    else:subprocess.run(args,cwd=cwd,env=env,check=True)

def main():
    p=argparse.ArgumentParser();p.add_argument('--bundle');p.add_argument('--rebuild',action='store_true');a=p.parse_args()
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
    run([sys.executable,str(destination/'scripts/ingest.py')],cwd=destination)
    rebuild=False
    if a.rebuild:
        env=dict(os.environ);env['UV_CACHE_DIR']=str(ROOT/'build/uv-cache');env['XDG_CACHE_HOME']=str(destination/'build/cache')
        base_python=subprocess.check_output([str(ROOT/'.venv/bin/python'),'-c','import sys; print(sys._base_executable)'],text=True).strip()
        run(['uv','venv','--python',base_python,str(destination/'.venv')],env=env)
        run(['uv','pip','install','--offline','--python',str(destination/'.venv/bin/python'),'--only-binary=:all:','-r',str(destination/'environment/requirements.lock')],env=env)
        run([str(destination/'project'),'build'],cwd=destination,env=env,log=destination/'build/full-rebuild.log')
        run([str(destination/'project'),'validate','--git-objects'],cwd=destination,env=env)
        original=json.loads((ROOT/'deliverables/current/analysis/resolved.json').read_text())
        restored=json.loads((destination/'deliverables/current/analysis/resolved.json').read_text())
        assert original==restored,'Resolved geometry changed in restored checkout'
        assert (destination/'canon/measurements.json').read_bytes()==(ROOT/'canon/measurements.json').read_bytes()
        rebuild=True
    report={'status':'PASS','kind':kind,'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=destination,text=True).strip(),
        'destination':str(destination.relative_to(ROOT)),'archives':archive_results,'snapshot_files_checked':len(manifest['files']),
        'extraction_from_repository_only':True,'Downloads_accessed':False,'fresh_environment_and_full_rebuild':rebuild,
        'resolved_geometry_agrees':True if rebuild else None,'physical_fit':'NOT PERFORMED','off_machine_backup':False}
    out=ROOT/'docs/validation/restore_check.json';reports=json.loads(out.read_text()) if out.exists() else {'runs':[]};reports['runs'].append(report)
    out.write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(report,indent=2))

if __name__=='__main__':main()
