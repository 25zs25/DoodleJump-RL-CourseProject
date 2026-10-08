(() => {
  const $=s=>document.querySelector(s),a=$('#original'),b=$('#adapted');let count=0,timer=null,result=null,ready=false;
  function physical(){return{window:{width:innerWidth,height:innerHeight,mobile:isMobile},canvas:{width,height},constants:{stepSize,jump:Doodler.jumpForce,gravity:config.GRAVITY,threshold:config.THRESHOLD,playerWidth:Doodler.w,playerHeight:Doodler.h,platformWidth:Platform.w,platformHeight:Platform.h,speed:Doodler.speed},player:{x:doodler.x,y:doodler.y,vx:doodler.vx,vy:doodler.vy,direction:doodler.direction},platforms:platforms.map(p=>({x:p.x,y:p.y,type:p.type,vx:p.vx,springed:p.springed,springX:p.springX,springY:p.springY})),hole:blackhole?{x:blackhole.x,y:blackhole.y}:null,score,isOver,isBlackholed};}
  const snapshot=f=>f.contentWindow.eval('('+physical.toString()+')()');
  function stop(){if(timer)clearInterval(timer);timer=null;$('#play').textContent='同步回放';}
  function check(){const original=snapshot(a),adapted=snapshot(b);const equal=JSON.stringify(original)===JSON.stringify(adapted);result={equal,frames:count,original,adapted};$('#result').textContent=equal?`已核对 ${count} 帧：全部物理状态一致；得分 ${original.score}`:`第 ${count} 帧出现差异，已停止`;$('#result').style.color=equal?'#39752d':'#b33';if(!equal||original.isOver)stop();return result;}
  function reset(){if(!ready)return;stop();const seed=Number($('#seed').value)>>>0;a.contentWindow.OriginalReference.reset(seed);b.contentWindow.DoodleNative.reset(seed);count=0;return check();}
  function step(action=1){if(!ready)return;if(result?.original.isOver)return result;a.contentWindow.OriginalReference.frame(action);b.contentWindow.DoodleNative.frame(action);count++;return check();}
  function fit(){const h=innerHeight,w=innerWidth,available=Math.max(120,innerHeight-$('#toolbar').offsetHeight-44),canvasW=w<=768?w:h*9/16;for(const f of [a,b]){const stage=f.parentElement,scale=Math.min(stage.clientWidth/canvasW,available/h);f.width=w;f.height=h;f.style.width=w+'px';f.style.height=h+'px';f.style.left=(stage.clientWidth-w*scale)/2+'px';f.style.transform=`scale(${scale})`;stage.style.height=available+'px';}$('#geometry').textContent=`内部窗口 ${w}×${h}；原版画布约 ${canvasW.toFixed(1)}×${h}。`;}
  $('#reset').onclick=reset;$('#left').onclick=()=>step(0);$('#stop').onclick=()=>step(1);$('#right').onclick=()=>step(2);
  $('#play').onclick=()=>{if(timer){stop();return;}if(!ready)return;$('#play').textContent='暂停回放';timer=setInterval(()=>step(Math.floor(count/31)%3),1000/70);};
  const initial=setInterval(()=>{try{if(a.contentWindow.OriginalReference?.ready()&&b.contentWindow.DoodleNative?.ready()){clearInterval(initial);ready=true;reset();}}catch(e){}},50);
  // Size the browsing contexts before p5 setup, using the actual top-level viewport.
  fit();addEventListener('resize',()=>location.reload());
  globalThis.NativeCompare={ready:()=>ready,result:()=>result,step,reset,stop};
})();
