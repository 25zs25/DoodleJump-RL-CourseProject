const {chromium}=require('playwright'),fs=require('fs'),path=require('path');
const base=process.env.DOODLE_URL||'http://127.0.0.1:8765',out=__dirname;
function capture(){return{window:{width:innerWidth,height:innerHeight,mobile:isMobile},canvas:{width,height},constants:{stepSize,jump:Doodler.jumpForce,gravity:config.GRAVITY,threshold:config.THRESHOLD,playerWidth:Doodler.w,playerHeight:Doodler.h,platformWidth:Platform.w,platformHeight:Platform.h,speed:Doodler.speed},player:{x:doodler.x,y:doodler.y,vx:doodler.vx,vy:doodler.vy,direction:doodler.direction},platforms:platforms.map(p=>({x:p.x,y:p.y,type:p.type,vx:p.vx,springed:p.springed,springX:p.springX,springY:p.springY})),hole:blackhole?{x:blackhole.x,y:blackhole.y}:null,score,isOver,isBlackholed};}
(async()=>{
 const browser=await chromium.launch({headless:true,channel:'msedge'}),errors=[],runs=[],portFixtures=[];
 try{
 for(const viewport of [{width:1360,height:1060},{width:1360,height:720},{width:1360,height:844},{width:390,height:844}]){
  const page=await browser.newPage({viewport}),native=await browser.newPage({viewport});
  for(const p of [page,native])p.on('pageerror',e=>errors.push(e.message));
  await page.goto(base);await page.waitForFunction(()=>OriginalApp.state()?.ready);
  if(!await page.locator('#controls').evaluate(e=>e.open))await page.locator('#controls summary').click();
  await native.goto(base+'/upstream/index.html');await native.waitForFunction(()=>!!window.doodler);
  await native.evaluate(()=>noLoop());
  const frame=page.frames().find(f=>f.url().includes('game.html'));
  const initial=await frame.evaluate(capture),options=await page.locator('#controller option').allTextContents();
  if(initial.window.width!==viewport.width||initial.window.height!==viewport.height)throw Error('Wrapper viewport differs from native viewport');
  for(const seed of [42,10003,20001]){
   await native.evaluate(seed=>{let s=seed>>>0;window.testRandom=()=>{s=(Math.imul(1664525,s)+1013904223)>>>0;return s/4294967296;};window.testDraw=()=>{const old=Math.random;Math.random=testRandom;try{draw();}finally{Math.random=old;}};const old=Math.random;Math.random=testRandom;try{resetGame();}finally{Math.random=old;}},seed);
   await frame.evaluate(seed=>DoodleNative.reset(seed),seed);
   const a=await native.evaluate(capture),b=await frame.evaluate(capture);
   const initialEqual=JSON.stringify(a)===JSON.stringify(b);
   const actions=Array.from({length:2000},(_,i)=>(Math.floor(i/31)+seed)%3);
   const ar=await native.evaluate(({actions,source})=>{const snap=(0,eval)('('+source+')');const records=[];for(const action of actions){if(isOver)break;doodler.vx=action===0?-Doodler.speed:action===2?Doodler.speed:0;if(action!==1)doodler.direction=action===0?0:1;testDraw();records.push(snap());}return records;},{actions,source:capture.toString()});
   const br=await frame.evaluate(({actions,source})=>{const snap=(0,eval)('('+source+')');const records=[];for(const action of actions){if(isOver)break;DoodleNative.frame(action);records.push(snap());}return records;},{actions,source:capture.toString()});
   const mismatch=ar.findIndex((x,i)=>JSON.stringify(x)!==JSON.stringify(br[i]));
   if(!initialEqual||mismatch!==-1||ar.length!==br.length)throw Error('Physics mismatch');
   if(seed===42)portFixtures.push({viewport,initial:a,actions:actions.slice(0,Math.min(ar.length,800)),records:ar.slice(0,800)});
   runs.push({viewport,seed,initialPlatforms:a.platforms.length,initialEqual,frames:ar.length,allFramesEqual:true,canvas:a.canvas});
  }
  await page.locator('#seed').fill('42');await page.locator('#reset').click();await page.waitForTimeout(150);
  const start=await frame.evaluate(()=>DoodleNative.snapshot());
  await page.locator('#start').click();await page.keyboard.down('ArrowRight');await page.waitForTimeout(120);await page.keyboard.up('ArrowRight');await page.locator('#start').click();
  const after=await frame.evaluate(()=>DoodleNative.snapshot());
  const moved=after.x!==start.x; if(!moved)throw Error('Manual parent keyboard failed');
  await page.locator('#reset').click();await page.waitForTimeout(100);
  await frame.evaluate(()=>{DoodleNative.metrics().steps=1500;});
  await page.locator('#start').click();await page.waitForTimeout(100);await page.locator('#start').click();
  if(await frame.evaluate(()=>DoodleNative.metrics().truncated))throw Error('Manual play was incorrectly time limited');
  await page.locator('#reset').click();await page.waitForTimeout(100);
  const pausedA=await frame.evaluate(()=>DoodleNative.snapshot());await page.waitForTimeout(100);const pausedB=await frame.evaluate(()=>DoodleNative.snapshot());
  if(JSON.stringify(pausedA)!==JSON.stringify(pausedB))throw Error('Pause drift');
  const shape=await page.evaluate(()=>({width:innerWidth,height:innerHeight,iframe:document.querySelector('#game').getBoundingClientRect().toJSON(),overflow:document.documentElement.scrollWidth>innerWidth}));
  if(shape.overflow)throw Error('Horizontal overflow');
  await page.locator('#controls').evaluate(e=>e.open=false);
  await page.screenshot({path:path.join(out,`native_window_${viewport.width}_${viewport.height}.png`)});
  if(viewport.width===1360&&viewport.height===1060){
   const geometry=await frame.evaluate(()=>({...DoodleNative.geometry(),upstream_commit:'d4b6071813a9c1353267d53dcfa9d8abc3e5b2f4',environment_version:'native-viewport-v2'}));
   fs.writeFileSync(path.join(out,'native-viewport.desktop.json'),JSON.stringify(geometry,null,2));
   await page.locator('#controls').evaluate(e=>e.open=true);
   await page.screenshot({path:path.join(out,'native_window_controls.png')});
   const modelId=await page.locator('#controller option').evaluateAll(es=>es.find(e=>e.textContent.includes('Double DQN')).value);await page.locator('#controller').selectOption(modelId);
   await page.locator('#start').click();await page.waitForTimeout(250);await page.locator('#start').click();
   if(!await frame.evaluate(()=>Array.isArray(lastNetworkOutput)&&lastNetworkOutput.length===3))throw Error('Trained inference failed');
  }
  await page.close();await native.close();
 }
 const compare=await browser.newPage({viewport:{width:1360,height:1060}});compare.on('pageerror',e=>errors.push(e.message));
 await compare.goto(base+'/compare.html');await compare.waitForFunction(()=>NativeCompare.ready());
 const comparison=await compare.evaluate(()=>{for(let i=0;i<1800&&!NativeCompare.result().original.isOver;i++)NativeCompare.step(Math.floor(i/31)%3);return NativeCompare.result();});
 if(!comparison.equal)throw Error('Independent side-by-side comparison failed');
 await compare.screenshot({path:path.join(out,'native_window_compare.png')});
 const report={runs,totalFrames:runs.reduce((n,r)=>n+r.frames,0),manualKeyboard:true,manualUnlimited:true,pauseStable:true,modelInference:true,independentReference:{frames:comparison.frames,equal:comparison.equal,viewport:comparison.original.window},errors};
 fs.writeFileSync(path.join(out,'native_window_qa.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report));await browser.close();
 fs.writeFileSync(path.join(out,'native_window_port_fixtures.json'),JSON.stringify(portFixtures));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
