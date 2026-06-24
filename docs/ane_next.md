## Authoritative Recovery Block
Use only the first `Current Phase` / `Current Sub-goal` / `Sole Hypothesis for This Round` block below as the active resume point. Later repeated `Current Phase` headings are historical next-state snapshots retained for provenance under `Previous Next-State History`.

## Current Phase
ExploitOrBlock

## Current Sub-goal
Determine whether larger bounded windows can materially reduce full-`test.m4a` iPhone wall time, or whether the remaining speed problem must return to private ANE/Core ML load/compile reuse instead of window tuning.

## Sole Hypothesis for This Round
Window-size 4 completed and was only marginally faster than window-size 2: `401.705s` vs `412.016s`, full RTF `1.289` vs `1.322`. If window-size 8 does not produce a much larger load reduction without eval/memory regression, bounded-window tuning is not the root solution; the next root task is load/compile reuse or lower-control private ANE carrier work.

## Minimal Probe
1. Keep archived baselines: window-2 `iphone13mini_bounded_window_full_20260625.json`; window-4 `iphone13mini_window4_full_20260625.json`.
2. Optional final window-tuning probe: change only `windowSize` from `4` to `8`, rebuild/sign/install, and run full `test.m4a` once. Do not modify stage order or output schema in the same round.
3. Compare against window-4: `pipeline_ms=401705.094375`, `load_ms=135062.72224899998`, eval sum `259168.27112300004ms`, full RTF `1.289120326903751`.
4. Verdict must explicitly distinguish `window8_materially_faster`, `window8_marginal_or_worse`, `window8_memory_blocked`, or `window8_device_service_blocked`. Treat less than `30s` wall improvement over window-4 as marginal.

## iPhone 13 mini Deployment Attempt - 2026-06-24
- App: `benchmark/ios_coreml_bench/CoreMLBenchApp.xcodeproj`.
- Model: `roformer_layer_pair_0.mlpackage`, input `x FLOAT32 [1, 938, 62, 256]`, output `FLOAT16 [1, 938, 62, 256]`.
- Result: deployment succeeded after trusting the developer profile and correcting Team ID to `LQAYX926KW`.
- Artifact: `mps/ANE/.ane_runs/json/iphone13mini_coreml_ane_subgraph_bench_20260624.json`.
- Measured latency: load `7305.597833ms`, first prediction `463.395333ms`, warm mean `435.92081045000015ms`, p50 `433.906125ms`, p95 `441.147583ms`, RTF `0.08718416209000003` under the 5s-shape assumption.

## iPhone 13 mini Practical Ladder Results - 2026-06-25
- Transformer scaling artifact: `mps/ANE/.ane_runs/json/iphone13mini_coreml_transformer_scaling_20260624.json`.
- Transformer warm means: 1 pair `436.43030835ms`, 2 pairs `869.0061333499998ms`, 4 pairs `1794.3140168999998ms`.
- Transformer loads: 1 pair `7005.73975ms`, 2 pairs `15071.733958ms`, 4 pairs `33324.411666ms`.
- Non-Transformer artifacts: `mps/ANE/.ane_runs/json/iphone13mini_coreml_complete_mask_estimator_20260624.json` and `mps/ANE/.ane_runs/json/iphone13mini_coreml_band_split_plus_mask_estimator_20260625.json`.
- Non-Transformer warm means: `complete_mask_estimator` `15.874591599999999ms`; `band_split_plus_mask_estimator` `16.0976666ms`.
- Practical conclusion: warm Transformer eval is the main remaining runtime cost, and load/cache behavior is the main deployment cost. Band split and mask-estimator heads are not the reason iPhone inference is slow.

## Latest Experiment B Result - 2026-06-24
- Artifact: `mps/ANE/.ane_runs/json/mlx_transformer_experiment_b_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/mlx_transformer_experiment_b_20260624.csv`.
- Full command: `/Users/baicai1145/miniconda3/bin/python mps/roformer_mlx_backend_compare.py --preset hyperace_v2_voc --audio test_clean.m4a --backends torch,mlx_transformer --dtype float16 --out benchmark_results/mps_attention/roformer_mlx_transformer_test_clean_full_20260624.json`.
- Result: `mlx_transformer` completed `test_clean.m4a` in `16.369129040976986s` versus Torch/MPS `26.91898808296537s`; speedup vs Torch/MPS is `1.644497273836551`; max abs diff vs Torch is `0.007223784923553467`; MLX Transformer calls `48`; backend errors `[]`.
- Comparison to prior private-ANE Transformer evidence: prior private-ANE Transformer eval loop was `20.12377158299205s`, so MLX Transformer is `3.7546425420150626s` faster for this comparison, about `1.2293733852678437x`.
- Verdict: `diagnostic_only_all_transformer_on_mlx_not_product_route`. The result is useful as a control showing current private-ANE Transformer overhead, but it is not a meaningful route candidate for the ANE/iPhone goal because it moves the heavy Transformer off ANE. Do not use this result to justify full-Transformer MLX offload.

## Small Fragmented Glue Candidate Map - 2026-06-24
- Artifact: `mps/ANE/.ane_runs/json/small_fragmented_glue_candidate_map_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/small_fragmented_glue_candidate_map_20260624.csv`.
- Ranked candidates:
  1. `mask_tail_final_norm_and_mask_estimator` -> `measure_first`.
  2. `stft_istft_windowing_overlap_add` -> `profile_split_before_offload`.
  3. `chunk_padding_crop_overlap_fold_and_output_stitch` -> `instrument_first`.
  4. `mask_application_complex_multiply` -> `fuse_with_neighbor_or_leave_cpu`.
  5. `band_split_projection` -> `low_priority`.
  6. `axis_layout_pack_unpack_between_ane_segments` -> `do_not_offload_as_mlx; eliminate_or_block`.
- Next probe: timing-only split around final norm, mask estimator, mask multiply, ISTFT, overlap/fold, chunk stitch, and conversion/sync costs on `test_clean.m4a`; do not change default routing until isolated cost and transfer/sync overhead are known.

## Latest Glue Timing Split Result - 2026-06-24
- Probe script: `benchmark/private_ane_glue_timing_split_probe.py`.
- Summary artifact: `mps/ANE/.ane_runs/json/glue_timing_split_summary_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/glue_timing_split_summary_20260624.csv`.
- Warm single-chunk result: elapsed `15.911116791015957s` for `5.0s` audio; mask core `14.919468542037066s` (`93.76757607901656%`), ISTFT `0.2694645829615183s` (`1.6935617185191467%`), STFT `0.017837415973190218s`, chunk glue `0.011735458974726498s`.
- Verdict: `confirmed_no_large_small_glue_bucket_in_5s_private_ane_path`.
- Next action: do not implement broad MLX glue offload. If continuing local glue work, only perform a source-level split inside `private_ane_istft_roformer` and adjacent mask multiply/tail conversion; otherwise return to the real blocker, private-ANE Transformer mask-core selector-2/lower-control timing.
## Authoritative Recovery Block - Single-Mac Static/User Trace Update 2026-06-24 17:15 +0800
- Current Phase: `ExploitOrBlock`
- Current Sub-goal: proceed without a second Mac by extracting all possible single-machine evidence from KDK static artifacts and user-space IOConnect boundary timing.
- Sole Hypothesis for This Round: single-Mac KDK/static analysis plus process-local IOConnect tracing can narrow user-space selector boundaries, but cannot split kernel/IOProcessor/firmware completion.
- Result: added `benchmark/private_ane_single_mac_static_trace_package.py`, `benchmark/private_ane_iokit_selector_trace.c`, `benchmark/private_ane_iokit_selector_trace.dylib`, and Frida fallback `benchmark/private_ane_iokit_selector_trace.js`.
- Static evidence: KDK standalone ANE kexts are available; relevant local binaries are `/Library/Developer/KDKs/KDK_26.5_25F71.kdk/System/Library/Extensions/AppleH16ANEInterface.kext/Contents/MacOS/AppleH16ANEInterface` and `/Library/Developer/KDKs/KDK_26.5_25F71.kdk/System/Library/Extensions/AppleT8132ANEHAL.kext/Contents/MacOS/AppleT8132ANEHAL`.
- Key confirmed exported H16 entrypoints include `ANE_ProgramSendRequest`, `ANE_ProgramInputsReady`, `ANE_GetDebugWorkProcessorItem`, `ANE_RegisterDebugWorkProcessor`, `ANE_CompleteDebugWorkProcessorItem`, `H11ANEInUserClient::externalMethod`, and `H11ANEInDirectPathClient::externalMethod`.
- User-space tracing result: Frida attach is blocked even for a spawned benign Python process, so the usable single-Mac tracer is the DYLD interpose dylib for self-launched benchmark processes. Run with `PYMSS_ANE_IOKIT_TRACE=/tmp/ane_iokit_trace.ndjson DYLD_INSERT_LIBRARIES=$PWD/benchmark/private_ane_iokit_selector_trace.dylib <benchmark command>`.
- Remaining opaque layer: selector-2 firmware/IOProcessor completion still cannot be split on this Mac without privileged runtime/KDP or equivalent lower instrumentation.
- Evidence: `mps/ANE/.ane_runs/json/single_mac_kdk_static_trace_package_20260624.json` and `mps/ANE/.ane_runs/csv/single_mac_kdk_static_trace_package_20260624.csv`.
- Trace smoke result: accepted `attention_pre` micro-profile completed under the DYLD tracer, and the dylib constructor logged `trace_loaded`, but zero `IOConnectCall*` rows and zero selector-2 rows were captured. Evidence: `mps/ANE/.ane_runs/json/single_mac_iokit_trace_smoke_20260624.json`.
- Next minimal action: do not rely on process-local IOConnect interpose for selector-2 timing. If continuing single-Mac work, the remaining useful path is static KDK/IDA field recovery or higher-level MLX/tail offload; lower completion timing still needs privileged runtime/KDP or equivalent service-side instrumentation.

## Authoritative Recovery Block - KDK Debug Environment Update 2026-06-24 16:52 +0800
- Current Phase: `ExploitOrBlock`
- Current Sub-goal: turn the previous privileged selector-2/IOProcessor blocker into a runnable PAC-safe observation setup.
- Sole Hypothesis for This Round: installing the exact-build KDK is necessary but not sufficient; live selector-2 completion splitting still requires a SIP-disabled Recovery-configured target and KDP-supported built-in Ethernet or a supported target Mac.
- Result: exact-build KDK installed and verified at `/Library/Developer/KDKs/KDK_26.5_25F71.kdk` for macOS `26.5` build `25F71`; source DMG SHA-256 is `90ed319cd1ba6e23d1eefcee89fa1b10743f4cf60b85208ae52aa9f45543c7aa`; package signature is Apple Software; KDK ReadMe extracted to `/Volumes/2T/kdk/KDK_26.5_25F71_ReadMe.txt`.
- Remaining blocker: this machine still has SIP enabled, `kern.development=0`, `kern.osbuildconfig=release`, and active Ethernet is `en5`; Apple KDK ReadMe says Apple Silicon two-machine debugging requires built-in Ethernet and not USB Ethernet or Wi-Fi, so MacBook Air M4 live KDP is likely still hardware-blocked unless a supported wired target/host setup is provided.
- Minimal next action if user wants to continue: boot the target into Recovery, run `csrutil disable`, reboot, identify a KDP-supported Ethernet interface, set `sudo nvram boot-args="debug=0x44 kdp_match_name=<enX> wdt=-1"`, reboot, then attach from the host with LLDB/KDK symbols.
- Do not repeat: qchunk sweeps, fuse/body toggles, direct `model.hwx` aliasing, selector bypasses, full-audio benchmarks, or memory-growth strategies before `single_attention_pre_selector2_completion_split` is actually observable.
- Evidence: `mps/ANE/.ane_runs/json/kdk_debug_environment_install_20260624.json` and `mps/ANE/.ane_runs/csv/kdk_debug_environment_install_20260624.csv`.

2. If new lower compiler/service evidence appears, first update the evidence matrix before any compile/eval run.
3. Otherwise stop local acceleration attempts and do not repeat closed paths.
4. Still forbidden: changing SIP/KDK/rebooting without explicit authorization, attaching to kernel targets, retaining ANE handles/IOSurfaces/snapshots, copying `model.hwx` across MIL hashes, or running full-audio benchmarks without a new validated candidate.

## Latest Completed Loop
- Artifact: `mps/ANE/.ane_runs/json/current_local_private_ane_dead_end_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/current_local_private_ane_dead_end_20260624.csv`.
- Verdict: `blocked_current_local_no_memory_neutral_path_remaining`.
- Conclusion: the current local no-memory-growth private-ANE acceleration path is formally exhausted. Host-visible MIL/body/request/control is exhausted, `attention_pre` compiler-contract hypotheses have `viable_hypothesis_count=0`, and privileged selector-2/IOProcessor visibility is blocked by current machine state. Long-term goal is not complete; local execution requires external-state change or genuinely new lower-layer evidence.

## Previous Completed Loop
- Artifact: `mps/ANE/.ane_runs/json/privileged_selector2_ioprocessor_requirements_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/privileged_selector2_ioprocessor_requirements_20260624.csv`.
- Verdict: `blocked_current_machine_requires_privileged_selector2_ioprocessor_visibility`.
- Conclusion: the privileged selector-2/IOProcessor requirements package is complete. Current machine blockers are SIP enabled, `kern.development=0`, no KDK listing, PAC/privilege barriers for lower arm64e targets, missing entitlement for regular ANE open routes, and insufficient memory for full-path native-supervised probes. The future minimal probe is one accepted `attention_pre` eval that splits `send_sec` into materialization, IOConnect submit, firmware compute/wait, completion interrupt, and callback wake without retained memory.

## Previous Completed Loop
- Artifact: `mps/ANE/.ane_runs/json/attention_pre_contract_evidence_matrix_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/attention_pre_contract_evidence_matrix_20260624.csv`.
- Verdict: `blocked_no_remaining_attention_pre_compiler_contract_hypothesis`.
- Conclusion: the compiler-contract matrix closed 9 candidate families with `viable_hypothesis_count=0`. Exact q240 is only the accepted baseline, same-identifier fast-load artifact is missing, alias `model.hwx` is MIL-hash incompatible, alternative qchunks/layout/fuse/policy families are closed, and no non-repeating memory-neutral request-count-reducing `attention_pre` contract remains in current artifacts.

## Previous Completed Loop
- Artifact: `mps/ANE/.ane_runs/json/lower_capability_track_selection_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/lower_capability_track_selection_20260624.csv`.
- Verdict: `selected_compiler_contract_requirements_package`.
- Conclusion: lower-capability track selection is complete. The selected next track is `compiler_contract_attention_pre_request_count_reduction` because it is weak but still locally actionable and read-only under the no-memory-growth constraint. The privileged selector-2/IOProcessor timing track is deferred as `blocked_on_current_machine` because existing evidence requires SIP/KDK/debug or equivalent privileged runtime access.

## Previous Completed Loop
- Artifact: `mps/ANE/.ane_runs/json/host_visible_mil_body_request_exhaustion_20260624.json` and CSV peer `mps/ANE/.ane_runs/csv/host_visible_mil_body_request_exhaustion_20260624.csv`.
- Verdict: `blocked_host_visible_mil_body_request_layer_exhausted`.
- Conclusion: current host-visible ANE transformer acceleration paths are exhausted under the no-memory-growth constraint. Closed classes include compiler-accepted `attention_pre` body inventory, route policy/request lifecycle, fused time/freq layout, selector-3/8 materializer control, remaining fuse/body toggles, bridge-visible eval setup, and selector-2 completion splitting at the current bridge layer. Further progress requires either a compiler-accepted request-count-reducing `attention_pre` contract or privileged selector-2/IOProcessor visibility/control.

## Previous Completed Loop
- Artifact:
  `mps/ANE/.ane_runs/json/route_policy_lifecycle_analysis_20260624.json`
  and CSV peer
  `mps/ANE/.ane_runs/csv/route_policy_lifecycle_analysis_20260624.csv`.
- Verdict:
  `falsified_no_memory_neutral_route_policy_candidate`.
- Conclusion: current transformer timing rows show 24 rows, 24 load-cache hit
  rows, 0 load misses, about 48 time-axis `attention_pre` selector requests,
  time-axis `attention_pre_eval_sec=9.538814419182017`, and time-axis
  `axis_pack_sec=2.5199859970016405`. Axis gating, q240 guard tightening,
  skip-source/write policy, request coalescing without MIL changes, and
  host-visible repack policies do not provide a remaining memory-neutral route
  policy candidate.

## Previous Completed Loop
- Artifact:
  `mps/ANE/.ane_runs/json/attention_pre_compiler_accepted_inventory_20260624.json`
  and CSV peer
  `mps/ANE/.ane_runs/csv/attention_pre_compiler_accepted_inventory_20260624.csv`.
- Verdict:
  `blocked_no_memory_neutral_compiling_candidate`.
- Conclusion: the consolidated inventory found 7 candidates and 0 promotable
  memory-neutral compiler-accepted replacements. The current q240 route remains
  the only operable baseline; exact q240 fast-load remains source-only/direct
  compile invalid; alias full-attention artifacts have compiled `model.hwx`
  files but incompatible MIL hashes; qchunk/layout/public-SDPA and B44E refresh
  classes remain closed.

## Previous Completed Loop
- Artifact:
  `mps/ANE/.ane_runs/json/band_split_b44e_refresh_probe_20260624.json`
  and CSV peer
  `mps/ANE/.ane_runs/csv/band_split_b44e_refresh_probe_20260624.csv`.
- Verdict:
  `blocked_b44e_load_qos_rejects_and_refresh_compile_invalid`.
- Conclusion: a minimal B44E-only bridge probe loaded the exact
  `band_split_l2_fused_0_4` MIL/weights/output sizes without full audio.
  Existing same-identifier cache load still failed via
  `load_cache_skip_source_write` (`load_qos_sec≈0.029s`, `success=0`), and
  fallback same-identifier compile failed `InvalidMILProgram`
  (`compile_qos_sec≈0.0086s`, `success=0`). The probe retained no handles or
  extra buffers. An initial unsafe probe invocation allowed bridge cleanup to
  remove the main cache directory; it was restored only from same-identifier
  wrapperwork/repro artifacts, not from an alias hash.

## Previous Completed Loop
- Artifact:
  `mps/ANE/.ane_runs/json/band_split_b44e_cache_materialization_probe_20260624.json`
  and CSV peer.
- Verdict:
  `blocked_band_split_cache_present_but_load_qos_rejects_then_compile_invalid`.
- Conclusion: the B44E cache exists and matches the MIL hash, but
  `loadWithQoS` rejects it on both relative and absolute cache paths; fallback
  compile still fails `InvalidMILProgram`.

## Previous Completed Loop
- Artifact:
  `mps/ANE/.ane_runs/json/full_path_q240_native_eval_capture_blocked_20260624.json`
  and CSV peer.
- Verdict:
  `blocked_full_path_q240_native_eval_capture_by_band_split_compile`.
- Conclusion: native eval telemetry should propagate into per-layer
  `transformer_timings`, but the current full-path q240 reruns fail before
  transformer at `band_split_l2_fused_0_4` with `InvalidMILProgram`. The next
  loop must restore or explain that auxiliary load-cache/materialization
  prerequisite.

## Previous Completed Loop
- Artifact:
  `mps/ANE/.ane_runs/json/accepted_q240_eval_native_profile_probe_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_native_eval_profile_instrumentation_but_exact_q240_blocked_before_eval`.
- Conclusion: `ane_bridge_eval` now emits native eval timing, and eval failures
  include `bridge_profile` JSON. The exact q240 layerwise seam still fails with
  `InvalidMILProgram` before eval, so it cannot split the accepted full-path
  q240 `ane_pre_eval` bucket.

## Previous Completed Loop
- Artifact:
  `mps/ANE/.ane_runs/json/attention_pre_memory_neutral_candidate_inventory_20260624.json`
  and CSV peer.
- Verdict: `blocked_no_memory_neutral_compiling_candidate`.
- Conclusion: accepted exact q240 remains the current opt-in baseline, but no
  newly promotable candidate satisfies compile/loadability, numerical safety,
  memory neutrality, and expected speed improvement. Same-weight alias compiled
  artifacts remain unsafe because MIL hash differs; alternative q-chunks and
  host-visible layout/surface variants are closed.

## Do Not Repeat
- Do not copy same-weight alias `model.hwx`; its MIL hash differs.
- Do not mutate the exact q240 MIL identity just to force compilation.
- Do not run full `test_clean.m4a` until the q240 compiler blocker or an
  equivalent memory-neutral route is resolved.
- Do not retain extra ANE handles, IOSurfaces, buffers, snapshots, or runtime
  clone caches as an acceleration strategy.
- Do not expand `NSError.userInfo` or Python-process Frida hooks again; both
  are confirmed not to carry the `ValidateEntry` reason map for exact q240.
- Do not attempt service-side attach again unless SIP/debug privilege changes.

## Previous Next-State History

## Current Phase
ExploitOrBlock

## Current Sub-goal
Choose the next memory-neutral workaround path now that exact q240
`ValidateEntry` capture is blocked behind `ANECompilerService` debug privilege.

## Sole Hypothesis for This Round
Python-process Frida hooks and recursive `NSError` capture both fail to expose
the exact q240 `ValidateEntry` reason map. `ANECompilerService.xpc` is the
compilation host, and current-user attach is denied. Therefore the next useful
loop should avoid depending on the exact q240 invalid body: identify one
compiler-accepted, memory-neutral MIL/route candidate and verify whether it
improves or preserves the accepted `test_clean.m4a` path constraints.

## Minimal Probe
1. Inventory compiler-accepted attention_pre bodies already present in cache or
   prior artifacts, especially same-weight alias/full-attention bodies and any
   non-interleaved/no-final-concat variants.
2. For each candidate, classify correctness equivalence risk, expected transient
   memory/RSS risk, and whether it can use existing compiled artifacts without
   copying incompatible `model.hwx` across MIL hashes.
3. Run only minimal layer/probe commands first. Do not run full audio until a
   candidate compiles, validates numerically, and does not increase retained
   memory.
4. Write the next artifact under `mps/ANE/.ane_runs/json/` and CSV peer with
   verdict `confirmed_memory_neutral_mil_fix_candidate`,
   `blocked_no_memory_neutral_compiling_candidate`, or
   `inconclusive_need_service_debug_privilege`.

## Do Not Repeat
- Do not copy same-weight alias `model.hwx`; its MIL hash differs.
- Do not mutate the exact q240 MIL identity just to force compilation.
- Do not run full `test_clean.m4a` until the q240 compiler blocker or an
  equivalent memory-neutral route is resolved.
- Do not retain extra ANE handles, IOSurfaces, buffers, snapshots, or runtime
  clone caches as an acceleration strategy.
- Do not spend another loop only comparing per-layer concat/slice/matmul
  validators unless it exposes the `ValidateEntry` reason map.
- Do not expand `NSError.userInfo` or Python-process Frida hooks again; both
  are confirmed not to carry the `ValidateEntry` reason map for exact q240.
- Do not attempt service-side attach again unless SIP/debug privilege changes.
- Do not copy same-weight alias `model.hwx` into the exact q240 cache unless a
  separate validator proves the MIL identity mismatch is safe.

## Previous Next-State History

# Private ANE Next
## Current Phase
`Control`
## Current Sub-goal
Map the exact q240 `model.mil` operations and shapes to ANECompiler validation
surfaces, then identify the operation/shape that triggers `InvalidMILProgram`
or prove this exact MIL body is a compiler dead end.
## Sole Hypothesis for This Round
Because runtime evidence now localizes the exact q240 failure to
`ANECCompile(...CFEEBA68...F8815657...E3B0C442...)` returning
`InvalidMILProgram`, the decisive next fact is whether the generated q240 MIL
contains a validator-visible unsupported operation/shape that can be changed
memory-neutrally without changing the accepted graph identity.
## Latest Loop Result
- Artifact:
  `mps/ANE/.ane_runs/json/exact_q240_runtime_error_payload_probe_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_runtime_error_payload_precondition`.
- Result:
  IDA MCP was recovered, AppleNeuralEngine and ANECompiler reopened, and the
  minimal q240 bridge-env probe captured native error payload:
  `com.apple.appleneuralengine.compiler Code=1`, `_ANECompiler :
  ANECCompile() FAILED`, underlying `InvalidMILProgram` for the exact q240 temp
  source directory.
- Bridge result:
  `client_file_error_detail` is now captured in bridge profile JSON for future
  materializer failures; `libane_bridge.dylib` rebuilt successfully.
## Minimal Probe
1. Parse the exact q240 `model.mil` from the source-only cache and summarize
   operation names, tensor shapes, constants, and q240 tiling structure.
2. Query ANECompiler IDA strings/functions for validators related to those ops:
   matrix multiply, softmax, slice/gather, SDPA, reshape/transpose, and dynamic
   shape restrictions.
3. Compare the failing exact q240 MIL against the same-weight compiled alias
   MIL hash family only as evidence; do not copy artifacts or change graph
   identity.
4. Verdict must be one of:
   `confirmed_invalid_q240_mil_op_shape`,
   `confirmed_memory_neutral_mil_fix_candidate`,
   `blocked_exact_q240_invalid_mil_dead_end`, or
   `inconclusive_need_compiler_validation_trace`.
## Previous Context

## Current Phase
`ExploitOrBlock`

## Current Sub-goal
Search for a known-good standalone fast-load run that produced a compatible
compiled `model.hwx` for the same q240 identifier; if none exists, formally
block artifact priming and move to the lower native compile/load artifact
materialization question.

## Sole Hypothesis for This Round
Because the cache inspector confirmed the integrated q240 identifier is
`source_only`, a valid fast-load route diagnostic requires finding or producing
a loadable compiled artifact (`model.hwx` and companion files) for the same
identifier without increasing runtime memory.

## Latest Loop Result
- Artifact:
  `mps/ANE/.ane_runs/json/integrated_q240_cache_artifact_inspection_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_loadable_artifact_missing`.
- Code added:
  `benchmark/private_ane_cache_artifact_inspector.py`.
- Result:
  target cache directory exists and contains `model.mil` plus 7 weight files,
  but no `model.hwx` or `model.hwx.tmp.additional_weights.bin`.

## Minimal Probe
1. Search `benchmark_results/private_ane` and bridge cache roots for the same
   q240 identifier with `model.hwx` present.
2. If found, compare companion files and record exact source/destination paths;
   do not copy into active cache until the plan is explicit.
3. If not found, record `blocked_no_known_good_compiled_artifact`.
4. Verdict must be one of:
   `confirmed_same_identifier_loadable_artifact_found`,
   `confirmed_loadable_artifact_priming_plan`,
   `blocked_no_known_good_compiled_artifact`, or
   `inconclusive_identifier_alias_possible`.

## Previous Context

## Current Phase
`ExploitOrBlock`

## Current Sub-goal
Recover a valid load-only route diagnostic by either priming a compiled/loadable
q240 artifact from a known-good standalone fast-load run into the integrated
cache identifier, or adding a plan-only cache inspector that checks loadable
artifact presence before invoking ANE compile.

## Sole Hypothesis for This Round
Because the existing integrated route-only harness reached a source-only cache
entry (`model.mil` plus weights, no `model.hwx`) and therefore attempted compile
before failing with `InvalidMILProgram`, a valid route diagnostic must first
prove or create a loadable compiled artifact for the same content identifier.

## Latest Loop Result
- Artifact:
  `mps/ANE/.ane_runs/json/integrated_attention_pre_route_only_q240_compile_blocker_20260624.json`
  and CSV peer.
- Verdict:
  `blocked_route_only_compile_invalid_mil_no_loadable_cache_artifact`.
- Probe launched:
  yes, transformer-only route diagnostic; no full audio.
- Result:
  command exited `1`, wrote no JSON output, and failed during candidate q240
  `attention_pre` compile with `InvalidMILProgram`.
- Cache result:
  matching identifier directory exists in `benchmark_results/private_ane/ane_tmp_loadcache`,
  but contains only `model.mil` and weights, not a compiled `model.hwx` or
  equivalent loadable artifact.

## Minimal Probe
1. Do not run full `test_clean.m4a`.
2. First inspect or build the target content-addressed cache directory and prove
   whether a compiled/loadable artifact exists.
3. If a known-good standalone fast-load run has a compiled artifact for the same
   MIL/weights identifier, test a copy/prime plan without retaining extra
   handles or IOSurfaces.
4. Otherwise add a plan-only cache inspector that reports source-only versus
   loadable cache state and exits before ANE compile.
5. Verdict must be one of:
   `confirmed_loadable_artifact_missing`,
   `confirmed_loadable_artifact_primed`,
   `falsified_same_identifier_artifact_reuse`, or
   `blocked_no_known_good_compiled_artifact`.

## Previous Context

## Current Phase
`ExploitOrBlock`

## Current Sub-goal
Create or run a small route-only integrated transformer load-cache diagnostic
that records the native load-only error/fallback reason for one q240
`attention_pre` artifact without full audio and without retaining extra
handles.

## Sole Hypothesis for This Round
Because static audit proved Python flags are set and the integrated fast-load
miss is gated by the native bridge early load-only predicate, the next smallest
useful probe is to capture the native load-only failure/fallback reason for one
integrated q240 `attention_pre` artifact without running full audio.

## Latest Loop Result
- Artifact:
  `mps/ANE/.ane_runs/json/integrated_fastload_route_static_audit_20260624.json`
  and CSV peer.
- Verdict:
  `confirmed_native_load_only_predicate_is_integrated_fastload_gate`.
- Benchmark launched:
  no. Memory preflight was still invalid (`15G used`, `5465M compressor`, only
  `106M unused`, swap used `2628.38M`), so the documented static fallback was
  used.
- Static result:
  Python/benchmark flags enable load-cache, keep-tmpdir, and skip-source; the
  route is decided inside `mps/maderix_ANE/bridge/ane_bridge.m`. The native
  bridge assigns `load_cache_skip_source_fast_load` only when the early
  load-only attempt succeeds; otherwise, if source files are complete, it falls
  to `load_cache_skip_source_write`.

## Minimal Probe
1. Use a one-artifact integrated transformer/q240 `attention_pre` route-only
   harness, not full `test_clean.m4a`.
2. Keep no retained transformer handles, IOSurfaces, buffers, snapshots, or
   runtime-clone cache.
3. Capture native bridge profile fields:
   `route`, `fast_load_attempted`, `fast_load_hit`, `fast_load_fallback`,
   load-only error string if available, `load_qos_sec`, `tmpdir_sec`,
   `file_write_sec`, and source completeness.
4. Verdict must be one of:
   `confirmed_load_only_error_reason`,
   `confirmed_route_only_fastload_hit`,
   `falsified_static_gate_missing_runtime_condition`, or
   `blocked_route_only_needs_clean_memory`.

## Previous Context

## Current Phase
`ExploitOrBlock`

## Current Sub-goal
Obtain a clean native-supervised batch-4 memory preflight and rerun the exact
integrated fast-load-hit acceptance command on `test_clean.m4a`; if the same
memory blocker repeats again, switch to an offline/static audit of why the
integrated path does not hit `load_cache_skip_source_fast_load`.

## Sole Hypothesis for This Round
Because the previous attempt to validate integrated transformer
`load_cache_skip_source_fast_load` was blocked by invalid memory preconditions,
the next useful step is not another wall-time run under pressure; it is either a
clean native-supervised batch-4 acceptance run or, after a repeated blocker, an
offline/static route audit of the integrated fast-load miss.

## Latest Loop Result
- Artifact:
  `mps/ANE/.ane_runs/json/integrated_fastload_acceptance_blocked_memory_20260624.json`
  and CSV peer.
- Verdict:
  `blocked_invalid_memory_preconditions`.
- Benchmark launched:
  no. Current memory was `15G used`, `3522M wired`, `4615M compressor`, only
  `140M unused`, and swap used `2676.38M`.
- Skipped acceptance command:
  `/Users/baicai1145/miniconda3/bin/python benchmark/private_ane_test_clean_benchmark.py --audio test_clean.m4a --full-audio --baseline none --private-ane-allow-long-audio --private-ane-native-supervisor on --private-ane-native-supervisor-path benchmark/ane_mem_supervisor --private-ane-chunk-batch-size 4 --private-ane-tiled-time-attention-pre --private-ane-tiled-time-attention-pre-q-chunk 240 --private-ane-skip-source-write-on-cache-hit --private-ane-fused-band-split --private-ane-fused-band-split-max-outputs 4 --private-ane-fused-mask-estimator --private-ane-fused-mask-estimator-max-outputs 2 --private-ane-load-cache --private-ane-keep-tmpdir --out benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_integrated_fastload_acceptance_20260624.json`.

## Previous Context

## Current Phase
`ExploitOrBlock`

## Current Sub-goal
Run a valid native-supervised batch-4 integrated fast-load-hit acceptance probe
on `test_clean.m4a`.

## Sole Hypothesis for This Round
Because the accepted integrated q240 MIL is byte-identical to the faster
standalone q240 MIL, but the accepted integrated path misses the
`load_cache_skip_source_fast_load` route that standalone hits, the next useful
speedup candidate is to validate an integrated transformer fast-load-hit route
under proper native-supervised batch-4 memory conditions.

## Next Minimal Probe
1. Confirm current machine memory preconditions before running. If native
   supervisor would immediately fail or auto-select batch-1, do not interpret
   wall time as acceptance.
2. Run the smallest valid native-supervised full-path probe on `test_clean.m4a`
   with `chunk_batch_size=4`, q240 shape guard, load-cache, keep-tmpdir,
   skip-source-on-cache-hit, and fast-load-before-source-verify route active.
3. Required evidence: wall time, RTF, max RSS, ANEServices RSS, swap/free-memory
   data, route counters for `load_cache_skip_source_fast_load`, cache misses,
   and transformer `ane_pre_eval_sec` / axis-pack split.
4. Verdict must be one of:
   `confirmed_integrated_fastload_speedup`,
   `falsified_fastload_no_eval_speedup`,
   `blocked_invalid_memory_preconditions`, or
   `inconclusive_need_lower_firmware_timing`.
5. Only if wall remains near/below `30s` and memory does not regress, run the
   existing correctness gate in a later loop.

## Current Evidence
- Current root-cause/solution map:
  `mps/ANE/.ane_runs/json/slow_inference_root_cause_solution_map_20260624.json`
  and CSV peer.
- Current lifecycle attribution:
  `mps/ANE/.ane_runs/json/transformer_lifecycle_bucket_attribution_20260624.json`
  and CSV peer.
- Current lifecycle verdict:
  `confirmed_next_lifecycle_bucket`; selected bucket is
  `time_axis_attention_pre_eval_request_lifecycle`.
- Current layer-0 lifecycle probe:
  `mps/ANE/.ane_runs/json/time_attention_pre_layer0_lifecycle_probe_20260624.json`
  and CSV peer.
- Current layer-0 verdict:
  `inconclusive_need_lower_runtime_access`; host setup is not dominant, but
  current user-space profile cannot split `ane_pre_eval_sec` into compute body
  versus selector-2 request/materialization.
- Current bridge eval attribution:
  `mps/ANE/.ane_runs/json/bridge_eval_path_attribution_20260624.json` and CSV
  peer.
- Current bridge eval verdict:
  `confirmed_firmware_wait_or_compute_dominant`; request materialization and
  IOConnect selector-2 submit are not the dominant cost, and user-space
  signposts do not span the compute/completion gap.
- Current throughput attribution:
  `mps/ANE/.ane_runs/json/attention_pre_throughput_roofline_20260624.json`
  and CSV peer.
- Current throughput verdict:
  `confirmed_low_utilization_compute_body`; accepted time-axis
  `attention_pre` is about `0.20732433083177246 TFLOPS`, or
  `1.1356503660811375%` of measured local ANE FP16 peak.
- Current integrated-vs-standalone q240 comparison:
  `mps/ANE/.ane_runs/json/integrated_vs_standalone_attention_pre_q240_20260624.json`
  and CSV peer.
- Current comparison verdict:
  `confirmed_memory_neutral_body_candidate`; the q240 MIL is identical
  (`sha256=cfeeba68a0867d458ffa754fc3777ecdce97c7ab6dd42abe81d759ad310d59c6`),
  but standalone hits `load_cache_skip_source_fast_load` while accepted
  integrated layer0 uses `load_cache_skip_source_write` with `fast_load_hit=0`.
- Verdict:
  `blocked_no_memory_neutral_candidate` for current host-visible
  `attention_pre` / request-count reduction.
- Best accepted full-path evidence:
  `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_tiled_q240_skip_source_20260623.private_ane_child/meta.json`.
- Best accepted full-path numbers:
  wall `27.903367375023663s`, RTF `0.7048080675165779`,
  transformer `24.631073875003494s`, transformer eval
  `19.743745001906063s`, transformer compile/load
  `1.944708043942228s`, max RSS `1282.671875MB`.
- Current cached transformer timing source:
  `benchmark_results/private_ane/test_clean_full_private_native_supervised_batch4_load_cache_bridgeprofile_20260623_profile/transformer_timings.csv`.
- Cache facts:
  `24/24` transformer rows are load-cache hits and load-cache misses are `0`.
  Load/compile absence is not the current dominant bottleneck.
- Dominant remaining bottleneck:
  time-axis `attention_pre` eval is `9.538814419182017s` across 12 rows,
  with about `48` estimated selector-2 requests. Freq-axis `attention_pre`
  eval is `3.0500712058274075s`, also about `48` estimated requests.
- Representative accepted hot-path layer:
  time layer 0 q240 has `ane_pre_eval_sec=0.7698414579790551s`,
  `ane_pre_write_sec=0.01106487397919409s`,
  `ane_pre_read_sec=0.026174624013947323s`, and
  `axis_pack_sec=0.05874783397302963s`; therefore host setup/write/read/pack
  are not the dominant cost for that layer.
- Lower eval path:
  ANEServices selector 2 (`ANE_ProgramSendRequest`) uses
  `IOConnectCallAsyncMethod`; submit returns quickly and the dominant opaque
  gap is between submit return and async completion.
- Throughput caveat:
  TFLOPS estimate counts qkv/rope/sdpa arithmetic only; softmax, slices,
  transposes, private scheduler, and firmware completion overhead are not
  represented as peak FLOPs.
- Prior fast-load caveat:
  `mps/ANE/.ane_runs/json/bridge_fastload_before_source_verify_probe_20260624.json`
  confirmed the bridge route but full speed was inconclusive because the valid
  native-supervised batch-4 run failed preconditions and non-supervised runs
  fell to batch-1.
- Secondary bottleneck:
  time-axis packing is `2.5199859970016405s`; freq-axis packing is
  `0.8207393719640095s`.
- Lower accepted-state route:
  `mps/ANE/.ane_runs/json/firmware_reply_runtime_observation_feasibility_20260624.json`
  has verdict `blocked_need_privileged_runtime_access`. Under current SIP /
  authenticated-root / no-KDK conditions, do not continue forcing this route.
- Current-layer closure:
  `mps/ANE/.ane_runs/json/time_attention_pre_request_axis_pack_audit_20260624.json`
  closed forced q240, bridge-pack disable, direct time-to-freq repack,
  surface handoff, batch-axis promotion, and H16-visible selector-2 gate bypass
  as current-loop candidates.
- Layout/control closure:
  `mps/ANE/.ane_runs/json/fused_time_freq_layout_compile_probe_20260624.json`
  confirms transpose/crop compiles, but the tested pad-to-64 concat fails with
  `InvalidMILProgram`; prior unpadded freq runtime eval fails without a new
  lower surface/materializer contract.
- Current dead-end boundary:
  the host-visible private ANE graph/layout/runtime layer plus H16 selector-2/3/8
  materializer layer is exhausted for this no-memory-growth objective. ANE
  firmware/internal scheduler below raw send is not proven exhausted, but it is
  not observable on this machine today.

## Do Not Repeat Without New Evidence
- Running or interpreting full-wall benchmarks when auto batching selects
  `chunk_batch_size=1`.
- Running full `test_clean.m4a` just to choose the next bucket; use
  transformer-only attribution first.
- Reusing `benchmark/private_ane_attention_pre_micro_profile.py` as the
  authority for time-axis layer-0 `attention_pre`; the standalone MIL seam
  failed compile with `InvalidMILProgram` and is not equivalent to the
  integrated transformer path.
- Running correctness validation before wall time is back near or below `30s`.
- Re-testing bridge tmpdir/source verification without a changed cache/load
  hypothesis; that path is already fixed at component level.
- Blind qchunk sweeps that ignore the shape-dependent q240 guard.
- Same-layer H16-visible selector-2 field guessing for resource collection,
  request replay, scheduler pending-entry reuse, or `ANERequest + 0x3150`
  force-clear/firmware command DVA bypass.
- Direct/unpadded freq repack or pad-to-64 layout probes unless a new lower
  surface/materializer contract is identified.
- Any speedup that increases RSS/wired memory/swap or keeps additional
  transformer handles, buffers, surfaces, or response snapshots alive.
- Selector-8 `needProgramRemap` forcing, `ProgramReMap` bypass, or
  `createANESurface` contract override without a new lower correctness proof.
- Repackaging the current-layer blocker again unless a new lower target or new
  evidence source is added.
- Re-enumerating lower accepted-state targets; one target was selected and the
  runtime observation route is blocked under current local privileges.
- Re-proving that `isProcessValid` consumes `process+0x203fc`; this is already
  confirmed.
## iPhone Core ML Hot-Cache Probe Recovery

- Completed hot-cache verdict: same-install relaunch reduces 4-pair Transformer `load_ms` from `30209.740375` to `266.615917` on iPhone 13 mini; evidence is `mps/ANE/.ane_runs/json/iphone13mini_coreml_transformer4_hotcache_20260625.json`.
- Prepared harness: `benchmark/ios_coreml_bench/CoreMLBenchApp/AppDelegate.swift` targets `roformer_layer_pairs_0_3`, source input shape `[1,938,62,256]`, `warmup=1`, `iterations=1`, removes stale `coreml_bench_result.json` at startup, and writes `coreml_bench_status.json` phase markers.
- Next minimal probe: keep the model loaded in-process and measure repeated real pipeline invocations without app relaunch; then separate remaining wall time into Transformer warm eval, feature/glue, output steps, and app lifecycle.
- Retained-model probe completed: after startup load, a same-process delayed prediction after 10s was `1796.053209ms`, matching warm eval and incurring no second load. Evidence: `mps/ANE/.ane_runs/json/iphone13mini_coreml_transformer4_retained_model_20260625.json`.
- Updated next minimal probe: build the iPhone end-to-end timing harness around the product pattern: app startup model load/warmup, long-lived `MLModel`, then timed user-triggered inference. Report real audio decode/features, Transformer eval, non-Transformer heads, output/ISTFT/write, and UI/app overhead separately.
- Do not use old copied JSONs showing `band_split_plus_mask_estimator` as Transformer evidence; those were stale container results from before the clean reinstall.
- Caveat to fix before publishing harness: result JSON still reports `input.shape=[1,938,62]`; revalidate the app-side metadata path because the successful rank-4 run followed a source patch to `[1,938,62,256]`.
