#!/usr/bin/env python3
"""Scripted field pictures without a display: sample cutting planes with the standalone postProcess
utility (raw format) and draw them with matplotlib.

    slices.py <case_dir> --time <t> --fields U k [sC01 sF] --out <png_dir> [--planes y0 zroof zint]

Planes: y0 (centre plane y = 0), zroof (horizontal, 1 m above the roof, z = 16),
zint (horizontal at the louvre centre, z = 16.5). Each PNG: filled contours of the field on the
plane with the building outline, a consistent colour map, and the units in the colour bar.
Concentrations are drawn on a log scale.
"""
import argparse, os, subprocess, math
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt, matplotlib.tri as mtri
ap = argparse.ArgumentParser(); ap.add_argument("case"); ap.add_argument("--time", required=True); ap.add_argument("--fields", nargs="+", default=["U"])
ap.add_argument("--out", required=True); ap.add_argument("--planes", nargs="+", default=["y0", "zroof"]); ap.add_argument("--xlim", nargs=2, type=float, default=[-60, 120]); ap.add_argument("--ylim", nargs=2, type=float, default=[-50, 50]); a = ap.parse_args()
PL = {"y0": ("(0 0 0)", "(0 1 0)"), "zroof": ("(0 0 16)", "(0 0 1)"), "zint": ("(0 0 16.5)", "(0 0 1)")}
fo = "slicePlanes\n{\n    type surfaces; libs (sampling); surfaceFormat raw; writeControl writeTime; interpolationScheme cellPoint; interpolate true;\n    fields (" + " ".join(a.fields) + ");\n    surfaces\n    {\n"
for p in a.planes: fo += f"        {p} {{ type cuttingPlane; planeType pointAndNormal; pointAndNormalDict {{ point {PL[p][0]}; normal {PL[p][1]}; }} interpolate true; }}\n"
fo += "    }\n}\n"
open(os.path.join(a.case, "system", "slicePlanes"), "w").write(fo)
env = dict(os.environ); env["BASH_ENV"] = os.path.expanduser("~/opt/openfoam2606.sh")
subprocess.run(["bash", "-c", f"source ~/opt/openfoam2606.sh >/dev/null 2>&1; cd '{a.case}' && postProcess -func slicePlanes -time {a.time} > log.slicePlanes 2>&1"], check=True)
os.makedirs(a.out, exist_ok=True)
d = os.path.join(a.case, "postProcessing", "slicePlanes", a.time)
for p in a.planes:
    for f in a.fields:
        fn = [x for x in os.listdir(d) if x.startswith(f"{f}_{p}") or x.startswith(f"{p}_{f}") or (x.endswith(".raw") and f + "_" in x and p in x)]
        fn = [x for x in os.listdir(d) if x == f"{f}_{p}.raw"] or fn
        if not fn: print("missing", f, p, os.listdir(d)[:5]); continue
        data = np.loadtxt(os.path.join(d, fn[0]), comments="#")
        x, y, z = data[:, 0], data[:, 1], data[:, 2]; vals = data[:, 3:]
        h, v = (x, z) if p == "y0" else (x, y)
        mag = np.linalg.norm(vals, axis=1) if vals.shape[1] == 3 else vals[:, 0]
        tri = mtri.Triangulation(h, v)
        # drop sliver triangles that span the building hole
        cx = h[tri.triangles].mean(axis=1); cz = v[tri.triangles].mean(axis=1)
        if p == "y0": tri.set_mask((np.abs(cx) < 30) & (cz < 15))
        fig, ax = plt.subplots(figsize=(11, 4.2 if p == "y0" else 6.5), dpi=150)
        if f.startswith("s"):
            m = np.clip(mag, 1e-5, 1); cf = ax.tricontourf(tri, np.log10(m), levels=np.linspace(-5, 0, 26), cmap="magma"); cb = fig.colorbar(cf, ax=ax, pad=0.01); cb.set_label(f"log10 {f}  (tracer fraction)")
        else:
            cf = ax.tricontourf(tri, mag, levels=30, cmap="viridis"); cb = fig.colorbar(cf, ax=ax, pad=0.01); cb.set_label(f"|{f}|  [m/s]" if f == "U" else f"{f}  [m2/s2]")
        if p == "y0": ax.add_patch(plt.Rectangle((-30, 0), 60, 15, fc="0.35", ec="k")); ax.set_ylabel("z [m]"); ax.set_ylim(0, 60)
        else: ax.add_patch(plt.Rectangle((-30, -20), 60, 40, fill=False, ec="k", lw=1.5)); ax.set_ylabel("y [m]"); ax.set_ylim(*a.ylim)
        ax.set_xlim(*a.xlim); ax.set_xlabel("x [m]"); ax.set_aspect("equal"); ax.set_title(f"{os.path.basename(os.path.abspath(a.case))}  t={a.time}  plane {p}", fontsize=10)
        fig.tight_layout(); out = os.path.join(a.out, f"{os.path.basename(os.path.abspath(a.case))}_{p}_{f}.png"); fig.savefig(out); plt.close(fig); print("wrote", out)
