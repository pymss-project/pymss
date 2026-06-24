import CoreML
import os
import UIKit

@main
final class AppDelegate: UIResponder, UIApplicationDelegate {
    var window: UIWindow?
    private let statusView = UITextView()

    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {
        let window = UIWindow(frame: UIScreen.main.bounds)
        let viewController = UIViewController()
        viewController.view.backgroundColor = .systemBackground
        statusView.frame = viewController.view.bounds.insetBy(dx: 12, dy: 40)
        statusView.autoresizingMask = [.flexibleWidth, .flexibleHeight]
        statusView.font = .monospacedSystemFont(ofSize: 11, weight: .regular)
        statusView.isEditable = false
        statusView.text = "CoreMLBench starting..."
        viewController.view.addSubview(statusView)
        window.rootViewController = viewController
        window.makeKeyAndVisible()
        self.window = window

        Task.detached(priority: .userInitiated) {
            await BenchmarkRunner { text in
                Task { @MainActor in
                    self.statusView.text = text
                }
            }.run()
        }
        return true
    }
}

struct BenchmarkRunner {
    private let log = Logger(subsystem: "com.baicai1145.CoreMLBench", category: "benchmark")
    private let updateStatus: @Sendable (String) -> Void

    init(updateStatus: @escaping @Sendable (String) -> Void) {
        self.updateStatus = updateStatus
    }

    func run() async {
        do {
            updateStatus("CoreMLBench running...")
            clearPreviousResult()
            try? writeStatus(phase: "suite_started", modelName: nil)
            let encoder = JSONEncoder()
            encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
            let statusModel: String?
            let data: Data
            if InMemoryStageMajorRunner.assetsAvailable() {
                let result = try InMemoryStageMajorRunner(status: { phase, detail in
                    try? writeStatus(phase: phase, modelName: "in_memory_stage_major", detail: detail)
                    updateStatus("\(phase): \(detail ?? "")")
                }).run()
                statusModel = result.model
                data = try encoder.encode(result)
            } else {
                let result = try runSuite()
                statusModel = result.results.first?.model
                data = try encoder.encode(result)
            }
            let json = String(data: data, encoding: .utf8) ?? "{}"
            print("COREML_BENCH_RESULT_BEGIN")
            print(json)
            print("COREML_BENCH_RESULT_END")
            log.info("COREML_BENCH_RESULT \(json, privacy: .public)")

            let url = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
                .appendingPathComponent("coreml_bench_result.json")
            try data.write(to: url, options: .atomic)
            log.info("COREML_BENCH_RESULT_FILE \(url.path, privacy: .public)")
            try? writeStatus(phase: "suite_finished", modelName: statusModel)
            updateStatus(json)
        } catch {
            let message = "COREML_BENCH_ERROR \(error)"
            print(message)
            log.error("\(message, privacy: .public)")
            try? writeStatus(phase: "error", modelName: nil, detail: "\(error)")
            updateStatus(message)
        }
    }

    private func runSuite() throws -> BenchSuiteResult {
        let specs = [
            BenchSpec(
                modelName: "roformer_layer_pairs_0_3",
                layerPairs: 4,
                inputShape: [1, 938, 62, 256],
                warmup: 1,
                iterations: 1
            ),
        ]
        var results: [BenchResult] = []
        for spec in specs {
            updateStatus("Running \(spec.modelName)...")
            results.append(try runBenchmark(spec: spec))
        }
        return BenchSuiteResult(
            device: UIDevice.current.name,
            systemName: UIDevice.current.systemName,
            systemVersion: UIDevice.current.systemVersion,
            computeUnits: "cpuAndNeuralEngine",
            audioSecondsAssumption: 5.0,
            results: results,
            timestampUnix: Date().timeIntervalSince1970
        )
    }

    private func runBenchmark(spec: BenchSpec) throws -> BenchResult {
        let modelName = spec.modelName
        try? writeStatus(phase: "model_lookup", modelName: modelName)
        guard let modelURL = Bundle.main.url(forResource: modelName, withExtension: "mlmodelc")
            ?? Bundle.main.url(forResource: modelName, withExtension: "mlpackage")
        else {
            throw BenchError.missingModel(modelName)
        }

        let config = MLModelConfiguration()
        config.computeUnits = .cpuAndNeuralEngine
        config.allowLowPrecisionAccumulationOnGPU = false

        try? writeStatus(phase: "compile_started", modelName: modelName)
        let compileStart = now()
        let compiledURL: URL
        if modelURL.pathExtension == "mlmodelc" {
            compiledURL = modelURL
        } else {
            compiledURL = try MLModel.compileModel(at: modelURL)
        }
        let compileMs = elapsedMs(since: compileStart)

        try? writeStatus(phase: "load_started", modelName: modelName, detail: "compile_ms=\(finite(compileMs))")
        let loadStart = now()
        let model = try MLModel(contentsOf: compiledURL, configuration: config)
        let loadMs = elapsedMs(since: loadStart)

        try? writeStatus(phase: "first_prediction_started", modelName: modelName, detail: "load_ms=\(finite(loadMs))")
        let input = try makeInput(shape: spec.inputShape)
        let provider = try MLDictionaryFeatureProvider(dictionary: ["x": MLFeatureValue(multiArray: input)])

        let firstStart = now()
        let firstOutput = try model.prediction(from: provider)
        let firstMs = elapsedMs(since: firstStart)
        _ = firstOutput.featureNames.count

        try? writeStatus(phase: "warmup_started", modelName: modelName, detail: "first_prediction_ms=\(finite(firstMs))")
        let warmup = spec.warmup
        for _ in 0..<warmup {
            _ = try model.prediction(from: provider)
        }

        try? writeStatus(phase: "timed_iterations_started", modelName: modelName)
        let iterations = spec.iterations
        var samples: [Double] = []
        samples.reserveCapacity(iterations)
        for _ in 0..<iterations {
            let start = now()
            let output = try model.prediction(from: provider)
            samples.append(elapsedMs(since: start))
            _ = output.featureNames.count
        }

        let sorted = samples.sorted()
        let totalAudioSeconds = 5.0
        let mean = samples.reduce(0, +) / Double(samples.count)
        let retainedDelaySeconds = 10.0
        try? writeStatus(phase: "retained_delay_started", modelName: modelName, detail: "delay_sec=\(retainedDelaySeconds)")
        Thread.sleep(forTimeInterval: retainedDelaySeconds)
        try? writeStatus(phase: "retained_prediction_started", modelName: modelName)
        let retainedStart = now()
        _ = try model.prediction(from: provider)
        let retainedPredictionMs = elapsedMs(since: retainedStart)
        return BenchResult(
            model: modelName,
            layerPairs: spec.layerPairs,
            computeUnits: "cpuAndNeuralEngine",
            input: BenchInput(name: "x", shape: spec.inputShape, dtype: "float32"),
            audioSecondsAssumption: totalAudioSeconds,
            compileMs: finite(compileMs),
            loadMs: finite(loadMs),
            firstPredictionMs: finite(firstMs),
            warmupIterations: warmup,
            iterations: iterations,
            warmPredictionMs: WarmPredictionStats(
                mean: finite(mean),
                p50: finite(percentile(sorted, 0.50)),
                p95: finite(percentile(sorted, 0.95)),
                min: finite(sorted.first ?? 0),
                max: finite(sorted.last ?? 0)
            ),
            warmPredictionRtf: finite(mean / (totalAudioSeconds * 1000.0)),
            retainedDelaySeconds: retainedDelaySeconds,
            retainedPredictionMs: finite(retainedPredictionMs),
            retainedPredictionRtf: finite(retainedPredictionMs / (totalAudioSeconds * 1000.0)),
            timestampUnix: Date().timeIntervalSince1970
        )
    }

    private func makeInput(shape: [Int]) throws -> MLMultiArray {
        let array = try MLMultiArray(shape: shape.map(NSNumber.init(value:)), dataType: .float32)
        let count = array.count
        let ptr = array.dataPointer.bindMemory(to: Float32.self, capacity: count)
        for index in 0..<count {
            ptr[index] = Float32((index % 251) - 125) / 512.0
        }
        return array
    }

    private func documentsURL() -> URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
    }

    private func clearPreviousResult() {
        let url = documentsURL().appendingPathComponent("coreml_bench_result.json")
        try? FileManager.default.removeItem(at: url)
    }

    private func writeStatus(phase: String, modelName: String?, detail: String? = nil) throws {
        var fields: [String] = [
            "\"phase\":\"\(phase)\"",
            "\"timestamp_unix\":\(Date().timeIntervalSince1970)",
        ]
        if let modelName {
            fields.append("\"model\":\"\(modelName)\"")
        }
        if let detail {
            fields.append("\"detail\":\"\(detail.replacingOccurrences(of: "\"", with: "\\\""))\"")
        }
        let json = "{\(fields.joined(separator: ","))}\n"
        let url = documentsURL().appendingPathComponent("coreml_bench_status.json")
        try Data(json.utf8).write(to: url, options: .atomic)
    }

    private func now() -> DispatchTime {
        DispatchTime.now()
    }

    private func elapsedMs(since start: DispatchTime) -> Double {
        let nanos = DispatchTime.now().uptimeNanoseconds - start.uptimeNanoseconds
        return Double(nanos) / 1_000_000.0
    }

    private func percentile(_ sorted: [Double], _ p: Double) -> Double {
        guard !sorted.isEmpty else { return 0 }
        let index = min(sorted.count - 1, max(0, Int((Double(sorted.count - 1) * p).rounded())))
        return sorted[index]
    }

    private func finite(_ value: Double) -> Double {
        value.isFinite ? value : -1
    }
}

struct RealAudioSegmentedRunner {
    typealias Status = (_ phase: String, _ detail: String?) -> Void

    private let status: Status

    init(status: @escaping Status) {
        self.status = status
    }

    static func assetsAvailable() -> Bool {
        assetDirectory() != nil
    }

    static func assetDirectory() -> URL? {
        Bundle.main.url(forResource: "manifest", withExtension: "json", subdirectory: "real_audio_chunks")
            .map { $0.deletingLastPathComponent() }
        ?? Bundle.main.url(forResource: "manifest", withExtension: "json", subdirectory: "real_audio_chunks_smoke")
            .map { $0.deletingLastPathComponent() }
    }

    func run() throws -> RealAudioSegmentedResult {
        guard let assetDir = Self.assetDirectory() else {
            throw BenchError.missingModel("real_audio_chunks/manifest.json")
        }
        status("real_audio_manifest", assetDir.path)
        let manifestURL = assetDir.appendingPathComponent("manifest.json")
        let manifest = try JSONDecoder().decode(RealAudioManifest.self, from: Data(contentsOf: manifestURL))
        let tensorURL = assetDir.appendingPathComponent(manifest.tensorFile)

        let config = MLModelConfiguration()
        config.computeUnits = .cpuAndNeuralEngine
        let stageSpecs = [
            RealStageSpec(name: "first_2_segments", input: "input_flat", output: "h1"),
            RealStageSpec(name: "roformer_layer_pairs_2_3", input: "x", output: nil),
            RealStageSpec(name: "roformer_layer_pairs_4_5", input: "x", output: nil),
            RealStageSpec(name: "roformer_layer_pairs_6_7", input: "x", output: nil),
            RealStageSpec(name: "roformer_layer_pairs_8_9", input: "x", output: nil),
            RealStageSpec(name: "roformer_layer_pairs_10_11", input: "x", output: nil),
            RealStageSpec(name: "tail_pipeline", input: "h10", output: "complex_mask"),
        ]

        var chunkResults: [RealAudioChunkResult] = []
        var totalLoadMs = 0.0
        var stageLoadMs: [String: Double] = Dictionary(uniqueKeysWithValues: stageSpecs.map { ($0.name, 0.0) })
        var totalStageMs: [String: Double] = Dictionary(uniqueKeysWithValues: stageSpecs.map { ($0.name, 0.0) })
        var lastOutputShape: [Int] = []
        let pipelineStart = DispatchTime.now()

        for chunkIndex in 0..<manifest.chunks {
            status("real_audio_chunk_started", "\(chunkIndex + 1)/\(manifest.chunks)")
            let chunkStart = DispatchTime.now()
            let inputHandle = try FileHandle(forReadingFrom: tensorURL)
            let input = try readChunk(handle: inputHandle, index: chunkIndex, manifest: manifest)
            try inputHandle.close()
            var current = input
            var stageTimings: [RealStageTiming] = []

            for spec in stageSpecs {
                guard let url = Bundle.main.url(forResource: spec.name, withExtension: "mlmodelc") else {
                    throw BenchError.missingModel(spec.name)
                }
                let loadStart = DispatchTime.now()
                status("real_audio_load_started", spec.name)
                let model = try MLModel(contentsOf: url, configuration: config)
                let loadMs = elapsedMs(since: loadStart)
                totalLoadMs += loadMs
                stageLoadMs[spec.name, default: 0.0] += loadMs
                status("real_audio_load_finished", "\(spec.name) ms=\(finite(loadMs))")

                let provider = try MLDictionaryFeatureProvider(dictionary: [
                    spec.input: MLFeatureValue(multiArray: current)
                ])
                let start = DispatchTime.now()
                let output = try model.prediction(from: provider)
                let ms = elapsedMs(since: start)
                totalStageMs[spec.name, default: 0.0] += ms
                current = try outputArray(from: output, preferredName: spec.output)
                stageTimings.append(RealStageTiming(stage: spec.name, ms: finite(ms)))
            }

            lastOutputShape = current.shape.map { $0.intValue }
            chunkResults.append(
                RealAudioChunkResult(
                    index: chunkIndex,
                    startSample: manifest.starts[chunkIndex],
                    totalMs: finite(elapsedMs(since: chunkStart)),
                    stages: stageTimings
                )
            )
        }

        let pipelineMs = elapsedMs(since: pipelineStart)
        return RealAudioSegmentedResult(
            model: "real_audio_segmented_coreml",
            audio: manifest.audio,
            audioSeconds: manifest.audioSeconds,
            sampleRate: manifest.sampleRate,
            chunks: manifest.chunks,
            inputShape: manifest.inputShape,
            outputShape: lastOutputShape,
            tensorFile: manifest.tensorFile,
            loadMs: finite(totalLoadMs),
            stageLoadMs: stageSpecs.map { RealStageTiming(stage: $0.name, ms: finite(stageLoadMs[$0.name] ?? 0.0)) },
            pipelineMs: finite(pipelineMs),
            stageTotalMs: stageSpecs.map { RealStageTiming(stage: $0.name, ms: finite(totalStageMs[$0.name] ?? 0.0)) },
            chunkResults: chunkResults,
            timestampUnix: Date().timeIntervalSince1970
        )
    }

    private func readChunk(handle: FileHandle, index: Int, manifest: RealAudioManifest) throws -> MLMultiArray {
        try readArray(
            handle: handle,
            index: index,
            shape: manifest.inputShape,
            bytesPerChunk: manifest.bytesPerChunk
        )
    }

    private func readArray(
        handle: FileHandle,
        index: Int,
        shape: [Int],
        strides: [Int]? = nil,
        bytesPerChunk: Int
    ) throws -> MLMultiArray {
        try handle.seek(toOffset: UInt64(index * bytesPerChunk))
        let data = try handle.read(upToCount: bytesPerChunk) ?? Data()
        if data.count != bytesPerChunk {
            throw BenchError.missingModel("chunk \(index) bytes \(data.count)/\(bytesPerChunk)")
        }
        if let strides {
            let pointer = UnsafeMutableRawPointer.allocate(
                byteCount: bytesPerChunk,
                alignment: MemoryLayout<Float>.alignment
            )
            data.withUnsafeBytes { src in
                if let base = src.baseAddress {
                    pointer.copyMemory(from: base, byteCount: bytesPerChunk)
                }
            }
            return try MLMultiArray(
                dataPointer: pointer,
                shape: shape.map { NSNumber(value: $0) },
                dataType: .float32,
                strides: strides.map { NSNumber(value: $0) },
                deallocator: { pointer in
                    pointer.deallocate()
                }
            )
        }
        let array = try MLMultiArray(shape: shape.map { NSNumber(value: $0) }, dataType: .float32)
        data.withUnsafeBytes { src in
            if let base = src.baseAddress {
                array.dataPointer.copyMemory(from: base, byteCount: bytesPerChunk)
            }
        }
        return array
    }

    private func writeArray(_ array: MLMultiArray, byteCount: Int, to handle: FileHandle) throws {
        let data = Data(bytes: array.dataPointer, count: byteCount)
        try handle.write(contentsOf: data)
    }

    private func byteCount(shape: [Int]) -> Int {
        shape.reduce(1, *) * MemoryLayout<Float>.size
    }

    private func storageByteCount(shape: [Int], strides: [Int]) -> Int {
        let elements = zip(shape, strides).reduce(1) { partial, item in
            let (dim, stride) = item
            return partial + max(0, dim - 1) * stride
        }
        return elements * MemoryLayout<Float>.size
    }

    private func makeTemporaryTensorURL(stage: String) throws -> URL {
        let documentsURL = try FileManager.default.url(
            for: .documentDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        )
        return documentsURL.appendingPathComponent("real_audio_\(stage)_f32.bin")
    }

    private func outputArray(from output: MLFeatureProvider, preferredName: String?) throws -> MLMultiArray {
        if let preferredName, let array = output.featureValue(for: preferredName)?.multiArrayValue {
            return array
        }
        for name in output.featureNames {
            if let array = output.featureValue(for: name)?.multiArrayValue {
                return array
            }
        }
        throw BenchError.missingModel("multiarray output")
    }

    private func elapsedMs(since start: DispatchTime) -> Double {
        let nanos = DispatchTime.now().uptimeNanoseconds - start.uptimeNanoseconds
        return Double(nanos) / 1_000_000.0
    }

    private func finite(_ value: Double) -> Double {
        value.isFinite ? value : -1
    }
}

struct InMemoryStageMajorRunner {
    typealias Status = (_ phase: String, _ detail: String?) -> Void

    private let status: Status

    init(status: @escaping Status) {
        self.status = status
    }

    static func assetsAvailable() -> Bool {
        RealAudioSegmentedRunner.assetsAvailable()
    }

    func run() throws -> RealAudioSegmentedResult {
        guard let assetDir = RealAudioSegmentedRunner.assetDirectory() else {
            throw BenchError.missingModel("real_audio_chunks/manifest.json")
        }
        status("in_memory_stage_major_manifest", assetDir.path)
        let manifestURL = assetDir.appendingPathComponent("manifest.json")
        let manifest = try JSONDecoder().decode(RealAudioManifest.self, from: Data(contentsOf: manifestURL))
        let tensorURL = assetDir.appendingPathComponent(manifest.tensorFile)
        let config = MLModelConfiguration()
        config.computeUnits = .cpuAndNeuralEngine
        let stageSpecs = [
            RealStageSpec(name: "first_2_segments", input: "input_flat", output: "h1"),
            RealStageSpec(name: "roformer_layer_pairs_2_3", input: "x", output: nil),
            RealStageSpec(name: "roformer_layer_pairs_4_5", input: "x", output: nil),
            RealStageSpec(name: "roformer_layer_pairs_6_7", input: "x", output: nil),
            RealStageSpec(name: "roformer_layer_pairs_8_9", input: "x", output: nil),
            RealStageSpec(name: "roformer_layer_pairs_10_11", input: "x", output: nil),
            RealStageSpec(name: "tail_pipeline", input: "h10", output: "complex_mask"),
        ]

        let pipelineStart = DispatchTime.now()
        let windowSize = 4
        var totalLoadMs = 0.0
        var stageLoadMs: [String: Double] = Dictionary(uniqueKeysWithValues: stageSpecs.map { ($0.name, 0.0) })
        var totalStageMs: [String: Double] = Dictionary(uniqueKeysWithValues: stageSpecs.map { ($0.name, 0.0) })
        var perChunkStageTimings = Array(repeating: [RealStageTiming](), count: manifest.chunks)
        var lastOutputShape: [Int] = manifest.inputShape

        for windowStart in stride(from: 0, to: manifest.chunks, by: windowSize) {
            let windowEnd = min(windowStart + windowSize, manifest.chunks)
            status("in_memory_stage_major_window_started", "\(windowStart + 1)-\(windowEnd)/\(manifest.chunks)")
            var tensors: [MLMultiArray] = []
            tensors.reserveCapacity(windowEnd - windowStart)

            for (stageIndex, spec) in stageSpecs.enumerated() {
                let model = try loadModel(name: spec.name, config: config)
                var nextTensors: [MLMultiArray] = []
                nextTensors.reserveCapacity(windowEnd - windowStart)
                let inputHandle = stageIndex == 0 ? try FileHandle(forReadingFrom: tensorURL) : nil
                defer {
                    try? inputHandle?.close()
                }

                for chunkIndex in windowStart..<windowEnd {
                    let inputArray: MLMultiArray
                    if let inputHandle {
                        status(
                            "in_memory_stage_major_read_chunk",
                            "window=\(windowStart + 1)-\(windowEnd) chunk=\(chunkIndex + 1)/\(manifest.chunks)"
                        )
                        inputArray = try readArray(
                            handle: inputHandle,
                            index: chunkIndex,
                            shape: manifest.inputShape,
                            bytesPerChunk: manifest.bytesPerChunk
                        )
                    } else {
                        inputArray = tensors[chunkIndex - windowStart]
                    }

                    let provider = try MLDictionaryFeatureProvider(dictionary: [
                        spec.input: MLFeatureValue(multiArray: inputArray)
                    ])
                    status(
                        "in_memory_stage_major_predict_started",
                        "\(spec.name) window=\(windowStart + 1)-\(windowEnd) chunk=\(chunkIndex + 1)/\(manifest.chunks)"
                    )
                    let start = DispatchTime.now()
                    let output = try model.prediction(from: provider)
                    let ms = elapsedMs(since: start)
                    let outputArray = try self.outputArray(from: output, preferredName: spec.output)
                    nextTensors.append(outputArray)
                    totalStageMs[spec.name, default: 0.0] += ms
                    perChunkStageTimings[chunkIndex].append(RealStageTiming(stage: spec.name, ms: finite(ms)))
                    lastOutputShape = outputArray.shape.map { $0.intValue }
                }

                tensors = nextTensors
                try? writeCheckpointResult(makeResult(
                    manifest: manifest,
                    stageSpecs: stageSpecs,
                    totalLoadMs: totalLoadMs,
                    stageLoadMs: stageLoadMs,
                    totalStageMs: totalStageMs,
                    perChunkStageTimings: perChunkStageTimings,
                    outputShape: lastOutputShape,
                    pipelineStart: pipelineStart
                ))
            }

            tensors.removeAll(keepingCapacity: false)
            status("in_memory_stage_major_window_finished", "\(windowStart + 1)-\(windowEnd)/\(manifest.chunks)")
        }

        return makeResult(
            manifest: manifest,
            stageSpecs: stageSpecs,
            totalLoadMs: totalLoadMs,
            stageLoadMs: stageLoadMs,
            totalStageMs: totalStageMs,
            perChunkStageTimings: perChunkStageTimings,
            outputShape: lastOutputShape,
            pipelineStart: pipelineStart
        )

        func loadModel(name: String, config: MLModelConfiguration) throws -> MLModel {
            guard let url = Bundle.main.url(forResource: name, withExtension: "mlmodelc") else {
                throw BenchError.missingModel(name)
            }
            status("in_memory_stage_major_load_started", name)
            let start = DispatchTime.now()
            let model = try MLModel(contentsOf: url, configuration: config)
            let ms = elapsedMs(since: start)
            totalLoadMs += ms
            stageLoadMs[name, default: 0.0] += ms
            status("in_memory_stage_major_load_finished", "\(name) ms=\(finite(ms))")
            return model
        }
    }

    private func makeResult(
        manifest: RealAudioManifest,
        stageSpecs: [RealStageSpec],
        totalLoadMs: Double,
        stageLoadMs: [String: Double],
        totalStageMs: [String: Double],
        perChunkStageTimings: [[RealStageTiming]],
        outputShape: [Int],
        pipelineStart: DispatchTime
    ) -> RealAudioSegmentedResult {
        let chunkResults = perChunkStageTimings.enumerated().map { index, timings in
            RealAudioChunkResult(
                index: index,
                startSample: manifest.starts[index],
                totalMs: finite(timings.reduce(0.0) { $0 + $1.ms }),
                stages: timings
            )
        }
        return RealAudioSegmentedResult(
            model: "real_audio_in_memory_stage_major_coreml",
            audio: manifest.audio,
            audioSeconds: manifest.audioSeconds,
            sampleRate: manifest.sampleRate,
            chunks: manifest.chunks,
            inputShape: manifest.inputShape,
            outputShape: outputShape,
            tensorFile: manifest.tensorFile,
            loadMs: finite(totalLoadMs),
            stageLoadMs: stageSpecs.map { RealStageTiming(stage: $0.name, ms: finite(stageLoadMs[$0.name] ?? 0.0)) },
            pipelineMs: finite(elapsedMs(since: pipelineStart)),
            stageTotalMs: stageSpecs.map { RealStageTiming(stage: $0.name, ms: finite(totalStageMs[$0.name] ?? 0.0)) },
            chunkResults: chunkResults,
            timestampUnix: Date().timeIntervalSince1970
        )
    }

    private func writeCheckpointResult(_ result: RealAudioSegmentedResult) throws {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(result)
        let url = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("coreml_bench_result.json")
        try data.write(to: url, options: .atomic)
    }

    private func readArray(
        handle: FileHandle,
        index: Int,
        shape: [Int],
        bytesPerChunk: Int
    ) throws -> MLMultiArray {
        try handle.seek(toOffset: UInt64(index * bytesPerChunk))
        let data = try handle.read(upToCount: bytesPerChunk) ?? Data()
        if data.count != bytesPerChunk {
            throw BenchError.missingModel("chunk \(index) bytes \(data.count)/\(bytesPerChunk)")
        }
        let array = try MLMultiArray(shape: shape.map { NSNumber(value: $0) }, dataType: .float32)
        data.withUnsafeBytes { src in
            if let base = src.baseAddress {
                array.dataPointer.copyMemory(from: base, byteCount: bytesPerChunk)
            }
        }
        return array
    }

    private func outputArray(from output: MLFeatureProvider, preferredName: String?) throws -> MLMultiArray {
        if let preferredName, let value = output.featureValue(for: preferredName)?.multiArrayValue {
            return value
        }
        for name in output.featureNames {
            if let value = output.featureValue(for: name)?.multiArrayValue {
                return value
            }
        }
        throw BenchError.missingModel("output")
    }

    private func elapsedMs(since start: DispatchTime) -> Double {
        Double(DispatchTime.now().uptimeNanoseconds - start.uptimeNanoseconds) / 1_000_000.0
    }

    private func finite(_ value: Double) -> Double {
        value.isFinite ? value : -1
    }
}

struct SpillValidationRunner {
    typealias Status = (_ phase: String, _ detail: String?) -> Void

    private let status: Status

    init(status: @escaping Status) {
        self.status = status
    }

    static func assetsAvailable() -> Bool {
        RealAudioSegmentedRunner.assetsAvailable()
    }

    func run() throws -> SpillValidationResult {
        guard let assetDir = RealAudioSegmentedRunner.assetDirectory() else {
            throw BenchError.missingModel("real_audio_chunks/manifest.json")
        }
        let manifestURL = assetDir.appendingPathComponent("manifest.json")
        let manifest = try JSONDecoder().decode(RealAudioManifest.self, from: Data(contentsOf: manifestURL))
        let tensorURL = assetDir.appendingPathComponent(manifest.tensorFile)
        let config = MLModelConfiguration()
        config.computeUnits = .cpuAndNeuralEngine

        status("spill_validation_read_input", "chunk=0")
        let inputHandle = try FileHandle(forReadingFrom: tensorURL)
        let input = try readArray(
            handle: inputHandle,
            index: 0,
            shape: manifest.inputShape,
            bytesPerChunk: manifest.bytesPerChunk
        )
        try inputHandle.close()

        var firstModel: MLModel? = try loadModel(name: "first_2_segments", config: config)
        let firstProvider = try MLDictionaryFeatureProvider(dictionary: [
            "input_flat": MLFeatureValue(multiArray: input)
        ])
        status("spill_validation_predict_started", "first_2_segments")
        let firstOutput = try firstModel!.prediction(from: firstProvider)
        let hiddenDirect = try outputArray(from: firstOutput, preferredName: "h1")
        firstModel = nil
        let hiddenShape = hiddenDirect.shape.map { $0.intValue }
        let hiddenStrides = hiddenDirect.strides.map { $0.intValue }
        let hiddenBytes = storageByteCount(shape: hiddenShape, strides: hiddenStrides)

        status(
            "spill_validation_hidden_ready",
            "shape=\(hiddenShape) strides=\(hiddenStrides) bytes=\(hiddenBytes)"
        )
        let hiddenSpilled = try makeContiguousCopy(hiddenDirect)
        let hiddenCompare = compareArrays(
            validationScope: "first_2_segments_h1_contiguous_restage",
            referenceName: "direct_h1",
            candidateName: "contiguous_h1",
            lhs: hiddenDirect,
            rhs: hiddenSpilled,
            tolerance: 0
        )

        let pairModel = try loadModel(name: "roformer_layer_pairs_2_3", config: config)
        let directPairProvider = try MLDictionaryFeatureProvider(dictionary: [
            "x": MLFeatureValue(multiArray: hiddenDirect)
        ])
        status("spill_validation_predict_started", "roformer_layer_pairs_2_3 direct")
        let directStart = DispatchTime.now()
        let directPairOutput = try pairModel.prediction(from: directPairProvider)
        let directMs = elapsedMs(since: directStart)
        let directPairArray = try outputArray(from: directPairOutput, preferredName: nil)
        let directCheckpoint = SpillValidationRow(
            validationScope: "roformer_layer_pairs_2_3_direct_completed",
            referenceName: "direct_pair_prediction",
            candidateName: "checkpoint",
            tolerance: 0,
            maxAbs: 0,
            meanAbs: 0,
            numChecked: 0,
            validationOk: true,
            validationFailureStage: nil,
            validationFailureReason: nil
        )
        try? writeCheckpointResult(SpillValidationResult(
            model: "spill_validation_first2_to_pair23_contiguous_checkpoint",
            audio: manifest.audio,
            chunks: manifest.chunks,
            inputShape: manifest.inputShape,
            hiddenShape: hiddenShape,
            directPairPredictionMs: finite(directMs),
            spilledPairPredictionMs: -1,
            validations: [hiddenCompare, directCheckpoint],
            timestampUnix: Date().timeIntervalSince1970
        ))

        let spilledPairProvider = try MLDictionaryFeatureProvider(dictionary: [
            "x": MLFeatureValue(multiArray: hiddenSpilled)
        ])
        status("spill_validation_predict_started", "roformer_layer_pairs_2_3 contiguous_restage")
        let spilledStart = DispatchTime.now()
        let spilledPairOutput = try pairModel.prediction(from: spilledPairProvider)
        let spilledMs = elapsedMs(since: spilledStart)
        let spilledPairArray = try outputArray(from: spilledPairOutput, preferredName: nil)

        let pairCompare = compareArrays(
            validationScope: "roformer_layer_pairs_2_3_direct_vs_contiguous_restage_input",
            referenceName: "direct_input_output",
            candidateName: "contiguous_restage_input_output",
            lhs: directPairArray,
            rhs: spilledPairArray,
            tolerance: 0.001
        )

        return SpillValidationResult(
            model: "spill_validation_first2_to_pair23",
            audio: manifest.audio,
            chunks: manifest.chunks,
            inputShape: manifest.inputShape,
            hiddenShape: hiddenShape,
            directPairPredictionMs: finite(directMs),
            spilledPairPredictionMs: finite(spilledMs),
            validations: [hiddenCompare, pairCompare],
            timestampUnix: Date().timeIntervalSince1970
        )
    }

    private func writeCheckpointResult(_ result: SpillValidationResult) throws {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.prettyPrinted, .sortedKeys]
        let data = try encoder.encode(result)
        let url = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("coreml_bench_result.json")
        try data.write(to: url, options: .atomic)
    }

    private func loadModel(name: String, config: MLModelConfiguration) throws -> MLModel {
        guard let url = Bundle.main.url(forResource: name, withExtension: "mlmodelc") else {
            throw BenchError.missingModel(name)
        }
        status("spill_validation_load_started", name)
        let model = try MLModel(contentsOf: url, configuration: config)
        status("spill_validation_load_finished", name)
        return model
    }

    private func makeContiguousCopy(_ array: MLMultiArray) throws -> MLMultiArray {
        guard array.dataType == .float32 else {
            throw BenchError.missingModel("expected float32 hidden tensor, got \(array.dataType.rawValue)")
        }
        let shape = array.shape.map { $0.intValue }
        let sourceStrides = array.strides.map { $0.intValue }
        let copy = try MLMultiArray(shape: array.shape, dataType: .float32)
        let destinationStrides = copy.strides.map { $0.intValue }
        let source = array.dataPointer.bindMemory(to: Float32.self, capacity: max(1, storageByteCount(shape: shape, strides: sourceStrides) / MemoryLayout<Float32>.stride))
        let destination = copy.dataPointer.bindMemory(to: Float32.self, capacity: copy.count)
        let rank = shape.count
        for linearIndex in 0..<copy.count {
            var remaining = linearIndex
            var sourceOffset = 0
            var destinationOffset = 0
            if rank > 0 {
                for axis in stride(from: rank - 1, through: 0, by: -1) {
                    let dimension = shape[axis]
                    let coordinate = dimension > 0 ? remaining % dimension : 0
                    remaining = dimension > 0 ? remaining / dimension : 0
                    sourceOffset += coordinate * sourceStrides[axis]
                    destinationOffset += coordinate * destinationStrides[axis]
                }
            }
            destination[destinationOffset] = source[sourceOffset]
        }
        return copy
    }

    private func compareArrays(
        validationScope: String,
        referenceName: String,
        candidateName: String,
        lhs: MLMultiArray,
        rhs: MLMultiArray,
        tolerance: Double
    ) -> SpillValidationRow {
        let lhsCount = lhs.count
        let rhsCount = rhs.count
        guard lhsCount == rhsCount else {
            return SpillValidationRow(
                validationScope: validationScope,
                referenceName: referenceName,
                candidateName: candidateName,
                tolerance: tolerance,
                maxAbs: Double.infinity,
                meanAbs: Double.infinity,
                numChecked: min(lhsCount, rhsCount),
                validationOk: false,
                validationFailureStage: validationScope,
                validationFailureReason: "count mismatch \(lhsCount) != \(rhsCount)"
            )
        }
        let lhsPtr = lhs.dataPointer.assumingMemoryBound(to: Float.self)
        let rhsPtr = rhs.dataPointer.assumingMemoryBound(to: Float.self)
        var maxAbs = 0.0
        var sumAbs = 0.0
        for index in 0..<lhsCount {
            let diff = abs(Double(lhsPtr[index] - rhsPtr[index]))
            maxAbs = max(maxAbs, diff)
            sumAbs += diff
        }
        let meanAbs = lhsCount > 0 ? sumAbs / Double(lhsCount) : 0.0
        let ok = maxAbs <= tolerance
        return SpillValidationRow(
            validationScope: validationScope,
            referenceName: referenceName,
            candidateName: candidateName,
            tolerance: tolerance,
            maxAbs: maxAbs,
            meanAbs: meanAbs,
            numChecked: lhsCount,
            validationOk: ok,
            validationFailureStage: ok ? nil : validationScope,
            validationFailureReason: ok ? nil : "max_abs \(maxAbs) > tolerance \(tolerance)"
        )
    }

    private func readArray(
        handle: FileHandle,
        index: Int,
        shape: [Int],
        strides: [Int]? = nil,
        bytesPerChunk: Int
    ) throws -> MLMultiArray {
        try handle.seek(toOffset: UInt64(index * bytesPerChunk))
        let data = try handle.read(upToCount: bytesPerChunk) ?? Data()
        if data.count != bytesPerChunk {
            throw BenchError.missingModel("chunk \(index) bytes \(data.count)/\(bytesPerChunk)")
        }
        if let strides {
            let pointer = UnsafeMutableRawPointer.allocate(
                byteCount: bytesPerChunk,
                alignment: MemoryLayout<Float>.alignment
            )
            data.withUnsafeBytes { src in
                if let base = src.baseAddress {
                    pointer.copyMemory(from: base, byteCount: bytesPerChunk)
                }
            }
            return try MLMultiArray(
                dataPointer: pointer,
                shape: shape.map { NSNumber(value: $0) },
                dataType: .float32,
                strides: strides.map { NSNumber(value: $0) },
                deallocator: { pointer in
                    pointer.deallocate()
                }
            )
        }
        let array = try MLMultiArray(shape: shape.map { NSNumber(value: $0) }, dataType: .float32)
        data.withUnsafeBytes { src in
            if let base = src.baseAddress {
                array.dataPointer.copyMemory(from: base, byteCount: bytesPerChunk)
            }
        }
        return array
    }

    private func writeArray(_ array: MLMultiArray, byteCount: Int, to handle: FileHandle) throws {
        let data = Data(bytes: array.dataPointer, count: byteCount)
        try handle.write(contentsOf: data)
    }

    private func outputArray(from output: MLFeatureProvider, preferredName: String?) throws -> MLMultiArray {
        if let preferredName, let array = output.featureValue(for: preferredName)?.multiArrayValue {
            return array
        }
        for name in output.featureNames {
            if let array = output.featureValue(for: name)?.multiArrayValue {
                return array
            }
        }
        throw BenchError.missingModel("multiarray output")
    }

    private func byteCount(shape: [Int]) -> Int {
        shape.reduce(1, *) * MemoryLayout<Float>.size
    }

    private func storageByteCount(shape: [Int], strides: [Int]) -> Int {
        let elements = zip(shape, strides).reduce(1) { partial, item in
            let (dim, stride) = item
            return partial + max(0, dim - 1) * stride
        }
        return elements * MemoryLayout<Float>.size
    }

    private func makeTemporaryTensorURL(stage: String) throws -> URL {
        let documentsURL = try FileManager.default.url(
            for: .documentDirectory,
            in: .userDomainMask,
            appropriateFor: nil,
            create: true
        )
        return documentsURL.appendingPathComponent("real_audio_\(stage)_f32.bin")
    }

    private func elapsedMs(since start: DispatchTime) -> Double {
        let nanos = DispatchTime.now().uptimeNanoseconds - start.uptimeNanoseconds
        return Double(nanos) / 1_000_000.0
    }

    private func finite(_ value: Double) -> Double {
        value.isFinite ? value : -1
    }
}

struct RealStageSpec {
    let name: String
    let input: String
    let output: String?
}

struct RealLoadedStage {
    let spec: RealStageSpec
    let model: MLModel
    let loadMs: Double
}

struct RealAudioManifest: Codable {
    let audio: String
    let audioSeconds: Double
    let sampleRate: Int
    let chunks: Int
    let starts: [Int]
    let inputShape: [Int]
    let tensorFile: String
    let bytesPerChunk: Int

    enum CodingKeys: String, CodingKey {
        case audio
        case audioSeconds = "audio_seconds"
        case sampleRate = "sample_rate"
        case chunks
        case starts
        case inputShape = "input_shape"
        case tensorFile = "tensor_file"
        case bytesPerChunk = "bytes_per_chunk"
    }
}

struct RealAudioSegmentedResult: Codable {
    let model: String
    let audio: String
    let audioSeconds: Double
    let sampleRate: Int
    let chunks: Int
    let inputShape: [Int]
    let outputShape: [Int]
    let tensorFile: String
    let loadMs: Double
    let stageLoadMs: [RealStageTiming]
    let pipelineMs: Double
    let stageTotalMs: [RealStageTiming]
    let chunkResults: [RealAudioChunkResult]
    let timestampUnix: Double

    enum CodingKeys: String, CodingKey {
        case model
        case audio
        case audioSeconds = "audio_seconds"
        case sampleRate = "sample_rate"
        case chunks
        case inputShape = "input_shape"
        case outputShape = "output_shape"
        case tensorFile = "tensor_file"
        case loadMs = "load_ms"
        case stageLoadMs = "stage_load_ms"
        case pipelineMs = "pipeline_ms"
        case stageTotalMs = "stage_total_ms"
        case chunkResults = "chunk_results"
        case timestampUnix = "timestamp_unix"
    }
}

struct RealAudioChunkResult: Codable {
    let index: Int
    let startSample: Int
    let totalMs: Double
    let stages: [RealStageTiming]

    enum CodingKeys: String, CodingKey {
        case index
        case startSample = "start_sample"
        case totalMs = "total_ms"
        case stages
    }
}

struct RealStageTiming: Codable {
    let stage: String
    let ms: Double
}

struct SpillValidationResult: Codable {
    let model: String
    let audio: String
    let chunks: Int
    let inputShape: [Int]
    let hiddenShape: [Int]
    let directPairPredictionMs: Double
    let spilledPairPredictionMs: Double
    let validations: [SpillValidationRow]
    let timestampUnix: Double

    enum CodingKeys: String, CodingKey {
        case model
        case audio
        case chunks
        case inputShape = "input_shape"
        case hiddenShape = "hidden_shape"
        case directPairPredictionMs = "direct_pair_prediction_ms"
        case spilledPairPredictionMs = "spilled_pair_prediction_ms"
        case validations
        case timestampUnix = "timestamp_unix"
    }
}

struct SpillValidationRow: Codable {
    let validationScope: String
    let referenceName: String
    let candidateName: String
    let tolerance: Double
    let maxAbs: Double
    let meanAbs: Double
    let numChecked: Int
    let validationOk: Bool
    let validationFailureStage: String?
    let validationFailureReason: String?

    enum CodingKeys: String, CodingKey {
        case validationScope = "validation_scope"
        case referenceName = "reference_name"
        case candidateName = "candidate_name"
        case tolerance
        case maxAbs = "max_abs"
        case meanAbs = "mean_abs"
        case numChecked = "num_checked"
        case validationOk = "validation_ok"
        case validationFailureStage = "validation_failure_stage"
        case validationFailureReason = "validation_failure_reason"
    }
}

enum BenchError: Error {
    case missingModel(String)
}

struct BenchSpec {
    let modelName: String
    let layerPairs: Int
    let inputShape: [Int]
    let warmup: Int
    let iterations: Int
}

struct BenchSuiteResult: Codable {
    let device: String
    let systemName: String
    let systemVersion: String
    let computeUnits: String
    let audioSecondsAssumption: Double
    let results: [BenchResult]
    let timestampUnix: Double

    enum CodingKeys: String, CodingKey {
        case device
        case systemName = "system_name"
        case systemVersion = "system_version"
        case computeUnits = "compute_units"
        case audioSecondsAssumption = "audio_seconds_assumption"
        case results
        case timestampUnix = "timestamp_unix"
    }
}

struct BenchResult: Codable {
    let model: String
    let layerPairs: Int
    let computeUnits: String
    let input: BenchInput
    let audioSecondsAssumption: Double
    let compileMs: Double
    let loadMs: Double
    let firstPredictionMs: Double
    let warmupIterations: Int
    let iterations: Int
    let warmPredictionMs: WarmPredictionStats
    let warmPredictionRtf: Double
    let retainedDelaySeconds: Double
    let retainedPredictionMs: Double
    let retainedPredictionRtf: Double
    let timestampUnix: Double

    enum CodingKeys: String, CodingKey {
        case model
        case layerPairs = "layer_pairs"
        case computeUnits = "compute_units"
        case input
        case audioSecondsAssumption = "audio_seconds_assumption"
        case compileMs = "compile_ms"
        case loadMs = "load_ms"
        case firstPredictionMs = "first_prediction_ms"
        case warmupIterations = "warmup_iterations"
        case iterations
        case warmPredictionMs = "warm_prediction_ms"
        case warmPredictionRtf = "warm_prediction_rtf"
        case retainedDelaySeconds = "retained_delay_seconds"
        case retainedPredictionMs = "retained_prediction_ms"
        case retainedPredictionRtf = "retained_prediction_rtf"
        case timestampUnix = "timestamp_unix"
    }
}

struct BenchInput: Codable {
    let name: String
    let shape: [Int]
    let dtype: String
}

struct WarmPredictionStats: Codable {
    let mean: Double
    let p50: Double
    let p95: Double
    let min: Double
    let max: Double
}
