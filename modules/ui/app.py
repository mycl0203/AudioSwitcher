# -*- coding: utf-8 -*-
"""
音频切换器主应用程序
现代化UI设计 - 包含所有交互优化
"""
import customtkinter as ctk
from tkinter import messagebox
import threading
import sys
import os
import time
from typing import Optional, List, Dict, Callable, Any

from modules.core.paths import path_manager
from modules.core.models import AppConfig, DeviceGroup
from modules.core.config import config_manager
from modules.audio.controller import audio_controller
from modules.utils.toast import init_toast_manager
from modules.utils.hotkey_capture import capture_hotkey
from modules.utils.theme import theme
from modules.ui.tray import TrayIconManager
from modules.ui.hotkeys import HotkeyManager


class AudioSwitcherApp:
    """音频切换器主应用类"""
    
    def __init__(self):
        self.config: Optional[AppConfig] = None
        self.current_group_index: int = 0
        self.root: Optional[ctk.CTk] = None
        self.hotkey_manager: Optional[HotkeyManager] = None
        self.tray_manager: Optional[TrayIconManager] = None
        self.toast_manager = None
        self._initialized = False
        
        # UI状态变量
        self.status_flash_timer: Optional[str] = None
        self.pending_deletion: Optional[int] = None
        self.deletion_timeout: Optional[str] = None
    
    def run(self):
        if self._initialized:
            return
        self._initialized = True
        
        try:
            self.config = config_manager.load()
            self._update_current_group_index()
            
            # 设置主题
            ctk.set_appearance_mode("light")
            ctk.set_default_color_theme("blue")
            
            # 高DPI适配
            self._setup_dpi_awareness()
            
            self.root = ctk.CTk()
            self.root.title("音频切换器")
            self.root.geometry("460x600")
            self.root.minsize(420, 560)
            self.root.resizable(True, True)
            self.root.protocol("WM_DELETE_WINDOW", self._minimize_to_tray)
            
            # 自定义滚动条样式
            self._setup_custom_styles()
            
            self._setup_window_icon()
            self.toast_manager = init_toast_manager(self.root)
            self._create_ui()
            self._setup_hotkeys()
            self._setup_tray()
            self.root.mainloop()
            
        except Exception as e:
            messagebox.showerror("启动错误", f"应用启动失败: {e}")
            raise
    
    def _setup_dpi_awareness(self):
        """设置高DPI适配"""
        try:
            from ctypes import windll
            # 设置进程DPI感知
            windll.shcore.SetProcessDpiAwareness(1)  # 系统DPI感知
        except Exception:
            pass
    
    def _setup_custom_styles(self):
        """设置自定义样式"""
        try:
            ctk.set_widget_scaling(1.0)
            ctk.set_window_scaling(1.0)
        except Exception:
            pass
    
    def _setup_window_icon(self):
        try:
            if os.path.exists(path_manager.icon_file):
                self.root.iconbitmap(path_manager.icon_file)
        except Exception:
            pass
    
    def _create_ui(self):
        # 主容器
        main_container = ctk.CTkFrame(self.root, fg_color=theme.colors.bg_secondary)
        main_container.pack(fill="both", expand=True, padx=12, pady=12)
        
        # 标签页 - 直接在顶部
        tabview = ctk.CTkTabview(
            main_container,
            corner_radius=theme.radius.lg,
            fg_color=theme.colors.bg_main
        )
        tabview.pack(fill="both", expand=True)
        
        # 设置标签页字体
        tabview._segmented_button.configure(
            font=(theme.fonts.main, theme.fonts.sizes["base"])
        )
        
        # 标签页
        tab_switch = tabview.add("快速切换")
        self._create_switch_tab(tab_switch)
        
        tab_config = tabview.add("设备管理")
        self._create_config_tab(tab_config)
        
        tab_settings = tabview.add("设置")
        self._create_settings_tab(tab_settings)
    
    def _create_switch_tab(self, parent):
        self.switch_frame = ctk.CTkScrollableFrame(
            parent,
            label_text="",
            corner_radius=theme.radius.md,
            fg_color=theme.colors.bg_main
        )
        self.switch_frame.pack(fill="both", expand=True, padx=4, pady=4)
        self._refresh_switch_tab()
    
    def _refresh_switch_tab(self):
        for widget in self.switch_frame.winfo_children():
            widget.destroy()
        
        # 当前设备卡片
        status_card = self._create_section_card(self.switch_frame, "当前设备")
        status_card.pack(fill="x", pady=(0, 10), padx=4)
        
        self.status_label = ctk.CTkLabel(
            status_card,
            text=self._get_current_group_name(),
            font=(theme.fonts.main, theme.fonts.sizes["xl"], "bold"),
            text_color=theme.colors.text_primary
        )
        self.status_label.pack(anchor="w", padx=16, pady=(6, 16))
        
        # 麦克风状态卡片
        mic_card = ctk.CTkFrame(
            self.switch_frame,
            corner_radius=theme.radius.lg,
            fg_color=theme.colors.bg_main,
            border_width=1,
            border_color=theme.colors.border
        )
        mic_card.pack(fill="x", pady=(0, 10), padx=4)
        
        mic_title = ctk.CTkLabel(
            mic_card,
            text="麦克风状态",
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            text_color=theme.colors.text_secondary
        )
        mic_title.pack(anchor="w", padx=16, pady=(12, 4))
        
        try:
            muted = audio_controller.get_mute_status()
            mute_text = "麦克风已静音" if muted else "麦克风正常"
            mute_color = theme.colors.error if muted else theme.colors.success
            
            self.mute_status_label = ctk.CTkLabel(
                mic_card,
                text=mute_text,
                font=(theme.fonts.main, theme.fonts.sizes["lg"]),
                text_color=mute_color
            )
        except Exception:
            self.mute_status_label = ctk.CTkLabel(
                mic_card,
                text="麦克风状态",
                font=(theme.fonts.main, theme.fonts.sizes["lg"]),
                text_color=theme.colors.text_secondary
            )
        self.mute_status_label.pack(anchor="w", padx=16, pady=(0, 12))
        
        # 快速操作卡片
        actions_card = self._create_section_card(self.switch_frame, "快速操作")
        actions_card.pack(fill="x", pady=(0, 10), padx=4)
        
        # 静音按钮
        mute_btn = ctk.CTkButton(
            actions_card,
            text="切换麦克风静音",
            height=52,
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            corner_radius=theme.radius.lg,
            fg_color=theme.colors.primary,
            hover_color=theme.colors.primary_hover,
            command=self._toggle_mute
        )
        mute_btn.pack(fill="x", padx=12, pady=(6, 6))
        
        # 循环切换按钮
        if self.config and len(self.config.device_groups) > 0:
            cycle_btn = ctk.CTkButton(
                actions_card,
                text="循环切换设备组",
                height=52,
                font=(theme.fonts.main, theme.fonts.sizes["base"]),
                corner_radius=theme.radius.lg,
                fg_color=theme.colors.gray_700,
                hover_color=theme.colors.gray_800,
                command=self._cycle_switch
            )
            cycle_btn.pack(fill="x", padx=12, pady=(0, 12))
        
        # 设备组卡片
        if self.config and len(self.config.device_groups) > 0:
            groups_card = self._create_section_card(self.switch_frame, "设备组")
            groups_card.pack(fill="x", padx=4)
            
            for idx, group in enumerate(self.config.device_groups):
                is_current = (idx == self.current_group_index)
                group_btn = self._create_group_button(groups_card, group, idx, is_current)
                group_btn.pack(fill="x", padx=12, pady=(0, 8))
            
            # 底部空白
            spacer = ctk.CTkLabel(groups_card, text="")
            spacer.pack(pady=4)
    
    def _create_section_card(self, parent, title_text: str) -> ctk.CTkFrame:
        """创建带标题的卡片"""
        card = ctk.CTkFrame(
            parent,
            corner_radius=theme.radius.lg,
            fg_color=theme.colors.bg_main,
            border_width=1,
            border_color=theme.colors.border
        )
        
        title = ctk.CTkLabel(
            card,
            text=title_text,
            font=(theme.fonts.main, theme.fonts.sizes["base"], "bold"),
            text_color=theme.colors.text_secondary
        )
        title.pack(anchor="w", padx=16, pady=(12, 0))
        
        return card
    
    def _create_group_button(self, parent, group: DeviceGroup, index: int, is_current: bool) -> ctk.CTkButton:
        """创建设备组按钮，带选中状态标识"""
        
        btn_container = ctk.CTkFrame(parent, fg_color="transparent")
        
        # 左侧指示条（仅选中时显示）
        if is_current:
            indicator = ctk.CTkFrame(
                btn_container,
                width=4,
                height=48,
                corner_radius=2,
                fg_color=theme.colors.primary
            )
            indicator.pack(side="left", fill="y", padx=(0, 8))
        
        # 按钮文本
        btn_text = f"✓ {group.display_name}" if is_current else group.display_name
        
        group_btn = ctk.CTkButton(
            btn_container,
            text=btn_text,
            height=48,
            font=(theme.fonts.main, theme.fonts.sizes["base"], "bold" if is_current else "normal"),
            corner_radius=theme.radius.md,
            fg_color=theme.colors.primary if is_current else theme.colors.gray_100,
            hover_color=theme.colors.primary_hover if is_current else theme.colors.gray_200,
            text_color="white" if is_current else theme.colors.text_primary,
            command=lambda: self._switch_to_group(index)
        )
        group_btn.pack(side="left", fill="x", expand=True)
        
        return btn_container
    
    def _create_config_tab(self, parent):
        self.config_frame = ctk.CTkScrollableFrame(
            parent,
            label_text="",
            corner_radius=theme.radius.md,
            fg_color=theme.colors.bg_main
        )
        self.config_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        # 添加按钮卡片
        add_card = self._create_section_card(self.config_frame, "设备组管理")
        add_card.pack(fill="x", pady=(0, 10), padx=4)
        
        add_btn = ctk.CTkButton(
            add_card,
            text="添加设备组",
            height=52,
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            corner_radius=theme.radius.lg,
            fg_color=theme.colors.success,
            hover_color=theme.colors.success_hover,
            command=lambda: self._open_group_editor()
        )
        add_btn.pack(fill="x", padx=12, pady=12)
        
        self._refresh_config_tab()
    
    def _refresh_config_tab(self):
        # 移除旧的设备组卡片（保留添加按钮）
        widgets = self.config_frame.winfo_children()
        for widget in widgets[1:]:
            widget.destroy()
        
        if not self.config or len(self.config.device_groups) == 0:
            empty_card = ctk.CTkFrame(
                self.config_frame,
                corner_radius=theme.radius.lg,
                fg_color=theme.colors.bg_main,
                border_width=1,
                border_color=theme.colors.border
            )
            empty_card.pack(fill="x", padx=4)
            
            empty_label = ctk.CTkLabel(
                empty_card,
                text="暂无设备组\n点击上方按钮添加",
                font=(theme.fonts.main, theme.fonts.sizes["base"]),
                text_color=theme.colors.text_muted
            )
            empty_label.pack(pady=40)
            return
        
        # 显示设备组列表
        for idx, group in enumerate(self.config.device_groups):
            card = self._create_device_group_card(idx, group)
            card.pack(fill="x", pady=(0, 10), padx=4)
        
        # 底部空白
        spacer = ctk.CTkLabel(self.config_frame, text="")
        spacer.pack(pady=4)
    
    def _create_device_group_card(self, index: int, group: DeviceGroup) -> ctk.CTkFrame:
        """创建设备组管理卡片"""
        card = ctk.CTkFrame(
            self.config_frame,
            corner_radius=theme.radius.lg,
            fg_color=theme.colors.bg_main,
            border_width=1,
            border_color=theme.colors.border
        )
        
        # 设备组信息
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=16, pady=14)
        
        name_label = ctk.CTkLabel(
            info_frame,
            text=group.display_name,
            font=(theme.fonts.main, theme.fonts.sizes["lg"], "bold"),
            anchor="w",
            text_color=theme.colors.text_primary
        )
        name_label.pack(fill="x")
        
        out_label = ctk.CTkLabel(
            info_frame,
            text=f"输出: {group.output_device_name}",
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            anchor="w",
            text_color=theme.colors.text_secondary
        )
        out_label.pack(fill="x", pady=(4, 0))
        
        in_label = ctk.CTkLabel(
            info_frame,
            text=f"输入: {group.input_device_name}",
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            anchor="w",
            text_color=theme.colors.text_secondary
        )
        in_label.pack(fill="x", pady=(2, 0))
        
        if group.hotkey:
            hotkey_label = ctk.CTkLabel(
                info_frame,
                text=f"快捷键: {group.hotkey}",
                font=(theme.fonts.main, theme.fonts.sizes["sm"]),
                anchor="w",
                text_color=theme.colors.text_muted
            )
            hotkey_label.pack(fill="x", pady=(2, 0))
        
        # 操作按钮
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="right", padx=12, pady=14)
        
        edit_btn = ctk.CTkButton(
            btn_frame,
            text="编辑",
            width=64,
            height=40,
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            corner_radius=theme.radius.md,
            fg_color=theme.colors.gray_100,
            hover_color=theme.colors.gray_200,
            text_color=theme.colors.text_primary,
            command=lambda i=index: self._open_group_editor(i)
        )
        edit_btn.pack(side="left", padx=3)
        
        delete_btn = ctk.CTkButton(
            btn_frame,
            text="删除",
            width=64,
            height=40,
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            corner_radius=theme.radius.md,
            fg_color=theme.colors.error,
            hover_color=theme.colors.error_hover,
            command=lambda i=index: self._confirm_delete_group(i)
        )
        delete_btn.pack(side="left", padx=3)
        
        return card
    
    def _create_settings_tab(self, parent):
        settings_frame = ctk.CTkScrollableFrame(
            parent,
            label_text="",
            corner_radius=theme.radius.md,
            fg_color=theme.colors.bg_main
        )
        settings_frame.pack(fill="both", expand=True, padx=4, pady=4)
        
        # 通知设置卡片
        notif_card = self._create_section_card(settings_frame, "通知设置")
        notif_card.pack(fill="x", pady=(0, 10), padx=4)
        
        notif_var = ctk.BooleanVar(value=self.config.enable_notification if self.config else True)
        
        def toggle_notif():
            if self.config:
                self.config.enable_notification = notif_var.get()
                config_manager.save(self.config)
                self._update_notification_status_label(notif_var.get())
        
        notif_switch = ctk.CTkSwitch(
            notif_card,
            text="切换通知",
            variable=notif_var,
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            switch_width=50,
            switch_height=28,
            command=toggle_notif
        )
        notif_switch.pack(anchor="w", padx=16, pady=(12, 0))
        
        # 状态文字
        self.notification_status_label = ctk.CTkLabel(
            notif_card,
            text=self._get_notification_status_text(notif_var.get()),
            font=(theme.fonts.main, theme.fonts.sizes["sm"]),
            text_color=theme.colors.text_muted
        )
        self.notification_status_label.pack(anchor="w", padx=16, pady=(4, 12))
        
        # 快捷键设置卡片
        hotkey_card = self._create_section_card(settings_frame, "快捷键设置")
        hotkey_card.pack(fill="x", pady=(0, 10), padx=4)
        
        self._create_hotkey_setting(
            hotkey_card,
            "循环切换设备组",
            self.config.hotkey_cycle if self.config else "ctrl+alt+right",
            self._update_cycle_hotkey
        )
        
        self._create_hotkey_setting(
            hotkey_card,
            "切换麦克风静音",
            self.config.hotkey_mute if self.config else "ctrl+alt+m",
            self._update_mute_hotkey
        )
        
        # 退出按钮卡片
        exit_card = self._create_section_card(settings_frame, "退出应用")
        exit_card.pack(fill="x", padx=4)
        
        exit_desc = ctk.CTkLabel(
            exit_card,
            text="关闭窗口会最小化到托盘，点击下方按钮彻底退出",
            font=(theme.fonts.main, theme.fonts.sizes["sm"]),
            text_color=theme.colors.text_muted
        )
        exit_desc.pack(anchor="w", padx=16, pady=(12, 8))
        
        exit_btn = ctk.CTkButton(
            exit_card,
            text="退出应用",
            height=52,
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            corner_radius=theme.radius.lg,
            fg_color=theme.colors.error,
            hover_color=theme.colors.error_hover,
            command=self._confirm_exit
        )
        exit_btn.pack(fill="x", padx=16, pady=(0, 12))
    
    def _get_notification_status_text(self, enabled: bool) -> str:
        """获取通知开关状态文字"""
        return "已开启切换通知" if enabled else "已关闭切换通知"
    
    def _update_notification_status_label(self, enabled: bool):
        """更新通知状态标签"""
        if hasattr(self, "notification_status_label"):
            self.notification_status_label.configure(
                text=self._get_notification_status_text(enabled)
            )
    
    def _create_hotkey_setting(self, parent, label_text: str, current_hotkey: str, update_func: Callable):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", padx=16, pady=6)
        
        label = ctk.CTkLabel(
            frame,
            text=label_text,
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            anchor="w",
            text_color=theme.colors.text_primary
        )
        label.pack(side="left", fill="x", expand=True)
        
        hotkey_var = ctk.StringVar(value=current_hotkey)
        
        hotkey_display = ctk.CTkLabel(
            frame,
            textvariable=hotkey_var,
            font=(theme.fonts.ui, theme.fonts.sizes["base"]),
            width=20,
            fg_color=theme.colors.gray_100,
            corner_radius=theme.radius.md,
            height=42
        )
        hotkey_display.pack(side="left", padx=10)
        
        def bind_hk():
            messagebox.showinfo("提示", "请在接下来的10秒内按下快捷键\n按ESC取消")
            
            def capture():
                hk = capture_hotkey()
                if hk:
                    self.root.after(0, lambda: update_func(hk, hotkey_var))
            
            threading.Thread(target=capture, daemon=True).start()
        
        bind_btn = ctk.CTkButton(
            frame,
            text="绑定",
            width=72,
            height=42,
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            corner_radius=theme.radius.md,
            fg_color=theme.colors.primary,
            hover_color=theme.colors.primary_hover,
            command=bind_hk
        )
        bind_btn.pack(side="left")
    
    def _update_cycle_hotkey(self, hotkey: str, var: Any):
        var.set(hotkey)
        if self.config:
            self.config.hotkey_cycle = hotkey
            config_manager.save(self.config)
            self._reload_hotkeys()
            if self.toast_manager:
                self.toast_manager.show_success(f"循环快捷键已设置: {hotkey}")
    
    def _update_mute_hotkey(self, hotkey: str, var: Any):
        var.set(hotkey)
        if self.config:
            self.config.hotkey_mute = hotkey
            config_manager.save(self.config)
            self._reload_hotkeys()
            if self.toast_manager:
                self.toast_manager.show_success(f"静音快捷键已设置: {hotkey}")
    
    def _reload_hotkeys(self):
        if self.hotkey_manager:
            self.hotkey_manager.stop()
        self._setup_hotkeys()
    
    def _get_current_group_name(self) -> str:
        try:
            output_id, input_id = config_manager.get_current_devices()
            output_id = output_id.strip().lower() if output_id else ""
            input_id = input_id.strip().lower() if input_id else ""
            
            for group in self.config.device_groups:
                if (group.output_device_id.strip().lower() == output_id and
                    group.input_device_id.strip().lower() == input_id):
                    return group.display_name
            return "自定义设备"
        except Exception:
            return "未知"
    
    def _update_current_group_index(self):
        try:
            output_id, input_id = config_manager.get_current_devices()
            output_id = output_id.strip().lower() if output_id else ""
            input_id = input_id.strip().lower() if input_id else ""
            
            for idx, group in enumerate(self.config.device_groups):
                if (group.output_device_id.strip().lower() == output_id and
                    group.input_device_id.strip().lower() == input_id):
                    self.current_group_index = idx
                    return
        except Exception:
            pass
    
    def _flash_status_label(self):
        """闪烁状态标签，提供操作反馈"""
        if hasattr(self, "status_label"):
            # 保存原颜色
            original_color = self.status_label.cget("text_color")
            
            def reset_color():
                self.status_label.configure(text_color=original_color)
            
            # 闪蓝色
            self.status_label.configure(text_color=theme.colors.primary)
            self.root.after(150, lambda: self.status_label.configure(text_color=original_color))
            self.root.after(300, lambda: self.status_label.configure(text_color=theme.colors.primary))
            self.root.after(450, reset_color)
    
    def _cycle_switch(self):
        if not self.config or len(self.config.device_groups) == 0:
            return
        next_idx = (self.current_group_index + 1) % len(self.config.device_groups)
        self._switch_to_group(next_idx)
    
    def _switch_to_group(self, index: int):
        if not self.config or index < 0 or index >= len(self.config.device_groups):
            return
        
        group = self.config.device_groups[index]
        
        try:
            audio_controller.switch_to_group(group)
            self.current_group_index = index
            
            if self.config.enable_notification and self.toast_manager:
                self.toast_manager.show_success(f"已切换到: {group.display_name}")
            
            # 刷新UI并提供反馈
            self._flash_status_label()
            self._refresh_switch_tab()
            
        except Exception as e:
            messagebox.showerror("错误", f"切换设备失败: {e}")
    
    def _toggle_mute(self):
        try:
            new_status = audio_controller.toggle_mute()
            
            if self.config.enable_notification and self.toast_manager:
                msg = "麦克风已静音" if new_status else "麦克风已取消静音"
                self.toast_manager.show_info(msg)
            
            if self.tray_manager:
                self.tray_manager.update_icon(new_status)
            
            self._refresh_switch_tab()
            
        except Exception as e:
            messagebox.showerror("错误", f"切换静音失败: {e}")
    
    def _open_group_editor(self, edit_index: Optional[int] = None):
        if not self.config:
            return
        
        editor = ctk.CTkToplevel(self.root)
        editor.title("编辑设备组" if edit_index is not None else "添加设备组")
        editor.geometry("620x780")
        editor.minsize(560, 600)
        editor.resizable(True, True)
        editor.grab_set()
        
        # 保存是否被修改的状态
        is_modified = {'value': False}
        # 记录是否手动修改过名称
        name_manually_modified = {'value': False}
        
        # 获取设备列表
        output_devices, input_devices = config_manager.scan_devices()
        output_names = [d.name for d in output_devices]
        input_names = [d.name for d in input_devices]
        
        # 准备编辑数据
        edit_group = None
        initial_output = ""
        initial_input = ""
        
        if edit_index is not None and 0 <= edit_index < len(self.config.device_groups):
            edit_group = self.config.device_groups[edit_index]
            # 编辑模式：优先通过设备ID匹配，如果找不到再使用名称
            initial_output = edit_group.output_device_name
            initial_input = edit_group.input_device_name
            
            # 尝试通过设备ID找到当前设备名
            if edit_group.output_device_id:
                for d in output_devices:
                    if d.device_id.strip().lower() == edit_group.output_device_id.strip().lower():
                        initial_output = d.name
                        break
            
            if edit_group.input_device_id:
                for d in input_devices:
                    if d.device_id.strip().lower() == edit_group.input_device_id.strip().lower():
                        initial_input = d.name
                        break
        else:
            # 新建模式：使用第一个设备作为默认
            initial_output = output_names[0] if output_names else ""
            initial_input = input_names[0] if input_names else ""
        
        name_var = ctk.StringVar(value=edit_group.display_name if edit_group else self._generate_default_name(initial_output, initial_input))
        output_var = ctk.StringVar(value=initial_output)
        input_var = ctk.StringVar(value=initial_input)
        hotkey_var = ctk.StringVar(value=edit_group.hotkey if edit_group else "")
        
        # 错误标签
        error_frame = ctk.CTkFrame(editor, fg_color="transparent")
        error_frame.pack(fill="x", padx=16, pady=12)
        
        error_label = ctk.CTkLabel(
            error_frame,
            text="",
            font=(theme.fonts.main, theme.fonts.sizes["sm"]),
            text_color=theme.colors.error,
            fg_color=theme.colors.error_light,
            corner_radius=theme.radius.md,
            padx=14,
            pady=10
        )
        error_label.pack(fill="x")
        error_label.pack_forget()
        
        def show_error(message: str):
            error_label.configure(text=message)
            error_label.pack(fill="x")
        
        def clear_error():
            error_label.pack_forget()
        
        # 使用可滚动的主容器
        scroll_container = ctk.CTkScrollableFrame(
            editor,
            label_text="",
            corner_radius=theme.radius.md,
            fg_color="transparent"
        )
        scroll_container.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        
        # 顶部必填提示
        top_hint = ctk.CTkLabel(
            scroll_container,
            text="📝 带 * 的为必填项",
            font=(theme.fonts.main, theme.fonts.sizes["sm"]),
            text_color=theme.colors.text_muted
        )
        top_hint.pack(anchor="w", pady=(0, 14))
        
        # 表单区域卡片
        form_card = self._create_section_card(scroll_container, "设备组信息")
        form_card.pack(fill="x", pady=(0, 16))
        
        # 名称
        name_container = ctk.CTkFrame(form_card, fg_color="transparent")
        name_container.pack(fill="x", padx=16, pady=(16, 14))
        
        ctk.CTkLabel(
            name_container,
            text="显示名称 *",
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            text_color=theme.colors.text_secondary
        ).pack(anchor="w", pady=(0, 6))
        
        name_entry = ctk.CTkEntry(
            name_container,
            textvariable=name_var,
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            height=46,
            corner_radius=theme.radius.md,
            border_width=2,
            border_color=theme.colors.border,
            fg_color=theme.colors.bg_main
        )
        name_entry.pack(fill="x")
        
        # 输出设备
        out_container = ctk.CTkFrame(form_card, fg_color="transparent")
        out_container.pack(fill="x", padx=16, pady=(0, 14))
        
        ctk.CTkLabel(
            out_container,
            text="输出设备 *",
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            text_color=theme.colors.text_secondary
        ).pack(anchor="w", pady=(0, 6))
        
        output_menu = ctk.CTkOptionMenu(
            out_container,
            values=output_names,
            variable=output_var,
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            height=46,
            corner_radius=theme.radius.md
        )
        output_menu.pack(fill="x")
        
        # 输入设备
        in_container = ctk.CTkFrame(form_card, fg_color="transparent")
        in_container.pack(fill="x", padx=16, pady=(0, 14))
        
        ctk.CTkLabel(
            in_container,
            text="输入设备 *",
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            text_color=theme.colors.text_secondary
        ).pack(anchor="w", pady=(0, 6))
        
        input_menu = ctk.CTkOptionMenu(
            in_container,
            values=input_names,
            variable=input_var,
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            height=46,
            corner_radius=theme.radius.md
        )
        input_menu.pack(fill="x")
        
        # 混合设备提示
        mix_hint_label = ctk.CTkLabel(
            form_card,
            text="💡 支持跨设备组合（比如：输出用音响 + 输入用耳机）",
            font=(theme.fonts.main, theme.fonts.sizes["sm"]),
            text_color=theme.colors.text_muted,
            fg_color=theme.colors.gray_100,
            corner_radius=theme.radius.md,
            padx=12,
            pady=10
        )
        mix_hint_label.pack(fill="x", padx=16, pady=(0, 14))
        
        # 快捷键（带提示）
        hk_container = ctk.CTkFrame(form_card, fg_color="transparent")
        hk_container.pack(fill="x", padx=16, pady=(0, 16))
        
        hk_label_frame = ctk.CTkFrame(hk_container, fg_color="transparent")
        hk_label_frame.pack(fill="x")
        
        ctk.CTkLabel(
            hk_label_frame,
            text="快捷键（可选）",
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            text_color=theme.colors.text_secondary
        ).pack(side="left", anchor="w", pady=(0, 6))
        
        # 小提示图标
        ctk.CTkLabel(
            hk_label_frame,
            text="❓",
            font=(theme.fonts.main, theme.fonts.sizes["sm"]),
            text_color=theme.colors.text_muted
        ).pack(side="left", padx=4)
        
        hk_row = ctk.CTkFrame(hk_container, fg_color="transparent")
        hk_row.pack(fill="x")
        
        hotkey_display = ctk.CTkLabel(
            hk_row,
            textvariable=hotkey_var,
            font=(theme.fonts.ui, theme.fonts.sizes["base"]),
            fg_color=theme.colors.gray_100,
            corner_radius=theme.radius.md,
            height=46
        )
        hotkey_display.pack(side="left", fill="x", expand=True)
        
        def bind_hk():
            messagebox.showinfo("提示", "请在接下来的10秒内按下快捷键\n按ESC取消")
            
            def capture():
                hk = capture_hotkey()
                if hk:
                    self.root.after(0, lambda: hotkey_var.set(hk))
            
            threading.Thread(target=capture, daemon=True).start()
        
        ctk.CTkButton(
            hk_row,
            text="绑定",
            width=90,
            height=46,
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            corner_radius=theme.radius.md,
            fg_color=theme.colors.primary,
            hover_color=theme.colors.primary_hover,
            command=bind_hk
        ).pack(side="left", padx=(12, 0))
        
        # ============== 固定在底部的按钮区域 ==============
        button_container = ctk.CTkFrame(editor, fg_color=theme.colors.bg_main)
        button_container.pack(fill="x", padx=16, pady=(0, 16))
        
        button_frame = ctk.CTkFrame(button_container, fg_color="transparent")
        button_frame.pack(fill="x", pady=12)
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="取消",
            width=120,
            height=52,
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            corner_radius=theme.radius.md,
            fg_color=theme.colors.gray_100,
            hover_color=theme.colors.gray_200,
            text_color=theme.colors.text_primary,
            command=lambda: check_and_close()
        )
        cancel_btn.pack(side="right", padx=(8, 0))
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="保存",
            width=120,
            height=52,
            font=(theme.fonts.main, theme.fonts.sizes["base"], "bold"),
            corner_radius=theme.radius.md
        )
        save_btn.pack(side="right", padx=(12, 0))
        
        # 验证函数 - 更新保存按钮状态
        def validate():
            name = name_var.get().strip()
            out_name = output_var.get()
            in_name = input_var.get()
            
            is_valid = bool(name and out_name and in_name)
            
            if is_valid:
                save_btn.configure(
                    state="normal",
                    fg_color=theme.colors.success,
                    hover_color=theme.colors.success_hover
                )
            else:
                save_btn.configure(
                    state="disabled",
                    fg_color=theme.colors.gray_300,
                    hover_color=theme.colors.gray_300
                )
            
            is_modified['value'] = True
        
        # 名称变更追踪（标记是否手动修改）
        def on_name_change(*args):
            name_manually_modified['value'] = True
            validate()
        
        name_var.trace_add("write", on_name_change)
        
        # 设备变更时更新默认名称（仅当未手动修改时）
        def on_device_change(*args):
            if not name_manually_modified['value']:
                auto_name = self._generate_default_name(output_var.get(), input_var.get())
                name_var.set(auto_name)
            validate()
        
        output_var.trace_add("write", on_device_change)
        input_var.trace_add("write", on_device_change)
        
        # 检查并关闭 - 防误操作
        def check_and_close():
            if is_modified['value']:
                confirm = messagebox.askyesno(
                    "确认关闭",
                    "您有未保存的修改，确定要关闭吗？"
                )
                if not confirm:
                    return
            editor.destroy()
        
        # 保存按钮逻辑
        def save():
            clear_error()
            
            name = name_var.get().strip()
            out_name = output_var.get()
            in_name = input_var.get()
            hk = hotkey_var.get().strip()
            
            # 验证
            if not name:
                show_error("请输入显示名称")
                return
            if not out_name or not in_name:
                show_error("请选择输入输出设备")
                return
            
            # 验证快捷键是否重复
            if hk:
                for idx, g in enumerate(self.config.device_groups):
                    if edit_index is not None and idx == edit_index:
                        continue
                    if g.hotkey == hk:
                        show_error(f"快捷键 '{hk}' 已被设备组 '{g.display_name}' 使用")
                        return
            
            # 查找设备ID
            out_id = None
            for d in output_devices:
                if d.name == out_name:
                    out_id = d.device_id
                    break
            
            in_id = None
            for d in input_devices:
                if d.name == in_name:
                    in_id = d.device_id
                    break
            
            if not out_id or not in_id:
                show_error("无法获取设备ID")
                return
            
            new_group = DeviceGroup(
                display_name=name,
                output_device_name=out_name,
                output_device_id=out_id,
                input_device_name=in_name,
                input_device_id=in_id,
                hotkey=hk
            )
            
            if edit_index is not None:
                self.config.device_groups[edit_index] = new_group
            else:
                self.config.device_groups.append(new_group)
            
            config_manager.save(self.config)
            self._update_current_group_index()
            self._refresh_switch_tab()
            self._refresh_config_tab()
            self._reload_hotkeys()
            
            if self.tray_manager:
                self.tray_manager.update_groups(self.config.device_groups)
            
            editor.destroy()
            if self.toast_manager:
                self.toast_manager.show_success("设备组已保存")
        
        save_btn.configure(command=save)
        
        # 覆盖关闭行为
        editor.protocol("WM_DELETE_WINDOW", check_and_close)
        
        # 初始验证一次
        validate()
    
    def _generate_default_name(self, output_name: str, input_name: str) -> str:
        """从设备名自动生成默认显示名称"""
        def extract_simple_name(name: str) -> str:
            """从设备名中提取简洁名称"""
            if not name:
                return ""
            # 移除常见的后缀
            suffixes = [" (", " [", " （", " 【", " - ", "  "]
            for suffix in suffixes:
                if suffix in name:
                    name = name.split(suffix)[0]
            return name.strip()
        
        output_simple = extract_simple_name(output_name)
        input_simple = extract_simple_name(input_name)
        
        if output_simple and input_simple:
            return f"{output_simple} + {input_simple}"
        elif output_simple:
            return output_simple
        elif input_simple:
            return input_simple
        return "我的设备组"
    
    def _confirm_delete_group(self, index: int):
        """确认删除设备组"""
        if not self.config or index < 0 or index >= len(self.config.device_groups):
            return
        
        group = self.config.device_groups[index]
        
        if messagebox.askyesno(
            "确认删除",
            f"确定要删除设备组「{group.display_name}」吗？",
            icon=messagebox.WARNING
        ):
            self._delete_group(index)
    
    def _delete_group(self, index: int):
        """删除设备组，带撤销功能"""
        if not self.config or index < 0 or index >= len(self.config.device_groups):
            return
        
        group = self.config.device_groups[index]
        
        # 保存删除前的数据
        old_groups = list(self.config.device_groups)
        
        # 删除
        del self.config.device_groups[index]
        config_manager.save(self.config)
        
        # 更新UI
        self._update_current_group_index()
        self._refresh_switch_tab()
        self._refresh_config_tab()
        self._reload_hotkeys()
        
        if self.tray_manager:
            self.tray_manager.update_groups(self.config.device_groups)
        
        # 显示撤销选项 - 使用一次性窗口而不是toast + messagebox
        self._show_undo_notification(group, index, old_groups)
    
    def _show_undo_notification(self, group: DeviceGroup, index: int, old_groups: List[DeviceGroup]):
        """显示带撤销选项的通知 - 实现真正的5秒撤销窗口"""
        
        # 创建撤销对话框
        undo_window = ctk.CTkToplevel(self.root)
        undo_window.title("撤销删除")
        undo_window.geometry("420x180")
        undo_window.resizable(False, False)
        undo_window.attributes("-topmost", True)
        undo_window.grab_set()
        
        # 居中显示
        undo_window.update_idletasks()
        x = (undo_window.winfo_screenwidth() // 2) - (420 // 2)
        y = (undo_window.winfo_screenheight() // 2) - (180 // 2)
        undo_window.geometry(f"+{x}+{y}")
        
        # 倒计时变量
        remaining_time = 5
        time_label_var = ctk.StringVar(value=f"5")
        
        # 撤销功能
        def undo_action():
            # 恢复数据
            if self.config:
                self.config.device_groups = old_groups.copy()
                config_manager.save(self.config)
                self._update_current_group_index()
                self._refresh_switch_tab()
                self._refresh_config_tab()
                self._reload_hotkeys()
                if self.tray_manager:
                    self.tray_manager.update_groups(self.config.device_groups)
                if self.toast_manager:
                    self.toast_manager.show_success(f"已恢复设备组: {group.display_name}")
            undo_window.destroy()
        
        # 关闭窗口（不撤销）
        def close_window():
            if self.toast_manager:
                self.toast_manager.show_success(f"已删除设备组: {group.display_name}")
            undo_window.destroy()
        
        # 更新倒计时
        def update_timer():
            nonlocal remaining_time
            if remaining_time > 0:
                remaining_time -= 1
                time_label_var.set(str(remaining_time))
                undo_window.after(1000, update_timer)
            else:
                close_window()
        
        # UI
        main_frame = ctk.CTkFrame(undo_window, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        icon_label = ctk.CTkLabel(
            main_frame,
            text="🗑️",
            font=(theme.fonts.main, 32)
        )
        icon_label.pack(pady=(0, 10))
        
        message_label = ctk.CTkLabel(
            main_frame,
            text=f"已删除设备组「{group.display_name}」",
            font=(theme.fonts.main, theme.fonts.sizes["base"]),
            text_color=theme.colors.text_primary
        )
        message_label.pack(pady=(0, 8))
        
        timer_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        timer_frame.pack(pady=(0, 16))
        
        ctk.CTkLabel(
            timer_frame,
            text="将在 ",
            font=(theme.fonts.main, theme.fonts.sizes["sm"]),
            text_color=theme.colors.text_muted
        ).pack(side="left")
        
        time_label = ctk.CTkLabel(
            timer_frame,
            textvariable=time_label_var,
            font=(theme.fonts.main, theme.fonts.sizes["lg"], "bold"),
            text_color=theme.colors.primary
        )
        time_label.pack(side="left")
        
        ctk.CTkLabel(
            timer_frame,
            text=" 秒后关闭",
            font=(theme.fonts.main, theme.fonts.sizes["sm"]),
            text_color=theme.colors.text_muted
        ).pack(side="left")
        
        # 按钮
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")
        
        cancel_btn = ctk.CTkButton(
            button_frame,
            text="关闭",
            width=120,
            height=40,
            fg_color=theme.colors.gray_100,
            hover_color=theme.colors.gray_200,
            text_color=theme.colors.text_primary,
            command=close_window
        )
        cancel_btn.pack(side="right", padx=(8, 0))
        
        undo_btn = ctk.CTkButton(
            button_frame,
            text="撤销删除",
            width=120,
            height=40,
            fg_color=theme.colors.primary,
            hover_color=theme.colors.primary_hover,
            command=undo_action
        )
        undo_btn.pack(side="right")
        
        # 启动倒计时
        update_timer()
    
    def _minimize_to_tray(self):
        """最小化到系统托盘"""
        if self.root:
            self.root.withdraw()
            
            if self.toast_manager:
                self.toast_manager.show_info("已最小化到托盘")
    
    def _show_window(self):
        """显示窗口"""
        if self.root:
            self.root.deiconify()
            self.root.lift()
            self._refresh_switch_tab()
    
    def _setup_tray(self):
        if self.config and self.root:
            try:
                muted = audio_controller.get_mute_status()
            except Exception:
                muted = False
            
            self.tray_manager = TrayIconManager(
                exit_callback=self._confirm_exit,
                open_ui_callback=self._show_window,
                switch_callback=self._switch_to_group,
                toggle_mute_callback=self._toggle_mute,
                get_current_group_name=self._get_current_group_name,
                get_mute_status=lambda: audio_controller.get_mute_status(),
                device_groups=self.config.device_groups,
                root=self.root
            )
            
            self.tray_manager.start()
            self.tray_manager.update_icon(muted)
            
            def sync_icon():
                if not self.root:
                    return
                try:
                    current_mute = audio_controller.get_mute_status()
                    if self.tray_manager:
                        self.tray_manager.update_icon(current_mute)
                except Exception:
                    pass
                self.root.after(3000, sync_icon)
            
            self.root.after(3000, sync_icon)
    
    def _setup_hotkeys(self):
        if (self.config and self.config.enable_hotkey and
            self.root and self.config.device_groups):
            
            self.hotkey_manager = HotkeyManager(
                cycle_hotkey=self.config.hotkey_cycle,
                device_groups=self.config.device_groups,
                cycle_callback=self._cycle_switch,
                switch_callback=self._switch_to_group,
                mute_hotkey=self.config.hotkey_mute,
                mute_callback=self._toggle_mute,
                root=self.root
            )
            self.hotkey_manager.start()
    
    def _confirm_exit(self):
        if messagebox.askyesno("确认", "确定要退出音频切换器吗？"):
            self._exit_app()
    
    def _exit_app(self):
        try:
            if self.hotkey_manager:
                self.hotkey_manager.stop()
        except Exception:
            pass
        
        try:
            if self.tray_manager:
                self.tray_manager.stop()
        except Exception:
            pass
        
        sys.exit(0)


def main():
    app = AudioSwitcherApp()
    app.run()


if __name__ == "__main__":
    main()
