# Archive Index

`project_state/gates/archive_index.json` is a bounded index of known governance and historical hygiene evidence. It is not archive compaction and it does not move files.

The index is limited to named sources:

- current round output paths
- the previous accepted round manifest
- known historical state hygiene decision packets
- current state manifest artifact roles
- current report summary artifact roles

It must not recursively scan all round archives, scan full `solve_reports/`, or treat historical sample gaps as current-round blockers. Entries are classified as current, accepted-round minimum evidence, historical nonblocking evidence, or future archive candidates.

Future archive compaction needs a separate approved decision and a gate that proves the move is safe.
