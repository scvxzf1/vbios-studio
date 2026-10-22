# VBIOS Studio v0.1.0 全量验收报告

- 验收日期：2026-10-23（Asia/Shanghai）
- 验收对象：`/home/scv/文档/vbios-编辑/vbios-studio`（当前工作树；此阶段尚未初始化 Git 仓库，验收对象以文件系统内容为准）
- 验收人：QA（独立执行）
- 结论：**软件层 PASS**。所有可执行的自动化测试、静态闸门、合成 ROM 端到端流程、Linux 分发包构建与启动均通过；真实 GPU 应用/刷写、Windows 实机、各厂商机型差异与 Volta 架构未验证，详见 §8。任何测试都不构成对真实硬件的安全保证。

## 1. 验收环境

| 项 | 值 |
| --- | --- |
| 主机 | Linux 6.8.0-136-generic x86_64 |
| 发行版 | Ubuntu 24.04.5 LTS |
| Python | 3.12.3（`/usr/bin/python3`） |
| PyGObject | 3.48.2（系统包） |
| GTK / Adw | GTK 4.14 / Adw 1.5 |
| 显示 | `/usr/bin/xvfb-run` + Xvfb（离屏） |
| GTK 开发文件 | `gtk4.pc`、`libadwaita-1.pc` **缺失**；因此不通过 pip 编译 PyGObject，venv 使用 `--system-site-packages` |
| pip 索引 | `https://pypi.org/simple`（本机默认镜像 TLS 不可达，显式覆盖） |

## 2. 干净虚拟环境重建与全量测试

### 2.1 建库与安装

```bash
rm -rf /tmp/vbios-t9-venv
python3 -m venv --system-site-packages /tmp/vbios-t9-venv
/tmp/vbios-t9-venv/bin/python -m pip install \
  --index-url https://pypi.org/simple \
  -r tools/requirements-dev.txt
/tmp/vbios-t9-venv/bin/python -m pip install \
  --index-url https://pypi.org/simple --no-build-isolation -e .
```

| 步骤 | 退出码 | 结果 |
| --- | --- | --- |
| `python3 -m venv --system-site-packages /tmp/vbios-t9-venv` | 0 | 新建干净 venv，能导入系统 PyGObject 3.48.2 |
| 安装 `tools/requirements-dev.txt` | 0 | pytest 9.1.1、ruff 0.17.1、mypy 2.4.0、import-linter 2.15、PyYAML 6.0.3 |
| 安装 `-e .` | 0 | `vbios-studio==0.1.0` editable；未尝试编译 PyGObject |

### 2.2 全量测试矩阵

在仓库根目录使用干净 venv 执行：

```bash
/tmp/vbios-t9-venv/bin/python -m pytest -q
```

| 命令 | 退出码 | 证据 |
| --- | --- | --- |
| `/tmp/vbios-t9-venv/bin/python -m pytest -q` | 0 | **189 passed, 1 skipped in 17.79s** |
| `/tmp/vbios-t9-venv/bin/ruff check src tests` | 0 | `All checks passed!` |
| `/tmp/vbios-t9-venv/bin/ruff format --check src tests` | 0 | `137 files already formatted` |
| `/tmp/vbios-t9-venv/bin/mypy src/vbios_studio` | 0 | `Success: no issues found in 72 source files` |
| `/tmp/vbios-t9-venv/bin/lint-imports` | 0 | `Contracts: 5 kept, 0 broken.` |

**skip 说明（不是失败）**：`tests/hygiene/test_gitignore.py::test_gitignore_covers_generated_artefacts_when_present` 因 `.gitignore` 按计划由仓库整理阶段交付而 skip。该文件的策略函数、完整模板和“缺失模式必被检出”的反例测试均已通过；仓库整理完成后此 skip 应消失。其余 189 条全部通过，失败用例数为 **0**。

### 2.3 本地 CI 等价入口

```bash
bash tools/build_local.sh --check
```

退出码 **0**。脚本完成：ruff check、ruff format --check、mypy --strict、lint-imports（5 kept）、pytest（189 passed, 1 skipped）、`python -m vbios_studio --version`（`vbios-studio 0.1.0`）。脚本内部 venv 使用 `--system-site-packages`，所有 pip 调用显式使用 `PIP_INDEX_URL`。

## 3. 端到端流程演练

使用合成 ADA ROM（`tests/core/rom_fixtures.py` 现场生成，`copies=2`，8 张镜像），通过真实 `build_gui_controller()` 和真实 `UpstreamEditorAdapter` 执行；应用面板使用 fake Windows 注册表后端与 fake runner，确保零真实系统写入。

```bash
/tmp/vbios-t9-venv/bin/python /tmp/t9_e2e.py
```

退出码 **0**，输出：

```text
PASS open architecture=ada images=8
PASS t3-confirmation-required field=power_max_w risk=T3
PASS t3-confirmed batch_risk=T3 changes={'power_max_w': '100'}
PASS save target=generated.rom source_sha_unchanged=e9e6a5a1b68d images=8 checksums_all_balanced=True manifest=generated.rom.json
PASS apply-dry-run action=load bytes=24592 writes=0 subprocess_calls=0
PASS apply-execute state=override-active restore state=no-override original_value=0x12 restored=True
```

逐项说明：

1. 打开合成 ROM：识别为 Ada，8 张镜像。
2. T3 实验字段 `power_max_w`：未确认时抛 `ConfirmationRequired`；解锁实验模式并传 `t3_confirmed=True` 后才进入 staged changes，batch risk 为 T3。
3. 生成新文件：目标 ROM 写入成功，源文件 SHA-256 前后不变，manifest 生成。
4. 校验和自愈：`scan_rom` 对全部 8 张镜像断言 `checksum_ok=True`。
5. 应用 dry-run：`writes=0`、`subprocess_calls=0`，注册表 mutation 列表不变。
6. 执行与还原：fake 注册表写入 override 后，`apply_restore` 恢复首次 load 前的 `EnableGpuFirmware=0x12`，并清理 override 值。

> 该流程只证明软件逻辑与假后端协议；没有在真实 GPU、真实注册表或真实 nvflash 上执行。

## 4. Linux 分发包构建与启动

```bash
bash tools/build_local.sh --dist
```

退出码 **0**，生成：

- `dist/vbios-studio-0.1.0-linux-x86_64.tar.gz`
- `dist/SHA256SUMS`
- 归档大小：302,875 字节
- SHA-256：`79d7ead03f4d1ae840c1ee63d4c521240064e76fbba5e6553b4433b94e86f4e2`

在临时目录解压后验证：

```bash
tar -xzf dist/vbios-studio-0.1.0-linux-x86_64.tar.gz -C /tmp/vbios-t9-dist
cd /tmp/vbios-t9-dist/vbios-studio-0.1.0-linux-x86_64
./bin/vbios-studio --version
xvfb-run -a ./bin/vbios-studio --selftest
```

| 命令 | 退出码 | 证据 |
| --- | --- | --- |
| `sha256sum -c dist/SHA256SUMS`（dist 目录内） | 0 | `vbios-studio-0.1.0-linux-x86_64.tar.gz: 成功` |
| `./bin/vbios-studio --version` | 0 | `vbios-studio 0.1.0` |
| `xvfb-run -a ./bin/vbios-studio --selftest` | 0 | `vbios-studio 0.1.0 selftest: ok (window, a11y, undo/redo, 3 screenshots)` |
| `VBIOS_STUDIO_PYTHON=/tmp/vbios-t9-venv/bin/python ./bin/vbios-studio --version` | 0 | 用干净 venv 解释器启动解压包，`vbios-studio 0.1.0` |
| `VBIOS_STUDIO_PYTHON=/tmp/vbios-t9-venv/bin/python xvfb-run -a ./bin/vbios-studio --selftest` | 0 | `vbios-studio 0.1.0 selftest: ok (window, a11y, undo/redo, 3 screenshots)` |

启动说明：Linux 包是源码分发包，launcher 默认使用 `/usr/bin/python3` 以使用系统 `python3-gi`/GTK 4；这是本机缺少 `gtk4.pc` 时的既定打包方式，不是缺陷。上表最后两行进一步验证了同一解压包可被干净 venv 的 Python 启动。测试期间出现的 `libEGL` DRI3 与 AT-SPI 警告来自无显示服务器的 xvfb 环境，命令仍以 0 退出。

## 5. README 与文档一致性

### 5.1 README 相对路径与截图

| 检查 | 结果 |
| --- | --- |
| README Markdown 本地链接 | 21 条，缺失 0 条 |
| `docs-assets/screenshots/*.png` | 3 张 |
| PNG 魔数 | 3/3 通过 `\x89PNG\r\n\x1a\n` |
| 截图尺寸 | 3 张均为 1270 × 830，均 ≥ 800 × 600 |
| README `docs/*.md` 引用 | 全部存在 |

### 5.2 file-tree 与实际文件树

| 检查 | 结果 |
| --- | --- |
| `tests/contract/test_docs_tree.py` | 9 passed |
| `tests/contract/test_structure_audit.py` | 4 passed |
| `src/vbios_studio` Python 模块 | 72 个，全部在 `docs/file-tree.md` 中列出且路径存在 |
| `tests/` 测试文件 | 全部在 `docs/file-tree.md` 的 tests 表中出现（含 `test_selftest_process.py`） |
| `docs/` 文档 | `requirements-review.md`、`verification-report.md` 等全部在 file-tree 中列出 |
| 模块 docstring / 400 行上限 | 全部通过 |

## 6. 仓库卫生审计

测试与打包完成后清理了所有生成物，再以独立脚本扫描（不含 `.venv` 与生成缓存）：

| 检查项 | 结果 |
| --- | --- |
| `tools/checks/repo_hygiene.scan_repository()` findings | **0** |
| `.rom` / `.bin` / `.exe`（`.venv` 外） | 0 个 |
| > 1 MB 文件（`.venv` 外） | 0 个 |
| `__pycache__` 目录（`.venv` 外） | 0 个 |
| `build/`、`dist/` 残留 | 不存在（验收后已清理） |
| 密钥/凭证模式 | 0 命中 |
| `.gitignore` | 本阶段尚未交付（由后续仓库整理阶段创建）；相关测试 1 条 skip，策略与反例测试已通过 |

> `.venv/` 是本地开发环境，不提交；其内部缓存不计入上述仓库卫生结论。

## 7. 上游对照测试证据

```bash
/tmp/vbios-t9-venv/bin/python -m pytest -q tests/golden
```

退出码 **0**，**8 passed**。其中 `tests/golden/test_upstream_parity.py` 5 条全部通过：

- 合成 Ada ROM：与 vendored `nvidia_vbios.rom.from_bytes + inspect_image` 对比 30 个上游公共字段，按 `key` 的集合、顺序与公共属性逐项一致，parity issues = 0。
- 合成 Ampere ROM：同样对比 39 个上游公共字段，parity issues = 0。
- 额外目录项只允许 `CANONICAL_FIELD_KEYS` 中的 T0 只读占位；`FieldSnapshot` 新增元数据仅允许 `section`、`risk`、`description`、`experimental`，并有篡改/缺字段/未声明额外键的反例测试。
- `tests/golden/test_catalog_golden.py` 3 条通过：字段总数（Ada 109 / Ampere 114）、可编辑数、风险分布、前五个字段与序列化确定性均符合 golden。

## 8. 未验证 / 无法验证矩阵

| 项目 | 状态 | 原因/影响 |
| --- | --- | --- |
| 真实 GPU 上应用编辑后的 VBIOS | ❌ 未验证 | 无真实测试硬件；所有应用路径使用 fake 注册表/fake runner |
| 真实 nvflash 刷写 | ❌ 未验证且默认禁用 | 修改镜像会破坏签名；生产守卫只允许未修改原厂镜像，且真实刷写未在硬件执行 |
| Windows 实机注册表 override / 驱动重启 / Verify | ❌ 未验证 | 需要 Windows + NVIDIA GPU + 管理员；本机只有 fake Windows 后端与静态 CI 配置 |
| Linux loader 实际注入 | ❌ 未验证 | 需要真实 GPU、内核与 root；适配器只生成可复制 payload 与指引 |
| 各厂商/机型/散热/供电差异 | ❌ 未验证 | 无硬件矩阵；只使用合成 Ada/Ampere 结构 |
| Volta 架构 | ❌ 未验证 | 本里程碑未提供 Volta 写支持，只作为只读研究遗留 |
| 长时间稳定性/压力/热测试 | ❌ 未验证 | 无实验室环境 |
| Windows 分发包实机运行 | ⚠️ 仅静态验证 | CI workflow / Nuitka 配置已检查，未在本机 Windows 执行 |
| macOS / 32 位 / ARM | ❌ 不支持 | 首版范围外 |
| 真实用户 ROM | ❌ 不使用 | 仓库和测试只使用脚本合成 ROM，不收集或上传用户固件 |

## 9. 最终结论与已知限制

1. **软件层结论：PASS**。干净 venv 全矩阵 189 passed / 1 skipped / 0 failed；四项静态闸门 exit 0；端到端合成流程、Linux 分发包构建/启动与上游字段 parity 均通过。
2. **唯一 skip** 是 `.gitignore` 由后续仓库整理阶段交付，不是测试失败；交付 `.gitignore` 后应重新运行 `pytest -q` 并达到 0 skip。
3. **不能从本报告推断真实硬件安全**：没有真实 GPU、Windows 实机、loader 注入或 nvflash 刷写验证。README/docs 中的“测试不完全/未在真实硬件验证”声明仍然有效，发布说明必须保留该声明。
4. GTK 运行时依赖系统 `python3-gi`；本机缺少 `gtk4.pc`/`libadwaita-1.pc`，因此不能把“pip 可编译 PyGObject”作为验收前提。
