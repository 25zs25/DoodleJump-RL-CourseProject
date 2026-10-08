"""Reproduce all frozen original-rule runs; completed runs are reused.

python run_experiments.py --train --evaluate --export
Use a fresh project copy for a completely new reproduction. Each training
run requires CPU PyTorch; no teacher or changed game-rule mode is used.
"""
from pathlib import Path
import argparse,sys,subprocess,json,time,hashlib,csv
import numpy as np
from env import DoodleEnv
from baselines import rule_action
from evaluate import summarize
P=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--train',action='store_true');ap.add_argument('--evaluate',action='store_true');ap.add_argument('--export',action='store_true')
    ap.add_argument('--workers',type=int,default=3);args=ap.parse_args()
    if not(args.train or args.evaluate or args.export):ap.error('Choose --train, --evaluate and/or --export')
    runs=[(a,s,'full') for a in ['dqn','double_dqn','ppo'] for s in [42,59,143]]+ [('ppo',s,'no_velocity') for s in [42,59,143]]
    if args.train:
        queue=[]
        for a,s,o in runs:
            rid=f'{a}_{o}_seed{s}_1000000';folder=P/'models'/rid
            if folder.exists():
                if (folder/'status.json').exists() and read(folder/'status.json')['training_complete']:
                    assert read(folder/'status.json')['steps']==1000000;continue
                raise RuntimeError(f'Incomplete run exists: {folder}. Use a fresh copy or inspect it before restarting.')
            queue.append([sys.executable,str(P/'train.py'),'--algorithm',a,'--seed',str(s),'--obs',o,'--steps','1000000','--epsilon-decay-steps','600000','--checkpoint-every','50000','--run-id',rid])
        active=[]
        while queue or active:
            while queue and len(active)<max(1,args.workers):active.append(subprocess.Popen(queue.pop(0),cwd=P))
            for proc in active[:]:
                if proc.poll() is not None:
                    active.remove(proc)
                    if proc.returncode:raise RuntimeError('Training process failed')
            if queue or active:time.sleep(2)
    if args.evaluate:
        records=[];out=P/'results/evaluation';out.mkdir(parents=True,exist_ok=True)
        for a,s,o in runs:
            rid=f'{a}_{o}_seed{s}_1000000';checkpoint=P/'models'/rid/'best.pt'
            assert read(P/'models'/rid/'status.json')['training_complete']
            settings=[(m,start,False) for m,start in [('original',20000),('viewport600',30000),('viewport900',40000)]]
            if a=='ppo' and o=='full':settings.append(('original',20000,True))
            for mode,start,sample in settings:
                file=out/f'{rid}_{mode}{"_sample" if sample else ""}.json'
                subprocess.run([sys.executable,str(P/'evaluate.py'),'--checkpoint',str(checkpoint),'--mode',mode,'--seed-start',str(start),'--episodes','100','--output',str(file)]+(['--stochastic'] if sample else []),cwd=P,check=True)
                d=read(file);d['checkpoint_sha256']=hashlib.sha256(checkpoint.read_bytes()).hexdigest();d['env_sha256']=hashlib.sha256((P/'env.py').read_bytes()).hexdigest()
                file.write_text(json.dumps(d,indent=2),encoding='utf-8')
                for ep in d['episodes']:records.append({'run':file.stem,'algorithm':a,'training_seed':s,'mode':mode,'selection':d['selection'],**ep})
        baseline=[]
        for mode,start in [('original',20000),('viewport600',30000),('viewport900',40000)]:
            for policy in ['random','rule']:
                episodes=[];env=DoodleEnv(mode=mode)
                for seed in range(start,start+100):
                    obs=env.reset(seed);rng=np.random.default_rng(seed^9181)
                    while not(env.terminated or env.truncated):obs,_,_,_,info=env.step(int(rng.integers(3)) if policy=='random' else rule_action(obs,env.height))
                    episodes.append({**info,'terminated':env.terminated,'truncated':env.truncated})
                baseline.append({'policy':policy,'mode':mode,'policy_frozen':True,'episode_count':100,'episodes':episodes,'summary':summarize(episodes)})
        (P/'results/baselines.json').write_text(json.dumps(baseline,indent=2),encoding='utf-8')
        with (P/'results/test_episodes.csv').open('w',newline='',encoding='utf-8-sig') as f:
            writer=csv.DictWriter(f,fieldnames=list(dict.fromkeys(k for r in records for k in r)));writer.writeheader();writer.writerows(records)
    if args.export:subprocess.run([sys.executable,str(P/'analyze_results.py')],cwd=P,check=True)
if __name__=='__main__':main()
