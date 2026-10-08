const fs=require('fs'),vm=require('vm'),path=require('path');
const project=path.resolve(__dirname,'..');
const input=JSON.parse(fs.readFileSync(0,'utf8')),h=input.height||720,w=h*9/16;
const ctx={console,Math:Object.create(Math),Float32Array,windowWidth:w,windowHeight:h,width:w,height:h,
window:{matchMedia:()=>({matches:false})},frameRate:()=>70,createCanvas:(a,b)=>{ctx.width=a;ctx.height=b},resizeCanvas:(a,b)=>{ctx.width=a;ctx.height=b},
userStartAudio:()=>{},noLoop:()=>{},soundFormats:()=>{},loadImage:()=>({}),loadSound:()=>null,
noStroke:()=>{},rectMode:()=>{},fill:()=>{},rect:()=>{},stroke:()=>{},strokeWeight:()=>{},arc:()=>{},line:()=>{},image:()=>{},background:()=>{},textSize:()=>{},textStyle:()=>{},textWidth:s=>s.length*10,textAlign:()=>{},text:()=>{},color:x=>x,
dist:(x,y,a,b)=>Math.hypot(x-a,y-b),floor:Math.floor,ellipse:()=>{},RADIUS:1,HALF_PI:Math.PI/2,PI:Math.PI,OPEN:1,BOLD:1,LEFT:1,NORMAL:1,CENTER:1};
vm.createContext(ctx);
for(const f of ['config','blackhole','platform','doodler','index'])vm.runInContext(fs.readFileSync(path.join(project,'upstream/js',f+'.js'),'utf8'),ctx,{filename:f+'.js'});
vm.runInContext(fs.readFileSync(path.join(project,'bridge-core.js'),'utf8'),ctx);
const observation=ctx.DoodleNative.boot(input.seed||42,input.observation||'full');
if(input.inject){ctx.inject=input.inject;vm.runInContext(`
 for(const k of ['x','y','vx','vy'])if(k in inject)doodler[k]=inject[k];
 if(inject.platforms)platforms=inject.platforms.map(p=>Object.assign(Object.create(Platform.prototype),p));
 if('hole' in inject)blackhole=inject.hole?Object.assign(new Blackhole(0,0),inject.hole):null;
 if('spawn_y' in inject)DoodleNative.metrics().spawnY=inject.spawn_y;
`,ctx);}
const records=[{snapshot:ctx.DoodleNative.snapshot(),obs:ctx.DoodleNative.obs()}];
for(const a of input.actions){let r=ctx.DoodleNative.step(a,input.repeat||4,input.maxSteps||1500);records.push(r);if(r.terminated||r.truncated)break;}
process.stdout.write(JSON.stringify(records));
