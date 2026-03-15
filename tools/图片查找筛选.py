import cv2
import os

sample_path = "sample.png"
folder_path = r"E:\~SMG\ObjectData"
top_n = 10

def calc_similarity(img1_path, img2_path):
    try:
        img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)
        sift = cv2.SIFT_create()
        kp1, des1 = sift.detectAndCompute(img1, None)
        kp2, des2 = sift.detectAndCompute(img2, None)
        bf = cv2.BFMatcher()
        matches = bf.knnMatch(des1, des2, k=2)
        good = [m for m, n in matches if m.distance < 0.75 * n.distance]
        return len(good) / max(len(kp1), len(kp2))
    except:
        return 0

results = []
for root, dirs, files in os.walk(folder_path):
    for file in files:
        if file.lower().endswith(('.jpg', '.jpeg', '.png')):
            path = os.path.join(root, file)
            print("正在运行:", path)

            score = calc_similarity(sample_path, path)
            rel_path = os.path.relpath(path, folder_path)  # 输出相对路径更清晰

            results.append((rel_path, score))

results.sort(key=lambda x: x[1], reverse=True)
print("\n最相似的图片：")
for name, sim in results[:top_n]:
    print(f"{name} -> 相似度: {sim:.2f}")
