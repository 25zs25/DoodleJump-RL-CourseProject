/* Rendering, sounds, physical updates and maps remain in upstream/js. */
(() => {
  const api=DoodleNative;let phase='paused',controller='manual',model=null,manual=1,action=1,within=0,before=0,sample=false,policyState=123;
  const randomPolicy=()=>{policyState=(Math.imul(1664525,policyState)+1013904223)>>>0;return policyState/4294967296;};
  function infer(o){let v=o;for(const l of model.layers){v=l.weights.map((row,i)=>{let n=l.bias[i];for(let k=0;k<row.length;k++)n+=row[k]*v[k];return l.activation==='relu'?Math.max(0,n):n;});}return v;}
  function choose(){
    if(controller==='manual')return manual;
    if(controller==='random')return Math.floor(randomPolicy()*3);
    const values=infer(api.obs());globalThis.lastNetworkOutput=values;
    if(sample&&model.algorithm==='ppo'){const mx=Math.max(...values),p=values.map(x=>Math.exp(x-mx)),sum=p.reduce((a,b)=>a+b,0);let r=randomPolicy()*sum;for(let a=0;a<3;a++){r-=p[a];if(r<=0)return a;}return 2;}
    return values.indexOf(Math.max(...values));
  }
  function staticRender(){drawBackground();if(blackhole)blackhole.render();platforms.forEach(p=>p.render());drawScore();if(doodler)doodler.render();}
  function send(){parent.postMessage({type:'doodle-state',phase,controller,action,network:globalThis.lastNetworkOutput||null,info:api.info(),snapshot:api.snapshot(),ready:api.ready()},location.origin);}
  draw=function(){
    if(!api.ready())return;
    if(phase==='running'&&!isOver&&!api.metrics().truncated){
      if(within===0){before=score;action=choose();}
      api.frame(action);within++;
      if(within===4||isOver){const m=api.metrics();m.steps++;m.truncated=m.steps>=1500&&!isOver;m.episodeReturn+=(score-before)/100-.001-(isOver?1:0);within=0;send();}
      if(isOver||api.metrics().truncated){phase='ended';send();if(api.metrics().truncated)noLoop();}
    }else if(isOver&&phase==='ended'){api.nativeDraw();}else staticRender();
  };
  const nativeSetup=setup;setup=function(){nativeSetup();staticRender();send();};
  const held=new Set();const keyAction=()=>{manual=held.has('left')?0:held.has('right')?2:1;};
  addEventListener('keydown',e=>{const k=e.key.toLowerCase();if(['arrowleft','arrowright','a','d',' '].includes(k))e.preventDefault();if(k==='arrowleft'||k==='a')held.add('left');if(k==='arrowright'||k==='d')held.add('right');keyAction();if(k===' '&&!e.repeat){phase=phase==='running'?'paused':'running';phase==='paused'?noLoop():loop();send();}});
  addEventListener('keyup',e=>{const k=e.key.toLowerCase();if(k==='arrowleft'||k==='a')held.delete('left');if(k==='arrowright'||k==='d')held.delete('right');keyAction();});
  addEventListener('blur',()=>{held.clear();keyAction();});
  const touchBegin=touchStarted,touchEnd=touchEnded,mouseBegin=mousePressed;
  touchStarted=function(){manual=mouseX<width/2?0:2;return touchBegin();};
  touchEnded=function(){manual=1;const over=isOver,r=touchEnd();if(over&&!isOver){phase='running';within=0;loop();send();}return r;};
  mousePressed=function(){const over=isOver;mouseBegin();if(over&&!isOver){phase='running';within=0;loop();send();}};
  addEventListener('message',e=>{
    if(e.origin!==location.origin||e.source!==parent)return;
    const d=e.data;if(d.type!=='doodle-command'||!api.ready())return;
    if(d.command==='reset'){noLoop();phase='paused';within=0;policyState=((d.seed>>>0)^0x91b1)>>>0;api.reset(d.seed,model?.observation||'full');staticRender();send();}
    if(d.command==='controller'){controller=d.controller;model=d.model||null;sample=!!d.sample;manual=1;}
    if(d.command==='action')manual=d.action;
    if(d.command==='start'){phase='running';loop();}
    if(d.command==='pause'){phase='paused';noLoop();send();}
  });
  globalThis.DoodleBridge={infer: o=>infer(o),api,state:()=>({phase,controller,within,action}),select:m=>{model=m;controller='model';}};
})();
