"""Blueprints, fit/research report, templates and local review from the same F005 geometry."""
from pathlib import Path
import sys,json,math,hashlib,zipfile,shutil,html,textwrap,os,base64
os.environ.setdefault('MPLCONFIGDIR',str(Path(__file__).resolve().parents[2]/'build/cache/matplotlib'))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle,Rectangle
from shapely.geometry import Polygon,Point,LineString
from shapely.affinity import translate
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3,letter,landscape
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.platypus import Paragraph,Table,TableStyle
from reportlab.lib.styles import ParagraphStyle
from pypdf import PdfReader
sys.path.insert(0,str(Path(__file__).resolve().parent));from build import ROOT,OUT,CACHE,shape2,rect2
D=json.loads((CACHE/'design.json').read_text());A=json.loads((OUT/'analysis.json').read_text());R=json.loads((ROOT/'data/derived/resolved.json').read_text());Q=json.loads((ROOT/'canon/fabrication_research.json').read_text());MC=json.loads((OUT/'mesh_path_check.json').read_text())
RF=json.loads((OUT/'reference_fit_check.json').read_text())
MM=72/25.4;NAVY='#103844';TEAL='#087e8b';RED='#b73d27';GOLD='#ab720a';INK='#152e37'
plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False,'svg.fonttype':'none','axes.titleweight':'bold'})
def plot_poly(ax,p,**kw):
 if p.is_empty:return
 if p.geom_type=='Polygon':
  x,y=p.exterior.xy;ax.fill(x,y,**kw)
  for hole in p.interiors:ax.fill(*hole.xy,color='white')
 elif hasattr(p,'geoms'):
  for g in p.geoms:plot_poly(ax,g,**kw)
def line_poly(ax,p,**kw):
 x,y=p.exterior.xy;ax.plot(x,y,**kw)
def savefig(fig,name):
 fig.savefig(OUT/'views'/f'{name}.svg',bbox_inches='tight');fig.savefig(OUT/'views'/f'{name}_diagram.png',dpi=150,bbox_inches='tight');plt.close(fig)
ap=Polygon(D['aperture']['base_convex_polygon_installed_mm']).buffer(D['aperture']['outward_radius_mm'],quad_segs=128)
# Coverage and neighbor comparison.
fig,axs=plt.subplots(1,2,figsize=(11,10))
for ax,pair in zip(axs,['A','B']):
 main=next(p for p in D['parts'] if p['id']=='MAIN-'+pair);div=next(p for p in D['parts'] if p['id']=='DIV-'+pair)
 for p in [main,div]:plot_poly(ax,shape2(p),facecolor='#d8e8eb',edgecolor=TEAL,lw=1.5)
 plot_poly(ax,ap,facecolor='white',edgecolor=TEAL,lw=1)
 plot_poly(ax,Point(*div['center_mm']).buffer(40),facecolor='white',edgecolor=TEAL,lw=1)
 for f in R['features']:
  if f.get('include_in_coverage'):
   poly=Polygon(f['contour_mm']);line_poly(ax,poly,color=RED,lw=1)
   if f['id'] in ['CUT-03','CUT-07']:ax.annotate(f['id'],poly.centroid.coords[0],xytext=(105,125 if f['id']=='CUT-03' else -15),arrowprops={'arrowstyle':'-','color':RED},color=RED,fontsize=8)
 line_poly(ax,Polygon(D['diverter_damage_trace']['contour_installed_mm']),color=RED,lw=1)
 for center,rad in [(R['trim_center_mm'],92.075),(R['diverter_tip_mm'][:2],49.2125)]:ax.add_patch(Circle(center,rad,fill=False,edgecolor='#56646a',ls='--',lw=1))
 g=next(g for g in A['neighbor_gaps'] if g['pair']==pair);ax.text(-118,-92,f"Plate gap {g['gap_mm']:.1f} mm",fontsize=9,color=TEAL)
 ax.set_aspect('equal');ax.set_xlim(-135,145);ax.set_ylim(-210,175);ax.set_title('A / round pair' if pair=='A' else 'B / rounded rectangular pair');ax.set_xlabel('Installed X (mm)');ax.set_ylabel('Installed Y (mm)');ax.grid(alpha=.12)
fig.text(.5,.02,'Red: traced damage. Dashed: factory trim. Blue: custom material. All scan distances remain conditionally scaled.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.04,1,1));savefig(fig,'coverage')
# Rear-foam sensitivity; do not convert assumptions into measurements.
fig,axs=plt.subplots(1,3,figsize=(11,5))
for ax,inset in zip(axs,[0,1.5,3]):
 outer=rect2(130.35-2*inset,165.1-2*inset,40-inset,R['inner_center_mm']);band=outer.difference(outer.buffer(-6))
 plot_poly(ax,band,facecolor='#d3a1b9',edgecolor='#8c4771',lw=.8);plot_poly(ax,ap,facecolor='#dfeff1',edgecolor=TEAL,lw=1);plot_poly(ax,band.intersection(ap),facecolor=RED,edgecolor=RED)
 ax.set_aspect('equal');ax.set_title(f'Assumed foam inset {inset:g} mm',fontsize=11);ax.set_xlim(-73,75);ax.set_ylim(-48,130);ax.axis('off')
 row=next(x for x in A['foam_sensitivity'] if x['inset_mm']==inset);text=f"Gap to foam: {row['min_gap_to_inner_band_mm']:.2f} mm" if row['conditional_continuous_land'] else f"Aperture crosses foam: {row['aperture_cuts_band_mm2']:.2f} mm²"
 ax.text(.5,-.02,text,transform=ax.transAxes,ha='center',fontsize=9,color=RED if not row['conditional_continuous_land'] else INK)
fig.suptitle('The rear foam trace is the decisive remaining aperture check',fontsize=14);fig.text(.5,.02,'6 mm band width is reported. These three rear paths are assumptions, not measurements.',ha='center',fontsize=10);fig.tight_layout(rect=(0,.06,1,.94));savefig(fig,'foam_sensitivity')
# Stud-pattern best rigid registration diagnostic.
fig,(ax,zax)=plt.subplots(1,2,figsize=(10,4.7),gridspec_kw={'width_ratios':[1.7,1]})
studs=np.array(R['studs_mm'])[:,:2];mid=studs.mean(0);direction=(studs[1]-studs[0])/np.linalg.norm(studs[1]-studs[0]);holes=np.array([mid-direction*112.05/2,mid+direction*112.05/2])
for p in holes:ax.add_patch(Circle(p,2.83,fill=False,color=TEAL,lw=2))
for p in studs:ax.add_patch(Circle(p,2.5,color=RED,alpha=.8))
ax.plot(*holes.T,color=TEAL,ls='--',label='Measured gap + assumed equal holes: 112.05 mm');ax.plot(*studs.T,color=RED,label='Captured tip centers: 108.01 mm');ax.set_aspect('equal');ax.set_xlim(-65,70);ax.set_ylim(0,85);ax.legend(loc='upper left',fontsize=8);ax.set_title('Best possible rigid alignment');ax.set_xlabel('X (mm)');ax.set_ylabel('Y (mm)')
error=A['mounting_fit']['best_rigid_registration_error_per_hole_mm'];zax.add_patch(Circle((0,0),2.83,fill=False,color=TEAL,lw=2));zax.add_patch(Circle((error,0),2.5,color=RED,alpha=.75));zax.set_xlim(-4,6);zax.set_ylim(-4,4);zax.set_aspect('equal');zax.axis('off');zax.set_title('One hole, enlarged');zax.text(1,-3.6,f'Center error {error:.2f} mm\nRadial allowance only 0.33 mm',ha='center',fontsize=10)
fig.text(.5,.01,'Conditional conflict: actual stud axes/diameters, NE hole diameter and scan scale remain unresolved.',ha='center',fontsize=9);fig.tight_layout(rect=(0,.04,1,1));savefig(fig,'stud_fit')
# Z stack, with original wall datum and explicit trial surface.
fig,ax=plt.subplots(figsize=(10.5,4.6));nw=2.524
for yy,label,tip in [(2,'SW stud',R['studs_mm'][0][2]),(1,'NE stud',R['studs_mm'][1][2])]:
 ax.barh(yy,tip,left=0,height=.22,color=RED);ax.text(tip+.4,yy,f'{tip:.2f} mm',va='center',fontsize=10);ax.text(-1,yy,label,ha='right',va='center')
ax.axvspan(1,nw,facecolor=TEAL,alpha=.5,label='1.524 mm plate; 1 mm trial seal gap')
ax.axvline(0,color=INK,lw=1.4);ax.axvline(nw+14.5,color=GOLD,ls='--',lw=2,label='Assumed cover rear at studs: 17.02 mm')
ax.axvline(11.1125,color='#777',ls=':',label='Guide limit from original finished wall: 11.11 mm')
ax.annotate('Unchanged tips extend beyond\nthe assumed cover rear',xy=(23,1.5),xytext=(17,2.8),arrowprops={'arrowstyle':'->','color':RED},color=RED)
ax.set_xlim(-.5,36);ax.set_ylim(.4,3.5);ax.set_yticks([]);ax.set_xlabel('Z out from original tile plane (mm)');ax.set_title('A backing plate does not cure the stud interference');ax.legend(loc='upper left',bbox_to_anchor=(0,-.20),fontsize=9,frameon=False,ncol=1);fig.tight_layout(rect=(0,.08,1,1));savefig(fig,'depth_stack')
# All SVG diagrams used in review; PDF plots read raster companion for reliable embedded layout.
STYLE=ParagraphStyle('body',fontName='Helvetica',fontSize=10,leading=14,textColor=colors.HexColor(INK))
SMALL=ParagraphStyle('small',parent=STYLE,fontSize=8,leading=10.8)
TITLE=ParagraphStyle('title',parent=STYLE,fontName='Helvetica-Bold',fontSize=14,leading=18)
def para(c,text,x,y,width,style=STYLE):
 p=Paragraph(text,style);w,h=p.wrap(width,2000);p.drawOn(c,x,y-h);return y-h-9
def table(c,rows,x,y,widths,fontsize=9):
 st=ParagraphStyle('cell',parent=STYLE,fontSize=fontsize,leading=fontsize*1.3)
 vals=[[Paragraph(str(v),st) for v in row] for row in rows];t=Table(vals,colWidths=widths,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#dbe9ed')),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),('LINEBELOW',(0,0),(-1,0),.7,colors.HexColor(TEAL)),('GRID',(0,1),(-1,-1),.3,colors.HexColor('#cbd6da'))]));w,h=t.wrap(2000,2000);t.drawOn(c,x,y-h);return y-h-12

def imagebox(c,path,x,y,w,h):
 if not Path(path).exists():raise FileNotFoundError(path)
 im=ImageReader(str(path));iw,ih=im.getSize();s=min(w/iw,h/ih);c.drawImage(im,x+(w-iw*s)/2,y+(h-ih*s)/2,width=iw*s,height=ih*s,mask='auto')

# Document callouts on the original render; component pixels remain unchanged.
CALLOUTS=[('1',1015,140,1115,80),('2',968,590,1125,460),('3',879,435,1080,280),('4',803,510,1120,625),('6',706,690,1120,785),('2',867,934,1120,1020),('6',315,520,140,420)]
def exploded_diagram(c,x,y,w,h):
 imagebox(c,OUT/'views/exploded_A.png',x,y,w,h)
 s=min(w/1250,h/1400);bx=x+(w-1250*s)/2;by=y+(h-1400*s)/2
 for num,px,py,lx,ly in CALLOUTS:
  tx,ty=bx+px*s,by+(1400-py)*s;cx,cy=bx+lx*s,by+(1400-ly)*s
  c.setStrokeColor(colors.white);c.setLineWidth(2.7);c.line(tx,ty,cx,cy)
  c.setStrokeColor(colors.HexColor(TEAL));c.setLineWidth(1);c.line(tx,ty,cx,cy);c.setFillColor(colors.white);c.circle(cx,cy,12,stroke=1,fill=1)
  c.setFillColor(colors.HexColor(TEAL));c.setFont('Helvetica-Bold',12);c.drawCentredString(cx,cy-4,num)
svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1250" height="1400" viewBox="0 0 1250 1400">', '<image width="1250" height="1400" href="data:image/png;base64,'+base64.b64encode((OUT/'views/exploded_A.png').read_bytes()).decode()+'"/>']
for num,px,py,lx,ly in CALLOUTS:
 svg.extend([f'<path d="M{px},{py} L{lx},{ly}" stroke="white" stroke-width="7"/>',f'<path d="M{px},{py} L{lx},{ly}" stroke="{TEAL}" stroke-width="3"/>',f'<circle cx="{lx}" cy="{ly}" r="27" fill="white" stroke="{TEAL}" stroke-width="3"/>',f'<text x="{lx}" y="{ly+10}" fill="{TEAL}" text-anchor="middle" font-family="sans-serif" font-weight="bold" font-size="30">{num}</text>'])
svg.append('</svg>');(OUT/'views/exploded_annotated.svg').write_text(''.join(svg))

def header(c,title,page,size=landscape(A3),subtitle=f"F005 / evidence {D['evidence_revision']} / DRAFT - NOT FOR FABRICATION"):
 W,H=size;c.setFillColor(colors.HexColor(NAVY));c.rect(0,H-57,W,57,fill=1,stroke=0);c.setFillColor(colors.white);c.setFont('Helvetica-Bold',19);c.drawString(28,H-29,title);c.setFont('Helvetica',9);c.drawString(29,H-45,subtitle);c.setStrokeColor(colors.HexColor('#b7cad0'));c.line(28,57,W-28,57);c.setFillColor(colors.HexColor(INK));c.setFont('Helvetica',8);c.drawString(28,40,f"SHOWER / KOHLER | mm | +X right, +Y up, +Z toward shower | {D.get('evidence_reconciled_date', D['date'])}");c.drawRightString(W-28,40,f'{page}');c.setFillColor(colors.HexColor(RED));c.setFont('Helvetica-Bold',8);c.drawString(28,26,'Quote / prototype review only. Physical fit, seal support and manufacturing release unresolved.')
def pathpoly(c,poly,ox,oy,scale=MM,stroke=TEAL,fill=None):
 co=list(poly.exterior.coords);pa=c.beginPath();pa.moveTo(ox+co[0][0]*scale,oy+co[0][1]*scale)
 for x,y in co[1:]:pa.lineTo(ox+x*scale,oy+y*scale)
 pa.close();c.setStrokeColor(colors.HexColor(stroke));c.setLineWidth(.9)
 if fill:c.setFillColor(colors.HexColor(fill))
 c.drawPath(pa,stroke=1,fill=bool(fill))
def dim(c,x1,y1,x2,y2,text,offset=17):
 c.setStrokeColor(colors.HexColor(INK));c.setFillColor(colors.HexColor(INK));c.setLineWidth(.5)
 if abs(y2-y1)<1e-7:
  y=y1-offset;c.line(x1,y1,x1,y-5);c.line(x2,y2,x2,y-5);c.line(x1,y,x2,y)
  for x,sign in [(x1,1),(x2,-1)]:c.line(x,y,x+sign*6,y+2);c.line(x,y,x+sign*6,y-2)
  c.setFont('Helvetica',10);c.drawCentredString((x1+x2)/2,y-13,text)
 else:
  x=x1-offset;c.line(x1,y1,x-5,y1);c.line(x2,y2,x-5,y2);c.line(x,y1,x,y2)
  for y,sign in [(y1,1),(y2,-1)]:c.line(x,y,x-2,y+sign*6);c.line(x,y,x+2,y+sign*6)
  c.saveState();c.translate(x-7,(y1+y2)/2);c.rotate(90);c.setFont('Helvetica',10);c.drawCentredString(0,0,text);c.restoreState()
# Blueprint pack: four part sheets, aperture definition, stack, exploded arrangement, specification/release.
blue=OUT/'blueprint_specifications_F005_DRAFT.pdf';c=canvas.Canvas(str(blue),pagesize=landscape(A3));W,H=landscape(A3)
for page,p in enumerate(D['parts'],1):
 header(c,p['id']+' / '+p['name'],page);ox,oy=370,431;center=np.array(p['center_mm']);poly=translate(shape2(p),-center[0],-center[1]);hole=translate(ap,-center[0],-center[1]) if p.get('aperture') else Point(0,0).buffer(40,quad_segs=256)
 pathpoly(c,poly,ox,oy,fill='#eef4f5');pathpoly(c,hole,ox,oy,fill='#ffffff')
 c.setDash(5,3);c.setStrokeColor(colors.HexColor('#80979f'));c.line(ox-340,oy,ox+340,oy);c.line(ox,oy-340,ox,oy+340);c.setDash()
 # Factory trim is reference-only and cannot appear in cutting files.
 fc=np.array(R['trim_center_mm'] if p['id'].startswith('MAIN') else R['diverter_tip_mm'][:2])-center;fr=92.075 if p['id'].startswith('MAIN') else 49.2125
 c.setDash(3,3);c.circle(ox+fc[0]*MM,oy+fc[1]*MM,fr*MM,stroke=1,fill=0);c.setDash()
 x0,y0,x1,y1=poly.bounds;dim(c,ox+x0*MM,oy+y0*MM,ox+x1*MM,oy+y0*MM,('OD ' if p['shape']=='circle' else 'Width ')+f'{x1-x0:.2f} mm',15)
 if p['shape']!='circle':dim(c,ox+x0*MM,oy+y0*MM,ox+x0*MM,oy+y1*MM,f'Height {y1-y0:.2f} mm',17)
 c.setFillColor(colors.HexColor(INK));c.setFont('Helvetica-Bold',9);c.drawString(ox+5,oy+7,'O / outline center');c.setFont('Helvetica',8);c.drawString(35,66,'Front view toward handles | Drawing scale 1:1 on A3 | Dashed factory trim is reference only')
 x=755;y=H-82
 y=para(c,'PART DEFINITION',x,y,390,TITLE)
 y=para(c,p['note'],x,y,390)
 rows=[['Item','Specification'],['Origin O','Center of custom outer outline; rear face Z = 0.'],['Installed O',f'X {center[0]:.3f}; Y {center[1]:.3f} mm (conditional scan frame).'],['Outer profile',f"Circle OD {p['diameter_mm']:.2f}" if p['shape']=='circle' else f"{p['width_mm']:.2f} x {p['height_mm']:.2f}; four corners R{p['radius_mm']:.2f}"],['Aperture','AP-MAIN: see sheet 5 / coordinate file' if p.get('aperture') else 'Concentric through opening OD 80.00 mm, trial dimension.'],['Separate holes','None. No countersink, thread or added bolt hole.'],['Cutting file',p['id']+'_F005_CUT_ONLY_DRAFT_NOT_FOR_FABRICATION.dxf'],['Plan area',f"{p['computed']['area_mm2']/100:.1f} cm2"],['Total cut length',f"{p['computed']['cut_length_mm']:.1f} mm"]]
 y=table(c,rows,x,y,[108,282],8.5)
 y=para(c,'CHOOSE ONE STOCK OPTION',x,y,390,TITLE)
 y=table(c,[['Suffix','Material / exact CAD thickness'],['SS060','316 stainless / 1.524 mm (0.060 inch)'],['SS125','316 stainless / 3.175 mm (0.125 inch)'],['PROTO3','Dry-fit plastic / 3.000 mm'] ],x,y,[85,305],9)
 y=para(c,'Thickness is a separate order input. The DXF profile is common to all three thicknesses. Select one suffix; do not order every file.',x,y,390,SMALL)
 y=para(c,'Quote target: XY +/-0.13 mm; global flatness <=0.5 mm, subject to shop acceptance. Actual stock thickness range must be supplied. See sheet 8 for finish, support and release conditions.',x,y,390,SMALL)
 c.showPage()
header(c,'AP-MAIN / exact generating profile and datums',5)
y=H-82;y=para(c,'One continuous aperture clears both control assemblies and the captured stud paths. No separate fastener holes are added.',30,y,1120,TITLE)
y=para(c,'The cut contour is the following closed convex polygon offset OUTWARD by 1.75 mm, with circular arc joins. The DXF and STEP contain that exact offset. Coordinates below are local to each outer-outline center O. They are design coordinates derived from the conditional scan, not accepted caliper readings. Do not scale a screenshot.',30,y,1120)
rows=[['Vertex','MAIN-A X','MAIN-A Y','MAIN-B X','MAIN-B Y']]
ca=np.array(D['parts'][0]['center_mm']);cb=np.array(D['parts'][1]['center_mm'])
for i,p in enumerate(D['aperture']['base_convex_polygon_installed_mm'],1):
 aa=np.array(p)-ca;bb=np.array(p)-cb;rows.append([str(i),f'{aa[0]:.4f}',f'{aa[1]:.4f}',f'{bb[0]:.4f}',f'{bb[1]:.4f}'])
table(c,rows,30,y,[65,110,110,110,110],9)
y2=H-170;y2=para(c,'DATUM AND INSTALLATION LOGIC',650,y2,490,TITLE)
y2=para(c,'Rear plate face = datum A, Z=0 in each STEP. Outline center O = XY origin. Front points +Z. In the installation the plate rear is shown 1 mm above tile solely as a depth scenario. The actual cured seal/support gap must be established and the handle/adapter stack rechecked.',650,y2,490)
y2=para(c,'Temporary centering method: print the matching template at 100%, verify both 100 mm bars, locate the control/stud references, then mark removable tape on intact stone at the outer top and sides. Place the clear prototype to those marks. Do not use the oversized central aperture as a locating feature.',650,y2,490)
y2=para(c,'Main A is 6 mm higher than the inferred cover center; main B is 5 mm higher. This is deliberate and makes space for the diverter companion. Measured outer-cover registration could revise these offsets.',650,y2,490)
y2=para(c,'Removal path: remove factory handles/cover and inner plate as the applicable Kohler guide permits; withdraw backing plate axially. Factory studs, adapters and valve stay unchanged unless separately corrected by the installer. Confirm actual tip/head clearance before any forcing.',650,y2,490)
y2=para(c,f'Captured forward surface check: {MC["forward_triangles_considered"]:,} clipped triangles; {MC["triangles_outside_aperture"]} outside the aperture. The mask excludes a 3 mm boundary strip of stone. Unseen geometry and physical scale remain unresolved.',650,y2,490)
c.showPage()
header(c,'Depth / sealing interfaces and correction checks',6)
imagebox(c,OUT/'views/depth_stack_diagram.png',25,345,720,420)
y=H-82;y=para(c,'ASSEMBLY ORDER',770,y,375,TITLE)
for i,t in enumerate(['Existing sound travertine and qualified support/landing repair where required.','Qualified wall-to-custom-plate surface seal; joint section and adhesion to be selected.','Custom backing plate, selected thickness.','Retained factory foam and inner plate; foam must land continuously.','Factory nuts behind decorative cover. Stud tips must not interfere.','Factory cover, notch down, correct adapters/bonnets/handles.'],1):y=para(c,f'<b>{i}.</b> {t}',770,y,375)
y=para(c,'The new surface plate does not establish concealed membrane continuity. Keep the factory bottom drain route open onto the front of the custom plate.',770,y,375)
imagebox(c,OUT/'views/foam_sensitivity_diagram.png',30,85,710,250)
y=para(c,'Z values still needed for release',770,335,375,TITLE)
y=para(c,'Stud depths/axes, local cover cavity over both nuts, rear foam footprint and installed compression, actual rear metal lands, and handle-adapter engagement. The free 15.44 mm envelope is known; the installed one is not.',770,y,375)
y=para(c,'The current 14.5 mm cavity assumption minus 15.44 mm free envelope is -0.94 mm. Compression can change that comparison, but no allowed compression has been established. Do not specify a generic 5 mm sealing tolerance.',770,y,375)
y=para(c,'No stud cut length, wood drilling or valve relocation is specified. First identify the same fasteners from both sides and verify reversible factory adjustment and retained thread engagement.',770,y,375)
c.showPage()
header(c,'Exploded assembly / measured and nominal components',7)
exploded_diagram(c,25,75,715,690)
y=H-82;y=para(c,'READ FROM WALL TOWARD HANDLES',770,y,375,TITLE)
for t in ['1 / Captured wall, valve and studs: unchanged evidence.','2 / New main and diverter backing plates: exact custom CAD.','3 / Main foam: about 6 x 6 mm section; rear footprint illustrated, not measured.','4 / Main inner plate: measured 130.35 x 165.1 mm envelope, upper opening and mounting edge constraints; formed/rear details provisional.','5 / Nuts (obscured in this view): order documented; local seats/height unmeasured.','6 / Covers, bonnets and handles: official Kohler exterior meshes. Manufacturer mesh is not a hidden-interface specification.','Diverter: retain its factory mounting plate/foam between custom plate and decorative cover. That hidden assembly is not dimensionally reconstructed; its fit is a release check.']:
 y=para(c,t,770,y,375)
y=para(c,'Exploded offsets only',770,y,375,TITLE);y=para(c,'Spacing here separates parts for explanation. It does not give installed Z dimensions, engagement lengths or an approved adjustment.',770,y,375)
y=para(c,'Main trim guide: Kohler 1216755-2-A, steps 8-15. Older guide 1041504-2-F, page 7, explicitly gives 7/16 inch maximum stud projection from finished wall. Diverter guide 1190382-2-A, steps 8-13.',770,y,375,SMALL);c.showPage()
header(c,'Fabricator specifications / release and inspection',8)
x=35;y=H-85
for title,txt in [('Scope','Manufacture custom backing plates only. The measured Kohler reference parts and source meshes are not replacement-part manufacturing data. Choose A or B and one thickness. No order has been authorized.'),('Material and finish',D['requested_shop_notes']['finish']+' Preferred metal comparison is 316 stainless; 304 #4 stock is an alternative requiring explicit material acceptance.'),('Edges and geometry',D['requested_shop_notes']['edges']+' Supply no kerf compensation in our CAD. The shop applies its process allowance. DXF has two contours only.'),('Thickness and flatness','Nominal choices: 1.524 / 3.175 mm stainless, 3.000 mm prototype. Requested XY tolerance +/-0.13 mm and global flatness <=0.5 mm are quote targets, not a guarantee. Confirm stock tolerance and finishing loss. Do not force a warped plate flat using factory nuts.'),('Support and retention','Provide sound, rigid bearing under the wall-facing plate where clamping loads enter the factory foam. Check rocking and flex before sealing. A silicone bead is not a substitute for verified support. Removable centering tape/template is required; no tile holes are authorized.')]:
 y=para(c,title.upper(),x,y,540,TITLE);y=para(c,txt,x,y,540)
x=625;y=H-85;y=para(c,'RELEASE CHECKLIST - OPEN',x,y,525,TITLE)
for t in ['Trace the actual rear foam on the template: no portion may bridge the custom aperture or a gap in support. Record minimum supported width.','Check plate insertion, stone high spots/grout crossing, worst traced cuts and separate-plate gap on the actual wall.','Reconcile actual diagonal stud axes and depths with the measured inner plate; verify stud/nut adjustment and cover seating.','Check both controls and the diverter with correct adapters, secured bonnets/handles, full permitted travel and removal/tool access.','Approve selected alloy, thickness, finish sample, support/seal detail and vendor tolerance/lead time.','Record explicit manufacturing release against F005 or a revised design before permanent manufacture.']:
 y=para(c,'[ ] '+t,x,y,525)
y=para(c,'INCOMING PART INSPECTION',x,y,525,TITLE)
y=para(c,'Measure outer size, aperture bounds/coordinates, thickness and flatness; check grain direction, scratches, burrs/tabs, and undamaged edges. Dry-fit before any permanent sealing. After the selected system has fully cured, distinguish pressure/supply leak testing from directed shower-water entry testing, with an observation path and stop on leakage.',x,y,525)
y=para(c,'Manufacturer package contains custom CAD and these sheets only. The private scan/house imagery remains in the local review and Blender project.',x,y,525,SMALL);c.showPage();c.save()
# 1:1 templates on A3 landscape with two-axis 100 mm calibration.
templates=OUT/'full_size_templates_F005_DRAFT.pdf';c=canvas.Canvas(str(templates),pagesize=landscape(A3))
for i,p in enumerate(D['parts'],1):
 header(c,p['id']+' / full-size fit template',i);ox,oy=370,431;center=np.array(p['center_mm']);poly=translate(shape2(p),-center[0],-center[1]);hole=translate(ap,-center[0],-center[1]) if p.get('aperture') else Point(0,0).buffer(40,quad_segs=256)
 pathpoly(c,poly,ox,oy,stroke=INK);pathpoly(c,hole,ox,oy,stroke=INK)
 if p.get('aperture'):
  for label,pt in [('Upper control',R['controls_mm'][1]),('Lower control',R['controls_mm'][0]),('SW stud',R['studs_mm'][0]),('NE stud',R['studs_mm'][1])]:
   xx,yy=np.array(pt[:2])-center;xx=ox+xx*MM;yy=oy+yy*MM;c.setStrokeColor(colors.HexColor('#849ba4'));c.line(xx-6,yy,xx+6,yy);c.line(xx,yy-6,xx,yy+6);c.setFont('Helvetica',8);c.drawString(xx+7,yy+4,label+' (scan reference)')
 c.setFont('Helvetica-Bold',10);c.drawCentredString(ox,oy+(poly.bounds[3]+4)*MM,'TOP / +Y')
 x=770;y=H-90;y=para(c,'PRINT AT 100% / ACTUAL SIZE',x,y,370,TITLE)
 y=para(c,'A3 landscape. Disable fit-to-page. If using Letter/A4 paper, use the PDF viewer\'s poster/tile mode at 100%, then align and tape the sheets.',x,y,370)
 y=para(c,'Measure both calibration bars below before using the profile. Paper confirms XY only. Use the matching plastic STL/DXF and known spacers for depth and insertion checks. Do not force the prototype over the hardware.',x,y,370)
 y=para(c,'For a main plate, place the actual inner plate over this template and trace the complete back foam edges. Mark any overlap with the central cutout. This resolves the narrow foam-landing uncertainty directly.',x,y,370)
 c.setStrokeColor(colors.HexColor(INK));c.setLineWidth(.7);bx,by=x+20,220
 c.line(bx,by,bx+100*MM,by);c.line(bx,by,bx,by+100*MM)
 for k in range(11):c.line(bx+k*10*MM,by-4,bx+k*10*MM,by+4);c.line(bx-4,by+k*10*MM,bx+4,by+k*10*MM)
 c.setFont('Helvetica',10);c.drawCentredString(bx+50*MM,by-18,'100.00 mm - measure this');c.saveState();c.translate(bx-15,by+50*MM);c.rotate(90);c.drawCentredString(0,0,'100.00 mm - measure this');c.restoreState();c.showPage()
c.save()
# Compact fit and vendor research report, US letter for convenient reading.
report=OUT/'fit_and_fabrication_report_F005_DRAFT.pdf';c=canvas.Canvas(str(report),pagesize=letter);LW,LH=letter
page=0
def rp(title):
 global page
 page+=1;header(c,title,page,letter);return LH-79
def end():c.showPage()
y=rp('Prepared designs / what fits now')
y=para(c,'Two coordinated pairs are prepared for prototype and quote review. Both preserve the primary scan and reuse the original Kohler trim. The current hardware cannot be claimed to fit unchanged.',30,y,552,TITLE)
imagebox(c,OUT/'views/pair_A_front.png',30,335,267,300);imagebox(c,OUT/'views/pair_B_front.png',315,335,267,300)
y=330;y=table(c,[['Design','Main / diverter','Projected gap'],['A - round','230 mm OD / 120 mm OD','6.24 mm'],['B - rounded rectangle','220 x 218 R62 / 120 x 120 R35','11.24 mm']],30,y,[135,310,107],9)
y=para(c,'Appearance views use the actual travertine and official Kohler exterior meshes. Captured hardware is hidden only in these cosmetic views so the intended appearance can be assessed; the unchanged observed state and conflicts remain in Blender. Neither image is evidence that the cover currently seats.',30,y,552)
y=para(c,'All profiles use a new shaped main aperture, not the rejected 118 x 136 mm rectangle. The separate diverter opening is an 80 mm trial and requires its factory rear-plate/foam check.',30,y,552);end()
y=rp('Fit study / measured plates and scan')
imagebox(c,OUT/'views/stud_fit_diagram.png',25,425,562,270)
y=413;y=para(c,'1. Diagonal mounting pattern',30,y,552,TITLE)
y=para(c,'106.39 mm nearest-edge gap + 5.66 mm, assuming equal small holes, gives 112.05 mm centers. The captured tip centers are 108.01 mm apart. Even the best rigid alignment leaves 2.02 mm center error per hole versus only 0.33 mm radial space around an assumed 5 mm stud. This is a model conflict; reflective tip picking, stud tilt, NE hole size and scan scale can change the real result.',30,y,552)
y=para(c,'2. Outer-cover controls',30,y,552,TITLE)
y=para(c,'The user confirmed both inside-edge gap contacts on 2026-10-15: 46.25 mm between openings and 35.23 mm from the lower opening to the bottom rim. With a hypothetical 33.79 mm lower bore, centers are 80.04 mm apart and the lower center is 52.125 mm above the rim. The lower bore remains unmeasured; exact registration is unresolved. These confirmations do not change F005 geometry.',30,y,552)
y=para(c,'3. Actual control surfaces versus old cylinders',30,y,552,TITLE)
y=para(c,'At Z about 14 mm the captured lower control surface within a 33 mm radius reaches roughly 17.1 mm radius; at Z about 18 mm it reaches about 14.2 mm. The old 30 mm-radius straight cylinder overstated that envelope. The lower bore, local cover profile and adapter/bonnet engagement still need dry-fit confirmation.',30,y,552)
y=para(c,'A separate exact inside-solid test also finds captured points inside the provisional inner plate (149-164 points over four trial foam depths) and cover (202 points). All detected points are in stud neighborhoods, with none in control neighborhoods at these trial poses. These are reference-shape conflicts, not proof of defective real parts: the stamped seats, rear cavity, foam compression and registration are unmeasured.',30,y,552,SMALL);end()
y=rp('Water entry / depth and foam support')
imagebox(c,OUT/'views/depth_stack_diagram.png',25,412,562,300)
y=405;y=para(c,'The studs still block the cover in the depth model',30,y,552,TITLE)
y=para(c,'With the thin metal and a 1 mm illustrative gap, the assumed cover rear is at Z=17.02 mm. Stud tips at 26.61 and 30.68 mm exceed it by about 9.59 and 13.65 mm. Even the 3.175 mm metal option does not eliminate that conflict. Do not convert these numbers into cutting instructions: actual local cavities, axes, adjustment and thread engagement are unknown.',30,y,552)
y=para(c,'The new aperture needs the actual rear foam trace',30,y,552,TITLE)
y=para(c,'If the 6 mm foam band follows the outer metal outline, the trial leaves about 1.45 mm from aperture to the foam inner edge. Moving that assumed path inward by 1.5 mm creates a small intersection. The former 116 mm-wide capsule placeholder is not the actual measured gasket. A back-face trace against the supplied template is more useful than guessing another diameter.',30,y,552)
y=para(c,'Handle/stem projection alone does not diagnose shower-water entry. Cover seating, the intended factory gasket path, supported contact and unobstructed drainage must work together. The free plate depth does not establish an allowed installed compression. No general 5 mm waterproofing allowance is justified.',30,y,552);end()
y=rp('Coverage / insertion / support')
imagebox(c,OUT/'views/coverage_diagram.png',30,290,552,420)
y=280
mins={p:min((x for x in A['coverage'] if x['part']==p),key=lambda x:x['after_trace_allowance_mm']) for p in ['MAIN-A','MAIN-B']}
y=table(c,[['Profile','Limiting trace','Margin after 1.5 mm trace allowance'],*[ [p,m['feature'],f"{m['after_trace_allowance_mm']:.2f} mm"] for p,m in mins.items()]],30,y,[110,140,302],9)
y=para(c,f'The forward-insertion check considers {MC["forward_triangles_considered"]:,} full-resolution clipped triangles inside the eroded wall opening: none projects beyond the new aperture. Minimum sampled clearance is {A["swept_aperture"]["min_projected_vertex_clearance_mm"]:.2f} mm. The boundary mask, hidden surfaces and unbounded scale prevent a physical clearance pass.',30,y,552)
y=para(c,'No structural load or clamp force is known. Relative stiffness of 3.175 versus 1.524 mm stainless is about 9.04x. That comparison does not prove either can bridge the actual unsupported span. Check bearing, rocking, local flex and the grout crossing before choosing thickness.',30,y,552);end()
y=rp('Prototype cost / lead-time research')
y=para(c,Q['cost_basis'],30,y,552,SMALL)
for vi,v in enumerate(Q['vendors'][:4]):
 if vi==2:
  end();y=rp('Prototype vendors / continued')
 y=para(c,f"{v['name']} / {v['process']}",30,y,552,TITLE)
 y=para(c,f"<b>Planning pair allowance: ${v['planning_pair_usd'][0]}-{v['planning_pair_usd'][1]}.</b> {v['published_price']}<br/>{v['lead']}<br/>{v['finishing']}",30,y,552,SMALL)
 y=para(c,'Source: <link href="'+v['sources'][0]+'" color="#087e8b">'+v['sources'][0]+'</link>',30,y,552,SMALL)
end()
y=rp('Metal cost / lead-time research')
y=para(c,'Prices below are unquoted planning reserves for one pair. Cosmetic finishing, taxes and shipping upgrades may add cost. Published production time is not a guaranteed delivered date.',30,y,552)
for v in Q['vendors'][4:]:
 y=para(c,f"{v['name']} / {v['process']}",30,y,552,TITLE)
 y=para(c,f"<b>Planning pair allowance: ${v['planning_pair_usd'][0]}-{v['planning_pair_usd'][1]}.</b> {v['published_price']}<br/>{v['lead']}<br/>{v['finishing']}",30,y,552,SMALL)
 y=para(c,'Source: <link href="'+v['sources'][0]+'" color="#087e8b">'+v['sources'][0]+'</link>',30,y,552,SMALL)
y=para(c,'Best next purchase path',30,y,552,TITLE);y=para(c,Q['recommendation'],30,y,552);end()
y=rp('Materials / practical release checks')
y=para(c,'Selected-system work still required',30,y,552,TITLE)
for key in ['material','prototype','seal_candidate','cure']:
 y=para(c,Q['engineering'][key],30,y,552)
y=para(c,'LATASIL DS-6200.1-0926 also requires a test area on stone; it describes joints at least 3 mm wide and approximately 2:1 width/depth for perimeter joints. It does not validate our illustrated 1 mm lap layer. A stone/metal seal detail must be reviewed before permanent installation. Factory foam and drainage must remain functional.',30,y,552)
y=para(c,'Four focused physical checks to release a design',30,y,552,TITLE)
for t in ['Rear foam: trace both edges on the full-size main template; inspect the diverter factory rear assembly too.','Hardware: remeasure the two diagonal studs and identify the rear contact; dry-fit the real inner plate, cover and handles without forcing.','On-wall prototype: confirm coverage, exact trim registration, gap between plates, flat support/rocking, full handle travel and removal access.','Final choice: select A or B, thickness, alloy/finish, validated support/seal detail and vendor quote; record explicit manufacturing release.']:
 y=para(c,'[ ] '+t,30,y,552)
y=para(c,'These checks replace repeated broad measurement requests. The accepted caliper readings are preserved; only the missing fit-critical information is needed next.',30,y,552,SMALL);end()
y=rp('Source register / scope of verification')
links=[]
for v in Q['vendors']:
 for u in v['sources']:
  if u not in links:links.append(u)
links.extend(['https://techcomm.kohler.com/techcomm/cad/T14489-4.obj','https://techcomm.kohler.com/techcomm/cad/T14491-4.obj','https://techcomm.kohler.com/techcomm/pdf/1216755-2.pdf','https://resources.kohler.com/onlinecatalog/pdf/1041504_2.pdf','https://techcomm.kohler.com/techcomm/pdf/1190382-2.pdf',Q['engineering']['seal_source']])
y=para(c,'Public primary sources reviewed 2026-10-14. Original photos, raw measurements, scan registration and the complete original goal remain in the private repository. No vendor contact, CAD upload, order, physical dry fit or water test was performed.',30,y,552)
for u in links:y=para(c,'<link href="'+u+'" color="#087e8b">'+u+'</link>',30,y,552,SMALL)
y=para(c,'Software verification includes valid single solids, STEP reimport dimensions/volume, STL watertightness, DXF reimport and two-contour checks, non-fused assemblies, captured triangle clearance, and saved Blender reopen/dimensions. These checks do not validate concealed waterproofing or installed sealing.',30,y,552,SMALL);end();c.save()
# Text report for later assistants, all numbers preserved in analysis JSON.
md=['# F005 fabrication preparation','',Q['scope'],'','## Current fit findings',f"- Mounting pattern: conditional 112.05 mm versus scan tip distance {A['mounting_fit']['scan_tip_center_distance_mm']:.3f} mm. No physical fit declared.",f"- Forward scan: {MC['forward_triangles_considered']} clipped triangles; zero conflicts with new aperture.",'- Rear foam path remains decisive: 1.5 mm inset can erase model landing.','- Unchanged studs interfere with assumed cover. No cutting/drilling/relocation specified.','- The measured outer-cover inside-edge/equal-bore scenario gives 80.04 mm centers.','', '## Costs and vendor evidence',Q['cost_basis']]
for v in Q['vendors']:md.extend(['',f"### {v['name']} - {v['process']}",f"Planning pair allowance ${v['planning_pair_usd'][0]}-{v['planning_pair_usd'][1]} (not a quote).",v['published_price'],v['lead'],v['finishing'],*['- '+s for s in v['sources']]])
md.extend(['','## Rebuild','Run `./project prepare-fabrication`. Canon is read-only input. Reconcile evidence revision before changing manufacturing geometry.','', '## Release checks','Rear foam trace; stud/cover/adapter fit; supported on-wall prototype and control travel; alloy/thickness/finish and explicit manufacturing release.'])
(OUT/'fit_report.md').write_text('\n'.join(md)+'\n');(OUT/'research.json').write_text(json.dumps(Q,indent=2)+'\n')
# Separate manufacturer/quote packages: no house scan, installation photo or nominal Kohler replacement geometry.
packages=[]
for pair in ['A','B']:
 for stock in D['stock_options']:
  name=f'quote_package_{pair}_{stock["id"]}_F005_DRAFT.zip';dest=OUT/name
  with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
   for part in ['MAIN-'+pair,'DIV-'+pair]:
    m=next(m for m in A['parts'] if m['id']==part+'-'+stock['id'])
    for k in ['step','stl']:
     z.write(OUT/m[k],Path(m[k]).name)
    f=OUT/'cad'/f'{part}_F005_CUT_ONLY_DRAFT_NOT_FOR_FABRICATION.dxf';z.write(f,f.name)
   # Blueprint contains scan-derived diagrams and exploded scan image, so include only custom drawing pages + spec.
   from pypdf import PdfWriter
   writer=PdfWriter();reader=PdfReader(blue)
   for pnum in ([0,2] if pair=='A' else [1,3])+[4,7]:writer.add_page(reader.pages[pnum])
   import io
   stream=io.BytesIO();writer.write(stream);z.writestr('custom_part_drawing_sheets_F005_DRAFT.pdf',stream.getvalue())
   readme=f'''F005 - DRAFT NOT FOR FABRICATION\nQUOTE / PROTOTYPE REVIEW ONLY; permanent manufacture on hold.\nChoose pair {pair}; quantity 1 MAIN-{pair} and 1 DIV-{pair}.\nRequested stock: {stock['material']}; exact CAD thickness {stock['thickness_mm']} mm.\nDXF units millimeters, 1:1; two closed contours, no separate fastener holes.\nDo not scale; do not make the other thickness variants shown in the reference drawing table.\nXY +/-0.13 mm and flatness <=0.5 mm are requested quote targets, not demonstrated capabilities. Confirm actual sheet thickness tolerance and finishing changes.\nDeburr all edges; remove tabs; protect satin cosmetic face. Grain direction +Y on both parts. Finish sample and support/seal fit require approval.\nNo scans, homeowner photos or Kohler replacement geometry are included.\nNo upload/order has been made. Contact/ordering requires separate user authorization.\n'''
   z.writestr('READ_ME_FIRST.txt',readme)
   paths=[info.filename for info in z.infolist()]
   z.writestr('SHA256SUMS.txt','\n'.join(hashlib.sha256(z.read(fn)).hexdigest()+'  '+fn for fn in paths)+'\n')
  packages.append(name)
# Self-contained local review; preserve user inputs in the separate measurement form.
esc=html.escape
cards=''.join(f'<figure><a href="views/{fn}.png"><img src="views/{fn}.png" alt="{esc(cap)}"></a><figcaption>{esc(cap)}</figcaption></figure>' for fn,cap in [('pair_A_oblique','A: offset round 230 mm main and 120 mm diverter'),('pair_B_oblique','B: rounded rectangular main and rounded square diverter')])
vcards=''.join(f'<tr><td><b>{esc(v["name"])}</b><br>{esc(v["process"])}</td><td>${v["planning_pair_usd"][0]}-{v["planning_pair_usd"][1]}<br><small>Planning estimate, not quote</small></td><td>{esc(v["lead"])}</td><td>{" ".join(f"<a href={json.dumps(u)}>Source {i+1}</a>" for i,u in enumerate(v["sources"]))}</td></tr>' for v in Q['vendors'])
packlinks=''.join(f'<li><a download href="{p}">{p.replace("quote_package_", "Pair ").replace("_F005_DRAFT.zip", "")}</a></li>' for p in packages)
pagehtml=f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>F005 - escutcheon designs and fabrication</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#eef3f3;color:#17333d;font:17px/1.55 system-ui,sans-serif}}main{{max-width:1200px;margin:auto;padding:28px}}nav{{background:#103844;padding:14px 28px;position:sticky;top:0;z-index:3}}nav a{{color:white;margin-right:22px}}h1{{font-size:clamp(30px,5vw,48px);line-height:1.1;margin-bottom:14px}}h2{{font-size:27px;margin-top:50px}}section{{scroll-margin-top:80px}}a{{color:#006b7d}}.lead{{font-size:21px;max-width:950px}}.flag{{border-left:5px solid #ae502c;background:#fff4e8;padding:15px 20px}}.grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}}figure{{margin:0;background:white;border:1px solid #cbd7da;border-radius:8px;overflow:hidden}}img{{width:100%;display:block}}figcaption{{padding:12px}}.diagram{{background:white;padding:16px;max-width:100%}}.links{{padding:22px;background:#fff;border-radius:8px}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:13px;text-align:left;vertical-align:top;border-bottom:1px solid #cad7dc}}th{{background:#d8e7eb}}td a{{display:inline-block;margin-right:8px}}.scroll{{overflow:auto}}small{{font-size:13px}}.checks li{{margin-bottom:12px}}@media(max-width:720px){{.grid{{grid-template-columns:1fr}}main{{padding:18px}}nav{{position:static}}nav a{{display:inline-block}}table{{min-width:760px}}}}
</style><nav><a href="#designs">Designs</a><a href="#fit">Fit findings</a><a href="#assembly">Assembly</a><a href="#vendors">Cost & timing</a><a href="#files">Files</a><a href="../../review/index.html#measurements">Measurement worksheet</a></nav><main>
<p>F005 design study / accepted measurements {D['evidence_revision']}</p><h1>Two escutcheon pairs, prepared for the next fit check.</h1><p class="lead">The real plate measurements now constrain the designs. The new shaped aperture clears the captured forward surfaces; the existing studs and the exact rear foam landing still need reconciliation.</p><p class="flag"><b>DRAFT - NOT FOR FABRICATION.</b> CAD files are prepared for quote and prototype review. No physical fit, water test, final design selection or manufacturing release has occurred.</p>
<section id="designs"><h2>Compare the designs on your travertine</h2><div class="grid">{cards}</div><p>The scan's vertical valve arrangement is preserved. A gives about <b>6.24 mm</b> between backing plates; B gives <b>11.24 mm</b>. These are conditional scan distances. The appearance views hide captured hardware only for the cosmetic comparison; no physical adjustment is asserted. Official Kohler exterior meshes supply the covers and handles.</p></section>
<section id="fit"><h2>What the supplied measurements tell us</h2><div class="grid"><div><h3>Mounting pattern needs reconciliation</h3><p>With equal 5.66 mm small holes, the measured gap implies <b>112.05 mm</b> centers. Captured tip centers give <b>108.01 mm</b>. Best rigid alignment still misses by <b>2.02 mm per hole</b>; the assumed stud allows only 0.33 mm radial clearance.</p><p>That flags the current reconstruction. It does not prove the actual plate is wrong: tip picking, stud angle, NE hole diameter and scale remain uncertain.</p></div><img class="diagram" src="views/stud_fit.svg" alt="Measured mounting pattern versus captured stud tips"></div>
<div class="grid"><img class="diagram" src="views/depth_stack.svg" alt="Unchanged stud depths extend past the assumed cover rear"><div><h3>The studs remain too far forward in the model</h3><p>The thin backing plate shifts the trial surface by 2.524 mm including a 1 mm illustrative seal gap. The unchanged stud tips still exceed the assumed cover rear by about <b>9.59 and 13.65 mm</b>. The thicker option also fails this comparison.</p><p>No cut length or drilling instruction follows from those estimates. Identify the same fasteners and verify factory adjustment, nut seats, cover cavity and retained threads.</p><h3>The cover's control spacing is plausible</h3><p>The 46.25 mm inside-edge gap and 35.23 mm lower-edge-to-rim gap are now confirmed. Provisionally using a 33.79 mm lower bore still gives <b>80.04 mm</b> centers. Only that lower bore remains unmeasured in this spacing calculation; no F005 outline or aperture changes result.</p></div></div>
<details><summary>Actual plates and reconstructed references</summary><div class="grid"><figure><img loading="lazy" src="../../review/views/inner_photo.png" alt="Your annotated inner plate front photograph"><figcaption>Your actual inner plate: measured features govern the reference.</figcaption></figure><figure><img loading="lazy" src="views/measured_inner.png" alt="Inner plate reference envelope"><figcaption>Measured envelope and openings; stamped details, sheet thickness, rear lands and nut-seat depths remain provisional.</figcaption></figure><figure><img loading="lazy" src="../../review/views/outer_photo.png" alt="Your annotated outer cover photograph"><figcaption>Your actual outer cover: diameter, upper bore and both edge gaps accepted.</figcaption></figure><figure><img loading="lazy" src="views/measured_cover.png" alt="Outer cover reference scenario"><figcaption>Confirmed edge gaps; equal lower bore remains a hypothesis. Actual rear cavity remains unmeasured.</figcaption></figure></div><p>The independent inside-solid calculation finds 149-164 captured points inside the provisional inner shell across trial foam depths, and 202 inside the cover shell. All detected points are in stud neighborhoods; none are in control neighborhoods at these trial poses. This flags unresolved model fit, not a proven defect in the actual plates. <a href="reference_fit_check.json">Detailed conditional results</a>.</p></details><h3>The rear foam trace is the deciding aperture check</h3><img class="diagram" src="views/foam_sensitivity.svg" alt="Three hypothetical foam paths showing how small inward shifts remove landing"><p>The reported 6 mm band is preserved. Its actual rear location is unknown. The zero-inset scenario leaves about 1.45 mm from the aperture to the foam; a 1.5 mm inward shift produces a small intersection. Trace both actual foam edges on the supplied full-size template.</p>
<details><summary>Coverage and captured-surface checks</summary><img class="diagram" src="views/coverage.svg" alt="Two plate outlines over traced damage and factory trim"><p>{MC['forward_triangles_considered']:,} full-resolution triangles were clipped to the forward installation path and the eroded main opening. Zero lie outside the shaped aperture. Minimum sampled clearance is {A['swept_aperture']['min_projected_vertex_clearance_mm']:.2f} mm. Hidden geometry, the excluded 3 mm stone boundary strip and scan-scale uncertainty remain. The 80 mm diverter aperture and its factory rear assembly require a separate check.</p></details></section>
<section id="assembly"><h2>Assembly and corrections</h2><div class="grid"><figure><a href="views/exploded_annotated.svg"><img src="views/exploded_annotated.svg" alt="Exploded order using actual scan and measured reference plate"></a><figcaption>Exploded offsets are for explanation; they are not installed dimensions.</figcaption></figure><div><ol class="checks"><li>Sound wall/support and a qualified wall-to-new-plate surface seal.</li><li>Custom backing plate, selected thickness.</li><li>Original foam on a continuous supported landing.</li><li>Retained factory inner plate, lying flat.</li><li>Factory nuts behind the decorative cover, with studs correctly adjusted (obscured in this view).</li><li>Cover notch down; correct adapters, bonnets and handles; full operation and drainage.</li></ol><p>The diverter retains its own factory mounting plate/foam. Its hidden assembly has not been dimensionally reconstructed. No additional holes in the travertine or the decorative covers are proposed.</p><p>Shower-water resistance depends on these interfaces together. Covering the cutout alone does not prove a watertight assembly or restore an unseen membrane.</p></div></div></section>
<section id="vendors"><h2>Prototype and metal fabrication</h2><p>{esc(Q['cost_basis'])}</p><div class="scroll"><table><tr><th>Vendor / process</th><th>Pair allowance</th><th>Published timing / conditions</th><th>Evidence</th></tr>{vcards}</table></div><p><b>Suggested first step:</b> clear 3 mm acrylic, using the same DXF, lets you see the landing and interference. It is 0.175 mm thinner than the thick metal option. Thin metal is 1.524 mm; thick metal is 3.175 mm and approximately 9.04 times as stiff for the same geometry. Neither thickness has a verified support/load test.</p><p>Stainless satin/brushed finish will not exactly match Kohler BN. Reserve separate cosmetic finishing time/cost if standard stock is unacceptable. No files have been uploaded and no quotes or orders obtained.</p></section>
<section id="files"><h2>Prepared files</h2><div class="grid"><div class="links"><p><a href="blueprint_specifications_F005_DRAFT.pdf">Eight-sheet blueprint and specification pack</a></p><p><a href="fit_and_fabrication_report_F005_DRAFT.pdf">Fit findings, material notes and vendor research</a></p><p><a href="full_size_templates_F005_DRAFT.pdf">Four full-size A3 templates with 100 mm calibration</a></p><p><a href="paired_escutcheons_F005_DRAFT.blend">Blender workspace: both pairs, observed state and exploded view</a></p><p><a href="analysis.json">Numerical analysis and export checks</a> · <a href="mesh_path_check.json">Triangle clearance check</a></p></div><div class="links"><b>Choose one pair and one thickness</b><p>Each ZIP contains only that pair's custom STEP/STL/DXF, drawing sheets, notes and hashes. No house photos or source scan.</p><ul>{packlinks}</ul></div></div><h3>Four remaining release checks</h3><ol class="checks"><li>Actual rear foam trace, plus diverter factory rear-plate/seal geometry.</li><li>Remeasured studs and real inner-plate / cover / handle fit.</li><li>On-wall prototype: coverage, spacing, rigid support, full handle travel and removal access.</li><li>Chosen material, thickness, finish, qualified seal/support detail and explicit manufacturing release.</li></ol></section></main></html>'''
(OUT/'index.html').write_text(pagehtml)
# Bound PDF text and page counts, then visual QA is performed outside this builder.
counts={p.name:len(PdfReader(p).pages) for p in [blue,report,templates]};assert counts[blue.name]==8 and counts[templates.name]==4
for p in [blue,report,templates]:assert all(page.extract_text() for page in PdfReader(p).pages)
(OUT/'document_validation.json').write_text(json.dumps({'page_counts':counts,'visual_review':'Required separately; generation does not imply visual QA','manufacturer_packages':packages},indent=2)+'\n')
print('F005 documents created',counts,'and',len(packages),'private quote packages')
