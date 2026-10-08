# 2026-10-08 公开发布说明

仓库： https://github.com/25zs25/DoodleJump-RL-CourseProject

来源为已经完成训练、评测和逐页视觉检查的最终交付。公开版本新增README入口、MIT许可证、第三方说明和组员协作指引；部分文本元数据中的原作者本机目录替换为 `<PROJECT_ROOT>` 或 `<USER_HOME>`，因此重新生成 `public_manifest.json`，不沿用旧交付文件清单。

原版21个文件、训练/评测源代码、模型权重、测试数值、PPT和游戏外观/物理未改变。权重中可能包含训练配置元数据；不把模型检查点当作凭据存储。`VERIFICATION.json` 是原完成交付的验证记录，其协议和模型哈希仍可核验。PPT的渲染源记录依赖当时的Codex演示文稿运行时，组员可直接使用已导出的可编辑PPT，无需该运行时。

旧405×720模型与实验文件仅供历史追溯。新实验统一标为 `native_v2` 或 `native-viewport-v2`。

原交付压缩包SHA256： `7ee81ab4e7afabd10f55b593d51be49c2ed0799b43d6de0723d1478b83eecb74`

下列 69 份文本文件仅清理本机路径（算法源和原版文件未改变）：

- `experiments/native_retrain_20261008/presentation_source.mjs`
- `experiments/native_retrain_20261008/presentation_validation.json`
- `models/native_v2_double_dqn_full_h128_seed143_1000000/config.json`
- `models/native_v2_double_dqn_full_h128_seed143_1000000/status.json`
- `models/native_v2_double_dqn_full_h128_seed42_1000000/config.json`
- `models/native_v2_double_dqn_full_h128_seed42_1000000/status.json`
- `models/native_v2_double_dqn_full_h128_seed59_1000000/config.json`
- `models/native_v2_double_dqn_full_h128_seed59_1000000/status.json`
- `models/native_v2_dqn_full_h128_seed143_1000000/config.json`
- `models/native_v2_dqn_full_h128_seed143_1000000/status.json`
- `models/native_v2_dqn_full_h128_seed42_1000000/config.json`
- `models/native_v2_dqn_full_h128_seed42_1000000/status.json`
- `models/native_v2_dqn_full_h128_seed59_1000000/config.json`
- `models/native_v2_dqn_full_h128_seed59_1000000/status.json`
- `models/native_v2_ppo_full_h128_seed143_1000000/config.json`
- `models/native_v2_ppo_full_h128_seed143_1000000/status.json`
- `models/native_v2_ppo_full_h128_seed42_1000000/config.json`
- `models/native_v2_ppo_full_h128_seed42_1000000/status.json`
- `models/native_v2_ppo_full_h128_seed59_1000000/config.json`
- `models/native_v2_ppo_full_h128_seed59_1000000/status.json`
- `models/native_v2_ppo_no_velocity_h128_seed143_1000000/config.json`
- `models/native_v2_ppo_no_velocity_h128_seed143_1000000/status.json`
- `models/native_v2_ppo_no_velocity_h128_seed42_1000000/config.json`
- `models/native_v2_ppo_no_velocity_h128_seed42_1000000/status.json`
- `models/native_v2_ppo_no_velocity_h128_seed59_1000000/config.json`
- `models/native_v2_ppo_no_velocity_h128_seed59_1000000/status.json`
- `results/evaluation/double_dqn_full_seed143_1000000_original.json`
- `results/evaluation/double_dqn_full_seed143_1000000_viewport600.json`
- `results/evaluation/double_dqn_full_seed143_1000000_viewport900.json`
- `results/evaluation/double_dqn_full_seed42_1000000_original.json`
- `results/evaluation/double_dqn_full_seed42_1000000_viewport600.json`
- `results/evaluation/double_dqn_full_seed42_1000000_viewport900.json`
- `results/evaluation/double_dqn_full_seed59_1000000_original.json`
- `results/evaluation/double_dqn_full_seed59_1000000_viewport600.json`
- `results/evaluation/double_dqn_full_seed59_1000000_viewport900.json`
- `results/evaluation/dqn_full_seed143_1000000_original.json`
- `results/evaluation/dqn_full_seed143_1000000_viewport600.json`
- `results/evaluation/dqn_full_seed143_1000000_viewport900.json`
- `results/evaluation/dqn_full_seed42_1000000_original.json`
- `results/evaluation/dqn_full_seed42_1000000_viewport600.json`
- `results/evaluation/dqn_full_seed42_1000000_viewport900.json`
- `results/evaluation/dqn_full_seed59_1000000_original.json`
- `results/evaluation/dqn_full_seed59_1000000_viewport600.json`
- `results/evaluation/dqn_full_seed59_1000000_viewport900.json`
- `results/evaluation/ppo_full_seed143_1000000_original.json`
- `results/evaluation/ppo_full_seed143_1000000_original_sample.json`
- `results/evaluation/ppo_full_seed143_1000000_viewport600.json`
- `results/evaluation/ppo_full_seed143_1000000_viewport900.json`
- `results/evaluation/ppo_full_seed42_1000000_original.json`
- `results/evaluation/ppo_full_seed42_1000000_original_sample.json`
- `results/evaluation/ppo_full_seed42_1000000_viewport600.json`
- `results/evaluation/ppo_full_seed42_1000000_viewport900.json`
- `results/evaluation/ppo_full_seed59_1000000_original.json`
- `results/evaluation/ppo_full_seed59_1000000_original_sample.json`
- `results/evaluation/ppo_full_seed59_1000000_viewport600.json`
- `results/evaluation/ppo_full_seed59_1000000_viewport900.json`
- `results/evaluation/ppo_no_velocity_seed143_1000000_original.json`
- `results/evaluation/ppo_no_velocity_seed143_1000000_viewport600.json`
- `results/evaluation/ppo_no_velocity_seed143_1000000_viewport900.json`
- `results/evaluation/ppo_no_velocity_seed42_1000000_original.json`
- `results/evaluation/ppo_no_velocity_seed42_1000000_viewport600.json`
- `results/evaluation/ppo_no_velocity_seed42_1000000_viewport900.json`
- `results/evaluation/ppo_no_velocity_seed59_1000000_original.json`
- `results/evaluation/ppo_no_velocity_seed59_1000000_viewport600.json`
- `results/evaluation/ppo_no_velocity_seed59_1000000_viewport900.json`
- `results/native_v2/summary.json`
- `results/presentation_data.json`
- `results/summary.json`
- `results.js`
