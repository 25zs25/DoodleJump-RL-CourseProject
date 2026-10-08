(()=>{
const $=s=>document.querySelector(s),frame=$('#game'),models=window.ORIGINAL_MODELS||[];let ready=false,last=null,playing=false;
const algorithmNames={double_dqn:'Double DQN',dqn:'DQN',ppo:'PPO'};
// The demo exposes one full-observation checkpoint per algorithm. Selection
// uses held-out validation scores; all repeated training runs remain recorded.
const displayModels=Object.keys(algorithmNames).map(algorithm=>models
  .filter(m=>m.algorithm===algorithm&&m.observation==='full')
  .sort((a,b)=>(b.validation_score??-Infinity)-(a.validation_score??-Infinity))[0])
  .filter(Boolean);
for(const m of displayModels){const o=document.createElement('option');o.value=m.id;o.textContent=algorithmNames[m.algorithm]+(m.environment_version==='native-viewport-v2'?'（当前窗口重训）':'（旧720窗口模型）');$('#controller').append(o);}
function send(command,extra={}){frame.contentWindow.postMessage({type:'doodle-command',command,...extra},location.origin);}
function selected(){return models.find(m=>m.id===$('#controller').value);}
function configure(){const m=selected();send('controller',{controller:m?'model':$('#controller').value,model:m,sample:$('#selection').value==='sample'});$('#model-info').textContent=m?`${algorithmNames[m.algorithm]}，网络 ${m.dimensions.join(' → ')}。${m.viewport?`训练画布 ${m.viewport.join(' × ')}，完成100万决策；按验证成绩选择权重。窗口变化会影响表现。`:'旧720高度训练权重，历史实验记录见报告。'}`:'手动试玩调用原版按键、触屏和逐帧更新；地图种子仅用于复现。';$('#selection').disabled=m?.algorithm!=='ppo';}
function reset(){configure();send('reset',{seed:Number($('#seed').value)>>>0});playing=false;$('#start').textContent='开始';}
$('#reset').onclick=reset;$('#start').onclick=()=>{if(!ready)return;if(last?.phase==='ended')reset();playing=!playing;send(playing?'start':'pause');$('#start').textContent=playing?'暂停':'开始';};
$('#controller').onchange=reset;$('#selection').onchange=reset;
const pressed=new Set();function action(){send('action',{action:pressed.has('left')?0:pressed.has('right')?2:1});}
addEventListener('keydown',e=>{if(['INPUT','SELECT','TEXTAREA'].includes(e.target.tagName))return;const k=e.key.toLowerCase();if(['arrowleft','a','arrowright','d',' '].includes(k))e.preventDefault();if(k==='arrowleft'||k==='a')pressed.add('left');if(k==='arrowright'||k==='d')pressed.add('right');if(k===' '&&!e.repeat)$('#start').click();action();});
addEventListener('keyup',e=>{if(['ArrowLeft','a','A'].includes(e.key))pressed.delete('left');if(['ArrowRight','d','D'].includes(e.key))pressed.delete('right');action();});
addEventListener('blur',()=>{pressed.clear();action();});
for(const side of ['left','right']){const b=$('#'+side);b.onpointerdown=e=>{b.setPointerCapture(e.pointerId);pressed.add(side);action();};b.onpointerup=b.onpointercancel=()=>{pressed.delete(side);action();};}
addEventListener('message',e=>{if(e.origin!==location.origin||e.source!==frame.contentWindow||e.data.type!=='doodle-state')return;last=e.data;if(!ready&&last.ready){ready=true;reset();}const i=last.info;$('#score').textContent=i.score.toLocaleString();$('#height').textContent=i.height.toFixed(0)+' px';$('#steps').textContent=`${i.steps} / ${['左','停','右'][last.action]}`;$('#status').textContent=last.phase==='running'?'运行中':last.phase==='ended'?(i.death_reason==='blackhole'?'撞黑洞':i.death_reason==='fall'?'跌落':'达到训练时限'):'已暂停';const g=last.geometry;if(g)$('#geometry').textContent=`原版窗口 ${g.windowWidth} × ${g.windowHeight}；画布 ${g.width.toFixed(1)} × ${g.height}；初始层距 ${g.stepSize}px。`;$('#network').textContent=last.network?'网络输出：'+last.network.map(v=>v.toFixed(3)).join('，'):'';if(last.phase==='ended'){playing=false;$('#start').textContent='重新开始';}});
if(matchMedia('(max-width:1100px)').matches)$('#controls').open=false;
$('#open-results').onclick=()=>$('#results-dialog').showModal();$('#close-results').onclick=()=>$('#results-dialog').close();
$('#results-dialog').onclick=e=>{if(e.target===$('#results-dialog'))e.target.close();};
$('#export-viewport').onclick=()=>{if(!last?.geometry)return;const config={...last.geometry,upstream_commit:'d4b6071813a9c1353267d53dcfa9d8abc3e5b2f4',environment_version:'native-viewport-v2'},url=URL.createObjectURL(new Blob([JSON.stringify(config,null,2)],{type:'application/json'})),link=document.createElement('a');link.href=url;link.download='native-viewport.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
const data=window.ORIGINAL_RESULTS;
if(data){$('#summary').textContent=data.caption;$('#table').innerHTML='<table><thead><tr><th>策略</th><th>场景</th><th>原版得分 ± 种子SD</th><th>平均上升高度</th><th>时限截断</th></tr></thead><tbody>'+data.rows.map(r=>`<tr><td>${r.label}</td><td>${r.mode}</td><td>${r.mean.toFixed(0)}${r.sd===null?'（100图，无训练）':' ± '+r.sd.toFixed(0)}</td><td>${r.height.toFixed(0)} px</td><td>${r.reason}</td></tr>`).join('')+'</tbody></table>';const c=$('#curve'),ctx=c.getContext('2d'),colors=['#ae772b','#2b84a0','#599436'],max=Math.max(100,...data.curves.flatMap(x=>x.scores));ctx.font='16px Microsoft YaHei';ctx.fillStyle='#637b50';for(let j=0;j<=4;j++){const y=275-j*55;ctx.strokeStyle='#d6dac4';ctx.beginPath();ctx.moveTo(65,y);ctx.lineTo(1000,y);ctx.stroke();ctx.fillText((max*j/4).toFixed(0),5,y+5);}data.curves.forEach((r,i)=>{ctx.strokeStyle=colors[i];ctx.lineWidth=3;ctx.beginPath();r.scores.forEach((v,j)=>{const x=65+j/(r.scores.length-1)*935,y=275-v/max*220;j?ctx.lineTo(x,y):ctx.moveTo(x,y);});ctx.stroke();ctx.fillStyle=colors[i];ctx.fillText(r.label,65+i*230,320);});ctx.fillStyle='#637b50';ctx.fillText('验证集原版得分 / 决策交互数',65,25);ctx.fillText('100万步',920,300);}
window.OriginalApp={state:()=>last,send,models,displayModels};
})();
