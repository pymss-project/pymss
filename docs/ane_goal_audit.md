# Private ANE Goal Audit

更新时间：2026-06-13

本文件按 [ane_goal.md](/Volumes/2T/pymss/docs/ane_goal.md) 的验收标准，
用当前工作区中的现有证据做状态审计。

## 验收标准 1

要求：

```text
能明确描述 descriptor 相关对象的创建链和消费链。
```

当前状态：`已满足`

主要证据：

- [ane_state.md](/Volumes/2T/pymss/docs/ane_state.md)
  中关于：
  - `AppleNeuralEngine.framework` load 主链
  - `_ANEClient / _ANEVirtualClient / _ANEModel`
  - wrapper-route / MIL / precompiled path 分界
- [final_blocker_evidence_package_note.md](/Volumes/2T/pymss/mps/ANE/experiments/results/final_blocker_evidence_package_note.md)
- 多份 bootkc 结果 note，已把 lower accepted-state family 收敛到：
  - `additional_params+0x18 / resource+0x493a0`
  - `resource+0x400d0`
  - `resource+0x402f0`
  - `record+0x1b8`
  - `process+0x203fc`

## 验收标准 2

要求：

```text
至少确认一组会影响 segment/cache/load/eval 的字段、selector 或 artifact 结构。
```

当前状态：`已满足`

主要证据：

- wrapper / file-model / companion / `cacheURLIdentifier` 路线
- `kANEFModelType` 与 `.hwx` file-model precompiled path 条件
- `modelAtURL:key:` vs `modelAtURLWithSourceURL:...cacheURLIdentifier:`
  的不同运行语义
- bootkc lower family：
  - `resource+0x493a0`
  - `resource+0x400d0`
  - `resource+0x402f0`
  - `record+0x1b8`

参考：

- [ane_state.md](/Volumes/2T/pymss/docs/ane_state.md)
- [current_control_layer_blocker_note.md](/Volumes/2T/pymss/mps/ANE/experiments/results/current_control_layer_blocker_note.md)

## 验收标准 3

要求：

```text
做出最小 PoC，证明修改该层会改变运行行为，例如：
- 更少 loadModel
- 更少 compileModel
- 更稳定 cache hit
- 更少 transformer 分段
- 更少 pre_eval
```

当前状态：`已满足`

主要证据：

- wrapper-route warm replay 原型
- `load_cache_client_wrapper_warm` 路由命中
- `bridge_profile_file_write_sec` 显著下降
- warm route 下 `load_qos` / repeated compile-load 行为变化明确

参考：

- [ane_state.md](/Volumes/2T/pymss/docs/ane_state.md)
  中 `test_clean_wrapper_route_*` 一组结果
- [final_blocker_evidence_package_note.md](/Volumes/2T/pymss/mps/ANE/experiments/results/final_blocker_evidence_package_note.md)

## 验收标准 4

要求：

```text
使用 test_clean.m4a 复测，private ANE wall time 相比当前较好结果有明确改进；目标为 <= 30s。
```

当前状态：`已满足（warm wrapper-route 原型）`

主要证据：

- 历史 private ANE supervised baseline：
  - `43.00265733300148 s`
  - 见 [ane_state.md](/Volumes/2T/pymss/docs/ane_state.md)
- 当前最好 warm wrapper-route：
  - `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4.json`
  - `seconds = 28.340`
- 与 `mlx_full` 对照：
  - `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4_vs_mlx.json`
  - `private_ane seconds = 30.186`
  - waveform diff 仍较小

注意：

```text
这个 <=30s 结论当前依赖 warm wrapper-route prototype，
不是“已完全恢复出一个一般化 accepted-state control surface”。
```

## 验收标准 5

要求：

```text
若未达标，必须给出阻塞证据，说明 descriptor 层为何不足，以及下一层需要什么控制能力。
```

当前状态：`额外已满足`

说明：

```text
虽然标准 4 已在 warm wrapper-route 上达标，
但“descriptor 层为何仍不足以恢复一般化 accepted runtime-state control”
这一点也已经有明确 blocker 证据。
```

主要证据：

- [final_blocker_evidence_package_note.md](/Volumes/2T/pymss/mps/ANE/experiments/results/final_blocker_evidence_package_note.md)
- [runtime_lower_next_layer_note.md](/Volumes/2T/pymss/mps/ANE/experiments/results/runtime_lower_next_layer_note.md)
- [legacy_helper_boundary_note.md](/Volumes/2T/pymss/mps/ANE/experiments/results/legacy_helper_boundary_note.md)

当前最明确的下一控制层需求：

- lower firmware request/reply/publish semantics
- lower accepted-state author/replay transitions below current H16-visible text
- 或承认当前 visible control layer 到 accepted-state author 之上为止

## 审计结论

当前最准确的阶段结论是：

```text
1. performance target 已在 warm wrapper-route prototype 上达成
2. descriptor/program-body semantics 已深入到足够强的程度
3. 但一般化 accepted runtime-state author/control layer 仍未恢复
4. blocker 证据已经足够明确，后续工作应聚焦更低 firmware/reply/publish 层，
   或直接基于 blocker package 输出阶段性结论
```
