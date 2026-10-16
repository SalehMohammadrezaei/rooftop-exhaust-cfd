# 0016 Run housekeeping: written times and free disk (approved 2026-10-16)

Two numerical settings, taken after the home disk filled twice during unattended runs
(notebook F2 and F8).

- `purgeWrite 2` in the applied controlDict: only the last two written times are kept, so a
  case holds at most two field sets per processor instead of ten. A restart needs one written
  time; nothing in the post-processing reads an intermediate one.
- The run driver refuses to start a case with less than 20 GB free on the case's file system
  and says so in its log. A 2.6 million cell case on 32 processors writes about 6 GB with the
  purge in place; the 6.7 million cell grid-study case on 64 wrote 16 GB without it.

Neither changes a result: the fields written at the end are the same, and the matrix is
computed from the monitor histories and the final time.
