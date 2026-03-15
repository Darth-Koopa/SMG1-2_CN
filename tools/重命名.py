import os
import shutil
import csv
import re

print("文件重命名工具")
print("mode1：A/B 原版模式")
print("mode2：LOD → 批量 MIP 模式")
print("输入 stop 退出程序\n")

records = []
csv_path = "rename_log.csv"

mode = "mode1"
current_c = None

while True:
    # ======================
    # MODE 1（原版）
    # ======================
    if mode == "mode1":
        a = input("拖入 文件A（作为新名字）：").strip()

        if a.lower() == "stop":
            break
        if a.lower() == "mode2":
            mode = "mode2"
            current_c = None
            print("🔁 已切换到 mode2\n")
            continue

        b = input("拖入 文件B（将被重命名）：").strip()
        if b.lower() == "stop":
            break

        a = a.strip('"')
        b = b.strip('"')

        if not os.path.isfile(a) or not os.path.isfile(b):
            print("❌ 文件不存在\n")
            continue

        a_name = os.path.basename(a)
        b_name = os.path.basename(b)

        records.append({
            "A_path": a,
            "A_name": a_name,
            "B_path": b,
            "B_name": b_name
        })

        new_path = os.path.join(os.path.dirname(b), a_name)

        if os.path.exists(new_path):
            print("⚠️ 目标文件已存在，跳过\n")
            continue

        shutil.move(b, new_path)
        print(f"✅ 已重命名：{a_name}\n")

    # ======================
    # MODE 2（批量 LOD）
    # ======================
    else:
        # ---- 拖入 C ----
        if current_c is None:
            c = input("拖入 文件C：").strip()

            if c.lower() == "stop":
                break
            if c.lower() == "mode1":
                mode = "mode1"
                print("🔁 已切换回 mode1\n")
                continue

            c = c.strip('"')
            if not os.path.isfile(c):
                print("❌ 文件C不存在\n")
                continue

            current_c = c
            print("✅ 已记录文件C\n")
            continue

        # ---- 拖入 任意 lod 文件D ----
        d = input("拖入 任意一个带 lod 的文件D：").strip()

        if d.lower() == "stop":
            break
        if d.lower() == "mode1":
            mode = "mode1"
            current_c = None
            print("🔁 已切换回 mode1\n")
            continue
        if d.lower() == "mode2":
            current_c = None
            print("🔁 重新拖入文件C\n")
            continue

        d = d.strip('"')
        if not os.path.isfile(d):
            print("❌ 文件D不存在\n")
            continue

        d_dir = os.path.dirname(d)
        d_name = os.path.basename(d)

        match = re.search(r"(.+?)_lod(\d+)", d_name, re.IGNORECASE)
        if not match:
            print("❌ 文件名中未找到 lod，重新拖入文件D\n")
            continue

        lod_prefix = match.group(1)

        c_base, c_ext = os.path.splitext(os.path.basename(current_c))

        # 搜索同前缀的所有 lod 文件
        lod_files = []
        for f in os.listdir(d_dir):
            m = re.match(rf"{re.escape(lod_prefix)}_lod(\d+)\{c_ext}$", f, re.IGNORECASE)
            if m:
                lod_files.append((f, m.group(1)))

        if not lod_files:
            print("❌ 未找到任何 lod 文件\n")
            continue

        for old_name, lod_num in lod_files:
            old_path = os.path.join(d_dir, old_name)
            new_name = f"{c_base}_mip{lod_num}{c_ext}"
            new_path = os.path.join(d_dir, new_name)

            records.append({
                "A_path": new_path,
                "A_name": new_name,
                "B_path": old_path,
                "B_name": old_name
            })

            if os.path.exists(new_path):
                print(f"⚠️ 已存在，跳过：{new_name}")
                continue

            shutil.move(old_path, new_path)
            print(f"✅ {old_name} → {new_name}")

        print("\n🔁 批量完成，继续拖入新的 文件C\n")
        current_c = None

# ======================
# 写入 CSV
# ======================
if records:
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["A_path", "A_name", "B_path", "B_name"]
        )
        writer.writeheader()
        writer.writerows(records)

    print(f"📄 已保存记录到 {csv_path}")

print("程序已终止")
