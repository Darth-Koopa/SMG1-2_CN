import cv2
import os
import csv

mario_folder = r"E:\hi-res smg1\ondemand_texture_replace\MarioGalaxy"
object_folder = r"E:\~SMG\ObjectData"
output_csv = r"E:\match_result.csv"
top_n = 10


# 读取图片 → HSV → 直方图 → 归一化，并返回直方图+图像尺寸
def load_image_feature(img_path):
    img = cv2.imread(img_path)
    if img is None:
        return None, None, None

    h, w = img.shape[:2]  # 记录尺寸

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    hist = cv2.calcHist(
        [hsv], [0, 1, 2], None,
        [50, 60, 60],
        [0, 180, 0, 256, 0, 256]
    )
    cv2.normalize(hist, hist)

    return hist, w, h  # 返回直方图 + 宽 + 高


# ---------------------------------------------------------
# STEP 1：加载 ObjectData 全部图片 → 预计算特征（直方图）
# ---------------------------------------------------------
object_features = []  # (relative_path, histogram, width, height)

print("正在预计算 ObjectData 直方图...")

for root, dirs, files in os.walk(object_folder):
    for file in files:
        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
            full = os.path.join(root, file)
            rel = os.path.relpath(full, object_folder)

            hist, w, h = load_image_feature(full)
            if hist is not None:
                object_features.append((rel, hist, w, h))

print(f"预计算完成！共 {len(object_features)} 张图片\n")


# ---------------------------------------------------------
# STEP 2：对 MarioGalaxy 文件匹配（只计算 sample 的直方图）
# ---------------------------------------------------------
with open(output_csv, 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(["sample_file", "matched_file", "similarity"])

    for sample_file in os.listdir(mario_folder):

        # 只处理图片
        if not sample_file.lower().endswith(('.jpg', '.jpeg', '.png')):
            continue

        sample_path = os.path.join(mario_folder, sample_file)
        print("=" * 60)
        print("当前 Sample：", sample_file)
        print("=" * 60)

        sample_hist, sample_w, sample_h = load_image_feature(sample_path)
        if sample_hist is None:
            print("读取失败，跳过\n")
            continue

        results = []

        # 遍历 ObjectData 特征
        for rel_path, obj_hist, obj_w, obj_h in object_features:

            # --------------------------
            # 尺寸过滤：object 要 ≤ sample
            # --------------------------
            if obj_w > sample_w or obj_h > sample_h:
                continue

            # 做直方图相似度比较
            sim = cv2.compareHist(sample_hist, obj_hist, cv2.HISTCMP_CORREL)
            results.append((rel_path, sim))

        # 排序
        results.sort(key=lambda x: x[1], reverse=True)

        # 输出前 N
        for name, sim in results[:top_n]:
            print(f"{name}  -> 相似度 {sim:.3f}")
            writer.writerow([sample_file, name, f"{sim:.4f}"])

        print("\n")

print(f"CSV 已导出：{output_csv}")
