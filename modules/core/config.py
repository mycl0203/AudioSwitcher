# -*- coding: utf-8 -*-
"""
配置管理模块
负责配置的加载、保存和初始化
"""

import json
import csv
import subprocess
import os
from typing import Optional, Tuple, List
from .paths import path_manager
from .models import AppConfig, AudioDevice, DeviceGroup


class ConfigError(Exception):
    """配置相关异常"""
    pass


class ConfigManager:
    """配置管理器"""
    
    def __init__(self):
        self._config: Optional[AppConfig] = None
    
    def load(self, auto_init: bool = True) -> AppConfig:
        """
        加载配置
        
        Args:
            auto_init: 如果配置不存在是否自动初始化
            
        Returns:
            AppConfig: 应用配置对象
            
        Raises:
            ConfigError: 配置加载失败
        """
        if not os.path.exists(path_manager.sv_exe):
            raise ConfigError(f"缺少 SoundVolumeView.exe，请放到项目根目录: {path_manager.sv_exe}")
        
        # 如果配置文件不存在，自动初始化
        if not os.path.exists(path_manager.config_json):
            if auto_init:
                self.init_first_run()
            else:
                raise ConfigError(f"配置文件不存在: {path_manager.config_json}")
        
        try:
            with open(path_manager.config_json, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
        except Exception as e:
            raise ConfigError(f"配置文件格式错误: {e}")
        
        config = AppConfig.from_dict(data)
        
        # 检查是否需要重新生成设备列表
        if config.regen_config:
            self.generate_device_csv()
            config.regen_config = False
            self.save(config)
        
        self._config = config
        return config
    
    def save(self, config: AppConfig) -> None:
        """
        保存配置
        
        Args:
            config: 应用配置对象
        """
        data = config.to_dict()
        with open(path_manager.config_json, "w", encoding="utf-8-sig") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._config = config
    
    def init_first_run(self) -> None:
        """首次运行初始化 - 生成设备列表和配置模板"""
        self.generate_device_csv()
        
        # 创建默认配置
        default_config = AppConfig()
        self.save(default_config)
    
    def generate_device_csv(self) -> None:
        """
        生成设备CSV文件
        
        Raises:
            ConfigError: 生成失败
        """
        if not os.path.exists(path_manager.sv_exe):
            raise ConfigError("SoundVolumeView.exe 不存在")
        
        try:
            # 导出原始数据
            subprocess.run(
                [path_manager.sv_exe, "/scomma", path_manager.devices_csv],
                creationflags=0x08000000,
                encoding="utf-8",
                check=True
            )
            
            # 过滤数据 - 只保留硬件设备
            filtered_rows = []
            keep_cols = ["Type", "Direction", "Device Name", "Default", "Device State", "Item ID"]
            
            if os.path.exists(path_manager.devices_csv):
                with open(path_manager.devices_csv, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames or []
                    col_indices = {name: idx for idx, name in enumerate(headers)}
                    
                    # 新表头
                    filtered_rows.append(keep_cols)
                    
                    for row in reader:
                        # 只保留硬件设备
                        type_val = row.get("Type", "").strip()
                        if type_val != "Device":
                            continue
                        
                        new_row = []
                        for col in keep_cols:
                            val = row.get(col, "").strip()
                            new_row.append(val)
                        filtered_rows.append(new_row)
            
            # 写入过滤后的数据
            with open(path_manager.devices_csv, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(filtered_rows)
                
        except Exception as e:
            raise ConfigError(f"生成设备列表失败: {e}")
    
    def scan_devices(self) -> Tuple[List[AudioDevice], List[AudioDevice]]:
        """
        扫描所有音频设备
        
        Returns:
            Tuple[List[AudioDevice], List[AudioDevice]]: (输出设备列表, 输入设备列表)
        """
        try:
            subprocess.run(
                [path_manager.sv_exe, "/scomma", path_manager.devices_csv],
                creationflags=0x08000000,
                check=True
            )
        except Exception:
            pass
        
        output_devices = []
        input_devices = []
        
        if os.path.exists(path_manager.devices_csv):
            try:
                with open(path_manager.devices_csv, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        type_val = row.get("Type", "").strip()
                        if type_val != "Device":
                            continue
                        
                        name = row.get("Device Name", "").strip()
                        device_id = row.get("Item ID", "").strip()
                        direction = row.get("Direction", "").strip()
                        
                        if not name or not device_id:
                            continue
                        
                        device = AudioDevice(
                            name=name,
                            device_id=device_id,
                            direction=direction
                        )
                        
                        if direction == "Render":
                            output_devices.append(device)
                        elif direction == "Capture":
                            input_devices.append(device)
            except Exception:
                pass
        
        return output_devices, input_devices
    
    def get_current_devices(self) -> Tuple[Optional[str], Optional[str]]:
        """
        获取当前默认设备ID
        
        Returns:
            Tuple[Optional[str], Optional[str]]: (输出设备ID, 输入设备ID)
        """
        try:
            subprocess.run(
                [path_manager.sv_exe, "/scomma", path_manager.devices_csv],
                creationflags=0x08000000,
                check=True
            )
        except Exception:
            pass
        
        output_id = None
        input_id = None
        
        if os.path.exists(path_manager.devices_csv):
            try:
                with open(path_manager.devices_csv, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        type_val = row.get("Type", "").strip()
                        if type_val != "Device":
                            continue
                        
                        direction = row.get("Direction", "").strip()
                        default = row.get("Default", "").strip().lower()
                        device_id = row.get("Item ID", "").strip().lower()
                        
                        if direction == "Render" and default == "render":
                            output_id = device_id
                        elif direction == "Capture" and default == "capture":
                            input_id = device_id
            except Exception:
                pass
        
        return output_id, input_id
    
    @property
    def config(self) -> Optional[AppConfig]:
        """获取当前配置"""
        return self._config


# 全局配置管理器实例
config_manager = ConfigManager()
