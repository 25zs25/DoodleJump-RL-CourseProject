"""Compare Python training states to actual browser-native frame captures."""
from pathlib import Path
import json,sys,math
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from env import DoodleEnv
from viewport import load_viewport
def compare(a,b,loc=''):
    if isinstance(a,dict):
        assert set(a)==set(b),(loc,set(a)^set(b))
        for k in a:compare(a[k],b[k],loc+'.'+k)
    elif isinstance(a,list):
        assert len(a)==len(b),(loc,len(a),len(b))
        for i,(x,y) in enumerate(zip(a,b)):compare(x,y,loc+f'[{i}]')
    elif a is None or isinstance(a,(bool,str)):assert a==b,(loc,a,b)
    else:assert abs(a-b)<2e-6,(loc,a,b)

fixtures=json.loads((ROOT/'tests/native_window_port_fixtures.json').read_text(encoding='utf-8'))
def physical(env):
    return {'player':dict(x=env.x,y=env.y,vx=env.vx,vy=env.vy,direction=env.direction),
            'platforms':env.platforms,'hole':env.hole,'score':env.score,
            'isOver':env.terminated,'isBlackholed':env.death_reason=='blackhole'}
total=0
for case in fixtures:
    initial=case['initial']
    env=DoodleEnv(seed=42,height=initial['canvas']['height'],width=initial['canvas']['width'],action_repeat=1,max_steps=5000)
    target=lambda record:{k:record[k] for k in physical(env)}
    compare(physical(env),target(initial),'initial')
    for i,(action,record) in enumerate(zip(case['actions'],case['records'])):
        env.step(action)
        compare(physical(env),target(record),f'{case["viewport"]}.{i}')
        total+=1
native=load_viewport(ROOT/'tests/native-viewport.desktop.json')
assert native['height']==1060 and native['width']==596.25
for key in ('gravity','jump'):
    modified=dict(native);modified[key]*=.8
    temp=ROOT/'tests/viewport_invalid_fixture.json'
    temp.write_text(json.dumps(modified),encoding='utf-8')
    try:
        try:load_viewport(temp)
        except ValueError:pass
        else:raise AssertionError('Repeated scaling was not rejected')
    finally:temp.unlink()
report={'actual_browser_viewports':len(fixtures),'frames':total,'all_passed':True,'stale_scaling_rejected':True}
(ROOT/'tests/native_window_port_parity.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps(report))
