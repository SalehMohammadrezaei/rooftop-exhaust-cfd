#!/usr/bin/env python3
"""Generate the data-hall geometry as STL files from params/hall_geometry.json.

    make_hall.py params/hall_geometry.json <triSurface_dir> [--flue-tip 3.0] [--rotate DEG]

Writes, with outward normals, one file per patch the case needs (names are the patch names):
  hall.stl            the building walls and roof (minus nothing: plant stands on the roof)
  parapet.stl         zero-thickness vertical strip on the roof perimeter (becomes a baffle)
  chiller_body.stl    the ten chiller boxes, all faces except the intake faces and discharge strips
  chiller_in_NN.stl   two long side faces of chiller NN (sinks, fixed flow)
  chiller_out_NN.stl  discharge strip on top of chiller NN (source, fixed flow)
  flue_wall.stl       the four flue cylinders' sides
  flue_exit.stl       the four exit discs (one patch: the flue group is one tagged scalar)
  intake_body.stl     the intake enclosure, minus the louvres
  intake_louvre_pos.stl / intake_louvre_neg.stl   the two louvres (sinks)
--rotate turns the whole assembly about the z axis at the origin (wind direction), after building it.
"""
import json, math, os, sys
args = sys.argv[1:]; P = json.load(open(args[0])); out = args[1]; os.makedirs(out, exist_ok=True)
tip = float(args[args.index("--flue-tip") + 1]) if "--flue-tip" in args else P["flues"]["tip_above_roof"]
rot = math.radians(float(args[args.index("--rotate") + 1])) if "--rotate" in args else 0.0
def R(p):
    x, y, z = p; c, s = math.cos(rot), math.sin(rot); return (c * x - s * y, s * x + c * y, z)
class STL:
    def __init__(self, name): self.name = name; self.tris = []
    def tri(self, a, b, c):
        a, b, c = R(a), R(b), R(c)
        u = tuple(b[i] - a[i] for i in range(3)); v = tuple(c[i] - a[i] for i in range(3))
        n = (u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]); l = math.sqrt(sum(k*k for k in n)) or 1
        self.tris.append(((n[0]/l, n[1]/l, n[2]/l), (a, b, c)))
    def quad(self, a, b, c, d): self.tri(a, b, c); self.tri(a, c, d)      # counter-clockwise seen from outside
    def write(self):
        with open(os.path.join(out, self.name + ".stl"), "w") as f:
            f.write(f"solid {self.name}\n")
            for n, (a, b, c) in self.tris:
                f.write(f" facet normal {n[0]:.6g} {n[1]:.6g} {n[2]:.6g}\n  outer loop\n")
                for p in (a, b, c): f.write("   vertex %.6g %.6g %.6g\n" % p)
                f.write("  endloop\n endfacet\n")
            f.write(f"endsolid {self.name}\n")
        return len(self.tris)
def box(stl, x0, y0, z0, x1, y1, z1, skip=()):
    """closed box with outward normals; skip faces by name: xmin xmax ymin ymax zmin zmax"""
    if "zmin" not in skip: stl.quad((x0,y0,z0),(x0,y1,z0),(x1,y1,z0),(x1,y0,z0))
    if "zmax" not in skip: stl.quad((x0,y0,z1),(x1,y0,z1),(x1,y1,z1),(x0,y1,z1))
    if "ymin" not in skip: stl.quad((x0,y0,z0),(x1,y0,z0),(x1,y0,z1),(x0,y0,z1))
    if "ymax" not in skip: stl.quad((x0,y1,z0),(x0,y1,z1),(x1,y1,z1),(x1,y1,z0))
    if "xmin" not in skip: stl.quad((x0,y0,z0),(x0,y0,z1),(x0,y1,z1),(x0,y1,z0))
    if "xmax" not in skip: stl.quad((x1,y0,z0),(x1,y1,z0),(x1,y1,z1),(x1,y0,z1))
def rect_frame_top(stl, x0, y0, x1, y1, z, ix0, iy0, ix1, iy1):
    """top face (normal +z) minus an inner rectangle: four quads"""
    stl.quad((x0,y0,z),(x1,y0,z),(x1,iy0,z),(x0,iy0,z)); stl.quad((x0,iy1,z),(x1,iy1,z),(x1,y1,z),(x0,y1,z))
    stl.quad((x0,iy0,z),(ix0,iy0,z),(ix0,iy1,z),(x0,iy1,z)); stl.quad((ix1,iy0,z),(x1,iy0,z),(x1,iy1,z),(ix1,iy1,z))
def rect_frame_y(stl, x0, z0, x1, z1, y, ix0, iz0, ix1, iz1, sign):
    """face normal to y (+y if sign>0) minus an inner rectangle"""
    def q(a,b,c,d): stl.quad(a,b,c,d) if sign > 0 else stl.quad(a,d,c,b)
    q((x0,y,z0),(x0,y,iz0),(x1,y,iz0),(x1,y,z0)); q((x0,y,iz1),(x0,y,z1),(x1,y,z1),(x1,y,iz1))
    q((x0,y,iz0),(x0,y,iz1),(ix0,y,iz1),(ix0,y,iz0)); q((ix1,y,iz0),(ix1,y,iz1),(x1,y,iz1),(x1,y,iz0))
def cylinder(wall, disc, xc, yc, z0, z1, r, n=48):
    pts = [(xc + r*math.cos(2*math.pi*i/n), yc + r*math.sin(2*math.pi*i/n)) for i in range(n)]
    for i in range(n):
        (xa,ya),(xb,yb) = pts[i], pts[(i+1)%n]
        wall.quad((xa,ya,z0),(xb,yb,z0),(xb,yb,z1),(xa,ya,z1)); disc.tri((xc,yc,z1),(xa,ya,z1),(xb,yb,z1))
H = P["hall"]; L, W, Hh = H["length_x"], H["width_y"], H["height"]; roof = Hh
files = {}
hall = STL("hall"); box(hall, -L/2, -W/2, 0, L/2, W/2, Hh, skip=("zmin",)); files["hall"] = hall.write()
par = STL("parapet"); hp = P["parapet"]["height"]
for (a, b) in (((-L/2,-W/2),(L/2,-W/2)), ((L/2,-W/2),(L/2,W/2)), ((L/2,W/2),(-L/2,W/2)), ((-L/2,W/2),(-L/2,-W/2))):
    par.quad((a[0],a[1],roof),(b[0],b[1],roof),(b[0],b[1],roof+hp),(a[0],a[1],roof+hp))
files["parapet"] = par.write()
C = P["chillers"]; body = STL("chiller_body"); k = 0
strip_x = C["flow_m3ps"] / C["discharge_speed_mps"] / C["discharge_strip_y"]
for row in range(C["rows"]):
    yc = (row - (C["rows"]-1)/2) * (C["unit_y"] + C["row_gap_y"])
    for i in range(C["count_per_row"]):
        k += 1; xc = C["centre_x"] + (i - (C["count_per_row"]-1)/2) * C["pitch_x"]
        x0, x1 = xc - C["unit_x"]/2, xc + C["unit_x"]/2; y0, y1 = yc - C["unit_y"]/2, yc + C["unit_y"]/2; z1 = roof + C["unit_height"]
        box(body, x0, y0, roof, x1, y1, z1, skip=("zmin", "xmin", "xmax", "zmax"))
        ix0, ix1 = xc - strip_x/2, xc + strip_x/2; iy0, iy1 = yc - C["discharge_strip_y"]/2, yc + C["discharge_strip_y"]/2
        rect_frame_top(body, x0, y0, x1, y1, z1, ix0, iy0, ix1, iy1)
        cin = STL(f"chiller_in_{k:02d}"); cin.quad((x0,y0,roof),(x0,y0,z1),(x0,y1,z1),(x0,y1,roof)); cin.quad((x1,y0,roof),(x1,y1,roof),(x1,y1,z1),(x1,y0,z1)); files[cin.name] = cin.write()
        cout = STL(f"chiller_out_{k:02d}"); cout.quad((ix0,iy0,z1),(ix1,iy0,z1),(ix1,iy1,z1),(ix0,iy1,z1)); files[cout.name] = cout.write()
files["chiller_body"] = body.write()
F = P["flues"]; fw = STL("flue_wall"); fe = STL("flue_exit"); xf = L/2 - F["inset_from_parapet_x"]
for j in range(F["count"]):
    yf = (j - (F["count"]-1)/2) * F["spacing_y"]; cylinder(fw, fe, xf, yf, roof, roof + tip, F["diameter"]/2)
files["flue_wall"] = fw.write(); files["flue_exit"] = fe.write()
I = P["intake"]; ib = STL("intake_body"); x0, x1 = I["centre_x"] - I["size_x"]/2, I["centre_x"] + I["size_x"]/2; y0, y1 = -I["size_y"]/2, I["size_y"]/2; z1 = roof + I["height"]
box(ib, x0, y0, roof, x1, y1, z1, skip=("zmin", "ymin", "ymax"))
lx0, lx1 = I["centre_x"] - I["louvre_width"]/2, I["centre_x"] + I["louvre_width"]/2; lz0 = roof + (I["height"] - I["louvre_height"])/2; lz1 = lz0 + I["louvre_height"]
rect_frame_y(ib, x0, roof, x1, z1, y1, lx0, lz0, lx1, lz1, +1); rect_frame_y(ib, x0, roof, x1, z1, y0, lx0, lz0, lx1, lz1, -1); files["intake_body"] = ib.write()
lp = STL("intake_louvre_pos"); lp.quad((lx0,y1,lz0),(lx0,y1,lz1),(lx1,y1,lz1),(lx1,y1,lz0)); files[lp.name] = lp.write()
ln = STL("intake_louvre_neg"); ln.quad((lx0,y0,lz0),(lx1,y0,lz0),(lx1,y0,lz1),(lx0,y0,lz1)); files[ln.name] = ln.write()
print(f"wrote {len(files)} STL files to {out} (flue tip {tip} m above the roof, rotation {math.degrees(rot):g} deg); discharge strip {strip_x:.2f} x {C['discharge_strip_y']} m = {strip_x*C['discharge_strip_y']:.1f} m2 per chiller")
for n, t in files.items(): print(f"  {n:20s} {t:4d} triangles")
