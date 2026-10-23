# 上游基线与同步手册（UPSTREAM）

> 本文是 VBIOS Studio 的上游**唯一事实来源**。任何依赖上游代码的构建、发布、审计都必须引用本文的 pin。修改上游版本 = 修改本文 + 走 §4 同步流程。

## 1. 上游仓库与 pin（冻结）

| # | 上游项目 | 仓库 URL | 角色 | 版本 | 当前 pin（40 位 SHA） | commit 日期 | 许可证 | 本地状态 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| A | NVIDIA VBIOS Vix Editor | <https://github.com/Panchovix/nvidia-vbios-vix-editor> | `src/nvidia_vbios/` 只读镜像（ROM 解析/编辑/normalize/字段目录） | `v0.1.28` | `1f8ee665bd175bd9ede367e6d15308f837bd987b` | 2026-10-22 | GPL-3.0 | 本地 checkout 干净（`git status --porcelain` 为空） |
| B | NVIDIA Windows VBIOS Vix Loader | <https://github.com/Panchovix/nvidia-windows-vbios-vix-loader> | Windows 注册表 override 协议参考（不直接 import） | `v0.3.1-6-gec7bdfe`（`v0.3.1` 之后 6 个提交） | `ec7bdfe317d3a52de160d17d2bb80ff20813596e` | 2026-10-21 | GPL-3.0 | 本地 checkout 干净 |

**相关但非 vendored 的上游（运行时可选依赖，不在 pin 范围）**

| 项目 | URL | 用途 | 说明 |
| --- | --- | --- | --- |
| NVIDIA Linux VBIOS Vix Loader | <https://github.com/Panchovix/nvidia-linux-vbios-vix-loader> | Linux 启动时注入修改后镜像 | 外部项目；本项目只探测/生成指引，不捆绑、不自动提权。若未来 vendored，必须补 pin 并升级本文版本。 |

### 1.1 为什么是这两个 pin

- **A（editor）** 提供经过审核的离线 ROM 解析、字段目录、编辑与 `normalize` 实现；本项目的 `domain`/`adapters` 通过其公开 API 桥接，不复制其逻辑。`v0.1.28` 含 Blackwell Advanced section、最高运行温度、出厂 GPC offset 与空校验和尾部可编辑修复。
- **B（Windows loader）** 定义注册表键名、`EnableGpuFirmware` 值、`VixLoaderPreviousEnableGpuFirmware` 备份语义、`romOverride00`–`FF` 清理与 `pnputil /restart-device` 重启流程；本项目的 Windows 适配器按该协议实现（不直接依赖其 Python 包，避免命名空间冲突）。
- 两个 pin 均为 2026-10-22 冻结时上游默认分支的 HEAD；`v0.1.28` 与 `v0.3.1` 为当时最新发布版本。

## 2. 引入方式与只读约束

### 2.1 目录布局（已落实）

```
vbios-studio/
├── src/
│   ├── nvidia_vbios/        # 上游 A 的逐字节只读镜像（vendor）
│   └── vbios_studio/        # 本项目自有代码（domain/ports/adapters/ui/app）
├── UPSTREAM.md              # 本文
└── ...
```

- `src/nvidia_vbios/` 为上游 A 在 pin SHA 的**逐字节镜像**，包括其 `pyproject` 元数据之外的所有运行时代码；不得格式化、不得加注释、不得改 import、不得“顺手修 bug”。
- 上游 bug 只能通过以下方式处理：①升级 pin；②在 `src/vbios_studio/adapters/upstream.py` 做适配层规避；③向上游提 PR。禁止直接改 vendored 文件。
- 上游 B 不 vendored：其注册表协议由 `src/vbios_studio/adapters/system/windows_registry.py` 按文档实现；若未来复用其代码，必须改为 vendored 并补 pin。

### 2.2 只读校验（已实现，CI 强制）

`tests/contract/test_version.py` 做三件事：

1. 从 `tests/contract/upstream-manifest.json` 读取 pin 与 31 个文件的 SHA-256；
2. 对 `src/nvidia_vbios/` 每个文件重新计算 SHA-256，并检查文件集合完全一致；
3. 校验 manifest 的 `commit` 与本文 §1 的 40 位 SHA 一致。

运行：

```bash
python -m pytest -q tests/contract/test_version.py
```

manifest 的当前结构：

```json
{
  "repo": "https://github.com/Panchovix/nvidia-vbios-vix-editor",
  "commit": "1f8ee665bd175bd9ede367e6d15308f837bd987b",
  "version": "0.1.28",
  "files": {
    "__init__.py": "<sha256>",
    "...": "<sha256>"
  }
}
```

> `src/nvidia_vbios/` 是**普通目录**（不是 git submodule），没有 `.git`；不要用 `git -C src/nvidia_vbios rev-parse HEAD` 校验。以 manifest + `test_version.py` 为准。

## 3. Pin 校验命令（可复制）

在仓库根目录执行：

```bash
# A. vendored 文件与 manifest 逐文件校验（推荐）
python -m pytest -q tests/contract/test_version.py

# B. manifest 中记录的 pin
python - <<'PY'
import json, pathlib
m = json.loads(pathlib.Path("tests/contract/upstream-manifest.json").read_text())
print(m["commit"], m["version"], len(m["files"]), "files")
PY

# C. 对照远程当前 HEAD（同步前检查）
git ls-remote https://github.com/Panchovix/nvidia-vbios-vix-editor.git refs/heads/main
git ls-remote https://github.com/Panchovix/nvidia-windows-vbios-vix-loader.git refs/heads/main

# D. 若本地还有独立上游 checkout，可核对
git -C ../nvidia-vbios-vix-editor rev-parse HEAD
git -C ../nvidia-windows-vbios-vix-loader rev-parse HEAD
```

期望：

| 仓库 | pin |
| --- | --- |
| `nvidia-vbios-vix-editor` | `1f8ee665bd175bd9ede367e6d15308f837bd987b` |
| `nvidia-windows-vbios-vix-loader` | `ec7bdfe317d3a52de160d17d2bb80ff20813596e` |

> 发布与同步只认完整 40 位 SHA；短 SHA、tag、分支名都不算 pin。

## 4. 上游同步流程（upstream-sync workflow + 人工审核）

### 4.1 触发

- **手动触发**（推荐）：`.github/workflows/upstream-sync.yml` 的 `workflow_dispatch`，输入目标 ref（默认 `main`）。
- **定时检查**（可选，SHOULD）：每周一次 `schedule`，仅当上游 HEAD 变化时开 PR，不自动合并。
- 禁止在普通 CI 中自动升级 pin。

### 4.2 步骤

1. **取新 HEAD**：`git ls-remote <repo> refs/heads/main`，记录完整 SHA。
2. **建分支**：`chore/upstream-sync-<sha7>`（两个仓库分开 PR，避免混合故障）。
3. **更新 vendored 副本**：用上游该 SHA 的归档覆盖 `src/nvidia_vbios/`（不是 `git merge`），重新生成 `upstream-manifest.json`。
4. **更新本文**：§1 表格的版本、SHA、commit 日期、本地状态；§5 记录同步日志。
5. **适配层回归**：`src/vbios_studio/adapters/upstream.py` 只允许调用公开 API；检查导入路径、异常类型、字段 key/单位是否变化。
6. **跑全量闸门**：
   ```bash
   ruff check .
   ruff format --check .
   mypy --strict src
   lint-imports
   pytest -q
   python tools/prepush_audit.py
   ```
   并运行 `python -m pytest -q`（若仓库提供 `tests/parity`，与上游 `nvbios fields` 的公共字段对照也一并运行）。
7. **记录**：PR 描述必须包含旧/新 SHA、变更文件数、失败/跳过用例、风险等级是否变化（字段增减/重分类）。
8. **评审**：至少 architect + reviewer 之一批准；涉及风险模型变化必须 reviewer 明确批准。
9. **合并后**：打新 tag 前确认 `UPSTREAM.md`、manifest、代码三处 SHA 一致。

### 4.3 冲突处理

- **禁止** `git checkout --ours/theirs` 整文件覆盖、禁止“以本地为准”合并 vendored 目录。
- 若上游改了本项目适配层依赖的 API：在 `adapters/upstream.py` 增加兼容 shim，保留旧字段 key 映射；不得改上游文件。
- 若上游把字段标为 `editable=false` 或改变 bounds：同步更新 `docs/risk-model.md` 与 `risk_registry.py`，并在 PR 中标注“风险模型变更”。
- 若上游删除本项目依赖的字段：先降级为只读并保留展示（T0），再评估是否移除功能；不得静默丢字段。

### 4.4 回滚

- pin 回滚 = 反向 PR：恢复上一版 vendored 副本 + manifest + 本文 SHA，跑全量闸门；禁止直接 `git reset --hard` 已发布分支。
- 回滚后必须发 patch release，并在 `CHANGELOG.md` 说明原因与影响。

## 5. 同步日志

| 日期 | 仓库 | 旧 SHA | 新 SHA | 操作人 | 测试结果 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| 2026-10-22 | editor | — | `1f8ee665bd175bd9ede367e6d15308f837bd987b` | architect（架构评审冻结） | ✅ 31 文件 manifest 哈希通过（`tests/contract/test_version.py`） | 初始 pin，v0.1.28；仓库骨架已 vendored |
| 2026-10-22 | windows-loader | — | `ec7bdfe317d3a52de160d17d2bb80ff20813596e` | architect（架构评审冻结） | ✅ 注册表协议测试通过（`tests/apply/test_windows_registry.py`） | 初始 pin，v0.3.1-6 |

## 6. 许可证与归属

- 上游 A、B 均为 **GPL-3.0**；本项目整体采用 **GPL-3.0-or-later**，衍生作品必须保留版权与许可证声明。
- 仓库根 `LICENSE`（GPL-3.0-or-later 全文）与 `NOTICE.md` 必须声明：
  - 源自 Panchovix 的 `nvidia-vbios-vix-editor` 与 `nvidia-windows-vbios-vix-loader`；
  - 非 NVIDIA 官方、未获 NVIDIA 背书；NVIDIA、GeForce 为 NVIDIA Corporation 商标；
  - 上游作者不对本项目的修改负责。
- 发布产物（tar.gz/exe）内必须包含 `LICENSE`、`NOTICE.md`、`THIRD_PARTY_NOTICES.md`（若上游要求）与本文的 pin 信息。
- 不得移除上游文件中的版权头；不得把 GPL 代码以非 GPL 许可证发布。

## 7. 当前状态

| 项 | 状态 | 承接阶段 |
| --- | --- | --- |
| 两个上游 URL 与 pin 记录 | ✅ 完成（本文 §1） | 需求冻结 |
| `src/nvidia_vbios/` vendored 副本 + 31 文件 SHA-256 manifest | ✅ 完成：`src/nvidia_vbios/`、`tests/contract/upstream-manifest.json`、`tests/contract/test_version.py` | 仓库骨架 |
| Windows 注册表协议适配 | ✅ 完成：`src/vbios_studio/adapters/system/windows_registry.py` + `tests/apply/test_windows_registry.py` | 系统适配 |
| Linux loader 探测与指引 | ✅ 完成：`src/vbios_studio/adapters/system/linux_loader.py` + `tests/apply/test_linux_loader.py` | 系统适配 |
| nvflash 硬守卫 | ✅ 完成：`src/vbios_studio/adapters/system/nvflash.py` + `tests/apply/test_nvflash_guard.py` | 系统适配 |
| `upstream-sync.yml` | ✅ 完成：`.github/workflows/upstream-sync.yml` | CI/CD |
| 同步手册 | ✅ 完成：`docs/upstream-sync.md` | 文档体系 |
| 上游 parity 对照测试 | ⏳ 由静态测试体系负责；当前字段对照覆盖见 `tests/core/test_risk_registry.py` 与 `tests/core/test_rom_structure.py` | 静态测试 |
| 同步日志自动化 | 可选；当前手工维护 §5 | 仓库整理 |

### 7.1 校验命令（发布前必跑）

```bash
python -m pytest -q tests/contract/test_version.py
python -m pytest -q tests/contract
python -m pytest -q
```

