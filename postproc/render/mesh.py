#!/usr/bin/env python3
"""Mesh cut-away: the snappyHexMesh refinement around the roof plant (headless PyVista).

    conda activate viz
    python postproc/render/mesh.py <case_dir> --out results/applied/figures/mesh_cut.png

Vertical cut through the chiller rows (y = 7.5 m, the centre of one row) with cell edges drawn,
plus the geometry behind it. Shows the level ladder from the 4 m background cells to the 0.125 m
cells at the chiller discharge.
"""
import argparse, os, glob
import pyvista as pv
from geometry import COL, kind

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("case"); ap.add_argument("--out", required=True)
    ap.add_argument("--y", type=float, default=7.5); ap.add_argument("--size", nargs=2, type=int, default=[2400, 1500]); a = ap.parse_args()
    foam = os.path.join(a.case, "case.foam"); open(foam, "a").close()
    rd = pv.OpenFOAMReader(foam); rd.disable_all_cell_arrays(); rd.disable_all_patch_arrays(); rd.enable_patch_array("internalMesh")
    mesh = rd.read()["internalMesh"]
    cut = mesh.slice(normal=(0, 1, 0), origin=(0, a.y, 0))
    pv.global_theme.background = "white"
    p = pv.Plotter(off_screen=True, window_size=a.size, lighting="three lights")
    for f in sorted(glob.glob(os.path.join(a.case, "constant", "triSurface", "*.stl"))):
        n = os.path.basename(f)[:-4]
        if n == "preview_all": continue
        m = pv.read(f).clip(normal=(0, -1, 0), origin=(0, a.y, 0))      # keep the far half so the cut is in front
        if m.n_points: p.add_mesh(m, color=COL[kind(n)], specular=0.1, ambient=0.3, diffuse=0.75)
    p.add_mesh(cut, color="#f7f6f3", show_edges=True, edge_color="#5a6270", line_width=0.6, ambient=0.6, diffuse=0.4)
    p.enable_anti_aliasing("ssaa")
    p.enable_parallel_projection()
    p.camera_position = ((-12, -200, 19), (-12, a.y, 19), (0, 0, 1)); p.camera.parallel_scale = 11   # half-height of the view in metres
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    p.screenshot(a.out); print("wrote", a.out)

if __name__ == "__main__":
    main()
