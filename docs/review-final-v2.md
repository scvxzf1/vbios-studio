# VBIOS Studio 发布前终审报告 v2

> 评审日期：2026-10-23 · 范围：**仅 F13/F14** · 结论：**PASS（软件层）**
>
> 本报告取代 `docs/review-final-report.md`：上一轮 F13/F14 的 root-cause 问题已由 ApplyPort 操作清单与实时确认正文修复；本报告重新绑定发布哈希。F11/F12 已在上一轮关闭，本轮不重新展开。

## 0. 评审规则

本轮只核对 F13（确认框列出的注册表键集合 == 实际写入集合）与 F14（restore 动态列出恢复/删除键）。F11/F12 已关闭，不重新展开。

- 新发现的非阻断问题只进入 §6「v0.1.1 backlog」，不阻断发布。
- 只有安全门控失效或 `risk-model` 冻结契约条文违规才允许判 `needs_revision`；本轮未发现此类问题。

## 1. 结论

**PASS（软件层）。** F13/F14 均通过生产路径（真实 `ApplyPanel` + `FakePlatform`/`WindowsRegistryAdapter`）验证，UI 不再存在硬编码注册表键名单，确认操作清单与实际写入来自同一份 `RegistryPlan.steps`。42 个绑定文件在评审结束时复算 **42/42 一致**。

本报告 §7 的 42 文件 SHA-256 集合即为**可发布哈希集合**；发布审计应以本报告为唯一依据，不使用上一轮 `docs/review-final-report.md` 的 needs_revision 结论。

## 2. 内容绑定基线

**本轮评审针对以下 42 个文件；评审结束逐项复算，任一变化即判 `needs_revision`。**

| # | 文件 | 字节数 | SHA-256 |
| --- | --- | ---: | --- |
| 1 | `README.md` | 13,898 | `af7d21e5617d0d906b2cc62818eaa7cae8d7651eabdc890b36922aaed8b6e360` |
| 2 | `pyproject.toml` | 3,539 | `8d5ef77f61ca9914625a81a57c650f5e86ac300542f342b9fd0460b25e61e2d1` |
| 3 | `docs/requirements.md` | 38,304 | `61d7e7d16f1e04075d60b0181bc3a65437119665e68753dc78d9e2fc219ab6a6` |
| 4 | `docs/risk-model.md` | 29,564 | `dbf0eb0d884e1a907dcdcfd796a752b7b6aabcf79aa314cddf9062c9b2852468` |
| 5 | `docs/architecture.md` | 15,630 | `6110770627ad03a85db9c7005f2074e58c8b11aab172dfbff6949d7df95fe786` |
| 6 | `docs/testing.md` | 8,724 | `7f1b7dc139c20907b2f50d2ca6f3a8d0f1a5b8ba99349fe72f09b7af5c3485f1` |
| 7 | `docs/file-tree.md` | 14,221 | `7b139a0e5cfc9105302278347a2e726a460adba2e89ae92e137136d03a293d02` |
| 8 | `docs/i18n.md` | 5,173 | `68f856ecaefd53b76f95b87fc5f64c691366c01e0059567bbb546a217acdbf6c` |
| 9 | `docs-assets/screenshots/02-fields-risk.png` | 207,749 | `c15b1bc73e72e3bbe3dd71e8e70a5883f6c09a4f09cd970afe0246422680cb42` |
| 10 | `src/vbios_studio/domain/rom.py` | 11,948 | `4226512ca2ce1ea8e83e3c8e0e4da4c9a0a862a4550f44050f80f90c1038b5a1` |
| 11 | `src/vbios_studio/adapters/system/nvflash.py` | 13,226 | `b07c7b446daa2f22c4ee3cfb933401d0639aad049d5660db46b5705bc6310932` |
| 12 | `src/vbios_studio/app/container.py` | 3,179 | `d24bc26a3054a2ecdf605d24cb4b834228212b61f3bcca2f728ab2e6c4ef380a` |
| 13 | `src/vbios_studio/ports/apply.py` | 2,189 | `3f00973ee4e86075b964cbf4debda4efd55a26e27d15850093a7f69f67309678` |
| 14 | `src/vbios_studio/adapters/system/windows_plan.py` | 13,335 | `b472520a8a0b8f7ac02feb49efad9f5e5f8b971e4e53ea66a78527244dbddda3` |
| 15 | `src/vbios_studio/adapters/system/windows_registry.py` | 14,805 | `620b825b189e35f230e167df51ca449db04ea4b28378a834fa53f1cb1c756bf8` |
| 16 | `src/vbios_studio/adapters/system/windows_winreg.py` | 5,972 | `fa9ed4e7d321ddedad49e8a7cd5cffed43050e2e2caf52dbf232c2c1c8cbf3dc` |
| 17 | `src/vbios_studio/adapters/system/windows_verify.py` | 3,361 | `7889e512582e42349adfddd3c9464dd423a99690888c36f542c5e818fd9d30d5` |
| 18 | `src/vbios_studio/adapters/system/linux_loader.py` | 7,785 | `be0154e64d1315ed24cd81e840f3ce199a6e6dce6cc3962cfad6e11627a170b1` |
| 19 | `src/vbios_studio/ui/apply_actions.py` | 4,176 | `4cc212d1ca45cbe140306eb4dcfdd2135969e3b2348c4216eaf972603a58402b` |
| 20 | `src/vbios_studio/ui/controller.py` | 10,586 | `7deaa91a2b9253dfb1b3afcf7da840945e4717efb6b2cb4757402a816ea79ab7` |
| 21 | `src/vbios_studio/ui/controller_errors.py` | 968 | `61325f6500c99c8eb1afece94e8d9fd9e599ba93157e6411bf697efe986a77d9` |
| 22 | `src/vbios_studio/ui/profile_controller.py` | 3,811 | `3eac00526869e58f641e3e6d73ffc6917cc7990cc15e6258317e3da030386a33` |
| 23 | `src/vbios_studio/ui/profile_flow.py` | 6,624 | `2033bc541567a46728bde78f1f0d5ad12a87d58ee6aa5781d4d81c16e2c9eb65` |
| 24 | `src/vbios_studio/ui/theme.py` | 5,847 | `ca299998bcd6a449f7096da48092ca9445f96b1e9309b939d28fd81ccb3d14cd` |
| 25 | `src/vbios_studio/ui/components/apply_panel.py` | 14,625 | `a6f0db8d5bfa3c28dd47c8ed2a9705226a5d3f90cb58131b1a163ea4daf3ce30` |
| 26 | `src/vbios_studio/ui/components/settings.py` | 1,253 | `2025fedba3155c11b450a678dd747b6c96e73e3195cebbd4b75168f80e606de9` |
| 27 | `src/vbios_studio/ui/main_window.py` | 14,322 | `7e977fdfa299e532d7434600610f299fe8f0010ec5d48d7bb5b4879822ee7fbb` |
| 28 | `src/vbios_studio/ui/window_dialogs.py` | 5,370 | `99b1a3641819753590429bb002ed54dedbb9bc903a56591bb32cfa44e1af78f5` |
| 29 | `src/vbios_studio/ui/dialogs/confirm_dialog.py` | 5,147 | `f3ac7f811489237fb8d5afda674ace3e00d2ba8bfe7a26ded387e034824ebdff` |
| 30 | `src/vbios_studio/i18n/locale/en/LC_MESSAGES/vbios_studio.po` | 19,304 | `34653667efc7529cb734f27bf4e4e0d3bdc23d73d127fb88e730758942dccf2f` |
| 31 | `src/vbios_studio/i18n/locale/zh_CN/LC_MESSAGES/vbios_studio.po` | 19,020 | `83393ebd367cf0f28ae2a9758249d95c4b8ad014088cf1f52e770753b6022c8f` |
| 32 | `tests/apply/fakes.py` | 4,035 | `ae0b0467998c672691dc7f20e62fb0b6e3367fb99c2c6167eb304ff22f900196` |
| 33 | `tests/apply/test_apply_operations.py` | 5,162 | `09e9c3af1e90cfb37f1dc5143089beed4de0b1fa170471849fa4fc78a652c49a` |
| 34 | `tests/apply/test_windows_registry.py` | 8,540 | `6831fcc3673272ad0c9910613fca58fe5ff2fff82dd930e859b176b20c062261` |
| 35 | `tests/apply/test_linux_loader.py` | 3,446 | `8e85fe0f5cddff479f4de994d047d770d88dfe340166b3c2dac67ba2eb82bc13` |
| 36 | `tests/integration/test_real_controller.py` | 3,602 | `75bf0ecf77b94c0169c53dffdb002fecbbfc8574b864aa8a0f3941a27fd99950` |
| 37 | `tests/ui/test_apply_panel.py` | 5,656 | `de34e7890e047ce92b127cbaf108d9068986657096b358ccce1ff5195eabceb9` |
| 38 | `tests/ui/test_apply_confirmation.py` | 6,116 | `1e8b1489b5f1a557595401b40e066079a65c9dda4f095ba38da8c5e706aaa7fb` |
| 39 | `tests/ui/test_profile_t3_gate.py` | 3,641 | `45131889bef09faee42f121b2bc35a3e4befab38051e371ac11807e27ac64b5a` |
| 40 | `tests/ui/test_confirmation_words.py` | 1,468 | `437c7db95aa120ac3eadbcddb18258949def065fc581621874f260b60509cd7c` |
| 41 | `tests/ui/test_profile_replace.py` | 4,556 | `34ad9ef7fe9e8660e7974fd91d251fe3c23982217ef4c72a4d287f5650a148f3` |
| 42 | `tests/meta/test_doc_counts.py` | 2,892 | `1182fc20ce646aec82206ee2a9683832e77ad9ce3b2c219017a3a080ef33a415` |

基线登记：2026-10-23T03:47+08:00；尾校验见 §7。

## 3. F13：注册表键集合一致 — PASS

### 3.1 同一份 plan 生成操作清单与实际写入

- `src/vbios_studio/ports/apply.py:46`：`ApplyPort.describe_operations(action)` 是只读操作清单接口。
- `src/vbios_studio/adapters/system/windows_plan.py:327-329`：`operations_for(plan)` 把 `RegistryPlan.steps` 原样映射为 `Operation(op, name, source)`。
- `src/vbios_studio/adapters/system/windows_plan.py:344-375`：`describe_operations()` 的 `load` 分支调用 `plan_load()`，`restore/unload` 分支调用 `plan_unload()`；未知 action 关闭失败。
- `src/vbios_studio/adapters/system/windows_registry.py:115-136`：Windows adapter 的 `describe_operations()` 调用同一 `windows_plan.describe_operations()`。
- 实际写入路径同一 plan：`windows_registry.py:234` 的 `load()` 使用 `plan_load()`，`:305` 的 `unload()` 使用 `plan_unload()`，`:249-253`/`:319-324` 执行 `plan.steps` 的 set/delete；不存在第二套写入规则。
- `src/vbios_studio/ui/components/apply_panel.py:42-44`：`operation_lines()` 只做展示渲染；`:197` dry-run、`:287` execute、`:311` restore 都实时调用 `controller.describe_apply_operations(...)`。

### 3.2 UI 层硬编码键名单已删除

```text
$ grep -R --include='*.py' -n '_ALWAYS_WRITTEN_NAMES\|registry_write_keys\|restore_key_lines' src tests
（无输出）
```

`apply_panel.py` 不再含 `VixLoaderPreviousEnableGpuFirmware`、`vbios`、`EnableGpuFirmware` 的硬编码集合；确认正文按 `Operation` 的 `op/name/source` 生成。

### 3.3 生产路径证据：backup=None

`tests/ui/test_apply_confirmation.py:103-124` 使用真实 `ApplyPanel`、`FakePlatform`、`WindowsRegistryAdapter`，不手工构造 preview：

```text
$ .venv/bin/python -m pytest -q tests/ui/test_apply_confirmation.py -k 'backup_none or existing_backup or restore_confirmation' -vv
5 passed, 3 deselected
```

断言内容：
- `expected = adapter.describe_operations("load")` 恰好包含 3 个名字：`VixLoaderPreviousEnableGpuFirmware`、`vbios`、`EnableGpuFirmware`。
- `panel.dry_run()` 后 `panel.request_execute()` 执行确认；`actual == {(operation.op, operation.name)}` 与实际 `FakePlatform.key.mutations` 完全相等。
- 确认正文 `bodies[-1]` 包含全部 3 个操作名字。
- `tests/ui/test_apply_confirmation.py:126-142` 覆盖已有 backup：操作清单不含 `VixLoaderPreviousEnableGpuFirmware`，实际 mutations 同样不含。

`tests/apply/test_apply_operations.py` 独立覆盖 `backup=None`、backup 存在、有 override、无 override 四态：

```text
$ .venv/bin/python -m pytest -q tests/apply/test_apply_operations.py
7 passed in 0.05s
```

`tests/apply/test_apply_operations.py:41-54` 断言首次 load 的 `previous` set 存在且 `(op, name)` 与 `FakePlatform.mutations` 完全相等；`:56-68` 断言已有 backup 时不含 `VixLoaderPreviousEnableGpuFirmware`；`:88-96`/`:98-116` 断言 restore 的操作清单与实际 mutations 相等。

**F13 结论：PASS。**

## 4. F14：restore 动态列出恢复/删除键 — PASS

### 4.1 restore 不再依赖 last_preview

`src/vbios_studio/ui/components/apply_panel.py:300-319` 的 `request_restore()`：

- `:311` 调用 `self.controller.describe_apply_operations("restore")`；
- `:315-318` 把返回的每个 `Operation` 渲染进确认正文；
- 不读取 `last_preview`，因此不依赖 dry-run 状态，也不受 `request_execute()` 清空 preview 的影响。

`last_preview` 仍只用于 execute 前的 dry-run 门控（`:270`）；restore 使用 live 的 `plan_unload()` 结果（`windows_plan.py:344-360`、`windows_registry.py:206-212`、`:305-313`）。

### 4.2 三种入口 + 取消零调用

`tests/ui/test_apply_confirmation.py:145-180` 用真实 `ApplyPanel` + `FakePlatform` 参数化覆盖：

- `direct`：`refresh()` 后直接 Restore；
- `after_apply`：先 `dry_run()` + `request_execute()` 成功 Apply，再 Restore（此时 `last_preview=None`）；
- `after_refresh`：再次 `refresh()` 后 Restore；
- 每个入口断言确认正文包含 `describe_operations("restore")` 的全部 `name`；
- 取消确认后 `platform.key.mutations` 不变，`adapter.restore_calls == 0`。

测试结果：

```text
$ .venv/bin/python -m pytest -q tests/ui/test_apply_confirmation.py -k restore_confirmation
3 passed
```

`tests/ui/test_apply_confirmation.py:146-180` 的 `CountingAdapter.restore()` 只在确认回调真正执行时递增；取消分支调用 0 次。

**F14 结论：PASS。**

## 5. 独立验证

```text
$ source .venv/bin/activate && python -m pytest -q
224 passed in 19.68s

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
148 files already formatted

$ .venv/bin/mypy --strict src/vbios_studio
Success: no issues found in 77 source files

$ python3 tools/prepush_audit.py --strict
forbidden payloads: 0
large files (> 1,000,000 bytes): 0
secret findings: 0
.gitignore gaps: 0
tracked-but-ignored files: 0
CONCLUSION: PASS
```

`tests/contract/test_docs_tree.py` 9 passed；`tests/meta/test_doc_counts.py` 1 passed；README/testing 当前声明 **224 passed / 20 UI 测试文件**，与实测一致。

## 6. v0.1.1 backlog（非阻断）

本轮未发现新的非阻断问题。上一轮报告 §6 的低优先级待办继续保留在 v0.1.1：文档计数元测试目前只解析 README（docs/testing 仍靠人工同步）；这不影响本轮 F13/F14 与发布哈希。

## 7. 内容绑定尾校验（42/42）与可发布哈希集合

| # | 文件 | 开始时 SHA-256 | 结束时 SHA-256 | 一致 |
| --- | --- | --- | --- | --- |
| 1 | `README.md` | `af7d21e5617d0d906b2cc62818eaa7cae8d7651eabdc890b36922aaed8b6e360` | `af7d21e5617d0d906b2cc62818eaa7cae8d7651eabdc890b36922aaed8b6e360` | 是 |
| 2 | `pyproject.toml` | `8d5ef77f61ca9914625a81a57c650f5e86ac300542f342b9fd0460b25e61e2d1` | `8d5ef77f61ca9914625a81a57c650f5e86ac300542f342b9fd0460b25e61e2d1` | 是 |
| 3 | `docs/requirements.md` | `61d7e7d16f1e04075d60b0181bc3a65437119665e68753dc78d9e2fc219ab6a6` | `61d7e7d16f1e04075d60b0181bc3a65437119665e68753dc78d9e2fc219ab6a6` | 是 |
| 4 | `docs/risk-model.md` | `dbf0eb0d884e1a907dcdcfd796a752b7b6aabcf79aa314cddf9062c9b2852468` | `dbf0eb0d884e1a907dcdcfd796a752b7b6aabcf79aa314cddf9062c9b2852468` | 是 |
| 5 | `docs/architecture.md` | `6110770627ad03a85db9c7005f2074e58c8b11aab172dfbff6949d7df95fe786` | `6110770627ad03a85db9c7005f2074e58c8b11aab172dfbff6949d7df95fe786` | 是 |
| 6 | `docs/testing.md` | `7f1b7dc139c20907b2f50d2ca6f3a8d0f1a5b8ba99349fe72f09b7af5c3485f1` | `7f1b7dc139c20907b2f50d2ca6f3a8d0f1a5b8ba99349fe72f09b7af5c3485f1` | 是 |
| 7 | `docs/file-tree.md` | `7b139a0e5cfc9105302278347a2e726a460adba2e89ae92e137136d03a293d02` | `7b139a0e5cfc9105302278347a2e726a460adba2e89ae92e137136d03a293d02` | 是 |
| 8 | `docs/i18n.md` | `68f856ecaefd53b76f95b87fc5f64c691366c01e0059567bbb546a217acdbf6c` | `68f856ecaefd53b76f95b87fc5f64c691366c01e0059567bbb546a217acdbf6c` | 是 |
| 9 | `docs-assets/screenshots/02-fields-risk.png` | `c15b1bc73e72e3bbe3dd71e8e70a5883f6c09a4f09cd970afe0246422680cb42` | `c15b1bc73e72e3bbe3dd71e8e70a5883f6c09a4f09cd970afe0246422680cb42` | 是 |
| 10 | `src/vbios_studio/domain/rom.py` | `4226512ca2ce1ea8e83e3c8e0e4da4c9a0a862a4550f44050f80f90c1038b5a1` | `4226512ca2ce1ea8e83e3c8e0e4da4c9a0a862a4550f44050f80f90c1038b5a1` | 是 |
| 11 | `src/vbios_studio/adapters/system/nvflash.py` | `b07c7b446daa2f22c4ee3cfb933401d0639aad049d5660db46b5705bc6310932` | `b07c7b446daa2f22c4ee3cfb933401d0639aad049d5660db46b5705bc6310932` | 是 |
| 12 | `src/vbios_studio/app/container.py` | `d24bc26a3054a2ecdf605d24cb4b834228212b61f3bcca2f728ab2e6c4ef380a` | `d24bc26a3054a2ecdf605d24cb4b834228212b61f3bcca2f728ab2e6c4ef380a` | 是 |
| 13 | `src/vbios_studio/ports/apply.py` | `3f00973ee4e86075b964cbf4debda4efd55a26e27d15850093a7f69f67309678` | `3f00973ee4e86075b964cbf4debda4efd55a26e27d15850093a7f69f67309678` | 是 |
| 14 | `src/vbios_studio/adapters/system/windows_plan.py` | `b472520a8a0b8f7ac02feb49efad9f5e5f8b971e4e53ea66a78527244dbddda3` | `b472520a8a0b8f7ac02feb49efad9f5e5f8b971e4e53ea66a78527244dbddda3` | 是 |
| 15 | `src/vbios_studio/adapters/system/windows_registry.py` | `620b825b189e35f230e167df51ca449db04ea4b28378a834fa53f1cb1c756bf8` | `620b825b189e35f230e167df51ca449db04ea4b28378a834fa53f1cb1c756bf8` | 是 |
| 16 | `src/vbios_studio/adapters/system/windows_winreg.py` | `fa9ed4e7d321ddedad49e8a7cd5cffed43050e2e2caf52dbf232c2c1c8cbf3dc` | `fa9ed4e7d321ddedad49e8a7cd5cffed43050e2e2caf52dbf232c2c1c8cbf3dc` | 是 |
| 17 | `src/vbios_studio/adapters/system/windows_verify.py` | `7889e512582e42349adfddd3c9464dd423a99690888c36f542c5e818fd9d30d5` | `7889e512582e42349adfddd3c9464dd423a99690888c36f542c5e818fd9d30d5` | 是 |
| 18 | `src/vbios_studio/adapters/system/linux_loader.py` | `be0154e64d1315ed24cd81e840f3ce199a6e6dce6cc3962cfad6e11627a170b1` | `be0154e64d1315ed24cd81e840f3ce199a6e6dce6cc3962cfad6e11627a170b1` | 是 |
| 19 | `src/vbios_studio/ui/apply_actions.py` | `4cc212d1ca45cbe140306eb4dcfdd2135969e3b2348c4216eaf972603a58402b` | `4cc212d1ca45cbe140306eb4dcfdd2135969e3b2348c4216eaf972603a58402b` | 是 |
| 20 | `src/vbios_studio/ui/controller.py` | `7deaa91a2b9253dfb1b3afcf7da840945e4717efb6b2cb4757402a816ea79ab7` | `7deaa91a2b9253dfb1b3afcf7da840945e4717efb6b2cb4757402a816ea79ab7` | 是 |
| 21 | `src/vbios_studio/ui/controller_errors.py` | `61325f6500c99c8eb1afece94e8d9fd9e599ba93157e6411bf697efe986a77d9` | `61325f6500c99c8eb1afece94e8d9fd9e599ba93157e6411bf697efe986a77d9` | 是 |
| 22 | `src/vbios_studio/ui/profile_controller.py` | `3eac00526869e58f641e3e6d73ffc6917cc7990cc15e6258317e3da030386a33` | `3eac00526869e58f641e3e6d73ffc6917cc7990cc15e6258317e3da030386a33` | 是 |
| 23 | `src/vbios_studio/ui/profile_flow.py` | `2033bc541567a46728bde78f1f0d5ad12a87d58ee6aa5781d4d81c16e2c9eb65` | `2033bc541567a46728bde78f1f0d5ad12a87d58ee6aa5781d4d81c16e2c9eb65` | 是 |
| 24 | `src/vbios_studio/ui/theme.py` | `ca299998bcd6a449f7096da48092ca9445f96b1e9309b939d28fd81ccb3d14cd` | `ca299998bcd6a449f7096da48092ca9445f96b1e9309b939d28fd81ccb3d14cd` | 是 |
| 25 | `src/vbios_studio/ui/components/apply_panel.py` | `a6f0db8d5bfa3c28dd47c8ed2a9705226a5d3f90cb58131b1a163ea4daf3ce30` | `a6f0db8d5bfa3c28dd47c8ed2a9705226a5d3f90cb58131b1a163ea4daf3ce30` | 是 |
| 26 | `src/vbios_studio/ui/components/settings.py` | `2025fedba3155c11b450a678dd747b6c96e73e3195cebbd4b75168f80e606de9` | `2025fedba3155c11b450a678dd747b6c96e73e3195cebbd4b75168f80e606de9` | 是 |
| 27 | `src/vbios_studio/ui/main_window.py` | `7e977fdfa299e532d7434600610f299fe8f0010ec5d48d7bb5b4879822ee7fbb` | `7e977fdfa299e532d7434600610f299fe8f0010ec5d48d7bb5b4879822ee7fbb` | 是 |
| 28 | `src/vbios_studio/ui/window_dialogs.py` | `99b1a3641819753590429bb002ed54dedbb9bc903a56591bb32cfa44e1af78f5` | `99b1a3641819753590429bb002ed54dedbb9bc903a56591bb32cfa44e1af78f5` | 是 |
| 29 | `src/vbios_studio/ui/dialogs/confirm_dialog.py` | `f3ac7f811489237fb8d5afda674ace3e00d2ba8bfe7a26ded387e034824ebdff` | `f3ac7f811489237fb8d5afda674ace3e00d2ba8bfe7a26ded387e034824ebdff` | 是 |
| 30 | `src/vbios_studio/i18n/locale/en/LC_MESSAGES/vbios_studio.po` | `34653667efc7529cb734f27bf4e4e0d3bdc23d73d127fb88e730758942dccf2f` | `34653667efc7529cb734f27bf4e4e0d3bdc23d73d127fb88e730758942dccf2f` | 是 |
| 31 | `src/vbios_studio/i18n/locale/zh_CN/LC_MESSAGES/vbios_studio.po` | `83393ebd367cf0f28ae2a9758249d95c4b8ad014088cf1f52e770753b6022c8f` | `83393ebd367cf0f28ae2a9758249d95c4b8ad014088cf1f52e770753b6022c8f` | 是 |
| 32 | `tests/apply/fakes.py` | `ae0b0467998c672691dc7f20e62fb0b6e3367fb99c2c6167eb304ff22f900196` | `ae0b0467998c672691dc7f20e62fb0b6e3367fb99c2c6167eb304ff22f900196` | 是 |
| 33 | `tests/apply/test_apply_operations.py` | `09e9c3af1e90cfb37f1dc5143089beed4de0b1fa170471849fa4fc78a652c49a` | `09e9c3af1e90cfb37f1dc5143089beed4de0b1fa170471849fa4fc78a652c49a` | 是 |
| 34 | `tests/apply/test_windows_registry.py` | `6831fcc3673272ad0c9910613fca58fe5ff2fff82dd930e859b176b20c062261` | `6831fcc3673272ad0c9910613fca58fe5ff2fff82dd930e859b176b20c062261` | 是 |
| 35 | `tests/apply/test_linux_loader.py` | `8e85fe0f5cddff479f4de994d047d770d88dfe340166b3c2dac67ba2eb82bc13` | `8e85fe0f5cddff479f4de994d047d770d88dfe340166b3c2dac67ba2eb82bc13` | 是 |
| 36 | `tests/integration/test_real_controller.py` | `75bf0ecf77b94c0169c53dffdb002fecbbfc8574b864aa8a0f3941a27fd99950` | `75bf0ecf77b94c0169c53dffdb002fecbbfc8574b864aa8a0f3941a27fd99950` | 是 |
| 37 | `tests/ui/test_apply_panel.py` | `de34e7890e047ce92b127cbaf108d9068986657096b358ccce1ff5195eabceb9` | `de34e7890e047ce92b127cbaf108d9068986657096b358ccce1ff5195eabceb9` | 是 |
| 38 | `tests/ui/test_apply_confirmation.py` | `1e8b1489b5f1a557595401b40e066079a65c9dda4f095ba38da8c5e706aaa7fb` | `1e8b1489b5f1a557595401b40e066079a65c9dda4f095ba38da8c5e706aaa7fb` | 是 |
| 39 | `tests/ui/test_profile_t3_gate.py` | `45131889bef09faee42f121b2bc35a3e4befab38051e371ac11807e27ac64b5a` | `45131889bef09faee42f121b2bc35a3e4befab38051e371ac11807e27ac64b5a` | 是 |
| 40 | `tests/ui/test_confirmation_words.py` | `437c7db95aa120ac3eadbcddb18258949def065fc581621874f260b60509cd7c` | `437c7db95aa120ac3eadbcddb18258949def065fc581621874f260b60509cd7c` | 是 |
| 41 | `tests/ui/test_profile_replace.py` | `34ad9ef7fe9e8660e7974fd91d251fe3c23982217ef4c72a4d287f5650a148f3` | `34ad9ef7fe9e8660e7974fd91d251fe3c23982217ef4c72a4d287f5650a148f3` | 是 |
| 42 | `tests/meta/test_doc_counts.py` | `1182fc20ce646aec82206ee2a9683832e77ad9ce3b2c219017a3a080ef33a415` | `1182fc20ce646aec82206ee2a9683832e77ad9ce3b2c219017a3a080ef33a415` | 是 |

**42/42 一致。** 评审期间未改动任何基线文件。§2/§7 的这 42 个 SHA-256 即为本报告的**可发布哈希集合**；发布审计与归档校验应逐项比对。

## 8. 复现命令汇总

```bash
cd vbios-studio
source .venv/bin/activate
python -m pytest -q
.venv/bin/lint-imports
.venv/bin/ruff check src tests
.venv/bin/ruff format --check src tests
.venv/bin/mypy --strict src/vbios_studio
python3 tools/prepush_audit.py --strict
.venv/bin/python -m pytest -q tests/ui/test_apply_confirmation.py
.venv/bin/python -m pytest -q tests/apply/test_apply_operations.py
test -f docs/review-final-v2.md
```

## 9. 最终判定

**PASS（软件层）。** F13/F14 均已关闭；UI 无硬编码键名单；确认正文与实际写入同源；42 文件内容绑定一致。可直接作为发布审计的哈希依据。
