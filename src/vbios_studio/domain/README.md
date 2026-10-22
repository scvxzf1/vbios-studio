# `vbios_studio.domain` — 纯领域层

## 职责

- 冻结的 DTO：`DocumentSnapshot`、`FieldSnapshot`、`ImageSnapshot`、`SectionSnapshot`、`EditPreview`、`ManifestView`、`SaveResult`、`RomDiff`、`DeviceStatus`、`ApplyPreview`、`ApplyResult`。
- 风险：`RiskLevel`、`risk_rank()`、`max_risk()`、`risk_registry.py` 的逐字段 T0–T3 注册表与方向降级。
- ROM 结构：`rom.py` 的 PCIR/NPDS 镜像链扫描、逐镜像 8-bit 校验和、末字节平衡与纯字节编辑管线。
- 字段目录：`catalog.py` 把上游 descriptor 映射为 `FieldSnapshot`，并为上游未暴露的 canonical 字段追加 T0 只读占位；`document.py` 汇总为不可变 `DocumentSnapshot`。
- 生成物：`manifest.py` 组装 FR-3.2 manifest；`serialization.py` 输出 JSON 安全的字段目录。
- 结构化错误：`DomainError(code, message, hint, details)` 与错误码常量。

## 依赖方向

- **只依赖 Python 标准库**。
- 禁止 import `gi`、`nvidia_vbios`、`vbios_studio.adapters`、`vbios_studio.ui`、`vbios_studio.app`、`vbios_studio.ports`、`subprocess`、`winreg`。
- 被 `ports`、`adapters`、`ui`、`app` 依赖；本包不反向依赖任何业务层。

## 约束

- DTO 全部 `frozen=True`，UI 不得就地修改。
- 新增字段必须有默认值，不得重命名既有字段（见 `docs/requirements.md` 附录 A）。
- 不读文件、不写注册表、不启动子进程、不做 i18n 副作用；ROM 解析只接收 `bytes`。
