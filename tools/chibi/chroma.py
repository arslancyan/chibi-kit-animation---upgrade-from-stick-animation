"""Chroma-key a green-screen sheet into an RGBA image and slice it into parts.
Usage: python3 -I tools/chibi/chroma.py <sheet.png|webp> <out_dir> [--min-area N] [--rows R] [--names a,b,c]
--rows R: sort parts row-major using R row bands (default: column-major). --names: file names in sorted order.
Writes full_rgba.png and part_XX.png plus parts.json (bbox of each part in sheet pixels)."""
import sys, json, os
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

def key(im):
    a = np.asarray(im.convert("RGB")).astype(np.float32)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    spill = g - np.maximum(r, b)
    alpha = 1.0 - np.clip(spill / 200.0, 0, 1)
    alpha = np.where(spill > 200, 0.0, alpha)
    g2 = np.minimum(g, np.maximum(r, b) + 4)       # despill
    out = np.dstack([r, g2, b, alpha * 255]).clip(0, 255).astype(np.uint8)
    return Image.fromarray(out, "RGBA")

def slice_parts(rgba, min_area=1500):
    al = np.asarray(rgba)[..., 3] > 128
    lab, n = ndi.label(al)
    parts = []
    for i, sl in enumerate(ndi.find_objects(lab), start=1):
        area = int((lab[sl] == i).sum())
        if area < min_area:
            continue
        y0, y1, x0, x1 = sl[0].start, sl[0].stop, sl[1].start, sl[1].stop
        m = (lab == i)
        arr = np.asarray(rgba).copy()
        arr[..., 3] = np.where(ndi.binary_dilation(m, iterations=3), arr[..., 3], 0)
        crop = Image.fromarray(arr[y0:y1, x0:x1], "RGBA")
        parts.append(dict(bbox=[x0, y0, x1, y1], area=area, img=crop))
    return parts

if __name__ == "__main__":
    src, out = sys.argv[1], sys.argv[2]
    ma = int(sys.argv[sys.argv.index("--min-area") + 1]) if "--min-area" in sys.argv else 1500
    os.makedirs(out, exist_ok=True)
    rgba = key(Image.open(src))
    rgba.save(os.path.join(out, "full_rgba.png"))
    parts = slice_parts(rgba, ma)
    if "--rows" in sys.argv:
        R = int(sys.argv[sys.argv.index("--rows") + 1]); H = rgba.size[1]
        parts.sort(key=lambda p: ((p["bbox"][1] + p["bbox"][3]) / 2 // (H / R), p["bbox"][0]))
    else:
        parts.sort(key=lambda p: (p["bbox"][0] // 100, p["bbox"][1]))
    names = sys.argv[sys.argv.index("--names") + 1].split(",") if "--names" in sys.argv else []
    meta = []
    for i, p in enumerate(parts):
        fn = (names[i] if i < len(names) else f"part_{i:02d}") + ".png"
        p["img"].save(os.path.join(out, fn))
        meta.append(dict(file=fn, bbox=p["bbox"], area=p["area"]))
    json.dump(meta, open(os.path.join(out, "parts.json"), "w"), indent=1)
    print(len(meta), "parts")
    for m in meta: print(m)
