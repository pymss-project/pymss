# Private ANE State

## iPhone 13 mini In-Memory Stage-Major Core ML Smoke - 2026-06-25

- App harness: `benchmark/ios_coreml_bench/CoreMLBenchApp/AppDelegate.swift`, `InMemoryStageMajorRunner`.
- Route: load one stage model, run all bundled chunks through it while preserving direct Core ML `MLMultiArray` outputs in memory, release the stage, then proceed to the next stage. This avoids disk/host hidden-tensor restage.
- Smoke asset: `benchmark/ios_coreml_bench/CoreMLBenchApp/Assets/real_audio_chunks_smoke`, real `test.m4a`, `chunks=2`, input shape `[1,938,4100]`.
- Result artifact: `mps/ANE/.ane_runs/json/iphone13mini_in_memory_stage_major_smoke_20260625.json`; status artifact: `mps/ANE/.ane_runs/json/iphone13mini_in_memory_stage_major_smoke_status_20260625.json`; CSV peer: `mps/ANE/.ane_runs/csv/iphone13mini_in_memory_stage_major_smoke_20260625.csv`.
- Result: `model=real_audio_in_memory_stage_major_coreml`, `pipeline_ms=125412.533625`, `load_ms=112247.027333`, output shape `[1,1,2050,938,2]`, both chunks completed all 7 stages.
- Stage eval totals for 2 chunks: `first_2_segments=1844.793375ms`, `2_3=1771.058625ms`, `4_5=1767.430416ms`, `6_7=1769.609833ms`, `8_9=1790.789416ms`, `10_11=1847.760626ms`, `tail=2119.691625ms`.
- Comparison to per-chunk reload smoke: wall improved from `137631.619375ms` to `125412.533625ms`, and load improved from `123988.39887599998ms` to `112247.027333ms`, but load still dominates. The architecture is functionally viable for direct tensor handoff, but not yet fast.
- Full-audio asset exported: `benchmark/ios_coreml_bench/CoreMLBenchApp/Assets/real_audio_chunks`, `chunks=31`, tensor file `476879200` bytes, manifest shape `[1,938,4100]`; copied into app bundle and launched on iPhone 13 mini.
- Full-audio retrieval blocker: after launching the full-asset app, all `devicectl device info/copy` operations failed with CoreDevice DDI mount/unmount errors `12040/12010` and mobiledevice `0xE8003FFE`; `devicectl manage ddis update --clean` succeeded but did not clear the device-side failure. Full-run result is currently unavailable.
- Reboot/retry update: after iPhone reboot, CoreDevice became available and the already-installed full app was visible/runnable. Initial status copied as `in_memory_stage_major_load_started first_2_segments`; no result existed. A reduced-memory patch changed first-stage input handling to stream the 31 flat chunks after model load instead of preloading all `476879200` bytes. The patched app installed/launched, but DDI-backed process/copy failed again with the same `12040/12010` and `0xE8003FFE` errors during polling and remained broken after a 5-minute wait.
- Verdict: `chunk_major_retained_smoke_passed_full_run_device_service_blocked`. The code path passes the 2-chunk direct-handoff smoke; the full-audio practical test currently destabilizes or blocks iPhone/CoreDevice developer services before a retrievable checkpoint/result. Treat this as a memory/device-service blocker for the 31-chunk in-memory direct-handoff strategy, not as a completed full-long-audio pass.
- Bounded-window update: `InMemoryStageMajorRunner` was changed to process the full 31-chunk `test.m4a` asset in 2-chunk windows, preserving direct Core ML tensor handoff only inside each window and writing the existing checkpoint result after every stage. Manual `swiftc` compile, executable-only codesign, and `codesign --verify --deep --strict` passed. Installation and app-container copy did not start because CoreDevice DDI mount/unmount still fails before app launch with `12040/12010` and mobiledevice `0xE8003FFE`, even after `xcrun devicectl manage ddis update --clean`.
- Current verdict: `bounded_window_device_service_blocked_before_launch`. This does not falsify the bounded-window memory hypothesis; it only proves the current host/device developer-service state is still broken before the new runner can execute.
- Full bounded-window iPhone result: after rebooting the iPhone 13 mini and restoring DDI access, the bounded-window runner completed all 31 chunks of `test.m4a` through all 7 stages with final output shape `[1,1,2050,938,2]`. Artifact: `mps/ANE/.ane_runs/json/iphone13mini_bounded_window_full_20260625.json`; CSV: `mps/ANE/.ane_runs/csv/iphone13mini_bounded_window_full_20260625.csv`; status: `mps/ANE/.ane_runs/json/iphone13mini_bounded_window_full_status_20260625.json`.
- Full bounded-window timing: `audio_seconds=311.61179138321995`, `pipeline_ms=412016.404958`, `load_ms=150309.29383500008`, chunk eval sum `254148.41408799993ms`, non-load `261707.11112299992ms`, full RTF `1.3222105721002788`, eval-only RTF `0.8155930587859186`, non-load RTF `0.8398498335422511`. Verdict: `bounded_window_full_passed_but_not_realtime`; it is the first complete real long-audio iPhone ANE/Core ML run, but repeated per-window model load keeps total wall time above real time.
- Window-size-4 follow-up: `mps/ANE/.ane_runs/json/iphone13mini_window4_full_20260625.json` completed all 31 chunks with output shape `[1,1,2050,938,2]`. Timing: `pipeline_ms=401705.094375`, `load_ms=135062.72224899998`, eval sum `259168.27112300004ms`, non-load `266642.372126ms`, full RTF `1.289120326903751`, eval-only RTF `0.831702388322896`. Compared with window-size-2, wall improved only `10311.310583ms`, load improved `15246.571586ms`, but eval/non-load worsened about `5s`. Verdict: `window4_full_passed_faster_but_marginal`; larger windows reduce repeated load somewhat but do not solve the root speed issue.

## iPhone 13 mini Hidden-Restage Validation - 2026-06-25

- App harness: `benchmark/ios_coreml_bench/CoreMLBenchApp/AppDelegate.swift`, `SpillValidationRunner` patched to test direct `first_2_segments -> roformer_layer_pairs_2_3` against a Core ML-owned contiguous copy of `h1`.
- Device: iPhone 13 mini, CoreDevice ID `86DF86A0-D5BB-52C1-B136-6DFED671CC07`, bundle `com.baicai1145.CoreMLBench`, `computeUnits=.cpuAndNeuralEngine`.
- Command path: manual `swiftc` compile, `codesign` with `Apple Development: 3423714059@qq.com (W32PC4WWNC)`, `devicectl device install app`, then `devicectl device process launch`.
- Result artifact: `mps/ANE/.ane_runs/json/iphone13mini_contiguous_restage_validation_first2_pair23_20260625.json`; status artifact: `mps/ANE/.ane_runs/json/iphone13mini_contiguous_restage_status_first2_pair23_20260625.json`; CSV peer: `mps/ANE/.ane_runs/csv/iphone13mini_contiguous_restage_validation_first2_pair23_20260625.csv`.
- Input: real `test.m4a` smoke chunk asset, `chunks=2`, validation uses chunk `0`, input shape `[1,938,4100]`, hidden shape `[1,938,62,256]`.
- Checkpoint result: `first_2_segments_h1_contiguous_restage` passed bit-exact comparison, `max_abs=0`, `mean_abs=0`, `num_checked=14887936`; direct `roformer_layer_pairs_2_3` prediction completed in `879.084042ms`.
- Terminal status before app exit: `phase=spill_validation_predict_started`, `detail=roformer_layer_pairs_2_3 contiguous_restage`. No final result was produced after feeding the restaged tensor.
- Verdict: `restaged_hidden_tensor_blocked`. The blocker is not only disk spill/readback byte layout: an equivalent Core ML-owned contiguous `MLMultiArray` also kills/exits during pair2 prediction. The next route should keep the direct Core ML output chain alive and reduce reloads via chunk-major retained sequencing, rather than host/disk hidden-tensor spill.

## iPhone 13 mini Real-Audio Segmented Core ML Smoke - 2026-06-25

- App harness: `benchmark/ios_coreml_bench/CoreMLBenchApp/AppDelegate.swift`.
- Input asset: `benchmark/ios_coreml_bench/CoreMLBenchApp/Assets/real_audio_chunks_smoke`, exported from real `test.m4a` STFT-flat tensors with 2 chunks.
- Model chain: `first_2_segments -> roformer_layer_pairs_2_3 -> roformer_layer_pairs_4_5 -> roformer_layer_pairs_6_7 -> roformer_layer_pairs_8_9 -> roformer_layer_pairs_10_11 -> tail_pipeline`.
- Interface evidence: `benchmark_results/iphone_coreml_segmented_io_20260625.json`.
- Result artifact: `mps/ANE/.ane_runs/json/iphone13mini_real_audio_segmented_smoke_20260625.json`; CSV peer: `mps/ANE/.ane_runs/csv/iphone13mini_real_audio_segmented_smoke_20260625.csv`.
- Device/result: iPhone 13 mini, `computeUnits=.cpuAndNeuralEngine`, `audio=test.m4a`, `audio_seconds=311.61179138321995`, `chunks=2`, input shape `[1,938,4100]`, output shape `[1,1,2050,938,2]`.
- Timing: `pipeline_ms=137631.619375`, cumulative per-chunk reload `load_ms=123988.39887599998`, eval-only total `13383.053457`, eval-only RTF versus full `test.m4a` duration `0.04294784031629128`.
- Per-stage eval totals for 2 chunks: `first_2_segments=1916.782333ms`, `2_3=1891.883ms`, `4_5=1847.154292ms`, `6_7=1839.195583ms`, `8_9=1879.723125ms`, `10_11=1881.82025ms`, `tail=2126.494874ms`.
- Verdict: `stage_complete_smoke_passed_but_not_full_long_audio`. The real 12-layer segmented mask-core can execute on iPhone real-audio tensors, but the successful fallback reloads every model per chunk, so it is not a viable full-long-audio architecture.
- Failed follow-up: upfront loading all seven models died while loading `roformer_layer_pairs_4_5`; stage-major tensor-spill runner died at `roformer_layer_pairs_2_3` chunk 1 prediction. Next blocker is validating spilled hidden tensor layout/readback or Core ML retained-stage first-prediction behavior.

## iPhone 13 mini Core ML Deployment Probe - 2026-06-24

- Artifact:
  `benchmark/ios_coreml_bench/CoreMLBenchApp.xcodeproj` with bundled
  `benchmark/ios_coreml_bench/CoreMLBenchApp/Models/roformer_layer_pair_0.mlpackage`.
- Model interface evidence:
  `mps/ANE/.ane_runs/json/iphone_coreml_model_interfaces_20260624.json`.
- Goal:
  test real on-device Core ML / ANE warm prediction latency on connected
  iPhone 13 mini before accepting Mac private-ANE full-path timing as the
  product answer.
- Device evidence:
  `xcrun devicectl list devices` sees `13mini`,
  CoreDevice identifier `86DF86A0-D5BB-52C1-B136-6DFED671CC07`,
  UDID `00008110-000A615E1483801E`, model `iPhone14,4`, iOS `26.5`,
  Developer Mode enabled.
- App behavior:
  the app loads `roformer_layer_pair_0.mlpackage` with
  `MLModelConfiguration.computeUnits = .cpuAndNeuralEngine`, creates
  deterministic `FLOAT32` input `x` shaped `[1, 938, 62, 256]`, measures
  compile, load, first prediction, and 20 warm predictions, then prints and
  writes JSON.
- Build verification:
  `xcodebuild -project benchmark/ios_coreml_bench/CoreMLBenchApp.xcodeproj -scheme CoreMLBenchApp -configuration Release -destination 'generic/platform=iOS' -derivedDataPath benchmark/ios_coreml_bench/DerivedData CODE_SIGNING_ALLOWED=NO build`
  succeeded, proving the Swift/Core ML benchmark compiles for `iphoneos`.
- Deployment status:
  not deployed yet. `xcodebuild -allowProvisioningUpdates ... DEVELOPMENT_TEAM=LQAYX926KW`
  now reaches Apple provisioning but is blocked by
  `Your team has no devices from which to generate a provisioning profile`
  because the iPhone is currently unavailable and no local matching
  provisioning profile exists. Direct device build also blocked because
  `The developer disk image could not be mounted on this device`;
  `devicectl device info details` reports `ddiServicesAvailable: false`.
- Current verdict:
  first iPhone Core ML / ANE subgraph latency was measured after fixing trust,
  Team ID, resource loading, and JSON serialization issues.
- Result artifact:
  `mps/ANE/.ane_runs/json/iphone13mini_coreml_ane_subgraph_bench_20260624.json`
  and CSV peer
  `mps/ANE/.ane_runs/csv/iphone13mini_coreml_ane_subgraph_bench_20260624.csv`.
- Result:
  `roformer_layer_pair_0`, input `x FLOAT32 [1, 938, 62, 256]`,
  `computeUnits=cpuAndNeuralEngine`, iPhone 13 mini iOS `26.5`.
  Load was `7305.597833ms`, first prediction `463.395333ms`, warm mean
  `435.92081045000015ms`, p50 `433.906125ms`, p95 `441.147583ms`,
  min `431.250916ms`, max `458.196125ms`, 20 iterations after 3 warmups.
- Interpreted RTF:
  using the current benchmark's 5s audio-shape assumption, one layer-pair
  warm prediction RTF is `0.08718416209000003`.
- Caveat:
  this is one exported RoFormer layer-pair subgraph, not the full
  end-to-end audio pipeline. The measured app container contains E5RT/ANE
  cache artifacts including `main_ane/model.anehash`, but `computeUnits`
  alone is still not a formal per-op ANE residency proof.
- Transformer scaling artifact:
  `mps/ANE/.ane_runs/json/iphone13mini_coreml_transformer_scaling_20260624.json`
  and CSV peer
  `mps/ANE/.ane_runs/csv/iphone13mini_coreml_transformer_scaling_20260624.csv`.
- Transformer scaling result:
  1 layer-pair warm mean `436.43030835ms`, RTF `0.08728606167`, load
  `7005.73975ms`; 2 layer-pairs warm mean `869.0061333499998ms`, RTF
  `0.17380122666999995`, load `15071.733958ms`; 4 layer-pairs warm mean
  `1794.3140168999998ms`, RTF `0.35886280338`, load `33324.411666ms`.
- Scaling verdict:
  `linear_enough_warm_eval_load_scales_poorly`. Warm eval is close to linear
  through 4 layer-pairs, but load time grows to `33.3s` for 4 layer-pairs.
- Non-Transformer ladder artifacts:
  `mps/ANE/.ane_runs/json/iphone13mini_coreml_complete_mask_estimator_20260624.json`
  and
  `mps/ANE/.ane_runs/json/iphone13mini_coreml_band_split_plus_mask_estimator_20260625.json`.
- Non-Transformer ladder result:
  `complete_mask_estimator` warm mean `15.874591599999999ms`, RTF
  `0.0031749183199999997`, load `2329.102125ms`; `band_split_plus_mask_estimator`
  warm mean `16.0976666ms`, RTF `0.00321953332`, load `3380.436333ms`.
- Practical conclusion:
  on iPhone 13 mini, exported non-Transformer Core ML subgraphs are not the
  practical bottleneck. The remaining end-to-end risk is the Transformer stack
  and especially model load/cache behavior, not band split or mask-estimator
  heads.

## Small Fragmented Glue Candidate Map - 2026-06-24

- Artifact:
  `mps/ANE/.ane_runs/json/small_fragmented_glue_candidate_map_20260624.json`
  and CSV peer
  `mps/ANE/.ane_runs/csv/small_fragmented_glue_candidate_map_20260624.csv`.
- Goal:
  identify non-Transformer glue that may run outside ANE without
  undermining the ANE-heavy/iPhone deployment objective.
- Non-goal:
  do not route full Transformer, attention, or FFN compute to MLX/Metal
  as the product path.
- Evidence sources:
  `benchmark_results/mps_attention/test_clean_full_torch_mps_profile_current.json`,
  `benchmark_results/mps_attention/profile_hyperace_480k_bottleneck_report.json`,
  `mps/ANE/.ane_runs/json/time_attention_pre_request_axis_pack_audit_20260624.json`,
  current `docs/ane_state.md`, `pymss/modules/bs_roformer/common.py`,
  and `pymss/modules/bs_roformer/private_ane.py`.
- Ranked decisions:
  `mask_tail_final_norm_and_mask_estimator` is the first measurable
  candidate; current Torch/MPS profile has `mask_estimator=0.7442880850030633s`
  on `test_clean.m4a`, but transfer/sync costs are unknown.
- Ranked decisions:
  `stft_istft_windowing_overlap_add` should be split before offload; current
  profile has `stft=0.08835171000100672s`, so STFT alone has limited ceiling,
  while ISTFT/overlap timing still needs isolation.
- Ranked decisions:
  `chunk_padding_crop_overlap_fold_and_output_stitch` needs instrumentation
  first because current scopes are inclusive wrappers.
- Ranked decisions:
  `mask_application_complex_multiply` should be fused with mask tail or ISTFT
  if used; otherwise the arithmetic is too small and transfer dominates.
- Ranked decisions:
  `band_split_projection` is low priority; current profile has
  `band_split=0.06806308399973204s`, and prior fused ANE grouping attempts
  hit compile/load blockers.
- Ranked decisions:
  `axis_layout_pack_unpack_between_ane_segments` should not be offloaded to
  MLX as a standalone step. It should be eliminated/fused through a lower
  layout contract, or remain a lower-control blocker. Prior evidence shows
  time-axis `axis_pack_sec=2.5199859970016405s`, but direct repack and
  bridge-pack variants did not produce a safe speed/RSS win.
- Recommended next probe:
  `glue_timing_split_no_route_change` on `test_clean.m4a`, measuring final
  norm, mask estimator, mask multiply, ISTFT, overlap/fold, chunk stitch,
  and conversion/sync costs without changing default routing.

## Glue Timing Split Probe - 2026-06-24

- Probe script:
  `benchmark/private_ane_glue_timing_split_probe.py`.
- Summary artifact:
  `mps/ANE/.ane_runs/json/glue_timing_split_summary_20260624.json`
  and CSV peer
  `mps/ANE/.ane_runs/csv/glue_timing_split_summary_20260624.csv`.
- Raw artifacts:
  cold single-chunk run
  `mps/ANE/.ane_runs/json/glue_timing_split_no_route_change_5s_20260624.json`
  and warm single-chunk run
  `mps/ANE/.ane_runs/json/glue_timing_split_no_route_change_5s_warm_20260624.json`.
- Warm command:
  `/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_glue_timing_split_probe.py --audio test_clean.m4a --duration 5 --out mps/ANE/.ane_runs/json/glue_timing_split_no_route_change_5s_warm_20260624.json --csv-out mps/ANE/.ane_runs/csv/glue_timing_split_no_route_change_5s_warm_20260624.csv`.
- Warm result:
  elapsed `15.911116791015957s` for `5.0s` audio. Dominant scope is
  `private_ane.private_ane_forward_mask_core_batch_layerwise`
  at `14.919468542037066s` (`93.76757607901656%`).
- Warm glue buckets:
  `private_ane.private_ane_istft_roformer=0.2694645829615183s`
  (`1.6935617185191467%`),
  `private_ane.private_ane_stft_roformer=0.017837415973190218s`
  (`0.11210662461645637%`), and aggregate chunk glue
  `0.011735458974726498s` (`0.07375634990846652%`).
- Verdict:
  `confirmed_no_large_small_glue_bucket_in_5s_private_ane_path`.
  There is no broad MLX-worthy glue bucket in this accepted single-chunk
  private-ANE path. The only remaining local glue follow-up worth considering
  is a narrow source-level split of `private_ane_istft_roformer` and adjacent
  mask multiply/tail conversion to see whether the `~0.27s` ISTFT bucket
  contains avoidable copy/conversion cost.
- Limitation:
  the probe was intentionally limited to `--duration 5` to stay inside the
  private-ANE single-chunk guard. Full `test_clean.m4a` was not rerun because
  this timing-only probe already falsified a large small-glue offload bucket.

## MLX Transformer Experiment B - 2026-06-24

- Artifact:
  `mps/ANE/.ane_runs/json/mlx_transformer_experiment_b_20260624.json`
  and CSV peer
  `mps/ANE/.ane_runs/csv/mlx_transformer_experiment_b_20260624.csv`.
- Full benchmark result:
  `benchmark_results/mps_attention/roformer_mlx_transformer_test_clean_full_20260624.json`.
- Smoke benchmark result:
  `benchmark_results/mps_attention/roformer_mlx_transformer_test_clean_10s_20260624.json`.
- Full command:
  `/Users/baicai1145/miniconda3/bin/python mps/roformer_mlx_backend_compare.py --preset hyperace_v2_voc --audio test_clean.m4a --backends torch,mlx_transformer --dtype float16 --out benchmark_results/mps_attention/roformer_mlx_transformer_test_clean_full_20260624.json`.
- Full `test_clean.m4a` result:
  Torch/MPS elapsed `26.91898808296537s`; `mlx_transformer`
  elapsed `16.369129040976986s`; speedup vs Torch/MPS
  `1.644497273836551`; MLX Transformer calls `48`;
  backend errors `[]`.
- Correctness comparison:
  max absolute difference vs Torch is `0.007223784923553467`
  for both `vocals` and `instrument` in this harness.
- Memory observation:
  Torch RSS `534.453125 MiB`, MLX RSS `714.953125 MiB`;
  Torch MPS driver memory `5553.828125 MiB`, MLX MPS driver memory
  `2507.40625 MiB`.
- Comparison to current private-ANE evidence:
  prior private-ANE Transformer eval loop `20.12377158299205s`,
  prior Transformer segment wall `29.116179916920373s`, prior warm
  private-ANE full wall `35.891103s`. MLX Transformer is
  `3.7546425420150626s` faster than the prior private-ANE Transformer
  eval loop, about `1.2293733852678437x`.
- Verdict:
  `diagnostic_only_all_transformer_on_mlx_not_product_route`.
  This benchmark routed the full RoFormer Transformer module execution to
  MLX, so it is not a meaningful product route for the ANE/iPhone goal.
  The result is useful only as a diagnostic control: it supports the
  existing diagnosis that the current private-ANE Transformer path is
  dominated by segmented selector-2 lifecycle, axis-pack/unpack, and
  request overhead rather than raw arithmetic.
- Planning consequence:
  do not implement full-Transformer MLX offload as the next route. Keep
  heavy Transformer compute on ANE, and only evaluate MLX/Metal/CPU for
  small fragmented glue steps if transfer, synchronization, correctness,
  and retained memory are measured directly.

## 2026-06-24 fused time+freq layout feasibility package

- Artifact:
  `mps/ANE/.ane_runs/json/fused_time_freq_layout_feasibility_package_20260624.json`
  and CSV peer
  `mps/ANE/.ane_runs/csv/fused_time_freq_layout_feasibility_package_20260624.csv`.
- Probe script:
  `benchmark/private_ane_fused_layout_feasibility_package.py`.
- Source artifact:
  `mps/ANE/.ane_runs/json/fused_time_freq_layout_compile_probe_20260624.json`.
- Verdict:
  `falsified_fused_layout_compile_invalid`.
- Compile evidence:
  `time_to_freq_transpose_compile_only` compiled, and
  `time_to_freq_crop_compile_only` compiled. The required
## Single-Mac Static/User Trace Update - 2026-06-24 17:15 +0800
- Added static KDK evidence packager: `benchmark/private_ane_single_mac_static_trace_package.py`.
- Generated evidence: `mps/ANE/.ane_runs/json/single_mac_kdk_static_trace_package_20260624.json` and CSV peer.
- Added process-local IOConnect boundary tracer: `benchmark/private_ane_iokit_selector_trace.c`, compiled to `benchmark/private_ane_iokit_selector_trace.dylib`.
- Added Frida fallback tracer: `benchmark/private_ane_iokit_selector_trace.js`, but Frida attach is currently blocked even under `sudo` with `unable to access process ... from the current user account`.
- Static KDK target surface is now confirmed locally: `AppleH16ANEInterface.kext` exports `ANE_ProgramSendRequest`, `ANE_ProgramInputsReady`, debug work-processor methods, `H11ANEInUserClient::externalMethod`, `H11ANEInDirectPathClient::externalMethod`, `ANECoreInterface::ANE_ProgramSendRequest`, and `ANEDriver::ANE_ProgramSendRequest`.
- Relevant H16 handler address evidence includes `ANE_ProgramSendRequest` at kext offset `0x127d1c`, `ANE_ProgramInputsReady` at `0x1290a8`, `ANE_GetDebugWorkProcessorItem` at `0x128bf0`, `ANE_RegisterDebugWorkProcessor` at `0x1289d4`, and `ANE_CompleteDebugWorkProcessorItem` at `0x128ce0`.
- DYLD tracer build verified with `clang -dynamiclib -O2 -Wall -Wextra -o benchmark/private_ane_iokit_selector_trace.dylib benchmark/private_ane_iokit_selector_trace.c -framework IOKit`.
- DYLD tracer smoke result: accepted `attention_pre` micro-profile completed and logged `trace_loaded`, but captured zero `IOConnectCall*` rows and zero selector-2 rows. This indicates process-local interposition in the Python benchmark process is not enough to see selector-2 boundary traffic for this accepted route.
- Current verdict: `single_mac_static_and_user_boundary_trace_ready_but_firmware_completion_still_opaque`.
- Remaining limit: single-Mac user-space boundary tracing can timestamp `IOConnectCall*` selector calls inside our benchmark process, but still cannot distinguish firmware compute/wait, IOProcessor queueing, completion interrupt, or callback wake after the call enters the kernel.

## KDK Debug Environment Update - 2026-06-24 16:52 +0800
- Exact-build KDK for macOS `26.5` build `25F71` is now installed at `/Library/Developer/KDKs/KDK_26.5_25F71.kdk`.
- Verified local build: `Darwin Kernel Version 25.5.0 ... RELEASE_ARM64_T8132`; KDK includes `kernel.development.t8132` and `kernel.release.t8132.dSYM`.
- Verified package: Apple Software signed; DMG SHA-256 `90ed319cd1ba6e23d1eefcee89fa1b10743f4cf60b85208ae52aa9f45543c7aa`; receipts `com.apple.pkg.KDK.25F71` and `com.apple.pkg.KDK_SDK.25F71`.
- Current runtime is still not a live debug target: SIP is enabled, `kern.development=0`, `kern.osbuildconfig=release`.
- Active Ethernet is `en5`; KDK ReadMe says Apple Silicon KDP requires built-in Ethernet and not USB Ethernet or Wi-Fi. On MacBook Air M4 this likely remains the main live-KDP hardware blocker.
- ANE device is present in IORegistry as `H11ANEIn`, `ane,t8020`, architecture `h16g`, 16 ANE cores.
- Current verdict: `kdk_installed_but_live_kdp_target_configuration_still_blocked`.
- Evidence: `mps/ANE/.ane_runs/json/kdk_debug_environment_install_20260624.json`, `mps/ANE/.ane_runs/csv/kdk_debug_environment_install_20260624.csv`, `/Volumes/2T/kdk/KDK_26.5_25F71_ReadMe.txt`.

  `time_to_freq_crop_pad_compile_only` padded contract failed with
  `InvalidMILProgram` while trying to concat zero-pad columns from
  `FREQ_SEQ=62` to `FREQ_PAD=64`.
- Memory/correctness status:
  this packaging loop was read-only and retained no runtime handles or buffers.
  Correctness was not reached for the required padded contract because compile
  failed before eval/load validation.
- Conclusion:
  the current host-visible fused time+freq MIL/layout contract is blocked at
  ANECompiler validation. Transpose/crop primitives alone are not enough,
  because unpadded freq runtime requires a lower padded surface/materializer
  contract. The next loop must move below the current host-visible layout
  surface or produce a formal blocker package naming the missing capability.

## 2026-06-24 route-policy / request-lifecycle analysis

- Artifact:
  `mps/ANE/.ane_runs/json/route_policy_lifecycle_analysis_20260624.json`
  and CSV peer
  `mps/ANE/.ane_runs/csv/route_policy_lifecycle_analysis_20260624.csv`.
- Probe script:
  `benchmark/private_ane_route_policy_lifecycle_analysis.py`.
- Verdict:
  `falsified_no_memory_neutral_route_policy_candidate`.
- Source profile:
  `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_load_cache_bridgeprofile_20260623_profile/transformer_timings.csv`.
- Measured buckets:
  24 transformer rows, 24 load-cache hit rows, 0 load-cache misses, estimated
  96 total `attention_pre` selector requests. Time axis remains dominant with
  48 estimated requests, `attention_pre_eval_sec=9.538814419182017`,
  `axis_pack_sec=2.5199859970016405`, `ane_write_sec=0.5406000427610707`,
  and `ane_read_sec=0.7503471150121186`.
- Closed route-policy candidates:
  axis gating / batch-axis promotion, q240 shape-guard tightening as a speed
  fix, skip-source/write or fast-load policy, request batching/coalescing
  without MIL/lower-contract change, and host-visible axis-pack repack policy.
- Conclusion:
  no memory-neutral route-policy lever remains at the current host-visible
  layer. Further speed progress must test a fused time+freq MIL/layout
  contract or move lower than the current service/compiler visibility boundary.

## 2026-06-24 attention_pre compiler-accepted inventory

- Artifact:
  `mps/ANE/.ane_runs/json/attention_pre_compiler_accepted_inventory_20260624.json`
  and CSV peer
  `mps/ANE/.ane_runs/csv/attention_pre_compiler_accepted_inventory_20260624.csv`.
- Probe script:
  `benchmark/private_ane_attention_pre_candidate_inventory.py`.
- Verdict:
  `blocked_no_memory_neutral_compiling_candidate`.
- Result:
  7 candidates were normalized and 0 were promotable. The current accepted
  integrated q240 route is still the only operable baseline, not a new fix.
  The exact q240 fast-load candidate remains blocked because the exact cache is
  source-only / no loadable `model.hwx`, and direct compile fails
  `InvalidMILProgram`. The alias full-attention family has 12 cache dirs with
  `model.hwx`, but the MIL hash is incompatible, so copying those artifacts
  remains disallowed. qchunk alternatives, host-visible layout/surface knobs,
  generic/public SDPA, and B44E same-identifier refresh are closed.
- Baseline retained for comparison:
  best known `test_clean.m4a` private ANE path remains wall
  `27.903367375023663s`, transformer eval `19.743745001906063s`; accepted
  hot-path time-axis `attention_pre` is still low utilization at roughly
  `0.207 TFLOPS` / `1.14%` of measured local ANE FP16 peak.
- Conclusion:
  compiler-accepted body substitution is exhausted under current constraints.
  The next loop must inspect memory-neutral route-policy / request-lifecycle
  changes that preserve the accepted q240 MIL identity and do not retain extra
  memory.

## 2026-06-24 band_split B44E same-identifier refresh probe

- Artifact:
  `mps/ANE/.ane_runs/json/band_split_b44e_refresh_probe_20260624.json`
  and CSV peer
  `mps/ANE/.ane_runs/csv/band_split_b44e_refresh_probe_20260624.csv`.
- Probe script:
  `benchmark/private_ane_band_split_b44e_refresh_probe.py`.
- Verdict:
  `blocked_b44e_load_qos_rejects_and_refresh_compile_invalid`.
- Target identifier:
  `B44E9E4203023F73CA510E0D86017ABD453DBD65680843296215AF2ADE2EDCB5_6A52E18B7A88B752DD6AC04AC4348A1D14976077C89669F9C2891772FF3287BA_E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`.
- Result:
  exact B44E load-only failed through `load_cache_skip_source_write`
  (`load_ok=false`, `load_qos_sec≈0.029s`, `success=0`), and same-identifier
  fallback compile also failed (`compile_ok=false`, route `compile`,
  `compile_qos_sec≈0.0086s`, `success=0`) with
  `InvalidMILProgram`.
- Memory status:
  probe frees any successful handle immediately and records
  `retained_handles=0`, `retained_extra_buffers=0`. This loop did not use
  retained handles, IOSurfaces, runtime clone cache, or extra long-lived
  buffers as an acceleration path.
- Safety note:
  the first probe implementation allowed bridge cleanup to remove the main
  B44E cache directory after fallback compile failure. The cache was restored
  only from same-identifier wrapperwork/repro artifacts: raw `model.mil` from
  `band_split_l2_fused_0_4_repro`, client/net/data/weights from the same
  B44E wrapper clone, and `model.hwx`/`model.src`/`model.retain` from the same
  B44E wrapper output. No alias or different-MIL `model.hwx` was copied.
- Conclusion:
  B44E refresh/materialization is closed under current safe host-visible
  controls. The next loop should inventory compiler-accepted, memory-neutral
  transformer / `attention_pre` body or route-policy alternatives instead of
  repeating B44E load-cache refresh.

## 2026-06-24 band_split B44E cache materialization probe

- Artifact:
  `mps/ANE/.ane_runs/json/band_split_b44e_cache_materialization_probe_20260624.json`
  and CSV peer
  `mps/ANE/.ane_runs/csv/band_split_b44e_cache_materialization_probe_20260624.csv`.
- Verdict:
  `blocked_band_split_cache_present_but_load_qos_rejects_then_compile_invalid`.
- Target identifier:
  `B44E9E4203023F73CA510E0D86017ABD453DBD65680843296215AF2ADE2EDCB5_6A52E18B7A88B752DD6AC04AC4348A1D14976077C89669F9C2891772FF3287BA_E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`.
- Cache state:
  the directory exists under
  `benchmark_results/private_ane/ane_tmp_loadcache/` and contains
  `model.hwx`, `model.mil`, `model.client.mil`, `net.plist`, `data`,
  `model.src`, `model.retain`, and `weights/`.
- Integrity:
  `model.mil` SHA-256 matches the identifier prefix
  `B44E9E4203023F73CA510E0D86017ABD453DBD65680843296215AF2ADE2EDCB5`;
  this is not a simple missing-cache or wrong-MIL case.
- Diagnostic change:
  `benchmark/private_ane_real_attention_probe.py` now preserves
  `load_cache_error_profile` when load-cache fails and fallback compile also
  fails.
- Probe results:
  - Relative tmpdir run:
    `load_cache_skip_source_write`, `fast_load_attempted=1`,
    `fast_load_hit=0`, `fast_load_fallback=1`, `load_qos_sec=0.027878875`;
    fallback route `compile` fails `InvalidMILProgram`.
  - Absolute tmpdir run:
    `load_cache_skip_source_write`, `fast_load_attempted=1`,
    `fast_load_hit=0`, `fast_load_fallback=1`, `load_qos_sec=0.016694167`;
    fallback route `compile` fails `InvalidMILProgram`.
- Conclusion:
  absolute cache path reduces `tmpdir_sec` but does not make the package
  loadable. The current blocker is a stale or service-rejected compiled
  artifact / `loadWithQoS` compatibility issue for this auxiliary band-split
  package, not a missing file or path mismatch.
- Next implication:
  test whether the exact B44E `model.hwx` can be safely regenerated/refreshed
  from the matching MIL/weights without changing identifier or increasing
  retained memory. Do not copy incompatible artifacts.

## 2026-06-24 full-path q240 native eval capture blocked by band_split

- Artifact:
  `mps/ANE/.ane_runs/json/full_path_q240_native_eval_capture_blocked_20260624.json`
  and CSV peer
  `mps/ANE/.ane_runs/csv/full_path_q240_native_eval_capture_blocked_20260624.csv`.
- Verdict:
  `blocked_full_path_q240_native_eval_capture_by_band_split_compile`.
- Goal:
  rerun the canonical accepted full-path q240 benchmark after adding native eval
  telemetry, so time-axis layer0 `attention_pre` could populate
  `ane_pre_native_eval_total_sec`.
- Result:
  both full-path attempts failed before transformer at
  `band_split_l2_fused_0_4`, so no q240 `attention_pre` eval timing was
  captured.
- Failed attempts:
  - Without explicit `--private-ane-load-cache`:
    child dir
    `benchmark_results/private_ane/test_clean_full_private_native_eval_profile_q240_20260624.private_ane_child`;
    failed at `band_split_l2_fused_0_4`, identifier
    `B44E9E4203023F73CA510E0D86017ABD453DBD65680843296215AF2ADE2EDCB5_6A52E18B7A88B752DD6AC04AC4348A1D14976077C89669F9C2891772FF3287BA_E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`,
    route `compile`, `fast_load_attempted=0`, `InvalidMILProgram`.
  - With explicit `--private-ane-load-cache --private-ane-cache-tmpdir benchmark_results/private_ane/ane_tmp_loadcache`:
    child dir
    `benchmark_results/private_ane/test_clean_full_private_native_eval_profile_q240_loadcache_20260624.private_ane_child`;
    same identifier, same stage, route `compile`, `fast_load_attempted=0`,
    `InvalidMILProgram`.
- Important distinction:
  native eval telemetry is already implemented and works on eval-reaching
  smoke probes, but the full-path q240 capture cannot currently reach
  transformer because an auxiliary band-split precondition regressed or is
  missing.
- Next implication:
  do not repeat q240 native eval capture until the accepted
  `band_split_l2_fused_0_4` load-cache/materialization route is restored or a
  different accepted full-path seam reaches transformer before band split.

## 2026-06-24 accepted q240 native eval profile probe

- Artifact:
  `mps/ANE/.ane_runs/json/accepted_q240_eval_native_profile_probe_20260624.json`
  and CSV peer
  `mps/ANE/.ane_runs/csv/accepted_q240_eval_native_profile_probe_20260624.csv`.
- Verdict:
  `confirmed_native_eval_profile_instrumentation_but_exact_q240_blocked_before_eval`.
- Code changes:
  - `mps/maderix_ANE/bridge/ane_bridge.m` now stores eval profile JSON from
    `ane_bridge_eval`, including `eval_total_sec`, `eval_client_sec`,
    `eval_direct_process_sec`, and `eval_model_sec`.
  - `benchmark/private_ane_real_attention_probe.py` now refreshes
    `last_bridge_profile` after eval, attaches numeric native eval fields to
    timing dictionaries, and includes `bridge_profile` JSON in eval failures.
  - `mps/maderix_ANE/bridge/libane_bridge.dylib` was rebuilt with
    `make -C mps/maderix_ANE/bridge`.
- Minimal probes:
  - Exact q240 layerwise seam command:
    `/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --compare bridge-env --layers 1 --chunks 1 --q-chunk 240 --cache-tmpdir benchmark_results/private_ane/ane_tmp_loadcache --probe-handle-scope pre --probe-stop-after-axis time --probe-stop-after-layer 1 --bridge-env ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT=1 --bridge-env PYMSS_PRIVATE_ANE_TILED_TIME_ATTENTION_PRE=1 --bridge-env PYMSS_PRIVATE_ANE_TILED_TIME_ATTENTION_PRE_Q_CHUNK=240 --out benchmark_results/private_ane/accepted_q240_eval_native_profile_probe_20260624.json`
  - Result: failed before eval with `InvalidMILProgram` for exact identifier
    `CFEEBA68A0867D458FFA754FC3777ECDCE97C7AB6DD42ABE81D759AD310D59C6_F88156576125F4F2458BEBCC36F5BEFAB235C4F43F46BA3EAEA629FAD5C6051D_E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`;
    no output JSON was written by the layerwise script.
  - Smoke command:
    `/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_real_attention_probe.py --axis freq --batch 1 --seq 8`
  - Smoke result: reached eval and failed with `bridge_profile` containing
    `route=eval_model`, `eval_total_sec=0.000174542`, and
    `eval_model_sec=0.000174542`, proving the native eval telemetry path works.
- Memory policy:
  instrumentation adds scalar timing/profile fields only; it does not retain
  ANE handles, IOSurfaces, buffers, snapshots, runtime clone caches, or extra
  model artifacts.
- Solution implication:
  exact q240 `ane_pre_eval` still cannot be split from the current layerwise
  seam because the handle is never created. The next valid route is to capture
  the new `ane_pre_native_eval_total_sec` fields inside an already accepted
  full-path q240 handle context, or continue exact q240 `model.hwx`
  materialization work instead of repeating compile-failing layerwise seams.

## 2026-06-24 attention_pre memory-neutral candidate inventory

- Artifact:
  `mps/ANE/.ane_runs/json/attention_pre_memory_neutral_candidate_inventory_20260624.json`
  and CSV peer
  `mps/ANE/.ane_runs/csv/attention_pre_memory_neutral_candidate_inventory_20260624.csv`.
- Verdict: `blocked_no_memory_neutral_compiling_candidate`.
- Baseline retained for comparison:
  `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_20260623.private_ane_child/meta.json`
  reports `27.903367s` for `39.590023s` audio (`RTF 0.704808`).
- Candidate inventory result:
  - Accepted integrated exact q240 remains the current opt-in baseline:
    compiler-accepted, numerically exact for existing layer0 evidence, and
    full-path validation did not show RSS/swap increase; however it still uses
    `load_cache_skip_source_write` with `fast_load_hit=0` and remains low
    utilization.
  - Exact integrated q240 fast-load/loadable artifact is the strongest
    theoretical memory-neutral candidate, but is not operable now: the target
    cache is source-only, exact `model.hwx` is absent, and direct exact q240
    compile fails `InvalidMILProgram`.
  - Same-weight alias/full-attention compiled artifacts are rejected under
    current constraints because the MIL hash differs; copying alias
    `model.hwx` into the exact q240 cache remains unsafe.
  - Alternative q-chunks are closed for this loop: q240 is the local accepted
    minimum; q480 compiles but is slower/higher RSS; q64/q120/q160/q192/q320/
    q960 fail with `InvalidMILProgram`.
  - Host-visible graph/layout knobs such as unpadded freq, surface handoff,
    forced all-layer q240, and generic SDPA/public explicit attention do not
    provide a memory-neutral promoted path based on existing artifacts.
- Code fact from sub-agent exploration:
  current code supports only monolithic full `attention_pre` and q-chunked
  tiled `attention_pre`; there is no implemented interleaved concat,
  no-final-concat, alias-attention, full-rank-alias, MQA, or GQA variant.
- Solution implication:
  do not run full audio again until either exact q240 loadable artifact
  materialization is unblocked or a lower bridge/native eval profile splits the
  accepted q240 `ane_pre_eval` bucket into selector-2 request/materialization,
  firmware wait, compute completion, and readback without retaining extra
  memory.

## 2026-06-24 exact q240 runtime error payload probe

- Artifact:
  `mps/ANE/.ane_runs/json/exact_q240_runtime_error_payload_probe_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_runtime_error_payload_precondition`.
- IDA recovery:
  cleared orphan IDA workers `96042`, `97076`, and `97079`; reopened
  AppleNeuralEngine as `apple_neural_engine_recovered_20260624` and
  ANECompiler as `ane_compiler_recovered_20260624`.
- IDA facts:
  `-[_ANEInMemoryModel loadWithQoS:options:error:]` saves model files when no
  compiled model exists, builds compiler options with the cached flag, and calls
  `_ANEClient loadModel:options:qos:error:`. `_ANEClient compileModel` and
  `doLoadModel` both dispatch through connection reply blocks that preserve
  `NSError`; `doLoadModel` also gates sandbox-extension behavior on
  `kANEFModelHasCacheURLIdentifierKey`.
- Bridge change:
  `mps/maderix_ANE/bridge/ane_bridge.m` now emits bounded
  `client_file_error_detail` in bridge profile JSON and captures native error
  descriptions without retaining Objective-C error objects. Rebuilt
  `mps/maderix_ANE/bridge/libane_bridge.dylib` successfully.
- Runtime probe:
  reran the minimal transformer-layerwise q240 bridge-env probe, not full audio.
  It failed as expected with `Error Domain=com.apple.appleneuralengine.compiler
  Code=1`, top description `_ANECompiler : ANECCompile() FAILED`, and
  underlying `ANECCompile(...CFEEBA68...F8815657...E3B0C442...) FAILED:
  err=(InvalidMILProgram)`.
- Conclusion:
  exact q240 materializer failure is now localized to `ANECCompile` on the exact
  temp source directory. The failure is not missing cache artifacts or wrapper
  file synthesis. Do not yet claim a permanent dead end; the next missing fact
  is which generated MIL operation/shape violates ANECompiler validation.
- Next target:
  map exact q240 `model.mil` operations/shapes to ANECompiler validation
  surfaces, focusing matmul/softmax/slice/SDPA-related validators and strings,
  to identify the unsupported op/shape or formally prove this exact MIL body is
  a compiler dead end.

## 2026-06-24 exact q240 native materializer precondition probe

- Artifact:
  `mps/ANE/.ane_runs/json/exact_q240_native_materializer_precondition_probe_20260624.json`
  and CSV peer.
- Verdict:
  `inconclusive_need_ida_or_runtime_instrumentation`.
- Method:
  static local evidence only: existing JSON/log artifacts, bridge source
  selectors/options, Mach-O `strings`/`nm`; no ANE compile/eval/full audio run.
- Confirmed facts:
  exact q240 source-only cache forces a native compiler/materializer path;
  wrapper/client-file materialization cannot independently synthesize
  `model.hwx`; `ane_bridge.m` invokes compiler-service
  `compileModelAt:...outputURL:aotModelBinaryPath:...` and expects
  `model.hwx`, `model.src`, and `model.retain` from that output; AppleNeuralEngine
  exports `_ANEClient` compile/load selectors and `_ANEInMemoryModel`
  `loadWithQoS`.
- IDA status:
  `idb_list` still showed prior sessions, but direct `server_health` returned
  session-not-found and fresh `idb_open` attempts failed for existing
  AppleNeuralEngine/ANECompiler binary paths. The delegated `ida` sub-agent
  was closed while still running after two waits, likely blocked on the same
  stale-session issue.
- Conclusion:
  current evidence does not identify the specific native materializer
  precondition or unsupported MIL operation behind exact q240
  `InvalidMILProgram`. Do not claim exact q240 is a dead end yet.
- Next target:
  restore IDA MCP or add a minimal runtime compiler-error instrumentation probe
  around `compileModelAt`, `loadModel`, `compileModel`, and `loadWithQoS` to
  capture selector, options, output/temp/clone paths, and full `NSError`
  domain/code/userInfo for the exact q240 failure.

## 2026-06-24 q240 wrapper/client-file materialization verdict

- Artifact:
  `mps/ANE/.ane_runs/json/q240_wrapper_materialization_static_verdict_20260624.json`
  and CSV peer.
- Verdict:
  `blocked_materialization_requires_successful_compile`.
- Static result:
  checked `32` exact q240 identifier directories for
  `CFEEBA68..._F8815657..._E3B0C442...`; found `0` compiled/loadable
  artifacts (`model.hwx`, wrapper `output/model.hwx`, `model.src`, or
  `model.retain`).
- Alias result:
  found `5` same-weight `model.hwx` examples, but all are under different MIL
  hashes and remain incompatible with exact q240.
- Bridge control-flow result:
  wrapper/client-file materialization can write source-root files
  (`model.mil`, `net.plist`, weights/data), but `model.hwx`, `model.src`, and
  `model.retain` are compiler-service outputs. The wrapper fast path only
  reuses an existing `model.hwx`; `bridge_write_data_if_needed` only copies
  existing compiler output and cannot generate a compiled artifact.
- Conclusion:
  current wrapper/client-file code is not an independent memory-neutral cache
  priming solution for exact integrated q240. Producing loadable fast-load
  artifacts requires a successful native compiler/materializer path for this
  exact MIL+weights pair.
- Next target:
  move one layer lower: recover the native compiler/materializer preconditions
  or failure point for exact q240 `model.hwx` generation, starting from
  `compileModelAt`, `loadModel`, `loadWithQoS`, and existing
  `InvalidMILProgram` evidence.

## 2026-06-24 q240 same-identifier compiled artifact search

- Artifact:
  `mps/ANE/.ane_runs/json/q240_same_identifier_compiled_artifact_search_20260624.json`
  and CSV peer.
- Verdict:
  `blocked_no_known_good_compiled_artifact`.
- Search result:
  found `32` directories for the exact q240 identifier
  `CFEEBA68..._F8815657..._E3B0C442...`, but found `0` `model.hwx`,
  `model.hwx.tmp.additional_weights.bin`, or other `.hwx` files under that
  exact identifier.
- Alias result:
  found compiled `model.hwx` files for same weight hash `F8815657...` under
  different MIL hash `B018EBD3...`, including
  `benchmark_results/private_ane/ane_tmp_loadcache/B018EBD3B31C9EBE76E817901553F402986074B0F1C1B4173831047B8BB9AE91_F88156576125F4F2458BEBCC36F5BEFAB235C4F43F46BA3EAEA629FAD5C6051D_E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855/model.hwx`.
- Conclusion:
  artifact priming for the exact integrated q240 identifier is blocked with
  current artifacts. Same-weight alias `model.hwx` is not reusable because the
  MIL hash differs, meaning the compiled artifact belongs to a different graph.
- Next target:
  move to lower native compile/load artifact materialization: determine whether
  a wrapper/client-file materialization path can produce `model.hwx` for the
  exact q240 identifier without changing the graph or increasing runtime memory.

## 2026-06-24 q240 cache artifact inspector

- Artifact:
  `mps/ANE/.ane_runs/json/integrated_q240_cache_artifact_inspection_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_loadable_artifact_missing`.
- Code added:
  `benchmark/private_ane_cache_artifact_inspector.py`, a plan-only cache
  inspector that checks source files and compiled/loadable bridge artifacts
  without invoking ANE compile or eval.
- Target identifier:
  `CFEEBA68A0867D458FFA754FC3777ECDCE97C7AB6DD42ABE81D759AD310D59C6_F88156576125F4F2458BEBCC36F5BEFAB235C4F43F46BA3EAEA629FAD5C6051D_E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`.
- Result:
  cache status is `source_only`; `model.mil` exists and 7 weight files exist,
  but `model.hwx` and `model.hwx.tmp.additional_weights.bin` are missing.
- Implication:
  the route-only q240 diagnostic failed because the cache was not loadable, not
  because the Python flag path was missing. A true native load-only diagnostic
  needs a compiled/loadable artifact for this identifier before invoking the
  bridge.
- Next target:
  search for a known-good standalone fast-load run that produced a compatible
  compiled `model.hwx` for the same q240 identifier; if none exists, formally
  block artifact priming and move to the lower native compile/load artifact
  materialization question.

## 2026-06-24 integrated q240 route-only diagnostic blocked by source-only cache

- Artifact:
  `mps/ANE/.ane_runs/json/integrated_attention_pre_route_only_q240_compile_blocker_20260624.json`
  and CSV peer.
- Verdict:
  `blocked_route_only_compile_invalid_mil_no_loadable_cache_artifact`.
- Probe:
  ran `benchmark/private_ane_transformer_layerwise_compare.py --compare bridge-env
  --layers 1 --chunks 4 --q-chunk 240 --cache-tmpdir
  benchmark_results/private_ane/ane_tmp_loadcache --probe-handle-scope pre
  --probe-stop-after-axis time --probe-stop-after-layer 1` with
  `ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT=1` and tiled q240 bridge env.
- Result:
  command exited `1`; no output JSON was written. Candidate q240
  `attention_pre` compile failed with `InvalidMILProgram` before route/fallback
  fields could be recorded.
- Cache inspection:
  the matching content-addressed cache directory exists for identifier
  `CFEEBA68A0867D458FFA754FC3777ECDCE97C7AB6DD42ABE81D759AD310D59C6_F88156576125F4F2458BEBCC36F5BEFAB235C4F43F46BA3EAEA629FAD5C6051D_E3B0C44298FC1C149AFBF4C8996FB92427AE41E4649B934CA495991B7852B855`,
  but it contains only `model.mil` plus weights and no `model.hwx` or compiled
  loadable artifact. Therefore the harness cannot force a true load-only
  fast-load hit for this artifact; it falls into compile and hits the known
  q240 `InvalidMILProgram` seam.
- Next target:
  recover a valid load-only route diagnostic by either priming a compiled/loadable
  q240 artifact from a known-good standalone fast-load run into the integrated
  cache identifier, or adding a plan-only cache inspector that checks loadable
  artifact presence before invoking ANE compile.

## 2026-06-24 integrated fast-load route static audit

- Artifact:
  `mps/ANE/.ane_runs/json/integrated_fastload_route_static_audit_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_native_load_only_predicate_is_integrated_fastload_gate`.
- Trigger:
  live memory preflight was still invalid (`15G used`, `3520M wired`,
  `5465M compressor`, only `106M unused`, swap used `2628.38M`), so the
  documented fallback was used instead of launching another full benchmark.
- Static conclusion:
  Python and benchmark flags are not the cause of the integrated
  `fast_load_hit=0`. `private_ane.py` sets `ANE_BRIDGE_LOAD_CACHE=1` and
  `ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT=1`; the benchmark defaults keep
  load-cache, keep-tmpdir, and skip-source enabled. Python only records the
  native `bridge_profile_route`.
- Native bridge gate:
  `mps/maderix_ANE/bridge/ane_bridge.m` assigns
  `load_cache_skip_source_fast_load` only after the early load-only
  `loadWithQoS(... bridge_load_options(..., YES) ...)` succeeds. If that
  direct load-only attempt does not load and source files are complete, the
  bridge falls through to `load_cache_skip_source_write` with
  `fast_load_hit=0`.
- Evidence tie-in:
  prior JSON confirms standalone and integrated q240 MIL bodies are
  byte-identical for the audited shape, while standalone route was
  `load_cache_skip_source_fast_load` (`fast_load_hit=1`, eval
  `0.23802358302054927s`) and accepted integrated route was
  `load_cache_skip_source_write` (`fast_load_hit=0`, eval
  `0.7698414579790551s`).
- Not proven:
  full native-supervised batch-4 speedup, correctness, and memory neutrality
  are still not accepted because no comparable full run can launch under the
  current host memory state.
- Next target:
  create or run a small route-only integrated transformer load-cache diagnostic
  that records the native load-only error/fallback reason for one q240
  `attention_pre` artifact without full audio and without retaining extra
  handles.

## 2026-06-24 integrated fast-load acceptance blocked by memory preconditions

- Artifact:
  `mps/ANE/.ane_runs/json/integrated_fastload_acceptance_blocked_memory_20260624.json`
  and CSV peer.
- Verdict:
  `blocked_invalid_memory_preconditions`.
- Short-term goal:
  run a valid native-supervised batch-4 integrated fast-load-hit acceptance
  probe on `test_clean.m4a`.
- Action:
  no full benchmark was launched. Current live memory was already contaminated:
  `15G used`, `3522M wired`, `4615M compressor`, only `140M unused`, and
  swap used `2676.38M`; `aned` RSS was only `2.671875MB`, so the blocker is
  host memory pressure rather than ANEServices RSS.
- Reason:
  under this state a full native-supervised batch-4 timing would risk native
  supervisor failure, batch-1 downgrade, or memory-contaminated wall time. It
  would not be valid acceptance evidence.
- Skipped command:
  `/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_test_clean_benchmark.py --audio test_clean.m4a --full-audio --baseline none --private-ane-allow-long-audio --private-ane-native-supervisor on --private-ane-native-supervisor-path benchmark/ane_mem_supervisor --private-ane-chunk-batch-size 4 --private-ane-tiled-time-attention-pre --private-ane-tiled-time-attention-pre-q-chunk 240 --private-ane-skip-source-write-on-cache-hit --private-ane-fused-band-split --private-ane-fused-band-split-max-outputs 4 --private-ane-fused-mask-estimator --private-ane-fused-mask-estimator-max-outputs 2 --private-ane-load-cache --private-ane-keep-tmpdir --out benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_integrated_fastload_acceptance_20260624.json`.
- Next target:
  obtain a clean native-supervised batch-4 memory preflight and rerun the exact
  integrated fast-load-hit acceptance command. If the same memory blocker
  repeats again, switch the next loop to an offline/static audit of why the
  integrated path does not hit `load_cache_skip_source_fast_load`.

## 2026-06-24 slow inference root-cause / solution map

- Artifact:
  `mps/ANE/.ane_runs/json/slow_inference_root_cause_solution_map_20260624.json`
  and CSV peer.
- Verdict:
  `blocked_no_memory_neutral_candidate`.
- Best accepted full-path baseline remains:
  `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_20260623.private_ane_child/meta.json`
  with wall `27.903367375023663s`, RTF `0.7048080675165779`,
  transformer `24.631073875003494s`, transformer eval
  `19.743745001906063s`, transformer compile/load
  `1.944708043942228s`, max RSS `1282.671875MB`, and ANEServices max RSS
  `112.421875MB`.
- Root cause by part:
  cold load/compile is mostly solved for the current baseline because the
  bridge profile has `24/24` transformer rows as load-cache hits and `0`
  misses. Remaining slow time is cached segmented execution, not repeated
  compile absence.
- Dominant remaining bottleneck:
  time-axis `attention_pre` has `9.538814419182017s` eval over 12 rows, about
  `48` estimated selector-2 requests, and `2.5199859970016405s` axis packing.
  Freq-axis `attention_pre` has `3.0500712058274075s` eval, about `48`
  estimated selector-2 requests, and `0.8207393719640095s` axis packing.
- Confirmed solution / closure status:
  load-cache and skip-source-write stay as solved baseline pieces; q240 stays
  guarded by shape because forced qchunk routes are not general speedups;
  direct repack, bridge-pack disable, unpadded freq, fused pad-to-64 layout,
  selector-2 gate bypass, and retained handle/surface routes are closed by
  prior wall/RSS/compile/runtime or privilege evidence.
- Reverse-engineering implication:
  the lower accepted-state route is known at the raw send/reply boundary but
  cannot currently be observed safely on this machine because SIP /
  authenticated root / no-KDK conditions block AppleH16ANEInterface FBT or
  kernel-resident state observation. Do not force this path again without a new
  evidence source.
- Next target:
  run a transformer-only per-axis lifecycle attribution probe to split the
  residual cost into ANE eval, write/read transfer, host packing, handle free,
  GC, and outer dispatch gaps. Do not run a full `test_clean.m4a` benchmark for
  this selection step.

## 2026-06-24 transformer lifecycle bucket attribution

- Artifact:
  `mps/ANE/.ane_runs/json/transformer_lifecycle_bucket_attribution_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_next_lifecycle_bucket`.
- Source profile:
  `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_load_cache_bridgeprofile_20260623_profile/transformer_timings.csv`.
- Selection result:
  selected bucket is `time_axis_attention_pre_eval_request_lifecycle`.
- Why selected:
  time-axis `attention_pre` eval/request lifecycle is `9.538814419182017s`,
  larger than total axis packing `3.34072536896565s`, total read/write
  `2.460594660748029s`, total GC/free `1.804850714164786s`, and total outer
  gap `1.2444323258532677s`.
- Non-selected buckets:
  time-axis axis pack remains the secondary bucket at `2.5199859970016405s`;
  read/write, GC/free, and outer gaps are measurable but lower priority.
- Next target:
  probe one representative time-axis `attention_pre` layer to separate ANE
  compute body from selector-2 request/materialization and host setup. Do not
  use retained handles/surfaces or a full audio run for this probe.

## 2026-06-24 time-axis attention_pre layer-0 lifecycle probe

- Artifact:
  `mps/ANE/.ane_runs/json/time_attention_pre_layer0_lifecycle_probe_20260624.json`
  and CSV peer.
- Verdict:
  `inconclusive_need_lower_runtime_access`.
- Commands:
  standalone `attention_pre_tiled` micro-profile failed ANE compile with
  `InvalidMILProgram`; standalone sub-stage micro-profile failed at `rms_qkv`
  with `InvalidMILProgram`; integrated transformer layer-0 compare completed
  and wrote
  `benchmark_results/private_ane/time_attention_pre_layer0_lifecycle_integrated_20260624.json`.
- Accepted hot-path row:
  from
  `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_20260623.private_ane_child/meta.json`,
  time layer 0 q240/load-cache-skip-source has segment wall
  `1.0697753750137053s`, compile/load `0.037306624988559633s`, eval
  `0.9883378339873161s`, `ane_pre_total_sec=0.8071342080074828s`, and
  `ane_pre_eval_sec=0.7698414579790551s`.
- Host setup result:
  time layer 0 `ane_pre_write_sec=0.01106487397919409s`,
  `ane_pre_read_sec=0.026174624013947323s`, `axis_pack_sec=0.05874783397302963s`,
  `handle_free_sec=0.012474084040150046s`, and
  `gc_sec=0.031519042007857934s`. These are not dominant relative to
  `ane_pre_eval_sec`.
- Integrated compare caveat:
  q240 was exact (`max_abs=0`) but the compare is cold compile/load
  contaminated: q240 wall increased by `2.3996788329677656s` and max RSS by
  `227.25MB`. Do not use it as a speed verdict for the accepted hot path.
- Next target:
  instrument or reverse-map the bridge eval call itself for one time-axis
  `attention_pre` request. Required split is selector-2 request/materialization,
  ANEServices submit, firmware wait/completion, and readback completion. Do not
  force accepted-state replay or retain extra memory.

## 2026-06-24 bridge eval path attribution

- Artifact:
  `mps/ANE/.ane_runs/json/bridge_eval_path_attribution_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_firmware_wait_or_compute_dominant`.
- Source evidence:
  existing `run_packed2_profiled` / `run_multi_inputs_profiled` already split
  cast, alloc, write, eval, read, and total. The runner records these as
  `ane_pre_*`, `ane_gate_*`, `ane_ffn_*`, `ane_eval_only_sec`,
  `ane_write_sec`, and `ane_read_sec`.
- Native bridge evidence:
  `mps/maderix_ANE/bridge/ane_bridge.m` has detailed compile/load profile
  fields through `ANEBridgeProfile`, but `ane_bridge_eval` is a monolithic
  blocking call through `evaluateWithModel`, `processRequest`, or
  `evaluateWithQoS`. The exported C API has coarse `ane_bridge_eval`,
  `ane_bridge_write_input`, and `ane_bridge_read_output`, but no submit/wait
  split.
- IDA evidence:
  ANEServices eval submit is `ANE_ProgramSendRequest` selector 2 via
  `IOConnectCallAsyncMethod` with a `0x948` request struct and async wake
  port/callback. User-space ANEServices signposts end after IOConnect return
  and do not span compute. The dominant gap is between selector-2 submit return
  and async completion.
- Attribution:
  request materialization and IOConnect submit are not credible explanations
  for the observed `0.7698414579790551s` accepted hot-path layer-0
  `ane_pre_eval_sec`. The remaining bucket is firmware wait/compute plus
  kernel completion dispatch.
- Next target:
  estimate achieved FLOPS/throughput for the accepted time-axis
  `attention_pre` hot path and decide whether the dominant bucket is
  low-utilization compute-body work or requires lower firmware/kernel timing.
  Do not increase memory.

## 2026-06-24 attention_pre throughput roofline

- Artifact:
  `mps/ANE/.ane_runs/json/attention_pre_throughput_roofline_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_low_utilization_compute_body`.
- Formula source:
  `benchmark/private_ane_attention_pre_micro_profile.py::_stage_flops`.
  Per layer, `rms_qkv = 3 * 2 * batch * seq * dim * inner`,
  `rope = 12 * batch * heads * seq * (head_dim / 2)`, and
  `sdpa = 4 * batch * heads * seq * seq * head_dim`.
- Shape:
  time-axis `batch=62`, `seq=960`, `heads=8`, `head_dim=64`, `dim=256`,
  `inner=512`.
- Per-layer FLOPs:
  `attention_pre_total=164012359680` FLOPs, with SDPA share
  `71.34894091415831%`, qkv share `28.53957636566332%`, and rope share
  `0.11148272017837235%`.
- Accepted hot-path throughput:
  time layer0 q240 `ane_pre_eval_sec=0.7698414579790551s` gives
  `0.21304693061160423 TFLOPS` / `1.1669967715359566%` of measured local ANE
  FP16 peak. Across all 12 time-axis layers, `ane_pre_eval_sec=9.493088960007299s`
  gives `0.20732433083177246 TFLOPS` / `1.1356503660811375%`.
- Interpretation:
  this is far below the measured local ANE FP16 peak `18.256 TFLOPS`. The
  number is effective utilization, not pure GEMM efficiency, because softmax,
  slice/transpose/layout, scheduler, and firmware completion costs are not
  represented as peak FLOPs.
- Next target:
  compare accepted integrated time-axis `attention_pre` MIL/body against prior
  faster standalone q240 evidence and current integrated q240 layer0 rows to
  identify one memory-neutral MIL/body/layout candidate, or prove lower
  firmware timing is required.

## 2026-06-24 integrated vs standalone attention_pre q240

- Artifact:
  `mps/ANE/.ane_runs/json/integrated_vs_standalone_attention_pre_q240_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_memory_neutral_body_candidate`.
- MIL/body result:
  standalone micro-profile q240 and integrated transformer q240 generate
  byte-identical MIL for `batch=62`, `seq=960`, `valid_seq=938`,
  `q_chunk=240`: SHA-256
  `cfeeba68a0867d458ffa754fc3777ecdce97c7ab6dd42abe81d759ad310d59c6`,
  with `8` matmuls, `4` softmaxes, and `8` `slice_by_index` ops.
- Timing contrast:
  standalone b62 q240 has `eval_sec=0.23802358302054927s`,
  `total_sec=0.26003245799802244s`, and `0.689059283952718 TFLOPS`.
  Accepted integrated time layer0 q240 has
  `ane_pre_eval_sec=0.7698414579790551s`,
  `ane_pre_total_sec=0.8071342080074828s`, and
  `0.21304693061160423 TFLOPS`.
- Concrete route difference:
  standalone hit `load_cache_skip_source_fast_load` with `fast_load_hit=1`.
  Accepted integrated layer0 used `load_cache_skip_source_write` with
  `fast_load_hit=0`, despite `fast_load_attempted=2`.
- Candidate:
  restore or validate integrated transformer fast-load-hit behavior under
  native-supervised batch-4 conditions. This is memory-neutral in principle
  because it changes the bridge route, not retained handles/surfaces/buffers,
  but it is accepted only if RSS/wired/swap do not regress.
- Caveat:
  `benchmark_results/private_ane/time_attention_pre_layer0_lifecycle_integrated_20260624.json`
  is useful for exactness but is cold compile/load contaminated
  (`load_cache=false`) and is not a speed acceptance result.
- Next target:
  run a valid native-supervised batch-4 integrated fast-load-hit acceptance
  probe on `test_clean.m4a`, or output an exact blocker if memory/preconditions
  are invalid.

## 2026-06-24 firmware reply runtime observation feasibility

- Artifact:
  `mps/ANE/.ane_runs/json/firmware_reply_runtime_observation_feasibility_20260624.json`
  and CSV peer.
- Verdict:
  `blocked_need_privileged_runtime_access`.
- Feasibility result:
  the lower observation seam is known, but the current machine cannot safely
  observe the required AppleH16ANEInterface kernel call sites or
  kernel-resident state under current permissions/tooling. `dtrace` needs root
  for trivial probes, and even root FBT matching for
  `com.apple.driver.AppleH16ANEInterface` fails because SIP is enabled.
- Current machine constraints:
  SIP and authenticated root are enabled; `kern.development=0`; `boot-args` is
  empty; `/Library/Developer/KDKs`, `/dev/kmem`, and `/dev/mem` are absent.
  `AppleH16ANEInterface` is loaded at `0xfffffe000743d780`, matching the IDA
  base, but loaded does not mean observable.
- User-space instrumentation limit:
  Frida can observe user-space ANEServices wrapper timing and process presence,
  but existing IOKit selector-2 hook evidence is blocked by PAC/non-exported
  targets and does not expose kernel `record+0x1b8`, scalar
  `process+0x203fc`, command-state `+0x58/+0x68/+0x88`, or
  `handleOutstandingCommand` internals.
- Unified logging limit:
  the AppleH16ANEInterface logging mode is visible, but recent logs do not
  expose command/output pointers, accepted-state fields, or response copyback
  state.
- Decision:
  do not force or synthesize accepted-state from this layer under current
  tooling. Treat the lower route as blocked unless SIP/KDK/kernel-debug
  conditions change. Continue acceleration from memory-neutral higher-level
  `attention_pre` / request-count reduction.

## 2026-06-24 firmware reply accepted-state observation requirements

- Artifact:
  `mps/ANE/.ane_runs/json/firmware_reply_accepted_state_observation_requirements_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_minimal_firmware_reply_observation_plan`.
- Lower boundary now named:
  both raw send wrappers converge on
  `ANEHWDevice::aneFirmwareCommandSend` (`0xfffffe00092c80c4`), which sends
  through `IOProcessorChannelSendRetry` at `0xfffffe00092c8a18`. Synchronous
  response handling reaches `ANEHWDevice::handleOutstandingCommand` at
  `0xfffffe00092c8dbc`; asynchronous response handling reaches the same
  handler via `processCommandResponse` at `0xfffffe00092c3cb0`.
- Key wrapper facts:
  `ANEHWDevice::aneCmdSend(void*,...)` (`0xfffffe00092bd638`) packages command
  pointer/size and output pointer/size into an `ANEFirmwareCommand` and calls
  `aneFirmwareCommandSend` at `0xfffffe00092bd6f4`. The typed
  `ANEHWDevice::aneCmdSend(ANEFirmwareCommand const&)`
  (`0xfffffe00092c93b0`) sends asynchronously and then sleeps on completion.
  `ANEFirmwareManager::sendInferenceCmd` (`0xfffffe00092bd930`) builds a
  pending request/property buffer, writes property DVA/size, and calls raw
  `aneCmdSend` at `0xfffffe00092bdc1c`.
- Minimal observation targets:
  `ProgramLoad` raw send at `0xfffffe0009281904`, restore raw send at
  `0xfffffe00092c1d60`, process-create raw send at `0xfffffe000927f444`,
  `SendRequestToFirmware_gated` raw sends at `0xfffffe0009291ac0`,
  `0xfffffe0009291e5c`, `0xfffffe0009292374`, selector-2 submit sends at
  `0xfffffe000929c4d4` / `0xfffffe000929cd98`, and RT inference
  `sendInferenceCmd` at `0xfffffe00093111a4`.
- Required runtime evidence before any exploit attempt:
  snapshot command/output pointers and bounded response memory before/after one
  raw send; snapshot `record+0x1b8` around ProgramLoad/RestoreState; snapshot
  scalar `process+0x203fc` before raw send, after return, before
  `isProcessValid(mode=1)`, and after `handleOutstandingCommand`; observe
  command-state `+0x58` status, `+0x68` device address, callback/copyback
  state, and outstanding-command removal.
- Memory constraint:
  the observation probe must be one-shot and bounded. It must not retain extra
  transformer handles, buffers, IOSurfaces, response snapshots, or other
  long-lived memory.
- Root-cause implication:
  static evidence is now sufficient to define the lower observation seam, but
  not sufficient to synthesize accepted-state. If this runtime observation is
  not feasible under local permissions/tooling, the lower route should be
  formally blocked and work should return to higher-level `attention_pre` /
  request-count reduction.

## 2026-06-24 visible bridge record/resource/gate to process-state probe

- Artifact:
  `mps/ANE/.ane_runs/json/visible_bridge_record_to_process_state_probe_20260624.json`
  and CSV peer.
- Verdict:
  `falsified_visible_bridge_hidden_writer_below_raw_send`.
- Confirmed visible bridges that stop before process state:
  `ANEHWDevice::ProgramLoad` (`0xfffffe00092812c4`) reads a `0x1c0`-stride
  `record+0x1b8` at `0xfffffe000928198c` and stores it into `gate+0x220` at
  `0xfffffe0009281990`. `ANEHWDevice::ANE_RestoreState`
  (`0xfffffe00092c1b38`) reads `record+0x1b8` at `0xfffffe00092c1d78` and
  stores it into `resource+0x402f0` at `0xfffffe00092c1d7c`.
- Classified `process+0x203fc` scalar writers:
  `ANEProcess::init` zero-initializes the region; `ANE_ProcessCreate_gated`
  clears it with `STR WZR` at `0xfffffe000927f5d4`;
  `ANE_ProgramCreateInstance_gated` writes immediate `1` at
  `0xfffffe000928d908`; `ANE_RestoreState.cold.2` writes immediate `1` at
  `0xfffffe000937654c`; `ProcessAbort` writes immediate `2` at
  `0xfffffe000927ea20`.
- Important nuance:
  the visible value-`2` writer is real but abort-local: `ProcessAbort` executes
  `MOV W8, #2` at `0xfffffe000927ea1c` then `STR W8, [X28,#0x3FC]` at
  `0xfffffe000927ea20`. It is not sourced from `record+0x1b8`,
  `gate+0x220`, or `resource+0x402f0`, so it is not a normal-path replay or
  single-process reuse bridge.
- Classified non-scalar `base+0x3fc` sites:
  selector-2 submit (`0xfffffe000929aad4`, `0xfffffe000929aebc`) and RT send
  (`0xfffffe000930f1c0`, `0xfffffe000930f584`) perform indexed writes
  `STR W9, [X8,W11,UXTW#2]` after adding `0x3fc`; these are per-entry array
  writes, not scalar `process+0x203fc` accepted-state publication.
- `process+0x20400` / sibling state:
  observed references are initialization, sibling-state consumption, or
  `process+0x20404` writes. No bridge into scalar `process+0x203fc` was found
  from this family.
- Root-cause implication:
  the selected lower accepted-state family has no visible H16 CPU-side bridge
  from restore/gate/resource copyback into the scalar accepted-state consumed
  by `isProcessValid`. The remaining memory-neutral route is now below raw
  `aneCmdSend` firmware reply semantics, privileged runtime observation, or a
  different higher-level route that reduces `attention_pre` / request count
  without retaining extra handles, buffers, or surfaces.
- Next target:
  produce a lower-boundary blocker/requirements package for firmware reply
  accepted-state observation, including the minimal runtime evidence needed to
  continue safely without increasing memory.

## 2026-06-24 lower completion state author/consumer probe

- Artifact:
  `mps/ANE/.ane_runs/json/lower_completion_state_author_consumer_probe_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_lower_state_author_or_consumer`.
- Confirmed consumer:
  `ANEHWDevice::isProcessValid` (`0xfffffe000927d410`) computes
  `process+0x203fc` with `ADD X8, X21, #0x20,LSL#12` and
  `ADD X25, X8, #0x3FC`, reads it at `0xfffffe000927d530`, and compares it
  against `2` at `0xfffffe000927d538`. In mode 1, accepted process validation
  depends on `process+0x203fc == 2`.
- Confirmed completion-side consumer path:
  `ANEHWDevice::handleRequestCompletion` (`0xfffffe000927c900`) calls
  `isProcessValid` with `W4=1` at `0xfffffe000927c978`, then dispatches
  through device vtable `+0x9c0` at `0xfffffe000927c990`-`0xfffffe000927c9b0`.
  This falsifies the narrow "completion family is bookkeeping-only" model.
- Confirmed restore replay/copyback:
  `ANEHWDevice::ANE_RestoreState` (`0xfffffe00092c1b38`) calls raw
  `ANEHWDevice::aneCmdSend` at `0xfffffe00092c1d60`, then reads
  `record+0x1b8` from a `0x1c0`-stride record at `0xfffffe00092c1d78` and
  stores it into `resource+0x402f0` at `0xfffffe00092c1d7c`.
- Not found:
  no direct completion-side writer for `process+0x203fc`, no visible CPU-side
  exact writer for `record+0x1b8`, and no safe memory-neutral replay/reset
  control.
- Root-cause implication:
  the remaining transformer slowdown is now tied to a lower accepted-state
  lifecycle surface. Segmented selector work repeatedly reaches validation /
  copyback paths whose authoring boundary is below raw firmware send; current
  host-visible code cannot safely synthesize this state.
- Next target:
  determine whether `resource+0x402f0` / `gate+0x220` / `process+0x203fc` are
  bridged by a visible H16 CPU-side path after restore/completion, or whether
  the hidden writer must be declared firmware reply semantics / privileged
  runtime observation boundary.

## 2026-06-24 next lower target selection

- Artifact:
  `mps/ANE/.ane_runs/json/next_lower_target_selection_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_next_lower_target`.
- Selected target:
  lower reply-publish/completion side effects, concretely
  device vtable `+0x9c0` -> `ANEHWDevice::isProcessValid` /
  `process+0x203fc` family, compared against restore-side `record+0x1b8`
  replay after raw firmware send.
- Why it is lower than the exhausted layer:
  the prior blocker ended at
  `ProgramReMap` / `dartMapResources` / `createANESurface`. The selected
  target is driven by post-send completion/lifecycle state and raw
  firmware-send replay evidence; it decides whether a process is accepted by
  consuming `process+0x203fc`, rather than constructing host-visible
  descriptors or IOSurfaces.
- IDA confirmation:
  active H16 session `apple_h16_ane_interface_20260624` resolves
  `0xfffffe000927d410` to `ANEHWDevice::isProcessValid`. The function validates
  program/process membership and, when mode is nonzero, tests
  `process+0x203fc == 2` before accepting the process.
- Completion-side evidence:
  `ANEHWDevice::handleRequestCompletion` (`0xfffffe000927c900`) calls
  `isProcessValid` at `0xfffffe000927c978` and dispatches through device
  vtable `+0x9c0` at `0xfffffe000927c990`-`0xfffffe000927c9b0`.
- Restore-side replay evidence:
  prior artifact
  `mps/ANE/.ane_runs/json/process203fc_state2_first_lower_surface_record1b8_verdict_20260619.json`
  says `record+0x1b8` has no visible CPU-side exact writer; active H16 IDA
  confirms `ANE_RestoreState` calls raw `ANEHWDevice::aneCmdSend` at
  `0xfffffe00092c1d60`, followed by restored record-state use around
  `0xfffffe00092c1d78`.
- Not a speedup yet:
  this selects the next reverse-engineering target only. It does not prove a
  memory-neutral acceleration route, does not authorize retaining extra
  handles/surfaces, and does not change inference code.
- Next target:
  statically probe this selected completion/accepted-state family for reads or
  writes of `record+0x1b8`, `process+0x203fc`, `process+0x20400`,
  `gate+0x220`, and `resource+0x402f0`.

## 2026-06-24 current layer exhausted blocker

- Artifact:
  `mps/ANE/.ane_runs/json/current_layer_exhausted_blocker_20260624.json`
  and CSV peer.
- Verdict:
  `falsified_current_layer_exhausted`.
- Dead-end control layer:
  current host-visible private ANE graph/layout/runtime layer plus H16
  selector-2/3/8 driver materializer layer through
  `ProgramReMap` / `dartMapResources` / `createANESurface`.
- Not proven dead:
  ANE firmware/internal scheduler/accepted-state implementation below
  `ProgramReMap` / `dartMapResources` / `createANESurface` was not directly
  observed and is not proven exhausted.
- Current best full-path evidence:
  `test_clean.m4a` best observed wall remains `27.903367375023663s`
  (`RTF=0.7048080675165779`) from
  `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_20260623.private_ane_child/meta.json`.
  This satisfies the prior under-30s wall target but does not prove proximity
  to ANE theoretical peak because transformer eval remains segmented and
  dominated by time-axis `attention_pre` request/materialization overhead.
- Current root-cause split:
  `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_load_cache_bridgeprofile_20260623_profile/transformer_timings.csv`
  has `24/24` load-cache-hit transformer rows and `0` load-cache misses.
  Time-axis rows contribute `14.225222417007899s` eval,
  `9.538814419182017s` `attention_pre` eval, and
  `2.5199859970016405s` axis-pack. Freq-axis rows contribute
  `5.89854916598415s` eval, `3.0500712058274075s` `attention_pre` eval, and
  `0.8207393719640095s` axis-pack.
- Closed routes tied into the blocker:
  existing load-cache already solved cold load/compile absence; cache-hit
  tmpdir/source regression was fixed; q240 is shape-guarded but not a general
  request-count solution; host-visible request-count/axis-pack audit found no
  memory-neutral candidate; fused time/freq pad-to-64 layout failed
  `InvalidMILProgram`; unpadded/direct freq route regressed full-path wall/RSS;
  selector-2 update gate cannot be safely observed/bypassed with current
  tooling; selector-8 `needProgramRemap` / `ProgramReMap` and
  `createANESurface` expose required correctness/materializer paths, not a
  proven speed lever.
- Solution implication:
  do not repeat host-visible qchunk/layout/repack/selector-2/selector-8
  probes without a new lower target. Further speed movement toward ANE peak
  requires one genuinely lower evidence source below
  `ProgramReMap` / `dartMapResources` / `createANESurface`, or the lower
  control-layer requirement must be formalized as the dead-end boundary.

## 2026-06-24 selector-3/8 create-instance materializer audit

- Artifact:
  `mps/ANE/.ane_runs/json/selector3_8_create_instance_materializer_audit_20260624.json`
  and CSV peer.
- Verdict:
  `inconclusive_current_layer_materializer_control_not_found`.
- IDA sessions:
  `apple_h16_ane_interface_20260624` for H16 lower driver evidence and
  `ane_services_dyld_20260623` for user-space wrapper context.
- Confirmed lower paths:
  `ANEHWDevice::ANE_ProgramCreateInstance_gated`
  (`0xfffffe000928c5ec`) calls
  `ANEProgramResource::needProgramRemap(uint)` at `0xfffffe000928cf48`.
  If remap is needed, it logs `Program not mapped in DART, remapping` at
  `0xfffffe000928cff4` and calls
  `ANEProgramResource::ProgramReMap` at `0xfffffe000928d048`.
- `needProgramRemap` semantics:
  `ANEProgramResource::needProgramRemap(uint)` (`0xfffffe0009305508`)
  checks whether required per-residency resource mapping slots are populated
  across program/resource arrays. This is a mapped-state readiness predicate,
  not an exposed user-space policy knob.
- `ProgramReMap` semantics:
  `ANEProgramResource::ProgramReMap` (`0xfffffe00093056bc`) waits for pending
  update, sets pending update, wires resources, calls `dartMapResources` when
  not `onlyWire`, recomputes DVA-derived offsets, clears pending update, and
  logs explicit `wireResources` / `dartMapResources` failures. It is shared by
  create-instance, send-request checks, client hints, and chaining prepare,
  which argues against bypassing it as a transformer-local speed knob.
- Surface materializer semantics:
  `ANEResource::create<(ANEResourceType)2>` (`0xfffffe0009318744`) rounds the
  requested size to device alignment (`ANEHWDevice + 0x3618`), reads usage and
  flags from `ANEResourceCreationParams`, then calls
  `ANEHWDevice::createANESurface` (`0xfffffe0009318970`). Direct callers of
  `createANESurface` are shared-memory allocation, firmware-heap allocation,
  and `ANEResource::create<2>`, with IOSurface strings confirming concrete
  `IOSurfaceWidth` / `IOSurfaceHeight` / `IOSurfaceBytesPerRow` /
  `IOSurfaceAllocSize` materialization.
- Solution implication:
  do not implement selector-8 remap bypass, forced `needProgramRemap=false`,
  or IOSurface contract override from current evidence. These are required
  mapping/materializer correctness paths, and no memory-neutral reusable
  accepted-state control was identified at this layer.
- Next target:
  move from `Control` toward `ExploitOrBlock`: package the current
  host-visible layout/surface/materializer boundary as exhausted, or identify
  a genuinely lower target that can prove single-process accepted-state
  replay/reset/rebuild without retained memory growth.

## 2026-06-24 fused time/freq layout compile probe

- Artifact:
  `mps/ANE/.ane_runs/json/fused_time_freq_layout_compile_probe_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_partial_layout_primitive_compile_padded_contract_blocked`.
- What compiled:
  a pure ANE-side transpose from time-axis layout
  `[62,256,1,960] -> [960,256,1,62]` compiled in `0.152650167s`.
  Transpose plus valid-time crop
  `[62,256,1,960] -> [938,256,1,62]` compiled in `0.105786125s`.
- What failed:
  the current padded freq contract formulation
  `[62,256,1,960] -> [938,256,1,64]`, implemented as
  transpose + crop + zero-pad concat, failed compile with
  `InvalidMILProgram`.
- Solution implication:
  this refreshes earlier 2026-06-23 compile evidence: the compiler does not
  reject transpose/crop itself, but the current host-visible runtime surface
  still requires padded input/output allocation for freq eval. Later full-path
  evidence already falsified unpadded freq padded-surface promotion:
  transformer-only was exact/slightly faster, but full-path `test_clean.m4a`
  was slower and max child RSS rose. Do not repeat the unpadded/direct repack
  route without a new lower surface/materializer contract.

## 2026-06-24 time attention_pre request/axis-pack audit

- Artifact:
  `mps/ANE/.ane_runs/json/time_attention_pre_request_axis_pack_audit_20260624.json`
  and CSV peer.
- Verdict:
  `falsified_no_memory_neutral_candidate`.
- Measured root cause:
  current batch-4 profile has `24/24` transformer rows as load-cache hits, so
  residual slow speed is not primarily cold compile/load. Time-axis
  `attention_pre` still accounts for `9.538814419s` eval, and time-axis
  host layout packing adds `2.519985997s`. The current request model estimates
  `48` time-axis `attention_pre` selector-2 requests and `96` total
  `attention_pre` selector-2 requests across time+freq.
- Code-level boundary:
  `pymss/modules/bs_roformer/private_ane.py` still executes layerwise time and
  freq axis families separately: `_attention_pre_mil_for_axis` only swaps the
  per-axis pre MIL body, `_run_time_axis_many_with_handles` and
  `_run_freq_axis_many_with_handles` each perform host pack/run/unpack, and
  `run_transformers_layerwise_many` iterates per-layer axis segments.
- Closed candidates:
  forced q240 beyond the guard, `bridge_pack_gate=0`, direct time-to-freq
  repack, surface/unpadded handoff, batch-axis promotion, and H16-visible
  `updateRequestFWCommand` gate bypass do not provide a promotable
  memory-neutral speedup.
- Solution implication:
  current host-visible knobs are exhausted for this sub-problem. The next
  control-layer requirement is a fused time+freq MIL/layout contract, an
  ANE-side transpose/repack primitive, or explicit `InvalidMILProgram` evidence
  proving this class is rejected by ANECompiler.

## 2026-06-24 selector-2 update gate runtime observation feasibility

- Artifact:
  `mps/ANE/.ane_runs/json/selector2_update_gate_runtime_observation_feasibility_20260624.json`
  and CSV peer.
- Verdict:
  `inconclusive_observation_unavailable_current_safe_tooling`.
- Confirmed limitation:
  current safe tooling cannot count the `updateRequestFWCommand` gate branch at
  `0xfffffe00092914a8` for time-axis `attention_pre`. Bridge and micro-profile
  timing expose only outer `eval_sec` / read-write totals. ANEServices Frida
  timing reaches only outer user-space selector-2 wrappers. IOConnect/Frida
  callsite attempts did not capture lower timing, PAC-signed import slots caused
  attach failures, and DTrace/system tracing is unavailable in this session.
- What remains true:
  static IDA already resolves the gate as `ANERequest + 0x3150` and identifies
  remap/resource-dirty writers, but it cannot quantify branch frequency.
- Solution implication:
  do not spend another loop force-clearing `ANERequest + 0x3150`, bypassing
  `updateRequestFWCommand`, or repeating the same IOConnect/Frida hook path.
  Under current constraints, speed progress should come from reducing repeated
  time-axis `attention_pre` selector-2 invocations, axis-pack overhead, or other
  memory-neutral graph/layout factors.
- Next target:
  perform a request-count and axis-pack reduction audit for time-axis
  `attention_pre`: enumerate current segment/request counts, axis-pack cost,
  layer/axis distribution, and identify one candidate that reduces selector-2
  invocations or packing without increasing RSS/wired/swap.

## 2026-06-24 selector-2 updateRequestFWCommand gate source

- Artifact:
  `mps/ANE/.ane_runs/json/selector2_update_fw_command_gate_source_20260624.json`
  and CSV peer.
- Verdict:
  `inconclusive_rewrite_gate_source_resolved_attention_pre_force_not_proven`.
- Confirmed field:
  `SendRequestToFirmware_gated` derives `var_170 = ANERequest + 0x3139` at
  `0xfffffe0009290afc-0xfffffe0009290b08`, then tests
  `[var_170 + 0x17]` at `0xfffffe00092914a4`; the gate byte is therefore
  `ANERequest + 0x3150`.
- Confirmed writers:
  `ProcessReMap.cold.1` writes `1` to `ANERequest + 0x3150` at
  `0xfffffe00093759a8` after checking `request + 0x189c`. 
  `ANEUnionResource::markPendingRequestsToBeUpdated.cold.2` writes the same
  byte at `0xfffffe0009376a78` after iterating pending requests and checking
  `request + 0x189c`.
- Meaning:
  the update gate is a lower remap/resource-DVA dirty bit, not a qchunk policy
  or top-level Python state. It is fed by process remap and union-resource
  pending-update propagation, including memory descriptor update and DART unmap
  callers.
- What remains unproven:
  static IDA does not prove that time-axis `attention_pre` always reaches
  `0xfffffe00092914a8` with bit 0 set. Current user-space timing still collapses
  this whole H16 path into opaque `eval_sec`.
- Solution implication:
  do not force-clear `ANERequest + 0x3150` or skip `updateRequestFWCommand`.
  The next useful probe is either safe runtime branch-frequency observation at
  `0xfffffe00092914a8`, or memory-neutral request-count/axis-pack reduction if
  branch observation remains unavailable.

## 2026-06-24 selector-2 updateRequestFWCommand DVA attribution

- Artifact:
  `mps/ANE/.ane_runs/json/selector2_update_fw_command_dva_attribution_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_update_fw_command_is_per_request_dva_rewrite_no_standalone_memory_neutral_bypass_found`.
- Confirmed root-cause contribution:
  `ANEHWDevice::updateRequestFWCommand(ANERequest *)` at
  `0xfffffe00092929a0` is a real lower selector-2 materialization class. Its
  only code xref is `SendRequestToFirmware_gated+0x158c` at
  `0xfffffe00092914b4`; it receives the current `ANERequest`, is guarded by a
  request flag at `0xfffffe00092914a8`, and failure aborts the send path at
  `0xfffffe00092914b8`.
- DVA evidence:
  the function reads request-owned program/process pointers from `[X1,#0x28]`,
  loads a request-local firmware/mutable command area from `[X1,#0x1890]`,
  writes request-derived fields into the command area, requires mutable memory
  to be DART-mapped, and logs explicit proc mutable DVA changes
  (`updated proc mutable dva address from 0x%llx to 0x%llx`).
- Solution implication:
  do not patch out `updateRequestFWCommand` or blindly cache its output. The
  static slice supports the root-cause model that remaining transformer eval
  time is lower selector-2 request/materialization work, but it does not expose
  a standalone memory-neutral bypass. Any safe reduction must prove unchanged
  request mapping/command state, reduce request count/axis-pack, or time the
  stage dynamically with a safe PAC-aware hook/signpost.
- Next target:
  identify the request flag / unchanged-DVA gate feeding
  `SendRequestToFirmware_gated+0x1580` (`[X8,#0x17]`) and determine whether
  repeated time-axis `attention_pre` requests always force the rewrite, or
  whether a memory-neutral coalescing/axis-pack route can keep it clear.
- Caveat:
  this loop produced static IDA evidence only. It did not quantify this
  substage's wall-time share because current user-space timing still collapses
  the H16 lower path into opaque `eval_sec`.

## 2026-06-24 attention_pre q240 shape guard

- Artifact:
  `mps/ANE/.ane_runs/json/attention_pre_q240_shape_guard_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_memory_neutral_q240_shape_guard_added_and_verified`.
- Code change:
  `pymss/modules/bs_roformer/private_ane.py` now has a shape-aware q240
  decision for time-axis `attention_pre`. Actual tiled MIL generation requires
  the existing q240 opt-in, time axis, layer `0`, `seq == TIME_PAD`, and
  `batch >= FREQ_SEQ` (`62`) unless
  `PYMSS_PRIVATE_ANE_FORCE_TILED_TIME_ATTENTION_PRE_SMALL_SHAPES=1` is set for
  explicit diagnostics.
- Verification:
  `py_compile` passed. Shape assertions passed for static layer-0 opt-in,
  `batch=4` guarded off, `batch=62` guarded on, freq-axis off, layer-1 off,
  and the explicit small-shape override.
- Impact:
  this is memory-neutral because it only selects MIL text; it does not retain
  handles, buffers, or surfaces. It prevents the measured `batch=4` q240 loss
  while preserving the representative `batch=62` q240 win.
- Remaining gate:
  no full-audio speed or correctness acceptance was run. Full-path promotion
  still requires native supervisor enabled, `chunk_batch_size=4`, no memory
  growth, wall near or below `30s`, and correctness validation.

## 2026-06-24 attention_pre q240 shape-policy probe

- Artifact:
  `mps/ANE/.ane_runs/json/attention_pre_q240_shape_policy_probe_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_q240_shape_dependent_large_attention_pre_win_small_segment_loss`.
- Probe scope:
  time-axis `attention_pre`, `seq=960`, `valid_seq=938`, patched bridge
  fast-load path active via `ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT=1`,
  load-cache enabled, no full-path acceptance claim.
- Small-segment result:
  at `batch=4`, q240 is worse than default: eval `+31.967592902216285%`,
  total `+100.07498110427656%`. Tiling/read overhead dominates, so q240 must
  not be used for small low-memory segments.
- Representative large-segment result:
  at `batch=62`, q240 is faster than default: eval `-8.129995525295493%`,
  total `-9.656408704901695%`; eval throughput improves from
  `0.6330387950007289` to `0.689059283952718` TFLOPS.
- Remaining gap:
  even q240 large-segment eval TFLOPS is far below measured ANE FP16 peak, so
  the next root-cause target remains lower selector-2 materialization/dispatch
  or request-count/layout reduction, not another blind q-chunk sweep.
- Caveat:
  batch-62 probes used `repeats=1`, `warmup=0` because host memory is low.
  This is directional per-segment policy evidence, not full-path promotion or
  correctness validation.

## 2026-06-24 low-memory batch-1 transformer multiplication

- Artifact:
  `mps/ANE/.ane_runs/json/low_memory_batch1_transformer_multiplication_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_low_memory_batch1_multiplies_transformer_segments_bridge_tmpdir_not_remaining_wall_cause`.
- Root cause for the patched `59s` diagnostic:
  the run is non-comparable because host memory forced `chunk_batch_size=1`.
  `transformer_timing_count` increased to `96`, exactly `4x` the prior batch-4
  control, with `48` time-axis and `48` freq-axis transformer segments instead
  of `12`/`12`.
- Bridge fix status:
  the bridge tmpdir regression is not the remaining wall-time cause. Patched
  time+freq bridge tmpdir is about `0.035476582s`, versus
  `5.9165631659999995s` in the current unpatched control.
- Remaining non-comparable cost:
  the low-memory diagnostic is dominated by multiplied transformer eval,
  `attention_pre` eval/materialization, `axis_pack`, and repeated `load_qos`
  across the increased segment count. This is a host batching/precondition
  effect and must not be interpreted as ANE full-path regression.
- Next implication:
  until valid batch-4 memory headroom returns, continue only narrow per-segment
  probes for time-axis `attention_pre` eval/materialization or axis-pack
  reduction; do not claim full-path speed acceptance.

## 2026-06-24 batch-4 native-supervisor precondition check

- Artifact:
  `mps/ANE/.ane_runs/json/batch4_native_supervisor_precondition_check_20260624.json`
  and CSV peer.
- Verdict:
  `inconclusive_full_acceptance_batch4_precondition_failed_low_free_memory`.
- Precondition result:
  benchmark-like native supervisor can run under current wired/compressor
  limits, but current free memory is only about `4.8-4.9%`, far below the
  `55%` auto-batch threshold needed to reproduce the prior batch-4 runs. A full
  run now would select `chunk_batch_size=1` and be non-comparable.
- System evidence:
  benchmark-like supervisor `/bin/sleep` exited normally with compressor about
  `3200MB` and wired about `3041MB`; swap used remained about `2181MB`.
  A stricter free-percent preflight killed immediately on `free_percent`.
- Attempted mitigation:
  `/usr/sbin/purge` is available but returned `Operation not permitted` in this
  shell. No user applications were killed and no benchmark artifacts were
  deleted.
- Implication:
  the bridge fast-load patch remains confirmed at component level, but full-path
  speed/no-memory-increase acceptance remains unproven until a valid
  batch-4/native-supervisor run is possible.

## 2026-06-24 bridge fast-load before source verification probe

- Artifact:
  `mps/ANE/.ane_runs/json/bridge_fastload_before_source_verify_probe_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_fast_load_before_source_verify_removes_tmpdir_check_overhead_full_speed_inconclusive_due_host_memory_precondition`.
- Code change:
  `mps/maderix_ANE/bridge/ane_bridge.m` now tries `loadWithQoS` immediately
  when `ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT` is enabled and `model.mil`
  exists. A successful load uses route `load_cache_skip_source_fast_load` and
  skips the expensive per-weight source completeness walk; failed fast-loads
  fall back to the existing verification/write path.
- Bridge-level result:
  the one-second one-layer probe produced `6/6` transformer fast hits and
  `0` fallbacks; transformer bridge tmpdir time was only `0.000278874s`.
  The full diagnostic produced `192/192` transformer fast hits and `0`
  fallbacks; transformer bridge tmpdir time was `0.02779358199999999s`,
  compared with the previous current regression of about `5.9-6.3s`.
- Full-speed acceptance status:
  not accepted yet. The native-supervisor full attempt was killed at elapsed
  `0.0s` with child RSS `<1MB`, free memory `2.866%`, compressor `6329MB`,
  and reason `compressor_memory`, so it did not exercise inference. The
  non-supervised full diagnostic completed but host memory pressure forced
  `chunk_batch_size=1` (`auto_memory_limited`) and wall `59.07401037501404s`,
  making it non-comparable to the prior batch-4 `28-39s` runs.
- Memory/correctness caveat:
  this loop confirms the bridge tmpdir fix but does not prove the final
  no-memory-increase acceptance gate. Correctness was not rechecked.

## 2026-06-24 bridge tmpdir/materialization regression attribution

- Artifact:
  `mps/ANE/.ane_runs/json/bridge_tmpdir_cache_regression_attribution_20260623.json`
  and CSV peer.
- Verdict:
  `confirmed_bridge_tmpdir_materialization_regression_dominates_current_compile_load`.
- Current rerun slowdown root cause:
  current q240/control reruns are slow because transformer compile/load regressed
  from prior under-30 `~1.94-1.99s` to `~9.14-9.56s`; the dominant new cost is
  bridge tmpdir/materialization preparation (`~5.92-6.33s`) despite load-cache
  hits and zero load-cache misses. ANE `load_qos` itself is only
  `~1.36-1.52s`, so this is primarily host bridge cache/tmpdir materialization
  overhead, not q240 eval cost and not a true ANE compute bottleneck.
- Structural remaining bottleneck after recovering under-30 state:
  even the prior best `~27.9-28.2s` path is still dominated by transformer eval
  (`~19.7-19.8s`), especially repeated time-axis `attention_pre` selector-2
  requests plus axis pack/write/read work. This remains the reason the path is
  far from the ANE theoretical peak after load/compile is minimized.
- Caveat:
  current reruns used `--baseline none`, so correctness was not rechecked in the
  slow reruns. Correctness must be restored before promoting any recovered
  under-30 path.

## 2026-06-23 q240 vs matched control current-worktree cache regression

- Artifact:
  `mps/ANE/.ane_runs/json/q240_vs_control_current_worktree_cache_regression_20260623.json`
  and CSV peer.
- Verdict:
  `confirmed_global_compile_cache_state_regression_not_q240_specific`.
- Current q240 rerun:
  wall `38.78787529101828s`, transformer `32.55836379202083s`,
  transformer compile/load `9.555925211054273s`, transformer eval
  `20.199491960869636s`, time-axis eval `14.328791043895762s`, time-axis
  `attention_pre` eval `9.703135077783372s`, time-axis pack
  `2.600520497362595s`, native max child RSS `1623.891 MB`, swap growth `0.0`.
- Current matched explicit non-q240 control:
  wall `39.23634491697885s`, transformer `32.27579816698562s`,
  transformer compile/load `9.136685500969179s`, transformer eval
  `20.17042325309012s`, time-axis eval `14.337507542106323s`, time-axis
  `attention_pre` eval `9.773464999743737s`, time-axis pack
  `2.52339941682294s`, native max child RSS `1660.484 MB`, swap growth `0.0`.
- Comparison:
  q240 is `0.44846962596057024s` faster than the matched control in this rerun,
  but both are about `10.9-11.1s` slower than the prior under-30 validation.
  Both report bridge load-cache hits `123` and misses `0`, so the next
  bottleneck is not q240 selection; it is the cache/load/materialization state
  behind the high transformer compile/load totals.
- Correctness:
  neither current rerun checked waveform correctness because both recovered
  commands used `--baseline none`. Prior validation was exact, but current
  promotion still requires fresh correctness once cache-state is recovered.

## 2026-06-23 q240 opt-in current-worktree rerun

- Artifact:
  `mps/ANE/.ane_runs/json/q240_opt_in_current_worktree_rerun_20260623.json`
  and CSV peer.
- Verdict:
  `falsified_current_worktree_q240_preset_promotion_due_compile_regression_and_missing_correctness_check`.
- Command:
  `/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_test_clean_benchmark.py --audio test_clean.m4a --full-audio --baseline none --private-ane-allow-long-audio --private-ane-fused-band-split --private-ane-fused-band-split-max-outputs 4 --private-ane-fused-mask-estimator --private-ane-fused-mask-estimator-max-outputs 2 --private-ane-persistent-aux-handles --private-ane-skip-source-write-on-cache-hit --private-ane-tiled-time-attention-pre --private-ane-tiled-time-attention-pre-q-chunk 240 --out benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_rerun_20260623.json`.
- Result:
  wall `38.78787529101828s`, transformer `32.55836379202083s`,
  transformer compile/load `9.555925211054273s`, transformer eval
  `20.199491960869636s`, time-axis eval `14.328791043895762s`,
  time-axis `attention_pre` eval `9.703135077783372s`, time-axis pack
  `2.600520497362595s`, freq-axis eval `5.870700916973874s`.
- Memory:
  native max child RSS `1623.891 MB`, max process-group RSS `1637.438 MB`,
  native swap growth `0.0 MB`. This run did not violate the no-memory-growth
  constraint.
- Correctness:
  not verified in this rerun because the recovered command used
  `--baseline none`; prior q240 validation was exact, but current-worktree
  promotion needs a fresh correctness check or matched baseline run.
- Conclusion:
  do not codify q240 as the current opt-in baseline yet. The regression is
  dominated by compile/load/cache state, not memory. Next loop must run the
  matched explicit non-q240 control on the current worktree to decide whether
  this is q240-specific or a global cache-state/worktree regression.

## 2026-06-23 transformer attention_pre segment-count audit

- Artifact:
  `mps/ANE/.ane_runs/json/transformer_attention_pre_segment_count_audit_20260623.json`
  and CSV peer.
- Verdict:
  `confirmed_time_axis_attention_pre_segment_count_dominates_no_new_memory_neutral_pack_candidate_visible`.
- Profile source:
  `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_load_cache_bridgeprofile_20260623_profile/transformer_timings.csv`.
- The current batch-4 profile contains 24 transformer rows: 12 time-axis rows
  and 12 freq-axis rows. Time-axis rows carry `bridge_pack_gate=4.0`,
  `axis_pack_reused=3.0`, `tiled_time_attention_pre=False`, and qchunk `0`.
  Combined with the prior micro-profile equivalence, this implies about
  48 time-axis `attention_pre` selector-2 requests and about 96 total
  `attention_pre` selector-2 requests across time+freq.
- Time-axis profile sums from this CSV:
  `attention_pre_eval_sec=9.538814419182017`,
  `attention_pre_total_sec=10.015570706047583`,
  `axis_pack_sec=2.5199859970016405`,
  `eval_sec=14.225222417007899`,
  `load_or_compile_wall_sec=3.456740210938733`,
  `ane_write_sec=0.5406000427610707`,
  `ane_read_sec=0.7503471150121186`,
  `segment_wall_sec=19.306082000985043`.
- Closed candidates carried forward:
  same-layer H16-visible selector-2 request reuse is falsified by the H16
  lower-control audit; `bridge_pack_gate=0` / materialized packed-buffer
  handoff was already falsified by transformer-only ablation; batch-axis eval
  promotion remains disallowed due prior multi-GiB wired/native-supervisor
  pressure.
- Current practical speed candidate:
  `full_path_tiled_q240_skip_source_validation_20260623.json` already measured
  exact `test_clean.m4a` opt-in q240/skip-source/fused runs, with matched
  control `28.173s`, q240 `27.903s`, and no RSS/swap increase. It is not yet a
  default because default smoke still hits the known band-split compile-fail
  path. Next loop should verify that preset on the current worktree and decide
  whether to document/codify it as the opt-in baseline.

## 2026-06-23 H16 selector-2 lower-control reuse-field audit

- Artifact:
  `mps/ANE/.ane_runs/json/h16_selector2_lower_control_reuse_field_audit_20260623.json`
  and CSV peer.
- Verdict:
  `falsified_static_h16_host_authorable_memory_neutral_reuse_field`.
- Profiler context carried into this static loop:
  `transformer_sec=24.871128999977373`,
  `transformer_eval_sec=19.867204998852685`,
  `transformer_compile_sec=1.9713062929804437`,
  `time_axis_eval_sec=13.97083224792732`,
  `time_pre_eval_sec=9.508778334013186`,
  `time_axis_pack_sec=2.45342729089316`,
  native max child RSS `1660.547 MB`, swap growth `0.0 MB`.
- IDA evidence from `apple_h16_ane_interface_20260623`:
  `ANE_ProgramPrepareAndSubmitRequest_gated` allocates/constructs/destructs
  `ANEResourceCollection` at `0xfffffe0009299ba8`,
  `0xfffffe0009299bac`, and `0xfffffe000929a024`; calls
  `ANE_ProgramCheckandPrewireBuffers_gated` at `0xfffffe0009299c60`;
  creates request at `0xfffffe0009299e5c`; adds pending scheduler request at
  `0xfffffe0009299ec4`; wires and DART-maps resources at
  `0xfffffe000929c80c` and `0xfffffe000929c854`; and removes pending request
  at `0xfffffe000929ca30`.
- `updateRequestFWCommand` is called from `SendRequestToFirmware_gated` at
  `0xfffffe00092914b4`; it updates intermediate/process mutable DVA state,
  uses `lookupClusterMutableBuffer` at `0xfffffe0009292c28` and
  `0xfffffe0009293148`, and contains the `mutable memory not dart mapped`
  check path.
- Conclusion: the H16-visible path contains request-lifetime kernel scheduler,
  resource, DART mapping, fence/shared-event, and firmware command mutation
  state. No audited field is both host-authorable and reusable without retaining
  additional buffers/handles. Further speed work should return to
  memory-neutral transformer runtime reductions: request count, segment
  dispatch, layout pack/unpack, and transfer overhead.

## 2026-06-23 IOKit selector-2 call-site trace attempt
- Evidence: `mps/ANE/.ane_runs/json/iokit_selector2_callsite_trace_attempt_20260623.json` and CSV peer `mps/ANE/.ane_runs/csv/iokit_selector2_callsite_trace_attempt_20260623.csv`.
- IDA session `ane_services_dyld_20260623` precisely located the `IOConnectCallAsyncMethod` call site inside `ANEServicesDevice::ANE_ProgramSendRequest`: static call instruction `0x19e69dcf8`, next instruction `0x19e69dcfc`, static imagebase `0x19e68b000`, offsets `0x12cf8` and `0x12cfc`.
- A Frida inline call-site hook attached to runtime addresses such as `0x1a32cdcf8` / `0x1a32cdcfc`, but recorded zero hits during the minimal `attention_pre` eval.
- A Frida Stalker attempt attached to the wrapper function address but did not produce usable call summaries for the lower IOKit call in this session.
- DTrace exists (`/usr/sbin/dtrace`) but is unavailable here: SIP is on and `dtrace` reports `DTrace requires additional privileges`.
- Latest minimal raw profile still ran successfully: `benchmark_results/private_ane/attention_pre_time_b4_frida_spawn_raw_20260623.json`, with eval mean about `0.018014s` in the last run.
- Verdict: `inconclusive_callsite_and_dtrace_selector2_timing_not_captured_current_session`.
- Solution implication: the remaining per-request selector-2 split is now blocked on stronger tracing or deeper static recovery. Near-term actionable work should either use privileged/PAC-aware tracing outside this session, or continue static H16 selector-2 analysis for reusable state/control fields that avoid needing per-phase runtime timings.
- Next target: continue with static H16 selector-2 lower-path analysis around `updateRequestFWCommand`, prewire, scheduler insertion, and resource collection lifetimes to look for a memory-neutral reusable state/control field.

## 2026-06-23 IOKit selector-2 hook boundary probe
- Evidence: `mps/ANE/.ane_runs/json/iokit_selector2_hook_boundary_probe_20260623.json` and CSV peer `mps/ANE/.ane_runs/csv/iokit_selector2_hook_boundary_probe_20260623.csv`.
- This loop attempted to time the boundary under `ANEServicesDevice::ANE_ProgramSendRequest`: `IOConnectCallAsyncMethod` selector `2` versus user-space request packing.
- Minimal probe reused the Frida-spawned `attention_pre` runner and produced `benchmark_results/private_ane/attention_pre_time_b4_frida_spawn_raw_20260623.json`, with latest `compile_sec≈0.289440s`, `eval_mean_sec≈0.017500s`, and `total_mean_sec≈0.018240s`.
- Direct Frida export hooks could not resolve `IOConnectCallAsyncMethod`, `IOConnectCallMethod`, or `IOConnectCallStructMethod` in the process, even though ANEServices imports `_IOConnectCallAsyncMethod`, `_IOConnectCallMethod`, and `_IOConnectCallStructMethod`.
- ANEServices import slots were located at the expected IDA-derived offsets: `_IOConnectCallAsyncMethod` import pointer `0x19e6b4308`, `_IOConnectCallMethod` `0x19e6b4318`, `_IOConnectCallStructMethod` `0x19e6b4338`, imagebase `0x19e68b000`.
- Runtime import slots resolved to PAC-signed arm64e pointers such as `0x9136a231f027ab11`; `Interceptor.attach` failed with access violations, including after a pointer-strip retry.
- No selector-2 IOKit timing was captured in this loop.
- Verdict: `inconclusive_iokit_selector2_import_hook_blocked_by_pac_or_non_exported_call_target`.
- Solution implication: user-space ANEServices wrappers are hookable, but the next lower IOKit boundary is not currently reachable through simple Frida export/import-pointer hooks. Further runtime attribution needs a PAC-aware hook method, DTrace/system tracing of IOKit calls, or kernel/H16 instrumentation; otherwise the practical next path is static RE of selector-2 lower state/control fields.
- Next target: try a PAC-aware or system-level timing route for the IOKit selector-2 boundary, such as hooking ANEServices call-site instruction addresses, using DTrace where permitted, or deriving call-site offsets from IDA and attaching before the authenticated branch target.

## 2026-06-23 ANEServices selector-2 Frida timing feasibility
- Evidence: `mps/ANE/.ane_runs/json/aneservices_selector2_frida_timing_feasibility_20260623.json` and CSV peer `mps/ANE/.ane_runs/csv/aneservices_selector2_frida_timing_feasibility_20260623.csv`.
- This loop used `reverse-engineering` and `ida-reverse` methodology, IDA session `ane_services_dyld_20260623`, Frida `17.11.0`, and a minimal `attention_pre` micro-profile. It did not run the full `test_clean.m4a` path and did not retain extra handles or buffers.
- IDA confirmed user-space selector-2 targets in ANEServices: `ANEServicesDevice::ANE_ProgramSendRequest` at `0x19e69dbc0`, `ANERequestReceiver::ProgramProcessRequest` at `0x19e6a18e4`, and `ANEServicesProgramProcessRequestDirect` at `0x19e6a7d2c`.
- Frida confirmed the active process loads `ANEServices` and can resolve these functions dynamically. In the spawned minimal probe, 18 ANEServices symbols matched the hook patterns including cold paths.
- Minimal probe command path: `mps/ANE/.ane_runs/tmp/attention_pre_hook_runner.py` running `benchmark/private_ane_attention_pre_micro_profile.py --axis time --batch 4 --seq 960 --valid-seq 938 --stages attention_pre --repeats 1 --warmup 0 --q-chunk 240`.
- Raw micro-profile: `benchmark_results/private_ane/attention_pre_time_b4_frida_spawn_raw_20260623.json`, with `compile_sec=0.311602s`, `eval_mean_sec≈0.017045s`, and `total_mean_sec≈0.017687s`.
- Dynamic hook hits during that single eval: `ANEServicesProgramProcessRequestDirect` count `1`, `ANERequestReceiver::ProgramProcessRequest` count `1`, and `ANEServicesDevice::ANE_ProgramSendRequest` count `1`. Each recorded about `17 ms` with millisecond-resolution Frida timing, matching the micro-profile outer eval.
- Verdict: `confirmed_user_space_aneservices_selector2_hooks_feasible_for_outer_wrapper_timing`.
- Solution implication: user-space ANEServices wrapper timing is feasible and confirms the minimal `attention_pre` eval traverses the selector-2 wrapper stack. This still does not split H16 kernel prepare/submit internals; next progress requires timing the boundary below `ANE_ProgramSendRequest`, especially `IOConnectCallAsyncMethod` selector `2`, or using kernel/H16 dynamic tracing.
- Next target: hook or otherwise time the next boundary under `ANEServicesDevice::ANE_ProgramSendRequest`, especially `IOConnectCallAsyncMethod` selector `2` versus user-space request packing, to separate user-space wrapper time from kernel/H16 selector-2 prepare/submit time.

## 2026-06-23 bridge eval selector-2 timing boundary
- Evidence: `mps/ANE/.ane_runs/json/bridge_eval_selector2_timing_boundary_20260623.json` and CSV peer `mps/ANE/.ane_runs/csv/bridge_eval_selector2_timing_boundary_20260623.csv`.
- This loop inspected the active Python bridge wrapper, transformer aggregation, active C bridge, and existing H16 selector-2 static RE artifact to determine whether current source-level timing can split `eval_sec` into selector-2 materialization classes.
- Active Python bridge source is `benchmark/private_ane_real_attention_probe.py`; it loads `mps/maderix_ANE/bridge/libane_bridge.dylib`, not the older `mps/ANE/bridge` copy.
- Existing Python run profiles expose host `cast_sec`, `alloc_sec`, `write_sec`, opaque `eval_sec`, and `read_sec`; transformer runtime adds `axis_pack_sec` / `axis_unpack_sec`.
- Active C bridge profile fields in `mps/maderix_ANE/bridge/ane_bridge.m` are compile/load centered: `total_sec`, `mil_data_sec`, `weights_dict_sec`, `descriptor_sec`, `model_create_sec`, `identifier_sec`, `tmpdir_sec`, `file_write_sec`, `compile_qos_sec`, `load_qos_sec`, `surface_create_sec`, `request_create_sec`, and `handle_create_sec`.
- Important correction: current `request_create_sec` is request object construction during compile/load-cache binding. It is not the per-eval selector-2 lower `ANERequest` creation / prewire / DVA update / firmware-submit preparation confirmed in H16 static RE.
- `ane_bridge_eval` is a single private call boundary: normal route calls `evaluateWithQoS:options:request:error:`, while alternate client/direct-process routes are also single calls. The bridge returns only boolean success and Python records the whole wall time as `eval_sec`.
- Verdict: `confirmed_current_bridge_collapses_selector2_materialization_into_opaque_eval_sec`.
- Solution implication: a source-level bridge patch can add scalar route/outer-eval timing but cannot split selector-2 internals because they occur inside private framework/kernel calls. Further speed work needs dynamic hooks/signposts/DTrace/Frida on ANEServices or AppleH16ANEInterface symbols, or an IDA-guided lower reusable state.
- Next target: create a minimal dynamic-hook feasibility probe for ANEServices / AppleH16 selector-2 timing targets, starting with user-space ANEServices functions if symbols are reachable and falling back to an IDA-guided static blocker if SIP/TCC/kernel tracing prevents safe runtime hooks.

## 2026-06-23 time attention_pre graph/layout candidate audit
- Evidence: `mps/ANE/.ane_runs/json/time_attention_pre_graph_layout_candidate_audit_20260623.json` and CSV peer `mps/ANE/.ane_runs/csv/time_attention_pre_graph_layout_candidate_audit_20260623.csv`.
- This loop audited existing `test_clean.m4a` full-path artifacts for host-visible, memory-neutral graph/layout candidates after the selector-2 attribution loop.
- Baseline policy artifact is non-tiled explicit control: `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_skip_source_explicit_control_20260623.json`, with full path `28.173455959011335s`, transformer eval `19.829284292005468s`, time-axis eval `13.969854625000153s`, time-axis pack `2.499261085089529s`, RSS `1639.469MB`, and swap growth `0.0MB`.
- q240 layer-0 tiled artifact `test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_component_fields_fixed_20260623.json` does not provide a clear promotable win over explicit-control default-off: full path `28.357753333984874s`, transformer eval `19.867204998852685s`, time-axis eval `13.97083224792732s`, time-axis pack `2.45342729089316s`, RSS `1660.547MB`, and swap growth `0.0MB`.
- The rerun q240 artifact is faster on full path (`27.649230875016656s`) but not enough to prove the route policy because the fixed component artifact and explicit-control artifact are within run variance and transformer eval remains about `19.7-19.9s`.
- `surface_handoff_gate_ffn` is closed as a memory-neutral speed candidate for this route: full path `30.064417415997013s`, about `+1.8909614569856785s` versus explicit control, with higher compile/materialization cost.
- `direct_time_to_freq_unpadded` is closed as a speed candidate for this route: full path `29.920132166007534s`, about `+1.7466762069961987s` versus explicit control, with higher compile/materialization cost.
- Time-axis batch eval remains disallowed by existing runtime evidence and code comment: it can compile/load for `batch=124, seq=960`, but creates multi-GiB wired pressure and is killed by the native supervisor, violating the no-memory-increase constraint.
- Verdict: `falsified_current_host_visible_graph_layout_candidates_for_memory_neutral_time_attention_pre_speedup`.
- Solution implication: current host-visible graph/layout knobs do not provide a safe path toward ANE peak. Further progress should instrument or recover lower selector-2 runtime classes rather than repeat qchunk, surface handoff, unpadded freq, or batch-axis promotion.
- Next target: add or mine lower selector-2/request timing counters around bridge eval so time-axis `attention_pre` can be split into request creation/prewire, DVA update/`updateRequestFWCommand`, fence/shared-event, firmware submit, read/write, and host pack classes without increasing retained memory.

## 2026-06-23 transformer runtime selector-2 attribution
- Evidence: `mps/ANE/.ane_runs/json/transformer_runtime_selector2_attribution_20260623.json` and CSV peer `mps/ANE/.ane_runs/csv/transformer_runtime_selector2_attribution_20260623.csv`.
- This loop synthesized existing `test_clean.m4a` profiler data and H16 selector-2 reverse-engineering evidence without changing inference behavior or retaining additional memory.
- Measured context: transformer `24.871128999977373s`; transformer eval `19.867204998852685s`; transformer compile `1.9713062929804437s`; native max child RSS `1660.547MB`; native max swap growth `0.0MB`.
- Time axis is dominant: `time_axis_eval_sec=13.97083224792732s`, which is `70.32107560542171%` of transformer eval. `time_axis_ane_eval_only_sec=10.320496624626685s`, `time_axis_pack_sec=2.45342729089316s`, and `time_axis_load_or_compile_wall_sec=1.550774584931787s`.
- Time-axis `pre` is the largest single measured component: `time_pre_eval_sec=9.508778334013186s`, `47.86168127103088%` of transformer eval and `33.53149391640117%` of the measured wall context.
- Attention-pre micro-profiles show q240 tiling is not a raw peak-compute path: `b4 q240 eval=0.014045583986444399s` for about `0.7533643720483468 TFLOPS`; `b62 q240 eval=0.18706374999601394s` for about `0.8767725424273536 TFLOPS`. This is far below the measured ANE peak and supports a segmented request/layout/materialization bottleneck rather than a single saturated kernel.
- Static selector-2 RE remains the causal mechanism: selector `2` lower eval includes fresh resource collection allocation, process validation, prewire, `ANERequest` creation, scheduler insertion, intermediate/mutable DVA updates, fence/shared-event work, firmware command DVA rewrites, and submit preparation.
- Verdict: `confirmed_segmented_time_attention_pre_eval_and_selector2_materialization_dominate_remaining_runtime`.
- Solution implication: do not spend the next loop on top-level load-cache, generic SDPA, qchunk resweeps, or retained-handle memory growth. Next speedups must either find a memory-neutral lower reusable selector-2/request materializer state or reduce time-axis `attention_pre` request count/layout/DVA update work.
- Next target: identify one memory-neutral graph/layout change that reduces time-axis `attention_pre` segmented request count or `axis_pack`/DVA-update cost, and benchmark it on `test_clean.m4a` with RSS/swap unchanged; if no such change is visible, instrument lower selector-2 runtime timestamps.

## 2026-06-23 H16 selector 2 prepare/submit materialization
- Evidence: `mps/ANE/.ane_runs/json/h16_selector2_prepare_submit_materialization_20260623.json` and CSV peer.
- Profiler context is unchanged: current best `test_clean.m4a` full path is about `27.649230875016656s`; transformer is `24.871128999977373s`; transformer eval is `19.867204998852685s`; transformer compile is `1.9713062929804437s`; `time.pre.eval_sec=9.508778334013186s`; `time.axis_pack_sec=2.45342729089316s`; native max child RSS is `1660.547MB`; swap growth is `0.0MB`.
- `ANEHWDevice::ANE_ProgramPrepareAndSubmitRequest_gated` at `0xfffffe0009299b34` allocates a fresh `ANEResourceCollection`, validates process state through `isProcessValid`, calls `ANE_ProgramCheckandPrewireBuffers_gated`, creates an `ANERequest`, inserts it into `ANEScheduler::addPendingRequest`, handles intermediate buffer updates, creates/signals fences and shared events, and populates resource collections.
- `ANEHWDevice::updateRequestFWCommand` at `0xfffffe00092929a0` writes request-derived metadata into the firmware command, updates intermediate DVA addresses, updates process mutable DVA addresses, checks mutable memory DART mapping, and writes command pointers at offsets such as `+0x18` and `+0x20`.
- Verdict: `confirmed_selector2_eval_has_per_request_materialization_and_dva_update_work`. This is now the strongest root-cause explanation for the remaining transformer eval wall time: segmented eval repeatedly pays request/materialization/DVA-update/firmware-submit preparation, while top-level load/compile is secondary.
- Solution implication: do not keep chasing top-level load-cache or selector replay. Either recover a lower firmware/private reusable request/materializer state, or reduce the number/cost of segmented requests and DVA/layout updates at the graph/layout level without increasing retained memory.
- Next target: quantify which selector-2 materialization class dominates runtime for time-axis `attention_pre`: request creation/prewire, `updateRequestFWCommand` DVA rewrites, process remap, or firmware submit. Add or mine existing per-stage trace counters/timestamps without increasing memory.

## 2026-06-23 H16 selector 8/2 lower path
- Evidence: `mps/ANE/.ane_runs/json/h16_selector8_selector2_lower_path_20260623.json` and CSV peer.
- Profiler context is unchanged: current best `test_clean.m4a` full path is about `27.649230875016656s`; transformer is `24.871128999977373s`; transformer eval is `19.867204998852685s`; transformer compile is `1.9713062929804437s`; `time.pre.eval_sec=9.508778334013186s`; `time.axis_pack_sec=2.45342729089316s`; native max child RSS is `1660.547MB`; swap growth is `0.0MB`.
- Correct H16 context is now restored: `/tmp/KMUtilProducts/BootKernelCollection.kc` is `Mach-O 64-bit arm64e`; `mps/ANE/.ane_runs/tmp/AppleH16ANEInterface.patched.macho` is `Mach-O 64-bit kext bundle arm64e`; IDA session `apple_h16_ane_interface_20260623` is healthy with imagebase `0xfffffe000743d780`.
- Selector `8` wrapper `ANE_ProgramCreateInstance` at `0xfffffe00093483c8` is a size gate: it checks input `0x35e18`, output `0xac738`, then calls `ANEClientDevice::programCreateInstance`.
- Selector `8` driver lower path `ANEDriver::ANE_ProgramCreateInstance_gated` at `0xfffffe0009271a3c` creates a program handle, calls per-ANE device create-instance, finds the driver client, and calls `addProgramToANEMapping_gated`. This stage is handle/mapping state, not a proven authorable transformer materializer.
- Selector `8` device lower path `ANEHWDevice::ANE_ProgramCreateInstance_gated` at `0xfffffe000928c5ec` validates args, procedure count, weight-buffer count, creates a program handle, and enters descriptor/process/load/patch subpaths. First pass found no safe memory-neutral accepted-state replay field.
- Selector `2` wrapper `ANE_ProgramSendRequest` at `0xfffffe0009347b3c` validates client state, request pointer, async wake port, and builds async reference; it does not author reusable materializer state.
- Selector `2` driver/device path resolves to `ANEDriver::ANE_ProgramSendRequest` at `0xfffffe00092724bc`, `ANEHWDevice::ANE_ProgramSendRequest_gated` at `0xfffffe0009297418`, `ANE_ProgramSendRequestInitialChecksAndLookups_gated` at `0xfffffe00092977e8`, `ANE_ProgramPrepareAndSubmitRequest_gated` at `0xfffffe0009299b34`, `updateRequestFWCommand` at `0xfffffe00092929a0`, and `SendRequestToFirmware_gated` at `0xfffffe000928ff28`.
- Verdict: `confirmed_matching_h16_context_and_first_lower_chain_no_direct_authorable_materializer`. This supports the current root-cause model: slow transformer inference remains in segmented eval/layout and firmware-submit/request materialization, not in a missing top-level wrapper control.
- Next target: analyze `ANEHWDevice::ANE_ProgramPrepareAndSubmitRequest_gated` and `ANEHWDevice::updateRequestFWCommand` for memory-neutral reuse/layout controls. Determine whether repeated time-axis `attention_pre` eval is caused by request rebuild, DVA update, process remap, mutable/intermediate buffer update, or unavoidable firmware-private submit semantics.

## 2026-06-23 selector 3/8/2 handler availability
- Evidence: `mps/ANE/.ane_runs/json/selector_3_8_2_handler_availability_20260623.json` and CSV peer.
- Profiler context is unchanged: current best `test_clean.m4a` full path is about `27.649230875016656s`; transformer is `24.871128999977373s`; transformer eval is `19.867204998852685s`; transformer compile is `1.9713062929804437s`; `time.pre.eval_sec=9.508778334013186s`; `time.axis_pack_sec=2.45342729089316s`; native max child RSS is `1660.547MB`; swap growth is `0.0MB`.
- BootKC target availability is confirmed through existing generated BootKC CSV/notes. Caveat: the reopened `bootkc_ane_dispatch_20260623` session points at `mps/ANE/ida_inputs/BootKernelExtensions.kc`, which `file(1)` reports as Mach-O 64-bit `x86_64`; it is not the authoritative arm64e H16 handler database for decompiling the prior AppleH16ANEInterface CSV addresses.
- Confirmed selector `3`: `ANEServicesDevice::ANE_ProgramCreate` at `0x19e69d07c` calls `IOConnectCallStructMethod` with input `0xd88` and output `0xac738`; BootKC `_sANEDriverClientMethods` visible row `3` is `ANE_ProgramCreate` with struct input `0x20` and output `0x0`.
- Confirmed selector `8`: `ANEServicesDevice::ANE_ProgramCreateInstance` at `0x19e69d248` calls `IOConnectCallStructMethod` with input `0x35e18` and output `0xac738`; BootKC visible row `8` is `ANE_ProgramCreateInstance` with struct input `0x20` and output `0x0`.
- Confirmed selector `2`: `ANEServicesDevice::ANE_ProgramSendRequest` at `0x19e69dbc0` calls `IOConnectCallAsyncMethod` with input `0x948` and output `0x28`; BootKC visible row `2` is `ANE_ProgramSendRequest` with matching struct input `0x948` and output `0x28`.
- Existing route evidence bounds ANEServices hinted open type `3` to `H11ANEInUserClient -> _sANEDriverClientMethods`, not the direct-path table. Selector `3/8` large structs therefore pass through a lower wrapper/copyin/repack layer rather than appearing as fixed visible dispatch struct sizes.
- Verdict: `confirmed_selector_3_8_2_handler_family_available_but_no_supported_memory_neutral_reuse_control_yet`. This closes the target-availability question and keeps the remaining root cause below same-layer wrapper replay: segmented transformer eval/layout still dominates because no supported memory-neutral persistent materializer/accepted-state control is proven at AppleNeuralEngine, ANEServices, or visible selector wrapper boundaries.
- Next target: reconstruct or reopen the matching arm64e/raw Preboot BootKC context for the existing AppleH16ANEInterface dispatch CSV, then focus on `ANE_ProgramCreateInstance` and `ANE_ProgramSendRequest` lower consumers. Recover whether any deeper accepted-state/materializer field is authorable; if not, close this as kernel-private/firmware-private and return to memory-neutral graph/layout reduction around time-axis `attention_pre`.

## 2026-06-23 ANEServices lower route semantics
- Evidence: `mps/ANE/.ane_runs/json/ane_services_lower_route_semantics_20260623.json` and CSV peer.
- Profiler context is unchanged: current best `test_clean.m4a` full path is about `27.649230875016656s`; transformer is `24.871128999977373s`; transformer eval is `19.867204998852685s`; transformer compile is `1.9713062929804437s`; `time.pre.eval_sec=9.508778334013186s`; `time.axis_pack_sec=2.45342729089316s`; native max child RSS is `1660.547MB`.
- IDA sessions opened/saved: `ane_services_dyld_20260623` for `ANEServices.i64`; `ane_compiler_dyld_20260623` for `ANECompiler.i64`.
- `ANEServices` is the relevant runtime lower framework: it exposes `ANEServicesProgramCreate`, `ANEServicesProgramCreateNewInstance`, `ANEServicesProgramProcessRequestDirect`, `ANERequestReceiver::ProgramProcessRequest`, and `ANEServicesDevice::ANE_ProgramSendRequest`.
- `ANECompiler` targeted string scan did not expose the runtime handle/cache route; the relevant scan only found `CompileANEProgramForDebugging`.
- Confirmed create/load wrappers: `ANEServicesDevice::ANE_ProgramCreate` at `0x19e69d07c` calls `IOConnectCallStructMethod` selector `3` and returns `progHandle`; `ANE_ProgramCreateInstance` at `0x19e69d248` calls `IOConnectCallStructMethod` selector `8` using an existing handle.
- Confirmed evaluate wrapper: `ANERequestReceiver::ProgramProcessRequest` at `0x19e6a18e4` reads `programHandle/procid/transid`, validates buffers, and calls `ANEServicesDevice::ANE_ProgramSendRequest`; `ANE_ProgramSendRequest` at `0x19e69dbc0` calls `IOConnectCallAsyncMethod` selector `2` with request struct size `0x948`.
- Verdict: `confirmed_ane_services_runtime_wrapper_no_supported_materializer_reuse_control`. ANEServices exposes runtime IOKit wrappers and request packers, but no supported memory-neutral field that authors/replays accepted transformer segment state.
- Next target: move below ANEServices selectors `3`, `8`, and `2` into the kernel/user-client layer or recover the request/output struct layouts enough to identify lower accepted-state/materializer fields. Do not repeat AppleNeuralEngine/ANEServices wrapper scans without new evidence.

## 2026-06-23 AppleNeuralEngine VirtualClient route semantics
- Evidence: `mps/ANE/.ane_runs/json/apple_neural_engine_virtualclient_route_semantics_20260623.json` and CSV peer.
- Profiler context is unchanged: current best `test_clean.m4a` full path is about `27.649230875016656s`; transformer is `24.871128999977373s`; transformer eval is `19.867204998852685s`; transformer compile is `1.9713062929804437s`; `time.pre.eval_sec=9.508778334013186s`; `time.axis_pack_sec=2.45342729089316s`; native max child RSS is `1660.547MB`.
- IDA session: `apple_neural_engine_dyld_20260623`, input `mps/ANE/ida_inputs/dyld_extracted/System/Library/PrivateFrameworks/AppleNeuralEngine.framework/Versions/A/AppleNeuralEngine`.
- Confirmed route map: dictionary wrapper `-[_ANEVirtualClient callIOUserClientWithDictionary:inDictionary:error:]` at `0x19f93fa34` multiplexes dictionary `command` through kernel selector `0x10`; cache commands are `5` exists-for, `6` purge-for, `7` exists-matching-hash, `8` purge-matching-hash.
- Confirmed load semantics: `loadModel` command `2` receives `programHandle`, `intermediateBufferHandle`, and `queueDepth` from the reply, then installs them via `updateModelAttributes:state:programHandle:intermediateBufferHandle:queueDepth:` at `0x19f92c894` and creates `_ANEProgramForEvaluation` at `0x19f92c8b0`.
- Confirmed evaluate/map boundaries: current evaluate calls direct `IOConnectCallMethod` selector `0x13` at `0x19f93300c`; map IOSurfaces calls raw command `0xD` at `0x19f937984`.
- Verdict: `confirmed_user_space_wrapper_no_supported_persistent_reuse_control`. This wrapper layer has post-load handles and cache/precompiled gates, but no confirmed supported memory-neutral control that reuses transformer segment accepted-state or removes segmented eval/materialization overhead.
- Next target: move below this user-space wrapper. Open/adopt `ANEServices` and `ANECompiler` IDA sessions and trace selector `0x10` command `2` load and selector `0x13` evaluate toward lower accepted-state/materializer control. Do not repeat host-visible qchunk/SDPA/retained-handle/descriptor/IOSurface probes without new evidence.

## 2026-06-23 AppleNeuralEngine dyld extraction/import
- Evidence: `mps/ANE/.ane_runs/json/dyld_apple_neural_engine_extraction_import_20260623.json`, CSV peer, and extraction log `mps/ANE/.ane_runs/dsc_extract_call_20260623.log`.
- Profiler context is unchanged this loop: current best wall `27.649230875016656s`, RTF `0.6983888617967803`, transformer `24.871128999977373s`, transformer eval `19.867204998852685s`, transformer compile `1.9713062929804437s`, `time.pre.eval_sec=9.508778334013186s`, `time.axis_pack_sec=2.45342729089316s`, native max child RSS `1660.547MB`.
- `dyldextractor==2.2.2` in a system-Python `3.9` venv still failed with the same `TypeError: can only concatenate str (not "int") to str`, so the previous failure was not only conda Python `3.13`.
- Homebrew `jtool2` installed successfully but is deprecated and was unusable for this split cache probe (`rc=137` on cache inspection).
- Built local caller `mps/ANE/experiments/dsc_extract_call.c` for `/usr/lib/dsc_extractor.bundle`; extraction succeeded with `rc=0`, processed `3646` images in `real 152.88s`, and wrote `3646` files / `5.2G` to `mps/ANE/ida_inputs/dyld_extracted`.
- Extracted targets are valid arm64e Mach-O dylibs.
- Extracted `AppleNeuralEngine`: `mps/ANE/ida_inputs/dyld_extracted/System/Library/PrivateFrameworks/AppleNeuralEngine.framework/Versions/A/AppleNeuralEngine`, size `680K`, imagebase `0x19f90e000`.
- Extracted `ANEServices`: `mps/ANE/ida_inputs/dyld_extracted/System/Library/PrivateFrameworks/ANEServices.framework/Versions/A/ANEServices`, size `292K`, imagebase `0x19e68b000`.
- Extracted `ANECompiler`: `mps/ANE/ida_inputs/dyld_extracted/System/Library/PrivateFrameworks/ANECompiler.framework/Versions/A/ANECompiler`, size `45M`, imagebase `0x222d54000`.
- IDA session `apple_neural_engine_dyld_20260623` is active for extracted `AppleNeuralEngine`; open-time health reported `auto_analysis_ready=true`, while the final post-query health check reported `auto_analysis_ready=false`, `hexrays_ready=true`, strings cache `2258`; survey recovered functions `3466` and named functions `2232`.
- Initial IDA findings expose the needed user-space control surface: `-[_ANEVirtualClient compileModel:options:qos:error:]` (`0x19f92a5e4`), `loadModel` (`0x19f92c158`), `loadModelNewInstance` (`0x19f92cec0`), `unloadModel` (`0x19f9302cc`), `evaluateWithModel` (`0x19f930d54`), `doEvaluateWithModel` (`0x19f931bbc`), `mapIOSurfacesWithModel:request:cacheInference:error:` (`0x19f936b44`), `callIOUserClientWithDictionary:inDictionary:error:` (`0x19f93fa34`), `shouldUsePrecompiledPath` (`0x19f941238`), and `compiledModelExistsFor:` (`0x19f933c04`).
- Relevant strings are present: `ANEVirtualClient`, compile/load/unload/evaluate dictionary methods, `programHandle`, `intermediateBufferHandle`, `cacheURLIdentifier`, `kANEFModelPreCompiled`, `_ANEF_COMPILED_MODEL_EXISTS`, and `_ANEF_PURGE_COMPILED_MODEL`.
- Verdict: `confirmed_dsc_extractor_produced_ida_usable_apple_neural_engine_targets`.
- Next target: use `apple_neural_engine_dyld_20260623` to slice compile/load/evaluate dictionary construction and `callIOUserClientWithDictionary` selector mapping; decide whether any supported cache/precompiled/dictionary route can reduce repeated compile/load or whether the remaining transformer runtime bottleneck stays below this user-space wrapper layer.

## 2026-06-23 dyld extractor tooling probe
- Evidence: `mps/ANE/.ane_runs/json/dyld_extractor_tooling_probe_20260623.json` and CSV peer.
- Installed PyPI `dyldextractor==2.2.2` into `/Users/baicai1145/miniconda3`; entry points `dyldex`, `dyldex_all`, `kextex`, and `kextex_all` are now present.
- Positive result: `DyldContext` can parse `/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e`, loads `3646` images, and locates `AppleNeuralEngine` at `0x19f90e000`, `ANEServices` at `0x19e68b000`, `ANECompiler` at `0x222d54000`, `ANEClientSignals` at `0x22ffa3000`, and `ANECompiler.framework/libORTools.dylib` at `0x22ffa5000`.
- Failed result: `dyldex` extraction of `AppleNeuralEngine.framework/Versions/A/AppleNeuralEngine` under conda Python `3.13.12` failed with `TypeError: can only concatenate str (not "int") to str`; no extracted Mach-O was produced under `mps/ANE/ida_inputs/dyld_extracted`.
- Available alternate runtimes: `/usr/bin/python3` is Python `3.9.6`; `/opt/homebrew/bin/python3` is Python `3.14.5`; Homebrew search exposes `jtool2`.
- Verdict: `inconclusive_extractor_installed_cache_parsed_extraction_failed`.
- Next target: retry dyld extraction in a compatible Python environment, preferably system Python `3.9`, or use Homebrew `jtool2`, then extract `AppleNeuralEngine` / `ANEServices` / `ANECompiler` for IDA import.

## 2026-06-23 AppleNeuralEngine target availability
- Evidence: `mps/ANE/.ane_runs/json/apple_neural_engine_target_availability_20260623.json` and CSV peer.
- Profiler context remains unchanged: transformer `24.871128999977373s`, transformer eval `19.867204998852685s`, transformer compile `1.9713062929804437s`, `time.pre.eval_sec=9.508778334013186s`, `time.axis_pack_sec=2.45342729089316s`, native max child RSS `1660.547MB`.
- Visible `/System/Library/PrivateFrameworks` framework directories for `ANECompiler`, `ANEServices`, `Espresso`, `CoreML`, `CoreMLOdie`, and `NeuralNetworks` do not contain executable binaries in `Versions/A`; SDK copies under CommandLineTools are `.tbd` stubs only.
- BootKC/SystemKC string checks still do not expose `AppleNeuralEngine`, `ANE_RestoreState`, `aneCmdSend`, `ANEFirmware`, or `ANEProgram` targets.
- Preboot dyld shared cache map at `/System/Volumes/Preboot/Cryptexes/OS/System/Library/dyld/dyld_shared_cache_arm64e.map` lists `/System/Library/PrivateFrameworks/AppleNeuralEngine.framework/Versions/A/AppleNeuralEngine`, plus `ANEServices`, `ANECompiler`, `ANEClientSignals`, `Espresso`, `NeuralNetworks`, and `CoreML`.
- Dyld cache strings include `ANEVirtualClient`, `_ANEProgramForEvaluation processRequest`, `_ANEProgramIOSurfacesMapper`, `programHandle`, `programInstance`, `intermediateBufferHandle`, compile/load/unload/evaluate dictionary method errors, and `ANEProgramProcessRequestDirect`.
- Extraction/import tooling is missing locally: no `dyld_shared_cache_util`, `dsc_extractor`, `dyld_extract`, `dyldex`, `jtool2`, or `ipsw` found.
- Verdict: `confirmed_apple_neural_engine_target_present_in_dyld_cache_extraction_missing`.
- Next target: acquire or build a dyld shared cache extraction/import path for `AppleNeuralEngine.framework`, `ANEServices.framework`, and `ANECompiler.framework`, then open extracted `AppleNeuralEngine` in IDA for selector/state-path analysis.

## 2026-06-23 non-IOSurface lower-carrier evidence audit
- Evidence: `mps/ANE/.ane_runs/json/non_iosurface_lower_carrier_evidence_audit_20260623.json` and CSV peer.
- Profiler source: `mps/ANE/.ane_runs/json/current_best_component_bottleneck_ledger_20260623.json`; current dominant bucket remains transformer `24.871128999977373s`, transformer eval `19.867204998852685s`, `time.pre.eval_sec=9.508778334013186s`, `time.axis_pack_sec=2.45342729089316s`, native max child RSS `1660.547MB`.
- Evidence reviewed: host-visible lower-control dead-end blocker, lower attention/layout contract blocker, fused time+freq layout primitive compile matrix, non-H16 daemon carrier artifacts, resource400d0 materializer boundary, record1b8 send/completion blockers, selector wrapper carrier verdicts, and IOSurface closure.
- IDA sanity check in active `bootkc_iosurface_20260623`: no matching strings, functions, names, or text hits for `AppleNeuralEngine`, `ANE_RestoreState`, `aneCmdSend`, `aneFirmwareCommandSend`, `ANEFirmware`, `ANEProgram`, `ANE_Process`, `ANEProgramResource`, `ANEVirtual`, `ANEDevice`, `ANECompiler`, or `ANEServices`.
- Verdict: `blocked_no_non_iosurface_safe_lower_carrier_in_current_evidence`.
- This is not a global impossibility proof; it means current repository evidence plus the active BootKC session do not expose a safe non-IOSurface carrier/layout/materializer control that can reduce transformer segmentation without RSS growth.
- Next target: locate a concrete AppleNeuralEngine-containing binary/session or authorized lower-observation capability; otherwise maintain the lower-carrier blocker and avoid same-layer host-visible runtime sweeps.

## 2026-06-23 BootKC IOSurface superbuffer IDA entry
- Evidence: `mps/ANE/.ane_runs/json/bootkc_iosurface_superbuffer_ida_entry_20260623.json`.
- IDA session `bootkc_iosurface_20260623` is active for local copy `mps/ANE/ida_inputs/BootKernelExtensions.kc`; IDA health reports `auto_analysis_ready=true`, `hexrays_ready=true`, strings cache size `136393`.
- Recovered key symbols: `_kIOSurfaceAllocateFromSuperbuffer` at `0xffffff8002ba7118`, `_kIOSurfaceSuperbuffer` at `0xffffff8002ba7120`, `IOSurfaceRootUserClient::create_surface` at `0xffffff8002b9492c`, `IOSurfaceRoot::create_surface_internal` at `0xffffff8002b8f8b2`, `IOSurface::init` at `0xffffff8002b7cd66`, `IOSurface::parse_properties` at `0xffffff8002b7d2b0`.
- Xrefs show `_kIOSurfaceAllocateFromSuperbuffer` is consumed by `IOSurfaceRootUserClient::create_surface`, where it is read as an `OSNumber`, treated as a memory-pool id, checked through `IOSurfaceMemoryPoolBunch::getPool` / `IOSurfaceMemoryPool::taskCanUsePool`, then the path calls `IOSurfaceRoot::create_surface_internal`.
- `IOSurfaceRoot::create_surface_internal` only allocates an `IOSurface`, calls `IOSurface::init`, registers the surface, and waits for async releases. `IOSurface::init` stores properties, allocates surface id/shared memory, calls `IOSurface::parse_properties`, then allocates backing memory.
- Verdict: `confirmed_bootkc_iosurface_superbuffer_path_recovered_static_entry`.
- Current interpretation: BootKC IOSurface superbuffer / memory-region follow-up is closed as a supporting allocation layer, not an ANE transformer carrier or accepted-state/materializer control point.
## 2026-06-23 BootKC IOSurface memory-region closure
- Evidence: `mps/ANE/.ane_runs/json/bootkc_iosurface_memory_region_closure_20260623.json` and CSV peer.
- IDA session: `bootkc_iosurface_20260623`; `auto_analysis_ready=true`, `hexrays_ready=true`, strings cache `136393`.
- `IOSurfaceRoot::lookupMemoryRegion` (`0xffffff8002b8fc1e`) only locks root state, waits for pending async releases, dictionary-lookups an `OSString` key, safe-casts to `IOSurfaceMemoryRegion`, retains, and returns it.
- `IOSurfaceMemoryPoolBunch::getPool` (`0xffffff8002b997d2`) is a pool-id linked-list lookup under a shared RW lock; `IOSurfaceMemoryPool::taskCanUsePool` (`0xffffff8002b9c134`) is owner/kernel/entitlement access control including `com.apple.private.iosurfaceinfo`.
- `IOSurfaceRoot::newWiredMemoryDescriptorFromMemoryPool` calls `getMemoryPoolBunch -> getPool -> taskCanUsePool -> IOSurfaceMemoryPool::newWiredMemoryDescriptorWithLength`; `IOSurface::allocate` consumes the result as backing memory descriptor/mapping setup.
- `IOSurfaceAllocateFromSuperbuffer` xrefs are limited to `IOSurface::parse_properties` at `0xffffff8002b809a8` plus the key global `0xffffff8002ba7118`; `IOSurfaceSuperbuffer` has only key global `0xffffff8002ba7120`.
- Scoped searches found no `AppleNeuralEngine`, `ANE_RestoreState`, `aneCmdSend`, `IOProcessor`, `Program`, `Command`, `Restore`, accepted-state, or materializer consumer tied to the IOSurface path.
- Verdict: `confirmed_iosurface_superbuffer_is_supporting_allocation_layer_not_transformer_carrier`.
- Policy: do not repeat IOSurface/superbuffer probing unless new ANE-specific evidence connects this layer to transformer accepted-state/materializer control.
- Next target: inspect `IOSurface::parse_properties` plus `IOSurfaceRoot::lookupMemoryRegion` / `IOSurfaceMemoryPoolBunch::getPool`; decide whether superbuffer/memory-region interpretation has any deeper semantic consumer relevant to ANE accepted-state/materialization, or close IOSurface as a supporting allocation layer.

## 2026-06-23 lower-layer transformer target audit
- Evidence: `mps/ANE/.ane_runs/json/lower_layer_transformer_target_audit_20260623.json`.
- Current evidence still exposes no safe host-writable compile-only carrier/layout/materialization field that can reduce q240 transformer segmentation. The missing authority remains below visible descriptor / ANEServices / H16 send-reply shells, in firmware-private or IOProcessor/interrupt-driven shared-state writeback for `record+0x1b8`, `process+0x203fc == 2`, or equivalent accepted-state/materializer fields.
- IDA MCP is reachable but currently has no open IDB sessions. Standard private framework binary paths were not found in the quick probe. Current-machine kernel collections exist at `/System/Library/KernelCollections/BootKernelExtensions.kc` and `/System/Library/KernelCollections/SystemKernelExtensions.kc`.
- Quick KC string scan found IOSurface/IOSurfaceRoot in `BootKernelExtensions.kc`, but did not find AppleNeuralEngine / `ANE_RestoreState` / `aneCmdSend` strings in the scanned kernel collections or Preboot KCs.
- Verdict: `confirmed_no_new_safe_compile_only_lower_target_in_current_evidence`.
- Policy: do not resume descriptor field guessing, ANEServices selector3/4/6/9 patching, ready-gate spoofing, visible `aneCmdSend` / typed-completion shell probing, qchunk resweeps, SDPA promotion, non-transformer grouping, or retained-handle probes without new evidence.
- Next target: create/adopt an IDA session for `/System/Library/KernelCollections/BootKernelExtensions.kc` and statically inspect IOSurfaceRoot / `IOSurfaceAllocateFromSuperbuffer` as the currently locatable lower-layer entry. If an AppleNeuralEngine.kext path is later resolved, prefer selector-9 dispatch/state-path analysis.

## 2026-06-23 band split grouping compile-gate probe
- Evidence: `mps/ANE/.ane_runs/json/band_split_grouping_compile_gate_verdict_20260623.json`.
- Baseline band split bucket remains `0.525994208001066s` on `test_clean.m4a`, with fused layout `multi_output_l2`, `17` groups, `62` outputs, `max_outputs_per_group=4`, compile/load `0.30077737307874486s`, eval `0.14639436668949202s`, write `0.06586439738748595s`, route `load_cache_skip_source_write`.
- Minimal larger-group probe `--private-ane-fused-band-split-max-outputs 5` fails at `band_split_l2_fused_0_5` with `InvalidMILProgram`; corroborating `max_outputs=8` fails at `band_split_l2_fused_0_8` with `InvalidMILProgram`.
- Verdict: `falsified_band_split_larger_grouping_not_promotable_compile_failed`.
- Policy: keep fused band split `max_outputs_per_group=4`. Do not rerun larger band-split grouping without a new MIL/layout hypothesis.
- Next target: stop treating sub-second non-transformer buckets as primary acceleration targets. Further meaningful speedup requires new private lower-layer transformer evidence for a carrier/layout/materialization control point that reduces segmented transformer eval/load without increasing RSS.

## 2026-06-23 ISTFT/IRFFT batch-channel probe
- Evidence: `mps/ANE/.ane_runs/json/istft_irfft_batch_channel_verdict_20260623.json`.
- Baseline ISTFT bucket remains `0.5914230409543961s` on `test_clean.m4a`, stage `private_ane_irfft_cpu_overlap_add`, route `load_cache_skip_source_write`, compile `0`, eval `0.29928666388150305s`, overlap-add `0.024029207008425146s`, max RSS `1167.75MB`.
- Minimal ANE-aligned probe `--private-ane-stft-istft-batch-channels` reached `istft_start` after releasing aux handles, then failed compiling `irfft_0_128_b2` with `InvalidMILProgram`.
- Verdict: `falsified_istft_batch_channel_not_promotable_compile_failed`.
- Policy: keep ISTFT on the existing per-channel ANE IRFFT + CPU overlap-add path. Do not promote batch-channel ISTFT or rerun it without a different IRFFT MIL/layout hypothesis. GPU ISTFT is diagnostic-only because the target backend is ANE, not GPU.
- Next target: probe the remaining band split bucket (`0.525994208001066s`) for a memory-neutral grouping or load/cache reduction; if closed, non-transformer buckets are too small and the next meaningful speedup requires new private lower-layer transformer evidence.

## 2026-06-23 closed-route priority ledger and mask grouping
- Evidence: `mps/ANE/.ane_runs/json/closed_route_priority_ledger_20260623.json`.
- Best stable q240+skip-source baseline remains `27.649230875016656s`; transformer is `24.61669554200489s`, leaving only about `3.032535333011765s` non-transformer wall.
- Remaining non-transformer buckets in the best stable run: mask `0.8139545s`, ISTFT `0.5914230s`, band split `0.5259942s`, final norm `0.2267059s`, STFT `0.0793139s`.
- Mask grouping was the largest plausible non-transformer knob, but `private_ane_fused_mask_estimator_max_outputs=3` fails at `mask_fused_0_3 InvalidMILProgram`, and `max_outputs=4` fails at `mask_fused_0_4 InvalidMILProgram`.
- Verdict: `confirmed_transformer_host_visible_routes_exhausted_for_now_mask_grouping_closed`.
- Next target: probe the ISTFT/IRFFT host-visible bucket (`0.591423s`) for a memory-neutral reduction; expected upside is sub-second, so further major transformer speedups now need new private lower-layer evidence.

## 2026-06-23 deferred transformer free-GC diagnostic
- Evidence: `mps/ANE/.ane_runs/json/host_visible_overhead_defer_transformer_free_gc_probe_20260623.json`.
- Code change: default-off env diagnostic `PYMSS_PRIVATE_ANE_DEFER_TRANSFORMER_FREE_GC=1` skips forced Python `gc.collect()` after transformer handle-free while still freeing native ANE handles immediately.
- Narrow transformer-only probe was exact (`max_abs=0`) and removed `0.245011542s` GC in the candidate, with wall `15.3080775s -> 15.157188125s`.
- Not promotable: candidate `maxrss` increased `1447.0MB -> 1934.25MB` (`+487.25MB`) in the narrow run. This violates the no-memory-growth rule.
- Verdict: `falsified_defer_transformer_free_gc_not_promotable_narrow_probe`.
- Policy: keep the env diagnostic default-off. Do not enable by default or full-path promote unless a later paired supervisor run proves no RSS/swap increase.

## 2026-06-23 lower attention carrier / layout-contract verdict
- Evidence: `mps/ANE/.ane_runs/json/lower_attention_carrier_layout_contract_verdict_20260623.json`.
- Existing RE notes do not expose a safe host-visible lower-segmentation attention carrier: the descriptor / ANEServices wrapper / H16-visible send-reply route is already a confirmed dead end for accepted-state/materializer control, and RT operation-description layouts are internal lower records, not current compile inputs.
- Public attention/SDPA evidence is not a path to peak: explicit attention sweep has successful cases but best quick success is about `0.446683 TFLOPS` / `2.4816%` utilization; SDPA/builtin SDPA remains low-utilization/high-compile and has known runtime eval boundaries.
- Verdict: `blocked_no_safe_lower_attention_carrier_or_layout_contract_exposed`.
- Policy: do not run qchunk resweeps, generic SDPA integration, public explicit attention promotion, retained transformer handles, or host-visible descriptor/selector lower-carrier probes without new evidence.
- Next target: pivot back to host-visible memory-neutral overheads that are still measurable and controllable: per-axis layout/write/read costs and q240 time.pre eval attribution from existing timing rows.

## 2026-06-23 time-axis attention_pre segmentation static verdict
- Evidence: `mps/ANE/.ane_runs/json/time_attention_pre_segmentation_static_verdict_20260623.json`.
- Generated qchunk MIL counts for shape `batch=62, seq=960`: q240 has 4 branches / 8 matmuls / 4 softmaxes / 8 slices; q480 has 2 branches / 4 matmuls / 2 softmaxes / 6 slices; q960 is a single huge branch but fails compile.
- Existing sweep remains decisive: q240 and q480 are the only compiling qchunk variants, and q240 is faster/lower-memory than q480. q64/q120/q160/q192/q320/q960 fail with `InvalidMILProgram`.
- Micro evidence confirms q480 is not better despite fewer branches: b62 q240 eval `0.18706375s`, q480 eval `0.199159666s`; q240 compile `4.803896125s`, q480 compile `10.145314208s`.
- Existing SDPA evidence is not promotable as-is: SDPA/built-in SDPA remains low utilization/high compile in this corpus and has known runtime eval boundaries, so do not pivot to SDPA without a new shape-specific hypothesis.
- Verdict: `confirmed_q240_manual_tiled_attention_pre_is_current_local_minimum`.
- Next target: inspect lower-segmentation attention carrier or ANE-side layout contract below the qchunk parameter; do not repeat qchunk sweeps or generic SDPA probes.

## 2026-06-23 native bridge load-cache materialization feasibility
- Evidence: `mps/ANE/.ane_runs/json/native_bridge_load_cache_materialization_feasibility_20260623.json`.
- Source inspection confirms current Python/bridge fast path is already exhausted for safe same-identifier reuse: `load_cache_skip_source_write` only applies when the current `_ANEInMemoryModel.hexStringIdentifier` directory has complete `model.mil`/weight files with matching sizes.
- Python exposes load-cache vs uncached compile only; it does not expose an identifier override, source-root alias, or aggregate/component materialization reuse API.
- Prior artifacts prove why this matters: surface-handoff pre/gate component identifiers have zero overlap with baseline aggregate identifiers, while the route still stays `load_cache_skip_source_write`; the regression is materialization/tmpdir/load QoS, not fallback.
- Verdict: `confirmed_python_bridge_fast_path_exhausted_native_materialization_required`.
- Policy: keep `surface_handoff_gate_ffn` closed as a Python/runtime-route promotion path. Revisit only after native/private bridge RE finds a memory-neutral materialization identity change; do not use retained transformer handles or runtime-clone caching because that violates the no-RSS-growth constraint.
- Next target: return to current-best ledger and attack `time.pre.eval_sec≈9.51s` / time-axis `attention_pre` segmentation directly.

## 当前结论
- 2026-06-23 `surface_handoff_gate_ffn` fast-path feasibility:
  - Evidence: `mps/ANE/.ane_runs/json/surface_handoff_fast_path_feasibility_20260623.json`, `mps/ANE/.ane_runs/csv/surface_handoff_fast_path_feasibility_20260623.csv`.
  - Candidate pre component identifiers: `24` unique, overlap with baseline aggregate identifiers `0`.
  - Candidate gate component identifiers: `24` unique, overlap with baseline aggregate identifiers `0`.
  - Candidate FFN and aggregate identifiers overlap baseline aggregate identifiers `24/24`, but still incur tmpdir/load_qos overhead.
  - Bridge load-cache boundary is keyed by exact MIL, weights, input sizes, and output sizes (`compile_multi_inputs_outputs -> load_multi_inputs_outputs`), so reusing aggregate tmpdirs for pre/gate would be unsafe without native bridge identity/materialization changes.
  - Verdict: `blocked_surface_handoff_fast_path_requires_native_identity_or_materialization_change`.
  - Policy: close surface-handoff as a Python/runtime-route promotion path. Only revisit via native bridge/RE work on load-cache materialization identity, not by rerunning full-path route toggles.

- 2026-06-23 `surface_handoff_gate_ffn` compile/load attribution:
  - Evidence: `mps/ANE/.ane_runs/json/surface_handoff_compile_load_attribution_20260623.json`, `mps/ANE/.ane_runs/csv/surface_handoff_compile_load_attribution_20260623.csv`.
  - The full-path policy artifact proved the route is exact and improves read/write, but is slower and increases RSS. This attribution explains why.
  - Cache route is unchanged: candidate component routes remain `load_cache_skip_source_write`, so this is not fallback or cache-miss behavior.
  - Regression is concentrated in component materialization: pre tmpdir `+0.5376s`, gate tmpdir `+0.3262s`, FFN tmpdir `+0.1956s`, gate load_qos `+0.1427s`, FFN load_qos `+0.1474s`.
  - Interpretation: surface handoff changes the pre/gate/ffn component identity/materialization pattern. Its read/write savings are real, but erased by extra tmpdir/load_qos work and RSS growth.
  - Verdict: `confirmed_surface_handoff_regression_is_component_materialization_not_cache_route`.
  - Policy: do not retry surface-handoff promotion unless a bridge-level fast path can reuse existing aggregate tmpdir/source-completeness without extra materialization or RSS.

- 2026-06-23 `surface_handoff_gate_ffn` full-path policy result:
  - Evidence: `mps/ANE/.ane_runs/json/surface_handoff_gate_ffn_fullpath_policy_20260623.json`, `mps/ANE/.ane_runs/csv/surface_handoff_gate_ffn_fullpath_policy_20260623.csv`, transformer-only raws `benchmark_results/private_ane/time_pre_surface_handoff_gate_ffn_raw_20260623.json` and `benchmark_results/private_ane/time_pre_surface_handoff_gate_ffn_chunks4_raw_20260623.json`.
  - Full-path candidate: `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_surface_handoff_20260623.json`, child meta `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_surface_handoff_20260623.private_ane_child/meta.json`.
  - Baseline: `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_rerun_20260623.private_ane_child/meta.json`.
  - Correctness: full-path outputs exact versus baseline (`max_abs=0`, `mean_abs=0`, `num_checked=6983680`).
  - Positive signal: transformer eval improved `-0.4985272499034181s`; gate read was eliminated (`ane_gate_read_sec -0.3813587502227165s`); FFN write was eliminated (`ane_ffn_write_sec -0.16588275792310014s`); total ANE read/write improved.
  - Blocking result: wall worsened `27.649230875016656s -> 30.064417415997013s` (`+2.4151865409803577s`), transformer total worsened `+1.3006933739525266s`, compile/load worsened `+1.6844570820685476s`, and max RSS increased `+181.828125MB`.
  - Verdict: `falsified_surface_handoff_gate_ffn_not_promotable_full_path`; keep default-off only, do not promote under no-memory-increase rule.

- 2026-06-23 two-input gate compile feasibility for forced layer-1 q240:
  - Evidence: `mps/ANE/.ane_runs/json/time_pre_q240_two_input_gate_compile_20260623.json`, `mps/ANE/.ane_runs/csv/time_pre_q240_two_input_gate_compile_20260623.csv`, raw `benchmark_results/private_ane/time_pre_q240_two_input_gate_compile_raw_20260623.json`.
  - Result: `gated_pre_gate_two_input`, `forced_pre_gate_two_input`, `gated_full_two_input`, and `forced_full_two_input` all fail before validation with `RuntimeError: ANE compile failed`; stderr reports `InvalidMILProgram`.
  - Verdict: `falsified_two_input_gate_compile_infeasible_for_layer1_q240`.
  - Policy: forced all-layer q240 tiled time-axis `attention_pre` is closed as a promotion family. Evidence chain: standalone `pre` exact, `pre_gate` non-exact, materialized packed boundary still non-exact, independent two-input gate compile-infeasible.
  - Next target must be a different memory-neutral `time.pre` reduction path, not additional forced all-layer q240 promotion attempts.

- 2026-06-23 materialized pre-to-gate boundary sweep for forced layer-1 q240:
  - Evidence: `mps/ANE/.ane_runs/json/time_pre_q240_gate_boundary_pack_sweep_20260623.json`, `mps/ANE/.ane_runs/csv/time_pre_q240_gate_boundary_pack_sweep_20260623.csv`, raw `benchmark_results/private_ane/time_pre_q240_gate_boundary_pack_sweep_raw_20260623.json`.
  - Validation policy: exactness tolerance remains `0.0`; both candidate rows have `validation_ok=0`, so promotion is terminally blocked.
  - Result: packed2 default forced-vs-gated pre_gate repeat failed with `max_abs=0.0009765625`, `mean_abs=2.871796800363313e-09`, `num_checked=14887936`.
  - Result: materialized packed-buffer gate input (`private_ane_bridge_pack_gate=0`) failed identically with `max_abs=0.0009765625`, so the mismatch is not caused by the packed2 bridge handoff alone.
  - Performance note: materialized pack adds explicit `att_pack_sec≈0.027s` in repeat rows and does not improve eval; it is both non-exact and not performance-promising.
  - Verdict: `falsified_materialized_pre_gate_boundary_does_not_restore_exactness`.
  - Policy: keep forced all-layer q240 diagnostic-only; next candidate is two-input gate or static gate MIL/input-order inspection. If that also fails, close this forced-all-layer q240 family.

- 2026-06-23 forced layer-1 q240 scope-localization result:
  - Evidence: `mps/ANE/.ane_runs/json/time_pre_q240_forced_scope_localization_20260623.json`, `mps/ANE/.ane_runs/csv/time_pre_q240_forced_scope_localization_20260623.csv`, raw `benchmark_results/private_ane/time_pre_q240_forced_scope_localization_raw_20260623.json`.
  - Validation policy: exactness tolerance remains `0.0` for this route-family promotion gate; validation failure is terminal per `mps/ANE/experiments/results/chain_validation_suite.md`.
  - Result: `probe_handle_scope=pre` is exact for forced vs gated layer-1 q240 (`max_abs=0`, `mean_abs=0`, `num_checked=14887936`).
  - Result: `probe_handle_scope=pre_gate` diverges (`max_abs=0.0009765625`, `mean_abs=2.871796800363313e-09`, `num_checked=14887936`), and full scope diverges the same way.
  - Verdict: `confirmed_forced_q240_drift_starts_at_pre_gate_not_pre_only`; the standalone tiled `attention_pre` seam is not the immediate mismatch source, but the pre-to-gate composition path fails exactness.
  - Policy: forced all-layer q240 stays diagnostic-only and must not be promoted or full-path tested unless gate-consumption exactness is recovered without increasing RSS/handle families.

- 2026-06-23 warm-cache and correctness localization for forced all-layer q240 tiled time-axis `attention_pre`:
  - Warm-cache artifact: `mps/ANE/.ane_runs/json/time_pre_q240_gated_vs_forced_warm_loadcache_20260623.json`, CSV peer, raw `benchmark_results/private_ane/time_pre_q240_gated_vs_forced_loadcache_raw_20260623.json`.
  - Localization artifact: `mps/ANE/.ane_runs/json/time_pre_q240_forced_correctness_localization_20260623.json`, CSV peer, raw `benchmark_results/private_ane/time_pre_q240_forced_correctness_localization_raw_20260623.json`.
  - Warm load-cache repeat result: forced all-layer q240 was narrowly faster than gated q240 (`1.1323377499938942s -> 1.0488913750159554s`, delta `-0.08344637497793883s`), but the gain was almost entirely load/cache (`load_or_compile -0.08286800101632252s`), not eval (`eval -0.00020099995890632272s`).
  - Correctness result: forced output differs from gated output at warm repeat (`max_abs=0.0078125`, `mean_abs=1.3825006028866937e-08`, `p99_abs=0`), so the route is not promotable under exactness policy.
  - Localization result: stop-after-layer 1 is exact (`max_abs=0`), stop-after-layer 2 is non-exact (`max_abs=0.0078125`), proving the first forced layer beyond the default q240 gate introduces the drift.
  - Policy: keep `PYMSS_PRIVATE_ANE_FORCE_TILED_TIME_ATTENTION_PRE_ALL_LAYERS=1` diagnostic-only; do not run full-path promotion for forced all-layer q240 unless layer-1 exactness is recovered without increasing RSS/handle families.

- 2026-06-23 forced all-layer q240 tiled time-axis `attention_pre` layer-extension probe:
  - Current short-term target remains `time.pre.eval_sec≈9.51s`, the largest memory-safe optimization target in the q240+skip-source path.
  - Minimal probe command: `PYMSS_PRIVATE_ANE_FORCE_TILED_TIME_ATTENTION_PRE_ALL_LAYERS=1 /Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --compare tiled --layers 2 --chunks 1 --q-chunk 240 --probe-stop-after-axis time --probe-stop-after-layer 2 --cache-tmpdir benchmark_results/private_ane/ane_tmp_loadcache --out benchmark_results/private_ane/time_axis_tiled_pre_layer_extension_forced_raw_20260623.json`.
  - Evidence: `mps/ANE/.ane_runs/json/time_axis_tiled_pre_layer_extension_probe_20260623.json`, `mps/ANE/.ane_runs/csv/time_axis_tiled_pre_layer_extension_probe_20260623.csv`, raw `benchmark_results/private_ane/time_axis_tiled_pre_layer_extension_forced_raw_20260623.json`.
  - Result: forced all-layer q240 compiled and ran in the two-layer/time-axis seam, so the old layer 1+ compile-fail comment is stale for this exact seam.
  - Verdict: `falsified_forced_layer_extension_not_promotable` because wall worsened `6.85981937503675s -> 13.884507624956314s` (`+7.0246882499195635s`, `+102.40%`), `max_abs=0.0078125`, summed load/compile grew `5.851932709047105s -> 12.911055126052815s`, and eval only improved `0.6462564579560421s -> 0.6364357090205885s`.
  - Policy: keep the diagnostic override default-off; do not promote forced all-layer tiled `attention_pre`, and do not run full-path promotion unless a later probe proves exact output, lower wall, and no RSS increase in a narrow seam.

- 2026-06-23 已生成 current-best component bottleneck ledger：
  - 新证据：
    - `mps/ANE/.ane_runs/json/current_best_component_bottleneck_ledger_20260623.json`
    - `mps/ANE/.ane_runs/csv/current_best_component_bottleneck_ledger_20260623.csv`
  - source：`benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_component_fields_fixed_20260623.json`
  - current observable baseline：wall `28.357753333984874s`，transformer `24.871128999977373s`，transformer compile/load `1.9713062929804437s`，transformer eval `19.867204998852685s`，native max child RSS `1660.547MB`。
  - top contributors：`time.eval_sec=13.97083224792732s`，`time.pre.eval_sec=9.508778334013186s`，`freq.eval_sec=5.896372750925366s`，`freq.pre.eval_sec=3.064940589829348s`，`time.axis_pack_sec=2.45342729089316s`。
  - decision：next target is `time_axis_attention_pre_eval_or_segmentation`。freq unpadded route 已因 RSS 放弃；q_chunk sweep 已证明当前模板里 q240 最优，因此下一轮需要找非 q_chunk 或更低层的 time-axis pre segmentation/eval overhead reduction。
- 2026-06-23 已完成 unpadded freq route repeated full-path promotion policy：
  - 新证据：
    - `mps/ANE/.ane_runs/json/unpadded_freq_route_repeated_fullpath_policy_20260623.json`
    - `mps/ANE/.ane_runs/csv/unpadded_freq_route_repeated_fullpath_policy_20260623.csv`
  - verdict=`abandon_unpadded_freq_padded_surface_route_for_promotion`。
  - repeated full-path pairs：3 组 q240 baseline vs unpadded-freq candidate。
  - wall time noisy：deltas `[+2.0167647909838706s, -0.4850976250017993s, -0.27936379198217764s]`，median `-0.27936379198217764s`，不能单独作为 promotion 依据。
  - native max child RSS consistently higher：deltas `[+7.967999999999847MB, +1.625MB, +2.436999999999898MB]`，median `+2.436999999999898MB`，3/3 positive；swap growth deltas all `0`。
  - policy：keep diagnostic route default-off only；do not run more full-path unpadded-freq probes unless there is a concrete memory-neutralization change. Under no-memory-increase constraint, route is abandoned even if some runs are faster.
  - implication：当前不再把 freq unpadded/padded-surface 作为主线加速；回到 dominant transformer bottlenecks：time-axis `ane_pre_eval` / segment overhead / load-cache materialization that can reduce wall without increasing RSS。
- 2026-06-23 已完成 component timing propagation fix + fixed-field full-path pair：
  - 新证据：
    - `benchmark_results/private_ane/transformer_layerwise_compare_l1_component_fields_fixed_20260623.json`
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_component_fields_fixed_20260623.json`
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_unpadded_freq_component_fields_fixed_20260623.json`
    - `mps/ANE/.ane_runs/json/full_path_component_timing_fixed_probe_20260623.json`
    - `mps/ANE/.ane_runs/csv/full_path_component_timing_fixed_probe_20260623.csv`
  - code fix：`pymss/modules/bs_roformer/private_ane.py` 的 timing row copy filter 从只接受 `bridge_profile_*` / `*_bridge_profile_route` 改为接受所有包含 `"_bridge_profile_"` 的 component-level fields；同时 `_accumulate_named_bridge_compile_profiles` 兼容 prefixed/unprefixed profile keys。cheap one-layer sanity 证明 `pre/gate/ffn_bridge_profile_{tmpdir_sec,load_qos_sec,...}` 已进入 JSON（component numeric key count `57`）。
  - verdict=`confirmed_component_timing_observable_candidate_faster_but_rss_higher`。
  - paired full-path result：candidate faster，wall `28.357753333984874s -> 28.078389542002697s`（`-0.27936379198217764s`）；transformer `24.871128999977373s -> 24.672542624990456s`；compile/load `1.9713062929804437s -> 1.941294958058279s`；eval `19.867204998852685s -> 19.721921790973283s`。
  - component timing result：large tmpdir spike did not reproduce；time aggregate tmpdir delta `-0.001007043s`，freq aggregate tmpdir delta `+0.004393379s`。component deltas are small: gate tmpdir/load_qos slightly increases on both axes, while freq pre load_qos decreases (`0.169599s -> 0.158026s`) and contributes most local savings.
  - memory gate：candidate native max child RSS still increases (`1660.547MB -> 1662.984MB`, `+2.437MB`)，swap growth remains `0`；under current constraints this route is still not promotable.
  - 下一步：做 repeated paired full-path wall/RSS statistics for q240 baseline vs unpadded-freq candidate with fixed component fields；若 median/native RSS 仍高，放弃该 route；只有 wall 稳定更快且 RSS 不增时才补 waveform diff / promotion。
- 2026-06-23 已完成 full-path component tmpdir paired probe：
  - 新证据：
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_component_fields_20260623.json`
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_unpadded_freq_component_fields_20260623.json`
    - `mps/ANE/.ane_runs/json/full_path_component_tmpdir_probe_20260623.json`
    - `mps/ANE/.ane_runs/csv/full_path_component_tmpdir_probe_20260623.csv`
  - verdict=`inconclusive_tmpdir_regression_not_reproduced_component_fields_missing`。
  - paired result：candidate 比 paired baseline 更快，wall `28.631398500001524s -> 28.146300874999724s`（`-0.4850976250017993s`）；transformer `25.028575417003594s -> 24.615128291014116s`；compile/load `2.1034516260842793s -> 1.9211887069395743s`；eval `19.79764278809307s -> 19.65482775005512s`。
  - tmpdir regression did not reproduce：time aggregate `bridge_profile_tmpdir_sec` delta `-0.002022332s`，freq delta `+0.001286875s`；这与上一轮 spike 相矛盾，说明 tmpdir regression 至少有明显 run-to-run / filesystem-state variance。
  - observability gap：timing rows 仍未包含 numeric `pre/gate/ffn_bridge_profile_*` fields（component numeric key count `0`），只有 component route fields；因此本轮仍无法判断 spike 是 `pre`、`gate` 还是 `ffn`。
  - memory：candidate native max child RSS `1662.078MB` vs baseline `1660.453MB`，仍略增；即使本轮 faster，也不能 promotion。
  - 下一步：修复 component-level timing propagation 或在 native bridge/profile side 增加 per-component compile-profile export；若后续 paired full-path 多次不再复现 tmpdir spike，则把上一轮 spike 归类为 filesystem variance，改用 repeated full-path wall/RSS 评估该 route。
- 2026-06-23 已完成 full-path compile/load regression root-cause analysis：
  - 新证据：
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_rerun_20260623.json`
    - `mps/ANE/.ane_runs/json/full_path_compile_load_regression_root_cause_20260623.json`
    - `mps/ANE/.ane_runs/csv/full_path_compile_load_regression_root_cause_20260623.csv`
  - instrumentation change：`pymss/modules/bs_roformer/private_ane.py::_accumulate_named_bridge_compile_profiles` 现在为后续 probe 记录 component-level `pre/gate/ffn_bridge_profile_{tmpdir_sec,load_qos_sec,...}` 和 fast-load flags，避免只看到 aggregate tmpdir。
  - verdict=`confirmed_tmpdir_materialization_regression_not_cache_identity_miss`：用 current code 重新跑 matched q240+skip-source baseline，baseline 仍快（`27.649230875016656s`），candidate 仍慢（`29.920132166007534s`），所以不是旧 baseline stale。
  - hypothesis result：`partially_falsified_identifier_mismatch_confirmed_tmpdir_materialization`。24/24 rows 的 aggregate bridge identifier 相同，24/24 rows route 相同且仍为 `load_cache_skip_source_write`，bridge load-cache hits 均为 `123`；因此不像 cache-key proliferation / load-cache miss。
  - root-cause slice：candidate vs fresh baseline 的 regression 主要来自 `bridge_profile_tmpdir_sec`，time axis `0.019240s -> 0.584193s`（`+0.564953s`），freq axis `0.036937s -> 0.430766s`（`+0.393828s`）；`bridge_profile_load_qos_sec` 基本持平（time `-0.036845s`, freq `+0.005615s`）。这说明慢点在 bridge load-cache tmpdir/source-completeness materialization/checking，而不是 ANE `loadWithQoS` 或 eval compute。
  - eval evidence：time eval slightly improves (`14.073928s -> 14.038463s`)，freq eval worsens only `+0.148925s`；不能解释 full wall `+2.270901s`。
  - 下一步：用新增 component-level profile 字段做窄 probe，判断 tmpdir spike 来自 `pre`、`gate` 还是 `ffn` 的 source-completeness/tmpdir 检查；随后决定优化 bridge tmpdir/source completeness checks，或放弃该 route。
- 2026-06-23 attempted narrow seam `transformer-only --layers 12` is invalid for this route：
  - 新证据：`mps/ANE/.ane_runs/json/transformer_l12_component_profile_failed_20260623.json`
  - command：`/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --compare bridge-env --layers 12 --chunks 4 --q-chunk 240 --cache-tmpdir benchmark_results/private_ane/ane_tmp_loadcache --bridge-env PYMSS_PRIVATE_ANE_DIRECT_TIME_TO_FREQ_UNPADDED=1 --out benchmark_results/private_ane/transformer_layerwise_compare_l12_unpadded_freq_component_profile_20260623.json`
  - verdict=`failed_transformer_only_l12_not_valid_narrow_seam`：candidate 在 freq `attention_pre` cold compile 触发 `InvalidMILProgram`，不能作为 full-path tmpdir regression 的窄复现 seam。
  - implication：下一轮不要再用 12-layer transformer-only cold compile 来解释 full-path；只能用 one-layer sanity check 验证新增字段，或直接 rerun full-path candidate/control with component-level bridge profile fields。
- 2026-06-23 已完成 full-path unpadded freq MIL + padded surface validation：
  - 新证据：
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_unpadded_freq_20260623.json`
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_unpadded_freq_20260623.private_ane_child/native_supervisor.ndjson`
    - `mps/ANE/.ane_runs/json/full_path_unpadded_freq_padded_surface_validation_20260623.json`
    - `mps/ANE/.ane_runs/csv/full_path_unpadded_freq_padded_surface_validation_20260623.csv`
  - verdict=`falsified_full_path_unpadded_freq_padded_surface_not_promotable`：虽然 transformer-only exact 且小幅加速，但 full-path `test_clean.m4a` 变慢。
  - candidate vs current q240+skip-source baseline：wall `27.903367375023663s -> 29.920132166007534s`（`+2.0167647909838706s`, `+7.2277%`）；transformer total `24.631073875003494s -> 26.10294062498724s`；transformer eval `19.743745001906063s -> 19.805018791987095s`；transformer compile/load `1.944708043942228s -> 3.401522250031121s`（`+1.4568142060888931s`）。
  - localized effect：freq eval barely improves (`5.77694412501296s -> 5.766555875074118s`, `-0.01038824993884191s`)，但 freq compile/load regresses (`0.3787375020037871s -> 1.1959509160369635s`, `+0.8172134140331764s`)；time compile/load also regresses (`+0.6396007920557167s`)。
  - memory constraint：internal max RSS decreased (`1282.671875MB -> 1188.765625MB`) and swap used decreased (`2345.12MB -> 2305.12MB`), but native-supervisor max child RSS slightly increased (`1630.766MB -> 1638.734MB`, `+7.968MB`)；因此也不满足“不靠增内存加速”的 promotion standard。
  - correctness caveat：本 full-path probe 没有生成 waveform diff；但由于速度和 native RSS 已经不满足 promotion，暂不补做 waveform diff。若未来修复 compile/load regression 后再重新做 waveform exactness。
  - 下一步：解释 transformer-only 小幅收益为何在 full-path 变成 compile/load regression；重点查 load-cache identifier/cache-key proliferation、freq logical seq 62 + surface 64 是否导致新 artifact family、以及 full-path handle/materialization profile 字段。
- 2026-06-23 已完成 unpadded freq MIL + padded surface-byte integrated runtime probe：
  - 新证据：
    - `benchmark_results/private_ane/transformer_layerwise_compare_l1_unpadded_freq_padded_surface_20260623.json`
    - `benchmark_results/private_ane/transformer_layerwise_compare_l1_unpadded_freq_padded_surface_v2_20260623.json`
    - `mps/ANE/.ane_runs/json/unpadded_freq_padded_surface_runtime_probe_20260623.json`
    - `mps/ANE/.ane_runs/csv/unpadded_freq_padded_surface_runtime_probe_20260623.csv`
  - code change：`benchmark/private_ane_real_block_probe.py::_compile_block` 支持 `surface_seq`，`pymss/modules/bs_roformer/private_ane.py` 在 opt-in `private_ane_direct_time_to_freq_unpadded` freq 路径下使用 logical MIL `seq=62`，但保持 input/output eval surface byte stride 为 `FREQ_PAD=64`，并把 `surface_seq` 加入 transformer handle cache key避免合同碰撞。
  - first attempt verdict=`falsified_width62_eval_buffer_wrong_output`：只改 compile bytes、仍传 width-62 eval buffer 时不再 eval-fail，但输出错误（`max_abs=16.433837890625`, `checksum_delta=-752790.125`），证明 eval 输入/输出 surface stride 也必须实际 padded。
  - corrected transformer-only verdict=`confirmed_exact_small_gain_requires_fullpath_validation`：one-layer/four-chunk matched harness exact（`max_abs=0`, `mean_abs=0`, `p99_abs=0`, `checksum_delta=0`）。
  - corrected candidate vs load-cache primed control：wall `1.8288877500162926s -> 1.776548375026323s`（`-0.052339374989969656s`, `-2.8618%`）；eval `1.4064495000056922s -> 1.3764750830014236s`；ANE eval-only `1.1553673749149311s -> 1.1280071689398028s`；freq eval `0.4400552920124028s -> 0.35807879199273884s`；freq `axis_pack` `0.05522933401516639s -> 0.0s`；total `axis_pack` slightly worsened `0.09679858398158103s -> 0.10237233500811271s` due surrounding time-path/noise.
  - memory constraint：transformer-only current RSS delta did not increase in the candidate run (`load_cache_prime=-202.53125MB`, `candidate=-79.75MB`), but this is not full-path max RSS/swap evidence；不能据此 promotion。
  - 下一步：必须做 full-path `test_clean.m4a` validation with q240 + skip-source + direct unpadded freq padded surfaces，记录 waveform exactness、wall、transformer eval/axis_pack、native-supervisor max RSS 和 swap；未通过 full-path 前不得默认启用。
- 2026-06-23 已完成 cache-hit skip-source-write shortcut full-path validation：
  - 新证据：
    - `benchmark_results/private_ane/transformer_layerwise_compare_l1_skip_source_write_20260623.json`
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_skip_source_write_20260623.json`
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_skip_source_write_20260623_profile/profile_summary.json`
    - `benchmark_results/private_ane/test_clean_1s_skip_source_write_flag_smoke_20260623.json`
    - `mps/ANE/.ane_runs/json/skip_source_write_cache_hit_fullpath_20260623.json`
    - `mps/ANE/.ane_runs/csv/skip_source_write_cache_hit_fullpath_20260623.csv`
  - code change：`mps/maderix_ANE/bridge/ane_bridge.m` 新增 opt-in `ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT=1`；`benchmark/private_ane_test_clean_benchmark.py` 新增 `--private-ane-skip-source-write-on-cache-hit`；`pymss/modules/bs_roformer/private_ane.py`、`common.py`、`separator.py` 已接入 `private_ane_skip_source_write_on_cache_hit`。
  - verdict=`confirmed`：full-path wall 从 current warm-cache diagnostic `35.891103s` 降到 `31.337585s`，改善 `4.553518s` / `12.69%`；RTF 从 `0.906569` 到 `0.791553`。
  - transformer `load_or_compile_wall_sec` 从 `5.942209s` 降到 `3.987150s`，改善 `1.955059s` / `32.90%`。
  - transformer rows route 全部变为 `load_cache_skip_source_write`；`bridge_profile_file_write_sec` 从 `0.573875s` 降到 `0`；`bridge_profile_tmpdir_sec` 从 `1.904578s` 降到 `1.284876s`；`load_qos` 基本不变。
  - memory constraint：internal max RSS `1351.219MB -> 1348.109MB`，max swap `2408MB -> 2392MB`，未通过增加内存换速度。
  - correctness：transformer-only one-layer/four-chunk probe exact (`max_abs=0`, `checksum_delta=0`)；full-path waveform validation 已完成且两 stem exact (`max_abs=0`, `mean_abs=0`, `num_checked=6983680`)。Artifact: `mps/ANE/.ane_runs/json/skip_source_write_fullpath_waveform_validation_20260623.json` and CSV peer.
  - benchmark default：`benchmark/private_ane_test_clean_benchmark.py` 已把 `private_ane_skip_source_write_on_cache_hit=True` 作为 experimental benchmark 默认项；1s default smoke 使用了 `load_cache_skip_source_write` route。
  - 下一步：继续处理剩余主因：transformer eval loop / `ane_pre_eval` / `axis_pack` / segment lifecycle / read-write；不要再把 full-path correctness 当作 skip-source-write 的 blocker。
- 2026-06-23 internal `/tmp` cache locality probe result:
  - 新证据：
    - `mps/ANE/.ane_runs/json/internal_tmp_cache_locality_probe_20260623.json`
    - `mps/ANE/.ane_runs/csv/internal_tmp_cache_locality_probe_20260623.csv`
    - `benchmark_results/private_ane/test_clean_1s_internal_tmp_cache_probe_20260623.private_ane_child/child.log`
    - `benchmark_results/private_ane/test_clean_1s_internal_tmp_cache_probe_20260623.private_ane_child/private_ane_trace.ndjson`
  - verdict=`inconclusive`：把现有 `1.0G` / `1129`-file load-cache 复制到 `/tmp/pymss_ane_tmp_loadcache_probe_20260623` 后，STFT preload 仍命中 copied load-cache (`bridge_profile_route=load_cache`, hit delta `1`, miss delta `0`)，但 1s full-path run 在到达 transformer 前于 `band_split_l2_0` cold compile 触发 `InvalidMILProgram`。
  - 结论：该 probe 不能作为 `/tmp` cache locality 的 speed verdict，也不能推广到 transformer；它证明 full-pipeline cache-path 移动会被 non-transformer cache portability / cold-compile failure 污染。下一轮必须用 transformer-only integrated harness 直接测 transformer `load_or_compile`、`ane_pre_eval`、`axis_pack`、read/write、lifecycle。
- 2026-06-23 transformer-only integrated harness skip-source validation:
  - 新证据：
    - `benchmark_results/private_ane/transformer_layerwise_compare_l1_skip_source_probe_20260623.json`
    - `mps/ANE/.ane_runs/json/transformer_only_skip_source_harness_probe_20260623.json`
    - `mps/ANE/.ane_runs/csv/transformer_only_skip_source_harness_probe_20260623.csv`
  - diagnostic code change：`benchmark/private_ane_transformer_layerwise_compare.py` 现在在 load-cache probe 中保留 tmpdir/source files，并把 candidate bridge env `ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT=1` 映射为 `model.private_ane_skip_source_write_on_cache_hit=True`，使 transformer-only harness 能真正走 `load_cache_skip_source_write` route。
  - verdict=`confirmed`：one-layer/four-chunk transformer-only candidate vs primed load-cache wall `1.978956s -> 1.864193s`，改善 `0.114763s` / `5.80%`；`bridge_profile_file_write_sec=0.085870s -> 0`；`load_or_compile=0.312161s -> 0.227733s`。
  - correctness：exact (`max_abs=0`, `mean_abs=0`, `checksum_delta=0`)。
  - memory constraint：current RSS delta 未增加 (`2.609MB -> 1.188MB`)；`ru_maxrss` 是进程历史峰值，会随同进程多 variant 单调上升，不能作为 candidate current-memory 回退证据。
  - 下一步：用同一 transformer-only harness 做 `bridge_pack_gate` / layout ablation，直接观察 `axis_pack`、`ane_pre_eval`、read/write、eval 和 correctness；不要再用 full-pipeline `--private-ane-no-bridge-pack-gate`，该路径已被 band-split compile failure 污染。
- 2026-06-23 transformer-only `bridge_pack_gate=0` layout ablation:
  - 新证据：
    - `benchmark_results/private_ane/transformer_layerwise_compare_l1_bridge_pack_gate_off_20260623.json`
    - `mps/ANE/.ane_runs/json/transformer_only_bridge_pack_gate_ablation_20260623.json`
    - `mps/ANE/.ane_runs/csv/transformer_only_bridge_pack_gate_ablation_20260623.csv`
  - diagnostic code change：`benchmark/private_ane_transformer_layerwise_compare.py` 支持 candidate env `PYMSS_PRIVATE_ANE_BRIDGE_PACK_GATE=0/1`，用于 transformer-only layout ablation。
  - verdict=`falsified`：candidate exact 且命中 `load_cache_skip_source_write`，但它没有降低 layout/pre-eval；相对 primed load-cache，`axis_pack +0.002769s`、`ane_pre_eval +0.001726s`、eval `+0.069799s`，current RSS delta `+176.391MB`；相对上一轮 skip-source/pack-on candidate，wall 还慢约 `+0.041s`。
  - 结论：不要推广 `bridge_pack_gate=0`，也不要再用 full-pipeline no-bridge-pack 结果推断 transformer layout；下一步应直接分析 `ane_pre_eval` 的 shape / segment / dispatch 路径。
- 2026-06-23 full-path tiled q240 + skip-source validation:
  - 新证据：
    - `benchmark_results/private_ane/transformer_layerwise_compare_l1_tiled_pre_q240_skip_source_20260623.json`
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_skip_source_explicit_control_20260623.json`
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_20260623.json`
    - `mps/ANE/.ane_runs/json/transformer_only_tiled_pre_q240_skip_source_probe_20260623.json`
    - `mps/ANE/.ane_runs/json/full_path_tiled_q240_skip_source_validation_20260623.json`
    - CSV peers under `mps/ANE/.ane_runs/csv/`
  - diagnostic code change：`benchmark/private_ane_transformer_layerwise_compare.py` 支持 tiled candidate env；`benchmark/private_ane_test_clean_benchmark.py` 保持 tiled 默认关闭，因为裸 default smoke 未携带 fused/persistent profile 时仍会落入已知 `band_split_l2_0 InvalidMILProgram`。tiled q240 目前是显式 opt-in validated profile，不是全局默认。
  - verdict=`confirmed_full_path_opt_in_not_default`：matched explicit skip-source/fused control full path wall=`28.173s`；tiled q240 full path wall=`27.903s`；均低于 `<30s`。
  - correctness：tiled q240 vs old best、tiled q240 vs matched control 均 exact (`max_abs=0`, `mean_abs=0`, `num_checked=6983680`)。
  - memory constraint：native-supervisor max child RSS 未增加（old best `1658.125MB`，matched control `~1303.844MB`，tiled `1630.766MB`）；swap growth `0`。
  - important caveat：full-path 大幅超过旧 `31.337585s` best 的主要原因是 load/materialization/cache state 改善；tiled q240 相对 matched control 只再改善约 `0.270s`。full-path transformer eval 仍约 `19.744s`，`ane_pre_eval` 仍约 `12.538s`，`axis_pack` 仍约 `3.328s`，所以 ANE 利用率问题尚未解决。
  - 当前 best full-path baseline：`test_clean.m4a` private ANE `27.903s`，RTF≈`0.7048`。
- 2026-06-23 transformer-only tiled attention-pre q_chunk sweep:
  - 新证据：
    - `benchmark_results/private_ane/transformer_layerwise_qsweep_l1_q240_skip_source_20260623.json`
    - `benchmark_results/private_ane/transformer_layerwise_qsweep_l1_q480_skip_source_20260623.json`
    - `benchmark_results/private_ane/transformer_layerwise_qsweep_l1_q{64,120,160,192,320,960}_skip_source_20260623.failure.log`
    - `mps/ANE/.ane_runs/json/transformer_only_tiled_pre_qchunk_sweep_20260623.json`
    - `mps/ANE/.ane_runs/csv/transformer_only_tiled_pre_qchunk_sweep_20260623.csv`
  - verdict=`confirmed_q240_best_of_sweep`：`q=240` 与 `q=480` 可编译且 exact；`q=64/120/160/192/320/960` 均在 ANE compile 阶段 `InvalidMILProgram`。
  - `q=240` 优于 `q=480`：candidate wall `1.790930s` vs `1.845064s`；`ane_pre_eval_delta=-0.031145s` vs `-0.003835s`；`axis_pack_delta=-0.015580s` vs `+0.004898s`；RSS delta `+0.0625MB` vs `+4.031MB`。
  - 结论：不要继续把 q_chunk sweep 当主要优化空间；当前 MIL family 中 q240 是最好的 valid tiled split。下一步应分析 attention-pre MIL / shape / segmentation 为什么大部分 q_chunk compile-fail，并寻找非 q_chunk 的 segmentation/shape 改法。
- 2026-06-23 attention-pre qchunk compile-gate static analysis:
  - 新证据：
    - `mps/ANE/.ane_runs/json/attention_pre_qchunk_compile_gate_analysis_20260623.json`
    - `mps/ANE/.ane_runs/csv/attention_pre_qchunk_compile_gate_analysis_20260623.csv`
  - minimal probe：直接调用当前实现的 `pymss.modules.bs_roformer.private_ane._attention_pre_tiled_mil(batch=62, seq=960, valid_seq=960, q_chunk=...)`，对 `64/120/160/192/240/320/480/960` 生成 MIL 并统计 op/shape，再与上一轮真实 ANECompiler q-sweep verdict 合并。
  - verdict=`confirmed_qchunk_sweep_not_root_solution`：当前 MIL family 的 branch fan-out 随 `ceil(seq/q_chunk)` 变化；q64 生成 `15` 个 softmax branch / `30` 个 matmul / `19` 个 slice，q240 生成 `4` / `8` / `8`，q480 生成 `2` / `4` / `6`，q960 退化为单个巨大 attention branch / `2` 个 matmul / `5` 个 slice。
  - compiler gate：真实 q-sweep 已证明只有 `q=240/480` 可编译；`q=64/120/160/192/320/960` 均 `InvalidMILProgram`。其中 q240 比 q480 更快且 RSS delta 更低，因此继续 sweep q_chunk 不是主线。
  - 结论：剩余慢速根因仍是 transformer segmented runtime，而不是 q_chunk 未调好；下一步应该做 transformer-only layout/segmentation reuse probe，目标同时观察 `axis_pack`、`ane_pre_eval`、eval、correctness、RSS/swap，不启用 retained transformer handle cache。
- 2026-06-23 transformer-only pre-scope q240 layout probe:
  - 新证据：
    - `benchmark_results/private_ane/transformer_layerwise_preonly_q240_skip_source_20260623.json`
    - `mps/ANE/.ane_runs/json/transformer_preonly_q240_layout_probe_20260623.json`
    - `mps/ANE/.ane_runs/csv/transformer_preonly_q240_layout_probe_20260623.csv`
  - diagnostic code change：`benchmark/private_ane_transformer_layerwise_compare.py` 新增 `--probe-handle-scope`、`--probe-stop-after-axis`、`--probe-stop-after-layer`，只用于 diagnostic harness；不改变 runtime 默认项，且每个 variant 仍立即 `clear_cache(...)`，不通过 retained transformer handles 加速。
  - probe command：`/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --compare bridge-env --layers 1 --chunks 4 --q-chunk 240 --cache-tmpdir benchmark_results/private_ane/ane_tmp_loadcache --probe-handle-scope pre --probe-stop-after-axis time --probe-stop-after-layer 1 --bridge-env ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT=1 --bridge-env PYMSS_PRIVATE_ANE_TILED_TIME_ATTENTION_PRE=1 --bridge-env PYMSS_PRIVATE_ANE_TILED_TIME_ATTENTION_PRE_Q_CHUNK=240 --out benchmark_results/private_ane/transformer_layerwise_preonly_q240_skip_source_20260623.json`
  - verdict=`confirmed_preonly_q240_small_gain_not_layout_solution`：candidate q240+skip-source vs primed load-cache pre-only control wall `1.126562s -> 0.961599s` (`-0.164963s`)，`ane_pre_eval_delta=-0.026105s`，但 `axis_pack_delta=+0.014333s`。
  - correctness：pre-scope output exact (`max_abs=0`, `mean_abs=0`, `checksum_delta=0`)。
  - 结论：q240 确实降低部分 attention-pre eval，但不能解决 layout movement；normal time-axis path 已有 scratch buffer reuse，剩余 `axis_pack` 更接近 transpose/copy/layout-contract 成本，不是简单 allocation reuse。下一步要么找到避免/摊销 time-axis transpose/copy 的 layout-route seam，要么输出明确 blocker。
- 2026-06-23 host-layout micro route-selection for direct time-to-freq repack:
  - 新证据：
    - `mps/ANE/.ane_runs/json/layout_repack_micro_time_to_freq_20260623.json`
    - `mps/ANE/.ane_runs/csv/layout_repack_micro_time_to_freq_20260623.csv`
  - minimal probe：NumPy-only host-layout micro，shape=`chunks=4, B=1, T=960, F=62, D=384, TIME_PAD=960, FREQ_PAD=64`，比较当前 `time_out -> natural contiguous -> freq_padded` 与 direct `time_out -> freq_padded`。
  - correctness：direct route 与当前 route 对 warmup chunks `array_equal`。
  - verdict=`candidate_direct_time_to_freq_repack_has_host_copy_headroom`：current mean `0.098836s`，direct mean `0.086570s`，mean delta `-0.012266s`（约 `-12.4%`）/ 4 chunks / 40 repeats。
  - 结论：这不是 inference-speed 证据，但证明存在值得实现的 safe diagnostic seam：把 time-axis ANE output 直接 repack 成 freq-axis ANE input，避免自然 layout 中间 copy。下一步必须在真实 `PrivateANETransformerRunner` 中实现 opt-in diagnostic route，再用 transformer-only exactness/profile 验证，不能直接推广到 full path。
- 2026-06-23 real runner direct time-to-freq repack probe:
  - 新证据：
    - `benchmark_results/private_ane/transformer_layerwise_direct_time_to_freq_repack_control_20260623.json`
    - `benchmark_results/private_ane/transformer_layerwise_direct_time_to_freq_repack_20260623.json`
    - `mps/ANE/.ane_runs/json/direct_time_to_freq_repack_probe_20260623.json`
    - `mps/ANE/.ane_runs/csv/direct_time_to_freq_repack_probe_20260623.csv`
  - diagnostic code change：`pymss/modules/bs_roformer/private_ane.py` 新增 opt-in `private_ane_direct_time_to_freq_repack` 路径；`benchmark/private_ane_transformer_layerwise_compare.py` 支持 candidate-only `PYMSS_PRIVATE_ANE_DIRECT_TIME_TO_FREQ_REPACK=0/1`。默认关闭，不改变 full path / production route。
  - probe commands：
    - control: `/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --compare bridge-env --layers 1 --chunks 4 --q-chunk 240 --cache-tmpdir benchmark_results/private_ane/ane_tmp_loadcache --bridge-env PYMSS_PRIVATE_ANE_DIRECT_TIME_TO_FREQ_REPACK=0 --out benchmark_results/private_ane/transformer_layerwise_direct_time_to_freq_repack_control_20260623.json`
    - direct: `/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --compare bridge-env --layers 1 --chunks 4 --q-chunk 240 --cache-tmpdir benchmark_results/private_ane/ane_tmp_loadcache --bridge-env PYMSS_PRIVATE_ANE_DIRECT_TIME_TO_FREQ_REPACK=1 --out benchmark_results/private_ane/transformer_layerwise_direct_time_to_freq_repack_20260623.json`
  - verdict=`falsified_direct_time_to_freq_repack_not_promotable`：matched candidate-position direct vs no-op control output exact (`max_abs=0`)，但 wall `+0.027971s`、eval `+0.044896s`、`axis_pack +0.014385s`，RSS delta `+173.516MB`。
  - 结论：不要推广 direct boundary repack；micro-probe 的 host-copy headroom 在真实 runner 中被额外 repack / memory pressure / ANE eval variance 吃掉。剩余 `axis_pack` 加速需要更深的 layout contract 改动（跨 time/freq/layer 保持 ANE-native layout）或更大 fused segment，而不是当前 boundary host repack。
- 2026-06-23 layout-contract axis-pack blocker:
  - 新证据：
    - `mps/ANE/.ane_runs/json/layout_contract_axis_pack_blocker_20260623.json`
    - `mps/ANE/.ane_runs/csv/layout_contract_axis_pack_blocker_20260623.csv`
  - verdict=`blocked_at_current_boundary_layout_contract`：当前 best full-path 中 `axis_pack=3.327896s`，time-axis `2.509663s`，freq-axis `0.818234s`。已确认 q-chunk sweep、`bridge_pack_gate=0`、pre-only q240、direct boundary repack 都不能在不增加内存的前提下解决该项。
  - required contract：需要 fused time+freq transformer segment、ANE-side transpose/repack primitive，或让 time/freq attention templates 共享 ANE-native internal layout；否则 host 必须在 `[B,T,F,D]` natural layout 与 axis-specific ANE padded layout 之间复制。
  - 下一步：做 one-layer/chunk 级 fused time+freq MIL compile-feasibility probe；若 ANECompiler 拒绝，产出 `InvalidMILProgram` evidence package，正式收窄 `axis_pack` 当前层 dead-end。
- 2026-06-23 fused time/freq compile-feasibility probe:
  - 新证据：
    - `mps/ANE/.ane_runs/json/fused_time_freq_layout_primitive_compile_matrix_20260623.json`
    - `mps/ANE/.ane_runs/csv/fused_time_freq_layout_primitive_compile_matrix_20260623.csv`
    - `mps/ANE/.ane_runs/json/freq_unpadded_segment_compile_probe_20260623.json`
    - `mps/ANE/.ane_runs/csv/freq_unpadded_segment_compile_probe_20260623.csv`
    - `mps/ANE/.ane_runs/json/freq_unpadded_direct_compile_probe_20260623.json`
    - `mps/ANE/.ane_runs/csv/freq_unpadded_direct_compile_probe_20260623.csv`
    - `mps/ANE/.ane_runs/json/fused_time_freq_compile_feasibility_summary_20260623.json`
    - `mps/ANE/.ane_runs/csv/fused_time_freq_compile_feasibility_summary_20260623.csv`
  - verdict=`confirmed_unpadded_freq_segment_compile_feasible_but_runner_contract_padded`。
  - layout primitive matrix：current-shape `identity`、`reshape_only`、`transpose_reshape_no_pad` 均可编译；`transpose_reshape_concat_pad` 到 `FREQ_PAD=64` 编译失败。因此不要在 MIL 内用 concat zero padding 做 fused route。
  - runner guard probe：`freq_padded_current seq=64/valid=62` 通过；`freq_unpadded_candidate seq=62/valid=62` 在 runner support gate 被拒绝，错误为 `private_ane batch-axis transformer eval is not supported...`，这不是 ANECompiler verdict。
  - direct compile probe：绕过 runner support gate 直接调用 `_compile_block`，`freq_padded_current_direct` 和 `freq_unpadded_candidate_direct` 都可编译；unpad candidate compile wall 约 `1.529s`。
  - 结论：当前 `axis_pack` dead-end 不是 ANECompiler 绝对拒绝 unpadded freq segment，而是 runtime contract 固定走 `FREQ_PAD=64`。下一步应实现 opt-in transformer-only unpadded freq route，并以 exactness / `axis_pack` / wall / RSS 决定是否可继续。
- 2026-06-23 unpadded freq runtime route probe:
  - 新证据：
    - `benchmark_results/private_ane/transformer_layerwise_unpadded_freq_control_20260623.json`
    - `benchmark_results/private_ane/transformer_layerwise_unpadded_freq_candidate_20260623.failure.log`
    - `mps/ANE/.ane_runs/json/unpadded_freq_runtime_probe_20260623.json`
    - `mps/ANE/.ane_runs/csv/unpadded_freq_runtime_probe_20260623.csv`
  - diagnostic code change：`private_ane_direct_time_to_freq_unpadded` / `PYMSS_PRIVATE_ANE_DIRECT_TIME_TO_FREQ_UNPADDED=1` 默认关闭；route 让 time-axis output 直接生成 width=`FREQ_SEQ=62` 的 freq input，并让 freq-axis compile 使用 `seq=62, valid=62`。
  - control command：`/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --compare bridge-env --layers 1 --chunks 4 --q-chunk 240 --cache-tmpdir benchmark_results/private_ane/ane_tmp_loadcache --bridge-env PYMSS_PRIVATE_ANE_DIRECT_TIME_TO_FREQ_UNPADDED=0 --out benchmark_results/private_ane/transformer_layerwise_unpadded_freq_control_20260623.json`
  - candidate command：`/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --compare bridge-env --layers 1 --chunks 4 --q-chunk 240 --cache-tmpdir benchmark_results/private_ane/ane_tmp_loadcache --bridge-env PYMSS_PRIVATE_ANE_DIRECT_TIME_TO_FREQ_UNPADDED=1 --out benchmark_results/private_ane/transformer_layerwise_unpadded_freq_candidate_20260623.json`
  - verdict=`falsified_unpadded_freq_runtime_eval_failed`：matched no-op control completed exact (`max_abs=0`)；unpad candidate fails at real ANE eval, specifically `_run_freq_axis_packed_with_handles -> _run_block_profiled -> bridge.run_profiled(pre, x_ane, (batch, INNER, 1, seq))` with `RuntimeError: ANE eval failed`。
  - 结论：compile feasibility 不足以推广；`seq=62` freq attention-pre 的 eval surface / descriptor / output-shape contract 与 bridge/runtime 不匹配。下一步应比较 padded vs unpadded handle descriptors、input/output byte sizes、surface shape assumptions，而不是继续改 host layout。
- 2026-06-23 padded-vs-unpadded freq surface contract probe:
  - 新证据：
    - `mps/ANE/.ane_runs/json/freq_padded_vs_unpadded_surface_contract_probe_20260623.json`
    - `mps/ANE/.ane_runs/csv/freq_padded_vs_unpadded_surface_contract_probe_20260623.csv`
  - verdict=`confirmed_unpadded_freq_eval_surface_contract_failure`。
  - padded `seq=64, valid=62` freq attention-pre：compile ok，descriptor `n_inputs=1, n_outputs=1, model_state=3`，input bytes `30,736,384`，output bytes `61,472,768`，pre-handle eval ok。
  - unpadded `seq=62, valid=62` freq attention-pre：compile ok，descriptor 同样 `n_inputs=1, n_outputs=1, model_state=3`，input bytes `29,775,872`，output bytes `59,551,744`，但 pre-handle eval fails (`RuntimeError: ANE eval failed`)。
  - 结论：failure 已定位到 compile 之后、完整 transformer block 之前的 attention-pre eval/surface compatibility 层。下一步应测试 bridge-level output shape / surface allocation variants；若仍失败，则 `FREQ_PAD=64` 是当前 family 的硬 runtime contract。
- 2026-06-23 unpadded freq surface-byte variant probe:
  - 新证据：
    - `mps/ANE/.ane_runs/json/freq_unpadded_surface_bytes_variant_probe_20260623.json`
    - `mps/ANE/.ane_runs/csv/freq_unpadded_surface_bytes_variant_probe_20260623.csv`
  - verdict=`confirmed_unpadded_mil_requires_padded_surfaces_for_eval`。
  - measured variants：
    - padded baseline `mil_seq=64`, input/output surface seq `64/64`, write/read `64/64`: eval ok。
    - unpadded actual `mil_seq=62`, surface `62/62`, write/read `62/62`: eval failed。
    - unpadded MIL with both input/output surfaces padded `64/64`, write/read `62/62`: eval ok。
    - unpadded MIL with both surfaces padded `64/64`, write `64`, read `62`: eval ok。
    - unpadded MIL with only input padded or only output padded: eval failed。
  - 结论：硬约束不是 MIL `seq=62` 本身，而是 ANE eval 需要 input 和 output IOSurface byte allocation 都保持 `FREQ_PAD=64`。下一步可实现一个更窄的 opt-in route：freq MIL `seq=62`，但 compile-time input/output bytes 使用 `seq=64` surface contract，运行时 write/read 有效 `62`。
- 2026-06-23 已完成 residual cache-hit transformer load/materialization decomposition：
  - 新证据：
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_load_cache_bridgeprofile_20260623.json`
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_load_cache_bridgeprofile_20260623_profile/profile_summary.json`
    - `mps/ANE/.ane_runs/json/residual_cache_hit_load_materialization_decomposition_20260623.json`
    - `mps/ANE/.ane_runs/csv/residual_cache_hit_load_materialization_decomposition_20260623.csv`
  - verdict=`confirmed`：current warm-cache batch4 run wall=`35.891103s`, transformer eval loop=`20.123772s`, transformer `load_or_compile_wall_sec=5.942209s`; 24/24 transformer rows are `load_cache_hit=True`, `bridge_profile_route=load_cache`, and `handle_cache_hit=False`。
  - bridge-profiled transformer load/materialization subwork=`3.777231s` / `63.57%` of `load_or_compile`：
    - `bridge_profile_tmpdir_sec=1.904578s` / `32.05%`
    - `bridge_profile_load_qos_sec=1.262232s` / `21.24%`
    - `bridge_profile_file_write_sec=0.573875s` / `9.66%`
    - descriptor/model/surface/request/handle creation collectively tiny (`<0.03s`)
  - unprofiled wrapper/materialization gap=`2.164978s` / `36.43%`。
  - Previous RE blocker still constrains solution choice: current safe host-visible lower-control layer cannot fundamentally replay/reset accepted state; do not return to descriptor guessing, selector/open-family replay, ready-gate spoofing, or default persistent transformer handles. Next solution should be memory-neutral source/materialization/segment reduction above that layer.
  - 下一步：做 cache-hit source-materialization shortcut / ablation，目标是降低 `tmpdir + file_write + unprofiled gap`，同时检查 eval、correctness、RSS/swap 不回退。
- 2026-06-23 已完成 full-path load-cache vs no-load-cache batch4 comparison：
  - 新证据：
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_no_load_cache_profile.json`
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_no_load_cache_profile_profile/profile_summary.json`
    - `mps/ANE/.ane_runs/json/full_path_load_cache_vs_no_load_cache_20260623.json`
    - `mps/ANE/.ane_runs/csv/full_path_load_cache_vs_no_load_cache_20260623.csv`
  - verdict=`confirmed`：bridge load-cache 已经是当前 baseline 的大幅加速项；关闭它后 wall 从 `43.002657s` 升到 `74.844223s`，增加 `31.841566s` / `74.05%`。
  - transformer `load_or_compile_wall_sec` 从 cache baseline 的 `5.712274s` 升到 no-cache 的 `44.994990s`，增加 `39.282716s` / `687.69%`。
  - transformer eval loop 基本同量级：cache `20.669241s` vs no-cache `19.619257s`，说明本 probe 主要隔离的是 load/materialization/cache 效应，不是 eval shape 的新改善。
  - correctness caveat：本 benchmark JSON 未保留输出音频路径，无法对 cache/no-cache 两个输出做直接 waveform diff；两次均完成 strict private ANE path 且无 torch fallback，但数值等价未在本 probe 重新验证。
  - 下一步已收窄为：解释 cache-hit 下残留的 `5.712274s` transformer load/materialization，而不是继续验证是否应该启用 load-cache。
- 2026-06-23 correction：`test_clean.m4a` 当前 `43.002657s` full private ANE baseline 已经启用 bridge load-cache，而不是 no-cache baseline：
  - `private_ane_memory_guard.load_cache=true`
  - `cache_tmpdir=/Volumes/2T/pymss/benchmark_results/private_ane/ane_tmp_loadcache`
  - `bridge_load_cache.enabled=true`, `hits=139`
  - `transformer_timings.csv`: `load_cache_hit=True` 24/24, `handle_cache_hit=False` 24/24
  - 因此当前慢速原因不能简化为“未启用 load-cache”；下一步应比较 `--private-ane-no-load-cache` full path，并解释 cache-hit 下残留的 `transformer.load_or_compile_wall_sec=5.712274s`。
- 当前 `test_clean.m4a` 慢速主因已确认是组合问题：
  - transformer time-axis ANE eval-only `10.686806s`
  - transformer residual load/materialization `5.712274s`
  - mask wall `5.441266s`
  - transformer freq-axis ANE eval-only `3.954855s`
  - transformer axis pack/layout `3.672866s`
  - transformer ANE read/write `2.297088s`
  - handle/free + GC `1.535922s`
  - 结论：这不是单一 ANE compute peak 问题，而是 shape/segmentation + residual load/materialization + host layout/transfer/lifecycle overhead。
- 2026-06-23 已完成 transformer bridge load-cache repeat candidate probe：
  - 新证据：
    - `benchmark_results/private_ane/transformer_layerwise_compare_l1_load_cache_chunks4_20260623.json`
    - `benchmark_results/private_ane/transformer_layerwise_compare_l1_load_cache_chunks4_r2_20260623.json`
    - `mps/ANE/.ane_runs/json/transformer_load_cache_repeat_compare_20260623.json`
    - `mps/ANE/.ane_runs/csv/transformer_load_cache_repeat_compare_20260623.csv`
  - verdict=`confirmed_candidate`：two fresh transformer-only same-process load-cache repeat probes were exact and averaged `-3.208305s` / `-62.187%` wall versus no-cache current.
  - Mechanism evidence: repeat rows show `load_cache_hit=True`, `handle_cache_hit=False`, and `bridge_profile_compile_qos_sec=0`; this is not persistent transformer handle caching.
  - Run 1 wall delta: `-3.223859s` / `-62.419%`; run 2 wall delta: `-3.192752s` / `-61.956%`; correctness exact in both (`max_abs=0`, checksum delta `0`).
  - Caution: the harness cache directory remained empty, so this appears to use bridge/ANE same-process load-cache behavior rather than a durable disk cache; full-path validation must record cache hit fields and memory/swap carefully.
  - Next short-term goal: run full `test_clean.m4a` private ANE profile with bridge load-cache enabled and compare against the `43.002657s` baseline: wall, correctness, transformer `load_or_compile`, auxiliary compile, memory, and cache hit fields.
- 2026-06-23 已完成 transformer batch-axis segment-count candidate probe：
  - 新证据：
    - `benchmark_results/private_ane/transformer_layerwise_compare_l1_batch_axis_chunks4_20260623.json`
    - `mps/ANE/.ane_runs/json/transformer_batch_axis_compare_20260623.json`
    - `mps/ANE/.ane_runs/csv/transformer_batch_axis_compare_20260623.csv`
  - verdict=`falsified`：batch-axis is not a valid default route for this transformer shape.
  - Time-axis batch-axis is unsupported (`batch_axis_supported=False`), so it does not reduce the dominant time-axis segment path.
  - Freq-axis batch-axis is supported, but worsens `load_or_compile` by `+3.372755s`, eval by `+1.155641s`, wall by `+4.415963s` / `+82.736%`, and introduces small numerical drift (`max_abs=0.015625`).
- 2026-06-23 已完成 transformer-only integrated tiled q=240 comparison：
  - 新证据：
    - `benchmark/private_ane_transformer_layerwise_compare.py`
    - `benchmark_results/private_ane/transformer_layerwise_compare_l1_q240_20260623.json`
    - `mps/ANE/.ane_runs/json/transformer_layerwise_tiled_q240_compare_20260623.json`
    - `mps/ANE/.ane_runs/csv/transformer_layerwise_tiled_q240_compare_20260623.csv`
  - verdict=`falsified`：tiled q=240 is not a valid default optimization under current constraints.
  - Correctness in the one-layer transformer-only harness is exact (`max_abs=0`, `mean_abs=0`, checksum delta `0`), so the route is functionally equivalent.
  - Performance is negative: wall worsens by `+3.418162s` (`+81.8747%`).
  - Root cause of regression: time-axis `load_or_compile_wall_sec` worsens by `+3.453054s`, while time-axis `eval_sec` improves only `-0.018812s`; `ane_pre_eval` improves only `-0.006038s`.
  - Memory constraint is also negative: max RSS increases by about `31.406MB`.
  - Solution decision: do not promote tiled q=240. The next viable route must target transformer `load_or_compile`, segment count, and lifecycle overhead without persistent handle memory growth.
- 2026-06-23 已完成 transformer `attention_pre` effective-shape micro-profile：
  - 新证据：
    - `mps/ANE/.ane_runs/json/transformer_attention_pre_shape_micro_20260623.json`
    - `mps/ANE/.ane_runs/csv/transformer_attention_pre_shape_micro_20260623.csv`
    - `benchmark_results/private_ane/attention_pre_time_b62_micro_profile_20260623.json`
    - `benchmark_results/private_ane/attention_pre_time_b62_tiled240_micro_profile_20260623.json`
    - `benchmark_results/private_ane/attention_pre_time_b62_tiled480_micro_profile_20260623.json`
    - `benchmark_results/private_ane/attention_pre_freq_b960_micro_profile_20260623.json`
  - verdict=`confirmed_root_cause_partial_solution_not_promoted`：time-axis `attention_pre` at effective `batch=62, seq=960` reproduces the integrated hotspot.
  - Time-axis effective-shape result: micro `batch=62, seq=960` eval=`0.201787s`; multiplied by 4 chunks gives `0.807148s`, matching integrated `time layer0 ane_pre_eval=0.832496s`.
  - Freq-axis effective-shape result: micro `batch=960, seq=64` eval=`0.062119s`; multiplied by 4 chunks gives `0.248475s`, close to integrated `freq layer0 ane_pre_eval=0.268893s`.
  - Tiled q=240 result: eval improves from `0.201787s` to `0.187064s` (`-7.296%`), but compile worsens from `1.480479s` to `4.803896s` (`+224.482%`).
  - Tiled q=480 result: eval improves only `-1.302%` and compile worsens `+585.272%`.
  - Solution decision: do not promote tiled attention-pre yet. It may reduce steady eval, but under current unresolved load/compile constraints the compile regression can erase the win. It requires a valid integrated run with wall/profile/memory evidence.
  - Attempted first-layer full-path control route with `--private-ane-max-transformer-layers 1 --private-ane-no-strict-stage-check` also failed before transformer at `band_split_l2_fused_0_4`; next loop must recover exact native-supervised full-path invocation or add a transformer-only integrated harness.
- 2026-06-23 已完成 first bridge-pack/layout ablation probe：
  - 新证据：
    - `mps/ANE/.ane_runs/json/transformer_bridge_pack_ablation_20260623.json`
    - `mps/ANE/.ane_runs/csv/transformer_bridge_pack_ablation_20260623.csv`
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_persistent_aux_no_bridge_pack_profile.private_ane_child/child.log`
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_persistent_aux_no_bridge_pack_profile.private_ane_child/parent_watchdog_failure.json`
  - verdict=`falsified` for the global ablation route: full-pipeline `--private-ane-no-bridge-pack-gate` is not a valid transformer measurement because it fails before transformer.
  - Failure point: `band_split_l2_fused_0_4` ANE compile fails with `InvalidMILProgram`; `private_ane batch band split failed and torch fallback is disabled`.
  - Interpretation: `bridge_pack_gate` is currently a global pipeline requirement for at least fused band split, not a transformer-only toggle. This does not remove `transformer.axis_pack=3.672866043s` as a bottleneck; it means the next probe must be transformer-scoped or transformer-only.
  - Next short-term goal: create or use a transformer-scoped layout ablation that leaves fused band split bridge packing enabled, or a transformer-only micro-harness, then compare transformer `axis_pack`, wall, ANE eval, read/write, correctness, and memory delta.
- 2026-06-23 已完成 `TransformerRuntime` root-cause ledger：
  - 新证据：
    - `mps/ANE/.ane_runs/json/transformer_runtime_root_cause_ledger_20260623.json`
    - `mps/ANE/.ane_runs/csv/transformer_runtime_root_cause_ledger_20260623.csv`
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_persistent_aux_profile_profile/profile_summary.json`
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_persistent_aux_profile_profile/transformer_timings.csv`
  - verdict=`confirmed`：当前 `test_clean.m4a` private ANE 慢速不是单一原因；主要是 transformer eval-only、load/compile、mask、layout pack、ANE read/write、handle lifecycle/GC 的组合。
  - Top measured causes by wall share:
    1. `transformer_time_axis_eval_only=10.686806459s` (`24.8515%` wall)
    2. `transformer_load_or_compile=5.712273665s` (`13.2835%` wall)
    3. `mask=5.441266209s` (`12.6533%` wall)
    4. `transformer_freq_axis_eval_only=3.954854589s` (`9.1968%` wall)
    5. `transformer_axis_pack=3.672866043s` (`8.5410%` wall)
    6. `transformer_ane_read_write=2.297088345s` (`5.3417%` wall)
    7. `transformer_handle_free_gc=1.535922207s` (`3.5717%` wall)
  - Flag evidence from `transformer_timings.csv`: `load_cache_hit=True` for 24/24 rows, but `handle_cache_hit=False`, `cache_hit=False`, and `cache_kept=False` for 24/24 rows; automatic handle/result reuse is not active in this measured path.
  - Constraint interpretation: persistent transformer handle cache may reduce load/free churn but is not a default solution under the "do not increase memory usage" constraint. It needs bounded memory-neutral evidence before becoming an allowed route.
  - Prior RE implication remains active: private lower-control same-layer routes are blocked by `host_visible_lower_control_dead_end_blocker_20260623`, so do not repeat descriptor/selector/visible send-shell probing for this loop.
  - Next short-term goal: run a memory-neutral bridge-pack/layout ablation, comparing current `bridge_pack_gate=true` against no-bridge-pack or equivalent pre-layout route, recording wall time, `axis_pack`, ANE eval, read/write, correctness, and memory delta.
- 2026-06-23 已完成 supported ANE repeat-load / precompiled-artifact cache route probe，当前 long-term plan 进入 `TransformerRuntime`：
  - 新证据：
    - `mps/ANE/.ane_runs/json/supported_ane_repeat_load_precompiled_probe_20260623.json`
    - `mps/ANE/.ane_runs/csv/supported_ane_repeat_load_precompiled_probe_20260623.csv`
    - `benchmark_results/coreml_ne_diagnostics/transformer_single_pipeline_same_process_double_load_20260623.json`
    - `benchmark_results/ane_load_path_probe/current_stages/load_compare.json`
    - `benchmark_results/coreml_ne_diagnostics/hyperace_maskcore_release_between_loads_precompiled_probe_len256.json`
  - verdict=`falsified`：supported same-process repeat-load / precompiled Core ML/ANE artifact route did not materially eliminate compile/load for the measured transformer and mask packages.
  - Transformer same-process double-load only improved from `10.880670542s` to `10.450698375s` (`0.429972167s`, `3.951707%`), which is not enough to explain or eliminate the full `test_clean.m4a` transformer `load_or_compile=5.712274s`.
  - Existing transformer package-vs-compiled evidence is negative for this route: `.mlpackage` total load `61.250500334s`, compiled `.mlmodelc` total load `72.949054543s` (`+11.698554209s`, `19.099524%` slower).
  - Mask evidence is also negative: precompiled release-between-loads changed from `173.080025958s` to `174.683764291s`; other repeat-load probes were equal or slower on the second load.
  - Updated long-term direction: keep ANE as target backend; MPS/MLX remain fallback/reference only; stop treating supported cache/precompile as a proven solution and now analyze remaining transformer runtime/dispatch/transfer/lifecycle costs.
  - Next phase hypothesis is persisted in `docs/ane_next.md`: remaining transformer latency is dominated by eval-only, segmentation/dispatch, axis pack/unpack, ANE read/write, handle/free, or fallback/sync costs rather than a supported Core ML/ANE second-load cache hit.
- 2026-06-23 已完成 `test_clean.m4a` ANE load/compile overhead map baseline：
  - 新证据：
    - `mps/ANE/.ane_runs/json/ane_baseline_load_compile_overhead_map_20260623.json`
    - `mps/ANE/.ane_runs/csv/ane_baseline_load_compile_overhead_map_20260623.csv`
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_persistent_aux_profile_profile/profile_summary.json`
    - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_persistent_aux_profile_profile/transformer_bottleneck_ledger.csv`
  - 当前事实：
    1. full private ANE `test_clean.m4a` wall=`43.002657s`，audio=`39.590023s`，RTF=`1.0862`
    2. transformer eval loop 是最大成本：`20.669241s` / `48.07% wall`
    3. transformer ANE eval-only 为 `14.641661s`，同时 transformer `load_or_compile` 为 `5.712274s` / `13.28% wall`，覆盖 24 segments
    4. non-transformer compile 也显著：`mask.compile=3.732670s`、`band_split.compile=1.196359s`、`istft.compile=0.607919s`、`stft.compile=0.469620s`
    5. 已知 compile/load 合计约 `11.718841s` / `27.25% wall`，足以解释从 `43s` 接近 `<=30s` 目标的大部分差距；dispatch/transfer/lifecycle 也显著：`axis_pack=3.672866s`、`ane_read=1.365294s`、`ane_write=0.931795s`
  - 结论：
    - verdict=`confirmed`：当前 baseline 已把 cold compile/load 与 steady eval / dispatch overhead 分离
    - next=`SupportedANECache`：优先验证 transformer `load_or_compile` 与 `mask.compile` 是否能通过 supported ANE cache/precompile/warm-process route 降低
- 2026-06-23 长期目标已重定向：
  - 新目标：
    1. 保持 ANE inference 为目标后端，先围绕 transformer repeated `load/compile` overhead 寻找 supported ANE artifact/cache/precompile/static-shape/warm-process reuse 路线
    2. MPS/MLX 只作为 fallback/reference，不作为目标后端
    3. 在 load/compile 降低后，继续解释并优化 transformer `eval_loop_wall`、ANE eval-only、segment dispatch、axis pack/unpack、ANE read/write、handle/free、fallback/sync 成本
    4. private lower-control RE 仅在出现新的 firmware-private reply/replay visibility、safe IOProcessor/interrupt completion observation，或 authorized entitlement/signing environment 时恢复
  - 保留边界：
    - 当前 machine-local safe host-visible private route 已由 `host_visible_lower_control_dead_end_blocker_20260623` 判死；不要重复 descriptor/selector/wrapper/visible send-shell probing
- 2026-06-23 已完成 current host-visible lower-control formal blocker package：
  - 新证据：
    - `mps/ANE/.ane_runs/json/host_visible_lower_control_dead_end_blocker_20260623.json`
    - `mps/ANE/.ane_runs/csv/host_visible_lower_control_dead_end_blocker_20260623.csv`
    - `mps/ANE/experiments/results/host_visible_lower_control_dead_end_blocker_package.md`
  - 当前事实：
    1. ANEServices selector/open family 已关闭：selector3/6 无 reusable carrier；raw selector-3 `status=0` 跳过 `resource+0x493a0` producer；`service+0x18` 来自 selector-0 reply `+0x1c`，当前 direct open 自然 ready=0；non-direct/hinted route 当前不可达
    2. resource/materializer visible author surface 仍缺 first positive author：`resource+0x493a0` 是 runtime-owned surface，但 current direct route 到不了 producer；`resource+0x400d0` first author 低于 visible helper/direct/bulk surface；procedure/cache/chaining 是 lookup/build/send
    3. `record+0x1b8` 是最小 lower state entry，但 first author 低于 H16-visible send/reply shell：`aneCmdSend(raw)` 后 5 条 visible 指令内无 store/call，随后读取 `record+0x1b8` 并 mirror 到 `resource+0x402f0`
    4. `process+0x203fc` visible exact writers 只证明 0/1；state-2 author 低于 visible exact-writer surface
    5. 当前 safe dynamic observation/control 不可用；禁止 SIP change、protected daemon attach、daemon replacement、risky kernel/firmware dynamic probe
  - 结论：
    - verdict=`confirmed`：当前 machine-local safe host-visible route 判死；从当前 descriptor/ANEServices/H16-visible lower route 无法根治 repeated `load/compile`
    - long_term_status=`complete_for_current_machine_local_host_visible_route`：剩余 required control capability 是 firmware-private reply/replay、IOProcessor/interrupt shared-state writeback observation/control，或外部 authorized entitlement/signing environment
- 2026-06-23 已完成 `record+0x1b8` visible send/reply shell first-author 判定：
  - 新证据：
    - `mps/ANE/.ane_runs/json/record1b8_visible_send_shell_author_blocker_20260623.json`
    - `mps/ANE/.ane_runs/csv/record1b8_visible_send_shell_author_blocker_20260623.csv`
  - 当前事实：
    1. `ANE_RestoreState` 在 `0xfffffe00092c1d60` 调 `ANEHWDevice::aneCmdSend(raw)`，随后 `0xfffffe00092c1d78` 读取 `record+0x1b8`
    2. raw-send return 到 `record+0x1b8` read 的 visible interval 为 5 条指令，`stores=0`、`calls=0`
    3. `aneCmdSend(raw)` / `aneFirmwareCommandSend` 已被界定为 stack command/callback packaging、`ANEFirmwareCommandState` payload/wrapper tracking、`IOProcessorChannelSendRetry` submit plumbing
    4. visible `handleOutstandingCommand` / typed completion route 是 completion status、optional copyback/free、resource lookup、callback/wakeup、cleanup、`process+0x20400` counter bookkeeping，不是 `record+0x1b8` durable author
    5. 当前机器 safe dynamic observation 到 bootkc/kernel `ANE_RestoreState` read point 不可用，仍禁止 SIP disable、protected daemon attach、daemon replacement 或 risky kernel/firmware dynamic probe
  - 结论：
    - verdict=`falsified`：H16-visible CPU-side send/reply shell 不是 `record+0x1b8` first author
    - long_term_status=`not_complete`：剩余 required control layer 在 visible shell 以下，候选为 IOProcessor/interrupt completion、firmware-side shared-state writeback、或 firmware-private reply/replay semantics
- 2026-06-23 已完成 `record+0x1b8` vs `process+0x203fc` 下一入口选择：
  - 新证据：
    - `mps/ANE/.ane_runs/json/lower_record_vs_process_entry_selection_20260623.json`
    - `mps/ANE/.ane_runs/csv/lower_record_vs_process_entry_selection_20260623.csv`
    - `mps/ANE/.ane_runs/csv/lower_record_vs_process_entry_process_state_20260623.csv`
    - `mps/ANE/.ane_runs/csv/lower_record_vs_process_entry_record_raw_send_20260623.csv`
    - `mps/ANE/.ane_runs/csv/lower_record_vs_process_entry_program_valid_20260623.csv`
  - 当前事实：
    1. `ANE_RestoreState` 在 `0xfffffe00092c1d34` finalize `x1=selected_record_ptr`，并在 `0xfffffe00092c1d60` 调 `ANEHWDevice::aneCmdSend(raw)`
    2. raw-send 返回后到 `record+0x1b8` 读取之间只有 5 条 visible H16 指令，`stores=0`、`calls=0`
    3. `0xfffffe00092c1d78` 读取 `record+0x1b8`，随后 `0xfffffe00092c1d7c` mirror 到 `resource+0x402f0`
    4. fresh `process+0x203fc` exact-target scan 仍只证明 visible H16 writers 写 0/1；`ProgramLoad` 读非零，`isProcessValid` 特判 exact state 2，但未暴露 state-2 author
    5. `device vtable +0x9c0` 已解析为 `ANEHWDevice::isProgramValid` resource-membership gate，不是 process state-2 author
  - 结论：
    - verdict=`confirmed`：下一最小静态入口选择 `record+0x1b8` raw-send/deeper-replay boundary；`process+0x203fc` 保留为 lifecycle/context surface
    - long_term_status=`not_complete`：下一轮应恢复 `ANE_RestoreState::aneCmdSend(raw)` 以下能填充 selected indexed record `+0x1b8` 的 first author，或证明该 author 已落入 firmware-private reply/replay 语义
- 2026-06-23 已完成 selector-3 ready/open-family 关闭后的 lower technical route selection：
  - 新证据：
    - `mps/ANE/.ane_runs/json/lower_route_after_ready_open_blocker_20260623.json`
    - `mps/ANE/.ane_runs/csv/lower_route_after_ready_open_blocker_20260623.csv`
  - 当前事实：
    1. `resource+0x493a0` 是跨 load/remap/wire/unmap/firmware request/unwire 的 runtime-owned program/resource surface
    2. `resource400d0_deeper_materializer_boundary` 已削弱 visible helper/direct/bulk materializer 假设，first positive author 更可能低于 visible H16/HAL direct surface
    3. `procedure/cache/chaining` 证据能把 accepted-side cacheHandler join 到 `resource+0x400d0/resource+0x9b698`，但这族仍更像 lookup/build/send，不是 durable author
    4. `record+0x1b8` 和 `process+0x203fc` 是当前最贴近 lower accepted-state / lifecycle author 的具体目标
    5. firmware reply-publish 路线保留为静态上下文；当前机器 safe dynamic observation 已证伪，不作为默认入口
  - 结论：
    - verdict=`confirmed`：selector-3 ready/open-family 关闭后，默认下一路线选择 lower resource/materializer lifecycle author recovery
    - long_term_status=`not_complete`：下一轮静态恢复 `record+0x1b8` 或 `process+0x203fc` 的 first author/consumer chain
- 2026-06-23 已完成 selector-3 ready-gate/open-family formal blocker package：
  - 新证据：
    - `mps/ANE/.ane_runs/json/selector3_ready_open_family_formal_blocker_20260623.json`
    - `mps/ANE/.ane_runs/csv/selector3_ready_open_family_formal_blocker_20260623.csv`
    - `mps/ANE/experiments/results/selector3_ready_open_family_formal_blocker_package.md`
  - 当前事实：
    1. ANEServices selector 3/6 visible boundary 无 reusable carrier
    2. default raw selector-3 `status=0` 是 ready-gate short-circuit，跳过 `resource+0x493a0` producer chain
    3. `service+0x18` natural author 是 selector-0 open reply `+0x1c`，当前 direct open 自然 ready=0
    4. regular/non-direct open 需要授权路径，当前 type/mode=3 probes 无 device handle；hinted/private open 在 crash、ABI correction、ad-hoc signing 后仍无正常 status/device route
    5. selector-4 visible patch 与 direct selector-9 payload patch 均未 replay lower resource/process/client tuple
  - 结论：
    - verdict=`confirmed`：当前机器的 selector-3 ready-gate/open-family 层已正式关闭；继续修改 wrapper/open/selector4/selector9 visible fields 的边际价值低
    - long_term_status=`not_complete`：剩余路线是 lower kernel/firmware/resource-materializer control，或外部授权/签名环境；默认下一轮走 lower technical route
- 2026-06-23 已完成 `service+0x18` ready-gate author / open-family blocker 判定：
  - 新证据：
    - `mps/ANE/.ane_runs/json/ready_gate_author_entitlement_blocker_20260623.json`
    - `mps/ANE/.ane_runs/csv/ready_gate_author_entitlement_blocker_20260623.csv`
    - `mps/ANE/.ane_runs/json/ready_gate_natural_author_verdict_20260619.json`
    - `mps/ANE/.ane_runs/json/non_direct_route_reachability_verdict_20260619.json`
    - `mps/ANE/.ane_runs/json/hinted_open_signed_probe_verdict_20260619.json`
  - 当前事实：
    1. `ANE::ANEServicesDevice::ANEDeviceOpen` at `0x19e69c71c` 调用 selector-0 open，随后在 `0x19e69c8b4/0x19e69c8b8` 把 reply `+0x1c` 写入 `service+0x18`
    2. 正确形状的本地 selector-0 successful open reply 自身就携带 `+0x1c=0`，不是 ANEServicesDeviceOpen 参数形状错误导致 ready=0
    3. 自然 author 链为 `ANEClientInfo+0x10 -> device+0x28 -> selector-0 reply+0x1c -> service+0x18`
    4. 当前可成功本地 open 的 direct path 是 `usageType=1 -> H11ANEInDirectPathClient::init -> ANEClientInfo::create(task,1,0,1)`，设计上得到 ready=0
    5. regular/non-direct route 在当前机器上被 `com.apple.ane.iokit-user-access` 等授权条件卡住；usageType/mode=3 sweeps 返回 `0x18` 且无 device handle
    6. `_ANEServicesLocateAndOpenHintedDevice` hinted route 的 crash/ABI correction/ad-hoc entitlement 三轮均未产生正常 status/device route
  - 结论：
    - verdict=`confirmed`：`service+0x18` ready-gate author 不是当前 user-space wrapper/control layer 中可 replay/reset/rebuild 的状态迁移；它收敛为 entitlement-gated higher-level open-family blocker + lower accepted pre-stage
    - long_term_status=`not_complete`：下一轮应把 selector3/6 no-carrier、resource+0x493a0 producer skip、ready-gate author、non-direct/hinted route、visible selector4/9 replay failures 合并为 formal blocker package，并决定剩余路线
- 2026-06-23 已完成 raw selector-3 status=0 path 与 `resource+0x493a0` producer chain 的关系判定：
  - 新证据：
    - `mps/ANE/.ane_runs/json/raw_selector3_ready_gate_producer_skip_20260623.json`
    - `mps/ANE/.ane_runs/csv/raw_selector3_ready_gate_producer_skip_20260623.csv`
    - `mps/ANE/experiments/results/selector3_ready_gate_transport_match_note.md`
    - `mps/ANE/experiments/results/raw_selector3_wrapper_internal_state_note.md`
  - 当前事实：
    1. default rawCreate `status=0` 是 ready-gate short-circuit：`service_ready_u8_0x18=0` 时不发送真实 selector-3
    2. raw create 仍会构造非空 wrapper/payload/device graph，但该 graph 处于 pre-accepted 状态，不等于 `resource+0x493a0` producer 完成
    3. 强制 `service_ready_u8_0x18=1` 后会发出真实 selector-3 public transport，`input_size=0x20`，返回 `0xe00002c2`
    4. 因此 caller-visible output untouched 不是“lower producer 写了 0”，而是 default path 没有进入 producer/publish；forced-ready path 进入 public transport 但仍缺 accepted pre-stage
  - 结论：
    - verdict=`confirmed`：raw selector-3 `status=0/output untouched` 跳过 base load-side `resource+0x493a0` producer chain；当前缺口收敛到 `service+0x18` ready-gate author 与 selector-3 valid 前的 accepted pre-stage
    - long_term_status=`not_complete`：下一轮应定位 `service_ready_u8_0x18` / `service+0x18` author，判断它是否可从 user-space/control-layer 安全恢复，或必须并入 lower blocker
- 2026-06-23 已完成 selector-3 lower user-client/resource-registry author target selection：
  - 新证据：
    - `mps/ANE/.ane_runs/json/selector3_lower_author_target_selection_20260623.json`
    - `mps/ANE/.ane_runs/csv/selector3_lower_author_target_selection_20260623.csv`
    - `mps/ANE/experiments/results/createinstance_process_args_seed_split_note.md`
    - `mps/ANE/experiments/results/process_resource_key_seed_join_note.md`
    - `mps/ANE/experiments/results/resource_493a0_producer_to_import_join_note.md`
  - 当前事实：
    1. create-instance deep path 的 `ANEProcessCreateArgs` 是 split-seeded：`args[0] <- resource+0x493a0[0]`、`args[8] <- hidden local handle/local_y`、`args[16] <- visible client-key family`
    2. 后续 copyback 方向是 `resource+0x493a0 -> external output`，同时 `local_y -> external_output[0]` 与 `params[0]`
    3. 现有 producer/import 链已经具体化为：base load-side external output -> `resource+0x493a0` -> later create-instance import from resolved base resource -> `process_args[0]` / later output refill
    4. visible selector-4/direct selector-9 与 ANEServices selector-3/6 边界都没有证明可 replay 这个 split resource/process/client tuple
  - 结论：
    - verdict=`confirmed`：下一层不再是 wrapper field/copyback；最小 target 是 `resource+0x493a0` producer/import 链如何被 raw selector-3 success 跳过、未运行、未复用或与 hidden-handle/client tuple 不一致
    - long_term_status=`not_complete`：下一轮应判定 raw selector-3 status=0 path 与 base load-side `resource+0x493a0` producer chain 的关系
- 2026-06-23 已完成 ANEServices selector 3/6 payload/copyback boundary 检查：
  - 新证据：
    - `mps/ANE/.ane_runs/json/selector3_6_payload_copyback_boundary_20260623.json`
    - `mps/ANE/.ane_runs/csv/selector3_6_payload_copyback_boundary_20260623.csv`
    - `mps/ANE/experiments/results/raw_selector3_output_sentinel_note.md`
    - `mps/ANE/experiments/results/selector3_livehandle_coherence_note.md`
  - 当前事实：
    1. `ANE::ANEServicesDevice::ANE_ProgramCreate` at `0x19e69d07c` 构造 0x20-byte descriptor：`{ANEProgramCreateArgs*, 0xd88, ANEProgramCreateArgsOutput*, 0xac738}`，随后调用 `IOConnectCallStructMethod(connection, selector=3, descriptor, 0x20, NULL, NULL)`
    2. selector-3 wrapper/logged ABI 只显式暴露 `prodAddr` 与 `progHandle`；没有可见 reusable tuple
    3. 既有 raw selector-3 sentinel probe 显示 status=0 时，caller-visible `0xac738` output buffer 预填 `0xA5` 后 `diff_count=0`，说明当前 raw path 没有写回该 output buffer
    4. 既有 live-handle coherence probe 显示，把 live successful `programHandle` 与 `queueDepth` patch 回 local wrapper 后，selector-4 仍停在 intermediate family
    5. `ANE::ANEServicesDevice::ANE_ProgramDestroy` at `0x19e69da28` 只调用 `IOConnectCallStructMethod(connection, selector=6, ANEProgramDestroyArgs, 0x10, NULL, NULL)`，并只记录 `progHandle`
  - 结论：
    - verdict=`falsified`：ANEServices-visible selector 3/6 boundary 不暴露可稳定复用、重置或重建的 lower-state carrier；selector-3 caller-visible output 与 selector-6 destroy copyback 都不是当前控制层
    - long_term_status=`not_complete`：下一层应贴着 selector-3 user-client/resource-registry handling，找 split resource/process/client tuple 的 author/copyback 点；若已有 H16/user-client blocker 能覆盖该层，则正式连接证据并上抬 blocker
- 2026-06-23 已完成 `controller.device` / `programInstance` vtable slots 的 provider 与实现边界定位：
  - 新证据：
    - `mps/ANE/.ane_runs/json/non_h16_vtable_provider_boundary_20260623.json`
    - `mps/ANE/.ane_runs/csv/non_h16_vtable_provider_boundary_20260623.csv`
    - `/Volumes/2T/dsc_arm64e_extract/System/Library/PrivateFrameworks/AppleNeuralEngine.framework/Versions/A/AppleNeuralEngine.i64`
    - `/Volumes/2T/dsc_arm64e_extract/System/Library/PrivateFrameworks/ANEServices.framework/Versions/A/ANEServices.i64`
  - 当前事实：
    1. `aned_bin_arm64e_20260623` 中 `_ANEDeviceController` 是来自 `AppleNeuralEngine.framework` 的 undefined external；`aned` 不拥有 device 实现
    2. `AppleNeuralEngine.framework` 的 `_ANEDeviceController start` block `0x19f9449a0` 会 `dlopen` `ANEServices.framework/ANEServices`、`dlsym` `ANEServicesDeviceOpen`，并通过 `setDevice:` 保存返回的 device pointer
    3. `ANEServices.framework` 中 `_ANEServicesDeviceOpen` at `0x19e6abc2c` 创建/打开 ANE services device，创建 `ANEDeviceController` 与 `ANERequestReceiver`，加载 firmware 并注册 `ANEServicesDevice`
    4. `_ANEServicesProgramCreate` -> `ANE::ANEServicesDevice::ANE_ProgramCreate` -> `IOConnectCallStructMethod(selector=3)`，callsite `0x19e69d184`
    5. `_ANEServicesProgramPrepare` -> `ANE::ANEServicesDevice::ANE_ProgramPrepare` -> `IOConnectCallStructMethod(selector=4)`，callsite `0x19e69d5c0`
    6. `_ANEServicesProgramStop` -> `ANE::ANEServicesDevice::ANE_ProgramUnprepare` -> `IOConnectCallStructMethod(selector=5)`，callsite `0x19e69d980`
    7. `_ANEServicesProgramDestroy` -> `ANE::ANEServicesDevice::ANE_ProgramDestroy` -> `IOConnectCallStructMethod(selector=6)`，callsite `0x19e69db10`
  - 结论：
    - verdict=`confirmed`：next lower user-space provider 已定位，链路为 `aned -> AppleNeuralEngine._ANEDeviceController -> ANEServicesDeviceOpen -> ANEServicesDevice::ANE_Program* -> IOConnect selectors 3/4/5/6`
    - long_term_status=`not_complete`：下一轮应分析 selector 3 create 与 selector 6 destroy 的 payload/copyback 语义，确认 reusable carrier 是否在 user-client boundary 暴露
- 2026-06-23 已完成 arm64e `_ANEServer unloadModel:options:qos:withReply:` 与 `_ANEProgramCache` unload carrier 检查：
  - 新证据：
    - `mps/ANE/.ane_runs/json/non_h16_unload_carrier_20260623.json`
    - `mps/ANE/.ane_runs/csv/non_h16_unload_carrier_20260623.csv`
  - 当前事实：
    1. `_ANEServer unloadModel:options:qos:withReply:` 不直接调用 native device / IOConnect；核心动作是等待 QoS semaphore 后调用 `+[_ANEProgramCache removeProgramForConnection:model:bundleID:]`
    2. `removeProgramForConnection` 的 block `sub_1000016DC` 只做 cache key lookup、`removeCachedReference`、`programHandle` telemetry 和 dictionary removal
    3. `-[_ANEProgramForLoad removeCachedReference]` / `sub_10000266C` 只递减 refcount；当 refcount 仍 `>=1` 时返回 false，低于 1 时允许 cache remove；它本身不调用 native destroy
    4. 最终 native stop/destroy 依赖 `_ANEProgramForLoad dealloc`，分别调用 `programInstance` vtable `+0x10` 和 `+0x18`，两者返回值都只作为 status
    5. daemon unload path 没有暴露 `0x201/0x401` reply word、durable tuple 或比 wrapper/cache handles 更低的 replay/reset/rebuild carrier
  - 结论：
    - verdict=`falsified`：arm64e `_ANEServer unloadModel` / `_ANEProgramCache` unload path 不是 firmware-published durable state carrier surface
    - long_term_status=`not_complete`：下一层应定位 `controller.device` / `programInstance` vtable slots 的 provider 与实现边界，判断具体 native implementation 是否在本机可见 linked framework 中，或已经越出 `aned` 可见层
- 2026-06-23 已完成正确 arm64e slice 上的 `_ANEProgramForLoad` native ANEProgramCreate/Destroy boundary 检查：
  - 新证据：
    - `mps/ANE/experiments/aned_bin_arm64e_20260623`
    - `mps/ANE/experiments/aned_bin_arm64e_20260623.i64`
    - `mps/ANE/.ane_runs/json/non_h16_native_boundary_carrier_20260623.json`
    - `mps/ANE/.ane_runs/csv/non_h16_native_boundary_carrier_20260623.csv`
  - 当前事实：
    1. `aned_bin` 是 universal binary；此前 `aned_bin_user_space` IDA session 对应 x86_64 slice，只能作为结构提示，不能作为 M4/arm64e runtime 证据
    2. 已抽取 `arm64e` thin slice 并打开为 `aned_bin_arm64e_user_space`，auto-analysis 与 Hex-Rays 均可用
    3. `-[_ANEProgramForLoad destroyProgramInstance]` dispatch block `sub_100006294` 只通过 `programInstance` vtable `+0x18` 调 native destroy，返回值仅作为 status；之后清 `programInstance/refcount/txn`
    4. `createProgramInstanceForModel:...` 的真正 create block `sub_100002EB0` 通过 `controller.device` vtable `+0x10` 调 native create；成功后只写回 `programHandle/intermediateBufferHandle/queueDepth/numInputs/numOutputs/refcount/wiredMemory`
    5. 同一 block 的 prepare 是 `programInstance` vtable `+0x0` status-only；失败 cleanup 是 `programInstance` vtable `+0x18` destroy status-only
  - 结论：
    - verdict=`falsified`：arm64e `_ANEProgramForLoad` create/destroy native boundary 没有暴露比 wrapper/cache handles 更低的 replayable firmware-published durable state carrier
    - long_term_status=`not_complete`：non-H16 route 仍可继续，但下一步应离开 `_ANEProgramForLoad` create/destroy wrapper，检查 `_ANEServer unloadModel:options:qos:withReply:` 与 daemon/IOConnect unload carrier
- 2026-06-23 已完成 non-H16 carrier search 初筛：
  - 新证据：
    - `mps/ANE/.ane_runs/json/non_h16_carrier_initial_surface_20260623.json`
    - `mps/ANE/.ane_runs/csv/non_h16_carrier_initial_surface_20260623.csv`
  - 当前事实：
    1. `mps/ANE/experiments/aned_bin.i64` 已通过 `ida-pro-mcp` 作为 `aned_bin_user_space` 打开，Hex-Rays 可用；该 IDB 是 user-space `aned_bin`，不是 H16 kext
    2. `_ANEProgramForLoad` 暴露 daemon/cache carrier：`programInstance`、`programHandle`、`intermediateBufferHandle`、`queueDepth`、`numInputs`、`numOutputs`、`wiredMemory`、`isNewInstance`、`controller`、`txn`、`refcount`
    3. `destroyProgramInstance` / `createProgramInstanceForModel:...` / `_ANEServer unloadModel:options:qos:withReply:` 是当前最直接的 non-H16 unload/create lifecycle surface
    4. 初筛未找到 `0x201/0x401` command-specific durable-state echo
  - 结论：
    - verdict=`inconclusive`：non-H16 surface 可继续查，但第一轮只证明 user-space wrapper/cache carrier 存在，尚未证明 replayable firmware-published state carrier
    - 下一轮应检查 `_ANEProgramForLoad destroyProgramInstance` 与 `createProgramInstanceForModel:...` 内部 native call boundary，定位 exact `ANEProgramDestroy/Create` carrier 及 output struct 是否含可复用 state word
- 2026-06-23 已完成 visible H16 blocker 后的下一控制层路线选择：
  - 新证据：
    - `mps/ANE/.ane_runs/json/next_control_layer_route_selection_20260623.json`
    - `mps/ANE/.ane_runs/csv/next_control_layer_route_selection_20260623.csv`
  - 当前事实：
    1. firmware-side command/reply handler recovery 当前缺少本机可见的 `0x201/0x401` firmware handler blob，暂缓
    2. safe low-level dynamic observation 已由 `record1b8_dynamic_observation_feasibility_20260623` 判定为当前机器不可安全执行
    3. non-H16 carrier search 具有现成本地证据面：ANEServices/aned/IOConnect traces、selector carrier verdicts、daemon-chain CSV、`mps/ANE/experiments/aned_bin.i64`
  - 结论：
    - verdict=`confirmed`：下一控制层获取路线选择 `non_h16_carrier_search`
    - 下一轮从 `aned_bin.i64` 与现有 selector/daemon-chain CSV 查找 firmware-published durable state 是否上浮到 user-space daemon/request/descriptor carrier
- 2026-06-23 已输出 visible H16 unload durability layer firmware-private blocker package：
  - 新证据：
    - `mps/ANE/.ane_runs/json/unload_firmware_private_blocker_20260623.json`
    - `mps/ANE/.ane_runs/csv/unload_firmware_private_blocker_20260623.csv`
  - 当前事实：
    1. `sendSetupCmd(0x401)` 无 visible reply-word copyback
    2. `0x401` / typed fallback `0x201` wrapper pair 只暴露 status-only join
    3. lower H16 `aneFirmwareCommandSend` / `IOProcessorChannelSendRetry` / `handleOutstandingCommand` 没有 command-specific `0x201/0x401` consumer
    4. visible `ProgramUnload` / `isProcessValid` shell 不是 durable author
    5. 当前机器没有安全可授权的 boot-kernel `record+0x1b8` pre/post dynamic observation path
  - 结论：
    - verdict=`confirmed`：visible H16 unload durability/control layer 已可判死；remaining authority 下沉到 firmware-private command/reply semantics 或更低 reply-publish path
    - long_term_status=`not_complete`：长期目标尚未完成；下一轮需选择下一控制层获取路线：firmware-side command/reply handler recovery、安全低层动态观测、或 non-H16 carrier 搜索
- 2026-06-23 已完成 command `0x201/0x401` lower submit/completion command-specific consumer probe：
  - 新证据：
    - `mps/ANE/experiments/ane_bootkc_unload_command_specific_completion_probe.py`
    - `mps/ANE/.ane_runs/csv/ane_bootkc_unload_command_specific_completion_probe.csv`
    - `mps/ANE/.ane_runs/json/unload_command_specific_completion_20260623.json`
    - `mps/ANE/.ane_runs/csv/unload_command_specific_completion_20260623.csv`
  - 当前事实：
    1. H16 `__TEXT_EXEC` 中 exact immediate `0x201/0x401` 命中共 18 个
    2. real command builders 仍集中在 `ReleaseProgramResource` / `ProgramUnload` / `sendSetupCmd` / load-path wrappers
    3. `IOProcessorChannelSendRetry` 中 command-specific `0x201/0x401` consumer 命中为 0
    4. `handleOutstandingCommand` 中 command-specific `0x201/0x401` consumer 命中为 0
    5. `aneFirmwareCommandSend` 中唯一 exact `0x201` hit 是 `add x3, x3, #0x201` 的 `os_log` address offset，不是 command comparison / reply publish / target-state author
    6. focused lower submit/completion windows 未发现 command-specific target-field write/copyback/consumer
  - 结论：
    - verdict=`falsified`：command `0x201/0x401` 在 H16-visible lower submit/completion path 中没有 command-specific consumer
    - 下一轮应准备 firmware-private blocker package：串联 no visible `0x401` copyback、no visible `0x201/0x401` wrapper side effect、no lower H16 command-specific submit/completion consumer
- 2026-06-23 已完成 `ProgramUnload` unload setup pair (`0x401` / `0x201`) side-effect probe：
  - 新证据：
    - `mps/ANE/experiments/ane_bootkc_unload_setup_pair_probe.py`
    - `mps/ANE/.ane_runs/csv/ane_bootkc_unload_setup_pair_probe.csv`
    - `mps/ANE/.ane_runs/json/unload_setup_pair_status_only_20260623.json`
    - `mps/ANE/.ane_runs/csv/unload_setup_pair_status_only_20260623.csv`
  - 当前事实：
    1. feature-enabled path 使用 `sendSetupCmd(0x401)`，payload size 为 `0x0c`，且无 post-send payload copyback
    2. feature-disabled fallback 构造 typed firmware command `0x201`，payload size 同为 `0x0c`
    3. fallback 在 send 前把 `*[sp+0x48]` 预置为 `-1`，这是 local word preseed，不是 send 后 reply copyback
    4. fallback 通过 `ANEHWDevice::aneCmdSend(ANEFirmwareCommand)` 发送 typed command
    5. typed sender 与 raw sender wrapper 都把 lower send result 作为 `x0` status 返回
    6. 两条 path 在 `ProgramUnload` 中 join 到同一个 `x0` status consumer，未发现 status 以外的 visible target-field write/copyback/consumer
  - 结论：
    - verdict=`falsified`：`0x401` / `0x201` unload setup pair 在 visible H16 wrapper 层不是 durable-state author
    - 下一轮应移动到更低的 command-specific submit/completion boundary，检查 command `0x201/0x401` 是否在 lower firmware command completion 中有专门 consumer；若仍无 H16 visible command-specific consumer，则准备 firmware-private blocker package
- 2026-06-23 已完成 `sendSetupCmd(0x401)` payload / reply carrier probe：
  - 新证据：
    - `mps/ANE/experiments/ane_bootkc_sendsetup401_payload_probe.py`
    - `mps/ANE/.ane_runs/csv/ane_bootkc_sendsetup401_payload_probe.csv`
    - `mps/ANE/.ane_runs/json/sendsetup401_payload_semantics_20260623.json`
    - `mps/ANE/.ane_runs/csv/sendsetup401_payload_semantics_20260623.csv`
  - 当前事实：
    1. `ProgramUnload` feature-gated path 调用 `sendSetupCmd(0x401, [sp+0x48], 0)`，`x3=0`
    2. `sendSetupCmd` 对 command `0x401` 分配 `0x0c` payload，只把 `*arg1` marshal 到 `payload+0x08`
    3. `sendSetupCmd` 中唯一 visible `*arg2` 读取属于 `0x403` path，不属于 `0x401`
    4. success copyback 只覆盖 `0x400 -> *arg1` 与 `0x402 -> *arg2`；`0x401` 成功后直接 free/return，没有 payload copyback
    5. `ProgramUnload` 调用后只消费 `x0` status（`mov x26, x0` / `cbz w0`），不消费 copied reply word
    6. feature-disabled fallback 会构造 typed firmware command `0x201`，并在 send 前把 `*[sp+0x48]` 置为 `-1`
  - 结论：
    - verdict=`falsified`：`sendSetupCmd(0x401)` reply word 不是 visible CPU-side durable state carrier，不能解释 `process+0x203fc == 2`、`record+0x1b8` 或 `resource+0x402f0`
    - 下一轮应比较 feature-enabled `0x401` 与 typed fallback `0x201` / raw-send completion boundary，判断 unload durability 是否已经完全下沉到 firmware-private semantics，或仍有 H16 visible status side effect
- 2026-06-23 已完成 `ProgramUnload` cold continuation / `isProcessValid` return path probe：
  - 新证据：
    - `mps/ANE/experiments/ane_bootkc_programunload_cold_continuation_probe.py`
    - `mps/ANE/.ane_runs/csv/ane_bootkc_programunload_cold_continuation_probe.csv`
    - `mps/ANE/.ane_runs/json/programunload_cold_continuation_firmware_handoff_20260623.json`
    - `mps/ANE/.ane_runs/csv/programunload_cold_continuation_firmware_handoff_20260623.csv`
  - 当前事实：
    1. `ProgramUnload` accepted continuation sample 从 `0xfffffe000928275c` 开始，窗口计数为 `target_hits=2 stores=13 loads=17 calls=4 branches=14`
    2. 两个 `0x2f0` 命中是 static table base add，不是 `resource+0x402f0` alias 访问
    3. accepted continuation 在条件路径上调用 `ANEFirmwareManager::sendSetupCmd` at `0xfffffe00092bd74c`
    4. 局部反汇编显示该调用形态为 `sendSetupCmd(0x401, [sp+0x48], 0)`
    5. `isProcessValid` return window 只读取 `process+0x203fc` 并返回，不 author state-2
    6. visible `process+0x203fc` source-provenance 仍只有 init/0/1 families，`const_two_source_count=0`
  - 结论：
    - verdict=`confirmed`：visible ProgramUnload/isProcessValid shell 不是 CPU-side durable author，下一层收敛到 firmware setup command handoff
    - 下一轮应恢复 `ANEFirmwareManager::sendSetupCmd(0x401)` 的 payload/reply semantics，尤其是 `[sp+0x48]` payload layout 是否能解释 `process+0x203fc == 2` 或 `record+0x1b8`
- 2026-06-23 已完成 unload-side post-send `device slot+0x9c0 -> 0x927d410` family 静态 probe：
  - 新证据：
    - `mps/ANE/.ane_runs/json/unload_postsend_revalidation_boundary_20260623.json`
    - `mps/ANE/.ane_runs/csv/unload_postsend_revalidation_boundary_20260623.csv`
    - `mps/ANE/.ane_runs/csv/ane_bootkc_unload_postsend_revalidation_probe.csv`
    - `mps/ANE/.ane_runs/csv/ane_bootkc_program_valid_gate_probe.csv`
  - 当前事实：
    1. restore-side post-send 仍是对照基线：send 后快速 read `record+0x1b8` 并 write `resource+0x402f0`
    2. ProgramUnload post-send 不做即时 record replay，而是进入 `device slot+0x9c0 -> 0x927d410`
    3. `device slot+0x9c0` 已解析为 `ANEHWDevice::isProgramValid` at `0xfffffe0009285d0c`，语义是 resource pointer membership validation
    4. `0x927d410` 已解析为 `ANEHWDevice::isProcessValid`，ProgramUnload 以 `isProcessValid(resource, process, out_index, mode=1)` 形态调用
    5. `isProcessValid` 会读取 `process+0x203fc`，但当前 H16 visible writers 只证明 0/1/init 类写入，没有 state-2 author
    6. `process+0x20400` 属于 `handleOutstandingCommand` completion counter/wakeup bookkeeping，不是 ProgramUnload post-send durable author
    7. 当前打开的 `aned_bin.i64` 是 user-space daemon IDB，不包含 H16 kext functions；可用于 daemon bridge 边界，不可作为 kernel offset 证据
  - 结论：
    - verdict=`inconclusive`：unload post-send family 已解析成 revalidation chain，但未找到 durable lower-state author
    - `record+0x1b8` durable author 与 `process+0x203fc == 2` author 仍缺失
    - 下一轮应 probe `ProgramUnload` cold continuation `0xfffffe000928275c` 和 `isProcessValid` return path；若仍无 author，则正式把该层下沉到 firmware-private reply/payload semantics
- 2026-06-23 已完成 firmware request/reply payload semantics vs lower reply-publish/completion side effects 的下一层 target 选择：
  - 新证据：
    - `mps/ANE/.ane_runs/json/firmware_reply_vs_completion_priority_20260623.json`
    - `mps/ANE/.ane_runs/csv/firmware_reply_vs_completion_priority_20260623.csv`
  - 当前事实：
    1. visible typed completion route 已证伪为 direct durable author；completion payload `+0x50/+0x68/+0x88` 仍是 carrier/lookup/callback bookkeeping
    2. firmware request/reply payload semantics 仍可能是最终原因，但当前没有 concrete payload grammar、handler、selector 或 reply field 证据
    3. restore-side post-send 已有对照：send 后短间隔 replay `record+0x1b8` 并 mirror 到 `resource+0x402f0`
    4. unload-side post-send 与 restore 不同：send 后进入 `device slot+0x9c0 -> 0x927d410` family，而不是即时 `record+0x1b8` replay
    5. cleanup/counter 证据给出 driver-visible 邻近状态面：`client_ctx+0x18 -> ANE_ProcessDestroy_gated -> resource+0x400d0` 和 `process+0x20400` counter/wakeup family
  - 结论：
    - verdict=`confirmed`：下一轮最窄 target 是 lower reply-publish/completion side effects，具体 surface 为 unload-side post-send `device slot+0x9c0 -> 0x927d410` family
    - firmware payload semantics 暂作为 fallback；只有当 unload-side post-send family 被证明只是 bookkeeping 时再正式下沉
    - 下一轮应比较 restore-side replay 与 unload-side post-send divergence，检查 `record+0x1b8` / `process+0x203fc` / `process+0x20400` / gate `+0x220` / `resource+0x402f0` 的读写或转发
- 2026-06-23 已完成 visible typed completion route 的 durable-author 判定：
  - 新证据：
    - `mps/ANE/.ane_runs/json/typed_completion_no_record_author_boundary_20260623.json`
    - `mps/ANE/.ane_runs/csv/typed_completion_no_record_author_boundary_20260623.csv`
  - 当前事实：
    1. `handleOutstandingCommand` visible completion facts 主要是 `inner_record+0x58` completion_status、`inner_record+0x88` callback sink、resource lookup key、wakeup plumbing、manager cleanup
    2. visible typed completion pipeline 没有 direct `record+0x1b8` read/write
    3. visible typed completion pipeline 没有 gate `+0x220` replay 或 `resource+0x402f0` writeback
    4. cleanup join 进入 `client_ctx+0x18 -> ANE_ProcessDestroy_gated -> resource+0x400d0 removeObject`，属于 process-registry cleanup，不是 durable record author
    5. completion path touch 到 `process+0x20400` counter/wakeup state，但它不同于 `process+0x203fc` state-2 author
  - 结论：
    - verdict=`falsified`：visible typed completion route 不是 `record+0x1b8` 或 alias durable author
    - 下一轮应恢复 firmware request/reply payload semantics 或 current H16 text 以下的 lower reply-publish/completion side effects
- 2026-06-23 已完成 `aneFirmwareCommandSend(...)` 静态边界恢复：
  - 新证据：
    - `mps/ANE/.ane_runs/json/ane_firmware_command_send_static_boundary_20260623.json`
    - `mps/ANE/.ane_runs/csv/ane_firmware_command_send_static_boundary_20260623.csv`
  - 当前事实：
    1. `aneCmdSend(raw)` 只做 stack-local command/callback packaging 并 forward 到 `aneFirmwareCommandSend(...)`
    2. `aneFirmwareCommandSend` 中 `OSValueObject<ANEFirmwareCommandState>` wrapper 与 inner payload 分离；request/body mutations 发生在 `wrapper+0x10` inner payload
    3. first visible hardware-facing submit 是 `IOProcessorChannelSendRetry`
    4. callback family 主要是 `commandWakeup` / callback shell，不直接 author `record+0x1b8`
    5. submit 返回后进入 `handleOutstandingCommand` completion route：status write、optional copyback/free、wakeups/resource lookup、callback sink、manager cleanup
    6. cleanup join 已能下接 `client_ctx+0x18 -> ANE_ProcessDestroy_gated -> resource+0x400d0 removeObject`
  - 结论：
    - verdict=`inconclusive`：visible `aneFirmwareCommandSend` 不暴露直接 `record+0x1b8` 或 alias author
    - 下一轮应静态恢复 `handleOutstandingCommand` / completion route，寻找 status/copyback/resource lookup/callback/cleanup 中是否存在 durable state author
- 2026-06-23 已完成 `record+0x1b8` raw-send boundary 动态可执行性判断：
  - 新证据：
    - `mps/ANE/.ane_runs/json/record1b8_dynamic_observation_feasibility_20260623.json`
    - `mps/ANE/.ane_runs/csv/record1b8_dynamic_observation_feasibility_20260623.csv`
    - `mps/ANE/.ane_runs/csv/ane_bootkc_raw_send_packaging_probe.csv`
    - `mps/ANE/experiments/results/raw_send_packaging_note.md`
  - 当前事实：
    1. 现有 runtime harness / userland IOConnect trace 太高层，不能直接读 `record+0x1b8` pre/post-send
    2. 当前 Frida 路径适用于 ANEServices/IOConnect 用户态 surface，不适用于 bootkc/kernel `ANE_RestoreState::aneCmdSend(raw)` 读点
    3. 当前机器 SIP enabled；最小 dtrace BEGIN probe 报 `DTrace requires additional privileges`
    4. 既有证据显示 protected daemon live attach 被拒绝，而目标读点还低于 daemon user-space
    5. `aneCmdSend(raw)` 静态边界已证明只做 stack-local command/callback packaging 并 forward 到 `aneFirmwareCommandSend(...)`
  - 结论：
    - verdict=`falsified`：在当前机器/工具约束下，没有安全可授权的动态路径执行 `record+0x1b8` pre/post raw-send probe
    - 下一轮应静态恢复 `aneFirmwareCommandSend(...)` 及其 callback/completion/replay path，寻找 `record+0x1b8` 或 alias author
- 2026-06-23 已完成 `record+0x1b8` raw-send boundary probe plan：
  - 新证据：
    - `mps/ANE/.ane_runs/json/record1b8_raw_send_boundary_probe_plan_20260623.json`
    - `mps/ANE/.ane_runs/csv/record1b8_raw_send_boundary_probe_plan_20260623.csv`
  - 当前事实：
    1. `ANE_RestoreState` 在 `0xfffffe00092c1d34` finalizes `x1=selected_record_ptr`
    2. `0xfffffe00092c1d60` 调用 `ANEHWDevice::aneCmdSend(raw)`，pre-send 可读 `*(uint32_t *)(x1+0x1b8)`
    3. raw send 返回后，`0xfffffe00092c1d74` recomputes `x8=selected_record_ptr`
    4. `0xfffffe00092c1d78` 读取 `record+0x1b8`
    5. `0xfffffe00092c1d7c` 把该值 mirror 到 `resource+0x402f0`
  - 结论：
    - verdict=`confirmed`：最小 probe plan 已具备单一 state word、两个读点和明确 pass/fail 条件
    - execution_status=`plan_only_not_run`，尚未执行 kernel/firmware dynamic observation
    - 下一轮应判断是否存在安全可授权的动态观察路径；否则继续静态恢复 `aneCmdSend(raw)` 以下
- 2026-06-23 已完成下一层 target 选择：
  - 新证据：
    - `mps/ANE/.ane_runs/json/next_lower_target_priority_20260623.json`
    - `mps/ANE/.ane_runs/csv/next_lower_target_priority_20260623.csv`
  - 当前事实：
    1. `process+0x203fc` 的 state-2 author 已低于 visible H16 store/helper/copy surface，且很可能受 record/table 或 firmware-driven lifecycle state 驱动
    2. `record+0x1b8` 的 exact visible stores 在 ProgramLoad / ANE_RestoreState / Legacy load / ProgramReMap 中仍为 0
    3. Legacy `_memmove(record, scratch, w24)` 已被证明是 small mode-sized prefix copy，不能覆盖 `record+0x1b8`
    4. `ANE_RestoreState -> aneCmdSend(raw)` 后到 `record+0x1b8` read 的 visible H16 interval 极短，未见独立 store/call
  - 结论：
    - verdict=`confirmed`：下一层最窄 target 是 `record+0x1b8` durable author
    - 下一轮应准备最小 raw-send boundary probe plan：比较 `ANE_RestoreState::aneCmdSend(raw)` 前后 `record+0x1b8` 是否变化
- 2026-06-23 已完成 `resource+0x400d0` deeper materializer boundary 复核：
  - 新证据：
    - `mps/ANE/.ane_runs/json/resource400d0_deeper_materializer_boundary_20260623.json`
    - `mps/ANE/.ane_runs/csv/resource400d0_deeper_materializer_boundary_20260623.csv`
    - `mps/ANE/.ane_runs/csv/ane_bootkc_resource_gate_cluster_memmove_probe.csv`
    - `mps/ANE/.ane_runs/csv/ane_bootkc_resource_gate_host_stack_probe.csv`
  - 当前事实：
    1. visible constructor / setup / create / load lifecycle 对 `resource+0x400d0` 的 target-covering positive store count 为 0
    2. 唯一 exact target-covering store 仍是 `ANEProgramResource::free` 的 teardown clear
    3. `resource+0x400c0..0x40100` 的 `memcpy/memmove/bzero/memset` bulk-cover scans 报 `window_hits=0 target_hits=0`
    4. host-stack note 已把缺口从 “H16 未找到” 下压到 “visible live host H16/HAL direct/bulk surface 均未找到”
  - 结论：
    - verdict=`inconclusive`：deeper materializer 未找到，但当前 visible helper/direct/bulk materializer hypothesis 已显著削弱
    - `resource+0x400d0` first positive author 更可能位于 lower runtime-owned registration/materializer phase，或当前 static scans 未覆盖的 path
    - 下一步应在 `record+0x1b8` durable author、`process+0x203fc` decisive lifecycle author、或 dynamic timing probe 之间选择最小下一层 target
- 2026-06-22 已完成 `device+0x4f8` / `resource+0x400d0` writer trace：
  - 新证据：
    - `mps/ANE/.ane_runs/json/device4f8_resource400d0_writer_trace_20260622.json`
    - `mps/ANE/.ane_runs/csv/device4f8_resource400d0_writer_trace_20260622.csv`
    - `mps/ANE/.ane_runs/csv/ane_bootkc_resource_gate_first_author_probe.csv`
    - `mps/ANE/experiments/results/bootkc_resource_gate_first_author_probe.md`
  - 当前事实：
    1. `device+0x4f8` first writer 已定位：`ANEHWDevice::initializeANEProperties` 在 `0xfffffe00092e4474` 执行 `str x0, [x19, #0x4f8]`
    2. `ANE_ProgramCreate_gated` 在 `0xfffffe000928c26c` 通过 OSArray slot `+0x1e8` 把 resource provisional insert 到 `device+0x4f8`
    3. `resource+0x400d0` 已确认是 resource-owned process registry；`ANE_ProcessCreate_gated.cold.1` 在 `0xfffffe0009375834` 通过 OSArray slot `+0x1e8` 插入 `ANEProcess*`
    4. `resource_gate_first_author` probe 确认 visible constructor / initial setup / createProgramResource / legacy load / legacy mutable setup / RT load 的 target-covering positive store 数为 0
    5. 当前唯一 exact `resource+0x400d0` target-covering store 是 `ANEProgramResource::free` 的 destructor clear：`0xfffffe00093050f4 str xzr, [x24, #0xd0]`
  - 结论：
    - verdict=`inconclusive`：`device+0x4f8` writer 已解决，`resource+0x400d0` entry writer 已解决，但 `resource+0x400d0` pointer first positive author 仍未知
    - 下一轮应追更深 materializer：helper call、bulk-copy path、或 visible resource setup 之后 / lookup-process-create 之前的 device/scheduler registration
- 2026-06-22 已完成现有 harness replay feasibility 检查：
  - 新证据：
    - `mps/ANE/.ane_runs/json/existing_harness_replay_feasibility_20260622.json`
    - `mps/ANE/.ane_runs/csv/existing_harness_replay_feasibility_20260622.csv`
  - 当前事实：
    1. `frida_selector9_raw_prepare_trace.js` 的 IOConnect hook 只抓 selector/input size/input 前 `0x40`/`u32_0x30`/output 前 24B
    2. raw_prepare hook 只抓 `prefix_56b_before/after` 与 `u32_0x30_before/after`
    3. 当前 `ANEServicesProgramCreate` 只被 dlsym / symbol-resolution 监控，没有 capture/inject 参数逻辑
    4. `frida_selector9_patch_a614.js` 只 patch descriptor+0xa614，已知不触及 resource/process/client tuple
    5. `ANE_ProgramInitialSetup` / `ANE_ProcessCreate_gated` 是 bootkc/kernel 路径，不是当前 user-space Frida harness 可直接 hook 的普通函数
  - 结论：
    - verdict=`falsified` 仅针对窄假设：“现有 harness 已足以直接 capture/replay `additional_params+0x60/+0x68` 或 `resource+0x493a0[0]`”
    - 这不判死更深 artifact/program authoring contract；下一轮应转向追踪 `device+0x4f8` / `resource+0x400d0` writer
- 2026-06-22 已输出 unprivileged direct selector-9 route 的 current-route blocker package，但直接 replay 实验尚未执行：
  - 新证据：
    - `mps/ANE/.ane_runs/json/unprivileged_direct_selector9_route_blocker_20260622.json`
    - `mps/ANE/.ane_runs/csv/unprivileged_direct_selector9_route_blocker_20260622.csv`
  - 当前事实：
    1. `InitialChecks` author 出 `additional_params+0x60/+0x68` resource/process pair，并由 `ANERequest::init` 复制到 `request+0x28/+0x30`
    2. `resource+0x493a0[0]` 属于 create-instance / process-args 的 split-seeded carrier，不等价于 visible `qword_0x10` 或 `programHandle`
    3. 当前 accepted reuse 至少需要 driver wrapper registry 与 device resource/process registry 同时 coherent
    4. add-client 路径还需要 live client context、`isProcessValid`、process/code-sign/team-id/executable-path identity binding
    5. shared acceptance stack 仍停在 `device+0x4f8 -> resource+0x400d0 -> process+0x203fc -> pending/remap/load -> client attach`，runtime-authorable accepted artifact/program body 尚未到达
  - 结论：
    - verdict=`inconclusive`，因为 capture+inject `{resource, process}` 的直接 replay/synthesize 实验未执行
    - 但 current-route blocker 已成立：现有 visible selector-4/direct selector-9 probes 没有证明可写入或重放 lower-authored resource/process/client tuple
    - 下一轮应做最小 replay feasibility probe；若无法从 user-space 捕获/注入 `additional_params+0x60/+0x68`，则转向追踪 `device+0x4f8` writer，定位 accepted artifact/program authoring contract 是否存在
- 2026-06-22 已恢复 ProgramCreate / InitialSetup 对 direct selector-9 carrier 的语义 author/source：
  - 新证据：
    - `mps/ANE/.ane_runs/json/programcreate_initialsetup_author_source_verdict_20260622.json`
    - `mps/ANE/.ane_runs/csv/programcreate_initialsetup_author_source_verdict_20260622.csv`
  - 当前事实：
    1. visible selector-4 args 不能靠任意非零 `qword_0x10` 解决；`programHandle` surrogate 和 daemon-layout `qword_0x10=1` 都不移动 `0xe00002c2`
    2. create-instance process args 是 split-seeded tuple：`process_args[0] <- resource+0x493a0[0]`、`process_args[8] <- hidden local handle/additional_params+0x18`、`process_args[16] <- visible client key`
    3. `additional_params+0x18` 是 hidden local handle / process-key sidecar，会进入 `lookupProgramResource(local_y, &process, 0)`
    4. `InitialChecks` 写 `additional_params+0x60 = resource` 与 `additional_params+0x68 = process`，`ANERequest::init` 再复制到 `request+0x28/+0x30`
    5. `resource+0x493a0 qword0` 参与 request builder 与 `device+0x98` cache coherence
  - 结论：
    - direct selector-9 carrier 不是单 visible field，而是 lower-authored resource/process/client tuple
    - 下一轮应判断 `resource+0x493a0[0]` / `additional_params+0x60/+0x68` authoring 是否能由现有 user-space probe replay/synthesize；若不能，应输出当前 unprivileged direct selector-9 route 的 blocker package
- 2026-06-22 已把 direct selector-9 `0xe00002c2` blocker 收敛为 process/resource carrier tuple 问题：
  - 新证据：
    - `mps/ANE/.ane_runs/json/direct_selector9_process_carrier_gate_verdict_20260622.json`
    - `mps/ANE/.ane_runs/csv/direct_selector9_process_carrier_gate_verdict_20260622.csv`
  - 当前事实：
    1. early validation family (`0x38/0x3950/0xa614/0x3040`) 是真实 gate，但 `0xa614=1` 单点不移动 direct selector-9 的 `0xe00002c2`
    2. later `lookupProgramResource` / process branch 需要语义正确的 `prepare_args+0x10` / process carrier，而不是任意非零值
    3. `qword10=current programHandle` 与 daemon-layout `qword_0x10=1` 都仍停在 `0xe00002c2`
    4. selector-4 `input+0x30` / `program+0xa8` 只证明 visible buffer 可写，不是直接 lower consumer
  - 结论：
    - direct selector-9 当前缺口不是 `0xa614` 或 `qword10` 单字段 patch，而是 ProgramCreate / InitialSetup 语义 author 出来的 resource/process carrier tuple
    - 下一轮应恢复 selector-4 `args+0x10/+0x18/+0x20/+0x8` 的正确 author/source，优先从静态 `STR X1,[X0,#0x18]` programHandle author 和能流入 `qword_0x10` 的运行字段开始
- 2026-06-22 已完成 selector-9 自然触发 probe 路径矩阵：
  - 新证据：
    - `mps/ANE/.ane_runs/json/selector9_natural_probe_path_matrix_verdict_20260622.json`
    - `mps/ANE/.ane_runs/csv/selector9_natural_probe_path_matrix_verdict_20260622.csv`
  - 当前事实：
    1. `ANEServicesProgramChainingPrepare` wrapper 会被调用，但返回 `0x14`，没有驱动可观察 selector-9 IOConnect
    2. DYLD IOKit interposer 路线只有 header-only CSV / empty JSON / killed probe
    3. same-connection selector-9 repeat 在两个 orthogonal precompiled cases 上都没有改变 second-call status 或 24-byte output prefix
    4. manual selector-9 direct transport 曾经真实成立，但 baseline、`0xa614=1`、`qword10=current programHandle` 都停在 `0xe00002c2`
    5. 当前可运行 entitled selector-9 host 被 AMFI restricted-entitlement signature validation 卡住
  - 结论：
    - “找一个现有 unprivileged natural selector-9 probe 并移动 gate”的假设已被收敛：没有现成路径能同时自然产生 selector-9 且移动 retained-control gate
    - 下一轮应围绕 direct selector-9 的第二个 exact `0xe00002c2` gate，恢复 `lookupProgramResource(*prepare_args+0x10, &process, 0)` 所需 carrier/process state
- 2026-06-22 已完成 selector-4 input buffer 字段级 diff：
  - 新证据：
    - `mps/ANE/experiments/selector4_input_field_diff.py`
    - `mps/ANE/.ane_runs/json/selector4_input_field_diff_verdict_20260622.json`
    - `mps/ANE/.ane_runs/csv/selector4_input_field_diff_verdict_20260622.csv`
  - 当前事实：
    1. baseline / `a8_one` 都有 `iokit_enter=7`、`raw_prepare_enter=10`
    2. 已分类 mutation offsets：`iokit_enter_input:0x8`、`iokit_enter_input:0x30`、`raw_prepare_input:0x30`
    3. 其余差异都落在 run-specific pointer/id/sequence 类字段：`0x0/0xc/0x18/0x1c/0x24/0x28/0x2c`
    4. 没有剩余 unclassified offsets
  - 结论：
    - selector-4 visible input surface 已 `falsified` 为当前 lower-control carrier：除已知 a8/u32_0x30 可见变化和运行噪声外，没有新的稳定可写控制字段
    - 下一轮应停止围绕 `program+0xa8` / selector-4 status 面继续扩散，转向构造或定位自然触发 selector-9 traffic 的 probe 路径
- 2026-06-22 已完成 client-side Frida precise capture 的 `program+0xa8` paired trace join：
  - 新证据：
    - `mps/ANE/experiments/program_wrapper_a8_frida_trace_join.py`
    - `mps/ANE/.ane_runs/json/program_wrapper_a8_frida_trace_join_verdict_20260622.json`
    - `mps/ANE/.ane_runs/csv/program_wrapper_a8_frida_trace_join_verdict_20260622.csv`
    - `mps/ANE/.ane_runs/logs/program_wrapper_a8_frida_attach_baseline_20260622.jsonl`
    - `mps/ANE/.ane_runs/logs/program_wrapper_a8_frida_attach_a8_one_20260622.jsonl`
  - 当前事实：
    1. baseline 与 `a8_one` trace 都有 414 行，事件计数一致：`raw_prepare_enter=10`、`raw_prepare_leave=10`、`iokit_enter=7`、`iokit_leave=7`
    2. 两边 IOConnect selector surface 一致：`{"4": 14}`
    3. mutation 已可见：raw_prepare / selector-4 input 的 `u32_0x30` 从 baseline 的 `0x00000000` 变成 `a8_one` 的 `0x00000001`
    4. return-status surface 没有变化：raw_prepare ret 仍是 `3758097089/3758097090`，IOKit ret 仍是 `3758097090`
  - 结论：
    - `program+0xa8` 作为当前 visible raw_prepare / selector-4 status 控制面已 `falsified`
    - 下一轮应下钻到 selector-4 input buffer 字段级 diff，找出除 `u32_0x30` 外是否存在更接近 lower control layer 的可写字段或自然 selector-9 触发路径
- 2026-06-22 已判定当前 `modelmanagerd` 非 daemon replacement harness 路线不可用：
  - 新证据：
    - `mps/ANE/experiments/modelmanager_simulator_service_probe.py`
    - `mps/ANE/.ane_runs/json/modelmanager_simulator_service_probe_20260622.json`
    - `mps/ANE/.ane_runs/csv/modelmanager_simulator_service_probe_20260622.csv`
    - `mps/ANE/.ane_runs/json/modelmanager_non_daemon_harness_verdict_20260622.json`
    - `mps/ANE/.ane_runs/csv/modelmanager_non_daemon_harness_verdict_20260622.csv`
  - 当前事实：
    1. 同一组 public task-like message body 发给 `com.apple.modelmanager` 时，`message_20_false/true` 能进入 `ModelXPCRequest` decode，并返回 `Invalid number of keys found, expected one`
    2. 同一组 body 发给 `com.apple.modelmanager.simulator` 时，只返回 `XPCErrorDescription: Connection interrupted`
    3. 已有 `LoadAssetBundle` / `HoldAssetBundle` client-side route 先撞 `notSupportedOnExternalBuild` gate
    4. 高层 `ModelManagerServices` Swift direct client surface 仍不可用；`PrewarmSession` 虽更深，但依赖有效 session/internal state，不能独立观察 `transitionAsset` dynamic-mode 面
  - 结论：
    - simulator service / client-side route 作为不替换 daemon 的最小 harness 已 `falsified`
    - 下一轮应转向已有可用的 client-side Frida precise capture 路线，观察私有 ANE load/compile 交通是否随可控 client-side artifact/request mutation 变化
- 2026-06-22 已判定当前用户态不存在安全的 `transitionAsset` patched-command 路径：
  - 新证据：
    - `mps/ANE/.ane_runs/json/modelmanagerd_transitionasset_patched_command_path_verdict_20260622.json`
    - `mps/ANE/.ane_runs/csv/modelmanagerd_transitionasset_patched_command_path_verdict_20260622.csv`
  - 当前事实：
    1. `modelmanagerd` 是 `system/com.apple.modelmanagerd` LaunchDaemon，程序路径 `/usr/libexec/modelmanagerd`，运行用户 `_modelmanagerd`
    2. SIP 当前启用，系统二进制路径带 `restricted,compressed` 标志
    3. patched thin slice 是 arm64e 单架构，`codesign --verify --strict` 报 `invalid signature (code or signature have been modified)`
    4. ad-hoc 重签只能让临时副本通过本地签名验证，但不能保留 Apple platform/private entitlements，因此不能等价替代 Apple-signed daemon
    5. `lldb` 和 `frida` attach live pid 528 都被当前用户权限拒绝
  - 结论：
    - 当前轮 `--patched-command` 假设已 `falsified`
    - paired runtime wrapper 仍保留，但 patched half 不能通过普通 current-user command 执行
    - 下一轮应检查 `com.apple.modelmanager.simulator` Mach service 或 ModelManagerServices client-side route 是否能提供不替换 daemon 的观察/控制路径
- 2026-06-22 已新增 `transitionAsset` dynamicMode paired runtime probe wrapper，并生成 plan-only JSON/CSV：
  - 新证据：
    - `mps/ANE/experiments/modelmanagerd_transitionasset_dynamicmode_runtime_probe.py`
    - `mps/ANE/.ane_runs/json/modelmanagerd_transitionasset_dynamicmode_runtime_probe_20260622.json`
    - `mps/ANE/.ane_runs/csv/modelmanagerd_transitionasset_dynamicmode_runtime_probe_20260622.csv`
  - 当前事实：
    1. wrapper 默认不替换系统 daemon；patched run 必须通过 `--run-patched --patched-command ...` 显式传入
    2. plan-only 输出已成功解析现有 baseline profile：`wall_time_s=43.00265733300148`、`transformer_compile_s=5.712273664999884`、`transformer_eval_s=20.669240746992728`
    3. 当前 verdict 是 `inconclusive`，原因是 patched command 还没有安全执行路径，patched 行为仍是 `not_run`
    4. 下一轮不是再写判据，而是选择最小安全 patched-command/daemon 注入路径，并补齐 baseline/patched 的统一日志窗口
- 2026-06-22 已完成 `transitionAsset` dynamicMode patch 的运行级判据设计 / 执行准备：
  - 新证据：
    - `mps/ANE/.ane_runs/json/modelmanagerd_transitionasset_dynamicmode_runtime_criteria_20260622.json`
  - 当前事实：
    1. 已复验 patch artifact：`mps/ANE/.ane_runs/tmp/modelmanagerd_arm64e_transitionasset_dynamicmode_patch_20260622`
    2. `0x10006881c` 在 patched slice 中已反汇编为读取 `LoadState.dynamicMode`，并保留后续原生 `ldr w1` / `str w1, [x22, #0x200]` 数据流
    3. 运行级观察面已固定为四类：`dynamic_mode_success`、`dynamic_mode_failure`、`already_loaded_or_self_heal`、`no_observable_change`
    4. 下一轮必须产出 paired baseline/patched 的 JSON/CSV、统一日志摘录和 `test_clean.m4a` profile/benchmark 摘要；不能只凭单次 daemon 行为或主观 wall time 下结论
- 2026-06-22 已把 consumer 侧 collapse 再压到 `ModelCatalogProvider` 的具体 vtable 方法，并确认当前用户态无法直接 attach live `_modelmanagerd` 做寄存器读取：
  - 新证据：
    - `mps/ANE/.ane_runs/json/modelmanagerd_query_dispatch_inplace_nil_patch_verdict_20260622.json`
    - `mps/ANE/.ane_runs/json/modelcatalog_harness_vs_patch_verdict_20260622.json`
    - `mps/ANE/.ane_runs/json/modelcatalog_catalogclient_ctor_probe_verdict_20260622.json`
    - `mps/ANE/.ane_runs/json/modelmanagerd_patchpoint_tradeoff_verdict_20260622.json`
    - `mps/ANE/.ane_runs/json/modelmanagerd_create_session_url_handoff_verdict_20260622.json`
    - `mps/ANE/.ane_runs/json/modelmanagerd_modelcatalog_instance_topology_verdict_20260622.json`
    - `mps/ANE/.ane_runs/json/modelmanagerd_modelcatalog_provider_seam_verdict_20260622.json`
    - `mps/ANE/.ane_runs/json/modelmanagerd_user_attach_capability_verdict_20260622.json`
  - 当前 machine-local 事实：
    1. `sub_10010CA70` 已确认是 `ModelCatalogProvider` 的 vtable[9] 方法，是 modelmanagerd 中唯一调用 `ModelCatalog.ClientProtocol.queryResourceBundle(with: URL)` 的 consumer-side seam
    2. createSession continuation `sub_100177FA4` 的数据流已确认：
       - 先调用 `sub_10010CA70`
       - 成功返回后才重新读取 `CreateSessionRequest.metadata.useCaseID`
       - `useCaseID` 仅参与后续 session 标记，不参与 URL 构造
    3. `sub_10010CA70` 本身不从参数取 URL，而是通过 `self.vtable[0x10]` 调度一个 `ModelCatalogProviding` 协议方法来派生 URL，再调用 `queryResourceBundle(with:)`
    4. 因而当前更可能承载 URL 构造输入的，不是 `useCaseID`，而是更早注入到 `ModelCatalogProvider` / `ModelCatalogProviding` self 状态里的 `assetBundleURI` 或其派生字段
    5. live daemon 动态 attach 在当前用户态已确认不可用：
       - `lldb` attach 到 pid 528 失败，原因是用户 `baicai1145` 不能附加到运行于 `_modelmanagerd` 账户下的进程
       - `frida -p 528` 同样失败，报 `unable to access process ... from the current user account`
    6. `ida` 已进一步确认：
       - `addSession(metadata:auditToken:alreadyLockedInferenceProvider:isUnentitled:)` 会分配 `DaemonSession`
       - `ModelCatalogProvider` 被装箱后存入 `DaemonSession.modelCatalog`
       - `CreateSessionRequest.metadata.assetBundleURI.getter -> sub_10010CA70 -> ModelClientProtocol.queryResourceBundle(with:)`
    7. 现在已进一步确认：
       - `DaemonContext.modelCatalog`
       - `UseCaseManager.modelCatalog`
       - `DaemonSession.modelCatalog`
       - `PolicyManager.modelCatalog`
       - `RemoteManager.modelCatalog`
       这 5 个持有者共享同一个 `ModelCatalogProvider` 分配/传递链，而不是各自独立构造
    8. 因而当前最合理的解释变成：
       - provider 是共享实例
       - lookup URL 是 **per-call 显式参数**
       - `assetBundleURI` 的真正注入层不在 provider 长生命周期字段，而在更早的 metadata->local URL buffer 构造路径
    9. 现在又已进一步确认：在 createSession 路径上，`Session.Metadata.assetBundleURI.getter()` 的局部结果会**直接**作为 URL buffer 传给 `sub_10010CA70`，当前没有发现 getter 与 lookup seam 之间还有更深的共享 URL rewrite helper
    10. 两类 patch/hook 点的战略比较也已完成：
        - createSession-specific：`Session.Metadata.assetBundleURI.getter()` 或其直接 callsite
        - shared seam：`sub_10010CA70`（createSession 与 LoadAssetBundle 共用）
        当前主线明确优先后者
    11. 选择 `sub_10010CA70` 的原因是：它是所有真正进入 bundle lookup 的路径所共享的瓶颈点，而 getter/callsite 只适合作为 createSession 局部触发与观察点
    12. 另外，`CatalogClient` 的用户态 harness 路线并未被整体判死：type metadata accessor 可调用，但默认 `cfC/cfc` ctor 入口在当前 ABI 假设下都会 crash
    13. 同时，`ModelCatalog.tbd` 还明确导出了 connection-based client 构造路线：
        - `ModelCatalog.InitializableFromExistingConnection.init(existingConnection:localObject:)`
        - `ModelCatalog.BidirectionalXPCServiceClientConnection.__allocating_init(localObject:delegate:)`
        - 以及其 `existingConnection:` 变体
    14. 修正 X20 约定后的 ctor probe 又进一步确认：它已经不再立即 crash，而是构造期挂起/阻塞，说明 ABI 恢复方向仍有信息量，但尚未达到可用 harness
    15. 因此当前最稳的主线决策是：
        - 用户态 harness：保留为次级调查方向
        - 当前主线：回到 `0x10010CE3C` 的静态 patch/injection 目标
    16. 现在又已进一步有了第一版可复跑的 patch 原型：
        - `0x10010CE18–0x10010CE3C` 被原地改写为“零化 optional existential + 清 X21”
        - 让控制流自然走入现有 nil fallback 路径
        - 不需要 executable code cave
    17. 当前真正待回答的问题已经从“能不能 patch”变成“这条 nil-fallback patch 是否足够保留下游行为，还是需要第二阶段更保真的 patch”
    18. 现有证据已把下一条更深的 host-side 边界收敛到：
        - `InferenceProviderAssetManager`
        - `getInferenceProvider(withDescriptor:)`
        - `assetBundleWithNewAndExistingAssets(for:runtimeAssets:inferenceProviderConnection:)`
        - `InferenceProviderXPCSender.requestInputStreamInference(...)`
        也就是说，接下来的主线不应继续困在纯 ModelCatalog 资源解析函数里，而应沿着 host-side provider handoff 继续往下追
    19. 在这组边界里，当前最值得优先打开的仍是 modelmanagerd 内的 provider-management 层：
        - `InferenceProviderAssetManager`
        - `getInferenceProvider(withDescriptor:)`
        - `assetBundleWithNewAndExistingAssets(for:runtimeAssets:inferenceProviderConnection:)`
        它们比直接跳到 ANECompiler / ANEServices 更接近当前静态证据能够连续追踪到的 first handoff
    20. 当前更具体的优先级已经收敛为：
        - 首先打开 `InferenceProviderAssetManager`
        - 优先追 `assetBundleWithNewAndExistingAssets(for:runtimeAssets:inferenceProviderConnection:)`
        - 再补 `getInferenceProvider(withDescriptor:)` 作为 provider 选择前置层
        因为前者已经拿到了 `inferenceProviderConnection`，更像第一次真正朝 `InferenceProviderXPCSender` request/transition 流推进的 handoff
    21. 另外，当前 machine-local 字符串面又给出一个更具体的 host-side 信号：
        - `InferenceProviderExtensionConnection setCurrentState creating new sender part`
        - `InferenceProviderExtensionConnection addActiveRequest ...`
        - `InferenceProvider requestInputStreamInference (...) executing on %s`
        这提示下一轮不应只盯 `assetBundleWithNewAndExistingAssets(...)`，还应同时关注 `InferenceProviderExtensionConnection` 的 sender-part 创建/状态迁移分支
- 2026-06-22 已把 `ModelCatalog.CatalogErrors.QueryError Code=2` 从“组件级猜测”推进到 case 级硬映射，同时确认 direct non-XPC seam 可用、宿主 ObjC bridge 不可直调：
  - 新证据：
    - `mps/ANE/experiments/modelcatalog_direct_bundle_query_uri_probe.swift`
    - `mps/ANE/experiments/modelcatalog_direct_bundle_query_uri_probe.py`
    - `mps/ANE/.ane_runs/csv/modelcatalog_direct_bundle_query_uri_probe_20260622.csv`
    - `mps/ANE/.ane_runs/json/modelcatalog_direct_bundle_query_uri_probe_verdict_20260622.json`
    - `mps/ANE/experiments/modelcatalog_resource_bundle_container_runtime_probe.m`
    - `mps/ANE/experiments/modelcatalog_resource_bundle_container_runtime_probe.py`
    - `mps/ANE/.ane_runs/csv/modelcatalog_resource_bundle_container_runtime_probe_20260622.csv`
    - `mps/ANE/.ane_runs/json/modelcatalog_resource_bundle_container_runtime_probe_verdict_20260622.json`
  - 当前 machine-local 事实：
    1. IDA 已确认 `QueryError` 的 ordinal 映射：
       - `0 -> invalidURI`
       - `1 -> invalidURIComponents`
       - `2 -> invalidURIString`
       - `3 -> invalidArgument`
       - `4 -> invalidQueryItem`
    2. 因而 `modelmanagerd` 日志里的 `Error Domain=ModelCatalog.CatalogErrors.QueryError Code=2 "(null)"` 已可明确解释为 `invalidURIString`
    3. 用 `@_silgen_name` 直调 `CatalogIndex.resolveResourceBundleQueryURI(uri:)` 与 `VariantHelpers.isResourceBundleQueryURIResolved(uri:)` 已成功打通 direct non-XPC seam，且它会区分 authority / non-authority URL decomposition：
       - `modelcatalog://bundle?id=... -> extractedBundleID=""`
       - `modelcatalog:bundle?id=... -> extractedBundleID="bundle"`
       - `modelcatalog:/bundle?id=... -> extractedBundleID="bundle"`
       - `modelcatalog:///bundle?id=... -> extractedBundleID="bundle"`
       - `file:///tmp/test.asset -> extractedBundleID="test.asset"`
    4. 这证明 `createSession -> modelCatalogError` 的 common collapse 发生在比 direct `CatalogIndex` helper 更高的一层
    5. 与静态 metadata 相反，宿主 runtime 上的 `ModelCatalog.ResourceBundleContainer` 虽然 class 可见，但 method list 只有 `NSSecureCoding` / `description` / `init` 家族，**不响应**：
       - `resourceBundleContainerWithIdentifier:with:`
       - `resourceBundleContainersWith:`
       - `supportedArgumentsFor:with:`
    6. 所以 `ResourceBundleContainer` 当前应视为 host-runtime dead end；下一条高价值 seam 是 **consumer 侧 Swift URL->identifier decomposition**，而不是继续在 ObjC runtime 上硬调静态看到的 selector
- 2026-06-22 已把 `modelcatalog:` 的组件级 QueryError 面再压窄一层，当前最高价值结论是：`QueryError Code=2` 对 host/query/fragment/userinfo/port 级别扰动并不敏感，更像一个早段共用分支，而不是晚段 `invalidQueryItem`：
  - 新证据：
    - `mps/ANE/experiments/modelmanager_create_session_modelcatalog_component_probe.py`
    - `mps/ANE/.ane_runs/csv/modelmanager_create_session_modelcatalog_component_probe_20260622.csv`
    - `mps/ANE/.ane_runs/json/modelmanager_create_session_modelcatalog_component_probe_verdict_20260622.json`
  - 当前 machine-local 事实：
    1. 以下 8 个 `assetBundleURI` 组件级变体全部稳定回到同一个 top-level `modelCatalogError`，没有任何一例掉出这条 gate：
       - `modelcatalog://com.apple.summarizationkit.ota.configuration`
       - `modelcatalog://bundle?id=com.apple.summarizationkit.ota.configuration`
       - `modelcatalog://?id=com.apple.summarizationkit.ota.configuration`
       - `modelcatalog://bundle?id=&empty=1`
       - `modelcatalog://bundle?=com.apple.summarizationkit.ota.configuration`
       - `modelcatalog://bundle?id=com.apple.summarizationkit.ota.configuration#fragment`
       - `modelcatalog://user@bundle?id=com.apple.summarizationkit.ota.configuration`
       - `modelcatalog://bundle:443?id=com.apple.summarizationkit.ota.configuration`
    2. 这 8 个 case 在 `modelmanagerd` 的底层日志都一致命中：
       - `Error Domain=ModelCatalog.CatalogErrors.QueryError Code=2 "(null)"`
    3. 因而“`Code=2` 只是某个对 query key / empty value / empty query-name 敏感的晚段分支”这条假设已被正式证伪
    4. 当前真正剩下的最小分歧不再是表层 URL 值，而是：
       - `QueryError Code=2` 到底落在 `invalidURIString` 还是 `invalidURIComponents`
       - 或 `createSession` 这条高层 carrier 是否额外包了一层统一映射，把多个更细的 ModelCatalog 错误都压成同一个 `Code=2`

- 2026-06-22 又已把 field1 的 `0x12` 家族定性成一个活的 out-of-line `Data` 分支，但它暂时不如 direct `UInt64` 主线高价值：
  - 新证据：
    - `mps/ANE/.ane_runs/json/modelmanager_outofline_data_path_verdict_20260622.json`
  - 当前 machine-local 事实：
    1. field1
       的 `0x12`
       不是死 tag，
       而是真正会消费
       `_CodableOutOfLine[index]`
       的 object-reference
       路径
    2. 用
       `_CodableOutOfLine[0] = uint64(7)`
       时，
       错误会变成：
       `XPC object does not represent valid Data`
       ，说明它期待的是
       `Data-like`
       XPC object，
       不是裸整数对象
    3. 改成
       `_CodableOutOfLine[0] = xpc_data`
       后，
       错误会稳定推进成：
       `Found dangling container in buffer`
    4. 这个结果对
       0-byte、
       1-byte、
       2-byte、
       4-byte、
       8-byte zero、
       8-byte little-endian 7、
       以及 replay 的
       129/162/247-byte
       server body
       都相同
    5. `_CodableOutOfLine4CodableObject`
       仍然不能满足
       这条路径
  - 因而当前对 `0x12` 的判断
    收紧为：
    - `0x12`
      是活的
      out-of-line
      `Data blob`
      分支
    - 但它目前只把 decode
      推到
      nested-container
      层，
      还没比 direct
      field1 `UInt64`
      主线
      更接近
      `ModelXPCRequest`
      根

- 2026-06-22 又已把 `AAAFoundationSwift.MessageSender` 这条 non-thunk wrapper 路径探完，结论是“构造可达，但协议不匹配”：
  - 新证据：
    - `mps/ANE/.ane_runs/json/aaafoundationswift_messagesender_probe_verdict_20260622.json`
  - 当前 machine-local 事实：
    1. 通过 low-level
       throwing-init ABI，
       `AAAFoundationSwift.MessageSender.init(machService:)`
       已可被直接调用
    2. 对
       `com.apple.modelmanager`
       和
       `definitely.invalid.codex.test`
       两个字符串，
       当前都得到
       `err=nil`
       且 raw pointer
       非空
    3. 但 `MessageSender.send`
       的静态约束是：
       `A: AAAFoundationSwift.Message`
    4. 而当前能确认的
       `TaskCancellableMessage<ModelXPCRequest>`
       只有
       `Encodable/Decodable`
       conformance，
       没有
       `AAAFoundationSwift.Message`
       证据
  - 因而当前对 AAA wrapper 的结论
    再次收紧为：
    - wrapper object
      reachability
      已经证明
    - 但 payload-side
      protocol mismatch
      仍然存在
    - 这使得
      `MessageSender`
      路线
      暂时不能替代
      byte-level 主线

- 2026-06-22 又已把 `AAAFoundationSwift.XPCEncoder.encode` 的崩溃进一步压缩成“thunk ABI / entrypoint”问题，而不是 generic body ABI 全局错误：
  - 新证据：
    - `mps/ANE/.ane_runs/json/swift_dispatch_thunk_abi_control_verdict_20260622.json`
  - 当前 machine-local 事实：
    1. 本地控制库
       `DynEncLib`
       同时导出：
       - body symbol
         `...encode...F`
       - thunk-style
         `...FTX`
         / `...FTx`
    2. 用已经校准的
       5 实参 ABI
       调用 body
       symbol
       `...F`
       可以稳定成功
    3. 但把同样的 ABI
       直接拿去调
       `FTX`
       / `FTx`
       ，本地控制库
       也会立刻崩溃
    4. 而
       `AAAFoundationSwift.XPCEncoder.encode`
       当前暴露给我们的，
       正是 thunk-style
       `FTj`
       入口
  - 因而当前对 bridge 路径的判断
    进一步收紧为：
    - 崩点更像是
      `FTj`
      这种 thunk-style
      entrypoint
      的调用约定/隐藏上下文
    - 而不是
      encoder 对象不可构造、
      framework 不可 load、
      或 generic body ABI
      完全错误

- 2026-06-22 已把 `AAAFoundationSwift` 从“shared-cache 里有真实实现”推进到“运行时可 load、constructor 可调，但 `encode` thunk 仍未打通”：
  - 新证据：
    - `mps/ANE/.ane_runs/json/aaafoundationswift_runtime_bridge_verdict_20260622.json`
  - 当前 machine-local 事实：
    1. `AAAFoundationSwift`
       / `BlastDoor`
       / `ModelManagerServices`
       都能通过
       install-name
       直接
       `dlopen`
       / `ctypes.CDLL`
       成功加载
    2. ObjC runtime
       里能看到
       `AAAFoundationSwift.XPCEncoder`
       / `XPCDecoder`
       / `DictionaryEncoder`
       和
       `BlastDoor.XPCEncoder`
       / `XPCDecoder`
       这些类 metadata
    3. 但这些类的
       ObjC method list
       为空，
       说明它们不是
       现成的 ObjC
       selector bridge
    4. `XPCEncoder` /
       `XPCDecoder`
       的 Swift
       constructor
       符号
       已经可以从
       C
       直接调起，
       并返回非空对象指针
    5. 本地对照库
       `LocalEncLib`
       已证明：
       generic instance method
       的低层 ABI
       已被校准成功；
       同一套 5 实参
       （value addr /
       type metadata /
       witness /
       self /
       swifterror）
       能稳定调用
       `LocalEnc.encode<T>`
       并返回
       `{\"v\":\"7\"}`
    6. 但把同一 ABI
       搬到
       `AAAFoundationSwift.XPCEncoder.encode`
       上时，
       无论
       `ctor0()`
       还是
       `ctor1(meta)`
       拿到的实例，
       都会在
       `before encode`
       之后立刻崩溃
  - 因而当前新的高价值 blocker
    是：
    `AAAFoundationSwift.XPCEncoder.encode`
    真正可调用的
    thunk / resilience
    边界，
    而不是 framework
    reachability
- 2026-06-22 已把 `TaskCancellableMessage<ModelXPCRequest>` 的首字段进一步做成了可重复的 tag-family 地图：
  - 新证据：
    - `mps/ANE/.ane_runs/json/modelmanager_taskcancellable_tag_scan_verdict_20260622.json`
  - 当前 machine-local 事实：
    1. `_CodableBody`
       prefix offset `2`
       这一个位置
       已经可稳定分出：
       `nil`
       / `bool(true)`
       / `bool(false)`
       / string-like
       / `key(XPC.EncodingGraph.Key.super)`
       / `XPC object index`
       / `.containerMetadata`
       等 tag family
    2. 其中：
       - `0x00 -> nil`
       - `0x01 -> bool(true)`
       - `0x02 -> bool(false)`
       - `0x03 / 0x11 -> string-like`
       - `0x12 -> XPC object index`
       - `0x13 -> containerMetadata`
    3. 给 offset `2`
       注入一个真正有效的
       string
       （例如 `A`）
       后，
       reply 会从
       low-level buffer
       error
       推进成：
       `DecodingError.typeMismatch: expected UInt64, found string("A")`
    4. 这说明：
       - field1
         不是 opaque bytes
       - server
         已经真的把
         offset `2`
         decode
         成一个值
       - 当前真正缺的
         是这个位置上
         被接受的
         `UInt64`
         编码，
         而不是继续猜
         “string 后面是什么”
    5. 进一步地，
       一旦注入
       1 个有效 string，
       下一个 undecoded
       tag boundary
       会移到
       offset `13`
       ；注入
       2 个有效 string
       后，
       又会移到
       offset `24`
  - 因而当前 formal boundary
    再次收紧为：
    - manager / `_CodableBody`
      envelope
      都已经打通
    - 当前主 blocker
      变成：
      找出 offset `2`
      的真实
      `UInt64`
      编码
    - 之后才轮到
      offset `13/24`
      这些后续
      string-like / tag
      字段
- 2026-06-22 已把 `TaskCancellableMessage<ModelXPCRequest>` wrapper 的第一个真实字段进一步定位到 `_CodableBody` prefix offset `2`：
  - 新证据：
    - `mps/ANE/.ane_runs/json/modelmanager_taskcancellable_prefix_probe_verdict_20260622.json`
    - `mps/ANE/experiments/modelmanager_xpc_codable_probe.c`
  - 当前 machine-local 事实：
    1. 改外层
       `_CodableIsSync`
       的类型和值
       （`bool false/true`,
       `int64 0`,
       甚至省略）
       都不会移动
       `expected UInt64, found bool(false)`
       这条错误
    2. 因而那个
       `bool(false)`
       不在 XPC envelope
       层，
       而在
       `_CodableBody`
       内部
    3. 只把
       `_CodableBody`
       的 prefix
       offset `2`
       从
       `0x02`
       改成
       `0x03`
       ，错误就会稳定推进成：
       `EarlyDecodingError("Cannot read a valid string from buffer")`
    4. 即使不覆写后面的
       8 bytes，
       只改这一个 tag
       也足以得到同样的
       string-error
       ，说明这个 tag
       本身就是首个
       `UInt64`
       字段的决定性边界
  - 因而当前 formal boundary
    再次下压为：
    - wrapper
      的首个
      `UInt64`
      字段
      已被定位到
      offset `2`
    - 下一层 blocker
      已经不是
      `UInt64`
      本身，
      而是它后面的
      string-like
      字段族
- 2026-06-22 已把 `com.apple.modelmanager` 的合法 XPC 路径继续推进到真正的 Codable wire-format blocker：
  - 新证据：
    - `mps/ANE/.ane_runs/json/modelmanager_xpc_codable_probe_verdict_20260622.json`
    - `mps/ANE/experiments/modelmanager_xpc_codable_probe.c`
  - 当前 machine-local 事实：
    1. 通过
       `modelmanager_xpc_codable_probe`
       对
       `com.apple.modelmanager`
       发送空 XPC
       message
       ，reply body
       会明确报：
       `Expected value of type TaskCancellableMessage<ModelXPCRequest> but found null instead`
    2. 这说明当前 endpoint
       期待的根类型
       不是裸
       `ModelXPCRequest`
       ，而是外面还有一层
       `TaskCancellableMessage<ModelXPCRequest>`
    3. 给 `_CodableBody`
       填入 binary plist
       （空 dict / 空 array）
       后，
       reply 会稳定变成：
       `EarlyDecodingError("Cannot read a valid tag from buffer")`
       ，说明 body
       不是 plist
    4. 把 server
       之前回过的
       `_CodableBody`
       原样 replay
       回去后，
       reply 又会稳定推进成：
       `DecodingError.typeMismatch: expected UInt64, found bool(false)`
    5. 这证明：
       - `_CodableBody` / coder-version
         这层 envelope
         已经对了
       - server
         也确实接受
         当前 tag family
       - 新 blocker
         收敛到
         `TaskCancellableMessage`
         wrapper
         内部的首个
         `UInt64`
         字段
  - 因而当前 formal boundary
    再次下压为：
    - “如何 reach manager”
      已解决
    - “如何带上 `_CodableBody`”
      已解决
    - 当前只差
      `TaskCancellableMessage<ModelXPCRequest>`
      wrapper
      的最小字段恢复，
      然后才轮到
      `createSession`
      本体
- 2026-06-22 已把“恢复 selector-9 可运行宿主”进一步收紧成一条合法的 Apple-signed manager 链：
  - 新证据：
    - `mps/ANE/.ane_runs/json/modelmanager_inferenceprovidermanager_xpc_surface_verdict_20260622.json`
  - 当前 machine-local 事实：
    1. Apple-signed
       inferenceprovider appex
       宿主确实存在：
       `InferenceProviderService`
       / `TGOnDeviceInferenceProviderService`
       / `HostInferenceProviderService`
    2. 但它们不能从
       Python/bash
       直接拉起；
       kernel log
       明确给出
       `AMFI: Launch Constraint Violation`
       并指向
       Python parent
    3. `modelmanagerd`
       自身带有
       `com.apple.modelmanager.inferenceprovidermanager`
       与
       `com.apple.private.extensionkit.host.unsandboxed-extensions-for-extension-points = com.apple.modelmanager.inferenceprovider`
       ，说明 inferenceprovider appex 的合法拉起链就在它里面
    4. 当前用户仍不能
       `frida -p`
       附着
       `modelmanagerd`
    5. 但当前用户对
       `com.apple.modelmanager`
       发送空 XPC
       message
       能收到
       正常 reply；
       同时
       `com.apple.modelmanager.query`
       会直接
       `Connection invalid`
    6. `modelmanagerd`
       静态符号已暴露：
       `ModelManagerServices.ModelXPCRequest`
       以及
       `createSession(CreateSessionRequest)`
       / `fetchAssets`
       / `FetchModelInstance`
       / `CancelRequest`
       等 request family
    7. 其中
       `CreateSessionRequest`
       已静态收窄到：
       - `metadata: Session.Metadata`
       - `alreadyLockedInferenceProvider: InferenceProviderDescriptor?`
  - 因而当前 formal boundary
    再次下压为：
    - “恢复合法宿主链”
      已基本完成
    - 新 blocker
      不再是 AMFI
      对我们自签 probe
      的直接执行
    - 而是如何恢复
      `com.apple.modelmanager`
      的最小
      Swift-Codable request
      编码，
      先从
      `ModelXPCRequest.createSession`
      开始
- 2026-06-22 已把 selector-9 direct transport 的下一轮 patch 面补到 `qword0` / `u32_0x18`，但重启后的当前机器先在 AMFI restricted-entitlements 校验层卡死：
  - 新证据：
    - `mps/ANE/.ane_runs/json/selector9_direct_transport_codesign_blocker_verdict_20260622.json`
    - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
  - 当前 machine-local 事实：
    1. `ane_services_program_create_runtime_probe.m`
       已新增 selector-9 direct
       `qword0`
       / `u32_0x18`
       patch 面，
       且 snapshot
       已能记录
       `qword_0x00`
       / `qword_0x08`
    2. probe
       可成功编译，
       本机也确实存在
       `Apple Development`
       签名身份
    3. 但旧的
       `adhoc`
       entitled binary
       与新鲜
       `Apple Development`
       签名的
       `/tmp/ane_services_program_create_runtime_probe_test`
       在同一条
       `data_precompiled_path_hwx`
       baseline
       命令下
       都直接
       `Killed: 9`
       / shell
       返回
       `137`
    4. kernel log
       对两者都给出：
       `Code has restricted entitlements, but the validation of its code signature failed`
  - 因而当前 formal boundary
    暂时变成：
    - selector-9 direct transport
      的语义 patch 面
      已准备好
    - 但当前机器
      没有一个
      可被 AMFI 接受的
      restricted-entitlement
      probe host
    - 下一步必须先恢复
      runnable host
      或等价注入 seam，
      再继续
      second exact gate
      的 carrier/process-state
      probe
- 2026-06-22 已把 `program+0xa8` 的可写边界继续下压到 public selector-4 输入面：
  - 新证据：
    - `mps/ANE/.ane_runs/logs/program_wrapper_a8_frida_attach_baseline_20260622.jsonl`
    - `mps/ANE/.ane_runs/logs/program_wrapper_a8_frida_attach_a8_one_20260622.jsonl`
    - `mps/ANE/.ane_runs/json/program_wrapper_a8_selector4_handoff_boundary_verdict_20260622.json`
  - 当前 machine-local 事实：
    1. 重新验证
       `frida -f`
       spawn
       仍会退回
       `script_loaded + hook_install`
       的假阴性，
       所以当前 working harness
       是：
       直接启动
       `ane_services_program_create_runtime_probe`
       并使用
       `--pause-after-symbol-resolve-ms 5000 --symbol-dump-file ...`
       撑开窗口，
       再对活进程执行
       `frida -p <probe_pid> -l frida_selector9_raw_prepare_trace.js`
    2. baseline
       attach trace
       中，
       `raw_prepare_enter.u32_0x30`
       序列为：
       `0,0,0,0,0,0,0x7f,0x7f,0x7f,0x7f`
    3. `--patch-program-wrapper-a8 0x1`
       attach trace
       中，
       `raw_prepare_enter.u32_0x30`
       序列变为：
       `1,1,1,1,1,1,0x7f,0x7f,0x7f,0x7f`
    4. 同一条 patch
       还会把
       public
       `IOConnectCallStructMethod(selector=4)`
       输入里的
       `input_u32_0x30`
       从
       `0,0,0,0x7f,0x7f,0x7f,0x7f`
       推到
       `1,1,1,0x7f,0x7f,0x7f,0x7f`
    5. 但 baseline / patched
       两边的：
       - selector family
         都仍然全是
         `4`
       - `iokit_leave.ret`
         都仍然全是
         `0xe00002c2`
       - `chaining_prepare_leave.ret`
         都仍然是
         `0x14`
  - 因而当前 formal boundary
    进一步收紧为：
    - `program+0xa8`
      的 visible user-space patch
      不仅进入
      `raw_prepare`
      参数面，
      还继续进入 public
      selector-4
      输入面
    - 剩余 retained-control
      语义不再停留在
      visible wrapper / raw_prepare /
      public selector-4 input
      之前，
      而在
      selector-4
      之下的 lower consumer /
      deeper paired-state gate
- 2026-06-22 又已把 selector-4 `input+0x30` 的静态边界再压一层：
  - 新证据：
    - `mps/ANE/.ane_runs/json/selector4_input_0x30_lower_consumer_boundary_verdict_20260622.json`
  - 当前 machine-local 事实：
    1. external method
       `ANE_ProgramPrepare`
       在 size gate
       通过后，
       会把
       `structureInput[6]`
       原样复制到
       `structureOutput[6]`
       即 selector-4
       `input+0x30`
       会被 transport
       到 ProgramPrepareArgs
    2. `ANEClientDevice::programPrepare`
       只把这个
       ProgramPrepareArgs*
       原样 forward
       到更低 vtable call
    3. 但在
       `ANEDriver::ANE_ProgramPrepare_gated`
       与
       `ANEHWDevice::ANE_ProgramPrepare_gated`
       中，
       当前没有任何
       `args+0x30`
       的 direct read
    4. `ANEHWDevice::ANE_ProgramPrepare_gated`
       当前直接读取的是：
       `args+0x0`
       /
       `+0x8`
       /
       `+0x10`
       /
       `+0x18`
       /
       `+0x20`
       而不是
       `+0x30`
    5. 该函数里仅有的
       `+0x30`
       访问
       是：
       `[X20,#0x30]`
       与
       `[X22,#0x30]`
       且它们发生在
       `lookupProgramResource`
       之后，
       属于 looked-up lower objects /
       derived state，
       不是原始
       ProgramPrepareArgs
  - 因而当前 formal boundary
    再次收紧为：
    - selector-4
      `input+0x30`
      确实能 transport
      到 lower prepare path
    - 但它不是当前 visible
      H16 prepare gated path
      里的 direct consumer
    - 剩余 retained-control
      语义更像依赖：
      derived lower object state
      或
      `args+0x10/+0x18/+0x20/+0x8`
      这组真正被 direct read
      的 paired fields
- 2026-06-22 已完成 selector-4 direct-read 字段的第一轮候选排序，并做了最小 visible surrogate patch matrix：
  - 新证据：
    - `mps/ANE/.ane_runs/json/selector4_direct_read_field_patch_matrix_20260622.json`
    - `mps/ANE/.ane_runs/json/selector4_direct_read_field_candidate_ranking_verdict_20260622.json`
  - 代码面：
    `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
    已新增
    `--patch-prepare-byte8 VAL`
    /
    `--patch-prepare-qword10 VAL`
    /
    `--patch-prepare-qword10-live-intermediate`
    /
    `--patch-prepare-u32-20 VAL`
    四个 raw-prepare args patch 开关
  - 当前 machine-local 事实：
    1. baseline
       `data_precompiled_path_hwx`
       的
       `raw_prepare_owner0_ready1_buffer_initial`
       是：
       `u8_0x8 = 0`
       /
       `qword_0x10 = 0`
       /
       `u32_0x20 = 101568`
       /
       `u32_0x30 = 0`
    2. 从 H16 static path 看，
       当前 direct-read
       候选排序应为：
       `+0x10 > +0x8 > +0x20`
       而
       `+0x18`
       在这条 path
       更像 writeback slot，
       不再是 inbound candidate
    3. 当前 first surrogate matrix
       已实测：
       - `byte8_1`
       - `u32_20_1`
       - `byte8_1_u32_20_1`
       - `qword10_programHandle`
       - `byte8_1_qword10_programHandle`
       五格
    4. 这五格的 visible status vector
       全部保持：
       `prepare1_owner0_ready1 = 0x2`
       /
       `prepare1_owner0_ready1_wordargs = 0x2`
       /
       `chaining_prepare = 0x14`
       /
       `raw_prepare_owner0_ready1 = 0xe00002c2`
    5. 因为当前 machine
       的
       `live_runtime_graph.model_intermediateBufferHandle = 0`
       所以
       `+0x10`
       的本轮 patch
       只能先用
       `programHandle`
       作为 visible surrogate；
       这不足以判死
       `+0x10`
       family，
       只能说明
       “naive visible surrogate 不够”
  - 因而当前 formal boundary
    再次收紧为：
    - selector-4
      的更可信 retained-control
      候选
      仍是
      `+0x10/+0x8`
      这对
    - 但它需要的
      `+0x10`
      值
      很可能不是 visible
      `programHandle`
      这种替身，
      而是某个 hidden lower handle source
- 2026-06-22 当前 legacy `*_path_hwx` 四格已可判定“不提供可见的非零 `+0x10` source”，但 daemon-layout 变体已补出一个 trivial nonzero `qword_0x10=1`：
  - 新证据：
    - `mps/ANE/.ane_runs/json/selector4_prepare_case_handle_scan_20260622.json`
    - `mps/ANE/.ane_runs/json/selector4_qword10_source_gap_verdict_20260622.json`
    - `mps/ANE/.ane_runs/json/selector4_daemon_layout_qword10_probe_20260622.json`
  - 当前 machine-local 事实：
    1. `hwx_precompiled_path_hwx`
       /
       `data_precompiled_path_hwx`
       /
       `hwx_nonprecompiled_path_hwx`
       /
       `data_nonprecompiled_path_hwx`
       四格
       的
       `live_runtime_graph.model_intermediateBufferHandle`
       全部为
       `0`
    2. 这四格
       baseline
       的
       `prepare qword_0x10`
       也全部为
       `0`
    3. daemon-layout
       `data_precompiled_path_hwx_daemon_layout`
       在开启
       `--allow-daemon-layout-lower-probes`
       后，
       已能给出：
       `qword_0x10 = 1`
       但
       `raw_prepare_owner0_ready1_status_hex`
       仍然是
       `0xe00002c2`
       且
       `byte8_1`
       后仍不变
    4. 同时 H16 static path
       目前只能稳妥确认：
       - `+0x18`
         在
         `ANE_ProgramCreate`
         中由 newly-created
         `programHandle`
         author
       - `+0x10`
         的真实 earlier author
         仍未闭合；
         先前把
         `0xfffffe00093061bc`
         认作
         `additional_params+0x10`
         author
         的解释
         已撤回
    5. 当前 runtime probe
       的
       `raw_create_output`
       仍是
       `0xA5`
       填充，
       `diff_count = 0`
       不足以暴露这个 hidden source
  - 因而当前 formal boundary
    再次收紧为：
    - legacy 四格
      不提供可观测的
      nonzero `+0x10`
      source
    - daemon-layout
      虽已提供
      trivial nonzero
      `qword_0x10=1`
      但这仍不足以推动状态变化
    - 因而当前更强边界不是
      “没有非零 `+0x10`”，
      而是
      “当前拿到的非零 `+0x10`
      仍不具备 load-bearing 语义”
    - 下一步应恢复
      `ProgramCreate / InitialSetup`
      里的 semantically correct
      `+0x10`
      source，
      而不是继续 blind patch
      arbitrary nonzero
      `qword_0x10`
- 2026-06-22 又已判死一条更浅的观察面：wrapper `prepareFn(program, buffer, flag)` 的第二参数 buffer 不是 `+0x10` 的真实来源
  - 新证据：
    - `mps/ANE/.ane_runs/json/selector4_wrapper_prepare_buffer_inert_verdict_20260622.json`
  - 当前 machine-local 事实：
    1. legacy
       `data_precompiled_path_hwx`
       下，
       `prepare0_buffer_before/after`
       /
       `prepare1_buffer_before/after`
       /
       `prepare1_owner0_ready1_buffer_before/after`
       全部保持全零，
       `qword_0x10`
       没有任何 author
    2. 同一条 case
       的
       `raw_prepare_owner0_ready1_buffer_initial`
       却已经带有：
       `u8_0x9 = 1`
       /
       `u8_0xa = 1`
       /
       `u32_0x20 = 101568`
       /
       `qword_0x10 = 0`
       说明这些 lower-visible 字段来自本地 builder，
       不是 wrapper prepare 回填
    3. daemon-layout
       baseline
       的
       `qword_0x10 = 1`
       同样不是 wrapper author，
       而是因为
       `build_prepare_args_from_request_and_program()`
       直接拷贝
       `req+0x10`
       而 daemon request
       恰好把
       `is_precompiled`
       放在
       `0x10`
  - 因而当前 formal boundary
    再收紧一层：
    - wrapper `prepareFn`
      的 second-arg buffer
      是 inert surface
    - legacy / daemon
      里看到的
      `qword_0x10`
      差异
      主要是 request-layout-derived，
      不是 semantically correct
      hidden source
    - 下一步必须去
      wrapper prepare
      更早的
      `ProgramCreate / InitialSetup`
      或 carrier surface
      恢复真实 `+0x10`
- 2026-06-22 又已把 stable public `0xe00002c2` 的优先级下移到 kernel-side chaining prepare：
  - 新证据：
    - `mps/ANE/.ane_runs/json/selector4_e00002c2_lower_gate_boundary_verdict_20260622.json`
  - 当前 machine-local / static 事实：
    1. `ProgramInitialSetup`
       本身不定义
       `0xe00002c2`
       这条 public failure
       family
    2. H16 static evidence
       指向：
       `ANEHWDevice::ANE_ProgramChainingPrepare_gated`
       (`0xfffffe00093595b0`)
       内部存在大量
       `MOVZ #0x2c2`
       +
       `MOVK #0xe000`
       的错误返回构造
    3. 同时 dynamic evidence
       已经证明：
       多组 visible selector-4
       input patches
       都能进入 public selector-4
       输入面，
       但
       `iokit_leave.ret`
       仍稳定为
       `0xe00002c2`
  - 因而当前 formal boundary
    再次收紧为：
    - `0xe00002c2`
      不再优先建模成
      visible selector-4
      prepare-arg shaping
      问题
    - 当前最值得缩小的是
      kernel-side
      `ANE_ProgramChainingPrepare_gated`
      里最早几个
      `0xe00002c2`
      return branches
- 2026-06-22 已进一步确认：当前最早的 exact `0xe00002c2` gate 发生在 `+0x8/+0x10` 路径之前
  - 新证据：
    - `mps/ANE/.ane_runs/json/selector4_first_exact_0x2c2_gate_boundary_verdict_20260622.json`
  - 当前 machine-local / static 事实：
    1. `ANE_ProgramChainingPrepare_gated`
       入口附近的第一个错误分支
       `0xfffffe0009359644`
       虽然构造了
       `0x2c2`
       常量，
       但最终通过
       `orr`
       变成
       `0xe00002ee`
       不是当前 public stable
       `0xe00002c2`
    2. 当前最早的 exact
       `0xe00002c2`
       return
       在
       `0xfffffe000935968c`
       一带
    3. 这条 gate
       检查的是 large internal prepare buffer 上的：
       `+0x38`
       /
       `+0x3950`
       /
       `+0xa614`
       /
       `+0x3040`
    4. 而当前
       `qword10`
       / `lookupProgramResource`
       路径
       从
       `0xfffffe00093597ac`
       才开始，
       明显发生在这条 exact
       `0xe00002c2`
       gate 之后
  - 因而当前 formal boundary
    再次收紧为：
    - `+0x8/+0x10`
      相关 patch
      不是当前 hottest gate
    - 当前真正优先级更高的 family
      是 internal prepare buffer 的
      `0x38 / 0x3950 / 0xa614 / 0x3040`
      早期校验面
- 2026-06-22 已完成这组 early-validation family 的 user-space author-surface 排序：
  - 新证据：
    - `mps/ANE/.ane_runs/json/selector4_early_validation_author_surface_ranking_verdict_20260622.json`
  - 当前 machine-local 事实：
    1. 现有 write-surface probe
       已明确：
       - `0x38`
         = `fixed_write.event_count`
       - `0x3040`
         = `fixed_write.surface_group_a_count`
       - `0x3950`
         = `fixed_write.surface_group_b_count`
    2. 这些字段
       还各自已有 visible wrapper guard：
       - `request+0x30 <= 0x100`
       - `request+0x2038 <= 0xff`
       - `request+0x3828 < 0xd`
    3. 唯独
       `0xa614`
       当前没有 visible direct write：
       user-space wrapper
       的 loop-authored writes
       停在
       `local_args+0xa610`
       而 bootkc
       early validation
       仍会读取
       `prepare_args+0xa614`
  - 因而当前 formal boundary
    再次收紧为：
    - `0xa614`
      是当前这组 earliest exact
      `0xe00002c2`
      gate family
      中最不透明、最值得继续 probe 的字段
    - 相比之下
      `0x38 / 0x3040 / 0x3950`
      已经有更完整的 visible author/guard 解释
- 2026-06-22 `0xa614` 这条 gap 已从“静态未知”推进到“静态闭合 + 可直接模拟”：
  - 新证据：
    - `mps/ANE/.ane_runs/json/selector9_a614_author_surface_and_sim_patch_verdict_20260622.json`
    - `mps/ANE/experiments/frida_selector9_patch_a614.js`
  - 当前 machine-local 事实：
    1. 现有 write-surface probe
       已确认
       visible user-space
       writes
       停在
       `local_args+0xa610`
       而 lower early-validation
       读取
       `prepare_args+0xa614`
    2. 因此
       `0xa614`
       在当前 visible path
       上可视为
       “无 visible writer”
       这件事已经闭合
    3. 现在仓库里已经有一把可直接模拟它的刀：
       `frida_selector9_patch_a614.js`
       会在
       `IOConnectCallStructMethod(selector=9)`
       进入时，
       解引用 descriptor
       并原位 patch
       payload `+0xa614`
  - 因而当前 formal boundary
    再收紧为：
    - `0xa614`
      的可见 author-surface
      问题
      已不再是“未知”
    - 下一步变成：
      找到一条当前机器上
      真正会发出
      selector-9
      的 runtime path，
      然后用这把 direct patch surface
      去验证 lower gate
- 2026-06-22 当前机器已经具备 real selector-9 runtime path，并且 direct transport 已把调查面推进到第二层 exact gate：
  - 新证据：
    - `mps/ANE/.ane_runs/json/selector9_direct_transport_boundary_verdict_20260622.json`
    - `mps/ANE/.ane_runs/json/selector9_direct_transport_a614_probe_20260622.json`
    - `mps/ANE/.ane_runs/json/selector9_direct_transport_gate_probe_20260622.json`
    - `mps/ANE/.ane_runs/json/selector9_direct_transport_qword10_programHandle_20260622.json`
  - 代码面：
    `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
    已新增
    `--manual-selector9-transport`
    与 direct patch 选项，
    可直接对当前 ANEServices 连接发
    `IOConnectCallStructMethod(selector=9, {args_ptr, size=0xae30}, output=24)`
  - 当前 machine-local 事实：
    1. direct selector-9
       baseline
       已能稳定返回
       `0xe00002c2`
    2. baseline
       direct input
       中：
       `0x38 / 0x3040 / 0x3950 / 0xa614`
       全为
       `0`
       也仍然返回
       `0xe00002c2`
       这说明 earliest exact gate
       的上界条件
       至少可以被当前 direct baseline
       满足
    3. `a614 = 1`
       仍然返回
       `0xe00002c2`
    4. `qword10 = current programHandle`
       仍然返回
       `0xe00002c2`
  - 因而当前 formal boundary
    再次收紧为：
    - “如何打到 selector-9”
      这个问题已经解决
    - `0xa614`
      单点 patch
      也不足以改变返回码
    - 当前更像卡在
      second exact
      `0xe00002c2`
      gate
      所需的
      carrier/process state
- 2026-06-22 又已把 `ANE_ProgramChainingPrepare_gated` 里的 exact `0xe00002c2` return 排成两层 gate ladder：
  - 新证据：
    - `mps/ANE/.ane_runs/json/selector4_exact_0x2c2_branch_ladder_verdict_20260622.json`
  - 当前 machine-local / static 事实：
    1. 第一个 exact
       `0xe00002c2`
       return
       在
       `0xfffffe000935968c`
       一带，
       仍属于
       early-validation family：
       `0x38 / 0x3950 / 0xa614 / 0x3040`
    2. 第二个 exact
       `0xe00002c2`
       return
       在
       `0xfffffe0009359868`
       一带，
       属于更晚的
       `qword10 -> lookupProgramResource / process`
       null gate
    3. 其间还存在
       `0xe00002ee`
       /
       `0xe00002c5`
       /
       `0xe00002f0`
       等近邻错误族，
       说明不能把
       “看见 `0x2c2` 常量”
       和
       “exact public `0xe00002c2` return”
       混为一谈
  - 因而当前 formal boundary
    再收紧为：
    - 当前应先跨过
      第一层 exact
      `0xe00002c2`
      gate
      (`0x38 / 0x3950 / 0xa614 / 0x3040`)
    - 在此之前，
      `qword10`
      / `lookupProgramResource`
      分支
      仍然是第二层，
      不宜继续作为主调查面
- 2026-06-21 已确认 visible ANEServices runtime probe 仍可直接 author `program+0xa0/+0xa8`，但当前可见 status surface 仍不响应：
  - 代码面：
    `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
    已新增
    `--patch-program-wrapper-a0 VAL`
    与
    `--patch-program-wrapper-a8 VAL`
    两个最小 CLI 开关，
    在 `ProgramCreate`
    成功后、
    `prepare/chaining/raw_prepare`
    前直接 patch wrapper 字段并落盘 patch 前后快照
  - 新证据：
    - `mps/ANE/.ane_runs/json/program_wrapper_authorability_baseline_v2_20260621.json`
    - `mps/ANE/.ane_runs/json/program_wrapper_authorability_a0_zero_v2_20260621.json`
    - `mps/ANE/.ane_runs/json/program_wrapper_authorability_a8_one_v2_20260621.json`
    - `mps/ANE/.ane_runs/json/program_wrapper_authorability_both_v2_20260621.json`
    - `mps/ANE/.ane_runs/json/program_wrapper_authorability_status_boundary_verdict_20260621.json`
  - 当前 machine-local 事实：
    1. baseline
       下
       `raw_prepare_owner0_ready1_buffer_initial.u32_0x30 = 0`
    2. `--patch-program-wrapper-a0 0x0`
       会把
       `wrapper_qword_0xa0`
       从
       `0x0000000100000015`
       改成
       `0x0000000000000000`
    3. `--patch-program-wrapper-a8 0x1`
       会把
       `wrapper_qword_0xa8`
       从
       `0x0000000100000000`
       改成
       `0x0000000000000001`
       且同步把
       `raw_prepare_owner0_ready1_buffer_initial.u32_0x30`
       从
       `0`
       推到
       `1`
    4. 但上述四格
       `baseline/a0_zero/a8_one/both`
       的
       `prepare0_status_hex`
       /
       `prepare1_status_hex`
       /
       `prepare1_wordargs_status_hex`
       /
       `chaining_prepare_status_hex`
       /
       `raw_prepare_owner0_ready1_status_hex`
       全部保持：
       `0x00000003 / 0x00000014 / 0x00000014 / 0x00000014 / 0xe00002c2`
  - 与 IDA 当前语义提示一致：
    - `+0xa8`
      在 H16 helper 中明确以
      32-bit
      compare/control
      方式消费
    - `+0xa0`
      更像
      64-bit handle/pointer-like
      载荷
  - 因而当前边界进一步收紧为：
    - visible ANEServices wrapper / raw_prepare status surface
      不是“完全不可写”
    - 它是
      “可写、且 `+0xa8`
      能进入 visible raw_prepare arg surface，
      但仍不足以改变当前可见返回码”
    - 剩余 retained-control 语义继续下压到
      raw_prepare / lower handoff
      之下的 control layer
- private ANE 路径已经可以完成多 chunk 推理，不是“完全没跑通”。
- 当前主要问题是速度与控制层，而不是基础功能是否可用。
- 当前系统稳定性问题按系统级内存压力处理，不能只看 Python 进程 RSS。
- 2026-06-20 新的 bridge-layer free trace 证据，已把 lower-side unload/free 观测主线从 `mach_msg` 正式切回 bridge 层：
  - 代码路径：
    `mps/maderix_ANE/bridge/ane_bridge.m`
    中的
    `ane_bridge_free`
    现已支持
    `ANE_BRIDGE_FREE_TRACE=1`
    与
    `ANE_BRIDGE_FREE_TRACE_FILE=<path>`
    两个环境变量，
    在 unload 前后各写一条 JSONL event
  - dedicated micro-harness：
    `benchmark/private_ane_free_unload_micro_probe.py`
    已在
    `compile_only`
    模式下验证此 trace
  - 对应证据：
    - `mps/ANE/.ane_runs/json/free_unload_bridge_probe_runtime_20260620.json`
    - `mps/ANE/.ane_runs/logs/ane_bridge_free_trace_20260620.jsonl`
    - `mps/ANE/.ane_runs/json/free_unload_bridge_observability_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. micro-harness
       稳定完成 compile，
       并到达
       `bridge.free(handle)`
    2. trace 明确记录
       `before_unload`
       与
       `after_unload`
       两条事件，
       且
       `after_unload.unload_ok = 1`
    3. 当前单 handle compile-only case
       的
       `after_unload.elapsed_sec ~= 0.0063`
       且
       `free_sec ~= 0.0076`
    4. trace 在 unload 边界直接捕获到：
       - `model_state = 3`
       - `program_handle != 0`
       - `queue_depth = 127`
       - `model_class = _ANEInMemoryModel`
  - 因而当前结论进一步收紧为：
    - 对 unload/free 这条 lower-side 问题，
      `mach_msg probe v2`
      已不是默认主线
    - bridge 层最小 instrumentation
      已经成为当前最直接、最可复用的 observability 面
- 2026-06-20 family-labeled free instrumentation 已经接通到代码路径，但 real multi-handle benchmark 仍未成功落盘：
  - 代码改动面：
    - `mps/maderix_ANE/bridge/ane_bridge.h`
    - `mps/maderix_ANE/bridge/ane_bridge.m`
    - `benchmark/private_ane_real_attention_probe.py`
    - `pymss/modules/bs_roformer/private_ane.py`
    - `pymss/utils.py`
  - 当前 machine-local 事实：
    1. `ANEBridge.free(handle, label=...)`
       已能把 Python family label
       传入 bridge free trace
    2. `private_ane` runner
       已新增
       `free_profile_by_family`
       聚合，
       覆盖：
       - `transformer_time`
       - `transformer_freq`
       - `band_split(_fused)`
       - `final_norm_*`
       - `mask(_fused)`
       - `stft_cache`
       - `irfft_cache`
       - `aux_*_cache`
       - `transformer_cache`
    3. 但当前两条 real-path 验证都还没让这套工件真正落盘：
       - subprocess child route：
         `benchmark_results/private_ane/test_clean_free_profile_20260620.private_ane_child/parent_watchdog_failure.json`
         记录
         `native supervisor killed child: compressor_memory`
       - in-process route：
         进入真实 private-ANE path，
         但在
         `band_split_l2_0`
         /
         `band_split_l2_fused_0_4`
         compile 上遭遇
         `InvalidMILProgram`
    4. 当前对应 verdict：
       `mps/ANE/.ane_runs/json/free_profile_family_wiring_verdict_20260620.json`
       为
       `inconclusive`
  - 因而当前状态收紧成：
    - instrumentation 链路已具备
    - 但“哪个最小 real path 能稳定跑到这些 free 点”
      仍是当前唯一未解前置条件
- 2026-06-20 direct multi-family probe 已把这个前置条件正式解开：
  - 新增脚本：
    `benchmark/private_ane_multifamily_free_profile_probe.py`
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_free_profile_probe_20260620.json`
    - `mps/ANE/.ane_runs/logs/ane_bridge_free_trace_multifamily_20260620.jsonl`
    - `mps/ANE/.ane_runs/json/multifamily_free_profile_probe_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. 这条路径绕过了当前会报
       `InvalidMILProgram`
       的 ANE band-split，
       改成：
       torch band-split
       +
       ANE STFT / transformer / final_norm / mask / IRFFT
    2. 在
       `private_ane_max_transformer_layers=1`
       条件下，
       1s `test_clean`
       真实多 family probe
       成功跑完，
       wall time
       `~13.69s`
    3. `free_profile_by_family`
       已真实落盘：
       - `transformer_time`: 3 handles
       - `transformer_freq`: 3 handles
       - `aux_final_norm_cache`: 1 handle
       - `aux_mask_cache`: 10 handles
       - `irfft_cache`: 16 handles
       - `stft_cache`: 1 handle
    4. bridge free trace
       JSONL 也已按 family label 落盘，
       当前事件分布：
       - `transformer_time`: 6
       - `transformer_freq`: 6
       - `aux_final_norm_cache`: 2
       - `aux_mask_cache`: 20
       - `irfft_cache`: 32
       - `stft_cache`: 2
  - 因而当前结论收紧成：
    - family-labeled free instrumentation
      已在 real multi-family path
      上被正式验证
    - 下一步不再需要证明“它是否可用”，
      而应直接拿它去解释
      full private-ANE path
      的 dominant repeated unload
- 2026-06-20 用 direct probe 对照 full private-ANE path 后，当前“dominant repeated free/unload”结论已分成两层：
  - 对应证据：
    - `mps/ANE/.ane_runs/json/full_path_free_dominance_verdict_20260620.json`
    - `benchmark_results/private_ane/test_clean_full_private_default_auto_batch4_after_batch_axis_code_profile.json`
    - `benchmark_results/private_ane/mask_batch_detail_smoke_1s.json`
  - 当前 machine-local 事实：
    1. 如果只看 visible `cache_release` 事件，
       full path 当前主角是：
       - `stft_cache_release`
         17 handles，`~0.0466s`
       - `irfft_cache_release`
         16 handles，`~0.0544s`
       而 aux families 在
       `persistent_aux_handles=True`
       下被保留
    2. 但如果看 full path
       `transformer_timings[*].handle_free_sec`
       的总和，
       transformer family
       的 runtime free 时间是：
       - time axis:
         `~0.418s`
       - freq axis:
         `~0.151s`
       - total:
         `~0.569s`
       明显高于 visible
       `stft + irfft`
       cache release
       的合计 `~0.10s`
  - 因而当前最准确的表述是：
    - visible cache-release 主角
      是
      `irfft/stft`
    - 但 total repeated free-time 主角
      是
      transformer family
    - 对 single-process reuse
      更关键的是后者，
      因为它直接对应 full path 中运行期反复 tear-down 的时间成本
- 2026-06-20 transformer keep-alive 对照已在窄路径上跑通：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_free_profile_repeat_free_20260620.json`
    - `benchmark_results/private_ane/multifamily_free_profile_repeat_keep_20260620.json`
    - `mps/ANE/.ane_runs/logs/ane_bridge_free_trace_repeat_free_20260620.jsonl`
    - `mps/ANE/.ane_runs/logs/ane_bridge_free_trace_repeat_keep_20260620.jsonl`
    - `mps/ANE/.ane_runs/json/transformer_keepalive_probe_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. baseline 组
       （`keep_transformer=false`, `repeats=2`）
       两次都成功，
       并且：
       - `transformer_time`
         / `transformer_freq`
         仍然进入
         `free_profile_by_family`
       - `final_cache_handles.transformer_handles = 0`
    2. keep-transformer 组
       （`keep_transformer=true`, `repeats=2`）
       两次也都成功，
       并且：
       - `transformer_time`
         / `transformer_freq`
         已从
         `free_profile_by_family`
         消失
       - `final_cache_handles.transformer_entries = 2`
         / `transformer_handles = 6`
         在两次 run 后仍存在
       - bridge trace 中
         也已完全没有
         `transformer_*`
         label
    3. 第二次 keepalive run
       比 baseline 第二次 run 更快：
       `~10.997s` vs `~12.212s`
  - 因而当前结论再次收紧成：
    - transformer keep-alive
      在窄路径上不只是“理论可行”，
      而是已被 runtime 对照正式证明：
      可以去掉 repeated transformer free，
      且第二次运行仍成功
    - 但这条结论当前只对
      窄路径
      （torch band-split + 1-layer transformer + ANE stft/final_norm/mask/irfft）
      成立，
      还不能直接外推到 full private-ANE path
- 2026-06-20 当前窄路径 keepalive 的首个失效边界已定位到 4 transformer layers：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers_1_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers_2_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers_4_20260620.json`
    - `mps/ANE/.ane_runs/json/transformer_keepalive_layer_boundary_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. `keep_transformer=true`
       时，
       1 layer
       与
       2 layers
       都能在同进程内成功跑两次，
       且 transformer handles
       持续保留：
       - 1 layer:
         6 handles
       - 2 layers:
         12 handles
    2. 到 4 layers
       时，
       第一次 run
       仍成功，
       并保留：
       - `transformer_entries = 8`
       - `transformer_handles = 24`
    3. 但第二次 run
       在同进程内失败，
       当前错误是：
       `RuntimeError('ANE eval failed')`
  - 因而当前状态继续收紧成：
    - transformer keepalive
      不是“一开就炸”，
      而是存在一个当前已观测到的
      first failure boundary:
      `4 transformer layers`
    - 下一步不应再问
      “keepalive 是否可行”，
      而应直接解释
      这个 4-layer failure
      是由 retained transformer state
      自身触发，
      还是由其他 family 的阶段交互触发
- 2026-06-20 `4-layer keepalive` 的 failure 已确认不依赖后续 aux/irfft 阶段：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers_4_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_stop_after_transformer_20260620.json`
    - `mps/ANE/.ane_runs/json/transformer_keepalive_stage_isolation_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. full narrow path 下，
       `4-layer keepalive`
       第二次运行失败：
       `RuntimeError('ANE eval failed')`
    2. 把路径收窄到
       `stop_after_transformer`
       之后，
       第二次运行仍然失败，
       错误完全相同
    3. 此时后续
       `final_norm`
       / `mask`
       / `irfft`
       已不再参与运行路径，
       但
       `transformer_handles = 24`
       仍然保留
  - 因而当前结论进一步收紧成：
    - `4-layer keepalive`
      的 second-run failure
      不需要借助后续
      aux/irfft
      阶段就能复现
    - 第一失效面
      已经落在
      retained transformer eval
      本身
      或其紧邻前置
      stft/map setup
      边界
- 2026-06-20 `4-layer` second-run failure 已进一步确认为 retained transformer reuse 根因：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_stop_after_transformer_20260620.json`
    - `benchmark_results/private_ane/multifamily_nokeep_layers4_stop_after_transformer_20260620.json`
    - `mps/ANE/.ane_runs/json/transformer_reuse_root_cause_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. `keep_transformer=true`
       时，
       `4-layer + stop_after_transformer`
       第二次运行失败，
       且
       `transformer_handles = 24`
       仍保留
    2. 用完全相同路径，
       但关闭 transformer keepalive
       后，
       第二次运行恢复成功，
       且
       `transformer_handles = 0`
  - 因而当前结论再收紧一层：
    - `4-layer` second-run failure
      不是“只要走到这个路径就会炸”，
      而是
      retained transformer handle reuse
      本身
      才会触发的 failure
    - 下一步不应再把怀疑面放在
      stft
      或
      后续 stages
      上，
      而要直接定位
      retained transformer cached stack
      内的 first failing surface
- 2026-06-20 当前 retained-transformer first failing surface 已缩到 `layer2 freq` 之后：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_stop_freq1_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_stop_freq2_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers_4_20260620.json`
    - `mps/ANE/.ane_runs/json/transformer_reuse_surface_narrowing_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. `keep_transformer=true`
       时，
       到
       `layer1 freq`
       仍稳定
    2. 到
       `layer2 freq`
       也仍稳定
    3. 但完整
       `4-layer`
       keepalive
       第二次运行已失败
  - 因而当前状态继续收紧成：
    - retained-transformer
      first failing surface
      不在
      `layer1`
      或
      `layer2 freq`
      之前
    - 下一步只需继续打
      `layer3 time`
      /
      `layer3 freq`
      两个边界，
      就能把 first failing segment
      进一步钉住
- 2026-06-20 first failing segment 已进一步收窄到 `layer3 time`：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_stop_freq2_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_stop_time3_20260620.json`
    - `mps/ANE/.ane_runs/json/transformer_reuse_first_failing_segment_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. keepalive 到
       `layer2 freq`
       仍然稳定，
       并保留：
       `transformer_handles = 12`
    2. 但只要推进到
       `layer3 time`
       之后，
       第二次运行就已经失败，
       并保留：
       `transformer_handles = 15`
  - 因而当前状态再次收紧成：
    - retained-transformer
      first failing segment
      已不晚于
      `layer3 time`
    - 下一步不再需要重扫
      `layer1/2`
      或完整
      `layer4`
      ，
      只需解决
      `layer3 time`
      自身
      vs
      其后续
      `layer3 freq`
      的最后一个二分
- 2026-06-20 `layer3 time` retained transformer stack 已正式被确认为 first failing surface：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_stop_time3_20260620.json`
    - `benchmark_results/private_ane/multifamily_nokeep_layers4_stop_time3_20260620.json`
    - `mps/ANE/.ane_runs/json/transformer_reuse_time3_root_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. `layer3 time`
       路径在
       `keep_transformer=true`
       时，
       第二次运行失败，
       且保留：
       `transformer_handles = 15`
    2. 完全相同路径在
       `keep_transformer=false`
       时，
       第二次运行恢复成功，
       且：
       `transformer_handles = 0`
  - 因而当前结论再次收紧成：
    - first failing surface
      已正式落在
      retained
      `layer3 time`
      transformer stack
      本身
    - 下一步不再需要继续做
      边界二分，
      而应直接在这个 stack
      里定位
      `pre / gate / ffn`
      三个 cached handle
      中谁先失效
- 2026-06-20 retained `layer3 time` stack 已被证实是充要失败面：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_stop_time3_20260620.json`
    - `benchmark_results/private_ane/multifamily_nokeep_layers4_stop_time3_20260620.json`
    - `mps/ANE/.ane_runs/json/transformer_reuse_handle_scope_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. retained
       `layer3 time`
       路径在
       `keep_transformer=true`
       时，
       第二次运行失败
    2. 同一路径在
       `keep_transformer=false`
       时，
       第二次运行恢复成功
  - 因而当前状态最终收敛为：
    - retained
      `layer3 time`
      transformer stack
      本身
      已经足以触发 first confirmed second-run failure
    - 下一步不再需要继续做
      时间/层数
      二分，
      而应直接转向
      `pre / gate / ffn`
      handle 级 mechanism-finding
- 2026-06-20 retained `pre` handle 的机制定位目前改判为 `inconclusive`：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_state_20260620.json`
    - `mps/ANE/.ane_runs/json/pre_handle_state_probe_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. 无 introspection 的
       `pre-only keepalive`
       第二次运行失败
    2. 但加入 live handle state
       读取后，
       相同
       `pre-only keepalive`
       路径
       第二次运行恢复成功
    3. 且当前读到的
       `model_state/programHandle/intermediateBufferHandle/queueDepth`
       在代表性 cached handle 上
       前后保持稳定
  - 因而当前结论改成：
    - 不能再把
      `pre`
      单独当作已确认根因
    - 当前 failure
      至少对
      introspection / timing
      敏感，
      下一步应以最小 timing/control 对照继续定位
- 2026-06-20 retained `pre+gate` 在 live handle snapshot 下同样恢复成功：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pregate_state_20260620.json`
    - `mps/ANE/.ane_runs/logs/ane_bridge_free_trace_time3_pregate_state_20260620.jsonl`
    - `mps/ANE/.ane_runs/json/pre_gate_handle_state_probe_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. 无 snapshot 的
       `pre-only keepalive`
       第二次运行失败
    2. 加入 live handle state
       读取后，
       `pre-only keepalive`
       第二次运行恢复成功
    3. 同样加入 live handle state
       读取后，
       `pre+gate keepalive`
       第二次运行也恢复成功
    4. run1 前后的 retained
       `layer3 time`
       handles
       仍保持稳定可读的：
       `model_state=3`
       / `queue_depth=127`
  - 因而当前状态再次收紧为：
    - 不能把
      `pre+gate`
      视作第一个稳定坏掉的
      cached subset
    - 当前最高价值的 mechanism-finding
      问题已从
      “subset 边界”
      转为：
      “live introspection
      本身或其引入的 timing slack
      为什么会把 run2 failure 消掉”
    - 下一步应减少观测扰动，
      用更小的 timing/control probe
      复现这种翻转
- 2026-06-20 轻量 timing/control 变量仍不足以替代 full snapshot：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_sleep250_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_representative_before_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_representative_both_20260620.json`
    - `mps/ANE/.ane_runs/json/pre_snapshot_load_bearing_matrix_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. `pre-only + full snapshot`
       第二次运行成功
    2. `pre-only + sleep 250ms`
       第二次运行仍失败
    3. `pre-only + representative handle before`
       第二次运行仍失败
    4. `pre-only + representative handle before+after`
       第二次运行仍失败
  - 因而当前状态再次收紧为：
    - 当前成功翻转
      不能归因于
      `纯延时`
      或
      `单个 representative handle`
      级别的轻量 bridge read
    - 当前 load-bearing
      effect
      仍然依赖
      full cache snapshot
      这类更重的 describe-handle 面
    - 下一步应从
      snapshot 的
      cardinality / placement
      本身继续下刀，
      而不是继续做更泛的 timing 猜测
- 2026-06-20 snapshot 的 placement / 全局 first-handle 子集仍不足以复现 green path：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_before_limit1_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_after_limit1_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_both_limit1_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_before_full_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_after_full_20260620.json`
    - `mps/ANE/.ane_runs/json/pre_snapshot_phase_cardinality_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. `both-side full snapshot`
       是当前唯一已知 green path
    2. `before-only full`
       和
       `before-limit1`
       都会在
       `run0`
       直接失败
    3. `after-only full`
       和
       `after-limit1`
       能保住
       `run0`
       ，但仍会在
       `run1`
       失败
    4. `both-limit1`
       也会在
       `run0`
       直接失败
  - 因而当前状态再次收紧为：
    - 当前 load-bearing
      effect
      不属于
      单侧 placement
      或
      全局 first-handle
      子集
    - 下一步应继续拆
      `both-side full snapshot`
      的结构化子集，
      例如每个 entry 的第一个 handle，
      或 axis / layer 限制，
      而不是继续做过粗的全局 limit
- 2026-06-20 `both-side full snapshot` 仍不能压成单 axis 或每 entry 第一个 handle：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_both_firsthandle_per_entry_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_both_time_only_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_both_freq_only_20260620.json`
    - `mps/ANE/.ane_runs/json/pre_snapshot_structured_subset_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. `both-side first-handle-per-entry`
       会在
       `run0`
       直接失败
    2. `both-side freq-only`
       也会在
       `run0`
       直接失败
    3. `both-side time-only`
       能保住
       `run0`
       ，但仍会在
       `run1`
       失败
  - 因而当前状态再次收紧为：
    - 当前 green path
      不属于
      单 axis
      或
      单一 handle-pattern
      级别的结构化子集
    - 下一步应继续测
      浅层 cross-axis
      组合，
      例如
      `time-all + freq-layer0`
      或
      `freq-all + time-layer0`
- 2026-06-20 浅层 layer/cross-axis 组合仍不足以保住 run0：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_both_layer0_only_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_both_layer01_only_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_timeall_freqlayer0_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_freqall_timelayer0_20260620.json`
    - `mps/ANE/.ane_runs/json/pre_snapshot_shallow_cross_axis_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. `layer0 only`
       会在
       `run0`
       直接失败
    2. `layer0-1 only`
       会在
       `run0`
       直接失败
    3. `time-all + freq-layer0`
       会在
       `run0`
       直接失败
    4. `freq-all + time-layer0`
       会在
       `run0`
       直接失败
  - 因而当前状态再次收紧为：
    - 当前 green path
      仍然不属于任何已测试的
      浅层 layer
      / cross-axis
      组合
    - 下一步应继续增加层深，
      找第一个不再破坏
      `run0`
      的 deeper subset，
      然后再看它是否能救回
      `run1`
- 2026-06-20 更深组合首次保住了 run0，但仍救不回 run1：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_both_layer02_only_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_timeall_freqlayer01_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_snapshot_freqall_timelayer01_20260620.json`
    - `mps/ANE/.ane_runs/json/pre_snapshot_deeper_non_destructive_boundary_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. `layer0-2 only`
       已能保住
       `run0`
       ，但仍会在
       `run1`
       失败
    2. `time-all + freq-layer0-1`
       已能保住
       `run0`
       ，但仍会在
       `run1`
       失败
    3. `freq-all + time-layer0-1`
       已能保住
       `run0`
       ，但仍会在
       `run1`
       失败
  - 因而当前状态再次收紧为：
    - 这 3 个更深组合
      已构成当前第一个
      non-destructive boundary
    - 下一步应从这个边界继续加覆盖，
      例如
      `layer0-3 only`
      / `time-all + freq-layer0-2`
      / `freq-all + time-layer0-2`
- 2026-06-20 当前 probe 代码下 full snapshot baseline 已稳定漂移成红：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_state_recheck_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_state_recheck2_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_nosnapshot_recheck_20260620.json`
    - `mps/ANE/.ane_runs/json/pre_snapshot_baseline_drift_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. 历史上的
       `both-side full snapshot`
       曾经是双绿
    2. 但当前 probe 代码下，
       `full snapshot`
       两次复验都在
       `run1`
       稳定失败
    3. 且它现在与
       `no snapshot`
       red baseline
       的 run1 失败行为已基本同态
  - 因而当前状态切换为：
    - 在恢复可区分的
      green / red
      基线前，
      后续 subset 结果不能再直接解释成对旧 green path 的稳定收敛
    - 下一步应优先判定
      这是
      probe 默认语义漂移
      还是
      运行时/环境漂移
- 2026-06-20 baseline 漂移来源当前更像 runtime drift，但仍未彻底排除脚本语义漂移：
  - 对应证据：
    - `mps/ANE/.ane_runs/json/pre_snapshot_drift_source_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. 当前 probe 的默认参数
       仍然是 neutral：
       `snapshot_phase=both`
       / `snapshot_limit=0`
       / `snapshot_axis=all`
       / 各种 filter 关闭
    2. 当前 full-snapshot recheck
       的
       `cache_before/cache_after`
       长度
       与历史 green case
       保持同态：
       `0/15`
       与
       `15/15`
    3. 但 probe 文件当前
       是 untracked，
       不存在 authoritative git baseline
  - 因而当前状态收敛为：
    - 现有证据
      **倾向**
      runtime / environment
      drift
    - 但在拿到更强分离证据前，
      仍不能把
      probe 语义漂移
      完全排除
- 2026-06-20 `current` 与 `historical_simple` 都变红，runtime drift 解释进一步变强：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_state_current_impl_recheck_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_state_historicalsimple_recheck_20260620.json`
    - `mps/ANE/.ane_runs/json/pre_snapshot_code_vs_runtime_split_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. `current`
       snapshot helper
       在
       `run1`
       失败
    2. 独立重构的
       `historical_simple`
       snapshot helper
       也在
       `run1`
       失败
    3. 且两者都保持
       与历史 green case
       同样的
       `0/15`、
       `15/15`
       snapshot 形态
  - 因而当前状态再次收紧为：
    - 当前 helper 语义本身
      不是最有力解释
    - runtime / environment
      drift
      已成为主导假设
- 2026-06-20 strict serial fresh-process A/B 已恢复 green，说明当前仍是同进程 authored runtime state：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_state_processA_single_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_state_processB_single_20260620.json`
    - `mps/ANE/.ane_runs/json/pre_snapshot_fresh_process_reset_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. `historical_simple`
       路径在
       进程 A
       单次运行成功
    2. A 退出后，
       独立进程 B
       单次运行也成功
    3. 但同一脚本里的
       `repeats=2`
       路径仍在
       `run1`
       失败
  - 因而当前状态再次收紧为：
    - 当前 red baseline
      仍属于
      同进程 authored
      runtime state
    - process-fresh green
      vs in-process red
      已重新成为有判别力的基线
    - 下一步应在
      **单进程内**
      寻找最小 reset / rebuild
      动作
- 2026-06-20 `clear_transformer_cache` 已成为当前最小有效用户态 reset 边界：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_reset_clear_transformer_recheck_20260620.json`
    - `mps/ANE/.ane_runs/json/pre_min_user_reset_clear_transformer_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. 无 reset 的
       in-process baseline
       仍然是
       `run1`
       变红
    2. 但在
       `run0`
       之后只执行
       `clear_transformer_cache`
       ，
       `run1`
       已恢复成功
  - 因而当前状态再次收紧为：
    - 最小已知有效 reset
      已落在
      transformer-cache
      清理边界
    - authored runtime state
      已被进一步局限到
      transformer retention
      一侧
    - 但当前还没有证明
      比完整
      `clear_transformer_cache`
      更小的动作
      是否足够
- 2026-06-20 更小 reset 成分已收紧到“必须真正 free transformer handles”：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_reset_drop_transformer_refs_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_reset_free_transformer_nogc_20260620.json`
    - `mps/ANE/.ane_runs/json/pre_min_reset_component_split_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. 仅做
       `drop_transformer_refs`
       时，
       `run0`
       直接失败
    2. 仅做
       `free_transformer_no_gc`
       时，
       `run1`
       已恢复成功
    3. 其效果与
       `clear_transformer_cache`
       等价
  - 因而当前状态再次收紧为：
    - 当前最小有效 reset
      依赖于
      **真正 free live transformer handles**
    - Python 引用层
      不是 load-bearing reset
    - `gc`
      也不是当前恢复 green
      的必需成分
- 2026-06-20 bridge 重建不是当前最小有效 reset 的必要成分：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_reset_free_transformer_new_bridge_20260620.json`
    - `mps/ANE/.ane_runs/json/pre_reset_bridge_rebuild_nonessential_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. `free_transformer_no_gc`
       已能双绿
    2. 但在 free handles 后
       额外重建
       `ANEBridge`
       ，
       反而会在
       `run0`
       前触发
       RSS guard
  - 因而当前状态再次收紧为：
    - bridge / controller
      重建
      不是当前最小有效恢复动作
    - 当前最小有效恢复动作
      仍然就是
      **free live transformer handles**
- 2026-06-20 当前 runtime 下已测 retained subset 无一存活：
  - 对应证据：
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_retained_pre_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_retained_pregate_20260620.json`
    - `benchmark_results/private_ane/multifamily_keep_layers4_time3_pre_retained_full_20260620.json`
    - `mps/ANE/.ane_runs/json/pre_retained_subset_no_survivor_verdict_20260620.json`
  - 当前 machine-local 事实：
    1. `pre`
       retained scope
       在
       `run0`
       直接失败
    2. `pre_gate`
       retained scope
       能过
       `run0`
       ，
       但在
       `run1`
       失败
    3. `full`
       retained scope
       在
       `run0`
       直接失败
  - 因而当前状态再次收紧为：
    - 在当前用户态控制面内，
      已测 retained subset
      没有可用幸存者
    - 当前更强结论已指向：
      retained reuse
      很可能需要
      lower control layer
- 2026-06-20 retained reuse formal blocker package 已就位：
  - 对应证据：
    - `mps/ANE/experiments/results/retained_reuse_formal_blocker_package.md`
  - 当前 machine-local 收敛结论：
    1. 当前 green/red
       判别面
       已恢复为：
       `process-fresh green`
       vs
       `in-process run2 red`
    2. 当前最小有效恢复动作
       已收敛到
       **free live transformer handles**
    3. 已测 retained subset
       在当前用户态控制面内
       无一存活
  - 因而当前 formal blocker
    已可表述为：
    retained reuse
    很可能需要
    低于当前用户态 cache/reset
    surface 的
    lower control layer
- 2026-06-21 selector-9 same-connection repeat 在首个真实 case 上未暴露新控制状态：
  - 对应证据：
    - `mps/ANE/.ane_runs/json/selector9_repeat_same_connection_data_precompiled_20260621.json`
    - `mps/ANE/.ane_runs/json/selector9_repeat_same_connection_data_precompiled_verdict_20260621.json`
  - 当前 machine-local 事实：
    1. `data_precompiled_path_hwx`
       case
       的第一次
       `rawPrepare`
       返回
       `0xe00002c1`
    2. 同一连接 / 同一 program
       上的第二次
       `rawPrepare`
       仍然返回
       `0xe00002c1`
    3. 且两次
       24B output prefix
       一致
  - 因而当前状态继续收紧为：
    - selector-9
      可见层
      在该 case 上
      没有暴露新的
      retained-control state
    - 若还要保留
      retained-control
      候选，
      其可信位置已更可能
      在 selector-9 visible layer
      之下
- 2026-06-21 selector-9 same-connection repeat 在第二个正交 case 上也同态：
  - 对应证据：
    - `mps/ANE/.ane_runs/json/selector9_repeat_same_connection_hwx_precompiled_20260621.json`
    - `mps/ANE/.ane_runs/json/selector9_repeat_same_connection_two_case_verdict_20260621.json`
  - 当前 machine-local 事实：
    1. `data_precompiled_path_hwx`
       case
       的第二次
       `rawPrepare`
       没有新状态
    2. `hwx_precompiled_path_hwx`
       case
       的第二次
       `rawPrepare`
       也没有新状态
    3. 两 case
       的第二次
       24B output prefix
       都与第一次一致
  - 因而当前状态继续收紧为：
    - selector-9
      visible layer
      作为 retained-control 候选
      已非常弱
    - 当前更可信的剩余控制语义
      已继续下压到
      selector-9 visible contract
      之下
- 2026-06-21 retained reuse handoff-boundary blocker package 已就位：
  - 对应证据：
    - `mps/ANE/experiments/results/retained_reuse_handoff_boundary_blocker_package.md`
  - 当前 machine-local 收敛结论：
    1. 当前用户态 retained-control
       surface
       已基本收尽
    2. selector-9 visible-layer
       repeat
       已不是高价值 retained-control 候选
    3. 当前 formal boundary
       已进一步收紧到
       shared-runtime handoff：
       `ProgramPartialUnwire -> ProgramLoad(load_type=2)`
  - 因而当前 retained reuse
    blocker
    已不仅是
    “broad lower control layer”，
    而是一个更具体的
    handoff-boundary
- 2026-06-21 dynamic-attach blocker package 已确认，passive sample 未能穿透 handoff 邻近层：
  - 对应证据：
    - `mps/ANE/experiments/results/retained_reuse_dynamic_attach_blocker_package.md`
    - `mps/ANE/.ane_runs/logs/aned_sample_during_runtime_probe_20260621.txt`
  - 当前 machine-local 事实：
    1. `aned`
       / `ANECompilerService`
       作为 platform binary
       无法被
       frida / lldb / dtrace-pid
       动态附加
    2. `sample(1)`
       在真实 runtime probe
       期间
       只稳定看到
       `ANEServicesThreadStart -> CFRunLoopRun -> mach_msg`
    3. 当前 passive path
       尚未把观察面
       拉到 handoff 邻近层
  - 因而当前状态继续收紧为：
    - 当前 formal blocker
      已同时包含：
      shared-runtime handoff boundary
      + machine-level dynamic-attach blocker
- 2026-06-21 client-side Frida capability 已确认可用：
  - 对应证据：
    - `mps/ANE/.ane_runs/json/client_side_frida_capability_verdict_20260621.json`
  - 当前 machine-local 事实：
    1. daemon-side dynamic attach
       仍被 AMFI
       结构性阻断
    2. 但 client-side Frida
       对自有 probe 进程
       已可成功 spawn
       并加载脚本
    3. 当前剩余问题
       是 hook 输出的稳定采集，
       不是 attach 能力本身
  - 因而当前状态继续收紧为：
    - 当前机器并非
      完全 capability-blocked
    - 仍保留一条
      client-side instrumentation
      路径
- 2026-06-21 client-side Frida 的 generic hook 点仍拿不到稳定 capture：
  - 对应证据：
    - `mps/ANE/.ane_runs/json/client_side_frida_generic_hook_negative_verdict_20260621.json`
  - 当前 machine-local 事实：
    1. attach 能力
       存在
    2. 但
       `IOConnectCallStructMethod`
       / `dlopen`
       / `dlsym`
       / 模块轮询
       这组 generic hook 点
       没有产出稳定事件
    3. `symbol-dump + pause`
       握手
       在 frida-spawn 下
       也未稳定成立
  - 因而当前状态继续收紧为：
    - 下一步应从
      generic hook
      转为
      precise address-aware
      harness
- 2026-06-21 `frida-spawn` 与 CLI `symbol-dump + pause` 握手当前不兼容：
  - 对应证据：
    - `mps/ANE/.ane_runs/json/frida_spawn_cli_pause_handshake_negative_verdict_20260621.json`
  - 当前 machine-local 事实：
    1. 直接运行 probe 时，
       CLI `symbol-dump + pause`
       可正常落盘
    2. 但同样参数
       在 `frida -f`
       spawn
       下不会产出 symbol dump
    3. no-op script
       也不能改变这个结果
  - 因而当前状态继续收紧为：
    - precise address-aware
      harness
      的当前阻塞点
      在 `frida-spawn`
      兼容性边界
- 2026-06-21 client-side Frida precise capture 已打通首个可用事件面：
  - 对应证据：
    - `mps/ANE/.ane_runs/json/client_side_frida_precise_capture_verdict_20260621.json`
    - `mps/ANE/experiments/frida_selector9_raw_prepare_trace.js`
  - 当前 machine-local 事实：
    1. 去掉
       `-q`
       后，
       `frida-spawn`
       已能保住
       `symbol-dump + pause`
       握手
    2. 已能稳定看到：
       `ANEServices` 模块加入、
       `dlsym`,
       `raw_prepare`,
       `IOConnectCallStructMethod(selector=4)`
    3. 当前仍未拿到
       干净的 buffer 前缀
       与 selector-9
       事件
  - 因而当前状态继续收紧为：
    - client-side Frida
      现在已经是
      可用的 lower-adjacent
      runtime capture path
    - 下一步不再是
      “让它能工作”，
      而是
      “让它命中正确 case / 正确 selector”
- 2026-06-21 现有 IOKit interposer 对 selector-9 仍然是 header-only + hang：
  - 对应证据：
    - `mps/ANE/.ane_runs/csv/selector9_iokit_trace_20260621.csv`
    - `mps/ANE/.ane_runs/json/selector9_iokit_trace_runtime_probe_20260621.json`
    - `mps/ANE/.ane_runs/json/selector9_iokit_interposer_negative_verdict_20260621.json`
  - 当前 machine-local 事实：
    1. selector-9 trace CSV
       只有 header
    2. JSON 输出
       为空
    3. runtime probe
       在 interposer 下
       挂住并需手工 kill
  - 因而当前状态继续收紧为：
    - 现有 public IOKit interposer
      不是 selector-9
      的稳定观测面
    - 如果继续本地下钻，
      更优先级应回到
      client-side Frida
      或更低观测点
- 2026-06-21 retained reuse current-layer formal closeout 已就位：
  - 对应证据：
    - `mps/ANE/experiments/results/retained_reuse_current_layer_formal_closeout.md`
  - 当前 machine-local 正式收口结论：
    1. 当前用户态 retained-control
       surface
       已经被压到
       formal closeout 条件
    2. 继续扩展同层
       retained subset /
       selector-9 visible repeat /
       bridge rebuild
       的边际收益
       已极低
  - 因而当前层
    已可视为
    formal closeout：
    剩余工作只属于
    lower-adjacent handoff
    或 capability escalation
- 2026-06-21 current capability boundary closeout 已确认：
  - 对应证据：
    - `mps/ANE/experiments/results/retained_reuse_current_capability_boundary_closeout.md`
    - `mps/ANE/.ane_runs/json/retained_reuse_current_capability_boundary_verdict_20260621.json`
  - 当前 machine-local 结论：
    1. 当前 capability boundary
       之上
       已无可信 retained-control path
    2. formal boundary
       已稳定停在：
       shared-runtime handoff
       + capability escalation
- 2026-06-21 `optOutOfModelMemoryUnwiring` / `kANEFKeepModelMemoryWiredKey` 候选已判死：
  - 对应证据：
    - `mps/ANE/.ane_runs/json/optout_model_memory_unwiring_candidate_closed_verdict_20260621.json`
  - 当前 machine-local 事实：
    1. 逆向结论里，
       `optOutOfModelMemoryUnwiring`
       对应
       `kANEFKeepModelMemoryWiredKey`
    2. 当前仓库源码里
       没有它的
       author 面
    3. 现有 direct-create
       文档已确认
       `keepWired`
       不改变
       lower create-program
       失败形态
  - 因而当前状态继续收紧为：
    - 这条 lower-adjacent
      retained-control 候选
      在当前 surface
      已判死
- 2026-06-21 explicit `ANEServicesProgramChainingPrepare` wrapper 也在 selector-9 之前被 gate 掉：
  - 对应证据：
    - `mps/ANE/.ane_runs/json/chaining_prepare_wrapper_preselector9_gate_verdict_20260621.json`
  - 当前 machine-local 事实：
    1. `ANEServicesProgramChainingPrepare`
       导出符号
       当前可解析
    2. 但显式调用后
       返回
       `0x14`
    3. 当前 trace
       里
       没有任何
       selector-9
       命中
    4. 同一条 trace
       仍只看到
       selector-4
       prepare family
  - 因而当前状态继续收紧为：
    - visible user-space
      chaining-prepare
      wrapper
      已不是可信 retained-control path
    - 当前 boundary
      已进一步压到
      wrapper gate
      之下
- 2026-06-18 严格串行 cross-process `A -> B` 证据，
  已把 eval 后 `0x12` 污染范围进一步钉死：
  - 进程 A：
    `mps/ANE/.ane_runs/csv/two_wrapper_after_eval_only_processA_serial_20260618.csv`
    中，
    `wrapper1_eval=1` 后，
    `wrapper2_map=0x12`
  - 进程 B（确认 A 已退出后再启动）：
    `mps/ANE/.ane_runs/csv/two_wrapper_after_map_only_processB_afterA_serial_20260618.csv`
    中，
    `wrapper1_map=1` 且 `wrapper2_map=1`
  - 因而当前最强表述已从
    “process-global / device-global runtime state”
    收紧成：
    “同进程 runtime-lower accepted-state / selector-2 side effect；
    process exit 后不会继续保留”
- 2026-06-15 新的 `ane_daemon_load_tap_probe` / machine-local XPC 证据：
  - `aneuserd` transport 不是“不兼容当前 `_ANEDaemonConnection` 协议”。
    用
    `--xpc-service-override com.apple.aneuserd`
    后，
    `compiledModelExistsFor:` /
    `compiledModelExistsMatchingHash:` /
    `loadModel:` 三条 selector
    都能收到正常 reply，不再像
    `com.apple.appleneuralengine.private`
    那样直接 `NSCocoaErrorDomain 4097`.
  - 对应证据：
    - `mps/ANE/.ane_runs/csv/ane_daemon_load_tap_probe_default_nonartifact_weighted_pre.csv`
    - `mps/ANE/.ane_runs/csv/ane_daemon_load_tap_probe_aneuserd_nonartifact_weighted_pre.csv`
  - 但这不等于 `aneuserd` 会自动解锁 regular/new-instance 语义：
    - 在默认 public route 和 `aneuserd` override 上，
      当 `modelInstParams.instanceName`
      正确编码成 `NSString`
      后，
      `loadModelNewInstance:options:modelInstParams:qos:error:`
      都不再是 transport 断连，
      而是稳定收到业务层：
      `Error Domain=com.apple.appleneuralengine Code=21`
      / `Program load new instance failure`
    - 对应证据：
      - `mps/ANE/.ane_runs/csv/ane_daemon_load_tap_probe_default_newinstance_restricted_no_hascache_v2.csv`
      - `mps/ANE/.ane_runs/csv/ane_daemon_load_tap_probe_aneuserd_newinstance_restricted_no_hascache_v2.csv`
      - `mps/ANE/.ane_runs/csv/ane_daemon_load_tap_probe_aneuserd_newinstance_restricted_yes_empty_v2.csv`
  - `loadModelNewInstance` 最初出现的 `4097 + no reply`
    不是 daemon 新实例路径本身崩溃，而是 probe 自己把
    `_ANEModelInstanceParameters`
    的 `_instanceName`
    编成了 `NSData`：
    - runtime introspection 已确认
      `_ANEModelInstanceParameters`
      只有：
      - `_instanceName :: NSString`
      - `_procedureArray :: NSArray`
    - `aneuserd` 日志已明确记录：
      `value for key 'instanceName' was of unexpected class 'NSData'`
      并在 decode selector
      `loadModelNewInstance:options:modelInstParams:qos:withReply:`
      时丢弃消息
    - runtime introspection 输出已单独落盘：
      `mps/ANE/.ane_runs/logs/ane_model_instance_parameters_runtime_introspection_20260615_0125.txt`
    - 对应持久化日志：
      `mps/ANE/.ane_runs/logs/aneuserd_aned_last15m_20260615_0120.log`
- 2026-06-15 继续下钻 `loadModelNewInstance` 后，当前 public new-instance 结论又收紧了一层：
  - 旧的 `ane_inmemory_new_instance_probe` 负结论里，
    `modelInstParams` 构造也被同一个问题污染过：
    - 之前把
      `_ANEModelInstanceParameters.withProcedureData:procedureArray:`
      的第一个参数当成 `NSData`
    - 现在已修正成 `NSString instanceName`
  - 在修正后，用真实成功的 in-memory base load
    (`base_shared_connection + base_internal_model`)
    重跑 strongest case：
    - option:
      `internal_model_url_path`
    - params:
      `real_proc_main_data_main_weight_sha`
    - 仍然稳定得到：
      `Error Domain=com.apple.appleneuralengine Code=21`
    - 对应证据：
      `mps/ANE/.ane_runs/csv/ane_inmemory_new_instance_probe_internalurl_weightsha_v2.csv`
  - 再把同一成功 base load 上的全部 base identifier 候选跑完：
    - `missing_base`
    - `model_hex`
    - `descriptor_hex`
    - `uuid`
    - `local_path`
    - `model_url_path`
    - `program_handle_decimal`
    - `internal_uuid`
    - `internal_model_url_path`
    - `internal_program_handle_decimal`
    - `model_hex_ibh`
    - 全部仍然统一返回：
      `Code=21 / Program load new instance failure`
    - 对应证据：
      `mps/ANE/.ane_runs/csv/ane_inmemory_new_instance_probe_baseinternal_allopts_weightsha_v2.csv`
  - 再把 strongest base-id
    `internal_model_url_path`
    固定后跑所有 param 形态，结果分成两类：
    1. `real_proc_main_data_main` /
       `real_proc_main_data_main_weight` /
       `real_proc_main_data_main_weight_sha`
       -> 有明确 reply，统一 `Code=21`
    2. `proc_main_empty_data` /
       `proc_main_data_main`
       -> request 发出，但 business reply 缺失
    - 对应证据：
      `mps/ANE/.ane_runs/csv/ane_inmemory_new_instance_probe_baseinternal_internalurl_allparams_v2.csv`
  - `aned` 最近 10 分钟日志已把这两类失败继续解释清楚：
    1. 对 real-procedure / real-weight 形态，
       `aned` 明确报：
       `No entitlement! [com.apple.aned.private.adapterWeight.allow = 0]`
    2. 对 shim 形态，
       `aned` 明确在 XPC decode 阶段丢消息：
       `decodeObjectForKey: class "CodexANEProcedureShim" not loaded or does not exist`
  - 这意味着：
    - 旧的“390 次都失败”里，
      至少一部分是 probe 形态错误造成的，
      不能再直接当作“lower semantic 全部证伪”
    - 但在把 `instanceName` 修正后，
      真实 base-load + 真实 procedure/weight
      仍然被
      `com.apple.aned.private.adapterWeight.allow`
      entitlement gate 卡住
  - 对应持久化日志/线索：
    - `mps/ANE/.ane_runs/logs/aned_last10m_20260615_0310.log`
    - `mps/ANE/.ane_runs/logs/adapterweight_entitlement_hits_20260615_0310.txt`
- 2026-06-15 新的 host-path 事实：
  - `com.apple.aned.private.adapterWeight.allow`
    不是只存在于某些无关 system binary；
    当前已确认它直接存在于
    `com.apple.modelmanager.inferenceprovider`
    生态里的正式宿主扩展：
    - `/System/Library/ExtensionKit/Extensions/InferenceProviderService.appex/Contents/MacOS/InferenceProviderService`
    - `/System/Library/ExtensionKit/Extensions/TGOnDeviceInferenceProviderService.appex/Contents/MacOS/TGOnDeviceInferenceProviderService`
    - `/System/Library/ExtensionKit/Extensions/VisualGenerationInference.appex/Contents/MacOS/VisualGenerationInference`
  - 其中
    `InferenceProviderService.appex`
    的 entitlements
    还明确包含：
    - `com.apple.aned.private.adapterWeight.allow`
    - `com.apple.aned.private.allow`
    - `com.apple.aned.private.processModelShare.allow`
    - `com.apple.security.exception.mach-lookup.global-name = com.apple.appleneuralengine`
  - system daemon 侧已确认真正的 host 是：
    - `/usr/libexec/modelmanagerd`
    - launchd MachServices:
      - `com.apple.modelmanager`
      - `com.apple.modelmanager.simulator`
      - feature-gated remote:
        `com.apple.modelmanager.remote`
    - `modelmanagerd` 自身 entitlements 明确包含：
      - `com.apple.modelmanager.inferenceprovidermanager`
      - `com.apple.private.extensionkit.host.unsandboxed-extensions-for-extension-points`
        -> `com.apple.modelmanager.inferenceprovider`
  - `modelmanagerd` / `ModelManagerServices` / provider extensions
    当前 machine-local 文本/运行时证据已经能拼出这条宿主链：
    - `ModelManagerServices`
      提供：
      - `ModelServiceClient`
      - `InferenceProviderXPCSender`
      - `InferenceProviderRequestStream`
      - `InferenceProviderXPCRequestDispatcher`
      - `PerRequestInferenceProviderXPCRequestDispatcher`
      - `InferenceProviderExtension`
      - `InferenceProviderDescriptor`
    - `modelmanagerd`
      日志/strings 明确包含：
      - `getInferenceProvider(withDescriptor:)`
      - `createSessionRequest`
      - `InferenceProviderExtensionConnection`
      - `requestInference`
      - `requestInputStreamInference`
      - `Builtin InferenceProviderService extension not found`
      - `directInferenceProviderEndpoint`
      - `InferenceProviderServiceConnection`
    - `TGOnDeviceInferenceProviderService`
      demangle 已确认其本质是：
      `ModelManagerServices.InferenceProviderExtension<TokenGenerationInference.TG_OnDeviceInferenceProvider>`
    - `TokenGenerationInference`
      demangle 已确认 provider 侧公开语义至少包含：
      - `OnDeviceInferenceProvider.requestOneShot(...)`
      - `OnDeviceInferenceProvider.requestStream(...)`
      - `TG_OnDeviceInferenceProvider.requestOneShot(...)`
      - `TG_OnDeviceInferenceProvider.requestStream(...)`
      - `TGIE5ANESessionObjC`
  - 2026-06-15 继续 reverse `ModelManagerServices` 后，
    当前 host-route schema 已经进一步落到字段级事实：
    - 本机 `swiftc` 仍然不能直接
      `import ModelManagerServices`
      (`no such module 'ModelManagerServices'`)，
      所以当前仍需沿
      `nm + swift-demangle + fieldmd`
      继续 reverse。
    - 外层 `ModelXPCRequest.CreateSessionRequest`
      已确认只有两个字段：
      1. `metadata : Session.Metadata`
      2. `alreadyLockedInferenceProvider : InferenceProviderDescriptor?`
    - `Session.Metadata.init(...)`
      已明确要求：
      - `assetBundleURI`
      - `useCaseID`
      - `onBehalfOfPID`
      - `parentOfOnBehalfOfPID`
      - `loggingIdentifier`
      - `id`
      - `sessionSetID`
    - `InferenceProviderDescriptor`
      已明确是：
      `init(id:instance:hostedOnServer:)`
      且字段级解析确认：
      - `id : String`
      - `instance : InferenceProviderDescriptor.Instance`
      - `hostedOnServer : Bool`
      其中 `Instance` 至少存在：
      - `defaultInstance`
      - `specificInstance(String)`
    - provider 内层还有独立
      `InferenceProviderXPCRequest`
      协议族；
      当前已确认至少包含：
      - `ConfigureBuiltInProviderRequest`
      - `DirectStreamHandshake`
      - `AwaitEndStreamRequest`
      - `FetchNextStreamResultsRequest`
      - `InputStreamEndedRequest`
      - `RequestRequest`
      - `InputStreamRequest`
      - `SessionTransition`
      - `TransitionAsset`
      - `PrewarmBundle`
      - `IsVersionSupported`
      以及 `WillCancel/EndOfStream/ClientTerminated`
      notification 家族。
    - 其中两个关键 provider-side request
      已落到字段级：
      1. `ConfigureBuiltInProviderRequest`
         只有一个字段：
         `provider : BuiltInInferenceProvider`
      2. `DirectStreamHandshake`
         只有一个字段：
         `requestID`
         且从
         `InferenceProviderXPCSender.directStreamHandshake(requestIdentifier:)`
         可收紧到
         `requestID ~ RequestKey`
      3. `InferenceRequest`
         已确认有 4 个字段：
         - `isStream`
         - `clientData`
         - `configuration`
         - `requestIdentifier`
      4. `InputStreamInferenceRequest`
         已确认有 4 个字段：
         - `clientDataArray`
         - `metadata`
         - `configuration`
         - `requestIdentifier`
    - provider 发射器语义也已经明确：
      - `InferenceProviderXPCSender.__allocating_init(builtInProvider:session:)`
      - `requestInference(asStream:clientData:configuration:)`
      - `requestInputStreamInference(clientDataArray:metadata:configuration:)`
      - 返回
        `InferenceProviderRequestResult`
        且结果里存在：
        - `firstResponse`
        - `directInferenceProviderEndpoint`
    - `InferenceProviderRequestConfiguration.init(...)`
      已明确要求：
      - `sessionLoggingIdentifier`
      - `requestLoggingIdentifier`
      - `assetIdentifiers`
      - `requestUUID`
      - `sessionUUID`
      - `sessionSetID`
      - `onBehalfOfPID`
      - `parentOfOnBehalfOfPID`
      - `auditToken`
      - `auditSessionUID`
  - 2026-06-22 新的 provider-management object-graph 事实：
    - 证据文件：
      - `mps/ANE/.ane_runs/json/modelmanagerd_provider_management_sender_object_graph_verdict_20260622.json`
    - 当前已不只是字符串层推测，而是有 Swift class ivar 元数据 + 真实外部调用点共同收敛：
      - `InferenceProviderAssetManager`
        持有：
        - `providerManager`
        - `modelCatalog`
        - `neuralEngine`
      - `InferenceProviderManager`
        持有：
        - `inferenceProviderConnections`
      - `InferenceProviderExtensionConnection`
        持有：
        - `sender`
        - `activeRequest`
        - `descriptor`
        - `providerIdentification`
    - 同时，`modelmanagerd` 自身已确认存在对
      `ModelManagerServices.InferenceProviderXPCSender`
      的真实代码引用，而不只是 strings：
      - `0x1000603d4` -> `InferenceProviderXPCSender.init(session:)`
      - `0x100060458` -> `InferenceProviderXPCSender.init(builtInProvider:session:)`
      - `0x10006c3f4` -> `requestInputStreamInference(clientDataArray:metadata:configuration:)`
      - `0x1000672b0` -> `sessionTransition(to:with:)`
      - `0x100067fa8` -> `prewarmBundle(information:)`
      - `0x100068f74` -> `transitionAsset(withDescriptor:to:from:requestIdentifier:)`
    - 这意味着：
      - 当前已可正式确认 provider-management **不是** 纯 asset-bookkeeping 层
      - lower-control carrier 已经以
        `InferenceProviderExtensionConnection.sender`
        的形式浮出到 `modelmanagerd`
      - 当前第一条已证实的宿主对象图是：
        `InferenceProviderAssetManager -> providerManager -> inferenceProviderConnections -> InferenceProviderExtensionConnection.sender`
    - 仍未证明的点只剩一个：
      - `assetBundleWithNewAndExistingAssets(for:runtimeAssets:inferenceProviderConnection:)`
        是否就是直接跨进这条 sender-backed 路径的函数级 seam，
        还是还要再经过某个相邻的
        `InferenceProviderExtensionConnection` /
        state-transition helper
  - 2026-06-22 `assetBundleWithNewAndExistingAssets(...)` 已被进一步判定为更像 AssetManager-side seam，而不是直接 sender seam：
    - 证据文件：
      - `mps/ANE/.ane_runs/json/modelmanagerd_assetbundle_function_seam_verdict_20260622.json`
    - 当前 machine-local 证据显示两簇分离：
      1. AssetManager / asset-state 窗口：
         - `assetBundleWithNewAndExistingAssets(for:runtimeAssets:inferenceProviderConnection:)`
         - `failed to transition to dynamic mode`
         - `Dynamic mode asset`
         - `InferenceProvider assets are de-synced with MM (alreadyLoaded)`
         - 对应已落到的反汇编窗口至少包括：
           - `0x1000b6608`
           - `0x1000c26ac`
      2. sender-backed lower-control 窗口：
         - `0x1000603d4` -> `InferenceProviderXPCSender.init(session:)`
         - `0x100060458` -> `InferenceProviderXPCSender.init(builtInProvider:session:)`
         - `0x1000672b0` -> `sessionTransition(to:with:)`
         - `0x100067fa8` -> `prewarmBundle(information:)`
         - `0x100068f74` -> `transitionAsset(withDescriptor:to:from:requestIdentifier:)`
         - `0x10006c3f4` -> `requestInputStreamInference(clientDataArray:metadata:configuration:)`
    - 当前还没有在已落到的 `0x1000b* / 0x1000c*` AssetManager 窗口里看到
      `InferenceProviderXPCSender`
      的 ctor / request / transition 代码引用
    - 因而这轮可以正式收敛：
      - `assetBundleWithNewAndExistingAssets(...)`
        更像 **AssetManager-side preparation / asset-state seam**
      - 它不是当前最直接的 sender-backed function-level edge
      - 当前更像 first direct seam 的是相邻的
        `InferenceProviderExtensionConnection`
        sender/state cluster，
        尤其是
        `setCurrentState creating new sender part`
        所在的状态迁移窗口
  - 2026-06-22 `InferenceProviderExtensionConnection setCurrentState creating new sender part` 已进一步收敛成当前最强 direct seam：
    - 证据文件：
      - `mps/ANE/.ane_runs/json/modelmanagerd_extensionconnection_sender_creation_seam_verdict_20260622.json`
    - 当前 machine-local 证据已把 sender/state cluster 再压小一层：
      - `0x10005f73c`
        引用日志：
        `InferenceProviderExtensionConnection setCurrentState creating new sender part`
      - 该窗口在记录 sender-part 创建后，立刻：
        - `swift_task_alloc`
        - 写入 continuation/function pointer
        - 并继续沿用当前上下文对象中的状态字段
      - 紧邻的 continuation cluster
        `0x10006036c–0x100060458`
        已确认直接调用：
        - `InferenceProviderXPCSender.init(session:)`
        - `InferenceProviderXPCSender.init(builtInProvider:session:)`
      - 两个窗口都读取同一类上下文/task-state 偏移，
        当前至少共同命中：
        - `x22 + 0x1d0`
    - 因而当前可以把函数级结论再收敛一步：
      - `assetBundleWithNewAndExistingAssets(...)`
        不是 first direct seam
      - 当前最强的 first direct host-side lower-control seam
        已经缩到
        `InferenceProviderExtensionConnection`
        的 sender/state 迁移窗口
      - 更具体地说：
        `setCurrentState creating new sender part`
        会直接先于、并高度疑似调度进，
        `InferenceProviderXPCSender`
        的 materialization continuation cluster
  - 2026-06-22 sender ctor 分支已压到“多载荷 enum + built-in payload”级：
    - 证据文件：
      - `mps/ANE/.ane_runs/json/modelmanagerd_sender_ctor_branch_control_verdict_20260622.json`
    - 当前在
      `0x10006036c–0x100060458`
      的 sender materialization cluster 已确认：
      - 分支输入来自 task/context frame：
        `ldp x19, x20, [x22, #0x1f8]`
      - 随后经
        `0x100055bb0`
        和
        `_swift_getEnumCaseMultiPayload`
        取 case tag
      - 然后做：
        `cmp w0, #0x1`
      - `w0 == 1`
        走：
        `InferenceProviderXPCSender.init(session:)`
      - `w0 != 1`
        走：
        `InferenceProviderXPCSender.init(builtInProvider:session:)`
    - 同时，在
      `0x100063ca8–0x100063ce0`
      已看到更强的 payload 证据：
      - 显式 materialize
        `BuiltInInferenceProvider`
        metadata
      - 向目标槽写入该 payload
      - 再以
        `w2 = 0`
        调
        `_swift_storeEnumTagMultiPayload`
    - 因而当前最合理、且已有强证据支撑的语义是：
      - 这个 ctor 分支受一个 **多载荷 enum**
        控制
      - `tag 0`
        对应
        `BuiltInInferenceProvider`
        payload case
      - `tag 1`
        对应 non-built-in / plain-session case
    - 仍未恢复的只剩：
      - 这个多载荷 enum 的**精确 Swift 类型名**
      - 以及它与后续统一 request 上游的更完整命名关系
  - 2026-06-22 major provider request/transition API 已进一步确认共享 sender-state 上游：
    - 证据文件：
      - `mps/ANE/.ane_runs/json/modelmanagerd_sender_shared_upstream_verdict_20260622.json`
    - 当前最强的 class/layout 结合证据：
      - `InferenceProviderExtensionConnection.sender`
        的 ivar 偏移已知为
        `112 / 0x70`
    - 三条最清楚的 sender API 路径都直接命中这个偏移：
      1. `sessionTransition`
         - 从 `x22 + 0x28` 取对象指针
         - 再取 `[object + 0x70]`
         - 然后进入
           `InferenceProviderXPCSender.sessionTransition(...)`
      2. `prewarmBundle`
         - 从 `x22 + 0x20` 取对象指针
         - 再取 `[object + 0x70]`
         - 然后进入
           `InferenceProviderXPCSender.prewarmBundle(...)`
      3. `transitionAsset`
         - 从 `x22 + 0xf8` 取对象指针
         - 再取 `[object + 0x70]`
         - 然后进入
           `InferenceProviderXPCSender.transitionAsset(...)`
    - `requestInputStreamInference`
      当前 slice 更间接，但仍落在同一类
      `x22` task/context frame
      与
      `swift_task_alloc + continuation`
      家族里，并紧邻同一组 sender API 调度逻辑
    - 因而当前可以把“统一上游”正式收敛为：
      - major provider request/transition API
        共享的 host-side carrier
        就是
        `InferenceProviderExtensionConnection`
        的 sender/state frame
      - 这比继续回头抠 AssetManager 或更早层更接近 lower control layer
  - 2026-06-22 shared sender/state frame 已恢复出第一批可操作 slot：
    - 证据文件：
      - `mps/ANE/.ane_runs/json/modelmanagerd_sender_frame_slot_recovery_verdict_20260622.json`
    - 当前最稳的 sender mirror slots：
      - `sessionTransition`
        - source object slot:
          `x22 + 0x28`
        - sender load:
          `[object + 0x70]`
        - frame mirror slot:
          `x22 + 0x88`
      - `prewarmBundle`
        - source object slot:
          `x22 + 0x20`
        - sender load:
          `[object + 0x70]`
        - frame mirror slot:
          `x22 + 0x98`
      - `transitionAsset`
        - source object slot:
          `x22 + 0xf8`
        - sender load:
          `[object + 0x70]`
        - frame mirror slot:
          `x22 + 0x1c8`
    - 当前两组最值得继续追的参数 slab：
      1. `requestInputStreamInference`
         - 紧凑 slab:
           `x22 + 0xb8 .. 0xc8`
         - 调度前直接装入：
           - `x0,x1 <- [x22 + 0xb8]`
           - `x2,x3 <- [x22 + 0xc8]`
         - 对应 task/continuation slot:
           `x22 + 0x1a0`
      2. `transitionAsset`
         - 富控制 slab:
           `x22 + 0x130 .. 0x200`
         - 其中
           `w1 <- [x22 + 0x200]`
           当前最像 load-state enum 输入
         - 同时还读取：
           - `0x160 / 0x170 / 0x180 / 0x1a0`
           这使它成为当前信息密度最高、最适合继续做字段恢复或 patch 试探的 sender-state slab
  - 2026-06-22 `transitionAsset` 富控制 slab 已恢复出第一层字段语义：
    - 证据文件：
      - `mps/ANE/.ane_runs/json/modelmanagerd_transitionasset_control_slot_semantics_verdict_20260622.json`
    - 当前最硬的 slot 语义恢复：
      - `x22 + 0x200`
        -> 当前最强的 `LoadState` 候选
        - 直接以
          `ldr w1, [x22, #0x200]`
          形式读出
        - 位于
          `transitionAsset`
          富控制 slab 的第一批 typed helper 参数里
        - 从签名角度看，
          `transitionAsset(withDescriptor:to:from:requestIdentifier:)`
          里最符合这种窄整数/enum 形状的就是
          `to/from LoadState`
      - 当前还不能严谨地区分它是
        `to`
        还是
        `from`
        ，但已经足够把它列为下一轮最优先的 patch/probe 候选
    - 同时，当前 slab 内还出现了更明确的 descriptor 信号：
      - 路径中加载了
        `InferenceProviderDescriptor`
        的
        `CustomStringConvertible`
        witness
      - 并且
        `x22 + 0xf8`
        对应的对象在后半段被 retain / 复用，
        这强化了
        `transitionAsset`
        slab 不只是 state enum，还携带 descriptor 相关材料
    - 因而当前最值得继续追的不是再证明“它像不像”，而是：
      - 把
        `x22 + 0x200`
        及其邻近 slot
        进一步区分成
        `to/from LoadState`
      - 把 descriptor / request metadata / request ID
        从
        `x22 + 0x130 .. 0x1a0`
        中再各自压出至少一个更具体的锚点
  - 2026-06-22 `transitionAsset` 的首选最小 patch 点已进一步收敛：
    - 证据文件：
      - `mps/ANE/.ane_runs/json/modelmanagerd_transitionasset_patchpoint_priority_verdict_20260622.json`
    - 当前首选 patch/probe 点：
      - `x22 + 0x200`
    - 选择理由已经够硬：
      1. 它以
         `ldr w1, [x22, #0x200]`
         的形式，
         在 rich slab 中**最早**进入首批 typed helper
      2. 它是当前恢复出的 slot 里，
         **最窄、最像 enum、最容易单点改写**
         的控制位
      3. 相较之下，
         `0x130 / 0x148 / 0x158 / 0x160 / 0x170 / 0x180`
         更多表现为 pointer/pair/witness 风格的复合输入，
         先 patch 它们的解释性更差、风险更高
      4. `x22 + 0xf8`
         虽然是 descriptor/source-object 锚点，
         但它是更宽的对象级杠杆，
         不如 state slot 适合作为第一刀
    - 当前最合理的 patch 优先级已经可以写死为：
      1. 第一候选：
         `x22 + 0x200`
      2. 第二候选：
         `x22 + 0xf8`
         所在的 descriptor/control-object 路径
    - 仍待收紧的只剩：
      - `x22 + 0x200`
        到底是
        `to`
        还是
        `from`
        的 `LoadState`
  - 2026-06-22 `x22 + 0x200` 的首个 probe 值已进一步收敛：
    - 证据文件：
      - `mps/ANE/.ane_runs/json/modelmanagerd_transitionasset_first_probe_value_verdict_20260622.json`
    - 当前首个 probe 值：
      - `dynamicMode`
    - 选择原因已经够强：
      1. 当前最直接的可观测面高度集中在
         dynamic-mode 相关结果：
         - `failed to transition to dynamic mode`
         - `Failed to move asset %s to dynamic mode: %@`
         - `Failed to move asset %s to dynamic mode in %s: %@`
      2. 相比之下，
         `loaded`
         受
         `alreadyLoaded`
         / self-heal 路径干扰更大，
         第一针的信息量更差
      3. `unloaded`
         在当前附近的 strings / 日志面里也不如
         `dynamicMode`
         直接
    - 当前对
      `to` vs `from`
      的最优先工作假设也已更新为：
      - `x22 + 0x200`
        更像
        `to`-side `LoadState`
      - 理由不是“已证实”，而是：
        - 它作为 rich slab 中最早的窄 enum-like scalar 被注入
        - 附近出现
          `Load in called for terminated extension`
          这类更像 destination-oriented 的语义面
    - 因而下一轮不应再问“先试哪个值”，而应直接围绕：
      - 把
        `x22 + 0x200`
        改向
        `dynamicMode`
        设计最小 probe
      - 观察它是否把路径推向更明确的
        dynamic-mode 成功 / 失败 / self-heal 分支
  - 2026-06-22 `x22 + 0x200 -> dynamicMode` 的最小 patch 原型已落地：
    - 证据文件：
      - `mps/ANE/.ane_runs/json/modelmanagerd_transitionasset_dynamicmode_patch_verdict_20260622.json`
    - patch 脚本：
      - `mps/ANE/experiments/modelmanagerd_transitionasset_dynamicmode_patch.py`
    - 输入 / 输出样本：
      - input:
        `mps/ANE/.ane_runs/tmp/modelmanagerd_arm64e_20260622`
      - output:
        `mps/ANE/.ane_runs/tmp/modelmanagerd_arm64e_transitionasset_dynamicmode_patch_20260622`
    - 当前 patch 位点已经收敛成一条 producer-side 单指令替换：
      - 地址：
        `0x10006881c`
      - before:
        `ldr x8, [x8, #0x3f0] ; LoadState.loaded`
      - after:
        `ldr x8, [x8, #0x3e8] ; LoadState.dynamicMode`
    - 这条 patch 的价值在于：
      - 不去破坏后续
        `ldr w1, [x8]`
        与
        `str w1, [x22, #0x200]`
        的现有流
      - 只改变 rich slab 对
        `x22 + 0x200`
        选择的 `LoadState`
      - 因而它比直接 patch consumer 更干净，也更利于解释结果
    - 当前 machine-local 校验已完成：
      - patched 文件 `0x6881c`
        从
        `0xf941f908`
        变成
        `0xf941f508`
      - 反汇编已显示：
        `LoadState.dynamicMode`
      - `useCaseIdentifier`
      - `assetBundleIdentifier`
      - `requestVersion`
      - `requestPriority`
      - `subrequestID`
      - `clientSessionData`
    - `RequestMetadata.init(...)`
      已明确要求：
      - `loggingIdentifier`
      - `clientData`
      - `UUID`
      - `sessionID`
      - `requiredAssetIDs`
      - `isInference`
      - `isStream`
      - `isInputStream`
      - `subrequestID`
      - `allInputStreamed`
      - `useCaseID`
    - `com.apple.modelmanager.inferenceprovider`
      生态下当前枚举到的 provider id
      已不止最初 3 个：
      - `BlackPowderInferenceProvider`
      - `CoreMotionFoundationModelInferenceProvider`
      - `com.apple.modelmanager.inferenceprovider.built-in`
      - `generative-experiences-safety-inference-provider`
      - `host-inference`
      - `pcc-agent-client`
      - `private-ml-client`
      - `token-generation-inference`
      - `visual-generation-inference`
    - 但 machine-local 上带
      `com.apple.aned.private.adapterWeight.allow`
      的当前只确认有：
      - `com.apple.modelmanager.inferenceprovider.built-in`
      - `token-generation-inference`
      - `visual-generation-inference`
    - 这进一步说明：
      - extension-level provider 选择
        与 built-in appex 内部的
        `BuiltInInferenceProvider`
        不是同一层命名空间
      - host route
        不是“createSession 后直接 eval”，
        而是：
        `modelmanagerd outer session`
        +
        `provider-side InferenceProviderXPCRequest inner protocol`
    - 2026-06-15 对
      `InferenceProviderService.appex`
      本体继续下钻后，
      `built-in` 这条路又收紧了一层：
      - `BuiltInInferenceProvider.inferenceProvider.getter`
        在 appex 本体里直接 decompile 成
        `fatalError`
      - `BuiltInInferenceProviderService`
        传给
        `InferenceProviderXPCRequestDispatcher.ProviderConfiguration.uninitializedBuiltIn(_:)`
        的本地 closure
        (`0x1000019ac`)
        也直接 decompile 成
        `fatalError`
      - 两处都指向：
        `InferenceProviderService/BuiltInInferenceProviderExtensions.swift`
      - 因而在当前 machine-local image 上，
        `com.apple.modelmanager.inferenceprovider.built-in`
        更像 placeholder / dead end，
        不是最现实的 adapter-weight ANE 执行面
    - 相对地，
      `token-generation-inference`
      已进一步确认是更真实的下一跳：
      - `TGOnDeviceInferenceProviderService`
        是
        `InferenceProviderExtension<TG_OnDeviceInferenceProvider>`
      - 它直接链接：
        `TokenGenerationInference.framework`
      - `TokenGenerationInference`
        里已明确存在：
        - `TG_OnDeviceInferenceProvider.requestOneShot(...)`
        - `TG_OnDeviceInferenceProvider.requestStream(...)`
        - `TGIE5ANESessionObjC`
        - `adapterWeightsFileName`
        - `ANEClientModelAssetPath`
        - `TGI_ANE_Clear_State`
      - 这说明下一轮若继续 host-route，
        优先 target 应该转向：
        `token-generation-inference -> TokenGenerationInference.framework`
    - 2026-06-15 继续沿
      `TokenGenerationInference.framework`
      做 shell 级逆向后，
      这条主线又收紧了一层：
      - 已确认关键入口地址：
        - `TG_OnDeviceInferenceProvider.requestOneShot`
          -> `0x275149e04`
        - `TG_OnDeviceInferenceProvider.requestStream`
          -> `0x2751564bc`
        - `OnDeviceInferenceContextFactory.createInferenceContext(...)`
          -> `0x2751295dc`
      - `requestOneShot/requestStream`
        都不是单薄 wrapper；
        当前已从 state-machine 片段看到它们命中：
        - `createInferenceContext(...).addPromptLookup`
        - `createInferenceContext(...).addPriorOutputSpeculation`
        - `createInferenceContext(...).buildDecoder`
      - provider 内明确存在
        per-request session configuration 构造，
        且日志点已经确认：
        - `tgSessionConfiguration for requestOneShot: %s`
        - `tgSessionConfiguration for prewarm: %s`
        - `tgSessionConfiguration for requestStream: %s`
      - `TGIE5ANESessionObjC`
        的角色也已收紧：
        - `initWithResourceURL:useEnergyEfficientMode:assetIdentifier:`
          只保存
          `resourceURL/useEnergyEfficientMode/assetIdentifier`
        - `resume`
          -> `sendStartSignalForResource:useEnergyEfficientMode:assetIdentifier:`
        - `stop`
          -> `sendStopSignalForResource:`
        - `dealloc`
          也会发 stop
      - 这说明：
        - `TGIE5ANESessionObjC`
          更像 session-lifecycle / ANE signal wrapper，
          不是完整 inference graph 执行面
        - 真正的 request shaping / model path
          仍在
          `TG_OnDeviceInferenceProvider`
          +
          `OnDeviceInferenceContextFactory`
    - 2026-06-15 再往 provider runtime / asset staging
      侧下钻后，
      `TokenGenerationInference.framework`
      已经出现更具体的 machine-local 执行链：
      - `TGIModelConfigurationObjC`
        当前已确认至少持有：
        - `modelBundlePath`
        - `adapterConfigurations`
        - `serializeModelIOPath`
        - `baseModel`
        - `useEnergyEfficientMode`
        - `useModelCatalogE5CompilerCache`
        - `assetIdentifier`
      - `TGIE5BaseModelObjC.initWithModelConfiguration:`
        已确认会：
        1. 读取
           `modelBundlePath`
        2. 通过
           `URLWithString:`
           生成 resource URL
        3. 读取
           `useEnergyEfficientMode`
           与
           `assetIdentifier`
        4. 构造
           `TGIE5ANESessionObjC.initWithResourceURL:useEnergyEfficientMode:assetIdentifier:`
           并保存到 `aneSession`
      - `TGIE5BaseModelObjC.load:`
        已确认会：
        1. 记录
           `Loading base model with model : %@`
        2. 从
           `modelURL.path`
           取出 bundle path
        3. 调用
           `cgm::token_generation_inference::espresso_inference::AJAXE5MLModelBase::create(path)`
        4. `setBaseModel:`
        5. `aneSession.resume`
        - 因而
          base model 真正落到的是
          `AJAXE5MLModelBase`
          +
          `TGIE5ANESessionObjC`
          这条组合链
      - `BaseModelLoader.load(from:)`
        与
        `LanguageModelLoader.load(from:baseModel:)`
        也已落到 machine-local 代码位点：
        - `LanguageModelLoader`
          会基于
          `TGIModelConfigurationObjC.modelBundlePath`
          做 asset / bundle 形态判断
        - 在需要 Objective-C loader 的分支上，
          它会调用
          `initWithModelConfiguration:error:`
      - `AppAssetManager`
        已不再只是 field / string 级存在；
        当前已确认至少有两条真实调用面：
        1. `OnDeviceAssetRepository.handleCustomAsset...`
           -> `AppAssetManager(identifier:auditToken:...)`
           -> `copyAssetsIfNeeded(metadata, adapterWeights, draftMIL, draftWeights)`
        2. `TG_OnDeviceInferenceProvider.compileAdapter(...)`
           -> `AppAssetManager(identifier:auditToken:...)`
           -> `copyAssetsIfNeeded(metadata, adapterWeights, draftMIL, draftWeights)`
        - 这说明
          adapter / draft asset staging
          是 provider 自己的正式执行流，
          不是外围脚手架
      - `TGI_ANE_Clear_State`
        也已收紧到具体 C++ 执行面：
        - 命中
          `cgm::token_generation_inference::ajax::ANEAJAXE5MLModel::clearAllState`
          及其 block invoke
        - 其中会对
          `in_embeddings`
          所在的 memory objects 集合做
          `zeroAllMemoryObjects(...)`
        - 因而它不是高层配置 key，
          而是运行时清 state / 清 memory object
          的真实路径
      - `TGIModelConfigurationObjC`
        到 compile/load contract
        的桥接位点也已进一步确认：
        - `-[TGIModelConfigurationObjC modelConfiguration]`
          会把
          `adapterConfigurations`
          /
          `e5Functions`
          组装进内部 vector
        - 同时会把：
          - `useModelCatalogE5CompilerCache`
          - `ignoreUnknownTokens`
          - `serializeModelIOPath`
          明确写入内部 config
        - `serializeModelIOPath`
          不是 metadata-only 字段；
          当前已看到它被转成
          `UTF8String`
          并 append 进内部 `basic_string`
      - `E5RunnerObjC`
        的 compile / precheck
        对这些字段有直接消费：
        - `+[E5RunnerObjC compiledModelWithConfiguration:bundleCachePath:error:]`
          会：
          1. 先用
             `compilerOptionsForModelType(TGIModelType)`
             选择
             `makeANEAjaxCompilerOptions`
             /
             `makeGPUAjaxCompilerOptions`
             /
             `makeCPUAjaxCompilerOptions`
          2. 再把
             `modelBundlePath`
             转成 filesystem path
          3. 若有 bundle cache path，
             调
             `makeProgramLibrary(path, compilerOptions, optional<string> bundleCachePath)`
          4. 若无 bundle cache path，
             调
             `makeProgramLibrary(path, compilerOptions, bool useModelCatalogE5CompilerCache)`
        - `+[E5RunnerObjC doesModelRequireCompilationWithConfiguration:bundleCachePath:]`
          也会：
          1. 读取
             `modelBundlePath`
             /
             `modelType`
          2. 做一层 path-extension 分流
          3. 最终调
             `modelRequiresCompilation(...)`
             的
             `optional<string> bundleCachePath`
             或
             `bool useModelCatalogE5CompilerCache`
             形态
        - 这说明：
          `useModelCatalogE5CompilerCache`
          已经是 machine-local 可见的
          compile/load contract 控制位，
          不只是高层布尔配置
        - `+[E5RunnerObjC compiledModelAtPath:modelType:bundleCachePath:error:]`
          也已补到一个关键细节：
          - 它会先构造
            `TGIModelConfigurationObjC`
          - 然后按
            `bundleCachePath == nil`
            设置
            `setUseModelCatalogE5CompilerCache:`
          - 再调用
            `compiledModelWithConfiguration:bundleCachePath:error:`
          - 即：
            `useModelCatalogE5CompilerCache`
            在这条 helper 上
            就是
            “没有显式 bundleCachePath 时使用 model catalog E5 cache”
            的直接编码
        - 额外的静态字符串证据也已补上：
          - `.bundle`
          - `.mil`
          - `Model path has .bundle extension, assuming its already compiled: %@`
          - `/var/mobile/Library/com.apple.modelcatalog/compiled/e5bundlecache/`
          - `/var/db/com.apple.modelcatalog/protected/compiled/e5bundlecache`
        - 这说明：
          - path-extension 分流大概率确实在区分
            precompiled bundle
            与
            source MIL
          - `bundleCachePath` /
            `useModelCatalogE5CompilerCache`
            很可能直接影响
            model catalog E5 compiler cache
            的命中方式
      - `LanguageModelLoader.load(from:baseModel:)`
        的 extension 分流也已进一步收紧：
        - 当前已确认
          `.mil`
          与
          `.bundle`
          两类 extension
          都会落到
          `E5RunnerObjC.initWithModelConfiguration:error:`
        - 而
          `E5RunnerObjC.initWithModelConfiguration:error:`
          会先调：
          `AJAXE5MLModelLoader::createModelFromBundle(TGIModelConfiguration)`
        - 之后若
          `modelType == 1`
          （当前与
          `makeANEAjaxCompilerOptions`
          分支一致，指向 ANE）
          ，则它会：
          1. 取
             `adapterConfigurations.anyObject`
          2. 若存在
             `mutableWeightsFilePath`
             则优先把它转成
             `resourceURL`
          3. 否则退回
             `modelBundlePath`
          4. 再构造
             `TGIE5ANESessionObjC.initWithResourceURL:useEnergyEfficientMode:assetIdentifier:`
             并立即 `resume`
        - 这说明：
          adapter mutable-weights 路径
          不是附属 metadata，
          而是 ANE session resource
          的直接来源之一
      - `mutableWeightsFilePath`
        的上游构造也开始落地：
        - provider 内至少有一条路径会在
          `fileExistsAtPath(...)`
          命中后，
          构造：
          `TGIAdapterConfigurationObjC.initWithAdapterType:symbolName:mutableWeightsFilePath:`
        - 当前 import 还已明确出现：
          - `ModelCatalog.LLMModelAssetMetadata.ANEExtendInfo.adapterType`
          - `adapterTypeToSymbolMapping`
          - `adapterTypeToSignatureMapping`
        - 因而
          `adapterType/symbolName/mutableWeightsFilePath`
          大概率来自 model-catalog / adapter metadata
          而不是纯本地硬编码
        - 更具体地，
          `OnDeviceAssetRepository.handleCustomAsset...`
          当前已看到：
          1. 先走
             `AppAssetManager.copyAssetsIfNeeded(...)`
          2. 再在自定义 asset 路径上
             处理
             `TGIGenericModelBundleID`
             分支
          3. 若
             `/var/mobile/ajax/adapter.weights.bin`
             存在，
             就构造
             `TGIAdapterConfigurationObjC.initWithAdapterType:symbolName:mutableWeightsFilePath:`
          4. 再用
             `/var/mobile/ajax/model.bundle`
             +
             adapter config
             +
             e5 functions
             构造
             `TGIModelConfigurationObjC`
        - 这说明：
          `/var/mobile/ajax/adapter.weights.bin`
          /
          `/var/mobile/ajax/model.bundle`
          当前很像 custom adapter / bundle
          publish 之后的标准落点
        - 2026-06-15 进一步收紧后，
          `compileAdapter(...)`
          与
          `loadAsset(...)`
          的职责边界已更清楚：
          1. `compileAdapter(...)`
             真实主体在
             `0x275165634`
             ，会：
             - 读取 audit token
             - 构造
               `AppAssetManager(identifier:auditToken:)`
             - 调
               `AppAssetManager.copyAssetsIfNeeded(metadata, adapterWeights, draftMIL, draftWeights)`
             - 只显式消费
               `AppAssetManager.draftMILFileName`
               并进入
               `DraftModelCompiler.findCompiledDraftPathOrBeginCompilation(...)`
          2. 当前 machine-local xref
             没看到
             `compileAdapter(...)`
             直接引用：
             - `/var/mobile/ajax/model.bundle`
             - `/var/mobile/ajax/adapter.weights.bin`
          3. 因而
             `compileAdapter(...)`
             当前更像：
             custom asset copy
             +
             draft-model compile kick
             ，
             不是
             `/var/mobile/ajax/*`
             pair
             的直接 publish writer
        - `AppAssetManager`
          默认文件名也已落到本地代码位点：
          - `adapterWeightsFileName = "lora.part.bin"`
          - `draftMILFileName = "draft.mil"`
          - `draftWeightsFileName = "draft_weights.bin"`
          - 这些默认名来自：
            `AppAssetManager.__allocating_init(identifier:auditToken:)`
            (`0x2750d8a28`)
          - 同一构造函数还直接暴露：
            - base root:
              `/private/var/db/AppleIntelligencePlatform/AppModelAssets`
            - temporary suffix:
              `tmp/`
            - manifest file:
              `manifest.json`
        - `AppAssetManager.copyAssetsIfNeeded(...)`
          的 immediate write
          侧也进一步收紧：
          1. 先调用：
             - `createCacheDirectoryIfNeeded()`
             - `createTemporaryDirectoryIfNeeded()`
          2. 再对
             `metadata / adapterWeights / draftWeights / draftMIL`
             四类 asset
             逐个做：
             - destination URL 拼接
             - `fileExistsAtPath:` 跳过
             - `copyContents(fd, url)`
          3. `copyContents(of:to:)`
             自身会记录：
             `Copying file descriptor %{public}d to %{public}s`
             并执行实际文件拷贝
          4. 当前 machine-local
             更像：
             `copyAssetsIfNeeded(...)`
             的 immediate destination
             是
             `AppAssetManager`
             internal cache/temp tree，
             不是真正直接把文件写成
             `/var/mobile/ajax/model.bundle`
             /
             `/var/mobile/ajax/adapter.weights.bin`
        - `loadAsset(...)`
          当前已可更具体地写成：
          1. `loadAsset` 的
             `TY0`
             分支
             (`0x275151754`)
             会先看
             override/default
             路径是否存在
          2. 若命中，
             就直接构造：
             `TGIAdapterConfigurationObjC.initWithAdapterType:symbolName:mutableWeightsFilePath:`
          3. 其中当前已确认的 fallback/default
             语义是：
             - `symbolName = "lora"`
             - `mutableWeightsFilePath = /var/mobile/ajax/adapter.weights.bin`
             - `modelBundlePath = /var/mobile/ajax/model.bundle`
          4. 随后它会用：
             `TGIModelConfigurationObjC.initWithModelType:modelBundlePath:e5Functions:adapterConfigurations:`
             生成 model config，
             再进入
             `loadRunner(...)`
          5. 因而
             `/var/mobile/ajax/*`
             这一对路径
             当前是
             `loadAsset`
             消费面上的真实 contract，
             不是仅仅出现在日志或注释里的残留
          5.5 当前更合理的分层解释是：
             - `AppAssetManager.copyAssetsIfNeeded(...)`
               负责
               internal cache/temp tree
             - `loadAsset(...)`
               负责消费
               `/var/mobile/ajax/*`
             - 中间仍然缺一条
               publish / materialize
               桥
          6. `loadAsset`
             /
             `createInferenceContext`
             /
             `unloadAsset`
             /
             `countTokens`
             之间的 override getter
             当前 machine-local 映射已进一步收紧：
             - `off_29E2641D0`
               = `modelPath`
               -> fallback
               `/var/mobile/ajax/model.bundle`
             - `off_29E2641D8`
               = `adapterPath`
               -> fallback
               `/var/mobile/ajax/adapter.weights.bin`
             - `off_29E2641E0`
               = `mutableWeightSymbolName`
               -> fallback
               `"lora"`
             - `off_29E2641E8`
               = `tokenizerPath`
               -> fallback
               `/var/mobile/ajax/tokenizer`
             - `off_29E264200`
               = `draftModelPath`
               -> fallback
               `/var/mobile/ajax/draftModel.bundle`
          6.5 `createInferenceContext(...)`
             (`0x27512a0a0`)
             的 machine-local 控制流也已收紧：
             - 它会先从
               `OnDeviceInferenceOverrides`
               读取：
               - `modelPath`
               - `tokenizerPath`
               - `draftModelPath`
             - 如果 getter 返回 `nil`，
               才分别回退到：
               - `/var/mobile/ajax/model.bundle`
               - `/var/mobile/ajax/tokenizer`
               - `/var/mobile/ajax/draftModel.bundle`
             - 随后直接对这些 target path
               做
               `NSFileManager.defaultManager.fileExistsAtPath:`
               检查
             - 缺失项不会在这里直接 copy/publish；
               而是被收集后下沉到：
               `AssetRepository.fetchAssetObjects(identifiers:configuration:)`
             - 这说明：
               `createInferenceContext`
               本身不是
               internal cache tree
               -> `/var/mobile/ajax/*`
               的 writer；
               它只是
               consumer-side
               的 default-path selector
               + missing-asset fetch trigger
          6.6 `loadAsset TY0`
             (`0x275151754`)
             与
             `loadAsset TY5`
             (`0x27515286c`)
             也补上了更细一层的消费语义：
             - `TY0`
               会读取：
               `adapterPath`
               /
               `mutableWeightSymbolName`
               /
               `modelPath`
             - 若 adapter path 不存在，
               就不会构造
               `TGIAdapterConfigurationObjC`
             - 若存在，
               则会用：
               `adapterType`
               + `symbolName`
               + `mutableWeightsFilePath`
               组装
               `TGIAdapterConfigurationObjC`
             - `TY5`
               会读取：
               `draftModelPath`
               并在缺省时回退
               `/var/mobile/ajax/draftModel.bundle`
             - 因而
               `/var/mobile/ajax/*`
               现在更像
               provider/runtime
               的 fallback contract，
               而不是已经确认的唯一 materialization 目标
          6.7 `handleCustomAsset TY2`
             (`0x275103f50`)
             调
             `handleDraftModel(...)`
             时，
             签名里已经带着
             `explicitBundleFileURL`
             参数；
             当前 call-site
             (`0x2751047e4`-`0x275104820`)
             没有出现
             `/var/mobile/ajax/*`
             字面量。
             这进一步支持：
             draft model
             path
             可以由上游显式注入，
             不一定只能走
             `/var/mobile/ajax/draftModel.bundle`
          6.8 `LanguageModelLoader.findURLOfKnown*Asset(...)`
             这层又补出了一条更强的
             internal-path
             证据：
             - `findURLOfKnownModelAsset(in:source:)`
               (`0x2751adf00`)
               当前会在给定 base URL
               下按顺序探测：
               - `model.bundle`
               - `model.mil`
               - `model.mlir.bc`
               - `model.mlir`
             - `findURLOfKnownAdapterAsset(in:source:)`
               (`0x2751ae1bc`)
               当前会在给定 base URL
               下按顺序探测：
               - `lora.part.bin`
               - `adapter.mlir.bc`
               - `adapter.mlir`
             - 其中
               `lora.part.bin`
               与此前已确认的
               `AppAssetManager.adapterWeightsFileName`
               完全一致
             - 这些 known-asset
               URL finder
               当前 machine-local caller
               已确认至少包括：
               - `handleLLMModel(...)`
               - `handleLLMAdapter(...)`
               - `handleImageTokenizer(...)`
               - `handleDraftModel(...)`
             - 因而：
               `TokenGenerationInference`
               内部已经存在一条
               “直接在某个 base URL
               下查找 internal cache
               / compiled artifact
               文件名”
               的消费链；
               它不依赖先把文件 rename /
               publish 成
               `/var/mobile/ajax/model.bundle`
               /
               `/var/mobile/ajax/adapter.weights.bin`
          6.9 `handleLLMAdapter(...)`
             的 machine-local
             实参槽位也补上了一层：
             - wrapper stub
               (`0x2750fe7d4`)
               会把：
               - `a1 -> 0x7B0`
               - `a2 -> 0x7B8`
               - `a3 -> 0x7C0`
               - `a4 -> 0x7C8`
               - `a5 -> 0x7D8`
               存进 async state
             - 后续
               `handleLLMAdapter TY0`
               在
               `0x2750ff1a4`
               读取
               `[state + 0x7C8]`
               并作为
               `findURLOfKnownAdapterAsset(...)`
               的 `in:` base URL
             - 这说明：
               known-asset discovery
               的 base URL
               当前是沿
               `handleLLMAdapter`
               的显式入参链传下来的，
               不是从
               `/var/mobile/ajax/*`
               fallback
               倒推出来的
             - 更细一层的 call-site
               形态也已收紧为：
               1. `loadAsset dispatcher`
                  (`0x27510f220`-`0x27510f268`)
                  把：
                  - `X0 = self`
                  - `X3 = X27`
                  - `X4 = X21`
                  喂进
                  `handleLLMAdapter(...)`
                  ，且其中
                  `X3`
                  后续落到
                  `[state + 0x7C8]`
               2. `handleCustom TY0`
                  (`0x275103dbc`-`0x275103e04`)
                  把：
                  - `X0 = self`
                  - `X3 = [SP + var_78]`
                  - `X4 = X21`
                  喂进
                  `handleLLMAdapter(...)`
               3. `handleCustom`
                  在调用前，
                  还会先记录：
                  `Loading custom adapter from: %{public}s`
                  这类 path/url
                  相关日志；
                  因而
                  `X3 -> [state + 0x7C8]`
                  当前最可信语义
                  已可收紧成：
                  “known adapter asset
                  lookup 的目录 URL / base URL”
          6.10 `loadAsset` 标准路径里
             `X27`
             的真实来源
             也已补上一层，
             且它不是
             “先 publish 成
             `/var/mobile/ajax/*`
             再回读”：
             - `0x27510daa4`
               会把
               `[SP + var_80]`
               重新装回
               `X27`
             - 这个值随后被直接作为
               `identifier`
               传给：
               `OnDeviceInferenceProviderDataSource.catalogResource(for:)`
               (`0x27510dab0`)
             - `catalogResource(for:)`
               成功后，
               `loadAsset`
               在
               `0x27510dbb0`
               以后分配
               `Asset`
               存储，
               保留原
               identifier
               到
               `X25`，
               再在
               `0x27510dc24`
               调：
               `OnDeviceInferenceProviderDataSource.asset(for:)`
               (`0x27517a558`)
             - 该调用使用
               Swift indirect-result
               约定把返回的
               `Asset`
               直接写进 caller
               提供的 buffer
               (`X8` / `X24`)；
               这就是后续在
               `loadAsset`
               内被沿用的
               `Asset`
               值对象
             - `ProviderDataSource.asset(for:)`
               自身也会再次调
               `catalogResource(for:)`
               (`0x27517a68c`)，
               并要求资源能被视为
               `AssetBackedResource`
               (`0x27517a710`)
             - 在成功路径里，
               `asset(for:)`
               会把最终导出的
               `Asset`
               字段写回 caller
               buffer
               (`0x27517aaf4`)
             - 因而：
               `loadAsset`
               标准路径里，
               `ProviderDataSource.asset(for:)`
               先产出的是
               `Asset`
               值对象；
               这一步发生在
               `handleLLMModel`
               /
               `handleTokenizer`
               /
               adapter 分发之前
             - 但 machine-local
               新证据也表明：
               到
               `handleLLMAdapter TY0`
               真正消费时，
               `[state + 0x7C8]`
               已经按
               `Foundation.URL?`
               的 ABI
               被读出，
               并在
               `0x2750ff1a4`-
               `0x2750ff1fc`
               直接喂给
               `findURLOfKnownAdapterAsset(...)`
             - 这说明：
               标准路径在
               `asset(for:)`
               之后、
               `handleLLMAdapter(...)`
               之前，
               还存在一层
               `Asset -> URL?`
               lowering；
               当前尚未锁死的
               正是这一步
             - 这与
               `handleCustom`
               路径在
               `0x275103a2c`
               之后把
               `AppAssetManager.cacheDirectory`
               写进上游对象的做法
               形成对应：
               两条路径当前更像是
               “都先准备带有
               root 信息的上游对象，
               再在 adapter 分发前
               lowering 成
               `Foundation.URL?`”
             - 尚未完全锁死的
               只剩最后一层：
               标准路径与 custom
               路各自是在哪一步，
               把上游对象降成
               `handleLLMAdapter(a4)`
               所见的
               `Foundation.URL?`
          6.11 `Asset`
             的 machine-local
             反射信息也已补出，
             纠正了此前对
             `handleLLMAdapter`
             实参槽位的过度简化：
             - `Asset`
               的 field metadata
               (`0x275244c1c`)
               当前可直接解出
               两个字段名：
               - `url`
               - `version`
             - 第一条字段类型
               typeref
               也已对上：
               `0x27523d4d6`
               ->
               `_symbolic _____ 10Foundation3URLV`
             - 第二条字段名
               `version`
               当前已解到
               `__swift5_reflstr`
               (`0x275241a10`)
             - `handleCustom`
               在
               `0x275103a28`-
               `0x275103a98`
               的构造
               也与此吻合：
               先把
               `cacheDirectory`
               相关值写到
               `Asset`
               的前一组字段，
               再把另一组值
               写到
               field-offset
               指向的位置
             - 更关键的是：
               `handleLLMAdapter`
               的 wrapper stub
               不能再按
               “五个业务参数
               一一对应”
               去理解，
               因为：
               1. `identifier: String`
                  在 call-site
                  上已可直接看出
                  占
                  `X1 / X2`
                  两个 machine words
               2. `asset: Asset`
                  也不是单寄存器，
                  而是按字段拆成
                  多个 machine words；
                  当前至少已能看到
                  它会继续占用
                  `X3 / X4 / X20`
               3. 当前 wrapper
                  保存的是：
                  - `[7B8]`
                  - `[7C0]`
                  - `[7C8]`
                  - `[7D0]`
                  - `[7D8]`
                  这几段连续槽位，
                  更准确地说
                  是
                  `identifier`
                  +
                  `asset`
                  的 ABI 展开结果
             - 因而：
               `handleLLMAdapter TY0`
               中的
               `[state + 0x7C8]`
               不能再直接解释成
               “原始 a4
               就是 URL”
               ；更准确的表述是：
               它是
               `asset: Asset`
               ABI 展开后的其中一段，
               而这段在
               `0x2750ff1a4`-
               `0x2750ff1fc`
               被当成
               `Foundation.URL?`
               传给
               `findURLOfKnownAdapterAsset(...)`
             - 当前最佳解释已可进一步收紧为：
               - `[7B8] / [7C0]`
                 更像
                 `identifier: String`
                 的两段
               - `[7C8] / [7D0] / [7D8]`
                 更像
                 `asset`
                 的展开部分
               - 其中
                 `[7C8]`
                 明确参与
                 `asset.url`
                 的
                 `Foundation.URL?`
                 传参
               - 而
                 `[7D8]`
                 在多处报错路径里
                 被当成另一组
                 可打印值消费，
                 当前更像
                 `asset.version`
             - 偏移这层也补了一条
               更准确的纠偏：
               - `ProviderDataSource.asset(for:)`
                 在
                 `0x27517aaf0`
                 用
                 `LDRSW X8, [X0,#0x14]`
                 取第二字段 offset
               - `handleCustom`
                 看起来像在
                 `0x275103a90`
                 用
                 `LDRSW X8, [X19,#0x1C]`
                 取 offset
               - 但它前面紧接着有
                 `LDR X16, [X19,#-8]!`
                 的写回，
                 所以此时
                 `X19`
                 已回退了
                 8 字节；
                 `#0x1C`
                 的有效地址
                 实际仍对齐到
                 原 metadata
                 基址的
                 `+0x14`
               - 因而：
                 当前看到的
                 并不是
                 `#0x14`
                 vs
                 `#0x1C`
                 两套冲突 offset，
                 而是同一条
                 second-field offset
                 读取逻辑
             - 另外，
               `Asset?`
               getter 侧的 machine-local
               模式也更清楚了：
               - `AssetObjectTokenizer.asset`
                 (`0x27505bad8`)
                 走的是
                 `*(int *)(metadata + 20)`
                 /
                 `#0x14`
               - `AssetObjectImageTokenizer.asset`
                 (`0x27505ba90`)
                 走的是
                 `*(int *)(metadata + 24)`
                 /
                 `#0x18`
               - 这说明：
                 optional `Asset?`
                 的 payload offset
                 也不是全局常数，
                 而是要跟着
                 具体 metadata
                 头布局来读
             - 2026-06-16 新增的
               machine-local ABI
               纠偏：
               1. `handleCustom TY0`
                  最终不是把
                  `Asset`
                  拆成多个业务寄存器
                  传给
                  `handleLLMAdapter`
                  ；它先在
                  `0x2751039fc`-
                  `0x275103a98`
                  分配并填好
                  `Asset`
                  buffer
                  (`X26`)
                  ，再在
                  `0x275103b74`
                  把这个
                  buffer 指针
                  存到
                  `[SP + var_78]`
                  ，最后
                  `0x275103dd0`
                  用
                  `X3 = [SP + var_78]`
                  调
                  `handleLLMAdapter(...)`
               2. `loadAsset`
                  标准路径也一致：
                  `0x27510dbc4`-
                  `0x27510dc24`
                  先分配
                  caller-owned
                  `Asset`
                  buffer
                  (`X27`)
                  并通过
                  `ProviderDataSource.asset(for:)`
                  直接写满，
                  最后
                  `0x27510f234`
                  用
                  `X3 = X27`
                  调
                  `handleLLMAdapter(...)`
               3. 因而：
                  `wrapper`
                  中
                  `X3 -> [state + 0x7C8]`
                  当前最准确的语义
                  不是
                  “裸 URL word”
                  ，也不是
                  “`asset`
                  的寄存器展开第一段”，
                  而是：
                  “指向
                  `Asset`
                  存储起始地址的
                  间接指针”
               4. 这也解释了
                  为什么
                  `handleLLMAdapter TY0`
                  在
                  `0x2750ff1a4`-
                  `0x2750ff1fc`
                  只需从
                  `[state + 0x7C8]`
                  取值，
                  就能把它当作
                  `findURLOfKnownAdapterAsset(in:...)`
                  的
                  `Foundation.URL?`
                  基址来消费：
                  因为
                  `Asset.url`
                  就是第一字段
               5. 因此上一版
                  “`asset`
                  继续占
                  `[7C8]/[7D0]/[7D8]`”
                  的口径
                  应视为
                  已证伪；
                  当前更稳的表述改成：
                  - `[7B8]/[7C0]`
                    仍最像
                    `identifier: String`
                  - `[7C8]`
                    是
                    `Asset`
                    存储起始地址
                    / 间接 URL 基址
                  - `[7D0]`
                    与 `[7D8]`
                    暂时不要再解释成
                    `asset.version`
                    或
                    `asset`
                    剩余 field words
               6. 2026-06-16
                  新增的更硬 ABI
                  证据是：
                  `findURLOfKnownAdapterAsset`
                  (`0x2751ae1bc`)
                  与
                  `findURLOfKnownModelAsset`
                  (`0x2751adf00`)
                  自身都解成了
                  Swift indirect-result
                  lowering
                  - decompile
                    形态都是：
                    `@<X0>(char *a1@<X8>)`
                  - 即：
                    返回的
                    `Foundation.URL?`
                    不是直接寄存器返回，
                    而是通过
                    `X8`
                    提供的
                    by-address
                    result buffer
                  - 这与
                    `handleLLMAdapter TY0`
                    在
                    `0x2750ff1ec`-
                    `0x2750ff1fc`
                    的调用形态
                    完全吻合：
                    先
                    `MOV X8, X24`
                    ，再
                    `BL findURLOfKnownAdapterAsset`
               7. 因而当前口径
                  还可再收紧一步：
                  `[7C8]`
                  不是
                  “把 URL?
                  值本身塞进寄存器”，
                  而是
                  “提供给
                  known-asset finder
                  的
                  `Asset.url`
                  间接存储基址”
               8. 2026-06-16
                  对
                  `[7D0]`
                  的 caller /
                  peer-wrapper
                  对照也已把它
                  基本排出
                  `Asset`
                  字段集合：
                  - `handleCustom`
                    的 async wrapper
                    (`0x27510293c`)
                    会把
                    `X20`
                    存到
                    `[ctx + 0xE8]`
                  - `loadAsset`
                    的 async wrapper
                    (`0x27510d444`)
                    会把
                    hidden `X20`
                    存到
                    `[ctx + 0x430]`
                  - 同型对照
                    `handleDraftModel`
                    wrapper
                    (`0x275107674`)
                    也一样：
                    - `X20 -> [0x440]`
                    - 显式业务参数
                      依次走
                      `X0..X5`
                  - 而
                    `handleLLMAdapter`
                    wrapper
                    正对应：
                    `X20 -> [0x7D0]`
                  - 再看
                    `handleLLMAdapter TY2`
                    (`0x2751020b8`-
                    `0x2751020c8`)
                    时，
                    state 上的
                    `[0xD8]/[0xE8]`
                    被整块搬进
                    runner/object
                    continuation，
                    与
                    `hidden async context`
                    的模式一致
               9. 2026-06-16 19:26
                  新增的 ABI / call-site
                  证据把
                  `[7D8]`
                  的范围继续收紧了：
                  - `handleCustom`
                    wrapper
                    不是实例方法 wrapper，
                    而是
                    local async helper
                    wrapper；
                    `template: ModelCatalog.AssetBackedLLMAdapter`
                    只占
                    `a2/a3`
                    两个 machine words，
                    并被保存到
                    `[0xE0]/[0xF0]`
                  - `handleCustom TY0`
                    在尾调
                    `handleLLMAdapter(...)`
                    前，
                    会先通过
                    `j__$...TW_598(0)`
                    取一个 imported type metadata，
                    再按其 value-witness
                    `+0x40`
                    动态分配 buffer
                    (`0x275103d18`-
                    `0x275103d88`)
                    ，最后把该 buffer
                    指针放进
                    `X4`
                  - `loadAsset TY0`
                    的尾调
                    也完全同型：
                    `a3`
                    先被存进
                    `[0x438]`，
                    失败路径里再取回
                    `LDR X19, [X22,#0x438]`
                    并喂给
                    同一个 helper
                    `j__$...TW_1400`
                    (`0x27510ef34`-
                    `0x27510ef78`)
                  - `handleLLMAdapter TY0`
                    / `TY3`
                    的失败路径也同型：
                    `LDR X22/X20, [state + 0x7D8]`
                    后，
                    与
                    `ModelManagerServices.InferenceError`
                    相关 imported witness
                    一起调用
                    `j__$...TW_1400`
                    (`0x2750fecc8`-
                    `0x2750fed0c`,
                    `0x2751016a8`-
                    `0x2751016ec`,
                    `0x275102744`-
                    `0x275102788`)
               10. 因而当前对
                   `[7D8] = X4`
                   的最佳解释
                   已更新为：
                   - 它不是
                     `asset.version`
                     ，也不是
                     `Asset`
                     剩余 field word
                   - 它更像
                     `async throws(ModelManagerServices.InferenceError)`
                     lowering
                     里的
                     typed error/result
                     storage
                     指针
                   - 这也解释了
                     为什么
                     `[7D8]`
                     在多个失败路径里
                     都被当成
                     某种
                     `InferenceError`
                     目标地址
                     来写入，
                     而不是被当成
                     URL / String /
                     Asset field
                     直接消费
                   - 2026-06-16
                     还新增了一条
                     本机 Swift ABI
                     对照证据：
                     用最小样例
                     `async throws(E)`
                     /
                     `any P`
                     /
                     local async helper
                     编出的
                     arm64 汇编
                     明确显示：
                     - entry ABI
                       的第 5 个
                       machine argument
                       就是
                       typed error
                       storage 槽
                     - throw 路径会先
                       组装
                       `E`
                       payload，
                       再经
                       `swift_willThrowTyped`
                       把整个
                       typed error
                       写回该槽
                     - 对照文件：
                       `/tmp/swiftabi.8d32iQ/sample.swift`
                       生成的
                       `/tmp/swiftabi.8d32iQ/sample.s`
                     - 其中最关键的
                       machine-level
                       对照是：
                       `Repo.handle`
                       entry
                       `str x4, [x22, #216]`
                       与后续
                       throw path
                       把
                       `E`
                       拷回该槽；
                       这与
                     `handleLLMAdapter`
                     wrapper
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
                   - 2026-06-16
                     进一步新增的
                     目标内横向证据是：
                     - `handleTokenizer`
                       失败路径
                       也会在
                       `0x2750fcbb4`-
                       `0x2750fcbe0`
                       先装
                       `InferenceError`
                       metadata / witness，
                       再走同一类
                       `_1400`
                       helper
                     - `handleImageTokenizer`
                       失败路径
                       也同型：
                       `0x275106640`-
                       `0x275106670`
                   - 因而
                     `_1400`
                     现在更像
                     模块内生成的
                     `swift_willThrowTyped`
                     风格 helper，
                     负责把已经构造好的
                     typed error
                     写回
                     `[7D8]`
                     一类 error storage；
                     它不像
                     `InferenceError`
                     case constructor，
                     因为调用时
                     没有传入
                     业务字符串 /
                     code /
                     userInfo
                     等上下文参数
                   - 2026-06-16
                     新增的链接层事实也支持这一点：
                     - `TokenGenerationInference`
                       自身只显式导入
                       `_swift_willThrowTypedImpl`
                       ，没有直接导入
                       `swift_willThrowTyped`
                       顶层包装层
                     - `ModelManagerServices`
                       本体也同样只显式导入
                       `_swift_willThrowTypedImpl`
                   - 结合本机 Swift ABI
                     对照，
                     当前最佳解释是：
                     `_1400`
                     不是业务
                     `InferenceError`
                     构造器，
                     而是该模块自己生成的
                     typed-throws
                     辅助包装层，
                     位于
                     case / payload
                     已构造完成
                     与
                     `_swift_willThrowTypedImpl`
                     之间
                   - 2026-06-16
                     21:08
                     新增的
                     `ModelManagerServices`
                     官方同型样本
                     已把这条解释再收紧一层：
                     1.
                     `ModelManagerServices`
                     本体里
                     `_swift_willThrowTyped`
                     (`0x25a724dd4`)
                     的真实代码
                     已确认是一个
                     很薄的 3 参 wrapper：
                     - `X0`
                       = typed error
                       storage / result slot
                     - `X1`
                       = 已构造好的
                       error payload
                     - `X2`
                       = `Error`
                       witness table
                     - 仅先做一次
                       OS/version gate
                       (`0x25a771e38`)
                       ，通过后直接
                       `bl`
                       `_swift_willThrowTypedImpl`
                     2.
                     这个 3 参形状
                     也与本机最小 Swift
                     样本完全一致：
                     `/tmp/swiftabi.8d32iQ/sample.s`
                     /
                     `sample_nested.s`
                     /
                     `sample_capture_self.s`
                     里，
                     调用序列都是：
                     - `x0 = error storage`
                     - `x1 = payload addr`
                     - `x2 = Error witness`
                     - `bl _swift_willThrowTyped`
                     3.
                     `TokenGenerationInference`
                     里多个
                     `_1400`
                     callsite
                     现在已经能与此
                     一一并列：
                     - 例如
                       `0x275143324`-
                       `0x275143330`
                       /
                       `0x27517d1f8`-
                       `0x27517d204`
                       /
                       `0x2750fcbec`-
                       `0x2750fcbf4`
                     - 统一都是
                       先
                       `bl _$s20ModelManagerServices14InferenceErrorOACs0E0AAWlTm`
                       取
                       `InferenceError : Error`
                       witness accessor
                     - 再把
                       `X0 = [7D8]`-family
                       error storage，
                       `X1 = 已构造好的 payload addr`，
                       `X2 = witness`
                       送进
                       `_1400`
                     - 调用后紧跟的
                       仍是资源释放 /
                       wrapper epilogue，
                       而不是继续拼装业务错误字段
                   - 因而当前可以把
                     `_1400`
                     从
                     “高概率 /
                     最佳解释”
                     升级成：
                     “与
                     `ModelManagerServices::_swift_willThrowTyped`
                     同型的
                     模块内
                     typed-throws
                     包装层”
                     ；当前剩下未锁死的
                     只是它更细的
                     私有符号名，
                     不是语义方向
                   - 2026-06-16
                     21:26
                     进一步把
                     `_1400`
                     的 stub 位置
                     压到了具体页级：
                     1.
                     它在
                     `__TEXT,__auth_stubs`
                     里的索引是
                     `1402`
                     ，对应
                     `0x275218a38`
                     2.
                     该 stub 的
                     `adrp/add`
                     解析结果是：
                     - `x17 -> 0x29a246000`
                     - `add #0x270`
                     - 最终指向
                       `0x29a246270`
                     3.
                     这个页簇里
                     `0x29a246208` /
                     `0x29a246270` /
                     `0x29a246358`
                     等槽位在旧间接符号表里
                     全都塌成同一个
                     占位符：
                     `_$s24TokenGenerationInference16DraftingBehaviorV10CodingKeys...TW`
                     4.
                     因而从当前
                     extracted Mach-O 的
                     旧 indirect symbol table
                     继续追
                     `_1400`
                     的更细真实名字
                     已基本进入
                     低收益区；
                     当前更有价值的是：
                     - 继续把该页簇里
                       不同 index 的
                       同型 stub
                       做行为归类
                     - 或转去追
                       `__AUTH_CONST/__auth_got`
                       和
                       `dyld_info -fixup_chains`
                       能否给出更细的
                       target family
                   - 这也说明
                     当前 `_1400`
                     的真正阻塞点
                     不是“它是不是
                     typed-throws wrapper”，
                     而是“从这个占位簇里
                     能否恢复出更细的
                     私有符号身份”
                   - 2026-06-16
                     21:51
                     起，
                     对同页簇
                     `1399/1400/1401`
                     的职责已经能稳定拆开：
                     1.
                     `j__..._1399`
                     (`0x275218a28`)
                     不应再和
                     `_1400`
                     混看。
                     它的调用族
                     主要出现在：
                     - `TGICAPIWrapper.makeSession`
                     - `AppAssetManager.createCacheDirectoryIfNeeded`
                     - `OnDeviceInferenceContextFactory.createInferenceContext`
                     等普通
                     `throws`
                     路径，
                     调用形状是：
                     - 先构造一个
                       普通 `Error`
                       object /
                       existential
                     - 再只传
                       `x0 = error`
                       进入
                       `1399`
                     - 之后直接走
                       `return / unwind`
                   结合本机最小
                   untyped `throws`
                   样本
                   (`/tmp/swiftthrow.Yvf6HP/sample_throw.s`)
                   中
                   `_swift_willThrow`
                   的一参形状，
                    当前最稳应写成：
                    “`_swift_willThrow`
                    家族的
                    untyped throw
                    入口”
                   - 2026-06-16
                     22:42
                     当时的
                     “导入表里没有
                     `_swift_willThrow`”
                     这一句
                     现已被
                     `nm -m`
                     纠正，
                     不能再保留
                   - 2026-06-16
                     23:00
                     以
                     `nm -m`
                     为准，
                     `TokenGenerationInference`
                     确实直接导入了：
                     - `_swift_willThrow`
                     - `_swift_willThrowTypedImpl`
                     因而当前关于
                     `1399`
                     的最稳写法应更新为：
                     “与 imported
                     `_swift_willThrow`
                     同家族的
                     untyped throw
                     入口”
                     至于它到底是
                     直接薄跳板
                     还是模块内再包一层，
                     在没有更细 stub /
                     fixup 恢复前
                     暂不硬写死
                     2.
                     `j__..._1400`
                     (`0x275218a38`)
                     仍保持前述结论：
                     - 调用前统一准备
                       `x0 = typed error storage`
                       `x1 = payload`
                       `x2 = Error witness`
                     - 与
                       `ModelManagerServices::_swift_willThrowTyped`
                       同型
                     因而应继续写成：
                     typed-throws
                     包装层
                   - 2026-06-16
                     22:36
                     进一步收紧：
                     当前更不应把
                     `_1400`
                     写成
                     “直接指向 imported
                     `_swift_willThrowTypedImpl`”
                     ，而应继续写成：
                     “模块内
                     typed-throws
                     gate/wrapper”
                     原因是：
                     1.
                     `TokenGenerationInference`
                     同时明确导入了：
                     - `_swift_willThrowTypedImpl`
                     - `Swift._stdlib_isOSVersionAtLeastOrVariantVersionAtLeast(...)`
                     2.
                     本机最小
                     typed-throws
                     样本里，
                     `_swift_willThrowTyped`
                     的结构正是：
                     - 先做 stdlib OS gate
                     - 再 tailcall
                       `_swift_willThrowTypedImpl`
                     3.
                     `_1400`
                     的 callsite
                     仍然统一是
                     `(storage,payload,witness)`
                     三参形状；
                     从外部调用协议看，
                     它更像
                     “对外暴露的 wrapper 入口”
                   - 因而当前关于
                     `_1400`
                     的最稳写法应更新为：
                     “模块内
                     typed-throws
                     gate/wrapper，
                     最终下沉到
                     `_swift_willThrowTypedImpl`”
                     3.
                     `j__..._1401`
                     (`0x275218a48`)
                     已经拿到反例样本：
                     `specialized Array<Float>.sampleRandomElement(...)`
                     里，
                     它被当作
                     数值数组变换 helper
                     使用，
                     典型调用形状是：
                     `dst/src/count/...`
                     这一类多参数值操作，
                     明显不是错误路径。
                     因而不能因为它和
                     `_1400`
                     同页、
                     同占位簇，
                     就把它也归入
                     throw helper
                     家族
                   - 2026-06-16
                     22:50
                     又补齐了：
                     `1402/1403`
                     也更像
                     非错误路径的
                     数值/vector helper
                     （调用点集中在
                     `sampleRandomElement`
                     一类数值处理路径），
                     进一步说明：
                     这一页簇只是
                     多种薄 wrapper
                     在 cache/import
                     布局上挤在一起，
                     不是
                     “整页都是 throw-family”
                   - 所以当前对这一页簇
                     最稳的总结合是：
                     - `1399`
                       = 与 imported
                       `_swift_willThrow`
                       同家族的
                       untyped throw
                       入口
                     - `1400`
                       = 模块内
                       typed-throws
                       gate/wrapper
                     - `1401/1402/1403`
                       = 非错误路径的
                       数值 helper
                     也就是说，
                     “同页簇”
                     只说明它们共享
                     cache / import 布局，
                     不说明语义同类
                   - 2026-06-16
                     23:19
                     当前还能再提出一个
                     更结构化的
                     working model：
                     - `1306`
                       (`0x275218458`)
                       很像
                       “先分配 /
                       初始化错误对象，
                       再返回
                       `(error, payload-slot)`
                       二元组”
                       的模板入口
                     - `1397/1398`
                       (`0x275218a08/18`)
                       目前从调用点看，
                       更像对
                       这个二元组
                       做额外字段写入 /
                       轻量初始化
                       的 helper
                     - `1399`
                       消费普通
                       `Error`
                       路径
                     - `1400`
                       消费
                       typed error
                       路径
                   - 这个模型的价值在于：
                     它把
                     `1399/1400`
                     从“两个孤立 stub”
                     提升成
                     “同一套错误构造模板的
                     两个收尾位点”
                   - 但当前仍缺
                     `1397/1398`
                     的更细反编译 /
                     fixup 恢复，
                     所以这一层
                     暂时只写成
                     working model，
                     不写成已证实事实
                   - 2026-06-16
                     23:47
                     继续补
                     `1397/1398`
                     汇编级调用形状后，
                     上面的
                     working model
                     可以部分推翻：
                     1.
                     `1398`
                     (`0x275218a18`)
                     在
                     `0x275168340`
                     的直接形状是：
                     - 先
                       `ADD X0, X20, #0x10`
                     - 再
                       `BL 1398`
                     - 紧跟
                       `CBZ X0`
                     这与
                     `swift_weakLoadStrong`
                     一类
                     “从 weak slot
                     取 strong object，
                     失败则返回 nil”
                     的 ABI
                     高度一致；
                     且当前 image
                     确实导入了
                     `_swift_weakLoadStrong`
                   2.
                     `1397`
                     (`0x275218a08`)
                     在
                     `0x2750c12bc`
                     /
                     `0x2750c15bc`
                     的直接形状是：
                     - `ADD X0, Xobj, #0x18`
                     - `MOV X1, #0`
                       或
                       `MOV X1, X25`
                     - `BL 1397`
                     这与
                     `swift_weakInit`
                     一类
                     “对 weak slot
                     做 nil / object
                     初始化”
                     的 ABI
                     高度一致；
                     当前 image
                     也确实导入了
                     `_swift_weakInit`
                   3.
                     因此，
                     `1397/1398`
                     不应再继续
                     放在
                     `1306 -> ... -> 1399/1400`
                     的错误构造模板里理解；
                     它们更像
                     同一组
                     weak-reference
                     生命周期 helper
                   4.
                     当前更稳的分层应改成：
                     - `1397/1398`
                       = weak helper
                       语义簇
                     - `1399`
                       = 与 imported
                       `_swift_willThrow`
                       同家族的
                       untyped throw
                       入口
                     - `1400`
                       = 模块内
                       typed-throws
                       gate/wrapper
                   5.
                     所以旧的
                     “`1306 + 1397/1398 + 1399/1400`
                     是一整套错误模板”
                     现在只能保留成
                     已证伪的旧假设，
                     不能再作为
                     当前主结论
                   6.
                     当前还未完全收紧的点：
                     - `1397/1398`
                       到底是
                       direct imported stub
                       还是模块内薄 wrapper
                     - `1395`
                       在同一 weak-slot
                       族里的具体分工
                     - `1306 -> 293 -> 1399`
                       这条
                       真正错误下沉链
                       里的
                       `1306/293`
                       语义
                   - 2026-06-16
                     23:52
                     再补
                     `1395/1316`
                     后，
                     当前还能再收紧一层：
                     1.
                     `1395`
                     (`0x2752189e8`)
                     在
                     `0x2750c1300`
                     /
                     `0x2750c15f8`
                     的直接形状是：
                     - `ADD X0, Xobj, #0x18`
                     - `MOV X1, #0`
                       或
                       `MOV X1, X25`
                     - `BL 1395`
                     这与
                     `swift_weakAssign`
                     的二参 ABI
                     高度一致；
                     且当前 image
                     确实导入了
                     `_swift_weakAssign`
                   2.
                     `1397`
                     和
                     `1395`
                     因而更像一对：
                     - `1397`
                       = weakInit
                     - `1395`
                       = weakAssign
                   3.
                     `1316`
                     (`0x2752184f8`)
                     当前不宜再放进
                     weak helper
                     小簇里理解：
                     - xref
                       超过
                       500
                       处
                     - 调用点覆盖
                       dictionary /
                       stream /
                       asset /
                       decoder
                       等大量无关路径
                     - 参数形状也跨
                       `x2=0/1/32/33`
                       等多种模式
                     因此它更像
                     通用地址型
                     copy/access
                     helper，
                     暂不当成
                     weak 专用入口
                   4.
                     当前更稳的语义分层
                     已变成：
                     - `1395/1397/1398`
                       = weak-reference
                       生命周期簇
                     - `1316`
                       = 通用
                       address/copy/access
                       簇
                     - `1399/1400`
                       = throw-family
                   - 2026-06-17
                     00:03
                     再往前追
                     `1306 -> 1399`
                     的寄存器形状后，
                     当前还能把
                     `1306`
                     再收紧一层：
                     1.
                     在
                     `0x275097df8`
                     /
                     `0x27512ab80`
                     这类典型样本里，
                     `1306`
                     的入参形状稳定是：
                     - `x0 = 294/296`
                       产出的
                       message / case-side
                       value
                     - `x1 = Error`
                       witness
                     - `x2 = 0`
                     - `w3 = 0`
                   2.
                     `1306`
                     返回后，
                     调用方稳定做：
                     - `x0`
                       保存为
                       最终错误 handle
                     - `x1`
                       作为
                       待填充 payload /
                       object slot
                     - 随后把
                       `x1`
                       传给某个
                       metadata /
                       value-witness
                       函数写入具体内容
                     - 最后再把
                       `x0`
                       送入
                       `1399`
                   3.
                     例如
                     `0x27512ab80`
                    ：
                     - `bl 1306`
                     - `mov x20, x0`
                     - `mov x26, x1`
                     - 后续
                       `mov x0, x1`
                       + `BLRAA`
                       写 payload
                     - 再以
                       `x20`
                       进入
                       throw path
                   4.
                     这说明
                     `1306`
                     现在最稳的工作模型
                     不是
                     “普通 helper”
                     而是：
                     - 为错误路径准备
                       `(error handle, payload slot)`
                       二元组
                     - 其后由调用方
                       写 payload
                     - 再交给
                       `1399`
                       做 untyped throw
                   5.
                     仍未完全证实的点：
                     - `1306`
                       是否最终直达
                       `_swift_allocError`
                     - `293`
                       在这条链里
                       究竟是
                       构造 message /
                       enum case /
                       还是别的
                   - 2026-06-17
                     00:09
                     继续补
                     `293`
                     调用形状后，
                     当前还能再收紧一层：
                     1.
                     `293`
                     并不是所有
                     `1306 -> 1399`
                     路径都必经；
                     当前至少已经看到两类：
                     - A.
                       `1306 -> direct payload write -> 1399`
                       例如
                       `0x275097df8`
                       一类样本
                     - B.
                       `1306 -> 293 -> 1399`
                       例如
                       `0x2751689e0`
                       /
                       `0x275165b70`
                       一类样本
                   2.
                     在 B 类样本里，
                     `293`
                     的入参形状稳定接近：
                     - `x0 = 1306`
                       返回的
                       error handle
                     - `x8 = 1306`
                       返回的
                       payload slot
                     然后才进入
                     `1399`
                   3.
                     因而当前对
                     `293`
                     最稳的工作模型
                     已变成：
                     - 不是 message builder
                       本体
                     - 更像某种
                       payload materializer /
                       finalize helper
                       （把
                       payload slot
                       中的内容
                       绑定进
                       error handle）
                   4.
                     当前 untyped throw
                     主链更稳的写法
                     应改成：
                     - 公共前段：
                       `294/296 -> 1306`
                     - 分叉：
                       a.
                       `payload write -> 1399`
                       b.
                       `293 -> 1399`
                     而不是
                     单一路径
                     `294/296 -> 1306 -> 293 -> 1399`
                   - 2026-06-17
                     00:09
                     继续补
                     `293`
                     /
                     `294/296`
                     调用形状后，
                     当前还可再收紧：
                     1.
                     `1306`
                     的最佳工作模型
                     已可进一步改写成：
                     - 入参更像
                       `error concrete type metadata`
                       +
                       `Error witness`
                     - 返回
                       `(error handle, payload slot)`
                     - 行为越来越像
                       `alloc error box`
                       风格入口
                     当前最典型证据是
                     `0x275097df8`
                     一类路径：
                     `1306`
                     返回后，
                     调用方直接对
                     `x1`
                     所指 slot
                     做 value-witness
                     写入
                   2.
                     `293`
                     也已更像
                     “把已准备好的
                     本地 error value /
                     payload
                     materialize
                     进
                     1306
                     返回的 payload slot”
                     的 helper，
                     而不是
                     简单 message builder
                     本体
                     - 证据：
                       在
                       `0x2751689e0`
                       /
                       `0x275165b70`
                       一类样本里，
                       `293`
                       发生在
                       `1306`
                       之后、
                       `1399`
                       之前，
                       且显式把
                       `x8 = x1(payload slot)`
                       再送入
                       `293`
                   3.
                     与此对应，
                     `0x275097df8`
                     一类样本
                     不走
                     `293`，
                     而是
                     直接调用
                     metadata / value-witness
                     函数
                     把 payload
                     写进 slot，
                     然后
                     `1399`
                   4.
                     所以当前
                     `293`
                     更像：
                     - 某些错误类型的
                       专用 materializer
                       / payload injector
                     而不是
                     所有 untyped throw
                     路径共享的
                     通用步骤
                   5.
                     `294/296`
                     的最佳当前读法
                     也可略收紧：
                     - `294`
                       强烈像
                       “把字符串/负载值
                       写到一个
                       本地 value buffer”
                     - `296`
                       更像
                       “返回后续 error
                       concrete type
                       或相关 payload type
                       metadata”
                     但这两点
                     仍是
                     working model，
                     尚未最终坐实
                   - 2026-06-17
                     00:16
                     再补
                     `295/598`
                     之后，
                     当前还能再收紧一层：
                     1.
                     `598(0)`
                     出现在大量
                     `1400`
                     以及
                     `1306`
                     前后错误路径里，
                     形状高度稳定：
                     - 先
                       `bl 598(0)`
                     - 再取
                       witness /
                       metadata
                     - 随后喂给
                       `1306`
                       或
                       `1400`
                     当前最稳工作模型：
                     `598`
                     更像
                     “concrete error type
                     metadata accessor”
                     或其极薄 wrapper
                   2.
                     `295(0)`
                     更常出现在
                     本地错误值构造开始处：
                     - `bl 295(0)`
                     - 紧接着
                       按返回类型大小
                       `alloca`
                     - 再调用
                       `294`
                       / 其他写入函数
                     当前最稳工作模型：
                     `295`
                     更像
                     “payload / local error value
                     type metadata accessor”
                   3.
                     因而当前
                     `294/295/296/598`
                     的较稳分工
                     可以先写成：
                     - `294`
                       = 往本地 value buffer
                         写 message/string/payload
                     - `295`
                       = 本地 payload /
                         local error value
                         type metadata
                     - `598`
                       = concrete error type
                         metadata
                     - `296`
                       仍待定，
                       但更像
                       untyped 本地 error value /
                       payload aggregate
                       一侧的 type helper，
                       而不像
                       `598`
                       那样稳定充当
                       typed-throw 的
                       concrete error type
                       metadata
                   - 2026-06-17
                     00:28
                     继续补
                     `296`
                     的寄存器形状后，
                     当前还能再收紧一层：
                     1.
                     在典型 untyped 路径
                     `0x275097ddc`
                     里，
                     `296(0)`
                     的返回值会：
                     - 先存到
                       `X21`
                     - 立刻拿去取
                       type metadata
                       的
                       `+[0x68]`
                       槽位
                     - 配合
                       `x0 = payload slot`
                       /
                       `x2 = 296 返回值`
                       做一次
                       value-witness
                       调用
                     之后才
                     `1399`
                   2.
                     而在典型 typed 路径
                     `0x27510327c`
                     里，
                     真正稳定进入
                     `1400`
                     的
                     `x1`
                     来自
                     `598(0)`，
                     不是
                     `296`
                   3.
                     因此，
                     `296`
                     当前最稳工作模型
                     需要改得更谨慎：
                     - 它显然和
                       `TokenGenerationError`
                       的 concrete type /
                       conformance
                       强绑定
                     - 但它不像
                       `598`
                       那样
                       在 typed path
                       中稳定充当
                       `1400`
                       的 `x1`
                     - 所以当前更像
                       “untyped TokenGenerationError
                       一侧的
                       concrete/local error type helper”
                     - 暂时不要再把它
                       写死成
                       纯 payload aggregate helper
                   4.
                     当前
                     `295/296/598`
                     更稳的对照是：
                     - `295`
                       = 本地 payload / local error value
                         type metadata
                     - `296`
                       = `TokenGenerationError`
                         侧的 concrete/local
                         error type helper
                     - `598`
                       = typed / concrete error type
                         metadata
                   5.
                     新证据：
                     `0x275098a48`
                     (`lazy protocol witness table accessor
                     for TokenGenerationError`)
                     在初始化 witness table
                     时
                     直接执行：
                     - `bl 296`
                     - `mov x1, x0`
                     - `mov x0, witness descriptor`
                     - `bl 1358`
                     这说明
                     `296`
                     至少直接参与
                     `TokenGenerationError`
                     的 witness/conformance
                     组装，
                     进一步支持它和
                     `TokenGenerationError`
                     concrete type
                     强绑定
                   6.
                     2026-06-17
                     00:57
                     再加一条
                     Mach-O
                     侧旁证后，
                     这层可以再硬一点：
                     - `nm -m`
                       已确认
                       当前 image
                       直接 import
                       `_$s15TokenGeneration0aB5ErrorOMa`
                       与
                       `_$s20ModelManagerServices14InferenceErrorOMa`
                     - 对应本地
                       witness accessor
                       形状分别是：
                       1.
                       `TokenGenerationError`
                       witness accessor
                       `0x275098a48`
                       走
                       `bl 296 -> bl 1358`
                       组表
                       2.
                       `InferenceError`
                       witness accessor
                       `0x275145e80`
                       /
                       `0x275177864`
                       走
                       `a2(255) -> bl 1358`
                       组表
                     - 因而
                       `296`
                       当前已不仅是
                       “看起来像”
                       `TokenGenerationError`
                       concrete/local type helper，
                       而是与
                       `TokenGenerationError`
                       witness/conformance
                       直接绑定
                   7.
                     2026-06-17
                     01:32
                     再补几类
                     `296`
                     调用点抽样后，
                     当前还能把
                     “是否被别的 untyped
                     error family 复用”
                     再收紧一层：
                     - 已抽样的
                       `296`
                       调用点
                       继续集中在：
                       `ClassificationSampling`
                       /
                       `NucleusSampling`
                       /
                       `TopK`
                       /
                       `ContextFactory`
                       /
                       `handleCustom...`
                       这类本地参数校验 /
                       配置校验 /
                       untyped throw
                       路径
                     - 这些路径最终都回到
                       `_$s15TokenGeneration0aB5ErrorOACs0C0AAWl`
                       或其等价
                       `TokenGenerationError`
                       conformance 链
                     - 当前没有看到
                       `296`
                       像
                       `598`
                       那样跨到
                       `InferenceError`
                       witness accessor
                       一侧
                   8.
                     因而当前最稳说法
                     可以再前进一步：
                     - `296`
                       目前更像
                       `TokenGenerationError`
                       专属或近专属的
                       concrete/local type helper
                     - 至少当前
                       machine-local
                       证据里，
                       还没看到它
                       被别的
                       untyped error family
                       明显复用
                   9.
                     2026-06-17
                     01:51
                     需要对上一条
                     “`296` 没跨到
                     `InferenceError`
                     一侧”
                     做一个更精确的修正：
                     - 新抽样的
                       `296`
                       调用点
                       里，
                       `0x275157824`
                       (`countTokens TY2`)
                       与
                       `0x27516d85c`
                       (`requestStream TY26`)
                       都出现了：
                       1.
                       `bl 296`
                       2.
                       `ADRL X0, _$s15TokenGeneration0aB5ErrorOACs0C0AAWL`
                       3.
                       `X1 = 0x28F664FE8`
                       4.
                       `X2 = 0x28F664FF0`
                       5.
                       `BL 0x275177864`
                       6.
                       `BL 1306`
                     - 这说明，
                       如果只看
                       `0x275177864`
                       被 IDA 命名成
                       `_$s20ModelManagerServices14InferenceErrorOACs0E0AAWlTm_0`，
                       会误以为
                       `296`
                       已经切到
                       `InferenceError`
                       家族。
                     - 但进一步看
                       `0x275177864`
                       /
                       `0x275145e80`
                       的机器体，
                       两者都是同一类
                       lazy witness builder：
                       - `result = *a1`
                       - `if !result { v6 = a2(255); result = 1358(a3, v6); atomic_store(result, a1); }`
                     - 更关键的是，
                       在这些
                       `296`
                       路径里，
                       `a1`
                       明确传的是
                       `TokenGenerationError`
                       的 cache slot
                       (`_$s15TokenGeneration0aB5ErrorOACs0C0AAWL`)，
                       不是
                       `InferenceError`
                       的 cache slot。
                     - 因而当前更稳的说法应改成：
                       1.
                       `296`
                       仍然站在
                       `TokenGenerationError`
                       concrete/type-helper
                       这一侧
                       2.
                       `0x275145e80`
                       /
                       `0x275177864`
                       不能只按
                       符号名
                       解释；
                       它们至少在机器体层面
                       已经表现成
                       由 caller 传入
                       `cache/callback/descriptor`
                       决定具体类型的
                       通用 witness helper
                       或 ICF/共用 thunk
                     - 所以，
                       之前那句
                       “当前没有看到
                       `296`
                       像
                       `598`
                       那样跨到
                       `InferenceError`
                       witness accessor
                       一侧”
                       需要改成：
                       “当前看到的
                       是
                       `296`
                       路径
                       复用了
                       一个被命名成
                       `InferenceError`
                       witness accessor
                       的 helper 机器体，
                       但实参仍然落在
                       `TokenGenerationError`
                       cache/witness
                       一侧”
                   10.
                     当前这条线的
                     剩余未决点
                     已进一步收窄成：
                     - `0x28F664FE8`
                       这一路
                       callback
                       到底是不是
                       `TokenGenerationError`
                       metadata/type
                       accessor
                     - `293`
                       为什么只在
                       一部分
                       `1306 -> 1399`
                       路径里出现，
                       它到底是
                       slot materialize /
                       project /
                       payload finalize
                       里的哪一步
                   11.
                     2026-06-17
                     02:28
                     对
                     extracted
                     `TokenGenerationInference`
                     的
                     `__auth_got`
                     继续补证后，
                     现在可以明确：
                     - 直接读取
                       以下槽位：
                       - `293 -> 0x29e25d4e8`
                       - `296 -> 0x29e25d500`
                       - `598 -> 0x29e25de70`
                       - `1306 -> 0x29e25f490`
                       - `1358 -> 0x29e25f630`
                       - `1399 -> 0x29e25f778`
                       - `1400 -> 0x29e25f780`
                       当前值全部是
                       `0`
                     - 因而这份
                       extracted
                       样本
                       不能靠
                       `__auth_got`
                       实值
                       直接恢复
                       这些 auth stub
                       的真实导入目标
                     - 这解释了
                       为什么：
                       - `dyld_info -fixups`
                         几乎不给
                         有效 target
                       - `otool -s __auth_got`
                         看到的是
                         零填充
                     - 所以后续
                       `293/296/1306/1358/1399`
                       reverse
                       应继续依赖：
                       1.
                       callsite 形态
                       2.
                       上游 framework
                       语义
                       3.
                       imported symbol
                       集合
                       三方交叉
                     - 不要再把
                       这份 extracted
                       `__auth_got`
                       当作可直接取证的
                       binding source
                   12.
                     同一轮里，
                     `293`
                     也比上一轮
                     收紧了一层：
                     - 在
                       `TokenGenerationInference`
                       中，
                       throw-path
                       典型形态仍然是：
                       - `1306`
                         返回后
                         `MOV X8, X1`
                       - 然后
                         `BL 293`
                       - 再
                         `1399`
                       - 见：
                         `0x2751442a4`
                         `0x275165798`
                         `0x2751689ec`
                     - 但在
                       `convertToInferenceError`
                       `0x2750d0990`
                       里，
                       `293`
                       并不在
                       `1399`
                       throw
                       路径上，
                       而是在
                       `TokenGenerationError?`
                       解析 /
                       重物化 /
                       转换
                       分支里出现
                     - 再结合
                       上游
                       `TokenGeneration.framework`
                       本体
                       明确存在
                       `TokenGenerationError.toInferenceError`
                       `0x274de6890`
                       且其本体
                       显式依赖
                       `TokenGenerationErrorOMa`
                       (`0x274de6ac8`)
                     - 当前最强工作假设
                       应更新成：
                       `293`
                       更像
                       `TokenGenerationError`
                       向
                       `InferenceError`
                       侧的
                       rebox / project / convert
                       helper family，
                       而不是泛化
                       `payload finalize`
                   13.
                     2026-06-17
                     02:52
                     再补一轮
                     system dyld
                     视图后，
                     `293`
                     这一结论又能再硬一点：
                     - 用
                       `xcrun dyld_info -no_validate -disassemble`
                       看系统里的
                       `TokenGeneration.framework`
                       本体，
                       现在已经能直接确认：
                       `TokenGenerationError.toInferenceError`
                       不是
                       命名噪声，
                       而是活跃的
                       本体函数
                     - 在该函数的
                       system disassembly
                       中，
                       可以直接看到多处
                       对
                       `_$s20ModelManagerServices14InferenceErrorOACs0E0AAWL`
                       的引用
                       （例如
                       `0x274DE8218`
                       `0x274DE82E0`
                       `0x274DE83D8`
                       `0x274DE8580`
                       `0x274DE86D4`
                       这些热点）
                     - 这说明
                       `toInferenceError`
                       确实在
                       `InferenceError`
                       侧组 witness /
                       case / context，
                       不是单纯做
                       本地字符串格式化
                     - 再结合
                       `TokenGenerationInference`
                       中
                       `293`
                       总是吃
                       `1306`
                       返回的
                       `X1 slot`
                       而不是
                       `X0 handle`
                     - 当前最稳的工作表述
                       可以收紧成：
                       `293`
                       很可能就是
                       “把
                       `TokenGenerationError`
                       侧局部值
                       投影 /
                       rebox /
                       写入
                       `InferenceError`
                       error slot”
                       的 helper family
                     - 还差的最后一跳
                       不是方向问题，
                       而是要把
                       `toInferenceError`
                       的具体
                       switch case
                       与
                       `TokenGenerationInference`
                       中对应的
                       `293`
                       callsite
                       一一回对
                   14.
                     2026-06-17
                     03:31
                     本轮再补了两层更硬的本地事实，
                     但也同时确认了一个新的硬边界：
                     1.
                     `TokenGenerationError.toInferenceError`
                     `0x274de6890`
                     的
                     system dyld
                     视图里，
                     各 case
                     不是各自直接 return
                     `InferenceError`，
                     而是先把
                     payload/context
                     按不同布局写进
                     临时位点，
                     再通过统一尾部
                     (`0x274DE90A0` /
                     `0x274DE90C8`)
                     收尾。
                     多个分支把不同
                     `w2`
                     case tag
                     带进统一尾部，
                     例如：
                     - `0x274DE8488 -> w2 = 1`
                     - `0x274DE82C4 -> w2 = 2`
                     - `0x274DE926C -> w2 = 3`
                     - `0x274DE861C -> w2 = 4`
                     - `0x274DE8E90 -> w2 = 5`
                     - `0x274DE8FC8 -> w2 = 6`
                     - `0x274DE8D94 -> w2 = 7`
                     - `0x274DE8890 -> w2 = 8`
                     - `0x274DE909C -> w2 = 9`
                     - `0x274DE9048 -> w2 = 10`
                     - `0x274DE8C08 -> w2 = 11`
                     - `0x274DE8AA0 -> w2 = 12`
                     - `0x274DE8B58 -> w2 = 13`
                     - `0x274DE8EE4 -> w2 = 14`
                     - `0x274DE8944 -> w2 = 15`
                     - `0x274DE8CC4 -> w2 = 16`
                     - `0x274DE8E3C -> w2 = 17`
                     这进一步支持：
                     `293`
                     更像
                     “把局部
                     TokenGenerationError/payload
                     rebox / project
                     到最终
                     InferenceError slot”
                     的 helper family，
                     而不是简单
                     throw 前 finalize。
                     2.
                     `ModelManagerServices`
                     本体的
                     `__swift5_reflstr`
                     已确认
                     `InferenceError`
                     至少包含以下 case 名：
                     - `notImplemented`
                     - `invalidClientData`
                     - `unsupportedRequestType`
                     - `responseEncodingFailed`
                     - `alreadyLoaded`
                     - `notLoaded`
                     - `loadFailed`
                     - `inferenceFailed`
                     - `operationNotAllowed`
                     - `streamNotFound`
                     - `rateLimited`
                     - `internalError`
                     - `networkError`
                     - `resourcesBusy`
                     - `hostFailed`
                     - `unspecifiedUnderlyingError`
                     - `unrecognizedUnderlyingError`
                     - `xpcError`
                     - `unspecified`
                     - `operationCancelled`
                     - `assetVersionMismatch`
                     - `conversionNotSupported`
                     - `deviceConnectionError`
                     - `versionNotSupported`
                     - `hostError`
                     这给
                     `w2 -> case`
                     的最终映射
                     提供了本机候选全集，
                     但本轮还没有把
                     tag
                     与具体 case
                     一一完全对死。
                     3.
                     对
                     `TokenGenerationInference`
                     extracted Mach-O
                     又确认了一次：
                     `__auth_stubs`
                     的
                     indirect symbol table
                     目前是坏的 /
                     不可信的。
                     `otool -Iv`
                     显示
                     `(__TEXT,__auth_stubs)`
                     1409 个入口
                     大片都错误地映成
                     index 0，
                     也就是同一个
                     `DraftingBehavior...`
                     符号。
                     因而：
                     - 不能把
                       `293/296/598/1306/1399/1400`
                       对应的
                       stub slot
                       直接当成
                       真实 import 名
                     - 这再次说明
                       当前 extracted 样本
                       的
                       GOT / indirect symbol /
                       export 层
                       都不适合作为
                       “外部绑定实锤”来源
                     4.
                     当前最稳的结论保持为：
                     - `598`
                       继续站在
                       `InferenceError`
                       concrete/type side
                     - `296`
                       继续站在
                       `TokenGenerationError`
                       concrete/type side，
                       但可能复用
                       caller-parameterized
                       witness helper 机器体
                     - `293`
                       已比上一轮更接近
                       `TokenGenerationError -> InferenceError`
                       的
                       rebox / convert / slot-write
                       helper，
                       但还差
                       `w2 -> InferenceError case`
                       的最终一一映射
                   15.
                     2026-06-17
                     04:22
                     当前又补上了两套
                     “真实 enum 顺序”
                     的硬证据，
                     但同时也确认了一个很容易误判的点：
                     1.
                     `ModelManagerServices.InferenceError`
                     顶层
                     field descriptor
                     (`0x25a7996b0`)
                     已经成功直接解出
                     25 个 case
                     的真实声明顺序：
                     1. `notImplemented`
                     2. `invalidClientData`
                     3. `unsupportedRequestType`
                     4. `responseEncodingFailed`
                     5. `alreadyLoaded`
                     6. `notLoaded`
                     7. `loadFailed`
                     8. `inferenceFailed`
                     9. `operationNotAllowed`
                     10. `streamNotFound`
                     11. `rateLimited`
                     12. `internalError`
                     13. `networkError`
                     14. `resourcesBusy`
                     15. `hostFailed`
                     16. `unspecifiedUnderlyingError`
                     17. `unrecognizedUnderlyingError`
                     18. `xpcError`
                     19. `unspecified`
                     20. `operationCancelled`
                     21. `assetVersionMismatch`
                     22. `conversionNotSupported`
                     23. `deviceConnectionError`
                     24. `versionNotSupported`
                     25. `hostError`
                     2.
                     `TokenGenerationError.Code`
                     也已经拿到两层硬证据：
                     - `Code.rawValue.getter`
                       `0x274deaa50`
                       直接是
                       `LDRB W0, [X20]`
                     - `Code(rawValue:)`
                       `0x274dea628`
                       用
                       `cmp x0, #0x12`
                       /
                       `csel`
                       证明
                       rawValue
                       是线性
                       `0..17`
                       （越界收敛到
                       `0x12`
                       sentinel）
                     - 对应 field / constructor
                       顺序为：
                       0. `timeout`
                       1. `rateLimited`
                       2. `networkError`
                       3. `tooManyTokens`
                       4. `cancelled`
                       5. `unservicableConfiguration`
                       6. `unknownSpecialToken`
                       7. `invalidGrammar`
                       8. `invalidParameters`
                       9. `toolInvocationFailure`
                       10. `modelExecutionError`
                       11. `documentRegistrationFailure`
                       12. `invalidated`
                       13. `authenticationFailure`
                       14. `safetyViolation`
                       15. `accountError`
                       16. `unsupportedGuide`
                       17. `malformedResponse`
                     3.
                     但这里也确认了一个
                     不能再忽略的修正：
                     `TokenGenerationError.toInferenceError`
                     `0x274de6890`
                     的
                     jump-table
                     注释
                     `case N`
                     不能直接解释成
                     `Code.rawValue == N`。
                     证据是：
                     - `Code.rawValue`
                       已明确是线性
                       `0..17`
                     - 但
                       `toInferenceError`
                       中
                       `tooManyTokens`
                       的
                       `count/max`
                       payload
                       现已用分页反汇编更正到
                       `case 3`
                       (`0x274de71b4`)
                     - 而
                       `case 11`
                       (`0x274de7020`)
                       实际是另一类带
                       `name`
                       字段的 payload
                     - `case 15`
                       的分支
                       (`0x274de6ec0`)
                       又明显在组
                       `SafetyRejectedInfo.ViolationCategory`
                       相关 payload
                     这说明：
                     - `switch case N`
                       前参与分发的
                       不是
                       “裸
                       `Code.rawValue`”
                     - 中间至少还有一层
                       helper /
                       remap /
                       grouped discriminator
                     4.
                     因而当前正确主线应更新为：
                     - `InferenceError`
                       的真实 case 顺序
                       已拿到
                     - `TokenGenerationError.Code`
                       的真实 rawValue 顺序
                       已拿到
                     - 下一步不是把
                       `switch case N`
                       机械套到
                       `Code.rawValue == N`
                     - 而是继续按
                       每个分支的
                       payload 形状 +
                       统一尾部
                       `w2`
                       + 外部
                       `InferenceError`
                       case constructor
                       消费方式
                       去做
                       `TokenGenerationError -> InferenceError`
                       精确映射
                   - 2026-06-16
                     21:59
                     再往下追
                     modern fixups
                     这一条，
                     当前 extracted 样本
                     已可明确判为
                     不可用：
                     1.
                     `TokenGenerationInference`
                     当前这份
                     `/Volumes/2T/dsc_arm64e_extract/...`
                     Mach-O
                     里
                     没有
                     `LC_DYLD_CHAINED_FIXUPS`
                     (`0x80000034`)
                     2.
                     仅有一个
                     `LC_DYLD_EXPORTS_TRIE`
                     (`0x80000033`)
                     ，且
                     `dataoff=0`
                     `datasize=0`
                     3.
                     `ModelManagerServices`
                     的同类 extracted 样本
                     也是同样状态
                   - 这说明：
                     - 当前 extracted 文件
                       对现代
                       dyld chained fixups
                       元数据已经丢失
                     - 所以
                       `dyld_info -fixups`
                       /
                       `-fixup_chain_details`
                       读不出有用内容
                       不是工具问题，
                       而是样本层面缺数据
                   - 因而若后续还要追
                     `1399/1400`
                     的更细真实 import 名字，
                     需要换成：
                     - 未丢链式 fixup
                       元数据的原始映像
                       / cache 内视图
                     - 或继续依赖
                       调用行为 +
                       ABI
                       分层推断
                   - 2026-06-16
                     22:11
                     又补了一层
                     cache-aware
                     负结论：
                     1.
                     真实系统路径下的
                     `dyld_info -load_commands`
                     仍只暴露：
                     - 空的
                       `LC_DYLD_EXPORTS_TRIE`
                     - `LC_SYMTAB`
                     - `LC_DYSYMTAB`
                     没有直接给出
                     `LC_DYLD_CHAINED_FIXUPS`
                     2.
                     cache map
                     只能稳定给出
                     image 名称和
                     VM range，
                     例如：
                     - `TokenGenerationInference`
                       `__TEXT 0x275058000 -> 0x2752675A0`
                     - `ModelManagerServices`
                       `__TEXT 0x25A628000 -> 0x25A7C0400`
                     3.
                     但
                     `0x29a246270`
                     这类 stub slot
                     所在页
                     不直接落在
                     image 自身 segment
                     range 里，
                     说明它涉及
                     shared cache
                     的外部页 / 分片映射
                     4.
                     当前能看到：
                     `/System/Volumes/Preboot/.../dyld_shared_cache_arm64e`
                     只是一个
                     560KB
                     的 header/atlas
                     入口；
                     真正 payload
                     分散在
                     `.01/.05/.09/...`
                     与
                     `.dylddata/.dyldlinkedit`
                     分片中
                   - 因而当前再往下的
                     真实 blocker
                     已经不是
                     `1399/1400`
                     的 ABI 语义，
                     而是：
                     “缺少 dyld subcache
                     header / 映射格式
                     的可靠结构定义，
                     无法把
                     shared-cache vmaddr
                     稳定映射回
                     对应分片 file offset”
                   - 在没有这个结构定义前，
                     继续硬做
                     `0x29a246270`
                     的 cache 级
                     原地解引用
                     风险过高，
                     容易把映射关系
                     猜错
               11. 相比之下，
                   `[7D0]`
                   目前仍只可保守写成：
                   local async helper
                   通过
                   `X20`
                   传递的隐藏槽位；
                   它先前被记成
                   “hidden async context /
                   continuation lowering”
                   现在需要降级为
                   待复核，
                   暂不要再把它硬写成
                   `asset.version`
                   或
                   `Asset`
                   剩余 field word
                   - 2026-06-16
                     新增的
                     nested local helper
                     本机 ABI
                     对照
                     (`/tmp/swiftabi.8d32iQ/sample_nested.swift`)
                     也支持这一降级：
                     `localHandle`
                     的
                     SIL
                     是
                     `@convention(thin) @async (@in_guaranteed any P, @guaranteed String, @in_guaranteed Asset, @guaranteed String) -> @error E`
                     ，即：
                     - 显式业务参数
                       后面跟的是
                       closure capture
                       `cap`
                     - typed error
                       仍是独立的
                       `@error E`
                       槽
                   - 对应 arm64
                     entry
                     (`sample_nested.s`)
                     也明确：
                     - `x6`
                       被存到
                       state 上
                       (`str x6, [x22, #152]`)
                       作为
                       typed error
                       storage
                     - `x5`
                       则作为
                       capture
                       `cap`
                       被存到
                       `[x22, #112]/[x22,#120]`
                   - 这说明在
                     local async helper
                     场景里，
                     “显式参数之后还会多出
                     hidden capture/self
                     槽”
                     是正常现象；
                     因而目标里的
                     `[7D0] = X20`
                     当前更像
                     capture/self
                     侧的隐藏保存槽，
                     而不是
                     typed-throws
                     error storage
                   - 2026-06-16
                     对目标二进制本身的
                     横向 wrapper
                     对照也与此一致：
                     1.
                     `handleLLMModel`
                     wrapper
                     (`0x2750f9808`)
                     只有：
                     - `X0 -> [0x370]`
                     - `X1 -> [0x378]`
                     - `X20 -> [0x380]`
                     即：
                     两个显式参数
                     + 一个隐藏槽位
                     ，没有任何
                     `Asset.version`
                     之类多余业务字段
                     空间
                     2.
                     `handleDraftModel`
                     wrapper
                     (`0x275107674`)
                     是：
                     - `X0..X5`
                       顺排显式参数
                     - `X20`
                       额外隐藏槽
                     3.
                     `handleLLMAdapterMetadataOverride`
                     wrapper
                     (`0x2750fcf38`)
                     与
                     `handleLLMAdapter`
                     wrapper
                     (`0x2750fe7d4`)
                     也都保持同型：
                     - `X0..X4`
                       是显式参数 / typed error
                       family
                     - `X20`
                       独立存到
                       `[...70]`
                       一类隐藏槽位
                   - 因而当前可以把
                     `[7D0]`
                     的工作假设进一步收紧成：
                     “local helper
                     的 capture/self
                     隐藏保存槽”
                     ，后续除非出现反证，
                     不再优先把它当成
                     continuation context
          7. 缩范围检索后，
             `/var/mobile/ajax/*`
             当前只在
             `TokenGenerationInference.framework`
             内出现，
             不在
             `ModelManagerServices.framework`
             /
             `ModelCatalog.framework`
             内出现
          8. 它们横跨的
             consumer 面
             已至少包括：
             - `loadAsset`
             - `createInferenceContext`
             - `unloadAsset`
             - `countTokens`
             因而更像
             `TokenGenerationInference`
             内部统一 published view，
             不是外部 host/service
             框架额外提供的路径
        - `adapterTypeToSymbolMapping`
          /
          `adapterTypeToSignatureMapping`
          的消费层级也进一步收紧：
          1. `Metadata json is missing adapter type to symbol mapping`
             的 xref
             当前在：
             `modelConfigurationWithURL(...)`
             (`0x2750f7e18`)
          2. `handleLLMAdapterMetadataOverride(...)`
             (`0x2750fcf6c`)
             会继续做
             override-specific
             的
             adapter-type / signature
             约束，
             命中：
             - `Override metadata adapter signature ...`
             - `Metadata override cannot be supported on adapter ...`
          3. 这说明：
             原始
             adapter-type -> symbol/signature
             解析
             主要在
             model-config
             生成阶段，
             override
             只是在其上追加一致性约束
      - `TGIAdapterConfigurationObjC.adapterConfiguration`
        与
        `TGIModelConfiguration.mutableWeightsSymbolToPath`
        也已收紧：
        - `adapterConfiguration`
          会把：
          - `adapterType`
          - `symbolName`
          - `mutableWeightsFilePath`
          分别转成：
          - `std::string`
          - `std::string`
          - `filesystem::path`
        - `mutableWeightsSymbolToPath`
          会把：
          `symbolName -> mutableWeightsFilePath`
          写入内部 `unordered_map`
        - 这说明：
          adapter mutable weight
          在内部 contract 里
          已经不是匿名 blob，
          而是带
          `symbolName`
          键控的路径映射
      - `ANEClientModelAssetPath`
        的真实落点也已收紧：
        - 它不在
          `TGIModelConfigurationObjC.modelConfiguration`
          这层
        - 当前 machine-local 证据显示，
          它属于
          `+[TGIE5ANESessionObjC sendStartSignalForResource:useEnergyEfficientMode:assetIdentifier:]`
          /
          `sendStopSignalForResource:`
          这组 start/stop hint path
        - 具体可对上的 key 语义为：
          1. `0x29e267700`
             -> `ANEClientModelAssetPath`
          2. `0x29e267720`
             -> `ANEClientEnergyEfficientWorkload`
          3. `0x29e267740`
             -> `ANEHintClientSessionStart`
          4. `0x29e267760`
             -> `ANEClientTotalPages`
          5. `0x29e267780`
             -> `ANEClientResidentPages`
          6. `0x29e2677a0`
             -> `ANEHintClientSessionStop`
        - `sendStartSignal...`
          会：
          1. 用
             `{ANEClientModelAssetPath: resource.path,
               ANEClientEnergyEfficientWorkload: NSNumber(bool)}`
             建字典
          2. 把它交给
             `ANEHintClientSessionStart`
             对应的调用
          3. 再从返回字典里按
             `ANEClientTotalPages`
             /
             `ANEClientResidentPages`
             取指标
        - `sendStopSignal...`
          会：
          1. 用
             `{ANEClientModelAssetPath: resource.path}`
             建字典
          2. 把它交给
             `ANEHintClientSessionStop`
             对应的调用
        - 这说明：
          `ANEClientModelAssetPath`
          是 ANE session 生命周期 hint / telemetry
          的 key，
          不是上游 compile contract
          的主控制位
      - 对应持久化笔记：
        - `mps/ANE/experiments/results/token_generation_provider_route_note.md`
  - 对应持久化笔记：
    - `mps/ANE/experiments/results/modelmanager_host_route_schema_note.md`
    - `mps/ANE/experiments/swift_fieldmd_dump.py`
  - 这意味着：
    - 真正有资格跨过
      `adapterWeight.allow`
      gate 的路径很可能不是 public
      `_ANEClient loadModelNewInstance`
      本身，
      而是：
      `client -> com.apple.modelmanager -> modelmanagerd -> inferenceprovider appex -> ANE`
    - 但当前我们还没有 machine-local 可调用的
      `ModelManagerServices` Swift client surface；
      module 不可直接 `import`，
      ObjC runtime 也拿不到可直接调用的方法表，
      说明下一层需要继续 reverse
      `com.apple.modelmanager`
      request schema 或 Swift symbol 调用面。
- `_ANEClient doLoadModel` 成功回调会显式写入 `_ANEModel` 的
  `modelAttributes/state/programHandle/intermediateBufferHandle/queueDepth`
  并构造 `program` 与 `mapper`，不只是写一个 `programHandle`。
- 对 eval-only bridge 路径，fresh wrapper 已经可以从 live anchor model
  的可见 runtime 状态重建并直接 `evaluateWithQoS`，不再需要对 fresh
  wrapper 再次 `loadWithQoS`。
- 当前 bridge 上的 `ANE_BRIDGE_RUNTIME_CLONE_CACHE=1` 已在本机 smoke 中
  命中并显著减少重复 load 开销，但这条路径目前只对“同一 identifier +
  同进程 + eval-only”成立。
- 2026-06-13 新增的 `AppleNeuralEngine.i64` 静态事实已把
  descriptor/runtime gap 进一步收窄到“load 成功后的 runtime state 复用”：
  - `+[_ANEInMemoryModelDescriptor modelWithMILText:weights:optionsPlist:]`
    / `modelWithNetworkDescription...`
    只是把 `networkText/weights/optionsPlist/isMILModel`
    交给
    `initWithNetworkText:weights:optionsPlist:isMILModel:`
  - `-[_ANEInMemoryModel saveModelFiles]`
    会把 descriptor 落成 file-model
    (`model.mil` + `weights/...` + 可选 compiler options file)
  - `-[_ANEInMemoryModel compilerOptionsWithOptions:isCompiledModelCached:]`
    明确写入：
    - `kANEFModelTypeKey`
    - `kANEFInMemoryModelIdentifierKey`
    - `kANEFInMemoryModelIsCachedKey`
    - 可选 `kANEFCompilerOptionsFilenameKey`
  - `+[_ANEVirtualClient shouldUsePrecompiledPath:options:shouldUseChunking:chunkingThreshold:]`
    已确认真正 precompiled file path 的硬条件是：
    - `kANEFModelType == kANEFModelPreCompiled`
    - `modelURL.path` 指向文件而不是目录
    - path 以 `.hwx` 结尾
  - 因此 directory-root wrapper-route 再怎么调，也不是真正的 precompiled path；
    它能跑通的仍然是 `MIL compile/load` family。
- 已在 `mps/maderix_ANE/bridge/ane_bridge.m`
  扩展 runtime template cache：
  - 不再只缓存 `_ANEInMemoryModel`
  - 也允许缓存已经 `loadModel` 成功的 `_ANEModel` runtime-visible state
  - `bridge_rehydrate_from_runtime_template(...)`
    现在会先尝试从 cached `_ANEModel`
    直接恢复 `modelAttributes/state/programHandle/intermediateBufferHandle/queueDepth/program/mapper`
- 该改动已拿到新的 machine-local 证据：
  - `benchmark_results/private_ane/runtime_clone_wrapper_client_route_smoke_after_patch.json`
    - 第一次 `load_cache_client_wrapper_mil`
    - 第二/三次同 identifier 直接 `runtime_clone`
    - `eval_ok = true`
  - `benchmark_results/private_ane/runtime_clone_real_ffn_load_roundtrip_after_patch.json`
    - real weighted FFN：
      - round1 `load_cache_client_wrapper_mil`
        `load_wall_sec ≈ 0.157s`
      - round2 `runtime_clone`
        `load_wall_sec ≈ 0.00126s`
      - checksum 一致
  - `benchmark_results/private_ane/runtime_clone_real_block_wrapper_roundtrip_after_patch.json`
    - real transformer block：
      - round1 `pre/gate/ffn` 仍是 cold compile/load
      - round2 三段全部 `bridge_profile_route = runtime_clone`
      - `bridge_profile_load_qos_sec` 从毫秒级/百毫秒级降到
        `~0.00015 - 0.00022s`
- 2026-06-13 复跑 `test_clean.m4a` full-audio 后，已拿到一次完整成功结果：
  - 输出文件：
    `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4_runtimeclone_clientmodel_after_patch_timeout600.json`
  - 关键结果：
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
    - `min_free_percent = 5.493`
  - 这次成功证明：
    - 之前的 `compressor_memory` 杀进程是系统基线过高导致的，
      不是 full-audio 路径本身不可跑
    - 在当前清理后的机器状态下，`batch4` + runtime-clone client-model
      已经可以完整跑完 `test_clean.m4a`
  - 对应失败证据仍保留，作为旧基线参考：
    `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4_runtimeclone_clientmodel_after_patch.private_ane_child/parent_watchdog_failure.json`
  - 当前工作重点因此从“先拿到完整 wall time”转回“压 speed”，而不是继续盯内存杀进程。
- 2026-06-14 已把 wrapper-route 做成受控参数，不再只能靠外部 env：
  - module/config:
    - `private_ane_bridge_wrapper_route`
  - benchmark CLI:
    - `--private-ane-bridge-wrapper-route`
  - 语义：
    - 启用时统一下发：
      - `ANE_BRIDGE_CLIENT_FILE_LOAD=1`
      - `ANE_BRIDGE_CLIENT_FILE_LOAD_ALL=1`
      - `ANE_BRIDGE_CLIENT_FILE_PACK_WEIGHTS=1`
      - `ANE_BRIDGE_CLIENT_FILE_WRAPPER=1`
    - 默认 `"default"` 不覆盖用户已有 env；显式 false 才清理这些 key
  - machine-local 轻量验证已通过：
    - `benchmark/private_ane_test_clean_benchmark.py` 的 flag
      会进入 `inference_params`
    - `PrivateANETransformerRunner` 会把该 flag 下发到 wrapper-route env
    - 且 `private_ane_bridge_client_variant=restricted_no`
      仍会一起生效
  - 当前主机在该验证时的 system free memory 只有约 `0.4% ~ 1.4%`，
    因此真实 1s smoke 仍被 native supervisor 以 `compressor_memory`
    杀掉；这说明当前不能把“真实 smoke 未完成”解释成新参数链路失败。
  - 同时已修正一个实际透传缺口：
    - `private_ane_bridge_client_variant`
      之前未加入 `separator.py` 的 inference target / passthrough / module
      赋值链，benchmark CLI 虽然能带这个参数，但不保证真正落到 runner
    - 现在已补齐：
      - `common.py` 默认值
      - `separator.py` 的 target/passthrough
      - `separator.py` 的 module 赋值与严格校验
    - 轻量验证已通过：
      `MSSeparator.update_inference_params(...)`
      会同时写入
      `private_ane_bridge_client_variant=restricted_no`
      与
      `private_ane_bridge_wrapper_route=True`
- `benchmark/private_ane_test_clean_benchmark.py` 之前默认把
  `private_ane_cache_tmpdir` 强制设到仓库内固定目录；当前实测这会污染
  `ANE_BRIDGE_TMPDIR`，让某些 STFT / band-split compile 在 benchmark
  路稳定报 `InvalidMILProgram`。默认值已改为 `global`，只在用户明确给路径时
  才启用自定义 cache tmpdir。
- 当前 worktree 下做历史基线对比时，必须显式固定
  `private_ane_fused_mask_estimator_max_outputs=2`；否则会落到当前默认的
  `mask_fused_0_8` 形态，并在 fixed-cache 复测中直接 `InvalidMILProgram`。
- 在当前代码上，`test_clean.m4a` 已拿到两个完整 full-audio 结果：
  - `cache_tmpdir=global` + `mask_max_outputs=2` -> `109.684s`
  - fixed cache tmpdir + `mask_max_outputs=2` -> `85.591s`
- bridge 现已拿到按 stage 聚合的 native profile 分项。最新证据表明：
  - fixed cache tmpdir 慢的核心不是 `load_qos`，而是桥层反复做
    `file_write/content-verify`
  - 在 fixed-cache 旧桥路径上，主要 `bridge_profile_file_write_sec` 为：
    - transformer `22.231s`
    - mask `11.531s`
    - band split `10.735s`
    - istft `5.457s`
- 已在 `mps/maderix_ANE/bridge/ane_bridge.m` 引入
  `ANE_BRIDGE_SKIP_CONTENT_VERIFY=1` 快速路径，并在 private ANE runner
  开启 load-cache 时默认下发。该路径依赖 identifier 目录内容寻址，仅做
  size-match，避免每次 load-cache hit 都重读整个权重文件。
- 新 bridge 路在 `test_clean.m4a` 的 full-audio 上已给出明显改进：
  - `benchmark_results/private_ane/test_clean_full_private_global_mask2_currentcode_bridgeprofile_profile/profile_summary.json`
  - `wall_clock.seconds = 61.952594041998964`
  - 同口径下 bridge `file_write` 已降到：
    - transformer `0.306s`
    - mask `0.158s`
    - band split `0.155s`
    - istft `0.037s`
- 反汇编/桥层联合事实：
  - `ANECompiler` 的 `ANECCompile` / `ANECCompileJIT` 明确是 file-oriented 路径，
    含 `"Start of compilation of network from file: %s"`、`.status.plist`、
    `jit_cfg_0` 等字符串；
  - `ANECGetJITCompilerInputs` 明确要求 AOT file、JIT shapes file、
    output JIT file；
  - bridge profile identifier 的第一段已验证等于 `sha256(mil_text)`；
    第二段权重 hash 形式仍未完全恢复。
- 2026-06-12 新增的 `AppleNeuralEngine.framework` 静态事实：
  - runtime load 主链确认都在 `AppleNeuralEngine.framework`，不是
    `ANECompiler.framework` / `ANEServices.framework`：
    - `-[_ANEClient doLoadModel:options:qos:error:]`
    - `-[_ANEVirtualClient loadModel:options:qos:error:]`
    - `-[_ANEClient compiledModelExistsFor:]`
    - `-[_ANEDaemonConnection loadModel:sandboxExtension:options:qos:withReply:]`
    - `+[_ANEModel modelAtURL:key:]`
    - `+[_ANEModel modelAtURLWithSourceURL:sourceURL:key:cacheURLIdentifier:]`
    - `+[_ANEInMemoryModelDescriptor modelWithMILText:weights:optionsPlist:]`
  - 因而后续若继续拆 warm `load_qos` / compiled-cache / descriptor 边界，
    优先在 `AppleNeuralEngine.i64` 追链，不要先回到 `ANECompiler/ANEServices`
    查 runtime load。
  - `-[_ANEClient connectionForLoadingModel:options:]` 只在
    `kANEFModelType == kANEFModelPreCompiled` 时选 `fastConnWithoutLock`；
    其它 load 仍走默认 `conn`。
  - `___44-[_ANEClient doLoadModel:options:qos:error:]_block_invoke` 在
    `kANEFModelHasCacheURLIdentifierKey` 为真时跳过
    `issueSandboxExtensionForModel:error:`；否则先发 sandbox extension。
  - `___44-[_ANEClient doLoadModel:options:qos:error:]_block_invoke_2`
    成功后会：
    - `updateModelAttributes:state:programHandle:intermediateBufferHandle:queueDepth:`
    - `setCacheURLIdentifier:`
    - `controllerWithProgramHandle:`
    - `programWithController:intermediateBufferHandle:queueDepth:`
    - `setProgram:` / `setMapper:`
  - `___45-[_ANEClient compileModel:options:qos:error:]_block_invoke_2`
    成功后只把 model 推到 compiled state (`state=2`) 并写入
    `cacheURLIdentifier`，不会生成 runtime `program` / `mapper`。
- source-style private client file-load 的 public 语义已从 probe 进一步收窄：
  - 对 STFT source MIL，`_ANEModel modelAtURL:key:` 传
    `directory URL + empty key` 仍会掉到
    `model.espresso.net` clone 路并失败；
  - `model.mil file URL + empty key` 可以直接 `loadModel/evaluate/unload`
    成功；
  - 因此 bridge 当前 `client_file_load` 路应使用 `model.mil` 文件 URL，
    但 `key` 必须为空串，不能再传 `hexStringIdentifier`。
- 该修正已经在 bridge 上拿到正向证据：
  - `benchmark_results/private_ane/realtime_stft_client_file_probe.json`
    证明：
    - directory direct compile/load 失败并显式报
      `Cannot load network .../model.espresso.net`
    - file direct load / file direct eval 成功
  - `benchmark_results/private_ane/stft_client_file_probe_fixed.json`
    证明修正 bridge 后，STFT preload 路：
    - `bridge_profile_route = load_cache_client_file`
    - `bridge_profile_fast_load_hit = 1`
    - `bridge_profile_fast_load_fallback = 0`
- 但 weighted `client_file_load` 仍未打通：
  - `benchmark_results/private_ane/block_client_file_probe.json`
    在真实 transformer block 的 `pre/gate/ffn` 三段上都显示：
    - `bridge_profile_n_weights = 4/5/6`
    - `bridge_profile_fast_load_attempted = 1`
    - `bridge_profile_fast_load_hit = 0`
    - `bridge_profile_fast_load_fallback = 1`
    - `bridge_profile_file_write_sec = 0.0`
  - 说明当前 public file-load 修正足以打通 STFT 一类 source MIL，
    但对 weighted transformer segments，`_ANEClient loadModel` 仍被拒绝，
    随后 fallback 到 `_ANEInMemoryModel loadWithQoS`。
- 2026-06-12 新增的最小 weighted public probe 已确认其直接拒绝原因：
  - `benchmark_results/private_ane/weighted_client_load_probe_pre.json`
  - 对未打包的 multi-file source artifact，所有 `file_key_empty` /
    `file_source_dir_*` / `file_cache_identifier` 变体都会在 public
    `compileModel/loadModel` 路上报：
    - `Error Domain=com.apple.appleneuralengine.espresso Code=-14`
    - `Network translation error: Blob storage must be backed by only one weight file.`
  - `has_cache_id` 只会把 `loadModel` 的失败面改成：
    - `Code=16 file not found`
    并没有解决 weighted source route 本身。
  - `precompiled_has_cache_id` 虽然让 `compileModel` 返回 `true`，
    但 `compiledModelExistsAfterCompile` 仍可能是假、`loadModel` 仍失败，
    不能作为可用路径。
- 基于上述错误，bridge 已新增实验性 packed single-file route：
  - 对 weighted `client_file_load`，在 identifier 目录下额外生成：
    - `model.client.mil`
    - `weights/packed.bin`
  - 并把原始多 `weights/*.bin` 的 `BLOBFILE` 引用重写到单一 packed 文件。
- 该 packed route 已证明能把 weighted public load 打通：
  - `benchmark_results/private_ane/weighted_client_load_probe_pre_packed.json`
  - 对同一个 real transformer `pre` segment：
    - `compile_ok = true`
    - `load_ok = true`
    - `compiled_exists_after_compile = true`
    - 多个 model variant / option variant 都能拿到 `state=3` 与非零 `programHandle`
- 但 packed route 仍未完成端到端：
  - `benchmark_results/private_ane/block_client_file_probe_packed_bridge_debug_verbose_v3.json`
  - bridge 级真实 `pre/gate/ffn` 三段已经显示：
    - iter1 `client_file_loaded = 1`
    - iter2 `fast_load_hit = 1`
    - `client_file_error = ""`
  - 也就是说 weighted `loadModel` 已不再是阻塞点。
  - 新阻塞点变成 `evaluateWithModel`：
    - stderr:
      `ANEProgramProcessRequestDirect() Failed with status=0x2 : statusType=0x9: Program Inference error`
  - 说明 packed artifact 已被 public compile/load 接受，但其 runtime/eval
    语义仍与 private in-memory path 不一致。
- 这个 packed eval 失败已经进一步收窄：
  - `benchmark_results/private_ane/weighted_client_eval_probe_pre_packed.json`
    证明对同一个 packed `pre` segment：
    - `empty` options 与 `file_opts` 都会
      `compile_ok = true`, `load_ok = true`, `eval_ok = false`
    - 所以问题不在 bridge 当前给 `evaluateWithModel` 的 options。
  - `benchmark_results/private_ane/weighted_client_eval_probe_pre_packed_variants.json`
    证明以下高层 model 形态全部无差别失败：
    - `file_key_empty`
    - `file_source_dir_id1`
    - `file_source_dir_id2`
    - `file_source_dir_id2_cache`
    - `file_cache_identifier`
    - 且对 `empty` / `file_opts` 都一样 `eval_ok = false`
    - 所以问题也不在 `sourceURL / identifierSource / cacheURLIdentifier`
      这类高层 `_ANEModel` 构造字段。
  - `benchmark_results/private_ane/weighted_pack_variants_pre/summary.json`
    证明对 packed.bin 的小改动：
    - `slice_keep / slice_abs / slice_rel64 / slice_zero`
      都会 `compile_ok = true`, `load_ok = true`, `eval_ok = false`
  - `slice_0x08_rel64 / slice_0x08_zero / peak_style`
      直接回到 `compile_ok = false`
    - 说明当前阻塞也不是一个“显而易见的单字段 offset 修补”。
- 2026-06-12 新增的 fresh packed probes 进一步说明当前分段状态不是单一结论：
  - `pre`:
    - `benchmark_results/private_ane/weighted_fresh_pack_pre_load_stable.json`
    - `benchmark_results/private_ane/weighted_fresh_pack_pre_eval_stable.json`
    - fresh 唯一路径下依然 `compile_ok = true`, `load_ok = true`, 但
      一输出 `eval_ok = false`，说明不是 stale compiled cache。
    - `benchmark_results/private_ane/weighted_fresh_pack_pre_eval_threeout_stable.json`
      证明给三输出 request（`0/1/2`）后 `eval_ok = true`。
    - `benchmark_results/private_ane/weighted_fresh_pack_pre_output_index_probe.json`
      进一步证明：
      - 单独请求 `[0]` / `[1]` / `[2]` 都是 `eval_ok = false`,
        `wrote_outputs = false`
      - 只有 `[0,1,2]` 一起请求时才 `eval_ok = true`
    - `benchmark_results/private_ane/weighted_fresh_pack_pre_threeout_compare_freq64.json`
      证明在真实同一输入上：
      - file-route three-output `out0/out1/out2` 三份输出逐字节完全一致
      - best mapping 到 `qraw/kraw/v` 的
        `mean_abs` 之和仍为 `0.5846427977`
      - 所以它不是可直接接入 runtime 的真实 `q/k/v` 契约
    - `benchmark_results/private_ane/publicload_privateeval_probe_pre_directprocess.json`
      证明：
      - 直接 `private evaluateWithQoS` 失败
      - `factory_full` runtime clone 也失败
      - 直接 `_ANEProgramForEvaluation processRequest...` 仍失败，`driver_status = 2`
    - `benchmark_results/private_ane/weighted_client_eval_probe_pre_packed_variants_with_dir_key_empty.json`
      进一步证明：
      - `dir_key_empty + empty/file_opts` 会回到
        `model.espresso.net` clone 失败路
      - `dir_key_empty + mil_model_type` 可以
        `compile_ok = true`, `load_ok = true`, `eval_ok = true`
    - `benchmark_results/private_ane/weighted_fresh_pack_pre_dir_mil_single_compare_freq64.json`
      但也同时证明：
      - `dir_key_empty + mil_model_type` 的单输出虽然能 eval，
        数值仍明显不是正确的 `att_flat`
      - 对 torch `att_flat`：
        - `mean_abs = 0.4253934920`
        - `max_abs = 242.2471008301`
    - `benchmark_results/private_ane/weighted_pre_private_vs_public_vs_torch_freq64.json`
      进一步把“是谁错”边界收窄为：
      - 同一 artifact、同一随机输入下：
        - private in-memory 输出
        - wrapper-companion `dir_key_empty + mil_model_type` 输出
        逐值完全一致（`mean_abs = 0`）
      - 且两者一起偏离当前 torch `att_flat` 参考：
        - `mean_abs = 0.4253934920`
        - `max_abs = 242.2471008301`
      - 所以当前“数值不对”不能再归因到 `dir_key_empty + mil_model_type`
        这条 public route 本身；更像是
        1. 当前 torch reference 指错了 block/axis，或
        2. 这份 packed artifact 的来源/权重身份并不是当前以为的那个 `pre`
    - `benchmark_results/private_ane/weighted_pre_wrapperroot_bruteforce_matches_freq64.json`
      说明把当前 wrapper root 输出对 model 内所有 layer/axis 的 `pre(att_flat)`
      做 brute-force 后，没有任何一个真实 block 接近匹配；
      best 也仍是 `mean_abs = 0.4253934920`。
    - `benchmark_results/private_ane/weighted_pre_weight_match_scan.json`
      说明对 `weighted_fresh_pack_pre_1781215248/weights/packed.bin` 按当前
      `model.mil` 偏移解析后，其 `gamma/Wq/Wk/Wv` 也不接近当前 checkpoint 中
      任一 layer/axis 的同名权重。
    - `benchmark_results/private_ane/regen_pre_freq0_publicpacked_compare_1781359181.json`
      给出当前最关键的新边界：
      - 用当前 checkpoint 的 `layer0/freq` 通过 bridge pack 路重新生成 fresh
        public-packed pre 后：
        - `model.mil` hash 与旧 artifact 相同
        - 但 `packed.bin` hash 不同：
          - old: `c52c1f2a34339012c6b1d9b9b83198e5095a692b`
          - new: `a35ecad57d7756b1616f3319b4dbbb5028f3413c`
      - 新生成 artifact 对当前 torch `att_flat`：
        - `mean_abs = 3.4188e-05`
        - `max_abs = 1.8311e-04`
      - 旧 artifact 对当前 torch `att_flat` 仍是：
        - `mean_abs = 0.4253934920`
        - `max_abs = 242.2471008301`
      - 所以 `weighted_fresh_pack_pre_1781215248` 的核心问题已经不是 route，
        而是其 `packed.bin` 本身并非当前 checkpoint 导出的内容。
    - 当前稳定、可复用的新 pre packed artifact 已固化为：
      - `benchmark_results/private_ane/weighted_pre_current_freq0_publicpacked_stable`
    - `benchmark_results/private_ane/regen_pre_freq0_threeout_compare_freq64.json`
      说明即便换成当前 checkpoint 重新生成的正确 packed artifact：
      - file-route three-output 仍然不对
      - 但它不再是“三份完全一样”的假输出
      - best mapping 到 `q/k/v` 的 `mean_abs` 总和仍有 `0.4999011457`
      - 说明 file-route public contract 问题是真存在的，不是旧 artifact 污染。
    - `benchmark_results/private_ane/regen_pre_freq0_dir_mil_single_compare_freq64.json`
      与
      `benchmark_results/private_ane/regen_pre_freq0_private_vs_public_dir_mil_freq64.json`
      说明对当前 checkpoint 重生 artifact：
      - `dir_key_empty + mil_model_type` 的单输出已经大幅改善
      - 对 torch `att_flat`：
        - `mean_abs = 0.0252261721`
        - `max_abs = 0.1537094116`
      - 但它与同一 artifact 的 private in-memory 仍有相同量级差异：
        - `mean_abs = 0.0252202097`
        - `max_abs = 0.1535949707`
      - 所以当前剩余问题可收窄为：
        `dir MIL public eval` 仍未完全等价于 private in-memory，
        而不是旧 artifact 身份问题。
    - `benchmark_results/private_ane/regen_pre_freq0_wrapper_restricted_no_mil_compare_freq64.json`
      与
      `benchmark_results/private_ane/weighted_pre_current_freq0_restricted_no_mil_compare_freq64.json`
      进一步把这条差异彻底收窄到 client 构造路径：
      - 只要把 `_ANEClient` 从 `sharedConnection` 换成
        `initWithRestrictedAccessAllowed:NO`（`client_variant=restricted_no`），
        `dir_key_empty + mil_model_type` 就能与 private in-memory 逐值完全一致
      - 对 torch `att_flat`：
        - `mean_abs = 3.4188e-05`
        - `max_abs = 1.8311e-04`
      - 所以先前 `mean_abs~0.025` 的剩余误差不是 artifact 问题，
        也不是 `mil_model_type` 路本身，而是 `sharedConnection`
        这条 client 构造路径带来的行为差异。
    - `benchmark_results/private_ane/weighted_pre_current_freq0_threeout_restricted_no_compare_freq64.json`
      则说明：
      - 即便换成 `restricted_no`，file-route three-output 的最佳 `q/k/v`
        对齐分数仍完全不变（`best_score = 0.4999011457`）
      - 所以 file-route three-output 的错误不在 client 构造路径，
        而在更低层的 lowered contract / output 语义。
    - 因而当前对 `pre` 的最强结论应更新为：
      - compiler-service 的 file-route metadata 确实 advertises lowered
        `kraw/qraw/v`
      - 但真实 public eval 并没有给出可用的 `q/k/v`
      - 旧 `weighted_fresh_pack_pre_1781215248` 的 `packed.bin` 不是当前 checkpoint
        导出的内容；不要再把它当作当前 pre packed 基线
      - 用当前 checkpoint 重生后：
        - file-route three-output 仍错
        - `dir_key_empty + mil_model_type` 在 `sharedConnection` 下会有
          `mean_abs~0.025` 漂移，但换成 `restricted_no` 后就与 private 完全对齐
      - 所以当前阻塞点应进一步更新为：
        1. 旧 artifact provenance 问题已基本厘清：`packed.bin` stale / foreign
        2. 下一轮重点转到：
           - 为什么 file-route three-output 在正确 artifact 上仍错
           - 为什么 `sharedConnection` 与 `restricted_no` 在 `dir MIL` 上有不同数值语义
  - `ffn`:
    - `benchmark_results/private_ane/weighted_fresh_pack_ffn_eval_stable.json`
    - one-output packed public route 已直接
      `compile_ok = true`, `load_ok = true`, `eval_ok = true`
    - 但新的数值对照已经否掉“可用”这一结论：
      - `benchmark_results/private_ane/ffn_mode_compare_packmodes_stable.json`
      - 同一组 `freq / batch=1 / seq=64 / EXACT / seed=5678` 输入下：
        - `private_inmem` 对 torch:
          - `mean_abs = 0.0020097045`
          - `max_abs = 0.0119628906`
        - `public_packed_public_eval` 对 torch:
          - `mean_abs = 0.1788446307`
          - `max_abs = 1.7541503906`
        - `public_packed_private_eval` 对 torch:
          - 与 `public_packed_public_eval` 完全一致
        - `public_packed_direct_process` 对 torch:
          - 也与 `public_packed_public_eval` 完全一致
        - `public_packed_synth_direct_process` 对 torch:
          - 仍与 `public_packed_public_eval` 完全一致
        - `public_data_root_direct_process` 对 torch:
          - 也仍与 `public_packed_public_eval` 完全一致
        - `public_eval_vs_public_privateeval = 0`
        - `direct_process_vs_public_eval = 0`
        - `synth_direct_process_vs_current_direct_process = 0`
        - `data_root_direct_process_vs_current_direct_process = 0`
      - 并且对同一 artifact 的 `model.mil -> model.client.mil` diff 已确认：
        - 只改了 `BLOBFILE(path, offset)` 引用
        - 没有额外的 MIL op / shape / attribute rewrite
    - 这说明对 `ffn`，当前 packed public route 的问题不是 client wrapper /
      private-eval sync / direct-process 入口差异，也不像是
      “copy 原始子头”或 “packed.bin vs @model_path/data 命名” 这层问题；
      更像是 public packed program 本身的语义或更深一层的 packed weight /
      sidecar contract 已经偏离 private baseline。
    - 2026-06-12 新增的 authored-shared-blob 分层结果进一步收窄了问题：
      - `benchmark_results/private_ane/sharedblob_convchain_compare_stable.json`
        - 一个最简单的 same-shape 两层 conv chain，直接 author 成单
          `weight.bin` 多 offset 后：
          - `private_inmem_sharedblob`
          - `public_sharedblob_public_eval`
          - `public_sharedblob_private_eval`
          - `public_sharedblob_direct_process`
          四者输出逐值完全一致
          (`public_eval_vs_private_inmem = 0`,
           `direct_process_vs_private_inmem = 0`)
        - 说明“单权重文件 + 多 offset”这件事本身在简单 same-shape case 上是成立的。
      - `benchmark_results/private_ane/ffn_authored_sharedblob_compare_stable.json`
        - 把完整 FFN 直接 author 成单 `weight.bin` 多 offset 后：
          - `private_inmem_authored_sharedblob` 对 torch 已经明显错误
            (`mean_abs = 2.7832823`, `max_abs = 116.1602783`)
          - public 三路也都错误，且三路彼此一致
        - 说明 full FFN 的 shared-blob 问题并不只是 public route 才有；
          private in-memory 对该 authored artifact 也无法给出正确结果。
      - `benchmark_results/private_ane/sharedblob_affine_fail_probe.json`
        - 一个更小的 heterogeneous `gamma + conv + bias` authored shared-blob
          在 private 路直接 `InvalidMILProgram`
        - 说明问题已经非常像“heterogeneous shared-blob contract”本身，
          而不是一般性的 shared-blob 多 offset 机制。
  - `gate`:
    - `benchmark_results/private_ane/weighted_fresh_pack_gate_eval_stable.json`
    - `file_opts` 下可达 `compile_ok = true`, `load_ok = true`
    - 但 `eval_ok = false`，仍是
      `ANEProgramProcessRequestDirect() ... Program Inference error`
    - 其它高层变体还会掉到 translator `Cannot serialize ANEC_IR_repr`
      的 `I/O error`。
- fixed cache tmpdir 不是纯收益：它明显改善了 STFT、transformer eval、
  `ane_pre_eval`、`axis_pack`、`ane_read`、GC 和 ISTFT，但同时把
  `band_split.compile` 与 `transformer.load_or_compile` 拉得更重。
- 2026-06-12 新增的 IDA + bridge 联合事实：
  - 当前 `ida-pro-mcp` + 本机 `/Applications/IDA Professional 9.0.app`
    已可直接工作；`ANECompiler.i64` / `AppleNeuralEngine.i64`
    会话可正常列出、重开并继续反编译。
  - 当前阻塞不是“缺另一套 IDA MCP transport”，而是需要继续沿
    `FillContext(...)` / translator / compiler service 往上追真实
    network-dictionary producer。
  - `anecompiler_i64` worker 偶发失联时，直接重新 `idb_open` 即可恢复；
    现阶段不需要为了 transport 切换到 `mrexodia/ida-pro-mcp` 或
    `blacktop/ida-mcp-rs`。
  - `-[_ANEInMemoryModel evaluateWithQoS:options:request:error:]`
    在本机正常环境下先检查 `sharedConnection`；
    若存在，则直接调用 `evaluateWithModel:options:request:qos:error:`，
    并不会天然落到更低层的 `processRequest...`。
  - 为排除这层歧义，bridge 已新增 `ANE_BRIDGE_DIRECT_PROCESS_EVAL=1`。
  - 但 `ffn_mode_compare_directprocess_stable.json` 已证明即便强制走
    `_ANEProgramForEvaluation processRequest...`，`ffn` 输出仍与
    public eval 逐值完全一致。
  - 在 `ANECompiler.framework` 中已确认几个更接近下一控制层的入口：
    - `ParseFileInfoFromTensorValue(...)`
      - 直接处理 `FILEBLOB`
      - 包含：
        - `Error: at most 16 weight files are allowed when compiling MIL model`
        - `Required FILEBLOB property "%s" not found`
        - `Value %s with mutable fileblob %s is not supported`
    - `mlir::anec::ANECIRNetwork::getWeightFileIndex(...)`
      - 负责把 weight file path 映射到内部 index
    - `SetupWeightFileProperties(...)`
      - 直接处理 weight-file property dictionary
      - 包含：
        - `kANECNetWeights`
        - `kANECNetMutableWeights`
        - `Encrypted property ... must be a boolean`
        - `Symbol property ... must be a string`
  - 这说明“只写 MIL + raw blob”并不一定覆盖 compiler 真正需要的全部
    weight-file companion 信息；对于 heterogeneous shared-blob，
    下一控制层很可能就是这些 weight-file property / FILEBLOB companion 语义。
  - 在 `AppleNeuralEngine.framework` 中又确认了 companion 的实际下传方式：
    - `-[_ANEInMemoryModel saveModelFiles]` 会把 `descriptor.optionsPlist`
      直接写到 `compilerOptionsFileName`
    - 因此 descriptor 侧 author compiler companion 是真实可达路径
  - 但最直观的 companion 试探已经给出负面结果：
    - `benchmark_results/private_ane/gamma_plus_w_weightfileprops_matrix.json`
    - 对 private `gamma_plus_w`，给 descriptor 注入二进制 plist：
      - `WeightFileProperties`
      - path 取值：
        - `weight.bin`
        - `weights/weight.bin`
        - `@model_path/weights/weight.bin`
      - `Symbol` 取值：
        - `G`
        - `W`
      - `Encrypted = false`
    - 这 6 组组合全部仍然 `InvalidMILProgram`
    - 说明仅靠已知的 `WeightFileProperties + Symbol + Encrypted`
      还不足以让 `gamma_plus_w` heterogeneous shared-blob 通过 private compile。
  - 更进一步的 top-level plist 试探也仍是负面：
    - `benchmark_results/private_ane/gamma_plus_w_optionsplist_matrix/matrix.json`
    - 对 private `gamma_plus_w` 已验证：
      - `Weights = ["weights/weight.bin"]`
      - `Weights = ["weight.bin"]`
      - `MutableWeights = ["weights/weight.bin"]`
      - 上述组合再叠加
        `WeightFileProperties`
      - 以及
        `GammaOffset`, `KernelOffset`, `BiasOffset`
    - 这些组合全部仍然 `InvalidMILProgram`
  - 对 `FillContext(...)` 的顶层字典形态也已拿到更具体的静态事实：
    - 顶层 key 已确认至少包括：
      - `Version`
      - `BinaryPoint`
    - per-network 字典里已确认：
      - `Attributes`
      - `Weights`
      - `MutableWeights`
      - `WeightFileProperties`
  - 并且一版最小 full compiler net plist author 也已被证伪：
    - `benchmark_results/private_ane/gamma_plus_w_fullnetplist_probe/probe.json`
    - 组合：
      - `Version ∈ {1.0.0, 1.0.4}`
      - network name ∈ {`main`, `net`}
      - per-network dict 含：
        - `Attributes = {}`
        - `Weights = ["weights/weight.bin"]`
        - 可选 `WeightFileProperties`
    - 这 8 组组合全部仍然 `InvalidMILProgram`
  - 说明下一控制层需求已经进一步收窄：
    - 不是“还差一个显而易见的 plist key”
    - 也不是“只差一版最小 full net plist”
    - 而是更深一层的 companion schema / registration state /
      compiler-side lowering contract。
  - 2026-06-12 继续沿 compile 主链往上追后，又收窄出一个更具体的边界：
    - `_ANECCompile(arg0, arg1, ...)` 中：
      - `arg0` 进入 `ANECGetCompilerInputs(...)`
      - `arg1` 进入 `ANECGetCompilerOptions(...)`
      - 随后进入 `ANECPrepare(...)`
    - `ANECPrepare(...)` 会按 `ANECGetCompilerFileFormat(...)` 分流：
      - `ANECIR`
      - `MIL file`
      - `MLIR`
    - 对当前最相关的 `MIL file` 路：
      - `ANECPrepare(...)`
      - `ANECCreatePrepareInfoFromMILFile(...)`
      - `CreateMILAndConvert(...)`
      - 产出 `vector<ANECProcedureInfo>`
    - `ZinCompilerCoreClassic::BuildLayerGraph()` 已确认直接执行：
      - `ZinIrFactory::ZinIrFactory(v30, *((const __CFDictionary **)this + 54), ...)`
      - 即 classic path 在进入 `ZinIrFactory/FillContext(...)` 之前，
        不再额外改写 procedure dictionary
    - 这说明对 classic compile 而言，真正的 producer 已经前移到
      `ANECPrepare/CreateMILAndConvert`，而不是 `FillContext(...)` 之后
      或 `optionsPlist` 这一侧。
  - `CreateMILAndConvert(...)` 里已确认存在更深的 MIL companion/lowering state：
    - 通过 `ANECGetAdditionalWeightFileName(...)` 拼接：
      - `.additional_weights.bin`
      - `/additional_weights.bin`
    - `ANECGetAdditionalWeightFileName(...)` 被 `CreateMILAndConvert(...)` 调用，
      且函数内直接出现：
      - `Failed to remove existing additional_weights.bin file.`
    - `CreateMILAndConvert(...)` 会：
      - `RegisteraneOpsets(...)`
      - `RetrieveMutableWeightToSymbol(...)`
      - `RetrieveModelSourceInformation(...)`
      - 遍历 MIL functions，并查找 `ANEprivate`
    - `RetrieveModelSourceInformation(...)` 会特意排除：
      - `BlobFileMutabilityInfo`
      - `ANEBinaryPoint`
      说明 compiler 自己维护了一层独立的 source-information companion，
      不等同于我们当前手工 author 的 MIL 文本。
    - `RetrieveMutableWeightToSymbol(...)` 会把 mutable blob 的绝对路径映射到 symbol。
  - 因而当前最强的新结论是：
    - `descriptor.optionsPlist` 试探失败，并不只是“key 还没猜全”
    - 更像是我们现在绕过了 `CreateMILAndConvert(...)` 这层真正 author
      `ANECProcedureInfo + additional_weights.bin + mutable-weight-symbol map +
      source-information + ANEprivate` companion 的 lowering 路
    - 所以下一控制层需求应从“继续补 optionsPlist key”
      转到“恢复/复现 `ANECPrepare/CreateMILAndConvert` 产出的 procedure artifact
      与 sidecar 语义”
  - 2026-06-12 新增的 compile-service / client / hwx 动态证据把边界继续收窄：
    - 对 `weighted_fresh_pack_pre_1781215248/model.mil`：
      - 证据：
        - `mps/ANE/.ane_runs/csv/ane_compiler_service_call_probe_weighted_pre.csv`
        - `mps/ANE/.ane_runs/csv/ane_client_options_probe_weighted_pre.csv`
        - `mps/ANE/.ane_runs/csv/ane_hwx_dictionary_probe_weighted_pre.csv`
      - `file_empty_options` / `file_coreml_model_type` compile 成功，但走的是
        lowered contract：
        - input symbol: `xn_ctx_tx_default__0`
        - outputs: `kraw@output`, `qraw@output`, `v@output`
        - procedure/network name: `net`
        - 这与先前 public packed file route 的三输出漂移一致
      - 同一个 source root 改成 `dir_mil_model_type` / `dir_mil_retain` 后，
        compile-service 又恢复到原始 MIL 语义：
        - input symbol: `x`
        - output symbol: `out@output`
        - procedure/network name: `main`
      - 这说明 compiler-service 对“file URL vs directory root + MIL model type”
        的语义分流非常实在，不只是路径外观不同。
      - `file_mil_model_type` 失败面会落下一份：
        - `output/model.hwx.tmp.additional_weights.bin`
        - 当前 size=0
        - 这是对 `additional_weights.bin` sidecar author 路径的直接动态证据。
      - 对成功生成的
        `dir_mil_retain/output/model.hwx` 再跑 `ane_hwx_dictionary_probe`，
        当前可见内容仍只有 `NetworkStatusList`，没有
        `ANEFModelDescription`。
      - 再用 `ane_client_options_probe` 回放同一 wrapper root，
        所有 option 组合下仍然：
        - `compiledModelExistsFor = 0`
        - `programHandle = 0`
        - `kANEFModelType = kANEFModelPreCompiled` 的 `compileModel` 可返回 true，
          但 `loadModel` 仍然不建立 runtime program
      - 这说明：
        - compile 侧已经能保住原始 segment contract
        - 但 runtime packaging 仍缺一层，不是单纯 `model.hwx/model.src/model.retain`
          三件套就足够
    - 对 `weighted_fresh_pack_ffn_1781216020/model.mil`：
      - 证据：
        - `mps/ANE/.ane_runs/csv/ane_compiler_service_call_probe_weighted_ffn.csv`
      - 与 `pre` 不同，这个 root 本身还带有：
        - `data`
        - `net.plist`
      - compile-service 在 clone 阶段会原样复制这两个 root companion，
        说明 source-root sidecar 不是被忽略的噪声，而是实际参与路径的一部分。
      - `file_empty_options` / `file_coreml_model_type` compile 成功时，
        contract 为：
        - input symbol: `xw_ctx_tx_default__0`
        - output symbol: `out@output`
        - procedure/network name: `net`
      - `dir_mil_model_type` / `dir_mil_retain` 仍然恢复到：
        - input symbol: `x`
        - output symbol: `out@output`
        - procedure/network name: `main`
      - `file_mil_model_type` 同样失败并留下零字节：
        - `output/model.hwx.tmp.additional_weights.bin`
    - 合并这两组动态结果后的新边界是：
      - `additional_weights.bin` 不是纯静态猜测，compile-service 真实会 author /
        尝试 author 这条 sidecar
      - source-root 形态与 companion（directory root、`data`、`net.plist`）
        会直接改变 compiler 产出的 procedure contract
      - 但即便 compile-service 已恢复出“原始 MIL 语义”的 wrapper，
        当前 visible wrapper 仍不足以让 `_ANEClient` 建立 nonzero
        `programHandle`
      - 因而下一控制层不只是 compile dictionary；还需要继续恢复
        runtime-packaging / load-side missing companion
  - 2026-06-12 新增的 runtime-wrapper augmentation 结果，把 runtime-side
    缺口从“缺一层”继续收窄成“缺 source-root companion 集合”：
    - 对 `weighted_pre` compiler-service wrapper：
      - baseline 仅 `model.hwx/model.src/model.retain` -> `MIL` load 失败
      - 单独加 `model.mil` 或单独加 `weights/packed.bin` 仍然
        `InvalidMILProgram`
      - 只有同时补回：
        - `model.mil`
        - `weights/packed.bin`
        `MIL` route 才会：
        - `compileModel(..., kANEFModelType = kANEFModelMIL) -> 1`
        - `loadModel(..., kANEFModelType = kANEFModelMIL) -> 1`
        - `programHandle != 0`
    - 对 `weighted_ffn` compiler-service wrapper：
      - baseline 失败
      - 单独加：
        - `data`
        - `net.plist`
        - `model.mil`
        - `weights/packed.bin`
        任意一项都仍失败
      - 只有把以下集合全部补回：
        - `data`
        - `net.plist`
        - `model.mil`
        - `weights/packed.bin`
        `MIL` route 才会成功 load 并建立 nonzero `programHandle`
    - 这说明 runtime 真正需要的不是抽象“隐藏状态”，而是：
      - compiler-service wrapper
      - 加上对应 segment 的 source-root companion 集合
    - 生命周期证据也已拿到：
      - fresh augmented root 首次运行：
        - `compiledModelExistsFor = 0`
        - `kANEFModelType = kANEFModelPreCompiled`：
          - `compileModel -> 1`
          - `programHandle` after compile 仍为 `0`
          - `loadModel -> 0`
        - `kANEFModelType = kANEFModelMIL`：
          - `compileModel -> 1`
          - `programHandle` after compile 仍为 `0`
          - `loadModel -> 1`
          - `programHandle` after load 变成 nonzero
      - 同一个 augmented root 第二次 fresh process：
        - `compiledModelExistsFor = 1`
        - `kANEFModelType = kANEFModelPreCompiled`：
          - `compileModel -> 1`
          - `programHandle` after compile 已变成 nonzero
          - `loadModel` 仍返回 `0`
        - 这说明 compiled-state 确实可复用，但 public `precompiled load`
          的返回语义仍不对
    - 因而当前最新边界是：
      1. compile-side contract 已可恢复
      2. runtime-side 需要 wrapper + source-root companion 集合
      3. compiled-state 可复用，但 `precompiled load` 还没真正打通
- 因此当前最接近历史基线的形态里，主阻塞已经从“native supervisor kill”
  转成“band-split / transformer compile-load 回退”，内存监管不再是首要事实。

## 当前较好结果

- private ANE:
  - `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_persistent_aux_profile_profile/profile_summary.json`
  - `wall_clock.seconds = 43.00265733300148`
  - `audio_seconds = 39.59002267573696`
- private ANE（当前代码、最近完整 fixed-cache 基线）:
  - `benchmark_results/private_ane/test_clean_full_private_fixedcache_mask2_currentcode_profile/profile_summary.json`
  - `wall_clock.seconds = 85.59072191699082`
  - `audio_seconds = 39.59002267573696`
- private ANE（当前代码、bridge file-verify 优化后的最好结果）:
  - `benchmark_results/private_ane/test_clean_full_private_global_mask2_currentcode_bridgeprofile_profile/profile_summary.json`
  - `wall_clock.seconds = 61.952594041998964`
  - `audio_seconds = 39.59002267573696`
- private ANE（当前代码、最近完整 current-run wall）:
  - `benchmark_results/private_ane/test_clean_full_private_historical_shape_bridgepatched_profile/profile_summary.json`
  - `wall_clock.seconds = 60.11096224997891`
  - `audio_seconds = 39.59002267573696`
- MLX full:
  - `benchmark_results/mlx_full_roformer_profile/test_clean_full_torch_mps_vs_mlx_full_current.json`
  - `mlx_full elapsed_sec = 13.503349041999172`

## 当前热点

来源：

- `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_persistent_aux_profile_profile/transformer_bottleneck_ledger.csv`

主要热点：

- `transformer.eval_loop_wall`
- `transformer.ane_pre_eval`
- `transformer.load_or_compile`
- `transformer.ane_total`
- `transformer.ane_eval_only`
- `transformer.axis_pack`
- `transformer.bridge_load_qos`
- `band_split.compile`
- `mask.compile`

## 当前阻塞

- transformer 仍有明显 `pre_eval` / `load_or_compile` / orchestration 开销。
- 在当前最好 bridgeprofile 结果里：
  - `transformer.eval = 33.175s`
  - `transformer.ane_pre_eval = 17.397s`
  - `transformer.axis_pack = 8.166s`
  - `transformer.load_or_compile = 10.229s`
  - 其中 `transformer.bridge_load_qos = 3.334s`
- descriptor / cache / segment 语义仍未恢复到足以直接操控行为的程度。
- `ffn` 当前虽然能 `compile/load/eval`，但 packed public route 数值明显错误；
  问题已收窄到 public packed program / single-blob weight 语义，而不是
  client eval 包装。
- 内存压力需要继续结合 watchdog、free memory、wired、compressor、swap 来解释和规避。
- `mapIOSurfacesWithRequest...` 在 fresh runtime clone 上仍报
  `Program IOSurfaces map failure (0x12)`；runtime clone 目前只证明了
  eval 路能绕过重复 load。
- 2026-06-17 新增 `ane_runtime_rehydrate_probe` 对照已把
  `mapIOSurfaces...` 的 blocker 再收窄一层：
  - `shallow_full` / `factory_full`：
    `fresh_mapper.controller_matches_program_controller = 0`、
    `fresh_controller.usecount = 1`，且
    `map_ok=0 eval_ok=1`
  - `shallow_full_shared_controller` / `factory_full_shared_controller`：
    强制让 mapper 复用 program 的 controller，
    `controller_matches_program_controller = 1`、
    `usecount = 2`，但仍然
    `map_ok=0 eval_ok=1`
  - `shallow_reuse_objects` / `factory_reuse_objects`：
    直接复用 baseline 已成功 load 的原始 `program`/`mapper` 对象，
    `controller_matches_program_controller = 1`、
    `usecount = 2`，仍然
    `map_ok=0 eval_ok=1`
  - `direct_base_model`：
    fresh `_ANEInMemoryModel` 直接持有原始 loaded `_ANEModel` 对象本身，
    也就是连 `program` / `mapper` / `controller` / `UUID` / `attrs` /
    `state` / `handles` 都不再经过 clone/rebuild，
    但仍然
    `map_ok=0 eval_ok=1`
  - 结论：`Program IOSurfaces map failure (0x12)` 已不再能归因于当前
    probe 可见的 `program/mapper/controller` 对象图差异，也不在
    `_ANEModel` 对象本身；缺口更像在 fresh `_ANEInMemoryModel` /
    mapper / virtual-client / lower driver map path 的 hidden accepted-state
    或 request-lowering state。
- 2026-06-17 21:57 新一轮 `ane_runtime_rehydrate_probe` machine-local 结果又把
  `0x12` 的语义收紧了一层：
  - `first_direct_base_model.map`：
    - `map_ok=1`
    - `eval_ok=1`
  - 紧接着同一进程、同一 `baseModel/program/mapper/controller/device` 上的
    `first_direct_base_model_repeat.map`：
    - 立刻变成 `Program IOSurfaces map failure (0x12)`
    - 但 `eval_ok=1`
  - 之后所有同 artifact loaded/fresh 路径：
    - `direct_base_model.map`
    - `prebaseline_loaded.map`
    - `prebaseline_loaded_repeat.map`
    - `baseline.map`
    - `baseline_repeat.map`
    - 全部都稳定 `0x12`
  - 这次还做了真正的 controller reopen，而不是先前那种
    `usecount 2 -> 1 -> 2` 的伪重启：
    - `prebaseline_loaded_restart` /
      `baseline_restart`
      都明确走到：
      - `stop[1]` 后 `usecount = 0`
      - `device = 0x0`
      - `start[0]` 后重新拿回非零 device 指针
      - `start[1]` 后 `usecount = 2`
    - 但 `*_after_restart.map` 仍然统一 `0x12`
  - 同一轮里 `second_loaded` 还出现了新的 side fact：
    - `compileWithQoS:options:error:` 直接失败为
      `_ANECompiler : ANECCompile() FAILED`
      / `InvalidMILProgram`
    - 所以当前不要再把 `second_loaded.map` 缺失解释成 map-path 差异；
      它这次根本没到 load/map 阶段
  - 当前最强结论已经不再是
    “fresh wrapper map 失败”，而是：
    - 同进程里第一次 direct-base map 可以成功
    - 成功一次后，后续 map 会进入稳定 `0x12`
    - 这个状态不会因为 controller 真正 `stop -> device nil -> start`
      而恢复
    - 因而 blocker 更像在 lower map path 的 process / client /
      device-global accepted-state、transaction/runtime table、
      或一次性 memory-map state，而不是 wrapper object graph
  - 2026-06-17 22:23 新增 request-lowering 对照后，这个结论又收紧一层：
    - `first_direct_base_model.pre_map.prepare`
      与
      `first_direct_base_model_repeat.pre_map.prepare`
      的 `mapping_params summary.hash`
      完全一致；
      差异只有 IOSurface ID / request 对象指针，不在
      `tailQ0/tailU32_0/tailU32_1/tailQ1`
      或总体 lowering 结构上。
    - `first_direct_base_model.mapper_unmap`
      也明确返回：
      - `ok=1`
      - `error=nil`
    - 因而当前没有证据支持：
      - “第二次失败是 request-lowering 参数变了”
      - “第一次成功后其实 mapper-level unmap 失败，状态没释放”
    - 当前更合理的主假设继续下压到：
      lower device/runtime table/process-global accepted-state
      或 lower memory-map bookkeeping。
  - `cacheInference=1` 当前也还没打开新口子：
    - 在已进入污染状态后再跑的
      `first_direct_base_model_cache_roundtrip.initial_map_yes`
      仍直接 `0x12`
    - 但 2026-06-17 22:42 新 probe
      `first_direct_base_model_txn_roundtrip`
      已把 `cacheInference=1` 放进“进程里的第一次成功 map”窗口，
      并拿到了更强事实：
      - `first_map_yes` 成功
      - request 在成功后拿到
        `transactionHandle = 0`
      - `first_mapper_unmap` 成功
      - 随后第二次继续走
        `cacheInference=1`
        且把上一轮 transaction 带回 request：
        - `second_map_yes` 也成功
        - request 上的 `transactionHandle`
          递增为 `1`
        - `second_mapper_unmap` 也成功
  - 这说明：
      - `0x12` 不是“第二次 map 必然失败”
      - 它更像是
        non-cacheInference / no-transaction
        路径缺失 lower transaction-aware map state
      - 带 transaction 的 cacheInference 路径可以连续成功，
        所以下一步主线应从
        `transaction/runtime table`
        继续下钻，而不是继续纠结 visible object graph
  - 2026-06-17 23:xx 新增 two-wrapper probe 后，
    问题又进一步收紧：
    - `two_wrapper_keepalive`：
      - wrapper1 第一次 map 成功
      - wrapper2 第一次 map 失败，`0x12`
    - `two_wrapper_release_first`：
      - 即使释放 wrapper1 后再建 wrapper2，
        wrapper2 第一次 map 仍失败，`0x12`
    - 而 `two_wrapper_diff` 显示：
      - wrapper1 成功 map/unmap 前后，
        `_ANEInMemoryModel` 原始内存不变
      - wrapper1 与 wrapper2 在 map 前相比，
        `_ANEModel/_ANEProgramForEvaluation/_ANEProgramIOSurfacesMapper`
        原始内存内容都一致
      - 唯一差异在 `_ANEInMemoryModel +0x18`
    - 本机 runtime introspection + IDA 已确认：
      - `_ANEInMemoryModel +0x18`
        对应 ivar `_hexStringIdentifier`
      - `initWithDesctiptor:` 会把
        `descriptor.hexStringIdentifier`
        写进这个 ivar，并统一抓取 `sharedConnection`
    - 因而当前主假设继续收窄成：
      - second wrapper failure 更像与 wrapper identity
        (`_hexStringIdentifier`) 相关的 lower map-owner / accepted-state key
      - 而不是 wrapper 内部可见 runtime graph、program、mapper、controller 内容差异
  - 2026-06-18 新增 `two_wrapper_hexid_alias` 进一步证伪单字段假设：
    - 直接把 wrapper2 的 `_hexStringIdentifier` 设成 wrapper1 同值后，
      wrapper2 的 first map 仍然是 `0x12`
    - 因而 `_hexStringIdentifier` 单字段本身不是足够条件；
      更像是更大 identity 组合中的一个成员，或者只是被 lower state 一并记账的标签
  - 2026-06-18 新 probe 又把 `0x12` 的触发条件收紧了一层：
    - `two_wrapper_identity_combo`：
      - wrapper1 只做 `map/unmap`，不做 `eval`
      - wrapper2 first map 直接成功
    - `two_wrapper_after_map_only`：
      - 复现同样结论：`map/unmap` 本身不会污染后续 fresh wrapper
    - `two_wrapper_after_map_eval`：
      - wrapper1 在成功 `map/unmap` 后再成功 `eval`
      - wrapper2 first map 立刻掉进稳定 `0x12`
    - `two_wrapper_txn_after_eval`：
      - wrapper1 先以 `cacheInference=1` 成功 map，拿到
        `transactionHandle=0`
      - 然后再成功 `eval`
      - wrapper2 即使带着这个 txn、也走 `cacheInference=1`，
        first map 仍然 `0x12`
    - 同轮把 `sharedConnection`、`program`、`controller`、
      `controller.device` 的 raw memory 都落盘后，wrapper1 eval 前后与
      wrapper2 pre-map 之间在这些可见对象上都没有变化
    - 当前更强结论：
      - 不是 second fresh wrapper 天生会失败
      - 不是 `map/unmap` 污染
      - 是一次成功 `eval` 之后，后续 fresh wrapper 的 map 路径进入了
        lower eval-side accepted-state / process-global runtime table 污染
      - 且这个污染点不在当前 probe 可见的
        `_ANEClient/_ANEProgramForEvaluation/_ANEDeviceController/device`
        原始对象内存里
  - 2026-06-18 新增 `two_wrapper_after_eval_only` 后，
    这条边界又收紧了一层：
    - wrapper1 不需要先显式 `map/unmap`
    - 只要先成功做一次 `eval`
    - wrapper2 first map 就会稳定进入 `0x12`
    - 因而当前最强表述是：
      `eval` 本身已经足够 author 那个污染状态；
      它不依赖前置 map 写出的 visible request/runtime state
  - 2026-06-18 再把 `two_wrapper_after_eval_only` /
    `two_wrapper_after_map_eval` / `two_wrapper_txn_after_eval`
    的 request-lowering 快照打开后，当前又多了一个排除项：
    - `request.signature_hash`
    - `prepareANEMemoryMappingParams summary`
    - `tailQ0/tailU32_0/tailU32_1/tailQ1`
    在 `eval` 前后都没有变化
    - `eval-only` 触发污染时，
      wrapper2 pre-map 的 lowering 也仍然是完全正常、可解释的
    - 因而当前没有证据支持
      “eval 改坏了 visible request-lowering / memory-mapping params”
    - 主怀疑继续下压到：
      `doEvaluateDirectWithModel...` /
      `processRequest` 成功侧带来的 lower runtime table /
      accepted-state side effect
  - 2026-06-18 新增 `same_wrapper_after_eval_map` /
    `two_wrapper_after_eval_only_txn0` 后，边界继续收紧：
    - `same_wrapper_after_eval_map`：
      同一个 wrapper 成功 `eval` 后，自己再 `map` 也会直接 `0x12`
    - `two_wrapper_after_eval_only_txn0`：
      在 eval-only 污染后，给后续 map 人工塞 `transactionHandle=0`
      也仍然 `0x12`
    - 这说明：
      - 污染不是 fresh-wrapper 专属
      - 也不是“少了一个手工 txn0”这么浅的原因
  - 同日静态 reverse 再确认：
    - `_ANEDeviceController start`
      通过 `ANEServicesDeviceOpen` 打开底层 device
    - `map` 路径在
      `___83-[_ANEProgramIOSurfacesMapper mapIOSurfacesWithModel:request:cacheInference:error:]_block_invoke`
      中调用 `device->vtable[0x38]`
    - `eval` 路径在
      `-[_ANEClient doEvaluateDirectWithModel:options:request:qos:error:]`
      / `processRequest...`
      中走另一条 device 间接调用（device vtable `+0x20`）
    - 在 `ANEServices.framework` 内已经确认：
      - `map` 对应
        `ANE::ANEServicesDevice::ANE_ProgramMemoryMapRequest(...)`
        -> `IOConnectCallMethod(selector=5)`
      - `unmap` 对应
        `ANE::ANEServicesDevice::ANE_ProgramMemoryUnMapRequest(...)`
        -> `IOConnectCallStructMethod(selector=6)`
      - `eval` driver request 对应
        `ANE::ANEServicesDevice::ANE_ProgramSendRequest(...)`
        -> `IOConnectCallAsyncMethod(selector=2)`
    - 因而当前最强主假设是：
      同一个 ANEServices device / runtime class 在 eval 槽位里 author 了状态，
      导致 map 槽位随后返回 `0x12`
  - 继续往 `ANEServices` 下钻后又多了两个 side fact：
      - `ANE::ANERequestReceiver::ProgramProcessRequest(sync)`
        成功后进入 `syncFrameDone(...)`，
        当前可见写回主要是 request-local / receiver-local bookkeeping：
        - request `status/programHandle/transid` 校验
        - pending count / cond signal
        - releaseRequestBuffers / 局部 callback
        没看到会显式清理后续 map 所需 lower state 的用户态写回
      - `ANE::ANEServicesDevice::ANE_CancelAllRequests()`
        当前是一个直接 `return 0` 的 stub，
        软件侧没有现成可用的“清场”实现
  - 2026-06-18 新增 `same_wrapper_after_async_eval_map` 后，
    这条边界又进一步收紧：
    - request 的 `completionHandler` 已成功安装并成功回调
    - 也就是说 eval 这次明确走了 async path，而不是 sync-only completion
    - 但 async eval 之后，同 wrapper 再 `map` 仍然直接 `0x12`
    - 因而 `syncFrameDone` 不是主嫌；
      污染更像在 `ProgramSendRequest` / device selector=2
      自身或其更低层完成路径上发生
  - 2026-06-18 新增 `loaded_eval_unload_reload_map` 后，
    public `unload/load` 也被排除了：
    - 成功 `eval`
    - 显式 `unloadWithQoS:error:` 成功
    - 随后 `loadWithQoS:options:error:` 也成功
    - 但再 `map` 仍然直接 `0x12`
    - 因而这层污染不会被 public unload/load 清掉；
      更像 process-global / device-global runtime state
  - 2026-06-18 新增严格串行 cross-process `A -> B` 后，
    这条边界再收紧一层：
    - 进程 A：
      `./ane_runtime_rehydrate_probe --case two_wrapper_after_eval_only`
      -> `wrapper1_eval=1`
      -> `wrapper2_map=0x12`
    - 确认进程 A 退出后，再单独启动进程 B：
      `./ane_runtime_rehydrate_probe --case two_wrapper_after_map_only`
      -> `wrapper1_map=1`
      -> `wrapper2_map=1`
    - 对应证据：
      - `mps/ANE/.ane_runs/csv/two_wrapper_after_eval_only_processA_serial_20260618.csv`
      - `mps/ANE/.ane_runs/csv/two_wrapper_after_map_only_processB_afterA_serial_20260618.csv`
    - 因而当前不要再把这层污染建模成
      “跨进程仍残留的 machine-global/device-global persistent state”；
      更准确的是：
      - 同进程内：
        `eval` 足以 author 一个 lower runtime state，
        后续 `map` 稳定 `0x12`
      - 跨进程：
        process exit 会把这层状态清掉
      - 所以当前 visible userland 层该判死的，
        是“同进程内清场/复位 control surface 不存在”，
        而不是“系统永久脏掉”
  - 2026-06-19 新增 `same_request_after_eval_map` 后，
    `request-local carrier` 这一层也可判死：
    - 同一个 `_ANERequest` 对象，
      `eval` 前后的 raw object memory hash 完全不变：
      `0xc8f5933a72c7979f`
    - 复用这个同一个 request 直接去 `map`，
      仍然稳定得到
      `Program IOSurfaces map failure (0x12)`
    - 对应证据：
      `mps/ANE/.ane_runs/csv/same_request_after_eval_map_20260619.csv`
    - 因而当前不要再把 blocker 建模成：
      - request 对象自身被 `eval` 原地改写
      - request-local `transactionHandle/sharedEvents/completionHandler`
        一类 carrier
    - 当前更合理的下一层只剩：
      - selector=2 打包后经
        `additional_params+0x60/+0x68 -> request+0x28/+0x30`
        这条 `{resource, process}` pair bridge
        下沉进入的 lower state
      - hidden handle / sidecar family
      - `resource+0x400d0` / `record+0x1b8` / `process+0x203fc`
        一类 registry / accepted-state family
  - 2026-06-19 当前 `Carrier` 阶段的静态焦点已进一步收紧：
    - `bootkc_memory_map_request_bridge_note.md`
      与
      `bootkc_request_pair_roles_probe.md`
      已共同确认：
      1. `InitialChecks`
         会写：
         `additional_params+0x60 = resource`
         `additional_params+0x68 = process`
      2. `ANERequest::init(...)`
         会把这对值复制到：
         `request+0x28 = resource`
         `request+0x30 = process`
      3. 后续 firmware send / builder
         会继续按 `{resource, process}` 角色消费这对值
    - 因而当前最值得继续追的不是
      request-local 普通 ivar，
      而是：
      `{resource, process}` pair bridge
      与更低的 registry / accepted-state family
  - 2026-06-19 对 `{resource, process}` pair bridge
    做了当前最小 runtime 交叉检查后，
    结论继续收紧：
    - 使用
      `same_request_after_eval_map_20260619_pair.csv`
      可见：
      同一个 `_ANERequest`
      在
      `eval` 前、
      `eval` 后、
      以及后续 `map -> 0x12`
      失败后，
      raw object `memory_summary` 完全不变
    - `memory_summary head`
      中对应 offset
      `0x28` / `0x30`
      的两个 qword
      也未出现变化
    - 因而当前没有证据支持：
      `eval` 会在 user-space request object 内直接改写
      这对 `{resource, process}` pair
    - 当前更合理的表述是：
      `{resource, process}` pair bridge
      已被确认是最具体的上层 bridge，
      但真正变化的 carrier
      更可能发生在它下沉后的 lower registry / accepted-state family，
      而不是 request object 内的可见 pair 值本身
  - 2026-06-19 在当前 `Carrier` 阶段，
    唯一下压目标已进一步收窄到：
    `resource+0x400d0`
    的 first-author / materializer gap
    - 依据：
      1. `{resource, process}` pair bridge
         已静态确认会进入更低 send / firmware 路
      2. `process+0x203fc`
         当前更像后续 load-type / recreate gate consumer，
         不是 pair bridge 最近的 first materializer
      3. `record+0x1b8`
         当前仍更像 replay / refresh 路线，
         也不是 pair bridge 最近的 first materializer
      4. `resource+0x400d0`
         仍保留明确的 first-author gap，
         并且是当前最接近 pair bridge 的 unresolved registry family
    - 因而下一轮若继续 `Carrier`，
      不再做
      `resource+0x400d0 / record+0x1b8 / process+0x203fc`
      的并列三选一，
      而是直接围绕
      `resource+0x400d0`
      first-author / materializer
      继续下压
  - 2026-06-19 现用 `.venv-capstone`
    重跑
    `ane_bootkc_resource_gate_first_author_probe.py`
    后，当前机器上的 first-author 负证据再次被直接落盘确认：
    - 新证据：
      `mps/ANE/.ane_runs/csv/ane_bootkc_resource_gate_first_author_probe_20260619.csv`
    - 当前结果与既有 note 一致并进一步提供 machine-local CSV：
      - constructor bulk-zero 只到 `self+0x40070`
      - visible load copy 只到 `0x40090..0x400a0`
      - visible mutable setup 只写：
        `0x400d8`
        `0x400e0`
      - target-covering exact store 仍只有：
        `ANEProgramResource::free -> clear resource+0x400d0`
    - 因而当前更强结论是：
      `resource+0x400d0`
      的 first-author gap
      不只是旧 note 的历史结论，
      而是当前机器重新验证过的 live negative
    - 同时结合
      `bootkc_resource_gate_preinit_boundary_probe.md`
      与
      `bootkc_resource_gate_host_stack_probe.md`
      的既有结论，
      当前更合理的下一轮唯一假设应是：
      缺失项已经不在 visible direct-store /
      bulk-copy /
      visible helper-depth surface，
      而在更深 registration / materializer helper
      或更低 runtime-owned phase
  - 2026-06-19 再用当前机器重跑：
    - `ane_bootkc_resource_gate_preinit_boundary_probe.py`
    - `ane_bootkc_resource_gate_host_stack_probe.py`
    之后，
    `resource+0x400d0`
    这条 first-author 负证据又收紧了一层：
    - 新证据：
      - `mps/ANE/.ane_runs/csv/ane_bootkc_resource_gate_preinit_boundary_probe_20260619.csv`
      - `mps/ANE/.ane_runs/csv/ane_bootkc_resource_gate_host_stack_probe_20260619.csv`
    - `preinit_boundary` 当前机器再次确认：
      1. `ANE_ProcessCreate_gated.cold.1`
         先读 `[resource+0x400d0]`
      2. 若该指针为 null，
         直接 branch away，
         不会 visible allocate / attach registry
      3. 只有 non-null 分支才调
         `OSArray::setObject(process)`
      4. 当前 H16 visible text
         仍无 non-free direct store /
         bulk-cover /
         same-function `OSArray::withCapacity -> direct sink`
         author
    - `host_stack` 当前机器再次确认：
      1. `AppleH16ANEInterface`
         只有 loads=45、stores=1(non_free=0)
      2. `AppleT8132ANEHAL`
         对 `resource+0x400d0`
         的 direct load/store/bulk/same-function author
         全为 0
      3. visible host H16/HAL stack
         唯一 target-covering direct store
         仍然只有
         `ANEProgramResource::free -> clear`
    - 因而当前最强 machine-local 结论已是：
      `resource+0x400d0`
      missing first author
      不在 current visible H16 direct/bulk surface，
      也不在 current visible HAL half，
      并且 `process_create_cold`
      只消费预先存在的 registry
    - 下一轮若继续 `Carrier`，
      更合理的唯一假设应继续下沉到：
      - daemon/service-side pre-reply bring-up window
      - 其之下的更低 runtime-owned materialization phase
      而不是继续在 visible host surface 内扫作者
  - 结合当前机器已有的
    `resource+0x400d0`
    线负证据，
    与
    `daemon_load_prereply_window_note.md`
    / `runtime_lower_next_layer_note.md`
    的既有结论，
    当前更合理的优先级已变成：
    1. daemon/service-side pre-reply bring-up
    2. 更低 runtime-owned materialization phase
    3. 最后才是已基本解释完的 receive/response/completion bookkeeping
  - 也就是说，
    当前长期目标在 `Carrier` 阶段的最佳下一窗口
    已不再是
    H16/HAL visible author surface，
    而是：
    `loadModel/createProgramInstance`
    成功 reply 之前的 bring-up / materialization 窗口
  - 2026-06-19 当前机器重跑
    `ane_daemon_static_probe.py`
    后，
    daemon/service-side pre-reply bring-up
    窗口也有了 fresh CSV 证据：
    - `mps/ANE/.ane_runs/csv/ane_daemon_program_create_state_chain.csv`
    - `mps/ANE/.ane_runs/csv/ane_daemon_load_reply_chain.csv`
    - `mps/ANE/.ane_runs/csv/ane_daemon_static_probe_summary.csv`
  - 当前机器再次确认：
    1. plain `loadModel` success reply
       只会在
       `createProgramInstanceForModel...`
       成功之后才读出并 reply：
       `programHandle`
       `intermediateBufferHandle`
       `queueDepth`
    2. `createProgramInstanceForModel...`
       不是单一步骤，
       而是明确的 multi-stage state machine：
       - create stage
       - optional prepare stage
       - failure family-4 / family-5 teardown path
       - only after settle 才发生 metadata writeback
    3. 因而当前最佳窗口已不只是抽象的
       “daemon/service-side pre-reply bring-up”，
       而是更具体的：
       `_ANEProgramForLoad createProgramInstanceForModel...`
       内部的
       create/prepare state machine
  - 下一轮若继续长期目标，
    最合理的唯一假设应围绕：
    `createProgramInstanceForModel...`
    成功前到底还缺哪一层 lower materialization /
    accepted-state coherence，
    而不是再回头扫 load reply ABI 或后置 request wrapper
  - 2026-06-19 再把
    plain daemon create/prepare
    与
    ANEServices selector contract
    做 current-machine join 后，
    这条结论又能再收紧一层：
    - 直接运行：
      `python3 mps/ANE/experiments/ane_daemon_program_lower_gate_join.py`
    - 新证据：
      - `mps/ANE/.ane_runs/csv/ane_daemon_program_lower_gate_join.csv`
      - `mps/ANE/.ane_runs/json/ane_daemon_program_lower_gate_join_verdict_20260619.json`
    - 当前机器确认：
      1. create stage
         仅可见：
         `selector 3 / _ANEServicesProgramCreate`
         + `create_status_zero_required`
      2. post-create
         仅新增：
         `program.programInstance != nil`
         与
         `skipPreparePhase`
         分支，
         没有新的 visible lower publish gate
      3. prepare stage
         仅可见：
         `selector 4 / _ANEServicesProgramPrepare`
         + `prepare_status_zero_required`
      4. prepare 失败时
         只会进一步走：
         `selector 6 / _ANEServicesProgramDestroy`
      5. 因而在 current-machine visible daemon join 里，
         create/prepare 成功
         与 metadata writeback
         之间没有额外 daemon-side publish gate
    - 当前最佳表述应更新为：
      若还存在
      accepted-state / publish coherence
      缺口，
      它已不再位于
      visible daemon plain-load
      的 create/prepare 之外，
      而只能落在：
      - selector-4 prepare 内部
      - 或更低 runtime-owned materialization phase
  - 2026-06-19 再把
    selector-4 prepare
    这条 current-machine visible surface
    单独做 boundary verdict 后，
    这条结论又能再收紧一层：
    - 新证据：
      - `mps/ANE/.ane_runs/json/selector4_prepare_boundary_verdict_20260619.json`
      - `mps/ANE/experiments/results/selector4_prepare_state_boundary_note.md`
      - `mps/ANE/experiments/results/current_control_layer_blocker_note.md`
    - 当前机器确认：
      1. selector-4
         是
         `wrapper+0x98`
         的 first visible writer
      2. selector-4 success
         会清
         `payload+0xd98`
         并回写
         `payload+0xd78..0xd97`
      3. 但 raw selector-4
         在 live handle / queue-depth patch
         后仍稳定
         `0xe00002c2`
      4. 所以剩余 gap
         不能再建模成：
         “还差一个 visible wrapper field patch”
         或
         “selector-4 自身就是 final accepted-state author”
    - 当前最佳表述应更新为：
      selector-4
      是 real visible state transition /
      first visible writer，
      但不是 current-machine
      可恢复的 final accepted-state author；
      剩余 blocker
      仍在其下方的
      device-side accepted-state /
      materialization gate
  - 2026-06-19 再补上
    `prepareChainingRequest:qos:qIndex:statsMask:error:`
    的 current-machine IDA 窄事实后，
    这条结论还能继续收紧：
    - 当前机器确认：
      1. `0x1000081dd`
         不做
         publish /
         accepted-state /
         result writeback
      2. 它只做：
         chainingRequest validate
         + input/output/signal event 枚举
         + 读取
           `programHandle/procedureIndex/fwEnqueueDelay/programInstance`
         + 经
           `controller.device`
           发
           `prepareChainingWithModel:options:chainingReq:qos:withReply:`
      3. 它的可见 decisive gate
         只剩：
         `validate`
         与
         daemon XPC reply code
    - 因而当前最佳表述应再更新为：
      `prepareChainingRequest...`
      也不是 current-machine
      可恢复 accepted-state author，
      而只是 wrapper-side request construction + XPC barrier；
      当前 `Carrier` 阶段最强下一目标
      应正式切到：
      daemon-side
      `-[_ANEServer prepareChainingWithModel:options:chainingReq:qos:withReply:]`
      或其下方更低 accepted-state/materialization gate
  - 2026-06-19 再补完
    daemon-side
    `-[_ANEServer prepareChainingWithModel:options:chainingReq:qos:withReply:]`
    的 current-machine IDA 窄事实后，
    这条结论还能继续收紧：
    - 新证据：
      - `mps/ANE/.ane_runs/json/daemon_preparechaining_boundary_verdict_20260619.json`
    - 当前机器确认：
      1. 该函数不做
         accepted-state /
         publish /
         reply payload writeback
      2. 它只做：
         XPC audit
         + QoS->queueIdx
         + per-QoS `dispatch_semaphore_wait(30s)`
         + `_ANEProgramCache programForConnection:model:bundleID:`
         + 调
           `[prog prepareChainingRequest:qos:qIndex:statsMask:error:]`
      3. 失败时
         只会：
         timeoutError
         或
         removeProgramForConnection:model:bundleID:
         后转发 `(ok,error)` reply
      4. 它的 decisive gate
         只剩：
         semaphore timeout
         与 delegated program-level BOOL/error
    - 因而当前最佳表述应再更新为：
      daemon-side prepare handler
      也不是 current-machine
      可恢复的 final author，
      而只是 server-side XPC/semaphore/cache gate；
      当前 `Carrier` 阶段最强下一窗口
      应正式切到：
      delegated program/device path
      的真实实现所在二进制
      （优先 `ANEServices.framework` /
      `ANECompiler.framework`）
    - 当前补充事实：
      本轮主线程尝试
      `ida-pro-mcp.idb_list`
      时出现
      `Transport closed`，
      说明下一轮若要继续静态下钻 delegated binary，
      需要先恢复对应 IDA transport / session；
      这影响的是
      “继续往下钻”
      的执行面，
      不影响本轮
      “server-side handler 不是 final author”
      的结论本身
  - 2026-06-19 再补一轮当前机器执行面核对后，
    transport 层 blocker 也已压实：
    - 新证据：
      - `mps/ANE/.ane_runs/json/ida_transport_closed_evidence_20260619.json`
    - 当前机器确认：
      1. `ANECompiler.i64`
         `AppleNeuralEngine.i64`
         与
         `ANEServices`
         路径都存在
      2. 本地仍有
         `idalib-mcp --stdio`
         与多个
         `ida_pro_mcp.idalib_server`
         进程存活
      3. `idalib-mcp --help`
         本机可正常执行
      4. 但当前会话里的
         `ida-pro-mcp.idb_list`
         `ida-pro-mcp.idb_open(...)`
         仍统一返回
         `Transport closed`
    - 因而当前最佳表述应再更新为：
      delegated binary
      继续静态下钻的直接 blocker
      不是缺少二进制或本地可执行损坏，
      而是当前会话的
      `ida-pro-mcp` transport / session；
      这不影响当前
      “server-side prepare handler 不是 final author”
      的结论，
      但会成为下一轮继续下钻
      `ANEServices.framework` /
      `ANECompiler.framework`
      前的唯一前置动作
  - 2026-06-19 再把
    `ANEServices`
    本体复制到
    `/private/tmp/ANEServices_arm64e`
    并重试后，
    这条 blocker 又能再收紧一层：
    - 新证据：
      - `mps/ANE/.ane_runs/json/aneservices_local_copy_ready_20260619.json`
    - 当前机器确认：
      1. `ANEServices`
         是可正常读取的 292K arm64e Mach-O
      2. 可成功复制到
         `/private/tmp/ANEServices_arm64e`
      3. `file`
         `otool -hv`
         都能正常读取副本
      4. 但当前会话里对
         `/private/tmp/ANEServices_arm64e`
         的 `ida-pro-mcp.idb_open`
         仍返回
         `Transport closed`
    - 因而当前最佳表述应再更新为：
      delegated binary
      继续静态下钻的 blocker
      已经不是 SIP /
      framework 原始路径 /
      binary 可读性，
      而只是当前会话的
      `ida-pro-mcp` transport / session；
      transport 一旦恢复，
      下一跳就直接是
      `/private/tmp/ANEServices_arm64e`
  - 2026-06-19 当前机器再补上一条
    不依赖 IDA MCP 的本地 Mach-O 证据链后，
    delegated 真身这层也已经落死：
    - 新证据：
      - `mps/ANE/.ane_runs/json/selector9_delegated_impl_local_macho_verdict_20260619.json`
    - 当前机器确认：
      1. `programInstance` vtable slot `+0x8`
         已由现有 runtime-chain
         映射到
         `_ANEServicesProgramChainingPrepare`
      2. 本地 `nm`
         在
         `/private/tmp/ANEServices_arm64e`
         中直接命中：
         - `_ANEServicesProgramChainingPrepare`
         - `ANE::ANEServicesDevice::ANE_ProgramChainingPrepare`
      3. 本地 `otool -tvV`
         直接显示：
         `_ANEServicesProgramChainingPrepare`
         调
         `ANE::ANEServicesDevice::ANE_ProgramChainingPrepare`
      4. 同一条本地反汇编证据链
         又确认它最终发
         selector 9
         `IOConnectCallStructMethod`
         （outer input `0xae30`，output `0x18`）
      5. 当前机器又进一步压实：
         - `_ANEServicesProgramChainingPrepare`
           位于
           `0x19e6a63cc`
         - `ANE::ANEServicesDevice::ANE_ProgramChainingPrepare`
           位于
           `0x19e69d668`
         - wrapper 在
           `0x19e6a6a08`
           调该 C++ 实现
         - 该 C++ 实现在
           `0x19e69d768`
           发 selector #9
           `IOConnectCallStructMethod`
    - 因而当前最佳表述应再更新为：
      delegated 真身是不是 `ANEServices`
      这一层已被 current-machine
      本地 Mach-O 证据 `confirmed`；
      剩余 blocker
      已继续下沉到
      selector-9
      更低 driver / bootkc
      accepted-state / materialization semantics
  - 2026-06-19 当前恢复后的
    `ida-pro-mcp`
    session 又补出一条更细的执行面事实：
    - 新证据：
      - `mps/ANE/.ane_runs/json/ida_session_unstable_evidence_20260619.json`
    - 当前机器确认：
      1. `idb_list`
         已能看到
         `aneservices_arm64e`
         `aned_arm64e`
         两个非空 session_id
      2. `server_health`
         也能返回
         `status=ok`
      3. 但真正查询
         `analyze_function`
         会直接报
         `Worker for session 'aneservices_arm64e' is not reachable`
      4. `xref_query` / `disasm`
         又会报
         `Session not found`
    - 因而当前最佳表述应再更新为：
      当前 IDA blocker
      已从
      `Transport closed`
      收紧成
      session reachability unstable；
      这不影响已拿到的
      `ANEServices`
      delegated 真身结论，
      但会限制继续用 MCP
      往下压
      selector-9
      更低语义
      与 program vtable
      更早来源二进制
- 当前历史基线对比不能再依赖“默认参数等价”：
  `private_ane_fused_mask_estimator_max_outputs` 的当前默认值已与旧基线不同，
  不显式固定为 `2` 时会触发不同 handle family，并污染结论。
- fixed cache tmpdir 的主要大头 `file_write/content-verify` 已被确认并压下去，
  当前主阻塞已转到：
  - transformer eval / pre-eval
  - axis pack / readback
  - load_qos
  - 以及 `load_or_compile_wall` 与 native `bridge_profile_total_sec` 之间
    仍未解释的 Python/ctypes 侧 gap
- 在当前最好 global-bridgeprofile 结果中：
  - `transformer.load_or_compile = 10.229s`
  - `transformer.bridge_profile_total = 3.757s`
  - 差值约 `6.47s`
  说明剩余 compile/load 开销并不主要在 ANE native compile/load 内部，
  而在桥调用前后的 Python/ctypes/materialization 路径。
- public client file-load 仍只打通了 STFT 一类 source MIL；真实 weighted
  transformer segments (`pre/gate/ffn`) 在“原始多权重文件”形态下仍然全部
  `fast_load_fallback=1`，并已定位到 translator 原因：
  `Blob storage must be backed by only one weight file.`
- 单一 packed weight file 已把 weighted `loadModel` / cache-hit 打通，
  但不同 transformer 子段的行为已明显分化：
  - `pre`: 需要三输出 request，当前 one-output 管线不匹配
  - `ffn`: 已可直接 packed public compile/load/eval
  - `gate`: compile/load 可部分成功，但 eval 仍失败
  这意味着当前阻塞已经进一步下沉到：
  - `pre` 的 runtime contract 改写问题
  - `gate` 的 packed runtime/eval 语义
  - 而不是单一的 “所有 weighted packed eval 都不行”
- `runtime_clone` fast path对当前 `test_clean.m4a` 基线形态的直接收益有限：
  当前较好基线是 `chunk_batch_size=4` 且只有 1 个 batch，大多数 handle 在进程内
  只出现一次；这一点目前是基于 trace/shape 的推断，尚未完成 full-audio 量化复测。
- 2026-06-12 新增的 rebuilt wrapper-augmentation 证据已把 runtime 语义再收窄一层：
  - `mps/ANE/experiments/artifact_replay` 已补 `out_fnv1a64` 输出，且保持与
    `ane_client_options_probe` 相同的 LCG 输入填充。
  - 对原始 private in-memory 路：
    - `weighted_pre`：
      `./artifact_replay --artifact benchmark_results/private_ane/weighted_fresh_pack_pre_1781215248 --input-bytes 32768 --output-bytes 65536`
      -> `out_fnv1a64=11324685616637522373`
    - `weighted_ffn`：
      `./artifact_replay --artifact benchmark_results/private_ane/weighted_fresh_pack_ffn_1781216020 --input-bytes 32768 --output-bytes 32768`
      -> `out_fnv1a64=9230850811434127481`
  - 对 augmented wrapper 路：
    - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_pre/eval_probe_rebuilt.csv`
    - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_ffn/eval_probe_rebuilt.csv`
    - `modelAtURL:key:` + `kANEFModelType = kANEFModelMIL` 两者 hash 与
      `artifact_replay` 完全一致：
      - `pre = 11324685616637522373`
      - `ffn = 9230850811434127481`
    - 这说明当前“wrapper + source-root companion + MIL load/eval”在这两个真实
      transformer segment 上已经不只是“能 eval”，而是对 private in-memory
      baseline 数值对齐。
  - 但 `weighted_pre` 上，`modelAtURLWithSourceURL:...cacheURLIdentifier:` 构造的
    `_ANEModel` 仍给出不同 hash：
    - `8685636208025030777`
    - 同一 wrapper root、同一输入下与 private baseline 不一致。
    - 这说明 `cacheURLIdentifier` 相关 model 构造/加载路径对 `pre` 不是数值中性的，
      当前 bridge/原型不要把它当成无害字段。
- 2026-06-12 新增的 fresh lifecycle + runtime-state 插点进一步解释了
  first-pass / second-pass 行为：
  - 证据：
    - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_pre/fresh_lifecycle_rebuilt.csv`
    - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_ffn/fresh_lifecycle_rebuilt.csv`
    - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_pre/cacheid_fresh.csv`
    - `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_pre/second_lifecycle_rebuilt.csv`
  - 在 fresh wrapper root 首次进入时：
    - `empty compile/load`：
      - `state: 1 -> 5`
      - `programHandle = 0`
      - `cacheURLIdentifier = nil`
    - `precompiled compile`：
      - `state = 2`
      - `programHandle = 0`
      - `cacheURLIdentifier = nil`
    - `precompiled load`：
      - `state = 5`
      - `programHandle = 0`
      - `cacheURLIdentifier = nil`
    - `MIL compile`：
      - `state = 2`
      - `programHandle = 0`
      - 已第一次生成非空 `cacheURLIdentifier`
    - `MIL load`：
      - `state = 3`
      - `programHandle != 0`
      - `cacheURLIdentifier` 保持同一个 compiled-cache id
  - 这说明对 wrapper directory root：
    - `PreCompiled compile success != loadable runtime handle`
    - 首次真正把 wrapper root 变成可复用 runtime/cached state 的关键动作是
      `MIL compile + MIL load`
- 2026-06-12 新增的 `AppleNeuralEngine.i64` 静态事实与上述动态结果一致：
  - `+[_ANEVirtualClient shouldUsePrecompiledPath:options:shouldUseChunking:chunkingThreshold:]`
    只有在以下条件同时满足时才返回真：
    - `kANEFModelType == kANEFModelPreCompiled`
    - `modelURL` 存在且是 file path，不是目录
    - 文件后缀为 `.hwx`
  - 因而当前 augmentation wrapper 的“目录根 + model.hwx/model.src/model.retain”
    形式天然不属于这条真正的 precompiled load 路。
  - `-[_ANEVirtualClient loadModel:options:qos:error:]`：
    - 如果输入 model 没有 `cacheURLIdentifier`，会额外构造并提交
      `stru_1F042C180` 对应的 serializer blob；
    - 如果输入 model 已有 `cacheURLIdentifier`，则改为把该 cache id 直接放入
      请求字典。
  - `-[_ANEVirtualClient compiledModelExistsFor:]`：
    - 当 daemon 返回 compiled hit 时，会把返回字典里的
      `cacheURLIdentifier` 回写到 `_ANEModel`。
  - 结合 `fresh_lifecycle_second.csv` 的 second-pass 行为，当前最合理的解释是：
    - first-pass `MIL load` 先把 compiled cache 建起来；
    - second-pass `compiledModelExistsFor:` / `compileModel(precompiled)` 让
      model 重新拿到 cache id；
    - 随后空 options `loadModel` 就能命中已编译状态；
    - 但这仍不等于 public `.hwx` precompiled file-load 语义已经正确。
- 2026-06-12 新增的 bridge wrapper-route 原型已经给出端到端正向证据：
  - [ane_bridge.m](/Volumes/2T/pymss/mps/maderix_ANE/bridge/ane_bridge.m)
    新增了 `ANE_BRIDGE_CLIENT_FILE_WRAPPER=1` 路线：
    - 先把 packed single-file source root 写成：
      - `model.mil`
      - `net.plist`
      - `data`
      - `weights/packed.bin`
    - 再用 compiler-service 生成 wrapper
      `model.hwx/model.src/model.retain`
    - warm 路直接走 `modelAtURL:key:` + compiled-state / empty load
    - 不再预置 `cacheURLIdentifier`
  - 实现中已确认一个关键坑：
    - compiler-service 的 `tmp/clone/output` 不能放进 source root 里，
      否则 clone 会把 `__wrapper_clone` 之类目录递归带进 source tree，
      并让 wrapper 生成失败。
    - 当前原型已改为把 wrapper work dir 放到 source root 外侧 sibling，
      只把 `model.hwx/model.src/model.retain` 回填回来。
  - 当前 warm-route smoke：
    - `benchmark/private_ane_real_block_probe.py`
      `axis=time batch=1 seq=64 valid_seq=48 blocks=1 gelu=EXACT seed=5678`
      已跑通，误差：
      - `mean_abs = 0.00242822128`
      - `max_abs = 0.0151367188`
    - 同时逐段 profile 已确认：
      - `pre/gate/ffn` 三段都命中
        `bridge_profile_route = load_cache_client_wrapper_warm`
  - `test_clean.m4a` 的 cold wrapper populate 仍然很重：
    - `benchmark_results/private_ane/test_clean_wrapper_route_onechunk.private_ane_child/parent_watchdog_failure.json`
    - 首轮 `mask_batch` 曾耗时约 `165s`，最终被 native supervisor 以 `timeout` 杀掉
    - 说明当前 prototype 的主要收益在 repeated load/compile，不在 cold populate
  - 但 warm cache replay 已经明显过线：
    - `benchmark_results/private_ane/test_clean_wrapper_route_onechunk_rerun2.json`
      - warm replay
      - `seconds = 24.520`
      - `chunks = 2`
      - `chunk_batch_size = 1`
    - `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch1.json`
      - explicit `--full-audio`
      - `seconds = 47.197`
      - `chunks = 4`
      - `chunk_batch_size = 1`
    - `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4.json`
      - explicit `--full-audio`
      - `seconds = 28.340`
      - `chunks = 4`
      - `chunk_batch_size = 4`
      - 这是当前已拿到的最快 `test_clean.m4a` private ANE 结果
  - 与 `mlx_full` 的整链对照也已补齐：
    - `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4_vs_mlx.json`
    - `baseline backend = mlx_full seconds = 12.131`
    - `private_ane seconds = 30.186`
    - waveform diff:
      - `mean_abs = 0.0007473685`
      - `p99_abs = 0.0036775926`
      - `max_abs = 0.0117839351`
    - 这说明当前 wrapper-route batch4 warm-run 不只是更快，而且整链输出仍与
      `mlx_full` 高度接近
  - 当前 warm-run 仍有剩余热点：
    - `transformer.load_qos` 仍是主要大头
    - `bridge_profile_file_write_sec` 在 warm route 上已经显著下降到很低，
      主要收益来自避免 repeated compile/load，而不是继续压文件写入
    - `test_clean_wrapper_route_fullaudio_batch4.json` 中：
      - `transformer.bridge_profile_load_qos_sec ≈ 1.36s`
      - `transformer.bridge_profile_file_write_sec ≈ 0.010s`
    - 这意味着下一步再想继续降，重点不该再放在 file-write，
      而应放在 cold wrapper populate 与 warm load_qos 本身
  - 2026-06-12 新增的 warm-load 收敛事实：
    - `compiledModelExistsFor` 本身不是热点。
      - 对真实 transformer wrapper root 的 probe：
        - `compiled_exists_sec ≈ 0.00015s ~ 0.00035s`
        - 量级远小于当前 benchmark 里的 `load_qos`
      - 证据：
        `benchmark_results/private_ane/wrapper_warm_load_probe_external_time_root.json`
    - 当前 directory-root wrapper route 不是“真正的 precompiled path”。
      - `AppleNeuralEngine.i64` 静态已确认：
        `+[_ANEVirtualClient shouldUsePrecompiledPath:options:shouldUseChunking:chunkingThreshold:]`
        只有在：
        1. `options[kANEFModelType] == kANEFModelPreCompiled`
        2. `modelURL.path` 以 `.hwx` 结尾
        时才会走 precompiled/file path。
      - 对 directory root，它只会返回 false，不会进入 `.hwx` file-model
        fast connection。
    - 直接把现有 wrapper root 切到 `.hwx file URL + sourceURL` 仍然不够。
      - 在真实 transformer wrapper root 上，
        `modelAtURLWithSourceURL(file_hwx, source_dir, key="", cacheId=nil)` +
        `loadModel(options={kANEFModelType=kANEFModelPreCompiled})`
        会快速失败：
        - `Code=6`
        - `Program load failure (0x170004)`
      - 即使先做 `compiledModelExistsFor` 也一样失败。
      - 证据：
        `benchmark_results/private_ane/wrapper_warm_load_probe_external_time_root.json`
  - 2026-06-12 新增的 tmpdir/path 结论：
    - 把 `private_ane_cache_tmpdir` 从当前 benchmark 默认外置盘路径切到
      `/tmp` 不是现成收益。
    - `test_clean.m4a` full-audio batch4：
      - internal tmpdir cold first-run：
        - `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4_tmp_internal.json`
        - `seconds = 142.387`
        - `transformer.bridge_profile_route = load_cache_client_wrapper_mil`
        - `transformer.bridge_profile_load_qos_sec ≈ 99.444s`
      - internal tmpdir second warm-run：
        - `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4_tmp_internal_rerun.json`
        - `seconds = 55.524`
        - `transformer.bridge_profile_route = load_cache_client_wrapper_warm`
        - `transformer.bridge_profile_load_qos_sec ≈ 21.758s`
      - 仍显著差于当前最好外置盘 warm-run：
        - `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4.json`
        - `seconds = 28.340`
        - `transformer.bridge_profile_load_qos_sec ≈ 1.360s`
    - 因而当前不要把 `TMPDIR/ANE_BRIDGE_TMPDIR` 迁到系统盘当成默认优化方向。
  - 2026-06-12 新增的 cold MIL route 对照：
    - 在真实 transformer wrapper root 的 clone 上：
      - `loadModel(MIL)` 直接成功：
        - `first_load_sec ≈ 0.124s`
      - `compileModel(MIL) + loadModel(MIL)` 也成功：
        - `compile_sec ≈ 0.107s`
        - `first_load_sec ≈ 0.017s`
        - 总量级与直接 `loadModel(MIL)` 接近
    - 说明当前 cold wrapper route 里，单纯去掉 `compileModel(MIL)` 不是确定性大收益。
    - 证据：
      `benchmark_results/private_ane/wrapper_warm_load_probe_external_time_root.json`
  - 2026-06-12 新增的 `.hwx file-model` 收敛事实：
    - 新 probe：
      `benchmark_results/private_ane/precompiled_file_route_probe_time_root_v4.json`
    - 在同一个 tmp work root 上，先用 working `MIL compile/load` 生成真实：
      - `cacheURLIdentifier`
      - `modelAttributes`
      - `string_id`
    - 然后对 `.hwx file-model` 试了这些高层组合：
      - factory:
        - `modelAtURL:key:` on `model.hwx`
        - `modelAtURL:key:modelAttributes:` on `model.hwx`
        - `modelAtURLWithSourceURL(... cacheId=nil)`
        - `modelAtURLWithSourceURL(... cacheId=set)`
        - `modelAtURLWithSourceURL(... identifierSource=1/2, cacheId=set)`
        - `modelAtURLWithCacheURLIdentifier(...)`
      - options:
        - `kANEFModelType = kANEFModelPreCompiled`
        - `kANEFModelHasCacheURLIdentifierKey = YES`
        - plain `"aotCacheUrlIdentifier" = <real cache id>`
        - constant `kANEFAOTCacheUrlIdentifierKey = <real cache id>`
        - `seed_attrs`
        - `seed_string_id`
      - 并补做 `compileModel(precompiled)` 后再 `loadModel(precompiled)`。
    - 结果：
      - 成功数仍然 `0`
      - 当没有 `kANEFModelHasCacheURLIdentifierKey` 时，
        常见失败面是：
        - `Code=6`
        - `Program load failure (0x170004)`
      - 当带 `kANEFModelHasCacheURLIdentifierKey` 时，
        常见失败面变成：
        - `load_err = nil`
        - `state = 5`
        - `programHandle = 0`
      - 即使：
        - `compiled_exists_before = true`
        - constructor 已带真实 `cacheURLIdentifier`
        - options 已带 `kANEFAOTCacheUrlIdentifierKey`
        - `modelAttributes` / `string_id` 已从 working MIL route 注入
        也仍然失败。
    - 这说明当前阻塞已强烈指向：
      - 不是高层 `cache-id`
      - 不是高层 `aot-cache-id`
      - 不是高层 `modelAttributes`
      - 也不是单纯 `string_id`
      - 更像是 file-model 所需的 retained companion / program-definition /
        lower request author 语义仍未满足
  - 2026-06-12 新增的 `aned` 静态事实：
    - 已可直接打开并分析本机 `/usr/libexec/aned`（复制后 `aned_bin.i64`）。
    - `-[_ANEServer loadModel:sandboxExtension:options:qos:withReply:]`
      已确认存在明确的两路分支：
      - 只有在 `existsInCache == 0` 且 `isPreCompiled == 0` 时，
        才会走
        `compileAsNeededAndLoadCachedModel:csIdentity:sandboxExtension:options:qos:modelFilePath:modelAttributes:error:`
      - 只要 `existsInCache == 1` 或 `isPreCompiled == 1`，
        就会先 `consumeSandboxExtension`、`memoryMapModelAtPath:isPrecompiled:modelAttributes:`
        ，然后直接调用
        `createProgramInstanceForModel:...cacheUrlIdentifier:aotCacheUrlIdentifier:...`
      - 这意味着当前失败的 `.hwx file-model precompiled load`
        在 daemon 侧不会再回到 compiler-service compile-as-needed，
        而是直接卡在 lower create-program 路。
    - `-[_ANEModelCacheManager cacheURLIdentifierForModel:useSourceURL:withReply:]`
      已确认：
      - 若 `useSourceURL` 或 `identifierSource == 2`，用 `sourceURL.path`
      - 否则用 `modelURL.path`
      - 再做 `hex(path) + hex(key)` 生成 cache id
    - `-[_ANEModelCacheManager URLForModel:bundleID:useSourceURL:forAllSegments:aotCacheUrlIdentifier:]`
      已确认：
      - 若 model 已有 `getCacheURLIdentifier`
      - 则优先按这个 cache id 生成 cache root
      - 不再回退依赖原始 `modelURL.path`
    - 这与新的 dynamic probe 一起说明：
      当前已经越过 “cache root / path / cache-id 算法” 这一层；
      即使 file-model 已带真实 cache id，仍会在后续 `createProgramInstance`
      侧失败。
    - `-[_ANEProgramForLoad createProgramInstanceForModel:...cacheUrlIdentifier:aotCacheUrlIdentifier:...]`
      的 `dispatch_sync` block 真身已经定位到：
      - `aned_bin` `0x10000307f`
    - 2026-06-14 新增
      `daemon_program_lower_gate_join_note.md`
      与
      `ane_daemon_program_lower_gate_join.csv`
      后，这条 plain daemon runtime 路
      可以更明确地和 selector 家族对齐：
      - create stage：
        - `device` vtable `+0x10`
        - daemon `0x1000035D0`
        - 对应
          `_ANEServicesProgramCreate`
          -> selector 3
          -> input `0xd88`
          -> output `0xac738`
        - 失败后归一化成
          family-4
          `(low16=4, high16=w20)`
      - post-create：
        - 只有在
          `program.programInstance != nil`
          之后才看
          `skipPreparePhase`
        - 这说明
          `skipPreparePhase`
          只能绕过 selector-4 prepare，
          不能绕过 selector-3 create
      - prepare stage：
        - `programInstance` vtable `+0x0`
        - daemon `0x1000039C0`
        - 对应
          `_ANEServicesProgramPrepare`
          -> selector 4
          -> inout `0x38`
      - prepare failure teardown：
        - `programInstance` vtable `+0x18`
        - daemon `0x100003A28`
        - 对应
          `_ANEServicesProgramDestroy`
          -> selector 6
          -> input `0x10`
          -> no output
        - 失败后归一化成
          family-5
          `(low16=5, high16=w21)`
      - 这把 daemon plain runtime path
        更准确地压成：
        selector-3 create
        -> optional selector-4 prepare
        -> selector-6 destroy on prepare failure
      - 因而当前 `.hwx precompiled`
        `0x170004`
        与 local selector-3 / selector-4
        probe 的关系也能更硬：
        - 它们已经在同一 lower gate family 上说话
        - 当前 blocker 更像在 selector-3/4
          之下的 lower accepted-state /
          request author / publish coherence
          而不是 daemon 自己独有的一层
    - 当前可确认的 marshalling 语义：
      - outer `loadModel...` -> `createProgramInstance...` 的关键参数来源：
        - `enablePowerSaving`
          - 默认来自
            `_ANEDeviceInfo isExcessivePowerDrainWhenIdle` /
            `_ANEXPCServiceHelper allowAggressivePowerSavingFor:`
          - 可被 `kANEFEnablePowerSavingKey` 覆盖
        - `modelIdentityStr`
          - 来自 `kANEFModelIdentityStrKey`
        - `enableLateLatch`
          - 来自 `kANEFEnableLateLatchKey`
        - `skipPreparePhase`
          - 来自 `kANEFSkipPreparePhaseKey`
        - `aotCacheUrlIdentifier`
          - 来自 `kANEFAOTCacheUrlIdentifierKey`
        - `optOutOfModelMemoryUnwiring`
          - 来自 `kANEFKeepModelMemoryWiredKey`
      - `block+0x38`:
        - `modelFilePath`
        - 长度上限 `0x400`
        - 拷到本地 path buffer
      - `block+0x40`:
        - `modelIdentityStr`
        - `UTF8String/length`
        - 长度上限 `0x100`
      - `block+0x48`:
        - 一条 `UTF8String/length`
        - 长度上限 `0x400`
        - 从当前调用签名与 outer capture 对位，强指向 `aotCacheUrlIdentifier`
      - `block+0x50`:
        - 另一条 `UTF8String/length`
        - 长度上限 `0x400`
        - 强指向 `cacheUrlIdentifier`
      - `block+0x30`:
        - 不是 cache/path，而是 `modelToken`
        - 会取：
          - `teamIdentity`
          - `csIdentity`
        - 并调用 `copySHA256For:toBuffer:` 各自做 SHA 填进 lower request
      - 随后会：
        - `self -> controller -> device`
        - 对 `device` 做一次 vtable `+0x10` 调用
        - 参数包含前面构造好的大 request struct
    - 这进一步说明：
      当前 `.hwx file-model` 阻塞已非常像是
      `modelToken / ProgramDefinition / retained companion`
      这层 lower request author 语义缺失，而不是高层 cache-id 或 path。
  - 2026-06-12 新增的 direct-create 参数矩阵结果：
    - 结果文件：
      `benchmark_results/private_ane/precompiled_file_route_probe_time_root_v5.json`
    - 选了两个最贴近 direct precompiled create-path 的 factory：
      - `file_source_cache_set`
      - `file_source_id2_cache_set`
    - 额外补测了 `loadModel...` 静态已确认消费的 options：
      - `kANEFModelIdentityStrKey`
        - 候选值：
          - `""`
          - `ane_precompiled_file_route_probe_root/model.hwx`
          - 完整 `.hwx` path
          - 真实 `cacheURLIdentifier`
          - decimal `"0"`（当前 bootstrap `string_id`）
      - `kANEFSkipPreparePhaseKey`
      - `kANEFEnableLateLatchKey`
      - `kANEFEnablePowerSavingKey`
      - `kANEFKeepModelMemoryWiredKey`
    - 新结论：
      - `has_cache_flag + aot_const + seed_attrs + seed_string_id`
        这一整族在 22 个 direct rows 上全部保持：
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
      - 也就是说，这批 direct-create 真正消费的高层 bool/string 字段，
        仍然完全没有改变 lower create-program 的失败形态。
    - 因而当前阻塞已进一步收敛：
      - 不只是 `cache-id / aot-cache-id / attrs / string_id` 不够
      - 连 `modelIdentityStr / skipPrepare / lateLatch / powerSaving / keepWired`
        这些 `loadModel...` 明确消费的 direct-create 参数也不够
      - 下一层更像是：
        - `modelToken` 绑定关系
        - `ProgramDefinition` / retained companion
        - 或更低的 selector-3 create-program descriptor 合同
  - 2026-06-14 补做 `.hwx file-model precompiled` 单例负证据：
    - 结果文件：
      `benchmark_results/private_ane/precompiled_file_route_probe_skip_prepare_no_has_cache_1781366852.json`
    - 同一 wrapper root 的 MIL bootstrap 仍正常：
      - `compile_ok = true`
      - `load_ok = true`
      - `state = 3`
      - `programHandle = 13084134868092`
      - `intermediateBufferHandle = 319979`
      - `queueDepth = 127`
    - 但 `.hwx` file-model precompiled route 使用
      `precompiled_aot_const_seed_attrs_seed_string_id_identity_short_model_skip_prepare`
      且不带 `has_cache_flag` 时仍失败：
      - `load_ok = false`
      - `load_error = Program load failure (0x170004)`
      - `after_load.state = 5`
      - `programHandle = 0`
      - `load_after_compile_ok = false`
      - `load_after_compile_error = Program load failure (0x170004)`
    - 这确认：
      - `skipPreparePhase` 不是 `.hwx precompiled` 失败的解锁点
      - `0x170004` 发生在能靠跳过 selector-4 prepare 获益之前
      - 后续不要再主要扩展高层 precompiled option 矩阵
    - 2026-06-14 新增
      `precompiled_170004_family4_note.md`
      与
      `ane_precompiled_error_family_join.csv`
      后，这个结论还能再硬一层：
      - 当前两个代表性 `.hwx precompiled` 失败 case
        都解码为：
        - `error_code_hex = 0x170004`
        - `status_high16 = 0x0017`
        - `family_low16 = 0x0004`
      - 而 daemon lower-gate join
        已确认：
        - family-4 = selector-3 create stage
        - family-5 = selector-4 prepare / selector-6 destroy
      - 因而当前 `.hwx precompiled`
        `0x170004`
        不是“prepare 还没过”；
        它已经更明确地是：
        selector-3 create-stage lower status `0x17`
      - 这也进一步确认：
        `skipPreparePhase`
        对当前这类失败无效，
        因为 failure family 根本还没走到 selector-4
    - 与 `aned_bin.i64` 的静态事实一致：
      `_ANEProgramForLoad createProgramInstance...` 在 `sub_10000307F`
      中先调用 `controller.device` vtable `+0x10` 创建 `programInstance`；
      若该 call 返回非零，会直接生成 `(status << 16) | 4` 的
      program-load error。`skipPreparePhase` 只在 create 成功并已有
      `programInstance` 后才影响是否进入 prepare。
  - 2026-06-14 新增 selector-3 request layout 对照：
    - 结果：
      `benchmark_results/private_ane/ane_services_program_create_runtime_probe_layout_compare_1781377876.json`
    - 说明文档：
      `mps/ANE/experiments/results/selector3_request_layout_compare_note.md`
    - 在同一 live device、同一 artifact root
      (`mps/ANE/.ane_runs/runtime_wrapper_aug_weighted_ffn/add_all`) 上，
      对比：
      - 旧 local probe `legacy` layout
      - 按 `aned_bin:sub_10000307F` 推断出的 `daemon` layout
    - 新 `daemon` layout 已按当前静态写入面移动关键 request 字段：
      - `is_precompiled: 0x10`
      - `team/cs SHA: 0x11 / 0x31`
      - `qos/power/stats: 0x54 / 0x58 / 0x5c`
      - `memory_pool_id: 0x60`
      - `model_identity: 0x68`
      - `owning_pid: 0x158`
      - `cache/aot/model_path: 0x16c / 0x56c / 0x96c`
    - 结果：
      - 两种布局的 local selector-3 `status` 都仍然是 `0`
      - 但 wrapper state 也同样都停在：
        - `wrapper+0x70 = 0`
        - `payload+0xda8 = 0`
        - `payload_u8_0xde0 = 4`
        - `destroy = 0x14`
    - 这确认：
      - local selector-3 “success” 不是因为旧 probe 采用了错误的
        visible request offsets
      - request field placement 本身不是当前 accepted-state 缺口
      - 仍更像缺 lower accepted-state materialization / replay / publish
  - 2026-06-14 新增 base-create direct-BL 纠偏：
    - fresh probe：
      `mps/ANE/.ane_runs/csv/ane_bootkc_base_create_process_args_probe.csv`
    - 说明文档：
      `mps/ANE/experiments/results/basecreate_direct_bl_correction_note.md`
    - 当前 machine-local 直接 `bl` 图已确认：
      - `ANEHWDevice::ANE_ProgramCreate`
        - `visible direct BL count = 35`
        - `direct ProcessCreate calls = 0`
        - `direct cleanup calls = 1`
      - `ANEHWDevice::ANE_ProgramCreate_gated`
        - `visible direct BL count = 22`
        - `direct ProcessCreate calls = 0`
        - `direct cleanup calls = 1`
    - `ANE_ProgramCreate_gated` 的 visible direct call graph 当前包含：
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
    - 这确认：
      - 旧 `ane_bootkc_base_create_process_args_probe.py`
        的 offset-based “visible local process-args callsite” 结论不应再当作
        事实源
      - base-create 线上若存在 process-create / accepted-state rebuild，
        当前已经在 direct visible BL lowering 之下
      - 现阶段继续追 base-create 时，优先级应停在：
        provisional resource insertion -> subclass load -> client attach
        -> later reply/publish
  - 2026-06-12 新增的 local selector-3 runtime authoring 结果：
    - 新 probe：
      - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
      - 已加入 `mps/ANE/experiments/Makefile`
    - 结果文件：
      - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v1_notrace.json`
      - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v2_emptyids.json`
    - 新 probe 先尝试 `ANEServicesDeviceOpen`，结果与旧结论一致：
      - mode=1 -> `0x00000004`
      - mode=2 -> `0x00000018`
      - standalone 仍拿不到 device
    - 但 probe 现在会 fallback 到一个已知成功的 tiny MIL load，
      直接复用：
      - `_ANEProgramForEvaluation program`
      - `program.controller`
      - `controller.device`
      作为 live ANEServices device 指针
    - 在这个 live device 上，当前手工 author 的 `0xd88`
      `ANEProgramCreateArgs` 已经可以直接让
      `ANEServicesProgramCreate` 返回成功：
      - payload=`model.hwx`, `is_precompiled=1` -> `status=0`
      - payload=`data`, `is_precompiled=1` -> `status=0`
      - payload=`model.hwx`, `is_precompiled=0` -> `status=0`
      - payload=`data`, `is_precompiled=0` -> `status=0`
    - 更强的对照：
      - 即使把
        - `cache_id=""`
        - `aot_id=""`
        - `model_identity=""`
        全部清空，
        上述四个 case 仍然全部 `status=0`
    - 当前最强结论：
      - selector-3 local authoring 已经到达“可直接调用、可稳定 success”的层
      - 对当前 probe 而言，
        `cacheUrlIdentifier / aotCacheUrlIdentifier / modelIdentityStr / isPreCompiled`
        这些字段都不是 selector-3 success 的必要条件
      - 因而当前 daemon `.hwx precompiled` 失败，更像卡在：
        - daemon 上层 request author / wrapper state
        - live device / owner/service state
      - 或 ANEServices wrapper 对 selector-3 success 结果的消费与回写
      - 而不像是 selector-3 driver contract 本身要求这些高层字符串字段
  - 2026-06-12 新增的 `modelToken / selector-3` 边界事实：
      - 静态入口：
        - `appleane_bin`:
          - `+[_ANEModelToken tokenWithAuditToken:modelIdentifier:processIdentifier:]`
          - `-[_ANEModelToken initWithAuditToken:modelIdentifier:processIdentifier:]`
          - `-[_ANEModelToken initWithCsIdentity:teamIdentity:modelIdentifier:processIdentifier:]`
        - `aned_bin`:
          - `-[_ANEServer loadModel:sandboxExtension:options:qos:withReply:]`
          - `sub_10000307F`
      - 结果文件：
        - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v15_zero_token_sha.json`
        - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v16_fake_token_sha.json`
        - `mps/ANE/experiments/results/modeltoken_selector3_boundary_note.md`
      - 当前已确认：
        - daemon `loadModel...` 里，
          `_ANEModelToken.modelIdentifier` 不是来自 cache-id、
          `modelIdentityStr` 或 selector-3 output；
          它是从 `modelURL.path` 的最后两级路径直接拼出来的
          userland 字符串。
        - `sub_10000307F` 里，
          `modelToken.modelIdentifier` 只可见地用于：
          - `csIdentity.processIdentifier.modelIdentifier`
            这条 `os_transaction_create(...)` 名字
          - 当前没有证据显示它再进入 lower selector-3 request body。
        - selector-3 request 里真正可见打包的是：
          - model bytes / length
          - model path
          - `teamIdentity` SHA256
          - `csIdentity` SHA256
          - `modelIdentityStr`
          - `cacheUrlIdentifier`
          - `aotCacheUrlIdentifier`
          - qos/power/stats/keepWired
        - 但新 runtime 对照已证明：
          - 把 request 里的 `team/cs SHA` 从全零改成固定伪造非零值后，
            四个 local selector-3 create case 仍全部：
            - `status=0`
            - `prepare1=0x14`
            - `prepare1_owner0_ready1=0x02`
            - `raw_prepare=0xe00002c1`
      - 因而当前最强结论变成：
      - `modelToken` identity 线已经不是当前 create-side 主阻塞；
      - 当前更像卡在
        `create success -> wrapper adoption / prepare-state / lower writeback`
        这条链，而不是卡在 token identity author。
  - 2026-06-12 新增的 selector-4 / prepare-state 边界事实：
    - 静态入口：
      - `aneservices_bin::_ANEServicesProgramCreate`
      - `aneservices_bin::_ANEServicesProgramPrepare`
      - `aneservices_bin::__ZN3ANE17ANEServicesDevice18ANE_ProgramPrepareEP21ANEProgramPrepareArgs`
      - `aneservices_bin::_ANEServicesProgramDestroy`
    - 结果文件：
      - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v16_fake_token_sha.json`
      - `mps/ANE/experiments/results/selector4_prepare_state_boundary_note.md`
    - 当前已确认：
      - selector-3 create success-side只会先 materialize：
        - `payload+0xda8`
        - `wrapper+0x70`
        - `wrapper+0xa8`
        - `payload+0xde0=4`
        - `payload+0xde4=statsMask`
      - 但它不会先 materialize：
        - `wrapper+0x98`
        - `payload+0xd98`
        - `payload+0xd78..0xd90`
      - `_ANEServicesProgramPrepare` 成功侧才是这组字段的第一个可见 writer：
        - `wrapper+0x98 <- returned_qword`
        - `payload+0xd98 <- 0`
        - `payload+0xd78..0xd97 <- prepare args shadow`
        - `payload+0xde0 <- normalized state`
        - `payload+0xde4 <- prepareArgs[2]`
      - `_ANEServicesProgramDestroy` 前置 gate 也直接依赖：
        - `payload+0xd98`
        - `payload+0xda8`
      - 更关键的是，runtime 对照已经证明：
        - raw prepare base: `0xe00002c1`
        - `owner0+ready1`: `0xe00002c2`
        - `owner0+ready1+handlepatch`: 仍 `0xe00002c2`
        - `raw_prepare_livehandle`: 仍 `0xe00002c2`
      - 也就是说：
        - 即使直接给 raw selector-4 live `programHandle + queueDepth`
          组合，当前 lower prepare 仍然拒绝。
    - 因而当前最强结论再下沉一层：
      - 当前缺口已经更像 selector-4 / device-side accepted state；
      - 不再适合主要建模成
        `token identity`、`visible handle`、
        `queueDepth` 或 `wrapper prepareArgs` 缺失。
    - 再结合现有 bootkc family-6 证据，
      当前这条 selector-4 边界已经可以进一步桥接成：
      - userland local raw prepare 的
        `0xe00002c2`
        最像 bootkc family-6 create/load/process-state stack
        里的 lower accepted-state 缺口，
        而不是 userland wrapper-visible field 缺口。
    - 当前支撑这条 join 的 machine-local 事实：
      - selector-4 侧：
        - `owner0+ready1 -> 0xe00002c2`
        - `owner0+ready1+handlepatch -> 0xe00002c2`
        - `raw_prepare_livehandle -> 0xe00002c2`
      - family-6 侧：
        - `ANE_ProcessCreate_gated` 依赖 firmware-issued setup token workflow
        - `isProcessValid(mode!=0)` 要求：
          - `resource+0x400d0` 非空
          - exact process-pointer membership
          - `process+0x203fc != 2`
        - `ProgramLoad` / `programLoadFromMachoFile`
          已经把：
          - `resource+0x493a0`
          - `[resource+0x400d0] + 0x220`
          - `record+0x1b8`
          - `process+0x203fc`
          串进同一条 lower load/state 路
      - 对应 note：
      - `mps/ANE/experiments/results/selector4_family6_state_join_note.md`
    - 2026-06-12 还可再明确一条边界：
      - `mps/ANE/experiments/results/selector4_visible_surface_limit_note.md`
      - 当前 selector-4 userland visible surface 已基本耗尽：
        - static contract 已收窄到 0x38-byte inout prepare buffer
        - shallow preflight（nil/device/runtime-entry）已被越过
        - visible handle/queue-depth/prepare-word/token 相关 patch 已试过
        - 仍然统一停在 `0xe00002c2`
      - 因而下一轮不该再主要扩新的 wrapper-visible selector-4 field sweep。
    - 2026-06-12 当前最强 blocker 总结已可写成：
      - `mps/ANE/experiments/results/lower_author_gap_summary_note.md`
      - `mps/ANE/experiments/results/current_control_layer_blocker_note.md`
      - 当前 artifact-descriptor / visible wrapper / visible CPU-side staging
        已基本耗尽；
      - 剩余缺口最像在以下更低层之一：
        1. `process+0x203fc == 2` decisive author
        2. `record+0x1b8` durable author below callback/completion side effects
        3. `resource+0x400d0` first materializer
        4. callback/completion sink execution 或 manager-side state replay
    - 2026-06-13 新增两条 machine-local 纠偏，直接影响后续建模：
      - `mps/ANE/experiments/results/completion_process_counter_note.md`
      - `mps/ANE/experiments/results/save_state_entry_flag_note.md`
      - 当前直接证据已表明：
        1. `handleOutstandingCommand(...)` 里那条 completion-side `+0x20400`
           路径不是 earlier note 里较弱表述的
           `matched_resource+0x20400`；
           它实际上是：
           - `lookupProgramResource(inner+0x68, &process, 0)`
           - 取回 `ANEProcess*`
           - `matched_process+0x20400 --`
           - `commandWakeup(device, matched_process+0x20400)`
        2. `ANE_SaveState(...)` 当前 visible 写入模式不是
           “把某个 lower accepted-state 写成 2”；
           当前更精确的 visible pattern 是：
           - `[resource+0x400d0]+0x220 <- -1`
           - `entry+0x18 <- -1`
           - `entry+0x203fc <- 1`
      - 因而当前应明确收回两种较弱旧读法：
        - 不要再把 completion-side `+0x20400` 默认建模成 resource-side
          outstanding bookkeeping；
        - 不要再把 `ANE_SaveState` 当成一个可能的 visible `state==2`
          author 候选。
      - 更好的当前 family 读法变成：
        - completion 路已经直接触到另一个 process-owned
          `0x203f0..0x2040c` 邻域槽位：`process+0x20400`
        - save 路当前更像：
          - demote / save / mark-dirty
          - 而不是 accepted-state promote
      - 对应新 probe / CSV：
        - `mps/ANE/experiments/ane_bootkc_completion_process_counter_probe.py`
        - `mps/ANE/.ane_runs/csv/ane_bootkc_completion_process_counter_probe.csv`
    - 2026-06-13 completion 线还能再向下确定一个 concrete owner：
      - `mps/ANE/experiments/results/completion_cleanup_destroy_join_note.md`
      - `mps/ANE/.ane_runs/csv/ane_bootkc_completion_cleanup_join_probe.csv`
      - 当前 machine-local join 已可写成：
        - completion callback shell
        - `device+0x4d0 remove/count`
        - `client_ctx+0x20` cleanup-side object
        - `client_ctx+0x18` clone/destroy-walk
        - `ANE_ProcessDestroy_gated(...)`
        - `[resource+0x400d0]->removeObject(index)`
      - 这意味着：
        - visible callback/std::function shell 已不是主疑点
        - completion 之后的下一个真正 state owner
          已经不是“泛泛的 manager cleanup”，而是
          `client_ctx+0x18/+0x20` cleanup/destroy path
      - 当前因此更值得继续沿：
        - `ANE_ProcessDestroy_gated`
        - `ProgramUnload`
        - `ANE_SaveState`
        这一组 save/destroy/demote 路，
        去看它们如何和：
        - `process+0x203fc`
        - `record+0x1b8`
        - `[resource+0x400d0]+0x220`
        形成更完整的 lifecycle family
    - 2026-06-13 新增的 demote-family 收敛已经够强：
      - `mps/ANE/experiments/results/demote_family_join_note.md`
      - 当前 machine-local visible family 可直接写成：
        - `ProgramUnload`
        - `ANE_ProgramCreateInstance_gated` side path
        - `ANE_RestoreStateEv.cold.2`
        - `ANE_SaveState`
      - 它们共同表现为：
        - `entry/process+0x18 <- -1`
        - `entry/process+0x203fc <- 1`
        - save 路额外还会：
          - `[resource+0x400d0]+0x220 <- -1`
        - 且 `ProgramUnload` / create-instance side path
          会在这之后立刻进入 `aneCmdSend(...)`
      - 因而当前 visible writers 已不该再被建模成
        “很多 unrelated writers”，而更像
        一个 coherent demote/unload/mark-dirty family
      - 这进一步支持：
        - visible `state==2` author 仍未出现
        - 更像在 demote family 之后的 deeper reply/replay path
    - 2026-06-13 现在还可以把 ProgramLoad replay 和 demote family
      并排成一个更强的 current-machine 对照：
      - `mps/ANE/experiments/results/programload_vs_demote_note.md`
      - `mps/ANE/.ane_runs/csv/ane_bootkc_programload_vs_demote_probe.csv`
      - ProgramLoad 当前 visible shape：
        - `[resource+0x400d0]+0x220` read
        - `process+0x203fc` gate
        - `record+0x1b8` read
        - gate-state refresh from `record+0x1b8`
      - demote family 当前 visible shape：
        - `entry/process+0x18 <- -1`
        - `entry/process+0x203fc <- 1`
        - optional `gate+0x220 <- -1`
        - `aneCmdSend(...)`
      - 更关键的是：
        - `ProgramUnload` 在 visible H16 层里，
          `aneCmdSend(...)` 之后并没有立刻出现
          `record+0x1b8` 形态的 replay/readback
      - 因而当前最强 blocker 口径应进一步收窄为：
        - 缺失的 `state==2` / `record+0x1b8` durable author
          最像位于
          demote/send family
          与
          replay/refresh family
          之间的 deeper reply/replay path
    - 2026-06-13 现在还能再把 post-send 边界分成两类：
      - `mps/ANE/experiments/results/post_send_replay_boundary_note.md`
      - `mps/ANE/.ane_runs/csv/ane_bootkc_post_send_replay_boundary_probe.csv`
      - restore-side send：
        - send 后几乎立刻出现
          `record+0x1b8 -> resource+0x402f0`
          replay
      - unload-side send：
        - send 后先进入
          `device slot+0x9c0`
          / `0x927d410` family
        - 当前 visible H16 不立刻出现
          `record+0x1b8` replay
      - 这让下一条 lower target 更明确：
        - 比起重复看 restore-side short replay，
          更值得优先追
          unload-side post-send device family
    - 2026-06-13 unload-side post-send family 现在还能再定名一层：
      - `mps/ANE/experiments/results/unload_postsend_revalidation_note.md`
      - `mps/ANE/.ane_runs/csv/ane_bootkc_unload_postsend_revalidation_probe.csv`
      - 当前 machine-local visible chain 已可写成：
        - `ProgramUnload`
          - demote/send
          - `isProgramValid(resource)`
          - `isProcessValid(resource, process, mode=1)`
          - conditional cold-path continuation
      - 因而 `device slot+0x9c0 / 0x927d410 family`
        这句模糊表述现在已经可以退休；
        当前更准确的说法是：
        unload-side post-send first reenters
        shared lower acceptance chain
    - 2026-06-13 继续往下看 accepted branch，
      当前又能再收窄一层：
      - `mps/ANE/experiments/results/programunload_accepted_continuation_note.md`
      - 当前 visible accepted continuation
        还不是显式 `record+0x1b8 / gate+0x220` replay
      - 它更像：
        - staged unload/control loop
        - mode-indexed table selection
        - logging
        - later deeper continuation
      - 这意味着：
        - 下一条更值钱的 lower target
          已经不是 first accepted branch shell
        - 而是 accepted continuation 更深处的后继 handoff
    - 2026-06-13 结合 client-hint fallback shared runtime family，
      当前还能再下一个结论：
      - `mps/ANE/experiments/results/programunload_shared_runtime_join_note.md`
      - ProgramUnload 不是 isolated leaf；
        它当前 machine-local 上更像 shared runtime chain 里的一步：
        - `ProgramUnload`
        - `ProgramPartialUnwire`
        - `ProgramReMap`
        - `ProgramLoad(load_type=2)`
      - 因而如果要找 missing replay/state-2 author，
        当前更值钱的点已经不只是
        `ProgramUnload` accepted continuation 本身，
        而是 unload 之后的 shared runtime continuation
    - 2026-06-13 shared runtime continuation 内部的优先级也已可排定：
      - `mps/ANE/experiments/results/post_unload_runtime_priority_note.md`
      - `ProgramLoad(load_type=2)` 已是 replay consumer
      - `ProgramReMap` 已是 metadata consumer
      - 因而当前最值钱的 unresolved step 是：
        - `ProgramPartialUnwire`
    - 2026-06-13 对 `ProgramPartialUnwire(...)` 的第一轮直接反汇编
      已经说明它不是 dead-end cleanup helper：
      - `mps/ANE/experiments/results/programpartialunwire_early_note.md`
      - 当前 early body 已可见：
        - repeated `+0x2f0` family touches
        - `waitForPendingUpdate(...)`
        - device-side collection/state machinery
        - device slot `+0x9c0` resource validation
      - 因而它仍然是当前最值得继续下钻的 post-unload lower target
    - 2026-06-13 再往后看，`ProgramPartialUnwire(...)` 的角色已能进一步分清：
      - `mps/ANE/experiments/results/programpartialunwire_loop_note.md`
      - 当前它更像：
        - lower shared-runtime cleanup/transition stage
        - 不是 direct replay/refresh consumer
      - machine-local 可见工作包括：
        - `waitForPendingUpdate`
        - resource validation
        - process/registy walk
        - `aneFreeIntermediateBuffer`
        - `ReleaseProgramResource`
      - 当前最可能的 missing lower author
        仍更像位于：
        - `ProgramPartialUnwire` cleanup/transition
          与
        - `ProgramLoad(load_type=2)` replay/refresh
          之间的 handoff
    - 2026-06-13 现在还能更强地说：
      - `mps/ANE/experiments/results/programpartialunwire_state_join_note.md`
      - `mps/ANE/.ane_runs/csv/ane_bootkc_programpartialunwire_state_join_probe.csv`
      - `ProgramPartialUnwire(...)` 已不只是“可能 reconnect lower state”；
        它当前 machine-local 上已经直接接回：
        - `resource+0x400d0` process registry
        - process-local state / collections
        - `resource+0x402f0` state alias
      - 但它仍未直接表现为：
        - `record+0x1b8` replay
        - `[resource+0x400d0]+0x220` refresh
      - 因而当前 missing lower handoff 已经非常窄：
        - `ProgramPartialUnwire` state-family reconnection
          ->
        - `ProgramLoad(load_type=2)` explicit replay
    - 2026-06-13 `setClientHint_gated(...)` 内 shared continuation
      也已可从“列表”收紧成 machine-local 串行链：
      - `mps/ANE/experiments/results/setclienthint_shared_continuation_note.md`
      - 当前顺序已明确：
        - `ProgramUnload`
        - `ProgramPartialUnwire`
        - `ProgramReMap`
        - `ProgramLoad(load_type=2)`
      - 这进一步支持：
        - `ProgramPartialUnwire`
          不只是优先级最高，
          还是 unload-side demote/revalidation
          与 metadata/replay consumers 之间的 exact handoff stage
    - 2026-06-13 `ProgramReMap(...) -> ProgramLoad(load_type=2)` 之间的
      CPU-visible 区间也已基本塌缩：
      - `mps/ANE/experiments/results/remap_to_programload_boundary_note.md`
      - `mps/ANE/.ane_runs/csv/ane_bootkc_remap_to_programload_boundary_probe.csv`
      - 当前 success-side visible chain 只剩：
        - remap status spill
        - branch on status
        - logging/formatting
        - ProgramLoad(load_type=2)
      - 没有再看到更丰富的 lower-state handoff
      - 因而当前 CPU-visible gap
        已进一步塌缩到：
        - `ProgramReMap(...)` 调用边界本身或更低
    - 2026-06-13 对 `ProgramLoad(load_type=2)` /
      `needProgramRemap(residency)` /
      `process+0x203fc` 的契约
      现已进一步压实：
      - `mps/ANE/experiments/results/programload_remap_process_contract_note.md`
      - 当前 `needProgramRemap(residency)`
        不是轻量状态位，而是 hard structural gate：
        - 先检查当前 resource 上多组
          per-residency `+0xa0` slots
        - 再扫描 `resource+0x400e8`
          child-resource collection，
          要求 child 的当前 residency slot
          与 `child+0x90+residency*0x28` 选中的 table entry
          都已非空
        - 任一不满足就返回 `1`
          (`Program needs to be remapped`)
      - 当前 `ProgramLoad(...)`
        的 visible 顺序已可更精确写成：
        - 先读：
          - `resource+0x493a0`
          - `[resource+0x400d0]+0x220`
        - 再用 `device+0xe270`
          作为 `residency` 调
          `needProgramRemap(residency)`
        - 通过后走
          `setPendingUpdate_gated(resource, 1, 1)`
      - 更重要的新分界是：
        `load_type`
        与
        `process+0x203fc`
        不是单一 zero/nonzero 语义：
        - `load_type == 0`
          且 gate-owned state 不是 `-1`
          时可直接 fast-success
        - `load_type == 1`
          时：
          - 先要求 `matched_process+0x20 == arg3`
          - `process+0x203fc == 0`
            视为已有 ready process
          - `process+0x203fc != 0`
            才 re-enter
            `ANE_ProcessCreate_gated(...)`
        - `load_type != 1`
          （包括当前主线里的 `load_type == 2`）
          时：
          - `process+0x203fc == 0`
            直接 skip 该 process
          - `process+0x203fc != 0`
            才 re-enter
            `ANE_ProcessCreate_gated(...)`
      - 当前 `record+0x1b8`
        仍只出现在更深 create-program / replay path：
        - `aneCmdSend(...)`
        - device `vslot +0x9c0` validation
        - `ldr [record+0x1b8]`
        - `str [gate+0x220]`
      - 因而 `ProgramLoad(load_type=2)`
        现在可以更强地归类为：
        - remap-ready table consumer
        - load-type-specific process-state consumer
        - record replay consumer
        而不是这三者的 durable author
      - 这也让当前 blocker 更硬：
        当前 artifact-descriptor / H16-visible CPU text
        更像 shape/check/reconnect/replay consumers；
        `record+0x1b8` durable author、
        `process+0x203fc == 2` decisive author、
        以及 remap-ready table 的 first author
        更像已经落到更低层
    - 2026-06-13 对顶层 `resource+0x60`
      的 author 链也已进一步闭合：
      - `mps/ANE/experiments/results/remap_ready_slot_resource60_author_note.md`
      - 当前 legacy load body 在
        `0xfffffe00092fccf8`
        调
        `ANEProgramLegacyResource::initOtherSections(...)`
      - `initOtherSections(...)`
        内部会先调用
        `ANEResource::create<(ANEResourceType)3>(...)`
        在栈局部生成新的 `shared_ptr<ANEResource>`
      - 随后通过：
        `ldur q0, [x29, #-0x20]`
        ->
        `str q0, [self+0x60]!`
        直接把这个新 `shared_ptr`
        写进 `resource+0x60/+0x68`
      - 这里先读的 `[self+0x68]`
        只是旧 control-block 的 release 面，
        不是新 payload 的 source bridge
      - 之后同一对象在 legacy load 里继续被消费：
        - `0xfffffe00092fcd14`
          `ldr x27, [self+0x60]`
          -> legacy-only `dartMap(...)` 路
        - `0xfffffe00092fcea0`
          `ldr x8, [self+0x60]`
          -> `+0x88` section/header 初始化路
      - 因而当前 `needProgramRemap(residency)`
        顶层可见 slot provenance
        已可更精确拆成：
        - `resource+0x20`
          <- `additional_params+0x38`
        - `resource+0x30`
          <- `additional_params+0x48`
        - `resource+0x60`
          <- legacy-only
             `initOtherSections(...)`
             `create(Type3)` author path
      - 这也意味着，
        当前 remap-ready 主未知项
        已不再是顶层 `resource+0x60`
      - 2026-06-13 对 `resource+0x400e8`
        child-resource collection 这一层也已进一步闭合：
        - `mps/ANE/experiments/results/resource_400e8_collection_lifecycle_note.md`
        - `mps/ANE/.ane_runs/csv/ane_bootkc_resource_400e8_collection_probe.csv`
      - 当前 shared Legacy/RT `preProcess`
        已明确直接作者化顶层 collection 指针：
        - Legacy:
          `0xfffffe00092faa08`
          `bl ANEResourceCollection::C1()`
          ->
          `0xfffffe00092faa0c`
          `str x0, [resource+0x400e8]`
        - RT:
          `0xfffffe00093092a8`
          `bl ANEResourceCollection::C1()`
          ->
          `0xfffffe00093092ac`
          `str x0, [resource+0x400e8]`
      - 当前 `ANEResourceCollection::C1()`
        raw body 也已收紧为：
        - 清空 begin/end/cap-like 头部
        - 构造 comparator `std::function`
        - 分配 `IORecursiveLock`
        - 没有直接可见 child materialization
      - 更重要的是，
        `resource+0x400e8`
        当前 visible 层不只做 construct，
        还已经包含 populate：
        - Legacy
          `initSplitKernelSections(...)`
          `0xfffffe00092fe5d0`
          直接对
          `ldr [resource+0x400e8]`
          调
          `ANEResourceCollection::addResource(...)`
        - RT
          `traverseProcedureGraphAndPopulateIOs(...)`
          `0xfffffe000930ca60`
          也会经
          `&resource+0x400e8`
          间接取出 collection
          后调用
          `addResource(...)`
      - 当前 `addResource(...)`
        自身 visible 逻辑
        更像 collection-level container insertion，
        没看到 child `+0x90/+0xa0`
        remap table 的直接作者化
      - 2026-06-13 又新增一个更强收紧：
        `resource+0x400e8`
        visible populate 的 child
        当前已不只是
        “某个 `ANEResource`”，
        而是已收紧到
        `ANEResource::create<Type4>()`
        路：
        - `mps/ANE/experiments/results/type4_child_table_visibility_note.md`
        - `mps/ANE/.ane_runs/csv/ane_bootkc_type4_child_table_probe.csv`
      - 当前 direct callers 里，
        与 `resource+0x400e8`
        直接相关的至少有：
        - Legacy
          `initSplitKernelSections(...)`
          `0xfffffe00092fe4e8`
        - RT
          `traverseProcedureGraphAndPopulateIOs(...)`
          `0xfffffe000930c90c`
      - 并且当前 machine-local 还表明：
        - `create<Type4>()` body
          自身没露出
          `child+0x90/+0xa0/+0xb0`
          非栈作者面
        - Legacy add-to-collection window
          只看到
          `child + residency*0x28 + 0xb0`
          一条可见写入
        - RT add-to-collection window
          里 `child+0x90/+0xa0/+0xb0`
          当前都没露出来
      - 2026-06-13 再继续往下到
        `Type4 -> Type0 -> resource ctor`
        后，
        当前结论仍然成立：
        - `mps/ANE/experiments/results/type0_type4_author_boundary_note.md`
        - `mps/ANE/.ane_runs/csv/ane_bootkc_type0_type4_author_boundary_probe.csv`
      - 新 probe summary 当前是：
        - `resource_c1`
          `child+0x90/+0xa0/+0xb0 = 0/0/0`
        - `create_type0`
          `child+0x90/+0xa0/+0xb0 = 0/0/0`
        - `create_type4`
          `child+0x90/+0xa0/+0xb0 = 0/0/0`
      - 所以当前更强的 machine-local 边界是：
        即使沿
        `Type4 -> Type0 -> ANEResource::C1`
        再往下一层，
        child `+0x90/+0xa0`
        仍没出现可见作者面
      - 这让当前主未知项更明确成：
        `Type4` child 的
        `+0x90/+0xa0`
        per-residency remap tables
        当前仍未在这些 visible windows
        里作者化
      - 因而当前 remap-ready 主未知项
        已进一步下沉为：
        - child `+0x90/+0xa0` tables
          的 first author
        - 当前 H16-visible
          `Type4/Type0/resource-ctor`
          以下的 lower author boundary
        - `ANE_ProgramInitialSetup(...)`
          里三处 `create<Type4>()`
          与这些 child remap surfaces 的关系
        - 以及更低层 process / record author
    - 2026-06-13 对 `ANE_ProgramInitialSetup(...)`
      三处 `create<Type4>()`
      与 top-level remap-ready 槽的 bridge
      也已有更强 current-machine 证据：
      - `mps/ANE/experiments/results/initialsetup_type4_slot_bridge_note.md`
      - `mps/ANE/.ane_runs/csv/ane_bootkc_initialsetup_type4_slot_bridge_probe.csv`
      - 当前 visible shape 已收紧为：
        - 三处 `create<Type4>()`
          先把 shared_ptr pairs
          staged 在
          `sp+0x48/0x88`,
          `sp+0x70/0xa8`,
          `x27/sp+0x78`
        - 随后出现强 bridge candidate：
          - `[sp+0x48/sp+0x88] -> [x29-0xe0]`
          - `[sp+0x70/sp+0xa8] -> [x29-0xd0]`
          - `[x27/sp+0x78] -> [x29-0xf0]`
        - 尾部硬事实仍是：
          - `[x29-0xd0] -> additional_params+0x38`
          - `[x29-0xe0] -> additional_params+0x48`
          - `[x29-0xf0] -> additional_params+0x68`
      - 因而当前最强解释是：
        `InitialSetup` 很像正在把三路
        Type4-derived shared_ptr pairs
        bridge 到
        `additional_params+0x38/+0x48/+0x68`
        的当前上游
    - 2026-06-13 对这些
      `InitialSetup` 三路 Type4
      的 section-family 语义
      又有了更强 current-machine 收紧：
      - `mps/ANE/experiments/results/initialsetup_type4_section_family_note.md`
      - `mps/ANE/.ane_runs/csv/ane_bootkc_initialsetup_type4_section_family_probe.csv`
      - 当前 visible compare shape
        已很像：
        - `x28`
          是 lower-case section name
        - `x28+0x10`
          是 upper-case segment name
      - 因而当前 top-level slot
        的最强 visible section-family 映射
        已可写成：
        - `__TEXT,__const`
          -> `call1`
          -> `additional_params+0x48`
          -> `resource+0x30`
        - `__TEXT,__text`
          -> `call2`
          -> `additional_params+0x38`
          -> `resource+0x20`
        - gated `__INIT,__text`
          -> `call3`
          -> `additional_params+0x68`
          -> `resource+0x50`
      - 并且第三路当前还明显不同于前两路：
        - 前两路是
          `aneVnodeAsyncReadAdvise(...)`
          lane
        - 第三路是
          `map(0x1000)`
          + `aneValidateVnodeFromMappedAddress(...)`
          lane
      - 当前同一
        `__INIT,__text`
        family
        里还存在一个 separate alternate branch：
        - `[sp+0x3c] != 0`
          时不会走第三个 `Type4`
        - 而会落到
          `create<Type3>()`
          -> `map(3)`
          -> `memmove(...)`
      - 所以当前可以更强地说：
        顶层 remap-ready seeds
        在 visible path 上
        当前至少只和
        `__TEXT,__const`
        `__TEXT,__text`
        以及 gated `__INIT,__text`
        直接相关；
        `__KERN_,__kern_`
        当前仍只像 counter lane，
        `__RUNTIME,__runtime`
        则虽不直接进入这三路 Type4 seed，
        但也不是 dead lane
    - 2026-06-13 对
      `w21 / [sp+0x3c] / additional_params+0x8a`
      这条当前 machine-local
      1-bit control path
      已有更强收紧：
      - `mps/ANE/experiments/results/initialsetup_runtime_carry_rtgraph_note.md`
      - `mps/ANE/.ane_runs/csv/ane_bootkc_initialsetup_runtime_carry_probe.csv`
      - 当前 visible 关键链已可写成：
        - `0x9306924`
          `str w21, [sp+0x3c]`
          先快照 previous-w21
        - `0x930692c`
          `mov w21, #0`
          再清当前 iteration 的 carry
        - `0x9306c44`
          `ldr w8, [sp+0x3c]`
          让 `__INIT,__text`
          读这个 previous-w21 snapshot
        - `0x9306e18`
          `mov w21, #1`
          是当前 `ANE_ProgramInitialSetup`
          visible body
          里唯一的 non-zero writer，
          且正好位于
          `__RUNTIME,__runtime`
          lane
        - success path 末尾：
          `0x93061c8`
          `and w8, w21, #1`
          `0x93061cc`
          `strb w8, [x20, #0x8a]`
          把这一 bit
          durable 地写到
          `additional_params+0x8a`
      - 并且当前更下游的
        `createProgramResource(...)`
        已明确消费这个字段：
        - `0x928b254`
          `ldrb w8, [x2, #0x8a]`
        - `0x928b258`
          `tbz w8, #0, 0x928b278`
          bit0==0
          直接走
          `ANEProgramLegacyResource::create`
        - bit0==1
          则检查
          `device+0x3db8`
          与
          `device+0x3674`
          后再走
          `ANEProgramRTResource::create`
          或显式报：
          `Firmware does not support RTGraph macho`
      - 所以当前更准确的结论是：
        `__RUNTIME,__runtime`
        当前不是 top-level Type4 seed，
        但它确实会落成
        `additional_params+0x8a`
        并作为
        `RTGraph-vs-Legacy`
        resource-class selector
      - 当前又可继续补硬一层：
        用 IDA 直接补函数并反编后，
        两条 create 入口的最早差异已经明确：
        - `ANEProgramLegacyResource::create`
          当前只做：
          `gMetaClass alloc`
          + `result+0x10 = device`
        - `ANEProgramRTResource::create`
          除了
          `result+0x10 = device`
          之外，
          还会立刻：
          `result+0x40333 = 1`
      - 所以当前更强的 machine-local 说法是：
        `additional_params+0x8a bit0`
        不只是“跳到哪个 create 符号”，
        而是已马上进入
        不同 program-resource class
        并 materialize 出
        至少一个 RT-only object flag
    - 2026-06-13 对这个
      RT-only object flag
      的更下游消费者
      也已有新的 current-machine 收紧：
      - `mps/ANE/experiments/results/rt_mode_flag_consumers_note.md`
      - `mps/ANE/.ane_runs/csv/ane_bootkc_rt_mode_flag_consumers_probe.csv`
      - 当前可见链条已经可再往下一层写成：
        `additional_params+0x8a bit0`
        -> `ANEProgramRTResource::create`
        -> `resource+0x40333 bit0`
      - 当前这条
        `resource+0x40333`
        flag
        的 visible writer
        仍只有：
        `ANEProgramRTResource::create`
        的
        `result+0x40333 = 1`
      - 但它现在已经有两个更下游的
        early consumers：
        1. `ANEHWDevice::ProcessAbort(...)`
           - `0x927e738`
             `ldrb w10, [x25, #0x333]`
           - `0x927e73c`
             `tbz w10, #0, ...`
           - bit0==1
             时走：
             `sendSetupCmd(0x403, resource+0x2f0, ...)`
        2. `ANEHWDevice::ANE_ProgramSendRequest_gated(...)`
           - `0x92976b0`
             `ldrb w8, [x8]`
           - `0x92976b4`
             `tbz w8, #0, ...`
           - bit0==1
             时改走
             resource vtable
             `+0x148`
             `programRTSendInferenceRequest`
           - bit0==0
             时回到
             generic
             `ANE_ProgramPrepareAndSubmitRequest_gated`
      - 并且当前 machine-local
        resource vtable decode
        也已对上这条 send path：
        - `ANEProgramResource::vtable +0x148`
          -> `ANEProgramResource::programRTSendInferenceRequest`
        - `ANEProgramLegacyResource::vtable +0x148`
          -> `ANEProgramResource::programRTSendInferenceRequest`
        - `ANEProgramRTResource::vtable +0x148`
          -> `ANEProgramRTResource::programRTSendInferenceRequest`
      - 所以当前更强的 machine-local 说法是：
        `additional_params+0x8a`
        已不只是
        create-time class selector，
        而是继续通过
        `resource+0x40333`
        影响至少：
        - abort path 的
          `sendSetupCmd(0x403, resource+0x2f0, ...)`
        - request path 的
          `programRTSendInferenceRequest`
          vs
          generic PrepareAndSubmit
    - 2026-06-13 对这条
      RT-specific request path
      与 generic request path
      的汇合边界
      也已有新的 current-machine 收紧：
      - `mps/ANE/experiments/results/rt_send_convergence_note.md`
      - `mps/ANE/.ane_runs/csv/ane_bootkc_rt_send_convergence_probe.csv`
      - 当前 machine-local 已确认：
        - `ANEProgramResource::programRTSendInferenceRequest`
          base implementation
          只是 error stub
        - `ANEProgramRTResource::programRTSendInferenceRequest`
          才是 substantive override
      - 但更重要的是：
        `resource+0x40333 bit0`
        把 request path
        分叉到：
        - generic
          `ANE_ProgramPrepareAndSubmitRequest_gated`
        - RT
          `programRTSendInferenceRequest`
        之后，
        两支当前都还会：
        1. 运行
           `ANE_ProgramCheckandPrewireBuffers_gated`
        2. 最终调用
           `ANERequest::create`
        3. 再进入
           `ANERequest::init`
      - 所以当前更准确的 lower-boundary 结论是：
        RTGraph / RT-mode
        当前并不是
        “完全独立的 request-object lowering 体系”，
        而是
        “在 request-object bridge 之前
        有一条 RT-specific orchestration path，
        之后又重新汇合到
        common `ANERequest::create/init`”
      - 这也让
        `[sp+0x3c]`
        的当前解释
        更准确成：
        previous-runtime-carry snapshot，
        而不是
        `__INIT,__text`
        自带的静态属性位
    - 2026-06-13 对 `ProgramReMap(...)` 本体的角色也可进一步细化：
      - `mps/ANE/experiments/results/programremap_sideeffects_note.md`
      - 当前仍成立：
        - `ProgramReMap` 不是 explicit `record+0x1b8` replay consumer
      - 但当前已可见它不只是 passive metadata reader，
        还会触发：
        - `waitForPendingUpdate`
        - `setPendingUpdate`
        - `wireResources`
        - `kernel_debug`
        - resource-side 0xf5xxx family writes
      - 因而当前最值钱的 `ProgramReMap` 线索
        已从“它读了哪些 metadata 字段”
        变成：
        - 它 deeper side effects
        - 以及这些 side effects 如何把 lower state
          传给 `ProgramLoad(load_type=2)`
    - 2026-06-13 对 `ProgramReMap(...)` side effects 的下一焦点
      也已收敛：
      - `mps/ANE/experiments/results/programremap_surface_focus_note.md`
      - 当前最有信号的 surface pairing
        已不再是直接找 `record+0x1b8`，
        而是：
        - `resource+0x493a0`
        - `resource+0x402f0`
      - 再加上：
        - `waitForPendingUpdate`
        - `setPendingUpdate`
        - `wireResources`
        - resource-side `0xf5xxx` writes
      - 这更像 ProgramReMap 在 prepare/reconnect
        `ProgramLoad(load_type=2)` later consumes 的状态
    - 2026-06-13 这个焦点现在已经有了 focused probe 证据：
      - `mps/ANE/experiments/results/programremap_surface_coupling_note.md`
      - `mps/ANE/.ane_runs/csv/ane_bootkc_programremap_surface_coupling_probe.csv`
      - 当前最强 CPU-visible handoff 已可写成：
        - `resource+0x493a0`
        - `resource+0x402f0`
        - wrapped inside
          `waitForPendingUpdate / setPendingUpdate / wireResources / setPendingUpdate`
      - 再之后才是：
        - `0xf5ad8`
        - `record+0x28 / 0xb8 / 0xe8`
      - 因而当前如果 CPU-visible 线索还没到底，
        最该深挖的就是
        `ProgramReMap` 里这组 surface-coupling side effects
    - 2026-06-13 对 `ProgramReMap(...)` 里先前未解的 self-vtable 调用
      已得到纠正性结论：
      - `mps/ANE/experiments/results/programremap_object_lifecycle_shell_note.md`
      - 当前 machine-local 反汇编 + vtable 解码已确认：
        - `0xfffffe00093058d8 / 0x93058e4`
          的 `self vtable +0x20`
          不是 hidden remap helper，
          而是 `OSObject::retain(self)`
        - `0xfffffe0009305bf8 / 0x9305c04`
          的 `self vtable +0x28`
          是匹配的 `OSObject::release(self)`
      - 因而 `ProgramReMap(...)` 在 `wireResources(...)`
        前后这两跳只是 object-lifecycle shell，
        不是 missing lower replay/state handoff
      - 这意味着当前下一焦点应从
        “继续追 slot +0x20”
        改成更深的：
        - `wireResources(...)`
        - optional `dartMapResources(...)`
        - `0xf5b58 / 0xf5b28 / 0xf5af8 / 0xf5b88 / 0xf5bb8 / 0xf5c18`
          materialization side effects
    - 2026-06-13 对上述更深 side-effect 链也已进一步收敛：
      - `mps/ANE/experiments/results/programremap_lower_sideeffect_boundary_note.md`
      - 当前 machine-local 结论：
        - `wireResources(...)`
          不是 hidden replay helper，
          而是：
          - `self+0x10 -> device`
          - device `0x3b42 / 0x3b44` gate
          - child-resource `ANEResource::wire / asyncWire / waitForAsyncWiring`
            loop
        - optional `dartMapResources(...)`
          不是 hidden replay helper，
          而是：
          - `self+0x10 -> device`
          - device `0xe270` residency-family state
          - child-resource `ANEResource::dartMap(residency, 1)` loop
        - `0xf5b58 / 0xf5b28 / 0xf5af8 / 0xf5b88 / 0xf5bb8 / 0xf5c18`
          当前只是：
          - `record+0x28 / 0xb8 / 0xe8`
          - device `0x3618`
          - `udiv / madd`
          - materialize into resource `0xf5xxx`
          这一段 pure arithmetic materialization
          当前没有再出现更深 helper 调用
      - 因而当前 `ProgramReMap(...)` 的 H16-visible 下边界已可更强地写成：
        - ordinary child-resource wire/map loops
        - followed by pure metadata materialization
      - 这使得当前 blocker 证据更硬：
        missing lower replay/state handoff
        更像已经落到
        H16-visible CPU text 之下
    - 2026-06-13 对 `ProgramReMap(...)` materialized `0xf5xxx` fields
      的 later consumer 扫描也已完成：
      - `mps/ANE/experiments/results/programremap_materialized_fields_consumer_note.md`
      - `mps/ANE/.ane_runs/csv/ane_bootkc_programremap_materialized_fields_probe.csv`
      - 当前扫描的 6 个 field：
        - `0xf5af8`
        - `0xf5b28`
        - `0xf5b58`
        - `0xf5b88`
        - `0xf5bb8`
        - `0xf5c18`
      - 当前 machine-local 结果：
        - 这 6 个 field 在 H16 `__TEXT_EXEC`
          里只有 `ProgramReMap(...)` 自己的
          split-add + `str`
        - 没有任何 later visible load / consumer 命中
      - 因而当前更强 blocker 证据是：
        - self `retain/release` shell：证伪
        - `wireResources(...)`：ordinary child-resource wire loop
        - `dartMapResources(...)`：ordinary child-resource DART-map loop
        - `0xf5xxx`：write-only materialization in current H16 text
      - 这意味着 missing lower replay/state handoff
        当前已不太像还藏在
        `ProgramReMap(...)` 可见 side-effect 链中，
        而更像已经落到：
        - lower helper
        - firmware/reply path
        - 或比当前 artifact-descriptor / H16 text
          更低的控制层
    - 2026-06-13 对 send-boundary 两侧的 `record+0x1b8` author gap
      现在已经形成 raw/typed 对称证据：
      - raw side:
        `mps/ANE/experiments/results/restore_record_raw_send_boundary_note.md`
      - typed side:
        `mps/ANE/experiments/results/legacy_typed_record_state_boundary_note.md`
        `mps/ANE/.ane_runs/csv/ane_bootkc_legacy_typed_record_state_boundary_probe.csv`
      - 当前 machine-local 结果：
        - restore/raw:
          `aneCmdSend(raw)` 返回后，
          到 `record+0x1b8` read 之前
          只有极短可见区间，
          无 visible store / 无 visible helper call
        - legacy/typed:
          typed `aneCmdSend(...)` 返回后，
          到 `x25+0x1b8` read 之前
          `visible_interval_insns=34 stores=0 calls=1`
          且唯一的 call
          只是 device slot `+0x9c0`
          -> `ANEHWDevice::isProgramValid(...)`
      - 因而当前更完整的 blocker 结论是：
        `record+0x1b8` durable author gap
        在 raw restore path 与 Legacy typed path
        上都已经落到 visible H16 send boundary 之下
      - 这把“下一控制层需求”进一步收紧成：
        - firmware request/reply payload semantics
        - lower helper / completion / callback side effects
        - 或另一层当前 artifact-descriptor / H16 text
          无法直接 author 的 runtime control surface
    - 2026-06-13 Legacy `x25+0x1b8` 分支的本地 pointer-table populate
      也已进一步收紧：
      - `mps/ANE/experiments/results/legacy_pointer_table_population_note.md`
      - `mps/ANE/.ane_runs/csv/ane_bootkc_legacy_pointer_table_population_probe.csv`
      - 当前 machine-local 结果：
        - `sp+0x130 + index*0x50 -> x25`
          这一段 immediate window
          没有 visible direct store 去 populate pointer table
        - 当前窗口只剩 4 个 call：
          - `__os_log_internal`
          - `ANEProgramLegacyResource::initSplitKernelSections(...)`
          - `ZinComputeProgramDestroy(...)`
          - `IOFreeTypeVarImpl`
      - 并且 `initSplitKernelSections(...)`
        一进来就进入更深结构：
        - `self + 0xf61d8`
        - `IOMallocTypeVarImpl`
        - `ZinComputeProgramGetNumberOfKernelSections(...)`
      - 因而当前 Legacy 分支的 next useful lower boundary
        已从泛泛的
        “继续追 sp+0x130 pointer table”
        收紧成：
        - `ANEProgramLegacyResource::initSplitKernelSections(...)`
        - `self+0xf61d8` side structure
        - `ZinComputeProgram*` helper family
    - 2026-06-13 typed completion path 侧的 blocker 也已形成汇总：
      - `mps/ANE/experiments/results/typed_completion_no_record_author_note.md`
      - 当前可见 completion-side fields：
        - `payload+0x50` = pre-submit carrier / response match consumer
        - `payload+0x68` = completion-side resource lookup key
        - `payload+0x88` = callback/wakeup slot
      - 当前 `handleOutstandingCommand(...)` 可见动作：
        - `inner+0x58 = completion_status`
        - `lookupProgramResource(inner+0x68)`
        - `matched_resource+0x20400 --`
        - callback sink / wakeup / OSSet cleanup / poll-timer disable
      - 当前没有看到：
        - direct `record+0x1b8` replay
        - gate-owned alias refresh
        - visible durable lower-state author/writeback
      - 因而当前更完整的 blocker 结论是：
        missing lower replay/state handoff
        不仅不在 `ProgramReMap(...)` 可见 side-effect 链里，
        也不在当前可见 typed completion bookkeeping 链里
      - 这使“下一控制层需求”进一步收紧为：
        - firmware request/reply payload semantics
        - lower reply publish / completion side effects below current H16 text
        - 更低 runtime helper/control layers
    - 2026-06-13 runtime-lower-side 的 next-layer 入口也已进一步收敛：
      - `mps/ANE/experiments/results/runtime_lower_next_layer_note.md`
      - 当前 machine-local 结论：
        - default receive/response 路：
          - `_IOProcessorChannelReceive` tag-strip
          - `processCommandResponse(...)`
          - `handleOutstandingCommand(...)`
          当前都已被解释为
          outstanding-command lifecycle / completion bookkeeping
    - 2026-06-13 对 success-style completion / request lifecycle 的更强收敛：
      - `mps/ANE/experiments/ane_bootkc_process_command_response_probe.py`
      - 当前 `processCommandResponse(...)`
        比 `handleOutstandingCommand(...)` 本体
        更像 success-style completion 的直接上游入口：
        - 遍历 `device+0x4d0` outstanding-command `OSSet`
        - `safeMetaCast(OSValueObject<ANEFirmwareCommandState>)`
        - 用 `payload+0x50 == response_arg1` 匹配 returned carrier
        - 命中后直接
          `handleOutstandingCommand(outstanding_osobject, 1)`
        - 未命中且 `payload+0x90 == 0`
          时走 `IOProcessorChannelSendRetry(...)` resend
      - 因而当前更准确的分层是：
        - `processCommandResponse(...)`
          = success-match / resend 入口
        - `handleOutstandingCommand(...)`
          = completion bookkeeping / callback / wakeup / cleanup 壳
      - 但这两层当前都仍未触到：
        - `process+0x203fc == 2`
        - `record+0x1b8`
        - visible durable lower-state writeback
      - 同日已有 request-side 负载链证据表明，
        若继续追 `FWPendingRequest` /
        `removeRequestByUUID` 一类 request lifecycle，
        更合理的下钻面是：
        `processTargetToHostIOCommand(...)`
        -> `ANE_HandleRPCRequestFromFW(...)`
        -> `ANEScheduler::iteratePendingRequests(...)`
        / `ANE_ScheduleWork_gated(...)`
        而不是继续把主精力放在
        `handleOutstandingCommand(...)` 本体
        - typed completion 路：
          也已被解释为
          status / lookup / wakeup / cleanup bookkeeping
        - 在当前可见 interrupt special-channel 分支里，
          唯一仍像真实协议面的入口是：
          `device+0xe200+0x204`
          -> `ANEHWDevice::processTargetToHostIOCommand(...)`
      - 当前可见事实：
        - `processTargetToHostIOCommand(...)`
          已有
          `device+0xe204` context
          `12-byte shared buffer`
          `msg+0x04 opcode`
          以及
          `0x100 / 0x102 / 0x103 / 0x106 / 0x302`
          等 visible opcode case
      - 因而当前若继续走 runtime lower side，
        最有价值的下一入口
        已明确收敛到：
        `ANEHWDevice::processTargetToHostIOCommand(...)`
    - 2026-06-13 对 visible target-to-host 路线与 accepted-state cluster
      的关系也已进一步厘清：
      - `mps/ANE/experiments/results/target_to_host_cluster_miss_note.md`
      - 当前 machine-local 结论：
        - default receive/response route
          已被解释为 outstanding-command lifecycle / completion bookkeeping
        - visible target-to-host strongest route
          `0x106/0x7000 -> ANE_HandleRPCRequestFromFW -> ANE_ScheduleWork_gated`
          已被解释为 debug-work scheduling/control family
      - 当前还没看到它与以下 accepted-state cluster
        有有价值的 visible join：
        - `resource+0x400d0`
        - `resource+0x402f0`
        - `resource+0x493a0`
        - `resource+0x9b698`
        - `resource+0xf5ad8`
        - `process+0x203fc`
        - `record+0x1b8`
      - 因而当前 visible target-to-host broad scan
        对主线价值已显著下降
      - 这进一步支持：
        剩余高价值方向
        更像是：
        - lower firmware request/reply / publish path
        - accepted-state cluster 本身
        - 或 final blocker evidence package
    - 2026-06-13 已补一份汇总 blocker package：
      - `mps/ANE/experiments/results/final_blocker_evidence_package_note.md`
      - 其核心汇总结论是：
        - 当前已经达到：
          - userland/runtime request shaping
          - real artifact/program-body semantics
          - visible send/receive/response/completion staging
          - concrete accepted-state cluster
        - 当前仍未达到：
          - `process+0x203fc == 2` decisive author
          - `record+0x1b8` durable author
          - `resource+0x400d0` first materializer
        - 并且当前 evidence 已足够支持：
          缺的不是“再找一个明显 descriptor field”，
          而是更低的 accepted runtime-state author/control layer
        - 其中 `resource+0x400d0` 这一 unresolved target
          现在也应明确表述成：
          - 语义已知：
            `OSArray`-style owned process registry
          - 但 first materializer 仍未进入当前 H16-visible surface
        - 2026-06-13 新增的 `cluster memmove` 负证据：
          - `mps/ANE/experiments/results/bootkc_resource_gate_cluster_memmove_probe.md`
          - `mps/ANE/.ane_runs/csv/ane_bootkc_resource_gate_cluster_memmove_probe.csv`
          - 当前 machine-local 结果：
            在 H16 `__TEXT_EXEC`
            里没有任何 tracked `_memmove`
            的 dst/src 覆盖
            `resource+0x400c0..0x40100`
          - 因而 `resource+0x400d0`
            当前不仅没有 visible direct store，
            也没有 visible cluster-covering bulk-copy 解释
- 2026-06-13 Legacy helper side 的 blocker 也已形成更明确分界：
      - `mps/ANE/experiments/results/legacy_helper_boundary_note.md`
      - 当前 machine-local 结果：
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
      - 也就是说，
        Legacy helper side
        已经不是“还没触到 artifact/program-body 语义”
      - 但另一边，
        `x25+0x1b8`
        的 first visible mutation opportunity
        仍然在 typed sender 之下
      - 因而当前更完整的总体 blocker 是：
        - artifact/program-body semantics：已深入
        - accepted runtime state author：仍未到达
      - 这进一步支持：
        当前缺的不是
        “再找一个 descriptor field”
        或
        “再深入一点 helper 语义”
        而是更低的 runtime accepted-state/control layer
    - 2026-06-13 新增目标审计：
      - `docs/ane_goal_audit.md`
      - 当前审计结论：
        - benchmark 目标 `<=30s`
          已在 warm wrapper-route prototype 上达到
          (`28.340s`)
        - 但“一般化 accepted runtime-state author/control layer”
          仍未恢复
        - 因而当前最准确的阶段结论是：
          - performance target on prototype: reached
          - generalized lower accepted-state control: not reached
    - 新增的 create-after-prepare 结果：
      - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v4_prepareflags.json`
      - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v7_ownerpatch_serial.json`
      - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v9_payloadstate_serial.json`
      - 当前 local `ANEServicesProgramCreate status=0` 之后，
        紧接着：
        - `ANEServicesProgramPrepare(flag=0) -> 0x03`
        - `ANEServicesProgramPrepare(flag=1) -> 0x14`
        - `ANEServicesProgramDestroy -> 0x14`
      - 并且这对四个 case 全部一致：
        - `model.hwx` / `data`
        - `is_precompiled=1/0`
      - 更强的 local patch 对照已经拿到：
        - 当前 created wrapper 的 live state：
          - `owner_state = 1`
          - `service_ready = 0`
          - `service_connect = 25347`（本轮样本）
        - 只把 `owner_state -> 0`：
          - `prepare1` 仍然 `0x14`
        - 再把 `service_ready -> 1`：
          - `prepare1` 变成 `0x02`
      - 结合 `ANEServicesProgramPrepare` 静态链可得：
        - `flag=0 -> 0x03`
          - 是 wrapper 的 `TBZ W2,#0` 直接分支，不进入 prepare 主链
        - `flag=1` 且当前原始 live state：
          - 先可能命中 wrapper 早期 owner-state gate 的 `0x14`
        - `owner_state=0` 后仍然 `0x14`
          - 说明这时已经越过早期 wrapper gate
          - 进入更深层后，又被 raw status `0xe00002c1 -> wrapper 0x14`
            这条映射打回
        - `owner_state=0 + service_ready=1` 后变 `0x02`
          - 对应更深层 raw status 已进一步变化，最像
            `0xe00002c2 -> wrapper 0x02`
      - 因而当前 local selector-3 success 不是“假的 create”，而是：
        - create call 本身成功
        - prepare 阶段的 wrapper/device/service state 仍不满足
        - 且 current daemon `.hwx precompiled` 的问题更像卡在这里，
          而不是卡在 selector-3 输入字段 author
      - 因而 daemon `.hwx precompiled` 失败现在更像是：
        - create 后的 wrapper state / prepare gate 问题
        - 而不只是 selector-3 输入字段 author 问题
    - 当前 local created program wrapper 的已见状态（以
      `hwx_precompiled_path_hwx` 为例）：
      - vtable:
        - `qword0_vtable = 0x1f6a59e68`
      - payload:
        - `payload_u32_0x20 = 1`
        - `payload_u32_0x24 = 0`
        - `payload_qword2 = 0x0000000000114000`
        - `payload_qword0 == created_device_layout.device`
          - 即 payload 首 qword 就是 live `ANEDeviceStruct *`
      - 这与 `ANEServicesProgramPrepare` / `Destroy` 的 `0x14` 前置 gate
        可以直接对照，值得下一轮继续沿 payload state 追。
    - 2026-06-12 新增的 runtime graph / handle-patch / wordargs 证据：
      - 结果文件：
        - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v12_livegraph_handlepatch.json`
        - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v14_wordargs_isolated.json`
      - `v12` 已把成功 tiny MIL load 的 live runtime graph 直接落盘：
        - `_ANEProgramForEvaluation` visible ivars:
          - `_programHandle = 10418008115395`（本轮样本）
          - `_queueDepth = 127`
          - `_intermediateBufferHandle = 0`
        - `_ANEDeviceController` visible ivars:
          - `_programHandle` 与 program 一致
          - `_device` 指向 live `ANEDeviceStruct *`
        - 这证明当前 probe 已不只是“借一个 live device 指针”，而是已经拿到
          成功路径的可见 runtime graph 与 `programHandle/queueDepth`。
      - `v12` 对 local created wrapper 继续做最小回填：
        - 先把 `owner_state -> 0`
        - 再把 `service_ready -> 1`
        - 再把
          - `wrapper+0x70 = live programHandle`
          - `payload+0xda8 = live programHandle`
          - `wrapper+0xa8.low32 = live queueDepth`
        - 结果仍然稳定：
          - `prepare1_owner0_ready1 -> 0x02`
          - `prepare1_owner0_ready1_handlepatch -> 0x02`
          - `raw_prepare_owner0_ready1 -> 0xe00002c2`
          - `raw_prepare_owner0_ready1_handlepatch -> 0xe00002c2`
      - 这条证据很关键：
        - 当前阻塞已经不是“缺一个 nonzero programHandle / queueDepth”
        - visible `wrapper+0x70 / payload+0xda8 / wrapper+0xa8.low32`
          这组最小回填不足以再把 `0x02` 往里推进
      - `v12` 还暴露出一个重要状态变化：
        - 原始 created wrapper:
          - `payload_u8_0xde0 = 4`
        - 在 `owner_state=0 + service_ready=1` 后，即使 prepare 失败：
          - `payload_u8_0xde0 = 2`
        - 说明当前 local prepare 已经能驱动 payload state 发生可见变化，
          但还没有拿到 success-side writeback
          （`wrapper+0x98 / payload+0xd98 / payload+0xd78..` 仍未 materialize）
      - `v14` 进一步验证了 wrapper `prepareArgs` 本身不是当前主阻塞：
        - 把 wrapper `a2` 从全零改成最小 non-zero 变体
          (`qos_word/is_precompiled/power_word/stats_mask`)
        - 结果仍然稳定：
          - `prepare1_wordargs -> 0x14`
          - `prepare1_owner0_ready1_wordargs -> 0x02`
          - `prepare1_owner0_ready1_handlepatch_wordargs -> 0x02`
      - 因而当前更强结论是：
        - 不是 wrapper `prepareArgs` 全零导致的早期失败
        - 不是 visible handle/queueDepth 缺失
        - 当前最像缺的是：
          - prepare success-side shadow / writeback group
            (`wrapper+0x98`, `payload+0xd98`, `payload+0xd78..0xd90`)
          - 或更低一层 selector-4 / device-side accepted state
      - 2026-06-12 继续新增的 raw selector-3 证据把问题再往下压了一层：
        - 在当前进程里直跑
          `mps/ANE/experiments/ane_services_program_create_runtime_probe`
          已确认：
          - `raw_create_fn = 0x1a4e5107c`
          - `raw_create_status_hex = 0x00000000`
          - 但 `ANEProgramCreateArgsOutput` 头部摘要仍全零：
            - `qword0/qword1/qword2/qword3 = 0`
            - `qword_0xac6f8/qword_0xac708 = 0`
            - `u32_0x2b140/u32_0x2b14c = 0`
        - 同一 case 上 wrapper 仍然：
          - `wrapper+0x70 = 0`
          - `payload+0xda8 = 0`
        - 这条证据的重要含义是：
          - 当前 local selector-3 `status=0`
            并不等于 create-output 已 materialize 出 nonzero runtime entry
          - 问题已经不像是“wrapper 吞掉了一个本来 nonzero 的 handle”
          - 更像是：
            - 当前 author 的 create request / artifact 仍没有让 lower
              selector-3 output 产出非零 program entry
            - 也就是缺口比 prepare/adopt 更早，
              已经下沉到 selector-3 output / additional_params /
              lower create-state
      - 2026-06-12 新跑的 bootkc fresh probes 进一步把 zero-output 的位置钉住：
        - fresh CSV：
          - `mps/ANE/.ane_runs/csv/ane_bootkc_output_handoff_probe_fresh.csv`
          - `mps/ANE/.ane_runs/csv/ane_bootkc_493a0_materialization_probe_fresh.csv`
          - `mps/ANE/.ane_runs/csv/ane_bootkc_process_setup_probe_fresh.csv`
          - `mps/ANE/.ane_runs/csv/ane_bootkc_is_process_valid_probe_fresh.csv`
          - `mps/ANE/.ane_runs/csv/ane_bootkc_resource_gate_table_probe_fresh.csv`
          - `mps/ANE/.ane_runs/csv/ane_bootkc_process_state_source_provenance_probe_fresh.csv`
        - 这些 fresh 证据继续确认：
          - `ANEHWDevice::ANE_ProgramCreate`
            直接调用
            `ANEProgramResource::ANE_ProgramInitialSetup`
          - `ANE_ProgramInitialSetup` 成功路径只把 external
            `ANEProgramCreateArgsOutput*`
            挂到 `additional_params+0x10`
          - 真正的 output populate 在更后面的：
            - `ANEProgramLegacyResource::programLoadFromMachoFile`
            - `ANEProgramRTResource::programLoadFromMachoFile`
          - 且这两条 load 路一开始都会：
            - 先 `bzero(output, 0xac738)`
            - 再进入后续 populate helper
          - 2026-06-13 新增
            `programload_output_publish_gate_note.md`
            后，base-create 的 output path 还能再收紧一层：
            - Legacy/RT 都不是一进入 ProgramLoad
              就直接写 caller-visible external output
            - 先发生的是：
              `resource+0x493a0.qword0 = additional_params+0x18`
            - 真正的 caller-visible publish 是更后面的：
              `*external_output = additional_params+0x18`
            - 并且这一步明确依赖：
              - `ANE_ProcessCreate_gated(...)` 成功
              - `findClient(...)` 成功
              - client 未 closed/cleanup-in-progress
          - 2026-06-13 新增
            `raw_selector3_output_sentinel_note.md`
            后，raw selector-3 的 caller-visible output 结论还能再加强：
            - 把 caller output 整块预填成 `0xA5` 后，
              `raw_create_status=0`
            - 但整个 `0xac738` 缓冲区
              `diff_count = 0`
            - 说明当前 raw selector-3
              不是“把 output 写成 0”，
              而是“完全没碰 caller-visible output buffer”
          - 2026-06-13 新增
            `raw_selector3_wrapper_internal_state_note.md`
            后，dynamic split 又能再收紧一层：
            - 即使 caller-visible output 完全未触碰，
              raw selector-3 仍然返回非空 `outProgram`
            - 而且 wrapper/payload 内部已经有稳定的：
              - `payload_qword0 = device ptr`
              - `payload_qword1 = model/data ptr`
              - `payload_qword2 = payload bytes`
              - `payload_u32_0x20 = precompiled bit`
            - `created_device_layout` 也稳定非空：
              - `device`
              - `owner`
              - `service`
              - `owner_state_u32_0x20 = 1`
              - `service_ready_u8_0x18 = 0`
            - 并且：
              `program_wrapper.payload_qword0 == created_device_layout.device`
        - 这意味着当前 selector-3 raw create `status=0` 但 output 全零，
          更像是：
          - 要么还没有真正进入 Legacy/RT `programLoadFromMachoFile`
            的 populate/publish 链
          - 要么只走到了 early `resource+0x493a0` publish，
            但没走到 later external-output publish gate
          - 要么 raw probe 里的 caller output buffer
            根本不是实际 threaded 到 `additional_params+0x10`
            的 external output slot
          - 同时也说明：
            当前 raw selector-3 不是“什么都没建出来”，
            而是“有效 create-state 先落在 wrapper/payload/device graph 内部”
        - 2026-06-12 新的 gate 细化结果：
          - `ANE_ProcessCreate_gated` 不是“只靠 visible params 就能过”的链：
            - 当前 body 依赖 firmware-issued token workflow：
              - `sendSetupCmd(0x402, &local_resource_state_u32, &create_token_u32)`
              - `sendSetupCmd(0x403, resource + 0x2f0, &create_token_u32)`
              - 或 feature-disabled 下的 raw/typed `0x202/0x203` 命令族
            - `ANEProcess::create(...)` 只是薄包装，
              真正 token shaping 发生在 `ANE_ProcessCreate_gated` 之前
          - `isProcessValid(mode!=0)` 当前最强模型：
            - leading resource-validation gate
            - `resource+0x400d0` 非空
            - exact process-pointer membership in that registry
            - `process+0x203fc != 2`
          - `ProgramLoad` 当前显式读取：
            - `resource+0x493a0` qword0
            - `[resource+0x400d0] + 0x220`
          - RT `programLoadFromMachoFile` 当前显式写：
            - `resource+0x493a0` qword0 <= `additional_params+0x18`
          - `process+0x203fc` 当前可见 store 来源里：
            - 没有 visible constant-2 source
            - 也没有 visible `0x1b8 / 0x220 / 0x402f0` source chain
            - 2026-06-13 新增更强 exact-writer 证据：
              - `ANEProcess::init`
                直接 zero qword 覆盖 `process+0x203fc`
              - `ANE_ProcessCreate_gated`
                直接 `str wzr` 到 `process+0x203fc`
              - `ANE_SaveState`
                main loop 直接写 `process+0x203fc <- 1`
              - `ANE_RestoreStateEv.cold.2`
                直接写 `process+0x203fc <- 1`
            - 见：
              `mps/ANE/experiments/results/process_state_and_record_author_tightening_note.md`
        - 因而当前最像的缺口已继续收窄为一个 gate family，而不是单字段：
          - firmware setup token workflow
          - `additional_params+0x18` / `resource+0x493a0` seed
          - `resource+0x400d0` gate-owned collection
          - process pointer membership / `process+0x203fc` lifecycle gate
        - 2026-06-13 新增 send/reply shell 负证据：
          - `aneCmdSendAsync(...)`
            只是 `std::function` 拷贝后转调
            `aneFirmwareCommandSend(...)`
          - typed `aneCmdSend(...)`
            只是 stack lambda + async send + sleep/cancel/wakeup 壳
          - typed `aneCmdSend(...)` 自带的
            `std::__function::__func<...>::operator()`
            也已确认只是：
            `ANEHWDevice::commandWakeup(device, *result_ptr)`
            没有额外 state writeback
          - `aneFirmwareCommandSend(...)`
            可见层主要是：
            - `ANEFirmwareCommandState` 分配/填充
            - payload copy
            - `IOProcessorChannelSendRetry(...)`
            - 失败侧 `handleOutstandingCommand(...)`
          - `handleOutstandingCommand(...)`
            可见层主要是：
            - command-state completion/result byte
            - optional memmove / DMA free
            - `commandWakeup(...)`
            - `lookupProgramResource(...)`
            - `matched_process+0x20400` 计数递减
            - callback 调用
          - `iterateOutstandingCommands(...)`
            及其 block 也已确认只是：
            - `safeMetaCast(OSValueObject<ANEFirmwareCommandState>)`
            - 若 payload 非空则调用外层 block
            不是目标状态物化层
          - 当前对
            `aneFirmwareCommandSend(...)` /
            `handleOutstandingCommand(...)`
            的 exact operand 检查仍是：
            - no `op_any == 0x3fc`
            - no `op_any == 0x1b8`
          - 见：
            `mps/ANE/experiments/results/send_reply_shell_negative_note.md`
        - 2026-06-13 新增 procedure/cache/chaining 边界收窄：
          - `findChainingRequestByCacheHandler(...)`
            `0xfffffe000935f214`
            当前已确认不是空壳：
            - 明确使用
              `resource+0x400d0`
              和
              `resource+0x9b698`
            - 先要求：
              - `[resource+0x400d0]+0x264` bit0 已置位
              - `*(resource+0x9b698) > 2`
            - 再枚举 `[resource+0x400d0]` 里的子项，
              从 `entry+0x90` 起扫描 pointer array，
              以 `(*slot)+0x8 == cacheHandler`
              为命中条件
            - 命中后只把 slot 指针写回 out-param，
              没有 visible state writeback
          - `findProcedureCallCacheRequest(...)`
            `0xfffffe00092855f0`
            当前已确认是 request-side lookup：
            - 直接走
              `ANEScheduler::pendingRequestsCount()`
              /
              `getMutablePendingRequest(i)`
            - 命中条件是：
              - `request+0x3120 != NULL`
              - 且
                `request+0x3130 == cacheHandle`
                或
                `[[request+0x18]+0x48] == uuid_like_arg`
            - 命中后只回填 `ANERequest*`
          - `sendChainingCacheRequestToFirmware(...)`
            `0xfffffe000928e7d4`
            当前已确认只是 send shell：
            - 调 `aneCmdSend(...)`
            - 成功后：
              - `req+0x30 <- 1`
              - `req+0x8 <- returned_obj+0x20`
                作为 firmware response cacheHandle
            - 当前不直接触到：
              - `resource+0x400d0`
              - `resource+0x402f0`
              - `resource+0x493a0`
              - `record+0x1b8`
              - `process+0x203fc`
          - `buildFirmwareChainingCacheRequest(...)` /
            `buildFirmwareProcedureCallCacheRequest(...)` /
            `buildFirmwareProcedureCallRequest(...)`
            当前可见层仍更像 command marshalling：
            - 组 procedure/cache request 的
              input/output/intermediate/raw-stat buffers
            - 记录 uuid/programId/processId/transactionId/
              programHandle/procedureID/live-in/dynamicOffset 等
            - 但 exact-operand 检查仍未命中：
              - `0x400d0`
              - `0x402f0`
              - `0x493a0`
              - `0x9b698`
              - `0x1b8`
              - `0x203fc`
          - 结论：
            - 这组函数不是空跑；
              `cacheHandler`
              确实能 join 到
              `resource+0x400d0 / resource+0x9b698`
              这一 accepted-side cluster
            - 但截至当前可见层，
              `procedure/cache/chaining`
              整体仍更像
              lookup/build/send family，
              不是
              `process+0x203fc == 2`
              /
              `record+0x1b8`
              的 durable author
          - 见：
            `mps/ANE/experiments/results/procedure_cache_chaining_boundary_note.md`
        - 2026-06-12 对现有 user-space probe surface 的回扫也已经给出负证据：
          - `ane_inmemory_new_instance_probe_direct_iokit_param_matrix_numeric.csv`
          - `ane_inmemory_new_instance_probe_direct_iokit_param_matrix_deep.csv`
          - `ane_inmemory_new_instance_probe_services_runtime.csv`
        - 当前已经明确试过的 user-space visible surface 至少包括：
          - `params[0] = known loaded base programHandle`
          - `pid tail = 0`
          - `baseModelIdentifier` 多种来源：
            - model hex
            - UUID
            - internal programHandle decimal
            - local path / modelURL path
          - real weight symbol/path/len/bytes
          - real SHA
        - 这些 direct selector-8 变体当前都稳定仍然：
          - `raw_status = 0xe00002c2`
          - `ANEProgramCreateArgsOutput` 全零
        - 因而当前最强的 machine-local 结论已经可以升级为：
          - 现有 repo 内能看到的 user-space visible surface 基本已覆盖完
          - 当前 artifact-descriptor / visible wrapper 可控层不足以穿过
            lower setup-command / resource-process coherence gate
        - 2026-06-12 再结合 bootkc create-instance notes，可把
          “first unavailable user-space-equivalent surface” 再收缩一层：
          - `bootkc_create_instance_additional_params_use_scan_note.md`
            已确认 visible direct additional-params contract 其实很小：
            - `+0x0`
            - `+0x18`
            - `+0x80`
          - `bootkc_create_instance_hidden_handle_bridge_probe.md`
            已确认：
            - regular visible selector-8 bridge:
              - `x5 = 0`
              - 无法直接让 `additional_params+0x18` 非空
            - driver-routed create-instance path:
              - 先有 local program-handle slot
              - 再经 provider wrapper/block capture
              - 最终把该 hidden handle 写进 `additional_params+0x18`
              - 再作为 `local_y` 参与
                `lookupProgramResource(local_y, &process, 0)`
              - 并回写到：
                - `resource+0x493a0[0]`
                - `params[0]`
          - 2026-06-13 新增 `createinstance_memmove_source_correction_note.md`
            已修正一条旧解释：
            - create-instance hidden branch 里的 later `0xac738` copy source
              不是 `ANE_ProcessCreate_gated(...)` 的直接返回值
            - `ANE_ProcessCreate_gated(...)` 当前 visible success return 是
              `status = 0`
            - hidden branch 里 post-call `x23` 先作为 status gate 使用，
              之后才由 `[sp+0x58]/[sp+0x60]` 相关 stack-restored surface 重新绑定
            - 因而当前更准确的说法是：
              - hidden sidecar/local_y 仍然 internal-author
                `params[0]`
                以及 create-instance 深分支里的当前 `x21` destination qword0
              - later copy direction 当前应表述为：
                `resource+0x493a0 -> external output`
              - 但这个 older `resource+0x493a0` surface 的 first producer
                仍需继续追
          - `bootkc_resource_gate_process_registry_probe.md`
            已确认：
            - `resource+0x400d0` 当前 behaves like
              `OSArray<ANEProcess*>` registry
          - 因而当前最像的第一个“用户态无等价 author”的 surface
            已经不是泛泛的 setup/process gate，而是更具体的：
            - driver/device-authored hidden handle sidecar
              -> `additional_params+0x18`
          - 这也解释了为什么：
            - visible selector-8 regular bridge
            - 以及现有 repo 中围绕 `params[0]/pid/baseModelIdentifier`
              的 sweep
            都还不足以进入 lower accepted state
        - 2026-06-12 再与 base-create 路交叉后，当前 strongest current split 是：
          - base create (`ANE_ProgramCreate`)：
            - 当前已明确看到
              `direct create output -> ANE_ProgramInitialSetup -> additional_params+0x10`
            - 也就是 external `ANEProgramCreateArgsOutput*` handoff
            - fresh `base_provenance` 还进一步确认：
              `additional_params+0x18 = *(arg5/out_handle_ptr)`
            - 因而当前未解点不再是“base create 有没有 +0x18”，而是：
              `arg5/out_handle_ptr` 的上游正来源
          - create-instance：
            - 当前已明确证明
              `additional_params+0x18 = driver/device-authored hidden handle`
          - 这条 split 很关键，因为它说明：
            - selector-3/base-create `status=0` 但 output 全零，
              不是简单缺少 output 指针 handoff
            - 更像是 base-create 当前虽然也有 `+0x18` seed 位点，
              但没有拿到 create-instance 那种可用的 hidden-handle/key restore 族
            - 因而 base create 路与 create-instance 路当前并不共享同一层
              visible sidecar surface
            - 同时也不应再把 create-instance 深分支
              简化成“`ANE_ProcessCreate_gated` 直接返回 later copied surface”
        - `process_resource_key_seed_join_note.md` 进一步把
          create-instance 路的 lower key family闭环补齐了：
          - hidden local handle
            -> `additional_params+0x18`
            -> `local_y`
            -> `process_args[8]`
            -> `process+0x20`
          - 同一个 hidden local handle 还会明确 seed：
            -> `params[0]`
            -> 以及 create-instance 深分支里的当前 `x21` destination qword0
          - 但这里不要再把这个结论写成
            “已经完整拿到 `resource+0x493a0` 的 first common seed”；
            当前更准确的是：
            - process-key family 的 seed 已足够强
            - `params[0]` 的 internal author 已足够强
            - older `resource+0x493a0` surface 的 full first-producer
              仍然未解
          - 反过来，base create 当前虽然已知会
            `seed additional_params+0x18`
            ，而且 ProgramLoad 当前已明确把
            local `ANEProcessCreateArgs` 组装成：
            `{ additional_params+0x18, additional_params+0x18, additional_params+0x0 }`
          - 因而当前不应再把 base-create 阻塞表述成
            “缺少把 process/resource key family 共同 seed 起来的 lower key family”
          - 更准确的是：
            - base-create 已经有自己明确的
              lower process-args contract
            - 但这个 contract 为什么仍不能走到
              selector-3 nonzero external output / accepted coherence
              仍未解
          - 2026-06-13 新增
            `createinstance_process_args_seed_split_note.md`
            后，当前这条线还能再写得更精确：
            - create-instance 深分支里，
              `process_args[0]` 与 `process_args[8]` 当前 visible seeds
              不是同源
            - 更具体地：
              - `process_args[0] <- older resource+0x493a0[0]`
              - `process_args[8] <- hidden local handle / local_y`
              - `process_args[16] <- client-key family`
            - 因而当前最准确的结论不是
              “已经 visible first-common-seed 闭环”，
              而是：
              - process-key side seed 很强
              - params-side internal author 很强
              - 但 visible assembly point 仍是 split-seed
          - 2026-06-13 新增
            `createinstance_old_493a0_import_note.md`
            后，当前还能再往前压一格：
            - older `resource+0x493a0` surface 的 first visible import point
              已经明确
            - 它发生在 base program resource 解析成功之后：
              `x23 -> x25 = resource+0x493a0 -> [sp+0x60]`
            - 这说明 older `resource+0x493a0` 的 first producer
              不在 later process-create/remap/load continuation 本身
          - 2026-06-13 再与
            `bootkc_output_procedure_table_alias_probe.md`
            / `bootkc_output_handoff_probe.md`
            串起来后，当前还能形成一条更完整的 join：
            - earlier base create/load path:
              `external output -> resource+0x493a0`
            - later create-instance path:
              `resolved resource -> import old resource+0x493a0`
            - 因而当前最准确的表述已经不再是
              “`resource+0x493a0` 的来路完全未知”，
              而是：
              - visible producer-to-import chain 已明确
              - 但 selector-3/base-create 为什么没走到可用 producer chain
                仍未解
          - 因而当前 base-create 路的阻塞可以再写得更硬：
            - 不只是“少一个 sidecar”
            - 也不是“完全没有自己的 lower key contract”
            - 而是：
              已存在的 base-create lower contract
              为什么没有 materialize 成 accepted coherence
        - 2026-06-12 新的 caller 扫描事实：
          - 使用 `/tmp/KMUtilProducts/BootKernelCollection.kc`
            对当前 H16 `__TEXT_EXEC` 做 exact `bl` 扫描后，
            `ANEHWDevice::ANE_ProgramCreate`
            当前 `exact_bl_callers = 0`
          - 这说明下一步不应继续优先找普通直调 caller，
            而应转去追：
            - selector-3 / dispatch table
            - vtable / `ANECoreInterface::ANE_ProgramCreate`
            - `externalMethod` / IOUserClient 间接入口
        - 2026-06-12 新的 base-create local-handle bridge 事实：
          - `mps/ANE/.ane_runs/csv/ane_bootkc_base_create_handle_bridge_probe_fresh.csv`
            已确认：
            - `ANEDriver::ANE_ProgramCreate_gated`
              先清零 `[x29-0x58]`
            - 再：
              - `x1 = &local_program_handle_slot`
              - `bl ANE_CreateProgramHandle_gated`
            - 紧接着：
              - `x5 = &local_program_handle_slot`
              - 通过 provider create slot (`vtable+0x8a0`)
                传给 `ANEHWDevice::ANE_ProgramCreate`
            - device create 内部则：
              - `mov x26, x5`
              - `ldr x8, [x26]`
          - 并且同一个 local handle 还会在 driver 侧再次被 reload，
            用于：
            - `addProgramToANEMapping_gated`
            - `findProgramANEMapping_gated`
          - 这意味着：
            - selector-3/base-create 的 `arg5/out_handle_ptr`
              在 driver 边界并不缺失
            - 它已经是一个 concrete driver-authored local handle carrier
          - 因而当前阻塞应再下沉一层：
            - 不再是“bridge 层没有 `arg5/out_handle_ptr`”
            - 而是“lower base-create path 没有把这个已存在 local handle
              materialize 成 create-instance 那种
              accepted process/resource coherence”
          - 2026-06-13 新增
            `basecreate_handle_coherence_gap_note.md`
            后，当前可以把 selector-3/base-create 的 blocker
            再写得更硬：
            - selector-3/base-create 不缺 out-handle carrier
            - 也不缺 shared handle-materialization family
            - 当前 visible split 开始于：
              `additional_params+0x18 = *(arg5/out_handle_ptr)` 之后
            - 也就是：
              base-create 当前缺的不是 handle existence，
              而是 handle -> lower accepted process/resource coherence
          - 2026-06-13 新增
            `basecreate_lower_consumer_split_note.md`
            后，这条 lower path 当前至少可以固定为：
            - provisional resource insertion
            - subclass `programLoadFromMachoFile(...)`
            - `client_ctx+0x18` attach
            - later pending clear / wakeup / timer state
          - 因而 selector-3/base-create 下一步更值钱的问题已再收缩为：
            - `programLoadFromMachoFile(...)` success requirements
            - `client_ctx+0x18` attach 之后的 accepted-state coherence
        - 2026-06-12 base-create / create-instance handle family 并排结论：
          - `mps/ANE/.ane_runs/csv/ane_bootkc_handle_materialization_probe.csv`
          - `mps/ANE/.ane_runs/csv/ane_bootkc_base_create_handle_bridge_probe_fresh.csv`
          - 两条路当前都共享同一个 handle materialization family：
            - driver 先分配本地 handle slot
            - `ANEDriver::ANE_CreateProgramHandle_gated`
            - `ANEHWDevice::ANE_ProgramHandleCreate_gated`
            - `mach_absolute_time()` candidate
            - `lookupProgramResource(candidate, &process, 0)` collision check
            - publish accepted handle 到 `*out_handle`
          - create-instance 路与 base-create 路的差别不在 handle family 本身，
            而在 handle 进入 lower consumer 之后：
            - create-instance：
              `x5 -> additional_params+0x18 -> local_y -> process/resource coherence`
            - base-create：
              `x5 -> *(arg5/out_handle_ptr) -> additional_params+0x18`
              之后尚未进入 accepted coherence
        - 2026-06-12 新的 ProgramLoad process-args 形态事实：
          - `mps/ANE/.ane_runs/csv/ane_bootkc_program_load_process_args_probe_fresh.csv`
          - Legacy/RT `programLoadFromMachoFile`
            在调用 `ANE_ProcessCreate_gated(...)` 前，
            当前本地 `ANEProcessCreateArgs` 形态已与 create-instance 不同：
            - create-instance：
              `{ qword0 = resource-derived key,
                 qword8 = local_y,
                 qword10 = client key }`
            - ProgramLoad (Legacy/RT)：
              `{ qword0 = key_family_A,
                 qword8 = same key_family_A,
                 qword10 = separate flag/client-ish band }`
          - 这意味着 first divergence 已经早于：
            - later `resource+0x493a0` restore/writeback
            - later `params[0]` internal authoring
          - 当前更准确的最早分叉点是：
            - create-instance 进入 `ANE_ProcessCreate_gated`
              前仍保留 `args+0x08 = local_y`
            - base-create/load-side `ProgramLoad`
              进入 `ANE_ProcessCreate_gated`
              前已经把 `args+0x08`
              变成与 `qword0` 同族的 mirror key
          - 这也意味着：
            - 当前 first divergence
              已不应表述成“更晚的 `resource+0x493a0` writeback 差异”
            - 而应表述成：
              `ProgramLoad -> local ANEProcessCreateArgs`
              组装阶段已经偏离 create-instance 的
              `local_y` 形态
        - 进一步的局部来源事实：
            - 新 note:
              `mps/ANE/experiments/results/program_load_process_args_tuple_note.md`
            - Legacy 当前可见 tuple：
              `{ additional_params+0x18,
                 additional_params+0x18,
                 additional_params+0x0 }`
            - RT 当前可见 tuple：
              `{ additional_params+0x18,
                 additional_params+0x18,
                 additional_params+0x0 }`
            - 也就是说，
              ProgramLoad 不是丢掉了
              `additional_params+0x18`
              这条 key family，
              而是把 dual-key 结构直接改写成：
              `{ additional_params+0x18,
                 additional_params+0x18,
                 additional_params+0x0 }`
          - 因而更准确的 first-divergence 表述应改成：
            - create-instance：
              仍保留
              `{resource-derived key, local_y, client key}`
              的 dual-key 结构
            - ProgramLoad：
              直接改写成
              `{ additional_params+0x18,
                 additional_params+0x18,
                 additional_params+0x0 }`
              ，抹平了原来的
              `resource-key vs local_y`
              双键结构
          - 再与 `ANE_ProcessCreate_gated` 当前参数语义对照后，
            这条改写更像是 lower contract，而不是 incidental drift：
            - 当 `x3 = resource` 非空时，
              `ANE_ProcessCreate_gated`
              会绕过
              `lookupProgramResource(args[0], ...)`
              的 fallback 路
            - 但仍然会继续用：
              - `args[8]`
                做 secondary
                `lookupProgramResource(args[8], ...)`
              - `args[0x10]`
                做
                `findClient(args[0x10], ...)`
          - 这与 ProgramLoad tuple
            `{ additional_params+0x18,
               additional_params+0x18,
               additional_params+0x0 }`
            是一致的：
            - resource 已由 `x3`
              直接给出
            - 两个 numeric key 位都压成 hidden key family
              `additional_params+0x18`
            - client key 保持为
              `additional_params+0x0`
          - 结合现有 `additional_params` 证据，
            三个字段的当前 best-effort 语义已足够稳定：
            - `additional_params+0x18`
              = hidden numeric key family
            - `additional_params+0x0`
              = pv / client key
            - `additional_params+0x80`
              = task
          - 因而当前更高信噪比的下一问已经不再是：
            - “这三个字段分别是什么”
          - 而是：
            - secondary
              `lookupProgramResource(args[8], ...)`
              与
              `findClient(args[0x10], ...)`
              之后，
              create-instance 路和 ProgramLoad 路
              为什么会走向不同 acceptance
          - 当前更高价值的 acceptance 入口也已经足够清楚：
            - family-6 create/load/process-state stack
            - `resource+0x400d0`
              first-author / process-registry gate
            - `process+0x203fc`
              exact-state-2 rejection gate
          - 所以下一步最值得做的不是再解释字段，
            而是比较：
            - create-instance：
              `args[8] = local_y`
              在 family-6 stack 中
              如何进入 accepted state
            - ProgramLoad：
              `args[8] = additional_params+0x18`
              在同一 stack 中
              为什么仍落到
              `resource+0x400d0 / process+0x203fc`
              这组 rejection/coherence gate
        - 换句话说，当前最像的缺口已经进一步收窄为：
          - `selector-3 success -> ANE_ProgramInitialSetup -> ProgramLoad`
            之后，ProgramLoad 组装给 `ANE_ProcessCreate_gated`
            的本地 args 为什么已经偏离 create-instance 的
            `local_y` 形态
          - 以及 raw selector-3 路上，
            `additional_params+0x10`
            是否真的接到了 probe 的 caller-visible output buffer，
            还是只在 raw `outProgram` / wrapper payload
            上 carry 了有效 create-output state
          - 以及 selector-4/prepare 或更后阶段，
            是否才是第一次把这份 wrapper-internal state
            bridge 到 caller-visible external output
          - 以及这条更早的 args-shape 分叉，
            如何导致后面无法进入 accepted lower coherence
          - 而不是 `additional_params+0x10` 本身，
            也不是 handle-family / `arg5` carrier 本身
        - 2026-06-13 新增
          `selector4_owner0_ready1_wrapperdiff_note.md`
          后，selector-4 的 visible bridge 结论也能更硬：
          - `owner0 + ready1` 这条 wrapper prepare
            确实能从 `0x14` 进到 `0x02`
          - 但 visible wrapper 前后只改了：
            - `payload_u8_0xde0 : 2 -> 7`
            - `payload_u32_0xde4 : 0 -> 1`
          - 没有 visible writeback 到：
            - `wrapper+0x70/+0x98/+0xa8`
            - `payload+0xd78..0xda8`
          - 这说明当前 `0x02`
            更像 intermediate state，
            不是 caller-visible output / runtime-ready bridge 本身
        - 2026-06-13 新增
          `selector4_status2_intermediate_note.md`
          后，这个判断还能再收紧一层：
          - bootkc lower family 已明确：
            - `process+0x203fc = 0`
              -> `ANEProcess::init` /
                 `ANE_ProcessCreate_gated`
            - `process+0x203fc = 1`
              -> `ANE_SaveState` /
                 `ANE_RestoreStateEv.cold.2` /
                 save-unload-demote family
            - `process+0x203fc = 2` -> `isProcessValid(mode!=0)` 明确拒绝
          - 而当前 selector-4 `0x02` 动态路径
            又没有命中 static success 路应有的 visible writeback
          - 因而当前 `selector-4 status 0x02`
            更该视为 intermediate state，
            不是 visible success/writeback state
        - 2026-06-14 新增
          `programload_client_attach_boundary_note.md`
          与
          `ane_bootkc_programload_attach_boundary_probe.csv`
          后，`programLoadFromMachoFile(...)`
          和 `client_ctx+0x18` attach
          的边界也能更硬：
          - Legacy / RT `programLoadFromMachoFile`
            都不是“只做一点 setup 然后把事交给 caller”：
            - 都有自己的
              `ANE_ProcessCreate_gated(...)`
            - 都有自己的 late
              `findClient(...)`
            - 都有自己的 late
              caller-visible
              `*external_output = additional_params+0x18`
              publish
          - 当前 machine-local direct-BL 计数还明确显示：
            - Legacy load 内部：
              - `findClient` x2
              - `ANE_ProcessCreate_gated` x1
              - `preProcess` x1
              - `aneCmdSend` x2
            - RT load 内部：
              - `findClient` x2
              - `ANE_ProcessCreate_gated` x1
              - `preProcess` x1
              - `sendSetupCmd` x3
          - 而 `ANE_ProgramCreate_gated`
            里的 `client_ctx+0x18` attach
            只发生在：
            - resource vtable `+0x138`
              subclass load 已经返回 `0`
            - caller 自己又做了一次
              `findClient(...)`
              之后
          - 因而当前不能再把
            `client_ctx+0x18` attach
            视为：
            - first visible client gate
            - first visible publish step
            - 或 `ProgramLoad` 成功侧的主要未知数
          - 更准确的主线表述现在是：
            provisional resource insertion
            -> subclass `programLoadFromMachoFile(...)`
               已自带 ProcessCreate / findClient / publish
            -> caller-side
               `client_ctx+0x18` membership attach
            -> 仍缺更低的 accepted-state /
               reply / publish author
        - 2026-06-14 新增
          `programcreate_success_epilogue_boundary_note.md`
          与
          `ane_bootkc_programcreate_success_epilogue_probe.csv`
          后，caller 这段 post-return 尾巴也能再收紧：
          - 当前直接 BL 计数只有：
            - `findClient` x1
            - `releaseDartMapLock` x1
            - `commandWakeup` x2
            - `EnableMemoryUnwireTimer` x1
            - `ReleaseProgramResource` x1
          - 而对当前最关心的更低 async 路，
            direct BL 计数都是 0：
            - `handleOutstandingCommand`
            - `processCommandResponse`
            - `processTargetToHostIOCommand`
            - `setPendingUpdate`
            - `waitForPendingUpdate`
          - 这说明
            `ANE_ProgramCreate_gated`
            在 subclass load 返回 `0`
            之后的 visible success tail，
            更像：
            - attach / pending clear / wakeup
            - lock / timer housekeeping
            而不是新的 lower accepted-state author
          - 因而当前更准确的边界是：
            - `ProgramLoad` 内部 publish/gate
            - caller post-return tail
            都已经被 visible CPU-side 解释完
            - 剩余 gap 更该下沉到：
              later async completion /
              request-removal /
              lower reply-publish path
        - 2026-06-14 新增
          `selector3_livehandle_coherence_note.md`
          与
          `ane_selector3_livehandle_coherence_join.csv`
          后，local selector-3 `status=0`
          的剩余 gap 也能排掉一个浅解释：
          - base local wrapper 统一仍是：
            - `wrapper+0x70 = 0`
            - `payload+0xda8 = 0`
            - `wrapper+0xa8 = 0x100000000`
            - `payload_u8_0xde0 = 4`
          - 但即使把 live 成功
            `_ANEProgramForEvaluation`
            的：
            - `programHandle`
            - `queueDepth = 127`
            补丁写进 local wrapper/payload，
            selector-4 结果仍保持：
            - `handlepatch_status = 0x02`
            - wrapper 前后不再进一步 promote
          - 因而当前不能再把 local selector-3 的 blocker
            建模成：
            “只差 wrapper-visible handle/queueDepth 字段”
          - 更准确的是：
            local selector-3 已经构造出一层 partial internal shell，
            但缺的仍是更深的
            accepted-state / request-author / publish coherence
        - 2026-06-14 新增
          `selector3_live_mil_negative_note.md`
          后，payload/model-format 这条浅解释也被进一步削弱：
          - 在同一
            `live_tiny_mil_controller_device`
            上，
            直接把真实 working
            `live_artifact/model.mil`
            喂给 selector-3，
            结果仍然是：
            - `status = 0`
            - `prepare1 = 0x14`
            - `owner0_ready1 = 0x02`
            - `handlepatch = 0x02`
            - base wrapper 仍无 runtime handle publish
            - raw create output buffer
              也仍是 untouched sentinel
              (`diff_count = 0`)
            - raw prepare 仍是：
              `0xe00002c1 / 0xe00002c2`
          - 进一步把 `modelPath/modelIdentity`
            对齐到 live 成功
            `_ANEInMemoryModel`
            的真实 `modelURL/model.mil`
            后，
            结果仍然不变：
            - `0 -> 0x14 -> 0x02`
            - raw create output 仍 untouched
          - 这说明当前 local selector-3 的 partial shell
            不只是 `.hwx` / `data` / `model.mil`
            顶层 payload 形态，
            也不只是 visible `modelPath/modelIdentity`
            这层差异导致的
          - 更像缺的仍是：
            - outer request threading
            - retained companion / modelToken-side context
            - 或更低 accepted-state / publish coherence
        - 2026-06-14 新增
          `selector3_fresh_controller_device_note.md`
          后，device/control-state 这条浅解释也被进一步削弱：
          - 当前已能通过
            `_ANEDeviceController controllerWithProgramHandle: -> start`
            构造一个新的 fresh controller-backed device：
            - `fresh_controller_device != nil`
            - 有独立 `owner/service/connect` 布局
          - 但把同一
            `live_modelurl_mil`
            case 放到这个 fresh device 上后，
            结果仍然不变：
            - `status = 0`
            - `prepare1 = 0x14`
            - `owner0_ready1 = 0x02`
            - raw create output 仍 untouched
            - base wrapper 仍无 runtime handle publish
          - 因而当前不能再把主 blocker
            主要建模成：
            “只是用错了 visible device/control-state 实例”
          - 更像缺的仍是：
            - outer request threading
            - retained companion / modelToken-side context
            - create-output threading
            - 或更低 accepted-state coherence
        - 2026-06-14 新增
          `selector3_programhandle_open_device_note.md`
          后，visible ANEServices open-shape 这条浅解释也基本收口了：
          - 当前已按
            `_ANEDeviceController start`
            的真实 open 形态，
            复现出两条成功的
            `ANEServicesDeviceOpen(programHandle-open, controller-arg)`：
            - `live_controller_arg` -> `status=0`, `device != nil`
            - `fresh_controller_arg` -> `status=0`, `device != nil`
          - 但把
            `live_modelurl_mil`
            case 放到这两个真正 userland-open device 上后，
            结果仍完全不变：
            - `status = 0`
            - `0x14`
            - `0x02`
            - raw create output untouched
            - base wrapper 无 runtime handle publish
          - 因而当前不能再把主 blocker
            主要建模成：
            “还没复现正确的 visible ANEServices open path”
          - 到这里为止，
            已经连续排掉：
            - top-level payload / modelPath / identity
            - wrapper-visible handle 字段
            - live/fresh device instance
            - real ANEServices programHandle-open shape
          - 剩余 gap 更像：
            - hidden outer request context
            - retained companion / modelToken-side state
            - create-output threading
            - deeper accepted-state / publish coherence
        - 2026-06-14 新增
          `loadmodel_hidden_model_state_boundary_note.md`
          后，`loadModel...` 这侧的 hidden `_ANEModel` 状态也进一步收口了：
          - 当前 `aned_bin` 静态已把
            `-[_ANEServer loadModel:sandboxExtension:options:qos:withReply:]`
            到
            `-[_ANEProgramForLoad createProgramInstanceForModel:...error:]`
            的 handoff 压成一条具体参数链：
            - cached model bytes/len
            - `modelToken`
            - `modelFilePath`
            - qos / precompiled / powerSaving / skipPrepare / statsMask /
              memoryPoolID / lateLatch / keepWired
            - `modelIdentityStr`
            - owning pid
            - `cacheUrlIdentifier`
            - `aotCacheUrlIdentifier`
          - 同时在同一 `loadModel...` 函数体内：
            - `string_id` 只命中 log/signpost 文本与相邻取值点
            - `UUID` / `identifierSource` 没有命中 lower create-side 调用体
            - `sourceURL` 只是在 `modelURL == nil` 时回退出 path surface
          - 因而当前不能再把主 blocker
            主要建模成：
            “daemon/plain load 还注入了某个 generic hidden `_ANEModel` ivar
             （`UUID/string_id/identifierSource`）”
          - 更紧的当前 framing 是：
            若 daemon/plain load 仍比 local direct create 多一层 accepted
            context，它更像：
            - `modelToken` team/cs provenance
            - retained companion / ProgramDefinition state
            - create-output threading
            - deeper accepted-state / publish coherence
    - 仍未解决的点：
      - `ane_ioconnect_trace_interpose.dylib` 现阶段即使补到
        `IOConnectCallMethod`，在这个 local create probe 上仍未抓到
        selector-3 live trace；说明实际 IOKit 入口可能不是当前 interposer
        已覆盖的导出符号，或存在更低层/直连调用路径
      - 2026-06-14 又补做了更强的 negative recheck：
        `selector3_extended_iokit_trace_negative_note.md`
        - interposer 现在已额外覆盖：
          - `IOConnectCallScalarMethod`
          - `IOConnectTrap6`
        - `ane_services_program_create_runtime_probe.m`
          也新增了 `--only-case`
        - 但对单个
          `live_mil_nonprecompiled_path_live_modelurl_mil`
          case 的复跑里，
          `trace_selector3_recheck_v3.csv`
          仍然只有 CSV 表头，没有任何 traced call
        - 同时该单 case probe 仍会 CPU-bound 卡住，JSON 输出保持 `0B`
        - 因而当前不能再把下一步主要建模成：
          “再补一个 public IOConnect variant 就能看见 selector-3”
        - 更像要把观察点下沉到：
          - `_ANEServicesProgramCreate`
          - `ANE::ANEServicesDevice::ANE_ProgramCreate`
          - 或更低的 private wrapper / mach-message 面
      - 2026-06-14 新增
        `selector3_postacquire_runtime_interpose_note.md`
        后，这条 negative framing 又被进一步收紧了一层：
        - 当前已把 trace 改成：
          1. 先正常 `recover_live_device`
          2. 再只对已加载的
             `ANEServices.framework` /
             `AppleNeuralEngine.framework`
             做 post-acquisition runtime interpose
        - 这样单 case 已经能完整跑完，不再卡在 device-open 阶段
        - 但即使开启 `TRACE_ALL`，
          `trace_selector3_runtime_all_v1.csv`
          仍然只有表头，没有任何 captured call
        - 因而当前可以更明确地说：
          不是“startup-time DYLD interpose 恰好把流程卡住，导致看不见 selector-3”
          这么简单；
          更像是当前 host 上真正相关的 transport
          根本不走这条可被现有 dyld runtime interpose
          捕获的 public `IOConnect*` 面
        - 所以下一轮不要再主要围绕：
          - public `IOConnect*` interpose 扩点
          - dyld runtime interpose 语义
          打转
        - 更值钱的入口是：
          - 直接贴近
            `_ANEServicesProgramCreate`
            / `ANE::ANEServicesDevice::ANE_ProgramCreate`
          - 或去看 stub/import slot / debugger-side breakpoint
      - 2026-06-14 新增
        `selector3_import_stub_public_iokit_noop_interpose_note.md`
        后，这条主线又进一步收紧到
        “public symbol 已确认，但 runtime interpose 对 auth slot 无效”：
        - 新结果：
          `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_manual_v7.json`
        - 当前已确认：
          1. `rawCreateFn+0x108 -> 0x1a4e68338`
             的 runtime stub 现在已可完整解码为：
             - `adrp/add/ldr`
             - `braa x16, x17`
             - `slot_addr = 0x1f43cbdd0`
             - `slot_value = 0x18b001d18`
          2. `0x18b001d18`
             不是“像 public symbol 的某个地址”，而是本机真实
             `IOConnectCallStructMethod` 导出地址：
             - `ctypes.CDLL(.../IOKit).IOConnectCallStructMethod`
               返回同一个地址
             - `dyld_info -exports IOKit`
               也能对上 `_IOConnectCallStructMethod @ 0x3d18`
          3. `dyld_info -disassemble ANEServices`
             已能看到同形态导入 stub：
             - `_IOConnectCallStructMethod`
             - `add x17, #0xdd0`
             - `ldr x16, [x17]`
             - `braa x16, x17`
             与 runtime stub 逐字段对齐
          4. 但 probe 新增的 interpose 前后 slot snapshot 表明：
             - `runtime_trace_interpose_before.stub_decode.slot_value`
               = `0x18b001d18`
             - `runtime_trace_interpose_after.stub_decode.slot_value`
               仍然 = `0x18b001d18`
             - hook 地址
               `0x1002223d0`
               没有进入该 slot
          5. 同时
             `trace_selector3_runtime_manual_v7.csv`
             仍然只有表头
        - 因而当前可以更明确地说：
          不是“rawCreateFn 没走 public IOKit”，
          而是：
          `rawCreateFn` 的 selector-3 确实经由 public
          `IOConnectCallStructMethod` import stub，
          但当前 `dyld_dynamic_interpose`
          对这条 arm64e auth slot 没生效
        - 所以下一轮不要再主要围绕：
          - public `IOConnect*` 扩点
          - generic runtime interpose 语义猜测
          打转
        - 更值钱的是：
          1. 直接 patch / observe
             `0x1f43cbdd0` 这条 auth slot
             （要带正确的 arm64e PAC 处理）
          2. 或把断点直接下到：
             - `rawCreateFn+0x108` stub
             - `IOConnectCallStructMethod` export entry
          3. 再对照 raw create 的 live args
             与当前 manual public selector-3
             `0xe00002c2`
             的参数差异
      - 2026-06-14 新增
        `selector3_ready_gate_transport_match_note.md`
        后，selector-3 主线又往前推进了两层：
        - 当前已确认：
          1. arm64e 下这条 auth slot
             不只是“可解码”，而且“可正确签名、可直接写入”：
             - `slot_value_raw == sign_export_slot`
             - `vm_protect_rw_copy_status = 0`
             - `write_match = 1`
          2. patch slot 后，
             `trace_selector3_runtime_manual_v9_arm64e_patch.csv`
             已经能稳定抓到 selector-4，
             说明 hook 本身工作正常
          3. 但同一轮里仍没有 selector-3，
             因而问题不再是
             “hook 没生效 / transport 没走 public symbol”
          4. 静态反汇编
             `__ZN3ANE17ANEServicesDevice17ANE_ProgramCreate...`
             现在已明确给出 selector-3 前置门：
             - `[service + 0x18] == 1`
             - 否则直接走
               `0x19e69d198 -> mov w23, #0`
               返回，不发 send
          5. 这与当前默认 dynamic 结果完全对齐：
             - `service_ready_u8_0x18 = 0`
             - `raw_create_status = 0`
             - 没有 selector-3 trace row
          6. 进一步地，强制
             `service_ready_u8_0x18 = 1`
             后，
             `trace_selector3_runtime_manual_v10_arm64e_patch_ready1.csv`
             已首次 machine-locally 抓到真实 selector-3：
             - `selector = 3`
             - `ret = 0xe00002c2`
             - `input_size = 0x20`
             - `output_summary = selector=3 output=nil`
          7. 同时这轮 `raw_create_status_hex`
             也从默认的 `0x00000000`
             变成了：
             - `0xe00002c2`
             - 与 `manual_selector3_transport`
               完全一致
          8. 该 ready byte 的 visible 来源
             也已在用户态进一步收紧：
             - `ANE::ANEServicesDevice::ANEDeviceOpen`
               会把 selector-0 open reply 的
               `ANEDeviceInfo+0x1c`
               写到 `service+0x18`
             - `ANE::ANEHWDevice::ANEHWDeviceOpen`
               也有同形态写入
        - 因而当前可以更准确地说：
          不是“rawCreate 神秘成功但不发 selector-3”，而是：
          - 默认路径：
            ready-gate 未开，rawCreate 直接早退并返回 0
          - 强制 ready1 后：
            rawCreate 才真正发出 public selector-3，
            且 transport 返回值就是 `0xe00002c2`
        - 同时也能进一步解释旧现象：
          `raw_create_output_change.diff_count = 0`
          不只是“也许 driver 没写”，
          还因为这条 public selector-3 send
          本身就是：
          - `input_size = 0x20`
          - `outputStruct = nil`
        - 所以下一轮不要再主要问：
          - “rawCreate 到底有没有真正发 selector-3”
        - 这个问题已经回答。
        - 更值钱的新问题是：
          1. 正常高层路径里，
             到底谁负责把 `[service + 0x18]`
             从 `0` author 到 `1`
          2. 这一步对应的 accepted-state /
             pre-stage / attach / ready transition
             究竟在哪
          3. 为什么在当前 local create case 里，
             这一步缺失后仍能先返回一个
             “status=0 的假成功壳”
      - 2026-06-14 新增
        `open_reply_ready_byte_alignment_note.md`
        后，open-path 这条支线也已经进一步排除了
        “只是 open 形态传错”的解释：
        - 当前已确认：
          1. `_ANEDeviceController start`
             的真实用户态 open 调用形态是：
             - `ANEServicesDeviceOpen(&outDevice, buf, self, fDeviceCallback)`
             - 非 privileged 路：
               `usageType = 1`
               `programHandle = self.programHandle`
          2. 新的 controller-style open probe
             已对齐到这条 live 调用形态：
             - recovered live/fresh controller object
             - real `fDeviceCallback`
          3. machine-local 成功/失败矩阵现在很清楚：
             - `usage1 + handle0`      -> `0x4`
             - `usage1 + liveHandle`   -> `0x0`
             - `usage2 + handle0`      -> `0x18`
             - `usage2 + liveHandle`   -> `0x18`
          4. 也就是说，
             当前唯一成功的 local open 形态就是：
             - `usageType = 1`
             - `programHandle = live handle`
             这与 live non-privileged 路吻合
          5. 但即使在这条“形态已对齐、open 已成功”的路径上，
             新 device 的
             `service_ready_u8_0x18`
             仍然稳定是 `0`
          6. 这个 `0`
             现在已经被进一步压成
             “selector-0 reply 自己给出来的 0”，不是后续异步变化：
             - 成功 open 的
               immediate / +10ms / +100ms
               三次快照都还是 `0`
             - 打开 selector-0 trace 后，
               成功 open 的 `0x68` reply buffer
               头 32 字节也直接显示：
               - `0x18..0x1b = 0x2710`
               - `0x1c..0x1f = 0x00000000`
             - 这与
               `ANEDeviceInfo+0x1c -> service+0x18`
               的静态 copy 完全对齐
        - 因而当前可以更明确地说：
          ready byte 不是因为
          - controller arg 传错
          - callback 传错
          - usageType / handle 组合完全走偏
          才变成 `0`
        - 更像是：
          selector-0 open reply 自身在这条成功 local path 上
          就把 `ANEDeviceInfo+0x1c`
          产成了 `0`
        - 所以下一轮不要再继续主要围绕：
          - `ANEServicesDeviceOpen` 参数组合穷举
          打转
        - 更值钱的是：
          1. 直接看 selector-0 open reply / lower open state
             为什么给出 `+0x1c = 0`
          2. 这是否对应：
             - missing attach
             - device state demotion
             - lower accepted-state 未完成
             - 或 callback / receiver start 之前的过早观测
        - 2026-06-14 新增的 full decode 结果又把 selector-0 这条线压实了一层：
          - 新证据：
            - `benchmark_results/private_ane/ane_services_program_create_open_sweep_v7_selector0_decode.json`
            - `mps/ANE/.ane_runs/csv/trace_open_selector0_v3_decode.csv`
          - 当前 runtime trace 已改成：
            - 对 selector-0 先抓调用前 input summary，
              再抓调用后 output summary
            - 不再被“同一 0x68 buffer 既当 input 又当 output”
              这个 in-place 调用形态误导
          - 静态/动态已经对齐：
            - selector-0 发下去的并不是最上层 cfg，
              而是 `ANEServicesHandleDeviceOpen`
              synth 出来的 `ANEDeviceInfo` request：
              - `qword_0x00 = programHandle`
              - `qword_0x08 = ANE::ANERequestReceiver::FrameDone`
              - `qword_0x10 = controller/context`
              - `qword_0x18 = timeout`
          - 成功 selector-0 reply 现在也不再只是“看见 +0x1c=0”：
            - 当前成功 reply 会稳定写出：
              - `qword_0x48 = 0x000000c000000020`
              - `qword_0x50 = 0x0000000100000000`
              - `qword_0x58 = 0x0000000000000007`
              - `qword_0x60 = 0x0000000280000000`
              - `u32_0x4c = 192`
              - `u32_0x50 = 0`
            - 但 `u32_0x1c` 仍然稳定是 `0`
          - 失败 selector-0 (`ret = 0xe00002f0`) 则整块 0x68 buffer 保持不变
          - 2026-06-14 新增的 wrapper/service decode
            已把上一轮的 `0x4c/0x50` 不一致解释清楚：
            - 新证据：
              - `benchmark_results/private_ane/ane_services_program_create_open_sweep_v8_wrapper_service_decode.json`
              - `mps/ANE/.ane_runs/csv/trace_open_selector0_v4_wrapper_service_decode.csv`
            - 当前 public open 返回的 `device`
              不是底层 `ANE::ANEServicesDevice *`
              而是：
              - `wrapper_base + 0x40`
            - 成功 local open 的动态字段已经对齐为：
              - `public_wrapper_base`
              - `underlying_service_device = *(wrapper_base + 0x8)`
              - `public_controller_arg = *(wrapper_base + 0x10)`
              - `public_callback_fn = *(wrapper_base + 0x18)`
            - 同时成功 local path 上：
              - `underlying_service_device_u32_0x88 = 1`
            - 这与静态
              `ANE::ANEServicesDevice::ANEDeviceOpen`
              的分支完全对齐：
              - 只有当 `service+0x88 != 1`
                时才会把
                `reply[0x4c]/reply[0x50]`
                拷到
                `service+0x1c/service+0x20`
            - 所以当前
              - `service_u32_0x1c = 0`
              - `service_u32_0x20 = 0`
              已不再是异常现象，
              而是当前 ANEDriver-style subtype 的正常结果
            - wrapper 侧也已经有新的对齐证据：
              - `public_wrapper_u8_0x58 = 1`
              - `public_wrapper_u32_0x5c = 7`
              - `public_wrapper_qword_0x60 = 0x0000000280000000`
              与 reply tail 对齐
          - 因而 selector-0 这条线当前剩下的核心问题重新收敛为：
            - 为什么 successful local selector-0 reply
              仍然 author
              `u32_0x1c = 0`
            - 也就是为什么
              `underlying_service_device + 0x18`
              最终还是 `0`
              并继续卡住 rawCreate ready-gate
          - 2026-06-14 新增的 callback/receiver 静态补证：
            - `MyANEServicesDeviceMessageNotification`
            - `ANE::ANERequestReceiver::startReceive`
            - `ANE::ANERequestReceiver::registerANEServicesDevice`
            当前都没有看到会在 public open return 后
            再去 author
            `underlying_service_device + 0x18`
          - 因而当前可以更明确地排除：
            - “ready 只是稍后由 startReceive / callback 补写”
          - 2026-06-14 新增的 bootkc 结论已经把 `reply+0x1c`
            的 author 路重新定位：
            - selector-0 wrapper：
              `__Z14ANE_DeviceOpenP15ANEClientDevicePvP25IOExternalMethodArguments`
            - bridge：
              `ANEClientDevice::open(ANEDeviceInfo *)`
            - 在 `ANEClientDevice::open(...)` 中，
              当前机器明确有：
              - `reply+0x1c <- (device+0x28 & 1)`
              - `reply+0x5d <- (device+0x29 & 1)`
            - 也就是说：
              `reply+0x1c`
              不是先由 provider vtable lower call
              直接写出来的，而是先由 `ANEClientDevice` 自身状态
              materialize 到 output
          - `ANEClientDevice+0x28/+0x29`
            又已经继续回溯到：
            - `ANEClientDevice::init(ANEClientInfo)`
              把
              `ANEClientInfo+0x10/+0x11`
              复制进
              `device+0x28/+0x29`
            - `ANEClientInfo::create(task, j, b1, b2)`
              当前机器明确是：
              - `+0x10` <- `hasTaskEntitlement(task, "com.apple.ane.iokit-user-access")`
                when `b1=1`, else `0`
              - `+0x11` <- `hasTaskEntitlement(task, "com.apple.ane.allow-dataChaining-access")`
                when `b2=1`, else `0`
          - 当前成功 local controller-style open
            之所以必然给出 `reply+0x1c = 0`，
            现在已经不是猜测：
            - `usageType=1`
              会走
              `ANEHWDevice::newUserClient`
              的 direct-path 分支
            - direct-path init 调的是：
              `ANEClientInfo::create(task, 1, 0, 1)`
            - 因为 `b1=0`，
              所以：
              - `ANEClientInfo+0x10 = 0`
              - `device+0x28 = 0`
              - `reply+0x1c = 0`
          - regular user-client 路反而是：
            - `H11ANEInUserClient::init`
              -> `ANEClientInfo::create(task, 2, 1, 1)`
            - 这条路会检查
              `com.apple.ane.iokit-user-access`
          - 新动态补证：
            - `benchmark_results/private_ane/ane_services_program_create_open_sweep_v9_usage3.json`
              中 controller-style `usageType=3`
              全部返回 `0x18`
            - `benchmark_results/private_ane/ane_services_program_create_open_sweep_v10_outermode3.json`
              中 outer `mode=3`
              也全部返回 `0x18`
            - 当前 probe 二进制
              `codesign -d --entitlements :-`
              无内嵌 entitlements
          - 因而当前可以更明确地说：
            - 不是“successful open 的 lower ready state 神秘地没变成 1”
            - 而是：
              当前唯一成功的 local open family
              本来就是 direct-path，
              它会把 `reply+0x1c`
              设计成 0；
              能让这一位来自 entitlement-checked 路径的 regular client
              在当前 probe 上又走不通

## 当前重点对象

- framework:
  - `ANECompiler.framework`
  - `ANEServices.framework`
  - `Espresso.framework`
- class / selector:
  - `_ANEInMemoryModelDescriptor`
  - `_ANEModel`
  - `_ANEVirtualClient`
  - `_ANEDaemonConnection`

## 关键证据文件

- `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_persistent_aux_profile_profile/profile_summary.json`
- `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_persistent_aux_profile_profile/transformer_bottleneck_ledger.csv`
- `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_persistent_aux_profile_profile/transformer_timings.csv`
- `benchmark_results/private_ane/test_clean_full_private_runtimeclone_off_persistentaux_profile/profile_summary.json`
- `benchmark_results/private_ane/test_clean_full_private_fixedcache_mask2_currentcode_profile/profile_summary.json`
- `benchmark_results/private_ane/test_clean_full_private_fixedcache_mask2_currentcode_bridgeprofile_profile/profile_summary.json`
- `benchmark_results/private_ane/test_clean_full_private_global_mask2_currentcode_bridgeprofile_profile/profile_summary.json`
- `benchmark_results/private_ane/test_clean_full_private_historical_shape_bridgepatched_profile/profile_summary.json`
- `benchmark_results/private_ane/realtime_stft_client_file_probe.json`
- `benchmark_results/private_ane/stft_client_file_probe_fixed.json`
- `benchmark_results/private_ane/block_client_file_probe.json`
- `benchmark_results/private_ane/weighted_client_load_probe_pre.json`
- `benchmark_results/private_ane/weighted_client_load_probe_pre_packed.json`
- `benchmark_results/private_ane/block_client_file_probe_with_error.json`
- `benchmark_results/private_ane/block_client_file_probe_packed_bridge_debug_verbose_v3.json`
- `benchmark_results/private_ane/weighted_client_eval_probe_pre_packed.json`
- `benchmark_results/private_ane/weighted_client_eval_probe_pre_packed_variants.json`
- `benchmark_results/private_ane/weighted_pack_variants_pre/summary.json`
- `benchmark_results/private_ane/weighted_fresh_pack_pre_load_stable.json`
- `benchmark_results/private_ane/weighted_fresh_pack_pre_eval_stable.json`
- `benchmark_results/private_ane/weighted_fresh_pack_pre_eval_threeout_stable.json`
- `benchmark_results/private_ane/publicload_privateeval_probe_pre_directprocess.json`
- `benchmark_results/private_ane/weighted_fresh_pack_gate_eval_stable.json`
- `benchmark_results/private_ane/weighted_fresh_pack_ffn_eval_stable.json`
- `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_pre/eval_probe_rebuilt.csv`
- `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_ffn/eval_probe_rebuilt.csv`
- `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_pre/fresh_lifecycle_rebuilt.csv`
- `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_ffn/fresh_lifecycle_rebuilt.csv`
- `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_pre/cacheid_fresh.csv`
- `mps/ANE/.ane_runs/csv/runtime_wrapper_aug_weighted_pre/second_lifecycle_rebuilt.csv`
- `benchmark_results/private_ane/test_clean_wrapper_route_onechunk.private_ane_child/parent_watchdog_failure.json`
- `benchmark_results/private_ane/test_clean_wrapper_route_onechunk_rerun2.json`
- `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch1.json`
- `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4.json`
- `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4_vs_mlx.json`
- `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4_tmp_internal.json`
- `benchmark_results/private_ane/test_clean_wrapper_route_fullaudio_batch4_tmp_internal_rerun.json`
- `benchmark_results/private_ane/wrapper_warm_load_probe_external_time_root.json`
- `benchmark_results/private_ane/precompiled_file_route_probe_time_root_v4.json`
- `benchmark_results/private_ane/precompiled_file_route_probe_time_root_v5.json`
- `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v1_notrace.json`
- `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v2_emptyids.json`
- `mps/ANE/experiments/aned_bin`
- `benchmark_results/mlx_full_roformer_profile/test_clean_full_torch_mps_vs_mlx_full_current.json`
- `mps/ANE/.ane_runs/csv/ane_runtime_rehydrate_probe.csv`
- `benchmark_results/private_ane/runtime_clone_bridge_smoke.json`
- `mps/ANE/experiments/results/runtime_rehydrate_clone_note.md`
- `benchmark_results/private_ane/test_clean_runtime_clone_onechunk_prime4.private_ane_child/parent_watchdog_failure.json`
- `benchmark_results/private_ane/test_clean_runtime_clone_onechunk_relaxed.private_ane_child/parent_watchdog_failure.json`
- `mps/ANE/.ane_runs/csv/ane_bootkc_programload_attach_boundary_probe.csv`
- `mps/ANE/experiments/results/programload_client_attach_boundary_note.md`
- `mps/ANE/.ane_runs/csv/ane_bootkc_programcreate_success_epilogue_probe.csv`
- `mps/ANE/experiments/results/programcreate_success_epilogue_boundary_note.md`
- `mps/ANE/.ane_runs/csv/ane_daemon_program_lower_gate_join.csv`
- `mps/ANE/experiments/results/daemon_program_lower_gate_join_note.md`
- `mps/ANE/.ane_runs/csv/ane_precompiled_error_family_join.csv`
- `mps/ANE/experiments/results/precompiled_170004_family4_note.md`
- `mps/ANE/.ane_runs/csv/ane_selector3_livehandle_coherence_join.csv`
- `mps/ANE/experiments/results/selector3_livehandle_coherence_note.md`
- `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v21_live_mil_case.json`
- `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v22_live_modelurl_case.json`
- `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v23_fresh_controller_case.json`
- `benchmark_results/private_ane/ane_services_program_create_runtime_probe_v24_programhandle_open_case.json`
- `mps/ANE/experiments/results/selector3_live_mil_negative_note.md`
- `mps/ANE/experiments/results/selector3_fresh_controller_device_note.md`
- `mps/ANE/experiments/results/selector3_programhandle_open_device_note.md`
- `mps/ANE/experiments/results/loadmodel_hidden_model_state_boundary_note.md`
- `benchmark_results/private_ane/ane_services_program_create_open_sweep_v7_selector0_decode.json`
- `benchmark_results/private_ane/ane_services_program_create_open_sweep_v8_wrapper_service_decode.json`
- `benchmark_results/private_ane/ane_services_program_create_open_sweep_v9_usage3.json`
- `benchmark_results/private_ane/ane_services_program_create_open_sweep_v10_outermode3.json`
- `mps/ANE/.ane_runs/csv/trace_open_selector0_v3_decode.csv`
- `mps/ANE/.ane_runs/csv/trace_open_selector0_v4_wrapper_service_decode.csv`
- `mps/ANE/.ane_runs/csv/trace_open_selector0_v5_usage3.csv`
- `mps/ANE/.ane_runs/csv/trace_open_selector0_v6_outermode3.csv`
- `mps/ANE/experiments/results/open_reply_ready_byte_alignment_note.md`
- `mps/ANE/.ane_runs/csv/trace_selector3_recheck_v3.csv`
- `mps/ANE/experiments/results/selector3_extended_iokit_trace_negative_note.md`
- `mps/ANE/.ane_runs/selector3_recheck_v5.sample.txt`
- `mps/ANE/.ane_runs/csv/trace_selector3_runtime_v1.csv`
- `mps/ANE/.ane_runs/csv/trace_selector3_runtime_all_v1.csv`
- `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_v1.json`
- `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_all_v1.json`
- `mps/ANE/experiments/results/selector3_postacquire_runtime_interpose_note.md`

- 2026-06-17 12:18 当前 5 个终态 group 的最合理映射（高置信推断，不是最终实锤）:
  - 当前基于三条证据综合判断：
    1. `InferenceError` 顶层真实 case 顺序已知，且更像零基 tag `0..24`；
    2. `ModelManagerServices.__TEXT,__const` 的 `0x25a773a10..` 连续 `u32=1..24` 更像 case-tag 常量区；
    3. `TokenGenerationError.toInferenceError` 的 5 个终态 group 通过 shared-cache slot 最终选中这块常量区中的不同表项。
  - 因而当前最合理的 group->InferenceError 候选是：
    - `0x4A8` <- `case 4` (`cancelled`)
      -> `InferenceError.operationCancelled`（零基 tag 19，1-based 序号 20）
    - `0x468` <- `case 12` (`documentRegistrationFailure`)
      -> 更像 `InferenceError.unspecifiedUnderlyingError` / `internalError` 这一类 context-bearing generic failure
    - `0x450` <- `case 2` (`networkError`)
      -> 更像 `InferenceError.networkError`（零基 tag 12，1-based 序号 13）
    - `0x4A0` <- `cases 7,8,9,15` (`invalidGrammar/invalidParameters/toolInvocationFailure/safetyViolation`)
      -> 更像 `InferenceError.invalidClientData` / `operationNotAllowed` / `internalError` 这一类 grouped business failure；
         其中 `safetyViolation` 可能把该组推向 `operationNotAllowed`，但未最终证死。
    - `0x498` <- `cases 3,5,6,10,11,13,14,16,17`
      (`tooManyTokens/unservicableConfiguration/unknownSpecialToken/modelExecutionError/documentRegistrationFailure/authenticationFailure/safetyViolation?/unsupportedGuide/malformedResponse`)
      -> 更像承接大多数 context-bearing generic conversion 的主组，候选优先级目前是
         `unspecifiedUnderlyingError` > `internalError` > `hostFailed/loadFailed/inferenceFailed`。
  - 当前最稳能先写死的只有：
    - `cancelled -> operationCancelled`
    - `networkError -> networkError`
  - 其余组仍需要继续找 `ModelManagerServices.__TEXT,__const` 这块表的消费链来收口。

- 2026-06-17 12:36 当前 5 个终态 group -> `InferenceError` 的高置信映射：
  - 基于现有 machine-local 证据，`ModelManagerServices.__TEXT,__const @ 0x25a7739f0..0x25a773a5c` 中这串常量区应按零基 case tag 解读；live 侧读到的终态槽位指针减 slide 后正好落到该区。
  - 因而当前 5 个终态 group 的最合理、已足够稳定的映射是：
    - `0x28F63A450` -> static table item `0x25a773a3c` -> zero-based tag `12` -> `InferenceError.networkError`
    - `0x28F63A468` -> static table item `0x25a773a34` -> zero-based tag `10` -> `InferenceError.rateLimited`
    - `0x28F63A498` -> static table item `0x25a773a28` -> zero-based tag `7` -> `InferenceError.inferenceFailed`
    - `0x28F63A4A0` -> static table item `0x25a773a10` -> zero-based tag `1` -> `InferenceError.invalidClientData`
    - `0x28F63A4A8` -> static table item `0x25a773a58` -> zero-based tag `19` -> `InferenceError.operationCancelled`
  - 这意味着当前 `TokenGenerationError -> InferenceError` 收敛面已经可以先写成：
    - `cancelled` -> `operationCancelled`
    - `networkError` -> `networkError`
    - `tooManyTokens/documentRegistrationFailure/...` 主组 -> `inferenceFailed`
    - `invalidGrammar/invalidParameters/toolInvocationFailure/safetyViolation` 组 -> `invalidClientData`
    - `rateLimited` / 文档资源相关组 -> `rateLimited`
  - 其中最后两条仍建议继续找 `ModelManagerServices` 消费链做最终实锤，但当前已经超出“纯候选”阶段。

- 2026-06-17 12:49 关于“静态消费链是否已足够闭环”的当前结论：
  - 当前虽然还没有从 `ModelManagerServices` 里拿到对 `0x25a7739f0..0x25a773a5c` 的普通 data xref，但这不再构成主要 blocker。
  - 原因是：
    1. `toInferenceError` 尾部已经静态确认经 `0x274de7718 -> metadata/value witness` 收尾；
    2. live 终态槽位已直接读到 shared-cache 指针；
    3. 这些指针减 slide 后严格落到 `ModelManagerServices.__TEXT,__const` 的 `InferenceError` 相关常量区；
    4. 常量区内容本身就是 `InferenceError/Context/CodingKeys` 文本 + 连续 `u32` tag 序列。
  - 因而当前链条已经足够收紧成：
    `TokenGenerationError.toInferenceError`
    -> 5 个终态 group
    -> 选 `ModelManagerServices.__TEXT,__const` 中的 `InferenceError` 常量表项
    -> 经 `InferenceError` metadata/value witness 写回结果 enum。
  - 还剩下的不是“case 映射是否成立”，而只是“`ModelManagerServices` 内部具体哪个 consumer function`”这一层函数名级别的补强。

- 2026-06-17 13:02 新增 ABI 级收口证据：
  - `TokenGenerationError.toInferenceError` 统一收尾里的这段序列：
    - `0x274de7720` 先取回目标 enum metadata
    - `0x274de772c` 从 metadata 前一字取 value witness table 指针
    - `AUTDA` 使用 discriminator `0x2E3F`，该值与 Swift ABI 中 `ValueWitnessTable` 的 ptr-auth discriminator 一致
    - `0x274de773c` 取 VWT 某个 enum witness slot
    - `0x274de774c` 通过 discriminator `0xB2E4` 做 `BLRAA` 调用
  - 结合 Swift 官方 ABI 源 `swift/include/swift/ABI/MetadataValues.h` 中 ptr-auth discriminator 常量：
    - `ValueWitnessTable = 0x2e3f`
    - `DestructiveInjectEnumTag = 0xb2e4`
    - `GetEnumTagSinglePayload = 0x60f0`
    - `StoreEnumTagSinglePayload = 0xa0d1`
    - `DestructiveProjectEnumData = 0x041d`
    - `GetEnumTag = 0xa3b5`
  - 因而当前可以把 `0x274de774c` 这一调用从“疑似写 enum tag”提升为 ABI 级事实：
    - 它就是对目标 `InferenceError` value witness table 上 `destructiveInjectEnumTag` 槽位的调用
    - 也就是把前面选好的 tag（`W19`）真正注入结果 enum。
  - 这使得当前链条进一步收紧成：
    `TokenGenerationError.toInferenceError`
    -> 选 `ModelManagerServices.__TEXT,__const` 中的 `InferenceError` 相关 tag 项
    -> `InferenceError` metadata
    -> `destructiveInjectEnumTag`
    -> 最终结果 enum


- 2026-06-17 12:38 当前 `ModelManagerServices` 侧已经拿到的 `InferenceError` consumer 链（新事实）：
  - 围绕 `0x25a7739f0..0x25a773a5c` 这块 `InferenceError/Context` + `u32 1..24` 常量区，虽然普通 data xref 仍为空，但本轮已在同一 framework 内补出三条真实消费面：
    1. `0x25a63e844`：`InferenceError` case-name 分发表
       - `otool` 明确显示它先通过 `0x25a63ed20` 取 `InferenceError` metadata，
         再经 `0x25a63ed40` / VWT project 取 enum tag，随后按 25-case jump table 分发到
         `invalidClientData` / `operationCancelled` / `rateLimited` / `networkError` 等字符串字面量。
       - 证据点：
         `0x25a63ea64` -> `"invalidClientData"`
         `0x25a63ece8` -> `"operationCancelled"`
         同函数中还可见 `responseEncodingFailed` / `unsupportedRequestType` / `operationNotAllowed` / `assetVersionMismatch` / `conversionNotSupportedError` 等 case-name 字面量。
    2. `0x25a63f9d4`：`InferenceError` -> 整数错误码分发表
       - 已强制定成函数并反编译；它先 project `InferenceError` tag，再按 25-case switch 返回固定整数码。
       - 当前 machine-local 码表：
         - `notImplemented -> 2002`
         - `invalidClientData -> 2014`
         - `unsupportedRequestType -> 2003`
         - `responseEncodingFailed -> 2004`
         - `alreadyLoaded -> 2005`
         - `notLoaded -> 2006`
         - `loadFailed -> 2007`
         - `inferenceFailed -> 2008`
         - `operationNotAllowed -> 2009`
         - `streamNotFound -> 2010`
         - `rateLimited -> 2011`
         - `internalError -> 2012`
         - `networkError -> 2016`
         - `resourcesBusy -> 2017`
         - `hostFailed -> 3001`
         - `unspecifiedUnderlyingError -> 2001`
         - `unrecognizedUnderlyingError -> 2001`
         - `xpcError -> 2015`
         - `unspecified -> 2000`
         - `operationCancelled -> 2013`
         - `assetVersionMismatch -> 2018`
         - `conversionNotSupported -> 2019`
         - `deviceConnectionError -> 2020`
         - `versionNotSupported -> 2021`
         - `hostError -> 3000`
       - 这说明 `0x25a773a10..0x25a773a5c` 不只是反射残留，而是被真实 error consumer 路径消费的 case-tag 区。
    3. `0x25a63f4d8`：`ModelManagerError -> InferenceError` 桥接 / 重封装函数
       - 反编译结果显示它分两路：
         - 一路直接处理 `ModelManagerError` 并在异常情况下打出
           `"Received a ModelManagerError wrapping an InferenceError"`
         - 另一路在 `objc_msgSend$domain` / `objc_msgSend$code` 后组装 `InferenceError.Context`，再把 context payload 写回结果结构。
       - 同函数内部还会在未知 tag 情况下打出
         `"InferenceError: got unrecognized error %@"`。
  - 这三条链共同说明：
    - `TokenGenerationError.toInferenceError` 终态选中的 `0x25a773a10/28/34/3c/58` 等表项，确实落在 `ModelManagerServices` 自己的真实 `InferenceError` 消费面上；
    - 剩余未补的已经不是“5 个 group 是否映射到对应 case”，而是这些 consumer 函数的精确 Swift 符号名，以及它们与 `TokenGenerationInference:293` 的最后一跳调用关系。
  - 对 `293` 的影响：
    - 现有最强假设应再收紧一层：`TokenGenerationInference:293` 更像 `TokenGenerationError` / `ModelManagerError` / `InferenceError` 之间的 enum project / rebox / convert helper family；
    - 它不太像单纯 payload finalize，因为 `ModelManagerServices` 侧已经能看到完整的 case-name、error-code、bridge/context 三层消费者。


- 2026-06-17 13:06 关于 `TokenGenerationInference:293` 的新收口：
  - 本轮直接打开 `TokenGenerationInference`，对 `convertToInferenceError`
    `0x2750d0990`、以及代表性 throw-path callsite
    `0x2751689ec` / `0x275165798` 做了 machine-local 反汇编与反编译。
  - 当前可明确写死的事实：
    1. `convertToInferenceError`
       `0x2750d0990`
       的三路语义已经足够清楚：
       - 先尝试把输入 `Error` 动态投影成 `TokenGenerationError?`
       - 若成功：
         - 把 `TokenGenerationError?` project 到临时位点
         - 拷到另一份临时栈位
         - 然后调用 `293`
         - 再销毁这份临时 `TokenGenerationError?`
       - 若失败，再尝试把输入 `Error` 动态投影成 `ModelManagerServices.InferenceError?`
         - 若成功：直接把已有 `InferenceError` 拷到输出，不经过 `293`
       - 两者都失败时：
         - 若是 `Swift.CancellationError`，直接取 `MEMORY[0x28F63A4A8]`
           -> `operationCancelled`
         - 否则走 `localizedDescription/domain/code/userInfo`
           组 `InferenceError.Context`
           并取 `MEMORY[0x28F63A498]`
           -> `inferenceFailed`
    2. 因而 `293` 不是泛化的 payload finalize，也不是所有错误路径都会走的一步；
       它只出现在“已确认输入是 `TokenGenerationError`，现在要把它转成 `InferenceError`”的那一条分支上。
    3. 在代表性 throw-path
       `0x2751689e0..0x2751689f4`
       中，形态已经很明确：
       - 先通过 `1306` 拿到 `InferenceError` 相关结果
       - `MOV X8, X1`
       - `BL 293`
       - `MOV X21, X27`
       - `BL 1399`
       这里的 `293` 仍然不是“生成错误对象”的主逻辑，而更像对上一跳准备好的 error payload / enum slot 做最后的 in-place convert/rebox，以满足后续 `1399` 的 throw ABI。
    4. `convertToInferenceError`
       里还能看到对 `0x28F63A4A8`
       (`operationCancelled`) 和 `0x28F63A498`
       (`inferenceFailed`) 的直接取用；这与前面在 `TokenGeneration.framework`
       `toInferenceError` 中确认的终态 group -> shared-cache slot 映射相互吻合。
  - 当前最强结论应更新成：
    - `293` = `TokenGenerationError? -> ModelManagerServices.InferenceError` 这条专用转换链上的 in-place convert / rebox helper；
    - 它服务于 enum/project/value-witness 语义，且只在相应 typed-error 分支上触发；
    - 它不是“所有 throw-path 都必须走的统一 finalize”。


- 2026-06-17 13:12 关于 `293` 调用约定/使用面的进一步收紧：
  - 对 `j__$..._293` 的 code xref 本轮已拿到 20+ 个真实 callsite，集中分布在：
    - `OnDevice.AssetRepository.handleCustom...`
    - `OnDevice.ContextFactory.supportedTools...`
    - `TG_OnDeviceProvider.compileAdapter...`
    - `TG_OnDeviceProvider.requestStream...`
    - `classify` 等少量 throw-path helper
  - 这些 callsite 的共性已经足够清楚：
    1. 上一跳通常先通过 `1306` 或等价 helper 产出一个 `InferenceError` 相关值；
    2. 紧接着把某个 companion 值/side-band 位点放进 `X8`（典型形态是 `MOV X8, X1`）；
    3. 然后 `BL 293`；
    4. 之后再进 `1399` / `1400` 这类更靠近 throw / return ABI 的收尾 helper。
  - 当前最有代表性的证据仍是：
    - `0x2751689e0..0x2751689f4`
      明确是
      `1306 -> MOV X8, X1 -> 293 -> 1399`
    - `0x275165798` / `0x275165a24` / `0x275165b7c` / `0x275165d18`
      等 compileAdapter 路径上也反复出现同类结构。
  - 因而当前可再收紧一层的结论是：
    - `293` 不只是“TokenGenerationError? -> InferenceError convert helper”，
      还是一个显式依赖 side-band 输入（经常走 `X8`）的 in-place rebox / slot-fixup helper；
    - 它位于“typed error 已经初步确定”之后、“最终 throw ABI 收尾”之前。


- 2026-06-17 13:18 关于 `293` 的 `X8` 语义，本轮可再收紧一层：
  - 当前更像“目标输出槽 / 间接返回位点”，而不只是随便的 side-band。
  - 关键证据：
    1. `convertToInferenceError 0x2750d0990`
       的反编译签名已经是：
       `__usercall convertToInferenceError(_:)@<X0>(__int64 a1@<X0>, __int64 a2@<X8>)`
       并且函数一开始就把来参 `X8` 存到 `var_60`，后面在
       `TokenGenerationError?` 成功分支里直接
       `LDUR X8, [X29,#var_60]` -> `BL 293`。
       这说明 `293` 吃到的 `X8` 不是现场临时拼出来的普通参数，而是上一层 ABI 明确传下来的目标位点。
    2. 在多个 callsite 中，`293` 前都能看到同类“先准备目标对象，再把 companion/结果位点塞进 `X8`”的形态；
       最典型仍是：
       `1306 -> MOV X8, X1 -> 293 -> 1399`。
    3. `classify` / `handleCustom` / `requestStream` 这些 callsite 中，`293` 前都紧邻一段 `destructiveInjectEnumTag` 或等价 typed-error 物化序列，之后立刻进入 `1399/1400` 或销毁路径。
  - 因而当前最具体的 machine-local 结论可以写成：
    - `293` = 依赖调用者通过 `X8` 传入目标输出槽/间接返回位点的 in-place error rebox / slot-fixup helper；
    - 它负责把前一跳已经选好的 typed error/materialized enum，改写到目标输出位点，以满足后续 `1399/1400` 的 throw / return ABI。


- 2026-06-17 13:24 关于 `1306` 次返回值 `X1` 与 `293.X8` 的关系，本轮已拿到更直接的 callsite 证据：
  - 在 `compileAdapter` 路径
    `0x275165d04..0x275165d3c` 中，可直接看到：
    - `BL 1306`
    - `MOV X25, X0`
    - `MOV X8, X1`
    - `BL 293`
    - `MOV X21, X25`
    - `BL 1399`
    这里 `1306` 的 secondary return `X1` 被原样转发到 `293` 的 `X8`。
  - 在 `requestStream` 路径
    `0x2751689e0..0x2751689f4` 中，同样是：
    - `BL 1306`
    - `MOV X27, X0`
    - `MOV X8, X1`
    - `BL 293`
    - `MOV X21, X27`
    - `BL 1399`
  - 这说明当前不需要再把 `X8` 只描述成“可能的 side-band”：
    至少在最关键的两条 typed-error throw-path 上，`293.X8` 就是 `1306.X1` 的直接转发。
  - 因而当前最具体、最干净的 machine-local 结论是：
    - `1306` 产出一对值 `(X0, X1)`；
    - `X0` 是主 error/result 值，后续会被保存到 `X25/X27` 一类寄存器；
    - `X1` 是 companion 输出位点/slot handle，并被直接送进 `293` 的 `X8`；
    - `293` 使用 `(X0, X8)` 做 in-place rebox / slot-fixup；
    - `1399` 再基于主值 `X0` 的保存副本完成最终 throw ABI 收尾。


- 2026-06-17 13:32 关于 `293` vs `1399/1400` 的职责边界，本轮已足够清楚：
  - `1399` / `1400` 的 xref 面显著更宽：
    - `1399` 当前已有 100+ code xref
    - `1400` 也有 90+ code xref
    覆盖大量 decoder / wrapper / asset / request / stream 等普通错误出口。
  - 相比之下，`293` 的 xref 面明显更窄，主要集中在少数 typed-error 需要重封装的位置。
  - 结合前面已经钉住的两条关键路径：
    - `compileAdapter`: `1306 -> MOV X8, X1 -> 293 -> MOV X21, X25 -> 1399`
    - `requestStream`: `1306 -> MOV X8, X1 -> 293 -> MOV X21, X27 -> 1399`
  - 当前最合理的固定模板已经可以写成：
    1. `1306`
       生成/返回 typed error 对 `(X0, X1)`；
    2. `293`
       消耗 `X0` 与 `X8 := X1`，对目标输出槽做 in-place rebox / slot-fixup；
    3. `1399/1400`
       作为更普适的 throw / return ABI 收尾 helper，消费保存下来的主值副本并把控制流真正带出当前 async frame。
  - 因而当前不必再把 `1399` 与 `293` 混在一起讨论：
    - `293` 是窄的、typed-error 专用的中间修复层；
    - `1399/1400` 是宽的、最终出口层。


- 2026-06-17 13:40 关于 `ModelManagerServices` 命名补强的当前收获与边界：
  - 本轮继续尝试把 `InferenceError` 侧 consumer 对上更正式的 witness 语义。
  - 当前最有价值的新锚点是：
    - `0x25a645560` 不是独立逻辑，而是直接 `b 0x25a63f9d4` 的 thunk；
    - 它与 `0x25a645568` 这一组附近桥一起，说明 `0x25a63f9d4` 已经处在 framework 内部被专门包一层入口的 consumer 位点上。
  - 再结合 `0x25a63f9d4` 本体的行为（25-case enum -> 固定整数码），当前最稳的命名语义仍可保持为：
    - `InferenceError` 的 error-code consumer / `CustomNSError` 风格 consumer
  - `0x25a63e844` 则保持为：
    - `InferenceError` case-name / description 风格 consumer
  - `0x25a63f4d8` 保持为：
    - `ModelManagerError -> InferenceError` bridge / context rebox consumer
  - 当前没拿到的仍然只是“精确的 Swift 原始符号名或 protocol witness 名”；
    但对主线而言，这已经不再构成阻塞，因为三者的职责分工已被 machine-local 行为和调用关系钉住。


- 2026-06-17 13:46 已新增短总结文档：
  - `docs/token_generation_inference_error_summary.md`
  - 该文档把当前这条支线的最终结论压成一页：
    - `TokenGenerationError.toInferenceError`
    - `ModelManagerServices` 3 条 `InferenceError` consumer
    - `convertToInferenceError`
    - `1306 -> 293 -> 1399/1400`
    - `293` vs `1399/1400` 的职责边界
  - 后续若只是恢复这条支线，不必再先翻 `ane_state.md` 的大段历史，可优先看这份摘要。


- 2026-06-17 14:06 已把这条支线的关键地址持久化到 IDA：
  - `ModelManagerServices`
    - 书签：`0x25a63e844` / `0x25a63f9d4` / `0x25a63f4d8`
    - 注释：`0x25a63f9d4` / `0x25a63f4d8` 已加函数注释；`0x25a63e844` 因当前 IDA 未认函数，改为入口地址行注释
  - `TokenGenerationInference`
    - 书签：`0x2750d0990` / `0x275165d04` / `0x2751689e0` / `0x2751442a4`
    - 注释：`convertToInferenceError` 与 3 个代表性 callsite 已写入摘要注释
  - 后续即使不先看 markdown，只进 IDA 也能快速恢复这条支线的语义。


- 2026-06-17 14:12 已把 `TokenGeneration.framework` 本体关键点也持久化到 IDA：
  - 书签：
    - `0x274de6890` `TokenGenerationError.toInferenceError`
    - `0x274de774c` ABI tail `destructiveInjectEnumTag`
    - `0x274de71b4` case 3 `tooManyTokens`
    - `0x274de6ec0` case 15 safety payload
    - `0x274de7454` case 12 `DocumentResource`
    - `0x274de75c0` case 6 `Prompt.SpecialToken`
    - `0x274de7020` case 11 name payload
  - 注释：
    - `toInferenceError` 函数注释已写入 5 个终态 group -> `InferenceError` 映射
    - `0x274de774c` 已标成 ABI-level `destructiveInjectEnumTag`
    - 几个关键 case 分支也已写入更正说明
  - 这意味着现在 3 个 framework
    (`TokenGeneration` / `ModelManagerServices` / `TokenGenerationInference`)
    都已经有对应的 IDA 持久化锚点。

---

## 2026-06-19: ProgramChainingPrepare（selector 9）用户态路径已被完全封死

### 已确认事实

- **`_ANEServicesProgramChainingPrepare`** @ `aneservices_arm64e:0x19e6a63cc` 是一个纯 C 输入验证包装器，校验所有入参后填充 `0xAE28` 字节的结构体，调下一步。
- **`ANE::ANEServicesDevice::ANE_ProgramChainingPrepare`** @ `aneservices_arm64e:0x19e69d668` 直接调用 `IOConnectCallStructMethod(conn, selector=9, {args_ptr, size=0xAE30}, 16, output, 24)`。无额外驱动级封装。
- `ANEServices.ANE::ANEServicesDevice` 中**不存在**以下符号：
  - `ANEDriver::ANE_ProgramChainingPrepare`
  - `ANEClientDevice::programChainingPrepare`
  - `ANEHWDevice::ANE_ProgramChainingPrepare`
  - 任何 `_gated` 变体
- `ANEHWDevice` 有大量方法（PowerOn/PowerOff/GetVersion/SendCommand/LoadFirmware 等），但不包含 ProgramChainingPrepare。
- **`aned` daemon 不参与 selector 9 IOConnect 路径**：`aned_arm64e` GOT 中零个 IOConnect 符号；aned 职责范围仅限于 XPC 编译/load 管理和 IOKit 事件通知订阅（通过 `_ANEDeviceController` 间接），无直接 kernel IOConnect。
- 实际 driver-facing decisive gate = `IOConnectCallStructMethod(conn, selector=9, ...)` → ANE kernel kext。

### 输入/输出结构体

- 输入：16 字节描述符 `{args_ptr, size=0xAE30}`，实际 payload 44584 字节位于 heap
- 输出：24 字节 `ANEProgramChainingPrepareOutput`
- IOKit 连接端口来自 `ANEServicesDevice+0x40`

### 返回值/错误路径

- 入口2 返回裸 IOReturn（连接不存在时返回 `0xE00002CD`）
- 入口1 用 `ANE::IOReturnToANEReturn` 将 IOReturn → ANE 错误码
- 成功时写回：`pANEProgramInstancePriv+90360` 的 cache handle + 24 字节 output struct

### 本轮 blocker 定位

用户态 ANEServices 层的 selector 9 ProgramChainingPrepare 路径已被完全封死——**无额外决定性 gate、无 return-code 再映射、无字段再写回**。若需理解或控制 selector 9 的行为，下一步必须进入 kernel kext（`AppleNeuralEngine.kext` / `AppleMobileFileIntegrity.kext`）。

### 2026-06-19 fresh selector-9 bootkc gate window

- 新证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_selector9_bridge_probe.csv`
  - `mps/ANE/.ane_runs/csv/ane_bootkc_chaining_prepare_args_bridge_probe.csv`
  - `mps/ANE/.ane_runs/csv/ane_bootkc_chaining_prepare_payload_use_scan.csv`
  - `mps/ANE/.ane_runs/json/selector9_bootkc_gate_window_verdict_20260619.json`
- 当前机器确认：
  1. selector-9 shim
     会先校验 outer input size = `0xae30`，
     再 tail-branch 到
     `ANEClientDevice::programChainingPrepare`
  2. `ANEClientDevice::programChainingPrepare`
     在 mapped payload 上新增可见写：
     - `+0x30 <- self`
     - `+0x3948` shared-event object rebuild
  3. `ANEHWDevice::ANE_ProgramChainingPrepare_gated`
     的 early validation
     明确读取并校验：
     - `0x38`
     - `0x3950`
     - `0xa614`
     - `0x3040`
  4. 进入 post-validation 后，
     又继续消费：
     - `0x30`
     - `0x10`
     - `0xae28`
     - `0xae18`
     - `0xae20`
- 因而当前最佳表述应继续收紧为：
  现阶段最强的 lower-control 窗口
  已不再是“谁拥有 delegated 真身”，
  而是
  `ANEHWDevice::ANE_ProgramChainingPrepare_gated`
  中哪些 selector-9 字段
  只是 size/count guard，
  哪些字段才真正参与
  accepted-state / materialization。

### 2026-06-19 selector-9 field-family partition

- 新证据：
  - `mps/ANE/.ane_runs/json/selector9_field_family_partition_verdict_20260619.json`
- 当前机器确认：
  1. `0x38 / 0x3950 / 0xa614 / 0x3040`
     全都位于
     `ANEHWDevice::ANE_ProgramChainingPrepare_gated`
     的 early validation
     读+比较链中，
     当前更像 guard-cluster
  2. `0x30`
     先在
     `ANEClientDevice::programChainingPrepare`
     被补写成 `self`，
     再在 post-validation
     被
     `ANE_PowerOn_gated`
     与
     `findClient`
     路线消费
  3. `0xae18 / 0xae20 / 0xae28`
     只在 post-validation
     的 helper / output-seeding
     路径出现，
     当前更像 materialization-cluster 候选
  4. `0x3944 / 0x3948`
     围绕 shared-event object rebuild
     与 later output seed
     出现，
     暂也归入 materialization-cluster 候选
- 因而当前最佳表述应再更新为：
  selector-9 的剩余 lower-control 搜索
  现在应一次只追一簇字段，
  而不是继续把整块 payload
  混在一起；
  当前优先字段族应收紧成：
  `0x30`
  vs
  `0xae18 / 0xae20 / 0xae28`

### 2026-06-19 selector-9 materialization-cluster priority

- 新证据：
  - `mps/ANE/.ane_runs/json/selector9_materialization_priority_verdict_20260619.json`
- 当前机器确认：
  1. `0x30`
     在 early validation 之后
     直接进入
     `ANE_PowerOn_gated`
     与
     `findClient`
     路线，
     当前是最高信号候选
  2. `0xae18 / 0xae20`
     直接喂给
     deeper helper
     与
     `AllocateSharedMemorySurface`
  3. `0xae28`
     会和 deeper resource-owned qword
     比较，并可能被清零，
     仍比纯 count 字段更像状态候选
  4. `0x3040 / 0x3950`
     虽然进入 post-validation，
     但当前更像
     alloc_count / shape
     字段
- 因而当前最佳表述应再更新为：
  selector-9 materialization-cluster
  的优先级已进一步收紧成：
  1. `0x30`
  2. `0xae18 / 0xae20 / 0xae28`
  而不是把
  `0x3040 / 0x3950`
  继续当成第一优先 accepted-state 候选

### 2026-06-19 selector-9 field `0x30` role

- 新证据：
  - `mps/ANE/.ane_runs/json/selector9_0x30_role_verdict_20260619.json`
- 当前机器确认：
  1. `0x30`
     不是 user-space wrapper
     直接写出的字段，
     而是在
     `ANEClientDevice::programChainingPrepare`
     中被补写成
     `self / ANEClientDevice*`
  2. 进入 bootkc 后，
     `0x30`
     在 output construction 之前
     就先被用于：
     - `ANE_PowerOn_gated`
     - `findClient`
  3. 它虽然也会 later output seed，
     但更早的消费路径
     明确先落在
     client/power/resource lookup
- 因而当前最佳表述应再更新为：
  `0x30`
  当前更像
  live client/power/resource lookup key，
  而不是 mere output helper；
  下一轮不必再纠缠 `0x30`，
  应正式切到
  `0xae18 / 0xae20 / 0xae28`

### 2026-06-19 selector-9 `0xae18 / 0xae20 / 0xae28` family role

- 新证据：
  - `mps/ANE/.ane_runs/json/selector9_ae_family_role_verdict_20260619.json`
- 当前机器确认：
  1. `0xae18 / 0xae20`
     会一起进入
     deeper helper
     与
     `AllocateSharedMemorySurface`
     路线，
     当前更像真正的
     resource/materialization 候选
  2. `0xae28`
     会被比较、
     可能被清零，
     也会 later output seed，
     当前更像 mixed state/tail-slot 字段
- 因而当前最佳表述应再更新为：
  `0xae18 / 0xae20`
  是 selector-9
  下一轮最高优先的
  materialization 候选，
  而 `0xae28`
  暂时降为后一位

### 2026-06-19 selector-9 `0xae18 / 0xae20` role

- 新证据：
  - `mps/ANE/.ane_runs/json/selector9_ae1820_role_verdict_20260619.json`
- 当前机器确认：
  1. `0xae18 / 0xae20`
     在 ANEServices
     中直接来自
     `program+0xa0 / +0xa8`
  2. 进入 bootkc 后，
     这对子字段会一起进入
     deeper helper
  3. 紧接着又一起种进
     `AllocateSharedMemorySurface`
     路线
  4. 当前没看到它们像 `0xae28`
     那样参与 compare-and-clear tail-slot 逻辑
- 因而当前最佳表述应再更新为：
  `0xae18 / 0xae20`
  当前最像 paired
  resource/materialization input family；
  下一轮应直接问：
  它们在 deeper helper /
  `AllocateSharedMemorySurface`
  里到底代表什么

### 2026-06-19 selector-9 `0xae18 / 0xae20` semantics

- 新证据：
  - `mps/ANE/.ane_runs/json/selector9_ae1820_semantics_verdict_20260619.json`
- 当前机器确认：
  1. `0xae18 / 0xae20`
     先来自
     `program+0xa0 / +0xa8`
  2. 进入 bootkc 后，
     它们会一起进入
     deeper helper
     与
     `AllocateSharedMemorySurface`
  3. 当前没看到它们退化成
     mere late output-bookkeeping 参数
- 因而当前最佳表述应再更新为：
  `0xae18 / 0xae20`
  已可视为 paired
  lower resource/materialization inputs；
  下一轮唯一问题
  应收紧成：
  `program+0xa0 / +0xa8`
  到底承载什么具体资源语义

### 2026-06-19 `program+0xa0 / +0xa8` resource-semantics boundary

- 新证据：
  - `mps/ANE/.ane_runs/json/program_a0_a8_resource_semantics_boundary_20260619.json`
- 当前机器确认：
  1. `program+0xa0 / +0xa8`
     经 `0xae18 / 0xae20`
     进入 deeper helper /
     `AllocateSharedMemorySurface`
     这一层已足以确认
     它们是 paired
     resource/materialization inputs
  2. 当前仍未唯一确认的只剩：
     它们具体是
     handle+size
     pointer+size
     surface+priority
     还是别的 paired resource tuple
- 因而当前最佳表述应再更新为：
  角色类别已定，
  剩余问题只剩 tuple 语义本身

### 2026-06-19 `program+0xa0 / +0xa8` tuple-semantics boundary

- 新证据：
  - `mps/ANE/.ane_runs/json/program_a0_a8_tuple_semantics_boundary_20260619.json`
- 当前机器确认：
  1. `program+0xa0 / +0xa8`
     是 stable carried inputs，
     不是 bridge mutation slot
  2. 它们会成对进入
     deeper helper
     与
     `AllocateSharedMemorySurface`
  3. 当前仍不能唯一分辨
     它们到底是
     handle+size
     pointer+size
     还是别的 paired resource tuple
- 因而当前最佳表述应再更新为：
  当前剩余问题
  已只剩
  `AllocateSharedMemorySurface`
  的接口语义

### 2026-06-19 `AllocateSharedMemorySurface` overload boundary

- 新证据：
  - `mps/ANE/.ane_runs/json/allocatesharedmemorysurface_overload_boundary_20260619.json`
- 当前机器确认：
  1. selector-9 当前命中的
     `AllocateSharedMemorySurface`
     是更具体的 overload：
     `ANEHWDevice::AllocateSharedMemorySurface(unsigned long long, ANESharedMemorySurfaceParams **, bool, unsigned int, bool, bool, unsigned int, bool, unsigned long long)`
  2. 因而当前剩余问题
     已从“paired resource tuple”
     再缩到：
     `0xae18 / 0xae20`
     如何映射到这个 overload
     的前导 `u64` / scalar 参数位
- 因而当前最佳表述应再更新为：
  下一轮唯一问题
  已收紧成
  `0xfffffe00092cb92c`
  调点前的寄存器/栈参数映射

### 2026-06-19 `AllocateSharedMemorySurface` callsite mapping boundary

- 新证据：
  - `mps/ANE/.ane_runs/json/allocatesharedmemorysurface_callsite_mapping_boundary_20260619.json`
- 当前机器确认：
  1. `0xae18`
     在 callsite 前
     进入 `x7`
  2. `0xae20`
     在 callsite 前
     进入 `w8`
  3. 这足以确认
     它们属于
     `AllocateSharedMemorySurface`
     overload 的 late argument material
  4. 但当前仍不足以恢复
     完整寄存器/栈位映射
- 因而当前最佳表述应再更新为：
  剩余问题已不是高层语义，
  而是
  `0xfffffe00092cb92c`
  调点前的完整寄存器/栈参数重建

### 2026-06-19 `AllocateSharedMemorySurface` pre-call reconstruction boundary

- 新证据：
  - `mps/ANE/.ane_runs/json/allocatesharedmemorysurface_precall_reconstruction_boundary_20260619.json`
- 当前机器确认：
  1. overload 已固定
  2. `0xae18 -> x7`
     `0xae20 -> w8`
     已固定
  3. 当前还没解决的只剩：
     `0xfffffe00092cb92c`
     调点前的完整寄存器/栈参数重建
- 因而当前最佳表述应再更新为：
  下一轮唯一问题
  已收紧成
  pre-call register/stack reconstruction probe

### 2026-06-19 `0xae18 / 0xae20` callsite late-argument boundary

- 新证据：
  - `mps/ANE/.ane_runs/json/allocatesharedmemorysurface_callsite_mapping_boundary_20260619.json`
  - `mps/ANE/.ane_runs/json/allocatesharedmemorysurface_precall_reconstruction_boundary_20260619.json`
- 当前机器确认：
  1. `0xae18 -> x7`
  2. `0xae20 -> w8`
  3. 它们已经足够收敛成
     late argument material
  4. 但还不足以恢复完整调用位图
- 因而当前最佳表述应再更新为：
  下一轮不再追高层语义，
  而是只做
  focused pre-call register/stack reconstruction

### 2026-06-19 `AllocateSharedMemorySurface` focused pre-call tuple boundary

- 新证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_allocatesharedmemorysurface_precall_probe.csv`
  - `mps/ANE/.ane_runs/json/allocatesharedmemorysurface_precall_probe_verdict_20260619.json`
- 当前机器确认：
  1. `0xfffffe00092cb92c`
     调点前
     `x2 = x29 - 0x78`
     即 caller-local
     `surface params`
     栈对象，
     不是
     `prepare_args+0xae18`
  2. `x7 <- prepare_args+0xae18`
     `sp+0x4 <- prepare_args+0xae20`
     仍成立，
     但它们属于
     late mixed register/stack tuple
  3. `sp+0x0`
     `sp+0x8`
     `sp+0x10`
     都在 call 前被清零，
     说明 stack-passed trailing args
     至少部分由当前 caller
     直接构造
  4. `x3=1`
     `x4=0x494e544d`
     `x5=1`
     `x6=0`
     也都在 caller 本地物化，
     不来自
     `prepare_args+0xae18/+0xae20`
- 因而当前最佳表述应再更新为：
  本轮已排除
  最简单的
  `pointer + size`
  读取，
  因为
  前导
  `ANESharedMemorySurfaceParams **`
  位置由
  caller-local stack object
  通过 `x2`
  提供；
  `0xae18 / 0xae20`
  更像
  lower materialization / control tuple
  的 trailing late arguments

### 2026-06-19 `AllocateSharedMemorySurface` trailing ABI slot boundary

- 新证据：
  - `mps/ANE/.ane_runs/json/arm64_member_call_abi_probe_verdict_20260619.json`
- 当前机器确认：
  1. 对 AArch64 C++ 成员函数，
     `this`
     占 `x0`
  2. 因而该 overload 的
     前 6 个 user-visible formal
     落
     `x1..x6`
  3. 第 7 个 user-visible formal
     落 `x7`
  4. 第 8/9/10/11 个
     user-visible formal
     依次落
     caller stack 的
     `sp+0`
     `sp+4`
     `sp+8`
     `sp+16`
  5. 代回
     `0xfffffe00092cb92c`
     调点后，
     `x7 <- prepare_args+0xae18`
     对应 overload 的
     第 7 个 user-visible formal
     `unsigned long long`
  6. `sp+0x4 <- prepare_args+0xae20`
     对应 overload 的
     第 9 个 user-visible formal
     `int`
- 因而当前最佳表述应再更新为：
  `0xae18 / 0xae20`
  已不只是
  late argument material，
  而是更精确的
  trailing
  `u64 / int`
  materialization-control tuple
  候选

### 2026-06-19 `AllocateSharedMemorySurface` early callee-use boundary

- 新证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_allocatesharedmemorysurface_early_use_probe.csv`
  - `mps/ANE/.ane_runs/json/allocatesharedmemorysurface_early_use_verdict_20260619.json`
- 当前机器确认：
  1. trailing `u64`
     formal
     一进 callee
     就被
     `mov x24, x7`
     捕获
  2. trailing `int`
     formal
     一进 callee
     就被
     `ldr w26, [x29, #0x14]`
     reload
  3. 该 `int`
     的最早用途不是
     arithmetic size/count，
     而是
     `cmp w26, #0`
     然后
     `cset w6, eq`
     压成布尔控制位
  4. 该 `u64`
     的最早下游用途是
     `mov x3, x24`
     然后直接送入
     `ANEHWDevice::createANESurface`
  5. 因而这对 tuple
     当前更像：
     - `u64` = identity-bearing
       surface/resource token
     - `int` = control/class/state selector
       或 mode family
- 因而当前最佳表述应再更新为：
  当前已经不该再把这对字段
  描述成
  `handle + size`
  候选；
  更好的边界是：
  `identity-bearing u64`
  +
  `control-like int`
  的 materialization tuple

### 2026-06-19 `createANESurface` early-use boundary

- 新证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_createanesurface_early_use_probe.csv`
  - `mps/ANE/.ane_runs/json/createanesurface_early_use_verdict_20260619.json`
- 当前机器确认：
  1. 从 selector-9
     带下来的 trailing `u64`
     进入
     `createANESurface`
     后立即被
     `mov x20, x3`
     捕获
  2. 从 selector-9
     带下来的 trailing `int`
     在进入
     `createANESurface`
     前已被压成 `w6`，
     入函数后
     与另一控制标量一起
     `stp w6, w4, [sp, #0x38]`
  3. 当前最早可见用法里，
     该 `u64`
     不是先去做
     lookup / compare / registry check，
     而是先被
     `OSNumber::withNumber`
     装箱
  4. 同一早期 property-construction path
     明确出现
     `IOSurfaceWidth`
     `IOSurfaceHeight`
     等 key，
     说明当前更像
     IOSurface property dictionary
     的构造路径
  5. 因而到当前证据为止，
     这个 `u64`
     更像
     opaque surface/resource identity token
     经 property path
     继续下发，
     而不是
     lookupProgramResource-style
     registry handle
- 因而当前最佳表述应再更新为：
  这对 tuple
  当前最强边界是：
  - `u64` = opaque surface/resource token
    on property path
  - `int` = class/mode selector
  但还没拿到
  “它永远不进入 registry/lookup”
  的最终证据

### 2026-06-19 `createANESurface` boxed-token follow-through boundary

- 新证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_createanesurface_token_followthrough_probe.csv`
  - `mps/ANE/.ane_runs/json/createanesurface_token_followthrough_verdict_20260619.json`
- 当前机器确认：
  1. selector-9
     带下来的 `u64`
     在
     `createANESurface`
     内先被
     `OSNumber::withNumber`
     装箱，
     然后保存在 `x22`
  2. 该 boxed token
     只有在
     原始 `x20 != 0`
     时才被插入
     property dictionary
  3. 在当前函数可见范围内，
     该 boxed token
     的下一大 consumer
     直接就是
     `IOSurfaceRoot::createSurface(task, OSDictionary)`
  4. 到这个 handoff 为止，
     当前没有看到
     `lookupProgramResource`
     / `getObject`
     / registry compare
     这类 consumer
  5. `createSurface`
     返回后
     `x20`
     被新建的
     IOSurface object
     覆盖，
     说明旧的 token path
     在当前可见层
     就止于 dictionary handoff
- 因而当前最佳表述应再更新为：
  到
  `IOSurfaceRoot::createSurface`
  之前，
  selector-9
  带下来的 `u64`
  仍应被视为
  opaque property token，
  而不是
  visible registry handle

### 2026-06-19 boxed token property-key boundary

- 新证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_createanesurface_token_followthrough_probe.csv`
  - `mps/ANE/.ane_runs/json/createanesurface_token_followthrough_verdict_20260619.json`
- 当前机器确认：
  1. boxed token
     在
     `createANESurface`
     中对应的 property key
     不是泛化未知项，
     而是
     `IOSurfaceAllocateFromSuperbuffer`
  2. 该 key
     只有在
     原始 `x20 != 0`
     时才插入
     OSDictionary
  3. post-create
     `IOSurface::setValue`
     写的是
     `IOSurfaceName`
     而不是 boxed token
     对应的 key
  4. 到函数尾声为止，
     boxed token (`x22`)
     只走
     OSDictionary
     → `IOSurfaceRoot::createSurface`
     这一路，
     后面只剩 release，
     没有第二个 visible consumer
- 因而当前最佳表述应再更新为：
  selector-9
  带下来的这个 `u64`
  当前最强可见语义
  不是 registry handle，
  而是
  `IOSurfaceAllocateFromSuperbuffer`
  这个 property key
  上的 opaque token / option value

### 2026-06-19 `IOSurfaceAllocateFromSuperbuffer` visibility boundary

- 新证据：
  - `mps/ANE/.ane_runs/json/iosurface_allocatefromsuperbuffer_visibility_boundary_20260619.json`
- 当前机器确认：
  1. `IOSurfaceAllocateFromSuperbuffer`
     是 selector-9
     带下来的 `u64`
     在当前可见层
     能被钉到的最后一个
     具体 property key
  2. 该 key
     的 visible consumer path
     只到
     `OSDictionary`
     → `IOSurfaceRoot::createSurface`
  3. post-create
     `IOSurface::setValue`
     写的是
     `IOSurfaceName`
     而不是这个 key
  4. 当前仓库与当前机器
     可见证据里，
     没有第二个公开 consumer
     把它再提升成
     更明确的 ANE-side handle /
     registry carrier
- 因而当前最佳表述应再更新为：
  剩余 lower-control 语义
  当前更可能已经下压到
  visible property construction
  之下，
  而不是还存在一个
  尚未识别的
  上层 ANE-side consumer

### 2026-06-19 visible property construction blocker package

- 新证据：
  - `mps/ANE/experiments/results/visible_property_construction_blocker_note.md`
- 当前机器确认：
  1. selector-9
     派生 `u64`
     的最后一个
     具体 visible carrier
     已固定为
     `IOSurfaceAllocateFromSuperbuffer`
  2. 其 visible consumer path
     已固定为
     `OSDictionary`
     → `IOSurfaceRoot::createSurface`
  3. post-create
     `IOSurfaceName`
     写入
     不再消费该 token
  4. 当前继续深挖
     同一 visible property layer
     的边际收益
     已显著下降
- 因而当前最佳表述应再更新为：
  这层 visible property construction
  已可作为
  当前 loop 的正式 blocker boundary；
  下一步要么下压到
  kernel / IOSurface-side 解释层，
  要么基于该 blocker package
  正式判死当前层

### 2026-06-19 `IOSurfaceAllocateFromSuperbuffer` visible-xref closure

- 新证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_iosurface_allocatefromsuperbuffer_xref_probe.csv`
  - `mps/ANE/.ane_runs/json/iosurface_allocatefromsuperbuffer_xref_verdict_20260619.json`
- 当前机器确认：
  1. 当前 visible H16 text
     只暴露出
     1 个
     `IOSurfaceAllocateFromSuperbuffer`
     materialization site
  2. 该唯一 site
     就在
     `ANEHWDevice::createANESurface+0x1e4`
  3. 当前没有第二个
     public visible consumer
     能把这个 key
     再带去别的上层 ANE-side 路径
- 因而当前最佳表述应再更新为：
  当前可见 property construction
  这一层
  在本机上已经不仅是
  “低收益”，
  而是可以
  正式视为
  已收口 / 已判死

### 2026-06-19 visible property construction formal closeout

- 新证据：
  - `mps/ANE/experiments/results/visible_property_construction_formal_blocker_package.md`
- 当前机器确认：
  1. 当前 visible ANE-side
     property-construction layer
     已不再是
     恢复 missing lower control
     的高价值下钻面
  2. `IOSurfaceAllocateFromSuperbuffer`
     已是 selector-9
     派生 `u64`
     的最后一个
     具体 visible carrier
  3. 该层的最后反证入口
     也已关闭
- 因而当前最佳表述应再更新为：
  这一层
  已可正式判死；
  若继续推进，
  应转到更低的
  kernel / IOSurface-side
  解释层，
  而不是回到
  同一 visible property layer

### 2026-06-19 lower-layer entry readiness

- 新证据：
  - `mps/ANE/experiments/results/lower_layer_entry_package.md`
- 当前机器确认：
  1. 当前最优先的
     更低层入口
     不是再加同层 probe，
     而是尝试
     `idb_open(kernelcache)`
     看 IDA
     能否直接吃当前 bootkc / fileset
  2. 若这条路不通，
     次优先分叉才是：
     - Python 解压 IM4P / 提取 fileset
     - 或 KDK
  3. `IOSurface.kext`
     / `BootKernelExtensions.kc`
     也是可直接使用的
     备选 lower-layer 入口
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  唯一最小入口
  就是
  `idb_open(kernelcache)`；
  失败再记录卡点并切备选

### 2026-06-19 kernelcache entry feasibility boundary

- 新证据：
  - `ida` 子代理对
    `idb_open(kernelcache)`
    的最小可行性探针
- 当前机器确认：
  1. 当前最合适的
     裸 Mach-O 目标
     是
     `/System/Library/Kernels/kernel.release.t8132`
  2. 当前失败
     不是 kernelcache 格式，
     而是
     宿主 `IDA Pro`
     未安装
  3. `KDK`
     当前也未安装，
     但这不是进入下一层
     的先决条件，
     因为裸 Mach-O
     已可直接用
  4. 当前可行的
     备选 lower-layer 入口
     是：
     - 安装 IDA Pro 后
       直接打开
       `kernel.release.t8132`
     - 或不用 IDA，
       改走
       `lldb` /
       其他本机逆向面
- 因而当前最佳表述应再更新为：
  下一层入口
  已从“找什么文件”
  收紧成
  “缺少哪种宿主能力”：
  当前缺的是
  `IDA Pro`
  宿主，
  不是
  kernel Mach-O 工件

### 2026-06-19 kernelcache shell-entry boundary

- 新证据：
  - `mps/ANE/.ane_runs/json/kernelcache_shell_entry_boundary_20260619.json`
- 当前机器确认：
  1. 当前真正的
     lower-layer 目标
     确实是
     `Preboot/.../System/Library/Caches/com.apple.kernelcaches/kernelcache`
  2. 先前尝试的
     `/System/Library/Kernels/kernel.release.t8132`
     只是纯 XNU 内核，
     不是 ANE 驱动所在层
  3. 但对当前 shell-only
     工作流而言，
     这个 kernelcache
     只表现为
     generic `data`
  4. 因而当前问题
     已从“目标选错层”
     收紧成
     “缺哪种解码/分析能力”
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  不应再重复
  `file/strings/nm`
  这类 shell-only 探针；
  唯一问题是
  选择哪种
  decode-capable 入口

### 2026-06-19 kernelcache fileset-entry visibility

- 新证据：
  - `mps/ANE/.ane_runs/json/kernelcache_fileset_entry_visibility_verdict_20260619.json`
- 当前机器确认：
  1. 当前 `kmutil`
     已能直接枚举
     `Preboot` kernelcache
     的 fileset entries
  2. 其中最有价值的
     下一层入口
     已明确为：
     `com.apple.driver.AppleH16ANEInterface`
     `vmaddr=0xfffffe000743d780`
     `fileoff=4429696`
  3. `AppleT8132ANEHAL`
     与 `IOSurface`
     已明确为
     次级/并列备选入口
  4. `kmutil emit-macho`
     已能产出
     `/tmp/KMUtilProducts/BootKernelCollection.kc`
     作为 raw Mach-O 容器
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  唯一最小目标
  不再是“找文件”，
  而是：
  提取 / 暴露
  `AppleH16ANEInterface`
  这个 fileset entry
  的符号与段信息

### 2026-06-19 `AppleH16ANEInterface` entry metadata boundary

- 新证据：
  - `kmutil inspect --show-fileset-entries`
    对当前 `Preboot` kernelcache
    的直接枚举
- 当前机器确认：
  1. `AppleH16ANEInterface`
     entry 已可直接枚举，
     且当前 metadata
     足够稳定：
     - `vmaddr=0xfffffe000743d780`
     - `fileoff=4429696`
     - `__TEXT_EXEC.__text size=1101912`
     - `nsyms=9136`
     - `nextdefsym=2256`
  2. `AppleT8132ANEHAL`
     和 `IOSurface`
     也可并列枚举，
     但作为次级入口更合适
  3. `/tmp/KMUtilProducts/BootKernelCollection.kc`
     已可稳定生成，
     因而下一步不需要再验证
     “能不能拿到 raw 容器”
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  唯一更低层目标
  应明确写成：
  `AppleH16ANEInterface`
  entry 的提取 /
  符号与段暴露

### 2026-06-19 `AppleH16ANEInterface` symbol-surface boundary

- 新证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_appleh16_fileset_symbol_probe.csv`
  - `mps/ANE/.ane_runs/json/appleh16_fileset_symbol_visibility_verdict_20260619.json`
- 当前机器确认：
  1. 当前已经能直接暴露
     `AppleH16ANEInterface`
     的 export symbol surface
  2. 当前 entry
     `nsyms=9136`
     `nextdefsym=2256`
     已足够做
     下一轮最小相关性收敛
  3. 当前样本统计里，
     已经可见：
     - `externalMethod` 命中
     - `descriptor` 命中
     - `segment` 命中
     - `cache` 命中
     - `prepare` 命中
     - `eval` 命中
- 因而当前最佳表述应再更新为：
  下一轮不再需要
  “暴露符号面”；
  唯一问题应收紧成：
  在这些符号家族里
  选一个
  selector-9 /
  artifact-descriptor
  相关的最小 deeper reverse target

### 2026-06-19 first deeper-target selection

- 新证据：
  - `mps/ANE/.ane_runs/json/appleh16_first_deeper_target_selection_20260619.json`
- 当前机器确认：
  1. 当前最小且最高价值的
     deeper reverse target
     已收敛为：
     `_Z22ANE_ProgramSendRequest`
  2. 它当前比
     `descriptor` /
     `segment` /
     `prepare`
     等家族更优先，
     因为当前 blocker
     更直接卡在
     eval-side hidden state /
     `0x12` 污染
  3. 其余家族
     仍重要，
     但在当前轮次
     已降为次级入口
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  唯一更低层目标
  就是
  `ANE_ProgramSendRequest`
  的 immediate call neighborhood
  与 first stateful callee

### 2026-06-19 `ANE_ProgramSendRequest` neighborhood boundary

- 新证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_program_send_request_neighborhood_probe.csv`
  - `mps/ANE/.ane_runs/json/program_send_request_neighborhood_verdict_20260619.json`
- 当前机器确认：
  1. 当前真正的目标符号
     不是先前口头简称，
     而是
     `__ZN9ANEDriver22ANE_ProgramSendRequestEP21ANEProgramRequestArgsPyPvbP18ANEReqCallbackDataP4taskP15ANESharedEvents`
  2. 它的近邻符号
     明确落在
     `ProgramPrepare / ProgramUnprepare / MemoryMap / ProgramDestroy`
     这一簇，
     说明当前选点正确
  3. 该函数最早可见的
     关键 stateful 候选
     不是直接 `bl`，
     而是一次
     `blraa x9, x17`
     间接调用
  4. 这次间接调用之前
     已读取：
     - `[x26 + 0xd8]`
     - vtable `+0x1e8`
     - `x25` 传入的 request args
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  不应再问
  “打哪个符号”，
  而应直接下钻
  `ANE_ProgramSendRequest`
  中这次最早的
  vtable 间接调用

### 2026-06-19 `ANE_ProgramSendRequest` first-stateful-callee boundary

- 新证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_program_send_request_neighborhood_probe.csv`
  - `mps/ANE/.ane_runs/json/program_send_request_neighborhood_verdict_20260619.json`
- 当前机器确认：
  1. 当前完整目标符号是
     `ANEDriver::ANE_ProgramSendRequest(ANEProgramRequestArgs *, unsigned long long *, bool, ANEReqCallbackData *, task *, ANESharedEvents *)`
  2. 当前最早 gate
     来自
     `ANEProgramRequestArgs + 0x89`
     的模式字节，
     `< 2`
     直接走 fast path
  3. 当前最早状态对象入口
     来自
     `ANEProgramRequestArgs + 0xd8`
  4. 当前最早值得下钻的
     两跳间接调用
     是：
     - vtable `+0x1e8`
     - vtable `+0x8c0`
  5. 第一跳返回值
     还会写到
     `out_u64 + 0x938`
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  唯一更低层目标
  应收紧成：
  识别
  `vtable + 0x1e8`
  的真实 callee，
  并确认它是否是
  eval-side hidden state
  的 first stateful consumer

### 2026-06-19 `ProgramSendRequest` vtable-slot split boundary

- 新证据：
  - 当前机器直接读取
    `ANEDriver` /
    `ANEHWDevice` /
    `ANECoreInterface`
    的 vtable 槽位
- 当前机器确认：
  1. `vtable + 0x1e8`
     在三张表上
     当前完全相同
  2. `vtable + 0x8c0`
     在三张表上
     当前并不相同
  3. 因而 `+0x1e8`
     更像共享前处理 /
     接口层 helper
  4. `+0x8c0`
     更像类特异的
     stateful 提交路径
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  优先级应改成：
  先识别
  `vtable + 0x8c0`
  的真实 callee；
  若它不足以解释
  eval-side hidden state，
  再回头解释
  共享的
  `+0x1e8`

### 2026-06-19 exported `ProgramSendRequest` chain boundary

- 新证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_hw_program_send_request_chain_probe.csv`
  - `mps/ANE/.ane_runs/json/hw_program_send_request_chain_verdict_20260619.json`
- 当前机器确认：
  1. `ANEDriver::ANE_ProgramSendRequest`
     之下的第一层
     exported chain
     已明确为：
     - `ANEHWDevice::ANE_ProgramSendRequest`
     - `ANE_ProgramSendRequest_gated`
     - `ANE_ProgramSendRequestInitialChecksAndLookups_gated`
  2. 这条链
     比继续停在
     driver wrapper
     更接近
     真正的 stateful 路径
  3. 因而当前更低层入口
     已可再下推一层
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  默认目标
  不再是
  `ANEDriver::ANE_ProgramSendRequest`，
  而是
  `ANEHWDevice::ANE_ProgramSendRequest_gated`
  或
  `ANE_ProgramSendRequestInitialChecksAndLookups_gated`

### 2026-06-19 gated send-request compare boundary

- 新证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_hw_sendrequest_gated_compare_probe.csv`
  - `mps/ANE/.ane_runs/json/hw_sendrequest_gated_compare_verdict_20260619.json`
- 当前机器确认：
  1. `ANE_ProgramSendRequest_gated`
     在当前窗口内
     没有直接 `bl`
  2. `ANE_ProgramSendRequestInitialChecksAndLookups_gated`
     在很早位置
     已直接调用
     `ANE_HandlePowerStateChecksForClientEbb`
  3. 因而第二个函数
     更像当前最早的
     clearly stateful direct-callee 入口
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  唯一默认目标
  应再收紧成：
  `ANE_ProgramSendRequestInitialChecksAndLookups_gated`
  中的
  `ANE_HandlePowerStateChecksForClientEbb`

### 2026-06-19 `ANE_HandlePowerStateChecksForClientEbb` neighborhood boundary

- 新证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_handle_powerstate_checks_probe.csv`
  - `mps/ANE/.ane_runs/json/handle_powerstate_checks_verdict_20260619.json`
- 当前机器确认：
  1. 该函数当前窗口内
     没有直接 `bl`
  2. 但其导出邻域
     明确落在：
     - `findClientByOwningTask`
     - `findClientByCodesigning`
     - `lookupClientProgramWithHandle`
     - `ANE_Add/RemovePersistentClient_gated`
     这一簇
  3. 因而它当前更像
     client/program-aware gate，
     不像纯电源薄包装
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  不应先找它的 direct `bl`，
  而应先读它内部
  对 client/program/persistent-state
  相关字段的访问模式

### 2026-06-19 `HandlePowerStateChecks` field-pattern boundary

- 新证据：
  - `mps/ANE/.ane_runs/csv/ane_bootkc_handle_powerstate_field_probe.csv`
  - `mps/ANE/.ane_runs/json/handle_powerstate_field_verdict_20260619.json`
- 当前机器确认：
  1. 当前窗口内
     两个 direct `bl`
     分别是：
     - 未命名 helper
     - `ANEHWDevice::commandSleep`
  2. 这两条
     当前都不像
     最关键的 client/program-aware
     入口
  3. 更高价值的
     可疑点
     反而是字段簇：
     - `self + 0x718`
     - object `+0x111`
     - object `+0xa8`
     - object `+0xa9`
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  默认目标
  应先读
  `0x718 / 0x111 / 0xa8 / 0xa9`
  这组字段模式，
  而不是优先下钻
  `commandSleep`

### 2026-06-19 `HandlePowerStateChecks` object-edge boundary

- 当前机器确认：
  1. `0x111 / 0xa8 / 0xa9`
     当前都以
     `ldrb` + `tbz`
     形式出现，
     更像 byte-flag gates
  2. `self + 0x718`
     当前是
     先被 `ldr x24, [x24, #0x718]`
     取出的指针型入口
  3. 因而真正更值得
     下一轮继续读的
     不是三个 flag byte，
     而是
     `self + 0x718`
     指向的对象边
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  唯一目标应再收紧成：
  `self + 0x718`
  指向的对象

### 2026-06-19 `self + 0x718` direct-callee boundary

- 当前机器确认：
  1. `self + 0x718`
     被装到 `x24` 后，
     立即作为
     `x1`
     传给
     `0xfffffe000bed82e8`
  2. 与之相比，
     `commandSleep(self, self+0xa0, 2)`
     出现在其后，
     当前更像次级路径
  3. 因而真正更值得
     下一轮下钻的
     不是 `commandSleep`，
     也不只是
     `self+0x718` 抽象对象边，
     而是这个
     未命名 direct callee
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  默认目标
  应再收紧成：
  `0xfffffe000bed82e8`
  这次 direct callee

### 2026-06-19 `0xfffffe000bed82e8` wrapper boundary

- 当前机器确认：
  1. `0xfffffe000bed82e8`
     自身只有一个很薄的
     prologue / 参数重排
  2. 它会立刻
     `bl`
     到
     `0xfffffe000bed8348`
  3. 后者一进入
     就建立更大的栈帧，
     并读取
     per-CPU / 线程本地
     状态，
     明显比前者更重
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  不应停在
  `0xfffffe000bed82e8`，
  而应直接下钻
  `0xfffffe000bed8348`

### 2026-06-19 `0xfffffe000bed8348` stateful-window boundary

- 当前机器确认：
  1. `0xfffffe000bed8348`
     一进入就读
     per-CPU / 线程本地
     状态
  2. 它随后读取
     多个全局状态位，
     并明确出现：
     `cmp w9, #0x12`
  3. 这使它当前
     直接落在我们关心的
     `0x12` 污染
     语义窗口上
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  默认目标
  不再是
  “泛读 0xfffffe000bed8348”，
  而是：
  围绕
  `cmp w9, #0x12`
  及其后的
  全局/线程本地
  状态读写
  做最小 probe

### 2026-06-19 `0x12` gate state-source selection

- 新证据：
  - `mps/ANE/.ane_runs/json/gate_0x12_state_source_selection_20260619.json`
- 当前机器确认：
  1. 与 `cmp w9, #0x12`
     最直接相连的
     单一状态源
     是：
     `[0xfffffe0007e7b000 + 0xa58]`
  2. 它的比较结果
     立即进入
     `csinc -> w24`
     这一派生 gate
  3. 其余状态源
     虽然仍重要，
     但当前已降为
     次级入口
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  唯一目标
  应再收紧成：
  识别
  `[0xfffffe0007e7b000 + 0xa58]`
  这个全局源

### 2026-06-19 `0x12` gate source address-space boundary

- 新证据：
  - `mps/ANE/.ane_runs/json/gate_0x12_state_source_address_space_boundary_20260619.json`
- 当前机器确认：
  1. 当前 active reverse
     使用的是
     `Preboot` kernelcache
     → `/tmp/KMUtilProducts/BootKernelCollection.kc`
     的运行时地址空间
  2. 因而
     `[0xfffffe0007e7b000 + 0xa58]`
     必须在这个
     `BootKC` 地址空间中解释
  3. 子代理给出的
     `kernel.release.t8132::__CTF`
     归属
     属于另一套地址空间，
     不能拿来反转当前路径
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  应继续在
  `BootKernelCollection`
  地址空间里
  识别这个状态源，
  而不是切回
  standalone kernel

### 2026-06-19 `0x12` state-source table-form boundary

- 当前机器确认：
  1. `[0xfffffe0007e7b000 + 0xa58]`
     在
     `com.apple.kernel::__DATA_CONST,__const`
     中
     不像单一计数值，
     更像静态表项的一部分
  2. 其邻域包含多组
     成对/重复的
     只读常量值，
     形态更接近
     配置表 / 描述表
     而不是运行时可写状态
  3. 因而当前默认问题
     不应再表述为
     “这个全局值属于谁”，
     而应改成
     “这张表是什么类型”
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  唯一目标
  应收紧成：
  识别
  `+0xa58`
  所在静态表
  的类型

### 2026-06-19 `+0xa58` encoded-table boundary

- 当前机器确认：
  1. `+0xa58`
     周围 8-byte 表项
     不是朴素的
     运行时高地址指针数组
  2. 其值形态更像：
     - 一组局部表内引用
     - 一组统一编码前缀的
       标记化值
  3. 因而这更像
     标记化描述表 /
     配置表项，
     而不是普通对象指针表
- 因而当前最佳表述应再更新为：
  下一轮若继续推进，
  默认目标
  不应再是
  “解引用指针”，
  而应是：
  识别这张
  标记化描述表
  的编码规则或表类型

### 2026-06-19 `+0xa58` source-table encoding boundary

- 新证据：
  - `mps/ANE/experiments/ane_bootkc_gate_0x12_source_table_probe.py`
  - `mps/ANE/.ane_runs/csv/ane_bootkc_gate_0x12_source_table_probe.csv`
  - `mps/ANE/.ane_runs/json/gate_0x12_source_table_verdict_20260619.json`
- 当前机器确认：
  1. `+0xa58`
     自身槽位
     当前值是 `0`
     更像一张更大静态表
     中的一行/空位，
     不是独立 runtime scalar
  2. 其后相邻
     非零 8-byte 表项
     中，
     绝大多数都可拆成：
     - 非 bind / 非 auth
     - 带非零 `next_delta`
     - low32 target
       可直接映射到
       当前 `BootKernelCollection.kc`
       的有效文件范围
  3. 当前窗口里
     已稳定出现两族 target：
     - 本地
       `__DATA_CONST`
       邻域
       `0xe77ac8 / 0xe77ad0`
     - 当前
       `__DATA`
       邻域
       `0x55500a0 .. 0xac`
  4. 同一个 low32 target
     `0x55500a4`
     还出现了
     仅 `next_delta`
     从 `2`
     变成 `60`
     的变体，
     这更像
     BootKC
     rebase / fixup-style
     编码表项，
     不是 ANE 业务枚举值
- 因而当前最佳表述应再更新为：
  `+0xa58`
  邻域当前更像
  `BootKernelCollection`
  的 rebase / fixup-style
  编码指针表，
  而不是
  ANE-specific
  business descriptor table
- 因而下一轮若继续推进，
  默认目标
  不应再是
  “这里的 tag 是什么业务态”，
  而应是：
  解码这些 low32 target
  尤其是
  `0x55500a0 .. 0xac`
  这一族
  到底属于哪个
  具体对象/记录家族，
  再判断它是
  generic kernel bookkeeping
  还是 ANE-adjacent
  lower state carrier

### 2026-06-19 `0x55500a0 .. 0xac` low32-target family boundary

- 新证据：
  - `mps/ANE/experiments/ane_bootkc_gate_0x12_low32_target_family_probe.py`
  - `mps/ANE/.ane_runs/csv/ane_bootkc_gate_0x12_low32_target_family_probe.csv`
  - `mps/ANE/.ane_runs/json/gate_0x12_low32_target_family_verdict_20260619.json`
- 当前机器确认：
  1. `0x55500a0 .. 0xac`
     这组 low32 target
     直落
     当前根 Mach-O
     的 `__DATA`
     段，
     不是
     `AppleH16ANEInterface`
     的 `__TEXT_EXEC`
     或邻近 ANE 符号面
  2. 精确目标槽位
     解出来只是
     `u32`
     小标量：
     - `0x20`
     - `0x20`
     - `0x0`
     - `0xc8`
     不是指针、
     vtable link
     或对象引用
  3. 紧邻后续行
     很快转成
     高字节密集的
     packed data
     形态，
     更像通用 lookup / blob
     数据，
     不像状态对象头
  4. 紧前导行
     `0x1 / 0xffffffff / 0x5 / 0x29 / 0x6`
     更像一个小型数据头，
     仍不像
     ANE runtime object boundary
  5. 进一步核验后，
     `0xc8`
     这段表体
     实际只覆盖
     `25 × 8`
     字节，
     不是
     `41 × 8`
     字节
  6. 同类头部模式
     在当前根 Mach-O
     `__DATA`
     里
     只扫到
     `2`
     处，
     其中当前
     `0x5550080`
     这一处
     是唯一挂
     大 LUT
     的专用结构
- 因而当前最佳表述应再更新为：
  `0x55500a0 .. 0xac`
  这一族
  当前更像
  generic kernel data
  with local header，
  不是
  ANE-adjacent
  stateful object/record carrier
- 因而下一轮若继续推进，
  默认目标
  不应再追
  `0x55500a0 .. 0xac`
  这条弱语义支线，
  而应回到
  同一 source-table window
  中更靠近本地
  `__DATA_CONST`
  落点的
  `0xe77ac8 / 0xe77ad0`
  家族，
  判断那里是否更接近
  ANE-owned
  lower state
  或仍然只是
  generic kernel table glue

### 2026-06-19 BootKC-on-IDA direct-open blocker

- 新证据：
  - `ida-pro-mcp idb_open(input_path=/tmp/KMUtilProducts/BootKernelCollection.kc, mode=prefer_headless)`
- 当前机器确认：
  1. `ida-pro-mcp`
     当前不能直接打开
     `/tmp/KMUtilProducts/BootKernelCollection.kc`
  2. 当前报错是：
     `Failed to open database: /private/tmp/KMUtilProducts/BootKernelCollection.kc`
  3. 因而
     以
     `BootKC raw macho`
     直接做
     IDA xref/module check
     目前存在
     明确工具 blocker，
     不是
     证据已证伪
- 因而当前最佳表述应再更新为：
  `0x55500a0 .. 0xac`
  这块结构的
  code xref / module
  归属问题
  现在卡在
  “BootKC raw macho
  无法直接被
  ida-pro-mcp
  打开”
  这一层，
  不是
  当前结构边界
  已反转

### 2026-06-19 `0xe77ac8 / 0xe77ad0` local-target boundary

- 新证据：
  - `mps/ANE/experiments/ane_bootkc_gate_0x12_local_target_boundary_probe.py`
  - `mps/ANE/.ane_runs/csv/ane_bootkc_gate_0x12_local_target_boundary_probe.csv`
  - `mps/ANE/.ane_runs/json/gate_0x12_local_target_boundary_verdict_20260619.json`
- 当前机器确认：
  1. `0xe77ac8`
     和
     `0xe77ad0`
     这两个
     decoded local target
     本身都落在
     `u64 == 0`
     的零槽位上，
     不是 live pointer
     或 scalar body
  2. 从
     `0xe77ac8`
     到下一个
     可见结构头
     `0xe77b90`
     之间
     有
     `25`
     个连续零 qword，
     gap 总长
     `200` 字节
  3. 当前第一处
     明显的结构化记录
     只从
     `0xe77b90`
     才开始，
     其头部立即出现
     `0x8035db49`
     / `0xffffffff`
     / `0xc0e00001`
     这一簇
  4. 因而
     `0xe77ac8 / 0xe77ad0`
     当前更像
     local anchor /
     pre-record table glue，
     不是
     实际 state-carrying
     record body
- 因而当前最佳表述应再更新为：
  这组
  `__DATA_CONST`
  decoded target
  自身
  也不是
  ANE-owned object body；
  真正值得继续追的
  下一个单一入口
  应前移到
  `0xe77b90`
  的首个真实记录头
- 因而下一轮若继续推进，
  默认目标
  不应再追
  `0xe77ac8 / 0xe77ad0`
  自身，
  而应是：
  识别
  `0xe77b90`
  这一记录家族
  更像
  generic kernel metadata
  还是更靠近
  lower ANE control path

### 2026-06-19 `[x23+0x1c0]` live-gate boundary

- 新证据：
  - `mps/ANE/experiments/ane_bootkc_gate_0x12_threadlocal_source_probe.py`
  - `mps/ANE/.ane_runs/csv/ane_bootkc_gate_0x12_threadlocal_source_probe.csv`
  - `mps/ANE/.ane_runs/json/gate_0x12_threadlocal_source_verdict_20260619.json`
- 当前机器确认：
  1. 在
     `0xfffffe000bed8348`
     这个原始 helper window
     里，
     `[x23+0x1c0]`
     的第一处用法就是：
     `ldr w8, [x23, #0x1c0]`
     紧接
     `cbz w8, ...`
  2. 这说明
     `[x23+0x1c0]`
     当前直接参与
     live control flow gate，
     不是像
     `+0xa58`
     分支那样
     先掉进
     BootKC metadata
     解码
  3. 当前窗口里
     它比
     `+0xa58`
     source-table
     分支
     更接近
     helper 本体的
     即时判定逻辑
- 因而当前最佳表述应再更新为：
  在当前
  `0x12`
  gate
  候选源里，
  `[x23+0x1c0]`
  现在是
  比 BootKC source-table
  更强的下一入口
- 因而下一轮若继续推进，
  默认目标
  应收紧成：
  判断
  `[x23+0x1c0]`
  到底更像
  per-thread admission state、
  per-client mode，
  还是
  通向更广
  device state
  的桥接位

### 2026-06-19 `[x23+0x1c0]` threadlocal-role boundary

- 新证据：
  - `mps/ANE/experiments/ane_bootkc_gate_0x12_threadlocal_role_probe.py`
  - `mps/ANE/.ane_runs/csv/ane_bootkc_gate_0x12_threadlocal_role_probe.csv`
  - `mps/ANE/.ane_runs/json/gate_0x12_threadlocal_role_verdict_20260619.json`
- 当前机器确认：
  1. `x23`
     在 helper
     里
     是直接由
     `mrs x23, tpidr_el1`
     取到的
     thread/per-CPU
     base
  2. 紧接着
     helper
     先读
     `[x23+0x1b0]`
     再读
     `[x23+0x1c0]`
  3. `[x23+0x1c0]`
     的第一处用法
     就是
     `ldr`
     后立刻
     `cbz`
     参与 gate
  4. 在这之后，
     当前窗口里
     还能看到
     它继续参与
     `bic`
     / 条件分支
     关联逻辑
- 因而当前最佳表述应再更新为：
  `[x23+0x1c0]`
  当前比
  per-client heap field
  更像
  thread/per-CPU
  admission state
- 因而下一轮若继续推进，
  默认目标
  应收紧成：
  判断
  这个
  threadlocal admission
  位
  是否在 helper 家族中
  进一步并入
  更广的
  device/client state，
  还是始终保持
  纯 threadlocal
  准入语义

### 2026-06-19 BootKC `0x12` gate branch falsified

- 新证据：
  - `mps/ANE/.ane_runs/json/gate_0x12_threadlocal_role_verdict_20260619.json`
  - `mps/ANE/.ane_runs/json/gate_0x12_threadlocal_source_verdict_20260619.json`
  - `ida` 子代理对 `0xfffffe000bed8348` 的函数级定位
- 当前机器确认：
  1. `0xfffffe000bed8348`
     不是
     ANE 私有 helper，
     而是
     XNU 内核
     `os_log`
     基础设施变体
  2. `[x23+0x1c0]`
     与
     `[x23+0x1b0]`
     都是
     `tpidr_el1`
     派生的
     thread/per-CPU
     字段
  3. `+0xa58`
     分支及其
     `source-table`
     / `local target`
     / `record family`
     继续下钻后
     也都收敛到
     BootKC/kext metadata，
     没有回到
     ANE-owned control state
- 因而当前最佳表述应再更新为：
  `BootKC + 0x12 gate`
  这整条支线
  已被正式
  `falsified`
  为
  通用内核基础设施
  假目标，
  不应再作为
  private ANE
  lower control layer
  的默认入口

### 2026-06-19 current best ANE-side lower entry

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_serializer_static_probe.py`
  - `mps/ANE/experiments/results/newinstance_serializer_static_note.md`
  - `mps/ANE/experiments/results/newinstance_packaging_bridge_note.md`
  - `mps/ANE/experiments/results/artifact_descriptor_surface_probe.md`
- 当前机器确认：
  1. 当前最强的
     user-space
     lower authoring / lowering
     入口
     已固定在
     `-[_ANEVirtualClient loadModelNewInstanceLegacy:options:modelInstParams:qos:error:]`
  2. 该路径已明确把：
     - `instanceName`
     - `procedureArray.count`
     - `procedureSymbol`
     - `weightArray.count`
     等语义
     压进
     `ANEModelInstanceParametersSerializerDeserializer`
     /
     `ANEProcedureDataSerializerDeserializer`
  3. 这条链
     比当前
     BootKC
     假目标
     更接近
     真正的
     private ANE
     lower control layer
- 因而下一轮若继续推进，
  默认目标
  应切到：
  在
  `loadModelNewInstanceLegacy`
  周围继续找
  哪个 lower field /
  serializer output /
  daemon request slot
  才是真正阻塞
  single-process reuse
  的控制点

### 2026-06-19 current blocker ranking below `loadModelNewInstanceLegacy`

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_blocker_ranking_probe.py`
  - `mps/ANE/.ane_runs/json/newinstance_blocker_ranking_verdict_20260619.json`
  - `mps/ANE/.ane_runs/csv/ane_newinstance_daemon_gap_summary.csv`
  - `mps/ANE/.ane_runs/csv/ane_newinstance_packaging_bridge_summary.csv`
  - `mps/ANE/.ane_runs/csv/ane_inmemory_new_instance_probe_request_inline_sha_matrix.csv`
- 当前机器确认：
  1. `instanceName`
     在 daemon getter
     之下
     当前已被收紧到
     logging helper
     `%@:instanceName:%@`
     路径，
     没有 pinned 到
     可见 `0x35a10`
     request slot
  2. `weight_sha`
     这条语义
     则不同：
     - selector-8
       目标位
       `params +0x530/+0x540`
       已 reached
     - ANEServices
       的 repack
       source slot
       `request +0x528`
       已 pinned
     - 但 daemon 侧
       当前 visible
       `0x35a10`
       map
       里
       仍没有
       writer
  3. 直接 runtime
     author
     `request +0x528..+0x547`
     也只是改变了
     字节值，
     仍停在同一
     wrapper rejection
     bucket
- 因而当前最佳表述应再更新为：
  `instanceName`
  不再是当前
  最强 blocker 候选；
  当前最强
  lower control gap
  已收紧成：
  在
  ANEServices
  消费之前，
  谁先 author /
  join 了
  `request weight +0x528..+0x547`
  这个 family
- 因而下一轮若继续推进，
  默认目标
  应进一步收紧成：
  找到
  第一个 lower stage
  对
  `request +0x528..+0x547`
  的
  author / join
  点

### 2026-06-19 current `request +0x528` provenance boundary

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_request528_next_probe.py`
  - `mps/ANE/.ane_runs/json/newinstance_request528_next_verdict_20260619.json`
  - `mps/ANE/.ane_runs/csv/ane_newinstance_request528_provenance_summary.csv`
  - `mps/ANE/.ane_runs/csv/ane_newinstance_helper_sidecar_summary.csv`
  - `mps/ANE/.ane_runs/csv/ane_inmemory_new_instance_probe_request_inline_sha_matrix.csv`
- 当前机器确认：
  1. `ANEServices`
     当前不是
     `request +0x528`
     family
     的 author；
     它只是从
     原始 daemon request
     memory
     读取该区域
  2. visible daemon
     weight-loop
     helper
     neighborhood
     也是
     request-blind，
     不会直接写
     `+0x528..+0x547`
  3. 直接 runtime
     author
     `request +0x528..+0x547`
     字节
     也不会改变
     wrapper rejection
     bucket
- 因而当前最佳表述应再更新为：
  当前最强 provenance
  缺口
  已不再是
  visible ANEServices repack
  或 visible daemon helper；
  当前唯一高价值目标
  是：
  找到
  第一个 non-visible
  clone / repack /
  sidecar stage
  去 materialize
  原始 daemon request
  的
  `+0x528..+0x547`
  region
- 因而下一轮若继续推进，
  默认目标
  应继续收紧成：
  找到
  这个 first non-visible
  author/join stage

### 2026-06-19 current first non-visible `request+0x528` candidate

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_request528_stage_ranking_probe.py`
  - `mps/ANE/.ane_runs/json/newinstance_request528_stage_ranking_verdict_20260619.json`
  - `mps/ANE/experiments/results/bootkc_create_instance_hidden_handle_bridge_probe.md`
- 当前机器确认：
  1. visible helper-result
     branch
     已 ruled out
  2. `ANEServices`
     只是
     原始 daemon request
     memory
     的 reader，
     不是
     `+0x528`
     的 author
  3. 当前 machine-local
     最具体的
     non-visible
     sidecar family
     已经是：
     driver/device-authored
     hidden handle
     `-> x5`
     `-> additional_params+0x18`
     `-> lower gated body`
- 因而当前最佳表述应再更新为：
  当前最强的
  first non-visible
  candidate
  已不再是
  抽象的
  clone/repack stage，
  而是
  deeper driver-routed
  create-instance
  hidden-handle family
- 因而下一轮若继续推进，
  默认目标
  应进一步收紧成：
  判断
  这条 hidden-handle
  family
  是否与
  `request +0x528..+0x547`
  region
  发生 join/gate

### 2026-06-19 hidden-handle join proximity boundary

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_hidden_handle_join_probe.py`
  - `mps/ANE/.ane_runs/json/newinstance_hidden_handle_join_verdict_20260619.json`
- 当前机器确认：
  1. `ANEServices`
     读取的是
     原始 daemon request
     memory，
     不是
     local staging copy
  2. visible daemon helper
     neighborhood
     也是
     request-blind
  3. 当前 machine-local
     已明确存在的
     最邻近 lower join/gate
     surface
     就是
     hidden-handle family：
     `x5 -> additional_params+0x18 -> lower gated body`
- 因而当前最佳表述应再更新为：
  hidden-handle family
  当前还不是
  `request +0x528..+0x547`
  的已证实 author，
  但已经是
  离它最近、
  证据最硬的
  lower join/gate
  surface
- 因而下一轮若继续推进，
  默认目标
  应继续收紧成：
  判断
  hidden-handle path
  与
  `request +0x528..+0x547`
  是否在同一
  accepted create-instance
  lower stage
  汇合

### 2026-06-19 hidden-handle stage equality boundary

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_hidden_handle_stage_probe.py`
  - `mps/ANE/.ane_runs/json/newinstance_hidden_handle_stage_verdict_20260619.json`
- 当前机器确认：
  1. hidden-handle family
     已经是
     已证实的
     accepted-state join
     surface：
     `x5 -> additional_params+0x18 -> local_y -> lookupProgramResource -> params[0]/x21[0]`
  2. `request +0x528`
     当前仍只被钉到：
     原始 daemon request
     memory
     被
     `ANEServices`
     later reader
     消费
  3. 当前 machine-local
     证据
     还不能证明
     这两个 family
     已在同一 lower stage
     汇合
- 因而当前最佳表述应再更新为：
  hidden-handle family
  仍是
  最近的已证实
  join/gate
  surface，
  但还不是
  `request +0x528..+0x547`
  的同阶段直接证据
- 因而下一轮若继续推进，
  默认目标
  应进一步收紧成：
  找到
  第一个同时看到
  hidden-handle-derived
  accepted state
  和
  `request +0x528..+0x547`
  family
  的 lower surface，
  或正式证明
  中间还隔着
  一层 clone/repack

### 2026-06-19 current smallest unresolved gap

- 当前机器确认：
  1. hidden-handle family
     已经能被一路追到：
     `params[0]`
     和
     外部输出
     `x21[0]`
     的 writeback
  2. `request +0x528`
     family
     已经能被一路追到：
     原始 daemon request
     memory
     被
     `ANEServices`
     later reader
     消费
  3. 当前仍缺的
     不是更泛的
     候选列表，
     而是：
     哪个 lower surface
     同时接触
     这两条已知强证据链
- 因而当前最佳表述应再更新为：
  当前最小未解缺口
  已收紧成：
  找到第一个同时看到
  `params[0]/x21[0]`
  hidden-handle writeback
  和
  `request +0x528..+0x547`
  消费链
  的 lower surface

### 2026-06-19 closest known convergence surface

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_convergence_surface_probe.py`
  - `mps/ANE/.ane_runs/json/newinstance_convergence_surface_verdict_20260619.json`
- 当前机器确认：
  1. hidden-handle family
     已经在
     accepted create-instance
     gated body
     中 live
  2. selector-8
     per-weight params
     投影
     也已经在
     lower path
     中结构化可见
  3. 因而当前最靠近
     两条强证据链
     交汇的 surface
     已不再是
     visible daemon helper
     或
     visible ANEServices repack
     loop，
     而是
     accepted create-instance
     lower path
- 因而当前最佳表述应再更新为：
  当前最接近
  交汇面的地方
  已收紧成：
  accepted create-instance
  lower path
  内部/紧邻 surface
- 因而下一轮若继续推进，
  默认目标
  应进一步收紧成：
  在该 lower path
  内部/紧邻位置
  找第一处同时接触
  hidden-handle-derived
  accepted state
  与
  selector-8 SHA-like
  per-weight family
  的 surface

### 2026-06-19 strongest current convergence candidate

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_convergence_candidate_probe.py`
  - `mps/ANE/.ane_runs/json/newinstance_convergence_candidate_verdict_20260619.json`
- 当前机器确认：
  1. `ANEHWDevice::ANE_ProgramCreateInstance_gated`
     已经同时看到：
     - `x25`
       additional-params
       侧
     - `x19`
       inner params blob
       侧
  2. hidden-handle family
     已在该函数内
     变成
     `additional_params+0x18 -> local_y`
  3. 同时，
     这也是当前已知
     inner create-instance
     params
     被做
     procedure / weight
     validation
     的首个 pinned 函数
- 因而当前最佳表述应再更新为：
  当前最强的
  visible convergence
  candidate
  已不再是
  抽象的
  lower path，
  而是
  `ANEHWDevice::ANE_ProgramCreateInstance_gated`
  本体
- 因而下一轮若继续推进，
  默认目标
  应再收紧成：
  在
  `ANEHWDevice::ANE_ProgramCreateInstance_gated`
  内部
  找第一处
  真实 join point
  where
  x25/additional-params
  state
  与
  x19/per-weight
  params
  共同影响
  同一 branch /
  helper /
  output surface

### 2026-06-19 earliest join-window boundary

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_create_instance_joinpoint_probe.py`
  - `mps/ANE/.ane_runs/json/newinstance_create_instance_joinpoint_verdict_20260619.json`
- 当前机器确认：
  1. `ANEHWDevice::ANE_ProgramCreateInstance_gated`
     里
     最早同时出现
     `x19`
     和
     `x25`
     的窗口
     只到：
     `cbz x1`
     这种
     参数非空校验
  2. 这说明
     “最早共同窗口”
     不等于
     “最早真实语义 join point”
  3. 当前下一步
     应自动跳过
     这种浅层
     argument validation
     窗口，
     继续找更深层的
     同窗口 branch/helper/output
- 因而当前最佳表述应再更新为：
  当前还没有
  找到
  真正的
  first semantic join point；
  已经排除掉的
  最早共同窗口
  只是浅层
  non-null validation

### 2026-06-19 manual deeper join-candidate ranking

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_create_instance_candidate_ranking_probe.py`
  - `mps/ANE/.ane_runs/json/newinstance_create_instance_candidate_ranking_verdict_20260619.json`
- 当前机器确认：
  1. 在当前已知
     deeper windows
     里，
     最强候选
     已收紧成：
     `0xfffffe000928da10`
  2. 该 call boundary
     已显式传入
     `x19`
     (`mov x2, x19`)
     同时仍带着
     accepted lower path
     的 live state
     (`x27`, `x22`)
  3. 相比之下：
     - `0xfffffe000928d494`
       更像
       accepted-state /
       resource lookup
     - `0xfffffe000928c9f8`
       更像
       preparatory gating
- 因而当前最佳表述应再更新为：
  当前下一步
  不应再泛读
  `ANE_ProgramCreateInstance_gated`
  全函数，
  而应直接锁定
  `0xfffffe000928da10`
  这个 helper call
  窗口

### 2026-06-19 first semantic join point confirmed

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_create_instance_semantic_join_confirm_probe.py`
  - `mps/ANE/.ane_runs/json/newinstance_create_instance_semantic_join_confirm_verdict_20260619.json`
- 当前机器确认：
  1. `0xfffffe000928da10`
     发生在
     hidden-handle /
     accepted-state
     一侧
     已经通过
     `local_y`
     路径
     解析出来之后
  2. 该 call boundary
     直接传入：
     - `x2 = x19`
       inner params
     - `x3 = x22`
       additional-params
       live state
  3. 因而它
     不再是
     浅层 validation，
     而是当前
     最早已钉住的
     first semantic join point
- 因而当前最佳表述应再更新为：
  当前最早的
  semantic join point
  已确认是：
  `0xfffffe000928da10`
  这处 helper call
- 因而下一轮若继续推进，
  默认目标
  应再收紧成：
  识别
  `0xfffffe0009354710`
  这个 callee
  是什么，
  以及它真正消耗
  哪些参数

### 2026-06-19 current strongest lower-control helper candidate

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_create_instance_callee_role_probe.py`
  - `mps/ANE/.ane_runs/json/newinstance_create_instance_callee_role_verdict_20260619.json`
- 当前机器确认：
  1. `0xfffffe0009354710`
     这个 call
     只会在
     两层 gate
     之后到达：
     - 先过一个
       accepted-state /
       mode-like
       helper
     - 再过一个
       `[sp+0x68] + 0xf5ac3`
       byte flag
  2. 它真正收到的参数是：
     - `x1 = x27`
       accepted-state /
       resource side
     - `x2 = x19`
       full inner params
     - `x3 = x22`
       additional-params-derived
       side state
  3. 因而它当前是
     最强的
     lower-control helper
     候选，
     比继续读
     更高层 branch
     更有价值
- 因而当前最佳表述应再更新为：
  当前下一步
  不应再问
  “join point 在哪”，
  而应直接问：
  `0xfffffe0009354710`
  到底是什么 family，
  又真正消耗
  `x1/x2/x3`
  中的哪些参数

### 2026-06-19 callee early parameter dominance

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_callee_param_dominance_probe.py`
  - `mps/ANE/.ane_runs/json/newinstance_callee_param_dominance_verdict_20260619.json`
- 当前机器确认：
  1. `0xfffffe0009354710`
     一进来
     最早先消费
     `x2`
     (`[x2+0x108]`,
     `x2+0x110`)
     来做
     inner params /
     procedure 迭代
  2. 然后才消费
     `x1`
     作为
     accepted-state /
     resource-side
     object surface
  3. `x3`
     当前在开头
     只被复制成
     `x27`，
     还没有在
     第一轮控制流里
     真正变成
     decisive use
- 因而当前最佳表述应再更新为：
  当前真正未解的
  参数问题
  已收紧成：
  `x3/x27`
  在 callee 内
  第一次什么时候
  真正变成
  语义活跃的输入

### 2026-06-19 `x27` first semantic use

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_callee_x27_first_use_probe.py`
  - `mps/ANE/.ane_runs/json/newinstance_callee_x27_first_use_verdict_20260619.json`
- 当前机器确认：
  1. `x27`
     开头只是
     incoming `x3`
     的副本
  2. 第一次真正的
     语义活跃使用
     出现在
     `0xfffffe0009354a0c`：
     `add x27, x28, x21, lsl #3`
     它把
     x3-derived state
     materialize 成
     per-entry object
     surface
  3. 随后这块
     derived surface
     被：
     - `str x0, [x27,#0x20]`
     - `ldr x2, [x27,#0x20]`
     - `mov x3, x27 ; bl #0xfffffe0009358590`
     继续向下传
- 因而当前最佳表述应再更新为：
  `x3/x27`
  的 first semantic use
  已经从
  “在哪一条指令”
  收紧到
  “它之后的
  `0xfffffe0009358590`
  helper
  是否才是
  真正的下一个
  decisive lower-control helper”

### 2026-06-19 `0xfffffe0009358590` early-use boundary

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_next_helper_param_use_probe.py`
  - `mps/ANE/.ane_runs/json/newinstance_next_helper_param_use_verdict_20260619.json`
- 当前机器确认：
  1. 这个 callee
     开头依旧是
     `x2`
     先主导，
     `x1`
     次之
  2. `x3`
     在前几十条里
     仍没有变成
     decisive input，
     只在更后面的
     辅助 / 格式化
     分支里露头
- 因而当前最佳表述应再更新为：
  `0xfffffe0009358590`
  当前更像
  中间的
  辅助 / 预处理
  helper，
  还不是
  明确的
  decisive lower-control
  helper
- 因而下一轮若继续推进，
  默认目标
  不应再停留在
  这个 callee
  的开头窗口，
  而应继续找
  更深一层
  真正消费
  `x3/x27`
  的 helper

### 2026-06-19 `0xfffffe000b828e50` callsite-shape boundary

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_b828e50_role_probe.py`
  - `mps/ANE/.ane_runs/csv/ane_newinstance_b828e50_role_probe.csv`
  - `mps/ANE/.ane_runs/json/newinstance_b828e50_role_verdict_20260619.json`
- 当前机器确认：
  1. 在
     `0xfffffe0009358b84..0xfffffe0009358ba0`
     的 callsite
     上，
     `0xfffffe000b828e50`
     收到：
     - `x1 = x22`
     - `w2 = 2`
     - `x3 = x29 - 0x38`
     - `x4 = x29 - 0x3c`
     - `x5 = x29 - 0x3d`
     - `x6 = sp + 0x48`
     - `x7 = sp + 0x40`
  2. 该 callee
     一进来先：
     - `str xzr, [x3]`
     - `str wzr, [x4]`
     - `strb wzr, [x5]`
     - `str xzr, [x6]`
     - `str xzr, [x7]`
     明确先清空
     多个 byref / out
     槽位
  3. 随后立刻
     `cmp w2, #3`
     并把
     `x3..x7`
     固化到
     `x22..x20`
     与栈槽，
     当前更像
     parser / materializer /
     byref-plumbing
     入口，
     还不像
     terminal create-instance
     commit 点
- 因而当前最佳表述应再更新为：
  `0xfffffe000b828e50`
  的 machine-local
  入口形状
  已经明显偏向
  byref-heavy helper，
  但仅凭
  shell-only
  反汇编窗口
  还不足以
  单独判定
  `auxiliary only`
- 因而下一轮若继续推进，
  默认目标
  应收紧成：
  用 focused IDA
  读取
  `0xfffffe000b828e50`
  的第一批
  语义性分支 /
  direct callee /
  out-slot
  消费点，
  判断它究竟是
  parser/materializer
  层
  还是
  first accepted-state
  lower-control helper

### 2026-06-19 `0xfffffe000b828e50` out-slot materialization boundary

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_b828e50_outslot_probe.py`
  - `mps/ANE/.ane_runs/csv/ane_newinstance_b828e50_outslot_probe.csv`
  - `mps/ANE/.ane_runs/json/newinstance_b828e50_outslot_verdict_20260619.json`
- 当前机器确认：
  1. `0xfffffe000b828e50`
     的第一批
     direct callee
     依次是：
     - `0xfffffe000b851124`
     - `0xfffffe000b79a1e4`
     - `0xfffffe000b8b16b0`
     - `0xfffffe000b8b3858`
     - `0xfffffe000b828970`
  2. 在
     `mov x0, x25; mov x1, x22; mov x2, x21; mov x3, x20; bl #0xfffffe000b828970`
     之前，
     当前窗口
     只看到：
     - 句柄/对象 lookup
     - bitmask / range validation
     - caller 提供
       byref/out
       槽位的
       清零与复位
  3. success path
     明确把
     materialized range/length
     风格的结果
     写回 caller：
     - `[x28] = [x25 + 0x10]`
     - `[*saved_x7] = [x25 + 0x18] - [x25 + 0x10]`
  4. failure / retry path
     会再次
     `str xzr, [x22]`
     与
     `str wzr, [x21]`，
     更像
     parser/materializer hygiene，
     不像
     accepted-state
     lower-control commit
- 因而当前最佳表述应再更新为：
  `0xfffffe000b828e50`
  已可判定为
  auxiliary-only
  parser/materializer
  子层；
  它的 first decisive work
  是
  object lookup /
  validation /
  out-slot materialization，
  而不是
  first accepted-state
  lower-control action
- 因而下一轮若继续推进，
  默认目标
  不应再把
  `0xfffffe000b828e50`
  本身
  当成答案，
  而应下推到：
  第一处真正消费
  它物化出来的
  out-slot / range / object
  结果，
  并进入
  accepted-state
  control
  的后续 callee

### 2026-06-19 first follow-on accepted-state callee after `0xfffffe000b828e50`

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_followon_callee_probe.py`
  - `mps/ANE/.ane_runs/csv/ane_newinstance_followon_callee_probe.csv`
  - `mps/ANE/.ane_runs/json/newinstance_followon_callee_verdict_20260619.json`
- 当前机器确认：
  1. 在
     `0xfffffe000b828e50`
     之后可见的
     follow-on callee
     里，
     `0xfffffe000b851124`
     更像
     小型 ref/guard helper，
     `0xfffffe000b79a1e4`
     / `0xfffffe000b8b16b0`
     / `0xfffffe000b8b3858`
     仍更像
     object / intermediate
     准备层
  2. `0xfffffe000b828970`
     是第一处
     直接收到
     parent helper
     物化结果三元组
     的 callee：
     - `x1 = x22`
     - `x2 = x21`
     - `x3 = x20`
  3. 该函数
     success path
     明确写回：
     - `str x9, [x22]`
     - `str w8, [x21]`
     - `strb w8, [x20]`
     且这些写回
     发生在
     `[x19+0x48]`
     / `[x19+0x7c]`
     / `[x8+0x20]`
     等状态检查之后
- 因而当前最佳表述应再更新为：
  `0xfffffe000b828970`
  已是
  `0xfffffe000b828e50`
  之后
  first visible
  follow-on
  accepted-state
  callee；
  它是当前最早
  同时
  消费
  materialized outputs
  并把它们转成
  accepted-state
  control outputs
  的可见 surface
- 因而下一轮若继续推进，
  默认目标
  应再收紧成：
  识别
  `0xfffffe000b828970`
  本身
  是不是
  first accepted-state
  lower-control helper，
  还是
  更下层 decisive control
  之前的
  中间
  state/classification
  surface

### 2026-06-19 `0xfffffe000b828970` role boundary

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_b828970_role_probe.py`
  - `mps/ANE/.ane_runs/csv/ane_newinstance_b828970_role_probe.csv`
  - `mps/ANE/.ane_runs/json/newinstance_b828970_role_verdict_20260619.json`
- 当前机器确认：
  1. `0xfffffe000b828970`
     本体可见工作
     主要是：
     - state probing
     - qualification checks
     - 把
       object / flags / bool
       写回
       caller 提供的
       `[x22] / [x21] / [x20]`
  2. 它返回的
     仍是
     boolean-style
     success indicator
     (`mov w20, #1`
     / `mov w20, #0`)
     而不是
     更大结果结构
  3. 紧邻 caller
     `0xfffffe000b828a90`
     会再次：
     - `bl #0xfffffe000b828970`
     - 然后继续把
       `x22`
       解包/搬运到
       `x25`
       指向的
       更大结果结构
       （如
       `0xfffffe000b828bb8..0xfffffe000b828c34`
       的连续字段写回）
- 因而当前最佳表述应再更新为：
  `0xfffffe000b828970`
  已可判定为
  intermediate
  state/classification
  surface，
  不是
  final decisive
  lower-control helper；
  decisive control/state packaging
  仍在
  它之后
  继续向下
- 因而下一轮若继续推进，
  默认目标
  不应再停留在
  `0xfffffe000b828970`
  本体，
  而应下推到
  enclosing caller
  `0xfffffe000b828a90`
  的
  packaging/handoff
  路径，
  找第一处
  把
  `x22` 派生结果
  变成
  real lower-control
  structure
  的
  callee / step

### 2026-06-19 first real packaging step inside `0xfffffe000b828a90`

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_b828a90_packaging_probe.py`
  - `mps/ANE/.ane_runs/csv/ane_newinstance_b828a90_packaging_probe.csv`
  - `mps/ANE/.ane_runs/json/newinstance_b828a90_packaging_verdict_20260619.json`
- 当前机器确认：
  1. 在
     `bl #0xfffffe000b828970`
     之后，
     代码
     没有立刻
     hand off
     到新的
     decisive callee，
     而是直接开始
     从
     `x22`
     inline
     解包到
     `x25`
  2. 第一段连续的
     packaging window
     是：
     `0xfffffe000b828bb8..0xfffffe000b828c34`
  3. 这段窗口里，
     `x22` 派生字段
     被规范化并写入
     `x25`
     的多个偏移：
     - `+0x10`
     - `+0x00`
     - `+0x04`
     - `+0x08`
     - `+0x18`
     - `+0x1c`
     - `+0x20`
     - `+0x50`
     - `+0x58`
  4. 后续才出现
     `0xfffffe000b8b43a8`
     / `0xfffffe000b8afeac`
     / `0xfffffe000b85120c`
     这类
     operate-on-structure
     callee
- 因而当前最佳表述应再更新为：
  在
  `0xfffffe000b828a90`
  下面，
  first real
  lower-control
  packaging step
  不是
  direct callee，
  而是
  inline
  packaging window
  `0xfffffe000b828bb8..0xfffffe000b828c34`
- 因而下一轮若继续推进，
  默认目标
  应再收紧成：
  识别
  这段
  inline packaging
  之后
  哪个 later callee
  (`0xfffffe000b8b43a8`
  / `0xfffffe000b8afeac`
  / `0xfffffe000b85120c`)
  第一个
  真正作用于
  新物化出来的
  `x25`
  结构，
  成为
  更接近
  decisive lower-control
  logic
  的下一表面

### 2026-06-19 first post-packaging callee after `0xfffffe000b828bb8..0xfffffe000b828c34`

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_postpack_callee_probe.py`
  - `mps/ANE/.ane_runs/csv/ane_newinstance_postpack_callee_probe.csv`
  - `mps/ANE/.ane_runs/json/newinstance_postpack_callee_verdict_20260619.json`
- 当前机器确认：
  1. `0xfffffe000b8b43a8`
     是第一个
     以
     `x0 = sp`
     进入的
     callee，
     也就是
     第一个
     直接作用于
     刚物化好的
     local structure
     的表面
  2. 它开头就读取：
     - `[x0 + 0x30]`
     - `[x0 + 0x28]`
     - `ldp [x0 + 8]`
     并继续进入
     更深的
     stateful traversal
  3. `0xfffffe000b8afeac`
     只是更后面的
     conditional
     ref/count /
     lifecycle
     side path
  4. `0xfffffe000b85120c`
     则发生在
     本地结构
     再次归一化之后，
     其形状仍更像
     retain/release
     家族
- 因而当前最佳表述应再更新为：
  inline packaging
  之后
  first truly
  acts on
  the newly
  materialized
  `x25`
  结构的
  callee
  已收紧成
  `0xfffffe000b8b43a8`
- 因而下一轮若继续推进，
  默认目标
  应再收紧成：
  判定
  `0xfffffe000b8b43a8`
  本身
  是不是
  decisive lower-control
  surface，
  还是
  inline packaging
  之后的
  又一个
  intermediate
  structure walker

### 2026-06-19 `0xfffffe000b8b43a8` role boundary

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_b8b43a8_role_probe.py`
  - `mps/ANE/.ane_runs/csv/ane_newinstance_b8b43a8_role_probe.csv`
  - `mps/ANE/.ane_runs/json/newinstance_b8b43a8_role_verdict_20260619.json`
- 当前机器确认：
  1. `0xfffffe000b8b43a8`
     一进来就读取
     新物化结构里的：
     - `[x0 + 0x30]`
     - `[x0 + 0x28]`
     - `ldp [x0 + 8]`
  2. 它的第一批
     visible callee
     是：
     - `0xfffffe000b79abf4`
     - `0xfffffe000b8b378c`
     - `0xfffffe000b8b0f38`
     组合起来更像
     checks / link traversal /
     subobject walk
  3. 本地可见的
     state mutation
     `str x23, [x19, #0x30]`
     也更像
     更新 walked node
     的追踪状态，
     不像
     terminal lower-control
     commit
  4. `reverse-engineer`
     子代理复核
     仓库现有证据后，
     结论同样是
     `lean intermediate`
- 因而当前最佳表述应再更新为：
  `0xfffffe000b8b43a8`
  已可判定为
  inline packaging
  之后的
  又一个
  intermediate
  structure walker，
  不是
  final decisive
  lower-control
  surface
- 因而下一轮若继续推进，
  默认目标
  应再收紧成：
  在
  `0xfffffe000b8b43a8`
  的更深 callee
  里，
  比较
  `0xfffffe000b8b378c`
  与
  `0xfffffe000b8b0f38`
  哪个是
  下一层
  更强的
  decisive lower-control
  候选

### 2026-06-19 stronger next-layer candidate: `0xfffffe000b8b0f38`

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_b8b378c_vs_b8b0f38_probe.py`
  - `mps/ANE/.ane_runs/csv/ane_newinstance_b8b378c_vs_b8b0f38_probe.csv`
  - `mps/ANE/.ane_runs/json/newinstance_b8b378c_vs_b8b0f38_verdict_20260619.json`
- 当前机器确认：
  1. `0xfffffe000b8b378c`
     更像
     上层 gate/wrapper；
     它在轻量
     flag check
     和
     sibling-object
     test
     之后，
     直接在
     `0xfffffe000b8b3810`
     调用
     `0xfffffe000b8b0f38`
  2. `0xfffffe000b8b0f38`
     本体
     才真正做
     更深的
     field-by-field
     comparison：
     - `[x2 + ...]`
       对
       `[x19 + ...]`
     - range/base/flag
       equivalence
     - 多个
       post-check
       helper call
  3. 只有
     `0xfffffe000b8b0f38`
     当前可见地
     继续进入
     更深 helper chain：
     - `0xfffffe000b8b11f4`
     - `0xfffffe000b8686d8`
     - `0xfffffe000b84c128`
     - `0xfffffe000b8b1240`
- 因而当前最佳表述应再更新为：
  在
  `0xfffffe000b8b43a8`
  之下，
  更强的
  next-layer
  decisive lower-control
  候选
  已收紧成
  `0xfffffe000b8b0f38`；
  `0xfffffe000b8b378c`
  应降级为
  prefilter/wrapper
- 因而下一轮若继续推进，
  默认目标
  应再收紧成：
  判定
  `0xfffffe000b8b0f38`
  本身
  是不是
  decisive lower-control
  surface，
  还是
  需要继续下推到
  它的
  post-check
  callees

### 2026-06-19 `0xfffffe000b8b0f38` role boundary

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_b8b0f38_role_probe.py`
  - `mps/ANE/.ane_runs/csv/ane_newinstance_b8b0f38_role_probe.csv`
  - `mps/ANE/.ane_runs/json/newinstance_b8b0f38_role_verdict_20260619.json`
- 当前机器确认：
  1. `0xfffffe000b8b0f38`
     本体
     可见工作
     仍主要是：
     - field-by-field
       equivalence checks
     - range/base/flag
       comparison
     - gate/branch
       决策
  2. 只有当这些 checks
     全部通过后，
     它才进入
     post-check
     helper chain
     `0xfffffe000b8b10c4..0xfffffe000b8b10ec`
  3. 在这些
     post-check
     callee 里，
     `0xfffffe000b8686d8`
     是第一处
     当前可见地
     对 downstream state
     做实质更新的表面：
     - `str x19, [x1,#0x18]`
     - 调整
       `[x0,#0x60]`
     相比之下
     `0xfffffe000b8b11f4`
     / `0xfffffe000b8b1240`
     更像
     ref/lifecycle
     helper，
     `0xfffffe000b84c128`
     更像
     validity helper
- 因而当前最佳表述应再更新为：
  `0xfffffe000b8b0f38`
  已可判定为
  post-check
  wrapper/gate，
  不是
  final decisive
  lower-control
  surface；
  当前更深一层
  最强候选
  已收紧成
  `0xfffffe000b8686d8`
- 因而下一轮若继续推进，
  默认目标
  应再收紧成：
  判定
  `0xfffffe000b8686d8`
  本身
  是不是
  decisive lower-control
  surface

### 2026-06-19 `0xfffffe000b8686d8` visible lower-control boundary

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_b8686d8_role_probe.py`
  - `mps/ANE/.ane_runs/csv/ane_newinstance_b8686d8_role_probe.csv`
  - `mps/ANE/.ane_runs/json/newinstance_b8686d8_role_verdict_20260619.json`
- 当前机器确认：
  1. `0xfffffe000b8686d8`
     在可见入口窗口里
     已经直接做
     downstream state
     写入：
     - `str x10, [x0,#0x60]`
     - `str x19, [x1,#0x18]`
  2. 它的本体
     不再只是
     compare / gate /
     traversal，
     而是继续进入
     更深的
     index / bitmap / offset
     处理逻辑
  3. 相邻的
     post-check
     helper
     `0xfffffe000b8b11f4`
     / `0xfffffe000b8b1240`
     更像
     ref/lifecycle
     辅助，
     `0xfffffe000b84c128`
     更像
     validity helper
  4. 因而在
     当前 machine-local
     可见证据里，
     `0xfffffe000b8686d8`
     已是
     first surface
     that turns
     accepted object/structure
     information
     into
     sustained downstream
     control-state mutation
- 因而当前最佳表述应再更新为：
  `0xfffffe000b8686d8`
  已经是
  当前路径上
  strongest visible
  decisive lower-control
  surface so far
- 因而下一轮若继续推进，
  默认目标
  应再收紧成：
  若还要继续下推，
  只验证
  其内部
  最深的
  state-authoring
  subcall
  `0xfffffe000b864b10`
  究竟只是
  internal helper
  还是
  true terminal
  decisive primitive

### 2026-06-19 `0xfffffe000b864b10` terminal-subprimitive boundary

- 新证据：
  - `mps/ANE/experiments/ane_newinstance_b864b10_terminal_probe.py`
  - `mps/ANE/.ane_runs/csv/ane_newinstance_b864b10_terminal_probe.csv`
  - `mps/ANE/.ane_runs/json/newinstance_b864b10_terminal_verdict_20260619.json`
- 当前机器确认：
  1. `0xfffffe000b864b10`
     的可见本体
     主要是：
     - table / bitmap / index
       扫描
     - 局部 record
       更新
     - 局部结果
       回写
  2. 它的可见写入
     都很窄且局部：
     - `strh [x0,#4]`
     - `str [x12]`
     - `str [x0]`
     然后通过
     `ldr x0, [x0]; ret`
     返回
  3. 上层 caller
     `0xfffffe000b8686d8`
     才负责：
     - 接受 object/structure
       关系
     - 持续的
       downstream
       control-state
       mutation
       （`[x0,#0x60]`
       / `[x1,#0x18]`）
- 因而当前最佳表述应再更新为：
  `0xfffffe000b864b10`
  更像
  `0xfffffe000b8686d8`
  之下的
  internal
  algorithmic
  terminal sub-primitive，
  而不是
  更高层的
  decisive lower-control
  surface
- 因而当前机器上的
  strongest visible
  lower-control surface
  仍是
  `0xfffffe000b8686d8`
- 因而下一轮若继续推进，
  默认目标
  应从纯静态层
  收回到
  runtime-facing
  证据：
  验证
  `0xfffffe000b8686d8`
  这一层
  能否与
  single-process reuse
  blocker family
  建立更直接的
  连接；
  若不能，
  则需要正式记录
  “matching build / IDB
  address-space blocker”

### 2026-06-19 runtime bridge vs address-space blocker boundary

- 新证据：
  - `mps/ANE/experiments/ane_runtime_bridge_or_blocker_probe.py`
  - `mps/ANE/.ane_runs/json/runtime_bridge_or_blocker_verdict_20260619.json`
- 当前机器确认：
  1. 当前 blocker family
     仍锚定在
     原始 daemon request
     `+0x528..+0x547`
     区域；
     visible author
     仍是
     non-visible
  2. 当前 strongest visible
     lower-control surface
     已经是
     `0xfffffe000b8686d8`
  3. 但当前机器上
     仍没有
     direct runtime-facing
     证据
     把
     `request +0x528..+0x547`
     blocker family
     与
     `0xfffffe000b8686d8`
     这一层
     直接连起来
  4. machine-local IDA
     路径
     当前被
     matching-build / IDB
     address-space mismatch
     卡住：
     现有 IDB
     与 kernel image
     都不覆盖
     `0xfffffe000b...`
     地址家族
- 因而当前最佳表述应再更新为：
  在当前机器上，
  对
  single-process reuse
  主线
  最准确的 runtime-facing
  结论是：
  还没有
  `request +0x528..+0x547`
  blocker family
  到
  `0xfffffe000b8686d8`
  level lower-control
  surface
  的 direct bridge evidence；
  当前硬阻塞
  是
  matching-build / IDB
  address-space mismatch
- 因而下一轮若继续推进，
  默认目标
  应再收紧成：
  先做一个
  不依赖 IDA 覆盖的
  最小
  runtime experiment；
  当前最小实现
  不是新 harness，
  而是扩展
  现有
  `ane_inmemory_new_instance_probe`
  的
  request-inline-sha
  matrix，
  让它在每个
  request variant
  上
  额外记录
  一个
  lower-path-facing
  observable

### 2026-06-19 runtime observable gap in the existing matrix

- 新证据：
  - `mps/ANE/experiments/ane_runtime_observable_gap_probe.py`
  - `mps/ANE/.ane_runs/json/runtime_observable_gap_verdict_20260619.json`
- 当前机器确认：
  1. 现有
     `ane_inmemory_new_instance_probe_request_inline_sha_matrix.csv`
     已覆盖：
     - `services_runtime_request_variant`
     - `services_runtime_request_layout`
     - `services_runtime_create_instance`
  2. 它已足够说明：
     所有 request-side
     inline-SHA
     变体
     都还停在同一
     `wrapper_status=0x14`
     rejection bucket
  3. 但它当前
     没有按
     request variant
     保留：
     - `wrapper_device_layout`
     - `services_runtime_registry_attempt`
     这类
     lower-path-facing
     observable
- 因而当前最佳表述应再更新为：
  下一步
  不需要
  重新发明一个
  runtime harness；
  当前最小有用动作
  是：
  扩展
  现有
  `ane_inmemory_new_instance_probe`
  的
  request-inline-sha
  matrix
  路径，
  让它在每个 variant
  上
  额外采样
  一个
  lower-path-facing
  observable
- 因而下一轮若继续推进，
  默认目标
  应再收紧成：
  重编并复跑
  现有
  `ane_inmemory_new_instance_probe`
  matrix，
  确认
  lower-path-facing
  observable
  是否真的出现

### 2026-06-19 rerun matrix lower-path-facing diff boundary

- 新证据：
  - `mps/ANE/.ane_runs/csv/ane_inmemory_new_instance_probe_request_inline_sha_matrix_rerun.csv`
  - `mps/ANE/experiments/ane_runtime_bridge_diff_probe.py`
  - `mps/ANE/.ane_runs/json/runtime_bridge_diff_verdict_20260619.json`
- 当前机器确认：
  1. 现有 harness
     重编并复跑后，
     每个 request variant
     现在都能看到
     `services_runtime_registry_attempt`
     rows
  2. 所有 request-side
     inline-SHA
     变体
     仍然停在同一
     `wrapper_status=0x14`
     rejection bucket
  3. 新出现的
     lower-path-facing
     observable
     里，
     `connect=0x4103`
     保持不变，
     `iokit_service entry`
     只呈现
     普通的
     per-call
     service-instance churn
     （不同调用递增），
     没有出现
     real-sha
     vs garbage-sha
     的分叉
- 因而当前最佳表述应再更新为：
  最小 runtime experiment
  已经真正跑通，
  但当前结果
  仍然是
  negative direct bridge：
  request-side
  inline-SHA
  authoring
  没有带来
  与 accepted-state
  lower path
  相关的
  可区分分叉，
  只看到
  ordinary
  service-instance churn
- 因而下一轮若继续推进，
  默认目标
  应再收紧成：
  要么在
  同一 harness
  上选一个
  更强的
  lower-path-facing
  observable，
  要么若没有
  更强 observable
  可用，
  就升级到
  matching-build / IDB

### 2026-06-19 rerun-v2 wrapper-device-layout diff boundary

- 新证据：
  - `mps/ANE/.ane_runs/csv/ane_inmemory_new_instance_probe_request_inline_sha_matrix_rerun_v2.csv`
  - `mps/ANE/experiments/ane_runtime_bridge_diff_v2_probe.py`
  - `mps/ANE/.ane_runs/json/runtime_bridge_diff_v2_verdict_20260619.json`
- 当前机器确认：
  1. 现有 matrix
     在每个 request variant
     上
     现在同时记录了：
     - `services_runtime_registry_attempt`
     - `services_runtime_device_attempt`
  2. 但新增的
     `wrapper_device_layout`
     信号
     对
     baseline /
     real mmap /
     real sha /
     garbage sha
     完全不分叉：
     - `owner_state=1`
     - `service_ready=0`
     - `service_connect=0x5403`
       全部不变
  3. 结合前一轮
     registry snapshots，
     当前机器
     在这一组 observable
     上
     仍然只暴露
     ordinary per-call
     service-instance churn，
     没有暴露
     request-variant-specific
     lower-path branch
- 因而当前最佳表述应再更新为：
  现有 harness
  上
  已尝试的
  lower-path-facing
  observable family
  当前基本耗尽；
  这些 observable
  足够证明
  request-side inline-SHA
  authoring
  还没有在
  当前可见
  accepted-state lower path
  上
  产生可区分分叉
- 因而下一轮若继续推进，
  默认目标
  应再收紧成：
  要么
  明确挑一个
  更强的
  lower-path-facing
  observable，
  要么若挑不出
  高价值 observable，
  就升级到
  matching-build / IDB

### 2026-06-19 current-bootkc drift boundary

- 新证据：
  - `mps/ANE/.ane_runs/json/iosurface_allocatefromsuperbuffer_current_bootkc_drift_verdict_20260619.json`
- 当前机器确认：
  1. 当前本机 kernelcache
     的 literal 扫描
     没有直接找到
     `IOSurfaceAllocateFromSuperbuffer`
  2. 因而
     当前本机
     `xref` probe
     作为“固定字串地址”扫描
     会返回
     `inconclusive`
  3. 但这当前更像
     bootkc / version drift
     的可见字符串层差异，
     不是第二个 visible consumer
     被重新打开
  4. project-local
     carrier / follow-through
     证据链
     仍然支持：
     boxed token
     的 visible path
     止于
     `OSDictionary -> IOSurfaceRoot::createSurface`
- 因而当前最佳表述应再更新为：
  这个 drift
  应被记作
  “当前 bootkc 可见字符串层差异”，
  不是当前 blocker boundary
  的反证

### 2026-06-19 host-local IM4P extraction unlocked

- 新证据：
  - `mps/ANE/experiments/ane_im4p_extract_probe.py`
  - `mps/ANE/.ane_runs/json/im4p_extract_probe_verdict_20260619.json`
  - `mps/ANE/.ane_runs/tmp/kernelcache.release.mac15s.payload.bin`
  - `mps/ANE/.ane_runs/tmp/kernelcache.release.mac15s.payload.decoded.bin`
- 当前机器确认：
  1. 选定 Preboot 工件
     `/System/Volumes/Preboot/C81FACCB-1E13-49BF-ACBC-4086DB16E2FD/restore-staged/kernelcache.release.mac15s`
     是
     DER-encoded
     `IM4P`
     容器，
     payload tag
     为
     `krnl`
  2. 主 payload
     可由本机本地
     DER 解析
     直接提取，
     提取结果
     magic
     为
     `bvx2`
  3. 当前 host
     可直接使用
     系统自带
     `/usr/bin/compression_tool -decode -a lzfse`
     将该 payload
     解压成
     117817344-byte
     decoded 文件
  4. decoded 文件
     已被
     `file`
     识别为
     `Mach-O 64-bit arm64e`
  5. decoded 文件
     已被
     `kmutil inspect -B --show-fileset-entries`
     识别为
     boot kernel collection /
     fileset，
     且当前可见
     `com.apple.kernel`
     等
     `LC_FILESET_ENTRY`
- 结论：
  matching-build 路径的单一 blocker
  已不再是
  “缺少 host-local IM4P 提取能力”；
  当前更精确的下一层问题
  已收紧为：
  `ida-pro-mcp`
  / `idb_open`
  是否能直接消费
  这份 decoded payload

### 2026-06-19 decoded collection vs idalib consumer boundary

- 新证据：
  - `ida` 子代理对
    `mps/ANE/.ane_runs/tmp/kernelcache.release.mac15s.payload.decoded.bin`
    的最小
    `idb_open`
    probe
  - `pyimg4 im4p info`
    / `pyimg4 im4p extract`
    对同一工件的复核
  - `kmutil inspect -B --show-fileset-entries`
    对同一 decoded 文件的枚举
- 当前机器确认：
  1. `pyimg4`
     已确认
     当前工件
     `FourCC=krnl`
     `Description=KernelManagement_host-487.100.11`
     `Data compression type=LZFSE`
     `Encrypted=False`
  2. `pyimg4 im4p extract`
     产出的
     `kernelcache.release.mac15s.pyimg4.decoded.bin`
     与
     系统自带
     `compression_tool`
     链路的
     decoded 输出
     逐字节一致
  3. 同一 decoded 文件
     已被
     `kmutil`
     识别为
     boot kernel collection /
     fileset
  4. 但 `ida-pro-mcp`
     的
     `idb_open`
     对该 decoded collection
     在
     `prefer_headless`
     / `force_headless`
     / `prefer_gui`
     下
     全部失败；
     底层
     `idapro.open_database()`
     返回
     `ERR_OPEN(4)`
  5. 当前 decoded collection
     暴露出的
     ANE 相关
     fileset entry
     已至少确认：
     - `com.apple.driver.AppleH11ANEInterface`
     - `com.apple.driver.AppleT6030ANEHAL`
     - `com.apple.iokit.IOSurface`
- 结论：
  当前更精确的 blocker
  已从
  “整个 matching-build 工件不可见”
  收紧为：
  “整个 decoded fileset collection
  对 `idalib`
  仍是不可消费输入”。
  因而下一层合理入口
  不再是重试
  整个 collection，
  而是拆出
  单个 fileset entry
  再测
  `idb_open`

### 2026-06-19 AppleH11ANEInterface single-entry IDA entry unlocked

- 新证据：
  - `mps/ANE/experiments/ane_fileset_entry_extract_probe.py`
  - `mps/ANE/.ane_runs/json/fileset_entry_extract_probe_verdict_20260619.json`
  - `mps/ANE/.ane_runs/tmp/AppleH11ANEInterface.patched.macho`
  - `ida` 子代理对
    `AppleH11ANEInterface.patched.macho`
    的
    `idb_open`
    probe
- 当前机器确认：
  1. `AppleH11ANEInterface`
     单 fileset entry
     已被抽出并重建为
     独立 Mach-O：
     `mps/ANE/.ane_runs/tmp/AppleH11ANEInterface.patched.macho`
  2. 该文件
     已被
     `file`
     识别为
     `Mach-O 64-bit kext bundle arm64e`
  3. `ida-pro-mcp`
     对该单 entry
     在
     `prefer_headless`
     模式下
     `idb_open`
     直接成功，
     无需 GUI
     或降级
  4. 当前可复用
     `session_id`
     为
     `34a08b79`
- 结论：
  matching-build 路径的
  当前 blocker
  已不再是
  “找不到 IDA
  可消费入口”；
  当前最小可用
  语义入口
  已固定为
  `AppleH11ANEInterface`
  单 entry。
  下一层问题
  应收紧为：
  这个 entry
  对 lower control
  的 selector /
  request /
  descriptor /
  program-create /
  send-request
  语义覆盖是否足够

### 2026-06-19 selector 2 / 8 mapping confirmed

- 新证据：
  - `ida` 子代理基于
    `session_id=34a08b79`
    对
    `sANEDriverClientMethods`
    的窄表项解析
- 当前机器确认：
  1. `H11ANEInUserClient::externalMethod`
     位于
     `0xfffffe00092abdd8`
  2. 该函数
     不内联
     selector switch，
     而是把
     `sANEDriverClientMethods`
     （`0xfffffe000801e818`）
     传给
     `IOUserClient2022::dispatchExternalMethod`
  3. `sANEDriverClientMethods`
     共有
     `17`
     个表项
     （selectors
     `0..16`）
  4. 当前已确认
     的关键 selector
     映射为：
     - selector `2`
       → `ANE_ProgramSendRequest`
     - selector `8`
       → `ANE_ProgramCreateInstance`
  5. 当前已确认
     的相邻顺序为：
     - `0`
       `ANE_DeviceOpen`
     - `1`
       `ANE_DeviceClose`
     - `2`
       `ANE_ProgramSendRequest`
     - `3`
       `ANE_ProgramCreate`
     - `4`
       `ANE_ProgramPrepare`
     - `5`
       `ANE_ProgramUnprepare`
     - `6`
       `ANE_ProgramDestroy`
     - `7`
       `ANE_GetStatus`
     - `8`
       `ANE_ProgramCreateInstance`
     - `9`
       `ANE_ProgramChainingPrepare`
- 结论：
  当前 selector-level
  第一道 mapping
  已经足够明确。
  下一层问题
  不再是
  dispatch 表顺序，
  而是：
  selector `2`
  / `8`
  进入
  `ANEClientDevice::*`
  之后，
  哪一段
  first deeper stateful control
  最贴近
  private ANE
  single-process reuse
  blocker

### 2026-06-19 current default deeper target selection

- 当前机器确认：
  1. selector `8`
     → `ANE_ProgramCreateInstance`
  2. selector `2`
     → `ANE_ProgramSendRequest`
  3. 在当前长期主线里，
     `ProgramCreateInstance`
     与既有
     create-instance /
     newinstance /
     accepted-state control
     证据链
     更直接对齐
- 结论：
  当前默认 deeper target
  不再需要
  在 selector `2`
  与 `8`
  之间反复比较；
  应固定为
  selector `8`
  /
  `ANE_ProgramCreateInstance`
  进入
  `ANEClientDevice::*`
  后的
  first deeper stateful control

### 2026-06-19 ProgramCreateInstance next-hop confirmed

- 新证据：
  - `ida` 子代理基于
    `session_id=34a08b79`
    对
    `ANE_ProgramCreateInstance`
    wrapper 的窄下钻结果
- 当前机器确认：
  1. `ANE_ProgramCreateInstance`
     wrapper
     位于
     `0xfffffe00092acd38`
  2. 该 wrapper
     先两次调用
     `ANEClientDevice::getClient()`
     （`0xfffffe00092a7238`）
  3. 随后通过
     tail branch
     直接跳到
     `ANEClientDevice::programCreateInstance(ANEProgramParamsWrapper*)`
     （`0xfffffe00092a85a4`）
  4. `0x92a85a4`
     内当前最早
     已确认的
     stateful 候选点为：
     - `0x92a8678`
       `bl 0xbe6e210`
       （导入的
       alloc/new-like
       callee）
     - `0x92a86b8`
       `blraa [x19+0x218]`
       （对象相关
       vtable dispatch）
- 结论：
  当前 deeper chain
  已从
  selector-level wrapper
  收紧到
  `ANEClientDevice::programCreateInstance`
  方法体内部。
  下一层问题
  不再是
  “下一跳方法名/地址”，
  而是：
  `bl 0xbe6e210`
  与
  `blraa [x19+0x218]`
  谁更像
  first deeper stateful control

### 2026-06-19 first deeper stateful control verdict inside programCreateInstance

- 新证据：
  - `ida` 子代理对
    `0x92a8678`
    / `0x92a86b8`
    的窄角色判断
- 当前机器确认：
  1. `0x92a8678`
     的
     `bl 0xBE6E210`
     参数形态为：
     - `ptr=*a2`
     - `size=0x35E18`
     - `flags=0x20003`
     - `task=this+0x18`
  2. 当前最合理角色
     是：
     分配/构造辅助函数，
     更像
     IOKit /
     Buffer descriptor /
     Request object
     factory
  3. `0x92a86b8`
     的
     `blraa [x19+0x218]`
     使用的
     `x19`
     正是
     `0xBE6E210`
     的返回对象
  4. 因而
     `blraa [x19+0x218]`
     更像消费该对象的
     状态查询/
     校验步骤，
     不是入口侧
     first control
- 结论：
  当前 `selector 8`
  deeper chain
  的
  first deeper stateful control
  已收紧为
  `0xBE6E210`。
  下一层问题
  不再是
  A/B 候选比较，
  而是：
  `0xBE6E210`
  的具体角色
  与返回对象类型

### 2026-06-19 0xBE6E210 concrete role clarified

- 新证据：
  - `ida` 子代理基于
    `appleh11_entry`
    对
    `0xBE6E210`
    的窄角色判断
- 当前机器确认：
  1. `0xBE6E210`
     在
     `ANEResource::create<ANEResourceType4>`
     的反编译里
     被显式当作
     `IOMemoryDescriptor *`
     工厂调用
  2. 其参数模式为：
     `(aligned_size, raw_size, direction_flags|0x10000, owning_task)`
  3. 这更像
     `IOBufferMemoryDescriptor::withFlags`
     /
     `IOMemoryDescriptor`
     家族的
     DMA/backing-memory
     分配入口
  4. 返回到
     `x19`
     的对象
     最像
     `IOMemoryDescriptor`
     或其子类，
     而不是
     `ANERequest`
     业务对象本体
  5. 后续
     `prepare/complete`
     / vtable
     生命周期操作
     与这一判断一致
- 结论：
  当前 deeper chain
  的下一层问题
  已不再是
  “`0xBE6E210`
  到底是什么”，
  而是：
  谁 first consumes
  这个
  `IOMemoryDescriptor`
  并把它转成
  `ANEResource`
  / request-specific
  state

### 2026-06-19 current blocker: AppleH11 entry session rebuild instability

- 当前机器确认：
  1. `AppleH11ANEInterface.patched.macho`
     曾成功作为
     headless IDA
     入口使用，
     并支持
     selector /
     deeper-chain
     分析
  2. 但该入口的
     worker/session
     不稳定，
     先前会话
     会丢失
  3. 本轮再次尝试
     以
     `preferred_session_id=appleh11_state`
     重建会话，
     `idb_open`
     已直接失败：
     `Failed to open database`
- 结论：
  当前最小 blocker
  已临时从
  deeper control
  语义问题
  回退为
  `ida-pro-mcp`
  会话重建稳定性问题。
  下一轮恢复入口
  应先解决
  `AppleH11ANEInterface`
  单 entry
  的会话可复用性，
  然后再继续追
  `IOMemoryDescriptor`
  的 first consumer

### 2026-06-19 i64 reopen path confirmed

- 当前机器确认：
  1. 先前存在一个
     orphan worker
     `pid=20094`
     持有
     `AppleH11ANEInterface.patched.macho`
     的
     `.id0/.id1/.nam`
  2. 清掉该 worker 后，
     `AppleH11ANEInterface.patched.macho.i64`
     可再次成功
     `idb_open`
  3. 当前稳定可复用会话为：
     `appleh11_i64_reopen`
  4. 但原始
     `AppleH11ANEInterface.patched.macho`
     仍不能直接
     `idb_open`
- 结论：
  当前会话工程层
  的最小边界
  已经明确：
  `.i64`
  是可复用入口，
  原始 macho
  不是。
  这已经足以继续
  `IOMemoryDescriptor`
  消费链的
  语义下钻

### 2026-06-19 first ANE-specific consumer of IOMemoryDescriptor

- 新证据：
  - `ida` 子代理基于
    `appleh11_i64_reopen`
    对
    `IOMemoryDescriptor`
    消费链的窄下钻
- 当前机器确认：
  1. `clientMemoryForType`
     先产出
     `IOMemoryDescriptor*`
     与相关 size
  2. 该 descriptor
     经
     `ANEResourceCreationParams`
     传入
     `ANEClientResource::create`
     （`0xfffffe00092494ac`）
  3. 当前这是
     first ANE-specific
     resource 构造函数，
     也是 first consumer
     that turns
     `IOMemoryDescriptor`
     into
     `ANEResource`
     管理侧对象
  4. `ANEGroupResource::create`
     等后续函数
     操作的是
     已封装好的
     `shared_ptr<ANEResource>`
     而不是原始
     `IOMemoryDescriptor`
- 结论：
  当前 deeper chain
  已不再停留在
  descriptor /
  DMA memory
  获取层。
  下一层问题
  应收紧为：
  `ANEClientResource::create`
  内部如何进一步
  materialize
  成更贴近
  request /
  group /
  lower control
  blocker 的状态

### 2026-06-19 first materialization and group handoff after descriptor consumption

- 新证据：
  - `ida` 子代理基于
    `appleh11_i64_reopen`
    对
    `ANEClientResource::create`
    的窄下钻
- 当前机器确认：
  1. `ANEClientResource::create`
     的 first materialization
     step 是
     `ANEResource::create<ANEResourceType0>`
     （`0xfffffe000926ae30`）
  2. 该 step
     继续通过
     `ANEResource::C1`
     →
     `ANEResource::C2`
     完成
     `ANEResource`
     对象构造
  3. first handoff
     到更高层 group
     的步骤是
     `ANEResourceCollection::addResource`
     （`0xfffffe0009271644`）
  4. 到这一步为止，
     资源已从
     raw descriptor
     转成
     已注册的
     `shared_ptr<ANEResource>`
- 结论：
  当前 deeper chain
  已从
  descriptor consumer
  推进到
  first materialization +
  group handoff。
  下一层问题
  应收紧为：
  谁 first consumes
  `ANEResourceCollection::addResource`
  之后的
  已注册资源

### 2026-06-19 current blocker: active session is not directly addressable

- 当前机器确认：
  1. `idb_list`
     当前同时暴露：
     - `appleh11_i64_reopen`
       （可命名，
       但 `is_active=false`）
     - 一个
       `AppleH11ANEInterface.patched.macho`
       活跃 worker
       （`is_active=true`，
       但 `session_id=\"\"`）
  2. 对
     `ANEResourceCollection::addResource`
     的
     `xref_query`
     已能拿到结果，
     说明活跃 worker
     里确有当前分析状态
  3. 但当主线程继续做
     `decompile`
     时，
     无法以稳定的
     `database=<session_id>`
     方式引用
     该活跃 worker
- 结论：
  当前最小 blocker
  已从
  “会话完全没有”
  收紧为
  “活跃会话不可直接地址化”。
  下一轮恢复入口
  应先拿到一个
  MCP 可直接引用的
  会话 id，
  再继续
  `ANEResourceCollection::addResource`
  的函数体反编译

### 2026-06-19 post-registration consumer family after addResource

- 新证据：
  - 主线程基于
    `appleh11_i64_live`
    对
    `ANEResourceCollection::addResource`
    的反编译 +
    xref 查询
- 当前机器确认：
  1. `ANEResourceCollection::addResource`
     内部本体
     主要是
     `shared_ptr<ANEResource>`
     排序插入 /
     去重 /
     collection 持有
  2. 其静态 code xrefs
     已暴露出
     post-registration
     consumer family：
     - `ANEHWDevice::ANE_ProgramPrepareAndSubmitRequest_gated`
       (`0xfffffe000929c47c`)
     - `ANEHWDevice::ANE_MemoryMapRequest_gated`
       (`0xfffffe00092a0ac8`)
     - `ANEBufferCache::cacheResource`
       (`0xfffffe000930737c`)
     - `ANEGroupResource::addResource`
       (`0xfffffe000924c180`)
  3. 其中与
     private ANE
     request/control
     主线最直接对齐的
     是
     `ANE_ProgramPrepareAndSubmitRequest_gated`
- 结论：
  当前 deeper chain
  已不再停留在
  “谁 first consumes
  已注册资源”的泛问题。
  下一层问题
  应收紧为：
  `ANE_ProgramPrepareAndSubmitRequest_gated`
  中，
  已注册资源如何 first
  转成
  request/control
  state

### 2026-06-19 exact request/control state boundary

- 新证据：
  - `ida` 子代理基于
    `appleh11_i64_live`
    对
    `ANE_ProgramPrepareAndSubmitRequest_gated`
    的窄下钻
- 当前机器确认：
  1. 已注册
     `shared_ptr<ANEResource>`
     在该链中
     先经过：
     - 局部
       `ANEResourceCollection`
       构造
     - `shared_ptr<ANEResource>`
       拷贝
     - `ANEUnionResource::incrementUseCount`
     - `ANE_ProgramCheckandPrewireBuffers_gated`
  2. first turns
     resource/group
     state
     into request/control
     state
     的确切边界是：
     `ANERequest::create()`
     →
     `ANERequest::init()`
  3. `ANERequest::init()`
     内部会把：
     - `ANEHWDevice*`
     - program request args
     - transactionId
     - heap
       `ANEResourceCollection`
     组装到 request
  4. 后续硬件相关
     关键步骤
     已暴露为：
     `wireResources` →
     `dartMapResources` →
     `aneCmdSend`
- 结论：
  当前 deeper chain
  已从
  resource/group
  state
  正式推进到
  request/control
  state 边界。
  下一层问题
  应收紧为：
  在
  `wireResources` /
  `dartMapResources` /
  `aneCmdSend`
  中，
  哪一段 first
  触碰
  hardware-facing
  lower control

### 2026-06-19 first hardware-facing lower-control transition

- 新证据：
  - `ida` 子代理基于
    `appleh11_i64_live`
    对
    `wireResources` /
    `dartMapResources` /
    `aneCmdSend`
    的窄判定
- 当前机器确认：
  1. `wireResources`
     本质是
     child resource
     vtable wire loop，
     仍停留在
     resource preparation
     层
  2. `dartMapResources`
     本质是
     child resource
     DART-map loop，
     仍停留在
     resource preparation
     层
  3. 真正 first touches
     hardware-facing
     lower control
     的函数是：
     `ANEHWDevice::aneCmdSend(...)`
  4. 该链继续进入：
     `aneFirmwareCommandSend(...)`
     →
     `IOProcessorChannelSendRetry(...)`
  5. 这已经是
     IOKit firmware channel
     层的真实 send gate
- 结论：
  当前 deeper chain
  已从
  request/control
  state
  推进到
  hardware-facing
  lower-control
  transition。
  下一层问题
  应收紧为：
  `IOProcessorChannelSendRetry`
  前后的
  command send /
  completion /
  writeback
  路径

### 2026-06-19 command send packaging and completion boundary

- 新证据：
  - `ida` 子代理基于
    `appleh11_sendpath`
    对
    `aneFirmwareCommandSend` /
    `IOProcessorChannelSendRetry`
    前后的窄梳理
- 当前机器确认：
  1. `IOProcessorChannelSendRetry`
     之前，
     `ANEFirmwareCommandState`
     payload
     已被打包完成，
     当前关键字段包括：
     - `+0x50`
       carrier pointer
     - `+0x68`
       resource key
     - `+0x70`
       callback/function family
     - `+0x90`
       live flag
  2. queue slot
     入队后，
     response 侧最关键的
     已确认路径是：
     `processCommandResponse`
     →
     `handleOutstandingCommand`
  3. 当前 unresolved
     的下一层问题
     不再是
     send gate，
     而是：
     firmware→H11
     echo/response
     如何形成
     `payload+0x50`
     的 untagged match
- 结论：
  当前 deeper chain
  已从
  hardware-facing send gate
  推进到
  response/completion
  边界。
  下一层问题
  应收紧为：
  `processCommandResponse`
  /
  `handleOutstandingCommand`
  路径中的
  first completion /
  writeback /
  callback
  分叉

### 2026-06-19 current blocker: ida-pro-mcp transport closed

- 当前机器确认：
  1. `appleh11_response`
     会话曾成功打开
  2. 但本轮继续做
     `lookup_funcs`
     / `search_text`
     / `idb_list`
     时，
     `ida-pro-mcp`
     已统一返回：
     `Transport closed`
  3. 这已不是
     session id
     漂移问题，
     而是整个
     MCP transport
     当前不可用
- 结论：
  当前最小 blocker
  已临时从
  response/completion
  语义问题
  回退为
  `ida-pro-mcp`
  transport
  可用性问题。
  下一轮恢复入口
  应先恢复
  transport，
  然后再继续
  `processCommandResponse`
  /
  `handleOutstandingCommand`
  路径

### 2026-06-19 response/completion fork confirmed

- 新证据：
  - `ida` 子代理对
    `processCommandResponse`
    / `handleOutstandingCommand`
    的窄下钻
- 当前机器确认：
  1. `processCommandResponse`
     位于
     `0xfffffe00092d2960`
  2. `payload+0x50`
     当前已可确认是
     command tag /
     identifier
  3. 当前匹配机制
     已明确为
     直接等值比较：
     `*(cmdAddr+0x50) == responseTag`
  4. match 时
     直接进入：
     `handleOutstandingCommand(this, stateObj, true)`
  5. mismatch 且
     `payload+0x90`
     未标记已处理时，
     走
     `IOProcessorChannelSendRetry`
     重发 /
     writeback 路径
  6. `handleOutstandingCommand`
     内部当前已确认的
     下一层关键分叉是：
     `stateObj->field_0x68`
     是否非空；
     非空时进入
     request completion
     callback 链
- 结论：
  当前 deeper chain
  已从
  hardware-facing send gate
  推进到
  response/completion
  分叉边界。
  下一层问题
  应收紧为：
  `handleOutstandingCommand`
  内部的
  first completion /
  writeback /
  callback
  分叉

### 2026-06-19 handleOutstandingCommand three-way fork clarified

- 新证据：
  - `ida` 子代理基于
    `appleh11_completion`
    对
    `handleOutstandingCommand`
    的窄下钻
- 当前机器确认：
  1. `handleOutstandingCommand`
     位于
     `0xfffffe00092d2274`
  2. 分叉前
     公共动作包括：
     - 校验
       `cmdObj`
       仍在
       `fOutstandingCommands`
     - 解包
       `ANEFirmwareCommandState`
     - `state->completed = success`
  3. first completion
     下的三路分叉为：
     - **Callback**
       `callbackFunc != 0`
       且
       `callbackArg != 0`
       且
       `success == 1`
       → `_B618BF0()`
     - **Writeback**
       失败或 fallback
       条件下
       `DeviceMemoryManager::Free(...)`
     - **Mixed fallback callback**
       特定 flag
       下仍走
       `_B618BF0()`
  4. 三路最终都汇入
     共享尾部：
     `commandWakeup`
     /
     `lookupProgramResource`
     /
     callbackArg vtable[6]
     /
     `removeObject`
- 结论：
  当前 response/completion
  边界
  已不再是
  “是否分叉”的问题，
  而是：
  **Callback**
  这一路
  如何继续进入
  request completion
  链

### 2026-06-19 current blocker: loose IDB regeneration on reopen

- 当前机器确认：
  1. `appleh11_completion`
     会话名仍在
     `idb_list`
     中，
     但对应 worker
     已消失
  2. 此时磁盘上
     `AppleH11ANEInterface.patched.macho.i64`
     仍存在，
     但同时伴随
     新鲜时间戳的
     `.id0/.id1/.nam/.til`
  3. 主线程尝试把
     这些 loose IDB
     移走后，
     它们立刻再次出现
  4. 这说明
     当前 reopen 失败
     与
     lingering / regenerated
     loose IDB
     高度相关，
     已不是单纯
     `idb_open` 参数问题
- 结论：
  当前最小 blocker
  已从
  callback 语义边界
  临时回退为
  `.i64` 会话重开时
  loose IDB
  再生导致的
  会话不稳定问题。
  下一轮恢复入口
  应先解决
  这一工程层问题，
  再继续
  `handleOutstandingCommand`
  Callback

### 2026-06-19 `_B618BF0` is not a visible callback continuation inside AppleH11ANEInterface

- 新证据：
  - `ida` 子代理基于
    `/Volumes/2T/pymss/mps/ANE/.ane_runs/tmp/AppleH11ANEInterface.patched.macho.i64`
    的独立会话
    `427e0358`
    对
    `ANEHWDevice::handleOutstandingCommand(OSObject *, bool)`
    （`0xfffffe00092d2274`）
    做了 callback 分叉窄分析
- 当前机器确认：
  1. `_B618BF0`
     的唯一调用点在
     `0xfffffe00092d243c`
  2. 调用前参数装载是：
     - `X1 = [X22,#0x38]`
     - `W2 = [X22,#8]`
     更像
     `buffer_addr + buffer_size`
     而不是 callback function / callback arg
  3. 到达该点的局部条件是：
     - `v8 != NULL`
     - `*(v8 + 136) == 0`
     - `a3 == true`
     - `(*(v8 + 45) & 1) == 0`
  4. 调用返回后立即落入
     `DeviceMemoryManager::Free`
     判定与共享尾部
     `commandWakeup`
     路径，
     没有出现新的 completion continuation
  5. 目标地址
     `0xFFFFFE000B618BF0`
     超出
     `AppleH11ANEInterface.patched.macho`
     的映射末端
     `0xfffffe00080297c0`，
     是正常跨 kext
     `BL`
     目标，
     不是本 binary 内
     trampoline / dispatcher / visible callback invoker
- 因而当前最强表述应更新为：
  - `handleOutstandingCommand`
    里此前被暂称为
    “Callback”
    的 `_B618BF0`
    分叉，
    目前更像
    command-buffer free path
    的一部分，
    而不是 request completion callback continuation
  - 当前真正未决的问题已经收紧成：
    需要在完整
    decoded kernelcache
    里确认
    `0xFFFFFE000B618BF0`
    的真实符号/签名，
    才能正式把这条伪 callback 支线判死
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/handle_outstanding_callback_b618bf0_role_verdict_20260619.json`

### 2026-06-19 `_B618BF0` formally resolved to kernel `_memcpy` / `_memmove`

- 新证据：
  - 主线程直接对
    `kernelcache.release.mac15s.payload.decoded.bin`
    做
    `nm -n`
    精确匹配
  - `reverse-engineer`
    子代理用同一工件做了非 IDA 交叉验证
- 当前机器确认：
  1. 地址
     `0xFFFFFE000B618BF0`
     精确命中：
     - `_memcpy`
     - `_memmove`
  2. 紧邻符号为：
     - `0xFFFFFE000B618BE0`
       `_bcopy` / `_ovbcopy`
     - `0xFFFFFE000B618E50`
       `_memset`
  3. 因而此前把
     `_B618BF0`
     暂视为
     free helper
     的表述也应继续收紧：
     它既不是 callback continuation，
     也不是 free helper，
     而只是普通内核内存复制例程
- 因而当前最强表述应更新为：
  - `handleOutstandingCommand`
    里的 `_B618BF0`
    分叉
    已被正式判死为
    伪 callback 支线
  - 当前更接近 private ANE lower control blocker 的下一层问题，
    已重新收敛为：
    `handleOutstandingCommand`
    里真正承载
    completion / writeback
    语义的
    state consumer
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/handle_outstanding_b618bf0_memcpy_verdict_20260619.json`

### 2026-06-19 `lookupProgramResource` is the real shared-tail completion/writeback consumer

- 新证据：
  - `reverse-engineer`
    子代理对本地既有工件做了窄交叉验证，
    聚焦
    `handleOutstandingCommand`
    共享尾部的四个候选：
    `lookupProgramResource`
    / `commandWakeup`
    / `removeObject`
    / `DeviceMemoryManager::Free`
- 当前机器确认：
  1. 共享尾部当前最可信顺序是：
     `status writeback`
     →
     `lookupProgramResource(inner+0x68, &process, 0)`
     →
     `matched_process+0x20400 counter--`
     →
     `commandWakeup`
     →
     callback invoke
     →
     `removeObject`
     →
     timer cleanup
     →
     `DeviceMemoryManager::Free`
  2. `lookupProgramResource`
     是其中唯一的
     command-state
     → process-state
     桥梁：
     它解析出的
     `ANEProcess*`
     立即参与
     `process+0x20400`
     的
     `ldr -> subs -> str`
     写回
  3. 因而当前更强表述应更新为：
     - shared-tail
       里真正承载
       completion/writeback
       语义的
       state consumer
       已收紧为
       `lookupProgramResource`
     - wakeup/remove/free
       都应降级为通知或清理壳
- 当前新的更小未决问题：
  - `inner+0x68`
    这个 key
    的真实语义是什么
  - 谁在
    `lookupProgramResource`
    之后负责
    `process+0x203fc/0x20400`
    的 durable acceptance writeback
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/handle_outstanding_lookup_program_resource_consumer_verdict_20260619.json`

### 2026-06-19 `inner+0x68` semantics narrowed to hidden numeric lookup key family

- 新证据：
  - `doc-reader`
    子代理对
    `completion_process_counter_note.md`
    / `legacy_typed_completion_route_note.md`
    / `command_state_materialization_note.md`
    / `process_state_window_note.md`
    / `bootkc_resource_gate_process_registry_probe.md`
    做了窄压缩
  - 主线程复用
    `newinstance_hidden_handle_stage_verdict_20260619.json`
    的既有 machine-local 结论
- 当前机器确认：
  1. `inner+0x68`
     已不应再被表述成
     泛化 opaque field；
     它当前最强语义候选是：
     hidden numeric lookup key family
  2. 支撑这点的最硬 join
     仍然是：
     `x5 -> additional_params+0x18 -> local_y -> lookupProgramResource -> params[0]/x21[0]`
  3. `lookupProgramResource`
     解析的目标对象
     已与
     `resource+0x400d0`
     这张
     `OSArray<ANEProcess*>`
     注册表
     对齐，
     后续直接进入
     `process+0x20400`
     计数递减
  4. 因而当前真正未解的 lower gap
     已进一步收紧为：
     `process+0x203fc == 2`
     的 decisive writer
  5. 当前 visible writer family
     对
     `process+0x203fc`
     已基本封口：
     - `0`
       来自 init / cold zero family
     - `1`
       来自 save/restore/create-instance-side family
     - `2`
       仍无 exact visible writer
- 当前更高价值的下一问：
  - `process+0x203fc == 2`
    是否来自
    `lookupProgramResource`
    之后更低的 replay/restore 路径
  - 还是来自
    family-6 / process-state stack
    中尚未显式命中的 lower-stage author
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/inner68_hidden_key_and_process203fc_gap_verdict_20260619.json`

### 2026-06-19 `process+0x203fc == 2` author narrowed to a two-layer split

- 新证据：
  - `reverse-engineer`
    子代理对当前
    visible writer family
    与 negative surfaces
    做了窄汇总
- 当前机器确认：
  1. `process+0x203fc`
     的 visible exact-writer surface
     当前已基本封口：
     - `0`
       来自
       `ANEProcess::init`
       / `ANE_ProcessCreate_gated`
     - `1`
       来自
       `ANE_SaveState`
       / `ANE_RestoreStateEv.cold.2`
       / demote family
     - `2`
       仍无 exact visible writer
  2. 对
     `aneCmdSend`
     / `aneFirmwareCommandSend`
     / `handleOutstandingCommand`
     / `ANE_RestoreState`
     / `ProgramLoad(load_type==2)`
     的既有 exact-operand 检查
     当前都没有命中
     `0x203fc`
     写入
  3. `record+0x1b8`
     也没有 visible CPU-side durable writer，
     因而当前最强解释是：
     二者共同指向更低的
     replay/restore / firmware readback
     层
  4. 但在把结论正式下沉前，
     还剩一个很小的可见层缺口必须排掉：
     - `ANE_ProgramUnprepare`
     - `ANE_ProgramDestroy`
- 当前最高信噪比的下一问：
  - selectors `5/6`
    是否 exact-write
    `process+0x203fc`
  - 若否，
    则 `state==2`
    writer
    应正式归入更低 replay/restore 层
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/process203fc_state2_writer_layer_split_verdict_20260619.json`

### 2026-06-19 selectors 5/6 excluded from current visible `process+0x203fc` exact-writer set

- 新证据：
  - 主线程基于
    `appleh11_sel56_probe`
    会话，
    对
    `ProgramUnprepare`
    /
    `ProgramDestroy`
    家族
    做了最小 IDA probe
- 当前机器确认：
  1. `ProgramUnprepare`
     /
     `ProgramDestroy`
     相关函数
     在当前 IDB
     中可通过字符串邻域确认存在
  2. 同一轮
     `op_any == 0x3fc`
     窄扫描
     命中的函数集合里，
     没有 selector 5/6
     家族
  3. 这组 negative hits
     已足够把当前
     visible CPU-side
     selectors 5/6
     从
     `process+0x203fc`
     exact writer
     候选中降级
  4. 虽然后续
     IDA MCP transport
     再次关闭，
     但不影响本轮 negative-set 结论
- 因而当前更强表述应更新为：
  - `process+0x203fc == 2`
    的 author
    已不应继续优先在
    visible selector 5/6 family
    里寻找
  - 当前最可信的作者层级
    已正式下沉到：
    replay/restore
    /
    firmware-readback
    lower layer
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/process203fc_state2_selector56_exclusion_verdict_20260619.json`

### 2026-06-19 `record+0x1b8` narrowed to the strongest first lower surface

- 新证据：
  - `doc-reader`
    子代理压缩了
    `restore_record_raw_send_boundary_note.md`
    等直接相关 note
  - `reverse-engineer`
    子代理比较了
    `record+0x1b8`
    / `gate+0x220`
    / unload-side reply/replay path
  - 主线程复核了
    `ane_bootkc_restore_record_raw_send_boundary_probe.py`
    的静态边界结果
- 当前机器确认：
  1. `record+0x1b8`
     是当前最上游的
     visible lower state word：
     它被多条 replay/restore 路读取，
     但没有 visible CPU-side exact store
  2. `ANE_RestoreState`
     中，
     `aneCmdSend(raw)`
     返回后到
     `record+0x1b8`
     读取前，
     只有
     5
     条可见指令，
     且没有 store / helper call
  3. 因而当前最强表述应更新为：
     - `record+0x1b8`
       的 durable author
       位于 raw firmware send 以下
     - `gate+0x220`
       只是
       `record+0x1b8`
       的下游镜像消费点
     - `process+0x203fc == 2`
       的 author
       现在最像与
       `record+0x1b8`
       共享同一个更低 firmware/replay writer 层
- 当前最高信噪比的下一问：
  - raw send
    前后
    `record+0x1b8`
    的值是否发生变化
  - 若发生变化，
    它是否已经落入
    `{0,1,2}`
    或与
    `process+0x203fc`
    同构的 state family
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/process203fc_state2_first_lower_surface_record1b8_verdict_20260619.json`

### 2026-06-19 current runtime harness cannot directly observe `record+0x1b8`

- 新证据：
  - 主线程核查了当前所有可复用 runtime 入口：
    - `mps/ANE/experiments/ane_ioconnect_trace_interpose.c`
    - `mps/ANE/experiments/ane_services_program_create_runtime_probe.m`
    - `pymss/utils.py::_private_ane_trace_event`
  - 并与
    `ane_bootkc_restore_record_raw_send_boundary_probe.py`
    的静态边界结果交叉
- 当前机器确认：
  1. 现有 IOKit interposer
     只观察 selector 3/8
     的 userland request/output
     buffer
  2. 现有 private-ANE ndjson trace
     只记录高层 batch/cache
     生命周期事件
  3. `record+0x1b8`
     的 durable author
     已被静态压到
     raw firmware send
     以下，
     因而不在这些高层 harness
     的直接观测范围内
- 因而当前更高信噪比的结论是：
  - 下一步不应继续扩展当前 userland harness
    去“顺带”观察
    `record+0x1b8`
  - 必须先降低观测面，
    例如扩展最低层 interposer
    或增加专用 lower-side dump path
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/runtime_harness_record1b8_observability_boundary_verdict_20260619.json`

### 2026-06-19 lowest reusable runtime entry is the IOKit interposer family

- 新证据：
  - 主线程对
    `ane_ioconnect_trace_interpose.c`
    / `ane_services_program_create_runtime_probe.m`
    / `pymss/utils.py`
    / `ane_bootkc_post_send_replay_boundary_probe.py`
    做了并排核查
- 当前机器确认：
  1. 高层
     `PYMSS_PRIVATE_ANE_TRACE_PATH`
     只适合 batch/cache 级别事件，
     不是 lower-state 观测面
  2. 当前最低可复用 runtime 入口
     是
     IOKit interposer / runtime probe
     这一组
  3. 但它们今天仍只覆盖
     selector request/output buffer
     和 pointed userland buffer，
     还没有 lower-side dump path
  4. 结合 post-send boundary 现状，
     当前最值得扩下去的 lower post-send family
     是 unload-side
     `device+0x9c0 / 0x927d410`
     路，
     而不只是继续围绕 restore-side replay
- 当前更高价值的下一问：
  - 如何在现有 IOKit interposer/tooling 基础上，
    加一个最小 lower-side observability surface，
    触到 unload-side deeper post-send family
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/lower_runtime_probe_surface_selection_verdict_20260619.json`

### 2026-06-19 Mach-message lower runtime probe surface implemented

- 新证据：
  - 新增文件：
    `mps/ANE/experiments/ane_mach_msg_runtime_probe.c`
  - `Makefile`
    新增编译目标：
    `ane_mach_msg_runtime_probe.dylib`
  - 本地验证：
    - `make -C mps/ANE/experiments ane_mach_msg_runtime_probe.dylib`
    - `file`
    - `otool -hv`
- 当前机器确认：
  1. 当前最低可复用 probe 面
     已不再停留在设计阶段，
     而是有了可编译的
     `mach_msg`
     级 interposer 实现
  2. 它仍不直接等于
     `record+0x1b8`
     观测，
     但已经把运行时观测面
     从 selector-buffer
     再往下压了一层
  3. 下一步真正需要回答的问题
     已变成：
     把它挂到真实 ANE 调用路径后，
     是否能看到与
     `device+0x9c0 / 0x927d410`
     或更深 reply family
     对齐的消息面
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/mach_msg_runtime_probe_surface_impl_verdict_20260619.json`

### 2026-06-19 first mach_msg attach proved probe viability but not traffic capture

- 新证据：
  - 主线程把
    `ane_mach_msg_runtime_probe.dylib`
    挂到
    `ane_services_program_create_runtime_probe --fast-trace`
    上完成了首次实跑
- 当前机器确认：
  1. interposer
     自身可工作：
     目标进程没有因注入而崩溃，
     并成功生成
     `mach_msg_selector3_fasttrace_20260619.csv`
  2. 但当前 CSV
     只有表头，
     没有实际消息行
  3. 根因是：
     本次 target path
     在 `device_open_failed / missing_default_artifact`
     处过早退出，
     没有走到真正的
     ANE device message
     流量
- 因而当前更准确的结论是：
  - `mach_msg`
    probe 面
    已经从“实现”推进到“可挂载”
  - 当前剩余问题
    已收敛成：
    选择一个真正能穿过
    ANE device open/create
    流量的 target path
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/mach_msg_probe_first_attach_verdict_20260619.json`

### 2026-06-19 next runtime boundary narrowed back to the arm64e IOConnect auth slot

- 新证据：
  - 主线程用已知成功的 v17 target path 重跑后，
    `mach_msg`
    trace 仍然只有表头
  - 再与旧结论
    `selector3_import_stub_public_iokit_noop_interpose_note.md`
    对齐
- 当前机器确认：
  1. 问题已不再是 target path 选择
  2. 当前最高价值的 runtime 边界
     不是继续换更宽消息原语，
     而是回到先前已证实的
     arm64e
     `IOConnectCallStructMethod`
     import-stub/auth-slot
     面
  3. 这条边界已有两类关键证据：
     - 它就是 `rawCreateFn+0x108`
       实际命中的 public IOKit import stub
     - `dyld_dynamic_interpose`
       之前就已被证明没改动这条 authenticated slot
- 因而当前更高价值的下一问：
  - 直接 auth-slot patch / observe
    是否能 finally 命中 live selector-3 交通
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/runtime_boundary_back_to_iokit_auth_slot_verdict_20260619.json`

### 2026-06-19 arm64e auth-slot patch path already has live selector-3 success evidence

- 新证据：
  - 主线程直接复核了历史成功产物：
    - `...trace_runtime_manual_v9_arm64e_patch.json`
    - `...trace_runtime_manual_v10_arm64e_patch_ready1.json`
    - 对应 CSV
      `trace_selector3_runtime_manual_v9_arm64e_patch.csv`
      / `...v10...csv`
- 当前机器确认：
  1. plain interpose 的
     `runtime_manual_v7`
     只有表头
  2. 但在
     arm64e auth-slot patch
     路径上，
     CSV 已出现真实 selector-3 rows：
     - v9: 8 行
     - v10: 9 行
  3. 且 JSON
     已记录 slot patch
     真实写入后的值：
     - v9 `after_raw = 0xca2d00010410ebac`
     - v10 `after_raw = 0xc438800104a3ec98`
- 因而当前更强表述应更新为：
  - arm64e
    `IOConnectCallStructMethod`
    auth-slot patch/observe
    不只是“理论上最值得做”
  - 它已经是当前 machine-local
    唯一已知能命中 live selector-3 交通的 runtime boundary
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/auth_slot_patch_live_selector3_success_verdict_20260619.json`
  分叉下钻

### 2026-06-19 historical slot-patch replay now patches successfully but still yields zero live selector-3 rows

- 新证据：
  - 主线程按历史成功参数直接重跑：
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_manual_replay_20260619.json`
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_manual_replay_arm64e_20260619.json`
    - 对应 CSV：
      - `mps/ANE/.ane_runs/csv/trace_selector3_runtime_manual_replay_20260619.csv`
      - `mps/ANE/.ane_runs/csv/trace_selector3_runtime_manual_replay_arm64e_20260619.csv`
- 当前机器确认：
  1. 复用历史成功参数
     `--fast-trace --manual-transport --slot-patch-structmethod`
     与
     `only_case=live_mil_nonprecompiled_path_live_modelurl_mil`
     后，
     default 与 arm64e
     replay
     都只产出
     header-only
     selector-3 CSV
  2. 这不是
     live compile/load
     失败：
     两次 replay
     都显示
     `live_device_compile_ok=true`
     `live_device_load_ok=true`
  3. 这也不再能归因于
     “没走 arm64e /
     没用 ptrauth intrinsics”：
     `ane_services_program_create_runtime_probe_arm64e`
     replay
     已恢复
     `ptrauth_intrinsics=true`
     且 slot patch
     写入成功
  4. 因而当前最小缺口已从
     “如何重放成功路径”
     收紧成：
     patched import slot
     为什么在当前 runtime
     里没有被实际命中
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/auth_slot_patch_replay_zero_hit_verdict_20260619.json`

### 2026-06-19 first decisive replay drift is the missing rawCreate ready-gate override

- 新证据：
  - 主线程直接比较
    `v9/v10/replay_arm64e`
    的同构字段，
    并补做一个最小对照：
    只在
    `replay_arm64e`
    上加
    `--rawcreate-force-ready1`
  - 新产物：
    - `benchmark_results/private_ane/ane_services_program_create_runtime_probe_trace_runtime_manual_replay_arm64e_force_ready1_20260619.json`
    - `mps/ANE/.ane_runs/csv/trace_selector3_runtime_manual_replay_arm64e_force_ready1_20260619.csv`
- 当前机器确认：
  1. `replay_arm64e_20260619`
     与历史成功
     `v10`
     的第一处决定性差异是：
     `rawcreate_force_ready1=false`
  2. baseline replay
     虽然
     slot patch
     与
     `ptrauth_intrinsics`
     都已正常，
     但因为
     rawCreate
     ready-gate
     没打开，
     CSV 仍只有表头
  3. 在其余参数完全不变时，
     只补
     `--rawcreate-force-ready1`
     当前 machine-local
     就立即恢复
     selector-3 live row：
     `selector=3`
     `ret=0xe00002c2`
  4. 因而之前看似
     “patched slot
     未被实际命中”
     的根因
     不是 slot patch 失效，
     而是
     rawCreate
     在 ready-gate
     关闭时直接 short-circuit，
     根本不发送 selector-3
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/auth_slot_ready_gate_replay_verdict_20260619.json`

### 2026-06-19 natural ready-gate author is the higher-level user-client split, not a later callback

- 新证据：
  - 主线程复核
    `open_reply_ready_byte_alignment_note.md`
    中
    `ANEClientDevice::open`
    /
    `ANEClientInfo::create`
    /
    `H11ANEInDirectPathClient`
    /
    `H11ANEInUserClient`
    这一组现有静态链，
    并与当前
    `usageType=1`
    成功样本、
    `mode/usageType=3`
    失败样本对齐
- 当前机器确认：
  1. `service+0x18`
     的自然 author
     不在 open 返回后的
     callback / receiver
     路径上，
     而在 open 阶段的
     higher-level user-client split
  2. 当前 lineage
     已收紧成：
     `ANEClientInfo+0x10`
     -> `ANEClientDevice+0x28`
     -> `selector-0 reply+0x1c`
     -> `service+0x18`
  3. 当前所有成功 local open
     都必然走
     `usageType=1`
     的 direct-path：
     `H11ANEInDirectPathClient::init`
     -> `ANEClientInfo::create(task, 1, 0, 1)`
     因为 `b1=0`，
     所以 ready byte
     为 `0`
     是设计使然，
     不是丢写
  4. 当前唯一已知可能自然产出
     ready=`1`
     的路径是：
     `H11ANEInUserClient::init`
     -> `ANEClientInfo::create(task, 2, 1, 1)`
     但它受
     `com.apple.ane.iokit-user-access`
     entitlement
     gate
     约束，
     当前 probe
     走不通
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/ready_gate_natural_author_verdict_20260619.json`

### 2026-06-19 no current machine-local evidence of a reachable non-direct/private open route without new entitlements

- 新证据：
  - 主线程复核
    `open_sweep_v9_usage3`
    /
    `v10_outermode3`
    runtime
    结果、
    `fresh_controller`
    /
    `programhandleopen`
    变体结论，
    并结合本机私有框架导出面扫描
- 当前机器确认：
  1. `usageType=3`
     与
     `mode=3`
     的现有 runtime
     尝试都只返回
     `0x18`，
     没有拿到非零 device handle
  2. `fresh_controller`
     /
     `programhandleopen`
     只是在已有 visible
     device/control-state
     上重放同一 partial family，
     没有 materialize
     新的 regular open route
  3. 静态上
     regular/hinted
     user-client family
     的确存在，
     但当前 runtime
     证据只证明“它存在”，
     不证明“当前 probe
     能走通它”
  4. 当前 probe
     二进制仍看不到 embedded
     entitlement XML；
     而 natural ready-gate
     author
     所在 regular path
     仍受
     `com.apple.ane.iokit-user-access`
     gate
     约束
- 因而当前更强的表述是：
  - 当前 machine-local
    尚未发现
    不依赖新签名 entitlement
    的本地可达
    non-direct/private open route
  - 当前 blocker
    已正式收敛为：
    entitlement-gated
    higher-level open family
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/non_direct_route_reachability_verdict_20260619.json`

### 2026-06-19 direct hinted-open blind probe crashes before yielding a usable status/device result

- 新证据：
  - 主线程新增并运行
    `mps/ANE/experiments/ane_services_hinted_open_probe.m`
    只做
    `_ANEServicesLocateAndOpenHintedDevice`
    的最小直调实验
- 当前机器确认：
  1. `_ANEServicesLocateAndOpenHintedDevice`
     确实真实导出，
     且
     `_ANEServicesDeviceOpen`
     内部确实会调用它
  2. 但按当前可见
     `ANEServicesDeviceOpen`
     配置布局做的
     “最低风险直调”
     在当前 machine-local
     上直接以
     `139`
     退出，
     输出 JSON
     文件为空
  3. 这说明当前失败
     不是
     `status != 0`
     或
     `device == nil`
     这类业务级否定，
     而是
     `_ANEServicesLocateAndOpenHintedDevice`
     的 ABI / 参数布局
     仍未恢复到
     可安全调用
     的程度
- 因而当前更准确的表述是：
  - hinted route
    还不能被当作
    “最低风险直接可调用”
    的 private route
  - 下一步必须先恢复
    最小 ABI / hint array
    形状，
    再决定是否二次重试
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/hinted_open_probe_crash_verdict_20260619.json`

### 2026-06-19 hinted-open still crashes after first ABI tightening and is no longer a low-cost route candidate

- 新证据：
  - 主线程继续按
    `_ANEServicesDeviceOpen`
    调用点
    修正
    `_ANEServicesLocateAndOpenHintedDevice`
    最小 probe：
    - `x6`
      不再硬编码为 `1`
    - `x7`
      改成
      `deviceHint/selectedIndex`
      指针
    - `x4/x5`
      按
      DeviceOpen
      原始后两参
      镜像
      对齐
  - 新产物：
    - `benchmark_results/private_ane/ane_services_hinted_open_probe_20260619_v2.json`
- 当前机器确认：
  1. 修正后的
     hinted-open probe
     仍然以
     `139`
     退出
  2. `v1`
     与
     `v2`
     输出文件
     都是
     零字节，
     行为完全一致
  3. 因而当前问题
     不能再归因于
     `x4/x5/x6/x7`
     这一层
     简单 ABI
     猜错
- 因而当前更强的表述是：
  - `_ANEServicesLocateAndOpenHintedDevice`
    还依赖更深的
    hint array /
    controller state /
    receiver state
    语义
  - 它不再是
    当前层的
    低成本突破口，
    当前应正式从
    “最低风险候选”
    降级
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/hinted_open_probe_v2_crash_verdict_20260619.json`

### 2026-06-19 ad-hoc signing with the known ANE entitlements still does not make hinted-open viable

- 新证据：
  - 主线程直接用
    `mps/ANE/experiments/ane_probe_test.entitlements.plist`
    对
    `ane_services_hinted_open_probe`
    副本做
    ad-hoc 重签，
    并确认
    `codesign -d --entitlements :-`
    可见：
    - `com.apple.ane.iokit-user-access`
    - `com.apple.ane.allow-dataChaining-access`
  - 然后运行已签名副本
- 当前机器确认：
  1. 本机上
     ad-hoc 重签
     + 嵌入这两个
     ANE entitlement
     是可执行的
  2. 但签名后的
     hinted-open probe
     仍然没有进入
     可观测的
     `status/device`
     返回路径：
     - exit `137`
     - 输出文件仍为
       `0` 字节
  3. 因而当前 hinted route
     的剩余问题
     不能再被简化成
     “只差 entitlement”
- 因而当前更强的表述是：
  - “外部授权条件”
    对这条 hinted route
    至少不是一个
    立即可用的
    低成本解
  - 当前主线应把
    hinted route
    与
    entitlement 直签分支
    一并降级
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/hinted_open_signed_probe_verdict_20260619.json`

### 2026-06-19 lower-layer mainline should re-enter from `record+0x1b8`, not from `process+0x203fc==2`

- 新证据：
  - 主线程在降级
    open-family /
    hinted-route
    分支后，
    直接对齐三份现有 lower-layer verdict：
    - `process203fc_state2_first_lower_surface_record1b8_verdict_20260619.json`
    - `runtime_harness_record1b8_observability_boundary_verdict_20260619.json`
    - `process203fc_state2_writer_layer_split_verdict_20260619.json`
- 当前机器确认：
  1. `process+0x203fc == 2`
     当前更像
     downstream state contract /
     symptom surface，
     它自身的 visible writer
     已基本排空
  2. `record+0x1b8`
     才是当前最上游的
     first lower surface，
     并且它的 durable author
     已被明确压到
     raw firmware send
     以下
  3. 当前 runtime harness
     无法直接观测
     `record+0x1b8`
     这恰好说明
     下一步应降低 observability surface，
     而不是继续围绕
     `process+0x203fc`
     做静态负向排除
- 因而当前更强的表述是：
  - lower-layer 主线
    的唯一默认下钻入口
    应正式回到
    `record+0x1b8`
  - `process+0x203fc==2`
    保留为 downstream
    state contract，
    不再作为默认 re-entry point
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/lower_layer_reentry_selection_verdict_20260619.json`

### 2026-06-19 mach_msg runtime probe upgraded into a denser lower-side dump path v2

- 新证据：
  - 主线程在不改变 hook 逻辑的前提下，
    只增强
    `mps/ANE/experiments/ane_mach_msg_runtime_probe.c`
    的 observability：
    - 新增
      `CODEX_ANE_MACH_MSG_TRACE_BODY_BYTES`
    - 摘要中加入
      header 之后的
      body hex prefix
    - CSV 新增
      send/reply
      remote/local/voucher/msgh_size
      字段
  - 随后重新编译：
    - `make -C mps/ANE/experiments ane_mach_msg_runtime_probe.dylib`
- 当前机器确认：
  1. 当前 lower-layer
     主线默认入口
     已正式回到
     `record+0x1b8`
  2. 而在现有可复用 runtime probe 面里，
     `ane_mach_msg_runtime_probe.c`
     现在已经足够充当
     一个更高信息密度的
     lower-side dump path v2
  3. 这一步仍未直接观测
     `record+0x1b8`
     本身，
     但它已经把下一轮所需的
     request/reply body
     与 port-level
     差异采样面准备好
- 因而当前更强的表述是：
  - 下一轮不应再做 probe 入口选择
  - 应直接把
    mach_msg runtime probe v2
    挂回一个更贴近
    `ANE_RestoreState raw-send`
    /
    `record+0x1b8`
    边界的 target path
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/mach_msg_probe_v2_entry_upgrade_verdict_20260619.json`

### 2026-06-19 unload-side `device+0x9c0 -> 0x927d410` selected as the default runtime target path

- 新证据：
  - 主线程对齐
    `restore_record_raw_send_boundary_note.md`
    与
    `post_send_replay_boundary_note.md`
    的当前边界结论，
    专门比较：
    - restore-side 5 指令短区间
    - unload-side post-send
      `device+0x9c0 / 0x927d410`
      family
- 当前机器确认：
  1. restore-side
     仍然是最贴近
     `record+0x1b8`
     的静态边界
  2. 但作为
     runtime probe
     挂载对象，
     这条 5 指令短区间
     的增量收益已经很低
  3. unload-side
     在 send 返回后
     立即发散到
     更深的
     `device+0x9c0 / 0x927d410`
     family，
     更有机会暴露
     deeper reply/replay
     state
- 因而当前更强的表述是：
  - restore-side
    保留为
    `record+0x1b8`
    的静态对照边界
  - mach_msg runtime probe v2
    的唯一默认挂载对象
    应改为
    unload-side post-send
    device family
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/lower_runtime_target_path_selection_verdict_20260619.json`

### 2026-06-20 stft-only benchmark is runnable under mach_msg probe v2 but is not the best unload-side target

- 新证据：
  - 主线程把
    `mach_msg runtime probe v2`
    挂到
    `benchmark.private_ane_stft_only_benchmark`
    的
    `1s / 1chunk / no-preload / no-load-cache`
    最小命令上
- 当前机器确认：
  1. 注入后的进程
     没有立即崩溃，
     说明
     probe v2
     至少与这条 harness
     共存
  2. 但在可接受观测窗口内，
     CSV 仍然只有表头，
     benchmark JSON
     也未落成终态结果
  3. 因而这条 harness
     虽然可运行，
     但仍把主要时间预算
     花在更早的 compile/load
     阶段，
     不是当前最有效的
     unload-side runtime target
- 因而当前更强的表述是：
  - `stft_only_benchmark`
    不应成为
    mach_msg probe v2
    的下一默认挂载对象
  - 下一默认候选
    应改成更直接触发
    `ANEBridge.free()`
    /
    `ProgramUnload`
    的 harness，
    例如
    `benchmark.private_ane_bridge_chain_probe`
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/mach_msg_probe_v2_stft_only_target_verdict_20260619.json`

### 2026-06-20 bridge-chain probe is more semantically aligned with `ANEBridge.free()` but still does not yield a short-window mach_msg signal

- 新证据：
  - 主线程把
    `mach_msg runtime probe v2`
    挂到
    `benchmark.private_ane_bridge_chain_probe`
    上，
    试图更直接触发
    `ANEBridge.free()`
    /
    `ProgramUnload`
    路径
- 当前机器确认：
  1. 注入后的
     bridge-chain 进程
     没有立即崩溃
  2. 但在合理短窗口内，
     CSV 仍然只有表头，
     输出 JSON
     也未完成落地
  3. 相比前一轮
     `stft_only`
     target，
     它在短窗口内
     也没有给出更强的
     mach_msg signal
- 因而当前更强的表述是：
  - 当前瓶颈
    已不再是 probe 字段不够，
    而是
    runtime target
    / harness
    本身在进入
    unload-side family
    之前仍过重
  - 下一步应继续缩小
    runnable harness，
    而不是继续扩 probe
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/mach_msg_probe_v2_bridge_chain_target_verdict_20260620.json`

### 2026-06-20 even the single compile/eval/free full-block harness still yields only a header in the short window

- 新证据：
  - 主线程继续把
    `mach_msg runtime probe v2`
    挂到更短的
    `benchmark.private_ane_full_block_probe`
    上
- 当前机器确认：
  1. `full_block_probe`
     的运行结构
     已经是
     单次 compile /
     单次 eval /
     单次 free
  2. 但在短观察窗内，
     CSV 仍然只有表头，
     输出 JSON
     也未落成终态文件
  3. 这说明当前瓶颈
     已不再是
     “再换一个稍短的
     现成 harness”
     就能解决
- 因而当前更强的表述是：
  - 现有 runtime harness
    家族
    在短窗口内
    普遍不足以
    给 mach_msg probe v2
    喂出有效的
    unload-side
    流量
  - 下一步要么找
    真正更接近
    `ane_bridge_free()`
    的极小 harness，
    要么改换
    lower-side
    观测策略
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/mach_msg_probe_v2_full_block_target_verdict_20260620.json`

### 2026-06-20 current runtime harness family is too heavy for short-window unload-side mach_msg observation

- 新证据：
  - 主线程在
    `stft_only`
    /
    `bridge_chain`
    /
    `full_block`
    三条现成 runtime harness
    全部做过最小注入后，
    又复核了
    `private_ane_ffn_authored_sharedblob_compare.py`
    /
    `private_ane_sharedblob_convchain_compare.py`
    /
    `private_ane_real_ffn_mode_compare.py`
    这类近邻脚本的
    compile/eval/free
    结构
- 当前机器确认：
  1. 现有三条已实测 harness
     在短窗口内
     都只产生
     header-only CSV
  2. 剩余几个近邻脚本
     本质上是多 mode compare harness，
     并不比
     `full_block`
     更小、
     更短、
     更直接
  3. 因而当前问题
     已不再是
     “继续换第四个现成 benchmark
     harness”
- 因而当前更强的表述是：
  - 当前 runtime harness
    家族
    在短窗口内
    普遍不足以
    给 mach_msg probe v2
    喂出有效的
    unload-side 流量
  - 下一步应转向
    dedicated free/unload
    micro-harness
    或其他更直接的
    lower-side 观测策略
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/runtime_harness_family_short_window_limit_verdict_20260620.json`

### 2026-06-20 dedicated free/unload micro-harness is now the mainline observation direction

- 新证据：
  - 主线程继续筛查
    `benchmark/`
    里剩余近邻脚本的
    compile/eval/free
    结构，
    包括：
    - `private_ane_ffn_authored_sharedblob_compare.py`
    - `private_ane_sharedblob_convchain_compare.py`
    - `private_ane_real_ffn_mode_compare.py`
    - `private_ane_batch_acceptance_probe.py`
- 当前机器确认：
  1. 这些脚本
     不是更小的
     dedicated free/unload
     harness，
     而是多 mode /
     多 stage /
     acceptance 型
     benchmark harness
  2. 当前已筛过的
     `stft_only`
     /
     `bridge_chain`
     /
     `full_block`
     与这些近邻脚本
     已足够覆盖
     “现成 benchmark harness
     家族”
  3. 当前主线
     若还要在短窗口内
     给
     mach_msg probe v2
     喂出有效 unload-side
     流量，
     已不应再继续找
     现成 benchmark 入口
- 因而当前更强的表述是：
  - 下一步主线
    应正式转向
    dedicated free/unload
    micro-harness
    设计
  - 继续在
    benchmark harness
    家族里轮换
    已属低收益循环
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/dedicated_micro_harness_direction_verdict_20260620.json`

### 2026-06-20 even a dedicated free/unload micro-harness still gives only a header under mach_msg probe v2

- 新证据：
  - 主线程实现并运行了
    `benchmark/private_ane_free_unload_micro_probe.py`
    这条
    dedicated free/unload
    micro-harness
  - 只用
    `compile_only`
    模式，
    目标是尽快到达
    `ANEBridge.free()`
    /
    `ProgramUnload`
- 当前机器确认：
  1. 注入后的
     micro-harness
     没有立即崩溃
  2. 但在短观察窗内，
     `mach_msg` CSV
     仍然只有表头，
     输出 JSON
     也未完成
  3. 这说明当前问题
     已不再能归因于
     “现有 benchmark harness
     家族太重”
- 因而当前更强的表述是：
  - `mach_msg`
    这条 lower-side
    观测路线本身
    很可能抓不到
    目标 unload/replay
    流量
  - 下一步主线
    应改换
    lower-side observability
    策略，
    而不是继续优化
    mach_msg runtime target
- 对应证据文件：
  - `mps/ANE/.ane_runs/json/free_unload_micro_probe_mach_msg_limit_verdict_20260620.json`
### 2026-06-22 public `libswiftXPC` loopback corpus confirmed

- 新证据：
  - `mps/ANE/experiments/xpc_swiftoverlay_loopback_probe.swift`
  - `mps/ANE/.ane_runs/json/xpc_swiftoverlay_loopback_probe_verdict_20260622.json`
  - `mps/ANE/.ane_runs/json/xpc_swiftoverlay_loopback_summary_verdict_20260622.json`
- 当前 machine-local 事实：
  1. 公开 `XPCListener/XPCSession` loopback harness 已能直接抓到系统 encoder 产出的合法 `_CodableBody`
  2. 合法样本已经覆盖：
     - primitive compact family：
       `13 0c ...`
     - keyed struct family：
       `13 0a key value ...`
     - unkeyed array family：
       `13 0b 14 ... 15 13 0c ...`
  3. `Array<Int>` / `Array<String>` 的合法 body 明确证实：
     当前长期主线里隔离出的 `0x14` graph seam 不是“私有乱序自定义格式”，而是 public `libswiftXPC` graph family 的真实成员
  4. 最关键的合法对照样本已经出现：
     `ErrorEnvelope { ipcError: ErrorLeaf(_0: "A") }`
     -> `130a1108000000000000006970634572726f7200140000000015130a1102000000000000005f30000301000000000000004100`
  5. 把 `modelmanager` reply tail 从 offset `9` 开始与这个合法 `ipc_error_struct` 样本对齐后，只剩 4 个字节不同：
     - inner `0x14` node id：`0x00` vs `0x01`
     - 最终字符串的长度/内容：`"A"` vs `DecodingError...`
  6. 合法 public task-like envelope 也已明确：
     - `CancelLike(id: 20) -> 130b0f1400000000000000`
     - `MessageLike(id: 20, payload: ErrorEnvelope, flag: false)`
       -> `130b0f1400000000000000140000000002...`
     - `MessageLike(..., flag: true)`
       -> `130b0f1400000000000000140000000001...`
     这说明 task-like unkeyed envelope 中合法 `UInt64` 首字段 tag 是 `0x0f`
  7. `modelmanager_taskshape_alignment_probe` 已直接证明 field1 是第一 blocker：
     - 合法 public `message_20_false` / `message_20_true`
       喂给 `modelmanager`
       -> `expected ModelXPCRequest ... Invalid number of keys found, expected one.`
     - 只把 baseline field1 tag 从 `0x02` 改成 `0x0f`
       -> 错误立刻从
       `expected UInt64, found bool(false)`
       推进到
       `Found dangling container in buffer`
     - 但如果整段替进更长的 public prefix，
       则会 overshoot 到
       `Cannot read a valid tag from buffer`
  8. `createSession` payload 已真正推进到字段级：
     - 顶层 key `createSession` 正确
     - associated-value wrapper `_0` 正确
     - `CreateSessionRequest.metadata` 字段正确
     - 当前已恢复出的 `Session.Metadata` 字段顺序与类型提示：
       1. `assetBundleURI`：URL-like，不接受 plain String
       2. `useCaseID`：String-like
       3. `onBehalfOfPID`：`Int32`
       4. `parentOfOnBehalfOfPID`：`Int`
       5. `loggingIdentifier`：String-like
       6. `id`：UUID string
       7. `sessionSetID`：UUID string
       8. `inferenceInterfaceVersion`：已确认为 `ModelManagerServices.Version{major,minor,patch}`
          - 标量 `Int(1)`：`singleValueGraphEncodingNodeID`
          - 二字段 `{major,minor}`：`Key 'patch' not found`
          - 三字段 `{major,minor,patch}`：稳定推进到 `assetBundleNotFound`
      - 新增 semantic gate：
        - raw `file://` 指向本机现存 UAF 目录并不能满足 `assetBundleURI`
        - 已证伪 family：
          1. `Translation_Assets/*.asset`
          2. `Translation_Assets/*.asset/AssetData`
          3. `Siri_UnderstandingNLOverrides/*.asset`
          4. `Siri_PlatformAssets/*.asset`
          5. `Siri_PlatformAssets/*.asset/AssetData`
          6. `Siri_PlatformAssets/*.asset/AssetData/<version>`
          7. `~/Library/Assistant/LLMCache/NLRouter`
          8. `UnifiedAssetFramework history` 中真实 locked 资产的 `localContentURL` 根：
             - `SummarizationKitConfiguration/*.asset/AssetData`
             - `Siri_Understanding/*.asset/AssetData`
             - `Siri_UnderstandingNLOverrides/*.asset/AssetData`
          9. current live asset 的 file-level 入口候选：
             - `.asset/Info.plist`
             - `AssetData/metadata.plist`
             - `AssetData/Configuration.plist`
             - `AssetData/version.yaml`
             - `AssetData/SummarizationOverrideRules.pbtxt`
             - `AssetData/regex.jsonl`
             - `AssetData/config.json`
          10. secure-mobile-asset file path family：
             - `purpose_auto/*.xml` manifest
             - `SecureAssetData/`
             - `SecureAssetData/SecureMobileAsset-Info.plist`
             - `SecureAssetData/BuildManifest.plist`
        - 这些候选全部仍回到同一个 `assetBundleNotFound`
      - 新增 manager-facing upstream boundary：
      - `ModelManagerServices.ModelXPCRequest.HoldAssetBundle(assetBundleIdentifier: String)`
      - `ModelManagerServices.ModelXPCRequest.LoadAssetBundle(assetBundleIdentifier: String, dynamicMode: Bool)`
        - SDK `tbd` 与保守 IDA reconciliation 已对齐：`assetBundleURI: URL` 不属于这两个 request 本体
        这两个 request 在本机对以下 identifier family 全部稳定回
        `notSupportedOnExternalBuild`
        ，并且与 identifier 内容无关：
          1. dummy string
          2. UAF `assetSpecifier`
          3. UAF `assetID` hash
          4. `localContentURL` path string
        这说明 manager-facing string identifier surface 先撞 product-build gate，尚未进入 bundle identifier 语义判定
      - `alreadyLockedInferenceProvider`
        尚未被真正触达；当前 bundle semantic gate 先于它报错
- 结论：
  - `modelmanager` 的 field2 keyed tail 已不再是未知语法，而是高度接近合法 public `ipcError -> _0 -> string` payload
  - 当前未知量已经重新压缩回：
    1. field1 的 `0x02` vs 合法 task-like `0x0f` 首字段 tag
    2. 最外层额外前导 `0x15`
    3. inner node-id / 最终错误字符串 payload 的差异
    4. `assetBundleURI` 所在的上层 Swift carrier（而不是 `load/hold asset bundle` 的 string identifier 面）
    5. `createSession` 当前 `assetBundleNotFound` / `modelCatalogError` 是否其实在表达“缺少 asset-ID / Model Catalog state”，以及 `modelcatalog:` URL 形状 / query key / version / resource-membership 这些因素还缺哪一层
    6. `requiredAssetIDs` / `PrewarmSession` / `FetchAssetsRequest` / `FetchDisabledUseCasesRequest` / `FetchModelInstance` 这些更上游语义面
    7. 越过 bundle gate 之后的 `customAssetConfigurations` / `alreadyLockedInferenceProvider`
- 下一步：
  - 不再广泛搜索 field2 closure grammar
  - 直接以合法 `ipc_error_struct` / `ipc_error_nested_dict` / `CancelLike` / `MessageLike` 样本为模板，主攻 field1 与最外层 wrapper 差异
  - 并继续沿 `createSession` 这条已打通的 payload 主线，优先恢复真正持有 `assetBundleURI` 的上层 carrier与 asset-ID/catalog 语义；`ModelCatalog` 目前只作为 SDK 语义来源而非现成宿主入口，宿主 runtime 虽能 `dlopen` 并拿到 `MCResourceInformation`/`MCResourceStatus`，但它们仅暴露 `NSSecureCoding` bridge 方法，没有直接查询 surface；`ModelCatalog.Index(sideloadURL:)` 这类最简单的高层 Swift constructor 也仍 unresolved；`PrewarmSession` 与 `FetchModelInstance` 则可作为已越过 UUID/wire gate 但当前仍停在 `internalError` 的旁证面；failed `createSession` 无论停在 `assetBundleNotFound` 还是 `modelCatalogError`，当前都不会留下可观察 session state；`FetchAssetsRequest` 与 `FetchDisabledUseCasesRequest` 现阶段都只证明了 entitlement gate；`customAssetConfigurations` 缺省/空数组差异也已压掉；当前新的最高价值 seam 是 `modelCatalogError`，而且它已经被证实对 `modelcatalog:` 的 URL 形状敏感；只有越过当前 catalog gate 后，再继续看 `alreadyLockedInferenceProvider`

### 2026-06-22 `0x14` graph identity seam confirmed

- 新证据：
  - `mps/ANE/experiments/modelmanager_taskcancellable_u14_outer_tail_probe.py`
  - `mps/ANE/.ane_runs/csv/modelmanager_taskcancellable_u14_outer_tail_probe_20260622.csv`
  - `mps/ANE/.ane_runs/json/modelmanager_taskcancellable_u14_outer_tail_probe_verdict_20260622.json`
  - `mps/ANE/.ane_runs/json/xpc_swiftoverlay_graph_error_cluster_verdict_20260622.json`
  - `mps/ANE/experiments/xpc_swiftoverlay_runtime_layout_probe.py`
  - `mps/ANE/.ane_runs/json/xpc_swiftoverlay_runtime_layout_verdict_20260622.json`
- 当前 machine-local 事实：
  1. 复用 baseline
     `body[3:]`
     这条以第二个
     `0x14`
     开头的尾巴时，field1 的
     `0x14`
     不只是 container family，而且其 4-byte field 会直接进入 duplicate-node seam：
     - 第一容器
       `u32=0`
       + `body[3:]`
       -> `Duplicate reference to node #0`
     - 第一容器
       `u32=1`
       + `body[3:]`
       -> `Duplicate reference to node #1`
     - 第一容器
       `u32>=2`
       + `body[3:]`
       -> `Insufficient container in buffer`
  2. 把第二个
     `0x14`
     显式 author 出来后，duplicate seam 变得可控且可复现：
     - `u32a=1, u32b=1`
       -> `Duplicate reference to node #1`
     - `u32a=2, u32b=2`
       -> `Duplicate reference to node #2`
     - `u32a=3, u32b=3`
       -> `Duplicate reference to node #3`
     - `u32a=4, u32b=4`
       -> `Duplicate reference to node #4`
     - `u32a=7, u32b=7`
       -> `Duplicate reference to node #7`
     - 当
       `u32a != u32b`
       时，错误会回落到
       `Found dangling container in buffer`
       或
       `Insufficient container in buffer`
  3. 这说明 `0x14` 后的 4-byte field 已经被实证为 graph/node identity bookkeeping，而不是单纯 child count
  4. shared-cache 的
     `XPC_swiftoverlay`
     静态错误簇进一步给出同一 graph family 的名字面：
     - `Missing container metadata for _SingleValueDecodingContainer`
     - `Missing container metadata for _UnkeyedDecodingContainer`
     - `Container is at end.`
     - `Duplicate reference to node #`
     - `Found dangling container in buffer`
     - `Insufficient container in buffer`
     但未发现直接命名的
     `node table` /
     `backreference` /
     `footer`
     字符串
  5. `.containerMetadata`
     本身不是单独的解法：
     - `0x14 + nil child + 13 0a`
       -> `Insufficient container in buffer`
     - `13 0a + 最小 stringA`
       -> 仍是 `Insufficient`
     - `13 0a + ipcError string 片段`
       -> 仍是 `Insufficient`
     - `13 0a + 去冲突的第二个 0x14(u32=2)`
       -> `Found dangling container in buffer`
  6. 在去冲突双
     `0x14(u32a=1,u32b=2)`
     骨架里，第二个 node 的首 tag scan 已把 closure 入口进一步收紧：
     - 只有 `0x15`
       仍保持结构合法，并落到
       `Found dangling container in buffer`
     - `0x03/0x11`
       -> string-family error
     - `0x12`
       -> `Bad index for XPC object: 135334419`
     - `0x13`
       -> `Found bad value for .containerMetadata: 19`
     - `0x00/0x01/0x02/0x10`
       -> `Duplicate reference to node #1`
  7. 即便固定
     `0x15`
     这条唯一结构合法 family，继续最小 author：
     - `15`
     - `15 13 0a`
     - `15 13 0a + stringA`
     - `15 13 0a + "_0"`
     - `15 13 0a + key10`
     以及 baseline tail 的所有结构性前缀截断
     （`1/3/4/12/21/26/29/30/38/41/42/50/154` 字节）
     全都只会稳定落回
     `Found dangling container in buffer`
  8. `XPC_swiftoverlay`
     的静态 keyed/unkeyed 终止条件现已明确：
     - keyed family：
       `Invalid encoding graph: Failed to find key`
       与
       `Invalid encoding graph:: Found key, expected value`
     - unkeyed family：
       `Container is at end.`
     - graph parser 还要求
       `expected odd number`
       的元素结构，说明 closure 更像 tagged key/value triad，而不是简单 footer
  9. “语义更像 baseline 的 keyed skeleton” 也已排除：
     - `ipcError -> third 0x14 -> "_0"` 但 inner key 无 value
     - `ipcError -> third 0x14 -> value 无 key`
     - `ipcError -> third 0x14 -> "_0":"A"` 最小 pair
     - outer `ipcError` key 无 value
     - outer value 无 key
     全部都只会稳定落回
     `Found dangling container in buffer`
  10. runtime class layout 已明确 keyed/unkeyed 的内部 shape：
      - `XPC.TopLevelGraphEncodingNode` 只有 `wrappedNode`
      - `XPC._KeyedGraphEncodingNode` 有 `keyToIndex` 与 `values`
      - `XPC.UnkeyedGraphEncodingNode` 只有 `values`
      - `XPC.DecodedContainer` 有 `decodedValues`
      它们的 runtime image path 都是
      `/usr/lib/swift/libswiftXPC.dylib`
  11. lldb 对 `libswiftXPC.dylib` 的符号面也已经收窄到 3 个核心入口：
      - `XPC.encodeToEncodingContainer<Encodable>(...) -> XPC.TopLevelGraphEncodingNode`
      - `XPC.decodeFromEncodingContainer<Decodable>(...)`
      - `XPC._KeyedGraphEncodingNode._valueIndex(forKey: XPC.EncodingGraph.Key) -> Optional<Int>`
      另有
      `Dictionary<UInt32, XPC.DecodedContainer>`
      specialization 命中，说明
      `decodedValues`
      更像字典而不是数组
- 结论：
  - `0x14` seam 已经从“counted container”进一步收紧成“graph identity + container closure”问题
  - 当前不是缺一个 raw leaf，也不是缺一个显然的 child-count；连裸 `.containerMetadata`、最小 `0x15` family、baseline tail 的任何结构前缀、以及显式 keyed skeleton 都已排除为单独解法，剩余问题只能是更深的 forward graph validator closure family
  - keyed path 现在更像 `keyToIndex + values` 双结构，而不是简单的顺序 key/value 流；unkeyed path 则更像纯 `values` exhaustion
  - 下一轮最值得围绕的静态入口已收窄到 `encodeToEncodingContainer` / `decodeFromEncodingContainer` / `_valueIndex(forKey:)`
  - “显式 footer/backreference table” 目前没有静态证据，只能作为弱假设
- 下一步：
  - 固定一个不 duplicate 的双
    `0x14`
    骨架（例如
    `u32a=1, u32b=2`
    ）
  - 继续最小化 author
    keyed termination /
    unkeyed exhaustion /
    next-field 片段
  - 目标是把错误从
    `Dangling/Insufficient`
    推到
    `Failed to find key` /
    `Found key, expected value` /
    `Container is at end.`
    中的任意一个新 family

### 2026-06-22 `0x14` counted-container seam confirmed

- 新证据：
  - `mps/ANE/experiments/modelmanager_taskcancellable_u14_container_probe.py`
  - `mps/ANE/.ane_runs/body/modelmanager_taskcancellable_typemismatch_reply_body_20260622.bin`
  - `mps/ANE/.ane_runs/csv/modelmanager_taskcancellable_u14_container_probe_20260622.csv`
  - `mps/ANE/.ane_runs/json/modelmanager_taskcancellable_u14_container_probe_verdict_20260622.json`
- 当前 machine-local 事实：
  1. `TaskCancellableMessage<ModelXPCRequest>` field1 的 `0x14` 分支在保留原 trailing bytes 时，不像 direct UInt64：
     - `u32=0` -> `Container size mismatch for SingleValueDecodingContainer4OptionalPrimitive`
     - `u32=1/2/20` -> `Found dangling container in buffer`
  2. 在 `u32=1` 下，offset `7` 自身表现为 nested tag boundary：
     - `0x03/0x11` -> `Cannot read a valid string from buffer`
     - `0x12` -> `Bad index for XPC object: 285872917`
     - `0x13` -> `Found bad value for .containerMetadata: 21`
     - `0x00/0x01/0x02/0x10/0x15` -> `Found dangling container in buffer`
     - 其余大部分 `0x04..0x1f` tag -> `Cannot read a valid tag from buffer`
  3. 当 offset `7` 与 offset `8` 连续放一字节 leaf family 时，bytes `3..6` 的 `u32` 语义是结构性的：
     - `u32=0` -> `Insufficient container in buffer`
     - `u32=1` -> `Duplicate reference to node #1`
     - `u32>=2` -> `Found dangling container in buffer`
  4. 只 hand-author 一个极小 `0x14 + u32=1 + single child` body（例如 `nil/bool/stringA`），不继承旧 `ipcError` reply tail，也仍只会得到 `Insufficient container in buffer`
  5. shared-cache 静态表面与 runtime probe 对齐：
     - `AAAFoundationSwift` 字符串表里存在
       `SingleValueDecodingContainer4OptionalPrimitive`
       与
       `Container size mismatch for SingleValueDecodingContainer4OptionalPrimitive`
     - 没有独立
       `OptionalPrimitive`
       类型名，也没有 `0x14` 对应 5-byte / 8-byte 头的静态证据
- 结论：
  - `0x14` 已经从“direct UInt64 候选”降级为“counted nested container family”
  - field1 的真实恢复问题不再是“猜一个整数编码”，而是“补齐单 child 容器闭合后所需的最小 outer bookkeeping”
  - 这也解释了为什么简单的 `0x14 + u32 + raw leaf` author 永远推进不到 `ModelXPCRequest`：当前缺的是 container/graph closure，而不是 leaf tag family 本身
- 下一步：
  - 固定 `u32=1 + single child`，去掉 inherited `ipcError` reply payload，author 最小 post-container outer tail，观察能否把错误推进到下一 outer field
## 2026-06-23 time-axis attention_pre route-candidate audit
- Evidence: `mps/ANE/.ane_runs/json/time_attention_pre_route_candidate_audit_20260623.json` and CSV peer.
- Profiler source: `mps/ANE/.ane_runs/json/current_best_component_bottleneck_ledger_20260623.json`.
- Current-best component facts remain: transformer `24.871128999977373s`, transformer eval `19.867204998852685s`, transformer compile `1.9713062929804437s`, time-axis eval `13.97083224792732s`, `time.pre.eval_sec=9.508778334013186s`, `time.axis_pack_sec=2.45342729089316s`, native max child RSS `1660.547MB`.
- Closed candidates: current manual-MIL qchunk resweep (`q240` local minimum, `q480` slower/higher RSS, others compile-fail), generic SDPA/public attention, forced q240 all layers, two-input gate, materialized pre-to-gate boundary, `surface_handoff_gate_ffn`, retained transformer handles/runtime clone cache, and IOSurface superbuffer.
- Verdict: `confirmed_no_current_host_visible_memory_neutral_attention_pre_candidate`.
- Root cause update: the remaining speed gap is segmented transformer execution, especially time-axis `attention_pre` dispatch/materialization/layout movement, not a single load-cache miss or untuned qchunk.
- Next target: recover or falsify a non-IOSurface lower-layer transformer carrier/layout contract that can reduce time-axis `attention_pre` segment dispatch/materialization without retained handles or RSS growth.
## 2026-06-24 exact q240 MIL validator correlation

- Artifact: `mps/ANE/.ane_runs/json/exact_q240_mil_validator_correlation_20260624.json`
  and CSV peer `mps/ANE/.ane_runs/csv/exact_q240_mil_validator_correlation_20260624.csv`.
- Verdict: `inconclusive_need_validateunits_or_compiler_trace`.
- Confirmed facts:
  - Exact q240 runtime failure remains localized to
    `ANECCompile(...CFEEBA68...F8815657...E3B0C442...) FAILED:
    err=(InvalidMILProgram)`, not cache lookup or wrapper synthesis.
  - Exact q240 MIL has `106` ops versus same-weight compiled alias `68`.
  - Delta exact minus alias is `slice_by_index +4`, `matmul +6`,
    `softmax +3`, `concat +1`, `add +3`, `mul +3`, `const +18`.
  - Exact q240 attention splits query into four `[62,8,240,64]` tiles,
    computes four `[62,8,240,960]` score/softmax branches and four
    `[62,8,240,64]` value branches, then concatenates to `[62,8,960,64]`.
  - Follow-up reverse evidence resolves the q240 concat axis as `cax = int32(2)`;
    this is a sequence/tile reconstruction concat, not the same full-attention
    body used by the compiled alias.
  - The compiled same-weight alias uses one full `[62,8,960,960]`
    score/softmax and `[62,8,960,64]` output path, with no final concat.
  - Local ANECompiler exports validators for concat, dynamic slice, matrix
    multiply, softmax, SDPA, reshape, transpose, and gather; strings include
    concat-axis/type/lowering failures, dynamic-slice parse/index failures,
    softmax dimension failures, matrix-multiply failures, dynamic-shape
    unsupported paths, and `InvalidMILProgram`.
  - Later IDA decompilation downgraded the concat-only hypothesis:
    `ZinConcatLayer::ValidateSemantics_Impl` (`0x222eeedb0`) checks dimension
    matching except on the concat axis and does not prove a tiled-concat block.
  - IDA decompilation also found a softmax architecture gate at `0x223070eec`
    (`Softmax is not supported by this ANE architecture`), but the compiled
    same-weight alias already contains one softmax, so this is not yet a
    differential explanation unless the repeated/tiled softmax context changes
    ANE residency.
  - `ValidateUnits` (`0x2240a3258`) and `ValidateDerivedMILProgram`
    (`0x2240a29c8`) are now the strongest next choke points because they can
    mark failed units non-ANE-resident across the expanded q240 body.
- Current interpretation:
  - The q240-only tiled attention body is now the narrow failure region.
  - The q240-only tiled body remains the narrowed failure region, but no single
    per-layer validator has been proven as the rejecting check.
  - The final `concat(interleave=..., axis=2)` is still a differential candidate
    because it exists only in exact q240, but it is no longer the primary
    supported explanation after IDA concat decompilation.
  - Current evidence does not prove the exact failing validator/check; do not
    declare `confirmed_invalid_q240_mil_op_shape` or a compiler dead end yet.
- Next required evidence:
  - Decompile or trace `ValidateUnits` (`0x2240a3258`),
    `ValidateDerivedMILProgram` (`0x2240a29c8`), and the softmax validation
    context to identify the first non-ANE-resident/rejected q240 op, or add
    minimal runtime compiler-validation instrumentation that records it.
## 2026-06-24 ValidateUnits static probe

- Artifact: `mps/ANE/.ane_runs/json/exact_q240_validateunits_static_probe_20260624.json`
  and CSV peer `mps/ANE/.ane_runs/csv/exact_q240_validateunits_static_probe_20260624.csv`.
- Verdict: `inconclusive_need_first_invalid_op_trace`.
- IDA MCP status:
  - `idb_list` showed one ANECompiler worker with an empty `session_id`
    (`pid 17993`), which could not be used by MCP calls.
  - The orphaned worker ignored normal `kill`, then was force-killed.
  - Named `idb_open` retries returned `Remote end closed connection without
    response`, so this loop degraded to local `nm` / `strings` / `objdump`.
- Static validation facts:
  - `ValidateOpList`: `0x22409c8bc`.
  - `ValidateDerivedMILProgram`: `0x2240a29c8`.
  - `ValidateUnits`: `0x2240a3258`.
  - `MarkAllOpsAsInvalid`: `0x2240a6b54` and `0x2240a28a4`.
  - `ZinIrSoftmaxUnit::ValidateForDynamicShapes`: `0x222f94330`.
  - `ZinSoftmaxLayer::ValidateSemantics_Impl`: `0x223070eec`.
- Disassembly facts:
  - `ZinIrSoftmaxUnit::ValidateForDynamicShapes` is `mov w0, #0; ret`, so
    softmax dynamic-shape validation itself is not the q240 blocker.
  - `ZinSoftmaxLayer::ValidateSemantics_Impl` checks HAL byte `[x2+0x815]`
    before input/output checks; this is the softmax architecture gate, but the
    same-weight compiled alias already contains one softmax, so it is not yet a
    differential explanation.
  - `ValidateDerivedMILProgram` builds a `ZinIrContext`, calls
    `ValidateMemoryFootprintLiveIO` helpers and `ValidateLiveIOMemoryFootprint`,
    and can call `MarkAllOpsAsInvalid`.
  - `MarkAllOpsAsInvalid` iterates MIL operations, calls
    `RetrieveOpIdentifier`, obtains operation names/debug strings, and inserts
    invalid `ValidateEntry` records with a supplied reason.
- High-signal compiler strings:
  - `Dynamic Shapes: One or more network operations are not ANE-resident -
    Marking all operations as non ANE-resident.`
  - `MaxLiveInLiveOutExceeded`
  - `Error: the live io tensor memory footprint (%zd bytes) exceeds the bss
    limit (%lld bytes)`
  - `The live IO size exceeds BSS limit!`
  - `Cannot validate the MIL program from MIL-ANEF validation interface!`
- Current interpretation:
  - The likely actionable missing evidence is not another per-layer validator
    guess; it is the exact `ValidateEntry` invalid reason map for exact q240.
  - The next minimal probe should capture the first invalid op identifier and
    reason produced around `ValidateUnits` / `MarkAllOpsAsInvalid`, then map it
    back to exact q240 `model.mil`.
## 2026-06-24 exact q240 deep NSError payload probe

- Artifact: `mps/ANE/.ane_runs/json/exact_q240_deep_error_detail_probe_20260624.json`
  and CSV peer `mps/ANE/.ane_runs/csv/exact_q240_deep_error_detail_probe_20260624.csv`.
- Probe log: `benchmark_results/private_ane/exact_q240_deep_error_detail_probe_20260624.log`.
- Verdict: `confirmed_nserror_payload_lacks_validateentry_reason`.
- Code changes:
  - `mps/maderix_ANE/bridge/ane_bridge.m` now recursively captures fixed-buffer
    `NSError` details and records direct `compileWithQoS:options:error:` failure
    details in the bridge profile.
  - `benchmark/private_ane_real_attention_probe.py` now includes
    `last_bridge_profile` JSON in `RuntimeError` on compile failure.
- Minimal probe command:
  - `/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --compare bridge-env --layers 1 --chunks 1 --q-chunk 240 --cache-tmpdir benchmark_results/private_ane/ane_tmp_loadcache --probe-handle-scope pre --probe-stop-after-axis time --probe-stop-after-layer 1 --bridge-env ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT=1 --bridge-env PYMSS_PRIVATE_ANE_TILED_TIME_ATTENTION_PRE=1 --bridge-env PYMSS_PRIVATE_ANE_TILED_TIME_ATTENTION_PRE_Q_CHUNK=240 --out benchmark_results/private_ane/exact_q240_deep_error_detail_probe_20260624.json`
- Observed profile:
  - Return code: `1`.
  - Route: `compile`.
  - Identifier: `CFEEBA68..._F8815657..._E3B0C442...`.
  - `compile_qos_sec`: about `0.0079s`; `total_sec`: about `0.0090s`.
  - Top-level `NSError.userInfo` keys: `NSLocalizedDescription`,
    `NSUnderlyingError`.
  - Underlying `NSError.userInfo` keys: `NSLocalizedDescription`.
  - No `ValidateEntry`, `validationErrors`, op identifier, rejected op name, or
    reason map is surfaced through `NSError`.
- Current interpretation:
  - The public/runtime `NSError` boundary is exhausted for exact q240 invalid-op
    attribution.
  - The next evidence must come from below the NSError boundary: hook/patch
    `MarkAllOpsAsInvalid`, `ValidateUnits`, or `RetrieveOpIdentifier`, or build
    a compiler-service probe that can dump the `ValidateEntry` map before it is
    collapsed to `InvalidMILProgram`.
## 2026-06-24 below-NSError boundary probe

- Artifact: `mps/ANE/.ane_runs/json/exact_q240_below_nserror_boundary_probe_20260624.json`
  and CSV peer `mps/ANE/.ane_runs/csv/exact_q240_below_nserror_boundary_probe_20260624.csv`.
- Verdict: `blocked_need_service_debug_privilege_for_validateentry_map`.
- Evidence:
  - `benchmark_results/private_ane/exact_q240_dyld_visibility_probe_20260624.log`
    shows the Python process loads `ANECompiler.framework`, `MIL.framework`,
    `AppleNeuralEngine.framework`, and `ANEServices.framework`.
  - Frida controller/script artifacts:
    `mps/ANE/.ane_runs/frida/run_exact_q240_validateentry_hook.py`,
    `mps/ANE/.ane_runs/frida/exact_q240_validateentry_hook.js`, and
    `mps/ANE/.ane_runs/frida/run_q240_preload_anecompiler.py`.
  - `benchmark_results/private_ane/exact_q240_frida_validateentry_probe_20260624.log`
    shows the Python process hook attaches to `ANECompiler`, but control hooks
    for `_ANECCompile`, `ZinAssertImpl`, and both `MarkAllOpsAsInvalid`
    overloads do not fire during the exact q240 failure.
  - `ANECompilerService` is visible as PID `76891`, but current-user Frida
    attach fails: `unable to access process with pid 76891 from the current user
    account`.
  - `benchmark_results/private_ane/anecompiler_service_log_probe_20260624.log`
    contains zero validation/error-detail lines from unified logs.
- Conclusion:
  - Validation detail is below the client process and below the public
    `NSError` boundary, inside `ANECompilerService.xpc`.
  - Capturing the exact `ValidateEntry` map now requires service-side debug
    privilege, such as SIP debug relaxation plus `lldb`/Frida/root attach, or
    an equivalent privileged service instrumentation path.
  - Without that external privilege, continuing to expand bridge/userInfo
    capture cannot identify the first rejected exact-q240 op.
- Impact on optimization plan:
  - Exact q240 `model.mil` remains a compiler-blocked body.
  - Next memory-neutral progress should pivot to compiler-accepted MIL-body
    alternatives or route-policy changes that avoid this invalid body, while
    preserving correctness and checking RSS/wired/swap impact.

## 2026-06-24 materializer control boundary package
- Script: `benchmark/private_ane_materializer_control_blocker_package.py`.
- Artifact: `mps/ANE/.ane_runs/json/materializer_control_boundary_package_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/materializer_control_boundary_package_20260624.csv`.
- Verdict: `blocked_no_safe_materializer_control_exposed`.
- Result:
  - `safe_memory_neutral_control_exposed=false`.
  - Rejected controls: selector-3 program create, selector-8 program create instance, DART resource remap, IOSurface materializer contract, and host-visible MIL/layout contract.
  - Route-profile hotspot context remains 24 transformer rows, 24 load-cache hits, 0 load-cache misses, 0 bridge fast-load hits, estimated 96 `attention_pre` selector-2 requests, `attention_pre_eval_sec=12.588885625009425`, `axis_pack_sec=3.34072536896565`, and `segment_wall_sec=29.116179916920373`.
- Conclusion:
  - Current host-visible MIL/layout/materializer controls and selector-3/selector-8 create-instance/materializer evidence do not expose a supported memory-neutral speed knob.
  - Do not implement selector-8 remap bypass, DART remap suppression, or IOSurface contract override from current evidence.
  - Remaining acceleration evidence must come from below `ProgramReMap` / `dartMapResources` / `createANESurface`, or from a compiler-accepted MIL/body/layout contract that reduces `attention_pre` request count without retained memory growth.
- Next:
  - Attribute lower selector-2 lifecycle time: firmware wait/compute, IOProcessor completion, and host-side dispatch/synchronization using existing traces or a minimal read-only observation path.

## 2026-06-24 selector-2 lower timing attribution package
- Script: `benchmark/private_ane_selector2_timing_attribution_package.py`.
- Artifact: `mps/ANE/.ane_runs/json/selector2_lower_timing_attribution_package_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/selector2_lower_timing_attribution_package_20260624.csv`.
- Verdict: `confirmed_selector2_completion_low_utilization_opaque`.
- Result:
  - Host write/read/pack/setup is not dominant for accepted time layer0: `ane_pre_eval_sec=0.7698414579790551`, `ane_pre_write_sec=0.01106487397919409`, `ane_pre_read_sec=0.026174624013947323`, `axis_pack_sec=0.05874783397302963`.
  - User-space eval subphase profile is not available: the current bridge exposes coarse write/eval/read only, and `ane_bridge_eval` is a monolithic blocking call.
  - Selector-2 submit path is mapped to `ANE_ProgramSendRequest` / `IOConnectCallAsyncMethod(selector=2)` and is not the dominant bucket.
  - `updateRequestFWCommand` is semantically required lower materialization; failure aborts send path, so it is not a safe bypass target from current evidence.
  - Dominant remaining bucket is firmware wait or compute body; accepted time-axis `attention_pre` reaches about `0.20732433083177246 TFLOPS`, `1.1356503660811375%` of measured ANE FP16 peak.
- Conclusion:
  - Current root cause attribution is now: low-utilization opaque selector-2 completion path, not top-level load/cache, host write/read/pack, selector-8 materializer, or IOSurface remap.
  - Remaining uncertainty is the split between firmware wait, compute body, IOProcessor completion, and kernel callback wake.
- Next:
  - Inventory existing event traces and bridge source to decide whether zero-retention eval subphase signposts can be added safely; otherwise package the exact privileged instrumentation requirement and return to MIL/body request-count reduction.

## 2026-06-24 eval signpost feasibility and bridge patch
- Script: `benchmark/private_ane_eval_signpost_feasibility_package.py`.
- Artifact: `mps/ANE/.ane_runs/json/eval_signpost_feasibility_package_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/eval_signpost_feasibility_package_20260624.csv`.
- Code changed: `mps/maderix_ANE/bridge/ane_bridge.m`; rebuilt `mps/maderix_ANE/bridge/libane_bridge.dylib` with `make -C mps/maderix_ANE/bridge`.
- Verdict: `confirmed_zero_retention_bridge_eval_setup_send_signposts_added`.
- Result:
  - Added eval profile fields: `setup_sec`, `send_sec`, `eval_client_setup_sec`, `eval_client_send_sec`, `eval_direct_process_setup_sec`, `eval_direct_process_send_sec`, `eval_model_setup_sec`, `eval_model_send_sec`.
  - Retained-memory change: none; implementation uses stack-local scalar timing values around existing ObjC eval calls.
  - Non-inference validation: `ane_bridge_eval(NULL)` through ctypes returns false and emits parseable profile JSON containing the new fields with `route=eval_invalid_handle` and `send_sec=0.0`.
  - Package validation: `required_source_markers_present=true`, 3 CSV seam rows.
- Conclusion:
  - Zero-retention bridge setup/send signposts are safe and implemented.
  - These fields split only bridge-side setup from the blocking ObjC eval call; `send_sec` still includes selector-2 completion, IOProcessor/firmware wait, and compute body.
  - Do not claim firmware wait versus compute split from this patch alone.
- Next:
  - Run a minimal accepted `attention_pre` eval profile that captures the new fields on test_clean-derived shapes, then decide whether to return to MIL/body request-count reduction or require privileged selector-2/IOProcessor instrumentation.

## 2026-06-24 eval signpost capture on accepted integrated path
- Script: `benchmark/private_ane_eval_signpost_capture_package.py`.
- Raw profile: `mps/ANE/.ane_runs/json/integrated_eval_signpost_capture_20260624.raw.json`.
- Artifact: `mps/ANE/.ane_runs/json/eval_signpost_capture_package_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/eval_signpost_capture_package_20260624.csv`.
- Command: `ANE_BRIDGE_SKIP_SOURCE_WRITE_ON_CACHE_HIT=1 /Users/baicai1145/miniconda3/bin/python benchmark/private_ane_transformer_layerwise_compare.py --compare tiled --layers 1 --chunks 1 --q-chunk 240 --out mps/ANE/.ane_runs/json/integrated_eval_signpost_capture_20260624.raw.json`.
- Verdict: `confirmed_eval_send_sec_contains_attention_pre_eval_bucket`.
- Result:
  - Standalone `attention_pre` micro-profile was not an accepted seam for the tested shape and failed `InvalidMILProgram`; integrated transformer path was used instead.
  - Current variant: `ane_pre_eval_sec=0.25607962504727766`, `ane_pre_native_setup_sec=0.000001375`, `ane_pre_native_send_sec=0.2559475`, `maxrss_mb=1213.3125`.
  - Tiled q240 variant: `ane_pre_eval_sec=0.2514954159851186`, `ane_pre_native_setup_sec=0.0000016669999999999999`, `ane_pre_native_send_sec=0.251380583`, `maxrss_mb=1245.3125`.
  - Correctness for the integrated compare remained exact: `max_abs=0.0`, `mean_abs=0.0`, `p99_abs=0.0`.
- Conclusion:
  - Bridge-visible eval setup is microseconds and not a performance target.
  - `send_sec` accounts for more than 99% of `ane_pre_eval_sec`, so the bottleneck is the opaque selector-2 completion bucket.
  - Further splitting of `send_sec` requires privileged selector-2/IOProcessor instrumentation; without that capability, the memory-neutral path returns to MIL/body/request-count reduction for `attention_pre`.
- Next:
  - Search for compiler-accepted MIL/body/request-count changes that reduce `attention_pre` selector-2 sends or improve accepted body utilization without retained memory growth.

## 2026-06-24 fuse/body candidate verdict package
- Script: `benchmark/private_ane_fuse_candidate_verdict_package.py`.
- Harness change: `benchmark/private_ane_transformer_layerwise_compare.py` now exposes candidate-only flags `--candidate-fuse-gate-ffn`, `--candidate-no-fuse-residual`, and `--candidate-gelu-mode` for minimal integrated probes.
- Artifact: `mps/ANE/.ane_runs/json/fuse_candidate_verdict_package_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/fuse_candidate_verdict_package_20260624.csv`.
- Verdict: `blocked_no_promotable_memory_neutral_fuse_body_candidate`.
- Result:
  - `fuse_gate_ffn`: exact (`max_abs=0.0`) but slower in one-layer integrated probe, `wall_delta_sec=3.256498041038867`, `wall_delta_pct=74.35996383226407`.
  - `fuse_gate_ffn_no_residual`: rejected for correctness delta, `max_abs=0.0546875`, `mean_abs=0.0004886302631348372`, `p99_abs=0.00390625`, `checksum_delta=-10.703125`.
  - `gelu_tanh`: exact (`max_abs=0.0`) but slower, `wall_delta_sec=6.622177083045244`, `wall_delta_pct=90.41151064020471`.
  - `promotable_candidate_count=0`.
- Conclusion:
  - The remaining unclosed host-visible fuse/body toggles are not viable memory-neutral speedups under current minimal integrated evidence.
  - Request-count reduction for gate+ffn can compile, but it does not improve wall time in the accepted one-layer probe; it should not be promoted without a new shape- or cache-specific hypothesis.
- Next:
  - Formalize current host-visible MIL/body/request-count exhaustion and name required lower capability for any further progress toward NPU peak.

## 2026-06-24 host-visible MIL/body/request-count exhaustion package
- Skill/method: `docs-generator` style blocker packaging with reverse-engineering evidence links.
- Script: `benchmark/private_ane_host_visible_exhaustion_package.py`.
- Artifact: `mps/ANE/.ane_runs/json/host_visible_mil_body_request_exhaustion_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/host_visible_mil_body_request_exhaustion_20260624.csv`.
- Verdict: `blocked_host_visible_mil_body_request_layer_exhausted`.
- Closed candidate classes:
  - Compiler-accepted `attention_pre` body inventory: `blocked_no_memory_neutral_compiling_candidate`.
  - Route-policy/request lifecycle: `falsified_no_memory_neutral_route_policy_candidate`.
  - Fused time/freq layout: `falsified_fused_layout_compile_invalid`.
  - Selector-3/8 materializer control: `blocked_no_safe_materializer_control_exposed`.
  - Remaining fuse/body toggles: `blocked_no_promotable_memory_neutral_fuse_body_candidate`.
  - Bridge-visible eval setup: `confirmed_eval_send_sec_contains_attention_pre_eval_bucket`; setup is microseconds and not a target.
  - Selector-2 completion split: `confirmed_selector2_completion_low_utilization_opaque`; deeper split requires lower capability.
- Required lower capability:
  - A compiler-accepted `attention_pre` MIL/body/layout contract that reduces selector-2 request count without retained buffers or incompatible `model.hwx` reuse.
  - PAC-safe or privileged selector-2/IOProcessor instrumentation that splits `send_sec` into request materialization, IOConnect submit, firmware compute/wait, completion interrupt, and callback wake.
  - Firmware-private accepted-state/replay visibility below `ProgramReMap` / `dartMapResources` / `createANESurface`.
  - Authorized debug/signing/KDK environment sufficient to observe AppleH16ANEInterface / IOProcessor completion without bypassing correctness paths.
- Blocked actions:
  - Do not bypass `updateRequestFWCommand`, selector-8 `ProgramReMap`, DART mapping, or IOSurface materialization.
  - Do not copy alias `model.hwx` across MIL hashes.
  - Do not add retained handles, IOSurfaces, snapshots, runtime clone caches, or large persistent buffers.
  - Do not claim closer-to-ANE-peak until selector-2 request count or `send_sec` internals are reduced with evidence.
- Conclusion:
  - Current host-visible ANE transformer acceleration paths are exhausted under the no-memory-growth constraint.
  - Further movement toward NPU peak requires a lower-capability track, not another host-visible toggle sweep.
- Next:
  - Choose the next lower-capability track: new compiler-accepted request-count-reducing `attention_pre` contract, or privileged selector-2/IOProcessor instrumentation requirements.

## 2026-06-24 lower-capability track selection package
- Skill/method: `diagnosing-bugs`, `reverse-engineering`, and `docs-generator` style evidence packaging.
- Script: `benchmark/private_ane_lower_capability_track_selection.py`.
- Artifact: `mps/ANE/.ane_runs/json/lower_capability_track_selection_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/lower_capability_track_selection_20260624.csv`.
- Verdict: `selected_compiler_contract_requirements_package`.
- Selected track: `compiler_contract_attention_pre_request_count_reduction`.
- Deferred track: `privileged_selector2_ioprocessor_timing`, status `blocked_on_current_machine`.
- Root-cause inputs carried forward:
  - `attention_pre_eval_sec=12.588885625009425`.
  - `eval_sec=20.12377158299205`.
  - `segment_wall_sec=29.116179916920373`.
  - `estimated_attention_pre_selector2_requests=96`.
  - `time_axis_pre_eval_tflops=0.20732433083177246`.
  - `time_axis_pre_eval_peak_pct=1.1356503660811375`.
- Evidence:
  - `mps/ANE/.ane_runs/json/host_visible_mil_body_request_exhaustion_20260624.json` proves current host-visible MIL/body/request-count/control classes have zero promotable candidates under the no-memory-growth constraint.
  - `mps/ANE/.ane_runs/json/selector2_lower_timing_attribution_package_20260624.json` proves selector-2 send/completion is the dominant opaque low-utilization bucket.
  - `mps/ANE/.ane_runs/json/firmware_reply_runtime_observation_feasibility_20260624.json` and `mps/ANE/.ane_runs/json/firmware_reply_accepted_state_observation_requirements_20260624.json` define the privileged instrumentation requirement, but current SIP/KDK/debug prerequisites are not available on this machine.
  - `mps/ANE/.ane_runs/json/attention_pre_compiler_accepted_inventory_20260624.json` and `mps/ANE/.ane_runs/json/integrated_vs_standalone_attention_pre_q240_20260624.json` remain the local evidence base for the next compiler-contract matrix.
- Conclusion:
  - The safe next loop is not another full-audio benchmark or qchunk sweep. It is a read-only `attention_pre` compiler-contract evidence matrix that either identifies one non-repeating request-count-reducing contract hypothesis or formally blocks the compiler-contract track.
  - Privileged selector-2/IOProcessor instrumentation is deferred until system prerequisites change; trying it now would repeat PAC/SIP/KDK-blocked paths.
- Next:
  - Build `attention_pre` contract evidence matrix from accepted/rejected MIL bodies and cache artifacts; propose exactly one request-count-reducing contract hypothesis, or mark the compiler-contract track blocked and promote the privileged requirements package.

## 2026-06-24 attention_pre compiler-contract evidence matrix
- Skill/method: `diagnosing-bugs`, `reverse-engineering`, and `docs-generator` style matrix packaging.
- Script: `benchmark/private_ane_attention_pre_contract_matrix.py`.
- Artifact: `mps/ANE/.ane_runs/json/attention_pre_contract_evidence_matrix_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/attention_pre_contract_evidence_matrix_20260624.csv`.
- Verdict: `blocked_no_remaining_attention_pre_compiler_contract_hypothesis`.
- Result:
  - `viable_hypothesis_count=0`.
  - `selected_hypothesis=null`.
  - Matrix rows closed 9 candidate families: accepted integrated exact q240, exact q240 same-identifier fast-load artifact, same-weight alias full-attention artifact, alternative qchunk family, fused time/frequency layout, route policy/request coalescing without MIL change, q240 shape guard/policy, fuse body toggles, and generic SDPA/public explicit attention.
- Root-cause context carried forward:
  - `attention_pre_eval_sec=12.588885625009425`.
  - `estimated_attention_pre_selector2_requests=96`.
  - `time_axis_pre_eval_tflops=0.20732433083177246`.
  - `time_axis_pre_eval_peak_pct=1.1356503660811375`.
- Conclusion:
  - No non-repeating memory-neutral `attention_pre` compiler-contract hypothesis remains in the current host-visible evidence.
  - Exact q240 remains only the accepted baseline and does not reduce selector-2 request count; same-identifier fast-load artifact is missing; alias `model.hwx` reuse is rejected because the MIL hash differs; qchunk/layout/fuse/policy alternatives are closed by compile, correctness, memory, or performance evidence.
  - Further progress toward NPU peak now requires privileged selector-2/IOProcessor timing/completion visibility or a genuinely new lower compiler/service capability not present in current artifacts.
- Next:
  - Prepare the privileged selector-2/IOProcessor requirements package: exact system prerequisites, target kernel/driver sites, minimal one-shot probe, fields/timestamps to capture, and safety constraints, without changing current machine state.

## 2026-06-24 privileged selector-2/IOProcessor requirements package
- Skill/method: `diagnosing-bugs`, `reverse-engineering`, `ida-reverse`, and `docs-generator` style requirements packaging.
- Script: `benchmark/private_ane_privileged_selector2_requirements_package.py`.
- Artifact: `mps/ANE/.ane_runs/json/privileged_selector2_ioprocessor_requirements_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/privileged_selector2_ioprocessor_requirements_20260624.csv`.
- Verdict: `blocked_current_machine_requires_privileged_selector2_ioprocessor_visibility`.
- Current-machine blockers:
  - SIP status: `System Integrity Protection status: enabled.`
  - `kern.development: 0`.
  - No KDK listed at `/Library/Developer/KDKs`.
  - Existing Frida/IOKit hooks reach user-space wrappers or selector traffic only; lower arm64e/PAC kernel targets remain unreachable.
  - `com.apple.ane.iokit-user-access` entitlement is not present for regular/non-direct open routes in the current profile.
  - Full-path native-supervised probes remain inappropriate in packaging loops because memory headroom is constrained; the future trace must be one-shot and minimal.
- Package contents:
  - `prerequisites=9`.
  - `target_sites=11`, including user-space `ANEServicesDevice::ANE_ProgramSendRequest` / `ANEServicesProgramProcessRequestDirect`, kernel `SendRequestToFirmware_gated`, `updateRequestFWCommand`, `ProcessReMap` / `ANEUnionResource` dirty-bit propagation, `ANE_ProgramPrepareAndSubmitRequest_gated`, `handleOutstandingCommand`, and `aneCmdSend` / `aneFirmwareCommandSend` / `IOProcessorChannelSendRetry`.
  - `critical_offsets=6`, including `ANERequest+0x3150`, `ANERequest+0x189c`, `record+0x1b8`, `process+0x203fc`, `resource+0x402f0`, and `command-state+0x58/+0x68/+0x88`.
  - Future one-shot probe: `single_attention_pre_selector2_completion_split`, scoped to one minimal accepted `attention_pre` eval, not full `test_clean.m4a`.
- Required future split:
  - Bridge eval entry.
  - Selector-2 request materialization start/end.
  - `updateRequestFWCommand` gate read and DVA rewrite start/end.
  - `IOConnectCallAsyncMethod` selector-2 submit.
  - `IOProcessorChannelSendRetry` entry/return.
  - Firmware completion or response delivery.
  - `ANEHWDevice::handleOutstandingCommand` entry/exit.
  - Callback wake / async completion observed by user-space `send_sec` return.
- Current feasible subset:
  - Frida-spawn own process for outer ANEServices wrapper timing.
  - `ANEServicesDevice::ANE_ProgramSendRequest` duration.
  - `ANEServicesProgramProcessRequestDirect` duration.
  - These are insufficient for the dominant kernel/IOProcessor/firmware completion split.
- Conclusion:
  - The exact future probe is specified, but cannot be executed safely on this machine without an authorized debug/KDK/PAC-safe instrumentation environment or genuinely new lower compiler/service evidence.
  - No local memory-neutral host-visible, compiler-contract, cache, qchunk, fuse, or layout path remains in current evidence.
- Next:
  - External-state change required. Do not repeat closed host-visible paths. If prerequisites change, run only the packaged one-shot selector-2 completion split probe first.

## 2026-06-24 current local private-ANE dead-end package
- Skill/method: `diagnosing-bugs`, `reverse-engineering`, `ida-reverse`, and `docs-generator` style blocker packaging.
- Script: `benchmark/private_ane_current_local_dead_end_package.py`.
- Artifact: `mps/ANE/.ane_runs/json/current_local_private_ane_dead_end_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/current_local_private_ane_dead_end_20260624.csv`.
- Verdict: `blocked_current_local_no_memory_neutral_path_remaining`.
- Local candidate remaining: `false`.
- Goal complete: `false`.
- Layer chain:
  - Host-visible MIL/body/request/control: `blocked_host_visible_mil_body_request_layer_exhausted`.
  - `attention_pre` compiler-contract layer: `blocked_no_remaining_attention_pre_compiler_contract_hypothesis`.
  - Privileged selector-2/IOProcessor visibility: `blocked_current_machine_requires_privileged_selector2_ioprocessor_visibility`.
- Root-cause context:
  - `attention_pre_eval_sec=12.588885625009425`.
  - `eval_sec=20.12377158299205`.
  - `segment_wall_sec=29.116179916920373`.
  - `estimated_attention_pre_selector2_requests=96`.
  - `time_axis_pre_eval_tflops=0.20732433083177246`.
  - `time_axis_pre_eval_peak_pct=1.1356503660811375`.
- Unblocking conditions:
  - Authorized debug/KDK/PAC-safe selector-2/IOProcessor instrumentation environment.
  - Ability to run packaged one-shot `single_attention_pre_selector2_completion_split` safely.
  - Genuinely new lower compiler/service evidence not present in current artifacts.
  - New compiler-accepted `attention_pre` contract evidence that is not a repeat of closed qchunk/fuse/layout/cache/policy families.
- Conclusion:
  - The current local no-memory-growth private-ANE acceleration path is exhausted. Continuing locally without new evidence or external-state change would repeat closed paths.
  - This does not complete the long-term goal; it defines the current dead-end layer and exact unblock requirements.
- Next:
  - Wait for external-state change or new lower-layer evidence. If provided, resume with the packaged one-shot selector-2 completion split probe; otherwise do not continue local acceleration attempts on closed paths.
## iPhone Core ML Hot-Cache Probe Status - 2026-06-25

- Completed: 4-pair Transformer hot-cache relaunch probe on iPhone 13 mini.
- Harness now targets `roformer_layer_pairs_0_3` with source shape `[1,938,62,256]`, `warmup=1`, `iterations=1`, invalidates stale `coreml_bench_result.json` at startup, and writes `coreml_bench_status.json` phase markers.
- Evidence: `mps/ANE/.ane_runs/json/iphone13mini_coreml_transformer4_hotcache_20260625.json` and CSV peer.
- Cold same-install launch: `compile_ms=0.02025`, `load_ms=30209.740375`, `first_prediction_ms=1781.672042`, timed warm mean `1757.408792`.
- Hot relaunch without reinstall: `compile_ms=0.016542`, `load_ms=266.615917`, `first_prediction_ms=1893.237375`, timed warm mean `1752.437042`.
- Verdict: Core ML/E5RT/ANE persistent backend cache is highly effective for this 4-pair Transformer after first successful load, reducing `load_ms` by `29943.124458ms` (`113.308x` cold/hot ratio). Warm eval remains essentially unchanged, so persistent cache solves startup materialization but not per-eval Transformer runtime.
- Invalid evidence caveat: earlier copied files under `mps/ANE/.ane_runs/tmp/iphone13mini_coreml_hotcache/*transformer4*` that report `band_split_plus_mask_estimator` are stale and must not be used as Transformer measurements.
- Metadata caveat: result JSON still records `input.shape=[1,938,62]`; the earlier rank error showed the Core ML model requires rank 4, and the final run completed after the rank-4 source patch. Before publishing the harness as reusable tooling, fix or revalidate the shape metadata field.

## iPhone Core ML Retained-Model Probe - 2026-06-25

- Completed: startup-load plus retained `MLModel` delayed-prediction probe on iPhone 13 mini.
- Evidence: `mps/ANE/.ane_runs/json/iphone13mini_coreml_transformer4_retained_model_20260625.json` and CSV peer.
- Result after install-over launch: `compile_ms=0.016875`, `load_ms=30021.432834`, `first_prediction_ms=1779.075125`, warm mean `1748.005417`, retained same-process prediction after 10s delay `1796.053209`.
- Verdict: keeping the `MLModel` alive avoids a second load in the same process; the delayed retained prediction remains at the same eval cost. App/model bundle install-over can make the next launch cold-like again, so product code should avoid model churn and should warm the cache once after install/update.
