#!/usr/bin/env python3
"""30-second teaser of the rooftop study, rendered headless from the converged cases (see STORYBOARD.md).

    conda activate viz
    python postproc/video/make_teaser.py --frames ~/scratch/teaser_frames --out results/video/rooftop_exhaust_cfd.mp4
        [--stills DIR]   one frame at 30 %, 60 % and 90 % of every shot, for checking composition
        [--quick]        every eighth frame, full resolution
        [--only SHOT ..] render only the named shots (hook wind mesh inlet flow plumes end)

Shots: hook, three wind directions, mesh 3D then 2D, inlet profile, velocity and turbulent kinetic
energy, tagged plumes one by one, end card. The 0-degree case gives every field except the wind
shot, which uses the 90- and 180-degree cases rotated into the building frame (those cases were
meshed with the building turned by +direction about the origin, so their results are turned back by
-direction here). Numbers on screen come from the case logs and results/, none is computed here.
"""
import argparse, glob, math, os, shutil, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont

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

def F(size, bold=False): return ImageFont.truetype(FONTB if bold else FONT, size)
def ease(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)
def kind(n):
    for k in ("chiller_in", "chiller_out", "intake_louvre", "chiller_body", "flue_wall", "flue_exit", "intake_body", "parapet", "hall"):
        if n.startswith(k): return k
    return "hall"

# ------------------------------------------------------------------ output
class Writer:
    def __init__(self, folder, stills=None):
        self.folder, self.stills, self.n, self.last, self.k, self.k0 = folder, stills, 0, None, 0, 0
    def dissolve(self, sec=0.35):
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
def text_layer(img, t, dur, kicker=None, head=None, big=False):
    """kicker word and one headline, top left, arriving staggered and leaving together"""
    global _VIG
    base = img.convert("RGBA"); layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    a_out = 1 - ease((t - (dur - 0.45)) / 0.4)
    if kicker or head:
        if _VIG is None:
            yy, xx = np.mgrid[0:H, 0:W]; _VIG = np.clip(1.0 - np.hypot(xx / (W * 0.6), yy / (H * 0.45)), 0, 1) ** 1.5
        layer.alpha_composite(Image.fromarray(np.dstack([np.zeros((H, W, 3), np.uint8), (200 * _VIG * a_out).astype(np.uint8)]), "RGBA"))
    d = ImageDraw.Draw(layer); x0, y0 = int(W * 0.055), int(H * (0.12 if big else 0.085))
    if kicker:
        a = ease(t / 0.3) * a_out
        d.rectangle([(x0, y0 - 18), (x0 + int(60 * a), y0 - 13)], fill=ACCENT + (int(255 * a),))
        d.text((x0, y0), kicker, font=F(26, True), fill=ACCENT + (int(255 * a),))
    if head:
        a = ease((t - 0.12) / 0.4) * a_out; size = 86 if big else 60
        d.text((x0, y0 + 40 + 16 * (1 - a)), head, font=F(size, True), fill=WHITE + (int(255 * a),))
    d.text((W - 48, H - 40), WATERMARK, font=F(22), fill=MUTED + (210,), anchor="rs")
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
    """streamlines of the computed mean velocity as lists of (points, time along line, speed, phase)"""
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
    """moving dashes along each streamline, at the local flow speed: visible where (time along line - s + phase)
    mod period < dash; the scalar runs 0 at the tail to 1 at the head, so a linear opacity map gives comet streaks"""
    import pyvista as pv
    pts, cells, head = [], [], []; off = 0
    for P, T, U, ph in lines:
        q = (T - s + ph) % period; vis = q < dash
        if not vis.any(): continue
        edges = np.flatnonzero(np.diff(np.r_[0, vis.astype(int), 0])); starts, ends = edges[::2], edges[1::2]
        for a, b in zip(starts, ends):
            if b - a < 3: continue
            pts.append(P[a:b]); head.append(q[a:b] / dash); cells.append(np.r_[b - a, np.arange(off, off + b - a)]); off += b - a
    if not pts: return None
    poly = pv.PolyData(np.vstack(pts)); poly.lines = np.concatenate(cells); poly["head"] = np.concatenate(head)
    return poly

# ------------------------------------------------------------------ scene
class Scene:
    def __init__(self):
        import pyvista as pv, cmcrameri.cm as cmc
        from matplotlib.colors import LinearSegmentedColormap
        self.pv, self.cmc, self.LSC = pv, cmc, LinearSegmentedColormap
        p = self.p = pv.Plotter(off_screen=True, window_size=(W, H), lighting="three lights")
        p.set_background("#07090c", top="#1a2230"); p.enable_anti_aliasing("ssaa"); p.enable_depth_peeling(10)
        self.geo = []
        for f in sorted(glob.glob(os.path.join(CASES, "D0_dir000_U10", "constant", "triSurface", "*.stl"))):
            n = os.path.basename(f)[:-4]
            if n == "preview_all": continue
            s = pv.read(f); self.geo.append((n, s, p.add_mesh(s, color=COLOURS[kind(n)], specular=0.25, specular_power=25, ambient=0.22, diffuse=0.8)))
        ground = pv.Plane(center=(0, 0, -0.03), direction=(0, 0, 1), i_size=600, j_size=600, i_resolution=60, j_resolution=60)
        self.ground = p.add_mesh(ground, color="#0f141a", show_edges=True, edge_color="#1b2430", line_width=1, ambient=0.6, diffuse=0.4)
        self.comet_map = LinearSegmentedColormap.from_list("comet", ["#0a3a5a", "#38a3c8", "#d8f4ff"])
        m = read_case("D0_dir000_U10", ["U", "k", "sAll", "sF"] + [f"sC{i:02d}" for i in range(1, 11)], patches=True)
        self.cells = m["internalMesh"]; self.pts = self.cells.cell_data_to_point_data(); self.boundary = m["boundary"]
        self.cloud0 = smooth(self.pts.contour([0.10], scalars="sAll")); self.flue0 = smooth(self.pts.contour([0.05], scalars="sF"))
        self.chiller_plumes = [smooth(self.pts.contour([0.06], scalars=f"sC{i:02d}")) for i in range(1, 11)]
        pal = cmc.batlow(np.linspace(0.08, 0.92, 10)); self.chiller_cols = [tuple(c[:3]) for c in pal]
        self.dirs = {0: (self.cloud0, self.flue0)}
        for d in (90, 180):
            mm = read_case(f"D0_dir{d:03d}_U10", ["sAll", "sF"])["internalMesh"].cell_data_to_point_data()
            self.dirs[d] = tuple(smooth(mm.contour([lv], scalars=f)).rotate_z(-d, point=(0, 0, 0)) for lv, f in ((0.10, "sAll"), (0.05, "sF")))

    def cam(self, keys, t, angle=34, smooth=True):
        pos, foc = path(keys, t, smooth); self.p.camera_position = (tuple(pos), tuple(foc), (0, 0, 1)); self.p.camera.view_angle = angle
    def grab(self):
        self.p.render(); return Image.fromarray(self.p.screenshot(return_img=True)[:, :, :3])
    def add(self, obj, **kw): kw.setdefault("render", False); return self.p.add_mesh(obj, **kw)
    def rm(self, *acts):
        for a in acts:
            if a is not None: self.p.remove_actor(a, render=False)
    def comet_actor(self, poly, width=4):
        if poly is None: return None
        return self.add(poly, scalars="head", cmap=self.comet_map, clim=[0, 1], opacity="linear", line_width=width,
                        render_lines_as_tubes=True, show_scalar_bar=False, lighting=False)

def run_shot(S, w, dur, keys, text, update=None, angle=34, smooth=True, post=None):
    idx, n = frames_for(dur, w)
    for i in idx:
        t = i / max(n - 1, 1)
        if update: update(t, i)
        S.cam(keys, t, angle, smooth); img = S.grab()
        if post: img = post(img, t)
        if text is not None: img = text_layer(img, t * dur, dur, **text)
        w.add(img)

# ------------------------------------------------------------------ the shots
def shot_hook(S, w):
    seeds = np.array([(-48.0, y, z) for y in np.linspace(-19, 19, 15) for z in (15.6, 16.4, 17.6, 19.0, 21.0, 24.0)])
    lines = streak_lines(S.pts, seeds); st = {"c": None}
    plumes = [S.add(pl, color=c, opacity=0.5, smooth_shading=True, specular=0.4, specular_power=30) for pl, c in zip(S.chiller_plumes, S.chiller_cols)]
    flue = S.add(S.flue0, color=FLUE, opacity=0.85, smooth_shading=True, specular=0.5)
    def upd(t, i):
        S.rm(st["c"]); st["c"] = S.comet_actor(comets(lines, 1.2 + t * 4.0 * 4.0), 4)
    run_shot(S, w, 4.0, [((-37, -3.5, 18.2), (12, 1.5, 17.6)), ((-60, -38, 28), (4, 0, 16)), ((-118, -92, 58), (6, 0, 13))],
             dict(kicker="OPENFOAM  ·  EXTERNAL AERODYNAMICS", head="Where does the exhaust go?", big=True), update=upd, angle=38)
    S.rm(st["c"], flue, *plumes)

def shot_wind(S, w):
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
        S.rm(st["arrow"]); start = -v * 72 + np.array([0, 0, 0.3])
        st["arrow"] = S.add(pv.Arrow(start=start, direction=v, scale=34, tip_length=0.3, tip_radius=0.16, shaft_radius=0.06),
                            color="#e8a840", ambient=0.6, diffuse=0.5)
        for d, (ca, fa) in acts.items():
            wgt = ease(max(0.0, 1 - abs(ang - d) / 90.0)); ca.GetProperty().SetOpacity(0.55 * wgt); fa.GetProperty().SetOpacity(0.85 * wgt)
        st["ang"] = ang
    def post(img, t):
        d = ImageDraw.Draw(img); d.text((W * 0.055, H * 0.88), f"{int(round(st['ang'])):d}°", font=F(110, True), fill=WHITE, anchor="ls")
        return img
    w.dissolve(0.3)
    run_shot(S, w, 4.0, [((-92, -92, 128), (4, 0, 6)), ((-60, -112, 132), (4, 0, 6))], dict(kicker="THREE WIND DIRECTIONS", head=None),
             update=upd, post=post, smooth=False)
    S.rm(st["arrow"], *[a for pair in acts.values() for a in pair])

def shot_mesh(S, w):
    surf = []
    for name in S.boundary.keys():
        b = S.boundary[name]
        if b is not None and b.n_points:
            surf.append(S.add(b, color=COLOURS[kind(name.split("/")[-1])], show_edges=True, edge_color="#11161c", line_width=0.8, ambient=0.3, diffuse=0.75))
    for _, _, act in S.geo: act.SetVisibility(False)
    w.dissolve(0.3)
    run_shot(S, w, 2.2, [((-62, -58, 40), (-10, 0, 16)), ((-44, -40, 30), (-12, 2, 16.5))], dict(kicker="MESH", head="snappyHexMesh  ·  2.6 M cells"))
    S.rm(*surf)
    s = S.cells.slice(normal=(0, 1, 0), origin=(0, Y_CUT, 0), generate_triangles=False)
    c = s.cell_centers().points; s = s.extract_cells(np.where((c[:, 0] > -80) & (c[:, 0] < 100) & (c[:, 2] < 52))[0]).extract_surface(algorithm="dataset_surface")
    size = np.sqrt(np.abs(s.compute_cell_sizes(length=False, volume=False)["Area"])); s.cell_data["level"] = np.clip(np.log2(4.0 / size), 0, 6)
    cx = s.cell_centers().points[:, 0]; lvl = S.LSC.from_list("lvl", ["#141c26", "#1d3346", "#2b5a78", "#3f88a8"])
    near = []
    for n, g, act in S.geo:
        cl = g.clip(normal=(0, -1, 0), origin=(0, Y_CUT, 0))
        if cl.n_points: near.append(S.add(cl, color=COLOURS[kind(n)], specular=0.25, ambient=0.22, diffuse=0.8))
    yc = Y_CUT - 0.03                                   # section caps where the cut passes through solids
    def cap(x0, x1, z0, z1, colour): near.append(S.add(S.pv.Rectangle([(x0, yc, z0), (x1, yc, z0), (x1, yc, z1)]), color=colour, ambient=0.75, diffuse=0.25))
    cap(-30, 30, 0, 15, "#2a3038"); cap(-30, -29.5, 15, 16.2, "#3a424c"); cap(29.5, 30, 15, 16.2, "#3a424c")
    for k in range(5): xc = -12 + (k - 2) * 4.5; cap(xc - 1.2, xc + 1.2, 15, 17.5, "#3d5670")
    st = {"a": None}; w.dissolve(0.3)
    def upd(t, i):
        S.rm(st["a"]); xr = -80 + 185 * ease(t / 0.7); part = s.extract_cells(np.flatnonzero(cx < xr))
        st["a"] = S.add(part, scalars="level", cmap=lvl, clim=[0, 6], show_edges=True, edge_color="#7fb3cc", line_width=0.7,
                        ambient=0.9, diffuse=0.1, show_scalar_bar=False) if part.n_cells else None
    run_shot(S, w, 2.3, [((-8, Y_CUT - 150, 36), (8, Y_CUT, 21)), ((-15, Y_CUT - 72, 26), (-9, Y_CUT, 20))], dict(kicker="MESH", head="six levels  ·  4 m to 6 cm"), update=upd)
    S.rm(st["a"], *near)
    for _, _, act in S.geo: act.SetVisibility(True)

def shot_inlet(S, w):
    pv = S.pv
    line = S.pts.sample_over_line((-110, 0, 0.6), (-110, 0, 44), resolution=22)
    z = line.points[:, 2]; u = np.linalg.norm(line["U"], axis=1); x0 = -100.0; scale = 1.45
    st = {"acts": []}; w.dissolve(0.3)
    def upd(t, i):
        S.rm(*st["acts"]); st["acts"] = []; k = int(ease(t / 0.75) * len(z))
        for zz, uu in zip(z[:k], u[:k]):
            if uu < 0.3: continue
            st["acts"].append(S.add(pv.Arrow(start=(x0, 0, zz), direction=(1, 0, 0), scale=float(uu * scale), tip_length=0.25, tip_radius=0.06, shaft_radius=0.022),
                                    color="#e8a840", ambient=0.6, diffuse=0.5))
        if k > 2:
            st["acts"].append(S.add(pv.Spline(np.c_[x0 + u[:k] * scale, np.zeros(k), z[:k]], 200), color="#f4d9a0", line_width=3, lighting=False))
    run_shot(S, w, 3.5, [((-120, -150, 22), (-62, 0, 24)), ((-104, -158, 24), (-50, 0, 23))], dict(kicker="SOLVER", head="steady RANS  ·  realizable k-ε"), update=upd)
    S.rm(*st["acts"])

def shot_flow(S, w):
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
        S.rm(st["c"]); st["c"] = S.comet_actor(comets(lines, t * 6.0 * 3.0, period=4.0, dash=1.6), 5)
    run_shot(S, w, 6.0, [((-80, -92, 26), (-10, 0, 15)), ((10, -100, 30), (25, 0, 15)), ((95, -88, 26), (60, 0, 12))],
             None, update=upd, smooth=False,
             post=lambda img, t: text_layer(img, (t * 6.0) if t < 0.5 else (t - 0.5) * 6.0, 3.0,
                                            kicker="FLOW", head="velocity" if t < 0.5 else "turbulent kinetic energy"))
    S.rm(st["c"], au, ak)

def shot_plumes(S, w):
    acts = [S.add(pl, color=c, opacity=0.0, smooth_shading=True, specular=0.4, specular_power=30) for pl, c in zip(S.chiller_plumes, S.chiller_cols)]
    fa = S.add(S.flue0, color=FLUE, opacity=0.0, smooth_shading=True, specular=0.5); w.dissolve(0.3)
    order = [0, 5, 1, 6, 2, 7, 3, 8, 4, 9]
    def upd(t, i):
        for rank, o in enumerate(order): acts[o].GetProperty().SetOpacity(0.55 * ease((t - (0.06 + rank * 0.055)) / 0.08))
        fa.GetProperty().SetOpacity(0.9 * ease((t - 0.68) / 0.1))
    run_shot(S, w, 5.0, [((-82, -78, 56), (-4, 0, 15)), ((-30, -108, 66), (2, 0, 15)), ((40, -96, 62), (6, 0, 14))],
             dict(kicker="TAGGED SCALARS", head="one tracer per source"), update=upd)

def shot_end(S, w):
    idx, n = frames_for(3.0, w); keys = [((40, -96, 62), (6, 0, 14)), ((78, -66, 58), (8, 0, 14))]
    for i in idx:
        t = i / max(n - 1, 1); S.cam(keys, t); img = S.grab()
        img = Image.blend(img, Image.new("RGB", img.size, (7, 9, 12)), ease(t / 0.3) * 0.72)
        d = ImageDraw.Draw(img); a = ease((t - 0.15) / 0.3); col = lambda c: tuple(int(v * a + 7 * (1 - a)) for v in c); x0 = int(W * 0.08)
        d.rectangle([(x0, int(H * 0.33)), (x0 + int(70 * a), int(H * 0.33) + 6)], fill=col(ACCENT))
        d.text((x0, int(H * 0.37)), "Validated. Grid-independent.", font=F(64, True), fill=col(WHITE))
        d.text((x0, int(H * 0.37) + 84), "Recirculation found at every wind.", font=F(44), fill=col(MUTED))
        d.text((x0, int(H * 0.72)), "Saleh Mohammadrezaei", font=F(40, True), fill=col(WHITE))
        d.text((x0, int(H * 0.72) + 56), "github.com/SalehMohammadrezaei/rooftop-exhaust-cfd", font=F(32), fill=col(ACCENT))
        w.add(img)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", default=None); ap.add_argument("--frames", required=True)
    ap.add_argument("--quick", action="store_true"); ap.add_argument("--stills", default=None); ap.add_argument("--only", nargs="*", default=None); a = ap.parse_args()
    MODE["quick"] = a.quick; shutil.rmtree(a.frames, ignore_errors=True); os.makedirs(a.frames)
    S = Scene(); w = Writer(a.frames, a.stills)
    shots = [("hook", shot_hook), ("wind", shot_wind), ("mesh", shot_mesh), ("inlet", shot_inlet), ("flow", shot_flow), ("plumes", shot_plumes), ("end", shot_end)]
    for name, fn in shots:
        if a.only and name not in a.only: continue
        n0 = w.n; fn(S, w); print(name, n0, "to", w.n - 1, flush=True)
    if a.out and not a.stills:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(a.frames, "%05d.jpg"), "-c:v", "libx264",
                        "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-movflags", "+faststart", a.out], check=True)
        print("wrote", a.out, w.n, "frames", round(w.n / FPS, 1), "s")

if __name__ == "__main__":
    main()
