# -*- coding: utf-8 -*-
"""
系统托盘管理模块
"""

import os
import threading
from typing import Optional, Callable, List
from PIL import Image, ImageDraw
from pystray import Icon, MenuItem as Item, Menu
from ..core.paths import path_manager
from ..core.models import DeviceGroup


class TrayIconManager:
    """托盘图标管理器"""
    
    def __init__(
        self,
        exit_callback: Callable,
        open_ui_callback: Callable,
        switch_callback: Callable[[int], None],
        toggle_mute_callback: Callable,
        get_current_group_name: Callable[[], str],
        get_mute_status: Callable[[], bool],
        device_groups: List[DeviceGroup],
        root
    ):
        self._exit_callback = exit_callback
        self._open_ui_callback = open_ui_callback
        self._switch_callback = switch_callback
        self._toggle_mute_callback = toggle_mute_callback
        self._get_current_group_name = get_current_group_name
        self._get_mute_status = get_mute_status
        self._device_groups = device_groups
        self._root = root
        
        self._icon: Optional[Icon] = None
        self._green_icon: Optional[Image.Image] = None
        self._red_icon: Optional[Image.Image] = None
        
        self._load_icons()
    
    def _load_icons(self) -> None:
        """加载图标"""
        icon_path = path_manager.icon_file
        base_icon = None
        
        if os.path.exists(icon_path):
            try:
                base_icon = Image.open(icon_path).resize((64, 64))
            except Exception:
                pass
        
        if base_icon is None:
            base_icon = Image.new('RGB', (64, 64), color='#2ecc71')
        
        base_icon = base_icon.convert("RGBA")
        
        # 创建圆形遮罩
        width, height = base_icon.size
        mask = Image.new('L', (width, height), 0)
        draw = ImageDraw.Draw(mask)
        draw.ellipse((0, 0, width, height), fill=255)
        base_icon.putalpha(mask)
        
        # 计算亮度函数
        def lum(r, g, b):
            return int(0.299 * r + 0.587 * g + 0.114 * b)
        
        # 生成绿色图标
        self._green_icon = Image.new('RGBA', (width, height))
        src_pixels = base_icon.load()
        dst_pixels = self._green_icon.load()
        for i in range(width):
            for j in range(height):
                r, g, b, a = src_pixels[i, j]
                l = lum(r, g, b)
                dst_pixels[i, j] = (0, l, 0, a)
        
        # 生成红色图标
        self._red_icon = Image.new('RGBA', (width, height))
        dst_pixels = self._red_icon.load()
        for i in range(width):
            for j in range(height):
                r, g, b, a = src_pixels[i, j]
                l = lum(r, g, b)
                dst_pixels[i, j] = (l, 0, 0, a)
    
    def _build_menu(self) -> Menu:
        """构建托盘菜单"""
        menu_items = []
        
        # 当前状态
        try:
            current_group = self._get_current_group_name()
        except Exception:
            current_group = "未知"
        menu_items.append(Item(f"当前：{current_group}", lambda *a: 0, enabled=False))
        menu_items.append(Menu.SEPARATOR)
        
        # 打开UI
        def _open_ui(*_):
            self._root.after(0, self._open_ui_callback)
            return 0
        
        menu_items.append(Item("打开控制面板", _open_ui))
        menu_items.append(Menu.SEPARATOR)
        
        # 设备组列表
        for idx, group in enumerate(self._device_groups):
            def _make_switch(i):
                def _switch(*_):
                    self._root.after(0, lambda: self._switch_callback(i))
                    return 0
                return _switch
            
            menu_items.append(Item(group.display_name, _make_switch(idx)))
        
        menu_items.append(Menu.SEPARATOR)
        
        # 麦克风静音
        try:
            muted = self._get_mute_status()
        except Exception:
            muted = False
        
        mute_text = "取消麦克风静音" if muted else "静音麦克风"
        
        def _toggle_mute(*_):
            self._root.after(0, self._toggle_mute_callback)
            return 0
        
        menu_items.append(Item(mute_text, _toggle_mute))
        menu_items.append(Menu.SEPARATOR)
        
        # 退出
        def _exit(*_):
            def _do_exit():
                if self._exit_callback:
                    self._exit_callback()
            
            self._root.after(0, _do_exit)
            return 0
        
        menu_items.append(Item("退出", _exit))
        
        return Menu(*menu_items)
    
    def update_icon(self, muted: bool) -> None:
        """更新托盘图标"""
        if self._icon is not None:
            self._icon.icon = self._red_icon if muted else self._green_icon
    
    def update_groups(self, groups: List[DeviceGroup]) -> None:
        """更新设备组"""
        self._device_groups = groups
        if self._icon is not None:
            self._icon.menu = self._build_menu()
    
    def start(self) -> None:
        """启动托盘"""
        if self._icon is not None:
            return
        
        self._icon = Icon(
            "AudioSwitcher",
            self._green_icon,
            "音频切换器",
            menu=self._build_menu()
        )
        
        threading.Thread(target=self._icon.run, daemon=True).start()
    
    def stop(self) -> None:
        """停止托盘"""
        if self._icon is not None:
            self._icon.stop()
            self._icon = None
