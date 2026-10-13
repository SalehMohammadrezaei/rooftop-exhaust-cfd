# Headless 3D renders

ParaView's batch renderer segfaults on this WSL machine, so the renders use PyVista with the
OSMesa (software OpenGL) build of VTK in a separate conda environment:

```bash
conda create -n viz python=3.12 pip
conda activate viz
pip install --extra-index-url https://wheels.vtk.org vtk-osmesa
pip install --no-deps pyvista
pip install numpy matplotlib pillow pooch scooby typing_extensions cmcrameri scipy
```

Scripts (run from this directory so `geometry.py` is importable):

| script | what it draws | input |
|---|---|---|
| `geometry.py` | shaded roof plant, one colour per element kind | `constant/triSurface/*.stl` |
| `mesh.py` | vertical mesh cut through a chiller row with cell edges | the case (reads `case.foam`) |
| `flow.py` | tracer isosurfaces (chiller air by height, flue plume) over the geometry | the case at one time |

Each writes one PNG at 2400 x 1500. Camera positions are fixed in the scripts so every condition
is drawn from the same viewpoint.
