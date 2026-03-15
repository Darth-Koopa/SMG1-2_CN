import os
from pathlib import Path

def replace_bytes_in_msbt_files(source_dir, target_dir):
    source_dir = Path(source_dir)
    target_dir = Path(target_dir)

    # 十六进制字节
    old_bytes = bytes.fromhex('32545854')  
    new_bytes = bytes.fromhex('54585432')  

    for file_path in source_dir.rglob('*.msbt'):
        # 计算目标文件路径
        relative_path = file_path.relative_to(source_dir)
        target_file_path = target_dir / relative_path

        # 确保目标子目录存在
        target_file_path.parent.mkdir(parents=True, exist_ok=True)

        # 读取原始二进制数据
        with open(file_path, 'rb') as f:
            content = f.read()

        # 替换十六进制字节
        modified_content = content.replace(old_bytes, new_bytes)

        # 保存到目标路径
        with open(target_file_path, 'wb') as f:
            f.write(modified_content)

        print(f"Processed: {file_path} -> {target_file_path}")

if __name__ == '__main__':
    # 示例路径（你可以换成自己的路径）
    folder1 = '1'
    folder2 = '2'

    replace_bytes_in_msbt_files(folder1, folder2)
