"""Faithful numerical port of frozen upstream draw(), at a declared viewport.

Upstream scripts are preserved unchanged in upstream/js. Regression tests
execute those exact scripts as the oracle, including Array.forEach mutation.
Only seeding, reset/step, observation, reward, telemetry and time limits added.
"""
from __future__ import annotations
import math
import numpy as np

PLATFORM_SLOTS, OBS_DIM = 20, 209
class LCG:
    def __init__(self,seed):self.state=int(seed)&0xffffffff
    def random(self):
        self.state=(1664525*self.state+1013904223)&0xffffffff
        return self.state/4294967296.

class DoodleEnv:
    observation_dim=OBS_DIM
    action_dim=3
    def __init__(self,mode='original',observation='full',seed=42,max_steps=1500,action_repeat=4,height=None):
        sizes={'original':720,'mixed':720,'viewport600':600,'viewport900':900}
        if mode not in sizes:raise ValueError(mode)
        if observation not in ('full','no_velocity'):raise ValueError(observation)
        self.mode,self.observation,self.seed=mode,observation,int(seed)
        self.height=float(height or sizes[mode]);self.width=self.height*9/16
        self.max_steps,self.action_repeat=int(max_steps),int(action_repeat)
        self.reset(seed)
    def reset(self,seed=None):
        if seed is not None:self.seed=int(seed)
        self.rng=LCG(self.seed)
        self.pw=110*self.width/725;self.ph=28*self.height/1289
        self.sw=14*self.width/725;self.sh=14*self.height/1289
        self.dw=80*self.width/725;self.dh=80*self.height/1289
        self.jump=8.15*self.height/1289;self.superjump=14*self.height/1289
        self.speed=7.2*self.width/725;self.gravity=.16*self.height/1289
        self.maxfall=10*self.height/1289;self.spacing=math.floor(self.height/9)
        self.platforms=[];self.hole=None;self.score=0;self.scroll=0.
        self.maxheight=0.;self.frames=0;self.steps=0;self.landings=0;self.springs=0
        self.fragile_used=0;self.episode_return=0.;self.terminated=False;self.truncated=False
        self.death_reason=None;self.last_event=None;self.direction=1
        y=self.height
        while y>0:
            x=self.pw/2+(self.width-self.pw)*self.rng.random()
            kind=self._kind()
            while kind==3:kind=self._kind()
            spring=self.rng.random()<.1
            self.platforms.append(self._platform(x,y,kind,spring))
            y-=self.spacing
        p=self.platforms[-2]
        self.x=p['x'];self.y=p['y']-self.dh/2-self.ph/2
        self.spawn_y=self.y;self.vx=0.;self.vy=0.
        return self.obs()
    def _kind(self):
        r=self.rng.random()*10
        return 5 if r<5 else 2 if r<7 else 3
    def _platform(self,x,y,kind,spring):
        sx=(self.rng.random()-.5)*self.pw*.8 if spring else None
        return {'x':x,'y':y,'type':kind,'vx':2.,'springed':bool(spring),
                'springX':sx,'springY':-self.ph/2-self.sh/2 if spring else None}
    def _collision(self,x,y,w,h):
        # Upstream checkCollision uses Platform.w/h even for the spring object.
        # Preserve that behavior rather than silently fixing the original rule.
        return (self.x-self.dw/4<x+self.pw/2 and self.x+self.dw/4>x-self.pw/2 and
                self.y+self.dh/2>y-self.ph/2 and self.y+self.dh/2<y)
    def _scroll_platforms(self):
        # JS forEach takes initial length, but reads the mutated array by index.
        length=len(self.platforms)
        for i in range(length):
            if i>=len(self.platforms):continue
            p=self.platforms[i];p['y']-=self.vy;self.score+=1
            if p['y']>self.height:
                if p['type'] not in (3,0):
                    x=self.pw/2+(self.width-self.pw)*self.rng.random()
                    y=p['y']-10*self.spacing
                    kind=self._kind();spring=self.rng.random()<.1
                    self.platforms.pop(i);self.platforms.append(self._platform(x,y,kind,spring))
                    if kind==3:
                        x=(x+self.width/3)%self.width;spring=self.rng.random()<.1
                        self.platforms.append(self._platform(x,y,5,spring))
                    elif self.hole is None and self.rng.random()<1:
                        self.hole={'x':(x+self.width/2)%self.width,'y':y}
                else:self.platforms.pop(i)
    def _frame(self,action):
        self.frames+=1
        # Same effect as upstream keyPressed / keyReleased: direct speed, no inertia.
        self.vx=(-self.speed if action==0 else self.speed if action==2 else 0.)
        if action!=1:self.direction=0 if action==0 else 1
        for p in self.platforms:
            if p['springed'] and self.vy>0 and self._collision(p['x']+p['springX'],p['y']+p['springY'],self.sw,self.sh):
                self.vy=-self.superjump;self.springs+=1;self.last_event='spring'
            if p['type']!=0 and self.vy>0 and self._collision(p['x'],p['y'],self.pw,self.ph):
                self.vy=-self.jump;self.landings+=1;self.last_event='jump'
                if p['type']==3:
                    p['type']=0;p['springed']=False;self.fragile_used+=1;self.last_event='fragile'
            if p['type']==2:
                p['x']+=p['vx']
                if p['x']>self.width-self.pw/2 or p['x']<self.pw/2:p['vx']*=-1
        self.x+=self.vx
        if self.x>self.width:self.x=0.
        elif self.x<0:self.x=self.width
        self.vy+=self.gravity if self.vy<0 else self.gravity*1.33
        if self.vy>self.maxfall:self.vy=self.maxfall
        self.y+=self.vy
        if self.y<=300:self.y=300.
        # Track physical ascent without changing native score or game state.
        self.maxheight=max(self.maxheight,self.spawn_y-self.y+self.scroll)
        if self.y>=self.height:
            self.terminated=True;self.death_reason='fall';self.vx=0.;self.vy=0.
        elif self.hole and math.hypot(self.x-self.hole['x'],self.y-self.hole['y'])<30:
            self.terminated=True;self.death_reason='blackhole';self.vx=0.;self.vy=0.
            self.x,self.y=self.hole['x'],self.hole['y']
        if self.hole and self.hole['y']>self.height:self.hole=None
        if self.y<=300 and self.vy<0:
            delta=-self.vy;self.scroll+=delta
            if self.hole:self.hole['y']-=self.vy
            self._scroll_platforms()
            self.maxheight=max(self.maxheight,self.spawn_y-self.y+self.scroll)
    def step(self,action):
        if self.terminated or self.truncated:raise RuntimeError('Reset after episode end')
        if int(action) not in (0,1,2):raise ValueError(action)
        oldscore=self.score;self.last_event=None
        for _ in range(self.action_repeat):
            self._frame(int(action))
            if self.terminated:break
        self.steps+=1
        self.truncated=self.steps>=self.max_steps and not self.terminated
        reward=(self.score-oldscore)/100.-.001-(1. if self.terminated else 0.)
        self.episode_return+=reward
        return self.obs(),reward,self.terminated,self.truncated,self.info()
    def obs(self):
        no_v=self.observation=='no_velocity'
        out=[self.x/self.width*2-1,self.y/self.height,0 if no_v else self.vx/self.speed,
             0 if no_v else self.vy/self.superjump,(self.spawn_y-self.y+self.scroll-self.maxheight)/self.height]
        ps=[p for p in self.platforms if p['type']!=0 and -self.ph<=p['y']<=self.height+self.ph]
        ps.sort(key=lambda p:abs(p['y']-self.y))
        for p in ps[:PLATFORM_SLOTS]:
            dx=((p['x']-self.x+self.width/2)%self.width)-self.width/2
            if abs(abs(dx)-self.width/2)<1e-8:dx=-self.width/2
            out.extend([dx/self.width,(p['y']-self.y)/self.height,self.pw/self.width,
                        0 if no_v or p['type']!=2 else p['vx']/2.,float(p['type']==5),float(p['type']==2),float(p['type']==3),
                        float(p['springed']),(p['springX'] or 0.)/self.width,1.])
        out.extend([0.]*(10*(PLATFORM_SLOTS-min(len(ps),PLATFORM_SLOTS))))
        if self.hole and -40<=self.hole['y']<=self.height+40:
            h=self.hole;dx=((h['x']-self.x+self.width/2)%self.width)-self.width/2
            if abs(abs(dx)-self.width/2)<1e-8:dx=-self.width/2
            out.extend([dx/self.width,(h['y']-self.y)/self.height,30/self.width,1.])
        else:out.extend([0.]*4)
        assert len(out)==OBS_DIM
        return np.array(out,dtype=np.float32)
    def info(self):
        return dict(score=self.score,height=self.maxheight,landings=self.landings,springs=self.springs,
                    fragile_used=self.fragile_used,death_reason=self.death_reason,last_event=self.last_event,
                    steps=self.steps,frames=self.frames,episode_return=self.episode_return,seed=self.seed,mode=self.mode)
    def snapshot(self):
        return {'width':self.width,'height':self.height,'x':self.x,'y':self.y,'vx':self.vx,'vy':self.vy,
                'direction':self.direction,'score':self.score,'rng':self.rng.state,'scroll':self.scroll,
                'heightScore':self.maxheight,'platforms':[dict(p) for p in self.platforms],
                'hole':dict(self.hole) if self.hole else None,'terminated':self.terminated,'frames':self.frames}
