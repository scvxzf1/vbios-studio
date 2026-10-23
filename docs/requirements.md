# VBIOS Studio 需求契约（冻结）

| 项目 | 值 |
| --- | --- |
| 仓库名 | `vbios-studio` |
| 文档版本 | `1.0.5-frozen`（ApplyPort 操作清单能力补充） |
| 冻结日期 | 2026-10-22 |
| 状态 | **FROZEN**（需求冻结；变更须走 §9 流程） |
| 负责人 | architect |
| 上游基线 | `nvidia-vbios-vix-editor@1f8ee665bd175bd9ede367e6d15308f837bd987b`、`nvidia-windows-vbios-vix-loader@ec7bdfe317d3a52de160d17d2bb80ff20813596e`（见 `UPSTREAM.md`） |
| 关联文档 | `docs/risk-model.md`、`UPSTREAM.md`、`README.md` |

## 0. 文档约定

- **MUST / SHOULD / MAY**：MUST 为发布阻断项；SHOULD 为发布前应完成项，未完成须在 `docs/reviews/verification-report.md` 记录理由；MAY 为可选。
- **验收口径**：每条需求以「可执行命令 + 可观察结果」或「可在 GUI 中复现的操作序列」描述，不接受“界面美观”“体验良好”这类不可判定表述。
- **实验性（experimental）**：沿用上游字段 `evidence` 中的实验性标记；表示**没有硬件验证证据**，不表示“可以随便改”。风险等级与实验性标记是两条正交属性，实验性字段最低为 T2，涉及电压/电流/保护阈值/高级电源行为的一律 T3。完整模型见 `docs/risk-model.md`。
- **原厂未修改镜像（pristine image）**：用户从自有显卡导出、在 VBIOS Studio 中**未产生任何 staged change**、且 SHA-256 与导入时记录一致的镜像。任何字节变化（含仅改校验和平衡字节）都使其成为“修改后镜像”。
- **修改后镜像（modified image）**：与原厂镜像存在任意字节差异的镜像。其 NVIDIA 密码学签名保持原样但已不匹配，**永远不得进入 nvflash 写通道**。
- **应用（apply）**：通过 Windows 注册表 override 或 Linux loader 让驱动加载修改后镜像；**不写显卡 flash 芯片**。
- **刷写（flash）**：调用 nvflash 等工具写显卡 flash 芯片；本工具只在“原厂未修改镜像”且逐项校验通过时提供该通道。

## 1. 产品定义

**VBIOS Studio** 是基于 Panchovix 两个 GPL-3.0 上游项目构建的 GTK4 图形化 NVIDIA VBIOS 编辑与应用套件：离线打开/检查 VBIOS 镜像，按 T0–T3 风险分级编辑字段（含实验性字段），生成新的 VBIOS 文件及 loader payload，并通过 Windows 注册表 override 或 Linux loader **受控地**让修改生效。中英双语、Windows/Linux 双平台发布。

### 1.1 目标用户

- 需要在自有显卡上调整功耗/电压/电流/风扇/时钟策略的高级用户与研究者。
- 需要审计 ROM 结构、比对两份 ROM、保存可复现修改记录的技术用户。

### 1.2 支持矩阵（首版 v0.1.0）

| 架构家族 | 只读检查 | 字段编辑 | 应用（override） | 刷写（仅原厂） | 证据状态 |
| --- | --- | --- | --- | --- | --- |
| Blackwell GB20x（GB202/203/205/206） | 支持 | 支持（按上游审核字段） | 支持 | 默认关闭 | 上游有用户报告；**本项目未做真机验证** |
| Ada AD10x | 支持 | 支持（按上游审核字段，部分实验性） | 支持（`ada-relocated-v2` payload） | 默认关闭 | 上游仅少量型号；**本项目未验证** |
| Ampere GA10x（GA102–GA107） | 支持 | 支持（全部字段上游标注实验性） | 支持（`ampere-relocated-v1` payload） | 默认关闭 | 上游仅少量型号；**本项目未验证** |
| Turing TU10x/TU11x | 支持 | 支持（实验性） | 支持（需 `turing-e0-end-v1` 兜底） | 默认关闭 | 上游仅 RTX 2080 Ti 等少量报告；**本项目未验证** |
| GA100（A100/A30/A800） | 结构报告 | **不支持** | **不支持** | **不支持** | 明确排除 |
| 未识别架构/损坏镜像 | 只读结构报告 | 禁止 | 禁止 | 禁止 | 明确降级 |

> **本项目的支持矩阵描述的是代码路径与上游证据，不是本项目完成的硬件验证。** 本项目未在真实 GPU 上执行过任何编辑、override 或刷写；发布说明与 README 必须显著声明这一点。

### 1.3 首版非目标

不做在线 ROM 库、不做自动超频、不做显卡识别以外的设备管理、不做 NVIDIA 签名生成/绕过、不做 GA100、不做 macOS/32 位、不做无人值守刷写。

## 2. 全局安全不变量（发布阻断）

| ID | 不变量 | 验证方式 |
| --- | --- | --- |
| INV-01 | **修改后镜像禁止经 nvflash 刷写**；代码路径必须在任何子进程启动前硬拒绝。 | `tests/apply/test_nvflash_guard.py` 负向用例 + 全仓字符串/调用扫描 |
| INV-02 | nvflash 写通道**只接受原厂未修改镜像**，且必须逐项通过 `docs/risk-model.md` §6.3 的校验清单。 | 守卫单元测试 + 集成测试（fake runner 断言零调用） |
| INV-03 | 主要应用路径只能是 Windows 注册表 override / Linux loader override，**不写 flash 芯片**。 | 适配器测试 + 文档审查 |
| INV-04 | 打开、编辑、保存全过程**绝不修改用户原文件**；输出必须是新文件。 | 前后 SHA-256 断言 + 只读文件测试 |
| INV-05 | 上游 `src/nvidia_vbios/` 为只读镜像，**不得改动一行**；自有代码只在 `src/vbios_studio/`。 | `tests/contract/test_version.py` 逐文件哈希 |
| INV-06 | 所有子进程调用必须列表参数、`shell=False`；禁止 `os.system`、`shell=True`、字符串拼接命令。 | 全仓静态扫描测试 |
| INV-07 | T3 字段默认隐藏；解锁后每次写入必须二次确认，取消不得产生任何 staged change。 | GUI 单元测试 + 手工验收 |
| INV-08 | 仓库不得提交任何真实 `.rom`/`.bin`/`.exe`/密钥/构建产物；测试 fixture 由脚本合成。 | `tools/prepush_audit.py` + 卫生元测试 |

## 3. 功能需求（6 组）

### FR-1 打开、拖放与只读检查

**目的**：让用户以最少步骤安全地载入 ROM，并在任何写入前看清“这是什么、由哪些镜像组成、校验和是否平衡”。

| ID | 需求（MUST） |
| --- | --- |
| FR-1.1 | 顶部工具栏与菜单提供“打开…”，使用 GTK4 `FileDialog`；文件过滤器包含 `*.rom`、`*.bin` 与“所有文件”；键盘快捷键 `Ctrl+O`。 |
| FR-1.2 | 主窗口接受拖放 `Gdk.FileList`：仅接受**恰好一个**普通文件；目录、多文件、空列表、非 ROM 文件均给出可复制的双语错误对话框，进程不得崩溃。 |
| FR-1.3 | 打开后展示文件信息卡片：产品名、PCI ID（vendor:device）、VBIOS 版本、板号、构建日期、文件大小、SHA-256、识别出的架构/格式。 |
| FR-1.4 | 展示镜像链列表：序号、类型（legacy/EFI/NPDS data/0x70 等）、文件偏移、大小、8-bit 校验和、是否平衡（`Sum % 256 == 0`）、是否 last。 |
| FR-1.5 | 打开即只读解析并缓存字段目录；未识别架构/损坏镜像降级为只读结构报告并禁用编辑与“应用”，给出原因，不崩溃。 |
| FR-1.6 | 最近一次打开的原文件 SHA-256 进入会话状态，供保存/应用阶段校验原文件未被替换。 |
| FR-1.7 | 空状态显示拖放提示与“打开文件…”按钮（GUI-09）。 |

**验收口径**

1. 用 `pytest -q tests/gui/test_drop_target.py`：合法合成 ROM 触发载入；目录/多文件/非 ROM 分别给出 `DROP_NOT_A_FILE`、`DROP_MULTIPLE_FILES`、`UNRECOGNIZED_ROM`，且窗口对象仍可交互。
2. `xvfb-run -a python -m vbios_studio.ui --selftest` 退出码 0，并在临时目录合成 ROM 上完成“打开→信息卡片→镜像链列表”快照断言。
3. 对损坏 ROM 打开后，字段编辑区为空、应用按钮 disabled、错误信息可复制；退出码 0（不崩溃）。
4. 打开前后原文件 SHA-256 一致（`sha256sum` 断言）。
5. 手工验收：`Ctrl+O` 与工具栏“打开”走同一 controller 命令，无重复实现。

**Out of scope**：从网络下载 ROM；自动从本机 GPU 读取 VBIOS（首版只读文件）；解析未审核的新架构字段；修复损坏镜像；自动猜测用户想打开哪份 ROM。

### FR-2 图形化编辑与风险分级呈现

**目的**：把“能改什么、改了多危险、当前改了什么”在一屏内讲清楚，并让高危/实验性字段默认不可见。

| ID | 需求（MUST） |
| --- | --- |
| FR-2.1 | 字段目录来自上游 adapter；每个字段展示：稳定 key、本地化名称、当前值、单位、允许范围、工厂默认值（若有）、原始偏移（若有）、风险等级徽章、实验性徽章、可编辑性、证据说明。 |
| FR-2.2 | 字段按 T0–T3 分组呈现；T3 默认隐藏。用户须在“设置 → 实验性功能”完成风险确认后才显示 T3；T3 每次写入前弹出二次确认（字段、旧值→新值、风险说明、勾选“我已理解风险”并输入确认词），取消则零变更。 |
| FR-2.3 | 字段区支持「表格视图 ↔ 表单视图」切换。表格列固定为：字段、当前值、单位、范围、默认值、风险徽章、原始偏移；列宽可调、可排序。 |
| FR-2.4 | 搜索框 + 三个独立过滤开关（仅已修改 / 仅实验性 T3 / 仅当前分区）+ 命中计数；搜索匹配 key、中英文名称、说明。 |
| FR-2.5 | 撤销/重做至少 20 步；快捷键 `Ctrl+Z`、`Ctrl+Y`、`Ctrl+Shift+Z`；打开新 ROM 时清空栈；撤销必须恢复字段值与“已修改”标记。 |
| FR-2.6 | 预设 profile：把一组字段改动保存为带 `schema_version` 的 JSON（含单位、期望架构/格式、每项风险等级）；可套用到另一份 ROM；架构/格式不符、字段不存在、越界时**整体拒绝且零部分写入**。 |
| FR-2.7 | 双 ROM 差异视图：字段级（相同/不同/仅左/仅右）与镜像级（偏移、大小、校验和、逐镜像差异计数）；只读，不可从差异视图直接写入。 |
| FR-2.8 | 编辑仅发生在内存 staged 状态；任何 T3 字段在未解锁状态下不可见且不可写；T0 只读字段不可编辑。 |
| FR-2.9 | 每次变更即时本地校验（类型、范围、ordering group、依赖字段 `depends_on`），错误显示在字段行内并阻止保存。 |
| FR-2.10 | 风险配色统一：T0 灰 `#6B7280`、T1 蓝 `#2563EB`、T2 橙 `#D97706`、T3 红 `#DC2626`；不得用颜色作为唯一信息载体（同时有文字徽章）。 |

**验收口径**

1. `pytest -q tests/domain/test_risk_registry.py`：`docs/risk-model.md` 中所有字段键在代码注册表中存在且等级一致（文档-代码一致性）。
2. T3 字段未解锁时 `field.visible == False` 且 `set_value()` 被拒绝；解锁并取消确认后，staged changes 数量为 0。
3. 连续 20 次编辑后连续撤销 20 次，字段值与初始快照逐项相等；重做 20 次恢复终态。
4. 预设跨架构套用返回 `PROFILE_ARCH_MISMATCH`，输出 ROM 不存在、staged changes 不变。
5. 差异视图对“两份只差一个功耗字段”的合成 ROM 报 1 个字段差异，镜像级报对应镜像差异；对相同文件全部 `identical`。
6. 搜索“power”+ 仅已修改过滤，命中计数等于表格可见行数并随编辑实时更新。

**Out of scope**：批量脚本化编辑/宏；网页版；绕过确认的“静默应用”；自动超频算法；导入未审核的第三方预设而不校验；编辑上游标记为 `editable=false` 的字段；修改字段编码/单位语义。

### FR-3 生成新 VBIOS

**目的**：把 staged 变更写成**新文件**，保证逐镜像校验和平衡、未改镜像字节不变、可追溯、可交给 loader。

| ID | 需求（MUST） |
| --- | --- |
| FR-3.1 | “另存为…”仅允许新路径；拒绝覆盖已存在文件、符号链接、源文件路径；输出 ROM 与 `<name>.rom.json` manifest 原子发布（失败回滚本次创建的文件）。 |
| FR-3.2 | manifest 至少含：`schema_version`、工具版本、上游 pin、源文件 SHA-256、输出 SHA-256、时间戳、逐字段变更（key、旧值、新值、单位、风险等级）、逐镜像校验和修复记录、`modified: true`。 |
| FR-3.3 | 对每张被修改镜像重算 8-bit 校验和，只允许改写该镜像**最后一个字节**（或上游审核过的尾部平衡字节）；未修改镜像必须逐字节不变。 |
| FR-3.4 | 导出 loader payload 沿用上游 `normalize` 语义：Blackwell 单 bank；Ada `ada-relocated-v2`；Ampere `ampere-relocated-v1`；Turing `turing-e0-end-v1` 兜底；文件名为 `<name>-loader.bin`（Turing 兜底 `<name>-loader-e0end.bin`）。 |
| FR-3.5 | 保存前必须通过：字段 bounds/ordering/depends_on、架构/格式识别、镜像链完整性、逐镜像校验和、输出路径安全检查；任一失败则不写任何文件并返回结构化错误。 |
| FR-3.6 | 生成阶段不访问 GPU、注册表、nvflash；纯离线文件操作。 |
| FR-3.7 | 保存成功后 UI 明确提示“这是修改后镜像，禁止用 nvflash 刷写；只能通过 loader override 应用”。 |

**验收口径**

1. 合成 ROM 改动 1 个字段后保存：被改镜像 `Sum % 256 == 0`；其余镜像与原文件逐字节相等（`cmp`/逐字节断言）；原文件 SHA-256 前后不变。
2. manifest 字段齐全且输出 SHA-256 与文件一致；`modified: true`；风险等级与字段注册表一致。
3. 负向测试至少 3 条：篡改签名区/结构、跨架构字段、越界值——均返回错误、无输出文件、无部分 manifest。
4. Ada/Ampere/Turing 合成样本分别产出规定 representation 的 payload；Blackwell 产出单 bank payload。
5. 目标路径已存在时返回 `OUTPUT_EXISTS` 且不覆盖；源路径作为目标返回 `SOURCE_AS_OUTPUT`。

**Out of scope**：生成 NVIDIA 签名或让修改镜像“可刷写”；生成可直接分发的完整 flash dump；批量转换目录；自动上传/云备份；修复损坏的原厂镜像；把修改后镜像伪装成原厂镜像。

### FR-4 应用与刷写（受控）

**目的**：让修改生效，同时把“写注册表/写 flash”的边界写死，任何越界在代码层硬拒绝。

| ID | 需求（MUST） |
| --- | --- |
| FR-4.1 | Windows 适配器写 `HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\NNNN` 的 `vbios`（REG_BINARY）、`EnableGpuFirmware=0x11`（REG_DWORD）、`VixLoaderPreviousEnableGpuFirmware`（REG_SZ，首次 load 保存，含 `absent`）；删除 `romOverride00`–`romOverrideFF`；flush + 回读；通过 `pnputil /restart-device` 重启设备。 |
| FR-4.2 | 所有写操作先 `--dry-run` 预览：展示目标键、值类型、字节数、将删除的项、将重启的设备；dry-run 零写入。 |
| FR-4.3 | `unload` 删除 `vbios`/`romOverride*`，把 `EnableGpuFirmware` 还原为首次 load 前的值（`absent` 则删除），删除 `VixLoaderPreviousEnableGpuFirmware`，并重启设备。 |
| FR-4.4 | Linux 适配器只探测 `nvidia-linux-vbios-vix-loader` 是否存在、生成 payload 与可复制的安装/配置指引；**不得**自行 `sudo`、提权或修改系统文件。 |
| FR-4.5 | nvflash 通道仅接受原厂未修改镜像，且必须逐项通过 §6.3 清单；镜像被修改、校验和不平衡、设备不匹配、nvflash 缺失/版本未知、无管理员权限，任一不满足即拒绝且**不启动任何子进程**。 |
| FR-4.6 | 应用/刷写面板包含：设备状态卡片（GPU 型号、PCI 总线、驱动版本、当前 override 状态）、dry-run 预览、执行、Verify、还原；所有写操作二次确认（显示将写入的注册表项/命令）。 |
| FR-4.7 | 应用前校验 payload 与当前 ROM 的对应关系（SHA-256、PCI ID、镜像链），不匹配拒绝；应用后提供 Verify：读取驱动实际运行的 VBIOS 镜像并与存储的 override 逐字节比较。 |
| FR-4.8 | 所有系统调用经 `ports` 抽象，列表参数、`shell=False`；无权限、键不存在、设备重启失败等返回结构化错误与建议，不抛裸异常。 |
| FR-4.9 | 应用成功后写入本地审计日志（时间、GPU、payload SHA-256、注册表键、结果）；日志不含用户 ROM 内容。 |

**验收口径**

1. 假注册表后端：dry-run 调用后写计数为 0；真实 load 写入的值与上游 loader 协议逐项一致；回读不一致时返回 `READBACK_MISMATCH`。
2. `unload` 在“首次 load 前 `EnableGpuFirmware` 存在=0x11”“不存在”“存在其他值”三种前置状态下均正确还原（含删除）。
3. 刷写守卫 3 条负向测试：镜像被修改过 → `REFUSE_MODIFIED_IMAGE`；校验和不平衡 → `REFUSE_BAD_CHECKSUM`；nvflash 未找到 → `NVFLASH_NOT_FOUND`；三者 fake runner 调用次数均为 0。
4. 全仓扫描禁止 `shell=True`、`os.system`、`subprocess.*(..., shell=True)`；子进程参数均为 `list[str]`。
5. 非管理员运行 load 返回 `ELEVATION_REQUIRED` 及“以管理员身份运行”建议，进程不崩溃。
6. Verify 对“运行镜像 == override”“不同”“无 override”分别返回 `override-active`、`override-not-active`、`no-override`（与上游协议一致）。

**Out of scope**：自动刷写/一键刷写；绕过或重签 NVIDIA 签名；修改 flash 芯片永久区/序列号；自动提权/自动 sudo；无备份应用；GA100/虚拟机/云 GPU；承诺驱动未来版本仍支持 override；在 Linux 上自动安装 loader 包。

### FR-5 中英双语、主题与跨平台打包

| ID | 需求（MUST） |
| --- | --- |
| FR-5.1 | 全部用户可见文案走 gettext；首发语言 `en` 与 `zh_CN`，msgid 集合完全一致，无缺失翻译；代码中无硬编码可见文案。 |
| FR-5.2 | 语言可运行时切换（无需重启），选择持久化；默认跟随系统 locale（`zh_*` → 中文，其余 → 英文）。 |
| FR-5.3 | 主题跟随系统浅/深色，并可手动切换；风险徽章在两种主题下对比度满足 WCAG AA。 |
| FR-5.4 | Linux 发布 `vbios-studio-<ver>-linux-x86_64.tar.gz`，内含 GUI 启动器与 CLI；Windows 发布单文件 `vbios-studio-<ver>-windows-x86_64.exe`（自带 GTK4，onefile），首次启动解包不联网。 |
| FR-5.5 | 构建在 GitHub Actions `ubuntu-*` 与 `windows-latest` 上完成；产物附 `SHA256SUMS`；构建脚本本地可复现（`tools/build_local.sh --check`）。 |
| FR-5.6 | README 至少包含 3 张界面截图（主窗口、字段表格/风险徽章、应用面板），文件位于 `docs-assets/screenshots/`，由自动化 UI 截图流程生成，不得手工伪造界面。 |
| FR-5.7 | 无障碍：全部控件可 Tab 遍历、有 accessible label；快捷键可在“帮助 → 快捷键”查看；错误对话框可选中复制。 |

**验收口径**

1. `pytest -q tests/i18n/test_catalog.py`：`en` 与 `zh_CN` 的 msgid 集合差集为空；UI 模块扫描无硬编码中文/英文可见文案（白名单仅日志与内部标识）。
2. `LANG=zh_CN.UTF-8 xvfb-run -a python -m vbios_studio.ui --lang zh_CN --selftest` 与 `--lang en` 均退出码 0；切换后主窗口所有可见文本变化。
3. `tools/build_local.sh --check` 退出码 0；CI 两个平台 job 均成功；产物名与 §1.2 一致；`sha256sum -c SHA256SUMS` 通过。
4. README 中 3 个 `<img>` 路径存在（占位阶段允许文件缺失但路径必须在 `docs-assets/screenshots/` 且由自动化 UI 截图流程生成）。
5. `gtk4` accessibility inspector 抽查：工具栏 8 个按钮均有 accessible label，Tab 顺序从工具栏→导航→字段区→日志。

**Out of scope**：首发支持西语/日语等其他语言；macOS/ARM Windows/32 位；代码签名证书与 SmartScreen 信誉；自动更新器；应用商店/包管理器分发；像素级品牌设计。

### FR-6 上游同步、文档与发布

| ID | 需求（MUST） |
| --- | --- |
| FR-6.1 | `src/nvidia_vbios/` 是上游 editor 仓库在 pin SHA 的**逐字节只读镜像**；任何本地修改视为发布阻断。 |
| FR-6.2 | `UPSTREAM.md` 记录两个上游仓库 URL、pin 的 40 位 commit SHA、版本、日期、许可证，以及可复制的 pin 校验命令。 |
| FR-6.3 | 上游同步流程：单独分支/PR、更新 `UPSTREAM.md` 与 submodule/vendor 清单、跑 parity 与全量静态测试、记录变更文件与结果；冲突不得用“覆盖本地”解决。 |
| FR-6.4 | 文档齐全：`architecture.md`、`file-tree.md`、`risk-model.md`、`testing.md`、`upstream-sync.md`、`i18n.md`、`security.md`、`faq.md`、`reviews/verification-report.md`、`prepush-audit.md`。 |
| FR-6.5 | 质量闸门：`ruff check`、`ruff format --check`、`mypy --strict`、`lint-imports`、`pytest` 全部退出码 0；每条检查有“故意违反必须失败”的元测试。 |
| FR-6.6 | 仓库卫生：无 `.rom`/`.bin`/`.exe`/`.env`/密钥/构建产物/大于 1 MB 文件；`.gitignore` 覆盖；`tools/prepush_audit.py` 输出 PASS。 |
| FR-6.7 | 公开 GitHub 仓库名 `vbios-studio`，GPL-3.0-or-later LICENSE + NOTICE（上游归属、非 NVIDIA 官方、商标）；Release `v0.1.0` 附 Linux/Windows 产物与 `SHA256SUMS`。 |
| FR-6.8 | README 与 RELEASE_NOTES 顶部显著包含“测试不完全 / 未在真实硬件验证”声明；不得夸大测试覆盖。 |

**验收口径**

1. `cd src/nvidia_vbios && git rev-parse HEAD`（或 vendor 清单哈希）等于 `UPSTREAM.md` 中的 SHA；`tests/contract/test_version.py` 逐文件哈希一致。
2. `grep -E 'https://github.com/Panchovix/(nvidia-vbios-vix-editor|nvidia-windows-vbios-vix-loader)' UPSTREAM.md` 命中 2 个 URL；每个 pin 为 40 位 hex。
3. `ruff check . && ruff format --check . && mypy --strict src && lint-imports && pytest -q` 全部退出码 0（记录在 `docs/reviews/verification-report.md`）。
4. `python tools/prepush_audit.py` 结论 PASS；`git ls-files | grep -Ei '\.(rom|bin|exe)$'` 为空。
5. `gh repo view <owner>/vbios-studio --json visibility` 返回 `PUBLIC`；Release 附件可下载且 `sha256sum -c` 通过。
6. README 首个屏幕内出现“测试不完全”和“未在真实硬件验证”两个短语。

**Out of scope**：自动合并上游冲突；发布到 PyPI/Flathub;微软商店；硬件测试农场；NVIDIA 官方认证；上游作者背书；自动生成发布公告。

## 4. GUI 基线 M1（强约束，10 项）

> 来源：用户明确要求“GUI 不能简陋”。以下 10 项是 v0.1.0 的**发布阻断项**，由 GTK 界面实现、静态测试检查、全量验收与独立评审确认。任何一项缺失不得发布。

| ID | 要求 | 验收口径 | 对应 |
| --- | --- | --- | --- |
| GUI-01 | 顶部工具栏：打开 / 另存为 / 撤销 / 重做 / 搜索 / 语言 / 主题 / 帮助 | 8 个入口全部可点击且有 tooltip/快捷键；搜索聚焦 `Ctrl+F`；语言/主题菜单可操作 | FR-1/2/5 |
| GUI-02 | 左侧导航分区 + 文件信息卡片（产品名、PCI ID、BIOS 版本、镜像链列表：序号/类型/大小/8bit 校验和是否平衡） | 打开合成 ROM 后卡片 6 项信息齐全；镜像链行数与解析结果一致；校验和列显示 balanced/unbalanced | FR-1 |
| GUI-03 | 字段区支持「表格视图 ↔ 表单视图」切换；表格列：字段、当前值、单位、范围、默认值、风险徽章、原始偏移 | 切换后同一字段值双向同步；表格 7 列齐全且可排序；表单视图按分区折叠 | FR-2 |
| GUI-04 | 搜索 + 三个过滤开关（仅已修改 / 仅实验性 T3 / 仅当前分区）+ 命中计数 | 组合过滤结果与计数正确；清空搜索恢复；无结果时显示空态文案 | FR-2 |
| GUI-05 | 撤销/重做 ≥20 步，`Ctrl+Z` / `Ctrl+Y` / `Ctrl+Shift+Z` | 25 次编辑后连续撤销 20 次值正确；快捷键与按钮行为一致；新开 ROM 清栈 | FR-2 |
| GUI-06 | 预设 profile：一组改动存 JSON，可套用到另一份 ROM（架构不符拒绝且无部分写入） | 导出 JSON 含 schema/架构/字段/风险；套用成功字段一致；跨架构返回错误且零变更 | FR-2 |
| GUI-07 | 双 ROM 差异视图（字段级 + 镜像级） | 打开两份 ROM 后并列展示差异；相同/不同/仅左/仅右分类正确；镜像级差异计数正确 | FR-2 |
| GUI-08 | 应用/刷写面板：设备状态卡片、dry-run 预览、执行与还原，写操作二次确认 | 状态卡片 4 项齐全；dry-run 显示目标键/字节数；执行前有确认对话框；还原可恢复 | FR-4 |
| GUI-09 | 空状态引导（拖放提示）、统一可复制的错误对话框、帮助菜单快捷键表 | 无 ROM 时显示拖放提示；所有错误走同一 dialog 组件且可复制；快捷键表与实现一致 | FR-1/5 |
| GUI-10 | 无障碍：全部可 Tab 遍历、有 accessible label；风险配色 T0 灰 / T1 蓝 / T2 橙 / T3 红 | Tab 顺序完整无陷阱；控件 accessible name 非空；4 种徽章颜色与文档一致且非唯一编码 | FR-2/5 |

**GUI 验收总口径**：`xvfb-run -a python -m vbios_studio.ui --selftest` 退出码 0；`pytest -q tests/gui` 全绿；人工按上表逐项走查并记录在 `docs/reviews/verification-report.md`。**没有真实硬件不构成跳过 GUI 验收的理由。**

## 5. 非功能需求

| ID | 要求 | 验收 |
| --- | --- | --- |
| NFR-01 | 分层：`domain`（纯逻辑）→ `ports`（抽象）← `adapters`（上游/注册表/loader/nvflash）；`ui` 只依赖 `ports`；`app` 组合根可依赖全部 | `lint-imports` ≥4 条契约；`ui`/`domain`/`ports` 不出现 `gi`/`winreg`/`subprocess` |
| NFR-02 | 任何单个 `.py` 文件 ≤ 400 行；单函数 ≤ 60 行（SHOULD） | `tests/contract/test_file_sizes.py` |
| NFR-03 | 每个包有 `__init__.py` 与模块 docstring；`docs/file-tree.md` 与真实树一致 | `tests/contract/test_docs_tree.py` |
| NFR-04 | 打开 1 MB 内 ROM ≤ 2 s（不含 GTK 启动）；字段搜索 ≤ 100 ms | 基准测试记录 |
| NFR-05 | 所有错误可结构化（code/message/context/suggestion），UI 可复制 | 单元测试 |
| NFR-06 | 日志不含 ROM 字节、密钥、用户名；默认 INFO，`--debug` 才详细 | 日志扫描测试 |
| NFR-07 | 无网络访问；运行时不下载任何内容 | 依赖/代码扫描 |
| NFR-08 | 可复现构建：锁定依赖版本，CI 与本地脚本一致 | `tools/build_local.sh --check` |
| NFR-09 | 文档中文为主，命令/字段/错误码保留英文；关键术语中英对照 | 文档审查 |
| NFR-10 | 代码注释与 docstring 使用英文；用户文案走 i18n | `ruff`/审查 |

## 6. README 结构（冻结大纲）

README 必须按以下顺序与要求组织；文档负责人负责最终文案，需求基线冻结结构：

1. **标题 + 一句话定位**：`VBIOS Studio`。
2. **⚠️ 显著声明（首屏，标题下第一块）**：`测试不完全 / 未在真实硬件验证` 加粗警告，说明本项目未在真实 GPU 上验证、上游证据不等于本项目验证、可能损坏硬件。
3. **徽章/状态**：CI、许可证、版本（占位）。
4. **截图（≥3 张）**：`docs-assets/screenshots/01-main-window.png`、`02-fields-risk.png`、`03-apply-panel.png`，每张有中文图注（自动化生成）。
5. **功能一览（逐条对应 GUI-01–GUI-10）**：10 条，一条一句话，不得合并省略。
6. **风险分级 T0–T3**：摘要表 + 链接 `docs/risk-model.md`；说明 T3 默认隐藏、二次确认。
7. **安全边界（醒目）**：修改后镜像禁止 nvflash；只通过 Windows 注册表/Linux loader override；刷写仅原厂未修改镜像且逐项校验。
8. **支持矩阵**：架构 × 检查/编辑/应用/刷写 × 证据状态，明确“未验证”。
9. **安装**：Windows 单文件 exe、Linux tar.gz、源码运行要求；`SHA256SUMS` 校验命令。
10. **快速开始**：打开/拖放 → 查看镜像链 → 编辑（示例为 T2 字段）→ 另存为 → 应用 dry-run → 应用/还原。
11. **上游关系与 GPL 继承**：两个上游 URL + pin + GPL-3.0-or-later + NOTICE + 非 NVIDIA 官方。
12. **测试与已知限制**：测试矩阵摘要、未覆盖项（真实硬件、Windows 实机、各厂商机型差异）、跳过的用例。
13. **文档索引**：architecture/file-tree/risk-model/testing/upstream-sync/i18n/security/faq。
14. **贡献与开发**：质量闸门命令。
15. **许可证与免责声明**：GPL-3.0-or-later、无担保、使用风险自负。

## 7. 全局 Out of scope（首版）

- 任何形式的 NVIDIA 签名生成、伪造、绕过或“让修改镜像通过 nvflash 校验”。
- 自动刷写、批量刷写、无人值守刷写、远程刷写。
- 自动提权/自动 sudo/静默修改系统。
- 捆绑或分发任何 NVIDIA VBIOS/固件/驱动二进制。
- 上传用户 ROM 到任何服务器；遥测。
- GA100、数据中心 GPU、虚拟机/云 GPU、macOS、32 位。
- 承诺任何具体超频结果、功耗结果或硬件安全。
- 替代 NVIDIA 官方工具或提供官方支持。

## 8. 追溯矩阵

| 需求组 | 承接实现 | 静态验证 | 最终验收 |
| --- | --- | --- | --- |
| FR-1 打开/拖放/检查 | 骨架与契约、GTK 界面 | GUI/拖放测试 | 全量验收、独立评审 |
| FR-2 编辑/风险分级 | 骨架与契约、核心引擎、GTK 界面 | 风险注册表/文档一致性 | 全量验收、独立评审 |
| FR-3 生成新 VBIOS | 核心引擎 | 校验和/字节保持测试 | 全量验收 |
| FR-4 应用/刷写 | 应用与刷写适配器 | nvflash 守卫/子进程扫描 | 全量验收、独立评审 |
| FR-5 双语/打包 | GTK 界面、CI/CD、GUI 丰富度 | i18n 完整性 | 全量验收、发布后审计 |
| FR-6 上游/文档/发布 | 骨架与契约、文档、仓库整理、发布 | 卫生/文档树 | 全量验收、发布后审计 |
| GUI-01–GUI-10 | GTK 界面 | GUI 静态检查 | 全量验收、独立评审 |

## 9. 变更控制

1. 本文件冻结后，任何范围/验收口径变更必须：新增 `docs/requirements.md` 末尾“变更记录”条目（日期、变更人、原因、影响任务），并由 captain 批准。
2. 删除或降低安全不变量（§2）与 T3 门槛属于**破坏性变更**，必须由 reviewer 复核并在 `docs/reviews/verification-report.md` 记录。
3. 字段风险等级调整必须同步 `docs/risk-model.md` 与代码注册表，否则文档一致性测试失败。

### 变更记录

| 日期 | 版本 | 变更 | 原因 |
| --- | --- | --- | --- |
| 2026-10-22 | 1.0.0-frozen | 初版冻结；并入 GUI M1 基线 10 项 | 需求冻结；用户要求 GUI 不得简陋 |
| 2026-10-23 | 1.0.1-frozen | 附录 A 的 FieldDiff/ImageDiff 改为 GUI 丰富度冻结结构（`changed` / `kind,size,equal`），并修正测试路径引用；以 `docs/architecture.md` §5.1 为准；生产 Diff/Profile 接线由集成接线实现 | 骨架/界面实现与需求冻结契约对齐 |
| 2026-10-23 | 1.0.2-frozen | 清理公开文档中的内部任务编号，改写为面向读者的阶段/角色描述；不改变需求、风险等级或验收契约 | 文档可读性修复 |
| 2026-10-23 | 1.0.3-frozen | 修正 NFR-02 测试文件名单复数笔误（`test_file_size.py` → `test_file_sizes.py`），并同步 README/testing 的可复现计数；不改变任何契约条文 | 计数同步，不改变契约 |
| 2026-10-23 | 1.0.4-frozen | 代码冻结后重新测量并同步 README/testing 计数（pytest 205、UI 18、mypy 77、msgid 282），不改变任何契约条文 | 计数同步，不改变契约 |
| 2026-10-23 | 1.0.5-frozen | architecture 的 ApplyPort 契约表补充只读 `describe_operations(action)`：操作清单与真实写入同源，作为确认正文唯一事实来源；端口能力补充，不改变安全语义与现有需求条文 | 确认正文与实际写入同源 |

## 附录 A：UI Ports 契约（骨架阶段冻结输入）

> 来源：GUI 的接口需求（避免界面与丰富度返工）。骨架阶段必须按此命名落地；如需改名，先在团队内确认并更新本附录。UI **只依赖 ports + domain DTO**，不 import adapters、不做 IO/校验。

### A.1 模块路径与 Protocol 名

| 模块 | 内容 | 允许依赖 |
| --- | --- | --- |
| `src/vbios_studio/domain/models.py` | 全部 DTO（`@dataclass(frozen=True)` / `Enum`） | 仅标准库 |
| `src/vbios_studio/domain/errors.py` | `DomainError`、错误码常量 | 仅标准库 |
| `src/vbios_studio/ports/editor.py` | `EditorPort`（Protocol） | domain |
| `src/vbios_studio/ports/diff.py` | `DiffPort` | domain |
| `src/vbios_studio/ports/profile.py` | `ProfilePort` | domain |
| `src/vbios_studio/ports/apply.py` | `ApplyPort` | domain |

禁止：`ports` import `gi`、`adapters`、`ui`；`domain` import `gi`/文件系统/注册表/`subprocess`。由 `lint-imports` 强制。

### A.2 冻结 DTO（字段名不得随意变更）

```python
# domain/models.py
RiskLevel = Literal["T0", "T1", "T2", "T3"]

@dataclass(frozen=True)
class ImageSnapshot:
    index: int
    kind: str                 # legacy / efi / npds-data / npds-70 ...
    offset: int
    size: int
    checksum_ok: bool
    is_last: bool

@dataclass(frozen=True)
class SectionSnapshot:
    id: str                   # info/power/voltage/current/clocks/fans/memory/apply/log
    title: str                # 已本地化
    order: int

@dataclass(frozen=True)
class FieldSnapshot:
    key: str
    label: str                # 已本地化
    section: str
    unit: str
    current: str | None       # 只读未知为 None；UI 直接显示
    default: str | None
    minimum: str | None
    maximum: str | None
    risk: RiskLevel
    offset: int | None
    editable: bool
    opt_in: bool
    experimental: bool
    description: str          # 已本地化
    depends_on: Mapping[str, Any] | None

@dataclass(frozen=True)
class DocumentSnapshot:
    path: Path
    display_name: str
    sha256: str
    file_size: int
    architecture: str
    product_name: str | None
    pci_id: str | None
    bios_version: str | None
    images: tuple[ImageSnapshot, ...]
    sections: tuple[SectionSnapshot, ...]
    fields: tuple[FieldSnapshot, ...]

@dataclass(frozen=True)
class FieldChange:
    key: str
    label: str
    old: str | None
    new: str
    unit: str
    risk: RiskLevel

@dataclass(frozen=True)
class FieldError:
    key: str
    code: str
    message: str              # 英文诊断；UI 可按 code 本地化
    hint: str

@dataclass(frozen=True)
class EditPreview:
    changed: tuple[FieldChange, ...]
    errors: tuple[FieldError, ...]
    batch_risk: RiskLevel     # 无变更时 T0
    requires_t3_confirmation: bool

@dataclass(frozen=True)
class ManifestView:
    source_sha256: str
    tool_version: str
    upstream_pin: str
    changes: tuple[FieldChange, ...]
    checksum_repairs: tuple[Mapping[str, Any], ...]
    modified: bool

@dataclass(frozen=True)
class SaveResult:
    path: Path
    sha256: str
    manifest: ManifestView
    payload_paths: tuple[Path, ...]

@dataclass(frozen=True)
class FieldDiff:
    key: str
    label: str
    left: str | None
    right: str | None
    risk: RiskLevel
    changed: bool          # diff 表直接渲染；status 仅为派生 property

@dataclass(frozen=True)
class ImageDiff:
    index: int
    kind: str
    size: int
    checksum_left: str | None
    checksum_right: str | None
    equal: bool            # diff 表直接渲染；status 仅为派生 property

@dataclass(frozen=True)
class RomDiff:
    field_diffs: tuple[FieldDiff, ...]
    image_diffs: tuple[ImageDiff, ...]
    summary: Mapping[str, int]

@dataclass(frozen=True)
class DeviceStatus:
    gpu_index: int
    name: str
    pci_id: str
    driver_version: str | None
    override_state: Literal["override-active", "override-not-active", "no-override", "unknown"]
    supports_payload: bool

@dataclass(frozen=True)
class ApplyPreview:
    action: Literal["load", "unload", "flash"]
    target: str               # 注册表键或设备描述
    values: Mapping[str, Any]
    bytes_written: int
    restart_required: bool
    warnings: tuple[str, ...]

@dataclass(frozen=True)
class ApplyResult:
    ok: bool
    state: str
    message: str
    details: Mapping[str, Any]
```

### A.3 Protocol 方法签名

```python
# ports/editor.py
class EditorPort(Protocol):
    def open(self, path: Path) -> DocumentSnapshot: ...
    def stage(self, changes: Mapping[str, str]) -> EditPreview: ...
    def preview(self) -> ManifestView: ...
    def save_as(self, path: Path) -> SaveResult: ...
    def reset(self) -> None: ...

# ports/diff.py
class DiffPort(Protocol):
    def diff_against(self, path: Path) -> RomDiff: ...

# ports/profile.py
class ProfilePort(Protocol):
    def export_changes(self) -> dict[str, Any]: ...
    def apply_profile(self, document: Mapping[str, Any]) -> EditPreview: ...

# ports/apply.py
class ApplyPort(Protocol):
    def device_status(self) -> DeviceStatus: ...
    def dry_run(self) -> ApplyPreview: ...
    def execute(self) -> ApplyResult: ...
    def restore(self) -> ApplyResult: ...

# domain/errors.py
class DomainError(Exception):
    code: str
    message: str             # 英文诊断
    hint: str                # 英文修复建议
    details: Mapping[str, Any]
```

### A.4 行为约束

1. `stage()` 每次返回 domain 校验后的 `EditPreview`；UI 只渲染，不自行计算 bounds/风险。
2. `ProfilePort.apply_profile()` 架构/格式不符时抛 `DomainError(code="PROFILE_ARCH_MISMATCH", ...)`，且**零部分写入**（先整体校验，再一次性 stage）。
3. Undo/redo 栈在 `app`/`ui`；重放必须调用 `EditorPort.reset()` + `stage(all_changes)`，由 domain 重新校验，禁止 UI 直接改 DTO 或绕过校验。
4. `ApplyPort` 的所有写操作先 `dry_run()`；`execute()` 前必须完成二次确认（确认状态由 UI 维护，但 `ApplyPort` 必须在没有有效确认票据时拒绝）。
5. 错误统一 `DomainError`；UI 按 `code` 翻译，禁止在 UI 里拼业务校验文案。
6. DTO 全部不可变；UI 不得就地修改 `DocumentSnapshot`/`FieldSnapshot`。
7. GUI 丰富度所需的 diff/profile/apply 端口必须在骨架阶段就位，不得后补架构。
8. Diff/Profile 的生产适配器（`adapters/diff.py`、`adapters/profile.py`）与 `app/container.py::build_gui_controller()` 由集成接线实现；文档按 GUI 丰富度合同冻结 DTO 字段。
