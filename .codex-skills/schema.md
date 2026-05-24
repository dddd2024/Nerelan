# Codex Skill Registry Schema

This schema governs repo-tracked Codex skills under `.codex-skills/`.
Skills are durable workflow and guardrail sources. Dynamic facts such as
current candidates, run names, artifact paths, freshness, bottlenecks, and
runtime metrics belong in `project_state/`.

## Directory Layout

Each active or deprecated skill lives at:

```text
.codex-skills/<skill-name>/SKILL.md
```

The directory name, frontmatter `name`, and registry key must match unless a
future registry explicitly defines aliases.

## Required Frontmatter

Every repo-tracked active skill must start with frontmatter bounded by `---`.
Minimum required fields:

```yaml
name: reverse-agent-iteration
description: Durable skill description.
version: 2
status: active
scope: generic_workflow
owner: project_state
last_reviewed: "2026-05-24"
```

Allowed `status` values:

```text
active
deprecated
archived
```

Allowed `scope` values:

```text
generic_workflow
engineering_branch
reverse_solving
sample_profile
tool_usage
```

Unknown frontmatter fields are allowed so long as the required fields remain
present and registry consistency checks pass.

## Facts Policy

Active workflow and sample profile skills should set `owner: project_state`.
They must not store dynamic facts. Dynamic facts include:

```text
current candidate hex
current best baseline
current run name
direct current artifact path
artifact freshness
current bottleneck
runtime metric values
```

Stable guardrails are allowed. For example, a sample profile may state that
current candidates must be read from `project_state/current_state.json`, or
that stale artifacts must not be promoted to current evidence.

## Forbidden Defaults

Active skills must not instruct Codex to do these by default:

```text
read PROJECT_PROGRESS_LOG.txt
scan full solve_reports/
inspect newest solve_reports/harness_runs/*
run runtime probes
run sample-specific breakpoint probes
```

Negative guardrails are allowed and encouraged. For example, `Do not scan full
solve_reports/ by default` is compliant.

## Registry

`.codex-skills/registry.json` must contain:

```json
{
  "schema_version": 1,
  "skills": {
    "skill-name": {
      "path": ".codex-skills/skill-name/SKILL.md",
      "status": "active",
      "scope": "generic_workflow",
      "version": 2
    }
  }
}
```

The registry must only list repo paths that exist. For each skill entry,
`status`, `scope`, and `version` must match the skill frontmatter.

## Decision Skill Profiles

`project_state/decision_packet.md` may include an additive
`decision_meta.skill_profiles` field. This field records the durable skill
profiles the decision expects Codex to apply for the round.

Formal profile strings use:

```text
skill-name@vN
```

For example:

```json
{
  "mainline": "engineering_branch",
  "skill_profiles": ["reverse-agent-iteration@v2"]
}
```

The transitional form `skill-name@vN-draft` may be parsed during migrations,
but approved decisions should emit a lint warning when they use it.

`lint-decision` validates declared profiles against
`.codex-skills/registry.json`:

```text
unknown skill: error
inactive/deprecated/archived skill: error
version mismatch: error
bad profile format: error
missing registry for a declared profile: error
```

Legacy decision packets without `skill_profiles` remain compatible and should
warn instead of failing. For `engineering_branch` and `reverse_solving`
approved decisions, lint should also warn when no active `generic_workflow`
skill is declared.

## Audit Requirements

The skill audit must use Python standard library only and must:

```text
check registry presence and shape
check registered SKILL.md paths exist
check required frontmatter
check registry/frontmatter consistency
check forbidden defaults in active skills
check sample_profile dynamic facts
emit JSON with status, skills_checked, errors, warnings
exit non-zero on hard errors
```

Heuristic content checks should prefer warnings over false hard failures when
language is ambiguous. Obvious dynamic facts and direct artifact paths in
active sample profile skills are hard errors.
