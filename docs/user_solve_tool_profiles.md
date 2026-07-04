# User Solve Tool Profiles

Tool profiles describe future tool availability. They are metadata, not adapters.

Profiles carry stable ids, categories, portable path sources, availability, capability flags, risk levels, and disabled or unavailable reasons. The default profile set is deterministic and can be overridden by explicit config records by `tool_id`.

Example config files use placeholders such as `USER_CONFIGURED_IDA_PATH`; they do not hardcode machine-specific paths or secrets.
