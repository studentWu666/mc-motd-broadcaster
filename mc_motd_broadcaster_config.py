#!/usr/bin/env python3

"""
Minecraft MOTD Broadcaster with Config File Support

This program broadcasts Minecraft server MOTD to the local LAN network
for servers that don't send UDP broadcasts by default.
Configurable via a JSON configuration file.

Based on the original project by minerz029:
https://bitbucket.org/minerz029/lan_broadcaster/

Original project copyright (C) 2013 minerz029
This modified version copyright (C) 2024

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import argparse
import socket
import threading
import time
import sys
import struct
import os
import json

__version__ = '1.1.0'

class MinecraftMOTDBroadcaster:
    """Broadcasts Minecraft server MOTD over LAN network."""
    
    # Minecraft LAN broadcast settings
    MULTICAST_ADDRESS = '224.0.2.60'
    BROADCAST_PORT = 4445
    BROADCAST_INTERVAL = 3  # seconds
    
    def __init__(self, motd, server_port):
        """Initialize the broadcaster.
        
        Args:
            motd (str): Server message of the day
            server_port (int): Server port
        """
        self.motd = motd.strip()
        self.server_port = server_port
        self._stop_event = threading.Event()
        self._stop_event.set()
        
        # Create UDP socket
        self.socket = socket.socket(type=socket.SOCK_DGRAM)
        
        # Create broadcast thread
        self.thread = threading.Thread(
            target=self._broadcast_loop,
            name="MOTDBroadcaster"
        )
    
    def _format_message(self):
        """Format the broadcast message according to Minecraft protocol.
        
        For Minecraft 1.7+, the format should be [MOTD]<motd>[/MOTD][AD]<port>[/AD]
        The client automatically uses the broadcast source IP as the server address.
        """
        # Format: [MOTD]Server Name[/MOTD][AD]Port[/AD]
        return f"[MOTD]{self.motd}[/MOTD][AD]{self.server_port}[/AD]"
    
    def _broadcast_message(self):
        """Send a single broadcast message."""
        message = self._format_message().encode()
        self.socket.sendto(
            message,
            (self.MULTICAST_ADDRESS, self.BROADCAST_PORT)
        )
    
    def _broadcast_loop(self):
        """Continuous broadcast loop."""
        try:
            while not self._stop_event.is_set():
                self._broadcast_message()
                time.sleep(self.BROADCAST_INTERVAL)
        except KeyboardInterrupt:
            pass
    
    def _get_server_motd(self, timeout=5):
        """Get the actual MOTD from the Minecraft server using the status protocol.
        
        This function is disabled since server address is no longer configured.
        
        Args:
            timeout (float): Connection timeout in seconds
            
        Returns:
            str: Always returns None since server address is not available
        """
        return None
    
    def start(self):
        """Start the broadcast loop.
        
        Raises:
            RuntimeError: If broadcaster is already running
        """
        if not self.is_running():
            self._stop_event.clear()
            self.thread = threading.Thread(
                target=self._broadcast_loop,
                name="MOTDBroadcaster"
            )
            self.thread.start()
        else:
            raise RuntimeError("Broadcaster is already running")
    
    def stop(self):
        """Stop the broadcast loop."""
        self._stop_event.set()
        if self.is_running():
            self.thread.join()
    
    def is_running(self):
        """Check if the broadcaster is running.
        
        Returns:
            bool: True if running, False otherwise
        """
        return self.thread.is_alive()
    
    def get_status(self):
        """Get current status information.
        
        Returns:
            str: Status message
        """
        status = "Running" if self.is_running() else "Stopped"
        return f"Minecraft MOTD Broadcaster {__version__}\n" \
               f"Status: {status}\n" \
               f"MOTD: {self.motd}\n" \
               f"Port: {self.server_port}\n" \
               f"Broadcast: {self.MULTICAST_ADDRESS}:{self.BROADCAST_PORT}\n" \
               f"Interval: {self.BROADCAST_INTERVAL}s"

def load_config(config_path):
    """Load configuration from a JSON file with multi-server support.
    Supports both explicit servers list and auto-generating servers from motd_count.
    
    Args:
        config_path (str): Path to the configuration file
        
    Returns:
        dict: Configuration dictionary with servers list
    """
    default_config = {
        "motd_count": 1,
        "motd": "A Minecraft Server",
        "base_port": 25565,
        "interval": 3.0,
        "auto_motd": False,
        "silent": False
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = json.load(f)
            
            # Merge with default config
            result = default_config.copy()
            result.update(user_config)
            
            # Generate servers list based on motd_count
            if "motd_count" in result:
                servers = []
                for i in range(result["motd_count"]):
                    port = result["base_port"] + i
                    server = {
                        "name": f"服务器 {i + 1}",
                        "motd": result["motd"],
                        "port": port,
                        "interval": result["interval"],
                        "auto_motd": result["auto_motd"]
                    }
                    servers.append(server)
                result["servers"] = servers
            
            return result
            
        except Exception as e:
            print(f"警告: 读取配置文件 {config_path} 失败: {e}")
            print("使用默认配置.")
            # 生成默认服务器列表
            default_config["servers"] = [{
                "name": "服务器 1",
                "motd": default_config["motd"],
                "port": default_config["base_port"],
                "interval": default_config["interval"],
                "auto_motd": default_config["auto_motd"]
            }]
            return default_config
    else:
        # 创建默认配置文件（motd_count格式）
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            print(f"已在 {config_path} 创建默认配置文件")
        except Exception as e:
            print(f"警告: 创建配置文件 {config_path} 失败: {e}")
        
        # 生成默认服务器列表
        default_config["servers"] = [{
            "name": "服务器 1",
            "motd": default_config["motd"],
            "port": default_config["base_port"],
            "interval": default_config["interval"],
            "auto_motd": default_config["auto_motd"]
        }]
        return default_config

def main():
    """主入口点，支持多服务器配置文件。"""
    parser = argparse.ArgumentParser(
        description="Minecraft MOTD 广播器 - 向局域网广播多个服务器信息（配置文件版）"
    )
    
    parser.add_argument(
        '--config', '-c',
        default='mc_motd_config.json',
        help="配置文件路径（默认：mc_motd_config.json）"
    )
    
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help="强制启动，不检查配置文件是否存在或是否已修改"
    )
    
    args = parser.parse_args()
    
    # 检查配置文件是否存在
    config_path = args.config
    if not os.path.exists(config_path):
        # 生成默认配置文件
        default_config = {
            "motd_count": 1,
            "motd": "A Minecraft Server",
            "base_port": 25565,
            "interval": 3.0,
            "auto_motd": False,
            "silent": False
        }
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            print(f"\n已生成默认配置文件: {config_path}")
            
            # 如果没有使用--force参数，提示用户修改配置文件
            if not args.force:
                print("\n请先修改配置文件，设置您的MOTD和端口号，然后重新启动程序。")
                print("\n配置文件内容：")
                print(json.dumps(default_config, indent=4, ensure_ascii=False))
                print("\n按任意键退出...")
                input()
                return
        except Exception as e:
            print(f"\n警告: 无法创建配置文件 {config_path}: {e}")
            print("使用默认配置启动...")
    
    # 从文件加载配置
    config = load_config(config_path)
    
    # 为每个服务器创建广播实例
    broadcasters = []
    
    for server in config['servers']:
        # 创建广播实例
        broadcaster = MinecraftMOTDBroadcaster(
            server['motd'],
            server['port']
        )
        
        # 如果指定了广播间隔，则设置
        if server['interval'] != 3.0:
            broadcaster.BROADCAST_INTERVAL = server['interval']
        
        # 保存服务器配置到广播实例
        broadcaster.server_config = server
        broadcasters.append(broadcaster)
    
    try:
        # 启动所有广播器
        for broadcaster in broadcasters:
            server = broadcaster.server_config
            
            # 如果配置了自动获取MOTD
            if server['auto_motd']:
                if not config['silent']:
                    print(f"\n尝试获取 {server['name']} 的实际MOTD...")
                    print(f"✗ {server['name']}: 自动获取MOTD功能已禁用，因为不再配置服务器地址")
            
            # 开始广播
            broadcaster.start()
        
        if not config['silent']:
            print("\n" + "="*60)
            print(f"Minecraft MOTD 广播器 {__version__} - 多服务器模式")
            print("="*60)
            for broadcaster in broadcasters:
                server = broadcaster.server_config
                print(f"\n{server['name']} 状态:")
                print(f"  MOTD: {broadcaster.motd}")
                print(f"  端口: {broadcaster.server_port}")
                print(f"  广播地址: {broadcaster.MULTICAST_ADDRESS}:{broadcaster.BROADCAST_PORT}")
                print(f"  广播间隔: {broadcaster.BROADCAST_INTERVAL}秒")
                print(f"  状态: 运行中")
            
            print("\n" + "="*60)
            print("正在向局域网广播Minecraft服务器信息...")
            print(f"服务器总数: {len(broadcasters)}")
            print("按 Ctrl+C 停止所有广播器。")
        
        # 保持程序运行
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        if not config['silent']:
            print("\n正在停止所有广播器...")
    
    finally:
        # 停止所有广播器
        for broadcaster in broadcasters:
            broadcaster.stop()
        
        if not config['silent']:
            print(f"所有 {len(broadcasters)} 个广播器已停止。")

if __name__ == "__main__":
    main()
