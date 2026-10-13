#!/bin/bash
# Run a list of generated applied cases, up to $MAXJOBS at a time (each uses its own core count).
#   queue_applied.sh <maxjobs> <case_dir> [<case_dir> ...]
trap "" HUP; MAXJOBS=$1; shift; REPO=$(cd "$(dirname "$0")/.." && pwd)
for C in "$@"; do
  while [ "$(jobs -rp | wc -l)" -ge "$MAXJOBS" ]; do sleep 60; done
  ( bash "$REPO/workflow/run_applied.sh" "$C" > "$C/log.run_applied" 2>&1 || echo "FAILED $C" ) &
  echo "launched $(basename "$C") at $(date +%H:%M) load $(cut -d' ' -f1 /proc/loadavg)"; sleep 20
done
wait; echo "QUEUE DONE $(date +%H:%M)"
