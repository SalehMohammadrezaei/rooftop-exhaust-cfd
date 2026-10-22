#!/usr/bin/env python3
"""A one-minute motion graphic of the rooftop study, rendered headless and assembled with ffmpeg.

    conda activate viz
    python postproc/video/make_video.py --case ~/scratch/openfoam_cases/applied/D0_dir000_U10 --time 7000 --out results/video/rooftop_exhaust_cfd.mp4

Segments (30 fps, 1920 x 1080):
  1. title card                                   4 s
  2. geometry orbit with labels fading in        10 s
  3. tracer cloud growing, flue plume appearing  15 s
  4. results chart, bars growing                 12 s
  5. source-to-receptor matrix and the finding    9 s
  6. closing card with the repository address     4 s
Frames are written as JPEG to a scratch folder and encoded with libx264. Fonts: Nimbus Sans.
"""
import argparse, glob, json, math, os, subprocess, sys, shutil
import numpy as np
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "render"))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

W, H, FPS = 1920, 1080, 30
QUICK = "--quick" in sys.argv          # ten times shorter segments for a layout test
def secs(n): return max(int(n * FPS / (10 if QUICK else 1)), 3)
INK, GREY, LIGHT, CFD, CFD2, CFD3 = "#1b1f24", "#7a818c", "#d6dae0", "#1f6f8b", "#c98b2a", "#b5443c"
FONT = "/usr/share/fonts/opentype/urw-base35/NimbusSans-Regular.otf"; FONTB = "/usr/share/fonts/opentype/urw-base35/NimbusSans-Bold.otf"
if not os.path.exists(FONTB): FONTB = FONT

def font(size, bold=False): return ImageFont.truetype(FONTB if bold else FONT, size)
def ease(t): return 0.5 - 0.5 * math.cos(math.pi * min(max(t, 0), 1))
def blank(): return Image.new("RGB", (W, H), "white")

class Writer:
    def __init__(self, folder): self.folder = folder; self.n = 0; os.makedirs(folder, exist_ok=True)
    def add(self, im): im.save(os.path.join(self.folder, f"{self.n:05d}.jpg"), quality=93); self.n += 1
    def crossfade(self, a, b, frames):
        for i in range(frames): self.add(Image.blend(a, b, ease((i + 1) / frames)))

def text(draw, xy, s, size, color=INK, bold=False, anchor="la", alpha=1.0):
    draw.text(xy, s, font=font(size, bold), fill=fade(color, alpha), anchor=anchor)

def fade(color, a):
    r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
    return (int(255 + (r - 255) * a), int(255 + (g - 255) * a), int(255 + (b - 255) * a))

def card(lines, hold, writer, sub=None, url=None):
    """lines: list of (text, size, bold); fades in over 1 s, holds, returns last frame."""
    for i in range(hold):
        a = ease(i / max(secs(1), 1)); im = blank(); d = ImageDraw.Draw(im); y = H * 0.36
        for s, size, b in lines:
            text(d, (W * 0.08, y), s, size, bold=b, alpha=a); y += size * 1.35
        if sub: text(d, (W * 0.08, y + 30), sub, 34, color=GREY, alpha=a)
        text(d, (W * 0.08, H * 0.80), "Saleh Mohammadrezaei", 36, bold=True, alpha=a)
        text(d, (W * 0.08, H * 0.80 + 48), url or "github.com/SalehMohammadrezaei/rooftop-exhaust-cfd", 30, color=CFD, alpha=a)
        d.line([(W * 0.08, H * 0.33), (W * 0.08 + 220 * a, H * 0.33)], fill=fade(CFD2, a), width=6)
        writer.add(im)
    return im

FOOTER = "Saleh Mohammadrezaei   ·   github.com/SalehMohammadrezaei/rooftop-exhaust-cfd"

def footer(im):
    d = ImageDraw.Draw(im); text(d, (W * 0.97, H * 0.045), FOOTER, 24, color=GREY, anchor="rm")
    return im

def caption(im, s, sub=None, alpha=1.0):
    """caption band at the bottom: title and one explanatory line; the name and address sit top right"""
    d = ImageDraw.Draw(im); d.rectangle([(0, H * 0.86), (W, H)], fill="white")
    d.line([(W * 0.05, H * 0.885), (W * 0.05 + 60, H * 0.885)], fill=fade(CFD2, alpha), width=5)
    text(d, (W * 0.05, H * 0.9), s, 40, bold=True, alpha=alpha)
    if sub: text(d, (W * 0.05, H * 0.9 + 56), sub, 27, color=GREY, alpha=alpha)
    return footer(im)

def path(keys, t):
    """Catmull-Rom through camera keyframes [(pos, focal), ...] at parameter t in [0, 1]"""
    pts = np.array([k[0] for k in keys]); foc = np.array([k[1] for k in keys]); n = len(keys) - 1
    u = min(max(t, 0), 1) * n; i = min(int(u), n - 1); f = u - i
    def cr(P):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, n)]
        return 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f * f + (-p0 + 3 * p1 - 3 * p2 + p3) * f ** 3)
    return cr(pts), cr(foc)

def render_segments(a, writer):
    import pyvista as pv, cmcrameri.cm as cmc, vtk
    from geometry import COL, kind, ANCHORS
    pv.global_theme.background = "white"
    p = pv.Plotter(off_screen=True, window_size=(W, H), lighting="three lights")
    tri = os.path.join(a.case, "constant", "triSurface")
    for f in sorted(glob.glob(os.path.join(tri, "*.stl"))):
        n = os.path.basename(f)[:-4]
        if n != "preview_all": p.add_mesh(pv.read(f), color=COL[kind(n)], specular=0.12, specular_power=15, ambient=0.28, diffuse=0.78)
    p.add_mesh(pv.Plane(center=(0, 0, -0.01), direction=(0, 0, 1), i_size=4000, j_size=4000), color="#f4f3f0", ambient=0.5, diffuse=0.5)
    p.enable_anti_aliasing("ssaa"); p.enable_ssao(radius=5, bias=0.1, kernel_size=48, blur=True)
    def cam(keys, t):
        pos, foc = path(keys, t); p.camera_position = (tuple(pos), tuple(foc), (0, 0, 1)); p.camera.view_angle = 32
    def proj(pt):
        c = vtk.vtkCoordinate(); c.SetCoordinateSystemToWorld(); c.SetValue(*pt); dx, dy = c.GetComputedDisplayValue(p.renderer); return dx, H - dy
    def frame(labels=None, cap=None, sub=None, lab_alpha=1.0):
        img = Image.fromarray(p.screenshot(return_img=True)[:, :, :3]); d = ImageDraw.Draw(img)
        if labels:
            for key, s, (tx, ty) in labels:
                x, y = proj(ANCHORS.get(key) or key); tx, ty = tx * W, ty * H
                d.line([(x, y), (tx, ty)], fill=fade(INK, lab_alpha), width=2)
                tw = d.textlength(s, font=font(30)); d.rectangle([(tx - tw / 2 - 10, ty - 22), (tx + tw / 2 + 10, ty + 22)], fill=fade("#ffffff", lab_alpha) if lab_alpha >= 1 else None)
                d.text((tx, ty), s, font=font(30), fill=fade(INK, lab_alpha), anchor="mm")
        if cap: caption(img, cap, sub)
        return img
    foam = os.path.join(a.case, "case.foam"); open(foam, "a").close()
    rd = pv.OpenFOAMReader(foam); rd.set_active_time_value(a.time); rd.disable_all_cell_arrays()
    for n in ("sAll", "sF", "U"): rd.enable_cell_array(n)
    rd.disable_all_patch_arrays(); rd.enable_patch_array("internalMesh")
    cells = rd.read()["internalMesh"]; mesh = cells.cell_data_to_point_data()
    # ---- 2. the question
    keys2 = [((-170, -60, 14), (-20, 0, 12)), ((-110, -110, 40), (-5, 0, 12)), ((-10, -130, 70), (5, 0, 10)), ((95, -95, 60), (10, 0, 10)), ((125, -30, 42), (10, 0, 10))]
    labels = [("chillers", "ten air-cooled chillers", (0.22, 0.12)), ("flues", "four generator flues", (0.82, 0.14)),
              ("intake", "fresh-air intake", (0.60, 0.09)), ("parapet", "parapet 1.2 m", (0.42, 0.20))]
    n2 = secs(6)
    for i in range(n2):
        t = i / n2; cam(keys2, t); p.render(); la = ease((t - 0.3) / 0.15) * (1 - ease((t - 0.85) / 0.1))
        writer.add(frame(labels if la > 0.02 else None, "The question", "does warm chiller discharge return to the chiller inlets, and does exhaust reach the intake?", lab_alpha=la))
    # ---- 3. the mesh
    # the real cells: one layer of hexahedra whose centres straddle the plane y = 7.5 m, within the view box
    cc = cells.cell_centers().points; size = np.abs(cells.compute_cell_sizes(length=False, area=False)["Volume"]) ** (1 / 3)
    pick = (np.abs(cc[:, 1] - 7.5) < 0.5 * size) & (cc[:, 0] > -60) & (cc[:, 0] < 70) & (cc[:, 2] < 45)
    cut = cells.extract_cells(np.where(pick)[0]).extract_surface()
    cut_actor = p.add_mesh(cut, color="#f7f6f3", show_edges=True, edge_color="#4a5260", line_width=1, ambient=0.6, diffuse=0.4, render=False)
    keys3 = [((-40, -130, 42), (-5, 7.5, 14)), ((-28, -85, 30), (-10, 7.5, 16)), ((-22, -62, 24), (-12, 7.5, 17))]
    n3 = secs(5)
    for i in range(n3):
        t = i / n3; cam(keys3, t); p.render()
        writer.add(frame(None, "The mesh", "2.6 million cells, 4 m in the far field down to 0.125 m at the chiller discharge"))
    p.remove_actor(cut_actor, render=False)
    # ---- 4. the wind
    seeds = pv.Plane(center=(-70, 0, 9), direction=(1, 0, 0), i_size=70, j_size=16, i_resolution=24, j_resolution=5)
    sl = mesh.streamlines_from_source(seeds, vectors="U", integration_direction="forward", max_length=260.0, initial_step_length=0.5, max_step_length=1.0, terminal_speed=0.05)
    sl["speed"] = np.linalg.norm(sl["U"], axis=1); tmax = float(sl["IntegrationTime"].max())
    keys4 = [((-150, -120, 45), (-10, 0, 14)), ((-60, -140, 55), (0, 0, 14)), ((40, -120, 50), (10, 0, 14)), ((110, -70, 40), (20, 0, 12))]
    n4 = secs(6); sl_actor = None
    for i in range(n4):
        t = i / n4; cam(keys4, t); T = tmax * min(1.0, ease(t / 0.75) * 1.05)
        part = sl.threshold([0.0, max(T, 0.3)], scalars="IntegrationTime")
        if sl_actor is not None: p.remove_actor(sl_actor, render=False)
        sl_actor = p.add_mesh(part, scalars="speed", cmap=cmc.lapaz, clim=[0, 12], line_width=4, opacity=0.95, render_lines_as_tubes=True, show_scalar_bar=False, render=False)
        p.render(); writer.add(frame(None, "The wind", "a neutral atmospheric boundary layer, 10 m/s at roof height; the hall lifts it, the plant deck slows it"))
    p.remove_actor(sl_actor, render=False)
    # ---- 5. the tracers
    keys5 = [((110, -70, 40), (20, 0, 12)), ((40, -120, 62), (10, 0, 12)), ((-50, -110, 58), (5, 0, 12)), ((-110, -40, 45), (10, 0, 10)), ((-70, 60, 55), (15, 0, 10))]
    n5 = secs(8); actor = None; flue_actor = None
    for i in range(n5):
        t = i / n5; cam(keys5, t); level = max(0.85 - 0.75 * ease(t / 0.45), 0.10)
        if actor is not None: p.remove_actor(actor, render=False)
        iso = mesh.contour([level], scalars="sAll")
        if iso.n_points:
            iso["h"] = iso.points[:, 2] - 15.0
            actor = p.add_mesh(iso, scalars="h", cmap=cmc.batlow, clim=[0, 12], opacity=0.5, smooth_shading=True, show_scalar_bar=False, specular=0.2, render=False)
        fa = ease((t - 0.55) / 0.2)
        if fa > 0:
            if flue_actor is None:
                flue = mesh.contour([0.05], scalars="sF"); flue_actor = p.add_mesh(flue, color=CFD3, opacity=0.0, smooth_shading=True, render=False)
            flue_actor.GetProperty().SetOpacity(0.75 * fa)
        p.render()
        if t < 0.55: cap, sub = "Tagging the sources", "one passive scalar per source: the cloud is air that came from the chillers"
        else: cap, sub = "The exhaust plume", "the flue scalar; every receptor's air is traced back to where it came from"
        writer.add(frame(None, cap, sub))
    return frame(None, cap, sub)

def validation_segment(writer, results, seconds=5):
    """the V2 comparison drawn progressively: tunnel points, then the CFD line sweeping in"""
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.font_manager as fm
    fm.fontManager.addfont(FONT); plt.rcParams.update({"font.family": "Nimbus Sans", "font.size": 22, "axes.edgecolor": INK, "text.color": INK, "axes.labelcolor": INK,
                                                       "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False})
    v2 = os.path.join(os.path.dirname(results.rstrip("/")), "V2")
    cases = [("hs1_M1_run1", "stack 1 m, M = 1", "met"), ("hs1_M3_run1", "stack 1 m, M = 3", "not met"), ("hs3_M1_run1", "stack 3 m, M = 1", "met"), ("hs3_M3_run1", "stack 3 m, M = 3", "not met")]
    data = []
    for name, title, verdict in cases:
        r = json.load(open(os.path.join(v2, name + ".json")))["receptors"]["s04"]
        data.append((title, verdict, np.array([q["x_m"] for q in r]), np.array([q["DN_exp"] for q in r]), np.array([q["DN_cfd"] for q in r])))
    nf = secs(seconds)
    for i in range(nf):
        t = i / nf; g = ease((t - 0.15) / 0.55)
        fig, axs = plt.subplots(1, 4, figsize=(W / 100, H / 100), dpi=100, sharey=True, gridspec_kw={"left": 0.07, "right": 0.98, "top": 0.84, "bottom": 0.32, "wspace": 0.12})
        for ax, (title, verdict, x, e, c) in zip(axs, data):
            ax.fill_between(x, e / 2, e * 2, color=LIGHT, lw=0); ax.plot(x, e, "o", color=INK, ms=9)
            k = max(int(g * len(x)), 1 if g > 0 else 0)
            if k: ax.plot(x[:k], c[:k], "-", color=CFD, lw=4)
            ax.set_yscale("log"); ax.set_ylim(0.05, 20); ax.set_xlim(0, 52); ax.set_title(title, loc="left", fontsize=26)
            if t > 0.8: ax.text(0.96, 0.05, verdict, transform=ax.transAxes, ha="right", fontsize=26, color=INK if verdict == "met" else CFD3)
            ax.set_xlabel("distance downwind [m]")
        axs[0].set_ylabel("dilution"); axs[0].text(5, 10, "wind tunnel", fontsize=22); axs[0].text(5, 6, "CFD", fontsize=22, color=CFD)
        fig.canvas.draw(); img = Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba(), "raw", "RGBA", 0, 1).convert("RGB"); plt.close(fig)
        writer.add(caption(img.resize((W, H)), "Validated first", "a rooftop stack against the IRSST wind tunnel: trusted where it matched, bounded where it did not"))
    return img.resize((W, H))

def chart_segment(writer, results):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.font_manager as fm, re
    fm.fontManager.addfont(FONT); plt.rcParams.update({"font.family": "Nimbus Sans", "font.size": 22, "axes.edgecolor": INK, "text.color": INK, "axes.labelcolor": INK,
                                                       "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False})
    rows = []
    for f in sorted(glob.glob(os.path.join(results, "*.json"))):
        r = json.load(open(f)); m = re.match(r"(D\d)_dir(\d+)_U([\d.]+)$", r.get("case", ""))
        if m: rows.append((int(m.group(2)), float(m.group(3)), {"D0": 3, "D1": 6, "D2": 9}[m.group(1)], r))
    rows.sort(key=lambda t: (t[0], t[1], t[2]))
    lab = [f"{d}°, {u:g} m/s, tip {tip} m" for d, u, tip, _ in rows]
    dil = np.array([r["intake_dilution_flues"] for *_, r in rows]); mean = np.array([r["chiller_rise_mean_K"] for *_, r in rows]); worst = np.array([r["chiller_rise_max_K"] for *_, r in rows])
    y = np.arange(len(rows)); n4 = secs(5)
    for i in range(n4):
        t = i / n4; g = ease(t / 0.5); fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(W / 100, H / 100), dpi=100, gridspec_kw={"wspace": 0.08, "left": 0.19, "right": 0.97, "top": 0.9, "bottom": 0.3})
        for ax in (ax1, ax2): ax.set_yticks(y); ax.set_ylim(len(rows) - 0.5, -0.5); ax.tick_params(axis="y", length=0)
        ax1.set_yticklabels(lab); ax2.tick_params(labelleft=False)
        ax1.barh(y, 10 * (dil / 10) ** g, color=[CFD if v >= 2000 else CFD3 for v in dil], height=0.62)
        ax2.barh(y, mean * g, color=[CFD if v <= 2 else CFD3 for v in mean], height=0.62)
        if t > 0.5: ax2.plot(worst, y, "o", color=INK, ms=9)
        ax1.set_xscale("log"); ax1.set_xlim(10, 1e9); ax1.axvline(2000, color=INK, lw=1.5, ls="--"); ax1.set_xlabel("flue dilution at the intake (limit 2,000)")
        ax2.axvline(2, color=INK, lw=1.5, ls="--"); ax2.axvline(4, color=INK, lw=1.5, ls=":"); ax2.set_xlim(0, 15); ax2.set_xlabel("chiller inlet rise [K] (limits 2 K mean, 4 K worst unit)")
        fig.canvas.draw(); img = Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba(), "raw", "RGBA", 0, 1).convert("RGB"); plt.close(fig)
        img = caption(img.resize((W, H)), "Against the limits", "intake dilution at least 2,000; chiller inlet rise at most 2 K mean, 4 K worst unit")
        writer.add(img)
    return img

def matrix_segment(writer, results, seconds=3):
    """the source-to-receptor matrix revealed column by column, with the chiller-rise bars growing"""
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.font_manager as fm
    from matplotlib.colors import LogNorm; import cmcrameri.cm as cmc
    fm.fontManager.addfont(FONT); plt.rcParams.update({"font.family": "Nimbus Sans", "font.size": 22, "axes.edgecolor": INK, "text.color": INK, "axes.labelcolor": INK,
                                                       "xtick.color": INK, "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False})
    r = json.load(open(os.path.join(results, "D0_dir000_U10.json"))); S, R, F = r["sources"], r["receptors"], np.array(r["F"])
    slab = [x.replace("sC", "chiller ").replace("sF", "flues") for x in S]
    rlab = [x.replace("chiller_in_", "chiller ").replace("intake_louvre_pos", "intake +y").replace("intake_louvre_neg", "intake −y") for x in R]
    rise = np.array(r["chiller_inlet_temperature_rise_K"]); n = len(rise); units = np.arange(1, n + 1); nf = secs(seconds)
    for i in range(nf):
        t = i / nf; g = ease(t / 0.6); k = min(int(g * (len(S) + 1)), len(S))
        fig = plt.figure(figsize=(W / 100, H / 100), dpi=100); gs = fig.add_gridspec(1, 2, width_ratios=[1.25, 1], left=0.12, right=0.96, top=0.88, bottom=0.3, wspace=0.45)
        ax = fig.add_subplot(gs[0]); M = np.clip(F, 1e-6, 1).copy(); M[:, k:] = np.nan
        ax.imshow(M, cmap=cmc.davos_r, norm=LogNorm(1e-4, 1), aspect="auto"); ax.set_xticks(range(len(S))); ax.set_xticklabels(slab, rotation=90); ax.set_yticks(range(len(R))); ax.set_yticklabels(rlab)
        for sp in ax.spines.values(): sp.set_visible(False)
        ax.tick_params(length=0); ax.set_title("fraction of each receptor's air from each source", loc="left", fontsize=26)
        ax2 = fig.add_subplot(gs[1]); ax2.barh(units, rise * g, color=[CFD3 if v > 4 else CFD2 if v > 2 else CFD for v in rise], height=0.7)
        ax2.axvline(2, color=INK, lw=1.5, ls="--"); ax2.axvline(4, color=INK, lw=1.5, ls=":"); ax2.set_yticks(units); ax2.set_yticklabels([f"chiller {u}" for u in units]); ax2.invert_yaxis()
        ax2.set_xlim(0, 12); ax2.set_xlabel("inlet temperature rise [K]"); ax2.set_title("limits 2 K mean, 4 K worst unit", loc="left", fontsize=26)
        fig.canvas.draw(); img = Image.frombuffer("RGBA", fig.canvas.get_width_height(), fig.canvas.buffer_rgba(), "raw", "RGBA", 0, 1).convert("RGB"); plt.close(fig)
        writer.add(caption(img.resize((W, H)), "Who feeds whom", "each downwind chiller breathes 13 to 17 % of its nearest neighbour: the layout, not the wind"))
    return img.resize((W, H))

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--case", required=True); ap.add_argument("--time", type=float, required=True)
    ap.add_argument("--out", required=True); ap.add_argument("--results", default="results/applied"); ap.add_argument("--frames", default=None)
    ap.add_argument("--skip-render", action="store_true"); ap.add_argument("--quick", action="store_true"); a = ap.parse_args()
    frames = a.frames or os.path.join(os.environ.get("TMPDIR", "/tmp"), "rooftop_video_frames"); shutil.rmtree(frames, ignore_errors=True)
    w = Writer(frames); X = FPS // 2
    last = card([("Rooftop exhaust and heat re-entrainment", 72, True), ("at a data-centre hall", 72, True)], secs(3), w,
                sub="OpenFOAM RANS, validated against wind-tunnel data")
    if not a.skip_render:
        nxt = None
        # peek first geometry frame for the crossfade by rendering segments into a temporary writer
        last_render = render_segments(a, w)
        last = last_render
    chart_first = None
    last = validation_segment(w, a.results, 5)
    last = chart_segment(w, a.results)
    last = matrix_segment(w, a.results, 3)
    card([("Chillers: 3 to 6 times the limit at every wind.", 56, True), ("Intake: a 6 m flue clears the limit,", 56, True),
          ("except with the flues directly upwind of it.", 56, True)], secs(3), w, url="github.com/SalehMohammadrezaei/rooftop-exhaust-cfd")
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(frames, "%05d.jpg"), "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "19", "-movflags", "+faststart", a.out], check=True)
    print("wrote", a.out, w.n, "frames", round(w.n / FPS, 1), "s")

if __name__ == "__main__":
    main()
