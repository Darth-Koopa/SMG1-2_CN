import os
from collections import defaultdict

# 要检查的根目录
root_dir = r"E:\hi-res smg1"   # ← 改成你的文件夹路径

# 用字典记录：filename -> [path1, path2, ...]
files_map = defaultdict(list)

# 遍历文件夹和子文件夹
for root, dirs, files in os.walk(root_dir):
    for file in files:
        full_path = os.path.join(root, file)
        files_map[file].append(full_path)

# 输出重名文件
has_duplicates = False
print("===== 重名文件检查结果 =====\n")

for filename, paths in files_map.items():
    if len(paths) > 1:
        has_duplicates = True
        print(f"文件名: {filename}")
        for p in paths:
            print(f"  - {p}")
        print()

if not has_duplicates:
    print("未发现重名文件 🎉")
