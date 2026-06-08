# -*- coding: utf-8 -*-
"""
现代美观的通知系统
参考 macOS 和 Windows 11 的通知设计
"""
import tkinter as tk
import threading
from typing import Optional, Callable
from dataclasses import dataclass
from queue import Queue, Empty

from modules.utils.theme import theme


@dataclass
class ToastMessage:
    """通知消息数据类"""
    message: str
    title: str = ""
    icon_type: str = "info"
    duration: float = 3.5


class ToastWindow:
    """精美的通知窗口"""
    
    def __init__(self, master=None, message: ToastMessage = None, 
                 on_close: Callable = None):
        self.message = message
        self.on_close = on_close
        self.master = master
        self.window = None
        self.closed = False
        self.animation_running = False
    
    def _get_icon_symbol(self) -> str:
        """获取精美的图标符号"""
        icons = {
            "info": "ℹ",
            "success": "✓",
            "warning": "⚠",
            "error": "✕"
        }
        return icons.get(self.message.icon_type, "ℹ")
    
    def show(self):
        """显示精美的通知"""
        if self.window is not None:
            return
        
        # 获取配色
        bg_color, accent_color, text_color = theme.get_notification_colors(
            self.message.icon_type
        )
        
        # 创建窗口
        self.window = tk.Toplevel(self.master)
        self.window.title("")
        self.window.overrideredirect(True)
        self.window.attributes('-topmost', True)
        self.window.attributes('-alpha', 0.0)
        self.window.configure(bg=bg_color)
        
        # 主容器 - 添加轻微阴影效果
        container = tk.Frame(
            self.window,
            bg=bg_color,
            padx=18,
            pady=14
        )
        container.pack(fill='both', expand=True)
        
        # 左侧图标区域
        icon_frame = tk.Frame(container, bg=bg_color)
        icon_frame.pack(side='left', padx=(0, 16))
        
        # 图标按钮 - 更大更美观
        icon_btn = tk.Frame(
            icon_frame,
            bg=accent_color,
            width=46,
            height=46
        )
        icon_btn.pack()
        icon_btn.pack_propagate(False)
        
        icon_label = tk.Label(
            icon_btn,
            text=self._get_icon_symbol(),
            font=("Segoe UI Symbol", 20, "bold"),
            bg=accent_color,
            fg="#ffffff"
        )
        icon_label.place(relx=0.5, rely=0.5, anchor='center')
        
        # 右侧内容区域
        content_frame = tk.Frame(container, bg=bg_color)
        content_frame.pack(side='left', fill='both', expand=True)
        
        # 标题
        if self.message.title:
            title_label = tk.Label(
                content_frame,
                text=self.message.title,
                font=("Microsoft YaHei UI", 13, "bold"),
                bg=bg_color,
                fg=text_color,
                anchor='w'
            )
            title_label.pack(fill='x', pady=(0, 4))
        
        # 消息内容 - 更大的字体
        message_label = tk.Label(
            content_frame,
            text=self.message.message,
            font=("Microsoft YaHei UI", 12),
            bg=bg_color,
            fg=text_color,
            anchor='w',
            wraplength=280
        )
        message_label.pack(fill='x')
        
        # 关闭按钮 - 更大更易用
        close_frame = tk.Frame(container, bg=bg_color)
        close_frame.pack(side='right', padx=(8, 0))
        
        close_label = tk.Label(
            close_frame,
            text="×",
            font=("Segoe UI", 22),
            bg=bg_color,
            fg=text_color,
            cursor="hand2"
        )
        close_label.pack()
        
        # 点击任意位置关闭
        def close_anywhere(event):
            self.close()
        
        self.window.bind("<Button-1>", close_anywhere)
        close_label.bind("<Button-1>", close_anywhere)
        icon_btn.bind("<Button-1>", close_anywhere)
        
        # 计算窗口位置
        self.window.update_idletasks()
        width = self.window.winfo_reqwidth()
        height = self.window.winfo_reqheight()
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        x = screen_width - width - 24
        y = screen_height - height - 48
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        
        # 淡入动画
        self._fade_in()
        
        # 自动关闭
        if self.message.duration > 0:
            self.window.after(int(self.message.duration * 1000), self.close)
    
    def _fade_in(self):
        """流畅的淡入动画"""
        if not self.window or self.closed:
            return
        
        alpha = self.window.attributes('-alpha')
        if alpha < 0.98:
            self.window.attributes('-alpha', min(0.98, alpha + 0.08))
            self.window.after(20, self._fade_in)
        else:
            self.window.attributes('-alpha', 0.98)
    
    def close(self):
        """关闭通知（流畅的淡出动画）"""
        if self.closed:
            return
        self.closed = True
        
        if self.window:
            def fade_out():
                if not self.window:
                    return
                
                alpha = self.window.attributes('-alpha')
                if alpha > 0:
                    self.window.attributes('-alpha', max(0, alpha - 0.12))
                    self.window.after(25, fade_out)
                else:
                    if self.window:
                        self.window.destroy()
                        if self.on_close:
                            self.on_close()
            
            fade_out()


class ToastManager:
    """通知管理器"""
    
    def __init__(self, root=None):
        self.root = root
        self.queue = Queue()
        self.active_toasts = []
        self.running = False
        self.thread = None
    
    def start(self):
        """启动通知队列处理"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()
    
    def _process_queue(self):
        """处理通知队列"""
        while self.running:
            try:
                msg = self.queue.get(timeout=0.1)
                if self.root:
                    self.root.after(0, lambda: self._show(msg))
            except Empty:
                continue
    
    def _show(self, msg):
        """显示单个通知"""
        toast = ToastWindow(self.root, msg, lambda: self._remove(toast))
        self.active_toasts.append(toast)
        toast.show()
    
    def _remove(self, toast):
        """移除通知"""
        if toast in self.active_toasts:
            self.active_toasts.remove(toast)
    
    def show(self, message: str, title: str = "", icon_type: str = "info", duration: float = 3.5):
        """显示通知"""
        self.queue.put(ToastMessage(message, title, icon_type, duration))
        if not self.running:
            self.start()
    
    def show_success(self, message: str, title: str = "成功"):
        """显示成功通知"""
        self.show(message, title, "success")
    
    def show_info(self, message: str, title: str = "提示"):
        """显示信息通知"""
        self.show(message, title, "info")
    
    def show_warning(self, message: str, title: str = "警告"):
        """显示警告通知"""
        self.show(message, title, "warning")
    
    def show_error(self, message: str, title: str = "错误"):
        """显示错误通知"""
        self.show(message, title, "error")
    
    def stop(self):
        """停止通知管理器"""
        self.running = False


_toast_manager: Optional[ToastManager] = None


def init_toast_manager(root=None):
    """初始化通知管理器"""
    global _toast_manager
    _toast_manager = ToastManager(root)
    _toast_manager.start()
    return _toast_manager


def get_toast_manager() -> Optional[ToastManager]:
    """获取通知管理器"""
    return _toast_manager


def show_toast(message: str, title: str = "", icon_type: str = "info", duration: float = 3.5):
    """显示通知（快捷函数）"""
    if _toast_manager:
        _toast_manager.show(message, title, icon_type, duration)
