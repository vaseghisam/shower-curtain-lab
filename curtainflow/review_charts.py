"""Static scientific comparison charts from the saved phase-one calculations."""
from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .mechanics import equilibrium
from .averaging import mean_over_window

ROOT=Path(__file__).resolve().parents[1]
PAPER='#f8f6ef';INK='#203746';TEAL='#187f82';RED='#bb5546';BLUE='#496b91'
plt.rcParams.update({'figure.facecolor':PAPER,'axes.facecolor':PAPER,'text.color':INK,'axes.labelcolor':INK,'xtick.color':INK,'ytick.color':INK,'font.size':11,'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':PAPER})

def save(fig,name):
    dest=ROOT/'figures';dest.mkdir(exist_ok=True)
    temp=dest/'.render-tmp';temp.mkdir(exist_ok=True)
    for ext in ('png','svg'):
        p=temp/(name+'.'+ext);fig.savefig(p,dpi=180);p.replace(dest/p.name)
    plt.close(fig)

def parameters():
    summary=json.loads((ROOT/'data/results_summary.json').read_text())
    rows=[('control_spray','Baseline'),('flow_low','Water flow 5 L/min'),('flow_high','Water flow 10 L/min'),('diameter_small','Droplet diameter 0.5 mm'),('diameter_large','Droplet diameter 1.5 mm'),('speed_low','Launch speed 0.5 m/s'),('speed_high','Launch speed 3 m/s'),('tilt_vertical','Vertical spray axis'),('tilt_high','Spray axis tilted 35°'),('mixing_low','Half the added air mixing'),('mixing_high','Twice the added air mixing')]
    rows=[r for r in rows if r[0] in summary];y=np.arange(len(rows))[::-1]
    fig,axes=plt.subplots(1,2,figsize=(12,7),sharey=True)
    fig.subplots_adjust(left=.30,right=.95,top=.80,bottom=.21,wspace=.15)
    fig.text(.05,.94,'Inward loading across the input study',fontsize=21)
    fig.text(.05,.885,'Spray only · one input changed at a time · same closed enclosure',fontsize=12)
    for ax,key,scale,color,title in zip(axes,['mean_pressure_Pa','static_mean_hem_m'],[1,100],[TEAL,BLUE],['Mean pressure difference (Pa)','Mean static hem displacement (cm)']):
        values=[summary[n][key]*scale for n,_ in rows]
        ax.axvline(0,color=INK,lw=.8)
        ax.scatter(values,y,s=48,color=color,zorder=3)
        ax.set_xlabel(title,labelpad=12);ax.grid(axis='x',alpha=.2)
        for yy,v in zip(y,values):ax.annotate(f'{v:.3f}' if scale==1 else f'{v:.2f}',(v,yy),xytext=(7,0),textcoords='offset points',va='center',fontsize=10)
        ax.set_xlim(min(0,min(values)*1.1),max(values)*1.3)
    axes[0].set_yticks(y,[label for _,label in rows]);axes[1].tick_params(axis='y',length=0)
    fig.text(.05,.08,'Pressure averaged over 10–12 s. Static response uses that full spatial load and the article’s strip equation.',fontsize=11)
    fig.text(.05,.04,'Screening grid 24 × 32 × 32 · curtain 0.20 kg/m² · hem 0.05 kg/m · conditional model results',fontsize=10,color='#536872')
    save(fig,'figure_04_parameter_study')

def mechanics():
    fig,axes=plt.subplots(1,2,figsize=(12,6.4));fig.subplots_adjust(left=.09,right=.95,bottom=.23,top=.77,wspace=.30)
    fig.text(.07,.93,'From calculated pressure to gravitational resistance',fontsize=20)
    fig.text(.07,.87,'Width-averaged load at 10–12 s · static equilibrium of the existing strip model',fontsize=12)
    hems=np.linspace(0,.15,80)
    for name,label,color in [('grid_fine_spray','Spray',BLUE),('grid_fine_heat','Heat',RED),('grid_fine_both','Spray + heat',TEAL)]:
        d=np.load(ROOT/'data'/(name+'.npz'));q=mean_over_window(d['trace'][:,0],d['pressure_load']).mean(axis=0);z=d['load_z'];s0=2.1-z[::-1]
        axes[0].plot(q,z,color=color,label=label,lw=2)
        values=[]
        for hem in hems:
            _,y=equilibrium(lambda s:np.interp(s,s0,q[::-1]),H=1.8,sigma=.2,hem=hem,n=256)
            values.append(y[-1]*100)
        axes[1].plot(hems,values,color=color,lw=2,label=label)
    axes[0].axvline(0,color=INK,lw=.7);axes[0].set(xlabel='Outside minus inside pressure (Pa)',ylabel='Height above floor (m)');axes[0].legend(frameon=False)
    axes[1].set(xlabel='Added hem mass per width (kg/m)',ylabel='Static hem displacement (cm)')
    for ax in axes:ax.grid(alpha=.2)
    fig.text(.07,.11,'Fine grid 48 × 64 × 64. Each curve uses a computed pressure profile around the fixed curtain;',fontsize=11)
    fig.text(.07,.065,'these curves are prescribed-load responses, not a simultaneous solution for the final airflow and curtain shape.',fontsize=11)
    save(fig,'figure_03_pressure_to_strip')

def resolution():
    summary=json.loads((ROOT/'data/results_summary.json').read_text())
    fig,axes=plt.subplots(1,3,figsize=(14,5.8));fig.subplots_adjust(left=.075,right=.96,bottom=.25,top=.76,wspace=.35)
    fig.text(.065,.94,'Resolution checks for the reported quantities',fontsize=21)
    fig.text(.065,.87,'Same physical enclosure and water inputs · independently checked source and pressure operators',fontsize=12)
    for kind,label,col in [('spray','Spray',BLUE),('heat','Heat',RED),('both','Spray + heat',TEAL)]:
        names=[f'control_{kind}',f'grid_medium_{kind}',f'grid_fine_{kind}'];available=[(n,c) for n,c in zip([24,36,48],names) if c in summary]
        for ax,key,scale in zip(axes,['mean_pressure_Pa','static_mean_hem_m','peak_sampled_strip_displacement_m'],[1,100,100]):
            ax.plot([n for n,c in available],[summary[c][key]*scale for n,c in available],'-o',label=label,color=col,lw=1.7)
    for ax,title in zip(axes,['Mean pressure difference (Pa)','Mean static hem displacement (cm)','Startup peak: spray cases unresolved (cm)']):
        ax.set_title(title,fontsize=11);ax.set_xlabel('Cells across the room’s x direction');ax.set_xticks([24,36,48]);ax.grid(alpha=.2)
    axes[0].legend(frameon=False)
    fig.text(.065,.12,'Grids: 24 × 32 × 32, 36 × 48 × 48, 48 × 64 × 64. Finest-grid timestep is 0.002 s;',fontsize=11)
    fig.text(.065,.075,'the other two use 0.004 s. Separate timestep and ray-count checks are reported in the QA document.',fontsize=11)
    save(fig,'figure_05_resolution')

def materials():
    from .analyze import static_response,atomic_npz
    fig,ax=plt.subplots(figsize=(11,6.7));fig.subplots_adjust(left=.24,right=.95,bottom=.25,top=.77)
    fig.text(.07,.93,'A lighter curtain moves farther under the same load',fontsize=20)
    fig.text(.07,.87,'Mean static hem displacement · computed 10–12 s pressure · fine grid',fontsize=12)
    choices=[('Light, unweighted',.1,0),('Unweighted',.2,0),('Baseline hem',.2,.05),('Heavier hem',.2,.1)]
    out={};position=np.arange(4)[::-1]
    for index,(kind,label,color) in enumerate([('spray','Spray',BLUE),('heat','Heat',RED),('both','Spray + heat',TEAL)]):
        rows=[]
        with np.load(ROOT/'data'/f'grid_fine_{kind}.npz') as data:
            for name,sigma,hem in choices:
                r=static_response(data,sigma,hem)
                rows.append({'label':name,'sigma_kg_m2':sigma,'hem_kg_m':hem,'mean_hem_m':r['mean_hem_m'],'max_m':r['max_m'],'max_slope':r['max_slope']})
        values=[row['mean_hem_m']*100 for row in rows];offset=(index-1)*.22
        ax.barh(position+offset,values,height=.19,color=color,label=label)
        for y,v in zip(position+offset,values):ax.text(v+.10,y,f'{v:.2f}',va='center',fontsize=10,color=color)
        out[kind]=rows
    ax.set_yticks(position,[f'{name}\nσ = {sigma:.2f} kg/m²; hem = {hem:.2f} kg/m' for name,sigma,hem in choices]);ax.tick_params(axis='y',length=0,labelsize=10)
    ax.set_xlabel('Width-averaged static hem displacement (cm)');ax.set_xlim(0,10.3);ax.grid(axis='x',alpha=.15);ax.legend(frameon=False,ncol=3,loc='upper right',bbox_to_anchor=(1,1.13))
    fig.text(.07,.12,'The mass changes the article’s gravitational tension. Pressure is calculated once and is not rescaled.',fontsize=11)
    fig.text(.07,.065,'Prescribed-load equilibria; a moved curtain would also change the airflow. Maximum slopes remain below 0.14.',fontsize=11)
    save(fig,'figure_06_material_response')
    (ROOT/'data/material_summary.json').write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__':
    mechanics();parameters();resolution();materials()
