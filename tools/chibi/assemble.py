"""Chibi character assembler: builds a posed character from the cutouts in assets/.

    python3 -I tools/chibi/assemble.py --out out.png [--expr smirk] [--pose rest|wave|walk|think] [--hair on|off]
    from tools.chibi.assemble import Character; Character().render(pose, expr, size=(1080,1920), scale=1.3)

Conventions
- Anatomical sides: R is the character's right = viewer's left in a front view.
- Angles are degrees, clockwise on screen is positive. 0 = rest (limbs hang straight down).
  For the R (viewer-left) arm a positive shoulder angle swings it outward; for the L arm a negative one does.
- Joint angles are cumulative down a chain: forearm angle is relative to the upper arm.
"""
import json, math, os, argparse
import numpy as np
from PIL import Image

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
A = os.path.join(ROOT, "assets")

# Tunable fit values (sheet pixels, in the scale of assets/base_body/parts)
FIT = dict(
    shoulder=dict(R=(32, 66), L=(213, 66)),
    arm_s=0.85,      # in torso-local px
    hip=dict(R=(78, 262), L=(167, 262)),
    neck_socket=(122, 16),
    head_w=420,                                   # expression heads are scaled to this width
    shirt=dict(s=0.84, anchor=(234, 44), at=(122, 10)),
    sleeve=dict(len=0.78, dx=0, dy=-6),
    ankle_row=118, foot_follow=0.35,    # shirt-local point -> torso-local point
    shorts=dict(s=0.88, anchor=(245, 20), at=(122, 168)),
    hair_front=dict(s=0.93, anchor=(240, 215), at=(0.5, 0.18)),   # at = fraction of head w/h
    hair_back=dict(s=0.93, anchor=(220, 230), at=(0.5, 0.42)),
    watch=dict(s=0.34, back=34),
    sandal=dict(s=0.66),
)

def load(*p):
    return Image.open(os.path.join(A, *p)).convert("RGBA")

def axis_ends(im, frac=0.12):
    """prox/dist ends of a piece along its long axis (prox = upper end)."""
    a = np.asarray(im)[..., 3]; ys, xs = np.nonzero(a > 128)
    pts = np.c_[xs, ys].astype(float); c = pts.mean(0)
    ax = np.linalg.svd(pts - c, full_matrices=False)[2][0]
    if ax[1] < 0: ax = -ax
    t = (pts - c) @ ax; lo, hi = t.min(), t.max()
    return pts[t < lo + frac * (hi - lo)].mean(0), pts[t > hi - frac * (hi - lo)].mean(0)

def split_rows(im, y0, y1):
    """copy of im keeping only rows y0 <= y < y1 (same canvas size)"""
    a = np.asarray(im).copy(); a[:y0] = 0; a[y1:] = 0
    return Image.fromarray(a, "RGBA")

class Rig:
    def __init__(self):
        r = json.load(open(os.path.join(A, "base_body", "rig.json")))["parts"]
        self.meta = r

    def align(self, name):
        """Rotation that makes the piece's prox->dist axis point straight down."""
        m = self.meta[name]
        vx, vy = m["dist"][0] - m["prox"][0], m["dist"][1] - m["prox"][1]
        return 90.0 - math.degrees(math.atan2(vy, vx))

class Character:
    def __init__(self, hair=True, clothes=True, expr_dir=None):
        self.rig = Rig(); self.hair = hair; self.clothes = clothes
        self.img = {}
        for n in self.rig.meta:
            self.img[n] = load("base_body", "parts", n + ".png")
        self.expr_dir = expr_dir or os.path.join(A, "faces", "expressions")
        self._cache = {}

    def expr(self, name):
        if name not in self._cache:
            im = Image.open(os.path.join(self.expr_dir, name + ".png")).convert("RGBA")
            s = FIT["head_w"] / im.width
            self._cache[name] = im.resize((FIT["head_w"], int(im.height * s)), Image.LANCZOS)
        return self._cache[name]

    # ---- drawing helper -------------------------------------------------
    def _draw(self, canvas, im, local_pt, world_pt, phi, s):
        """Paste im so that local_pt lands on world_pt, rotated phi degrees clockwise, scaled by s."""
        p = math.radians(phi); c, sn = math.cos(p), math.sin(p)
        a, b = c / s, sn / s
        d, e = -sn / s, c / s
        cx = local_pt[0] - (a * world_pt[0] + b * world_pt[1])
        cy = local_pt[1] - (d * world_pt[0] + e * world_pt[1])
        layer = im.transform(canvas.size, Image.AFFINE, (a, b, cx, d, e, cy), resample=Image.BICUBIC)
        canvas.alpha_composite(layer)

    @staticmethod
    def _fwd(origin, phi, s, v):
        p = math.radians(phi)
        return (origin[0] + s * (math.cos(p) * v[0] - math.sin(p) * v[1]),
                origin[1] + s * (math.sin(p) * v[0] + math.cos(p) * v[1]))

    def render(self, pose=None, expr="neutral", size=(1080, 1920), scale=1.3, origin=None):
        P = dict(torso_x=0, torso_y=0, torso=0, neck=0, head=0,
                 shoulder_R=4, elbow_R=0, shoulder_L=-4, elbow_L=0,
                 hip_R=0, knee_R=0, hip_L=0, knee_L=0)
        P.update(pose or {})
        s = scale; rig = self.rig; M = rig.meta
        canvas = Image.new("RGBA", size, (0, 0, 0, 0))
        # torso top-left in world; hips at ~ 60% of canvas height by default
        ox, oy = origin or (size[0] / 2, size[1] * 0.44)
        ox += P["torso_x"] * s; oy += P["torso_y"] * s
        tphi = P["torso"]
        tor_pt = (122, 150)                        # torso-local pivot used as rotation centre
        T = (ox, oy)                               # world position of tor_pt
        def tw(v):                                 # torso-local -> world
            return self._fwd(T, tphi, s, (v[0] - tor_pt[0], v[1] - tor_pt[1]))

        draws = []   # (z, callable)
        def add(z, fn): draws.append((z, fn))

        # ----- legs -----
        for side in ("R", "L"):
            hip = tw(FIT["hip"][side]); phi_t = P["hip_" + side] + tphi * 0
            thigh = "thigh_" + side; ll = "lower_leg_" + side
            ph = phi_t + rig.align(thigh)
            knee = self._fwd(hip, ph, s, (M[thigh]["dist"][0] - M[thigh]["prox"][0], M[thigh]["dist"][1] - M[thigh]["prox"][1]))
            pk = P["hip_" + side] + P["knee_" + side]
            add(10, lambda t=thigh, h=hip, ph=ph: self._draw(canvas, self.img[t], M[t]["prox"], h, ph, s))
            ar = FIT["ankle_row"]; full = self.img[ll]
            fa_ = np.asarray(full)[..., 3] > 128
            xs = np.nonzero(fa_[100])[0]; ax_ = ((xs.min() + xs.max()) / 2.0, float(ar))
            shaft, foot = split_rows(full, 0, ar + 4), split_rows(full, ar, full.height)
            add(9, lambda sh_=shaft, k=knee, pk=pk, ll=ll: self._draw(canvas, sh_, M[ll]["prox"], k, pk, s))
            ankle = self._fwd(knee, pk, s, (ax_[0] - M[ll]["prox"][0], ax_[1] - M[ll]["prox"][1]))
            pfoot = pk * FIT["foot_follow"]
            add(11, lambda f_=foot, an=ankle, pf=pfoot, ax_=ax_: self._draw(canvas, f_, ax_, an, pf, s))
            if self.clothes:
                sz = M[ll]["size"]
                off = (sz[0] / 2 + (8 if side == "R" else -8) - ax_[0], sz[1] - 52 - ax_[1])
                sand = load("clothes", "sandal_A.png" if side == "R" else "sandal_B.png")
                spt = self._fwd(ankle, pfoot, s, off)
                add(12, lambda sa=sand, sp_=spt, pf=pfoot: self._draw(canvas, sa, (sa.width / 2, sa.height * 0.62), sp_, pf, s * FIT["sandal"]["s"]))

        # ----- torso, clothes -----
        add(20, lambda: self._draw(canvas, self.img["torso"], tor_pt, T, tphi, s))
        if self.clothes:
            sh = load("clothes", "shorts_front.png"); f = FIT["shorts"]
            sw = tw(f["at"])
            add(21, lambda: self._draw(canvas, sh, f["anchor"], sw, tphi, s * f["s"]))
            ts = load("clothes", "tshirt_front_nosleeve.png"); f2 = FIT["shirt"]
            tw_ = tw(f2["at"])
            add(30, lambda: self._draw(canvas, ts, f2["anchor"], tw_, tphi, s * f2["s"]))

        # ----- arms -----
        for side in ("R", "L"):
            sp = tw(FIT["shoulder"][side]); sa = s * FIT["arm_s"]
            ua, fa = "upper_arm_" + side, "forearm_" + side
            ph = P["shoulder_" + side] + tphi + rig.align(ua)
            elbow = self._fwd(sp, ph, sa, (M[ua]["dist"][0] - M[ua]["prox"][0], M[ua]["dist"][1] - M[ua]["prox"][1]))
            pf = P["shoulder_" + side] + P["elbow_" + side] + tphi
            pfa = pf + rig.align(fa)
            add(31, lambda u=ua, sp=sp, ph=ph: self._draw(canvas, self.img[u], M[u]["prox"], sp, ph, sa))
            add(32, lambda f_=fa, e=elbow, pfa=pfa: self._draw(canvas, self.img[f_], M[f_]["prox"], e, pfa, sa))
            if self.clothes:
                sl = load("clothes", "sleeve_" + side + ".png")
                sp0, sp1 = axis_ends(sl); slen = math.hypot(*(sp1 - sp0))
                ulen = math.hypot(M[ua]["dist"][0] - M[ua]["prox"][0], M[ua]["dist"][1] - M[ua]["prox"][1])
                ss = sa * FIT["sleeve"]["len"] * ulen / slen
                vx, vy = sp1 - sp0; psl = P["shoulder_" + side] + tphi + (90.0 - math.degrees(math.atan2(vy, vx)))
                add(33, lambda sl=sl, sp0=sp0, sp=sp, psl=psl, ss=ss: self._draw(canvas, sl, (sp0[0], sp0[1]), (sp[0], sp[1] + FIT["sleeve"]["dy"] * s), psl, ss))
            if self.clothes and side == "L":
                wp = self._fwd(elbow, pfa, sa, (M[fa]["dist"][0] - M[fa]["prox"][0], M[fa]["dist"][1] - M[fa]["prox"][1] - FIT["watch"]["back"]))
                w = load("clothes", "watch.png")
                add(34, lambda w=w, wp=wp, pfa=pfa: self._draw(canvas, w, (w.width / 2, w.height / 2), wp, pfa, sa * FIT["watch"]["s"]))

        # ----- neck + head -----
        nm = M["neck"]; sock = tw(FIT["neck_socket"])
        pn = P["neck"] + tphi
        neck_top = self._fwd(sock, pn, s, (nm["prox"][0] - nm["dist"][0], nm["prox"][1] - nm["dist"][1]))
        add(19, lambda: self._draw(canvas, self.img["neck"], nm["dist"], sock, pn, s))
        hd = self.expr(expr); ph_ = pn + P["head"]
        hanchor = (hd.width / 2, hd.height - 28)
        add(40, lambda: self._draw(canvas, hd, hanchor, neck_top, ph_, s))
        if self.hair:
            hf, hb = FIT["hair_front"], FIT["hair_back"]
            def hpt(fr):   # fraction of head box -> world
                loc = (fr[0] * hd.width, fr[1] * hd.height)
                return self._fwd(neck_top, ph_, s, (loc[0] - hanchor[0], loc[1] - hanchor[1]))
            hfi, hbi = load("hair", "hair_front.png"), load("hair", "hair_back_layer.png")
            add(5, lambda: self._draw(canvas, hbi, hb["anchor"], hpt(hb["at"]), ph_, s * hb["s"]))
            add(45, lambda: self._draw(canvas, hfi, hf["anchor"], hpt(hf["at"]), ph_, s * hf["s"]))

        for _, fn in sorted(draws, key=lambda x: x[0]):
            fn()
        return canvas

POSES = {
    "rest": {},
    "wave": dict(shoulder_R=125, elbow_R=-30, shoulder_L=-8, head=6),
    "walk": dict(hip_R=-16, knee_R=0, hip_L=16, knee_L=-22, shoulder_R=18, shoulder_L=18, elbow_R=-10, elbow_L=-30, torso=2),
    "think": dict(shoulder_L=-40, elbow_L=-110, head=-6, neck=-3, shoulder_R=8),
    "point": dict(shoulder_L=-95, elbow_L=0, shoulder_R=6, torso=-3, head=4),
}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True); ap.add_argument("--expr", default="neutral")
    ap.add_argument("--pose", default="rest"); ap.add_argument("--hair", default="on")
    ap.add_argument("--bg", default="")
    a = ap.parse_args()
    im = Character(hair=a.hair == "on").render(POSES[a.pose], a.expr)
    if a.bg:
        bg = Image.new("RGBA", im.size, tuple(int(a.bg[i:i + 2], 16) for i in (0, 2, 4)) + (255,)); bg.alpha_composite(im); im = bg
    im.save(a.out)
