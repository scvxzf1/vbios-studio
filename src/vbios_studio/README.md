# `vbios_studio` — 应用包

VBIOS Studio 的 Python 包，采用五层 + i18n 的分层结构：

```
vbios_studio/
├── domain/     # 纯逻辑与冻结 DTO（不依赖 gi/adapters/ui）
├── ports/      # Protocol 抽象接口（只依赖 domain）
├── adapters/   # 上游桥接与系统适配器（注册表/loader/nvflash）
├── ui/         # GTK4 视图（只依赖 ports/domain/i18n）
├── app/        # 组合根与 CLI（可依赖全部）
└── i18n/       # gettext 与语言检测（仅标准库）
```

## 入口

```bash
python -m vbios_studio --version
python -m vbios_studio --selftest
python -m vbios_studio.ui --selftest
vbios-studio            # 安装后的 CLI
vbios-studio-gui        # 安装后的 GUI
```

`--version` 与 `--selftest` 不加载 GTK；`--gui` 才会延迟 import PyGObject。

## 依赖规则

详见 `docs/architecture.md`；由 `pyproject.toml` 的 `[tool.importlinter]` 与 `tests/contract/` 强制。
