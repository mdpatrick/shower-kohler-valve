"""Engineering figures from actual exported meshes and unchanged captured surfaces."""
from pathlib import Path
import os,sys,json,math
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'build/FT02/mpl'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection,PolyCollection
from matplotlib.patches import Circle,Polygon as PP,Rectangle,FancyArrowPatch
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import numpy as np,trimesh
from shapely.geometry import LineString,Point
from shapely.affinity import affine_transform
from src.fabrication.fit_trial import rr
from src.analysis.fit_trial_release import load_capture
from src.analysis.registration_trial import coeff

def run():
 d=json.load(open(ROOT/'canon/fit_trial_design.json'));out=ROOT/d['output_directory'];r=json.load(open(out/'design_report.json'));s=json.load(open(out/'engineering/locator_evaluation.json'))
 for p in r['parts']:
  mesh=trimesh.load(out/p['files']['stl'],force='mesh');f=mesh.triangles
  fig=plt.figure(figsize=(8,4));ax=fig.add_subplot(121);top=f[np.all(f[:,:,2]>p['thickness_mm']-.001,axis=1)]
  ax.add_collection(PolyCollection(top[:,:,:2],facecolor='#a4c3cc',edgecolor='none'))
  rad=p['diameter_mm']/2;ax.set(xlim=(-rad-10,rad+10),ylim=(-rad-10,rad+10));ax.set_aspect('equal');ax.axis('off');ax.set_title('Front / +Y up')
  ax=fig.add_subplot(122,projection='3d');ax.add_collection3d(Poly3DCollection(f,facecolor='#a4c3cc',edgecolor='none',alpha=1))
  ax.set(xlim=(-rad,rad),ylim=(-rad,rad),zlim=(-rad/3,rad/3));ax.set_box_aspect((1,1,.35));ax.view_init(35,-65);ax.axis('off');ax.set_title('Actual thickness')
  fig.suptitle(p['id'],fontsize=10);fig.tight_layout();fig.savefig(out/'cad'/(p['id']+'_preview.png'),dpi=150);plt.close(fig)
 # Sections use actual primary geometry; drawings of the backing are exact selected cross-sections.
 v,f=load_capture();mesh=trimesh.Trimesh(v,f,process=False)
 tf=s['transforms']['cover_to_installed_xy_up'];Q=np.array(tf['row_rotation']);t=np.array(tf['translation_mm'])
 ap=rr(d['main']['aperture_width_mm'],d['main']['aperture_height_mm'],d['main']['aperture_radius_mm']);back=Point(0,0).buffer(110,quad_segs=256).difference(ap)
 fig,axs=plt.subplots(1,2,figsize=(11,7))
 centers=s['transforms']['mounting_centers_in_cover_frame_mm']
 for ax,(name,a,b) in zip(axs,[('Both controls',[0,-39.95],[0,40.09]),('Both mounting studs',centers['B'],centers['A'])]):
  a,b=np.array(a),np.array(b);u=(b-a)/np.linalg.norm(b-a);origin=a@Q+t;direction=u@Q;n=np.array([-direction[1],direction[0],0])
  seg=trimesh.intersections.mesh_plane(mesh,n,[*origin,0]);along=(seg[:,:,:2]-origin)@direction
  segments=np.stack([seg[:,:,2],along],axis=2)
  valid=(along.min(1)>-100)&(along.max(1)<200)&(seg[:,:,2].min(1)>-80)&(seg[:,:,2].max(1)<90)
  ax.add_collection(LineCollection(segments[valid],colors='#58646a',linewidths=.45))
  chord=back.intersection(LineString([a-u*200,a+u*200]))
  for line in getattr(chord,'geoms',[chord]):
   if line.is_empty:continue
   q=(np.array(line.coords)-a)@u;ax.add_patch(Rectangle((1,q.min()),d['stocks'][0]['thickness_mm'],q.max()-q.min(),facecolor='#16768c'))
  ax.axvline(0,c='#b99561',ls='--',lw=1);ax.set(xlim=(-25,50),ylim=(-70,150),xlabel='Z outward from nominal tile plane (mm)',ylabel='Distance along section (mm)');ax.set_title(name);ax.grid(alpha=.15)
  for lab,p in zip(['L','U'] if name=='Both controls' else ['B / SW','A / NE'],[a,b]):ax.annotate(lab,xy=(36,float((p-a)@u)),fontsize=10)
 fig.suptitle('Actual capture sections + selected backing cross-section',fontsize=14)
 fig.text(.5,.025,'Gray: unchanged primary scan surfaces. Blue: custom sheet at illustrative 1 mm bedding.\nFactory plate/handles are removed in this capture. Sections do not establish hidden contact or engagement.',ha='center',fontsize=9)
 fig.tight_layout(rect=[0,.09,1,.95]);fig.savefig(out/'sections.png',dpi=160);plt.close(fig)
 # Clear distinction among seal, support, gasket and factory drain.
 fig,axs=plt.subplots(1,2,figsize=(11,6))
 ax=axs[0];ax.add_patch(Circle((0,0),110,fc='#d7e5e9',ec='#1c6578'));ax.add_patch(PP(np.array(ap.exterior.coords),fc='white',ec='#1c6578'))
 for rad,style,col in [(110,'-','#2b8a66'),(92.075,'--','#666')]:ax.add_patch(Circle((0,0),rad,fill=False,ec=col,ls=style,lw=2.5))
 foam=d['foam'];outer=rr(130.35,165.1,40);inner=rr(118.35,153.1,34)
 for p in [outer,inner]:ax.plot(*p.exterior.xy,c='#af7a2c',lw=2)
 ax.annotate('NEW wall-to-backing perimeter seal',xy=(-100,44),xytext=(-126,135),arrowprops={'arrowstyle':'->'},fontsize=9)
 ax.annotate('Factory drain at cover bottom',xy=(0,-92.075),xytext=(-120,-132),arrowprops={'arrowstyle':'->'},fontsize=9)
 ax.plot([0,0],[-91,-108],c='#2a8cb6',lw=3);ax.annotate('',xy=(0,-109),xytext=(0,-93),arrowprops={'arrowstyle':'->','color':'#2a8cb6'})
 ax.set(xlim=(-140,140),ylim=(-145,150));ax.set_aspect('equal');ax.axis('off');ax.set_title('Front: separate water paths')
 ax=axs[1];ax.axis('off');ax.set(xlim=(0,110),ylim=(0,105))
 for x,w,c,lab in [(5,15,'#c3b392','Sound stone /\nlocal solid repair'),(30,3,'#5c98aa','Custom plate'),(45,9,'#b88c49','Factory foam'),(66,4,'#9c9f9e','Inner plate'),(91,4,'#aeb9bb','Cover')]:
  ax.add_patch(Rectangle((x,20),w,48,fc=c,ec='#344f57'));ax.text(x+w/2,77,lab,ha='center',va='bottom',fontsize=8)
 ax.plot([28,28],[20,68],c='#2b8a66',lw=3);ax.text(25,9,'Seal at outer edge; support is a separate solid load path',ha='left',fontsize=8,wrap=True)
 ax.text(53,98,'Toward shower  →',ha='center',fontsize=12)
 ax.text(8,1,'Exploded section. No prescribed foam compression or bedding height.',fontsize=8)
 fig.suptitle('Support the sheet; seal the new interface; preserve the factory drain',fontsize=14)
 fig.text(.5,.015,'Gold: edge-flush factory gasket footprint, approximately 6 mm wide. Green: continuous new outer perimeter joint.\nFactory drain discharges onto the FRONT of the new plate. Do not copy that opening into the new rear seal.',ha='center',fontsize=9)
 fig.tight_layout(rect=[0,.1,1,.94]);fig.savefig(out/'support_seal.png',dpi=160);plt.close(fig)
 print('Exported-part previews, actual capture sections and support/seal figure generated.')
if __name__=='__main__':run()
