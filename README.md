# mc-motd-broadcaster

一个简单的Minecraft服务端MOTD转发软件，用于向局域网发送UDP广播，使客户端能在局域网游戏列表中看到服务器。

## 提示
本质上是从指定端口广播motd，所以不需要真的有服务器即可广播
可以使用其他机器运行，请自行设置端口转发（或者其他乱七八糟的）
除了README里的“提示”，其他都是AI写的！！！

## 功能特性

- ✅ 支持多服务器同时广播
- ✅ 简洁的配置文件管理
- ✅ 自动生成默认配置
- ✅ 支持自定义MOTD和端口
- ✅ 中文界面，操作友好
- ✅ 单文件可执行，无需Python环境（windows）


### 直接运行

1. 双击 `mc_motd_broadcaster.exe` 运行
2. 首次运行会生成默认配置文件 `mc_motd_config.json`
3. 修改配置文件后重新运行

### 命令行运行

```bash
# 直接运行（生成/使用配置文件）
python mc_motd_broadcaster_config.py

# 强制运行，不检查配置文件
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

### 参数说明

| 参数名 | 说明 |
|--------|------|
| `motd_count` | 要广播的服务器数量 |
| `motd` | 服务器MOTD |
| `base_port` | 基础端口，自动递增 |
| `interval` | 广播间隔（秒） |
| `auto_motd` | 自动获取MOTD（已禁用） |
| `silent` | 静默运行 |

## 许可证

本项目基于 [minerz029/lan_broadcaster](https://bitbucket.org/minerz029/lan_broadcaster/) 开发，使用 GNU GPL v3 许可证。

## 更新日志
100%AI制作，后续不需要也不会更新awa

### v1.1.0
- 移除服务器地址配置，简化使用
- 添加友好的配置文件生成提示
- 支持 `--force` 参数强制启动
- 默认MOTD改为 "A Minecraft Server"
- 优化中文界面
