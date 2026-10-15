#!/usr/bin/env python3
"""3D view of the recirculating chiller air and the flue plume on the roof (headless PyVista).

    conda activate viz
    python postproc/render/flow.py <case_dir> --time 5000 --out results/applied/figures/D0_dir000_U10_plume.png

Isosurfaces of the all-sources tracer (sAll, the fraction of air that came from any roof source)
at 0.1 (one tenth source air), coloured by height above the roof, over the shaded geometry. The flue tracer
sF is drawn as a separate isosurface at 0.05 so the thin jet is visible beside the chiller cloud.
"""
import argparse, os, glob
import numpy as np, pyvista as pv, cmcrameri.cm as cmc
from geometry import COL, kind, export_anchors

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("case"); ap.add_argument("--time", type=float, required=True); ap.add_argument("--out", required=True)
    ap.add_argument("--iso", nargs="+", type=float, default=[0.1]); ap.add_argument("--flue-iso", type=float, default=0.05); ap.add_argument("--anchors", default=None); ap.add_argument("--size", nargs=2, type=int, default=[2400, 1500])
    a = ap.parse_args()
    foam = os.path.join(a.case, "case.foam"); open(foam, "a").close()
    rd = pv.OpenFOAMReader(foam); rd.set_active_time_value(a.time)
    rd.disable_all_cell_arrays()
    for n in ("sAll", "sF"): rd.enable_cell_array(n)
    rd.disable_all_patch_arrays(); rd.enable_patch_array("internalMesh")
    mesh = rd.read()["internalMesh"].cell_data_to_point_data()
    pv.global_theme.background = "white"
    p = pv.Plotter(off_screen=True, window_size=a.size, lighting="three lights")
    for f in sorted(glob.glob(os.path.join(a.case, "constant", "triSurface", "*.stl"))):
        n = os.path.basename(f)[:-4]
        if n == "preview_all": continue
        p.add_mesh(pv.read(f), color=COL[kind(n)], specular=0.1, ambient=0.3, diffuse=0.75)
    p.add_mesh(pv.Plane(center=(0, 0, -0.01), direction=(0, 0, 1), i_size=200, j_size=140), color="#f4f3f0", ambient=0.5, diffuse=0.5)
    iso = mesh.contour(a.iso, scalars="sAll")
    iso["height above roof [m]"] = iso.points[:, 2] - 15.0
    p.add_mesh(iso, scalars="height above roof [m]", cmap=cmc.batlow, clim=[0, 12], opacity=0.5, smooth_shading=True, specular=0.2,
               scalar_bar_args=dict(title="height above roof [m]", vertical=False, position_x=0.3, position_y=0.04, width=0.4, height=0.06,
                                    title_font_size=28, label_font_size=24, color="#1b1f24", fmt="%.0f", n_labels=5))
    flue = mesh.contour([a.flue_iso], scalars="sF")
    p.add_mesh(flue, color="#b5443c", opacity=0.75, smooth_shading=True)
    p.enable_anti_aliasing("ssaa")
    p.camera_position = ((-70, -170, 95), (15, 0, 8), (0, 0, 1)); p.camera.zoom(1.35)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    if a.anchors: export_anchors(p, a.anchors, {"cloud": (-5, 10, 24), "plume": (32, 0, 21)})
    p.screenshot(a.out); print("wrote", a.out)

if __name__ == "__main__":
    main()
