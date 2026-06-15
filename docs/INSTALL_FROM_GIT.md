# 从 GitHub 下载与使用

## 1. 文档用途

本文说明如何在另一台 Windows 电脑上从 GitHub 下载项目、安装依赖、运行测试、完成校准，以及后续更新代码。

项目仓库：

```text
https://github.com/ShyNodes1208/codex-anhei4
```

## 2. 使用前须知

- 项目当前是屏幕视觉自动化原型。
- 游戏自动化可能违反服务条款并导致账号处罚。
- 新电脑必须重新校准分辨率、UI 区域和操作坐标。
- 默认配置为 `dry_run`，不会发送键盘或鼠标输入。
- 未完成实机校准前不要切换到 `native`。

## 3. 安装 Git

先检查 Git：

```powershell
git --version
```

如果能显示版本，例如：

```text
git version 2.51.0.windows.2
```

说明已经安装。

如果提示找不到 `git`，从 Git for Windows 官网下载安装：

```text
https://git-scm.com/download/win
```

安装完成后关闭并重新打开 PowerShell。

## 4. 安装 uv

先检查：

```powershell
uv --version
```

如果没有安装，可以使用官方 PowerShell 安装命令：

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

该命令会下载并执行官方安装脚本。执行前应确认网络环境和脚本来源。

安装完成后关闭并重新打开 PowerShell，然后再次检查：

```powershell
uv --version
```

也可以参考官方文档：

```text
https://docs.astral.sh/uv/getting-started/installation/
```

## 5. 选择代码目录

以下示例将项目放到：

```text
E:\code\codex-anhei4
```

如果电脑没有 `E:` 盘，可以换成：

```text
C:\code\codex-anhei4
```

创建并进入父目录：

```powershell
New-Item -ItemType Directory -Force E:\code
Set-Location E:\code
```

## 6. 克隆代码

执行：

```powershell
git clone https://github.com/ShyNodes1208/codex-anhei4.git
```

进入项目目录：

```powershell
cd E:\code\codex-anhei4
```

检查仓库状态：

```powershell
git status
```

正常情况下会显示当前位于 `main` 分支，并且工作区干净。

## 7. 安装项目依赖

在项目目录执行：

```powershell
uv sync
```

该命令会：

- 根据 `pyproject.toml` 和 `uv.lock` 安装依赖。
- 在项目目录创建 `.venv` 虚拟环境。
- 安装项目命令 `d4-assistant`。

依赖安装完成后，可检查虚拟环境：

```powershell
Test-Path .\.venv\Scripts\python.exe
```

返回 `True` 表示虚拟环境已创建。

## 8. 运行测试

执行：

```powershell
.\.venv\Scripts\pytest.exe -q
```

当前预期结果：

```text
14 passed
```

如果测试失败，不要进入原生输入模式。保存完整错误输出后再处理。

## 9. 查看命令帮助

执行：

```powershell
.\.venv\Scripts\d4-assistant.exe --help
```

当前支持：

```text
run
calibrate
```

## 10. 检查默认安全模式

打开：

```text
config\default.yaml
```

确认：

```yaml
runtime:
  mode: dry_run
```

`dry_run` 只记录动作，不发送输入。

## 11. 准备实机资料

在有游戏的电脑上，先阅读：

```text
docs\REQUIRED_INFORMATION.md
```

按文档采集：

- 游戏分辨率和 UI 缩放。
- 召唤装置截图。
- Boss 房角落截图。
- Boss 战斗和清场截图。
- 宝箱和掉落截图。
- 空、半满、全满背包截图。
- 城镇、仓库和返回传送门截图。
- 各阶段实际耗时。

建议将截图放入：

```text
samples\
```

截图不要裁剪或缩放。

## 12. 运行校准

确保游戏使用固定分辨率和无边框窗口模式。

在需要校准的游戏画面中执行：

```powershell
.\.venv\Scripts\d4-assistant.exe calibrate
```

输出：

```text
runtime\calibration.jpg
```

检查图中的：

- 生命区域。
- 敌人区域。
- 掉落区域。
- 背包区域。
- 召唤装置标记。
- 房间角落标记。
- 宝箱标记。
- 仓库标记。
- 返回传送门标记。

召唤房和城镇不在同一个场景，需要分别截图和校准。

## 13. 修改配置

主配置：

```text
config\default.yaml
```

屠夫配置：

```text
config\bosses\butcher.yaml
```

修改配置前建议备份：

```powershell
Copy-Item config\default.yaml config\default.yaml.bak
Copy-Item config\bosses\butcher.yaml config\bosses\butcher.yaml.bak
```

重点需要调整：

- 屏幕检测区域。
- 召唤装置坐标。
- Boss 房角落坐标。
- 宝箱坐标。
- 仓库坐标。
- 返回传送门坐标。
- 移动和加载等待时间。
- 技能冷却时间。
- 背包占用检测阈值。

## 14. 观察模式运行

在项目目录执行：

```powershell
.\.venv\Scripts\d4-assistant.exe --verbose run
```

观察：

- 日志中的生命值是否合理。
- 有怪时 `enemy=True`。
- 无怪时 `enemy=False`。
- 有物品时 `loot=True`。
- 背包占用率是否接近实际值。
- 状态切换是否符合预期。

状态截图保存在：

```text
runtime\
```

默认 `dry_run` 下动作会被安全地阻止，因此不会完整执行实机状态循环。

## 15. 原生输入模式

只有完成所有校准并逐步验证后，才能修改：

```yaml
runtime:
  mode: native
```

运行：

```powershell
.\.venv\Scripts\d4-assistant.exe --verbose run
```

快捷键：

| 快捷键 | 功能 |
|---|---|
| `F8` | 启用输入并开始；再次按下则关闭输入并暂停 |
| `F7` | 重新开始屠夫召唤流程 |
| `F9` | 暂停或恢复 |
| `F12` | 紧急停止 |

首次原生输入测试应只验证单个动作，不要直接长时间循环。

## 16. 鼠标宏模式

如果使用鼠标宏：

```yaml
runtime:
  mode: macro_hotkey

barbarian:
  macro_hotkeys:
    combat_rotation: "f6"
```

宏应满足：

- 按一次只执行一轮。
- 不使用无限循环。
- 不负责移动、回城或仓库存放。
- 可以通过停止脚本终止后续触发。

## 17. 后续更新代码

进入项目目录：

```powershell
cd E:\code\codex-anhei4
```

查看本地修改：

```powershell
git status
```

如果工作区干净，执行：

```powershell
git pull
uv sync
```

然后重新运行测试：

```powershell
.\.venv\Scripts\pytest.exe -q
```

## 18. 保留本地配置

如果直接修改了仓库中的 YAML，`git pull` 可能与远端更新冲突。

更新前先备份：

```powershell
Copy-Item config\default.yaml config\default.local.yaml
Copy-Item config\bosses\butcher.yaml config\bosses\butcher.local.yaml
```

拉取更新：

```powershell
git pull
```

再手工将本地坐标和阈值合并回新配置。

不要使用以下命令强行覆盖本地配置：

```powershell
git reset --hard
```

除非明确知道它会删除所有未提交修改。

## 19. 提交自己的配置修改

查看修改：

```powershell
git status
git diff
```

提交：

```powershell
git add config docs src tests
git commit -m "chore: calibrate local game settings"
git push
```

如果仓库只有只读权限，推送会失败，需要使用有写权限的 GitHub 账号或创建自己的 Fork。

## 20. 常见问题

### 20.1 找不到 git

```text
git : 无法将“git”识别为命令
```

处理：

- 安装 Git for Windows。
- 重新打开 PowerShell。
- 执行 `git --version`。

### 20.2 找不到 uv

```text
uv : 无法将“uv”识别为命令
```

处理：

- 安装 uv。
- 重新打开 PowerShell。
- 执行 `uv --version`。

### 20.3 uv 缓存权限错误

如果 `uv run` 报缓存目录权限错误，直接使用：

```powershell
.\.venv\Scripts\d4-assistant.exe
.\.venv\Scripts\pytest.exe
```

### 20.4 PowerShell 禁止脚本

本项目主要运行 `.exe` 入口，通常不需要修改 PowerShell 永久执行策略。

安装工具时如需临时绕过，应只对单次进程使用：

```powershell
powershell -ExecutionPolicy Bypass -File .\script.ps1
```

不要随意修改全局执行策略。

### 20.5 git safe.directory

如果出现：

```text
detected dubious ownership in repository
```

确认目录可信后，为精确目录添加例外：

```powershell
git config --global --add safe.directory E:/code/codex-anhei4
```

不要将所有目录通配加入安全列表。

### 20.6 GitHub 仓库无法访问

先检查：

```powershell
git ls-remote https://github.com/ShyNodes1208/codex-anhei4.git HEAD
```

如果出现 TLS、代理或网络错误：

- 检查浏览器是否能访问 GitHub。
- 检查公司代理、防火墙或 VPN。
- 稍后重试。

### 20.7 测试通过但游戏中不能运行

单元测试只验证代码逻辑，不代表视觉阈值和坐标适用于实际游戏。

必须继续检查：

- 分辨率。
- UI 缩放。
- 颜色和语言。
- 召唤器坐标。
- Boss 房角落。
- 宝箱位置。
- 仓库位置。
- 背包占用阈值。

## 21. 完整命令速查

首次安装：

```powershell
cd E:\code
git clone https://github.com/ShyNodes1208/codex-anhei4.git
cd codex-anhei4
uv sync
.\.venv\Scripts\pytest.exe -q
.\.venv\Scripts\d4-assistant.exe --help
```

校准：

```powershell
.\.venv\Scripts\d4-assistant.exe calibrate
```

观察模式：

```powershell
.\.venv\Scripts\d4-assistant.exe --verbose run
```

更新：

```powershell
cd E:\code\codex-anhei4
git status
git pull
uv sync
.\.venv\Scripts\pytest.exe -q
```

## 22. 相关文档

- `docs/FUNCTIONS.md`：已实现功能和技术结构。
- `docs/USAGE.md`：项目配置、校准和使用说明。
- `docs/REQUIRED_INFORMATION.md`：需要采集的实机资料。

