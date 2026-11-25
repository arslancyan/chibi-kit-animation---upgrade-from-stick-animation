"""Make sleeveless shirt cutouts (sleeves are drawn separately on the upper arms).
    python3 -I tools/chibi/prep_clothes.py
Reads assets/clothes/tshirt_front.png / tshirt_back.png, writes *_nosleeve.png next to them."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "clothes")
OUTLINE = (30, 20, 20, 255)

def nosleeve(name):
    im = Image.open(os.path.join(D, name + ".png")).convert("RGBA")
    w, h = im.size
    # keep polygon: vertical-ish body, cut where the sleeves join
    xl0, xl1 = w * 0.25, w * 0.205      # left cut x at top / at hem line
    xr0, xr1 = w * 0.75, w * 0.79
    yc = h * 0.63
    poly = [(xl0, 0), (xr0, 0), (xr1, yc), (w, yc), (w, h), (0, h), (0, yc), (xl1, yc)]
    keep = Image.new("L", (w, h), 0); ImageDraw.Draw(keep).polygon(poly, fill=255)
    # below the hem line keep everything (body only there)
    ImageDraw.Draw(keep).rectangle([0, yc, w, h], fill=255)
    a = np.asarray(im).copy()
    a[..., 3] = (a[..., 3].astype(np.float32) * (np.asarray(keep) / 255.0)).astype(np.uint8)
    out = Image.fromarray(a, "RGBA")
    # outline stroke along the two cut edges, clipped to the kept silhouette
    stroke = Image.new("RGBA", (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(stroke)
    d.line([(xl0, h * 0.02), (xl1, yc)], fill=OUTLINE, width=9)
    d.line([(xr0, h * 0.02), (xr1, yc)], fill=OUTLINE, width=9)
    clip = np.minimum(np.asarray(out)[..., 3], np.asarray(im)[..., 3])
    sa = np.asarray(stroke).copy(); sa[..., 3] = np.minimum(sa[..., 3], clip)
    out = Image.alpha_composite(out, Image.fromarray(sa, "RGBA"))
    out.save(os.path.join(D, name + "_nosleeve.png"))

for n in ("tshirt_front", "tshirt_back"):
    nosleeve(n)
print("ok")
