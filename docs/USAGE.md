# 使用说明

## 1. 使用前须知

本项目是开发和实验用途的屏幕视觉自动化原型。游戏自动化可能违反服务条款，并可能导致账号处罚。

首次使用必须保持：

```yaml
runtime:
  mode: dry_run
```

在没有实机截图、坐标校准和人工观察验证前，不要切换到 `native`。

## 2. 环境要求

- Windows 10 或 Windows 11
- Python 3.11 及以上
- `uv`
- 《暗黑破坏神 IV》使用稳定分辨率
- 建议使用无边框窗口模式
- 游戏窗口标题包含 `Diablo IV`

## 3. 安装

打开 PowerShell：

```powershell
cd E:\code\codex\anhei4
uv sync
```

如果 `uv run` 因缓存目录权限失败，可直接使用项目虚拟环境：

```powershell
.\.venv\Scripts\d4-assistant.exe --help
```

运行测试：

```powershell
.\.venv\Scripts\pytest.exe -q
```

## 4. 准备截图

保持游戏分辨率、窗口模式和 UI 缩放不变，将完整屏幕截图放入：

```text
E:\code\codex\anhei4\samples
```

建议文件：

```text
summon-device.png
room-corner.png
boss-fighting.png
boss-dead-chest.png
inventory-empty.png
inventory-half.png
inventory-full.png
town-arrival.png
town-stash.png
stash-open.png
return-portal.png
```

截图不要裁剪。

## 5. 运行校准工具

在游戏处于目标画面时执行：

```powershell
.\.venv\Scripts\d4-assistant.exe calibrate
```

输出文件：

```text
runtime\calibration.jpg
```

校准图包含：

- 生命值检测区域
- 周围敌人检测区域
- 掉落标签检测区域
- 背包界面检测区域
- 背包格子区域
- 屠夫召唤装置位置
- Boss 房角落方向
- Boss 宝箱位置
- 城镇仓库位置
- 返回传送门位置

注意：召唤器、Boss 房和城镇不在同一场景，一张校准图无法同时验证所有坐标。应分别在对应场景截图，并逐项更新配置。

## 6. 校准坐标

### 6.1 归一化坐标

点位格式：

```yaml
device_position: [0.50, 0.52]
```

区域格式：

```yaml
health_region: [0.028, 0.790, 0.115, 0.965]
```

坐标计算：

```text
x = 像素横坐标 / 屏幕宽度
y = 像素纵坐标 / 屏幕高度
```

例如，在 `1920×1080` 屏幕中，像素点 `(960, 540)` 为：

```yaml
[0.5, 0.5]
```

### 6.2 需要校准的 Boss 点位

编辑 `config/bosses/butcher.yaml`：

```yaml
summon:
  device_position: [召唤装置]
  room_corner_position: [房间角落方向]

loot:
  chest_position: [宝箱位置]
```

### 6.3 需要校准的城镇点位

编辑 `config/default.yaml`：

```yaml
inventory:
  stash_world_position: [仓库方向]
  return_portal_position: [返回传送门方向]
```

这些坐标目前表示屏幕点击方向，不是世界地图坐标。人物起点、相机位置或障碍变化都会影响结果。

## 7. 校准视觉区域

编辑 `config/default.yaml` 中的 `vision`：

```yaml
vision:
  health_region: [...]
  inventory_region: [...]
  inventory_slots_region: [...]
  nearby_enemy_region: [...]
  loot_region: [...]
```

需要重点准备三类背包截图：

- 空背包
- 半满背包
- 全满背包

用于调整：

```yaml
inventory_slot_edge_ratio: 0.055
full_ratio: 1.0
empty_ratio: 0.05
```

## 8. 配置职业技能

当前配置：

```yaml
barbarian:
  opener:
    name: call_of_the_ancients
    key: "1"

  whirlwind:
    toggle_key: "right"
    restart_delay: 0.25

  cooldown_skills:
    - {name: challenging_shout, key: "2", cooldown: 25.0, priority: 90}
    - {name: war_cry, key: "3", cooldown: 25.0, priority: 85}
    - {name: rallying_cry, key: "4", cooldown: 25.0, priority: 80}
    - {name: iron_skin, key: "5", cooldown: 14.0, priority: 95}
```

数字越大的 `priority` 越先释放。

目前冷却时间为估算值，应按实际装备、技能等级和减 CD 属性修改。

## 9. 调整移动和等待时间

Boss 流程配置位于 `config/bosses/butcher.yaml`：

```yaml
summon:
  move_to_device_seconds: 2.0
  post_interact_wait_seconds: 1.5
  move_to_corner_seconds: 2.5
  corner_wait_seconds: 3.0

loot:
  move_to_chest_seconds: 2.0
  chest_open_wait_seconds: 1.5
```

城镇流程配置位于 `config/default.yaml`：

```yaml
inventory:
  town_load_seconds: 8.0
  move_to_stash_seconds: 4.0
  stash_open_wait_seconds: 2.0
  move_to_portal_seconds: 3.0
  return_load_seconds: 8.0
```

所有时间应留有余量。加载不稳定时优先增加等待时间。

## 10. 观察模式

启动程序：

```powershell
.\.venv\Scripts\d4-assistant.exe --verbose run
```

默认 `dry_run` 不发送输入。此模式适合：

- 检查生命值估算。
- 检查敌人检测。
- 检查掉落检测。
- 检查背包占用率。
- 检查状态截图和日志。

由于 `dry_run` 中动作被判定为未执行，状态机不会假装完成完整流程。这是安全设计。

## 11. 输入模式

### 11.1 原生输入

完成校准后：

```yaml
runtime:
  mode: native
```

脚本直接执行技能、点击和交互。

### 11.2 鼠标宏

```yaml
runtime:
  mode: macro_hotkey
```

战斗时脚本触发：

```yaml
barbarian:
  macro_hotkeys:
    combat_rotation: "f6"
```

鼠标宏应设置为每次触发只运行一轮，避免使用无法被脚本停止的无限循环宏。

## 12. 快捷键

| 快捷键 | 功能 |
|---|---|
| `F8` | 启用输入并开始；再次按下则关闭输入并暂停 |
| `F7` | 请求重新开始屠夫召唤流程 |
| `F9` | 暂停或恢复；输入被关闭时必须先按 `F8` |
| `F12` | 紧急停止，必须重启程序才能恢复 |

## 13. 仓库设置

默认转移方式：

```yaml
inventory:
  transfer_modifier: "shift"
  transfer_button: "left"
```

即 `Shift+左键`。

必须确认游戏中这一组合确实能将物品从背包移动到仓库。如果快捷键不同，应先修改配置和输入实现，再进行测试。

当前脚本不理解：

- 收藏标记
- 锁定物品
- 物品价值
- 词缀
- 装备升级潜力
- 仓库是否已满

建议使用专门的测试角色和空仓库页。

## 14. 日志和截图

开启详细日志：

```powershell
.\.venv\Scripts\d4-assistant.exe --verbose run
```

状态切换截图保存在：

```text
runtime\
```

文件名包含时间、循环次数和状态名称，例如：

```text
20260615-140000-c3-COMBAT.jpg
```

## 15. 常见暂停原因

| 日志 | 原因 |
|---|---|
| `Game window lost focus` | 游戏不是前台窗口 |
| `Boss was never detected` | Boss 未出现或敌人识别失败 |
| `Enemy detected during chest looting` | 拾取阶段仍检测到怪物 |
| `Loot remains after maximum pickup attempts` | 物品未捡完或掉落误判 |
| `Inventory did not open` | 背包界面识别失败 |
| `Stash did not open` | 仓库界面识别失败 |
| `No inventory items were transferred` | 未识别到物品或输入被阻止 |
| `Inventory is not empty after stash transfer` | 仓库满、快捷键错误或识别错误 |
| `Combat input was blocked` | 窗口失焦或安全门关闭 |

出现暂停后，先查看 `runtime/` 中对应状态截图，不要直接反复按 `F8`。

## 16. 推荐实机验证顺序

1. 仅验证截图和校准图。
2. 验证生命、敌人和掉落识别。
3. 验证空包、半满、满包占用率。
4. 在安全区域验证单次鼠标移动。
5. 验证单次 `F` 交互。
6. 验证旋风斩开启和关闭。
7. 验证单次 Boss 召唤，不启用仓库。
8. 验证单次 Boss 战和宝箱拾取。
9. 验证单次回城。
10. 使用测试物品验证仓库存放。
11. 最后才测试多轮循环。

不要跳过上述阶段直接进行长时间运行。

