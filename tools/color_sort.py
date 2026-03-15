import os
import shutil
from PIL import Image
import colorsys

# --- 配置 ---
SOURCE_DIR = r'C:\Users\BobDi\Desktop\romfs\ObjectData'  # 替换为你的源文件夹
TARGET_DIR = r'C:\Users\BobDi\Desktop\romfs\新建文件夹'       # 结果存放路径
EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

# 定义颜色区间 (H: 0-360)
# 基于颜色学对必应 12 色的大致划分
COLOR_MAP = {
    '红色': (0, 10),
    '橙色': (11, 40),
    '黄色': (41, 70),
    '绿色': (71, 150),
    '青色': (151, 190),
    '蓝色': (191, 250),
    '紫色': (251, 290),
    '粉色': (291, 330),
    '红色2': (331, 360), # 红色在色轮两端
}

def get_dominant_color(pil_img):
    """获取图片的主导颜色名称"""
    # 缩小图片尺寸以提高计算速度
    img = pil_img.copy()
    img.thumbnail((50, 50))
    img = img.convert('RGB')
    
    # 统计所有像素的平均 RGB
    pixels = list(img.getdata())
    r, g, b = 0, 0, 0
    n = len(pixels)
    for pix in pixels:
        r += pix[0]
        g += pix[1]
        b += pix[2]
    
    avg_r, avg_g, avg_b = r/n, g/n, b/n
    
    # 转换为 HSV
    # h(色相), s(饱和度), v(明度)
    h, s, v = colorsys.rgb_to_hsv(avg_r/255, avg_g/255, avg_b/255)
    h *= 360
    
    # 逻辑判断：黑色、白色、灰色 (根据饱和度和明度)
    if v < 0.2: return '黑色'
    if v > 0.8 and s < 0.1: return '白色'
    if s < 0.15: return '灰色'
    
    # 逻辑判断：棕色 (通常是暗橙色)
    if 10 < h < 45 and s > 0.2 and v < 0.5: return '棕色'

    # 根据色相 H 分类
    for name, (low, high) in COLOR_MAP.items():
        if low <= h <= high:
            return '红色' if name == '红色2' else name
            
    return '其他'

def sort_images():
    if not os.path.exists(TARGET_DIR):
        os.makedirs(TARGET_DIR)

    for root, dirs, files in os.walk(SOURCE_DIR):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in EXTENSIONS:
                img_path = os.path.join(root, file)
                try:
                    with Image.open(img_path) as img:
                        color_name = get_dominant_color(img)
                    
                    # 创建颜色文件夹
                    save_path = os.path.join(TARGET_DIR, color_name)
                    if not os.path.exists(save_path):
                        os.makedirs(save_path)
                    
                    # 复制文件 (避免破坏原文件)
                    shutil.copy(img_path, os.path.join(save_path, file))
                    print(f"已分类: {file} -> {color_name}")
                except Exception as e:
                    print(f"处理失败 {file}: {e}")

if __name__ == "__main__":
    sort_images()
