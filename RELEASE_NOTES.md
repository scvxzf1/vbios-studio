# VBIOS Studio v0.1.0

> [!WARNING]
> ## ⚠️ 测试不完全 / 未在真实硬件验证
>
> **本项目尚未在真实 GPU 上完成验证。** 我们没有在真实硬件上执行过编辑后的应用、Windows 注册表 override、Linux loader 注入或任何刷写操作；自动化测试只覆盖离线解析、合成 ROM、fake 注册表/命令 runner、dry-run 与 xvfb 离屏 UI。
>
> - 上游项目的历史用户报告**不代表本项目已验证**；不同厂商、型号、散热与供电设计的结果可能完全不同。
> - 修改 VBIOS 可能导致死机、花屏、过热、硬件永久损坏或失去保修。
> - **修改后的镜像签名失效，严禁使用 nvflash 刷写。** 修改后镜像只能通过 Windows 注册表 override 或 Linux loader 应用。
> - 刷写通道只接受**原厂未修改镜像**，且必须逐项校验；本项目默认禁用刷写。
> - 使用风险完全由你自行承担。详见仓库中的 `docs/risk-model.md`、`docs/security.md` 与 `docs/testing.md`。

VBIOS Studio 是基于 [Panchovix/nvidia-vbios-vix-editor](https://github.com/Panchovix/nvidia-vbios-vix-editor) 与 [nvidia-windows-vbios-vix-loader](https://github.com/Panchovix/nvidia-windows-vbios-vix-loader) 构建的 GTK4 图形化 NVIDIA VBIOS 编辑 / 应用套件：离线打开与检查 ROM，按 T0–T3 风险分级编辑字段（含实验性字段），生成新的 VBIOS 与 loader payload，并通过受控的 loader override 让修改生效。中英双语，Windows / Linux 双平台。

## 下载

| 平台 | 文件 | 说明 |
| --- | --- | --- |
| Linux x86_64 | `vbios-studio-0.1.0-linux-x86_64.tar.gz` | 需要系统 Python 3、PyGObject 与 GTK 4（例如 `sudo apt-get install python3-gi gir1.2-gtk-4.0 gir1.2-adw-1`） |
| Windows x86_64 | `vbios-studio-0.1.0-windows-x86_64.exe` | 单文件，内含 GTK 4 运行时；首次启动解包不联网 |
| 校验和 | `SHA256SUMS` | 覆盖上述两个产物 |

```bash
sha256sum -c SHA256SUMS
```

## 本版功能

- **GTK4 原生界面**：工具栏、分区导航、文件信息卡片、表格/表单双视图、搜索与过滤、撤销/重做（100 步）、预设、双 ROM 差异、应用/刷写面板、日志与状态栏。
- **T0–T3 风险分级**：字段按风险徽章展示；T3 默认隐藏，解锁实验模式需输入 `I UNDERSTAND`，逐字段确认需输入字段 key 或 `T3`；预设中的 T3 字段同样逐字段确认。
- **ROM 编辑与生成**：加载单/多镜像 ROM，生成新文件并自动配平 8-bit 校验和；原文件只读，保存附 manifest 与 loader payload。
- **受控应用**：Windows 注册表 override（dry-run、一次性确认票据、Verify、restore）；Linux 提供外部 loader 的探测与可复制指引，不自动提权、不修改系统文件。
- **中英双语**：运行时切换 `en` / `zh_CN`；风险徽章、确认对话框和错误提示全部走 gettext。

## 支持矩阵

| 架构家族 | 检查 | 编辑 | 应用（override） | 刷写（仅原厂） | 验证状态 |
| --- | --- | --- | --- | --- | --- |
| Blackwell GB20x（GB202/203/205/206） | ✅ | ✅ 按上游审核字段 | ✅ | 默认关闭 | 上游有用户报告；**本项目未在真实硬件验证** |
| Ada AD10x | ✅ | ✅ 部分字段实验性 | ✅ `ada-relocated-v2` | 默认关闭 | 上游少量型号；**本项目未验证** |
| Ampere GA10x（GA102–GA107） | ✅ | ⚠️ 全部字段上游标注实验性 | ✅ `ampere-relocated-v1` | 默认关闭 | 上游少量型号；**本项目未验证** |
| Turing TU10x/TU11x | ✅ | ⚠️ 实验性 | ✅ 需 `turing-e0-end-v1` 兜底 | 默认关闭 | 上游少量报告；**本项目未验证** |
| GA100（A100/A30/A800） | 只读结构报告 | ❌ | ❌ | ❌ | 明确不支持 |
| 未识别 / 损坏镜像 | 只读结构报告 | ❌ | ❌ | ❌ | 降级，不崩溃 |

## 已知限制

- ❌ 未在真实 GPU 上验证编辑后的应用、override、压力测试与长期稳定性。
- ❌ 未在 Windows 实机验证注册表写入、驱动重启和 Verify 全流程；Windows 构建仅由 CI `windows-latest` job 覆盖。
- ❌ 未验证各厂商/机型/散热/供电设计的兼容性差异。
- ❌ 未验证 Linux loader 的实际注入（属外部项目）。
- ❌ 任何刷写操作均未验证；本项目默认禁用，且不做真机刷写。
- ❌ 不保证未来 NVIDIA 驱动仍支持 override。
- ⚠️ 真实 Windows `WinregPlatform.vbios_image` 当前无法读取运行中镜像，因此 Verify 在真实机器上会返回 `VERIFY_UNAVAILABLE`；不要把它当作“已验证通过”。

## 许可证与上游

- 许可证：GPL-3.0-or-later，全文见 `LICENSE`；上游归属与商标声明见 `NOTICE.md`。
- 上游 editor：`Panchovix/nvidia-vbios-vix-editor` @ `1f8ee665bd175bd9ede367e6d15308f837bd987b`（v0.1.28）。
- 上游 loader 协议参考：`Panchovix/nvidia-windows-vbios-vix-loader` @ `ec7bdfe317d3a52de160d17d2bb80ff20813596e`（v0.3.1-6）。
- 非 NVIDIA 官方项目，未获 NVIDIA 认可或赞助。NVIDIA、GeForce 是 NVIDIA Corporation 的商标。
