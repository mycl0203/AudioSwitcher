@echo off
echo ==========================================
echo AudioSwitcher 3 打包脚本
echo ==========================================
echo.

echo [1/4] 创建应用图标...
python -c "from PIL import Image, ImageDraw; import os; size=256; icon=Image.new('RGBA',(size,size),(46,204,113,255)); draw=ImageDraw.Draw(icon); border_size=20; draw.ellipse([border_size,border_size,size-border_size,size-border_size],outline=(255,255,255,255),width=8); center=size//2; left_x=center-90; draw.ellipse([left_x-25,center-25,left_x+25,center+25],fill=(255,255,255,255)); right_x=center+90; draw.ellipse([right_x-25,center-25,right_x+25,center+25],fill=(255,255,255,255)); draw.line([left_x+25,center,right_x-25,center],fill=(255,255,255,255),width=8); icon.save('icon.png','PNG'); icon.save('icon.ico','ICO',sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)]); print('图标创建成功')"

echo.
echo [2/4] 检查PyInstaller...
python -m pip install pyinstaller

echo.
echo [3/4] 开始打包...
pyinstaller --onefile --windowed --name "AudioSwitcher" --icon=icon.ico --add-data "SoundVolumeView.exe;." --add-data "icon.ico;." main.py

echo.
echo [4/4] 提交并推送到Git...
git add -A
git commit -m "更新：新增设备组UI重构、优化窗口尺寸、完善依赖文档"
git push

echo.
echo ==========================================
echo 打包和推送完成！
echo 可执行文件位置：dist\AudioSwitcher.exe
echo ==========================================
pause
