# 常见问题（FAQ）

## 基础

### VBIOS Studio 是什么？

一个离线的 GTK4 NVIDIA VBIOS 编辑器/应用套件：打开 ROM、按 T0–T3 风险分级编辑字段、生成新 ROM 与 loader payload，并通过 Windows 注册表 override 或 Linux loader 让修改生效。它**不刷写**修改后镜像。

### 它和 nvflash、MSI Afterburner、mVolt+ 是什么关系？

- 与 NVIDIA、nvflash、MSI、mVolt+ 均无隶属或背书关系。
- nvflash 只作为“原厂未修改镜像”的受限恢复通道；修改后镜像禁止使用。
- Windows 注册表 override 协议与 `nvidia-windows-vbios-vix-loader` 兼容；不替代其工具。

### 支持哪些显卡？

见 README 的[支持矩阵](../README.md#支持矩阵)。首版覆盖 GB20x、Ada、Ampere、Turing 的**代码路径**；GA100 与未识别架构只读。**本项目没有在真实硬件上验证任何型号**。

### 为什么叫“测试不完全”？

因为自动化测试只能验证离线逻辑、合成 ROM、fake 系统后端和 xvfb 界面；没有真实 GPU、真实驱动、真实注册表写入、真实刷写。详见 [`testing.md`](testing.md)。

## 安全

### 修改后的 VBIOS 能用 nvflash 刷吗？

**不能。** 修改后镜像的 NVIDIA 签名保持原样但已不匹配；nvflash 会拒绝，或造成不可恢复的损坏。修改后镜像只能通过 Windows 注册表 override / Linux loader 应用。代码层会硬拒绝，UI 不提供该入口。

### 什么情况下可以用 nvflash？

只允许**原厂未修改镜像**，且必须逐项通过：SHA-256 一致、逐字节相同、每张镜像校验和平衡、结构有效、PCI/子系统 ID 匹配、nvflash 版本受支持、管理员权限、显式确认。默认 `allow_flash=False`；即使全部通过，刷写仍有断电/错卡/引导失败风险。

### 会不会变砖？

任何 VBIOS 修改都有风险。通过 loader override 不写 flash 芯片，通常可通过重启/`unload` 恢复；但错误参数仍可能导致死机、过热或硬件损坏。刷写原厂镜像也可能失败。**使用风险自负**。

### 为什么 T3 字段默认隐藏？

T3 包括电压、电流/OCP、保护阈值、高级电源策略等高风险/实验性字段。需要先解锁实验模式，并对每个字段二次确认；取消不会产生任何变更。详见 [`risk-model.md`](risk-model.md)。

### 应用后黑屏怎么办？

1. 等待/重启；不要反复执行 load。
2. 用第二块 GPU 或安全模式启动，运行 `unload` 恢复；Windows 可重装/回滚驱动。
3. Linux 使用外部 loader 的卸载流程；必要时用原厂备份恢复。
4. 若已刷写失败，可能需要硬件编程器或售后；本项目不保证可恢复。

## 使用

### 为什么 Windows 要求管理员权限？

写 `HKLM\...\Class\{4d36e968-...}\NNNN` 的驱动注册表键需要管理员。非管理员会返回 `ELEVATION_REQUIRED`，不会尝试提权。

### Windows 上 `--gui` 没反应/返回 2？

`vbios-studio-gui` 的安装入口是 `vbios_studio.app.gui:main`，内部通过 `app/container.py::build_gui_controller()` 注入真实控制器；`python -m vbios_studio --gui` 也走同一生产路径，可直接启动主界面。若 `vbios-studio-gui` 或 `--gui` 仍返回 2，请视为缺陷：附上 `vbios-studio --version`、`python -m vbios_studio --version` 与完整 stderr 提交 issue，不要用其他启动方式绕过。

### 为什么 Linux 包不带 GTK？

Linux 上 PyGObject/GTK 由发行版提供（`python3-gi`、`gir1.2-gtk-4.0`、`gir1.2-adw-1`）；打包 GTK 会引入 ABI/主题/输入法问题。Windows exe 才内嵌 GTK4 运行时。

### 我的 ROM 会被上传吗？

不会。应用无网络访问、无遥测、无云服务；ROM 只在本机处理。详见 [`security.md`](security.md)。

### 原文件会被修改吗？

不会。打开只读；保存必须“另存为”新路径；原文件 SHA-256 全程校验。若原文件在会话中被替换，保存/应用/刷写都会拒绝。

### 支持拖放吗？

支持：拖入**恰好一个**本地 `.rom`/`.bin` 文件；目录、多文件、非 ROM 会给出可复制错误。也支持 `Ctrl+O` 文件对话框。

### 字段值为什么显示为只读？

T0 字段、未识别字段、上游未暴露的占位字段都是只读。若字段应可编辑但显示只读，可能是该架构/变体未通过上游审核，或风险注册表未登记。不要尝试绕过。

### 预设 profile 可以跨显卡套用吗？

只允许同架构/同格式；架构不符会整体拒绝且零部分写入。即使同架构，字段 bounds/硬件能力也可能不同，套用前必须逐项检查。

### 为什么 Verify 显示 `override-not-active`？

驱动没有接受 override，可能原因：驱动版本不支持、payload 与 GPU 不匹配、写入后未重启 GPU、驱动更新重建了注册表键。先 `unload`，检查驱动版本与 payload，再重试；不要反复 load。

### 驱动更新后失效？

Windows override 依赖驱动内部行为；驱动更新可能移除/改变。更新后运行 `status`，重新 load；每次驱动更新后都应 Verify。

### 为什么风险徽章颜色是这四种？

T0 灰 `#6B7280`、T1 蓝 `#2563EB`、T2 橙 `#D97706`、T3 红 `#DC2626`；同时有文字徽章，颜色不是唯一信息载体（无障碍要求）。

## 开发与贡献

### 如何从源码运行？

```bash
python -m venv --system-site-packages .venv
. .venv/bin/activate
pip install -r tools/requirements-dev.txt
pip install -e .
python -m vbios_studio --version
python -m vbios_studio --gui
```

### 如何跑测试？

```bash
python -m pytest -q
ruff check src tests
ruff format --check src tests
mypy --strict src/vbios_studio
lint-imports
bash tools/build_local.sh --check
```

### 为什么不用 PyGObject 的 pip 包？

PyGObject 从源码构建需要 `gtk4.pc`、`libadwaita-1.pc` 等开发头文件；本项目把它作为系统包/可选 extra，避免 `pip install -e .` 在无 GTK 开发环境失败。

### 如何报告 bug？

附版本、OS、Python/GTK 版本、复现步骤、错误 `code`/`details`、GPU 型号/驱动版本。**不要上传真实 VBIOS 文件**；测试 fixture 请用 `tests/core/rom_fixtures.py` 合成。

### 许可证是什么？

GPL-3.0-or-later；上游 editor 与 Windows loader 均为 GPL-3.0。再分发必须保留 `LICENSE`、`NOTICE.md` 与上游版权声明。本项目非 NVIDIA 官方项目。
