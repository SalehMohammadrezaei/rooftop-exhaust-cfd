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

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("tri"); ap.add_argument("--out", required=True)
    ap.add_argument("--size", nargs=2, type=int, default=[2400, 1500]); ap.add_argument("--view", default="sw")
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
    p.screenshot(a.out, transparent_background=False)
    print("wrote", a.out)

if __name__ == "__main__":
    main()
