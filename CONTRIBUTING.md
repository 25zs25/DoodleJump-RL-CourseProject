# 四人协作说明

公开仓库可直接克隆。需要直接推送时由仓库所有者在 Settings → Collaborators 中添加组员GitHub账号；也可以Fork后通过Pull Request提交。下载代码不需要协作者权限。

## 模块分工

| 成员占位 | 主要模块 | 对应报告 |
| --- | --- | --- |
| A | 原版保留、环境与逐帧一致性验证 | `reports/A_环境与原版保留报告.md` |
| B | DQN、Double DQN与训练诊断 | `reports/B_DQN与DoubleDQN报告.md` |
| C | PPO、GAE与速度观测消融 | `reports/C_PPO与消融报告.md` |
| D | 独立评测、网页部署与PPT | `reports/D_评测部署与汇报报告.md` |

以上为项目模块建议和技术草稿，不能代替实际完成者署名。先在报告中填写真实姓名与已完成贡献。

## 提交修改

```bash
git pull --ff-only
git switch -c codex/your-topic
# 修改自己的模块
git add <修改的文件>
git commit -m "Describe the change"
git push -u origin codex/your-topic
```

在GitHub中发起Pull Request说明修改目的与验证结果。不要提交凭据、虚拟环境、浏览器缓存、完整回放缓存或大批中间检查点；现有训练权重已随首版保留。

## 实验约定

- `upstream/` 是冻结的原版文件；不要修改外观、平台分布、物理或碰撞来提高得分。
- 当前主实验入口为 `retrain_native.py`，冻结协议为 `experiments/native_retrain_20261008/protocol.json`。
- 不覆盖已发布模型和测试结果；新实验使用新的run-id、独立输出路径和清楚的预算、窗口、种子记录。
- 测试集不用于挑选模型，窗口或奖励改变时应明确标注新实验，不能混入当前成绩。
- 代码验证命令见README。文档修改可检查链接、数值与真实贡献，无需重新训练模型。
