# -*- coding: utf-8 -*-
"""
音频切换器 - v2.0
现代化UI设计、稳定性提升、功能增强
"""

import sys
import os

# 确保模块路径正确
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
modules_path = os.path.join(BASE_DIR, 'modules')
if modules_path not in sys.path:
    sys.path.insert(0, modules_path)

from modules.ui.app import main

if __name__ == "__main__":
    main()
