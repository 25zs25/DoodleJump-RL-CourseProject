const {chromium}=require('playwright'),fs=require('fs');
(async()=>{
 const fixture=JSON.parse(fs.readFileSync(__dirname+'/native_gap_replay.json','utf8'));
 const browser=await chromium.launch({headless:true,channel:'msedge'});
 try{
  const page=await browser.newPage({viewport:{width:1360,height:720}});await page.goto('http://127.0.0.1:8765/reference.html');await page.waitForFunction(()=>OriginalReference.ready());
  const result=await page.evaluate(f=>{
   OriginalReference.reset(f.seed);
   for(const a of f.decisions)for(let n=0;n<4&&!isOver;n++)OriginalReference.frame(a);
   const snapshot={x:doodler.x,y:doodler.y,vx:doodler.vx,vy:doodler.vy,direction:doodler.direction,score,platforms:platforms.map(p=>({x:p.x,y:p.y,type:p.type,vx:p.vx,springed:p.springed,springX:p.springX,springY:p.springY})),hole:blackhole?{x:blackhole.x,y:blackhole.y}:null,terminated:isOver};
   let maxError=0;function compare(a,b){if(a===null||typeof a==='boolean'){if(a!==b)throw Error('State mismatch');}else if(typeof a==='number'){maxError=Math.max(maxError,Math.abs(a-b));}else if(Array.isArray(a)){if(a.length!==b.length)throw Error('Platform count mismatch');a.forEach((x,i)=>compare(x,b[i]));}else for(const k in a)compare(a[k],b[k]);}
   compare(snapshot,f.expected);if(maxError>2e-6)throw Error('Physics mismatch');
   const ps=platforms.filter(p=>p.type!==0).sort((a,b)=>a.y-b.y),gaps=[];
   for(let i=0;i<ps.length-1;i++)if(ps[i+1].y-ps[i].y>120)gaps.push({upperY:ps[i].y,lowerY:ps[i+1].y,distance:ps[i+1].y-ps[i].y});
   let vy=-Doodler.jumpForce,ascent=0;while(vy<0){vy+=config.GRAVITY;if(vy<0)ascent-=vy;}
   return{actualOriginalBrowser:true,viewport:{width:innerWidth,height:innerHeight},canvas:{width,height},seed:f.seed,frames:f.decisions.length*4,score,maxError,gaps,normalJumpAscent:ascent,springs:ps.filter(p=>p.springed).length};
  },fixture);
  await page.screenshot({path:__dirname+'/native_gap_original.png'});
  fs.writeFileSync(__dirname+'/native_gap_browser.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
