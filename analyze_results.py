"""Retired 405x720 publisher; use analyze_native.py for current results."""
from pathlib import Path
import json,numpy as np
P=Path(__file__).resolve().parent
NAMES={'dqn':'DQN','double_dqn':'Double DQN','ppo':'PPO'}
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def group(records):
    scores=[d['summary']['mean_score'] for d in records]
    return {'mean':float(np.mean(scores)),'sd':float(np.std(scores,ddof=1)),
            'height':float(np.mean([d['summary']['mean_height'] for d in records])),
            'score_ge_3000':float(np.mean([e['score']>=3000 for d in records for e in d['episodes']])),
            'truncated':float(np.mean([e['truncated'] for d in records for e in d['episodes']])),
            'n_training_seeds':len(records),'n_maps_per_seed':100,
            'reason':f"截断 {100*np.mean([e['truncated'] for d in records for e in d['episodes']]):.1f}%"}
def main():
    raise SystemExit(
        "analyze_results.py is a retired 405x720 result publisher.\n"
        "Use python analyze_native.py for the current native-window results.\n"
        "Historical data is retained in experiments/legacy_720_delivery/ and\n"
        "results/evaluation/ for inspection only.\n"
        "No model, score, or browser deployment files have been changed."
    )
    files=list((P/'results/evaluation').glob('*.json'))
    assert len(files)==39, len(files)
    records=[read(p) for p in files]
    rows=[]
    for a in NAMES:
        for mode in ['original','viewport600','viewport900']:
            rs=[r for r in records if r['algorithm']==a and r['mode']==mode and r['observation']=='full' and not r['stochastic']]
            assert len(rs)==3
            rows.append({'algorithm':a,'label':NAMES[a],'mode':mode,**group(rs)})
    abl=[]
    for mode in ['original','viewport600','viewport900']:
        rs=[r for r in records if r['observation']=='no_velocity' and r['mode']==mode]
        assert len(rs)==3;abl.append({'algorithm':'ppo','label':'PPO速度置零','mode':mode,**group(rs)})
    sampled=group([r for r in records if r['stochastic']])
    baseline=read(P/'results/baselines.json')
    baseline_rows=[{'label':'随机动作' if r['policy']=='random' else '物理规则参考','mode':r['mode'],
                    'mean':r['summary']['mean_score'],'sd':None,'height':r['summary']['mean_height'],
                    'score_ge_3000':float(np.mean([e['score']>=3000 for e in r['episodes']])),
                    'reason':f"截断 {r['summary']['time_limit_rate']*100:.1f}%"} for r in baseline]
    models=[];curves=[];statuses=[]
    for folder in sorted((P/'models').iterdir()):
        if not (folder/'status.json').exists():continue
        s=read(folder/'status.json');assert s['training_complete'] and s['steps']==1000000
        m=read(folder/'best.json');m['budget']=s['steps'];m['validation_score']=s['best_validation_score'];models.append(m);statuses.append(s)
    assert len(models)==12
    models.sort(key=lambda m:(m['observation']!='full',-m['validation_score']))
    for a in NAMES:
        cs=[read(P/'models'/f'{a}_full_seed{s}_1000000'/'curve.json') for s in [42,59,143]]
        points=[]
        for target in range(50000,1000001,50000):
            vals=[min(c,key=lambda p:abs(p['steps']-target))['validation']['mean_score'] for c in cs]
            points.append(float(np.mean(vals)))
        curves.append({'algorithm':a,'label':NAMES[a],'steps':list(range(50000,1000001,50000)),'scores':points})
    summary={'protocol':'original-rules-v1','budget':1000000,'training_seeds':[42,59,143],
             'main':rows,'ablation':abl,'ppo_sample':sampled,'baselines':baseline_rows,
             'curves':curves,'default_model':models[0]['id'],'statuses':statuses,
             'caption':'原版规则从头训练：3算法×3种子×100万决策。每个场景每模型100张保留地图。表中的±是训练种子间SD，原版得分与上升高度分开记录。'}
    (P/'results/summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
    (P/'models.js').write_text('window.ORIGINAL_MODELS='+json.dumps(models,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    browser={**summary,'rows':rows+abl+baseline_rows}
    (P/'results.js').write_text('window.ORIGINAL_RESULTS='+json.dumps(browser,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
    print(json.dumps({'main':rows,'ablation':abl,'sampled':sampled,'default_model':models[0]['id']},ensure_ascii=False))
if __name__=='__main__':main()
