import struct
import os
from pathlib import Path

def swap_byte_pairs(data: bytes) -> bytes:
    """每两个字节交换位置"""
    swapped = bytearray()
    for i in range(0, len(data), 2):
        pair = data[i:i+2]
        if len(pair) == 2:
            swapped.extend([pair[1], pair[0]])
        else:
            swapped.extend(pair)  # 奇数长度，最后一个字节不变
    return bytes(swapped)

def process_hex_data(hex_data: bytes) -> bytes:
    marker = b'\x54\x58\x54\x32'  # TXT2
    pos = hex_data.find(marker)
    if pos == -1:
        raise ValueError("找不到标志头 TXT2")

    #print(f"标志头位置：{pos}")

    next_line_pos = pos + 16  # 下一行开头
    offset_bytes = hex_data[next_line_pos:next_line_pos+4]
    offset = struct.unpack('<I', offset_bytes)[0]

    #print(f"偏移量（4字节单位）：{offset}")

    start_pos = next_line_pos + 4 + offset * 4
    if start_pos >= len(hex_data):
        raise ValueError("计算出的处理起始位置超过数据长度")

    #print(f"数据处理起始位置：{start_pos}")

    # 处理从start_pos到文件末尾的内容
    data_to_process = hex_data[start_pos:]
    processed_part = swap_byte_pairs(data_to_process)

    # 返回拼接结果：文件开头到start_pos未变 + 处理后的部分
    return hex_data[:start_pos] + processed_part

def function(source_dir, target_dir):
    source_dir = Path(source_dir)
    target_dir = Path(target_dir)

    for file_path in source_dir.rglob('*.msbt'):
        # 计算目标文件路径
        relative_path = file_path.relative_to(source_dir)
        target_file_path = target_dir / relative_path

        # 确保目标子目录存在
        target_file_path.parent.mkdir(parents=True, exist_ok=True)

        # 读取原始二进制数据
        with open(file_path, 'rb') as f:
            data = f.read()
            
        # 处理
        processed = process_hex_data(data)
        
        # 保存为 .bak，二进制写入
        with open(target_file_path, 'wb') as f:
            f.write(processed)

        print(f"Processed: {file_path} -> {target_file_path}")

if __name__ == '__main__':
    # 示例路径（你可以换成自己的路径）
    folder1 = '1'
    folder2 = '2'

    function(folder1, folder2)
