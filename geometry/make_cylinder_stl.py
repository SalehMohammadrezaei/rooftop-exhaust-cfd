#!/usr/bin/env python3
"""Write ASCII STL files for a vertical circular stack: the side wall and the top (exit) disc as two
separate files, so that snappyHexMesh can make them two patches (wall and inlet).

    make_cylinder_stl.py xc yc z0 z1 radius nseg name outdir

Writes <outdir>/<name>_wall.stl (side surface, outward normals) and <outdir>/<name>_exit.stl
(top disc, normal +z). The bottom is open: the stack stands on the roof inside the building.
"""
import math, os, sys
xc, yc, z0, z1, r = map(float, sys.argv[1:6]); n = int(sys.argv[6]); name, out = sys.argv[7], sys.argv[8]
pts = [(xc + r * math.cos(2 * math.pi * i / n), yc + r * math.sin(2 * math.pi * i / n)) for i in range(n)]
def facet(f, nrm, tri):
    f.write(f" facet normal {nrm[0]:.6g} {nrm[1]:.6g} {nrm[2]:.6g}\n  outer loop\n")
    for p in tri: f.write("   vertex %.9g %.9g %.9g\n" % p)
    f.write("  endloop\n endfacet\n")
with open(os.path.join(out, name + "_wall.stl"), "w") as f:
    f.write(f"solid {name}_wall\n")
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % n]
        am = math.atan2((ya + yb) / 2 - yc, (xa + xb) / 2 - xc); nrm = (math.cos(am), math.sin(am), 0.0)
        facet(f, nrm, ((xa, ya, z0), (xb, yb, z0), (xb, yb, z1)))
        facet(f, nrm, ((xa, ya, z0), (xb, yb, z1), (xa, ya, z1)))
    f.write(f"endsolid {name}_wall\n")
with open(os.path.join(out, name + "_exit.stl"), "w") as f:
    f.write(f"solid {name}_exit\n")
    for i in range(n):
        (xa, ya), (xb, yb) = pts[i], pts[(i + 1) % n]
        facet(f, (0, 0, 1), ((xc, yc, z1), (xa, ya, z1), (xb, yb, z1)))
    f.write(f"endsolid {name}_exit\n")
print(f"wrote {name}_wall.stl ({2*n} triangles) and {name}_exit.stl ({n} triangles): centre ({xc},{yc}), z {z0}..{z1}, radius {r}")
