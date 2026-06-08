# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

size = 256
icon = Image.new('RGBA', (size, size), (46, 204, 113, 255))
draw = ImageDraw.Draw(icon)

border_size = 20
draw.ellipse(
    [border_size, border_size, size-border_size, size-border_size],
    outline=(255,255,255,255),
    width=8
)

center = size//2
left_x = center-90
draw.ellipse([left_x-25, center-25, left_x+25, center+25], fill=(255,255,255,255))

right_x = center+90
draw.ellipse([right_x-25, center-25, right_x+25, center+25], fill=(255,255,255,255))

draw.line([left_x+25, center, right_x-25, center], fill=(255,255,255,255), width=8)

icon.save(os.path.join(BASE_DIR, 'icon.png'), 'PNG')
icon.save(os.path.join(BASE_DIR, 'icon.ico'), 'ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])

print('图标创建完成')
