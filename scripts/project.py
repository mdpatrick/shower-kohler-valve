#!/usr/bin/env python3
"""Small local command wrapper. Canon is input; generated outputs are never canon."""
from pathlib import Path
import argparse,hashlib,json,os,subprocess,sys,shutil,datetime,zipfile,socket,time,urllib.request
ROOT=Path(__file__).resolve().parents[1];os.chdir(ROOT)
BLENDER=os.environ.get('PROJECT_BLENDER','/Applications/Blender.app/Contents/MacOS/Blender')
SOURCE_GLOBS=['project','src/**/*','scripts/*.py','scripts/*.sh','canon/*.json','environment/requirements.lock','environment/three-package.json']
os.environ.setdefault('XDG_CACHE_HOME',str(ROOT/'build/cache'))
def read(p):return json.loads((ROOT/p).read_text())
def write(p,data):
    path=ROOT/p;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(data,indent=2)+'\n')
def sha(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def run(args,log=None):
    if log:
        with open(ROOT/'build'/log,'w') as f:
            result=subprocess.run(args,cwd=ROOT,stdout=f,stderr=subprocess.STDOUT)
        if result.returncode:raise RuntimeError('Failed; see build/'+log)
    else:subprocess.run(args,cwd=ROOT,check=True)
def fingerprint(patterns):
    paths=set()
    for pattern in patterns:
        paths.update(p for p in ROOT.glob(pattern) if p.is_file() and '__pycache__' not in p.parts)
    h=hashlib.sha256()
    for p in sorted(paths):h.update(str(p.relative_to(ROOT)).encode());h.update(sha(p).encode())
    return h.hexdigest()
def doctor():
    import platform,importlib.metadata
    libraries={}
    for lib in ['cadquery','cadquery-ocp','numpy','trimesh','reportlab','pypdf']:
        try:libraries[lib]=importlib.metadata.version(lib)
        except importlib.metadata.PackageNotFoundError:libraries[lib]='MISSING'
    result={'project_root':str(ROOT),'platform':platform.platform(),'python':sys.version.split()[0],'libraries':libraries,'blender':BLENDER,'blender_exists':Path(BLENDER).exists(),
            'raw_archives':[{k:i[k] for k in ['id','repository_path','size_bytes']} for i in read('canon/inputs.json')['inputs']],
            'physical_readiness':read('canon/project_state.json')['readiness']}
    print(json.dumps(result,indent=2));return result
def preserve_edits():
    mp=ROOT/'deliverables/current/manifest.json'
    if not mp.exists():return
    changed=[]
    for entry in read('deliverables/current/manifest.json').get('files',[]):
        p=ROOT/entry['path']
        if p.exists() and sha(p)!=entry['sha256']:changed.append(p)
    if changed:
        dest=ROOT/'deliverables/manual_edits'/datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        for p in changed:
            target=dest/p.relative_to(ROOT/'deliverables/current');target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,target)
        print('Preserved modified deliverables before rebuild:',dest.relative_to(ROOT))
def publish_manifest():
    try:commit=subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()
    except subprocess.CalledProcessError:commit=None
    files=[]
    for p in sorted((ROOT/'deliverables/current').rglob('*')):
        if p.is_file() and p.name!='manifest.json' and not p.name.endswith(('.blend1','.blend2')):
            files.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p),size_bytes=p.stat().st_size))
    write('deliverables/current/manifest.json',dict(project_id='shower-kohler-valve',revision=read('canon/measurements.json')['revision'],
        status='DRAFT_NOT_FOR_FABRICATION',source_commit=commit,source_commit_note='Commit present at build time; source_tree_hash includes current source/canon, avoiding future-commit circularity.',
        source_tree_hash=fingerprint(SOURCE_GLOBS),
        input_hashes={i['id']:i['sha256'] for i in read('canon/inputs.json')['inputs']},files=files,
        readiness=read('canon/project_state.json')['readiness']))
    return files
def build(force=False):
    (ROOT/'build').mkdir(exist_ok=True);preserve_edits();run([sys.executable,'scripts/ingest.py'])
    state=read('build/stages.json') if (ROOT/'build/stages.json').exists() else {}
    rev=read('canon/measurements.json')['revision']
    stages=[
      ('registration',['src/analysis/register.py','canon/scan_annotations.json','canon/measurements.json','canon/inputs.json'],['data/derived/registration.json'],[sys.executable,'src/analysis/register.py']),
      ('parameters',['src/analysis/resolve.py','canon/*.json','data/derived/registration.json'],['data/derived/resolved.json'],[sys.executable,'src/analysis/resolve.py']),
      ('cad',['src/cad/build_parts.py','data/derived/resolved.json'],['data/derived/cad/parts.json','deliverables/current/cad/CUSTOM-01_DRAFT_NOT_FOR_FABRICATION.step'],[sys.executable,'src/cad/build_parts.py']),
      ('analysis',['src/analysis/checks.py','src/analysis/depth.py','src/analysis/rough_in.py','data/derived/resolved.json','data/derived/cad/parts.json'],['deliverables/current/analysis/checks.json','deliverables/current/analysis/depth_stack.json'],[sys.executable,'src/analysis/checks.py']),
      ('blender',['src/blender/build_scene.py','src/blender/user_notes.py','data/derived/resolved.json','data/derived/registration.json','data/derived/cad/*','canon/inputs.json','deliverables/current/blender/user_notes.blend'],[f'deliverables/current/blender/installation_{rev}_DRAFT.blend','deliverables/current/review/views/coverage.png','deliverables/current/review/installation_DRAFT.glb'],[BLENDER,'--background','--factory-startup','--python-exit-code','1','--python','src/blender/build_scene.py']),
      ('review',['src/review/build_review.py','src/review/depth_view.py','src/review/requests.py','src/review/*.css','src/review/*.js','src/review/vendor/**/*','data/evidence/scan_quality/*','data/evidence/user/*-plate-front-caliper-*','deliverables/current/review/views/coverage.png','deliverables/current/review/view_geometry.json','deliverables/current/analysis/checks.json','deliverables/current/analysis/depth_stack.json'],['deliverables/current/review/index.html','deliverables/current/review/measurement_requests.json'],[sys.executable,'src/review/build_review.py']),
      ('pdf',['src/review/build_pdfs.py','src/review/requests.py','src/review/build_review.py','data/derived/resolved.json','deliverables/current/analysis/depth_stack.json','deliverables/current/review/views/*.png'],[f'deliverables/current/drawings/measurement_worksheet_{rev}.pdf',f'deliverables/current/drawings/profile_template_{rev}_DRAFT.pdf',f'deliverables/current/manual/repair_manual_{rev}_DRAFT.pdf'],[sys.executable,'src/review/build_pdfs.py'])]
    for name,inputs,outputs,cmd in stages:
        digest=fingerprint(inputs)
        prior=state.get(name,{}).get('outputs',{});expected=set(outputs)|set(prior)
        unchanged=not force and state.get(name,{}).get('fingerprint')==digest and all((ROOT/p).exists() and sha(ROOT/p)==prior.get(p) for p in expected)
        if unchanged:print(name+': unchanged')
        else:print(name+': building',flush=True);run(cmd,name+'.log')
        # Remember all files owned by the stage, so a deleted secondary export is stale too.
        extra={'registration':['data/derived/*-vertices.npy'], 'parameters':[],
          'cad':['data/derived/cad/*','deliverables/current/cad/*'],
          'analysis':['deliverables/current/analysis/checks.json','deliverables/current/analysis/registration.json','deliverables/current/analysis/resolved.json','deliverables/current/analysis/contractor_schedule.json'],
          'blender':['deliverables/current/blender/scene_check.json','deliverables/current/blender/wall_display_proxy.glb','deliverables/current/review/view_geometry.json']+[f'deliverables/current/review/views/{v}.png' for v in ['coverage','overview','control_depth','assembled','factory','neighbor','exploded','inner_front','inner_back','outer_front','outer_back','gasket','section_controls','section_studs']],
          'review':['deliverables/current/review/*.js','deliverables/current/review/*.css','deliverables/current/review/*.json','deliverables/current/review/vendor/**/*','deliverables/current/review/views/*measure.png','deliverables/current/review/views/inner_photo.png','deliverables/current/review/views/outer_photo.png','deliverables/current/review/views/depth_*.svg','deliverables/current/review/views/plate_scan_*.png','deliverables/current/manual/index.html'],
          'pdf':[f'deliverables/current/drawings/candidate_drawing_{rev}_DRAFT.pdf']}[name]
        owned=set(outputs)
        for pattern in extra:owned.update(str(p.relative_to(ROOT)) for p in ROOT.glob(pattern) if p.is_file())
        state[name]={'fingerprint':digest,'outputs':{p:sha(ROOT/p) for p in sorted(owned)}};write('build/stages.json',state)
    shutil.copy2(ROOT/'canon/source_register.json',ROOT/'deliverables/current/analysis/source_register.json')
    publish_manifest();print('Build finished. Physical fit and fabrication remain UNRESOLVED.')
def prepare_fabrication(stage='all',force=False):
    """Supplemental design revision reconciled explicitly with accepted measurements."""
    design=read('canon/fabrication_designs.json')
    if design['evidence_revision'] != read('canon/measurements.json')['revision'] or design['evidence_revision'] != read('data/derived/resolved.json')['revision']:
        raise ValueError('Fabrication design evidence is stale; reconcile accepted measurements and design before any stage.')
    preserve_edits();state=read('build/fabrication_stages.json') if (ROOT/'build/fabrication_stages.json').exists() else {}
    out='deliverables/current/fabrication/F005'
    stages=[
      ('cad',['src/fabrication/build.py','src/fabrication/mesh_check.py','canon/fabrication_designs.json','canon/measurements.json','data/derived/resolved.json','data/derived/registration.json','data/evidence/kohler-T14489-4.obj','data/evidence/kohler-T14491-4.obj'],[out+'/cad/*',out+'/reference/*',out+'/analysis.json',out+'/mesh_path_check.json','data/derived/fabrication_F005/*'],[sys.executable,'src/fabrication/build.py']),
      ('fit',['src/fabrication/reference_fit.py','data/derived/fabrication_F005/REF-*.brep','data/derived/resolved.json','data/derived/registration.json'],[out+'/reference_fit_check.json'],[sys.executable,'src/fabrication/reference_fit.py']),
      ('render',['src/fabrication/blender_scene.py','data/derived/fabrication_F005/*',f"deliverables/current/blender/installation_{design['evidence_revision']}_DRAFT.blend"],[out+'/views/pair_*.png',out+'/views/exploded_A.png',out+'/views/as_found_depth.png',out+'/views/measured_*.png',out+'/paired_escutcheons_F005_DRAFT.blend',out+'/blender_validation.json'],[BLENDER,'--background','--factory-startup','--python-exit-code','1','--python','src/fabrication/blender_scene.py']),
      ('documents',['src/fabrication/documents.py','src/fabrication/build.py','canon/fabrication_research.json','canon/fabrication_designs.json',out+'/analysis.json',out+'/blender_validation.json',out+'/mesh_path_check.json',out+'/reference_fit_check.json',out+'/views/pair_*.png',out+'/views/exploded_A.png'],[out+'/*.pdf',out+'/index.html',out+'/views/*.svg',out+'/views/*_diagram.png',out+'/document_validation.json',out+'/fit_report.md',out+'/research.json',out+'/quote_package_*.zip'],[sys.executable,'src/fabrication/documents.py'])]
    for name,inputs,patterns,cmd in stages:
        if stage not in ('all',name):continue
        digest=fingerprint(inputs);prior=state.get(name,{});files=prior.get('outputs',{})
        unchanged=not force and prior.get('fingerprint')==digest and files and all((ROOT/f).exists() and sha(ROOT/f)==h for f,h in files.items())
        if unchanged:print('fabrication '+name+': unchanged',flush=True);continue
        print('fabrication '+name+': building',flush=True);run(cmd,'fabrication_'+name+'.log')
        owned={str(p.relative_to(ROOT)) for pat in patterns for p in ROOT.glob(pat) if p.is_file() and not p.name.endswith('.blend1')}
        state[name]={'fingerprint':digest,'outputs':{p:sha(ROOT/p) for p in sorted(owned)}};write('build/fabrication_stages.json',state)
    publish_manifest()
    print('F005 preparation checkpoint saved. Permanent manufacturing release remains HOLD.')

def validate(git_objects=False):
    errors=[];input_results=[]
    for i in read('canon/inputs.json')['inputs']:
        p=ROOT/i['repository_path'];ok=p.exists() and sha(p)==i['sha256'] and p.stat().st_size==i['size_bytes']
        if git_objects:
            b=subprocess.check_output(['git','show','HEAD:'+i['repository_path']]);ok=ok and hashlib.sha256(b).hexdigest()==i['sha256'] and len(b)==i['size_bytes']
        input_results.append(dict(id=i['id'],status='PASS' if ok else 'FAIL',committed_bytes_checked=git_objects))
        if not ok:errors.append(i['id'])
    rev=read('canon/measurements.json')['revision']
    for p in ['deliverables/current/cad/cad_manifest.json','deliverables/current/blender/scene_check.json','deliverables/current/analysis/checks.json']:
        if not (ROOT/p).exists():errors.append('missing '+p);continue
        if read(p)['revision']!=rev:errors.append('stale '+p)
    mp=ROOT/'deliverables/current/manifest.json'
    if mp.exists():
        manifest=read('deliverables/current/manifest.json')
        if manifest['revision']!=rev:errors.append('stale manifest revision')
        current_source=fingerprint(SOURCE_GLOBS)
        if manifest['source_tree_hash']!=current_source:errors.append('source/canon changed since build')
        for f in manifest['files']:
            if not (ROOT/f['path']).exists() or sha(ROOT/f['path'])!=f['sha256']:errors.append('changed/missing '+f['path'])
    else:errors.append('missing deliverables/current/manifest.json')
    result={'status':'PASS' if not errors else 'FAIL','scope':'evidence/revision/export snapshot integrity only','revision':rev,'input_checks':input_results,'errors':errors,'physical_fit':'UNRESOLVED','fabrication_approval':'NOT GIVEN'}
    write('docs/validation/latest_integrity.json',result);print(json.dumps(result,indent=2))
    if errors:raise SystemExit(1)
    return result
def query(args):
    op=args[0] if args else 'help';r=read('deliverables/current/analysis/resolved.json');checks=read('deliverables/current/analysis/checks.json')
    header={'units':'mm','revision':r['revision'],'state':read('canon/project_state.json')['working_state'],'scale_status':r['scale_status']}
    if op=='features':result=r['features'] if len(args)==1 else next((f for f in r['features'] if f['id']==args[1]),None)
    elif op=='dimension':
        id=args[1];accepted=[m for m in read('canon/measurements.json')['measurements'] if m['id']==id]
        if accepted:result=accepted
        else:
            parts=id.split('.');result=r
            for p in parts:result=result[p]
            result={'value':result,'provenance':'resolved model; inspect assumptions/nominal/candidate status','not_physical_measurement':True}
    elif op=='measure':
        a,b=(next(f for f in r['features'] if f['id']==id) for id in args[1:3]);pa=a['point_mm'];pb=b['point_mm'];result={'distance_mm':sum((x-y)**2 for x,y in zip(pa,pb))**.5,'method':'approximate scan-landmark Euclidean distance','a':args[1],'b':args[2],'independent':False}
    elif op=='coverage':result=checks['coverage'] if len(args)==1 else [x for x in checks['coverage'] if x['feature_id']==args[1]]
    elif op=='clearance':result=[x for x in checks['checks'] if any(k in x['id'] for k in ['DEPTH','CLASH','SLICE','ENGAGEMENT','NEIGHBOR'])]
    elif op=='depth':result=read('deliverables/current/analysis/depth_stack.json')
    elif op=='section':
        axis=args[1] if len(args)>1 else 'controls'
        if axis not in ['controls','studs']:raise ValueError('section must be controls or studs')
        result={'path':f'deliverables/current/review/views/section_{axis}.png','type':'saved generated display section; not an exact solid query','regenerate':'./project build'}
    elif op=='compare-states':result={'states':read('canon/project_state.json')['states'],'changes':['candidate outer plate and illustrative wall seal added','original-wall trial at original stone plane; added-plate trial shifts those reference parts outward; both have modeled clashes','separate diverter trim remains at original wall plane','raw wall/valve pose preserved; no changes since capture reported 2026-10-14'],'part_poses':[{k:p[k] for k in ['id','location_mm','factory_location_mm']} for p in read('deliverables/current/cad/cad_manifest.json')['parts']],'selected_arrangement':None}
    elif op=='validate':return validate()
    elif op=='solid':
        import cadquery as cq
        id=args[1];p=next(x for x in read('deliverables/current/cad/cad_manifest.json')['parts'] if x['id']==id)
        if not p.get('step'):raise ValueError('No separate STEP for this envelope')
        s=cq.importers.importStep(str(ROOT/p['step'])).val();b=s.BoundingBox();result={'method':'recomputed exact OCCT solid query of provisional design','id':id,'bounds_local_mm':[[b.xmin,b.ymin,b.zmin],[b.xmax,b.ymax,b.zmax]],'volume_mm3':s.Volume(),'is_valid':s.isValid(),'provenance':p['evidence'],'physical_fit':'UNRESOLVED'}
    else:result={'operations':['features [ID]','dimension <M-ID or candidate.diameter_mm>','measure <landmark-ID> <landmark-ID>','coverage [feature-ID]','clearance','depth','section controls|studs','compare-states','solid CUSTOM-01|PLATE-INNER|TRIM-OUTER','validate']}
    print(json.dumps(dict(header,result=result),indent=2))
def review(no_open=False):
    port=int(os.environ.get('PROJECT_REVIEW_PORT','8765'))
    url=f'http://127.0.0.1:{port}/review/index.html'
    def ready():
        try:
            with urllib.request.urlopen(url,timeout=1) as response:
                return 'shower-kohler-valve' in response.read().decode('utf-8')
        except (OSError,ValueError):return False
    try:
        with socket.create_connection(('127.0.0.1',port),timeout=.3):pass
    except OSError:
        (ROOT/'build').mkdir(exist_ok=True)
        log=open(ROOT/'build/review-server.log','a')
        proc=subprocess.Popen([sys.executable,'-m','http.server',str(port),'--bind','127.0.0.1','--directory',str(ROOT/'deliverables/current')],stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        for _ in range(20):
            if ready():break
            if proc.poll() is not None:raise RuntimeError('Local server could not start; see build/review-server.log')
            time.sleep(.1)
    if not ready():raise RuntimeError('Review page not available on this port. Set PROJECT_REVIEW_PORT to an unused port.')
    print(url)
    if not no_open:subprocess.run(['open',url],check=True)
def handoff():
    dest=ROOT/'build/handoff';dest.mkdir(parents=True,exist_ok=True);bundle=dest/'shower-kohler-valve.git.bundle'
    if bundle.exists():bundle=bundle.with_name('shower-kohler-valve-'+datetime.datetime.now().strftime('%Y%m%d-%H%M%S')+'.git.bundle')
    run(['git','bundle','create',str(bundle),'--all']);run(['git','bundle','verify',str(bundle)])
    changes=subprocess.check_output(['git','status','--porcelain'],text=True).strip()
    notes=ROOT/'deliverables/current/blender/user_notes.blend'
    if changes or notes.exists():
        paths=subprocess.check_output(['git','ls-files','--modified','--others','--exclude-standard','-z']).decode().split('\0')
        if notes.exists():paths.append(str(notes.relative_to(ROOT)))
        stamp=datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        with zipfile.ZipFile(dest/('uncommitted-files-'+stamp+'.zip'),'w',zipfile.ZIP_DEFLATED) as z:
            for name in paths:
                if name and (ROOT/name).is_file():z.write(ROOT/name,name)
        (dest/('uncommitted-status-'+stamp+'.txt')).write_text(changes+'\n'+('Separate ignored user_notes.blend included.\n' if notes.exists() else ''))
    with zipfile.ZipFile(dest/'analysis-review.zip','w',zipfile.ZIP_DEFLATED) as z:
        for base in ['canon','docs','deliverables/current/analysis']:
            for p in (ROOT/base).rglob('*'):
                if p.is_file():z.write(p,str(p.relative_to(ROOT)))
        for name in ['coverage','control_depth_measure','inner_front','inner_back','section_studs','assembled','exploded','factory','neighbor_measure']:
            p=ROOT/f'deliverables/current/review/views/{name}.png';z.write(p,str(p.relative_to(ROOT)))
        for name in ['deliverables/current/review/manual_steps.json','deliverables/current/review/measurement_requests.json',
                     'data/evidence/user/inner-plate-front-caliper-2026-10-14.png','data/evidence/user/outer-plate-front-caliper-2026-10-14.png',
                     'data/evidence/user/depth-side-view-2026-10-14.png','data/evidence/kohler-2973-KS-spec.pdf','data/evidence/kohler-2973-install-1205551-2.pdf','data/evidence/kohler-1041504_2.pdf','data/evidence/kohler-1216755-2.pdf','data/evidence/kohler-T14489-4-spec.pdf','data/evidence/kohler-T14491-4-spec.pdf']:
            z.write(ROOT/name,name)
        for case in ['factory','proposed']:
            name=f'deliverables/current/review/views/depth_{case}.svg';z.write(ROOT/name,name)
        fab=ROOT/'deliverables/current/fabrication/F005'
        if fab.exists():
            for pattern in ['*.json','*.pdf','*.md','index.html','views/*','cad/*.csv','quote_package_*.zip']:
                for p in sorted(fab.glob(pattern)):z.write(p,str(p.relative_to(ROOT)))
            for name in ['inner_photo','outer_photo']:
                p=ROOT/f'deliverables/current/review/views/{name}.png';z.write(p,str(p.relative_to(ROOT)))
            z.writestr('READ_REVIEW_PACKAGE_FIRST.txt','Private compact review package. F005 drawings, images, analysis and six custom-only quote ZIPs are included. The complete Git bundle contains Blender, all source code, original scans and the full interactive measurement review. The F005 Blender and measurement-worksheet links require that complete checkout. No manufacturing release or physical fit is implied.\n')
    print('Private local handoff:',bundle.relative_to(ROOT),'(contains complete committed originals). Not an off-machine backup.')

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor');sub.add_parser('ingest');b=sub.add_parser('build');b.add_argument('--force',action='store_true')
    fab=sub.add_parser('prepare-fabrication');fab.add_argument('--stage',choices=['all','cad','fit','render','documents'],default='all');fab.add_argument('--force',action='store_true')
    r=sub.add_parser('review');r.add_argument('--no-open',action='store_true');i=sub.add_parser('import-measurements');i.add_argument('file');i.add_argument('--dry-run',action='store_true')
    v=sub.add_parser('validate');v.add_argument('--git-objects',action='store_true');q=sub.add_parser('query');q.add_argument('args',nargs='*');sub.add_parser('handoff');sub.add_parser('manifest')
    args=p.parse_args()
    if args.command=='doctor':doctor()
    elif args.command=='ingest':run([sys.executable,'scripts/ingest.py'])
    elif args.command=='build':
        build(args.force)
        if (ROOT/'canon/fabrication_designs.json').exists():prepare_fabrication(force=args.force)
    elif args.command=='prepare-fabrication':prepare_fabrication(args.stage,args.force)
    elif args.command=='review':review(args.no_open)
    elif args.command=='validate':validate(args.git_objects)
    elif args.command=='query':query(args.args)
    elif args.command=='handoff':handoff()
    elif args.command=='manifest':publish_manifest()
    elif args.command=='import-measurements':
        sys.path.insert(0,str(ROOT/'src/analysis'));from import_measurements import import_response
        print(json.dumps(import_response(Path(args.file).resolve(),dry_run=args.dry_run),indent=2))
        if not args.dry_run:print('Next: ./project build ; ./project validate. No raw scan or accepted prior observation was overwritten.')

if __name__=='__main__':main()
