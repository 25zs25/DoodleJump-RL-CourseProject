# Doodle Jump 原版窗口强化学习项目

2026-10-08已取消此前固定405×720试玩。游戏直接执行takosenpai2687/doodle-jump固定提交d4b6071813a9c1353267d53dcfa9d8abc3e5b2f4的原脚本，按当前浏览器真实窗口初始化。全部21个上游文件未修改；图片、物理、平台生成、黑洞、碰撞、计分与窗口适配由原版决定。

## 运行

双击start_game.cmd；或在本目录运行`python serve.py --port 8765`，打开http://127.0.0.1:8765/。已有服务仍可用，按Ctrl+F5强制刷新。

默认手动试玩，点击“开始”，←/→或A/D控制，空格暂停；手机点击游戏左右半边。控制面板可收起，手动游戏无训练步数上限。原版改变窗口时存在缩放问题，改变窗口后刷新初始化，再导出训练配置。

“未修改的原版”打开upstream/index.html；“同种子原版对照”打开compare.html，可逐帧同步动作。双方同窗口、种子、动作时平台及物理状态一致。原版默认随机，每次独立打开的随机地图不会自动相同。

## 为什么之前会卡住

固定720高度恰好只生成9层，原版回收却按10层间距放回，出现约150–160像素空档，正常跳跃约114像素。真实浏览器原版中已复现此情况，不能归因网络参数不足。此次取消固定窗口，保持原公式；部分实际窗口也可能触发原版自身的问题，不擅自加密平台或增大跳力。详见WINDOW_AUDIT.md。

## 模型与实验状态

下拉框保留DQN、Double DQN、PPO各一个旧720窗口模型，均明确标注；当前真实窗口表现需要重评。模型种子不作为试玩选项，地图种子只用于复现地图。

旧12组CPU训练、旧统计、PPT与报告来自405×720历史窗口。它们不代表当前窗口效果。本轮GPU512网络已完成100万步，GPU128在反馈后停止于最后保存的25万步检查点；配对实验及独立测试没有完成，没有容量提升结论。记录见experiments/capacity_1m_seed42/environment_review.json。

## 新窗口训练

先在试玩页刷新后点击“导出训练窗口”，把native-viewport.json放在本目录。此文件只读取原版画布、窗口、跳跃与重力，不修改规则；训练入口会拒绝省略窗口配置或重复缩放的配置。训练和验证使用同一导出宽高，移动端不再强行使用桌面9:16宽度。

依赖版本见requirements-tested.txt。正式容量对照的两个命令如下，二者使用同一个导出文件；此轮尚未重新执行：

```powershell
python train.py --algorithm double_dqn --hidden 128 --device cuda --seed 42 --steps 1000000 --viewport-json native-viewport.json --epsilon-decay-steps 600000 --checkpoint-every 50000 --run-id native_ddqn_h128_seed42_1000000
python train.py --algorithm double_dqn --hidden 512 --device cuda --seed 42 --steps 1000000 --viewport-json native-viewport.json --epsilon-decay-steps 600000 --checkpoint-every 50000 --run-id native_ddqn_h512_seed42_1000000
```

新检查点记录真实窗口，evaluate.py在original模式默认读取其窗口；也可显式传`--viewport-json`。旧检查点没有该元数据，默认仅复现旧720实验。旧run_experiments.py和旧协议属于历史实验，不能直接当作新窗口训练入口。

状态仍为209维：玩家5，最多20个平台各10，黑洞4；输出左/停/右3个动作，每次执行4帧。奖励仍为原版得分增量/100−0.001−死亡，不改变原版得分。

## 验证

```powershell
python -m unittest discover -s tests -p test_agents.py
python tests/verify_original.py
python tests/verify_native_window.py
```

verify_original.py需要Node.js，核对30条81803帧轨迹和7类特殊案例。verify_native_window.py核对实际原版浏览器捕获的4种窗口、3096帧，包含移动端宽度。真实Edge浏览器另核对12条共13191帧，报告在tests/native_window_qa.json。独立对照1800帧全一致；原版间距复現6000帧见tests/native_gap_browser.json。

如需重跑浏览器验证，在本目录运行`npm install`安装已测Playwright开发依赖，保持serve.py运行，然后`node tests/qa_native_window.cjs`；默认使用本机Edge。也可设置DOODLE_URL连接不同端口。

仅有3000步新窗口GPU接口检查，已确认更新、验证和保存使用596.25×1060实测画布；它是运行验证，不是正式训练效果。旧PPT与报告须在新实验完成后更新，不应当作当前项目最终效果交付。
