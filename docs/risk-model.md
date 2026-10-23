# VBIOS Studio 风险模型与刷写安全边界（冻结）

| 项目 | 值 |
| --- | --- |
| 文档版本 | `1.0.0-frozen` |
| 冻结日期 | 2026-10-22 |
| 状态 | **FROZEN**（规范文件；与代码注册表不一致视为发布阻断） |
| 适用版本 | v0.1.1 |
| 关联 | `docs/requirements.md` §2/§3、`UPSTREAM.md`、`docs/security.md`、`src/vbios_studio/domain/risk_registry.py` |

> 本文是**规范**，不是建议。所有字段风险等级、UI 门槛、nvflash 守卫行为都必须与本文逐项一致；`tests/core/test_risk_registry.py` 与 `tests/contract/test_docs_tree.py` 会强制校验。

## 0. 四条安全不变量（最高优先级）

1. **修改后的镜像签名失效。禁止用 nvflash 刷写任何修改后镜像。** 不存在“高级选项”“我知道风险”或环境变量可以绕过这一条。
2. **刷写通道只接受原厂未修改镜像**，且必须逐项通过 §6.3 的全部校验；任一失败即拒绝，且不得启动 nvflash 子进程。
3. **主路径永远是 loader override**：Windows 写驱动注册表 `vbios` / `EnableGpuFirmware`，Linux 用 `nvidia-linux-vbios-vix-loader` 启动注入；两者都不写显卡 flash 芯片。
4. **原文件只读**：打开、编辑、保存、应用任何阶段都不得修改用户原始 ROM；输出必须为新文件。

## 1. T0–T3 定义表

| 等级 | 名称 | 定义 | 硬件损伤可能性 | 可逆性 | 默认 UI 状态 | 交互门槛 | 颜色 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **T0** | 只读 / 信息 | 不写入 VBIOS 字节：解析、展示、校验、差异、语言/主题、保存副本（未应用）。 | 无 | 完全可逆 | 可见 | 无；只读字段不可编辑 | 灰 `#6B7280` |
| **T1** | 低风险 | 只降低电气/热包络，或只增加散热余量；最坏结果是性能下降、驱动重置或重启，不造成永久损伤。 | 极低 | 重启 / unload 即恢复 | 可见 | 单次普通确认（批量应用时列出变更） | 蓝 `#2563EB` |
| **T2** | 中风险 | 在上游编码 bounds 内调整功耗、时钟、风扇，可能死机、花屏、过热降频；通常有固件保护，重启 / unload 可恢复。 | 低–中 | 通常可恢复 | 可见；实验性字段带 `EXPERIMENTAL` 徽章 | 应用前确认 + 变更预览 | 橙 `#D97706` |
| **T3** | 高风险 / 实验性 | 可提高电压、电流、功耗或温度包络，改变保护阈值/风扇停转行为/高级电源策略，或证据不足、无法给出安全上限的实验性字段；可能导致永久硬件损坏或不可恢复。 | 高 | 可能不可逆 | **默认隐藏** | 解锁实验模式 + **逐字段二次确认** + 应用前总确认 + 强烈建议 dry-run | 红 `#DC2626` |

### 1.1 判定规则（按顺序）

1. **不写 ROM 字节 → T0**；写 ROM 但只生成磁盘副本、未应用 → 该动作本身 T0，但产物是“修改后镜像”（见 §6）。
2. **只读字段**（上游 `editable=false`、`capability_status != verified`、未识别、值未知）→ T0。
3. **能提高电压 / 电流 / 功耗 / 温度上限，或放宽/关闭保护阈值** → **T3**。
4. **能让风扇停转、减少有效风扇通道、或提高风扇启动温度** → T3；一般的风扇曲线/转速调整按 §3.4 的方向规则定级。
5. **仅时钟/频率偏移，不直接改变电压** → T2。
6. **只降低功耗/电流/温度上限，且不改变保护逻辑** → T1（若同时改变编码/保护语义则 T2）。
7. **实验性字段最低 T2**；若同时满足第 3 条则 T3。`EXPERIMENTAL` 徽章与风险等级同时显示，不得互相替代。
8. **组合变更取最高等级**：一次 `stage()`/apply 中包含任一 T3 字段，整个变更批次按 T3 门槛处理。
9. **架构降级**：未识别或不受支持的架构 → 全部只读 T0；Turing 家族整体按“实验性”处理（见 §5）。
10. **无法归类的字段 → T0 只读**，直到在本文与代码注册表中同时登记；禁止“先可编辑、后补文档”。

### 1.2 方向性降级规则

同一字段允许的写入方向不同，风险不同。表中“基础等级”为**最危险方向**；若用户只做安全方向，可按“降级”列显示更低等级，但**代码仍须按字段注册表校验方向与 bound**。

| 操作方向 | 规则 |
| --- | --- |
| 提高功耗/电流/电压/温度上限 | T3（不得降级） |
| 降低功耗/电流/温度上限 | T1；若改变保护阈值语义则 T2 |
| 提高风扇转速/降低启动温度 | T1 |
| 降低风扇转速/提高启动温度 | T2；可能导致停转则 T3 |
| 时钟偏移（任意方向） | T2 |
| 只读/无变更 | T0 |

## 2. 字段风险归属总则

- 字段键沿用上游稳定 key（`nvbios fields` 的 `key`），不得重命名。
- 通配符语义：`*` = `nvvdd` 或 `msvdd`；`N` = 风扇通道号 / 12 V 供电通道号（风扇 1..4，供电 1..4）；`M` = 额外风扇曲线号（1..7）；`K` = 风扇曲线点 1..3；`memory_point_K` 的 K = 1..7（显存中间频点，从最低点起）。
- 表中“实验性”列：**是** = 上游 `evidence` 明确标注 experimental / not hardware-tested；**部分** = 仅部分架构或部分型号有硬件报告；**否** = 上游未标注实验性（仍不代表本项目验证过）。
- “UI”列：`可见` = 默认显示；`T3 门控` = 默认隐藏，解锁实验模式后可见；`只读` = 显示但不可编辑。

## 3. 字段风险归属（按 6 类 + 只读类）

### 3.1 功耗（Power）

| 字段键 | 单位 | 基础等级 | 实验性 | 允许方向 / 降级 | 理由与备注 | UI |
| --- | --- | --- | --- | --- | --- | --- |
| `power_min_w` | W | T1 | 否 | 1 W … TGP rated default 内任意方向均 T1 | TGP 下限；不提高上限，最坏为低负载不稳定 | 可见 |
| `power_default_w` | W | T3 | 是 | 降低 → T1；提高 → T3 | 启动即生效的额定 TGP；提高直接增加功耗与发热 | T3 门控 |
| `power_max_w` | W | T3 | 部分 | 降低 → T1；提高 → T3 | 最大 TGP；上游 bounds 是编码边界，**不是硬件安全上限** | T3 门控 |
| `slot_power_rated_w` / `slot_power_max_w` | W | T3 | 是 | 降低 → T1；提高 → T3 | PCIe 插槽供电策略；可能超出插槽/主板设计 | T3 门控 |
| `connector_N_power_rated_w` / `connector_N_power_max_w` | W | T3 | 是 | 降低 → T1；提高 → T3 | 12 V 外接供电 sense channel 策略；可能超出线材/端子设计 | T3 门控 |
| `connector_sum_power_rated_w` / `connector_sum_power_max_w` | W | T3 | 是 | 降低 → T1；提高 → T3 | 多通道总和策略；提高可能绕过总功率保护 | T3 门控 |
| `board_fixed_rated_w` | W | T3 | 是（opt-in） | 仅解锁后可写；提高 → T3 | 固定 board policy 2/7；上游默认在 GUI 隐藏 | T3 门控 |
| `max_operating_temp_c` | °C | T2 | 是 | 降低 → T1；提高（≤ 产品 stock + 3 °C）→ T2 | 仅 GB20x；三个温度一起写；提高增加热应力 | 可见（实验徽章） |
| `nvvdd_power_threshold_rated_w` / `nvvdd_power_threshold_max_w` | W | T3 | 是（opt-in） | 提高 → T3 | Ada NVVDD 输出功率硬件阈值，属于保护策略 | T3 门控 |

### 3.2 电压（Voltage）

> 电压类**全部 T3**：上游没有给出硬件安全上限（`hardware_safe_maximum=null`），且任何提高都可能直接损坏 GPU 核心/显存供电。降低电压可能不稳定，但仍按 T3 处理，避免“降压一定安全”的误解。

| 字段键 | 单位 | 基础等级 | 实验性 | 允许方向 | 理由与备注 | UI |
| --- | --- | --- | --- | --- | --- | --- |
| `nvvdd_rel_max_mv` | mV | T3 | 部分 | 任意方向 T3 | NVVDD REL 输出钳位上限；直接改变核心电压上限 | T3 门控 |
| `msvdd_rel_max_mv` | mV | T3 | 是 | 任意方向 T3 | MSVDD REL 上限（GB20x / 双 rail Ampere 只读） | T3 门控 |
| `nvvdd_rel_fixed_mv` | mV | T3 | 是（opt-in） | 任意方向 T3 | 固定 REL 方程值；绕过动态曲线 | T3 门控 |
| `nvvdd_alt_fixed_mv` | mV | T3 | 是（opt-in） | 任意方向 T3 | 固定 ALT 方程值；与 REL/VMIN 有 ordering 约束 | T3 门控 |
| `nvvdd_vmin_mv` / `msvdd_vmin_mv` | mV | T3 | 是 | 任意方向 T3 | 最低工作电压；降低可能导致低负载不稳/损坏 | T3 门控 |
| `nvvdd_rel_alt_follow_ov` | 0/1 | T3 | 是（opt-in） | 仅 0→1 | XOC 风格：REL/ALT 指向 OV 方程；改变整个电压曲线 | T3 门控 |
| `*_rel_equation_max_mv` | mV | T3 | 部分 | 任意方向 T3 | REL 方程输出上限（uV float32 存储） | T3 门控 |
| `*_alt_equation_max_mv` | mV | T3 | 部分 | 任意方向 T3 | ALT 方程输出上限 | T3 门控 |
| `*_ov_equation_max_mv` | mV | T3 | 部分 | 任意方向 T3 | OV 方程输出上限；XOC 相关 | T3 门控 |
| `*_vmin_equation_max_mv` | mV | **T0** | — | 只读 | 上游明确 read-only；不等于 evaluated VMIN | 只读 |
| `*_rel_selector_index` / `*_alt_selector_index` / `*_ov_selector_index` / `*_vmin_selector_index` | index | **T0** | — | 只读 | 选择器索引，仅供审计 | 只读 |
| `*_boot_voltage_uv` | uV | **T0** | — | 只读/保留 | 启动电压，上游保留原值 | 只读 |

### 3.3 电流与保护阈值（Current / OCP）

> 提高电流上限或 OCP 阈值 = 放宽保护，**全部 T3**。降低同类阈值通常更安全，按方向降级。

| 字段键 | 单位 | 基础等级 | 实验性 | 允许方向 / 降级 | 理由与备注 | UI |
| --- | --- | --- | --- | --- | --- | --- |
| `input_current_rated_ma` / `input_current_max_ma` | mA | T3 | 是 | 降低 → T2；提高 → T3 | 12 V 板输入电流策略；提高可能超出供电/线材设计 | T3 门控 |
| `input_current_policy7_limit_ma` | mA | T3 | 是 | 降低 → T2；提高 → T3 | 与 12 V 输入 policy 7 联动的限值 | T3 门控 |
| `*_output_ocp_rated_ma` | mA | T3 | 是 | 降低 → T1；提高 → T3 | 输出过流保护额定值；提高会削弱保护 | T3 门控 |
| `*_output_ocp_max_ma` | mA | T3 | 部分 | 降低 → T1；提高 → T3 | 输出 OCP 上限（客户/板级 ceiling） | T3 门控 |
| `slot_current_threshold_rated_ma` / `slot_current_threshold_max_ma` | mA | T3 | 是（opt-in） | 降低 → T1；提高 → T3 | PCIe 插槽 12 V 电流硬件阈值 | T3 门控 |
| `connector_N_current_threshold_rated_ma` / `connector_N_current_threshold_max_ma` | mA | T3 | 是（opt-in） | 降低 → T1；提高 → T3 | 外接供电通道电流硬件阈值 | T3 门控 |
| `current_limit_a` / `ocp_limit_a` | A | **T0** | — | 只读 | 上游标注 read-only pending evidence | 只读 |
| `input_policy_9_max_raw` | raw | **T0** | — | 只读 | 单位未知的 raw 上限 | 只读 |

### 3.4 风扇（Fan）

| 字段键 | 单位 | 基础等级 | 实验性 | 允许方向 / 降级 | 理由与备注 | UI |
| --- | --- | --- | --- | --- | --- | --- |
| `fan_channels` | count | T3 | 是 | 只能按上游允许范围；任何减少有效通道 → T3 | 改错可能让某个风扇不转，导致局部过热 | T3 门控 |
| `fan_pwm_frequency_hz` | Hz | T2 | 是 | 21–28 kHz 内 → T2 | 影响风扇驱动兼容性/噪声；极端值可能停转（上游已限定范围） | 可见（实验徽章） |
| `fan_N_min_rpm` / `fan_N_max_rpm` | RPM | T2 | 是 | 提高 → T1；降低 → T2 | 转速上限降低会削弱散热；下游 bound 受曲线约束 | 可见（实验徽章） |
| `fan_N_min_pct` / `fan_N_max_pct` | % | T2 | 是 | 提高 → T1；降低 → T2 | 同上，百分比形式 | 可见（实验徽章） |
| `fan_N_curve_K_temp_c` | °C | T2 | 是 | 降低启动温度 → T1；提高 → T2 | 提高温度阈值会让风扇更晚介入 | 可见（实验徽章） |
| `fan_N_curve_K_rpm` / `fan_N_curve_K_pct` | RPM / % | T2 | 是 | 提高转速 → T1；降低 → T2 | 降低转速削弱散热 | 可见（实验徽章） |
| `fan_extra_M_curve_K_temp_c/rpm/pct` | °C / RPM / % | T2 | 是 | 同 fan_N 曲线 | 额外曲线，同样受顺序与边界约束 | 可见（实验徽章） |
| `fan_zero_rpm` | 0/1 | T3 | 是（opt-in） | 任意方向 T3 | 允许低负载停转；配置错误可能在负载下不转 | T3 门控 |
| `fan_N_zero_rpm_low_temp_c` / `fan_N_zero_rpm_high_temp_c` | °C | T3 | 是（opt-in） | 任意方向 T3 | 停转/启动温度；错误组合可导致过热 | T3 门控 |
| `fan_extra_M_zero_rpm_*_temp_c` | °C | T3 | 是（opt-in） | 任意方向 T3 | 额外曲线停转温度 | T3 门控 |

### 3.5 时钟（Clock）

| 字段键 | 单位 | 基础等级 | 实验性 | 允许方向 / 降级 | 理由与备注 | UI |
| --- | --- | --- | --- | --- | --- | --- |
| `gpc_offset_min_mhz` / `gpc_offset_max_mhz` | MHz | T2 | 部分 | 任意方向 T2 | GPC 时钟偏移范围；可能死机/花屏，重启可恢复；不直接改电压 | 可见（实验徽章） |
| `memory_offset_min_mhz` / `memory_offset_max_mhz` | MHz | T2 | 部分 | 任意方向 T2 | 显存偏移范围；NVML 显示为 2×table MHz | 可见（实验徽章） |
| `dram_min_table_mhz` / `dram_max_table_mhz` | table MHz | T2 | 是 | 任意方向 T2 | 显存时钟范围（table 单位） | 可见（实验徽章） |
| `xbar_min_table_mhz` / `xbar_max_table_mhz` / `sys_*` / `vid_*` | table MHz | T2 | 是 | 任意方向 T2 | 互连/系统/视频时钟范围 | 可见（实验徽章） |
| `gpc_curve_offset_mhz` | MHz | T2 | 是（opt-in） | −500…+500 MHz 内 T2 | GPC VF 曲线默认偏移；不改变电压方程 | 可见（实验徽章） |
| `factory_gpc_offset_mhz` | MHz | T2 | 是 | 仅厂商已启用的镜像可写；±500 MHz 内 T2 | 厂方出厂偏移；改错可能不稳定 | 可见（实验徽章） |
| `factory_rated_boost_mhz` | MHz | **T0** | — | 只读 | 厂方额定 boost，仅展示 | 只读 |
| `memory_point_K_follows_offset` | 0/1 | T2 | 是（opt-in） | 仅上游允许的 bit；任意方向 T2 | 显存中间频率点是否跟随偏移 | 可见（实验徽章） |
| 内存表 `configurations` / `bands` / `timings` / `tables` / `board_profile` | — | **T0** | — | 只读 | 上游 memory view 只读；board profile 仅整片刷写才生效 | 只读 |

### 3.6 实验性 / 高级（Advanced）

> 以下字段没有独立硬件验证，且会改变功耗管理/电源门控/利用率策略，统一 T3；即使只是“开关”也不得降级。

| 字段键 | 单位 | 基础等级 | 实验性 | 允许方向 | 理由与备注 | UI |
| --- | --- | --- | --- | --- | --- | --- |
| `perf_cf_util_policy` | 0/1 | T3 | 是 | 任意方向 T3 | PERF_CF 利用率策略总开关；改变性能控制器行为 | T3 门控 |
| `perf_cf_gpc_target_pct` / `perf_cf_gpc_jump_pct` / `perf_cf_gpc_hysteresis_down` / `perf_cf_gpc_hysteresis_up` | % / count | T3 | 是 | 任意方向 T3 | GPC 利用率控制器；仅 `perf_cf_util_policy=1` 时生效 | T3 门控 |
| `perf_cf_dram_*`（同上 4 项） | % / count | T3 | 是 | 任意方向 T3 | DRAM 利用率控制器 | T3 门控 |
| `perf_cf_vid_*`（同上 4 项） | % / count | T3 | 是 | 任意方向 T3 | 视频引擎利用率控制器 | T3 门控 |
| `lpwr_gr_power_gating` | 0/1 | T3 | 是 | 任意方向 T3 | GR 电源门控；错误关闭可能增加功耗/发热 | T3 门控 |
| `lpwr_mscg` | 0/1 | T3 | 是 | 任意方向 T3 | 存储系统时钟门控 | T3 门控 |
| `lpwr_nvdec_gating` / `lpwr_nvenc_gating` / `lpwr_ofa_gating` / `lpwr_nvjpg_gating` | 0/1 | T3 | 是 | 任意方向 T3 | 各媒体引擎门控 | T3 门控 |
| `lpwr_difr` | 0/1 | T3 | 是 | 任意方向 T3 | DIFR 空闲电源特性 | T3 门控 |
| `lpwr_gr_rail_gating` | 0/1 | T3 | 是 | 任意方向 T3 | GR rail 门控（仅部分型号） | T3 门控 |
| `lpwr_difr_dfpr_idle_ms` / `lpwr_difr_sw_asr_idle_us` / `lpwr_difr_cg_idle_us` / `lpwr_gr_rail_gating_idle_us` | ms / us | T3 | 是 | 0.5×–4× stock 内 T3 | 空闲时间；仅在对应开关为 Stock 时生效 | T3 门控 |
| `nvvdd_rel_alt_follow_ov` | 0/1 | T3 | 是（opt-in） | 仅 0→1 | 见 §3.2，XOC 风格电压选择器 | T3 门控 |
| `board_fixed_rated_w` | W | T3 | 是（opt-in） | 提高 → T3 | 见 §3.1 | T3 门控 |

### 3.7 T0 只读字段与界面信息

| 类别 | 内容 | 说明 |
| --- | --- | --- |
| 文件/设备身份 | 产品名、PCI ID、子系统 ID、VBIOS 版本、板号、构建日期、文件大小、SHA-256 | 只展示，不参与写入 |
| 镜像链 | 序号、类型、偏移、大小、8-bit 校验和、是否平衡、是否 last | 只展示；校验和失败阻止编辑/应用 |
| 上游只读字段 | `*_vmin_equation_max_mv`、`*_selector_index`、`*_boot_voltage_uv`、`factory_rated_boost_mhz`、`input_policy_9_max_raw`、`current_limit_a`、`ocp_limit_a` | 即使 key 存在也不可编辑 |
| 内存视图 | `configurations`、`bands`、`timings`、`tables`、`board_profile` | 上游 memory report；只读 |
| 应用结果 | manifest 查看、diff、日志、Verify 状态 | 只读 |
| 应用设置 | 语言、主题、窗口布局、搜索过滤 | 不写 ROM/注册表 |

### 3.8 未列出字段的兜底

任何未出现在 §3.1–§3.6 的字段（包括上游未来新增字段、未识别变体、`editable` 为 `null` 的字段）**一律按 T0 只读处理**，直到：

1. 在本文新增一行并说明等级/方向/理由；
2. 在 `src/vbios_studio/domain/risk_registry.py` 注册同一等级；
3. 通过 `tests/core/test_risk_registry.py` 的字段等级与方向测试。

## 4. 实验性字段清单（显式）

以下字段在上游 `evidence` 中标注为 experimental，**至少 T2**；其中标 ★ 的为 T3：

- 功耗：`power_default_w` ★、`power_max_w`（Ada/Ampere/Turing）★、`slot_power_*` ★、`connector_*_power_*` ★、`connector_sum_*` ★、`board_fixed_rated_w` ★、`max_operating_temp_c`、`nvvdd_power_threshold_*` ★。
- 电压：`nvvdd_rel_max_mv`（部分）、`msvdd_rel_max_mv` ★、`nvvdd_rel_fixed_mv` ★、`nvvdd_alt_fixed_mv` ★、`nvvdd_vmin_mv` / `msvdd_vmin_mv` ★、`nvvdd_rel_alt_follow_ov` ★、`*_rel/alt/ov_equation_max_mv` ★。
- 电流：`input_current_*` ★、`input_current_policy7_limit_ma` ★、`*_output_ocp_*` ★、`slot_current_threshold_*` ★、`connector_*_current_threshold_*` ★。
- 风扇：`fan_channels` ★、`fan_pwm_frequency_hz`、`fan_N_*`、`fan_extra_M_*`、`fan_zero_rpm` ★、`*_zero_rpm_*_temp_c` ★。
- 时钟：`gpc_offset_*`（部分）、`memory_offset_*`（部分）、`dram_*_table_mhz`、`xbar/sys/vid_*`、`gpc_curve_offset_mhz`、`factory_gpc_offset_mhz`、`memory_point_K_follows_offset`。
- 高级：`perf_cf_*` ★、`lpwr_*` ★。

> 说明：`EXPERIMENTAL` 是**证据标签**，T3 是**风险门槛**。两者同时展示；不得因为“只是实验性”就跳过 T3 确认，也不得因为“有用户报告”就把 T3 降级。

## 5. 架构支持与降级

| 家族 | 字段可写性 | 风险修正 | 应用方式 | 降级行为 |
| --- | --- | --- | --- | --- |
| GB20x | 上游审核字段 | 按本表 | 单 bank payload → 注册表/Linux loader | 未审核字段 → T0 只读 |
| Ada AD10x | 上游审核字段（部分实验） | 按本表；电压类 T3 | `ada-relocated-v2` payload | 未识别变体 → 只读 |
| Ampere GA10x | 全部上游标注实验 | **家族整体至少 T2**；功耗/电流/电压按本表 T3 | `ampere-relocated-v1` payload | 未识别变体 → 只读 |
| Turing TU10x/TU11x | 上游标注实验 | **家族整体至少 T2**；功耗/电流/电压按本表 T3；默认 `turing-e0-end-v1` 兜底 | 先试标准 payload，再试 e0end | 失败 → 保持原厂 |
| GA100 / 未知 / 损坏 | 不可写 | T0 | 禁止 | 只读结构报告 |

**家族修正规则**：Ampere/Turing 的字段若本表为 T1，则实际显示 T2；若本表为 T2，则实际显示 T3；T3 保持 T3。GB20x/Ada 不额外提升。

## 6. 刷写安全边界决议（核心）

### 6.1 事实基础：修改后镜像签名失效

- NVIDIA VBIOS 含厂商密码学签名。编辑工具只修改数据字节，**没有 NVIDIA 私钥，无法重新签名**；保存后的镜像仍带原签名，但签名与内容不再匹配。
- nvflash 在写入前后会做签名/完整性校验；修改后镜像会被拒绝，或在部分旧工具/异常路径下被写入，导致显卡无法启动（变砖）。
- 因此：**修改后镜像的签名失效，禁止 nvflash 刷写。** 本工具不实现、也不提供任何签名生成、补签、绕过或“让 nvflash 接受修改镜像”的功能。
- 修改后镜像的唯一支持应用方式是 loader override；它让驱动在启动时读取镜像，**不写 flash 芯片**。

### 6.2 三条通道决议

| 通道 | 允许的镜像 | 机制 | 写 flash？ | 默认 | 决议 |
| --- | --- | --- | --- | --- | --- |
| **A. Windows loader override** | 修改后镜像 | 注册表 `vbios`、`EnableGpuFirmware=0x11`、`VixLoaderPreviousEnableGpuFirmware`；`pnputil /restart-device` | 否 | **主路径** | 允许 |
| **B. Linux loader override** | 修改后镜像 | `nvidia-linux-vbios-vix-loader` 启动时注入；本工具只生成 payload 与指引 | 否 | **主路径** | 允许（不自动提权） |
| **C. nvflash（原厂恢复）** | **仅原厂未修改镜像** | `nvflash` 写 flash | 是 | 默认禁用 | **严格受限**：必须逐项通过 §6.3 |
| **D. nvflash + 修改后镜像** | 修改后镜像 | — | 是 | **永不实现** | **硬禁止**；UI 不提供入口，代码路径不存在 |

> **刷写通道只接受未修改镜像。** 即使文件只改了一个字节、即使只改了校验和平衡字节、即使修改后“看起来还能通过校验”，都属于修改后镜像，禁止刷写。

### 6.3 nvflash 守卫逐项校验清单（全部通过才允许启动子进程）

`NvflashGuard.check(candidate, pristine_original, expected_sha256, device, nvflash_path)` 按顺序执行；任一失败返回 `FlashDecision(allowed=False, code, message, hint)`，且 **fake/real runner 的调用次数必须为 0**。

| # | 检查 | 失败码 | 说明 |
| --- | --- | --- | --- |
| 1 | 全局刷写开关已显式开启，且本次调用带 `--i-understand-flash-risk` | `FLASH_DISABLED` | 默认 `allow_flash=false`；配置文件/环境变量不能单独开启，必须同时有 CLI 标志 |
| 2 | 候选文件存在且为普通文件（非符号链接、非目录） | `CANDIDATE_INVALID` | 防 TOCTOU/链接替换 |
| 3 | 候选 SHA-256 == 会话记录的原始 SHA-256 | `CANDIDATE_HASH_MISMATCH` | 打开后原文件被替换也拒绝 |
| 4 | 候选与原始文件**逐字节相同**（流式比较，不只比哈希） | `CANDIDATE_MODIFIED` | 直接落实“修改后镜像禁止刷写” |
| 5 | 当前会话无 staged changes，manifest `modified=false` | `SESSION_MODIFIED` | 防止“另存为后拿旧文件”混淆 |
| 6 | 每张镜像 `Sum % 256 == 0`，且尾部平衡字节符合上游审核形状 | `CHECKSUM_UNBALANCED` | 校验和不平衡 → 拒绝 |
| 7 | 镜像链可解析、格式受支持、无多 bank 歧义 | `STRUCTURE_INVALID` | 无法证明是完整单卡镜像 → 拒绝 |
| 8 | 候选 PCI ID / 子系统 ID 与目标 GPU 匹配；板号（若有）匹配 | `DEVICE_MISMATCH` | 防止刷错卡 |
| 9 | `nvflash` 存在、可执行、版本在允许列表内 | `NVFLASH_NOT_FOUND` / `NVFLASH_VERSION_UNSUPPORTED` | 找不到就明确报错，不执行任何命令 |
| 10 | 当前进程有管理员/root 权限 | `ELEVATION_REQUIRED` | 返回结构化建议 |
| 11 | 用户已勾选“我已有当前 VBIOS 备份”，并输入确认词 `FLASH ORIGINAL <sha256 前 8 位>` | `CONFIRMATION_REQUIRED` | 二次确认，防误触 |
| 12 | 执行前再次读取候选 SHA-256 并比对（紧邻 exec） | `RACE_DETECTED` | 缩小 TOCTOU 窗口 |

**执行约束**

- 通过后只允许调用标准写命令（例如 `nvflash --write <candidate>`，具体参数由适配器按上游 nvflash 语法构造），**禁止**追加 `--protectoff`、`--erase`、`--force` 等绕过保护的参数。
- 子进程必须 `list[str]` + `shell=False`；禁止 `os.system`、字符串拼接、管道。
- 刷写前后记录日志（设备、文件 SHA-256、nvflash 版本、退出码）；日志不含 ROM 内容。
- 刷写失败不自动重试；提示用户用原厂备份/硬件编程器恢复。
- 即使全部通过，界面仍显示“刷写原厂镜像也有风险（断电、型号不匹配、引导失败）”，并要求最终确认。

### 6.4 修改后镜像的应用流程（唯一允许路径）

1. 打开原厂 ROM → 记录 SHA-256、镜像链、设备身份（T0）。
2. staged 编辑 → 本地校验（字段级）。
3. “另存为”生成新 ROM + manifest（`modified=true`）；原文件不变。
4. 导出 loader payload（按架构 representation；见 `requirements.md` FR-3.4）。
5. 应用面板：设备状态 → `dry-run` 预览（注册表键/值/字节数/重启设备）→ 二次确认 → 执行 → Verify。
6. 失败/黑屏：重启；必要时安全模式/第二块 GPU 运行 `unload`/还原；驱动更新后重新检查。
7. **任何步骤都不提供“用 nvflash 刷写此修改镜像”的入口**；UI 明确显示“修改后镜像：仅可 loader override”。

### 6.5 失败与恢复

| 场景 | 预期行为 | 恢复 |
| --- | --- | --- |
| 驱动拒绝 override | Verify 返回 `override-not-active`；显卡运行原厂 VBIOS | 重新选择 payload/驱动版本；`unload` |
| 应用后黑屏 | 不自动重试 | 重启；安全模式/第二 GPU `unload`；重装驱动 |
| 注册表写失败 | 返回结构化错误，可能已部分写入 | 用 `VixLoaderPreviousEnableGpuFirmware`/备份恢复；重新 `load` 或 `unload` |
| nvflash 刷写失败 | 不自动重试，明确报错 | 原厂备份 + 硬件编程器/售后；不保证可恢复 |
| 原文件被替换 | 保存/应用/刷写全部拒绝（SHA-256 不一致） | 重新打开正确原厂文件 |

### 6.6 实现约束（已实现）

- `NvflashGuard` 位于 `src/vbios_studio/adapters/system/nvflash.py`（或同层子模块），必须可注入 fake runner；`check()` 为纯函数（文件读取除外），返回 `FlashDecision`。
- `flash()` 在 `decision.allowed is False` 时直接抛 `FlashRefused`，**不得**先构造命令再判断。
- 全仓只允许 `adapters/system/nvflash.py` 出现 `nvflash` 可执行名；UI/domain/ports 不得引用。
- `tests/apply/test_nvflash_guard.py` 覆盖负向用例：修改后镜像、校验和不平衡、设备不匹配、nvflash 缺失、竞态、dry-run，均断言 runner 零调用。
- `tests/apply/test_no_shell_true.py` 做全仓 AST 扫描：`shell=True`、`os.system` 均为 0 命中；`--protectoff`、`--erase`、`--force`、`--no-preserve` 由 `NvflashGuard` 禁止。

## 7. 风险呈现规范（UI）

### 7.1 徽章与颜色

| 等级 | 徽章文案（zh / en） | 颜色 | 说明 |
| --- | --- | --- | --- |
| T0 | 只读 / Read-only | 灰 `#6B7280` | 不可编辑 |
| T1 | 低风险 / Low | 蓝 `#2563EB` | 普通确认 |
| T2 | 中风险 / Medium | 橙 `#D97706` | 应用前确认 + 变更预览 |
| T3 | 高风险·实验 / High · Experimental | 红 `#DC2626` | 默认隐藏 + 逐字段二次确认 |

颜色不得作为唯一信息载体：徽章必须同时有文字；色盲用户可通过文字/图标区分。

### 7.2 T3 门控流程

1. 默认启动：T3 字段不可见；侧栏显示“实验性功能已锁定”。
2. 用户打开“设置 → 实验性功能”：显示风险说明，需勾选“我理解可能损坏硬件”并输入 `I UNDERSTAND`。
3. 解锁仅对**当前会话**有效，不持久化；重启应用后重新锁定。
4. 编辑任一 T3 字段：弹窗显示字段 key、旧值→新值、单位、风险说明、上游证据状态；需再次勾选并输入字段 key 或 `T3`。
5. 取消 → 不产生 staged change；确认 → 进入 staged 状态，字段行显示红色“已修改（T3）”。
6. 应用批次若含 T3：应用面板顶部红色横幅列出全部 T3 变更；执行前再确认一次。
7. 任何“全部展开/批量填充/预设套用”都不得绕过上述逐字段确认；预设中的 T3 字段套用时同样触发确认。

### 7.3 其他写操作

- Windows `load`/`unload`、nvflash（若启用）：显示目标设备、注册表键/命令、SHA-256，勾选确认后执行。
- `unload` 属于恢复操作，可减少一次确认，但仍显示将删除/还原的键值。
- 所有错误对话框统一组件，含 `code`、`message`、`hint`、`details`，可一键复制。

## 8. 已知盲区与免责

1. **本项目未在真实 GPU 上验证**：没有执行过编辑后应用、override、刷写或压力测试；上游报告不能替代本项目验证。
2. 上游 `bounds` 是**编码边界 + 保留默认值**，不是硬件安全上限；即使 T1/T2 字段也可能在特定板卡上不稳定。
3. 没有热仿真、功耗仿真、VRM 余量分析；无法判断某组参数对具体显卡是否安全。
4. Windows 注册表 override 依赖 NVIDIA 驱动内部行为，驱动更新可能随时失效；Linux loader 为外部项目，本项目不捆绑、不保证可用。
5. 无 NVIDIA 签名能力；修改后镜像永远不能通过 nvflash 的签名校验。
6. 刷写原厂镜像本身也有风险（断电、错卡、引导失败）；本工具默认禁用刷写通道。
7. 不同厂商/机型/散热设计的实际结果差异巨大；支持矩阵只代表代码路径，不代表硬件兼容性承诺。
8. 使用本工具造成的任何硬件损坏、数据丢失或保修失效，由用户自行承担。
