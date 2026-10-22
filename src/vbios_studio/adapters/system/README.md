# `vbios_studio.adapters.system` — 系统适配器子包

## 职责

- Windows 注册表 override、Linux loader 探测、nvflash 硬守卫。
- 与 `adapters/upstream.py` 严格分离：系统权限相关代码不得混入上游桥接。

## 依赖方向

- 依赖 `vbios_studio.domain` / `vbios_studio.ports`；不依赖 UI/app。
- 子进程调用必须通过可注入的 runner，列表参数、`shell=False`。

## 安全边界

修改后镜像永远不得进入 nvflash 写通道；详见 `docs/risk-model.md` §6。
