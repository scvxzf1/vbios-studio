# VBIOS Studio 增量复审报告（第三轮）

> 评审角色：reviewer · 评审日期：2026-10-23 · 被评审交付：T3 批次确认/预设替换提示修复 与 文档口径修复
>
> **结论：PASS（软件层）**。F8/F9/F10 的核心关闭条件均满足；全量 213 passed，lint-imports 5/5，既有 T3 门控与票据测试未被削弱。另记录 4 项非阻断文档/文案观察（§5），建议发布前处理。
>
> 前一轮 `docs/review-report.md` 的 33 文件绑定已被本轮改动取代；本报告是新的、内容绑定的发布依据。旧报告文件不在本任务 inScope，未修改。

## 0. 评审基线（内容绑定）

**本评审针对以下 37 个文件；评审结束时逐项复算，任一变化即判 `needs_revision` 并指出被改动文件。**

| # | 文件 | 字节数 | SHA-256 |
| --- | --- | ---: | --- |
| 1 | `README.md` | 13,898 | `f2ede61059a96a05c9c3b14a40b8b2c72ae693d8a7a716cadd8a62a4390e8417` |
| 2 | `pyproject.toml` | 3,539 | `8d5ef77f61ca9914625a81a57c650f5e86ac300542f342b9fd0460b25e61e2d1` |
| 3 | `docs/requirements.md` | 38,009 | `2e60a573c60661f37a167d504e45e0553b5318325caa8c332ab94cd13e4b8050` |
| 4 | `docs/risk-model.md` | 29,564 | `dbf0eb0d884e1a907dcdcfd796a752b7b6aabcf79aa314cddf9062c9b2852468` |
| 5 | `docs/architecture.md` | 15,050 | `e2e741afe768e1568a263fb9536474633c1e12f770ecbd3254e7ee71393b24e1` |
| 6 | `docs/testing.md` | 8,642 | `cd9441f2f2e4b037e7d8fbb117d467a355040de3a41dd822b198d29658ee32e3` |
| 7 | `docs/file-tree.md` | 15,153 | `0f592055661ca5abcc31b3b8f769c7fea4c763da4b5e040592a0185aa016266c` |
| 8 | `docs/i18n.md` | 5,173 | `68f856ecaefd53b76f95b87fc5f64c691366c01e0059567bbb546a217acdbf6c` |
| 9 | `src/vbios_studio/domain/rom.py` | 11,948 | `4226512ca2ce1ea8e83e3c8e0e4da4c9a0a862a4550f44050f80f90c1038b5a1` |
| 10 | `src/vbios_studio/adapters/system/nvflash.py` | 13,226 | `b07c7b446daa2f22c4ee3cfb933401d0639aad049d5660db46b5705bc6310932` |
| 11 | `src/vbios_studio/app/container.py` | 3,179 | `d24bc26a3054a2ecdf605d24cb4b834228212b61f3bcca2f728ab2e6c4ef380a` |
| 12 | `src/vbios_studio/ports/apply.py` | 1,447 | `4c80b357a8068be03e9694eb16130035ec8db803317739a7d9c355108c25b19f` |
| 13 | `src/vbios_studio/adapters/system/windows_registry.py` | 14,682 | `465e502753742fe0ded503d8b42b7222b78623beb3e2b4295aa424b76e3c1b0d` |
| 14 | `src/vbios_studio/adapters/system/windows_winreg.py` | 5,972 | `fa9ed4e7d321ddedad49e8a7cd5cffed43050e2e2caf52dbf232c2c1c8cbf3dc` |
| 15 | `src/vbios_studio/adapters/system/windows_verify.py` | 2,115 | `d650da65feb601d63fc6f09e7e7855096140246bfe379083496aab4c74f2791d` |
| 16 | `src/vbios_studio/adapters/system/linux_loader.py` | 7,283 | `42c3164b88e48af69ba4421a7b6128cb2411560bb2ea1998aa8e540409257a29` |
| 17 | `src/vbios_studio/ui/apply_actions.py` | 3,894 | `f72b6fbab8fc298a90cb7b55f1cd494e5fa3cfcfb835e28fd82ee868a33130e4` |
| 18 | `src/vbios_studio/ui/controller.py` | 10,586 | `7deaa91a2b9253dfb1b3afcf7da840945e4717efb6b2cb4757402a816ea79ab7` |
| 19 | `src/vbios_studio/ui/controller_errors.py` | 968 | `61325f6500c99c8eb1afece94e8d9fd9e599ba93157e6411bf697efe986a77d9` |
| 20 | `src/vbios_studio/ui/profile_controller.py` | 3,811 | `3eac00526869e58f641e3e6d73ffc6917cc7990cc15e6258317e3da030386a33` |
| 21 | `src/vbios_studio/ui/profile_flow.py` | 6,624 | `2033bc541567a46728bde78f1f0d5ad12a87d58ee6aa5781d4d81c16e2c9eb65` |
| 22 | `src/vbios_studio/ui/theme.py` | 5,847 | `ca299998bcd6a449f7096da48092ca9445f96b1e9309b939d28fd81ccb3d14cd` |
| 23 | `src/vbios_studio/ui/components/apply_panel.py` | 14,045 | `8b3f084d6bc26028d9d72755da6e00ef4a3956b47120e2d71218f86e7926d0c7` |
| 24 | `src/vbios_studio/ui/components/settings.py` | 1,253 | `2025fedba3155c11b450a678dd747b6c96e73e3195cebbd4b75168f80e606de9` |
| 25 | `src/vbios_studio/ui/main_window.py` | 14,322 | `7e977fdfa299e532d7434600610f299fe8f0010ec5d48d7bb5b4879822ee7fbb` |
| 26 | `src/vbios_studio/ui/window_dialogs.py` | 5,370 | `99b1a3641819753590429bb002ed54dedbb9bc903a56591bb32cfa44e1af78f5` |
| 27 | `src/vbios_studio/ui/dialogs/confirm_dialog.py` | 5,147 | `f3ac7f811489237fb8d5afda674ace3e00d2ba8bfe7a26ded387e034824ebdff` |
| 28 | `src/vbios_studio/i18n/locale/en/LC_MESSAGES/vbios_studio.po` | 19,304 | `34653667efc7529cb734f27bf4e4e0d3bdc23d73d127fb88e730758942dccf2f` |
| 29 | `src/vbios_studio/i18n/locale/zh_CN/LC_MESSAGES/vbios_studio.po` | 19,020 | `83393ebd367cf0f28ae2a9758249d95c4b8ad014088cf1f52e770753b6022c8f` |
| 30 | `tests/integration/test_real_controller.py` | 3,602 | `75bf0ecf77b94c0169c53dffdb002fecbbfc8574b864aa8a0f3941a27fd99950` |
| 31 | `tests/apply/test_windows_registry.py` | 8,540 | `6831fcc3673272ad0c9910613fca58fe5ff2fff82dd930e859b176b20c062261` |
| 32 | `tests/apply/test_linux_loader.py` | 3,446 | `8e85fe0f5cddff479f4de994d047d770d88dfe340166b3c2dac67ba2eb82bc13` |
| 33 | `tests/ui/test_profile_t3_gate.py` | 3,641 | `45131889bef09faee42f121b2bc35a3e4befab38051e371ac11807e27ac64b5a` |
| 34 | `tests/ui/test_apply_panel.py` | 5,326 | `485cdf1c4f1d513074380c7718085d0b2c3aa74d10d58a094cb57b9abb9f1115` |
| 35 | `tests/ui/test_confirmation_words.py` | 1,468 | `437c7db95aa120ac3eadbcddb18258949def065fc581621874f260b60509cd7c` |
| 36 | `tests/ui/test_apply_confirmation.py` | 2,899 | `9bf7592701226c6cac5b1cab1fa18e065e2567de4b68b3c9c876ee4a87b85846` |
| 37 | `tests/ui/test_profile_replace.py` | 4,556 | `34ad9ef7fe9e8660e7974fd91d251fe3c23982217ef4c72a4d287f5650a148f3` |

基线登记时间：2026-10-23T03:09+08:00。评审期间未修改上表任何文件；尾校验见 §7。

## 1. 评审范围与方法

- 增量核对 F8/F9（T3 批次确认/预设替换提示）与 F10（文档口径），并复核本轮是否削弱既有 T3 门控/票据测试。
- 独立执行：全量 `pytest`、`lint-imports`、`ruff`、`format --check`、`mypy --strict`、`tools/prepush_audit.py --strict`、3 进程并发 GUI selftest、目标测试子集、文档 grep 与 `test -f`。
- 只写入本文件 `docs/review-delta-report.md`；未改动源码、测试、既有文档或旧评审报告。
- 行号针对 §0 基线字节；本轮不需要修改代码，因此不存在“修复后行号漂移”的同一文件复评问题。

## 2. F8：T3 批次横幅与最终应用确认正文

**结论：PASS。**

代码路径：

- `src/vbios_studio/ui/components/apply_panel.py:26-40`：`T3 changes`/`T3 change lines` helper 从 `controller.preview.changed` 过滤 `risk == "T3"`，每行包含 key、旧值→新值、单位、`[T3]`。
- `src/vbios_studio/ui/components/apply_panel.py:47-62`：`registry_write_keys()` 从 `ApplyPreview.values` 生成 `target\name`，并展开 `delete` 列表为 `name (delete)`；元数据键排除。
- `:95-103`：新增 `T3 banner`（`vb-warning` + 红色 T3 样式类），`:213-224` 的 `refresh_t3_banner()` 动态渲染；`MainWindow._on_controller_event("changes")` 会在每次 staged edit 后刷新（`main_window.py:173-177`）。
- `:288-295`：`request_execute()` 把完整 T3 明细与注册表键追加到最终确认正文。
- `src/vbios_studio/ui/theme.py` 新增红色 T3 样式类。

测试证据：

```text
$ .venv/bin/python -m pytest -q tests/ui/test_apply_confirmation.py tests/ui/test_profile_replace.py
8 passed in 0.14s
```

`tests/ui/test_apply_confirmation.py:27-62` 断言横幅包含 `power_max_w`、`power_default_w`、两组 `250 → 300/350`、`[T3]`，并断言最终确认 body 含 T3 明细与 `vbios`/`EnableGpuFirmware`；`:63-83` 覆盖 target/delete 键生成。

**非阻断准确性问题（§5.3）**：`registry_write_keys()` 目前枚举 `ApplyPreview.values` 的全部非元数据项；`plan_load()` 即使已有 previous-value 备份、不会写 `VixLoaderPreviousEnableGpuFirmware`，该键仍可能被列为“将写入”。这是“多列一个只读键”的展示精度问题，不会漏掉实际写入键，也不改变 T3 门控；建议后续按 plan steps 生成精确的 write/delete 集合。

## 3. F9：预设替换前提示

**结论：PASS。**

代码路径：

- `src/vbios_studio/ui/profile_flow.py:27-36`：`uncovered_change_keys(existing, document)` 返回当前 `controller.changes` 中未被 profile `changes` 覆盖的 key。
- `:45-50`：`apply_document()` 在调用 controller 前检查；有未覆盖 key 时进入 `_confirm_replace`，不直接 stage。
- `:52-69`：确认框标题复用 `edit.reset`，正文由 `status.unsaved`（当前 N 项未保存改动）+ 未覆盖 key 列表 + 安全说明组成；取消不调用 controller，确认才 `_start`。
- 既有 T3 逐字段确认仍在 `_start/_ask`：`:71-143`；替换提示不会绕过 T3 门控。

测试证据：

```text
$ .venv/bin/python -m pytest -q tests/ui/test_profile_replace.py
3 passed
```

`tests/ui/test_profile_replace.py:53-61` 覆盖 uncovered key 计算；`:64-101` 断言取消后 `changes` 与 `editor.stage_calls` 不变、`profile.write_calls == 0`；`:104-131` 断言确认后 profile 写入一次且 `changes == {"power_min_w": "120"}`。

## 4. F10：文档口径同步

**结论：PASS（文档旧口径零命中）。**

命令与结果：

```text
$ grep -Rno '279\|CONFIRM' docs/architecture.md docs/i18n.md docs/file-tree.md
（无输出，exit 1）

$ grep -c '^msgid' src/vbios_studio/i18n/locale/en/LC_MESSAGES/vbios_studio.po
282
$ grep -c '^msgid' src/vbios_studio/i18n/locale/zh_CN/LC_MESSAGES/vbios_studio.po
282
```

- `docs/architecture.md:57` 已改为 282；`:187` 已改为 `I UNDERSTAND` + 字段 key/`T3`，并附复核 grep。
- `docs/i18n.md:8` 已改为 282，附 `grep -c '^msgid'` 命令。
- `docs/file-tree.md:121,123` 已改为 282，并附复核命令。

**非阻断文档新鲜度观察（§5.1）**：本轮新增 8 条测试后，全量实际为 **213 passed、20 个 UI 测试文件**，但 `README.md:149`、`docs/testing.md:6,19,35,83,90` 仍写 205 passed / 18 个 UI 测试文件。三份文档旧口径已清零，但 README/testing 的计数已被本轮测试增量再次推陈旧；建议发布前同步（不是本轮文档旧口径目标本身）。

**非阻断文档旧表述（§5.2）**：`docs/architecture.md:56` 仍写 app “后续确认票据”（票据已实现）；`docs/file-tree.md:51` 的 `ports/apply.py` 仍列旧的 `device_status/dry_run/execute/restore`，未列 `configure_payload`/`verify`。建议一并清理。

## 5. 非阻断观察汇总

### 5.1 README/testing 计数在本轮测试增量后过期（LOW）

`README.md:149` / `docs/testing.md:6,35,83,90` 为 205 passed，实际 `pytest -q` 为 **213 passed**；`docs/testing.md:19` 为 18 个 UI 测试文件，实际 `ls tests/ui/test_*.py | wc -l` 为 **20**。这是本轮新增测试导致的新鲜度问题，不影响 F10 对 279/CONFIRM 旧口径的关闭；建议发布前更新并保留可复现命令。

### 5.2 文档旧表述（LOW）

- `docs/architecture.md:56` app “后续确认票据与会话状态”：票据已实现，建议改为“确认票据/会话状态”。
- `docs/file-tree.md:51` ApplyPort 方法列表仍为旧签名（`device_status/dry_run/execute/restore`），未列 `configure_payload`/`verify`。
- 这些是文档一致性问题，不影响 F10 的 279/CONFIRM 零命中验收。

### 5.3 注册表键展示略多列（LOW）

`registry_write_keys()` 枚举 `ApplyPreview.values` 的所有非元数据项；`plan_load()` 的 `values` 包含 `VixLoaderPreviousEnableGpuFirmware`（仅在无备份时写入）。确认正文可能把它列为“将写入”，属于展示精度问题，不会漏掉实际写入的 `vbios`/`EnableGpuFirmware`，也不改变票据/T3 门控。若后续要严格“只列实际 steps”，建议在 `ApplyPreview` 增加显式 write/delete 列表。

### 5.4 Restore 确认仍是静态文案（LOW）

`ApplyPanel.request_restore()` 仍使用 `apply.restore_confirm.body` 静态 body，没有像 apply 一样动态列出将要删除/还原的注册表键；risk-model §7.3 建议 unload 显示键值。当前 `restore` 有确认且 `WindowsRegistryAdapter.restore()` 会清票据后调用 unload，安全路径未削弱；建议后续补齐恢复键列表。

## 6. 独立验证

```text
$ .venv/bin/python -m pytest -q
213 passed in 16.84s

$ .venv/bin/lint-imports
domain-pure KEPT
ui-no-adapters KEPT
ports-no-implementations KEPT
layers-app-top KEPT
i18n-standalone KEPT
Contracts: 5 kept, 0 broken.

$ .venv/bin/ruff check src tests
All checks passed!

$ .venv/bin/ruff format --check src tests
144 files already formatted

$ .venv/bin/mypy --strict src/vbios_studio
Success: no issues found in 77 source files

$ python3 tools/prepush_audit.py --strict
files scanned: 218
tracked files: 210
forbidden payloads: 0
large files (> 1,000,000 bytes): 0
secret findings: 0
.gitignore gaps: 0
tracked-but-ignored files: 0
CONCLUSION: PASS
exit 0
```

3 进程并发 GUI selftest：

```bash
for i in 1 2 3; do
  xvfb-run -a .venv/bin/vbios-studio-gui --selftest     --screenshots "/tmp/vbios-selftest/$i" &
done
wait
```

三个进程均 exit 0，均输出 `vbios-studio 0.1.0 selftest: ok (window, a11y, undo/redo, 3 screenshots)`；共 9 张 1270×830 PNG；stdout 仅有 libEGL DRI3 与 at-spi accessibility bus 环境警告，stderr 为空。

目标回归子集：

```text
$ .venv/bin/python -m pytest -q tests/ui/test_profile_t3_gate.py tests/ui/test_apply_panel.py tests/apply/test_windows_registry.py tests/ui/test_confirmation_words.py
29 passed
$ .venv/bin/python -m pytest -q tests/ui/test_apply_confirmation.py tests/ui/test_profile_replace.py
8 passed
```

**未削弱既有 T3 门控/票据测试的证据：**

| 文件 | 与上一轮基线比较 | 结论 |
| --- | --- | --- |
| `tests/ui/test_profile_t3_gate.py` | SHA-256 `45131889…` 未变 | 三态门控/`changes`/`stage_calls` 断言保留 |
| `tests/ui/test_apply_panel.py` | SHA-256 `485cdf1c…` 未变 | 无票据/无 preview 拒绝路径保留 |
| `tests/apply/test_windows_registry.py` | SHA-256 `6831fcc3…` 未变 | 无票据/重放/哈希不匹配零写入测试保留 |
| `tests/ui/test_confirmation_words.py` | SHA-256 `437c7db9…` 未变 | I UNDERSTAND / 字段 key/T3 测试保留 |

## 7. 评审尾校验（内容绑定）

评审结束时（2026-10-23T03:11+08:00）复算 §0 的 37 个文件：

| # | 文件 | 开始时 SHA-256 | 结束时 SHA-256 | 一致 |
| --- | --- | --- | --- | --- |
| 1 | `README.md` | `f2ede61059a96a05c9c3b14a40b8b2c72ae693d8a7a716cadd8a62a4390e8417` | `f2ede61059a96a05c9c3b14a40b8b2c72ae693d8a7a716cadd8a62a4390e8417` | 是 |
| 2 | `pyproject.toml` | `8d5ef77f61ca9914625a81a57c650f5e86ac300542f342b9fd0460b25e61e2d1` | `8d5ef77f61ca9914625a81a57c650f5e86ac300542f342b9fd0460b25e61e2d1` | 是 |
| 3 | `docs/requirements.md` | `2e60a573c60661f37a167d504e45e0553b5318325caa8c332ab94cd13e4b8050` | `2e60a573c60661f37a167d504e45e0553b5318325caa8c332ab94cd13e4b8050` | 是 |
| 4 | `docs/risk-model.md` | `dbf0eb0d884e1a907dcdcfd796a752b7b6aabcf79aa314cddf9062c9b2852468` | `dbf0eb0d884e1a907dcdcfd796a752b7b6aabcf79aa314cddf9062c9b2852468` | 是 |
| 5 | `docs/architecture.md` | `e2e741afe768e1568a263fb9536474633c1e12f770ecbd3254e7ee71393b24e1` | `e2e741afe768e1568a263fb9536474633c1e12f770ecbd3254e7ee71393b24e1` | 是 |
| 6 | `docs/testing.md` | `cd9441f2f2e4b037e7d8fbb117d467a355040de3a41dd822b198d29658ee32e3` | `cd9441f2f2e4b037e7d8fbb117d467a355040de3a41dd822b198d29658ee32e3` | 是 |
| 7 | `docs/file-tree.md` | `0f592055661ca5abcc31b3b8f769c7fea4c763da4b5e040592a0185aa016266c` | `0f592055661ca5abcc31b3b8f769c7fea4c763da4b5e040592a0185aa016266c` | 是 |
| 8 | `docs/i18n.md` | `68f856ecaefd53b76f95b87fc5f64c691366c01e0059567bbb546a217acdbf6c` | `68f856ecaefd53b76f95b87fc5f64c691366c01e0059567bbb546a217acdbf6c` | 是 |
| 9 | `src/vbios_studio/domain/rom.py` | `4226512ca2ce1ea8e83e3c8e0e4da4c9a0a862a4550f44050f80f90c1038b5a1` | `4226512ca2ce1ea8e83e3c8e0e4da4c9a0a862a4550f44050f80f90c1038b5a1` | 是 |
| 10 | `src/vbios_studio/adapters/system/nvflash.py` | `b07c7b446daa2f22c4ee3cfb933401d0639aad049d5660db46b5705bc6310932` | `b07c7b446daa2f22c4ee3cfb933401d0639aad049d5660db46b5705bc6310932` | 是 |
| 11 | `src/vbios_studio/app/container.py` | `d24bc26a3054a2ecdf605d24cb4b834228212b61f3bcca2f728ab2e6c4ef380a` | `d24bc26a3054a2ecdf605d24cb4b834228212b61f3bcca2f728ab2e6c4ef380a` | 是 |
| 12 | `src/vbios_studio/ports/apply.py` | `4c80b357a8068be03e9694eb16130035ec8db803317739a7d9c355108c25b19f` | `4c80b357a8068be03e9694eb16130035ec8db803317739a7d9c355108c25b19f` | 是 |
| 13 | `src/vbios_studio/adapters/system/windows_registry.py` | `465e502753742fe0ded503d8b42b7222b78623beb3e2b4295aa424b76e3c1b0d` | `465e502753742fe0ded503d8b42b7222b78623beb3e2b4295aa424b76e3c1b0d` | 是 |
| 14 | `src/vbios_studio/adapters/system/windows_winreg.py` | `fa9ed4e7d321ddedad49e8a7cd5cffed43050e2e2caf52dbf232c2c1c8cbf3dc` | `fa9ed4e7d321ddedad49e8a7cd5cffed43050e2e2caf52dbf232c2c1c8cbf3dc` | 是 |
| 15 | `src/vbios_studio/adapters/system/windows_verify.py` | `d650da65feb601d63fc6f09e7e7855096140246bfe379083496aab4c74f2791d` | `d650da65feb601d63fc6f09e7e7855096140246bfe379083496aab4c74f2791d` | 是 |
| 16 | `src/vbios_studio/adapters/system/linux_loader.py` | `42c3164b88e48af69ba4421a7b6128cb2411560bb2ea1998aa8e540409257a29` | `42c3164b88e48af69ba4421a7b6128cb2411560bb2ea1998aa8e540409257a29` | 是 |
| 17 | `src/vbios_studio/ui/apply_actions.py` | `f72b6fbab8fc298a90cb7b55f1cd494e5fa3cfcfb835e28fd82ee868a33130e4` | `f72b6fbab8fc298a90cb7b55f1cd494e5fa3cfcfb835e28fd82ee868a33130e4` | 是 |
| 18 | `src/vbios_studio/ui/controller.py` | `7deaa91a2b9253dfb1b3afcf7da840945e4717efb6b2cb4757402a816ea79ab7` | `7deaa91a2b9253dfb1b3afcf7da840945e4717efb6b2cb4757402a816ea79ab7` | 是 |
| 19 | `src/vbios_studio/ui/controller_errors.py` | `61325f6500c99c8eb1afece94e8d9fd9e599ba93157e6411bf697efe986a77d9` | `61325f6500c99c8eb1afece94e8d9fd9e599ba93157e6411bf697efe986a77d9` | 是 |
| 20 | `src/vbios_studio/ui/profile_controller.py` | `3eac00526869e58f641e3e6d73ffc6917cc7990cc15e6258317e3da030386a33` | `3eac00526869e58f641e3e6d73ffc6917cc7990cc15e6258317e3da030386a33` | 是 |
| 21 | `src/vbios_studio/ui/profile_flow.py` | `2033bc541567a46728bde78f1f0d5ad12a87d58ee6aa5781d4d81c16e2c9eb65` | `2033bc541567a46728bde78f1f0d5ad12a87d58ee6aa5781d4d81c16e2c9eb65` | 是 |
| 22 | `src/vbios_studio/ui/theme.py` | `ca299998bcd6a449f7096da48092ca9445f96b1e9309b939d28fd81ccb3d14cd` | `ca299998bcd6a449f7096da48092ca9445f96b1e9309b939d28fd81ccb3d14cd` | 是 |
| 23 | `src/vbios_studio/ui/components/apply_panel.py` | `8b3f084d6bc26028d9d72755da6e00ef4a3956b47120e2d71218f86e7926d0c7` | `8b3f084d6bc26028d9d72755da6e00ef4a3956b47120e2d71218f86e7926d0c7` | 是 |
| 24 | `src/vbios_studio/ui/components/settings.py` | `2025fedba3155c11b450a678dd747b6c96e73e3195cebbd4b75168f80e606de9` | `2025fedba3155c11b450a678dd747b6c96e73e3195cebbd4b75168f80e606de9` | 是 |
| 25 | `src/vbios_studio/ui/main_window.py` | `7e977fdfa299e532d7434600610f299fe8f0010ec5d48d7bb5b4879822ee7fbb` | `7e977fdfa299e532d7434600610f299fe8f0010ec5d48d7bb5b4879822ee7fbb` | 是 |
| 26 | `src/vbios_studio/ui/window_dialogs.py` | `99b1a3641819753590429bb002ed54dedbb9bc903a56591bb32cfa44e1af78f5` | `99b1a3641819753590429bb002ed54dedbb9bc903a56591bb32cfa44e1af78f5` | 是 |
| 27 | `src/vbios_studio/ui/dialogs/confirm_dialog.py` | `f3ac7f811489237fb8d5afda674ace3e00d2ba8bfe7a26ded387e034824ebdff` | `f3ac7f811489237fb8d5afda674ace3e00d2ba8bfe7a26ded387e034824ebdff` | 是 |
| 28 | `src/vbios_studio/i18n/locale/en/LC_MESSAGES/vbios_studio.po` | `34653667efc7529cb734f27bf4e4e0d3bdc23d73d127fb88e730758942dccf2f` | `34653667efc7529cb734f27bf4e4e0d3bdc23d73d127fb88e730758942dccf2f` | 是 |
| 29 | `src/vbios_studio/i18n/locale/zh_CN/LC_MESSAGES/vbios_studio.po` | `83393ebd367cf0f28ae2a9758249d95c4b8ad014088cf1f52e770753b6022c8f` | `83393ebd367cf0f28ae2a9758249d95c4b8ad014088cf1f52e770753b6022c8f` | 是 |
| 30 | `tests/integration/test_real_controller.py` | `75bf0ecf77b94c0169c53dffdb002fecbbfc8574b864aa8a0f3941a27fd99950` | `75bf0ecf77b94c0169c53dffdb002fecbbfc8574b864aa8a0f3941a27fd99950` | 是 |
| 31 | `tests/apply/test_windows_registry.py` | `6831fcc3673272ad0c9910613fca58fe5ff2fff82dd930e859b176b20c062261` | `6831fcc3673272ad0c9910613fca58fe5ff2fff82dd930e859b176b20c062261` | 是 |
| 32 | `tests/apply/test_linux_loader.py` | `8e85fe0f5cddff479f4de994d047d770d88dfe340166b3c2dac67ba2eb82bc13` | `8e85fe0f5cddff479f4de994d047d770d88dfe340166b3c2dac67ba2eb82bc13` | 是 |
| 33 | `tests/ui/test_profile_t3_gate.py` | `45131889bef09faee42f121b2bc35a3e4befab38051e371ac11807e27ac64b5a` | `45131889bef09faee42f121b2bc35a3e4befab38051e371ac11807e27ac64b5a` | 是 |
| 34 | `tests/ui/test_apply_panel.py` | `485cdf1c4f1d513074380c7718085d0b2c3aa74d10d58a094cb57b9abb9f1115` | `485cdf1c4f1d513074380c7718085d0b2c3aa74d10d58a094cb57b9abb9f1115` | 是 |
| 35 | `tests/ui/test_confirmation_words.py` | `437c7db95aa120ac3eadbcddb18258949def065fc581621874f260b60509cd7c` | `437c7db95aa120ac3eadbcddb18258949def065fc581621874f260b60509cd7c` | 是 |
| 36 | `tests/ui/test_apply_confirmation.py` | `9bf7592701226c6cac5b1cab1fa18e065e2567de4b68b3c9c876ee4a87b85846` | `9bf7592701226c6cac5b1cab1fa18e065e2567de4b68b3c9c876ee4a87b85846` | 是 |
| 37 | `tests/ui/test_profile_replace.py` | `34ad9ef7fe9e8660e7974fd91d251fe3c23982217ef4c72a4d287f5650a148f3` | `34ad9ef7fe9e8660e7974fd91d251fe3c23982217ef4c72a4d287f5650a148f3` | 是 |

**37/37 一致，评审期间没有任何基线文件被改动。** 本报告 PASS 绑定上述哈希集合；旧 `docs/review-report.md` 的 33 文件绑定不覆盖本轮变更，发布审计应引用本报告。

## 8. 结论

**判定：PASS（软件层）。**

- F8：PASS——T3 批次横幅与最终应用确认正文动态列出 T3 字段与注册表键（§2）。
- F9：PASS——profile 未覆盖已有 staged changes 时先提示，取消不调用 controller（§3）。
- F10：PASS——architecture/i18n/file-tree 的 279/CONFIRM 旧口径 grep 命中 0，282 msgid 与确认词已同步（§4）。
- 全量 `pytest` **213 passed**、`lint-imports` **5/5**；既有 T3 门控/票据测试哈希未变且目标子集全绿（§6）。
- 非阻断观察：README/testing 的 205/18 计数已因本轮新增测试变为 213/20（§5.1）；architecture:56/file-tree:51 旧表述（§5.2）；registry_write_keys 多列潜在不写键（§5.3）；restore 确认仍静态（§5.4）。建议发布前清理，但不影响本轮 F8/F9/F10 核心关闭与 PASS 判定。

**本次 PASS 绑定的哈希集合：§0/§7 的 37 个文件 SHA-256（37/37 复算一致）。**
