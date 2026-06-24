# Private ANE Log

## 2026-06-24 08:38 +0800
- Goal:
  restore or explain the accepted full-path auxiliary
  `band_split_l2_fused_0_4` load-cache/materialization route for identifier
  `B44E9E...3287BA`.
- Actions:
  - Delegated code-path lookup to `searcher` and prior evidence lookup to
    `doc-reader`.
  - Inspected exact B44E cache directory under
    `benchmark_results/private_ane/ane_tmp_loadcache/`.
  - Added diagnostic preservation of `load_cache_error_profile` in
    `benchmark/private_ane_real_attention_probe.py`.
  - Reran the q240 full-path precondition probe with explicit load-cache,
    batch4, and relative cache tmpdir.
  - Reran the same probe with absolute cache tmpdir
    `/Volumes/2T/pymss/benchmark_results/private_ane/ane_tmp_loadcache`.
  - Wrote
    `mps/ANE/.ane_runs/json/band_split_b44e_cache_materialization_probe_20260624.json`
    and CSV peer.
- Evidence:
  - Cache directory exists and contains `model.hwx`, `model.mil`,
    `model.client.mil`, `net.plist`, `data`, `model.src`, `model.retain`, and
    `weights/`.
  - `model.mil` SHA-256 matches identifier prefix
    `B44E9E4203023F73CA510E0D86017ABD453DBD65680843296215AF2ADE2EDCB5`.
  - Relative tmpdir load profile:
    `route=load_cache_skip_source_write`, `fast_load_attempted=1`,
    `fast_load_hit=0`, `fast_load_fallback=1`, `load_qos_sec=0.027878875`;
    fallback compile fails `InvalidMILProgram`.
  - Absolute tmpdir load profile:
    `route=load_cache_skip_source_write`, `fast_load_attempted=1`,
    `fast_load_hit=0`, `fast_load_fallback=1`, `load_qos_sec=0.016694167`;
    fallback compile fails `InvalidMILProgram`.
- Conclusion:
  verdict `blocked_band_split_cache_present_but_load_qos_rejects_then_compile_invalid`.
  This is not a missing-cache, wrong-MIL, or relative-path-only problem. The
  compiled artifact is present but rejected by `loadWithQoS`, and fresh compile
  is still invalid.
- Next:
  build or reuse a band-split-only harness for exact B44E MIL/weights and
  output sizes. Attempt load-only first, then a safe same-identifier
  refresh/materialization if possible. Do not copy incompatible artifacts or
  increase retained memory.

## 2026-06-24 08:28 +0800
- Goal:
  use the canonical accepted full-path q240 run to capture
  `ane_pre_native_eval_total_sec` after native eval telemetry was added.
- Actions:
  - Delegated benchmark command discovery to `searcher` and propagation
    confirmation to `explorer`.
  - Confirmed code path: `native_eval_*` fields propagate through
    `_run_block_profiled` into per-layer `transformer_timings` as
    `ane_pre_native_eval_*`; aggregate `transformer_detail` does not yet sum
    them.
  - Ran canonical full-path q240 command without explicit load-cache.
  - Ran full-path q240 command again with explicit `--private-ane-load-cache`
    and `--private-ane-cache-tmpdir benchmark_results/private_ane/ane_tmp_loadcache`.
  - Wrote
    `mps/ANE/.ane_runs/json/full_path_q240_native_eval_capture_blocked_20260624.json`
    and CSV peer.
- Evidence:
  - First child dir:
    `benchmark_results/private_ane/test_clean_full_private_native_eval_profile_q240_20260624.private_ane_child`.
  - Second child dir:
    `benchmark_results/private_ane/test_clean_full_private_native_eval_profile_q240_loadcache_20260624.private_ane_child`.
  - Both runs failed before transformer at `band_split_l2_fused_0_4` with
    `InvalidMILProgram` for identifier
    `B44E9E4203023F73CA510E0D86017ABD453DBD65680843296215AF2ADE2EDCB5_6A52E18B7A88B752DD6AC04AC4348A1D14976077C89669F9C2891772FF3287BA_E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`.
  - Both failures reported route `compile`, `fast_load_attempted=0`; the
    second run's trace confirms STFT load-cache worked, but band split still
    did not use a loadable route.
- Conclusion:
  verdict `blocked_full_path_q240_native_eval_capture_by_band_split_compile`.
  Native q240 eval capture is currently blocked by a non-transformer auxiliary
  band-split compile/materialization precondition, not by the eval telemetry
  itself.
- Next:
  inspect and restore/explain the exact `B44E9E...3287BA` band-split
  cache/materialization route. Do not repeat q240 native eval capture until
  this precondition is satisfied or a different accepted full-path seam reaches
  transformer.

## 2026-06-24 08:13 +0800
- Goal:
  split accepted exact q240 `attention_pre` `ane_pre_eval` below the Python
  eval bucket without increasing retained memory.
- Actions:
  - Added native eval telemetry in
    `mps/maderix_ANE/bridge/ane_bridge.m`: `ane_bridge_eval` now stores
    `eval_total_sec`, `eval_client_sec`, `eval_direct_process_sec`, and
    `eval_model_sec` into `g_last_profile_json`.
  - Updated `benchmark/private_ane_real_attention_probe.py` so eval paths
    refresh `last_bridge_profile`, attach numeric native eval fields to timing
    dictionaries, and include `bridge_profile` JSON in eval failures.
  - Rebuilt `mps/maderix_ANE/bridge/libane_bridge.dylib` with
    `make -C mps/maderix_ANE/bridge`.
  - Ran the minimal exact q240 layerwise probe and one tiny eval smoke.
  - Wrote
    `mps/ANE/.ane_runs/json/accepted_q240_eval_native_profile_probe_20260624.json`
    and CSV peer.
- Evidence:
  - Exact q240 layerwise command failed before eval with
    `InvalidMILProgram` for identifier
    `CFEEBA68A0867D458FFA754FC3777ECDCE97C7AB6DD42ABE81D759AD310D59C6_F88156576125F4F2458BEBCC36F5BEFAB235C4F43F46BA3EAEA629FAD5C6051D_E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`;
    no layerwise output JSON was written.
  - Tiny eval smoke command
    `/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_real_attention_probe.py --axis freq --batch 1 --seq 8`
    reached eval and failed with profile
    `route=eval_model`, `eval_total_sec=0.000174542`,
    `eval_model_sec=0.000174542`.
  - JSON/CSV validation passed for
    `accepted_q240_eval_native_profile_probe_20260624`.
- Conclusion:
  verdict `confirmed_native_eval_profile_instrumentation_but_exact_q240_blocked_before_eval`.
  Native eval timing is now observable, but the current exact q240 layerwise
  seam cannot split `ane_pre_eval` because it fails before handle creation.
- Next:
  use an already accepted full-path q240 handle context to capture
  `ane_pre_native_eval_total_sec`, or continue exact q240 `model.hwx`
  materialization/reuse. Do not repeat the compile-failing layerwise seam until
  a loadable exact q240 artifact exists.

## 2026-06-24 07:52 +0800
- Goal:
  identify the next memory-neutral `attention_pre` route candidate after exact
  q240 `ValidateEntry` capture was blocked behind `ANECompilerService.xpc`.
- Actions:
  - Used `diagnosing-bugs` for the performance/root-cause loop and
    `reverse-engineering` as the evidence-boundary checklist.
  - Delegated long-doc recovery to `doc-reader`, code/artifact location to
    `searcher`, and `attention_pre` variant/code-path exploration to
    `explorer`.
  - Inventoried existing compiler-accepted or previously-tested
    `attention_pre` candidates from prior JSON artifacts without rerunning full
    audio.
  - Wrote
    `mps/ANE/.ane_runs/json/attention_pre_memory_neutral_candidate_inventory_20260624.json`
    and CSV peer.
- Evidence:
  - Current accepted full-path baseline remains
    `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_20260623.private_ane_child/meta.json`
    with `27.903367s`, `RTF 0.704808`.
  - `integrated_vs_standalone_attention_pre_q240_20260624.json` confirms
    byte-identical standalone/integrated q240 MIL for the target shape; the
    standalone fast-load seam is faster for one layer, but the accepted
    integrated path still uses `load_cache_skip_source_write`.
  - `integrated_q240_cache_artifact_inspection_20260624.json` confirms the
    exact q240 cache is source-only and lacks `model.hwx`.
  - `q240_same_identifier_compiled_artifact_search_20260624.json` confirms
    same-weight alias compiled artifacts have different MIL hashes and must not
    be copied into the exact q240 cache.
  - `time_attention_pre_route_candidate_audit_20260623.json` and
    `time_attention_pre_graph_layout_candidate_audit_20260623.json` close
    alternative q-chunks and host-visible graph/layout variants for this loop.
- Conclusion:
  `blocked_no_memory_neutral_compiling_candidate`. Accepted exact q240 remains
  the opt-in baseline, but no newly promotable candidate satisfies all gates:
  compiler-accepted/loadable, numerically safe for exact q240, memory-neutral,
  and expected faster.
- Next:
  either find a safe exact-identifier q240 `model.hwx` materialization/reuse
  route without changing MIL identity, or instrument the accepted q240
  `ane_pre_eval` bucket below the current bridge profile to split selector-2
  request/materialization, firmware wait, compute completion, and readback.

## 2026-06-20
- 时间：2026-06-20 03:xx:xx +0800
- 目标：解决最后一个二分：`layer3 time` cached stack 自身是否已足够触发 second-run failure。
- 动作：
  - 运行：
    - `keep_transformer=true`
      `layer3 time`
    - `keep_transformer=false`
      `layer3 time`
  - 两组路径其余条件完全相同，
    只对比 retained transformer handles
    是否存在
- 证据：
  - `benchmark_results/private_ane/multifamily_keep_layers4_stop_time3_20260620.json`
  - `benchmark_results/private_ane/multifamily_nokeep_layers4_stop_time3_20260620.json`
  - `mps/ANE/.ane_runs/json/transformer_reuse_time3_root_verdict_20260620.json`
- 结论：
  - 本轮 verdict=`confirmed`
  - `layer3 time`
    在
    `keep_transformer=true`
    时，
    第二次运行失败，
    并保留：
    `transformer_handles = 15`
  - 完全相同路径在
    `keep_transformer=false`
    时，
    第二次运行恢复成功
  - 因而当前 first failing surface
    已正式落在
    retained
    `layer3 time`
    transformer stack
    本身
- 下一步：
  - 已完成：
    `pre / gate / ffn`
    三分之一的第一步
  - 下一步：
    直接围绕 retained
    `pre`
    handle
    做机制定位，
    不再继续拆
    `gate`
    /
    `ffn`
- 时间：2026-06-20 03:xx:xx +0800
- 目标：把 retained-transformer first failing surface 从“layer2 freq 之后”继续缩到更小的 segment。
- 动作：
  - 运行 keepalive stop 对照：
    - `layer2 freq`
    - `layer3 time`
  - 对比第二次运行是否成功
- 证据：
  - `benchmark_results/private_ane/multifamily_keep_layers4_stop_freq2_20260620.json`
  - `benchmark_results/private_ane/multifamily_keep_layers4_stop_time3_20260620.json`
  - `mps/ANE/.ane_runs/json/transformer_reuse_first_failing_segment_verdict_20260620.json`
- 结论：
  - 本轮 verdict=`confirmed`
  - keepalive 到
    `layer2 freq`
    仍稳定
  - 但推进到
    `layer3 time`
    之后，
    第二次运行就已经失败
  - 因而 first failing segment
    已收窄到：
    `layer3 time`
    或其后续
    `layer3 freq`
- 下一步：
  - 只解决最后一个二分：
    `layer3 time`
    cached stack
    自身是否已足够失败，
    还是必须进入
    `layer3 freq`
    才失败
- 时间：2026-06-20 03:xx:xx +0800
- 目标：把 retained-transformer first failing surface 从“整个 4-layer stack”继续缩到更小边界。
- 动作：
  - 给
    `run_transformers_layerwise_many`
    加入最小 stop 钩子：
    - `private_ane_probe_stop_after_transformer_layer`
    - `private_ane_probe_stop_after_transformer_axis`
  - 通过
    `benchmark/private_ane_multifamily_free_profile_probe.py`
    触发：
    - `stop_after_transformer_layer=1, axis=freq`
    - `stop_after_transformer_layer=2, axis=freq`
  - 与已有 full
    `4-layer keepalive`
    失败结果做夹逼对照
- 证据：
  - `benchmark_results/private_ane/multifamily_keep_layers4_stop_freq1_20260620.json`
  - `benchmark_results/private_ane/multifamily_keep_layers4_stop_freq2_20260620.json`
  - `benchmark_results/private_ane/multifamily_keep_layers_4_20260620.json`
  - `mps/ANE/.ane_runs/json/transformer_reuse_surface_narrowing_verdict_20260620.json`
- 结论：
  - 本轮 verdict=`confirmed`
  - keepalive 在：
    - `layer1 freq`
    - `layer2 freq`
    都仍然稳定
  - 但完整
    `4-layer`
    keepalive
    已失败
  - 因而 first failing surface
    已被收窄到：
    `layer2 freq` 之后，
    也就是下一轮只需检查
    `layer3 time`
    /
    `layer3 freq`
- 下一步：
  - 只做
    `layer3 time`
    和
    `layer3 freq`
    两个 stop 对照，
    不再回头重扫
    layer1/2
- 时间：2026-06-20 02:xx:xx +0800
- 目标：确认 `4-layer + stop_after_transformer` 的 second-run failure 是否需要 retained transformer handles 才会触发。
- 动作：
  - 保持路径完全不变，
    仅切换：
    - `keep_transformer=true`
    - `keep_transformer=false`
  - 运行：
    `benchmark/private_ane_multifamily_free_profile_probe.py --repeats 2 --max-transformer-layers 4 --stop-after-transformer`
  - 对比两组第二次运行是否成功
- 证据：
  - `benchmark_results/private_ane/multifamily_keep_layers4_stop_after_transformer_20260620.json`
  - `benchmark_results/private_ane/multifamily_nokeep_layers4_stop_after_transformer_20260620.json`
  - `mps/ANE/.ane_runs/json/transformer_reuse_root_cause_verdict_20260620.json`
- 结论：
  - 本轮 verdict=`confirmed`
  - `keep_transformer=true`
    时，
    第二次运行失败，
    且
    `transformer_handles = 24`
    保留
  - `keep_transformer=false`
    时，
    完全相同路径的第二次运行恢复成功，
    且
    `transformer_handles = 0`
  - 因而 `4-layer` second-run failure
    已可正式归因到
    retained transformer handle reuse
    本身
- 下一步：
  - 只在 retained transformer cached stack
    内部定位
    first failing surface：
    time axis
    / freq axis
    / combined stack
- 时间：2026-06-20 02:xx:xx +0800
- 目标：判断 `4-layer keepalive` 的 second-run failure 是否依赖后续 `final_norm/mask/irfft` 阶段。
- 动作：
  - 扩展
    `benchmark/private_ane_multifamily_free_profile_probe.py`
    支持：
    - `--stop-after-transformer`
    - `--stop-after-final-norm`
  - 先跑最关键对照：
    `--keep-transformer --max-transformer-layers 4 --repeats 2 --stop-after-transformer`
  - 对比已有
    full narrow path
    的
    `4-layer keepalive`
    结果
- 证据：
  - `benchmark_results/private_ane/multifamily_keep_layers_4_20260620.json`
  - `benchmark_results/private_ane/multifamily_keep_layers4_stop_after_transformer_20260620.json`
  - `mps/ANE/.ane_runs/json/transformer_keepalive_stage_isolation_verdict_20260620.json`
- 结论：
  - 本轮 verdict=`confirmed`
  - 即使把路径收窄到
    transformer 执行后立即停止，
    `4-layer keepalive`
    第二次运行仍然失败，
    错误同样是：
    `RuntimeError('ANE eval failed')`
  - 因而这个 failure
    不依赖后续
    `final_norm/mask/irfft`
    阶段
  - 当前 first failing surface
    已收窄到：
    retained transformer eval
    本身
    或其紧邻前置
    stft/map setup
- 下一步：
  - 只围绕 retained transformer eval
    本身做 first failing surface
    定位，
    不再把怀疑面放在后续
    aux / irfft
    阶段
- 时间：2026-06-20 02:xx:xx +0800
- 目标：从已证实可行的 keepalive 窄路径往真实路径推，找出 first run-to-run failure boundary。
- 动作：
  - 给
    `benchmark/private_ane_multifamily_free_profile_probe.py`
    增加：
    - `--max-transformer-layers`
    - `--repeats`
    - `--keep-transformer`
  - 跑 keepalive sweep：
    - 1 layer
    - 2 layers
    - 4 layers
  - 逐组记录：
    - 第二次 run 是否成功
    - `transformer_handles` 是否保留
    - 错误类型
- 证据：
  - `benchmark_results/private_ane/multifamily_keep_layers_1_20260620.json`
  - `benchmark_results/private_ane/multifamily_keep_layers_2_20260620.json`
  - `benchmark_results/private_ane/multifamily_keep_layers_4_20260620.json`
  - `mps/ANE/.ane_runs/json/transformer_keepalive_layer_boundary_verdict_20260620.json`
- 结论：
  - 本轮 verdict=`confirmed`
  - `keep_transformer=true`
    在：
    - 1 layer
    - 2 layers
    上都能稳定跑两次
  - 到 4 layers
    时：
    - run0 成功
    - run1 失败
    - 错误：
      `RuntimeError('ANE eval failed')`
    - 并且仍保留：
      `transformer_handles = 24`
  - 当前 first confirmed keepalive failure boundary
    已明确落在
    `4 transformer layers`
- 下一步：
  - 只解释这个 4-layer boundary：
    是 retained transformer state
    自身导致
    second-run eval failure，
    还是与
    stft/irfft/aux
    的阶段交互导致
- 时间：2026-06-20 02:xx:xx +0800
- 目标：直接验证 transformer keep-alive 是否能去掉 repeated transformer free，并观察同进程第二次运行是否立刻撞回旧污染边界。
- 动作：
  - 扩展
    `benchmark/private_ane_multifamily_free_profile_probe.py`
    支持：
    - `--repeats`
    - `--keep-transformer`
    - 对每次 run 记录：
      `ok/error`
      `seconds`
      `free_profile_by_family`
      `final_cache_handles`
  - 模型开关：
    - `private_ane_cache_transformers=True`
    - `private_ane_allow_transformer_handle_cache=True`
    - `private_ane_transformer_cache_segments=999`
    - `private_ane_persistent_transformer_handles=True`
  - 先跑 baseline：
    `keep_transformer=false`
    `repeats=2`
  - 再跑 keepalive：
    `keep_transformer=true`
    `repeats=2`
  - 同时保留两份 bridge free trace：
    - `ane_bridge_free_trace_repeat_free_20260620.jsonl`
    - `ane_bridge_free_trace_repeat_keep_20260620.jsonl`
- 证据：
  - `benchmark_results/private_ane/multifamily_free_profile_repeat_free_20260620.json`
  - `benchmark_results/private_ane/multifamily_free_profile_repeat_keep_20260620.json`
  - `mps/ANE/.ane_runs/logs/ane_bridge_free_trace_repeat_free_20260620.jsonl`
  - `mps/ANE/.ane_runs/logs/ane_bridge_free_trace_repeat_keep_20260620.jsonl`
  - `mps/ANE/.ane_runs/json/transformer_keepalive_probe_verdict_20260620.json`
- 结论：
  - 本轮 verdict=`confirmed`
  - baseline 组：
    transformer free
    仍然发生，
    第二次 run 成功，
    但没有任何 transformer handle 留存
  - keepalive 组：
    transformer free
    已从
    `free_profile_by_family`
    和 bridge trace
    中消失，
    且两次 run
    都成功；
    两次之后
    `transformer_handles = 6`
    仍保留
  - 第二次 keepalive run
    比 baseline 第二次 run
    更快，
    当前窄路径下
    没有立即复现
    `0x12`
    旧污染边界
- 下一步：
  - 从这个窄路径向真实路径推进：
    先增加 transformer layers，
    再逐步引回 full private-ANE band-split，
    记录第一次重新出现
    lower-state corruption
    的边界
- 时间：2026-06-20 02:xx:xx +0800
- 目标：在 family-labeled free instrumentation 已被 direct multi-family probe 验证后，进一步判断 full private-ANE path 的 dominant repeated free/unload 到底是谁。
- 动作：
  - 直接对照：
    - `benchmark_results/private_ane/multifamily_free_profile_probe_20260620.json`
    - `mps/ANE/.ane_runs/logs/ane_bridge_free_trace_multifamily_20260620.jsonl`
    - `benchmark_results/private_ane/mask_batch_detail_smoke_1s.json`
    - `benchmark_results/private_ane/test_clean_full_private_default_auto_batch4_after_batch_axis_code_profile.json`
  - 额外提取 full path
    `transformer_timings[*].handle_free_sec`
    的 time/freq 总和，
    避免把“visible cache_release 主角”
    误当成“total free-time 主角”
- 证据：
  - full path visible cache-release：
    - `stft_cache_release`:
      17 handles,
      `~0.0466s`
    - `irfft_cache_release`:
      16 handles,
      `~0.0544s`
  - full path transformer runtime free：
    - time axis total:
      `~0.418s`
    - freq axis total:
      `~0.151s`
    - total:
      `~0.569s`
  - direct probe 已证明 family-labeled trace
    在 transformer / aux_final_norm / aux_mask / irfft / stft
    上都能落盘
- 结论：
  - 本轮 verdict=`confirmed`
  - 当前必须分清两个口径：
    1. visible cache-release 主角：
       `irfft/stft`
    2. total repeated free-time 主角：
       transformer family
  - 对 single-process reuse
    真正更关键的是第 2 条，
    因为它对应 full path 中运行期重复 tear-down 的总时间
- 下一步：
  - 直接面向 transformer family
    做 single-process reuse：
    验证是否能在不重新引入 lower-state corruption 的前提下，
    把这 `~0.57s`
    的 repeated transformer free
    去掉或显著压缩
- 时间：2026-06-20 01:xx:xx +0800
- 目标：在 full benchmark entry 一直被 `compressor_memory` / `band_split InvalidMILProgram` 阻塞的情况下，证明 family-labeled free instrumentation 能在一个真实 multi-family private-ANE path 上跑通。
- 动作：
  - 根据 `explorer` 子代理给出的路径组合，
    新增
    `benchmark/private_ane_multifamily_free_profile_probe.py`
  - 路径设计：
    - torch band-split
    - ANE STFT
    - ANE transformer
    - ANE final_norm
    - ANE mask
    - ANE IRFFT
  - 先后解决三类非本质阻塞：
    1. preload headroom gate
       -> 对齐 smoke 的 0-floor memory 条件
    2. STFT chunk shape
       -> 手工 zero-pad 到 `(2, 480000)`
    3. wall time 过长
       -> 先收窄到
       `private_ane_max_transformer_layers=1`
  - 补齐 `clear_*_cache()` 对
    `free_profile_by_family`
    的统计，
    让
    `aux_*` / `irfft_cache` / `stft_cache`
    也进入 summary
  - 执行：
    `ANE_BRIDGE_FREE_TRACE=1 ANE_BRIDGE_FREE_TRACE_FILE=/tmp/ane_bridge_free_trace_multifamily.jsonl python benchmark/private_ane_multifamily_free_profile_probe.py --audio test_clean.m4a --seconds 1.0 --out benchmark_results/private_ane/multifamily_free_profile_probe_20260620.json`
- 证据：
  - `benchmark_results/private_ane/multifamily_free_profile_probe_20260620.json`
  - `mps/ANE/.ane_runs/logs/ane_bridge_free_trace_multifamily_20260620.jsonl`
  - `mps/ANE/.ane_runs/json/multifamily_free_profile_probe_verdict_20260620.json`
- 结论：
  - 本轮 verdict=`confirmed`
  - family-labeled free instrumentation
    已经不再只是“代码接通”，
    而是在 real multi-family private-ANE path
    上真实工作
  - 当前最小已证实 free profile：
    - `transformer_time`: 3 handles
    - `transformer_freq`: 3 handles
    - `aux_final_norm_cache`: 1 handle
    - `aux_mask_cache`: 10 handles
    - `irfft_cache`: 16 handles
    - `stft_cache`: 1 handle
  - 当前桥层 free trace label 分布：
    - `transformer_time`: 6 events
    - `transformer_freq`: 6 events
    - `aux_final_norm_cache`: 2 events
    - `aux_mask_cache`: 20 events
    - `irfft_cache`: 32 events
    - `stft_cache`: 2 events
- 下一步：
  - 只把这套 family-level 剖面拿去和 full private-ANE path 对照，
    识别 single-process reuse 的 dominant repeated unload
    到底是 transformer family
    还是 aux / irfft churn
- 时间：2026-06-20 01:xx:xx +0800
- 目标：把 free/unload instrumentation 从“只能看到 bridge 边界”推进到“真实多-handle private-ANE path 上按 family 归因 free 成本”。
- 动作：
  - 并行派发：
    - `searcher` 确认现有 `_profile_free_handle/_profile_free_handles` 与 cache clear 路径、调用点和 family 分类
    - `explorer` 梳理真实 benchmark path 里 STFT / IRFFT / transformer / aux families 的创建与释放入口
  - 代码侧最小打通 family label：
    - `mps/maderix_ANE/bridge/ane_bridge.h`
      新增
      `ane_bridge_set_free_trace_label(const char *)`
    - `mps/maderix_ANE/bridge/ane_bridge.m`
      在 free trace JSONL 中新增
      `label`
      字段
    - `benchmark/private_ane_real_attention_probe.py`
      扩
      `ANEBridge.free(handle, label=None)`
    - `pymss/modules/bs_roformer/private_ane.py`
      给：
      - `transformer_time`
      - `transformer_freq`
      - `band_split(_fused)`
      - `final_norm_*`
      - `mask(_fused)`
      - `stft_cache`
      - `irfft_cache`
      - `aux_*_cache`
      - `transformer_cache`
      等 free path 注入 label；
      同时新增
      `free_profile_by_family`
      聚合
    - `pymss/utils.py`
      将
      `free_profile_by_family`
      暴露进 batch summary
  - 运行两条 real-path 验证：
    1. subprocess child:
       `benchmark/private_ane_test_clean_benchmark.py ... --out benchmark_results/private_ane/test_clean_free_profile_20260620.json`
    2. in-process:
       `benchmark/private_ane_test_clean_benchmark.py ... --private-ane-in-process --private-ane-allow-in-process --out benchmark_results/private_ane/test_clean_free_profile_inproc_20260620.json`
- 证据：
  - `mps/ANE/.ane_runs/json/free_profile_family_wiring_verdict_20260620.json`
  - `benchmark_results/private_ane/test_clean_free_profile_20260620.private_ane_child/parent_watchdog_failure.json`
  - in-process stderr:
    `band_split_l2_0`
    /
    `band_split_l2_fused_0_4`
    `InvalidMILProgram`
- 结论：
  - 本轮 verdict=`inconclusive`
  - 不是 instrumentation 没接通：
    code path 已经把 family label 传到 bridge free trace，
    也把 `free_profile_by_family` 暴露到 summary
  - 当前真正未解的是
    real benchmark entry
    的运行时条件：
    - child route
      在业务执行前
      被
      `compressor_memory`
      kill
    - in-process route
      进入真实 path
      但在
      band-split compile
      上卡到
      `InvalidMILProgram`
- 下一步：
  - 只找一个最小已知可运行的
    real private-ANE path，
    让
    `free_profile_by_family`
    与带 label 的 bridge free trace
    真正落盘；
    如果当前 benchmark driver
    继续被 band-split compile 卡住，
    就收窄成 direct multi-family driver
- 时间：2026-06-20 01:xx:xx +0800
- 目标：在 `mach_msg probe v2` 已被 dedicated micro-harness 正式判成不匹配 unload/free family 后，选择并验证一个新的 lower-side observability 主线。
- 动作：
  - 用 `diagnosing-bugs` 的 Phase 1 思路，把这一轮的反馈回路固定成：
    `ANE_BRIDGE_FREE_TRACE=1 ANE_BRIDGE_FREE_TRACE_FILE=/tmp/ane_bridge_free_trace.jsonl python -m benchmark.private_ane_free_unload_micro_probe --mode compile_only --out mps/ANE/.ane_runs/json/free_unload_bridge_probe_runtime_20260620.json`
  - 并行派发 sub-agent：
    - `explorer` 只读比较
      `ane_ioconnect_trace_interpose.c`
      与
      `mps/maderix_ANE/bridge/ane_bridge.m`
      的可插桩面；
      结论是当前应优先走
      `ane_bridge_free`
      而不是继续扩 IOKit interposer
  - 主线程在
    `mps/maderix_ANE/bridge/ane_bridge.m`
    的
    `ane_bridge_free`
    上新增最小 JSONL trace：
    - `ANE_BRIDGE_FREE_TRACE`
    - `ANE_BRIDGE_FREE_TRACE_FILE`
    - `before_unload`
    - `after_unload`
    - 记录
      `model_state/program_handle/intermediate_buffer_handle/queue_depth`
      与
      `unload_ok/error`
  - 重编：
    `make -C mps/maderix_ANE/bridge`
  - 运行 dedicated micro-harness 验证新 trace
  - 将结果固化到：
    - `mps/ANE/.ane_runs/logs/ane_bridge_free_trace_20260620.jsonl`
    - `mps/ANE/.ane_runs/json/free_unload_bridge_observability_verdict_20260620.json`
- 证据：
  - `mps/ANE/.ane_runs/json/free_unload_bridge_probe_runtime_20260620.json`
  - `mps/ANE/.ane_runs/logs/ane_bridge_free_trace_20260620.jsonl`
  - `mps/ANE/.ane_runs/json/free_unload_bridge_observability_verdict_20260620.json`
  - `explorer` 子代理结论：
    IOKit interposer 目前仍缺 selector 语义映射与 free/unload payload 布局，
    而 bridge 层已有完整的
    `ANEBridge.free -> ane_bridge_free -> unloadModel/unloadWithQoS`
    调用链
- 结论：
  - 本轮 verdict=`confirmed`
  - 既然 dedicated micro-harness 下
    `mach_msg probe v2`
    仍只有表头，
    而 bridge 层 trace 已能稳定给出
    `before_unload/after_unload`
    两条事件、
    `unload_ok=1`
    与
    `~6ms`
    级别 unload 耗时，
    当前 lower-side unload/free 主线应正式切到 bridge-layer instrumentation
- 下一步：
  - 只把
    `ANE_BRIDGE_FREE_TRACE`
    挂到一个真实多 handle benchmark 路径上，
    量化各 handle family 的
    free/unload
    频率和累计成本；
    不再回头优化
    `mach_msg runtime target`

## 2026-06-12
- 时间：2026-06-12 22:53:25 +0800
- 目标：确认 `_ANEModelToken` 到 selector-3 / direct create 的真实边界，判断 token identity 是否仍是 create-side 主阻塞。
- 动作：
  - 用 `ida-pro-mcp` 继续分析：
    - `appleane_bin`:
      - `+[_ANEModelToken tokenWithAuditToken:modelIdentifier:processIdentifier:]`
      - `-[_ANEModelToken initWithAuditToken:modelIdentifier:processIdentifier:]`
      - `-[_ANEModelToken initWithCsIdentity:teamIdentity:modelIdentifier:processIdentifier:]`
    - `aned_bin`:
      - `-[_ANEServer loadModel:sandboxExtension:options:qos:withReply:]`
      - `-[_ANEProgramForLoad createProgramInstanceForModel:...error:]`
      - 其 `dispatch_sync` block `sub_10000307F`
      - `+[_ANEStorageHelper memoryMapModelAtPath:isPrecompiled:modelAttributes:]`
  - 静态确认：
    - `loadModel...` 中 `modelIdentifier` 来自 `modelURL.path` 最后两级路径，
      然后才进入
      `_ANEModelToken tokenWithAuditToken:modelIdentifier:processIdentifier:`
    - `sub_10000307F` 里，
      `modelToken.modelIdentifier` 只可见地用于
      `csIdentity.processIdentifier.modelIdentifier` 这条
      `os_transaction_create(...)` 名字；
      visible lower request body 仍是：
      - model bytes/len
      - model path
      - team SHA
      - cs SHA
      - `modelIdentityStr`
      - `cacheUrlIdentifier`
      - `aotCacheUrlIdentifier`
      - qos/power/stats/keepWired
    - `memoryMapModelAtPath:isPrecompiled:modelAttributes:` 当前只做：
      - open / mmap 单文件
      - `ANECCreateModelDictionary`
      - access-time update
      没看到它主动拉 `.retain/.src` 之类 companion。
  - 修改并编译：
    - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
      - 新增 request 级 `team_sha_* / cs_sha_*` 摘要输出
    - `clang -fobjc-arc -framework Foundation -o /tmp/ane_services_program_create_runtime_probe ...`
  - 顺序运行两组 selector-3 对照：
    - zero token SHA:
      - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v15_zero_token_sha.json`
    - fake non-zero token SHA:
      - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v16_fake_token_sha.json`
  - 新增结果 note：
    - `mps/ANE/experiments/results/modeltoken_selector3_boundary_note.md`
- 证据：
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v15_zero_token_sha.json`
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v16_fake_token_sha.json`
  - `mps/ANE/experiments/results/modeltoken_selector3_boundary_note.md`
  - `appleane_bin` / `aned_bin` 上述函数的 `ida-pro-mcp` 反编译与反汇编
- 结论：
  - `modelToken.modelIdentifier` 的语义现在已经被解释清楚：
    - 它是 daemon userland 从 `modelURL.path` 最后两级拼出来的字符串。
  - 当前 `sub_10000307F` 里它只影响 transaction/debug identity，
    不是 visible selector-3 request 的关键字段。
  - selector-3 request 里可见的 `team/cs SHA` 已明确存在，但把它们从全零改成
    固定伪造非零值后，四个 local create case 仍全部：
    - `status=0x00000000`
    - `prepare1=0x00000014`
    - `prepare1_owner0_ready1=0x00000002`
    - `raw_prepare=0xe00002c1`
  - 因而当前主阻塞不再适合建模为 token identity / token SHA author 错误；
    更像是：
    - `create success -> wrapper adoption`
    - `prepare-state gate`
    - `success-side lower writeback`
  - 下一步：
  - 不再主要扫 `modelIdentifier` / token SHA。
  - 直接沿 `ANEServicesProgramPrepare` / raw prepare 成功侧追：
    - wrapper `+0x70/+0x98/+0xa8`
    - payload `+0xd78..+0xda8`
    的 success-side materialization。

## 2026-06-18
- 时间：2026-06-18 02:11:42 +0800
- 目标：确认 second fresh wrapper 的 `0x12` 是否由 `eval` 触发，而不是 `map/unmap` 或 wrapper identity 本身。
- 动作：
  - 扩展 `mps/ANE/experiments/ane_runtime_rehydrate_probe.m`
    - 记录 `sharedConnection` / `descriptor.hexStringIdentifier` / `descriptor.hash`
    - 记录 `program` / `controller` / `controller.device` 的 raw memory
    - 新增 `two_wrapper_identity_combo`
    - 新增 `two_wrapper_after_map_only`
    - 新增 `two_wrapper_after_map_eval`
    - 新增 `two_wrapper_txn_after_eval`
  - 用 `ida-pro-mcp` 反编译：
    - `-[_ANEInMemoryModel mapIOSurfacesWithRequest:cacheInference:error:]`
    - `-[_ANEInMemoryModel evaluateWithQoS:options:request:error:]`
    - `-[_ANEProgramIOSurfacesMapper mapIOSurfacesWithModel:request:cacheInference:error:]`
    - `-[_ANEProgramForEvaluation processRequest:model:qos:qIndex:modelStringID:options:returnValue:error:]`
    - `___100-[_ANEProgramForEvaluation processRequest:model:qos:qIndex:modelStringID:options:returnValue:error:]_block_invoke`
  - 跑 probe：
    - `mps/ANE/.ane_runs/csv/two_wrapper_identity_combo.csv`
    - `mps/ANE/.ane_runs/csv/two_wrapper_after_map_only.csv`
    - `mps/ANE/.ane_runs/csv/two_wrapper_after_map_eval.csv`
    - `mps/ANE/.ane_runs/csv/two_wrapper_txn_after_eval.csv`
- 证据：
  - `two_wrapper_identity_combo`：
    wrapper1 只做 `map/unmap` 时，wrapper2 first map 成功
  - `two_wrapper_after_map_only`：
    复现 `map/unmap` 不污染后续 fresh wrapper
  - `two_wrapper_after_map_eval`：
    wrapper1 成功 `eval` 后，wrapper2 first map 稳定 `0x12`
  - `two_wrapper_txn_after_eval`：
    wrapper1 先以 `cacheInference=1` 成功 map，拿到 `transactionHandle=0`，
    随后成功 `eval`；wrapper2 带 txn 再 map 仍然 `0x12`
  - raw memory snapshot：
    `sharedConnection` / `program` / `controller` / `controller.device`
    在 wrapper1 eval 前后及 wrapper2 pre-map 之间没有可见变化
- 结论：
  - 这轮实验把边界进一步收紧到：
    - 不是 second fresh wrapper 天生失败
    - 不是 wrapper identity 单字段
    - 不是 `map/unmap` 污染
    - 是一次成功 `eval` 之后，后续 fresh wrapper 的 map 路径进入
      `0x12`
  - 当前更强假设是：
    - `evaluateWithModel` / `processRequest` 触发了 lower eval-side accepted-state
      或 process-global runtime table 污染
    - 污染点不在当前 probe 可见的对象图 raw memory 中
- 下一步：
  - 转静态追 `evaluateWithModel` / `processRequest` 的 lower writeback 路
  - 查成功 eval 后到底哪层 runtime table 影响后续 map
  - 不再继续扩 wrapper identity / descriptor 变体

- 时间：2026-06-18 04:51:35 +0800
- 目标：确认 eval 是否必须依赖前置 map，还是单独一次成功 eval 就足以污染后续 fresh wrapper。
- 动作：
  - 新增 `two_wrapper_after_eval_only`
    - wrapper1 不做显式 `map/unmap`
    - 只做一次成功 `eval`
    - wrapper2 first map 再测
  - 重开 `appleneuralengine_arm64e` IDA 会话，准备继续追 `evaluateWithModel` 下游
- 证据：
  - `mps/ANE/.ane_runs/csv/two_wrapper_after_eval_only.csv`
- 结论：
  - `wrapper1` 只做一次成功 `eval`，不先显式 `map/unmap`，
    wrapper2 first map 仍然稳定 `0x12`
  - 因而污染不依赖前置 map；`eval` 本身已经足够 author 这个 lower state
- 下一步：
  - 直接追 `evaluateWithModel` / `processRequest` 的 lower writeback / accepted-state

- 时间：2026-06-18 11:25:55 +0800
- 目标：确认 eval 污染是否会反映到 visible request-lowering / prepare params。
- 动作：
  - 把 `ane_runtime_rehydrate_probe.m` 的 lowering snapshot 扩到全部 `two_wrapper_*` case
  - 重跑：
    - `two_wrapper_after_eval_only`
    - `two_wrapper_after_map_eval`
    - `two_wrapper_txn_after_eval`
  - 用 IDA 继续静态读：
    - `-[_ANEClient doEvaluateDirectWithModel:options:request:qos:error:]`
    - `-[_ANEClient connectionUsedForLoadingModel:]`
    - `___44-[_ANEClient connectionUsedForLoadingModel:]_block_invoke`
- 证据：
  - 3 个 CSV 中：
    - `request.signature_hash`
    - `prepareANEMemoryMappingParams summary`
    - `tailQ0/tailU32_0/tailU32_1/tailQ1`
    在 eval 前后都没有变化
  - `doEvaluateDirectWithModel...` 静态确认：
    - public `evaluateWithModel...` 只是 thunk
    - 真正路径是 `_ANEClient doEvaluateDirectWithModel...`
      -> `program processRequest...`
    - 超时与同步失败会走 `reportEvaluateFailure`，但这次是成功 eval 污染，不在这条失败上报里
- 结论：
  - eval 污染没有体现在 visible request-lowering / prepare params 上
  - 当前主怀疑继续下压到 `doEvaluateDirectWithModel...` /
    `processRequest` 成功侧的 lower runtime side effect
- 下一步：
  - 继续 reverse `doEvaluateDirectWithModel...` 里的 semaphore / completion /
    `emitEndTracepoint` / driver request completion 路

- 时间：2026-06-18 11:25:55 +0800
- 目标：确认 eval 污染是不是 same-wrapper 也成立，以及它是否只是缺少手工 txn0。
- 动作：
  - 新增并运行：
    - `same_wrapper_after_eval_map`
    - `two_wrapper_after_eval_only_txn0`
  - 静态继续 reverse：
    - `_ANEDeviceController start`
    - `___83-[_ANEProgramIOSurfacesMapper mapIOSurfacesWithModel:request:cacheInference:error:]_block_invoke`
    - `device` 间接调用位置
- 证据：
  - `mps/ANE/.ane_runs/csv/same_wrapper_after_eval_map.csv`
  - `mps/ANE/.ane_runs/csv/two_wrapper_after_eval_only_txn0.csv`
  - IDA:
    - `__29-[_ANEDeviceController start]_block_invoke`
    - `___83-[_ANEProgramIOSurfacesMapper mapIOSurfacesWithModel:request:cacheInference:error:]_block_invoke`
- 结论：
  - 同一个 wrapper 成功 `eval` 后，自己再 `map` 也会直接 `0x12`
  - eval-only 污染后，给后续 map 人工塞 `transactionHandle=0` 也没用
  - `_ANEDeviceController start` 通过 `ANEServicesDeviceOpen` 打开底层 device
  - `map` 明确走 `device->vtable[0x38]`
  - 当前更强假设是：
    eval 走的 device driver-request 槽位 author 了某个 lower runtime state，
    随后 map 槽位返回 `0x12`
- 下一步：
  - 继续把 eval 那个 device 间接调用槽位解出来，确认与 map 槽位的关系

- 时间：2026-06-18 12:08:07 +0800
- 目标：把 `map` / `eval` 在 ANEServices device 层对应到具体 IOKit 通道。
- 动作：
  - 打开 `ANEServices.framework` IDA 会话
  - 反编译：
    - `ANE::ANEServicesDevice::ANE_ProgramMemoryMapRequest(...)`
    - `ANE::ANEServicesDevice::ANE_ProgramMemoryUnMapRequest(...)`
    - `ANE::ANEServicesDevice::ANE_ProgramSendRequest(...)`
    - `ANE::ANERequestReceiver::ProgramProcessRequest(...)`
    - `ANE::ANERequestReceiver::syncFrameDone(...)`
- 证据：
  - `ANE_ProgramMemoryMapRequest`
    -> `IOConnectCallMethod(selector=5)`
  - `ANE_ProgramMemoryUnMapRequest`
    -> `IOConnectCallStructMethod(selector=6)`
  - `ANE_ProgramSendRequest`
    -> `IOConnectCallAsyncMethod(selector=2)`
  - `ProgramProcessRequest` 在 sync 路上直接调用 `ANE_ProgramSendRequest`
  - `syncFrameDone` 会消费 `reqCb` 里的
    `transid / programHandle / status`
- 结论：
  - AppleNeuralEngine 侧看到的
    `map device->vtable[0x38]`
    和
    `eval device->vtable[0x20]`
    已能分别对上 ANEServices 的
    `MemoryMapRequest` 与 `ProgramSendRequest`
  - 现在最值得继续下钻的是
    `ProgramProcessRequest -> syncFrameDone`
    的成功侧 callback / transid / status writeback
- 下一步：
  - 继续追 `syncFrameDone` 和 request callback data

- 时间：2026-06-18 12:08:07 +0800
- 目标：确认 `ProgramProcessRequest(sync)` 成功侧有没有显式清理 lower state，以及软件侧是否存在现成“清场”入口。
- 动作：
  - 反编译：
    - `ANE::ANERequestReceiver::ProgramProcessRequest(...)`
    - `ANE::ANERequestReceiver::syncFrameDone(...)`
    - `ANE::ANEServicesDevice::ANE_CancelAllRequests()`
  - 跑 probe：
    - `same_wrapper_after_eval_map_cache1`
    - `two_wrapper_after_eval_request_txn0`
- 证据：
  - `same_wrapper_after_eval_map_cache1`：
    成功 `eval` 后，同 wrapper 连 `cacheInference=1` 的初始 map 也直接 `0x12`
  - `two_wrapper_after_eval_request_txn0`：
    把 eval 请求本身的 `transactionHandle` 设成 `0`，污染仍然存在
  - `syncFrameDone(...)` 当前可见写回主要是 request-local / receiver-local
    状态与 callback
  - `ANE_CancelAllRequests()` 当前是 stub，直接 `return 0`
- 结论：
  - 污染不只是普通 map 路径，连 eval 后的 `cacheInference=1` 初始 map 也会一起失败
  - 污染也不依赖 eval 请求的 txn nil/0 差异
  - 用户态目前没有现成可用的 clear/reset 入口
- 下一步：
  - 继续把焦点放在 selector=2 / selector=5 对同一底层 device state 的影响上

- 时间：2026-06-18 12:08:07 +0800
- 目标：确认污染是否只发生在 sync eval 路。
- 动作：
  - 新增并运行 `same_wrapper_after_async_eval_map`
  - 对 request 安装 `completionHandler`
  - 等待 completion 实际回调后，再做同 wrapper `map`
- 证据：
  - `mps/ANE/.ane_runs/csv/same_wrapper_after_async_eval_map.csv`
  - `setCompletionHandler: installed`
  - `completion_wait = signaled`
  - 随后 `map = 0x12`
- 结论：
  - async eval 也会污染后续 map
  - `syncFrameDone` 不是主嫌
  - 当前主嫌继续收紧到 `ANE_ProgramSendRequest` /
    device selector=2 自身或其更低层完成路径
- 下一步：
  - 继续追 selector=2 对底层 runtime state 的影响

- 时间：2026-06-18 12:08:07 +0800
- 目标：确认 public unload/load 能否清掉 eval 后的 map 污染。
- 动作：
  - 新增并运行 `loaded_eval_unload_reload_map`
  - 顺序执行：
    - 成功 `eval`
    - `unloadWithQoS:error:`
    - `loadWithQoS:options:error:`
    - 再 `map`
- 证据：
  - `mps/ANE/.ane_runs/csv/loaded_eval_unload_reload_map.csv`
  - `eval = 1`
  - `unload = 1`
  - `reload = 1`
  - 随后 `map = 0x12`
- 结论：
  - public unload/load 不能清掉污染
  - 当前更像 process-global / device-global runtime state，而不是单个 in-memory model 生命周期问题
- 下一步：
  - 继续围绕 selector=2 / selector=5 的底层共享状态追

- 时间：2026-06-12 23:00:00 +0800
- 目标：确认 selector-4 / prepare 阶段是否已经比 wrapper 可见字段更深，判断 `0x14/0x02` 是否还能靠 visible handle/queueDepth 修补推进。
- 动作：
  - 新开并使用 `ida-pro-mcp` 的 `aneservices_bin` 会话，继续分析：
    - `_ANEServicesProgramCreate`
    - `_ANEServicesProgramPrepare`
    - `__ZN3ANE17ANEServicesDevice18ANE_ProgramPrepareEP21ANEProgramPrepareArgs`
    - `_ANEServicesProgramDestroy`
  - 静态确认：
    - create success-side：
      - `payload+0xda8 <- create_output.qword0`
      - `wrapper+0x70 <- payload+0xda8`
      - `wrapper+0xa8 <- payload queue-depth family`
      - `payload+0xde0 <- 4`
      - `payload+0xde4 <- statsMask`
    - prepare success-side：
      - `wrapper+0x98 <- returned_qword`
      - `payload+0xd98 <- 0`
      - `payload+0xd78..0xd97 <- incoming prepare-args shadow`
      - `payload+0xde0 <- normalized state`
      - `payload+0xde4 <- prepareArgs[2]`
    - destroy 前置 gate 直接依赖：
      - `payload+0xd98`
      - `payload+0xda8`
  - 读取并对照现有 probe：
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v16_fake_token_sha.json`
    - 重点抽取：
      - `raw_prepare_status_hex`
      - `raw_prepare_owner0_ready1_status_hex`
      - `raw_prepare_owner0_ready1_handlepatch_status_hex`
      - `raw_prepare_livehandle_status_hex`
      - wrapper/payload snapshots
  - 新增结果 note：
    - `mps/ANE/experiments/results/selector4_prepare_state_boundary_note.md`
- 证据：
  - `mps/ANE/experiments/results/selector4_prepare_state_boundary_note.md`
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v16_fake_token_sha.json`
  - `aneservices_bin` 上述 4 个函数的 `ida-pro-mcp` 静态结果
- 结论：
  - `prepare` 不是次要包装步骤，而是 first visible writer：
    - `wrapper+0x98`
    - `payload+0xd78..0xd98`
  - 但 runtime 对照已证明：
    - base raw prepare: `0xe00002c1`
    - `owner0+ready1`: `0xe00002c2`
    - `owner0+ready1+handlepatch`: 仍 `0xe00002c2`
    - `raw_prepare_livehandle`: 仍 `0xe00002c2`
  - 这说明当前缺口已经不是：
    - token identity
    - `wrapper+0x70`
    - `payload+0xda8`
    - `wrapper+0xa8`
    - wrapper-visible `prepareArgs`
  - 当前最强边界是：
    - selector-4 / device-side accepted state
    - 它比当前 visible handle/queue-depth patch family 更深
- 下一步：
  - 把 `raw prepare 0xe00002c2` 与 bootkc：
    - `ProgramLoad`
    - `ANE_ProcessCreate_gated`
    - `isProcessValid`
    - family-6 create/load/process-state
    串成同一条 lower accepted-state 证据链。

- 时间：2026-06-12 23:08:00 +0800
- 目标：判断 `selector-4 raw prepare 0xe00002c2` 是否已经足够和 bootkc family-6 lower gate 收敛成同一条阻塞证据链。
- 动作：
  - 读取并对齐现有结果：
    - `process_state_source_provenance_note.md`
    - `program_load_state_join_note.md`
    - `bootkc_resource_gate_process_registry_probe.md`
    - `bootkc_process_create_probe.md`
    - `docs/ane_state.md` / `docs/ane_next.md` 中已有 family-6 摘要
  - 继续使用 `ida-pro-mcp` 分析 `aneservices_bin`：
    - `_ANEServicesProgramCreate`
    - `_ANEServicesProgramPrepare`
    - `__ZN3ANE17ANEServicesDevice18ANE_ProgramPrepareEP21ANEProgramPrepareArgs`
    - `_ANEServicesProgramDestroy`
  - 静态进一步确认：
    - create success-side只会先写
      `payload+0xda8 / wrapper+0x70 / wrapper+0xa8 / payload+0xde0 / payload+0xde4`
    - prepare success-side才会 first-write：
      `wrapper+0x98 / payload+0xd98 / payload+0xd78..`
    - destroy gate 依赖：
      `payload+0xd98 / payload+0xda8`
  - 从
    `ane_services_program_create_runtime_probe_v16_fake_token_sha.json`
    抽取并核对：
    - `raw_prepare_status_hex`
    - `raw_prepare_owner0_ready1_status_hex`
    - `raw_prepare_owner0_ready1_handlepatch_status_hex`
    - `raw_prepare_livehandle_status_hex`
  - 新增 bridge note：
    - `mps/ANE/experiments/results/selector4_family6_state_join_note.md`
- 证据：
  - `mps/ANE/experiments/results/selector4_family6_state_join_note.md`
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v16_fake_token_sha.json`
  - `aneservices_bin` 上述 4 个函数的 `ida-pro-mcp` 静态结果
- 结论：
  - `selector-4` 当前已经不是“继续补 visible handle/queueDepth 就可能过”的层：
    - `owner0+ready1 -> 0xe00002c2`
    - `owner0+ready1+handlepatch -> 0xe00002c2`
    - `raw_prepare_livehandle -> 0xe00002c2`
  - 这与 bootkc family-6 当前 lower gate family 是一致的：
    - setup token
    - `additional_params+0x18 / resource+0x493a0`
    - `resource+0x400d0` process registry
    - exact process membership
    - `process+0x203fc != 2`
  - 因而当前最合理的主线已经可以固定为：
    - `resource+0x400d0` first author
    - `record+0x1b8` durable author
    - `process+0x203fc == 2` decisive author
    这三者之一或其组合导致 current lower accepted-state 缺口。
- 下一步：
  - 下一轮默认不要再扩新的 userland visible field sweep。
  - 直接沿上面三条 bootkc lower author 路继续压。

- 时间：2026-06-12 23:20:00 +0800
- 目标：判断当前 selector-4/userland 可见面是否还有明显漏试项，还是应该正式转向 bootkc lower author。
- 动作：
  - 复读并对齐现有结果：
    - `process_state_*` 一组 note / probes
    - `restore_record_*` 一组 note / probes
    - `ane_services_static_probe.py`
    - `program_runtime_chain_note.md`
  - 明确确认：
    - `record+0x1b8` 线已经有：
      - state surface
      - bridge
      - copy bound
      - raw-send boundary
      - legacy scratch author gap
    - `process+0x203fc` 线已经有：
      - exact flag surface
      - window
      - helper surface
      - source provenance
      - `isProcessValid` gate
    - selector-4 userland visible contract当前只剩：
      - 0x38-byte inout prepare buffer
      - success-side `wrapper+0x98 / payload+0xd78..0xd98`
      - shallow device/runtime-entry preflight
  - 新增 note：
    - `mps/ANE/experiments/results/selector4_visible_surface_limit_note.md`
- 证据：
  - `mps/ANE/experiments/results/selector4_visible_surface_limit_note.md`
  - `mps/ANE/experiments/results/selector4_family6_state_join_note.md`
  - `mps/ANE/experiments/results/selector4_prepare_state_boundary_note.md`
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v16_fake_token_sha.json`
- 结论：
  - 当前 selector-4 userland visible surface 已基本耗尽：
    - shallow preflight 已越过
    - visible handle/queue-depth/prepare-word/token patch 已试过
    - 仍统一停在 `0xe00002c2`
  - 因而继续扩新的 wrapper-visible selector-4 field sweep，
    当前已不再是高价值方向。
  - 现在更合理的主线就是：
    - `resource+0x400d0` first author
    - `record+0x1b8` durable author
    - `process+0x203fc == 2` decisive author
- 下一步：
  - 下一轮默认从 bootkc lower author 里选一个继续下压，
    而不是回到新的 selector-4 wrapper patch。

- 时间：2026-06-12 23:32:00 +0800
- 目标：确认 `record+0x1b8` / completion-side 路线是否还值得继续加新 CPU-side probe，还是已经足够支持更强 blocker 结论。
- 动作：
  - 回读并对齐：
    - `restore_record_raw_send_boundary_note.md`
    - `legacy_scratch_author_gap_note.md`
    - `legacy_typed_submit_route_note.md`
    - `legacy_typed_completion_route_note.md`
    - `process_state_*` / `is_process_valid_probe_note.md`
    - `selector4_*` 两条新 note
  - 明确确认：
    - `record+0x1b8` 线已经覆盖：
      - visible scratch publication
      - restore-record bridge
      - copy bound
      - raw-send boundary
      - typed submit route
      - typed completion route
    - `process+0x203fc` 线已经覆盖：
      - exact flag surface
      - window
      - helper surface
      - source provenance
      - `isProcessValid` gate
  - 新增 blocker 汇总：
    - `mps/ANE/experiments/results/lower_author_gap_summary_note.md`
- 证据：
  - `mps/ANE/experiments/results/lower_author_gap_summary_note.md`
  - 上述 6 份已有 restore/submit/completion note
- 结论：
  - 当前再继续新增 CPU-visible probe，收益已经明显递减。
  - 现有证据已经足够支撑更强的 blocker 说法：
    - artifact-descriptor / visible wrapper / visible CPU-side staging
      已基本耗尽
    - 剩余缺口最像位于：
      1. `process+0x203fc == 2` decisive author
      2. `record+0x1b8` durable author below callback/completion side effects
      3. `resource+0x400d0` first materializer
      4. callback/completion sink execution 或 manager-side state replay
- 下一步：
  - 下一轮不再做泛化 blocker 收敛；
  - 直接从上面 4 个 lower target 里选一个继续下压。

- 时间：2026-06-12 23:40:00 +0800
- 目标：把当前 blocker 从“可能还漏了某个 visible field”提升到更可辩护的控制层边界陈述。
- 动作：
  - 回看现有 userland / bootkc 证据后，不再新增 probe，而是整理：
    - `selector4_family6_state_join_note.md`
    - `selector4_visible_surface_limit_note.md`
    - `lower_author_gap_summary_note.md`
  - 新增：
    - `mps/ANE/experiments/results/current_control_layer_blocker_note.md`
- 证据：
  - `mps/ANE/experiments/results/current_control_layer_blocker_note.md`
  - 上述三份现有 summary / bridge note
- 结论：
  - 当前最强 blocker claim 已可明确表述为：
    - artifact-descriptor / visible wrapper / visible CPU-side staging
      已基本耗尽
    - 缺口更像在更低 accepted-state/control-layer transition
    - 不再适合继续主要表述为
      “再找一个 obvious descriptor / wrapper field”
- 下一步：
  - 下一轮若继续推进，直接选 lower target：
    1. `process+0x203fc == 2`
    2. `record+0x1b8`
    3. `resource+0x400d0`
    之一继续下压；
  - 否则就已经足够支持“当前 visible control layer ends above accepted-state author”这条阻塞证据。

- 目标：把 private ANE 长时工作流从会话内记忆迁移到仓库持久规则。
- 动作：在 `AGENTS.md` 中加入 `/goal`、MCP 使用、文档更新、恢复顺序和 benchmark 口径规则；新增 `docs/ane_goal.md`、`docs/ane_state.md`、`docs/ane_next.md`、`docs/ane_log.md`。
- 证据：
  - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_persistent_aux_profile_profile/profile_summary.json`
  - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_persistent_aux_profile_profile/transformer_bottleneck_ledger.csv`
  - `benchmark_results/mlx_full_roformer_profile/test_clean_full_torch_mps_vs_mlx_full_current.json`
- 结论：以后 private ANE / artifact-descriptor 主线不再依赖单次会话记忆；恢复工作有固定入口。
- 下一步：用 `ida-pro-mcp` 建立 descriptor 到 `load/compile/eval` 的调用链，并对齐 trace。

- 目标：确认 descriptor/runtime 可见字段是否足够绕过重复 `loadWithQoS`，并把结论落到 bridge PoC。
- 动作：
  - 用 `ida-pro-mcp` 反编译 `-[_ANEInMemoryModel loadWithQoS:options:error:]` 与 `___44-[_ANEClient doLoadModel:options:qos:error:]_block_invoke_2`，确认成功 load 后 public 层会写入 `_ANEModel` 的 `modelAttributes/state/programHandle/intermediateBufferHandle/queueDepth/program/mapper`。
  - 新增 `mps/ANE/experiments/ane_runtime_rehydrate_probe.m`，在 phase4 linear artifact 上验证 fresh wrapper runtime rehydrate。
  - 在 `mps/maderix_ANE/bridge/ane_bridge.m` 加入 `ANE_BRIDGE_RUNTIME_CLONE_CACHE=1` 的 experimental fast path，并补上 clone handle `skipUnload`，避免 shared program 被 clone free 卸掉。
  - 用 `benchmark_results/private_ane/runtime_clone_bridge_smoke.json` 做桥级 smoke，确认重复 identifier 已可命中 `runtime_clone`。
  - 尝试用 `test_clean.m4a` 做整链复测；第一次因 benchmark 入口 Python 环境缺少 `numpy` 失败，切到 conda Python 后又确认当前 worktree 在 `band_split_l2_*` 首次 compile 即 `InvalidMILProgram`，因此整链 wall time 还无法直接和 43s 基线比较。
- 证据：
  - `mps/ANE/.ane_runs/csv/ane_runtime_rehydrate_probe.csv`
  - `benchmark_results/private_ane/runtime_clone_bridge_smoke.json`
  - `mps/ANE/experiments/results/runtime_rehydrate_clone_note.md`
  - `benchmark_results/private_ane/test_clean_runtime_clone_batch4_persistent_aux_smoke.private_ane_child/child.log`
  - `benchmark_results/private_ane/test_clean_runtime_clone_batch4_persistent_aux_fused_smoke.private_ane_child/child.log`
- 结论：
  - bridge eval-only 路径已经证实可以绕过 fresh wrapper 的重复 `loadWithQoS`；
  - `mapIOSurfaces...` 仍然失败，说明 runtime clone 目前不是完整 descriptor/runtime authoring 方案；
  - 当前整链 benchmark 的主要新阻塞不是 runtime clone，而是当前 worktree/config 下 band-split MIL 首次 compile 失败。
- 下一步：
  - 先定位 `band_split_l2_0` / `band_split_l2_fused_0_4` 的 `InvalidMILProgram`；
  - 然后用 `test_clean.m4a` 重跑当前最佳配置，统计 `runtime_clone` 命中次数和总 wall time 变化。

- 目标：恢复 `test_clean.m4a` benchmark 的真实 compile/load 路，并确认新的主要阻塞是不是从 compile 转到了内存监管。
- 动作：
  - 用最小复现确认 `band_split_l2_fused_0_4`、`stft_0_128_b1`、`stft_128_128_b1` 单独 compile 都是可行的。
  - 进一步做 STFT compile 矩阵，确认自定义 `ANE_BRIDGE_TMPDIR` 会把静态 STFT handle compile 稳定打成 `InvalidMILProgram`；不管目录是不是全新、atomic/keep 怎样都能复现。
  - 修改 `benchmark/private_ane_test_clean_benchmark.py`，把默认 `private_ane_cache_tmpdir` 从固定路径改成 `global`，只在用户明确给路径时才下发到 inference config。
  - 复跑 `test_clean.m4a` 短 benchmark；结果显示 compile 路已穿过 STFT 阶段并进入 `mask_batch_start`，新的 kill 原因变成 native supervisor 的 `wired_memory` / `compressor_memory`。
- 证据：
  - `benchmark_results/private_ane/stft_0_128_b1_real_repro/stft_0_128_b1.mil`
  - `benchmark_results/private_ane/band_split_l2_fused_0_4_repro/band_split_l2_fused_0_4.mil`
  - `benchmark_results/private_ane/test_clean_runtime_clone_onechunk_prime4.private_ane_child/parent_watchdog_failure.json`
  - `benchmark_results/private_ane/test_clean_runtime_clone_onechunk_relaxed.private_ane_child/parent_watchdog_failure.json`
  - `benchmark_results/private_ane/test_clean_runtime_clone_10p9s_batch1.private_ane_child/parent_watchdog_failure.json`
- 结论：
  - benchmark 路 compile fail 的一个真实来源是默认自定义 cache tmpdir，不是模板本身天然非法；
  - 修正默认 cache tmpdir 后，当前主阻塞已经转成 `mask_batch` 期间的系统级内存/压缩内存压力；
  - `runtime_clone` bridge fast path 已经在桥层成立，但对当前 `test_clean.m4a` 的单 batch 基线是否有显著收益，仍需在能跑完的真实链路上继续验证。
- 下一步：
  - 优先找一个能稳定完成的 `test_clean.m4a` 子集/批次配置，拿到真实链路的 route/hit 数据；
  - 再决定是否值得继续为 full-audio 43s 基线推进 memory supervisor 放宽或改 batch 策略。

- 时间：2026-06-12
- 目标：确认当前代码下 fixed cache tmpdir 是否能把 `test_clean.m4a` 拉回接近 43s 历史基线，并判断当前主要阻塞是否仍是内存监管。
- 动作：
  - 先对齐当前结果与 43s 历史基线，确认当前完整 run 里 `cache_tmpdir=global` 时约 `109.684s`，且当前 profile 产物可用 `benchmark/analyze_private_ane_profile.py` 补出。
  - 发现历史基线与当前 worktree 有关键参数漂移：当前 `FUSED_MASK_MAX_OUTPUTS=8`，而历史基线/先前成功 run 实际是 `2`；一次未显式固定该值的 fixed-cache 复测落到 `mask_fused_0_8` 并在 `mask_batch_start` 后 `InvalidMILProgram`。
  - 用真正同口径的参数重跑：
    - `test_clean.m4a`
    - `full-audio`
    - `chunk_batch_size=4`
    - `fused_band_split`
    - `fused_mask_estimator`
    - `fused_mask_estimator_max_outputs=2`
    - fixed `private_ane_cache_tmpdir=/Volumes/2T/pymss/benchmark_results/private_ane/ane_tmp_loadcache`
  - 结果写到 `benchmark_results/private_ane/test_clean_full_private_fixedcache_mask2_currentcode.json`，
    并生成 `benchmark_results/private_ane/test_clean_full_private_fixedcache_mask2_currentcode_profile/profile_summary.json`。
- 证据：
  - `benchmark_results/private_ane/test_clean_full_private_fixedcache_currentcode.private_ane_child/parent_watchdog_failure.json`
  - `benchmark_results/private_ane/test_clean_full_private_fixedcache_mask2_currentcode.json`
  - `benchmark_results/private_ane/test_clean_full_private_fixedcache_mask2_currentcode_profile/profile_summary.json`
  - `benchmark_results/private_ane/test_clean_full_private_runtimeclone_off_persistentaux_profile/profile_summary.json`
- 结论：
  - fixed cache tmpdir 在当前代码下不是无效，`109.684s -> 85.591s`，改进约 `22%`；
  - 但离历史 `43.003s` 仍远，说明主问题不是单一 cache 开关；
  - fixed cache 改善了 `transformer.eval` / `ane_pre_eval` / `axis_pack` / `ane_read` / `gc` / `istft`，
    却显著恶化了 `band_split.compile` 与 `transformer.load_or_compile`；
  - 因此在当前最接近基线的形态里，主要阻塞已从“native supervisor kill”转成
    “compile/load 路径回退 + bridge orchestration 开销”。
- 下一步：
  - 给 band split / mask / transformer pre/gate/ffn 补 bridge 级 load/compile 分项，
    直接看 `descriptor_sec` / `model_create_sec` / `file_write_sec` / `load_qos_sec`；
  - 继续对照 43s 历史基线，找出为什么当前 fixed-cache 形态下
    `transformer.load_or_compile=25.908s`、`band_split.compile=7.793s` 仍然过高。

- 时间：2026-06-12
- 目标：把 current worktree 的 compile/load 回退继续拆细，确认是不是桥层文件校验与 Python 侧 materialization 在主导。
- 动作：
  - 在 `private_ane.py` / `analyze_private_ane_profile.py` 补齐 stage 级 bridge 分项：
    - `descriptor_sec`
    - `model_create_sec`
    - `file_write_sec`
    - `load_qos_sec`
    - `surface_create_sec`
    - `request_create_sec`
  - 用现代码重跑：
    - `benchmark_results/private_ane/test_clean_full_private_fixedcache_mask2_currentcode_bridgeprofile.json`
    - `benchmark_results/private_ane/test_clean_full_private_global_mask2_currentcode_bridgeprofile.json`
  - 继续用 `ida-pro-mcp` 打开 `ANECompiler.i64`，确认：
    - `ANECCompile` 含 `"Start of compilation of network from file: %s"` 和 `.status.plist`
    - `ANECCompileJIT` 含 `jit_cfg_0`
    - `ANECGetJITCompilerInputs` 明确要求 AOT file / JIT shapes file / output JIT file
  - 在 bridge 侧新增 `ANE_BRIDGE_SKIP_CONTENT_VERIFY=1`，把 load-cache hit 时的
    全量文件内容比对改成 size-match 快速跳过，并在 private ANE runner 开启
    load-cache 时默认下发。
  - 试做过 Python-side blob cache，但在 `test_clean.m4a` 单 batch 口径下没有给出
    明确收益，已回退，保留 bridge 主线优化。
- 证据：
  - `benchmark_results/private_ane/test_clean_full_private_fixedcache_mask2_currentcode_bridgeprofile_profile/profile_summary.json`
  - `benchmark_results/private_ane/test_clean_full_private_global_mask2_currentcode_bridgeprofile_profile/profile_summary.json`
  - `mps/maderix_ANE/bridge/ane_bridge.m`
  - `ANECompiler` session `anecompiler_i64` 下：
    - `_ANECCompile`
    - `_ANECCompileJIT`
    - `__Z24ANECGetJITCompilerInputsPK14__CFDictionaryR23ZinIrCompilerParametersRiR27ZinIrPlistCompilationStatus`
- 结论：
  - fixed-cache 慢的核心已确认不是 `load_qos`，而是桥层 `file_write/content-verify`；
  - 在 fixed-cache bridgeprofile 结果里：
    - transformer `bridge_file_write = 22.231s`
    - mask `bridge_file_write = 11.531s`
    - band split `bridge_file_write = 10.735s`
    - istft `bridge_file_write = 5.457s`
  - 开启 `ANE_BRIDGE_SKIP_CONTENT_VERIFY=1` 后，global 路最佳结果降到 `61.953s`，
    且对应 `bridge_file_write` 已被压到亚秒级：
    - transformer `0.306s`
    - mask `0.158s`
    - band split `0.155s`
    - istft `0.037s`
  - 当前 remaining gap 已经不是“native compile/load 黑盒本体慢”：
    - 在 `61.953s` 结果里 `transformer.load_or_compile = 10.229s`
    - 但 `transformer.bridge_profile_total = 3.757s`
    - 差值约 `6.47s`
    说明剩余大头在 Python/ctypes/materialization 路径。
  - 同时已验证 bridge identifier 第一段等于 `sha256(mil_text)`；第二段 weights hash
    形式仍未完全恢复。
- 下一步：
  - 优先研究“pure identifier / file-backed load”路线，目标是绕过 Python 侧
    大 weights dict / ctypes copy；
  - 若第二段 hash 仍无法完全恢复，则考虑持久化 manifest，把
    `compile-key -> identifier` 映射写到 cache dir，下一次直接走
    `_ANEModel modelAtURL:key:` / `_ANEClient loadModel:options:qos:error:`。

- 时间：2026-06-12 05:10:59 +0800
- 目标：验证 public `client_file_load` 的真实 `modelURL/key` 语义，并确认它对 weighted transformer segments 是否足够。
- 动作：
  - 用 `ida-pro-mcp` 重新打开 `AppleNeuralEngine.i64` / `ANEServices.i64`，反编译：
    - `-[_ANEClient connectionForLoadingModel:options:]`
    - `-[_ANEClient doLoadModel:options:qos:error:]`
    - `___44-[_ANEClient doLoadModel:options:qos:error:]_block_invoke`
    - `___44-[_ANEClient doLoadModel:options:qos:error:]_block_invoke_2`
    - `-[_ANEClient compileModel:options:qos:error:]`
    - `___45-[_ANEClient compileModel:options:qos:error:]_block_invoke_2`
    - `_ANEModel` 的 `modelAtURL*` / `setCacheURLIdentifier:` / `initWithModelIdentifier:`
  - 从静态结果确认：
    - `loadModel` 只有在 `kANEFModelHasCacheURLIdentifierKey` 为真时才跳过 sandbox extension
    - compile success 只写 compiled state + cache id，load success 才会写 program/mapper
  - 修正 `mps/maderix_ANE/bridge/ane_bridge.m` 的 `client_file_load`：
    - 不再把 `hexStringIdentifier` 传成 `_ANEModel modelAtURL:key:` 的 `key`
    - 改成 `model.mil file URL + @""`
  - 修正 `benchmark/private_ane_realtime_stft_probe.m` 中名为 `file_empty` 的 probe，
    让它实际传空 key。
  - 新增并保存三组证据：
    - `benchmark_results/private_ane/realtime_stft_client_file_probe.json`
    - `benchmark_results/private_ane/stft_client_file_probe_fixed.json`
    - `benchmark_results/private_ane/block_client_file_probe.json`
  - 补齐缺失 profile：
    - `benchmark_results/private_ane/test_clean_full_private_historical_shape_bridgepatched_profile/profile_summary.json`
- 证据：
  - `benchmark_results/private_ane/realtime_stft_client_file_probe.json`
    - `direct_compile_ok = false`
    - `direct_load_ok = false`
    - `file_direct_load_ok = true`
    - `file_opt_direct_load_ok = true`
    - directory 路明确报
      `Cannot load network .../model.espresso.net`
  - `benchmark_results/private_ane/stft_client_file_probe_fixed.json`
    - preload `bridge_profile_route = load_cache_client_file`
    - `bridge_profile_fast_load_hit = 1`
    - `bridge_profile_fast_load_fallback = 0`
  - `benchmark_results/private_ane/block_client_file_probe.json`
    - 真实 transformer block 的 `pre/gate/ffn` 都有权重 (`n_weights = 4/5/6`)
    - 但两轮都是 `fast_load_attempted = 1`, `fast_load_hit = 0`,
      `fast_load_fallback = 1`
    - 且 `bridge_profile_file_write_sec = 0.0`，说明不是重新写文件，而是
      `_ANEClient loadModel` 本身仍拒绝 weighted source route
  - `ida-pro-mcp` 静态事实：
    - `connectionForLoadingModel:options:` 仅对 `kANEFModelPreCompiled` 选 fast connection
    - `doLoadModel` 成功回调显式写 program/mapper
    - `compileModel` 成功回调只推进到 compiled state + cache id
- 结论：
  - public source-style `client_file_load` 的关键高层语义已确认：
    - `modelURL` 不能用目录 URL
    - `key` 不能再用 `hexStringIdentifier`
    - 当前可工作的 public 形态是 `model.mil file URL + empty key`
  - 这个修正已经足以打通 STFT 一类 source MIL 的 direct file-load hit。
  - 但它还不足以打通 weighted transformer segments；当前缺的已经不是简单
    URL/key 拼接，而是 weighted source artifact 在 `_ANEClient loadModel`
    路上的额外接纳条件。
- 下一步：
  - 在 bridge profile 或最小 Objective-C probe 里把 weighted
    `client_file_load` 的中间 `NSError` 单独落盘，避免被 fallback 掩盖；
  - 以 `block_client_file_probe.json` 的 `pre/gate/ffn` cache dir 为样本，
    继续最小化重放 `_ANEModel modelAtURL:key:` + `_ANEClient loadModel`，
    对照 options / attributes / sourceURL 差异。

- 时间：2026-06-12 05:30:00 +0800
- 目标：确认 weighted public file-load 的真实拒绝原因，并验证单一 packed weight file 是否能把 `loadModel` 打通。
- 动作：
  - 新增 `benchmark/ane_weighted_client_load_probe.m`，对保存下来的 real transformer
    `pre` segment cache dir 测多组 `_ANEModel` 构造 + `_ANEClient compile/load` 组合。
  - 结果落盘：
    - `benchmark_results/private_ane/weighted_client_load_probe_pre.json`
    - `benchmark_results/private_ane/weighted_client_load_probe_pre_packed.json`
  - 在 bridge 中新增 `client_file_error` / `client_file_loaded` profile 字段，并把
    weighted `client_file_load` 的中间错误透传到 Python probe/benchmark JSON。
  - 在 bridge 中新增实验性 packed single-file route：
    - `ANE_BRIDGE_CLIENT_FILE_PACK_WEIGHTS`
    - 额外写 `model.client.mil`
    - 额外写 `weights/packed.bin`
  - 用真实 block probe 验证 packed route：
    - `benchmark_results/private_ane/block_client_file_probe_packed_bridge_debug_verbose_v3.json`
    - 打开 `ANE_BRIDGE_VERBOSE_EVAL_FAIL=1`
- 证据：
  - `benchmark_results/private_ane/weighted_client_load_probe_pre.json`
    - multi-file weighted source artifact 的 public compile/load 直接报：
      `Blob storage must be backed by only one weight file.`
  - `benchmark_results/private_ane/weighted_client_load_probe_pre_packed.json`
    - 同一 `pre` segment 改成单一 packed.bin 后：
      - `compile_ok = true`
      - `load_ok = true`
      - `compiled_exists_after_compile = true`
      - 多个 model variant / option variant 都能进入 `state=3` 并拿到非零 `programHandle`
  - `benchmark_results/private_ane/block_client_file_probe_with_error.json`
    - 原始 multi-file bridge 路在真实 `pre/gate/ffn` 上已能稳定复现
      `client_file_error = ... Blob storage must be backed by only one weight file`
  - `benchmark_results/private_ane/block_client_file_probe_packed_bridge_debug_verbose_v3.json`
    - packed route 下：
      - iter1 `client_file_loaded = 1`
      - iter2 `fast_load_hit = 1`
      - 但 eval 仍失败
    - stderr:
      `ANEProgramProcessRequestDirect() Failed with status=0x2 : statusType=0x9: Program Inference error`
  - 本地已有的 single-blob 参考：
    - `mps/ANE/inmem_peak.m`
    - `mps/ANE/experiments/results/ane_artifact_format.md`
    说明 M4 上 single-blob 不是天然不支持，当前是我们 packed 形态仍不完全正确。
- 结论：
  - 当前最核心的新事实不是“weighted public load 不通”，而是：
    1. 原始 multi-file source artifact 被 public translator 拒绝，原因已定位。
    2. 单一 packed weight file 已足以让 weighted `loadModel` / cache-hit 成功。
    3. 新阻塞点下沉到了 packed artifact 的 runtime/eval 语义。
  - 因此这条线已经从 URL/key/cache-id 问题，推进到了 single-blob runtime container
    或 sidecar 语义问题。
- 下一步：
  - 优先对照 `mps/ANE/inmem_peak.m` 的 single-blob 生成方式，继续收窄
    `packed.bin` 的正确 chunk/header 形态；
  - 其次检查 packed source route 是否还缺 `data` 等运行期 sidecar。

- 时间：2026-06-12 05:55:00 +0800
- 目标：继续收窄 packed weighted artifact 的 eval 失败边界，确认哪些高层字段和哪些 chunk-header 小改动已经可以排除。
- 动作：
  - 新增 `benchmark/ane_weighted_client_eval_probe.m`，直接对 packed `pre` segment 做
    `compileModel -> loadModel -> evaluateWithModel -> unloadModel`。
  - 先验证 options：
    - `benchmark_results/private_ane/weighted_client_eval_probe_pre_packed.json`
  - 再验证 `_ANEModel` 高层构造变体：
    - `benchmark_results/private_ane/weighted_client_eval_probe_pre_packed_variants.json`
    - `file_key_empty`
    - `file_source_dir_id1`
    - `file_source_dir_id2`
    - `file_source_dir_id2_cache`
    - `file_cache_identifier`
  - 再做 packed.bin header/offset 小矩阵：
    - `benchmark_results/private_ane/weighted_pack_variants_pre/summary.json`
    - `slice_keep`
    - `slice_abs`
    - `slice_rel64`
    - `slice_zero`
    - `slice_0x08_rel64`
    - `slice_0x08_zero`
    - `peak_style`
- 证据：
  - `weighted_client_eval_probe_pre_packed.json`
    - `empty` 和 `file_opts` 都是：
      - `compile_ok = true`
      - `load_ok = true`
      - `eval_ok = false`
      - 错误固定为
        `ANEProgramProcessRequestDirect() ... Program Inference error`
  - `weighted_client_eval_probe_pre_packed_variants.json`
    - 所有 tested `_ANEModel` 变体都是：
      - `compile_ok = true`
      - `load_ok = true`
      - `eval_ok = false`
    - 说明 `sourceURL / identifierSource / cacheURLIdentifier` 都不是当前解锁点。
  - `weighted_pack_variants_pre/summary.json`
    - `slice_keep / abs / rel64 / zero`：
      `compile_ok = true`, `load_ok = true`, `eval_ok = false`
    - `slice_0x08_rel64 / slice_0x08_zero / peak_style`：
      直接 `compile_ok = false`
- 结论：
  - packed weighted artifact 的 `Program Inference error` 已经证明与：
    - eval options
    - sourceURL / identifierSource / cacheURLIdentifier
    - 以及当前尝试过的几种 header offset 小修补
    无关。
  - 这进一步说明阻塞点已经收窄到：
    - single-blob 容器中更低层的 chunk/header 语义
    - 或 packed source artifact 缺失的 sidecar / runtime state
- 下一步：
  - 对照 `mps/ANE/inmem_peak.m` / `ane_artifact_format.md` 深挖 single-blob
    容器的剩余字段；
  - 若仍无解，优先测试 `data` 等 sidecar 是否影响 packed eval。

- 时间：2026-06-12 06:22:07 +0800
- 目标：继续判断 packed weighted 路线到底是“容器坏了”还是“不同子段的 runtime contract 已经分化”。
- 动作：
  - 新增并运行：
    - `benchmark/ane_weighted_client_eval_threeout_probe.m`
    - `benchmark/ane_publicload_privateeval_probe.m`（增加 `direct_process`）
  - 生成 fresh 唯一路径 packed artifact，排除 stale compiled cache：
    - `benchmark_results/private_ane/weighted_fresh_pack_pre_1781215248`
  - 对 `pre` 做三类验证：
    1. one-output public eval
    2. three-output public eval
    3. public load 后转 private wrapper / factory_full / direct process
  - 对 `gate` / `ffn` 各做 fresh packed one-output eval：
    - `weighted_fresh_pack_gate_1781216020_eval.json`
    - `weighted_fresh_pack_ffn_1781216020_eval.json`
  - 把关键结果复制成稳定文件名：
    - `weighted_fresh_pack_pre_load_stable.json`
    - `weighted_fresh_pack_pre_eval_stable.json`
    - `weighted_fresh_pack_pre_eval_threeout_stable.json`
    - `weighted_fresh_pack_gate_eval_stable.json`
    - `weighted_fresh_pack_ffn_eval_stable.json`
- 证据：
  - `weighted_fresh_pack_pre_load_stable.json`
    - fresh packed `pre` 一样 `compile_ok = true`, `load_ok = true`
  - `weighted_fresh_pack_pre_eval_stable.json`
    - one-output `eval_ok = false`
  - `weighted_fresh_pack_pre_eval_threeout_stable.json`
    - three-output request 后 `eval_ok = true`
  - `publicload_privateeval_probe_pre_directprocess.json`
    - `direct` private eval 失败
    - `factory_full` private eval 失败
    - `direct_process` 直接 `_ANEProgramForEvaluation processRequest` 也失败，
      `driver_status = 2`
  - `weighted_fresh_pack_gate_eval_stable.json`
    - `gate` 在 `file_opts` 下 `compile_ok = true`, `load_ok = true`, 但
      `eval_ok = false`
  - `weighted_fresh_pack_ffn_eval_stable.json`
    - `ffn` 已直接 `compile_ok = true`, `load_ok = true`, `eval_ok = true`
- 结论：
  - 当前 packed weighted 路线已经不是一个统一问题：
    - `pre` 的 public runtime contract 已经变成三输出 `k/q/v`
    - `ffn` 已是可用 packed public route
    - `gate` 仍是 packed eval 阻塞点
  - 因此下一轮最值得做的不是继续泛化 single-blob 猜测，而是：
    1. 先尝试把 `ffn` packed public route 落进真实 block/pipeline
    2. 再单独攻 `gate`
    3. `pre` 则作为“public contract 已偏移”的强证据线处理
- 下一步：
  - 做一个 mixed-mode block：
    - `pre/gate` 先保持 private in-memory
    - `ffn` 单独切到 packed public route
  - 若 mixed block 跑通，再考虑往真实 transformer pipeline 接。

- 时间：2026-06-12 06:52:07 +0800
- 目标：确认 `ffn` 的 packed public 数值漂移到底是 client/private-eval 包装问题，还是 packed public program 本身的语义问题。
- 动作：
  - 新增 `benchmark/private_ane_real_ffn_mode_compare.py`：
    - 同一输入下比较
      `private_inmem` /
      `public_packed_public_eval` /
      `public_packed_private_eval` /
      `public_packed_direct_process`
  - 在 bridge 新增 `ANE_BRIDGE_DIRECT_PROCESS_EVAL=1`，
    让非 clientModel 路径可直接调用
    `_ANEProgramForEvaluation processRequest:model:qos:qIndex:modelStringID:options:returnValue:error:`
  - 用 IDA 复核 `-[_ANEInMemoryModel evaluateWithQoS:options:request:error:]`，
    确认正常主机环境下它会优先走 `sharedConnection -> evaluateWithModel`
  - 生成并固化结果：
    - `benchmark_results/private_ane/ffn_mode_compare_directprocess_stable.json`
- 证据：
  - `ffn_mode_compare_directprocess_stable.json`
    - `private_inmem` 对 torch：
      - `mean_abs = 0.0020097045`
      - `max_abs = 0.0119628906`
    - `public_packed_public_eval` 对 torch：
      - `mean_abs = 0.1788446307`
      - `max_abs = 1.7541503906`
    - `public_packed_private_eval` 对 torch：
      - 与 public eval 完全一致
    - `public_packed_direct_process` 对 torch：
      - 与 public eval 完全一致
    - `public_eval_vs_public_privateeval = 0`
    - `direct_process_vs_public_eval = 0`
  - IDA：
    - `-[_ANEInMemoryModel evaluateWithQoS:options:request:error:]`
      在 `sharedConnection` 存在时直接调用
      `evaluateWithModel:options:request:qos:error:`
- 结论：
  - 当前 `ANE_BRIDGE_CLIENT_FILE_PRIVATE_EVAL` 并不构成真正的“更低层数值路径”；
    在正常主机环境下它仍回到 public client eval。
  - 但即便显式强制 `direct_process`，`ffn` 输出仍与 public eval 逐值完全相同。
  - 因此 `ffn` 的问题已经收窄为：
    - public packed compiled program 语义偏移，或
    - packed single-blob weight / offset / sidecar contract 不正确，
    而不是 wrapper / mapper / evaluate 入口差异。
- 下一步：
  - 不再做 `ffn` mixed-mode pipeline 集成。
  - 先检查：
    1. `model.client.mil` rewrite 是否只改了 `BLOBFILE(path, offset)`；
    2. `weights/packed.bin` 的 header / 对齐 / offset 是否与 public translator
       真正要求一致；
    3. 如有必要，再补更低层输出导出 probe，把 packed blob decode 和 compile 后
       program 语义区分开。

- 时间：2026-06-12 07:05:00 +0800
- 目标：继续收窄 `ffn` packed public 数值错误，验证它是否来自 copied sub-header、
  `packed.bin` 路径命名，还是更深一层的 public packed contract。
- 动作：
  - 先核对当前 packed artifact：
    - `model.client.mil` 相对 `model.mil` 的 diff
    - `weights/packed.bin` 与原始 `weights/*.bin` 头部/offset
  - bridge 新增 `ANE_BRIDGE_CLIENT_FILE_PACK_MODE`：
    - `synth_simple`：不再复制原始 second-half header，改为合成
      `64B global + 64B chunk header + payload`
    - `data_root`：把单 blob 写到根目录 `data`，MIL 引用 `@model_path/data`
  - 扩展 `benchmark/private_ane_real_ffn_mode_compare.py`，新增模式：
    - `public_packed_synth_direct_process`
    - `public_data_root_direct_process`
  - 生成并固化结果：
    - `benchmark_results/private_ane/ffn_mode_compare_packmodes_stable.json`
- 证据：
  - `model.mil -> model.client.mil` diff：
    - 只改了 `BLOBFILE(path, offset)`，没有额外 MIL 语义改写
  - `ffn_mode_compare_packmodes_stable.json`
    - `public_packed_direct_process` 对 torch：
      - `mean_abs = 0.1788446307`
      - `max_abs = 1.7541503906`
    - `public_packed_synth_direct_process`：
      - 与 `public_packed_direct_process` 逐值完全一致
    - `public_data_root_direct_process`：
      - 也与 `public_packed_direct_process` 逐值完全一致
    - `synth_direct_process_vs_current_direct_process = 0`
    - `data_root_direct_process_vs_current_direct_process = 0`
- 结论：
  - `ffn` 错误已经进一步排除了：
    - copied original sub-header 这一层
    - `weights/packed.bin` vs `@model_path/data` 路径/命名这一层
    - `client eval` / `private eval` / `direct process` 入口差异
  - 因此当前最像的根因已收窄到：
    - public source compiler 对 packed shared-blob 的更深层语义偏移，或
    - 缺失当前 bridge 未 author 的 sidecar / companion descriptor
- 下一步：
  - 更值得做的是：
    1. 构造一个最小 “单文件多 offset 但非 transformer” 数值 probe；
    2. 或继续查 public route 是否还依赖 `data` 之外的 companion 文件/字段。

- 时间：2026-06-12 07:18:00 +0800
- 目标：区分“shared-blob 多 offset 一般性不成立”与“heterogeneous FFN 常量组合有问题”。
- 动作：
  - 新增并运行：
    - `benchmark/private_ane_ffn_authored_sharedblob_compare.py`
      - 把完整 FFN 从一开始就 author 成单 `weight.bin` 多 offset
    - `benchmark/private_ane_sharedblob_convchain_compare.py`
      - 做 same-shape 两层 conv chain shared-blob 对照
  - 另外补一个更小的 heterogeneous `gamma + conv + bias` ad-hoc probe，
    并把失败 profile 固化到：
    - `benchmark_results/private_ane/sharedblob_affine_fail_probe.json`
- 证据：
  - `benchmark_results/private_ane/sharedblob_convchain_compare_stable.json`
    - same-shape shared-blob：
      - private/public/private-eval/direct-process 四路输出逐值完全一致
      - `public_eval_vs_private_inmem = 0`
  - `benchmark_results/private_ane/ffn_authored_sharedblob_compare_stable.json`
    - 完整 FFN authored shared-blob：
      - private 就已经明显错误
        (`mean_abs = 2.7832823`, `max_abs = 116.1602783`)
      - public 三路也错误，且三路彼此一致
  - `benchmark_results/private_ane/sharedblob_affine_fail_probe.json`
    - heterogeneous `gamma + conv + bias` shared-blob：
      - private 路直接 `InvalidMILProgram`
- 结论：
  - `single weight.bin + multi-offset` 机制本身不是普遍失效；
    same-shape case 已证实可用。
  - 当前更像的真实边界是：
    - heterogeneous shared-blob contract
    - 或 heterogeneous 常量组合需要额外 sidecar / companion descriptor
  - 因而 full FFN 的 blocker 已从“public packed route 一般性错误”进一步收窄为：
    “heterogeneous shared-blob / FFN constant family 的 deeper contract 未恢复”。
- 下一步：
  - 做更小的 heterogeneous ladder，优先顺序：
    1. `W + B`
    2. `gamma + W`
    3. `W1 + B1 + W2`
  - 若这些都能找到明确最小失败集合，再回头用 IDA 追 descriptor/runtime
    是否有与 mixed constant families 对应的 companion 字段。

- 时间：2026-06-12 07:30:00 +0800
- 目标：把 heterogeneous shared-blob 的最小失败集合固化出来，并确认下一控制层是否已在 `ANECompiler` 里显式出现。
- 动作：
  - 新增并运行：
    - `benchmark/private_ane_sharedblob_hetero_ladder.py`
  - 产出：
    - `benchmark_results/private_ane/sharedblob_hetero_ladder_stable.json`
  - 新开 `ANECompiler.framework` 的 IDA session：
    - `anecompiler_i64`
  - 在 `ANECompiler` 里定位并读取：
    - `ParseFileInfoFromTensorValue(...)`
    - `ANECIRNetwork::getWeightFileIndex(...)`
    - `SetupWeightFileProperties(...)`
- 证据：
  - `sharedblob_hetero_ladder_stable.json`
    - `w_plus_b`
      - private `InvalidMILProgram`
      - public / private-eval / direct 都能跑，且数值一致
    - `gamma_plus_w`
      - private 失败
      - public 三路也失败，显式报
        `Cannot serialize ANEC_IR_repr`
    - `gamma_w_b`
      - 与 `gamma_plus_w` 同类失败
    - `w1_w2`
      - private 失败
      - public 三路都能跑，且数值一致
    - `w1_b1_w2`
      - private 失败
      - public 三路都能跑，且数值一致
  - `ANECompiler`:
    - `ParseFileInfoFromTensorValue(...)`
      - 直接处理 `FILEBLOB`
      - 含：
        - `at most 16 weight files`
        - `Required FILEBLOB property`
        - `mutable fileblob ... is not supported`
    - `SetupWeightFileProperties(...)`
      - 直接处理 weight-file property dictionary
      - 含：
        - `kANECNetWeights`
        - `kANECNetMutableWeights`
        - `Encrypted property ...`
        - `Symbol property ...`
- 结论：
  - 最小失败边界比上一轮更清楚：
    - same-shape shared-blob 正常
    - heterogeneous family 一旦出现，private 往往先失败
    - `gamma` 参与时，public translator 也会掉到
      `Cannot serialize ANEC_IR_repr`
  - 因而下一控制层需求已经不再是“继续改 packed raw blob”，而是：
    - 搞清并 author `FILEBLOB` companion / weight-file property dictionary
    - 尤其是 `Symbol` / `Encrypted` / `kANECNetWeights` 这类 compiler 显式入口
- 下一步：
  - 直接围绕 `SetupWeightFileProperties(...)` 追调用链和输入来源，
    看当前 bridge 是否有办法通过 `optionsPlist` 或同类入口 author 这些属性。

- 时间：2026-06-12 07:40:00 +0800
- 目标：验证 compiler companion 是否真的可通过 descriptor `optionsPlist` 下传，以及最直观的 `WeightFileProperties` 是否能撬动 heterogeneous 失败。
- 动作：
  - 在 bridge 加入 env-gated descriptor companion 注入：
    - `ANE_BRIDGE_DESCRIPTOR_WEIGHT_FILE_PATH`
    - `ANE_BRIDGE_DESCRIPTOR_WEIGHT_FILE_SYMBOL`
    - `ANE_BRIDGE_DESCRIPTOR_WEIGHT_FILE_ENCRYPTED`
  - 修正实现细节：
    - `_ANEInMemoryModelDescriptor` 的 `optionsPlist` 不是字典对象，而是 `NSData`
    - 因此 helper 改为把 plist 字典序列化成二进制 plist bytes
  - 用 `gamma_plus_w` 跑 6 组矩阵：
    - path:
      - `weight.bin`
      - `weights/weight.bin`
      - `@model_path/weights/weight.bin`
    - symbol:
      - `G`
      - `W`
    - `Encrypted = false`
  - 固化结果：
    - `benchmark_results/private_ane/gamma_plus_w_weightfileprops_matrix.json`
- 证据：
  - `AppleNeuralEngine -[_ANEInMemoryModel saveModelFiles]`
    - 会把 `descriptor.optionsPlist` 写到 `compilerOptionsFileName`
    - 说明 descriptor companion 的 compiler 下传路径真实存在
  - `gamma_plus_w_weightfileprops_matrix.json`
    - 6 组组合全部仍然 `InvalidMILProgram`
- 结论：
  - `optionsPlist` 路不是空路，但最直观的
    `WeightFileProperties + Symbol + Encrypted`
    还不足以修复 `gamma_plus_w`
  - 因而下一控制层需求比这更深：
    - 要么还有额外 companion 字段未恢复
    - 要么 `WeightFileProperties` 只是其中一层，而 heterogeneous shared-blob
      还依赖别的 compiler-side registration/state
- 下一步：
  - 继续追 `SetupWeightFileProperties(...)` 的调用方和上游字典来源；
  - 尤其看 `kANECNetWeights` / `kANECNetMutableWeights` 及其 surrounding schema。

- 时间：2026-06-12 07:50:00 +0800
- 目标：验证 `Weights / MutableWeights / WeightFileProperties / GammaOffset...` 这一层最小 plist author 是否足以改变 private heterogeneous 失败面。
- 动作：
  - 在 bridge 增加通用入口：
    - `ANE_BRIDGE_DESCRIPTOR_OPTIONS_PLIST_FILE`
    - 允许外部实验直接喂二进制 plist bytes
  - 先对 `gamma_plus_w` 跑：
    - `Weights`
    - `MutableWeights`
    - `WeightFileProperties`
    - `GammaOffset / KernelOffset / BiasOffset`
    的最小矩阵
  - 固化结果：
    - `benchmark_results/private_ane/gamma_plus_w_optionsplist_matrix/matrix.json`
    - `benchmark_results/private_ane/gamma_kernel_offset_probe/probe.json`
- 证据：
  - `gamma_plus_w_optionsplist_matrix/matrix.json`
    - `Weights=["weights/weight.bin"]`
    - `Weights=["weight.bin"]`
    - `MutableWeights=["weights/weight.bin"]`
    - 再叠加 `WeightFileProperties(Symbol, Encrypted)`
    - 全部仍然 `InvalidMILProgram`
  - `gamma_kernel_offset_probe/probe.json`
    - `GammaOffset`
    - `KernelOffset`
    - `BiasOffset`
    这组显式 offset key 也未改变失败面
- 结论：
  - 当前 companion 恢复已经可以确定不是缺一个显而易见的 plist key。
  - 下一控制层需求更像：
    - compiler-side deeper schema
    - 或 driver/compiler registration state
    - 而不再是继续堆 top-level plist key 组合。
- 下一步：
  - 继续从 `SetupWeightFileProperties(...)` / `FillContext(...)` 往上追，
    看这些字典到底由哪个更高层对象 author；
  - 或转向 `ANECompilerService` / translator caller，确认 `optionsFilename`
    之外是否还有 companion 输入面。

- 时间：2026-06-12 08:05:00 +0800
- 目标：确认 `optionsPlist` 是否需要一整版 compiler network plist，而不只是散的 companion key。
- 动作：
  - 继续解 `FillContext(...)` 顶层 key：
    - `Version`
    - `BinaryPoint`
    - per-network `Attributes`
  - 基于这些 key author 一版最小 full net plist：
    - `Version ∈ {1.0.0, 1.0.4}`
    - network name ∈ {main, net}
    - per-network dict:
      - `Attributes = {}`
      - `Weights = ["weights/weight.bin"]`
      - optional `WeightFileProperties`
  - 结果固化：
    - `benchmark_results/private_ane/gamma_plus_w_fullnetplist_probe/probe.json`
- 证据：
  - `gamma_plus_w_fullnetplist_probe/probe.json`
    - 8 组 full-net-plist 组合全部仍然 `InvalidMILProgram`
- 结论：
  - `descriptor.optionsPlist` 不是完全错方向，但当前已知的
    minimal network-plist author 仍然远远不够。
  - 这意味着下一控制层需求已经不只是“知道有哪些 key”，而是：
    - 更深的 schema 细节
    - 或 compiler/translator 更高层对象 author 出来的 state
- 下一步：
  - 不再继续做 `Version/BinaryPoint/Weights/...` 小矩阵；
  - 转去追 `FillContext(...)` 的调用方和 `ANECompilerService`/translator
    上游，找真实 network dictionary 的生产者。

- 时间：2026-06-12 08:15:38 +0800
- 目标：确认是否需要额外接入 `mrexodia/ida-pro-mcp` 或 `blacktop/ida-mcp-rs`，
  以及当前 IDA/现有 MCP 是否已足够支撑下一轮逆向。
- 动作：
  - 读取恢复文档，核对 handoff 与仓库内状态是否一致。
  - 用现有 `ida-pro-mcp` 直接枚举会话，确认：
    - `anecompiler_i64`
    - `appleneuralengine_i64`
    已存在。
  - 发现 `anecompiler_i64` worker 不可达后，直接重新 `idb_open`，
    并成功恢复到可反编译状态。
  - 用恢复后的会话重新解 `ZinIrFactory::FillContext(...)` 及其构造层。
- 证据：
  - `mcp__ida_pro_mcp.idb_list`
  - `mcp__ida_pro_mcp.idb_open(database=anecompiler_i64 对应 input_path)`
  - `mcp__ida_pro_mcp.analyze_batch(addr=0x222e695dc)`
- 结论：
  - 当前瓶颈不是“缺另一套 IDA MCP 实现”，而是继续往上追
    `FillContext(...)` 的真实 producer。
  - 现有 `ida-pro-mcp` 已足够；worker 偶发失联属于会话稳定性问题，
    先重开 session 即可，不值得现在切换 transport。
- 下一步：
  - 继续在当前 `ida-pro-mcp` 上追 `FillContext(...)` / translator /
    compiler service 的上游构造链，定位真实 network dictionary
    的 author 位置。

- 时间：2026-06-12 08:28:52 +0800
- 目标：确认 `FillContext(...)` 之前是否还有更高层 producer/rewriter，
  并判断当前阻塞更像 descriptor plist 缺 key，还是更早的 MIL lowering 缺失。
- 动作：
  - 继续解 `_ANECCompile(...)`、`ZinCompilerCoreClassic::BuildLayerGraph()`、
    `ANECPrepare(...)`、`ANECCreatePrepareInfoFromMILFile(...)`、
    `CreateMILAndConvert(...)`。
  - 确认 `_ANECCompile` 参数流：
    - `arg0 -> ANECGetCompilerInputs(...)`
    - `arg1 -> ANECGetCompilerOptions(...)`
    - 然后进入 `ANECPrepare(...)`
  - 确认 `BuildLayerGraph()` 直接把 stored procedure dictionary 传入
    `ZinIrFactory::ZinIrFactory(...)`，没有在 classic path 再做一层 rewrite。
  - 确认 `MIL file` 路会经过：
    - `ANECPrepare(...)`
    - `ANECCreatePrepareInfoFromMILFile(...)`
    - `CreateMILAndConvert(...)`
  - 继续在 `CreateMILAndConvert(...)` 中追到：
    - `ANECGetAdditionalWeightFileName(...)`
    - `RetrieveMutableWeightToSymbol(...)`
    - `RetrieveModelSourceInformation(...)`
    - `ANEprivate`
- 证据：
  - `mcp__ida_pro_mcp.disasm(addr=0x222e4bc24)`
  - `mcp__ida_pro_mcp.analyze_function(__ZN22ZinCompilerCoreClassic15BuildLayerGraphEv)`
  - `mcp__ida_pro_mcp.analyze_function(__Z11ANECPrepareR23ZinIrCompilerParametersR27ZinIrPlistCompilationStatus)`
  - `mcp__ida_pro_mcp.analyze_function(__Z32ANECCreatePrepareInfoFromMILFileRK23ZinIrCompilerParametersR27ZinIrPlistCompilationStatus)`
  - `mcp__ida_pro_mcp.analyze_function(__ZL19CreateMILAndConvert...)`
  - `mcp__ida_pro_mcp.analyze_function(__Z31ANECGetAdditionalWeightFileName...)`
  - `mcp__ida_pro_mcp.analyze_batch(RetrieveMutableWeightToSymbol, RetrieveModelSourceInformation)`
- 结论：
  - 当前问题已进一步收敛到 `ANECPrepare/CreateMILAndConvert` 这层。
  - `descriptor.optionsPlist` 不是唯一也不是最前沿的控制面；
    classic compile 在进入 `FillContext(...)` 前使用的 procedure dictionary
    已经由 prepare/lowering 层产出。
  - MIL lowering 还会额外 author：
    - `additional_weights.bin`
    - mutable-weight -> symbol 映射
    - source-information companion
    - `ANEprivate` 相关标记
  - 这比“继续补几个 plist key”更能解释 heterogeneous shared-blob /
    packed public route 的失败与数值偏移。
- 下一步：
  - 继续锁定 `CreateMILAndConvert(...)` 内部真正产出 `ANECProcedureInfo`
    的 helper，确认 procedure dictionary 与 sidecar 的具体字段和落盘/内存形态；
  - 然后再决定是复现该 lowering 产物，还是寻找更低层的 artifact-descriptor
    接口来直接 author 同等 companion state。

- 时间：2026-06-12 08:41:13 +0800
- 目标：把静态的 `CreateMILAndConvert/additional_weights.bin` 结论转成动态证据，
  并确认 compile-side 与 runtime-side 的边界是否已经分离。
- 动作：
  - 直接运行现成 probe：
    - `ane_compiler_service_call_probe` on
      `benchmark_results/private_ane/weighted_fresh_pack_pre_1781215248/model.mil`
    - `ane_client_options_probe` on 生成的
      `dir_mil_retain/output`
    - `ane_hwx_dictionary_probe` on 同一个 `model.hwx`
    - 再对
      `benchmark_results/private_ane/weighted_fresh_pack_ffn_1781216020/model.mil`
      跑一轮 `ane_compiler_service_call_probe`
  - 观察 compile-service 对 file vs directory root 的 contract 差异，
    以及 `additional_weights.bin` 是否真实出现。
- 证据：
  - `mps/ANE/.ane_runs/csv/ane_compiler_service_call_probe_weighted_pre.csv`
  - `mps/ANE/.ane_runs/csv/ane_client_options_probe_weighted_pre.csv`
  - `mps/ANE/.ane_runs/csv/ane_hwx_dictionary_probe_weighted_pre.csv`
  - `mps/ANE/.ane_runs/csv/ane_compiler_service_call_probe_weighted_ffn.csv`
- 结论：
  - `weighted_pre`：
    - `file_empty_options` / `file_coreml_model_type`
      -> lowered `net/xn_ctx_tx_default__0/kraw,qraw,v`
    - `dir_mil_model_type` / `dir_mil_retain`
      -> 原始 `main/x/out@output`
    - `file_mil_model_type`
      -> `InvalidMILProgram`
      -> 留下 `model.hwx.tmp.additional_weights.bin`（当前 0 字节）
    - 生成后的 `model.hwx` 仍只暴露 `NetworkStatusList`
    - `_ANEClient` 回放 wrapper 仍然全部 `programHandle=0`
  - `weighted_ffn`：
    - root 自带 `data` + `net.plist`，compile-service clone 时会原样复制
    - `file_empty_options` / `file_coreml_model_type`
      -> `net/xw_ctx_tx_default__0/out@output`
    - `dir_mil_model_type` / `dir_mil_retain`
      -> 原始 `main/x/out@output`
    - `file_mil_model_type`
      -> 同样留下 `model.hwx.tmp.additional_weights.bin`（0 字节）
  - 这把边界进一步拆成两层：
    1. compile-side：directory-root + MIL route 已能恢复原始 segment contract
    2. runtime-side：visible wrapper 仍不足以建立 runtime `programHandle`
- 下一步：
  - 继续追 `CreateMILAndConvert(...)` 内真正决定
    `ANECProcedureInfo` / `additional_weights.bin` / source companion 的 helper；
  - 同时结合 `model.hwx` 只含 `NetworkStatusList` 这一事实，继续收窄
    runtime-side 缺失的 packaging / descriptor companion。

- 时间：2026-06-12 08:51:39 +0800
- 目标：验证 runtime wrapper 缺的是不是完整 source-root companion 集合，
  并确认 compiled-state 命中后的 second-pass 行为。
- 动作：
  - 给 `weighted_ffn` wrapper 做 7 组 augmentation：
    - baseline
    - `+data`
    - `+net.plist`
    - `+data+net.plist`
    - `+model.mil`
    - `+weights/packed.bin`
    - `+all`
  - 给 `weighted_pre` wrapper 做 4 组 augmentation：
    - baseline
    - `+model.mil`
    - `+weights/packed.bin`
    - `+all`
  - 用现成 `ane_client_options_probe` 批量回放。
  - 给 `ane_client_options_probe.m` 增加 `model_post_compile programHandle`
    插点，并重编译 probe。
  - 对 `weighted_pre/add_all` 做 fresh-root first-pass / second-pass 复测。
- 证据：
  - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_ffn/add_all.csv`
  - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_pre/add_all.csv`
  - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_pre/fresh_lifecycle.csv`
  - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_pre/fresh_lifecycle_second.csv`
  - `mps/ANE/experiments/ane_client_options_probe.m`
- 结论：
  - `weighted_ffn`：
    - 只有 wrapper + `data` + `net.plist` + `model.mil` + `weights/packed.bin`
      同时存在时，`MIL` load 才成功
  - `weighted_pre`：
    - 只有 wrapper + `model.mil` + `weights/packed.bin`
      同时存在时，`MIL` load 才成功
  - fresh root 首次运行：
    - `compiledModelExistsFor = 0`
    - `precompiled compile` 之后 handle 仍是 0
    - `MIL compile` 之后 handle 仍是 0
    - 只有 `MIL load` 之后 handle 才变成 nonzero
  - 同 root 第二次 fresh process：
    - `compiledModelExistsFor = 1`
    - `precompiled compile` 之后 handle 已直接变成 nonzero
    - `precompiled load` 仍返回 0
  - 这说明：
    - runtime-side 缺口已经从“未知 hidden state”收窄到
      “wrapper + source-root companion 集合”
    - compiled-state 的确可复用
    - 但 public `precompiled load` 调用语义仍不正确
- 下一步：
  - 继续追为什么 `precompiled compile` 能建 handle，而 `precompiled load`
    仍返回 0；
  - 评估是否可把 augmentation 自动接到 bridge/cache 路中，
    作为减少重复 `MIL` compile` 的原型。

- 时间：2026-06-12 17:30:00 +0800
- 目标：验证 augmentation wrapper 路是否已经数值对齐 private in-memory baseline，并把 first-pass / second-pass 的 `cacheURLIdentifier` 语义闭环。
- 动作：
  - 给 `mps/ANE/experiments/artifact_replay.m` 补 `out_fnv1a64` 输出并重编译。
  - 重编 `ane_client_options_probe`，复跑：
    - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_pre/eval_probe_rebuilt.csv`
    - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_ffn/eval_probe_rebuilt.csv`
  - 为 `weighted_pre` / `weighted_ffn` 各复制一个 fresh wrapper root，补跑 rebuilt lifecycle：
    - `fresh_lifecycle_rebuilt.csv`
    - `second_lifecycle_rebuilt.csv`
  - 再给 `ane_client_options_probe` 增加 `state/programHandle/cacheURLIdentifier` 插点，重编后对 `weighted_pre` 做 `cacheid_fresh.csv`。
  - 用 `ida-pro-mcp` 新开并反编 `AppleNeuralEngine.i64` / `ANEServices.i64`，重点查看：
    - `+[_ANEVirtualClient shouldUsePrecompiledPath:options:shouldUseChunking:chunkingThreshold:]`
    - `-[_ANEVirtualClient loadModel:options:qos:error:]`
    - `-[_ANEVirtualClient compiledModelExistsFor:]`
    - `+[_ANEModel modelAtURL:key:]`
    - `+[_ANEModel modelAtURLWithSourceURL:sourceURL:key:identifierSource:cacheURLIdentifier:]`
- 证据：
  - `./artifact_replay --artifact benchmark_results/private_ane/weighted_fresh_pack_pre_1781215248 --input-bytes 32768 --output-bytes 65536`
    -> `out_fnv1a64=11324685616637522373`
  - `./artifact_replay --artifact benchmark_results/private_ane/weighted_fresh_pack_ffn_1781216020 --input-bytes 32768 --output-bytes 32768`
    -> `out_fnv1a64=9230850811434127481`
  - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_pre/eval_probe_rebuilt.csv`
  - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_ffn/eval_probe_rebuilt.csv`
  - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_pre/fresh_lifecycle_rebuilt.csv`
  - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_ffn/fresh_lifecycle_rebuilt.csv`
  - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_pre/cacheid_fresh.csv`
  - `AppleNeuralEngine.i64` sessions:
    - `appleneuralengine_i64`
    - `aneservices_i64`
- 结论：
  - augmentation wrapper 路已经越过“只是能 eval”的阶段：
    - `weighted_pre` / `weighted_ffn` 上，
      `modelAtURL:key:` + wrapper-companion + `MIL load/eval`
      的 hash 与 private in-memory baseline 完全一致。
  - 但 `weighted_pre` 上，
    `modelAtURLWithSourceURL:...cacheURLIdentifier:` 仍给出不同 hash，
    说明 `cacheURLIdentifier` 相关 model 构造/加载路径不是数值中性的。
  - fresh root 首次运行时：
    - `empty` 与 `precompiled` 都不能建立 handle，且 `cacheURLIdentifier=nil`
    - `MIL compile` 首次把 `cacheURLIdentifier` 变成非空
    - 只有 `MIL load` 才把 `state` 推到 3 并生成 nonzero `programHandle`
  - 静态上：
    - `compiledModelExistsFor:` 成功时会回写 `cacheURLIdentifier`
    - `loadModel:` 在无 cache id 时会带额外 serializer blob；有 cache id 时改走 cache-id 字典键
    - `shouldUsePrecompiledPath(...)` 真正要求 `.hwx` file URL，不接受当前 wrapper directory root
  - 因而当前最合理的 bridge/cache 原型不是“直接 public precompiled load wrapper dir”，而是：
    1. first-pass 用 `modelAtURL:key:` 对 wrapper root 做 `MIL compile + MIL load`
    2. 让系统生成并保留 compiled cache id
    3. second-pass 再研究如何只靠 compiled-state / warm load 复用
- 下一步：
  - 在 bridge/cache 主路径里做一个最小 augmentation wrapper 原型：
    - first-pass 强制 `modelAtURL:key:` + `MIL`
    - 不预置 `cacheURLIdentifier`
    - second-pass 先用 `compiledModelExistsFor:` / warm empty load 试复用
  - 用同样的 hash 插点验证 bridge 原型不会退回 `modelAtURLWithSource...cacheid` 那条错误的 `pre` 路。

- 时间：2026-06-12 18:45:00 +0800
- 目标：把已验证数值正确的 wrapper+MIL 路接进 bridge/cache 主路径，并检查它对 `test_clean.m4a` 的真实收益。
- 动作：
  - 在 `mps/maderix_ANE/bridge/ane_bridge.m` 中新增 opt-in 路线：
    - `ANE_BRIDGE_CLIENT_FILE_WRAPPER=1`
    - packed source root 自动补：
      - `model.mil`
      - `net.plist`
      - `data`
      - `weights/packed.bin`
    - compiler-service wrapper 生成
    - `modelAtURL:key:` + `MIL compile/load`
    - warm `compiledModelExistsFor` + empty load 复用
  - 修正 bridge 原型一个关键 bug：
    - wrapper 的 `tmp/clone/output` 不能放进 source root 本身；
      已改成 source root 外侧 sibling work dir，再把
      `model.hwx/model.src/model.retain` 回填回来。
  - 增加失败时 `ANE_BRIDGE_KEEP_TMPDIR=1` 保留 tmpdir，便于直接检查 source/wrapper 产物。
  - 用 `private_ane_real_block_probe.py` 做单 block smoke，确认：
    - `pre/gate/ffn` 三段都命中
      `bridge_profile_route = load_cache_client_wrapper_warm`
    - 误差：
      - `mean_abs = 0.00242822128`
      - `max_abs = 0.0151367188`
  - 用 `test_clean.m4a` 做整链 benchmark：
    1. cold onechunk first-pass：
       - `test_clean_wrapper_route_onechunk.private_ane_child/parent_watchdog_failure.json`
       - 证明 cold wrapper populate 仍可能超时
    2. warm onechunk rerun：
       - `test_clean_wrapper_route_onechunk_rerun2.json`
       - `24.520s`
    3. explicit full-audio batch1：
       - `test_clean_wrapper_route_fullaudio_batch1.json`
       - `47.197s`
    4. explicit full-audio batch4：
       - `test_clean_wrapper_route_fullaudio_batch4.json`
       - `28.340s`
    5. 再补 `mlx_full` 对照：
       - `test_clean_wrapper_route_fullaudio_batch4_vs_mlx.json`
- 证据：
  - `benchmark_results/private_ane/test_clean_wrapper_route_onechunk.private_ane_child/parent_watchdog_failure.json`
  - `benchmark_results/private_ane/test_clean_wrapper_route_onechunk_rerun2.json`
  - `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch1.json`
  - `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4.json`
  - `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4_vs_mlx.json`
- 结论：
  - wrapper-route bridge 原型不是“纸面可行”，而是已经在真实 pipeline 上工作。
  - warm cache 条件下，`test_clean.m4a` 已从当前主线参考约 `61.95s`
    压到 `28.34s`，明显低于先前 `43s` 量级。
  - `mlx_full` 对照下：
    - `baseline = 12.131s`
    - `private_ane = 30.186s`
    - `mean_abs = 7.473684963770211e-04`
    - `max_abs = 0.011783935129642487`
    - 整链正确性仍然可接受。
  - 当前最主要的剩余问题不再是 warm-route 是否成立，而是：
    1. cold wrapper populate 仍过重
    2. warm-route 的主要 bridge 开销已经从 file-write 转到 `load_qos`
- 下一步：
  - 优先拆 warm `load_qos` 里还在重复做什么；
  - 同时考虑把 cold wrapper populate 迁成显式预热/离线准备，而不是首个 batch 内现做。

- 时间：2026-06-12 13:07:28 +0800
- 目标：确认当前是否还需要额外安装/切换其它 IDA MCP，并把 warm `load_qos`
  的静态追链入口收敛到正确 framework。
- 动作：
  - 直接调用当前会话内的 `ida_pro_mcp.idb_list`，确认 MCP 已可用。
  - 重新打开：
    - `ANECompiler.i64`
    - `ANEServices.i64`
    - `AppleNeuralEngine.i64`
  - 对 `doLoadModel/loadModel/compiledModelExistsFor/modelAtURL/_ANEInMemoryModelDescriptor`
    做名称检索与反编译。
- 证据：
  - `ida_pro_mcp.idb_list` 已返回活动/可打开 session。
  - `AppleNeuralEngine.i64` 中命中：
    - `-[_ANEClient doLoadModel:options:qos:error:]`
    - `-[_ANEVirtualClient loadModel:options:qos:error:]`
    - `-[_ANEClient compiledModelExistsFor:]`
    - `-[_ANEDaemonConnection loadModel:sandboxExtension:options:qos:withReply:]`
    - `+[_ANEModel modelAtURL:key:]`
    - `+[_ANEModel modelAtURLWithSourceURL:sourceURL:key:cacheURLIdentifier:]`
    - `+[_ANEInMemoryModelDescriptor modelWithMILText:weights:optionsPlist:]`
- 结论：
  - 当前不需要额外切到 `mrexodia/ida-pro-mcp` 或 `blacktop/ida-mcp-rs`；
    本会话里的 `ida_pro_mcp` 已经够用，而且已经能直接追
    `AppleNeuralEngine.framework` 的 runtime load 主链。
  - 若下一轮继续拆 warm `load_qos`，重点应放在
    `AppleNeuralEngine.i64`，不是 `ANECompiler/ANEServices`。
- 下一步：
  - 继续围绕 `-[_ANEClient doLoadModel:options:qos:error:]` 与
    `-[_ANEVirtualClient loadModel:options:qos:error:]`
    拆 warm path 里仍重复发生的 remote call / qos / state update。

- 时间：2026-06-12 13:37:49 +0800
- 目标：判断当前 warm `load_qos` 还值不值得继续围绕 `compiledModelExistsFor` 和
  `TMPDIR` 做文章，并确认真正的 precompiled/file-model 边界现在卡在哪里。
- 动作：
  - 新增最小动态 probe：
    - `mps/ANE/experiments/ane_wrapper_warm_load_probe.m`
    - 输出保存到：
      `benchmark_results/private_ane/wrapper_warm_load_probe_external_time_root.json`
  - 对真实 transformer wrapper root 做四类对照：
    1. `loadModel(MIL)`
    2. `compileModel(MIL) + loadModel(MIL)`
    3. `.hwx file URL + sourceURL` + `loadModel(precompiled)`
    4. 上述 precompiled file route 前先做 `compiledModelExistsFor`
  - 用 `ida_pro_mcp` 继续静态确认：
    - `+[_ANEModel modelAtURL:key:]`
    - `+[_ANEModel modelAtURLWithSourceURL:sourceURL:key:cacheURLIdentifier:]`
    - `+[_ANEVirtualClient shouldUsePrecompiledPath:options:shouldUseChunking:chunkingThreshold:]`
  - 再做两个 `test_clean.m4a` full-audio batch4 benchmark：
    - internal tmpdir cold first-run
    - internal tmpdir second warm-run
- 证据：
  - `benchmark_results/private_ane/wrapper_warm_load_probe_external_time_root.json`
  - `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4_tmp_internal.json`
  - `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4_tmp_internal_rerun.json`
  - `AppleNeuralEngine.i64`：
    - `+[_ANEVirtualClient shouldUsePrecompiledPath:options:shouldUseChunking:chunkingThreshold:]`
    - `-[_ANEClient connectionForLoadingModel:options:]`
- 结论：
  - `compiledModelExistsFor` 不是当前热点：
    - `~0.00015s - 0.00035s`
  - 当前 directory-root wrapper-route 不是“真正的 precompiled path”：
    - 静态上只有 `.hwx` file URL + `kANEFModelPreCompiled`
      才会命中 `shouldUsePrecompiledPath(...)`
  - 但当前真正的 `.hwx file-model precompiled load` 仍然失败：
    - `Code=6`
    - `Program load failure (0x170004)`
    - 说明还缺 file-model 所需的 cache-id / aot-cache-id / companion /
      descriptor 级语义，不能直接迁移 bridge
  - `private_ane_cache_tmpdir=/tmp/...` 也不是当前现成收益：
    - cold first-run `142.387s`
    - second warm-run `55.524s`
    - 都差于当前外置盘 warm-run `28.340s`
  - `compileModel(MIL)+loadModel(MIL)` 与直接 `loadModel(MIL)` 总时长接近，
    当前不值得把“删 compileModel”当作主要性能方向。
- 下一步：
  - 继续围绕 `.hwx file-model precompiled load -> 0x170004` 追字段来源与缺失 companion，
    不再把 `compiledModelExistsFor` 或 `TMPDIR` 迁移当主线。

- 时间：2026-06-12 13:56:39 +0800
- 目标：确认 `.hwx file-model precompiled load` 卡住时，问题是否还停留在
  cache-id / aot-cache-id / attrs / path 这一层，还是已经更低。
- 动作：
  - 新增 probe：
    - `mps/ANE/experiments/ane_precompiled_file_route_probe.m`
    - 结果：
      `benchmark_results/private_ane/precompiled_file_route_probe_time_root_v4.json`
  - 在同一 tmp work root 上先做 working `MIL compile/load`，拿到真实：
    - `cacheURLIdentifier`
    - `modelAttributes`
    - `string_id`
  - 再对 `.hwx file-model` 试：
    - constructor:
      - `modelAtURL:key:`
      - `modelAtURL:key:modelAttributes:`
      - `modelAtURLWithSourceURL(... cacheId=nil/set, identifierSource=1/2)`
      - `modelAtURLWithCacheURLIdentifier(...)`
    - options:
      - `kANEFModelType=kANEFModelPreCompiled`
      - `kANEFModelHasCacheURLIdentifierKey`
      - plain `aotCacheUrlIdentifier`
      - constant `kANEFAOTCacheUrlIdentifierKey`
      - `seed_attrs`
      - `seed_string_id`
    - 以及 `compileModel(precompiled)` 后再 `loadModel(precompiled)`
  - 复制本机 `/usr/libexec/aned` 到仓库内并用 `ida_pro_mcp` 打开
    `aned_bin.i64`，静态分析：
    - `-[_ANEProgramForLoad createProgramInstanceForModel:...cacheUrlIdentifier:aotCacheUrlIdentifier:...]`
    - `-[_ANEModelCacheManager cacheURLIdentifierForModel:useSourceURL:withReply:]`
    - `-[_ANEModelCacheManager URLForModel:bundleID:useSourceURL:forAllSegments:aotCacheUrlIdentifier:]`
- 证据：
  - `benchmark_results/private_ane/precompiled_file_route_probe_time_root_v4.json`
  - `mps/ANE/experiments/aned_bin`
  - `aned_bin.i64` analysis via `ida_pro_mcp`
- 结论：
  - `.hwx file-model precompiled load` 当前不是“缺少某个明显的高层 key”：
    - 真实 `cacheURLIdentifier`
    - `kANEFAOTCacheUrlIdentifierKey`
    - `seed_attrs`
    - `seed_string_id`
    - `compileModel(precompiled)` 预热
    全部不足以让 load 成功。
  - `compiled_exists_before = true` 的 case 也仍会失败，说明单纯 cache lookup
    已经打通，但 program instance materialization 仍失败。
  - `aned` 静态进一步确认：
    - `cacheURLIdentifierForModel...` 只是 `hex(path)+hex(key)` 生成器
    - `URLForModel...` 在 model 已带 cache id 时会直接按 cache id 出 root
  - 因而当前阻塞已基本下沉到：
    - `_ANEProgramForLoad createProgramInstance...`
    - 以及其更低一层的 ProgramDefinition / retained companion author 语义
    - 不是高层 path/cache-id/attrs sweep。
- 下一步：
  - 继续追 `createProgramInstance...` 的 block 真身和更下游 request/program
    materialization，优先寻找 `.hwx/.src/.retain` 之外仍缺的 companion /
    program-definition 语义。

- 时间：2026-06-12 14:18:00 +0800
- 目标：把 `.hwx file-model precompiled load` 的阻塞继续往 daemon lower path
  收敛，确认它是否已经低于 cache/path 层。
- 动作：
  - 新增 probe：
    - `mps/ANE/experiments/ane_precompiled_file_route_probe.m`
    - 结果：
      `benchmark_results/private_ane/precompiled_file_route_probe_time_root_v4.json`
  - 在同一 tmp work root 上先做 working `MIL compile/load`，
    拿到真实：
    - `cacheURLIdentifier`
    - `modelAttributes`
    - `string_id`
  - 对 `.hwx file-model` 再加了：
    - `modelAtURL:key:modelAttributes:`
    - `seed_attrs`
    - `seed_string_id`
    - `kANEFAOTCacheUrlIdentifierKey`
    - `aotCacheUrlIdentifier`
    - `compileModel(precompiled)` 后再 `loadModel(precompiled)`
  - 把本机 `/usr/libexec/aned` 复制到：
    - `mps/ANE/experiments/aned_bin`
    - 并在 `ida_pro_mcp` 中打开 `aned_bin.i64`
  - 静态拆出：
    - `-[_ANEServer loadModel:sandboxExtension:options:qos:withReply:]`
    - `-[_ANEProgramForLoad createProgramInstanceForModel:...cacheUrlIdentifier:aotCacheUrlIdentifier:...]`
    - 其 `dispatch_sync` block 真身 `0x10000307f`
- 证据：
  - `benchmark_results/private_ane/precompiled_file_route_probe_time_root_v4.json`
  - `mps/ANE/experiments/aned_bin`
  - `aned_bin.i64` analysis
- 结论：
  - 就算给 `.hwx file-model` 注入：
    - 真实 `cacheURLIdentifier`
    - `kANEFAOTCacheUrlIdentifierKey`
    - `modelAttributes`
    - `string_id`
    - `compileModel(precompiled)` 预热
    也仍然 `0 success`.
  - `aned` lower block 已确认：
    - 会把 `modelPath / modelIdentityStr / aotCacheUrlIdentifier / cacheUrlIdentifier`
      拷进本地请求缓冲
    - 会从 `modelToken` 里额外取：
      - `teamIdentity`
      - `csIdentity`
      并各自做 SHA 填进 lower request
    - 最后通过 `controller.device` 的 vtable `+0x10` 进入真正的 lower create path
  - 因而当前阻塞已经非常像：
    - `modelToken / ProgramDefinition / retained companion`
      这层 lower author 语义缺失
    - 而不是 cache/path/options 高层问题
- 下一步：
  - 继续从 `-[_ANEServer loadModel...withReply:]` 往上看是谁构造
    `modelToken/modelIdentityStr/modelFilePath`，
    并围绕这些字段设计下一轮更贴近 lower path 的 probe。

- 时间：2026-06-12 14:33:06 +0800
- 目标：确认 `aned loadModel` 内部到底在什么条件下走
  `compileAsNeededAndLoadCachedModel...`，以及 direct create-program
  还真实消费哪些 options 字段。
- 动作：
  - 继续使用当前 `ida-pro-mcp` 会话，直接静态分析：
    - `-[_ANEServer loadModel:sandboxExtension:options:qos:withReply:]`
    - `-[_ANEProgramForLoad createProgramInstanceForModel:...cacheUrlIdentifier:aotCacheUrlIdentifier:...]`
  - 对 `loadModel` 做分段反汇编，确认：
    - precompiled / existsInCache 分支
    - `createProgramInstance...` 调用点的 stack-arg 来源
  - 本地 grep 对照现有 probe，确认
    `ane_precompiled_file_route_probe.m` 目前还没有扫
    `kANEFModelIdentityStrKey / kANEFSkipPreparePhaseKey /
     kANEFEnableLateLatchKey / kANEFEnablePowerSavingKey /
     kANEFKeepModelMemoryWiredKey`
- 证据：
  - `aned_bin.i64` via `ida-pro-mcp`
  - `docs/ane_state.md`
  - `docs/ane_next.md`
  - `mps/ANE/experiments/ane_precompiled_file_route_probe.m`
- 结论：
  - `aned` 里现在已经可以静态确认：
    - 只有 `existsInCache == 0 && isPreCompiled == 0`
      才走 `compileAsNeededAndLoadCachedModel...`
    - 只要 `existsInCache == 1 || isPreCompiled == 1`
      就会 `memoryMapModelAtPath(...)` 后直接走
      `createProgramInstance(...)`
  - 因而当前 `.hwx file-model precompiled load` 的失败，不该再被描述成
    “compile-as-needed / cache-id 还没对上”；它已经是明确的 lower
    create-program 阶段问题。
  - `loadModel...` 对 direct create-program 额外消费的 options 也已明确一批：
    - `kANEFModelIdentityStrKey`
    - `kANEFSkipPreparePhaseKey`
    - `kANEFEnableLateLatchKey`
    - `kANEFEnablePowerSavingKey`
    - `kANEFKeepModelMemoryWiredKey`
    - `kANEFAOTCacheUrlIdentifierKey`
  - 其中 `kANEFModelIdentityStrKey` 是本轮最值得补到 probe 的新字段，
    因为此前主要只扫了 cache-id / attrs / string_id。
- 下一步：
  - 先把 `ane_precompiled_file_route_probe.m` 扩成最小 direct-create
    参数矩阵，优先补 `modelIdentityStr / skipPreparePhase / enableLateLatch /
    enablePowerSaving / keepModelMemoryWired`，观察 `.hwx precompiled`
    的错误面是否从 `0x170004` 发生变化。

- 时间：2026-06-12 14:33:06 +0800
- 目标：验证 `loadModel...` 静态里新确认的 direct-create options
  （`modelIdentityStr / skipPrepare / lateLatch / powerSaving / keepWired`）
  是否能改变 `.hwx precompiled` 的失败面。
- 动作：
  - 修改：
    - `mps/ANE/experiments/ane_precompiled_file_route_probe.m`
  - 新增 helper：
    - `model_hwx_path(...)`
    - `short_model_identifier_for_work_root(...)`
    - `identity_value_for_variant(...)`
  - 在 probe 里补上：
    - `kANEFModelIdentityStrKey`
      - `""`
      - `ane_precompiled_file_route_probe_root/model.hwx`
      - full `.hwx` path
      - `cacheURLIdentifier`
      - decimal `"0"`（bootstrap `string_id`）
    - `kANEFSkipPreparePhaseKey`
    - `kANEFEnableLateLatchKey`
    - `kANEFEnablePowerSavingKey`
    - `kANEFKeepModelMemoryWiredKey`
  - 保留旧 `rows` sweep，同时新增 targeted `direct_rows`：
    - factory:
      - `file_source_cache_set`
      - `file_source_id2_cache_set`
  - 编译并运行：
    - `clang -fobjc-arc -framework Foundation -o /tmp/ane_precompiled_file_route_probe mps/ANE/experiments/ane_precompiled_file_route_probe.m`
    - `/tmp/ane_precompiled_file_route_probe <wrapper_root> > benchmark_results/private_ane/precompiled_file_route_probe_time_root_v5.json`
- 证据：
  - `benchmark_results/private_ane/precompiled_file_route_probe_time_root_v5.json`
  - `mps/ANE/experiments/ane_precompiled_file_route_probe.m`
- 结论：
  - direct-create 新矩阵没有带来任何正向变化。
  - `has_cache_flag + aot_const + seed_attrs + seed_string_id`
    这一族在 22 条 `direct_rows` 上全部仍是：
    - `load_ok = false`
    - `load_error = nil`
    - `after_load.state = 5`
    - `after_load.programHandle = 0`
    - `compile_ok = true`
    - `load_after_compile_ok = false`
  - 去掉 `has_cache_flag` 的两条
    `aot_const + seed_attrs + seed_string_id + identity_short_model`
    仍然稳定报：
    - `Program load failure (0x170004)`
  - 因此当前阻塞再次收敛：
    - 不只是 `cache-id / aot-cache-id / attrs / string_id`
    - 连 `modelIdentityStr / skipPrepare / lateLatch / powerSaving / keepWired`
      这些 `loadModel...` 明确消费的 direct-create 参数也不够
    - 更像是：
      - `modelToken` 绑定关系
      - `ProgramDefinition` / retained companion
      - 或更低 selector-3 create-program descriptor 合同
- 下一步：
  - 不再继续主要扫高层 load options。
  - 继续往下追：
    - `_ANEModelToken tokenWithAuditToken:modelIdentifier:processIdentifier:`
      的 `modelIdentifier` 语义
    - `_ANEServicesProgramCreate` / selector-3 create descriptor
    - `.retain/.src/.hwx` 之外是否还缺 lower companion / manifest

- 时间：2026-06-12 15:35:14 +0800
- 目标：把 selector-3 从“静态已知存在”推进到“本地可 author、可直接调用”的层，并判断当前 daemon 失败是不是 selector-3 字段本身导致。
- 动作：
  - 新开 `ANEServices` IDA 会话：
    - `aneservices_bin`
  - 用 `ida-pro-mcp` 确认：
    - `_ANEServicesProgramCreate`
    - `_ANEServicesDeviceOpen`
    - `ANE::ANEServicesDevice::ANE_ProgramCreate`
    的 ABI/调用链
  - 扩展：
    - `mps/ANE/experiments/ane_ioconnect_trace_interpose.c`
      - 新增 selector-3 输入/输出摘要
      - 新增 selector-3 dump
      - 新增 `IOConnectCallMethod` interpose 路径
  - 修改：
    - `mps/ANE/experiments/ane_precompiled_file_route_probe.m`
      - 新增 `--bootstrap-only`
      - 新增 `--factory` / `--option-variant`
      - 用于隔离 MIL bootstrap 和单个 failing precompiled case
  - 新增 probe：
    - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
      - 先尝试 `ANEServicesDeviceOpen`
      - 若失败，则 fallback 到一个已知成功的 tiny MIL load，
        复用 live `program.controller.device`
      - 在该 live device 上手工 author `0xd88`
        `ANEServicesProgramCreate` request
  - 更新：
    - `mps/ANE/experiments/Makefile`
      - 增加 `ane_services_program_create_runtime_probe`
- 证据：
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v1_notrace.json`
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v2_emptyids.json`
  - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
  - `mps/ANE/experiments/ane_ioconnect_trace_interpose.c`
- 结论：
  - standalone `ANEServicesDeviceOpen` 仍然失败：
    - mode=1 -> `0x4`
    - mode=2 -> `0x18`
  - 但复用 tiny MIL live `controller.device` 后，
    本地 `ANEServicesProgramCreate` 已经可以直接 success：
    - `model.hwx` bytes + `is_precompiled=1` -> `status=0`
    - `data` bytes + `is_precompiled=1` -> `status=0`
    - `model.hwx` bytes + `is_precompiled=0` -> `status=0`
    - `data` bytes + `is_precompiled=0` -> `status=0`
  - 更强的是：
    - 即使把 `cache_id / aot_id / model_identity` 全清空，
      上述四个 case 仍然全部 `status=0`
  - 这说明：
    - selector-3 local authoring 已经进入“可直接调用、可稳定 success”的层
    - 当前 daemon `.hwx precompiled load` 的失败，不像是
      selector-3 本身要求这些高层字符串字段
    - 更像卡在：
      - daemon 上层 request/wrapper state
      - live service/device state
      - 或 success 后的 wrapper adoption / writeback
  - 未解点：
    - `ANEServicesProgramDestroy` 对本地新建 program 返回 `0x14`
    - `ane_ioconnect_trace_interpose.dylib` 即使补到 `IOConnectCallMethod`
      仍未抓到 local create probe 的 selector-3 live trace；
      当前 IOKit 入口可能不是现有 interposer 覆盖的导出符号
- 下一步：
  - 优先解释：
    1. local `ANEServicesProgramCreate status=0` 与 daemon `state=5/programHandle=0`
       为什么分叉
    2. local `ANEServicesProgramDestroy -> 0x14` 暗示了什么 wrapper/state 差异
  - 优先从：
    - `_ANEServicesProgramCreate` 成功返回后的 `out_program` 包装层
    - daemon `createProgramInstance...` 成功分支写回链
    - live service/device state
    继续往下追。

- 时间：2026-06-12 15:35:14 +0800
- 目标：判断 daemon `.hwx precompiled` 的失败是否已经从 selector-3 create
  本身上移到 create 后 wrapper/program-state gate。
- 动作：
  - 用 `ida-pro-mcp` 继续分析：
    - `_ANEServicesProgramDestroy`
    - `_ANEServicesProgramPrepare`
  - 在
    `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
    中补：
    - `out_program` wrapper snapshot
    - payload `qword/u32` 快照
    - local `ANEServicesProgramPrepare`
    - local `ANEServicesProgramDestroy`
  - 结果文件：
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v3_prepare.json`
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v4_prepareflags.json`
- 证据：
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v4_prepareflags.json`
  - `ANEServices` IDA session `aneservices_bin`
- 结论：
  - local `ANEServicesProgramCreate` 的四个 case 仍然全部 `status=0`
  - 但 create 之后立刻：
    - `ANEServicesProgramPrepare -> 0x14`
    - `ANEServicesProgramDestroy -> 0x14`
    - 对 `model.hwx/data`、`is_precompiled=1/0` 全都一致
  - 这说明当前 local selector-3 success 还不是“可被 wrapper 正常 adopt 的
    runtime program”：
    - create call 成功
    - create 后的 wrapper/program-state gate 仍拒绝
  - 因而 daemon `.hwx precompiled load` 失败现在更像是：
    - create 后的 wrapper state / prepare gate
    - 而不只是 selector-3 输入字段 author
  - 当前 local created wrapper 已见到的可对照字段：
    - `qword0_vtable = 0x1f6a59e68`
    - `payload_u32_0x20 = 1`
    - `payload_u32_0x24 = 0`
    - `payload_qword2 = 0x0000000000114000`
    - 值得下一轮直接和 prepare/destroy 的前置 gate 对位
- 下一步：
  - 直接把 local `out_program` payload state 与
    `_ANEServicesProgramPrepare/_Destroy` 静态 gate 对起来
  - 如果对上，就可以更有把握证明 daemon `.hwx precompiled`
    不是卡在 selector-3 create，而是卡在 create 后 adopt / prepare。

- 时间：2026-06-12 17:33:18 +0800
- 目标：验证 local selector-3 create 之后，当前阻塞是否只是 visible
  `programHandle/queueDepth` 或 wrapper `prepareArgs` 缺失。
- 动作：
  - 修复并重编
    `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
  - 给 probe 补：
    - 成功 tiny MIL path 的 live runtime graph 落盘
      (`_ANEProgramForEvaluation` / `_ANEDeviceController` ivars、
      `programHandle`、`queueDepth`、`controller.device`)
    - local created wrapper 上的 live-handle patch：
      - `wrapper+0x70`
      - `payload+0xda8`
      - `wrapper+0xa8.low32`
    - isolated wrapper `prepareArgs` non-zero 变体
  - 新结果文件：
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v12_livegraph_handlepatch.json`
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v14_wordargs_isolated.json`
  - 用 `ida-pro-mcp` 复核：
    - `_ANEServicesProgramPrepare`
    - `_ANEServicesProgramDestroy`
- 证据：
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v12_livegraph_handlepatch.json`
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v14_wordargs_isolated.json`
  - `aneservices_bin::_ANEServicesProgramPrepare`
  - `aneservices_bin::_ANEServicesProgramDestroy`
- 结论：
  - 成功 tiny MIL path 的 visible runtime graph 已确认：
    - `_ANEProgramForEvaluation._programHandle = nonzero`
    - `_ANEProgramForEvaluation._queueDepth = 127`
    - `_ANEDeviceController._programHandle` 与 program 一致
    - `_ANEDeviceController._device` 可稳定给出 live `ANEDeviceStruct *`
  - 但对 local create wrapper：
    - 在 `owner_state=0 + service_ready=1` 后，
      `prepare1` 稳定从 `0x14` 推进到 `0x02`
    - 再回填 live `programHandle / queueDepth` 到
      `wrapper+0x70 / payload+0xda8 / wrapper+0xa8.low32`
      后，`prepare1` 仍然稳定 `0x02`
    - raw prepare 也稳定不变：
      `0xe00002c2`
  - isolated `prepareArgs` non-zero 变体也已证伪：
    - `prepare1_wordargs -> 0x14`
    - `prepare1_owner0_ready1_wordargs -> 0x02`
    - `prepare1_owner0_ready1_handlepatch_wordargs -> 0x02`
  - 因此当前阻塞已进一步收窄：
    - 不是 wrapper `prepareArgs` 全零
    - 不是 visible `programHandle / queueDepth` 缺失
    - 当前最像缺的是 prepare success-side shadow / writeback group：
      - `wrapper+0x98`
      - `payload+0xd98`
      - `payload+0xd78..0xd90`
    - 或更低一层 selector-4 / device-side accepted state
- 下一步：
  - 优先追 `Prepare` 成功/失败路径里
    `wrapper+0x98 / payload+0xd98 / payload+0xd78..0xd90`
    的真实读写条件
  - 若 wrapper-visible patch 仍推不动，就把结论升级为：
    当前缺口已下沉到 selector-4 / lower device state，而不是 artifact
    create 后可见 wrapper 字段。

- 时间：2026-06-12 18:17:12 +0800
- 目标：确认当前 local selector-3 success 到底有没有产出 nonzero
  create-output / program entry，区分“driver 没给 handle”和“wrapper 吞了 handle”。
- 动作：
  - 重新拉起 `ida-pro-mcp` 的 `aneservices_bin` worker
  - 继续反编译：
    - `_ANEServicesProgramCreate`
    - `_ZN3ANE17ANEServicesDevice17ANE_ProgramCreateEP20ANEProgramCreateArgsP26ANEProgramCreateArgsOutput`
  - 在
    `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
    中接入 raw selector-3 helper
  - 用当前进程直接跑 probe，读取 stdout JSON 中：
    - `raw_create_fn`
    - `raw_create_status_hex`
    - `raw_create_output_after`
- 证据：
  - `aneservices_bin::_ANEServicesProgramCreate`
  - `aneservices_bin::_ZN3ANE17ANEServicesDevice17ANE_ProgramCreateEP20ANEProgramCreateArgsP26ANEProgramCreateArgsOutput`
  - 进程内直跑：
    `mps/ANE/experiments/ane_services_program_create_runtime_probe ...`
- 结论：
  - raw selector-3 lower C++ 入口已确认：
    - `a1 = servicesDevice`
    - `a2 = 0xd88 create args`
    - `a3 = 0xac738 output`
    - preflight 只要求：
      - `servicesDevice+0x40 != 0`
      - `servicesDevice+0x18 == 1`
      - `output != nil`
  - 当前进程内直跑 probe 已确认：
    - `raw_create_fn = 0x1a4e5107c`
    - `raw_create_status_hex = 0x00000000`
    - 但 `ANEProgramCreateArgsOutput` 头部仍全零：
      - `qword0/qword1/qword2/qword3 = 0`
      - `qword_0xac6f8/qword_0xac708 = 0`
      - `u32_0x2b140/u32_0x2b14c = 0`
  - 同一 case 上 wrapper 仍然：
    - `wrapper+0x70 = 0`
    - `payload+0xda8 = 0`
  - 这把问题进一步压到 selector-3 output 层：
    - 当前 local selector-3 `status=0` 还不等于
      create-output 已 materialize nonzero runtime entry
    - 问题不像是 wrapper 吞掉了 nonzero handle
    - 更像是当前 create request / artifact 还没有满足 lower output
      populate 的真正前置条件
- 下一步：
  - 继续沿
    `ANEProgramCreateArgsOutput -> ANEProgramCreateAdditionalParams -> ANE_ProgramInitialSetup`
    追 output populate / handoff
  - 优先解释：
    为什么 raw create `status=0` 时 output 仍全零。

- 时间：2026-06-12 19:02:19 +0800
- 目标：把 raw selector-3 `status=0` 但 output 全零这一现象继续往下压，
  判断卡在 handoff、本体 populate，还是更早的 ProgramLoad/process gate。
- 动作：
  - 修正并验证 `ane_services_program_create_runtime_probe` 中
    raw selector-3 `dlsym` / stdout 直跑结果
  - 确认当前进程内直跑下：
    - `raw_create_fn = 0x1a4e5107c`
    - `raw_create_status_hex = 0x00000000`
    - `ANEProgramCreateArgsOutput` 深偏移仍全零
  - 为 bootkc probes 建本地专用 venv：
    - `/Volumes/2T/pymss/.venv_bootkc`
    - 安装 `capstone`
  - 重跑 fresh probes：
    - `ane_bootkc_output_handoff_probe.py`
    - `ane_bootkc_493a0_materialization_probe.py`
- 证据：
  - 进程内直跑
    `mps/ANE/experiments/ane_services_program_create_runtime_probe`
  - `mps/ANE/.ane_runs/csv/ane_bootkc_output_handoff_probe_fresh.csv`
  - `mps/ANE/.ane_runs/csv/ane_bootkc_493a0_materialization_probe_fresh.csv`
- 结论：
  - raw selector-3 create 目前最强事实仍是：
    - `status = 0`
    - output 头部与 wrapper 真消费的 deep output 字段仍全零
  - fresh bootkc 证据把问题位置进一步压实：
    - `ANEHWDevice::ANE_ProgramCreate`
      -> `ANEProgramResource::ANE_ProgramInitialSetup`
    - `ANE_ProgramInitialSetup` 成功路径只是把 external output 指针挂到
      `additional_params+0x10`
    - 真正 populate 在更后面的：
      - `ANEProgramLegacyResource::programLoadFromMachoFile`
      - `ANEProgramRTResource::programLoadFromMachoFile`
    - 且这两条 load 路都会先 `bzero(output, 0xac738)` 再继续 helper populate
  - 所以当前 zero-output 现象更像：
    - 还没有真正进入 `ProgramLoad / programLoadFromMachoFile` populate 链
    - 或更早的 `ProgramLoad / ProcessCreate / isProcessValid`
      gate 没满足
  - 当前不再优先怀疑：
    - `additional_params+0x10` handoff 本身
    - prepare wrapper adoption
- 下一步：
  - 继续追
    `ProgramLoad -> ANE_ProcessCreate_gated -> programLoadFromMachoFile`
    这一跳的前置字段与 gate
  - 找到决定是否真正进入 output populate 的最早条件后，
    再回到 user-space probe 做最小 patch。

- 时间：2026-06-12 19:15:00 +0800
- 目标：把 zero-output 现象继续收敛为具体 gate family，而不是泛泛的
  “ProgramLoad 之前某处失败”。
- 动作：
  - 用本地专用 venv 跑 fresh bootkc probes：
    - `ane_bootkc_process_setup_probe.py`
    - `ane_bootkc_is_process_valid_probe.py`
    - `ane_bootkc_resource_gate_table_probe.py`
    - `ane_bootkc_process_state_source_provenance_probe.py`
  - 读取其 fresh CSV，直接抽：
    - firmware setup token 路
    - `resource+0x400d0`
    - `resource+0x493a0`
    - `process+0x203fc`
    - `additional_params+0x18`
- 证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_process_setup_probe_fresh.csv`
  - `mps/ANE/.ane_runs/csv/ane_bootkc_is_process_valid_probe_fresh.csv`
  - `mps/ANE/.ane_runs/csv/ane_bootkc_resource_gate_table_probe_fresh.csv`
  - `mps/ANE/.ane_runs/csv/ane_bootkc_process_state_source_provenance_probe_fresh.csv`
- 结论：
  - `ANE_ProcessCreate_gated` 当前依赖 firmware-issued token workflow：
    - `0x402/0x403`
    - 或 `0x202/0x203`
    - `ANEProcess::create(...)` 只是薄包装，不是 token 真正来源
  - `isProcessValid(mode!=0)` 当前要求：
    - leading resource-validation gate
    - `resource+0x400d0` 非空
    - exact process-pointer membership
    - `process+0x203fc != 2`
  - `ProgramLoad` 当前显式读取：
    - `resource+0x493a0` qword0
    - `[resource+0x400d0] + 0x220`
  - RT `programLoadFromMachoFile` 当前显式写：
    - `resource+0x493a0` qword0 <= `additional_params+0x18`
  - `process+0x203fc` 当前 visible source provenance 里：
    - 没有 visible constant-2 source
    - 没有 visible `0x1b8 / 0x220 / 0x402f0` source
  - 因而当前最像的缺口已具体化为一个 gate family：
    - setup token
    - `additional_params+0x18` / `resource+0x493a0`
    - `resource+0x400d0`
    - process membership
    - `process+0x203fc`
  - 这比“继续猜更多 output 偏移”更接近真正阻塞。
- 下一步：
  - 优先判断 user-space 侧是否存在任何可等价 author：
    - setup token
    - `additional_params+0x18`
    - process-state transition
  - 如果没有，就把阻塞明确升级为：
    当前 descriptor/wrapper 可控层不足以穿过 setup-command /
    process-state gate。

- 时间：2026-06-12 19:28:00 +0800
- 目标：确认现有 repo 内的 user-space visible surface 是否还有明显漏试项，
  还是已经足够支持“当前控制层不够”的硬结论。
- 动作：
  - 回扫现有
    `ane_inmemory_new_instance_probe_*`
    相关 CSV，重点看：
    - `direct_iokit_param_matrix_numeric`
    - `direct_iokit_param_matrix_deep`
    - `services_runtime`
  - 直接比对这些已试 surface 与当前 gate family：
    - `params[0]`
    - `pid tail`
    - `baseModelIdentifier`
    - visible `programHandle`
    - real weight / sha
- 证据：
  - `mps/ANE/.ane_runs/csv/ane_inmemory_new_instance_probe_direct_iokit_param_matrix_numeric.csv`
  - `mps/ANE/.ane_runs/csv/ane_inmemory_new_instance_probe_direct_iokit_param_matrix_deep.csv`
  - `mps/ANE/.ane_runs/csv/ane_inmemory_new_instance_probe_services_runtime.csv`
- 结论：
  - 当前 repo 内 user-space visible surface 已经试得比较完整：
    - `params[0] = known loaded base programHandle`
    - `pid tail = 0`
    - `baseModelIdentifier` 多种来源
    - visible `programHandle` decimal
    - real weight symbol/path/len/bytes
    - real SHA
  - 这些 direct selector-8 变体当前都仍然稳定：
    - `raw_status = 0xe00002c2`
    - `ANEProgramCreateArgsOutput = all zero`
  - 所以当前 machine-local 结论已经足够强：
    - 现有 artifact-descriptor / visible wrapper / visible selector-8
      参数层，基本不足以穿过 lower setup-command /
      resource-process coherence gate
  - 这意味着下一轮如果继续深挖，应明确改成：
    - lower token/resource insertion
    - 或正式产出“当前控制层边界已到”的阻塞证据
- 下一步：
  - 若继续推进，优先转向 lower token/resource insertion；
    不再主要扩展新的 user-space visible 参数 sweep。

- 时间：2026-06-12 19:36:00 +0800
- 目标：把当前“控制层不够”的判断再从 gate family 收缩到
  first unavailable user-space-equivalent surface。
- 动作：
  - 继续读现有 bootkc notes：
    - `bootkc_create_instance_additional_params_probe.md`
    - `bootkc_create_instance_hidden_handle_bridge_probe.md`
    - `bootkc_resource_gate_process_registry_probe.md`
    - `bootkc_create_instance_additional_params_use_scan_note.md`
  - 将这些 lower notes 与
    `ane_inmemory_new_instance_probe_*`
    已试过的 visible surface 做交叉判断
- 证据：
  - `mps/ANE/experiments/results/bootkc_create_instance_additional_params_probe.md`
  - `mps/ANE/experiments/results/bootkc_create_instance_hidden_handle_bridge_probe.md`
  - `mps/ANE/experiments/results/bootkc_resource_gate_process_registry_probe.md`
  - `mps/ANE/experiments/results/bootkc_create_instance_additional_params_use_scan_note.md`
- 结论：
  - visible direct additional-params contract 其实很小：
    - `+0x0`
    - `+0x18`
    - `+0x80`
  - 其中真正关键的新 surface 是：
    - driver/device-authored hidden handle sidecar
      -> `additional_params+0x18`
  - regular visible selector-8 bridge 当前明确是：
    - `x5 = 0`
    - 因而无法直接 seed non-null `additional_params+0x18`
  - 反过来，driver-routed create-instance path 当前明确是：
    - local program-handle slot
    - x5 sidecar
    - block callback dereference
    - `additional_params+0x18 = local_program_handle`
    - lower writeback to `resource+0x493a0[0]` and `params[0]`
  - `resource+0x400d0` 当前也已不再是 opaque object，
    而是 behaves like `OSArray<ANEProcess*>`
  - 因而当前最像的 first unavailable user-space-equivalent surface
    已经可以明确写成：
    - driver/device-authored hidden handle sidecar
      -> `additional_params+0x18`
- 下一步：
  - 若继续推进，优先回答：
    1. selector-3 route 能否构造出与该 hidden handle sidecar 等价的 lower state
    2. 现有 user-space path 中是否存在任何能让 x5 非零的 caller shape
  - 如果两条都没有，就可以把当前控制层边界写得更硬。

- 时间：2026-06-12 19:44:00 +0800
- 目标：把当前阻塞再从“hidden handle sidecar 缺失”细化成
  base-create 与 create-instance 两条路的结构性分叉。
- 动作：
  - 继续对照：
    - `bootkc_output_handoff_probe.md`
    - `bootkc_493a0_key_bridge_probe.md`
    - `bootkc_create_instance_hidden_handle_bridge_probe.md`
  - 重点比较：
    - base create:
      `output -> additional_params+0x10`
    - create-instance:
      `hidden handle -> additional_params+0x18`
- 证据：
  - `mps/ANE/experiments/results/bootkc_output_handoff_probe.md`
  - `mps/ANE/experiments/results/bootkc_493a0_key_bridge_probe.md`
  - `mps/ANE/experiments/results/bootkc_create_instance_hidden_handle_bridge_probe.md`
- 结论：
  - 当前 base-create 路最强证据只到：
    - direct `ANEProgramCreateArgsOutput*`
    - `ANE_ProgramInitialSetup`
    - `additional_params+0x10`
    - later `programLoadFromMachoFile` uses that output pointer
  - 当前 create-instance 路则更深一层：
    - `additional_params+0x18 = driver/device-authored hidden handle`
    - 该值再作为 `local_y`
      参与 `lookupProgramResource(...)`
      并回写到 `resource+0x493a0[0]` / `params[0]`
  - 这条 split 的直接意义是：
    - selector-3/base-create `status=0` 但 output 全零，
      不是简单缺一个 output pointer handoff
    - 更像是 base create 当前没有进入 create-instance 那种
      hidden-handle/key-restore/coherence 路
  - 因而当前阻塞可再写得更硬：
    - base create 与 create-instance 当前并不共享同一层 visible sidecar surface
    - 如果 selector-3 路没有自己的 lower hidden key/sidecar family，
      那么现有 descriptor/wrapper 控制层很可能天然不足以把 base create
      推到 accepted runtime state
- 下一步：
  - 若继续推进，优先判断：
    1. base create 路是否存在自己独立的 hidden key/sidecar family
    2. 若没有，则把当前控制层边界正式表述为：
       visible descriptor/wrapper 层不足以从 selector-3 base-create
       进入 lower runtime coherence 路

- 时间：2026-06-12 19:50:00 +0800
- 目标：把当前 strongest split 再提升为“是否存在 first common seed”的层级，
  为后续是否正式下边界结论做准备。
- 动作：
  - 继续对照：
    - `bootkc_output_handoff_probe.md`
    - `bootkc_493a0_key_bridge_probe.md`
    - `process_resource_key_seed_join_note.md`
  - 重点不是再问“有没有 sidecar”，而是：
    - create-instance 是否已有 process/resource key first common seed
    - base create 是否存在对等闭环
- 证据：
  - `mps/ANE/experiments/results/bootkc_output_handoff_probe.md`
  - `mps/ANE/experiments/results/bootkc_493a0_key_bridge_probe.md`
  - `mps/ANE/experiments/results/process_resource_key_seed_join_note.md`
- 结论：
  - create-instance 路当前已经有 machine-local first common seed：
    - hidden local handle
      -> `additional_params+0x18`
      -> `local_y`
      -> `process_args[8]`
      -> `process+0x20`
      -> `resource+0x493a0[0]`
      -> `params[0]`
  - base create 路当前仍只有：
    - `output -> additional_params+0x10`
    - later `programLoadFromMachoFile` consume that output pointer
    - 但没有对等的 process/resource key first common seed 证据
  - 所以当前 base-create 路阻塞的最硬表述已经变成：
    - 不只是“少一个 hidden sidecar”
    - 而是“缺少把 process/resource key family 共同 seed 起来的
      lower key family”
- 下一步：
  - 若继续推进，直接围绕：
    - base create 是否存在自己独立的 first common seed
  - 若没有，就可以把当前 visible descriptor/wrapper 层边界写成更硬的
    阻塞证据。

- 时间：2026-06-12 20:15:49 +0800
- 目标：修正 base-create 过时结论，并补一条能改变下一步追链方向的 caller 事实。
- 动作：
  - 复核 fresh CSV：
    - `mps/ANE/.ane_runs/csv/ane_bootkc_base_provenance_probe_fresh.csv`
  - 抽取关键 current-machine 指令：
    - `ANEHWDevice::ANE_ProgramCreate`
      - `ldr x8, [x26]` -> `x8 = *(arg5/out_handle_ptr)`
      - `str x1, [x0, #0x18]` -> `additional_params+0x18 = *(arg5/out_handle_ptr)`
    - `ANEProgramResource::ANE_ProgramInitialSetup`
      - `stp x2, x8, [sp, #0xc8]`
      - `str x8, [x20, #0x10]`
  - 用 `.venv_bootkc` 对 `/tmp/KMUtilProducts/BootKernelCollection.kc`
    当前 H16 `__TEXT_EXEC` 做 exact `bl` 扫描，
    专门检查
    `ANEHWDevice::ANE_ProgramCreate`
    的 direct caller。
- 证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_base_provenance_probe_fresh.csv`
  - 本轮命令输出：
    - `target=__ZN11ANEHWDevice17ANE_ProgramCreateEP20ANEProgramCreateArgsP26ANEProgramCreateArgsOutputP4taskPvPy addr=0xfffffe000928b3f4`
    - `exact_bl_callers 0`
- 结论：
  - 之前 docs 里“base create 只看到 `additional_params+0x10`、没见到对等 sidecar”
    已被 fresh 证据推翻。
  - 当前 base create 也会 seed：
    - `additional_params+0x18 = *(arg5/out_handle_ptr)`
  - 因而当前未解点已经进一步收敛为：
    - `arg5/out_handle_ptr` 的上游正来源
  - 同时，`ANEHWDevice::ANE_ProgramCreate`
    在当前 H16 `__TEXT_EXEC` 里没有 exact `bl` caller，
    所以下一轮不应继续优先找普通直调 caller；
    应转去追：
    - selector-3 / dispatch table
    - `ANECoreInterface::ANE_ProgramCreate`
    - `externalMethod` / IOUserClient / vtable 间接入口
- 下一步：
  - 先沿现有 selector/dispatch 证据，
    收敛 `ANECoreInterface::ANE_ProgramCreate`
    到 `ANEHWDevice::ANE_ProgramCreate` 的间接桥。
  - 再判断 `arg5/out_handle_ptr`
    是否在该间接桥里被写成一个 driver-authored slot，
    还是来自更低的 device/runtime author 语义。

- 时间：2026-06-12 21:30:07 +0800
- 目标：确认 selector-3/base-create 的 `arg5/out_handle_ptr`
  是否在 bridge 层已经有 concrete carrier，而不是继续把它当作抽象缺口。
- 动作：
  - 继续拆：
    - `ANE_ProgramCreate`
    - `ANEClientDevice::programCreate(ANEProgramParamsWrapper*)`
    - `ANEDriver::ANE_ProgramCreate`
    - `ANEDriver::ANE_ProgramCreate_gated`
    - `ANEHWDevice::ANE_ProgramCreate`
  - 新增只读 probe：
    - `mps/ANE/experiments/ane_bootkc_base_create_handle_bridge_probe.py`
  - 生成 fresh CSV：
    - `mps/ANE/.ane_runs/csv/ane_bootkc_base_create_handle_bridge_probe_fresh.csv`
- 证据：
  - `ANE_ProgramCreate`：
    - tail-branch 到
      `ANEClientDevice::programCreate(ANEProgramParamsWrapper*)`
  - `ANEDriver::ANE_ProgramCreate`：
    - 只是薄转发：
      - `x5 = x4`
      - `x4 = x3`
      - `x3 = x2`
      - `x2 = x1`
      - 再经 `driver->...->vtable+0x1e8` 进入 gated body
  - `ANEDriver::ANE_ProgramCreate_gated`：
    - `stur xzr, [x29, #-0x58]`
    - `sub x1, x29, #0x58`
    - `bl ANE_CreateProgramHandle_gated`
    - `sub x5, x29, #0x58`
    - provider create slot (`vtable+0x8a0`) dispatch
    - 返回后又：
      - `ldur x1, [x29, #-0x58]`
      - `bl addProgramToANEMapping_gated`
      - 再次 `ldur x1, [x29, #-0x58]`
      - `bl findProgramANEMapping_gated`
  - `ANEHWDevice::ANE_ProgramCreate`：
    - `mov x26, x5`
    - `ldr x8, [x26]`
    - 之后 `additional_params+0x18 = *(arg5/out_handle_ptr)`
- 结论：
  - selector-3/base-create 的 `arg5/out_handle_ptr`
    在 driver 边界并不缺失。
  - 当前 bridge 已经明确：
    - driver 先 author 一个 local program-handle slot
    - 再把 `&local_slot` 作为 `x5`
      传给 device create
    - 同一个 local handle 还会被 driver 侧用于
      mapping registration / lookup
  - 因而当前边界已从：
    - “`arg5/out_handle_ptr` 是否存在 / 谁提供 carrier”
    下沉到：
    - “lower base-create path 为什么没有把这个已存在 local handle
      materialize 成 create-instance 那种
      accepted process/resource coherence”
- 下一步：
  - 继续围绕 base-create 的 local handle
    在 lower path 中的 consume / restore / acceptance，
    重点看：
    - `ANE_CreateProgramHandle_gated`
      产出的 handle 与 create-instance handle family 是否同族
    - `ANEHWDevice::ANE_ProgramCreate_gated` /
      `ProgramLoad` / `ProcessCreate`
      哪一跳没有接住这个 handle

- 时间：2026-06-12 21:33:33 +0800
- 目标：确认 base-create 与 create-instance 的 local handle
  是否共享同一 materialization family，避免后续继续在 handle 生成层绕圈。
- 动作：
  - 并排复核：
    - `mps/ANE/.ane_runs/csv/ane_bootkc_handle_materialization_probe.csv`
    - `mps/ANE/.ane_runs/csv/ane_bootkc_base_create_handle_bridge_probe_fresh.csv`
  - 对照两条路的：
    - local slot 分配
    - `ANEDriver::ANE_CreateProgramHandle_gated`
    - `ANEHWDevice::ANE_ProgramHandleCreate_gated`
    - `lookupProgramResource(...)` collision check
    - publish `*out_handle`
    - `x5 = &local_handle_slot`
- 证据：
  - create-instance：
    - `[sp+0x40]` local slot
    - `bl ANE_CreateProgramHandle_gated`
    - `x5 = sp+0x40`
    - device side handle create：
      `mach_absolute_time()` +
      `lookupProgramResource(candidate, &process, 0)` +
      `str x22, [x20]`
  - base-create：
    - `[x29-0x58]` local slot
    - `bl ANE_CreateProgramHandle_gated`
    - `x5 = x29-0x58`
    - 后续同一个 handle 被用于：
      - `addProgramToANEMapping_gated`
      - `findProgramANEMapping_gated`
    - device side create：
      `mov x26, x5`
      / `ldr x8, [x26]`
- 结论：
  - base-create 与 create-instance 当前共享同一个
    handle materialization family。
  - 因而阻塞不在：
    - handle 生成
    - driver bridge
    - `arg5/out_handle_ptr` carrier
  - 当前真正的 first unresolved divergence
    已下沉到：
    - `additional_params+0x18`
      之后的 lower consumer path
    - 也就是 base-create 为什么没有像 create-instance 那样进入
      `process_args[8] / process+0x20 / resource+0x493a0`
      的 accepted coherence 链
- 下一步：
  - 直接围绕：
    - `ANEHWDevice::ANE_ProgramCreate_gated`
    - `ANE_ProcessCreate_gated`
    - `ProgramLoad`
    做 first divergence 收敛，
    不再优先重复 handle-family 方向。

- 时间：2026-06-12 21:42:59 +0800
- 目标：确认 first divergence
  是否已经早于 `resource+0x493a0` writeback，
  而发生在 `ProgramLoad -> ANE_ProcessCreate_gated`
  的本地 args 组装阶段。
- 动作：
  - 复核现有 notes：
    - `bootkc_process_create_probe.md`
    - `bootkc_create_instance_resource_probe.md`
    - `bootkc_493a0_key_bridge_probe.md`
    - `program_load_state_join_note.md`
  - 新增只读 probe：
    - `mps/ANE/experiments/ane_bootkc_program_load_process_args_probe.py`
  - 生成 fresh CSV：
    - `mps/ANE/.ane_runs/csv/ane_bootkc_program_load_process_args_probe_fresh.csv`
  - 纠正一处中间误判：
    - `0xfffffe0009307870` 不是 `ANE_ProcessCreate_gated`
    - 它是
      `ANEProgramResource::ANE_CleanupResourcesAllocatedForInitialSetup`
- 证据：
  - create-instance 侧已有：
    - `{ qword0 = resource-derived key,
         qword8 = local_y,
         qword10 = client key }`
  - fresh `ProgramLoad` 侧当前可见：
    - Legacy callsite 前：
      - `stp x27, x27, [sp, #0xb8]`
      - `stp x8, xzr, [sp, #0xc8]`
    - RT callsite 前：
      - `stp x8, x8, [sp, #0x58]`
      - `stp x9, xzr, [sp, #0x68]`
  - 即：
    - ProgramLoad 进入 `ANE_ProcessCreate_gated`
      前，
      `qword0/qword8`
      已经 mirror 同一 key family，
      而不是保留 create-instance 的
      `qword8 = local_y`
- 结论：
  - first divergence
    已经早于：
    - later `resource+0x493a0` restore/writeback
    - later `params[0]` internal authoring
  - 当前更早、也更有价值的分叉点是：
    - create-instance：
      `ANE_ProcessCreate_gated` 前仍保留
      `args+0x08 = local_y`
    - base-create/load-side ProgramLoad：
      `ANE_ProcessCreate_gated` 前已经把
      `args+0x08`
      变成与 `qword0`
      同族的 mirror key
  - 这说明当前阻塞最早已不是
    `resource+0x493a0` 的后写回，
    而是 ProgramLoad 对 local process-args 的作者链本身
- 下一步：
  - 直接追：
    - Legacy/RT `ProgramLoad`
      本地 args 的 `qword0/qword8/qword10`
      各自从哪里来
    - 哪个更早的 lower source / record / gate state
      把 `args+0x08`
      从 `local_y`
      变成 mirror key

- 时间：2026-06-12 21:46:20 +0800
- 目标：验证 first divergence 是否已经早于
  `resource+0x493a0` writeback，
  并把下一步入口收敛到 `ProgramLoad` 本地 process-args 的作者链。
- 动作：
  - 新增只读 probe：
    - `mps/ANE/experiments/ane_bootkc_program_load_process_args_probe.py`
  - 生成 fresh CSV：
    - `mps/ANE/.ane_runs/csv/ane_bootkc_program_load_process_args_probe_fresh.csv`
  - 直接抽取 ProgramLoad callsite 小窗口：
    - Legacy:
      `0xfffffe00092fc124 .. 0xfffffe00092fc154`
    - RT:
      `0xfffffe000930a7bc .. 0xfffffe000930a7f0`
- 证据：
  - Legacy:
    - `stp xzr, xzr, [sp, #0xa8]`
    - `stp x27, x27, [sp, #0xb8]`
    - `stp x8, xzr, [sp, #0xc8]`
    - `bl ANE_ProcessCreate_gated`
  - RT:
    - `stp xzr, xzr, [sp, #0x40]`
    - `stp x8, x8, [sp, #0x58]`
    - `stp x9, xzr, [sp, #0x68]`
    - `bl ANE_ProcessCreate_gated`
  - create-instance 既有对照：
    - `{ qword0 = resource-derived key, qword8 = local_y, qword10 = client key }`
- 结论：
  - Legacy/RT `ProgramLoad`
    喂给 `ANE_ProcessCreate_gated`
    的 local args tuple
    已经不同于 create-instance。
  - 当前 first divergence
    不应再表述成“更晚的 `resource+0x493a0` writeback 差异”，
    而应表述成：
    - `ProgramLoad -> local ANEProcessCreateArgs`
      组装阶段已经偏离 create-instance 的
      `local_y` 形态
  - 因而下一步最值钱的问题是：
    - `x27/x8/x9`
      在 ProgramLoad 内各自从哪来，
      为什么会被组装成
      `{same key, same key, separate band}`
- 下一步：
  - 直接沿：
    - Legacy `x27/x8`
    - RT `x8/x9`
    的作者链往前追，
    看哪个更早的 lower source / record / gate state
    把 `args+0x08`
    从 create-instance 的 `local_y`
    改写成 mirror key。

- 时间：2026-06-12 21:50:24 +0800
- 目标：确认 ProgramLoad 的 first-divergence
  是“丢失 local_y”，还是“保留 key family 但改成 mirror-key tuple”。
- 动作：
  - 直接抽取 ProgramLoad 内更早窗口：
    - Legacy:
      `ldr x27, [x19, #0x18]`
      -> later `stp x27, x27, [sp, #0xb8]`
    - RT:
      preserved `additional_params+0x18` family
      -> later `stp x8, x8, [sp, #0x58]`
  - 对照已有 create-instance tuple：
    - `{ resource-derived key, local_y, client key }`
- 证据：
  - Legacy:
    - `0xfffffe00092fb7b8   ldr x27, [x19, #0x18]`
    - `0xfffffe00092fc128   stp x27, x27, [sp, #0xb8]`
  - RT:
    - `0xfffffe0009309fcc   ldp x21, x28, [x23, #0x10]`
    - later `0xfffffe000930a7c4   stp x8, x8, [sp, #0x58]`
  - 结合 `bootkc_493a0_key_bridge_probe.md`
    可知这条 preserved key family 就是
    `additional_params+0x18`
- 结论：
  - ProgramLoad 并没有丢掉
    `additional_params+0x18`
    这条 key family。
  - 它做的是：
    - 把这条 key family
      mirror 到
      `process_args.qword0`
      和
      `process_args.qword8`
  - 因而 first-divergence
    不应再表述成
    “`args+0x08` 变成无关值”，
    而应表述成：
    - create-instance 保留 dual-key 结构
    - ProgramLoad 把 dual-key 结构抹平成
      `{same key, same key, separate band}`
- 下一步：
  - 继续追：
    - 为什么 ProgramLoad 需要这种 mirror-key struct
    - 哪个更早的 lower source / record / gate state
      决定了这种 struct 形态，
      而不是 create-instance 那条
      `resource-key vs local_y`
      双键形态。

- 时间：2026-06-12 21:58:39 +0800
- 目标：把 ProgramLoad mirror-key 结论从 callsite 形态推进到更硬的字段 provenance。
- 动作：
  - 新增只读 provenance probe：
    - `mps/ANE/experiments/ane_bootkc_program_load_args_provenance_probe.py`
  - 生成 fresh CSV：
    - `mps/ANE/.ane_runs/csv/ane_bootkc_program_load_args_provenance_probe_fresh.csv`
  - 重点只追：
    - Legacy:
      `x27`, `sp+0x68`
    - RT:
      `x28`, `x29-0x68`, `sp+0x38`
- 证据：
  - Legacy:
    - `ldr x27, [x19, #0x18]`
    - later `stp x27, x27, [sp, #0xb8]`
    - `str x22, [sp, #0x68]`
    - callsite 前：
      - `qword0/qword8 = preserved additional_params+0x18`
      - `qword10 = *(sp+0x68)`
  - RT:
    - `ldp x21, x28, [x23, #0x10]`
      -> `x28 = *(additional_params+0x18)`
    - `stur x28, [x29-0x68]`
    - later `stp x8, x8, [sp, #0x58]`
      where `x8 = *(x29-0x68)`
    - `ldp x8, x9, [sp, #0x30]`
      then `stp x9, xzr, [sp, #0x68]`
    - callsite 前：
      - `qword0/qword8 = preserved additional_params+0x18`
      - `qword10 = *(sp+0x38)`
- 结论：
  - ProgramLoad 并不是“泛泛地 mirror 某个 key”。
  - 当前更硬的 machine-local 说法是：
    - Legacy/RT 都明确把
      `additional_params+0x18`
      复制成
      `process_args.qword0/qword8`
    - 同时保留第三个独立 band 给 `qword10`
  - 这说明下一步最值得做的不是继续证明
    `qword0/qword8`
    的来源，
    而是去追：
    - `qword10` 的 lower role
    - 以及为什么 lower consumer 需要
      `{same key, same key, separate band}`
      而不是 create-instance 的 dual-key struct
- 下一步：
  - 直接围绕：
    - `ANE_ProcessCreate_gated`
      如何消费 `qword10`
    - 以及 `qword0/qword8` mirror-key
      与 create-instance `local_y`
      在 lower consumer 行为上的差异。

- 时间：2026-06-12 22:05:43 +0800
- 目标：把 ProgramLoad first-divergence 从“mirror-key”推进到精确 tuple。
- 动作：
  - 扩展 provenance：
    - `mps/ANE/experiments/ane_bootkc_program_load_args_provenance_probe.py`
  - 生成 fresh CSV：
    - `mps/ANE/.ane_runs/csv/ane_bootkc_program_load_args_provenance_probe_fresh.csv`
  - 新增总结 note：
    - `mps/ANE/experiments/results/program_load_process_args_tuple_note.md`
- 证据：
  - Legacy:
    - `ldr x27, [additional_params+0x18]`
    - `stp x27, x27, [sp, #0xb8]`
    - `ldr x22, [additional_params+0x0]`
    - `str x22, [sp, #0x68]`
    - callsite 前 tuple：
      `{ additional_params+0x18, additional_params+0x18, additional_params+0x0 }`
  - RT:
    - `ldp x21, x28, [additional_params+0x10/+0x18]`
    - `stur x28, [x29-0x68]`
    - later `stp x8, x8, [sp, #0x58]`
      where `x8 = *(x29-0x68)`
    - `str x20, [sp, #0x38]`
      where `x20` preserves the `additional_params+0x0` band
    - callsite 前 tuple：
      `{ additional_params+0x18, additional_params+0x18, additional_params+0x0 }`
- 结论：
  - ProgramLoad 进入 `ANE_ProcessCreate_gated`
    前的 tuple
    已可精确写成：
    `{ additional_params+0x18, additional_params+0x18, additional_params+0x0 }`
  - 这比此前的
    “same key / separate band”
    更强，因为三个字段来源都已可见。
  - 因而当前最早 semantic divergence
    已可正式表述为：
    - create-instance：
      `{ resource-derived key, local_y, client key }`
    - ProgramLoad：
      `{ additional_params+0x18, additional_params+0x18, additional_params+0x0 }`
- 下一步：
  - 直接追：
    - `additional_params+0x18`
      这条 hidden key family
      在 lower consumer 的角色
    - `additional_params+0x0`
      作为第三个 qword
      在 `ANE_ProcessCreate_gated`
      与更低层扮演什么角色
    - 看这是否就是 ProgramLoad 路和 create-instance 路
      acceptance 行为不同的最早语义原因。

- 时间：2026-06-12 22:14:10 +0800
- 目标：把 `{ additional_params+0x18, additional_params+0x18, additional_params+0x0 }`
  这个 ProgramLoad tuple 和 `ANE_ProcessCreate_gated` 的实际参数语义对齐。
- 动作：
  - 直接展开 `ANEHWDevice::ANE_ProcessCreate_gated`
  - 复核已有 `bootkc_process_create_probe.md`
  - 对照 ProgramLoad / create-instance 两条 callsite
- 证据：
  - `x3 = resource` 非空时，
    `ANE_ProcessCreate_gated`
    会绕过：
    - `lookupProgramResource(args[0], ...)`
      的 fallback 路
  - 但仍会继续用：
    - `args[8]`
      做 secondary
      `lookupProgramResource(args[8], ...)`
    - `args[0x10]`
      做
      `findClient(args[0x10], ...)`
  - 这与 ProgramLoad tuple：
    `{ additional_params+0x18, additional_params+0x18, additional_params+0x0 }`
    是一致的：
    - resource 已由 `x3`
      直接给定
    - 两个 numeric key 位都压成
      hidden key family
      `additional_params+0x18`
    - client key 保持为
      `additional_params+0x0`
- 结论：
  - ProgramLoad tuple 的改写现在更像 lower contract，
    不是 incidental drift。
  - 下一步最值钱的方向不是继续证明 tuple 来源，
    而是：
    - create-instance 的
      `args[8] = local_y`
      与 ProgramLoad 的
      `args[8] = additional_params+0x18`
      在 secondary lookup / acceptance 上
      有什么语义差异
    - `args[0x10] = additional_params+0x0`
      是否只是 client key，
      还是还携带更深的 gate/role 语义

- 时间：2026-06-12 22:18:17 +0800
- 目标：结束“字段是什么”这类低层问题，把 field semantics 固定下来。
- 动作：
  - 交叉核对：
    - `bootkc_create_instance_additional_params_probe.md`
    - `bootkc_process_create_probe.md`
    - `device_client_context_note.md`
    - `program_load_process_args_tuple_note.md`
  - 把 ProgramLoad tuple 与 `ANE_ProcessCreate_gated`
    的实际消费方式对齐
- 证据：
  - `additional_params+0x18`
    已稳定表现为
    hidden numeric key family
  - `additional_params+0x0`
    已稳定表现为
    `pv / client key`
  - `additional_params+0x80`
    已稳定表现为
    task
  - `ANE_ProcessCreate_gated`
    在 `x3=resource` 非空时：
    - 绕过 `args[0]` fallback lookup
    - 但继续消费：
      - `args[8]`
      - `args[0x10]`
- 结论：
  - 当前 field semantics 可视为已收敛：
    - `+0x18` = hidden numeric key
    - `+0x0`  = pv/client key
    - `+0x80` = task
  - 下一步最值钱的工作不再是重新解释字段，
    而是直接比较：
    - `lookupProgramResource(args[8], ...)`
      后的 acceptance 分叉
    - `findClient(args[0x10], ...)`
      后的 client-owned state / role / gate 分叉

- 时间：2026-06-12 22:22:57 +0800
- 目标：把下一轮主线从字段语义正式切到 family-6 acceptance gate。
- 动作：
  - 复核：
    - `bootkc_resource_process_contract_probe.md`
    - `bootkc_resource_gate_process_registry_probe.md`
    - `process_key_coherence_note.md`
    - `newinstance_acceptance_stage_join_note.md`
  - 将 ProgramLoad / create-instance 分叉
    与 family-6 stack 对齐
- 证据：
  - family-6 是当前最合理的 acceptance gap 所在层：
    - 不是 family-3 preflight
    - 不是 family-7 post-create prepare
  - `ANE_ProcessCreate_gated`
    在 `x3=resource` 非空时：
    - 绕过 `args[0]` fallback
    - 继续消费 `args[8]` / `args[0x10]`
  - 当前 lower high-value targets
    已收敛到：
    - `resource+0x400d0` first author
    - `record+0x1b8` durable author
    - `process+0x203fc == 2` decisive author
- 结论：
  - 下轮不再从字段解释开始。
  - 应直接比较：
    - create-instance 的 `args[8] = local_y`
      如何通过 family-6 stack
    - ProgramLoad 的 `args[8] = additional_params+0x18`
      为什么在同一 stack 下
      仍然掉进
      `resource+0x400d0 / process+0x203fc`
      相关 rejection/coherence gate

- 时间：2026-06-13 00:20:14 +0800
- 目标：收紧 family-6 / completion 线里两个仍在漂的低层语义：
  1. completion-side `+0x20400` 到底属于 process 还是 resource
  2. `ANE_SaveState` 是否可能是 visible `state==2` author
- 动作：
  - 复读 `process_state_*`、`legacy_typed_completion_route`、
    `bootkc_resource_gate_*` 现有 notes
  - 用 conda Python + capstone 直接重拉：
    - `ANEHWDevice::ANE_SaveState`
    - `ANEHWDevice::handleOutstandingCommand`
    - `ANEHWDevice::commandWakeup`
    的关键窗口
  - 新增并运行只读 probe：
    - `mps/ANE/experiments/ane_bootkc_completion_process_counter_probe.py`
  - 新增结果 notes：
    - `mps/ANE/experiments/results/completion_process_counter_note.md`
    - `mps/ANE/experiments/results/save_state_entry_flag_note.md`
- 证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_completion_process_counter_probe.csv`
  - 直接反汇编：
    - `handleOutstandingCommand`:
      - `bl lookupProgramResource(inner+0x68, &process, 0)`
      - `matched_process+0x20400 --`
      - `bl commandWakeup(device, matched_process+0x20400)`
    - `ANE_SaveState`:
      - `mov w23, #-1`
      - `str w23, [x24, #0x220]`
      - `str w23, [x26, #0x18]`
      - `mov w9, #1`
      - `str w9, [x26 + 0x203fc]`
- 结论：
  - completion-side `+0x20400` 不应再建模成 resource-side outstanding
    bookkeeping；它当前更像 process-owned counter/wakeup slot
  - `ANE_SaveState` 不是 visible `state==2` author；
    当前 visible pattern 更像 demote/save/mark-dirty：
    `-1 / -1 / 1`
- 下一步：
  - 优先看 deeper completion/callback/replay 如何共同作用于：
    - `process+0x203fc`
    - `process+0x20400`
    - `record+0x1b8`
  - 如果仍没有正向 author，再切回
    `resource+0x400d0` first author

- 时间：2026-06-13 00:30:27 +0800
- 目标：把 completion 线继续往下压一层，确认 callback shell 之后真正接管的
  state owner 是谁。
- 动作：
  - 复核：
    - `command_state_materialization_note.md`
    - `legacy_typed_completion_route_note.md`
    - `device_client_context_note.md`
    - `device_client_set_roles_note.md`
  - 新增并运行只读 join probe：
    - `mps/ANE/experiments/ane_bootkc_completion_cleanup_join_probe.py`
  - 新增结果 note：
    - `mps/ANE/experiments/results/completion_cleanup_destroy_join_note.md`
- 证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_completion_cleanup_join_probe.csv`
  - 当前明确链路：
    - `handleOutstandingCommand` callback sink 已是 wakeup-only shell
    - `device+0x4d0 remove/count`
    - `cleanupRCClientWithContext_gated`
      - `client_ctx+0x20` early cleanup-side object
      - `OSSet::withSet(client_ctx+0x18, 0)` clone
      - descend into `ANE_ProcessDestroy_gated(...)`
    - `ANE_ProcessDestroy_gated`
      - `[resource+0x400d0]->removeObject(index)`
- 结论：
  - callback/std::function shell 已不是最值得继续抠的对象
  - completion 之后的下一个 concrete state owner
    已经落到 `client_ctx+0x18/+0x20` cleanup/destroy 路
  - 当前最值钱的新主线应转成：
    `destroy/unload/save-demote`
    如何和
    `process+0x203fc / process+0x20400 / record+0x1b8 / [resource+0x400d0]+0x220`
    组成完整 lifecycle family
- 下一步：
  - 直接比较：
    - `ANE_ProcessDestroy_gated`
    - `ProgramUnload`
    - `ANE_SaveState`
    - `ProgramLoad`
  - 优先找：
    - 哪条 destroy/demote/replay 路最接近
      `process+0x203fc == 2`
      或 `record+0x1b8` durable author

- 时间：2026-06-13 00:35:11 +0800
- 目标：把 `ProgramUnload / create-instance side / restore-cold / save`
  这几条 visible writers 统一成一个更清楚的 lifecycle family。
- 动作：
  - 直接反汇编：
    - `ProgramUnload`
    - `ANE_ProgramCreateInstance_gated` 相关 side path
    - `ANE_RestoreStateEv.cold.2`
  - 对照已有 `ANE_SaveState` 结果
  - 新增结果 note：
    - `mps/ANE/experiments/results/demote_family_join_note.md`
- 证据：
  - `ProgramUnload`:
    - `entry+0x18 <- -1`
    - `entry+0x203fc <- 1`
    - `bl aneCmdSend(...)`
  - create-instance side path:
    - `process+0x18 <- -1`
    - `process+0x203fc <- 1`
    - `bl aneCmdSend(...)`
  - restore-cold:
    - `entry+0x18 <- -1`
    - `entry+0x203fc <- 1`
  - save:
    - `[resource+0x400d0]+0x220 <- -1`
    - `entry+0x18 <- -1`
    - `entry+0x203fc <- 1`
- 结论：
  - 这些当前 visible writers 应被建模成一个 coherent
    demote/unload/mark-dirty family，
    不是很多 unrelated writers
  - visible `state==2` author 仍然没出现；
    更像在 demote family 之后的 deeper reply/replay path
- 下一步：
  - 直接做：
    - `ProgramLoad replay join`
      vs
    - `demote family`
    的窄对照，
    看 `record+0x1b8` 和 `process+0x203fc==2`
    的缺口更像卡在两者之间哪一段

- 时间：2026-06-13 00:44:01 +0800
- 目标：把 `ProgramLoad replay` 与 `demote family` 放到同一张 machine-local
  对照表里，收紧“真正缺口在哪一段”。
- 动作：
  - 新增并运行只读对照 probe：
    - `mps/ANE/experiments/ane_bootkc_programload_vs_demote_probe.py`
  - 新增结果 note：
    - `mps/ANE/experiments/results/programload_vs_demote_note.md`
  - 直接补充反汇编观察：
    - `ProgramUnload` send 后续可见 path
    - create-instance side path 的精确 demote/send 指令点
- 证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_programload_vs_demote_probe.csv`
  - 当前对照：
    - `ProgramLoad`:
      - gate `+0x220` read
      - `process+0x203fc` gate
      - `record+0x1b8` read
      - gate refresh from `record+0x1b8`
    - demote family:
      - `entry/process+0x18 <- -1`
      - `entry/process+0x203fc <- 1`
      - optional `gate+0x220 <- -1`
      - `aneCmdSend(...)`
    - `ProgramUnload` send 后，visible H16 不立刻出现
      `record+0x1b8` replay 形态
- 结论：
  - 缺失的 `state==2` / `record+0x1b8` durable author
    现在最像位于：
    - demote/send family
    与
    - replay/refresh family
    之间的 deeper reply/replay path
  - 因而下一轮不再主要花在 visible writer 层，
    而应直接追：
    `aneCmdSend(...)` 之后的 lower reply/replay family
- 下一步：
  - 优先看：
    1. `ProgramUnload` send 之后的
       `device slot+0x9c0 / 0x927d410` 族
    2. Legacy / restore bridge 里
       `record+0x1b8`
       authoritative 的 reply/replay 入口

- 时间：2026-06-13 00:51:22 +0800
- 目标：比较 restore-side send 与 unload-side send 的 post-send 边界，
  确认哪个更像缺失 lower author 的入口。
- 动作：
  - 新增并运行只读 probe：
    - `mps/ANE/experiments/ane_bootkc_post_send_replay_boundary_probe.py`
  - 新增结果 note：
    - `mps/ANE/experiments/results/post_send_replay_boundary_note.md`
- 证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_post_send_replay_boundary_probe.csv`
  - restore-side:
    - `aneCmdSend(raw)`
    - 极短 visible interval
    - `record+0x1b8` read
    - `resource+0x402f0` writeback
  - unload-side:
    - `aneCmdSend(...)`
    - `device slot+0x9c0` family
    - `0x927d410` family
    - 当前 visible H16 不立刻出现 `record+0x1b8` replay
- 结论：
  - restore-side short replay 已经够清楚，不是当前最好下钻点
  - unload-side post-send device family
    现在是更值得优先追的 lower target
- 下一步：
  - 直接追：
    - `ProgramUnload` send 后的
      `device slot+0x9c0`
      / `0x927d410`
      族
  - 看它是否正是：
    - demote family
      ->
    - deeper reply/replay family
      ->
    - record+0x1b8 / gate refresh / state-2 rejection
    的中间层

- 时间：2026-06-13 01:00:48 +0800
- 目标：把 unload-side post-send family 从模糊地址族收窄成 named gate 链。
- 动作：
  - 直接反汇编 `ProgramUnload` send 后窗口
  - 新增并运行只读 probe：
    - `mps/ANE/experiments/ane_bootkc_unload_postsend_revalidation_probe.py`
  - 新增结果 note：
    - `mps/ANE/experiments/results/unload_postsend_revalidation_note.md`
- 证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_unload_postsend_revalidation_probe.csv`
  - `ProgramUnload` send 后当前 visible chain：
    - `isProgramValid(resource)`
    - `isProcessValid(resource, process, mode=1)`
    - conditional cold-path continuation
- 结论：
  - unload-side post-send 第一跳已经不是“某个 deeper device family”，
    而是 shared lower acceptance chain 本身
  - 所以下一轮不再问 `0x9c0` 是什么，
    而该直接问：
    revalidation 成功后的 accepted branch / cold path
    如何再接回
    `record+0x1b8 / gate refresh / state-2 rejection`
- 下一步：
  - 直接打：
    - `ProgramUnload.cold.1`
      以及它之后真正的 accepted continuation
  - 目标是确认：
    revalidation 通过后，
    哪一条 lower continuation 才是把 demote family 往 replay/refresh/state-2
    方向推进的关键入口

- 时间：2026-06-13 01:06:45 +0800
- 目标：快速确认 revalidation 成功后的 first accepted branch
  是不是已经接回 `record+0x1b8 / gate+0x220 / process+0x203fc` 家族。
- 动作：
  - 直接反汇编：
    - `ProgramUnload` post-isProcessValid mainline
    - `ProgramUnload +0x8fc` onward
    - `ProgramUnload.cold.1` 起始窗口
  - 新增结果 note：
    - `mps/ANE/experiments/results/programunload_accepted_continuation_note.md`
- 证据：
  - current accepted branch first visible shape：
    - optional `ProgramUnload.cold.1`
    - `+0x8fc` onward loop/index/log path
    - later visible re-entry into another `isProgramValid(resource)`-shaped gate
  - 当前没有看到明确的：
    - `record+0x1b8` read
    - `resource+0x402f0` writeback
    - `[resource+0x400d0]+0x220` refresh
- 结论：
  - revalidation 成功后的 first accepted branch
    仍然更像 staged unload/control loop，
    不是显式 replay/refresh 点
  - 所以下一轮不该卡在 first accepted branch shell，
    而应继续追 accepted continuation 更深处的 handoff

- 时间：2026-06-13 01:10:13 +0800
- 目标：判断 ProgramUnload 本体是不是最值得继续深挖的 lower target，
  还是它只是 shared runtime family 中的一步。
- 动作：
  - 复核现有 `client_hint_fallback_runtime_note.md`
  - 新增结果 note：
    - `mps/ANE/experiments/results/programunload_shared_runtime_join_note.md`
- 证据：
  - current client-hint fallback shared runtime chain already includes:
    - `ProgramUnload`
    - `ProgramPartialUnwire`
    - `ProgramReMap`
    - `ProgramLoad(load_type=2)`
  - current unload-side reverse already gives:
    - demote/send
    - revalidation chain
    - accepted continuation
- 结论：
  - ProgramUnload 不是 isolated leaf，
    而是 shared runtime continuation 里的一步
  - 当前更值钱的下一跳应转到 unload 之后的 shared continuation：
    - `ProgramPartialUnwire`
    - `ProgramReMap`
    - `ProgramLoad(load_type=2)`
- 下一步：
  - 直接比较上述三者里，
    哪个 first reconnects to:
    - `record+0x1b8`
    - `[resource+0x400d0]+0x220`
    - `process+0x203fc`

- 时间：2026-06-13 01:13:26 +0800
- 目标：在 unload 之后的 shared runtime continuation 三者中排优先级。
- 动作：
  - 结合已有 machine-local 结论做优先级收敛：
    - `ProgramLoad(load_type=2)` 已是 replay consumer
    - `ProgramReMap` 已是 metadata consumer
  - 新增结果 note：
    - `mps/ANE/experiments/results/post_unload_runtime_priority_note.md`
- 结论：
  - 当前最值钱的 unresolved step 是：
    - `ProgramPartialUnwire`
- 下一步：
  - 直接 reverse `ProgramPartialUnwire(...)`
  - 看它是不是 unload 之后 shared runtime continuation 里
    first reconnects to:
    - `record+0x1b8`
    - `[resource+0x400d0]+0x220`
    - `process+0x203fc`

- 时间：2026-06-13 01:18:18 +0800
- 目标：验证 `ProgramPartialUnwire(...)` 是否真的是值得继续下钻的 lower target，
  而不是 dead-end cleanup helper。
- 动作：
  - 直接反汇编 `ProgramPartialUnwire(...)` 前半段
  - 新增结果 note：
    - `mps/ANE/experiments/results/programpartialunwire_early_note.md`
- 证据：
  - current early body 可见：
    - repeated `+0x2f0` family touches
    - `waitForPendingUpdate(resource, 1, 1)`
    - device-side collection/state machinery
    - device slot `+0x9c0` resource validation
- 结论：
  - `ProgramPartialUnwire(...)` 不是 terminal cleanup leaf
  - 它已经明显重回 lower shared-runtime family
  - 所以下一轮继续追它后半段是合理的

- 时间：2026-06-13 01:33:06 +0800
- 目标：把 `ProgramPartialUnwire(...)` 与 lower state family 的连接单独钉死。
- 动作：
  - 新增并运行 focused probe：
    - `mps/ANE/experiments/ane_bootkc_programpartialunwire_state_join_probe.py`
  - 新增结果 note：
    - `mps/ANE/experiments/results/programpartialunwire_state_join_note.md`
- 证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_programpartialunwire_state_join_probe.csv`
  - 当前已直接可见：
    - `waitForPendingUpdate(resource, 1, 1)`
    - `resource+0x400d0` process-registry walk
    - process-local checks
    - `resource+0x402f0` read
    - `ReleaseProgramResource(...)`
  - 当前仍未见：
    - `record+0x1b8` replay
    - `[resource+0x400d0]+0x220` refresh
- 结论：
  - `ProgramPartialUnwire(...)`
    已经 direct reconnect lower state family
  - 当前 missing lower handoff 已经收窄到：
    `ProgramPartialUnwire` state-family reconnection
    ->
    `ProgramLoad(load_type=2)` explicit replay
- 下一步：
  - 直接找：
    谁 first brings in
    `record+0x1b8`
    在
    `ProgramPartialUnwire -> ProgramReMap -> ProgramLoad(load_type=2)`
    这条 shared continuation 里

- 时间：2026-06-13 01:23:02 +0800
- 目标：继续确认 `ProgramPartialUnwire(...)` 后半段到底是 replay 点还是 cleanup/transition 点。
- 动作：
  - 直接反汇编 `ProgramPartialUnwire(...)` 后半段
  - 定名 helper：
    - `setPendingUpdate_gated`
    - `aneFreeIntermediateBuffer`
    - `dartUnmapResources`
    - `unwireResources`
  - 新增结果 note：
    - `mps/ANE/experiments/results/programpartialunwire_loop_note.md`
- 证据：
  - 当前可见：
    - `waitForPendingUpdate`
    - device collection walk
    - device slot `+0x9c0`
    - process-local collection walk through `process+0x58`
    - `aneFreeIntermediateBuffer`
    - `ReleaseProgramResource`
  - 当前没看到明确：
    - `record+0x1b8` read
    - `resource+0x402f0` writeback
    - `[resource+0x400d0]+0x220` refresh
- 结论：
  - `ProgramPartialUnwire(...)` 当前更像 lower shared-runtime
    cleanup/transition stage，
    不是 direct replay/refresh consumer
  - 所以下一轮该追的是：
    `ProgramPartialUnwire`
    与
    `ProgramLoad(load_type=2)`
    之间的 shared-runtime handoff

- 时间：2026-06-13 01:27:07 +0800
- 目标：确认 unload 之后 shared runtime continuation 的真实顺序，
  避免继续把三者只当作并列候选。
- 动作：
  - 直接反汇编 `setClientHint_gated(...)` 中
    `ProgramUnload -> ProgramPartialUnwire -> ProgramReMap -> ProgramLoad(2)`
    这一整段窗口
  - 新增结果 note：
    - `mps/ANE/experiments/results/setclienthint_shared_continuation_note.md`
- 证据：
  - 当前 machine-local 串行链已明确：
    - `ProgramUnload(resource, 1, 0)`
    - `ProgramPartialUnwire(resource, 0)`
    - `ProgramReMap(resource, residency, 0, 1)`
    - `ProgramLoad(resource, load_type=2, y=0, final_flag=1)`
- 结论：
  - `ProgramPartialUnwire`
    不只是“可能最值钱”，
    而是 shared continuation 里 unload-side demote/revalidation
    与 metadata/replay consumers 之间的 exact handoff stage
- 下一步：
  - 直接盯：
    `ProgramPartialUnwire` 末尾
    到
    `ProgramLoad(load_type=2)` 入口
    之间的最小 handoff 区间

- 时间：2026-06-13 01:38:19 +0800
- 目标：确认 `ProgramReMap(...)` 成功返回后到 `ProgramLoad(load_type=2)` 之前，
  是否还存在更丰富的 CPU-visible lower-state handoff。
- 动作：
  - 新增并运行边界 probe：
    - `mps/ANE/experiments/ane_bootkc_remap_to_programload_boundary_probe.py`
  - 新增结果 note：
    - `mps/ANE/experiments/results/remap_to_programload_boundary_note.md`
- 证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_remap_to_programload_boundary_probe.csv`
  - current success-side visible chain:
    - `ProgramReMap(...)`
    - status spill
    - branch on status
    - logging/materialized-mode formatting
    - `ProgramLoad(load_type=2)`
  - 当前没有再看到：
    - `record+0x1b8` read
    - `resource+0x402f0` write
    - `[resource+0x400d0]+0x220` refresh
- 结论：
  - CPU-visible gap 已进一步塌缩到
    `ProgramReMap(...)` 调用边界本身或更低
  - 所以下一轮优先不再看
    `ProgramReMap -> ProgramLoad` 之间的小窗口，
    而应直接深挖：
    - `ProgramReMap(...)` 内部更深处
    - 或其更低层 side effects

- 时间：2026-06-13 01:42:12 +0800
- 目标：判断 `ProgramReMap(...)` 是否只是 metadata consumer，还是已经带有更深的 side effects。
- 动作：
  - 直接反汇编 `ProgramReMap(...)` 本体
  - 新增结果 note：
    - `mps/ANE/experiments/results/programremap_sideeffects_note.md`
- 证据：
  - 仍可见 metadata reads：
    - `record+0x28`
    - `record+0xb8`
    - `record+0xe8`
  - 但也已可见 side effects：
    - `waitForPendingUpdate`
    - `setPendingUpdate`
    - `wireResources`
    - `kernel_debug`
    - resource-side `0xf5xxx` family writes
- 结论：
  - `ProgramReMap` 不是 explicit replay consumer
  - 但它也不是 passive metadata-only stage
  - 当前最值钱的下一步应直接看
    `ProgramReMap` deeper side effects
    如何把 lower state 传给 `ProgramLoad(load_type=2)`

- 时间：2026-06-13 01:46:09 +0800
- 目标：进一步收敛 `ProgramReMap(...)` deeper side effects 的具体焦点。
- 动作：
  - 结合现有 `0x493a0` post-copy consumer / split-materializer / resource-field
    probes，与当前 `ProgramReMap` reverse 交叉核对
  - 新增结果 note：
    - `mps/ANE/experiments/results/programremap_surface_focus_note.md`
- 结论：
  - 当前不该主要再找
    `ProgramReMap` 里的 direct `record+0x1b8` read
  - 更有信号的焦点应转成：
    - `resource+0x493a0`
    - `resource+0x402f0`
    这对 surface
    在 `ProgramReMap` side effects 里的 coupling
- 下一步：
  - 直接围绕这两个 surface
    在 `ProgramReMap` 里的 side effects
    做 focused reverse

- 时间：2026-06-13 01:53:09 +0800
- 目标：把 `ProgramReMap` 的 `0x493a0 / 0x402f0` coupling 从口头焦点变成
  machine-local probe 证据。
- 动作：
  - 新增并运行 focused probe：
    - `mps/ANE/experiments/ane_bootkc_programremap_surface_coupling_probe.py`
  - 新增结果 note：
    - `mps/ANE/experiments/results/programremap_surface_coupling_note.md`
- 证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_programremap_surface_coupling_probe.csv`
  - current visible sequence:
    - read `resource+0x493a0`
    - read `resource+0x402f0`
    - `waitForPendingUpdate`
    - `setPendingUpdate`
    - `wireResources`
    - later `0xf5ad8` indexed-record metadata reads
    - later `setPendingUpdate(resource, 0, flag)`
- 结论：
  - 当前最强 CPU-visible ProgramReMap handoff
    已收敛到：
    `0x493a0 / 0x402f0`
    coupling side effects
  - 如果 CPU-visible gap 还没到底，
    这里就是最值得继续深挖的点

- 时间：2026-06-13 02:12:10 +0800
- 目标：确认 `ProgramReMap(...)` 里 `wireResources(...)` 前后的 unresolved self-vtable 调用
  是否真是 hidden remap helper。
- 动作：
  - 重开 `ida-pro-mcp` session：`bootkc_i64_v3`
  - 用本地 capstone 直接反汇编：
    - `0xfffffe00093057d8 .. 0xfffffe0009305910`
    - `0xfffffe0009305b0c .. 0xfffffe0009305c30`
  - 解码 `ANEProgramResource / Legacy / RT` vtable 的
    `+0x20` 与 `+0x28` slot
  - 新增 note：
    - `mps/ANE/experiments/results/programremap_object_lifecycle_shell_note.md`
  - 新增 probe：
    - `mps/ANE/experiments/ane_bootkc_programremap_indirect_call_probe.py`
- 证据：
  - `0xfffffe00093058d8 / 0x93058e4`
    当前是：
    - `ldr x16, [x24]`
    - `autda x16, x17`
    - `ldr x8, [x16, #0x20]!`
    - `mov x0, x24`
    - `blraa x8, x16`
  - vtable 解码：
    - `ANEProgramResource::vtable +0x20 -> __ZNK8OSObject6retainEv`
    - `ANEProgramLegacyResource::vtable +0x20 -> __ZNK8OSObject6retainEv`
    - `ANEProgramRTResource::vtable +0x20 -> __ZNK8OSObject6retainEv`
  - exit-side：
    - `0xfffffe0009305bf8 / 0x9305c04`
      是 `self vtable +0x28`
    - 三个 vtable 的 `+0x28`
      都解到 `__ZNK8OSObject7releaseEv`
  - `0xfffffe00093058f0 -> ANEProgramResource::wireResources`
  - `0xfffffe00093059c0 -> ANEProgramResource::dartMapResources`
- 结论：
  - `ProgramReMap(...)` 里 `wireResources(...)` 前后的 unresolved self-vtable 调用
    只是 object-lifecycle shell：
    - pre-wire: `retain(self)`
    - exit-side: `release(self)`
  - 这条线不是 missing lower replay/state handoff
  - 当前下一焦点应明确下沉到：
    - `wireResources(...)`
    - optional `dartMapResources(...)`
    - `0xf5xxx` materialization side effects
- 下一步：
  - 继续 reverse `wireResources(...)` / `dartMapResources(...)`
    与 `0xf5b58 / 0xf5b28 / 0xf5af8 / 0xf5b88 / 0xf5bb8 / 0xf5c18`
    这条 side-effect 链
  - 判断这里是否还能给出
    `ProgramLoad(load_type=2)` 之前的 CPU-visible lower handoff，
    还是已到底到 H16 之下

- 时间：2026-06-13 02:12:10 +0800
- 目标：继续压 `ProgramReMap(...)` 更深 side effects，判断
  `wireResources(...)` / `dartMapResources(...)` / `0xf5xxx`
  是否仍可能藏着 missing lower handoff。
- 动作：
  - 直接反汇编：
    - `ANEProgramResource::wireResources` `0xfffffe00093078c4 .. 0x9307c20`
    - `ANEProgramResource::dartMapResources` `0xfffffe0009308074 .. 0x9308420`
    - `ProgramReMap` materialization tail `0xfffffe0009305b0c .. 0x9305c30`
  - 结合既有 note：
    - `program_resource_self10_device_note.md`
    - `bootkc_program_resource_class_probe.md`
    - `bootkc_resource_gate_indirect_callee_probe.md`
  - 新增 note：
    - `mps/ANE/experiments/results/programremap_lower_sideeffect_boundary_note.md`
- 证据：
  - `wireResources(...)` 当前可见：
    - `self+0x10 -> device`
    - device `0x3b42 / 0x3b44`
    - child resource vtable `+0x10`
      -> `ANEResource::wire`
    - fallback:
      `ANEResource::asyncWire` /
      `ANEResource::waitForAsyncWiring`
  - `dartMapResources(...)` 当前可见：
    - `self+0x10 -> device`
    - device `0xe270` residency-family state
    - child resource vtable `+0x18`
      -> `ANEResource::dartMap(residency, 1)`
  - `ProgramReMap` tail 当前可见：
    - `record+0x28 / 0xb8 / 0xe8`
    - device `0x3618`
    - `udiv / madd`
    - write to
      `0xf5b58 / 0xf5b28 / 0xf5af8 / 0xf5b88 / 0xf5bb8 / 0xf5c18`
    - 这段内部没有新的 deeper helper call
- 结论：
  - `wireResources(...)` 与 `dartMapResources(...)`
    当前都更像 ordinary child-resource wire/map loops，
    不是 missing lower replay/state handoff
  - `0xf5xxx` 当前更像 pure metadata materialization，
    也还没有 visible deeper helper chain
  - 因而 `ProgramReMap(...)` 的 H16-visible 下边界
    已进一步收紧到：
    ordinary child-resource wire/map loops
    + pure indexed-record materialization
  - 当前 blocker 证据更强：
    missing lower handoff
    很可能已经落到 H16-visible CPU text 之下
- 下一步：
  - 直接追 `0xf5xxx` / `0xf5ad8`
    这些 materialized surface 的 later consumers
  - 或进一步形成更硬的结论：
    仅靠当前 H16-visible / artifact-descriptor 层
    已不足以恢复 `ProgramLoad(load_type=2)` 前的关键 lower semantics

- 时间：2026-06-13 02:25:44 +0800
- 目标：确认 `ProgramReMap(...)` materialized
  `0xf5af8 / 0xf5b28 / 0xf5b58 / 0xf5b88 / 0xf5bb8 / 0xf5c18`
  是否有 later visible consumer。
- 动作：
  - 新增 focused probe：
    - `mps/ANE/experiments/ane_bootkc_programremap_materialized_fields_probe.py`
  - 运行并生成：
    - `mps/ANE/.ane_runs/csv/ane_bootkc_programremap_materialized_fields_probe.csv`
  - 新增 note：
    - `mps/ANE/experiments/results/programremap_materialized_fields_consumer_note.md`
- 证据：
  - probe `rows=12`
  - 全部命中都属于
    `ANEProgramResource::ProgramReMap(...)`
  - 每个 field 只有：
    - split-add address materializer
    - 紧随其后的 `str`
  - 当前没有任何 H16 `__TEXT_EXEC`
    later load / consumer 命中：
    - `0xf5af8`
    - `0xf5b28`
    - `0xf5b58`
    - `0xf5b88`
    - `0xf5bb8`
    - `0xf5c18`
- 结论：
  - `0xf5xxx` materialization block
    在当前 H16-visible text 中
    是 write-only
  - 这进一步加强了 blocker：
    missing lower replay/state handoff
    当前已不太像还藏在
    `ProgramReMap(...)` visible side-effect chain
  - 当前最强 blocker 证据已经形成闭环：
    - self vtable shell = `retain/release`
    - `wireResources` = child-resource wire loop
    - `dartMapResources` = child-resource DART-map loop
    - `0xf5xxx` = write-only materialization
- 下一步：
  - 若继续沿此线推进，直接下沉到：
    - lower helper
    - firmware/reply path
  - 或转回 higher runtime / descriptor 对照，
    产出“为什么 descriptor 层不足”的更系统证据汇总

- 时间：2026-06-13 02:32:14 +0800
- 目标：把 `record+0x1b8` durable author gap
  在 raw restore path 与 Legacy typed path
  上做成对称边界证据。
- 动作：
  - 复核现有：
    - `restore_record_raw_send_boundary_note.md`
  - 新增 focused probe：
    - `mps/ANE/experiments/ane_bootkc_legacy_typed_record_state_boundary_probe.py`
  - 运行并生成：
    - `mps/ANE/.ane_runs/csv/ane_bootkc_legacy_typed_record_state_boundary_probe.csv`
  - 新增 note：
    - `mps/ANE/experiments/results/legacy_typed_record_state_boundary_note.md`
- 证据：
  - Legacy typed path 当前 interval summary：
    - `visible_interval_insns=34`
    - `stores=0`
    - `calls=1`
  - 唯一的 call 是：
    - `device slot+0x9c0`
    - `-> ANEHWDevice::isProgramValid(...)`
  - 然后才：
    - `read x25+0x1b8`
    - `mirror to resource alias`
  - 与已有 raw restore path 对照：
    - `aneCmdSend(raw)` 返回后到
      `record+0x1b8` read 前
      无 visible store / 无 visible helper call
- 结论：
  - raw restore path 与 Legacy typed path
    现在都把 `record+0x1b8` durable author gap
    压到了 visible H16 send boundary 之下
  - 这把下一控制层需求进一步明确为：
    - firmware request/reply payload semantics
    - lower helper / completion / callback side effects
    - 或更低 runtime control surface
- 下一步：
  - 若继续沿逆向线推进，
    直接下沉到 firmware/reply/completion path
  - 否则开始整理系统 blocker 证据，
    准备回答“为什么 artifact-descriptor 层不足以把
    test_clean.m4a private ANE 从 ~43s 继续压下去”

- 时间：2026-06-13 02:40:24 +0800
- 目标：确认 Legacy `x25+0x1b8` 分支里
  `sp+0x130 + index*0x50 -> x25`
  这条 local pointer-table
  是否在 immediate window 中有 visible populate author。
- 动作：
  - 新增 focused probe：
    - `mps/ANE/experiments/ane_bootkc_legacy_pointer_table_population_probe.py`
  - 运行并生成：
    - `mps/ANE/.ane_runs/csv/ane_bootkc_legacy_pointer_table_population_probe.csv`
  - 新增 note：
    - `mps/ANE/experiments/results/legacy_pointer_table_population_note.md`
  - 额外反汇编并命名 4 个 window call target
- 证据：
  - 当前 immediate window
    没有 visible direct table-populate store
  - 只看到 4 个 call：
    - `__os_log_internal`
    - `ANEProgramLegacyResource::initSplitKernelSections(...)`
    - `ZinComputeProgramDestroy(...)`
    - `IOFreeTypeVarImpl`
  - 其中最有信号的是
    `initSplitKernelSections(...)`
    一进来就进入更深结构：
    - `self + 0xf61d8`
    - `IOMallocTypeVarImpl`
    - `ZinComputeProgramGetNumberOfKernelSections(...)`
- 结论：
  - `sp+0x130 -> x25` 这一层
    不是最值得继续停留的边界
  - 当前更具体的 Legacy-side lower target
    已经下沉到：
    - `ANEProgramLegacyResource::initSplitKernelSections(...)`
    - `self+0xf61d8` side structure
    - `ZinComputeProgram*` helper family
- 下一步：
  - 二选一：
    1. 继续走 runtime lower side：
       firmware / reply / completion
    2. 走 Legacy helper side：
       `initSplitKernelSections(...)` / `ZinComputeProgram*`

- 时间：2026-06-13 02:44:32 +0800
- 目标：确认 typed completion path
  是否仍可能藏着 `record+0x1b8` 或等价 lower-state 的 visible author。
- 动作：
  - 汇总并重读：
    - `command_state_materialization_note.md`
    - `payload_field_lineage_note.md`
    - `legacy_typed_completion_route_note.md`
  - 新增汇总 note：
    - `mps/ANE/experiments/results/typed_completion_no_record_author_note.md`
- 证据：
  - `payload+0x50`：
    pre-submit carrier -> first submit consumer -> response match
  - `payload+0x68`：
    pre-submit staged command lineage -> completion-side resource lookup key
  - `payload+0x88`：
    callback/wakeup slot
  - `handleOutstandingCommand(...)` 当前可见：
    - `inner+0x58 = completion_status`
    - `lookupProgramResource(inner+0x68)`
    - `matched_resource+0x20400 --`
    - callback/wakeup
    - OSSet cleanup / count / poll-timer disable
  - 当前未见：
    - direct `record+0x1b8` replay
    - gate-owned alias refresh
    - visible durable lower-state author/writeback
- 结论：
  - 当前 typed completion path
    也更像 bookkeeping / wakeup / cleanup，
    不是 missing lower-state author 面
  - 这进一步把 blocker 压缩到：
    - firmware request/reply payload semantics
    - lower reply publish side effects below current H16 text
    - 更低 runtime helper/control layers
- 下一步：
  - 若继续走 runtime lower side，
    直接下沉到 firmware/reply/publish 层
  - 否则开始整理 final blocker evidence package

- 时间：2026-06-13 02:49:50 +0800
- 目标：把 runtime lower side 的 next-layer 入口
  从泛泛的 send/receive/response/completion
  收敛到一个最有信号的可见协议面。
- 动作：
  - 汇总并重读：
    - `receive_response_bridge_note.md`
    - `processCommandResponse Note`
    - `interrupt_special_channel_note.md`
    - `typed_completion_no_record_author_note.md`
  - 新增汇总 note：
    - `mps/ANE/experiments/results/runtime_lower_next_layer_note.md`
- 证据：
  - default receive/response 路：
    - `_IOProcessorChannelReceive` tag-strip
    - `processCommandResponse(...)`
    - `handleOutstandingCommand(...)`
    已都被解释为 lifecycle / completion bookkeeping
  - typed completion 路：
    已都被解释为 status / lookup / wakeup / cleanup bookkeeping
  - special-channel 分支里，
    唯一仍像真实协议面的入口是：
    - `device+0xe200+0x204`
    - `-> ANEHWDevice::processTargetToHostIOCommand(...)`
  - 当前可见 `processTargetToHostIOCommand(...)` 已有：
    - `device+0xe204` context
    - `12-byte shared buffer`
    - `msg+0x04 opcode`
    - visible cases `0x100 / 0x102 / 0x103 / 0x106 / 0x302`
- 结论：
  - runtime lower side 若继续推进，
    最有价值的下一入口
    已经明确收敛到：
    `ANEHWDevice::processTargetToHostIOCommand(...)`
  - 不再应主要围绕
    default `processCommandResponse(...)`
    或 visible typed completion bookkeeping
    做泛扫
- 下一步：
  - 直接下钻 `processTargetToHostIOCommand(...)`
    的 opcode case / shared fallback / deeper helper

- 时间：2026-06-13 02:57:03 +0800
- 目标：确认 Legacy helper side
  是否已经足够深入 artifact/program-body 语义，
  从而把 blocker 更明确地压到更低 runtime accepted-state 层。
- 动作：
  - 汇总并重读：
    - `legacy_pointer_table_population_note.md`
    - `restore_record_bridge_note.md`
    - `legacy_scratch_author_gap_note.md`
    - `bootkc_kind14_section_reference_vector_probe.md`
    - `bootkc_runtime_base_visibility_probe.md`
  - 新增汇总 note：
    - `mps/ANE/experiments/results/legacy_helper_boundary_note.md`
- 证据：
  - `initSplitKernelSections(...)`
    已经进入：
    - `self+0xf61d8`
    - `IOMallocTypeVarImpl`
    - `ZinComputeProgramGetNumberOfKernelSections(...)`
  - `ZinComputeProgram*`
    已经有：
    - section enumeration
    - section-reference carrier resolution
    - wrapper-side section-pointer cache materialization
  - 同时，
    `x25+0x1b8`
    的 first visible mutation opportunity
    仍然在 typed sender 之下
- 结论：
  - Legacy helper side
    已经不再是“还没触到 artifact/program-body 语义”
  - 当前缺的仍然是：
    更低的 accepted runtime state author/control layer
  - 这进一步支持总体 blocker：
    artifact/program-body semantics 已深入，
    accepted runtime state 仍未到达
- 下一步：
  - 若继续逆向推进，
    直接回到 runtime lower side，
    下钻 `processTargetToHostIOCommand(...)`
  - 或开始整理 final blocker evidence package

- 时间：2026-06-13 03:01:08 +0800
- 目标：验证 visible target-to-host 路线
  是否真的和 accepted-state cluster 有价值交集，
  还是也该从主线降权。
- 动作：
  - 汇总并重读：
    - `target_to_host_case_map_note.md`
    - `target_to_host_remaining_cases_note.md`
    - `rpc_request_from_fw_note.md`
    - `receive_response_bridge_note.md`
    - `processCommandResponse Note`
  - 新增汇总 note：
    - `mps/ANE/experiments/results/target_to_host_cluster_miss_note.md`
- 证据：
  - default receive/response route：
    已被解释为
    `_IOProcessorChannelReceive` tag-strip
    -> `processCommandResponse(...)`
    -> outstanding-command lifecycle / completion bookkeeping
  - strongest visible target-to-host route：
    `0x106/0x7000`
    -> `ANE_HandleRPCRequestFromFW(...)`
    -> typed debug-work request object
    -> `ANE_ScheduleWork_gated(...)`
    -> async result path
  - 当前未见它与 accepted-state cluster
    的有价值 visible join：
    - `resource+0x400d0`
    - `resource+0x402f0`
    - `resource+0x493a0`
    - `resource+0x9b698`
    - `resource+0xf5ad8`
    - `process+0x203fc`
    - `record+0x1b8`
- 结论：
  - visible target-to-host broad scan
    对主线价值已显著下降
  - 这条线当前更像独立 debug-work/runtime control family，
    而不是 accepted-state cluster author/replay 路
- 下一步：
  - 若继续 runtime lower side，
    更偏向更低 firmware request/reply/publish
  - 或开始整理 final blocker evidence package

- 时间：2026-06-13 03:07:44 +0800
- 目标：产出一份更完整的 blocker evidence package，
  把当前 benchmark 结果、已达成边界、已证伪路径、剩余缺口和下一控制层需求
  收束到一个可直接引用的总结。
- 动作：
  - 汇总并重读：
    - `current_control_layer_blocker_note.md`
    - `runtime_lower_next_layer_note.md`
    - `legacy_helper_boundary_note.md`
    - `docs/ane_goal.md`
    - `docs/ane_state.md` 当前较好结果 / 当前阻塞
  - 新增汇总 note：
    - `mps/ANE/experiments/results/final_blocker_evidence_package_note.md`
- 证据：
  - 当前最好 private ANE warm wrapper-route：
    - `test_clean.m4a`
    - `28.340s`
  - 历史 supervised baseline：
    - `43.00265733300148s`
  - 但仍未恢复一般化 accepted-state control surface
  - 已达到：
    - userland/runtime request shaping
    - artifact/program-body semantics
    - visible send/receive/response/completion staging
    - concrete accepted-state cluster
  - 仍未达到：
    - `process+0x203fc == 2` decisive author
    - `record+0x1b8` durable author
    - `resource+0x400d0` first materializer
- 结论：
  - 当前 evidence 已足够支持：
    缺的不是“再找一个明显 descriptor field”
    而是更低的 accepted runtime-state author/control layer
- 下一步：
  - 若继续技术推进：
    直接进入更低 firmware request/reply/publish
  - 若转阶段性输出：
    直接围绕该 blocker package 组织最终结论/说明

- 时间：2026-06-13 03:53:10 +0800
- 目标：修正 create-instance hidden branch 中 `0xac738` copy source 的旧解释，避免继续把 `ANE_ProcessCreate_gated(...)` 的返回值误当成 copied surface。
- 动作：
  - 重新打开 `BootKernelCollection.kc` 为 `bootkc_i64_v4`。
  - 在 `bootkc_i64_v4` 中手工定义并读取：
    - `ANEHWDevice::ProgramLoad`
    - `ANEHWDevice::ANE_ProcessCreate_gated`
    - `ANEProgramResource::ANE_ProgramInitialSetup`
    - `ANEProgramLegacyResource::programLoadFromMachoFile`
    - `ANEProgramRTResource::programLoadFromMachoFile`
    - `ANEHWDevice::ANE_ProgramCreateInstance_gated`
    - `ANEHWDevice::isProcessValid`
  - 用 `ida-pro-mcp` 重点核对：
    - `ANE_ProcessCreate_gated` success return
    - create-instance hidden branch 内
      `ProgramLoad / ProgramReMap / needProgramRemap`
      与 `[sp+0x58] / [sp+0x68] / [sp+0x60]` 栈槽
    - later `memmove(..., 0xac738)` 前的真实 source rebinding
  - 新增 note：
    - `mps/ANE/experiments/results/createinstance_memmove_source_correction_note.md`
  - 修正文档：
    - `mps/ANE/experiments/results/bootkc_create_instance_params0_writeback_probe.md`
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - `bootkc_i64_v4` 上的 `ida-pro-mcp.disasm(...)`：
    - `0xfffffe000927f6f0`
    - `0xfffffe000928cf00`
    - `0xfffffe000928d088`
    - `0xfffffe000928d2e4`
    - `0xfffffe000928d3a0`
    - `0xfffffe000928d470`
  - `mps/ANE/experiments/results/createinstance_memmove_source_correction_note.md`
- 结论：
  - 旧解释需要纠正：
    - create-instance hidden branch 中，
      `ANE_ProcessCreate_gated(...)` 的 visible success return 是 `status = 0`
      ，不是 later copied 0xac738 surface 指针。
  - hidden branch 里：
    - post-call `x23` 先作为 status gate 使用
      (`cbz w23, ...`)
    - later 才通过 `[sp+0x58] / [sp+0x60]` 相关 stack handoff
      重新绑定 old surface。
  - 因而当前更准确的 lower dataflow 是：
    - hidden local handle
      -> `additional_params+0x18`
      -> `local_y`
      -> `lookupProgramResource(local_y, &process, 0)`
      -> later old `resource+0x493a0` surface rebinding
      -> `memmove(..., 0xac738)` direction:
         `resource+0x493a0 -> external output`
      -> `local_y` writeback to
         `params[0]`
         以及 create-instance 深分支里的当前 `x21` destination qword0
  - 其中当前可见寄存器角色也应固定为：
      - `x21 = arg2 = external output`
      - 不能再把 `x21` 误解成 `resource+0x493a0`
  - 这不会推翻 hidden-sidecar / first-common-seed 结论，
    但会改变下一步优先级：
    - 不再追“`ANE_ProcessCreate_gated` 直接产出 copied surface”
    - 改追 old `resource+0x493a0` surface 的 first producer
- 下一步：
  - 若继续推进，优先回答：
    1. create-instance 深分支里 old `resource+0x493a0` surface 的
       first producer 是谁
    2. `[sp+0x58] / [sp+0x60]` 与
       `ProgramLoad / ProgramReMap / needProgramRemap` 的关系
    3. 该 later copied surface 与 selector-3 zero-output external output
       是否属于同一 contract family

- 时间：2026-06-13 04:18:00 +0800
- 目标：确认 create-instance 深分支里 local `ANEProcessCreateArgs`
  的 visible seeds 是否已经 one-seed 闭环，还是仍然 split。
- 动作：
  - 继续用 `ida-pro-mcp` 读取
    `ANE_ProgramCreateInstance_gated` 的 `0xfffffe000928d16c` 窗口。
  - 结合当前已确认的 stack-slot roles，核对：
    - `[sp+0x60]`
    - `[x29-0x60]`
    - `x24`
    到 local `ANEProcessCreateArgs` 的组装。
  - 新增 note：
    - `mps/ANE/experiments/results/createinstance_process_args_seed_split_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - `bootkc_i64_v4` 上 `ida-pro-mcp.disasm(0xfffffe000928d160)`
  - `mps/ANE/experiments/results/createinstance_process_args_seed_split_note.md`
- 结论：
  - create-instance 深分支里，
    local `ANEProcessCreateArgs` 当前 visible seeds 仍然是 split：
    - `process_args[0]  <- older resource+0x493a0[0]`
    - `process_args[8]  <- hidden local handle / local_y`
    - `process_args[16] <- client-key family`
  - 因而当前不能再把这条路写成
    “process/resource key first-common-seed 已 visible 闭环”。
  - 更准确的是：
    - hidden local handle 强力 seed 了 process-key / params-side
    - 但 older `resource+0x493a0` seed 仍然单独进入
    - visible assembly point 还是 split-seed
- 下一步：
  - 继续追 older `resource+0x493a0[0]` 的 first producer
  - 或回到 selector-3/base-create 看
    `arg5/out_handle_ptr` 是否能提供对等的 coherence 起点

- 时间：2026-06-13 04:52:00 +0800
- 目标：把 selector-3/base-create 的 blocker 从
  “有没有 handle carrier” 再下沉到
  “handle 之后为什么没进入 accepted coherence”。
- 动作：
  - 汇总并重读现有 base-create handle facts：
    - `ANEDriver::ANE_ProgramCreate_gated`
    - local program-handle slot
    - `ANE_CreateProgramHandle_gated`
    - provider create slot (`vtable+0x8a0`)
    - `additional_params+0x18 = *(arg5/out_handle_ptr)`
  - 新增 note：
    - `mps/ANE/experiments/results/basecreate_handle_coherence_gap_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - `docs/ane_state.md` / `docs/ane_log.md` 中现有
    `ane_bootkc_base_create_handle_bridge_probe_fresh.csv`
    摘要
  - `mps/ANE/experiments/results/basecreate_handle_coherence_gap_note.md`
- 结论：
  - selector-3/base-create 当前不缺 `arg5/out_handle_ptr` carrier
  - 也不缺 shared handle-materialization family
  - 同时不应再把 base-create 说成
    “没有 lower process-args contract”；
    ProgramLoad 当前已明确是：
    `{ additional_params+0x18, additional_params+0x18, additional_params+0x0 }`
  - 当前 visible split 仍开始于：
    `additional_params+0x18 = *(arg5/out_handle_ptr)` 之后
  - 因而下一步更值钱的问题是：
    为什么 base-create 自己这套已存在 lower contract
    仍没 materialize 成 accepted coherence
- 下一步：
  - 不再主要追 driver-side / device-side bridge 自身
  - 直接追：
    1. `additional_params+0x18 = *(arg5/out_handle_ptr)` 之后的最早 lower
       consumer 分叉点
    2. 它与 selector-3 external output 全零的关系

- 时间：2026-06-13 04:41:00 +0800
- 目标：把 old `resource+0x493a0` 从“first visible import”继续提升成
  “producer-to-import join”。
- 动作：
  - 复读并对齐：
    - `bootkc_output_handoff_probe.md`
    - `bootkc_output_procedure_table_alias_probe.md`
    - `bootkc_493a0_output_surface_probe.md`
    - `createinstance_old_493a0_import_note.md`
  - 新增 join note：
    - `mps/ANE/experiments/results/resource_493a0_producer_to_import_join_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - base load-side notes already pin:
    `external output -> memmove(...) -> resource+0x493a0`
  - create-instance note now pins:
    `resolved resource -> x25 = resource+0x493a0 -> [sp+0x60]`
  - `process_args[0] <- *(resource+0x493a0)`
- 结论：
  - old `resource+0x493a0` 已经不该再表述成
    “来路完全未知”。
  - 当前 visible producer-to-import chain 已明确：
    - earlier base create/load path:
      `external output -> resource+0x493a0`
    - later create-instance path:
      `resolved resource -> import old resource+0x493a0`
  - 因而下一步更值钱的问题改成：
    1. selector-3/base-create 为什么没走到能产出 nonzero external output
       的那条 producer chain
    2. create-instance 如何把 imported `resource+0x493a0` family 与
       hidden-handle/local_y family 进一步做 accepted-state coherence

- 时间：2026-06-13 04:29:00 +0800
- 目标：把 old `resource+0x493a0` surface 的 first visible import point 钉住，
  区分“first import”与“first producer”。
- 动作：
  - 继续读取 `ANE_ProgramCreateInstance_gated` 的
    `0xfffffe000928cd48` 到 `0xfffffe000928ce30` 窗口。
  - 对照：
    - base resource lookup
    - `x23`
    - `x25 = resource+0x493a0`
    - `[sp+0x60]`
    与后续 `process_args[0]` 组装的关系。
  - 新增 note：
    - `mps/ANE/experiments/results/createinstance_old_493a0_import_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - `bootkc_i64_v4` 上 `ida-pro-mcp.disasm(0xfffffe000928cd48)`
  - `mps/ANE/experiments/results/createinstance_old_493a0_import_note.md`
- 结论：
  - old `resource+0x493a0` surface 的 first visible import point
    已明确发生在：
    `lookupProgramResource -> resolved resource -> +0x493a0 -> [sp+0x60]`
  - 因而它不是在 later process-create/remap/load continuation
    里第一次出现的。
  - 下一步更该回追：
    resolved base resource 更早的 author/load path，
    而不是继续在 later copied surface 之后猜 first producer。

- 时间：2026-06-13 01:00:48 +0800
- 目标：快速抽样 `ProgramUnload.cold.1`，判断它是不是已经接回
  `record+0x1b8 / gate+0x220 / process+0x203fc` 家族。
- 动作：
  - 直接反汇编 `ProgramUnload.cold.1` 起始窗口
  - 对照：
    - `resource+0x402f0`
    - `record+0x1b8`
    - `[resource+0x400d0]+0x220`
    - `process+0x203fc`
    当前是否出现
- 证据：
  - `ProgramUnload.cold.1` 前半段可见的是：
    - shared/object 引用计数
    - mode-indexed表项选择
    - logging / outlined helper
    - 以及不同 cold helper 片段
  - 当前没有看到明确的：
    - `record+0x1b8` read
    - `resource+0x402f0` writeback
    - `[resource+0x400d0]+0x220` refresh
- 结论：
  - `ProgramUnload.cold.1` 前半段本身更像 shared/object cleanup shell，
    不是显式 replay/refresh 点
  - 所以下一轮不该卡在 `cold.1` 开头，
    而该继续追 revalidation 成功后的 accepted continuation
    在更后面如何再接回 lower state family

- 时间：2026-06-13 05:18:00 +0800
- 目标：把 selector-3/base-create 的最早 lower consumer split
  从抽象表述收紧成可点名的 visible path。
- 动作：
  - 用 `ida-pro-mcp` 继续读取：
    - `ANEHWDevice::ANE_ProgramCreate_gated`
      的成功侧 / attach 侧窗口
  - 对齐现有 notes：
    - `device_client_context_note.md`
    - `program_create_registry_timing_note.md`
  - 新增 note：
    - `mps/ANE/experiments/results/basecreate_lower_consumer_split_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - `bootkc_i64_v4` 上 `ida-pro-mcp.disasm(0xfffffe000928bfa4)`
  - `mps/ANE/experiments/results/basecreate_lower_consumer_split_note.md`
- 结论：
  - selector-3/base-create 的最早 visible lower consumer split
    现在至少可固定为：
    - provisional resource insertion
    - subclass `programLoadFromMachoFile(...)`
    - `client_ctx+0x18` attach
    - later pending clear / wakeup / timer state
  - 因而下一步最值钱的问题已明确改成：
    - `programLoadFromMachoFile(...)` success requirements
    - `client_ctx+0x18` attach 之后为什么仍不能进入
      selector-3 nonzero external output / accepted coherence

- 时间：2026-06-13 04:59:43 +0800
- 目标：把 base-create ProgramLoad 的“真正 external output publish 点”
  和它前面的 gate 从模糊的“ProgramLoad 前后”收紧到具体分支。
- 动作：
  - 用 `ida-pro-mcp` 继续反汇编：
    - `ANEProgramLegacyResource::programLoadFromMachoFile`
    - `ANEProgramRTResource::programLoadFromMachoFile`
    - `ANEHWDevice::ANE_ProcessCreate_gated`
    - `ANEProgramResource::ANE_ProgramInitialSetup`
  - 新增总结 note：
    - `mps/ANE/experiments/results/programload_output_publish_gate_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - Legacy entry:
    - `0xfffffe00092fb844  ldr x22, [additional_params+0x10]`
    - `0xfffffe00092fb860  bzero(x22, 0xac738)`
  - Legacy early resource publish:
    - `0xfffffe00092fb96c .. 0xfffffe00092fb974`
    - `resource+0x493a0.qword0 = additional_params+0x18`
  - Legacy late external-output publish:
    - `0xfffffe00092fc6f8 .. 0xfffffe00092fc734`
    - 需先过：
      - `ANE_ProcessCreate_gated(...)`
      - `findClient(...)`
      - client-open gate
    - 然后才：
      `*external_output = additional_params+0x18`
  - RT entry:
    - `0xfffffe0009309fcc  ldp x21, x28, [additional_params+0x10/+0x18]`
    - `0xfffffe0009309fe0  bzero(x21, 0xac738)`
  - RT early resource publish:
    - `0xfffffe000930a130 .. 0xfffffe000930a138`
    - `resource+0x493a0.qword0 = additional_params+0x18`
  - RT late external-output publish:
    - `0xfffffe000930a990 .. 0xfffffe000930a9c0`
    - 同样依赖：
      - `ANE_ProcessCreate_gated(...)`
      - `findClient(...)`
      - client-open gate
- 结论：
  - raw selector-3 `status=0` 但 external output 全零，
    现在不能再笼统说成“ProgramLoad 前后某处卡住”。
  - 当前更精确的三种可能是：
    1. raw path 根本没进入 ProgramLoad
    2. 进入了 ProgramLoad，也走到了 early
       `resource+0x493a0` publish，
       但没走到 later external-output publish gate
    3. raw probe 的 caller output buffer
       并不是实际 threaded 到 `additional_params+0x10`
  - 所以下一步应优先验证：
    - raw selector-3 caller output
      是否真的 threaded 到 `additional_params+0x10`
    - raw path 是否至少走到 early
      `resource+0x493a0` publish

- 时间：2026-06-13 05:18:26 +0800
- 目标：用更强的动态证据确认 raw selector-3 是否真的碰了
  caller-visible `ANEProgramCreateArgsOutput` 缓冲。
- 动作：
  - 修改：
    `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
    给 `rawCreateFn(service, req, rawOutput)` 前的
    `rawOutput`
    整块预填 `0xA5`
  - 新增 before/after diff 摘要：
    `raw_create_output_change`
  - 编译 probe
  - 运行：
    `./mps/ANE/experiments/ane_services_program_create_runtime_probe \
      benchmark_results/private_ane/ane_tmp_loadcache/D3667668E4FD9569ED8D2AEF8AD71FA10DCAE4E4F08C131128FF746307CCCEF8_535F95FE51587A0849EAD904149115A78D6E46DA4A693892436941057C5CB252_E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 \
      > benchmark_results/private_ane/ane_services_program_create_runtime_probe_v17_raw_output_sentinel.json`
  - 新增总结 note：
    `mps/ANE/experiments/results/raw_selector3_output_sentinel_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v17_raw_output_sentinel.json`
  - 四个当前 case 都显示：
    - `raw_create_status_hex = 0x00000000`
    - `raw_create_output_change.diff_count = 0`
    - `first_diff = null`
    - `last_diff = null`
    - head hash before/after 完全一致
  - 也就是：
    - `qword0..qword3`
    - `u32_0x229e8`
    - `u32_0x522f4/0x522f8`
    - `u32_0xac700..0xac714`
    - `qword_0xac718`
    全都保持 `0xA5` 哨兵值不变
- 结论：
  - 当前 raw selector-3 `status=0`
    不是“把 caller output 写成了 0”
  - 而是：
    raw create 在当前探针下完全没有触碰
    caller-visible `0xac738` output buffer
  - 所以下一步不该再主要问
    “它是不是写了 output 只是值不对”
  - 当前更值钱的问题改成：
    1. effective create-output state 是否只在 raw `outProgram` /
       wrapper payload 内部出现
    2. raw caller output 是否根本没被 threaded 到
       ProgramLoad 所见的 external output slot

- 时间：2026-06-13 05:30:00 +0800
- 目标：确认 raw selector-3 在 caller-visible output 不变的情况下，
  是否已经把有效 create-state materialize 到 wrapper/payload 内部。
- 动作：
  - 继续使用：
    `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
  - 复跑并分析：
    `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v19_internal_windows_text.json`
  - 从现有 `program_wrapper` / `created_device_layout`
    提取当前稳定内部状态
  - 新增总结 note：
    `mps/ANE/experiments/results/raw_selector3_wrapper_internal_state_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - `v19` 四个 case 全都显示：
    - `raw_create_status = 0`
    - `outProgram != NULL`
    - `program_wrapper.payload_qword0 == created_device_layout.device`
    - `created_device_layout.device/owner/service` 均非空
    - `owner_state_u32_0x20 = 1`
    - `service_ready_u8_0x18 = 0`
  - wrapper/payload 里还稳定带有：
    - `payload_qword1 = model/data ptr`
    - `payload_qword2 = payload bytes`
    - `payload_u32_0x20 = precompiled bit`
    - `wrapper_qword_0xa0 = 0x0000000100000015`
    - `wrapper_qword_0xa8 = 0x0000000100000000`
- 结论：
  - raw selector-3 当前不是“什么都没建出来”
  - 而是：
    有效 create-state 至少已经先落在
    wrapper/payload/device graph 内部
  - 这和 caller-visible output 完全未触碰并不矛盾，
    反而说明：
    当前真正缺的更像是 later publish / bridge，
    而不是最初 create 本身
  - 所以下一步更该追：
    selector-4/prepare 或更后阶段
    是否才是第一次
    wrapper-internal state -> external output

- 时间：2026-06-13 05:34:41 +0800
- 目标：确认 selector-4 `owner0 + ready1` 从 `0x14 -> 0x02`
  时，visible wrapper/payload 到底改了什么。
- 动作：
  - 修改：
    `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
    增加：
    - `program_wrapper_owner0_ready1_before_prepare`
    - `program_wrapper_owner0_ready1_after_prepare`
  - 运行：
    `./mps/ANE/experiments/ane_services_program_create_runtime_probe \
      benchmark_results/private_ane/ane_tmp_loadcache/D3667668E4FD9569ED8D2AEF8AD71FA10DCAE4E4F08C131128FF746307CCCEF8_535F95FE51587A0849EAD904149115A78D6E46DA4A693892436941057C5CB252_E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855 \
      > benchmark_results/private_ane/ane_services_program_create_runtime_probe_v20_owner0_ready1_wrapperdiff.json`
  - 新增总结 note：
    `mps/ANE/experiments/results/selector4_owner0_ready1_wrapperdiff_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - `v20` 四个 case 全都显示：
    - `prepare1_owner0_ready1_status_hex = 0x00000002`
    - wrapper 前后只有两处 visible diff：
      - `payload_u8_0xde0 : 2 -> 7`
      - `payload_u32_0xde4 : 0 -> 1`
    - 没有 visible writeback 到：
      - `wrapper+0x70/+0x98/+0xa8`
      - `payload+0xd78..0xda8`
- 结论：
  - selector-4 `owner0 + ready1`
    确实跨过了一步真实状态转移，
    但这一步不是 visible handle/output bridge
  - 当前 `0x02`
    更像 intermediate state，
    不是 runtime-ready publish 本身
  - 所以下一步仍应继续往更低层看，
    而不是再做 wrapper-field sweep

- 时间：2026-06-13 05:39:30 +0800
- 目标：把 selector-4 `0x02` 和 bootkc lower process-state family
  放到同一张图里，判断 `0x02` 是不是 visible success。
- 动作：
  - 重开 IDA：
    `bootkc_i64_v5`
  - 重新定义 lower gate 关键函数并读取：
    - `ANEHWDevice::ProgramLoad`
    - `ANEHWDevice::isProcessValid`
    - `ANEHWDevice::ANE_ProcessCreate_gated`
    - `ANEHWDevice::ANE_SaveState`
    - `ANEHWDevice::ANE_RestoreState`
    - `ANEProcess::init`
  - 提取当前最关键 lower 语义：
    - `isProcessValid(mode!=0)` 对 `process+0x203fc == 2`
      的明确拒绝
    - `create-active -> 0`
    - `save/unload/restore-cold -> 1`
  - 新增总结 note：
    `mps/ANE/experiments/results/selector4_status2_intermediate_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - `isProcessValid(...)` 反编译：
    - 命中 registry 里的 exact `ANEProcess*`
    - `mode==0` 直接 accept
    - `mode!=0` 时只有 `process+0x203fc != 2` 才 accept
  - 现有 bootkc 结果已确认：
    - create-active path 写 `0`
    - save/unload/restore-cold path 写 `1`
  - 现有 selector-4 dynamic 结果已确认：
    - `owner0+ready1` 到 `0x02`
    - 但没有命中 static success 路应有的 visible writeback
- 结论：
  - 当前 `selector-4 status 0x02`
    不该再被当作 visible success
  - 更合理的模型是：
    `0x02 = intermediate restore/prepare state`
  - 这和 bootkc family-6 lower gate 更一致，
    而不是和 full runtime-ready publish 一致

- 时间：2026-06-13 05:59:54 +0800
- 目标：把 `process+0x203fc` 的 visible writer family
  从口头总结收紧成 exact function-level author 证据，并确认
  `record+0x1b8` 仍然只停在 replay/read boundary。
- 动作：
  - 用 `ida-pro-mcp` 继续读取：
    - `ANEProcess::init`
    - `ANEHWDevice::ANE_ProcessCreate_gated`
    - `ANEHWDevice::ANE_SaveState`
    - `ANEHWDevice::ANE_RestoreStateEv.cold.2`
    - `ANEHWDevice::ProgramLoad`
    - `ANEHWDevice::isProcessValid`
    - `sub_FFFFFE00092C1BD4`
  - 新增总结 note：
    `mps/ANE/experiments/results/process_state_and_record_author_tightening_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - `ANEProcess::init`
    直接 zero qword 覆盖 `process+0x203fc`
  - `ANE_ProcessCreate_gated`
    在 create/recreate active path
    直接 `str wzr` 到 `process+0x203fc`
  - `ANE_SaveState`
    main loop 里直接 `process+0x203fc <- 1`
  - `ANE_RestoreStateEv.cold.2`
    直接 `process+0x203fc <- 1`
  - `ProgramLoad` / `ANE_RestoreState` / `Legacy load`
    仍只看到 `record+0x1b8` read，
    没有新的 visible exact store 到 `+0x1b8`
- 结论：
  - `process+0x203fc` 的 visible exact-writer surface 现在基本已封口：
    - `0`:
      `ANEProcess::init` / `ANE_ProcessCreate_gated`
    - `1`:
      `ANE_SaveState` / `ANE_RestoreStateEv.cold.2` / demote family
    - `2`:
      仍没有 visible CPU-side exact writer
  - `record+0x1b8`
    仍更像 firmware reply / deeper replay author，
    而不是当前 visible CPU-side durable write
  - 下一轮应直接下沉到：
    - `aneCmdSend(...)` 之后的 reply/replay family
    - `state==2` lower author
    - `record+0x1b8` durable author

- 时间：2026-06-13 06:21:20 +0800
- 目标：确认 visible `aneCmdSend` / callback / outstanding-command 壳层
  是否就是 `process+0x203fc == 2` / `record+0x1b8`
  的缺失作者层。
- 动作：
  - 用 `ida-pro-mcp` 继续定义并读取：
    - `ANEHWDevice::aneCmdSend(...)`
    - `ANEHWDevice::aneCmdSendAsync(...)`
    - `ANEHWDevice::aneFirmwareCommandSend(...)`
    - `ANEHWDevice::handleOutstandingCommand(...)`
    - `ANEHWDevice::iterateOutstandingCommands(...)`
    - typed `aneCmdSend(...)` 的
      `std::__function::__func<...>::operator()`
    - `ProgramUnload(...).cold.1`
  - 新增总结 note：
    `mps/ANE/experiments/results/send_reply_shell_negative_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - `aneCmdSendAsync(...)`
    只是 function copy 后转调
    `aneFirmwareCommandSend(...)`
  - typed `aneCmdSend(...)` 的 lambda
    `__ZNSt3__110__function6__func<...>::operator()`
    只做：
    `ANEHWDevice::commandWakeup(device, *result_ptr)`
  - `aneFirmwareCommandSend(...)`
    当前可见层是：
    - `ANEFirmwareCommandState` 分配/填充
    - payload copy
    - `IOProcessorChannelSendRetry(...)`
    - 失败侧 `handleOutstandingCommand(...)`
  - `handleOutstandingCommand(...)`
    当前可见层是：
    - command-state completion/result byte
    - optional memmove / DMA free
    - `lookupProgramResource(...)`
    - `matched_process+0x20400` 计数递减
    - callback 调用
    - `commandWakeup(...)`
  - `iterateOutstandingCommands(...)`
    及其 block
    只做 `safeMetaCast(OSValueObject<ANEFirmwareCommandState>)`
    后转调外层 block
  - 对
    `aneFirmwareCommandSend(...)` /
    `handleOutstandingCommand(...)` /
    `iterateOutstandingCommands(...)`
    的 exact operand 检查仍是：
    - no `op_any == 0x3fc`
    - no `op_any == 0x1b8`
- 结论：
  - 当前 visible send/reply shell
    更像 command-state / sleep-wakeup / callback 壳，
    不是缺失的 lower state 作者层
  - `handleOutstandingCommand(...)`
    也更像失败侧清理/回调壳，
    不是统一成功 completion writeback 层
  - 下一轮若继续沿 send/completion 家族下沉，
    应直接看更低层：
    - `IOProcessorChannelSendRetry(...)` 之后的真实 completion/writeback
    - firmware-side shared-state writeback
    - 或不经当前 `handleOutstandingCommand(...)`
      的成功 completion/request-removal 路
- 时间：2026-06-13 15:05:00 +0800
- 目标：确认当前 send/reply 家族里，
  是否已经有比 `handleOutstandingCommand(...)`
  更像 success-style completion /
  request-removal 入口的可见层。
- 动作：
  - 读取：
    - `mps/ANE/experiments/ane_bootkc_process_command_response_probe.py`
    - `mps/ANE/experiments/ane_bootkc_completion_cleanup_join_probe.py`
    - `mps/ANE/experiments/README.md`
    - `docs/ane_state.md`
  - 复核现有 probe / note 对
    `processCommandResponse(...)`
    与 request-side RPC 路的结论
  - 最小更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - `processCommandResponse(...)`
    当前可见动作：
    - 遍历 `device+0x4d0` outstanding-command `OSSet`
    - `safeMetaCast(OSValueObject<ANEFirmwareCommandState>)`
    - `payload+0x50 == response_arg1`
      时直接
      `handleOutstandingCommand(outstanding_osobject, 1)`
    - 未命中且 `payload+0x90 == 0`
      时走 `IOProcessorChannelSendRetry(...)` resend
  - 这使当前分层更清楚：
    - `processCommandResponse(...)`
      = success-match / resend 入口
    - `handleOutstandingCommand(...)`
      = completion bookkeeping / callback / wakeup / cleanup 壳
  - 但这两层都仍未触到：
    - `process+0x203fc == 2`
    - `record+0x1b8`
    - visible durable lower-state writeback
  - request-side 现有仓库证据里，
    更值得继续下钻的是：
    `processTargetToHostIOCommand(...)`
    -> `ANE_HandleRPCRequestFromFW(...)`
    -> `ANEScheduler::iteratePendingRequests(...)`
    / `ANE_ScheduleWork_gated(...)`
- 结论：
  - 当前比 `handleOutstandingCommand(...)`
    更像 success-style completion 入口的，
    是上游的 `processCommandResponse(...)`
  - 但它仍只是 response-side bookkeeping，
    不是 lower state author
  - 若下一轮要追
    `FWPendingRequest` /
    `removeRequestByUUID`
    一类 request lifecycle，
    主攻点应切到 RPC / pending-request /
    scheduler 侧，而不是继续抠
    `handleOutstandingCommand(...)` 本体
- 时间：2026-06-13 06:52:52 +0800
- 目标：确认新的 `procedure/cache/chaining` 线索
  到底只是 lookup/build/send 壳，
  还是已经碰到了 accepted-state /
  durable-author 层。
- 动作：
  - 用 `ida-pro-mcp` 读取并对照：
    - `findChainingRequestByCacheHandler(...)`
      `0xfffffe000935f214`
    - `findProcedureCallCacheRequest(...)`
      `0xfffffe00092855f0`
    - `sendChainingCacheRequestToFirmware(...)`
      `0xfffffe000928e7d4`
    - `buildFirmwareChainingCacheRequest(...)`
      `0xfffffe000928e954`
    - `buildFirmwareProcedureCallCacheRequest(...)`
      `0xfffffe0009294688`
    - `buildFirmwareProcedureCallRequest(...)`
      `0xfffffe0009295280`
  - 追加结果 note：
    `mps/ANE/experiments/results/procedure_cache_chaining_boundary_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - `findChainingRequestByCacheHandler(...)`
    当前明确是这组函数里唯一直接碰到
    accepted-state cluster 的点：
    - 使用 `resource+0x400d0`
    - 使用 `resource+0x9b698`
    - 先要求
      `[resource+0x400d0]+0x264` bit0 置位
      且
      `*(resource+0x9b698) > 2`
    - 再枚举 `[resource+0x400d0]` 子项，
      从 `entry+0x90` 起按
      `(*slot)+0x8 == cacheHandler`
      查找
    - 命中后只把 slot 指针写回 out-param
  - `findProcedureCallCacheRequest(...)`
    当前明确是 request-side pending lookup：
    - `ANEScheduler::pendingRequestsCount()`
    - `getMutablePendingRequest(i)`
    - 命中条件：
      - `request+0x3120 != NULL`
      - 且
        `request+0x3130 == cacheHandle`
        或
        `[[request+0x18]+0x48] == uuid_like_arg`
  - `sendChainingCacheRequestToFirmware(...)`
    当前明确只是 send shell：
    - 调 `aneCmdSend(...)`
    - 成功后：
      - `req+0x30 <- 1`
      - `req+0x8 <- returned_obj+0x20`
    - 不直接触到
      `resource+0x400d0` /
      `resource+0x402f0` /
      `resource+0x493a0` /
      `record+0x1b8` /
      `process+0x203fc`
  - `buildFirmwareChainingCacheRequest(...)` /
    `buildFirmwareProcedureCallCacheRequest(...)` /
    `buildFirmwareProcedureCallRequest(...)`
    当前都更像 command marshalling：
    - 组 procedure/cache request buffers
    - 记录
      uuid/programId/processId/transactionId/
      programHandle/procedureID/live-in/dynamicOffset
    - exact-operand 检查未命中
      `0x400d0 / 0x402f0 / 0x493a0 / 0x9b698 / 0x1b8 / 0x203fc`
- 结论：
  - 这条新线索不是空跑；
    `cacheHandler`
    确实能 join 到
    `resource+0x400d0 / resource+0x9b698`
    这组 accepted-side cluster。
  - 但截至当前 visible layer，
    `procedure/cache/chaining`
    仍整体更像
    lookup/build/send family，
    不是
    `process+0x203fc == 2`
    /
    `record+0x1b8`
    的 durable author。
  - 因而它应保留为 accepted-side context bridge，
    但不再作为当前主线最高优先级；
    主攻点仍应回到：
    - success completion / request-removal
    - firmware-side shared-state writeback
    - `record+0x1b8`
    - `process+0x203fc == 2`
- 下一步：
  - 保留
    `findChainingRequestByCacheHandler(...)`
    作为 accepted-side cacheHandler join 证据；
  - 主线继续下沉到更低层 completion/writeback；
  - 若再回看 procedure/cache/chaining，
    只需要回答：
    它们的 caller 中，
    是否有更后面的 completion-side consumer
    利用 `cacheHandle`
    重新接回 lower state family。
- 时间：2026-06-13 07:20:00 +0800
- 目标：进一步压实
  `ProgramLoad(load_type=2)`
  的真实 consumer 语义，
  判断当前 shared continuation
  还能否在 H16-visible text 上给出新的 author 线索。
- 动作：
  - 在 `bootkc_i64_v5` 里把以下入口补定义成函数：
    - `0xfffffe00092800cc`
      `ANEHWDevice::ProgramPartialUnwire(...)`
    - `0xfffffe0009305508`
      `ANEProgramResource::needProgramRemap(unsigned int)`
    - `0xfffffe00093056bc`
      `ANEProgramResource::ProgramReMap(...)`
    - `0xfffffe000933c1a8`
      `ANEHWDevice::setClientHint_gated(...)`
  - 继续用 `ida-pro-mcp`
    读取：
    - `ProgramLoad(...)`
    - `needProgramRemap(...)`
    - `ProgramPartialUnwire(...)`
    - `ProgramReMap(...)`
    - `setClientHint_gated(...)`
  - 新增结果 note：
    `mps/ANE/experiments/results/programload_remap_process_contract_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - `setClientHint_gated(...)`
    当前 xref/反汇编已再次确认唯一可见 shared continuation：
    - `ProgramPartialUnwire(resource, 0)`
      at `0xfffffe000933d4e8`
    - `ProgramReMap(resource, residency, 0, 1)`
      at `0xfffffe000933d8dc`
    - `ProgramLoad(resource, load_type=2, y=0, final_flag=1)`
      at `0xfffffe000933d994`
  - `needProgramRemap(residency)`
    当前 machine-local 反编译/反汇编已明确：
    - 先检查当前 resource
      上多组 per-residency `+0xa0` slots
    - 再扫描 `resource+0x400e8`
      child-resource collection
    - 对每个 child
      要求当前 residency slot 与
      `child+0x90+residency*0x28`
      选中的 table entry 均非空
    - 任一不满足即返回 `1`
  - `ProgramLoad(...)`
    当前可见顺序已更精确：
    - 先读：
      - `resource+0x493a0`
      - `[resource+0x400d0]+0x220`
    - 再用 `device+0xe270`
      作为 `residency`
      调 `needProgramRemap(residency)`
    - 通过后走
      `setPendingUpdate_gated(resource, 1, 1)`
  - `ProgramLoad(...)`
    里 `load_type`
    与 `process+0x203fc`
    当前已明确不是单一 zero/nonzero 语义：
    - `load_type == 0`
      且 gate-owned state 不是 `-1`
      时可直接 fast-success
    - `load_type == 1`
      时：
      - `process+0x203fc == 0`
        才视为已有 ready process
      - nonzero 才 re-enter
        `ANE_ProcessCreate_gated(...)`
    - `load_type != 1`
      （当前主线里的 `load_type == 2`）
      时：
      - `process+0x203fc == 0`
        直接 skip 该 process
      - nonzero 才 re-enter
        `ANE_ProcessCreate_gated(...)`
  - `record+0x1b8`
    当前仍只在更深 create-program / replay path
    上被消费：
    - `aneCmdSend(...)`
    - device `vslot +0x9c0` validation
    - `ldr [record+0x1b8]`
    - `str [gate+0x220]`
- 结论：
  - 当前 `ProgramLoad(load_type=2)`
    可以更强地归类为：
    - remap-ready structural-table consumer
    - load-type-specific process-state consumer
    - record replay consumer
  - `ProgramPartialUnwire` / `ProgramReMap`
    在当前 H16-visible text
    虽然仍负责 reconnect / remap / materialize，
    但没有直接作者化：
    - remap-ready tables
    - `process+0x203fc == 2`
    - `record+0x1b8`
  - 因而当前 blocker 进一步硬化为：
    artifact-descriptor / H16-visible CPU text
    更像 shape/check/reconnect/replay consumers；
    关键 durable author
    更像已经在更低层。
- 下一步：
  - 若继续留在 H16 visible 层，
    最值钱的新入口已改成：
    1. 谁 first authors
       `needProgramRemap(residency)`
       依赖的 per-residency remap-ready tables
    2. 谁 decisively authors
       `process+0x203fc == 2`
    3. 谁 durably authors
       `record+0x1b8`
  - 不再主要把希望放在
    `ProgramReMap -> ProgramLoad`
    之间那段已被压薄的 CPU-visible 小窗口。
- 时间：2026-06-13 07:48:18 +0800
- 目标：闭合 `needProgramRemap(residency)` 顶层
  `resource+0x60` 的 visible author 链，
  并纠正此前对 `self+0x68` 的过宽解释。
- 动作：
  - 继续沿用当前 `ida-pro-mcp`
    会话 `bootkc_i64_v5`
  - 复查：
    - `ANEProgramLegacyResource::initOtherSections(...)`
      `0xfffffe00092ff2c0`
    - `ANEProgramLegacyResource::programLoadFromMachoFile(...)`
      `0xfffffe00092fb6d0`
    - `ANEProgramResource::needProgramRemap(...)`
      `0xfffffe0009305508`
  - 新增结果 note：
    `mps/ANE/experiments/results/remap_ready_slot_resource60_author_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - `programLoadFromMachoFile(...)`
    在 `0xfffffe00092fccf8`
    明确调用
    `initOtherSections(...)`
  - `initOtherSections(...)`
    当前可见顺序已明确：
    - `0xfffffe00092ff340`
      `ANEResource::create<(ANEResourceType)3>(...)`
    - `0xfffffe00092ff348`
      `ldur q0, [x29, #-0x20]`
    - `0xfffffe00092ff350`
      `str q0, [self+0x60]!`
  - 因而 `resource+0x60/+0x68`
    当前可见 first author
    不是 `additional_params+0x68`
    也不是 `self+0x68 -> self+0x60` 拷贝，
    而是 `create(Type3)` 产出的新 `shared_ptr`
  - `0xfffffe00092ff344`
    处先读 `[self+0x68]`
    之后只走旧 control-block release，
    不是新 payload 来源
  - 后续消费面也已明确：
    - `0xfffffe00092fcd14`
      `ldr x27, [self+0x60]`
      -> legacy-only `dartMap(...)` 路
    - `0xfffffe00092fcea0`
      `ldr x8, [self+0x60]`
      -> `+0x88` section/header 初始化路
- 结论：
  - `resource+0x60`
    的顶层 visible author 链现在已经闭合
  - 当前 `needProgramRemap(residency)`
    的顶层可见 slot provenance
    已可更精确写成：
    - `resource+0x20`
      <- `additional_params+0x38`
    - `resource+0x30`
      <- `additional_params+0x48`
    - `resource+0x60`
      <- legacy-only
         `initOtherSections(...)`
         `create(Type3)` author path
  - 因而当前 remap-ready 主未知项
    已不再是顶层 `resource+0x60`，
    而是 child collection/table authors
    以及更低层 `process+0x203fc` /
    `record+0x1b8` author
- 下一步：
  - 继续留在 H16 visible 层时，
    优先转向：
    1. `resource+0x400e8` child collection
       的 first author
    2. child `+0x90/+0xa0` table authors
    3. `process+0x203fc == 2`
       与 `record+0x1b8`
       的 lower author surfaces
- 时间：2026-06-13 08:14:39 +0800
- 目标：收紧 `resource+0x400e8`
  child-resource collection
  这一层到底停在
  construct，还是已包含 visible populate。
- 动作：
  - 新增 probe：
    `mps/ANE/experiments/ane_bootkc_resource_400e8_collection_probe.py`
  - 运行输出：
    `mps/ANE/.ane_runs/csv/ane_bootkc_resource_400e8_collection_probe.csv`
  - 结合 raw bootkc 反汇编，
    复查：
    - `ANEResourceCollection::C1()`
      `0xfffffe000931e5e8`
    - `ANEResourceCollection::addResource(...)`
      `0xfffffe000931e904`
    - Legacy `preProcess`
      `0xfffffe00092faa08 / 0xfffffe00092faa0c`
    - RT `preProcess`
      `0xfffffe00093092a8 / 0xfffffe00093092ac`
    - Legacy `initSplitKernelSections`
      `0xfffffe00092fe5d0`
    - RT
      `traverseProcedureGraphAndPopulateIOs`
      `0xfffffe000930ca60`
  - 新增结果 note：
    `mps/ANE/experiments/results/resource_400e8_collection_lifecycle_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - 当前 shared Legacy/RT `preProcess`
    已明确：
    - Legacy
      `0xfffffe00092faa08`
      `bl ANEResourceCollection::C1()`
      ->
      `0xfffffe00092faa0c`
      `str x0, [resource+0x400e8]`
    - RT
      `0xfffffe00093092a8`
      `bl ANEResourceCollection::C1()`
      ->
      `0xfffffe00093092ac`
      `str x0, [resource+0x400e8]`
  - `ANEResourceCollection::C1()`
    raw body 当前已收紧为：
    - 清空 begin/end/cap-like 头部
    - 构造 comparator `std::function`
    - 分配 `IORecursiveLock`
    - 没有直接可见 child materialization
  - `ANEResourceCollection::size()`
    当前用
    `(end - begin) >> 4`
    计算元素数，
    说明 collection 元素粒度是
    16-byte `shared_ptr<ANEResource>` slot
  - 当前 `resource+0x400e8`
    后续 visible 层也已明确 populate：
    - Legacy
      `initSplitKernelSections(...)`
      `0xfffffe00092fe5b4`
      `ldr [resource+0x400e8]`
      ->
      `0xfffffe00092fe5d0`
      `bl ANEResourceCollection::addResource(...)`
    - RT
      `traverseProcedureGraphAndPopulateIOs(...)`
      `0xfffffe000930ae58`
      先把 `&resource+0x400e8`
      存到 `[sp,#0xb8]`
      之后
      `0xfffffe000930ca3c`
      `ldr x8, [sp,#0xb8]`
      ->
      `0xfffffe000930ca40`
      `ldr x28, [x8]`
      ->
      `0xfffffe000930ca60`
      `bl ANEResourceCollection::addResource(...)`
  - 当前 `addResource(...)`
    visible body
    主要围绕 lock / comparator /
    begin-end-cap / shared_ptr slot 搬移，
    仍没看到 child `+0x90/+0xa0`
    table 的直接作者化
- 结论：
  - `resource+0x400e8`
    不应再表述成
    “child collection first author 未知”
  - 当前更准确的是：
    H16 visible 层
    已覆盖
      construct
      top-level store
      visible populate
    三步
  - 当前主未知项已进一步下沉到：
    1. 被加入 collection 的 child
       `shared_ptr<ANEResource>`
       具体来自哪类 child path
    2. 这些 child 的
       `+0x90/+0xa0`
       per-residency remap tables
       谁 first authors
    3. `process+0x203fc == 2`
       与 `record+0x1b8`
       的 lower author
- 下一步：
  - 继续留在 H16 visible 层时，
    先针对：
    1. Legacy `initSplitKernelSections`
       与 RT `traverseProcedureGraphAndPopulateIOs`
       中传给 `addResource(...)`
       的 child `shared_ptr`
       来源做 provenance 收紧
    2. 再判断 child `+0x90/+0xa0`
       table author
       是否仍停在 H16 visible 层
- 时间：2026-06-13 08:33:09 +0800
- 目标：继续收紧
  `resource+0x400e8`
  visible populate 的 child provenance，
  并判断 `Type4` child 的
  `+0x90/+0xa0`
  table author
  是否仍未露到 H16 visible 层。
- 动作：
  - 新增 probe：
    `mps/ANE/experiments/ane_bootkc_type4_child_table_probe.py`
  - 运行输出：
    `mps/ANE/.ane_runs/csv/ane_bootkc_type4_child_table_probe.csv`
  - 结合 raw bootkc 反汇编，
    复查：
    - `ANEResource::create<Type4>()`
      `0xfffffe00093183e4`
    - Legacy
      `initSplitKernelSections(...)`
      `0xfffffe00092fe4e8`
      到
      `0xfffffe00092fe5d0`
    - RT
      `traverseProcedureGraphAndPopulateIOs(...)`
      `0xfffffe000930c90c`
      到
      `0xfffffe000930ca60`
    - `ANE_ProgramInitialSetup(...)`
      三处 `create<Type4>()`
  - 新增结果 note：
    `mps/ANE/experiments/results/type4_child_table_visibility_note.md`
  - 更新：
    - `mps/ANE/experiments/results/resource_400e8_collection_lifecycle_note.md`
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - 当前 direct callers 里，
    `ANEResource::create<Type4>()`
    至少被以下几类可见路径直接调用：
    - Legacy `initSplitKernelSections(...)`
    - Legacy `initMutableKernelSections(...)`
    - `ANE_ProgramInitialSetup(...)` 三处
    - RT `traverseProcedureGraphAndPopulateIOs(...)`
  - 与 `resource+0x400e8`
    直接相关的两条 populate 路
    现在都已接回 `Type4`：
    - Legacy
      `0xfffffe00092fe4e8`
      `create<Type4>()`
      ->
      `0xfffffe00092fe5d0`
      `addResource(...)`
    - RT
      `0xfffffe000930c90c`
      `create<Type4>()`
      ->
      `0xfffffe000930ca60`
      `addResource(...)`
  - 新 probe 还表明：
    - `create<Type4>()` body
      `child+0x90/+0xa0/+0xb0`
      非栈访问当前都没露出来
    - Legacy add-to-collection window
      当前只看到
      `child + residency*0x28 + 0xb0`
      一条可见写入
    - RT add-to-collection window
      `child+0x90/+0xa0/+0xb0`
      当前都没露出来
- 结论：
  - 当前可以更强地说：
    `resource+0x400e8`
    visible populate 的 child
    已收紧到 `Type4` child resources
  - 但当前 machine-local
    仍没有证明
    `Type4` child 的
    `+0x90/+0xa0`
    per-residency remap tables
    是在这些 visible windows
    里作者化的
  - 所以当前主未知项
    已继续下沉到：
    1. `ANE_ProgramInitialSetup(...)`
       里三处 `create<Type4>()`
       对 remap-ready surfaces 的发布关系
    2. `Type4` child
       `+0x90/+0xa0`
       table 的 first author
    3. `process+0x203fc == 2`
       与 `record+0x1b8`
       的 lower author
- 下一步：
  - 继续留在 H16 visible 层时，
    先复查
    `ANE_ProgramInitialSetup(...)`
    三处 `create<Type4>()`
    的结果分别被送到了哪些 surfaces；
  - 若这些窗口里仍没有 child
    `+0x90/+0xa0`
    作者面，
    就把该 table author
    归为更低层 blocker 证据之一。
- 时间：2026-06-13 09:01:15 +0800
- 目标：验证
  `Type4 -> Type0 -> ANEResource::C1`
  这一层是否仍无
  child `+0x90/+0xa0`
  作者面，并把该边界固化为更强 blocker 证据。
- 动作：
  - 新增 probe：
    `mps/ANE/experiments/ane_bootkc_type0_type4_author_boundary_probe.py`
  - 运行输出：
    `mps/ANE/.ane_runs/csv/ane_bootkc_type0_type4_author_boundary_probe.csv`
  - 新增结果 note：
    `mps/ANE/experiments/results/type0_type4_author_boundary_note.md`
  - 同时新增：
    `mps/ANE/experiments/results/initialsetup_type4_slot_bridge_note.md`
    与其 CSV evidence
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
- 证据：
  - 当前 `Type4` 路
    明确会 direct call
    `ANEResource::create<Type0>()`
  - 新 probe summary 当前是：
    - `resource_c1`
      `child+0x90/+0xa0/+0xb0 = 0/0/0`
    - `create_type0`
      `child+0x90/+0xa0/+0xb0 = 0/0/0`
    - `create_type4`
      `child+0x90/+0xa0/+0xb0 = 0/0/0`
    - `legacy_add_to_400e8`
      只命中
      `child + residency*0x28 + 0xb0`
    - `rt_add_to_400e8`
      `child+0x90/+0xa0/+0xb0 = 0/0/0`
  - `InitialSetup Type4 slot bridge`
    live-validated CSV 当前表明：
    - 三处 `create<Type4>()`
      先把 shared_ptr pairs
      staged 在
      `sp+0x48/0x88`,
      `sp+0x70/0xa8`,
      `x27/sp+0x78`
    - 随后出现 bridge candidate：
      - `-> [x29-0xe0]`
      - `-> [x29-0xd0]`
      - `-> [x29-0xf0]`
    - 尾部硬事实：
      - `[x29-0xd0] -> additional_params+0x38`
      - `[x29-0xe0] -> additional_params+0x48`
      - `[x29-0xf0] -> additional_params+0x68`
- 结论：
  - 当前 machine-local 现在可以更强地说：
    即使沿
    `Type4 -> Type0 -> resource ctor`
    再往下一层，
    也还没出现
    child `+0x90/+0xa0`
    remap-table 的可见作者面
  - 同时，
    `InitialSetup` 当前很像正在把
    三路 Type4-derived shared_ptr pairs
    bridge 到
    `additional_params+0x38/+0x48/+0x68`
    的上游
- 下一步：
  - 继续收紧
    `InitialSetup` 三路 Type4
    与
    `additional_params+0x38/+0x48/+0x68`
    的对应关系；
  - 如果仍无 child `+0x90/+0xa0`
    visible author，
    就把该 table author
    正式归入 lower-layer blocker 证据。
- 时间：2026-06-13 09:40:19 +0800
- 目标：把
  `ANE_ProgramInitialSetup(...)`
  三路 `create<Type4>()`
  从 slot bridge
  继续收紧到
  current-machine visible
  section-family 语义。
- 动作：
  - 新增 probe：
    `mps/ANE/experiments/ane_bootkc_initialsetup_type4_section_family_probe.py`
  - 运行输出：
    `mps/ANE/.ane_runs/csv/ane_bootkc_initialsetup_type4_section_family_probe.csv`
  - 新增结果 note：
    `mps/ANE/experiments/results/initialsetup_type4_section_family_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
    - `docs/ane_log.md`
- 证据：
  - 当前 visible compare shape
    已很像：
    - `x28`
      是 lower-case section name
    - `x28+0x10`
      是 upper-case segment name
  - 当前 exact string families
    已验证到：
    - `__TEXT`
      / `__text`
      / `__const`
    - `__INIT`
      / `__text`
    - `__KERN_`
      / `__kern_`
    - `__RUNTIME`
      / `__runtime`
  - `call1`
    当前可直接收紧为：
    `__TEXT,__const`
    -> `create<Type4>()`
    -> `aneVnodeAsyncReadAdvise(... usage=9)`
    -> `additional_params+0x48`
    -> `resource+0x30`
  - `call2`
    当前可直接收紧为：
    `__TEXT,__text`
    -> `create<Type4>()`
    -> `aneVnodeAsyncReadAdvise(... usage=8)`
    -> `additional_params+0x38`
    -> `resource+0x20`
  - `call3`
    当前可直接收紧为：
    gated `__INIT,__text`
    -> `create<Type4>()`
    -> `map(0x1000)`
    -> `aneValidateVnodeFromMappedAddress(...)`
    -> `additional_params+0x68`
    -> `resource+0x50`
  - 同一
    `__INIT,__text`
    family
    当前还存在
    alternate lane：
    `[sp+0x3c] != 0`
    -> `create<Type3>()`
    -> `map(3)`
    -> `memmove(...)`
  - `__KERN_,__kern_`
    和
    `__RUNTIME,__runtime`
    当前分别只落到
    counter / flag lane，
    没有直接进入三路 Type4 top-level seed
- 结论：
  - 当前可以更强地说：
    top-level remap-ready slots
    在 visible path 上
    已具备更具体的
    section-family semantics，
    不再只是
    “三次 Type4 create”
  - 但当前还不能把
    `__INIT,__text`
    整个 family
    直接等价成
    `resource+0x50`，
    因为它还存在
    separate `Type3`
    alternate lane
  - 同时，
    这轮工作仍没有改变
    更低层 blocker：
    `Type4` child
    `+0x90/+0xa0`
    per-residency remap tables
    依旧没有 visible first author
- 下一步：
  - 继续追
    `[sp+0x3c]`
    的来源，
    看它为何让
    `__INIT,__text`
    在
    `Type3`
    与
    `Type4`
    两条 lane 之间分裂
  - 再判断
    这条
    `__INIT,__text`
    alternate `Type3`
    lane
    是否会在更低层
    join 回
    `resource+0x50`
    或其它 remap-ready surface
- 时间：2026-06-13 10:12:00 +0800
- 目标：验证
  `ANE_ProgramInitialSetup(...)`
  里的
  `w21 / [sp+0x3c]`
  是否会落成后续真正被消费的
  create-time control field。
- 动作：
  - 新增 probe：
    `mps/ANE/experiments/ane_bootkc_initialsetup_runtime_carry_probe.py`
  - 运行输出：
    `mps/ANE/.ane_runs/csv/ane_bootkc_initialsetup_runtime_carry_probe.csv`
  - 新增结果 note：
    `mps/ANE/experiments/results/initialsetup_runtime_carry_rtgraph_note.md`
  - 更新：
    - `mps/ANE/experiments/results/initialsetup_type4_section_family_note.md`
    - `docs/ane_state.md`
    - `docs/ane_next.md`
    - `docs/ane_log.md`
- 证据：
  - `0x9306924`
    `str w21, [sp+0x3c]`
    与
    `0x930692c`
    `mov w21, #0`
    当前表明：
    `[sp+0x3c]`
    是 previous-w21 snapshot，
    不是当前
    `__INIT,__text`
    section 自带的静态属性位
  - `0x9306c44`
    `ldr w8, [sp+0x3c]`
    当前说明：
    `__INIT,__text`
    的
    `Type3-vs-Type4`
    split
    当前读的就是这个 previous-runtime-carry snapshot
  - `0x9306e18`
    `mov w21, #1`
    是当前
    `ANE_ProgramInitialSetup`
    visible body
    里唯一的 non-zero writer，
    且位于
    `__RUNTIME,__runtime`
    lane
  - success path 末尾：
    `0x93061c8`
    `and w8, w21, #1`
    `0x93061cc`
    `strb w8, [x20, #0x8a]`
    当前把这一 bit
    durable 地写入
    `additional_params+0x8a`
  - `createProgramResource(...)`
    开头：
    `0x928b254`
    `ldrb w8, [x2, #0x8a]`
    `0x928b258`
    `tbz w8, #0, 0x928b278`
    已直接证明：
    `additional_params+0x8a bit0`
    是
    `RTGraph-vs-Legacy`
    resource-class selector
    - `bit0==0`
      -> `ANEProgramLegacyResource::create`
    - `bit0==1`
      -> 检查
         `device+0x3db8`
         / `device+0x3674`
         后走
         `ANEProgramRTResource::create`
         或显式报
         `Firmware does not support RTGraph macho`
- 结论：
  - 当前可以更强地说：
    `__RUNTIME,__runtime`
    不是 top-level Type4 seed，
    但也不是 dead lane；
    它是当前 machine-local
    唯一会把
    runtime-carry
    置 1 的 section family
  - 这条 carry
    至少有两类当前可见作用：
    1. 作为 previous-w21 snapshot，
       gate
       `__INIT,__text`
       的
       `Type3-vs-Type4`
       split
    2. 作为 durable field，
       publish 到
       `additional_params+0x8a`
       并被
       `createProgramResource()`
       直接消费为
       `RTGraph-vs-Legacy`
       resource-class selector
  - 这让当前 bridge
    明确推进到了：
    `section-family semantics`
    -> `runtime carry`
    -> `additional_params+0x8a`
    -> `program resource class selection`
- 下一步：
  - 继续判断
    `__INIT,__text`
    alternate `Type3`
    lane
    是否会在更低层
    join 回
    RTGraph / `resource+0x50`
    相关路径，
    还是仅仅作为
    runtime-carry 触发下的独立旁路
  - 再往下比较
    `ANEProgramRTResource::create`
    和
    `ANEProgramLegacyResource::create`
    的更深行为差异，
    看它最终怎样影响
    transformer
    `segment/cache/load/eval`
    的形态
- 补充证据：
  - 用 IDA 直接补函数并反编：
    - `0xfffffe00092fa738`
      `ANEProgramLegacyResource::create`
    - `0xfffffe0009308fac`
      `ANEProgramRTResource::create`
  - 当前最早类内差异已确认：
    - Legacy create：
      `gMetaClass alloc`
      + `result+0x10 = device`
    - RT create：
      `gMetaClass alloc`
      + `result+0x10 = device`
      + `result+0x40333 = 1`
  - 这进一步强化：
    `additional_params+0x8a bit0`
    已不是抽象分支条件，
    而是立即 materialize 成
    不同 program-resource class
    的对象初始化差异
- 时间：2026-06-13 10:31:02 +0800
- 目标：验证
  `ANEProgramRTResource::create`
  里
  `result+0x40333 = 1`
  这条 RT-only object flag
  是否已经在当前 machine-local
  被更下游的 request / abort 路径真正消费。
- 动作：
  - 新增 probe：
    `mps/ANE/experiments/ane_bootkc_rt_mode_flag_consumers_probe.py`
  - 运行输出：
    `mps/ANE/.ane_runs/csv/ane_bootkc_rt_mode_flag_consumers_probe.csv`
  - 新增结果 note：
    `mps/ANE/experiments/results/rt_mode_flag_consumers_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
    - `docs/ane_log.md`
- 证据：
  - 当前 machine-local
    `resource+0x40333`
    的 visible writer
    仍只有：
    `ANEProgramRTResource::create`
    的
    `result+0x40333 = 1`
  - `ProcessAbort`
    当前已直接消费这条 flag：
    - `0x927e738`
      `ldrb w10, [x25, #0x333]`
    - `0x927e73c`
      `tbz w10, #0, ...`
    - bit0==1
      时走：
      `sendSetupCmd(0x403, resource+0x2f0, ...)`
  - `ANE_ProgramSendRequest_gated`
    当前也直接消费这条 flag：
    - `0x92976b0`
      `ldrb w8, [x8]`
    - `0x92976b4`
      `tbz w8, #0, ...`
    - bit0==1
      时改走
      resource vtable
      `+0x148`
    - bit0==0
      时回到
      `ANE_ProgramPrepareAndSubmitRequest_gated`
  - 当前 machine-local
    resource vtable decode
    也已对上：
    - `ANEProgramResource::vtable +0x148`
      -> `ANEProgramResource::programRTSendInferenceRequest`
    - `ANEProgramLegacyResource::vtable +0x148`
      -> `ANEProgramResource::programRTSendInferenceRequest`
    - `ANEProgramRTResource::vtable +0x148`
      -> `ANEProgramRTResource::programRTSendInferenceRequest`
- 结论：
  - 当前 machine-local 上，
    `additional_params+0x8a bit0`
    已不只是
    `RTGraph-vs-Legacy`
    create selector
  - 更完整的当前可见链条已推进到：
    `section-family semantics`
    -> `runtime carry`
    -> `additional_params+0x8a`
    -> `resource class`
    -> `resource+0x40333`
    -> `request/abort mode split`
  - 也就是说，
    当前已经看到：
    `__RUNTIME,__runtime`
    这条语义
    不是局部死 flag，
    而是会一路影响到
    request path
    与
    abort path
- 下一步：
  - 继续沿
    `programRTSendInferenceRequest`
    family
    往下追，
    但当前更准确的问题
    已收敛成：
    在
    `ANERequest::create/init`
    之前，
    它比 generic
    `PrepareAndSubmit`
    多了哪些
    resource-mode-specific
    orchestration / validation / setup
    字段与 side effects
  - 同时对照
    `__INIT,__text`
    alternate `Type3`
    lane，
    判断这条 RT-specific request path
    是否就是它在更低层的 join 点之一
- 时间：2026-06-13 11:30:06 +0800
- 目标：验证
  `resource+0x40333`
  把 request path
  送进
  `programRTSendInferenceRequest`
  之后，
  当前 machine-local 上
  是否仍会回到
  common
  `ANERequest::create/init`
  bridge。
- 动作：
  - 新增 probe：
    `mps/ANE/experiments/ane_bootkc_rt_send_convergence_probe.py`
  - 运行输出：
    `mps/ANE/.ane_runs/csv/ane_bootkc_rt_send_convergence_probe.csv`
  - 新增结果 note：
    `mps/ANE/experiments/results/rt_send_convergence_note.md`
  - 更新：
    - `docs/ane_state.md`
    - `docs/ane_next.md`
    - `docs/ane_log.md`
- 证据：
  - base
    `ANEProgramResource::programRTSendInferenceRequest`
    当前只是 error stub
  - generic path：
    - 先读
      `additional_params`
      pair
    - 走
      `ANE_ProgramCheckandPrewireBuffers_gated`
    - 再调
      `ANERequest::create`
  - RT path：
    - 当前也读同一
      `additional_params`
      family
    - 也走
      `ANE_ProgramCheckandPrewireBuffers_gated`
    - 然后同样调
      `ANERequest::create`
  - `ANERequest::create`
    当前仍会 forward 到
    `ANERequest::init`
- 结论：
  - `resource+0x40333`
    确实把 request path
    分成
    generic
    与
    RT
    两支
  - 但这两支
    当前 machine-local 上
    不是在 request-object lowering
    层彻底分家；
    它们会在
    `ANERequest::create/init`
    这一层重新汇合
  - 所以当前真正值得继续追的
    不是
    “RT path 会不会创建不同 request object”，
    而是：
    在创建 common request object 之前，
    RT path
    比 generic path
    多出来的
    orchestration / validation / setup
    差异字段
- 时间：2026-06-13 17:20:00 +0800
- 目标：把 `ida-pro-mcp` 新确认的 `AppleNeuralEngine` runtime 语义直接映射到 bridge，
  验证是否能把 wrapper/client-model route 的重复 `loadModel`
  也降成 `runtime_clone`，并尝试在 `test_clean.m4a` full-audio 上拿到新 wall time。
- 动作：
  - 通过 `ida-pro-mcp` 接管现成：
    - `/Volumes/2T/dsc_arm64e_extract/System/Library/PrivateFrameworks/AppleNeuralEngine.framework/Versions/A/AppleNeuralEngine.i64`
    - `/Volumes/2T/dsc_arm64e_extract/System/Library/PrivateFrameworks/ANECompiler.framework/Versions/A/ANECompiler.i64`
  - 反编译并确认：
    - `+[_ANEInMemoryModelDescriptor modelWithMILText:weights:optionsPlist:]`
    - `+[_ANEInMemoryModelDescriptor modelWithNetworkDescription:weights:optionsPlist:]`
    - `+[_ANEInMemoryModel inMemoryModelWithDescriptor:]`
    - `-[_ANEInMemoryModel initWithDesctiptor:]`
    - `-[_ANEInMemoryModel saveModelFiles]`
    - `-[_ANEInMemoryModel compilerOptionsWithOptions:isCompiledModelCached:]`
    - `-[_ANEClient connectionForLoadingModel:options:]`
    - `___44-[_ANEClient doLoadModel:options:qos:error:]_block_invoke`
    - `___44-[_ANEClient doLoadModel:options:qos:error:]_block_invoke_2`
    - `+[_ANEVirtualClient shouldUsePrecompiledPath:options:shouldUseChunking:chunkingThreshold:]`
  - 在 `mps/maderix_ANE/bridge/ane_bridge.m`
    扩展 runtime template cache：
    - 不再只接受 `_ANEInMemoryModel`
    - 也允许缓存已 `loadModel` 成功的 `_ANEModel`
    - clone 时优先从 cached `_ANEModel`
      恢复 runtime-visible state
  - 重新 `cd mps/maderix_ANE/bridge && make`
  - 跑新的 smoke / focused validation：
    - `benchmark_results/private_ane/runtime_clone_wrapper_client_route_smoke_after_patch.json`
    - `benchmark_results/private_ane/runtime_clone_real_ffn_load_roundtrip_after_patch.json`
    - `benchmark_results/private_ane/runtime_clone_real_block_wrapper_roundtrip_after_patch.json`
    - `benchmark/private_ane_real_block_probe.py --axis freq --batch 1 --seq 64 --blocks 1 --gelu-mode EXACT`
  - 尝试复跑：
    - `test_clean.m4a`
    - full-audio
    - batch4
    - wrapper-route
    - baseline none
    - 输出目标：
      `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4_runtimeclone_clientmodel_after_patch.json`
- 证据：
  - 静态：
    - `-[_ANEClient connectionForLoadingModel:options:]`
      只在 `kANEFModelType == kANEFModelPreCompiled`
      时选 fast connection
    - `___44-[_ANEClient doLoadModel:options:qos:error:]_block_invoke`
      仅在 `kANEFModelHasCacheURLIdentifierKey`
      为真时跳过 sandbox extension
    - `___44-[_ANEClient doLoadModel:options:qos:error:]_block_invoke_2`
      成功后写回：
      `modelAttributes/state/programHandle/intermediateBufferHandle/queueDepth/cacheURLIdentifier/program/mapper`
    - `+[_ANEVirtualClient shouldUsePrecompiledPath:options:shouldUseChunking:chunkingThreshold:]`
      确认真正 precompiled path
      必须是 `.hwx` file URL
  - 动态：
    - wrapper linear smoke：
      第一次 `load_cache_client_wrapper_mil`
      第二/三次 `runtime_clone`
      eval 全部成功
    - real weighted FFN：
      第一轮 `load_wall_sec ≈ 0.157s`
      第二轮 `runtime_clone` 后
      `load_wall_sec ≈ 0.00126s`
      checksum 一致
    - real transformer block：
      round2 的 `pre/gate/ffn`
      三段全部 `bridge_profile_route = runtime_clone`
  - full-audio 尝试：
    - `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4_runtimeclone_clientmodel_after_patch.private_ane_child/parent_watchdog_failure.json`
    - child 已进入真实主链：
      - `stft_preload_done`
      - `batch_start`
      - 多个 `stft_start/stft_done`
      - `mask_batch_start`
    - 但 native supervisor 最终以
      `compressor_memory`
      终止 child
- 结论：
  - 这次 bridge 改动不是纸面推断，已经把
    wrapper/client-model route
    的重复 `loadModel`
    实际压成了 `runtime_clone`，
    且在 real weighted FFN / real transformer block 上成立。
  - 当前离 `test_clean.m4a` 新 wall time 只差最后一层系统级运行门槛：
    native supervisor 的 `compressor_memory` 阈值。
  - 所以下一轮优先任务不再是继续证明 clone correctness，
    而是安全地拿到完整 full-audio wall time 证据。

## 2026-06-13
- 时间：2026-06-13 17:43:42 +0800
- 目标：在清空无关应用后的较干净系统基线下，重新跑 `test_clean.m4a` full-audio
  batch4 wrapper-route benchmark，确认是否还会被系统级内存保护杀掉，并拿到
  可用于后续速度拆解的完整 wall time。
- 动作：
  - 先检查系统内存状态：
    - `vm_stat`
    - `sysctl vm.swapusage`
    - `memory_pressure`
  - 再复跑 benchmark：
    - 先按原配置跑一次，确认旧的 `compressor_memory` 问题是否消失
    - 随后把 `--private-ane-child-timeout-sec` 提到 `600`，避免 180s 默认超时把完整结果截断
  - 运行命令：
    - `ANE_BRIDGE_RUNTIME_CLONE_CACHE=1 ... benchmark/private_ane_test_clean_benchmark.py --baseline none --audio test_clean.m4a --full-audio --private-ane-allow-long-audio --private-ane-child-timeout-sec 600 --private-ane-chunk-batch-size 4 --private-ane-fused-band-split --private-ane-fused-band-split-max-outputs 4 --private-ane-fused-mask-estimator --private-ane-fused-mask-estimator-max-outputs 2 --private-ane-persistent-aux-handles --private-ane-persistent-stft-handles --private-ane-preload-stft-handles`
- 证据：
  - 成功输出：
    `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4_runtimeclone_clientmodel_after_patch_timeout600.json`
  - 结果摘要：
    - `private_ane.seconds = 76.6213315409841`
    - `exit_status = 0`
    - `kill_reason = null`
    - `transformer_sec = 52.34276712499559`
    - `transformer_compile_sec = 11.94899945706129`
    - `transformer_eval_sec = 32.93408137385268`
    - `band_split.wall_sec = 2.434334042016417`
    - `mask.wall_sec = 13.802996542013716`
    - `istft.wall_sec = 5.9245834170724265`
    - `max_child_rss_mb = 1675.109`
    - `max_compressor_mb = 1288.469`
    - `max_swap_used_mb = 1142.062`
  - 旧失败对照仍保留：
    `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4_runtimeclone_clientmodel_after_patch.private_ane_child/parent_watchdog_failure.json`
- 结论：
  - 清空无关应用后，系统级 compressor / swap 压力已经降下来，`test_clean.m4a`
    full-audio 可以完整跑完。
  - 现在主问题回到速度本身，且最大热点仍然是 transformer 主段，不再是内存 kill。
- 下一步：
  - 继续拆 `transformer_sec` 的内部耗时，优先看 compile / eval / axis-pack / load_qos。

- 时间：2026-06-13 21:06:22 +0800
- 目标：继续收窄 `pre` packed public route 到底是不是可用的减少分段入口，先把
  file-route 三输出和 dir-route MIL 单输出的真实语义钉死。
- 动作：
  - 修正 `benchmark/private_ane_pre_threeout_compare.py`：
    - probe 与 torch 共用同一份真实输入，不再拿零输入对随机 torch 比
    - 增加 shape fallback、全排列比对
  - 扩展 `benchmark/ane_weighted_client_eval_threeout_probe.m`：
    - 支持真实输入文件
    - 支持自定义 output index list
    - 支持 `dir_key_empty` / `mil_model_type`
  - 扩展 `benchmark/ane_weighted_client_eval_probe.m`：
    - 新增 `dir_key_empty`
    - 新增 `mil_model_type` option
  - 生成并保存：
    - `benchmark_results/private_ane/weighted_fresh_pack_pre_threeout_compare_freq64.json`
    - `benchmark_results/private_ane/weighted_fresh_pack_pre_output_index_probe.json`
    - `benchmark_results/private_ane/weighted_client_eval_probe_pre_packed_variants_with_dir_key_empty.json`
    - `benchmark_results/private_ane/weighted_fresh_pack_pre_dir_mil_single_compare_freq64.json`
- 证据：
  - `weighted_fresh_pack_pre_threeout_compare_freq64.json`
    - `file_key_empty` + `[0,1,2]` + 真实输入下 `eval_ok = true`
    - 但 `out0/out1/out2` 三份输出逐字节完全一致
    - best mapping 到 `qraw/kraw/v` 的 `mean_abs` 总和仍为 `0.5846427977`
  - `weighted_fresh_pack_pre_output_index_probe.json`
    - `[0]` / `[1]` / `[2]` 单独请求都 `eval_ok = false`
    - 只有 `[0,1,2]` 一起请求时 `eval_ok = true`
  - `weighted_client_eval_probe_pre_packed_variants_with_dir_key_empty.json`
    - `dir_key_empty + empty/file_opts` 走回 `model.espresso.net` clone 失败
    - `dir_key_empty + mil_model_type` 则能 `compile_ok = true`,
      `load_ok = true`, `eval_ok = true`
  - `weighted_fresh_pack_pre_dir_mil_single_compare_freq64.json`
    - `dir_key_empty + mil_model_type + output[0]` 虽然成功 eval，
      但对 torch `att_flat`：
      - `mean_abs = 0.4253934920`
      - `max_abs = 242.2471008301`
- 结论：
  - `pre` 的 file-route three-output 不是可用的真实 `q/k/v` 契约，只是一个
    “三输出一起请求才成功、且三份输出完全相同”的假入口。
  - `pre` 的 dir-route 只有显式 `kANEFModelType = kANEFModelMIL` 才能 compile/eval，
    但其单输出数值仍错误，所以“compile/load/eval 成功”不等于 contract 正确。
  - 当前真正值得继续追的不是“file-route 三输出能不能接进 runtime”，而是
    public client / runtime 在 dir-MIL 路上到底还缺了哪层 companion/retain/contract
    语义，导致它能跑但输出错。
- 下一步：
  - 优先比较 `dir_key_empty + mil_model_type` 与已知数值正确的 wrapper-companion MIL
    路之间，到底还差了哪些 compile/load companion 或 retain 语义。
  - 不要再优先重复 file-route three-output 的 `q/k/v` 替代设想。

- 时间：2026-06-13 21:28:00 +0800
- 目标：确认“`dir_key_empty + mil_model_type` 数值错”到底是不是 public route 的锅，
  还是 artifact/reference 身份问题。
- 动作：
  - 直接把同一份随机输入喂给：
    1. packed artifact private in-memory
    2. wrapper-companion public route
    3. 当前 torch `pre(att_flat)` 参考
  - 新增并保存：
    - `benchmark_results/private_ane/weighted_pre_private_vs_public_vs_torch_freq64.json`
    - `benchmark_results/private_ane/weighted_pre_wrapperroot_bruteforce_matches_freq64.json`
    - `benchmark_results/private_ane/weighted_pre_weight_match_scan.json`
  - 另外用同一 public probe 直接打到
    `mps/ANE/.ane_runs/runtime_wrapper_aug_weighted_pre/add_all_fresh_rebuilt_81M03F`
    上，排除“缺 wrapper companion 文件”这个猜测。
- 证据：
  - `weighted_pre_private_vs_public_vs_torch_freq64.json`
    - private in-memory vs wrapper public:
      - `mean_abs = 0`
      - `max_abs = 0`
    - 二者对当前 torch `att_flat` 都是：
      - `mean_abs = 0.4253934920`
      - `max_abs = 242.2471008301`
  - `weighted_pre_wrapperroot_bruteforce_matches_freq64.json`
    - 对 model 内所有 layer/axis 的 `pre(att_flat)` brute-force 后，
      没有任何一个 block 接近匹配；
      best 仍是 layer0/freq，`mean_abs = 0.4253934920`
  - `weighted_pre_weight_match_scan.json`
    - 按当前 `model.mil` 偏移直接解析 `packed.bin` 后，
      `gamma/Wq/Wk/Wv` 也不接近当前 checkpoint 中任一 layer/axis 的同名权重
- 结论：
  - 当前“数值不对”不能再归因到 `dir_key_empty + mil_model_type` 这条 public route；
    它与 private in-memory 在同一 artifact 上逐值完全一致。
  - 真正需要优先确认的是：
    1. `weighted_fresh_pack_pre_1781215248` 的真实 provenance / layer identity
    2. 或者我们对 `packed.bin` 的直接偏移解析并不等于其真实权重语义
- 下一步：
  - 优先反查 `weighted_fresh_pack_pre_1781215248` 的生成来源；
  - 若来源仍不清楚，再最小化复现“从当前 checkpoint 生成一份已知 layer/axis 的 fresh packed pre”，
    用同一套 probe 验证它与 torch 是否对齐。

- 时间：2026-06-13 22:08:00 +0800
- 目标：验证旧 `weighted_fresh_pack_pre_1781215248` 到底是不是 stale/foreign packed
  artifact，并在确认后把 `pre` public contract 实验切到当前 checkpoint 重生产物。
- 动作：
  - 追到真实生成入口：
    - `pymss/modules/bs_roformer/private_ane.py` 里的 `attention_pre_mil/_pre_weights`
      实际来自 `benchmark/private_ane_real_attention_split_probe.py`
    - single `packed.bin` 由
      `mps/maderix_ANE/bridge/ane_bridge.m:bridge_write_client_packed_artifact(...)`
      动态从 `gamma.bin/wq.bin/wk.bin/wv.bin/cos.bin/sin.bin` 拼接而成
  - 用当前 checkpoint `layer0/freq` 重新生成一份 fresh public-packed pre：
    - `benchmark_results/private_ane/regen_pre_freq0_publicpacked_1781359181`
  - 固化稳定路径：
    - `benchmark_results/private_ane/weighted_pre_current_freq0_publicpacked_stable`
  - 重跑对照：
    - `regen_pre_freq0_publicpacked_compare_1781359181.json`
    - `regen_pre_freq0_threeout_compare_freq64.json`
    - `regen_pre_freq0_dir_mil_single_compare_freq64.json`
    - `regen_pre_freq0_private_vs_public_dir_mil_freq64.json`
- 证据：
  - `regen_pre_freq0_publicpacked_compare_1781359181.json`
    - `model.mil` hash 与旧 artifact 相同
    - `packed.bin` hash 不同：
      - old `c52c1f2a34339012c6b1d9b9b83198e5095a692b`
      - new `a35ecad57d7756b1616f3319b4dbbb5028f3413c`
    - 新 packed artifact 对 torch `att_flat`：
      - `mean_abs = 3.4188e-05`
      - `max_abs = 1.8311e-04`
    - 旧 packed artifact 对 torch `att_flat`：
      - `mean_abs = 0.4253934920`
      - `max_abs = 242.2471008301`
  - `regen_pre_freq0_threeout_compare_freq64.json`
    - 在正确 packed artifact 上，file-route three-output 仍错误；
      只是它已经不是“三份完全一样”的旧假输出了
  - `regen_pre_freq0_dir_mil_single_compare_freq64.json`
    - `dir_key_empty + mil_model_type` 对 torch：
      - `mean_abs = 0.0252261721`
      - `max_abs = 0.1537094116`
  - `regen_pre_freq0_private_vs_public_dir_mil_freq64.json`
    - regenerated artifact 上，
      `dir MIL public` 相比 `private in-memory` 仍有：
      - `mean_abs = 0.0252202097`
      - `max_abs = 0.1535949707`
- 结论：
  - 旧 `weighted_fresh_pack_pre_1781215248` 的核心问题已经确定是 `packed.bin`
    stale/foreign，不是当前 checkpoint 导出。
  - 但切到当前 checkpoint 重新生成的正确 packed artifact 后，
    public contract 问题并没有消失：
    - file-route three-output 仍错
    - dir-route 单输出虽已大幅改善，但仍未完全等价 private in-memory
- 下一步：
  - 后续 `pre` public contract 验证默认使用：
    `benchmark_results/private_ane/weighted_pre_current_freq0_publicpacked_stable`
  - 优先查 regenerated artifact 上：
    1. file-route three-output 为什么仍错
    2. `dir_key_empty + mil_model_type` 为什么仍比 private 多一个 `mean_abs~0.025`

- 时间：2026-06-13 22:15:00 +0800
- 目标：确认 regenerated artifact 上 `dir MIL` 的残余误差是不是 client 构造路径导致，
  并验证 `file-route three-output` 是否也受同一因素影响。
- 动作：
  - 给 `benchmark/ane_weighted_client_eval_threeout_probe.m` 增加 `client_variant`
    参数，支持：
    - `shared`（默认）
    - `restricted_no`
  - 生成并保存：
    - `benchmark_results/private_ane/weighted_pre_current_freq0_restricted_no_mil_compare_freq64.json`
    - `benchmark_results/private_ane/weighted_pre_current_freq0_threeout_restricted_no_compare_freq64.json`
    - `benchmark_results/private_ane/regen_pre_freq0_wrapper_restricted_no_mil_compare_freq64.json`
- 证据：
  - `weighted_pre_current_freq0_restricted_no_mil_compare_freq64.json`
    - 在稳定 current packed artifact 上，
      `restricted_no + dir_key_empty + mil_model_type`
      与 private in-memory 逐值完全一致
    - 对 torch `att_flat`：
      - `mean_abs = 3.4188e-05`
      - `max_abs = 1.8311e-04`
  - `regen_pre_freq0_wrapper_restricted_no_mil_compare_freq64.json`
    - 在 regenerated wrapper root 上也得到同样结论：
      `restricted_no + mil_model_type` 与 private/torch 完全对齐
  - `weighted_pre_current_freq0_threeout_restricted_no_compare_freq64.json`
    - 即便换成 `restricted_no`，
      file-route three-output 的最佳对齐分数仍然不变：
      `best_score = 0.4999011457`
- 结论：
  - regenerated artifact 上，
    `dir MIL` 的残余 `mean_abs~0.025` 已确认不是 artifact 问题，
    而是 `sharedConnection` client 路带来的数值语义差异。
  - file-route three-output 的错误则与 client 构造路径无关；
    它是真正的 lowered contract / output 语义问题。
- 下一步：
  - bridge 若要走当前可用的 `pre` public 路，优先试：
    `initWithRestrictedAccessAllowed:NO` + `dir_key_empty + mil_model_type`
  - 继续把 file-route three-output 当成独立 blocker 线追，不要再和 client 差异混在一起。

- 时间：2026-06-13 22:28:00 +0800
- 目标：把 `restricted_no` 结论从 probe 提升到 bridge/benchmark 可控开关，便于后续真实 smoke。
- 动作：
  - `mps/maderix_ANE/bridge/ane_bridge.m`
    - 新增 `ANE_BRIDGE_CLIENT_VARIANT`
    - 支持：
      - `shared`
      - `private_shared`
      - `restricted_yes`
      - `restricted_no`
    - 当前 wrapper/direct public client load 已改成走统一 client 工厂
  - `pymss/modules/bs_roformer/private_ane.py`
    - 新增 `private_ane_bridge_client_variant` inference param 到 env 映射
  - `benchmark/private_ane_test_clean_benchmark.py`
    - 新增 `--private-ane-bridge-client-variant`
  - 受控 smoke：
    - `benchmark_results/private_ane/bridge_client_variant_probe_restricted_no_pre_freq64.json`
- 证据：
  - `bridge_client_variant_probe_restricted_no_pre_freq64.json`
    - bridge wrapper route:
      - `route = load_cache_client_wrapper_mil`
      - `client_file_loaded = 1`
    - 对 torch `att_flat`：
      - `mean_abs = 3.4188e-05`
      - `max_abs = 1.8311e-04`
- 结论：
  - `restricted_no` 不只是 probe 技巧；已经可作为 bridge/benchmark 的受控运行选项使用。
  - 后续真实 smoke/benchmark 若要验证 `pre` public 路，优先用：
    `--private-ane-bridge-client-variant restricted_no`

- 时间：2026-06-14 00:08:33 +0800
- 目标：补齐 `.hwx file-model precompiled` direct-create 矩阵中的一个小缺口：
  不带 `has_cache_flag` 但带 `skipPreparePhase` 时，是否仍会在 prepare 前
  报 `0x170004`。
- 动作：
  - 读取当前恢复状态与 `precompiled_file_route_probe_time_root_v5.json`
    的 direct matrix。
  - 用现有 probe 跑单例：
    - `/tmp/ane_precompiled_file_route_probe --factory file_source_cache_set --option-variant precompiled_aot_const_seed_attrs_seed_string_id_identity_short_model_skip_prepare <wrapper_root>`
  - 结果写入：
    - `benchmark_results/private_ane/precompiled_file_route_probe_skip_prepare_no_has_cache_1781366852.json`
  - 用 `ida-pro-mcp` 打开 `mps/ANE/experiments/aned_bin.i64`，确认
    `-[_ANEProgramForLoad createProgramInstance...]` 的真正执行体是
    `sub_10000307F`，并在其中先调用 `controller.device` vtable `+0x10`
    创建 `programInstance`；只有 create 成功后，`skipPreparePhase`
    才影响是否进入 prepare 分支。
- 证据：
  - 同一 wrapper root 的 MIL bootstrap 正常：
    - `compile_ok = true`
    - `load_ok = true`
    - `state = 3`
    - `programHandle = 13084134868092`
    - `intermediateBufferHandle = 319979`
    - `queueDepth = 127`
  - `.hwx` precompiled 单例仍失败：
    - `load_ok = false`
    - `load_error = Program load failure (0x170004)`
    - `after_load.state = 5`
    - `programHandle = 0`
    - `load_after_compile_ok = false`
    - `load_after_compile_error = Program load failure (0x170004)`
- 结论：
  - `skipPreparePhase` 不是 `.hwx file-model precompiled` 的解锁点。
  - `0x170004` 在当前 case 中发生于 create-program 阶段，早于
    selector-4 prepare 能介入的位置。
  - 当前主线不应继续扩高层 precompiled option sweep；下一步要么继续下钻
    lower firmware/reply/publish author，要么围绕
    `final_blocker_evidence_package_note.md` 固化 blocker 与工程化路线。
- 下一步：
  - 优先整理最终 blocker 证据和工程方向：
    - warm wrapper-route 作为当前可用路线继续工程化；
    - `.hwx precompiled` 一般化控制层暂列为 lower accepted-state
      author/replay 缺口；
    - 若继续逆向，只从 lower firmware/reply/publish 入口继续，不再扫
      `cacheURLIdentifier/aot/attrs/string_id/skipPrepare`。

- 时间：2026-06-14 00:20:00 +0800
- 目标：把当前可用的 warm wrapper-route 从“手工 export 环境变量”收口成
  module/config/benchmark 的受控开关，并做不触发大内存波动的轻量验证。
- 动作：
  - 新增 module 默认属性：
    - `private_ane_bridge_wrapper_route = "default"`
  - `separator.py`：
    - 将 `private_ane_bridge_wrapper_route` 加入 inference 透传与 config 应用
  - `pymss/modules/bs_roformer/private_ane.py`：
    - `PrivateANETransformerRunner.__init__` 新增统一下发逻辑
    - 启用时设置：
      - `ANE_BRIDGE_CLIENT_FILE_LOAD=1`
      - `ANE_BRIDGE_CLIENT_FILE_LOAD_ALL=1`
      - `ANE_BRIDGE_CLIENT_FILE_PACK_WEIGHTS=1`
      - `ANE_BRIDGE_CLIENT_FILE_WRAPPER=1`
    - 默认 `"default"` 不覆盖已有 env；显式 false 才清理这些 key
  - `benchmark/private_ane_test_clean_benchmark.py`：
    - 新增 `--private-ane-bridge-wrapper-route`
    - 传递到 child argv / inference_params / output json
  - `pymss/utils.py`：
    - summary 新增 `bridge_wrapper_route`
  - 轻量验证：
    - `python -m py_compile ...`
    - `python benchmark/private_ane_test_clean_benchmark.py --help`
    - one-off Python snippet:
      - 验证 benchmark flag -> `inference_params`
      - 验证 runner flag -> wrapper-route env
  - 尝试真实 1s smoke：
    - `test_clean.m4a`
    - `--private-ane-bridge-wrapper-route`
    - `--private-ane-bridge-client-variant restricted_no`
    - `--private-ane-max-transformer-layers 1`
    - 结果被 native supervisor 以 `compressor_memory` 杀掉
- 证据：
  - 轻量验证输出：
    - `ok: benchmark flag -> inference_params, runner flag -> env`
  - 真实 smoke 失败目录：
    - `benchmark_results/private_ane/test_clean_1s_wrapper_route_flag_smoke.private_ane_child/`
  - 当前 machine baseline：
    - free memory 约 `0.4% ~ 1.4%`
    - `compressor_mb` 约 `5.9 ~ 6.1 GB`
    - `swap_used_mb` 约 `1424 MB`
- 结论：
  - wrapper-route 的参数链路已经工程化并经轻量验证通过。
  - 当前真实 smoke 失败主要是系统 headroom 太低，不应解释成新参数未生效。
  - 之后的 warm wrapper-route benchmark/复测可以直接用：
    `private_ane_bridge_wrapper_route=True`
    或
    `--private-ane-bridge-wrapper-route`
- 下一步：
  - 若机器 headroom 恢复，再用这个新开关重跑
    `test_clean.m4a` 真实 warm wrapper-route smoke / full-audio。
  - 在此之前，继续主线时不要再回到手工 env 注入。

- 时间：2026-06-14 00:28:00 +0800
- 目标：把 wrapper-route 工程化链再收口一层，修掉 `bridge_client_variant`
  实际未经过 `separator` 透传的漏洞，并补严格校验。
- 动作：
  - `pymss/modules/bs_roformer/private_ane.py`
    - `private_ane_bridge_wrapper_route` 无效字符串现在直接 `ValueError`
  - `pymss/modules/bs_roformer/common.py`
    - 新增默认值：
      `private_ane_bridge_client_variant = "default"`
  - `pymss/separator.py`
    - 将 `private_ane_bridge_client_variant` 加入
      `INFERENCE_PARAM_TARGETS` / `PASSTHROUGH_INFERENCE_PARAMS`
    - 新增 module 赋值与严格校验：
      `default/shared/private_shared/restricted_yes/restricted_no`
    - `private_ane_bridge_wrapper_route` 的字符串解析也改为严格校验
  - 轻量验证：
    - `python -m py_compile ...`
    - `MSSeparator.update_inference_params(...)`
      同时保存
      `private_ane_bridge_client_variant=restricted_no`
      与
      `private_ane_bridge_wrapper_route=True`
    - runner 侧：
      - wrapper-route `true/false/default` 语义正确
      - invalid `bridge_client_variant` / invalid `bridge_wrapper_route`
        都会报错
- 证据：
  - `ok: separator.update_inference_params stores bridge client + wrapper route`
  - `ok: wrapper-route default/true/false wiring verified`
  - `private_ane_bridge_client_variant must be one of ...`
  - `private_ane_bridge_wrapper_route must be one of ...`
- 结论：
  - 现在 wrapper-route 与 `restricted_no` 已经都属于完整的
    benchmark -> separator -> module -> runner 工程化链路，
    不再只是局部 env 技巧。
  - 后续真实 smoke 若失败，应优先按系统 headroom 或 lower route
    解释，不再先怀疑参数没有传到 runner。
- 下一步：
  - 机器 headroom 恢复后，用
    `--private-ane-bridge-wrapper-route --private-ane-bridge-client-variant restricted_no`
    重跑 `test_clean.m4a` 真实 warm wrapper-route smoke / full-audio。

- 时间：2026-06-14 02:18:00 +0800
- 目标：验证 local selector-3 create 成功是否只是因为 probe 使用了和 daemon
  不同的 visible request layout。
- 动作：
  - 修改：
    - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
  - 新增 request layout 变体：
    - `legacy`
    - `daemon`
  - 新 `daemon` layout 依据 `aned_bin:sub_10000307F` 的当前静态写入面，
    把关键 request 字段移动到：
    - `0x10 / 0x11 / 0x31 / 0x54 / 0x58 / 0x5c / 0x60 / 0x68 / 0x158 / 0x16c / 0x56c / 0x96c`
  - 重编：
    - `/tmp/ane_services_program_create_runtime_probe`
  - 在稳定 artifact root 上跑对照：
    - `mps/ANE/.ane_runs/runtime_wrapper_aug_weighted_ffn/add_all`
  - 结果写入：
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_layout_compare_1781377876.json`
  - 新增说明文档：
    - `mps/ANE/experiments/results/selector3_request_layout_compare_note.md`
- 证据：
  - `legacy` 四个 case：
    - `status = 0`
    - `prepare1 = 0x14`
    - `prepare1_owner0_ready1 = 0x02`
    - `raw_create_status = 0`
  - `daemon` 四个 case：
    - `status = 0`
    - `wrapper+0x70 = 0`
    - `payload+0xda8 = 0`
    - `payload_u8_0xde0 = 4`
    - `destroy = 0x14`
  - 两种布局在 create 后的 wrapper-visible state 仍然同样卡住
- 结论：
  - local selector-3 “success” 不是因为旧 probe 采用了错误的 visible
    request offsets。
  - 把 request field placement 改得更像 daemon 后，
    仍然不会 materialize accepted runtime state。
  - 因而当前 gap 仍然更像 lower accepted-state
    materialization / replay / publish，而不是 selector-3 request layout 本身。
- 下一步：
  - 不再优先追 “local probe request layout 是否错”。
  - 继续主线时，优先回到 lower reply/publish / accepted-state author。

- 时间：2026-06-14 02:43:00 +0800
- 目标：验证 base-create 线上“visible local process-args tuple”这条旧方向是否可靠，
  并纠正 `ane_bootkc_base_create_process_args_probe.py` 的误导性结论。
- 动作：
  - 手工小窗反汇编 `ANEHWDevice::ANE_ProgramCreate_gated(...)`
    发现旧 probe 指向的 `0xfffffe000928becc` 实际是：
    - `ANEProgramResource::ANE_CleanupResourcesAllocatedForInitialSetup`
    - 不是 `ANE_ProcessCreate_gated(...)`
  - 重写：
    - `mps/ANE/experiments/ane_bootkc_base_create_process_args_probe.py`
    - 从旧的固定 offset 假设，改成扫描：
      - `ANEHWDevice::ANE_ProgramCreate`
      - `ANEHWDevice::ANE_ProgramCreate_gated`
      的 visible direct `bl` call graph
  - 重跑 fresh probe：
    - `mps/ANE/.ane_runs/csv/ane_bootkc_base_create_process_args_probe.csv`
  - 新增说明文档：
    - `mps/ANE/experiments/results/basecreate_direct_bl_correction_note.md`
- 证据：
  - `ANEHWDevice::ANE_ProgramCreate`
    - visible direct BL count = 35
    - direct `ANE_ProcessCreate_gated` calls = 0
    - direct cleanup calls = 1
  - `ANEHWDevice::ANE_ProgramCreate_gated`
    - visible direct BL count = 22
    - direct `ANE_ProcessCreate_gated` calls = 0
    - direct cleanup calls = 1
  - `ANE_ProgramCreate_gated` current visible direct call graph 包含：
    - `ANE_HandlePowerStateChecksForClient`
    - `ANE_PowerOn_gated`
    - `ANEProgramResource::ANE_CleanupResourcesAllocatedForInitialSetup`
    - `findClient`
    - `acquireDartMapLock`
    - `ReleaseProgramResource`
    - `releaseDartMapLock`
    - `EnableMemoryUnwireTimer`
    - `commandWakeup`
    - 但不包含 direct `ANE_ProcessCreate_gated` / `ProgramLoad`
- 结论：
  - 旧的 offset-based “base-create visible local process-args tuple” 结论不应再当作
    事实源。
  - base-create 若存在 process-create / accepted-state rebuild，
    当前已经在 direct visible BL lowering 之下。
  - 这条纠偏会把主线重新收敛到：
    provisional resource insertion -> subclass load -> client attach
    -> later reply/publish
- 下一步：
  - 不再主要追 “base-create 本地 process-args field0/8/10”。
  - 继续主线时，优先围绕：
    `programLoadFromMachoFile(...)` success requirements
    / `client_ctx+0x18` attach
    / later accepted-state publish。

- 时间：2026-06-14 04:20:00 +0800
- 目标：把 `programLoadFromMachoFile(...)` 内部 publish/gate 链与 caller 的
  `client_ctx+0x18` attach 明确分层，判断 attach 是否只是 post-return membership。
- 动作：
  - 新增只读 bootkc probe：
    - `mps/ANE/experiments/ane_bootkc_programload_attach_boundary_probe.py`
  - 该 probe 不再依赖 capstone，直接从 raw bootkc bytes 手工解
    direct `bl`，并结合已有地址锚点记录：
    - Legacy / RT `programLoadFromMachoFile`
      的 direct-BL 图
    - load 内部：
      - early `resource+0x493a0`
        publish
      - `ANE_ProcessCreate_gated(...)`
      - late `findClient(...)`
      - late
        `*external_output = additional_params+0x18`
        publish
    - caller `ANE_ProgramCreate_gated`
      里的：
      - slot `+0x138` dispatch
      - nonzero rollback
      - post-return `findClient(...)`
      - `client_ctx+0x18` attach
      - pending clear
  - 跑 fresh probe：
    - `mps/ANE/.ane_runs/csv/ane_bootkc_programload_attach_boundary_probe.csv`
  - 新增说明文档：
    - `mps/ANE/experiments/results/programload_client_attach_boundary_note.md`
- 证据：
  - Legacy `programLoadFromMachoFile`
    direct-BL summary：
    - `ANE_ProcessCreate_gated` x1
    - `findClient` x2
    - `preProcess` x1
    - `aneCmdSend` x2
    - `_memmove` x3
  - RT `programLoadFromMachoFile`
    direct-BL summary：
    - `ANE_ProcessCreate_gated` x1
    - `findClient` x2
    - `preProcess` x1
    - `sendSetupCmd` x3
    - `_memmove` x2
  - load-side tracked facts：
    - Legacy：
      - early resource publish `+0x2a4`
      - ProcessCreate `+0xa84`
      - late findClient `+0x1038`
      - late external-output publish `+0x1064`
    - RT：
      - early resource publish `+0x1cc`
      - ProcessCreate `+0x884`
      - late findClient `+0xa30`
      - late external-output publish `+0xa54`
  - caller-side tracked facts：
    - subclass load dispatch `+0x568`
    - branch on nonzero load status `+0x570`
    - post-return findClient `+0x588`
    - `client_ctx+0x18` attach `+0x5bc`
    - pending clear after attach `+0x6f0`
- 结论：
  - 当前不能再把 `client_ctx+0x18` attach 当作：
    - first visible client gate
    - first visible external-output publish
    - 或 `ProgramLoad` 成功侧的主要未知数
  - 更准确的是：
    - Legacy / RT `programLoadFromMachoFile`
      自己内部已经有
      ProcessCreate / findClient / publish
    - `client_ctx+0x18` attach
      是 caller `ANE_ProgramCreate_gated`
      在 subclass load 返回 `0` 之后做的
      post-return membership attach
  - 因而当前主线更适合继续写成：
    provisional resource insertion
    -> subclass load 自带 internal publish/gate
    -> caller-side attach
    -> 更低的 accepted-state / reply / publish author
- 下一步：
  - 不再优先解释 attach 的命名或类型。
  - 优先继续追：
    1. ProgramLoad 内部两次 `findClient(...)`
       与 post-return attach
       之间，到底还差哪层 accepted-state coherence
    2. attach / pending-clear 之后，
       为什么仍不能走到更低 reply/publish author

- 时间：2026-06-14 04:45:00 +0800
- 目标：确认 `ANE_ProgramCreate_gated(...)` 在 subclass load 返回 `0` 之后的
  visible tail 是否还直接碰 lower async completion/reply path，还是只剩 housekeeping。
- 动作：
  - 新增只读 bootkc probe：
    - `mps/ANE/experiments/ane_bootkc_programcreate_success_epilogue_probe.py`
  - probe 只扫：
    - `ANE_ProgramCreate_gated + 0x588 .. end`
    - 也就是 post-return `findClient(...)`
      开始的 caller tail
  - 记录：
    - tracked fact offsets：
      `+0x588 / +0x5bc / +0x61c / +0x6a0 / +0x6f0 / +0x6fc / +0x704`
    - direct BL 计数：
      - `findClient`
      - `releaseDartMapLock`
      - `commandWakeup`
      - `EnableMemoryUnwireTimer`
      - `ReleaseProgramResource`
      - `handleOutstandingCommand`
      - `processCommandResponse`
      - `processTargetToHostIOCommand`
      - `setPendingUpdate`
      - `waitForPendingUpdate`
  - 跑 fresh probe：
    - `mps/ANE/.ane_runs/csv/ane_bootkc_programcreate_success_epilogue_probe.csv`
  - 新增说明文档：
    - `mps/ANE/experiments/results/programcreate_success_epilogue_boundary_note.md`
- 证据：
  - post-return region direct-BL 计数：
    - `findClient` x1
    - `releaseDartMapLock` x1
    - `commandWakeup` x2
    - `EnableMemoryUnwireTimer` x1
    - `ReleaseProgramResource` x1
  - 同一区间对 lower async 路的 direct-BL 计数全为 0：
    - `handleOutstandingCommand`
    - `processCommandResponse`
    - `processTargetToHostIOCommand`
    - `setPendingUpdate`
    - `waitForPendingUpdate`
  - tracked success-side fact offsets 仍是：
    - `+0x588` post-return `findClient(...)`
    - `+0x5bc` `client_ctx+0x18` attach
    - `+0x6a0` `releaseDartMapLock(...)`
    - `+0x6f0` clear pending
    - `+0x6fc` `commandWakeup(...)`
    - `+0x704` `EnableMemoryUnwireTimer(...)`
- 结论：
  - 当前 `ANE_ProgramCreate_gated(...)`
    在 subclass load 返回 `0`
    之后的 visible tail，
    已可以更明确地视为：
    - attach / pending clear / wakeup
    - lock / timer housekeeping
  - 当前不应再把这段 tail
    建模成：
    - first async completion entry
    - 或隐藏的 lower accepted-state author
  - 结合上一条
    `programload_client_attach_boundary_note.md`
    后，visible create-side 已能更完整地写成：
    - subclass ProgramLoad
      自带 internal ProcessCreate / findClient / publish
    - caller post-return tail
      只做 membership / pending / wakeup housekeeping
    - 剩余 gap 更该下沉到
      later async completion /
      request-removal /
      lower reply-publish path
- 下一步：
  - 不再主要盯 `ANE_ProgramCreate_gated(...)` success epilogue。
  - 优先切到：
    1. 哪条 success-side async completion /
       request-removal 路
       真正接管 create-side 之后的 lower author
    2. `processTargetToHostIOCommand(...)`
       是否比 default
       `processCommandResponse(...)`
       更接近缺失的 reply-publish/control 层

- 时间：2026-06-14 05:10:00 +0800
- 目标：把 plain daemon `createProgramInstanceForModel...` 的 lower gate
  和本地已逆出的 selector 家族正式接成一条链，避免后续再把
  daemon runtime 路和 selector-3/4 路割裂讨论。
- 动作：
  - 读取并对齐已有 machine-local CSV：
    - `mps/ANE/.ane_runs/csv/ane_daemon_program_create_state_chain.csv`
    - `mps/ANE/.ane_runs/csv/ane_services_program_create_chain.csv`
    - `mps/ANE/.ane_runs/csv/ane_services_program_vtable_chain.csv`
    - `mps/ANE/.ane_runs/csv/ane_services_program_runtime_chain.csv`
  - 新增 join 脚本：
    - `mps/ANE/experiments/ane_daemon_program_lower_gate_join.py`
  - 生成聚合结果：
    - `mps/ANE/.ane_runs/csv/ane_daemon_program_lower_gate_join.csv`
  - 新增说明文档：
    - `mps/ANE/experiments/results/daemon_program_lower_gate_join_note.md`
- 证据：
  - joined create row：
    - daemon `device` vtable `+0x10`
    - `0x1000035D0`
    - lower wrapper
      `_ANEServicesProgramCreate`
    - selector 3
    - input `0xd88`
    - output `0xac738`
    - create failure family-4
      `(low16=4, high16=w20)`
  - joined post-create row：
    - `program.programInstance != nil`
      之后才看 `skipPreparePhase`
    - 说明 `skipPreparePhase`
      只能绕过 prepare，
      不能绕过 create
  - joined prepare row：
    - `programInstance` vtable `+0x0`
    - `0x1000039C0`
    - lower wrapper
      `_ANEServicesProgramPrepare`
    - selector 4
    - inout `0x38`
    - prepare failure family-5
      `(low16=5, high16=w21)`
  - joined destroy row：
    - `programInstance` vtable `+0x18`
    - `0x100003A28`
    - lower wrapper
      `_ANEServicesProgramDestroy`
    - selector 6
    - input `0x10`
    - no output
- 结论：
  - plain daemon runtime path
    已可更准确地写成：
    selector-3 create
    -> optional selector-4 prepare
    -> selector-6 destroy on prepare failure
  - 这说明：
    - daemon `.hwx precompiled`
      `0x170004`
    - local selector-3 `status=0`
    - local selector-4 `0x02`
    已经处在同一 lower gate family 里。
  - 因而当前不应再把 daemon plain load
    和 selector-3/4 路
    当成两套彼此分离的问题。
  - 剩余 gap 更像：
    selector-3/4 之下的
    lower accepted-state /
    request author /
    publish coherence。
- 下一步：
  - 不再重复扩充高层 load options 或把 `skipPreparePhase`
    当作 create 侧解锁点。
  - 继续主线时优先追：
    1. selector-3 / selector-4 之下，
       谁 first authors lower accepted-state coherence
    2. `resource+0x400d0`
       first author 与这条 selector family
       的接合点

- 时间：2026-06-14 05:30:00 +0800
- 目标：把 `.hwx precompiled` 的
  `Program load failure (0x170004)`
  直接解码到 daemon family code，确认它到底卡在 create 还是 prepare。
- 动作：
  - 新增 join 脚本：
    - `mps/ANE/experiments/ane_precompiled_error_family_join.py`
  - 输入：
    - `benchmark_results/private_ane/precompiled_file_route_probe_time_root_v5.json`
    - `benchmark_results/private_ane/precompiled_file_route_probe_skip_prepare_no_has_cache_1781366852.json`
  - 输出：
    - `mps/ANE/.ane_runs/csv/ane_precompiled_error_family_join.csv`
  - 新增说明文档：
    - `mps/ANE/experiments/results/precompiled_170004_family4_note.md`
- 证据：
  - 当前两条 joined row 都明确是：
    - `error_code_hex = 0x170004`
    - `status_high16_hex = 0x0017`
    - `family_low16_hex = 0x0004`
    - `family_name = family-4 create/load stage`
  - 结合上一条
    `daemon_program_lower_gate_join_note.md`
    已确认：
    - family-4 = selector-3 create stage
    - family-5 = selector-4 prepare / selector-6 destroy
- 结论：
  - 当前 `.hwx precompiled`
    `0x170004`
    不是 prepare 失败，也不是 selector-4 `0x02`
    那条 intermediate 问题。
  - 它更明确地是：
    selector-3 create-stage lower status `0x17`
  - 因而 `skipPreparePhase`
    对当前这类失败无效，
    因为 failure family 根本还没走到 selector-4。
- 下一步：
  - 不再把 `.hwx precompiled` 失败
    和 selector-4 intermediate 问题混在一起。
  - 优先继续追：
    1. daemon/plain load
       为什么在 selector-3 create-stage 会得到 lower status `0x17`
    2. local selector-3 direct create
       为什么能 `status=0`
       但仍缺 accepted writeback
    3. 两者之间缺的是
       `modelToken` / retained companion /
       create-output threading /
       还是更低 accepted-state coherence

- 时间：2026-06-14 05:50:00 +0800
- 目标：确认 local selector-3 `status=0`
  的剩余 gap 是否只是 wrapper-visible handle/queueDepth 缺失，
  还是即使补上 live 成功 handle 族字段也仍卡在更深 coherence。
- 动作：
  - 新增 join 脚本：
    - `mps/ANE/experiments/ane_selector3_livehandle_coherence_join.py`
  - 输入：
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v12_livegraph_handlepatch.json`
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v19_internal_windows_text.json`
  - 输出：
    - `mps/ANE/.ane_runs/csv/ane_selector3_livehandle_coherence_join.csv`
  - 新增说明文档：
    - `mps/ANE/experiments/results/selector3_livehandle_coherence_note.md`
- 证据：
  - 所有 local cases 都是：
    - `selector3_status = 0x00000000`
    - `prepare1_status = 0x00000014`
    - `owner0_ready1_status = 0x00000002`
    - `handlepatch_status = 0x00000002`
  - base local wrapper 统一仍是：
    - `wrapper+0x70 = 0`
    - `payload+0xda8 = 0`
    - `wrapper+0xa8 = 0x0000000100000000`
    - `payload_u8_0xde0 = 4`
  - 同一 joined row 还带出 live 成功 program：
    - v12 `programHandle = 0x979a1ac48c3`
    - v19 `programHandle = 0x0a6f0222ded0`
    - 两者 `queueDepth = 127`
  - 把这些 live 成功
    `programHandle + queueDepth`
    直接补进 local wrapper/payload 后：
    - `wrapper+0x70 / payload+0xda8`
      都已对齐 live handle
    - `wrapper+0xa8`
      变成 `0x000000010000007f`
    - 但 selector-4 结果仍是 `0x02`
    - patched before/after wrapper
      也没有进一步 promote
- 结论：
  - 当前不能再把 local selector-3 的 blocker
    建模成：
    “只差 wrapper-visible handle/queueDepth 字段”
  - 更准确的是：
    local selector-3 已经构造出 partial internal shell，
    但缺的仍是更深的
    accepted-state / request-author / publish coherence
- 下一步：
  - 不再优先做 wrapper-visible handle/queueDepth patch 类实验。
  - 继续主线时优先追：
    1. daemon `0x17/family-4`
       与 local `status=0 but no accepted writeback`
       之间的更深 request/coherence 差异
    2. `modelToken` / retained companion /
       create-output threading
       哪个最像这条差异的入口

- 时间：2026-06-14 06:15:00 +0800
- 目标：验证 local selector-3 partial shell
  是否主要只是 `.hwx/data` payload 形态导致，
  还是即使换成真实 working `model.mil`
  也仍然卡在同一 create/prepare 中间态。
- 动作：
  - 修改：
    - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
  - 新增两个 case：
    - `live_mil_nonprecompiled_path_mil`
    - `live_mil_nonprecompiled_path_mil_daemon_layout`
  - 它们都复用：
    - 同一 `live_tiny_mil_controller_device`
    - 同一 `live_artifact`
      （已成功通过 private API load 的 tiny MIL root）
    - 真实 `live_artifact/model.mil`
      作为 selector-3 payload
  - 重新编译：
    - `clang -fobjc-arc -framework Foundation -o /tmp/ane_services_program_create_runtime_probe mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
  - 生成新结果：
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v21_live_mil_case.json`
  - 新增说明文档：
    - `mps/ANE/experiments/results/selector3_live_mil_negative_note.md`
- 证据：
  - `device_source = live_tiny_mil_controller_device`
  - 新 case
    `live_mil_nonprecompiled_path_mil`
    返回：
    - `status_hex = 0x00000000`
    - `prepare1_status_hex = 0x00000014`
    - `prepare1_owner0_ready1_status_hex = 0x00000002`
    - `prepare1_owner0_ready1_handlepatch_status_hex = 0x00000002`
    - `destroy_status_hex = 0x00000014`
  - base wrapper 仍然：
    - `wrapper+0x70 = 0`
    - `payload+0xda8 = 0`
    - `payload_u8_0xde0 = 4`
  - 同一 case 的 raw 路也仍然显示：
    - `raw_create_status_hex = 0x00000000`
    - `raw_create_output_change.diff_count = 0`
    - raw output 仍是 sentinel `0xa5...`
    - `raw_prepare_status_hex = 0xe00002c1`
    - `raw_prepare_owner0_ready1_status_hex = 0xe00002c2`
  - 也就是说，在同一 live 成功 device 上：
    - `hwx/data` cases -> `0 / 0x14 / 0x02`
    - `real working model.mil` case -> `0 / 0x14 / 0x02`
  - 后续又把
    `modelPath/modelIdentity`
    对齐到 live 成功
    `_ANEInMemoryModel`
    的真实
    `modelURL/model.mil`
    （结果：
    `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v22_live_modelurl_case.json`）
    后，
    新 case
    `live_mil_nonprecompiled_path_live_modelurl_mil`
    仍然是：
    - `status = 0`
    - `prepare1 = 0x14`
    - `owner0_ready1 = 0x02`
    - `handlepatch = 0x02`
    - `raw_create_output_change.diff_count = 0`
- 结论：
  - 当前 local selector-3 partial shell
    不只是 `.hwx` / `data` payload 形态导致，
    也不只是 visible `modelPath/modelIdentity`
    这层差异导致。
  - 即使换成真实 working `model.mil`
    并进一步对齐到 live 成功的
    `modelURL/model.mil`，
    direct selector-3
    也仍然停在同一 partial create/prepare family。
  - 因而下一步不应再主要做
    `hwx/data/model.mil`
    这一层的 payload format sweep。
  - 更像缺的仍是：
    - outer request threading
    - retained companion / modelToken-side context
    - 或更低 accepted-state / publish coherence
- 下一步：
  - 不再优先做 top-level payload 形态 sweep。
  - 也不再优先做 visible path/identity sweep。
  - 继续主线时优先追：
    1. daemon `0x17/family-4`
       与 local `status=0 but no accepted writeback`
       之间真正的 outer context / coherence 差异
    2. `modelToken` / retained companion /
       create-output threading
       哪个最像这条差异的入口

- 时间：2026-06-14 07:00:00 +0800
- 目标：确认 local selector-3 partial shell
  是否主要只是因为还没复现 `_ANEDeviceController start`
  那条真实的 ANEServices userland-open 形态。
- 动作：
  - 继续修改：
    - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
  - 新增一条更接近 `_ANEDeviceController start` 的 open 路：
    - `CodexProgramHandleOpenConfig`
      - `mode = 1`
      - `programHandle = live programHandle`
      - `timeout0 = 0x2710`
      - `timeout1 = 0x2710`
    - `ANEServicesDeviceOpen(&device, &cfg, controller_arg, NULL)`
  - 记录两条 attempt：
    - `live_controller_arg`
    - `fresh_controller_arg`
  - 若 open 成功，则在这些新 device 上再跑：
    - `programhandleopen_*_live_mil_nonprecompiled_path_live_modelurl_mil`
  - 重新编译并生成：
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v24_programhandle_open_case.json`
  - 新增说明文档：
    - `mps/ANE/experiments/results/selector3_programhandle_open_device_note.md`
- 证据：
  - 这次 `ANEServicesDeviceOpen(programHandle-open, controller-arg)`
    已真实成功两次：
    - `live_controller_arg`
      -> `status=0`, `device != nil`
    - `fresh_controller_arg`
      -> `status=0`, `device != nil`
  - 但在这两个真正 userland-open device 上，
    `programhandleopen_*_live_mil_nonprecompiled_path_live_modelurl_mil`
    仍然全部是：
    - `status = 0`
    - `prepare1 = 0x14`
    - `owner0_ready1 = 0x02`
    - `handlepatch = 0x02`
    - `raw_create_output_change.diff_count = 0`
    - base wrapper 无 runtime handle publish
- 结论：
  - 当前 partial shell
    不是因为“还没复现正确的 visible ANEServices open path”。
  - 到这里为止，
    已经连续排掉：
    - top-level payload 形态
    - visible `modelPath/modelIdentity`
    - wrapper-visible handle/queueDepth
    - live/fresh device instance
    - real ANEServices programHandle-open shape
  - 剩余 gap 更集中在：
    - hidden outer request context
    - retained companion / modelToken-side state
    - create-output threading
    - deeper accepted-state / publish coherence
- 下一步：
  - 不再优先做 visible payload/path/device/open 形态实验。
  - 继续主线时优先追：
    1. daemon `0x17/family-4`
       与 local `status=0`
       之间到底差哪层 hidden outer context
    2. 这层 hidden context
       更像 `modelToken`、retained companion，
       还是 create-output threading / accepted coherence

- 时间：2026-06-14 06:40:00 +0800
- 目标：确认 local selector-3 partial shell
  是否主要只是因为用了 “错误的 live device/control-state 实例”，
  还是换成 fresh controller-backed device 也仍然不变。
- 动作：
  - 继续修改：
    - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
  - 新增 fresh controller 路：
    - `_ANEDeviceController controllerWithProgramHandle:`
    - `start`
    - `device`
  - 在这个 fresh controller-backed device 上，
    新增 case：
    - `fresh_controller_live_mil_nonprecompiled_path_live_modelurl_mil`
  - 重新编译并生成：
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v23_fresh_controller_case.json`
  - 新增说明文档：
    - `mps/ANE/experiments/results/selector3_fresh_controller_device_note.md`
- 证据：
  - 当前 fresh controller 已真实构造成功：
    - `fresh_controller_summary = <_ANEDeviceController: ...>`
    - `fresh_controller_device != nil`
    - `fresh_controller_device_layout`
      里有独立 `owner/service/connect`
  - 但在这个 fresh device 上，
    `fresh_controller_live_mil_nonprecompiled_path_live_modelurl_mil`
    仍然返回：
    - `status = 0`
    - `prepare1 = 0x14`
    - `owner0_ready1 = 0x02`
    - `destroy = 0x14`
    - `raw_create_status = 0`
    - `raw_create_output_change.diff_count = 0`
    - `raw_prepare = 0xe00002c1 / 0xe00002c2`
    - base wrapper 仍无 runtime handle publish
- 结论：
  - 当前 partial shell
    不是因为“用了错误的 live device 实例”。
  - 即使换成由成功 `programHandle`
    衍生出来的 fresh controller-backed device，
    local direct selector-3
    也仍然停在同一 partial family。
  - 到这里为止，
    已经连续排掉了：
    - top-level payload 形态
    - visible `modelPath/modelIdentity`
    - wrapper-visible handle/queueDepth
    - visible live device/control-state 实例
  - 剩余 gap 更集中在：
    - outer request threading
    - retained companion / modelToken-side context
    - create-output threading
    - 更低 accepted-state / publish coherence
- 下一步：
  - 不再优先做 visible payload/path/device/handle patch 类实验。
  - 继续主线时优先追：
    1. daemon `0x17/family-4`
       与 local `status=0`
       之间到底差哪层 hidden context
    2. 这层 hidden context
       更像 `modelToken`、retained companion，
       还是 create-output threading / accepted coherence

- 时间：2026-06-14 11:32:30 +0800
- 目标：确认 daemon/plain `loadModel...` 是否还把 hidden `_ANEModel` 状态
  （`UUID / string_id / identifierSource / sourceURL-side identity`）
  注入到 lower create-program authoring。
- 动作：
  - 重新打开 `aned_bin.i64` worker；
  - 用 IDA 直接读取：
    - `-[_ANEServer loadModel:sandboxExtension:options:qos:withReply:]`
    - `-[_ANEProgramForLoad createProgramInstanceForModel:...error:]`
    - `sub_10000307F`
  - 重点看：
    - `0x10001c76b..0x10001c883`
      的 `createProgramInstance...` 调用点参数打包
    - `sub_10000307F`
      里 lower request 的真实 author 字段
    - `string_id / UUID / identifierSource / sourceURL`
      在 `loadModel...` 里的可见用途
  - 新增说明文档：
    - `mps/ANE/experiments/results/loadmodel_hidden_model_state_boundary_note.md`
- 证据：
  - `mps/ANE/experiments/results/loadmodel_hidden_model_state_boundary_note.md`
  - `aned_bin.i64`
    - `0x10001a8b4`
    - `0x100002775`
    - `0x10000307f`
- 结论：
  - 当前 `loadModel... -> createProgramInstance...` handoff
    已经被压成具体参数表，而不是“把整个 hidden `_ANEModel` 扔给下层”。
  - `sub_10000307F` 当前可见真正 author 的仍是：
    - cached model bytes/len
    - `modelToken` 的 team/cs identity SHA
    - `modelFilePath`
    - `modelIdentityStr`
    - `cacheUrlIdentifier`
    - `aotCacheUrlIdentifier`
    - qos / skipPrepare / powerSaving / lateLatch / keepWired /
      memoryPoolID / statsMask
  - `string_id` 在 `loadModel...` 里只命中 log/signpost 面；
    `UUID` / `identifierSource` 在该函数体内没有 lower create-side 命中；
    `sourceURL` 只是在 `modelURL == nil` 时回退出 path surface。
  - 因而当前不能再把 selector-3 / family-4 的主 blocker
    建模成 generic hidden `_ANEModel` ivar。
- 下一步：
  - 不再回头扫 `UUID / string_id / identifierSource`。
  - 继续主线时优先追：
    1. daemon/plain 与 local direct create 之间，
       `modelToken` team/cs provenance
       是否还差 lower author / accepted-state glue
    2. retained companion / ProgramDefinition state
       是否才是 selector-3 create-stage 的真正 sidecar
    3. raw create output untouched
       与 later publish / accepted-state coherence
       谁才是更早缺失层

- 时间：2026-06-14 14:39:00 +0800
- 目标：验证当前 selector-3 trace gap 是否只是 interposer 覆盖面不够，
  并把 runtime probe 缩到单 case 便于复检。
- 动作：
  - 修改：
    - `mps/ANE/experiments/ane_ioconnect_trace_interpose.c`
      - 新增 hook:
        - `IOConnectCallScalarMethod`
        - `IOConnectTrap6`
    - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
      - 新增 `--only-case SUBSTR`
  - 重新编译：
    - `make -C mps/ANE/experiments ane_ioconnect_trace_interpose.dylib ane_services_program_create_runtime_probe`
  - 单 case 复跑：
    - `--only-case live_mil_nonprecompiled_path_live_modelurl_mil`
    - trace 输出：
      `mps/ANE/.ane_runs/csv/trace_selector3_recheck_v3.csv`
- 证据：
  - `mps/ANE/.ane_runs/csv/trace_selector3_recheck_v3.csv`
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_recheck_v3.json`
  - `mps/ANE/experiments/results/selector3_extended_iokit_trace_negative_note.md`
- 结论：
  - 单 case 复跑里，trace CSV 仍只有表头，没有任何
    `struct/method/scalar/trap6` 命中。
  - 同时单 case probe 仍会 CPU-bound 卡住，JSON 输出保持 `0B`，
    需要人工 kill。
  - 因而当前不能再把下一步主要建模成：
    “再补一个 public `IOConnect*` 入口就能抓到 selector-3”。
- 下一步：
  - 把观察点移近：
    - `_ANEServicesProgramCreate`
    - `ANE::ANEServicesDevice::ANE_ProgramCreate`
  - 或直接判断当前单 case probe
    是卡在 send 前还是 send 后。
  - 如果还要追 transport，
    直接下沉到 mach-message / XPC / private wrapper 层。

- 时间：2026-06-14 15:16:00 +0800
- 目标：把 selector-3 trace gap 从“startup-time interposer 会卡住”
  收缩成“post-acquisition runtime interpose 仍然 zero-hit”的明确证据。
- 动作：
  - 修改：
    - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
      - 新增 `--fast-trace`
      - 新增进程内 runtime interpose：
        - `CODEX_RUNTIME_IOCONNECT_TRACE_CSV`
        - `CODEX_RUNTIME_IOCONNECT_TRACE_ALL`
    - `mps/ANE/experiments/Makefile`
      - probe 链接 `IOKit`
  - 采样：
    - startup-time interposer 挂住时：
      `mps/ANE/.ane_runs/selector3_recheck_v5.sample.txt`
  - 运行后 post-acquisition runtime interpose：
    - selector3-only:
      `trace_selector3_runtime_v1.csv`
    - trace-all:
      `trace_selector3_runtime_all_v1.csv`
  - 结果 JSON：
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_v1.json`
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_all_v1.json`
  - 新增说明文档：
    - `mps/ANE/experiments/results/selector3_postacquire_runtime_interpose_note.md`
- 证据：
  - `mps/ANE/.ane_runs/selector3_recheck_v5.sample.txt`
  - `mps/ANE/.ane_runs/csv/trace_selector3_runtime_v1.csv`
  - `mps/ANE/.ane_runs/csv/trace_selector3_runtime_all_v1.csv`
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_all_v1.json`
- 结论：
  - startup-time `DYLD_INSERT_LIBRARIES`
    的 zero-hit 不能直接解释成 selector-3 没走 public IOKit；
    它先被 device-open 路卡住了。
  - 但把 trace 改成 post-acquisition runtime interpose 之后，
    单 case 已经能跑完，
    `status=0 / prepare1=0x14 / raw_create_status=0` 这些老现象保持不变。
  - 同时即便开启 `TRACE_ALL`，
    runtime trace CSV 仍然只有表头，没有任何 captured call。
  - 因而当前更强的结论是：
    这条 host 上真正相关的 selector-3 transport，
    不是现有 dyld runtime interpose 能直接抓到的 public `IOConnect*` 面。
- 下一步：
  - 不再继续堆 public `IOConnect*` interpose。
  - 直接往：
    1. `_ANEServicesProgramCreate`
    2. `ANE::ANEServicesDevice::ANE_ProgramCreate`
    3. stub / import slot / debugger-side runtime callsite
    这三条走。

- 时间：2026-06-14 16:30:20 +0800
- 目标：确认 `rawCreateFn+0x108` 的 stub 实际是不是 public `IOConnectCallStructMethod`，以及为什么 runtime interpose 仍然零命中。
- 动作：
  - 修改：
    - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
      - `decode_import_stub(...)` 现在可识别 arm64e
        `braa x16, x17`
      - 新增 `runtime_trace_interpose_before/after`
        snapshot，直接记录
        `rawCreateFn` stub auth slot 在
        `dyld_dynamic_interpose` 前后的值
  - 重新编译：
    - `make -C mps/ANE/experiments ane_services_program_create_runtime_probe`
  - 复跑：
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_manual_v7.json`
    - `mps/ANE/.ane_runs/csv/trace_selector3_runtime_manual_v7.csv`
  - 新增说明文档：
    - `mps/ANE/experiments/results/selector3_import_stub_public_iokit_noop_interpose_note.md`
- 证据：
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_manual_v7.json`
  - `mps/ANE/.ane_runs/csv/trace_selector3_runtime_manual_v7.csv`
  - `dyld_info -exports /System/Library/Frameworks/IOKit.framework/Versions/A/IOKit`
  - `dyld_info -disassemble /System/Library/PrivateFrameworks/ANEServices.framework/ANEServices`
- 结论：
  - `rawCreateFn+0x108`
    的 runtime stub 已确认是 arm64e PAC 形式的
    public `IOConnectCallStructMethod` import stub：
    - `slot_addr = 0x1f43cbdd0`
    - `slot_value = 0x18b001d18`
    - `branch = braa x16, x17`
  - `0x18b001d18`
    已被 machine-local 证据对齐成真实
    `IOConnectCallStructMethod` 导出地址，
    不是某个“看起来像 public symbol”的假目标。
  - 但 `dyld_dynamic_interpose` 前后，
    该 auth slot 的值完全没变：
    - before = `0x18b001d18`
    - after  = `0x18b001d18`
    - hook   = `0x1002223d0`
  - 同时 trace CSV 仍只有表头。
  - 因而当前更强的结论是：
    `rawCreateFn` 的 selector-3 确实经由 public
    `IOConnectCallStructMethod` import stub，
    但当前 `dyld_dynamic_interpose`
    对这条 arm64e auth slot 没生效。
- 下一步：
  - 不再继续堆 public `IOConnect*` hook 变体。
  - 直接尝试：
    1. patch / observe `0x1f43cbdd0`
       这条 auth slot（带正确 PAC 处理）
    2. 或在
       `rawCreateFn+0x108` /
       `IOConnectCallStructMethod`
       export entry 下断点看 live args
    3. 再对照 raw create 与 manual public
       selector-3 `0xe00002c2`
       的参数差异

- 时间：2026-06-14 17:27:20 +0800
- 目标：把 selector-3 主线从“auth slot 可控”继续推进到“rawCreate 为什么默认不发 selector-3，以及强制 ready 后会发生什么”。
- 动作：
  - 修改：
    - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
      - 新增 arm64e `ptrauth` 支持：
        - function pointer strip / resign
        - slot signature candidate snapshot
        - auth slot direct patch
      - 修正 arm64e 下：
        - 对 signed function pointer 做反汇编前先 strip
        - `rawPrepareFn = imageBase + 0x124d0`
          后先按 function-pointer 规则重签
      - 新增 CLI：
        - `--slot-patch-structmethod`
        - `--rawcreate-force-ready1`
  - 运行：
    1. arm64e no-patch:
       `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_manual_v8_arm64e.json`
    2. arm64e slot-patch:
       `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_manual_v9_arm64e_patch.json`
       `mps/ANE/.ane_runs/csv/trace_selector3_runtime_manual_v9_arm64e_patch.csv`
    3. arm64e slot-patch + force-ready1:
       `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_manual_v10_arm64e_patch_ready1.json`
       `mps/ANE/.ane_runs/csv/trace_selector3_runtime_manual_v10_arm64e_patch_ready1.csv`
  - 静态/动态联合：
    - 提取文件：
      `/Volumes/2T/dsc_arm64e_extract/System/Library/PrivateFrameworks/ANEServices.framework/Versions/A/ANEServices`
    - 反汇编确认：
      `__ZN3ANE17ANEServicesDevice17ANE_ProgramCreate...`
      在 `0x19e69d160` 先检查 `[service + 0x18] == 1`
      才会走 `0x19e69d184 -> _IOConnectCallStructMethod(selector=3)`
- 证据：
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_manual_v8_arm64e.json`
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_manual_v9_arm64e_patch.json`
  - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_manual_v10_arm64e_patch_ready1.json`
  - `mps/ANE/.ane_runs/csv/trace_selector3_runtime_manual_v9_arm64e_patch.csv`
  - `mps/ANE/.ane_runs/csv/trace_selector3_runtime_manual_v10_arm64e_patch_ready1.csv`
  - `mps/ANE/experiments/results/selector3_ready_gate_transport_match_note.md`
- 结论：
  - arm64e 下 auth slot 签名规则已 machine-locally 确认：
    - `slot_value_raw == sign_export_slot`
    - 也就是：
      `ptrauth_key_function_pointer + slotAddr discriminator`
  - auth slot patch 已经成功：
    - `vm_protect_rw_copy_status = 0`
    - `write_match = 1`
  - patch 后 selector-4 trace 已经能稳定抓到，
    说明 hook/patch 路可用。
  - 但默认 rawCreate case 没有 selector-3，
    不是 hook 问题，而是：
    `ANE_ProgramCreate`
    在发 selector-3 前先检查
    `[service + 0x18] == 1`；
    当前默认 case 这里是 `0`，
    所以直接 early return `status = 0`。
  - 强制把 `service_ready_u8_0x18` 改成 `1` 之后：
    - `raw_create_status_hex = 0xe00002c2`
    - `manual_selector3_transport = 0xe00002c2`
    - trace CSV 首次抓到真实
      `selector = 3`
  - 同时已静态确认：
    - `ANE::ANEServicesDevice::ANEDeviceOpen`
      会把 selector-0 open reply 的
      `ANEDeviceInfo+0x1c`
      写到 `service+0x18`
    - `ANE::ANEHWDevice::ANEHWDeviceOpen`
      也有同形态写入
  - 因而当前更强的结论是：
    默认 rawCreate 的 `status=0`
    本质上是一个 ready-gate 未开的 early-success shell；
    真正的 public selector-3 transport
    只有在 ready-gate 打开后才会发生，
    且它当前返回的就是 `0xe00002c2`。
- 下一步：
  - 不再继续问：
    “rawCreate 到底有没有真正发 selector-3”
  - 这个问题已经回答。
  - 直接追：
    1. 为什么当前 live/local path 的
       selector-0 open reply
       会把 `ANEDeviceInfo+0x1c`
       产成 `0`
    2. 这一步对应哪条 accepted-state /
       attach / ready transition
    3. 为什么 local create case
       会先暴露一个 `status=0` early shell

- 时间：2026-06-14 18:37:15 +0800
- 目标：验证 `service+0x18 = 0` 是否只是因为我们之前 direct open 没按 live path 的真实参数形态去调。
- 动作：
  - 修改：
    - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
      - 新增 `loaded_image_base_matching(...)`
      - 修正 `fDeviceCallback` 取址：从已加载
        `AppleNeuralEngine` 镜像 base + offset
        `0x36de4`
      - 新增 `controller_style_open_attempts`
        复现 `_ANEDeviceController start`
        的真实 open 形态：
        - `ANEServicesDeviceOpen(&outDevice, buf, self, fDeviceCallback)`
        - 并比较
          `usageType=1/2`
          `programHandle=0/liveHandle`
  - 运行：
    - `benchmark_results/private_ane/ane_services_program_create_open_sweep_v3_controller_style.json`
  - 静态补证：
    - `ANEServicesDeviceOpen` /
      `ANEHWDeviceOpen`：
      `service+0x18 <- openReply+0x1c`
    - `AppleNeuralEngine`
      `___29-[_ANEDeviceController start]_block_invoke`
      确认真实 open 参数：
      - 非 privileged：
        `usageType=1`
        `programHandle=self.programHandle`
      - 调用形态：
        `ANEServicesDeviceOpen(&outDevice, buf, self, fDeviceCallback)`
  - 新增说明文档：
    - `mps/ANE/experiments/results/open_reply_ready_byte_alignment_note.md`
- 证据：
  - `benchmark_results/private_ane/ane_services_program_create_open_sweep_v3_controller_style.json`
  - `mps/ANE/experiments/results/open_reply_ready_byte_alignment_note.md`
  - `ANEServicesDeviceOpen` / `ANEHWDeviceOpen` / `_ANEDeviceController start`
    的本地反编译结果
- 结论：
  - 当前唯一成功的 local open 形态已经 machine-locally 确认：
    - `usageType = 1`
    - `programHandle = live handle`
  - 这与 live non-privileged path 本身一致。
  - 但即使在这条“controller/callback/usage/handle 都已对齐”的
    成功 open 路径上，
    新 device 的
    `service_ready_u8_0x18`
    仍然稳定是 `0`。
  - 因而当前可以排除：
    `ready=0`
    只是因为
    - controller arg 传错
    - callback 传错
    - usage/handle 组合走偏
  - 更像是：
    selector-0 open reply
    自身在这条成功 local path 上
    就把 `ANEDeviceInfo+0x1c`
    产成了 `0`。
- 继续补证：
  - controller-style 成功 open 的
    immediate / +10ms / +100ms
    三次快照里，
    `service_ready_u8_0x18`
    都保持 `0`
  - 打开 selector-0 trace 后，
    成功 open 的 `0x68` reply buffer
    头 32 字节也直接显示：
    - `0x18..0x1b = 0x2710`
    - `0x1c..0x1f = 0x00000000`
  - 这与
    `ANEDeviceInfo+0x1c -> service+0x18`
    的静态 copy 完全对齐
- 下一步：
  - 不再继续主要围绕 open 参数组合穷举。
  - 直接追：
    1. selector-0 open reply / lower open state
       为什么会给 `+0x1c = 0`
    2. 这是否对应：
       - lower attach 未完成
       - callback / receiver start 之前过早观测
       - ANEServices vs HWDevice path 的 state split
       - 或更低层 accepted-state / demotion

## 2026-06-14 22:28:00 +0800

- 目标：
  - 把 selector-0 open reply 从 `head32` 级别提升到完整 0x68 结构化 decode，
    同时保留调用前 input，避免 in-place buffer 误导。
- 动作：
  - 修改：
    - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
      - 新增 `snapshot_selector0_open_buffer(...)`
      - selector-0 trace 现在输出：
        - `qword_0x00/0x08/0x10/0x18`
        - `qword_0x48/0x50/0x58/0x60`
        - `u32_0x1c/0x4c/0x50`
        - `full_hex`
      - `IOConnectCallStructMethod/Method` trace
        改为先抓调用前 input summary，再抓调用后 output summary
      - `snapshot_device_layout_from_pointer(...)`
        新增：
        - `service_u32_0x1c`
        - `service_u32_0x20`
  - 构建：
    - `make -C mps/ANE/experiments ane_services_program_create_runtime_probe`
  - 运行：
    - `CODEX_RUNTIME_IOCONNECT_TRACE_ALL=1`
    - `CODEX_RUNTIME_IOCONNECT_TRACE_CSV=/Volumes/2T/pymss/mps/ANE/.ane_runs/csv/trace_open_selector0_v3_decode.csv`
    - `./mps/ANE/experiments/ane_services_program_create_runtime_probe --slot-patch-structmethod --only-case __skip_all_cases__ --live-artifact /Volumes/2T/pymss/mps/ANE/.ane_runs/runtime_wrapper_aug_weighted_ffn/add_all_fresh_rebuilt_VHE1I1 /Volumes/2T/pymss/mps/ANE/.ane_runs/runtime_wrapper_aug_weighted_ffn/add_all_fresh_rebuilt_VHE1I1`
    - 输出：
      - `benchmark_results/private_ane/ane_services_program_create_open_sweep_v7_selector0_decode.json`
      - `mps/ANE/.ane_runs/csv/trace_open_selector0_v3_decode.csv`
- 证据：
  - `benchmark_results/private_ane/ane_services_program_create_open_sweep_v7_selector0_decode.json`
  - `mps/ANE/.ane_runs/csv/trace_open_selector0_v3_decode.csv`
  - `mps/ANE/experiments/results/open_reply_ready_byte_alignment_note.md`
  - IDA:
    - `ANEServicesHandleDeviceOpen`
    - `ANE::ANEServicesDevice::ANEDeviceOpen`
- 结论：
  - selector-0 input 不是顶层 cfg，而是
    `ANEServicesHandleDeviceOpen`
    synth 出来的 `ANEDeviceInfo` request：
    - `qword_0x00 = programHandle`
    - `qword_0x08 = ANE::ANERequestReceiver::FrameDone`
    - `qword_0x10 = controller/context`
    - `qword_0x18 = timeout`
  - failed selector-0 (`ret = 0xe00002f0`) 时，
    整块 0x68 buffer 保持不变。
  - successful selector-0 reply 会稳定填：
    - `qword_0x48 = 0x000000c000000020`
    - `qword_0x50 = 0x0000000100000000`
    - `qword_0x58 = 0x7`
    - `qword_0x60 = 0x0000000280000000`
    - `u32_0x4c = 192`
    - `u32_0x50 = 0`
    同时 `u32_0x1c` 仍为 `0`
  - 新出现的不一致：
    - 静态 `ANE::ANEServicesDevice::ANEDeviceOpen`
      表示在 ready=0 分支会把
      `reply[0x4c]/reply[0x50]`
      拷到 `service+0x1c/+0x20`
    - 但当前 immediate device snapshot
      仍显示：
      - `service_ready_u8_0x18 = 0`
      - `service_u32_0x1c = 0`
      - `service_u32_0x20 = 0`
  - 所以 selector-0 这条线的下一问已经收紧成：
    1. tail 字段是否落在不同 object layer
    2. 或 `_ANEServicesDeviceOpen` 返回后
       有后续 stage 把这两个缓存字段规范化 / 清零
- 下一步：
  - 先静态追 `_ANEServicesDeviceOpen`
    在 lower open 成功返回之后，
    是否还会重写 `service+0x1c/+0x20`
  - 若静态不足，再给 controller-style open
    增加 service memory window，
    直接抓 open-return 前后该区域字节。

## 2026-06-14 22:38:00 +0800

- 目标：
  - 判断 `reply[0x4c]/reply[0x50]` 没落到 `service+0x1c/+0x20`
    到底是读错 object layer，还是静态分支本来就不走。
- 动作：
  - 修改：
    - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
      - 在 `snapshot_device_layout_from_pointer(...)`
        增加 public wrapper / underlying service decode：
        - `public_wrapper_base`
        - `public_controller_arg`
        - `public_callback_fn`
        - `public_cfg_head32`
        - `public_wrapper_u8_0x58`
        - `public_wrapper_u32_0x5c`
        - `public_wrapper_qword_0x60`
        - `underlying_service_device`
        - `service_u32_0x88`
  - 构建：
    - `make -C mps/ANE/experiments ane_services_program_create_runtime_probe`
  - 运行：
    - `CODEX_RUNTIME_IOCONNECT_TRACE_ALL=1`
    - `CODEX_RUNTIME_IOCONNECT_TRACE_CSV=/Volumes/2T/pymss/mps/ANE/.ane_runs/csv/trace_open_selector0_v4_wrapper_service_decode.csv`
    - `./mps/ANE/experiments/ane_services_program_create_runtime_probe --slot-patch-structmethod --only-case __skip_all_cases__ --live-artifact /Volumes/2T/pymss/mps/ANE/.ane_runs/runtime_wrapper_aug_weighted_ffn/add_all_fresh_rebuilt_VHE1I1 /Volumes/2T/pymss/mps/ANE/.ane_runs/runtime_wrapper_aug_weighted_ffn/add_all_fresh_rebuilt_VHE1I1`
    - 输出：
      - `benchmark_results/private_ane/ane_services_program_create_open_sweep_v8_wrapper_service_decode.json`
      - `mps/ANE/.ane_runs/csv/trace_open_selector0_v4_wrapper_service_decode.csv`
- 证据：
  - `benchmark_results/private_ane/ane_services_program_create_open_sweep_v8_wrapper_service_decode.json`
  - `mps/ANE/.ane_runs/csv/trace_open_selector0_v4_wrapper_service_decode.csv`
  - `ANE::ANEServicesDevice::ANEDeviceOpen`
    的静态分支：
    `if (*(a1 + 0x88) != 1) { copy reply[0x4c]/[0x50]; }`
- 结论：
  - public `ANEServicesDeviceOpen` 返回的 `device`
    已确认不是底层 `ANE::ANEServicesDevice *`，
    而是：
    - `wrapper_base + 0x40`
  - 成功 local open 的当前 object 关系已对齐为：
    - `public_wrapper_base = *(device + 0x10)`
    - `underlying_service_device = *(wrapper_base + 0x8)`
    - `public_controller_arg = *(wrapper_base + 0x10)`
    - `public_callback_fn = *(wrapper_base + 0x18)`
  - 成功 local path 上：
    - `underlying_service_device_u32_0x88 = 1`
  - 这直接解释了上一轮的“不一致”：
    - `reply[0x4c]/reply[0x50]`
      没有进
      `service+0x1c/+0x20`
      不是因为写丢了
    - 而是因为当前成功 open 走的是
      `service+0x88 == 1`
      的 ANEDriver-style path，
      static copy branch 本来就不会走
  - 同时 wrapper 侧也对齐了 reply tail：
    - `public_wrapper_u8_0x58 = 1`
    - `public_wrapper_u32_0x5c = 7`
    - `public_wrapper_qword_0x60 = 0x0000000280000000`
  - 因而当前剩下的核心问题重新收敛为：
    - successful local selector-0 reply
      为什么仍然 author
      `u32_0x1c = 0`
- 下一步：
  - 不再继续围绕 `0x4c/0x50 -> service+0x1c/+0x20`
    打转。
  - 直接回到：
    - `reply+0x1c`
      的 lower author 语义 / state 来源。

## 2026-06-14 23:20:30 +0800

- 目标：
  - 确认 public open return 之后，
    `register/startReceive/callback`
    这条 user-space 路是否会把
    `underlying_service_device + 0x18`
    再补成 1。
- 动作：
  - 读取 ANEServices 静态函数：
    - `__ZL38MyANEServicesDeviceMessageNotificationPN3ANE17ANEServicesDeviceEjPvS2_`
    - `__ZN3ANE18ANERequestReceiver12startReceiveEv`
    - `__ZN3ANE18ANERequestReceiver25registerANEServicesDeviceEPNS_17ANEServicesDeviceE`
- 证据：
  - `MyANEServicesDeviceMessageNotification`
    只把 message/status
    转发给 callback hook
  - `ANE::ANERequestReceiver::startReceive`
    只改 receiver-local running state
  - `ANE::ANERequestReceiver::registerANEServicesDevice`
    只把 service device 指针存进 receiver
- 结论：
  - 当前没看到这条 user-space 路
    会在 public open return 后
    再去 author
    `underlying_service_device + 0x18`
  - 因而可以进一步排除：
    - “ready 只是稍后由 startReceive / callback 补写”
- 下一步：
  - 继续下沉 selector-0 lower reply author 本身，
    不再把主要精力放在 public open return 后的 user-space 辅助路径。

## 2026-06-14 23:33:00 +0800

- 目标：
  - 确认 `reply+0x1c` 到底是谁 author，
    以及为什么当前 successful local open
    必然得到 `0`。
- 动作：
  - 用 bootkc + 临时 venv `capstone`
    反汇：
    - `ANE_DeviceOpen`
    - `ANEClientDevice::open`
    - `ANEClientDevice::init`
    - `ANEClientInfo::create`
    - `ANEDriver::newUserClient`
    - `ANEHWDevice::newUserClient`
    - `H11ANEInUserClient::init`
    - `H11ANEInDirectPathClient::init`
  - 修改：
    - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
      - 新增 controller-style `usageType=3` case
      - 新增 outer `mode=3` open attempts
  - 构建并运行：
    - `benchmark_results/private_ane/ane_services_program_create_open_sweep_v9_usage3.json`
    - `benchmark_results/private_ane/ane_services_program_create_open_sweep_v10_outermode3.json`
- 证据：
  - `ANEClientDevice::open` 当前机器明确有：
    - `reply+0x1c <- (device+0x28 & 1)`
    - `reply+0x5d <- (device+0x29 & 1)`
  - `ANEClientDevice::init(ANEClientInfo)`
    把 `ANEClientInfo+0x10/+0x11`
    复制进 `device+0x28/+0x29`
  - `ANEClientInfo::create(task, j, b1, b2)` 当前明确是：
    - `+0x10 <- hasTaskEntitlement(task, "com.apple.ane.iokit-user-access")`
      when `b1=1`, else `0`
    - `+0x11 <- hasTaskEntitlement(task, "com.apple.ane.allow-dataChaining-access")`
      when `b2=1`, else `0`
  - `H11ANEInDirectPathClient::init`
    调：
    - `ANEClientInfo::create(task, 1, 0, 1)`
  - `H11ANEInUserClient::init`
    调：
    - `ANEClientInfo::create(task, 2, 1, 1)`
  - `ANEHWDevice::newUserClient`
    当前 split：
    - type `1/4/5` -> direct path
    - other types -> regular user path
  - 当前 dynamic：
    - successful controller-style open 使用 `usageType=1`
    - controller-style `usageType=3` 全部 `0x18`
    - outer `mode=3` 也全部 `0x18`
  - 当前 probe binary:
    - `codesign -d --entitlements :-`
      看不到 embedded entitlements
- 结论：
  - `reply+0x1c`
    不是后续 lower async / callback 再补写，
    也不是 provider 直接 first-author 的神秘位。
  - 它当前是：
    - `ANEClientInfo+0x10`
      -> `ANEClientDevice+0x28`
      -> selector-0 `reply+0x1c`
  - 当前唯一成功的 local open family
    是 direct-path：
    - `usageType=1`
      -> `H11ANEInDirectPathClient::init`
      -> `ANEClientInfo::create(task, 1, 0, 1)`
    - 因为 `b1=0`，
      所以 `ANEClientInfo+0x10`
      被设计成 `0`
      -> `reply+0x1c = 0`
  - regular path 才会走
    `com.apple.ane.iokit-user-access`
    entitlement-checked 路，
    但当前 probe 上：
    - controller-style `usageType=3`
    - outer `mode=3`
    都失败为 `0x18`
  - 所以这条 selector-0 线当前已经从
    “lower ready state 不明”
    收敛为：
    “当前成功 open 是 direct-path，
    它本来就把这一位做成 0；
    regular entitlement-checked path 当前又进不去”
- 下一步：
  - 去找 private / system framework 内
    还能成功进入 regular `H11ANEInUserClient`
    的 open route，
    而不是继续在 current direct-path 成功样本上追 ready flip。

## 2026-06-15 01:23:50 +0800

- 目标：
  - 完成 `aneuserd` XPC transport override 的 machine-local 验证，
    并把 `loadModelNewInstance` 的真实失败层级继续收窄。
- 动作：
  - 在
    `mps/ANE/experiments/ane_daemon_load_tap_probe.m`
    增加：
    - `--probe-new-instance`
    - `--only-case-substr`
    - daemon-side
      `loadModelNewInstance:options:modelInstParams:qos:withReply:`
      tap
    - 最小
      `_ANEModelInstanceParameters`
      构造器
  - 跑 non-artifact weighted-pre transport 对照：
    - `mps/ANE/.ane_runs/csv/ane_daemon_load_tap_probe_default_nonartifact_weighted_pre.csv`
    - `mps/ANE/.ane_runs/csv/ane_daemon_load_tap_probe_aneuserd_nonartifact_weighted_pre.csv`
  - 跑两组聚焦 new-instance case：
    - public/non-restricted:
      `source_with_cacheid|restricted_NO|has_cache_id`
    - private/restricted:
      `cache_modelAtURLWithCacheURLIdentifier|restricted_YES|empty`
    - 对应 v2 结果：
      - `mps/ANE/.ane_runs/csv/ane_daemon_load_tap_probe_default_newinstance_restricted_no_hascache_v2.csv`
      - `mps/ANE/.ane_runs/csv/ane_daemon_load_tap_probe_aneuserd_newinstance_restricted_no_hascache_v2.csv`
      - `mps/ANE/.ane_runs/csv/ane_daemon_load_tap_probe_default_newinstance_restricted_yes_empty_v2.csv`
      - `mps/ANE/.ane_runs/csv/ane_daemon_load_tap_probe_aneuserd_newinstance_restricted_yes_empty_v2.csv`
  - 持久化最近 15 分钟 daemon 日志：
    - `mps/ANE/.ane_runs/logs/aneuserd_aned_last15m_20260615_0120.log`
- 证据：
  - `aneuserd` override
    已证明能接住当前 `_ANEDaemonConnection`
    的
    `compiledModelExists*` / `loadModel`
    selector；默认
    `restricted_yes -> com.apple.appleneuralengine.private`
    仍只是 transport `4097`.
  - `loadModelNewInstance`
    最初的 `4097 + no reply`
    不是 daemon deeper lower gap，
    而是 probe 把
    `_ANEModelInstanceParameters._instanceName`
    错编码成了 `NSData`。
  - runtime introspection 已确认：
    `_ANEModelInstanceParameters`
    只有：
    - `_instanceName :: NSString`
    - `_procedureArray :: NSArray`
  - `aneuserd` 日志明确记录：
    - `value for key 'instanceName' was of unexpected class 'NSData'`
    - selector
      `loadModelNewInstance:options:modelInstParams:qos:withReply:`
      在 decode 阶段被丢弃
  - 把 `instanceName`
    修正为 `@"main"` 后，
    `loadModelNewInstance`
    在 default public route 与 `aneuserd` override
    上都稳定收到同一业务层 reply：
    - `Error Domain=com.apple.appleneuralengine Code=21`
    - `Program load new instance failure`
- 结论：
  - `aneuserd` override
    解决的是 private/restricted route 的 transport 可达性，
    不会自动解锁 new-instance 语义。
  - 当前 `loadModelNewInstance`
    的 blocker 已从
    “transport/secure-coding 形态错误”
    收敛到
    “server 业务层稳定拒绝，code=21”。
- 下一步：
  - 不再重复验证：
    - `aneuserd` transport 是否可通
    - `instanceName` 是否必须是 `NSString`
  - 直接矩阵化
    `instanceName / procedureArray / option`
    对 `code=21`
    的影响，或静态追
    `loadModelNewInstance` lower consumer。

## 2026-06-15 03:10:00 +0800

- 目标：
  - 校正 `ane_inmemory_new_instance_probe` 的
    `_ANEModelInstanceParameters`
    形态污染，
    并确认 public new-instance 现在真正卡在哪一层。
- 动作：
  - 修改
    `mps/ANE/experiments/ane_inmemory_new_instance_probe.m`
    的
    `make_model_instance_params_spec(...)`：
    - 不再把 `withProcedureData:procedureArray:`
      的第一个参数写成 `NSData`
    - 改为 `NSString instanceName`
  - 重编译：
    - `make -C mps/ANE/experiments ane_inmemory_new_instance_probe`
  - 在真实成功 base-load 上跑三组最小复测：
    1. strongest 单点：
       `base_shared_connection + base_internal_model + opts_internal_model_url_path + params_real_proc_main_data_main_weight_sha`
       -> `ane_inmemory_new_instance_probe_internalurl_weightsha_v2.csv`
    2. 同一 strongest param 下的全部 base-id 候选：
       -> `ane_inmemory_new_instance_probe_baseinternal_allopts_weightsha_v2.csv`
    3. strongest base-id 下的全部 param 形态：
       -> `ane_inmemory_new_instance_probe_baseinternal_internalurl_allparams_v2.csv`
  - 追加保存：
    - `aned_last10m_20260615_0310.log`
    - `adapterweight_entitlement_hits_20260615_0310.txt`
- 证据：
  - strongest 单点在修正后仍有 daemon business reply，
    且稳定是：
    `Code=21 / Program load new instance failure`
  - 全部 base-id 候选
    (`missing_base / model_hex / descriptor_hex / uuid / local_path /
      model_url_path / program_handle_decimal / internal_uuid /
      internal_model_url_path / internal_program_handle_decimal / model_hex_ibh`)
    仍统一 `Code=21`
  - strongest base-id 下的 param sweep 分出两类：
    1. real-procedure / real-weight 形态：
       - 有 reply
       - `Code=21`
    2. shim 形态：
       - request 发出
       - 但 reply 缺失
  - `aned` 日志把原因继续钉死：
    1. real-procedure / real-weight：
       `No entitlement! [com.apple.aned.private.adapterWeight.allow = 0]`
    2. shim：
       `decodeObjectForKey: class "CodexANEProcedureShim" not loaded or does not exist`
- 结论：
  - 旧的 `ane_inmemory_new_instance_probe` 负结果里，
    至少有一部分是 probe 形态错误，不再可直接引用。
  - 但把 `instanceName` 修正后，
    public `loadModelNewInstance`
    仍然被
    `com.apple.aned.private.adapterWeight.allow`
    entitlement gate 卡住。
  - 同时，
    `CodexANEProcedureShim`
    也不能再当成有效的 daemon-side procedure carrier；
    它只会制造 decode-drop 假阴性。
- 下一步：
  - 先判断是否存在可控的
    entitlement-bearing host/path
    能真正跨过
    `com.apple.aned.private.adapterWeight.allow`
  - 如果没有，
    就停止把 public `loadModelNewInstance`
    当作消除重复 load/compile 的现实入口，
    转回 private selector-8 / lower route

## 2026-06-15 03:38:00 +0800

- 目标：
  - 继续判断
    `adapterWeight.allow`
    gate 之后是否存在现实可用的 host path，
    而不是继续在 public `_ANEClient`
    路线上空转。
- 动作：
  - 重新核对带
    `com.apple.aned.private.adapterWeight.allow`
    的系统宿主：
    - `InferenceProviderService.appex`
    - `TGOnDeviceInferenceProviderService.appex`
    - `VisualGenerationInference.appex`
  - 核对
    `/usr/libexec/modelmanagerd`
    的 launchd plist / entitlements / strings
  - 运行时 `dlopen` 这些 extension binary，
    枚举实际载入的类，确认：
    - `ModelManagerServices.*`
    - `TokenGenerationInference.*`
    - `VisualGeneration.*`
    都会进当前进程
  - demangle 关键二进制：
    - `TGOnDeviceInferenceProviderService`
    - `TokenGenerationInference`
    - `ModelManagerServices` extract
  - 新增系统副本：
    - `mps/ANE/.ane_runs/system_bins/modelmanagerd`
    并为后续 IDA 预热。
- 证据：
  - `InferenceProviderService.appex`
    的 entitlements 已明确带：
    - `com.apple.aned.private.adapterWeight.allow`
    - `com.apple.aned.private.allow`
    - `com.apple.aned.private.processModelShare.allow`
    - `com.apple.security.exception.mach-lookup.global-name = com.apple.appleneuralengine`
  - `modelmanagerd` 是真实 host daemon：
    - MachServices:
      - `com.apple.modelmanager`
      - `com.apple.modelmanager.simulator`
      - feature-gated `com.apple.modelmanager.remote`
    - entitlements:
      - `com.apple.modelmanager.inferenceprovidermanager`
      - `com.apple.private.extensionkit.host.unsandboxed-extensions-for-extension-points`
        包含
        `com.apple.modelmanager.inferenceprovider`
  - `modelmanagerd` strings 已明确：
    - `getInferenceProvider(withDescriptor:)`
    - `createSessionRequest`
    - `InferenceProviderExtensionConnection`
    - `requestInference`
    - `requestInputStreamInference`
    - `Builtin InferenceProviderService extension not found`
    - `directInferenceProviderEndpoint`
    - `InferenceProviderServiceConnection`
  - `TGOnDeviceInferenceProviderService`
    demangle 已明确是：
    `ModelManagerServices.InferenceProviderExtension<TokenGenerationInference.TG_OnDeviceInferenceProvider>`
  - `TokenGenerationInference`
    demangle 已明确 provider 面至少有：
    - `OnDeviceInferenceProvider.requestOneShot(...)`
    - `OnDeviceInferenceProvider.requestStream(...)`
    - `TG_OnDeviceInferenceProvider.requestOneShot(...)`
    - `TG_OnDeviceInferenceProvider.requestStream(...)`
    - `TGIE5ANESessionObjC`
- 结论：
  - 当前最可能跨过
    `adapterWeight.allow`
    gate 的现实路径已经不是 public
    `_ANEClient loadModelNewInstance`
    本身，
    而是：
    `client -> com.apple.modelmanager -> modelmanagerd -> inferenceprovider appex -> ANE`
  - 但当前还没有 machine-local 可直接调用的
    `ModelManagerServices` client surface：
    - Swift module 不能直接 `import`
    - ObjC runtime 也拿不到可直接调用的方法表
  - 因而下一层工作已经收敛成：
    reverse
    `com.apple.modelmanager`
    request schema / Swift symbol 调用面，
    而不是继续猜 `newInstance` option。

## 2026-06-15 03:58:43 +0800

- 目标：
  - 把 `modelmanagerd / ModelManagerServices` 宿主链从“字符串级存在”
    收紧到 request/field 级事实。
- 动作：
  - 用 `nm -j | xcrun swift-demangle` 继续抽
    `ModelXPCRequest` /
    `InferenceProviderXPCRequest` /
    `InferenceProviderXPCSender` /
    `InferenceProviderRequestConfiguration` /
    `RequestMetadata`
    的真实 Swift 签名。
  - 用本机 `otool -l` + 新增的
    `mps/ANE/experiments/swift_fieldmd_dump.py`
    验证：
    - `CreateSessionRequest`
    - `InferenceProviderDescriptor`
    - `ConfigureBuiltInProviderRequest`
    - `DirectStreamHandshake`
    的真实字段。
  - 核对所有
    `com.apple.modelmanager.inferenceprovider`
    appex 的
    `InferenceProviderIdentifier`
    和
    `com.apple.aned.private.adapterWeight.allow`
    entitlement 分布。
  - 新增：
    - `mps/ANE/experiments/swift_fieldmd_dump.py`
    - `mps/ANE/experiments/results/modelmanager_host_route_schema_note.md`
- 证据：
  - `CreateSessionRequest`
    字段已确认为：
    - `metadata`
    - `alreadyLockedInferenceProvider`
  - `InferenceProviderDescriptor`
    字段已确认为：
    - `id`
    - `instance`
    - `hostedOnServer`
  - `Session.Metadata.init(...)`
    已明确要求：
    `assetBundleURI/useCaseID/onBehalfOfPID/parentOfOnBehalfOfPID/loggingIdentifier/id/sessionSetID`
  - `ConfigureBuiltInProviderRequest`
    已确认是单字段：
    `provider : BuiltInInferenceProvider`
  - `DirectStreamHandshake`
    已确认是单字段：
    `requestID`
    且从 sender 签名可继续收紧到
    `RequestKey`
  - `InferenceProviderXPCSender`
    已确认：
    - `requestInference(asStream:clientData:configuration:)`
    - `requestInputStreamInference(clientDataArray:metadata:configuration:)`
    - `directStreamHandshake(requestIdentifier:)`
    返回值存在
    `directInferenceProviderEndpoint`
  - provider id inventory：
    - `BlackPowderInferenceProvider`
    - `CoreMotionFoundationModelInferenceProvider`
    - `com.apple.modelmanager.inferenceprovider.built-in`
    - `generative-experiences-safety-inference-provider`
    - `host-inference`
    - `pcc-agent-client`
    - `private-ml-client`
    - `token-generation-inference`
    - `visual-generation-inference`
  - 当前带
    `com.apple.aned.private.adapterWeight.allow`
    的 provider 仅确认：
    - `com.apple.modelmanager.inferenceprovider.built-in`
    - `token-generation-inference`
    - `visual-generation-inference`
- 结论：
  - host route 已确认至少是两层协议：
    1. outer `ModelXPCRequest` session/request 层
    2. inner provider-side `InferenceProviderXPCRequest` 层
  - `BuiltInInferenceProvider`
    不是 extension-level
    `InferenceProviderIdentifier`
    列表，而更像 built-in appex 内部子 provider 选择面。
  - 下一轮最有价值的工作已经收敛到：
    - 解 provider-side
      `RequestRequest` /
      `InputStreamRequest`
      字段
    - 恢复
      `BuiltInInferenceProvider`
      case/raw-value
    - 判断能否最小构造
      `CreateSessionRequest -> directInferenceProviderEndpoint -> provider-side request`
- 下一步：
  - 先从
    `mps/ANE/experiments/results/modelmanager_host_route_schema_note.md`
    和
    `mps/ANE/experiments/swift_fieldmd_dump.py`
    继续；
    不要再回去扫 public `_ANEClient loadModelNewInstance` 参数矩阵。

## 2026-06-15 04:18:38 +0800

- 目标：
  - 继续收紧 provider-side inner request 形态，
    并判断 `built-in` appex 是否还是值得追。
- 动作：
  - 用
    `swift_fieldmd_dump.py`
    解出：
    - `InferenceProviderXPCRequest.InferenceRequest`
    - `InferenceProviderXPCRequest.InputStreamInferenceRequest`
  - 复制并分别打开：
    - `InferenceProviderService`
    - `InferenceProviderService_arm64e`
    到 IDA
  - 追
    `BuiltInInferenceProviderService`
    初始化链、
    `ProviderConfiguration.uninitializedBuiltIn(_:)`
    传入的本地 closure、
    `BuiltInInferenceProvider.inferenceProvider.getter`
  - 顺手核对
    `TGOnDeviceInferenceProviderService`
    与
    `TokenGenerationInference.framework`
    的链接和 provider 符号。
- 证据：
  - `InferenceRequest`
    已确认字段：
    - `isStream`
    - `clientData`
    - `configuration`
    - `requestIdentifier`
  - `InputStreamInferenceRequest`
    已确认字段：
    - `clientDataArray`
    - `metadata`
    - `configuration`
    - `requestIdentifier`
  - `InferenceProviderService_arm64e`
    里：
    - `BuiltInInferenceProvider.inferenceProvider.getter`
      decompile 为直接
      `fatalError`
    - 传给
      `InferenceProviderXPCRequestDispatcher.ProviderConfiguration.uninitializedBuiltIn(_:)`
      的本地 closure
      `sub_1000019AC`
      也直接
      `fatalError`
    - 两处都指向
      `InferenceProviderService/BuiltInInferenceProviderExtensions.swift`
  - `TGOnDeviceInferenceProviderService`
    已确认链接：
    `TokenGenerationInference.framework`
  - `TokenGenerationInference`
    已再次确认存在：
    - `TG_OnDeviceInferenceProvider.requestOneShot(...)`
    - `TG_OnDeviceInferenceProvider.requestStream(...)`
    - `TGIE5ANESessionObjC`
    - `adapterWeightsFileName`
    - `ANEClientModelAssetPath`
    - `TGI_ANE_Clear_State`
- 结论：
  - provider-side inner request 的最小形态已经不再空白；
    现在可以围绕
    `InferenceRequest/InputStreamInferenceRequest/DirectStreamHandshake`
    继续恢复编码面。
  - `com.apple.modelmanager.inferenceprovider.built-in`
    在当前 image 上高度可疑，
    更像 placeholder / dead end，
    不应再作为首选主线。
  - `token-generation-inference`
    更像现实的 entitlement-bearing provider 路径，
    下一轮应优先转向
    `TokenGenerationInference.framework`
    的真实实现。
- 下一步：
  - 以
    `token-generation-inference -> TokenGenerationInference.framework`
    为下一主线，
    看它如何把
    `InferenceProviderRequestConfiguration`
    / `RequestMetadata`
    / `TGIE5ANESessionObjC`
    接到实际 ANE 会话。

## 2026-06-15 05:31:34 +0800

- 目标：
  - 把 `token-generation-inference`
    这条主线从符号存在
    收紧到 request/context/session-lifecycle 级。
- 动作：
  - 用 `nm -an` / `swift-demangle` /
    `otool -tvV` /
    `strings -t x`
    继续抽：
    - `TG_OnDeviceInferenceProvider.requestOneShot`
    - `TG_OnDeviceInferenceProvider.requestStream`
    - `OnDeviceInferenceContextFactory.createInferenceContext`
    - `TGIE5ANESessionObjC`
  - 记录关键入口地址和日志点。
  - 新增：
    - `mps/ANE/experiments/results/token_generation_provider_route_note.md`
- 证据：
  - 入口地址已确认：
    - `requestOneShot = 0x275149e04`
    - `requestStream = 0x2751564bc`
    - `createInferenceContext = 0x2751295dc`
  - `requestOneShot/requestStream`
    的 async state machine
    已看到命中：
    - `createInferenceContext(...).addPromptLookup`
    - `createInferenceContext(...).addPriorOutputSpeculation`
    - `createInferenceContext(...).buildDecoder`
  - 已确认存在：
    - `tgSessionConfiguration for requestOneShot`
      日志点近 `0x27514a124`
    - `tgSessionConfiguration for prewarm`
      日志点近 `0x275151430`
    - `tgSessionConfiguration for requestStream`
      日志点近 `0x2751568c8`
  - `TGIE5ANESessionObjC`
    已确认：
    - `resume -> sendStartSignalForResource:useEnergyEfficientMode:assetIdentifier:`
    - `stop -> sendStopSignalForResource:`
    - `dealloc` 也会 stop
    - `init...` 只保存
      `resourceURL/useEnergyEfficientMode/assetIdentifier`
- 结论：
  - `TGIE5ANESessionObjC`
    只是 session-lifecycle / ANE signal wrapper，
    不是完整 inference implementation。
  - 真实 request shaping / context construction
    在：
    `TG_OnDeviceInferenceProvider`
    +
    `OnDeviceInferenceContextFactory`
  - 所以下轮最该做的是：
    等 IDA worker 可用后，
    直接反编译
    `TokenGenerationInference.framework`
    这三处主函数，
    再追
    `adapterWeightsFileName`
    / `ANEClientModelAssetPath`
    / `TGI_ANE_Clear_State`
    的消费链。

## 2026-06-15 06:18:31 +0800

- 目标：
  - 把
    `TokenGenerationInference.framework`
    从
    `request/context`
    继续收紧到
    `model configuration / base-model load / adapter asset staging / clear-state`
    级。
- 动作：
  - 用
    `otool -tvV`
    +
    `grep -nF`
    +
    `ida-pro-mcp.entity_query`
    继续抽：
    - `TGIModelConfigurationObjC`
    - `TGIE5BaseModelObjC`
    - `BaseModelLoader.load(from:)`
    - `LanguageModelLoader.load(from:baseModel:)`
    - `OnDeviceAssetRepository.handleCustomAsset...`
    - `TG_OnDeviceInferenceProvider.compileAdapter(...)`
    - `ANEAJAXE5MLModel::clearAllState`
- 证据：
  - `TGIModelConfigurationObjC`
    已确认至少暴露：
    - `modelBundlePath`
    - `adapterConfigurations`
    - `serializeModelIOPath`
    - `baseModel`
    - `useEnergyEfficientMode`
    - `useModelCatalogE5CompilerCache`
    - `assetIdentifier`
  - `TGIE5BaseModelObjC.initWithModelConfiguration:`
    已确认：
    - 读取 `modelBundlePath`
    - `URLWithString:`
      生成 resource URL
    - 读取
      `useEnergyEfficientMode`
      /
      `assetIdentifier`
    - 构造
      `TGIE5ANESessionObjC.initWithResourceURL:useEnergyEfficientMode:assetIdentifier:`
  - `TGIE5BaseModelObjC.load:`
    已确认：
    - 记录
      `Loading base model with model : %@`
    - 从
      `modelURL.path`
      取 path
    - 调用
      `cgm::token_generation_inference::espresso_inference::AJAXE5MLModelBase::create(path)`
    - `setBaseModel:`
    - `aneSession.resume`
  - `AppAssetManager`
    的真实调用位点已确认至少有两条：
    1. `OnDeviceAssetRepository.handleCustomAsset...`
    2. `TG_OnDeviceInferenceProvider.compileAdapter(...)`
    且二者都会走：
    `AppAssetManager(identifier:auditToken:...)`
    ->
    `copyAssetsIfNeeded(metadata, adapterWeights, draftMIL, draftWeights)`
  - `TGI_ANE_Clear_State`
    已确认落在：
    `cgm::token_generation_inference::ajax::ANEAJAXE5MLModel::clearAllState`
    /
    `clearAllState` block invoke，
    并会对
    `in_embeddings`
    所在 memory objects
    做
    `zeroAllMemoryObjects(...)`
- 结论：
  - `TokenGenerationInference`
    当前不是只有
    host/provider/request
    语义；
    我们已经拿到更具体的本地链：
    `TGIModelConfigurationObjC`
    ->
    `BaseModelLoader / LanguageModelLoader`
    ->
    `TGIE5BaseModelObjC`
    ->
    `AJAXE5MLModelBase`
    +
    `TGIE5ANESessionObjC`
  - `AppAssetManager`
    是 provider 正式路径的一部分；
    adapter / draft staging
    与 compile flow 强相关，
    值得继续沿
    `compileAdapter`
    深挖，
    而不是只盯
    `requestOneShot`
    外围状态机
- 下一步：
  - 优先 reverse：
    1. `LanguageModelLoader.load(from:baseModel:)`
       的
       `modelBundlePath`
       分支判定
    2. `TGIModelConfigurationObjC.serializeModelIOPath`
       /
       `useModelCatalogE5CompilerCache`
       消费链
    3. `compileAdapter(...)`
       在
       `copyAssetsIfNeeded(...)`
       之后的 compile/publish/handoff
       路径

## 2026-06-15 06:26:17 +0800

- 目标：
  - 确认
    `serializeModelIOPath`
    /
    `useModelCatalogE5CompilerCache`
    是否真进了 compile/load contract，
    不是只停留在 ObjC 属性层。
- 动作：
  - 用
    `otool -tvV`
    +
    `grep -nF`
    直接追：
    - `-[TGIModelConfigurationObjC modelConfiguration]`
    - `+[E5RunnerObjC compiledModelWithConfiguration:bundleCachePath:error:]`
    - `+[E5RunnerObjC doesModelRequireCompilationWithConfiguration:bundleCachePath:]`
- 证据：
  - `-[TGIModelConfigurationObjC modelConfiguration]`
    已确认会把：
    - `adapterConfigurations`
    - `e5Functions`
    - `useModelCatalogE5CompilerCache`
    - `ignoreUnknownTokens`
    - `serializeModelIOPath`
    写入内部 config；
    其中
    `serializeModelIOPath`
    明确被转成
    `UTF8String`
    再 append 到内部 `basic_string`
  - `+[E5RunnerObjC compiledModelWithConfiguration:bundleCachePath:error:]`
    已确认：
    - 先走
      `compilerOptionsForModelType(TGIModelType)`
    - 再按
      `modelBundlePath`
      构造 filesystem path
    - 若有 cache path，
      调
      `makeProgramLibrary(path, compilerOptions, optional<string> bundleCachePath)`
    - 若无 cache path，
      调
      `makeProgramLibrary(path, compilerOptions, bool useModelCatalogE5CompilerCache)`
  - `+[E5RunnerObjC doesModelRequireCompilationWithConfiguration:bundleCachePath:]`
    已确认：
    - 同样读取
      `modelBundlePath`
      /
      `modelType`
    - 做一层 path-extension 分流
    - 最终调
      `modelRequiresCompilation(...)`
      的
      `optional<string> bundleCachePath`
      或
      `bool useModelCatalogE5CompilerCache`
      形态
  - strings 侧还补到：
    - `.bundle`
    - `.mil`
    - `Model path has .bundle extension, assuming its already compiled: %@`
    - `/var/mobile/Library/com.apple.modelcatalog/compiled/e5bundlecache/`
    - `/var/db/com.apple.modelcatalog/protected/compiled/e5bundlecache`
- 结论：
  - `useModelCatalogE5CompilerCache`
    已经是 machine-local 可见的
    compile/load contract 控制位，
    不是高层装饰字段。
  - `.bundle`
    很可能就是
    already-compiled
    分支，
    而
    `.mil`
    是 source-style 输入之一；
    `e5bundlecache`
    则像 model-catalog compiler cache 根路径。
  - `TGIModelConfigurationObjC.modelConfiguration`
    是当前最值得继续盯住的
    ObjC -> internal runtime/config
    桥接层。
- 下一步：
  - 继续看
    `compilerOptionsForModelType`
    周围的 model-type 分流，
    以及
    `doesModelRequireCompilation`
    里的 path-extension 特判
  - 再把这条线和
    `LanguageModelLoader`
    /
    `compileAdapter`
    接起来

## 2026-06-15 06:37:20 +0800

- 目标：
  - 把
    `.mil/.bundle`
    分流进一步接到
    `E5RunnerObjC`
    和
    `mutableWeightsFilePath`
    这一层，
    看 ANE session 的 resource URL
    到底从哪里来。
- 动作：
  - 用
    `otool -tvV`
    继续读：
    - `LanguageModelLoader.load(from:baseModel:)`
    - `E5RunnerObjC.initWithModelConfiguration:error:`
    - `compiledModelAtPath:modelType:bundleCachePath:error:`
    - `TGIAdapterConfigurationObjC`
      相关构造位点
- 证据：
  - `LanguageModelLoader.load(from:baseModel:)`
    已确认：
    - `.mil`
      与
      `.bundle`
      都会落到
      `E5RunnerObjC.initWithModelConfiguration:error:`
  - `E5RunnerObjC.initWithModelConfiguration:error:`
    已确认：
    - 先取
      `modelConfiguration`
    - 调
      `AJAXE5MLModelLoader::createModelFromBundle(TGIModelConfiguration)`
    - 若
      `modelType == 1`
      ，则读取
      `adapterConfigurations.anyObject.mutableWeightsFilePath`
      作为优先 resource URL；
      若没有，
      才退回
      `modelBundlePath`
    - 然后构造
      `TGIE5ANESessionObjC.initWithResourceURL:useEnergyEfficientMode:assetIdentifier:`
      并 `resume`
  - `compiledModelAtPath:modelType:bundleCachePath:error:`
    已确认：
    - 先构造
      `TGIModelConfigurationObjC`
    - 再按
      `bundleCachePath == nil`
      设置
      `useModelCatalogE5CompilerCache`
    - 然后调
      `compiledModelWithConfiguration:bundleCachePath:error:`
  - provider 内另一条构造路径
    已确认会在
    `fileExistsAtPath(...)`
    成功后，
    创建：
    `TGIAdapterConfigurationObjC.initWithAdapterType:symbolName:mutableWeightsFilePath:`
  - imports 已确认还出现：
    - `ModelCatalog...ANEExtendInfo.adapterType`
    - `adapterTypeToSymbolMapping`
    - `adapterTypeToSignatureMapping`
- 结论：
  - `mutableWeightsFilePath`
    不是边缘字段；
    它已经是
    ANE session resource URL
    的直接来源之一。
  - 当前最有价值的下一步，
    不是重新看 outer request，
    而是继续把
    `compileAdapter / model catalog metadata`
    如何产出
    `mutableWeightsFilePath`
    接到这条 ANE session 链上。
- 下一步：
  - 继续逆：
    1. `compileAdapter(...)`
       之后谁写出
       `mutableWeightsFilePath`
    2. `adapterTypeToSymbolMapping`
       /
       `adapterTypeToSignatureMapping`
       的实际消费点
    3. `ANEClientModelAssetPath`
       是否就是同一条
       compiled bundle / mutable weight publish
       contract

## 2026-06-15 07:04:59 +0800

- 目标：
  - 确认
    `ANEClientModelAssetPath`
    到底属于 compile contract
    还是 start/stop session hint。
- 动作：
  - 直接读：
    - `+[TGIE5ANESessionObjC sendStartSignalForResource:useEnergyEfficientMode:assetIdentifier:]`
    - `+[TGIE5ANESessionObjC sendStopSignalForResource:]`
  - 结合
    `__AUTH_CONST.__cfstring`
    地址与字符串长度
    反推匿名 cfstring key。
- 证据：
  - `sendStartSignal...`
    里当前已确认会构造两项字典：
    - key `0x29e267700`
      + value `resource.path`
    - key `0x29e267720`
      + value `NSNumber(useEnergyEfficientMode)`
  - 随后它把这个字典交给
    `0x29e267740`
    对应的 hint 调用，
    再从返回字典里用：
    - `0x29e267760`
    - `0x29e267780`
    取回两个数值指标
  - `sendStopSignal...`
    里会构造单项字典：
    - key `0x29e267700`
      + value `resource.path`
    再交给
    `0x29e2677a0`
    对应的 hint 调用
  - 结合本地字符串长度和顺序，
    当前可以稳定对上：
    - `0x29e267700` -> `ANEClientModelAssetPath`
    - `0x29e267720` -> `ANEClientEnergyEfficientWorkload`
    - `0x29e267740` -> `ANEHintClientSessionStart`
    - `0x29e267760` -> `ANEClientTotalPages`
    - `0x29e267780` -> `ANEClientResidentPages`
    - `0x29e2677a0` -> `ANEHintClientSessionStop`
- 结论：
  - `ANEClientModelAssetPath`
    当前更像
    ANE session lifecycle hint / telemetry key，
    而不是
    `TGIModelConfiguration`
    那层 compile/load contract key。
  - 所以下一步应继续追
    `mutableWeightsFilePath`
    的 producer，
    而不是优先围绕
    `ANEClientModelAssetPath`
    误判 compile 面。
- 下一步：
  - 继续收紧：
    1. `loadAsset` / `compileAdapter`
       谁落盘
       `mutableWeightsFilePath`
    2. `adapterTypeToSymbolMapping`
       /
       `adapterTypeToSignatureMapping`
       与这个落盘动作的关系

## 2026-06-15 07:04:59 +0800

- 目标：
  - 把
    `mutableWeightsFilePath`
    的 producer
    再往前接到
    custom asset staging / publish
    这一层。
- 动作：
  - 继续读：
    - `OnDeviceAssetRepository.handleCustomAsset...`
    - `TGIAdapterConfigurationObjC.adapterConfiguration`
    - `TGIModelConfiguration.mutableWeightsSymbolToPath`
- 证据：
  - `handleCustomAsset...`
    在
    `copyAssetsIfNeeded(...)`
    之后，
    当前已看到：
    - 检查
      `/var/mobile/ajax/adapter.weights.bin`
      是否存在
    - 若存在则构造
      `TGIAdapterConfigurationObjC.initWithAdapterType:symbolName:mutableWeightsFilePath:`
    - 随后再用
      `/var/mobile/ajax/model.bundle`
      +
      adapter config
      +
      e5 functions
      构造
      `TGIModelConfigurationObjC`
  - `TGIAdapterConfigurationObjC.adapterConfiguration`
    已确认会把：
    - `adapterType`
    - `symbolName`
    - `mutableWeightsFilePath`
    转成内部：
    - `std::string`
    - `std::string`
    - `filesystem::path`
  - `TGIModelConfiguration.mutableWeightsSymbolToPath`
    已确认会把：
    `symbolName -> mutableWeightsFilePath`
    写进内部 `unordered_map`
- 结论：
  - `mutableWeightsFilePath`
    当前不是单纯 session hint，
    而是：
    custom asset staging
    ->
    adapter config
    ->
    symbol-to-path map
    ->
    ANE session resource
    这条链上的正式一环。
  - `/var/mobile/ajax/adapter.weights.bin`
    /
    `/var/mobile/ajax/model.bundle`
    当前很像 custom adapter/bundle
    publish 后的标准落点。
- 下一步：
  - 优先确认：
    1. `compileAdapter(...)`
       是否也写到同一对路径
    2. `symbolName -> mutableWeightsFilePath`
       map
       在
       `AJAXE5MLModelLoader`
       /
       `E5RunnerObjC`
       内部的具体消费点

## 2026-06-15 08:23:46 +0800

- 目标：
  - 收紧
    `compileAdapter`
    /
    `AppAssetManager`
    /
    `loadAsset`
    /
    `adapterTypeToSymbolMapping`
    之间的真实职责边界。
- 动作：
  - 重新打开
    `TokenGenerationInference`
    的 IDA session：
    `tokengenerationinference_arm64e`
  - 反编译并核对：
    - `compileAdapter TY0`
      (`0x275165634`)
    - `AppAssetManager.__allocating_init`
      (`0x2750d8a28`)
    - `loadAsset TY0`
      (`0x275151754`)
    - `handleLLMAdapterMetadataOverride TY0`
      (`0x2750fcf6c`)
    - `modelConfigurationWithURL`
      (`0x2750f7e18`)
  - 交叉使用：
    - `xrefs_to`
      看
      `/var/mobile/ajax/model.bundle`
      /
      `/var/mobile/ajax/adapter.weights.bin`
      的真实引用点
    - `strings`
      +
      小字符串解码，
      确认
      `1634889580 -> "lora"`
- 证据：
  - `compileAdapter TY0`
    当前只显式做到：
    `AppAssetManager.copyAssetsIfNeeded(...)`
    +
    `DraftModelCompiler.findCompiledDraftPathOrBeginCompilation(...)`
    ，
    没有直接 xref 到：
    - `/var/mobile/ajax/model.bundle`
    - `/var/mobile/ajax/adapter.weights.bin`
  - `AppAssetManager.__allocating_init`
    设定默认文件名：
    - `adapterWeightsFileName = "lora.part.bin"`
    - `draftMILFileName = "draft.mil"`
    - `draftWeightsFileName = "draft_weights.bin"`
    - 同时暴露 internal cache tree
      常量：
      - `/private/var/db/AppleIntelligencePlatform/AppModelAssets`
      - `tmp/`
      - `manifest.json`
  - `loadAsset TY0`
    在路径存在时会直接构造：
    `TGIAdapterConfigurationObjC.initWithAdapterType:symbolName:mutableWeightsFilePath:`
    然后再构造：
    `TGIModelConfigurationObjC.initWithModelType:modelBundlePath:e5Functions:adapterConfigurations:`
  - 当前已能稳定对上它的 fallback/default：
    - `symbolName = "lora"`
    - `mutableWeightsFilePath = /var/mobile/ajax/adapter.weights.bin`
    - `modelBundlePath = /var/mobile/ajax/model.bundle`
  - `Metadata json is missing adapter type to symbol mapping`
    当前 xref 在：
    `modelConfigurationWithURL(...)`
    (`0x2750f7e18`)
  - `handleLLMAdapterMetadataOverride(...)`
    则命中：
    - `Override metadata adapter signature ...`
    - `Metadata override cannot be supported on adapter ...`
  - `copyAssetsIfNeeded(...)`
    已能确认：
    - 先调用
      `createCacheDirectoryIfNeeded()`
      /
      `createTemporaryDirectoryIfNeeded()`
    - 再对
      `metadata / adapterWeights / draftWeights / draftMIL`
      分别拼 URL
      并调
      `copyContents(fd, url)`
    - `copyContents(...)`
      会记录：
      `Copying file descriptor %{public}d to %{public}s`
  - 缩范围 strings 检索后，
    `/var/mobile/ajax/model.bundle`
    /
    `adapter.weights.bin`
    /
    `draftModel.bundle`
    /
    `tokenizer`
    当前只在
    `TokenGenerationInference.framework`
    内出现，
    不在
    `ModelManagerServices.framework`
    /
    `ModelCatalog.framework`
    内出现
- 结论：
  - 旧假设
    “`compileAdapter(...)`
    直接写
    `/var/mobile/ajax/model.bundle`
    +
    `/var/mobile/ajax/adapter.weights.bin`”
    当前不成立。
  - 更接近 machine-local 事实的是：
    1. `compileAdapter`
       负责
       copy
       +
       draft compile
    2. `copyAssetsIfNeeded(...)`
       的 immediate destination
       是
       `AppAssetManager`
       internal cache/temp tree，
       不是直接
       `/var/mobile/ajax/*`
    3. `/var/mobile/ajax/*`
       pair
       当前在
       `loadAsset`
       消费面上形成
       `TGIAdapterConfigurationObjC`
       /
       `TGIModelConfigurationObjC`
       contract
    4. `/var/mobile/ajax/*`
       当前仍更像
       `TokenGenerationInference`
       内部统一 published view
       ，
       bridge
       大概率还在该 framework 内部
    5. `adapterTypeToSymbolMapping`
       /
       `adapterTypeToSignatureMapping`
       的原始解析
       主要在
       `modelConfigurationWithURL(...)`
       ，
       override
       分支再做一致性约束
- 下一步：
  - 继续 reverse：
    1. `AppAssetManager.copyAssetsIfNeeded(...)`
       四个 copy arm
       各自使用
       `cacheDirectory`
       /
       `temporaryDirectory`
       的哪一个，
       以及 internal cache tree
       如何 later-publish 到
       `/var/mobile/ajax/*`
    1.5 不再优先扩大到
       `ModelManagerServices`
       /
       `ModelCatalog`
       ，
       先把
       `TokenGenerationInference`
       内部 bridge
       走通
    2. `loadAsset`
       里的
       `off_29E2641D0 / 1D8 / 1E0 / 1E8`
       精确字段语义
    3. `modelConfigurationWithURL(...)`
       内
       `adapterTypeToSymbolMapping`
       /
       `adapterTypeToSignatureMapping`
       如何产出最终
       `adapterType / symbolName / mutableWeightsFilePath`
       组合
  - 本轮最后又补了一层：
    - `off_29E2641D0 -> /var/mobile/ajax/model.bundle`
    - `off_29E2641D8 -> /var/mobile/ajax/adapter.weights.bin`
    - `off_29E2641E0 -> "lora"` fallback
    - `off_29E264200 -> /var/mobile/ajax/tokenizer`
    - `off_29E2641E8`
      仍待继续确认

## 2026-06-15 18:54:36 +0800

- 目标：
  - 继续追
    `TokenGenerationInference.framework`
    里
    internal cache
    /
    published view
    的桥接链。
- 动作：
  - 重新分析：
    - `OnDeviceInferenceContextFactory.createInferenceContext`
      (`0x27512a0a0`)
    - `AssetRepository.fetchAssetObjects`
      (`0x27511267c`)
    - `AssetRepository.loadAsset`
      (`0x27510d470`)
    - `handleLLMAdapterMetadataOverride`
      (`0x2750fcf6c`)
    - `TG_OnDeviceProvider.loadAsset TY0`
      (`0x275151754`)
    - `TG_OnDeviceProvider.loadAsset TY5`
      (`0x27515286c`)
    - `handleCustomAsset TY2`
      (`0x275103f50`)
  - 核对并修正
    override getter
    映射：
    - `off_29E2641D0`
    - `off_29E2641D8`
    - `off_29E2641E0`
    - `off_29E2641E8`
    - `off_29E264200`
  - 确认
    `handleCustomAsset TY2`
    调
    `handleDraftModel(...)`
    时
    已携带
    `explicitBundleFileURL`
    参数。
- 证据：
  - `createInferenceContext`
    先读
    `modelPath/tokenizerPath/draftModelPath`
    override，
    只有 getter 返回 `nil`
    才回退到：
    - `/var/mobile/ajax/model.bundle`
    - `/var/mobile/ajax/tokenizer`
    - `/var/mobile/ajax/draftModel.bundle`
  - 它随后直接
    `fileExistsAtPath:`
    检查这些 target path，
    再把缺失项下沉到：
    `AssetRepository.fetchAssetObjects(identifiers:configuration:)`
  - getter 映射已修正为：
    - `1D0 -> modelPath`
    - `1D8 -> adapterPath`
    - `1E0 -> mutableWeightSymbolName`
    - `1E8 -> tokenizerPath`
    - `200 -> draftModelPath`
  - `loadAsset TY0`
    会读取
    `adapterPath`
    /
    `mutableWeightSymbolName`
    /
    `modelPath`
    并在 adapter path 存在时构造：
    `TGIAdapterConfigurationObjC.initWithAdapterType:symbolName:mutableWeightsFilePath:`
  - `loadAsset TY5`
    会读取
    `draftModelPath`
    并在缺省时回退
    `/var/mobile/ajax/draftModel.bundle`
- 结论：
  - 当前更像是
    `override -> default-path selector -> fileExists -> fetchAssetObjects`
    这条 consumer-side
    控制链，
    不是已经确认的
    internal cache tree
    -> `/var/mobile/ajax/*`
    writer。
- 下一步：
  - 继续下钻
    `fetchAssetObjects(...)`
    /
    `loadAsset(...)`
    的后半段，
    看 missing asset
    最终 materialize 到哪里，
    以及
    `explicitBundleFileURL`
    是否就是 draft publish 的真正入口。
  - 同时优先验证新的更强假设：
    `handleLLMAdapter / handleDraftModel`
    传入
    `findURLOfKnown*Asset`
    的 base URL
    是否已经就是
    internal cache/temp
    目录；
    若是，
    则 bridge
    可能只是
    known-file discovery，
    而不是
    ajax publish

- 补充证据（同轮）：
  - `findURLOfKnownModelAsset(...)`
    当前已确认会探测：
    - `model.bundle`
    - `model.mil`
    - `model.mlir.bc`
    - `model.mlir`
  - `findURLOfKnownAdapterAsset(...)`
    当前已确认会探测：
    - `lora.part.bin`
    - `adapter.mlir.bc`
    - `adapter.mlir`
  - 其中
    `lora.part.bin`
    与
    `AppAssetManager.adapterWeightsFileName`
    完全一致。
  - `handleLLMAdapter` wrapper stub
    (`0x2750fe7d4`)
    当前已确认：
    - `a4 -> [state + 0x7C8]`
    - `handleLLMAdapter TY0`
      在
      `0x2750ff1a4`
      从
      `[state + 0x7C8]`
      取值，
      并把它作为
      `findURLOfKnownAdapterAsset(...)`
      的 `in:` base URL。
  - 两个 call site
    也补了一层：
    - `loadAsset dispatcher`
      (`0x27510f220`-`0x27510f268`)
      用 `X3 = X27`
      传入这个 base URL 槽位
    - `handleCustom TY0`
      (`0x275103dbc`-`0x275103e04`)
      用 `X3 = [SP + var_78]`
      传入同一槽位，
      且调用前已出现
      `Loading custom adapter from: %{public}s`
      这类 path/url
      相关日志

2026-06-15 20:20:28 CST

- 目标：
  - 继续锁死
    `loadAsset dispatcher -> X27 -> handleLLMAdapter(a4)`
    的真实语义，
    判断它是不是仍然需要
    `/var/mobile/ajax/*`
    publish bridge
- 动作：
  - 用 IDA 继续读
    `loadAsset`
    (`0x27510d470`)
    在
    `0x27510daa4`
    /
    `0x27510dc24`
    /
    `0x27510f220`
    周围的汇编
  - 继续读
    `OnDeviceInferenceProviderDataSource.asset(for:)`
    (`0x27517a558`)
    与
    `catalogResource(for:)`
    (`0x27517a468`)
  - 抽查
    `handleLLMAdapter TY0`
    (`0x2750fe808`)
    的局部指令，
    用来校正
    `a4`
    更像
    `Asset`
    还是裸 URL
- 证据：
  - `loadAsset`
    在
    `0x27510daa4`
    把
    `[SP + var_80]`
    装回
    `X27`
    并传给
    `OnDeviceInferenceProviderDataSource.catalogResource(for:)`
    (`0x27510dab0`)
  - 成功后，
    `loadAsset`
    在
    `0x27510dbb0`-
    `0x27510dc28`
    分配
    `Asset`
    存储，
    再在
    `0x27510dc24`
    调
    `OnDeviceInferenceProviderDataSource.asset(for:)`
    (`0x27517a558`)
  - `asset(for:)`
    的 decompile
    明确显示：
    - 先再次调
      `catalogResource(for:)`
      (`0x27517a68c`)
    - 再要求资源能视为
      `AssetBackedResource`
      (`0x27517a710`)
    - 最后把构造出的
      `Asset`
      字段写回 caller
      buffer
      (`0x27517aaf4`)
  - `handleCustom`
    路此前已确认：
    `0x275103a2c`
    直接取
    `AppAssetManager.cacheDirectory`
    并把它写进传给
    `handleLLMAdapter(...)`
    的
    `Asset`
    值对象
- 结论：
  - `loadAsset`
    标准路径与
    `handleCustom`
    路径，
    当前都更像是
    “先准备带有
    root 信息的上游对象”
  - 但这轮后半段又补到一条
    更精确的 machine-local
    事实：
    `handleLLMAdapter TY0`
    在
    `0x2750ff1a4`-
    `0x2750ff1fc`
    直接把
    `[state + 0x7C8]`
    按
    `Foundation.URL?`
    喂给
    `findURLOfKnownAdapterAsset(...)`
  - 因而
    `a4/X3`
    到达
    `handleLLMAdapter`
    边界时，
    不应再记成
    `Asset`
    ；更准确的描述是：
    上游某一步已经把
    `Asset`
    或 custom 路的等价对象
    lowering 成了
    `Foundation.URL?`
  - 随后又补到一个更重要的
    ABI 纠偏：
    不能再把
    `handleLLMAdapter`
    wrapper
    里的
    `[7B8]/[7C0]/[7C8]/[7D0]/[7D8]`
    当成
    “五个业务参数”
    逐个对应
  - 当前 machine-local
    事实更支持：
    - `identifier: String`
      在 call-site
      上更像占
      `X1 / X2`
    - `asset: Asset`
      也按字段拆成多个
      machine words，
      当前至少能看到
      `X3 / X4 / X20`
      继续参与传参
    - wrapper
      保存的是这两者的
      ABI 展开结果
  - `Asset`
    的 field metadata
    (`0x275244c1c`)
    也已部分解出：
    - 字段 1 名称：
      `url`
    - 字段 2 名称：
      `version`
    - 字段 1 类型 typeref：
      `Foundation.URL`
  - 因而
    `0x2750ff1a4`
    读出的
    `[state + 0x7C8]`
    更准确的含义不是
    “原始 a4 就是 URL”，
    而是：
    `asset: Asset`
    ABI 展开后的其中一段，
    且这段在该 call site
    被当成
    `Foundation.URL?`
    参数的一部分
  - 当前最佳临时映射：
    - `[7B8]/[7C0]`
      更像
      `identifier`
    - `[7C8]/[7D0]/[7D8]`
      更像
      `asset`
      的展开部分
    - 其中
      `[7C8]`
      参与
      `asset.url`
      的 URL? 传参
    - `[7D8]`
      更像
      `asset.version`
      一侧的 machine word
  - 又补到一条对后续非常关键的
    metadata 纠偏：
    - `ProviderDataSource.asset(for:)`
      在
      `0x27517aaf0`
      用
      `LDRSW [#0x14]`
      取第二字段 offset
    - `handleCustom`
      看起来在
      `0x275103a90`
      用的是
      `LDRSW [#0x1C]`
    - 但其前面紧接着有
      `LDR ... [X19,#-8]!`
      写回，
      所以有效地址仍回到
      原 metadata
      的
      `+0x14`
    - 因而目前看到的并不是
      两套冲突 offset，
      而是同一条
      second-field offset
      读取逻辑
  - 还补到一条更细的事实：
    optional `Asset?`
    的 payload offset
    也不是全局常数
    - `AssetObjectTokenizer.asset`
      走
      `*(int *)(metadata + 20)`
      /
      `+0x14`
    - `AssetObjectImageTokenizer.asset`
      走
      `*(int *)(metadata + 24)`
      /
      `+0x18`
    - 所以后续必须按
      具体 metadata
      头布局来解释
      payload offset，
      不能再把它写死成
      单一常数
  - 这进一步削弱了
    “必须存在
    internal cache
    -> `/var/mobile/ajax/*`
    publish bridge
    才能跑通 adapter load”
    这个前提
  - 下一步：
  - 继续拆
    `Asset`
    的两个字段
    `url`
    /
    `version`
    的具体偏移与类型
    ，尤其要锁死
    second-field offset
    在不同 metadata
    头布局下
    为什么会落到
    `+0x14`
    或
    `+0x18`
  - 再按
    Swift ABI
    重建
    `handleLLMAdapter`
    参数展开，
    把
    `[7B8]/[7C0]/[7C8]/[7D0]/[7D8]`
    映射回
    `identifier`
    /
    `asset.url`
    /
    `asset.version`
  - 最后再回到
    `findURLOfKnownAdapterAsset(...)`
    这条 call，
    确认实际喂进去的是
    `asset.url`
2026-06-16 15:04:13 +0800
- 目标：
  - 继续还原
    `handleLLMAdapter`
    的 Swift ABI，
    重点确认
    `[7C8]/[7D0]/[7D8]`
    是否真是
    `asset`
    的直接寄存器展开
- 动作：
  - 用 IDA 继续核对
    `handleCustom TY0`
    (`0x275102960`)
    /
    `loadAsset TY0`
    (`0x27510d470`)
    两条 caller
    在最终跳进
    `handleLLMAdapter`
    wrapper
    (`0x2750fe7d4`)
    前的
    `X3/X4/X20`
    来源链
  - 重点看了：
    - `0x2751039fc`-
      `0x275103a98`
    - `0x275103b74`
    - `0x275103dd0`
    - `0x27510dbc4`-
      `0x27510dc24`
    - `0x27510f234`
    - `0x2750ff1a4`-
      `0x2750ff1fc`
- 证据：
  - `handleCustom`
    先分配并填充
    `Asset`
    buffer
    (`X26`)，
    再在
    `0x275103b74`
    把该 buffer
    指针存入
    `[SP + var_78]`，
    最终
    `0x275103dd0`
    用
    `X3 = [SP + var_78]`
    调
    `handleLLMAdapter`
  - `loadAsset`
    先在
    `0x27510dbc4`-
    `0x27510dc24`
    分配 caller-owned
    `Asset`
    buffer
    (`X27`)
    并通过
    `ProviderDataSource.asset(for:)`
    直接写满，
    最终
    `0x27510f234`
    用
    `X3 = X27`
    调
    `handleLLMAdapter`
  - 因而
    `wrapper`
    里
    `X3 -> [state + 0x7C8]`
    当前应解释为
    `Asset`
    存储起始地址
    / 间接 URL 基址，
    而不是
    “裸 URL”
    或
    “asset 直接寄存器展开第一段”
- 结论：
  - 旧的
    “`asset`
    继续占
    `[7C8]/[7D0]/[7D8]`”
    假设
    已被 machine-local
    caller 证据推翻
  - 当前更稳的表述是：
    - `[7B8]/[7C0]`
      仍最像
      `identifier: String`
    - `[7C8]`
      是
      `Asset`
      起始地址
      / 间接
      `Foundation.URL?`
      基址
    - `[7D0]`
      /
      `[7D8]`
      暂时不能再直接写成
      `asset.version`
- 下一步：
  - 确认
    `findURLOfKnownAdapterAsset(in:...)`
    的
    `Foundation.URL?`
    是否按
    indirect / by-address
    ABI 消费
  - 单独识别
    `[7D0]`
    /
    `[7D8]`
    的真实来源与语义
2026-06-16 17:26:19 +0800
- 目标：
  - 给
    `[7C8] = Asset 起始地址 / 间接 URL 基址`
    再补一层 callee-side
    ABI 证据
- 动作：
  - 重开
    `TokenGenerationInference`
    IDA session
  - 反编译并反汇编：
    - `findURLOfKnownAdapterAsset`
      (`0x2751ae1bc`)
    - `findURLOfKnownModelAsset`
      (`0x2751adf00`)
- 证据：
  - 两个函数
    decompile
    形态都显示为：
    `@<X0>(char *a1@<X8>)`
  - 也就是：
    返回的
    `Foundation.URL?`
    本身就是
    Swift indirect-result
    / by-address
    lowering
  - 这与
    `handleLLMAdapter TY0`
    在
    `0x2750ff1ec`-
    `0x2750ff1fc`
    的 callsite
    完全一致：
    先
    `MOV X8, X24`
    再
    `BL findURLOfKnownAdapterAsset`
- 结论：
  - `[7C8]`
    现在可以更稳地解释为：
    `Asset.url`
    的间接存储基址，
    而不是
    “URL? 的直接寄存器值”
  - 下一步的主要不确定性
    已收缩到：
    `[7D0]`
    /
    `[7D8]`
    是否属于
    async / continuation
    lowering
- 下一步：
  - 单独追
    `[7D0]`
    /
    `[7D8]`
    的写入来源和消费点，
    优先验证它们是否与
    async context
    /
    continuation
    相关
2026-06-16 18:20:05 +0800
- 目标：
  - 继续拆
    `[7D0]`
    /
    `[7D8]`
    ，确认哪些是
    hidden async lowering，
    哪些仍可能是
    显式业务参数
- 动作：
  - 重新打开
    `TokenGenerationInference`
    IDA session
  - 回到
    `handleCustom`
    /
    `loadAsset`
    的 async wrapper
    存参点，
    再用
    `handleDraftModel`
    做同型对照
- 证据：
  - `handleCustom`
    wrapper
    (`0x27510293c`)
    明确：
    - `X20 -> [ctx + 0xE8]`
    - `a3  -> [ctx + 0xF0]`
    - `a1/a2 -> [ctx + 0xD8]/[ctx + 0xE0]`
  - `loadAsset`
    wrapper
    (`0x27510d444`)
    明确：
    - hidden `X20 -> [ctx + 0x430]`
    - `a3 -> [ctx + 0x438]`
    - `a1 -> [ctx + 0x428]`
  - 同型对照
    `handleDraftModel`
    wrapper
    (`0x275107674`)
    明确：
    - `X20 -> [0x440]`
    - 显式业务参数顺排
      `X0..X5`
  - `handleLLMAdapter`
    wrapper
    正对应：
    - `X20 -> [0x7D0]`
    - `X4  -> [0x7D8]`
- 结论：
  - `[7D0]`
    现在基本可定性为
    hidden async context /
    continuation lowering
    ，不应再往
    `Asset`
    字段上套
  - 仍未锁死的
    主要剩
    `X4 / [7D8]`
    ：
    它比
    `[7D0]`
    更像最后一个
    显式业务 lowering
    word
- 下一步：
  - 单独追
    `X4 / [7D8]`
    在
    `handleLLMAdapter`
    内的全部消费点，
    判断它是否真能落到
    `asset.version`
    或其他显式业务 lowering
2026-06-16 19:26:43 +0800
- 目标：
  - 锁死
    `handleLLMAdapter`
    里
    `X4 / [7D8]`
    的真实语义，
    并复核
    `[7D0]`
    是否被过早写成
    continuation context
- 动作：
  - 继续使用
    `tokengenerationinference_arm64e`
    session
  - 对照：
    `handleLLMAdapter`
    wrapper / TY0 / TY3、
    `handleCustom`
    wrapper / TY0、
    `loadAsset`
    wrapper / TY0
  - 追加检查：
    `AssetBackedLLMAdapter`
    导入符号类型，
    以及
    `_1400`
    的所有失败路径调用点
- 证据：
  - `AssetBackedLLMAdapter`
    导入表是
    `_$s12ModelCatalog21AssetBackedLLMAdapterMp`
    ，说明它是
    protocol，
    不是 concrete metadata
  - `handleCustom`
    wrapper
    (`0x27510293c`)
    明确只保存：
    - `a1/a2 -> [0xD8]/[0xE0]`
    - `a3 -> [0xF0]`
    - `X20 -> [0xE8]`
    对应
    `(configuration, template)`
    的 local async helper
    机器级 lowering
  - `handleCustom TY0`
    在尾调
    `handleLLMAdapter(...)`
    前，
    会先通过
    `j__$...TW_598(0)`
    取 imported type metadata，
    再按
    value-witness
    `+0x40`
    动态分配 buffer
    (`0x275103d18`-
    `0x275103d88`)
    ，并把该 buffer
    指针放进
    `X4`
  - `loadAsset`
    wrapper
    (`0x27510d444`)
    把
    `a3`
    存到
    `[0x438]`；
    `loadAsset TY0`
    失败路径再取回
    `LDR X19, [X22,#0x438]`
    并调用
    `_1400`
    (`0x27510ef34`-
    `0x27510ef78`)
  - `handleLLMAdapter TY0`
    / `TY3`
    失败路径也同型：
    - `0x2750fecc8`-
      `0x2750fed0c`
    - `0x2751016a8`-
      `0x2751016ec`
    - `0x275102744`-
      `0x275102788`
    都是先取
    `[7D8]`
    ，再配
    `ModelManagerServices.InferenceError`
    imported witness
    调
    `_1400`
- 结论：
  - `[7D8] = X4`
    现在基本可排除
    `asset.version`
    /
    `Asset`
    剩余 field word
    假设；
    更像
    `async throws(ModelManagerServices.InferenceError)`
    lowering
    里的
    typed error/result
    storage
    指针
  - `[7D0] = X20`
    目前不能再直接写死成
    continuation context；
    更保守的表述应改成：
    local async helper
    沿
    `X20`
    传递的隐藏槽位，
    待继续判断它更接近
    `self`
    还是其它 hidden lowering
- 下一步：
  - 继续恢复
    `_1400`
    的真实 imported symbol，
    判断它构造的是
    `InferenceError`
    本体
    还是
    `InferenceError.Context`
  - 继续确认
    `[7D0]`
    在这些 helper
    里究竟对应
    `self`
    / continuation record
    / 其它 hidden slot
2026-06-16 19:41:12 +0800
- 目标：
  - 用本机 Swift ABI
    最小样例验证
    `[7D8]`
    的 typed-throws
    假设
- 动作：
  - 在
    `/tmp/swiftabi.8d32iQ/`
    写
    `sample.swift`
    ，构造：
    - `any P`
    - `Asset`
    - `async throws(E)`
    - local helper
    - 显式 `throw .failed(Ctx(...))`
  - 用
    `xcrun swiftc`
    生成：
    - `/tmp/swiftabi.8d32iQ/sample.s`
    - `/tmp/swiftabi.8d32iQ/sample.sil`
  - 对照
    `Repo.handle`
    /
    `Repo.helper`
    /
    `Repo.custom`
    的 entry 与 throw path
- 证据：
  - `sample.sil`
    明确：
    `Repo.handle`
    类型是
    `@convention(method) @async (@in_guaranteed any P, @guaranteed String, @in_guaranteed Asset, Repo) -> @error E`
  - `sample.s`
    明确：
    `Repo.handle`
    entry
    会把第 5 个
    machine argument
    存入状态：
    `str x4, [x22, #216]`
  - 对应 throw path：
    先构造
    `E.Ctx`
    / `E`，
    再经
    `_swift_willThrowTyped`
    ，最后把
    整个
    `E`
    payload
    拷回
    该错误槽
    (`str x13/x12/x11/x10/x8`)
  - `Repo.helper`
    也同型：
    组装
    `E`
    后，
    `swift_willThrowTyped`
    再把结果写回
    entry 传入的
    error storage
- 结论：
  - 这条本机 ABI
    对照与
    `handleLLMAdapter`
    的
    `STR X4, [X22,#0x7D8]`
    +
    多个失败路径
    取回
    `[7D8]`
    再配
    `InferenceError`
    witness
    写值
    的模式
    高度同构
  - 因而
    `[7D8]`
    作为
    typed-throws
    `InferenceError`
    storage
    的假设
    从
    “高概率”
    进一步提升为
    “有 machine-local
    ABI 对照支撑”
- 下一步：
  - 继续把
    `_1400`
    还原到具体 imported symbol
  - 继续确认
    `[7D0]`
    是否在这些 local helper
    里扮演
    `self`
    的隐藏保存槽
2026-06-16 19:47:27 +0800
- 目标：
  - 用
    nested local async helper
    的本机 ABI
    对照继续收紧
    `[7D0]`
    的语义
- 动作：
  - 新增
    `/tmp/swiftabi.8d32iQ/sample_nested.swift`
    ，构造：
    `Repo.outer(flag:)`
    内部的
    `localHandle(_ p:id:asset:) async throws(E)`
  - 生成：
    - `/tmp/swiftabi.8d32iQ/sample_nested.s`
    - `/tmp/swiftabi.8d32iQ/sample_nested.sil`
  - 对照 local helper
    的
    SIL
    与 arm64 entry
- 证据：
  - `sample_nested.sil`
    明确：
    `localHandle`
    是
    `@convention(thin) @async (@in_guaranteed any P, @guaranteed String, @in_guaranteed Asset, @guaranteed String) -> @error E`
    其中最后一个显式参数
    是 closure capture
    `cap`
  - `sample_nested.s`
    entry
    明确：
    - `x6`
      被存到
      state
      (`str x6, [x22, #152]`)
      作为 typed error storage
    - `x5`
      被存到
      `[x22,#112]/[x22,#120]`
      作为 capture
      `cap`
  - 这说明在
    local async helper
    场景下，
    “显式参数之后还有一个
    hidden capture/self
    槽”
    本身是正常 lowering，
    不需要优先解释成
    continuation context
- 结论：
  - `[7D8]`
    作为 typed-throws
    `InferenceError`
    storage
    的判断继续加强
  - `[7D0]`
    当前更像
    capture/self
    侧的隐藏保存槽，
    而不是
    continuation context；
    后续应朝
    `self`
    /
    capture record
    方向继续验证
- 下一步：
  - 继续把
    `_1400`
    还原到具体 imported symbol
  - 继续对照
    `handleLLMModel`
    /
    `handleDraftModel`
    /
    `handleLLMAdapterMetadataOverride`
    的 local helper
    wrapper，
    看
    `[7D0]`
    是否统一落在
    capture/self
    一侧
2026-06-16 20:04:16 +0800
- 目标：
  - 用
    “捕获 self”
    的本机 local helper
    对照
    +
    目标二进制横向 wrapper
    对照，
    继续收紧
    `[7D0]`
- 动作：
  - 新增
    `/tmp/swiftabi.8d32iQ/sample_capture_self.swift`
    ，构造：
    local async helper
    同时捕获
    `cap`
    与
    `self.seed`
  - 生成：
    - `/tmp/swiftabi.8d32iQ/sample_capture_self.s`
    - `/tmp/swiftabi.8d32iQ/sample_capture_self.sil`
  - 横向检查目标 wrapper：
    - `handleLLMModel`
      `0x2750f9808`
    - `handleDraftModel`
      `0x275107674`
    - `handleLLMAdapterMetadataOverride`
      `0x2750fcf38`
- 证据：
  - `sample_capture_self.sil`
    明确：
    `localHandle`
    是
    `@convention(thin) @async (@in_guaranteed any P, @guaranteed String, @in_guaranteed Asset, @guaranteed String, @guaranteed Repo) -> @error E`
    即：
    显式参数后面
    继续追加
    `cap`
    与
    `self`
    两个 capture
  - `sample_capture_self.s`
    对应 entry
    明确：
    - `x6`
      是 typed error storage
    - `x5`
      / `x4`
      是 capture
      family
  - 目标二进制横向 wrapper
    也同型：
    - `handleLLMModel`
      wrapper
      (`0x2750f9808`)
      只有
      `X0/X1/X20`
      三槽
    - `handleDraftModel`
      wrapper
      (`0x275107674`)
      是
      `X0..X5`
      顺排显式参数
      +
      `X20`
      隐藏槽
    - `handleLLMAdapterMetadataOverride`
      wrapper
      (`0x2750fcf38`)
      也是
      `X0..X4`
      +
      `X20`
      隐藏槽
- 结论：
  - `[7D0]`
    继续朝
    capture/self
    隐藏保存槽
    收敛
  - 现在最需要继续锁死的，
    已经不是
    `[7D0]`
    的大方向，
    而是
    `_1400`
    究竟在构造
    `InferenceError`
    本体
    还是只写
    `InferenceError.Context`
- 下一步：
  - 继续恢复
    `_1400`
    的真实链接级身份；
    当前优先验证它是否其实是
    模块内生成的
    `swift_willThrowTyped`
    风格 helper
  - 继续补
    `handleTokenizer`
    /
    `handleImageTokenizer`
    的 wrapper
    看
    `X20`
    是否仍统一落在
    capture/self
    一侧
2026-06-16 20:24:33 +0800
- 目标：
  - 继续缩小
    `_1400`
    的真实身份，
    并补
    tokenizer
    两条 helper
    的失败路径
- 动作：
  - 用
    `otool -Iv`
    读取
    `__auth_stubs`
    间接符号表，
    确认
    `0x275218a38`
    落在
    `__TEXT,__auth_stubs`
    内
  - 继续补查：
    - `handleTokenizer`
      失败路径
      `0x2750fcbb4`-
      `0x2750fcbe0`
    - `handleImageTokenizer`
      失败路径
      `0x275106640`-
      `0x275106670`
- 证据：
  - `nm -m`
    已确认：
    `TokenGenerationInference`
    自身导入了
    `_swift_willThrowTypedImpl`
    ，但没有直接导入
    `swift_willThrowTyped`
    顶层包装层
  - `handleTokenizer`
    与
    `handleImageTokenizer`
    的失败路径
    都和
    `handleLLMAdapter`
    /
    `handleLLMModel`
    /
    `handleDraftModel`
    一样，
    先装
    `InferenceError`
    metadata / witness，
    再走
    `_1400`
  - 这些调用点都没有传入
    业务字符串 /
    code /
    userInfo
    等上下文；
    所以
    `_1400`
    不像
    `InferenceError`
    case constructor
- 结论：
  - `_1400`
    当前更像
    模块内生成的
    `swift_willThrowTyped`
    风格 helper，
    负责把已经构造好的
    typed error
    写回 error storage
  - 当前主线剩余的精细问题是：
    它到底是
    `swift_willThrowTyped`
    的薄包装，
    还是在此之上还做了
    一层
    `InferenceError`
    witness / metadata
    绑定
- 下一步：
  - 继续从
    `__auth_stubs`
    /
    `__auth_got`
    /
    相关 callsite
    反推出
    `_1400`
    的精确链接身份
  - 若仍卡住，
    就转去
    `ModelManagerServices`
    本体里找
    `InferenceError`
    typed-throws
    辅助层的同型代码
2026-06-16 20:50:40 +0800
- 目标：
  - 继续把
    `_1400`
    的身份从
    “高概率 typed-throws helper”
    推到更稳的链接层结论
- 动作：
  - 用脚本直接解析
    `TokenGenerationInference`
    Mach-O：
    - `__TEXT,__auth_stubs`
    - `LC_SYMTAB`
    - `LC_DYSYMTAB`
    - indirect symbol table
  - 确认
    `0x275218a38`
    位于
    `__auth_stubs`
    第
    `1402`
    项
  - 打开
    `ModelManagerServices`
    新 IDA 会话
    `modelmanagerservices_arm64e`
- 证据：
  - 解析结果显示：
    `0x275218a38`
    的 indirect symbol index
    仍指回
    `_$s24TokenGenerationInference16DraftingBehavior...TW`
    这一类占位符；
    说明从当前 extracted Mach-O
    的 indirect symbol table
    还原真实目标
    仍不可靠
  - `TokenGenerationInference`
    自身只显式导入
    `_swift_willThrowTypedImpl`
    ，没有直接导入
    `swift_willThrowTyped`
  - `ModelManagerServices`
    本体也同样只显式导入
    `_swift_willThrowTypedImpl`
  - 再结合：
    - `handleLLMAdapter`
    - `handleLLMModel`
    - `handleDraftModel`
    - `handleTokenizer`
    - `handleImageTokenizer`
    这些失败路径
    对
    `_1400`
    的统一调用形状
- 结论：
  - 当前已经可以把
    `_1400`
    更明确地写成：
    模块内生成的
    typed-throws
    辅助包装层，
    位于
    `InferenceError`
    payload 已构造完成
    与
    `_swift_willThrowTypedImpl`
    之间
  - 目前缺的不是
    语义方向，
    而是
    “它在链接表里到底对应哪一个私有符号”
    这一级更细的名字
- 下一步：
  - 去
    `ModelManagerServices`
    本体里找
    `_swift_willThrowTypedImpl`
    附近的 wrapper
    call pattern，
    当成
    `_1400`
    的官方同型样本

## 2026-06-16 21:08:23 +0800

- 目标：
  - 用
    `ModelManagerServices`
    本体里的
    官方 typed-throws
    wrapper
    给
    `TokenGenerationInference::_1400`
    补一层
    machine-local
    同型证据，
    把语义从
    “高概率”
    收紧到
    “同型确认”
- 动作：
  - 读取
    `ModelManagerServices`
    的
    `_swift_willThrowTyped`
    本体汇编
    (`0x25a724dd4`)
  - 抓取其两个真实调用点：
    - `0x25a74b3d0`
    - `0x25a74ba38`
  - 对照
    `/tmp/swiftabi.8d32iQ/`
    下的
    `sample.s`
    /
    `sample_nested.s`
    /
    `sample_capture_self.s`
    调用形状
  - 再对照
    `TokenGenerationInference`
    中
    `_1400`
    的多个失败路径片段：
    - `0x275143330`
    - `0x27517d204`
    - `0x2750fcbf4`
- 证据：
  - `ModelManagerServices::_swift_willThrowTyped`
    是薄 3 参 wrapper：
    - `X0 = error storage`
    - `X1 = payload`
    - `X2 = Error witness`
    - 仅做一次
      OS/version gate
      后
      直跳
      `_swift_willThrowTypedImpl`
  - 本机 Swift 最小样本的
    `_swift_willThrowTyped`
    调用形状完全一致
  - `TokenGenerationInference`
    的 `_1400`
    callsite
    统一表现为：
    1. 先
       `bl _$s20ModelManagerServices14InferenceErrorOACs0E0AAWlTm`
       取
       `InferenceError : Error`
       witness accessor
    2. 再把
       `X0 = [7D8]`-family
       error storage，
       `X1 = 已构造 payload addr`，
       `X2 = witness`
       送入
       `_1400`
  - `TokenGenerationInference`
    自身仍只显式导入
    `_swift_willThrowTypedImpl`
    ，未直接导入
    `_swift_willThrowTyped`
- 结论：
  - `_1400`
    现在可以从
    “高概率 typed-throws helper”
    升级为：
    与
    `ModelManagerServices::_swift_willThrowTyped`
    同型的
    模块内
    typed-throws
    包装层
  - 当前未解决的只是
    `_1400`
    更细的私有符号名，
    不是它的 ABI / 语义方向
- 下一步：
  - 若继续深挖，
    目标改成恢复
    `_1400`
    更细的私有符号身份
  - 或横向补齐
    `handleTokenizer`
    /
    `handleImageTokenizer`
    /
    `handleLLMAdapterMetadataOverride`
    的
    `[7D8]`
    /
    `[7D0]`
    同型覆盖

## 2026-06-16 21:26:20 +0800

- 目标：
  - 继续压缩
    `_1400`
    的真实身份，
    不是重复证明
    typed-throws 语义，
    而是确认它所在
    `__TEXT,__auth_stubs`
    页簇和 stub 索引
- 动作：
  - 读取
    `TokenGenerationInference`
    的
    `__TEXT,__auth_stubs`
    以及 segment layout
  - 用脚本计算
    `_1400`
    对应 stub index
    和 `adrp/add`
    页级目标
  - 取
    `0x275218508`
    /
    `0x275218878`
    /
    `0x275218a28`
    /
    `0x275218a38`
    /
    `0x275218a48`
    做邻位对照
  - 直接解析
    `LC_SYMTAB`
    /
    `LC_DYSYMTAB`
    里的
    indirect symbol table
    index `1401-1403`
- 证据：
  - `_1400`
    对应的 stub 地址是
    `0x275218a38`
    ，stub index 为
    `1402`
  - 该 stub 的
    `adrp/add`
    解析结果为：
    - `x17 -> 0x29a246000`
    - `add #0x270`
    - 最终指向
      `0x29a246270`
  - 同页簇里的
    `0x29a246208` /
    `0x29a246270` /
    `0x29a246358`
    等槽位在当前 extracted Mach-O
    的旧间接符号表里
    全都塌成同一个占位符号：
    `_$s24TokenGenerationInference16DraftingBehaviorV10CodingKeys...TW`
  - `dyld_info -imports`
    能读到该二进制，
    但 `-fixups` /
    `-fixup_chain_details`
    对这个 extracted 文件
    不给足够细的目标信息
- 结论：
  - `_1400`
    继续被压实为：
    一簇
    `CodingKeys...TW`
    占位 stub 里的第
    1402 个槽位
  - 继续靠当前
    extracted Mach-O 的
    旧 indirect symbol table
    抠更细私有符号名
    已进入低收益区
  - 更合理的下一步是：
    1. 继续做同页簇的
       行为归类，
       看哪些 stub 真正和
       `InferenceError` /
       `willThrowTyped` 同类
    2. 或改追
       `__AUTH_CONST/__auth_got`
       /
       fixup 链，
       看能否得到更细的
       import family
- 下一步：
  - 停止在旧间接符号表里
    继续重复抠 `_1400`
    的名字
  - 改转向：
    - 同页簇行为归类
    - 或 fixup 链级别的
      import family 追踪

## 2026-06-16 21:51:40 +0800

- 目标：
  - 把
    `0x275218a28 / 0x275218a38 / 0x275218a48`
    这三个相邻 stub
    从“同页簇”
    进一步拆成不同职责，
    避免把 `_1400`
    和邻位误归成同类
- 动作：
  - 抓取
    `a28/a38/a48`
    的 xref 调用族
  - 用 IDA 反编译：
    - `specialized Array<Float>.sampleRandomElement(...)`
    - `TGICAPIWrapper.makeSession`
    - `AppAssetManager.createCacheDirectoryIfNeeded`
    - `OnDeviceInferenceContextFactory.createInferenceContext`
  - 另外用本机最小
    untyped `throws`
    样本
    (`/tmp/swiftthrow.Yvf6HP/sample_throw.s`)
    对照
    `_swift_willThrow`
    的 call shape
- 证据：
  - `1401`
    (`0x275218a48`)
    在
    `specialized Array<Float>.sampleRandomElement(...)`
    中
    明确被当成
    多参数数值 helper
    使用，
    不是错误路径
  - `1399`
    (`0x275218a28`)
    的调用族
    多出现在普通
    `throws`
    路径，
    调用前只需要
    一个普通 `Error`
    object / existential
    ，之后直接抛出返回
  - 本机最小
    untyped `throws`
    样本里，
    `_swift_willThrow`
    也是一参形状：
    - 先 `swift_allocError`
    - 再 `bl _swift_willThrow`
  - `1400`
    (`0x275218a38`)
    则继续保持
    `(storage, payload, witness)`
    三参 typed-throws
    形状
- 结论：
  - 同页簇里的这几个 stub
    不是同类 helper：
    - `1399`
      更像
      `_swift_willThrow`
      家族的
      untyped throw helper
    - `1400`
      是 typed-throws helper
    - `1401`
      已证实是
      非错误数值 helper
  - 所以之后不能再拿
    `1401`
    作为 `_1400`
    的同类旁证
- 下一步：
  - 若继续追 throw-family，
    只围绕
    `1399`
    /
    `1400`
    两个位点
    做更细分工
  - 若继续追名字，
    也应只对这两个位点
    找更细 target family

## 2026-06-16 21:59:16 +0800

- 目标：
  - 验证能否从
    `LC_DYLD_CHAINED_FIXUPS`
    直接恢复
    `1399/1400`
    的真实 import 名字
- 动作：
  - 手工枚举
    `TokenGenerationInference`
    /
    `ModelManagerServices`
    的
    load commands
  - 对照
    `mach-o/fixup-chains.h`
    确认
    `LC_DYLD_CHAINED_FIXUPS`
    常量和 header 结构
- 证据：
  - `TokenGenerationInference`
    当前 extracted Mach-O
    里
    没有
    `LC_DYLD_CHAINED_FIXUPS`
    (`0x80000034`)
  - 仅有
    `LC_DYLD_EXPORTS_TRIE`
    (`0x80000033`)
    ，且
    `dataoff=0`
    `datasize=0`
  - `ModelManagerServices`
    的 extracted 样本
    也是同样状态
- 结论：
  - 在当前
    `/Volumes/2T/dsc_arm64e_extract/...`
    样本上，
    chained fixups
    元数据已经缺失
  - 所以
    `dyld_info -fixups`
    /
    `-fixup_chain_details`
    读不出有用目标
    不是工具问题，
    而是样本本身不带这部分数据
- 下一步：
  - 不要再在这份
    extracted Mach-O
    上重复尝试
    fixups 解析
  - 继续主线应回到：
    - `1399/1400`
      的行为与 ABI 分层
    - 或换原始未丢
      chained-fixups
      元数据的映像

## 2026-06-16 22:11:04 +0800

- 目标：
  - 评估是否能直接转到
    shared-cache
    本体视角继续追
    `1399/1400`
    的真实 import 名字
- 动作：
  - 检查真实系统路径下
    `TokenGenerationInference`
    /
    `ModelManagerServices`
    的
    `dyld_info -load_commands`
  - 查看
    `dyld_shared_cache_arm64e.map`
    里的 image 与 segment range
  - 检查
    `/System/Volumes/Preboot/.../dyld_shared_cache_arm64e*`
    分片布局
- 证据：
  - 系统路径下的
    `dyld_info -load_commands`
    仍只稳定暴露：
    - 空的
      `LC_DYLD_EXPORTS_TRIE`
    - `LC_SYMTAB`
    - `LC_DYSYMTAB`
  - cache map
    只能稳定给出
    image 名称与 VM range
  - `_1400`
    所在 stub slot
    `0x29a246270`
    不直接落在
    image 自身的
    Mach-O segment
    range 里
  - `dyld_shared_cache_arm64e`
    主文件本体只有
    560KB，
    真正 payload
    分散在
    `.01/.05/.09/...`
    与
    `.dylddata/.dyldlinkedit`
    分片中
- 结论：
  - 继续追 shared-cache
    这条线的当前 blocker
    已经变成：
    缺少 dyld subcache
    header / mapping
    结构定义，
    无法把
    shared-cache vmaddr
    稳定映射回
    分片 file offset
  - 在没有这个结构定义前，
    不应硬做
    `0x29a246270`
    的 cache 级解引用
- 下一步：
  - 若继续 shared-cache
    主线，
    先补
    subcache header /
    mapping format
    的结构定义
  - 否则回到
    `1399/1400`
    的行为与 ABI
    分层主线

## 2026-06-16 22:36:56 +0800

- 目标：
  - 收紧
    `_1400`
    是否可能直接等于
    imported
    `_swift_willThrowTypedImpl`
- 动作：
  - 读取
    `TokenGenerationInference`
    /
    `ModelManagerServices`
    的导入符号
  - 对照本机最小
    typed-throws
    样本
    `/tmp/swiftabi.8d32iQ/sample.s`
- 证据：
  - `TokenGenerationInference`
    明确导入：
    - `_swift_willThrowTypedImpl`
    - `Swift._stdlib_isOSVersionAtLeastOrVariantVersionAtLeast(...)`
  - 本机最小
    typed-throws
    样本里，
    `_swift_willThrowTyped`
    的结构是：
    - 先做
      stdlib OS gate
    - 再进入
      `_swift_willThrowTypedImpl`
  - `_1400`
    的外部 callsite
    仍稳定表现为
    `(storage,payload,witness)`
    三参入口
- 结论：
  - `_1400`
    当前更像
    “模块内
    typed-throws
    gate/wrapper，
    最终下沉到
    `_swift_willThrowTypedImpl`”
  - 不应在当前证据下
    直接把它写成
    imported impl 本体
- 下一步：
  - 后续若继续收紧
    `_1400`
    的名字，
    也应围绕
    “wrapper 名字 / gate 名字”
    这一级，
    不要默认把目标设成
    `_swift_willThrowTypedImpl`

## 2026-06-16 22:42:54 +0800

- 目标：
  - 收紧
    `1399`
    是否可直接等同于
    imported
    `_swift_willThrow`
- 动作：
  - 检查
    `TokenGenerationInference`
    的导入表
  - 对照
    `1399`
    的真实调用族
  - 再对照本机最小
    untyped `throws`
    样本
    `/tmp/swiftthrow.Yvf6HP/sample_throw.s`
- 证据：
  - `TokenGenerationInference`
    导入表里
    没有
    `_swift_willThrow`
    ，只有：
    - `_swift_allocError`
    - `_swift_errorRetain`
    - `_swift_errorRelease`
    - `_swift_willThrowTypedImpl`
  - `1399`
    的调用点
    仍统一表现成：
    - 先构造普通
      `Error`
      object / existential
    - 再单参抛出
  - 本机最小
    untyped `throws`
    样本里，
    标准路径确实是
    `swift_allocError`
    后
    `bl _swift_willThrow`
- 结论：
  - `1399`
    当前更稳的写法
    不是
    “direct imported
    `_swift_willThrow`”
    而是：
    “模块内
    untyped throw
    wrapper，
    最终下沉到
    Swift runtime”
  - 这样与
    `1400`
    的
    “模块内
    typed-throws
    gate/wrapper”
    解释是对称的
- 下一步：
  - 后续若继续追名字，
    以
    `1399/1400`
    的 wrapper 层命名
    为目标，
    不再把目标直接设成
    runtime imported symbol

## 2026-06-16 22:50:17 +0800

- 目标：
  - 补齐同页簇里
    `1402/1403`
    的职责，
    确认 throw-family
    的边界是不是只到
    `1399/1400`
- 动作：
  - 抓取
    `0x275218a58`
    /
    `0x275218a68`
    的调用点
  - 对照
    `sampleRandomElement`
    一类数值路径
  - 补查
    `Accelerate`
    导入表
    (`vDSP_vsadd/vDSP_vsdiv/vDSP_sve/vDSP_maxv/_vvexpf`)
- 证据：
  - `1402`
    /
    `1403`
    的调用点
    都集中在
    `sampleRandomElement`
    一类数值/vector
    处理路径
  - `TokenGenerationInference`
    本身也明确导入了：
    - `_vDSP_maxv`
    - `_vDSP_sve`
    - `_vDSP_vsadd`
    - `_vDSP_vsdiv`
    - `_vvexpf`
- 结论：
  - `1402/1403`
    也应归入
    非错误数值 helper
  - 所以当前这整页簇里，
    throw-family
    只稳定覆盖：
    - `1399`
    - `1400`
  - `1401/1402/1403`
    不再作为 `_1400`
    的任何同类旁证
- 下一步：
  - 后续继续收紧名字时，
    主线只保留
    `1399`
    /
    `1400`
    两个位点

## 2026-06-16 23:00:14 +0800

- 目标：
  - 复核
    `1399`
    是否真的不能和
    imported
    `_swift_willThrow`
    直接相关
- 动作：
  - 用
    `nm -m`
    重新检查
    `TokenGenerationInference`
    /
    `ModelManagerServices`
    的导入事实
- 证据：
  - `TokenGenerationInference`
    确实直接导入：
    - `_swift_willThrow`
    - `_swift_willThrowTypedImpl`
  - `ModelManagerServices`
    也导入：
    - `_swift_willThrow`
    - `_swift_willThrowTypedImpl`
    且本地定义了
    `_swift_willThrowTyped`
- 结论：
  - 前一轮
    “TGI 导入表里没有
    `_swift_willThrow`”
    的说法是错的，
    以
    `nm -m`
    为准
  - 当前关于
    `1399`
    的最稳写法应修正为：
    “与 imported
    `_swift_willThrow`
    同家族的
    untyped throw
    入口”
  - 但在没有更细
    fixup / stub
    恢复前，
    仍不应把它过早写死成
    “一定就是 direct
    `_swift_willThrow`
    跳板”
- 下一步：
  - 继续主线时，
    对 `1399`
    的收紧目标改成：
    “到底是
    direct imported stub
    还是模块内薄 wrapper”

## 2026-06-16 23:19:50 +0800

- 目标：
  - 看 `1397/1398`
    是否能把
    `1399/1400`
    串成一套更完整的
    编译器错误模板
- 动作：
  - 抓取
    `0x275218a08`
    /
    `0x275218a18`
    /
    `0x275218458`
    的调用族
  - 计算其 slot 位置
  - 对照已有的
    `1399/1400`
    结论
- 证据：
  - `1306`
    (`0x275218458`)
    的调用点
    大量表现为：
    - `mov x2, #0`
    - `mov w3, #0`
    - `bl 1306`
    - 然后立即消费
      `x0/x1`
  - `1397`
    (`0x275218a08`)
    当前已见到的调用点
    更像对
    某个已分配对象
    / slot
    再做一小步写入
  - `1398`
    (`0x275218a18`)
    目前样本不足，
    但 slot 上紧邻
    `1397`
- 结论：
  - 当前可以提出一个
    更结构化的
    working model：
    - `1306`
      先产出
      `(error, payload-slot)`
      二元组
    - `1397/1398`
      做轻量初始化
    - `1399`
      收尾到
      untyped throw
    - `1400`
      收尾到
      typed throw
  - 这还不是最终证实，
    但已经比
    “单个孤立 stub”
    更接近编译器模板视角
- 下一步：
  - 优先补
    `1397/1398`
    的更细调用形状 /
    反编译证据，
    看是否能把这套模板
    从 working model
    升到事实层

## 2026-06-16 23:47:46 +0800

- 目标：
  - 收紧
    `1397/1398`
    的真实语义，
    判断它们是否真属于
    `1306 -> 1399/1400`
    错误模板
- 动作：
  - 在
    `TokenGenerationInference`
    里补抓：
    - `0x2750c1278`
    - `0x2750c13e4`
    - `0x2751682f0`
    的反编译与汇编
  - 同时核对
    image imports
    里的
    `_swift_weakInit`
    /
    `_swift_weakLoadStrong`
- 证据：
  - `1398`
    (`0x275218a18`)
    在
    `0x275168340`
    的直接调用形状是：
    - `ADD X0, X20, #0x10`
    - `BL 1398`
    - `CBZ X0`
    这与
    `swift_weakLoadStrong`
    语义高度一致
  - `1397`
    (`0x275218a08`)
    在
    `0x2750c12bc`
    /
    `0x2750c15bc`
    的直接调用形状是：
    - `ADD X0, Xobj, #0x18`
    - `MOV X1, #0`
      或
      `MOV X1, X25`
    - `BL 1397`
    这与
    `swift_weakInit`
    语义高度一致
  - 同一 image
    已确认导入：
    - `_swift_weakInit`
    - `_swift_weakLoadStrong`
    - `_swift_weakAssign`
    - `_swift_weakDestroy`
- 结论：
  - `1397/1398`
    不是
    error-template
    helper；
    它们更像
    weak-reference
    生命周期 helper
  - 因而
    23:19
    提出的
    `1306 + 1397/1398 + 1399/1400`
    整体错误模板
    现在被部分证伪：
    - `1399/1400`
      仍可保留在
      throw-family
    - `1397/1398`
      必须拆出去
  - 当前真正未决的
    error-chain
    收紧点应改成：
    `1306 -> 293 -> 1399`
    与
    `1400`
- 下一步：
  - 先补
    `1395`
    的非 nil
    样本，
    把
    `weakAssign`
    收到事实层
  - 然后回到
    `1306/293/1399`
    的寄存器形状，
    收紧
    allocError /
    payload /
    willThrow
    链条

## 2026-06-16 23:52:20 +0800

- 目标：
  - 继续拆开
    weak helper
    簇内部语义，
    避免把
    `1316`
    也错归进去
- 动作：
  - 分析
    `1395`
    (`0x2752189e8`)
    的 xref
    与直接调用形状
  - 统计
    `1316`
    (`0x2752184f8`)
    的 xref
    覆盖范围
- 证据：
  - `1395`
    仅见 3 个直接调用点，
    其中关键样本
    `0x2750c15f0 -> 0x2750c15f8`
    形状是：
    - `ADD X0, X27, #0x18`
    - `MOV X1, X25`
    - `BL 1395`
    与
    `swift_weakAssign`
    高度一致
  - `1395`
    在
    `0x2750c12f8 -> 0x2750c1300`
    也有
    nil
    赋值形状：
    - `ADD X0, X23, #0x18`
    - `MOV X1, #0`
  - `1316`
    当前 xref
    已超过
    500
    处，
    覆盖
    dictionary /
    decoder /
    asset /
    stream
    等大量路径，
    不像
    weak 专用 helper
- 结论：
  - `1395`
    当前最强语义
    已收紧到
    `weakAssign`
  - `1395/1397/1398`
    可以暂时视为
    同一 weak-reference
    生命周期簇
  - `1316`
    应从该簇里拆出，
    作为通用
    address/copy/access
    helper 另看
- 下一步：
  - 再补
    `1395`
    的 1-2 个
    非 nil
    调用样本后，
    把
    `weakAssign`
    写成事实层
  - 主线回到
    `1306 -> 293 -> 1399`
    与
    `1400`
    的真正错误下沉链

## 2026-06-17 00:03:42 +0800

- 目标：
  - 收紧
    `1306 -> 1399`
    的真实 ABI，
    确认
    `1306`
    的双返回值
    到底代表什么
- 动作：
  - 对照
    `0x275097df8`
    /
    `0x27512ab80`
    /
    `0x2750d16a4`
    的汇编与反编译
  - 观察
    `1306`
    返回后
    `x0/x1`
    的去向
- 证据：
  - 在多个 throw 样本里，
    `1306`
    调用前参数稳定近似：
    - `x0 = 294/296`
      产出的值
    - `x1 = Error witness`
    - `x2 = 0`
    - `w3 = 0`
  - `1306`
    返回后，
    调用方稳定做：
    - 保存
      `x0`
      作为后续 throw handle
    - 保存
      `x1`
      作为待填充 slot
    - 用
      `x1`
      调某个
      metadata /
      value witness
      写入具体 payload
    - 再把
      `x0`
      送进
      `1399`
- 结论：
  - `1306`
    当前最稳的工作模型
    已收紧成：
    “为错误路径准备
    `(error handle, payload slot)`
    二元组”
  - 因而
    `1399`
    前面的真正链条
    可以先写成：
    `294/296 -> 1306 -> payload write -> 1399`
  - 但
    `1306`
    是否直达
    `_swift_allocError`
    仍未被本样本直接坐实
- 下一步：
  - 继续补
    `293`
    的真实调用语义
  - 看
    `294/296/293`
    里谁在构造
    message，
    谁在构造
    case/value，
    谁只是在
    bridge/box

## 2026-06-17 00:09:42 +0800

- 目标：
  - 判断
    `293`
    是否是
    `1306 -> 1399`
    链里的必经步骤
- 动作：
  - 对照
    `0x2751689e0`
    /
    `0x275165b70`
    /
    `0x275097df8`
    三类样本的
    汇编形状
- 证据：
  - 在
    `0x2751689e0`
    /
    `0x275165b70`
    一类样本里：
    - `bl 1306`
    - `mov x27/x25, x0`
    - `mov x8, x1`
    - `bl 293`
    - `bl 1399`
  - 但在
    `0x275097df8`
    一类样本里：
    - `bl 1306`
    - 保存
      `x0/x1`
    - 用
      `x1`
      直接走
      value-witness
      写 payload
    - 随后
      `bl 1399`
    中间并没有
    `293`
- 结论：
  - `293`
    不是所有
    untyped throw
    路径的必经步骤
  - 当前最稳的模型是：
    - 公共前段：
      `294/296 -> 1306`
    - 然后分叉成：
      1. `payload write -> 1399`
      2. `293 -> 1399`
  - `293`
    当前更像
    payload finalize /
    materialize
    helper，
    不是通用 message builder
- 下一步：
  - 继续找
    触发
    `293`
    与不触发
    `293`
    的分叉条件
  - 再判断
    `294/296`
    谁更偏
    message，
    谁更偏
    case/value

## 2026-06-17 00:09:42 +0800

- 目标：
  - 继续收紧
    `293`
    与
    `294/296`
    的职责边界
- 动作：
  - 复核
    `0x275097df8`
    /
    `0x2751689e0`
    /
    `0x275165b70`
    /
    `0x2751442a4`
    等样本的
    详细汇编
- 证据：
  - `0x275097df8`
    一类路径：
    - `bl 1306`
    - 保存
      `x0=handle`
      /
      `x1=slot`
    - 直接通过
      metadata / value-witness
      对
      `x1`
      写 payload
    - `bl 1399`
  - `0x2751689e0`
    /
    `0x275165b70`
    一类路径：
    - `bl 1306`
    - `mov x8, x1`
    - `bl 293`
    - `bl 1399`
  - 这说明
    `293`
    发生在
    error box
    已分配之后，
    更像
    slot materializer
- 结论：
  - `1306`
    当前更像
    真正的
    error-box
    allocation entry
  - `293`
    更像
    某些错误类型的
    专用 payload injector /
    materializer
  - `293`
    不是所有
    untyped throw
    路径共享步骤
  - `294/296`
    当前更像
    前置本地 payload /
    metadata
    构造段，
    但还没最终坐实
- 下一步：
  - 继续找
    `293`
    与
    direct payload write
    的分叉条件
  - 继续收紧
    `294/295/296/598`
    的分工

## 2026-06-17 00:16:00 +0800

- 目标：
  - 拆开
    `295/598`
    与
    `294/296`
    的职责边界
- 动作：
  - 分析
    `295`
    /
    `598`
    的 xref
    与典型调用形状
  - 对照
    `0x275102e64`
    /
    `0x275103104`
    /
    `0x275165b24`
    等样本
- 证据：
  - `598(0)`
    在多条错误路径里都紧贴
    `1306`
    /
    `1400`
    出现，
    形状更像
    “先拿 concrete error type
    metadata，再配 witness
    进入下游 error runtime”
  - `295(0)`
    更常见于：
    - `bl 295(0)`
    - 读取返回类型大小
    - 栈上分配局部 buffer
    - 再调用
      `294`
      往里写值
- 结论：
  - `598`
    当前最像
    concrete error type
    metadata accessor
  - `295`
    当前最像
    local payload / local error value
    type metadata accessor
  - `294`
    则更像
    往该本地 value buffer
    写 message/string/payload
- 下一步：
  - 继续看
    `296`
    到底是
    full local error value
    helper
    还是
    与
    `598`
    平行的另一类
    metadata accessor

## 2026-06-17 00:28:10 +0800

- 目标：
  - 把
    `296`
    和
    `598`
    明确区分开
- 动作：
  - 对照
    `0x275097ddc`
    的 untyped 路径
    与
    `0x27510327c`
    的 typed 路径
    看
    `296`
    /
    `598`
    返回值
    分别喂给谁
- 证据：
  - `0x275097ddc`
    中，
    `296(0)`
    返回值进入
    `X21`，
    随后被拿去取
    type metadata 的
    `+0x68`
    槽位，
    并配合
    `payload slot`
    做 value-witness
    写入，
    然后
    `1399`
  - `0x27510327c`
    中，
    真正进入
    `1400`
    的
    `x1`
    来自
    `598(0)`，
    而不是
    `296`
- 结论：
  - `598`
    依旧最像
    concrete error type
    metadata accessor
  - `296`
    不应再简单写成
    “payload aggregate helper”；
    它至少和
    `TokenGenerationError`
    的 concrete type /
    conformance
    强绑定
- 下一步：
  - 继续找
    `296`
    到底是
    `TokenGenerationError`
    concrete/local type helper
    还是
    更通用的
    untyped error-side
    metadata accessor
  - 再回头看
    `294`
    是否始终只做
    本地 value buffer
    写入

## 2026-06-17 00:33:47 +0800

- 目标：
  - 用最小证据链
    判断
    `296`
    是否直接绑定
    `TokenGenerationError`
    conformance
- 动作：
  - 分析
    `0x275098a48`
    (`TokenGenerationError`
    witness accessor)
    的完整汇编与反编译
- 证据：
  - 该 witness accessor
    在 cache miss
    时执行：
    - `bl 296`
    - `mov x1, x0`
    - `mov x0, witness descriptor`
    - `bl 1358`
    然后把结果
    存进
    `TokenGenerationError`
    的 witness cache
- 结论：
  - `296`
    至少直接参与
    `TokenGenerationError`
    conformance / witness
    的构建
  - 所以当前不能再把
    `296`
    简单写成
    “纯 payload aggregate helper”
  - 当前更稳的说法是：
    `296`
    是
    `TokenGenerationError`
    concrete/local type helper
- 下一步：
  - 继续找
    `296`
    在非
    `TokenGenerationError`
    路径里
    是否也保持同样角色

## 2026-06-17 00:57:41 +0800

- 目标：
  - 给
    `296 ~= TokenGenerationError`
    再补一条
    非调用形状的旁证
- 动作：
  - 用
    `nm -m`
    直接核对
    `TokenGenerationErrorOMa`
    /
    `InferenceErrorOMa`
    的导入情况
  - 对照本地
    witness accessor
    的控制流
- 证据：
  - 当前 image
    直接 import：
    - `_$s15TokenGeneration0aB5ErrorOMa`
    - `_$s20ModelManagerServices14InferenceErrorOMa`
  - 本地 witness accessor：
    - `TokenGenerationError`
      `0x275098a48`
      走
      `bl 296 -> bl 1358`
    - `InferenceError`
      `0x275145e80`
      /
      `0x275177864`
      走
      `a2(255) -> bl 1358`
- 结论：
  - `296`
    与
    `TokenGenerationError`
    witness/conformance
    的绑定已经有
    Mach-O + control-flow
    双重旁证
  - 当前剩余未决点
    已进一步收窄成：
    `296`
    是否只服务
    `TokenGenerationError`
    一家，
    还是还被别的
    untyped error family
    复用

## 2026-06-17 01:32:20 +0800

- 目标：
  - 判断
    `296`
    是否真的只围绕
    `TokenGenerationError`
    使用
- 动作：
  - 抽样
    `296`
    的几类非 witness
    调用点：
    - `ClassificationSampling`
    - `NucleusSampling`
    - `TopK`
    - `handleCustom...`
    - `ContextFactory`
- 证据：
  - 抽样路径继续集中在
    本地参数校验 /
    配置校验 /
    untyped throw
    侧
  - 这些路径最终都回到
    `TokenGenerationError`
    witness/conformance
    相关链条
  - 当前没有看到
    `296`
    像
    `598`
    一样
    明确跨到
    `InferenceError`
    一侧
- 结论：
  - `296`
    当前更像
    `TokenGenerationError`
    专属或近专属的
    concrete/local type helper
  - “被别的 untyped error family
    广泛复用”
    目前没有证据支持
- 下一步：
  - 继续找
    `296`
    的剩余少量调用点里
    是否存在
    非
    `TokenGenerationError`
    家族的反例

## 2026-06-17 01:51:28 +0800

- 目标：
  - 验证
    `296`
    的“反例”调用点，
    并确认
    `296`
    是否真的跨到了
    `InferenceError`
    一侧
- 动作：
  - 继续抽样
    `296`
    的可疑 xref：
    - `KVLRUCache.insert`
      `0x2751d77d0`
      /
      `0x2751d78f8`
    - `AppAssetManager.copyAssetsIfNeeded`
      `0x2750d50fc`
    - `ModelMetadata.from`
      `0x2750e6a88`
    - `supportedTools`
      `0x2751441d8`
    - `countTokens`
      `0x275157824`
    - `requestStream`
      `0x27516d85c`
  - 反汇编 /
    反编译：
    - `296`
      `0x275214538`
    - `1306`
      `0x275218458`
    - `1358`
      `0x275218798`
    - `InferenceError`
      lazy witness helper
      `0x275145e80`
      /
      `0x275177864`
- 证据：
  - `296`
    /
    `1306`
    /
    `1358`
    当前都只是
    `__auth_stubs`
    跳板：
    - `296 -> MEMORY[0x29A219548]`
    - `1306 -> MEMORY[0x29A245CC0]`
    - `1358 -> MEMORY[0x29A246010]`
  - `0x275098a48`
    (`TokenGenerationError`
    witness accessor)
    仍然是最干净的直证：
    - `bl 296`
    - `MOV X1, X0`
    - `MOV X0, 0x28F664FF0`
    - `bl 1358`
  - 但新的
    `296`
    路径里，
    `0x275157824`
    和
    `0x27516d85c`
    都出现了：
    - `bl 296`
    - `ADRL X0, _$s15TokenGeneration0aB5ErrorOACs0C0AAWL`
    - `X1 = 0x28F664FE8`
    - `X2 = 0x28F664FF0`
    - `BL 0x275177864`
    - `BL 1306`
  - `0x275177864`
    /
    `0x275145e80`
    的机器体本身是同一类
    caller-parameterized
    lazy witness builder：
    - `result = *a1`
    - `if !result { v6 = a2(255); result = 1358(a3, v6); atomic_store(result, a1); }`
  - 所以，
    虽然 IDA
    把
    `0x275177864`
    命名成
    `InferenceError...WlTm_0`，
    但在
    `296`
    路径里，
    传进去的
    `a1`
    实际是
    `TokenGenerationError`
    的 cache slot，
    不是
    `InferenceError`
    cache slot
- 结论：
  - 之前那句
    “当前没有看到
    `296`
    跨到
    `InferenceError`
    一侧”
    说得太死，
    需要修正
  - 更准确的结论是：
    - `296`
      路径
      确实会复用
      一个被命名成
      `InferenceError`
      witness accessor
      的 helper 机器体
    - 但这还不能说明
      error family
      真切到
      `InferenceError`
      了；
      从实参看，
      它在这些路径里
      仍然落在
      `TokenGenerationError`
      cache/witness
      一侧
    - `0x275145e80`
      /
      `0x275177864`
      更像
      通用 lazy witness helper
      或
      ICF/共用 thunk，
      不能只按符号名断类型
  - 因而当前主线应从
    “继续找
    `296`
    反例”
    收紧成：
    1.
    确认
    `0x28F664FE8`
    这条 callback
    到底是什么
    2.
    继续拆
    `293`
    为什么只在
    一部分
    `1306 -> 1399`
    路径里出现
- 下一步：
  - 对比
    `293`
    路径
    (`0x2751441d8`,
    `0x2751689ec`,
    `0x275165b7c`)
    与
    direct payload write
    路径
    (`0x2750e6a88`,
    `0x2751d77d0`)
  - 判断
    `293`
    是
    payload project /
    slot materialize /
    finalize
    中的哪一步

## 2026-06-17 02:28:19 +0800

- 目标：
  - 继续收紧
    `293`
    身份，
    并判断
    extracted
    `TokenGenerationInference`
    是否还能从
    `__auth_got`
    直接恢复
    stub
    真实目标
- 动作：
  - 直接读取
    `TokenGenerationInference`
    `__AUTH_CONST,__auth_got`
    中
    `293/296/598/1306/1358/1399/1400`
    对应槽位
  - 继续对比
    `293`
    路径：
    - `supportedTools`
    - `compileAdapter`
    - `requestStream`
    - `convertToInferenceError`
  - 新开
    `TokenGeneration.framework`
    session，
    直接查看
    `TokenGenerationError.toInferenceError`
    `0x274de6890`
- 证据：
  - `TokenGenerationInference`
    中以下
    `__auth_got`
    槽位当前值全为
    `0`：
    - `0x29e25d4e8`
      (`293`)
    - `0x29e25d500`
      (`296`)
    - `0x29e25de70`
      (`598`)
    - `0x29e25f490`
      (`1306`)
    - `0x29e25f630`
      (`1358`)
    - `0x29e25f778`
      (`1399`)
    - `0x29e25f780`
      (`1400`)
  - 因而这份
    extracted
    Mach-O
    的
    `__auth_got`
    不能直接给出
    真实导入绑定；
    `dyld_info -fixups`
    / `otool -s __auth_got`
    在当前样本上
    也不再值得继续深挖
  - `293`
    路径的寄存器形态继续稳定：
    - `1306`
      返回后
      `MOV X8, X1`
      / `BL 293`
      再
      `1399`
      的 throw 形态
      见
      `0x2751442a4`
      `0x275165798`
      `0x2751689ec`
  - 但
    `convertToInferenceError`
    `0x2750d0990`
    里，
    `293`
    不在
    `1399`
    路径上，
    而是在
    `TokenGenerationError?`
    分支被解析 /
    投影后出现
  - `TokenGeneration.framework`
    本体已确认存在：
    `TokenGenerationError.toInferenceError`
    `0x274de6890`
    且其本体
    显式调用
    `TokenGenerationErrorOMa`
    (`0x274de6ac8`)
- 结论：
  - 对当前
    extracted
    `TokenGenerationInference`
    而言，
    继续靠
    `__auth_got`
    零值
    恢复
    `293/296/1306/1358/1399`
    真实导入目标
    已经是死路
  - `293`
    的最强工作假设
    现在应更新成：
    它更像
    `TokenGenerationError`
    向
    `InferenceError`
    侧的
    rebox / project / convert
    helper family，
    而不是泛化
    `payload finalize`
  - 这条假设还没到
    “证明完成”，
    但方向已经明显优于
    旧的模糊表述
- 下一步：
  - 继续拆
    `TokenGenerationError.toInferenceError`
    `0x274de6890`
    的 switch 分支，
    确认它具体调用了哪些
    `InferenceError`
    case/context
  - 再把这些分支形态
    回对到
    `TokenGenerationInference`
    里
    `293`
    的使用点

## 2026-06-17 02:52:15 +0800

- 目标：
  - 用
    system dyld
    视图
    继续确认
    `TokenGenerationError.toInferenceError`
    是否真的在
    `InferenceError`
    侧做组装，
    从而继续压实
    `293`
    的身份
- 动作：
  - 使用
    `xcrun dyld_info -no_validate -disassemble`
    查看系统里的
    `TokenGeneration.framework`
    真正 shared-cache 反汇编
  - 聚焦：
    - `TokenGenerationError.toInferenceError`
    - `_$s20ModelManagerServices14InferenceErrorOACs0E0AAWL`
    - `InferenceErrorOSgMd`
    - `InferenceErrorO7ContextVSgMd`
- 证据：
  - system dyld
    视图里，
    `TokenGenerationError.toInferenceError`
    本体
    直接出现了多处
    对
    `_$s20ModelManagerServices14InferenceErrorOACs0E0AAWL`
    的引用热点：
    - `0x274DE8218`
    - `0x274DE82E0`
    - `0x274DE83D8`
    - `0x274DE8580`
    - `0x274DE86D4`
  - 这说明
    `toInferenceError`
    确实在
    `InferenceError`
    侧做
    witness / case / context
    相关工作，
    不是单纯的
    本地 error
    字符串处理
  - 同时，
    `TokenGenerationInference`
    中
    `293`
    继续稳定表现为：
    - 吃
      `1306`
      返回的
      `X1 slot`
    - 而不是
      `X0 handle`
- 结论：
  - `293`
    当前已不只是
    “像 convert helper”，
    而是有了
    更具体的工作表述：
    它很可能就是
    把
    `TokenGenerationError`
    侧局部值
    投影 /
    rebox /
    写入
    `InferenceError`
    error slot
    的 helper family
  - 当前缺的最后一跳
    是把
    `toInferenceError`
    的具体 switch case
    与
    `TokenGenerationInference`
    里对应
    `293`
    callsite
    一一回对
- 下一步：
  - 继续围绕
    `0x274DE8218`
    `0x274DE82E0`
    `0x274DE83D8`
    `0x274DE8580`
    `0x274DE86D4`
    这些热点
    找到对应的
    `InferenceError`
    case/context
  - 再把这些 case
    映射回
    `0x2751442a4`
    `0x275165798`
    `0x2751689ec`
    等
    `293`
    使用点

## 2026-06-17 03:31:58 +0800

- 目标：
  - 继续把
    `TokenGenerationError.toInferenceError`
    与
    `TokenGenerationInference:293`
    的关系从
    “强假设”
    压到更硬的本地证据
- 动作：
  - 继续用
    system dyld
    视图拆
    `TokenGenerationError.toInferenceError`
    `0x274de6890`
    的后半段和统一尾部
  - 本地提取
    `ModelManagerServices`
    本体里的
    `InferenceError`
    case 字符串全集
  - 检查
    extracted
    `TokenGenerationInference`
    的
    `__auth_stubs`
    / indirect symbol table
    是否可靠
- 证据：
  - `toInferenceError`
    多个分支都把不同
    payload/context
    写进临时位点后，
    汇到统一尾部
    `0x274DE90A0/0x274DE90C8`
    并用
    `w2`
    作为 case tag 收尾；
    已确认的 tag
    至少包括：
    `1 2 3 4 5 6 7 8 9 10 11 12 13 14 15 16 17`
  - `ModelManagerServices`
    本体的
    `__swift5_reflstr`
    当前已抓到
    `InferenceError`
    case 名全集候选：
    `notImplemented`
    `invalidClientData`
    `unsupportedRequestType`
    `responseEncodingFailed`
    `alreadyLoaded`
    `notLoaded`
    `loadFailed`
    `inferenceFailed`
    `operationNotAllowed`
    `streamNotFound`
    `rateLimited`
    `internalError`
    `networkError`
    `resourcesBusy`
    `hostFailed`
    `unspecifiedUnderlyingError`
    `unrecognizedUnderlyingError`
    `xpcError`
    `unspecified`
    `operationCancelled`
    `assetVersionMismatch`
    `conversionNotSupported`
    `deviceConnectionError`
    `versionNotSupported`
    `hostError`
  - `otool -Iv`
    证明
    extracted
    `TokenGenerationInference`
    的
    `(__TEXT,__auth_stubs)`
    indirect symbol table
    当前基本不可用：
    大片入口都错误显示成
    index 0 /
    同一个
    `DraftingBehavior...`
    符号
- 结论：
  - `293`
    再次朝
    `TokenGenerationError -> InferenceError`
    的
    rebox / convert / slot-write
    helper
    收紧了一步；
    当前它已经明显更像
    “把局部 error/payload
    填进最终
    `InferenceError`
    slot”
    的家族，
    而不是简单
    throw finalize
  - 但
    `w2 -> InferenceError case`
    还没完全一一映射完，
    这是下一轮最值钱的缺口
  - extracted Mach-O
    上继续做
    `__auth_stubs` /
    indirect symbol
    绑定恢复，
    当前继续判为
    不值得投入
- 下一步：
  - 优先完成
    `w2 = 1..17`
    到
    `InferenceError`
    具体 case
    的一一映射
  - 再把这些
    case
    回对到
    `TokenGenerationInference`
    中
    `293`
    的几个关键 callsite

## 2026-06-17 04:22:02 +0800

- 目标：
  - 继续推进
    `w2 -> InferenceError case`
    的精确映射，
    同时验证
    `TokenGenerationError.Code`
    与
    `toInferenceError`
    switch 注释之间
    是否真是一一对应
- 动作：
  - 直接解出
    `ModelManagerServices.InferenceError`
    顶层 field descriptor
    的 25 个 case 顺序
  - 直接解出
    `TokenGenerationError.Code`
    的
    field / rawValue / constructor
    顺序
  - 回看
    `toInferenceError`
    的几个关键分支
    (`0x274de6ec0`
    `0x274de7020`
    等)
- 证据：
  - `InferenceError`
    顶层 field descriptor
    `0x25a7996b0`
    已直接解出
    25 个 case
    的真实声明顺序
  - `TokenGenerationError.Code.rawValue.getter`
    `0x274deaa50`
    直接是
    `LDRB W0, [X20]`
  - `TokenGenerationError.Code(rawValue:)`
    `0x274dea628`
    通过
    `cmp x0, #0x12`
    / `csel`
    证明
    rawValue
    是线性
    `0..17`
    （越界落到 sentinel）
  - `toInferenceError`
    中
    `0x274de7020`
    （jump-table 注释
    `case 11`）
    实际在组
    `tooManyTokens`
    的
    `count/max`
    payload
  - `0x274de6ec0`
    （注释
    `case 15`）
    明显在组
    `SafetyRejectedInfo.ViolationCategory`
    相关 payload
- 结论：
  - 当前可以明确否掉一个旧隐含假设：
    `toInferenceError`
    jump-table
    注释里的
    `case N`
    不是
    `TokenGenerationError.Code.rawValue == N`
  - 也就是说，
    `toInferenceError`
    在进入 jump-table
    前
    至少做了一层
    helper / remap / grouped discriminator
    转换
  - 因而后续正确做法是：
    用
    分支 payload 形状 +
    统一尾部
    `w2`
    + `InferenceError`
    case 消费面
    去做映射，
    不能再拿
    switch 注释
    机械套
    rawValue
- 下一步：
  - 先锁定
    `0x274DE7710/0x274DE7718`
    这条
    无 payload /
    直接 case
    收尾路径
  - 再按
    `w2`
    分组，
    把
    `tooManyTokens`
    `safetyViolation`
    `rateLimited`
    `networkError`
    这些
    已知 payload 形状
    与
    `InferenceError`
    具体 case
    对死

- 2026-06-17 11:30
  - 目标：继续 `TokenGenerationError.toInferenceError`，补 `w2/tag group -> InferenceError case`。
  - 动作：重新分页反汇编 `0x274de6890` 全函数，按 offset 把 jump-table 主体、统一尾部与 `0x274de7718` 收尾拉平；同时复查 `TokenGenerationError` field metadata / `InferenceError` case 顺序。
  - 证据：`toInferenceError` 901 instructions 分页反汇编；`case 3 @ 0x274de71b4` 明确组 `count/max`；`case 11 @ 0x274de7020` 明确组 `name`；`case 15 @ 0x274de6ec0` 仍是 safety payload；`case 12 @ 0x274de7454` 是 `DocumentResource(...)`；`case 6 @ 0x274de75c0` 是 `Prompt.SpecialToken + Context`。
  - 结论：旧摘要里 “`tooManyTokens` = switch case 11” 是误记，现更正为 `switch case 3`。当前稳定可见的终态是 5 个直达 tag 组（`0x450/468/498/4A0/4A8`）经 `0x274de7718` 统一收尾，而不是 18 个独立终态。
  - 下一步：把这 5 个 tag group 进一步翻译成 `ModelManagerServices.InferenceError` 具体 case，优先解决 `case 4`（cancelled?）与 `cases 7/8/9/15` 组（rateLimited/network/safety）对应关系。
- 2026-06-17 11:52
  - 目标：继续把 `toInferenceError` 的 5 个终态 tag group 对死到 `InferenceError`。
  - 动作：重新起 live probe 进程，用 `lldb` 校验 `0x28F63A4xx` 需要加 shared-cache slide 才能落到 live 映射。
  - 证据：`lldb image list -o -f` 显示 shared-cache offset 为 `0x45f8000`；`0x28f63a450 + 0x45f8000 = 0x293c32450` 后，`memory region 0x293c32450` 成功落在 `[0x293bd8000-0x296804000) r--`。
  - 结论：`0x28F63A450/468/498/4A0/4A8` 这组终态槽位应按 shared-cache 未 slide 地址理解，后续 live 读值必须先加 slide，之前直接读未 slide 地址得到的“像代码的值”不能再用。
  - 下一步：继续读 slide 后 5 个槽位实际内容，并把它们翻译成 `InferenceError` tag / constructor 组。
- 2026-06-17 12:08
  - 目标：继续把 `toInferenceError` 5 个终态 group 对死到 `InferenceError`。
  - 动作：重起 live probe，用 shared-cache slide 后地址读取 `0x28F63A450/468/498/4A0/4A8`；再把读出的 live 指针减 slide 映射回静态地址。
  - 证据：slide 后 `0x293c32450/468/498/4A0/4A8` 中读到一组 `0x25ed6ba10..0x25ed6ba5c` 指针；减去 slide `0x45f8000` 后得到 `0x25a773a10..0x25a773a5c`；该区域位于 `ModelManagerServices.__TEXT,__const`，并含连续 `u32=1..24` 与 `InferenceError/Context/CodingKeys` 相关字样。
  - 结论：5 个终态 group 最后不是直接写小整数，而是在选 `ModelManagerServices` 里的 `InferenceError` 相关常量表项。后续要解释的是“5 个 group -> const table item -> InferenceError case”，而不是“5 个 group -> raw enum tag”。
  - 下一步：围绕 `0x25a7739f0..0x25a773a5c` 继续 reverse 其消费链，优先找谁读取这串 `1..24` 常量以及它与 `InferenceError` value witness 的连接点。
- 2026-06-17 12:18
  - 目标：在 IDA worker 不稳定时，先把当前足够高置信的终态 group->InferenceError 映射落成中间结论。
  - 动作：基于 `InferenceError` 已知 25-case 顺序、`ModelManagerServices.__TEXT,__const` 的 `u32=1..24` 常量区、以及 `toInferenceError` 5 个终态 group 的收敛面，整理零基/一基 tag 的候选映射。
  - 证据：`case 4` 对应 `cancelled`；`case 2` 对应 `networkError`；`0x25a773a10..` 为连续 `1..24` 常量，紧邻 `InferenceError/Context/CodingKeys` 文本。
  - 结论：当前可以先固定两条高置信映射：`cancelled -> InferenceError.operationCancelled`，`networkError -> InferenceError.networkError`。其余 3 个终态组仍需继续找 `ModelManagerServices.__TEXT,__const` 的消费链。
  - 下一步：重开 `modelmanagerservices_arm64e` 后优先找谁读取 `0x25a773a10..0x25a773a5c`，不要再只围绕 `TokenGeneration` 侧反复看 jump-table。
- 2026-06-17 12:36
  - 目标：把 5 个终态 group 的 `InferenceError` case 继续从“候选”提升到高置信结论。
  - 动作：基于 live 读到的终态槽位指针、shared-cache slide 回算后的静态地址、以及 `ModelManagerServices.__TEXT,__const` 中连续 `u32=1..24` 常量区，按零基 tag 解释 5 个 group 选中的表项。
  - 证据：live `0x25ed6ba..` 指针减 slide 后落到 `0x25a773a10..0x25a773a5c`；其中关键表项分别对应 zero-based `1/7/10/12/19`；`InferenceError` 真实 case 顺序已知。
  - 结论：当前 5 个终态 group 的高置信映射为 `0x450->networkError`、`0x468->rateLimited`、`0x498->inferenceFailed`、`0x4A0->invalidClientData`、`0x4A8->operationCancelled`。
  - 下一步：重开 `modelmanagerservices_arm64e` 后，直接找谁消费 `0x25a773a10..0x25a773a5c`，把这 5 条映射补成静态消费链实锤。
- 2026-06-17 12:49
  - 目标：判断在未拿到普通 data xref 的情况下，`TokenGenerationError -> InferenceError` 这条链是否已经足够闭环。
  - 动作：复核 `toInferenceError` 统一收尾、live 指针、shared-cache slide 回算、`ModelManagerServices.__TEXT,__const` 常量区内容，以及 IDA 上对该常量区无普通 xref 的情况。
  - 证据：`0x274de7718 -> metadata/value witness` 收尾；live `0x25ed6ba..` -> static `0x25a773a10..`；静态常量区内容为 `InferenceError/Context/CodingKeys` + 连续 `u32` tag 序列；`xref_query` 对该常量区返回 no xref。
  - 结论：当前主线已经足够闭环到“5 个终态 group -> 具体 InferenceError case”；剩余未补的是 `ModelManagerServices` 内部 consumer function 名，不再是 case 映射本身。
  - 下一步：继续找 `ModelManagerServices` 内部谁消费这块常量区，用作函数名级别补强。
- 2026-06-17 13:02
  - 目标：把 `toInferenceError` 末尾的写回路径从“高置信”提升到 ABI 级事实。
  - 动作：对照 Swift 官方 ABI 源里的 ptr-auth discriminator 常量，重新解释 `0x274de772c..0x274de774c`。
  - 证据：Swift 官方源 `MetadataValues.h` 搜索片段给出 `ValueWitnessTable=0x2e3f`、`DestructiveInjectEnumTag=0xb2e4`；而 `toInferenceError` 末尾正好先用 `0x2E3F` 认证 VWT，再用 `0xB2E4` 认证并调用目标 slot。
  - 结论：`0x274de774c` 已可 ABI 级定性为对 `InferenceError` VWT 上 `destructiveInjectEnumTag` 的调用，即把选定 tag 注入结果 enum。当前主线已不只是 case 映射高置信，而是写回路径也闭环。
  - 下一步：继续补 `ModelManagerServices.__TEXT,__const` tag 常量区的内部 consumer function 名。

- 2026-06-17 12:38
  - 目标：继续补 `ModelManagerServices` 侧 `InferenceError` 常量区的内部 consumer function 名，并把它和 `TokenGenerationInference:293` 的假设关系收紧。
  - 动作：重开 `modelmanagerservices_arm64e`；对 `0x25a7739f0..0x25a773a5c` 周围的 `InferenceError` 相关字符串、`otool` 反汇编和 IDA 强制定函数后的伪代码做交叉；把 `0x25a63ed40`、`0x25a63f4d8`、`0x25a63f9d4` 这些核心点补成可读 consumer 链。
  - 证据：
    - `0x25a63e844` 所在 jump-table 函数直接命中 `invalidClientData`(`0x25a63ea64`) / `operationCancelled`(`0x25a63ece8`) / `responseEncodingFailed` / `operationNotAllowed` / `assetVersionMismatch` 等 case-name 字面量；
    - `0x25a63f9d4` 已成功定义并反编译，明确是 `InferenceError` project tag 后返回整数码的 25-case switch；本轮整理出的 machine-local 映射里，`invalidClientData -> 2014`、`inferenceFailed -> 2008`、`rateLimited -> 2011`、`networkError -> 2016`、`operationCancelled -> 2013` 等都已固定；
    - `0x25a63f4d8` 已成功反编译，内部可见 `"Received a ModelManagerError wrapping an InferenceError"` 和 `"InferenceError: got unrecognized error %@"` 两条日志，同时还会走 `objc_msgSend$domain` / `objc_msgSend$code` 与 `InferenceError.Context` 的组装/回写路径；
    - `0x25a7739f0..0x25a773a5c` 原始 `__TEXT,__const` dump 仍是 `InferenceErrorContext` + 连续 `u32 1..24`。
  - 结论：`ModelManagerServices` 侧已经不再只是“有一块 `InferenceError` tag 常量区”，而是已经出现真实的 case-name consumer、error-code consumer、以及 `ModelManagerError -> InferenceError` bridge consumer。现阶段足以把 `TokenGenerationError.toInferenceError` 的 5 个终态 group 映射视为已被 consumer 面支撑；剩余主线变成把这 3 条 consumer 链回接到 `TokenGenerationInference:293`。
  - 下一步：只开 `TokenGenerationInference`，围绕 `293` 本体、`convertToInferenceError 0x2750d0990` 和代表性 callsite `0x2751442a4/0x275165798/0x2751689ec` 做最小回接，确认 `293` 是 enum project/rebox/convert helper family 的哪一层。

- 2026-06-17 13:06
  - 目标：把 `TokenGenerationInference:293` 从“强假设”进一步压到具体分支语义。
  - 动作：打开 `tokengenerationinference_arm64e`；反编译 `convertToInferenceError 0x2750d0990`，并检查代表性 throw-path callsite `0x2751689ec` 与 `0x275165798` 附近指令序列。
  - 证据：
    - `convertToInferenceError` 伪代码显示：先尝试 `TokenGenerationError?`，成功才走 `293`；若输入已是 `InferenceError?` 则直接拷出，不走 `293`；若都失败，则 `CancellationError` 直接取 `MEMORY[0x28F63A4A8]`，generic NSError-like 分支直接取 `MEMORY[0x28F63A498]` 并组 `localizedDescription/domain/code/userInfo`。
    - `0x2751689e0..0x2751689f4` 的典型形态是：`1306` -> `MOV X8, X1` -> `BL 293` -> `BL 1399`。
    - `convertToInferenceError` 内对 `0x28F63A4A8` / `0x28F63A498` 的直接取用，与前面在 `TokenGeneration.framework.toInferenceError` 中确认的终态 slot 映射一致。
  - 结论：`293` 现在可以更具体地定性为 `TokenGenerationError? -> InferenceError` 专用分支上的 in-place convert / rebox helper，而不是泛化 payload finalize，也不是所有 throw-path 都统一走的一步。
  - 下一步：若继续这一主线，只补两点：给 `ModelManagerServices` 侧 3 个 consumer 函数找更正式的 Swift 名称；再选一个 `1306 -> 293 -> 1399` callsite 比对 `293` 前后的目标位点是否与 `convertToInferenceError` 的临时 `InferenceError` 栈槽一致。

- 2026-06-17 13:12
  - 目标：确认 `293` 的调用约定模式是否一致，尤其是它是否依赖 `X8` 这类 side-band 输入。
  - 动作：对 `j__$..._293` 做 code xref 汇总，并抽查 `0x2751689ec`、`0x275165798` 一带的代表性 callsite。
  - 证据：
    - `293` 当前已有 20+ 个 code xref，主要集中在 `handleCustom`、`supportedTools`、`compileAdapter`、`requestStream`、`classify` 等少数 typed-error 路径；
    - 代表性路径 `0x2751689e0..0x2751689f4` 仍然是 `1306 -> MOV X8, X1 -> 293 -> 1399`；
    - `compileAdapter` 的多个路径也出现相同局部模板。
  - 结论：`293` 进一步收紧为“显式依赖 side-band 输入（常见是 `X8`）的 in-place rebox / slot-fixup helper”，位置在 typed error 已确定之后、throw ABI 收尾之前。
  - 下一步：若继续这条线，只抽查 2 个 callsite，把 `X8` 对应的临时 error slot / witness companion 钉死即可。

- 2026-06-17 13:18
  - 目标：确认 `293` 前的 `X8` 更像什么语义。
  - 动作：抽查 `handleCustom`、`classify`、`requestStream` 三个 callsite 片段，并回看 `convertToInferenceError` 的 usercall 签名。
  - 证据：
    - `convertToInferenceError` 已被反编译成 `a1@<X0>, a2@<X8>` 形态，且函数开头立即把 `X8` 保存为 `var_60`，后续成功分支原样取回后喂给 `293`；
    - 多个 callsite 都复现 `1306/typed-error helper -> MOV X8, X1(或等价) -> 293 -> 1399/1400` 模板。
  - 结论：`293` 使用的 `X8` 更像调用者传入的目标输出槽 / 间接返回位点；`293` 本身则是在该目标位点上做 in-place error rebox / slot-fixup。
  - 下一步：若继续，只追一个 callsite 中 `MOV X8, X1` 的 `X1` 来源，把它钉到具体栈槽/结果对象即可。

- 2026-06-17 13:24
  - 目标：确认 `1306` 的 `X1` 是否就是 `293` 的 `X8` 来源。
  - 动作：抽查 `compileAdapter` 与 `requestStream` 两条最关键 throw-path 的 `293` 前后指令。
  - 证据：
    - `0x275165d04..0x275165d3c`：`BL 1306 -> MOV X25, X0 -> MOV X8, X1 -> BL 293 -> MOV X21, X25 -> BL 1399`
    - `0x2751689e0..0x2751689f4`：`BL 1306 -> MOV X27, X0 -> MOV X8, X1 -> BL 293 -> MOV X21, X27 -> BL 1399`
  - 结论：`293.X8` 在关键 typed-error throw-path 上就是 `1306.X1` 的直接转发；`1306` 产出 `(X0, X1)`，`293` 消耗 `(X0, X8=X1)` 做 slot-fixup，`1399` 再基于保存下来的 `X0` 副本完成最终 throw 收尾。
  - 下一步：若继续，只补 `1399` 前主值寄存器保存模式是否固定即可。

- 2026-06-17 13:32
  - 目标：确认 `293` 与 `1399/1400` 的职责边界是否已经足够清楚。
  - 动作：拉取 `1399/1400` 的 xref 面，并与 `293` 的 xref 面做对比；复核前面两条关键路径的寄存器模板。
  - 证据：
    - `1399` 当前已有 100+ code xref，`1400` 也有 90+ code xref，覆盖大量普通错误出口；
    - `293` 的 xref 面明显更窄，主要集中在 typed-error 重封装点；
    - `compileAdapter` / `requestStream` 两条关键路径都稳定呈现 `1306 -> MOV X8, X1 -> 293 -> MOV 保存主值 -> 1399`。
  - 结论：当前已足够把三者职责拆开：`1306` 产出 typed error 对；`293` 做 typed-error 专用 slot-fixup；`1399/1400` 做更普适的最终 throw/return 收尾。主线可视为基本封口。
  - 下一步：若继续，只做文档清理和命名补强。

- 2026-06-17 13:40
  - 目标：再做一轮 `ModelManagerServices` 命名补强，看看能否给 `InferenceError` consumer 找到更正式的本地锚点。
  - 动作：检查 `ModelManagerServices` 中 `InferenceError` 相关 associated conformance 文本，并直接看 `0x25a645560` / `0x25a63e844` 一带的反汇编。
  - 证据：
    - `0x25a645560` 直接 `b 0x25a63f9d4`，说明 `0x25a63f9d4` 被专门包成 framework 内 consumer 入口；
    - `0x25a63e844` 仍稳定命中大量 case-name 字面量；
    - `0x25a63f9d4` 仍稳定表现为 25-case enum -> 整数错误码分发表。
  - 结论：虽然还没拿到完美的 Swift 原始符号名，但 `0x25a63e844 / 0x25a63f9d4 / 0x25a63f4d8` 的职责分工已经足够稳定，继续追 stub/witness 精确命名的收益很低。
  - 下一步：这条线如果继续，优先做文档收敛，而不是再深挖命名。

- 2026-06-17 13:46
  - 目标：把当前 `TokenGenerationError -> InferenceError -> throw ABI` 这条线压成单独的短总结文档，避免后续重复翻长历史。
  - 动作：新增 `docs/token_generation_inference_error_summary.md`，只保留当前已经稳定的结论模板与关键地址。
  - 证据：文档已落盘，内容覆盖 `toInferenceError`、`InferenceError` 3 条 consumer、`convertToInferenceError`、`1306/293/1399/1400` 模板和职责边界。
  - 结论：后续恢复这条支线时可以优先看这份摘要，不再需要先重新消化 `ane_state.md` 的长篇历史。
  - 下一步：如继续，优先做文档清理和主线切换，而不是再深挖这条已基本封口的支线。

- 2026-06-17 14:06
  - 目标：把这条支线的最终结论直接固化到 IDA 里，减少后续恢复成本。
  - 动作：重开 `ModelManagerServices` / `TokenGenerationInference` 会话；对关键函数和关键 callsite 加书签，并补最小摘要注释。
  - 证据：
    - `ModelManagerServices` 书签已加在 `0x25a63e844` / `0x25a63f9d4` / `0x25a63f4d8`
    - `TokenGenerationInference` 书签已加在 `0x2750d0990` / `0x275165d04` / `0x2751689e0` / `0x2751442a4`
    - `0x25a63f9d4` / `0x25a63f4d8` / `0x2750d0990` 等地址已写入摘要注释；`0x25a63e844` 因未被当前 IDA 识别成函数，改写为行注释
  - 结论：这条支线现在不仅有 markdown 摘要，也有 IDA 内部持久化锚点，恢复成本已足够低。
  - 下一步：如继续，优先切回主线，不再继续深挖这条已封口支线。

- 2026-06-17 14:12
  - 目标：把 `TokenGeneration.framework` 本体的关键结论也直接固化到 IDA，补齐 3 个 framework 的持久化闭环。
  - 动作：打开 `TokenGeneration` 会话；对 `toInferenceError` 本体、ABI 尾部注入点和几个关键 case 分支添加书签与摘要注释。
  - 证据：
    - `0x274de6890` / `0x274de774c` / `0x274de71b4` / `0x274de6ec0` / `0x274de7454` / `0x274de75c0` / `0x274de7020` 均已写入书签；
    - `toInferenceError` 函数注释已包含 5 个终态 group -> `InferenceError` 映射；
    - `0x274de774c` 已被标成 ABI-level `destructiveInjectEnumTag`。
  - 结论：这条 `TokenGenerationError -> InferenceError -> throw ABI` 支线现在在 `TokenGeneration` / `ModelManagerServices` / `TokenGenerationInference` 三个 framework 中都已完成 IDA 持久化锚定，恢复成本已经降到最低。
  - 下一步：优先切回主线；这条支线只保留为参考结论，不再继续深挖。

- 2026-06-17 19:57:32 +0800
  - 目标：把 `ane_runtime_rehydrate_probe` 的 baseline/clone 对照再做一层 machine-local 收窄，判断 `mapIOSurfaces...` 的 `0x12` 是否只是 `program/mapper/controller` 对象图差异。
  - 动作：
    - 修复并扩展 `mps/ANE/experiments/ane_runtime_rehydrate_probe.m`：
      - 新增 baseline `base_program/base_mapper/base_controller` snapshot
      - 新增 clone 侧 `candidate_* / fresh_*` runtime-family snapshot
      - 新增 `shallow_full_shared_controller` / `factory_full_shared_controller`
      - 新增 `shallow_reuse_objects` / `factory_reuse_objects`
    - 重新 `make ane_runtime_rehydrate_probe && ./ane_runtime_rehydrate_probe`
      并读取 `mps/ANE/.ane_runs/csv/ane_runtime_rehydrate_probe.csv`
  - 证据：
    - `mps/ANE/experiments/ane_runtime_rehydrate_probe.m`
    - `mps/ANE/.ane_runs/csv/ane_runtime_rehydrate_probe.csv`
  - 结论：
    - `shallow_full` / `factory_full`：
      `fresh_mapper.controller_matches_program_controller = 0`、
      `fresh_controller.usecount = 1`，且 `map_ok=0 eval_ok=1`
    - `*_full_shared_controller`：
      即使强制让 mapper 复用 program 的 controller，
      `controller_matches_program_controller = 1`、
      `usecount = 2`，仍然 `map_ok=0 eval_ok=1`
    - `*_reuse_objects`：
      即使直接复用 baseline 已成功 load 的原始 `program`/`mapper` 对象，
      仍然 `map_ok=0 eval_ok=1`
    - 因而 `Program IOSurfaces map failure (0x12)` 已经不能再归因于当前
      probe 可见的 `program/mapper/controller` 对象图差异；缺口更像在 fresh
      `_ANEInMemoryModel` 自身或更低层 hidden accepted-state / request-lowering state。
  - 下一步：
    - 直接静态 reverse
      `-[_ANEInMemoryModel mapIOSurfacesWithRequest:cacheInference:error:]`
      及其下游 consumer；
    - 查 fresh `_ANEInMemoryModel` 上当前 probe 没同步到的隐藏状态；
    - 不再继续围绕 visible object graph 加同类 probe 变体。

- 2026-06-17 21:xx:xx +0800
  - 目标：继续验证 hidden state 是否可能挂在 `_ANEModel` 对象本身，而不只是其公开字段或 `program/mapper` 子对象。
  - 动作：
    - 在 `mps/ANE/experiments/ane_runtime_rehydrate_probe.m` 新增 `direct_base_model` 变体；
    - fresh `_ANEInMemoryModel` 直接 `setModel(baseModel)`，不再 clone/rebuild `_ANEModel`；
    - 重新 `make ane_runtime_rehydrate_probe && ./ane_runtime_rehydrate_probe`
  - 证据：
    - `mps/ANE/.ane_runs/csv/ane_runtime_rehydrate_probe.csv`
      中 `direct_base_model*` 行
  - 结论：
    - 即使 fresh `_ANEInMemoryModel` 直接持有原始 loaded `_ANEModel` 对象本身，
      `mapIOSurfacesWithRequest:cacheInference:error:` 仍然
      `Program IOSurfaces map failure (0x12)`，
      但 `evaluateWithQoS:options:request:error:` 仍成功；
    - 因而 hidden state 已进一步收窄：
      不在 visible `program/mapper/controller` 图上，
      也不在 `_ANEModel` 对象本身，
      更像在 `_ANEInMemoryModel` / `_ANEClient` /
      `_ANEProgramIOSurfacesMapper` / lower map path。
  - 下一步：
    - 继续静态 reverse
      `_ANEProgramIOSurfacesMapper validateRequest:model:`
      / `prepareANEMemoryMappingParams:request:`
      / `block_invoke`
      / `_ANEVirtualClient doMapIOSurfacesWithModel:request:cacheInference:error:`

- 2026-06-17 21:57:36 +0800
  - 目标：判断 `0x12` 是否具有“一次成功后污染 lower state”的性质，并验证真正 `controller stop/start` 能否恢复 map。
  - 动作：
    - 继续修改 `mps/ANE/experiments/ane_runtime_rehydrate_probe.m`：
      - 修正 `first_direct_base_model` 证据污染；
      - 新增 `first_direct_base_model_repeat`；
      - 新增 `prebaseline_loaded_repeat`；
      - 新增 `restart_controller_for_model(...)`，显式把 controller 从
        `usecount=2` 连续 `stop` 到 `0`，确认 `device=nil`，再 `start`
        回 `2`；
      - 重新编译并运行 `/tmp/ane_runtime_rehydrate_probe`；
      - 读取 `mps/ANE/.ane_runs/csv/ane_runtime_rehydrate_probe.csv`。
    - 配合 `ida-pro-mcp` 继续确认静态链：
      - `_ANEClient mapIOSurfacesWithModel:request:cacheInference:error:`
        只是取 `model.mapper` 再下发；
      - `_ANEProgramForEvaluation initWithController...` /
        `_ANEProgramIOSurfacesMapper initWithController:`
        都会对 controller `start`；
      - 它们的 `dealloc` 都会 `stop`；
      - `_ANEDeviceController stop` 在 `usecount==0` 时会真的关 device 并清零。
  - 证据：
    - `mps/ANE/experiments/ane_runtime_rehydrate_probe.m`
    - `mps/ANE/.ane_runs/csv/ane_runtime_rehydrate_probe.csv`
    - `AppleNeuralEngine` IDA:
      - `-[_ANEClient mapIOSurfacesWithModel:request:cacheInference:error:]`
      - `-[_ANEProgramIOSurfacesMapper initWithController:]`
      - `-[_ANEProgramForEvaluation initWithController:intermediateBufferHandle:queueDepth:]`
      - `-[_ANEProgramForEvaluation dealloc]`
      - `-[_ANEProgramIOSurfacesMapper dealloc]`
      - `___29-[_ANEDeviceController start]_block_invoke`
      - `___28-[_ANEDeviceController stop]_block_invoke`
  - 结论：
    - `first_direct_base_model.map` 第一次成功，且 `eval_ok=1`；
    - 紧接着同进程的 `first_direct_base_model_repeat.map` 就掉进稳定
      `Program IOSurfaces map failure (0x12)`，但 `eval_ok=1`；
    - 之后：
      - `direct_base_model.map`
      - `prebaseline_loaded.map`
      - `prebaseline_loaded_repeat.map`
      - `baseline.map`
      - `baseline_repeat.map`
      全部统一 `0x12`；
    - `prebaseline_loaded_restart` / `baseline_restart`
      都明确做到：
      - `stop[1] -> usecount=0 -> device=nil`
      - `start[0] -> device reopened`
      - `start[1] -> usecount=2`
      但 `*_after_restart.map` 仍然 `0x12`；
    - 因而当前最强 machine-local 结论是：
      `0x12` 更像 lower map path 的一次性 accepted-state / runtime-table /
      process-global state 污染，而不是 fresh wrapper / program / mapper /
      controller 图差异，甚至也不是单纯“device 没真正重开”。
    - 同轮 side fact：
      `second_loaded` 这次在 `compileWithQoS` 就直接
      `InvalidMILProgram`，因此不要把它这轮缺失当作 map-path 差异。
  - 下一步：
    - 直接比较第一次成功 map 与第二次失败 map 的
      `prepareANEMemoryMappingParams` / request tail / transactionHandle
      是否一致；
    - 静态继续追
      `-[_ANEProgramIOSurfacesMapper unmapIOSurfacesWithModel:request:error:]`
      与 lower device vtable `+0x38` 的 shared state；
    - 不再继续扩 visible object graph 变体。

- 2026-06-17 22:23:38 +0800
  - 目标：确认第一次成功 map 与第二次失败 map 的差异是否还停留在 request-lowering / visible unmap 这一层。
  - 动作：
    - 在 `mps/ANE/experiments/ane_runtime_rehydrate_probe.m` 复用
      `ane_request_runtime_bridge_probe` 的逻辑，新增：
      - `snapshot_request`
      - `validateRequest:model:`
      - `prepareANEMemoryMappingParams:request:`
      的前后快照
    - 对：
      - `first_direct_base_model`
      - `first_direct_base_model_repeat`
      做 map 前后 request / mapping params 对照；
    - 新增 mapper-level
      `unmapIOSurfacesWithModel:request:error:`
      直接返回值记录；
    - 静态读取：
      - `___83-...map..._block_invoke`
      - `___70-...unmap..._block_invoke`
      确认 map/unmap lower ret code 都直接来自 `controller.device` vtable。
  - 证据：
    - `mps/ANE/.ane_runs/csv/ane_runtime_rehydrate_probe.csv`
    - `AppleNeuralEngine` IDA:
      - `___83-[_ANEProgramIOSurfacesMapper mapIOSurfacesWithModel:request:cacheInference:error:]_block_invoke`
      - `___70-[_ANEProgramIOSurfacesMapper unmapIOSurfacesWithModel:request:error:]_block_invoke`
  - 结论：
    - `first_direct_base_model.pre_map.prepare`
      与
      `first_direct_base_model_repeat.pre_map.prepare`
      的 `mapping_params` hash 完全一致；
      当前可见差异只在 IOSurface ID / request 对象指针，不在 tail fields /
      lowering 结构本身。
    - `first_direct_base_model.mapper_unmap`
      明确返回：
      - `ok=1`
      - `error=nil`
    - 因而这轮已经基本证伪：
      1. 第二次 `0x12` 是 request-lowering 参数不同
      2. 第一次成功后 visible mapper-level unmap 失败、状态没释放
    - static 还补清楚了一点：
      - 只有 `cacheInference=1` 且 lower map 成功时，
        block 才会把 `params+3088` 写回 `request.transactionHandle`
      - 当前我们大多数成功窗口都跑在 `cacheInference=0`
        或已污染状态里，因此暂时拿不到 transaction 证据
  - 下一步：
    - 若继续追 transaction 线，必须把 `cacheInference=1`
      放到“进程里的第一次成功 map”窗口；
    - 否则直接转去更低层：
      lower device/runtime table / process-global accepted-state。

- 2026-06-17 22:42:40 +0800
  - 目标：验证 transaction 线在“进程里的第一次成功 map”窗口中是否真的能打开，判断 `0x12` 是否只属于 no-transaction 路径。
  - 动作：
    - 在 `ane_runtime_rehydrate_probe.m` 新增
      `run_variant_cache_roundtrip(...)`：
      - fresh direct-base wrapper
      - 第一次直接用 `cacheInference=1` 做 map
      - 读取成功后回填的 `request.transactionHandle`
      - 用该 transaction 构造第二个 request，再做第二次 `cacheInference=1` map
    - 重新编译并运行 probe；
    - 读取 `first_direct_base_model_txn_roundtrip*` 行。
  - 证据：
    - `mps/ANE/.ane_runs/csv/ane_runtime_rehydrate_probe.csv`
      中 `first_direct_base_model_txn_roundtrip*`
  - 结论：
    - `first_direct_base_model_txn_roundtrip.first_map_yes`
      成功；
    - map 成功后 request 上确实拿到：
      `transactionHandle = 0`
    - `first_mapper_unmap` 成功；
    - 随后第二次继续带 transaction 再做
      `cacheInference=1` map：
      - `second_map_yes` 仍成功
      - request 上 `transactionHandle` 递增为 `1`
      - `second_mapper_unmap` 也成功
    - 这说明：
      - `0x12` 不是“第二次 map 必然失败”
      - 真正分水岭是：
        no-transaction 的 `cacheInference=0` 路
        vs.
        transaction-aware 的 `cacheInference=1` 路
      - 主线已经进一步收紧到：
        lower transaction/runtime-table state 的 author 与消费
  - 下一步：
    - 继续 reverse / probe：
      `cacheInference=0`
      为什么不 author 同样的 transaction/runtime state；
    - 把 transaction/runtime-table 作为当前最优先控制层继续下钻。

- 2026-06-17 23:12:53 +0800
  - 目标：区分“同一 wrapper 的第二个 request”与“second fresh wrapper 的 first map”，确认 transaction/cache 线是否只对同一 wrapper 生效。
  - 动作：
    - 新增 followup 矩阵与 two-wrapper probe：
      - `txn_followup_cache1_with_txn`
      - `txn_followup_cache1_no_txn`
      - `txn_followup_cache0_with_txn`
      - `txn_followup_cache0_no_txn`
      - `two_wrapper_keepalive`
      - `two_wrapper_release_first`
      - `two_wrapper_second_cache1_no_txn`
      - `two_wrapper_second_cache1_txn0`
      - `two_wrapper_second_cache0_txn0`
      - `two_wrapper_diff`
    - 补了一个本机小工具，直接打印：
      - `_ANEInMemoryModel`
      - `_ANEModel`
      - `_ANEProgramForEvaluation`
      - `_ANEProgramIOSurfacesMapper`
      - `_ANEDeviceController`
      的 ivar 偏移。
    - 用 IDA 继续解：
      - `-[_ANEInMemoryModel initWithDesctiptor:]`
      - `+[_ANEInMemoryModel inMemoryModelWithDescriptor:]`
      - `-[_ANEInMemoryModel dealloc]`
      - `-[_ANEInMemoryModel hexStringIdentifier]`
  - 证据：
    - `mps/ANE/.ane_runs/csv/txn_followup_cache*.csv`
    - `mps/ANE/.ane_runs/csv/firstcache0_followup_*.csv`
    - `mps/ANE/.ane_runs/csv/two_wrapper_*.csv`
    - `_ANEInMemoryModel` ivar dump：
      - `+0x18 = _hexStringIdentifier`
      - `+0x28 = _sharedConnection`
      - `+0x40 = _model`
      - `+0x58 = _program`
      - `+0x68 = _descriptor`
    - IDA：
      `initWithDesctiptor:` 会把
      `descriptor.hexStringIdentifier`
      写入 `_ANEInMemoryModel +0x18`
  - 结论：
    - 同一 wrapper 内：
      - first map 成功后，
      - second map 可以继续成功；
      - 不管 second map 用：
        - `cacheInference=1/no-txn`
        - `cacheInference=1/txn0`
        - `cacheInference=0/txn0`
        - `cacheInference=0/no-txn`
        都能成功
    - two-wrapper 路：
      - wrapper1 first map 成功
      - wrapper2 first map 失败，稳定 `0x12`
      - 即使释放 wrapper1 后再建 wrapper2，仍失败
      - 即使给 wrapper2：
        - `cacheInference=1/no-txn`
        - `cacheInference=1/txn0`
        - `cacheInference=0/txn0`
        仍失败
    - `two_wrapper_diff` 显示：
      - wrapper1 成功 map/unmap 前后，
        `_ANEInMemoryModel` 原始内存不变
      - wrapper1 与 wrapper2 在 map 前相比：
        - `_ANEModel` 内容一致
        - `_ANEProgramForEvaluation` 内容一致
        - `_ANEProgramIOSurfacesMapper` 内容一致
        - 唯一差异是 `_ANEInMemoryModel +0x18`
    - 因而当前最强结论更新为：
      - 关键差异不是 request，也不是 transaction，也不是 program/mapper 内容
      - 更像是 wrapper identity
        (`_hexStringIdentifier`)
        参与了 lower map-owner / accepted-state key
  - 下一步：
    - 继续 reverse `_hexStringIdentifier` /
      `descriptor.hexStringIdentifier` /
      `descriptor.hash`
      的 lower consumer；
    - 优先判断这条 identity 线是 debug-only，
      还是确实进入了 lower map-owner 语义。

- 2026-06-18 01:34:49 +0800
  - 目标：验证 `_hexStringIdentifier` 是否已经足够解释 second wrapper first map 的 `0x12`。
  - 动作：
    - 新增 `two_wrapper_hexid_alias`：
      - wrapper1 first map 成功；
      - wrapper2 first map 前，直接把其 `_hexStringIdentifier`
        alias 成 wrapper1 同值；
      - 再测 wrapper2 first map；
    - 同时继续 `ida-pro-mcp` 静态 reverse：
      - `-[_ANEInMemoryModel initWithDesctiptor:]`
      - `-[_ANEInMemoryModel hexStringIdentifier]`
      - `-[_ANEInMemoryModelDescriptor hexStringIdentifier]`
      - `-[_ANEInMemoryModelDescriptor hash]`
  - 证据：
    - `mps/ANE/.ane_runs/csv/two_wrapper_hexid_alias.csv`
    - `AppleNeuralEngine` IDA 上述函数
  - 结论：
    - `two_wrapper_hexid_alias` 中：
      - wrapper2 的 `_hexStringIdentifier` 已改成与 wrapper1 完全相同
      - 但 wrapper2 的 first map 仍然稳定 `0x12`
    - 因而 `_hexStringIdentifier` 单字段并不是足够条件；
      它更像更大 identity 组合的一部分，或者只是 lower state 一并记录的标签
    - 静态也确认：
      - `descriptor.hexStringIdentifier`
        只是 `networkTextHash + weightsHash + optionsPlistHash` 的字符串拼接
      - `descriptor.hash`
        只是这三者 hash 的 XOR
      - `initWithDesctiptor:` 会把这个 string 写进 wrapper 的 `_hexStringIdentifier`
    - 当前更合理的下一步是继续看：
      - `sharedConnection`
      - `modelURL`
      - `descriptor.hash`
      - 及其组合是否共同构成 lower map-owner key
  - 下一步：
    - 别再把 root cause 简化成“hex id 单字段不同”；
    - 继续在 identity 组合层做最小 probe / 静态 consumer 追踪。

- 时间：2026-06-18 23:42:14 +0800
  - 目标：先把“污染层级”在当前 visible/userland runtime 层彻底判死，确认
    `eval -> 0x12` 是否会跨进程残留。
  - 动作：
    - 严格串行跑两个独立进程：
      1. 进程 A：
         `cd mps/ANE/experiments && ./ane_runtime_rehydrate_probe --case two_wrapper_after_eval_only --csv ../.ane_runs/csv/two_wrapper_after_eval_only_processA_serial_20260618.csv`
      2. 确认 A 退出后，
         进程 B：
         `cd mps/ANE/experiments && ./ane_runtime_rehydrate_probe --case two_wrapper_after_map_only --csv ../.ane_runs/csv/two_wrapper_after_map_only_processB_afterA_serial_20260618.csv`
    - 同时把结论回写到：
      - `docs/ane_state.md`
      - `docs/ane_next.md`
  - 证据：
    - `mps/ANE/.ane_runs/csv/two_wrapper_after_eval_only_processA_serial_20260618.csv`
      - `wrapper1_eval=1`
      - `wrapper2_map=0x12`
    - `mps/ANE/.ane_runs/csv/two_wrapper_after_map_only_processB_afterA_serial_20260618.csv`
      - `wrapper1_map=1`
      - `wrapper2_map=1`
  - 结论：
    - `eval` 触发的 `0x12` 污染不会跨进程残留；
      process exit 后 fresh process 可以重新 map 成功
    - 所以当前不要再把问题建模成
      `machine-global/device-global persistent state`
    - 当前真正该判死的是：
      同进程内 current visible/userland runtime surface 上，
      不存在可用的 clear/reset control surface
    - 已被判死、不要再重复的同层尝试：
      - `_hexStringIdentifier`
      - `transactionHandle=0`
      - public `unload/load`
      - controller `stop/start`
      - visible request-lowering params
      - sync vs async completion
  - 下一步：
    - 若继续追污染线，直接下沉到
      selector=2 / selector=5 共享的 lower runtime state /
      accepted-state author
    - 若切回主性能线，则把
      “同进程内无 userland clear/reset surface”
      当作已确认前提，不再在 wrapper/descriptor 层兜圈子

- 时间：2026-06-19 00:27:11 +0800
  - 目标：完成当前污染线 loop 的本轮唯一假设验证：
    判断 carrier 是否仍可能落在 request 对象自身或 request-local 字段上。
  - 动作：
    - 修改
      `mps/ANE/experiments/ane_runtime_rehydrate_probe.m`
      新增：
      `same_request_after_eval_map`
    - 同一个 wrapper、同一个 `_ANERequest`：
      1. `eval`
      2. 记录 request raw memory
      3. 不新建 request，直接复用同一个 request 去 `map`
      4. 再记录 request raw memory
    - 重新编译并运行：
      `xcrun clang -O2 -fobjc-arc -framework Foundation -framework IOSurface -ldl -o ane_runtime_rehydrate_probe ane_runtime_rehydrate_probe.m && ./ane_runtime_rehydrate_probe --case same_request_after_eval_map --csv ../.ane_runs/csv/same_request_after_eval_map_20260619.csv`
  - 证据：
    - `mps/ANE/.ane_runs/csv/same_request_after_eval_map_20260619.csv`
    - 关键结果：
      - `pre_eval_raw.request.memory_summary.hash = 0xc8f5933a72c7979f`
      - `post_eval_raw.request.memory_summary.hash = 0xc8f5933a72c7979f`
      - `post_map_raw.request.memory_summary.hash = 0xc8f5933a72c7979f`
      - 同一个 request 上：
        `evaluateWithQoS... = 1`
        后，
        `mapIOSurfacesWithRequest... = 0x12`
  - 结论：
    - 本轮 loop verdict：`falsified`
    - 当前没有证据支持：
      request 对象自身被 `eval` 原地改写成了后续 `map` 所需的关键 carrier
    - 也没有证据支持：
      request-local
      `transactionHandle/sharedEvents/completionHandler`
      这一层是 root carrier
    - 因而污染线下一轮不能再围绕 request object 本身扩展
  - 下一步：
    - 若继续污染线，只能继续下沉到：
      1. selector=2 stack request-args 下沉后的 lower state
      2. hidden handle / sidecar family
      3. `resource+0x400d0` / `record+0x1b8` / `process+0x203fc`
         registry / accepted-state family

- 时间：2026-06-19 01:15:47 +0800
  - 目标：在长期 loop 的 `Carrier` 阶段，把本轮唯一假设从泛化的
    “stack request-args / sidecar / registry 三选一”
    收紧成一个更具体的 bridge family。
  - 动作：
    - 复查并统一引用：
      - `mps/ANE/experiments/results/bootkc_memory_map_request_bridge_note.md`
      - `mps/ANE/experiments/results/bootkc_request_pair_roles_probe.md`
      - `mps/ANE/experiments/results/request_lowering_static_bridge_note.md`
    - 同步更新：
      - `docs/ane_state.md`
      - `docs/ane_next.md`
  - 证据：
    - 静态已共同确认：
      1. `InitialChecks`
         写：
         `additional_params+0x60 = resource`
         `additional_params+0x68 = process`
      2. `ANERequest::init(...)`
         复制：
         `request+0x28 = resource`
         `request+0x30 = process`
      3. 后续 firmware send / builder
         继续按 `{resource, process}` 消费这对值
    - 对应文件：
      - `bootkc_memory_map_request_bridge_note.md`
      - `bootkc_request_pair_roles_probe.md`
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - 当前 `Carrier` 阶段的最具体上层 bridge
      已不再是“普通 request-local 字段”，
      而是：
      `additional_params+0x60/+0x68 -> request+0x28/+0x30`
      这条 `{resource, process}` pair bridge
    - 但长期目标仍未完成；
      还没有证明这条 pair 本身就是最终 carrier，
      也没有证明更低 registry / accepted-state family 可控
  - 下一步：
    - 下一轮若继续 `Carrier`，
      本轮唯一假设应围绕：
      `{resource, process}` pair bridge
      与更低
      `resource+0x400d0 / record+0x1b8 / process+0x203fc`
      的接缝，而不是回到 request-local 层

- 时间：2026-06-19 01:21:47 +0800
  - 目标：确认 `{resource, process}` pair bridge
    是否至少在当前 user-space request object 内发生可见变化。
  - 动作：
    - 在
      `mps/ANE/experiments/ane_runtime_rehydrate_probe.m`
      增加 request raw-memory 辅助插点
    - 重编并运行：
      `./ane_runtime_rehydrate_probe --case same_request_after_eval_map --csv ../.ane_runs/csv/same_request_after_eval_map_20260619_pair.csv`
    - 对比：
      `pre_eval_raw` /
      `post_eval_raw` /
      `post_map_raw`
  - 证据：
    - `mps/ANE/.ane_runs/csv/same_request_after_eval_map_20260619_pair.csv`
    - 关键事实：
      - 同一个 request 的 raw `memory_summary` 在
        `eval` 前后和 `map -> 0x12` 后都完全不变
      - `memory_summary head`
        里对应 offset
        `0x28` / `0x30`
        的两个 qword 也未变化
      - 同时：
        `evaluateWithQoS... = 1`
        后，
        `mapIOSurfacesWithRequest... = 0x12`
  - 结论：
    - 本轮阶段性 verdict：`falsified`
    - 当前没有证据支持：
      `eval` 会在 user-space request object 内直接改写
      `{resource, process}` pair
    - 因而 `{resource, process}` pair bridge
      仍是当前最具体的上层 bridge，
      但真正 carrier 更可能发生在它下沉后的
      hidden sidecar / registry / accepted-state family，
      而不是 request object 内这两个可见 qword
  - 下一步：
    - 下一轮若继续 `Carrier`，
      只能继续压
      `{resource, process}` pair
      与
      `resource+0x400d0 / record+0x1b8 / process+0x203fc`
      的接缝

- 时间：2026-06-19 01:27:21 +0800
  - 目标：在 `Carrier` 阶段把
    `{resource, process}` pair bridge
    之后的下压目标从泛化的三选一
    收窄到一个唯一 family。
  - 动作：
    - 复查并统一引用：
      - `bootkc_request_pair_roles_probe.md`
      - `bootkc_memory_map_request_bridge_note.md`
      - `process_state_flag_note.md`
      - `bootkc_resource_gate_indirect_callee_probe.md`
      - `docs/ane_state.md` 里关于
        `resource+0x400d0`
        `record+0x1b8`
        `process+0x203fc`
        的既有结论
    - 更新：
      - `docs/ane_state.md`
      - `docs/ane_next.md`
  - 证据：
    - `{resource, process}` pair bridge
      已静态确认进入更低 send / firmware 路
    - `process+0x203fc`
      当前更像 load-type / recreate gate consumer
    - `record+0x1b8`
      当前更像 replay / refresh consumer
    - `resource+0x400d0`
      仍保留明确 first-author / materializer gap
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - 当前 `Carrier` 阶段的唯一下压目标
      已正式收窄成：
      `resource+0x400d0`
      first-author / materializer gap
    - 下一轮不再做
      `resource+0x400d0 / record+0x1b8 / process+0x203fc`
      的并列三选一
  - 下一步：
    - 继续 `Carrier` 时，
      直接围绕
      `resource+0x400d0`
      的 first-author / materializer
      做最小静态和 runtime probe

- 时间：2026-06-19 01:37:21 +0800
  - 目标：用当前机器重新验证
    `resource+0x400d0`
    first-author gap，
    并判断下一轮是否还值得停留在 visible helper-depth。
  - 动作：
    - 因系统 Python 被 PEP 668 限制，
      在仓库内创建实验虚拟环境：
      `.venv-capstone`
    - 安装本地实验依赖：
      `capstone`
    - 运行：
      `./.venv-capstone/bin/python mps/ANE/experiments/ane_bootkc_resource_gate_first_author_probe.py --csv /Volumes/2T/pymss/mps/ANE/.ane_runs/csv/ane_bootkc_resource_gate_first_author_probe_20260619.csv`
    - 复查：
      - `bootkc_resource_gate_preinit_boundary_probe.md`
      - `bootkc_resource_gate_host_stack_probe.md`
      - `bootkc_resource_gate_two_hop_helper_probe.md`
  - 证据：
    - `mps/ANE/.ane_runs/csv/ane_bootkc_resource_gate_first_author_probe_20260619.csv`
    - 关键结果：
      - constructor zero 只到 `0x40070`
      - visible load copy 只到 `0x40090..0x400a0`
      - visible mutable setup 只写：
        `0x400d8`
        `0x400e0`
      - target-covering store 仍只有：
        `ANEProgramResource::free -> clear resource+0x400d0`
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - `resource+0x400d0`
      first-author gap
      已在当前机器上重新验证，
      不再只是历史 note
    - 结合既有
      `preinit_boundary`
      `host_stack`
      `two_hop_helper`
      结果，
      下一轮不要再把假设放在
      visible direct/bulk/helper-depth/visible HAL
      这些面上
  - 下一步：
    - 若继续 `Carrier`，
      直接把唯一假设收紧为：
      missing first author
      位于更深 registration / materializer helper
      或更低 runtime-owned phase

- 时间：2026-06-19 01:43:13 +0800
  - 目标：把
    `resource+0x400d0`
    的 current-machine live negative
    从单一 `first_author` probe
    扩展到 visible host surface 级别。
  - 动作：
    - 用同一个
      `.venv-capstone`
      继续运行：
      - `ane_bootkc_resource_gate_preinit_boundary_probe.py`
      - `ane_bootkc_resource_gate_host_stack_probe.py`
    - 处理 `host_stack` 运行前的
      `/tmp/KMUtilProducts`
      冲突后重跑
  - 证据：
    - `mps/ANE/.ane_runs/csv/ane_bootkc_resource_gate_preinit_boundary_probe_20260619.csv`
    - `mps/ANE/.ane_runs/csv/ane_bootkc_resource_gate_host_stack_probe_20260619.csv`
    - 关键事实：
      - `process_create_cold`
        先读 `[resource+0x400d0]`
        null 分支直接跳走，
        不 visible init registry
      - H16：
        direct stores 仍只有
        `free -> clear`
      - HAL：
        direct load/store/bulk/inline author
        对 `resource+0x400d0`
        全为 0
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - `resource+0x400d0`
      missing first author
      现在已被 current-machine 证据推进到：
      不在 visible H16 direct/bulk surface，
      不在 visible HAL half，
      `process_create_cold`
      也只消费预先存在的 registry
    - 这意味着下一轮若继续 `Carrier`，
      不应再继续扫 current visible host surface
  - 下一步：
    - 把唯一假设正式收紧成：
      missing first author
      位于更低 runtime-owned phase
      或 daemon/service-side bring-up side effect

- 时间：2026-06-19 01:48:44 +0800
  - 目标：在当前机器证据基础上，决定
    `Carrier` 阶段
    下一轮唯一优先窗口到底是
    runtime-owned phase
    还是
    daemon/service-side bring-up。
  - 动作：
    - 复查：
      - `daemon_load_prereply_window_note.md`
      - `runtime_lower_next_layer_note.md`
      - 本轮新跑的
        `first_author`
        `preinit_boundary`
        `host_stack`
        CSV
    - 更新：
      - `docs/ane_state.md`
      - `docs/ane_next.md`
  - 证据：
    - `resource+0x400d0`
      missing first author
      当前已被 current-machine 证据推进到：
      不在 visible H16 direct/bulk/helper-depth，
      不在 visible HAL，
      `process_create_cold`
      也只消费预先存在 registry
    - `daemon_load_prereply_window_note.md`
      已明确：
      user-side request / IOSurface
      构造发生在 `loadWithQoS/loadModel`
      success reply 之后，
      因而更高价值窗口在 pre-reply bring-up
    - `runtime_lower_next_layer_note.md`
      已明确：
      default receive/response 与 typed completion
      更像 bookkeeping，
      不是最强 author 面
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - `Carrier` 阶段下一轮唯一优先窗口
      现在应正式切到：
      daemon/service-side pre-reply bring-up
    - `runtime-owned phase`
      仍是备选下一层，
      但优先级落后于 pre-reply bring-up
  - 下一步：
    - 下一轮若继续长期目标，
      直接围绕
      `loadModel/createProgramInstance`
      成功 reply 之前的 bring-up / materialization
      窗口做最小 probe

- 时间：2026-06-19 02:10:18 +0800
  - 目标：把
    `daemon/service-side pre-reply bring-up`
    从优先窗口推进成 current-machine live CSV 证据。
  - 动作：
    - 直接运行：
      `python3 mps/ANE/experiments/ane_daemon_static_probe.py`
    - 刷新：
      - `ane_daemon_program_create_state_chain.csv`
      - `ane_daemon_load_reply_chain.csv`
      - `ane_daemon_static_probe_summary.csv`
  - 证据：
    - `mps/ANE/.ane_runs/csv/ane_daemon_program_create_state_chain.csv`
    - `mps/ANE/.ane_runs/csv/ane_daemon_load_reply_chain.csv`
    - `mps/ANE/.ane_runs/csv/ane_daemon_static_probe_summary.csv`
    - 当前机器关键事实：
      1. `loadModel` success reply
         只在
         `createProgramInstanceForModel...`
         成功后才读/回传
         `programHandle/intermediateBufferHandle/queueDepth`
      2. `createProgramInstanceForModel...`
         不是单步骤，
         而是：
         create stage
         -> optional prepare stage
         -> family-4 / family-5 failure normalization
         -> settle 后 metadata writeback
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - 当前长期目标在 `Carrier` 阶段的最佳窗口
      已从抽象的
      `daemon/service-side pre-reply bring-up`
      进一步收紧成：
      `_ANEProgramForLoad createProgramInstanceForModel...`
      内部的 create/prepare pre-reply state machine
  - 下一步：
    - 下一轮若继续长期目标，
      唯一假设应围绕：
      `createProgramInstanceForModel...`
      成功前到底还缺哪一层 lower materialization /
      accepted-state coherence

- 时间：2026-06-19 07:07:02 +0800
  - 目标：确认 plain daemon
    `createProgramInstanceForModel...`
    visible state machine
    在 create/prepare 之外
    是否还存在额外 publish gate
  - 动作：
    - 直接运行：
      `python3 mps/ANE/experiments/ane_daemon_program_lower_gate_join.py`
    - 读取：
      - `mps/ANE/.ane_runs/csv/ane_daemon_program_create_state_chain.csv`
      - `mps/ANE/.ane_runs/csv/ane_services_program_create_chain.csv`
      - `mps/ANE/.ane_runs/csv/ane_services_program_vtable_chain.csv`
      - `mps/ANE/.ane_runs/csv/ane_services_program_runtime_chain.csv`
    - 生成：
      - `mps/ANE/.ane_runs/csv/ane_daemon_program_lower_gate_join.csv`
      - `mps/ANE/.ane_runs/json/ane_daemon_program_lower_gate_join_verdict_20260619.json`
  - 证据：
    - join 结果当前机器固定为 4 行：
      1. `create`
         -> `selector 3 / _ANEServicesProgramCreate`
      2. `post_create`
         -> `program.programInstance != nil`
         + `skipPreparePhase`
      3. `prepare`
         -> `selector 4 / _ANEServicesProgramPrepare`
      4. `destroy_on_prepare_failure`
         -> `selector 6 / _ANEServicesProgramDestroy`
    - join 中未出现
      create/prepare 成功
      与 metadata writeback
      之间的额外 visible daemon-side publish gate
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - 当前 `Carrier` 阶段可再收紧一层：
      visible daemon plain-load
      的剩余 lower-control gap
      已不能再建模成
      create/prepare 之外的额外 publish gate
    - 剩余 accepted-state / publish coherence
      只能继续下沉到：
      `selector 4 prepare`
      内部，
      或更低 runtime-owned materialization phase
  - 下一步：
    - 下一轮若继续长期目标，
      先用 IDA 或更小 probe
      直接拆
      `selector 4 / _ANEServicesProgramPrepare`
      内部的 decisive gate /
      accepted-state publish /
      materializer helper

- 时间：2026-06-19 07:16:52 +0800
  - 目标：确认
    visible selector-4 prepare
    与
    `prepareChainingRequest...`
    是否已经触到
    final accepted-state author，
    还是都还只是 wrapper/XPC 层
  - 动作：
    - 汇总当前 machine-local 证据：
      - `mps/ANE/.ane_runs/csv/ane_services_program_runtime_chain.csv`
      - `mps/ANE/.ane_runs/csv/ane_daemon_program_lower_gate_join.csv`
      - `mps/ANE/experiments/results/selector4_prepare_state_boundary_note.md`
      - `mps/ANE/experiments/results/current_control_layer_blocker_note.md`
    - 生成：
      - `mps/ANE/.ane_runs/json/selector4_prepare_boundary_verdict_20260619.json`
    - 追加 IDA 窄查：
      `-[_ANEProgramForLoad prepareChainingRequest:qos:qIndex:statsMask:error:]`
      (`0x1000081dd`)
  - 证据：
    - selector-4 current-machine 事实：
      1. 是
         `wrapper+0x98`
         的 first visible writer
      2. success 会清
         `payload+0xd98`
         并回写
         `payload+0xd78..0xd97`
      3. 但 raw selector-4
         在 visible handle / queue-depth patch
         后仍稳定
         `0xe00002c2`
    - `prepareChainingRequest...`
      current-machine IDA 事实：
      1. 不做
         publish /
         accepted-state /
         result writeback
      2. 只是
         chaining request validate
         + descriptor 构造
         + XPC 发
         `prepareChainingWithModel:options:chainingReq:qos:withReply:`
      3. 可见 decisive gate
         只剩
         `validate`
         与 daemon reply code
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - selector-4 prepare
      不是 final accepted-state author；
      `prepareChainingRequest...`
      也不是
    - 当前 `Carrier` 阶段最强下一窗口
      已正式切到：
      daemon-side
      `-[_ANEServer prepareChainingWithModel:options:chainingReq:qos:withReply:]`
      或其下方更低 accepted-state /
      materialization gate
  - 下一步：
    - 下一轮若继续长期目标，
      直接围绕
      `0x100021e17`
      做窄 IDA / static join，
      判断 daemon 端
      是不是已经拥有当前缺失的 decisive gate

- 时间：2026-06-19 07:20:47 +0800
  - 目标：确认
    daemon-side
    `-[_ANEServer prepareChainingWithModel:options:chainingReq:qos:withReply:]`
    是否已经触到
    final accepted-state / publish author
  - 动作：
    - 对
      `0x100021e17`
      做 current-machine IDA 窄查
    - 结合现有：
      - `mps/ANE/experiments/ane_client_runtime_surface_probe.m`
      - `mps/ANE/experiments/results/ane_private_api_map.md`
      - `mps/ANE/experiments/ane_daemon_static_probe.py`
    - 生成：
      - `mps/ANE/.ane_runs/json/daemon_preparechaining_boundary_verdict_20260619.json`
  - 证据：
    - 当前机器确认该函数只做：
      - XPC audit
      - QoS->queueIdx
      - per-QoS semaphore 30s timeout
      - `_ANEProgramCache programForConnection:model:bundleID:`
      - 调
        `[prog prepareChainingRequest:qos:qIndex:statsMask:error:]`
    - 失败时只会：
      - timeoutError
      - 或 remove cached program 后转发 `(ok,error)`
    - 它不做：
      - accepted-state author
      - publish
      - reply payload writeback
      - programHandle/intermediateBuffer/queueDepth 序列化
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - daemon-side prepare handler
      也不是 final accepted-state author，
      而只是 server-side XPC/semaphore/cache gate
    - 当前 `Carrier` 阶段最强下一窗口
      已正式切到：
      delegated program/device path
      的真实实现所在二进制
      （优先 `ANEServices.framework` /
      `ANECompiler.framework`）
  - 下一步：
    - 下一轮若继续长期目标，
      直接打开或复用
      `ANEServices.framework` /
      `ANECompiler.framework`
      的 IDB，
      追 delegated
      `prepareChainingRequest`
      真身的 IOConnect / accepted-state /
      materialization path
    - 补充：
      本轮主线程在收尾时尝试
      `ida-pro-mcp.idb_list`
      返回
      `Transport closed`；
      因而下一轮开做前
      先恢复 IDA transport / session

- 时间：2026-06-19 07:31:00 +0800
  - 目标：确认 delegated binary
    (`ANEServices.framework` /
    `ANECompiler.framework`)
    继续静态下钻的直接 blocker
    到底是缺 binary
    还是当前会话 transport / session
  - 动作：
    - 检查路径是否存在：
      - `ANECompiler.i64`
      - `AppleNeuralEngine.i64`
      - `ANEServices`
    - 检查本地进程：
      - `idalib-mcp --stdio`
      - `ida_pro_mcp.idalib_server`
    - 本地执行：
      `idalib-mcp --help`
    - 当前会话里重试：
      - `ida-pro-mcp.idb_list`
      - `ida-pro-mcp.idb_open(...)`
    - 生成：
      - `mps/ANE/.ane_runs/json/ida_transport_closed_evidence_20260619.json`
  - 证据：
    - binary / `.i64` 路径都存在
    - `idalib-mcp --stdio`
      与多个
      `ida_pro_mcp.idalib_server`
      进程存活
    - `idalib-mcp --help`
      正常返回
    - 但当前会话中的
      `idb_list`
      与
      `idb_open(...)`
      统一返回
      `Transport closed`
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - 当前 delegated binary
      静态下钻的直接 blocker
      已精确收紧为：
      当前会话的
      `ida-pro-mcp` transport / session
    - 这不影响当前长期结论：
      server-side prepare handler
      不是 final author
  - 下一步：
    - 下一轮若继续长期目标，
      首先恢复
      `ida-pro-mcp`
      transport / session，
      再直接进入
      `ANEServices.framework` /
      `ANECompiler.framework`
      的 delegated 真身

- 时间：2026-06-19 07:36:00 +0800
  - 目标：确认 delegated binary 的 blocker
    是否还包含
    SIP / framework 路径 / binary 可读性
  - 动作：
    - 检查：
      `/Volumes/2T/dsc_arm64e_extract/.../ANEServices`
      的 `file` / `otool -hv`
    - 复制到：
      `/private/tmp/ANEServices_arm64e`
    - 对副本重试：
      `ida-pro-mcp.idb_open`
    - 生成：
      - `mps/ANE/.ane_runs/json/aneservices_local_copy_ready_20260619.json`
  - 证据：
    - `ANEServices`
      是可直接复制的 292K arm64e Mach-O
    - 副本
      `/private/tmp/ANEServices_arm64e`
      仍可被
      `file`
      `otool -hv`
      正常读取
    - 但当前会话里对该副本的
      `ida-pro-mcp.idb_open`
      仍统一报
      `Transport closed`
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - delegated binary 的继续静态下钻
      已不再受
      SIP / framework 路径 / binary 可读性
      限制
    - 唯一剩余执行 blocker
      仍是当前会话的
      `ida-pro-mcp` transport / session
  - 下一步：
    - 下一轮若继续长期目标，
      transport 一旦恢复，
      直接打开
      `/private/tmp/ANEServices_arm64e`
      追
      `programInstance->vtable[+8]`
      delegated 真身

- 时间：2026-06-19 07:45:00 +0800
  - 目标：在不依赖当前会话
    `ida-pro-mcp`
    的前提下，
    直接把
    `programInstance->vtable[+8]`
    映射到本地
    `ANEServices`
    具体实现
  - 动作：
    - 复用现有：
      - `program_runtime_chain_note.md`
      - `chaining_prepare_write_surface_note.md`
    - 本地对
      `/private/tmp/ANEServices_arm64e`
      运行：
      - `nm -nm`
      - `otool -tvV`
    - 生成：
      - `mps/ANE/.ane_runs/json/selector9_delegated_impl_local_macho_verdict_20260619.json`
  - 证据：
    - `programInstance` vtable slot `+0x8`
      由现有 runtime-chain
      已固定到
      `_ANEServicesProgramChainingPrepare`
    - 本地 `nm`
      命中：
      - `_ANEServicesProgramChainingPrepare`
      - `ANE::ANEServicesDevice::ANE_ProgramChainingPrepare`
    - 本地 `otool`
      直接显示：
      `_ANEServicesProgramChainingPrepare`
      调
      `ANE::ANEServicesDevice::ANE_ProgramChainingPrepare`
    - 同一条反汇编证据链
      又确认该 C++ 实现发：
      selector 9
      `IOConnectCallStructMethod`
      （outer input `0xae30`，output `0x18`）
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - delegated 真身是不是 `ANEServices`
      这一层已落死，
      不再依赖 IDA MCP
    - 当前 `Carrier` 阶段最强下一窗口
      已继续下沉到：
      selector-9
      更低 driver / bootkc
      accepted-state / materialization semantics
  - 下一步：
    - 下一轮若继续长期目标，
      不要再重复证明 delegated 真身；
      直接围绕
      `ANEClientDevice::programChainingPrepare`
      /
      `ANEDriver::ANE_ProgramChainingPrepare`
      /
      `ANEHWDevice::ANE_ProgramChainingPrepare(_gated)`
      去压剩余 accepted-state 语义
  - 补充：
    - 子代理进一步补实了地址级事实：
      - `_ANEServicesProgramChainingPrepare`
        = `0x19e6a63cc`
      - `ANE::ANEServicesDevice::ANE_ProgramChainingPrepare`
        = `0x19e69d668`
      - wrapper 在
        `0x19e6a6a08`
        调 C++ 实现
      - C++ 实现在
        `0x19e69d768`
        发 selector #9
        `IOConnectCallStructMethod`

- 时间：2026-06-19 07:52:00 +0800
  - 目标：确认恢复后的
    `ida-pro-mcp`
    session
    是否真正稳定可查询
  - 动作：
    - 主线程直接调用：
      - `idb_list`
      - `server_health(aneservices_arm64e)`
      - `analyze_function(0x19e69d668)`
      - `xref_query`
      - `disasm`
    - 生成：
      - `mps/ANE/.ane_runs/json/ida_session_unstable_evidence_20260619.json`
  - 证据：
    - `idb_list`
      已出现：
      `aneservices_arm64e`
      `aned_arm64e`
    - `server_health`
      对
      `aneservices_arm64e`
      返回 `status=ok`
    - 但真实查询会立刻分裂：
      - `analyze_function`
        -> `Worker for session ... is not reachable`
      - `xref_query/disasm`
        -> `Session not found`
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - 当前 IDA blocker
      已从粗粒度
      `Transport closed`
      收紧成：
      session reachability unstable
    - 这不影响已经拿到的
      `ANEServices` delegated 真身结论
  - 下一步：
    - 下一轮若继续长期目标，
      要么继续走本地 Mach-O / probe 路线
      压 selector-9 更低语义，
      要么先专门修复
      session reachability

- 时间：2026-06-19 08:05:00 +0800
  - 目标：继续把 selector-9 的 lower gate
    从 delegated 真身
    压到 bootkc 早期验证窗口
  - 动作：
    - 新建轻量环境：
      `.venv-capstone`
    - 安装：
      `capstone`
    - 重跑：
      - `ane_bootkc_selector9_bridge_probe.py`
      - `ane_bootkc_chaining_prepare_args_bridge_probe.py`
      - `ane_bootkc_chaining_prepare_payload_use_scan.py`
    - 生成：
      - `mps/ANE/.ane_runs/json/selector9_bootkc_gate_window_verdict_20260619.json`
  - 证据：
    - selector-9 shim
      校验 outer input size = `0xae30`
      后 tail-branch 到
      `ANEClientDevice::programChainingPrepare`
    - `ANEClientDevice::programChainingPrepare`
      在 mapped payload 上新增写：
      - `+0x30 <- self`
      - `+0x3948` shared-event object rebuild
    - `ANEHWDevice::ANE_ProgramChainingPrepare_gated`
      的 early validation
      读取/校验：
      - `0x38`
      - `0x3950`
      - `0xa614`
      - `0x3040`
    - post-validation
      继续消费：
      - `0x30`
      - `0x10`
      - `0xae28`
      - `0xae18`
      - `0xae20`
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - 当前 blocker
      已不再是 delegated 真身定位，
      而是
      `ANEHWDevice::ANE_ProgramChainingPrepare_gated`
      中 selector-9 字段语义
  - 下一步：
    - 下一轮若继续长期目标，
      直接区分：
      哪些字段只是 size/count guard，
      哪些字段才真正参与
      accepted-state / materialization

- 时间：2026-06-19 08:12:00 +0800
  - 目标：把 selector-9 payload
    字段族分成
    guard-cluster
    与 materialization-cluster
  - 动作：
    - 汇总 fresh：
      - `ane_bootkc_selector9_bridge_probe.csv`
      - `ane_bootkc_chaining_prepare_args_bridge_probe.csv`
      - `ane_bootkc_chaining_prepare_payload_use_scan.csv`
    - 生成：
      - `mps/ANE/.ane_runs/json/selector9_field_family_partition_verdict_20260619.json`
  - 证据：
    - early validation
      明确读+比较：
      `0x38 / 0x3950 / 0xa614 / 0x3040`
    - `0x30`
      先在
      `ANEClientDevice::programChainingPrepare`
      被补写成 `self`
      再进入 post-validation helper
    - `0xae18 / 0xae20 / 0xae28`
      只在 post-validation
      helper / output-seeding
      路径出现
    - `0x3944 / 0x3948`
      围绕 shared-event object rebuild
      与 later output seed
      出现
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - 当前最优拆分是：
      - guard-cluster:
        `0x38 / 0x3950 / 0xa614 / 0x3040`
      - materialization-cluster 候选:
        `0x30 / 0xae18 / 0xae20 / 0xae28 / 0x3944 / 0x3948`
  - 下一步：
    - 下一轮若继续长期目标，
      不再追整块 selector-9 payload；
      只追
      `0x30`
      vs
      `0xae18 / 0xae20 / 0xae28`

- 时间：2026-06-19 08:18:00 +0800
  - 目标：给 materialization-cluster
    再排一个优先级，
    决定下一轮先追哪一簇
  - 动作：
    - 复用：
      - `ane_bootkc_chaining_prepare_args_bridge_probe.csv`
      - `ane_bootkc_chaining_prepare_payload_use_scan.csv`
    - 生成：
      - `mps/ANE/.ane_runs/json/selector9_materialization_priority_verdict_20260619.json`
  - 证据：
    - `0x30`
      在 early validation 后
      直接进入
      `ANE_PowerOn_gated`
      与
      `findClient`
    - `0xae18 / 0xae20`
      直接喂给
      deeper helper
      与
      `AllocateSharedMemorySurface`
    - `0xae28`
      会和 deeper resource-owned qword
      比较并可能被清零
    - `0x3040 / 0x3950`
      更像 alloc_count / shape
      字段
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - 当前 materialization-cluster
      优先级已收紧成：
      1. `0x30`
      2. `0xae18 / 0xae20 / 0xae28`
  - 下一步：
    - 下一轮若继续长期目标，
      先只追
      `0x30`

- 时间：2026-06-19 08:24:00 +0800
  - 目标：把 selector-9 的
    `0x30`
    单独定性
  - 动作：
    - 汇总：
      - `bootkc_selector9_bridge_note.md`
      - `driver_client_context_note.md`
      - fresh selector-9 bridge/args/payload CSV
    - 生成：
      - `mps/ANE/.ane_runs/json/selector9_0x30_role_verdict_20260619.json`
  - 证据：
    - `0x30`
      在
      `ANEClientDevice::programChainingPrepare`
      中被补写成
      `self / ANEClientDevice*`
    - 进入 bootkc 后，
      `0x30`
      在 output construction 之前
      就先进入：
      - `ANE_PowerOn_gated`
      - `findClient`
    - 所以它不是 mere output helper
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - `0x30`
      当前更像
      live client/power/resource lookup key
  - 下一步：
    - 下一轮若继续长期目标，
      正式切到
      `0xae18 / 0xae20 / 0xae28`

- 时间：2026-06-19 08:31:00 +0800
  - 目标：给
    `0xae18 / 0xae20 / 0xae28`
    再排一个优先级
  - 动作：
    - 复用：
      - `ane_bootkc_chaining_prepare_args_bridge_probe.csv`
      - `ane_bootkc_chaining_prepare_payload_use_scan.csv`
      - `chaining_prepare_write_surface_note.md`
    - 生成：
      - `mps/ANE/.ane_runs/json/selector9_ae_family_role_verdict_20260619.json`
  - 证据：
    - `0xae18 / 0xae20`
      会一起进入
      deeper helper
      与
      `AllocateSharedMemorySurface`
    - `0xae28`
      会被比较、
      可能被清零，
      也会 later output seed
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - `0xae18 / 0xae20`
      当前比
      `0xae28`
      更像真正的 resource/materialization 候选
  - 下一步：
    - 下一轮若继续长期目标，
      只追
      `0xae18 / 0xae20`

- 时间：2026-06-19 08:38:00 +0800
  - 目标：把
    `0xae18 / 0xae20`
    单独定性
  - 动作：
    - 复用：
      - `ane_bootkc_chaining_prepare_args_bridge_probe.csv`
      - `ane_bootkc_chaining_prepare_payload_use_scan.csv`
      - `bootkc_chaining_prepare_args_bridge_note.md`
      - `program_runtime_chain_note.md`
    - 生成：
      - `mps/ANE/.ane_runs/json/selector9_ae1820_role_verdict_20260619.json`
  - 证据：
    - `0xae18 / 0xae20`
      在 ANEServices
      中来自
      `program+0xa0 / +0xa8`
    - 进入 bootkc 后，
      两者一起进入
      deeper helper
    - 紧接着又一起种进
      `AllocateSharedMemorySurface`
    - 未见它们像 `0xae28`
      一样参与 compare-and-clear
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - `0xae18 / 0xae20`
      当前最像 paired
      resource/materialization input family
  - 下一步：
    - 下一轮若继续长期目标，
      直接追
      deeper helper /
      `AllocateSharedMemorySurface`
      对这对子字段的语义

- 时间：2026-06-19 08:45:00 +0800
  - 目标：把
    `0xae18 / 0xae20`
    再定硬一层
  - 动作：
    - 复用：
      - `bootkc_chaining_prepare_args_bridge_note.md`
      - `ane_services_chaining_prepare_write_surface_probe.py`
      - fresh selector-9 CSV
    - 生成：
      - `mps/ANE/.ane_runs/json/selector9_ae1820_semantics_verdict_20260619.json`
  - 证据：
    - `0xae18 / 0xae20`
      先来自
      `program+0xa0 / +0xa8`
    - 进入 bootkc 后，
      它们会一起进入
      deeper helper
      与
      `AllocateSharedMemorySurface`
    - 未见它们退化成
      mere late output-bookkeeping 参数
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - `0xae18 / 0xae20`
      已可视为 paired
      lower resource/materialization inputs
  - 下一步：
    - 下一轮若继续长期目标，
      直接追
      `program+0xa0 / +0xa8`
      到底是什么具体资源语义

- 时间：2026-06-19 08:52:00 +0800
  - 目标：把
    `program+0xa0 / +0xa8`
    的问题边界再收紧一层
  - 动作：
    - 复用：
      - `bootkc_chaining_prepare_args_bridge_note.md`
      - fresh selector-9 CSV
      - `ane_bootkc_selector9_mutation_surface_probe.csv`
    - 生成：
      - `mps/ANE/.ane_runs/json/program_a0_a8_tuple_semantics_boundary_20260619.json`
  - 证据：
    - `program+0xa0 / +0xa8`
      是 stable carried inputs，
      不是 bridge mutation slot
    - 它们会成对进入
      deeper helper
      与
      `AllocateSharedMemorySurface`
    - 但当前仍不能唯一分辨
      它们到底是
      handle+size
      pointer+size
      还是别的 paired resource tuple
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - 当前剩余问题
      已只剩
      `AllocateSharedMemorySurface`
      的接口语义
  - 下一步：
    - 下一轮若继续长期目标，
      只追
      `AllocateSharedMemorySurface`

- 时间：2026-06-19 09:00:00 +0800
  - 目标：把
    `AllocateSharedMemorySurface`
    的边界再收紧一层
  - 动作：
    - 用 `nm -nm /tmp/KMUtilProducts/BootKernelCollection.kc`
      锁定
      `AllocateSharedMemorySurface`
      overload
    - 结合 selector-9 callsite
      `0xfffffe00092cb92c`
      生成：
      - `mps/ANE/.ane_runs/json/allocatesharedmemorysurface_overload_boundary_20260619.json`
  - 证据：
    - 当前命中的 overload 是：
      `ANEHWDevice::AllocateSharedMemorySurface(unsigned long long, ANESharedMemorySurfaceParams **, bool, unsigned int, bool, bool, unsigned int, bool, unsigned long long)`
    - 所以问题空间
      已不再是任意 paired resource tuple，
      而是
      `0xae18 / 0xae20`
      如何映射到这个 overload
      的前导 `u64` / scalar 参数位
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - 当前剩余问题
      已进一步收紧到：
      callsite 参数位映射
  - 下一步：
    - 下一轮若继续长期目标，
      直接追
      `0xfffffe00092cb92c`
      调点前的寄存器/栈参数映射

- 时间：2026-06-19 09:08:00 +0800
  - 目标：把
    `AllocateSharedMemorySurface`
    调点边界再收紧一层
  - 动作：
    - 复用：
      - `ane_bootkc_chaining_prepare_args_bridge_probe.csv`
      - bootkc `nm`
    - 生成：
      - `mps/ANE/.ane_runs/json/allocatesharedmemorysurface_callsite_mapping_boundary_20260619.json`
  - 证据：
    - 当前命中的 overload 已固定
    - callsite 前：
      - `0xae18 -> x7`
      - `0xae20 -> w8`
    - 这足以确认
      它们属于 late argument material，
      但还不足以恢复全套寄存器/栈位
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - 当前剩余问题
      已收紧成
      callsite 参数重建
  - 下一步：
    - 下一轮若继续长期目标，
      直接重建
      `0xfffffe00092cb92c`
      调点前的寄存器/栈参数位

- 时间：2026-06-19 09:16:00 +0800
  - 目标：把
    `AllocateSharedMemorySurface`
    的剩余问题
    压成一个最小动作
  - 动作：
    - 汇总现有边界：
      - overload 已固定
      - `0xae18 -> x7`
      - `0xae20 -> w8`
    - 生成：
      - `mps/ANE/.ane_runs/json/allocatesharedmemorysurface_precall_reconstruction_boundary_20260619.json`
  - 证据：
    - 当前已有事实
      已足够证明：
      pair 属于 late callsite argument material
    - 但仍不足以恢复
      `0xfffffe00092cb92c`
      前的完整寄存器/栈位
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - 当前最小剩余问题
      已收紧成：
      pre-call register/stack reconstruction
  - 下一步：
    - 下一轮若继续长期目标，
      只写/只跑
      一个 focused reconstruction probe

- 时间：2026-06-19 09:25:00 +0800
  - 目标：把
    `0xae18 / 0xae20`
    到 overload 参数位
    的边界再收紧一层
  - 动作：
    - 复用：
      - `allocatesharedmemorysurface_callsite_mapping_boundary_20260619.json`
      - `allocatesharedmemorysurface_precall_reconstruction_boundary_20260619.json`
    - 生成：
      - `mps/ANE/.ane_runs/json/program_a0_a8_tuple_semantics_boundary_20260619.json`
      - `mps/ANE/.ane_runs/json/allocatesharedmemorysurface_overload_boundary_20260619.json`
      - `mps/ANE/.ane_runs/json/allocatesharedmemorysurface_precall_reconstruction_boundary_20260619.json`
  - 证据：
    - `0xae18 -> x7`
    - `0xae20 -> w8`
    - overload 已固定
    - 仍不足以恢复全套调用位图
  - 结论：
    - 本轮阶段性 verdict：`confirmed`
    - 下一轮应只做
      focused pre-call register/stack reconstruction probe
  - 下一步：
    - 下一轮若继续长期目标，
      直接写/跑
      pre-call reconstruction probe

---

- 2026-06-19 已用 ida-pro-mcp 完成对 `aneservices_arm64e` + `aned_arm64e` 窄下钻：
  - 目标围绕 `_ANEServicesProgramChainingPrepare`（0x19e6a63cc）和 `ANE::ANEServicesDevice::ANE_ProgramChainingPrepare`（0x19e69d668）的 driver-facing 决定性 gate
  - 方法：
    1. `aneservices_arm64e`：decompile + callees + disasm 确认入口1 是验证包装器，入口2 直接 `IOConnectCallStructMethod(conn, selector=9, ...)`
    2. 搜索 `ANEDriver/ANEClientDevice/ANEHWDevice` ProgramChainingPrepare → 不存在
    3. `aned_arm64e`：survey + import check → 零 IOConnect 符号；aned 不参与 selector 9 路径
  - 结论：用户态 selector 9 ProgramChainingPrepare 路径已被完全封死；实际决定性 gate = IOConnect → kernel kext；无隐藏中间层
  - 文档更新：
    - `docs/ane_state.md`：新增 "ProgramChainingPrepare（selector 9）用户态路径已被完全封死" 节
    - `docs/ane_next.md`：更新长期 Loop 状态 + 新增 2026-06-19 条目，明确指出下一轮两个方向（Control 或 kernel）
    - `docs/ane_log.md`：本条目
2026-06-19 08:57:59 +0800 | 目标: 将 `AllocateSharedMemorySurface` callsite 重建从“只知 `0xae18->x7`, `0xae20->w8`”推进到足以排除最简单 `pointer+size` 解释 | 动作: 新增并运行 `mps/ANE/experiments/ane_bootkc_allocatesharedmemorysurface_precall_probe.py`，聚焦 `ANEHWDevice::ANE_ProgramChainingPrepare_gated` 中 `0xfffffe00092cb92c` 前窗口；同时用 `doc-reader` 子代理压文档状态，用 `ida` 子代理验证当前 `aned_bin.i64` 不含目标符号后立即停止 | 证据: `mps/ANE/.ane_runs/csv/ane_bootkc_allocatesharedmemorysurface_precall_probe.csv`; `mps/ANE/.ane_runs/json/allocatesharedmemorysurface_precall_probe_verdict_20260619.json`; 子代理结论确认 `aned_bin.i64` 不含 `AllocateSharedMemorySurface`/callsite，不再在 daemon IDB 上扩散 | 结论: 本轮确认 `x2 = x29-0x78` 为 caller-local `surface params` 栈对象，`x7 <- 0xae18`、`sp+0x4 <- 0xae20`，且 `sp+0x0/0x8/0x10` 在 call 前清零；因此已排除把 `0xae18/0xae20` 直接读成前导 `pointer+size` 的最简单解释，更像 trailing late-argument 的 lower materialization/control tuple | 下一步: 只做 `0xfffffe00092cb92c` 的 trailing ABI slot mapping，判断 `x7` 和 `sp+0x4` 分别落在哪个 formal slot，不再回头追高层 selector-9 叙述
2026-06-19 09:05:25 +0800 | 目标: 将 `0xae18/0xae20` 从“late mixed tuple”进一步精确到 `AllocateSharedMemorySurface` overload 的具体 trailing formal slots | 动作: 先在主线程用 `/tmp/abi_slots.cpp` + `clang++ -target arm64-apple-macos -O0 -S` 建立最小 AArch64 C++ 成员函数 ABI 反馈环，再固化为 `mps/ANE/experiments/ane_arm64_member_call_abi_probe.py` 并生成正式 verdict；同时发起 `reverse-engineer`/`test-runner` 子代理，前者因 shell 环境降级未取到本地证据，后者未提供额外结论，不影响主线程证据链 | 证据: `/tmp/abi_slots.s` 中 caller 明确将第 8/9/10/11 个 user-visible formal 写到 `sp+0 / sp+4 / sp+8 / sp+16`；`mps/ANE/.ane_runs/json/arm64_member_call_abi_probe_verdict_20260619.json`；结合既有 `ane_bootkc_allocatesharedmemorysurface_precall_probe.csv` 中 `x7 <- 0xae18`、`sp+0x4 <- 0xae20` | 结论: `this` 占 `x0`，所以 `0xae18` 对应 overload 的 trailing `unsigned long long` formal，`0xae20` 对应 trailing `int` formal；本轮把这对字段从“late argument material”推进成更精确的 trailing `u64 / int` materialization-control tuple 候选 | 下一步: 只追这对 trailing `u64 / int` tuple 在 lower materialization path 里的具体控制族语义，更像 handle / class / id / state 的哪一种
2026-06-19 09:12:09 +0800 | 目标: 将 trailing `u64 / int` tuple 从 ABI slot 级别再推进到更接近 handle/class/id/state 的控制族语义 | 动作: 新增并运行 `mps/ANE/experiments/ane_bootkc_allocatesharedmemorysurface_early_use_probe.py`，只检查 `AllocateSharedMemorySurface` 本体入口前 80 条指令里的最早参数用途；并用 `searcher` 子代理定位最相关现有 probe/结果，用 `ida` 子代理尝试当前 IDB 可用性（无目标会话即停） | 证据: `mps/ANE/.ane_runs/csv/ane_bootkc_allocatesharedmemorysurface_early_use_probe.csv`; `mps/ANE/.ane_runs/json/allocatesharedmemorysurface_early_use_verdict_20260619.json`; 关键指令为 `mov x24, x7`、`ldr w26, [x29,#0x14]`、`cmp w26,#0`、`cset w6,eq`、`mov x3, x24`、`bl ANEHWDevice::createANESurface` | 结论: 当前机器上，这对 tuple 更像 `identity-bearing u64` + `control-like int`，其中 `u64` 很早被直接带入 `createANESurface`，而 `int` 很早就被压成布尔控制位；因此已进一步远离 `handle + size` 解释，但还不能安全断言 `u64` 就是 registry handle，或 `int` 就是具体 class id | 下一步: 只追 `createANESurface` 对该 `u64` 是 lookup/registry-like handle 还是 opaque resource token，同时看该 `int` 是否对应具体 surface class/mode family
2026-06-19 09:18:18 +0800 | 目标: 继续下钻 `createANESurface` 对 trailing `u64 / int` tuple 的最早用途，判断 `u64` 更像 registry handle 还是 opaque property token | 动作: 新增并运行 `mps/ANE/experiments/ane_bootkc_createanesurface_early_use_probe.py`，只查看 `ANEHWDevice::createANESurface` 入口前 150 条指令；并用 `searcher` 子代理定位相关现有 probe/结果，用 `reverse-engineer` 子代理基于本地现有事实做窄摘要 | 证据: `mps/ANE/.ane_runs/csv/ane_bootkc_createanesurface_early_use_probe.csv`; `mps/ANE/.ane_runs/json/createanesurface_early_use_verdict_20260619.json`; 关键指令为 `mov x20, x3`、`stp w6, w4, [sp,#0x38]`、`mov x0, x20` → `OSNumber::withNumber`，以及同一路径上的 `IOSurfaceWidth` / `IOSurfaceHeight` property key | 结论: 当前最早可见用法里，selector-9 带下来的 `u64` 没有立刻进入 lookup/compare/registry 路径，而是先被装箱并进入 IOSurface property dictionary 构造；paired `int` 继续像 class/mode selector 控制位。因此当前更像 `opaque token/property path + class/mode selector`，但还不能断言后续绝不会再进 registry consumer | 下一步: 只追 boxed `u64` 后续是否进入任何 IOSurface/resource registry consumer，还是一路保持 opaque property token
2026-06-19 09:26:20 +0800 | 目标: 继续追 `createANESurface` 中 boxed `u64` 是否在 `IOSurfaceRoot::createSurface` 前进入任何 registry/lookup consumer | 动作: 新增并运行 `mps/ANE/experiments/ane_bootkc_createanesurface_token_followthrough_probe.py`，扫描 `createANESurface` 全函数里与 `x20/x22`、dictionary/property insertion、`IOSurfaceRoot::createSurface`、以及 lookup/registry 相关的指令与 helper 调用；并用 `searcher` / `reverse-engineer` 子代理压缩现有相关证据 | 证据: `mps/ANE/.ane_runs/csv/ane_bootkc_createanesurface_token_followthrough_probe.csv`; `mps/ANE/.ane_runs/json/createanesurface_token_followthrough_verdict_20260619.json`; 关键链路为 `mov x20, x3` → `OSNumber::withNumber` → `x22` → `mov x2, x22` property insertion → `IOSurfaceRoot::createSurface(task, OSDictionary)`，且 `createSurface` 返回后 `x20` 被新建 IOSurface object 覆盖 | 结论: 到 `IOSurfaceRoot::createSurface` handoff 为止，selector-9 带下来的 boxed `u64` 仍停留在 opaque property-token path，当前没有看到 visible registry/lookup consumer；paired `int` 仍保持 class/mode selector 假设 | 下一步: 只追 boxed token 对应的具体 property key 或 post-create IOSurface mutation path，判断能否把它钉成某个具体 IOSurface/resource field；若仍不能，则考虑剩余 lower-control 语义已落到 visible property construction 之下
2026-06-19 09:34:39 +0800 | 目标: 把 boxed token 从“opaque property token”进一步钉到具体 property key，并确认 post-create mutation 是否继续消费它 | 动作: 直接解出 `createANESurface` 后半段相关 cstring，并对齐 `IOSurfaceRoot::createSurface` / `IOSurface::setValue` 附近的寄存器值流；同时结合子代理给出的本地事实摘要确认 boxed token 的唯一 property key | 证据: `IOSurfaceAllocateFromSuperbuffer` 是 boxed token 对应的 OSDictionary key；`IOSurface::setValue` 的 key 是 `IOSurfaceName`；`x20` 在 `createSurface` 返回后被新建 IOSurface object 覆盖，`x22`（boxed token）此后仅剩 release | 结论: selector-9 带下来的 `u64` 当前最强可见语义是 `IOSurfaceAllocateFromSuperbuffer` 这个 property key 上的 opaque token / option value，不是 visible registry handle；post-create mutation 不再消费它 | 下一步: 判断 `IOSurfaceAllocateFromSuperbuffer` 在当前 ANE 路径里只是 surface-construction option，还是已经是 lower control layer 暴露到可见层的最后 carrier；若仍无更深 visible consumer，就准备“visible property construction 以下”的 blocker package
2026-06-19 09:43:35 +0800 | 目标: 判断 `IOSurfaceAllocateFromSuperbuffer` 是否已经是 selector-9 派生 `u64` 在当前可见层的最后一个 carrier | 动作: 汇总本轮关于 property key、follow-through、post-create mutation 的全部可见证据，形成新的 visibility-boundary verdict，而不再新增同层 probe | 证据: `mps/ANE/.ane_runs/json/iosurface_allocatefromsuperbuffer_visibility_boundary_20260619.json`；已确认 `IOSurfaceAllocateFromSuperbuffer` 是 boxed token 的唯一具体 property key，visible consumer path 止于 `OSDictionary -> IOSurfaceRoot::createSurface`，post-create `IOSurfaceName` 写入不再消费该 token | 结论: 当前可见层里，`IOSurfaceAllocateFromSuperbuffer` 已是 selector-9 派生 `u64` 能抵达的最后一个具体 carrier；剩余 lower-control 语义更可能已经下压到 visible property construction 之下 | 下一步: 准备“visible property construction 以下”的 blocker package，或仅保留一个极小 kernel-side consumer existence probe 来反证当前边界
2026-06-19 09:49:59 +0800 | 目标: 把“visible property construction 以下”整理成正式 blocker package，避免继续在同层无边界深挖 | 动作: 复用仓库既有 blocker note 风格，新建 `mps/ANE/experiments/results/visible_property_construction_blocker_note.md`，系统整理当前层已确认事实、盲区、可声称与不可声称内容 | 证据: `mps/ANE/experiments/results/visible_property_construction_blocker_note.md`；其中明确串起 selector-9 → AllocateSharedMemorySurface → createANESurface → OSDictionary → `IOSurfaceRoot::createSurface` 的完整可见链，以及 `IOSurfaceAllocateFromSuperbuffer` 作为最后一个具体 visible carrier 的结论 | 结论: 当前 visible property construction 已可作为正式 blocker boundary；若无新的 kernel / IOSurface-side consumer 证据，再继续在同层打转的收益很低 | 下一步: 只保留一个极小 kernel-side consumer existence probe 作为最后反证；若无反证，就可基于 blocker package 正式判死这一层并切更低层
2026-06-19 09:57:57 +0800 | 目标: 关闭当前层最后一个极小反证入口，确认 `IOSurfaceAllocateFromSuperbuffer` 是否存在第二个可见 consumer | 动作: 新增并运行 `mps/ANE/experiments/ane_bootkc_iosurface_allocatefromsuperbuffer_xref_probe.py`，扫描当前 H16 visible text 对该 cstring 的 materialization site | 证据: `mps/ANE/.ane_runs/csv/ane_bootkc_iosurface_allocatefromsuperbuffer_xref_probe.csv`; `mps/ANE/.ane_runs/json/iosurface_allocatefromsuperbuffer_xref_verdict_20260619.json`；唯一命中为 `ANEHWDevice::createANESurface+0x1e4` | 结论: `IOSurfaceAllocateFromSuperbuffer` 在当前 visible bootkc 里没有第二个 public consumer；visible property construction 这一层在本机上已正式收口 | 下一步: 不再为这一层追加 probe；按 blocker package 结束当前层，或切向更低 kernel / IOSurface-side 解释层
2026-06-19 09:59:34 +0800 | 目标: 把“当前 bootkc 字面量缺失”与“当前层已收口”之间的表述对齐，避免后续恢复时误判为结论冲突 | 动作: 新增 `mps/ANE/.ane_runs/json/iosurface_allocatefromsuperbuffer_current_bootkc_drift_verdict_20260619.json`，把本机 literal 缺失记录为 version drift 说明，而不是 reopen 当前层 | 证据: drift verdict 明确区分：当前本机 kernelcache literal 扫描未见该字符串，但 project-local carrier/follow-through 证据链仍支持 boxed token visible path 止于 `OSDictionary -> IOSurfaceRoot::createSurface` | 结论: 当前 bootkc 的字面量缺失应视作可见字符串层 drift，不是当前 blocker boundary 的反证 | 下一步: 直接按 blocker package 结束当前 visible property construction 层，或切向更低 kernel / IOSurface-side 解释层
2026-06-19 10:04:49 +0800 | 目标: 把当前 visible property construction 层从 blocker note 提升为正式判死的阶段性交付物 | 动作: 新增 `mps/ANE/experiments/results/visible_property_construction_formal_blocker_package.md`，并把 `ane_next` 阶段从 `Control` 切到 `ExploitOrBlock` | 证据: formal blocker package 明确写出：当前层已正式耗尽、最后一个具体 carrier 已固定、无第二个 visible consumer、继续在同层 probing 的边际收益很低 | 结论: visible property construction 层已作为已判死子层沉淀，可在后续最终结论中直接引用；后续若继续推进，应转向更低的 kernel / IOSurface-side 解释层 | 下一步: 只定义一个更低层最小入口，而不是回到当前可见 property 路径
2026-06-19 10:13:25 +0800 | 目标: 把更低层的最小进入点收敛到一个可执行入口，避免下一轮再做准备性发散 | 动作: 结合 lower-layer entry package 与 IDA 可行性核对结果，把下一层入口优先级写回主文档 | 证据: `mps/ANE/experiments/results/lower_layer_entry_package.md`；子代理可行性结论表明最优先动作是直接试 `idb_open(kernelcache)`，失败后才考虑 IM4P 解压或 KDK；`IOSurface.kext` / `BootKernelExtensions.kc` 是可直接使用的备选 lower-layer 入口 | 结论: 下一轮唯一最小入口已确定为 `idb_open(kernelcache)` 可行性 probe；这一步成功则直接进入更低层，失败则把失败正式记录为入口卡点并切备选 | 下一步: 执行一次 `idb_open(kernelcache)` probe
2026-06-19 10:13:25 +0800 | 目标: 把 `idb_open(kernelcache)` probe 的失败从“未做”变成“已收敛的宿主能力卡点” | 动作: 记录 `ida` 子代理的最小可行性结果：当前最佳目标文件是 `/System/Library/Kernels/kernel.release.t8132`，但 `IDA Pro` 宿主未安装，`ida-pro-mcp` 因此不可用 | 证据: 子代理确认当前机 macOS 26.5 / t8132 上存在裸 Mach-O `kernel.release.t8132`；`ida64` 不存在；当前失败不是 IM4P 格式导致 | 结论: 下一层入口的核心卡点已从“找不到目标工件”收紧成“缺少 IDA Pro 宿主”；若继续推进，只需在 `IDA Pro` 安装路径与非 IDA 的本机 lower-layer 入口之间二选一 | 下一步: 选择安装 IDA Pro 后直开 `kernel.release.t8132`，或改走 `lldb` / 其他本机 lower-layer 入口
2026-06-19 10:27:54 +0800 | 目标: 确认真正的 lower-layer 目标是否已找对，以及 shell-only 路线是否还有继续挖的价值 | 动作: 用 shell 直接探测 `kernel.release.t8132` 与真实 `Preboot/.../kernelcache`；对前者做 `nm/strings`，对后者做 `file/strings` 级别最小检查 | 证据: `kernel.release.t8132` 只暴露 XNU / IOService exclave 基础设施，不含 `AppleH16ANEInterface` 私有驱动特征；真实 `Preboot/.../kernelcache` 对当前 shell-only 路线只显示为 generic `data`；新增 `mps/ANE/.ane_runs/json/kernelcache_shell_entry_boundary_20260619.json` | 结论: lower-layer 正确目标已知，但 shell-only 路线对它的信息密度不足；下一层问题已从“找什么文件”收紧成“选哪种 decode-capable 入口” | 下一步: 在 `IDA Pro`、`KDK/解压`、或其他 decode-capable 入口之间选一条，不再重复普通 shell 探针
2026-06-19 10:36:43 +0800 | 目标: 验证当前本机工具是否已经足够把正确的更低层 fileset entry 暴露出来，而不只是确认目标文件路径 | 动作: 用 `kmutil inspect --show-fileset-entries` 直接枚举当前 `Preboot` kernelcache 的关键 fileset entries，并用 `kmutil emit-macho` 产出 raw `BootKernelCollection.kc` | 证据: 当前已可直接看到 `AppleH16ANEInterface (vmaddr=0xfffffe000743d780, fileoff=4429696)`、`AppleT8132ANEHAL`、`IOSurface` 三个关键 entry；`/tmp/KMUtilProducts/BootKernelCollection.kc` 已成功生成 | 结论: lower-layer 入口已从“找对目标文件”推进到“已拿到正确 fileset entry metadata”；下一轮不应再做入口可见性检查，而应直接针对 `AppleH16ANEInterface` 做 entry 提取/符号与段暴露 | 下一步: 只做 `AppleH16ANEInterface` fileset entry 的提取 / 符号化最小 probe
2026-06-19 10:44:29 +0800 | 目标: 把 `AppleH16ANEInterface` 从“正确入口之一”进一步固定成下一轮的唯一默认入口 | 动作: 直接记录当前 `kmutil inspect` 暴露出的 `AppleH16ANEInterface` 关键 metadata（vmaddr/fileoff/__TEXT_EXEC 大小/nsyms/nextdefsym），不再做额外入口判断 | 证据: `kmutil inspect --show-fileset-entries` 已给出 `AppleH16ANEInterface vmaddr=0xfffffe000743d780 fileoff=4429696 __TEXT_EXEC.__text size=1101912 nsyms=9136 nextdefsym=2256` | 结论: 下一轮的唯一合理动作就是对 `AppleH16ANEInterface` entry 做提取 / 符号与段暴露；入口选择问题已经结束 | 下一步: 针对 `AppleH16ANEInterface` 做 entry 提取 / 符号化最小 probe
2026-06-19 10:49:38 +0800 | 目标: 把 `AppleH16ANEInterface` 从“可见 entry”推进到“已暴露的符号面”，让下一轮能直接选一个 deeper reverse target | 动作: 新增并运行 `mps/ANE/experiments/ane_bootkc_appleh16_fileset_symbol_probe.py`，直接解析 raw `BootKernelCollection.kc` 中 `AppleH16ANEInterface` entry 的 `LC_SYMTAB` / `LC_DYSYMTAB`，导出样本符号与命名家族统计 | 证据: `mps/ANE/.ane_runs/csv/ane_bootkc_appleh16_fileset_symbol_probe.csv`; `mps/ANE/.ane_runs/json/appleh16_fileset_symbol_visibility_verdict_20260619.json`; 当前统计已可见 `externalMethod`、`descriptor`、`segment`、`cache`、`prepare`、`eval` 等命名家族命中 | 结论: 下一轮不应再做工具层/入口层工作；唯一问题是从这些符号家族里选一个最小的 selector-9 / artifact-descriptor 相关 deeper reverse target | 下一步: 选一个最小相关符号家族并深入
2026-06-19 10:54:30 +0800 | 目标: 把 `AppleH16ANEInterface` 的多个候选符号家族收缩成一个唯一 default deeper reverse target | 动作: 基于 `ane_bootkc_appleh16_fileset_symbol_probe.csv` 的关键词过滤与排序，形成 `appleh16_first_deeper_target_selection_20260619.json`，固定首个目标为 `_Z22ANE_ProgramSendRequest` | 证据: 当前候选排序中，`ANE_ProgramSendRequest` 直接对应 eval dispatch 门，且与当前 `0x12` 污染问题最直接；其余 `descriptor`/`segment`/`prepare` 家族降为次级入口 | 结论: 下一轮唯一合理动作是围绕 `ANE_ProgramSendRequest` 做最小 call-neighborhood / first-stateful-callee probe | 下一步: 对 `ANE_ProgramSendRequest` 做最小邻域下钻
2026-06-19 11:04:50 +0800 | 目标: 把 `ANE_ProgramSendRequest` 从“选中的符号”推进成一个可直接下钻的具体邻域入口 | 动作: 新增并运行 `mps/ANE/experiments/ane_bootkc_program_send_request_neighborhood_probe.py`，从 `AppleH16ANEInterface` fileset entry 中导出该符号的近邻符号簇与固定反汇编窗口 | 证据: `mps/ANE/.ane_runs/csv/ane_bootkc_program_send_request_neighborhood_probe.csv`; `mps/ANE/.ane_runs/json/program_send_request_neighborhood_verdict_20260619.json`; 关键窗口显示在保存入参后很快读取 `[x26+0xd8]`、vtable `+0x1e8`，并触发一次 `blraa x9, x17` 间接调用 | 结论: 下一轮无需再选 deeper target；唯一应该下钻的是 `ANE_ProgramSendRequest` 中这次最早的 vtable 间接调用，判断其真实 callee 与 stateful 角色 | 下一步: 识别 `blraa x9, x17` 对应的真实 callee
2026-06-19 11:04:50 +0800 | 目标: 把 `ANE_ProgramSendRequest` 的邻域事实进一步沉淀成可执行的下一轮入口，而不是只停留在一个目标名 | 动作: 补充记录完整 demangled 符号、`request_args + 0x89` 模式 gate、`request_args + 0xd8` 状态对象入口、以及 `vtable + 0x1e8 / +0x8c0` 两跳间接调用 | 证据: 同一邻域 probe 已确认第一跳返回值还会写到 `out_u64 + 0x938`，说明它不是纯日志/薄包装 | 结论: 下一轮若继续推进，应优先识别 `vtable + 0x1e8` 的真实 callee，它是当前最像 first stateful consumer 的点 | 下一步: 识别 `vtable + 0x1e8` 的真实 callee
2026-06-19 11:17:37 +0800 | 目标: 判断 `ProgramSendRequest` 里两跳 vtable 间接调用哪一跳更像真正的 stateful 路径 | 动作: 直接读取 `ANEDriver` / `ANEHWDevice` / `ANECoreInterface` 三张 vtable 的 `+0x1e8` 和 `+0x8c0` 槽位，比较它们是否跨类一致 | 证据: 当前机器上 `+0x1e8` 在三张表上相同，而 `+0x8c0` 在三张表上不同 | 结论: `+0x1e8` 更像共享前处理 / 接口层 helper，`+0x8c0` 更像类特异的 stateful 提交路径 | 下一步: 优先识别 `vtable + 0x8c0` 的真实 callee
2026-06-19 11:23:42 +0800 | 目标: 把 `ProgramSendRequest` 从 driver wrapper 再下推一层，固定真正应该继续下钻的 exported 目标 | 动作: 新增并运行 `mps/ANE/experiments/ane_bootkc_hw_program_send_request_chain_probe.py`，直接导出 `ProgramSendRequest` 家族的 exported chain | 证据: `mps/ANE/.ane_runs/json/hw_program_send_request_chain_verdict_20260619.json`; 链路明确为 `ANEDriver::ANE_ProgramSendRequest` → `ANEHWDevice::ANE_ProgramSendRequest` → `ANE_ProgramSendRequest_gated` → `ANE_ProgramSendRequestInitialChecksAndLookups_gated` | 结论: 下一轮默认目标不再是 driver wrapper，而是 `ANEHWDevice::*SendRequest*_gated` 这一层 | 下一步: 在 `ANE_ProgramSendRequest_gated` 和 `InitialChecksAndLookups_gated` 中选一个最早的 clearly stateful direct callee
2026-06-19 11:30:15 +0800 | 目标: 在两个 `ANEHWDevice::*SendRequest*_gated` 候选里选出一个更早、更明确的 direct-callee 入口 | 动作: 新增并运行 `mps/ANE/experiments/ane_bootkc_hw_sendrequest_gated_compare_probe.py`，并对比两者前 32 条指令里的直接调用关系 | 证据: `ANE_ProgramSendRequest_gated` 当前窗口无直接 `bl`；`ANE_ProgramSendRequestInitialChecksAndLookups_gated` 在 `0xfffffe0009297840` 直接调用 `ANE_HandlePowerStateChecksForClientEbb` | 结论: 下一轮默认目标再收紧成 `ANE_ProgramSendRequestInitialChecksAndLookups_gated` 中的 `ANE_HandlePowerStateChecksForClientEbb` | 下一步: 下钻 `ANE_HandlePowerStateChecksForClientEbb`
2026-06-19 11:34:59 +0800 | 目标: 判断 `ANE_HandlePowerStateChecksForClientEbb` 更像纯 power gate 还是已经进入 client/program-aware 状态层 | 动作: 新增并运行 `mps/ANE/experiments/ane_bootkc_handle_powerstate_checks_probe.py`，导出其近邻符号与固定反汇编窗口 | 证据: `mps/ANE/.ane_runs/json/handle_powerstate_checks_verdict_20260619.json`; 近邻落在 `findClientByOwningTask`、`findClientByCodesigning`、`lookupClientProgramWithHandle`、`ANE_Add/RemovePersistentClient_gated` 这一簇；当前窗口内无直接 `bl` | 结论: 当前更应把它视作 client/program-aware gate，而不是纯电源薄包装 | 下一步: 读它内部的 client/program/persistent-state 相关字段访问模式
2026-06-19 11:40:26 +0800 | 目标: 在 `ANE_HandlePowerStateChecksForClientEbb` 内部字段与直接调用之间，选出更值得下一轮下钻的单一入口 | 动作: 补读 probe 输出中与 `self+0x718`、对象 `+0x111/+0xa8/+0xa9`、以及两个 direct `bl` 对应的局部窗口 | 证据: 当前 direct `bl` 只有一个未命名 helper 和 `ANEHWDevice::commandSleep`；同时已确认字段簇 `self+0x718`、`+0x111`、`+0xa8`、`+0xa9` | 结论: 下一轮不应优先下钻 `commandSleep`，而应先读这组字段模式，它们更像 client/program/persistent-state 的真实入口 | 下一步: 读 `0x718 / 0x111 / 0xa8 / 0xa9` 这组字段模式
2026-06-19 11:40:26 +0800 | 目标: 在 `0x718 / 0x111 / 0xa8 / 0xa9` 这组模式里再下推一层，选出真正的对象入口 | 动作: 复读局部窗口，确认 `0x111 / 0xa8 / 0xa9` 都是 `ldrb + tbz` 形式的 byte-flag gates，而 `self+0x718` 是唯一的指针加载入口 | 证据: `ldr x24, [x24, #0x718]` 后立即进入后续判断；三个 byte 字段都只是 gate 条件 | 结论: 下一轮唯一目标应再收紧成 `self + 0x718` 指向的对象，而不是继续追三个 flag byte 本身 | 下一步: 识别 `self + 0x718` 指向的对象
2026-06-19 11:47:58 +0800 | 目标: 在 `self + 0x718` 对象边之后再下推一层，确认真正更值得下钻的 direct-callee | 动作: 复读 `ANE_HandlePowerStateChecksForClientEbb` 完整窗口，跟踪 `x24 = [self+0x718]` 的第一去向 | 证据: `mov x1, x24` 后立刻调用 `0xfffffe000bed82e8`；`commandSleep(self, self+0xa0, 2)` 出现在其后 | 结论: 下一轮默认目标应再收紧成未命名 direct callee `0xfffffe000bed82e8`，而不是 `commandSleep` | 下一步: 识别 `0xfffffe000bed82e8` 的真实角色
2026-06-19 11:51:28 +0800 | 目标: 判断 `0xfffffe000bed82e8` 本身是不是值得继续追，还是只是一个很薄的通用包装层 | 动作: 直接反汇编 `0xfffffe000bed82e8` 周围小窗口，观察它是否立刻跳进更重的核心 helper | 证据: 当前窗口显示 `0xfffffe000bed82e8` 只做短 prologue/参数重排，然后立即 `bl 0xfffffe000bed8348`；后者一开始就建立更大栈帧并读取 per-CPU/线程本地状态 | 结论: 下一轮默认目标应继续下推到 `0xfffffe000bed8348` | 下一步: 读 `0xfffffe000bed8348` 本体
2026-06-19 11:58:52 +0800 | 目标: 判断 `0xfffffe000bed8348` 是否已经触到我们关心的 `0x12` 污染语义窗口 | 动作: 读取其前 80 条指令，观察它的第一批全局/线程本地状态读写与比较条件 | 证据: 当前窗口显示它会读 per-CPU / 线程本地状态、多个全局状态位，并出现 `cmp w9, #0x12` | 结论: 下一轮不应泛读整个 helper，而应围绕 `cmp w9, #0x12` 和其后的状态读写做最小 probe | 下一步: 围绕 `cmp w9, #0x12` 做最小 probe
2026-06-19 12:04:40 +0800 | 目标: 把 `0x12` gate window 里的 5 个状态源再收窄成一个单一下一目标 | 动作: 基于当前窗口中状态源与比较/布尔派生链的距离和作用强度，形成 `gate_0x12_state_source_selection_20260619.json` | 证据: `[0xfffffe0007e7b000 + 0xa58]` 是唯一直接参与 `cmp w9, #0x12` 并立即流入 `csinc -> w24` 的状态源；其他 thread-local / bitfield / byte-flag 先降为次级入口 | 结论: 下一轮唯一目标应收紧成 `[0xfffffe0007e7b000 + 0xa58]` 的真实归属 | 下一步: 识别 `[0xfffffe0007e7b000 + 0xa58]` 的真实归属
2026-06-19 12:11:15 +0800 | 目标: 消除 `[0xfffffe0007e7b000 + 0xa58]` 的地址空间歧义，防止把 BootKC runtime 地址误解释成 standalone kernel `__CTF` 元数据 | 动作: 新增 `mps/ANE/.ane_runs/json/gate_0x12_state_source_address_space_boundary_20260619.json`，明确当前 active reverse 使用的是 `Preboot` kernelcache → `BootKernelCollection.kc` 地址空间 | 证据: `BootKC` 地址空间里该地址落在 `com.apple.kernel::__DATA_CONST,__const`；子代理给出的 `kernel.release.t8132::__CTF` 结论来自另一套地址空间 | 结论: 下一轮仍应在 `BootKernelCollection` 地址空间里识别该状态源，不能让 `kernel.release.t8132` 的错配归属反转当前路径 | 下一步: 在 `BootKC` 地址空间里识别 `[0xfffffe0007e7b000 + 0xa58]` 的真实归属
2026-06-19 12:14:52 +0800 | 目标: 把 `[0xfffffe0007e7b000 + 0xa58]` 从“单一状态源”再收紧成一个更具体的分析对象 | 动作: 读取其在 `com.apple.kernel::__DATA_CONST,__const` 中的原始邻域 0xc0 字节模式 | 证据: 该地址附近出现多组重复/成对的只读常量值，形态更像静态配置表或描述表，而非单一运行时计数位 | 结论: 下一轮不应再把它当作单一全局值，而应识别它所在静态表的类型 | 下一步: 识别 `+0xa58` 所在静态表的类型
2026-06-19 12:18:11 +0800 | 目标: 判断 `+0xa58` 所在静态表更像普通指针表还是标记化描述表 | 动作: 按 8-byte 表项读取 `+0xa58` 周围窗口，比较值模式 | 证据: 表项既有局部重复引用，也有统一高前缀的编码值，形态不像朴素运行时指针数组 | 结论: 这更像一张标记化描述表/配置表项，而不是普通对象指针表 | 下一步: 识别这张标记化描述表的编码规则
2026-06-19 12:37:12 +0800 | 目标: 判断 `+0xa58` 邻域到底是 ANE 业务表，还是更底层的 BootKC 编码指针表 | 动作: 新增并运行 `mps/ANE/experiments/ane_bootkc_gate_0x12_source_table_probe.py`，只解析 `BootKernelCollection.kc` 中 `0xfffffe0007e7ba58` 邻域 33 个 8-byte 表项；把每个 qword 拆成 low32 target / next_delta / bind/auth，并映射到当前 BootKC 根 Mach-O 段范围；同时参考 `reverse-engineer` 子代理给出的更激进候选，但未直接采信 | 证据: `mps/ANE/.ane_runs/csv/ane_bootkc_gate_0x12_source_table_probe.csv`; `mps/ANE/.ane_runs/json/gate_0x12_source_table_verdict_20260619.json`; 当前窗口中 10 个非零 qword 有 9 个落入 `chained_rebase_like`，稳定指向 `__DATA_CONST` 邻域 `0xe77ac8/0xe77ad0` 与 `__DATA` 邻域 `0x55500a0..0xac`；同一 low32 target `0x55500a4` 还出现了 `next_delta=2` 与 `60` 两种变体 | 结论: 本轮 verdict=`confirmed`；`+0xa58` 邻域当前更像 BootKC rebase/fixup-style 编码指针表，而不是 ANE-specific business descriptor table；当前真正值得继续追的不是 `0x12` 这个字面值，而是这些 low32 target 尤其 `0x55500a0..0xac` 所落入的具体对象/记录家族 | 下一步: 只做一个更小 probe，把 `0x55500a0..0xac` 这一族 low32 target 解到真实对象边界，判断它是 generic kernel bookkeeping 还是 ANE-adjacent lower state carrier
2026-06-19 12:46:41 +0800 | 目标: 判断 `0x55500a0 .. 0xac` 这一族 decoded target 到底是不是值得继续当作 ANE lower-state 入口 | 动作: 新增并运行 `mps/ANE/experiments/ane_bootkc_gate_0x12_low32_target_family_probe.py`，只读取 `BootKernelCollection.kc` 根 Mach-O `__DATA` 中 `0x5550080..0x5550110` 的紧邻 u32/u64 布局；过程中修正了一个窗口长度 bug 后立即重跑，不扩散范围 | 证据: `mps/ANE/.ane_runs/csv/ane_bootkc_gate_0x12_low32_target_family_probe.csv`; `mps/ANE/.ane_runs/json/gate_0x12_low32_target_family_verdict_20260619.json`; 当前目标槽位仅解出 `0x20 / 0x20 / 0x0 / 0xc8` 小标量，区域落在根 Mach-O `__DATA`，且后续快速进入 packed generic data 模式 | 结论: 本轮 verdict=`confirmed`；`0x55500a0 .. 0xac` 这一支更像 generic kernel data with local header，不像 ANE-adjacent stateful object/record carrier；这条支线应降级 | 下一步: 回到同一 source-table window，改追更靠近本地 `__DATA_CONST` 的 `0xe77ac8 / 0xe77ad0` decoded target 家族
2026-06-19 12:56:58 +0800 | 目标: 在不依赖高层猜测的前提下，再核验 `0x55500a0 .. 0xac` 这块结构到底有多“专用”，以及 raw `BootKC` 能否直接进 IDA 做 xref/module 判定 | 动作: 主线程额外核验 `0xc8` 表体长度与字节字母表，确认其实际是 `25 × 8` LUT 且仅使用 `{00,33,66,99,cc,ff}` 六种字节；再扫描 `__DATA` 中同类头模式，当前只见 `0x5543498` 与 `0x5550080` 两处；随后直接用 `ida-pro-mcp idb_open(/tmp/KMUtilProducts/BootKernelCollection.kc, mode=prefer_headless)` 做最小 IDA 探测；同时启动并关闭了 `ida` 子代理，但其未在时限内返回可用 xref 结果 | 证据: shell 核验显示 `lut_len=200`, `rows_8=25`, `distinct_bytes=[0,51,102,153,204,255]`；头模式命中仅 `0x5543498` 与 `0x5550080`；`ida-pro-mcp` 当前返回 `Failed to open database: /private/tmp/KMUtilProducts/BootKernelCollection.kc` | 结论: 当前这块结构仍更像专用 generic-kernel LUT/header，而 raw `BootKC` 直接做 IDA xref/module check 存在明确工具 blocker；这不是当前 lower-layer 路径被证伪，只是该验证手段暂时卡住 | 下一步: 不再卡在 raw `BootKC` 打开问题；下一轮只追同一 source-table window 中更靠近本地 `__DATA_CONST` 的 `0xe77ac8 / 0xe77ad0` decoded target 家族，或先把 `BootKC` 切成可被 IDA 导入的更小目标后再做 xref
2026-06-19 13:07:12 +0800 | 目标: 判断 `0xe77ac8 / 0xe77ad0` 这组本地 `__DATA_CONST` decoded target 自身到底是不是值得继续当作 lower-state 入口 | 动作: 新增并运行 `mps/ANE/experiments/ane_bootkc_gate_0x12_local_target_boundary_probe.py`，只读取 `0xe77a88..0xe77bc8` 的局部布局，显式量化 `0xe77ac8` 到下一处结构头 `0xe77b90` 之间的零区；同时用 `searcher` 子代理确认仓库内无更早历史线索可复用并立即关闭 | 证据: `mps/ANE/.ane_runs/csv/ane_bootkc_gate_0x12_local_target_boundary_probe.csv`; `mps/ANE/.ane_runs/json/gate_0x12_local_target_boundary_verdict_20260619.json`; 当前显示 `0xe77ac8` 与 `0xe77ad0` 自身均为 `u64==0`，到 `0xe77b90` 前共有 `25` 个连续零 qword / `200` 字节 gap，而第一处结构化记录头只从 `0xe77b90` 才开始并出现 `0x8035db49` / `0xffffffff` / `0xc0e00001` 这一簇 | 结论: 本轮 verdict=`confirmed`；`0xe77ac8 / 0xe77ad0` 当前更像 local anchor / pre-record table glue，不是实际 state-carrying record body；这条入口应再前移到 `0xe77b90` | 下一步: 只追 `0xe77b90` 这一首个真实记录头，判断它所属家族是 generic kernel metadata 还是更靠近 lower ANE control path
2026-06-19 13:18:04 +0800 | 目标: 判断 `0xe77b90` 这处首个真实记录头所属家族，确认它是不是比前面的 source-table 分支更接近 ANE-owned control state | 动作: 新增并运行 `mps/ANE/experiments/ane_bootkc_gate_0x12_record_family_probe.py`，对 `0xe77b90` 起始、步长 `0x50` 的 12 条记录做 qword 级跨段映射；同时读取固定槽位与变化槽位分布；随后发现这条分支依然主要混合指向 `__DATA_CONST`、`__DATA`、`__PRELINK_TEXT` 与固定 `__TEXT_EXEC` 位置，不再继续在其上扩散 | 证据: `mps/ANE/.ane_runs/csv/ane_bootkc_gate_0x12_record_family_probe.csv`; `mps/ANE/.ane_runs/json/gate_0x12_record_family_verdict_20260619.json`; 当前家族固定 `0x50` 步长，稳定出现 `__PRELINK_TEXT+0xd809a` 与固定 `__TEXT_EXEC+0x33eff50`，同时变化槽位在小 `__DATA+0x843f4..0x84410` 与 `__PRELINK_TEXT+0xd80xx..0xd823c` 之间游走 | 结论: 本轮 verdict=`confirmed`；`0xe77b90` 记录族当前更像 generic BootKC/kext metadata，不像 lower ANE control-state record family；因此当前 `+0xa58 -> source-table` 整条支线应整体降级 | 下一步: 回到原始 helper `0xfffffe000bed8348`，改追下一个 live 候选源 `[x23+0x1c0]`
2026-06-19 13:24:46 +0800 | 目标: 在 source-table 分支整体降级后，确认下一候选源 `[x23+0x1c0]` 是否比 BootKC metadata 分支更贴近 live helper control flow | 动作: 新增并运行 `mps/ANE/experiments/ane_bootkc_gate_0x12_threadlocal_source_probe.py`；首次使用 `python3` 因当前机器缺少 `capstone` 失败，随后切换到已安装 `capstone` 的 `python` 解释器重跑成功 | 证据: `mps/ANE/.ane_runs/csv/ane_bootkc_gate_0x12_threadlocal_source_probe.csv`; `mps/ANE/.ane_runs/json/gate_0x12_threadlocal_source_verdict_20260619.json`; 在 `0xfffffe000bed8348` 窗口里，`[x23+0x1c0]` 的第一处用法就是 `ldr w8, [x23, #0x1c0]` 后立刻 `cbz w8, ...` | 结论: 本轮 verdict=`confirmed`；`[x23+0x1c0]` 当前是比 BootKC source-table 分支更强的下一入口，因为它直接参与 live gate，而不是先掉进 metadata 解码 | 下一步: 只追 `[x23+0x1c0]` 的角色语义，判断它更像 per-thread admission state、per-client mode，还是 device-state bridge
2026-06-19 13:32:11 +0800 | 目标: 把 `[x23+0x1c0]` 从“更强下一入口”再推进到更具体的角色语义判断 | 动作: 新增并运行 `mps/ANE/experiments/ane_bootkc_gate_0x12_threadlocal_role_probe.py`，使用当前机器已有 `capstone` 的 `python` 解释器，只读取 `0xfffffe000bed8348` 周围 0x300 字节窗口中的 `tpidr_el1`、`[x23+0x1b0]`、`[x23+0x1c0]` 和紧随其后的分支/位运算关系 | 证据: `mps/ANE/.ane_runs/csv/ane_bootkc_gate_0x12_threadlocal_role_probe.csv`; `mps/ANE/.ane_runs/json/gate_0x12_threadlocal_role_verdict_20260619.json`; 当前窗口中 `x23` 直接来自 `mrs x23, tpidr_el1`，helper 先读 `[x23+0x1b0]` 再读 `[x23+0x1c0]`，且 `+0x1c0` 首次读取后立即参与 `cbz` 与后续 `bic` / 条件分支 | 结论: 本轮 verdict=`confirmed`；`[x23+0x1c0]` 当前比 per-client heap field 更像 thread/per-CPU admission state | 下一步: 只追这个 threadlocal admission 位是否在 helper 家族中进一步并入更广的 device/client state
2026-06-19 13:44:55 +0800 | 目标: 判断 `BootKC + 0x12 gate` 支线是否还值得继续，还是应正式判定为通用内核假目标并切回 ANE-side 入口 | 动作: 汇总 `ida` 子代理对 `0xfffffe000bed8348` 的函数级定位，以及本轮对 `[x23+0x1c0]` 的 live-gate / threadlocal-role 两次 probe；同时避开当前机器对系统私有 framework 文件的可读性 blocker，不再硬撞 `ida-pro-mcp` 打开系统 framework，而改从仓库现有 `newinstance` 静态探针与说明中提取当前最强的 ANE-side lower entry | 证据: `0xfffffe000bed8348` 已被 `ida` 定位为 XNU `os_log` 变体；`[x23+0x1c0]` 来自 `tpidr_el1` per-CPU base；`+0xa58 -> source-table -> local target -> record family` 整条链继续下钻后只落到 BootKC/kext metadata；与此同时，`mps/ANE/experiments/ane_newinstance_serializer_static_probe.py` 与 `results/newinstance_serializer_static_note.md` 已明确固定 `-[_ANEVirtualClient loadModelNewInstanceLegacy:options:modelInstParams:qos:error:]` 为当前最强 lower serializer authoring 入口 | 结论: 本轮 verdict=`falsified`；`BootKC + 0x12 gate` 整条支线正式判死为通用内核基础设施假目标，不再作为 private ANE lower control layer 默认入口 | 下一步: 下一轮只围绕 `loadModelNewInstanceLegacy` 的 lower serializer / daemon request authoring 做一个更小 probe，找出真正阻塞 single-process reuse 的 field/slot
2026-06-19 13:56:08 +0800 | 目标: 在切回 `loadModelNewInstanceLegacy` 后，判断当前最像 single-process reuse blocker 的具体 field/slot 到底是 `instanceName` 还是 `request +0x528..+0x547` family | 动作: 复用现有 `ane_newinstance_daemon_gap_summary.csv`、`ane_newinstance_packaging_bridge_summary.csv` 与 `ane_inmemory_new_instance_probe_request_inline_sha_matrix.csv`，新增并运行 `mps/ANE/experiments/ane_newinstance_blocker_ranking_probe.py` 做一个纯聚合排序；同时重新核验 `newinstance_daemon_gap_note` / `newinstance_packaging_bridge_note` / `newinstance_request_inline_sha_authoring_note` 的现有文字证据 | 证据: `mps/ANE/.ane_runs/json/newinstance_blocker_ranking_verdict_20260619.json`; `instanceName` 当前只收敛到 daemon-side logging helper `%@:instanceName:%@`，未 pinned 到可见 request slot；相反 `weight_sha` 已到达 selector-8 目标位，ANEServices repack source slot `request +0x528` 已 pinned，但 daemon writer 缺失；直接 author `request +0x528..+0x547` 也仍停在相同 wrapper rejection bucket | 结论: 本轮 verdict=`confirmed`；当前最强 blocker 候选已不再是 `instanceName`，而是 `request weight +0x528..+0x547` family 的隐藏 writer / transient sidecar | 下一步: 只追这个 family 的第一个 lower author/join 点
2026-06-19 14:05:17 +0800 | 目标: 在 `request +0x528..+0x547` 已成为最强 blocker 候选后，再把 provenance 边界收紧到“谁不是 author，谁才是下一步唯一高价值目标” | 动作: 复用 `ane_newinstance_request528_provenance_summary.csv`、`ane_newinstance_helper_sidecar_summary.csv`、`ane_newinstance_daemon_gap_summary.csv` 与 `ane_inmemory_new_instance_probe_request_inline_sha_matrix.csv`，新增并运行 `mps/ANE/experiments/ane_newinstance_request528_next_probe.py`，把当前 machine-local 证据压成一个显式 next-step verdict | 证据: `mps/ANE/.ane_runs/json/newinstance_request528_next_verdict_20260619.json`; 当前明确显示：ANEServices 读取的是原始 daemon request memory，不是 wrapper-local staging copy；visible daemon helper neighborhood request-blind；直接 inline author `+0x528..+0x547` 也仍停在同一 wrapper rejection bucket | 结论: 本轮 verdict=`confirmed`；当前唯一高价值目标已进一步收紧成“找到第一个 non-visible clone/repack/sidecar stage 对原始 daemon request `+0x528..+0x547` region 的 author/join 点” | 下一步: 只追这个 first non-visible author/join stage
2026-06-19 14:12:34 +0800 | 目标: 在 first non-visible stage 仍过于抽象时，把当前 machine-local 最强候选收紧成一个更具体的 family | 动作: 复用 `ane_newinstance_helper_sidecar_summary.csv`、`ane_newinstance_request528_provenance_summary.csv` 与现有 `bootkc_create_instance_hidden_handle_bridge_probe.md`，新增并运行 `mps/ANE/experiments/ane_newinstance_request528_stage_ranking_probe.py` 做一个候选优先级压缩 | 证据: `mps/ANE/.ane_runs/json/newinstance_request528_stage_ranking_verdict_20260619.json`; visible helper 已 ruled out；ANEServices 只是 reader；当前 machine-local 最具体的 non-visible sidecar family 已是 driver/device-authored hidden handle `-> x5 -> additional_params+0x18 -> lower gated body` | 结论: 本轮 verdict=`confirmed`；当前最强的 first non-visible candidate 已收紧成 deeper driver-routed create-instance hidden-handle family | 下一步: 只追 hidden-handle family 是否与 `request +0x528..+0x547` region 发生 join/gate
2026-06-19 14:19:05 +0800 | 目标: 在 hidden-handle family 已成为最强候选后，再把问题收紧成“它是不是最近的 join/gate surface，还是已经是已证实 author” | 动作: 复用 `ane_newinstance_request528_provenance_summary.csv`、`ane_newinstance_helper_sidecar_summary.csv` 与 `bootkc_create_instance_hidden_handle_bridge_probe.md`，新增并运行 `mps/ANE/experiments/ane_newinstance_hidden_handle_join_probe.py` 做一个更小的 join-proximity verdict | 证据: `mps/ANE/.ane_runs/json/newinstance_hidden_handle_join_verdict_20260619.json`; 当前 machine-local 仍只证明：ANEServices 是 reader、visible helper request-blind、hidden-handle family 是最近的 lower join/gate surface；尚未直接证明 hidden-handle family 本身就是 `+0x528..+0x547` 的 author | 结论: 本轮 verdict=`confirmed`；hidden-handle family 当前不是已证实 author，但已是离 `request +0x528..+0x547` 最近、证据最硬的 lower join/gate surface | 下一步: 只追 hidden-handle path 与 `request +0x528..+0x547` 是否在同一 accepted create-instance lower stage 汇合
2026-06-19 14:26:43 +0800 | 目标: 在 hidden-handle path 已成为最近 join/gate surface 后，再判断它是否已经与 `request +0x528..+0x547` 位于同一 lower stage，还是中间还隔着 clone/repack | 动作: 复用 `ane_newinstance_request528_provenance_summary.csv`、`ane_newinstance_packaging_bridge_summary.csv` 与 `bootkc_create_instance_hidden_handle_bridge_probe.md`，新增并运行 `mps/ANE/experiments/ane_newinstance_hidden_handle_stage_probe.py` 做一个 stage-equality verdict | 证据: `mps/ANE/.ane_runs/json/newinstance_hidden_handle_stage_verdict_20260619.json`; 当前 machine-local 已证明 hidden-handle 是 accepted-state join surface，而 `request +0x528` 仍只被钉到原始 daemon request memory 的 later reader；当前还没有二者同 stage 汇合的直接证据 | 结论: 本轮 verdict=`confirmed`；hidden-handle family 仍是最近的 join/gate 面，但还不是 `request +0x528..+0x547` 的同阶段直接证据 | 下一步: 只追第一个同时看到 hidden-handle accepted state 和 `request +0x528..+0x547` family 的 lower surface，或正式证明中间还隔着 clone/repack
2026-06-19 14:33:22 +0800 | 目标: 在 hidden-handle stage equality 已收紧后，再把剩余问题压成最小未解缺口 | 动作: 复用 `bootkc_create_instance_hidden_handle_bridge_probe.md`、`newinstance_request528_provenance_note.md`、`newinstance_helper_sidecar_note.md` 与 `newinstance_packaging_bridge_note.md` 的现有强证据，不再新增运行时假设，只把当前 machine-local 能证明的两条强证据链对齐 | 证据: hidden-handle family 已明确写回 `params[0]/x21[0]`；`request +0x528` family 已明确被 `ANEServices` 作为原始 request memory later reader 消费；当前仍没有同一 lower surface 同时接触这两条链的直接证据 | 结论: 本轮 verdict=`confirmed`；当前最小未解缺口已收紧成“找第一个同时看到 hidden-handle writeback 与 request+0x528 消费链的 lower surface” | 下一步: 只追这个交汇面
2026-06-19 14:40:51 +0800 | 目标: 在最小未解缺口已经成形后，再判断当前最靠近交汇的地方是不是已经落在 accepted create-instance lower path 本身 | 动作: 复用 `bootkc_create_instance_hidden_handle_bridge_probe.md`、`ane_newinstance_request528_provenance_summary.csv`、`ane_newinstance_packaging_bridge_summary.csv` 与 `bootkc_create_instance_gated_probe.md`，新增并运行 `mps/ANE/experiments/ane_newinstance_convergence_surface_probe.py` 做一个 closest-surface verdict | 证据: `mps/ANE/.ane_runs/json/newinstance_convergence_surface_verdict_20260619.json`; hidden-handle family 已在 accepted create-instance gated body 中 live；selector-8 per-weight params 也已在 lower path 结构化可见；当前最接近两条强证据链交汇的 surface 已不再是 visible daemon helper 或 visible ANEServices repack loop，而是 accepted create-instance lower path 本身 | 结论: 本轮 verdict=`confirmed`；当前下一步不应再在更高层 wrapper/helper 上徘徊，而应直接在 accepted create-instance lower path 内部/紧邻位置找第一处交汇 surface | 下一步: 只追 accepted create-instance lower path 内部/紧邻的第一处交汇 surface
2026-06-19 14:48:07 +0800 | 目标: 在 accepted create-instance lower path 已成为最近交汇面后，再把问题压缩到一个具体函数级入口 | 动作: 复用 `bootkc_create_instance_gated_probe.md`、`bootkc_create_instance_hidden_handle_bridge_probe.md`、`selector8_request_params_bridge_note.md` 与 `ane_newinstance_packaging_bridge_summary.csv`，新增并运行 `mps/ANE/experiments/ane_newinstance_convergence_candidate_probe.py` 做一个函数级 convergence-candidate verdict | 证据: `mps/ANE/.ane_runs/json/newinstance_convergence_candidate_verdict_20260619.json`; 当前 machine-local 已明确 `ANEHWDevice::ANE_ProgramCreateInstance_gated` 同时消费 x25/additional-params 侧和 x19/inner params 侧；hidden-handle family 已在该函数内成为 `additional_params+0x18 -> local_y`；inner params 也在该函数内做 procedure/weight validation | 结论: 本轮 verdict=`confirmed`；当前最强的 visible convergence candidate 已收紧成 `ANEHWDevice::ANE_ProgramCreateInstance_gated` 本体 | 下一步: 只追 `ANEHWDevice::ANE_ProgramCreateInstance_gated` 内部第一处真实 join point
2026-06-19 14:59:36 +0800 | 目标: 在 `ANEHWDevice::ANE_ProgramCreateInstance_gated` 已成为唯一入口后，进一步选出最值得读的 deeper join 窗口 | 动作: 复用 `ane_bootkc_create_instance_gated_probe.csv`，新增并运行 `mps/ANE/experiments/ane_newinstance_create_instance_candidate_ranking_probe.py`，对当前已读的几个候选窗口做手工约束排名 | 证据: `mps/ANE/.ane_runs/json/newinstance_create_instance_candidate_ranking_verdict_20260619.json`; 当前最强候选已收紧成 `0xfffffe000928da10`，因为它显式传入 `x19` 同时仍带着 accepted lower path live state；`0xfffffe000928d494` 更像 accepted-state/resource lookup；`0xfffffe000928c9f8` 更像 preparatory gating | 结论: 本轮 verdict=`confirmed`；当前下一步应直接读 `0xfffffe000928da10` helper call 窗口 | 下一步: 只追 `0xfffffe000928da10` 这个 helper call 是否就是 first semantic join point
2026-06-19 15:07:41 +0800 | 目标: 在候选窗口已收紧成 `0xfffffe000928da10` 后，确认它是不是 first semantic join point 本身 | 动作: 复用已读局部窗口事实，新增并运行 `mps/ANE/experiments/ane_newinstance_create_instance_semantic_join_confirm_probe.py` 做一个极小确认 verdict | 证据: `mps/ANE/.ane_runs/json/newinstance_create_instance_semantic_join_confirm_verdict_20260619.json`; 当前明确显示该 call boundary 发生在 hidden-handle / local_y 已经 live 之后，并且直接传入 `x2 = x19` 与 `x3 = x22` | 结论: 本轮 verdict=`confirmed`；`0xfffffe000928da10` 已经是当前最早的 first semantic join point | 下一步: 只追它调用的 `0xfffffe0009354710` callee 是什么，以及它真正消耗哪些参数
2026-06-19 15:15:18 +0800 | 目标: 在 first semantic join point 已经确认后，再把剩余问题压缩成单一 callee 级目标 | 动作: 复用 `0xfffffe000928da10` 的局部窗口事实，新增并运行 `mps/ANE/experiments/ane_newinstance_create_instance_callee_role_probe.py` 做一个极小角色 verdict | 证据: `mps/ANE/.ane_runs/json/newinstance_create_instance_callee_role_verdict_20260619.json`; 当前显示 `0xfffffe0009354710` 只会在两层 gate 之后到达，且收到 `x1=x27`, `x2=x19`, `x3=x22` 这一组最强的混合语义参数 | 结论: 本轮 verdict=`confirmed`；`0xfffffe0009354710` 已经成为当前最强的 lower-control helper 候选 | 下一步: 只追这个 callee 的 family，以及它真正消耗 `x1/x2/x3` 中的哪些参数
2026-06-19 15:24:03 +0800 | 目标: 在 `0xfffffe0009354710` 已成为唯一 callee 目标后，再把参数问题压缩成最小未解缺口 | 动作: 复用 `ane_newinstance_callee_param_use_probe.py` 的局部反汇编窗口，新增并运行 `mps/ANE/experiments/ane_newinstance_callee_param_dominance_probe.py`，把 x1/x2/x3 的 early-use 次序固化成一个极小 verdict | 证据: `mps/ANE/.ane_runs/json/newinstance_callee_param_dominance_verdict_20260619.json`; 当前显示 `x2` 先通过 `[x2+0x108]` / `x2+0x110` 主导 inner params / procedure 迭代，`x1` 随后进入 accepted-state/resource-side object surface，而 `x3` 开头只被复制成 `x27`，还未在第一轮控制流中变成 decisive use | 结论: 本轮 verdict=`confirmed`；当前最小未解缺口已收紧成“`x3/x27` 在 callee 内第一次什么时候真正变成语义活跃输入” | 下一步: 只追 `x3/x27` 的 first semantic use
2026-06-19 15:33:46 +0800 | 目标: 在 `x3/x27` 已成为唯一未解参数后，再把它压缩成单一 helper 目标 | 动作: 直接读取 `0xfffffe0009354710` 的更长局部窗口，围绕所有 `x27` / `w27` 使用点定位 first semantic use，随后新增并运行 `mps/ANE/experiments/ane_newinstance_callee_x27_first_use_probe.py` 做一个极小 verdict | 证据: `mps/ANE/.ane_runs/json/newinstance_callee_x27_first_use_verdict_20260619.json`; 当前显示 `x27` 开头只是 incoming `x3` 的副本，真正的 first semantic use 出现在 `0xfffffe0009354a0c`，并随后通过 `mov x3, x27 ; bl #0xfffffe0009358590` 把这块 derived per-entry surface 传给下一个 helper | 结论: 本轮 verdict=`confirmed`；`x3/x27` 的 first semantic use 已进一步收紧成 `0xfffffe0009358590` 这个 helper call | 下一步: 只追 `0xfffffe0009358590` 的 family 与参数消耗
2026-06-19 15:42:18 +0800 | 目标: 在 `0xfffffe0009358590` 已成为当前唯一 helper 候选后，再判断它是不是 decisive lower-control helper 本身 | 动作: 新增并运行 `mps/ANE/experiments/ane_newinstance_next_helper_param_use_probe.py`，直接读取 `0xfffffe0009358590` 的开头窗口，比较 x1/x2/x3 的 first-use 次序 | 证据: `mps/ANE/.ane_runs/json/newinstance_next_helper_param_use_verdict_20260619.json`; 当前显示该 callee 开头仍由 `x2` 先主导、`x1` 次之，而 `x3` 只在更后面的辅助/格式化分支里露头 | 结论: 本轮 verdict=`confirmed`；`0xfffffe0009358590` 当前更像中间辅助/预处理 helper，而不是明确的 decisive lower-control helper | 下一步: 只追更深一层的 first decisive `x3/x27` consumer
2026-06-19 16:18:49 +0800 | 目标: 在 `0xfffffe0009358590` 已降级为中间 helper 后，判断下一层 `0xfffffe000b828e50` 更像 parser/materializer 子层还是 first accepted-state lower-control helper | 动作: 新增并运行 `mps/ANE/experiments/ane_newinstance_b828e50_role_probe.py`，只读取 callsite `0xfffffe0009358b84..0xfffffe0009358ba0` 与 target `0xfffffe000b828e50` 的固定机器窗口；并并行派发 `reverse-engineer` 子代理做仓库内只读事实复核；`ida` 子代理本轮未在时限内产出结果后关闭，不把它当关键路径 | 证据: `mps/ANE/.ane_runs/csv/ane_newinstance_b828e50_role_probe.csv`; `mps/ANE/.ane_runs/json/newinstance_b828e50_role_verdict_20260619.json`; 当前 callsite 明确组装 `x3=x29-0x38`, `x4=x29-0x3c`, `x5=x29-0x3d`, `x6=sp+0x48`, `x7=sp+0x40`, `x1=x22`, `w2=2` 后 `bl #0xfffffe000b828e50`；callee 开头先清空全部 byref/out 槽，再 `cmp w2, #3` 分派；`reverse-engineer` 子代理复核仓库现有证据后同样将其归为更像 parser/materializer 辅助子层 | 结论: 本轮 verdict=`inconclusive`；当前 machine-local 与仓库证据都明显偏向 `0xfffffe000b828e50` 是 byref-heavy parser/materializer helper，而不是 terminal create-instance commit，但还缺 focused IDA 级别的第一批语义分支 / direct callee / out-slot 消费证据，暂不能单独判成 `auxiliary only` | 下一步: 只追 `0xfffffe000b828e50` 内部第一批语义性分支 / direct callee / out-slot 消费点，确认它是否只是 parser/materializer 子层，还是 first accepted-state lower-control helper
2026-06-19 14:58:37 +0800 | 目标: 在 `0xfffffe000b828e50` 已明显偏向 helper 后，继续判定它能否正式降级为 auxiliary-only parser/materializer 子层 | 动作: 新增并运行 `mps/ANE/experiments/ane_newinstance_b828e50_outslot_probe.py`，直接读取 `0xfffffe000b828e50` 的更长固定窗口，固化第一批 direct callee、success path 的 out-slot 写回点和 failure/retry path 的复位行为；同时再次派发 `ida` 子代理做 focused 分析，但本轮仍未在时限内返回有效结果，关闭后不作为结论依据 | 证据: `mps/ANE/.ane_runs/csv/ane_newinstance_b828e50_outslot_probe.csv`; `mps/ANE/.ane_runs/json/newinstance_b828e50_outslot_verdict_20260619.json`; 当前机器明确显示 first visible direct callee 依次为 `0xfffffe000b851124`、`0xfffffe000b79a1e4`、`0xfffffe000b8b16b0`、`0xfffffe000b8b3858`、`0xfffffe000b828970`；success path 只把 materialized range/length 风格的结果写回 caller：`[x28]=[x25+0x10]` 与 `[*saved_x7]=[x25+0x18]-[x25+0x10]`；failure/retry path 会再次 `str xzr, [x22]` 与 `str wzr, [x21]` | 结论: 本轮 verdict=`confirmed`；`0xfffffe000b828e50` 已可正式降级为 auxiliary-only parser/materializer 子层，它的 first decisive work 是 object lookup / validation / out-slot materialization，而不是 first accepted-state lower-control action | 下一步: 只追 `0xfffffe000b828e50` 之后第一处真正消费这些 materialized out-slot / range / object 结果并进入 accepted-state control 的 follow-on callee
2026-06-19 15:03:56 +0800 | 目标: 在 `0xfffffe000b828e50` 已正式降级后，确认哪个 follow-on callee 第一个真正消费其 materialized outputs 并进入 accepted-state control | 动作: 新增并运行 `mps/ANE/experiments/ane_newinstance_followon_callee_probe.py`，并行读取 `0xfffffe000b828970` 的固定窗口与前几个 follow-on callee (`0xfffffe000b851124` / `0xfffffe000b79a1e4` / `0xfffffe000b8b16b0` / `0xfffffe000b8b3858`) 的短窗口做角色对比；同时再次派发 `ida` 子代理，但仍未在时限内返回有效结果，关闭后不作为结论依据 | 证据: `mps/ANE/.ane_runs/csv/ane_newinstance_followon_callee_probe.csv`; `mps/ANE/.ane_runs/json/newinstance_followon_callee_verdict_20260619.json`; 当前机器明确显示 `0xfffffe000b828970` 是第一处直接收到 `x1=x22`, `x2=x21`, `x3=x20` 这组三元物化结果的 callee，并在 success path 写回 `str x9, [x22]`、`str w8, [x21]`、`strb w8, [x20]`；相比之下其前几层 callee 仍更像 ref/guard 或 object/intermediate preparation surfaces | 结论: 本轮 verdict=`confirmed`；`0xfffffe000b828970` 已是 `0xfffffe000b828e50` 之后 first visible follow-on accepted-state callee，也是当前最早同时消费 materialized outputs 并转成 accepted-state control outputs 的可见 surface | 下一步: 只追 `0xfffffe000b828970` 本身是不是 first accepted-state lower-control helper，还是更下层 decisive control 之前的中间 state/classification surface
2026-06-19 15:09:29 +0800 | 目标: 在 `0xfffffe000b828970` 已确认为 first visible accepted-state callee 后，判断它本身是不是 first lower-control helper，还是更下层 decisive control 前的中间 state/classification surface | 动作: 新增并运行 `mps/ANE/experiments/ane_newinstance_b828970_role_probe.py`，直接读取 `0xfffffe000b828970` 的长窗口，并把它后面的 enclosing caller `0xfffffe000b828a90` 一并纳入只读机器窗口，观察 `bl #0xfffffe000b828970` 之后是否继续把 `x22` 解包成更大结构；同时再次派发 `ida` 子代理，但仍未在时限内返回有效结果，关闭后不作为结论依据 | 证据: `mps/ANE/.ane_runs/csv/ane_newinstance_b828970_role_probe.csv`; `mps/ANE/.ane_runs/json/newinstance_b828970_role_verdict_20260619.json`; 当前机器明确显示 `0xfffffe000b828970` 本体可见工作主要是 state probing + object/flags/bool 写回到 `[x22]/[x21]/[x20]`，返回仍是 boolean-style success indicator；紧邻 caller `0xfffffe000b828a90` 在 `bl #0xfffffe000b828970` 之后继续把 `x22` 解包/搬运到 `x25` 指向的更大结果结构（`0xfffffe000b828bb8..0xfffffe000b828c34`） | 结论: 本轮 verdict=`confirmed`；`0xfffffe000b828970` 已可判定为 intermediate state/classification surface，而不是 final decisive lower-control helper；真正的 decisive control/state packaging 仍在它之后继续向下 | 下一步: 只追 enclosing caller `0xfffffe000b828a90` 中第一处把 `x22` 派生结果变成 real lower-control structure 的 packaging/handoff callee 或 step
2026-06-19 15:14:50 +0800 | 目标: 在 `0xfffffe000b828a90` 已成为当前最近 packaging/handoff surface 后，确认 first real lower-control packaging 是 direct callee 还是 inline step | 动作: 新增并运行 `mps/ANE/experiments/ane_newinstance_b828a90_packaging_probe.py`，直接读取 `0xfffffe000b828a90` 的固定窗口，并同时对 `0xfffffe000b8b0584`、`0xfffffe000b86e3f0`、`0xfffffe000b79b960` 做短窗口角色核验；同时再次派发 `ida` 子代理，但仍未在时限内返回有效结果，关闭后不作为结论依据 | 证据: `mps/ANE/.ane_runs/csv/ane_newinstance_b828a90_packaging_probe.csv`; `mps/ANE/.ane_runs/json/newinstance_b828a90_packaging_verdict_20260619.json`; 当前机器明确显示在 `bl #0xfffffe000b828970` 之后，first real packaging 不是新的 decisive callee，而是 inline window `0xfffffe000b828bb8..0xfffffe000b828c34`，其间 `x22` 派生字段被连续规范化并写入 `x25` 的多个偏移；随后才出现 `0xfffffe000b8b43a8` / `0xfffffe000b8afeac` / `0xfffffe000b85120c` 这类 operate-on-structure callee | 结论: 本轮 verdict=`confirmed`；在 `0xfffffe000b828a90` 之下，first real lower-control packaging step 不是 direct callee，而是 inline packaging window `0xfffffe000b828bb8..0xfffffe000b828c34` | 下一步: 只追这段 inline packaging 之后，`0xfffffe000b8b43a8` / `0xfffffe000b8afeac` / `0xfffffe000b85120c` 里哪个 first acts on the newly materialized `x25` structure，成为更接近 decisive lower-control logic 的下一表面
2026-06-19 15:20:34 +0800 | 目标: 在 first real packaging step 已经确认后，比较 inline packaging 之后的三个候选 callee，找出哪个 first truly acts on the newly materialized `x25` structure | 动作: 新增并运行 `mps/ANE/experiments/ane_newinstance_postpack_callee_probe.py`，直接读取 `0xfffffe000b8b43a8`、`0xfffffe000b8afeac`、`0xfffffe000b85120c` 的短窗口，并补读 caller `0xfffffe000b828c84` 之后的传参点与 control flow；同时再次派发 `ida` 子代理，但仍未在时限内返回有效结果，关闭后不作为结论依据 | 证据: `mps/ANE/.ane_runs/csv/ane_newinstance_postpack_callee_probe.csv`; `mps/ANE/.ane_runs/json/newinstance_postpack_callee_verdict_20260619.json`; 当前机器明确显示 `0xfffffe000b8b43a8` 是第一个以 `x0=sp` 进入、直接从新物化结构读取 `[x0+0x30]`、`[x0+0x28]`、`ldp [x0+8]` 并继续 stateful traversal 的 callee；`0xfffffe000b8afeac` 只是更后面的 conditional ref/count / lifecycle side path，`0xfffffe000b85120c` 则发生在结构再次归一化之后 | 结论: 本轮 verdict=`confirmed`；inline packaging 之后 first truly acts on the newly materialized `x25` structure 的 callee 已收紧成 `0xfffffe000b8b43a8` | 下一步: 只追 `0xfffffe000b8b43a8` 本身是不是 decisive lower-control surface，还是 inline packaging 之后的又一个 intermediate structure walker
2026-06-19 15:26:34 +0800 | 目标: 在 `0xfffffe000b8b43a8` 已成为 first post-packaging callee 后，判定它本身是不是 decisive lower-control surface | 动作: 新增并运行 `mps/ANE/experiments/ane_newinstance_b8b43a8_role_probe.py`，直接读取 `0xfffffe000b8b43a8` 的长窗口与其第一批 callee；并行派发 `reverse-engineer` 子代理只做仓库事实复核，结果同样倾向 `lean intermediate`；`ida` 子代理本轮仍未在时限内返回有效结果，关闭后不作为结论依据 | 证据: `mps/ANE/.ane_runs/csv/ane_newinstance_b8b43a8_role_probe.csv`; `mps/ANE/.ane_runs/json/newinstance_b8b43a8_role_verdict_20260619.json`; `reverse-engineer` 子代理确认当前 docs/json 现有证据一致将其视为“可能只是又一个 intermediate structure walker”；本地窗口明确显示该函数开头即读取新结构字段 `[x0+0x30]`、`[x0+0x28]`、`ldp [x0+8]`，并立即派发到 `0xfffffe000b79abf4` / `0xfffffe000b8b378c` / `0xfffffe000b8b0f38` 这一串 checks/link traversal helper；局部状态写回 `str x23, [x19,#0x30]` 也更像 walked node tracking 而不是 terminal commit | 结论: 本轮 verdict=`confirmed`；`0xfffffe000b8b43a8` 已可判定为 inline packaging 之后的又一个 intermediate structure walker，不是 final decisive lower-control surface | 下一步: 只比较它更深的两个候选 callee `0xfffffe000b8b378c` 与 `0xfffffe000b8b0f38`，找下一层更强的 decisive lower-control 候选
2026-06-19 15:32:27 +0800 | 目标: 在 `0xfffffe000b8b43a8` 已降级为 intermediate walker 后，比较 `0xfffffe000b8b378c` 与 `0xfffffe000b8b0f38` 谁是下一层更强的 decisive lower-control 候选 | 动作: 新增并运行 `mps/ANE/experiments/ane_newinstance_b8b378c_vs_b8b0f38_probe.py`，直接读取两者的更长窗口；并行派发 `reverse-engineer` 子代理只做仓库现有事实复核，确认此前没有偏向证据；`ida` 子代理本轮仍未在时限内返回有效结果，关闭后不作为结论依据 | 证据: `mps/ANE/.ane_runs/csv/ane_newinstance_b8b378c_vs_b8b0f38_probe.csv`; `mps/ANE/.ane_runs/json/newinstance_b8b378c_vs_b8b0f38_verdict_20260619.json`; 当前机器明确显示 `0xfffffe000b8b378c` 在轻量 flag/sibling-object 检查后，于 `0xfffffe000b8b3810` 直接 `bl #0xfffffe000b8b0f38`，自身更像上层 gate/wrapper；而 `0xfffffe000b8b0f38` 才继续做更深的 field-by-field comparison、range/base/flag equivalence 检查，并进入 `0xfffffe000b8b11f4` / `0xfffffe000b8686d8` / `0xfffffe000b84c128` / `0xfffffe000b8b1240` 这一更深 helper chain | 结论: 本轮 verdict=`confirmed`；下一层更强的 decisive lower-control 候选已收紧成 `0xfffffe000b8b0f38`，`0xfffffe000b8b378c` 应降级为 prefilter/wrapper | 下一步: 只追 `0xfffffe000b8b0f38` 本身是不是 decisive lower-control surface，还是还要继续下推到它的 post-check callees
2026-06-19 15:39:19 +0800 | 目标: 在 `0xfffffe000b8b0f38` 已成为当前最强候选后，判定它本身是不是 decisive lower-control surface | 动作: 新增并运行 `mps/ANE/experiments/ane_newinstance_b8b0f38_role_probe.py`，直接读取 `0xfffffe000b8b0f38` 的更长窗口与其 post-check helper chain；并行派发 `reverse-engineer` 子代理只做仓库现有事实复核，其结果为 `lean decisive`，即确认它较 wrapper 更深，但不构成“已终局 decisive”的反证；`ida` 子代理本轮仍未在时限内返回有效结果，关闭后不作为结论依据 | 证据: `mps/ANE/.ane_runs/csv/ane_newinstance_b8b0f38_role_probe.csv`; `mps/ANE/.ane_runs/json/newinstance_b8b0f38_role_verdict_20260619.json`; 当前机器明确显示 `0xfffffe000b8b0f38` 本体仍以 field-by-field equivalence / range/base/flag comparison 和 gate/branch 为主，只有在全部 checks 通过后才进入 `0xfffffe000b8b11f4` / `0xfffffe000b8686d8` / `0xfffffe000b84c128` / `0xfffffe000b8b1240` 这条 post-check helper chain；其中 `0xfffffe000b8686d8` 是第一处当前可见地对 downstream state 做实质更新（如 `str x19, [x1,#0x18]`、调整 `[x0,#0x60]`）的表面 | 结论: 本轮 verdict=`confirmed`；`0xfffffe000b8b0f38` 已可判定为 post-check wrapper/gate，而不是 final decisive lower-control surface；更深一层最强候选已收紧成 `0xfffffe000b8686d8` | 下一步: 只追 `0xfffffe000b8686d8` 本身是不是 decisive lower-control surface
2026-06-19 15:49:06 +0800 | 目标: 在 `0xfffffe000b8686d8` 已成为当前最强候选后，判定它本身是不是 decisive lower-control surface，并核验其内部最深 subcall 是否会反转这一判断 | 动作: 新增并运行 `mps/ANE/experiments/ane_newinstance_b8686d8_role_probe.py` 与 `mps/ANE/experiments/ane_newinstance_b864b10_terminal_probe.py`，分别读取 `0xfffffe000b8686d8` 与其内部 `0xfffffe000b864b10` 的固定窗口；并行派发 `reverse-engineer` 子代理只做仓库事实复核，得到 `lean decisive`；`ida` 子代理返回新的 machine-local blocker：当前机器现有 IDB / kernel 地址空间均不覆盖这些 `0xfffffe000b...` 地址，因此不能提供函数级 IDA 语义，只能记录 address-space mismatch | 证据: `mps/ANE/.ane_runs/csv/ane_newinstance_b8686d8_role_probe.csv`; `mps/ANE/.ane_runs/json/newinstance_b8686d8_role_verdict_20260619.json`; `mps/ANE/.ane_runs/csv/ane_newinstance_b864b10_terminal_probe.csv`; `mps/ANE/.ane_runs/json/newinstance_b864b10_terminal_verdict_20260619.json`; 当前机器明确显示 `0xfffffe000b8686d8` 在可见入口窗口里已直接做 downstream state 写入（`[x0,#0x60]` / `[x1,#0x18]`）并继续进入 index/bitmap/offset 处理；而 `0xfffffe000b864b10` 的本体只是 table/bitmap/index 扫描与局部 record 更新，写入很窄（`strh [x0,#4]`、`str [x12]`、`str [x0]`）且通过 `ldr x0, [x0]; ret` 返回，更像 internal algorithmic terminal sub-primitive | 结论: 本轮 verdict=`confirmed`；在当前机器可见静态证据里，`0xfffffe000b8686d8` 已是 strongest visible decisive lower-control surface so far，而 `0xfffffe000b864b10` 只是其下方的 internal terminal sub-primitive；若后续还要继续推进，默认不再做同层静态下钻，而应回到 runtime-facing 证据，验证 `0xfffffe000b8686d8` 这一层能否与 single-process reuse blocker family 建立更直接连接，或正式记录 matching-build / IDB address-space blocker | 下一步: 只做一个更小 probe，把 `0xfffffe000b8686d8` 这一可见 lower-control surface 与 single-process reuse blocker family 做最小 runtime-facing 连接验证；若不能连接，则明确归档 address-space blocker
2026-06-19 15:57:31 +0800 | 目标: 在 `0xfffffe000b8686d8` 已固定为 strongest visible lower-control surface 后，判定当前机器上是否已经存在把它与 `request +0x528..+0x547` blocker family 直接连起来的 runtime-facing bridge | 动作: 新增并运行 `mps/ANE/experiments/ane_runtime_bridge_or_blocker_probe.py`，只汇总当前 blocker provenance 证据（`request +0x528..+0x547`）、`0xfffffe000b8686d8` static surface 证据、以及 machine-local IDA address-space mismatch 事实；并行派发 `searcher` 与 `reverse-engineer` 子代理分别确认这些语义是否只集中在主线文档，以及现有仓库证据是否已经出现任何 direct bridge 线索 | 证据: `mps/ANE/.ane_runs/json/runtime_bridge_or_blocker_verdict_20260619.json`; 当前机器确认 `ANEServices` 仍只是 `request +0x528..+0x547` 的 later reader，visible daemon/helper 仍 request-blind，direct runtime authoring 该区域仍落在同一 wrapper rejection bucket；同时 `0xfffffe000b8686d8` 虽然已是 strongest visible lower-control surface，但 machine-local 仍没有 direct runtime-facing 证据把这两条链连接到同一 build/session；`ida` 侧新增 blocker 也已明确为 matching-build / IDB address-space mismatch | 结论: 本轮 verdict=`confirmed`；在当前机器上，对 single-process reuse 主线最准确的 runtime-facing 结论是：还没有 `request +0x528..+0x547` blocker family 到 `0xfffffe000b8686d8`-level lower-control surface 的 direct bridge evidence，当前硬阻塞就是 matching-build / IDB address-space mismatch | 下一步: 只做一个更小 probe：要么拿到覆盖 `0xfffffe000b...` 地址家族的 matching-build kernelcache / IDB，要么设计一个不依赖 IDA 覆盖的 runtime experiment，直接关联 `request +0x528..+0x547` 行为与 accepted-state lower path
2026-06-19 16:04:12 +0800 | 目标: 在 runtime bridge vs blocker 结论已经明确后，把“下一步到底先做 runtime experiment 还是先追 matching-build IDB”压成单一决策 | 动作: 新增并运行 `mps/ANE/experiments/ane_next_step_decision_probe.py`，并行派发 `doc-reader` / `searcher` 子代理压缩主线文档与现有 runtime/blocker 证据分布；确认 visible property construction 层已正式关闭、当前 strongest visible lower-control surface 已固定为 `0xfffffe000b8686d8`，而 matching-build / IDB blocker 已明确存在 | 证据: `mps/ANE/.ane_runs/json/next_step_decision_verdict_20260619.json`; `doc-reader` 子代理返回 `split decision`：当前下一最小动作应先做 focused runtime experiment，只有这步仍 `inconclusive` 才升级到 matching-build / IDB；`searcher` 子代理确认 `request +0x528..+0x547`、hidden-handle、accepted-state 与 single-process reuse 相关证据已经高度集中在现有主线文档与 results note 中，不缺候选列表，缺的是 direct bridge | 结论: 本轮 verdict=`confirmed`；当前机器上的最佳下一步不是直接跳 matching-build / IDB，而是先做一个不依赖 IDA 覆盖的最小 runtime experiment，直接尝试把 `request +0x528..+0x547` blocker family 与 accepted-state lower path 关联起来；只有这步失败或仍 `inconclusive`，才升级到 matching-build / IDB 路径 | 下一步: 只设计并运行一个 focused runtime experiment，测试 `request +0x528..+0x547` 行为与 accepted-state lower path 的最小可观测关联
2026-06-19 16:12:44 +0800 | 目标: 在“先做 runtime experiment”已经成为统一决策后，再把这个 runtime experiment 压缩成一个最小可执行改动 | 动作: 新增并运行 `mps/ANE/experiments/ane_runtime_experiment_design_probe.py` 与 `mps/ANE/experiments/ane_runtime_observable_gap_probe.py`；同时复读 `ane_inmemory_new_instance_probe.m` 中 `--services-runtime-request-inline-sha-matrix` 的现有实现，确认该路径目前只记录 `services_runtime_request_variant` / `services_runtime_request_layout` / `services_runtime_create_instance`，没有为每个 request variant 保留 `wrapper_device_layout` 或 `services_runtime_registry_attempt` 这类 lower-path-facing observable | 证据: `mps/ANE/.ane_runs/json/runtime_experiment_design_verdict_20260619.json`; `mps/ANE/.ane_runs/json/runtime_observable_gap_verdict_20260619.json`; 当前 matrix CSV 也已验证：`|req_` case 只有三类 phase，现有实验只能说明所有 inline-SHA 变体都停在同一 `wrapper_status=0x14` rejection bucket，却还看不到 lower-path-facing signal 是否随之变化 | 结论: 本轮 verdict=`confirmed`；当前最小 runtime experiment 不需要新建 harness，最小有用动作是扩展现有 `ane_inmemory_new_instance_probe`，让 `--services-runtime-request-inline-sha-matrix` 也按 request variant 记录 `wrapper_device_layout` 和/或 `services_runtime_registry_attempt` | 下一步: 只修改 `ane_inmemory_new_instance_probe` 的 request-inline-sha matrix 路径，把一个 lower-path-facing observable 挂进去，然后重跑 baseline / real sha / garbage sha 做差分
2026-06-19 16:20:18 +0800 | 目标: 在最小 runtime experiment 设计完成后，验证现有 harness 是否真的需要改代码，还是只需重编并复跑就能得到 lower-path-facing signal | 动作: 复读 `ane_inmemory_new_instance_probe.m`，确认 `run_services_create_instance_cases(...)` 的 request-variant loop 里源码已包含 `snapshot_services_registry(..., \"services_runtime_registry_attempt\", ...)`；随后强制重编 `ane_inmemory_new_instance_probe`，并重跑 `--services-runtime-request-inline-sha-matrix` 到新的 `ane_inmemory_new_instance_probe_request_inline_sha_matrix_rerun.csv`；最后新增并运行 `mps/ANE/experiments/ane_runtime_bridge_diff_probe.py` 汇总差分 | 证据: `mps/ANE/.ane_runs/csv/ane_inmemory_new_instance_probe_request_inline_sha_matrix_rerun.csv`; `mps/ANE/.ane_runs/json/runtime_bridge_diff_verdict_20260619.json`; 重跑后每个 request variant 现在都出现了 `services_runtime_registry_attempt` rows，说明之前的 gap 是 build/run gap 而不是设计 gap；但对比结果也明确显示：所有 inline-SHA 变体仍停在同一 `wrapper_status=0x14` bucket，新增 observable 只看到 `iokit_service entry` 随调用递增的普通 per-call service-instance churn，没有 real-sha vs garbage-sha 的 lower-path 分叉 | 结论: 本轮 verdict=`confirmed`；最小 runtime experiment 已真正跑通，但结果仍然是 negative direct bridge：当前 request-side inline-SHA authoring 还不能在可见 accepted-state lower path 上产生可区分的 lower-path-facing signal | 下一步: 只在同一 harness 上再找一个比 service-instance churn 更强的 lower-path-facing observable；如果没有，就升级到 matching-build / IDB
2026-06-19 16:27:03 +0800 | 目标: 在重跑 matrix 已经拿到第一批 lower-path-facing rows 后，验证再补一个更强 observable（`wrapper_device_layout`）是否能打破当前负结果 | 动作: 对 `ane_inmemory_new_instance_probe.m` 做最小补丁，仅在 request-variant loop 的 before/after wrapper 调用周围补写 `wrapper_device_layout`；随后强制重编并重跑 matrix 到 `ane_inmemory_new_instance_probe_request_inline_sha_matrix_rerun_v2.csv`，再新增并运行 `mps/ANE/experiments/ane_runtime_bridge_diff_v2_probe.py` 汇总差分 | 证据: `mps/ANE/.ane_runs/csv/ane_inmemory_new_instance_probe_request_inline_sha_matrix_rerun_v2.csv`; `mps/ANE/.ane_runs/json/runtime_bridge_diff_v2_verdict_20260619.json`; 现在每个 request variant 同时拥有 `services_runtime_registry_attempt` 和 `wrapper_device_layout` rows，但新加入的 `wrapper_device_layout` 在 baseline / real mmap / real sha / garbage sha 上完全不分叉：`owner_state=1`, `service_ready=0`, `service_connect=0x5403` 全不变 | 结论: 本轮 verdict=`confirmed`；现有 harness 上已尝试的 lower-path-facing observable family 基本耗尽，当前只能暴露普通 per-call service-instance churn，仍没有 request-variant-specific lower-path branch signal | 下一步: 只判断是否还能在同一 harness 上挑出明显更强的 observable；若不能，就升级到 matching-build / IDB
2026-06-19 16:40:52 +0800 | 目标: 在同一 harness observable family 已基本耗尽后，把 matching-build / IDB 路径压成一个真正可执行的下一步 | 动作: 新增并运行 `mps/ANE/experiments/ane_matching_build_artifact_probe.py` 与 `mps/ANE/experiments/ane_matching_build_im4p_probe.py`；主线程枚举当前 host 的 Preboot kernelcache candidates、对选定 candidate 做 `file` / `xxd` 级头部确认、并测试 `kmutil inspect --show-fileset-entries --kernel <candidate>`；同时检查当前 host PATH 是否已有 `img4` / `img4tool` / `ipsw` | 证据: `mps/ANE/.ane_runs/json/matching_build_artifact_verdict_20260619.json`; `mps/ANE/.ane_runs/json/matching_build_im4p_verdict_20260619.json`; 当前 host 已暴露多个 Preboot kernelcache candidate，但它们只识别成 generic `data`；选定 candidate 头部明确是 `IM4P`/`krnl` 容器；当前 host 又没有现成 `img4` / `img4tool` / `ipsw` 解包工具，因此 matching-build 路径的下一最小步不是 `idb_open` 本身，而是先建立 host-local IM4P 提取能力 | 结论: 本轮 verdict=`confirmed`；matching-build / IDB 路径现在已经精确收敛到一个单一 blocker：缺少把选定 Preboot `IM4P` kernelcache 工件解成 decode-capable payload 的 host-local 提取路径 | 下一步: 只做一个更小 probe：建立一个 host-local IM4P 提取路径，然后重新验证 `kmutil` / 后续 IDA 是否能真正消费解包后的 payload
2026-06-19 18:21:44 +0800 | 目标: 解除 matching-build / IDB 的 IM4P 提取阻塞，并确认解包后的 payload 是否已进入 decode-ready kernelcache 形态 | 动作: 新增并运行 `mps/ANE/experiments/ane_im4p_extract_probe.py`，用最小 DER 解析直接提取选定 Preboot `IM4P` 容器的主 `OCTET STRING` payload，再调用系统自带 `/usr/bin/compression_tool -decode -a lzfse` 解出 decoded payload；随后用 `file` 与 `kmutil inspect -B --show-fileset-entries` 验证输出形态 | 证据: `mps/ANE/.ane_runs/json/im4p_extract_probe_verdict_20260619.json`; `mps/ANE/.ane_runs/tmp/kernelcache.release.mac15s.payload.bin`; `mps/ANE/.ane_runs/tmp/kernelcache.release.mac15s.payload.decoded.bin`; 当前提取结果 payload magic 为 `bvx2`，decoded 文件大小为 `117817344` bytes；`file` 识别其为 `Mach-O 64-bit arm64e`；`kmutil inspect -B` 已把它识别成 boot kernel collection / fileset，并直接枚举出 `com.apple.kernel` 等 `LC_FILESET_ENTRY` | 结论: 本轮 verdict=`confirmed`；host-local IM4P 提取阻塞已正式解除，matching-build 路径现在不再卡在工件解包层，而是推进到“IDA / `idb_open` 是否能直接消费 decoded payload”这一更窄的消费层问题 | 下一步: 只对 `/Volumes/2T/pymss/mps/ANE/.ane_runs/tmp/kernelcache.release.mac15s.payload.decoded.bin` 做 `idb_open` 最小可行性 probe；若成功，立即进入 matching-build address family 的 IDA 语义分析；若失败，只记录精确失败层
2026-06-19 18:38:57 +0800 | 目标: 把 matching-build 路径从“decoded payload 可见”进一步压成“IDA 到底卡在哪一层”，同时确认现成解包入口是否可复用 | 动作: 委派 `ida` 子代理只对 `mps/ANE/.ane_runs/tmp/kernelcache.release.mac15s.payload.decoded.bin` 做最小 `idb_open` probe；主线程并行用 `/Users/baicai1145/miniconda3/bin/pyimg4` 复核同一 `IM4P` 工件的 `info/extract`，再与系统自带 `compression_tool` 链路做逐字节对比，并用 `kmutil inspect -B --show-fileset-entries` 读取当前 decoded collection 的 ANE 相关 entry | 证据: 子代理返回 `idb_open` 在 `prefer_headless` / `force_headless` / `prefer_gui` 下均失败，底层 `idapro.open_database()` 为 `ERR_OPEN(4)`；`pyimg4 im4p info` 明确给出 `Data compression type: LZFSE`, `Encrypted: False`；`pyimg4 im4p extract` 成功产出 `mps/ANE/.ane_runs/tmp/kernelcache.release.mac15s.pyimg4.decoded.bin`，且与 `mps/ANE/.ane_runs/tmp/kernelcache.release.mac15s.payload.decoded.bin` 逐字节一致；`kmutil inspect -B` 当前已直接暴露 `com.apple.driver.AppleH11ANEInterface`、`com.apple.driver.AppleT6030ANEHAL`、`com.apple.iokit.IOSurface` 等 fileset entry | 结论: 本轮 verdict=`confirmed`；当前阻塞已再收紧一层：不是 IM4P 解包，不是 decoded collection 不可识别，而是 `idalib` 不能直接消费整个 decoded fileset collection；下一层合理入口必须改成“拆单个 fileset entry / 更窄 Mach-O 再试 `idb_open`” | 下一步: 只做一个更小 probe：从当前 decoded collection 中抽出一个单 ANE fileset entry（默认优先 `AppleH11ANEInterface` 或 `AppleT6030ANEHAL`），再对该单 entry 做 `idb_open` 最小可行性验证
2026-06-19 19:12:06 +0800 | 目标: 把“整包不可被 idalib 消费”的 blocker 收紧成一个真正可用的单 entry IDA 入口 | 动作: 新增并迭代 `mps/ANE/experiments/ane_fileset_entry_extract_probe.py`，从 decoded fileset collection 中抽出 `AppleH11ANEInterface` 单 entry，生成 `AppleH11ANEInterface.slice.bin` 与 `AppleH11ANEInterface.patched.macho`；主线程同时做字节级 load-command 核对；随后委派 `ida` 子代理只对 `AppleH11ANEInterface.patched.macho` 做最小 `idb_open` probe | 证据: `mps/ANE/.ane_runs/json/fileset_entry_extract_probe_verdict_20260619.json`; `mps/ANE/.ane_runs/tmp/AppleH11ANEInterface.patched.macho`; 主线程已确认该单 entry 文件被 `file` 识别为 `Mach-O 64-bit kext bundle arm64e`；`ida` 子代理返回 `prefer_headless` 下 `idb_open` 直接成功，当前 `session_id=34a08b79`，无需 GUI 或降级 | 结论: 本轮 verdict=`confirmed`；matching-build 路径已经正式打通一个 machine-local 可复用的 headless IDA 入口：`AppleH11ANEInterface.patched.macho`。当前 blocker 已不再是“找不到可消费入口”，而是“这个入口对 lower control 的语义覆盖是否足够”。 | 下一步: 只基于 `session_id=34a08b79` 做最小语义下钻，优先 selector / `externalMethod` / `ProgramCreateInstance` / `ProgramSendRequest` / request-descriptor-chain
2026-06-19 19:24:31 +0800 | 目标: 在 `AppleH11ANEInterface` 单 entry 已能被 headless IDA 打开后，把第一层控制语义收紧成可操作的 selector 映射事实 | 动作: 委派 `ida` 子代理基于 `session_id=34a08b79` 先确认 `externalMethod` 的 dispatch 形态，再窄解析 `sANEDriverClientMethods` 的表项顺序；主线程不做重叠 IDA 工作，只收高密度事实回包并持久化 | 证据: 子代理确认 `H11ANEInUserClient::externalMethod` (`0xfffffe00092abdd8`) 与 `H11ANEInDirectPathClient::externalMethod` (`0xfffffe00092abfac`) 都委托给 `IOUserClient2022::dispatchExternalMethod`；`sANEDriverClientMethods` 位于 `0xfffffe000801e818`，共有 17 个表项；当前已恢复关键 selector 映射：selector `2` → `ANE_ProgramSendRequest`，selector `8` → `ANE_ProgramCreateInstance`；相邻顺序已确认 `0:ANE_DeviceOpen`, `1:ANE_DeviceClose`, `2:ANE_ProgramSendRequest`, `3:ANE_ProgramCreate`, `4:ANE_ProgramPrepare`, `5:ANE_ProgramUnprepare`, `6:ANE_ProgramDestroy`, `7:ANE_GetStatus`, `8:ANE_ProgramCreateInstance`, `9:ANE_ProgramChainingPrepare` | 结论: 本轮 verdict=`confirmed`；当前 selector-level 第一层语义已经足够明确，下一层问题不再是 dispatch 表顺序，而是 selector `2` / `8` 进入 `ANEClientDevice::*` 之后哪一段 first deeper stateful control 最贴近 private ANE single-process reuse blocker | 下一步: 只在 selector `2` / `8` 中选一个更接近 blocker 的 wrapper（默认优先 selector `8` / `ProgramCreateInstance`），继续恢复其进入 `ANEClientDevice::*` 后的 first deeper stateful control 链
2026-06-19 19:31:02 +0800 | 目标: 在 selector-level mapping 已经明确后，把下一轮唯一 deeper target 再收紧成一条单链，而不是继续在 selector `2` / `8` 间摇摆 | 动作: 基于当前已确认的 selector 映射与既有 create-instance / newinstance 主线，对当前 deeper target 做一次只读选择收敛；同时委派 `ida` 子代理只尝试恢复 selector `8` / `ANE_ProgramCreateInstance` 进入 `ANEClientDevice::*` 后的第一跳与 first deeper stateful control，但本轮未在时限内返回足够小的事实包，不把它当结论依据 | 证据: 当前已确认 selector `8` → `ANE_ProgramCreateInstance`，而这一条与历史上 `ANEHWDevice::ANE_ProgramCreateInstance_gated`、accepted-state control、newinstance 主线最直接对齐；相比之下 selector `2` / `ANE_ProgramSendRequest` 目前更像次级平行入口，尚无证据显示它比 selector `8` 更接近当前 blocker | 结论: 本轮 verdict=`confirmed`；当前默认 deeper target 已可正式固定为 selector `8` / `ANE_ProgramCreateInstance` 进入 `ANEClientDevice::*` 后的 first deeper stateful control；下一轮不应再回到 selector 选择题，而应只恢复这条单链的下一跳与第一处 clearly stateful control | 下一步: 只基于 `session_id=34a08b79` 沿 selector `8` / `ANE_ProgramCreateInstance` 继续下钻一跳，恢复 wrapper 调到的 `ANEClientDevice::*` 方法名 / 地址与其 first direct callee 或 first clearly stateful branch
2026-06-19 19:38:44 +0800 | 目标: 在 selector `8` 已成为当前唯一默认 deeper target 后，恢复 `ANE_ProgramCreateInstance` wrapper 的下一跳与第一处更深 stateful 点 | 动作: 先重新打开 `AppleH11ANEInterface.patched.macho` 为新会话 `appleh11_entry`，再委派 `ida` 子代理只沿 selector `8` / `ANE_ProgramCreateInstance` 窄下钻一层；主线程不做重叠 IDA 工作，只收最小调用链与直接证据 | 证据: `mcp__ida_pro_mcp.idb_open` 成功恢复 `session_id=appleh11_entry`；`ida` 子代理确认 `ANE_ProgramCreateInstance` wrapper 位于 `0xfffffe00092acd38`，先两次调 `ANEClientDevice::getClient()` (`0xfffffe00092a7238`)，随后通过 tail branch 直接跳到 `ANEClientDevice::programCreateInstance(ANEProgramParamsWrapper*)` (`0xfffffe00092a85a4`)；该方法内当前最早的 stateful 候选点为 `0x92a8678: bl 0xbe6e210`（导入的 alloc/new-like callee）与 `0x92a86b8: blraa [x19+0x218]`（对象相关 vtable dispatch） | 结论: 本轮 verdict=`confirmed`；当前 deeper chain 已从 selector-level wrapper 再收紧一层，下一层问题不再是“下一跳方法是谁”，而是 `ANEClientDevice::programCreateInstance` 体内 `bl 0xbe6e210` 与 `blraa [x19+0x218]` 哪个 first deeper stateful control 更贴近 private ANE single-process reuse blocker | 下一步: 只在 `0x92a85a4` 内继续区分 `bl 0xbe6e210` 与 `blraa [x19+0x218]` 的角色，默认优先追 `blraa [x19+0x218]` 的对象/方法族
2026-06-19 19:45:12 +0800 | 目标: 在 `ANEClientDevice::programCreateInstance` 内部两个 earliest stateful 候选点之间做最终判决，避免下一轮继续比较 A/B | 动作: 委派 `ida` 子代理只围绕 `0x92a8678: bl 0xBE6E210` 与 `0x92a86b8: blraa [x19+0x218]` 做窄角色判断；主线程不做重叠 IDA 工作，只等待“谁更像 first deeper stateful control”的最小结论 | 证据: 子代理确认 `0xBE6E210` 的参数形态为 `ptr=*a2`, `size=0x35E18`, `flags=0x20003`, `task=this+0x18`，更像 IOKit / Buffer descriptor / request object 的分配/构造辅助函数；同时确认 `blraa [x19+0x218]` 的 `x19` 正是 `0xBE6E210` 的返回值，因此其角色更像消费该对象的状态查询/校验，而非入口侧 first control | 结论: 本轮 verdict=`confirmed`；当前 `selector 8` deeper chain 的 first deeper stateful control 已正式收紧为 `0xBE6E210`，`blraa [x19+0x218]` 只是后续消费该对象的状态查询点 | 下一步: 只追 `0xBE6E210` 的具体角色与返回对象类型，确认它更接近 IOKit 分配器、Buffer descriptor 工厂，还是 `ANERequest` / companion object materializer
2026-06-19 19:52:08 +0800 | 目标: 在 `0xBE6E210` 已成为唯一默认 deeper target 后，把它的角色从“抽象分配辅助”再收紧成具体对象族，并据此重新定义更贴近 ANE 业务态的下一跳 | 动作: 委派 `ida` 子代理只围绕 `0xBE6E210` 的参数模式、反编译类型信息与返回对象后续 vtable 用法做窄判断；主线程不做重叠 IDA 工作，只收最小对象族结论 | 证据: 子代理确认 `ANEResource::create<ANEResourceType4>` 的反编译里已将该调用显式标注为 `IOMemoryDescriptor *` 工厂；参数模式为 `(aligned_size, raw_size, direction_flags|0x10000, owning_task)`，与 `IOBufferMemoryDescriptor::withFlags` / `IOMemoryDescriptor` DMA backing-memory 工厂一致；返回值随后被当作 `IOMemoryDescriptor` 进行 `prepare/complete` / vtable 生命周期操作 | 结论: 本轮 verdict=`confirmed`；`0xBE6E210` 不是 `ANERequest` 业务对象构造器，而是 DMA/backing-memory 工厂。当前更贴近 private ANE single-process reuse blocker 的下一层问题，已经从“分配器本体”切换为“谁 first consumes 这个 IOMemoryDescriptor 并把它转成 `ANEResource` / request-specific state” | 下一步: 只沿 `ANEResource::create<ANEResourceType4>` 或 `programSendRequest` 中消费该 `IOMemoryDescriptor` 的路径继续下钻，恢复 first ANE-specific resource/state materialization step
2026-06-19 19:58:41 +0800 | 目标: 在 `0xBE6E210` 的对象族已经确认后，继续追其 first ANE-specific consumer，但先验证当前 `AppleH11ANEInterface` 单 entry 的 IDA 入口是否还能稳定复用 | 动作: 主线程直接对 `AppleH11ANEInterface.patched.macho` 再次执行 `mcp__ida_pro_mcp.idb_open(preferred_session_id=appleh11_state, prefer_headless, no auto analysis)`；本轮不再扩散语义查询，只先验证会话重建稳定性 | 证据: 本轮 `idb_open` 直接失败：`Failed to open database: /Volumes/2T/pymss/mps/ANE/.ane_runs/tmp/AppleH11ANEInterface.patched.macho`。这与此前会话 `34a08b79` / `appleh11_entry*` 丢失现象一致，说明当前问题已临时回退到 `ida-pro-mcp` 会话重建稳定性，而非更深的资源/状态语义判断 | 结论: 本轮 verdict=`inconclusive`；当前更小 blocker 不是“找不到 next consumer”，而是无法稳定恢复 `AppleH11ANEInterface` 单 entry 的可复用 IDA 会话。下一轮必须先解决会话重建/worker 可达性，再继续沿 `IOMemoryDescriptor -> ANEResource/request state` 下钻 | 下一步: 只恢复稳定可复用的 `AppleH11ANEInterface` IDA 会话，然后继续追 `IOMemoryDescriptor` 的 first consumer
2026-06-19 20:05:17 +0800 | 目标: 在会话重建稳定性已成为当前唯一 blocker 后，把它从“整体不稳定”再收紧成可操作的最小恢复路径 | 动作: 先用 `idb_list` / `lsof` / `ps` 确认现有 `AppleH11ANEInterface.patched.macho.i64` 对应的 orphan worker 与 loose IDB 占用；随后主线程强制清掉 `pid=20094`，再并行测试 `.i64` 与原始 `patched.macho` 的重开能力 | 证据: `idb_list` 暴露了一个空 session_id 的活动 worker，指向 `AppleH11ANEInterface.patched.macho.i64`；`lsof -p 20094` 确认其持有 `.id0/.id1/.nam`；清掉 orphan worker 后，`idb_open(AppleH11ANEInterface.patched.macho.i64, preferred_session_id=appleh11_i64_reopen)` 成功，而同轮 `idb_open(AppleH11ANEInterface.patched.macho, preferred_session_id=appleh11_macho_reopen)` 仍失败 | 结论: 本轮 verdict=`confirmed`；当前会话工程层的最小边界已明确：`.i64` 是稳定可复用入口，原始 patched Mach-O 不是。会话 blocker 已足够收敛，不应再停留在“能否恢复会话”的泛问题，而应直接基于 `appleh11_i64_reopen` 继续追 `IOMemoryDescriptor` 的 first ANE-specific consumer | 下一步: 只基于 `appleh11_i64_reopen` 会话沿 `ANEResource::create<ANEResourceType4>` / `programSendRequest` 继续下钻，恢复 first consumer that turns `IOMemoryDescriptor` into `ANEResource` / request-specific state
2026-06-19 20:12:54 +0800 | 目标: 在 `.i64` 会话恢复后，把 `IOMemoryDescriptor` 消费链从“抽象资源化”再收紧成具体的 first ANE-specific consumer | 动作: 委派 `ida` 子代理基于 `appleh11_i64_reopen`，只沿 `ANEResource::create<ANEResourceType4>` / `programSendRequest` 两条局部路径追 `IOMemoryDescriptor` 的 first consumer；主线程不做重叠 IDA 工作，只收最小调用链与直接证据 | 证据: 子代理确认 `clientMemoryForType` 先产出 `IOMemoryDescriptor*`，随后经 `ANEResourceCreationParams` 直接送入 `ANEClientResource::create`（`0xfffffe00092494ac`）；这是 first ANE-specific resource 构造函数。`ANEGroupResource::create` 等更高层函数处理的是已封装好的 `shared_ptr<ANEResource>`，不再直接接触原始 descriptor | 结论: 本轮 verdict=`confirmed`；当前 deeper chain 已从 IOKit memory descriptor 层正式推进到 first ANE-specific consumer：`ANEClientResource::create`。下一层问题不再是“谁 first consumes descriptor”，而是 `ANEClientResource::create` 内部如何进一步 materialize 成更贴近 request/group/lower control blocker 的状态 | 下一步: 只沿 `ANEClientResource::create` (`0xfffffe00092494ac`) 继续下钻，恢复其 first deeper materialization / handoff step
2026-06-19 20:19:36 +0800 | 目标: 在 `ANEClientResource::create` 已成为当前唯一 default deeper target 后，再把其内部资源 materialization 与 group handoff 收紧成一个更具体的下一跳 | 动作: 委派 `ida` 子代理基于 `appleh11_i64_reopen`，只对 `ANEClientResource::create` 做窄下钻，恢复其 first materialization step 与 first handoff step；主线程不做重叠 IDA 工作，只收最小调用链与地址事实 | 证据: 子代理确认 `ANEClientResource::create` 内部先调用 `ANEResource::create<ANEResourceType0>`（`0xfffffe000926ae30`）完成资源实例化，并通过 `ANEResource::C1` → `ANEResource::C2` 完成对象构造；随后 first handoff 到 `ANEResourceCollection::addResource`（`0xfffffe0009271644`），将已构造的 `shared_ptr<ANEResource>` 注册到 group/collection | 结论: 本轮 verdict=`confirmed`；当前 deeper chain 已正式推进到 first materialization + group handoff 层。下一层问题不再是 `ANEClientResource::create` 内部 first step 是谁，而是 `ANEResourceCollection::addResource` 之后谁 first consumes 已注册资源并把它推进到更贴近 request/lower control blocker 的状态 | 下一步: 只沿 `ANEResourceCollection::addResource` (`0xfffffe0009271644`) 之后的 consumer 继续下钻
2026-06-19 20:27:48 +0800 | 目标: 在 `ANEResourceCollection::addResource` 已成为当前唯一 default deeper target 后，尝试直接恢复其 post-registration first consumer，但先验证当前活跃 IDA 会话是否可被主线程稳定引用 | 动作: 先委派 `ida` 子代理只做一次 `xref_query(addr=0xfffffe0009271644, direction=from, xref_type=code)`；子代理确认存在一个活跃会话 `da37b74f` 并建议下一步直接 `decompile(addResource)`。主线程随后尝试直接对该会话做 `decompile`，但因 `idb_list` 返回的活跃 worker `session_id` 为空串、命名会话 `appleh11_i64_reopen` 又处于 `is_active=false`，无法稳定以 `database=<session_id>` 形式继续引用当前分析态 | 证据: `idb_list` 同时暴露了 `appleh11_i64_reopen`（可命名但 inactive）与一个 `is_active=true` 的 `AppleH11ANEInterface.patched.macho` worker（`session_id=\"\"`）；子代理能在该活跃 worker 上拿到 `xref_query` 结果，但主线程后续 `decompile` 无法稳定引用该会话 | 结论: 本轮 verdict=`inconclusive`；当前最小 blocker 已从“谁是 post-registration first consumer”回退为“活跃会话不可直接地址化”。在没有一个 MCP 可直接引用的活跃 session id 前，不应继续扩散 `addResource` 之后的语义分析 | 下一步: 只恢复一个 MCP 可直接引用的 `AppleH11ANEInterface` 活跃会话 id，然后继续 `ANEResourceCollection::addResource` 的函数体反编译
2026-06-19 20:34:22 +0800 | 目标: 在活跃会话不可地址化后，把会话工程层再次收紧成可复用入口，并立即用它推进 `addResource` 之后的 consumer 家族识别 | 动作: 主线程先用 `server_health` / `lookup_funcs` / `decompile` 确认命名会话 `appleh11_i64_reopen` 已不可达；随后清掉新的活跃但不可地址化 worker（持有 `.id0/.id1/.nam` 的 `pid=33139`），只重开 `.i64` 为 `appleh11_i64_live`，再直接对 `ANEResourceCollection::addResource` 做 `decompile + xref_query` | 证据: `idb_open(AppleH11ANEInterface.patched.macho.i64, preferred_session_id=appleh11_i64_live)` 成功，且 `idb_list` 明确显示 `appleh11_i64_live is_active=true`；`decompile(addResource)` 与 `xref_query(addResource, both, code)` 暴露出 post-registration consumer family：`ANE_ProgramPrepareAndSubmitRequest_gated (0xfffffe000929c47c)`、`ANE_MemoryMapRequest_gated (0xfffffe00092a0ac8)`、`ANEBufferCache::cacheResource (0xfffffe000930737c)`、`ANEGroupResource::addResource (0xfffffe000924c180)` | 结论: 本轮 verdict=`confirmed`；会话工程层 blocker 已被重新收敛并再次穿透。当前不应再问“怎么拿会话”，而应直接沿最贴近 private ANE request/control 主线的 `ANE_ProgramPrepareAndSubmitRequest_gated` 继续下钻 | 下一步: 只基于 `appleh11_i64_live` 沿 `ANE_ProgramPrepareAndSubmitRequest_gated` 恢复已注册资源 first turns into request/control state 的步骤
2026-06-19 20:41:11 +0800 | 目标: 在 `ANE_ProgramPrepareAndSubmitRequest_gated` 已成为当前唯一 default deeper target 后，把已注册资源进入 request/control state 的边界再收紧成一个可继续下钻的最小步骤 | 动作: 委派 `ida` 子代理基于 `appleh11_i64_live`，只对 `ANE_ProgramPrepareAndSubmitRequest_gated` 做窄下钻；主线程不做重叠 IDA 工作，只收最小调用链与关键地址事实 | 证据: 子代理确认已注册 `shared_ptr<ANEResource>` 在该链中先经历局部 `ANEResourceCollection` 构造、resource 拷贝、`ANEUnionResource::incrementUseCount`、`ANE_ProgramCheckandPrewireBuffers_gated`，随后在 `0xfffffe000929c7a4` 的 `ANERequest::create()` → `ANERequest::init()` 处 first turns into request/control state；再往后依次暴露 `wireResources` (`0xfffffe000929f154` callsite)、`dartMapResources(bool)` (`0xfffffe000929f19c`)、`aneCmdSend(...)` (`0xfffffe000929f6e0`) 作为更下层硬件相关步骤 | 结论: 本轮 verdict=`confirmed`；当前 deeper chain 已正式推进到 request/control 边界，下一层问题不再是“谁 first turns resource into request”，而是 wire/map/send 链中哪一段 first touches hardware-facing lower control | 下一步: 只沿 `ANERequest::wireResources()` / `ANERequest::dartMapResources(bool)` / `ANEHWDevice::aneCmdSend(...)` 继续下钻，默认优先 `wireResources`
2026-06-19 14:55:21 +0800 | 目标: 在 `ANEHWDevice::ANE_ProgramCreateInstance_gated` 已成为当前唯一入口后，确认最早的共同窗口是不是已经算语义交汇 | 动作: 复用 `ane_bootkc_create_instance_gated_probe.csv`，新增并运行 `mps/ANE/experiments/ane_newinstance_create_instance_joinpoint_probe.py`，自动在反汇编里搜索最早同时出现 x19 与 x25 并紧邻 branch/call/write 的窗口 | 证据: `mps/ANE/.ane_runs/json/newinstance_create_instance_joinpoint_verdict_20260619.json`; 当前最早共同窗口是 `0xfffffe000928c624: cbz x1`，其上下文只包含 `mov x25, x3`、`mov x19, x1` 和非空参数校验 | 结论: 本轮 verdict=`confirmed`；最早共同窗口只是浅层 non-null validation，不是 first semantic join point | 下一步: 跳过这类浅层参数校验窗口，继续在 `ANEHWDevice::ANE_ProgramCreateInstance_gated` 中找更深层的 first semantic join point
2026-06-19 20:52:03 +0800 | 目标: 在 request/control 边界之后，把 wire/map/send 三个候选点再收紧成唯一的 first hardware-facing lower-control transition | 动作: 委派 `ida` 子代理基于 `appleh11_i64_live`，只对 `ANERequest::wireResources()`、`ANERequest::dartMapResources(bool)`、`ANEHWDevice::aneCmdSend(...)` 做窄角色判定；主线程不做重叠 IDA 工作，只收三选一判决与最小证据 | 证据: 子代理确认 `wireResources` 是 child-resource wire loop，`dartMapResources` 是 child-resource DART-map loop，二者都仍停留在 resource preparation 层；而 `ANEHWDevice::aneCmdSend(...)` 继续进入 `aneFirmwareCommandSend(...)` → `IOProcessorChannelSendRetry(...)`，首次触及真实 IOKit firmware channel | 结论: 本轮 verdict=`confirmed`；当前链上的 first hardware-facing lower-control transition 已正式收紧为 `ANEHWDevice::aneCmdSend(...)`。下一层问题不再是 wire/map/send 三选一，而是 `IOProcessorChannelSendRetry(...)` 前后的 command send / completion / writeback 路径 | 下一步: 只沿 `ANEHWDevice::aneCmdSend(...)` → `aneFirmwareCommandSend(...)` → `IOProcessorChannelSendRetry(...)` 继续下钻
2026-06-19 21:03:44 +0800 | 目标: 在 `ANEHWDevice::aneCmdSend(...)` 已成为唯一 hardware-facing deeper target 后，把 send gate 前后的最小 payload / completion 边界再收紧成一个可继续下钻的问题 | 动作: 委派 `ida` 子代理基于 `appleh11_sendpath`，只对 `aneFirmwareCommandSend(...)` 与 `IOProcessorChannelSendRetry(...)` 前后做窄梳理；主线程不做重叠 IDA 工作，只收 payload 组装字段与 completion 最小路径 | 证据: 子代理确认 `IOProcessorChannelSendRetry` 之前 `ANEFirmwareCommandState` payload 已被打包完成，关键字段包括 `+0x50` carrier pointer、`+0x68` resource key、`+0x70` callback/function family、`+0x90` live flag；send 后 response 侧最关键的已确认路径是 `processCommandResponse` → `handleOutstandingCommand`；当前 unresolved 的下一层问题是 firmware→H11 echo/response 如何形成 `payload+0x50` 的 untagged match | 结论: 本轮 verdict=`confirmed`；当前 deeper chain 已从 hardware-facing send gate 推进到 response/completion 边界。下一层问题不再是 command send 本身，而是 `processCommandResponse` / `handleOutstandingCommand` 路径中的 first completion / writeback / callback 分叉 | 下一步: 只沿 `processCommandResponse` → `handleOutstandingCommand` 继续下钻
2026-06-19 21:10:42 +0800 | 目标: 在 `aneCmdSend -> IOProcessorChannelSendRetry` 已成为当前唯一 hardware-facing deeper target 后，把 response/completion 边界再收紧成可继续下钻的最小问题 | 动作: 委派 `ida` 子代理基于 `appleh11_response`，只对 `processCommandResponse` / `handleOutstandingCommand` 做窄下钻；主线程不做重叠 IDA 工作，只收 match 机制与 completion/writeback 最小分叉 | 证据: 子代理确认 `processCommandResponse` 位于 `0xfffffe00092d2960`；`payload+0x50` 当前已可确认是 command tag/identifier，匹配机制是直接等值比较 `*(cmdAddr+0x50) == responseTag`；match 时直接进入 `handleOutstandingCommand(this, stateObj, true)`；mismatch 且 `payload+0x90` 未标记已处理时，走 `IOProcessorChannelSendRetry` 重发/writeback 路径；`handleOutstandingCommand` 内部下一层关键分叉是 `stateObj->field_0x68` 是否非空，非空时进入 request completion callback 链 | 结论: 本轮 verdict=`confirmed`；当前 deeper chain 已从 hardware-facing send gate 推进到 response/completion 分叉边界。下一层问题不再是 `payload+0x50` 如何比较，而是 `handleOutstandingCommand` 内部的 first completion / writeback / callback 分叉 | 下一步: 只沿 `handleOutstandingCommand` 继续下钻
2026-06-19 21:18:16 +0800 | 目标: 在 `processCommandResponse -> handleOutstandingCommand` 已成为当前唯一 completion deeper target 后，把其内部 first completion/writeback/callback 分叉再收紧成一条可继续下钻的 callback 主线 | 动作: 委派 `ida` 子代理基于 `appleh11_completion`，只对 `handleOutstandingCommand` 做窄下钻；主线程不做重叠 IDA 工作，只收分叉条件、关键函数和共享尾部事实 | 证据: 子代理确认 `handleOutstandingCommand` 位于 `0xfffffe00092d2274`；在 `state->completed = success` 之后，first completion 下存在三路分叉：1) `callbackFunc != 0 && callbackArg != 0 && success==1` → `_B618BF0()` callback 路径；2) 失败或 fallback 条件 → `DeviceMemoryManager::Free(...)` writeback/free 路径；3) 特定 flag 下仍走 `_B618BF0()` 的 mixed fallback callback；三路最终都汇入共享尾部：`commandWakeup` / `lookupProgramResource` / callbackArg vtable[6] / `removeObject` | 结论: 本轮 verdict=`confirmed`；当前 response/completion 边界的关键问题不再是“是否有分叉”，而是 **Callback** 这一路如何继续进入 request completion 链。下一层问题已收紧为 `_B618BF0()` 之后的 callback continuation | 下一步: 只沿 `handleOutstandingCommand` 的 Callback 分叉继续下钻
2026-06-19 21:27:11 +0800 | 目标: 在 `handleOutstandingCommand` Callback 分叉已成为当前唯一语义入口后，验证当前 `.i64` 会话为何再次不可复用，并把 blocker 再收紧成最小工程问题 | 动作: 主线程先对 `appleh11_completion` 做 `idb_list` 与 `idb_open(.i64)` 探针；随后检查对应 worker `pid=59491` 是否仍在、磁盘上 `.i64` 与 loose IDB (`.id0/.id1/.nam/.til`) 的时间戳；再尝试把 loose IDB 移走观察是否复生 | 证据: `idb_open(AppleH11ANEInterface.patched.macho.i64, preferred_session_id=appleh11_response2)` 失败；`ps`/`lsof` 确认 `pid=59491` 已不存在，但磁盘上 `.i64` 仍在，且伴随新鲜时间戳的 `.id0/.id1/.nam/.til`；尝试移动这些 loose IDB 后，它们立刻再次出现，说明 reopen 失败与 lingering / regenerated loose IDB 高度相关 | 结论: 本轮 verdict=`inconclusive`；当前最小 blocker 已从 ANE 语义边界临时回退为 `.i64` 会话重开时 loose IDB 再生导致的会话不稳定问题。下一轮必须先解决这一工程层问题，再继续沿 `handleOutstandingCommand` 的 Callback 分叉下钻 | 下一步: 只解决 `AppleH11ANEInterface.patched.macho.i64` 重开时 `.id0/.id1/.nam/.til` 再生导致的会话不稳定问题
2026-06-19 20:47:06 +0800 | 目标: 判断 `handleOutstandingCommand` 里 `_B618BF0()` 到底是不是 request completion callback continuation | 动作: 委派 `ida` 子代理只围绕 `0xfffffe00092d2274` 的 `_B618BF0` 调用点做窄分析；主线程不做重叠 IDA 工作，只收调用条件、参数来源、返回后控制流与目标地址边界 | 证据: 子代理确认唯一调用点在 `0xfffffe00092d243c`；调用前参数是 `X1=[X22+0x38]`、`W2=[X22+0x8]`，更像 `(buffer_addr, buffer_size)`；返回后立即落入 `DeviceMemoryManager::Free` 判定与共享 `commandWakeup` 尾部；目标 `0xFFFFFE000B618BF0` 超出 `AppleH11ANEInterface` 映射范围，是正常跨 kext `BL` 目标而非本 binary 内 trampoline/dispatcher | 结论: 本轮 verdict=`confirmed`；`_B618BF0` 不是当前可见的 callback continuation，更像 command-buffer free helper。下一轮不应继续把它当 callback 主线，而应到完整 decoded kernelcache 中确认 `0xFFFFFE000B618BF0` 的真实符号/签名，正式判定这条伪 callback 支线
2026-06-19 21:02:00 +0800 | 目标: 在完整 decoded kernelcache 中正式确认 `0xFFFFFE000B618BF0` 的真实身份，判定 `_B618BF0` 支线是否应从 completion 主线剥离 | 动作: 并行起 `reverse-engineer` 子代理与主线程最小本地复核；两边都只对 `/Volumes/2T/pymss/mps/ANE/.ane_runs/tmp/kernelcache.release.mac15s.payload.decoded.bin` 做 `nm -n` 精确地址命中，不扩散到无关语义 | 证据: 子代理与主线程都命中 `fffffe000b618bf0 S _memcpy` / `_memmove`，邻域还包含 `fffffe000b618be0 S _bcopy` / `_ovbcopy` 与 `fffffe000b618e50 S _memset`；目标位置也有非零代码字节，说明这不是空洞占位 | 结论: 本轮 verdict=`confirmed`；`_B618BF0` 已被正式判死为内核 `_memcpy` / `_memmove`，既不是 callback continuation，也不是 free helper。下一轮不应再沿这条伪 callback 支线扩散，而应回到 `handleOutstandingCommand` 里 `DeviceMemoryManager::Free` 判定、`lookupProgramResource` 与共享尾部对象消费路径，识别真正的 completion/writeback state consumer
2026-06-19 21:03:00 +0800 | 目标: 在 `handleOutstandingCommand` 共享尾部里识别真正承载 completion/writeback 语义的 state consumer | 动作: 并行起 `ida` 与 `reverse-engineer` 子代理；其中 shell 侧子代理不扩散新逆向，只交叉现有高密度工件和局部符号面，专门比较 `lookupProgramResource`、`commandWakeup`、`removeObject`、`DeviceMemoryManager::Free` 四个候选 | 证据: 交叉工件确认共享尾部顺序为 `status writeback -> lookupProgramResource(inner+0x68,&process,0) -> process+0x20400 counter-- -> commandWakeup -> callback invoke -> removeObject -> timer cleanup -> DeviceMemoryManager::Free`；其中只有 `lookupProgramResource` 会把命令完成事件桥接到 `ANEProcess*`，并立即驱动 `process+0x20400` 上的 `ldr -> subs -> str` 持久状态更新；其余候选均只承担通知或清理 | 结论: 本轮 verdict=`confirmed`；`lookupProgramResource` 已成为 `handleOutstandingCommand` shared-tail true state consumer。下一轮不应再问谁是 shared-tail consumer，而应只追 `inner+0x68` 的 key 语义，以及 `lookupProgramResource` 之后谁负责 `process+0x203fc/0x20400` 的 durable acceptance writeback
2026-06-19 21:03:00 +0800 | 目标: 把 `inner+0x68` 的 key 语义与 `process+0x203fc/0x20400` 的 durable writeback 缺口再收紧一层 | 动作: 并行起 `doc-reader` 与 `ida` 子代理；`doc-reader` 只压缩 `completion_process_counter_note.md`、`legacy_typed_completion_route_note.md`、`command_state_materialization_note.md`、`process_state_window_note.md`、`bootkc_resource_gate_process_registry_probe.md` 五份直接相关工件；主线程再复用 `newinstance_hidden_handle_stage_verdict_20260619.json` 的既有 join 结论做交叉，不等待未返回的 IDA 结果 | 证据: 文档侧确认 `inner+0x68` 是传给 `lookupProgramResource(inner+0x68, &process, 0)` 的查找键，并通过 `resource+0x400d0` 这张 `OSArray<ANEProcess*>` 注册表解析为 `ANEProcess*`；既有 hidden-handle 结论又已确认 accepted-state join 为 `x5 -> additional_params+0x18 -> local_y -> lookupProgramResource -> params[0]/x21[0]`；同时 `process+0x203fc` 的 visible writer family 已基本封口为 `0` 与 `1`，但 `== 2` 的 decisive writer 仍不可见 | 结论: 本轮 verdict=`confirmed`；`inner+0x68` 已足够收紧为 hidden numeric lookup key family，当前真正未解的 lower control gap 已进一步收敛为 `process+0x203fc == 2` 的 decisive author。下一轮不应再泛问 key 语义，而应只追这个 state-2 writer 所在的更低 replay/restore 或 family-6/process-state 路径
2026-06-19 21:03:00 +0800 | 目标: 把 `process+0x203fc == 2` 的 decisive writer 从泛化缺口收紧成最小层级分叉 | 动作: 并行起 `ida` 与 `reverse-engineer` 子代理；主线程只复核已精确定位到的 `process_state_and_record_author_tightening_note.md` 与 `send_reply_shell_negative_note.md` 相关片段，不重跑大范围搜索 | 证据: 当前 visible exact writers 只覆盖 `0`（`ANEProcess::init` / `ANE_ProcessCreate_gated`）与 `1`（`ANE_SaveState` / `ANE_RestoreStateEv.cold.2` / demote family）；对 `aneCmdSend`、`aneFirmwareCommandSend`、`handleOutstandingCommand`、`ANE_RestoreState`、`ProgramLoad(load_type==2)` 的既有 exact-operand 检查都未命中 `0x203fc` 写入；同时 `record+0x1b8` 也缺少 visible CPU-side durable writer；当前 remaining visible gap 只剩 selectors 5/6：`ANE_ProgramUnprepare` 与 `ANE_ProgramDestroy` | 结论: 本轮 verdict=`confirmed`；`process+0x203fc == 2` 的 decisive writer 已被收紧成一个两层分叉：要么藏在 selectors 5/6 的最后可见 gap，要么必须下沉到 replay/restore / firmware readback lower path。下一轮只应显式排除 selectors 5/6 对 `0x203fc` 的写入
2026-06-19 21:29:57 +0800 | 目标: 显式排除 selectors 5/6（`ANE_ProgramUnprepare` / `ANE_ProgramDestroy`）对 `process+0x203fc` 的 exact 写入 | 动作: 主线程直接重开 `AppleH11ANEInterface.patched.macho.i64` 为 `appleh11_sel56_probe`；先用 `search_text` 确认 `ProgramUnprepare` / `ProgramDestroy` 家族在当前 IDB 中存在，再对整张 image 做 `op_any == 0x3fc` 窄扫描，并对命中函数集合做 family 对比 | 证据: 当前 `+0x3fc` hit set 只包含 `ANEProcess::init`、`ANEProgramRTResource::programRTSendInferenceRequest`、`ANEHWDevice::isProcessValid`、`ANEHWDevice::ANE_ProcessCreate_gated`、`ANEHWDevice::ANE_ProgramCreateInstance_gated`、`ANEHWDevice::ANE_ProgramPrepareAndSubmitRequest_gated`；其中没有 `ProgramUnprepare` / `ProgramDestroy` 家族函数；随后 IDA MCP transport 再次关闭，但 negative set 已拿到 | 结论: 本轮 verdict=`confirmed`；selectors 5/6 已足够从当前 visible `process+0x203fc` exact-writer set 中排除。下一轮应正式把 `state==2` author 下沉到 replay/restore / firmware-readback lower layer，停止把 visible CPU-side family 当主战场
2026-06-19 21:37:22 +0800 | 目标: 在 replay/restore / firmware-readback family 中收敛第一个可能 materialize `process+0x203fc == 2` 的 lower surface | 动作: 并行起 `doc-reader` 与 `reverse-engineer` 子代理压缩 `restore_record_raw_send_boundary_note.md`、`process_state_and_record_author_tightening_note.md`、`send_reply_shell_negative_note.md`、`selector4_status2_intermediate_note.md` 等直接相关材料；主线程只复核现有静态 boundary probe `ane_bootkc_restore_record_raw_send_boundary_probe.py`，不新开大范围 IDA | 证据: `record+0x1b8` 被 `ProgramLoad`、`ANE_RestoreState`、Legacy `programLoadFromMachoFile`、`ProgramReMap` 四条路径读取，但零个 visible CPU-side exact store；`ANE_RestoreState` 中 raw send 返回后到 `record+0x1b8` 读取前只有 5 条指令且 `stores=0 calls=0`；`gate+0x220` 只是 `record+0x1b8` 的下游镜像消费点 | 结论: 本轮 verdict=`confirmed`；`record+0x1b8` 已成为当前最强的 first lower surface，其 durable author 位于 raw firmware send 以下。下一轮只应在 restore raw-send 边界对同一 `record+0x1b8` 做 pre/post-send 取值，验证它是否直接 materialize 与 `process+0x203fc` 同构的 state family
2026-06-19 21:37:22 +0800 | 目标: 判断现有 runtime/userland harness 是否足以直接观测 `record+0x1b8` 的 pre/post-send 值 | 动作: 主线程核查 `ane_ioconnect_trace_interpose.c`、`ane_services_program_create_runtime_probe.m`、`pymss/utils.py::_private_ane_trace_event` 三个现有 runtime 入口，并与 `ane_bootkc_restore_record_raw_send_boundary_probe.py` 的静态边界结论对照；不新增代码，只确认观测面边界 | 证据: IOKit interposer 当前只总结/转储 selector 3/8 的 userland request/output buffer；`PYMSS_PRIVATE_ANE_TRACE_PATH` 只记录高层 batch/cache/stft/mask/istft 事件；而 `ANE_RestoreState` 的静态边界已确认 `record+0x1b8` 位于 raw firmware send 以下，不在返回后的 visible H16 CPU 代码里 | 结论: 本轮 verdict=`confirmed`；现有 runtime harness 太高，不能直接观测 `record+0x1b8` pre/post-send 值。下一轮应先设计/实现一个更低的 runtime probe 面，而不是继续扩展高层 trace
2026-06-19 21:37:22 +0800 | 目标: 在“现有 runtime harness 太高”之后，再收紧一个可实施的更低 probe 面选择 | 动作: 主线程对比 `ane_ioconnect_trace_interpose.c`、`ane_services_program_create_runtime_probe.m`、`pymss/utils.py` 高层 trace，以及 `ane_bootkc_post_send_replay_boundary_probe.py` 的 post-send 层级结论；不改代码，只判断哪一层最值得扩 | 证据: `PYMSS_PRIVATE_ANE_TRACE_PATH` 只记录 batch/cache 生命周期；`ane_ioconnect_trace_interpose.c` / `ane_services_program_create_runtime_probe.m` 是当前最低可复用 runtime 入口，但仍只观察 selector request/output buffer；post-send boundary 结果又显示 unload-side `device+0x9c0 / 0x927d410` family 比 restore-side replay 更深、更接近 hidden writer | 结论: 本轮 verdict=`confirmed`；当前最低可复用 runtime 入口已收紧为 IOKit interposer family，但下一步必须在其上增加 lower-side dump path，优先瞄准 unload-side `device+0x9c0 / 0x927d410` post-send family
2026-06-19 22:03:00 +0800 | 目标: 把“更低 runtime probe 面”从设计推进到可执行实现 | 动作: 新增 `mps/ANE/experiments/ane_mach_msg_runtime_probe.c`，用 `__DATA,__interpose` 拦截 `mach_msg` / `mach_msg_overwrite`；同时更新 `mps/ANE/experiments/Makefile` 增加 `ane_mach_msg_runtime_probe.dylib` 目标；随后本地执行 `make -C mps/ANE/experiments ane_mach_msg_runtime_probe.dylib` 并用 `file` / `otool -hv` 验证产物 | 证据: 新 probe 输出 `option/send_size/rcv_size/ret/msgid/request_hash/reply_hash/nonzero/head-bytes summary` 等字段，并支持 remote-port/msgid/head-bytes 过滤；本机已生成 `/Volumes/2T/pymss/mps/ANE/experiments/ane_mach_msg_runtime_probe.dylib`，`file` 确认为 `Mach-O 64-bit dynamically linked shared library arm64`，`otool -hv` 显示 `MH_MAGIC_64 ARM64 DYLIB` | 结论: 本轮 verdict=`confirmed`；更低 runtime probe 面已从“建议”变成可执行产物。下一轮不应再停在设计层，而应把 `ane_mach_msg_runtime_probe.dylib` 挂到一个真实 ANE 调用路径上，确认是否能看到更深 post-send reply surface
2026-06-19 22:11:00 +0800 | 目标: 首次把 `ane_mach_msg_runtime_probe.dylib` 挂到真实 ANE 目标路径上，验证 lower probe 面是否可挂载 | 动作: 选用一份同时具备 `model.hwx`/`data` 的 `benchmark_results/private_ane/ane_tmp_loadcache/...` 目录，执行 `ane_services_program_create_runtime_probe --fast-trace`，并注入 `DYLD_INSERT_LIBRARIES=/Volumes/2T/pymss/mps/ANE/experiments/ane_mach_msg_runtime_probe.dylib`，输出到 `mps/ANE/.ane_runs/csv/mach_msg_selector3_fasttrace_20260619.csv` | 证据: 目标进程在 interposer 注入下未崩溃，正常输出 JSON；`mach_msg_selector3_fasttrace_20260619.csv` 成功创建，但仅有表头、无消息行；运行 JSON 明确显示失败发生在 `device_open_failed / missing_default_artifact`，说明这条 target path 过早退出，没真正跨过 ANE 设备消息流量 | 结论: 本轮 verdict=`confirmed`；`mach_msg` probe 面已经证明可挂载，但当前选的 fast-trace target path 不足以产生实际消息。下一轮只需换一个已知能成功穿过 device open/create 流量的 target path，让 CSV 里出现至少一条真实 Mach row
2026-06-19 22:16:00 +0800 | 目标: 在已知成功的 v17 target path 仍让 `mach_msg` interposer 零命中后，收紧下一层 runtime 边界 | 动作: 主线程把本轮 `mach_msg` v17 零命中结果与旧的 `selector3_import_stub_public_iokit_noop_interpose_note.md` 结论重新对齐，不新增代码，只做边界决策收敛 | 证据: 新事实是 v17 target path 仍只有 header-only mach_msg trace；旧事实是 `rawCreateFn+0x108` 已明确命中 public `IOConnectCallStructMethod` arm64e import stub，且 `dyld_dynamic_interpose` 没改动这条 authenticated slot | 结论: 本轮 verdict=`confirmed`；当前最高价值的 runtime probe 边界不是继续猜 `mach_msg2`/更宽消息原语，而是回到已证实的 arm64e IOConnect auth-slot 面，直接做 patch/observe 验证
2026-06-19 22:16:00 +0800 | 目标: 在决定回到 arm64e IOConnect auth-slot 之后，确认这条路径是否已经有 machine-local 的 live selector-3 成功样本 | 动作: 主线程直接复核历史成功产物 `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_manual_v9_arm64e_patch.json` / `...v10_arm64e_patch_ready1.json` 及对应 CSV，不新增代码、不复跑 | 证据: `runtime_manual_v7` 只有表头；但 `trace_selector3_runtime_manual_v9_arm64e_patch.csv` 有 8 行、`trace_selector3_runtime_manual_v10_arm64e_patch_ready1.csv` 有 9 行；对应 JSON 也明确记录了 auth-slot patch 后的真实 slot 值 | 结论: 本轮 verdict=`confirmed`；arm64e auth-slot patch/observe 已经是当前 machine-local 唯一已知能命中 live selector-3 交通的 runtime boundary。下一轮不应再证明这条边界值不值得做，而应直接复用/重建它并把 captured 交通接回当前 lower-control 主线
2026-06-19 22:41:20 +0800 | 目标: 复用历史成功的 slot-patch selector-3 runtime path，验证当前 machine-local 是否还能直接复现 live rows | 动作: 不改代码，直接用历史成功参数 `--fast-trace --manual-transport --slot-patch-structmethod --only-case live_mil_nonprecompiled_path_live_modelurl_mil --live-artifact ...add_all_fresh_rebuilt_VHE1I1 <artifact_root>` 分别重跑 `./mps/ANE/experiments/ane_services_program_create_runtime_probe` 与 `./mps/ANE/experiments/ane_services_program_create_runtime_probe_arm64e`；输出到 `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_manual_replay_20260619.json`、`...replay_arm64e_20260619.json` 及对应 CSV | 证据: 两次 replay 的 live compile/load 都成功，slot patch 也都 `write_match=1`；default replay 显示 `ptrauth_intrinsics=false`，arm64e replay 恢复 `ptrauth_intrinsics=true`；但两份 CSV `trace_selector3_runtime_manual_replay_20260619.csv` / `...replay_arm64e_20260619.csv` 都仍然只有表头 1 行，无任何 live selector-3 row；见 `mps/ANE/.ane_runs/json/auth_slot_patch_replay_zero_hit_verdict_20260619.json` | 结论: 本轮 verdict=`falsified`；当前阻塞已不再是参数误用、非 arm64e 二进制或 slot patch 写入失败。即便恢复 arm64e+ptrauth slot patch，patched import slot 仍未在当前 runtime 中被实际命中 | 下一步: 只比较历史成功 v9/v10 与当前 replay 在 `image_base/raw_create_fn/raw_create_callsite_0x108/target_stub_decode/slot_signature_candidates/slot_patch before/after` 上的最小差异，定位第一处 runtime 漂移面
2026-06-19 22:49:38 +0800 | 目标: 在 `v9/v10/replay_arm64e` 差异中找出第一处真正解释 zero-hit 的 runtime 漂移面 | 动作: 先把 `v9`、`v10`、`replay_arm64e_20260619` 的 `raw_create_callsite_0x108`、`target_stub_decode`、`slot_signature_candidates`、`runtime_trace_manual_slot_patch`、case 级 `manual_selector3_transport`/`service_ready_u8_0x18` 等字段压成同构 diff；随后发现 replay 与历史成功的第一处决定性差异是 `rawcreate_force_ready1=false`，再在其余参数完全不变时补跑 `./mps/ANE/experiments/ane_services_program_create_runtime_probe_arm64e --fast-trace --manual-transport --slot-patch-structmethod --rawcreate-force-ready1 --only-case live_mil_nonprecompiled_path_live_modelurl_mil --live-artifact ...add_all_fresh_rebuilt_VHE1I1 <artifact_root>` | 证据: baseline replay 仍是 `raw_create_status_hex=0x00000000` 且 CSV 只有表头；forced-ready replay 新产物 `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_manual_replay_arm64e_force_ready1_20260619.json` 与 `mps/ANE/.ane_runs/csv/trace_selector3_runtime_manual_replay_arm64e_force_ready1_20260619.csv` 立即出现 `selector=3, ret=0xe00002c2` 的 live row，同时 JSON 明确记录 `raw_create_force_ready1_before=0`, `after=1`, `restored=0`；见 `mps/ANE/.ane_runs/json/auth_slot_ready_gate_replay_verdict_20260619.json` | 结论: 本轮 verdict=`confirmed`；当前 replay 的首个决定性漂移面不是 slot patch，而是 rawCreate ready-gate 没被打开。之前看似“patched slot 未命中”其实是 rawCreate 在 ready-gate 关闭时直接 short-circuit，根本不发送 selector-3 | 下一步: 只追当前 higher-level state machine 中，什么 accepted-state / pre-stage 会自然把 `service+0x18` 置为 `1`，从而不依赖 probe 强制 ready-gate 也能放行 selector-3
2026-06-19 23:02:10 +0800 | 目标: 把 `service+0x18` 的自然 author 从“某个 higher-level pre-stage”继续收紧到最小可行动的 open-family 分叉 | 动作: 不新开大 IDA 面，直接复核 `open_reply_ready_byte_alignment_note.md`、`selector3_ready_gate_transport_match_note.md`、`ane_services_static_probe.py` 及现有成功/失败 open 样本；并行用 `doc-reader`/`searcher` 子代理只压缩 `reply[0x1c] -> service+0x18`、`ANEClientInfo::create(task, j, b1, b2)`、`H11ANEInDirectPathClient`/`H11ANEInUserClient` 现有证据，不重复做大段反编译 | 证据: 当前链条已闭合为 `ANEClientInfo+0x10 -> ANEClientDevice+0x28 -> selector-0 reply+0x1c -> service+0x18`；成功 local path 固定是 `usageType=1 -> H11ANEInDirectPathClient::init -> ANEClientInfo::create(task, 1, 0, 1)`，因此 `b1=0` 导致 ready byte 设计上就是 0；regular/non-direct 路径则是 `H11ANEInUserClient::init -> ANEClientInfo::create(task, 2, 1, 1)`，但受 `com.apple.ane.iokit-user-access` entitlement gate 约束，当前 `mode/usageType=3` 样本都在 open 前返回 `0x00000018`；见 `mps/ANE/.ane_runs/json/ready_gate_natural_author_verdict_20260619.json` | 结论: 本轮 verdict=`confirmed`；当前 natural ready-gate author 已不再是模糊的“某个 pre-stage”，而是 higher-level user-client split 本身。当前 ready byte 为 0 不是 lost write，而是 direct-path 的设计结果 | 下一步: 只验证当前 machine-local 是否存在任何不依赖新签名 entitlement 的本地可达 non-direct-path / private route；若没有，就把 blocker 正式收敛为 entitlement-gated higher-level open family
2026-06-19 23:13:20 +0800 | 目标: 验证当前 machine-local 是否还存在任何不依赖新签名 entitlement 的本地可达 non-direct-path / private route | 动作: 主线程先以 runtime 结果为准，复核 `ane_services_program_create_open_sweep_v9_usage3.json`、`ane_services_program_create_open_sweep_v10_outermode3.json`、`ane_services_program_create_runtime_probe_v23_fresh_controller_case.json` 和 `bootkc_userclient_probe.md`/`virtualclient_route_split_note.md` 的静态路由说明；并行让 `searcher`/`doc-reader`/`reverse-engineer` 子代理只压缩 regular/hinted/private route 线索，不新开大规模 IDA | 证据: 当前 runtime 上 `usageType=3` 与 `mode=3` 尝试都只返回 `0x18`，没有 device handle；`fresh_controller` / `programhandleopen` 变体也只重放同一 partial family，没有 materialize 新 regular route；静态上 regular/hinted family 确实存在，但当前 probe 二进制无可见 embedded entitlement XML，而 natural ready-gate author 所在 regular path 仍受 `com.apple.ane.iokit-user-access` gate 约束；见 `mps/ANE/.ane_runs/json/non_direct_route_reachability_verdict_20260619.json` | 结论: 本轮 verdict=`confirmed`；当前 machine-local 尚未发现不依赖新签名 entitlement 的本地可达 non-direct/private open route。当前 blocker 已可正式收敛为 entitlement-gated higher-level open family | 下一步: 只验证一个最低风险的新候选：直接调用 `_ANEServicesLocateAndOpenHintedDevice`，看 hinted/private route 是否能在当前 machine-local 上拿到非零 device handle；若仍失败，就可把当前层正式判死并转向更低 control layer 或外部授权条件
2026-06-19 23:17:40 +0800 | 目标: 直接调用 `_ANEServicesLocateAndOpenHintedDevice`，验证 hinted/private route 是否真能在当前 machine-local 上拿到非零 device handle | 动作: 主线程先用解包 ANEServices 镜像静态缩小 `_ANEServicesDeviceOpen -> _ANEServicesLocateAndOpenHintedDevice` 的调用点寄存器准备，再新增最小实验 `mps/ANE/experiments/ane_services_hinted_open_probe.m` 与 `Makefile` 目标，只用现有 `ANEServicesDeviceOpen` 的 0x20 config 布局做一次最小直调；构建并运行 `ane_services_hinted_open_probe`，输出到 `benchmark_results/private_ane/ane_services_hinted_open_probe_20260619.json` | 证据: `_ANEServicesLocateAndOpenHintedDevice` 真实导出偏移 `0x00020320`，且 `_ANEServicesDeviceOpen` 内部确实会调它；但最小 probe 在当前 machine-local 上直接以 exit `139` 退出，输出 JSON 文件大小为 `0`；见 `mps/ANE/.ane_runs/json/hinted_open_probe_crash_verdict_20260619.json` | 结论: 本轮 verdict=`confirmed`；hinted route 不能再被视为“最低风险直接可调用”的 private route。当前失败不是 `status/device` 级否定，而是 ABI / 参数布局尚未恢复到可安全调用的程度 | 下一步: 只恢复 `_ANEServicesLocateAndOpenHintedDevice` 的最小 ABI（x1 hint-state、x4/x5 hint array、x6 count、x7 selected-index）；若无法在小成本内恢复，就把 hinted route 从“最低风险候选”正式降级
2026-06-19 23:23:20 +0800 | 目标: 验证 `_ANEServicesLocateAndOpenHintedDevice` 是否只差一层最小 ABI 修正即可进入可观测结果 | 动作: 主线程继续只做最小 ABI 收紧：从 `_ANEServicesDeviceOpen` 调用点确认 `x6` 来自设备数量、`x7` 指向 `openConfig+0x14` 派生的 selected-index/deviceHint 槽、`x4/x5` 是 DeviceOpen 原始后两参镜像；随后仅修改 `ane_services_hinted_open_probe.m` 以对齐这些寄存器，再次编译运行，输出到 `benchmark_results/private_ane/ane_services_hinted_open_probe_20260619_v2.json` | 证据: `v2` probe 仍然以 exit `139` 退出，输出文件仍为 `0` 字节，和 `v1` 完全同态；见 `mps/ANE/.ane_runs/json/hinted_open_probe_v2_crash_verdict_20260619.json` | 结论: 本轮 verdict=`confirmed`；当前 hinted route 的问题不能再归因于 `x4/x5/x6/x7` 这一层简单 ABI 猜错。它还依赖更深的 hint array / controller state / receiver state 语义，短期内不再是低成本突破口 | 下一步: 只决定当前主线是否正式把 hinted route 判死并回到更低 control layer，或转成需要外部授权 / entitlement 条件的分支工作
2026-06-19 23:29:40 +0800 | 目标: 验证“外部授权条件”这条分支在本机是否现实可行：仅靠 ad-hoc 重签并嵌入已知 ANE entitlements，能否让 hinted-open probe 进入可观测结果 | 动作: 主线程直接复用现有 `mps/ANE/experiments/ane_probe_test.entitlements.plist`，对 `ane_services_hinted_open_probe` 副本执行 `codesign -s - --force --entitlements ...`，确认 `codesign -d --entitlements :-` 已显示 `com.apple.ane.iokit-user-access` 与 `com.apple.ane.allow-dataChaining-access`，然后运行该已签名副本，输出到 `benchmark_results/private_ane/ane_services_hinted_open_probe_signed_20260619.json` | 证据: ad-hoc 重签与 entitlement 嵌入在本机上都成功，但已签名 hinted-open probe 仍未进入正常 status/device 路径：exit `137`，输出文件仍为 `0` 字节；见 `mps/ANE/.ane_runs/json/hinted_open_signed_probe_verdict_20260619.json` | 结论: 本轮 verdict=`confirmed`；对当前 hinted route 而言，“外部授权条件”至少不是一个立即可用的低成本解。当前主线应把 hinted route 与 entitlement 直签分支一起降级 | 下一步: 正式回到底层 control layer 主线，重新选择一个最小下钻入口，不再继续 open-family / hinted-route 分支
2026-06-19 23:37:10 +0800 | 目标: 在正式降级 open-family / hinted-route 分支后，为 lower control layer 主线重新选择唯一默认下钻入口 | 动作: 主线程不再新增 probe，只对齐三份现有 lower-layer verdict：`process203fc_state2_first_lower_surface_record1b8_verdict_20260619.json`、`runtime_harness_record1b8_observability_boundary_verdict_20260619.json`、`process203fc_state2_writer_layer_split_verdict_20260619.json`；目标是判断回到 `record+0x1b8` 还是继续围绕 `process+0x203fc==2` 做结果面排除 | 证据: 现有证据已明确 `process+0x203fc==2` 更像 downstream state contract / symptom surface，自身 visible writer 基本排空；`record+0x1b8` 才是当前最上游的 first lower surface，且 durable author 已被压到 raw firmware send 以下；当前 runtime harness 无法直接观测它，说明下一步应降低 observability surface | 结论: 本轮 verdict=`confirmed`；lower-layer 主线的唯一默认下钻入口应正式回到 `record+0x1b8`，不再把 `process+0x203fc==2` 当默认 re-entry point | 下一步: 只围绕 `record+0x1b8` 重新设计一个更低 observability surface，使主线重新接回 raw firmware send 以下的 first lower surface
2026-06-19 23:47:20 +0800 | 目标: 围绕 `record+0x1b8` 把现有最低 runtime probe 面提升成一个更有用的 lower-side dump path | 动作: 主线程直接修改 `mps/ANE/experiments/ane_mach_msg_runtime_probe.c`，不改 hook 逻辑，只增强 observability：新增 `CODEX_ANE_MACH_MSG_TRACE_BODY_BYTES`、把 header 后的 body 前缀加入 summary，并在 CSV 中增加 send/reply 的 `remote/local/voucher/msgh_size` 字段；随后执行 `make -C mps/ANE/experiments ane_mach_msg_runtime_probe.dylib` 确认编译通过 | 证据: `ane_mach_msg_runtime_probe.dylib` 重新编译成功；新 verdict `mps/ANE/.ane_runs/json/mach_msg_probe_v2_entry_upgrade_verdict_20260619.json` 已记录这次 lower-side dump path v2 升级 | 结论: 本轮 verdict=`confirmed`；probe 入口选择问题已结束。当前最低层可复用 runtime 入口已升级成一个更高信息密度的 lower-side dump path v2 | 下一步: 只选择一个最贴近 `ANE_RestoreState raw-send / record+0x1b8` 边界的 target path，把 mach_msg runtime probe v2 挂上去，检查它是否能比旧版 probe 捕获更多 reply/body 差异
2026-06-19 23:56:10 +0800 | 目标: 在 mach_msg runtime probe v2 已准备好后，正式选定唯一默认 runtime target path | 动作: 主线程只对齐 `restore_record_raw_send_boundary_note.md` 与 `post_send_replay_boundary_note.md` 的边界结论，不新增 probe；目标是判断 mach_msg runtime probe v2 下一轮该挂到 restore-side 5 指令短区间，还是 unload-side `device+0x9c0 / 0x927d410` family | 证据: restore-side 仍是最贴近 `record+0x1b8` 的静态对照边界，但其 send 返回后只有 5 条可见指令，增量收益已经很低；unload-side 在 send 返回后立即发散到更深的 `device+0x9c0 / 0x927d410` family，更可能暴露 deeper reply/replay state；见 `mps/ANE/.ane_runs/json/lower_runtime_target_path_selection_verdict_20260619.json` | 结论: 本轮 verdict=`confirmed`；mach_msg runtime probe v2 的唯一默认挂载对象应改为 unload-side post-send device family，restore-side 只保留为 `record+0x1b8` 的静态对照边界 | 下一步: 只找一个最容易驱动 unload-side `device+0x9c0 / 0x927d410` family 的 runnable harness/command，把 mach_msg runtime probe v2 挂上去做最小实测
2026-06-20 00:05:10 +0800 | 目标: 为 mach_msg runtime probe v2 选第一个最小 runnable target path，并验证它是否是合适的 unload-side runtime harness | 动作: 主线程按最小可运行原则，把 probe v2 先挂到 `benchmark.private_ane_stft_only_benchmark` 的 `1s / 1chunk / no-preload / no-load-cache` 命令上，输出到 `mps/ANE/.ane_runs/csv/mach_msg_stft_only_unload_v2_20260619.csv` 和 `benchmark_results/private_ane/stft_only_unload_probe_20260619.json`；在合理观察窗口内只检查 CSV/JSON 是否快速进入可观测结果 | 证据: 注入后的进程未立即崩溃，说明 probe v2 至少与该 harness 共存；但在观察窗口内 CSV 仍只有表头、benchmark JSON 也未落成终态结果；见 `mps/ANE/.ane_runs/json/mach_msg_probe_v2_stft_only_target_verdict_20260619.json` | 结论: 本轮 verdict=`confirmed`；`stft_only_benchmark` 虽可运行，但不是当前最有效的 unload-side runtime target，它仍把主要时间预算消耗在更早的 compile/load 阶段 | 下一步: 只把 mach_msg runtime probe v2 挂到更直接触发 `ANEBridge.free()` / `ProgramUnload` 的 runnable harness，优先 `benchmark.private_ane_bridge_chain_probe.py`
2026-06-20 00:16:40 +0800 | 目标: 验证 `benchmark.private_ane_bridge_chain_probe.py` 是否比 `stft_only` 更适合充当 unload-side runtime target | 动作: 主线程把 `mach_msg runtime probe v2` 直接挂到 `python -m benchmark.private_ane_bridge_chain_probe --out benchmark_results/private_ane/bridge_chain_unload_probe_20260620.json` 上，输出到 `mps/ANE/.ane_runs/csv/mach_msg_bridge_chain_v2_20260620.csv`；只检查短窗口内是否快速出现非表头消息行或完成结果 JSON | 证据: 注入后的 bridge-chain 进程未立即崩溃；但在短观察窗内 CSV 仍只有表头，输出 JSON 也未落成终态文件；见 `mps/ANE/.ane_runs/json/mach_msg_probe_v2_bridge_chain_target_verdict_20260620.json` | 结论: 本轮 verdict=`confirmed`；bridge-chain 虽然语义上更接近 `ANEBridge.free()` / `ProgramUnload`，但在当前短窗口内依旧没有给出更强的 mach_msg signal，说明当前瓶颈已经转成 runtime harness 本身在进入 unload-side family 之前仍然过重 | 下一步: 只继续缩小 runnable harness，找一个比 `bridge_chain_probe` 更短、更专门触发 free/unload 的现成入口，或把现有 harness 输入进一步压小到能在短窗口内稳定触发 `ANEBridge.free()`
2026-06-20 00:24:50 +0800 | 目标: 验证 single compile/eval/free 的 full-block harness 是否终于足够短，能在短观察窗内给 mach_msg probe v2 喂出有效 unload-side 流量 | 动作: 主线程把 `mach_msg runtime probe v2` 直接挂到 `python -m benchmark.private_ane_full_block_probe --out benchmark_results/private_ane/full_block_unload_probe_20260620.json --fail-ok` 上，输出到 `mps/ANE/.ane_runs/csv/mach_msg_full_block_v2_20260620.csv`；只检查短窗口内 CSV 是否出现非表头消息行、JSON 是否完成 | 证据: 注入后的进程未立即崩溃；但在短观察窗内 CSV 仍只有表头，输出 JSON 也未落成终态文件；见 `mps/ANE/.ane_runs/json/mach_msg_probe_v2_full_block_target_verdict_20260620.json` | 结论: 本轮 verdict=`confirmed`；即使是 single compile/eval/free 的 full-block harness，也不足以在短窗口内喂出有效 mach_msg 行。当前问题已不再是“再换一个稍短的现成 harness”就能解决 | 下一步: 只决定两件事之一：要么找到一个真正更接近 `ane_bridge_free()` 的极小 harness；要么正式承认当前 runtime harness 家族不足以在短窗口内给 mach_msg probe v2 喂出有效 unload-side 流量
2026-06-20 00:35:20 +0800 | 目标: 结束“继续换第四个现成 benchmark harness”这条路，并决定是否正式转向新的 lower-side 观测策略 | 动作: 主线程复核 `benchmark/` 中剩余几类近邻脚本（`private_ane_ffn_authored_sharedblob_compare.py` / `private_ane_sharedblob_convchain_compare.py` / `private_ane_real_ffn_mode_compare.py`）的 compile/eval/free 结构，并与已实测的 `stft_only` / `bridge_chain` / `full_block` 对比，不再新增第四次注入实测 | 证据: 三条已实测 harness 在短窗口内都只产生 header-only CSV；剩余近邻脚本本质上仍是多 mode compare harness，并不比 `full_block` 更小、更直接；见 `mps/ANE/.ane_runs/json/runtime_harness_family_short_window_limit_verdict_20260620.json` | 结论: 本轮 verdict=`confirmed`；当前 runtime harness 家族已在短窗口 lower-side 观测问题上整体判定为过重，不应再继续拿现有 benchmark harness 喂 mach_msg probe v2 | 下一步: 设计一个 dedicated free/unload micro-harness，直接触发 `ANEBridge.free()` / `ProgramUnload`，作为下一轮唯一入口
2026-06-20 00:46:20 +0800 | 目标: 正式结束“继续在现有 benchmark harness 家族里找更小入口”这条路，并把主线切到 dedicated micro-harness 方向 | 动作: 主线程继续筛查 `private_ane_ffn_authored_sharedblob_compare.py` / `private_ane_sharedblob_convchain_compare.py` / `private_ane_real_ffn_mode_compare.py` / `private_ane_batch_acceptance_probe.py` 的 compile/eval/free 结构，确认它们仍是多 mode / 多 stage / acceptance 型 benchmark harness，而不是更小的 free/unload 微入口；不再新增第四次运行时注入 | 证据: 当前已实测的 `stft_only` / `bridge_chain` / `full_block` 已足够代表现有 benchmark harness 家族；新筛查的近邻脚本没有一个在 practical short-window 意义上更接近 `ane_bridge_free()`；见 `mps/ANE/.ane_runs/json/dedicated_micro_harness_direction_verdict_20260620.json` | 结论: 本轮 verdict=`confirmed`；主线下一步应正式转向 dedicated free/unload micro-harness 设计，不再继续轮换现有 benchmark harness 家族 | 下一步: 实现一个 dedicated free/unload micro-harness：单 compile/load，最少或零 readback，立即 free，专门为 mach_msg runtime probe v2 提供短窗口 unload-side 流量
2026-06-20 00:57:20 +0800 | 目标: 验证 dedicated free/unload micro-harness 是否终于足以在短窗口内给 mach_msg runtime probe v2 喂出有效 unload-side 流量 | 动作: 主线程新增 `benchmark/private_ane_free_unload_micro_probe.py`，只做单 compile/load、零或最少 readback、立即 `bridge.free(handle)`；随后把 `mach_msg runtime probe v2` 挂到 `python -m benchmark.private_ane_free_unload_micro_probe --mode compile_only --out benchmark_results/private_ane/free_unload_micro_probe_20260620.json` 上，输出到 `mps/ANE/.ane_runs/csv/mach_msg_free_unload_micro_v2_20260620.csv` | 证据: dedicated micro-harness 注入后未立即崩溃；但在短观察窗内 CSV 仍只有表头，输出 JSON 也未完成；见 `mps/ANE/.ane_runs/json/free_unload_micro_probe_mach_msg_limit_verdict_20260620.json` | 结论: 本轮 verdict=`confirmed`；当前问题已不再能归因于 harness 家族太重。即使 dedicated free/unload micro-harness 也无法在短窗口内让 mach_msg probe v2 看到有效流量，因此下一步主线必须改换 lower-side 观测策略，而不是继续优化 mach_msg runtime target | 下一步: 决定新的 lower-side 观测策略方向，优先回到 IOKit interposer family 或桥层更直接的 instrumentation
2026-06-20 03:45:37 +0800 | 目标: 完成 `layer3 time` retained stack 的最小 control matrix，判断 failure 是 `pre+gate` 子集边界还是 introspection/timing-sensitive | 动作: 先关闭四个已完成旧 sub-agent 释放线程配额；读取 `diagnosing-bugs` skill 约束后，不改代码，直接运行 `ANE_BRIDGE_FREE_TRACE=1 ANE_BRIDGE_FREE_TRACE_FILE=mps/ANE/.ane_runs/logs/ane_bridge_free_trace_time3_pregate_state_20260620.jsonl python benchmark/private_ane_multifamily_free_profile_probe.py --audio test_clean.m4a --seconds 1.0 --repeats 2 --keep-transformer --max-transformer-layers 4 --stop-after-transformer --stop-after-transformer-layer 3 --stop-after-transformer-axis time --transformer-handle-scope pre_gate --out benchmark_results/private_ane/multifamily_keep_layers4_time3_pregate_state_20260620.json`；随后把 `pre_no_snapshot` / `pre_state` / `pregate_state` 三个结果并排比对，并新增 `mps/ANE/.ane_runs/json/pre_gate_handle_state_probe_verdict_20260620.json` | 证据: `multifamily_keep_layers4_time3_pre_20260620.json` 中 `run1_ok=false`；但 `multifamily_keep_layers4_time3_pre_state_20260620.json` 与新产物 `multifamily_keep_layers4_time3_pregate_state_20260620.json` 都是 `run1_ok=true`，且 `cache_before/cache_after` 都为 15 条 retained transformer handles；代表性 handle 在 `pregate_state` 路径上保持 `model_state=3`、`queue_depth=127`，对应 free trace 落在 `ane_bridge_free_trace_time3_pregate_state_20260620.jsonl` | 结论: 本轮 verdict=`confirmed`；failure 没有在 `pre+gate + live snapshot` 下重新出现，因此当前不能再把 `pre+gate` 当作 first invalid retained subset。当前最高价值解释转向：run2 failure 对 live introspection 或其引入的 timing slack 敏感，而不是由简单 cached subset 边界单独决定 | 下一步: 去掉当前重型全量 handle snapshot，改做更小的 timing/control probe，例如显式固定延时或单个 representative handle 的一次性轻量读取，确认恢复成功究竟来自 timing slack 还是 introspection 路径本身
2026-06-20 03:53:03 +0800 | 目标: 把 `pre-only + full snapshot` 的成功翻转继续拆成更小的 timing/control 变量，判断轻量延时或轻量 bridge read 是否已经足够救回 run2 | 动作: 先在 `benchmark/private_ane_multifamily_free_profile_probe.py` 增加两个最小开关：`--sleep-before-run-ms` 与 `--representative-handle-state {none,before,after,both}`，不改 runner 主逻辑；随后并行运行 `pre-only + sleep250ms` 与 `pre-only + representative-before`，再补跑 `pre-only + representative-before+after`，输出到 `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_sleep250_20260620.json`、`...pre_representative_before_20260620.json`、`...pre_representative_both_20260620.json`；最后新增 `mps/ANE/.ane_runs/json/pre_snapshot_load_bearing_matrix_verdict_20260620.json` 归档矩阵结论 | 证据: baseline `multifamily_keep_layers4_time3_pre_20260620.json` 在 run1 失败；`pre_state` 路径 `multifamily_keep_layers4_time3_pre_state_20260620.json` 在 run1 成功；但新三格 `sleep250` / `representative_before` / `representative_both` 都是 `run1_ok=false`，且 `representative_both` 虽能前后读到稳定的 `model_state=3` / `queue_depth=127`，run1 仍报 `RuntimeError('ANE eval failed')` | 结论: 本轮 verdict=`confirmed`；成功翻转不能再被简化为 `纯 timing slack` 或 `一次/两次轻量 describe_handle`。当前 load-bearing effect 仍然依赖 full cache snapshot 这类更重的观测面 | 下一步: 直接拆 full snapshot 自身，优先测 snapshot 只读前 N 个 handles、只读 before/after 单侧、或只读某一 axis/层，找出 first load-bearing subset
2026-06-20 04:01:55 +0800 | 目标: 继续拆 `full snapshot` 的 placement/cardinality，判断 green path 是否能由 before-only、after-only 或全局 first-handle 子集承载 | 动作: 在 `benchmark/private_ane_multifamily_free_profile_probe.py` 新增 `--snapshot-phase {none,before,after,both}` 与 `--snapshot-limit`，只改本文件；先跑 `pre-only` 的 `before/after/both + limit=1` 三格，再补 `before-full` 与 `after-full` 两格，输出到 `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_*_20260620.json`；最后新增 `mps/ANE/.ane_runs/json/pre_snapshot_phase_cardinality_verdict_20260620.json` 归档结论 | 证据: `before-limit1`、`both-limit1`、`before-full` 都会在 `run0` 直接报 `RuntimeError('ANE eval failed')`；`after-limit1` 与 `after-full` 都能保住 `run0`，但仍在 `run1` 失败；此前 `pre_state` 的 `both-full` 仍是唯一已知 `run0/run1` 双绿路径 | 结论: 本轮 verdict=`confirmed`；当前 green path 不能被压成 `before-only`、`after-only` 或全局 `first-handle` 子集。当前 load-bearing effect 更像依赖 `both-side full snapshot` 的某个更结构化 subset，而不是简单的单侧 placement 或粗暴全局 limit | 下一步: 继续拆 `both-side full snapshot` 的结构化子集，优先测“每个 entry 只读第一个 handle”、`time-only/freq-only`、`layer0 only/layer0-1 only`
2026-06-20 04:08:46 +0800 | 目标: 把 `both-side full snapshot` 继续拆成更结构化的 subset，判断 green path 是否能由“每个 entry 只读第一个 handle”或单 axis `both-side` 承载 | 动作: 在 `benchmark/private_ane_multifamily_free_profile_probe.py` 新增 `--snapshot-axis`、`--snapshot-max-layer`、`--snapshot-first-handle-per-entry`，仍只改本文件；随后运行 `both-side + first-handle-per-entry`、`both-side + time-only`、`both-side + freq-only` 三格，输出到 `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_both_*_20260620.json`；最后新增 `mps/ANE/.ane_runs/json/pre_snapshot_structured_subset_verdict_20260620.json` | 证据: `both-side first-handle-per-entry` 与 `both-side freq-only` 都在 `run0` 直接报 `RuntimeError('ANE eval failed')`；`both-side time-only` 能保住 `run0`，但仍在 `run1` 失败；此前 `both-side full snapshot` 仍是唯一已知双绿路径 | 结论: 本轮 verdict=`confirmed`；当前 green path 不能压成单 axis 或每个 entry 的第一个 handle。当前 load-bearing effect 更像是浅层 cross-axis 混合 subset，而不是任何单 axis / 单 handle-pattern | 下一步: 继续测浅层组合，优先 `layer0 only`、`layer0-1 only`、`time-all + freq-layer0`、`freq-all + time-layer0`
2026-06-20 04:13:55 +0800 | 目标: 继续测试 `both-side full snapshot` 的浅层 layer/cross-axis 组合，判断是否已有第一个不破坏 `run0` 的 mixed subset | 动作: 在 `benchmark/private_ane_multifamily_free_profile_probe.py` 增加 `--snapshot-time-max-layer` 与 `--snapshot-freq-max-layer`，仍只改 probe 文件；随后运行 `layer0 only`、`layer0-1 only`、`time-all + freq-layer0`、`freq-all + time-layer0` 四格，输出到 `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_*_20260620.json`；最后新增 `mps/ANE/.ane_runs/json/pre_snapshot_shallow_cross_axis_verdict_20260620.json` | 证据: `layer0 only`、`layer0-1 only`、`time-all + freq-layer0`、`freq-all + time-layer0` 四格全部在 `run0` 直接报 `RuntimeError('ANE eval failed')`；此前 `both-side full snapshot` 仍是唯一已知双绿路径 | 结论: 本轮 verdict=`confirmed`；当前 green path 不属于任何已测试的浅层 layer/cross-axis 组合。下一步必须继续增加层深或覆盖范围，而不是停留在 layer0 / layer1 的浅层混合 | 下一步: 继续增加层深，优先 `layer0-2 only`、`time-all + freq-layer0-1`、`freq-all + time-layer0-1`
2026-06-20 04:20:04 +0800 | 目标: 继续增加层深，验证是否已出现第一个不再破坏 `run0` 的更深 cross-axis / layer 组合 | 动作: 委派 `test-runner` 运行 `layer0-2 only`、`time-all + freq-layer0-1`、`freq-all + time-layer0-1` 三格，输出到 `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_*_20260620.json`；主线程只做结果归档并新增 `mps/ANE/.ane_runs/json/pre_snapshot_deeper_non_destructive_boundary_verdict_20260620.json` | 证据: `layer0-2 only`、`time-all + freq-layer0-1`、`freq-all + time-layer0-1` 三格全部 `run_count=2`，且 `run0_ok=true`、`run1_ok=false`、`run1_error=\"RuntimeError('ANE eval failed')\"`；相较前一轮浅层组合，这 3 格首次不再破坏 `run0` | 结论: 本轮 verdict=`confirmed`；当前已找到第一个 non-destructive deeper boundary，但它仍然不足以救回 `run1`。下一步应从这个边界继续加覆盖，而不是回到更浅组合 | 下一步: 继续加覆盖，优先 `layer0-3 only`、`time-all + freq-layer0-2`、`freq-all + time-layer0-2`
2026-06-20 04:48:32 +0800 | 目标: 复验当前 probe 代码下 `both-side full snapshot` baseline 是否仍然双绿，避免在失真基线上继续解释 subset 结果 | 动作: 委派 `test-runner` 运行两条命令：1) 当前 `full snapshot` baseline 重跑到 `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_state_recheck2_20260620.json`；2) `no snapshot` red baseline 对照到 `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_nosnapshot_recheck_20260620.json`；主线程同时对齐已有 `...pre_state_recheck_20260620.json`，并新增 `mps/ANE/.ane_runs/json/pre_snapshot_baseline_drift_verdict_20260620.json` | 证据: 历史 `multifamily_keep_layers4_time3_pre_state_20260620.json` 仍记录双绿；但当前代码下 `pre_state_recheck_20260620.json` 与 `pre_state_recheck2_20260620.json` 都是 `run0_ok=true, run1_ok=false, run1_error=\"RuntimeError('ANE eval failed')\"`，且 `pre_nosnapshot_recheck_20260620.json` 也是同样的 red baseline | 结论: 本轮 verdict=`confirmed`；当前 probe 代码下，历史 full-snapshot green path 已稳定漂移成红，并且与 no-snapshot red baseline 行为同态。在恢复一个可区分 green/red 的基线前，不应再把后续 subset 结果当成对旧 green path 的直接收敛 | 下一步: 优先判断这是 probe 默认语义漂移还是运行时/环境漂移，并先恢复基线判别力
2026-06-20 04:48:32 +0800 | 目标: 在确认 full-snapshot baseline 已漂移成红后，继续判断这更像 probe 语义漂移还是 runtime/environment 漂移 | 动作: 主线程先核对 `benchmark/private_ane_multifamily_free_profile_probe.py` 当前默认值与历史 green case 的 snapshot 形态；确认 `snapshot_phase=both`、`snapshot_limit=0`、`snapshot_axis=all`、layer/filter 全关时，当前 `cache_before/cache_after` 长度仍与历史 green case 同态；同时发现 probe 文件当前是 untracked、无 authoritative git baseline；随后新增 `mps/ANE/.ane_runs/json/pre_snapshot_drift_source_verdict_20260620.json` | 证据: `pre_state_20260620.json` 与 `pre_state_recheck{,2}_20260620.json` 的 cache 形态都是 run0 `0/15`、run1 `15/15`；当前 `full snapshot` recheck 与 `no snapshot` baseline 都在 `run1` 稳定变红；`git ls-files` 明确显示 `benchmark/private_ane_multifamily_free_profile_probe.py` 为 `untracked` | 结论: 本轮 verdict=`inconclusive`；现有证据更像 runtime/environment drift，而不是新增默认开关直接改坏了 full-snapshot 语义，但因为 probe 文件没有 git 历史基线，仍不能彻底排除脚本语义漂移 | 下一步: 做更强的 code-vs-runtime 分离验证，例如重构最小 historical full-snapshot side path，或在 fresh runtime reset 后复验同一脚本
2026-06-20 05:17:02 +0800 | 目标: 用更强的 code-vs-runtime 分离证据判断 baseline 漂移是否主要来自当前 featureful snapshot helper | 动作: 在 `benchmark/private_ane_multifamily_free_profile_probe.py` 中新增一条独立的 `historical_simple` snapshot 实现，不改 runner；随后委派 `test-runner` 并排运行 `snapshot_impl=current` 与 `snapshot_impl=historical_simple` 两条 full-snapshot recheck，输出到 `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_state_current_impl_recheck_20260620.json` 与 `...historicalsimple_recheck_20260620.json`；最后新增 `mps/ANE/.ane_runs/json/pre_snapshot_code_vs_runtime_split_verdict_20260620.json` | 证据: `current` 与 `historical_simple` 两条路径都表现为 `run0_ok=true, run1_ok=false, run1_error=\"RuntimeError('ANE eval failed')\"`，且 snapshot 形态都保持与历史 green case 相同的 run0 `0/15`、run1 `15/15`；差异只体现在 wall time，不改变 run verdict | 结论: 本轮 verdict=`confirmed`；当前 featureful helper 自身已不再是最有力解释，runtime/environment drift 成为当前主导假设。下一步应优先做更强的 runtime reset / fresh-runtime 复验，而不是继续在当前失真基线上切 subset | 下一步: 设计并执行一个 fresh-runtime reset 路径，再用同一脚本复验 full-snapshot baseline
2026-06-20 05:49:43 +0800 | 目标: 用 strict serial fresh-process A/B 验证当前 red baseline 是否仍然是同进程 authored runtime state | 动作: 先尝试并行 A/B 后立即纠正，杀掉并发实例；随后严格串行运行同一条 `historical_simple` full-snapshot 路径：进程 A 单次写入 `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_state_processA_single_20260620.json`，确认 A 完整退出后，再单独运行进程 B 到 `...processB_single_20260620.json`；同时与同脚本 `repeats=2` 的 `pre_state_recheck2_20260620.json` 对比；最后新增 `mps/ANE/.ane_runs/json/pre_snapshot_fresh_process_reset_verdict_20260620.json` | 证据: 进程 A 单次 `run0_ok=true`，A 退出后进程 B 单次 `run0_ok=true`；但 `repeats=2` 的 in-process baseline 仍然是 `run0_ok=true, run1_ok=false, run1_error=\"RuntimeError('ANE eval failed')\"` | 结论: 本轮 verdict=`confirmed`；fresh-process reset 可以恢复 green，而同一进程的第二次运行仍然变红。这说明当前问题仍然是同进程 authored runtime state，而不是跨进程持久污染 | 下一步: 在单进程内寻找最小用户态 reset / controller rebuild 步骤，尝试复制 fresh-process 的 green 行为
2026-06-20 06:18:14 +0800 | 目标: 在同进程内找到第一个真正能把 `run1` 拉回绿的最小用户态 reset 动作 | 动作: 先把 `clear_transformer` / `clear_cache` / `rebuild_runner` 接进 `benchmark/private_ane_multifamily_free_profile_probe.py` 作为 `--between-run-reset` 选项；注意到并发矩阵会污染 `run0` 后，单独严格串行重跑 `clear_transformer` 到 `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_reset_clear_transformer_recheck_20260620.json`；与无 reset 的 `pre_state_recheck2_20260620.json` 对照后，新增 `mps/ANE/.ane_runs/json/pre_min_user_reset_clear_transformer_verdict_20260620.json` | 证据: 无 reset baseline 仍是 `run0_ok=true, run1_ok=false, run1_error=\"RuntimeError('ANE eval failed')\"`；而 `clear_transformer` 严格串行复验变成 `run0_ok=true, run1_ok=true` | 结论: 本轮 verdict=`confirmed`；`clear_transformer_cache` 已经是当前最小已知有效用户态 reset 边界。当前 authored runtime state 被进一步局限到 transformer retention 一侧，但这仍不是 reuse 解，因为它依赖释放 transformer handles | 下一步: 继续拆 `clear_transformer_cache` 本身，优先区分“仅释放 handles / runner rebuild / controller-relevant rebuild”哪一部分才是真正 load-bearing
2026-06-20 06:43:52 +0800 | 目标: 把 `clear_transformer_cache` 再拆成更小成分，判断真正的 load-bearing reset 是“丢引用”还是“free live handles” | 动作: 在 `benchmark/private_ane_multifamily_free_profile_probe.py` 里新增 `drop_transformer_refs`、`free_transformer_no_gc`、`rebuild_runner_only` 三个 reset 模式；随后分别运行三格并读取输出，重点对比 `drop_transformer_refs`、`free_transformer_no_gc` 与已知双绿的 `clear_transformer` 严格串行复验；最后新增 `mps/ANE/.ane_runs/json/pre_min_reset_component_split_verdict_20260620.json` | 证据: `drop_transformer_refs` 在 `run0` 直接失败；`free_transformer_no_gc` 结果是 `run0_ok=true, run1_ok=true`；`clear_transformer_recheck` 同样是双绿 | 结论: 本轮 verdict=`confirmed`；恢复 green 的 load-bearing reset 不是丢 Python cache 引用，而是**真正 free live transformer handles**。`gc` 不是必需成分 | 下一步: 继续把“free handles”与更宽的 runner/controller rebuild 关注点分离，测试 targeted bridge/controller refresh 是否还会额外改变行为
2026-06-20 07:03:58 +0800 | 目标: 继续把最小有效 reset 从“free handles”与“bridge/controller rebuild”之间分离，判断更宽的 rebuild 是否真的必要 | 动作: 先补跑 `free_transformer_new_bridge` 的严格串行复验到 `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_reset_free_transformer_new_bridge_20260620.json`，并与已有 `drop_transformer_refs` / `free_transformer_no_gc` 结果并排；随后新增 `mps/ANE/.ane_runs/json/pre_reset_bridge_rebuild_nonessential_verdict_20260620.json` | 证据: `drop_transformer_refs` 在 `run0` 直接报 `RuntimeError('ANE eval failed')`；`free_transformer_no_gc` 仍然双绿；而 `free_transformer_new_bridge` 在 `run0` 前就触发 `MemoryError('private_ane RSS exceeded limit: 1851.0 MB > 1792.0 MB at freq_layer1_before_segment_compile')` | 结论: 本轮 verdict=`confirmed`；当前恢复 green 的最小有效动作并不需要 bridge/controller rebuild。更宽的 bridge 重建在本 probe 下反而更差，当前最小有效恢复动作仍然就是 **free live transformer handles** | 下一步: 直接回到长期主问题，判断在不 free handles 的前提下是否还存在任何 retained subset 能 survive；若不能，则更强地指向 lower control layer
2026-06-20 13:30:31 +0800 | 目标: 回到长期主问题，验证在不 free handles 的前提下当前是否还有任何 retained transformer subset 能 survive | 动作: 主线程直接并行运行 `historical_simple` 路径下的 `transformer_handle_scope=pre`、`pre_gate`、`full` 三格，统一使用 `repeats=2`、`between_run_reset=none`，输出到 `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_retained_{pre,pregate,full}_20260620.json`；随后新增 `mps/ANE/.ane_runs/json/pre_retained_subset_no_survivor_verdict_20260620.json` | 证据: `pre` retained scope 在 `run0` 直接报 `RuntimeError('ANE eval failed')`；`pre_gate` retained scope 是 `run0_ok=true, run1_ok=false`；`full` retained scope 也在 `run0` 直接报 `RuntimeError('ANE eval failed')` | 结论: 本轮 verdict=`confirmed`；在当前用户态控制面内，已测 retained subset 无一存活。当前更强结论已经从“还要不要继续调 cache policy”切到“retained reuse 很可能需要 lower control layer” | 下一步: 把决策边界正式收束成“是否还存在最后一个可信 retained-control 路径；若没有，就把 lower control layer blocker package 再明确一层”
2026-06-21 23:32:01 +0800 | 目标: 验证 `program+0xa0/+0xa8` 在当前 visible ANEServices runtime probe 中是否仍可 user-space author，且这些写入是否足以改变任何可见 `prepare/chaining/raw_prepare` status surface | 动作: 先在 `mps/ANE/experiments/ane_services_program_create_runtime_probe.m` 增加 `--patch-program-wrapper-a0 VAL` 与 `--patch-program-wrapper-a8 VAL` 两个最小 CLI 开关，只在 `ProgramCreate` 成功后、`prepare/chaining/raw_prepare` 前 patch wrapper 字段并落盘 patch 前后快照；随后编译 probe；再对 `hwx_precompiled_path_hwx` case 重新跑 4 组权威对照到 `mps/ANE/.ane_runs/json/program_wrapper_authorability_{baseline_v2,a0_zero_v2,a8_one_v2,both_v2}_20260621.json`；并结合 H16 IDA 事实新增 `mps/ANE/.ane_runs/json/program_wrapper_authorability_status_boundary_verdict_20260621.json` | 证据: baseline `raw_prepare_owner0_ready1_buffer_initial.u32_0x30 = 0`；`a0_zero_v2` 将 `wrapper_qword_0xa0` 从 `0x0000000100000015` 改到 `0x0000000000000000`；`a8_one_v2` 将 `wrapper_qword_0xa8` 从 `0x0000000100000000` 改到 `0x0000000000000001`，并把 `raw_prepare_owner0_ready1_buffer_initial.u32_0x30` 从 `0` 推到 `1`；但四格 `baseline/a0_zero/a8_one/both` 的 `prepare0/prepare1/prepare1_wordargs/chaining_prepare/raw_prepare_owner0_ready1` 返回码始终固定为 `0x00000003 / 0x00000014 / 0x00000014 / 0x00000014 / 0xe00002c2`；H16 侧另有新事实：`+0xa8` 在 helper `0x8C48/0x8CAD` 以 32-bit compare/control 方式消费，`+0xa0` 在 `0x63EF/0xA9E5/0x8387` 以 64-bit pointer-like 方式消费 | 结论: 本轮 verdict=`confirmed`；当前 visible ANEServices wrapper surface 不是“完全不可写”，而是“可写，且 `+0xa8` 的变化能真实进入 visible raw_prepare 参数面，但仍不足以改变当前可见 status surface”。formal boundary 因而继续下压到 `raw_prepare` 之下的 lower handoff / control layer | 下一步: 用已打通的 client-side Frida trace 直接对比 baseline vs `a8 -> 1`，确认 `u32_0x30` 翻转后 lower-visible `raw_prepare/IOConnect` payload 或 selector traffic 是否仍完全不变；若仍不变，则把 blocker 再正式下压一层
2026-06-22 00:09:49 +0800 | 目标: 判断 `program+0xa8` 翻转后的 `u32_0x30` 变化是否已经进入 lower-visible public selector handoff，还是仍死在 raw_prepare 之前 | 动作: 先给 `mps/ANE/experiments/frida_selector9_raw_prepare_trace.js` 补上最小增量日志：`raw_prepare` 记录 `prefix_56b_before/after` 与 `u32_0x30_before/after`，`IOConnectCallStructMethod` 记录 `input_prefix_64b` 与 `input_u32_0x30`；随后重新验证 `frida -f` spawn 仍然只给出 `script_loaded + hook_install` 假阴性，因此改用新的 working launcher：直接启动 `ane_services_program_create_runtime_probe --only-case data_precompiled_path_hwx --call-chaining-prepare --chaining-arg2 0 --pause-after-symbol-resolve-ms 5000 --symbol-dump-file ...`，等 symbol dump 落盘后再 `frida -p <probe_pid> -l frida_selector9_raw_prepare_trace.js` attach；最后分别对 baseline 与 `--patch-program-wrapper-a8 0x1` 跑 attach trace，落盘到 `mps/ANE/.ane_runs/logs/program_wrapper_a8_frida_attach_{baseline,a8_one}_20260622.jsonl`，并新增 `mps/ANE/.ane_runs/json/program_wrapper_a8_selector4_handoff_boundary_verdict_20260622.json` | 证据: baseline attach trace 中 `raw_prepare_enter.u32_0x30` 序列为 `0,0,0,0,0,0,0x7f,0x7f,0x7f,0x7f`，`iokit_enter.input_u32_0x30` 序列为 `0,0,0,0x7f,0x7f,0x7f,0x7f`；patched attach trace 中它们分别变为 `1,1,1,1,1,1,0x7f,0x7f,0x7f,0x7f` 与 `1,1,1,0x7f,0x7f,0x7f,0x7f`；但两边的 public selector 序列都仍然全是 `4`，`iokit_leave.ret` 都仍然全是 `0xe00002c2`，`chaining_prepare_leave.ret` 都仍然是 `0x14` | 结论: 本轮 verdict=`confirmed`；`program+0xa8` 的 visible patch 不仅进入 `raw_prepare`，还继续进入 public selector-4 输入面，因而剩余 retained-control 语义已明确下压到 selector-4 之下的 lower consumer / deeper paired-state gate，而不再停留在 visible wrapper / raw_prepare / public selector input 之前 | 下一步: 在 H16 / ANEServices 的 ProgramPrepare 路径中定位 selector-4 输入 `+0x30` 的下游消费者，判断它是在更低层被忽略、被规范化，还是需要另一个 paired field 才能影响 retained-control 决策
2026-06-22 00:26:06 +0800 | 目标: 静态确认 public selector-4 `input+0x30` 在 H16 ProgramPrepare 路径里是否有 direct lower consumer | 动作: 先用 `ida-pro-mcp` 重新打开 `mps/ANE/.ane_runs/tmp/AppleH16ANEInterface.patched.macho` 为 session `h16_prepare`；随后窄查 `ANE_ProgramPrepare` external method、`ANEClientDevice::programPrepare`、`ANEDriver::ANE_ProgramPrepare_gated`、`ANEHWDevice::ANE_ProgramPrepare_gated`；重点验证 external wrapper 是否 transport `input+0x30`、`ANEClientDevice` 是否原样 forward args pointer、以及 gated lower path 是否有任何 `args+0x30` direct read；最后新增 `mps/ANE/.ane_runs/json/selector4_input_0x30_lower_consumer_boundary_verdict_20260622.json` | 证据: `ANE_ProgramPrepare` 在 size gate 通过后会做 `structureOutput[6] = structureInput[6]`，即把 selector-4 `input+0x30` transport 到 ProgramPrepareArgs；`ANEClientDevice::programPrepare` 仅 `MOV X19, X1` 后在 lower vtable call 前 `MOV X1, X19`，说明 args pointer 被原样 forward；但 `ANEDriver::ANE_ProgramPrepare_gated` 与 `ANEHWDevice::ANE_ProgramPrepare_gated` 当前都没有 `args+0x30` direct read；`ANEHWDevice::ANE_ProgramPrepare_gated` 当前 direct read 的是 `args+0x0/+0x8/+0x10/+0x18/+0x20`，而其仅有的 `+0x30` 访问是 `LDR X12, [X20,#0x30]` 与 `LDR X8, [X22,#0x30]`，发生在 `lookupProgramResource()` 之后，属于 looked-up lower objects / derived state | 结论: 本轮 verdict=`confirmed`；selector-4 `input+0x30` 确实被 transport 到 lower prepare path，但它不是当前 visible H16 prepare gated path 的 direct consumer。它更像 transported sideband，而剩余 retained-control 语义更可能落在 derived lower object state 或 `args+0x10/+0x18/+0x20/+0x8` 这组真正被 direct read 的 paired fields 上 | 下一步: 直接围绕 `args+0x10/+0x18/+0x20/+0x8` 这组字段做下一轮 lower candidate 排序，优先结合动态 trace 与 H16 static path，判断哪一个最可能是当前 retained-control 的 load-bearing pair
2026-06-22 00:31:40 +0800 | 目标: 对 selector-4 prepare 路径里真正被 direct read 的字段做第一轮候选排序，并验证哪类 visible surrogate patch 最值得继续追 | 动作: 先让 `searcher` 汇总仓库内已有 `+0x8/+0x10/+0x18/+0x20` 证据，再用主线程继续读 H16 static path，确认 `+0x18` 在当前 prepare path 更像 writeback slot；随后在 `mps/ANE/experiments/ane_services_program_create_runtime_probe.m` 里新增 raw-prepare args patch 开关：`--patch-prepare-byte8 VAL` / `--patch-prepare-qword10 VAL` / `--patch-prepare-qword10-live-intermediate` / `--patch-prepare-u32-20 VAL`；编译后对 `data_precompiled_path_hwx` 跑一组最小 matrix，输出到 `mps/ANE/.ane_runs/json/selector4_direct_read_{baseline,byte8_1,u32_20_1,byte8_1_u32_20_1,qword10_programHandle,byte8_1_qword10_programHandle}_20260622.json`，并汇总为 `selector4_direct_read_field_patch_matrix_20260622.json`；最后新增 `selector4_direct_read_field_candidate_ranking_verdict_20260622.json` | 证据: baseline `raw_prepare_owner0_ready1_buffer_initial = { u8_0x8=0, qword_0x10=0, u32_0x20=101568, u32_0x30=0 }`；H16 static path 显示 `+0x10` 是最强 direct-read 候选（直接进 `aneAllocateIntermediateBuffer(...)`），`+0x8` 是 gating byte，`+0x20` 更像 size/count sideband，而 `+0x18` 在当前 path 是 writeback slot；动态 matrix 中 `byte8_1`、`u32_20_1`、`byte8_1_u32_20_1`、`qword10_programHandle`、`byte8_1_qword10_programHandle` 五格的 visible status vector 全部保持 `0x2 / 0x2 / 0x14 / 0xe00002c2` | 结论: 本轮 verdict=`confirmed`；当前 selector-4 prepare 的更可信 retained-control 候选已收敛成 `+0x10/+0x8` 这对，而 `+0x18` 可暂时从 inbound candidate 列表里移除。与此同时，这轮也确认了：`+0x10=programHandle` 这种 naive visible surrogate 不足以推动状态改变，所以当前真正缺失的更像是 `args+0x10` 的 hidden lower handle source，而不是再翻一个表面 flag | 下一步: 直接恢复或逼近 selector-4 `args+0x10` 的正确 hidden source，并与 `+0x8` 配对做下一轮更强的 dynamic patch
2026-06-22 00:40:27 +0800 | 目标: 判断当前 probe 是否已经提供 selector-4 `args+0x10` 的任何可用 source，以及 nonzero `qword_0x10` 本身是否足以改变 lower-visible状态 | 动作: 先继续读 H16 static path，补出一条更稳妥的 author split：`ANE_ProgramCreate` 在 `0xfffffe000928b86c` 明确写 `additional_params+0x18`，而先前把 `0xfffffe00093061bc` 认作 `additional_params+0x10` author 的解释在本轮撤回；随后对四个 legacy case（`hwx_precompiled_path_hwx` / `data_precompiled_path_hwx` / `hwx_nonprecompiled_path_hwx` / `data_nonprecompiled_path_hwx`）做 live handle scan，输出到 `mps/ANE/.ane_runs/json/selector4_prepare_case_handle_scan_20260622.json`；再在 `ane_services_program_create_runtime_probe.m` 中新增 `--allow-daemon-layout-lower-probes`，让 daemon-layout case 也能跑 owner/service patch 下的 raw_prepare；最后对 `data_precompiled_path_hwx_daemon_layout` 做 baseline 与 `byte8_1` 最小对照，输出到 `mps/ANE/.ane_runs/json/selector4_daemon_layout_qword10_probe_20260622.json`，并回写 `selector4_qword10_source_gap_verdict_20260622.json` | 证据: 四个 legacy case 的 `live_runtime_graph.model_intermediateBufferHandle` 与 baseline `prepare qword_0x10` 全部为 `0`；daemon-layout baseline 则第一次给出 `raw_prepare_owner0_ready1_buffer_initial.qword_0x10 = 0x1`，但 `raw_prepare_owner0_ready1_status_hex` 仍然是 `0xe00002c2`，且 `byte8_1` 后也不变；同时 `qword10=programHandle` 与 `byte8_1 + qword10=programHandle` 仍然保持 `0x2 / 0x2 / 0x14 / 0xe00002c2` | 结论: 本轮 verdict=`confirmed`；当前边界已从“有没有非零 `+0x10`”收紧到“当前拿到的 nonzero `+0x10` 仍不具备 load-bearing 语义”。legacy 四格不给 `+0x10` source，daemon-layout 虽给出 trivial `qword_0x10=1` 但仍然红，所以真正缺的是 semantically correct 的 `+0x10` source，而不是 arbitrary nonzero | 下一步: 继续回到 `ProgramCreate / InitialSetup`，恢复 selector-4 `args+0x10` 的 semantically correct author/source，并据此设计下一次更早 surface 的 patch
2026-06-22 00:49:12 +0800 | 目标: 判断 wrapper `prepareFn(program, buffer, flag)` 的 second-arg buffer 自身是否就能暴露 selector-4 `+0x10` 的真实来源 | 动作: 先在 `ane_services_program_create_runtime_probe.m` 的 wrapper prepare 调用点补前后 buffer 快照：`prepare0_buffer_before/after`、`prepare1_buffer_before/after`、`prepare1_owner0_ready1_buffer_before/after`；随后编译 probe，并分别跑 `data_precompiled_path_hwx` 与 `data_precompiled_path_hwx_daemon_layout --allow-daemon-layout-lower-probes`；最后新增 `mps/ANE/.ane_runs/json/selector4_wrapper_prepare_buffer_inert_verdict_20260622.json` | 证据: legacy `data_precompiled_path_hwx` 下，`prepare0/prepare1/prepare1_owner0_ready1` 的 wrapper buffers 前后都保持全零，`qword_0x10` 没有任何 author；但同一条 case 的 `raw_prepare_owner0_ready1_buffer_initial` 已经带有 `u8_0x9=1` / `u8_0xa=1` / `u32_0x20=101568` / `qword_0x10=0`；daemon-layout 下 `raw_prepare_owner0_ready1_buffer_initial.qword_0x10 = 1`，而这来自本地 builder 直接拷贝 `req+0x10`，不是 wrapper author | 结论: 本轮 verdict=`confirmed`；wrapper `prepareFn` 的 second-arg buffer 是 inert surface，legacy/daemon 里看到的 `qword_0x10` 差异主要是 request-layout-derived，不是 semantically correct hidden source。因此下一步必须去 wrapper prepare 更早的 `ProgramCreate / InitialSetup` 或其它 carrier surface 恢复真实 `+0x10` | 下一步: 直接面向 `ProgramCreate / InitialSetup` 的 caller-provided slot / carrier surface 做下一轮 author-source 恢复，而不再继续追 wrapper prepare buffer
2026-06-22 00:56:10 +0800 | 目标: 判定当前 stable public `0xe00002c2` 是否仍应归因于 visible selector-4 prepare-arg shaping，还是已明确来自更低层的 kernel-side chaining prepare gate | 动作: 先利用现有动态 matrix 和 daemon-layout 修正，整理出“visible selector-4 input 已被多次成功 patch 却不改 public return”的统一事实；随后结合 `ida` 子代理对 H16 local binary 的极窄静态结论，新增 `mps/ANE/.ane_runs/json/selector4_e00002c2_lower_gate_boundary_verdict_20260622.json`；最后更新 `ane_state/ane_next`，把主调查面从 `ProgramCreate / InitialSetup qword10 source` 切换到 `ANE_ProgramChainingPrepare_gated` 内最早几个 `0x2c2` return branches | 证据: `program+0xa8 -> selector4 input+0x30`、`+0x8`、`+0x20`、`+0x10=programHandle`、daemon-layout `qword_0x10=1`、wrapper/buffer inertness 等多组 visible patch 均已达到 public selector-4 边界但 `iokit_leave.ret` 仍稳定 `0xe00002c2`；同时 H16 static evidence 表明 `ProgramInitialSetup` 本身不定义这条 failure family，而 `ANEHWDevice::ANE_ProgramChainingPrepare_gated` (`0xfffffe00093595b0`) 内部包含大量 `MOVZ #0x2c2` + `MOVK #0xe000` 的错误返回构造 | 结论: 本轮 verdict=`confirmed`；当前 decisive gate 已不宜再建模成 visible selector-4 prepare-arg shaping 问题，而应收敛到 kernel-side `ANE_ProgramChainingPrepare_gated` 的早期 `0x2c2` branches | 下一步: 直接缩小 `ANE_ProgramChainingPrepare_gated` 最早几个 `0x2c2` return 点的条件检查，判断下一次 probe 应围绕哪个 lower input / object offset 展开
2026-06-22 01:03:44 +0800 | 目标: 从 `ANE_ProgramChainingPrepare_gated` 里继续缩小当前最早的 exact `0xe00002c2` gate，判断 `+0x8/+0x10` 路径是否根本还没走到 | 动作: 因主线程 `ida-pro-mcp` 会话不稳定，先改用本地 `xcrun llvm-objdump --macho --disassemble --arch=arm64e` 对 `AppleH16ANEInterface.patched.macho` 做按地址窗口反汇编；随后围绕 `0xfffffe00093595b0` 抽出 `0x93595ec..0x9359824` 窗口，并将结果与上一轮 `ida` 子代理关于 `0xe00002c2` 来源的结论做 join；最后新增 `mps/ANE/.ane_runs/json/selector4_first_exact_0x2c2_gate_boundary_verdict_20260622.json` | 证据: `0xfffffe0009359644` 虽构造 `0x2c2` 常量，但经 `orr` 与 `0x2c` 组合后实际返回 `0xe00002ee`；当前最早的 exact `0xe00002c2` return 在 `0xfffffe000935968c` 一带，由 `prepare_args+0x38`、`+0x3950`、`+0xa614`、`+0x3040` 的 early validation 触发；而 `qword10` / `lookupProgramResource` 路径要到 `0xfffffe00093597ac` 才开始，明显晚于这条 gate | 结论: 本轮 verdict=`confirmed`；当前 hottest gate 不是 `+0x8/+0x10` 相关分支，而是 large internal prepare buffer 的 `0x38 / 0x3950 / 0xa614 / 0x3040` 早期校验面 | 下一步: 恢复当前 probe 路径对这组 large-buffer offsets 的 user-space author surface，判断哪一个最可能是当前 mismatch 的根源
2026-06-22 01:09:26 +0800 | 目标: 在 `0x38 / 0x3040 / 0x3950 / 0xa614` 这组 earliest exact `0xe00002c2` family 中，选出当前最值得继续 probe 的字段 | 动作: 先读取现有 `ane_bootkc_chaining_prepare_args_bridge_probe.csv`、`ane_services_chaining_prepare_write_surface_probe.csv`、`ane_bootkc_chaining_prepare_payload_use_scan.csv`；随后把 bootkc early reads 与 visible user-space writes/guards 做 join，并新增 `mps/ANE/.ane_runs/json/selector4_early_validation_author_surface_ranking_verdict_20260622.json` | 证据: write-surface probe 已明确 `0x38 = fixed_write.event_count`、`0x3040 = fixed_write.surface_group_a_count`、`0x3950 = fixed_write.surface_group_b_count`，并且这三族已有 visible wrapper guards；而 `0xa614` 在同一 probe 中只有 derived boundary：visible writes 停在 `local_args+0xa610`，bootkc 却会在 early validation 读取 `prepare_args+0xa614` | 结论: 本轮 verdict=`confirmed`；在当前 earliest exact `0xe00002c2` family 中，`0xa614` 是最不透明、最值得继续 probe 的 gap，而 `0x38/0x3040/0x3950` 已有更完整的 visible author/guard 解释 | 下一步: 直接恢复或模拟当前 probe 路径对 `0xa614` 的 author surface，判断它究竟是隐式零值还是缺少某个 user-space writer
2026-06-22 01:14:33 +0800 | 目标: 进一步区分 `ANE_ProgramChainingPrepare_gated` 内 exact `0xe00002c2` 的层级，避免把更晚的 `qword10` gate 和更早的 early-validation gate 混在一起 | 动作: 继续用本地 `xcrun llvm-objdump --macho --disassemble --arch=arm64e` 对 `0xfffffe00093595b0` 周边做窗口反汇编；从 `0x93597ac..0x93598bc` 补出 `qword10 -> lookupProgramResource / process` 路径，并将其与 `0x935968c` 的 earliest exact `0xe00002c2` gate 做并排对照；最后新增 `mps/ANE/.ane_runs/json/selector4_exact_0x2c2_branch_ladder_verdict_20260622.json` | 证据: 第一层 exact `0xe00002c2` 仍在 `0xfffffe000935968c`，由 `0x38 / 0x3950 / 0xa614 / 0x3040` early validation 触发；第二层 exact `0xe00002c2` 在 `0xfffffe0009359868`，来自 `lookupProgramResource(*prepare_args+0x10, &process, 0)` 返回空或 out-process 指针为空；而 `0xfffffe0009359644` / `0x9818` / `0x9858` 虽邻近 `0x2c2` 常量，但实际分别归属 `0xe00002ee` / `0xe00002c5` / `0xe00002f0` | 结论: 本轮 verdict=`confirmed`；当前 public-stable `0xe00002c2` 至少存在两层 gate ladder，现阶段必须先跨过第一层 early-validation family，再回到第二层 `qword10/lookupProgramResource` 分支 | 下一步: 继续围绕第一层 gate，优先恢复 `0xa614` 的 user-space author surface
2026-06-22 01:20:18 +0800 | 目标: 把 `0xa614` 从“最不透明的 static gap”推进到“可直接执行的 patch surface” | 动作: 先确认现有 `ane_services_chaining_prepare_write_surface_probe.csv` 已经把 visible writes 的终点卡在 `local_args+0xa610`，并验证 `0x38/0x3040/0x3950` 都已有 visible writer/guard；随后新增 `mps/ANE/experiments/frida_selector9_patch_a614.js`，该脚本在 `IOConnectCallStructMethod(selector=9)` 进入时解引用 descriptor 并直接 patch payload `+0xa614`；最后新增 `mps/ANE/.ane_runs/json/selector9_a614_author_surface_and_sim_patch_verdict_20260622.json`，把 `0xa614` 的 visible author-surface 问题正式闭合为“无 visible writer，但已有 direct simulation surface” | 证据: write-surface probe 明确 `local_args+0xa610 -> local_args+0xa614` 存在 4-byte gap，且无 visible direct or loop-authored write reaches `+0xa614`；新脚本则能在 selector-9 发生时直接 patch payload `+0xa614` 并把 patch 前后写到 `/tmp/frida_selector9_patch_trace.jsonl` | 结论: 本轮 verdict=`confirmed`；当前 `0xa614` 的可见 author-surface 问题已经不再是“未知”，而是“visible 无 writer，但 direct patch surface 已备好” | 下一步: 找到一条当前机器上真正会发出 selector-9 的 runtime path，并用这把 `0xa614` direct patch surface 去验证 lower gate 是否会被移动
2026-06-22 01:31:12 +0800 | 目标: 在当前机器上建立一条真正可用的 selector-9 runtime path，并立即验证 `0xa614` 与 `qword10` 单点 patch 是否足以移动 lower gate | 动作: 先从 `ane_services_static_probe.py` 抽出 selector-9 outer descriptor contract：`{args_ptr, 0xae30}` + `output_size=0x18`；随后在 `ane_services_program_create_runtime_probe.m` 中新增 `--manual-selector9-transport`，直接对当前 service 连接发 `IOConnectCallStructMethod(selector=9, ...)`，并补上 `--selector9-direct-patch-u32-a614` 与 `--selector9-direct-patch-qword10-program-handle` 两个最小 direct patch；编译后对 `data_precompiled_path_hwx` 运行 baseline、`a614=1`、`qword10=programHandle` 三格，输出到 `mps/ANE/.ane_runs/json/selector9_direct_transport_{a614_probe,gate_probe,qword10_programHandle}_20260622.json`，并汇总为 `selector9_direct_transport_boundary_verdict_20260622.json` | 证据: direct selector-9 baseline 已能稳定返回 `0xe00002c2`；baseline direct input 中 `0x38 / 0x3040 / 0x3950 / 0xa614` 全为 `0` 也仍然返回 `0xe00002c2`；`a614 = 1` 仍然返回 `0xe00002c2`；`qword10 = current programHandle` 也仍然返回 `0xe00002c2` | 结论: 本轮 verdict=`confirmed`；当前机器上“如何打到 selector-9”这一步已经完成，且 direct transport 已把调查面推进到 second exact `0xe00002c2` gate。单点 `0xa614` 和单点 `qword10` 都不足以改变 lower gate，下一步应直接恢复 `lookupProgramResource(*prepare_args+0x10, &process, 0)` 所需的 process/carrier state | 下一步: 直接围绕 second exact `0xe00002c2` gate 所需的 carrier/process state 做最小恢复或 patch，而不再停留在单点 field patch
2026-06-20 13:30:31 +0800 | 目标: 把 retained-reuse 这一轮证据链从零散 verdict 收束成可上抬的 formal blocker package | 动作: 基于当日已确认的 4 条主线事实独立新增 `mps/ANE/experiments/results/retained_reuse_formal_blocker_package.md`：1) `process-fresh green` vs `in-process run2 red` 判别面已恢复；2) 最小有效恢复动作已收敛到 **free live transformer handles**；3) bridge/controller rebuild 不是最小必需成分；4) 已测 retained subset 无一存活；随后把该 blocker package 回链到 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: `retained_reuse_formal_blocker_package.md` 已明确 formal blocker statement：当前用户态 retained-reuse surface 已逼近极限，若要在不 free handles 的前提下恢复 reuse，更可能需要 lower control-layer semantics；与同日 `pre_min_user_reset_clear_transformer_verdict_20260620.json`、`pre_min_reset_component_split_verdict_20260620.json`、`pre_retained_subset_no_survivor_verdict_20260620.json` 一致 | 结论: 本轮 verdict=`confirmed`；retained reuse 方向的 formal blocker package 已就位。下一步不应再无限扩展同层 retained-subset grid，而应只做最后一个 credible retained-control 反证，或者把 blocker package 正式上抬
2026-06-21 19:47:41 +0800 | 目标: 对最后一个 credible retained-control 候选做最小 selector-9 runtime 反证，判断同一连接上重复 `ProgramChainingPrepare` 是否会暴露新的可见状态 | 动作: 在 `mps/ANE/experiments/ane_services_program_create_runtime_probe.m` 中新增 `--repeat-prepare-same-connection` 开关；在首次 `rawPrepareFn(service, rawArgs)` 之后，用同一 `service/program/request` 再构造一份 fresh `rawArgsRepeat` 并调用第二次 `rawPrepareFn`，记录两次 status 与 24B 输出前缀是否相同；重新编译 probe 后，选取同时具备 `model.hwx/model.src/model.retain/model.mil/data/net.plist` 的 artifact root，运行 `--only-case data_precompiled_path_hwx --repeat-prepare-same-connection`，输出到 `mps/ANE/.ane_runs/json/selector9_repeat_same_connection_data_precompiled_20260621.json`；随后新增 `selector9_repeat_same_connection_data_precompiled_verdict_20260621.json` | 证据: `data_precompiled_path_hwx` case 下，第一次 `rawPrepare` 返回 `0xe00002c1`，第二次 `rawPrepare` 仍返回 `0xe00002c1`，`raw_prepare_repeat_same_status=1`，`raw_prepare_repeat_same_after_24b=1` | 结论: 本轮 verdict=`confirmed`；在首个真实 case 上，selector-9 same-connection repeat 没有暴露新的可见 retained-control state。这个结果显著削弱了 selector-9 visible layer 作为剩余高价值 retained-control 候选的可信度 | 下一步: 只决定两件事之一——补一个正交第二 case 作为最后反证，或把 blocker 正式下压到 selector-9 visible layer 之下（`ProgramPartialUnwire -> ProgramLoad(load_type=2)` handoff）
2026-06-21 19:50:50 +0800 | 目标: 为 selector-9 same-connection repeat 补一个正交第二 case，决定是否可以把 visible-layer retained-control 候选基本判死 | 动作: 在已新增 `--repeat-prepare-same-connection` 的 `ane_services_program_create_runtime_probe` 上，选取同一完整 artifact root 的第二个正交 case `hwx_precompiled_path_hwx`，输出到 `mps/ANE/.ane_runs/json/selector9_repeat_same_connection_hwx_precompiled_20260621.json`；随后与 `selector9_repeat_same_connection_data_precompiled_20260621.json` 并排比较，并新增 `selector9_repeat_same_connection_two_case_verdict_20260621.json` | 证据: `data_precompiled_path_hwx` 与 `hwx_precompiled_path_hwx` 两个 case 都表现为 `raw_prepare_status_hex = 0xe00002c1`、`raw_prepare_repeat_status_hex = 0xe00002c1`、`raw_prepare_repeat_same_status = 1`、`raw_prepare_repeat_same_after_24b = 1` | 结论: 本轮 verdict=`confirmed`；在两个正交 precompiled case 上，selector-9 same-connection repeat 都没有暴露新的可见 retained-control state。selector-9 visible layer 作为剩余高价值 retained-control 候选已显著降级 | 下一步: 只剩两条合理路——给出最后一个 lower-adjacent retained-control 路径，或把 blocker 正式上抬为 `ProgramPartialUnwire -> ProgramLoad(load_type=2)` handoff 边界
2026-06-21 19:50:50 +0800 | 目标: 把 retained-reuse 的 formal blocker 从“broad lower control layer”继续收紧成更具体的 shared-runtime handoff boundary | 动作: 在两条 selector-9 same-connection repeat 反证（`data_precompiled_path_hwx` / `hwx_precompiled_path_hwx`）与既有 retained-reuse formal blocker 基础上，独立新增 `mps/ANE/experiments/results/retained_reuse_handoff_boundary_blocker_package.md`；把当前 formal boundary 明确写成 `ProgramPartialUnwire -> ProgramLoad(load_type=2)` shared-runtime handoff，并回链到 `docs/ane_state.md` / `docs/ane_next.md` | 证据: 当前用户态 retained-control surface 已收尽；`free live transformer handles` 仍是最小有效恢复动作；selector-9 visible-layer repeat 在两个正交 case 上都无新状态；既有静态/动态证据已把 shared runtime continuation 收敛到 `ProgramUnload -> ProgramPartialUnwire -> ProgramReMap -> ProgramLoad(load_type=2)` | 结论: 本轮 verdict=`confirmed`；retained-reuse 的 formal blocker 已从“broad lower control layer”收紧到更具体的 `ProgramPartialUnwire -> ProgramLoad(load_type=2)` handoff boundary | 下一步: 只剩二选一——给出最后一个 lower-adjacent retained-control path 贴着该 handoff，或把这个 handoff-boundary blocker package 正式上抬
2026-06-21 20:07:12 +0800 | 目标: 在 handoff-boundary blocker 之外，确认当前机器是否还具备 daemon-side 直接下钻能力；若没有，再看 passive path 是否至少能触达 handoff 邻近符号 | 动作: 先基于 `aned` / `ANECompilerService` 的附加能力结果新增 `mps/ANE/experiments/results/retained_reuse_dynamic_attach_blocker_package.md`；随后在一个真实 `ane_services_program_create_runtime_probe` 负载期间，对 `aned` 执行 `sudo sample 554 1 1 -file mps/ANE/.ane_runs/logs/aned_sample_during_runtime_probe_20260621.txt`，再用 `rg` 检查采样栈中是否出现 `_ANEServer` / `_ANEDeviceController` / `handleIOKitEvent` / `ProgramChainingPrepare` / `ProgramLoad` / `ProgramPartialUnwire` 邻近符号 | 证据: 动态附加方面，frida/lldb/dtrace-pid 全部被 AMFI/platform-binary 结构性阻断；被动采样方面，`aned_sample_during_runtime_probe_20260621.txt` 在负载期间仅稳定显示 `ANE::ANEServicesThreadStart -> CFRunLoopRun -> mach_msg`，未触达更低层 handoff 邻近帧 | 结论: 本轮 verdict=`confirmed`；当前 formal blocker 已不仅是 shared-runtime handoff boundary，还叠加了 machine-level dynamic-attach blocker。当前 passive path 也尚未穿透到 handoff 邻近层 | 下一步: 决定是否还保留一个最后的 lower-adjacent passive/client-side 反证；若没有，就把当前 handoff+attach blocker package 作为本层正式结论上抬
2026-06-21 20:07:12 +0800 | 目标: 把 retained-reuse 方向从“不断追加同层反证”正式收束成 current-layer formal closeout | 动作: 在 handoff-boundary blocker 与 dynamic-attach blocker 基础上，新增 `mps/ANE/experiments/results/retained_reuse_current_layer_formal_closeout.md`，明确当前机器/当前权限层下的用户态 retained-control surface 已正式收口；随后把该 formal closeout 回链到 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: 当前证据链已同时包含 `process-fresh green vs in-process red`、`free live transformer handles` 是最小有效恢复动作、bridge rebuild 非必要、retained subset 无存活者、selector-9 visible repeat 两个正交 case 无新状态、dynamic attach 被 platform-binary/AMFI 结构性阻断、passive sample 未穿透 handoff 邻近层 | 结论: 本轮 verdict=`confirmed`；retained reuse 的 current user-space layer 已正式 closeout。下一步不应再扩展同层 retained grid，而只剩 capability escalation 或最后一个 lower-adjacent handoff 假设
2026-06-21 20:18:09 +0800 | 目标: 关闭最后一个 still-plausible 的 lower-adjacent 候选 `optOutOfModelMemoryUnwiring` / `kANEFKeepModelMemoryWiredKey` | 动作: 先用仓库级搜索确认当前源码中不存在 `optOutOfModelMemoryUnwiring` / `KeepModelMemoryWired` / `programInstanceOptions` 的 author surface；再结合 `docs/ane_state.md` 中既有 direct-create 结论（该 key 已被测试但不改变 lower create-program 失败形态），新增 `mps/ANE/.ane_runs/json/optout_model_memory_unwiring_candidate_closed_verdict_20260621.json` | 证据: 代码搜索零命中；`docs/ane_state.md` 已明确 `optOutOfModelMemoryUnwiring <- kANEFKeepModelMemoryWiredKey`，且 `modelIdentityStr / skipPrepare / lateLatch / powerSaving / keepWired` 这组 direct-create 参数都“不改变 lower create-program 的失败形态” | 结论: 本轮 verdict=`confirmed`；`optOutOfModelMemoryUnwiring` 在当前 surface 已可判死。当前 formal boundary 继续停在 shared-runtime handoff + machine-level attach blocker | 下一步: 除非引入新的 lower-surface capability，否则应把 handoff-boundary blocker package 作为 retained reuse 的当前正式结论上抬
2026-06-21 20:43:18 +0800 | 目标: 判断在 daemon-side attach 被 AMFI 阻断后，当前机器是否还保留任何本地 capability-escalation 路径 | 动作: 先用 `frida-trace -f` 尝试对自有 `ane_services_program_create_runtime_probe` 进程做最低成本 hook，因 stdout 管道不稳改为 `frida -f ... -l /tmp/hook_iocm.js` 的最小 JS 脚本方式；确认 Frida 能成功 spawn 目标并加载 hook 脚本，随后新增 `mps/ANE/.ane_runs/json/client_side_frida_capability_verdict_20260621.json` | 证据: 本机存在 `frida` / `frida-trace` 17.11.0；daemon-side attach 仍被 AMFI 阻断；但 `frida -f /Volumes/2T/pymss/mps/ANE/experiments/ane_services_program_create_runtime_probe -l /tmp/hook_iocm.js` 已成功 spawn 目标进程并加载脚本，只是当前 hook 输出还未稳定收回 | 结论: 本轮 verdict=`confirmed`；当前机器并非完全 capability-blocked，仍保留一条 client-side Frida instrumentation 路径。下一步应把这条路径从“能 attach”推进到“能稳定捕获 IOConnect selector/retval”。
2026-06-21 20:56:16 +0800 | 目标: 验证现有 `ane_ioconnect_trace_interpose.dylib` 是否能作为 selector-9 的稳定 client-side capture 面 | 动作: 先重新编译/确认 `ane_ioconnect_trace_interpose.dylib` 与 `ane_services_program_create_runtime_probe`，再用 `DYLD_INSERT_LIBRARIES` 包住 `ane_services_program_create_runtime_probe --only-case data_precompiled_path_hwx`，把 trace 写到 `mps/ANE/.ane_runs/csv/selector9_iokit_trace_20260621.csv`、JSON 写到 `mps/ANE/.ane_runs/json/selector9_iokit_trace_runtime_probe_20260621.json`；观测到 probe 长时间挂住后检查文件内容并手工 kill；随后新增 `selector9_iokit_interposer_negative_verdict_20260621.json` | 证据: CSV 只有 header，无任何 selector-9 row；JSON 仍是 `0B`；probe 挂住并需手工 kill | 结论: 本轮 verdict=`confirmed`；现有 public IOKit interposer 不是 selector-9 的稳定 capture 面。若继续本地下钻，更优先级应回到 client-side Frida 或更低观测点
2026-06-21 21:30:19 +0800 | 目标: 把 client-side Frida 从“能 attach”推进到“能稳定抓到 selector/retval/buffer” | 动作: 先给 `ane_services_program_create_runtime_probe.m` 补上环境变量驱动的 `symbol-dump + pause` 能力，再新增 `mps/ANE/experiments/frida_selector9_raw_prepare_trace.js`，尝试在 spawned probe 上用 generic hook 点（`IOConnectCallStructMethod` / `dlopen` / `dlsym` / 模块轮询）抓 `rawPrepare` 与 selector-9；随后又尝试结合 `symbol-dump + pause` 做更精确 attach，但在 frida-spawn 下并未稳定拿到 `rawPrepare` / selector 事件 | 证据: `/tmp/frida_selector9_trace.jsonl` 只能稳定记录 `script_loaded` 与 hook install，缺失 `raw_prepare_*` / `iokit_*` / `dlopen` / `dlsym` 事件；`/tmp/ane_symbols3.json` 在 frida-spawn 路径下也未出现；同时现有 IOKit interposer 仍是 header-only + hang | 结论: 本轮 verdict=`confirmed`；client-side Frida attach 能力存在，但当前 generic hook 集合仍拿不到稳定 capture。下一步应放弃泛 hook，改做 precise address-aware harness
2026-06-21 21:44:43 +0800 | 目标: 判断新的 CLI `symbol-dump + pause` 能否与 `frida -f` spawn 组合使用，作为 precise address-aware harness 的早期握手 | 动作: 先确认 probe 直接运行时 `--pause-after-symbol-resolve-ms 1 --symbol-dump-file /tmp/ane_symbols_cli_direct.json` 可正常落盘；再用 no-op Frida 脚本执行同样的 CLI 参数到 `/tmp/ane_symbols_cli_noop.json`；最后把 direct-positive / frida-spawn-negative 结果整理成 `mps/ANE/.ane_runs/json/frida_spawn_cli_pause_handshake_negative_verdict_20260621.json` | 证据: direct CLI 路径成功产生 `/tmp/ane_symbols_cli_direct.json`；但 `frida -f ... --pause-after-symbol-resolve-ms ... --symbol-dump-file /tmp/ane_symbols_cli_noop.json` 下，`/tmp/ane_symbols_cli_noop.json` 不会出现，尽管 frida 进程返回码为 0 | 结论: 本轮 verdict=`confirmed`；当前 precise address-aware harness 的阻塞点不在 probe 侧 dump 逻辑，而在 `frida-spawn` 与早期握手的兼容边界 | 下一步: 改 launcher model，而不是继续试同一 `frida-spawn + generic script` 组合
2026-06-21 21:56:49 +0800 | 目标: 把 client-side Frida 从“能 attach”推进成真正可用的 lower-adjacent runtime capture path | 动作: 先定位并修正关键 launcher 问题：去掉 `frida -q` 导致的会话提前退出；随后用 `frida-spawn` 配合 `mps/ANE/experiments/frida_selector9_raw_prepare_trace.js`、`symbol-dump + pause` 重跑 `data_precompiled_path_hwx`，并确认当前默认 trace 文件 `/tmp/frida_selector9_trace.jsonl` 中已出现 `module_added(ANEServices)`、`dlsym(ANEServicesProgramCreate/Prepare/DeviceOpen/...)`、`raw_prepare_enter/leave`、`IOConnectCallStructMethod(selector=4)` 事件；最后新增 `client_side_frida_precise_capture_verdict_20260621.json` | 证据: `/tmp/ane_symbols_live2.json` 在 frida-spawn 路径下成功落盘；默认 trace 文件中出现 `module_poll_hit`, `module_added`, `dlsym`, `raw_prepare_enter/leave`, `iokit_enter(selector=4)` 等事件；当前 buffer 前缀仍因脚本格式问题未完全清洗干净，且尚未驱动到 selector-9 事件 | 结论: 本轮 verdict=`confirmed`；client-side Frida 已从“可 attach”推进到“可用的 lower-adjacent runtime capture path”。下一步应聚焦正确 case / 正确 selector，而不是再证明这条路径能不能工作
2026-06-21 22:22:37 +0800 | 目标: 验证 `ANEServicesProgramChainingPrepare` 自身是否还是最后一个可信 visible retained-control 候选 | 动作: 先在 `ane_services_program_create_runtime_probe.m` 中新增可选 `--call-chaining-prepare --chaining-arg2` 路径，并确认 `ANEServicesProgramChainingPrepare` 导出可 `dlsym`；随后对 `data_precompiled_path_hwx` case 做显式调用，并用已打通的 client-side Frida trace 记录事件；最后新增 `mps/ANE/.ane_runs/json/chaining_prepare_wrapper_preselector9_gate_verdict_20260621.json` | 证据: `ANEServicesProgramChainingPrepare` 导出已解析到 `0x1a32d63cc`；显式调用后 `chaining_prepare_status_hex = 0x00000014`；Frida trace 中能看到 `chaining_prepare_enter/leave`，但没有任何 selector-9 `IOConnectCallStructMethod` 命中，只有 selector-4 事件 | 结论: 本轮 verdict=`confirmed`；最后一个 visible chaining-prepare 候选也在 selector-9 之前被 wrapper gate 掉。当前 formal boundary 已更强地压到 shared-runtime handoff / lower surface | 下一步: 除非引入新的 lower-surface capability，否则应把 current-layer formal closeout + handoff-boundary blocker package 作为 retained reuse 的当前正式结论上抬
2026-06-22 03:37:12 +0800 | 目标: 继续 direct selector-9 第二层 exact `0xe00002c2` gate 的 carrier/process-state 恢复，并补上最小 `qword0` / `u32_0x18` patch 面 | 动作: 在 `mps/ANE/experiments/ane_services_program_create_runtime_probe.m` 中新增 selector-9 direct `qword0` / `u32_0x18` patch 开关与 snapshot 字段；用 `xcrun clang -fobjc-arc -framework Foundation -framework IOKit` 成功重编 probe；随后分别测试旧的 `adhoc` entitled binary 与使用 `Apple Development: 3423714059@qq.com (W32PC4WWNC)` 重签的 `/tmp/ane_services_program_create_runtime_probe_test`，都在 `data_precompiled_path_hwx` + full artifact root (`mps/ANE/.ane_runs/runtime_wrapper_aug_weighted_ffn/add_all`) 上执行 `--manual-selector9-transport` baseline；最后用 `log show` 抓取 kernel / AMFI 诊断，并新增 `mps/ANE/.ane_runs/json/selector9_direct_transport_codesign_blocker_verdict_20260622.json` | 证据: 编译成功；本机存在 1 个有效 `Apple Development` codesign identity；两条运行命令都直接 `Killed: 9` / shell 返回 `137`；kernel log 明确给出 `/Volumes/2T/pymss/mps/ANE/.ane_runs/system_bins/ane_services_program_create_runtime_probe_entitled` 与 `/private/tmp/ane_services_program_create_runtime_probe_test` 的 `Code has restricted entitlements, but the validation of its code signature failed` | 结论: 本轮 verdict=`confirmed`；当前 blocker 已从 second-gate field semantics 暂时下沉为“重启后没有一个 AMFI 接受的 restricted-entitlement selector-9 probe host”。语义 patch 面已准备好，但这轮无法继续 runtime matrix | 下一步: 先恢复一个可运行的 entitled host 或等价注入 seam；一旦恢复，立刻在 `data_precompiled_path_hwx` 上执行 `{baseline, u32_0x18=1, qword10=programHandle+u32_0x18=1, 可选 qword0 patch}` 最小矩阵
2026-06-22 04:05:33 +0800 | 目标: 判断 AMFI host blocker 之下是否存在一条当前用户可达的合法 Apple-signed manager 链，而不是继续尝试自签 probe 或手工直启 appex | 动作: 先枚举系统 ANE 相关宿主 entitlement，确认 `/usr/libexec/modelmanagerd` 具备 `com.apple.modelmanager.inferenceprovidermanager` 与 inferenceprovider ExtensionKit host 权限；随后直接尝试拉起 `/System/Library/ExtensionKit/Extensions/{InferenceProviderService,TGOnDeviceInferenceProviderService,HostInferenceProviderService}.appex/Contents/MacOS/*`，并抓取内核日志；再对 `com.apple.modelmanager` 与 `com.apple.modelmanager.query` 做原始 XPC 探针，比较 empty-message reply；最后从 `modelmanagerd` 的 Swift 符号中恢复 `ModelManagerServices.ModelXPCRequest` / `CreateSessionRequest` / `Session.Metadata` / `InferenceProviderDescriptor` 的静态 shape，并新增 `mps/ANE/.ane_runs/json/modelmanager_inferenceprovidermanager_xpc_surface_verdict_20260622.json` | 证据: 三个 Apple-signed inferenceprovider appex 都不是签名损坏，而是被 `AMFI: Launch Constraint Violation` 拒绝从 Python parent 直接拉起；`frida -p 528` 无法从当前用户附着 `modelmanagerd`；但 `com.apple.modelmanager` 对 empty XPC message 返回正常 `_CodableBody` reply，而 `com.apple.modelmanager.query` 返回 `Connection invalid`；静态符号进一步确认 request family 根是 `ModelManagerServices.ModelXPCRequest`，且 `CreateSessionRequest = { metadata: Session.Metadata, alreadyLockedInferenceProvider: InferenceProviderDescriptor? }`，其中 `Session.Metadata.init(assetBundleURI:, useCaseID:, onBehalfOfPID:, parentOfOnBehalfOfPID:, loggingIdentifier:, id:, sessionSetID:)` 已可恢复 | 结论: 本轮 verdict=`confirmed`；合法 Apple-signed 宿主链并未消失，而是被收紧到 `modelmanagerd -> com.apple.modelmanager.inferenceprovider appex`。当前新 blocker 不再是“找宿主”，而是“恢复最小 Swift-Codable `ModelXPCRequest.createSession` 编码”，这样才能通过合法 manager 链拉起 inferenceprovider host 并回到 selector-9 / lower-gate 主线 | 下一步: 构造并发送最小 `createSession` Codable request 到 `com.apple.modelmanager`，优先验证 manager 会返回何种分类错误（invalid request / invalid inference provider / missing entitlement / provider not found），用它继续恢复 request shape
2026-06-22 04:31:28 +0800 | 目标: 把 `com.apple.modelmanager` 的真实 wire-format blocker 从“manager XPC surface 可 reach”继续收紧到 Codable wrapper 层，而不是盲猜 `createSession` 本体 | 动作: 先新增可复用实验工具 `mps/ANE/experiments/modelmanager_xpc_codable_probe.c` 并接入 `mps/ANE/experiments/Makefile`；随后用它对 `com.apple.modelmanager` 做 5 组 probe：1) 空 XPC message；2) `_CodableBody =` binary plist 空 dict；3) `_CodableBody =` binary plist 空 array；4) `_CodableBody =` 之前 `old XPC coder` reply 的 247B body replay；5) `_CodableBody =` 之前 `EarlyDecodingError` reply 的 129B body replay；最后新增 `mps/ANE/.ane_runs/json/modelmanager_xpc_codable_probe_verdict_20260622.json` | 证据: 空消息 reply 明确报 `Expected value of type TaskCancellableMessage<ModelXPCRequest> but found null instead`；binary plist body 稳定报 `EarlyDecodingError("Cannot read a valid tag from buffer")`；replay server-originated body 会稳定推进成 `DecodingError.typeMismatch: expected UInt64, found bool(false)`；所有 reply 都继续走 `_CodableBody/_CodableCoderVersion/_CodableOutOfLine*` 这套 envelope | 结论: 本轮 verdict=`confirmed`；`com.apple.modelmanager` 的新 blocker 已收紧成 `TaskCancellableMessage<ModelXPCRequest>` wrapper 内部的首个 `UInt64` 字段恢复问题。当前不需要再证明 manager 可达性，也不需要再尝试 plist body；下一步应围绕该 wrapper 做定向 byte-level / field-level 恢复 | 下一步: 先恢复 `TaskCancellableMessage<ModelXPCRequest>` 的首个 `UInt64` 字段及最小顶层容器，再把错误推进到 `createSession` request 本体
2026-06-22 04:42:07 +0800 | 目标: 判定 `expected UInt64, found bool(false)` 究竟来自 XPC envelope 还是 `_CodableBody` prefix，并尽量把 wrapper blocker 再往后推一层 | 动作: 先给 `modelmanager_xpc_codable_probe` 增加 `_CodableIsSync` 的多种编码模式（bool false/true、int64 0/1、omit）；随后以 `mm_oldcoder_reply_body.bin` / `mm_earlydecode_reply_body.bin` 为种子，验证 envelope 变体是否移动错误；再对 `_CodableBody` prefix 做定向 mutation：只把 offset `2` 的 `0x02` 改成 `0x03`，以及 `0x03 + 8-byte zero/one payload` 两组对照；最后新增 `mps/ANE/.ane_runs/json/modelmanager_taskcancellable_prefix_probe_verdict_20260622.json` | 证据: 改 `_CodableIsSync` 的类型和值完全不影响 `expected UInt64, found bool(false)`；但只改 `_CodableBody` 的 offset `2` tag，就能稳定把错误推进成 `EarlyDecodingError(\"Cannot read a valid string from buffer\")`，无论是否覆写后续 8 bytes 都成立 | 结论: 本轮 verdict=`confirmed`；首个 `UInt64` 字段的决定性边界已经定位在 `_CodableBody` prefix offset `2`，且它之后立刻进入 string-like 字段家族。当前 blocker 已经不再是找 `UInt64`，而是恢复它后面的 string-like 字段 | 下一步: 围绕 offset `2` 之后的 string-like 字段做更小的 tag/length/bytes 恢复，让 decode 继续穿过 `TaskCancellableMessage<ModelXPCRequest>` 前缀并开始命中 `ModelXPCRequest` 本体
2026-06-22 04:55:14 +0800 | 目标: 给 `TaskCancellableMessage<ModelXPCRequest>` 的首字段建立真实 tag-family 地图，判断当前应优先恢复 `UInt64` 本身，还是继续盲推进后续 string/tag 字段 | 动作: 先对 `_CodableBody` prefix offset `2` 做 `0x00..0x1f` 全扫描，分别在“保留原 trailing bytes”和“把 bytes 3..10 清零”两种条件下记录 ascii error；随后构造有效 string 注入（offset `2` 用 `0x03/0x11 + len=1 + 'A'`），并继续对 offset `13` / `24` 做 tag 扫描，确认后续 undecoded field 边界；最后新增 `mps/ANE/.ane_runs/json/modelmanager_taskcancellable_tag_scan_verdict_20260622.json` | 证据: offset `2` 已稳定区分出 `nil / bool(true) / bool(false) / string-like / key(XPC.EncodingGraph.Key.super) / XPC object index / containerMetadata` 等 tag family；注入有效 string 后，reply 从 low-level string error 推进成 `DecodingError.typeMismatch: expected UInt64, found string(\"A\")`；同时后续 undecoded tag boundary 会依次移到 offset `13`、offset `24` | 结论: 本轮 verdict=`confirmed`；当前最小突破口不是“继续瞎猜后续 string 字段”，而是“找出 offset `2` 位置真正接受的 `UInt64` 编码”。field1 已经被证实是个真实 typed value，只是我们还没把它编码对 | 下一步: 以 tag-family 地图为基础，定向恢复 offset `2` 的 `UInt64` 编码（优先数值/计数/varint/container-count 家族），成功后再继续推进 offset `13/24` 的 string-like/tag 字段
2026-06-22 05:38:46 +0800 | 目标: 判断 `AAAFoundationSwift` shared-cache encoder 是否足以替代当前 byte-level wrapper 恢复路线 | 动作: 先验证 `/System/Library/PrivateFrameworks/{AAAFoundationSwift,BlastDoor,ModelManagerServices}.framework/*` 都能被 `dlopen` / `ctypes.CDLL` 成功加载；随后用 ObjC runtime 盘点类 metadata，确认 `AAAFoundationSwift.XPCEncoder` / `XPCDecoder` / `DictionaryEncoder` 与 `BlastDoor.XPCEncoder` / `XPCDecoder` 可见但 method list 为空；再用 C 直接 `dlsym` 调 `AAAFoundationSwift.XPCEncoder/XPCDecoder` constructor，确认可返回非空对象；同时构造本地对照库 `LocalEncLib`，从其 IR 中恢复 generic instance method 低层 ABI，并成功用 5 实参低层调用 `LocalEnc.encode<T>` 返回 `{\"v\":\"7\"}`；最后把同一 ABI 搬到 `AAAFoundationSwift.XPCEncoder.encode` 上，分别对 `ctor0()` 和 `ctor1(meta)` 生成的实例尝试低层调用，并新增 `mps/ANE/.ane_runs/json/aaafoundationswift_runtime_bridge_verdict_20260622.json` | 证据: shared-cache framework reachability 已确认；constructor 调用已确认；本地对照库 low-level ABI 已确认；但 `AAAFoundationSwift.XPCEncoder.encode` 在 `before encode` 之后立刻崩溃，且与 `ctor0/ctor1` 路径无关 | 结论: 本轮 verdict=`confirmed`；shared-cache runtime bridge 真实存在，但当前卡在 `AAAFoundationSwift.XPCEncoder.encode` 的真正可调用 thunk / resilience 边界。它已成为一条高价值分叉，但暂时还不能替代 byte-level wrapper 恢复 | 下一步: 先决定是继续深挖 `AAAFoundationSwift.encode` 的真实 thunk / 非泛型包装，还是暂时放弃这条桥并回到 offset `2` 的 `UInt64` 编码恢复
2026-06-21 22:22:37 +0800 | 目标: 把当前 retained-reuse 层从“多个 formal blocker package 并列”收束成一个 machine-level capability boundary closeout | 动作: 基于当日已确认的 retained-subset 无存活者、最小恢复动作为 free live handles、selector-9 repeat 两 case 同态、explicit chaining wrapper pre-selector9 gate、keepWired candidate 关闭、daemon-side attach 阻断等证据，新增 `mps/ANE/experiments/results/retained_reuse_current_capability_boundary_closeout.md` 和 `mps/ANE/.ane_runs/json/retained_reuse_current_capability_boundary_verdict_20260621.json`；并回链到 `docs/ane_state.md` / `docs/ane_next.md` | 证据: 上述已落盘 verdict / blocker package 已共同表明当前 capability boundary 之上没有可信 retained-control path 剩余 | 结论: 本轮 verdict=`confirmed`；current capability boundary closeout 已确认。下一步只剩 capability escalation 或 truly lower-adjacent handoff hypothesis 两类
2026-06-22 05:52:31 +0800 | 目标: 区分 `AAAFoundationSwift.XPCEncoder.encode` 的崩溃究竟是“generic method ABI 不对”还是“当前只拿到 thunk-style entrypoint” | 动作: 先构造本地控制库 `DynEncLib`，让它同时导出 `encode...F` body 和 `encode...FTX/FTx` thunk-style 符号；再用已经在 `LocalEncLib` 校准过的 5 实参 ABI，分别对 `F`、`FTX`、`FTx` 做低层调用；最后新增 `mps/ANE/.ane_runs/json/swift_dispatch_thunk_abi_control_verdict_20260622.json`，并把结论映射回 `AAAFoundationSwift` 当前只见 `FTj` 的现状 | 证据: `DynEncLib.encode...F` 可稳定调用成功；`DynEncLib.encode...FTX` 会在 `before FTX` 后直接 bus error；`DynEncLib.encode...FTx` 会在 `before FTx` 后直接 illegal instruction；而 `AAAFoundationSwift.XPCEncoder.encode` 当前暴露的正是 thunk-style `FTj` entrypoint | 结论: 本轮 verdict=`confirmed`；当前 AAA bridge 的高概率 blocker 不是 generic body ABI 全局错误，而是“我们手上只有 thunk-style encode entrypoint，不能直接按 body-style ABI 调用”。这明显降低了继续硬怼 `FTj` 的价值 | 下一步: 若找不到 `AAAFoundationSwift.XPCEncoder.encode` 的非-thunk body/wrapper，就应正式回退到 byte-level 主线，继续恢复 `TaskCancellableMessage<ModelXPCRequest>` offset `2` 的真实 `UInt64` 编码
2026-06-22 06:07:18 +0800 | 目标: 判断 `AAAFoundationSwift.MessageSender.init(machService:)` 是否能成为 `XPCEncoder.encode` 之外的 non-thunk wrapper 出口 | 动作: 先用本地控制库 `ThrowInitLib` 的 `init(label:) throws` 从 IR 中确认 low-level throwing-init ABI；随后把同一 ABI 直接套到 `AAAFoundationSwift.MessageSender.init(machService:)`，分别对 `com.apple.modelmanager` 和 `definitely.invalid.codex.test` 做 raw-pointer 级调用；再静态确认 `MessageSender.send` 的 payload 约束，并新增 `mps/ANE/.ane_runs/json/aaafoundationswift_messagesender_probe_verdict_20260622.json` | 证据: `MessageSender.init(machService:)` low-level 调用对两种 service 字符串都返回 `err=nil` 且 non-null raw pointer；但 `MessageSender.send` 的静态约束是 `A: AAAFoundationSwift.Message`，而 `TaskCancellableMessage<ModelXPCRequest>` 当前只见 `Encodable/Decodable`，没有 `AAAFoundationSwift.Message` conformance 证据 | 结论: 本轮 verdict=`confirmed`；`MessageSender` 路线已经从“未知”收敛成“wrapper reachability 已成立，但 payload protocol mismatch 仍阻断主线”。AAA wrapper 路径应暂时降级，主线返回 byte-level 恢复 | 下一步: 回到 `TaskCancellableMessage<ModelXPCRequest>` field1 的真实 `UInt64` 编码恢复，并把后续 undecoded bytes 视为 `ModelXPCRequest` 根而不是继续主攻 AAA wrapper
2026-06-22 06:53:29 +0800 | 目标: 判断 field1 的 `0x14` 分支到底是不是 direct UInt64，还是一个 counted nested container seam | 动作: 新增 `mps/ANE/experiments/modelmanager_taskcancellable_u14_container_probe.py`，并把 baseline body 持久化到 `mps/ANE/.ane_runs/body/modelmanager_taskcancellable_typemismatch_reply_body_20260622.bin`，避免后续 loop 依赖 `/tmp`；随后复用 `modelmanager_xpc_codable_probe` 系统化跑了 4 组 coarse `u32` case、offset `7` 的 `0x00..0x1f` nested tag scan、`u32`/leaf follow-up 矩阵，以及 5 个不继承旧 `ipcError` tail 的最小 hand-authored body；结果落到 `mps/ANE/.ane_runs/csv/modelmanager_taskcancellable_u14_container_probe_20260622.csv` 与 `mps/ANE/.ane_runs/json/modelmanager_taskcancellable_u14_container_probe_verdict_20260622.json`；并追加 shared-cache 静态事实收集，确认 `AAAFoundationSwift` 中存在 `SingleValueDecodingContainer4OptionalPrimitive` 与对应 `Container size mismatch ...` 错误串、但不存在独立 `OptionalPrimitive` 类型名或 5-byte/8-byte `0x14` 头证据 | 证据: 原 trailing bytes 下 `u32=0 -> Container size mismatch for SingleValueDecodingContainer4OptionalPrimitive`，`u32=1/2/20 -> Found dangling container in buffer`；在 `u32=1` 下 offset `7` 会暴露真实 nested tag family（`0x03/0x11 -> string error`，`0x12 -> Bad index for XPC object: 285872917`，`0x13 -> bad .containerMetadata: 21`，`0x00/0x01/0x02/0x10/0x15 -> dangling`）；对连续一字节 leaf follow-up，`u32=0 -> Insufficient container`，`u32=1 -> Duplicate reference to node #1`，`u32>=2 -> dangling`；而极小 `0x14 + u32=1 + single child` body 一律仍是 `Insufficient container` | 结论: 本轮 verdict=`confirmed`；`0x14` 已从“direct UInt64 候选”收敛成“counted nested container family”，且 runtime / shared-cache 静态证据一致。当前缺失的是单 child 容器闭合后的最小 outer bookkeeping，而不是再猜一个 raw integer bytes 值 | 下一步: 固定 `u32=1 + single child` 骨架，author 不继承旧 `ipcError` payload 的最小 post-container outer tail，观察能否把 decode 从 container-family error 推进到下一 outer `ModelXPCRequest` 字段
2026-06-22 07:17:32 +0800 | 目标: 判断 `0x14` 后的 4-byte field 到底是不是 child count，还是 graph/node identity bookkeeping，并据此把 outer-tail 主问题从“扫 tag”收紧到“去冲突后的 graph closure” | 动作: 新增 `mps/ANE/experiments/modelmanager_taskcancellable_u14_outer_tail_probe.py`，固定 baseline body `mps/ANE/.ane_runs/body/modelmanager_taskcancellable_typemismatch_reply_body_20260622.bin`；先验证复用 baseline `body[3:]` 这条以第二个 `0x14` 开头的尾巴时，`u32=0/1/2` 会分别落到 `Duplicate reference to node #0/#1` 与 `Insufficient container`；再显式 author 双 `0x14` 结构，对 `u32a/u32b` 做可控碰撞测试，确认 `1/1 -> #1`、`2/2 -> #2`、`3/3 -> #3`、`4/4 -> #4`、`7/7 -> #7`，而 `u32a != u32b` 时回落到 `Dangling/Insufficient`；同时把 shared-cache 静态错误簇持久化到 `mps/ANE/.ane_runs/json/xpc_swiftoverlay_graph_error_cluster_verdict_20260622.json`，确认 `XPC_swiftoverlay` 中存在 `Missing container metadata` / `Container is at end.` / `Duplicate reference to node #` / `Dangling` / `Insufficient` 同一 graph family，但没有直接命名的 `node table` / `backreference` / `footer` 字符串 | 证据: `mps/ANE/.ane_runs/csv/modelmanager_taskcancellable_u14_outer_tail_probe_20260622.csv` 与 `mps/ANE/.ane_runs/json/modelmanager_taskcancellable_u14_outer_tail_probe_verdict_20260622.json` 已稳定重现 node-id 碰撞；静态字符串证据已落盘到 `mps/ANE/.ane_runs/json/xpc_swiftoverlay_graph_error_cluster_verdict_20260622.json` | 结论: 本轮 verdict=`confirmed`；`0x14` 后的 4-byte field 已被实证为 graph/node identity bookkeeping，而不是单纯 child count。当前 blocker 已从“找下一个 tag”收紧到“在 node id 去冲突后，补齐 forward metadata / graph closure 仍需的最小 family” | 下一步: 固定一个不 duplicate 的双 `0x14` 骨架（优先 `u32a=1,u32b=2`），最小化 author `.containerMetadata` / end-of-container / next-field 片段，目标是把错误从 `Dangling/Insufficient` 推进到新的 graph-closure 或下一 outer field family
2026-06-22 07:21:07 +0800 | 目标: 判断在 node id 已去冲突后，裸 `.containerMetadata` 是否就是当前 graph closure 唯一缺失项 | 动作: 把 4 组最小 metadata 变体并入 `mps/ANE/experiments/modelmanager_taskcancellable_u14_outer_tail_probe.py`：`0x14 + nil child + 13 0a`、再接最小 stringA、再接 `ipcError` string 片段、以及 `13 0a + 去冲突第二个 0x14(u32=2)`；重新生成 `mps/ANE/.ane_runs/csv/modelmanager_taskcancellable_u14_outer_tail_probe_20260622.csv` 与 `mps/ANE/.ane_runs/json/modelmanager_taskcancellable_u14_outer_tail_probe_verdict_20260622.json` | 证据: `meta_only -> Insufficient container`；`meta_stringA -> Insufficient`；`meta_ipcerror -> Insufficient`；`meta_dual14_2 -> Found dangling container in buffer` | 结论: 本轮 verdict=`confirmed`；裸 `.containerMetadata` 不是单独解法。即使 node id 已去冲突，graph 仍缺比 `13 0a` 更完整的 forward closure family | 下一步: 固定 `u32a=1,u32b=2` 的去冲突双 `0x14` 骨架，转向最小化 author end-of-container / next-field / keyed-vs-unkeyed closure 片段，而不是继续单独主攻 `.containerMetadata`
2026-06-22 07:34:06 +0800 | 目标: 判断在去冲突双 `0x14` 骨架下，closure 能否由“第二 node 的最小 `0x15` family”或“baseline tail 的某个结构前缀”直接给出 | 动作: 先把去冲突双 `0x14(u32a=1,u32b=2)` 下第二 node 的首 tag scan 并入 `mps/ANE/experiments/modelmanager_taskcancellable_u14_outer_tail_probe.py`，确认 `0x15` 是唯一仍保持结构合法的 family，而 `0x03/0x11/0x12/0x13/0x14/0x00/0x01/0x02/0x10` 会立刻分流到 string/object/metadata/duplicate-node 错误；随后把最小 `0x15` 片段（`15`、`15 13 0a`、`15 13 0a + stringA`、`15 13 0a + "_0"`、`15 13 0a + key10`）和 baseline tail 的所有结构性前缀截断（`1/3/4/12/21/26/29/30/38/41/42/50/154` 字节）都并入同一个 probe 并重跑；同时补充 `XPC_swiftoverlay` 静态 keyed/unkeyed 终止条件到 `mps/ANE/.ane_runs/json/xpc_swiftoverlay_graph_error_cluster_verdict_20260622.json` | 证据: `deconflicted_tag_15 -> Found dangling container`；`deconflicted_tag_03/11 -> Cannot read a valid string`；`deconflicted_tag_12 -> Bad index for XPC object: 135334419`；`deconflicted_tag_13 -> Found bad value for .containerMetadata: 19`；`deconflicted_tag_00/01/02/10 -> Duplicate reference to node #1`；而全部 `u15_*` 与 `tailcut_*` case 均稳定落回 `Found dangling container in buffer` | 结论: 本轮 verdict=`confirmed`；在去冲突双 `0x14` 骨架下，最小 `0x15` family 与 baseline tail 的任何结构前缀都不是缺失 closure 的直接答案。当前剩余问题只能是更深的 keyed-vs-unkeyed 终止条件 / next-field 结构，而不是继续裁现有 prefix | 下一步: 固定 `u32a=1,u32b=2`，直接 author 以 keyed termination（`Failed to find key` / `Found key, expected value`）或 unkeyed exhaustion（`Container is at end.`）为目标的最小 closure 片段，争取把错误从 `Dangling/Insufficient` 推进到这三个新 family 之一
2026-06-22 07:46:24 +0800 | 目标: 判断当前 `Dangling` 是否仍可能由“隐藏第三个 baseline 0x14 节点冲突”或“浅层 keyed parity / 语义 keyed skeleton 不完整”造成 | 动作: 继续扩展 `mps/ANE/experiments/modelmanager_taskcancellable_u14_outer_tail_probe.py`：1) 新增 third-u14 phase，显式 patch 去冲突双 `0x14` + `tag15 + baseline[9:]` 中隐藏第三个 baseline `0x14` 的 `u32c=0/1/2/3/4/7/20`；2) 新增 parity phase，在 `15 13 0a` 后分别 author 1/2/3 个最小字符串元素，试图命中静态 `expected odd number` / keyed validator；3) 新增 semantic-keyed phase，显式拼 `ipcError -> third 0x14 -> "_0"` 骨架，并分别测试 inner key 无 value、inner value 无 key、inner 最小 pair、outer key 无 value、outer value 无 key；随后重跑 probe 并更新 outer-tail verdict | 证据: 所有 `third_u14_u32c_*` case 无论 `u32c` 如何取值都稳定回到 `Found dangling container in buffer`；所有 `parity_*` case 也都只回到 `Found dangling container in buffer`，完全进不了 `expected odd number` / keyed-validator seam；所有 `semantic_*` case 同样都只回到 `Found dangling container in buffer`，即使结构已经刻意模仿 baseline 的 `ipcError -> third 0x14 -> "_0"` 形状 | 结论: 本轮 verdict=`confirmed`；当前 `Dangling` 不是由隐藏第三节点 id 冲突导致，也不是由浅层 parity 或显式 key-without-value / value-without-key 骨架就能解决的。剩余 closure 缺口比“最小 keyed skeleton”更深 | 下一步: 固定 `u32a=1,u32b=2`，直接 author 以 `Failed to find key` / `Found key, expected value` / `Container is at end.` 为目标的更深 keyed-vs-unkeyed 终止条件，而不是继续主攻 prefix、第三节点 id 或浅层 pair 结构
2026-06-22 08:12:08 +0800 | 目标: 判断 keyed/unkeyed closure 的真正内部 shape 是否已经能从 runtime image layout 直接收紧，而不是继续把 keyed 当成简单顺序 pair 流 | 动作: 先用 runtime introspection 解析 `XPC.TopLevelGraphEncodingNode`、`XPC._KeyedGraphEncodingNode`、`XPC.UnkeyedGraphEncodingNode`、`XPC.DecodedContainer` 的 `class_getImageName`、superclass、ivar list；确认它们实际来自 runtime image `/usr/lib/swift/libswiftXPC.dylib`，且分别暴露 `wrappedNode`、`keyToIndex + values`、`values`、`decodedValues`；同时补做一组 value-kind negative probe：把 semantic keyed skeleton 的 value 改成 `0x12` object-reference，并分别喂 `_CodableOutOfLine[0]=uint64` 与 `data(server body)`，结果仍只回到 `Found dangling container in buffer` | 证据: runtime 类布局已确认：`_KeyedGraphEncodingNode` 不是单纯顺序 pair，而是显式 `keyToIndex + values` 双结构；`UnkeyedGraphEncodingNode` 则只有 `values`；`DecodedContainer` 有 `decodedValues`。所有 `semantic_*_tag12` 变体仍未进入 `-Codable value` 或 keyed termination，只是 `Dangling` | 结论: 本轮 verdict=`confirmed`；当前 runtime / static 证据都指向：keyed path 更像 `keyToIndex + values` 双结构，而不是简单 triad/pair 流。继续把 keyed 当作浅层 key/value 骨架去 author 的边际收益已经很低 | 下一步: 固定 `u32a=1,u32b=2`，优先围绕 `keyToIndex + values` 与 `decodedValues` 这三个 runtime 结构名设计下一轮 probe 或静态分析入口，而不是继续重复 string pair / parity / out-of-line value-kind 的浅层尝试
2026-06-22 08:16:16 +0800 | 目标: 把 `libswiftXPC` runtime layout 发现从临时 shell 观察升级为可复跑 artifact，并验证它是否足以进一步压缩 keyed/unkeyed 方向 | 动作: 新增 `mps/ANE/experiments/xpc_swiftoverlay_runtime_layout_probe.py`，系统化记录 `XPC.TopLevelGraphEncodingNode`、`XPC._KeyedGraphEncodingNode`、`XPC.UnkeyedGraphEncodingNode`、`XPC.DecodedContainer` 的 runtime image path、superclass、instance size、ivar 列表，并输出到 `mps/ANE/.ane_runs/json/xpc_swiftoverlay_runtime_layout_verdict_20260622.json`；随后补做一组非常小的 `keyToIndex + values` 双子节点雏形 case（`key_node + val_node` / `val_node + key_node` / 双 key / 双 val`），结果仍只回到 `Found dangling container in buffer`，所以不再并入主 probe，避免 artifact 过胖 | 证据: 新 probe 明确落盘：runtime image 是 `/usr/lib/swift/libswiftXPC.dylib`；`TopLevelGraphEncodingNode -> wrappedNode`；`_KeyedGraphEncodingNode -> keyToIndex + values`；`UnkeyedGraphEncodingNode -> values`；`DecodedContainer -> decodedValues` | 结论: 本轮 verdict=`confirmed`；`keyed` 与 `unkeyed` 的内部 shape 已被收紧成 runtime 级可复跑事实。当前主线应该围绕 `keyToIndex + values` / `decodedValues` 继续设计，而不是再回到“顺序 key/value pair 流”的浅层模型 | 下一步: 固定 `u32a=1,u32b=2`，围绕 `keyToIndex + values` 与 `decodedValues` 这三个 runtime 结构名，继续找最可能映射到 bytes 的更深 closure seam
2026-06-22 08:26:25 +0800 | 目标: 判断 `libswiftXPC` 的 runtime 结构能否再给出比 ivar 名更具体的静态入口函数，从而把下一轮 probe 从“结构猜测”推进到“围绕真实 encode/decode 入口” | 动作: 先用 lldb 交互式 attach 到最小 helper 进程，成功在 `/usr/lib/swift/libswiftXPC.dylib` 中命中 `XPC.encodeToEncodingContainer<Encodable>(...) -> XPC.TopLevelGraphEncodingNode`、`XPC.decodeFromEncodingContainer<Decodable>(...)`，以及 `XPC._KeyedGraphEncodingNode._valueIndex(forKey: XPC.EncodingGraph.Key) -> Optional<Int>`；同时在 `DecodedContainer` 相关符号中命中 `Dictionary<UInt32, XPC.DecodedContainer>` specialization。把这些符号面补写回 `mps/ANE/.ane_runs/json/xpc_swiftoverlay_runtime_layout_verdict_20260622.json`；随后又补做了一组更贴近 `_valueIndex(forKey:)` 的 `key(super)` probe 和一组更像 `keyToIndex + values` 的双子节点雏形 probe，结果仍只回到 `Found dangling container in buffer` | 证据: lldb 符号面已明确；`_KeyedGraphEncodingNode._valueIndex(forKey: XPC.EncodingGraph.Key)` 是第一个直接暴露 key 语义的函数；`decodedValues` 对应 `Dictionary<UInt32, XPC.DecodedContainer>` specialization；但 `key(super)+node` / `key(super)+u64index` / `key_node+val_node` 这些更贴近结构名的最小 case 仍未推进到 keyed/unkeyed 终止 family | 结论: 本轮 verdict=`confirmed`；下一轮最值得围绕的不再只是 ivar 名，而是 `encodeToEncodingContainer` / `decodeFromEncodingContainer` / `_valueIndex(forKey:)` 这 3 个真实入口。当前主线继续收紧到“如何把 bytes 映射到 `keyToIndex + values` 与 `decodedValues`” | 下一步: 固定去冲突双 `0x14(u32a=1,u32b=2)` 骨架，优先围绕 `EncodingGraph.Key` 与 `UInt32 -> DecodedContainer` 字典语义，设计比现有 shallow keyed skeleton 更深一层的 closure probe
2026-06-22 08:55:27 +0800 | 目标: 验证公开 `XPCListener/XPCSession` loopback 是否足以直接产出合法 `libswiftXPC` `_CodableBody` 样本，并判断这些样本能否与 `modelmanager` reply tail 对齐 | 动作: 先从 `swift-api-digester` 确认 `XPCSession.send`、`XPCReceivedMessage.decode(as:)`、`XPCDictionary.withUnsafeUnderlyingDictionary(_:)` 都是公开 API；随后写出 `mps/ANE/experiments/xpc_swiftoverlay_loopback_probe.swift`，用 loopback listener/session 直接抓 `_CodableBody`。初版 probe 因对 auto-active listener/session 再次显式 `activate()` 而触发 `libxpc` API misuse；修正为不显式 activate，成功抓到 primitive/keyed/unkeyed/sample corpus，并总结到 `mps/ANE/.ane_runs/json/xpc_swiftoverlay_loopback_probe_verdict_20260622.json` 与 `mps/ANE/.ane_runs/json/xpc_swiftoverlay_loopback_summary_verdict_20260622.json`；随后补充 `ipc_error_string_dict`、`ipc_error_nested_dict`、`ipc_error_struct` 三个最像 `modelmanager` 的样本并完成对齐比较 | 证据: `ErrorEnvelope { ipcError: ErrorLeaf(_0: \"A\") }` 的合法 body 为 `130a1108000000000000006970634572726f7200140000000015130a1102000000000000005f30000301000000000000004100`；把 `modelmanager` reply tail 从 offset `9` 开始对齐后，只剩 4 个字节不同：inner `0x14` node id（`0x00` vs `0x01`）与最终字符串的长度/内容（`\"A\"` vs `DecodingError...`） | 结论: 本轮 verdict=`confirmed`；field2 尾巴已经不再是未知 grammar，而是高度接近合法 public `ipcError -> _0 -> string` payload。当前长期主线已从“广义 closure 语法恢复”重新压缩回“field1 + 最外层额外 `0x15` wrapper + inner node-id / final string payload 差异” | 下一步: 以合法 `ipc_error_struct` / `ipc_error_nested_dict` 样本为模板，直接回到 `modelmanager` 主线，把 probe 重点放在 field1 与最外层 wrapper 对齐，而不是继续宽泛猜测 field2 closure
2026-06-22 09:05:05 +0800 | 目标: 验证合法 public task-like envelope 能否进一步把 `modelmanager` 主线从“field1 + wrapper”收紧到“field1 的具体合法 tag 与最外层 wrapper 差异” | 动作: 新增 `mps/ANE/experiments/xpc_swiftoverlay_taskshape_probe.swift`，用同一个公开 loopback harness 直接编码两类手工 unkeyed 形状：`CancelLike(id: 20)` 与 `MessageLike(id: 20, payload: ErrorEnvelope, flag: Bool)`；结果落到 `mps/ANE/.ane_runs/json/xpc_swiftoverlay_taskshape_probe_verdict_20260622.json`，并额外总结到 `mps/ANE/.ane_runs/json/xpc_swiftoverlay_taskshape_summary_verdict_20260622.json` | 证据: `CancelLike(id: 20) -> 130b0f1400000000000000`；`MessageLike(id: 20, payload: ErrorEnvelope, flag: false) -> 130b0f1400000000000000140000000002...`；`MessageLike(..., true) -> 130b0f1400000000000000140000000001...`。这说明 task-like unkeyed envelope 中合法 `UInt64` 首字段 tag 是 `0x0f`，而 `modelmanager` 现在的 `130b021400000000...` 更像是“本该是 `0x0f` 的合法 task-like prefix 被 `0x02(bool false)` 顶掉” | 结论: 本轮 verdict=`confirmed`；当前主线已从“field1 + wrapper”进一步收紧到“field1 的 `0x02` vs 合法 task-like `0x0f` 首字段 tag + 最外层 `0x15` wrapper + inner node-id 差异” | 下一步: 直接以合法 `CancelLike(20)` / `MessageLike(20, ..., false)` 作为新模板，回到 `modelmanager` 主线做定向对齐 probe，验证只改 field1 tag 与最外层 wrapper 是否就能复现或推进当前 body
2026-06-22 09:14:06 +0800 | 目标: 验证 `modelmanager` baseline 是否已经能用合法 public task-like 模板直接推进，而不是继续把 field1 与 field2 混在一起猜 | 动作: 新增 `mps/ANE/experiments/modelmanager_taskshape_alignment_probe.py`，把 3 个合法 public control（`cancel_20`、`message_20_false`、`message_20_true`）和 4 个最小对齐 case（`baseline_tag0f_only`、`baseline_prefix_cancel20`、`baseline_prefix_msgfalse17`、`baseline_prefix_msgfalse_full`）统一喂给 `modelmanager_xpc_codable_probe`；结果落到 `mps/ANE/.ane_runs/csv/modelmanager_taskshape_alignment_probe_20260622.csv` 与 `mps/ANE/.ane_runs/json/modelmanager_taskshape_alignment_probe_verdict_20260622.json` | 证据: 合法 `message_20_false/true` 都能推进到 `expected ModelXPCRequest ... Invalid number of keys found, expected one.`；只把 baseline field1 tag 从 `0x02` 改成 `0x0f`，或把前 11 字节替成合法 `cancel_20` prefix，都能把错误从 `expected UInt64, found bool(false)` 推进到 `Found dangling container in buffer`；但如果把更长的 public prefix 整段替进去，则会 overshoot 到 `Cannot read a valid tag from buffer` | 结论: 本轮 verdict=`confirmed`；field1 tag/wrapper 已被证明是当前第一 blocker，field2 尾巴则已经足够合法到能把错误推进到 payload 解码层。主线因此不再是“广义 closure 恢复”，而是“围绕 baseline 的 `0x02` vs 合法 `0x0f` 做最小 field1/wrapper 对齐” | 下一步: 继续用合法 `CancelLike(20)` / `MessageLike(20, ..., false)` 作为模板，只围绕 field1 与最外层 wrapper 做更小的定向 probe，争取把 `Found dangling container` 再推进到比 wrapper 更靠后的新 family
2026-06-22 09:39:14 +0800 | 目标: 判断 `ModelXPCRequest.createSession` 路径是否已经能从“顶层 key 猜测”推进到字段级恢复，并尽量恢复 `CreateSessionRequest.metadata` 的字段顺序与类型 | 动作: 基于公开 task-like envelope 和已确认的 `createSession` 顶层 key，临时生成一组 `createSession` payload 变体并直接喂给 `modelmanager_xpc_codable_probe`：先验证单-key `createSession` + `_0` associated-value wrapper 是否正确；再对 `metadata` 依次补字段，比较 `String` vs `URL`、`Int` vs `Int32` 的效果；最后继续把字段推进到 `loggingIdentifier` 与 `id`，并把结果汇总到 `mps/ANE/.ane_runs/json/modelmanager_create_session_payload_verdict_20260622.json` | 证据: `createSession` 顶层 key 正确；缺 `_0` 时直接报 `CreateSessionCodingKeys(\"_0\") not found`；有 `_0` 后，`metadata` 是必需的 keyed 字段；`assetBundleURI` 不接受 plain String，但接受 URL-like 值并推进到缺 `useCaseID`；随后依次推进出 `onBehalfOfPID`、`parentOfOnBehalfOfPID`、`loggingIdentifier`、`id` 的顺序；其中 `onBehalfOfPID` 期待 `Int32`，`parentOfOnBehalfOfPID` 期待 `Int`，`id` 期待 UUID string | 结论: 本轮 verdict=`confirmed`；`createSession` 路径已从“case 名猜测”推进到字段级恢复。当前已恢复出的 `Session.Metadata` 字段顺序与类型提示为：`assetBundleURI(URL-like) -> useCaseID(String-like) -> onBehalfOfPID(Int32) -> parentOfOnBehalfOfPID(Int) -> loggingIdentifier(String-like) -> id(UUID string)` | 下一步: 沿这条已打通的 `createSession` 主线继续补 `sessionSetID` 与 `alreadyLockedInferenceProvider`，同时保留 field1 `0x02 -> 0x0f` 主线；不再回到广义 field2 closure 猜测
2026-06-22 09:50:10 +0800 | 目标: 继续沿 `createSession` 主线恢复剩余字段，优先判 `sessionSetID` 的类型和 `alreadyLockedInferenceProvider` 的 optional 行为，再看下一步缺口是否仍在 metadata 内部 | 动作: 先生成 `id=UUID` 但缺 `sessionSetID` 的 case，确认它会直接报 `sessionSetID` 缺失；随后生成 `sessionSetID=\"sid\"` 与 `sessionSetID=<UUID>` 两个 case，前者触发 `Attempted to decode UUID from invalid UUID string.`，后者不再报 provider，而是推进到缺 `inferenceInterfaceVersion`；再对 `inferenceInterfaceVersion` 做 `Int` / `Int32` / `String` 三种最小候选，三者都稳定报 `Found singleValueGraphEncodingNodeID ... unable to recover from encoded value`；结果已回填到 `mps/ANE/.ane_runs/json/modelmanager_create_session_payload_verdict_20260622.json` | 证据: `sessionSetID` 必填且类型为 UUID string；`alreadyLockedInferenceProvider` 在 metadata 未完整前不会先报错；`inferenceInterfaceVersion` 不是 plain `Int` / `Int32` / `String` 标量 | 结论: 本轮 verdict=`confirmed`；`createSession` 主线已从“顶层 key + wrapper”推进到 `metadata.inferenceInterfaceVersion` 这一更深字段。当前优先级应从 `sessionSetID/provider` 进一步收缩为：先恢复 `inferenceInterfaceVersion` 的非标量 shape，再判断 `alreadyLockedInferenceProvider` 是否真正 optional | 下一步: 固定现有已恢复的 `metadata` 前缀，专门围绕 `inferenceInterfaceVersion` 的 shape 做更窄的定向 probe；`alreadyLockedInferenceProvider` 暂列第二优先级
2026-06-22 06:20:44 +0800 | 目标: 判断 field1 的 `0x12` 是否是一个可行的 out-of-line 备用编码路径，而不是继续把它当死 tag | 动作: 先修复 `modelmanager_xpc_codable_probe` 的 out-of-line 注入实现（确认 `xpc_array_set_value/set_uint64` 在 fresh array 上会本地 trap，改为 `xpc_array_append_value` + typed object）；随后对 field1 `tag 0x12 + index 0` 依次测试 `_CodableOutOfLine` 的 `uint64(7)`、`Data`(0/1/2/4/8/16 zero bytes)、`Data`(8-byte little-endian 7)、以及 replay 的 129/162/247-byte server body；同时验证 `_CodableOutOfLine4CodableObject` 不命中；最后新增 `mps/ANE/.ane_runs/json/modelmanager_outofline_data_path_verdict_20260622.json` | 证据: `tag 0x12` baseline 为 `Bad index for XPC object: 0`；填入 `_CodableOutOfLine[0] = uint64(7)` 后变成 `XPC object does not represent valid Data`；改成 `_CodableOutOfLine[0] = xpc_data(...)` 后，无论 data 长度和内容如何都稳定推进成 `Found dangling container in buffer`；`_CodableOutOfLine4CodableObject` 仍无效 | 结论: 本轮 verdict=`confirmed`；`0x12` 是一条真实的 out-of-line `Data blob` 分支，但它目前只把 decode 推到 nested-container 层，尚不足以替代 direct `UInt64` 主线 | 下一步: 回到 field1 direct `UInt64` 编码恢复，把 `0x12 -> out-of-line Data` 仅作为 secondary branch 记录
2026-06-22 10:34:56 +0800 | 目标: 把 `createSession.metadata.inferenceInterfaceVersion` 从“非标量”进一步恢复成可验证的具体 wire-shape | 动作: 新增 `mps/ANE/experiments/xpc_swiftoverlay_create_session_version_probe.swift` 与 `mps/ANE/experiments/modelmanager_create_session_version_probe.py`，用 public `XPCListener/XPCSession` loopback 生成合法 task-like `createSession` bodies，再回放给 `modelmanager_xpc_codable_probe`；对照测试标量 `Int(1)`、二字段 `{major,minor}`、三字段 `{major,minor,patch}` | 证据: `ModelManagerServices.tbd` 明确暴露 `Version.init(major: UInt32, minor: UInt32, patch: UInt32)` 与 `Session.Metadata.inferenceInterfaceVersion : Version`；结果文件为 `mps/ANE/.ane_runs/json/modelmanager_create_session_version_probe_verdict_20260622.json` / `mps/ANE/.ane_runs/csv/modelmanager_create_session_version_probe_20260622.csv`；其中标量 `Int(1)` 稳定报 `singleValueGraphEncodingNodeID`，二字段 `{major,minor}` 稳定报 `Key 'patch' not found`，三字段 `{major,minor,patch}` 稳定推进到 `assetBundleNotFound` | 结论: 本轮 verdict=`confirmed`；`inferenceInterfaceVersion` 已不再是泛化“非标量”未知量，而是明确的 `ModelManagerServices.Version{major,minor,patch}` | 下一步: 固定三字段 `Version` 形状，把主问题前移到 `assetBundleURI` 的更高层 semantic 表示
2026-06-22 10:34:56 +0800 | 目标: 判断 raw `file://` 指向本机现存 UAF 目录是否足以充当 `assetBundleURI`，从而把 `createSession` 推过当前 `assetBundleNotFound` gate | 动作: 新增 `mps/ANE/experiments/xpc_swiftoverlay_create_session_asset_bundle_probe.swift` 与 `mps/ANE/experiments/modelmanager_create_session_asset_bundle_probe.py`；动态发现本机候选并逐个回放：`Translation_Assets/*.asset`、`*.asset/AssetData`、`Siri_UnderstandingNLOverrides/*.asset`、`Siri_PlatformAssets/*.asset`、`Siri_PlatformAssets/*.asset/AssetData`、`Siri_PlatformAssets/*.asset/AssetData/<version>`、`~/Library/Assistant/LLMCache/NLRouter`，以及 dummy `/tmp` 控制项 | 证据: 结果文件为 `mps/ANE/.ane_runs/json/modelmanager_create_session_asset_bundle_probe_verdict_20260622.json` / `mps/ANE/.ane_runs/csv/modelmanager_create_session_asset_bundle_probe_20260622.csv`；所有现存 UAF 目录候选与 NLRouter 候选都稳定回到同一个 `assetBundleNotFound`，没有任何一个推进到 `useCaseID` / `customAssetConfigurations` / `alreadyLockedInferenceProvider` | 结论: 本轮 verdict=`falsified`；当前失败点不是“路径不存在”或“随便一个现成 UAF 目录都行”，而是 raw `file://` 到本机现存 `.asset` / `AssetData` / `NLRouter` family 整体不足以满足 `assetBundleURI` | 下一步: 放弃继续穷举 raw on-disk 目录；转向更高层 `AssetBundleSpecification` / secure-mobile-asset family 表示，优先确认 `assetBundleURI` 的真实上层 carrier
2026-06-22 11:02:00 +0800 | 目标: 判断 manager-facing `LoadAssetBundle` / `HoldAssetBundle` 是否接受 UAF history 给出的 `assetSpecifier` / `assetID` 作为合法 `assetBundleIdentifier`，从而为 `createSession` 主线找到上游 bundle surface | 动作: 先用 SDK `tbd` 与 `ModelManagerServices.i64` 确认 `HoldAssetBundle(assetBundleIdentifier: String)`、`LoadAssetBundle(assetBundleIdentifier: String, dynamicMode: Bool)` 的存在及字段；随后新增 `mps/ANE/experiments/xpc_swiftoverlay_asset_bundle_identifier_probe.swift` 与 `mps/ANE/experiments/modelmanager_asset_bundle_identifier_probe.py`，用 public `XPCListener/XPCSession` loopback 生成合法 task-like `hold/load` bodies，并把 dummy string、UAF `assetSpecifier`、UAF `assetID` hash、`localContentURL` path string 逐个回放给 `modelmanager_xpc_codable_probe` | 证据: `mps/ANE/.ane_runs/json/modelmanager_asset_bundle_identifier_probe_verdict_20260622.json` 与 `mps/ANE/.ane_runs/csv/modelmanager_asset_bundle_identifier_probe_20260622.csv` 显示所有 tested identifier family 都稳定回同一个 reply：`notSupportedOnExternalBuild`；`ModelManagerServices.i64` 同时确认 `assetBundleIdentifier` 与 `assetBundleURI` 不在同一 request struct 中，前者属于 `HoldAssetBundle/LoadAssetBundle`，后者仍是另一个上层 `Foundation.URL` field | 结论: 本轮 verdict=`confirmed`；manager-facing string identifier surface 已被统一 external-build gate 拦住，identifier 语义尚未开始判定。`createSession` 当前走到的 `assetBundleNotFound` 因此更像是另一条更高层 path，而不是 `load/hold asset bundle` 这层 string surface | 下一步: 不再穷举 `assetBundleIdentifier`；直接定位真正持有 `assetBundleURI` 的上层 Swift carrier，并判断 `createSession` 的 `assetBundleNotFound` 是否来自这条未被 external-build gate 直接截断的更高层 path
2026-06-22 11:18:00 +0800 | 目标: 补强 `createSession.assetBundleURI` 的 file-root 证伪范围，避免因为之前只试了 Translation / Siri 平台类目录而误留“也许真实 locked 资产根可以过”的假口子 | 动作: 扩展 `mps/ANE/experiments/modelmanager_create_session_asset_bundle_probe.py`，新增从 `~/Library/UnifiedAssetFramework/history` 动态抽取 `localContentURL` 的逻辑，把 `SummarizationKitConfiguration`、`Siri_Understanding`、`Siri_UnderstandingNLOverrides` 的真实 locked 资产根并入现有 createSession asset-bundle probe，再次回放给 `modelmanager_xpc_codable_probe` | 证据: 重跑后的 `mps/ANE/.ane_runs/json/modelmanager_create_session_asset_bundle_probe_verdict_20260622.json` 与对应 CSV 显示，新增的 `history_summarizationkit_*`、`history_siri_understanding_*`、`history_siri_understanding_nl_*` case 仍然全部稳定回同一个 `assetBundleNotFound`，没有任何一个推进到 `useCaseID` / `customAssetConfigurations` / `alreadyLockedInferenceProvider` | 结论: 本轮 verdict=`confirmed`；“raw `file://` 指向本机现存 UAF asset roots” 这条 family 现在已被更强地证伪，连真实 locked 的 history `localContentURL` 根也不例外 | 下一步: 不再继续穷举任何 file-root 资产目录；直接把 effort 转到 `assetBundleURI` 的上层 carrier / 非 raw-file 表示
2026-06-22 11:27:00 +0800 | 目标: 对齐 IDA 返回与 SDK `tbd` 的冲突，避免把 `assetBundleURI` 错贴到 `LoadAssetBundle` / `HoldAssetBundle` 本体上 | 动作: 针对同一个 `ModelManagerServices.i64` session 追加一次最小 reconciliation，只问 7 字段 `assetBundleURI` field-cluster 是否真能被强证据证明属于 `LoadAssetBundle` / `LoadAssetBundle.Response` | 证据: SDK `tbd` 的强事实仍是 `HoldAssetBundle(assetBundleIdentifier: String)` 与 `LoadAssetBundle(assetBundleIdentifier: String, dynamicMode: Bool)`；追加 IDA 结论确认我上一轮看到的 7 字段 cluster 不能被强证据挂到这两个 request，本质上更像相邻的内部 session/descriptor/assertion 类型；冲突点在于 field metadata 相邻性不足以替代 FieldDescriptor offset 链验证 | 结论: 本轮 verdict=`confirmed`；当前可安全确认的是 `load/hold` 的 wire surface 只吃 string identifier，`assetBundleURI` 必须继续在别的上层 Swift carrier 中寻找 | 下一步: 直接定位真正拥有 `assetBundleURI` 的上层 Swift carrier，不再回头怀疑 `LoadAssetBundle` / `HoldAssetBundle` 的 wire-format
2026-06-22 11:46:00 +0800 | 目标: 把 `createSession.assetBundleURI` 的 raw file family 真正判死到 file-level，而不只停在目录层级 | 动作: 先用本机目录扫描确认 `SummarizationKitConfiguration`、`Siri_Understanding`、`Siri_UnderstandingNLOverrides`、`Translation_Assets` 中不存在任何嵌套 `.bundle/.framework/Contents/Info.plist/Resources` package；随后扩展 `mps/ANE/experiments/modelmanager_create_session_asset_bundle_probe.py`，把 current live asset 的 file-level 入口候选并入：`.asset/Info.plist`、`AssetData/metadata.plist`、`AssetData/Configuration.plist`、`AssetData/version.yaml`、`AssetData/SummarizationOverrideRules.pbtxt`、`AssetData/regex.jsonl`、`AssetData/config.json`，并重跑 createSession probe | 证据: `mps/ANE/.ane_runs/csv/modelmanager_create_session_asset_bundle_probe_20260622.csv` 现已包含 `translation_info_plist`、`siri_nl_info_plist`、`siri_nl_metadata_plist`、`siri_platform_info_plist`、`summarization_info_plist`、`summarization_SummarizationOverrideRules_pbtxt`、`siri_understanding_info_plist` 等 case，这些 file-level 候选全部仍稳定回 `assetBundleNotFound`；对应 verdict 仍是 `mps/ANE/.ane_runs/json/modelmanager_create_session_asset_bundle_probe_verdict_20260622.json` | 结论: 本轮 verdict=`confirmed`；`assetBundleURI` 的 raw `file://` family 现在不只是目录层级被证伪，连 current live asset 的 file-level metadata/config 入口也全部无效。下一步应不再继续猜文件路径，而是转向 `requiredAssetIDs` / `prewarmSession` / `fetchInstance` / 上层 Swift carrier 这些更上游语义面 | 下一步: 不再继续穷举任何 file-root / file-level URL；直接调查 `requiredAssetIDs`、`prewarmSession`、`fetchInstance` 与 `assetBundleURI` 上层 carrier 的关系
2026-06-22 12:02:00 +0800 | 目标: 判断 `PrewarmSession` 这条更上游 path 当前首先撞到的是 wire gate、external-build gate，还是更深的 session/internal gate | 动作: 先用 `tbd` 压缩出 `ModelXPCRequest.PrewarmSession` 的最小签名（`sessionID: UUIDIdentifier<Session>` + `metadata: [String:String]?`），随后新增 `mps/ANE/experiments/xpc_swiftoverlay_prewarm_session_probe.swift` 与 `mps/ANE/experiments/modelmanager_prewarm_session_probe.py`，用 public loopback 生成合法 task-like prewarm bodies，再分别回放 `metadata=nil`、`metadata={}`、`metadata={\"probe\":\"1\"}` 和 `bad UUID + metadata={}` 四组 case | 证据: `mps/ANE/.ane_runs/json/modelmanager_prewarm_session_probe_verdict_20260622.json` 与 CSV 显示：`metadata=nil` 稳定报 `DecodingError.keyNotFound ... metadata`；`sessionID=\"sid\"` + `metadata={}` 稳定报 `Attempted to decode UUID from invalid UUID string`；而合法 UUID + `metadata={}` / `{\"probe\":\"1\"}` 已不再报 decode，而是都稳定推进到 `internalError` | 结论: 本轮 verdict=`confirmed`；`PrewarmSession` 当前已经越过了 UUID / metadata wire-shape gate，并且不像 `LoadAssetBundle` / `HoldAssetBundle` 那样先撞 `notSupportedOnExternalBuild`。它更像是进入了更深的 session/internal-state gate | 下一步: 把 `PrewarmSession` 视为“上游语义面可达”的旁证，继续追 `requiredAssetIDs` / `FetchAssetsRequest` / `createSession.assetBundleNotFound` 三者之间的关系
2026-06-22 12:18:00 +0800 | 目标: 判断 `FetchAssetsRequest` 是否是一个比 `createSession` 更低门槛的 asset/catalog state 观察入口 | 动作: 先用 `tbd` 点查确认 `FetchAssetsRequest` 至少暴露了 `Response(assetInfo: [AssetInfo])`，但 request 字段本身未在符号层直接露出；随后新增 `mps/ANE/experiments/xpc_swiftoverlay_fetch_assets_probe.swift` 与 `mps/ANE/experiments/modelmanager_fetch_assets_probe.py`，构造最小空 `fetchAssets` request 并直接回放给 `modelmanager` | 证据: `mps/ANE/.ane_runs/json/modelmanager_fetch_assets_probe_verdict_20260622.json` 与对应 CSV 显示，这条 request 当前不会先报 decode，也不会走 `assetBundleNotFound`，而是稳定返回 `missingEntitlement` | 结论: 本轮 verdict=`confirmed`；`FetchAssetsRequest` 不是当前机器上可直接用来观察 catalog state 的低门槛入口，它先撞 entitlement gate。到此为止，上游 gate topology 已更清晰：`load/hold -> notSupportedOnExternalBuild`，`prewarm -> internalError`，`fetchAssets -> missingEntitlement`，而 `createSession(assetBundleURI=...)` 仍独特地走到 `assetBundleNotFound` | 下一步: 继续专注于 `createSession` 这条仍可达 asset gate 的 path，并结合 `PrewarmSession` 已越过 wire gate 的事实，追 `assetBundleURI` 的上层 carrier 与 asset-ID/catalog state 关系
2026-06-22 12:33:00 +0800 | 目标: 把 `useCaseID` 与 secure-mobile-asset file path 两条剩余假设从 `createSession -> assetBundleNotFound` 主线里进一步压掉 | 动作: 新增 `mps/ANE/experiments/xpc_swiftoverlay_create_session_usecase_probe.swift` 与 `mps/ANE/experiments/modelmanager_create_session_usecase_probe.py`，固定 current live `.asset` 根，只改变 `useCaseID`；测试真实 `UsageAliasName` 候选（`siri.TextSummarization`、`summarization.summarizeMailMessage`、`summarization.notesAudioTranscript`、`com.apple.siri.assistant.language`、`com.apple.siri.nl.system.language`、`siri.ActionValidator`、`translation.system.text.ondevice`、`translation.translateapp.text.ondevice`）；同时扩展 `mps/ANE/experiments/modelmanager_create_session_asset_bundle_probe.py`，加入 secure-mobile-asset file path family：`purpose_auto/*.xml`、`SecureAssetData/`、`SecureMobileAsset-Info.plist`、`BuildManifest.plist` | 证据: `mps/ANE/.ane_runs/json/modelmanager_create_session_usecase_probe_verdict_20260622.json` 与 CSV 显示所有真实 `UsageAliasName` case 仍统一回 `assetBundleNotFound`；扩展后的 `mps/ANE/.ane_runs/csv/modelmanager_create_session_asset_bundle_probe_20260622.csv` 进一步显示 `translation_manifest_xml`、`summarization_manifest_xml`、`siri_nl_manifest_xml`、`siri_understanding_manifest_xml`、`siri_understanding_secure_data`、`siri_understanding_secure_info_plist`、`siri_understanding_secure_build_manifest` 也全部仍是 `assetBundleNotFound` | 结论: 本轮 verdict=`confirmed`；当前 `createSession -> assetBundleNotFound` 已经对 raw `.asset` 根、`AssetData`、file-level metadata/config、secure-mobile-asset file path family、以及真实 `useCaseID` 候选都不敏感。剩余最高价值假设是更高层 carrier 或 asset-ID/catalog state，而不是路径/用例值 | 下一步: 不再继续穷举任何路径或 useCase 值；继续追 `requiredAssetIDs` / `PrewarmSession` / `FetchAssetsRequest` 与 `createSession` 分叉的根因
2026-06-22 12:52:00 +0800 | 目标: 验证 use-case 查询面本身是否可达，避免在 `useCaseID` 假设已压掉后又从另一条查询 request 侧回流 | 动作: 依据 `tbd` 中的零字段 `FetchDisabledUseCasesRequest` 轮廓，新增 `mps/ANE/experiments/xpc_swiftoverlay_fetch_disabled_usecases_probe.swift` 与 `mps/ANE/experiments/modelmanager_fetch_disabled_usecases_probe.py`，构造最小空 request 并直接回放给 `modelmanager` | 证据: `mps/ANE/.ane_runs/json/modelmanager_fetch_disabled_usecases_probe_verdict_20260622.json` 与对应 CSV 显示，这条 request 当前稳定返回 `missingEntitlement`，没有进入 use-case 数据层 | 结论: 本轮 verdict=`confirmed`；`FetchDisabledUseCasesRequest` 与 `FetchAssetsRequest` 一样属于 entitlement-gated 查询面，不能作为当前机器上的低门槛 use-case 观察入口 | 下一步: 继续专注于 `createSession(assetBundleURI=...)` 与 `PrewarmSession` 这两条当前仍能推进到更深 gate 的 path，不再投入到 use-case 查询面
2026-06-22 13:08:00 +0800 | 目标: 判断 `FetchModelInstance` 是不是另一个可达的 session-scoped 上游入口，而不是像 `FetchAssetsRequest` 一样先撞 entitlement gate | 动作: 先从 `tbd` 确认 enum case 名字就是 `fetchModelInstance(FetchModelInstance)`，随后新增 `mps/ANE/experiments/xpc_swiftoverlay_fetch_model_instance_probe.swift` 与 `mps/ANE/experiments/modelmanager_fetch_model_instance_probe.py`；先试空 request，发现直接缺 `sessionID`，再补 `bad UUID` / `good UUID` 两组最小对照并重跑 | 证据: `mps/ANE/.ane_runs/json/modelmanager_fetch_model_instance_probe_verdict_20260622.json` 与对应 CSV 显示：空 request 缺 `sessionID`；`sessionID=\"sid\"` 稳定报 `Attempted to decode UUID from invalid UUID string`；合法 UUID string 则不再报 decode，而是稳定进入 `internalError` | 结论: 本轮 verdict=`confirmed`；`FetchModelInstance` 与 `PrewarmSession` 一样已经越过了 UUID/wire gate，当前卡在更深的 session/internal gate，而不是 entitlement/build gate | 下一步: 把 `FetchModelInstance` 和 `PrewarmSession` 统一当作 session-scoped reachable path 的旁证，继续解释为何 `createSession` 独特地停在 `assetBundleNotFound` 而不是直接进入相同 internal gate
2026-06-22 13:25:00 +0800 | 目标: 判断 failed `createSession(assetBundleNotFound)` 是否会留下可观察的部分 session state，从而改变同 UUID 的 downstream session request 行为 | 动作: 新增 `mps/ANE/experiments/xpc_swiftoverlay_failed_create_session_state_probe.swift` 与 `mps/ANE/experiments/modelmanager_failed_create_session_state_probe.py`，用 fresh UUID 生成同一组 `createSession` / `PrewarmSession` / `FetchModelInstance` bodies；顺序执行 `prewarm_before -> fetch_before -> create_session -> prewarm_after -> fetch_after` 并比较前后信号 | 证据: `mps/ANE/.ane_runs/json/modelmanager_failed_create_session_state_probe_verdict_20260622.json` 与对应 CSV 显示：`prewarm_before=internalError`、`fetch_before=internalError`、`create_session=assetBundleNotFound`、`prewarm_after=internalError`、`fetch_after=internalError`，前后没有任何变化 | 结论: 本轮 verdict=`confirmed`；当前 failed `createSession` 不会留下可观察的 session state，至少不会让 `PrewarmSession` / `FetchModelInstance` 的行为改变。这把主问题继续压回 asset gate 之前缺少的 carrier / catalog state，而不是 downstream session 方法 | 下一步: 不再把 failed `createSession` 当作部分 session 已落地的 path；继续专注于 asset gate 之前缺失的更高层 carrier / asset-ID / catalog state
2026-06-22 13:39:00 +0800 | 目标: 再压掉 `createSession -> assetBundleNotFound` 上一个剩余的直接输入假设：`customAssetConfigurations` 省略与显式空数组是否会改变 asset gate | 动作: 新增 `mps/ANE/experiments/xpc_swiftoverlay_create_session_custom_assets_probe.swift` 与 `mps/ANE/experiments/modelmanager_create_session_custom_assets_probe.py`，固定 summarization current live `.asset` 根与 `siri.TextSummarization`，只切换 `customAssetConfigurations` 为缺省 vs 空数组 | 证据: `mps/ANE/.ane_runs/json/modelmanager_create_session_custom_assets_probe_verdict_20260622.json` 与对应 CSV 显示，两种 case 都稳定回到同一个 `assetBundleNotFound`，没有任何更深或不同的 gate | 结论: 本轮 verdict=`confirmed`；`customAssetConfigurations` 的缺省/空数组差异不足以解释当前 `assetBundleNotFound`。到这一步，路径、useCase、secure path、file-level metadata/config、以及 customAssetConfigurations 的表层输入都已被压掉 | 下一步: 不再继续改造这些表层输入；继续追更高层 carrier 或 asset-ID / Model Catalog state
2026-06-22 13:50:00 +0800 | 目标: 判断能否直接绕过 raw XPC，通过高层 `ModelManagerServices.Session` Swift symbol 直连来构造合法 session / carrier | 动作: 不改仓库，只做两次临时编译实验；先用 `swift-demangle` 确认 `Session.__allocating_init(supportedAssetBundleIdentifiers:...)` 的完整 mangled 名，再分别用 `@_silgen_name` + `xcrun swiftc -F /System/Library/PrivateFrameworks -framework ModelManagerServices` 与 `-F /Applications/Xcode.app/.../MacOSX.sdk/System/Library/PrivateFrameworks -framework ModelManagerServices` 尝试直接链接 `Session.__allocating_init(supportedAssetBundleIdentifiers: [String], useCaseID: String, onBehalfOfPID: Int, loggingIdentifier: String)` | 证据: 两次实验都能过前端，但链接阶段都稳定报同一个 unresolved symbol：`__$s20ModelManagerServices7SessionC31supportedAssetBundleIdentifiers9useCaseID13onBehalfOfPID17loggingIdentifierACSaySSG_SSSiSStcfC`；也就是说不仅宿主 framework 不可直接链接，连 SDK `tbd` 路径也不能把这条高层 Swift constructor 变成可用 client surface | 结论: 本轮 verdict=`confirmed`；“直接 import / 直调高层 Session Swift API” 当前整体不可用，至少不是现成可走的入口。主线仍应优先留在 raw XPC 与更高层 carrier / asset-ID / catalog state 恢复上 | 下一步: 不再回头尝试高层 Swift 直连；直接转向 `ModelCatalog` SDK 接口与更高层 carrier/catalog state 恢复
2026-06-22 14:02:00 +0800 | 目标: 把 `assetBundleNotFound` 的更高层语义从“路径/metadata 猜测”继续压缩到明确的 catalog 身份链 | 动作: 用 `searcher` 子代理窄查 Xcode SDK 的 `ModelCatalog.tbd`，只围绕 `ResourceBundleIdentifier`、`LocalClient.resourceBundle(for:)`、`ModelErrors.AssetError.failedToFindAsset`、`AssetBackedLLMBundle` / `LLMBundle` 这些符号收证 | 证据: `ModelCatalog.ResourceBundleIdentifier<T>` 是带 `id: String` 的泛型 Codable/Hashable/ExpressibleByStringLiteral 标识符；`LocalClient` 提供同步 `throws` 的 `resourceBundle(for:)` / `resourceBundles()` / `resourceStatus()` / `resourceInformation()`；`ModelErrors.AssetError.failedToFindAsset` 与当前已知 `assetBundleNotFound` 对齐；`AssetBackedLLMBundle` / `LLMBundle` 都以内嵌 `id: ResourceBundleIdentifier<...>` 作为核心身份字段 | 结论: 本轮 verdict=`confirmed`；当前 `assetBundleNotFound` 最像缺少更高层 `ResourceBundleIdentifier` / catalog identity，而不是 URL 路径形状本身。下一步要验证的是：这些 `ModelCatalog` client 接口在宿主上是否也是 SDK-only，不是现成可用 runtime surface | 下一步: 只做一个小验证，判断 `ModelCatalog` / `LocalService` 是否在当前宿主上存在可直接用的 runtime/client surface；若没有，就继续把主线留在 raw XPC 与 carrier-state 恢复上
2026-06-22 14:12:00 +0800 | 目标: 判断 `ModelCatalog` 是否只是 SDK 语义来源，还是当前宿主上已有可直接用的 client/runtime surface | 动作: 先用 `searcher` 子代理窄查 `ModelCatalog.tbd`，确认 `ResourceBundleIdentifier<T>`、`LocalClient.resourceBundle(for:)`、`ModelErrors.AssetError.failedToFindAsset`、`AssetBackedLLMBundle` / `LLMBundle` 等接口；随后本地核对宿主 `/System/Library/PrivateFrameworks/ModelCatalog.framework` 的目录结构，并确认其仅有 `Resources` 与签名、无独立 module/binary 文件 | 证据: `ModelCatalog.tbd` 明确给出完整 bundle-identity 链：`ResourceBundleIdentifier.id: String`、`LocalClient.resourceBundle(for:)`、`ModelErrors.AssetError.failedToFindAsset`；但宿主 framework 当前仅见 `Resources/Info.plist`、`Resources/version.plist`、`_CodeSignature`，没有可直接 import 的 module 文件或独立 binary 文件。结合此前 `ModelManagerServices` 高层 Swift constructor 链接失败，当前没有现成证据表明 `ModelCatalog` / `LocalClient` 是宿主上可直接拿来调用的入口 | 结论: 本轮 verdict=`confirmed`；`ModelCatalog` 目前应视为 SDK 语义来源，而不是已证明可直接调用的宿主 client surface。主线仍应留在 raw XPC 与 carrier/catalog-state 恢复上 | 下一步: 不再回头尝试宿主高层 catalog/client 直连；继续专注于解释 `createSession` 独特可达的 `assetBundleNotFound` 与更高层 asset-ID/catalog state 的关系
2026-06-22 14:26:00 +0800 | 目标: 验证 `assetBundleURI` 是否接受简单的非-`file://` identity URL，而不是继续只在 raw path 家族里打转 | 动作: 新增 `mps/ANE/experiments/xpc_swiftoverlay_create_session_identity_uri_probe.swift` 与 `mps/ANE/experiments/modelmanager_create_session_identity_uri_probe.py`；固定 `createSession` 其他字段，只把 `assetBundleURI` 切成多组简单 identity URL：`modelcatalog://...`、`resourcebundle://...`、`uaf://...`，并覆盖当前最相关的真实 `AssetSpecifier` 值（`com.apple.summarizationkit.ota.configuration` / `.rules`、`com.apple.siri.understanding.uaf.metadata`、`com.apple.siri.nl.nlv4.zh_CN`、`com.apple.siri.nl.cati.zh_CN`、`com.apple.siri.asr.assistant.zh_CN`、`com.apple.sequoia.asset.config`、`com.apple.sequoia.asset.lid`） | 证据: `mps/ANE/.ane_runs/json/modelmanager_create_session_identity_uri_probe_verdict_20260622.json` 与对应 CSV 显示：所有简单 identity URL 候选都不再返回 `assetBundleNotFound`，而是统一稳定进入 `modelCatalogError` | 结论: 本轮 verdict=`confirmed`；当前已经证实 `assetBundleURI` 存在一个不同于 raw file path 的 identity/catalog code path，而且它比 `assetBundleNotFound` 更深一层。下一步应不再改表层字段值，而是直接围绕 `modelCatalogError` 这条新 seam 收窄 URL 形状或 identity carrier | 下一步: 固定最相关的 identity 体系（优先 `modelcatalog://<AssetSpecifier>`），判断 `modelCatalogError` 是否对 URL 形状本身敏感，或是否已经说明真正缺失的是更高层 catalog/client state
2026-06-22 14:26:00 +0800 | 目标: 验证 `assetBundleURI` 是否接受简单的非-`file://` identity URL，而不是继续只在 raw path 家族里打转 | 动作: 新增 `mps/ANE/experiments/xpc_swiftoverlay_create_session_identity_uri_probe.swift` 与 `mps/ANE/experiments/modelmanager_create_session_identity_uri_probe.py`；固定 `createSession` 其他字段，只把 `assetBundleURI` 切成多组简单 identity URL：`modelcatalog://...`、`resourcebundle://...`、`uaf://...`，并覆盖当前最相关的真实 `AssetSpecifier` 值（`com.apple.summarizationkit.ota.configuration` / `.rules`、`com.apple.siri.understanding.uaf.metadata`、`com.apple.siri.nl.nlv4.zh_CN`、`com.apple.siri.nl.cati.zh_CN`、`com.apple.siri.asr.assistant.zh_CN`、`com.apple.sequoia.asset.config`、`com.apple.sequoia.asset.lid`） | 证据: `mps/ANE/.ane_runs/json/modelmanager_create_session_identity_uri_probe_verdict_20260622.json` 与对应 CSV 显示：简单 identity URL 已把 signal 从 `assetBundleNotFound` 推进到 `modelCatalogError` | 结论: 本轮 verdict=`confirmed`；当前已经证实 `assetBundleURI` 存在一个不同于 raw file path 的 identity/catalog code path，而且它比 `assetBundleNotFound` 更深一层 | 下一步: 固定 identity 体系，继续测试 `modelCatalogError` 是否对 URL 形状敏感
2026-06-22 14:39:00 +0800 | 目标: 判断 `modelCatalogError` 是 identity 值问题还是 `modelcatalog:` URL 形状问题 | 动作: 新增 `mps/ANE/experiments/xpc_swiftoverlay_create_session_modelcatalog_shape_probe.swift` 与 `mps/ANE/experiments/modelmanager_create_session_modelcatalog_shape_probe.py`，固定同一个 `AssetSpecifier`=`com.apple.summarizationkit.ota.configuration`，分别测试 `modelcatalog://<id>`、`modelcatalog:///<id>`、`modelcatalog:<id>`、`modelcatalog://bundle/<id>`、`modelcatalog://resource/<id>`、`modelcatalog://bundle?id=<id>` 六种形状 | 证据: `mps/ANE/.ane_runs/json/modelmanager_create_session_modelcatalog_shape_probe_verdict_20260622.json` 与对应 CSV 显示：`host_form` 与 `id_query_form` 稳定返回 `modelCatalogError`；而 `path_form`、`opaque_form`、`bundle_path_form`、`resource_path_form` 全部回退到 `assetBundleNotFound` | 结论: 本轮 verdict=`confirmed`；当前 `modelCatalogError` 已被实证为对 `modelcatalog:` URL 形状敏感。也就是说，authority/query 这类形状确实进入了更深的 catalog code path，而 path/opaque 形状没有 | 下一步: 不再改更多普通字段；固定 authority/query 这两类能进入 `modelCatalogError` 的形状，继续测试是否还缺少 version/configuration 等更高层 identity 信息
2026-06-22 14:52:00 +0800 | 目标: 判断 `modelCatalogError` 这条更深的 createSession path 是否会比 `assetBundleNotFound` 更晚失败，从而留下可观察的部分 session state | 动作: 新增 `mps/ANE/experiments/xpc_swiftoverlay_failed_modelcatalog_create_session_state_probe.swift` 与 `mps/ANE/experiments/modelmanager_failed_modelcatalog_create_session_state_probe.py`，用 fresh UUID 顺序执行 `prewarm_before -> fetch_before -> create_session(modelcatalog://com.apple.summarizationkit.ota.configuration) -> prewarm_after -> fetch_after` 并比较前后信号 | 证据: `mps/ANE/.ane_runs/json/modelmanager_failed_modelcatalog_create_session_state_probe_verdict_20260622.json` 与对应 CSV 显示：`prewarm_before=internalError`、`fetch_before=internalError`、`create_session=modelCatalogError`、`prewarm_after=internalError`、`fetch_after=internalError`，前后完全不变 | 结论: 本轮 verdict=`confirmed`；`modelCatalogError` 路径和 `assetBundleNotFound` 路径一样，当前都不会留下可观察的 session state。这把主问题继续压回 session materialize 之前的更高层 carrier / asset-ID / catalog state | 下一步: 不再把 failed createSession 的任一路径当作部分 session 已落地的 path；继续收窄进入 `modelCatalogError` 的 identity 形状与更高层 catalog/client state
2026-06-22 14:46:00 +0800 | 目标: 判断 `ModelCatalog.CatalogErrors.QueryError Code=2` 是否只是一个对 query key / empty value / empty query-name 敏感的晚段分支，还是更早的共用 URI 组件分支 | 动作: 先用 `reverse-engineer` sub-agent 收窄 `QueryError`/`AssetError`/`ResourceBundleQuery` 的静态表面，再用 `ida` sub-agent确认 `modelmanagerd` 的 `queryResourceBundle(with:)` / `resource(for:)` imports 与 `QueryError` case 家族；随后新增 `mps/ANE/experiments/modelmanager_create_session_modelcatalog_component_probe.py`，复用现有 `xpc_swiftoverlay_create_session_identity_uri_probe.swift` 与 `modelmanager_xpc_codable_probe`，对 `host_only`、`bundle?id=`、`empty_host_query`、`empty_id_value`、`empty_query_name`、`fragment_suffix`、`userinfo_bundle`、`port_bundle` 8 个组件级 `modelcatalog:` URL 逐一生成合法 `createSession` body，重放后再抓 `modelmanagerd` 原始日志 | 证据: `mps/ANE/.ane_runs/csv/modelmanager_create_session_modelcatalog_component_probe_20260622.csv` 与 `mps/ANE/.ane_runs/json/modelmanager_create_session_modelcatalog_component_probe_verdict_20260622.json` 显示 8 个 case 全部稳定回到 top-level `modelCatalogError`；对应日志逐条都是 `Failed to get resource bundle for ... Error Domain=ModelCatalog.CatalogErrors.QueryError Code=2 "(null)"`，包括 `modelcatalog://?id=...`、`modelcatalog://bundle?id=&empty=1`、`modelcatalog://bundle?=...`、`...#fragment`、`user@bundle`、`bundle:443` 等 edge case | 结论: 本轮 verdict=`falsified`；`Code=2` 不是一个会被 query key / empty value / empty query-name / fragment / userinfo / port 扰动的晚段分支，当前更像一个早段共用 QueryError 分支。这把下一步正式压成二选一：`invalidURIString` vs `invalidURIComponents`，或 `createSession` 高层 carrier 额外做了统一映射 | 下一步: 不再继续穷举 query key、host/path、fragment、userinfo、port 这些表层 `modelcatalog:` 成分；优先找更直接的 ModelCatalog client seam，或构造一个会改变 Foundation URL component decomposition 的更小 URL probe，用来分开 `invalidURIString` 与 `invalidURIComponents`
2026-06-22 16:08:00 +0800 | 目标: 把 `modelCatalogError` 的不确定性再向下压一层，确认 `Code=2` 的真实 case，同时验证是否存在可直打的 non-XPC ModelCatalog seam | 动作: 先用 `ida` 子代理把 `QueryError` 的 string<->ordinal 编解码与 `errorDescription` 钉死，确认 `Code=2` 的 case；再新增 `mps/ANE/experiments/modelcatalog_direct_bundle_query_uri_probe.swift` 与 `.../modelcatalog_direct_bundle_query_uri_probe.py`，用 `@_silgen_name` 直调 `CatalogIndex.resolveResourceBundleQueryURI(uri:)` 和 `VariantHelpers.isResourceBundleQueryURIResolved(uri:)`，对 authority / non-authority / file URL 做 direct parse matrix；随后再新增 `mps/ANE/experiments/modelcatalog_resource_bundle_container_runtime_probe.m` 与 `.../modelcatalog_resource_bundle_container_runtime_probe.py`，用 Objective-C runtime 检查 `ModelCatalog.ResourceBundleContainer` 是否真的在宿主上注册了静态分析里看到的 selector | 证据: 1) IDA 明确给出 `0 -> invalidURI`, `1 -> invalidURIComponents`, `2 -> invalidURIString`, `3 -> invalidArgument`, `4 -> invalidQueryItem`，因此 `Error Domain=ModelCatalog.CatalogErrors.QueryError Code=2` 已可硬解释为 `invalidURIString`；2) `mps/ANE/.ane_runs/csv/modelcatalog_direct_bundle_query_uri_probe_20260622.csv` 与 `...verdict_20260622.json` 显示 direct seam 可运行且会区分 URL decomposition：`modelcatalog://bundle?id=... -> extractedBundleID=\"\"`，而 `modelcatalog:bundle?id=...` / `modelcatalog:/bundle?id=...` / `modelcatalog:///bundle?id=... -> extractedBundleID=\"bundle\"`，`file:///tmp/test.asset -> extractedBundleID=\"test.asset\"`；3) `mps/ANE/.ane_runs/csv/modelcatalog_resource_bundle_container_runtime_probe_20260622.csv` 与 `...verdict_20260622.json` 显示 `ModelCatalog.ResourceBundleContainer` 类虽然存在，但对 `resourceBundleContainerWithIdentifier:with:` / `resourceBundleContainersWith:` / `supportedArgumentsFor:with:` 的 `class_respondsToSelector` 和 `instanceResponds...` 全为 0，宿主 runtime 上只剩 `NSSecureCoding` / `init` / `description` 这些基础 method list | 结论: 本轮先后完成了两个相连的短期目标：1) `Code=2` 已正式从“可能的 parser 分支”收窄成 **`invalidURIString`**；2) direct non-XPC `ModelCatalog` seam 已打通，且证明 `createSession` 上层确实把更丰富的 URL 解析结果压扁了；与此同时，`ResourceBundleContainer` 这个看似更低的 ObjC bridge 在宿主 runtime 上是 dead end，当前不能直接靠 `objc_msgSend` 往下走 | 下一步: 不再继续猜 `QueryError` case，也不再尝试宿主侧直接调 `ResourceBundleContainer`；下一轮应专注于 **consumer 侧 Swift URL->identifier decomposition**，定位是谁在 `createSession` 上游把 authority / non-authority / file-style URL 的 richer parse 结果统一折叠成当前 `invalidURIString`
2026-06-22 16:54:00 +0800 | 目标: 在 consumer 侧继续往前追，确认 `queryResourceBundle(with:)` 的唯一上游 seam、它与 `useCaseID` / `assetBundleURI` 的真实关系，并判断当前用户态是否能动态 attach live `_modelmanagerd` 读出构造时刻的 URL | 动作: 先从 `/usr/libexec/modelmanagerd` 切出 arm64e thin slice `mps/ANE/.ane_runs/tmp/modelmanagerd_arm64e_20260622`，再用 `ida` 子代理对 thin-slice 反编译 `sub_10010CA70` 与 createSession continuation `sub_100177FA4`，继续追 `self.vtable[0x10]` 的 URL 构造分发；同时用最小 capability probe 分别尝试 `lldb` 和 `frida` attach live pid 528，不下断点、不改状态，只确认当前用户态是否能附加 | 证据: 1) thin-slice 反编译已确认 `sub_10010CA70` 是 `ModelCatalogProvider` 的 vtable[9] 方法，是 modelmanagerd 中唯一调用 `ModelCatalog.ClientProtocol.queryResourceBundle(with: URL)` 的 consumer seam；2) `sub_100177FA4` 先调用 `sub_10010CA70`，成功返回后才重新读取 `CreateSessionRequest.metadata.useCaseID`，因此 `useCaseID` 不参与 URL 构造；3) `sub_10010CA70` 本身不从函数参数接收 URL，而是通过 `self.vtable[0x10]` 调度一个 `ModelCatalogProviding` 协议方法，从 self 内部状态派生 URL；4) `mps/ANE/.ane_runs/json/modelmanagerd_user_attach_capability_verdict_20260622.json` 记录了当前用户态的动态 attach 结果：`lldb` 失败于用户不匹配（`baicai1145` vs `_modelmanagerd`），`frida` 也失败于无法访问该 pid | 结论: 本轮完成了两个连续的短期目标：1) 已把 consumer 侧唯一 seam 从“某个 modelmanagerd 高层 path”收窄成 **`ModelCatalogProvider.vtable[9] -> sub_10010CA70`**；2) 已确认 live `_modelmanagerd` 的 LLDB/Frida 动态附加在当前用户态不可行，因此“直接读 X9/URL 寄存器”不是当前回合能推进的路径。结合 `useCaseID` 只在返回后参与后续 session 标记这一事实，当前最值得追的就是 `assetBundleURI` 或其派生状态是如何在 `ModelCatalogProvider` / `ModelCatalogProviding` self 上被注入的 | 下一步: 不再继续尝试当前用户态 attach `_modelmanagerd`，也不再围绕 `useCaseID` 兜圈；下一轮应继续静态追 **`ModelCatalogProvider` 的对象构造与 `ModelCatalogProviding` 的具体实现者**，把 `CreateSessionRequest.metadata.assetBundleURI` 注入 self 状态的那一层找出来
2026-06-22 17:24:00 +0800 | 目标: 把 consumer 侧对象构造链再向前压一层，确认 `ModelCatalogProvider` / `DaemonSession.modelCatalog` 的构造位置，以及 `assetBundleURI` 究竟在 `queryResourceBundle(with:)` 之前的哪一步进入状态 | 动作: 继续用 `ida` 子代理对 arm64e thin-slice 深挖 `sub_10010CA70`、`sub_100177FA4` 和 `addSession(metadata:auditToken:alreadyLockedInferenceProvider:isUnentitled:)`，确认 `sub_10010CA70` 的具体实现者、`ModelCatalogProvider` 的 vtable 与字段、`DaemonSession.modelCatalog` 的存储点；同时用 `reverse-engineer` 子代理补充 `DaemonContext` / `UseCaseManager` / `DaemonSession` 的 `modelCatalog` 字段分布与对象图；主线程再把本轮关键静态链整理成 `mps/ANE/.ane_runs/json/modelmanagerd_modelcatalog_provider_seam_verdict_20260622.json` | 证据: 1) `ida` 已确认 `sub_10010CA70` 通过 `ModelCatalog.ModelClientProtocol.queryResourceBundle(with:)` 的协议扩展 thunk 调用 `ModelCatalog.ModelClient`，而不是再次走 `ModelCatalogProviding`；2) `addSession(...)` 中会分配 `DaemonSession`，创建/装箱 `ModelCatalogProvider`，并把它存入 `DaemonSession.modelCatalog`（ObjC ivar offset 指针 `0x1001da9b0`）；3) `sub_100177EC4` / `sub_100177FA4` 路径已能静态确认 `CreateSessionRequest.metadata.getter -> Session.Metadata.assetBundleURI.getter -> sub_10010CA70 -> queryResourceBundle(with:)` 这条链，而 `useCaseID` 只在返回后参与 session 标记；4) `reverse-engineer` 还确认 `DaemonContext(+72)`, `UseCaseManager(+112)`, `PolicyManager(+240)`, `RemoteManager(+112)`, `DaemonSession(+112)` 都持有 `modelCatalog` 字段，提示 provider 可能有多条构造/持有路径 | 结论: 本轮完成了一个新的短期目标：已把 `assetBundleURI` 进入 consumer state 的链条收窄成 **`CreateSessionRequest.metadata.assetBundleURI.getter -> addSession(...) 构造的 DaemonSession.modelCatalog -> ModelCatalogProvider.vtable[9]`**。同时也确认了一个重要边界：`sub_10010CA70` 之后就已经进入 `ModelCatalog.ModelClientProtocol.queryResourceBundle(with:)`，所以想改变 lookup key，最干净的侵入点不在 query 调用之后，而在 `assetBundleURI` getter 或 provider/self 注入之前 | 下一步: 不再继续讨论 `queryResourceBundle` 的实现者，也不再把 `useCaseID` 当 URL 构造输入；下一轮应专注于 **`addSession(...)` / `DaemonSession` / `DaemonContext` / `UseCaseManager` 谁负责把 `assetBundleURI` 注入 provider/self 状态**，优先判断这些 `modelCatalog` 持有者是共享同一实例还是各自构造
2026-06-22 17:47:00 +0800 | 目标: 判定 `DaemonContext` / `UseCaseManager` / `DaemonSession` / `PolicyManager` / `RemoteManager` 的 `modelCatalog` 是共享一个 `ModelCatalogProvider` 实例，还是各自构造，从而继续缩窄 `assetBundleURI` 的注入层 | 动作: 用 `ida` 子代理机械追 5 个 `modelCatalog` 字段的写入点与来源分类（直接新建 vs 传递已有 existential），再用更窄的补问解决一个关键矛盾：`sub_10010CA70` 的 URL 到底是显式参数还是 provider/self 状态；主线程把两部分结果整理成 `mps/ANE/.ane_runs/json/modelmanagerd_modelcatalog_instance_topology_verdict_20260622.json` | 证据: 1) 5 个 `modelCatalog` 持有者的写入来源全部归到同一条 `ModelCatalogProvider` 分配/传递链，没有发现第二条独立 `alloc` 路；2) `sub_10010CA70` 的 ABI 形参布局已确认 URL 是 **per-call 显式参数**，而不是从共享 provider 的持久字段中取出；3) createSession call site 明确是 `Session.Metadata.assetBundleURI.getter()` 的局部结果被传给 `sub_10010CA70`，而 `useCaseID` 继续只在 lookup 返回后才参与 bookkeeping | 结论: 本轮完成了一个新的短期目标：`modelCatalog` 持有者是**共享单实例**，但 lookup URL 不是 provider 的长生命周期状态，而是 **由 request metadata 派生的 per-call argument**。这正式削弱了“往 provider 字段里找 `assetBundleURI` 注入”的路线，也把下一步从“找哪个字段存了 URL”改成了“找哪个 helper/dispatcher 把 `assetBundleURI` 变成本地 URL buffer” | 下一步: 不再继续问 `modelCatalog` 是不是共享实例，也不再把 provider 当成 URL 状态容器；下一轮应专注于 **`CreateSessionRequest.metadata.assetBundleURI.getter()` 之后、`sub_10010CA70` 之前** 的本地 URL buffer 构造 helper，判断 `addSession(...)` 还是更早的 dispatcher 是最窄的 patch/hook 点
2026-06-22 18:08:00 +0800 | 目标: 判定 createSession 路径上 `assetBundleURI.getter()` 之后是否还存在一个更深的共享 URL rewrite helper，还是局部结果会直接传进 `sub_10010CA70` | 动作: 用 `ida` 子代理把 `sub_10010CA70` 的 ABI 形参布局和 5 个 call site 再压窄一层，只回答 URL 是来自局部 buffer 还是 provider/self 状态；主线程把结论整理成 `mps/ANE/.ane_runs/json/modelmanagerd_create_session_url_handoff_verdict_20260622.json` 并回写长期文档 | 证据: 1) `ida` 已确认 `sub_10010CA70` 入口 `X0` 就是 URL buffer 指针；2) createSession call site (`sub_100177FA4`) 传入的 `X0` 直接来自 `Session.Metadata.assetBundleURI.getter()` 写入的局部栈 buffer；3) LoadAssetBundle 并行路径则是 `assetBundleIdentifier.getter() -> URL.init(string:) -> sub_10010CA70`，两条路径在 lookup seam 汇合，但 createSession 路径上当前没有发现比 getter 更深的一层共享 URL rewrite helper | 结论: 本轮完成了一个新的短期目标：createSession 路径上的 URL handoff 已收敛成 **`assetBundleURI.getter()` 局部结果 -> 本地 URL buffer -> `sub_10010CA70`**，不存在更深的共享 rewrite helper。因而最窄的 createSession-specific patch/hook 点就是 `Session.Metadata.assetBundleURI.getter()` 或其直接 callsite；如果希望同时覆盖 LoadAssetBundle，则应转向共用的 `sub_10010CA70` seam | 下一步: 不再继续追 getter 之后是否还有隐藏 helper；下一轮应直接比较两类 patch/hook 点的战略价值：**createSession-specific 的 `assetBundleURI` getter/callsite** vs **createSession+LoadAssetBundle 共用的 `sub_10010CA70` seam**，并判断哪一个更符合当前 private ANE 主线目标
2026-06-22 18:31:00 +0800 | 目标: 在已经确认 URL 是 per-call argument、且 getter 后面无更深共享 rewrite helper 的前提下，比较两个候选 patch/hook 点的战略价值：createSession-specific 的 `assetBundleURI` getter/callsite vs createSession+LoadAssetBundle 共用的 `sub_10010CA70` | 动作: 用 `doc-reader` 汇总现有证据，确认 createSession 是当前唯一仍能推进到更深 gate 的 live path、而 LoadAssetBundle / HoldAssetBundle 的 manager-facing string surface 被 `notSupportedOnExternalBuild` 提前封死；再用 `ida` 子代理机械统计两个候选点的 caller 覆盖范围、路径类型和副作用半径；主线程把结论整理成 `mps/ANE/.ane_runs/json/modelmanagerd_patchpoint_tradeoff_verdict_20260622.json` | 证据: 1) `assetBundleURI.getter` 被 6 个 caller 读取，但不覆盖显式 `LoadAssetBundle` handler 与 `RemoteManager/provider` 路径；2) `sub_10010CA70` 被 5 个 code caller 共享覆盖，包含 createSession 下游共享解析、显式 LoadAssetBundle handler、RemoteManager/provider 解析，是 asset bundle -> ModelCatalog -> resource bundle 的唯一共享瓶颈解析点；3) 虽然 `LoadAssetBundle` manager-facing string surface 被 `notSupportedOnExternalBuild` 提前挡住，但 `sub_10010CA70` 仍是所有真正进入 bundle lookup 的路径所共享的 seam；4) getter/callsite 更窄、更低副作用，但本质只是 createSession-local 的 URL 来源点，而不是真正的 lookup bottleneck | 结论: 本轮完成了一个新的短期目标：当前 private ANE 主线优先的 patch/hook 点应明确选 **`sub_10010CA70`**，而不是 createSession-specific 的 getter/callsite。后者只适合作为 createSession 局部触发与观察点；前者才是覆盖 createSession / LoadAssetBundle / RemoteManager-provider 解析的共享 lookup seam，也是最接近真正 lower control layer 解析瓶颈的点 | 下一步: 不再继续争论 getter/callsite 与 `sub_10010CA70` 谁更优；下一轮应在 **`sub_10010CA70` 内部** 继续选更窄的 sub-hook / patch site，重点比较：入口 URL rewrite、`ModelClientProtocol.queryResourceBundle(with:)` dispatch、以及 post-query `ResourceBundle.rawID` 处理 三者中哪个最适合当前 private ANE 主线
2026-06-22 18:55:00 +0800 | 目标: 在已选中的 `sub_10010CA70` 共享 lookup seam 内，再向下选出当前最实际的 sub-hook / patch site，并验证用户态 `CatalogClient` harness 是否已经可直接起步 | 动作: 先用 `ida` 子代理对 `sub_10010CA70` 内部三个候选点做静态 tradeoff：A=入口 URL rewrite，B=`0x10010CE3C` 的 `ModelClientProtocol.queryResourceBundle(with:)` dispatch，C=post-query `ResourceBundle.rawID` 处理；随后主线程补做一个最小用户态构造探针 `mps/ANE/experiments/modelcatalog_catalogclient_ctor_probe.py`，分别测试 `CatalogClient` type metadata accessor、`cfc` ctor、`cfC` ctor 的可调性，并把结果落到 `mps/ANE/.ane_runs/json/modelcatalog_catalogclient_ctor_probe_verdict_20260622.json` | 证据: 1) 静态对比显示 A 虽然最早但输入是 `ModelCatalogAsset` 而不是 URL，本地结构布局不透明；C 只覆盖成功路径，最多适合 fallback/override；B（`0x10010CE3C`）则是函数内第一个真正的外部调用边界，100% 覆盖成功/失败/fallback 路径，且参数/返回边界最清晰、改动半径最小；2) `CatalogClient` harness probe 进一步确认：type metadata accessor 可直接调用，说明符号解析与链接没问题；但在当前 `@_silgen_name` + `AnyObject` 假设下，无论 `cfC` 还是 `cfc` ctor 都会 crash，这把问题收窄成 **构造 ABI 未恢复**，而不是整个用户态入口不存在 | 结论: 本轮完成了两个连续的短期目标：1) `sub_10010CA70` 内部最优的下钻点已明确是 **`0x10010CE3C` 的 `ModelClientProtocol.queryResourceBundle(with:)` dispatch**；2) 这条 dispatch 点目前还不能直接通过一个朴素的用户态 `CatalogClient` harness 跑通，瓶颈集中在 ctor ABI 恢复，而不是符号/链接层。当前最稳的判断是：把 `0x10010CE3C` 当作优先的 patch/hook 目标，同时把 `CatalogClient` 正确构造 ABI 恢复作为并行可选方向 | 下一步: 不再继续比较 A/B/C 三个子点；下一轮应直接回答一个更窄的问题：**是继续恢复 `CatalogClient` 正确 ctor/call ABI，让用户态 harness 跑通 `0x10010CE3C`；还是接受它当前只能作为静态 patch/injection 目标，并转去恢复该点的最小二进制 patch 方案**。两者选其一并推进到可验证实验
2026-06-22 19:11:00 +0800 | 目标: 基于 `CatalogClient` ctor probe 的 crash 结果，判断用户态 harness 路线是不是已经走死，或者是否还存在 connection-based 的替代构造入口 | 动作: 主线程先用一手 `ModelCatalog.tbd` + `swift-demangle` 核对 `CatalogClient` / `LocalCatalogClient` / `InitializableFromExistingConnection` / `BidirectionalXPCServiceClientConnection` 的导出符号；确认 `CatalogClient` 默认 ctor 之外，`ModelCatalog` 自身还导出了 `InitializableFromExistingConnection.init(existingConnection:localObject:)` 和 `BidirectionalXPCServiceClientConnection.__allocating_init(localObject:delegate:)` 及其 `existingConnection:` 变体；再把这组候选入口补写进 `docs/ane_next.md` / `docs/ane_state.md` 作为下一轮 ABI 恢复方向 | 证据: 1) `ModelCatalog.tbd` 明确包含 `_$s12ModelCatalog35InitializableFromExistingConnectionP08existingF011localObjectxSo15NSXPCConnectionC_7Service_9InterfaceQZtKcfCTj/Tq`；2) 还包含 `_$s12ModelCatalog39BidirectionalXPCServiceClientConnectionC11localObject8delegate...` 和 `...existingConnection...delegate...` 的 allocating init；3) 这说明当前问题不是“根本没有用户态入口”，而是**默认 `CatalogClient` ctor ABI 未恢复**，同时还存在 connection-based 的替代构造路线可试 | 结论: 本轮在完成 `0x10010CE3C` 这个最优静态 sub-hook 点选择后，又把“继续恢复用户态 harness 还是彻底转向纯 patch”这个二选一问题往前推进了一步：用户态 harness 方向尚未判死，因为除了会 crash 的默认 ctor 之外，`ModelCatalog` 还暴露了 connection-based 初始化协议与 client connection 构造器。当前真正未知的是这些入口的 ABI 与所需 `NSXPCConnection` / `Interface` / `delegate` 组合是否可在用户态满足 | 下一步: 不再只围绕 `CatalogClient.init()` 的 `cfC/cfc` 入口打转；下一轮应专注于 **connection-based 的 `InitializableFromExistingConnection` / `BidirectionalXPCServiceClientConnection` 路线**，判断它们是否比默认 ctor 更接近一个可跑通的用户态 `queryResourceBundle` harness，若仍不可行，再正式收敛到纯 patch/injection 方案
2026-06-22 14:55:00 +0800 | 目标: 判断宿主 `ModelCatalog` runtime 是否至少通过 ObjC bridge 暴露了可直接用的资源查询入口 | 动作: 不改仓库，只做最小 runtime introspection；先确认宿主 `/System/Library/PrivateFrameworks/ModelCatalog.framework/ModelCatalog` 可 `dlopen`，再用 `objc_getClass` / `class_copyMethodList` 检查 `MCResourceInformation`、`MCResourceStatus` 及若干可能的 bridge 类 | 证据: `MCResourceInformation` 与 `MCResourceStatus` 可从 runtime 拿到，但实例/类方法只有 `init` / `initWithCoder:` / `encodeWithCoder:` / `supportsSecureCoding` 这类 `NSSecureCoding` bridge 方法；未发现任何可直接执行 resource 查询或 bundle lookup 的方法；`ResourceContainer` / `ResourceBundleContainer` / `SafetyFailureWrapper` / `GuardrailResultWrapper` 在宿主 runtime 中也不可见 | 结论: 本轮 verdict=`confirmed`；宿主 `ModelCatalog` runtime 虽然存在，但当前可见的 ObjC bridge surface 只是被动的数据容器，不是可直接拿来打 catalog query 的入口 | 下一步: 不再继续在 ObjC bridge surface 上找直接查询 API；继续围绕 `modelCatalogError` 的 raw XPC seam 收窄真正缺失的 catalog/client state
2026-06-22 14:43:00 +0800 | 目标: 判断 `modelCatalogError` 是不是只差更高层的 ModelCatalog resource ID（`com.apple.fm.*` / `com.apple.gm.*`）或更复杂的 multi-ID bundle membership | 动作: 新增 `mps/ANE/experiments/modelmanager_create_session_modelcatalog_resource_id_probe.py` 与 `mps/ANE/experiments/modelmanager_create_session_modelcatalog_multid_probe.py`，分别测试 `com.apple.fm.language.instruct_3b.summarization.generic`、`.draft.generic`、`.base.generic`、`.tokenizer.generic`、`com.apple.gm.overrides.model_config.all.generic`、`com.apple.gm.safety.disabledusecases.generic` 等高层 resource ID，以及 `base + summarization + draft + tokenizer + safety` 的 multi-ID 组合 | 证据: `mps/ANE/.ane_runs/json/modelmanager_create_session_modelcatalog_resource_id_probe_verdict_20260622.json` 与 `...modelcatalog_multid_probe_verdict_20260622.json` 显示，单个高层 resource ID 与多 ID 组合都仍统一落在 `modelCatalogError`，没有任何一个更进一步 | 结论: 本轮 verdict=`confirmed`；当前 catalog seam 已经不是“选错了更高层 model ID”或“少了几个 resource member”这么浅的问题 | 下一步: 不再继续穷举更高层 ID 与简单 bundle membership；转而判断 `modelCatalogError` 是否至少对 query key / shape 之外的更深 catalog state 敏感
2026-06-22 14:48:00 +0800 | 目标: 判断 `modelCatalogError` 更像 query key parser 错，还是更深的 catalog lookup/state gate | 动作: 新增 `mps/ANE/experiments/modelmanager_create_session_modelcatalog_querykey_probe.py`，固定 `modelcatalog://bundle?...` 形状，只切换 query key：`id=`、`assetSpecifier=`、`resourceBundleIdentifier=`、`identifier=`、`bogus=`、空 query | 证据: `mps/ANE/.ane_runs/json/modelmanager_create_session_modelcatalog_querykey_probe_verdict_20260622.json` 与对应 CSV 显示，上述所有 query-key 变体全部统一落在同一个 `modelCatalogError`，没有任何分叉 | 结论: 本轮 verdict=`inconclusive`；`Code=2` 至少不是一个显而易见的浅层 query-key parser 错，当前更像更深的 catalog gate。主线应继续把它当作 deeper catalog/client-state seam，而不是继续穷举 query key 名 | 下一步: 若继续走 modelcatalog 路线，应优先寻找更深的 catalog/client state，而不是再改普通 query key
2026-06-22 15:10:00 +0800 | 目标: 验证 `ModelCatalog` 是否存在一个比 `LocalClient` 更容易直连的高层入口，从而绕开 raw XPC 继续推进 catalog identity 主线 | 动作: 从 `ModelCatalog.tbd` 中提取最简单的 constructor：`ModelCatalog.Index.__allocating_init(sideloadURL: URL)`，然后做一次不落盘的临时编译/链接实验，用 `@_silgen_name` + SDK `tbd` 直接尝试构造 `ModelCatalog.Index` 对象 | 证据: 编译能过前端，但链接阶段稳定报 unresolved symbol：`__$s12ModelCatalog0B5IndexC11sideloadURLAC10Foundation0E0V_tcfC`；说明即便是 `ModelCatalog.Index(sideloadURL:)` 这种最简单的高层 constructor，也不能直接通过 SDK `tbd` 变成可调用的宿主 client surface | 结论: 本轮 verdict=`confirmed`；高层 `ModelCatalog` Swift 直连整体仍不可用，不只是 `LocalClient` 难用。当前主线继续锁定在 raw XPC 与更深的 catalog/client state 恢复上 | 下一步: 不再回头尝试高层 `ModelCatalog` Swift constructors；继续围绕 `modelCatalogError` 的 raw XPC seam 和内部 case 语义推进
2026-06-22 19:41:00 +0800 | 目标: 判断当前主线是否还应继续把主要精力压在用户态 `ModelCatalog` harness 上，还是正式把它降级为次级方向，并回到 `0x10010CE3C` 的静态 patch/injection 目标 | 动作: 先用 `reverse-engineer` 子代理把 `ModelCatalog` 中与 `InitializableFromExistingConnection` / `BidirectionalXPCServiceClientConnection` / `XPCService` 相关的 export surface 彻底收集一遍，确认 connection-based 路线在当前可见 surface 内是否已有 concrete conformer；再用 `ida` 子代理恢复 `CatalogClient` 的 concrete ctor 链，确认 `sub_25A307890` (`cfC`) / `sub_25A308220` (`cfc`) 的真实 ABI；主线程随后新增 `mps/ANE/experiments/modelcatalog_catalogclient_fixed_ctor_probe.S` 与 `...fixed_ctor_probe.py`，按 `X20=self/metatype` 的恢复 ABI 再试一次修正版 ctor probe，并将这条结果与 earlier `CatalogClient` probe 一起归并到 `mps/ANE/.ane_runs/json/modelcatalog_harness_vs_patch_verdict_20260622.json` | 证据: 1) export-surface 线确认：`InitializableFromExistingConnection` 在当前 `ModelCatalog` 可见 surface 内仍是纯协议，只有 associated type `Service: XPCService`，看不到 concrete conformer；`BidirectionalXPCServiceClientConnection` 的构造同样依赖 generic service/interface/delegate concrete 化，当前没有现成 concrete 类型；2) IDA 线确认：`CatalogClient` 的 concrete ctor 链确实存在，`sub_25A307890` 是分配 init (`cfC`)，`sub_25A308220` 是 non-allocating init body (`cfc`)，并且 `cfc` 低层 ABI 确实要求 `X20=self`；3) 修正 X20 约定后的 ctor probe 不再像之前那样立即 crash，而是在超时内挂起/阻塞，说明用户态 harness 路并非完全虚假，但当前仍被 ctor/初始化 ABI 与 service concrete 化问题双重阻塞 | 结论: 本轮完成了一个新的短期目标：**用户态 `ModelCatalog` harness 路线应正式降级为次级方向，主线回到 `0x10010CE3C` 的静态 patch/injection 目标。** 原因不是它完全不存在，而是：connection-based 路线在当前可见 surface 内只有协议没有 concrete conformer；默认 `CatalogClient` ctor 即便修正了 X20 也仍挂在更深初始化阶段。相反，`0x10010CE3C` 已经是静态上最窄、最清楚、最可控的共享 lookup seam | 下一步: 不再继续把主要精力压在用户态 client harness 上；下一轮应直接进入 **`0x10010CE3C` 的最小二进制 patch 设计**，在三种方向里选一个具体策略：1) 入口前参数改写，2) 替换 `queryResourceBundle(with:)` 调度目标，3) 只在返回后合成受控结果，并给出最小可验证 patch 方案
2026-06-22 20:24:00 +0800 | 目标: 把已选中的 `0x10010CE3C` 共享 lookup seam 从“最优 patch 点”推进成第一版**可复跑的实际 patch 原型**，并验证主线无需再等待用户态 harness 跑通 | 动作: 先用主线程扫描 `modelmanagerd_arm64e_20260622` 的 `__TEXT,__text`，确认 0x10010CE3C 附近不存在可容纳 20B stub 的 executable code cave；据此把 patch 形态继续收窄为“原地 nil-fallback patch”。随后新增 `mps/ANE/experiments/modelmanagerd_query_dispatch_patch_layout_probe.py` 固化 `0x10010CE18`、`0x10010CE3C`、`0x10010D2CC` 的文件偏移与反汇编窗口，再新增 `mps/ANE/experiments/modelmanagerd_query_dispatch_inplace_nil_patch.py`，对 copied arm64e slice `mps/ANE/.ane_runs/tmp/modelmanagerd_arm64e_20260622` 做 40B 原地改写：把 `0x10010CE18–0x10010CE3C` 的 10 条指令替换为 4 次 `stur xzr` 零化 `[X29-0xA8..-0x90]` 的 optional existential buffer、`mov x21,#0` 与 5 个 `nop`，让控制流自然从 `0x10010CE40` / `CBZ X21, 0x10010D028` 落入现有 nil fallback 路径 | 证据: 1) `mps/ANE/.ane_runs/json/modelmanagerd_query_dispatch_patch_layout_verdict_20260622.json` 已把共享 patch 点固化为具体文件偏移与窗口；2) `mps/ANE/.ane_runs/json/modelmanagerd_query_dispatch_inplace_nil_patch_verdict_20260622.json` 已确认 patched copy `mps/ANE/.ane_runs/tmp/modelmanagerd_arm64e_query_nil_patch_20260622` 的反汇编完全符合预期，原 `queryResourceBundle(with:)` dispatch 前准备与 `BL` 已被原地替换为 zero-optional + clear-X21 方案；3) 与此同时，`mps/ANE/.ane_runs/json/modelcatalog_catalogclient_fixed_ctor_probe_verdict_20260622.json` 继续表明修正 X20 后的 ctor probe 已从“立即 crash”推进到“构造期挂起/阻塞”，但仍不足以让用户态 harness 反超 patch 主线 | 结论: 本轮完成了一个新的短期目标：`0x10010CE3C` 的静态最佳 patch 点已经推进成了**第一版可复跑的原地二进制 patch 原型**。当前主线不再停留在抽象 patch 讨论，而是已经有一个具体 patched copy 可供下一轮验证下游行为。与此同时，用户态 `CatalogClient` harness 继续保留为次级调查，不再阻塞主线推进 | 下一步: 不再继续争论 patch 点或 harness 可行性；下一轮应直接验证 **这条 in-place nil-fallback patch 是否足以保留下游行为并推进主线**，若不够，再设计第二阶段 patch 去保留更多真实 query 语义
2026-06-22 20:46:00 +0800 | 目标: 判定第一版 in-place nil-fallback patch 是否足够推进主线，还是应立即转向更深的 host-side provider handoff | 动作: 先用 `ida` 子代理聚焦 `0x10010D468` 之后的 nil/fallback 路径，确认 `loc_10010D468`、`sub_10010D73C`、`sub_100056EB8` 的真实角色；再用主线程汇总现有 `modelmanagerd` strings / schema note / `ane_state` 中已确认的 host route，把下一条更深的边界整理成 `mps/ANE/.ane_runs/json/modelmanagerd_query_dispatch_inplace_nil_patch_next_handoff_verdict_20260622.json` | 证据: 1) `ida` 已确认 nil-fallback 路径本身仍限在 ModelCatalog 资产解析/包装域：它把资源切到 test assets bundle 并产出 async task 包装，但不在 `sub_10010CA70` / `sub_10010D73C` 内直接触发 ANE compile/load/eval；2) `modelmanagerd` 的现有 strings / docs 已经把更深的 host-side 边界收敛到 `InferenceProviderAssetManager`、`getInferenceProvider(withDescriptor:)`、`assetBundleWithNewAndExistingAssets(...)`、以及 `InferenceProviderXPCSender.requestInputStreamInference(...)` / `sessionTransition` / `transitionAsset` 等路径；3) 这说明 nil-fallback patch 适合作为 asset-resolution → async-task continuity 的 smoke 验证，但其本身不足以回答 lower control layer 的单进程复用问题 | 结论: 本轮完成了一个新的短期目标：**第一版 nil-fallback patch 已被正式降格为 smoke/asset-resolution 级 patch**。它虽然让我们拥有了一个可复跑的 patched copy，但真正需要打开的下一条边界已经转移到 host-side provider handoff，而不再是继续细抠 `sub_10010CA70` / `sub_10010D73C` 自身 | 下一步: 不再继续优化这条 nil-fallback patch；下一轮应直接打开 **`InferenceProviderAssetManager` / `getInferenceProvider(withDescriptor:)` / `InferenceProviderXPCSender.requestInputStreamInference(...)`** 这一组 host-side 边界，追出第一次真正接近 ANE lower control layer 的 handoff
2026-06-22 21:02:00 +0800 | 目标: 在 nil-fallback patch 已被降级为 smoke patch 后，把下一轮应打开的更深 host-side 边界从一组候选函数收敛成一个更明确的优先模块/函数对 | 动作: 先让 `ida` 子代理尝试直接追 `sub_10003D870` / async task 之后最先离开纯 ModelCatalog 域的 handoff，但受服务端高负载中断；主线程于是基于现有 strings / `modelmanager_host_route_schema_note.md` / `ane_state.md` 中已经确认的 host route，把边界选择整理成 `mps/ANE/.ane_runs/json/modelmanagerd_host_side_provider_handoff_target_verdict_20260622.json` | 证据: 1) `modelmanagerd` strings 已明确出现 `InferenceProviderAssetManager`、`getInferenceProvider(withDescriptor:)`、`assetBundleWithNewAndExistingAssets(for:runtimeAssets:inferenceProviderConnection:)`、`InferenceProviderXPCSender.requestInputStreamInference(...)`、`sessionTransition`、`transitionAsset`、`prewarmBundle` 等真实 host-side/provider-side 交界语义；2) `modelmanager_host_route_schema_note.md` 与 `ane_state.md` 已确认 `InferenceProviderXPCSender` 的构造与 request surface，说明这条边界不仅存在，而且是当前 machine-local 证据能连续追到的第一条 provider request/transition 层；3) 相比直接跳到 `ANECompiler`/`ANEServices`，`InferenceProviderAssetManager` 仍在 modelmanagerd 内，离当前静态证据链最近，也最适合继续做主线 handoff 压缩 | 结论: 本轮完成了一个新的短期目标：**下一轮最值得打开的边界已经从“某个 host-side provider handoff”收敛成 modelmanagerd 内的 `InferenceProviderAssetManager`，优先函数是 `getInferenceProvider(withDescriptor:)` 与 `assetBundleWithNewAndExistingAssets(...)`。** 也就是说，主线现在不再需要在 ModelCatalog patch 层做更多争论，而应直接进入 provider-management 这一层 | 下一步: 不再继续围绕 `sub_10010CA70` / nil-fallback patch 本身做追加优化；下一轮应直接对 **`InferenceProviderAssetManager.getInferenceProvider(withDescriptor:)`** 与 **`assetBundleWithNewAndExistingAssets(for:runtimeAssets:inferenceProviderConnection:)`** 做窄分析，找出它们中哪一个是第一次真正把控制权交给 `InferenceProviderXPCSender` / provider request / transition 的边界
2026-06-22 21:23:00 +0800 | 目标: 在 host-side provider-management 层里，把“下一轮该开哪个函数”再压一层，不再只是停在 `InferenceProviderAssetManager` 模块级 | 动作: 尝试用更轻的 `reverse-engineer` / `ida` 子代理对 `getInferenceProvider(withDescriptor:)` 与 `assetBundleWithNewAndExistingAssets(...)` 做二选一收敛，但仍受服务端高负载影响；主线程于是退回到 machine-local 一手证据：`modelmanagerd` strings 中不仅有 `InferenceProviderAssetManager` / `getInferenceProvider(withDescriptor:)` / `assetBundleWithNewAndExistingAssets(...)`，还同时出现 `InferenceProviderExtensionConnection setCurrentState creating new sender part`、`addActiveRequest`、`requestInputStreamInference (...) executing on %s`、`transitionAsset failed ...` 等字符串。基于这组信号，我把新的边界优先级整理成 `mps/ANE/.ane_runs/json/modelmanagerd_provider_management_first_handoff_verdict_20260622.json` | 证据: 1) `assetBundleWithNewAndExistingAssets(...)` 的签名已经拿到 `inferenceProviderConnection`，说明它位于 provider 已选择/已连接之后；2) `InferenceProviderExtensionConnection setCurrentState creating new sender part` 与 `addActiveRequest` / `requestInputStreamInference` / `transitionAsset` 同时出现在 modelmanagerd strings 面，强烈提示 provider-management 内真正开始 request/transition 工作的节点与 connection 状态/active request 管理直接相关；3) 因此相较于 `getInferenceProvider(withDescriptor:)` 这种 provider 选择前置层，`assetBundleWithNewAndExistingAssets(...)` 更像第一次真正把控制权朝 `InferenceProviderXPCSender` 流推进的 handoff，而 `InferenceProviderExtensionConnection` 则是紧随其后的具体状态机/发射器创建分支 | 结论: 本轮完成了一个新的短期目标：**provider-management 层内最值得优先打开的函数已经进一步收敛成 `assetBundleWithNewAndExistingAssets(for:runtimeAssets:inferenceProviderConnection:)`，并且下一层应同时盯 `InferenceProviderExtensionConnection` 的 sender-part 创建/状态迁移。** 也就是说，主线现在不再需要在 `getInferenceProvider(withDescriptor:)` 和 `assetBundleWithNewAndExistingAssets(...)` 之间摇摆，而应直接追后者以及紧随其后的 connection-state 分支 | 下一步: 不再继续做 provider 选择层的优先级争论；下一轮应直接对 **`assetBundleWithNewAndExistingAssets(for:runtimeAssets:inferenceProviderConnection:)`** 和 **`InferenceProviderExtensionConnection setCurrentState creating new sender part`** 做窄分析，确认它们是否直接构造/调用 `InferenceProviderXPCSender` 的 request/transition 路径
2026-06-22 21:19:00 +0800 | 目标: 在已确定 host-side provider-management 是下一层边界后，把 `InferenceProviderAssetManager` 内的两个候选函数再压出一个更具体的优先级：`getInferenceProvider(withDescriptor:)` vs `assetBundleWithNewAndExistingAssets(...)` | 动作: 先尝试让 `ida` / `reverse-engineer` 子代理直接做这一步，但都因服务端高负载中断；主线程于是退回到 machine-local 一手证据：1) `modelmanagerd` strings 明确出现 `InferenceProviderAssetManager`、`getInferenceProvider(withDescriptor:)`、`assetBundleWithNewAndExistingAssets(for:runtimeAssets:inferenceProviderConnection:)`、`InferenceProviderExtensionConnection`、`requestInputStreamInference`、`sessionTransition`、`transitionAsset`；2) `modelmanager_host_route_schema_note.md` 与 `ane_state.md` 已确认 `InferenceProviderXPCSender` 的 request/transition surface；3) 结合函数签名本身，`getInferenceProvider(withDescriptor:)` 更像 provider 选择边界，而 `assetBundleWithNewAndExistingAssets(...)` 因为已经拿到了 `inferenceProviderConnection`，更像第一次真正朝 request/transition 流推进的 host-side handoff。随后把这个判断整理成 `mps/ANE/.ane_runs/json/modelmanagerd_provider_management_first_handoff_verdict_20260622.json` | 证据: 1) `assetBundleWithNewAndExistingAssets(for:runtimeAssets:inferenceProviderConnection:)` 的签名本身已经包含 `inferenceProviderConnection`，表明它处于 provider 已选择/已连接之后的阶段；2) 同一批 strings 中 `requestInputStreamInference`、`sessionTransition`、`transitionAsset`、`prewarmBundle` 明显属于 provider-side request/transition 语义，说明 host-side handoff 离它们最近的函数，更可能是已经持有 provider connection 的那一支；3) 相比之下，`getInferenceProvider(withDescriptor:)` 更自然地属于 provider 选择前置层，仍早于真正的 request/transition handoff | 结论: 本轮完成了一个新的短期目标：**在 modelmanagerd 的 provider-management 层内，当前最值得优先打开的具体函数已经从两选一收敛成 `assetBundleWithNewAndExistingAssets(for:runtimeAssets:inferenceProviderConnection:)`。** `getInferenceProvider(withDescriptor:)` 仍然重要，但更像前置 provider 选择层；真正更接近 `InferenceProviderXPCSender` request/transition 流的第一次 handoff，应优先从已经持有 `inferenceProviderConnection` 的函数打开 | 下一步: 不再继续在 `getInferenceProvider(withDescriptor:)` 和 `assetBundleWithNewAndExistingAssets(...)` 之间摇摆；下一轮应直接对 **`assetBundleWithNewAndExistingAssets(for:runtimeAssets:inferenceProviderConnection:)`** 做窄分析，确认它是否直接构造/调用 `InferenceProviderXPCSender` 的 `transitionAsset` / `requestInputStreamInference` / `prewarmBundle` 流，还是仍只是更早的数据准备层
2026-06-22 22:05:00 +0800 | 目标: 判断 modelmanagerd 的 provider-management 层到底还是不是纯 asset-bookkeeping，还是已经实际持有 lower-control carrier | 动作: 由于当前 Codex 会话里的主线程 `ida-pro-mcp` 绑定仍是 `Transport closed`，且子代理持续被平台高负载打断，本轮改走 machine-local 一手链路：1) 用 `otool -ov` 读取 Swift class ivar 元数据；2) 用 `otool -tvV`/`nm -m` 收集 `InferenceProviderXPCSender` 的真实外部调用点；3) 把 `InferenceProviderAssetManager` / `InferenceProviderManager` / `InferenceProviderExtensionConnection` 的对象图与 sender ctor / request / transition 调用地址合并成新的结构化 verdict `mps/ANE/.ane_runs/json/modelmanagerd_provider_management_sender_object_graph_verdict_20260622.json` | 证据: 1) `InferenceProviderAssetManager` 持有 `providerManager`、`modelCatalog`、`neuralEngine`；2) `InferenceProviderManager` 持有 `inferenceProviderConnections`；3) `InferenceProviderExtensionConnection` 持有 `sender`、`activeRequest`、`descriptor`、`providerIdentification`；4) `modelmanagerd` 内部存在对 `InferenceProviderXPCSender.init(session:)`(`0x1000603d4`)、`init(builtInProvider:session:)`(`0x100060458`)、`requestInputStreamInference(...)`(`0x10006c3f4`)、`sessionTransition(...)`(`0x1000672b0`)、`prewarmBundle(...)`(`0x100067fa8`)、`transitionAsset(...)`(`0x100068f74`) 的真实代码引用；5) strings 同时出现 `InferenceProviderExtensionConnection setCurrentState creating new sender part` 与 `addActiveRequest` / `requestInputStreamInference` / `sessionTransition` / `transitionAsset` | 结论: 本轮完成了一个新的短期目标：**provider-management 已被正式证实不是纯 asset-preparation 层，lower-control carrier 已经以 `InferenceProviderExtensionConnection.sender` 的形式浮出到 modelmanagerd；当前第一条已证实的宿主对象图是 `InferenceProviderAssetManager -> providerManager -> inferenceProviderConnections -> InferenceProviderExtensionConnection.sender`。** 但这轮还没有把函数级 seam 压到 `assetBundleWithNewAndExistingAssets(...)` 本身，所以“它是不是直接跨入 sender/request-transition 流”的问题仍未关闭 | 下一步: 继续把函数级 seam 压小到一个 yes/no：优先证明 `assetBundleWithNewAndExistingAssets(for:runtimeAssets:inferenceProviderConnection:)` 是否直接调用/促成 `InferenceProviderExtensionConnection` 的 sender-part 创建；若当前 headless IDA 仍打不开 `modelmanagerd`，就转而用重启后的 Codex MCP 或 GUI/替代反汇编手段做这一步
2026-06-22 22:28:00 +0800 | 目标: 把 `assetBundleWithNewAndExistingAssets(for:runtimeAssets:inferenceProviderConnection:)` 压成一个函数级 yes/no：它到底是不是 direct sender seam | 动作: 先按默认规则起了一个 `reverse-engineer` 子代理做窄判断，但仍被平台高负载打断；主线程随后改走 machine-local 证据：1) 用 `strings -a -t x` 确认 `assetBundleWithNewAndExistingAssets(...)`、`getInferenceProvider(withDescriptor:)`、`setCurrentState creating new sender part` 等字符串在 `__cstring` 的相对位置；2) 用 `otool -tvV` 追 `failed to transition to dynamic mode` 与 `InferenceProvider assets are de-synced with MM (alreadyLoaded)` 的代码窗口，落到 `0x1000b6608` / `0x1000c26ac` 等 AssetManager/asset-state 簇；3) 并把所有已确认的 `InferenceProviderXPCSender` ctor / request / transition 引用重新收敛，确认它们全部集中在 `0x100060000–0x10006dfff`；4) 产出 `mps/ANE/.ane_runs/json/modelmanagerd_assetbundle_function_seam_verdict_20260622.json` | 证据: 1) `assetBundleWithNewAndExistingAssets(...)` 附近的同簇字符串是 `modelmanagerd/InferenceProviderAssetManager.swift`、`purgeAssets(for:)`、`failed to transition to dynamic mode`、`Dynamic mode asset`、`InferenceProvider assets are de-synced with MM (alreadyLoaded)`，明显更像 AssetManager/asset-state 面；2) `failed to transition to dynamic mode` 已落到 `0x1000b6608`，`Failed to load asset ... de-synced with MM (alreadyLoaded)` 已落到 `0x1000c26ac`；3) 当前没有在已落到的 `0x1000b* / 0x1000c*` 窗口里看到 `InferenceProviderXPCSender` 的 ctor / request / transition 引用；4) 相反，`InferenceProviderXPCSender.init(session:)`(`0x1000603d4`)、`init(builtInProvider:session:)`(`0x100060458`)、`sessionTransition(...)`(`0x1000672b0`)、`prewarmBundle(...)`(`0x100067fa8`)、`transitionAsset(...)`(`0x100068f74`)、`requestInputStreamInference(...)`(`0x10006c3f4`) 全部集中在 `0x100060000–0x10006dfff`；5) `InferenceProviderExtensionConnection setCurrentState creating new sender part` 仍是最强的相邻 sender-materialization 信号 | 结论: 本轮完成了一个新的短期目标：**`assetBundleWithNewAndExistingAssets(...)` 已被进一步判定为 AssetManager-side preparation / asset-state seam，而不是当前最直接的 sender-backed function-level edge。** 也就是说，之前“它也许就是 direct seam”的假设可以先正式降级；当前更像 direct seam 的是相邻的 `InferenceProviderExtensionConnection` sender/state 迁移窗口 | 下一步: 直接把下一轮唯一问题切到 `InferenceProviderExtensionConnection setCurrentState creating new sender part`：证明那个窗口是否第一次 materialize `InferenceProviderXPCSender`，并尽量把它和 `0x1000603d4` / `0x100060458` 这两个 sender ctor 调用窗口绑到一起
2026-06-22 22:42:00 +0800 | 目标: 继续下一轮，把 `InferenceProviderExtensionConnection setCurrentState creating new sender part` 从“强候选”压到更明确的 direct seam | 动作: 1) 先计算 `__cstring` 相对偏移，把 `setCurrentState creating new sender part`、`requestInputStreamInference executing on %s`、`prewarmBundle executing on %s`、`sessionTransition executing on %s` 映射回虚拟地址；2) 用 `otool -tvV` 直接搜到 `setCurrentState creating new sender part` 的代码窗口 `0x10005f73c`；3) 展开该窗口和邻近的 `0x10006036c–0x100060458` continuation cluster，确认后者直接调用 `InferenceProviderXPCSender.init(session:)` 与 `init(builtInProvider:session:)`；4) 比较两个窗口的 task/context 状态访问，确认二者都依赖同一类上下文偏移（至少共同命中 `x22 + 0x1d0`）；5) 产出 `mps/ANE/.ane_runs/json/modelmanagerd_extensionconnection_sender_creation_seam_verdict_20260622.json` | 证据: 1) `0x10005f73c` 是 `InferenceProviderExtensionConnection setCurrentState creating new sender part` 的直接日志引用点；2) 该窗口在记录 sender-part 创建后，立即 `swift_task_alloc`，写入 continuation/function pointer，并沿用当前上下文对象状态；3) 紧邻的 `0x10006036c–0x100060458` 窗口直接调用 `InferenceProviderXPCSender.init(session:)`(`0x1000603d4`) 与 `init(builtInProvider:session:)`(`0x100060458`)；4) 相比之下，之前已被降级的 AssetManager/asset-state 窗口在 `0x1000b* / 0x1000c*`，与这里分属不同 cluster | 结论: 本轮又完成了一个新的短期目标：**当前最强的 first direct host-side lower-control seam 已经从泛泛的 provider-management 层，再压到 `InferenceProviderExtensionConnection` 的 sender/state 迁移窗口；`setCurrentState creating new sender part` 现在是第一次 materialize `InferenceProviderXPCSender` 的最强候选直接边界。** 也就是说，当前主线已经不用再在 AssetManager helper 上摇摆，而应直接围绕这个 sender-state 窗口继续追 built-in vs non-built-in 分支与统一 request 上游 | 下一步: 继续把问题压小到控制字段级：确认 `0x10006036c–0x100060458` 里哪些状态字段或分支决定走 `init(session:)` 还是 `init(builtInProvider:session:)`，并判断这条 sender materialization cluster 是否就是后续 `requestInputStreamInference` / `sessionTransition` / `prewarmBundle` / `transitionAsset` 的统一上游
2026-06-22 22:56:00 +0800 | 目标: 把 `InferenceProviderExtensionConnection` sender materialization cluster 里的 ctor 分支从“看起来像 built-in vs non-built-in”压到状态/载荷级 | 动作: 1) 展开 `0x10006036c–0x100060458` sender ctor 窗口；2) 确认分支输入来自 `ldp x19, x20, [x22, #0x1f8]`，经 `0x100055bb0` 和 `_swift_getEnumCaseMultiPayload` 取 tag，再 `cmp w0, #0x1` 分出两条 ctor 路；3) 继续在本地二进制里搜 `BuiltInInferenceProvider`、`InferenceProviderDescriptor.Instance.default/specific` 相关构造窗口；4) 在 `0x100063ca8–0x100063ce0` 看到显式 materialize `BuiltInInferenceProvider` metadata，再以 `w2 = 0` 调 `_swift_storeEnumTagMultiPayload`，把 tag 0 和 built-in payload 绑定起来；5) 产出 `mps/ANE/.ane_runs/json/modelmanagerd_sender_ctor_branch_control_verdict_20260622.json` | 证据: 1) `w0 == 1` 走 `InferenceProviderXPCSender.init(session:)`；`w0 != 1` 走 `InferenceProviderXPCSender.init(builtInProvider:session:)`；2) 分支前不是布尔判断，而是 `_swift_getEnumCaseMultiPayload`，说明控制位来自多载荷 enum；3) `0x100063ca8–0x100063ce0` 显式 materialize `BuiltInInferenceProvider` metadata，并以 `tag 0` 存进 multi-payload enum；4) `0x10005f17c–0x10005f1ec` 还把与 `BuiltInInferenceProvider` 相关的 metadata/state 放进 `x22 + 0x1d8/0x1e0/0x1e8`，而 branch 输入放在 `x22 + 0x1f8` | 结论: 本轮完成了一个新的短期目标：**sender ctor 分支已经被压到“多载荷 enum + built-in payload case”级。** 当前最强语义是：`tag 0` 对应 `BuiltInInferenceProvider` payload，并流向 `init(builtInProvider:session:)`；`tag 1` 对应 non-built-in / plain-session case，并流向 `init(session:)`。这已经足够指导下一步围绕 sender-kind/provider-kind carrier 继续追 lower control layer | 下一步: 不再回头追 AssetManager；下一轮直接验证这个 enum-controlled sender materialization cluster 是否就是 `requestInputStreamInference` / `sessionTransition` / `prewarmBundle` / `transitionAsset` 的公共上游状态对象或 continuation
2026-06-22 23:10:00 +0800 | 目标: 验证 sender materialization cluster 是否真的是 major provider request/transition API 的公共上游，而不是只对某一条路径成立 | 动作: 1) 展开 `sessionTransition`、`prewarmBundle`、`transitionAsset`、`requestInputStreamInference` 四条 sender API 的反汇编窗口；2) 把它们和已知的 class ivar 元数据对齐；3) 发现 `InferenceProviderExtensionConnection.sender` 的 ivar 偏移是 `112 / 0x70`，而三条最清楚的 sender 路径都显式从某个对象的 `+0x70` 取值后进入对应的 `InferenceProviderXPCSender.*` API；4) `requestInputStreamInference` 虽然当前 slice 更间接，但仍在同一类 `x22` frame + `swift_task_alloc + continuation` 家族里；5) 产出 `mps/ANE/.ane_runs/json/modelmanagerd_sender_shared_upstream_verdict_20260622.json` | 证据: 1) `sessionTransition` 窗口 `0x10006729c–0x1000672f4`：从 `x22 + 0x28` 取对象，再取 `[object + 0x70]`，随后进入 `InferenceProviderXPCSender.sessionTransition(...)`；2) `prewarmBundle` 窗口 `0x100067f94–0x100067fe8`：从 `x22 + 0x20` 取对象，再取 `[object + 0x70]`，随后进入 `InferenceProviderXPCSender.prewarmBundle(...)`；3) `transitionAsset` 窗口 `0x100068f60–0x100068fc4`：从 `x22 + 0xf8` 取对象，再取 `[object + 0x70]`，随后进入 `InferenceProviderXPCSender.transitionAsset(...)`；4) 已知 `InferenceProviderExtensionConnection.sender` 的 ivar 偏移正好就是 `0x70`；5) `requestInputStreamInference` 窗口 `0x10006c3f4–0x10006c444` 同样使用同类 `x22` frame、`swift_task_alloc`、continuation 写入和相邻 sender API 调度逻辑 | 结论: 本轮完成了一个新的短期目标：**major provider request/transition API 的共享 host-side carrier 已经正式收敛到 `InferenceProviderExtensionConnection.sender` / sender-state frame。** 这意味着当前主线已经从“哪个 helper 更像 handoff”推进到“哪组共享 frame slots 才是 lower control layer carrier”，后续应围绕这些共享 slots 恢复 descriptor / request metadata / state 语义，而不是再在函数级边界上打转 | 下一步: 继续把 shared sender/state frame 压到可控字段级：确认其中哪些 slot 对应 descriptor / request metadata / load state / request ID 等关键控制字段，并判断哪个 slot 最适合做最小 probe 或 patch
2026-06-22 23:22:00 +0800 | 目标: 把 shared sender/state frame 从“共享 carrier”再推进到第一批可操作 slot，给下一轮 probe / patch 选点 | 动作: 1) 展开 `transitionAsset` 与 `requestInputStreamInference` 的参数装配窗口；2) 把已知 `InferenceProviderExtensionConnection.sender @ 0x70` 的类布局事实，与三条显式 sender API 路径的 `[object + 0x70]` 读取对齐；3) 固定三条 sender mirror slots：`sessionTransition -> x22 + 0x88`、`prewarmBundle -> x22 + 0x98`、`transitionAsset -> x22 + 0x1c8`；4) 固定两组下一轮最值得继续追的参数 slab：`requestInputStreamInference` 的紧凑 slab `x22 + 0xb8 .. 0xc8` 和 `transitionAsset` 的富控制 slab `x22 + 0x130 .. 0x200`；5) 产出 `mps/ANE/.ane_runs/json/modelmanagerd_sender_frame_slot_recovery_verdict_20260622.json` | 证据: 1) `sessionTransition`：从 `x22 + 0x28` 取对象，再取 `[object + 0x70]`，并把 sender mirror 存到 `x22 + 0x88`；2) `prewarmBundle`：从 `x22 + 0x20` 取对象，再取 `[object + 0x70]`，并把 sender mirror 存到 `x22 + 0x98`；3) `transitionAsset`：从 `x22 + 0xf8` 取对象，再取 `[object + 0x70]`，并把 sender mirror 存到 `x22 + 0x1c8`；4) `requestInputStreamInference` 调度前直接装入 `x0,x1 <- [x22 + 0xb8]`、`x2,x3 <- [x22 + 0xc8]`，并使用 `x22 + 0x1a0` 作为 task/continuation slot；5) `transitionAsset` 在进入更深调度前读取 `x22 + 0x130 .. 0x200` 的密集 slab，其中 `w1 <- [x22 + 0x200]` 当前最像 load-state enum 输入 | 结论: 本轮完成了一个新的短期目标：**shared sender/state frame 已恢复出第一批可操作 slot。** 现在不只是知道 carrier 在哪，还知道下一轮最值得动手的是哪一组 slot：`transitionAsset` 的富控制 slab 比 `requestInputStreamInference` 的紧凑 slab 更适合先做字段恢复与最小 patch 试探 | 下一步: 直接盯 `transitionAsset` 的 `x22 + 0x130 .. 0x200`：优先恢复 `w1 <- [x22 + 0x200]` 及其邻近 slot 的 `LoadState / descriptor / request metadata / request ID` 语义，并据此挑一个最小 probe / patch 点
2026-06-22 23:34:00 +0800 | 目标: 在 shared sender/state frame 的 `transitionAsset` 富控制 slab 里，先恢复第一层具体字段语义，避免下一轮 patch 还停在“盲打” | 动作: 1) 进一步展开 `transitionAsset` 的中段窗口；2) 观察 `x22 + 0x130 .. 0x200` 的装配顺序；3) 确认 `w1 <- [x22 + 0x200]` 是进入第一批 typed helper 之前唯一明显以窄 enum 形态读出的 slot；4) 结合目标 sender API 签名 `transitionAsset(withDescriptor:to:from:requestIdentifier:)`，将其正式收敛为当前最强的 `LoadState` 候选；5) 同时记录同一路径里出现的 `InferenceProviderDescriptor.CustomStringConvertible` witness 与 `x22 + 0xf8` 对应对象的 retain/复用，作为 descriptor 相关信号；6) 产出 `mps/ANE/.ane_runs/json/modelmanagerd_transitionasset_control_slot_semantics_verdict_20260622.json` | 证据: 1) `ldr w1, [x22, #0x200]` 直接进入 `transitionAsset` 富控制 slab 的首批 typed helper；2) `transitionAsset` 目标签名中，最符合这种窄整型/enum 形状的参数是 `to/from LoadState`；3) 当前还不能严谨区分它到底是 `to` 还是 `from`，但已经足够把它列为下一轮最优先的 patch/probe 候选；4) 同一路径后半段加载了 `InferenceProviderDescriptor` 的 `CustomStringConvertible` witness，并对 `x22 + 0xf8` 对应对象做 retain / 复用，说明这条 rich slab 同时携带 descriptor 相关材料 | 结论: 本轮完成了一个新的短期目标：**`transitionAsset` 富控制 slab 的第一层字段语义已经恢复出来，其中 `x22 + 0x200` 是当前最强的 `LoadState` 候选。** 这使下一轮可以从“恢复语义”切换到“选最小 patch 点”，优先测试 state slot 而不是继续在更早层绕圈 | 下一步: 继续把 `transitionAsset` slab 压成最小 patch 选择：优先判断改写 `x22 + 0x200` 或其邻近 state slot 是否最可能改变 `transitionAsset` 行为，并尽量把 `to/from` 区分出来
2026-06-22 23:46:00 +0800 | 目标: 不再泛泛恢复语义，直接在 `transitionAsset` 富控制 slab 里选出第一个最小 patch 点 | 动作: 1) 复看 `x22 + 0x130 .. 0x200` 的装配顺序；2) 对比 `x22 + 0x200` 与邻近 composite slots 的使用形态；3) 确认 `x22 + 0x200` 是当前 rich slab 中最早进入 typed helper、最窄、最像 enum 的控制位；4) 把 `x22 + 0xf8` descriptor/object 路径保留为第二候选，而不是第一刀；5) 产出 `mps/ANE/.ane_runs/json/modelmanagerd_transitionasset_patchpoint_priority_verdict_20260622.json` | 证据: 1) `ldr w1, [x22, #0x200]` 在 rich slab 中最早进入首批 typed helper；2) `x22 + 0x130 / 0x148 / 0x158 / 0x160 / 0x170 / 0x180` 更多表现为 pointer/pair/witness 风格的复合输入，不适合作为第一刀；3) `x22 + 0xf8` 虽是 descriptor/source-object 锚点，但对象级杠杆过宽，解释性不如 state slot；4) `transitionAsset(withDescriptor:to:from:requestIdentifier:)` 的签名让 `x22 + 0x200` 继续保持当前最强的 `LoadState` 候选 | 结论: 本轮完成了一个新的短期目标：**`transitionAsset` 的首选最小 patch/probe 点已经正式收敛到 `x22 + 0x200`。** 这意味着下一轮不该再纠结“先动哪个 slot”，而应直接设计 state-value 级 probe，比较不同 `LoadState` 候选值是否能改变路径行为 | 下一步: 继续把 `x22 + 0x200` 压成可执行 probe 设计：优先判断改向 `loaded / unloaded / dynamicMode` 中哪个候选最有信息量，并尽量再压小 `to` vs `from`
2026-06-22 23:58:00 +0800 | 目标: 把 `x22 + 0x200` 的 state-value probe 从“试哪个值”压到一个明确首选值，避免下一轮还在值空间里反复摇摆 | 动作: 1) 汇总 `LoadState` 相关可见值面；2) 对比 `dynamicMode`、`loaded`、`unloaded` 在 `transitionAsset` 周围 strings / 日志里的可观测强度；3) 复看 `alreadyLoaded` / dynamic-mode failure / `Load in called for terminated extension` 等语义面；4) 产出 `mps/ANE/.ane_runs/json/modelmanagerd_transitionasset_first_probe_value_verdict_20260622.json` | 证据: 1) 当前最直接的可观测面明显偏向 dynamic-mode：`failed to transition to dynamic mode`、`Failed to move asset %s to dynamic mode: %@`、`Failed to move asset %s to dynamic mode in %s: %@`；2) `loaded` 受 `alreadyLoaded` / self-heal 路径干扰更大，第一针信息量更差；3) `unloaded` 在当前附近的 strings / 日志面也不如 `dynamicMode` 直接；4) `x22 + 0x200` 作为 rich slab 中最早的窄 enum-like scalar，再叠加 `Load in called for terminated extension` 这类语义面，当前更像 `to`-side `LoadState` 而不是 `from` | 结论: 本轮完成了一个新的短期目标：**`x22 + 0x200` 的首个 probe 值已经收敛到 `dynamicMode`。** 这让下一轮可以直接进入“最小可执行 patch 设计”，不必再在 `loaded / unloaded / dynamicMode` 三选一上浪费回合 | 下一步: 直接围绕 `x22 + 0x200 -> dynamicMode` 设计最小可执行 patch / probe，并写清楚最值得观察的成功/失败判据
2026-06-23 00:10:00 +0800 | 目标: 把 `x22 + 0x200 -> dynamicMode` 从“首选 probe 值”推进到真正可执行的最小 patch 原型 | 动作: 1) 发现比 patch consumer 更干净的 producer-side 位点：`0x10006881c` 本来就把 `x22 + 0x200` 初始化成 `LoadState.loaded`；2) 把它与 `0x100069c28` 的 `LoadState.dynamicMode` literal pool 引用对照；3) 计算 arm64e thin-slice `mps/ANE/.ane_runs/tmp/modelmanagerd_arm64e_20260622` 的真实文件偏移；4) 写出最小 patch 脚本 `mps/ANE/experiments/modelmanagerd_transitionasset_dynamicmode_patch.py`；5) 运行脚本生成 `mps/ANE/.ane_runs/tmp/modelmanagerd_arm64e_transitionasset_dynamicmode_patch_20260622`；6) 用反汇编和原始字节校验 patch 已生效；7) 产出 `mps/ANE/.ane_runs/json/modelmanagerd_transitionasset_dynamicmode_patch_verdict_20260622.json` | 证据: 1) patch 地址 `0x10006881c` 原本是 `ldr x8, [x8, #0x3f0] ; LoadState.loaded`；2) 替换后变成 `ldr x8, [x8, #0x3e8] ; LoadState.dynamicMode`；3) 文件偏移 `0x6881c` 处的指令字从 `0xf941f908` 变成 `0xf941f508`；4) patched 样本反汇编已经显示 `LoadState.dynamicMode` 被写入 `x22 + 0x200` 的 producer-side 路径 | 结论: 本轮完成了一个新的短期目标：**`x22 + 0x200 -> dynamicMode` 的最小可执行 patch 原型已经落地，而且是单指令 producer-side 替换。** 这比直接 patch consumer 更干净，因为它保留了后续 `ldr w1` / `str w1, [x22, #0x200]` 的原生流，只改变选取的 `LoadState` | 下一步: 从静态 patch 进入运行级判据设计 / 执行准备：明确这条 patch 最值得观察的是 dynamic-mode 成功、dynamic-mode 失败、掉进 `alreadyLoaded` / self-heal、还是完全无变化
2026-06-22 22:12:52 +0800 | 目标: 把 `transitionAsset` dynamicMode patch 从“静态 patch 已落地”推进到可执行的运行级判据 / 执行准备 | 动作: 1) 复验 `mps/ANE/experiments/modelmanagerd_transitionasset_dynamicmode_patch.py` 生成的 patched slice；2) 用 `otool -tvV` 确认 `0x10006881c` 已从 `LoadState.loaded` 改为 `LoadState.dynamicMode`，且后续 `ldr w1` / `str w1, [x22, #0x200]` 原生流保持；3) 固化四类运行观察面：`dynamic_mode_success`、`dynamic_mode_failure`、`already_loaded_or_self_heal`、`no_observable_change`；4) 新增 `mps/ANE/.ane_runs/json/modelmanagerd_transitionasset_dynamicmode_runtime_criteria_20260622.json`；5) 更新 `docs/ane_state.md` 和 `docs/ane_next.md` | 证据: 1) patched binary SHA256: `6cba9ac4f982b5a399573b3606eb55b5b61cc3ace8a9eea47b177220033ca5e8`；2) original thin slice SHA256: `6e4f5574587ac198842ca50508ca6d5fcc334546a52fa918a79e9a1bbe7e399d`；3) patched disassembly: `0x10006881c ldr x8, [x8, #0x3e8] ; LoadState.dynamicMode` followed by `ldr w1, [x8]` and `str w1, [x22, #0x200]`；4) `ida` sub-agent 和 `doc-reader` sub-agent 本轮均因平台 high demand/线程限制未能产出事实包，主线程 `ida-pro-mcp idb_list` 仍报 `Transport closed`，但本地 `codex_stdio_wrapper.py` 的 MCP initialize 握手成功，说明安装/stdio 桥可启动、当前主要是 Codex 会话绑定的 transport 问题 | 结论: 本轮短期目标完成：dynamicMode patch 的运行级判据已经明确，当前结论为 `confirmed`。下一轮不应继续扩大静态归因，而应做 paired baseline/patched runtime probe；若完全无变化，则本 sender-state carrier 应进入 `falsified` 候选 | 下一步: 准备最小 paired runtime probe，输出 `mps/ANE/.ane_runs/json/modelmanagerd_transitionasset_dynamicmode_runtime_probe_20260622.json`、对应 CSV、统一日志摘录和 `test_clean.m4a` profile/benchmark 摘要
2026-06-22 22:12:52 +0800 | 目标: 准备最小 paired runtime probe wrapper，让下一轮能用同一格式采集 baseline/patched profile 与日志差异 | 动作: 1) 定位现有入口 `benchmark/private_ane_test_clean_benchmark.py` 与 `benchmark/analyze_private_ane_profile.py`；2) 新增 `mps/ANE/experiments/modelmanagerd_transitionasset_dynamicmode_runtime_probe.py`，默认 plan-only，不做系统 daemon 替换；3) 运行 wrapper 默认模式，生成 `mps/ANE/.ane_runs/json/modelmanagerd_transitionasset_dynamicmode_runtime_probe_20260622.json` 和 CSV；4) 执行 `python3 -m py_compile` 验证脚本语法 | 证据: 1) baseline profile 来自既有 `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_persistent_aux_profile.json`；2) plan-only CSV 中 baseline 行为 `ok`，patched 行为 `not_run`；3) baseline 指标：`wall_time_s=43.00265733300148`、`transformer_compile_s=5.712273664999884`、`transformer_eval_s=20.669240746992728`；4) `searcher` sub-agent 仍因平台 high demand 失败，因此命令入口定位由主线程本地 `rg/find/jq` 完成 | 结论: 本轮短期目标完成但 verdict 为 `inconclusive`：probe wrapper 已就绪，能够统一输出结果；真正 patched 对照尚未执行，因为安全的 patched-command/daemon 注入路径还未选择 | 下一步: 选择最小安全 patched-command/daemon 注入路径，并用 `modelmanagerd_transitionasset_dynamicmode_runtime_probe.py --run-baseline --run-patched --patched-command ... --baseline-log ... --patched-log ...` 产出 paired 对照
2026-06-22 22:34:23 +0800 | 目标: 判断当前用户态是否存在可直接传给 paired wrapper 的安全 `--patched-command` / daemon 注入路径 | 动作: 1) 只读检查 `launchctl print system/com.apple.modelmanagerd`、`ps`、`csrutil status`、`codesign`、`lipo`、`file`；2) 用 `lldb -p 528` 和 `frida -p 528` 做非破坏性 attach 探测；3) 用 `/usr/bin/log show` 验证后续日志谓词可用；4) 在 `/tmp` 副本上做 ad-hoc 重签测试，只验证签名/entitlement 变化，不运行 daemon；5) 产出 `mps/ANE/.ane_runs/json/modelmanagerd_transitionasset_patched_command_path_verdict_20260622.json` 和 CSV | 证据: 1) `modelmanagerd` 是 `system/com.apple.modelmanagerd` LaunchDaemon，程序 `/usr/libexec/modelmanagerd`，用户 `_modelmanagerd`，pid 528；2) SIP enabled，系统二进制路径显示 `restricted,compressed`；3) 原始 `/usr/libexec/modelmanagerd` `codesign --verify --strict` 通过，patched thin slice 报 `invalid signature (code or signature have been modified)` 且 exit 1；4) ad-hoc 签名临时副本可通过本地验证，但不保留 Apple platform/private entitlements；5) `lldb` attach 失败原因是当前用户不能附加到 `_modelmanagerd`，`frida` 同样报 unable to access process；6) reverse-engineer sub-agent 仍因平台 high demand 失败，本轮由主线程本地证据完成 | 结论: 本轮短期目标完成，verdict 为 `falsified`：当前用户态没有安全的 command-level patched daemon 路径，paired wrapper 的 patched half 不能靠普通 `--patched-command` 执行 | 下一步: 检查 `com.apple.modelmanager.simulator` Mach service 或 ModelManagerServices client-side route 是否能提供不替换 system daemon 的最小观察/控制 harness
2026-06-22 22:50:29 +0800 | 目标: 判断 `com.apple.modelmanager.simulator` 或现有 ModelManagerServices client-side route 是否能提供不替换 daemon 的最小观察/控制 harness | 动作: 1) 新增 `mps/ANE/experiments/modelmanager_simulator_service_probe.py`，用同一组 `xpc_swiftoverlay_taskshape_probe` body 对比 `com.apple.modelmanager` 与 `com.apple.modelmanager.simulator`；2) 运行 probe 并生成 `mps/ANE/.ane_runs/json/modelmanager_simulator_service_probe_20260622.json` / CSV；3) 汇总已有 `LoadAssetBundle` / `HoldAssetBundle` / high-level Swift client / `PrewarmSession` 证据；4) 产出 `mps/ANE/.ane_runs/json/modelmanager_non_daemon_harness_verdict_20260622.json` / CSV；5) `python3 -m py_compile` 验证新增脚本 | 证据: 1) 默认 `com.apple.modelmanager` 对 `message_20_false/true` 返回 `ModelXPCRequest decode reached: Invalid number of keys found, expected one`；2) `com.apple.modelmanager.simulator` 对同样 body 只返回 `XPCErrorDescription: Connection interrupted`；3) `LoadAssetBundle` / `HoldAssetBundle` 已知先撞 `notSupportedOnExternalBuild`；4) 高层 `ModelManagerServices` Swift direct client surface 仍不可用，`PrewarmSession` 需要有效 session/internal state；5) searcher sub-agent 仍因 high demand 失败，本轮由主线程本地证据完成 | 结论: 本轮短期目标完成，verdict 为 `falsified`：当前 simulator/client-side route 不能作为不替换 daemon 的 `transitionAsset` dynamic-mode observation harness | 下一步: 复用已有可用的 client-side Frida precise capture 路线，测试私有 ANE load/compile traffic 是否随可控 client-side artifact/request mutation 变化
2026-06-22 23:06:12 +0800 | 目标: 复用已有 client-side Frida precise capture，比较 baseline vs `program+0xa8=1` 在 raw_prepare / IOConnect handoff 边界的事件与字段差异 | 动作: 1) 解析 `program_wrapper_a8_frida_attach_baseline_20260622.jsonl` 与 `program_wrapper_a8_frida_attach_a8_one_20260622.jsonl`；2) 新增 `mps/ANE/experiments/program_wrapper_a8_frida_trace_join.py`；3) 产出 `mps/ANE/.ane_runs/json/program_wrapper_a8_frida_trace_join_verdict_20260622.json` 和 CSV；4) 用 `python3 -m py_compile` 验证脚本；5) sub-agent `searcher` 本轮成功返回，确认了相同文件链和下一步建议 | 证据: 1) baseline/a8-one 都是 414 行 trace，事件计数一致；2) selector surface 一致：`{"4": 14}`；3) mutation 可见：raw_prepare / selector-4 input 的 `u32_0x30` 从 `0x00000000` 变为 `0x00000001`；4) raw_prepare ret 仍为 `3758097089/3758097090`，IOKit ret 仍为 `3758097090`；5) 没有出现 selector-9 | 结论: 本轮短期目标完成，verdict 为 `falsified`：`program+0xa8` 已能写入当前 visible raw_prepare buffer，但不改变 selector traffic 或 status surface，说明 retained-control 语义低于当前 selector-4 visible status 面 | 下一步: 做 selector-4 input buffer 字段级 diff，恢复 baseline vs a8-one 的具体变化 offset，并决定是继续尝试相邻字段 mutation 还是转向构造自然 selector-9 probe
2026-06-22 23:11:56 +0800 | 目标: 对 baseline vs `a8_one` 做 selector-4 IOConnect input / raw_prepare input 字段级 diff，判定当前 visible selector-4 input 是否还有未分类 lower-control 字段 | 动作: 1) 新增 `mps/ANE/experiments/selector4_input_field_diff.py`；2) 解析 `input_prefix_64b` 与 `prefix_56b_before`，按 4-byte little-endian word 对齐比较；3) 产出 `mps/ANE/.ane_runs/json/selector4_input_field_diff_verdict_20260622.json` 和 CSV；4) `python3 -m py_compile` 验证脚本 | 证据: 1) baseline/mutation 都有 `iokit_enter=7`、`raw_prepare_enter=10`；2) mutation offsets 为 `iokit_enter_input:0x8`、`iokit_enter_input:0x30`、`raw_prepare_input:0x30`；3) run-specific noise offsets 为 `0x0/0xc/0x18/0x1c/0x24/0x28/0x2c`；4) unclassified offsets 为空 | 结论: 本轮短期目标完成，verdict 为 `falsified`：selector-4 visible input 只暴露已知 a8/u32_0x30 变化和运行噪声，没有新的稳定 lower-control 字段 | 下一步: 构造或定位自然触发 selector-9 traffic 的 probe 路径，优先复查 `ane_bootkc_selector9_*`、`chaining_prepare_wrapper_preselector9`、`frida_selector9_patch_a614.js`
2026-06-22 23:21:31 +0800 | 目标: 构造或定位自然触发 selector-9 traffic 的 probe 路径，判断是否还有现成 unprivileged user-space selector-9 route 能移动 retained-control gate | 动作: 1) 汇总 `chaining_prepare_wrapper_preselector9_gate_verdict_20260621.json`、`selector9_iokit_interposer_negative_verdict_20260621.json`、`selector9_repeat_same_connection_two_case_verdict_20260621.json`、`selector9_direct_transport_boundary_verdict_20260622.json`、`selector9_direct_transport_codesign_blocker_verdict_20260622.json` 和 `frida_selector9_patch_a614.js`；2) 产出 `mps/ANE/.ane_runs/json/selector9_natural_probe_path_matrix_verdict_20260622.json` 与 CSV；3) reverse-engineer sub-agent 本轮返回空结果，主线程完成证据整合 | 证据: 1) exported `ANEServicesProgramChainingPrepare` wrapper 返回 `0x14` 且未驱动 selector-9；2) IOKit interposer 只有 header-only/empty JSON/killed probe；3) two-case same-connection selector-9 repeat 不改变 status/output；4) manual direct selector-9 transport 曾真实成立，但 baseline、`0xa614=1`、`qword10=current programHandle` 都停在 `0xe00002c2`；5) 当前 entitled selector-9 host 被 AMFI restricted-entitlement signature validation 卡住 | 结论: 本轮短期目标完成，verdict 为 `confirmed`：没有现成 unprivileged natural selector-9 probe 能同时自然产生 selector-9 并移动 gate；下一步不再追 wrapper/selector-4/a614 单点，而要恢复 direct selector-9 第二个 exact `0xe00002c2` gate 的 carrier/process state | 下一步: 从 `lookupProgramResource(*prepare_args+0x10, &process, 0)` 分支和 `qword0/u32_0x18/qword_0x10` 字段开始，恢复 direct selector-9 所需最小 process/carrier state
2026-06-22 23:26:24 +0800 | 目标: 恢复 direct selector-9 `0xe00002c2` gate 所需的 carrier/process state，区分 early validation family 与 later lookupProgramResource/process branch | 动作: 1) 汇总 `selector4_first_exact_0x2c2_gate_boundary_verdict_20260622.json`、`selector4_qword10_source_gap_verdict_20260622.json`、`selector4_input_0x30_lower_consumer_boundary_verdict_20260622.json`、`selector9_direct_transport_boundary_verdict_20260622.json`、`selector9_direct_transport_gate_probe_20260622.json`、`selector9_direct_transport_qword10_programHandle_20260622.json`；2) 产出 `mps/ANE/.ane_runs/json/direct_selector9_process_carrier_gate_verdict_20260622.json` 与 CSV | 证据: 1) early validation family (`0x38/0x3950/0xa614/0x3040`) 是真实 gate，但 `0xa614=1` 不移动 direct selector-9 的 `0xe00002c2`；2) `qword10=current programHandle` 和 daemon-layout `qword_0x10=1` 都不移动 `0xe00002c2`；3) selector-4 `input+0x30` / `program+0xa8` 不是直接 lower consumer；4) selector-4 真实 directly-read source family 是 `args+0x8/+0x10/+0x20` 和 writeback `+0x18` | 结论: 本轮短期目标完成，verdict 为 `confirmed`：direct selector-9 缺口是 semantically authored resource/process carrier tuple，而不是 `0xa614` 或 `qword10` 单字段 patch | 下一步: 恢复 ProgramCreate / InitialSetup 对 selector-4 `args+0x10/+0x18/+0x20/+0x8` 的语义 author/source，尤其是静态 `STR X1,[X0,#0x18]` programHandle author 和能流入 `qword_0x10` 的运行字段
2026-06-22 23:32:34 +0800 | 目标: 恢复 ProgramCreate / InitialSetup 对 selector-4 `args+0x10/+0x18/+0x20/+0x8` 与 direct selector-9 carrier 的语义 author/source | 动作: 1) 汇总 `selector4_qword10_source_gap_verdict_20260622.json`、`direct_selector9_process_carrier_gate_verdict_20260622.json`、`createinstance_process_args_seed_split_note.md`、`bootkc_memory_map_request_bridge_note.md`、`handle_registry_bridge_note.md`、`bootkc_493a0_request_key_bridge_probe.md`、`newinstance_convergence_candidate_verdict_20260619.json`；2) 产出 `mps/ANE/.ane_runs/json/programcreate_initialsetup_author_source_verdict_20260622.json` 与 CSV | 证据: 1) visible selector-4 `qword_0x10` 不是任意非零可用；2) create-instance process args split-seeded：`resource+0x493a0[0]`、hidden local handle/additional_params+0x18、visible client key；3) `additional_params+0x18` 是 hidden process-key sidecar；4) `InitialChecks` 写 `additional_params+0x60/+0x68` resource/process pair，并由 `ANERequest::init` 复制到 request+0x28/+0x30；5) resource+0x493a0 qword0 参与 request builder 与 device+0x98 cache coherence | 结论: 本轮短期目标完成，verdict 为 `confirmed`：direct selector-9 carrier 是 lower-authored resource/process/client tuple，无法由单 visible selector-4 field 或 programHandle surrogate 构成 | 下一步: 判断 `resource+0x493a0[0]` / `additional_params+0x60/+0x68` authoring 是否能由现有 user-space probe replay/synthesize；若不能，输出当前 unprivileged direct selector-9 route blocker package
2026-06-22 23:59:00 +0800 | 目标: 判断 `resource+0x493a0[0]` / `additional_params+0x60/+0x68` authoring 是否能由现有 user-space probe replay/synthesize，并输出当前 unprivileged direct selector-9 route blocker package | 动作: 1) 复核 `bootkc_memory_map_request_bridge_note.md`、`handle_registry_bridge_note.md`、`bootkc_add_client_binding_probe.md`、`shared_acceptance_note.md`；2) 接收并关闭 `doc-reader` 子代理，采纳其“直接 replay 未执行，不能硬判 falsified”的口径校正；3) 新增 `mps/ANE/.ane_runs/json/unprivileged_direct_selector9_route_blocker_20260622.json` 与 CSV，并将 verdict 收窄为 `inconclusive`、`direct_replay_probe_status=not_run`；4) 用 JSON/CSV parser 验证新产物 | 证据: 1) `InitialChecks` author `additional_params+0x60/+0x68` 并复制到 `request+0x28/+0x30`；2) `resource+0x493a0[0]` 属于 split-seeded resource/process/client tuple；3) accepted reuse 需要 driver wrapper registry + device resource/process registry；4) add-client 还需要 live client context、`isProcessValid`、process/code-sign/team-id/executable-path identity binding；5) `shared_acceptance_note.md` 仍显示 runtime-authorable accepted artifact/program body 未到达；6) 新 JSON 严格解析通过，CSV 6 行，statuses=`current_route_blocker/not_run` | 结论: 本轮短期目标完成但 verdict=`inconclusive`：current-route blocker package 已就位，现有 visible selector-4/direct selector-9 probes 没有证明可写入或重放 lower-authored tuple；但 capture+inject `{resource, process}` 的直接 replay/synthesize 实验未执行，不能宣称 definitive replay failure | 下一步: 做最小 replay feasibility probe：搜索/复用现有 harness 是否能捕获并注入 `additional_params+0x60/+0x68`；若不可行，转向追踪 `device+0x4f8` writer 以定位 accepted artifact/program authoring contract
2026-06-22 23:59:30 +0800 | 目标: 判断现有 harness 是否已足以直接 capture/replay `additional_params+0x60/+0x68` 或 `resource+0x493a0[0]`，避免下一轮基于不存在的注入能力设计实验 | 动作: 1) 委派并关闭 `searcher` 子代理搜索 ProgramCreate/InitialSetup/selector-4/selector-9 harness 与 Frida trace；2) 主线程复核 `frida_selector9_raw_prepare_trace.js`、`frida_selector9_patch_a614.js`、`program_wrapper_a8_frida_trace_join.py`、`selector4_input_field_diff.py` 与相关 verdict；3) 新增 `mps/ANE/.ane_runs/json/existing_harness_replay_feasibility_20260622.json` 与 CSV；4) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: 1) IOConnect hook 只抓 input 前 `0x40`、`u32_0x30` 与 output 前 24B；2) raw_prepare hook 只抓 `prefix_56b_before/after` 与 `u32_0x30_before/after`；3) `ANEServicesProgramCreate` 当前只有 dlsym/symbol-resolution 监控，没有参数 capture/inject；4) selector-9 patch harness 只改 descriptor+0xa614；5) `ANE_ProgramInitialSetup` / `ANE_ProcessCreate_gated` 是 bootkc/kernel 路径，不是当前 user-space Frida harness 可直接 hook 的普通函数；6) 新 JSON 严格解析通过，CSV 5 行 | 结论: 本轮短期目标完成，verdict=`falsified` 仅针对窄假设“现有 harness 已可直接 replay lower tuple”：现有 harness 不足以执行 `{resource, process}` replay；这不判死更深 artifact/program authoring contract | 下一步: 追踪 `device+0x4f8` / `resource+0x400d0` writer，优先复用 `ane_newinstance_acceptance_stage_join_probe.py` 与 shared acceptance 相关 bootkc static probes，判断 accepted artifact/program authoring contract 是否存在于当前 selector/contract 可达面
2026-06-22 23:59:45 +0800 | 目标: 追踪 `device+0x4f8` / `resource+0x400d0` acceptance state writer，判断 accepted artifact/program authoring contract 是否已经进入 selector/contract 可达面 | 动作: 1) 委派并关闭 `reverse-engineer` 子代理收集 bootkc static 证据；2) 主线程解析 `ane_bootkc_shared_acceptance_probe.csv`、`ane_bootkc_device_resource_registry_probe.csv`、`ane_bootkc_resource_gate_process_registry_probe.csv`、`ane_newinstance_acceptance_stage_join*.csv`；3) 复核已有 `ane_bootkc_resource_gate_first_author_probe.csv` 与 `bootkc_resource_gate_first_author_probe.md`；4) 新增并修订 `mps/ANE/.ane_runs/json/device4f8_resource400d0_writer_trace_20260622.json` 与 CSV | 证据: 1) `device+0x4f8` first writer 是 `ANEHWDevice::initializeANEProperties` at `0xfffffe00092e4474 str x0,[x19,#0x4f8]`；2) `ANE_ProgramCreate_gated` at `0xfffffe000928c26c` 通过 OSArray slot `+0x1e8` provisional insert resource；3) `resource+0x400d0` 是 process registry，`ANE_ProcessCreate_gated.cold.1` at `0xfffffe0009375834` 插入 `ANEProcess*`；4) first-author probe 证实 visible constructor/setup/load lifecycle target-covering positive stores=0；5) 唯一 exact `0x400d0` store 是 `ANEProgramResource::free` at `0xfffffe00093050f4 str xzr,[x24,#0xd0]` destructor clear | 结论: 本轮短期目标完成，verdict=`inconclusive`：`device+0x4f8` writer 和 `resource+0x400d0` process-entry writer 已定位，但 `resource+0x400d0` pointer first positive author 仍未知；accepted artifact/program contract 未被证明可由当前 visible route author | 下一步: 追 `resource+0x400d0` deeper materializer，优先 helper call、bulk-copy path、或 visible resource setup 后 / lookup-process-create 前的 device/scheduler registration
2026-06-23 00:10:00 +0800 | 目标: 追 `resource+0x400d0` pointer first positive author 的 deeper materializer，验证 helper/direct/bulk/host-surface 是否已有正向 writer | 动作: 1) 委派 `reverse-engineer` 子代理做只读事实收集；2) 主线程解析 `resource_gate_first_author`、`cluster_memmove`、`cluster_sink`、`helper_graph`、`indirect_callee`、`preinit_boundary`、`host_stack` 等现有 CSV/Markdown；3) 新增 `mps/ANE/.ane_runs/json/resource400d0_deeper_materializer_boundary_20260623.json` 与 CSV；4) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: 1) visible constructor/setup/create/load lifecycle 对 `resource+0x400d0` target-covering positive store count=0；2) 唯一 exact target-covering store 是 `ANEProgramResource::free` teardown clear；3) `resource+0x400c0..0x40100` 的 `memcpy/memmove/bzero/memset` scans 报 `window_hits=0 target_hits=0`；4) host-stack note 明确 no visible positive direct-store author in H16 and no visible target-covering load/store/bulk/inline-allocation surface in HAL | 结论: 本轮短期目标完成，verdict=`inconclusive`：deeper materializer 未找到，但 visible helper/direct/bulk materializer hypothesis 被显著削弱；`resource+0x400d0` first positive author 更可能位于 lower runtime-owned registration/materializer phase 或当前 scans 未覆盖 path | 下一步: 在 `record+0x1b8` durable author、`process+0x203fc` lifecycle author、dynamic timing probe 之间选择最小下一层 target
2026-06-23 00:18:00 +0800 | 目标: 在 `record+0x1b8` durable author、`process+0x203fc` lifecycle author、dynamic timing probe 之间选择最小下一层 target | 动作: 1) 委派并关闭 `doc-reader` 子代理压缩 process-state 与 restore-record 笔记；2) 主线程复核 `restore_record_raw_send_boundary_note.md`、`restore_record_copy_bound_note.md`、`restore_record_author_path_note.md`、`process_state_and_record_author_tightening_note.md` 与对应 CSV；3) 新增 `mps/ANE/.ane_runs/json/next_lower_target_priority_20260623.json` 与 CSV；4) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: 1) `process+0x203fc` state-2 provenance 已低于 visible H16 store/helper/copy surface；2) `record+0x1b8` exact visible stores 在 ProgramLoad / ANE_RestoreState / Legacy load / ProgramReMap 中为 0；3) Legacy memmove 是 small mode-sized prefix copy，不覆盖 `record+0x1b8`；4) `ANE_RestoreState -> aneCmdSend(raw)` 后到 `record+0x1b8` read 的 visible interval 极短，无独立 visible store/call | 结论: 本轮短期目标完成，verdict=`confirmed`：下一层最窄 target 是 `record+0x1b8` durable author；`process+0x203fc` 暂缓，因为其 state-2 可能依赖 record/table 或 firmware-driven lifecycle state | 下一步: 准备最小 raw-send boundary probe plan，比较 `ANE_RestoreState::aneCmdSend(raw)` 前后 selected restore record 的 `record+0x1b8`
2026-06-23 00:22:00 +0800 | 目标: 准备最小 `record+0x1b8` raw-send boundary probe plan，比较 `ANE_RestoreState::aneCmdSend(raw)` 前后 selected restore record 的 state word | 动作: 1) 复核 `ane_bootkc_restore_record_raw_send_boundary_probe.csv`、`restore_record_raw_send_boundary_note.md`、`restore_record_copy_bound_note.md`；2) 新增 `mps/ANE/.ane_runs/json/record1b8_raw_send_boundary_probe_plan_20260623.json` 与 CSV；3) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: 1) `0xfffffe00092c1d34 csel x1,...` finalizes `x1=selected_record_ptr`；2) `0xfffffe00092c1d60 bl aneCmdSend(raw)` 是 pre-send boundary；3) `0xfffffe00092c1d74 smaddl x8,...` post-send recomputes selected record pointer；4) `0xfffffe00092c1d78 ldr w8,[x8,#0x1b8]` reads the state word；5) `0xfffffe00092c1d7c str w8,[x23,#0x2f0]` mirrors it to `resource+0x402f0` | 结论: 本轮短期目标完成，verdict=`confirmed`：probe plan 已明确单一 state word、两个读点和 pass/fail；execution_status=`plan_only_not_run`，没有执行 restricted kernel/firmware dynamic observation | 下一步: 判断是否存在安全可授权的动态观察路径；若没有，继续静态恢复 `aneCmdSend(raw)` 以下的 firmware-return / completion / table-population path
2026-06-23 00:30:00 +0800 | 目标: 判断 `record+0x1b8` raw-send boundary probe 是否能在当前机器安全动态执行 | 动作: 1) 委派 `reverse-engineer` 子代理做只读动态可行性事实收集；2) 主线程复核 runtime harness boundary、Frida/userland trace、SIP/dtrace、本机 daemon/ANE 进程与 raw-send packaging 证据；3) 新增 `mps/ANE/.ane_runs/json/record1b8_dynamic_observation_feasibility_20260623.json` 与 CSV；4) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: 1) runtime harness 太高层，不能读 `record+0x1b8` pre/post-send；2) Frida 当前适合 ANEServices/IOConnect 用户态 surface，不适合 bootkc/kernel `ANE_RestoreState` 读点；3) SIP enabled，最小 dtrace probe 报 `DTrace requires additional privileges`；4) protected daemon attach 既有证据为 denied；5) `aneCmdSend(raw)` 只做 stack-local command/callback packaging，并 forward 到 `aneFirmwareCommandSend(...)` | 结论: 本轮短期目标完成，verdict=`falsified`：当前机器/工具约束下不能安全执行 `record+0x1b8` raw-send dynamic probe；probe plan 保留但不运行 | 下一步: 静态恢复 `aneFirmwareCommandSend(...)` 及其 callback/completion/replay path，寻找 `record+0x1b8` 或 alias (`resource+0x402f0` / gate-owned `+0x220`) 的 author
2026-06-23 00:36:00 +0800 | 目标: 静态恢复 `aneCmdSend(raw)` 以下的 `aneFirmwareCommandSend(...)` boundary，判断 visible firmware-send body 是否 author `record+0x1b8` 或 alias | 动作: 1) 解析 `ane_bootkc_raw_send_packaging_probe.csv`、`ane_bootkc_command_state_materialization_probe.csv`、`ane_bootkc_legacy_typed_submit_route_probe.csv`、`ane_bootkc_command_state_callback_family_probe.csv`、`ane_bootkc_legacy_typed_completion_route_probe.csv`、`ane_bootkc_completion_cleanup_join_probe.csv`、`ane_bootkc_post_send_replay_boundary_probe.csv`；2) 新增 `mps/ANE/.ane_runs/json/ane_firmware_command_send_static_boundary_20260623.json` 与 CSV；3) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: 1) `aneCmdSend(raw)` stack-packages command/callback and forwards to `aneFirmwareCommandSend`；2) `aneFirmwareCommandSend` tracks `OSValueObject<ANEFirmwareCommandState>` wrapper while mutating inner payload at `wrapper+0x10`；3) first visible submit is `IOProcessorChannelSendRetry`；4) callback shell is `commandWakeup`-style, not direct lower-state author；5) after submit, `handleOutstandingCommand` owns structured completion route; cleanup joins to `client_ctx+0x18 -> ANE_ProcessDestroy_gated -> resource+0x400d0 removeObject` | 结论: 本轮短期目标完成，verdict=`inconclusive`：visible `aneFirmwareCommandSend` does not expose direct `record+0x1b8` / alias author；remaining gap is now submit-status / reply / completion / manager-cleanup side effects | 下一步: 静态恢复 `handleOutstandingCommand` / completion route，聚焦 status write、optional copyback/free、resource lookup、callback sink、manager cleanup 是否 author durable lower state
2026-06-23 00:42:00 +0800 | 目标: 静态恢复 `handleOutstandingCommand` / visible typed completion route，判断其是否 author `record+0x1b8` 或 alias | 动作: 1) 解析 `ane_bootkc_legacy_typed_completion_route_probe.csv`、`ane_bootkc_completion_cleanup_join_probe.csv`、`ane_bootkc_completion_process_counter_probe.csv` 与相关 notes；2) 新增 `mps/ANE/.ane_runs/json/typed_completion_no_record_author_boundary_20260623.json` 与 CSV；3) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: 1) visible completion facts 包括 `inner_record+0x58` completion_status、`inner_record+0x88` callback sink、resource lookup key、wakeup plumbing、manager cleanup；2) 没有 visible direct `record+0x1b8` read/write；3) 没有 visible gate `+0x220` replay 或 `resource+0x402f0` writeback；4) cleanup join 进入 `client_ctx+0x18 -> ANE_ProcessDestroy_gated -> resource+0x400d0 removeObject`；5) completion path touch `process+0x20400` wake/counter state，但不是 `process+0x203fc` state-2 author | 结论: 本轮短期目标完成，verdict=`falsified`：visible typed completion route 不是 durable lower-record author；missing authority below visible completion bookkeeping/callback/wakeup shell | 下一步: 恢复 firmware request/reply payload semantics 或 lower reply-publish/completion side effects；若仍不可见，准备把当前层 blocker 表述为 firmware-private reply semantics
2026-06-23 02:18:00 +0800 | 目标: 在 firmware request/reply payload semantics 与 lower reply-publish/completion side effects 之间选择下一层最窄 target | 动作: 1) 委派并关闭 `doc-reader` 子代理压缩 submit/completion/command-state/cleanup/post-send notes 与 CSV；2) 主线程复核 `ane_firmware_command_send_static_boundary_20260623.json`、`typed_completion_no_record_author_boundary_20260623.json` 和 `ane_bootkc_*submit*/*completion*/*command_state*/*post_send*` CSV；3) 新增 `mps/ANE/.ane_runs/json/firmware_reply_vs_completion_priority_20260623.json` 与 CSV；4) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: 1) completion payload `+0x50/+0x68/+0x88` 仍是 carrier/lookup/callback bookkeeping；2) firmware payload semantics 没有 concrete grammar/handler/reply field 证据；3) restore-side send 后 replay `record+0x1b8` 并 mirror 到 `resource+0x402f0`；4) unload-side post-send 进入 `device slot+0x9c0 -> 0x927d410` family；5) cleanup/counter 证据连接到 `client_ctx+0x18 -> ANE_ProcessDestroy_gated -> resource+0x400d0` 与 `process+0x20400` | 结论: 本轮短期目标完成，verdict=`confirmed`：下一轮最窄 target 是 lower reply-publish/completion side effects，具体为 unload-side post-send `device slot+0x9c0 -> 0x927d410` family；firmware payload semantics 保留为 fallback | 下一步: 静态 probe unload-side post-send `device slot+0x9c0 -> 0x927d410` family，并与 restore-side `record+0x1b8 -> resource+0x402f0` replay 对照，判定其是否触及 `record+0x1b8`、`process+0x203fc`、`process+0x20400`、gate `+0x220` 或 `resource+0x402f0`
2026-06-23 02:32:00 +0800 | 目标: 静态 probe unload-side post-send `device slot+0x9c0 -> 0x927d410` family，并与 restore-side replay 对照 | 动作: 1) 委派并关闭 `reverse-engineer` 子代理收集 bootkc static evidence；2) 委派并关闭 `ida` 子代理验证当前 `aned_bin.i64` IDB 边界，确认它是 user-space daemon 而非 H16 kext；3) 主线程复核 `ane_bootkc_unload_postsend_revalidation_probe.csv`、`ane_bootkc_program_valid_gate_probe.csv`、`ane_bootkc_process_state_window_probe.csv`、`ane_bootkc_programpartialunwire_state_join_probe.csv`；4) 新增 `mps/ANE/.ane_runs/json/unload_postsend_revalidation_boundary_20260623.json` 与 CSV；5) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: 1) restore post-send read `record+0x1b8` at `0xfffffe00092c1d78` and write `resource+0x402f0` at `0xfffffe00092c1d7c`; 2) ProgramUnload post-send enters `device slot+0x9c0` then `0x927d410`; 3) `+0x9c0` resolves to `ANEHWDevice::isProgramValid`; 4) `0x927d410` resolves to `ANEHWDevice::isProcessValid`; 5) `isProcessValid` reads `process+0x203fc`, while known H16 writers only prove 0/1/init state; 6) daemon IDB does not contain the H16 kext target offsets | 结论: 本轮短期目标完成，verdict=`inconclusive`：unload post-send family 已从 unknown slot 收缩成 `ProgramUnload -> isProgramValid -> isProcessValid(mode=1) -> cold continuation`，但未找到 durable lower-state author | 下一步: probe `ProgramUnload` cold continuation `0xfffffe000928275c` 与 `isProcessValid` return path，寻找 `process+0x203fc == 2` author、`record+0x1b8` replay 或新的 firmware/private completion handoff
2026-06-23 02:45:00 +0800 | 目标: probe `ProgramUnload` cold continuation `0xfffffe000928275c` 与 `isProcessValid` return path，寻找 state-2 author、record replay 或 firmware/private handoff | 动作: 1) 委派并关闭 `reverse-engineer` 子代理确认 existing evidence gap；2) 新增并运行 `mps/ANE/experiments/ane_bootkc_programunload_cold_continuation_probe.py`；3) 解析 `ane_bootkc_programunload_cold_continuation_probe.csv`，并补局部反汇编确认 `0x2f0` 命中是 static table offset；4) 符号解析 `0xfffffe00092bd74c` 为 `ANEFirmwareManager::sendSetupCmd`；5) 新增 `mps/ANE/.ane_runs/json/programunload_cold_continuation_firmware_handoff_20260623.json` 与 CSV；6) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: 1) cold continuation window counts=`target_hits=2 stores=13 loads=17 calls=4 branches=14`; 2) `0xfffffe000928277c/0xfffffe00092827b4` 的 `#0x2f0` 是 static table add，不是 `resource+0x402f0`; 3) `0xfffffe000928289c` 调用 `ANEFirmwareManager::sendSetupCmd`; 4) 局部调用形态为 `sendSetupCmd(0x401, [sp+0x48], 0)`; 5) `isProcessValid` return window 只读 `process+0x203fc`，不 author state-2; 6) process-state source provenance 仍为 init/0/1 且 `const_two_source_count=0` | 结论: 本轮短期目标完成，verdict=`confirmed`：visible ProgramUnload/isProcessValid shell 不是 CPU-side durable author，下一层收敛到 firmware setup command handoff | 下一步: 恢复 `ANEFirmwareManager::sendSetupCmd(0x401)` 的 request/reply payload semantics，尤其是 `[sp+0x48]` payload layout 与其 completion side effect 是否解释 `process+0x203fc == 2` / `record+0x1b8`
2026-06-23 03:04:24 +0800 | 目标: 恢复 `ANEFirmwareManager::sendSetupCmd(0x401, sp+0x48, 0)` payload / reply semantics，判断它是否是 visible CPU-side durable state carrier | 动作: 1) 复测 direct `ida-pro-mcp`，transport 已恢复但当前无 open IDB session；当前会话未暴露 `spawn_agent`，无法新建 `agent_type=ida` sub-agent；2) 新增并运行 `mps/ANE/experiments/ane_bootkc_sendsetup401_payload_probe.py`；3) 反汇编 `sendSetupCmd` 与 `ProgramUnload` callsite/consumer 窗口；4) 生成 `mps/ANE/.ane_runs/json/sendsetup401_payload_semantics_20260623.json`、`mps/ANE/.ane_runs/csv/sendsetup401_payload_semantics_20260623.csv` 与 instruction CSV，并用 `jq` / `csv.DictReader` 验证 | 证据: 1) `ProgramUnload` 调用 `sendSetupCmd(0x401, [sp+0x48], 0)`，`x3=0`; 2) `sendSetupCmd(0x401)` 分配 `0x0c` payload，只写 `payload+0x08 = *arg1`; 3) 唯一 `*arg2` 读取属于 `0x403` path; 4) success copyback 只覆盖 `0x400 -> *arg1` 与 `0x402 -> *arg2`，`0x401` 无 payload copyback; 5) `ProgramUnload` 调用后只消费 `x0` status，不消费 reply word; 6) feature-disabled fallback 构造 typed command `0x201` 并预置 `*[sp+0x48] = -1` | 结论: 本轮短期目标完成，verdict=`falsified`：`sendSetupCmd(0x401)` reply word 不是 visible CPU-side durable state carrier，不能解释 `process+0x203fc == 2`、`record+0x1b8` 或 `resource+0x402f0` | 下一步: 比较 feature-enabled `0x401` 与 typed fallback `0x201` / raw-send completion boundary，判断 unload durability 是否完全 firmware-private，或仍有 H16 visible status side effect
2026-06-23 03:10:39 +0800 | 目标: 比较 feature-enabled `0x401` 与 typed fallback `0x201` unload setup pair，判断 visible H16 wrapper 层是否存在 status 以外的 side effect | 动作: 1) 新增并运行 `mps/ANE/experiments/ane_bootkc_unload_setup_pair_probe.py`；2) 反汇编 `ProgramUnload` setup pair、`sendSetupCmd` copyback checks、raw sender、typed sender；3) 生成 `mps/ANE/.ane_runs/json/unload_setup_pair_status_only_20260623.json`、`mps/ANE/.ane_runs/csv/unload_setup_pair_status_only_20260623.csv` 与 instruction CSV；4) 用 `jq` 和 `csv.DictReader` 验证 verdict 与行结构 | 证据: 1) feature path 使用 command `0x401`，payload size `0x0c`，无 post-send copyback; 2) fallback path 构造 typed command `0x201`，payload size `0x0c`; 3) fallback send 前写 `*[sp+0x48] = -1`，不是 send 后 reply; 4) fallback 调用 `ANEHWDevice::aneCmdSend(ANEFirmwareCommand)`; 5) raw/typed sender wrapper 都返回 `x20 -> x0` status; 6) 两条 path join 到 `ProgramUnload` 的 `x0` status consumer | 结论: 本轮短期目标完成，verdict=`falsified`：`0x401/0x201` unload setup pair 在 visible H16 wrapper 层不是 durable-state author | 下一步: 下沉到 command-specific firmware submit/completion boundary，检查 command `0x201/0x401` 是否还有 H16-visible consumer/reply publish；若仍无，准备 firmware-private blocker package
2026-06-23 03:18:53 +0800 | 目标: 检查 command `0x201/0x401` 在 lower firmware submit/completion path 中是否有 H16-visible command-specific consumer、reply publish 或 target-state side effect | 动作: 1) 新增并运行 `mps/ANE/experiments/ane_bootkc_unload_command_specific_completion_probe.py`；2) 用 Capstone operand detail 扫描 H16 `__TEXT_EXEC` exact immediate `0x201/0x401`；3) 聚焦扫描 `aneFirmwareCommandSend`、`IOProcessorChannelSendRetry`、`handleOutstandingCommand` lower windows；4) 生成 `mps/ANE/.ane_runs/json/unload_command_specific_completion_20260623.json`、`mps/ANE/.ane_runs/csv/unload_command_specific_completion_20260623.csv` 与 instruction CSV；5) 用 `jq` 和 `csv.DictReader` 验证 | 证据: 1) exact command immediate hits=18; 2) `IOProcessorChannelSendRetry` command-specific hits=0; 3) `handleOutstandingCommand` command-specific hits=0; 4) lower submit/completion consumer hits=0; 5) `aneFirmwareCommandSend+0xfc0` 的 exact `0x201` 是 `os_log` address offset，不是 command consumer; 6) command builders 仍集中在 Release/Unload/setup/load wrappers | 结论: 本轮短期目标完成，verdict=`falsified`：command `0x201/0x401` 在 H16-visible lower submit/completion path 中没有 command-specific consumer | 下一步: 准备 firmware-private blocker package，串联 no visible `0x401` copyback、no visible `0x201/0x401` wrapper side effect、no lower H16 command-specific submit/completion consumer，并明确下一控制层需求
2026-06-23 03:22:16 +0800 | 目标: 准备 visible H16 unload durability layer firmware-private blocker package，并明确下一控制层需求 | 动作: 1) 新增 `mps/ANE/.ane_runs/json/unload_firmware_private_blocker_20260623.json` 与 CSV；2) 串联最近证据包：`sendsetup401_payload_semantics`、`unload_setup_pair_status_only`、`unload_command_specific_completion`、`programunload_cold_continuation_firmware_handoff`、`record1b8_dynamic_observation_feasibility`; 3) 用 `jq` 与 `csv.DictReader` 验证 package | 证据: 1) no visible `0x401` reply-word copyback; 2) no visible `0x201/0x401` wrapper side effect beyond status; 3) no lower H16 command-specific submit/completion consumer; 4) visible ProgramUnload/isProcessValid shell 不是 durable author; 5) 当前机器没有安全 boot-kernel dynamic observation path | 结论: 本轮短期目标完成，verdict=`confirmed`：visible H16 unload durability/control layer 已可判死；remaining authority 下沉到 firmware-private command/reply semantics 或更低 reply-publish path；long_term_status=`not_complete` | 下一步: 选择下一控制层获取路线：firmware-side command/reply handler recovery、安全低层动态观测、或 non-H16 carrier 搜索
2026-06-23 03:26:42 +0800 | 目标: 在 firmware-side handler recovery、安全低层动态观测、non-H16 carrier 搜索三条路线中选择下一控制层最小可验证入口 | 动作: 1) 搜索本机系统路径与现有 `.ane_runs` artifacts；2) 新增 `mps/ANE/.ane_runs/json/next_control_layer_route_selection_20260623.json` 与 CSV；3) 用 `jq` 与 `csv.DictReader` 验证 route-selection package | 证据: 1) 系统路径搜索只见 ANE 日志/模型资产，没有明显可直接分析的 `0x201/0x401` firmware handler blob; 2) safe low-level dynamic observation 已由 `record1b8_dynamic_observation_feasibility_20260623` 判定当前机器不可安全执行; 3) non-H16 carrier 搜索有现成 ANEServices/aned/IOConnect traces、selector carrier verdicts、daemon-chain CSV 与 `mps/ANE/experiments/aned_bin.i64` | 结论: 本轮短期目标完成，verdict=`confirmed`：选择 `non_h16_carrier_search` 作为下一控制层获取路线 | 下一步: 从 `aned_bin.i64` 与现有 selector/daemon-chain CSV 查找 firmware-published durable state 是否上浮到 user-space daemon/request/descriptor carrier
2026-06-23 03:32:36 +0800 | 目标: 执行 `non_h16_carrier_search` 初筛，判断 user-space daemon bridge 是否暴露 firmware-published durable state carrier | 动作: 1) 通过 `ida-pro-mcp` 打开 `mps/ANE/experiments/aned_bin.i64` 为 `aned_bin_user_space`; 2) 执行 minimal `survey_binary`; 3) 查询 program/resource/process/unload/destroy/descriptor/state/reply/completion 字符串与 `_ANEProgramForLoad` 函数面；4) 反编译 `destroyProgramInstance`、`createProgramInstanceForModel:...`、`_ANEServer unloadModel:options:qos:withReply:`；5) 新增 `mps/ANE/.ane_runs/json/non_h16_carrier_initial_surface_20260623.json` 与 CSV 并验证 | 证据: 1) IDA open 成功，`aned_bin` 521 functions / 978 strings; 2) `_ANEProgramForLoad` 暴露 `programInstance/programHandle` 等 daemon/cache carrier; 3) `destroyProgramInstance` 日志面包含 `controller.device/programInstance/refcount` 与 final `ok/controller.device`; 4) `createProgramInstanceForModel` 日志面包含 `programHandle/intermediateBufferHandle/queueDepth/numInputs/numOutputs/refcount/wiredMemory`; 5) 初筛未找到 `0x201/0x401` durable-state echo | 结论: 本轮短期目标完成，verdict=`inconclusive`：non-H16 surface 有继续价值，但第一轮只证明 wrapper/cache carrier，尚未证明 replayable firmware-published state carrier | 下一步: 检查 `_ANEProgramForLoad destroyProgramInstance` 与 `createProgramInstanceForModel:...` 的 native ANEProgramDestroy/Create call boundary，定位 exact carrier 与 output struct 是否含可复用 state word
2026-06-23 03:50:58 +0800 | 目标: 检查正确 arm64e slice 上 `_ANEProgramForLoad destroyProgramInstance` 与 `createProgramInstanceForModel:...` 的 native ANEProgramDestroy/Create boundary 是否暴露 replayable lower-state carrier | 动作: 1) 发现 `aned_bin` 为 x86_64/arm64e universal，当前 `aned_bin_user_space` IDA session 是 x86_64；2) 抽取 `mps/ANE/experiments/aned_bin_arm64e_20260623` 并打开为 `aned_bin_arm64e_user_space`；3) 分析 `-[_ANEProgramForLoad destroyProgramInstance]`、`sub_100006294`、`createProgramInstanceForModel:...`、`sub_100002EB0`；4) 新增 `mps/ANE/.ane_runs/json/non_h16_native_boundary_carrier_20260623.json` 与 CSV | 证据: 1) destroy block 在 `0x1000062e4` 调 `programInstance` vtable `+0x18`，只消费 status 并清 `programInstance/refcount/txn`; 2) create block 在 `0x1000035d0` 调 `controller.device` vtable `+0x10`，成功后只写 `programHandle/intermediateBufferHandle/queueDepth/numInputs/numOutputs/refcount/wiredMemory`; 3) prepare `0x1000039c0` 与 cleanup destroy `0x100003a28` 都是 status-only；4) 未发现比 wrapper/cache handles 更低的 reusable word/tuple | 结论: 本轮短期目标完成，verdict=`falsified`：arm64e `_ANEProgramForLoad` create/destroy native boundary 不是 firmware-published durable carrier surface；long_term_status=`not_complete` | 下一步: 检查 `_ANEServer unloadModel:options:qos:withReply:` 与相邻 daemon/IOConnect unload carrier，判断 unload path 是否上浮非 wrapper 的 reusable lower-state carrier
2026-06-23 04:08:30 +0800 | 目标: 检查 arm64e `_ANEServer unloadModel:options:qos:withReply:` 与相邻 `_ANEProgramCache` unload path 是否暴露非 wrapper 的 reusable lower-state carrier | 动作: 1) 分析 `-[_ANEServer unloadModel:options:qos:withReply:]` at `0x10001bea8`; 2) 追到 `+[_ANEProgramCache removeProgramForConnection:model:bundleID:]`、`sub_1000016DC`、`-[_ANEProgramForLoad removeCachedReference]`、`sub_10000266C`、`-[_ANEProgramForLoad dealloc]`; 3) 新增 `mps/ANE/.ane_runs/json/non_h16_unload_carrier_20260623.json` 与 CSV | 证据: 1) unloadModel 核心 callsite `0x10001cc74` 只是 `removeProgramForConnection:model:bundleID:`，没有直接 native/IOConnect call; 2) `sub_1000016DC` 做 cache key lookup、removeCachedReference、programHandle telemetry、dictionary removal; 3) `sub_10000266C` 只递减 refcount，不 destroy; 4) dealloc 在 `0x100002188` / `0x100002230` 调 `programInstance` vtable `+0x10/+0x18`，返回值只作为 status 并清 wrapper 字段 | 结论: 本轮短期目标完成，verdict=`falsified`：daemon unload/cache path 没有上浮 firmware-published durable carrier；long_term_status=`not_complete` | 下一步: 定位 `controller.device` / `programInstance` vtable slots 的 provider 与实现边界，判断 next lower user-space implementation 是否在本机 linked framework 中可见，或已越出 `aned` 可见层
2026-06-23 04:22:00 +0800 | 目标: 定位 `controller.device` / `programInstance` vtable slots 的 provider 与实现边界，判断 next lower user-space implementation 是否本机可见 | 动作: 1) 确认 `aned_bin_arm64e_20260623` 中 `_ANEDeviceController` 从 `AppleNeuralEngine.framework` 导入；2) 打开 `/Volumes/2T/dsc_arm64e_extract/.../AppleNeuralEngine.i64` 与 `ANEServices.i64`; 3) 分析 `_ANEDeviceController start/stop`、`ANEServicesDeviceOpen/Close`、`_ANEServicesProgramCreate/Prepare/Stop/Destroy` 和 `ANEServicesDevice::ANE_Program*`; 4) 新增 `mps/ANE/.ane_runs/json/non_h16_vtable_provider_boundary_20260623.json` 与 CSV | 证据: 1) AppleNeuralEngine `_ANEDeviceController start` block `0x19f9449a0` dlopen/dlsym `ANEServicesDeviceOpen` 并 `setDevice:`; 2) `ANEServicesDeviceOpen` at `0x19e6abc2c` 创建/打开 services device、request receiver 并加载 firmware; 3) create/prepare/unprepare/destroy 分别落到 `IOConnectCallStructMethod` selectors `3/4/5/6`, callsites `0x19e69d184/0x19e69d5c0/0x19e69d980/0x19e69db10` | 结论: 本轮短期目标完成，verdict=`confirmed`：vtable provider 已定位到 `AppleNeuralEngine -> ANEServices -> IOConnect selectors 3/4/5/6`; long_term_status=`not_complete` | 下一步: 分析 selector 3 create 与 selector 6 destroy 的 payload/copyback 语义，尤其 `ANEProgramCreateArgsOutput` 与 `ANEProgramDestroyArgs` 是否包含可复用 lower-state carrier
2026-06-23 04:35:50 +0800 | 目标: 分析 ANEServices selector 3 create 与 selector 6 destroy 的 payload/copyback 语义，判断 `ANEProgramCreateArgsOutput` / `ANEProgramDestroyArgs` 是否暴露可复用 lower-state carrier | 动作: 1) 用 `ida-pro-mcp` 复核 `ANE::ANEServicesDevice::ANE_ProgramCreate` at `0x19e69d07c` 与 `ANE::ANEServicesDevice::ANE_ProgramDestroy` at `0x19e69da28`; 2) 串联既有 raw selector-3 output sentinel note、selector3 live-handle coherence note、ProgramCreate/InitialSetup split-seeded authority verdict; 3) 新增 `mps/ANE/.ane_runs/json/selector3_6_payload_copyback_boundary_20260623.json` 与 CSV | 证据: selector-3 构造 `{args_ptr,0xd88,output_ptr,0xac738}` 0x20-byte descriptor 后调用 `IOConnectCallStructMethod(selector=3, outputStruct=NULL)`；raw selector-3 status=0 时 caller-visible `0xac738` output buffer 预填 `0xA5` 后 `diff_count=0`；patch live `programHandle/queueDepth` 仍不能让 selector-4 脱离 intermediate family；selector-6 只发 0x10 input 且无 output/copyback，日志仅 `progHandle` | 结论: 本轮短期目标完成，verdict=`falsified`：ANEServices-visible selector 3/6 boundary 不暴露可 replay/reset/rebuild 的 durable lower-state carrier；long_term_status=`not_complete` | 下一步: 贴着 selector-3 lower user-client/resource-registry handling 找 split resource/process/client tuple 的 author/copyback 点，或连接既有 H16/user-client blocker 证据后上抬 blocker
2026-06-23 04:42:59 +0800 | 目标: 连接 selector-3 下方 user-client/resource-registry 既有证据，选择 split resource/process/client tuple 的下一最小 author/copyback target | 动作: 1) 聚焦读取 `createinstance_process_args_seed_split_note.md`、`process_resource_key_seed_join_note.md`、`resource_493a0_producer_to_import_join_note.md`; 2) 串联 `programcreate_initialsetup_author_source_verdict_20260622`、`resource400d0_deeper_materializer_boundary_20260623`、`unprivileged_direct_selector9_route_blocker_20260622`、本轮 selector3/6 payload-copyback verdict; 3) 新增 `mps/ANE/.ane_runs/json/selector3_lower_author_target_selection_20260623.json` 与 CSV | 证据: create-instance path 明确 `process_args[0] <- resource+0x493a0[0]`、`process_args[8] <- hidden local handle/local_y`、`process_args[16] <- visible client key`; later copyback 为 `resource+0x493a0 -> external output` 且 `local_y -> external_output[0]/params[0]`; producer/import 链已连接成 base load-side external output -> `resource+0x493a0` -> later create-instance import；visible selector-4/direct selector-9 与 ANEServices selector-3/6 均未给出 replay path | 结论: 本轮短期目标完成，verdict=`confirmed`：下一最小 target 是 raw selector-3 status=0 path 与 base load-side `resource+0x493a0` producer/import 链的关系，而不是 wrapper output 或 selector-6 destroy | 下一步: 判定 raw selector-3 success 是跳过 producer chain、到达 producer chain 但 split hidden-handle/client tuple 不一致，还是进入另一个 no-publish path
2026-06-23 04:47:17 +0800 | 目标: 判定 raw selector-3 `status=0/output untouched` 与 base load-side `resource+0x493a0` producer chain 的关系 | 动作: 1) 聚焦读取 `selector3_ready_gate_transport_match_note.md`、`raw_selector3_wrapper_internal_state_note.md`、`selector3_request_layout_compare_note.md`、`program_create_registry_timing_note.md`; 2) 对照 forced-ready trace 与 raw output sentinel/internal-windows JSON; 3) 新增 `mps/ANE/.ane_runs/json/raw_selector3_ready_gate_producer_skip_20260623.json` 与 CSV | 证据: default rawCreate `status=0` 是 ready-gate short-circuit 且无 selector-3 send；raw create 构造 wrapper/payload/device graph 但 `service_ready_u8_0x18=0`; 强制 ready 后真实 selector-3 public transport 发出，`input_size=0x20` 且返回 `0xe00002c2`; ProgramCreate 的 `resource+0x493a0` producer 依赖 pending registry insert 后的 resource vtable `+0x138` subclass load path | 结论: 本轮短期目标完成，verdict=`confirmed`：raw selector-3 `status=0/output untouched` 跳过 base load-side `resource+0x493a0` producer chain；forced-ready 进入 public transport 但缺 accepted pre-stage | 下一步: 定位 `service_ready_u8_0x18` / `service+0x18` ready-gate author，判断它是否可 replay/reset/rebuild，或并入 lower formal blocker
2026-06-23 04:56:31 +0800 | 目标: 定位 `service_ready_u8_0x18` / `service+0x18` ready-gate author 与 selector-3 accepted pre-stage，判断是否可从当前 user-space/control-layer replay | 动作: 1) 读取 `ready_gate_natural_author_verdict_20260619`、`non_direct_route_reachability_verdict_20260619`、hinted-open 三轮 verdict 与 `open_reply_ready_byte_alignment_note.md`; 2) 用 `ida-pro-mcp` 复核 `ANE::ANEServicesDevice::ANEDeviceOpen` at `0x19e69c71c`; 3) 新增 `mps/ANE/.ane_runs/json/ready_gate_author_entitlement_blocker_20260623.json` 与 CSV | 证据: IDA 确认 selector-0 open reply `+0x1c` 在 `0x19e69c8b4/0x19e69c8b8` 被复制到 `service+0x18`; 正确形状的 successful local open reply 自身携带 `+0x1c=0`; natural author 链为 `ANEClientInfo+0x10 -> device+0x28 -> reply+0x1c -> service+0x18`; 当前 successful local route 是 usageType=1 direct path 并自然 ready=0; usageType/mode=3 non-direct sweeps 返回 `0x18`; hinted/private open 在 crash、ABI correction、ad-hoc entitlement 后仍无正常 status/device route | 结论: 本轮短期目标完成，verdict=`confirmed`：ready-gate author 不是当前 wrapper/control layer 可 replay 的状态迁移，已收敛为 entitlement-gated higher-level open-family blocker + lower accepted pre-stage | 下一步: 构建 selector-3 ready-gate/open-family formal blocker package，合并 selector3/6 no-carrier、producer-skip、ready-gate author、non-direct/hinted route 与 visible selector4/9 replay failures，决定剩余路线
2026-06-23 05:01:02 +0800 | 目标: 构建 selector-3 ready-gate/open-family formal blocker package，合并 selector3/6 no-carrier、producer-skip、ready-gate author、non-direct/hinted route 与 visible selector4/9 replay failures | 动作: 1) 串联 `selector3_6_payload_copyback_boundary_20260623`、`selector3_lower_author_target_selection_20260623`、`raw_selector3_ready_gate_producer_skip_20260623`、`ready_gate_author_entitlement_blocker_20260623`、`non_direct_route_reachability_verdict_20260619`、hinted-open 三轮 verdict、selector4/selector9 blocker verdicts; 2) 新增 `mps/ANE/.ane_runs/json/selector3_ready_open_family_formal_blocker_20260623.json`、CSV 与 `mps/ANE/experiments/results/selector3_ready_open_family_formal_blocker_package.md` | 证据: ANEServices selector3/6 无 reusable carrier；raw selector3 default path 跳过 `resource+0x493a0` producer；ready gate author 落在 selector-0 open reply / entitlement-gated open family；non-direct/hinted route 当前不可达；selector4 visible patch 与 selector9 direct payload 均未 replay lower tuple | 结论: 本轮短期目标完成，verdict=`confirmed`：当前机器 selector-3 ready/open-family 层已正式关闭；same-layer wrapper/open/selector4/selector9 probing 不再是默认路线 | 下一步: 选择关闭层以下的最小 lower technical route：resource/materializer lifecycle author、selector-3 kernel user-client accepted-state handling、或 firmware reply-publish path
2026-06-23 05:06:05 +0800 | 目标: 在 selector-3 ready/open-family 层关闭后选择下一条 lower technical route | 动作: 1) 比较 resource/materializer lifecycle、selector-3 kernel user-client accepted-state、firmware reply-publish/completion 三条候选; 2) 读取 `bootkc_493a0_split_materializer_scan.md`、`procedure_cache_chaining_boundary_note.md`、`resource400d0_deeper_materializer_boundary_20260623`、`record1b8_dynamic_observation_feasibility_20260623`、`firmware_reply_vs_completion_priority_20260623`; 3) 新增 `mps/ANE/.ane_runs/json/lower_route_after_ready_open_blocker_20260623.json` 与 CSV | 证据: `resource+0x493a0` 是 runtime-owned surface 且跨多阶段复用；`resource+0x400d0` accepted-state cluster 的 visible materializer 仍未找到；procedure/cache/chaining 只提供 lookup/build/send bridge；safe dynamic `record+0x1b8` observation 当前不可行；firmware reply-publish 保留为静态 fallback | 结论: 本轮短期目标完成，verdict=`confirmed`：默认下一路线是 lower resource/materializer lifecycle author recovery，具体追 `record+0x1b8` durable author 或 `process+0x203fc` decisive lifecycle author | 下一步: 静态恢复 `record+0x1b8` 或 `process+0x203fc` 的 first author/consumer chain，起点为 procedure/cache/chaining、restore-record、typed-completion、resource400d0 notes
2026-06-23 06:24:00 +0800 | 目标: 在 lower resource/materializer lifecycle route 中选择 `record+0x1b8` 或 `process+0x203fc` 的下一最小静态入口 | 动作: 1) 按 skill 规则读取 `reverse-engineering` 与 `ida-reverse`；2) `spawn_agent` 不在当前工具 schema 中，sub-agent 降级；`ida-pro-mcp idb_list` 返回空 session，未做新 IDB walk；3) 运行只读 bootkc probes：`ane_bootkc_process_state_flag_probe.py`、`ane_bootkc_restore_record_raw_send_boundary_probe.py`、`ane_bootkc_program_valid_gate_probe.py` 到本轮 CSV；4) 新增 `mps/ANE/.ane_runs/json/lower_record_vs_process_entry_selection_20260623.json` 与 CSV；5) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: `ANE_RestoreState` 在 `0xfffffe00092c1d60` 调 `ANEHWDevice::aneCmdSend(raw)`，返回后到 `0xfffffe00092c1d78` 读取 `record+0x1b8` 之间只有 5 条 visible H16 指令且 `stores=0/calls=0`，随后 `0xfffffe00092c1d7c` 写 `resource+0x402f0`；fresh `process+0x203fc` exact scan 仍只证明 visible H16 writers 写 0/1，`ProgramLoad` 读非零，`isProcessValid` 特判 exact state 2；`+0x9c0` gate 解析为 `ANEHWDevice::isProgramValid` resource-membership gate | 结论: 本轮短期目标完成，verdict=`confirmed`：下一最小静态入口选择 `record+0x1b8` raw-send/deeper-replay boundary；`process+0x203fc` 保留为 lifecycle/context surface，但当前不比 record route 更具体 | 下一步: 恢复 `ANE_RestoreState::aneCmdSend(raw)` 以下能填充 selected indexed record `+0x1b8` 的 first author/replay chain；若仍无 visible H16 author，则形成 firmware-private reply/replay blocker
2026-06-23 06:42:00 +0800 | 目标: 判定 `ANE_RestoreState::aneCmdSend(raw)` 以下的 H16-visible send/reply shell 是否包含 `record+0x1b8` first author | 动作: 1) 汇总本轮 `lower_record_vs_process_entry_record_raw_send_20260623.csv`；2) 复核 `ane_firmware_command_send_static_boundary_20260623.json`、`typed_completion_no_record_author_boundary_20260623.json`、`record1b8_dynamic_observation_feasibility_20260623.json` 与 `send_reply_shell_negative_note.md`；3) 新增 `mps/ANE/.ane_runs/json/record1b8_visible_send_shell_author_blocker_20260623.json` 与 CSV；4) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: raw-send return 到 `record+0x1b8` read 的 visible interval 为 5 条指令且 `stores=0/calls=0`；`aneCmdSend(raw)` / `aneFirmwareCommandSend` 是 stack command/callback packaging、`ANEFirmwareCommandState` payload/wrapper tracking 与 `IOProcessorChannelSendRetry` submit plumbing；visible typed completion 是 status/copyback/resource lookup/callback/wakeup/cleanup bookkeeping，触及 `process+0x20400` counter 但不 author `record+0x1b8` 或 `process+0x203fc==2`；safe dynamic observation 当前不可用 | 结论: 本轮短期目标完成，verdict=`falsified`：H16-visible CPU-side send/reply shell 不是 `record+0x1b8` first author；剩余 required control layer 在 visible shell 以下 | 下一步: 构建 current host-visible lower-control formal blocker package，合并 selector/open-family closure、`record+0x1b8` visible send-shell falsification、`process+0x203fc` state-2 author gap 与 safe dynamic infeasibility，判断当前机器-local host-visible lower route 是否已正式死亡
2026-06-23 06:58:00 +0800 | 目标: 构建 current host-visible lower-control formal blocker package，回答 private ANE single-process reuse 所需 lower control layer 是否已在当前机器-local route 判死 | 动作: 1) 合并 `selector3_ready_open_family_formal_blocker_20260623`、`lower_record_vs_process_entry_selection_20260623`、`record1b8_visible_send_shell_author_blocker_20260623`、`resource400d0_deeper_materializer_boundary_20260623`、`record1b8_dynamic_observation_feasibility_20260623`、`ready_gate_author_entitlement_blocker_20260623`、`raw_selector3_ready_gate_producer_skip_20260623`、`typed_completion_no_record_author_boundary_20260623`、`ane_firmware_command_send_static_boundary_20260623`; 2) 新增 `mps/ANE/.ane_runs/json/host_visible_lower_control_dead_end_blocker_20260623.json`、CSV 与 `mps/ANE/experiments/results/host_visible_lower_control_dead_end_blocker_package.md`; 3) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: selector/open family 已关闭；resource/materializer visible author missing；`record+0x1b8` first author 低于 H16-visible send/reply shell；`process+0x203fc` state-2 author 低于 visible exact-writer surface；safe dynamic observation/control 当前不可用且不使用 unsafe kernel/firmware/protected-daemon actions | 结论: 本轮短期目标完成，verdict=`confirmed`：当前 machine-local safe host-visible route 判死；multiple `load/compile` 不能从当前 descriptor/ANEServices/H16-visible lower layer 根治。具体死点在 H16-visible CPU-side send/reply shell 以下的 firmware-private 或 IOProcessor/interrupt-driven shared-state writeback/accepted-state materializer | 下一步: 默认停止 same-layer probing；只有出现 firmware-private reply/replay visibility、safe IOProcessor/interrupt completion observation，或 authorized entitlement/signing environment 时才开启新 loop
2026-06-23 07:12:00 +0800 | 目标: 根据用户澄清修改长期目标，保持 ANE inference 为目标而不是转向 MPS/MLX | 动作: 更新 `docs/ane_goal.md` 的主目标、长期 loop 阶段、验收标准与非目标；更新 `docs/ane_next.md` 顶部当前阶段为 `Baseline`，下一步改为建立 `test_clean.m4a` ANE load/compile overhead map；更新 `docs/ane_state.md` 顶部记录目标重定向 | 证据: 已完成的 `host_visible_lower_control_dead_end_blocker_20260623` 只判死 current machine-local safe host-visible private route，并不判死 ANE inference 本身；用户目标仍是使用 ANE inference，问题是 transformer load/compile overhead | 结论: 长期目标已从“继续追 same-layer private lower-control”改为“ANE-only load/compile overhead reduction”，supported ANE artifact/cache/precompile/static-shape/warm-process 为默认路线，private lower-control RE 仅在出现新安全能力时恢复 | 下一步: 建立 `test_clean.m4a` ANE overhead map，分离 compile、load、segment dispatch、eval、teardown 成本，再判断 supported ANE cache/artifact 层是否存在可控 PoC
2026-06-23 07:28:00 +0800 | 目标: 建立 `test_clean.m4a` ANE load/compile overhead map，分离 compile、load、segment dispatch、eval、teardown 成本 | 动作: 1) 使用 `ane-consumer-benchmark` 方法；2) 复用现有 full private ANE profile：`benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_persistent_aux_profile_profile/profile_summary.json` 与 `transformer_bottleneck_ledger.csv`，未触发新长跑；3) 新增 `mps/ANE/.ane_runs/json/ane_baseline_load_compile_overhead_map_20260623.json` 与 CSV；4) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: wall=`43.002657s`、audio=`39.590023s`、RTF=`1.0862`；transformer eval loop=`20.669241s` / `48.07% wall`；transformer ANE eval-only=`14.641661s`；transformer `load_or_compile=5.712274s` / `13.28% wall` across 24 segments；`mask.compile=3.732670s`、`band_split.compile=1.196359s`、`istft.compile=0.607919s`、`stft.compile=0.469620s`；known compile/load total≈`11.718841s` / `27.25% wall`；dispatch/transfer/lifecycle includes `axis_pack=3.672866s`、`ane_read=1.365294s`、`ane_write=0.931795s` | 结论: 本轮短期目标完成，verdict=`confirmed`：cold compile/load 与 steady eval / dispatch overhead 已分离，compile/load 足以解释接近 `<=30s` 目标的大部分差距 | 下一步: 进入 `SupportedANECache`，优先验证 transformer `load_or_compile` 与 `mask.compile` 是否能通过 same-process repeat-load、precompiled Core ML/ANE artifact、static-shape/warm-process route 显著降低
2026-06-23 07:40:00 +0800 | 目标: 根据用户要求再次细化长期目标：不仅尽量消除 ANE load/compile，还要解释 transformer 为什么仍耗时并继续加速 inference | 动作: 更新 `docs/ane_goal.md` 的主目标、长期问题、阶段与验收标准；更新 `docs/ane_next.md` 的 `SupportedANECache` 假设，把 load/compile 降低后的 transformer runtime 分析列入后续必答；更新 `docs/ane_state.md` 顶部目标重定向说明 | 证据: 当前 baseline 显示 wall=`43.002657s`，known compile/load≈`11.718841s` / `27.25% wall`，但 transformer eval loop 仍为 `20.669241s` / `48.07% wall`，ANE eval-only=`14.641661s`，axis_pack=`3.672866s`，ane_read=`1.365294s`，ane_write=`0.931795s` | 结论: 新长期计划明确为两段：先最大化消除 load/compile；再解释并降低 transformer eval/dispatch/transfer/lifecycle 成本，继续以 ANE 为目标后端 | 下一步: 仍先执行 `SupportedANECache`，验证 transformer `load_or_compile` 与 `mask.compile` 的 same-process repeat-load / precompiled artifact / warm-process reuse；随后进入 `TransformerRuntime` 分析剩余长耗时
2026-06-23 07:55:00 +0800 | 目标: 修改长期目标并关闭 `SupportedANECache` loop，确认 supported same-process repeat-load / precompiled Core ML/ANE artifact 是否能 materially 降低 transformer/mask load/compile | 动作: 1) 解析已有 mask repeat/precompiled probes；2) 使用 `/Users/baicai1145/miniconda3/bin/python` 完成 transformer single-pipeline same-process double-load probe；3) 新增 `mps/ANE/.ane_runs/json/supported_ane_repeat_load_precompiled_probe_20260623.json` 与 CSV；4) 更新 `docs/ane_goal.md`、`docs/ane_state.md`、`docs/ane_next.md`，把 active phase 从 `SupportedANECache` 移到 `TransformerRuntime` | 证据: transformer load0=`10.880670542s`、load1=`10.450698375s`，仅下降 `0.429972167s` / `3.951707%`；existing transformer package-vs-compiled total load 为 `.mlpackage=61.250500334s`、`.mlmodelc=72.949054543s`；mask precompiled release-between-loads 为 `173.080025958s -> 174.683764291s`，其他 mask repeat probes second load 也未下降 | 结论: 本轮短期目标完成，verdict=`falsified`：supported repeat-load/precompiled route 不能作为当前 measured transformer/mask compile/load material elimination solution；ANE 仍是目标后端，MPS/MLX 仍仅作 fallback/reference | 下一步: `TransformerRuntime` 阶段，从 `test_clean.m4a` private ANE profile 分离 transformer eval-only、segment dispatch、axis pack/unpack、ANE read/write、handle/free、fallback/sync 成本，找出为什么 transformer runtime 仍长，并提出最小可验证加速 probe
2026-06-23 08:20:00 +0800 | 目标: 在 `TransformerRuntime` 阶段识别 `test_clean.m4a` private ANE 慢速的分部根因，并结合已有 RE blocker 约束确认可行解法方向 | 动作: 1) 使用 `ane-consumer-benchmark` 与 `diagnosing-bugs` 方法；2) 从 `profile_summary.json` 与 `transformer_timings.csv` 生成 `mps/ANE/.ane_runs/json/transformer_runtime_root_cause_ledger_20260623.json` 与 CSV；3) 按 axis/layer 聚合 transformer eval、pack、read/write、load/compile、handle/free、GC；4) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: top causes: `transformer_time_axis_eval_only=10.686806459s`、`transformer_load_or_compile=5.712273665s`、`mask=5.441266209s`、`transformer_freq_axis_eval_only=3.954854589s`、`transformer_axis_pack=3.672866043s`、`transformer_ane_read_write=2.297088345s`、`transformer_handle_free_gc=1.535922207s`; flags show `load_cache_hit=True` 24/24 but `handle_cache_hit=False/cache_hit=False/cache_kept=False` 24/24 | 结论: 本轮短期目标完成，verdict=`confirmed`：慢速是 eval-only + compile/load + layout/transfer + lifecycle 的组合，不是单一 ANE compute 峰值问题；previous RE 已判死 current private lower-control same-layer route，supported repeat-load/precompiled route 也已 falsified；持久 handle cache 可能省时间但默认违反“不增加内存”约束，除非后续证明 bounded/memory-neutral | 下一步: 做 memory-neutral bridge-pack/layout ablation，比较当前 `bridge_pack_gate=true` 与 no-bridge-pack/pre-layout route，记录 wall、`axis_pack`、ANE eval、read/write、correctness、memory delta，再决定是否改推理路径
2026-06-23 08:40:00 +0800 | 目标: 执行 memory-neutral bridge-pack/layout ablation，验证是否能通过全局 `--private-ane-no-bridge-pack-gate` 降低 transformer `axis_pack_sec=3.672866s` | 动作: 1) 用 `/Users/baicai1145/miniconda3/bin/python` 运行 full `test_clean.m4a` private ANE batch4 persistent-aux no-bridge-pack benchmark；2) 读取 child log 与 watchdog failure；3) 新增 `mps/ANE/.ane_runs/json/transformer_bridge_pack_ablation_20260623.json` 与 CSV；4) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: command 在 child 进入 private ANE 后失败，failure point 为 `band_split_l2_fused_0_4` compile；log 中 ANECompiler 返回 `InvalidMILProgram`，随后 `RuntimeError: private_ane batch band split failed and torch fallback is disabled`；没有产生完整 transformer profile，因此不能比较 transformer `axis_pack` | 结论: 本轮短期目标完成，verdict=`falsified` for global ablation route：全局 no-bridge-pack 不是有效 transformer 测量，因为它先破坏 fused band split ANE MIL；但 `transformer.axis_pack=3.672866s` 仍是已确认 bottleneck | 下一步: 创建 transformer-scoped layout ablation 或 transformer-only micro-harness，保持 fused band split bridge packing enabled，只在 transformer boundary 测 `axis_pack`、wall、ANE eval、read/write、correctness、memory delta
2026-06-23 09:05:00 +0800 | 目标: 用 transformer-only `attention_pre` micro-harness 验证 `TransformerRuntime` 最大 eval-only 根因，并评估 tiled time attention 是否可作为不增内存的候选解 | 动作: 1) 先尝试 `private_ane_full_block_probe.py`，确认 full-block standalone 在当前 shape 下 ANE compile 失败，不能作为集成对照；2) 使用 `private_ane_attention_pre_micro_profile.py` 跑 integrated effective shapes：time `batch=62, seq=960`、freq `batch=960, seq=64`，以及 time tiled q=240/q=480；3) 新增 `mps/ANE/.ane_runs/json/transformer_attention_pre_shape_micro_20260623.json` 与 CSV；4) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: time micro eval=`0.201787s`，乘 4 chunks 为 `0.807148s`，匹配 integrated `time layer0 ane_pre_eval=0.832496s`；freq micro eval=`0.062119s`，乘 4 chunks 为 `0.248475s`，接近 integrated `freq layer0 ane_pre_eval=0.268893s`；time tiled q=240 eval 降到 `0.187064s` (`-7.296%`) 但 compile 从 `1.480479s` 增至 `4.803896s` (`+224.482%`)；q=480 eval 仅 `-1.302%` 且 compile `+585.272%` | 结论: 本轮短期目标完成，verdict=`confirmed_root_cause_partial_solution_not_promoted`：time-axis attention-pre shape 是真实主因之一；tiled q=240 是候选但不能直接采用，因为 compile/load 成本在当前约束下会吞掉 steady eval 小幅收益 | 下一步: 恢复有效 integrated comparison：要么找回正确 native-supervised full-path invocation，要么新增 transformer-only integrated harness，只比较 current vs tiled q=240 的 wall/profile/memory/correctness
2026-06-23 09:25:00 +0800 | 目标: 恢复有效 integrated comparison，验证 tiled q=240 是否能在 transformer-only 集成路径中带来 wall/profile/memory/correctness 收益 | 动作: 1) 新增 benchmark-only harness `benchmark/private_ane_transformer_layerwise_compare.py`，直接调用 `PrivateANETransformerRunner.run_transformers_layerwise_many`，避开 fused band split/mask；2) 运行 one-layer current vs tiled q=240：`/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --layers 1 --q-chunk 240 --out benchmark_results/private_ane/transformer_layerwise_compare_l1_q240_20260623.json`; 3) 新增 `mps/ANE/.ane_runs/json/transformer_layerwise_tiled_q240_compare_20260623.json` 与 CSV；4) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: correctness exact (`max_abs=0`, `mean_abs=0`, checksum delta 0)；但 wall `+3.418162s` / `+81.8747%`；time-axis `load_or_compile_wall_sec +3.453054s`，time-axis `eval_sec -0.018812s`，`ane_pre_eval -0.006038s`；max RSS `+31.406MB` | 结论: 本轮短期目标完成，verdict=`falsified`：tiled q=240 不应作为默认优化；它的 steady eval 微小收益被 compile/load 成本吞掉，并且不满足“不增加内存”的默认约束 | 下一步: 转向 transformer `load_or_compile` / segment lifecycle / segment count 的 memory-neutral 降低路线；候选必须降低 `load_or_compile_wall_sec` 或减少 segment count，不能依赖 persistent handle memory growth
2026-06-23 10:05:00 +0800 | 目标: 评估 memory-neutral 的 transformer `load_or_compile` / segment lifecycle 降低路线，避免 persistent handle memory growth | 动作: 1) 扩展 `benchmark/private_ane_transformer_layerwise_compare.py` 支持 `--compare batch-axis` 和 `--compare load-cache`；2) 运行 batch-axis one-layer/four-chunk probe 并新增 `transformer_batch_axis_compare_20260623` verdict；3) 连续两次用 fresh cache dir 运行 load-cache repeat one-layer/four-chunk probe，新增 `transformer_load_cache_repeat_compare_20260623` verdict；4) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: batch-axis: wall `+4.415963s` / `+82.736%`，time-axis unsupported，freq-axis supported but `load_or_compile +3.372755s`、eval `+1.155641s`、`max_abs=0.015625`; load-cache repeat: run1 wall `-3.223859s` / `-62.419%`，run2 wall `-3.192752s` / `-61.956%`，both exact (`max_abs=0`)，repeat rows show `load_cache_hit=True`、`handle_cache_hit=False`、`bridge_profile_compile_qos_sec=0` | 结论: 本轮短期目标完成：batch-axis verdict=`falsified`; bridge load-cache repeat verdict=`confirmed_candidate`。这是当前第一个真正对 transformer `load_or_compile` 有大幅收益且不依赖 persistent handle cache 的候选路线 | 下一步: 在 full `test_clean.m4a` private ANE profile 中启用 bridge load-cache，对比 43.002657s baseline，记录 wall、correctness、transformer `load_or_compile`、aux compile、memory/swap、cache hit fields；若有效，再考虑作为默认路线
2026-06-23 09:25:42 +0800 | 目标: 回答当前 `test_clean.m4a` private ANE 慢速根因，并修正 full-path load-cache 状态 | 动作: 1) 使用 `diagnosing-bugs` 方法；2) 复查 `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_persistent_aux_profile.json`、`profile_summary.json`、`transformer_timings.csv` 与 `mps/ANE/.ane_runs/json/transformer_runtime_root_cause_ledger_20260623.json`；3) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` 顶部恢复状态 | 证据: wall=`43.002657s`; baseline already has `private_ane_memory_guard.load_cache=true`, `bridge_load_cache.enabled=true`, `hits=139`; transformer rows show `load_cache_hit=True` 24/24 and `handle_cache_hit=False` 24/24; top measured causes remain `time_axis_eval_only=10.686806s`, `load_or_compile_wall_sec=5.712274s`, `mask=5.441266s`, `freq_axis_eval_only=3.954855s`, `axis_pack=3.672866s`, `ane_read_write=2.297088s`, `handle_free_gc=1.535922s` | 结论: 慢速不是单一 compute bottleneck，也不是简单未启用 load-cache；当前是 transformer shape/segmentation eval cost + cache-hit 下残留 bridge/model materialization + host layout/transfer/lifecycle overhead 的组合问题 | 下一步: 跑 comparable `--private-ane-no-load-cache` full-path profile，量化 load-cache 已省掉多少；随后分析 cache-hit rows 内残留 `load_or_compile_wall_sec` 的具体组成，并优先寻找 memory-neutral 的 segment/materialization/layout reduction route
2026-06-23 09:36:34 +0800 | 目标: 完成 full-path load-cache vs no-load-cache batch4 comparison，量化 current baseline 中 load-cache 已解决多少 load/compile/materialization 成本 | 动作: 1) 使用 `ane-consumer-benchmark` 方法；2) 运行 `/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_test_clean_benchmark.py --baseline none --audio test_clean.m4a --full-audio --private-ane-allow-long-audio --private-ane-child-timeout-sec 600 --private-ane-chunk-batch-size 4 --private-ane-auto-chunk-batch-max 2 --private-ane-fused-band-split --private-ane-fused-band-split-max-outputs 4 --private-ane-fused-mask-estimator --private-ane-fused-mask-estimator-max-outputs 2 --private-ane-persistent-aux-handles --private-ane-persistent-stft-handles --private-ane-preload-stft-handles --private-ane-no-load-cache --out benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_no_load_cache_profile.json`；3) 运行 `benchmark/analyze_private_ane_profile.py` 生成 no-cache profile summary；4) 新增 `mps/ANE/.ane_runs/json/full_path_load_cache_vs_no_load_cache_20260623.json` 与 CSV；5) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: no-cache wall=`74.844223s`, RTF=`1.890482`; cache baseline wall=`43.002657s`, RTF=`1.086199`; no-cache transformer `load_or_compile_wall_sec=44.994990s` vs cache `5.712274s`; wall delta=`+31.841566s` / `+74.05%`; transformer load/materialization delta=`+39.282716s` / `+687.69%`; transformer eval loop remains comparable (`20.669241s` cache vs `19.619257s` no-cache) | 结论: 本轮短期目标完成，verdict=`confirmed`：bridge load-cache is already a major active speedup, but it does not eliminate residual cache-hit transformer `load_or_compile_wall_sec=5.712274s`; current slow speed remains combined shape/segmented eval + residual materialization + layout/transfer/lifecycle overhead | 下一步: 进入 residual cache-hit load/materialization decomposition，优先从 transformer rows / bridge profile surfaces 拆分 file/source materialization、descriptor/model/surface/request creation、load QoS、handle lifecycle，并寻找不增加 memory 的 segment/materialization reduction probe
2026-06-23 09:43:17 +0800 | 目标: 完成 residual cache-hit transformer load/materialization decomposition，找出 bridge load-cache 命中后 `load_or_compile` 仍耗时的主要子项 | 动作: 1) 运行 current warm-cache batch4 diagnostic profile：`/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_test_clean_benchmark.py --baseline none --audio test_clean.m4a --full-audio --private-ane-allow-long-audio --private-ane-child-timeout-sec 600 --private-ane-chunk-batch-size 4 --private-ane-auto-chunk-batch-max 2 --private-ane-fused-band-split --private-ane-fused-band-split-max-outputs 4 --private-ane-fused-mask-estimator --private-ane-fused-mask-estimator-max-outputs 2 --private-ane-persistent-aux-handles --private-ane-persistent-stft-handles --private-ane-preload-stft-handles --private-ane-load-cache --private-ane-cache-tmpdir benchmark_results/private_ane/ane_tmp_loadcache --out benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_load_cache_bridgeprofile_20260623.json`；2) 运行 `benchmark/analyze_private_ane_profile.py` 生成 profile；3) 聚合 `transformer_timings.csv` 的 `bridge_profile_*` 字段；4) 新增 `mps/ANE/.ane_runs/json/residual_cache_hit_load_materialization_decomposition_20260623.json` 与 CSV；5) 复查 `host_visible_lower_control_dead_end_blocker_20260623.json` 约束 solution choice；6) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: wall=`35.891103s`, RTF=`0.906569`; transformer eval loop=`20.123772s`; transformer `load_or_compile_wall_sec=5.942209s`; 24/24 rows `load_cache_hit=True`, `bridge_profile_route=load_cache`, `handle_cache_hit=False`; bridge-profiled total=`3.777231s`, including `tmpdir=1.904578s`, `load_qos=1.262232s`, `file_write=0.573875s`; unprofiled load/materialization gap=`2.164978s`; time-axis load/materialization=`3.456740s` vs freq-axis=`2.485469s` | 结论: 本轮短期目标完成，verdict=`confirmed`：cache-hit residual is dominated by source/tmpdir materialization, load QoS, file-write, and an unprofiled wrapper/materialization gap, not descriptor/model/surface/request creation; previous RE blocker rules out returning to lower accepted-state replay as the default safe solution | 下一步: prototype or ablate a memory-neutral cache-hit source-materialization shortcut that avoids redundant tmpdir/file writes, then measure wall/load_or_compile, `bridge_profile_tmpdir_sec`, `bridge_profile_file_write_sec`, `bridge_profile_load_qos_sec`, eval, correctness, and RSS/swap
2026-06-23 10:25:14 +0800 | 目标: prototype/validate memory-neutral cache-hit source-materialization shortcut，避免 transformer cache-hit loads 重复写 source files | 动作: 1) 修改 `benchmark/private_ane_transformer_layerwise_compare.py`，新增 candidate-only `--compare bridge-env` / `--bridge-env KEY=VALUE` 诊断模式；2) 修改 `mps/maderix_ANE/bridge/ane_bridge.m`，新增 opt-in `ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT=1`，当 content-addressed cache dir 中 `model.mil` 与全部 weight files 已存在且 size match 时跳过 repeated source writes，仍走 normal `_ANEInMemoryModel loadWithQoS`；3) `make` 重建 `mps/maderix_ANE/bridge/libane_bridge.dylib`；4) transformer-only probe：`benchmark_results/private_ane/transformer_layerwise_compare_l1_skip_source_write_20260623.json`；5) full-path probe：`benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_skip_source_write_20260623.json` 并用 `benchmark/analyze_private_ane_profile.py` 生成 profile；6) 将 shortcut 接入 `private_ane_skip_source_write_on_cache_hit` / `--private-ane-skip-source-write-on-cache-hit`，并跑 `test_clean_1s_skip_source_write_flag_smoke_20260623.json` 验证 flag path；7) 新增 `mps/ANE/.ane_runs/json/skip_source_write_cache_hit_fullpath_20260623.json` 与 CSV；8) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: transformer-only one-layer/four-chunk exact：`max_abs=0`, `mean_abs=0`, `p99_abs=0`, `checksum_delta=0`; full path wall `35.891103s -> 31.337585s` (`-4.553518s`, `-12.69%`); RTF `0.906569 -> 0.791553`; transformer `load_or_compile_wall_sec=5.942209s -> 3.987150s` (`-1.955059s`, `-32.90%`); transformer `bridge_profile_file_write_sec=0.573875s -> 0`; `bridge_profile_tmpdir_sec=1.904578s -> 1.284876s`; `bridge_profile_load_qos_sec` 基本不变；internal max RSS `1351.219MB -> 1348.109MB`，max swap `2408MB -> 2392MB`; 24/24 transformer rows route=`load_cache_skip_source_write` | 结论: 本轮短期目标完成，verdict=`confirmed`：skip-source-write shortcut 是 memory-neutral 的有效 load/materialization reduction；之前 direct/wrapper client-file load 路线要么 eval fail，要么 exact 但更慢且 maxrss 增加，不作为解法 | 下一步: 补 full-path output retention / waveform diff 证据；若通过，把 `private_ane_skip_source_write_on_cache_hit` 提升为当前 experimental ANE benchmark profile 默认项，然后继续攻击最大剩余项：transformer eval loop (`ane_pre_eval`) 与 `axis_pack`
2026-06-23 10:46:06 +0800 | 目标: 测试把 private ANE load-cache/tmpdir 从 `/Volumes/2T` 仓库目录搬到 internal `/tmp` 是否能 memory-neutral 地降低 cache-hit load/materialization | 动作: 使用 `diagnosing-bugs` / `ane-consumer-benchmark` 方法，先确认最新 full profile 的剩余热点：wall=`31.337585s`、transformer lifecycle+eval≈`26.619177s`、eval loop=`19.676179s`、ANE total=`16.323630s`、ANE eval-only=`14.088463s`、`ane_pre_eval=12.523742s`、`load_or_compile=3.987150s`、`axis_pack=3.299838s`；随后执行 bounded 1s probe：先空 `/tmp` cache 失败，再用 `/usr/bin/ditto` 将 `benchmark_results/private_ane/ane_tmp_loadcache` (`1.0G`, `1129` files, `138` model.hwx) 复制到 `/tmp/pymss_ane_tmp_loadcache_probe_20260623` 后重跑 `/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_test_clean_benchmark.py --audio test_clean.m4a --seconds 1 --baseline none --private-ane-cache-tmpdir /tmp/pymss_ane_tmp_loadcache_probe_20260623 --out benchmark_results/private_ane/test_clean_1s_internal_tmp_cache_probe_20260623.json` | 证据: 新增 `mps/ANE/.ane_runs/json/internal_tmp_cache_locality_probe_20260623.json` 与 CSV；失败 child 在 `benchmark_results/private_ane/test_clean_1s_internal_tmp_cache_probe_20260623.private_ane_child/`；trace 证明 STFT preload copied-cache hit (`bridge_profile_route=load_cache`, hit delta `1`, miss delta `0`, `bridge_profile_tmpdir_sec=0.000603792`, `bridge_profile_load_qos_sec=0.019998542`)，但 full run 在到达 transformer 前 `band_split_l2_0` cold compile 触发 `InvalidMILProgram`；native supervisor max child RSS≈`695.766MB`、max swap growth=`0`，但失败发生在 transformer 前，不能作为 full-path memory verdict | 结论: 本轮短期目标完成，verdict=`inconclusive`：internal `/tmp` cache locality 未被验证或证伪；full-pipeline probe 被 non-transformer cache portability / band_split cold-compile failure 污染，不能用于评价 transformer cache/tmpdir speed | 下一步: 建立或复用 transformer-only integrated harness，绕过 band_split，直接测 cache/tmpdir/layout 对 transformer `load_or_compile`、`ane_pre_eval`、`axis_pack`、read/write、segment lifecycle 的影响；目标是在不增加 memory retention 的前提下再压掉至少 `1.34s` 以越过 `<30s`
2026-06-23 11:08:00 +0800 | 目标: 完成 transformer-only integrated harness 短期目标，绕过 band_split blocker，直接验证 transformer cache-hit skip-source-write route 与 profiler 字段 | 动作: 先运行 `benchmark/private_ane_transformer_layerwise_compare.py --compare load-cache --layers 1 --chunks 4` 确认 transformer-only load-cache repeat exact 且 wall `5.408751s -> 1.922326s`；发现 bridge-env 版本没有走 `load_cache_skip_source_write`，因为 harness 未设置 `private_ane_skip_source_write_on_cache_hit` 且未保留 source files；随后只修改 diagnostic harness：load-cache probe 设置 `private_ane_keep_tmpdir=True`，并把 candidate `ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT=1` 映射到 model attribute；重跑 `/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --compare bridge-env --bridge-env ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT=1 --layers 1 --chunks 4 --cache-tmpdir benchmark_results/private_ane/transformer_layerwise_skip_source_probe_20260623 --out benchmark_results/private_ane/transformer_layerwise_compare_l1_skip_source_probe_20260623.json` | 证据: 新增 `mps/ANE/.ane_runs/json/transformer_only_skip_source_harness_probe_20260623.json` 与 CSV；candidate routes=`load_cache_skip_source_write`; candidate vs primed load-cache wall `1.978956s -> 1.864193s` (`-0.114763s`, `-5.80%`)，`load_or_compile=0.312161s -> 0.227733s`，`bridge_profile_file_write_sec=0.085870s -> 0`，`axis_pack=0.105115s -> 0.092803s`，`ane_pre_eval=1.045733s -> 1.022603s`; exact output `max_abs=0`, `checksum_delta=0`; current RSS delta `2.609MB -> 1.188MB`，未通过增加 retained memory 换速度 | 结论: 本轮短期目标完成，verdict=`confirmed`：transformer-only harness 已可绕过 band_split，并能正确测到 `load_cache_skip_source_write`；该 shortcut 在 transformer-only one-layer/four-chunk 上仍是 memory-neutral 正收益，但它只压掉约 `0.115s/layer` 级别的 load/materialization，剩余主因仍是 `ane_pre_eval` / `axis_pack` / eval lifecycle | 下一步: 用同一 transformer-only harness 做 `bridge_pack_gate` / layout ablation，确认能否降低 `axis_pack` 和 `ane_pre_eval`，严禁用已污染的 full-pipeline no-bridge-pack 结果下结论
2026-06-23 11:18:00 +0800 | 目标: 用 transformer-only harness 做 `bridge_pack_gate=0` layout ablation，验证是否能降低 `axis_pack` / `ane_pre_eval` 而不增加 retained memory | 动作: 在 diagnostic harness 中加入 candidate env `PYMSS_PRIVATE_ANE_BRIDGE_PACK_GATE=0/1` 到 `model.private_ane_bridge_pack_gate` 的映射；执行 `/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --compare bridge-env --bridge-env ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT=1 --bridge-env PYMSS_PRIVATE_ANE_BRIDGE_PACK_GATE=0 --layers 1 --chunks 4 --cache-tmpdir benchmark_results/private_ane/transformer_layerwise_bridge_pack_gate_probe_20260623 --out benchmark_results/private_ane/transformer_layerwise_compare_l1_bridge_pack_gate_off_20260623.json` | 证据: 新增 `mps/ANE/.ane_runs/json/transformer_only_bridge_pack_gate_ablation_20260623.json` 与 CSV；candidate routes=`load_cache_skip_source_write`，`bridge_pack_gate_sum=0`，输出 exact (`max_abs=0`, `checksum_delta=0`)；但相对 primed load-cache：`axis_pack +0.002769s`、`ane_pre_eval +0.001726s`、eval `+0.069799s`、current RSS delta `+176.391MB`；相对上一轮 skip-source/pack-on candidate，wall 慢约 `+0.041s` | 结论: 本轮短期目标完成，verdict=`falsified`：`bridge_pack_gate=0` 不是可推广加速路径，小的 load/materialization 收益来自 skip-source，而 layout/pre-eval 没改善且内存明显回退 | 下一步: 直接分析 `ane_pre_eval` 的 shape / segment / dispatch 路径，候选方向是减少 segment 数、改变 time/freq axis orientation、或复用 pre/post layout，但必须先用 transformer-only harness 建立 exact + RSS 不增加证据
2026-06-23 11:34:00 +0800 | 目标: 验证 transformer-only tiled q240 + skip-source 是否能推广到 full-path `test_clean.m4a`，并确认是否真正解决 `<30s` | 动作: 先给 diagnostic transformer harness 增加 `PYMSS_PRIVATE_ANE_TILED_TIME_ATTENTION_PRE` 与 `PYMSS_PRIVATE_ANE_TILED_TIME_ATTENTION_PRE_Q_CHUNK` override；运行 transformer-only q240+skip-source probe，随后运行 full-path；第一次 full-path 缺少 fused/persistent profile，失败在已知 `band_split_l2_0 InvalidMILProgram`，判定为命令 profile mismatch；随后按旧成功 profile 显式加 `--private-ane-fused-band-split --private-ane-fused-band-split-max-outputs 4 --private-ane-fused-mask-estimator --private-ane-fused-mask-estimator-max-outputs 2 --private-ane-persistent-aux-handles --private-ane-skip-source-write-on-cache-hit`，分别跑 matched control 与 tiled q240 full-path | 证据: transformer-only tiled q240+skip-source `benchmark_results/private_ane/transformer_layerwise_compare_l1_tiled_pre_q240_skip_source_20260623.json`：candidate vs primed load-cache wall `1.949738s -> 1.728605s`、`ane_pre_eval -0.037984s`、eval `-0.079682s`、RSS delta `-3.781MB`、exact；full-path artifacts `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_skip_source_explicit_control_20260623.json` 与 `...tiled_q240_skip_source_20260623.json`；new verdict `mps/ANE/.ane_runs/json/full_path_tiled_q240_skip_source_validation_20260623.json`；matched control wall=`28.173s`，tiled q240 wall=`27.903s`，old best=`31.337585s`；output NPZ diff vs old best/control exact (`max_abs=0`, `num_checked=6983680`)；native supervisor max child RSS did not regress vs old best and swap growth stayed `0` | 结论: 本轮短期目标完成，verdict=`confirmed_full_path_opt_in_not_default`：`<30s` milestone 已达到，当前 best explicit opt-in full-path `test_clean.m4a` private ANE baseline 是 `27.903s`；裸 default smoke 未携带 fused/persistent profile 时仍会落入已知 `band_split_l2_0 InvalidMILProgram`，因此不作为全局默认；但 root cause 结论必须保持严谨：tiled q240 相对 matched control 只贡献约 `0.270s`，大幅超过旧 best 主要来自 load/materialization/cache state 改善；remaining dominant costs 仍是 transformer eval loop≈`19.744s`、`ane_pre_eval≈12.538s`、`axis_pack≈3.328s` | 下一步: 不再把 file-write 或 `bridge_pack_gate=0` 当主线；进入下一 loop 直接分析 attention-pre segmentation/shape/dispatch，目标是在不增加 memory retention 的前提下降低 `ane_pre_eval` / eval loop，使 `27.903s` 继续接近 ANE theoretical utilization
2026-06-23 11:52:00 +0800 | 目标: 在 transformer-only harness 中 sweep tiled time-axis attention-pre `q_chunk`，确认是否存在比 q240 更好的 memory-neutral split | 动作: 使用 load-cache + skip-source + tiled candidate env，测试 `q_chunk=64/120/160/192/240/320/480/960`；对 invalid candidates 额外保存 failure log；聚合为 `mps/ANE/.ane_runs/json/transformer_only_tiled_pre_qchunk_sweep_20260623.json` 与 CSV | 证据: `q=240` 与 `q=480` 可编译且 exact；`q=64/120/160/192/320/960` 均在 ANE compile 阶段 `InvalidMILProgram`；`q=240` candidate wall=`1.790930s`、`ane_pre_eval_delta=-0.031145s`、`axis_pack_delta=-0.015580s`、RSS delta=`+0.0625MB`；`q=480` candidate wall=`1.845064s`、`ane_pre_eval_delta=-0.003835s`、`axis_pack_delta=+0.004898s`、RSS delta=`+4.031MB` | 结论: 本轮短期目标完成，verdict=`confirmed_q240_best_of_sweep`：当前 `_attention_pre_tiled_mil` family 中 q240 是最佳 valid split；继续扫 q_chunk 收益很低且大量形状编译失败 | 下一步: 分析 attention-pre MIL / shape / segmentation 约束，解释 invalid q_chunk 的 compile gate，并寻找非 q_chunk 的改法来降低 full-path `ane_pre_eval≈12.54s` / eval loop，而不是重复 q_chunk sweep
2026-06-23 12:14:00 +0800 | 目标: 完成 attention-pre qchunk compile-gate static analysis，解释为什么 q_chunk sweep 不是继续接近 ANE 理论上限的主线 | 动作: 使用 `diagnosing-bugs` 与 `reverse-engineering` 方法；导入当前 `pymss.modules.bs_roformer.private_ane._attention_pre_tiled_mil`，对 effective time-axis shape `batch=62, seq=960, valid_seq=960` 生成 q=`64/120/160/192/240/320/480/960` 的 MIL，统计 `slice_by_index`、`matmul`、`softmax`、`concat`、MIL 行数/字符数和 score 元素规模；合并上一轮真实 ANECompiler q-sweep verdict；更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: 新增 `mps/ANE/.ane_runs/json/attention_pre_qchunk_compile_gate_analysis_20260623.json` 与 CSV；q64 生成 `15` softmax branch / `30` matmul / `19` slice，q240 为 `4` / `8` / `8`，q480 为 `2` / `4` / `6`，q960 为 `1` / `2` / `5`；真实 sweep 仍只有 q240/q480 编译且 exact，q240 wall/RSS 优于 q480 | 结论: 本轮短期目标完成，verdict=`confirmed_qchunk_sweep_not_root_solution`：慢速根因不是 q_chunk 未扫完，而是 segmented transformer runtime 的 attention-pre shape/layout/dispatch；继续 q_chunk sweep 不符合收益/风险 | 下一步: 做 transformer-only, memory-neutral 的 time-axis attention-pre layout/segmentation reuse probe；必须记录 correctness、`ane_pre_eval`、`axis_pack`、eval、RSS/swap，并禁止通过 retained transformer handle cache 换速度
2026-06-23 12:38:00 +0800 | 目标: 用 transformer-only pre-scope probe 判断 q240 是否同时解决 `attention_pre` eval 与 time-axis layout movement | 动作: 在 `benchmark/private_ane_transformer_layerwise_compare.py` 增加 diagnostic-only `--probe-handle-scope`、`--probe-stop-after-axis`、`--probe-stop-after-layer`，把 current / primed control / candidate 都限制到真实 runner seam `private_ane_probe_transformer_handle_scope=pre`、`stop_after_axis=time`、`stop_after_layer=1`；运行 q240+skip-source bridge-env candidate，并聚合 `benchmark_results/private_ane/transformer_layerwise_preonly_q240_skip_source_20260623.json` 为 `mps/ANE/.ane_runs/json/transformer_preonly_q240_layout_probe_20260623.json` 与 CSV | 证据: q240+skip-source candidate vs primed load-cache pre-only control wall `1.126562s -> 0.961599s`，`ane_pre_eval_delta=-0.026105s`，`axis_pack_delta=+0.014333s`，output exact (`max_abs=0`, `mean_abs=0`, `checksum_delta=0`)；normal non-batch time-axis path already reuses a scratch padded buffer, so this probe did not add retained ANE handles or global defaults | 结论: 本轮短期目标完成，verdict=`confirmed_preonly_q240_small_gain_not_layout_solution`：q240 是 attention-pre eval 的小幅优化，不是 layout solution；剩余 `axis_pack≈3.33s` 更像 transpose/copy/layout-contract 成本 | 下一步: 判断现有 runner 是否存在可避免/摊销 time-axis transpose/copy 的 safe layout-route seam；若没有，输出 blocker，明确需要改变 transformer internal layout contract 或 fused segment boundary
2026-06-23 12:49:00 +0800 | 目标: 判断 direct time-axis ANE output -> freq-axis ANE input repack 是否有足够 host-copy headroom，决定是否值得实现真实 runner diagnostic route | 动作: 写入 NumPy-only micro probe artifact；对 `chunks=4, B=1, T=960, F=62, D=384, TIME_PAD=960, FREQ_PAD=64` 比较当前 route `time_out -> natural contiguous -> freq_padded` 与 direct route `time_out -> freq_padded`，40 repeats，并验证 array equality | 证据: `mps/ANE/.ane_runs/json/layout_repack_micro_time_to_freq_20260623.json` 与 CSV；current mean `0.098836s`，direct mean `0.086570s`，mean delta `-0.012266s`（约 `-12.4%`），warmup chunks `array_equal` | 结论: 本轮短期目标完成，verdict=`candidate_direct_time_to_freq_repack_has_host_copy_headroom`；这是 host-layout route-selection evidence，不是 ANE inference speed evidence | 下一步: 在 `PrivateANETransformerRunner` 中实现 opt-in diagnostic direct time-to-freq route，真实跑 transformer-only exactness/profile，观察 `axis_pack`、wall、RSS；若收益不成立，输出 layout-contract blocker
2026-06-23 13:08:00 +0800 | 目标: 在真实 `PrivateANETransformerRunner` 中验证 direct time-to-freq boundary repack 是否能降低 transformer `axis_pack` 且不增加内存 | 动作: 新增默认关闭的 `private_ane_direct_time_to_freq_repack` diagnostic route；time-axis 后把 ANE output 直接 repack 成 freq-axis padded input，freq-axis 消费 prepacked input；harness 支持 `PYMSS_PRIVATE_ANE_DIRECT_TIME_TO_FREQ_REPACK=0/1`；先跑 direct candidate，再跑 matched no-op candidate，最后按 candidate-position 聚合为 `mps/ANE/.ane_runs/json/direct_time_to_freq_repack_probe_20260623.json` 与 CSV | 证据: control 和 direct 均 exact (`max_abs=0`)；direct vs no-op matched candidate-position：wall `+0.027971s`、eval `+0.044896s`、`axis_pack +0.014385s`、RSS delta `+173.516MB`；artifact 源文件为 `benchmark_results/private_ane/transformer_layerwise_direct_time_to_freq_repack_control_20260623.json` 与 `benchmark_results/private_ane/transformer_layerwise_direct_time_to_freq_repack_20260623.json` | 结论: 本轮短期目标完成，verdict=`falsified_direct_time_to_freq_repack_not_promotable`；boundary-level direct repack 不解决 `axis_pack`，且违反“不增加内存”方向 | 下一步: 输出或细化 layout-contract blocker：要继续压 `axis_pack≈3.33s`，需要跨 time/freq/layer 的 ANE-native internal layout contract 或更大 fused segment，而不是当前 host boundary repack
2026-06-23 13:17:00 +0800 | 目标: 关闭当前 boundary-level `axis_pack` 路线，明确下一层所需 layout contract / fused segment 条件 | 动作: 聚合 current best full-path profile、qchunk compile-gate、bridge-pack ablation、pre-only q240、direct boundary repack 证据，生成 `mps/ANE/.ane_runs/json/layout_contract_axis_pack_blocker_20260623.json` 与 CSV | 证据: current best `axis_pack=3.327896s`，time-axis `2.509663s`，freq-axis `0.818234s`；qchunk sweep 只影响 eval family；`bridge_pack_gate=0` 与 direct boundary repack 均 exact 但不降 `axis_pack` 且增加 RSS；pre-only q240 降低部分 `ane_pre_eval` 但不解决 layout movement | 结论: 本轮短期目标完成，verdict=`blocked_at_current_boundary_layout_contract`：当前 host boundary 层没有 memory-neutral `axis_pack` 低风险优化 | 下一步: 进入 fused time+freq MIL compile-feasibility probe；若 ANECompiler 拒绝，输出 `InvalidMILProgram` evidence package，作为当前 `axis_pack` dead-end 的更深证据
2026-06-23 13:33:00 +0800 | 目标: 验证 fused time/freq layout route 的最低编译可行性，区分 ANECompiler 限制与 runner policy 限制 | 动作: 用 Python bridge 编译 current-shape layout primitive matrix；分别测 `identity`、`reshape_only`、`transpose_reshape_no_pad`、`transpose_reshape_concat_pad`；再用 runner guard probe 测 freq `seq=64/valid=62` 与 `seq=62/valid=62`；最后绕过 guard 直接 `_compile_block` 编译 padded/unpadded freq segment；聚合为 `mps/ANE/.ane_runs/json/fused_time_freq_compile_feasibility_summary_20260623.json` 与 CSV | 证据: layout primitive 中 `identity`、`reshape_only`、`transpose_reshape_no_pad` 可编译，`transpose_reshape_concat_pad` 失败；runner guard 拒绝 unpadded `seq=62`，但 direct `_compile_block` 下 `freq_unpadded_candidate_direct seq=62/valid=62` 可编译（compile wall 约 `1.529s`） | 结论: 本轮短期目标完成，verdict=`confirmed_unpadded_freq_segment_compile_feasible_but_runner_contract_padded`：ANECompiler 并未绝对拒绝 unpadded freq transformer segment，当前限制主要是 runtime contract 固定 `FREQ_PAD=64` | 下一步: 实现 opt-in transformer-only unpadded freq route，输入 direct time-to-freq unpadded layout，测 exactness、`axis_pack`、wall、RSS；若不 exact 或内存/速度回退，则输出该路线 blocker
2026-06-23 13:50:00 +0800 | 目标: 在真实 runner 中验证 opt-in unpadded freq route 是否能减少 `axis_pack` 且保持 exact/RSS-neutral | 动作: 实现默认关闭的 `private_ane_direct_time_to_freq_unpadded` route；harness 支持 `PYMSS_PRIVATE_ANE_DIRECT_TIME_TO_FREQ_UNPADDED=0/1`；先跑 matched no-op control，再跑 unpadded candidate，candidate 失败后重跑并保存 failure log；聚合为 `mps/ANE/.ane_runs/json/unpadded_freq_runtime_probe_20260623.json` 与 CSV | 证据: no-op control `benchmark_results/private_ane/transformer_layerwise_unpadded_freq_control_20260623.json` completed exact (`max_abs=0`)；candidate failure log `benchmark_results/private_ane/transformer_layerwise_unpadded_freq_candidate_20260623.failure.log` 显示失败点为 `_run_freq_axis_packed_with_handles -> _run_block_profiled -> bridge.run_profiled(pre, x_ane, (batch, INNER, 1, seq))`，异常 `RuntimeError: ANE eval failed` | 结论: 本轮短期目标完成，verdict=`falsified_unpadded_freq_runtime_eval_failed`：`seq=62` freq segment 能编译但不能在当前 bridge/runtime surface contract 下 eval；不能推广 | 下一步: 比较 padded vs unpadded handle descriptors、surface byte sizes、bridge output-shape assumptions，确认 eval failure 是 surface/descriptor contract 问题还是 MIL 输出 shape 问题
2026-06-23 14:03:00 +0800 | 目标: 比较 padded 与 unpadded freq attention-pre 的 handle descriptor / surface byte-size / eval behavior，定位 unpadded route 失败层级 | 动作: 直接 `_compile_block` 编译 padded `seq=64, valid=62` 与 unpadded `seq=62, valid=62`，对 pre handle 调 `describe_handle`、surface id、`run_profiled(pre, x, out_shape)`，聚合为 `mps/ANE/.ane_runs/json/freq_padded_vs_unpadded_surface_contract_probe_20260623.json` 与 CSV | 证据: 两者 compile ok 且 descriptor 均 `n_inputs=1, n_outputs=1, model_state=3`；padded input/output bytes `30,736,384 / 61,472,768` 且 pre eval ok；unpadded input/output bytes `29,775,872 / 59,551,744` 但 pre eval failed (`RuntimeError: ANE eval failed`) | 结论: 本轮短期目标完成，verdict=`confirmed_unpadded_freq_eval_surface_contract_failure`：failure 位于 compile 之后、pre-handle eval/surface contract 层 | 下一步: 测试 bridge-level output-shape / surface allocation variants；若仍失败，则记录 `FREQ_PAD=64` 为当前 freq attention-pre family 的硬 runtime contract
2026-06-23 14:15:00 +0800 | 目标: 测试 unpadded freq attention-pre 的 bridge-level surface byte allocation variants，判断是否必须 padded MIL 或只需 padded IOSurface | 动作: 对 unpadded `mil_seq=62` 编译 5 个 surface/write/read 组合，并保留 padded baseline；聚合为 `mps/ANE/.ane_runs/json/freq_unpadded_surface_bytes_variant_probe_20260623.json` 与 CSV | 证据: padded baseline eval ok；unpadded MIL + unpadded surfaces eval failed；unpadded MIL + both input/output surfaces padded to `FREQ_PAD=64` eval ok（write/read 62 或 write 64/read 62 均 ok）；only input padded 或 only output padded 均 eval failed | 结论: 本轮短期目标完成，verdict=`confirmed_unpadded_mil_requires_padded_surfaces_for_eval`：ANE runtime 需要 padded input/output IOSurface allocation，但 MIL 本身可以是 `seq=62` | 下一步: 实现 opt-in runtime route：freq MIL `seq=62` + input/output bytes `seq=64` + direct width-62 input + seq-62 readback，测 exactness、`axis_pack`、wall、RSS
2026-06-23 14:05:00 +0800 | 目标: 把 reverse-engineered padded surface-byte requirement 接入 integrated transformer runtime，验证 unpadded freq MIL `seq=62` 是否能在不增加内存的情况下减少 freq eval / layout overhead | 动作: 1) 在 `benchmark/private_ane_real_block_probe.py::_compile_block` 使用 `surface_seq` 编译 padded input/output byte contracts；2) 在 `pymss/modules/bs_roformer/private_ane.py` 的 opt-in `private_ane_direct_time_to_freq_unpadded` freq 路径下，把 `surface_seq=FREQ_PAD` 加入 compile/cache key；3) 先运行 width-62 eval-buffer 版本，确认其不再 eval-fail 但输出错误；4) 修正 direct time-to-freq handoff，使 eval buffer 实际保持 width `FREQ_PAD=64`，MIL logical seq 仍为 `62`，readback trim 到 `62`；5) 运行 `/Users/baicai1145/miniconda3/bin/python -m py_compile pymss/modules/bs_roformer/private_ane.py benchmark/private_ane_transformer_layerwise_compare.py benchmark/private_ane_real_block_probe.py` 和 transformer-only matched harness：`/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --compare bridge-env --layers 1 --chunks 4 --q-chunk 240 --cache-tmpdir benchmark_results/private_ane/ane_tmp_loadcache --bridge-env PYMSS_PRIVATE_ANE_DIRECT_TIME_TO_FREQ_UNPADDED=1 --out benchmark_results/private_ane/transformer_layerwise_compare_l1_unpadded_freq_padded_surface_v2_20260623.json` | 证据: `benchmark_results/private_ane/transformer_layerwise_compare_l1_unpadded_freq_padded_surface_20260623.json` 记录 first attempt wrong output（`max_abs=16.433837890625`, `checksum_delta=-752790.125`）；`benchmark_results/private_ane/transformer_layerwise_compare_l1_unpadded_freq_padded_surface_v2_20260623.json` 记录 corrected route exact（`max_abs=0`, `mean_abs=0`, `p99_abs=0`, `checksum_delta=0`）；summary artifact `mps/ANE/.ane_runs/json/unpadded_freq_padded_surface_runtime_probe_20260623.json` / CSV peer 记录 load-cache primed control wall `1.8288877500162926s`，candidate `1.776548375026323s`，delta `-0.052339374989969656s` / `-2.8618%`，freq eval `0.4400552920124028s -> 0.35807879199273884s`，freq axis_pack `0.05522933401516639s -> 0.0s`，total axis_pack `0.09679858398158103s -> 0.10237233500811271s` | 结论: 本轮完成了一个短期目标：reverse-engineered surface-byte contract 已在 integrated runtime 中确认可用，且 transformer-only exact 并有小幅速度收益；同时证明“只改 compile bytes、不实际 padded eval buffer”是错误路线。当前还不能 promotion，因为只有 transformer-only RSS delta 和 correctness，缺少 full-path `test_clean.m4a` waveform、native-supervisor max RSS、swap、wall 证据 | 下一步: 做 full-path `test_clean.m4a` validation：q240 tiled time attention + skip-source-write load-cache + `PYMSS_PRIVATE_ANE_DIRECT_TIME_TO_FREQ_UNPADDED=1`，比较 wall、waveform exactness、transformer eval/axis_pack、max RSS/swap；若 exact 且不增内存，再考虑默认 benchmark profile 或进一步 segment/read-write 优化。
2026-06-23 14:28:00 +0800 | 目标: 对 transformer-only exact 的 unpadded freq MIL + padded surface-byte route做 full-path `test_clean.m4a` promotion gate | 动作: 1) 为 `benchmark/private_ane_test_clean_benchmark.py` 新增 default-off `--private-ane-direct-time-to-freq-unpadded` 并转发到 child；2) 为 `pymss/separator.py` 新增 `private_ane_direct_time_to_freq_unpadded` passthrough/config application；3) 运行 `/Users/baicai1145/miniconda3/bin/python -m py_compile pymss/modules/bs_roformer/private_ane.py pymss/separator.py benchmark/private_ane_test_clean_benchmark.py benchmark/private_ane_transformer_layerwise_compare.py benchmark/private_ane_real_block_probe.py`；4) 运行 full-path command：`/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_test_clean_benchmark.py --audio test_clean.m4a --full-audio --baseline none --private-ane-allow-long-audio --private-ane-fused-band-split --private-ane-fused-band-split-max-outputs 4 --private-ane-fused-mask-estimator --private-ane-fused-mask-estimator-max-outputs 2 --private-ane-persistent-aux-handles --private-ane-skip-source-write-on-cache-hit --private-ane-tiled-time-attention-pre --private-ane-tiled-time-attention-pre-q-chunk 240 --private-ane-direct-time-to-freq-unpadded --out benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_unpadded_freq_20260623.json` | 证据: `mps/ANE/.ane_runs/json/full_path_unpadded_freq_padded_surface_validation_20260623.json` / CSV peer；candidate flag true；wall `29.920132166007534s` vs q240+skip-source baseline `27.903367375023663s`，delta `+2.0167647909838706s` / `+7.2277%`；transformer total `26.10294062498724s` vs `24.631073875003494s`；transformer eval `19.805018791987095s` vs `19.743745001906063s`；transformer compile/load `3.401522250031121s` vs `1.944708043942228s`；freq eval `5.766555875074118s` vs `5.77694412501296s` only `-0.01038824993884191s`；freq compile/load `1.1959509160369635s` vs `0.3787375020037871s`；native-supervisor max child RSS `1638.734MB` vs `1630.766MB`，swap growth `0` | 结论: 本轮完成 full-path promotion gate，verdict=`falsified_full_path_unpadded_freq_padded_surface_not_promotable`。该 route 在 transformer-only 中成立，但 full-path 中 compile/load materialization regression 吞掉 eval 小收益并使总 wall 变慢，native max child RSS 还小幅上升；不得 promotion。由于性能和内存已失败，本轮不补 waveform diff，不声称 full-path waveform exact | 下一步: 进入新的短期目标：解释 full-path compile/load regression。优先比较 q240 baseline 与 unpadded candidate 的 transformer timing rows / bridge profile identifier / load-cache route / tmpdir/file-write/load_qos 字段，判断是否 logical `seq=62` 引入新 artifact family 或缓存身份分裂。
2026-06-23 14:55:00 +0800 | 目标: 解释 unpadded freq padded-surface route 为什么 transformer-only 小幅加速但 full-path compile/load 回退 | 动作: 1) 对旧 q240 baseline、candidate、fresh q240 rerun baseline 的 `transformer_timings` 做 row-level 对比；2) 重新跑 matched full-path q240+skip-source baseline：`/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_test_clean_benchmark.py --audio test_clean.m4a --full-audio --baseline none --private-ane-allow-long-audio --private-ane-fused-band-split --private-ane-fused-band-split-max-outputs 4 --private-ane-fused-mask-estimator --private-ane-fused-mask-estimator-max-outputs 2 --private-ane-persistent-aux-handles --private-ane-skip-source-write-on-cache-hit --private-ane-tiled-time-attention-pre --private-ane-tiled-time-attention-pre-q-chunk 240 --out benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_rerun_20260623.json`；3) 产出 `mps/ANE/.ane_runs/json/full_path_compile_load_regression_root_cause_20260623.json` / CSV peer；4) 为 `pymss/modules/bs_roformer/private_ane.py::_accumulate_named_bridge_compile_profiles` 加入 component-level `pre/gate/ffn_bridge_profile_*` timing/fast-load fields，供下一轮窄 probe 定位具体组件 | 证据: fresh baseline `27.649230875016656s`，candidate `29.920132166007534s`；24/24 aggregate identifiers same，24/24 route same，均为 `load_cache_skip_source_write`，bridge hits 均 `123`；candidate vs fresh baseline：time `bridge_profile_tmpdir_sec` `0.019240s -> 0.584193s` (`+0.564953s`)，freq `0.036937s -> 0.430766s` (`+0.393828s`)；time `load_qos_sec` `-0.036845s`，freq `+0.005615s`；time eval slightly improves，freq eval only `+0.148925s` | 结论: 本轮完成短期目标，verdict=`confirmed_tmpdir_materialization_regression_not_cache_identity_miss`。最初“cache-key/artifact identifier proliferation”假设被部分否定：aggregate identifier/route/hit count 没变；真正主因是 bridge load-cache tmpdir/source-completeness materialization/checking，而非 ANE loadWithQoS 或 eval compute。当前 profiler 旧数据无法拆出 pre/gate/ffn 哪个组件，已加 instrumentation 解决下一轮可观测性 | 下一步: 运行窄 probe（优先 transformer-only integrated 或短 full-path）读取新增 `pre/gate/ffn_bridge_profile_tmpdir_sec` 等字段，确认 tmpdir spike 属于 pre/gate/ffn 哪个组件；若集中在某组件，再考虑 native bridge tmpdir/source-completeness check 快路径，否则放弃 unpadded freq route。
2026-06-23 15:08:00 +0800 | 目标: 尝试用更便宜的 12-layer transformer-only harness 读取新增 component-level bridge profile fields，避免再跑 full-path | 动作: 运行 `/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --compare bridge-env --layers 12 --chunks 4 --q-chunk 240 --cache-tmpdir benchmark_results/private_ane/ane_tmp_loadcache --bridge-env PYMSS_PRIVATE_ANE_DIRECT_TIME_TO_FREQ_UNPADDED=1 --out benchmark_results/private_ane/transformer_layerwise_compare_l12_unpadded_freq_component_profile_20260623.json`；该 probe 运行约 70s 后失败，随后写入 `mps/ANE/.ane_runs/json/transformer_l12_component_profile_failed_20260623.json` | 证据: ANECompiler 返回 `InvalidMILProgram`，traceback 落在 candidate freq `attention_pre` compile：`_compile_axis_handles -> _compile_block -> bridge.compile -> RuntimeError("ANE compile failed")` | 结论: 12-layer transformer-only cold-compile 不是该 full-path tmpdir regression 的有效窄 seam；full-path 可以走已有 load-cache handles，而 transformer-only l12 candidate 会 cold compile 到失败。不要再重复这个 seam | 下一步: 若要拆 pre/gate/ffn tmpdir，只能做 1-layer sanity check 或直接 rerun full-path q240 baseline/candidate with 新增 component-level profile fields；为了回答 full-path regression，应优先 full-path paired rerun。
2026-06-23 15:28:00 +0800 | 目标: 用新增 component-level bridge profile 字段做 paired full-path control/candidate，定位 pre/gate/ffn tmpdir spike | 动作: 1) 运行 baseline：`/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_test_clean_benchmark.py --audio test_clean.m4a --full-audio --baseline none --private-ane-allow-long-audio --private-ane-fused-band-split --private-ane-fused-band-split-max-outputs 4 --private-ane-fused-mask-estimator --private-ane-fused-mask-estimator-max-outputs 2 --private-ane-persistent-aux-handles --private-ane-skip-source-write-on-cache-hit --private-ane-tiled-time-attention-pre --private-ane-tiled-time-attention-pre-q-chunk 240 --out benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_component_fields_20260623.json`; 2) 运行 candidate 加 `--private-ane-direct-time-to-freq-unpadded` 输出 `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_unpadded_freq_component_fields_20260623.json`; 3) 发现 component numeric fields 仍缺失，补丁改为兼容 prefixed/unprefixed profile keys并用 one-layer sanity probe验证，但输出仍只有 route fields；4) 写入 `mps/ANE/.ane_runs/json/full_path_component_tmpdir_probe_20260623.json` / CSV peer | 证据: paired full-path baseline wall `28.631398500001524s`，candidate `28.146300874999724s`，candidate faster `-0.4850976250017993s`；transformer compile/load `2.1034516260842793s -> 1.9211887069395743s`；aggregate tmpdir did not spike，time delta `-0.002022332s`，freq delta `+0.001286875s`；component numeric key count baseline/candidate 均 `0`；native max child RSS `1660.453MB -> 1662.078MB` 略增 | 结论: 本轮 verdict=`inconclusive_tmpdir_regression_not_reproduced_component_fields_missing`。上一轮 tmpdir spike 不是稳定复现；本轮 candidate faster 但 RSS 仍略增，且还缺 full-path waveform/repeated statistics，不能 promotion。component attribution 仍不可见，说明当前 instrumentation 没有进入实际 timing rows 或被路径过滤 | 下一步: 先修 component-level timing propagation（或改 native bridge/profile export），否则改走 repeated full-path wall/RSS statistics：至少多跑 paired control/candidate，若速度收益稳定且 RSS 不增再考虑 waveform exactness/promotion；如果 RSS 一直略增则放弃该 route。
2026-06-23 15:48:00 +0800 | 目标: 修复 component-level bridge profile fields 没有进入 timing rows 的 observability blocker，并用 fixed fields 做一组 full-path pair | 动作: 1) 追到 timing row copy filter 只接受 `bridge_profile_*` 或 `*_bridge_profile_route`，导致 `pre_bridge_profile_tmpdir_sec` 这类 numeric fields 被过滤；2) patch `pymss/modules/bs_roformer/private_ane.py`：`_accumulate_named_bridge_compile_profiles` 兼容 prefixed/unprefixed profile keys，timing row filter 改为接受所有包含 `"_bridge_profile_"` 的 key；3) 运行 one-layer sanity：`benchmark_results/private_ane/transformer_layerwise_compare_l1_component_fields_fixed_20260623.json`，确认 component numeric key count `57`；4) 运行 fixed-field full-path baseline/candidate：`benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_component_fields_fixed_20260623.json` 和 `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_unpadded_freq_component_fields_fixed_20260623.json`；5) 写入 `mps/ANE/.ane_runs/json/full_path_component_timing_fixed_probe_20260623.json` / CSV peer | 证据: fixed-field full-path pair candidate faster：wall `28.357753333984874s -> 28.078389542002697s`，transformer `24.871128999977373s -> 24.672542624990456s`，compile/load `1.9713062929804437s -> 1.941294958058279s`，eval `19.867204998852685s -> 19.721921790973283s`；large tmpdir spike did not reproduce，time aggregate tmpdir delta `-0.001007043s`，freq `+0.004393379s`；component split shows only small gate tmpdir/load_qos increases and freq pre load_qos decrease；native max child RSS `1660.547MB -> 1662.984MB` (`+2.437MB`)，swap growth `0` | 结论: 本轮完成 observability fix。unpad route 在本 pair 中更快，但仍因 native RSS 增加不能 promotion；之前 tmpdir spike 更像 unstable filesystem/materialization variance，不是稳定 component-specific hotspot。单次 wall win 不够，route fate 必须靠 repeated paired full-path wall/RSS statistics | 下一步: repeated full-path q240 baseline/candidate paired stats with fixed fields；如果 median RSS 仍高，按 no-memory-increase 约束放弃该 route；如果 wall 稳定更快且 RSS 不增，再做 waveform diff / promotion。
2026-06-23 16:05:00 +0800 | 目标: 用 repeated full-path evidence 决定 unpadded freq padded-surface route 是否还能 promotion | 动作: 聚合三组 q240 baseline/candidate full-path pair：initial validation、component-fields missing pair、component-fields fixed pair；写入 `mps/ANE/.ane_runs/json/unpadded_freq_route_repeated_fullpath_policy_20260623.json` / CSV peer | 证据: wall delta 分别为 `+2.0167647909838706s`, `-0.4850976250017993s`, `-0.27936379198217764s`，median `-0.27936379198217764s`，说明 wall win/noise 混杂；native max child RSS delta 分别为 `+7.967999999999847MB`, `+1.625MB`, `+2.436999999999898MB`，3/3 positive，median `+2.436999999999898MB`；swap growth delta 全为 `0` | 结论: verdict=`abandon_unpadded_freq_padded_surface_route_for_promotion`。该 route 可以保留 default-off diagnostic，但在没有新的 memory-neutralization idea 前不得继续作为主线 promotion 候选；即使部分 run 更快，也违反“不增加内存”硬约束 | 下一步: 回到 current best q240+skip-source 主线，生成 fresh component-level bottleneck ledger：time-axis `ane_pre_eval`、segment overhead、read/write、axis pack、load/cache、RSS，选择下一个不增内存的优化目标。
2026-06-23 16:12:00 +0800 | 目标: 在放弃 unpadded-freq route 后，重新生成 current-best q240+skip-source component bottleneck ledger，选择下一主线目标 | 动作: 基于 fixed-field current observable baseline `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_component_fields_fixed_20260623.json` 解析 transformer rows，输出 `mps/ANE/.ane_runs/json/current_best_component_bottleneck_ledger_20260623.json` / CSV peer | 证据: current observable baseline wall `28.357753333984874s`，transformer `24.871128999977373s`，compile/load `1.9713062929804437s`，eval `19.867204998852685s`，native max child RSS `1660.547MB`；top contributors：`time.eval_sec=13.97083224792732s`，`time.pre.eval_sec=9.508778334013186s`，`freq.eval_sec=5.896372750925366s`，`freq.pre.eval_sec=3.064940589829348s`，`time.axis_pack_sec=2.45342729089316s` | 结论: 下一个主线目标确定为 `time_axis_attention_pre_eval_or_segmentation`。freq unpadded route 已因 RSS 放弃，q_chunk sweep 已证明当前模板 q240 最优；下一轮需要找非 q_chunk 或更低层的 time-axis pre eval/segmentation reduction，且不得增加 retained handles/RSS | 下一步: 分析 time-axis attention_pre 的 current q240 MIL/segment structure 和 bridge eval profile，寻找 memory-neutral segmentation/eval 改法；如果没有 compile-feasible改法，输出 blocker 并转向 host read/write/axis_pack。
2026-06-23 15:13:37 +0800 | 目标: 验证 time-axis `attention_pre` 的 q240 tiled route 能否扩展到 layer 1+，作为降低 `time.pre.eval_sec≈9.51s` 的 memory-neutral 下一步 | 动作: 1) 阅读 `ane-consumer-benchmark` 与 `diagnosing-bugs` skill；2) 确认当前最大瓶颈来自 `mps/ANE/.ane_runs/json/current_best_component_bottleneck_ledger_20260623.json`；3) 在 `pymss/modules/bs_roformer/private_ane.py` 增加 default-off diagnostic env `PYMSS_PRIVATE_ANE_FORCE_TILED_TIME_ATTENTION_PRE_ALL_LAYERS=1`，仅用于强制绕过 layer-0 q240 gate；4) 运行 `/Users/baicai1145/miniconda3/bin/python -m py_compile pymss/modules/bs_roformer/private_ane.py`；5) 运行窄 probe：`PYMSS_PRIVATE_ANE_FORCE_TILED_TIME_ATTENTION_PRE_ALL_LAYERS=1 /Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --compare tiled --layers 2 --chunks 1 --q-chunk 240 --probe-stop-after-axis time --probe-stop-after-layer 2 --cache-tmpdir benchmark_results/private_ane/ane_tmp_loadcache --out benchmark_results/private_ane/time_axis_tiled_pre_layer_extension_forced_raw_20260623.json`；6) 生成 `mps/ANE/.ane_runs/json/time_axis_tiled_pre_layer_extension_probe_20260623.json` / CSV peer | 证据: forced all-layer q240 在 two-layer/time-axis seam 中可 compile/eval，说明旧 “layer 1+ InvalidMILProgram” 注释对该 seam 已过期；但 wall `6.85981937503675s -> 13.884507624956314s`，delta `+7.0246882499195635s` / `+102.40%`；`max_abs=0.0078125`；summed load/compile `5.851932709047105s -> 12.911055126052815s`；eval 仅 `0.6462564579560421s -> 0.6364357090205885s` | 结论: 本轮短期目标完成，verdict=`falsified_forced_layer_extension_not_promotable`。强行把 q240 tiled pre 扩到所有 layer 会引入更多 handle/artifact materialization，compile/load 成本远大于 eval 小收益，且 narrow seam 非 exact；不得 promotion，不运行 full-path | 下一步: 进入更窄的 warm-cache/eval-only attribution：区分当前 layer-0 q240 与 forced all-layer q240 的 cold materialization vs steady-state eval，寻找 fused/reused `attention_pre` carrier，而不是增加 per-layer tiled handle family。
2026-06-23 15:30:32 +0800 | 目标: 对 forced all-layer q240 tiled time-axis `attention_pre` 做 cold materialization vs warm load-cache 分离，并定位非 exact drift 的出现层 | 动作: 1) 运行 inline `_run_variant` load-cache probe，比较 `gated_cold/gated_repeat/forced_cold/forced_repeat`，参数 `layers=2/chunks=1/q_chunk=240/probe_stop_after_axis=time/probe_stop_after_layer=2/load_cache=True/no retained transformer handles`，输出 raw `benchmark_results/private_ane/time_pre_q240_gated_vs_forced_loadcache_raw_20260623.json`；2) 生成 `mps/ANE/.ane_runs/json/time_pre_q240_gated_vs_forced_warm_loadcache_20260623.json` / CSV peer；3) 运行 localization probe，对 `probe_stop_after_layer=1` 与 `2` 分别比较 gated vs forced repeat，输出 raw `benchmark_results/private_ane/time_pre_q240_forced_correctness_localization_raw_20260623.json`；4) 生成 `mps/ANE/.ane_runs/json/time_pre_q240_forced_correctness_localization_20260623.json` / CSV peer | 证据: warm repeat `gated_repeat=1.1323377499938942s`，`forced_repeat=1.0488913750159554s`，delta `-0.08344637497793883s`；该 gain 几乎全部来自 `load_or_compile -0.08286800101632252s`，eval 只 `-0.00020099995890632272s`；forced vs gated warm repeat correctness `max_abs=0.0078125`，`mean_abs=1.3825006028866937e-08`，`p99_abs=0`；localization：stop-after-layer 1 exact (`max_abs=0`)，stop-after-layer 2 non-exact (`max_abs=0.0078125`) | 结论: 本轮短期目标完成，verdict=`confirmed_layer1_forced_q240_introduces_nonexactness`。forced all-layer q240 的 warm-cache 小收益不是 eval root solution，且第一层超出默认 gate 后就引入非 exact drift；不得 promotion，也不进入 full-path | 下一步: 检查 layer-1 q240 tiled `attention_pre` MIL/operator ordering 与 non-tiled layer-1 route 的输出差异来源；若 drift 是 q-chunk softmax/matmul 顺序固有误差，则关闭该 route family，转向其他 `time.pre` eval/segmentation reduction。
2026-06-23 15:40:17 +0800 | 目标: 判断 forced layer-1 q240 drift 是否来自 tiled `attention_pre` 本身，还是来自后续 gate composition | 动作: 1) 按 `ane-consumer-validation` 读取 `mps/ANE/experiments/results/chain_validation_suite.md`，保持 promotion exactness tolerance `0.0`；2) 运行 inline `_run_variant` scope localization，参数 `probe_handle_scope=pre/pre_gate/full`、`probe_stop_after_axis=time`、`probe_stop_after_layer=2`、`q_chunk=240`、gated vs `PYMSS_PRIVATE_ANE_FORCE_TILED_TIME_ATTENTION_PRE_ALL_LAYERS=1`、`load_cache=True`、不保留 transformer handles；3) 输出 raw `benchmark_results/private_ane/time_pre_q240_forced_scope_localization_raw_20260623.json`；4) 生成 validation artifact `mps/ANE/.ane_runs/json/time_pre_q240_forced_scope_localization_20260623.json` / CSV peer | 证据: `pre` scope forced vs gated repeat exact：`max_abs=0`，`mean_abs=0`，`num_checked=14887936`；`pre_gate` scope divergence：`max_abs=0.0009765625`，`mean_abs=2.871796800363313e-09`；full scope 同样 divergence：`max_abs=0.0009765625` | 结论: 本轮短期目标完成，verdict=`confirmed_forced_q240_drift_starts_at_pre_gate_not_pre_only`。standalone q240 tiled `attention_pre` 在该 pre-only seam 中不是直接 mismatch 源；drift 从 pre->gate composition 开始。route 仍不 promotable，因为 validation failure terminal | 下一步: 检查 layer-1 gate consumption path：pre 输出 layout/shape/route metadata、gate 输入是否需要 materialized contiguous boundary、是否可切换 gate route 恢复 exactness；必须不增加 RSS/handle family。
2026-06-23 15:53:23 +0800 | 目标: 验证 materialized contiguous pre-to-gate boundary 是否能修复 forced layer-1 q240 的 `pre_gate` non-exact | 动作: 1) 复用 `ane-consumer-validation` exactness gate（tolerance `0.0`）；2) 运行 inline `_run_variant` pre_gate boundary sweep：packed2 default vs `PYMSS_PRIVATE_ANE_BRIDGE_PACK_GATE=0` materialized pack，gated vs `PYMSS_PRIVATE_ANE_FORCE_TILED_TIME_ATTENTION_PRE_ALL_LAYERS=1`，`probe_handle_scope=pre_gate`，`probe_stop_after_axis=time`，`probe_stop_after_layer=2`，`q_chunk=240`，load-cache repeat，不保留 transformer handles；3) 输出 raw `benchmark_results/private_ane/time_pre_q240_gate_boundary_pack_sweep_raw_20260623.json`；4) 生成 `mps/ANE/.ane_runs/json/time_pre_q240_gate_boundary_pack_sweep_20260623.json` / CSV peer | 证据: packed2 default repeat forced-vs-gated：`max_abs=0.0009765625`，`mean_abs=2.871796800363313e-09`，`num_checked=14887936`；materialized pack repeat forced-vs-gated 同样：`max_abs=0.0009765625`，`mean_abs=2.871796800363313e-09`；materialized repeat 还增加显式 `att_pack_sec≈0.027s`，不改善 eval | 结论: 本轮短期目标完成，verdict=`falsified_materialized_pre_gate_boundary_does_not_restore_exactness`。pre_gate mismatch 不是 packed2 handoff/layout 单独导致；materialized boundary 非 exact 且性能更差，不得 promotion | 下一步: 测试 independent two-input gate route 或静态检查 gate MIL input ordering/shape metadata；若 two-input 也不能 exact，则关闭 forced all-layer q240 family，转向其他 `time.pre` eval/segmentation family。
2026-06-23 16:07:28 +0800 | 目标: 测试 independent two-input gate route 是否能恢复 forced layer-1 q240 的 exactness，作为 forced all-layer q240 family 的最后一个 memory-neutral recovery candidate | 动作: 1) 为 `benchmark/private_ane_transformer_layerwise_compare.py` 新增 default-off diagnostic env override `PYMSS_PRIVATE_ANE_TWO_INPUT_GATE=1`；2) 运行 `/Users/baicai1145/miniconda3/bin/python -m py_compile benchmark/private_ane_transformer_layerwise_compare.py pymss/modules/bs_roformer/private_ane.py`；3) 运行 inline `_run_variant` compile-capture probe，参数 `PYMSS_PRIVATE_ANE_TWO_INPUT_GATE=1`、`probe_handle_scope=pre_gate/full`、gated 与 `PYMSS_PRIVATE_ANE_FORCE_TILED_TIME_ATTENTION_PRE_ALL_LAYERS=1` forced、`probe_stop_after_layer=2`、load-cache、no retained handles；4) 输出 raw `benchmark_results/private_ane/time_pre_q240_two_input_gate_compile_raw_20260623.json`；5) 生成 `mps/ANE/.ane_runs/json/time_pre_q240_two_input_gate_compile_20260623.json` / CSV peer | 证据: `gated_pre_gate_two_input`、`forced_pre_gate_two_input`、`gated_full_two_input`、`forced_full_two_input` 均在 validation 前失败，`RuntimeError: ANE compile failed`，stderr family 为 `InvalidMILProgram` | 结论: 本轮短期目标完成，verdict=`falsified_two_input_gate_compile_infeasible_for_layer1_q240`。结合前序证据：`pre` exact、`pre_gate` non-exact、materialized pack 仍 non-exact、two-input gate compile-infeasible，forced all-layer q240 tiled time-axis `attention_pre` promotion family 正式关闭 | 下一步: 回到 current-best ledger，选择新的 memory-neutral `time.pre` 目标：优先比较 `time.axis_pack_sec≈2.45s`、read/write overhead，或新 attention_pre carrier；不得继续 full-path promotion forced all-layer q240。
2026-06-23 16:24:13 +0800 | 目标: 在 forced all-layer q240 family 关闭后，测试 `surface_handoff_gate_ffn` 是否能作为 memory-neutral read/write reduction route | 动作: 1) 为 `benchmark/private_ane_transformer_layerwise_compare.py` 新增 diagnostic env `PYMSS_PRIVATE_ANE_SURFACE_HANDOFF_GATE_FFN=1`；2) 运行 `/Users/baicai1145/miniconda3/bin/python -m py_compile benchmark/private_ane_transformer_layerwise_compare.py pymss/modules/bs_roformer/private_ane.py`；3) 运行 transformer-only two-layer one-chunk probe，输出 `benchmark_results/private_ane/time_pre_surface_handoff_gate_ffn_raw_20260623.json`；4) 运行 transformer-only two-layer four-chunk probe，输出 `benchmark_results/private_ane/time_pre_surface_handoff_gate_ffn_chunks4_raw_20260623.json`；5) 因窄 probe exact 且 read/write 改善，升级到 full-path `test_clean.m4a`：`/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_test_clean_benchmark.py --audio test_clean.m4a --full-audio --baseline none --private-ane-allow-long-audio --private-ane-fused-band-split --private-ane-fused-band-split-max-outputs 4 --private-ane-fused-mask-estimator --private-ane-fused-mask-estimator-max-outputs 2 --private-ane-persistent-aux-handles --private-ane-skip-source-write-on-cache-hit --private-ane-tiled-time-attention-pre --private-ane-tiled-time-attention-pre-q-chunk 240 --private-ane-surface-handoff-gate-ffn --out benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_surface_handoff_20260623.json`；6) 生成 policy artifact `mps/ANE/.ane_runs/json/surface_handoff_gate_ffn_fullpath_policy_20260623.json` / CSV peer | 证据: transformer-only chunks=4 repeat exact (`max_abs=0`) 且 wall `2.991808040998876s -> 2.9400682499981485s`；`ane_gate_read_sec 0.026675376167986542 -> 0`，`ane_ffn_write_sec 0.01780599995981902 -> 0`。Full-path output exact (`max_abs=0`, `num_checked=6983680`)，但 wall `27.649230875016656s -> 30.064417415997013s` (`+2.4151865409803577s`)；transformer eval `-0.4985272499034181s`，read/write improved (`ane_gate_read_sec -0.3813587502227165s`, `ane_ffn_write_sec -0.16588275792310014s`)，but compile/load `+1.6844570820685476s`，transformer total `+1.3006933739525266s`，max RSS `+181.828125MB` | 结论: 本轮短期目标完成，verdict=`falsified_surface_handoff_gate_ffn_not_promotable_full_path`。该 route 证明 read/write 方向有效，但 full-path compile/load identity/materialization regression 和 RSS 增长违反硬约束，不得 promotion | 下一步: 选择新的 memory-neutral target；优先静态解释 surface handoff 为何改变 compile/load/RSS identity，或转向非 transformer compile/load/read-write，不能增加 retained handles/RSS。
2026-06-23 16:32:42 +0800 | 目标: 解释 `surface_handoff_gate_ffn` 为什么 transformer-only read/write 有收益但 full-path compile/load 和 RSS 回退 | 动作: 1) 读取 `surface_handoff_gate_ffn_fullpath_policy_20260623.json`；2) 对比 baseline `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_rerun_20260623.private_ane_child/meta.json` 与 candidate `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_surface_handoff_20260623.private_ane_child/meta.json` 的 24 条 transformer timing rows；3) 汇总 bridge/profile route、identifier、tmpdir、load_qos、file_write、eval/read/write；4) 写入 `mps/ANE/.ane_runs/json/surface_handoff_compile_load_attribution_20260623.json` / CSV peer | 证据: candidate 仍全部走 `load_cache_skip_source_write`，不是 fallback / cache miss；compile/load regression 主因集中在 component materialization：pre tmpdir `+0.5376s`，gate tmpdir `+0.3262s`，FFN tmpdir `+0.1956s`，gate load_qos `+0.1427s`，FFN load_qos `+0.1474s`；read/write/eval gains already在上一轮确认，但被上述 materialization/RSS 吞掉 | 结论: 本轮短期目标完成，verdict=`confirmed_surface_handoff_regression_is_component_materialization_not_cache_route`。surface handoff 的方向本身能减少传输，但当前 bridge/component materialization identity 使其不符合 no-memory/no-slowdown gate | 下一步: 不再重跑 surface handoff promotion。只有在设计出 bridge-level fast path，能复用 existing aggregate tmpdir/source-completeness 且不增加 RSS 时才回到该 route；否则转向 current-best ledger 的其他非 transformer route-family target。
2026-06-23 16:41:29 +0800 | 目标: 判断 `surface_handoff_gate_ffn` 是否存在 Python/bridge-level safe fast path，可复用 existing aggregate tmpdir/source-completeness 以消除 component materialization regression | 动作: 1) 读取 `surface_handoff_compile_load_attribution_20260623.json`、baseline/candidate child `meta.json`；2) 比较 baseline aggregate bridge identifiers 与 candidate `pre/gate/ffn/bridge` identifiers 的 overlap；3) 检查 bridge load-cache boundary：`ANEBridge.compile_multi_inputs_outputs` 先调用 `load_multi_inputs_outputs(mil, weights, input_bytes, output_bytes)`，identity 绑定 exact MIL/weights/surface sizes；4) 写入 `mps/ANE/.ane_runs/json/surface_handoff_fast_path_feasibility_20260623.json` / CSV peer | 证据: candidate pre identifiers：24 unique，和 baseline aggregate overlap `0`；candidate gate identifiers：24 unique，overlap `0`；candidate FFN 和 aggregate 与 baseline aggregate overlap `24/24`，但仍有 tmpdir/load_qos materialization overhead；pre/gate 若复用 aggregate tmpdir 会加载错误 program 风险 | 结论: 本轮短期目标完成，verdict=`blocked_surface_handoff_fast_path_requires_native_identity_or_materialization_change`。surface handoff 作为 Python/runtime route promotion path 关闭；除非做 native bridge / reverse engineering 层面的 load-cache materialization identity fast path，否则不得重跑 full-path promotion | 下一步: pivot 到 current-best ledger 的其他 target，或显式开启 native bridge/RE work；不要继续 surface-handoff route toggles。
2026-06-23 16:55:29 +0800 | 目标: 判断 native bridge load-cache materialization/source-completeness overhead 是否存在安全、memory-neutral 的 Python/bridge-level fast path | 动作: 1) 使用 `diagnosing-bugs`、`ane-consumer-benchmark`、`reverse-engineering` 方法做静态最小 probe；2) 检查 `mps/maderix_ANE/bridge/ane_bridge.m` 中 `hexStringIdentifier`、`load_cache_skip_source_write`、source-completeness、tmpdir、`loadWithQoS`、handle/runtime-clone 路径；3) 检查 `pymss/modules/bs_roformer/private_ane.py` 中 load-cache env、skip-source、runtime-clone、`_compile_bridge_multi_outputs` wrapper；4) 复用 `surface_handoff_fast_path_feasibility_20260623.json`、`surface_handoff_compile_load_attribution_20260623.json`、`surface_handoff_gate_ffn_fullpath_policy_20260623.json`，未重跑已关闭 full-path benchmark；5) 写入 `mps/ANE/.ane_runs/json/native_bridge_load_cache_materialization_feasibility_20260623.json` 并更新 `docs/ane_state.md` / `docs/ane_next.md` | 证据: bridge 以 `_ANEInMemoryModel.hexStringIdentifier` 作为 temp/cache identity；`load_cache_skip_source_write` 只在同一 identifier 目录 source files complete 时跳过写入；Python 只暴露 load-cache vs uncached compile，没有 identifier override/source-root alias；surface-handoff pre/gate identifiers 与 baseline aggregate overlap 为 0，复用 aggregate tmpdir 会有加载错误 ANE program 风险；retained runtime-clone/transformer handle cache 已因 RSS 风险不允许 | 结论: 本轮短期目标完成，verdict=`confirmed_python_bridge_fast_path_exhausted_native_materialization_required`。surface-handoff Python/runtime promotion path 关闭，除非 native/private bridge RE 找到 memory-neutral materialization identity change | 下一步: 回到 current-best ledger，针对 `time.pre.eval_sec≈9.51s` 做 q240 time-axis `attention_pre` MIL/operator/component segmentation 静态总结，寻找不增加 retained handles/RSS 的 lower-segmentation carrier，或证明当前模板是本地最小。
2026-06-23 17:05:00 +0800 | 目标: 静态总结 q240 time-axis `attention_pre` MIL/operator/component segmentation，判断是否继续 qchunk 或 generic SDPA carrier | 动作: 1) 用 `_attention_pre_tiled_mil(62,960,960,q)` 生成 q64/q120/q160/q192/q240/q320/q480/q960 MIL 并统计 branches/matmul/softmax/slice/concat；2) 复用 `transformer_only_tiled_pre_qchunk_sweep_20260623.json` 与 `attention_pre_qchunk_compile_gate_analysis_20260623.json`；3) 读取 b62/b4 q240/q480 micro jsonl；4) 读取 `lower_boundary_sdpa.md` 与 `attention_pre_micro_time_sdpa*.json`；5) 写入 `mps/ANE/.ane_runs/json/time_attention_pre_segmentation_static_verdict_20260623.json` 并更新 `docs/ane_state.md` / `docs/ane_next.md` | 证据: q240 为 4 branches / 8 matmuls / 4 softmaxes / 8 slices；q480 为 2 branches / 4 matmuls / 2 softmaxes / 6 slices；q960 单 branch 但 compile fail；既有 sweep 只有 q240/q480 compile，且 q240 wall/eval/axis_pack/RSS 都优于 q480；micro b62 q240 eval `0.18706375s`、q480 eval `0.199159666s`，q240 compile `4.803896125s`、q480 compile `10.145314208s`；generic/builtin SDPA 既有证据显示低利用、高 compile 或 runtime eval boundary | 结论: 本轮短期目标完成，verdict=`confirmed_q240_manual_tiled_attention_pre_is_current_local_minimum`。不要继续 qchunk resweep 或 generic SDPA probe | 下一步: 进入 lower-segmentation carrier / ANE-side layout contract 搜索：只考虑能改变 carrier 本身且不增加 retained handles/RSS 的目标，输出 compile-only probe target 或 blocker。
2026-06-23 17:20:00 +0800 | 目标: 检查既有 ANE artifact/private-framework notes 是否暴露 qchunk 之下的 lower-segmentation attention carrier 或 ANE-side layout contract | 动作: 1) 读取 active `docs/ane_next.md`；2) 检索并抽取 `host_visible_lower_control_dead_end_blocker_package.md`、`request_lowering_static_bridge_note.md`、`artifact_descriptor_surface_probe.md`、`bootkc_rt_operation_description_layout_probe.md`、`lower_boundary_sdpa.md`；3) 汇总 `ane_attention_quick.csv` / `ane_attention_full.csv` 中 public attention family 的成功/失败和利用率；4) 复用 `time_attention_pre_segmentation_static_verdict_20260623.json`；5) 写入 `mps/ANE/.ane_runs/json/lower_attention_carrier_layout_contract_verdict_20260623.json` 并更新 `docs/ane_state.md` / `docs/ane_next.md` | 证据: host-visible descriptor / ANEServices wrapper / H16 send-reply route 已确认无法 replay/reset/rebuild accepted materializer state；`_ANEProgramIOSurfacesMapper` 之后是真正 lower crossing，layout records 是内部 command-handler/materializer records，不是当前安全 host compile input；artifact descriptor/high-level runtime-loadable cache paths 仍无法产生有效 `programHandle`；public explicit attention best quick success 约 `0.446683 TFLOPS` / `2.4816%` utilization，SDPA/builtin SDPA 既有证据低利用/高 compile/存在 eval boundary | 结论: 本轮短期目标完成，verdict=`blocked_no_safe_lower_attention_carrier_or_layout_contract_exposed`。这不证明 firmware/private layer 不可能，只证明当前安全证据没有暴露可运行的 compile-only carrier target | 下一步: pivot 到 host-visible memory-neutral overhead：从 current-best full-path timing rows 生成更细 ledger，分离 q240 `time.pre` eval、axis_pack、read/write、load/cache、free/GC，再选择不会增加 retained handles/RSS 的实现 probe。
2026-06-23 17:35:00 +0800 | 目标: 从 current-best timing rows 选择并测试一个 host-visible memory-neutral overhead target | 动作: 1) 解析 `test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_component_fields_fixed_20260623.private_ane_child/meta.json`，确认 full-path transformer `gc_sec≈1.0972s` 是未关闭的 host-visible overhead；2) 在 `pymss/modules/bs_roformer/private_ane.py::_profile_free_handles` 增加默认关闭 env `PYMSS_PRIVATE_ANE_DEFER_TRANSFORMER_FREE_GC=1`，仍立即 `bridge.free` native handles，仅跳过 transformer family forced Python GC；3) 运行 `/Users/baicai1145/miniconda3/bin/python -m py_compile pymss/modules/bs_roformer/private_ane.py benchmark/private_ane_transformer_layerwise_compare.py benchmark/private_ane_test_clean_benchmark.py`；4) 运行 transformer-only q240 2-layer/4-chunk control 与 env candidate，输出 `benchmark_results/private_ane/transformer_defer_free_gc_control_20260623.json`、`benchmark_results/private_ane/transformer_defer_free_gc_candidate_20260623.json`；5) 写入 `mps/ANE/.ane_runs/json/host_visible_overhead_defer_transformer_free_gc_probe_20260623.json` 并更新 docs | 证据: candidate exact (`max_abs=0`)；GC 从 `0.245011542s` 降到 `0`，wall `15.3080775s -> 15.157188125s`；但 candidate maxrss `1447.0MB -> 1934.25MB`，delta `+487.25MB` | 结论: 本轮短期目标完成，verdict=`falsified_defer_transformer_free_gc_not_promotable_narrow_probe`。该 route 保留为 default-off diagnostic，不得默认启用；除非未来 paired full-path supervisor 证明 RSS/swap 不增，否则不 promotion | 下一步: 生成 closed-route priority ledger：汇总 qchunk/SDPA/lower-carrier/surface-handoff/layout/deferred-GC 等已关闭路线和 current-best timing rows，判断 transformer host-visible路线是否耗尽，或转向 non-transformer host-visible target。
2026-06-23 17:45:00 +0800 | 目标: 生成 closed-route priority ledger，并测试 largest non-transformer knob `fused_mask_estimator_max_outputs` 是否还能 memory-neutral 降低 wall | 动作: 1) 解析 best stable `test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_rerun_20260623.private_ane_child/meta.json`；2) 汇总 non-transformer buckets：mask、ISTFT、band_split、final_norm、STFT；3) 运行 full-path `test_clean.m4a` mask grouping candidate `max_outputs=4`，失败后运行 `max_outputs=3`；4) 读取 child logs/native supervisor，确认失败点；5) 写入 `mps/ANE/.ane_runs/json/closed_route_priority_ledger_20260623.json` 并更新 docs | 证据: best stable wall `27.649230875016656s`，transformer `24.61669554200489s`，non-transformer estimate `3.032535333011765s`；mask bucket `0.8139545s` 是最大 non-transformer target，但 `max_outputs=4` 在 `mask_fused_0_4` compile 失败 `InvalidMILProgram`，`max_outputs=3` 在 `mask_fused_0_3` compile 失败 `InvalidMILProgram` | 结论: 本轮短期目标完成，verdict=`confirmed_transformer_host_visible_routes_exhausted_for_now_mask_grouping_closed`。当前 host-visible transformer 路线已基本耗尽，mask grouping >2 也关闭 | 下一步: 只剩 sub-second host-visible non-transformer targets；先检查 ISTFT/IRFFT `0.591423s` bucket 是否有 memory-neutral probe，否则 formal pivot 到新的 private lower-layer evidence。
2026-06-23 17:59:41 +0800 | 目标: 完成 ISTFT/IRFFT host-visible bucket 的 memory-neutral probe | 动作: 1) 验证 `closed_route_priority_ledger_20260623.json`；2) 解析 best stable ISTFT timing：wall `0.5914230409543961s`、eval `0.29928666388150305s`、overlap-add `0.024029207008425146s`、route `load_cache_skip_source_write`；3) 运行 full-path `test_clean.m4a` probe：`/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_test_clean_benchmark.py --baseline none --audio test_clean.m4a --full-audio --private-ane-allow-long-audio --private-ane-child-timeout-sec 600 --private-ane-chunk-batch-size 0 --private-ane-auto-chunk-batch-max 4 --private-ane-tiled-time-attention-pre --private-ane-tiled-time-attention-pre-q-chunk 240 --private-ane-fused-band-split --private-ane-fused-band-split-max-outputs 4 --private-ane-fused-mask-estimator --private-ane-fused-mask-estimator-max-outputs 2 --private-ane-persistent-aux-handles --private-ane-dynamic-stft --private-ane-persistent-stft-handles --private-ane-preload-stft-handles --private-ane-load-cache --private-ane-keep-tmpdir --private-ane-skip-source-write-on-cache-hit --private-ane-stft-istft-batch-channels --out benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_batchch_istft_20260623.json`；4) 写入 `mps/ANE/.ane_runs/json/istft_irfft_batch_channel_verdict_20260623.json` 并更新 `docs/ane_state.md` / `docs/ane_next.md` | 证据: child log `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_batchch_istft_20260623.private_ane_child/child.log`；probe 到达 `istft_start` 且先释放 50 个 aux handles，随后 `irfft_0_128_b2` compile 失败，ANECompiler 返回 `InvalidMILProgram`；watchdog 记录 swap growth `0`，失败类别不是 memory guard | 结论: 本轮短期目标完成，verdict=`falsified_istft_batch_channel_not_promotable_compile_failed`。现有 ISTFT per-channel ANE IRFFT + CPU overlap-add 路线保持；batch-channel ISTFT 不得 promotion；GPU ISTFT 只可作为 diagnostic，不作为 ANE 目标路线 | 下一步: 进入 band split host-visible bucket (`0.525994208001066s`)：检查 fused band split grouping/timing rows，若没有 memory-neutral grouping/cache/load knob，则关闭该 bucket 并 pivot 回 private lower-layer transformer evidence。
2026-06-23 18:14:30 +0800 | 目标: 完成 band split host-visible bucket 的 memory-neutral grouping/cache-load probe | 动作: 1) 解析 best stable band split timing：wall `0.525994208001066s`、compile/load `0.30077737307874486s`、eval `0.14639436668949202s`、write `0.06586439738748595s`、fused groups `17`、outputs `62`、`max_outputs_per_group=4`、route `load_cache_skip_source_write`；2) 运行 current-code 1s compile-gate probe `max_outputs=8`，输出目录 `benchmark_results/private_ane/test_clean_1s_private_fused_band_split_grouped8_current_20260623.private_ane_child`；3) 运行 smallest-larger current-code compile-gate probe `max_outputs=5`，输出目录 `benchmark_results/private_ane/test_clean_1s_private_fused_band_split_grouped5_current_20260623.private_ane_child`；4) 写入 `mps/ANE/.ane_runs/json/band_split_grouping_compile_gate_verdict_20260623.json` 并更新 `docs/ane_state.md` / `docs/ane_next.md` | 证据: `max_outputs=5` 在 `band_split_l2_fused_0_5` ANE compile failed，ANECompiler `InvalidMILProgram`，parent result json 未写出，watchdog `max_swap_growth_mb=0`；`max_outputs=8` 同样在 `band_split_l2_fused_0_8` compile failed，`InvalidMILProgram`，watchdog `max_swap_growth_mb=0` | 结论: 本轮短期目标完成，verdict=`falsified_band_split_larger_grouping_not_promotable_compile_failed`。当前 fused band split `max_outputs_per_group=4` 是该 host-visible carrier 的编译边界；不得重复 larger grouping probe，除非有新的 MIL/layout hypothesis | 下一步: 停止把 sub-second non-transformer bucket 作为主加速目标；进入 private lower-layer transformer evidence loop，寻找能减少 q240 segmented transformer eval/load 且不增加 RSS 的 carrier/layout/materialization control point。
2026-06-23 18:26:28 +0800 | 目标: 从已有 lower-layer RE 文档与 IDA 状态中寻找新的 safe compile-only transformer target | 动作: 1) 使用 `reverse-engineering` 与 `ida-reverse` 方法；2) 验证当前 `docs/ane_next.md` lower-layer target；3) 读取 `host_visible_lower_control_dead_end_blocker_package.md`、`request_lowering_static_bridge_note.md`、`artifact_descriptor_surface_probe.md`、`bootkc_rt_operation_description_layout_probe.md`、`lower_boundary_sdpa.md`、`lower_layer_entry_package.md` 及相关 JSON verdict；4) 调用 `ida-pro-mcp idb_list`，结果 open sessions `0`；5) 快速探测本机二进制：标准 `ANEServices.framework` / `ANECompiler.framework` / `Espresso.framework` 路径未命中，`/System/Library/KernelCollections/BootKernelExtensions.kc` 与 `SystemKernelExtensions.kc` 存在；6) 用 `strings` 快速扫描 KC，`BootKernelExtensions.kc` 有 IOSurface/IOSurfaceRoot 字符串，未找到 AppleNeuralEngine / `ANE_RestoreState` / `aneCmdSend`；7) 写入 `mps/ANE/.ane_runs/json/lower_layer_transformer_target_audit_20260623.json` 并更新 docs | 证据: 既有 blocker 仍指向 H16-visible send/reply shell 以下的 firmware-private 或 IOProcessor/interrupt writeback；`lower_attention_carrier_layout_contract_verdict_20260623.json` 明确无 safe writable host-visible lower-carrier field；`lower_layer_entry_package.md` 要求下一步优先 selector-9 dispatch，否则 IOSurface/IOSurfaceRoot superbuffer interpretation；IDA MCP 当前无 open session | 结论: 本轮短期目标完成，verdict=`confirmed_no_new_safe_compile_only_lower_target_in_current_evidence`。这不是全局 dead-end，而是关闭当前 host-visible compile-only 继续猜测；下一步必须转入 static IDA lower-layer entry | 下一步: 创建或接管 `/System/Library/KernelCollections/BootKernelExtensions.kc` 的 IDA session，优先定位 IOSurfaceRoot / `IOSurfaceAllocateFromSuperbuffer` / `createSurface`；若之后解析到 AppleNeuralEngine.kext 路径，则优先 selector-9 dispatch/state-path。
2026-06-23 18:43:58 +0800 | 目标: 创建/adopt BootKC IDA session 并静态定位 IOSurfaceRoot / `IOSurfaceAllocateFromSuperbuffer` lower-layer entry | 动作: 1) 直接 `idb_open(/System/Library/KernelCollections/BootKernelExtensions.kc)` 失败；2) 复制到 `mps/ANE/ida_inputs/BootKernelExtensions.kc` 后再次 `idb_open`，工具层 300s timeout 但 worker 实际成功创建 session `bootkc_iosurface_20260623`；3) `server_health` 确认 `auto_analysis_ready=true`、`hexrays_ready=true`、strings cache `136393`；4) 查询 `IOSurfaceRoot|IOSurfaceAllocateFromSuperbuffer|createSurface|Superbuffer` strings/names/xrefs；5) decompile `IOSurfaceRoot::create_surface_internal`、`IOSurfaceRootUserClient::create_surface`、`IOSurface::init`，并 disasm `IOSurface::parse_properties` tail；6) 添加 IDA bookmarks；7) 写入 `mps/ANE/.ane_runs/json/bootkc_iosurface_superbuffer_ida_entry_20260623.json` 并更新 docs | 证据: `_kIOSurfaceAllocateFromSuperbuffer=0xffffff8002ba7118`，`_kIOSurfaceSuperbuffer=0xffffff8002ba7120`，`IOSurfaceRootUserClient::create_surface=0xffffff8002b9492c`，`IOSurfaceRoot::create_surface_internal=0xffffff8002b8f8b2`，`IOSurface::init=0xffffff8002b7cd66`，`IOSurface::parse_properties=0xffffff8002b7d2b0`；`_kIOSurfaceAllocateFromSuperbuffer` 只有一个函数 xref，在 `create_surface` 中作为 OSNumber/memory-pool id，随后 `getPool` / `taskCanUsePool` / `create_surface_internal`；`_kIOSurfaceSuperbuffer` 当前无 direct xref；`create_surface_internal` 只做 alloc/init/register；`IOSurface::init` 调用 `parse_properties` 后 allocate backing memory | 结论: 本轮短期目标完成，verdict=`confirmed_bootkc_iosurface_superbuffer_path_recovered_static_entry`。BootKC/IOSurface lower entry 可静态分析，但当前证据显示 superbuffer 是 memory-pool/surface-allocation路径，还不是 ANE-specific carrier/materializer field | 下一步: 在 session `bootkc_iosurface_20260623` 中切片 `IOSurface::parse_properties`、`IOSurfaceRoot::lookupMemoryRegion`、`IOSurfaceMemoryPoolBunch::getPool`，只寻找 ANE accepted-state/materializer 相关 consumer；若没有，则关闭 IOSurface 作为 supporting allocation layer。
2026-06-23 18:54:06 +0800 | 目标: 完成 BootKC IOSurface superbuffer / memory-region lower-layer closure check，判断其是否是 ANE transformer accepted-state/materializer control point | 动作: 1) 使用 `ane-consumer-benchmark`、`ida-reverse`、`reverse-engineering` 方法；2) 复核 `docs/ane_next.md` 当前 phase/sub-goal；3) 通过 IDA MCP 复用 session `bootkc_iosurface_20260623`，确认 `auto_analysis_ready=true`、`hexrays_ready=true`、strings cache `136393`；4) decompile/slice `IOSurfaceRoot::lookupMemoryRegion`、`IOSurfaceMemoryPoolBunch::getPool`、`IOSurfaceMemoryPool::taskCanUsePool`、`IOSurfaceRoot::newWiredMemoryDescriptorFromMemoryPool`、`IOSurfaceMemoryRegion::init`、`IOSurface::allocate`，并查询 `IOSurfaceAllocateFromSuperbuffer` / `IOSurfaceSuperbuffer` / `IOSurfaceMemoryRegion` xrefs；5) 写入 `mps/ANE/.ane_runs/json/bootkc_iosurface_memory_region_closure_20260623.json` 与 CSV；6) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: `lookupMemoryRegion` 只是 root dictionary lookup + `IOSurfaceMemoryRegion` safe-cast/retain；`getPool` 是 pool-id linked-list lookup；`taskCanUsePool` 是 owner/kernel/entitlement gate；`newWiredMemoryDescriptorFromMemoryPool` 串联 `getMemoryPoolBunch -> getPool -> taskCanUsePool -> newWiredMemoryDescriptorWithLength`；`IOSurfaceMemoryRegion::init` 只保存 root、分配 lock、读取/retain dictionary object；`IOSurfaceAllocateFromSuperbuffer` xrefs 仅 `IOSurface::parse_properties` 与 key global，`IOSurfaceSuperbuffer` 仅 key global；scoped search 未发现 ANE/Neural/Program/Command/State/Restore/materializer consumer | 结论: 本轮短期目标完成，verdict=`confirmed_iosurface_superbuffer_is_supporting_allocation_layer_not_transformer_carrier`。IOSurface 是 supporting allocation layer，不能解释或根治 q240 transformer segmented eval/load overhead | 下一步: 回到 current q240 transformer runtime bottleneck，做 component-level `attention_pre` ledger/codegen knob probe，只允许 memory-neutral 路线；不重复 IOSurface、generic qchunk、SDPA、retained-handle probes。
2026-06-23 19:08:00 +0800 | 目标: 审计 current q240 time-axis `attention_pre` host-visible route candidates，判断是否还有 memory-neutral runtime probe 值得执行 | 动作: 1) 复用 current-best profiler ledger `current_best_component_bottleneck_ledger_20260623.json`；2) 复核 source 中 `_attention_pre_tiled_mil`、`_tiled_attention_pre_axis`、`_attention_pre_mil_for_axis` 相关 gating；3) 复核 qchunk/static verdict、forced all-layer q240 exactness localization、materialized pre_gate boundary、two-input gate compile、surface handoff、retained handle、IOSurface closure证据；4) 写入 `mps/ANE/.ane_runs/json/time_attention_pre_route_candidate_audit_20260623.json` 与 CSV；5) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: current-best transformer `24.871128999977373s`，eval `19.867204998852685s`，compile `1.9713062929804437s`，`time.pre.eval_sec=9.508778334013186s`，`time.axis_pack_sec=2.45342729089316s`；q240 是当前 manual MIL local minimum，q480 更慢/更高 RSS，其他 qchunk compile-fail；forced all-layer q240 standalone pre exact但 pre_gate/full 不 exact，two-input gate 全部 `InvalidMILProgram`，materialized pre_gate 仍 non-exact，surface handoff wall/RSS 变差，retained handles/RSS 路线关闭，IOSurface 为 allocation layer | 结论: 本轮短期目标完成，verdict=`confirmed_no_current_host_visible_memory_neutral_attention_pre_candidate`。当前慢速根因是 segmented transformer execution + layout/materialization/dispatch，特别是 time-axis attention_pre，而不是单个未调 qchunk 或 load-cache miss | 下一步: 转向 non-IOSurface lower-layer transformer carrier/layout contract 或 accepted-state/materializer hook；若现有证据没有该 hook，写 lower-carrier blocker，不再跑 host-visible qchunk/SDPA/forced-layer/retained-handle runtime sweep。
2026-06-23 19:19:28 +0800 | 目标: mine existing private-framework/BootKC lower-layer evidence，寻找 non-IOSurface transformer carrier/layout contract 或 accepted-state/materializer hook | 动作: 1) 使用 `reverse-engineering`、`ida-reverse`、`ane-consumer-benchmark` 方法；2) 读取 current canonical `docs/ane_next.md`；3) 复核 `host_visible_lower_control_dead_end_blocker_package.md`、`lower_layer_entry_package.md`、`request_lowering_static_bridge_note.md`、`bootkc_rt_operation_description_layout_probe.md`、`lower_attention_carrier_layout_contract_verdict_20260623.json`、`layout_contract_axis_pack_blocker_20260623.json`、`fused_time_freq_layout_primitive_compile_matrix_20260623.json`、`non_h16_*_carrier_20260623.json`、`resource400d0_deeper_materializer_boundary_20260623.json`、`record1b8_visible_send_shell_author_blocker_20260623.json`、`typed_completion_no_record_author_boundary_20260623.json`、selector wrapper verdicts；4) 用 IDA MCP 在 `bootkc_iosurface_20260623` 搜索 `AppleNeuralEngine`、`ANE_RestoreState`、`aneCmdSend`、`ANEFirmware`、`ANEProgram`、`ANEServices` 等；5) 写入 `mps/ANE/.ane_runs/json/non_iosurface_lower_carrier_evidence_audit_20260623.json` 与 CSV；6) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: current-best profiler 仍为 transformer `24.871128999977373s`、eval `19.867204998852685s`、compile `1.9713062929804437s`、`time.pre.eval_sec=9.508778334013186s`、`time.axis_pack_sec=2.45342729089316s`；host-visible lower-control package 已证明 descriptor/ANEServices/H16 send-reply 不能 rebuild accepted state；layout blocker 需要 fused time+freq/ANE-side repack/shared native layout，但 padding concat layout primitive compile-fails；non-H16 daemon artifacts only expose programHandle/programInstance wrappers；resource400d0/record1b8 authors remain below visible surfaces；active BootKC session has no AppleNeuralEngine/ANE_RestoreState/aneCmdSend/ANEProgram matching strings/functions/names/text | 结论: 本轮短期目标完成，verdict=`blocked_no_non_iosurface_safe_lower_carrier_in_current_evidence`。这不是 global dead-end，但当前证据没有可安全使用的 non-IOSurface carrier/layout/materializer control | 下一步: 搜索本机 filesystem/KC/dyld cache 中 concrete AppleNeuralEngine-containing binary or reusable IDA input；若没有，写 machine-local target-availability blocker，不重复 descriptor/selector/qchunk/SDPA/retained-handle/IOSurface/daemon-wrapper probes。
2026-06-23 19:32:00 +0800 | 目标: 搜索本机 filesystem/KC/dyld cache 中 concrete AppleNeuralEngine-containing binary or reusable IDA input | 动作: 1) 搜索 `/System/Library`、`/Library`、`/usr/lib`、`mps/ANE` 的 `AppleNeuralEngine`/`ANE`/`Neural` 文件名；2) 检查 `/System/Library/PrivateFrameworks` 与 CommandLineTools SDK 中 `ANECompiler`、`ANEServices`、`Espresso`、`CoreML`、`NeuralNetworks` framework contents；3) 检查 BootKC/SystemKC strings；4) 检查 Preboot dyld cache 目录与 `dyld_shared_cache_arm64e.map`；5) 查询 `dyld_shared_cache_util`、`dsc_extractor`、`dyld_extract`、`dyldex`、`jtool2`、`ipsw`；6) 对 dyld cache 做只读 strings 抽样；7) 写入 `mps/ANE/.ane_runs/json/apple_neural_engine_target_availability_20260623.json` 与 CSV；8) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: visible framework `Versions/A` 只有 Resources/_CodeSignature/XPCServices，无 executable image；CommandLineTools SDK 只有 `ANECompiler.tbd`、`ANEServices.tbd`、`Espresso.tbd` stubs；BootKC/SystemKC 无 AppleNeuralEngine/ANE_RestoreState/aneCmdSend hits；Preboot dyld cache map lists `/System/Library/PrivateFrameworks/AppleNeuralEngine.framework/Versions/A/AppleNeuralEngine`、`ANEServices`、`ANECompiler`、`ANEClientSignals`、`Espresso`、`NeuralNetworks`、`CoreML`；dyld cache strings include `ANEVirtualClient`、`_ANEProgramForEvaluation processRequest`、`_ANEProgramIOSurfacesMapper`、`programHandle`、`programInstance`、compile/load/unload/evaluate dictionary method errors；local extraction tools are missing | 结论: 本轮短期目标完成，verdict=`confirmed_apple_neural_engine_target_present_in_dyld_cache_extraction_missing`。目标存在于 Preboot dyld shared cache；当前 blocker 是 extraction/import tooling，而不是目标不存在 | 下一步: 找到或安装 safe dyld shared cache extraction/import tool，只提取 AppleNeuralEngine/ANEServices/ANECompiler 到 `mps/ANE/ida_inputs/`，创建/adopt AppleNeuralEngine IDA session 后分析 selector/state path；不要 attach daemon 或跑 inference。
2026-06-23 19:40:00 +0800 | 目标: 安装或定位 safe dyld shared cache extraction tool，并尝试 narrow AppleNeuralEngine extraction | 动作: 1) 安装 PyPI `dyldextractor==2.2.2` 到 `/Users/baicai1145/miniconda3`；2) 确认 entrypoints `dyldex`、`dyldex_all`、`kextex`、`kextex_all`；3) 用 `DyldExtractor.dyld.dyld_context.DyldContext` 直接解析 Preboot split cache；4) 列出 ANE 相关 image map；5) 尝试提取 `/System/Library/PrivateFrameworks/AppleNeuralEngine.framework/Versions/A/AppleNeuralEngine` 到 `mps/ANE/ida_inputs/dyld_extracted`；6) 写入 `mps/ANE/.ane_runs/json/dyld_extractor_tooling_probe_20260623.json` 与 CSV；7) 更新 docs | 证据: `DyldContext` 成功加载 `3646` images；image hits: `ANEServices=0x19e68b000`、`AppleNeuralEngine=0x19f90e000`、`ANECompiler=0x222d54000`、`ANEClientSignals=0x22ffa3000`、`libORTools=0x22ffa5000`；`dyldex` extraction 在 conda Python `3.13.12` 下失败：`TypeError: can only concatenate str (not "int") to str`；未生成 extracted Mach-O；可用替代 runtime：`/usr/bin/python3` 3.9.6、`/opt/homebrew/bin/python3` 3.14.5；Homebrew search 有 `jtool2` | 结论: 本轮短期目标完成，verdict=`inconclusive_extractor_installed_cache_parsed_extraction_failed`。目标和 parser 都可用，blocker 缩小为 extraction implementation/runtime 兼容性 | 下一步: 用 system Python 3.9 venv 或 Homebrew `jtool2` 重试，只提取 AppleNeuralEngine/ANEServices/ANECompiler；成功后打开 AppleNeuralEngine IDA session。
2026-06-23 20:18:00 +0800 | 目标: 完成 AppleNeuralEngine/ANEServices/ANECompiler dyld-cache extraction and IDA import，解除 user-space private framework RE blocker | 动作: 1) 使用 `ane-consumer-benchmark`、`reverse-engineering`、`ida-reverse` 方法；2) 创建 system-Python `3.9` venv `mps/ANE/.tmp/dyldextractor39` 并安装 `dyldextractor==2.2.2`，确认仍复现 `TypeError: can only concatenate str (not "int") to str`；3) 安装 Homebrew `jtool2`，确认其对当前 split cache probe 不可用（`rc=137`）；4) 新增并编译 `mps/ANE/experiments/dsc_extract_call.c`，调用 `/usr/lib/dsc_extractor.bundle`；5) 成功提取 Preboot dyld cache 到 `mps/ANE/ida_inputs/dyld_extracted`；6) 用 `file`/`otool`/`strings` 验证 `AppleNeuralEngine`、`ANEServices`、`ANECompiler`；7) 通过 IDA MCP 打开 `AppleNeuralEngine` 为 session `apple_neural_engine_dyld_20260623`；8) survey 并查询 `_ANEVirtualClient` compile/load/evaluate/precompiled/cache functions；9) 写入 `mps/ANE/.ane_runs/json/dyld_apple_neural_engine_extraction_import_20260623.json` 与 CSV；10) 更新 `docs/ane_state.md` 与 `docs/ane_next.md` | 证据: profiler context unchanged，current best wall `27.649230875016656s`，transformer `24.871128999977373s`，transformer eval `19.867204998852685s`，`time.pre.eval_sec=9.508778334013186s`，`time.axis_pack_sec=2.45342729089316s`，native max child RSS `1660.547MB`；`dsc_extractor` `rc=0`，processed `3646` images，`real 152.88s`，输出 `3646` files / `5.2G`；extracted `AppleNeuralEngine` `680K` imagebase `0x19f90e000`，`ANEServices` `292K` imagebase `0x19e68b000`，`ANECompiler` `45M` imagebase `0x222d54000`；IDA open-time health reported `auto_analysis_ready=true`，final post-query health reported `auto_analysis_ready=false` but `hexrays_ready=true` and strings cache `2258`；survey recovered functions `3466`；key functions include `compileModel=0x19f92a5e4`、`loadModel=0x19f92c158`、`loadModelNewInstance=0x19f92cec0`、`unloadModel=0x19f9302cc`、`evaluateWithModel=0x19f930d54`、`doEvaluateWithModel=0x19f931bbc`、`mapIOSurfaces=0x19f936b44`、`callIOUserClientWithDictionary=0x19f93fa34`、`shouldUsePrecompiledPath=0x19f941238`、`compiledModelExistsFor=0x19f933c04`；strings include `ANEVirtualClient`、compile/load/unload/evaluate dictionary methods、`programHandle`、`intermediateBufferHandle`、`cacheURLIdentifier`、`kANEFModelPreCompiled`、`_ANEF_COMPILED_MODEL_EXISTS`、`_ANEF_PURGE_COMPILED_MODEL` | 结论: 本轮短期目标完成，verdict=`confirmed_dsc_extractor_produced_ida_usable_apple_neural_engine_targets`。当前 blocker 已从 extraction/import 转为具体 `_ANEVirtualClient` dictionary/IOUserClient route semantics | 下一步: 在 `apple_neural_engine_dyld_20260623` 中切片 `compileModel`、`loadModel`、`loadModelNewInstance`、`doEvaluateWithModel`、`mapIOSurfacesWithModel`、`callIOUserClientWithDictionary`、`shouldUsePrecompiledPath`、`compiledModelExistsFor`，记录 selector IDs、dictionary keys、cacheURLIdentifier/precompiled gates、IOSurface transfer fields，以及是否存在 durable `programHandle` / `intermediateBufferHandle` reuse control。
2026-06-23 21:10:00 +0800 | Goal: close the AppleNeuralEngine user-space VirtualClient route loop and decide whether supported cache/precompiled/dictionary controls can reduce repeated transformer load/eval without increasing RSS | Actions: used `ida-reverse`, `reverse-engineering`, and `ane-consumer-benchmark` methodology; queried live IDA session `apple_neural_engine_dyld_20260623`; sliced `callIOUserClientWithDictionary`, cache exists/purge functions, `loadModel`, `_ANEModel updateModelAttributes`, `_ANEProgramForEvaluation programWithHandle`, `doEvaluateWithModel`, and `doMapIOSurfacesWithModel`; wrote `mps/ANE/.ane_runs/json/apple_neural_engine_virtualclient_route_semantics_20260623.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: current best profiler remains `test_clean.m4a` wall `27.649230875016656s`, transformer `24.871128999977373s`, eval `19.867204998852685s`, compile `1.9713062929804437s`, `time.pre.eval_sec=9.508778334013186s`, `time.axis_pack_sec=2.45342729089316s`, RSS `1660.547MB`; dictionary wrapper at `0x19f93fa34` uses selector `0x10`; cache commands `5/6/7/8` confirmed; `loadModel` installs post-load handles at `0x19f92c894` and `0x19f92c8b0`; evaluate direct selector `0x13` at `0x19f93300c`; map raw command `0xD` at `0x19f937984`; precompiled path is internal-build/capability gated | Conclusion: short-term loop complete, verdict=`confirmed_user_space_wrapper_no_supported_persistent_reuse_control`; user-space AppleNeuralEngine wrapper does not expose a supported memory-neutral persistent transformer segment reuse control | Next: open/adopt `ANEServices` and `ANECompiler` IDA sessions and trace selector `0x10` command `2` load and selector `0x13` evaluate into lower accepted-state/materializer or artifact-control logic.
2026-06-23 21:28:00 +0800 | Goal: test whether `ANEServices` / `ANECompiler` expose a lower accepted-state, materializer, or artifact-control route beyond AppleNeuralEngine post-load handles | Actions: opened and saved IDA sessions `ane_services_dyld_20260623` and `ane_compiler_dyld_20260623`; surveyed `ANEServices`; ran targeted string scans in both frameworks; decompiled `ANEServicesDevice::ANE_ProgramCreate`, `ANE_ProgramCreateInstance`, `ANE_ProgramSendRequest`, `ANERequestReceiver::ProgramProcessRequest`, and `ANEHWDevice::ANE_SendCommand`; wrote `mps/ANE/.ane_runs/json/ane_services_lower_route_semantics_20260623.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: `ANEServices` exposes `ANEServicesProgramCreate`, `ANEServicesProgramCreateNewInstance`, `ANEServicesProgramProcessRequestDirect`, `ANERequestReceiver::ProgramProcessRequest`, and `ANEServicesDevice::ANE_ProgramSendRequest`; `ANECompiler` targeted runtime string scan only found `CompileANEProgramForDebugging`; `ANE_ProgramCreate` at `0x19e69d07c` calls `IOConnectCallStructMethod` selector `3`; `ANE_ProgramCreateInstance` at `0x19e69d248` calls selector `8`; `ANE_ProgramSendRequest` at `0x19e69dbc0` calls `IOConnectCallAsyncMethod` selector `2` with request struct size `0x948`; `ANEHWDevice::ANE_SendCommand` at `0x19e69f42c` is property read/write only in this evidence | Conclusion: short-term loop complete, verdict=`confirmed_ane_services_runtime_wrapper_no_supported_materializer_reuse_control`; ANEServices is still a runtime wrapper/request packer layer, not the durable memory-neutral transformer segment-reuse author | Next: trace kernel/user-client handlers for selectors `3`, `8`, and `2`, or write a precise target-availability blocker if the required handler binary/session is unavailable.
2026-06-23 21:32:04 +0800 | Goal: answer the target-availability question for ANEServices selectors `3`, `8`, and `2`, and determine whether current BootKC evidence exposes a memory-neutral reuse/materializer control | Actions: used `ida-reverse`, `reverse-engineering`, and `ane-consumer-benchmark` methodology; reopened local BootKC as IDA session `bootkc_ane_dispatch_20260623`; spot-checked ANEServices IDA decompilation for selectors `3`, `8`, and `2`; reused existing BootKC dispatch/user-client CSVs and selector-3/selector-8 notes; wrote `mps/ANE/.ane_runs/json/selector_3_8_2_handler_availability_20260623.json` and CSV peer; updated `docs/ane_state.md` and rewrote `docs/ane_next.md` with short recovery lines | Evidence: selector `3` wrapper `0x19e69d07c` uses `IOConnectCallStructMethod` input `0xd88`, output `0xac738`, but BootKC visible client row `3` is `ANE_ProgramCreate` with `0x20 -> 0x0`; selector `8` wrapper `0x19e69d248` uses input `0x35e18`, output `0xac738`, but BootKC visible client row `8` is `ANE_ProgramCreateInstance` with `0x20 -> 0x0`; selector `2` wrapper `0x19e69dbc0` uses `IOConnectCallAsyncMethod` input `0x948`, output `0x28`, matching BootKC visible client row `2`; `mps/ANE/ida_inputs/BootKernelExtensions.kc` is reported as x86_64 and is not the matching arm64e H16 decompilation context; current best profiler remains wall `27.649230875016656s`, transformer `24.871128999977373s`, eval `19.867204998852685s`, compile `1.9713062929804437s`, `time.pre.eval_sec=9.508778334013186s`, `time.axis_pack_sec=2.45342729089316s`, RSS `1660.547MB`, swap growth `0` | Conclusion: short-term loop complete, verdict=`confirmed_selector_3_8_2_handler_family_available_but_no_supported_memory_neutral_reuse_control_yet`; target handlers are available through existing BootKC evidence, selector `2` is the visible eval path, and selector `3/8` lower/repack large descriptors below the visible dispatch row, but no safe memory-neutral reusable transformer materializer is proven yet | Next: reconstruct or reopen the matching arm64e/raw Preboot BootKC context, then run a focused lower-consumer loop for `ANE_ProgramCreateInstance` and `ANE_ProgramSendRequest`.
2026-06-23 21:51:26 +0800 | Goal: restore the matching arm64e H16 context and classify the first selector `8` / selector `2` lower chain for memory-neutral materializer controls | Actions: opened `mps/ANE/.ane_runs/tmp/AppleH16ANEInterface.patched.macho` as IDA session `apple_h16_ane_interface_20260623`; verified `/tmp/KMUtilProducts/BootKernelCollection.kc` is arm64e and the H16 patched Mach-O is arm64e; queried symbols for selector `8` and selector `2`; decompiled `ANE_ProgramCreateInstance`, `ANEDriver::ANE_ProgramCreateInstance_gated`, `ANEHWDevice::ANE_ProgramCreateInstance`, `ANEHWDevice::ANE_ProgramCreateInstance_gated`, `ANE_ProgramSendRequest`, `ANEDriver::ANE_ProgramSendRequest`, `ANEHWDevice::ANE_ProgramSendRequest_gated`, `lookupProgramResource`, and related staged functions; wrote `mps/ANE/.ane_runs/json/h16_selector8_selector2_lower_path_20260623.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: H16 IDA imagebase `0xfffffe000743d780`, health `auto_analysis_ready=true`, `hexrays_ready=true`; selector `8` wrapper `0xfffffe00093483c8` checks `0x35e18 -> 0xac738` then dispatches; driver gated `0xfffffe0009271a3c` creates program handle and calls `addProgramToANEMapping_gated`; device gated `0xfffffe000928c5ec` validates args/procedure count/weight-buffer count and enters descriptor/process/load/patch subpaths; selector `2` wrapper `0xfffffe0009347b3c` validates async request state; driver entry `0xfffffe00092724bc` selects ANE and writes selected context at request offset `2360`; device path includes `0xfffffe0009297418`, `0xfffffe00092977e8`, `0xfffffe0009299b34`, `0xfffffe00092929a0`, and `0xfffffe000928ff28`; profiler unchanged: wall `27.649230875016656s`, transformer `24.871128999977373s`, eval `19.867204998852685s`, `time.pre.eval_sec=9.508778334013186s`, `time.axis_pack_sec=2.45342729089316s`, RSS `1660.547MB`, swap growth `0` | Conclusion: short-term loop complete, verdict=`confirmed_matching_h16_context_and_first_lower_chain_no_direct_authorable_materializer`; the visible H16 selector `8` first chain is handle/mapping/descriptor-validation oriented, and selector `2` first chain is request validation/lookup/prepare/firmware-submit oriented; no direct memory-neutral accepted-state materializer has been recovered yet | Next: analyze `ANEHWDevice::ANE_ProgramPrepareAndSubmitRequest_gated` and `ANEHWDevice::updateRequestFWCommand` to determine whether repeated time-axis `attention_pre` eval is caused by request rebuild, DVA update, process remap, mutable/intermediate buffer update, or unavoidable firmware-private submit semantics.
2026-06-23 21:55:35 +0800 | Goal: classify selector `2` eval preparation and firmware-command update work to explain remaining transformer eval slowness | Actions: used IDA session `apple_h16_ane_interface_20260623`; sliced `ANEHWDevice::ANE_ProgramPrepareAndSubmitRequest_gated` at `0xfffffe0009299b34` and `ANEHWDevice::updateRequestFWCommand` at `0xfffffe00092929a0`; queried xrefs to DVA/update/error strings and instruction writes; wrote `mps/ANE/.ane_runs/json/h16_selector2_prepare_submit_materialization_20260623.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: `PrepareAndSubmit` allocates `ANEResourceCollection`, calls `isProcessValid`, calls `ANE_ProgramCheckandPrewireBuffers_gated`, creates `ANERequest`, calls `ANEScheduler::addPendingRequest`, calls `handleIntermediateBufferUpdate`, creates/signals fences/shared events, moves/adds resources, and creates `ANEClientResource`; `updateRequestFWCommand` writes command metadata (`STR W8, [X26,#8]`, `STR W8, [X26,#0xC]`), has xrefs for `Updated intermediate buffer dva`, `updated proc mutable dva address`, and `mutable memory not dart mapped`, and writes command pointers at offsets including `+0x18` and `+0x20`; profiler unchanged: wall `27.649230875016656s`, transformer `24.871128999977373s`, eval `19.867204998852685s`, `time.pre.eval_sec=9.508778334013186s`, `time.axis_pack_sec=2.45342729089316s`, RSS `1660.547MB`, swap growth `0` | Conclusion: short-term loop complete, verdict=`confirmed_selector2_eval_has_per_request_materialization_and_dva_update_work`; remaining transformer eval wall time is best explained by repeated per-request materialization/DVA update/firmware-submit preparation below selector `2`, not load/compile | Next: add or mine runtime per-stage attribution for request create/prewire, process validation/remap, `updateRequestFWCommand`, DVA update, fence/shared-event work, and firmware submit on `test_clean.m4a`, then choose lower-state RE vs graph/layout request-count reduction.
2026-06-23 22:11:35 +0800 | Goal: quantify the current runtime reason for slow private ANE transformer inference and decide the next memory-neutral acceleration direction | Actions: used `ane-consumer-benchmark` and `diagnosing-bugs` methodology; mined existing `test_clean.m4a` component ledger, attention_pre micro-profiles, and H16 selector-2 static RE artifact; generated `mps/ANE/.ane_runs/json/transformer_runtime_selector2_attribution_20260623.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: transformer `24.871128999977373s`, transformer eval `19.867204998852685s`, transformer compile `1.9713062929804437s`, time-axis eval `13.97083224792732s`, time-axis ANE eval-only `10.320496624626685s`, time-axis `pre` eval `9.508778334013186s`, time-axis pack `2.45342729089316s`, native max child RSS `1660.547MB`, native max swap growth `0.0MB`; q240 attention_pre micro-profile remains only about `0.7533643720483468 TFLOPS` for batch 4 and `0.8767725424273536 TFLOPS` for batch 62; selector-2 static evidence includes per-request resource collection allocation, process validation, prewire, `ANERequest` creation, scheduler insertion, intermediate/mutable DVA updates, fences/shared events, firmware command DVA rewrites, and submit preparation | Conclusion: short-term loop complete, verdict=`confirmed_segmented_time_attention_pre_eval_and_selector2_materialization_dominate_remaining_runtime`; the slow speed is segmented eval/layout/materialization overhead, especially time-axis `attention_pre`, not raw ANE compute saturation and not top-level load/compile | Next: inspect the transformer runtime for one memory-neutral graph/layout change that reduces time-axis `attention_pre` segmented request count or axis_pack/DVA-update cost; if no candidate exists, instrument lower selector-2 runtime timestamps.
2026-06-23 22:11:35 +0800 | Goal: audit host-visible graph/layout candidates for reducing time-axis `attention_pre` or `axis_pack` cost without increasing memory | Actions: compared existing `test_clean.m4a` full-path artifacts for non-tiled explicit control, q240 layer-0 tiling, surface handoff, and unpadded freq handoff; checked runtime policy defaults and prior time-axis batch-eval evidence; generated `mps/ANE/.ane_runs/json/time_attention_pre_graph_layout_candidate_audit_20260623.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: explicit-control non-tiled baseline `28.173455959011335s` full path, transformer eval `19.829284292005468s`, time-axis eval `13.969854625000153s`, time-axis pack `2.499261085089529s`, RSS `1639.469MB`, swap growth `0.0MB`; q240 fixed component artifact `28.357753333984874s` full path and transformer eval `19.867204998852685s`; surface handoff `30.064417415997013s`; unpadded freq `29.920132166007534s`; default module value is `private_ane_tiled_time_attention_pre=False`; time batch-axis eval remains disallowed because prior runtime evidence reports multi-GiB wired pressure and native-supervisor kill | Conclusion: short-term loop complete, verdict=`falsified_current_host_visible_graph_layout_candidates_for_memory_neutral_time_attention_pre_speedup`; current host-visible knobs do not safely move the transformer toward ANE peak | Next: add or mine lower selector-2/request timing counters around bridge eval so time-axis `attention_pre` can be split into request creation/prewire, DVA update/`updateRequestFWCommand`, fence/shared-event, firmware submit, read/write, and host pack classes without increasing retained memory.
2026-06-23 22:11:35 +0800 | Goal: determine whether current bridge/native instrumentation can split selector-2 materialization classes inside `eval_sec` without increasing memory | Actions: inspected active Python bridge `benchmark/private_ane_real_attention_probe.py`, active C bridge `mps/maderix_ANE/bridge/ane_bridge.m`, transformer aggregation in `pymss/modules/bs_roformer/private_ane.py`, and H16 selector-2 static RE artifact; generated `mps/ANE/.ane_runs/json/bridge_eval_selector2_timing_boundary_20260623.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: active bridge loads `mps/maderix_ANE/bridge/libane_bridge.dylib`; Python run profiles expose host `cast/alloc/write/eval/read`; C bridge profile exposes compile/load-time fields including `request_create_sec`, but that is request binding during compile/load-cache, not per-eval selector-2 lower `ANERequest` creation; active `ane_bridge_eval` is one private call boundary through `evaluateWithQoS:options:request:error:` or equivalent client/direct-process calls; selector-2 static RE still contains resource collection allocation, process validation, prewire, request creation, scheduler insertion, DVA update, fence/shared-event, firmware command rewrite, and submit preparation | Conclusion: short-term loop complete, verdict=`confirmed_current_bridge_collapses_selector2_materialization_into_opaque_eval_sec`; bridge-only source timing can add outer scalar eval timing but cannot split selector-2 internals | Next: create a minimal dynamic-hook feasibility probe for ANEServices / AppleH16 selector-2 timing targets, starting with user-space ANEServices functions if reachable and falling back to an IDA-guided static blocker if SIP/TCC/kernel tracing prevents safe hooks.
2026-06-23 22:11:35 +0800 | Goal: test whether user-space ANEServices selector-2 wrapper functions are dynamically hookable and timed during a minimal `attention_pre` eval | Actions: used `reverse-engineering` and `ida-reverse` methodology; queried IDA session `ane_services_dyld_20260623` for selector-2 target symbols; verified Frida `17.11.0`; spawned `/Users/baicai1145/miniconda3/bin/python` under Frida with `mps/ANE/.ane_runs/tmp/attention_pre_hook_runner.py`; hooked ANEServices symbols; generated `mps/ANE/.ane_runs/json/aneservices_selector2_frida_timing_feasibility_20260623.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: IDA targets include `ANEServicesDevice::ANE_ProgramSendRequest` `0x19e69dbc0`, `ANERequestReceiver::ProgramProcessRequest` `0x19e6a18e4`, and `ANEServicesProgramProcessRequestDirect` `0x19e6a7d2c`; Frida resolved ANEServices in-process and hooked 18 matching symbols; minimal raw profile `benchmark_results/private_ane/attention_pre_time_b4_frida_spawn_raw_20260623.json` compiled in `0.311602s`, eval mean about `0.017045s`, total mean about `0.017687s`; dynamic hits: `ANEServicesProgramProcessRequestDirect` count `1`, `ANERequestReceiver::ProgramProcessRequest` count `1`, and `ANEServicesDevice::ANE_ProgramSendRequest` count `1`, each about `17 ms` | Conclusion: short-term loop complete, verdict=`confirmed_user_space_aneservices_selector2_hooks_feasible_for_outer_wrapper_timing`; user-space wrapper timing is feasible, but this still does not split kernel/H16 prepare-submit internals | Next: hook or otherwise time the next boundary under `ANEServicesDevice::ANE_ProgramSendRequest`, especially `IOConnectCallAsyncMethod` selector `2`, to separate user-space wrapper time from kernel/H16 selector-2 prepare/submit time.
2026-06-23 22:11:35 +0800 | Goal: hook or time the IOKit selector-2 boundary below `ANEServicesDevice::ANE_ProgramSendRequest` during a minimal `attention_pre` eval | Actions: ran Frida-spawned minimal attention_pre probes; first attempted direct Frida export hooks for `IOConnectCallAsyncMethod`, `IOConnectCallMethod`, and `IOConnectCallStructMethod`; then used ANEServices IDA import pointer offsets for `_IOConnectCallAsyncMethod` `0x19e6b4308`, `_IOConnectCallMethod` `0x19e6b4318`, and `_IOConnectCallStructMethod` `0x19e6b4338`; retried with pointer stripping; generated `mps/ANE/.ane_runs/json/iokit_selector2_hook_boundary_probe_20260623.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: direct Frida export hooks reported `IOKIT_HOOK_MISSING`; ANEServices import slots were found at runtime but target pointers were PAC-signed arm64e values such as `0x9136a231f027ab11`; `Interceptor.attach` failed with access violations even after pointer-strip retry; latest minimal raw profile still ran successfully with eval mean about `0.017500s`; no selector-2 IOKit timing was captured | Conclusion: short-term loop complete, verdict=`inconclusive_iokit_selector2_import_hook_blocked_by_pac_or_non_exported_call_target`; simple Frida export/import-pointer hooks cannot yet time the IOKit boundary | Next: try a PAC-aware or system-level timing route, such as hooking ANEServices call-site instruction addresses, DTrace where permitted, or IDA-derived pre/post call-site offsets before the authenticated branch target.
2026-06-23 23:26:25 +0800 | Goal: determine whether H16 selector-2 lower path exposes a memory-neutral host-authorable reuse/control field for repeated transformer evals | Actions: reopened stale IDA session `apple_h16_ane_interface_20260623`; queried `ANE_ProgramPrepareAndSubmitRequest_gated`, `updateRequestFWCommand`, and `SendRequestToFirmware_gated`; collected exact call-site evidence for resource collection lifetime, prewire, request creation, scheduler insertion/removal, resource wiring/DART mapping, mutable DVA command update, and `aneCmdSend`; generated `mps/ANE/.ane_runs/json/h16_selector2_lower_control_reuse_field_audit_20260623.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: `ANEResourceCollection` allocation/ctor/dtor at `0xfffffe0009299ba8`/`0xfffffe0009299bac`/`0xfffffe000929a024`; prewire at `0xfffffe0009299c60`; `ANERequest::create` at `0xfffffe0009299e5c`; `ANEScheduler::addPendingRequest` at `0xfffffe0009299ec4`; `wireResources`/`dartMapResources` at `0xfffffe000929c80c`/`0xfffffe000929c854`; `updateRequestFWCommand` call at `0xfffffe00092914b4`; `lookupClusterMutableBuffer` at `0xfffffe0009292c28` and `0xfffffe0009293148`; `aneCmdSend` sites include `0xfffffe0009291ac0`, `0xfffffe0009291e5c`, `0xfffffe0009292374` | Conclusion: short-term loop complete, verdict=`falsified_static_h16_host_authorable_memory_neutral_reuse_field`; H16-visible same-layer reuse/control fields are per-request lifecycle or kernel/firmware-private state and are not safe memory-neutral acceleration knobs | Next: measure Python-side transformer time-axis `attention_pre` segment/request-count structure and look for one memory-neutral request-count or pack/unpack reduction candidate without batch-axis promotion or retained handles.
2026-06-23 23:39:00 +0800 | Goal: classify Python-side transformer time-axis `attention_pre` segmentation/request-count structure and identify the next memory-neutral candidate | Actions: inspected current batch-4 transformer timing profile `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_load_cache_bridgeprofile_20260623_profile/transformer_timings.csv`, prior micro-profile artifact `transformer_attention_pre_shape_micro_20260623.json`, closed bridge-pack artifacts, and q240 full-path validation; generated `mps/ANE/.ane_runs/json/transformer_attention_pre_segment_count_audit_20260623.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: transformer CSV has 24 rows = 12 time + 12 freq; time rows carry `bridge_pack_gate=4.0`, `axis_pack_reused=3.0`, `tiled_time_attention_pre=False`, qchunk `0`; using prior micro 4x equivalence, estimated time-axis `attention_pre` selector-2 requests are `48`; time-axis sums are `attention_pre_eval_sec=9.538814419182017`, `attention_pre_total_sec=10.015570706047583`, `axis_pack_sec=2.5199859970016405`, `eval_sec=14.225222417007899`; prior q240 validation had exact matched control `28.173s`, q240 `27.903s`, no RSS/swap increase | Conclusion: short-term loop complete, verdict=`confirmed_time_axis_attention_pre_segment_count_dominates_no_new_memory_neutral_pack_candidate_visible`; repeated time-axis `attention_pre` selector-2 requests plus pack/write/read remain the main reason speed is far from ANE peak | Next: rerun current-worktree explicit q240/skip-source/fused full-path preset on `test_clean.m4a`, record wall/correctness/RSS/swap/transformer breakdown, and decide whether to codify it as documented opt-in baseline while leaving default conservative.
2026-06-23 23:48:00 +0800 | Goal: verify current-worktree explicit q240/skip-source/fused preset as an opt-in baseline candidate | Actions: ran recovered command from `full_path_tiled_q240_skip_source_validation_20260623.json` with new output `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_rerun_20260623.json`; extracted parent result and native supervisor fields; generated `mps/ANE/.ane_runs/json/q240_opt_in_current_worktree_rerun_20260623.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: run completed with wall `38.78787529101828s`; transformer `32.55836379202083s`; transformer compile/load `9.555925211054273s`; transformer eval `20.199491960869636s`; time-axis eval `14.328791043895762s`; time-axis `attention_pre` eval `9.703135077783372s`; time-axis pack `2.600520497362595s`; bridge load-cache hits `123`, misses `0`; native max child RSS `1623.891MB`, max process-group RSS `1637.438MB`, swap growth `0.0MB`; correctness was not checked because command used `--baseline none` | Conclusion: short-term loop complete, verdict=`falsified_current_worktree_q240_preset_promotion_due_compile_regression_and_missing_correctness_check`; q240 cannot be codified from this run even though memory stayed within constraint | Next: run matched explicit skip-source/fused non-q240 control on current worktree and compare compile/eval/RSS/swap to determine whether slowdown is q240-specific or global cache-state/worktree regression.
2026-06-23 23:58:00 +0800 | Goal: run matched explicit non-q240 control and classify whether current q240 slowdown is q240-specific or global cache/worktree state | Actions: ran recovered control command with output `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_skip_source_explicit_control_rerun_20260623.json`; compared against q240 rerun; generated `mps/ANE/.ane_runs/json/q240_vs_control_current_worktree_cache_regression_20260623.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: control wall `39.23634491697885s`, transformer `32.27579816698562s`, transformer compile/load `9.136685500969179s`, transformer eval `20.17042325309012s`, time-axis eval `14.337507542106323s`, time-axis `attention_pre` eval `9.773464999743737s`, time-axis pack `2.52339941682294s`, native max child RSS `1660.484MB`, swap growth `0.0MB`; q240 rerun wall `38.78787529101828s`; both report bridge load-cache hits `123` and misses `0`; neither rerun checked correctness due `--baseline none` | Conclusion: short-term loop complete, verdict=`confirmed_global_compile_cache_state_regression_not_q240_specific`; current slowdown is cache/load/materialization-state regression, not q240-specific, and memory did not increase | Next: compare prior under-30 validation artifacts against current q240/control reruns at bridge-profile identifier/tmpdir/load_qos/compile_qos level to explain why load-cache-hit runs now spend about 9s in transformer compile/load.
2026-06-23 22:11:35 +0800 | Goal: try PAC-aware or system-level timing for the IOKit selector-2 boundary using ANEServices call-site offsets or DTrace | Actions: used IDA disassembly for `ANEServicesDevice::ANE_ProgramSendRequest`; located `BL _IOConnectCallAsyncMethod` at static `0x19e69dcf8` and post-call instruction `0x19e69dcfc`; ran a Frida inline call-site hook at runtime offsets `0x12cf8/0x12cfc`; ran a Frida Stalker attempt around `ANE_ProgramSendRequest`; checked local DTrace capability; generated `mps/ANE/.ane_runs/json/iokit_selector2_callsite_trace_attempt_20260623.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: call-site hook attached at runtime addresses such as `0x1a32cdcf8/0x1a32cdcfc` but recorded zero hits during the minimal eval; Stalker attached to the wrapper function address but produced no usable call summaries; `dtrace` exists but reports SIP is on and `DTrace requires additional privileges`; latest minimal raw profile still ran successfully with eval mean about `0.018014s` | Conclusion: short-term loop complete, verdict=`inconclusive_callsite_and_dtrace_selector2_timing_not_captured_current_session`; runtime IOKit boundary timing is not captured with available unprivileged/PAC-naive tooling | Next: continue static H16 selector-2 lower-path analysis around `updateRequestFWCommand`, prewire, scheduler insertion, and resource collection lifetimes to look for a memory-neutral reusable state/control field.
2026-06-24 00:11:24 +0800 | Goal: answer current slow-speed root cause and finish the bridge-profile attribution loop | Actions: used `ane-consumer-benchmark` and `diagnosing-bugs` methodology; compared prior under-30 q240/control artifacts against current q240/control reruns; generated `mps/ANE/.ane_runs/json/bridge_tmpdir_cache_regression_attribution_20260623.json` and CSV peer; updated `docs/ane_state.md` and rewrote fixed-format `docs/ane_next.md` | Evidence: prior q240/control wall `27.903367375023663s` / `28.173455959011335s`, transformer compile/load `1.944708043942228s` / `1.9895249569090083s`, transformer eval `19.743745001906063s` / `19.829284292005468s`; current q240/control wall `38.78787529101828s` / `39.23634491697885s`, transformer compile/load `9.555925211054273s` / `9.136685500969179s`, transformer eval `20.199491960869636s` / `20.17042325309012s`; current bridge tmpdir/materialization `6.331118126999998s` / `5.9165631659999995s`; current ANE `load_qos` only `1.5175505839999996s` / `1.3551657050000012s`; load-cache misses `0`; current reruns used `--baseline none` | Conclusion: short-term loop complete, verdict=`confirmed_bridge_tmpdir_materialization_regression_dominates_current_compile_load`; immediate 38-39s slowness is host bridge tmpdir/cache materialization regression, while best-case under-30 slowness remains transformer eval dominated by repeated time-axis `attention_pre` selector-2/materialization plus axis packing | Next: inspect/fix `ane_bridge.m` tmpdir/load-cache keep path with a memory-neutral skip or prove why it is unsafe, then rerun matched control on `test_clean.m4a`.
2026-06-24 00:35:24 +0800 | Goal: remove repeated bridge tmpdir/source materialization checks on load-cache-hit rows without increasing retained ANE handles or buffers | Actions: patched `mps/maderix_ANE/bridge/ane_bridge.m` so `ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT` attempts `loadWithQoS` before walking every weight file; rebuilt `mps/maderix_ANE/bridge/libane_bridge.dylib`; ran a native-supervisor full attempt, a one-second one-layer diagnostic, and a full non-supervised diagnostic; generated `mps/ANE/.ane_runs/json/bridge_fastload_before_source_verify_probe_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: native-supervisor full attempt killed at elapsed `0.0s` with child RSS `0.578MB`, free memory `2.866%`, compressor `6329MB`, reason `compressor_memory`; one-second one-layer diagnostic produced route `load_cache_skip_source_fast_load`, `6/6` transformer fast hits, `0` fallbacks, transformer bridge tmpdir `0.000278874s`; full non-supervised diagnostic produced `192/192` transformer fast hits, `0` fallbacks, transformer bridge tmpdir `0.02779358199999999s`, but host memory forced `chunk_batch_size=1`, wall `59.07401037501404s`, parent-watchdog max child RSS `980.6875MB`, swap growth `1046.25MB`; bridge source SHA256 `d1bb029f695c5d93ec8b0292be34f284eb739a3309311b56ac78dbbcd74cf71d`, dylib SHA256 `62e0a52748122bb0120ee49dbc12e5fb5d155c2885ef014214eb511090ec7cce` | Conclusion: short-term loop complete, verdict=`confirmed_fast_load_before_source_verify_removes_tmpdir_check_overhead_full_speed_inconclusive_due_host_memory_precondition`; the bridge tmpdir regression is fixed at code-path/profile-field level, but valid batch-4/native-supervisor speed and no-memory-increase acceptance are still unproven | Next: restore valid host benchmark preconditions, rerun matched batch-4 native-supervisor control on `test_clean.m4a`, then run correctness validation if wall returns under `30s`.
2026-06-24 00:44:37 +0800 | Goal: determine whether current host state permits a comparable patched batch-4 native-supervisor control rerun | Actions: checked `vm_stat`, `sysctl vm.swapusage`, benchmark native-supervisor defaults, process RSS leaders, `/usr/sbin/purge`, and benchmark-like `ane_mem_supervisor` `/bin/sleep` preflight; generated `mps/ANE/.ane_runs/json/batch4_native_supervisor_precondition_check_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: benchmark-like supervisor `/bin/sleep` exited normally with wired about `3041MB`, compressor about `3200MB`, swap used about `2181MB`; free memory was only about `4.8-4.9%`, far below the `55%` auto-batch threshold needed to reproduce prior batch-4 runs; stricter `--min-free-percent 5` preflight killed immediately on `free_percent`; `/usr/sbin/purge` returned `Operation not permitted`; top RSS users were mostly Chrome renderers, but no user applications were killed | Conclusion: short-term loop complete, verdict=`inconclusive_full_acceptance_batch4_precondition_failed_low_free_memory`; native supervisor can now launch, but full-path acceptance is still invalid because auto batching would select `chunk_batch_size=1` | Next: wait for or create valid host memory headroom, then run the patched matched-control benchmark only if native supervisor is enabled and `chunk_batch_size=4`; otherwise continue with narrow micro-probes that do not claim full-path acceptance.
2026-06-24 00:51:10 +0800 | Goal: attribute the patched full diagnostic wall time under low-memory batch-1 conditions without claiming full-path acceptance | Actions: parsed `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_skip_source_fastload_patch_nativesup_off_20260624.json`; compared it to prior batch-4 control and current unpatched batch-4 control; generated `mps/ANE/.ane_runs/json/low_memory_batch1_transformer_multiplication_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: patched low-memory run had `chunk_batch_size=1`, `transformer_timing_count=96`, time/freq segments `48/48`; prior batch-4 control had time/freq segments `12/12`, so segment count increased exactly `4x`; patched total time+freq bridge tmpdir was about `0.035476582s`, compared with `5.9165631659999995s` in current unpatched control; patched run remained non-comparable because native supervisor was off and host memory forced batch splitting | Conclusion: short-term loop complete, verdict=`confirmed_low_memory_batch1_multiplies_transformer_segments_bridge_tmpdir_not_remaining_wall_cause`; the patched `59s` diagnostic is explained by low-memory batch splitting multiplying transformer eval/load/axis-pack work, not by the bridge tmpdir path | Next: run only narrow per-segment time-axis `attention_pre` eval/materialization or `axis_pack` probes while full-audio batch-4 acceptance remains gated by host memory headroom.
2026-06-24 01:02:21 +0800 | Goal: compare default vs q240 time-axis `attention_pre` per-segment behavior under the patched fast-load bridge path | Actions: used `benchmark/private_ane_attention_pre_micro_profile.py` with `ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT=1`, load-cache, and keep-tmpdir; ran batch-4 default/q240 with repeats `5`/warmup `1`; ran representative batch-62 default/q240 with repeats `1`/warmup `0`; generated `mps/ANE/.ane_runs/json/attention_pre_q240_shape_policy_probe_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: batch-4 default eval `0.014133558387402444s`, total `0.014603433397132904s`; batch-4 q240 eval `0.018651716795284302s`, total `0.029217816609889268s`, so q240 is eval `+31.967592902216285%` and total `+100.07498110427656%`; batch-62 default eval `0.2590873750159517s`, total `0.287826124986168s`, TFLOPS `0.6330387950007289`; batch-62 q240 eval `0.23802358302054927s`, total `0.26003245799802244s`, TFLOPS `0.689059283952718`, so q240 is eval `-8.129995525295493%` and total `-9.656408704901695%` | Conclusion: short-term loop complete, verdict=`confirmed_q240_shape_dependent_large_attention_pre_win_small_segment_loss`; q240 should be treated as a large-shape-only policy candidate and not used on small low-memory segments; remaining gap to ANE peak is not bridge tmpdir or generic qchunk choice | Next: inspect q240 gating and either add a memory-neutral shape guard or move to lower selector-2 materialization/dispatch timing if policy is already manual-only.
2026-06-24 01:13:28 +0800 | Goal: add and verify a memory-neutral shape guard for q240 time-axis `attention_pre` | Actions: patched `pymss/modules/bs_roformer/private_ane.py` to add `_tiled_attention_pre_for_shape`; actual tiled MIL generation now requires q240 opt-in, time axis, layer `0`, `seq == TIME_PAD`, and `batch >= FREQ_SEQ` unless `PYMSS_PRIVATE_ANE_FORCE_TILED_TIME_ATTENTION_PRE_SMALL_SHAPES=1`; updated profiled timing metadata to use the same shape-aware decision; ran `py_compile`, direct shape assertions, and diagnostic override assertion; generated `mps/ANE/.ane_runs/json/attention_pre_q240_shape_guard_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: static layer-0 opt-in remains true; batch-4 shape decision false and MIL generation returns none; batch-62 shape decision true and tiled MIL is generated; freq-axis false; layer-1 false; diagnostic override makes batch-4 true; source SHA256 `7d79be53fe8bd6f70b4e06b67befc8d0ff51dd773fb13fd46f3d5526e4047411` | Conclusion: short-term loop complete, verdict=`confirmed_memory_neutral_q240_shape_guard_added_and_verified`; the measured small-shape q240 loss is now guarded while preserving the representative large-shape q240 path, without increasing memory | Next: move to lower selector-2 materialization/dispatch attribution or run guarded full-path batch-4 acceptance if host memory recovers.
2026-06-24 01:23:54 +0800 | Goal: attribute the selector-2 `updateRequestFWCommand` DVA/firmware-command update path and decide whether it exposes a memory-neutral reuse lever | Actions: used `reverse-engineering`, `ida-reverse`, `diagnosing-bugs`, and `ane-consumer-benchmark` workflow constraints; reopened H16 IDA session as `apple_h16_ane_interface_20260624`; queried `updateRequestFWCommand`, `SendRequestToFirmware_gated`, `ANE_ProgramPrepareAndSubmitRequest_gated`, prewire, and request-create xrefs; generated `mps/ANE/.ane_runs/json/selector2_update_fw_command_dva_attribution_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: `updateRequestFWCommand` at `0xfffffe00092929a0` has only one code xref, `SendRequestToFirmware_gated+0x158c` at `0xfffffe00092914b4`; caller passes current `ANERequest` (`MOV X1, X19`) and aborts send on failure (`CBZ W0`); update function reads request-owned fields from `[X1,#0x28]` and `[X1,#0x1890]`, writes into command area, requires mutable memory to be DART-mapped, and logs `updated proc mutable dva address from 0x%llx to 0x%llx`; downstream path still includes shared-event doorbell and `aneCmdSend` | Conclusion: short-term loop complete, verdict=`confirmed_update_fw_command_is_per_request_dva_rewrite_no_standalone_memory_neutral_bypass_found`; this is a real lower selector-2 materialization/root-cause class but no safe standalone memory-neutral bypass was found | Next: recover the request flag / unchanged-DVA gate feeding `SendRequestToFirmware_gated+0x1580` (`[X8,#0x17]`) and decide whether time-axis `attention_pre` always forces rewrite or can avoid it through memory-neutral request-count/axis-pack/coalescing.
2026-06-24 01:32:15 +0800 | Goal: recover the request flag / unchanged-DVA gate before `updateRequestFWCommand` and determine whether time-axis `attention_pre` can avoid repeated DVA/firmware-command rewriting without increasing memory | Actions: used IDA MCP session `apple_h16_ane_interface_20260624`; traced `SendRequestToFirmware_gated` stack slot `var_170`; searched request offset `0x3150` and `0x3139`; analyzed `ProcessReMap`, `ANEUnionResource::markPendingRequestsToBeUpdated`, `buildFirmwareRequest`, and `ANERequest::resetCacheHandle`; generated `mps/ANE/.ane_runs/json/selector2_update_fw_command_gate_source_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: `var_170` is set to `ANERequest + 0x3139` at `0xfffffe0009290afc-0xfffffe0009290b08`; `0xfffffe00092914a4` loads `[var_170 + 0x17]`, so the gate is `ANERequest + 0x3150`; `ProcessReMap.cold.1` sets `request+0x3150` at `0xfffffe00093759a8` after checking `request+0x189c`; `ANEUnionResource::markPendingRequestsToBeUpdated.cold.2` sets the same byte at `0xfffffe0009376a78`; callers include memory descriptor update and DART unmap; current timing has no branch counter for `0xfffffe00092914a8` | Conclusion: short-term loop complete, verdict=`inconclusive_rewrite_gate_source_resolved_attention_pre_force_not_proven`; the gate is a lower remap/resource-DVA dirty bit, but static IDA alone does not prove whether time-axis `attention_pre` always takes the update branch | Next: try safe runtime branch-frequency observation for `0xfffffe00092914a8`; if unavailable, stop field guessing and move to memory-neutral request-count/axis-pack reduction.
2026-06-24 01:39:42 +0800 | Goal: determine whether current safe local tooling can count the `updateRequestFWCommand` gate branch frequency for time-axis `attention_pre` without increasing retained memory or using unsafe kernel/protected-daemon patching | Actions: reviewed prior runtime trace artifacts (`aneservices_selector2_frida_timing_feasibility_20260623`, `iokit_selector2_callsite_trace_attempt_20260623`, `iokit_selector2_hook_boundary_probe_20260623`, `bridge_eval_selector2_timing_boundary_20260623`, client-side Frida capability), inspected local bridge/micro-profile/interpose surfaces, generated `mps/ANE/.ane_runs/json/selector2_update_gate_runtime_observation_feasibility_20260624.json` and CSV peer, updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: bridge/micro-profile expose only outer eval/read/write; ANEServices Frida timed outer selector-2 wrapper calls but cannot read H16 `ANERequest+0x3150`; IOConnect callsite/Stalker did not capture lower timing; PAC-signed ANEServices import slots caused Frida attach failures; C IOKit interposer observes selector traffic, not the kernel/H16 branch; DTrace/system tracing unavailable in this session | Conclusion: short-term loop complete, verdict=`inconclusive_observation_unavailable_current_safe_tooling`; current safe tooling cannot count branch frequency at `0xfffffe00092914a8`; this is a current-machine/tooling verdict, not a global impossibility proof | Next: stop same-field guessing and perform a memory-neutral request-count/axis-pack reduction audit for time-axis `attention_pre`.
2026-06-24 01:53:03 +0800 | Goal: complete the memory-neutral request-count and axis-pack reduction audit for time-axis `attention_pre` | Actions: used `diagnosing-bugs` and `ane-consumer-benchmark` workflow constraints; parsed `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_load_cache_bridgeprofile_20260623_profile/transformer_timings.csv`; inspected the layerwise transformer/axis-pack code anchors in `pymss/modules/bs_roformer/private_ane.py`; reviewed closed route artifacts for q240, `bridge_pack_gate`, direct time-to-freq repack, surface/unpadded handoff, batch-axis promotion, and selector-2 update gate observation; generated `mps/ANE/.ane_runs/json/time_attention_pre_request_axis_pack_audit_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: profile has `24/24` load-cache-hit transformer rows; time-axis has 12 rows, estimated 48 `attention_pre` selector-2 requests, `attention_pre_eval_sec=9.538814419182017`, `axis_pack_sec=2.5199859970016405`, `eval_sec=14.225222417007899`; freq-axis has estimated 48 `attention_pre` requests, `attention_pre_eval_sec=3.0500712058274075`, `axis_pack_sec=0.8207393719640095`; closed candidates either do not reduce request/pack cost, increase RSS, regress wall/eval, are unsupported, or cannot be safely observed/bypassed | Conclusion: short-term loop complete, verdict=`falsified_no_memory_neutral_candidate`; current host-visible graph/layout knobs are exhausted for reducing time-axis `attention_pre` request count or axis-pack under the no-memory-growth constraint | Next: investigate fused time+freq MIL/layout compile feasibility for one layer/chunk; if rejected, produce an `InvalidMILProgram` blocker package for the current layout/control boundary.
2026-06-24 02:03:07 +0800 | Goal: probe whether a fused time/freq ANE-side layout primitive is compile-feasible without promoting runtime changes | Actions: used the existing `ANEBridge` compile surface from `benchmark/private_ane_real_attention_probe.py`; compiled three minimal MIL candidates: pure transpose `[62,256,1,960] -> [960,256,1,62]`, transpose+crop `[62,256,1,960] -> [938,256,1,62]`, and transpose+crop+zero-pad concat `[62,256,1,960] -> [938,256,1,64]`; generated `mps/ANE/.ane_runs/json/fused_time_freq_layout_compile_probe_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: pure transpose compiled in `0.152650167s`; transpose+crop compiled in `0.105786125s`; zero-pad concat variant failed in `0.076668375s` with ANECompiler `InvalidMILProgram`; no runtime inference path was changed and no retained handle/cache route was introduced | Conclusion: short-term loop complete, verdict=`confirmed_partial_layout_primitive_compile_padded_contract_blocked`; the fused layout route is not dead because ANE-side transpose/crop compiles, but the current padded freq contract cannot be reached through the tested const+concat formulation | Next: test an unpadded freq-axis attention/block contract consuming `[938,256,1,62]`, or try one alternate pad-to-64 formulation if unpadded freq compile fails.
2026-06-24 02:06:00 +0800 | Goal: correct recovery target after discovering prior unpadded freq/full-path evidence | Actions: cross-checked `fused_time_freq_compile_feasibility_summary_20260623.json`, `unpadded_freq_runtime_probe_20260623.json`, `freq_unpadded_surface_bytes_variant_probe_20260623.json`, `full_path_unpadded_freq_padded_surface_validation_20260623.json`, and `unpadded_freq_route_repeated_fullpath_policy_20260623.json`; corrected `docs/ane_next.md`, `docs/ane_state.md`, and `fused_time_freq_layout_compile_probe_20260624.json` so recovery does not repeat the unpadded/direct repack branch | Evidence: older evidence already shows unpadded freq `seq=62` compiles, unpadded eval needs padded input/output surfaces, transformer-only padded-surface route was exact/slightly faster, but full-path `test_clean.m4a` was slower and max child RSS rose; route verdicts include `falsified_full_path_unpadded_freq_padded_surface_not_promotable` and `abandon_unpadded_freq_padded_surface_route_for_promotion` | Conclusion: short-term correction complete; next work should move below the host-visible layout/runtime surface toward selector-3/selector-8 create-instance materializer state or produce a current-layer blocker package, not rerun unpadded freq/direct repack/qchunk/selector-2 gate probes | Next: recover matching arm64e/H16 selector-3/8 materializer evidence and test exactly one lower candidate, or package the current layer as exhausted.
2026-06-24 02:25:31 +0800 | Goal: complete selector-3/8 create-instance materializer audit and decide whether current lower materializer state exposes a memory-neutral acceleration lever | Actions: used `reverse-engineering`, `ida-reverse`, `ane-consumer-benchmark`, and `diagnosing-bugs` constraints; queried IDA session `apple_h16_ane_interface_20260624`; analyzed `ANEHWDevice::ANE_ProgramCreateInstance_gated`, `ANEProgramResource::needProgramRemap(uint)`, `ANEProgramResource::ProgramReMap`, `ANEResource::create<(ANEResourceType)2>`, and `ANEHWDevice::createANESurface`; generated `mps/ANE/.ane_runs/json/selector3_8_create_instance_materializer_audit_20260624.json` and CSV peer; updated `docs/ane_state.md` and rewrote `docs/ane_next.md` | Evidence: selector-8 calls `needProgramRemap` at `0xfffffe000928cf48`; true path logs `Program not mapped in DART, remapping` at `0xfffffe000928cff4` and calls `ProgramReMap` at `0xfffffe000928d048`; `needProgramRemap` checks missing per-residency mapping slots across program/resource arrays; `ProgramReMap` waits/sets pending update, wires resources, calls `dartMapResources` when needed, recomputes DVA offsets, and clears pending update; `ANEResource::create<2>` rounds size to device alignment and calls `createANESurface`, whose xrefs/strings confirm IOSurface contract materialization | Conclusion: short-term loop complete, verdict=`inconclusive_current_layer_materializer_control_not_found`; current selector-8 remap/reload and IOSurface materializer paths are required correctness/materialization sinks, not confirmed memory-neutral speed levers | Next: move to `ExploitOrBlock` and package current host-visible layout/surface/materializer boundary as exhausted unless a genuinely lower target can be named with direct evidence.
2026-06-24 02:35:29 +0800 | Goal: package current host-visible layout/surface/materializer boundary as exhausted or name a stronger lower target | Actions: used reverse-engineering/docs/benchmark evidence packaging constraints; extracted current best wall from `test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_20260623.private_ane_child/meta.json`; extracted cached transformer root-cause split from `test_clean_full_private_native_supervised_batch4_load_cache_bridgeprofile_20260623_profile/transformer_timings.csv`; tied closed-route artifacts for load-cache, cache-hit materialization, bridge tmpdir regression, q240 shape guard, request-count/axis-pack audit, fused layout compile, unpadded/direct freq, selector-2 observation, and selector-3/8 materializer audit; generated `mps/ANE/.ane_runs/json/current_layer_exhausted_blocker_20260624.json` and CSV peer; updated `docs/ane_state.md` and rewrote `docs/ane_next.md` | Evidence: best full-path `test_clean.m4a` wall `27.903367375023663s`, RTF `0.7048080675165779`; current timing profile has `24/24` load-cache-hit transformer rows and `0` load-cache misses; time-axis rows contribute `14.225222417007899s` eval, `9.538814419182017s` `attention_pre` eval, and `2.5199859970016405s` axis-pack; all current-layer candidate families either solved a prior regression, fail compile/eval, regress wall/RSS, cannot be safely observed, or expose only mapping/materializer correctness paths | Conclusion: short-term loop complete, verdict=`falsified_current_layer_exhausted`; the specific dead-end layer is the current host-visible private ANE graph/layout/runtime layer plus H16 selector-2/3/8 driver materializer layer through `ProgramReMap` / `dartMapResources` / `createANESurface`; ANE firmware/internal scheduler below that layer is not proven exhausted | Next: enumerate candidate lower targets and produce `confirmed_next_lower_target` or `blocked_need_lower_target_access` without rerunning full benchmarks.
2026-06-24 02:46:04 +0800 | Goal: identify exactly one genuinely lower target below `ProgramReMap` / `dartMapResources` / `createANESurface` from local evidence | Actions: used reverse-engineering and IDA evidence constraints; reviewed prior artifacts `firmware_reply_vs_completion_priority_20260623`, `next_lower_target_priority_20260623`, `ane_firmware_command_send_static_boundary_20260623`, and `process203fc_state2_first_lower_surface_record1b8_verdict_20260619`; queried active IDA session `apple_h16_ane_interface_20260624`; looked up/decompiled `ANEHWDevice::isProcessValid` at `0xfffffe000927d410`; inspected `ANEHWDevice::handleRequestCompletion` at `0xfffffe000927c900`; confirmed `ANE_RestoreState` raw-send boundary around `0xfffffe00092c1d60`; generated `mps/ANE/.ane_runs/json/next_lower_target_selection_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: prior artifact selected lower reply-publish/completion side effects and concrete surface `device slot+0x9c0 -> 0x927d410`; active IDA resolves `0xfffffe000927d410` to `ANEHWDevice::isProcessValid`, which consumes `process+0x203fc == 2` for accepted validation in mode 1; `handleRequestCompletion` calls `isProcessValid` at `0xfffffe000927c978` and dispatches through device vtable `+0x9c0` at `0xfffffe000927c990`-`0xfffffe000927c9b0`; prior `record+0x1b8` evidence shows no visible CPU-side exact writer and restore raw send at `0xfffffe00092c1d60` followed by record-state use | Conclusion: short-term loop complete, verdict=`confirmed_next_lower_target`; selected target is lower reply-publish/completion accepted-state family, not a speedup yet | Next: statically probe this target for reads/writes of `record+0x1b8`, `process+0x203fc`, `process+0x20400`, `gate+0x220`, and `resource+0x402f0`, then decide `confirmed_lower_state_author_or_consumer`, `falsified_completion_family_bookkeeping_only`, or `blocked_need_firmware_reply_or_privileged_runtime_access`.
2026-06-24 02:55:42 +0800 | Goal: statically probe the selected lower reply-publish/completion accepted-state family for a concrete lower state author or consumer | Actions: used IDA session `apple_h16_ane_interface_20260624`; inspected `ANEHWDevice::isProcessValid` at `0xfffffe000927d410`, `ANEHWDevice::handleRequestCompletion` at `0xfffffe000927c900`, and `ANEHWDevice::ANE_RestoreState` around raw send `0xfffffe00092c1d60`; generated `mps/ANE/.ane_runs/json/lower_completion_state_author_consumer_probe_20260624.json` and CSV peer; updated `docs/ane_state.md` and rewrote `docs/ane_next.md` | Evidence: `isProcessValid` computes `process+0x203fc` via `ADD X8, X21, #0x20,LSL#12` and `ADD X25, X8, #0x3FC`, reads it at `0xfffffe000927d530`, and compares it with `2` at `0xfffffe000927d538`; `handleRequestCompletion` calls `isProcessValid` with `W4=1` at `0xfffffe000927c978` and dispatches through device vtable `+0x9c0` at `0xfffffe000927c990`-`0xfffffe000927c9b0`; `ANE_RestoreState` calls raw `aneCmdSend` at `0xfffffe00092c1d60`, reads `record+0x1b8` at `0xfffffe00092c1d78`, and stores it into `resource+0x402f0` at `0xfffffe00092c1d7c` | Conclusion: short-term loop complete, verdict=`confirmed_lower_state_author_or_consumer`; the selected family is not bookkeeping-only, but no direct completion-side writer for `process+0x203fc` and no visible CPU-side exact writer for `record+0x1b8` were found | Next: determine whether a visible H16 CPU-side bridge connects `record+0x1b8` / `resource+0x402f0` / `gate+0x220` to `process+0x203fc`, or whether the hidden accepted-state writer is below raw firmware send.
2026-06-24 03:13:02 +0800 | Goal: determine whether visible H16 CPU-side code bridges `record+0x1b8` / `resource+0x402f0` / `gate+0x220` into scalar `process+0x203fc` | Actions: used `reverse-engineering`, `ida-reverse`, `diagnosing-bugs`, and `docs-generator`; no `spawn_agent` tool was available, so degraded sub-agent usage to scoped shell plus `ida-pro-mcp`; queried H16 session `apple_h16_ane_interface_20260624`; classified all `#0x3FC` sites, scoped `process+0x20400`/`#0x404` references, and source fields `#0x1B8`, `#0x220`, `#0x2F0`; generated `mps/ANE/.ane_runs/json/visible_bridge_record_to_process_state_probe_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: `ProgramLoad` reads `record+0x1b8` at `0xfffffe000928198c` and stores it to `gate+0x220` at `0xfffffe0009281990`; `ANE_RestoreState` reads `record+0x1b8` at `0xfffffe00092c1d78` and stores it to `resource+0x402f0` at `0xfffffe00092c1d7c`; scalar `process+0x203fc` writers are init zeroing, `ANE_ProcessCreate_gated` clear at `0xfffffe000927f5d4`, `ANE_ProgramCreateInstance_gated` immediate `1` at `0xfffffe000928d908`, `ANE_RestoreState.cold.2` immediate `1` at `0xfffffe000937654c`, and `ProcessAbort` immediate `2` at `0xfffffe000927ea20`; selector-2 and RT `base+0x3fc` stores are indexed per-entry writes, not scalar accepted-state publication | Conclusion: short-term loop complete, verdict=`falsified_visible_bridge_hidden_writer_below_raw_send`; the visible value-`2` writer is abort-local and not sourced from restore/gate/resource state, so no normal visible bridge exists for memory-neutral single-process reuse | Next: produce a lower-boundary blocker/requirements package for firmware reply accepted-state observation below raw `aneCmdSend`, or formally return to higher-level `attention_pre`/request-count reduction if privileged observation is required.
2026-06-24 03:24:46 +0800 | Goal: package the lower-boundary evidence and requirements for observing firmware reply accepted-state below raw `aneCmdSend` | Actions: used IDA session `apple_h16_ane_interface_20260624`; inspected `ANEHWDevice::aneCmdSend` wrapper variants, `ANEFirmwareManager::sendInferenceCmd`, `ANEHWDevice::aneFirmwareCommandSend`, `processCommandResponse`, and `handleOutstandingCommand`; mapped key raw-send call sites in ProgramLoad, ProcessCreate, RestoreState, SendRequestToFirmware, selector-2 submit, and RT inference; generated `mps/ANE/.ane_runs/json/firmware_reply_accepted_state_observation_requirements_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: `aneCmdSend(void*,...)` packages command/output pointer and size then calls `aneFirmwareCommandSend` at `0xfffffe00092bd6f4`; `sendInferenceCmd` builds pending request/property buffers and calls raw send at `0xfffffe00092bdc1c`; `aneFirmwareCommandSend` sends through `IOProcessorChannelSendRetry` at `0xfffffe00092c8a18`; synchronous response handling reaches `handleOutstandingCommand` at `0xfffffe00092c8dbc`, while async `processCommandResponse` reaches it at `0xfffffe00092c3cb0`; required fields are command/output pointers, `record+0x1b8`, scalar `process+0x203fc`, command-state `+0x58/+0x68/+0x88`, and optional copyback execution | Conclusion: short-term loop complete, verdict=`confirmed_minimal_firmware_reply_observation_plan`; static evidence is sufficient to define the lower observation seam but not to synthesize accepted-state | Next: test whether a one-shot runtime observation around ProgramLoad or RestoreState raw send is feasible under local permissions without retaining extra ANE handles, buffers, IOSurfaces, or response snapshots; if not, declare `blocked_need_privileged_runtime_access` for this lower route and return to higher-level `attention_pre` / request-count reduction.
2026-06-24 03:40:21 +0800 | Goal: determine whether the minimal firmware reply accepted-state observation probe is feasible on this machine without persistent memory growth | Actions: used `reverse-engineering`, `ida-reverse`, `diagnosing-bugs`, and `docs-generator`; no `spawn_agent` tool was available, so degraded to scoped shell/IDA evidence; checked current docs and prior selector-2 observation artifact; tested `lldb`/`dtrace` availability, SIP/authenticated-root status, boot args, KDK and kernel-memory prerequisites, loaded ANE kexts, Frida/user-space hook artifacts, and unified logging; generated `mps/ANE/.ane_runs/json/firmware_reply_runtime_observation_feasibility_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: `dtrace` without sudo fails with `DTrace requires additional privileges`; `sudo dtrace` can run a trivial BEGIN probe but warns SIP is on; `sudo dtrace -l -n 'fbt:com.apple.driver.AppleH16ANEInterface::entry'` fails because SIP is on; SIP and authenticated root are enabled; `kern.development=0`, boot-args is empty, no KDK directory, no `/dev/kmem` or `/dev/mem`; `AppleH16ANEInterface` is loaded at `0xfffffe000743d780`; Frida can time user-space ANEServices wrappers but does not expose kernel `record+0x1b8`, scalar `process+0x203fc`, command-state `+0x58/+0x68/+0x88`, or `handleOutstandingCommand` internals | Conclusion: short-term loop complete, verdict=`blocked_need_privileged_runtime_access`; do not force accepted-state or continue lower route under current tooling | Next: select exactly one memory-neutral higher-level `attention_pre` / request-count reduction candidate from existing profiler artifacts and code, excluding retained handles/surfaces and previously falsified RSS/wall regressions.
2026-06-24 03:51:52 +0800 | Goal: reconcile slow-inference root causes with prior reverse-engineering and profiling evidence after the lower firmware reply route was blocked | Actions: used `diagnosing-bugs` and `ane-consumer-benchmark`; no `spawn_agent` tool is available in this session, so degraded sub-agent usage to scoped shell evidence; reread `docs/ane_next.md`, checked the latest state/log entries, parsed `transformer_timings.csv`, reviewed the completed `time_attention_pre_request_axis_pack_audit_20260624`, `fused_time_freq_layout_compile_probe_20260624`, and `firmware_reply_runtime_observation_feasibility_20260624` artifacts; generated `mps/ANE/.ane_runs/json/slow_inference_root_cause_solution_map_20260624.json` and CSV peer; rewrote `docs/ane_next.md` to the next transformer-only lifecycle attribution loop; updated `docs/ane_state.md` | Evidence: best accepted full run remains wall `27.903367375023663s`, RTF `0.7048080675165779`, transformer `24.631073875003494s`, transformer eval `19.743745001906063s`, transformer compile/load `1.944708043942228s`, max RSS `1282.671875MB`; bridge profile has `24/24` transformer rows as load-cache hits and `0` misses; time-axis `attention_pre_eval_sec=9.538814419182017`, time `axis_pack_sec=2.5199859970016405`, freq `attention_pre_eval_sec=3.0500712058274075`, freq `axis_pack_sec=0.8207393719640095`; current-layer graph/layout candidates and lower accepted-state observation are closed or blocked under the no-memory-growth and local privilege constraints | Conclusion: short-term loop complete, verdict=`blocked_no_memory_neutral_candidate`; slow inference is now dominated by cached segmented transformer request lifecycle and packing, not cold compile/load | Next: run transformer-only per-axis lifecycle attribution to select exactly one measurable bucket among ANE eval, write/read, host packing, handle free, GC, and outer-gap dispatch without full `test_clean.m4a` and without increasing memory.
2026-06-24 03:51:52 +0800 | Goal: select exactly one residual lifecycle bucket from existing transformer timing evidence without a full audio benchmark | Actions: parsed the existing cached batch-4 bridge profile `transformer_timings.csv`; generated `mps/ANE/.ane_runs/json/transformer_lifecycle_bucket_attribution_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: total attention_pre eval is `12.588885625009425s`; time-axis attention_pre eval is `9.538814419182017s`; total axis pack is `3.34072536896565s`; total read/write is `2.460594660748029s`; total GC/free is `1.804850714164786s`; total outer gap is `1.2444323258532677s` | Conclusion: short-term loop complete, verdict=`confirmed_next_lifecycle_bucket`; selected bucket is `time_axis_attention_pre_eval_request_lifecycle` | Next: probe one representative time-axis `attention_pre` layer to determine whether that bucket is dominated by ANE compute body, selector-2 request/materialization overhead, or host-side setup, without retained memory or full `test_clean.m4a`.
2026-06-24 04:05:00 +0800 | Goal: probe one representative time-axis `attention_pre` layer and classify compute body vs request/materialization vs host setup | Actions: tried standalone `attention_pre_tiled` and sub-stage micro-profiles with q240/load-cache; both failed ANE compile with `InvalidMILProgram`; ran integrated transformer layer-0 compare `benchmark/private_ane_transformer_layerwise_compare.py --compare tiled --layers 1 --chunks 4 --q-chunk 240`, producing `benchmark_results/private_ane/time_attention_pre_layer0_lifecycle_integrated_20260624.json`; cross-checked accepted hot-path layer-0 timing from best full-run meta; generated `mps/ANE/.ane_runs/json/time_attention_pre_layer0_lifecycle_probe_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: accepted hot-path time layer0 q240 has `ane_pre_eval_sec=0.7698414579790551`, `ane_pre_write_sec=0.01106487397919409`, `ane_pre_read_sec=0.026174624013947323`, `axis_pack_sec=0.05874783397302963`, `compile_wall_sec=0.037306624988559633`; integrated q240 compare was exact (`max_abs=0`) but cold-load contaminated, with `wall_delta_sec=2.3996788329677656` and `maxrss_delta_mb=227.25` | Conclusion: short-term loop complete, verdict=`inconclusive_need_lower_runtime_access`; host setup/write/read/pack are not dominant, but current user-space timing cannot split the opaque bridge eval call into ANE compute body versus selector-2 request/materialization/firmware wait | Next: inspect or instrument the private ANE bridge eval path for one time-axis `attention_pre` request to split request creation/materialization, ANEServices submit, firmware wait/completion, and readback completion without retained memory.
2026-06-24 04:20:00 +0800 | Goal: instrument or reverse-map the private ANE bridge eval path for one time-axis `attention_pre` request | Actions: delegated source inspection to explorer sub-agent `019ef61e-3c97-7ba3-984a-4eb2eddfe1ed` and IDA eval seam mapping to ida sub-agent `019ef61e-80f1-78e3-a651-2566708d109d`; inspected local bridge profile fields and exported C API; generated `mps/ANE/.ane_runs/json/bridge_eval_path_attribution_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: source confirms existing user-space profile already splits cast/alloc/write/eval/read and that `ane_bridge_eval` is a monolithic blocking call; native bridge compile/load profile has no eval subphase fields; IDA maps eval submit to `ANE_ProgramSendRequest` selector 2 / `IOConnectCallAsyncMethod` with async wake port/callback and user-space signposts ending after submit return | Conclusion: short-term loop complete, verdict=`confirmed_firmware_wait_or_compute_dominant`; request materialization and IOConnect submit are not dominant, and the main unknown is firmware wait/compute plus kernel completion dispatch | Next: compute accepted hot-path `attention_pre` FLOP/throughput estimates against the measured local NPU FP16 peak to decide whether the next target is MIL/body utilization or lower firmware timing.
2026-06-24 04:35:00 +0800 | Goal: compute accepted hot-path `attention_pre` FLOP/throughput and decide whether the firmware-wait/compute bucket is low-utilization compute-body work | Actions: used the repository `_stage_flops` formula from `benchmark/private_ane_attention_pre_micro_profile.py`; parsed accepted hot-path transformer rows from `test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_20260623.private_ane_child/meta.json`; generated `mps/ANE/.ane_runs/json/attention_pre_throughput_roofline_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: per-layer time-axis `attention_pre` FLOPs are `164012359680`; accepted time layer0 q240 `ane_pre_eval_sec=0.7698414579790551s` gives `0.21304693061160423 TFLOPS` / `1.1669967715359566%` of measured ANE FP16 peak; all 12 time-axis layers have `ane_pre_eval_sec=9.493088960007299s`, giving `0.20732433083177246 TFLOPS` / `1.1356503660811375%` | Conclusion: short-term loop complete, verdict=`confirmed_low_utilization_compute_body`; accepted time-axis `attention_pre` is far below measured ANE peak, so the next target is MIL/body/layout utilization, not load/compile or host setup | Next: compare accepted integrated time-axis `attention_pre` MIL/body against prior faster standalone q240 evidence and current integrated q240 layer0 rows, then name one memory-neutral body/layout candidate or prove lower firmware timing is required.
2026-06-24 04:50:00 +0800 | Goal: compare accepted integrated time-axis `attention_pre` q240 against prior faster standalone q240 evidence | Actions: delegated broad comparison to explorer sub-agent `019ef62c-8caf-79c3-a2f3-be1cbf509743`; extracted standalone q240 artifact rows, accepted full-run layer0 row, integrated cold compare row, and prior fast-load verdict; generated standalone and integrated q240 MIL for `batch=62, seq=960, valid_seq=938, q_chunk=240` and compared hashes; generated `mps/ANE/.ane_runs/json/integrated_vs_standalone_attention_pre_q240_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: standalone and integrated q240 MIL are identical (`sha256=cfeeba68a0867d458ffa754fc3777ecdce97c7ab6dd42abe81d759ad310d59c6`, 8 matmuls, 4 softmaxes, 8 slices); standalone b62 q240 hits `load_cache_skip_source_fast_load` and evals in `0.23802358302054927s`; accepted integrated layer0 uses `load_cache_skip_source_write`, `fast_load_hit=0`, and evals in `0.7698414579790551s`; prior `bridge_fastload_before_source_verify_probe_20260624` confirms the route but full speed was inconclusive due invalid memory/native-supervisor preconditions | Conclusion: short-term loop complete, verdict=`confirmed_memory_neutral_body_candidate`; the next concrete candidate is integrated transformer fast-load-hit route validation, not MIL text changes | Next: run a valid native-supervised batch-4 full-path `test_clean.m4a` probe with fast-load route active, or output a blocker if memory/preconditions are invalid.
2026-06-24 04:57:29 +0800 | Goal: run or block the valid native-supervised batch-4 integrated fast-load-hit acceptance probe on `test_clean.m4a` | Actions: 1) used `diagnosing-bugs`, `reverse-engineering`, and `ida-reverse` constraints; 2) delegated doc compression to `doc-reader` and command/flag discovery to `searcher`, then closed both agents; 3) checked live memory with `top`, `vm_stat`, `memory_pressure`, `sysctl vm.swapusage`, `ps`, and `df`; 4) did not launch the full benchmark because current memory preconditions were invalid; 5) wrote `mps/ANE/.ane_runs/json/integrated_fastload_acceptance_blocked_memory_20260624.json` and CSV peer; 6) updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: current `top` reported `15G used`, `3522M wired`, `4615M compressor`, only `140M unused`; `sysctl vm.swapusage` reported `2676.38M` swap used; `aned` RSS was `2736KB`; accepted baseline remains `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_20260623.private_ane_child/meta.json` with wall `27.903367375023663s`, transformer eval `19.743745001906063s`, transformer compile/load `1.944708043942228s`, and max RSS `1282.671875MB` | Conclusion: short-term loop complete, verdict=`blocked_invalid_memory_preconditions`; no wall time was accepted because a native-supervised batch-4 run under current pressure would risk failure, auto batch downgrade, or memory-contaminated timing | Next: obtain a clean native-supervised batch-4 memory preflight and rerun the exact integrated fast-load-hit acceptance command; if the same memory blocker repeats again, switch the next loop to an offline/static audit of why integrated transformer does not hit `load_cache_skip_source_fast_load`.
2026-06-24 05:14:24 +0800 | Goal: after repeated invalid memory preconditions, statically audit why the integrated transformer path did not hit `load_cache_skip_source_fast_load` | Actions: 1) rechecked memory and confirmed full native-supervised batch-4 preflight remained invalid; 2) delegated prior route evidence reading to `doc-reader` and route-code location to `searcher`, then closed both agents; 3) inspected Python flag propagation and native bridge route predicates; 4) generated `mps/ANE/.ane_runs/json/integrated_fastload_route_static_audit_20260624.json` and CSV peer; 5) updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: live memory remained invalid: `15G used`, `3520M wired`, `5465M compressor`, only `106M unused`, swap used `2628.38M`; Python sets `ANE_BRIDGE_LOAD_CACHE=1` and `ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT=1`; benchmark defaults keep load-cache/keep-tmpdir/skip-source enabled; Python only records `bridge_profile_route`; native bridge assigns `load_cache_skip_source_fast_load` only after early load-only success and falls to `load_cache_skip_source_write` when direct load-only does not load but source files are complete; prior evidence has standalone route `load_cache_skip_source_fast_load` with eval `0.23802358302054927s` and accepted integrated route `load_cache_skip_source_write` with eval `0.7698414579790551s` | Conclusion: short-term loop complete, verdict=`confirmed_native_load_only_predicate_is_integrated_fastload_gate`; the integrated miss is not a missing Python flag or MIL-body difference, but the native load-only predicate/fallback path | Next: create or run a small route-only integrated transformer load-cache diagnostic that records the native load-only error/fallback reason for one q240 `attention_pre` artifact without full audio and without retaining extra handles.
2026-06-24 05:22:52 +0800 | Goal: run a small route-only integrated transformer q240 `attention_pre` load-cache diagnostic without full audio | Actions: 1) delegated harness discovery to `searcher`, then closed it; 2) ran `/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --compare bridge-env --layers 1 --chunks 4 --q-chunk 240 --cache-tmpdir benchmark_results/private_ane/ane_tmp_loadcache --probe-handle-scope pre --probe-stop-after-axis time --probe-stop-after-layer 1 --bridge-env ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT=1 --bridge-env PYMSS_PRIVATE_ANE_TILED_TIME_ATTENTION_PRE=1 --bridge-env PYMSS_PRIVATE_ANE_TILED_TIME_ATTENTION_PRE_Q_CHUNK=240 --out benchmark_results/private_ane/integrated_attention_pre_route_only_q240_20260624.json`; 3) after failure, inspected the matching cache directory; 4) generated `mps/ANE/.ane_runs/json/integrated_attention_pre_route_only_q240_compile_blocker_20260624.json` and CSV peer; 5) updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: command exited `1`, no output JSON was written, candidate q240 `attention_pre` compile failed with `InvalidMILProgram` for identifier `CFEEBA68A0867D458FFA754FC3777ECDCE97C7AB6DD42ABE81D759AD310D59C6_F88156576125F4F2458BEBCC36F5BEFAB235C4F43F46BA3EAEA629FAD5C6051D_E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`; matching cache directory exists but contains only `model.mil` and weights, no `model.hwx` or compiled loadable artifact; cache root is `1.0G` with `452` directories; post-failure memory was `13G used`, `3212M wired`, `4040M compressor`, `2668M unused`, swap used `3340.94M` | Conclusion: short-term loop complete, verdict=`blocked_route_only_compile_invalid_mil_no_loadable_cache_artifact`; the existing route-only harness cannot force a true fast-load hit for this q240 artifact because the cache entry is source-only and compile fails before route profile fields are emitted | Next: recover a valid load-only route diagnostic by either priming a compiled/loadable q240 artifact from a known-good standalone fast-load run into the integrated cache identifier, or adding a plan-only cache inspector that checks loadable-artifact presence before invoking ANE compile.
2026-06-24 05:29:15 +0800 | Goal: add and run a plan-only cache inspector for the failing integrated q240 identifier | Actions: 1) added `benchmark/private_ane_cache_artifact_inspector.py`; 2) ran `python3 -m py_compile benchmark/private_ane_cache_artifact_inspector.py`; 3) inspected cache root `benchmark_results/private_ane/ane_tmp_loadcache` for identifier `CFEEBA68A0867D458FFA754FC3777ECDCE97C7AB6DD42ABE81D759AD310D59C6_F88156576125F4F2458BEBCC36F5BEFAB235C4F43F46BA3EAEA629FAD5C6051D_E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`; 4) generated `mps/ANE/.ane_runs/json/integrated_q240_cache_artifact_inspection_20260624.json` and CSV peer; 5) updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: inspector output status=`source_only`, `source_present=true`, `loadable_present=false`, `weight_file_count=7`; `model.mil` exists, while `model.hwx` and `model.hwx.tmp.additional_weights.bin` are missing | Conclusion: short-term loop complete, verdict=`confirmed_loadable_artifact_missing`; a true fast-load route diagnostic for this q240 identifier needs a compiled/loadable artifact first, otherwise the bridge must compile and hits `InvalidMILProgram` | Next: search for a known-good standalone fast-load run that produced a compatible compiled `model.hwx` for the same q240 identifier; if none exists, formally block artifact priming and move to lower native compile/load artifact materialization.
2026-06-24 05:36:04 +0800 | Goal: search for a known-good standalone fast-load run that produced a compatible compiled `model.hwx` for the exact integrated q240 identifier | Actions: 1) delegated broad artifact search to `searcher`, then closed it; 2) searched `benchmark_results/private_ane` and `mps/ANE/.ane_runs` for exact identifier directories and `.hwx` files; 3) compared same-weight alias compiled artifacts; 4) generated `mps/ANE/.ane_runs/json/q240_same_identifier_compiled_artifact_search_20260624.json` and CSV peer; 5) updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: exact identifier `CFEEBA68..._F8815657..._E3B0C442...` has `32` directories and `0` compiled/loadable artifacts; same-weight alias MIL hash `B018EBD3...` has `model.hwx` paths, including `benchmark_results/private_ane/ane_tmp_loadcache/B018EBD3B31C9EBE76E817901553F402986074B0F1C1B4173831047B8BB9AE91_F88156576125F4F2458BEBCC36F5BEFAB235C4F43F46BA3EAEA629FAD5C6051D_E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855/model.hwx`, but the MIL hash differs | Conclusion: short-term loop complete, verdict=`blocked_no_known_good_compiled_artifact`; alias `model.hwx` cannot be treated as compatible for target `CFEEBA68...` because it is a different MIL graph | Next: move to lower native compile/load artifact materialization and determine whether a wrapper/client-file path can produce `model.hwx` for the exact q240 identifier without changing the graph or increasing runtime memory.
2026-06-24 05:54:13 +0800 | Goal: determine whether wrapper/client-file materialization can produce `model.hwx` for the exact integrated q240 identifier without graph changes or increased runtime memory | Actions: 1) used `reverse-engineering` and `ida-reverse` methodology; 2) delegated local artifact/doc inspection to `doc-reader` and bridge control-flow inspection to `explorer`, then closed both agents; 3) performed static bridge/source and filesystem spot checks; 4) generated `mps/ANE/.ane_runs/json/q240_wrapper_materialization_static_verdict_20260624.json` and CSV peer; 5) updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: exact q240 identifier `CFEEBA68..._F8815657..._E3B0C442...` has `32` checked source/cache dirs and `0` compiled artifacts; same-weight aliases have `5` `model.hwx` examples but all under different MIL hashes; `ane_bridge.m` wrapper path writes source-root files but `model.hwx`/`model.src`/`model.retain` are outputs of the native compiler-service `compileModelAt` path and wrapper fast path only reuses existing files | Conclusion: short-term loop complete, verdict=`blocked_materialization_requires_successful_compile`; wrapper/client-file materialization is not an independent memory-neutral cache-priming bypass for exact q240 and requires successful native compiler/materializer output | Next: recover native compiler/materializer preconditions or failure point for exact q240 `model.hwx` generation, starting from `compileModelAt`, `loadModel`, `compileModel`, `loadWithQoS`, and existing `InvalidMILProgram` evidence; do not copy alias artifacts, change MIL identity, run full audio, or retain extra runtime memory.
2026-06-24 06:09:34 +0800 | Goal: recover native compiler/materializer preconditions or failure point for exact q240 `model.hwx` generation without graph changes, alias copies, full-audio reruns, or increased retained memory | Actions: 1) used `reverse-engineering` and `ida-reverse` methodology; 2) checked active `docs/ane_next.md`; 3) delegated focused native selector fact-gathering to `ida` sub-agent; 4) direct `ida-pro-mcp` `idb_list` showed prior sessions but `server_health` returned session-not-found and fresh `idb_open` failed for existing AppleNeuralEngine/ANECompiler paths; 5) closed the still-running `ida` sub-agent after two waits; 6) mined existing JSON/log artifacts, bridge source selectors/options, and local Mach-O `strings`/`nm`; 7) generated `mps/ANE/.ane_runs/json/exact_q240_native_materializer_precondition_probe_20260624.json` and CSV peer; 8) updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: exact q240 source-only cache still forces native compiler/materializer path; bridge line evidence shows `compileModelAt:...outputURL:aotModelBinaryPath:...` and compiler-output reads for `model.hwx`/`model.src`/`model.retain`; AppleNeuralEngine exports `_ANEClient compileModel/loadModel` and `_ANEInMemoryModel loadWithQoS`; existing q240 artifacts contain `InvalidMILProgram` failures but not the exact compiler-internal precondition or unsupported MIL op | Conclusion: short-term loop complete, verdict=`inconclusive_need_ida_or_runtime_instrumentation`; static evidence reaches only the bridge boundary and does not justify declaring exact q240 a compiler dead end | Next: restore IDA MCP enough to decompile/xref ANECompiler materializer and `InvalidMILProgram` construction, or add/run a minimal runtime error trace around exact q240 materialization to capture selector, options, paths, and full `NSError` domain/code/userInfo; do not run full audio, copy alias artifacts, change MIL identity, or retain extra runtime memory.
2026-06-24 06:30:29 +0800 | Goal: restore lower-layer visibility for exact q240 materializer failure via IDA recovery and/or minimal runtime compiler-error instrumentation | Actions: 1) used `reverse-engineering` and `ida-reverse` methodology; 2) found IDA MCP had empty-session orphan workers, killed stale worker PIDs `96042`, `97076`, `97079`, and reopened AppleNeuralEngine as `apple_neural_engine_recovered_20260624` plus ANECompiler as `ane_compiler_recovered_20260624`; 3) surveyed both IDBs; 4) decompiled `-[_ANEInMemoryModel loadWithQoS:options:error:]`, `-[_ANEClient compileModel:options:qos:error:]`, compile reply block, `doLoadModel`, and load reply block; 5) patched `mps/maderix_ANE/bridge/ane_bridge.m` to emit fixed-buffer `client_file_error_detail` in profile JSON and rebuilt `mps/maderix_ANE/bridge/libane_bridge.dylib`; 6) ran minimal q240 bridge-env transformer-layerwise probe twice, second time capturing log to `benchmark_results/private_ane/exact_q240_runtime_error_detail_probe_20260624.log`; 7) generated `mps/ANE/.ane_runs/json/exact_q240_runtime_error_payload_probe_20260624.json` and CSV peer; 8) updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: IDA shows `_ANEInMemoryModel loadWithQoS` saves files and calls `_ANEClient loadModel` with compiler options; `_ANEClient compileModel` and load paths preserve `NSError` in reply blocks; ANECompiler contains `InvalidMILProgram`; minimal q240 probe failed with `Error Domain=com.apple.appleneuralengine.compiler Code=1`, top `_ANECompiler : ANECCompile() FAILED`, underlying `ANECCompile(...CFEEBA68...F8815657...E3B0C442...) FAILED: err=(InvalidMILProgram)` | Conclusion: short-term loop complete, verdict=`confirmed_runtime_error_payload_precondition`; exact q240 failure is localized to `ANECCompile` on the exact generated source directory, not cache lookup or wrapper synthesis | Next: parse exact q240 `model.mil` and map its operations/shapes to ANECompiler validation surfaces, focusing matmul/softmax/slice/gather/SDPA/reshape/transpose/dynamic-shape restrictions, to identify the invalid op/shape or prove this MIL body is a compiler dead end; do not copy aliases, change graph identity, run full audio, or increase retained memory.
2026-06-24 07:05:00 +0800 | Goal: correlate exact q240 `model.mil` operations and shapes with ANECompiler validation surfaces | Actions: used `reverse-engineering` and `ida-reverse` methodology; delegated current-doc compression to doc-reader and focused reverse/IDA fact gathering to sub-agents; parsed `mps/ANE/.ane_runs/json/exact_q240_mil_parse_working_20260624.json`; mined local ANECompiler `strings`/`nm`; incorporated IDA decompilation of concat/slice/matmul/softmax/SDPA validation surfaces; generated `mps/ANE/.ane_runs/json/exact_q240_mil_validator_correlation_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: exact q240 has `106` ops vs compiled alias `68`; delta is `slice_by_index +4`, `matmul +6`, `softmax +3`, `concat +1`, `add +3`, `mul +3`, `const +18`; exact q240 forms four `[62,8,240,*]` attention tiles and final `concat(interleave=..., axis=2)` to `[62,8,960,64]`, while alias uses one full `[62,8,960,960]` attention path without concat; runtime error remains `ANECCompile(...CFEEBA68...F8815657...E3B0C442...) FAILED: err=(InvalidMILProgram)`; IDA reports concat/slice/matmul validators do not prove q240-specific blocking, softmax has an architecture gate but alias softmax compiles, and `ValidateUnits`/`ValidateDerivedMILProgram` are the likely next choke points | Conclusion: short-term loop complete, verdict=`inconclusive_need_validateunits_or_compiler_trace`; q240 tiled attention is the narrowed failure region, but current evidence does not prove the exact failing validator or justify declaring a dead end | Next: decompile/trace `ValidateUnits` (`0x2240a3258`), `ValidateDerivedMILProgram` (`0x2240a29c8`), and softmax validation context, or add minimal compiler-validation instrumentation to record the first rejected q240 MIL op/check; do not run full audio, copy alias artifacts, mutate MIL identity, or increase retained memory.
2026-06-24 07:25:00 +0800 | Goal: inspect `ValidateUnits` / `ValidateDerivedMILProgram` / softmax validation context for exact q240 `InvalidMILProgram` | Actions: used `reverse-engineering` and `ida-reverse` methodology; spawned a focused IDA sub-agent but closed it after it remained blocked; direct IDA MCP showed an unusable empty-session ANECompiler worker (`pid 17993`), force-killed it after normal kill failed, and named reopen attempts returned `Remote end closed connection without response`; degraded to local `nm` / `strings` / `objdump`; generated `mps/ANE/.ane_runs/json/exact_q240_validateunits_static_probe_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: local symbols confirm `ValidateOpList=0x22409c8bc`, `ValidateDerivedMILProgram=0x2240a29c8`, `ValidateUnits=0x2240a3258`, `MarkAllOpsAsInvalid=0x2240a6b54/0x2240a28a4`; `ZinIrSoftmaxUnit::ValidateForDynamicShapes` returns success (`mov w0,#0; ret`); softmax semantic validation gates on HAL byte `[x2+0x815]`, but alias contains one compiled softmax; `ValidateDerivedMILProgram` calls live-IO memory validation and can call `MarkAllOpsAsInvalid`; `MarkAllOpsAsInvalid` iterates MIL ops, retrieves op identifiers, and inserts invalid `ValidateEntry` records with a supplied reason | Conclusion: short-term loop complete, verdict=`inconclusive_need_first_invalid_op_trace`; the next missing evidence is the exact `ValidateEntry` invalid reason map, not more per-layer validator speculation | Next: instrument or decompile around `ValidateUnits` / `MarkAllOpsAsInvalid` / `RetrieveOpIdentifier` to capture first rejected op id/name/reason for exact q240 and map it back to `model.mil`; do not run full audio, copy alias artifacts, mutate MIL identity, or increase retained memory.
2026-06-24 07:45:00 +0800 | Goal: capture deeper exact q240 compile-error details through bridge/runtime error payload before attempting lower instrumentation | Actions: used `reverse-engineering`, `ida-reverse`, and `diagnosing-bugs` methodology; delegated probe-path discovery to searcher and closed it; patched `mps/maderix_ANE/bridge/ane_bridge.m` to recursively capture fixed-buffer `NSError` details and direct compile failure details; patched `benchmark/private_ane_real_attention_probe.py` to include `last_bridge_profile` JSON in compile failure exceptions; rebuilt `mps/maderix_ANE/bridge/libane_bridge.dylib`; killed a hung older route-only probe; reran the minimal one-layer/one-chunk q240 time `attention_pre` compile seam; generated `mps/ANE/.ane_runs/json/exact_q240_deep_error_detail_probe_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: minimal command exited `1` quickly; bridge profile route=`compile`, identifier=`CFEEBA68..._F8815657..._E3B0C442...`, `compile_qos_sec≈0.0079s`, `total_sec≈0.0090s`; recursive `client_file_error_detail` shows top-level `NSError` keys `[NSLocalizedDescription, NSUnderlyingError]` and underlying keys `[NSLocalizedDescription]`; no `ValidateEntry`, validation error array, op identifier, rejected op name, or reason map is exposed through `NSError` | Conclusion: short-term loop complete, verdict=`confirmed_nserror_payload_lacks_validateentry_reason`; the public runtime error boundary is exhausted for exact invalid-op attribution | Next: instrument below `NSError`, around `MarkAllOpsAsInvalid` / `ValidateUnits` / `RetrieveOpIdentifier`, or build a compile-service probe that can dump the `ValidateEntry` map before it collapses to `InvalidMILProgram`; do not run full audio, copy alias artifacts, mutate MIL identity, retain runtime memory, or repeat `NSError.userInfo` expansion.
2026-06-24 09:03:55 +0800 | Goal: determine whether exact B44E `band_split_l2_fused_0_4` can be safely regenerated/refreshed so `loadWithQoS` succeeds again | Actions: used `diagnosing-bugs` methodology; delegated current-doc compression to `doc-reader` and code/harness location to `searcher`, then closed both agents; added `benchmark/private_ane_band_split_b44e_refresh_probe.py`; ran the B44E-only probe using existing exact MIL/weights/output sizes without full audio; generated `mps/ANE/.ane_runs/json/band_split_b44e_refresh_probe_20260624.json` and CSV peer; restored the probe-removed B44E main cache only from same-identifier wrapperwork/repro artifacts; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: CSV records `load_ok=False`, `compile_ok=False`, `load_route=load_cache_skip_source_write`, `compile_route=compile`, `load_qos_sec=0.029365583`, `compile_qos_sec=0.00861125`; JSON records `retained_handles=0`, `retained_extra_buffers=0`; bridge error remains `_ANECompiler : ANECCompile() FAILED` with underlying `InvalidMILProgram`; post-run same-identifier `model.hwx` is present with SHA-256 `42394392BF4FC24A81C4CA0B27DA2882E2D7059728402EFC8749D712E4088C23` | Conclusion: short-term loop complete, verdict=`blocked_b44e_load_qos_rejects_and_refresh_compile_invalid`; B44E same-identifier refresh/materialization is not a safe current-layer solution under existing controls | Next: inventory compiler-accepted, memory-neutral transformer / `attention_pre` body or route-policy alternatives from existing cache/results; do not repeat B44E refresh, do not copy alias `model.hwx`, do not retain extra memory, and do not run full audio before a minimal candidate compiles and validates.
2026-06-24 09:19:42 +0800 | Goal: inventory compiler-accepted, memory-neutral `attention_pre` / transformer body alternatives after B44E closure | Actions: used `diagnosing-bugs` methodology; delegated active-loop doc compression to `doc-reader` and artifact/script discovery to `searcher`, then closed both agents; added read-only `benchmark/private_ane_attention_pre_candidate_inventory.py`; generated `mps/ANE/.ane_runs/json/attention_pre_compiler_accepted_inventory_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: JSON validation passed with `verdict=blocked_no_memory_neutral_compiling_candidate`, `candidate_count=7`, `promotable_candidate_count=0`, exact q240 cache dirs `1`, alias full-attention cache dirs `12`, B44E dirs `6`; CSV confirms only `accepted_integrated_exact_q240_load_cache_skip_source_write` is operable and it is kept only as baseline, not a new fix; exact q240 fast-load remains blocked, alias artifacts remain MIL-hash incompatible, qchunk/layout/public-SDPA/B44E classes remain closed | Conclusion: short-term loop complete, verdict=`blocked_no_memory_neutral_compiling_candidate`; compiler-accepted body substitution is exhausted under current no-extra-memory constraints | Next: move to memory-neutral route-policy/request-lifecycle analysis using existing transformer timing rows; determine whether axis gating, q240 shape guard tightening, skip-source/write policy, or request batching/coalescing can reduce selector/request count or axis-pack overhead without changing MIL identity or retaining extra memory.
2026-06-24 09:30:53 +0800 | Goal: determine whether memory-neutral route-policy/request-lifecycle changes can reduce selector/request count or axis-pack overhead without changing MIL identity | Actions: used `diagnosing-bugs` methodology; delegated current-loop docs to `doc-reader` and timing/code field discovery to `searcher`, then closed both agents; added read-only `benchmark/private_ane_route_policy_lifecycle_analysis.py`; consumed `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_load_cache_bridgeprofile_20260623_profile/transformer_timings.csv`; generated `mps/ANE/.ane_runs/json/route_policy_lifecycle_analysis_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: JSON validation passed with `verdict=falsified_no_memory_neutral_route_policy_candidate`; profile has 24 rows, 24 load-cache hit rows, 0 load-cache misses, estimated 96 total `attention_pre` selector requests; time axis has estimated 48 requests, `attention_pre_eval_sec=9.538814419182017`, `axis_pack_sec=2.5199859970016405`, `ane_write_sec=0.5406000427610707`, `ane_read_sec=0.7503471150121186`; candidates axis gating/batch-axis promotion, q240 shape guard as speed fix, skip-source/write policy, request coalescing without MIL changes, and host-visible repack policy are closed or require lower/MIL contract changes | Conclusion: short-term loop complete, verdict=`falsified_no_memory_neutral_route_policy_candidate`; no current host-visible memory-neutral route-policy lever remains | Next: investigate fused time+freq MIL/layout feasibility for one minimal layer/chunk under the no-memory-growth constraint; if ANECompiler rejects it, package the `InvalidMILProgram` evidence and declare the current host-visible layout/control boundary.
2026-06-24 09:47:52 +0800 | Goal: investigate fused time+freq MIL/layout feasibility for one minimal layer/chunk under the no-memory-growth constraint | Actions: used `diagnosing-bugs` methodology; delegated current-loop docs to `doc-reader` and fused/layout artifact discovery to `searcher`, then closed both agents; reused `mps/ANE/.ane_runs/json/fused_time_freq_layout_compile_probe_20260624.json`; added read-only `benchmark/private_ane_fused_layout_feasibility_package.py`; generated `mps/ANE/.ane_runs/json/fused_time_freq_layout_feasibility_package_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: package validation passed with `verdict=falsified_fused_layout_compile_invalid`; source probe compiled `time_to_freq_transpose_compile_only` and `time_to_freq_crop_compile_only`, but `time_to_freq_crop_pad_compile_only` failed with `InvalidMILProgram` while attempting concat zero-padding from `FREQ_SEQ=62` to `FREQ_PAD=64`; package loop was read-only and retained no runtime handles or buffers; correctness was not reached because the required padded contract failed before eval/load validation | Conclusion: short-term loop complete, verdict=`falsified_fused_layout_compile_invalid`; current host-visible fused time+freq MIL/layout contract is blocked at ANECompiler validation | Next: move below the current host-visible layout surface and inspect selector-3/selector-8 create-instance/materializer evidence, or produce a current-layer blocker package if no safe materializer control is exposed.
2026-06-24 08:05:00 +0800 | Goal: determine whether exact q240 `ValidateEntry` map capture is reachable without service-side debug privilege | Actions: used `reverse-engineering`, `ida-reverse`, and `diagnosing-bugs` methodology; delegated boundary feasibility analysis to reverse-engineer sub-agent and closed it; ran `DYLD_PRINT_LIBRARIES=1` minimal q240 compile seam to confirm framework visibility; created Frida hook/controller/preload scripts under `mps/ANE/.ane_runs/frida/`; ran Python-process hooks for `_ANECCompile`, `ZinAssertImpl`, and both `MarkAllOpsAsInvalid` overloads; tested Frida attach to `ANECompilerService` PID `76891`; ran a zero-mod unified-log filter for `ANECompilerService`; generated `mps/ANE/.ane_runs/json/exact_q240_below_nserror_boundary_probe_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: dyld log shows Python loads `ANECompiler.framework`/`MIL.framework`, but Python-process Frida hooks do not fire for `_ANECCompile` or `MarkAllOpsAsInvalid`; reverse sub-agent confirms validation host is `ANECompilerService.xpc`; current-user Frida attach to PID `76891` fails with `unable to access process`; unified log probe yields zero validation/detail lines | Conclusion: short-term loop complete, verdict=`blocked_need_service_debug_privilege_for_validateentry_map`; exact `ValidateEntry` map capture requires service-side debug privilege or equivalent instrumentation outside current user process | Next: pivot to a memory-neutral compiler-accepted MIL/route candidate search, or only return to service-side instrumentation if SIP/debug privilege changes; do not repeat bridge `NSError` expansion or Python-process Frida hooks.
2026-06-24 10:05:52 +0800 | Goal: package selector-3/selector-8/create-instance/materializer evidence and decide whether a safe memory-neutral speed control is exposed | Actions: used reverse-engineering and ida-reverse methodology; delegated current docs/artifact compression to doc-reader and closed it; added read-only benchmark/private_ane_materializer_control_blocker_package.py; generated mps/ANE/.ane_runs/json/materializer_control_boundary_package_20260624.json and CSV peer; validated JSON/CSV assertions; updated docs/ane_state.md and docs/ane_next.md | Evidence: package verdict=blocked_no_safe_materializer_control_exposed, safe_memory_neutral_control_exposed=false, rejected 5 controls, route profile context has 24 rows, 24 load-cache hits, 0 misses, 0 bridge fast-load hits, estimated 96 attention_pre selector-2 requests, attention_pre_eval_sec=12.588885625009425, axis_pack_sec=3.34072536896565 | Conclusion: short-term loop complete; current host-visible MIL/layout/materializer layer and selector-3/selector-8 create-instance boundary expose no safe memory-neutral speed knob | Next: run a smaller lower-layer timing attribution loop for selector-2 firmware wait/compute vs IOProcessor completion vs host dispatch/synchronization.
2026-06-24 10:21:17 +0800 | Goal: attribute lower selector-2 timing after materializer controls were blocked | Actions: delegated existing artifact discovery to searcher and closed it; added read-only benchmark/private_ane_selector2_timing_attribution_package.py; consumed bridge_eval_path_attribution, attention_pre_throughput_roofline, time_attention_pre_layer0_lifecycle, selector2_update_fw_command_dva_attribution, and materializer_control_boundary artifacts; generated mps/ANE/.ane_runs/json/selector2_lower_timing_attribution_package_20260624.json and CSV peer; validated JSON/CSV assertions; updated docs/ane_state.md and docs/ane_next.md | Evidence: verdict=confirmed_selector2_completion_low_utilization_opaque; route attention_pre_eval_sec=12.588885625009425; accepted layer0 ane_pre_eval_sec=0.7698414579790551 vs write=0.01106487397919409/read=0.026174624013947323/axis_pack=0.05874783397302963; time-axis attention_pre effective throughput=0.20732433083177246 TFLOPS, 1.1356503660811375% of measured ANE FP16 peak; timing buckets classify host setup not dominant, user-space eval subphase unavailable, selector2 submit mapped/not dominant, updateRequestFWCommand semantically required/no safe bypass, firmware_wait_or_compute_body dominant opaque bucket | Conclusion: short-term loop complete; slow inference root cause is low-utilization opaque selector-2 completion path, not top-level load/cache or host-visible materializer control | Next: inventory event traces and bridge source for safe zero-retention eval subphase signposts; if unsafe/unavailable, package privileged instrumentation requirement and return to MIL/body request-count reduction.
2026-06-24 10:39:29 +0800 | Goal: decide and implement safe zero-retention eval subphase signposts | Actions: used diagnosing-bugs plus reverse-engineering/ida-reverse constraints; delegated bridge/source seam analysis to explorer and closed it after completion; patched mps/maderix_ANE/bridge/ane_bridge.m to add setup_sec/send_sec and route-specific setup/send eval profile fields; rebuilt libane_bridge.dylib with make -C mps/maderix_ANE/bridge; validated invalid-handle profile JSON through ctypes; added benchmark/private_ane_eval_signpost_feasibility_package.py; generated mps/ANE/.ane_runs/json/eval_signpost_feasibility_package_20260624.json and CSV peer; validated marker/verdict/CSV checks; updated docs/ane_state.md and docs/ane_next.md | Evidence: make succeeded; invalid-handle profile contains route=eval_invalid_handle, setup_sec, send_sec, eval_client_setup_sec, eval_direct_process_send_sec, eval_model_send_sec; package verdict=confirmed_zero_retention_bridge_eval_setup_send_signposts_added, required_source_markers_present=true, retained_memory_change=none_stack_local_doubles_only, CSV seam rows=3 | Conclusion: short-term loop complete; safe bridge-level setup/send signposts are implemented, but deeper firmware wait vs compute vs IOProcessor completion still requires lower instrumentation | Next: run a minimal accepted attention_pre eval profile to capture setup_sec/send_sec on real ANE eval before deciding between MIL/body request-count reduction and privileged lower selector-2 instrumentation.
2026-06-24 10:49:16 +0800 | Goal: capture new setup_sec/send_sec fields on a minimal accepted integrated attention_pre path | Actions: added new eval keys to BRIDGE_PROFILE_TIME_KEYS and low-level _attach_native_eval_profile; py_compile checked private_ane.py, private_ane_real_attention_probe.py, and transformer_layerwise_compare.py; attempted standalone attention_pre micro-profile, which failed InvalidMILProgram and was rejected as a non-accepted seam; ran integrated layerwise compare with --layers 1 --chunks 1 --compare tiled --q-chunk 240; added benchmark/private_ane_eval_signpost_capture_package.py; generated mps/ANE/.ane_runs/json/eval_signpost_capture_package_20260624.json and CSV peer; updated docs/ane_state.md and docs/ane_next.md | Evidence: integrated compare exact with max_abs=0.0; current variant ane_pre_eval_sec=0.25607962504727766, setup_sec=0.000001375, send_sec=0.2559475, maxrss_mb=1213.3125; tiled_q240 variant ane_pre_eval_sec=0.2514954159851186, setup_sec=0.0000016669999999999999, send_sec=0.251380583, maxrss_mb=1245.3125 | Conclusion: short-term loop complete; bridge-visible setup is negligible and send_sec contains >99% of attention_pre eval bucket, so the remaining bottleneck is opaque selector-2 completion | Next: return to memory-neutral MIL/body/request-count reduction for attention_pre, or require privileged selector-2/IOProcessor instrumentation to split send_sec further.
2026-06-24 10:50:54 +0800 | Correction: exact verdict token for previous loop is `confirmed_eval_send_sec_contains_attention_pre_eval_bucket`; artifact=`mps/ANE/.ane_runs/json/eval_signpost_capture_package_20260624.json`; no new experiment run.
2026-06-24 11:07:22 +0800 | Goal: test remaining unclosed memory-neutral fuse/body/request-count candidates | Actions: delegated code candidate inventory to explorer and closed it; extended benchmark/private_ane_transformer_layerwise_compare.py with candidate-only flags; ran minimal integrated one-layer probes for fuse_gate_ffn, fuse_gate_ffn+no_fuse_residual, and gelu_tanh; added benchmark/private_ane_fuse_candidate_verdict_package.py; generated mps/ANE/.ane_runs/json/fuse_candidate_verdict_package_20260624.json and CSV peer; updated docs/ane_state.md and docs/ane_next.md | Evidence: fuse_gate_ffn exact but slower wall_delta_sec=3.256498041038867; fuse_gate_ffn_no_residual rejected with max_abs=0.0546875; gelu_tanh exact but slower wall_delta_sec=6.622177083045244; package verdict=blocked_no_promotable_memory_neutral_fuse_body_candidate, promotable_candidate_count=0 | Conclusion: short-term loop complete; remaining host-visible fuse/body toggles do not provide a memory-neutral speed candidate | Next: formalize current host-visible MIL/body/request-count exhaustion and name lower capability required for further speedup toward NPU peak.
2026-06-24 11:13:53 +0800 | Goal: formalize host-visible MIL/body/request-count exhaustion and name lower capability requirements | Actions: used docs-generator style packaging plus reverse-engineering/ida-reverse constraints; delegated artifact consistency verification to doc-reader and closed it; added benchmark/private_ane_host_visible_exhaustion_package.py; generated mps/ANE/.ane_runs/json/host_visible_mil_body_request_exhaustion_20260624.json and CSV peer; validated verdict, closed candidate count, and CSV rows; updated docs/ane_state.md and docs/ane_next.md | Evidence: source artifacts present with verdicts: attention_pre body blocked, route policy falsified, eval signpost confirmed send_sec, fused layout invalid, materializer control blocked, fuse/body candidates blocked, selector2 timing opaque; package verdict=blocked_host_visible_mil_body_request_layer_exhausted, promotable_host_visible_candidate_count=0, closed_candidate_classes=7 | Conclusion: short-term loop complete; current host-visible acceleration layer is exhausted under no-memory-growth constraints | Next: choose lower-capability track: new compiler-accepted request-count-reducing attention_pre contract, or privileged selector-2/IOProcessor instrumentation requirements.
2026-06-24 11:25:31 +0800 | Goal: choose the next lower-capability track after host-visible MIL/body/request-count/control exhaustion | Actions: used diagnosing-bugs, reverse-engineering, and docs-generator methodology; delegated lower-capability feasibility scan to doc-reader and closed completed agents; added read-only benchmark/private_ane_lower_capability_track_selection.py; generated mps/ANE/.ane_runs/json/lower_capability_track_selection_20260624.json and CSV peer; updated docs/ane_state.md and docs/ane_next.md | Evidence: package verdict=selected_compiler_contract_requirements_package; selected_track=compiler_contract_attention_pre_request_count_reduction; deferred privileged selector2_ioprocessor_timing as blocked_on_current_machine; carried forward attention_pre_eval_sec=12.588885625009425, eval_sec=20.12377158299205, estimated_attention_pre_selector2_requests=96, time_axis_pre_eval_tflops=0.20732433083177246, time_axis_pre_eval_peak_pct=1.1356503660811375; sub-agent independently confirmed compiler-contract is weak but safe/local while privileged instrumentation is blocked by SIP/KDK/PAC prerequisites | Conclusion: short-term loop complete; next progress should be a read-only attention_pre compiler-contract evidence matrix, not another full-audio benchmark, qchunk sweep, alias model.hwx reuse, or privileged selector-2 instrumentation attempt on the current host | Next: build attention_pre contract evidence matrix from accepted/rejected MIL bodies and cache artifacts; propose exactly one request-count-reducing contract hypothesis, or mark compiler-contract track blocked and promote the privileged requirements package.
2026-06-24 11:35:52 +0800 | Goal: build the attention_pre compiler-contract evidence matrix and decide whether one request-count-reducing hypothesis remains | Actions: used diagnosing-bugs, reverse-engineering, and docs-generator methodology; delegated artifact scan to doc-reader but it completed without payload, then closed it; directly extracted existing JSON evidence; added read-only benchmark/private_ane_attention_pre_contract_matrix.py; generated mps/ANE/.ane_runs/json/attention_pre_contract_evidence_matrix_20260624.json and CSV peer; updated docs/ane_state.md and docs/ane_next.md | Evidence: package verdict=blocked_no_remaining_attention_pre_compiler_contract_hypothesis; viable_hypothesis_count=0; selected_hypothesis=null; 9 matrix rows closed accepted exact q240 baseline, missing exact q240 same-identifier fast-load artifact, MIL-hash-incompatible alias model.hwx, alternative qchunks, fused time/freq layout, route-policy/request coalescing, q240 guard/policy, fuse body toggles, and generic SDPA/public explicit attention; selector2 context preserved attention_pre_eval_sec=12.588885625009425, estimated_attention_pre_selector2_requests=96, time_axis_pre_eval_tflops=0.20732433083177246, time_axis_pre_eval_peak_pct=1.1356503660811375 | Conclusion: short-term loop complete; no memory-neutral host-visible compiler-contract hypothesis remains for attention_pre request-count reduction | Next: prepare privileged selector-2/IOProcessor requirements package with exact prerequisites, target sites, minimal one-shot probe, fields/timestamps, and safety constraints, without changing current machine state.
2026-06-24 11:46:56 +0800 | Goal: package privileged selector-2/IOProcessor requirements without changing current machine state | Actions: used diagnosing-bugs, reverse-engineering, ida-reverse, and docs-generator methodology; delegated selector-2/IOProcessor requirements scan to doc-reader and closed it; captured read-only host facts (`csrutil status`, `sysctl kern.development`, `sw_vers`, `uname`, `/Library/Developer/KDKs` listing); added benchmark/private_ane_privileged_selector2_requirements_package.py; generated mps/ANE/.ane_runs/json/privileged_selector2_ioprocessor_requirements_20260624.json and CSV peer; expanded package with sub-agent target-site precision; updated docs/ane_state.md and docs/ane_next.md | Evidence: package verdict=blocked_current_machine_requires_privileged_selector2_ioprocessor_visibility; current machine has SIP enabled, kern.development=0, no KDK listing, PAC/privilege barriers for lower arm64e targets, no regular ANE open entitlement, and memory constraints requiring one-shot minimal probes only; package contains prerequisites=9, target_sites=11, critical_offsets=6; future probe `single_attention_pre_selector2_completion_split` would split send_sec across materialization, IOConnect submit, firmware compute/wait, completion interrupt, and callback wake | Conclusion: short-term loop complete; exact future lower-layer probe is specified, but local execution is blocked without authorized debug/KDK/PAC-safe instrumentation environment or genuinely new lower compiler/service evidence | Next: external-state change required; do not repeat closed host-visible qchunk/fuse/cache/compiler-contract sweeps.
2026-06-24 11:55:19 +0800 | Goal: formalize the current local private-ANE dead-end across host-visible, compiler-contract, and privileged selector-2 layers | Actions: used diagnosing-bugs, reverse-engineering, ida-reverse, and docs-generator methodology; delegated consistency scan to doc-reader and closed it; added read-only benchmark/private_ane_current_local_dead_end_package.py; generated mps/ANE/.ane_runs/json/current_local_private_ane_dead_end_20260624.json and CSV peer; updated docs/ane_next.md with an explicit authoritative recovery block marker; updated docs/ane_state.md | Evidence: package verdict=blocked_current_local_no_memory_neutral_path_remaining; local_candidate_remaining=false; goal_complete=false; layer chain is host_visible_mil_body_request_control=blocked_host_visible_mil_body_request_layer_exhausted, attention_pre_compiler_contract=blocked_no_remaining_attention_pre_compiler_contract_hypothesis, privileged_selector2_ioprocessor_visibility=blocked_current_machine_requires_privileged_selector2_ioprocessor_visibility; root cause preserved attention_pre_eval_sec=12.588885625009425, estimated_attention_pre_selector2_requests=96, time_axis_pre_eval_tflops=0.20732433083177246, time_axis_pre_eval_peak_pct=1.1356503660811375 | Conclusion: short-term loop complete; current local no-memory-growth private-ANE acceleration path is exhausted, but the long-term goal is not complete because no speedup toward NPU peak was achieved | Next: external-state change or genuinely new lower-layer evidence is required; if provided, resume with packaged one-shot selector-2 completion split probe, otherwise do not continue closed local paths.
2026-06-24 16:52:13 +0800 | Goal: install and verify KDK/debug/PAC-safe instrumentation prerequisites for the private ANE selector-2/IOProcessor blocker | Actions: used reverse-engineering and docs-generator methodology; downloaded `Kernel_Debug_Kit_26.5_build_25F71.dmg` to `/Volumes/2T/kdk`; verified SHA-256 `90ed319cd1ba6e23d1eefcee89fa1b10743f4cf60b85208ae52aa9f45543c7aa`; mounted the DMG; verified `KernelDebugKit.pkg` is signed Apple Software; installed with `installer`; extracted KDK ReadMe text to `/Volumes/2T/kdk/KDK_26.5_25F71_ReadMe.txt`; verified receipts and KDK path; captured SIP/kernel/debug/network/ANE IORegistry facts; generated `mps/ANE/.ane_runs/json/kdk_debug_environment_install_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: KDK installed at `/Library/Developer/KDKs/KDK_26.5_25F71.kdk`; receipts `com.apple.pkg.KDK.25F71` and `com.apple.pkg.KDK_SDK.25F71`; local OS `26.5` build `25F71`; kernel `RELEASE_ARM64_T8132`; SIP enabled; `kern.development=0`; `kern.osbuildconfig=release`; active Ethernet `en5`; ANE IORegistry reports `H11ANEIn`, `ane,t8020`, `h16g`, 16 cores | Conclusion: KDK package installation is complete, but live PAC-safe selector-2 instrumentation is not yet runnable because target security/debug configuration still requires Recovery changes and the KDK ReadMe states Apple Silicon KDP needs built-in Ethernet, likely unavailable on MacBook Air M4 | Next: if continuing, use a supported second-Mac + built-in-Ethernet target setup, disable SIP from Recovery on the target, set `debug=0x44 kdp_match_name=<enX> wdt=-1`, reboot, and run the packaged `single_attention_pre_selector2_completion_split` probe via LLDB/KDK symbols.
2026-06-24 17:15:40 +0800 | Goal: proceed with the first two no-second-Mac routes: static/KDK/IDA-style correlation and single-Mac user-space tracing | Actions: used reverse-engineering, ida-reverse, and docs-generator methodology; attempted `ida-pro-mcp/idb_list` but MCP transport was closed; found many stale `ida_pro_mcp.idalib_server` workers and continued with local KDK/Mach-O tooling; confirmed dyld-cache-backed user frameworks lack standalone binaries but KDK provides standalone ANE kext binaries; inspected `AppleH16ANEInterface.kext`, `AppleT8132ANEHAL.kext`, and `AppleANELoadBalancer.kext`; added `benchmark/private_ane_single_mac_static_trace_package.py`; added Frida fallback `benchmark/private_ane_iokit_selector_trace.js`; Frida attach failed even under `sudo`; added and compiled DYLD interpose tracer `benchmark/private_ane_iokit_selector_trace.c` -> `.dylib`; generated `mps/ANE/.ane_runs/json/single_mac_kdk_static_trace_package_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: static package verdict `single_mac_static_and_user_boundary_trace_ready_but_firmware_completion_still_opaque`; `AppleH16ANEInterface` exports `ANE_ProgramSendRequest` at `0x127d1c`, `ANE_ProgramInputsReady` at `0x1290a8`, debug work-processor entrypoints, `H11ANEInUserClient::externalMethod`, `H11ANEInDirectPathClient::externalMethod`, `ANECoreInterface::ANE_ProgramSendRequest`, and `ANEDriver::ANE_ProgramSendRequest`; local timing context remains `attention_pre_eval_sec=12.588885625009425`, estimated selector-2 requests `96`; DYLD tracer build passed; Frida attach failed with `unable to access process with pid ... from the current user account` | Conclusion: first two requested routes are now actionable within single-Mac constraints: static KDK correlation is packaged and process-local IOConnect boundary tracing is ready. The firmware/IOProcessor completion split remains opaque without privileged runtime/KDP. | Next: run one minimal transformer-only or attention-pre-only benchmark with `PYMSS_ANE_IOKIT_TRACE=/tmp/ane_iokit_trace.ndjson DYLD_INSERT_LIBRARIES=$PWD/benchmark/private_ane_iokit_selector_trace.dylib ...`, then aggregate non-empty selector-2 rows before any full-audio benchmark.
2026-06-24 17:19:00 +0800 | Goal: smoke-test process-local DYLD IOConnect tracing on an accepted `attention_pre` micro-profile | Actions: rebuilt `benchmark/private_ane_iokit_selector_trace.dylib` with a constructor `trace_loaded` marker; ran accepted `batch=62 seq=960 valid_seq=938 q_chunk=128` time-axis micro-profile under `PYMSS_ANE_IOKIT_TRACE=/tmp/ane_iokit_trace_attention_pre_b62.ndjson DYLD_INSERT_LIBRARIES=$PWD/benchmark/private_ane_iokit_selector_trace.dylib`; wrote profile `benchmark_results/private_ane/attention_pre_iokit_trace_b62_20260624.json`; added smoke evidence JSON/CSV | Evidence: profile completed; stages included `rms_qkv`, `rope`, `sdpa`, and `post_reshape`; trace file contained only `trace_loaded` and no `IOConnectCall*` rows; generated `mps/ANE/.ane_runs/json/single_mac_iokit_trace_smoke_20260624.json` and CSV peer | Conclusion: process-local DYLD interpose is loadable but does not observe selector-2 boundary traffic for this accepted ANE route; traffic is outside this Python process, not using these exported wrappers, or below this observable boundary | Next: close process-local IOConnect tracing as insufficient for selector-2 completion splitting; continue only with static KDK/IDA field recovery or higher-level speed work unless service-side/privileged instrumentation becomes available.
2026-06-24 20:32:03 +0800 | Goal: conduct experiment B comparing MLX Transformer execution against the current private-ANE Transformer bottleneck | Actions: used diagnosing-bugs and ane-consumer-benchmark methodology; verified `pymss/modules/bs_roformer/private_ane.py` had no partial diff; ran 10s smoke and full `test_clean.m4a` through `mps/roformer_mlx_backend_compare.py` with `--backends torch,mlx_transformer --dtype float16`; generated `mps/ANE/.ane_runs/json/mlx_transformer_experiment_b_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: smoke result `mlx_transformer` 7.075330000021495s vs Torch/MPS 14.696576665970497s, max abs diff 0.003414243459701538, no backend errors; full result `mlx_transformer` 16.369129040976986s vs Torch/MPS 26.91898808296537s, speedup 1.644497273836551, MLX Transformer calls 48, max abs diff 0.007223784923553467, no backend errors; prior private-ANE Transformer eval loop evidence 20.12377158299205s | Conclusion: experiment B verdict=`confirmed_mlx_transformer_faster_than_current_private_ane_transformer_eval_loop`; MLX is not intrinsically unsuitable for this Transformer workload, and current private-ANE slowness is better explained by segmented selector-2 lifecycle/packing/request overhead than raw compute | Next: implement only an opt-in diagnostic hybrid seam around `run_transformers_layerwise_many(xs)` and measure conversion/sync/memory/correctness on `test_clean.m4a`; do not change default routing or rerun closed ANE qchunk/cache/compiler-contract sweeps.
2026-06-24 20:40:00 +0800 | Goal: correct experiment B interpretation after clarifying deployment objective | Actions: updated `mps/ANE/.ane_runs/json/mlx_transformer_experiment_b_20260624.json` and CSV verdict from a route-candidate framing to `diagnostic_only_all_transformer_on_mlx_not_product_route`; updated `docs/ane_next.md` and `docs/ane_state.md` to state that full-Transformer MLX offload is not meaningful for the ANE/iPhone objective | Evidence: experiment B routed the full RoFormer Transformer module execution to MLX, not just small fragmented glue; user goal is ANE-heavy Transformer inference for future iPhone deployment, with MLX only for low-compute fragmented steps when transfer/sync costs do not erase speed | Conclusion: experiment B remains useful only as a diagnostic control showing current private-ANE Transformer overhead; it must not drive the next route toward full-Transformer MLX offload | Next: identify small fragmented glue/offload candidates around the ANE path and estimate transfer/sync/memory cost before coding; continue lower-control ANE work if authorized instrumentation becomes available.
2026-06-24 20:50:00 +0800 | Goal: define the concrete small fragmented glue candidates after rejecting full-Transformer MLX offload as a route candidate | Actions: used ane-consumer-op-map methodology; inspected current RoFormer/private-ANE path and existing timing artifacts; generated `mps/ANE/.ane_runs/json/small_fragmented_glue_candidate_map_20260624.json` and CSV peer; updated `docs/ane_next.md` and `docs/ane_state.md` | Evidence: current Torch/MPS full profile has `mask_estimator=0.7442880850030633s`, `stft=0.08835171000100672s`, `band_split=0.06806308399973204s`; prior ANE audit has time-axis `axis_pack_sec=2.5199859970016405s` with direct-repack/bridge-pack route variants closed due no safe speed/RSS win | Conclusion: ranked glue candidates are mask tail/final_norm+mask_estimator, STFT/ISTFT/window/overlap, chunk padding/crop/fold/stitch, mask complex multiply, low-priority band_split, and axis layout pack/unpack as eliminate-or-block rather than MLX offload | Next: run a timing-only `glue_timing_split_no_route_change` probe on `test_clean.m4a` that separates final norm, mask estimator, mask multiply, ISTFT, overlap/fold, chunk stitch, and conversion/sync costs before any route change.
2026-06-24 21:50:00 +0800 | Goal: run the next timing-only glue split probe without changing private-ANE routing | Actions: added `benchmark/private_ane_glue_timing_split_probe.py`; py_compile passed; first 10s run was blocked by private_ane long-input guard because it produced 2 chunks; ran 5s single-chunk cold probe and warm rerun; fixed stage grouping so ISTFT is not counted as STFT; generated `mps/ANE/.ane_runs/json/glue_timing_split_summary_20260624.json` and CSV peer; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: cold 5s run elapsed 65.132326833962s with mask core 63.82529950002208s, ISTFT 0.6337148330057971s, STFT 0.020326208032201976s, chunk glue 0.0066303740604780614s; warm 5s run elapsed 15.911116791015957s with mask core 14.919468542037066s (93.76757607901656%), ISTFT 0.2694645829615183s (1.6935617185191467%), STFT 0.017837415973190218s, chunk glue 0.011735458974726498s | Conclusion: verdict=`confirmed_no_large_small_glue_bucket_in_5s_private_ane_path`; broad MLX glue offload is not justified by current evidence. The only local glue follow-up with any plausible ceiling is a narrow source-level split inside `private_ane_istft_roformer` and adjacent mask multiply/tail conversion; the real blocker remains private-ANE mask-core/Transformer selector-2/lower-control timing | Next: either perform the narrow ISTFT/tail source-level split, or return to lower-control/private-ANE Transformer work if authorized instrumentation becomes available.
2026-06-24 22:45:00 +0800 | Goal: deploy a minimal Core ML benchmark to the connected iPhone 13 mini and measure real on-device ANE/Core ML warm refresh/RTF | Actions: used ane-consumer-benchmark methodology; inspected selected RoFormer `.mlpackage` interfaces with coremltools and wrote `mps/ANE/.ane_runs/json/iphone_coreml_model_interfaces_20260624.json`; created `benchmark/ios_coreml_bench/CoreMLBenchApp.xcodeproj` and Swift benchmark app bundling `roformer_layer_pair_0.mlpackage`; benchmark uses `MLModelConfiguration.computeUnits = .cpuAndNeuralEngine`, deterministic `x FLOAT32 [1,938,62,256]`, and measures compile, load, first prediction, and 20 warm predictions; verified unsigned iphoneos build with `CODE_SIGNING_ALLOWED=NO`; queried iPhone 13 mini device details and Xcode signing state | Evidence: device `13mini` is paired/available via CoreDevice id `86DF86A0-D5BB-52C1-B136-6DFED671CC07`, UDID `00008110-000A615E1483801E`, iPhone14,4, iOS `26.5`, Developer Mode enabled; unsigned `xcodebuild -destination 'generic/platform=iOS' ... CODE_SIGNING_ALLOWED=NO build` succeeded; signed build blocked by `No Account for Team "W32PC4WWNC"` and no local matching provisioning profile; direct device build blocked by `The developer disk image could not be mounted on this device`; `devicectl device info details` reports `ddiServicesAvailable: false` | Conclusion: verdict=`inconclusive_environment_blocked_before_on_device_latency`; the iPhone benchmark app is ready and compile-valid, but no on-device latency/RTF was measured because deployment prerequisites are unresolved | Next: in Xcode, add/refresh the Apple ID for team `LQAYX926KW` or install a matching provisioning profile for `com.baicai1145.CoreMLBench`, fix DDI mounting for iPhone 13 mini iOS `26.5`, then run the signed build/install/launch commands recorded in `docs/ane_next.md` and parse `COREML_BENCH_RESULT` into JSON/CSV.
2026-06-24 23:18:30 +0800 | Goal: correct Xcode team selection for the iPhone Core ML benchmark deployment | Actions: inspected the Apple Development certificate subject and Xcode build settings; identified certificate subject `OU=LQAYX926KW` as the actual Team ID, while `W32PC4WWNC` is only the certificate common-name suffix; updated `benchmark/ios_coreml_bench/CoreMLBenchApp.xcodeproj` to use `DEVELOPMENT_TEAM=LQAYX926KW`; retried signed generic/device builds | Evidence: certificate subject is `UID=QQGCKVB9G2, CN=Apple Development: 3423714059@qq.com (W32PC4WWNC), OU=LQAYX926KW, O=1145号员工 白菜工厂`; after switching team, Xcode no longer reports `No Account for Team`; generic signed build reaches Apple provisioning and fails with `Your team has no devices from which to generate a provisioning profile`; current `devicectl list devices` reports `13mini` as `unavailable`, tunnel unavailable, `ddiServicesAvailable=false` | Conclusion: team ID is corrected to `LQAYX926KW`; remaining deployment blocker is registering/connecting the iPhone for provisioning plus DDI/tunnel availability, not wrong team selection | Next: unlock/reconnect/trust the iPhone 13 mini until `devicectl` shows available/tunnel connected, then rerun signed build so Xcode can register the device and create the profile.
2026-06-24 23:39:30 +0800 | Goal: obtain first real iPhone 13 mini Core ML / ANE subgraph latency | Actions: after developer trust, relaunched installed app; fixed app resource lookup from `.mlpackage` to compiled `.mlmodelc`; added on-screen status; diagnosed crash report `CoreMLBenchApp-2026-06-24-233217.ips` showing abort inside `NSJSONSerialization`; replaced fragile `[String: Any]` JSON with typed `Codable` result; rebuilt, reinstalled, launched, waited, and copied `Documents/coreml_bench_result.json` from the app container; wrote canonical JSON/CSV result | Evidence: app container created E5RT cache entries under `Library/Caches/com.baicai1145.CoreMLBench/com.apple.e5rt.e5bundlecache/.../main_ane/model.anehash`; result artifact `mps/ANE/.ane_runs/json/iphone13mini_coreml_ane_subgraph_bench_20260624.json`; iPhone 13 mini iOS `26.5`, model `roformer_layer_pair_0`, input `x FLOAT32 [1,938,62,256]`, `computeUnits=cpuAndNeuralEngine`, load `7305.597833ms`, first prediction `463.395333ms`, warm mean `435.92081045000015ms`, p50 `433.906125ms`, p95 `441.147583ms`, min `431.250916ms`, max `458.196125ms`, 20 iterations after 3 warmups, 5s-shape RTF `0.08718416209000003` | Conclusion: verdict=`confirmed_on_device_coreml_ane_subgraph_latency_measured`; iPhone Core ML / ANE 1-layer-pair warm eval is sub-real-time by a large margin for the 5s-shape assumption, while load remains ~7.3s for this app/model path | Next: reuse the same harness to test 2-pair and 4-pair exported Transformer subgraphs and classify scaling as linear/load-cliff/warm-eval-cliff before extrapolating full Transformer feasibility.
2026-06-25 00:10:00 +0800 | Goal: continue iPhone 13 mini practical Core ML / ANE testing beyond the first 1-pair subgraph toward end-to-end feasibility | Actions: expanded `benchmark/ios_coreml_bench/CoreMLBenchApp` to bundle and benchmark multiple Core ML packages; ran 1/2/4 Transformer layer-pair scaling in one installed app; saved `mps/ANE/.ane_runs/json/iphone13mini_coreml_transformer_scaling_20260624.json` and CSV; then ran `complete_mask_estimator` alone with 5 iterations and saved `mps/ANE/.ane_runs/json/iphone13mini_coreml_complete_mask_estimator_20260624.json`; then added dynamic input shape support and ran `band_split_plus_mask_estimator` with input `x FLOAT32 [1,938,4100]`, saving `mps/ANE/.ane_runs/json/iphone13mini_coreml_band_split_plus_mask_estimator_20260625.json` and CSV | Evidence: Transformer scaling on iPhone 13 mini iOS 26.5 with `computeUnits=cpuAndNeuralEngine`: 1 pair load `7005.73975ms`, warm mean `436.43030835ms`, RTF `0.08728606167`; 2 pairs load `15071.733958ms`, warm mean `869.0061333499998ms`, RTF `0.17380122666999995`; 4 pairs load `33324.411666ms`, warm mean `1794.3140168999998ms`, RTF `0.35886280338`; `complete_mask_estimator` load `2329.102125ms`, warm mean `15.874591599999999ms`, RTF `0.0031749183199999997`; `band_split_plus_mask_estimator` load `3380.436333ms`, warm mean `16.0976666ms`, RTF `0.00321953332` | Conclusion: verdict=`linear_enough_warm_eval_load_scales_poorly`; exported non-Transformer heads are fast and not the practical bottleneck. The remaining iPhone deployment risks are the full Transformer stack warm cost and especially load/cache cost. Current evidence supports proceeding to a real `test_clean.m4a` iPhone app pipeline only after deciding how to package Transformer subgraphs and amortize load | Next: build or export a real iPhone end-to-end path that separates audio decode/STFT, Core ML load, first/warm Transformer prediction, mask/band heads, postprocess/ISTFT, and output write; do not spend time optimizing band split/mask heads first.
2026-06-25 00:47:11 +0800 | Goal: run iPhone 13 mini Core ML hot-cache probe for 4-pair Transformer load persistence | Actions: switched `benchmark/ios_coreml_bench/CoreMLBenchApp/AppDelegate.swift` back to `roformer_layer_pairs_0_3` with input `[1,938,62]`; discovered copied result was stale because the prior app process had not relaunched the new benchmark; added startup result invalidation plus `coreml_bench_status.json` phase markers; rebuilt Release app with team `LQAYX926KW`; clean uninstalled/reinstalled app to clear stale container | Evidence: local app binary contains `roformer_layer_pairs_0_3` and no `band_split_plus_mask_estimator`; clean install path `BD8A02D7-E260-40D5-9454-5CADD96AFC74`; launch failed with `FBSOpenApplicationErrorDomain error 3` / `profile has not been explicitly trusted by the user`; no valid hot-cache Transformer result produced yet | Conclusion: verdict=`blocked_by_ios_developer_profile_trust_after_clean_reinstall`; benchmark harness is prepared, but device-side trust must be restored before cold/hot cache measurement can continue | Next: on iPhone, trust the developer profile for team `LQAYX926KW` again, then relaunch without modifying the app and collect `coreml_bench_status.json` plus cold/hot `coreml_bench_result.json`.
2026-06-25 01:08:23 +0800 | Goal: complete same-install iPhone 13 mini hot-cache probe for 4-pair Core ML Transformer | Actions: relaunched after trust was restored; observed rank-3 input error; patched source input shape to `[1,938,62,256]`; rebuilt and installed over existing app; collected cold launch with phase status and result; terminated PID and relaunched same installed app without reinstall; generated summary artifacts | Evidence: cold status reached `load_started` with `compile_ms=0.02025`, then `first_prediction_started` with `load_ms=30209.740375`; cold result `first_prediction_ms=1781.672042`, warm mean `1757.408792`; hot relaunch result `compile_ms=0.016542`, `load_ms=266.615917`, `first_prediction_ms=1893.237375`, warm mean `1752.437042`; summary `mps/ANE/.ane_runs/json/iphone13mini_coreml_transformer4_hotcache_20260625.json` and CSV peer | Conclusion: verdict=`confirmed_coreml_e5rt_ane_persistent_hot_cache_removes_most_transformer_load_time`; public Core ML persistent backend cache can reduce 4-pair Transformer load by `29943.124458ms` / `113.308x` after first successful load, but it does not reduce warm Transformer eval | Next: design product route around install/first-launch warmup plus in-process `MLModel` retention; focus remaining acceleration on warm eval and real end-to-end pipeline on iPhone, not repeated Core ML load.
2026-06-25 01:17:41 +0800 | Goal: verify product pattern of startup model load plus in-process retained `MLModel` prediction on iPhone 13 mini | Actions: extended iOS harness with a 10s delayed retained prediction using the same loaded `MLModel`; rebuilt and installed over the trusted app; launched once and polled status/result; generated retained-model JSON/CSV artifacts; updated state and next docs | Evidence: install-over launch produced cold-like `load_ms=30021.432834`; first prediction `1779.075125`; warm timed prediction `1748.005417`; retained same-process prediction after `10s` delay `1796.053209`; artifact `mps/ANE/.ane_runs/json/iphone13mini_coreml_transformer4_retained_model_20260625.json` and CSV peer | Conclusion: verdict=`confirmed_startup_warmup_plus_mlmodel_retention_is_correct_product_pattern`; retained model avoids any second load in-process, but active eval remains about `1.75-1.8s` for 4 pairs | Next: build iPhone end-to-end product-pattern timing harness and split real audio pipeline into decode/features, Transformer eval, non-Transformer heads, output/ISTFT/write, and UI/app overhead.
2026-06-25 02:53:55 +0800 | Goal: complete real long-audio iPhone inference path beyond random tensor microbenchmarks | Actions: used `ane-consumer-benchmark` methodology; added real-audio segmented runner to `benchmark/ios_coreml_bench/CoreMLBenchApp/AppDelegate.swift`; exported/bundled 2 real `test.m4a` STFT-flat chunks; inspected segmented Core ML package I/O into `benchmark_results/iphone_coreml_segmented_io_20260625.json`; manually compiled and injected `first_2_segments`, `roformer_layer_pairs_2_3`, `4_5`, `6_7`, `8_9`, `10_11`, and `tail_pipeline` `.mlmodelc` bundles; manually compiled/signed/installed the iOS app after Xcode build service hung on Swift build; ran iPhone 13 mini smoke; also tried all-model upfront load and stage-major tensor-spill variants | Evidence: successful smoke artifact `mps/ANE/.ane_runs/json/iphone13mini_real_audio_segmented_smoke_20260625.json`, CSV `mps/ANE/.ane_runs/csv/iphone13mini_real_audio_segmented_smoke_20260625.csv`; input `[1,938,4100]`, output `[1,1,2050,938,2]`, `chunks=2`, `pipeline_ms=137631.619375`, `load_ms=123988.39887599998`, eval-only total `13383.053457ms`, eval-only RTF versus full `test.m4a` duration `0.04294784031629128`; upfront all-model load died while loading `roformer_layer_pairs_4_5`; stage-major spill died at `roformer_layer_pairs_2_3` chunk 1 prediction | Conclusion: real-audio full 12-layer segmented mask-core execution on iPhone is confirmed for a 2-chunk smoke, but full long-audio inference is not complete because the only successful path reloads models per chunk and stage-major reuse/spill is currently blocked | Next: validate `first_2_segments` hidden tensor spill/readback against direct in-memory output for one real chunk, then reattempt retained-stage processing; only after 2-stage spill passes should full `test.m4a` chunk export and full long-audio run be attempted.
2026-06-25 03:52:51 +0800 | Goal: continue real long-audio iPhone Core ML inference by validating whether hidden tensor spill/restage can support stage-major model reuse | Actions: used `diagnosing-bugs`, `ane-consumer-debug`, and `ane-consumer-benchmark` methodology; checked the prior spill-validation run and found no result plus stale status; patched `benchmark/ios_coreml_bench/CoreMLBenchApp/AppDelegate.swift` so `SpillValidationRunner` writes a checkpoint after direct pair2 success and tests a Core ML-owned contiguous `h1` restage instead of disk readback; manually compiled with `swiftc`, re-signed the large app bundle, installed and launched on iPhone 13 mini; archived JSON/CSV evidence and updated `docs/ane_state.md` / `docs/ane_next.md` | Evidence: checkpoint artifact `mps/ANE/.ane_runs/json/iphone13mini_contiguous_restage_validation_first2_pair23_20260625.json`, status artifact `mps/ANE/.ane_runs/json/iphone13mini_contiguous_restage_status_first2_pair23_20260625.json`, CSV `mps/ANE/.ane_runs/csv/iphone13mini_contiguous_restage_validation_first2_pair23_20260625.csv`; direct pair2 completed in `879.084042ms`; contiguous `h1` restage matched direct `h1` bit-exactly over `14,887,936` floats (`max_abs=0`, `mean_abs=0`); terminal status before app exit was `spill_validation_predict_started` with detail `roformer_layer_pairs_2_3 contiguous_restage`; no final result was produced after the restaged prediction | Conclusion: verdict=`restaged_hidden_tensor_blocked`; the blocker is not just disk spill/readback byte layout because an equivalent Core ML-owned contiguous `MLMultiArray` also kills/exits during pair2 prediction. The next viable route is to keep the direct Core ML output chain alive and reduce reloads through chunk-major retained sequencing, not host/disk hidden-tensor spill | Next: replace the active app runner with a chunk-major retained sequencing smoke for the 2 real chunks, load/release models one stage at a time while feeding direct outputs, then only proceed to full `test.m4a` chunks if the smoke passes.
2026-06-25 04:39:43 +0800 | Goal: run the next direct-handoff iPhone Core ML smoke and attempt full `test.m4a` long-audio inference | Actions: added `InMemoryStageMajorRunner` to `benchmark/ios_coreml_bench/CoreMLBenchApp/AppDelegate.swift`; routed the app to it when real-audio assets are present; compiled with manual `swiftc`; signed/installed/launched the smoke app; copied and archived smoke result/CSV; exported full `test.m4a` STFT-flat asset with `/Users/baicai1145/miniconda3/bin/python benchmark/export_roformer_stft_flat_chunks.py --preset hyperace_v2_voc --audio test.m4a --out-dir benchmark/ios_coreml_bench/CoreMLBenchApp/Assets/real_audio_chunks --max-chunks 0`; copied full asset into the app bundle; re-signed the 774M app; installed and launched it on iPhone 13 mini; attempted status/result retrieval; refreshed host DDIs with `xcrun devicectl manage ddis update --clean`; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: smoke result `mps/ANE/.ane_runs/json/iphone13mini_in_memory_stage_major_smoke_20260625.json`, CSV `mps/ANE/.ane_runs/csv/iphone13mini_in_memory_stage_major_smoke_20260625.csv`; smoke completed both chunks through all 7 stages with `pipeline_ms=125412.533625`, `load_ms=112247.027333`, output shape `[1,1,2050,938,2]`; full asset manifest has `chunks=31`, input shape `[1,938,4100]`, tensor file size `476879200` bytes; full app installed and launched, but every post-launch `devicectl device info/copy` failed with CoreDevice DDI mount/unmount errors `12040/12010` and mobiledevice `0xE8003FFE`, unchanged after host DDI refresh | Conclusion: verdict=`chunk_major_retained_smoke_passed_full_run_transport_blocked`; direct Core ML object handoff is viable for the 2-chunk smoke and avoids the restaged-tensor failure, but the full-run result is not retrievable until the iPhone/CoreDevice developer-service state is reset. Load still dominates the smoke, so this path is correctness/probing progress, not a final speed solution | Next: reconnect or reboot the iPhone 13 mini, then copy `Documents/coreml_bench_status.json` and `Documents/coreml_bench_result.json` from `com.baicai1145.CoreMLBench`; if no final result exists, relaunch the already-installed full-asset app and poll again.
2026-06-25 04:46:46 +0800 | Goal: retry full-audio result retrieval after the user reconnected the iPhone 13 mini | Actions: reran `devicectl list devices`, `devicectl device info processes`, and app-container copies for `Documents/coreml_bench_status.json` / `Documents/coreml_bench_result.json`; checked `xcdevice list` raw output; verified Xcode/CoreDevice versions and installed host DDIs | Evidence: `devicectl list devices` and `xcdevice list` both show `13mini` available over USB, model `iPhone14,4`, iOS `26.5 (23F77)`, UDID `00008110-000A615E1483801E`; all DDI-backed operations still fail before process/copy with CoreDevice errors `12040/12010` and mobiledevice `0xE8003FFE`; Xcode is `26.2 (17C52)`, CoreDevice `506.6`, host DDIs were already refreshed | Conclusion: verdict=`full_long_audio_transport_blocked_reconnect_insufficient`; reconnect did not reset the device-side developer disk image/session state | Next: reboot the iPhone 13 mini or otherwise reset Developer Mode/device services, unlock it, reconnect by cable, then retry copying app status/result before rebuilding or reinstalling.
2026-06-25 05:12:31 +0800 | Goal: retry full-audio Core ML result retrieval after iPhone reboot and reduce first-stage memory pressure | Actions: after reboot, verified `13mini` was available in `devicectl` and `xcdevice`; copied status once and confirmed the full app was running at `in_memory_stage_major_load_started first_2_segments` with no result yet; waited and found status unchanged; patched `InMemoryStageMajorRunner` to stream first-stage input chunks from `input_flat_f32.bin` after model load instead of preloading all 31 chunks; compiled with `swiftc`; signed only the executable and verified the existing 774M app bundle; installed and launched; polled immediately, after 60s, and after 5 minutes | Evidence: after reboot, process list showed `CoreMLBenchApp` PID `464` and status `first_2_segments` load started; no `coreml_bench_result.json` existed; patched build verified with `codesign --verify --deep --strict`; install/launch succeeded; every post-launch process/copy poll failed again with CoreDevice DDI errors `12040/12010` plus mobiledevice `0xE8003FFE`; waiting 5 minutes did not restore DDI-backed access | Conclusion: verdict=`full_long_audio_device_service_blocked_after_launch`; stable CoreDevice access exists before the full app launch, but the full-asset run causes or coincides with DDI-backed service failure before a checkpoint can be retrieved. This is consistent with memory/device-service pressure from the 31-chunk direct-handoff strategy rather than a source compile/signing problem | Next: do not keep polling this run. For further progress, switch to a bounded-window full-audio runner that processes a small window of chunks end-to-end and writes per-window checkpoints, accepting more reloads, or add on-device file logging visible after reboot to preserve the last completed status when CoreDevice dies.
2026-06-25 05:31:32 +0800 | Goal: implement the bounded-window full-audio iPhone runner and attempt deployment | Actions: used `diagnosing-bugs` plus `ane-consumer-benchmark` methodology; patched `benchmark/ios_coreml_bench/CoreMLBenchApp/AppDelegate.swift` so `InMemoryStageMajorRunner` processes the 31 real-audio chunks in 2-chunk windows, keeps direct Core ML tensor handoff only inside each window, writes the existing checkpoint result after each stage, and releases window-local tensors before advancing; manually compiled with `swiftc`; signed only `CoreMLBenchApp`; verified the full app bundle; refreshed host DDIs; retried device info, install, and app-container copy | Evidence: compile succeeded and produced an arm64 iOS Mach-O; `codesign --verify --deep --strict` passed; `xcrun devicectl manage ddis update --clean` completed but reported the refreshed DDI set was equivalent; `devicectl device info details` returned device metadata for iPhone 13 mini but still warned `The developer disk image could not be mounted on this device`; `devicectl device install app` and `devicectl device copy from ... Documents/coreml_bench_status.json` both failed before app launch with CoreDevice `12040/12010` and mobiledevice `0xE8003FFE` | Conclusion: verdict=`bounded_window_device_service_blocked_before_launch`; the bounded-window memory hypothesis is implemented but not yet tested because CoreDevice/DDI access is broken before the new app can be installed or queried | Next: restore iPhone/CoreDevice DDI access by reconnecting or rebooting the iPhone 13 mini, verify `devicectl device info details` has no DDI mount error, then install/launch the already signed bounded-window app and poll `coreml_bench_status.json` / `coreml_bench_result.json`.
2026-06-25 05:55:34 +0800 | Goal: complete real long-audio iPhone 13 mini ANE/Core ML inference with the bounded-window runner | Actions: after the user rebooted the iPhone and `devicectl device reboot` restored DDI access, installed and launched the signed bounded-window app; repeatedly copied `Documents/coreml_bench_status.json` and `Documents/coreml_bench_result.json`; verified all 31 chunks reached 7 stages; archived JSON/status/CSV; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: status ended as `suite_finished` for `real_audio_in_memory_stage_major_coreml`; artifact `mps/ANE/.ane_runs/json/iphone13mini_bounded_window_full_20260625.json`; CSV `mps/ANE/.ane_runs/csv/iphone13mini_bounded_window_full_20260625.csv`; status `mps/ANE/.ane_runs/json/iphone13mini_bounded_window_full_status_20260625.json`; `chunks=31`, final output shape `[1,1,2050,938,2]`, `audio_seconds=311.61179138321995`, `pipeline_ms=412016.404958`, `load_ms=150309.29383500008`, chunk eval sum `254148.41408799993ms`, non-load `261707.11112299992ms`, full RTF `1.3222105721002788`, eval-only RTF `0.8155930587859186`, non-load RTF `0.8398498335422511`; stage eval totals include `tail_pipeline=41704.717877ms` and each transformer/first stage about `35.1-35.7s` across 31 chunks | Conclusion: verdict=`bounded_window_full_passed_but_not_realtime`; this is the first complete real `test.m4a` iPhone ANE/Core ML long-audio run, but repeated model load keeps total wall time above real time | Next: run a minimal `windowSize=4` probe against the same full asset to test whether fewer repeated loads reduce wall time without reintroducing memory or CoreDevice instability.
2026-06-25 06:06:32 +0800 | Goal: test whether larger bounded windows materially reduce repeated-load wall time | Actions: changed only `windowSize` from `2` to `4` in `benchmark/ios_coreml_bench/CoreMLBenchApp/AppDelegate.swift`; rebuilt with manual `swiftc`; executable-only signed and verified the app bundle; installed/launched on iPhone 13 mini; polled status/result until `suite_finished`; archived JSON/status/CSV; updated `docs/ane_state.md` and `docs/ane_next.md` | Evidence: artifact `mps/ANE/.ane_runs/json/iphone13mini_window4_full_20260625.json`; CSV `mps/ANE/.ane_runs/csv/iphone13mini_window4_full_20260625.csv`; status `mps/ANE/.ane_runs/json/iphone13mini_window4_full_status_20260625.json`; `chunks=31`, output shape `[1,1,2050,938,2]`, `pipeline_ms=401705.094375`, `load_ms=135062.72224899998`, chunk eval sum `259168.27112300004ms`, non-load `266642.372126ms`, full RTF `1.289120326903751`, eval-only RTF `0.831702388322896`; compared with window-size-2, wall improved `10311.310583ms`, load improved `15246.571586ms`, eval worsened `5019.857035ms` | Conclusion: verdict=`window4_full_passed_faster_but_marginal`; increasing window size from 2 to 4 is stable but not a root solution because it saves only about 10.3s wall time and remains above real time | Next: optional final tuning point is `windowSize=8`; if it gives less than 30s improvement over window-4 or blocks memory/DDI, stop window tuning and return to private ANE/Core ML load/compile reuse.
