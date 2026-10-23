# VBIOS Studio 发布前终审报告

> ⚠️ 历史记录：本报告反映当时状态，可能包含已被修复的问题。
> 当前状态见 [评审与审计索引](README.md)。

> 评审日期：2026-10-23 · 评审范围：**仅 F11/F12/F13/F14** · 结论：**NEEDS_REVISION（暂不可发布）**

## 0. 冻结规则（本轮预先声明）

本轮只核对 F11/F12（文档计数与两处旧表述）与 F13/F14（注册表键集合一致、restore 动态列出）；其余历史观察不重新展开。

- **新发现的非阻断问题**：只登记到 §6「v0.1.1 backlog」，不阻断 v0.1.0 发布。
- **允许判 `needs_revision` 的唯一例外**：安全门控失效，或冻结契约条文违规。本报告 §4/§5 的两项均属于 `docs/risk-model.md` §7.3 冻结条文的直接违反，因此不是 backlog 项。
- 本轮不因为风格、命名、注释或非阻断易用性问题阻断发布。

## 1. 评审结论

**NEEDS_REVISION。** F11、F12 已关闭；F13、F14 未关闭，且分别涉及“确认框列出的注册表写集合不完整”和“restore 在正常入口下不显示将恢复/删除的键值”，属于 `risk-model §7.3` 冻结写操作契约违规。修复前不生成可发布哈希集合，发布审计不得以本报告作为发布依据。

## 2. 内容绑定基线

**本轮评审针对以下 38 个文件；结束时逐项复算，任一变化即判 `needs_revision`。** 评审期间不修改任何基线文件；只写本报告。

| # | 文件 | 字节数 | SHA-256 |
| --- | --- | ---: | --- |
| 1 | `README.md` | 13,898 | `556fc361a99b61264de1ed8e4daa12740024e1a32a4dade80a0fbba2f7fa4b43` |
| 2 | `pyproject.toml` | 3,539 | `8d5ef77f61ca9914625a81a57c650f5e86ac300542f342b9fd0460b25e61e2d1` |
| 3 | `docs/requirements.md` | 38,009 | `2e60a573c60661f37a167d504e45e0553b5318325caa8c332ab94cd13e4b8050` |
| 4 | `docs/risk-model.md` | 29,564 | `dbf0eb0d884e1a907dcdcfd796a752b7b6aabcf79aa314cddf9062c9b2852468` |
| 5 | `docs/architecture.md` | 15,306 | `38f5bc86224de0cce8cdd19db59929d753cf77ae58d4cfd2b2f2968fb3f7434d` |
| 6 | `docs/testing.md` | 8,655 | `98815c4d4d1c5ef039a35ed059d8837f2aee7929b53c95a227e3a2863f91d7b7` |
| 7 | `docs/file-tree.md` | 14,221 | `7b139a0e5cfc9105302278347a2e726a460adba2e89ae92e137136d03a293d02` |
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
| 23 | `src/vbios_studio/ui/components/apply_panel.py` | 16,225 | `4682d7ccb97dbf31405c509a3b68cbc38d847babcf562672c6b8d05325667de9` |
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
| 36 | `tests/ui/test_apply_confirmation.py` | 6,111 | `c3c792f2163653b065ec48efda842a758bcfb7b2f231aa528d3b40131526defa` |
| 37 | `tests/ui/test_profile_replace.py` | 4,556 | `34ad9ef7fe9e8660e7974fd91d251fe3c23982217ef4c72a4d287f5650a148f3` |
| 38 | `tests/meta/test_doc_counts.py` | 2,892 | `1182fc20ce646aec82206ee2a9683832e77ad9ce3b2c219017a3a080ef33a415` |

基线登记：2026-10-23T03:29+08:00；结束复算见 §7。

## 3. F11/F12：文档计数与旧表述

### F11 文档计数：PASS

实测：

```text
$ .venv/bin/python -m pytest -q
217 passed in 18.01s

$ ls tests/ui/test_*.py | wc -l
20
```

声明值已同步：

- `README.md:149`：`pytest -q | tail -1` → **217 passed**；`ls tests/ui/test_*.py | wc -l` → **20**。
- `docs/testing.md:6,35,83,90`：**217 passed**；`:19`：**20 个测试文件**；`:23`：tests/meta **4 个测试文件**。
- `tests/meta/test_doc_counts.py:1-93`：读取 README 的两个声明值，与 `pytest --collect-only -q` 的实际收集值和 `tests/ui/test_*.py` 实际文件数比较；内含 tmp README 999/999 反例，篡改后必须失败。
- `tests/meta/test_doc_counts.py` 1 passed；`tests/contract/test_docs_tree.py` 9 passed。

结论：F11 **PASS**。计数与可复现命令一致，且有元测试防止再次漂移。

### F12 两处旧表述：PASS

```text
$ grep -RnoE '\b279\b|\bCONFIRM\b' docs/architecture.md docs/i18n.md docs/file-tree.md
（无输出，exit 1）

$ grep -Rno '后续确认票据' docs/architecture.md
（无输出，exit 1）
```

- `docs/architecture.md:56`：app 职责已改为“构造平台适配器并注入四 Port；`--version`/`--selftest`/`--gui` 入口；GUI 入口 `app/gui.py` 注入 `build_gui_controller()`”，不再写“后续确认票据”。
- `docs/architecture.md:137-147` §5.4 已包含 `ApplyPort.configure_payload()`、`device_status()`、`dry_run()`、`execute()`、`verify()`、`restore()`。
- `docs/file-tree.md:51`：ApplyPort 已列 `configure_payload/device_status/dry_run/execute/restore/verify`。
- `docs/file-tree.md` 的 tests 段已按目录描述职责与覆盖类别，不再逐文件枚举，避免每加测试文件即过期。

结论：F12 **PASS**。

## 4. F13：注册表键集合一致 — FAIL

**验收原文要求：确认对话框列出的注册表键与实际写入集合完全一致。当前实现对“无备份的首次 load”会漏列一个实际写入键。**

代码证据：

- `src/vbios_studio/adapters/system/windows_plan.py:193-194`：`if backup is None: steps.append(Step("set", PREVIOUS_VALUE_NAME, ...))`。首次 load（无备份）实际会写 `VixLoaderPreviousEnableGpuFirmware`。
- `src/vbios_studio/adapters/system/windows_plan.py:202-213`：`values` 同时包含 `VixLoaderPreviousEnableGpuFirmware` 与 `delete`，但不包含“实际 steps 的 write 集合”。
- `src/vbios_studio/ui/components/apply_panel.py:27`：`_ALWAYS_WRITTEN_NAMES = frozenset({"vbios", "EnableGpuFirmware"})`。
- `src/vbios_studio/ui/components/apply_panel.py:51-66`：`registry_write_keys()` 只遍历 `_ALWAYS_WRITTEN_NAMES`，因此无条件跳过 `VixLoaderPreviousEnableGpuFirmware`。

实际对照命令（使用仓库 `tests/apply/fakes.py` 的 `FakePlatform`，无备份的首个 load）：

```text
$ PYTHONPATH=src:tests/apply .venv/bin/python - <<'EOF'
from fakes import FakePlatform, FakeRunner
from vbios_studio.adapters.system.windows_registry import WindowsRegistryAdapter
from vbios_studio.ui.components.apply_panel import registry_write_keys
p = FakePlatform()
a = WindowsRegistryAdapter(platform=p, runner=FakeRunner())
a.configure_payload(b"PAYLOAD")
preview = a.dry_run()
listed = set(registry_write_keys(preview))
res = a.execute()
actual = {name for op, name in p.key.mutations}
print("listed:", sorted(listed))
print("actual writes:", sorted(actual))
EOF
listed: ['HKLM\\...\\0000\\EnableGpuFirmware', 'HKLM\\...\\0000\\vbios']
actual writes: ['EnableGpuFirmware', 'VixLoaderPreviousEnableGpuFirmware', 'vbios']
execute ok: True
```

确认框会漏掉 `VixLoaderPreviousEnableGpuFirmware`，不满足“列出什么 == 实际写什么”。

测试证据为何未捕获：`tests/ui/test_apply_confirmation.py:117-141` 名为 `test_registry_write_keys_match_backend_write_set_exactly`，但 `fake_backend_writes` 是手工构造的集合（`vbios`/`EnableGpuFirmware`/`romOverride00`），没有实例化 `FakePlatform`，也没有覆盖 `backup is None` 的首次 load 路径；`tests/ui/test_apply_confirmation.py:91-114` 同样用手工 `ApplyPreview` 断言“不包含 Vix”，因此漏列被当成预期行为。

**结论：F13 FAIL（契约违规）。**

## 5. F14：restore 动态列出恢复/删除键 — FAIL

**验收原文要求：restore 确认正文动态列出将被恢复/删除的键与值来源；取消则不调用 restore。当前实现只在 `last_preview` 存在时动态追加；正常入口下 `last_preview` 为 `None`。**

代码证据：

- `src/vbios_studio/ui/components/apply_panel.py:189-192`：`refresh()` 每次进入应用面板都会 `self.last_preview = None`。
- `src/vbios_studio/ui/components/apply_panel.py:326-328`：`request_execute()` 的 `finally` 再次清空 `last_preview`。
- `src/vbios_studio/ui/components/apply_panel.py:350-354`：`request_restore()` 仅调用 `restore_key_lines(self.last_preview)`；`restore_key_lines(None)` 在 `:76-78` 返回空元组，正文保持静态 `apply.restore_confirm.body`。
- 因此：用户在应用面板直接点 Restore（未先 dry-run），或成功 Apply 后再点 Restore，确认正文均没有恢复/删除键。`risk-model §7.3` 明确要求 unload “仍显示将删除/还原的键值”。

实际入口命令（xvfb，构造 `ApplyPanel` 后直接 `refresh()`，再 `request_restore()`，不手工注入 `last_preview`）：

```text
last_preview after refresh: None
restore body has target key? False
restore_key_lines(None): ()
```

测试证据为何未捕获：`tests/ui/test_apply_confirmation.py:144-180` 在 `:154` 手工设置 `panel.last_preview = ApplyPreview(...)`，绕过了 `refresh()`/成功 Apply 后 `last_preview=None` 的生产路径；测试只验证了“有人预先塞入 preview”这一条非生产路径。

**结论：F14 FAIL（契约违规；恢复写操作的确认正文缺键值）。**

## 6. v0.1.1 backlog（非阻断）

按冻结规则，以下新观察只登记为 v0.1.1 待办，不参与本轮 `needs_revision` 判定；本轮的两个失败项（§4/§5）不在此列。

1. **LOW：文档计数的元测试只解析 README**。`tests/meta/test_doc_counts.py` 检查 `README.md` 的 pytest/UI 计数，但未解析 `docs/testing.md`；后者仍靠人工同步。建议 v0.1.1 扩展为同时校验两份文档，或让 docs/testing 从 README 单一来源生成。
2. **LOW：restore 键行的删除项显示可更精确**。`restore_key_lines()` 目前无条件列出 `VixLoaderPreviousEnableGpuFirmware (delete)`；当备份标记本来不存在时，unload 实际不会删除该值。该问题与 §5 的 F14 修复一并处理，不属于新的发布阻断项。
3. **LOW：`file-tree` 的 tests 目录改为目录级描述后，具体覆盖类别仍可能与实际测试文件轻微漂移**；当前以 `docs/testing.md` 的测试矩阵为主要来源，建议后续保持两者人工对账。

## 7. 独立验证

```text
$ .venv/bin/python -m pytest -q
217 passed in 18.01s

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
147 files already formatted

$ .venv/bin/mypy --strict src/vbios_studio
Success: no issues found in 77 source files

$ python3 tools/prepush_audit.py --strict
CONCLUSION: PASS
exit 0
```

`prepush_audit` 的完整尾部：forbidden payloads 0、large files 0、secret findings 0、.gitignore gaps 0、tracked-but-ignored 0。

## 8. 内容绑定尾校验（38/38）

| # | 文件 | 开始时 SHA-256 | 结束时 SHA-256 | 一致 |
| --- | --- | --- | --- | --- |
| 1 | `README.md` | `556fc361a99b61264de1ed8e4daa12740024e1a32a4dade80a0fbba2f7fa4b43` | `556fc361a99b61264de1ed8e4daa12740024e1a32a4dade80a0fbba2f7fa4b43` | 是 |
| 2 | `pyproject.toml` | `8d5ef77f61ca9914625a81a57c650f5e86ac300542f342b9fd0460b25e61e2d1` | `8d5ef77f61ca9914625a81a57c650f5e86ac300542f342b9fd0460b25e61e2d1` | 是 |
| 3 | `docs/requirements.md` | `2e60a573c60661f37a167d504e45e0553b5318325caa8c332ab94cd13e4b8050` | `2e60a573c60661f37a167d504e45e0553b5318325caa8c332ab94cd13e4b8050` | 是 |
| 4 | `docs/risk-model.md` | `dbf0eb0d884e1a907dcdcfd796a752b7b6aabcf79aa314cddf9062c9b2852468` | `dbf0eb0d884e1a907dcdcfd796a752b7b6aabcf79aa314cddf9062c9b2852468` | 是 |
| 5 | `docs/architecture.md` | `38f5bc86224de0cce8cdd19db59929d753cf77ae58d4cfd2b2f2968fb3f7434d` | `38f5bc86224de0cce8cdd19db59929d753cf77ae58d4cfd2b2f2968fb3f7434d` | 是 |
| 6 | `docs/testing.md` | `98815c4d4d1c5ef039a35ed059d8837f2aee7929b53c95a227e3a2863f91d7b7` | `98815c4d4d1c5ef039a35ed059d8837f2aee7929b53c95a227e3a2863f91d7b7` | 是 |
| 7 | `docs/file-tree.md` | `7b139a0e5cfc9105302278347a2e726a460adba2e89ae92e137136d03a293d02` | `7b139a0e5cfc9105302278347a2e726a460adba2e89ae92e137136d03a293d02` | 是 |
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
| 23 | `src/vbios_studio/ui/components/apply_panel.py` | `4682d7ccb97dbf31405c509a3b68cbc38d847babcf562672c6b8d05325667de9` | `4682d7ccb97dbf31405c509a3b68cbc38d847babcf562672c6b8d05325667de9` | 是 |
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
| 36 | `tests/ui/test_apply_confirmation.py` | `c3c792f2163653b065ec48efda842a758bcfb7b2f231aa528d3b40131526defa` | `c3c792f2163653b065ec48efda842a758bcfb7b2f231aa528d3b40131526defa` | 是 |
| 37 | `tests/ui/test_profile_replace.py` | `34ad9ef7fe9e8660e7974fd91d251fe3c23982217ef4c72a4d287f5650a148f3` | `34ad9ef7fe9e8660e7974fd91d251fe3c23982217ef4c72a4d287f5650a148f3` | 是 |
| 38 | `tests/meta/test_doc_counts.py` | `1182fc20ce646aec82206ee2a9683832e77ad9ce3b2c219017a3a080ef33a415` | `1182fc20ce646aec82206ee2a9683832e77ad9ce3b2c219017a3a080ef33a415` | 是 |

**38/38 一致。** 评审期间未改动任何基线文件；本报告之外的改动只允许来自修复任务，并必须重新走一次终审与重新绑定。

## 9. 发布哈希结论

**当前没有可发布的哈希集合。** 本报告判定 `NEEDS_REVISION`：F13（`registry_write_keys` 漏列无备份首次 load 的 `VixLoaderPreviousEnableGpuFirmware`）与 F14（`request_restore` 在正常 `last_preview=None` 入口不显示恢复/删除键）均违反 `risk-model §7.3`。修复后必须以新的 38 文件（或更新后的文件集）重新绑定并重跑全量/静态/卫生检查；本报告的 38 文件哈希只能作为本轮评审基线，不能交给发布审计使用。

## 10. 复现命令汇总

```bash
cd vbios-studio
source .venv/bin/activate
python -m pytest -q
.venv/bin/lint-imports
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
.venv/bin/mypy --strict src/vbios_studio
python3 tools/prepush_audit.py --strict
test -f docs/reviews/review-final-report.md
```
