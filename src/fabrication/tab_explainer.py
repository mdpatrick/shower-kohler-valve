"""Assets and captioned movie for the FT02 tab explanation. No release changes."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import textwrap

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
BUILD = ROOT / 'build/FT02/tab_explainer'
OUT = ROOT / 'deliverables/current/fabrication/FT02/tab-explainer'
FPS = 15
CHAPTERS = [
    (0, 5, 'Where the tabs would go', 'Rejected tab candidate',
     'Amber tabs extend into the opening to surround the two trim rods.',
     'CAD candidate over the unchanged original scan; working alignment is approximate.'),
    (5, 9, 'Look closely at the upper-right rod', 'Captured installation',
     'The tab-hole center comes from your measured inner-plate layout.',
     'The custom sheet and factory mounting holes occupy different depth planes.'),
    (9, 17, 'Move the tab toward the wall', 'Geometric insertion sweep',
     'The captured rod end meets the added tab material along this modeled path.',
     'Removing or retracting the rods could clear their ends; seated alignment is a separate check.'),
    (17, 22, 'Inspect the seated tab', 'Scan-based conflict warning',
     'Red marks the small overlap flagged near the upper-right shaft.',
     'Capture and placement uncertainty remain; this is not a confirmed physical defect.'),
    (22, 31, 'What larger hole clearance can allow', 'Illustrative shift',
     'The foam stays fixed while the backing moves sideways by 1.50 mm.',
     'Local straight-edge section: nominal 6 mm foam width + 1 mm extra backing.'),
    (31, 36, 'The selected FT02 plate has no tabs', 'Current fit-trial design',
     'Use the removable front guide to center it, then verify stable support and clamping.',
     'Check the full foam contact in the actual trial; this movie does not establish sealing.'),
]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare():
    import cadquery as cq
    import trimesh
    import numpy as np
    from src.fabrication.fit_trial import make_main
    BUILD.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    d = json.loads((ROOT/'canon/fit_trial_design.json').read_text())
    report = json.loads((ROOT/d['output_directory']/'engineering/locator_evaluation.json').read_text())
    locators = report['transforms']['mounting_centers_in_cover_frame_mm']
    thickness = next(s['thickness_mm'] for s in d['stocks'] if s['id']=='T1520')
    plain = make_main(d, thickness)
    tabbed = make_main(d, thickness, locators)
    # This section uses the actual selected CAD profile; the foam is a nominal local section.
    cutter = cq.Workplane('XY').box(16, 14, 30).translate((-61, 0, 10))
    section = plain.intersect(cutter)
    foam = (cq.Workplane('XY').box(d['foam']['width_mm'],14,d['foam']['free_depth_mm'],
                                centered=(True,True,False))
            .translate((-d['foam']['outer_width_mm']/2+d['foam']['width_mm']/2,0,thickness)))
    assets = {}
    for name, obj in [('plain',plain),('tabbed_candidate',tabbed),('backing_section',section),('foam_section',foam)]:
        p = BUILD/(name+'.stl')
        cq.exporters.export(obj, str(p), tolerance=.012, angularTolerance=.04)
        mesh = trimesh.load(p, force='mesh')
        assert obj.val().isValid() and mesh.is_watertight
        assets[name]={'path':str(p.relative_to(ROOT)),'sha256':digest(p),
                      'bounds_mm':np.asarray(mesh.bounds).tolist(),'solids':len(obj.val().Solids())}
    # Existing analysis defines a measured-source overlap region, not an invented rod axis.
    seated = next(c for c in report['full_capture_checks'] if c['case']=='seated_1mm_bedding')
    collision = seated['parts']['balanced']
    sources = ['canon/fit_trial_design.json','canon/measurements.json','data/derived/registration.json',
               d['output_directory']+'/engineering/locator_evaluation.json',
               d['output_directory']+'/cad/FT02_MAIN_220_T1520_FIT_TRIAL.step',
               d['output_directory']+'/cad/FT02_MAIN_220_T1520_FIT_TRIAL.stl']
    state={'revision':'FT02_TAB_EXPLANATION_01','fps':FPS,'duration_seconds':36,
           'frames':FPS*36,'size':[1024,640], 'assets':assets,
           'sources_sha256':{p:digest(ROOT/p) for p in sources},
           'plate_transform':report['transforms']['cover_to_installed_xy_up'],
           'tab_geometry':report['candidate_geometry'],
           'studs_mm':json.loads((ROOT/'data/derived/resolved.json').read_text())['studs_mm'],
           'seated_overlap':collision,
           'overlap_reference_note':'Reported overlap uses the existing 1.524 mm tab study; this 1.520 mm explanatory mesh uses its region as a qualitative callout, not a newly calculated collision volume.',
           'thickness_mm':thickness,'bedding_mm':1,
           'bedding_status':'Illustrative working placement, not measured support',
           'scan_transform':'Unchanged data/derived/registration.json',
           'relative_shift_mm':1.504,
           'section_status':'Local straight side, nominal 6 x 6 mm uncompressed foam; no full-footprint or engagement proof',
           'chapters':[{'start':a,'end':b,'title':c,'status':s,'caption':x,'limit':y}
                       for a,b,c,s,x,y in CHAPTERS],
           'physical_fit':'NOT PERFORMED','manufacturing_files_changed':False}
    (BUILD/'scene.json').write_text(json.dumps(state,indent=2)+'\n')
    print('Validated explanatory CAD assets prepared.',flush=True)


def chapter_at(t):
    return next((c for c in CHAPTERS if c[0]<=t<c[1]),CHAPTERS[-1])


def annotate(path, frame):
    from PIL import Image, ImageDraw, ImageFont
    image=Image.open(path).convert('RGB')
    canvas=Image.new('RGB',(1024,840),(20,30,37))
    canvas.paste(image,(0,72))
    draw=ImageDraw.Draw(canvas)
    font_path='/System/Library/Fonts/Supplemental/Arial.ttf'
    font=ImageFont.truetype(font_path,23)
    small=ImageFont.truetype(font_path,18)
    heading=ImageFont.truetype(font_path,28)
    t=(frame-1)/FPS
    a,b,title,status,caption,limit=chapter_at(t)
    draw.text((28,12),title,font=heading,fill=(240,245,246))
    draw.text((28,45),status,font=small,fill=(150,202,207))
    draw.text((990,15),f'{int(t):02d}s / 36s',anchor='ra',font=small,fill=(214,224,228))
    if a==22:
        if t<24.5:
            caption='Centered: the complete 6 mm foam band has about 1 mm of extra backing.'
        elif t<28.5:
            caption='Illustrative shift: larger holes allow positioning freedom before clamping.'
        else:
            caption='After 1.50 mm relative shift: about 0.50 mm of foam extends past the backing.'
        limit='Conservative clearance example, not observed sliding or a leak threshold.'
    # Short measured labels projected from 3D landmarks.
    labels_path=BUILD/'labels'/f'{frame:04d}.json'
    if labels_path.exists():
        for lab in json.loads(labels_path.read_text()):
            tx,ty=lab['label_pixel'];ty+=72
            color=tuple(lab.get('color',[235,240,242]))
            if 'dimension_pixels' in lab:
                (x1,y1),(x2,y2)=lab['dimension_pixels'];y1+=72;y2+=72
                draw.line([(x1,y1),(x2,y2)],fill=color,width=3)
                import math
                dx,dy=x2-x1,y2-y1;length=math.hypot(dx,dy)
                ux,uy=-dy/length*6,dx/length*6
                for x,y in [(x1,y1),(x2,y2)]:
                    draw.line([(x-ux,y-uy),(x+ux,y+uy)],fill=color,width=2)
                px,py=(x1+x2)/2,(y1+y2)/2
            else:
                px,py=lab['pixel'];py+=72
            bb=draw.textbbox((tx,ty),lab['text'],font=small)
            draw.line([(px,py),(tx-3,ty+10)],fill=color,width=2)
            draw.rectangle((bb[0]-7,bb[1]-5,bb[2]+7,bb[3]+5),fill=(20,30,37))
            draw.text((tx,ty),lab['text'],font=small,fill=(244,247,248))
    y=729
    for line in textwrap.wrap(caption,85):
        draw.text((28,y),line,font=font,fill=(244,247,248));y+=28
    draw.text((28,795),limit,font=small,fill=(190,204,210))
    draw.text((28,820),'Blue: custom plate     Amber: candidate tabs     Purple: foam     Scan: captured surface',
              font=ImageFont.truetype(font_path,15),fill=(174,192,202))
    return canvas


def encode(preview=False):
    cfg=json.loads((BUILD/'scene.json').read_text())
    frames_dir=BUILD/('preview' if preview else 'frames')
    annotated=BUILD/('preview_annotated' if preview else 'annotated')
    annotated.mkdir(parents=True,exist_ok=True)
    frames=sorted(frames_dir.glob('*.png'))
    if not preview:assert len(frames)==cfg['frames'],(len(frames),cfg['frames'])
    for path in frames:
        frame=int(path.stem)
        annotate(path,frame).save(annotated/path.name)
    if preview:
        from PIL import Image,ImageDraw
        thumb_w=512;thumb_h=420
        sheet=Image.new('RGB',(thumb_w*2,thumb_h*((len(frames)+1)//2)),(20,30,37))
        for i,p in enumerate(frames):
            im=Image.open(annotated/p.name).resize((thumb_w,thumb_h))
            sheet.paste(im,((i%2)*thumb_w,(i//2)*thumb_h))
        sheet.save(BUILD/'preview_contact_sheet.jpg')
        print('Preview contact sheet prepared.',flush=True)
        return
    dest=OUT/'FT02_tabs_and_foam_explained.mp4'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate',str(FPS),'-i',str(annotated/'%04d.png'),
                    '-c:v','libx264','-preset','medium','-crf','19','-r','30','-pix_fmt','yuv420p',
                    '-movflags','+faststart',str(dest)],check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(dest)]))
    video=next(s for s in probe['streams'] if s['codec_type']=='video')
    assert video['width']==1024 and video['height']==840
    assert abs(float(probe['format']['duration'])-36)<.1
    for source,digest_before in cfg['sources_sha256'].items():
        assert digest(ROOT/source)==digest_before,'Source was changed: '+source
    from PIL import Image
    Image.open(annotated/'0046.png').save(OUT/'poster.jpg',quality=93)
    for name,frame in [('tabs_overview',46),('rod_tip',181),('seated_scan_overlap',301),('foam_centered',346),('foam_shifted',451),('selected_plain',511)]:
        Image.open(annotated/f'{frame:04d}.png').save(OUT/(name+'.jpg'),quality=93)
    cfg['video']={'path':dest.name,'sha256':digest(dest),'codec':video['codec_name'],
                  'width':1024,'height':840,'seconds':float(probe['format']['duration'])}
    cfg['explanatory_blender']={'path':'FT02_tab_explanation.blend',
                              'sha256':digest(OUT/'FT02_tab_explanation.blend')}
    cfg['shift_basis']={
        'factory_bore_mm':5.66,'custom_hole_mm':7,'nominal_rod_crest_mm':4.826,
        'sum_of_radial_clearances_mm':(5.66-4.826)/2+(7-4.826)/2,
        'interpretation':'Conservative relative translation opportunity for the round-hole stack; not measured travel. The second locator, real geometry and clamping can restrict movement.'}
    cfg['source_hashes_unchanged']=True
    cfg['checks']=['Actual CadQuery solid and watertight display exports','Original scan transform unchanged',
                   'Selected manufacturing STEP/STL and measurement canon unchanged','All frames encoded and H.264 dimensions/duration verified']
    (OUT/'provenance.json').write_text(json.dumps(cfg,indent=2)+'\n')
    (OUT/'READ_ME.txt').write_text('''FT02 — why the bolt tabs were not selected

Play FT02_tabs_and_foam_explained.mp4. It is a 36-second captioned video.
The optional FT02_tab_explanation.blend contains the animated geometry and packed scan texture.
This folder is an explanation, not a package to send for manufacture.

TIMELINE
0–5 s: the amber round-hole/slot tabs added to the blue custom plate.
5–17 s: the plate approaches the original captured rod end.
17–22 s: a close-up of the small source-surface overlap near the seated upper-right tab.
22–31 s: nominal foam backing, then an illustrative sideways shift.
31–36 s: the selected plain FT02 plate, without tabs.

WHAT THE MOVIE DOES AND DOES NOT ESTABLISH
The plate and tabs come from CadQuery solids. The original wall/valve capture uses
its unchanged recorded transform. The tab layout comes from the accepted coplanar
inner-plate survey; its pose against the installed capture remains an approximation.
Installed tip-to-tip distances are 3D and were not used as planar hole coordinates.
The captured rod end is an obstruction along this modeled insertion path. Removing
or retracting the rods could remove that end obstruction. The small seated overlap
remains scan/placement evidence, not a proven physical defect or certified error.

The foam example is a LOCAL STRAIGHT-EDGE section, with 6 mm nominal width and
6 mm free depth. The foam belongs to the factory inner plate, hidden in this close-up.
The 7 mm nominal inset provides the complete 6 mm band plus 1 mm extra inward backing.
Illustrative relative shift: (7.00−4.826)/2 + (5.66−4.826)/2 = 1.504 mm.
The 4.826 mm crest is a thread nominal, not an owner measurement. This is a conservative
clearance opportunity, not measured motion: the second locator and clamping constrain it.
At a 1.504 mm shift, 0.504 mm of this nominal foam band extends beyond the backing edge.
That is not a leak threshold or a full-perimeter contact prediction.

The selected plain plate still needs correct centering, firm support and factory clamping.
The removable front border gauge is a positioning aid, not a permanent fastener.
Physical fit, actual gasket contact, handle engagement and water performance remain untested.

REBUILD FROM THE REPOSITORY
./project explain-tabs --stage all
Optional: --stage preview for seven review frames. Build caches are under build/FT02/tab_explainer.
provenance.json records input hashes, geometry and the numerical illustration.
No selected plate manufacturing geometry or vendor package was changed by this explanation.
''')
    print('Captioned 36-second movie encoded; source and order files unchanged.',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['assets','preview','encode']);args=p.parse_args()
    if args.stage=='assets':prepare()
    else:encode(args.stage=='preview')
