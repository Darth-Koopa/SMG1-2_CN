import os
from pathlib import Path
import shutil
import numpy as np
from PIL import Image
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import torch
import torch.nn.functional as F

# ==========================
# 配置区域（修改这里）
# ==========================
FOLDER1 = r"SMG1wii"       # 原始图片，深层目录
FOLDER2 = r"SMG1TEXSW"       # 单层图片目录
FOLDER3 = r"out"       # 输出目录
CSV_OUT = r"match_results.csv"

IMG_SIZE = 224
THREADS = os.cpu_count() or 8
# ==========================

device = "cuda" if torch.cuda.is_available() else "cpu"

# 载入 DINOv2（严格匹配模型）
model = torch.hub.load('facebookresearch/dinov2', 'dinov2_vitb14').to(device)
model.eval()

# 图像预处理
def load_img(path):
    try:
        img = Image.open(path).convert("RGB")
        img = img.resize((IMG_SIZE, IMG_SIZE), Image.LANCZOS)
        arr = np.asarray(img).astype(np.float32) / 255.0
        arr = (arr - 0.5) / 0.5
        arr = arr.transpose(2, 0, 1)  # HWC → CHW
        tensor = torch.tensor(arr).unsqueeze(0).to(device)
        return tensor
    except:
        return None

# 特征向量提取（L2 normalize）
def get_feat(img_tensor):
    with torch.no_grad():
        feat = model(img_tensor)
        feat = F.normalize(feat, dim=-1)
        return feat.squeeze(0).cpu().numpy()

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}

def list_recursive(folder):
    return [p for p in Path(folder).rglob("*") if p.suffix.lower() in IMAGE_EXTS]

def list_flat(folder):
    return [p for p in Path(folder).iterdir() if p.suffix.lower() in IMAGE_EXTS]

# ========================
# 预加载 folder2 特征
# ========================
files2 = list_flat(FOLDER2)
cand_feats = []
cand_paths = []

print("加载 FOLDER2 ...")
for p in tqdm(files2):
    t = load_img(p)
    if t is None:
        continue
    feat = get_feat(t)
    cand_feats.append(feat)
    cand_paths.append(p)

cand_feats = np.stack(cand_feats)


# ========================
# 匹配函数（线程内调用）
# ========================
def match_single(path):
    t = load_img(path)
    if t is None:
        return None
    f1 = get_feat(t)

    # 逐张比对（严格）
    sims = cand_feats @ f1
    idx = sims.argmax()
    score = sims[idx]
    matched = cand_paths[idx]

    # 复制文件
    rel = path.relative_to(FOLDER1)
    out_path = Path(FOLDER3) / rel.parent
    out_path.mkdir(parents=True, exist_ok=True)
    shutil.copy2(matched, out_path / path.name)

    return str(path), str(matched), float(score)


# ========================
# 主调度（多线程）
# ========================
files1 = list_recursive(FOLDER1)
Path(FOLDER3).mkdir(parents=True, exist_ok=True)

results = []
print("开始严格匹配（多线程）...")

with ThreadPoolExecutor(max_workers=THREADS) as exe:
    futures = {exe.submit(match_single, p): p for p in files1}

    for fut in tqdm(as_completed(futures), total=len(files1)):
        r = fut.result()
        if r:
            results.append(r)

# 保存 CSV
df = pd.DataFrame(results, columns=["source", "matched", "score"])
df.to_csv(CSV_OUT, index=False, encoding="utf-8-sig")

print("完成！结果已保存：", CSV_OUT)
print("输出目录：", FOLDER3)
