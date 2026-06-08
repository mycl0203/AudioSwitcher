# -*- coding: utf-8 -*-
"""
快捷键捕获模块
用于可视化绑定快捷键
"""

import keyboard
import time
from typing import Optional


def capture_hotkey(timeout: int = 10) -> Optional[str]:
    """
    捕获用户按下的快捷键
    
    Args:
        timeout: 超时时间（秒）
        
    Returns:
        捕获到的快捷键字符串，None表示取消或超时
    """
    pressed_keys = set()
    captured_hotkey = None
    cancel = False
    
    def on_press(event):
        nonlocal captured_hotkey, cancel
        if event.name == "esc":
            cancel = True
            return False
        
        key = event.name.lower()
        pressed_keys.add(key)
        
        modifiers = {"ctrl", "alt", "shift", "win"}
        normal_keys = pressed_keys - modifiers
        
        if normal_keys:
            parts = []
            for mod in ["ctrl", "alt", "shift", "win"]:
                if mod in pressed_keys:
                    parts.append(mod)
            parts.extend(sorted(normal_keys))
            captured_hotkey = "+".join(parts)
            return False
    
    hook_id = keyboard.hook(on_press)
    
    try:
        start_time = time.time()
        while captured_hotkey is None and not cancel:
            if time.time() - start_time > timeout:
                break
            time.sleep(0.01)
        
        return captured_hotkey if not cancel else None
    finally:
        keyboard.unhook(hook_id)
