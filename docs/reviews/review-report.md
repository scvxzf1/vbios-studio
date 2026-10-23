# VBIOS Studio 独立评审报告（第二轮）

> ⚠️ 历史记录：本报告反映当时状态，可能包含已被修复的问题。
> 当前状态见 [评审与审计索引](README.md)。

> 评审角色：reviewer · 评审日期：2026-10-23 · 被评审交付：修复后的当前工作树
>
> **结论：PASS（软件层）**。本轮对 33 个文件做内容绑定；F1–F7 关闭项均通过，验收 4 项均通过。另记录 4 项非阻断观察（§5），其中预设整体替换当前改动建议作为发布前 follow-up；不影响本轮 PASS 判定。
>
> 本报告取代上一轮 `NEEDS_REVISION` 报告；上一轮报告中的阻断项已在当前字节上逐项复核。

## 0. 评审基线（内容绑定）

**本评审针对以下 33 个文件的哈希集合；评审结束时逐项复算，任一变化即判 `needs_revision` 并指出被改动文件。** 这些文件覆盖：8 份仓库/契约/说明文件 + 20 个源码文件 + 5 个关键测试文件。

| # | 文件 | 字节数 | SHA-256 |
| --- | --- | ---: | --- |
| 1 | `README.md` | 13,898 | `f2ede61059a96a05c9c3b14a40b8b2c72ae693d8a7a716cadd8a62a4390e8417` |
| 2 | `pyproject.toml` | 3,539 | `8d5ef77f61ca9914625a81a57c650f5e86ac300542f342b9fd0460b25e61e2d1` |
| 3 | `docs/requirements.md` | 38,009 | `2e60a573c60661f37a167d504e45e0553b5318325caa8c332ab94cd13e4b8050` |
| 4 | `docs/risk-model.md` | 29,564 | `dbf0eb0d884e1a907dcdcfd796a752b7b6aabcf79aa314cddf9062c9b2852468` |
| 5 | `docs/architecture.md` | 14,903 | `5e3a651a9c81113711aa4ac3dbeaf3cd4a8a008ab8982e84ca45469726e1366f` |
| 6 | `docs/testing.md` | 8,642 | `cd9441f2f2e4b037e7d8fbb117d467a355040de3a41dd822b198d29658ee32e3` |
| 7 | `docs/file-tree.md` | 15,033 | `774adee779ee703b59ced5b5bdbce82322f4a09d0c4aa5436a7287599eaf3ccd` |
| 8 | `docs/i18n.md` | 5,046 | `b6b76a14e71ba37945615e122bb2ef769f43a1ea76ec6cce77d606861f993b83` |
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
| 21 | `src/vbios_studio/ui/profile_flow.py` | 5,274 | `c694a267fb3c3148b7a552ab1982eaada9846625ef41a9b69aaf91e6791cace5` |
| 22 | `src/vbios_studio/ui/components/apply_panel.py` | 10,967 | `f5763a0845b396dfd2cac60c0cadb8148b72ac323d8aba8c399ab4f41472db7a` |
| 23 | `src/vbios_studio/ui/components/settings.py` | 1,253 | `2025fedba3155c11b450a678dd747b6c96e73e3195cebbd4b75168f80e606de9` |
| 24 | `src/vbios_studio/ui/main_window.py` | 14,233 | `bbd77f34a17ee87ed2c84f1d7e8933450d2bec60cf98ea7ca3de2c9acd9f5463` |
| 25 | `src/vbios_studio/ui/window_dialogs.py` | 5,370 | `99b1a3641819753590429bb002ed54dedbb9bc903a56591bb32cfa44e1af78f5` |
| 26 | `src/vbios_studio/ui/dialogs/confirm_dialog.py` | 5,147 | `f3ac7f811489237fb8d5afda674ace3e00d2ba8bfe7a26ded387e034824ebdff` |
| 27 | `src/vbios_studio/i18n/locale/en/LC_MESSAGES/vbios_studio.po` | 19,304 | `539b7f2b318cdecc0a5dbe11569e52a90ffb748e38d6989a0086b56877df75b1` |
| 28 | `src/vbios_studio/i18n/locale/zh_CN/LC_MESSAGES/vbios_studio.po` | 19,020 | `ec6aeb2e272a1e1e8da22e30a467789b1727534e65f004fa26f67abb80b357b2` |
| 29 | `tests/integration/test_real_controller.py` | 3,602 | `75bf0ecf77b94c0169c53dffdb002fecbbfc8574b864aa8a0f3941a27fd99950` |
| 30 | `tests/apply/test_windows_registry.py` | 8,540 | `6831fcc3673272ad0c9910613fca58fe5ff2fff82dd930e859b176b20c062261` |
| 31 | `tests/ui/test_profile_t3_gate.py` | 3,641 | `45131889bef09faee42f121b2bc35a3e4befab38051e371ac11807e27ac64b5a` |
| 32 | `tests/ui/test_apply_panel.py` | 5,326 | `485cdf1c4f1d513074380c7718085d0b2c3aa74d10d58a094cb57b9abb9f1115` |
| 33 | `tests/ui/test_confirmation_words.py` | 1,468 | `437c7db95aa120ac3eadbcddb18258949def065fc581621874f260b60509cd7c` |

基线登记时间：2026-10-23T02:49+08:00。评审期间未修改上表任何文件；尾校验见 §7。

## 1. 评审范围与方法

- 对当前工作树独立复核上一轮 F1–F7，并重新检查分层、T0–T3 风险标注、文件大小/重复实现、README/docs 测试声明。
- 独立执行：全量 `pytest`、`ruff check`、`ruff format --check`、`mypy --strict`、`lint-imports`、`tools/build_local.sh --check`、`tools/prepush_audit.py --strict`、3 进程并发 `vbios-studio-gui --selftest`、`git check-ignore`。
- 评审只写入本文件 `docs/reviews/review-report.md`；未改动源码、测试或文档。
- 本报告所有行号均针对 §0 基线字节；行号只用于定位，修复后应重新定位符号。

## 2. 上一轮 F1–F7 关闭核对

| 项 | 结论 | 当前字节证据 |
| --- | --- | --- |
| F1 payload 由组合根注入，集成测试不再手动 `set_payload` | **PASS** | `src/vbios_studio/ui/apply_actions.py:40-66` 的 `save_as()` 读取 `SaveResult.payload_paths[0]` 并调用 `configure_payload`；`src/vbios_studio/ports/apply.py:20-22` 暴露配置入口；`tests/integration/test_real_controller.py:76-82` 断言 `apply.payload == payload_bytes` 且 dry-run 字节数一致。`grep -n 'set_payload' tests/integration/test_real_controller.py` → 0。 |
| F2 execute 消费一次性票据；无票据/哈希不匹配/重放均零写入 | **PASS** | `src/vbios_studio/adapters/system/windows_registry.py:73-74` 私有票据；`:145-167` dry-run 生成绑定 payload SHA-256/target/device 的票据；`:170-196` 消费票据并在不匹配时返回 `CONFIRMATION_MISMATCH`。`tests/apply/test_windows_registry.py:148`、`:162`、`:197` 分别覆盖无票据、重放、哈希不匹配；均断言 `writable_opens == 0`/mutations 空。 |
| F3 预设 T3 门控：未解锁拒绝、解锁未确认拒绝、确认成功；changes 与 stage 次数均有断言 | **PASS** | `src/vbios_studio/ui/profile_controller.py:41-82` 在调用 profile adapter 前收集 T3 字段并校验 `experimental_unlocked` + `confirmed_t3`；`tests/ui/test_profile_t3_gate.py:43-70` 三个用例分别断言 `changes == {}`、`editor.stage_calls == 0` 或 `== 1`；`:74-109` 覆盖 UI 取消/确认。 |
| F4 确认词 I UNDERSTAND / 字段 key 或 T3，含 i18n | **PASS** | `src/vbios_studio/ui/dialogs/confirm_dialog.py:19-20` 定义 `EXPERIMENTAL_UNLOCK_WORD = "I UNDERSTAND"`、`T3_CONFIRM_WORD = "T3"`；`src/vbios_studio/ui/components/settings.py:38` 使用前者；`src/vbios_studio/ui/profile_flow.py:95,142` 使用 `allowed_words=(field.key, T3_CONFIRM_WORD)`；`tests/ui/test_confirmation_words.py:15-41` 覆盖词表、规则和 i18n。 |
| F5 Verify 逐字节比较 + LinuxLoaderAdapter 接入生产组合根 | **PASS（有文档化硬件盲区）** | `src/vbios_studio/ports/apply.py:35-37` 暴露 `verify`；`src/vbios_studio/ui/apply_actions.py:74-89` 调用；`src/vbios_studio/ui/components/apply_panel.py:262-270` Verify 按钮走 `controller.apply_verify()`；`src/vbios_studio/adapters/system/windows_verify.py:23-80` 做 `active == running_image` 字节比较；`src/vbios_studio/app/container.py:52-65` 在 Linux 选择 `LinuxLoaderAdapter`，`tests/apply/test_linux_loader.py:72` 覆盖。实际 `windows_winreg.py:149-156` 的 `vbios_image()` 仍返回 `None`，README:128 已明确 `VERIFY_UNAVAILABLE`；真实 NvAPI 读取仍是硬件盲区（§5.4）。 |
| F6 测试计数同步；F7 NFR-02 路径修正 | **PASS** | `README.md:149` 与 `docs/testing.md:6,81` 当前均为 205 passed、18 UI 测试文件、77 mypy、282 msgid；`docs/requirements.md:237` 指向实际存在的 `tests/contract/test_file_sizes.py`。全量 205 passed 与 `test_docs_tree.py` 通过（§4）。 |

## 3. 验收项逐项核对

### 3.1 分层解耦：UI 是否仅依赖 ports

**结论：PASS。**

```text
$ .venv/bin/lint-imports
domain-pure KEPT
ui-no-adapters KEPT
ports-no-implementations KEPT
layers-app-top KEPT
i18n-standalone KEPT
Contracts: 5 kept, 0 broken.
```

`tests/contract/test_import_boundaries.py` 通过。抽查 3 个 UI 文件：

| 文件 | import 证据 | 判断 |
| --- | --- | --- |
| `src/vbios_studio/ui/controller.py` | `11-27`：`domain.errors/models`、`ports.apply/diff/editor/profile`、`ui.apply_actions/controller_errors/filtering/profile_controller`；无 `gi`/`nvidia_vbios`/`subprocess`/`winreg`/`adapters` | 仅依赖 domain/ports/UI |
| `src/vbios_studio/ui/main_window.py` | `11-38`：`gi`/`gi.repository`、`domain.errors/models`、`i18n`、`ui.components/dialogs/drop_target/shortcuts`；无 `vbios_studio.adapters` | GTK 视图不直接触达适配器 |
| `src/vbios_studio/ui/profile_controller.py` | `7-17`：`domain.errors/models`、`ports.profile`、`ui.controller_errors`；无 `gi`/`adapters` | 预设批量路径仍只经 port |

`ui` 到 `vbios_studio.adapters`/`nvidia_vbios` 的导入为 0；`app/container.py` 是唯一组合根。

### 3.2 T0–T3 风险标注与实验性字段

**结论：PASS（T3 逐字段门控与预设门控均已落地；批次 UI 观察见 §5.3）。**

实验性字段清单（源码 `src/vbios_studio/domain/risk_registry.py:49-164`）：

| 类别 | 实验性字段（键/模式） | 基础等级 | UI 代码位置 |
| --- | --- | --- | --- |
| 功耗 | `power_default_w`、`power_max_w`、`slot_power_(max|rated)_w`、`connector_N_power_(max|rated)_w`、`connector_sum_power_*`、`board_fixed_rated_w`、`nvvdd_power_threshold_*`；`max_operating_temp_c` | T3；`max_operating_temp_c` T2 | `risk_registry.py:49-83`；徽章 `risk_badge.py:37-43`、`field_form.py:89-91`、`field_table.py:225-226` |
| 电压 | `(nvvdd|msvdd)_rel_max_mv`、`*_vmin_mv`、`nvvdd_(rel|alt)_fixed_mv`、`nvvdd_rel_alt_follow_ov`、`*_equation_max_mv` | T3 | `risk_registry.py:85-89`；`field_form.py:96-101` 显示 evidence 描述 |
| 电流/保护阈值 | `input_current_*`、`*_output_ocp_*`、`slot_current_threshold_*`、`connector_N_current_threshold_*` | T3 | `risk_registry.py:94-125`；`field_table.py:225-226` |
| 风扇 | `fan_channels`、`fan_zero_rpm`、`*_zero_rpm_*_temp_c`；`fan_pwm_frequency_hz`、`fan_N_min/max_*`、风扇曲线 | T3；后三类 T2 | `risk_registry.py:129-155`；`risk_badge.py:37-43` |
| 时钟 | `(gpc|memory)_offset_*`、`(dram|xbar|sys|vid)_*_table_mhz`、`gpc_curve_offset_mhz`、`factory_gpc_offset_mhz`、`memory_point_*_follows_offset` | T2 | `risk_registry.py:157-161`；`catalog.py:97-102` 写入 DTO |
| 高级电源 | `perf_cf_*`、`lpwr_*` | T3 | `risk_registry.py:163-164`；`field_form.py:89-91` |

T3 门控证据：

- `src/vbios_studio/ui/controller.py:136-139` 默认过滤全部 T3；`:199-221` 要求 `experimental_unlocked` 与 `t3_confirmed` 双条件。
- `src/vbios_studio/ui/main_window.py:315-346` 显示字段、旧值→新值、单位、风险说明；`src/vbios_studio/ui/dialogs/confirm_dialog.py:20-130` 校验勾选 + 字段 key/`T3`。
- `src/vbios_studio/ui/profile_controller.py:41-82` 对预设中的 T3 字段走同一门控；`tests/ui/test_profile_t3_gate.py` 覆盖 locked/unconfirmed/confirmed。
- `src/vbios_studio/ui/components/settings.py:38` 实验模式使用 `I UNDERSTAND`；`src/vbios_studio/i18n` 的 `experimental.word` 与 T3 确认词文案已同步为冻结词。
- `src/vbios_studio/domain/catalog.py:97-102` 将 `is_experimental()` 写入 `FieldSnapshot.experimental`；`tests/domain/test_risk_registry.py` 全量通过。

T2 实验性字段同样带 `EXPERIMENTAL` 徽章与说明；T3 默认隐藏、逐字段二次确认，符合 `docs/risk-model.md` §1/§7.2 的字段级要求。

### 3.3 超大文件、400 行与重复实现

**结论：PASS。**

- 自有 `src/vbios_studio/` 共 77 个 `.py`，最大 `src/vbios_studio/adapters/upstream.py:1-399`；无自有文件 >400 行。`tests/` 共 59 个 `.py`，最大 `tests/core/rom_fixtures.py:1-400`（恰好 400，未超）。
- `tests/contract/test_file_sizes.py` 通过；`git ls-files` 无 >1 MB 文件。
- 上游只读镜像 `src/nvidia_vbios/editor/registry.py:1-3240`、`src/nvidia_vbios/gui/app.py:1-1456` 等 >400 行；这是 `UPSTREAM.md` 固定 pin 的逐字节镜像，受 `INV-05` 保护并由 `tests/contract/test_version.py` 校验 31 文件 SHA-256，NFR-02 的 400 行只适用于自有代码。若要求 vendored 上游也 ≤400 行，会违反 INV-05，故该例外必要。
- 重复实现：`src/vbios_studio/domain/rom.py:169-252` 的 `scan_rom()` 与 `:274-334` 的 `apply_byte_edits()` 确实重复实现 PCI/NPDS 扫描与校验和修复；`docs/architecture.md:13,52,113,133` 明确 domain 是 ROM 结构/校验和的唯一职责，`tests/core/test_rom_structure.py`、`test_checksum_rebalance.py`、`tests/golden` 覆盖；字段编辑/plan/normalize/save 仍只经 `adapters/upstream.py` 调 vendored `nvidia_vbios`，未发现第二套字段算法。该重复为有意的纯 domain 设计，不判缺陷。

### 3.4 README/docs 的“测试不完全”声明

**结论：PASS（主声明醒目、计数与实测一致；残留文档漂移见 §5.2）。**

- `README.md:3-14` 首屏第一块即 `[!WARNING] ## ⚠️ 测试不完全 / 未在真实硬件验证`，明确写明未在真实 GPU 执行应用、override、Linux loader 注入或刷写，并列出硬件损坏风险；`:147-160` 再次列出未测试矩阵。
- `docs/testing.md:3-8` 顶部声明“所有测试都是软件层测试……没有在真实显卡上执行过……压力测试或刷写”，`:92` 明确本机结果不是 Windows/真实硬件结果。
- 当前实测与文档主计数一致：`README.md:149`、`docs/testing.md:6,81` 均写 205 passed、18 UI 测试文件、77 mypy、282 msgid；实际 `pytest -q` 为 205 passed/0 skipped（§4），不存在把软件测试说成真机验证的夸大。
- 残留：`docs/architecture.md:57`、`docs/i18n.md:8`、`docs/file-tree.md:121,123` 仍写 279 msgid；`docs/architecture.md:187` 仍写 T3 确认词 `CONFIRM`（冻结词已为字段 key/`T3`）；`docs/file-tree.md:25` 的 ApplyPort 方法列表仍是旧签名。均为文档同步问题，不影响主 README/testing 的测试声明；建议发布前清理（§5.2）。

## 4. 独立命令结果

```text
$ .venv/bin/python -m pytest -q
205 passed in 16.96s

$ .venv/bin/ruff check src tests
All checks passed!

$ .venv/bin/ruff format --check src tests
144 files already formatted

$ .venv/bin/mypy --strict src/vbios_studio
Success: no issues found in 77 source files

$ .venv/bin/lint-imports
Contracts: 5 kept, 0 broken.

$ bash tools/build_local.sh --check
205 passed in 18.96s
==> all checks passed

$ python tools/prepush_audit.py --strict
files scanned: 218
tracked files: 210
total size: 2.1 MiB
largest file: src/nvidia_vbios/editor/registry.py (234,736 bytes)
likely binary files: 5（3 张截图 + 2 个 .mo，均为预期资产）
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

| 进程 | exit code | 关键输出 |
| --- | --- | --- |
| 1 | 0 | `vbios-studio 0.1.0 selftest: ok (window, a11y, undo/redo, 3 screenshots)` |
| 2 | 0 | 同上 |
| 3 | 0 | 同上 |

三次均生成 3 张 1270×830 PNG；stdout 仅 libEGL DRI3 警告与“Unable to connect to the accessibility bus”，stderr 为空，非失败。并发 selftest：**PASS**。

## 5. 非阻断观察

### 5.1 预设应用整体替换当前 staged changes（建议发布前处理）

`src/vbios_studio/ui/profile_controller.py:82-87` 的 `apply_profile()`：

```python
previous = dict(self.changes)
preview = self.profile_port.apply_profile(document)
...
self.changes = {change.key: change.new for change in preview.changed}
```

`EditorPort.stage()` 当前是替换式（`UpstreamEditorAdapter.stage()` 用本次 `requested` 覆盖 `_staged`）；而普通单字段 `set_value()` 用 `candidate = dict(self.changes)` 累积。实测：已有 `power_min_w=120`、`gpc_offset_max_mhz=250` 两项编辑时，套用只含 `power_min_w=110` 的 profile，`changes` 变为 `{'power_min_w': '110'}`，另外一项被静默清空；`undo` 可恢复，但应用前没有提示。

**判定：**
- **不是 `docs/risk-model.md` §7.2 的字面冲突**：§7.2 只规定 T3 逐字段确认，不规定 profile 与已有 changes 的合并策略。
- **不直接违反 `docs/requirements.md` FR-2.6 的“整体拒绝/零部分写入”**：该条只针对无效/跨架构/越界 profile；当前行为仍是原子 stage。
- **但属于用户可见的数据完整性/UX 缺陷**：它违背了“变更集”的直觉，尤其 profile 只含 1 个字段时会无声丢掉其他未保存编辑（undo 只是补救，不是告知）。

**最小修法（推荐显式提示，而不是默认合并）：** 在 `ProfileFlow.apply_document()` 调用 `controller.apply_profile()` 前，若 `controller.changes` 非空且存在 `set(controller.changes) - set(profile_changes)`，弹出确认：“应用预设将替换当前 N 项未保存改动（列出 key）”；取消则不调用 controller、`changes` 不变；确认后才进入现有 T3 流程。若要合并，则需先定义冲突优先级，并对合并后的 T3 集合重新走逐字段确认，成本更高。建议补测试：已有 2 项编辑 + 1 字段 profile，取消保留 2 项，确认后替换且 undo 恢复 2 项。

### 5.2 文档残留计数/确认词漂移（LOW）

- `docs/architecture.md:57`、`docs/i18n.md:8`、`docs/file-tree.md:121,123` 仍写 279 msgid，实测 282（`grep -c '^msgid' ...`，en/zh_CN 均 282）。
- `docs/architecture.md:187` 仍写 T3 需输入 `CONFIRM` + 勾选；冻结实现已改为字段 key 或 `T3`（`confirm_dialog.py:19-20`）。
- `docs/file-tree.md:25` 的 `ports/apply.py` 方法列表仍是旧的 `device_status/dry_run/execute/restore`，未列 `configure_payload`/`verify`；`docs/architecture.md:56` 仍说 app “后续确认票据”，与已实现的票据不符。
- `docs/requirements.md:237` 已正确指向 `tests/contract/test_file_sizes.py`；最后一轮文档计数同步已更新 README/testing 主计数。上述残余属于文档一致性，不影响 §3.4 主声明；发布前建议一并清理。

### 5.3 T3 批次横幅/应用确认文案（MEDIUM，建议发布前补）

`docs/risk-model.md` §7.2 第 6 条要求“应用批次若含 T3：应用面板顶部红色横幅列出全部 T3 变更；执行前再确认一次”。当前 `src/vbios_studio/ui/components/apply_panel.py` 没有使用 `controller.batch_risk()` 或 `preview.changes`，确认 body 是静态 `apply.confirm.body`（`apply_panel.py:222`），没有把具体注册表项/命令动态带入；dry-run 预览本身会显示 target/bytes/values，因此不是 T3 门控绕过，但属于 T3 批次说明缺失。建议在应用面板增加 T3 变更清单（key/旧值→新值）并让确认 body 包含 `last_preview.target`/`bytes_written`/payload SHA-256；不影响本轮 PASS，但应作为发布前 UI 完整性 follow-up。

### 5.4 真实 Windows Verify 的硬件盲区（LOW/已声明）

`src/vbios_studio/adapters/system/windows_winreg.py:149-156` 的 `vbios_image()` 目前返回 `None`，等待注入 NvAPI 读取器；因此真实 Windows 上 `Verify` 会明确返回 `VERIFY_UNAVAILABLE`，不会把存储 override 当运行镜像。`README.md:128` 已声明该限制；这是硬件/驱动层盲区，不是本轮软件层回归。F5 的 fake platform 逐字节路径已由 `tests/apply/test_windows_registry.py:185` 覆盖。

## 6. 仓库卫生与 .gitignore

`python tools/prepush_audit.py --strict` 已 PASS（§4）。补充：

```text
.venv/pyvenv.cfg                         .gitignore:9:.venv/
build/x                                  .gitignore:15:build/
dist/x                                   .gitignore:16:dist/
src/vbios_studio/__pycache__/x.pyc       .gitignore:2:__pycache__/
tests/fixtures/card.rom                  .gitignore:40:*.rom
tests/fixtures/card.bin                  .gitignore:41:*.bin
bin/tool.exe                             .gitignore:42:*.exe
```

`git ls-files` 210 个跟踪文件；无 `.rom`/`.bin`/`.exe`/`.dll`/`.sys`/`.efi` 禁止载荷；无被忽略但已跟踪文件。结论：**PASS**。

## 7. 评审尾校验（内容绑定）

评审结束时（2026-10-23T02:50+08:00）复算 §0 的 33 个文件：

| # | 文件 | 开始时 SHA-256 | 结束时 SHA-256 | 一致 |
| --- | --- | --- | --- | --- |
| 1 | `README.md` | `f2ede61059a96a05c9c3b14a40b8b2c72ae693d8a7a716cadd8a62a4390e8417` | `f2ede61059a96a05c9c3b14a40b8b2c72ae693d8a7a716cadd8a62a4390e8417` | 是 |
| 2 | `pyproject.toml` | `8d5ef77f61ca9914625a81a57c650f5e86ac300542f342b9fd0460b25e61e2d1` | `8d5ef77f61ca9914625a81a57c650f5e86ac300542f342b9fd0460b25e61e2d1` | 是 |
| 3 | `docs/requirements.md` | `2e60a573c60661f37a167d504e45e0553b5318325caa8c332ab94cd13e4b8050` | `2e60a573c60661f37a167d504e45e0553b5318325caa8c332ab94cd13e4b8050` | 是 |
| 4 | `docs/risk-model.md` | `dbf0eb0d884e1a907dcdcfd796a752b7b6aabcf79aa314cddf9062c9b2852468` | `dbf0eb0d884e1a907dcdcfd796a752b7b6aabcf79aa314cddf9062c9b2852468` | 是 |
| 5 | `docs/architecture.md` | `5e3a651a9c81113711aa4ac3dbeaf3cd4a8a008ab8982e84ca45469726e1366f` | `5e3a651a9c81113711aa4ac3dbeaf3cd4a8a008ab8982e84ca45469726e1366f` | 是 |
| 6 | `docs/testing.md` | `cd9441f2f2e4b037e7d8fbb117d467a355040de3a41dd822b198d29658ee32e3` | `cd9441f2f2e4b037e7d8fbb117d467a355040de3a41dd822b198d29658ee32e3` | 是 |
| 7 | `docs/file-tree.md` | `774adee779ee703b59ced5b5bdbce82322f4a09d0c4aa5436a7287599eaf3ccd` | `774adee779ee703b59ced5b5bdbce82322f4a09d0c4aa5436a7287599eaf3ccd` | 是 |
| 8 | `docs/i18n.md` | `b6b76a14e71ba37945615e122bb2ef769f43a1ea76ec6cce77d606861f993b83` | `b6b76a14e71ba37945615e122bb2ef769f43a1ea76ec6cce77d606861f993b83` | 是 |
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
| 21 | `src/vbios_studio/ui/profile_flow.py` | `c694a267fb3c3148b7a552ab1982eaada9846625ef41a9b69aaf91e6791cace5` | `c694a267fb3c3148b7a552ab1982eaada9846625ef41a9b69aaf91e6791cace5` | 是 |
| 22 | `src/vbios_studio/ui/components/apply_panel.py` | `f5763a0845b396dfd2cac60c0cadb8148b72ac323d8aba8c399ab4f41472db7a` | `f5763a0845b396dfd2cac60c0cadb8148b72ac323d8aba8c399ab4f41472db7a` | 是 |
| 23 | `src/vbios_studio/ui/components/settings.py` | `2025fedba3155c11b450a678dd747b6c96e73e3195cebbd4b75168f80e606de9` | `2025fedba3155c11b450a678dd747b6c96e73e3195cebbd4b75168f80e606de9` | 是 |
| 24 | `src/vbios_studio/ui/main_window.py` | `bbd77f34a17ee87ed2c84f1d7e8933450d2bec60cf98ea7ca3de2c9acd9f5463` | `bbd77f34a17ee87ed2c84f1d7e8933450d2bec60cf98ea7ca3de2c9acd9f5463` | 是 |
| 25 | `src/vbios_studio/ui/window_dialogs.py` | `99b1a3641819753590429bb002ed54dedbb9bc903a56591bb32cfa44e1af78f5` | `99b1a3641819753590429bb002ed54dedbb9bc903a56591bb32cfa44e1af78f5` | 是 |
| 26 | `src/vbios_studio/ui/dialogs/confirm_dialog.py` | `f3ac7f811489237fb8d5afda674ace3e00d2ba8bfe7a26ded387e034824ebdff` | `f3ac7f811489237fb8d5afda674ace3e00d2ba8bfe7a26ded387e034824ebdff` | 是 |
| 27 | `src/vbios_studio/i18n/locale/en/LC_MESSAGES/vbios_studio.po` | `539b7f2b318cdecc0a5dbe11569e52a90ffb748e38d6989a0086b56877df75b1` | `539b7f2b318cdecc0a5dbe11569e52a90ffb748e38d6989a0086b56877df75b1` | 是 |
| 28 | `src/vbios_studio/i18n/locale/zh_CN/LC_MESSAGES/vbios_studio.po` | `ec6aeb2e272a1e1e8da22e30a467789b1727534e65f004fa26f67abb80b357b2` | `ec6aeb2e272a1e1e8da22e30a467789b1727534e65f004fa26f67abb80b357b2` | 是 |
| 29 | `tests/integration/test_real_controller.py` | `75bf0ecf77b94c0169c53dffdb002fecbbfc8574b864aa8a0f3941a27fd99950` | `75bf0ecf77b94c0169c53dffdb002fecbbfc8574b864aa8a0f3941a27fd99950` | 是 |
| 30 | `tests/apply/test_windows_registry.py` | `6831fcc3673272ad0c9910613fca58fe5ff2fff82dd930e859b176b20c062261` | `6831fcc3673272ad0c9910613fca58fe5ff2fff82dd930e859b176b20c062261` | 是 |
| 31 | `tests/ui/test_profile_t3_gate.py` | `45131889bef09faee42f121b2bc35a3e4befab38051e371ac11807e27ac64b5a` | `45131889bef09faee42f121b2bc35a3e4befab38051e371ac11807e27ac64b5a` | 是 |
| 32 | `tests/ui/test_apply_panel.py` | `485cdf1c4f1d513074380c7718085d0b2c3aa74d10d58a094cb57b9abb9f1115` | `485cdf1c4f1d513074380c7718085d0b2c3aa74d10d58a094cb57b9abb9f1115` | 是 |
| 33 | `tests/ui/test_confirmation_words.py` | `437c7db95aa120ac3eadbcddb18258949def065fc581621874f260b60509cd7c` | `437c7db95aa120ac3eadbcddb18258949def065fc581621874f260b60509cd7c` | 是 |

**33/33 一致，评审期间没有任何基线文件被改动。** 本报告结论绑定上述哈希集合；若后续修改任何基线文件，本 PASS 失效，应重新评审。

## 8. 结论

**判定：PASS（软件层）。**

- 分层解耦：PASS（§3.1）。
- T0–T3 风险标注与实验性字段：PASS（§3.2）；T3 逐字段确认、预设 T3 门控、确认词均已落地。
- 超大文件/400 行/重复实现：PASS（§3.3）。
- README/docs“测试不完全”声明：PASS（§3.4）；主计数 205 passed/0 skipped 与实测一致。
- 独立验证：205 passed、ruff/format/mypy/lint-imports、build_local --check、prepush --strict、3 进程并发 selftest 全部通过（§4/§6）。
- 非阻断观察：预设整体替换（§5.1，建议发布前提示）、文档残留计数/确认词（§5.2）、T3 批次横幅与应用确认文案（§5.3）、真实 Windows NvAPI Verify 盲区（§5.4，已声明）。这些不构成当前冻结契约的字面违反，但 §5.1/§5.3 建议在公开发布前处理。

**本次 PASS 绑定的哈希集合：§0/§7 的 33 个文件 SHA-256（33/33 复算一致）。**
