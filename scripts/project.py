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
    tracked=set(subprocess.check_output(['git','ls-files','-z','deliverables/current']).decode().split('\0'))
    active=read('canon/fit_trial_design.json').get('output_directory','deliverables/current/fabrication/fit-trial')+'/'
    for p in sorted((ROOT/'deliverables/current').rglob('*')):
        rel=str(p.relative_to(ROOT))
        if rel not in tracked and not rel.startswith(active):continue
        if p.is_file() and p.name!='manifest.json' and not p.name.endswith(('.blend1','.blend2')):
            files.append(dict(path=str(p.relative_to(ROOT)),sha256=sha(p),size_bytes=p.stat().st_size))
    write('deliverables/current/manifest.json',dict(project_id='shower-kohler-valve',revision=read('canon/measurements.json')['revision'],
        status='DRAFT_NOT_FOR_FABRICATION',source_commit=commit,source_commit_note='Commit present at build time; source_tree_hash includes current source/canon, avoiding future-commit circularity.',
        source_tree_hash=fingerprint(SOURCE_GLOBS),
        input_hashes={i['id']:i['sha256'] for i in read('canon/inputs.json')['inputs']},files=files,
        readiness=read('canon/project_state.json')['readiness'],
        current_recommendation=read('canon/project_state.json').get('fabrication_design_revision'),
        current_recommendation_scope='Current selected plate-only files are for quotes and sacrificial dry fit; permanent installation remains unreleased.'))
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

def prepare_concentric(stage='all',force=False):
    """Dependency-aware CB01 appearance/clearance trials, kept separate from F005."""
    preserve_edits()
    state=read('build/concentric_stages.json') if (ROOT/'build/concentric_stages.json').exists() else {}
    out='deliverables/current/fabrication/concentric-border-study'
    stages=[
      ('base',['scripts/concentric_border_study.py','canon/concentric_border_requirement.json','canon/fabrication_designs.json','data/derived/resolved.json'],[out+'/analysis.json',out+'/cad/*SS060*',out+'/views/C?_front.svg'],[sys.executable,'scripts/concentric_border_study.py']),
      ('stock',['src/fabrication/concentric_package.py',out+'/analysis.json',out+'/cad/*SS060*.dxf','canon/fabrication_designs.json'],[out+'/package_manifest.json',out+'/cad/*'],[sys.executable,'src/fabrication/concentric_package.py','cad']),
      ('locator',['src/fabrication/stud_locator.py','canon/stud_locator_study.json','canon/measurements.json','canon/fabrication_designs.json','data/derived/registration.json','data/derived/resolved.json','deliverables/current/analysis/center_reconciliation_DRAFT.json'],[out+'/stud_locator_analysis.json',out+'/reconciled_model_state.json',out+'/views/stud_locator_trial.*',out+'/diagnostic/*'],[sys.executable,'src/fabrication/stud_locator.py']),
      ('damage',['scripts/concentric_damage_overlay.py','canon/damage_visibility_requirement.json','canon/concentric_border_requirement.json','data/derived/resolved.json','data/evidence/scan_quality/wall_detail_registered.*',out+'/analysis.json'],[out+'/damage.html',out+'/damage_mapping.json',out+'/views/*_damage_overlay.svg',out+'/views/*_top_gouges.svg',out+'/views/wall_detail_source.png'],[sys.executable,'scripts/concentric_damage_overlay.py']),
      ('render',['src/fabrication/concentric_blender.py',out+'/analysis.json',out+'/package_manifest.json',out+'/stud_locator_analysis.json',out+'/reconciled_model_state.json',out+'/diagnostic/*.stl','deliverables/current/fabrication/F005/paired_escutcheons_F005_DRAFT.blend'],[out+'/views/C?_*.png',out+'/views/LOC01_tabs.png',out+'/paired_concentric_CB01_DRAFT.blend',out+'/blender_validation.json'],[BLENDER,'--background','--factory-startup','--python-exit-code','1','--python','src/fabrication/concentric_blender.py']),
      ('documents',['src/fabrication/concentric_package.py',out+'/*.json',out+'/views/*.png','data/evidence/scan_quality/wall_detail_registered.*','docs/physical_checks/installed_center_distances_2026-10-15.json','deliverables/current/analysis/center_reconciliation_DRAFT.json'],[out+'/*.pdf',out+'/quote_*.zip',out+'/index.html',out+'/document_validation.json'],[sys.executable,'src/fabrication/concentric_package.py','documents'])]
    for name,inputs,patterns,cmd in stages:
        if stage not in ('all',name):continue
        # The documents stage's own validation must not invalidate its inputs.
        if name=='documents':
            inputs=[x for x in inputs if x!=out+'/*.json']+[out+'/'+x for x in ['analysis.json','package_manifest.json','blender_validation.json','stud_locator_analysis.json','reconciled_model_state.json']]
        digest=fingerprint(inputs);prior=state.get(name,{});files=prior.get('outputs',{})
        unchanged=not force and prior.get('fingerprint')==digest and files and all((ROOT/f).exists() and sha(ROOT/f)==h for f,h in files.items())
        if unchanged:print('concentric '+name+': unchanged',flush=True);continue
        print('concentric '+name+': building',flush=True);run(cmd,'concentric_'+name+'.log')
        owned={str(p.relative_to(ROOT)) for pat in patterns for p in ROOT.glob(pat) if p.is_file() and not p.name.endswith('.blend1')}
        state[name]={'fingerprint':digest,'outputs':{p:sha(ROOT/p) for p in sorted(owned)}};write('build/concentric_stages.json',state)
    if stage in ('all','render','documents') and (ROOT/'docs/physical_checks/rear_installation_2026-10-15.json').exists():
        prepare_rear(force=False,preserve=False)
    publish_manifest()
    print('CB01 prepared as an unselected draft; LOC01 remains diagnostic. Physical checks and release remain open.')

def prepare_rear(force=False,preserve=True):
    """Add current rear photo evidence without rebuilding or altering manufactured parts."""
    if preserve:preserve_edits()
    base='deliverables/current/fabrication/concentric-border-study/paired_concentric_CB01_DRAFT.blend'
    record='docs/physical_checks/rear_installation_2026-10-15.json'
    inputs=['src/blender/rear_review.py',record,base]+[p['path'] for p in read(record)['photos']]
    target='deliverables/current/blender/installation_REAR01_DRAFT.blend'
    outputs=[target,'deliverables/current/review/rear/rear_photos_REAR01.png','deliverables/current/review/rear/blender_validation.json']
    state=read('build/rear_stages.json') if (ROOT/'build/rear_stages.json').exists() else {}
    digest=fingerprint(inputs)
    unchanged=not force and state.get('fingerprint')==digest and all((ROOT/p).exists() and state.get('outputs',{}).get(p)==sha(ROOT/p) for p in outputs)
    if unchanged:print('rear Blender: unchanged',flush=True)
    else:
        run([BLENDER,'--background','--factory-startup','--python-exit-code','1','--python','src/blender/rear_review.py'],'rear_review.log')
        write('build/rear_stages.json',{'fingerprint':digest,'outputs':{p:sha(ROOT/p) for p in outputs}})
    run([sys.executable,'src/review/rear_evidence.py'])
    if (ROOT/'deliverables/current/fabrication/aperture-access/index.html').exists():
        sys.path.insert(0,str(ROOT/'src/fabrication'))
        from aperture_access import attach_panel
        attach_panel()
    if (ROOT/'deliverables/current/fabrication/aperture-access/control_alignment.json').exists():
        sys.path.insert(0,str(ROOT/'src/analysis'))
        from control_alignment import attach_panel as attach_alignment_panel
        attach_alignment_panel()
    if (ROOT/'deliverables/current/fabrication/control-registration/registration_trial.json').exists():
        sys.path.insert(0,str(ROOT/'src/analysis'))
        from registration_trial import attach_panel as attach_registration_panel
        attach_registration_panel()
    # The existing documents stage owns this HTML; acknowledge the evidence panel
    # without invalidating its already-reviewed PDF or manufacturing ZIP outputs.
    cache=ROOT/'build/concentric_stages.json'
    if cache.exists():
        stages=read(cache);page='deliverables/current/fabrication/concentric-border-study/index.html'
        if page in stages.get('documents',{}).get('outputs',{}):
            stages['documents']['outputs'][page]=sha(ROOT/page)
            write(cache,stages)
    publish_manifest()

def prepare_aperture(stage='all'):
    """Separate AP01 control-access candidates; never replace historical quote CAD."""
    preserve_edits()
    prepare_rear(force=False,preserve=False)
    rear='deliverables/current/blender/installation_REAR01_DRAFT.blend'
    rear_before=sha(ROOT/rear)
    if stage in ('all','analysis'):
        run([sys.executable,'src/fabrication/aperture_access.py'],'aperture_access.log')
    if stage in ('all','blender'):
        run([BLENDER,'--background','--factory-startup','--python-exit-code','1','--python','src/blender/aperture_access.py'],'aperture_access_blender.log')
    assert sha(ROOT/rear)==rear_before, 'AP01 modified the generated rear input'
    if stage in ('all','blender'):
        run([sys.executable,'src/fabrication/audit_aperture.py','--rear-before-sha256',rear_before])
    if (ROOT/'docs/physical_checks/control_alignment_2026-10-15.json').exists():
        run([sys.executable,'src/analysis/control_alignment.py'])
    publish_manifest()

def prepare_registration(stage='all'):
    """Small independent pose study; original source and AP01 cutting shapes stay fixed."""
    preserve_edits()
    if stage in ('all','analysis'):
        run([sys.executable,'src/analysis/registration_trial.py'],'control_registration_analysis.log')
    if stage in ('all','blender'):
        run([BLENDER,'--background','--factory-startup','--threads','2','--python-exit-code','1','--python','src/blender/control_registration.py'],'control_registration_blender.log')
    sys.path.insert(0,str(ROOT/'src/analysis'))
    from registration_trial import page,attach_panel
    page(read('deliverables/current/fabrication/control-registration/registration_trial.json'));attach_panel()
    publish_manifest()

def prepare_fit_trial(stage='all',force=False):
    """Current quote/dry-fit package; keep historical studies and source poses intact."""
    preserve_edits()
    d=read('canon/fit_trial_design.json');out=d['output_directory'];rev=d['revision']
    statefile='build/fit_trial_'+rev+'_stages.json'
    state=read(statefile) if (ROOT/statefile).exists() else {}
    blender=[BLENDER,'--background','--factory-startup','--threads','2','--python-exit-code','1','--python']
    stages=[
      ('analysis',['src/analysis/fit_trial_release.py','src/analysis/mounting_layout.py','src/fabrication/release_analysis.py','src/fabrication/release_views.py','src/fabrication/repair_form.py','src/fabrication/fit_trial.py','src/fabrication/fit_trial_spec.py','canon/fit_trial_design.json','canon/repair_form_design.json','canon/measurements.json','data/derived/resolved.json','data/derived/registration.json'],
       [out+'/design_report.json',out+'/engineering/*',out+'/reference/*',out+'/cad/*',out+'/sections.png',out+'/support_seal.png',out+'/REPAIR_FORM_TRIAL/*.step',out+'/REPAIR_FORM_TRIAL/*.stl',out+'/REPAIR_FORM_TRIAL/*.json'],
       [[sys.executable,'src/fabrication/release_analysis.py'],[sys.executable,'src/fabrication/release_views.py'],[sys.executable,'src/fabrication/repair_form.py']]),
      ('blender',['src/blender/fit_trial.py',out+'/design_report.json',out+'/reference/*',out+'/cad/*.stl','build/attached_scan/wall_frame.json'],
       [out+'/*.blend',out+'/blender_check.json',out+'/paired_*.png',out+'/exploded.png'],[blender+['src/blender/fit_trial.py']]),
      ('documents',['src/fabrication/release_documents.py','src/fabrication/release_support_documents.py','src/fabrication/ponoko.py','canon/fit_trial_handoff.json','canon/repair_form_design.json','canon/fit_trial_design.json',out+'/design_report.json',out+'/engineering/*.json',out+'/*.png',out+'/cad/*',out+'/ponoko/quotes.json'],
       [out+'/*.pdf',out+'/*.html',out+'/*.source.json',out+'/*.zip',out+'/packages.json',out+'/document_check.json',out+'/METAL_FIT_TRIAL/*',out+'/CLEAR_FIT_TRIAL/*',out+'/REPAIR_FORM_TRIAL/*'],[[sys.executable,'src/fabrication/release_documents.py']]),
      ('audit',['src/fabrication/audit_release.py',out+'/design_report.json',out+'/cad/*',out+'/*.pdf',out+'/*.zip',out+'/index.html',out+'/blender_check.json',out+'/REPAIR_FORM_TRIAL/*'],
       [out+'/audit.json','docs/validation/fit_trial_FT02.json'],[[sys.executable,'src/fabrication/audit_release.py']])]
    for name,inputs,patterns,commands in stages:
        if stage not in ('all',name):continue
        digest=fingerprint(inputs);prior=state.get(name,{})
        unchanged=not force and prior.get('fingerprint')==digest and prior.get('outputs') and all((ROOT/p).exists() and sha(ROOT/p)==h for p,h in prior['outputs'].items())
        if unchanged:print(rev+' '+name+': unchanged',flush=True);continue
        print(rev+' '+name+': building',flush=True)
        for i,cmd in enumerate(commands):run(cmd,'fit_trial_'+name+'_'+str(i)+'.log')
        owned={str(p.relative_to(ROOT)) for pat in patterns for p in ROOT.glob(pat) if p.is_file() and not p.name.endswith('.blend1')}
        state[name]={'fingerprint':digest,'outputs':{p:sha(ROOT/p) for p in sorted(owned)}}
        write(statefile,state)
    # Old pages remain available as evidence but identify the current recommendation.
    d=read('canon/fit_trial_design.json')
    banner=f'<aside id="ft01-current" style="padding:16px;background:#e5f1f3;border:2px solid #236679;margin:12px;color:#183e48">Current quote and dry-fit recommendation: <a href="/{out.removeprefix("deliverables/current/")}/index.html">{d["revision"]} main {d["main"]["outer_diameter_mm"]:g} / diverter {d["diverter"]["outer_diameter_mm"]:g}, upright capsule opening</a>. This page is a historical study.</aside>'
    for rel in ['review/index.html','review/rear/index.html','manual/index.html','fabrication/F005/index.html','fabrication/concentric-border-study/index.html','fabrication/aperture-access/index.html','fabrication/control-registration/index.html']:
        p=ROOT/'deliverables/current'/rel
        if p.exists():
            import re
            text=p.read_text()
            if 'id="ft01-current"' in text:
                text=re.sub(r'<aside id="ft01-current".*?</aside>',lambda m:banner,text,count=1)
            elif re.search(r'<body\b',text):
                text=re.sub(r'(<body\b[^>]*>)',lambda m:m.group(1)+banner,text,count=1)
            else:
                text=re.sub(r'(<(?:main|header|nav)\b[^>]*>)',lambda m:banner+m.group(1),text,count=1)
            p.write_text(text)
    publish_manifest()
    print(rev+' quote/dry-fit package prepared. Physical fit, support/seal and water verification remain open.')

def explain_tabs(stage='all'):
    """Separate explanatory movie. Selected CAD, canon and vendor packages are inputs only."""
    blender=[BLENDER,'--background','--factory-startup','--threads','4','--python-exit-code','1','--python','src/blender/tab_explainer.py']
    if stage in ('all','assets'):
        run([sys.executable,'src/fabrication/tab_explainer.py','assets'],'tab_explainer_assets.log')
    if stage=='preview':
        run(blender+['--','preview'],'tab_explainer_preview.log')
        run([sys.executable,'src/fabrication/tab_explainer.py','preview'])
    if stage in ('all','render'):
        run(blender,'tab_explainer_render.log')
    if stage in ('all','encode'):
        run([sys.executable,'src/fabrication/tab_explainer.py','encode'])
    if stage in ('all','verify'):
        run([BLENDER,'--background','--factory-startup','--threads','4','--python-exit-code','1',
             '--python','src/blender/check_tab_explainer.py'],'tab_explainer_readback.log')

def rethink_tabs(stage='all'):
    """TR02 narrated reassessment, including RF01; existing order files are inputs only."""
    if stage in ('all','analysis'):
        run([sys.executable,'src/analysis/tab_rethink.py'],'tab_rethink_analysis.log')
    if stage in ('all','speech'):
        run([sys.executable,'src/fabrication/tab_rethink_video.py','speech'],'tab_rethink_speech.log')
    if stage in ('all','render'):
        run([BLENDER,'--background','--factory-startup','--threads','4','--python-exit-code','1',
             '--python','src/blender/tab_rethink.py'],'tab_rethink_render.log')
    for action in ['preview','encode','verify']:
        if stage in ('all',action):run([sys.executable,'src/fabrication/tab_rethink_video.py',action])
    if stage in ('all','verify'):
        run([BLENDER,'--background','--factory-startup','--threads','4','--python-exit-code','1',
             '--python','src/blender/check_tab_rethink.py'],'tab_rethink_readback.log')

def validate(git_objects=False):
    errors=[];input_results=[]
    for i in read('canon/inputs.json')['inputs']:
        p=ROOT/i['repository_path'];ok=p.exists() and sha(p)==i['sha256'] and p.stat().st_size==i['size_bytes']
        if git_objects:
            b=subprocess.check_output(['git','show','HEAD:'+i['repository_path']]);ok=ok and hashlib.sha256(b).hexdigest()==i['sha256'] and len(b)==i['size_bytes']
        input_results.append(dict(id=i['id'],status='PASS' if ok else 'FAIL',committed_bytes_checked=git_objects))
        if not ok:errors.append(i['id'])
    rev=read('canon/measurements.json')['revision']
    design=read('canon/fit_trial_design.json');out=design['output_directory']
    for p in [out+'/design_report.json',out+'/blender_check.json',out+'/audit.json']:
        if not (ROOT/p).exists():errors.append('missing '+p);continue
        item=read(p)
        if item.get('revision',design['revision'])!=design['revision']:errors.append('stale '+p)
        if p.endswith('blender_check.json') and not all(x.startswith(design['revision']+'_') for x in item.get('custom_dimensions_verified',[])):errors.append('stale Blender part identities')
    if read(out+'/design_report.json').get('design')!=design:errors.append('stale active design report')
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
def historical_query(args,scope='historical_reconstruction'):
    op=args[0] if args else 'help';r=read('deliverables/current/analysis/resolved.json');checks=read('deliverables/current/analysis/checks.json')
    header={'units':'mm','evidence_revision':r['revision'],'state':scope,'scale_status':r['scale_status'],
            'current_design_revision':read('canon/project_state.json')['fabrication_design_revision'],
            'current_design_fit_result':False,
            'source':'deliverables/current/analysis/resolved.json',
            'scope_note':'Preserved evidence/reference reconstruction and old diagnostic assemblies. Historical candidate dimensions and clashes do not describe the current selected fit-trial parts.'}
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
    elif op=='reconcile-centers':
        sys.path.insert(0,str(ROOT/'src/analysis'))
        from reconcile_installed_centers import save
        result=save(ROOT)
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
    else:result={'operations':['features [ID]','dimension <M-ID or candidate.diameter_mm>','measure <landmark-ID> <landmark-ID>','coverage [feature-ID]','clearance','depth','reconcile-centers','section controls|studs','compare-states','solid CUSTOM-01|PLATE-INNER|TRIM-OUTER','validate']}
    print(json.dumps(dict(header,result=result),indent=2))

def query(args):
    # Historical reconstructions must never inherit the current design's label.
    sys.path.insert(0,str(ROOT))
    from src.analysis.fit_trial_query import CurrentQuery,QueryError
    op=args[0] if args else 'help'
    try:
        if op=='historical':
            if len(args)<2:raise QueryError('Specify a historical operation, e.g. historical solid PLATE-INNER.')
            return historical_query(args[1:])
        if op in ['features','measure']:
            counts=(1,2) if op=='features' else (3,3)
            if not counts[0]<=len(args)<=counts[1]:raise QueryError('Use features [ID] or measure <landmark-ID> <landmark-ID>.')
            return historical_query(args,scope='preserved_evidence_registry')
        if op in ['section','reconcile-centers']:
            return historical_query(args)
        if op=='validate':return validate()
        print(json.dumps(CurrentQuery(ROOT).run(args),indent=2))
    except (QueryError,KeyError,IndexError,StopIteration,FileNotFoundError) as error:
        print(json.dumps({'status':'QUERY_ERROR','error':str(error) or 'Unknown historical feature or part; inspect query help.',
                          'physical_fit':'NOT PERFORMED'},indent=2))
        raise SystemExit(2)
def review(no_open=False):
    port=int(os.environ.get('PROJECT_REVIEW_PORT','8765'))
    design=read('canon/fit_trial_design.json');page=design['output_directory']+'/index.html'
    current=(ROOT/page).exists()
    url=f'http://127.0.0.1:{port}/'+(page.removeprefix('deliverables/current/') if current else 'review/index.html')
    def ready():
        try:
            with urllib.request.urlopen(url,timeout=1) as response:
                return (design['revision'] if current else 'shower-kohler-valve') in response.read().decode('utf-8')
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
        concentric=ROOT/'deliverables/current/fabrication/concentric-border-study'
        if concentric.exists():
            for pattern in ['*.json','*.pdf','*.html','views/*','quote_*.zip','diagnostic/*']:
                for p in sorted(concentric.glob(pattern)):z.write(p,str(p.relative_to(ROOT)))
            for p in sorted((ROOT/'data/evidence/user').glob('installed-*-2026-10-15.png')):
                z.write(p,str(p.relative_to(ROOT)))
            z.writestr('CURRENT_CB01_REVIEW.txt','Current circular-only CB01 candidates supersede the F005 appearances. Open deliverables/current/fabrication/concentric-border-study/index.html, including damage.html and the 3D tip-distance clarification. RECON-001 revision 2 preserves six 3D end-tip-center lengths; derived fits do not establish plate-plane hole locations. LOC01 is diagnostic and excluded from quote ZIPs. Full Blender scenes and source scans are in the complete Git bundle. Physical fit and manufacturing release remain open.\n')
        design=read('canon/fit_trial_design.json');trial=ROOT/design['output_directory']
        if trial.exists():
            for pattern in ['*.json','*.pdf','*.html','*.png','*.jpg','*.zip','cad/*','engineering/*','photos/*','ponoko/*.json','ponoko/*.txt']:
                for p in sorted(trial.glob(pattern)):z.write(p,str(p.relative_to(ROOT)))
            z.writestr('START_WITH_'+design['revision']+'.txt',f'{design["revision"]} is the current quote and sacrificial fit-trial release. Open {design["output_directory"]}/index.html and ORDER_AND_NEXT_STEP.pdf. Choose one material route, one main plus one diverter. Earlier FT01/F005/CB01/AP01 notes describe history. The three-scene Blender file and original ZIPs remain in the complete Git bundle. Physical fit and permanent use remain unestablished.\n')
    print('Private local handoff:',bundle.relative_to(ROOT),'(contains complete committed originals). Not an off-machine backup.')

def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    sub.add_parser('doctor');sub.add_parser('ingest');b=sub.add_parser('build');b.add_argument('--force',action='store_true')
    fab=sub.add_parser('prepare-fabrication');fab.add_argument('--stage',choices=['all','cad','fit','render','documents'],default='all');fab.add_argument('--force',action='store_true')
    con=sub.add_parser('prepare-concentric');con.add_argument('--stage',choices=['all','base','stock','locator','damage','render','documents'],default='all');con.add_argument('--force',action='store_true')
    rear=sub.add_parser('prepare-rear');rear.add_argument('--force',action='store_true')
    ap=sub.add_parser('prepare-aperture');ap.add_argument('--stage',choices=['all','analysis','blender'],default='all')
    sub.add_parser('audit-aperture')
    sub.add_parser('audit-control-alignment')
    align=sub.add_parser('prepare-registration');align.add_argument('--stage',choices=['all','analysis','blender'],default='all')
    trial=sub.add_parser('prepare-fit-trial');trial.add_argument('--stage',choices=['all','analysis','blender','documents','audit'],default='all');trial.add_argument('--force',action='store_true')
    movie=sub.add_parser('explain-tabs');movie.add_argument('--stage',choices=['all','assets','preview','render','encode','verify'],default='all')
    rethink=sub.add_parser('rethink-tabs');rethink.add_argument('--stage',choices=['all','analysis','speech','render','preview','encode','verify'],default='all')
    sub.add_parser('preview-finishes')
    refine=sub.add_parser('refine-tabs');refine.add_argument('--stage',choices=['probe','deeper','build','render','documents'],default='probe')
    formprint=sub.add_parser('prepare-form-print');formprint.add_argument('--stage',choices=['cad','capture','render','documents','audit'],default='cad')
    smallform=sub.add_parser('prepare-small-bed-form');smallform.add_argument('--stage',choices=['cad','render','documents','audit'],default='cad')
    r=sub.add_parser('review');r.add_argument('--no-open',action='store_true');i=sub.add_parser('import-measurements');i.add_argument('file');i.add_argument('--dry-run',action='store_true')
    v=sub.add_parser('validate');v.add_argument('--git-objects',action='store_true');q=sub.add_parser('query');q.add_argument('args',nargs='*');sub.add_parser('handoff');sub.add_parser('manifest')
    args=p.parse_args()
    if args.command=='doctor':doctor()
    elif args.command=='ingest':run([sys.executable,'scripts/ingest.py'])
    elif args.command=='build':
        build(args.force)
        if (ROOT/'canon/fabrication_designs.json').exists():prepare_fabrication(force=args.force)
        if (ROOT/'canon/concentric_border_requirement.json').exists():prepare_concentric(force=args.force)
        if (ROOT/'canon/aperture_access_study.json').exists():prepare_aperture()
        if (ROOT/'docs/physical_checks/control_alignment_2026-10-15.json').exists():prepare_registration()
        if (ROOT/'canon/fit_trial_design.json').exists():prepare_fit_trial(force=args.force)
    elif args.command=='prepare-fabrication':prepare_fabrication(args.stage,args.force)
    elif args.command=='prepare-concentric':prepare_concentric(args.stage,args.force)
    elif args.command=='prepare-rear':prepare_rear(args.force)
    elif args.command=='prepare-aperture':prepare_aperture(args.stage)
    elif args.command=='audit-aperture':run([sys.executable,'src/fabrication/audit_aperture.py'])
    elif args.command=='audit-control-alignment':
        run([sys.executable,'src/analysis/control_alignment.py'])
        publish_manifest()
    elif args.command=='prepare-registration':prepare_registration(args.stage)
    elif args.command=='prepare-fit-trial':prepare_fit_trial(args.stage,args.force)
    elif args.command=='explain-tabs':explain_tabs(args.stage)
    elif args.command=='rethink-tabs':rethink_tabs(args.stage)
    elif args.command=='preview-finishes':run([BLENDER,'--background','--factory-startup','--threads','6','--python-exit-code','1','--python','src/blender/finish_study.py'],'finish_study.log')
    elif args.command=='refine-tabs':
        if args.stage=='render':run([BLENDER,'--background','--factory-startup','--threads','4','--python-exit-code','1','--python','src/blender/tab_refinement.py'],'tab_refinement_render.log')
        elif args.stage=='documents':run([sys.executable,'src/fabrication/tab_refinement_review.py'],'tab_refinement_documents.log')
        else:run([sys.executable,'src/analysis/tab_refinement.py']+([] if args.stage=='probe' else ['--'+args.stage]),'tab_refinement_'+args.stage+'.log')
    elif args.command=='prepare-form-print':
        if args.stage=='render':run([BLENDER,'--background','--factory-startup','--threads','4','--python-exit-code','1','--python','src/blender/formwork_print.py'],'RF03_render.log')
        elif args.stage=='documents':run([sys.executable,'src/fabrication/formwork_print_handoff.py'],'RF03_documents.log')
        elif args.stage=='audit':run([sys.executable,'src/fabrication/audit_formwork_print.py'],'RF03_audit.log')
        else:run([sys.executable,'src/fabrication/formwork_print.py']+(['--capture'] if args.stage=='capture' else []),'RF03_'+args.stage+'.log')
    elif args.command=='prepare-small-bed-form':
        if args.stage=='render':run([BLENDER,'--background','--factory-startup','--threads','4','--python-exit-code','1','--python','src/blender/formwork_small_bed.py'],'RF04_render.log')
        elif args.stage=='documents':run([sys.executable,'src/fabrication/formwork_small_bed_handoff.py'],'RF04_documents.log')
        elif args.stage=='audit':run([sys.executable,'src/fabrication/audit_formwork_small_bed.py'],'RF04_audit.log')
        else:run([sys.executable,'src/fabrication/formwork_small_bed.py'],'RF04_cad.log')
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
