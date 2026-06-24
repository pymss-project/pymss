# TokenGeneration InferenceError Summary

## 范围

本文件只总结当前已经收敛的这条支线：

- `TokenGeneration.framework`
  `TokenGenerationError.toInferenceError`
- `ModelManagerServices.framework`
  `InferenceError` / `ModelManagerError`
- `TokenGenerationInference.framework`
  `convertToInferenceError`
  与
  `1306 -> 293 -> 1399/1400`
  throw-path

不覆盖 private ANE benchmark / artifact-descriptor / public `_ANEClient` 主线。

## 最终模板

当前 machine-local 证据已经足够把关键 throw-path 写成固定模板：

1. `1306`
   产出 typed error 对 `(X0, X1)`
2. `293`
   使用
   `X0`
   和
   `X8 := X1`
   对目标输出槽做 in-place rebox / slot-fixup
3. `1399/1400`
   作为更普适的 throw / return ABI 收尾 helper，
   消费保存下来的主值副本并把控制流带出当前 async frame

## TokenGeneration.framework

### `TokenGenerationError.toInferenceError`

- 地址：
  `0x274de6890`
- 已确认：
  - 它不是命名噪声，而是活跃函数
  - 末尾通过
    `InferenceError` metadata
    + value witness
    写回结果 enum
  - `0x274de774c`
    已按 Swift ABI 定性为
    `destructiveInjectEnumTag`

### 5 个终态 group -> `InferenceError`

当前高置信映射：

- `0x28F63A450` -> `networkError`
- `0x28F63A468` -> `rateLimited`
- `0x28F63A498` -> `inferenceFailed`
- `0x28F63A4A0` -> `invalidClientData`
- `0x28F63A4A8` -> `operationCancelled`

## ModelManagerServices.framework

### 常量区

- 关键区域：
  `0x25a7739f0..0x25a773a5c`
- 内容：
  - `InferenceError`
  - `Context`
  - 连续 `u32 1..24`

这块区域不再只视为“像 tag 表”，而是已经被真实 consumer 路径支撑。

### 3 条真实 consumer 链

1. `0x25a63e844`
   - `InferenceError` case-name / description 风格 consumer
   - 直接命中
     `invalidClientData`
     `operationCancelled`
     `responseEncodingFailed`
     `operationNotAllowed`
     `assetVersionMismatch`
     等 case-name 字面量

2. `0x25a63f9d4`
   - `InferenceError` error-code / `CustomNSError` 风格 consumer
   - 25-case enum -> 固定整数错误码分发表
   - 关键码表：
     - `invalidClientData -> 2014`
     - `inferenceFailed -> 2008`
     - `rateLimited -> 2011`
     - `networkError -> 2016`
     - `operationCancelled -> 2013`
   - 额外锚点：
     `0x25a645560`
     直接 thunk 到
     `0x25a63f9d4`

3. `0x25a63f4d8`
   - `ModelManagerError -> InferenceError`
     bridge / context rebox consumer
   - 内部可见：
     - `"Received a ModelManagerError wrapping an InferenceError"`
     - `"InferenceError: got unrecognized error %@"`

## TokenGenerationInference.framework

### `convertToInferenceError`

- 地址：
  `0x2750d0990`
- 反编译签名：
  `a1@<X0>, a2@<X8>`

### 三路语义

1. 输入 `Error`
   若能动态投影成
   `TokenGenerationError?`
   - project 到临时位点
   - 拷到另一份临时位点
   - 调 `293`
   - 再销毁临时值

2. 输入若已是
   `InferenceError?`
   - 直接拷到输出
   - 不走 `293`

3. 两者都失败
   - `Swift.CancellationError`
     -> 直接取
     `0x28F63A4A8`
     -> `operationCancelled`
   - generic NSError-like
     -> 组
     `localizedDescription/domain/code/userInfo`
     -> 直接取
     `0x28F63A498`
     -> `inferenceFailed`

### `293` 的当前定性

`293`
不是泛化 payload finalize。

当前最具体结论：

- 它是
  `TokenGenerationError? -> InferenceError`
  专用分支上的 in-place convert / rebox helper
- 它依赖调用者通过
  `X8`
  传入目标输出槽 / 间接返回位点

## `1306 -> 293 -> 1399`

### 已直接证实的两条关键路径

#### compileAdapter

`0x275165d04..0x275165d3c`

- `BL 1306`
- `MOV X25, X0`
- `MOV X8, X1`
- `BL 293`
- `MOV X21, X25`
- `BL 1399`

#### requestStream

`0x2751689e0..0x2751689f4`

- `BL 1306`
- `MOV X27, X0`
- `MOV X8, X1`
- `BL 293`
- `MOV X21, X27`
- `BL 1399`

### 含义

- `1306`
  产出 `(X0, X1)`
- `X0`
  是主 error/result 值
- `X1`
  是 companion 输出位点 / slot handle
- `293.X8`
  就是 `1306.X1` 的直接转发
- `1399`
  基于保存下来的 `X0` 副本做最终 throw 收尾

## `293` vs `1399/1400`

- `293`
  xref 面更窄：
  主要集中在 typed-error 重封装点
- `1399/1400`
  xref 面更宽：
  覆盖大量普通 decoder / request / stream / wrapper 错误出口

因此：

- `293`
  是窄的 typed-error 中间修复层
- `1399/1400`
  是宽的最终出口层

## 当前剩余价值

继续深挖这条线的高价值工作只剩：

1. 文档清理与摘要收敛
2. 若真的需要，再补
   `ModelManagerServices`
   侧 3 个 consumer 的更正式 Swift / witness 名称

继续追 `__auth_got` / `__auth_stubs` / fixups / 完美原始符号名，
当前收益很低。
