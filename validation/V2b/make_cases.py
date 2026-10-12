#!/usr/bin/env python3
"""V2b: the V2 isolated-building stack cases at full scale (x200) with the applied ABL setup.

    make_cases.py <out_root>      -> <out_root>/V2b/case_hs1_M1, case_hs3_M1

Everything geometric is the V2 case times 200: building 50 x 50 x 15 m, stack 0.6 m diameter with
its wall 0.2 m inside the upwind roof edge, hs 1 and 3 m, domain -125..225 x +-115 x 0..120 m,
background cell 4 m (the brief's far-field size), the same six refinement levels so the stack exit
keeps 10 cells across (0.0625 m). The wind is the applied ABL of decision 0002: log-law family with
z0 0.3 m, U_H 10 m/s at 15 m, kappa 0.4, fixed-shear top, atm wall set on the ground; building and
stack smooth. M = 1 so Ve = 10 m/s; exit turbulence by the same pipe estimate. Receptors 0.2 m above
the roof at 5 to 50 m behind the stack. Criterion (Project.md s.5): dimensionless dilution within
the V2 uncertainty band of the model-scale result (15 % tunnel + 2.6 % digitising).
"""
import math, os, re, shutil, subprocess, sys
root = sys.argv[1]; repo = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
v2 = os.path.join(repo, "validation", "V2", "case_by_hand")
S = 200.0; H = 15.0; UH = 10.0; z0 = 0.3; kappa = 0.4; Cmu = 0.09
ustar = kappa * UH / math.log((H + z0) / z0); tau = ustar ** 2
for name, hs in (("case_hs1_M1", 1.0), ("case_hs3_M1", 3.0)):
    C = os.path.join(root, "V2b", name); shutil.rmtree(C, ignore_errors=True)
    os.makedirs(os.path.join(C, "constant", "triSurface")); os.makedirs(os.path.join(C, "system")); os.makedirs(os.path.join(C, "0.orig", "include"))
    subprocess.run(["python3", os.path.join(repo, "geometry", "make_box_stl.py"), "-50", "-25", "0", "0", "25", "15", "building", os.path.join(C, "constant/triSurface/building.stl")], check=True, capture_output=True)
    subprocess.run(["python3", os.path.join(repo, "geometry", "make_cylinder_stl.py"), "-49.5", "0", "15", str(15 + hs), "0.3", "48", "stack", os.path.join(C, "constant/triSurface")], check=True, capture_output=True)
    # blockMesh: scale the V2 numbers
    b = open(os.path.join(v2, "system/blockMeshDict")).read()
    for k, v in (("H       0.075;", "H       15;"), ("xMin    -0.625;", "xMin    -125;"), ("xMax     1.125;", "xMax     225;"), ("yMin    -0.575;", "yMin    -115;"), ("yMax     0.575;", "yMax     115;"), ("zMax     0.6;", "zMax     120;"), ("dx      0.02;", "dx      4;")):
        assert k in b, k; b = b.replace(k, v)
    b = re.sub(r"/\*.*?\*/", "/*  V2b: the V2 box at full scale (x200), applied ABL.  Background 4 m = the brief's far-field cell.  */", b, count=1, flags=re.S)
    open(os.path.join(C, "system/blockMeshDict"), "w").write(b)
    # snappy: scale every box and keep the levels
    s = open(os.path.join(v2, "system/snappyHexMeshDict")).read()
    def scale_box(m):
        nums = [float(x) * S for x in m.group(2).split()]
        return m.group(1) + " ".join(f"{v:g}" for v in nums) + m.group(3)
    s = re.sub(r"(min \()([-\d. ]+)(\))", scale_box, s); s = re.sub(r"(max \()([-\d. ]+)(\))", scale_box, s)
    if hs > 1.5:
        s = s.replace("max (-47 2 18)", "max (-47 2 20)").replace("max (-48.5 1 16.6)", "max (-48.5 1 18.6)").replace("max (-30 4 20)", "max (-30 4 22)")
    s = s.replace("locationInMesh (-0.5 0.3 0.3);", "locationInMesh (-100 60 60);").replace("minVol 1e-16", "minVol 1e-13")
    open(os.path.join(C, "system/snappyHexMeshDict"), "w").write(s)
    shutil.copy(os.path.join(v2, "system/surfaceFeatureExtractDict"), os.path.join(C, "system/"))
    for f in ("fvSchemes", "fvSolution", "decomposeParDict", "scalarTransport"):
        shutil.copy(os.path.join(v2, "system", f), os.path.join(C, "system", f))
    f = open(os.path.join(C, "system/fvSolution")).read()
    f = re.sub(r"    residualControl.*?\n    \{\n.*?\n    \}\n", "    // no residualControl: convergence on the tracer probes\n", f, flags=re.S); open(os.path.join(C, "system/fvSolution"), "w").write(f)
    # fields: V2 files with the inlet replaced by the ABL family and the ground by the atm wall set; exit values for M = 1
    Ve = UH; ke = 1.5 * (0.05 * Ve) ** 2; le = 0.07 * 0.6; epse = Cmu ** 0.75 * ke ** 1.5 / le; ome = epse / (Cmu * ke)
    open(os.path.join(C, "0.orig/include/ABLConditions"), "w").write(f"kappa {kappa}; Cmu {Cmu}; flowDir (1 0 0); zDir (0 0 1); Uref {UH}; Zref {H}; z0 uniform {z0}; d uniform 0.0;\n")
    def swap_inlet(txt, typ):
        return re.sub(r"    inlet\n    \{.*?\n    \}\n", f"    inlet\n    {{\n        type            {typ};\n        #include        \"include/ABLConditions\"\n        value           uniform 0;\n    }}\n", txt, count=1, flags=re.S)
    U = open(os.path.join(v2, "0.orig/U")).read(); U = swap_inlet(U, "atmBoundaryLayerInletVelocity").replace("value           uniform 0;\n    }\n    outlet", "value           uniform (0 0 0);\n    }\n    outlet")
    U = U.replace("stack_exit  { type fixedValue; value uniform (0 0 18.6); }", f"stack_exit  {{ type fixedValue; value uniform (0 0 {Ve:g}); }}")
    U = U.replace("    top         { type slip; }", f"    top         {{ type fixedShearStress; tau ({tau:.6g} 0 0); value uniform (0 0 0); }}")
    open(os.path.join(C, "0.orig/U"), "w").write(U)
    shutil.copy(os.path.join(v2, "0.orig/p"), os.path.join(C, "0.orig/p"))
    k = swap_inlet(open(os.path.join(v2, "0.orig/k")).read(), "atmBoundaryLayerInletK"); k = re.sub(r"stack_exit  \{ type fixedValue; value uniform [0-9.e+-]+; \}", f"stack_exit  {{ type fixedValue; value uniform {ke:.4g}; }}", k)
    open(os.path.join(C, "0.orig/k"), "w").write(k)
    e = swap_inlet(open(os.path.join(v2, "0.orig/epsilon")).read(), "atmBoundaryLayerInletEpsilon"); e = re.sub(r"stack_exit  \{ type fixedValue; value uniform [0-9.e+-]+; \}", f"stack_exit  {{ type fixedValue; value uniform {epse:.4g}; }}", e)
    e = e.replace("    ground      { type epsilonWallFunction; value $internalField; }", "    #include \"include/ABLConditions\"\n    ground      { type atmEpsilonWallFunction; z0 uniform 0.3; kappa 0.4; Cmu 0.09; value $internalField; }")
    open(os.path.join(C, "0.orig/epsilon"), "w").write(e)
    o = swap_inlet(open(os.path.join(v2, "0.orig/omega")).read(), "atmBoundaryLayerInletOmega"); o = re.sub(r"stack_exit  \{ type fixedValue; value uniform [0-9.e+-]+; \}", f"stack_exit  {{ type fixedValue; value uniform {ome:.4g}; }}", o)
    o = o.replace("    ground      { type omegaWallFunction; value $internalField; }", "    ground      { type atmOmegaWallFunction; z0 uniform 0.3; kappa 0.4; Cmu 0.09; value $internalField; }")
    open(os.path.join(C, "0.orig/omega"), "w").write(o)
    n = open(os.path.join(v2, "0.orig/nut")).read().replace("    ground      { type nutkWallFunction; value uniform 0; }", "    ground      { type atmNutkWallFunction; z0 uniform 0.3; kappa 0.4; Cmu 0.09; value uniform 0; }")
    open(os.path.join(C, "0.orig/nut"), "w").write(n)
    for sn in ("s04", "s07"): shutil.copy(os.path.join(v2, "0.orig", sn), os.path.join(C, "0.orig", sn))
    shutil.copy(os.path.join(v2, "constant/transportProperties"), os.path.join(C, "constant/")); shutil.copy(os.path.join(v2, "constant/turbulenceProperties"), os.path.join(C, "constant/"))
    open(os.path.join(C, "system/setExprFieldsDict"), "w").write(f"""FoamFile {{ version 2.0; format ascii; class dictionary; object setExprFieldsDict; }}
expressions ( Uprofile {{ field U; dimensions [0 1 -1 0 0 0 0]; variables ( "ustar = {ustar:.6g}" "z0 = {z0}" "kappa = {kappa}" ); expression #{{ vector( ustar/kappa * log((pos().z() + z0)/z0), 0, 0 ) #}}; }} );
""")
    xs = -49.5; pts = [(xs + 5 * i, 0.0, 15.2) for i in range(1, 11)]
    open(os.path.join(C, "system/samplePoints"), "w").write("samplePoints\n{\n    type sets; libs (sampling); setFormat raw; interpolationScheme cellPoint; writeControl writeTime;\n    fields (U k s04 s07);\n    sets { receptors { type cloud; axis xyz; points (\n" + "".join(f"        ({x:.2f} {y} {z})\n" for x, y, z in pts) + "    ); } }\n}\n")
    c = open(os.path.join(v2, "system/controlDict")).read().replace("libs            (atmosphericModels);", "")
    c = c.replace("application     simpleFoam;", "libs            (atmosphericModels);\napplication     simpleFoam;")
    c = re.sub(r"probeLocations \(.*?\);", f"probeLocations ( ({xs+5:.1f} 0 15.2) ({xs+20:.1f} 0 15.2) ({xs+50:.1f} 0 15.2) ({xs:.1f} 0 {15+hs+2:.1f}) );", c, flags=re.S)
    c = c.replace("CofR (-0.125 0 0.0375)", "CofR (-25 0 7.5)").replace('    #include "plumeLines"\n', "")
    open(os.path.join(C, "system/controlDict"), "w").write(c)
    print(name, "built: hs", hs, "Ve", Ve, "tau", round(tau, 3))
