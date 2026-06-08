# AudioSwitcher 3 打包说明

## 快速打包
### 使用一键脚本（推荐）
```bash
# 直接运行打包脚本
build_and_push.bat
```

### 手动打包步骤
1. 生成应用图标
```bash
python make_icon.py
```

2. 安装PyInstaller
```bash
pip install pyinstaller
```

3. 打包应用
```bash
pyinstaller --onefile --windowed --name "AudioSwitcher" --icon=icon.ico --add-data "SoundVolumeView.exe;." --add-data "icon.ico;." main.py
```

4. 生成的可执行文件位于 `dist/AudioSwitcher.exe`

## 打包选项说明
- `--onefile`: 将所有依赖打包到单个exe文件
- `--windowed`: 无控制台窗口，适合GUI应用
- `--name`: 生成的可执行文件名称
- `--icon`: 应用图标
- `--add-data`: 需要打包的附加文件

## 推送到Git
```bash
git add -A
git commit -m "更新内容"
git push
```
