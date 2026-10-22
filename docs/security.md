# 安全模型与边界

| 项目 | 值 |
| --- | --- |
| 适用版本 | v0.1.0 |
| 信任模型 | 本地桌面应用；用户主动打开自己的 VBIOS 文件 |
| 网络 | **无网络访问、无遥测、无自动更新** |
| 最高风险操作 | nvflash 刷写（默认禁用，仅原厂未修改镜像） |
| 关联 | [`risk-model.md`](risk-model.md)、[`architecture.md`](architecture.md)、[`../UPSTREAM.md`](../UPSTREAM.md) |

## 1. 安全不变量（发布阻断）

1. **修改后的镜像签名失效，禁止 nvflash 刷写。** 修改后镜像只能通过 Windows 注册表 override 或 Linux loader 应用。
2. **nvflash 通道只接受原厂未修改镜像**，且必须逐项通过 `risk-model.md` §6.3 的检查；任何失败即拒绝，且不启动子进程。
3. **不打包任何 NVIDIA 固件/ROM/VBIOS 二进制**：仓库与分发包只含本项目代码、文档、图标；`src/nvidia_vbios/` 是解析代码，不含固件数据。
4. **不上传用户 ROM**：应用不联网、不调用云服务、不写遥测；用户文件只在本机内存/磁盘处理。
5. **注册表写入需要管理员权限**：Windows adapter 在非管理员下返回 `ELEVATION_REQUIRED`，不尝试提权。
6. **原文件只读**：打开/编辑/保存全程不修改源 ROM；输出为新文件 + manifest。
7. **所有子进程列表参数 + `shell=False`**：禁止 `shell=True`、`os.system`、字符串拼接命令。
8. **无 NVIDIA 签名能力**：不实现、不提供签名生成、补签、绕过或“让 nvflash 接受修改镜像”。

## 2. 威胁模型

### 2.1 防护目标

- 防止用户误把**修改后镜像**送进 nvflash（会导致签名校验失败或变砖）。
- 防止把**错误型号/错误架构**的镜像应用到另一块 GPU。
- 防止 UI/插件意外获得文件系统、注册表或子进程能力。
- 防止发布包被替换（SHA256SUMS + 构建来源可追溯）。

### 2.2 不在防护范围

- 用户主动在管理员权限下运行恶意修改版二进制。
- 操作系统/驱动/固件供应链被攻破。
- 物理访问、侧信道、DMA 攻击。
- 用户自行用第三方工具修改/刷写。
- NVIDIA 驱动未来移除 override 机制（可用性风险，不是安全漏洞）。

## 3. 数据流与数据最小化

| 数据 | 位置 | 是否离开本机 | 保留 |
| --- | --- | --- | --- |
| 用户 ROM / payload | 用户选择的本地路径、内存 | 否 | 仅用户指定输出目录 |
| ROM SHA-256 | manifest、日志 | 否 | 随输出文件 |
| GPU 型号 / PCI ID / 驱动版本 | 应用面板、日志 | 否 | 仅本地日志 |
| 编辑变更 | manifest JSON | 否 | 随输出文件 |
| 语言/主题 | 进程内设置 | 否 | 仅当前会话（不做账号/云同步） |
| 遥测 | 无 | — | — |

- 日志不记录 ROM 字节内容；只记录路径、SHA-256、设备、结果、错误 code。
- 错误对话框的 `details` 可复制，但由用户决定是否公开；**不要上传真实 VBIOS**。
- 测试 fixture 全部由脚本合成，不含任何真实固件。

## 4. 权限边界

| 操作 | 所需权限 | 实现 |
| --- | --- | --- |
| 打开/编辑/保存 ROM | 普通用户，目标目录可写 | `Path` + 显式新文件检查 |
| Windows 注册表 override | **管理员** | `WindowsPlatform` 注入；非管理员返回 `ELEVATION_REQUIRED` |
| Windows 设备重启 | 管理员 | `pnputil /restart-device`，list 参数 |
| Linux loader 注入 | 由外部 loader 决定（通常 root） | 本项目只生成 payload 与指引，**不 sudo、不提权、不改系统文件** |
| nvflash 刷写 | 管理员/root + 显式 opt-in + 确认词 | `NvflashGuard` 12 项检查；默认 `allow_flash=False` |

## 5. 系统调用与子进程

- 所有系统命令经 `adapters/system/_base.py::SubprocessRunner`：
  - 参数必须是 `list[str]`；
  - `shell=False`；
  - 不拼接用户输入到命令行；
  - 超时与退出码显式处理。
- `tests/apply/test_no_shell_true.py` 全仓 AST 扫描 `shell=True`、`os.system`、字符串命令。
- nvflash 守卫在构造命令**之前**完成文件/哈希/逐字节/会话/校验和/结构/设备/版本/权限/确认/竞态检查；拒绝时 runner 调用次数必须为 0。
- 禁止参数：`--protectoff`、`--erase`、`--force`、`--no-preserve`。

## 6. 文件与路径安全

- 输出采用“新文件”语义：拒绝已存在路径、符号链接、源文件路径；失败回滚本次创建的文件。
- 打开/保存/应用前校验源文件 SHA-256 与首次打开一致，防止文件被替换。
- 刷写前做逐字节比较（不仅比较哈希），执行前再次读取 SHA-256，缩小 TOCTOU 窗口。
- 拖放只接受**恰好一个**本地普通文件；目录、多文件、非 ROM 均拒绝。
- 不跟随符号链接写入；manifest 与 ROM 同目录、同名 `.json`。

## 7. 注册表安全（Windows）

写入位置（仅当前 GPU 的 driver key）：

```text
HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\NNNN
```

写入值：

| 值 | 类型 | 内容 |
| --- | --- | --- |
| `vbios` | REG_BINARY | 单链 VBIOS 镜像 |
| `EnableGpuFirmware` | REG_DWORD | `0x11` |
| `VixLoaderPreviousEnableGpuFirmware` | REG_SZ | 首次 load 前的值，或 `absent` |

- 删除 `romOverride00`–`romOverrideFF`，避免旧 override 残留。
- `dry-run` 默认零写入；真实写入前展示目标键、值类型、字节数、将删除项、将重启设备。
- `unload` 恢复首次 load 前的 `EnableGpuFirmware`，并清理本工具写入的值。
- 不修改 driver key 中的其他值；不写 `romOverride` 以外的系统位置。

## 8. 发布与供应链

- 上游 A/B 以完整 40 位 SHA 固定；vendored 31 文件由 `tests/contract/test_version.py` 逐文件 SHA-256 校验。
- 发布产物附 `SHA256SUMS`；下载后必须校验：

  ```bash
  sha256sum -c SHA256SUMS          # Linux
  Get-FileHash .\vbios-studio-*.exe  # Windows PowerShell，对照 SHA256SUMS
  ```

- CI 从本仓库构建，不使用第三方预编译二进制；Windows 构建需要 MSYS2 UCRT64 + Nuitka（见 `build.yml`）。
- 仓库不得包含 `.rom`/`.bin`/`.exe`/密钥/构建产物；测试 fixture 由脚本生成。
- 许可证：GPL-3.0-or-later；发布包保留 `LICENSE`、`NOTICE.md`、上游版权声明。

## 9. 漏洞与风险报告

- 发现安全问题时，请**不要公开上传真实 VBIOS 或个人信息**；提供：
  - 版本、操作系统、复现步骤；
  - 错误 `code` / `details`；
  - 影响范围（是否涉及注册表写入、文件覆盖、子进程）。
- 高风险问题（任意文件写、命令注入、绕过 nvflash 守卫）应优先修复并加回归测试。
- 本项目不提供漏洞赏金或官方支持；响应尽力而为。

## 10. 已知残余风险

1. **无真实硬件验证**：安全不变量只能证明代码路径，不能证明具体显卡不会因参数组合损坏。
2. **驱动行为变化**：Windows override 依赖 NVIDIA 驱动内部实现，未来驱动可能拒绝或改变行为。
3. **外部 Linux loader**：其安全性/维护状态不由本项目控制。
4. **用户手动绕过**：用户可用其他工具刷写修改镜像；本工具只能保证自身路径。
5. **管理员权限**：拥有管理员权限的恶意程序可绕过本工具的所有保护。
6. **上游解析器漏洞**：恶意构造的 ROM 可能触发上游解析器异常；本项目做边界检查与异常转 `DomainError`，但不能证明零漏洞。
