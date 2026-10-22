# NOTICE

VBIOS Studio. Copyright (C) 2026 VBIOS Studio contributors.

本文档汇总本项目的版权归属、上游来源、商标与第三方参考。项目整体以
GNU General Public License v3.0 or later（GPL-3.0-or-later）发布，完整许可证
文本见仓库根目录的 [`LICENSE`](LICENSE)。

## 上游来源

本项目基于以下两个 Panchovix 项目的代码与协议实现：

| 上游项目 | 仓库 | 当前 pin | 许可证 | 使用方式 |
| --- | --- | --- | --- | --- |
| NVIDIA VBIOS Vix Editor | <https://github.com/Panchovix/nvidia-vbios-vix-editor> | `1f8ee665bd175bd9ede367e6d15308f837bd987b`（v0.1.28） | GPL-3.0 | `src/nvidia_vbios/` 为逐字节只读镜像；本项目的 domain/adapters 通过公开 API 桥接 |
| NVIDIA Windows VBIOS Vix Loader | <https://github.com/Panchovix/nvidia-windows-vbios-vix-loader> | `ec7bdfe317d3a52de160d17d2bb80ff20813596e`（v0.3.1-6） | GPL-3.0 | 注册表 override 协议参考；不直接 import、不 vendored |

上游作者：panchovix。上游代码的版权归其原作者所有；本项目对上游代码的
再分发遵循 GPL-3.0-or-later。上游同步流程与 pin 校验命令见
[`UPSTREAM.md`](UPSTREAM.md)。

## 非 NVIDIA 官方项目

本项目**不是** NVIDIA Corporation 的官方项目，未获 NVIDIA 认可、赞助或背书。
NVIDIA、GeForce、NVIDIA VBIOS 等名称与标识是 NVIDIA Corporation 的商标。
文中出现的其他产品名称可能是其各自所有者的商标。

## 不包含 NVIDIA 固件

本仓库不包含任何 NVIDIA VBIOS、固件、驱动、内核模块或安装程序。测试使用的
ROM 全部由 `tests/core/rom_fixtures.py` 在运行时合成，不含真实硬件数据。
发布产物也不打包 NVIDIA 固件；用户提供的 ROM 不会被上传。

## NVIDIA 格式参考资料

本仓库不包含任何 NVIDIA 源文件。以下 NVIDIA 公开资料仅作为数据布局参考：

- 功耗、供电轨与 VFE 表的字段位置参考 NVIDIA nvgpu `bios.h` 结构定义（MIT）：
  <https://github.com/OE4T/linux-nvgpu/blob/patches-rel-36/drivers/gpu/nvgpu/include/nvgpu/bios.h>，
  对应实现位于 `src/nvidia_vbios/rom/tables.py`。
- BIT 指针与 token 结构参考 NVIDIA BIOS Information Table 规范：
  <https://nvidia.github.io/open-gpu-doc/BIOS-Information-Table/BIOS-Information-Table.html>。
- `src/nvidia_vbios/families.py` 的 PCI 设备到架构映射参考 NVIDIA open GPU
  kernel modules 的支持列表：
  <https://github.com/NVIDIA/open-gpu-kernel-modules/blob/615.71.09/README.md>；
  `EDITOR_ONLY` 条目（10de:2501）来自 PCI ID Repository（pci.ids）。

## 运行时与构建依赖

- Linux：PyGObject 与 GTK 4 由发行版软件包提供（LGPL-2.1-or-later），本项目
  不静态链接、不修改它们；分发 tar.gz 只包含本项目 Python 代码与启动器。
- Windows：单文件 exe 由 Nuitka 构建，内含 MSYS2 UCRT64 提供的 GTK 4 /
  PyGObject 运行时（LGPL-2.1-or-later）及各自依赖。对应许可证文本随构建工程的
  第三方声明流程提供；GTK/PyGObject 以可替换的独立文件形式解包。
- 开发与 CI 依赖（pytest、ruff、mypy、import-linter、PyYAML）均为各自作者的
  开源软件，仅用于开发与测试，不进入运行时分发包。

## 致谢

感谢 @pantsoftime（overclock.net）在 GB202 VBIOS 编辑与 `vbios_override`
方向的早期工作；感谢 Panchovix 维护的两个上游项目。
