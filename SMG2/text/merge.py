import os

def merge_kup_files(root_dir, output_file):
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for foldername, subfolders, filenames in os.walk(root_dir):
            for filename in filenames:
                if filename.lower().endswith('.kup'):
                    file_path = os.path.join(foldername, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(f"// Start of {file_path}\n")  # 可选：标注文件名
                            outfile.write(infile.read())
                            outfile.write(f"\n// End of {file_path}\n\n")
                    except Exception as e:
                        print(f"❌ Error reading {file_path}: {e}")

if __name__ == '__main__':
    current_dir = os.getcwd()  # 获取当前脚本所在目录
    output_filename = 'merged.kup'  # 合并后文件名
    merge_kup_files(current_dir, output_filename)
    print(f"✅ 所有 .kup 文件已合并为：{output_filename}")
