# OpenFOAM v2606 (OpenCFD build 2606.0, unpacked into a user prefix; no root).
# Usage:  source ~/opt/openfoam2606.sh
# The binaries link the SYSTEM OpenMPI 4.1.6 (/usr/bin/mpirun). The user OpenMPI 5.0.6 in
# ~/opt/openmpi is NOT compatible with them and is pushed behind the system one here.
export LD_LIBRARY_PATH=/home/impres/opt/openfoam2606-root/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}
export FOAM_MPI=sys-openmpi
export PATH=/usr/bin:$PATH
source /home/impres/opt/openfoam2606-root/usr/lib/openfoam/openfoam2606/etc/bashrc
source /home/impres/opt/openfoam2606-root/usr/lib/openfoam/openfoam2606/etc/config.sh/aliases   # foamVersion, foamTutorials, etc.
export OF2606_MPIRUN=/usr/bin/mpirun
