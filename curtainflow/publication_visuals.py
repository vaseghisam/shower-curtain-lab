"""Reproduce publication figures and animations from equations and saved data.

No CFD is rerun. Analytic demonstrations are explicitly separate from the
three-dimensional droplet/air and prescribed-load strip calculations.
Every public output is decoded before atomic replacement. Use --only verify
to check analytic benchmarks and all recorded hashes/media without rerendering.
"""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, FFMpegWriter, PillowWriter
from matplotlib.colors import SymLogNorm
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle, Circle
from PIL import Image
from scipy.integrate import solve_ivp
from .render import _atomic_export, _verify_export, load_case, load_structure, PRESSURE_CMAP
from .averaging import mean_over_window
from .mechanics import exact_profile, equilibrium

ROOT=Path(__file__).resolve().parents[1]
ASSETS=ROOT/'assets'
STYLE=ASSETS/'style/messi_style.py'
spec=importlib.util.spec_from_file_location('publication_style',STYLE)
style=importlib.util.module_from_spec(spec);spec.loader.exec_module(style)
C=style.COLORS
PAPER=C['warm_background'];INK=C['ink'];MUTED=C['muted'];BLUE=C['blue'];RED=C['red'];TEAL=C['teal']
COLORS=(BLUE,RED,C['navy']);LABELS=('Spray','Heating','Spray + heating')
KINDS=('spray','heat','both')
plt.rcParams.update({'figure.facecolor':PAPER,'axes.facecolor':PAPER,'savefig.facecolor':PAPER,
 'text.color':INK,'axes.labelcolor':INK,'xtick.color':MUTED,'ytick.color':MUTED,
 'font.family':'DejaVu Sans','font.size':13,'axes.titlesize':15,'axes.labelsize':13,
 'axes.spines.top':False,'axes.spines.right':False,'axes.edgecolor':C['line'],
 'svg.fonttype':'none','grid.color':C['line'],'grid.alpha':.7})


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def source(path):
 path=Path(path);return {'file':str(path.relative_to(ROOT)),'sha256':digest(path)}
def register(name,files,sources=(),**details):
 path=ASSETS/'publication_manifest.json'
 manifest=json.loads(path.read_text()) if path.exists() else {}
 manifest[name]={'files':[source(p) for p in files], 'sources':[source(p) for p in sources],**details}
 _atomic_export(path,lambda p:p.write_text(json.dumps(manifest,indent=2)+'\n'))

def header(title,subtitle,kind='CALCULATED',animation=False):
 fig=plt.figure(figsize=(14 if animation else 16,9),dpi=100)
 fig.text(.05,.937,kind,fontsize=12,fontproperties=style.SANS_BOLD,color=MUTED)
 fig.text(.05,.872,title,fontsize=27 if animation else 29,fontproperties=style.SERIF_BOLD)
 fig.text(.05,.821,subtitle,fontsize=14 if animation else 15,color=MUTED)
 return fig

def footer(fig,text,second=''):
 fig.lines.append(Line2D([.05,.95],[.106,.106],transform=fig.transFigure,color=C['line'],lw=1))
 fig.text(.05,.066,text,fontsize=11,color=MUTED)
 if second:fig.text(.05,.035,second,fontsize=10.5,color=MUTED)

def axes(fig,rect,xlabel='',ylabel='',title=''):
 ax=fig.add_axes(rect);ax.set(xlabel=xlabel,ylabel=ylabel,title=title)
 ax.tick_params(length=0,pad=7,labelsize=11);ax.grid(axis='y',zorder=0)
 return ax

def svg_metadata(path,title,description):
 ns='http://www.w3.org/2000/svg';ET.register_namespace('',ns)
 tree=ET.parse(path);root=tree.getroot();root.set('role','img')
 root.set('width','1400px' if title.startswith('animation') else '1600px');root.set('height','900px')
 for node in list(root):
  if node.tag in ('{'+ns+'}title','{'+ns+'}desc'):root.remove(node)
 for name,value in [('title',title.replace('_',' ')),('desc',description)]:
  node=ET.Element('{'+ns+'}'+name);node.text=value;root.insert(0,node)
 tree.write(path,encoding='utf-8',xml_declaration=True)

def savefig(fig,name,sources=(),**details):
 files=[]
 for ext in ('png','svg'):
  target=ASSETS/f'{name}.{ext}'
  def writer(path):
   fig.savefig(path,dpi=100)
   if ext=='svg':svg_metadata(path,name,details.get('description',name))
  _atomic_export(target,writer);files.append(target)
 plt.close(fig);register(name,files,sources,**details)
 return files

def save_animation(fig,update,times,name,sources=(),fps=None,**details):
 times=np.asarray(times);fps=float(fps or 1/np.diff(times)[0])
 ani=FuncAnimation(fig,update,frames=range(len(times)),interval=1000/fps,blit=False,repeat=False)
 files=[]
 for ext,writer in [('mp4',FFMpegWriter(fps=fps,codec='libx264',bitrate=2200,extra_args=['-pix_fmt','yuv420p'])),('gif',PillowWriter(fps=fps))]:
  target=ASSETS/f'{name}.{ext}'
  _atomic_export(target,lambda p:ani.save(p,writer=writer,dpi=100),len(times));files.append(target)
 update(len(times)-1)
 for ext in ('png','svg'):
  target=ASSETS/f'{name}_poster.{ext}'
  def writer(p):
   fig.savefig(p,dpi=100)
   if ext=='svg':svg_metadata(p,name,details.get('description',name))
  _atomic_export(target,writer);files.append(target)
 frames=[]
 for i in [0,len(times)//2,len(times)-1]:
  update(i);buffer=io.BytesIO();fig.savefig(buffer,format='png',dpi=70);buffer.seek(0)
  with Image.open(buffer) as im:frames.append(im.convert('RGB').copy())
 sheet=Image.new('RGB',(frames[0].width*3,frames[0].height),PAPER)
 for j,im in enumerate(frames):sheet.paste(im,(j*im.width,0))
 target=ASSETS/f'{name}_keyframes.png';_atomic_export(target,lambda p:sheet.save(p));files.append(target)
 plt.close(fig)
 register(name,files,sources,frames=len(times),frames_per_second=fps,frame_coordinates=times.tolist(),**details)
 print('Rendered',name,flush=True)


def geometry():
 fig=header('The curtain separates two connected air spaces','Model geometry and pressure sign used in the numerical calculations','SCHEMATIC')
 a=axes(fig,[.075,.235,.43,.50],xlabel='Across the enclosure x (m)',ylabel='Height z (m)',title='Cross-section perpendicular to the curtain')
 a.set(xlim=(-.04,1.84),ylim=(-.03,2.48));a.set_aspect('equal');a.grid(False)
 a.add_patch(Rectangle((0,0),1.8,2.4,fill=False,ec=INK,lw=1.5))
 a.plot([.9,.9],[.3,2.1],color=BLUE,lw=5)
 a.scatter([.45],[2.1],s=60,color=INK,zorder=4)
 a.text(.05,2.22,'Showerhead',fontsize=12)
 a.annotate('',(.45,.6),(.45,1.98),arrowprops=dict(arrowstyle='->',color=BLUE,lw=2))
 a.text(.13,1.35,'Spray\nside',fontsize=13)
 a.text(1.16,1.35,'Outer\nair',fontsize=13)
 a.text(.96,2.23,'0.30 m gap',fontsize=11,color=MUTED)
 a.text(.96,.12,'0.30 m gap',fontsize=11,color=MUTED)
 a.annotate('',(.75,.3),(.75,2.1),arrowprops=dict(arrowstyle='<->',color=MUTED))
 a.text(.68,1.15,'H = 1.80 m',rotation=90,va='center',ha='right',fontsize=11)
 b=axes(fig,[.57,.30,.35,.41],title='Forces on a small curtain patch')
 b.set(xlim=(0,1),ylim=(0,1));b.axis('off')
 b.plot([.5,.5],[.06,.91],color=BLUE,lw=6)
 b.annotate('',(.54,.64),(.95,.64),arrowprops=dict(arrowstyle='->',color=INK,lw=3))
 b.annotate('',(.46,.40),(.13,.40),arrowprops=dict(arrowstyle='->',color=MUTED,lw=2))
 b.text(.96,.73,r'$p_{\mathrm{out}}$',ha='right',fontsize=20)
 b.text(.13,.27,r'$p_{\mathrm{in}}$',fontsize=20)
 b.text(.50,.98,'Curtain',ha='center',fontsize=13,color=BLUE)
 fig.text(.57,.22,r'$\Delta p=p_{\mathrm{out}}-p_{\mathrm{in}}>0$  means inward force',fontsize=17)
 footer(fig,'The modeled room is 1.80 × 2.40 × 2.40 m; curtain width is 2.40 m, with sealed side edges.',
        'The numerical enclosure has no bather. Water direction here is schematic; the modeled spray tilts along the room width.')
 savefig(fig,'figure_01_geometry',[ROOT/'data/grid_fine_both_config.json'],description='Schematic model cross-section and inward pressure sign. No bather or predicted curtain deformation.')


def prescribed_strip():
 s=np.linspace(0,1.8,500);hems=np.linspace(0,.20,101)
 fig=header('A small pressure can move a long, light sheet','Uniform prescribed pressure: 0.20 Pa · sheet mass: 0.20 kg/m²','ANALYTIC STRIP MODEL')
 a=axes(fig,[.085,.23,.37,.51],xlabel='Inward displacement Y (cm)',ylabel='Distance below support s (m)',title='Equilibrium profile')
 for hem,label,col in [(0,'No added hem',BLUE),(.1,'Hem 0.10 kg/m',RED)]:
  Y=exact_profile(s,hem=hem);a.plot(Y*100,s,color=col,lw=2.6,label=label)
  a.annotate(f'{Y[-1]*100:.2f} cm',(Y[-1]*100,1.8),xytext=(0,12),textcoords='offset points',ha='center',color=col,fontsize=13)
 a.invert_yaxis();a.set_xlim(-.5,22);a.set_ylim(1.96,0);a.legend(frameon=False,loc='upper right',fontsize=12)
 b=axes(fig,[.58,.23,.35,.51],xlabel='Added hem mass (kg per m of width)',ylabel='Hem displacement Y(H) (cm)',title='Greater hem mass raises the tension')
 values=np.array([exact_profile([1.8],hem=h)[0]*100 for h in hems]);b.plot(hems,values,color=BLUE,lw=2.6);b.set(xlim=(0,.2),ylim=(0,20))
 for h in [0,.1]:b.scatter(h,exact_profile([1.8],hem=h)[0]*100,s=60,color=BLUE if h==0 else RED,zorder=4)
 footer(fig,'Computed from the article’s small-slope hanging-strip equation. These are selected inputs, not measured shower loads.',
        'Profile chart uses centimetres horizontally and metres vertically; it is a displacement plot, not a true-aspect curtain drawing.')
 savefig(fig,'figure_02_prescribed_strip',description='Exact constant-pressure hanging-strip equilibrium, unweighted 18.35 cm and weighted 10.57 cm.')


def pressure_to_strip():
 flows=[load_case('grid_fine_'+k) for k in KINDS]
 fig=header('Calculated pressure feeds the same strip equation','Three controls · mean load over airflow time 10–12 s · fine grid 48 × 64 × 64')
 a=axes(fig,[.085,.24,.37,.49],xlabel='Outside minus inside pressure (Pa)',ylabel='Height z (m)',title='Pressure averaged across curtain width')
 b=axes(fig,[.58,.24,.35,.49],xlabel='Added hem mass (kg per m of width)',ylabel='Mean static hem displacement (cm)',title='Response under that calculated load')
 hems=np.linspace(0,.15,76)
 for d,label,col in zip(flows,LABELS,COLORS):
  q=mean_over_window(d['trace'][:,0],d['pressure_load']).mean(axis=0);z=d['load_z'];s0=2.1-z[::-1]
  a.plot(q,z,label=label,color=col,lw=2.4)
  vals=[equilibrium(lambda s:np.interp(s,s0,q[::-1]),n=256,H=1.8,sigma=.2,hem=h)[1][-1]*100 for h in hems]
  b.plot(hems,vals,label=label,color=col,lw=2.4)
  value=equilibrium(lambda s:np.interp(s,s0,q[::-1]),n=256,H=1.8,sigma=.2,hem=.05)[1][-1]*100
  b.scatter(.05,value,color=col,s=44,zorder=5)
 a.axvline(0,color=MUTED,lw=.8);a.set_ylim(.3,2.1);a.legend(frameon=False,fontsize=12,loc='lower right')
 b.axvline(.05,color=MUTED,ls=':',lw=1);b.set(xlim=(0,.15),ylim=(0,4.9))
 fig.text(.58,.143,'Dotted line: baseline hem 0.05 kg/m',fontsize=11,color=MUTED)
 footer(fig,'The pressure is calculated from droplet/air motion; no desired pressure or displacement is imposed.',
        'Sheet mass 0.20 kg/m². The strip response uses a fixed airflow boundary; it does not update the air as the curtain moves.')
 savefig(fig,'figure_03_pressure_to_strip',[d['source_path'] for d in flows],description='Fine-grid averaged pressure profiles and strip equilibrium versus hem mass.')


def mass_response():
 path=ROOT/'data/material_summary.json';data=json.loads(path.read_text())
 fig=header('A lighter curtain travels farther under the same load','Width-averaged static hem displacement · fine-grid pressure averaged over 10–12 s')
 ax=axes(fig,[.33,.235,.59,.51],xlabel='Mean static hem displacement (cm)')
 ypos=np.arange(4)[::-1]
 for j,(k,label,col) in enumerate(zip(KINDS,LABELS,COLORS)):
  values=[r['mean_hem_m']*100 for r in data[k]];y=ypos+(1-j)*.22
  ax.barh(y,values,height=.17,color=col,label=label,zorder=3)
  for yy,v in zip(y,values):ax.text(v+.10,yy,f'{v:.2f}',va='center',fontsize=12,color=col)
 choices=[('Light; no added hem',.1,0),('No added hem',.2,0),('Baseline hem',.2,.05),('Heavier hem',.2,.1)]
 ax.set_yticks(ypos,[f'{l}\nσ = {s:.2f} kg/m²; hem {h:.2f} kg/m' for l,s,h in choices]);ax.set_xlim(0,10);ax.grid(False);ax.legend(frameon=False,ncol=3,loc='upper left',bbox_to_anchor=(0,1.13),fontsize=12)
 footer(fig,'Only sheet mass and hem mass change; all four mechanical cases receive the same calculated pressure for each control.',
        'These are free equilibria of the small-slope model. Compare local reach with clearance before drawing a contact conclusion.')
 savefig(fig,'figure_04_mass_response',[path,*[ROOT/f'data/grid_fine_{k}.npz' for k in KINDS]],description='Fine-grid fixed-pressure response for four selected sheet and hem masses.')


def parameter_study():
 path=ROOT/'data/results_summary.json';data=json.loads(path.read_text())
 rows=[('control_spray','Baseline'),('flow_low','Flow 5 L/min'),('flow_high','Flow 10 L/min'),('diameter_small','Droplets 0.5 mm'),('diameter_large','Droplets 1.5 mm'),('speed_low','Launch speed 0.5 m/s'),('speed_high','Launch speed 3 m/s'),('tilt_vertical','Vertical spray axis'),('tilt_high','Spray tilted 35°'),('mixing_low','Half added air mixing'),('mixing_high','Twice added air mixing')]
 fig=header('Inward loading persists across the sampled inputs','Spray-only controls · one input varied at a time · screening grid 24 × 32 × 32')
 a=axes(fig,[.30,.235,.28,.50],xlabel='Mean pressure (Pa)');b=axes(fig,[.67,.235,.26,.50],xlabel='Mean static hem displacement (cm)')
 y=np.arange(len(rows))[::-1]
 for ax,key,scale,col in [(a,'mean_pressure_Pa',1,BLUE),(b,'static_mean_hem_m',100,C['navy'])]:
  values=[data[k][key]*scale for k,_ in rows];ax.scatter(values,y,s=45,color=col,zorder=3);ax.axvline(0,color=MUTED,lw=.8)
  for yy,v in zip(y,values):ax.text(v+.02*max(values),yy,f'{v:.3f}' if scale==1 else f'{v:.2f}',va='center',fontsize=11,color=col)
  ax.set_xlim(0,max(values)*1.29);ax.set_ylim(-.6,len(rows)-.4);ax.set_yticks(y)
 a.set_yticklabels([l for _,l in rows]);b.set_yticklabels([])
 footer(fig,'All values use the computed 10–12 s load and the same strip equation: sheet 0.20 kg/m²; hem 0.05 kg/m.',
        'This is a plausible-input study, without experimental fitting. Individual parameter cases have not each been mesh-refined.')
 savefig(fig,'figure_05_parameter_study',[path,*[ROOT/f'data/{n}.npz' for n,_ in rows]],description='One-at-a-time coarse-grid spray parameter study, mean pressure and static hem displacement.')


def droplet_values(t):
 g=9.81;rho=1.2;rhow=1000.;d=.001;cd=.47;k=3*rho*cd/(4*rhow*d);vt=np.sqrt(g/k);b=0.
 v=vt*np.tanh(g*np.asarray(t)/vt+b)
 distance=np.log(np.cosh(g*np.asarray(t)/vt+b)/np.cosh(b))/k
 return v,distance,k

def droplet():
 times=np.linspace(0,.5,61);_,_,k=droplet_values(times)
 sol=solve_ivp(lambda t,y:[y[1],9.81-k*y[1]**2],(0,.5),[0,0],t_eval=times,method='DOP853',rtol=1e-12,atol=1e-14)
 if not sol.success:raise RuntimeError(sol.message)
 dist,vel=sol.y;mass=1000*np.pi*.001**3/6;force=mass*k*vel**2
 fig=header('A falling droplet transfers momentum to air','Single-droplet benchmark · still air · constant drag coefficient','ANALYTIC DEMONSTRATION',True)
 a=axes(fig,[.09,.25,.24,.47],xlabel='Horizontal position',ylabel='Distance fallen (m)',title='Calculated droplet position');a.set(xlim=(-.5,.5),ylim=(1.8,-.12));a.set_xticks([]);a.grid(False)
 point,=a.plot([],[],'o',ms=13,color=BLUE);trail,=a.plot([],[],color=BLUE,lw=1.5,alpha=.5)
 b=axes(fig,[.47,.48,.45,.24],xlabel='',ylabel='Speed (m/s)',title='The air receives the reaction to drag');b.set(xlim=(0,.5),ylim=(0,5));b.plot(times,vel,color=BLUE,alpha=.2)
 c=axes(fig,[.47,.22,.45,.19],xlabel='Physical time (s)',ylabel='Force to air (μN)');c.set(xlim=(0,.5),ylim=(0,max(force)*1e6*1.1));c.plot(times,force*1e6,color=RED,alpha=.2)
 line,=b.plot([],[],color=BLUE,lw=2.5);fl,=c.plot([],[],color=RED,lw=2.5);clock=fig.text(.09,.759,'',fontsize=13)
 footer(fig,'Solution of dv/dt = g − k v², k = 3ρₐCᴅ/(4ρwd); force to air is m k v² downward.',
        'Released from rest; d = 1 mm; Cᴅ = 0.47; droplet enlarged for visibility. The enclosure model evolves the air and uses variable drag.')
 def update(i):
  point.set_data([0],[dist[i]]);trail.set_data([0,0],[0,dist[i]]);line.set_data(times[:i+1],vel[:i+1]);fl.set_data(times[:i+1],force[:i+1]*1e6);clock.set_text(f't = {times[i]:.3f} s');return point,trail,line,fl,clock
 save_animation(fig,update,times,'animation_01_droplet',fps=12,description='Numerically integrated constant-drag falling droplet, independently checked against analytic solution. Playback slowed by factor ten.',physical_time_s=times.tolist(),playback='10 seconds of video per second of physical time')


def vortex():
 times=np.linspace(0,6,61);rho=1.2;omega=1.2;R=.5;r=np.linspace(0,R,101);v=omega*r;p=.5*rho*omega**2*r**2
 fig=header('Turning air requires an inward pressure force','Solid-body core viewed along its axis · rotation lies in a plane parallel to the curtain','ANALYTIC DEMONSTRATION',True)
 a=axes(fig,[.075,.24,.40,.50],xlabel='Distance from axis (m)',ylabel='Distance from axis (m)');a.set(xlim=(-.6,.6),ylim=(-.6,.6));a.set_aspect('equal');a.grid(False)
 for rr in [.2,.35,.5]:a.add_patch(Circle((0,0),rr,fill=False,ec=C['line'],lw=1))
 a.scatter([0],[0],color=INK,s=20);a.text(.02,.035,'Low-pressure centre',fontsize=11)
 points=a.scatter([],[],color=BLUE,s=45);radii=np.tile([.2,.35,.5],4);angles=np.repeat(np.arange(4)*np.pi/2,3)
 b=axes(fig,[.60,.51,.32,.21],ylabel='Tangential speed (m/s)');b.plot(r,v,color=BLUE,lw=2.5);b.set_xlim(0,R)
 c=axes(fig,[.60,.22,.32,.21],xlabel='Radius r (m)',ylabel='Pressure above centre (Pa)');c.plot(r,p,color=RED,lw=2.5);c.set_xlim(0,R)
 clock=fig.text(.075,.77,'',fontsize=13)
 footer(fig,'vθ = Ωr and p(r) − p(0) = ½ρₐΩ²r²; Ω = 1.2 rad/s, radius 0.50 m, ρₐ = 1.2 kg/m³.',
        'Markers follow the exact steady circular velocity field. This ideal core is not a computed shower vortex.')
 def update(i):
  th=angles+omega*times[i];points.set_offsets(np.c_[radii*np.cos(th),radii*np.sin(th)]);clock.set_text(f't = {times[i]:.1f} s · speed and pressure profiles stay steady');return points,clock
 save_animation(fig,update,times,'animation_02_vortex',description='Material markers rotate in an analytic solid-body core; steady speed and pressure profiles.',playback='physical seconds')


def thermal():
 values=np.linspace(0,5,61);z=np.linspace(0,2.4,201);zn=1.0;factor=1.2*9.81/295
 fig=header('A warm air column changes pressure with height','Two hydrostatic columns, equal pressure at a specified neutral level','ANALYTIC PARAMETER SWEEP',True)
 a=axes(fig,[.10,.24,.33,.48],ylabel='Height z (m)',title='');a.set(xlim=(0,1),ylim=(0,2.4));a.set_xticks([]);a.grid(False)
 a.add_patch(Rectangle((.05,0),.32,2.4,fc=C['blue_fill'],ec=C['line']));warm=Rectangle((.63,0),.32,2.4,fc=C['red_fill'],ec=C['line']);a.add_patch(warm)
 a.axhline(zn,color=MUTED,ls='--');a.text(.21,2.5,'Outside',ha='center',fontsize=13);a.text(.79,2.5,'Inside',ha='center',fontsize=13)
 b=axes(fig,[.59,.24,.32,.48],xlabel='Outside minus inside pressure (Pa)',ylabel='Height z (m)',title='Pressure difference');b.set(xlim=(-.31,.25),ylim=(0,2.4));b.axvline(0,color=MUTED,lw=1);b.axhline(zn,color=MUTED,ls='--');line,=b.plot([],[],color=RED,lw=2.5)
 b.text(.23,.25,'Inward',ha='right',color=RED,fontsize=12);b.text(-.29,2.12,'Outward',ha='left',color=BLUE,fontsize=12)
 label=fig.text(.10,.765,'',fontsize=14)
 footer(fig,'Δp(z) = ρ₀g(ΔT/T₀)(zₙ − z); T₀ = 295 K, ρ₀ = 1.2 kg/m³, specified zₙ = 1.00 m.',
        'The animation varies ΔT from 0 to 5 K. It is a sequence of hydrostatic states, not a simulated heating history.')
 def update(i):
  q=factor*values[i]*(zn-z);line.set_data(q,z);warm.set_alpha(.25+.75*values[i]/5);label.set_text(f'Air-temperature difference ΔT = {values[i]:.2f} K');return line,warm,label
 save_animation(fig,update,values,'animation_03_thermal',fps=10,description='Hydrostatic thermal pressure difference versus height for selected temperature differences.',frame_coordinate='air-temperature difference K; not physical time')


def airflow():
 data=[load_case('grid_fine_'+k) for k in KINDS];times=data[0]['trace'][:,0];lim=max(float(np.abs(d['pressure_yz']).max()) for d in data)
 norm=SymLogNorm(linthresh=.02,linscale=1,vmin=-lim,vmax=lim,base=10)
 fig=header('Water and heating generate different air circulations','Saved projected velocity and reduced pressure · fine grid · fixed curtain','COMPUTED AIRFLOW',True)
 axs=[];ims=[];notes=[]
 for j,(d,label) in enumerate(zip(data,LABELS)):
  ax=axes(fig,[.06+j*.285,.28,.245,.45],xlabel='Width y (m)',ylabel='Height z (m)' if j==0 else '',title=label);ax.grid(False);ax.set_aspect('equal');ax.set_xticks([0,1.2,2.4]);ax.set_yticks([0,1.2,2.4]);ax.set(xlim=(0,2.4),ylim=(0,2.4))
  im=ax.imshow(d['pressure_yz'][0].T,origin='lower',extent=(0,2.4,0,2.4),cmap=PRESSURE_CMAP,norm=norm,interpolation='nearest');axs.append(ax);ims.append(im)
  notes.append(fig.text(.06+j*.285,.23,'',fontsize=10,color=MUTED))
 cax=fig.add_axes([.92,.32,.012,.36]);cb=fig.colorbar(ims[0],cax=cax);cb.set_label('Reduced pressure (Pa)',fontsize=11)
 ticks=[t for t in [-10,-1,-.1,-.02,0,.02,.1,1,10] if -lim<=t<=lim];cb.set_ticks(ticks);cb.set_ticklabels([f'{t:g}' for t in ticks]);cb.ax.tick_params(labelsize=9)
 clock=fig.text(.06,.76,'',fontsize=13)
 footer(fig,'Slice x = 0.46875 m, parallel to the curtain at x = 0.90 m. Curves follow the instantaneous projected (y, z) velocity.',
        'Curves are not particle paths. Shared symmetric-log pressure scale, linear within ±0.02 Pa; pressure reference is the room mean.')
 def update(i):
  for ax,d,im,note in zip(axs,data,ims,notes):
   im.set_data(d['pressure_yz'][i].T)
   for artist in [*ax.collections,*ax.patches]:artist.remove()
   vy,vz=d['velocity_yz'][i,1],d['velocity_yz'][i,2];speed=float(np.hypot(vy,vz).max())
   if speed>0:ax.streamplot(d['y'],d['z'],vy.T,vz.T,color=INK,density=.70,linewidth=.65,arrowsize=.7,minlength=.15,maxlength=4)
   note.set_text(f'Largest in-plane speed: {speed:.3f} m/s')
  clock.set_text(f'Airflow time t = {times[i]:.1f} s');return (*ims,*notes,clock)
 save_animation(fig,update,times,'animation_04_airflow',[d['source_path'] for d in data],description='Fine-grid saved pressure and instantaneous projected streamlines at x=0.46875 m.',actual_slice_x_m=.46875,pressure_limits_Pa=[-lim,lim],pressure_linear_threshold_Pa=.02,playback='physical seconds; no interpolated flow frames')


def release():
 structures=[load_structure('release_grid_fine_'+k) for k in KINDS]
 selected=[d['strips'][int(d['meta']['selected_probe_index'])] for d in structures]
 indices=np.arange(0,len(selected[0]['t']),5);times=selected[0]['t'][indices]
 histories=[np.max(s['y'],axis=1)*100 for s in selected]
 fig=header('The curtain overshoots its static position after release','Separate mechanics experiment under the unchanged 10–12 s mean pressure','COMPUTED STRIP RESPONSE',True)
 a=axes(fig,[.09,.22,.19,.53],xlabel='Y (m)',ylabel='Height z (m)',title='Strip profiles');a.set(xlim=(-.08,.17),ylim=(.3,2.1));a.set_aspect('equal');a.set_xticks([0,.1],['0','0.1']);a.axvline(0,color=MUTED,lw=.8)
 b=axes(fig,[.43,.25,.50,.47],xlabel='Time since release τ (s)',ylabel='Largest inward displacement along strip (cm)');b.set(xlim=(0,6),ylim=(0,8.6))
 shapes=[];lines=[];dots=[]
 for strip,h,label,col in zip(selected,histories,LABELS,COLORS):
  shape,=a.plot([],[],color=col,lw=2.4);shapes.append(shape)
  a.plot(strip['static_y'],2.1-strip['static_s'],color=col,ls='--',lw=1,alpha=.7)
  b.plot(strip['t'],h,color=col,alpha=.13,lw=1.5)
  static=float(np.max(strip['static_y']))*100;b.axhline(static,color=col,ls='--',lw=1,alpha=.65)
  line,=b.plot([],[],color=col,lw=2.5,label=f'{label} · y = {strip["width_y_m"]:.4f} m');lines.append(line)
  dot,=b.plot([],[],'o',color=col,ms=5);dots.append(dot)
 b.legend(frameon=False,loc='upper right',fontsize=11);clock=fig.text(.43,.76,'',fontsize=13)
 fig.text(.43,.172,'Dashed lines: static reference under the identical load',fontsize=11,color=MUTED)
 footer(fig,'Each control uses its largest-excursion probe among nine fixed widths. Shape axes use equal metre scales.',
        'τ starts at release from rest; it is not the airflow clock. Sheet 0.20 kg/m², hem 0.05 kg/m, damping 0.08 kg/(m² s).')
 def update(j):
  i=indices[j]
  for s,h,shape,line,dot in zip(selected,histories,shapes,lines,dots):
   shape.set_data(s['y'][i],2.1-s['s']);line.set_data(s['t'][:i+1],h[:i+1]);dot.set_data([s['t'][i]],[h[i]])
  clock.set_text(f'Time since release τ = {times[j]:.1f} s');return (*shapes,*lines,*dots,clock)
 save_animation(fig,update,times,'animation_05_mean_load_release',[d['source_path'] for d in structures]+[ROOT/f'data/grid_fine_{k}.npz' for k in KINDS],description='Saved strip release response under constant computed 10–12 s mean pressure; no geometry feedback.',selected_widths_y_m=[s['width_y_m'] for s in selected],playback='physical seconds since release, independent of airflow clock',airflow_window_s=[10,12],equal_shape_axis_scales=True)


def analytic_checks():
 t=np.linspace(0,.5,101);v,x,k=droplet_values(t)
 sol=solve_ivp(lambda t,y:[y[1],9.81-k*y[1]**2],(0,.5),[0,0],t_eval=t,method='DOP853',rtol=1e-12,atol=1e-14)
 error=max(float(np.max(abs(sol.y[0]-x))),float(np.max(abs(sol.y[1]-v))))
 checks={'droplet_analytic_vs_DOP853_max_error':error}
 assert error<1e-9
 for hem in [0,.1]:
  s,Y=equilibrium(.2,n=4096,H=1.8,sigma=.2,hem=hem)
  e=float(np.max(np.abs(Y-exact_profile(s,hem=hem))))
  checks[f'strip_hem_{hem}_max_error_m']=e;assert e<1e-6
 checks['unweighted_exact_hem_m']=float(exact_profile([1.8],hem=0)[0])
 checks['weighted_exact_hem_m']=float(exact_profile([1.8],hem=.1)[0])
 r=np.linspace(.001,.5,501);pressure=.5*1.2*1.2**2*r**2
 e=float(np.max(abs(np.gradient(pressure,r,edge_order=2)-1.2*(1.2*r)**2/r)));checks['vortex_radial_balance_residual_Pa_m']=e;assert e<1e-10
 z=np.linspace(0,2.4,501);q=1.2*9.81*5/295*(1.0-z)
 e=float(np.max(abs(np.gradient(q,z,edge_order=2)+1.2*9.81*5/295)));checks['thermal_gradient_residual_Pa_m']=e;assert e<1e-10
 checks['thermal_pressure_at_neutral_Pa']=1.2*9.81*5/295*(1.0-1.0)
 assert checks['thermal_pressure_at_neutral_Pa']==0
 _atomic_export(ASSETS/'analytic_checks.json',lambda p:p.write_text(json.dumps(checks,indent=2)+'\n'))
 return checks


def verify():
 checks=analytic_checks();path=ASSETS/'publication_manifest.json';manifest=json.loads(path.read_text())
 count=0
 for name,record in manifest.items():
  for entry in record['files']+record['sources']:
   p=ROOT/entry['file'];assert digest(p)==entry['sha256'],f'Hash mismatch {p}'
  for entry in record['files']:
   p=ROOT/entry['file'];_verify_export(p,record.get('frames') if p.suffix in ('.gif','.mp4') else None);count+=1
 provenance={'sources':[source(Path(__file__)),source(STYLE),source(ROOT/'curtainflow/render.py'),source(ROOT/'curtainflow/mechanics.py'),source(ROOT/'curtainflow/averaging.py')],
             'verified_media_files':count,'analytic_checks':checks,'manifest_sha256':digest(path)}
 _atomic_export(ASSETS/'generation_source.json',lambda p:p.write_text(json.dumps(provenance,indent=2)+'\n'))
 print(f'Verified {count} outputs, source hashes, and analytic checks',flush=True)


def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--only',choices=['all','static','early','airflow','release','verify'],default='all');args=p.parse_args();ASSETS.mkdir(exist_ok=True)
 if args.only in ('all','static'):
  for f in [geometry,prescribed_strip,pressure_to_strip,mass_response,parameter_study]:f();print('Rendered',f.__name__,flush=True)
 if args.only in ('all','early'):
  for f in [droplet,vortex,thermal]:f()
 if args.only in ('all','airflow'):airflow()
 if args.only in ('all','release'):release()
 verify()
if __name__=='__main__':main()
