#!/usr/bin/env python3
"""Write <case>/run_record.json from the case record and the logs (rule 11).

    run_record.py <case_dir> <t0_epoch> <t1_epoch>

wall_time_s is the time between the two epochs given (the driver measures them); when a case was
resumed the record keeps the earlier wall time and adds the resumed part under wall_time_resume_s.
"""
import json, os, re, sys

def _build():
    """OpenFOAM version and build from the sourced environment (rule 11)."""
    d = os.environ.get("WM_PROJECT_DIR", ""); v = os.environ.get("WM_PROJECT_VERSION", "unknown"); b = ""
    try: b = re.search(r"build=(\S+)", open(os.path.join(d, "META-INFO", "api-info")).read()).group(1)
    except Exception: pass
    return f"OpenFOAM-{v} {b}".strip()

C, t0, t1 = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
r = json.load(open(f"{C}/case_record.json"))
prev = f"{C}/run_record.json"
if os.path.exists(prev):
    r.update(json.load(open(prev)))
    r["wall_time_resume_s"] = r.get("wall_time_resume_s", 0) + (t1 - t0)
else:
    r["wall_time_s"] = t1 - t0
chk = open(f"{C}/log.checkMesh").read()
r.update({"cells": int(re.search(r"cells:\s+(\d+)", chk).group(1)), "mesh_ok": "Mesh OK" in chk,
          "flow_iterations": open(f"{C}/log.simpleFoam").read().count("\nTime = "),
          "scalar_iterations": open(f"{C}/log.simpleFoam_scalars").read().count("\nTime = "),
          "host": os.uname().nodename, "openfoam": _build()})
json.dump(r, open(prev, "w"), indent=1)
print("done", r["case"], r["cells"], "cells", r.get("wall_time_s"), "s")
