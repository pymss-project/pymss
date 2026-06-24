# Private ANE Goal

## 主目标

让 `test_clean.m4a` 的推理继续使用 ANE 作为目标执行后端，先尽可能消除 transformer 路径中的 repeated `load/compile` overhead，再解释并降低剩余 transformer runtime / dispatch / transfer 成本；优先寻找可实际落地的 ANE artifact/cache/precompile/static-shape/warm-process 路线，只有在出现新的安全能力时才恢复 private lower-control RE。

当前已完成的 RE 结论是边界条件，不是放弃 ANE：当前 machine-local safe host-visible private route（descriptor / ANEServices / selector / H16-visible send-reply shell）已正式判死，不能从该层根治 repeated `load/compile`。后续不再默认重复 same-layer private probing。

2026-06-23 current plan update: supported same-process repeat-load / precompiled Core ML/ANE artifact probes have also been measured and are not a material load/compile elimination route for the tested transformer and mask packages. The long-term plan therefore remains ANE-first, but the active phase moves to `TransformerRuntime`: explain why transformer time is still high and reduce eval-only, segmentation/dispatch, axis pack/unpack, ANE read/write, handle/free, and fallback/sync costs with reproducible evidence.

## 长期 Loop

### 长期目标

恢复一个可实际使用的 ANE compile/load reuse 路线，并继续压缩剩余 transformer eval/dispatch/transfer 成本；若不能达成，则证明在当前机器和安全约束下没有可达的 ANE-only overhead 根治路径，并最终明确回答：

1. 能否通过 supported ANE artifact/cache/precompile/warm-process 路线真正减少 repeated `load/compile`
2. transformer 剩余耗时到底来自 ANE eval 本身、分段/调度、layout pack/unpack、read/write transfer、handle lifecycle，还是 fallback/CPU 同步
3. 能否通过更少 segment、更稳定 static shape、更大 fused package、更少 transfer/readback、更少 handle churn 继续加速 ANE inference
4. 若 supported route 不足，是否存在新的安全 lower-control 能力可继续 private ANE RE
5. 若仍不能，具体卡死在哪一层：supported ANE cache/artifact 层、transformer execution/dispatch 层、external entitlement 层、还是 firmware-private / IOProcessor writeback 层

### 固定阶段

1. `Baseline`
   - 分离 `test_clean.m4a` 的 compile、load、segment dispatch、eval、transfer、teardown 成本
2. `SupportedANECache`
   - 验证 Core ML / ANE supported artifact、precompile、static-shape、warm-process、model cache 是否能减少 repeated `load/compile`
   - Current measured status: same-process repeat-load and precompiled-artifact probes are falsified as a material fix for the measured transformer and mask packages; revisit only with a new cache key/source-URL/compiler-service hypothesis and a smaller probe.
3. `TransformerRuntime`
   - 解释并优化 transformer eval-only、segment count、axis pack/unpack、ANE read/write、handle/free、fallback/sync 成本；即使 `load/compile` 不能通过 supported cache route 消除，也必须分离这些剩余成本。
4. `PrivateCapabilityGate`
   - 只有出现 firmware-private reply/replay visibility、safe IOProcessor/interrupt completion observation，或 authorized entitlement/signing environment 时，才恢复 private lower-control RE
5. `ExploitOrBlock`
   - 若 supported 或 newly-authorized private route 可控，则做最小 PoC 并复测
   - 若不可控，则输出 blocker package，明确下一控制层需求

### 每轮固定输出

1. 一个唯一假设
2. 一个最小 probe
3. 一个结果 CSV/JSON
4. 一个 `confirmed / falsified / inconclusive` verdict
5. 一个更小的下一轮子目标

## 验收标准

1. 能明确拆分 `test_clean.m4a` 当前 ANE 路径中的 compile、load、segment dispatch、eval、transfer、teardown 成本。
2. 至少确认一组会影响 ANE `segment/cache/load/eval` overhead 的 supported artifact/cache/precompile/static-shape/warm-process 结构或行为。
3. 至少确认 transformer 剩余长耗时的主因类别：eval-only、segment/dispatch、layout pack/unpack、read/write transfer、handle lifecycle、fallback/sync，不能只用 wall time 下结论。
4. 做出最小 PoC，证明修改该层会改变 ANE 运行行为，例如：
   - 更少 `loadModel`
   - 更少 `compileModel`
   - 更稳定 cache hit
   - 更少 transformer 分段
   - 更少 `pre_eval`
   - 更少 axis pack/unpack
   - 更少 ANE read/write
   - 更少 handle/free
5. 使用 `test_clean.m4a` 复测，ANE wall time 相比当前较好结果有明确改进；目标仍为 `<= 30s`。
6. 若未达标，必须给出阻塞证据，说明 supported ANE artifact/cache 或 transformer runtime 层为何不足，以及是否需要新的 firmware-private / IOProcessor / entitlement 能力。

## 非目标

- 不把 MPS/MLX 作为目标后端；它们只能作为 fallback/reference，不替代 ANE 目标。
- 不重复已经判死的 private same-layer 路线：descriptor field guessing、ANEServices selector3/4/6/9 patching、ready-gate spoofing、visible `aneCmdSend` / typed-completion shell probing。
- 不把“逆到 ISA / kernel / scheduler”作为当前完成标准，除非先获得新的安全 lower-control capability。
- 不为了 private ANE 实验把实验性依赖强行写入默认发布路径。
- 不在未有证据时宣称“ANE 已接近 18 TFLOPS 峰值”。

## 统一 benchmark 口径

- 默认验证/benchmark 音频：`test_clean.m4a`
- 长音频扩展验证：`test.m4a`
- 结果至少记录：
  - 命令
  - 输入音频
  - 输出结果文件路径
  - wall time
  - 正确性比较口径
  - 关键 profile / trace 路径
