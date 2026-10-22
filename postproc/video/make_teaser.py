#!/usr/bin/env python3
"""Teaser of the rooftop study, rendered headless from the converged cases (see STORYBOARD.md).

    conda activate viz
    python postproc/video/make_teaser.py --frames ~/scratch/teaser_frames --out results/video/rooftop_exhaust_cfd.mp4
        [--stills DIR]   one frame at 30 %, 60 % and 90 % of every scene, for checking composition
        [--quick]        every eighth frame, full resolution
        [--only SCENE ..] render only the named scenes

Chapters: problem, question, method, result, answer. The 0-degree case gives the method scenes;
the 90- and 180-degree cases and the 9 m flue case are rotated into the building frame (they were
meshed with the building turned by +direction about the origin, so their results are turned back by
-direction). Numbers on screen are read from results/ or quoted from the case logs.
"""
import argparse, glob, json, math, os, shutil, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
W, H, FPS = 1920, 1080, 30
CASES = os.path.expanduser("~/scratch/openfoam_cases/applied"); TIME = 7000
WHITE, MUTED, ACCENT, FLUE = (236, 239, 243), (150, 158, 170), (232, 168, 64), "#ff5533"
FONT = "/usr/share/fonts/opentype/urw-base35/NimbusSans-Regular.otf"
FONTB = "/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf"
WATERMARK = "Saleh Mohammadrezaei   ·   github.com/SalehMohammadrezaei/rooftop-exhaust-cfd"
COLOURS = {"hall": "#979ea7", "parapet": "#868d96", "chiller_body": "#5f7b98", "chiller_in": "#4c6782", "chiller_out": "#d09a3c",
           "flue_wall": "#c0412f", "flue_exit": "#8c2f29", "intake_body": "#7f9b74", "intake_louvre": "#5f8a5a"}
Y_CUT = 7.56                    # mesh cut through the centre of the +y chiller row, off the cell faces
MODE = {"quick": False}
RES = {c: json.load(open(os.path.join(REPO, "results", "applied", c + ".json"))) for c in ("D0_dir000_U10", "D0_dir180_U10", "D2_dir180_U10")}
GEO = json.load(open(os.path.join(REPO, "params", "hall_geometry.json")))

def F(size, bold=False): return ImageFont.truetype(FONTB if bold else FONT, size)
def ease(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)
def kind(n):
    for k in ("chiller_in", "chiller_out", "intake_louvre", "chiller_body", "flue_wall", "flue_exit", "intake_body", "parapet", "hall"):
        if n.startswith(k): return k
    return "hall"
def rgba(c, a): return tuple(c) + (int(255 * max(0, min(1, a))),)

# ------------------------------------------------------------------ output
class Writer:
    def __init__(self, folder, stills=None):
        self.folder, self.stills, self.n, self.last, self.k, self.k0 = folder, stills, 0, None, 0, 0
    def dissolve(self, sec=0.3):
        if not self.stills: self.k = self.k0 = max(int(sec * FPS / (8 if MODE["quick"] else 1)), 1)
    def add(self, im):
        if self.k and self.last is not None:
            im = Image.blend(self.last, im, ease(1 - (self.k - 1) / self.k0)); self.k -= 1
        im.save(os.path.join(self.folder, f"{self.n:05d}.jpg"), quality=94); self.n += 1; self.last = im

def frames_for(sec, writer):
    n = max(int(round(sec * FPS)), 2)
    if writer.stills: return [int(n * f) for f in (0.3, 0.6, 0.9)], n
    return (list(range(0, n, 8)) if MODE["quick"] else list(range(n))), n

_VIG = None
def text_layer(img, t, dur, kicker=None, head=None, lines=(), line_t=None, big=False, line_size=38):
    """kicker word, one headline and up to two short lines, top left; items arrive staggered, leave together"""
    global _VIG
    base = img.convert("RGBA"); layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    a_out = 1 - ease((t - (dur - 0.4)) / 0.35)
    if kicker or head:
        if _VIG is None:
            yy, xx = np.mgrid[0:H, 0:W]; _VIG = np.clip(1.0 - np.hypot(xx / (W * 0.62), yy / (H * 0.5)), 0, 1) ** 1.5
        layer.alpha_composite(Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), (205 * _VIG * a_out).astype(np.uint8)]), "RGBA"))
    base = Image.alpha_composite(base, layer); layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer); x0, y0 = int(W * 0.055), int(H * (0.12 if big else 0.085))
    if kicker:
        a = ease(t / 0.3) * a_out
        d.rectangle([(x0, y0 - 18), (x0 + int(60 * a), y0 - 13)], fill=rgba(ACCENT, a))
        d.text((x0, y0), kicker, font=F(26, True), fill=rgba(ACCENT, a))
    y = y0 + 40
    if head:
        a = ease((t - 0.12) / 0.35) * a_out; size = 86 if big else 58
        d.text((x0, y + 14 * (1 - a)), head, font=F(size, True), fill=rgba(WHITE, a)); y += size + 22
    for j, s in enumerate(lines):
        t0 = line_t[j] if line_t else 0.35 + 0.25 * j
        a = ease((t - t0) / 0.35) * a_out
        d.text((x0, y + 12 * (1 - a)), s, font=F(line_size, line_size > 44), fill=rgba((210, 216, 224) if line_size <= 44 else WHITE, a)); y += int(line_size * 1.4)
    d.text((W - 48, H - 40), WATERMARK, font=F(22), fill=rgba(MUTED, 0.82), anchor="rs")
    return Image.alpha_composite(base, layer).convert("RGB")

def path(keys, t, smooth=True):
    """Catmull-Rom through camera keyframes [(position, focal point), ...]"""
    t = ease(t) if smooth else t; P = np.array([k[0] for k in keys], float); Fo = np.array([k[1] for k in keys], float); n = len(keys) - 1
    u = min(t, 1.0) * n; i = min(int(u), n - 1); f = u - i
    def cr(A):
        p0, p1, p2, p3 = A[max(i - 1, 0)], A[i], A[i + 1], A[min(i + 2, n)]
        return 0.5 * (2 * p1 + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)
    return cr(P), cr(Fo)

# ------------------------------------------------------------------ data
def read_case(name, arrays, patches=False):
    import pyvista as pv
    foam = os.path.join(CASES, name, "case.foam"); open(foam, "a").close()
    r = pv.OpenFOAMReader(foam); r.set_active_time_value(TIME); r.disable_all_cell_arrays()
    for a in arrays: r.enable_cell_array(a)
    r.disable_all_patch_arrays(); r.enable_patch_array("internalMesh")
    if patches:
        for p in r.patch_array_names:
            if p.startswith("patch/") and p.split("/")[1] not in ("inlet", "outlet", "ground", "top", "sides"): r.enable_patch_array(p)
    return r.read()

def smooth(s, n=60): return s.smooth_taubin(n_iter=n, pass_band=0.05) if s.n_points else s

def streak_lines(field, seeds, length=320.0):
    """streamlines of the computed mean velocity as (points, time along line, speed, phase)"""
    import pyvista as pv
    sl = field.streamlines_from_source(pv.PolyData(seeds), vectors="U", integration_direction="forward", max_length=length,
                                       initial_step_length=0.3, max_step_length=0.6, terminal_speed=0.1)
    T, U, P = sl["IntegrationTime"], np.linalg.norm(sl["U"], axis=1), sl.points; out = []; L = sl.lines; i = 0
    rng = np.random.default_rng(7)
    while i < len(L):
        n = L[i]; idx = L[i + 1:i + 1 + n]; i += n + 1
        if n > 8: out.append((P[idx], T[idx], U[idx], rng.uniform(0, 10)))
    return out

def comets(lines, s, period=5.0, dash=1.3):
    """dashes moving along each streamline at the local flow speed; scalar 0 at the tail to 1 at the head"""
    import pyvista as pv
    pts, cells, head = [], [], []; off = 0
    for P, T, U, ph in lines:
        q = (T - s + ph) % period; vis = q < dash
        if not vis.any(): continue
        edges = np.flatnonzero(np.diff(np.r_[0, vis.astype(int), 0]))
        for a, b in zip(edges[::2], edges[1::2]):
            if b - a < 3: continue
            pts.append(P[a:b]); head.append(q[a:b] / dash); cells.append(np.r_[b - a, np.arange(off, off + b - a)]); off += b - a
    if not pts: return None
    poly = pv.PolyData(np.vstack(pts)); poly.lines = np.concatenate(cells); poly["head"] = np.concatenate(head)
    return poly

def chiller_boxes():
    C = GEO["chillers"]; out = []
    for row in range(C["rows"]):
        yc = (row - (C["rows"] - 1) / 2) * (C["unit_y"] + C["row_gap_y"])
        for i in range(C["count_per_row"]):
            xc = C["centre_x"] + (i - (C["count_per_row"] - 1) / 2) * C["pitch_x"]; out.append((xc, yc))
    return out

# ------------------------------------------------------------------ scene
class Scene:
    def __init__(self):
        import pyvista as pv, cmcrameri.cm as cmc, vtk
        from matplotlib.colors import LinearSegmentedColormap
        self.pv, self.cmc, self.LSC, self.vtk = pv, cmc, LinearSegmentedColormap, vtk
        p = self.p = pv.Plotter(off_screen=True, window_size=(W, H), lighting="three lights")
        p.set_background("#07090c", top="#1a2230"); p.enable_anti_aliasing("ssaa"); p.enable_depth_peeling(10)
        self.geo = []
        for f in sorted(glob.glob(os.path.join(CASES, "D0_dir000_U10", "constant", "triSurface", "*.stl"))):
            n = os.path.basename(f)[:-4]
            if n == "preview_all": continue
            s = pv.read(f); self.geo.append((n, s, p.add_mesh(s, color=COLOURS[kind(n)], specular=0.25, specular_power=25, ambient=0.22, diffuse=0.8)))
        ground = pv.Plane(center=(0, 0, -0.03), direction=(0, 0, 1), i_size=600, j_size=600, i_resolution=60, j_resolution=60)
        p.add_mesh(ground, color="#0f141a", show_edges=True, edge_color="#1b2430", line_width=1, ambient=0.6, diffuse=0.4)
        self.comet_map = LinearSegmentedColormap.from_list("comet", ["#0a3a5a", "#38a3c8", "#d8f4ff"])
        m = read_case("D0_dir000_U10", ["U", "k", "sAll", "sF"] + [f"sC{i:02d}" for i in range(1, 11)], patches=True)
        self.cells = m["internalMesh"]; self.pts = self.cells.cell_data_to_point_data(); self.boundary = m["boundary"]
        self.cloud0 = smooth(self.pts.contour([0.10], scalars="sAll")); self.flue0 = smooth(self.pts.contour([0.05], scalars="sF"))
        self.chiller_plumes = [smooth(self.pts.contour([0.06], scalars=f"sC{i:02d}")) for i in range(1, 11)]
        self.chiller_cols = [tuple(c[:3]) for c in cmc.batlow(np.linspace(0.08, 0.92, 10))]
        self.dirs = {0: (self.cloud0, self.flue0)}
        for d in (90, 180):
            mm = read_case(f"D0_dir{d:03d}_U10", ["sAll", "sF"])["internalMesh"].cell_data_to_point_data()
            self.dirs[d] = tuple(smooth(mm.contour([lv], scalars=f)).rotate_z(-d, point=(0, 0, 0)) for lv, f in ((0.10, "sAll"), (0.05, "sF")))
            if d == 180: self.flue180_low = smooth(mm.contour([0.012], scalars="sF")).rotate_z(-180, point=(0, 0, 0))
        mm = read_case("D2_dir180_U10", ["sF"])["internalMesh"].cell_data_to_point_data()
        self.flue180_9m = smooth(mm.contour([0.012], scalars="sF")).rotate_z(-180, point=(0, 0, 0))
        tri9 = os.path.join(CASES, "D2_dir180_U10", "constant", "triSurface")
        self.flues_9m = [pv.read(os.path.join(tri9, f + ".stl")).rotate_z(-180, point=(0, 0, 0)) for f in ("flue_wall", "flue_exit")]

    def cam(self, keys, t, angle=34, smooth=True):
        pos, foc = path(keys, t, smooth); self.p.camera_position = (tuple(pos), tuple(foc), (0, 0, 1)); self.p.camera.view_angle = angle
    def grab(self):
        self.p.render(); return Image.fromarray(self.p.screenshot(return_img=True)[:, :, :3])
    def proj(self, pt):
        c = self.vtk.vtkCoordinate(); c.SetCoordinateSystemToWorld(); c.SetValue(*[float(v) for v in pt])
        x, y = c.GetComputedDoubleDisplayValue(self.p.renderer); return x, H - y
    def add(self, obj, **kw): kw.setdefault("render", False); return self.p.add_mesh(obj, **kw)
    def rm(self, *acts):
        for a in acts:
            if a is not None: self.p.remove_actor(a, render=False)
    def show(self, names, on):
        for n, _, act in self.geo:
            if kind(n) in names or n in names: act.SetVisibility(on)
    def comet_actor(self, poly, width=4):
        if poly is None: return None
        return self.add(poly, scalars="head", cmap=self.comet_map, clim=[0, 1], opacity="linear", line_width=width,
                        render_lines_as_tubes=True, show_scalar_bar=False, lighting=False)

def run_scene(S, w, dur, keys, text, update=None, angle=34, smooth=True, post=None):
    idx, n = frames_for(dur, w)
    for i in idx:
        t = i / max(n - 1, 1)
        if update: update(t, i)
        S.cam(keys, t, angle, smooth); img = S.grab()
        if post: img = post(img, t)
        if text is not None: img = text_layer(img, t * dur, dur, **text)
        w.add(img)

# ------------------------------------------------------------------ overlays drawn in screen space, crisp at any camera
def labels(img, S, items, alpha=1.0):
    """leader-line labels: (world point, text, (fx, fy) text position as fractions of the frame)"""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    for pt, s, (fx, fy) in items:
        x, y = S.proj(pt); tx, ty = fx * W, fy * H; f = F(30); tw = d.textlength(s, font=f)
        d.line([(x, y), (tx, ty + 18)], fill=rgba(WHITE, 0.75 * alpha), width=2); d.ellipse([(x - 4, y - 4), (x + 4, y + 4)], fill=rgba(ACCENT, alpha))
        d.rounded_rectangle([(tx - tw / 2 - 12, ty - 4), (tx + tw / 2 + 12, ty + 40)], radius=6, fill=(10, 14, 20, int(200 * alpha)))
        d.text((tx, ty + 18), s, font=f, fill=rgba(WHITE, alpha), anchor="mm")
    return Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")

def dims(img, S, items, alpha=1.0):
    """engineering dimension lines: (start, end, text, extension origins or None)"""
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); col = rgba((214, 221, 230), alpha)
    for p0, p1, s, ext in items:
        a, b = np.array(S.proj(p0)), np.array(S.proj(p1))
        if ext:
            for e, q in zip(ext, (p0, p1)): d.line([tuple(S.proj(e)), tuple(S.proj(q))], fill=rgba((214, 221, 230), 0.45 * alpha), width=1)
        d.line([tuple(a), tuple(b)], fill=col, width=2); v = b - a; nrm = np.array([-v[1], v[0]]) / (np.linalg.norm(v) + 1e-9)
        for q in (a, b): d.line([tuple(q - 9 * nrm), tuple(q + 9 * nrm)], fill=col, width=2)
        mid = (a + b) / 2; f = F(30, True); tw = d.textlength(s, font=f)
        d.rounded_rectangle([(mid[0] - tw / 2 - 10, mid[1] - 22), (mid[0] + tw / 2 + 10, mid[1] + 22)], radius=6, fill=(10, 14, 20, int(215 * alpha)))
        d.text(tuple(mid), s, font=f, fill=col, anchor="mm")
    return Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")

def big_number(img, s, sub=None, alpha=1.0, colour=WHITE):
    """large readout bottom left on a dark panel, so it reads over any surface"""
    if alpha <= 0.01: return img
    lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); x0 = int(W * 0.055); yb = int(H * 0.87)
    fb, fs = F(120, True), F(32); wb = d.textlength(s, font=fb); ws = d.textlength(sub, font=fs) if sub else 0
    d.rounded_rectangle([(x0 - 26, yb - 128), (x0 + max(wb, ws + 8) + 26, yb + (64 if sub else 24))], radius=10, fill=(8, 11, 16, int(205 * alpha)))
    d.text((x0, yb), s, font=fb, fill=rgba(colour, alpha), anchor="ls")
    if sub: d.text((x0 + 8, yb + 46), sub, font=fs, fill=rgba((196, 203, 212), alpha), anchor="ls")
    return Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")

def tube_arrow(S, pts, frac, colour, radius=0.28):
    """a spline through pts drawn to fraction frac, with a cone at its head"""
    pv = S.pv; sp = pv.Spline(np.array(pts, float), 160); k = max(int(frac * sp.n_points), 2)
    seg = pv.Spline(sp.points[:k], k); acts = [S.add(seg.tube(radius=radius, n_sides=14), color=colour, ambient=0.5, diffuse=0.6, specular=0.4, smooth_shading=True)]
    if frac > 0.05:
        tip, back = sp.points[k - 1], sp.points[max(k - 6, 0)]; dr = tip - back
        acts.append(S.add(pv.Cone(center=tip + 0.5 * dr / (np.linalg.norm(dr) + 1e-9), direction=dr, height=1.6, radius=0.75, resolution=24),
                          color=colour, ambient=0.5, diffuse=0.6))
    return acts

# ------------------------------------------------------------------ scenes
def sc_hook(S, w):
    seeds = np.array([(-48.0, y, z) for y in np.linspace(-19, 19, 15) for z in (15.6, 16.4, 17.6, 19.0, 21.0, 24.0)])
    lines = streak_lines(S.pts, seeds); st = {"c": None}
    plumes = [S.add(pl, color=c, opacity=0.5, smooth_shading=True, specular=0.4, specular_power=30) for pl, c in zip(S.chiller_plumes, S.chiller_cols)]
    flue = S.add(S.flue0, color=FLUE, opacity=0.85, smooth_shading=True, specular=0.5)
    def upd(t, i): S.rm(st["c"]); st["c"] = S.comet_actor(comets(lines, 1.2 + t * 3.0 * 4.0), 4)
    run_scene(S, w, 3.0, [((-37, -3.5, 18.2), (12, 1.5, 17.6)), ((-60, -38, 28), (4, 0, 16)), ((-118, -92, 58), (6, 0, 13))],
              dict(kicker="OPENFOAM  ·  EXTERNAL CFD", head="Rooftop exhaust re-entrainment", lines=["data-centre hall, 60 × 40 × 15 m"], line_t=[0.6], big=True), update=upd, angle=38)
    S.rm(st["c"], flue, *plumes)

def sc_problem(S, w):
    items = [((-12, -7.5, 18.6), "10 air-cooled chillers", (0.27, 0.30)), ((12, -2, 18.3), "fresh-air intake", (0.55, 0.24)),
             ((25, -3, 18.4), "4 generator flues", (0.80, 0.30))]
    w.dissolve(0.3)
    run_scene(S, w, 3.0, [((-118, -92, 58), (6, 0, 13)), ((-70, -112, 62), (6, 0, 13))], dict(kicker="LAYOUT", head="Roof plant"),
              post=lambda img, t: labels(img, S, items, ease((t - 0.2) / 0.2) * (1 - ease((t - 0.88) / 0.1))))

def sc_question(S, w):
    arrow1 = [(-12, -9.2, 17.6), (-12.2, -9.2, 21.0), (-10.6, -9.2, 23.0), (-9.3, -9.2, 20.5), (-9.4, -9.2, 16.6)]
    arrow2 = [(25, -1.5, 18.6), (24.0, -1.5, 23.0), (19.5, -2.2, 24.5), (14.5, -3.0, 20.5), (12.8, -3.2, 17.2)]
    st = {"a": []}; w.dissolve(0.3)
    def upd(t, i):
        S.rm(*st["a"]); st["a"] = []
        f1, f2 = ease((t - 0.08) / 0.32), ease((t - 0.46) / 0.32)
        if f1 > 0: st["a"] += tube_arrow(S, arrow1, f1, "#ffa23a", 0.24)
        if f2 > 0: st["a"] += tube_arrow(S, arrow2, f2, FLUE, 0.3)
    def post(img, t):
        items = [((-10.6, -9.2, 23.4), "1"), ((19.5, -2.2, 25.0), "2")]
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for (pt, s), t0 in zip(items, (0.3, 0.68)):
            a = ease((t - t0) / 0.12) * (1 - ease((t - 0.9) / 0.1))
            if a <= 0.01: continue
            x, y = S.proj(pt); d.ellipse([(x - 26, y - 70), (x + 26, y - 18)], fill=rgba(ACCENT, a))
            d.text((x, y - 44), s, font=F(34, True), fill=rgba((10, 12, 16), a), anchor="mm")
        return Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    run_scene(S, w, 4.0, [((-32, -70, 42), (4, -3, 17)), ((-22, -76, 44), (6, -3, 17))],
              dict(kicker="DESIGN CHECKS", head=None, lines=["1   Chiller discharge recirculation", "2   Exhaust ingestion at the fresh-air intake"], line_t=[1.0, 2.4], line_size=52),
              update=upd, post=post)
    S.rm(*st["a"])

def sc_wind(S, w):
    pv = S.pv; acts = {}
    for d, (c, f) in S.dirs.items():
        acts[d] = (S.add(c, scalars=c.points[:, 2] - 15.0, cmap=S.cmc.batlow, clim=[0, 12], opacity=0.0, smooth_shading=True, show_scalar_bar=False, specular=0.3),
                   S.add(f, color=FLUE, opacity=0.0, smooth_shading=True))
    st = {"arrow": None, "ang": 0.0}; keyang = [(0.0, 0), (0.30, 0), (0.46, 90), (0.64, 90), (0.80, 180), (1.0, 180)]
    def angle_at(t):
        for (t0, a0), (t1, a1) in zip(keyang, keyang[1:]):
            if t <= t1: return a0 + (a1 - a0) * ease((t - t0) / max(t1 - t0, 1e-6))
        return keyang[-1][1]
    def upd(t, i):
        ang = angle_at(t); th = math.radians(-ang); v = np.array([math.cos(th), math.sin(th), 0.0])
        st["tail"] = -v * 84 + np.array([0, 0, 0.3])
        S.rm(st["arrow"]); st["arrow"] = S.add(pv.Arrow(start=st["tail"], direction=v, scale=30, tip_length=0.3, tip_radius=0.16, shaft_radius=0.06),
                                               color="#e8a840", ambient=0.6, diffuse=0.5)
        for d, (ca, fa) in acts.items():
            wgt = ease(max(0.0, 1 - abs(ang - d) / 90.0)); ca.GetProperty().SetOpacity(0.5 * wgt); fa.GetProperty().SetOpacity(0.85 * wgt)
        st["ang"] = ang
    D = [((-30, -27, 0), (30, -27, 0), "60 m", ((-30, -20, 0), (30, -20, 0))), ((-37, -20, 0), (-37, 20, 0), "40 m", ((-30, -20, 0), (-30, 20, 0))),
         ((-33, -23, 0), (-33, -23, 15), "15 m", None)]
    def post(img, t):
        img = dims(img, S, D, ease((t - 0.05) / 0.15) * (1 - ease((t - 0.9) / 0.1)))
        x, y = S.proj(st["tail"]); x = min(max(x, W * 0.09), W * 0.9); y = min(max(y, H * 0.36), H * 0.86); d = ImageDraw.Draw(img); s = f"{int(round(st['ang'])):d}°"
        d.text((x, y - 18), s, font=F(78, True), fill=WHITE, anchor="mb"); d.text((x, y + 10), "wind", font=F(28), fill=MUTED, anchor="mt")
        return img
    w.dissolve(0.3)
    run_scene(S, w, 4.0, [((-96, -96, 132), (2, 0, 4)), ((-62, -118, 136), (2, 0, 4))], dict(kicker="LOAD CASES", head="Wind 0°, 90°, 180°  ·  U = 10 m/s at roof height"),
              update=upd, post=post, smooth=False)
    S.rm(st["arrow"], *[a for pair in acts.values() for a in pair])

def sc_mesh3d(S, w):
    surf = []
    for name in S.boundary.keys():
        b = S.boundary[name]
        if b is not None and b.n_points:
            surf.append(S.add(b, color=COLOURS[kind(name.split("/")[-1])], show_edges=True, edge_color="#11161c", line_width=0.8, ambient=0.3, diffuse=0.75))
    for _, _, act in S.geo: act.SetVisibility(False)
    w.dissolve(0.3)
    run_scene(S, w, 2.2, [((-62, -58, 40), (-10, 0, 16)), ((-44, -40, 30), (-12, 2, 16.5))], dict(kicker="MESH", head="snappyHexMesh  ·  2.6 M cells, 95 % hex"))
    S.rm(*surf)
    for _, _, act in S.geo: act.SetVisibility(True)

def sc_mesh2d(S, w):
    s = S.cells.slice(normal=(0, 1, 0), origin=(0, Y_CUT, 0), generate_triangles=False)
    c = s.cell_centers().points; s = s.extract_cells(np.where((c[:, 0] > -80) & (c[:, 0] < 100) & (c[:, 2] < 52))[0]).extract_surface(algorithm="dataset_surface")
    size = np.sqrt(np.abs(s.compute_cell_sizes(length=False, volume=False)["Area"])); s.cell_data["level"] = np.clip(np.log2(4.0 / size), 0, 6)
    cx = s.cell_centers().points[:, 0]; lvl = S.LSC.from_list("lvl", ["#141c26", "#1d3346", "#2b5a78", "#3f88a8"])
    near = []
    for _, _, act in S.geo: act.SetVisibility(False)
    for n, g, act in S.geo:
        cl = g.clip(normal=(0, -1, 0), origin=(0, Y_CUT, 0))
        if cl.n_points: near.append(S.add(cl, color=COLOURS[kind(n)], specular=0.25, ambient=0.22, diffuse=0.8))
    yc = Y_CUT - 0.03
    def cap(x0, x1, z0, z1, colour): near.append(S.add(S.pv.Rectangle([(x0, yc, z0), (x1, yc, z0), (x1, yc, z1)]), color=colour, ambient=0.75, diffuse=0.25))
    cap(-30, 30, 0, 15, "#2a3038"); cap(-30, -29.5, 15, 16.2, "#3a424c"); cap(29.5, 30, 15, 16.2, "#3a424c")
    for xc, _ in chiller_boxes()[:5]: cap(xc - 1.2, xc + 1.2, 15, 17.5, "#3d5670")
    st = {"a": None}; w.dissolve(0.3)
    def upd(t, i):
        S.rm(st["a"]); part = s.extract_cells(np.flatnonzero(cx < -80 + 185 * ease(t / 0.7)))
        st["a"] = S.add(part, scalars="level", cmap=lvl, clim=[0, 6], show_edges=True, edge_color="#7fb3cc", line_width=0.7,
                        ambient=0.9, diffuse=0.1, show_scalar_bar=False) if part.n_cells else None
    run_scene(S, w, 2.3, [((-8, Y_CUT - 150, 36), (8, Y_CUT, 21)), ((-15, Y_CUT - 72, 26), (-9, Y_CUT, 20))], dict(kicker="MESH", head="6 refinement levels  ·  4 m to 0.06 m"), update=upd)
    S.rm(st["a"], *near)
    for _, _, act in S.geo: act.SetVisibility(True)

def sc_inlet(S, w):
    pv = S.pv
    line = S.pts.sample_over_line((-110, 0, 0.6), (-110, 0, 44), resolution=22)
    z = line.points[:, 2]; u = np.linalg.norm(line["U"], axis=1); x0 = -100.0; scale = 1.45
    u15 = float(np.interp(15.0, z, u))
    st = {"acts": []}; w.dissolve(0.3)
    def upd(t, i):
        S.rm(*st["acts"]); st["acts"] = []; k = int(ease(t / 0.6) * len(z))
        for zz, uu in zip(z[:k], u[:k]):
            if uu < 0.3: continue
            st["acts"].append(S.add(pv.Arrow(start=(x0, 0, zz), direction=(1, 0, 0), scale=float(uu * scale), tip_length=0.25, tip_radius=0.06, shaft_radius=0.022),
                                    color="#e8a840", ambient=0.6, diffuse=0.5))
        if k > 2: st["acts"].append(S.add(pv.Spline(np.c_[x0 + u[:k] * scale, np.zeros(k), z[:k]], 200), color="#f4d9a0", line_width=3, lighting=False))
    def post(img, t):
        a = ease((t - 0.55) / 0.15) * (1 - ease((t - 0.9) / 0.1))
        if a <= 0: return img
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        p0, p1 = np.array(S.proj((x0 + u15 * scale, 0, 15))), np.array(S.proj((-30, 0, 15)))
        n = 22
        for j in range(n):
            if j % 2 == 0: d.line([tuple(p0 + (p1 - p0) * j / n), tuple(p0 + (p1 - p0) * (j + 1) / n)], fill=rgba(WHITE, 0.8 * a), width=2)
        s = f"U = {u15:.0f} m/s at H = 15 m"; mid = (p0 + p1) / 2; f = F(30, True); tw = d.textlength(s, font=f)
        d.rounded_rectangle([(mid[0] - tw / 2 - 12, mid[1] - 60), (mid[0] + tw / 2 + 12, mid[1] - 16)], radius=6, fill=(10, 14, 20, int(210 * a)))
        d.text((mid[0], mid[1] - 38), s, font=f, fill=rgba(WHITE, a), anchor="mm")
        return Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
    run_scene(S, w, 3.0, [((-120, -150, 22), (-62, 0, 24)), ((-104, -158, 24), (-50, 0, 23))],
              dict(kicker="BOUNDARY CONDITIONS", head="Neutral ABL inlet  ·  log law, z0 = 0.3 m"), update=upd, post=post)
    S.rm(*st["acts"])

def sc_flow(S, w):
    sl = S.pts.slice(normal=(0, 1, 0), origin=(0, 0.3, 0)); c = sl.cell_centers().points
    sl = sl.extract_cells(np.where((c[:, 0] > -75) & (c[:, 0] < 150) & (c[:, 2] < 32))[0]).extract_surface(algorithm="dataset_surface")
    sl["umag"] = np.linalg.norm(sl["U"], axis=1)
    au = S.add(sl, scalars="umag", cmap=S.LSC.from_list("uvel", ["#04070b", "#0f2a3e", "#235f84", "#5aa6cc", "#a9dcf0"]), clim=[0, 14], opacity=0.0, ambient=0.9, diffuse=0.1, show_scalar_bar=False)
    ak = S.add(sl.copy(), scalars="k", cmap=S.LSC.from_list("tke", ["#04070b", "#1a0d07", "#6b2a10", "#d0661f", "#ffd27a"]), clim=[3.4, 13], opacity=0.0, ambient=0.9, diffuse=0.1, show_scalar_bar=False)
    seeds = np.array([(-70.0, y, z) for y in np.linspace(-14, -2, 7) for z in (15.8, 16.6, 17.6, 19.0, 21.0, 24.0, 28.0)])
    wake = np.array([(x, -1.0, z) for x in (36, 44, 52, 62) for z in (2, 5, 9, 13)])
    lines = streak_lines(S.pts, seeds) + streak_lines(S.pts, wake, 160.0); st = {"c": None}; w.dissolve(0.3)
    def upd(t, i):
        mix = ease((t - 0.5) / 0.15)
        au.GetProperty().SetOpacity(0.9 * ease(t / 0.15) * (1 - mix)); ak.GetProperty().SetOpacity(0.9 * mix)
        S.rm(st["c"]); st["c"] = S.comet_actor(comets(lines, t * 5.0 * 3.0, period=4.0, dash=1.6), 5)
    run_scene(S, w, 5.0, [((-80, -92, 26), (-10, 0, 15)), ((10, -100, 30), (25, 0, 15)), ((95, -88, 26), (60, 0, 12))], None, update=upd, smooth=False,
              post=lambda img, t: text_layer(img, (t * 5.0) if t < 0.5 else (t - 0.5) * 5.0, 2.5, kicker="TURBULENCE MODEL",
                                             head="Steady RANS  ·  realizable k-ε" if t < 0.5 else "Turbulent kinetic energy",
                                             lines=["velocity magnitude, centre plane"] if t < 0.5 else ["k, centre plane"], line_t=[0.4]))
    S.rm(st["c"], au, ak)

def sc_tracers(S, w):
    acts = [S.add(pl, color=c, opacity=0.0, smooth_shading=True, specular=0.4, specular_power=30) for pl, c in zip(S.chiller_plumes, S.chiller_cols)]
    fa = S.add(S.flue0, color=FLUE, opacity=0.0, smooth_shading=True, specular=0.5); w.dissolve(0.3)
    order = [0, 5, 1, 6, 2, 7, 3, 8, 4, 9]
    def upd(t, i):
        for rank, o in enumerate(order): acts[o].GetProperty().SetOpacity(0.55 * ease((t - (0.06 + rank * 0.055)) / 0.08))
        fa.GetProperty().SetOpacity(0.9 * ease((t - 0.68) / 0.1))
    run_scene(S, w, 3.5, [((-82, -78, 56), (-4, 0, 15)), ((-30, -108, 66), (2, 0, 15)), ((10, -108, 64), (4, 0, 14))],
              dict(kicker="SCALAR TRANSPORT", head="Passive scalar per source", lines=["10 chillers + flues, Sct = 0.4, frozen flow field"], line_t=[0.6]), update=upd)
    S.rm(fa, *acts)

def sc_result_chillers(S, w):
    rise = RES["D0_dir000_U10"]["chiller_inlet_temperature_rise_K"]; C = GEO["chillers"]
    heat = S.LSC.from_list("heat", ["#2f7fa3", "#e8a840", "#ff3b2f"])
    boxes = []
    for (xc, yc), r in zip(chiller_boxes(), rise):
        b = S.pv.Box(bounds=(xc - C["unit_x"] / 2 - 0.03, xc + C["unit_x"] / 2 + 0.03, yc - C["unit_y"] / 2 - 0.03, yc + C["unit_y"] / 2 + 0.03, 15.0, 15.0 + C["unit_height"] + 0.04))
        boxes.append(S.add(b, color=heat((r - 2) / 6.5)[:3], ambient=0.45, diffuse=0.7, specular=0.3))
    cloud = S.add(S.cloud0, color="#c8d3de", opacity=0.12, smooth_shading=True); w.dissolve(0.3)
    def post(img, t):
        a = ease((t - 0.25) / 0.2) * (1 - ease((t - 0.9) / 0.1))
        if a <= 0: return img
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for (xc, yc), r in zip(chiller_boxes(), rise):
            x, y = S.proj((xc, yc, 18.2)); s = f"+{r:.1f} K"; f = F(26, True); tw = d.textlength(s, font=f)
            d.rounded_rectangle([(x - tw / 2 - 8, y - 38), (x + tw / 2 + 8, y - 6)], radius=5, fill=(10, 14, 20, int(210 * a)))
            d.text((x, y - 22), s, font=f, fill=rgba(heat((r - 2) / 6.5)[:3] and tuple(int(255 * v) for v in heat((r - 2) / 6.5)[:3]), a), anchor="mm")
        img = Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB")
        return big_number(img, f"{RES['D0_dir000_U10']['chiller_rise_mean_K']:.1f} K", "mean inlet temperature rise   ·   criterion 2 K", ease((t - 0.35) / 0.2) * (1 - ease((t - 0.9) / 0.1)), (255, 120, 80))
    run_scene(S, w, 3.2, [((-48, -52, 34), (-12, 0, 16)), ((-36, -60, 37), (-10, 0, 16))],
              dict(kicker="RESULT", head="Chiller inlet temperature rise", lines=["0°, 10 m/s  ·  per unit, from the tagged scalars"], line_t=[0.7]), post=post)
    S.rm(cloud, *boxes)

def sc_result_intake(S, w):
    pv = S.pv; I = GEO["intake"]
    plume = S.add(S.flue180_low, color="#ff7a45", opacity=0.0, smooth_shading=True, specular=0.4)
    glow = S.add(pv.Box(bounds=(I["centre_x"] - I["size_x"] / 2 - 0.05, I["centre_x"] + I["size_x"] / 2 + 0.05, -I["size_y"] / 2 - 0.05, I["size_y"] / 2 + 0.05, 15.0, 15.0 + I["height"] + 0.05)),
                 color="#ff2a55", opacity=0.0, ambient=0.9, diffuse=0.3)
    arrow = None
    w.dissolve(0.3)
    def upd(t, i):
        plume.GetProperty().SetOpacity(0.55 * ease((t - 0.1) / 0.3)); glow.GetProperty().SetOpacity(0.9 * ease((t - 0.4) / 0.15) * (0.75 + 0.25 * math.sin(t * 18)))
    dil = RES["D0_dir180_U10"]["intake_dilution_flues"]
    run_scene(S, w, 3.2, [((78, -62, 40), (8, 0, 15)), ((62, -76, 44), (10, 0, 15))],
              dict(kicker="RESULT", head="Exhaust dilution at the intake", lines=["180°, 10 m/s  ·  flue tip 3 m"], line_t=[0.6]),
              update=upd, post=lambda img, t: big_number(labels(img, S, [((12, 2, 18.2), "fresh-air intake", (0.62, 0.36))], ease((t - 0.35) / 0.15) * (1 - ease((t - 0.9) / 0.1))),
                                                          f"{dil:.0f}", "dilution at the louvres   ·   criterion 2,000", ease((t - 0.45) / 0.2) * (1 - ease((t - 0.9) / 0.1)), (255, 120, 80)))
    S.rm(plume, glow, arrow)

def sc_result_flues(S, w):
    p3 = S.add(S.flue180_low, color="#ff7a45", opacity=0.55, smooth_shading=True, specular=0.4)
    p9 = S.add(S.flue180_9m, color="#ff7a45", opacity=0.0, smooth_shading=True, specular=0.4)
    f9 = [S.add(g, color=COLOURS["flue_wall"], opacity=0.0, ambient=0.25, diffuse=0.8) for g in S.flues_9m]
    arrow = None
    d3, d9 = RES["D0_dir180_U10"]["intake_dilution_flues"], RES["D2_dir180_U10"]["intake_dilution_flues"]; st = {"m": 0.0}
    def upd(t, i):
        m = ease((t - 0.3) / 0.25); st["m"] = m
        p3.GetProperty().SetOpacity(0.55 * (1 - m)); p9.GetProperty().SetOpacity(0.55 * m)
        for a in f9: a.GetProperty().SetOpacity(m)
        S.show(("flue_wall", "flue_exit"), m < 0.5)
    def post(img, t):
        m = st["m"]; val = d3 + (d9 - d3) * m; tip = 3 + 6 * m
        return big_number(img, f"{val:.0f}×", f"flue tip {tip:.0f} m above the roof   ·   needs 2,000×", 1 - ease((t - 0.9) / 0.1), (255, 120, 80))
    run_scene(S, w, 3.2, [((70, -70, 40), (12, 0, 17)), ((58, -82, 46), (12, 0, 18))],
              dict(kicker="RESULT 3", head="Taller flues are not enough", lines=["from 3 m to 9 m, still short with this wind"], line_t=[0.7]), update=upd, post=post)
    S.show(("flue_wall", "flue_exit"), True); S.rm(p3, p9, arrow, *f9)

def sc_answer(S, w):
    plumes = [S.add(pl, color=c, opacity=0.5, smooth_shading=True, specular=0.4) for pl, c in zip(S.chiller_plumes, S.chiller_cols)]
    flue = S.add(S.flue0, color=FLUE, opacity=0.85, smooth_shading=True)
    rows = [("TURBULENCE", "steady RANS, realizable k-ε, wall functions"),
            ("INFLOW", "neutral atmospheric boundary layer, log law"),
            ("GRID", "snappyHexMesh, three-mesh study, GCI"),
            ("VALIDATION", "wind tunnel: AIJ Case H, IRSST R-848"),
            ("TRANSPORT", "passive scalars for heat and exhaust")]
    idx, n = frames_for(3.8, w); keys = [((40, -96, 62), (6, 0, 14)), ((78, -66, 58), (8, 0, 14))]; w.dissolve(0.3)
    for i in idx:
        t = i / max(n - 1, 1); S.cam(keys, t); img = S.grab()
        img = Image.blend(img, Image.new("RGB", img.size, (7, 9, 12)), ease(t / 0.2) * 0.8)
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0)); d = ImageDraw.Draw(lay); x0, x1 = int(W * 0.08), int(W * 0.24)
        a = ease((t - 0.08) / 0.2)
        d.rectangle([(x0, int(H * 0.17)), (x0 + int(70 * a), int(H * 0.17) + 6)], fill=rgba(ACCENT, a))
        d.text((x0, int(H * 0.2)), "Rooftop exhaust re-entrainment", font=F(58, True), fill=rgba(WHITE, a))
        y = int(H * 0.33)
        for j, (k, v) in enumerate(rows):
            b = ease((t - 0.14 - 0.06 * j) / 0.18)
            d.text((x0, y + 8 * (1 - b)), k, font=F(26, True), fill=rgba(ACCENT, b)); d.text((x1, y - 6 + 8 * (1 - b)), v, font=F(38), fill=rgba((214, 220, 228), b))
            y += 62
        c = ease((t - 0.5) / 0.2); y = int(H * 0.72)
        d.line([(x0, y - 24), (int(W * 0.62), y - 24)], fill=rgba((60, 68, 80), c), width=2)
        d.text((x0, y), "Saleh Mohammadrezaei", font=F(42, True), fill=rgba(WHITE, c))
        d.text((x0, y + 62), "linkedin.com/in/saleh-mohammadrezaei", font=F(32), fill=rgba(ACCENT, c))
        d.text((x0, y + 108), "github.com/SalehMohammadrezaei/rooftop-exhaust-cfd", font=F(32), fill=rgba(ACCENT, c))
        w.add(Image.alpha_composite(img.convert("RGBA"), lay).convert("RGB"))
    S.rm(flue, *plumes)

SCENES = [("hook", sc_hook), ("problem", sc_problem), ("question", sc_question), ("wind", sc_wind), ("mesh3d", sc_mesh3d), ("mesh2d", sc_mesh2d),
          ("inlet", sc_inlet), ("flow", sc_flow), ("tracers", sc_tracers), ("r1", sc_result_chillers), ("r2", sc_result_intake), ("answer", sc_answer)]

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=None); ap.add_argument("--frames", required=True)
    ap.add_argument("--quick", action="store_true"); ap.add_argument("--stills", default=None); ap.add_argument("--only", nargs="*", default=None); a = ap.parse_args()
    MODE["quick"] = a.quick; shutil.rmtree(a.frames, ignore_errors=True); os.makedirs(a.frames)
    S = Scene(); w = Writer(a.frames, a.stills)
    for name, fn in SCENES:
        if a.only and name not in a.only: continue
        n0 = w.n; fn(S, w); print(name, n0, "to", w.n - 1, flush=True)
    if a.out and not a.stills:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(a.frames, "%05d.jpg"), "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-movflags", "+faststart", a.out], check=True)
        print("wrote", a.out, w.n, "frames", round(w.n / FPS, 1), "s")

if __name__ == "__main__":
    main()
