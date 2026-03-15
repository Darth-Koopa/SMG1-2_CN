import os
import shutil
import hashlib

# ====== 配置路径 ======
folder_a = r"C:\Users\BobDi\Desktop\romfs\100FD8022DAA000\Romfs\data\texture_replace\MarioGalaxy_Sub"
folder_b = r"C:\Users\BobDi\Desktop\romfs\MarioGalaxy_Sub"
output_root = r"C:\Users\BobDi\Desktop\romfs"

only_a_dir = os.path.join(output_root, "only_in_A")
only_b_dir = os.path.join(output_root, "only_in_B")
same_name_diff_dir = os.path.join(output_root, "same_name_diff_contentA")
same_name_diff_dirB = os.path.join(output_root, "same_name_diff_contentB")
for d in [only_a_dir, only_b_dir, same_name_diff_dir, same_name_diff_dirB]:
    os.makedirs(d, exist_ok=True)


# ====== MD5 计算函数 ======
def file_md5(path):
    md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            md5.update(chunk)
    return md5.hexdigest()

# ====== 获取文件集合（只比较文件，不管文件夹） ======
files_a = {f for f in os.listdir(folder_a)
           if os.path.isfile(os.path.join(folder_a, f))}
files_b = {f for f in os.listdir(folder_b)
           if os.path.isfile(os.path.join(folder_b, f))}

# ====== 1. 文件名不同 ======
only_in_a = files_a - files_b
only_in_b = files_b - files_a

for f in only_in_a:
    shutil.copy2(
        os.path.join(folder_a, f),
        os.path.join(only_a_dir, f)
    )

for f in only_in_b:
    shutil.copy2(
        os.path.join(folder_b, f),
        os.path.join(only_b_dir, f)
    )

# ====== 2. 文件名相同但内容不同 ======
common_files = files_a & files_b

for f in common_files:
    path_a = os.path.join(folder_a, f)
    path_b = os.path.join(folder_b, f)

    if file_md5(path_a) != file_md5(path_b):

        shutil.copy2(
            path_a,
            os.path.join(same_name_diff_dir, f)
        )
        shutil.copy2(
            path_b,
            os.path.join(same_name_diff_dirB, f)
        )

print("完成：差异文件已按类型分别复制")
