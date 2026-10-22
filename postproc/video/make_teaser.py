#!/usr/bin/env python3
"""30-second teaser of the rooftop study, rendered headless from the real case and assembled with ffmpeg.

    conda activate viz
    python postproc/video/make_teaser.py --case ~/scratch/openfoam_cases/applied/D0_dir000_U10 --time 7000 \
        --frames ~/scratch/teaser_frames --out results/video/rooftop_exhaust_cfd.mp4 [--quick]

Every shot is a 3D render of the converged 0-degree, 10 m/s case: the hook on the tracer cloud with the
title, the roof, a polygon cut through the real mesh, streamlines of the computed wind, the tagged scalars
forming, and a pull-back carrying the verification and validation facts, then the end card. The numbers on
screen are quoted from results/ and the case logs (checkMesh, fvSchemes); none is computed here.
--quick renders an eighth of the frames at full resolution, for checking the layout.
"""
import argparse, glob, math, os, shutil, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, "..", "render"))

W, H, FPS = 1920, 1080, 30
INK, GREY, ACCENT, BLUE = (27, 31, 36), (96, 103, 114), (201, 139, 42), (31, 111, 139)
FONT = "/usr/share/fonts/opentype/urw-base35/NimbusSans-Regular.otf"
FONTB = "/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf"
WATERMARK = "Saleh Mohammadrezaei   ·   github.com/SalehMohammadrezaei/rooftop-exhaust-cfd"
QUICK = False
Y_CUT = 7.56                     # mesh cut through the centre of the second chiller row, off the cell faces

def F(size, bold=False): return ImageFont.truetype(FONTB if bold else FONT, size)
def ease(t): t = min(max(t, 0.0), 1.0); return t * t * (3 - 2 * t)
def nframes(sec): return max(int(round(sec * FPS / (8 if QUICK else 1))), 4)

# ------------------------------------------------------------------ frames and text
class Writer:
    """numbered JPEG frames; dissolve(k) blends the next k frames from the last one written"""
    def __init__(self, folder): self.folder = folder; self.n = 0; self.last = None; self.k = 0; self.k0 = 0
    def dissolve(self, sec=0.4): self.k = self.k0 = nframes(sec)
    def add(self, im):
        im = im.convert("RGB")
        if self.k and self.last is not None:
            im = Image.blend(self.last, im, ease(1 - (self.k - 1) / self.k0)); self.k -= 1
        im.save(os.path.join(self.folder, f"{self.n:05d}.jpg"), quality=94); self.n += 1; self.last = im

def panel(layer, x0, y0, x1, y1, alpha=215):
    """white panel fading to the right and at top and bottom, so text reads over any render"""
    w, h = x1 - x0, y1 - y0
    gx = np.clip(1.25 - 1.25 * np.linspace(0, 1, w), 0, 1)
    gy = np.clip(np.minimum(np.linspace(0, 1, h), np.linspace(1, 0, h)) * 3, 0, 1)
    a = (alpha * np.outer(gy, gx)).astype(np.uint8)
    rgba = np.dstack([np.full((h, w), 255, np.uint8)] * 3 + [a])
    layer.alpha_composite(Image.fromarray(rgba, "RGBA"), (x0, y0))

def overlay(img, t, dur, kicker=None, head=None, lines=(), big=False, wm=True):
    """the text block, top left over the render; items arrive staggered and slide up, all leave together"""
    base = img.convert("RGBA"); layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    leave = 1 - ease((t - (dur - 0.5)) / 0.45)
    items = []
    if kicker: items.append((kicker, F(25, True), ACCENT, 0.0, 44))
    if head: items.append((head, F(80 if big else 56, True), INK, 0.12, 100 if big else 74))
    for i, s in enumerate(lines): items.append((s, F(36 if big else 32), GREY, 0.38 + 0.24 * i, 48 if big else 44))
    x0 = int(W * 0.055); y0 = int(H * (0.11 if big else 0.08)); total = sum(it[4] for it in items)
    if items:
        wmax = max(ImageDraw.Draw(layer).textlength(it[0], font=it[1]) for it in items)
        panel(layer, 0, max(y0 - 60, 0), int(min(W, x0 + wmax + 360)), min(y0 + total + 60, H), alpha=int(215 * leave))
    d = ImageDraw.Draw(layer); y = y0
    if kicker:
        a = ease((t - 0.0) / 0.35) * leave
        d.rectangle([(x0, y - 16), (x0 + int(56 * a), y - 11)], fill=ACCENT + (int(255 * a),))
    for s, f, col, t0, step in items:
        a = ease((t - t0) / 0.4) * leave
        if a > 0: d.text((x0, y + 18 * (1 - a)), s, font=f, fill=col + (int(255 * a),))
        y += step
    if wm: d.text((W - 48, H - 40), WATERMARK, font=F(22), fill=GREY + (200,), anchor="rs")
    return Image.alpha_composite(base, layer).convert("RGB")

def path(keys, t):
    """Catmull-Rom through camera keyframes [(position, focal point), ...] at t in [0, 1], eased"""
    t = ease(t); P = np.array([k[0] for k in keys], float); Fo = np.array([k[1] for k in keys], float); n = len(keys) - 1
    u = t * n; i = min(int(u), n - 1); f = u - i
    def cr(A):
        p0, p1, p2, p3 = A[max(i - 1, 0)], A[i], A[i + 1], A[min(i + 2, n)]
        return 0.5 * (2 * p1 + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)
    return cr(P), cr(Fo)

# ------------------------------------------------------------------ scene
def build(a):
    import pyvista as pv, cmcrameri.cm as cmc
    from matplotlib.colors import LinearSegmentedColormap
    from geometry import COL, kind
    p = pv.Plotter(off_screen=True, window_size=(W, H), lighting="three lights")
    p.set_background("#dedcd7", top="#ffffff")
    geo = []
    for f in sorted(glob.glob(os.path.join(a.case, "constant", "triSurface", "*.stl"))):
        n = os.path.basename(f)[:-4]
        if n == "preview_all": continue
        s = pv.read(f); geo.append((n, s, p.add_mesh(s, color="#f6f4f0" if kind(n) == "hall" else COL[kind(n)], specular=0.12, specular_power=15, ambient=0.3, diffuse=0.75)))
    p.add_mesh(pv.Plane(center=(0, 0, -0.02), direction=(0, 0, 1), i_size=1200, j_size=1200), color="#d6d3cd", ambient=0.55, diffuse=0.45)
    p.enable_anti_aliasing("ssaa"); p.enable_depth_peeling(8)
    foam = os.path.join(a.case, "case.foam"); open(foam, "a").close()
    rd = pv.OpenFOAMReader(foam); rd.set_active_time_value(a.time); rd.disable_all_cell_arrays()
    for n in ("U", "sAll", "sF"): rd.enable_cell_array(n)
    rd.disable_all_patch_arrays(); rd.enable_patch_array("internalMesh")
    cells = rd.read()["internalMesh"]; pts = cells.cell_data_to_point_data()
    S = {"p": p, "pv": pv, "cmc": cmc, "geo": geo, "cells": cells, "pts": pts, "COL": COL, "kind": kind, "LSC": LinearSegmentedColormap}
    # the finished tracer cloud and flue plume, shared by the hook and the closing shots
    S["cloud"] = cloud_surface(S, 0.10); S["plume"] = pts.contour([0.05], scalars="sF").smooth_taubin(n_iter=60, pass_band=0.05)
    return S

def cloud_surface(S, level):
    iso = S["pts"].contour([level], scalars="sAll")
    if iso.n_points: iso = iso.smooth_taubin(n_iter=60, pass_band=0.05); iso["h"] = iso.points[:, 2] - 15.0
    return iso

def add_cloud(S, iso, opacity=0.55):
    return S["p"].add_mesh(iso, scalars="h", cmap=S["cmc"].batlow, clim=[0, 12], opacity=opacity, smooth_shading=True,
                           show_scalar_bar=False, specular=0.25, specular_power=20, render=False)

def cam(S, keys, t, angle=32):
    pos, foc = path(keys, t); S["p"].camera_position = (tuple(pos), tuple(foc), (0, 0, 1)); S["p"].camera.view_angle = angle

def shot(S, w, keys, dur, text, update=None, angle=32):
    n = nframes(dur)
    for i in range(n):
        t = i / max(n - 1, 1)
        if update: update(t)
        cam(S, keys, t, angle); S["p"].render()
        img = Image.fromarray(S["p"].screenshot(return_img=True)[:, :, :3])
        w.add(overlay(img, t * dur, dur, **text) if text else img)
    return img

# ------------------------------------------------------------------ the shots
def run(a, w):
    S = build(a); p = S["p"]
    # 1. hook: the finished cloud, low and close, the question as the title
    c = add_cloud(S, S["cloud"]); pl = p.add_mesh(S["plume"], color="#b5443c", opacity=0.8, smooth_shading=True, specular=0.3)
    shot(S, w, [((-58, -92, 26), (2, 0, 15)), ((-34, -100, 31), (6, 0, 15)), ((-12, -104, 36), (9, 0, 14))], 4.0,
         dict(kicker="OPENFOAM  ·  EXTERNAL CFD", head="Where does the exhaust go?", big=True,
              lines=["Rooftop exhaust and heat re-entrainment at a data-centre hall"]))
    p.remove_actor(c); p.remove_actor(pl)
    # 2. the roof
    w.dissolve()
    shot(S, w, [((-150, -70, 22), (-10, 0, 13)), ((-90, -115, 48), (0, 0, 12)), ((-10, -125, 66), (6, 0, 10))], 3.5,
         dict(kicker="THE ROOF", head="10 chillers, 4 generator flues, 1 fresh-air intake",
              lines=["60 × 40 × 15 m hall in a neutral atmospheric boundary layer, 10 m/s at roof height"]))
    # 3. the mesh: polygon cut through the real cells, geometry behind it, the cut solids capped
    w.dissolve(); extra = mesh_cut(S)
    shot(S, w, [((-5, Y_CUT - 190, 42), (8, Y_CUT, 22)), ((-14, Y_CUT - 105, 30), (-4, Y_CUT, 21)), ((-16, Y_CUT - 60, 25), (-12, Y_CUT, 20.5))], 4.5,
         dict(kicker="MESH", head="snappyHexMesh, 2.6 million cells",
              lines=["six refinement levels: 4 m in the far field to 6 cm across the flues",
                     "95 % hexahedra, max non-orthogonality 31°, skewness 0.37"]))
    for e in extra: p.remove_actor(e)
    for _, _, act in S["geo"]: act.SetVisibility(True)
    # 4. the wind: |U| on the centre plane behind, streamlines of the computed velocity in front, released upwind above roof height
    w.dissolve(); vs = velocity_slice(S); sl = streamlines(S); tmax = float(sl["IntegrationTime"].max()); hold = {"a": None}
    def grow(t):
        vs.GetProperty().SetOpacity(0.92 * ease(t / 0.2))
        if hold["a"] is not None: p.remove_actor(hold["a"])
        part = sl.threshold([0.0, max(tmax * ease((t - 0.1) / 0.75), 0.2)], scalars="IntegrationTime")
        if part.n_points: hold["a"] = p.add_mesh(part.extract_geometry().tube(radius=0.09, n_sides=8), color="#23272e",
                                                 smooth_shading=True, specular=0.4, specular_power=30, render=False)
    shot(S, w, [((-95, -128, 58), (12, 0, 13)), ((-25, -150, 62), (28, 0, 13)), ((55, -140, 56), (40, 0, 12))], 5.0,
         dict(kicker="PHYSICS AND NUMERICS", head="Steady RANS, realizable k-ε",
              lines=["log-law atmospheric inflow, z0 = 0.3 m, rough-ground wall functions",
                     "SIMPLEC   ·   second-order linearUpwind   ·   GAMG"]), update=grow)
    if hold["a"] is not None: p.remove_actor(hold["a"])
    p.remove_actor(vs)
    # 5. the tracers forming, then the exhaust plume
    w.dissolve(); st = {"c": None, "f": None}
    def form(t):
        if st["c"] is not None: p.remove_actor(st["c"])
        iso = cloud_surface(S, max(0.85 - 0.75 * ease(t / 0.55), 0.10))
        if iso.n_points: st["c"] = add_cloud(S, iso)
        fa = ease((t - 0.55) / 0.25)
        if fa > 0:
            if st["f"] is None: st["f"] = p.add_mesh(S["plume"], color="#b5443c", opacity=0.0, smooth_shading=True, specular=0.3, render=False)
            st["f"].GetProperty().SetOpacity(0.8 * fa)
    shot(S, w, [((60, -95, 40), (14, 0, 13)), ((10, -118, 56), (8, 0, 13)), ((-60, -100, 54), (4, 0, 12))], 5.5,
         dict(kicker="TAGGED SCALARS", head="12 passive tracers, one per source",
              lines=["carried on the converged flow: chiller discharge in colour, exhaust in red",
                     "each receptor's air traced back to where it came from"]), update=form)
    # 6. verification and validation, on a high pull-back
    w.dissolve()
    shot(S, w, [((-60, -100, 54), (4, 0, 12)), ((-25, -125, 88), (8, 0, 10)), ((20, -125, 112), (12, 6, 6))], 4.5,
         dict(kicker="VERIFICATION AND VALIDATION", head="Checked before it was trusted",
              lines=["validated against two wind-tunnel datasets: AIJ Case H, IRSST R-848",
                     "three-mesh grid study: 0.3 % on chiller rise, 3 % on dilution",
                     "acceptance limits fixed before every run"]))
    # 7. end card: the scene keeps moving under a white wash
    n = nframes(3.5); keys = [((20, -125, 112), (12, 6, 6)), ((55, -108, 122), (12, 6, 6))]
    for i in range(n):
        t = i / max(n - 1, 1); cam(S, keys, t); p.render()
        img = Image.fromarray(p.screenshot(return_img=True)[:, :, :3]); wash = ease(t / 0.3) * 0.86
        img = Image.blend(img, Image.new("RGB", img.size, "white"), wash); d = ImageDraw.Draw(img); al = ease((t - 0.15) / 0.3)
        col = lambda c: tuple(int(255 + (v - 255) * al) for v in c)
        x0 = int(W * 0.08)
        d.rectangle([(x0, int(H * 0.30)), (x0 + int(70 * al), int(H * 0.30) + 6)], fill=col(ACCENT))
        d.text((x0, int(H * 0.34)), "Chiller discharge recirculates at every wind direction.", font=F(50, True), fill=col(INK))
        d.text((x0, int(H * 0.34) + 70), "A 6 m flue clears the intake, except with the flues straight upwind.", font=F(50, True), fill=col(INK))
        d.text((x0, int(H * 0.70)), "Saleh Mohammadrezaei", font=F(40, True), fill=col(INK))
        d.text((x0, int(H * 0.70) + 56), "github.com/SalehMohammadrezaei/rooftop-exhaust-cfd", font=F(34), fill=col(BLUE))
        w.add(img)

def mesh_cut(S):
    """polygon slice of the real cells at y = Y_CUT, tinted by refinement level; near-side geometry hidden"""
    pv, p = S["pv"], S["p"]
    s = S["cells"].slice(normal=(0, 1, 0), origin=(0, Y_CUT, 0), generate_triangles=False)
    c = s.cell_centers().points; s = s.extract_cells(np.where((c[:, 0] > -80) & (c[:, 0] < 100) & (c[:, 2] < 52))[0]).extract_surface(algorithm="dataset_surface")
    size = np.sqrt(np.abs(s.compute_cell_sizes(length=False, volume=False)["Area"])); s.cell_data["level"] = np.clip(np.log2(4.0 / size), 0, 6)
    cmap = S["LSC"].from_list("lvl", ["#fbfaf7", "#e6edf2", "#c9dbe8"])
    acts = [p.add_mesh(s, scalars="level", cmap=cmap, clim=[0, 6], show_edges=True, edge_color="#3a414c", line_width=0.9,
                       ambient=0.85, diffuse=0.15, show_scalar_bar=False, render=False)]
    for n, surf, act in S["geo"]:
        act.SetVisibility(False); g = surf.clip(normal=(0, -1, 0), origin=(0, Y_CUT, 0))
        if g.n_points: acts.append(p.add_mesh(g, color=S["COL"][S["kind"](n)], specular=0.12, ambient=0.28, diffuse=0.78, render=False))
    # section caps where the cut passes through solids: hall, parapet strips, the five chillers of the second row
    y = Y_CUT - 0.03
    def cap(x0, x1, z0, z1, color):
        q = pv.Rectangle([(x0, y, z0), (x1, y, z0), (x1, y, z1)]); acts.append(p.add_mesh(q, color=color, ambient=0.7, diffuse=0.3, render=False))
    cap(-30, 30, 0, 15, "#d8d4cc"); cap(-30, -29.5, 15, 16.2, "#c8c3ba"); cap(29.5, 30, 15, 16.2, "#c8c3ba")
    for i in range(5):
        xc = -12 + (i - 2) * 4.5; cap(xc - 1.2, xc + 1.2, 15, 17.5, "#4e6a86")
    return acts

def velocity_slice(S):
    """|U| on the plane y = 0.3 m (off the cell faces), cropped to the near field"""
    sl = S["pts"].slice(normal=(0, 1, 0), origin=(0, 0.3, 0))
    c = sl.cell_centers().points; sl = sl.extract_cells(np.where((c[:, 0] > -75) & (c[:, 0] < 150) & (c[:, 2] < 34))[0]).extract_surface(algorithm="dataset_surface")
    sl["umag"] = np.linalg.norm(sl["U"], axis=1)
    return S["p"].add_mesh(sl, scalars="umag", cmap=S["cmc"].lapaz, clim=[0, 12], opacity=0.0, ambient=0.85, diffuse=0.15,
                           show_scalar_bar=False, render=False)

def streamlines(S):
    """released on the near side of the centre plane only, from roof height upwards, so none crosses the section"""
    pv = S["pv"]
    ys, zs = np.linspace(-18, -2.5, 8), np.array([15.8, 16.8, 18.2, 20.5, 24.0])
    seeds = pv.PolyData(np.array([(-70.0, yy, zz) for yy in ys for zz in zs]))
    sl = S["pts"].streamlines_from_source(seeds, vectors="U", integration_direction="forward", max_length=260.0,
                                          initial_step_length=0.4, max_step_length=0.8, terminal_speed=0.05)
    sl = sl.clip(normal=(1, 0, 0), origin=(160, 0, 0)).clip(normal=(0, 1, 0), origin=(0, 0.0, 0))
    return sl

def main():
    global QUICK
    ap = argparse.ArgumentParser(); ap.add_argument("--case", required=True); ap.add_argument("--time", type=float, required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--frames", required=True); ap.add_argument("--quick", action="store_true"); a = ap.parse_args()
    QUICK = a.quick; a.case = os.path.expanduser(a.case); shutil.rmtree(a.frames, ignore_errors=True); os.makedirs(a.frames)
    w = Writer(a.frames); run(a, w)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(a.frames, "%05d.jpg"),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow", "-movflags", "+faststart", a.out], check=True)
    print("wrote", a.out, w.n, "frames", round(w.n / FPS, 1), "s")

if __name__ == "__main__":
    main()
