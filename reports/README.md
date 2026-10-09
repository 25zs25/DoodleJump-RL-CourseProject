# 课程报告使用说明

本目录包含四份个人模块报告和一份小组技术报告。每份同时提供正式A4 PDF和可编辑Markdown，数字对应2026年10月8日的 native-viewport-v2 原窗口重训。

| 报告 | 正式PDF | 可编辑Markdown | 对应内容 |
| --- | --- | --- | --- |
| A 环境与原版保留 | [下载PDF](A_环境与原版保留报告.pdf) | [编辑源稿](A_环境与原版保留报告.md) | 原版边界、种子、209维观测、物理和逐帧一致性 |
| B DQN与DoubleDQN | [下载PDF](B_DQN与DoubleDQN报告.pdf) | [编辑源稿](B_DQN与DoubleDQN报告.md) | TD目标、网络、超参、真实对照和复现 |
| C PPO与消融 | [下载PDF](C_PPO与消融报告.pdf) | [编辑源稿](C_PPO与消融报告.md) | 策略目标、GAE边界、速度置零和部署方式 |
| D 评测部署与汇报 | [下载PDF](D_评测部署与汇报报告.pdf) | [编辑源稿](D_评测部署与汇报报告.md) | 5400局组成、统计、浏览器推理、演示与课程交付 |
| 小组技术报告 | [下载PDF](小组技术报告.pdf) | [编辑源稿](小组技术报告.md) | 系统、实验、结果、局限和来源 |

四份个人报告保留姓名、学号和实际参与填写区。模块叙述不等于四位成员已经亲自完成全部对应工作；提交前按真实实现、复核、实验和写作贡献补全，核对姓名与学号。

当前逐局数据在 `results/native_v2/test_episodes.csv` 与 `baseline_episodes.csv`，根目录旧结果仅用于历史复现。±表示三训练种子均分之间的样本SD，不是300局置信区间。原版得分与最高攀升分开报告。

报告为静态PDF，填信息或改内容时编辑同名Markdown并重新导出。项目源代码、模型、原版素材与来源声明的授权边界参见项目LICENSE及THIRD_PARTY_NOTICES.md。

## 填写后重新导出

在项目根目录执行：

```powershell
python -m pip install -r reports/requirements-render.txt
python reports/export_pdf.py --output-dir reports/updated
```

工具读取五份报告Markdown，把新PDF放到 `reports/updated/`，保留原始源稿和已验收PDF。只导出一份可加 `--file reports/B_DQN与DoubleDQN报告.md`。重复导出到同一目录需加 `--overwrite`。Windows默认使用微软雅黑；其他系统通过 `--font` 和 `--bold-font` 指定含中文字形的TrueType字体（TTF或TTC）。修改内容后重新检查分页与姓名、实际贡献字段。

正式交付PDF的页数、源稿与PDF哈希及逐页检查记录见 [REPORT_VERIFICATION.json](REPORT_VERIFICATION.json)。
