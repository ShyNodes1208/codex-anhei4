# D4 Barbarian Screen Assistant

面向《暗黑破坏神 IV》溶解旋风斩野蛮人的 Windows 屏幕视觉自动化原型。

项目通过屏幕截图判断状态，并使用普通键鼠输入。它不读取游戏内存、不注入进程，也不包含反作弊绕过。

自动化可能违反游戏服务条款并导致账号处罚。当前版本必须先完成实机截图和坐标校准。

## 文档

- [功能实现说明](docs/FUNCTIONS.md)
- [使用说明](docs/USAGE.md)
- [从 GitHub 下载与使用](docs/INSTALL_FROM_GIT.md)
- [实机信息提供清单](docs/REQUIRED_INFORMATION.md)

## 快速验证

```powershell
cd E:\code\codex\anhei4
uv sync
.\.venv\Scripts\pytest.exe -q
.\.venv\Scripts\d4-assistant.exe --help
```

默认配置为 `dry_run`，不会发送键鼠输入。
