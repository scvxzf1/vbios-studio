# `vbios_studio.ui` — GTK4 视图层

## 职责

- 主窗口、工具栏、左侧导航、文件信息卡片、字段表格/表单、搜索过滤、撤销重做、预设、diff、应用/刷写面板、空状态与错误对话框（t4）。
- 仅渲染 domain DTO，调用 `EditorPort` / `DiffPort` / `ProfilePort` / `ApplyPort`。
- 所有文案经 `vbios_studio.i18n` / gettext；不硬编码可见文本。
- `--selftest`：无显示环境下的自检入口（t2 为纯 Python 版本，t4 扩展为 xvfb 检查）。

## 依赖方向

- 允许依赖 `vbios_studio.domain`、`vbios_studio.ports`、`vbios_studio.i18n` 与 PyGObject/GTK（仅 GUI 路径，延迟 import）。
- **禁止** import `vbios_studio.adapters` 或 `nvidia_vbios`；不得直接读写文件/注册表/子进程。

## 入口

- `python -m vbios_studio --selftest`
- `python -m vbios_studio.ui --selftest`
- `vbios-studio-gui`（安装后）
