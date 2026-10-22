# 上传前仓库审计报告（prepush audit）

> 本报告由 `python tools/prepush_audit.py --strict --report docs/prepush-audit.md` 生成。结论基于当前工作树的实际字节；任何一项检查失败都会使 `--strict` 退出非 0。

## 结论

**PASS**

## 概览

| 项目 | 结果 |
| --- | --- |
| 扫描文件数 | 210 |
| Git 跟踪文件数 | 210 |
| 总体积 | 2.1 MiB |
| 最大文件 | `src/nvidia_vbios/editor/registry.py`（234,736 bytes） |
| 疑似二进制文件 | 5 |
| 禁止的固件/原生二进制 | 0 |
| 超过 1 MB 的文件 | 0 |
| 疑似密钥 | 0 |
| `.gitignore` 缺失模式 | 0 |
| 被 ignore 但已跟踪的文件 | 0 |

## 疑似二进制清单

| 文件 | 大小 | 说明 |
| --- | ---: | --- |
| `docs-assets/screenshots/01-main-window.png` | 220,941 bytes | 界面截图（预期资产） |
| `docs-assets/screenshots/02-fields-risk.png` | 207,747 bytes | 界面截图（预期资产） |
| `docs-assets/screenshots/03-apply-panel.png` | 165,201 bytes | 界面截图（预期资产） |
| `src/vbios_studio/i18n/locale/en/LC_MESSAGES/vbios_studio.mo` | 18,429 bytes | 编译后的 gettext 翻译目录（预期资产） |
| `src/vbios_studio/i18n/locale/zh_CN/LC_MESSAGES/vbios_studio.mo` | 18,164 bytes | 编译后的 gettext 翻译目录（预期资产） |

## 禁止的固件 / 原生二进制

  - 无

## 超大文件（> 1 MB）

  - 无

## 疑似密钥扫描

  - 无

## .gitignore 策略

覆盖完整：`.venv/`、`__pycache__/`、`*.pyc`、`*.egg-info/`、`.pytest_cache/`、`.mypy_cache/`、`.ruff_cache/`、pip 缓存、`build/`、`dist/`、`*.rom`、`*.bin`、`*.exe`、`.env`、`.DS_Store`。

## 被 ignore 但已跟踪的文件

无（符合要求）。

## 判定规则

- 禁止的固件/原生二进制：`.bin`, `.cap`, `.dll`, `.efi`, `.exe`, `.fv`, `.img`, `.iso`, `.pyc`, `.pyo`, `.rom`, `.sys`, `.vbi`；
- 禁止的环境文件：`.env`, `.env.local`, `.env.production`；
- 单文件上限：1,000,000 bytes；
- 被 `.gitignore` 命中却仍被 Git 跟踪的文件必须为 0。
