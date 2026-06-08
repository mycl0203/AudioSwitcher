# -*- coding: utf-8 -*-
"""
统一路径管理模块
负责处理项目中所有文件路径的获取和管理
"""

import os
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class PathConfig:
    """路径配置数据类"""
    base_dir: str
    sv_exe: str
    config_json: str
    devices_csv: str
    icon_file: str


class PathManager:
    """路径管理器 - 单例模式"""
    
    _instance: Optional['PathManager'] = None
    _initialized: bool = False
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._config = self._init_paths()
    
    def _init_paths(self) -> PathConfig:
        """初始化所有路径"""
        base_dir = self._get_base_dir()
        return PathConfig(
            base_dir=base_dir,
            sv_exe=os.path.join(base_dir, "SoundVolumeView.exe"),
            config_json=os.path.join(base_dir, "audio_config.json"),
            devices_csv=os.path.join(base_dir, "audio_devices.csv"),
            icon_file=os.path.join(base_dir, "icon.ico")
        )
    
    @staticmethod
    def _get_base_dir() -> str:
        """获取项目根目录 - 兼容源码运行和打包运行"""
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        # 源码运行时，获取当前文件的上两级目录
        current_file = os.path.abspath(__file__)
        modules_dir = os.path.dirname(current_file)
        core_dir = os.path.dirname(modules_dir)
        return os.path.dirname(core_dir)
    
    @property
    def base_dir(self) -> str:
        return self._config.base_dir
    
    @property
    def sv_exe(self) -> str:
        return self._config.sv_exe
    
    @property
    def config_json(self) -> str:
        return self._config.config_json
    
    @property
    def devices_csv(self) -> str:
        return self._config.devices_csv
    
    @property
    def icon_file(self) -> str:
        return self._config.icon_file
    
    def ensure_dir_exists(self, path: str) -> None:
        """确保目录存在"""
        dir_path = os.path.dirname(path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)


# 全局路径管理器实例
path_manager = PathManager()
