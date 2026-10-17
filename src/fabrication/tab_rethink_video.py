"""Narrated TR02 film, using locally synthesized speech and reproducible diagrams."""
from pathlib import Path
import sys,json,math,subprocess,textwrap,wave,hashlib,html
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
BUILD=ROOT/'build/FT02/tab_rethink';OUT=ROOT/'deliverables/current/fabrication/FT02/tab-rethink'
W,H,FPS=1440,960,8
BG='#f3f6f8';DARK='#142b37';BLUE='#267f96';GOLD='#e5a143';PURPLE='#a079ad';GREEN='#237d62';RED='#bf4c40'
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
def font(s):return ImageFont.truetype(FONT,s)
CHAPTERS=[
 {'id':'correction','title':'Adding tabs does not move the foam','tag':'Correction to the first video','visual':'design','sentences':[
  'You were right. Adding tabs inside the opening does not move the foam or use up its backing margin.',
  'Both outside circles stay the same size. Only the gold areas change.',
  'My earlier video separately shifted the entire backing plate. That was a hypothetical alignment error, not something that tabs automatically cause.']},
 {'id':'water','title':'The water path we care about','tag':'Shower water entering the wall','visual':'water','sentences':[
  'Your concern is shower spray getting behind the trim and into the wall.',
  'There are two interfaces to address. The factory foam contacts the front of the custom backing. The custom backing also needs an appropriate seal to the travertine.',
  'The foam does not have to line up with the opening edge. It needs continuous effective contact around the opening. Keep the factory cover drain open toward the shower.']},
 {'id':'margin','title':'What the extra margin actually means','tag':'A deliberate offset example — not an observed movement','visual':'margin','sentences':[
  'Here the purple foam stays fixed. Blue is the backing underneath it.',
  'Only in this example, I deliberately position the whole backing two millimeters to one side. A smaller opening leaves more material underneath the same foam.',
  'A loss of full width is not a proven leak threshold. We have no validated minimum partial contact width. Keeping the whole band supported is the more forgiving target.']},
 {'id':'tabs','title':'Longer tabs, with room to adjust','tag':'Local CAD change; outside diameter stays 220 mm','visual':'design','sentences':[
  'This new study extends each tab farther inward, and uses an eighteen by ten millimeter slot.',
  'The slot extends toward the center, where the captured rods need more room in our current overlay.',
  'These are loose locating features. They help get close, while visual alignment and a suitable retention detail establish the final position. They do not need to be precision dowels.']},
 {'id':'inward','title':'More backing under the same foam','tag':'1 mm and 2 mm inward support compared','visual':'narrow','sentences':[
  'I also tested adding one and two millimeters of backing around the interior opening. The outside diameter stays unchanged.',
  'The two millimeter version has an opening about one hundred twelve by one hundred forty seven millimeters.',
  'In this nominal layout, its smallest extra foam support is about two point six millimeters, including the slots. Neither smaller opening added a captured surface clash in the tested placement.']},
 {'id':'rods','title':'Getting past the ends versus fitting around the rods','tag':'Original capture + new tab CAD; approximate placement','visual':'rods','sentences':[
  'The new slots remove the small seated clash that the earlier tight tab showed in this model.',
  'Getting the plate into position is a separate question. The captured lower left end hardware still intersects the tab during a straight approach.',
  'Check whether that end hardware comes off, or whether the rod can be retracted. Do not force the acrylic over it. This modeled overlap is not proof of a physical defect.']},
 {'id':'scans','title':'Both installed Polycam captures','tag':'Separate captures; no forced alignment','visual':'scans','sentences':[
  'Here are both actual three dimensional captures. The first shows exposed valve hardware. The second shows your inner plate attached.',
  'I have kept their source geometry separate and unchanged. The second scan is not a precision registration of the first.',
  'It confirms the attached state, but the plate and end hardware hide parts of the rod path that a new backing must clear.']},
 {'id':'numbers','title':'Do both scans disagree with your calipers?','tag':'3D end distances — not factory hole coordinates','visual':'table','sentences':[
  'They do not show one consistent error. Your rod tip distance is one hundred nine point eight millimeters.',
  'The original scan gives about one hundred nine point seven after improving the visible tip centers and using your eighty millimeter control spacing as a comparison scale. The attached scan gives about one hundred eleven point seven from visible end picks.',
  'Eighty millimeters is a calibration input here, not an independent check. Your coplanar inner plate measurements remain the stronger evidence for the factory hole layout.']},
 {'id':'handles','title':'Where the handles actually attach','tag':'Official Kohler exterior CAD + approximate inner plate','visual':'factory','sentences':[
  'The complete handles do not have to pass through the custom backing. They attach from the shower side, through the factory trim, onto the inner plate hubs and valve adapters.',
  'The hardware occupying the backing plane, and the assembly path, control our opening.',
  'The two millimeter inset still clears the factory opening footprints in this reference layout by at least about eight point six millimeters. The lower footprint is assumed, and these exterior models cannot prove hidden engagement.']},
 {'id':'formtool','title':'The proposed temporary formwork','tag':'RF01 · actual exported tool CAD · optional support repair','visual':'formtool','sentences':[
  'This is the proposed formwork. It is a separate, temporary printed tool, not another escutcheon.',
  'The front panel is two hundred forty millimeters across and twelve millimeters thick. A twelve millimeter deep collar projects behind it into the opening.',
  'The panel and collar are one piece. A separate protective cover, removable film, and a stable padded front brace complete the setup. Use it only if the fit trial finds missing support.']},
 {'id':'formsection','title':'Where repair material goes — and must not go','tag':'Illustrative side section · actual repair zones depend on sound support','visual':'formsection','sentences':[
  'This section shows the form holding the front surface of a small repair. The lined, wall-facing side sets the finished plane.',
  'Repair material is placed from the rear, only in missing support zones outside the collar. The center stays empty for the valve and service access.',
  'The fresh patch needs suitable sound substrate and permanent backing. The temporary front brace must not load the valve rods or pipes. The form does not supply the final waterproofing.']},
 {'id':'formremove','title':'Remove the tool; then fit the permanent parts','tag':'Exploded placement and withdrawal · no actual casting shown','visual':'formplace','sentences':[
  'Here the actual tool is shown apart from the captured installation, then moving toward its working position.',
  'The collar narrows slightly toward the rear, so the tool withdraws toward the shower after appropriate curing. Remove the film, pads, cover and brace too.',
  'The modeled collar clears the tested captured surfaces. Full panel seating, bracing, release and service access still need a dry rehearsal. Recheck the backing plate and handles on the finished support before sealing.']},
 {'id':'next','title':'A sensible next fit trial','tag':'More adjustment, more backing, then align and retain','visual':'next','sentences':[
  'Your proposal is worth testing: longer tabs with adjustment slots, and a modestly smaller opening for more foam support.',
  'Align the backing with the actual trim before locking its position. The bonding and sealing detail must suit acrylic or metal and travertine, and preserve service access.',
  'The new shapes are prepared as a separate study. No order files were silently replaced. The physical trial should settle end clearance, handle attachment, and continuous contact without a new measurement survey.']}
]

def speech():
    audio=BUILD/'speech';audio.mkdir(parents=True,exist_ok=True);chapters=[];clock=0
    for c in CHAPTERS:
        chunks=[];timings=[];at=.3
        for j,sentence in enumerate(c['sentences']):
            base=audio/f'{c["id"]}_{j}';txt=base.with_suffix('.txt');aiff=base.with_suffix('.aiff');wav=base.with_suffix('.wav')
            changed=not txt.exists() or txt.read_text()!=sentence
            txt.write_text(sentence)
            valid=False
            if wav.exists():
                with wave.open(str(wav)) as f:valid=f.getnframes()/f.getframerate()>len(sentence.split())/5
            if changed or not valid:
                subprocess.run(['/usr/bin/say','-v','Samantha','-r','172','-f',str(txt),'-o',str(aiff)],check=True)
                subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(aiff),'-ar','24000','-ac','1','-c:a','pcm_s16le',str(wav)],check=True)
            with wave.open(str(wav)) as f:raw=f.readframes(f.getnframes());duration=f.getnframes()/f.getframerate()
            assert duration>len(sentence.split())/5, 'Speech service produced empty/truncated audio: '+str(wav)
            timings.append({'start':at,'end':at+duration,'text':sentence});at+=duration+.2;chunks.append(raw)
        duration=math.ceil((at+.7)*FPS)/FPS
        merged=b'\x00\x00'*int(.3*24000)
        for raw in chunks:merged+=raw+b'\x00\x00'*int(.2*24000)
        merged+=b'\x00\x00'*max(0,int(duration*24000)-len(merged)//2)
        path=audio/(c['id']+'.wav')
        with wave.open(str(path),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(24000);f.writeframes(merged)
        chapters.append({**c,'start':clock,'duration':duration,'sentences_timed':timings,'audio':str(path.relative_to(ROOT))});clock+=duration
    (BUILD/'story.json').write_text(json.dumps({'voice':'macOS Samantha, synthetic narration','rate_wpm':172,'fps':FPS,'duration':clock,'chapters':chapters},indent=2)+'\n')
    print(f'Prepared {len(chapters)} spoken chapters, {clock:.1f} seconds.',flush=True)

def text(d,xy,s,size=28,fill=DARK,anchor=None):d.text(xy,s,font=font(size),fill=fill,anchor=anchor)
def wrap(d,xy,s,width=80,size=27,fill=DARK):
    for j,line in enumerate(textwrap.wrap(s,width)):text(d,(xy[0],xy[1]+j*(size+9)),line,size,fill)
def arrow(d,p,q,color=BLUE,width=5):
    d.line([p,q],fill=color,width=width);a=math.atan2(q[1]-p[1],q[0]-p[0]);L=14
    d.polygon([q,(q[0]-L*math.cos(a-.5),q[1]-L*math.sin(a-.5)),(q[0]-L*math.cos(a+.5),q[1]-L*math.sin(a+.5))],fill=color)
def poly(d,p,center,scale,fill,outline=None,width=3):
    xy=[(center[0]+x*scale,center[1]-y*scale) for x,y in p.exterior.coords];d.polygon(xy,fill=fill)
    if outline:d.line(xy,fill=outline,width=width)
    for hole in p.interiors:d.polygon([(center[0]+x*scale,center[1]-y*scale) for x,y in hole.coords],fill=BG)
def circle(d,c,r,fill=None,outline=None,width=3):d.ellipse((c[0]-r,c[1]-r,c[0]+r,c[1]+r),fill=fill,outline=outline,width=width)

def render_image(key,u):
    # The camera clips finish at a front-facing inspection pose and then hold.
    n=min(36,1+int(min(u/.7,1)*35));p=BUILD/'renders'/key/f'{n:03d}.png'
    return Image.open(p).convert('RGB'),json.loads(p.with_suffix('.json').read_text())

def model_panel(canvas,key,u,box,add_labels=True,crop=False):
    image,labs=render_image(key,u);bx,by,bw,bh=box
    ratio=(max if crop else min)(bw/1200,bh/700)
    w,h=round(1200*ratio),round(700*ratio);x=bx+(bw-w)//2;y=by+(bh-h)//2
    image=image.resize((w,h),Image.Resampling.LANCZOS)
    if crop:
        image=image.crop((bx-x,by-y,bx-x+bw,by-y+bh));canvas.paste(image,(bx,by))
    else:canvas.paste(image,(x,y))
    if add_labels:
        d=ImageDraw.Draw(canvas)
        for lab in labs:
            px,py=lab['pixel'];xx=x+px*w/1200;yy=y+py*h/700
            if len(lab['text'])==1:
                circle(d,(xx,yy),6,fill='#f7e3b3',outline=DARK,width=2);text(d,(xx+10,yy-27),lab['text'],27)
            else:
                txt=lab['text'];size=24;tw=d.textbbox((0,0),txt,font=font(size))[2]
                xx=min(max(x+8,xx-tw/2),x+w-tw-8);yy=max(y+8,yy)
                d.rounded_rectangle((xx-6,yy-4,xx+tw+6,yy+31),radius=5,fill='#f3f6f8')
                text(d,(xx,yy),txt,size)

def water(canvas,u):
    from src.fabrication.fit_trial import rr
    d=ImageDraw.Draw(canvas);c=(420,450);s=2.55
    circle(d,c,110*s,fill=BLUE)
    poly(d,rr(116.35,151.1,58.175),c,s,BG)
    foam=rr(130.35,165.1,40).difference(rr(118.35,153.1,34))
    # Draw only the real band area, keeping the view of the blue support inside it.
    mask=Image.new('L',canvas.size,0);md=ImageDraw.Draw(mask)
    xy=[(c[0]+x*s,c[1]-y*s) for x,y in foam.exterior.coords];md.polygon(xy,fill=255)
    for h in foam.interiors:md.polygon([(c[0]+x*s,c[1]-y*s) for x,y in h.coords],fill=0)
    ink=Image.new('RGB',canvas.size,PURPLE);canvas.paste(ink,(0,0),mask)
    circle(d,c,105*s,outline=GREEN,width=8)
    text(d,(420,765),'Front view: inner plate hidden to show its foam',23,anchor='mm')
    text(d,(795,225),'1  Foam → custom backing',32,PURPLE)
    wrap(d,(795,280),'A continuous contact band around the opening. Edge-to-edge alignment is unnecessary.',35,27)
    arrow(d,(770,265),(570,290),PURPLE)
    text(d,(795,415),'2  Backing → travertine',32,GREEN)
    wrap(d,(795,470),'A separate, appropriate perimeter seal behind the backing. Bonding and sealing need a defined detail.',35,27)
    arrow(d,(770,460),(675,500),GREEN)
    wrap(d,(795,640),'Factory cover drain remains open on the shower side.',35,27)
    for y in [225,345,465]:arrow(d,(85,y),(150,y+18),BLUE,4)
    text(d,(70,175),'Shower spray',25,BLUE)
    text(d,(420,450),'Opening to valve',27,anchor='mm')

def margin(canvas,u):
    d=ImageDraw.Draw(canvas)
    shift=2*min(max((u-.22)/.40,0),1)
    for i,reserve in enumerate([1,3]):
        x0=90+i*710;y0=530;scale=43
        text(d,(x0,190),'Original local edge' if i==0 else '+2 mm inward backing',31)
        # All local sections are schematic. The fixed foam occupies x=0..6.
        left=x0+105;end=left+(6+reserve-shift)*scale
        d.rectangle((x0,y0,end,y0+42),fill=BLUE)
        d.rectangle((left,y0-118,left+6*scale,y0),fill=PURPLE)
        d.rectangle((left-18,y0-143,left+6*scale+55,y0-118),fill='#75838b')
        text(d,(left+3*scale,y0-92),'6 mm wide foam',25,'white',anchor='mm')
        text(d,(left+100,y0-175),'Inner plate stays fixed',26,anchor='mm')
        text(d,(x0,y0+62),'Blue backing',26,BLUE)
        text(d,(end+16,y0+9),'Opening',24)
        supported=min(6,max(0,6+reserve-shift))
        text(d,(x0,660),f'Foam backed: {supported:.1f} / 6.0 mm',31,GREEN if supported==6 else DARK)
        text(d,(x0,708),f'Deliberate relative offset: {shift:.1f} mm',25)
        if shift>0:arrow(d,(left+80,y0+118),(left+80-shift*scale,y0+118),DARK,4)
    text(d,(720,790),'Local straight-edge illustration. It does not specify a safe partial seal width.',24,anchor='mm')

def table(canvas,u,analysis):
    d=ImageDraw.Draw(canvas)
    cols=[85,435,750,1090];headers=['3D tip pair','Your caliper','Original: new picks*','Attached: picks*']
    for x,s in zip(cols,headers):text(d,(x,210),s,25)
    for i,row in enumerate(analysis['scan_comparison']):
        y=270+i*66
        if row['pair']=='A-B':d.rounded_rectangle((65,y-7,1370,y+49),radius=8,fill='#e0ecee')
        for x,s in zip(cols,[row['pair'],f'{row["owner_3d_mm"]:g} mm',f'{row["original_refitted_80_anchor_3d_mm"]:.1f} mm',f'{row["attached_visible_picks_3d_mm"]:.1f} mm']):text(d,(x,y),s,31)
    text(d,(85,700),'* Both comparisons use U–L = 80 mm as an input, not a validation result.',25)
    text(d,(85,739),'Factory bore centers: 113.21 mm apart in the separate, coplanar R006 survey.',25)
    text(d,(85,778),'Tip spacing is a different 3D quantity; it is not a reason to change those holes.',25)

def formsection(canvas,u):
    d=ImageDraw.Draw(canvas)
    # Schematic x is depth: left = rear, right = shower; y is distance from axis.
    # The 0.05 mm film is exaggerated. Missing repair region is illustrative.
    wallx=760;panelw=85;rearx=675
    text(d,(300,175),'REAR / CLOSET',27,anchor='mm');text(d,(1110,175),'SHOWER SIDE',27,anchor='mm')
    d.rectangle((500,240,wallx,370),fill='#cfb996');text(d,(624,277),'Existing',27,anchor='mm');text(d,(624,310),'sound wall',27,anchor='mm')
    d.rectangle((rearx,370,wallx,480),fill='#b7ceb1');text(d,(620,413),'Small supported repair',25,anchor='rm')
    arrow(d,(628,420),(715,420),GREEN)
    d.rectangle((rearx-15,370,rearx,480),fill='#8d775b')
    text(d,(620,462),'Permanent backing required',23,anchor='rm');arrow(d,(628,463),(rearx-7,463),'#8d775b',3)
    d.rectangle((wallx,240,wallx+panelw,505),fill=BLUE)
    d.rectangle((rearx,480,wallx+panelw,505),fill=BLUE)
    d.line([(rearx,478),(wallx-4,478),(wallx-4,240)],fill=PURPLE,width=5)
    d.line([(wallx,215),(wallx,670)],fill='#324c58',width=2)
    text(d,(880,272),'12 mm front panel',27,BLUE)
    text(d,(880,329),'Wall-facing molding face',25)
    arrow(d,(875,365),(wallx-4,351),PURPLE)
    text(d,(880,394),'Removable liner',25,PURPLE)
    text(d,(880,435),'(thickness exaggerated)',22)
    text(d,(510,570),'NO FILL: valve + service space',29,DARK)
    arrow(d,(rearx+5,518),(rearx+84,518),BLUE)
    text(d,(540,518),'12 mm collar depth',24,anchor='rm')
    arrow(d,(900,630),(1230,630),BLUE,8);text(d,(1060,672),'Withdraw toward shower',26,anchor='mm')
    text(d,(720,748),'Brace the panel from the front against a sound independent reaction.',26,anchor='mm')
    text(d,(720,788),'No load on rods or pipes. No fill across the whole cavity.',26,anchor='mm')

def next_panel(canvas,u,analysis):
    model_panel(canvas,'primary',1,(25,180,725,490),True,crop=True);d=ImageDraw.Draw(canvas)
    text(d,(800,215),'A promising study to trial',34)
    steps=['Longer tabs + 18 × 10 mm slots','1–2 mm more inward support','Visually align before retaining','Inspect continuous contact','Fit real handles and preserve drain']
    for j,s in enumerate(steps):text(d,(800,285+74*j),str(j+1)+'. '+s,27)
    wrap(d,(65,730),'Geometry checked. Physical assembly, the bonding/seal detail and shower-spray performance remain to be established.',94,26)

def frame(c,t,total,analysis):
    im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im);u=t/c['duration']
    d.rectangle((0,0,W,133),fill=DARK)
    text(d,(42,24),c['title'],43,'white');text(d,(44,85),c['tag'],26,'#afd3dc')
    visual=c['visual']
    if visual=='water':water(im,u)
    elif visual=='margin':margin(im,u)
    elif visual=='table':table(im,u,analysis)
    elif visual=='formsection':formsection(im,u)
    elif visual=='scans':
        model_panel(im,'primary_bare',u,(30,205,680,555),crop=True);model_panel(im,'attached',u,(730,205,680,555),crop=True)
        d=ImageDraw.Draw(im);text(d,(370,160),'Original exposed-hardware scan',29,anchor='mm');text(d,(1070,160),'Later attached-inner-plate scan',29,anchor='mm')
        text(d,(720,800),'Two diagnostic frames. No stretching or forced alignment. A = upper-right rod; B = lower-left.',24,anchor='mm')
    elif visual=='rods':
        model_panel(im,'rod_A',u,(30,205,680,555),False,crop=True);model_panel(im,'rod_B',u,(730,205,680,555),False,crop=True)
        d=ImageDraw.Draw(im);text(d,(370,165),'A · upper-right',31,anchor='mm');text(d,(1070,165),'B · lower-left',31,anchor='mm')
        text(d,(720,800),'Shown seated. The full straight insertion path still meets captured B end hardware.',25,anchor='mm')
    elif visual=='next':next_panel(im,u,analysis)
    elif visual=='factory':
        model_panel(im,visual,u,(200,150,1040,605),False)
        d=ImageDraw.Draw(im)
        for pos,label,target in [((70,220),'Handles / hubs',(605,325)),((1010,285),'Custom backing',(940,420)),((1030,560),'Inner plate',(885,525))]:
            arrow(d,(pos[0]+75,pos[1]+40),target,DARK,3)
            tw=d.textbbox((0,0),label,font=font(26))[2];d.rectangle((pos[0]-4,pos[1]-3,pos[0]+tw+4,pos[1]+34),fill=BG);text(d,pos,label,26)
        text(d,(720,794),'Decorative cover hidden. Exterior CAD does not prove hidden connection depths.',25,anchor='mm')
    else:
        model_panel(im,visual,u,(20,145,1400,680),True)
        d=ImageDraw.Draw(im)
        if visual=='design':
            text(d,(720,794),'Outer circle unchanged • Foam position unchanged • Gold = local tab additions',25,anchor='mm')
        if visual=='narrow':
            # Caption areas are aligned with the three rendered CAD solids.
            for x,row in zip([365,720,1075],analysis['inward_support_variants']):
                text(d,(x,682),f'{row["capsule_mm"][0]:.2f} × {row["capsule_mm"][1]:.2f} mm',27,anchor='mm')
                text(d,(x,725),f'Extra land ≈ {row["nominal_min_foam_reserve_including_slots_mm"]:.2f} mm',23,anchor='mm')
            text(d,(720,792),'Counts all inner cut edges, including slots. Foam outline remains approximate.',24,anchor='mm')
        if visual=='factory':text(d,(720,794),'Decorative cover hidden. Official exterior geometry does not show hidden mating details.',25,anchor='mm')
        if visual=='formtool':text(d,(720,794),'Same one-piece tool, two views • Gold highlights the 12 mm rear collar',25,anchor='mm')
        if visual=='formplace':
            d.rectangle((0,770,W,834),fill=BG)
            text(d,(720,794),'Approximate working pose; no fill, repaired wall, brace or established full-face fit is implied.',24,anchor='mm')
    d=ImageDraw.Draw(im);d.rectangle((0,835,W,H),fill=DARK)
    current=next((s['text'] for s in c['sentences_timed'] if s['start']<=t<s['end']+.2),'')
    for j,line in enumerate(textwrap.wrap(current,100)):text(d,(42,847+j*29),line,26,'white')
    elapsed=c['start']+t
    d.rectangle((0,951,W*elapsed/total,959),fill='#7dbecc')
    text(d,(1395,935),f'{int(elapsed)//60}:{int(elapsed)%60:02d} / {int(total)//60}:{int(total)%60:02d}',18,'#bfd2d8',anchor='ra')
    return im

def stamp(t):
    ms=int(round(t*1000));return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'

def encode():
    story=json.loads((BUILD/'story.json').read_text());a=json.loads((BUILD/'analysis.json').read_text())
    clips=BUILD/'clips';clips.mkdir(exist_ok=True);shots=OUT/'stills';shots.mkdir(exist_ok=True);srt=[];transcript=[]
    for c in story['chapters']:
        dest=clips/(c['id']+'.mp4')
        cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-', '-i',str(ROOT/c['audio']),'-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-r','24','-c:a','aac','-b:a','128k','-ar','48000','-af','loudnorm=I=-16:TP=-1.5:LRA=11','-t',str(c['duration']),str(dest)]
        proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
        for n in range(round(c['duration']*FPS)):
            im=frame(c,n/FPS,story['duration'],a);proc.stdin.write(im.tobytes())
            if n==round(c['duration']*.72*FPS):im.save(shots/(c['id']+'.jpg'),quality=93)
        proc.stdin.close();assert proc.wait()==0
        for s in c['sentences_timed']:
            srt.append(f'{len(srt)+1}\n{stamp(c["start"]+s["start"])} --> {stamp(c["start"]+s["end"])}\n{s["text"]}\n')
        transcript.append(f'{stamp(c["start"]).split(",")[0]} — {c["title"]}\n'+'\n'.join(c['sentences'])+'\n')
        print('Encoded '+c['id'],flush=True)
    listing=clips/'concat.txt';listing.write_text(''.join("file '"+str(clips/(c['id']+'.mp4'))+"'\n" for c in story['chapters']))
    dest=OUT/'TR02_tabs_foam_and_two_scans_NARRATED.mp4'
    subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(dest)],check=True)
    (OUT/'TR02_captions.srt').write_text('\n'.join(srt));(OUT/'TR02_transcript.txt').write_text('TR02 — synthetic narration using macOS Samantha\n\n'+'\n'.join(transcript))
    (OUT/'story.json').write_text(json.dumps(story,indent=2)+'\n')
    write_page(story,a)
    add_study_links(a)
    print('Saved narrated movie and transcript.',flush=True)

def add_study_links(a):
    rows=''.join('<tr><td>'+str(r['inward_per_edge_mm'])+' mm</td><td>'+
                 f'{r["capsule_mm"][0]:.2f} × {r["capsule_mm"][1]:.2f}'+'</td><td>'+
                 f'{r["nominal_min_foam_reserve_including_slots_mm"]:.2f} mm'+'</td><td><a href="'+
                 Path(r['step']).name+'">Study STEP</a></td></tr>' for r in a['inward_support_variants'])
    extra='''<h2>Review the isolated study parts</h2><p>Each STEP is one custom solid, Ø220 mm and 1.50 mm thick. The variants below share the larger tabs and slots. They are for reviewing the new direction, not current vendor upload files. Enlarging the stock thickness or moving the plate requires the depth check to be repeated.</p><table><tr><th>Inward boundary change</th><th>Opening, mm</th><th>Minimum extra modeled foam support</th><th>CAD</th></tr>'''+rows+'''</table><p>The 2 mm version is the promising next trial direction. Its slot edge limits the extra land to 2.55 mm in the current nominal layout. That is a model clearance, not a measured tolerance or proof of sealing.</p><h2>The proposed RF01 formwork</h2><p>The video uses the existing exported one-piece tool: Ø240 mm front panel, 12 mm thick; a 12 mm rearward collar with a 2 mm wall and 1° draft. The two isolated views are the same tool, not two parts to order. Gold highlights the collar. The placement scene shows the actual tool against the original capture, while the section is an illustration of a small supported repair, not evidence of hidden wall construction.</p><p>Use the tool only if the physical plate trial finds missing support. The wall-facing lined face sets the repair datum. Place material from the rear only in supported missing zones outside the collar; keep the valve and service opening empty. Independent padded bracing, removable protection and liner are required but are not dimensioned or load-certified by this movie. After appropriate cure, pull the tool toward the shower and remove every temporary item. The actual full face must seat and withdraw freely in a dry rehearsal before filling.</p><p><a href="../REPAIR_FORM_SETUP.html">Existing RF01 setup and removal instructions</a> · <a href="../REPAIR_FORM_DRAWING.pdf">Tool drawing</a> · <a href="../REPAIR_FORM_TRIAL/RF01_MAIN_REMOVABLE_FORM_PETG.step">Actual RF01 tool STEP</a>. The as-cast front opening is about 118.45 × 145.20 mm; it is intentionally different from the custom backing's opening. No form geometry or order package was changed for this video.</p>'''
    p=OUT/'index.html';body=p.read_text();body=body.replace('<h2>Water sealing concept</h2>',extra+'<h2>Water sealing concept</h2>');p.write_text(body)
    notice='''<section id="tr02-explanation-update"><h2>October 17: updated narrated explanation</h2><p>Adding tabs does not move the foam or consume its support margin. The earlier comparison separately moved the whole backing. TR02 now tests longer loose slots and a modestly smaller opening, with both installed scans, handle access and the actual RF01 formwork. <a href="tab-rethink/index.html">Watch the new narrated video and read the study</a>. The historical tab rejection below describes the earlier candidates; the current order files have not been replaced.</p></section>'''
    for name in ['index.html','ORDER_AND_NEXT_STEP.html','ENGINEERING_RECORD.html']:
        page=OUT.parent/name;body=page.read_text()
        if 'id="tr02-explanation-update"' not in body:page.write_text(body.replace('<section>',notice+'<section>',1))

def write_page(story,a):
    rows=''.join('<tr><th>'+r['pair']+'</th>'+''.join(f'<td>{r[k]:.2f}</td>' for k in ['owner_3d_mm','original_stored_picks_3d_mm','original_refitted_80_anchor_3d_mm','attached_visible_picks_3d_mm'])+'</tr>' for r in a['scan_comparison'])
    chapters=''.join(f'<li><button onclick="document.querySelector(\'video\').currentTime={c["start"]};document.querySelector(\'video\').play()">{stamp(c["start"]).split(",")[0]} · {html.escape(c["title"])}</button></li>' for c in story['chapters'])
    transcript=''.join(f'<h3>{html.escape(c["title"])}</h3><p>'+html.escape(' '.join(c['sentences']))+'</p>' for c in story['chapters'])
    (OUT/'index.html').write_text('''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Tabs, foam and both scans — narrated explanation</title><style>body{font:18px/1.55 system-ui;background:#f3f6f8;color:#142b37;margin:30px auto;max-width:1100px;padding:0 22px}video{width:100%;background:#142b37}h1{font-size:34px}table{border-collapse:collapse;width:100%;font-size:15px}th,td{border-bottom:1px solid #bccbd1;text-align:left;padding:10px}button{font:inherit;border:0;background:transparent;color:#126c81;text-align:left;cursor:pointer}li{margin:6px 0}.note{border-left:5px solid #e5a143;padding:10px 18px;background:white}a{color:#126c81}details{margin:25px 0}</style></head><body><h1>Tabs do not move the foam</h1><p>TR02 · October 17, 2026 · Narrated design study</p><p class="note">The earlier video combined two separate events: adding tabs and moving the whole backing. Adding tabs alone consumes no foam margin. Larger slots can allow adjustment; the installer then aligns and retains the backing. The concern here is shower spray entering the wall.</p><video controls preload="metadata" poster="stills/correction.jpg" src="TR02_tabs_foam_and_two_scans_NARRATED.mp4"></video><p><a href="TR02_transcript.txt">Transcript</a> · <a href="TR02_captions.srt">Captions</a> · <a href="TR02_tabs_scans_and_handles.blend">Both scans and CAD in Blender</a> · <a href="analysis.json">Calculations and limitations</a></p><ol>'''+chapters+'''</ol><h2>Two independent scans, compared correctly</h2><p>All distances below are 3D tip/end distances in millimeters. They are not hole coordinates. The original frozen picks are retained for transparency. Refitted centers and the later attached scan are diagnostic comparisons, each using U–L=80 mm as a scale anchor. Their agreement at 80 is not validation.</p><table><tr><th>Pair</th><th>Owner caliper</th><th>Original stored picks</th><th>Original refitted + 80 anchor</th><th>Attached visible picks</th></tr>'''+rows+'''</table><p>A means upper-right rod; B means lower-left. The attached scan has different fitted hardware, distorted reflective surfaces and hidden contacts. The original refit varies about 109.3–109.9 mm for A–B across selected front-cap depth bands; that sensitivity is not a physical accuracy bound. The attached outline width is approximately 134.5 mm, versus the owner's coplanar 130.35 mm. Do not average these scans or use their scatter as machining tolerance.</p><p>The separate R006 factory-hole layout is coplanar and higher-confidence. Its derived 113.21 mm bore-center spacing is a different quantity from the 109.8 mm installed rod-tip distance. Hole depth, inclination, loose fit, scan error and assembly pose remain separate effects.</p><h2>What changed in the new study</h2><p>The outer circle remains Ø220 mm. The extended tabs use 18 × 10 mm inward-running slots, with nominal 4 mm end material and 18 mm tab width. The original capsule is retained in the first comparison. Additional variants bring its boundary inward by 1 or 2 mm. Their nominal minimum extra foam support, counting all slots and the current 0.23 mm outline offset, is about 1.77 and 2.55 mm. The original is about 0.77 mm in that same full-footprint comparison. These are model margins, not calibrated physical tolerances.</p><p>The new tabs show no added captured-surface overlap at the illustrative seated Z=1–2.5 mm placement. The straight insertion sweep still intersects captured lower-left end hardware. Neither inward-ring variant adds a further overlap in that tested pose. The 2 mm inset clears the reference factory opening footprints by at least about 8.6 mm, with the lower Ø50 mm footprint provisional. Neither scan reveals all hidden mating geometry or establishes handle engagement.</p><p class="note">These STEP files are explanatory variants, not replacements for the current order files. No revised vendor upload or order occurred. The promising direction is loose locators plus modest extra land, aligned visually before a suitable retention/seal detail is finalized. Bonding suitability, support, full assembly and shower-spray performance remain physical checks.</p><h2>Water sealing concept</h2><p>The factory foam needs effective continuous contact with the custom backing; the backing needs an appropriate seal to the travertine. Matching the foam edge to the cut edge is unnecessary. Keep the factory decorative-cover drain open to the shower side. No minimum safe partial foam contact width or adhesive is specified here. A surface cover is not proof of concealed waterproofing. <a href="https://resources.kohler.com/onlinecatalog/pdf/1041504_2.pdf#page=7">Kohler's factory assembly guide, pages 7–8</a>, supports the plate seating, foam coverage and drain requirements; it does not approve this custom repair.</p><details><summary>Full narration</summary>'''+transcript+'''</details></body></html>''')

def preview():
    story=json.loads((BUILD/'story.json').read_text());a=json.loads((BUILD/'analysis.json').read_text())
    folder=BUILD/'preview';folder.mkdir(exist_ok=True)
    for c in story['chapters']:frame(c,c['duration']*.72,story['duration'],a).save(folder/(c['id']+'.jpg'),quality=93)
    sheet=Image.new('RGB',(1440,480*math.ceil(len(story['chapters'])/2)),'white')
    for i,c in enumerate(story['chapters']):sheet.paste(Image.open(folder/(c['id']+'.jpg')).resize((720,480)),(i%2*720,i//2*480))
    sheet.save(BUILD/'storyboard.jpg',quality=90)
    print('Narrated storyboard rendered.',flush=True)

def verify():
    a=json.loads((BUILD/'analysis.json').read_text());story=json.loads((BUILD/'story.json').read_text());dest=OUT/'TR02_tabs_foam_and_two_scans_NARRATED.mp4'
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(dest)]))
    v=next(s for s in probe['streams'] if s['codec_type']=='video');au=next(s for s in probe['streams'] if s['codec_type']=='audio')
    assert v['width']==W and v['height']==H and au['codec_name']=='aac'
    assert abs(float(probe['format']['duration'])-story['duration'])<1
    subprocess.run(['ffmpeg','-v','error','-i',str(dest),'-f','null','-'],check=True)
    decoded=subprocess.check_output(['ffmpeg','-v','error','-i',str(dest),'-vn','-ac','1','-ar','16000','-f','f32le','-'])
    samples=np.frombuffer(decoded,dtype='<f4')
    encoded_rms=float(np.sqrt(np.mean(samples*samples)))
    encoded_peak=float(np.max(np.abs(samples)))
    assert encoded_rms>.01 and encoded_peak<1,(encoded_rms,encoded_peak)
    for path,expected in a['sources_sha256'].items():assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected,path
    stats=[]
    for c in story['chapters']:
        with wave.open(str(ROOT/c['audio'])) as f:data=np.frombuffer(f.readframes(f.getnframes()),dtype='<i2').astype(float)/32768
        rms=float(np.sqrt(np.mean(data*data)));assert rms>.005,(c['id'],rms)
        stats.append({'chapter':c['id'],'seconds':c['duration'],'speech_rms':rms})
    result={'status':'PASS','video_codec':v['codec_name'],'audio_codec':au['codec_name'],'size':[W,H],'duration_seconds':float(probe['format']['duration']),'decoded_all_frames':True,'decoded_audio_rms':encoded_rms,'decoded_audio_peak':encoded_peak,'speech':stats,'original_sources_unchanged':True,'manufacturing_release_unchanged':True,'physical_tests':'NOT PERFORMED','video_sha256':hashlib.sha256(dest.read_bytes()).hexdigest()}
    (OUT/'video_checks.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':{'speech':speech,'preview':preview,'encode':encode,'verify':verify}[sys.argv[1]]()
