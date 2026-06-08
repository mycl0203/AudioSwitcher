# -*- coding: utf-8 -*-
"""
现代化主题系统 - 简洁优雅设计
提供统一的配色、字体、间距等设计系统
"""
from dataclasses import dataclass
from typing import Tuple, Dict


@dataclass
class ThemeColors:
    """主题颜色系统"""
    # 主色调
    primary: str = "#3b82f6"
    primary_hover: str = "#2563eb"
    primary_light: str = "#dbeafe"
    
    # 成功色
    success: str = "#22c55e"
    success_hover: str = "#16a34a"
    success_light: str = "#dcfce7"
    
    # 警告色
    warning: str = "#f59e0b"
    warning_hover: str = "#d97706"
    warning_light: str = "#fef3c7"
    
    # 错误色
    error: str = "#ef4444"
    error_hover: str = "#dc2626"
    error_light: str = "#fee2e2"
    
    # 中性色
    gray_50: str = "#f9fafb"
    gray_100: str = "#f3f4f6"
    gray_200: str = "#e5e7eb"
    gray_300: str = "#d1d5db"
    gray_400: str = "#9ca3af"
    gray_500: str = "#6b7280"
    gray_600: str = "#4b5563"
    gray_700: str = "#374151"
    gray_800: str = "#1f2937"
    gray_900: str = "#111827"
    
    # 背景色
    bg_main: str = "#ffffff"
    bg_secondary: str = "#f9fafb"
    bg_card: str = "#ffffff"
    
    # 文字色
    text_primary: str = "#111827"
    text_secondary: str = "#4b5563"
    text_muted: str = "#6b7280"
    text_white: str = "#ffffff"
    
    # 边框色
    border: str = "#e5e7eb"
    border_focus: str = "#3b82f6"
    
    # 错误提示色
    error_bg: str = "#fef2f2"
    error_border: str = "#fecaca"
    error_text: str = "#dc2626"


@dataclass
class ThemeFonts:
    """主题字体系统"""
    main: str = "Microsoft YaHei UI"
    ui: str = "Segoe UI"
    mono: str = "Consolas"
    
    sizes: Dict[str, int] = None
    
    def __post_init__(self):
        if self.sizes is None:
            self.sizes = {
                "xs": 12,
                "sm": 13,
                "base": 14,
                "lg": 15,
                "xl": 16,
                "2xl": 18,
                "3xl": 20
            }


@dataclass
class ThemeSpacing:
    """主题间距系统"""
    xs: int = 4
    sm: int = 8
    md: int = 12
    lg: int = 16
    xl: int = 20
    xxl: int = 24


@dataclass
class ThemeRadius:
    """主题圆角系统"""
    none: int = 0
    sm: int = 6
    md: int = 8
    lg: int = 12
    xl: int = 16
    full: int = 9999


@dataclass
class ThemeShadow:
    """主题阴影系统（模拟）"""
    sm: str = "0 1px 2px 0 rgba(0,0,0,0.05)"
    md: str = "0 4px 6px -1px rgba(0,0,0,0.1)"
    lg: str = "0 10px 15px -3px rgba(0,0,0,0.1)"


class Theme:
    """主题配置单例"""
    
    def __init__(self):
        self.colors = ThemeColors()
        self.fonts = ThemeFonts()
        self.spacing = ThemeSpacing()
        self.radius = ThemeRadius()
        self.shadow = ThemeShadow()
    
    def get_notification_colors(self, icon_type: str) -> Tuple[str, str, str]:
        """获取通知配色
        
        Returns: (背景色, 图标色, 文字色)
        """
        color_map = {
            "info": (self.colors.primary, self.colors.primary, self.colors.text_white),
            "success": (self.colors.success, self.colors.success, self.colors.text_white),
            "warning": (self.colors.warning, self.colors.warning, self.colors.text_white),
            "error": (self.colors.error, self.colors.error, self.colors.text_white)
        }
        return color_map.get(icon_type, color_map["info"])
    
    def get_card_colors(self) -> Tuple[str, str]:
        """获取卡片配色
        
        Returns: (背景色, 边框色)
        """
        return (self.colors.gray_50, self.colors.gray_200)


# 全局主题实例
theme = Theme()
