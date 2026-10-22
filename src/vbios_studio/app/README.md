# `vbios_studio.app` — 组合根与应用服务

## 职责

- `cli.py`：`vbios-studio` / `python -m vbios_studio` 命令入口；`--version`、`--selftest`、`--gui`。
- `container.py`：构造具体 adapter 并以 `ports` Protocol 注入；测试可替换 fake。
- 未来的撤销/重做栈、确认票据、会话状态（t4/t6）。

## 依赖方向

- **可以依赖全部层**：domain、ports、adapters、ui、i18n。
- 是唯一允许同时 import adapters 与 ui 的层；UI 不得反向 import app。

## 约束

- `--version` 路径不得 import `gi`、adapters 或 ui（由 `tests/contract/test_gtk_independence.py` 强制）。
- 不在本层写业务校验；校验只存在于 domain/adapters。
