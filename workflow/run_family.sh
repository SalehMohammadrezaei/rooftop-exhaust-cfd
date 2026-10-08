#!/bin/bash
# Run every generated case of a family sequentially (serial each).  run_family.sh <cases_root>/<family>
root="$1"; here="$(cd "$(dirname "$0")" && pwd)"
for c in "$root"/*/; do
    [ -f "$c/0.orig/U" ] || continue
    bash "$here/run_case.sh" "$c" || echo "FAILED: $c"
done
