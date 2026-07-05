# Deletion Manifest And Tombstone

`project_state/gates/deletion_manifest_schema.json` and `project_state/gates/tombstone_schema.json` are schema-only artifacts. They do not identify real files for deletion and they do not write tombstones for actual deletion.

A future deletion manifest must include a future decision ID, future round ID, original path, original hash, reason, retention class, audit approval, and tombstone target.

A future tombstone must include the original path, deleted hash, deletion manifest ID, deletion round, deletion timestamp, reason, restore notes, and audit notes.

No current artifact may be deleted, moved, archived, compacted, or tombstoned in State Governance Bundle Big Step v1. Cleanup-apply remains deferred until a separate decision accepts these schemas and the deletion safety gates.
