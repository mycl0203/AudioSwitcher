# -*- coding: utf-8 -*-
"""
数据模型模块
定义项目中使用的所有数据结构
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class AudioDevice:
    """音频设备数据类"""
    name: str
    device_id: str
    direction: str  # "Render" 或 "Capture"
    
    def __str__(self) -> str:
        return f"{self.name} ({self.direction})"


@dataclass
class DeviceGroup:
    """设备组数据类"""
    display_name: str
    output_device_name: str
    output_device_id: str
    input_device_name: str
    input_device_id: str
    hotkey: str = ""
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DeviceGroup':
        """从字典创建设备组"""
        # 兼容新旧配置字段名
        out_id_key = "输出设备ID" if "输出设备ID" in data else "输出设备"
        in_id_key = "输入设备ID" if "输入设备ID" in data else "输入设备"
        
        return cls(
            display_name=data.get("显示名", ""),
            output_device_name=data.get("输出设备名", ""),
            output_device_id=str(data.get(out_id_key, "")).strip().lower(),
            input_device_name=data.get("输入设备名", ""),
            input_device_id=str(data.get(in_id_key, "")).strip().lower(),
            hotkey=data.get("快捷键", "").strip().lower()
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "显示名": self.display_name,
            "输出设备名": self.output_device_name,
            "输出设备ID": self.output_device_id,
            "输入设备名": self.input_device_name,
            "输入设备ID": self.input_device_id,
            "快捷键": self.hotkey
        }


@dataclass
class AppConfig:
    """应用配置数据类"""
    regen_config: bool = False
    enable_tray: bool = False
    enable_hotkey: bool = True
    hotkey_cycle: str = "ctrl+alt+right"
    hotkey_mute: str = "ctrl+alt+m"
    enable_gui: bool = False
    enable_notification: bool = True
    device_groups: List[DeviceGroup] = field(default_factory=list)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AppConfig':
        """从字典创建配置"""
        groups_data = data.get("设备组", [])
        groups = []
        for g_data in groups_data:
            try:
                group = DeviceGroup.from_dict(g_data)
                if group.display_name and group.output_device_id and group.input_device_id:
                    groups.append(group)
            except Exception:
                continue
        
        return cls(
            regen_config=data.get("regen_config", False),
            enable_tray=data.get("enable_tray", False),
            enable_hotkey=data.get("enable_hotkey", True),
            hotkey_cycle=str(data.get("hotkey_cycle", "ctrl+alt+right")).strip().lower(),
            hotkey_mute=str(data.get("hotkey_mute", "ctrl+alt+m")).strip().lower(),
            enable_gui=data.get("enable_gui", False),
            enable_notification=data.get("enable_notification", True),
            device_groups=groups
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "===== 使用必读 =====": "",
            "1.配置说明": "优先用Item ID，永久稳定",
            "2.后台开关": "默认关闭，不占资源；改为true开启常驻",
            "3.操作说明": "所有配置都可以在UI界面完成，无需手动编辑JSON",
            "4.刷新设备": "修改 regen_config 为 true，运行脚本自动更新CSV",
            "regen_config": self.regen_config,
            "enable_tray": self.enable_tray,
            "enable_hotkey": self.enable_hotkey,
            "hotkey_cycle": self.hotkey_cycle,
            "hotkey_mute": self.hotkey_mute,
            "enable_gui": self.enable_gui,
            "enable_notification": self.enable_notification,
            "设备组": [g.to_dict() for g in self.device_groups]
        }
