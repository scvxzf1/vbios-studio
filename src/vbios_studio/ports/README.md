# `vbios_studio.ports` — 抽象接口层

## 职责

- 定义 UI 与系统能力之间的 `Protocol`：
  - `EditorPort`：`open` / `stage` / `preview` / `save_as` / `reset`
  - `DiffPort`：`diff_against`
  - `ProfilePort`：`export_changes` / `apply_profile`
  - `ApplyPort`：`device_status` / `dry_run` / `execute` / `restore`
- 只声明契约，不包含实现、不读文件、不写注册表、不启动子进程。

## 依赖方向

- 仅依赖 `vbios_studio.domain`。
- 禁止 import `gi`、`nvidia_vbios`、`vbios_studio.adapters`、`vbios_studio.ui`、`vbios_studio.app`、`subprocess`、`winreg`。
- 由 `adapters` 实现，由 `ui` / `app` 消费。

## 约束

- 方法签名与 DTO 见 `docs/requirements.md` 附录 A；字段名变更需先更新契约。
- `stage()` 返回 domain 校验后的 `EditPreview`；UI 只渲染。
- 所有写操作先 `dry_run()`；`execute()` 必须有确认票据（由 app 层维护）。
