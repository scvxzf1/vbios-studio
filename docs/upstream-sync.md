# 上游同步手册

| 项目 | 值 |
| --- | --- |
| 当前 pin（editor） | `1f8ee665bd175bd9ede367e6d15308f837bd987b`（v0.1.28） |
| 当前 pin（windows loader） | `ec7bdfe317d3a52de160d17d2bb80ff20813596e`（v0.3.1-6） |
| vendored 目录 | `src/nvidia_vbios/`（31 个文件，逐字节只读） |
| 完整性 manifest | `tests/contract/upstream-manifest.json` |
| 自动 workflow | `.github/workflows/upstream-sync.yml`（手动触发） |
| 事实来源 | [`../UPSTREAM.md`](../UPSTREAM.md) |

> 任何同步都必须以**完整 40 位 commit SHA**为准；tag、短 SHA、分支名都不算 pin。同步完成后 `UPSTREAM.md`、manifest、代码三者必须一致。

## 1. 同步前检查

```bash
# 进入仓库根目录
cd vbios-studio

# 1) 本地工作区必须干净
git status --porcelain

# 2) 当前 pin
grep -nE '^\| [AB] \|' UPSTREAM.md
git -C ../nvidia-vbios-vix-editor rev-parse HEAD
git -C ../nvidia-windows-vbios-vix-loader rev-parse HEAD

# 3) 上游当前 HEAD（决定是否有新版本）
git ls-remote https://github.com/Panchovix/nvidia-vbios-vix-editor.git refs/heads/main
git ls-remote https://github.com/Panchovix/nvidia-windows-vbios-vix-loader.git refs/heads/main

# 4) 当前完整性基线必须绿
python -m pytest -q tests/contract/test_version.py
```

## 2. 手动同步 editor（vendored 包）

### 2.1 取上游归档到临时目录

```bash
UPSTREAM_SHA=1f8ee665bd175bd9ede367e6d15308f837bd987b   # 替换为目标 40 位 SHA
TMP=$(mktemp -d)
git clone --filter=blob:none --no-checkout \
  https://github.com/Panchovix/nvidia-vbios-vix-editor.git "$TMP/editor"
git -C "$TMP/editor" fetch --depth 1 origin "$UPSTREAM_SHA"
git -C "$TMP/editor" checkout --detach "$UPSTREAM_SHA"
git -C "$TMP/editor" rev-parse HEAD   # 必须等于 UPSTREAM_SHA
```

### 2.2 替换 `src/nvidia_vbios/`（只替换该目录，不 merge）

```bash
# 先建同步分支
git switch -c "chore/upstream-sync-$(printf '%s' "$UPSTREAM_SHA" | cut -c1-7)"

# 用归档内容替换，不要 git merge vendored 目录
rm -rf src/nvidia_vbios
mkdir -p src
cp -a "$TMP/editor/src/nvidia_vbios" src/nvidia_vbios
find src/nvidia_vbios -name '__pycache__' -type d -prune -exec rm -rf {} +
find src/nvidia_vbios -name '*.pyc' -delete
```

### 2.3 重新生成 manifest

```bash
python - <<'PY'
import hashlib, json
from pathlib import Path

root = Path("src/nvidia_vbios")
files = {}
for path in sorted(root.rglob("*")):
    if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
        files[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()

manifest = {
    "repo": "https://github.com/Panchovix/nvidia-vbios-vix-editor",
    "commit": "REPLACE_WITH_40_CHAR_SHA",
    "version": "REPLACE_WITH_UPSTREAM_VERSION",
    "files": files,
}
Path("tests/contract/upstream-manifest.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(len(files), "files hashed")
PY
```

### 2.4 更新 `UPSTREAM.md`

必须同时更新：

1. §1 表格的 `版本`、`当前 pin（40 位 SHA）`、`commit 日期`、`本地状态`；
2. §5 同步日志新增一行（日期、旧 SHA、新 SHA、操作人、测试结果、备注）；
3. 若上游改了字段/风险行为，同步更新 `docs/risk-model.md` 与 `src/vbios_studio/domain/risk_registry.py`；
4. 不修改 `src/nvidia_vbios/` 内任何文件（格式、注释、import 都不行）。

## 3. 手动同步 windows loader（协议参考）

上游 B **不 vendored**，只用于核对注册表协议。同步步骤：

```bash
TMP=$(mktemp -d)
git clone --depth 1 https://github.com/Panchovix/nvidia-windows-vbios-vix-loader.git "$TMP/loader"
git -C "$TMP/loader" rev-parse HEAD

# 对照 README 的注册表键/值/重启语义
# 如果协议变化：只改 src/vbios_studio/adapters/system/windows_*.py，并跑：
python -m pytest -q tests/apply/test_windows_registry.py
```

需要核对的协议点：

- `HKLM\SYSTEM\CurrentControlSet\Control\Class\{4d36e968-e325-11ce-bfc1-08002be10318}\NNNN`
- `vbios`（REG_BINARY）、`EnableGpuFirmware=0x11`（REG_DWORD）
- `VixLoaderPreviousEnableGpuFirmware`（REG_SZ，首次 load 保存，含 `absent`）
- 清理 `romOverride00`–`romOverrideFF`
- `pnputil /restart-device`
- `verify` / `status` / `unload` 状态语义

## 4. 自动 workflow

`.github/workflows/upstream-sync.yml` 支持手动触发：

| 输入 | 说明 |
| --- | --- |
| `upstream` | `editor` 或 `loader` |
| `ref` | 分支、tag 或 commit SHA（建议完整 SHA） |

行为：

1. `git fetch` 指定上游与 ref，解析完整 SHA；
2. 在 `sync/<upstream>-<UTC 时间>` 分支尝试 `git merge --no-commit --no-ff`；
3. 无冲突：提交并开 PR，PR 描述要求更新 `UPSTREAM.md` 与跑全量测试；
4. 有冲突：**立即 `git merge --abort`**，在干净分支上写 `docs/upstream-sync-conflict.md`（冲突路径 + 处理清单），推送并开 **draft PR**；
5. 不自动合并、不覆盖本地文件、不自动改 pin。

> workflow 只做机械合并；**pin 更新与风险模型复核仍由人完成**。

## 5. 冲突处理流程

1. 打开 draft PR，阅读 `docs/upstream-sync-conflict.md` 的冲突路径。
2. 逐文件人工解决；**禁止** `git checkout --ours` / `--theirs` 整文件覆盖，禁止把 vendored 目录整体替换后不检查。
3. 若冲突在 `src/nvidia_vbios/`：以目标 SHA 的上游文件为准，重新复制该文件（不要手改），然后重新生成 manifest。
4. 若冲突在 `src/vbios_studio/`：以本项目的接口/行为为准，适配上游 API 变化；新增 shim 时保留旧字段 key 映射。
5. 若上游删除本项目依赖的字段：先降级为 T0 只读并保留展示，再评估功能移除；不得静默丢字段。
6. 解决后跑全量闸门（见 §6），把 draft PR 标为 ready 并请求 review。
7. 合并后删除同步分支；不要 `git push --force` 到 `main`。

## 6. 同步后的验证闸门

```bash
# 1) 上游只读 + manifest
python -m pytest -q tests/contract/test_version.py

# 2) 契约与分层
python -m pytest -q tests/contract

# 3) 核心/应用/UI/i18n/release
python -m pytest -q

# 4) 静态
ruff check src tests
ruff format --check src tests
mypy --strict src/vbios_studio
lint-imports

# 5) 一键 CI 等价
bash tools/build_local.sh --check
```

若上游字段/风险变化，额外：

```bash
python -m pytest -q tests/core/test_risk_registry.py
python -m pytest -q tests/i18n
```

## 7. `UPSTREAM.md` pin SHA 更新规则

1. 只写**完整 40 位十六进制 SHA**；禁止短 SHA、tag、`main`。
2. `UPSTREAM.md` §1 表格、`tests/contract/upstream-manifest.json` 的 `commit`、同步日志三处必须一致。
3. 每个 pin 更新单独 PR；editor 与 loader 不同时混在一个 PR（除非两者都只是文档 pin 更新）。
4. PR 描述必须包含：旧 SHA、新 SHA、上游版本、变更文件数、全量测试结果、风险等级是否变化。
5. 涉及风险模型/字段可编辑性变化：必须由 reviewer 明确批准；更新 `docs/risk-model.md` 与 `risk_registry.py`。
6. 合并前确认 `git diff --stat` 没有 `src/nvidia_vbios/` 之外的意外改动；合并后打 tag 前再跑一次 `test_version.py`。

## 8. 回滚

```bash
# 在同步分支上反向恢复上一版 vendored 文件与 manifest
git revert <sync-commit>

# 或从上一个 pin 重新复制（不要 reset 已发布 main）
UPSTREAM_SHA=<old-40-char-sha>
# 重复 §2.1–§2.4
```

回滚后发 patch release，并在 `CHANGELOG.md` 记录原因、影响的字段/风险等级。

## 9. 常见故障

| 现象 | 处理 |
| --- | --- |
| `test_version.py` 报 manifest 文件集合不一致 | 检查是否多/少文件；重新执行 §2.3 生成 manifest |
| `test_version.py` 报某文件哈希不一致 | 该 vendored 文件被修改；从上游目标 SHA 重新复制，不要手改 |
| `lint-imports` 报 `domain-pure` 失败 | 检查是否在 domain 中 import 了 gi/nvidia_vbios/adapters |
| UI 字段显示 T0 只读 | 上游字段未在 `risk_registry.py` 注册；按 `docs/risk-model.md` 先归类再开放 |
| 同步后 i18n 缺失 | 新 msgid 必须同时加入 `en` 与 `zh_CN` 的 `.po`/`.mo`；见 [`i18n.md`](i18n.md) |
