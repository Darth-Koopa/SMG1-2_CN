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
# 配置区域
# ==========================
FOLDER1 = r"SMG1wii"
FOLDER2 = r"SMG1TEXSW"
FOLDER3 = r"out"
CSV_OUT = r"match_results.csv"

IMG_SIZE = 224
THREADS = os.cpu_count() or 8
MIN_SCORE = 0.97     # ★★最低相似度阈值（越接近1越严格）
RATIO_TOL = 0.00     # ★★宽高比例误差允许（3%）

device = "cuda" if torch.cuda.is_available() else "cpu"
print(device)

# 模型加载
model = torch.hub.load('facebookresearch/dinov2', 'dinov2_vitb14').to(device)
model.eval()

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}

# 图像预处理 & 记录比例
def load_img(path):
    try:
        img = Image.open(path).convert("RGB")
        w, h = img.size
        ratio = w / h

        img = img.resize((IMG_SIZE, IMG_SIZE), Image.LANCZOS)
        arr = np.asarray(img).astype(np.float32) / 255.0
        arr = (arr - 0.5) / 0.5
        arr = arr.transpose(2, 0, 1)
        tensor = torch.tensor(arr).unsqueeze(0).to(device)
        return tensor, ratio
    except:
        return None, None

def get_feat(img_tensor):
    with torch.no_grad():
        feat = model(img_tensor)
        feat = F.normalize(feat, dim=-1)
        return feat.squeeze(0).cpu().numpy()

def list_recursive(folder):
    return [p for p in Path(folder).rglob("*") if p.suffix.lower() in IMAGE_EXTS]

def list_flat(folder):
    return [p for p in Path(folder).iterdir() if p.suffix.lower() in IMAGE_EXTS]


# ==========================
# 预加载 Folder2 特征
# ==========================
print("加载 FOLDER2 ...")
files2 = list_flat(FOLDER2)
cand_feats, cand_paths, cand_ratios = [], [], []

for p in tqdm(files2):
    t, r = load_img(p)
    if t is None:
        continue
    cand_feats.append(get_feat(t))
    cand_paths.append(p)
    cand_ratios.append(r)

cand_feats = np.stack(cand_feats)
cand_ratios = np.array(cand_ratios)


# ==========================
# 匹配逻辑
# ==========================
def match_single(path):
    t1, r1 = load_img(path)
    if t1 is None:
        return None

    f1 = get_feat(t1)

    # ★★过滤长宽比例不一致的候选
    mask = np.abs(cand_ratios - r1) <= RATIO_TOL
    if not np.any(mask):
        return None

    cand_feats_f = cand_feats[mask]
    cand_paths_f = np.array(cand_paths)[mask]

    # 初筛：取最高相似度
    sims = cand_feats_f @ f1
    idx = np.argmax(sims)
    score1 = sims[idx]
    match1 = cand_paths_f[idx]

    # 阈值检查：低于不匹配
    if score1 < MIN_SCORE:
        return None

    # ★★二次严格匹配（防止错配）
    # 取匹配图的特征再算一遍相似度校验
    t2, _ = load_img(match1)
    f2 = get_feat(t2)
    score2 = float(f2 @ f1)

    score = min(score1, score2)
    if score < MIN_SCORE:
        return None

    # 通过 → 复制文件保持结构
    rel = path.relative_to(FOLDER1)
    out_path = Path(FOLDER3) / rel.parent
    out_path.mkdir(parents=True, exist_ok=True)
    shutil.copy2(match1, out_path / path.name)

    return str(path), str(match1), float(score)


# ==========================
# 开始多线程匹配
# ==========================
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
pd.DataFrame(results, columns=["source", "matched", "score"]) \
    .to_csv(CSV_OUT, index=False, encoding="utf-8-sig")

print("完成！匹配数量:", len(results))
print("结果已保存:", CSV_OUT)
print("输出目录:", FOLDER3)
