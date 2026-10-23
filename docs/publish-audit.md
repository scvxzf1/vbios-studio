# VBIOS Studio 发布后审计报告

> 审计日期：2026-10-23 · 对象：[scvxzf1/vbios-studio](https://github.com/scvxzf1/vbios-studio) · Release：[v0.1.0](https://github.com/scvxzf1/vbios-studio/releases/tag/v0.1.0)
>
> **结论：PASS（软件/发布层）。** 五项发布验收全部通过；§6 保留不影响本次发布有效性的剩余风险，建议在 v0.1.1 处理。

## 0. 审计范围与方法

独立执行以下检查，未复用发布者的本地构建产物：

1. 从 GitHub 全新 `git clone`，新建 venv，执行项目安装、版本检查和 GUI `--selftest`。
2. 从 GitHub Release 重新下载全部资产，核对 `SHA256SUMS` 与实际字节哈希、资产大小，并解压 Linux 包运行。
3. 对远端 `git ls-files` 全量扫描禁止扩展名、超大文件、密钥样式与构建产物；执行仓库自带的 `tools/prepush_audit.py --strict`。
4. 检查 README、Release body、About 对话框（源码 + gettext 目录）的“测试不完全 / 未在真实硬件验证”声明。
5. 核对 tag、main HEAD、Release 元数据与 GitHub Actions release run；核对 README 支持矩阵与 `docs/requirements.md` 是否一致。

## 1. 全新克隆可用性

```text
$ git clone --depth 1 https://github.com/scvxzf1/vbios-studio.git /tmp/publish-check
clone_exit=0
$ git rev-parse HEAD
fdeb1554704d13e47876134510386f7e3f1e9085
$ git ls-files | wc -l
226
```

新 venv 与安装（使用 `--system-site-packages` 以复用系统 PyGObject/GTK4）：

```text
$ python3 -m venv --system-site-packages /tmp/publish-check-venv
$ . /tmp/publish-check-venv/bin/activate
$ pip install -e .
Successfully installed vbios-studio-0.1.0
pip_exit=0
$ python -m vbios_studio --version
vbios-studio 0.1.0
version_exit=0
$ xvfb-run -a python -m vbios_studio --selftest
vbios-studio 0.1.0 selftest: ok (window, a11y, undo/redo, 3 screenshots)
selftest_exit=0
```

测试套件：

```text
$ PYTHONPATH=/tmp/publish-check/src /home/scv/文档/vbios-编辑/vbios-studio/.venv/bin/python -m pytest -q
224 passed in 15.42s
```

说明：`pip install -e .` 只安装运行时包，不包含 `pytest`；README §开发与质量闸门明确要求先安装 `tools/requirements-dev.txt`。审计环境当前访问 PyPI 出现 SSL EOF，无法在全新 venv 内安装 pytest；因此用本机已有 dev 环境对**克隆源码**（`PYTHONPATH` 指向 `/tmp/publish-check/src`）执行全量测试，代码来源仍是新克隆。该环境限制不改变产品可用性结论。

## 2. Release 附件校验

`gh release view` 元数据与实际下载：

| 资产 | Release 标注大小 | 实际大小 | Release digest | 实际 SHA-256 |
| --- | ---: | ---: | --- | --- |
| `SHA256SUMS` | 209 B | 209 B | `sha256:3684fb7f…` | — |
| `vbios-studio-0.1.0-linux-x86_64.tar.gz` | 323,463 B | 323,463 B | `sha256:25ccf65b…` | `25ccf65b…` |
| `vbios-studio-0.1.0-windows-x86_64.exe` | 23,198,208 B | 23,198,208 B | `sha256:bf55414b…` | `bf55414b…` |

```text
$ gh release download v0.1.0 --repo scvxzf1/vbios-studio --dir /tmp/publish-release
$ cd /tmp/publish-release && sha256sum -c SHA256SUMS
vbios-studio-0.1.0-linux-x86_64.tar.gz: 成功
vbios-studio-0.1.0-windows-x86_64.exe: 成功
sha_exit=0
```

Linux 包解压后验证：

```text
$ tar -xzf vbios-studio-0.1.0-linux-x86_64.tar.gz -C /tmp/publish-linux
$ cd /tmp/publish-linux/vbios-studio-0.1.0-linux-x86_64
$ ./bin/vbios-studio --version
vbios-studio 0.1.0
$ xvfb-run -a ./bin/vbios-studio --selftest
vbios-studio 0.1.0 selftest: ok (window, a11y, undo/redo, 3 screenshots)
```

`bin/vbios-studio` 与 `bin/vbios-studio-gui` 权限均为 `755`；tar 包内包含 `LICENSE`、`NOTICE.md`、`README.md`。

## 3. 远端仓库卫生与许可证

- 仓库 visibility：**PUBLIC**；GitHub license 识别为 **GPL-3.0**。
- `git ls-files`：**226** 个文件；无 `.rom`/`.bin`/`.exe`/`.dll`/`.sys`/`.efi` 等禁止载荷扩展名。
- 无 `>1MB` 的跟踪文件；最大文件为 `src/nvidia_vbios/editor/registry.py`（234,736 B）。
- `tools/prepush_audit.py --strict`：`CONCLUSION: PASS`；`forbidden payloads: 0`、`large files: 0`、`secret findings: 0`、`.gitignore gaps: 0`、`tracked-but-ignored: 0`。
- `LICENSE`：35,149 B（GPL-3.0 全文）；`NOTICE.md`：3,548 B（上游 Panchovix 归属、GPL、非 NVIDIA 官方与商标声明）。
- `git log --all` 共 17 个提交；提交标题**没有**小写内部任务编号命中。
- 远端仓库无 `.gitignore` 未覆盖的已跟踪缓存/构建产物。

## 4. 声明落实

### README

`README.md:3-12` 首屏第一块即：

```text
> [!WARNING]
> ## ⚠️ 测试不完全 / 未在真实硬件验证
```

明确说明未在真实 GPU 执行编辑应用、Windows 注册表 override、Linux loader 注入或刷写；并列出硬件损坏风险与“修改后镜像禁止 nvflash”约束。`README.md:151-158` 再次列出未测试项。

### Release 页面

`gh release view v0.1.0` body 首屏同一警告存在；`已知限制` 段落也在 body 中（自动检查 `warning True`、`known_limits True`）。Release 描述、tag 与资产元数据均为公开状态。

### About 对话框

`src/vbios_studio/ui/dialogs/about_dialog.py:24` 将 `about.comments` 传入 `Adw.AboutDialog`；`en` 与 `zh_CN` 的 `.po` 该 msgid 均包含 “Testing is incomplete / 测试不完全” 与真实硬件未验证说明。`zh_CN` 明确写入“本项目未在真实 GPU 上验证，任何写入都可能导致硬件损坏”。

### 支持矩阵

`README.md:81-88` 的架构家族、检查、编辑、应用、刷写、证据状态与 `docs/requirements.md:34-43` 一致：GB20x/Ada/Ampere/Turing 支持代码路径，GA100 与未识别镜像只读；每一行均标注“本项目未验证/未做真机验证”。

## 5. Tag、main 与 CI 对应关系

```text
$ git ls-remote --tags origin refs/tags/v0.1.0 'refs/tags/v0.1.0^{}'
5f04ce658052379e9c0c407438fbbc3b7d827541  refs/tags/v0.1.0
fdeb1554704d13e47876134510386f7e3f1e9085  refs/tags/v0.1.0^{}
$ git ls-remote origin refs/heads/main
fdeb1554704d13e47876134510386f7e3f1e9085  refs/heads/main
```

- `v0.1.0` 是 annotated tag，解引用 commit 为 `fdeb155…`；main HEAD 同一 commit。
- Release target commitish：`main`；Release 状态：非 draft、非 prerelease。
- GitHub Actions run [`39878967865`](https://github.com/scvxzf1/vbios-studio/actions/runs/39878967865)：`success`；headSha `fdeb155…`；jobs：`build / windows-x86_64` success（约 9m54s）、`build / linux-x86_64` success（约 40s）、`publish v0.1.0` success（约 12s）。
- Release 资产的 digests 与 `SHA256SUMS` 完全一致，且下载后本地复算一致（§2）。

## 6. 剩余风险（非阻断）

1. **公开文档仍有内部任务编号（LOW/MEDIUM，建议 v0.1.1 清理）**：`UPSTREAM.md:149-174` 的同步日志/状态表有 12 处内部任务编号；`src/vbios_studio/adapters/README.md:18`、`src/vbios_studio/app/README.md:7`、`src/vbios_studio/i18n/README.md:7,17`、`src/vbios_studio/ui/README.md:5,8` 及 `.github/workflows/ci.yml:45` 也有少量。它们不影响 Release 资产安全、许可证或功能，但属于公开仓库文档卫生问题；本次审计不把历史同步日志重写为发布阻断项。
2. **README 项目状态句已过时（LOW）**：`README.md:16` 仍写“v0.1.0 预发布（…等待独立评审与发布）”，而 v0.1.0 已发布。建议在下一版改为“v0.1.0 已发布”，避免公开读者误解。
3. **干净 venv 的 pytest 依赖（LOW）**：`pip install -e .` 不安装 pytest；README §开发与质量闸门已指向 `tools/requirements-dev.txt`。本次 PyPI SSL 故障属于审计环境限制，不影响产品安装/启动。
4. **selftest 默认写回截图（LOW）**：在全新 clone 中直接运行默认 `--selftest` 会把 `docs-assets/screenshots/02-fields-risk.png` 标记为 modified（随后已 `git checkout` 还原）。这是截图资产的非确定性/重生成副作用，不影响 Release 包校验；建议 v0.1.1 将默认截图写入临时目录或加 `--check` 模式。
5. **真实硬件与 Windows 实机验证仍缺失（已知边界，保留）**：没有真实 GPU 应用、注册表 override、Linux loader 注入、刷写或 Windows 实机验证；Release 资产在 Linux 上验证，Windows exe 仅做资产哈希与元数据检查。README/Release/About 均已显著声明，因此不构成隐性风险。

## 7. 最终审计结论

**PASS（软件/发布层）。**

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| 全新克隆安装 + `--selftest`（Linux） | PASS | §1；clone `fdeb155`，`--version` 与 selftest exit 0 |
| Release 附件 SHA-256 与 Linux 包可执行 | PASS | §2；`sha256sum -c` 两件成功，解压包 selftest exit 0 |
| 远端卫生/许可证 | PASS | §3；226 文件、prepush PASS、LICENSE/NOTICE 在位 |
| README + Release 声明 | PASS | §4；首屏 warning、Release body、About i18n 均验证 |
| PASS/FAIL 与剩余风险 | PASS | §6 列出 5 项非阻断风险 |

本次 Release 可作为 v0.1.0 对外发布基线；剩余风险属于后续文档/可复现性改进，不影响当前 Release 的资产完整性与用户安全声明。
