# VBIOS Studio v0.1.1 发布后审计报告

> ⚠️ 历史记录：本报告反映当时状态，可能包含已被修复的问题。
> 当前状态见 [评审与审计索引](README.md)。

> 审计日期：2026-10-23 · 对象：[scvxzf1/vbios-studio](https://github.com/scvxzf1/vbios-studio) · Release：[v0.1.1](https://github.com/scvxzf1/vbios-studio/releases/tag/v0.1.1)
>
> **结论：PASS（软件/发布层）。** v0.1.1 的克隆、安装、测试、版本、selftest 工作树、资产校验与 tag/HEAD 一致性全部通过；真实硬件验证仍未完成，属于已声明的已知边界。

## 0. 审计范围与方法

独立执行，不复用发布者本地构建产物：

1. 从 GitHub 全新 clone main，创建干净 venv，执行 `pip install -e .`、开发依赖安装、全量 pytest、`--version` 和默认 `--selftest`。
2. 从 GitHub Release 重新下载 v0.1.1 三个资产，核对大小、`SHA256SUMS` 与实际哈希，解压 Linux 包执行版本检查和 selftest。
3. 检查 README 是否仍有“预发布”措辞、7 个指定文件的内部任务编号是否清零；复跑 `tools/prepush_audit.py --strict`。
4. 核对 tag `v0.1.1` 解引用 commit、main HEAD、GitHub Actions 的 build/release run。
5. 核对 README 与 Release 的“测试不完全 / 未在真实硬件验证”声明、支持矩阵和 About 文案。

## 1. 全新克隆与安装

```text
$ git clone --depth 1 https://github.com/scvxzf1/vbios-studio.git /tmp/v011-check
clone_exit=0
$ cd /tmp/v011-check && git rev-parse HEAD
a0e88ec0015e351680ad379ee2f59f3aa03c16a8
$ git log -1 --oneline
a0e88ec release: prepare v0.1.1
$ git ls-files | wc -l
227
```

干净 venv：

```text
$ python3 -m venv --system-site-packages /tmp/v011-venv
$ . /tmp/v011-venv/bin/activate
$ pip install -e . --no-build-isolation
Successfully installed vbios-studio-0.1.1
pip_exit=0
$ pip install -r tools/requirements-dev.txt --index-url https://pypi.org/simple
dev_install_exit=0
```

这里的 `pip install -e .` 只安装运行时包；README §开发与质量闸门明确要求先安装 `tools/requirements-dev.txt`，审计按该步骤执行。

## 2. 全量测试、版本与默认 selftest

```text
$ python -m pytest -q
224 passed in 15.34s
pytest_exit=0

$ python -m vbios_studio --version
vbios-studio 0.1.1
version_exit=0
```

默认 selftest（不传 `--screenshots`）：

```text
$ xvfb-run -a python -m vbios_studio --selftest
selftest screenshots: /tmp/vbios-selftest-9lr7szhw/screenshots
vbios-studio 0.1.1 selftest: ok (window, a11y, undo/redo, 3 screenshots)
selftest_exit=0
```

运行前后克隆目录 `git status --porcelain` 均为空：

```text
$ git status --porcelain
（无输出）
CLEAN
```

说明默认 selftest 已改为写入临时目录，不再改写 `docs-assets/screenshots`；这验证了 v0.1.1 的发布卫生修复。

## 3. 版本号一致性

```text
$ grep -nE '^version =|__version__' pyproject.toml src/vbios_studio/__init__.py
pyproject.toml:7:version = "0.1.1"
src/vbios_studio/__init__.py:3:__version__ = "0.1.1"
```

- 克隆安装后的 `python -m vbios_studio --version`：`vbios-studio 0.1.1`。
- Release tag、README 项目状态、Release Notes 与 Linux 包内 `bin/vbios-studio --version` 均为 0.1.1（§4）。

## 4. Release v0.1.1 资产

Release 元数据与实际下载（完整 SHA-256 见下表）：

| 资产 | Release 大小 | 实际大小 | Release digest / 实际 SHA-256 |
| --- | ---: | ---: | --- |
| `SHA256SUMS` | 209 B | 209 B | `sha256:801724b2…` |
| `vbios-studio-0.1.1-linux-x86_64.tar.gz` | 323,436 B | 323,436 B | `sha256:741e8b1d…` |
| `vbios-studio-0.1.1-windows-x86_64.exe` | 23,201,792 B | 23,201,792 B | `sha256:6eab9921…` |

```text
$ gh release download v0.1.1 -R scvxzf1/vbios-studio --dir /tmp/v011-release
$ cd /tmp/v011-release && sha256sum -c SHA256SUMS
vbios-studio-0.1.1-linux-x86_64.tar.gz: 成功
vbios-studio-0.1.1-windows-x86_64.exe: 成功
sha_exit=0
```

Linux 包解压与运行：

```text
$ tar -xzf vbios-studio-0.1.1-linux-x86_64.tar.gz -C /tmp/v011-linux
$ ./bin/vbios-studio --version
vbios-studio 0.1.1
$ xvfb-run -a ./bin/vbios-studio --selftest
selftest: ok (window, a11y, undo/redo, 3 screenshots)
```

包内 `bin/vbios-studio` 与 `bin/vbios-studio-gui` 权限均为 `755`；包含 `LICENSE`（35,149 B）、`NOTICE.md`（3,548 B）与 `README.md`。

## 5. README 状态与内部编号清理

### README 状态

```text
$ grep -n '预发布' README.md
（无输出，exit 1）

$ grep -n 'v0.1.1' README.md
16:> **项目状态**：v0.1.0 已发布，v0.1.1 为补丁版本。...
```

`README.md:3-12` 仍有显著的“⚠️ 测试不完全 / 未在真实硬件验证”首屏警告；`README.md:16` 已不再写“等待独立评审与发布”。

### 指定的 7 个文件内部任务编号

以下 7 个文件均无小写 `tNN` 形式的内部任务编号：

```text
README.md
UPSTREAM.md
.github/workflows/ci.yml
src/vbios_studio/adapters/README.md
src/vbios_studio/app/README.md
src/vbios_studio/i18n/README.md
src/vbios_studio/ui/README.md
```

```text
$ grep -nE '(^|[^A-Za-z0-9])t[0-9]{1,3}([^A-Za-z0-9]|$)' <上述 7 文件>
（无输出）
ZERO
```

提交历史同样干净：`git log --all --format='%h %s'` 的 21 个提交无小写内部任务编号命中。

## 6. Tag、main 与 CI 对应关系

```text
$ git ls-remote --tags origin refs/tags/v0.1.1 'refs/tags/v0.1.1^{}'
ef5cf60fafd512d41071f0f98156247d1b66a913  refs/tags/v0.1.1
a0e88ec0015e351680ad379ee2f59f3aa03c16a8  refs/tags/v0.1.1^{}

$ git ls-remote origin refs/heads/main
a0e88ec0015e351680ad379ee2f59f3aa03c16a8  refs/heads/main
```

- `v0.1.1` 是 annotated tag（tag object `ef5cf60…`），解引用 commit `a0e88ec…`。
- 远端 main HEAD 与 tag 指向 commit 完全一致。
- Release target：`main`；非 draft、非 prerelease。
- GitHub Actions build run [`39882052236`](https://github.com/scvxzf1/vbios-studio/actions/runs/39882052236)：linux/windows 两 job 成功。
- GitHub Actions release run [`39882644672`](https://github.com/scvxzf1/vbios-studio/actions/runs/39882644672)：headSha `a0e88ec…`，`build / linux-x86_64`、`build / windows-x86_64`、`publish v0.1.1` 三 job 均 `success`。

## 7. 远端卫生与许可证

- 仓库 visibility：**PUBLIC**；GitHub license：**GPL-3.0**。
- `git ls-files`：**227** 个文件；无 `.rom`/`.bin`/`.exe`/`.dll`/`.sys`/`.efi` 等禁止扩展名，无 `>1MB` 跟踪文件。
- `python3 tools/prepush_audit.py --strict`：`CONCLUSION: PASS`；`forbidden payloads: 0`、`large files: 0`、`secret findings: 0`、`.gitignore gaps: 0`、`tracked-but-ignored: 0`。
- `LICENSE` 35,149 B；`NOTICE.md` 3,548 B；两者均在仓库根与 Linux tar 包内。

## 8. 声明与支持矩阵

- README 首屏第 3-12 行、Release body、`RELEASE_NOTES.md` 首屏均包含“⚠️ 测试不完全 / 未在真实硬件验证”和已知限制。
- About：`src/vbios_studio/ui/dialogs/about_dialog.py:24` 使用 `about.comments`；`en`/`zh_CN` 的 `.po` msgid 均包含测试不完整/未验证声明。
- `README.md:81-88` 的架构家族、只读、编辑、应用、刷写与证据状态与 `docs/requirements.md:34-43` 一致；GA100 与未识别镜像均为只读/不支持，所有可编辑架构均标注本项目未验证。

## 9. 剩余风险（非阻断）

1. **真实硬件与 Windows 实机验证仍缺失**：没有真实 GPU 应用、override、Linux loader 注入、刷写或 Windows 实机测试；Release 的 Linux 包已执行 selftest，Windows exe 仅做资产哈希/元数据核对。README、Release、About 均已显著声明。
2. **Windows 二进制未在真实 Windows 环境运行**：CI 构建成功与资产校验不等同于 Windows 运行时验证；属于已知边界。
3. **公开仓库保留历史评审报告**：`docs/` 中的历史评审报告包含不同阶段的结论；当前发布依据是本报告、v0.1.1 Release 与 `docs/reviews/review-final-v2.md`，历史文件不应被当作当前状态。
4. **二次开发环境的 PyPI 可用性**：本次审计环境首次访问 PyPI 出现 SSL 临时错误；重试后 `tools/requirements-dev.txt` 安装成功，pytest 224 passed。该问题属于环境网络，不是项目依赖声明缺陷。

## 10. 最终审计结论

**PASS（软件/发布层）。**

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 新克隆 main、pip install、pytest 全绿、版本 0.1.1 | PASS | §1/§2：clone `a0e88ec`；224 passed；`--version` 0.1.1 |
| README 无“预发布” | PASS | §5：`grep '预发布' README.md` 零命中；状态为 v0.1.0 已发布 / v0.1.1 补丁 |
| 指定 7 文件内部任务编号为 0 | PASS | §5：7 文件 grep 零命中；git log 17 commits 无命中 |
| 默认 selftest 后工作树干净 | PASS | §2：`git status --porcelain` 为空；截图写入 `/tmp/vbios-selftest-*` |
| Release v0.1.1 资产重新下载、sha256 通过 | PASS | §4：`sha256sum -c` 两件成功；大小与元数据一致 |
| tag commit == main HEAD | PASS | §6：annotated tag `ef5cf60` → `a0e88ec`；main `a0e88ec`；CI 三 job success |

v0.1.1 可作为当前补丁发布基线；§9 的已知边界与历史文档事项不改变本次发布验收结果。
