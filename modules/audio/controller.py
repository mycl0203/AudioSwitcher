# -*- coding: utf-8 -*-
"""
音频设备控制器模块
负责音频设备的切换和麦克风静音控制
"""

import subprocess
from typing import Optional, Callable
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
from ..core.paths import path_manager
from ..core.models import DeviceGroup


class AudioController:
    """音频设备控制器"""
    
    def __init__(self):
        pass
    
    def set_default_device(self, device_id: str) -> None:
        """
        设置默认音频设备
        
        Args:
            device_id: 设备ID
        """
        try:
            subprocess.run(
                [path_manager.sv_exe, "/s", "/SetDefault", device_id, "all"],
                creationflags=0x08000000,
                check=True
            )
        except Exception as e:
            raise RuntimeError(f"设置默认设备失败: {e}")
    
    def switch_to_group(self, group: DeviceGroup) -> None:
        """
        切换到指定设备组
        
        Args:
            group: 设备组对象
        """
        self.set_default_device(group.output_device_id)
        self.set_default_device(group.input_device_id)
    
    def get_mute_status(self) -> bool:
        """
        获取麦克风静音状态
        
        Returns:
            bool: True表示已静音
        """
        try:
            device = AudioUtilities.GetMicrophone()
            interface = device.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            return volume.GetMute()
        except Exception:
            return False
    
    def toggle_mute(self) -> bool:
        """
        切换麦克风静音状态
        
        Returns:
            bool: 切换后的静音状态
        """
        try:
            device = AudioUtilities.GetMicrophone()
            interface = device.Activate(
                IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            current = volume.GetMute()
            volume.SetMute(not current, None)
            return not current
        except Exception as e:
            raise RuntimeError(f"切换静音失败: {e}")


# 全局音频控制器实例
audio_controller = AudioController()
