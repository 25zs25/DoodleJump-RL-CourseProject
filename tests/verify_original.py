from pathlib import Path
import sys,json,subprocess,shutil,numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from env import DoodleEnv
from baselines import rule_action
NODE=shutil.which('node')
if NODE is None:raise RuntimeError('Install Node.js to run the original JavaScript oracle tests')
def compare(a,b,loc=''):
    if isinstance(a,dict):
        assert set(a)==set(b),(loc,set(a)^set(b))
        for k in a:compare(a[k],b[k],loc+'.'+k)
    elif isinstance(a,list):
        assert len(a)==len(b),(loc,len(a),len(b))
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,loc+f'[{i}]')
    elif a is None or isinstance(a,(bool,str)):assert a==b,(loc,a,b)
    else:assert abs(a-b)<2e-6,(loc,a,b)
cases=[]
for h in [600,720,900]:
    for seed in [1,42,143,10003,20000]:
        actions=np.random.default_rng(seed).integers(0,3,1500).tolist()
        ref=json.loads(subprocess.check_output([NODE,str(ROOT/'tests/oracle.cjs')],input=json.dumps({'height':h,'seed':seed,'actions':actions}).encode(),cwd=ROOT))
        env=DoodleEnv(height=h,seed=seed)
        compare(env.snapshot(),ref[0]['snapshot'],'initial')
        compare(env.obs().tolist(),ref[0]['obs'],'obs0')
        for i,r in enumerate(ref[1:]):
            o,reward,t,tr,info=env.step(actions[i])
            compare(env.snapshot(),r['snapshot'],f'height{h}.seed{seed}.step{i}')
            compare(o.tolist(),r['obs'],'obs')
            compare(reward,r['reward'],'reward')
            compare(t,r['terminated'],'terminated')
        cases.append({'height':h,'seed':seed,'policy':'random','decisions':len(ref)-1,'frames':env.frames,'score':env.score,'passed':True})
for h in [600,720,900]:
    for seed in [10000,10001,10003,10007,10019]:
        e=DoodleEnv(height=h,seed=seed);actions=[]
        while not(e.terminated or e.truncated):
            a=rule_action(e.obs(),h);actions.append(a);e.step(a)
        ref=json.loads(subprocess.check_output([NODE,str(ROOT/'tests/oracle.cjs')],input=json.dumps({'height':h,'seed':seed,'actions':actions}).encode(),cwd=ROOT))
        e=DoodleEnv(height=h,seed=seed)
        for i,r in enumerate(ref[1:]):
            o,rew,t,tr,info=e.step(actions[i]);compare(e.snapshot(),r['snapshot'],f'rule.{h}.{seed}.{i}');compare(o.tolist(),r['obs'],'obs')
        cases.append({'height':h,'seed':seed,'policy':'rule','decisions':len(ref)-1,'frames':e.frames,'score':e.score,'passed':True})
special=[]
base=DoodleEnv()
p=lambda x,y,k=5,s=False:dict(x=x,y=y,type=k,vx=2.,springed=s,springX=0. if s else None,springY=-base.ph/2-base.sh/2 if s else None)
specs={
 'spring':{'x':200.,'y':400-base.dh/2-base.ph/4,'vy':2.,'platforms':[p(200,400,s=True)],'hole':None},
 'fragile':{'x':200.,'y':400-base.dh/2-base.ph/4,'vy':2.,'platforms':[p(200,400,k=3)],'hole':None},
 'moving_boundary':{'x':0.,'y':500.,'platforms':[p(base.width-base.pw/2+1,600,k=2)],'hole':None},
 'hole_death':{'x':200.,'y':400.,'platforms':[],'hole':{'x':200.,'y':400.}},
 'fall':{'y':719.9,'vy':base.maxfall,'platforms':[],'hole':None},
 'wrap':{'x':base.width-1,'y':500.,'platforms':[],'hole':None},
 'scroll_and_splice':{'x':100.,'y':300.,'vy':-base.jump,'platforms':[p(100,719),p(200,719,k=3),p(250,718),p(300,500)],'hole':None},
}
for name,inject in specs.items():
    e=DoodleEnv(seed=42)
    for k,v in inject.items():setattr(e,k,v)
    ref=json.loads(subprocess.check_output([NODE,str(ROOT/'tests/oracle.cjs')],input=json.dumps({'seed':42,'inject':inject,'actions':[2]*12,'repeat':1}).encode(),cwd=ROOT))
    e.action_repeat=1
    for i,r in enumerate(ref[1:]):
        e.step(2);compare(e.snapshot(),r['snapshot'],f'special.{name}.{i}')
    special.append({'case':name,'passed':True,'frames':e.frames})
(ROOT/'tests/original_special.json').write_text(json.dumps(special,indent=2),encoding='utf-8')
(ROOT/'tests/original_parity.json').write_text(json.dumps(cases,indent=2),encoding='utf-8')
print(json.dumps({'trajectories':len(cases),'decisions':sum(c['decisions'] for c in cases),'frames':sum(c['frames'] for c in cases),'special_cases':len(special),'all_passed':True}))
