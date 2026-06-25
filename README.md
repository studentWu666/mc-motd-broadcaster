# mc-motd-broadcaster

一个简单的 Minecraft 服务端 MOTD 转发工具，向局域网发送 UDP 广播，让客户端能在局域网游戏列表中看到服务器。

本质是从指定端口广播 motd，**不需要真的有服务器即可广播**。

## 功能

- ✅ **Fluent Design GUI** — 基于 PyQt5 + qfluentwidgets，Win11 风格暗色界面
- ✅ **MOTD 编辑器** — 16 种颜色 / 6 种格式 / 实时预览，类似 motd.gg
- ✅ **多服务器同时广播** — 一次启动广播 N 个端口
- ✅ **配置文件管理** — JSON 配置，自动生成默认配置
- ✅ **命令行模式** — 无 GUI 环境也可运行
- ✅ **单端口简化模式** — Minecraft 1.6+ 自动使用发送端 IP

## 截图

```
┌─── 导航 ───┐  ┌─────────────────────────────────────┐
│  📤 广播    │  │  MOTD 编辑器                        │
│  ✏️ MOTD 编辑│  │  [黑][深蓝][深绿]…  [B][I][U][S]    │
│  ─────────  │  │  ┌──────────┐  ┌──────────────────┐ │
│  ℹ️ 关于     │  │  │ §aHello  │  │ Hello (绿色)      │ │
│             │  │  │ §6§lWorld │  │ World (金色加粗)  │ │
│             │  │  └──────────┘  └──────────────────┘ │
└─────────────┘  └─────────────────────────────────────┘
```

## 快速开始

```bash
# 克隆
git clone https://github.com/studentWu666/mc-motd-broadcaster.git
cd mc-motd-broadcaster

# 安装依赖
pip install PyQt-Fluent-Widgets

# 运行 GUI
py -3.11 mc_motd_broadcaster_gui.py
```

首次运行会自动生成 `mc_motd_config.json`，修改后再次运行即可开始广播。

### 命令行模式（无 GUI）

```bash
# 使用配置文件
python mc_motd_broadcaster_config.py

# 强制启动
python mc_motd_broadcaster_config.py --force

# 指定配置文件
python mc_motd_broadcaster_config.py --config your_config.json
```

## 配置文件

```json
{
    "motd_count": 1,
    "motd": "A Minecraft Server",
    "base_port": 25565,
    "interval": 3.0,
    "auto_motd": false,
    "silent": false
}
```

| 参数 | 说明 |
|------|------|
| `motd_count` | 要广播的服务器数量 |
| `motd` | 服务器 MOTD（支持 § 颜色代码） |
| `base_port` | 基础端口，自动递增 |
| `interval` | 广播间隔（秒） |
| `auto_motd` | 自动获取 MOTD（已禁用） |
| `silent` | 静默运行 |

## 项目结构

```
mc-motd-broadcaster/
├── mc_motd_broadcaster_gui.py   # Fluent Design GUI（含 MOTD 编辑器）
├── mc_motd_broadcaster_config.py # 广播核心 + 命令行入口
├── config.example.json           # 配置示例
├── mc_motd_config.json           # 实际配置（git 忽略）
├── README.md
└── LICENSE                       # GNU GPL v3
```

## 许可证

本项目基于 [minerz029/lan_broadcaster](https://bitbucket.org/minerz029/lan_broadcaster/) 开发，使用 GNU GPL v3 许可证。
