# `vbios_studio.i18n` — 国际化

## 职责

- 语言代码归一化：`zh_*` → `zh_CN`，`en_*` → `en`，默认 `en`。
- 从 `LC_ALL` / `LC_MESSAGES` / `LANG` 推断界面语言。
- 承载 gettext 目录（t4 起加入 `locale/<lang>/LC_MESSAGES/*.po|*.mo`）。

## 依赖方向

- **仅依赖 Python 标准库**。
- 禁止 import `gi`、`nvidia_vbios`、`vbios_studio.adapters`、`vbios_studio.ui`、`vbios_studio.app`、`vbios_studio.ports`。
- 由 `ui` / `app` 使用；`domain` / `ports` 不使用。

## 约束

- 用户可见文案不得硬编码；所有 msgid 必须同时存在于 `en` 与 `zh_CN`（t7 检查）。
