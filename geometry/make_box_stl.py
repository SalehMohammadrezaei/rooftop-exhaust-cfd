#!/usr/bin/env python3
"""Write an ASCII STL of an axis-aligned box.  make_box_stl.py xmin ymin zmin xmax ymax zmax name out.stl
Outward normals; two triangles per face.  Used for the V1 building (0.1 x 0.1 x 0.2 m)."""
import sys
x0,y0,z0,x1,y1,z1 = map(float, sys.argv[1:7]); name, out = sys.argv[7], sys.argv[8]
P = {0:(x0,y0,z0),1:(x1,y0,z0),2:(x1,y1,z0),3:(x0,y1,z0),4:(x0,y0,z1),5:(x1,y0,z1),6:(x1,y1,z1),7:(x0,y1,z1)}
faces = [((0,3,2,1),(0,0,-1)),((4,5,6,7),(0,0,1)),((0,1,5,4),(0,-1,0)),((2,3,7,6),(0,1,0)),((1,2,6,5),(1,0,0)),((0,4,7,3),(-1,0,0))]
with open(out,"w") as f:
    f.write(f"solid {name}\n")
    for (a,b,c,d),n in faces:
        for tri in ((a,b,c),(a,c,d)):
            f.write(f" facet normal {n[0]} {n[1]} {n[2]}\n  outer loop\n")
            for i in tri: f.write("   vertex %g %g %g\n" % P[i])
            f.write("  endloop\n endfacet\n")
    f.write(f"endsolid {name}\n")
print(f"wrote {out}: 12 triangles, box ({x0},{y0},{z0})-({x1},{y1},{z1})")
