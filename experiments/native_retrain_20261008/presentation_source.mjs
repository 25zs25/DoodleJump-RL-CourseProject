import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
process.env.RUNTIME_NODE_MODULES='<USER_HOME>/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules';
const ROOT=path.resolve('.'),OUT=path.join(ROOT,'outputs/doodle_jump_original'),WORK=path.join(ROOT,'work/doodle_native_deck');
const SKILL='<USER_HOME>/.codex/plugins/cache/openai-primary-runtime/presentations/26.1007.11041/skills/presentations',PYTHON='<USER_HOME>/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe';
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(path.join(SKILL,'container_tools/artifact_tool_utils.mjs')));
const D=JSON.parse(await fs.readFile(path.join(OUT,'results/presentation_data.json'),'utf8'));
const FONT='Microsoft YaHei',INK='#163229',GREEN='#39744A',BLUE='#346F9D',GOLD='#BC7C30',MUTED='#58655E',PAPER='#FAF9F1';
const colors={dqn:GOLD,double_dqn:BLUE,ppo:GREEN};
const refs={game:'https://github.com/takosenpai2687/doodle-jump/tree/d4b6071813a9c1353267d53dcfa9d8abc3e5b2f4',dqn:'https://arxiv.org/abs/1312.5602',ddqn:'https://arxiv.org/abs/1509.06461',ppo:'https://arxiv.org/abs/1707.06347',gae:'https://arxiv.org/abs/1506.02438'};
const pres=Presentation.create({slideSize:{width:1280,height:720}}),slides=[],pages=[],timing=[25,45,55,55,60,60,65,55,65,60,65,65,60,45];
function text(sl,s,x,y,w,h,size=28,color=INK,bold=false){const a=sl.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});a.text=String(s);a.text.style={typeface:FONT,fontSize:size,color,bold,autoFit:'none'};return a;}
function slide(title,notes,sources=[]){const n=slides.length+1,sl=pres.slides.add();slides.push(sl);notes=D.talk[n]??notes;sl.background.fill=PAPER;text(sl,title,64,44,1150,78,43,INK,true);text(sl,'DOODLE JUMP / 原版规则强化学习',64,675,1060,22,15,MUTED);text(sl,String(n).padStart(2,'0'),1155,663,70,38,19,MUTED);const seconds=timing[n-1]??0;sl.speakerNotes.textFrame.setText((seconds?`建议时长 ${seconds} 秒。\n`:'答辩备用页，不计入13分钟。\n')+notes+(sources.length?'\n参考来源：\n'+sources.join('\n'):''));pages.push({slide:n,title,seconds,notes});return sl;}
function table(sl,values,x,y,w,h,widths,size=25){const t=sl.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,values,columnWidths:widths});for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){const cell=t.getCell(r,c);cell.fill=r===0?'#E4EBDD':PAPER;cell.text.style={typeface:FONT,fontSize:size,color:INK,bold:r===0};}t.borders.assign({fill:'#D3DBCD',width:1,style:'solid'});return t;}
function chart(sl,type,cats,series,pos,opts={}){series=series.map(s=>({...s,values:s.values.map(v=>Number(v.toFixed(3)))}));const c=sl.charts.add(type,{position:pos,categories:cats,series,hasLegend:true,legend:{position:'bottom',overlay:false,textStyle:{typeface:FONT,fontSize:23,fill:INK}},xAxis:{textStyle:{typeface:FONT,fontSize:23,fill:MUTED}},yAxis:{min:0,numberFormatCode:'0',textStyle:{typeface:FONT,fontSize:22,fill:MUTED},majorGridlines:{fill:'#D9DFD2',width:1,style:'solid'}},chartFill:PAPER,plotAreaFill:PAPER,chartLine:{fill:'none',width:0},...opts});applyPresentationChartFont(c,{fontFamily:FONT});return c;}
async function pic(sl,file,x,y,w,h){sl.images.add({blob:new Uint8Array(await fs.readFile(path.join(OUT,file))),contentType:'image/png',alt:'原仓库素材或本项目实际浏览器运行画面',fit:'contain',position:{left:x,top:y,width:w,height:h}});}
const num=v=>Number(v).toFixed(0),row=(a,m='native')=>D.main.find(r=>r.algorithm===a&&r.mode===m);
let sl=slide('Doodle Jump 原版规则强化学习','本项目使用开源原版的引擎和素材，通过训练接口学习左右控制，比较DQN、Double DQN与PPO。',[refs.game]);
text(sl,'DQN / Double DQN / PPO',64,173,820,60,38,GREEN,true);text(sl,'保留原画面、物理与平台随机生成\n从头训练并测试学习效果',64,298,820,143,41,INK,true);text(sl,'四人小组 A–D（姓名待填写）\n26秋研究生强化学习课程\n主讲14页，约13分钟',64,528,780,103,25,MUTED);await pic(sl,'upstream/assets/img/doodler_right.png',930,199,235,326);

sl=slide('自动跳跃需要持续预测落点','绿色普通、蓝色移动、白色易碎平台使用原绘制函数。角色自动弹跳，模型左右控制，利用弹簧与绕屏并避开黑洞。',[refs.game]);
await pic(sl,'assets/native_mechanics.png',64,151,365,482);table(sl,[['原版机制','控制难点'],['移动平台','预测下降时的横向位置'],['易碎平台','落地后不能重复借力'],['弹簧','更长飞行时间和更远落点'],['黑洞与绕屏','比较两侧移动并规避危险']],472,173,739,393,[210,529],25);text(sl,'每4个物理帧观察一次，选择左 / 不动 / 右',474,592,734,55,25,GREEN,true);

sl=slide('原版文件与游戏规则保持不变','upstream保存21个原文件。浏览器直接调用原setup、draw、reset，Python以这些未改代码为对照移植。种子控制替换随机源，未添加地图安全性约束。',[refs.game]);
table(sl,[['项目','保留的实际行为'],['外观与声音','原角色图片、平台绘制、网格、音效和署名'],['物理与顺序','直接横向速度、不同升降重力、先碰撞再移动'],['平台生成','全宽随机、原类型抽样、易碎旁补普通'],['原版特殊行为','顶部出生、300阈值、弹簧碰撞尺寸、数组刷新'],['新增训练接口','reset(seed)、step(action)、观测、奖励、时限']],64,164,1150,386,[270,880],25);text(sl,'原版得分按滚屏时处理的平台数累计，得分并非像素高度',64,586,1150,67,26,GREEN,true);

sl=slide('209维观测与三动作策略','209维指输入向量长度。局部结构特征不包含未来地图、随机状态、目标平台或教师动作。奖励使用原版得分增量，同时保留实际高度作为独立指标。');
table(sl,[['观测','维数','内容'],['玩家','5','位置、速度和最高高度差'],['可见平台','20×10=200','相对位置、宽度、速度、类型、弹簧、掩码'],['原版单黑洞','4','相对位置、半径和掩码']],64,162,1150,275,[240,225,685],25);text(sl,'209 → 128 → 128 → 左 / 不动 / 右',64,469,1150,56,34,GREEN,true);text(sl,'r = Δ原版得分 / 100 − 0.001 − 1×死亡\n1500决策为时间截断，跌落或黑洞为真实终止',64,560,1150,93,28);

sl=slide('DQN与Double DQN只改变TD目标','经验回放与目标网络保持一致。DQN目标中的最大值会放大带噪声的估计，Double DQN分离动作选择和价值评估，但并不保证最终成绩更高。',[refs.dqn,refs.ddqn]);
text(sl,'DQN',64,174,600,53,34,GOLD,true);text(sl,'y = r + γ maxₐ Qtarget(s′, a)',64,253,1150,64,35);text(sl,'Double DQN',64,353,700,53,34,BLUE,true);text(sl,'a* = argmaxₐ Qonline(s′, a)\ny = r + γ Qtarget(s′, a*)',64,430,1150,114,33);text(sl,'真实终止屏蔽bootstrap，时间截断保留下一状态价值',64,608,1150,41,25,MUTED);

sl=slide('PPO用动作概率与优势更新策略','Actor产生动作概率，Critic估计状态价值。GAE组合多步TD误差，概率比裁剪限制过大的策略更新。相同交互预算不代表相同计算量。',[refs.ppo,refs.gae]);
text(sl,'ρₜ = πθ(aₜ | sₜ) / πold(aₜ | sₜ)',64,170,1150,73,35,GREEN,true);text(sl,'Lclip = E[min(ρₜAₜ, clip(ρₜ, 0.8, 1.2)Aₜ)]',64,279,1150,76,32);text(sl,'δₜ = rₜ + γV(sₜ₊₁) − V(sₜ)\nGAE(γ=0.99, λ=0.95)估计动作优势',64,387,1150,113,31);text(sl,'PPO使用当前策略采样，DQN反复使用长期回放\n重置时停止优势递推，时限仍bootstrap',64,569,1150,87,26,MUTED);

sl=slide('每次100万决策，三个独立训练种子','主实验9次、消融3次，每次100万决策。验证地图选择最佳检查点，39组保留测试各100张图。没有按测试成绩挑权重。');
table(sl,[['数据划分','种子或窗口','用途'],['训练','42、59、143；地图≥1000000','683×871当前原版窗口更新策略'],['验证','10000–10019','选检查点，记录学习曲线'],['原窗口测试','61000–61099；683×871','同分布新地图'],['窗口适应测试','62000–62099；596.25×1060','沿用原窗口缩放规则'],['窗口适应测试','63000–63099；390×844','沿用原窗口缩放规则']],64,163,1150,372,[260,465,425],24);text(sl,'12次训练共1200万决策，主比较统一argmax',64,565,1150,50,32,GREEN,true);text(sl,'±为3个训练种子之间的SD，地图数量不能当作训练种子数',64,624,1150,33,23,MUTED);

sl=slide('验证得分的学习曲线',D.talk[8]);
chart(sl,'line',D.curves[0].steps.filter((_,i)=>i%2===1).map(s=>`${s/10000}万`),D.curves.map(c=>({name:c.label,values:c.scores.filter((_,i)=>i%2===1),line:{fill:colors[c.algorithm],width:4,style:'solid'},marker:{symbol:'circle',size:6}})),{left:64,top:158,width:1150,height:424},{lineOptions:{grouping:'standard',smooth:false}});text(sl,'纵轴：20张验证图的原版平均得分，再对3种子取均值',64,602,1150,42,25,MUTED);

sl=slide('当前窗口保留地图测试',D.talk[9]);
table(sl,[['策略','原版得分（均值 ± SD）','实际上升高度'],...D.main_rows],64,166,1150,370,[285,555,310],25);text(sl,'每个学习策略3种子×100图，所有策略使用相同测试图',64,559,1150,42,26,GREEN,true);text(sl,D.sample_caption,64,613,1150,42,23,MUTED);

sl=slide('窗口适应能力仍有明显差异',D.talk[10]);
chart(sl,'bar',['训练窗口683×871','桌面596.25×1060','手机390×844'],['dqn','double_dqn','ppo'].map(a=>({name:row(a).label,values:['native','desktop','mobile'].map(m=>row(a,m).mean),fill:colors[a]})),{left:64,top:158,width:1150,height:414},{barOptions:{direction:'column',grouping:'clustered',gapWidth:150},dataLabels:{showValue:true,position:'outEnd',textStyle:{typeface:FONT,fontSize:21,fill:INK},numberFormatCode:'0'}});text(sl,'纵轴为原版得分。窗口改变尺度与初始布局，应在同窗口比较算法',64,599,1150,61,25,MUTED);

sl=slide('PPO速度置零消融',D.talk[11]);
table(sl,[['观测设置','当前窗口','桌面窗口','手机窗口'],...D.ablation_rows],64,185,1150,228,[340,270,270,270],25);text(sl,D.ablation_caption,64,476,1150,111,31,GREEN,true);text(sl,'维数209、网络和预算不变，玩家与平台速度置零后重新训练',64,616,1150,40,24,MUTED);

sl=slide('真实推理画面与失败回合',D.talk[12]);
await pic(sl,'assets/native_demo.png',64,151,325,483);await pic(sl,'assets/native_failure.png',429,151,325,483);text(sl,'验证集展示回合',800,182,413,53,32,GREEN,true);text(sl,D.demo_caption,800,259,413,175,26);text(sl,'失败边界',800,470,413,51,32,BLUE,true);text(sl,D.failure_caption,800,537,413,98,25,MUTED);

sl=slide('四人工作量与模块验收','分工按A–D提供，每人约25%。报告是模块技术草稿，署名前须按实际工作确认。');
table(sl,[['成员','负责工作','验收证据'],['A','原版移植、训练接口、种子','原文件哈希与逐帧原版对照'],['B','DQN / Double DQN实现与训练','TD目标单测、6次训练日志'],['C','PPO / GAE与速度消融','边界单测、6次训练日志'],['D','保留测试、浏览器推理、汇报','逐地图CSV、模型对齐、PPT']],64,176,1150,354,[140,520,490],25);text(sl,'交付代码、原版素材、12组权重、逐局结果、报告与讲稿',64,576,1150,65,28,GREEN,true);

sl=slide('同参数重训的实测结果',D.talk[14]);
text(sl,D.conclusion_title,64,178,1150,125,40,GREEN,true);table(sl,[['算法','旧模型：当前窗口均分 ± SD','重训模型：当前窗口均分 ± SD'],...D.legacy_rows],64,320,1150,211,[230,460,460],25);text(sl,'同一100张新测试地图，参数量不变；历史与当前训练窗口不同',64,566,1150,43,25,MUTED);text(sl,'原版得分和上升高度分开报告，3种子结果仅反映本次实验',64,617,1150,39,24,MUTED);

sl=slide('附录：超参数与实际训练记录','备用页。CPU实测时间包含验证，三进程并行与系统竞争，不能视作标准硬件速度比较。');
table(sl,[['设置','DQN / Double DQN','PPO'],...D.parameter_rows],64,164,1150,421,[330,410,410],23);text(sl,D.parameter_caption,64,619,1150,37,23,MUTED);

sl=slide('附录：原版对照与部署验证','对照直接执行未修改的upstream游戏JavaScript，而非另一份自写移植。', [refs.game]);
table(sl,[['证据','本次检查'],['原文件完整性','21个文件SHA256全部匹配'],['物理逐帧对照','原JS数值81803帧；当前真实浏览器4202帧'],['特殊规则','7案例：弹簧、易碎、边界、黑洞、跌落、绕屏、刷新'],['算法与部署','5项算法单测，12个新模型×360观测，动作一致'],['浏览器与运行','原图加载、手动控制、暂停、重开、一键启动']],64,165,1150,389,[300,850],25);text(sl,'所有原版特殊行为继续保留，修复需新环境版本并重新训练',64,597,1150,53,25,MUTED);

sl=slide('附录：来源与运行入口','游戏代码MIT许可保留，原README中的第三方图片和音效来源一并保留。具体来源与边界见PROVENANCE。',[...Object.values(refs)]);
text(sl,'游戏：takosenpai2687/doodle-jump\n固定提交：d4b6071813a9c1353267d53dcfa9d8abc3e5b2f4\n算法：DQN (2013)、Double DQN (2015)\nPPO (2017)、GAE (2015)',64,170,1150,235,27);text(sl,'试玩：双击 start_game.cmd（需要Python 3）\n复现：README.md / train.py / evaluate.py\n核查：PROVENANCE.md / tests/ / results/',64,467,1150,153,29,GREEN,true);

await fs.mkdir(WORK,{recursive:true});await fs.writeFile(path.join(WORK,'speaker_notes.json'),JSON.stringify(pages,null,2));
const candidate=path.join(WORK,'candidate_native_r2.pptx');await (await PresentationFile.exportPptx(pres)).save(candidate);
const tableOwners=[2,3,4,7,9,11,13,14,15,16],chartOwners=[8,10];
const result=await finalizePresentation({workspaceDir:ROOT,candidatePath:candidate,finalPath:path.join(OUT,'DoodleJump_当前窗口重训_13分钟汇报.pptx'),pythonExecutable:PYTHON,integrityValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_package_integrity.py'),layoutValidatorPath:path.join(SKILL,'container_tools/inspect_presentation_layout_geometry.py'),layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-bullet-geometry','--validate-heading-fit',...tableOwners.flatMap(n=>['--require-native-table-slide',String(n)])],requiredNativeTableOwnerSlides:tableOwners,requiredNativeChartOwnerSlides:chartOwners,materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(WORK,'validation_native.json')});
console.log(JSON.stringify(result));
