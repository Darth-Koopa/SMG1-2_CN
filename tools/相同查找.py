import os
import hashlib
import csv

def file_hash(path, chunk_size=8192):
    """计算文件 SHA256"""
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def scan_folder(folder):
    """
    扫描文件夹（含子文件夹）
    返回：hash -> [file_path, ...]
    """
    hash_map = {}

    for root, _, files in os.walk(folder):
        for name in files:
            path = os.path.join(root, name)
            try:
                h = file_hash(path)
                hash_map.setdefault(h, []).append(path)
            except Exception as e:
                print(f"跳过无法读取的文件: {path} ({e})")

    return hash_map


def find_same_files(folder_a, folder_b, output_csv):
    print("扫描文件夹 A...")
    map_a = scan_folder(folder_a)

    print("扫描文件夹 B...")
    map_b = scan_folder(folder_b)

    same_files = []

    for h in map_a:
        if h in map_b:
            for pa in map_a[h]:
                for pb in map_b[h]:
                    same_files.append([pa, pb])

    print(f"找到 {len(same_files)} 对相同文件")

    with open(output_csv, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["path_in_A", "path_in_B"])
        writer.writerows(same_files)

    print(f"结果已导出到: {output_csv}")


if __name__ == "__main__":
    folder_a = input("拖入文件夹 A 并回车: ").strip('"')
    folder_b = input("拖入文件夹 B 并回车: ").strip('"')
    output_csv = "same_files.csv"

    find_same_files(folder_a, folder_b, output_csv)
