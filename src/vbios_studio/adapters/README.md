# `vbios_studio.adapters` — 适配器层

## 职责

- `upstream.py`：桥接 vendored `nvidia_vbios`（ROM 解析、字段目录、编辑、normalize）。唯一允许 import 上游的层。
- `system/windows_registry.py`：Windows 注册表 override（`vbios` / `EnableGpuFirmware` / `VixLoaderPreviousEnableGpuFirmware`），支持 dry-run、回读、unload。
- `system/linux_loader.py`：探测外部 `nvidia-linux-vbios-vix-loader`，生成 payload 与指引，不自动提权。
- `system/nvflash.py`：刷写守卫；修改后镜像一律拒绝，原厂镜像也须逐项校验。

## 依赖方向

- 依赖 `vbios_studio.ports` 与 `vbios_studio.domain`；`upstream.py` 允许依赖 `nvidia_vbios`。
- **禁止** import `vbios_studio.ui`、`vbios_studio.app`。
- 所有系统调用必须列表参数、`shell=False`，经 ports 注入，禁止 `os.system`。

## 当前状态

仓库骨架阶段只建立依赖边界；具体实现分别由 upstream 桥接与 registry/loader/nvflash 适配器完成。
