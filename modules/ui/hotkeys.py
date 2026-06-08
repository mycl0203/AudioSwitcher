# -*- coding: utf-8 -*-
"""
全局快捷键管理模块
"""

import keyboard
from typing import List, Callable
from ..core.models import DeviceGroup


class HotkeyManager:
    """快捷键管理器"""
    
    def __init__(
        self,
        cycle_hotkey: str,
        device_groups: List[DeviceGroup],
        cycle_callback: Callable,
        switch_callback: Callable[[int], None],
        mute_hotkey: str,
        mute_callback: Callable,
        root
    ):
        self._cycle_hotkey = cycle_hotkey
        self._mute_hotkey = mute_hotkey
        self._device_groups = device_groups
        self._cycle_callback = cycle_callback
        self._switch_callback = switch_callback
        self._mute_callback = mute_callback
        self._root = root
        self._registered = False
    
    def start(self) -> None:
        """启动快捷键监听"""
        if self._registered:
            return
        
        # 注册循环切换快捷键
        if self._cycle_hotkey:
            keyboard.add_hotkey(
                self._cycle_hotkey,
                lambda: self._root.after(0, self._cycle_callback)
            )
        
        # 注册静音快捷键
        if self._mute_hotkey:
            keyboard.add_hotkey(
                self._mute_hotkey,
                lambda: self._root.after(0, self._mute_callback)
            )
        
        # 注册每个设备组的快捷键
        for idx, group in enumerate(self._device_groups):
            if group.hotkey:
                def _make_switch(i):
                    return lambda: self._root.after(0, lambda: self._switch_callback(i))
                
                keyboard.add_hotkey(group.hotkey, _make_switch(idx))
        
        self._registered = True
    
    def stop(self) -> None:
        """停止快捷键监听"""
        keyboard.unhook_all()
        self._registered = False
