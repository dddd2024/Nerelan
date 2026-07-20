# Framework authority matrix

One fact class has one primary owner. Adapters may cache or link facts, but cannot override the primary system.

| Fact class | Primary authority | Boundary |
|---|---|---|
| Product discovery and PRD | BMAD | Planning only; no command authority |
| Architecture and story definition | BMAD | Export trace links to engineering items |
| Engineering work item | GitHub | Issue/PR status follows repository work |
| Workflow runtime state | LangGraph | Single primary runtime |
| Checkpoint and resume | LangGraph | Reverse-agent may request a risk interrupt |
| Branch, commit, PR, review | GitHub | `project_state` is a read-only cache |
| CI and release truth | GitHub | Exact repository and head SHA required |
| High-risk authorization | Reverse-agent Trust Layer | R2/R3 actions require explicit approval |
| Command allowlist | Reverse-agent Trust Layer | Manual Decision remains compatibility input |
| Binary observation | Reverse-agent Trust Layer | Requires tool and artifact provenance |
| Claim and counterevidence | Reverse-agent Trust Layer | Frameworks reference, never assert |
| Validation status | Reverse-agent Trust Layer | Distinct from generic CI success |
| Audit history | Git history | Trust records and PRs provide indexed views |

MetaGPT and ChatDev are reference designs. Microsoft Agent Framework remains a possible future adapter alternative, not a second primary runtime.

The machine-readable authority is `project_state/gates/framework_authority_matrix.json`.
