# 文件树与模块职责

> 本文件与 v0.1.1 真实目录一致；`tests/contract/test_docs_tree.py` 强制校验“源码模块路径必须出现在本文、本文中的路径必须真实存在”。新增/删除模块时必须同步更新本文件。

## 1. 仓库总览

```text
vbios-studio/
├── README.md                     # 用户入口：警告、功能、安全边界、安装、文档索引
├── UPSTREAM.md                   # 上游 URL、pin SHA、vendored manifest、同步流程
├── pyproject.toml                # 打包、ruff/mypy/pytest/import-linter 配置
├── docs/                         # 需求、风险、架构、文件树、测试、同步、i18n、安全、FAQ
├── docs-assets/screenshots/      # xvfb 生成的真实界面截图（3 张）
├── src/
│   ├── nvidia_vbios/             # 上游 editor 的逐字节只读镜像（禁止修改）
│   └── vbios_studio/             # 本项目自有代码（六包）
├── tests/                        # contract / core / apply / ui / integration / golden / hygiene / meta / i18n / release
├── tools/                        # 本地构建与发布脚本
├── .github/workflows/            # ci / build / release / upstream-sync
└── .venv/                        # 本地开发虚拟环境（不提交）
```

## 2. `src/vbios_studio/` 自有模块清单

### 2.1 包入口与领域层

| 路径 | 职责 |
| --- | --- |
| `src/vbios_studio/__init__.py` | 包版本 `__version__ = "0.1.1"` |
| `src/vbios_studio/__main__.py` | `python -m vbios_studio` 入口 |
| `src/vbios_studio/domain/__init__.py` | domain 包导出与 docstring |
| `src/vbios_studio/domain/models.py` | 冻结 DTO：`DocumentSnapshot`、`FieldSnapshot`、`EditPreview`、`SaveResult`、`FieldDiff`、`ImageDiff`、`RomDiff`、`DeviceStatus`、`ApplyPreview`、`ApplyResult` |
| `src/vbios_studio/domain/errors.py` | `DomainError(code, message, hint, details)` 与稳定错误码 |
| `src/vbios_studio/domain/risk.py` | `RiskLevel`、`risk_rank()`、`max_risk()`、`is_t3()` |
| `src/vbios_studio/domain/risk_registry.py` | T0–T3 逐字段风险注册表、方向降级、Ampere/Turing 家族修正 |
| `src/vbios_studio/domain/catalog.py` | 字段描述 → `FieldSnapshot`，单位格式化、只读占位、风险注解 |
| `src/vbios_studio/domain/document.py` | 由上游 report 构建 `DocumentSnapshot` |
| `src/vbios_studio/domain/rom.py` | 纯 ROM 结构扫描、逐镜像 8-bit 校验和、末字节配平 |
| `src/vbios_studio/domain/manifest.py` | 生成带版本号的 manifest |
| `src/vbios_studio/domain/serialization.py` | DTO 的 JSON 兼容序列化 |
| `src/vbios_studio/domain/sections.py` | 分区 id / 顺序 / 字段归区 |

### 2.2 Ports 与 Adapters

| 路径 | 职责 |
| --- | --- |
| `src/vbios_studio/ports/__init__.py` | 四个 Protocol 的导出 |
| `src/vbios_studio/ports/editor.py` | `EditorPort`（open/stage/preview/save_as/reset） |
| `src/vbios_studio/ports/diff.py` | `DiffPort.diff_against` |
| `src/vbios_studio/ports/profile.py` | `ProfilePort.export_changes/apply_profile` |
| `src/vbios_studio/ports/apply.py` | `ApplyPort.configure_payload/device_status/dry_run/execute/restore/verify` |
| `src/vbios_studio/adapters/__init__.py` | adapters 包 docstring |
| `src/vbios_studio/adapters/upstream.py` | `nvidia_vbios` 桥接：open/catalog/stage/preview/save_as/reset/export_loader_payload |
| `src/vbios_studio/adapters/diff.py` | 生产 `DiffPort`：复用 `ui.diff_model.compare`，加载右侧 ROM 并转 `RomDiff` |
| `src/vbios_studio/adapters/profile.py` | 生产 `ProfilePort`：导出/应用 JSON preset，整体校验后一次 `stage()`，零部分写入 |
| `src/vbios_studio/adapters/system/__init__.py` | system 子包 docstring |
| `src/vbios_studio/adapters/system/_base.py` | 可注入命令 runner（列表参数、`shell=False`） |
| `src/vbios_studio/adapters/system/windows_plan.py` | Windows 注册表 override 的纯计划/回读/预览 |
| `src/vbios_studio/adapters/system/windows_registry.py` | `WindowsRegistryAdapter`：status/dry-run/load/verify/unload |
| `src/vbios_studio/adapters/system/windows_verify.py` | Windows override 只读逐字节 Verify（running image 由 platform 提供） |
| `src/vbios_studio/adapters/system/windows_winreg.py` | 生产 Windows 注册表后端（延迟 import winreg） |
| `src/vbios_studio/adapters/system/linux_loader.py` | 探测外部 Linux loader，生成可复制指引，不执行/不提权 |
| `src/vbios_studio/adapters/system/nvflash.py` | `NvflashGuard`：修改镜像硬拒绝、逐项校验、唯一受控执行入口 |

### 2.3 UI 层

| 路径 | 职责 |
| --- | --- |
| `src/vbios_studio/ui/__init__.py` | ui 包 docstring |
| `src/vbios_studio/ui/__main__.py` | `python -m vbios_studio.ui` 入口 |
| `src/vbios_studio/ui/application.py` | GTK 应用生命周期、窗口重建、语言/主题切换、selftest 分流 |
| `src/vbios_studio/ui/main_window.py` | 主窗口：HeaderBar + NavigationSplitView + 堆叠视图 + 日志 + 状态栏 |
| `src/vbios_studio/ui/controller.py` | GTK-free 控制器：staged edits、撤销/重做、过滤、端口调用 |
| `src/vbios_studio/ui/apply_actions.py` | 控制器 mixin：保存 payload 注入、ApplyPort dry-run/execute/verify/restore |
| `src/vbios_studio/ui/controller_errors.py` | `ConfirmationRequired` / `T3LockedError` 异常契约 |
| `src/vbios_studio/ui/profile_controller.py` | 预设批量应用的 T3 门控 mixin |
| `src/vbios_studio/ui/profile_flow.py` | 预设逐字段 T3 确认对话框流程 |
| `src/vbios_studio/ui/a11y.py` | accessible label、Tab 链、控件顺序辅助 |
| `src/vbios_studio/ui/theme.py` | 固定 T0–T3 颜色、CSS、浅/深色切换 |
| `src/vbios_studio/ui/shortcuts.py` | Ctrl+O/S/Z/Y、Ctrl+Shift+Z 等快捷键 |
| `src/vbios_studio/ui/field_text.py` | 字段/分区本地化显示名 |
| `src/vbios_studio/ui/filtering.py` | 纯字段过滤（已修改/仅 T3/仅分区/搜索） |
| `src/vbios_studio/ui/diff_model.py` | 两个 `DocumentSnapshot` 的字段级+镜像级 diff |
| `src/vbios_studio/ui/drop_rules.py` | 拖放 payload 校验（GTK-free） |
| `src/vbios_studio/ui/drop_target.py` | 窗口拖放目标：恰好一个本地 ROM |
| `src/vbios_studio/ui/profile_io.py` | 预设 JSON 文件对话框与读写 |
| `src/vbios_studio/ui/window_dialogs.py` | 打开/另存/预设/diff 对话框流程 |
| `src/vbios_studio/ui/demo.py` | 内存 demo ports（selftest / 截图） |
| `src/vbios_studio/ui/demo_data.py` | 合成演示文档 |
| `src/vbios_studio/ui/selftest.py` | xvfb/离屏 selftest：构建窗口、a11y、撤销/重做、3 张截图 |
| `src/vbios_studio/ui/components/__init__.py` | 组件包 docstring |
| `src/vbios_studio/ui/components/header_bar.py` | 顶部工具栏 |
| `src/vbios_studio/ui/components/sidebar.py` | 左侧导航与文档身份 |
| `src/vbios_studio/ui/components/file_info.py` | 文件信息卡片 + 镜像链列表 |
| `src/vbios_studio/ui/components/field_table.py` | 表格视图（字段/当前值/单位/范围/默认值/风险/偏移） |
| `src/vbios_studio/ui/components/field_form.py` | 表单视图（按分区折叠卡片） |
| `src/vbios_studio/ui/components/field_filters.py` | 搜索 + 三个过滤开关 + 命中计数 + 视图切换 |
| `src/vbios_studio/ui/components/risk_badge.py` | T0–T3 徽章与统一颜色映射 |
| `src/vbios_studio/ui/components/settings.py` | 实验模式门控与风险确认 |
| `src/vbios_studio/ui/components/apply_panel.py` | 设备状态、dry-run、执行、Verify、还原 |
| `src/vbios_studio/ui/components/diff_view.py` | 双 ROM 差异视图 |
| `src/vbios_studio/ui/components/empty_state.py` | 空状态与拖放引导 |
| `src/vbios_studio/ui/components/log_panel.py` | 可复制/清空日志面板 |
| `src/vbios_studio/ui/components/status_bar.py` | 文件/架构/未保存/校验和状态 |
| `src/vbios_studio/ui/dialogs/__init__.py` | 对话框包 docstring |
| `src/vbios_studio/ui/dialogs/about_dialog.py` | About：版本、上游、测试声明 |
| `src/vbios_studio/ui/dialogs/confirm_dialog.py` | T3 / 系统写操作二次确认 |
| `src/vbios_studio/ui/dialogs/error_dialog.py` | 统一错误对话框（含可复制 details） |
| `src/vbios_studio/ui/dialogs/shortcuts_dialog.py` | 帮助 → 快捷键表 |

### 2.4 App 与 i18n

| 路径 | 职责 |
| --- | --- |
| `src/vbios_studio/app/__init__.py` | app 包 docstring |
| `src/vbios_studio/app/cli.py` | `--version` / `--selftest` / `--gui` / ROM 参数 |
| `src/vbios_studio/app/gui.py` | 安装后 `vbios-studio-gui` 入口：注入 `build_gui_controller()` |
| `src/vbios_studio/app/container.py` | 组合根：构造 adapter、注入 ports，`build_gui_controller()` 返回四 Port 真实控制器 |
| `src/vbios_studio/i18n/__init__.py` | gettext catalogue、`set_language`、`gettext`、运行时切换 |
| `src/vbios_studio/i18n/catalog.py` | locale 归一化、环境语言检测 |
| `src/vbios_studio/i18n/locale/en/LC_MESSAGES/vbios_studio.po` | 英文目录源（282 msgid） |
| `src/vbios_studio/i18n/locale/en/LC_MESSAGES/vbios_studio.mo` | 英文编译目录 |
| `src/vbios_studio/i18n/locale/zh_CN/LC_MESSAGES/vbios_studio.po` | 简体中文目录源（282 msgid） |
| `src/vbios_studio/i18n/locale/zh_CN/LC_MESSAGES/vbios_studio.mo` | 简体中文编译目录 |

> msgid 数复核：`grep -c '^msgid' src/vbios_studio/i18n/locale/en/LC_MESSAGES/vbios_studio.po`（`zh_CN` 同）。

## 3. `src/nvidia_vbios/`（上游只读镜像）

```text
src/nvidia_vbios/
├── __init__.py                   # 上游版本 0.1.28
├── __main__.py                   # 上游 CLI 入口
├── cli.py                        # 上游命令行
├── families.py                   # 架构家族定义
├── editor/                       # 上游稳定 API：load/inspect/plan/edit/save/normalize/registry
├── rom/                          # 上游 ROM 解析：PCI/NPDS、Blackwell/Ada/Ampere/Turing、memory view
└── gui/                          # 上游 GTK 界面（仅参考，本项目不 import）
```

- **只读约束**：31 个文件，SHA-256 记录在 `tests/contract/upstream-manifest.json`；`tests/contract/test_version.py` 逐文件校验。
- **pin**：`1f8ee665bd175bd9ede367e6d15308f837bd987b`（v0.1.28），见 `UPSTREAM.md`。
- 禁止格式化、改注释、改 import 或“顺手修 bug”；上游问题只通过升级 pin / adapter shim / 上游 PR 处理。

## 4. `tests/` 测试树

| 目录/入口 | 职责与覆盖类别 |
| --- | --- |
| `tests/conftest.py` | 共享合成 ROM fixtures（Ada/Ampere 等变体），供各测试域复用 |
| `tests/contract/` | 契约与结构不变量：包/分层/import 边界、无 GTK、版本与上游 pin、文件大小、文档树、GUI 入口、i18n/结构审计 |
| `tests/core/` | 合成 ROM 解析、逐镜像校验和、保存管线、负向用例、风险注册表 |
| `tests/apply/` | Windows 注册表 dry-run/回读/verify/restore、一次性 dry-run 票据、Linux loader 指引、nvflash 硬拒绝、AST shell 扫描 |
| `tests/ui/` | xvfb GTK 视图/交互/i18n/截图/无障碍/自检进程；覆盖主窗口、表格/表单、搜索过滤、撤销重做、T3 门控与确认、预设/替换、diff、拖放、错误/确认对话框、应用面板、主题与并发 selftest |
| `tests/integration/` | 真实控制器端到端：打开→编辑→生成→校验和自愈→应用 dry-run/应用路径 |
| `tests/golden/` | 上游字段 parity、字段目录 golden 快照 |
| `tests/hygiene/` | 仓库卫生扫描、`.gitignore` 策略与已跟踪文件审计 |
| `tests/meta/` | 质量闸门、卫生结构、i18n 对称性与文档一致性自检 |
| `tests/i18n/` | en/zh_CN msgid 集合、翻译完整性与源码 msgid 覆盖 |
| `tests/release/` | 4 个 workflow YAML、产物名、pip 索引、shell 语法 |

## 5. `docs/` 文档树

```text
docs/
├── requirements.md      # 需求契约（FR-1..FR-6、GUI-01..10、Ports 附录）
├── reviews/             # 历史评审/审计报告与状态索引
│   ├── README.md        # 报告索引：日期/结论/当前状态
│   ├── review-report.md
│   ├── review-delta-report.md
│   ├── review-final-report.md
│   ├── review-final-v2.md
│   ├── publish-audit.md
│   ├── publish-audit-v011.md
│   ├── verification-report.md
│   └── requirements-review.md
├── risk-model.md        # T0–T3 定义、逐字段风险、nvflash 安全边界
├── architecture.md      # 分层架构、依赖图、import-linter、数据流
├── file-tree.md         # 本文件
├── testing.md           # 测试矩阵、命令、证据、已知盲区
├── upstream-sync.md     # 上游同步手册、冲突处理、pin 更新规则
├── i18n.md              # gettext 翻译流程
├── security.md          # 安全模型、数据/权限边界
└── faq.md               # 常见问题与故障排查
```

## 6. `tools/` 与 `.github/workflows/`

| 路径 | 职责 |
| --- | --- |
| `tools/build_local.sh` | 本地等价 CI：`--check` 跑全部闸门；`--dist` 构建 Linux 包；`--clean` 清理 |
| `tools/build_release.py` | 构建确定性 `dist/vbios-studio-<ver>-linux-x86_64.tar.gz` 与 `SHA256SUMS` |
| `tools/entry_gui.py` | Windows Nuitka 入口 |
| `tools/release/build-windows.sh` | Windows onefile exe 构建脚本（MSYS2 UCRT64） |
| `tools/requirements-dev.txt` | 开发依赖锁定 |
| `tools/checks/` | 仓库卫生、i18n 审计、结构审计、上游 parity 的可复用检查模块（`__init__.py`、`repo_hygiene.py`、`i18n_audit.py`、`structure_audit.py`、`parity.py`） |
| `.github/workflows/ci.yml` | Ubuntu 24.04 质量闸门 + 仓库卫生（发布前检查） |
| `.github/workflows/build.yml` | Linux tar.gz + Windows exe 构建与冒烟 |
| `.github/workflows/release.yml` | tag `v*` 触发，汇总产物 + `SHA256SUMS` 创建 Release |
| `.github/workflows/upstream-sync.yml` | 手动合并上游；冲突时 abort + draft PR + 冲突报告 |

## 7. 不提交的生成物

`__pycache__/`、`*.pyc`、`.venv/`、`build/`、`dist/`、`.mypy_cache/`、`.pytest_cache/`、`.ruff_cache/`、`.import_linter_cache/`、`src/vbios_studio.egg-info/`、真实 `.rom`/`.bin`/`.exe`、密钥与 `.env`。测试 ROM 由 `tests/core/rom_fixtures.py` 合成，不入库。
