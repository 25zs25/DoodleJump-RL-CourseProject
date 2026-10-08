"""Reproduce the frozen native-window experiments; never alters game rules.

python retrain_native.py --train --workers 3
python retrain_native.py --evaluate --workers 2
"""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys, time
from concurrent.futures import ProcessPoolExecutor
import numpy as np
P=Path(__file__).resolve().parent
E=P/'experiments/native_retrain_20261008'
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def write(p,data): p.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def freeze():
    from viewport import load_viewport
    geometry=load_viewport(E/'viewport.json')
    runs=[{'algorithm':a,'seed':s,'observation':'full'} for s in [42,59,143] for a in ['dqn','double_dqn','ppo']]
    runs += [{'algorithm':'ppo','seed':s,'observation':'no_velocity'} for s in [42,59,143]]
    for r in runs:r['id']=f"native_v2_{r['algorithm']}_{r['observation']}_h128_seed{r['seed']}_1000000"
    cases=[]
    for name,ww,hh,start in [('native',683,871,61000),('desktop',1360,1060,62000),('mobile',390,844,63000)]:
        width=hh*9/16 if ww>768 else ww
        g={'windowWidth':ww,'windowHeight':hh,'width':width,'height':hh,'stepSize':hh//9,
           'threshold':300,'jump':8.15*hh/1289,'gravity':.16*hh/1289,
           'upstream_commit':geometry['upstream_commit'],'environment_version':'native-viewport-v2'}
        file=E/f'viewport_{name}.json'
        write(file,g)
        cases.append({'name':name,'viewport':g,'seed_start':start,'episodes':100,'file':file.name})
    protocol={'id':'native-viewport-v2-128-20261008','frozen_before_test':True,
        'training_viewport':geometry,'hidden':128,'device':'cpu','training_workers':3,
        'torch_threads_per_worker':1,'steps_per_run':1000000,'action_repeat':4,'max_decisions':1500,
        'reward':'original score delta / 100 - 0.001 - 1 on death',
        'validation_seeds':list(range(10000,10020)),
        'selection':'best validation mean native game score; never test scores',
        'checkpoint_every':50000,'epsilon_decay_steps':600000,'runs':runs,'test_conditions':cases,
        'ppo_eval':'argmax primary; stochastic secondary on native maps',
        'legacy_comparison':'all 9 old full models evaluated on same 100 native test seeds; fixed pre-test UI selections',
        'legacy_display_ids':{'dqn':'dqn_full_seed143_1000000','double_dqn':'double_dqn_full_seed42_1000000','ppo':'ppo_full_seed42_1000000'},
        'hardware':'Intel i7-12700H / 16 GB / RTX 3060 Laptop 6 GB available; CPU chosen from 20k timing pilot',
        'source_sha256':{n:sha(P/n) for n in ['agents.py','env.py','train.py','evaluate.py','viewport.py','baselines.py','bridge-core.js','ui-bridge.js']},
        'legacy_checkpoint_sha256':{f'{a}_full_seed{s}_1000000':sha(P/'models'/f'{a}_full_seed{s}_1000000'/'best.pt') for a in ['dqn','double_dqn','ppo'] for s in [42,59,143]},
        'created_at_utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
    if (E/'protocol.json').exists():return read(E/'protocol.json')
    write(E/'protocol.json',protocol)
    return protocol
def train(protocol,workers):
    queue=[]
    for r in protocol['runs']:
        folder=P/'models'/r['id']
        if folder.exists():
            status=read(folder/'status.json') if (folder/'status.json').exists() else {}
            if status.get('training_complete') and status['steps']==1000000:continue
            raise RuntimeError(f'Incomplete run {r["id"]}; inspect before replacing')
        queue.append(r)
    active=[];done=[];start=time.perf_counter()
    while queue or active:
        while queue and len(active)<workers:
            r=queue.pop(0);log=(E/f'{r["id"]}.log').open('w',encoding='utf-8')
            cmd=[sys.executable,'-u',str(P/'train.py'),'--algorithm',r['algorithm'],'--seed',str(r['seed']),
                 '--obs',r['observation'],'--hidden','128','--device','cpu','--steps','1000000',
                 '--epsilon-decay-steps','600000','--checkpoint-every','50000',
                 '--viewport-json',str(E/'viewport.json'),'--run-id',r['id']]
            proc=subprocess.Popen(cmd,cwd=P,stdout=log,stderr=subprocess.STDOUT)
            active.append((r,proc,log))
            print(json.dumps({'event':'started','run':r['id'],'pid':proc.pid}),flush=True)
        for r,proc,log in active[:]:
            if proc.poll() is None:continue
            log.close();active.remove((r,proc,log))
            if proc.returncode:raise RuntimeError(f'Training failed: {r["id"]}; see its log')
            done.append(r['id']);print(json.dumps({'event':'completed','run':r['id']}),flush=True)
        write(E/'orchestrator_status.json',{'completed_this_launch':done,'active':[{'id':r['id'],'pid':p.pid} for r,p,l in active],
            'queued':[r['id'] for r in queue],'elapsed_seconds':time.perf_counter()-start,'complete':not(queue or active)})
        if queue or active:time.sleep(2)
def evaluate_one(job):
    rid,case,stochastic,legacy=job
    from agents import load_model
    from evaluate import evaluate_policy
    import torch
    torch.set_num_threads(1)
    out=P/'results/native_v2/evaluation';out.mkdir(parents=True,exist_ok=True)
    file=out/f'{rid}_{case["name"]}{"_sample" if stochastic else ""}.json'
    if file.exists():return str(file)
    model,record=load_model(P/'models'/rid/'best.pt')
    vp=case['viewport'];s=case['seed_start']
    result=evaluate_policy(model,observation=record['observation'],seeds=range(s,s+case['episodes']),
        stochastic=stochastic,width=vp['width'],height=vp['height'])
    result.update({'condition':case['name'],'algorithm':record['algorithm'],'training_seed':record['seed'],
                   'run_id':rid,'legacy':legacy,'checkpoint_sha256':sha(P/'models'/rid/'best.pt'),
                   'checkpoint':f'models/{rid}/best.pt','policy_frozen':True,
                   'selection':'probability sampling' if stochastic else 'argmax',
                   'env_sha256':sha(P/'env.py'),
                   'environment_version':'native-viewport-v2'})
    write(file,result);return str(file)
def evaluate(protocol,workers,watch=False):
    jobs=[]
    for r in protocol['runs']:
        if not watch:
            st=read(P/'models'/r['id']/'status.json')
            assert st['training_complete'] and st['steps']==1000000
        for case in protocol['test_conditions']:jobs.append((r['id'],case,False,False))
        if r['algorithm']=='ppo' and r['observation']=='full':jobs.append((r['id'],protocol['test_conditions'][0],True,False))
    for rid in protocol['legacy_checkpoint_sha256']:jobs.append((rid,protocol['test_conditions'][0],False,True))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        active={}
        while jobs or active:
            for job in jobs[:]:
                if len(active)>=workers:break
                rid,case,sample,legacy=job;folder=P/'models'/rid
                try:status=read(folder/'status.json')
                except (FileNotFoundError,json.JSONDecodeError):continue
                if not status.get('training_complete'):continue
                assert status['steps']==1000000
                active[pool.submit(evaluate_one,job)]=job;jobs.remove(job)
            for future in list(active):
                if future.done():
                    path=future.result();del active[future]
                    print(json.dumps({'evaluated':Path(path).name}),flush=True)
            if jobs or active:time.sleep(2)
    from env import DoodleEnv
    from baselines import rule_action
    from evaluate import summarize
    baselines=[]
    for case in protocol['test_conditions']:
        for policy in ['random','rule']:
            episodes=[];vp=case['viewport'];env=DoodleEnv(width=vp['width'],height=vp['height'])
            for seed in range(case['seed_start'],case['seed_start']+case['episodes']):
                obs=env.reset(seed);rng=np.random.default_rng(seed^9181)
                while not(env.terminated or env.truncated):
                    action=int(rng.integers(3)) if policy=='random' else rule_action(obs,env.height,env.width)
                    obs,_,_,_,info=env.step(action)
                episodes.append({'seed':seed,**info,'terminated':env.terminated,'truncated':env.truncated})
            baselines.append({'policy':policy,'condition':case['name'],'viewport':[vp['width'],vp['height']],
                'episode_count':len(episodes),'episodes':episodes,'summary':summarize(episodes)})
    write(P/'results/native_v2/baselines.json',baselines)
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--train',action='store_true');ap.add_argument('--evaluate',action='store_true')
    ap.add_argument('--workers',type=int,default=3);ap.add_argument('--watch',action='store_true');args=ap.parse_args();protocol=freeze()
    for n,h in protocol['source_sha256'].items():assert sha(P/n)==h,f'Frozen source changed: {n}'
    if args.train:train(protocol,args.workers)
    if args.evaluate:evaluate(protocol,args.workers,args.watch)
if __name__=='__main__':main()
