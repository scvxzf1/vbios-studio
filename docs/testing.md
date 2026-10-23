# 测试矩阵与已知盲区

| 项目 | 值 |
| --- | --- |
| 适用版本 | v0.1.0 |
| 最近一次本机全量 | 2026-10-23：`python -m pytest -q \| tail -1` → **224 passed**（无 skip） |
| 代码范围 | 离线解析、合成 ROM、fake 系统后端、xvfb 离屏 UI；**无真实 GPU** |
| 强制入口 | `tools/build_local.sh --check` 与 `.github/workflows/ci.yml` |

> **最重要的结论：所有测试都是软件层测试。** 没有在真实显卡上执行过编辑后的应用、注册表 override、Linux loader 注入、压力测试或刷写。

## 1. 测试目录与职责

| 目录 | 文件数 | 覆盖内容 | 是否依赖硬件 |
| --- | --- | --- | --- |
| `tests/contract/` | 12 个测试文件 + manifest | 六包结构、README/模块 docstring、文件 ≤400 行、无 GTK 的 CLI、pyproject、import 边界、5 条 import-linter、diff DTO、上游 31 文件 SHA-256、doc tree、GUI 入口、i18n/结构审计 | 否 |
| `tests/core/` | 5 个测试文件 + 合成 ROM fixture | ROM 链解析、逐镜像 8-bit 校验和、末字节配平、保存管线、原文件 SHA 不变、manifest、负向用例（篡改/跨架构/越界/覆盖）、风险注册表方向降级 | 否 |
| `tests/apply/` | 5 个测试文件 + fakes | Windows 注册表 dry-run 零写入、一次性 dry-run 票据、无票据 execute 零写入、load 协议、回读、三种 unload 还原、权限/重启错误；ApplyPort.describe_operations 与真实写入同源的操作清单；ApplyPort.verify 逐字节比较（运行镜像由 platform 提供）；Linux loader 只读指引与 guidance-only ApplyPort；nvflash 修改镜像/校验和/缺失/版本/确认/竞态硬拒绝；全仓 `shell=True`/`os.system` AST 扫描 | 否（fake registry/runner） |
| `tests/ui/` | 20 个测试文件 + fixtures | 主窗口构建、a11y/Tab 顺序、表格/表单、搜索过滤、撤销/重做、T3 门控与确认取消、预设、diff、拖放、错误/确认对话框、i18n 切换、3 张截图（xvfb） | 否（xvfb 软件渲染） |
| `tests/integration/` | 1 个测试文件 + conftest | 真实 `build_gui_controller()` 路径：打开→编辑→生成→校验和自愈→应用 dry-run（集成接线） | 否 |
| `tests/golden/` | 2 个测试文件 | 上游字段 `nvbios fields` 公共字段 parity、字段目录 golden 快照 | 否 |
| `tests/hygiene/` | 2 个测试文件 | 仓库卫生（无 ROM/密钥/构建产物）；`.gitignore` 策略与已跟踪文件审计 | 否 |
| `tests/meta/` | 4 个测试文件 | 质量闸门自检、卫生结构、i18n 对称性、文档计数防漂移 | 否 |
| `tests/i18n/` | 1 个测试文件 | 282 条 msgid，`en` 与 `zh_CN` 集合完全一致；源码中每个 msgid 都有翻译 | 否 |
| `tests/release/` | 1 | 4 个 workflow YAML 可解析、Windows runner/产物名、release 附件、pip 显式索引、`build_local.sh` 使用 system-site-packages、shell 语法 | 否 |

测试 fixture 全部由 `tests/core/rom_fixtures.py` 合成为小型 ROM，**仓库不包含任何真实 `.rom`/`.bin`/`.exe`**。

表中“测试文件数”均可用 `find <目录> -maxdepth 1 -name 'test_*.py' | wc -l` 复核。

### 1.1 计数测量命令

| 指标 | 命令 | 当前值 |
| --- | --- | --- |
| pytest 总数 | `python -m pytest -q \| tail -1` | 224 passed |
| UI 测试文件数 | `ls tests/ui/test_*.py \| wc -l` | 20 |
| mypy 覆盖文件数 | `mypy --strict src/vbios_studio \| tail -1` | 77 source files |
| msgid 数 | `grep -c '^msgid' src/vbios_studio/i18n/locale/en/LC_MESSAGES/vbios_studio.po` | 282（en/zh_CN 一致） |

全量测试的直接测量命令：`python -m pytest -q | tail -1`。

## 2. 可复制命令

在仓库根目录执行：

```bash
# 全量测试（需要 GTK 4 系统包与 xvfb；CI 与本地一致）
python -m pytest -q

# 只跑契约层（不依赖 GTK）
python -m pytest -q tests/contract

# 只跑核心离线管线
python -m pytest -q tests/core

# 只跑系统适配器（fake runner）
python -m pytest -q tests/apply

# 只跑 i18n 完整性
python -m pytest -q tests/i18n

# 只跑发布配置
python -m pytest -q tests/release

# 静态闸门
ruff check src tests
ruff format --check src tests
mypy --strict src/vbios_studio
lint-imports

# 无 GTK 的入口
python -m vbios_studio --version
python -m vbios_studio --selftest

# 一键等价 CI
bash tools/build_local.sh --check
```

### 2.1 本机最近一次结果（2026-10-23）

| 命令 | 结果 |
| --- | --- |
| `python -m pytest -q` | `224 passed`，exit 0 |
| `python -m pytest -q tests/contract` | 当前契约测试全部通过，exit 0 |
| `ruff check src tests` | All checks passed，exit 0 |
| `ruff format --check src tests` | 当前源码与测试文件全部格式正确，exit 0 |
| `mypy --strict src/vbios_studio` | Success: no issues found in 77 source files，exit 0 |
| `lint-imports` | 5 kept, 0 broken，exit 0 |
| `python -m vbios_studio --version` | `vbios-studio 0.1.0`，exit 0 |
| `bash tools/build_local.sh --check` | 5 条 import-linter 契约 KEPT，224 passed / 0 skipped，`vbios-studio 0.1.0`，exit 0 |

> 上表是**本机**（Linux + 系统 PyGObject/GTK 4）结果，不是 Windows 或真实硬件结果。

## 3. 安全相关负向测试（重点）

| 测试 | 断言 |
| --- | --- |
| `tests/apply/test_nvflash_guard.py::test_modified_image_is_refused_before_any_command` | 修改后镜像 → `REFUSE_MODIFIED_IMAGE`，runner 调用次数 0 |
| `...::test_unbalanced_checksum_is_refused_before_any_command` | 校验和不平衡 → 拒绝，runner 0 |
| `...::test_missing_nvflash_is_reported_without_any_command` | nvflash 缺失 → `NVFLASH_NOT_FOUND`，runner 0 |
| `...::test_flash_channel_is_disabled_by_default` | 默认 `allow_flash=False`，即使原厂镜像也拒绝 |
| `...::test_pristine_image_is_allowed_and_flash_uses_a_list_command` | 原厂镜像通过后才允许 list 参数命令 |
| `tests/apply/test_windows_registry.py::test_dry_run_performs_zero_writes` | dry-run 写计数 0 |
| `tests/apply/test_windows_registry.py::test_unload_restores_the_first_load_value` | 三种首次状态（有值/absent/其他）还原 |
| `tests/apply/test_no_shell_true.py::test_no_shell_true_or_os_system_anywhere` | 全仓禁止 `shell=True` / `os.system` |
| `tests/core/test_negative_cases.py` | 篡改签名区、跨架构字段、越界值、覆盖输出均拒绝且不写文件 |

## 4. 未测试 / 无法测试的矩阵

| 项 | 状态 | 原因 / 影响 |
| --- | --- | --- |
| 真实 GPU 编辑后应用 | ❌ 未测试 | 无测试硬件；上游报告不能替代本项目验证 |
| Windows 实机注册表 override / 驱动重启 / Verify | ❌ 未测试 | 需要 Windows + NVIDIA GPU + 管理员；本地仅 fake 后端与 YAML 静态检查 |
| Linux loader 实际注入 | ❌ 未测试 | 外部项目，需真实 GPU 与内核/驱动环境 |
| nvflash 真机刷写 | ❌ 未测试且默认禁用 | 风险过高；守卫只做负向与 fake 正向测试 |
| 各厂商/机型/散热/供电差异 | ❌ 未测试 | 无硬件矩阵；Turing/Ampere 上游证据仅少量型号 |
| 长时间稳定性/压力/热测试 | ❌ 未测试 | 无实验室环境 |
| NVIDIA 签名验证/重签 | ❌ 不实现 | 无 NVIDIA 私钥；修改镜像签名必然失效 |
| 真实控制器集成路径（`--gui`、生产 Diff/Profile） | ✅ `tests/integration` 2 passed（集成接线） | 覆盖打开→编辑→生成→校验和自愈→应用 dry-run；仍未在真实硬件执行 |
| Windows 构建产物运行 | ⚠️ CI 配置完成，未本地执行 | 需 `windows-latest` + MSYS2；发布时验证 |
| macOS/32 位/ARM | ❌ 不支持 | 首版范围外 |

## 5. 测试设计原则

1. **合成 ROM**：所有 ROM fixture 由脚本生成，不含真实硬件 dump；测试不依赖任何用户数据。
2. **fake 优先**：注册表、命令 runner、设备状态都可注入；系统写路径在测试中零真实调用。
3. **负向优先**：安全边界用“必须拒绝 + 零调用”的断言，而不是只测成功路径。
4. **文档一致性**：`tests/contract/test_docs_tree.py` 强制 README 声明、docs 文件存在、file-tree 覆盖所有源码模块；`test_architecture_contracts.py` 强制 import-linter 契约与架构文档同步。
5. **无 GTK 的 CLI**：`tests/contract/test_gtk_independence.py` 在 `gi` 抛异常的环境下运行 `--version`/`--selftest`。

## 6. 如何报告问题

请附上：

- `python -m vbios_studio --version` 输出；
- 操作系统、Python、GTK/PyGObject 版本；
- 完整复现步骤与错误对话框的 `code` / `details`；
- GPU 型号、PCI ID、驱动版本（**不要上传真实 VBIOS 文件**；如必须，先说明并自行脱敏）。
