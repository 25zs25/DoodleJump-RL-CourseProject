/* Training adapter around the unmodified upstream scripts. No game-rule overrides. */
(() => {
  const realRandom=Math.random,nativeSetup=setup,nativeDraw=draw,nativeReset=resetGame,nativeUpdate=Doodler.prototype.update;
  let rngState=42,seed=42,observation='full',metrics,ready=false;
  const random=()=>{rngState=(Math.imul(1664525,rngState)+1013904223)>>>0;return rngState/4294967296;};
  const seeded=fn=>{Math.random=random;try{return fn();}finally{Math.random=realRandom;}};
  const fresh=()=>{metrics={steps:0,frames:0,scroll:0,maxHeight:0,spawnY:doodler.y,landings:0,springs:0,fragile:0,episodeReturn:0,reason:null,truncated:false};};
  Doodler.prototype.update=function(){nativeUpdate.call(this);if(metrics)metrics.maxHeight=Math.max(metrics.maxHeight,metrics.spawnY-this.y+metrics.scroll);};
  setup=function(){seeded(nativeSetup);fresh();ready=true;if(typeof noLoop==='function')noLoop();};
  resetGame=function(){rngState=seed>>>0;seeded(nativeReset);fresh();};
  function setAction(a){doodler.vx=a===0?-Doodler.speed:a===2?Doodler.speed:0;if(a!==1)doodler.direction=a===0?0:1;}
  function frame(a){
    if(isOver)return;
    setAction(a);const vy=doodler.vy,oldScore=score,oldFragile=platforms.filter(p=>p.type===3);
    seeded(nativeDraw);metrics.frames++;
    if(vy>0&&doodler.vy<0){
      if(Math.abs(doodler.vy-(-Doodler.superJumpForce+config.GRAVITY))<1e-8)metrics.springs++;
      else metrics.landings++;
    }
    metrics.fragile+=oldFragile.filter(p=>p.type===0).length;
    if(score>oldScore){metrics.scroll-=doodler.vy;metrics.maxHeight=Math.max(metrics.maxHeight,metrics.spawnY-doodler.y+metrics.scroll);}
    if(isOver)metrics.reason=isBlackholed?'blackhole':'fall';
  }
  function obs(){
    const nv=observation==='no_velocity',dx=x=>{const d=((x-doodler.x+width/2)%width+width)%width-width/2;return Math.abs(Math.abs(d)-width/2)<1e-8?-width/2:d;};
    const o=[doodler.x/width*2-1,doodler.y/height,nv?0:doodler.vx/Doodler.speed,nv?0:doodler.vy/Doodler.superJumpForce,(metrics.spawnY-doodler.y+metrics.scroll-metrics.maxHeight)/height];
    const ps=platforms.filter(p=>p.type!==0&&p.y>=-Platform.h&&p.y<=height+Platform.h).sort((a,b)=>Math.abs(a.y-doodler.y)-Math.abs(b.y-doodler.y));
    for(const p of ps.slice(0,20))o.push(dx(p.x)/width,(p.y-doodler.y)/height,Platform.w/width,nv||p.type!==2?0:p.vx/2,+(p.type===5),+(p.type===2),+(p.type===3),+p.springed,(p.springX||0)/width,1);
    for(let i=Math.min(ps.length,20);i<20;i++)o.push(...Array(10).fill(0));
    if(blackhole&&blackhole.y>=-40&&blackhole.y<=height+40)o.push(dx(blackhole.x)/width,(blackhole.y-doodler.y)/height,Blackhole.ROCHE_LIMIT/width,1);
    else o.push(0,0,0,0);
    return Array.from(new Float32Array(o));
  }
  function snapshot(){return{width,height,x:doodler.x,y:doodler.y,vx:doodler.vx,vy:doodler.vy,direction:doodler.direction,score,rng:rngState,scroll:metrics.scroll,heightScore:metrics.maxHeight,platforms:platforms.map(p=>({x:p.x,y:p.y,type:p.type,vx:p.vx,springed:p.springed,springX:p.springX,springY:p.springY})),hole:blackhole?{x:blackhole.x,y:blackhole.y}:null,terminated:isOver,frames:metrics.frames};}
  function info(){return{score,height:metrics.maxHeight,landings:metrics.landings,springs:metrics.springs,fragile_used:metrics.fragile,death_reason:metrics.reason,steps:metrics.steps,frames:metrics.frames,episode_return:metrics.episodeReturn,seed};}
  function step(a,repeat=4,maxSteps=1500){
    if(isOver||metrics.truncated)throw Error('Reset after episode end');
    const old=score;for(let i=0;i<repeat&&!isOver;i++)frame(a);
    metrics.steps++;metrics.truncated=metrics.steps>=maxSteps&&!isOver;
    const reward=(score-old)/100-.001-(isOver?1:0);metrics.episodeReturn+=reward;
    return{obs:obs(),reward,terminated:isOver,truncated:metrics.truncated,info:info(),snapshot:snapshot()};
  }
  globalThis.DoodleNative={boot(s=42,ob='full'){seed=s>>>0;rngState=seed;observation=ob;setup();return obs();},reset(s=seed,ob='full'){seed=s>>>0;observation=ob;resetGame();return obs();},step,frame,obs,snapshot,info,setAction,ready:()=>ready,nativeDraw,metrics:()=>metrics};
  // Browser draw is driven by ui-bridge.js; oracle uses step() without p5 scheduling.
})();
