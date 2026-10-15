#!/usr/bin/env python3
"""Shaded 3D view of the hall and its roof plant from the STL set (headless, PyVista + OSMesa).

    conda activate viz
    python postproc/render/geometry.py <triSurface_dir> --out results/applied/figures/geometry.png

One colour per element kind, soft lighting, no axes. The view is from the south-west, 30 deg
elevation, which shows the chiller rows, the intake and the flues in one frame.
"""
import argparse, os, glob
import pyvista as pv

COL = {"hall": "#e7e4df", "parapet": "#d9d5ce", "chiller_body": "#6f8aa6", "chiller_in": "#4e6a86",
       "chiller_out": "#c98b2a", "flue_wall": "#b5443c", "flue_exit": "#8c2f29",
       "intake_body": "#8aa37b", "intake_louvre": "#5b8c5a"}

def kind(name):
    for k in ("chiller_in", "chiller_out", "intake_louvre", "chiller_body", "flue_wall", "flue_exit", "intake_body", "parapet", "hall"):
        if name.startswith(k): return k
    return "hall"

ANCHORS = {"chillers": (-12, 0, 17.5), "flues": (25, 0, 18.5), "intake": (12, 0, 18), "parapet": (0, 20, 16.2),
           "wind_a": (-66, -8, 22), "wind_b": (-42, -8, 22), "roof_corner": (-30, -20, 15)}

def export_anchors(p, path, extra=None):
    """Display coordinates (pixels from the top-left of the uncropped image) of named world points,
    so a matplotlib pass can place labels and leader lines in the house style."""
    import json, vtk
    p.render(); w, h = p.window_size; out = {}
    pts = dict(ANCHORS); pts.update(extra or {})
    for k, (x, y, z) in pts.items():
        c = vtk.vtkCoordinate(); c.SetCoordinateSystemToWorld(); c.SetValue(x, y, z)
        dx, dy = c.GetComputedDisplayValue(p.renderer); out[k] = [dx, h - dy]
    out["_size"] = [w, h]; json.dump(out, open(path, "w"), indent=1)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("tri"); ap.add_argument("--out", required=True)
    ap.add_argument("--size", nargs=2, type=int, default=[2400, 1500]); ap.add_argument("--view", default="sw"); ap.add_argument("--anchors", default=None)
    a = ap.parse_args()
    pv.global_theme.background = "white"
    p = pv.Plotter(off_screen=True, window_size=a.size, lighting="three lights")
    for f in sorted(glob.glob(os.path.join(a.tri, "*.stl"))):
        n = os.path.basename(f)[:-4]
        if n == "preview_all": continue
        m = pv.read(f)
        p.add_mesh(m, color=COL[kind(n)], smooth_shading=False, specular=0.15, specular_power=20, ambient=0.25, diffuse=0.8)
    # ground: a pale plane larger than the hall so the box has a footprint
    g = pv.Plane(center=(0, 0, -0.01), direction=(0, 0, 1), i_size=140, j_size=110)
    p.add_mesh(g, color="#f4f3f0", ambient=0.5, diffuse=0.5)
    p.enable_ssao(radius=4, bias=0.1, kernel_size=64, blur=True)
    p.enable_anti_aliasing("ssaa")
    views = {"sw": ((-95, -120, 70), (0, 0, 9), (0, 0, 1)), "se": ((110, -120, 70), (0, 0, 9), (0, 0, 1)),
             "top": ((0, -1, 220), (0, 0, 0), (0, 1, 0))}
    p.camera_position = views[a.view]
    p.camera.zoom(1.25)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    if a.anchors: export_anchors(p, a.anchors)
    p.screenshot(a.out, transparent_background=False)
    print("wrote", a.out)

if __name__ == "__main__":
    main()
