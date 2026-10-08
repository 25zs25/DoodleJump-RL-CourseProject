"""Publish only completed, frozen native-v2 experiments, excluding old/smoke runs."""
from pathlib import Path
import csv,json,hashlib
import numpy as np
P=Path(__file__).resolve().parent
E=P/'experiments/native_retrain_20261008'
R=P/'results/native_v2'
NAMES={'dqn':'DQN','double_dqn':'Double DQN','ppo':'PPO'}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
def group(rs):
    assert len(rs)==3
    scores=[r['summary']['mean_score'] for r in rs]
    return {'mean':float(np.mean(scores)),'sd':float(np.std(scores,ddof=1)),
        'height':float(np.mean([r['summary']['mean_height'] for r in rs])),
        'score_ge_3000':float(np.mean([e['score']>=3000 for r in rs for e in r['episodes']])),
        'truncated':float(np.mean([e['truncated'] for r in rs for e in r['episodes']])),
        'n_training_seeds':3,'n_maps_per_seed':100,
        'reason':f"截断 {100*np.mean([e['truncated'] for r in rs for e in r['episodes']]):.1f}%"}
def main():
    protocol=read(E/'protocol.json');runs=protocol['runs'];conditions=[c['name'] for c in protocol['test_conditions']]
    records=[read(f) for f in (R/'evaluation').glob('*.json')]
    # Release metadata is also populated for files produced by already-running workers.
    for r in records:
        r.update({'checkpoint':f"models/{r['run_id']}/best.pt",'policy_frozen':True,
            'selection':'probability sampling' if r['stochastic'] else 'argmax',
            'env_sha256':hashlib.sha256((P/'env.py').read_bytes()).hexdigest()})
        suffix='_sample' if r['stochastic'] else ''
        write(R/'evaluation'/f"{r['run_id']}_{r['condition']}{suffix}.json",r)
    current=[r for r in records if not r['legacy']];legacy=[r for r in records if r['legacy']]
    assert len(current)==39 and len(legacy)==9,(len(current),len(legacy))
    rows=[];ablation=[]
    for a in NAMES:
        for c in conditions:
            rs=[r for r in current if r['algorithm']==a and r['condition']==c and r['observation']=='full' and not r['stochastic']]
            rows.append({'algorithm':a,'label':NAMES[a],'mode':c,**group(rs)})
    for c in conditions:
        rs=[r for r in current if r['condition']==c and r['observation']=='no_velocity']
        ablation.append({'algorithm':'ppo','label':'PPO速度置零','mode':c,**group(rs)})
    sampled=group([r for r in current if r['stochastic']])
    rawbase=read(R/'baselines.json');bases=[]
    baseline_episodes=[{'policy':r['policy'],'condition':r['condition'],**e} for r in rawbase for e in r['episodes']]
    with (R/'baseline_episodes.csv').open('w',newline='',encoding='utf-8-sig') as f:
        wr=csv.DictWriter(f,fieldnames=list(baseline_episodes[0]));wr.writeheader();wr.writerows(baseline_episodes)
    for r in rawbase:
        bases.append({'label':'随机动作' if r['policy']=='random' else '物理规则参考','mode':r['condition'],
            'mean':r['summary']['mean_score'],'sd':None,'height':r['summary']['mean_height'],
            'score_ge_3000':float(np.mean([e['score']>=3000 for e in r['episodes']])),
            'reason':f"截断 {100*r['summary']['time_limit_rate']:.1f}%"})
    models=[];statuses=[];curves=[]
    for r in runs:
        folder=P/'models'/r['id'];s=read(folder/'status.json')
        assert s['training_complete'] and s['steps']==1000000 and s['hidden']==128
        assert s['viewport']==[683,871] and s['parameters']==(43908 if r['algorithm']=='ppo' else 43779)
        m=read(folder/'best.json');m['budget']=s['steps'];m['validation_score']=s['best_validation_score']
        models.append(m);statuses.append(s)
    models.sort(key=lambda m:(m['observation']!='full',-m['validation_score']))
    for a in NAMES:
        cs=[read(P/'models'/r['id']/'curve.json') for r in runs if r['algorithm']==a and r['observation']=='full']
        points=[];sd=[];actual=[]
        for target in range(50000,1000001,50000):
            ps=[min(c,key=lambda p:abs(p['steps']-target)) for c in cs]
            vals=[p['validation']['mean_score'] for p in ps]
            points.append(float(np.mean(vals)));sd.append(float(np.std(vals,ddof=1)));actual.append([p['steps'] for p in ps])
        curves.append({'algorithm':a,'label':NAMES[a],'steps':list(range(50000,1000001,50000)),
            'scores':points,'sd':sd,'actual_checkpoint_steps':actual})
    oldrows=[];oldselected=[]
    for a in NAMES:
        rs=[r for r in legacy if r['algorithm']==a]
        oldrows.append({'algorithm':a,'label':NAMES[a],'mode':'native',**group(rs)})
        rid=protocol['legacy_display_ids'][a];r=next(r for r in rs if r['run_id']==rid)
        oldselected.append({'algorithm':a,'id':rid,'score':r['summary']['mean_score'],'height':r['summary']['mean_height']})
    summary={'protocol':protocol['id'],'budget':1000000,'training_seeds':[42,59,143],
        'viewport':[683,871],'conditions':protocol['test_conditions'],'main':rows,'ablation':ablation,
        'ppo_sample':sampled,'baselines':bases,'curves':curves,'default_model':models[0]['id'],
        'display_models':{a:max((m for m in models if m['algorithm']==a and m['observation']=='full'),key=lambda m:m['validation_score'])['id'] for a in NAMES},
        'statuses':statuses,'legacy_same_window':oldrows,'legacy_previous_display':oldselected,
        'caption':'当前683×871原版窗口重新训练；每次100万决策，3算法×3训练种子，另有3次PPO速度消融。各场景每模型100张保留地图，±为3个训练种子均分之间的SD。原版得分与上升高度分开报告。'}
    write(R/'summary.json',summary)
    all_ep=[]
    for r in records:
        for e in r['episodes']:all_ep.append({'run':r['run_id'],'algorithm':r['algorithm'],'training_seed':r['training_seed'],
            'condition':r['condition'],'stochastic':r['stochastic'],'legacy':r['legacy'],**e})
    with (R/'test_episodes.csv').open('w',newline='',encoding='utf-8-sig') as f:
        wr=csv.DictWriter(f,fieldnames=list(all_ep[0]));wr.writeheader();wr.writerows(all_ep)
    write(P/'results/summary.json',summary)
    (P/'models.js').write_text('window.ORIGINAL_MODELS='+json.dumps(models,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    labels={'native':'当前窗口683×871','desktop':'桌面画布596.25×1060','mobile':'手机画布390×844'}
    browser={**summary,'rows':[{**r,'mode':labels[r['mode']]} for r in rows+ablation+bases]}
    (P/'results.js').write_text('window.ORIGINAL_RESULTS='+json.dumps(browser,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    write(E/'release_model_manifest.json',{m['id']:{n:hashlib.sha256((P/'models'/m['id']/n).read_bytes()).hexdigest() for n in ['best.pt','best.json','final.pt','final.json','config.json','curve.json','status.json']} for m in models})
    print(json.dumps({'main':[r for r in rows if r['mode']=='native'],'legacy':oldrows,'default_model':models[0]['id']},ensure_ascii=False))
if __name__=='__main__':main()
