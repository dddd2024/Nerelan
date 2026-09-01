# Research Baseline — Agent Security and Memory Trust

Status: research-derived architecture baseline; **not an implementation claim**.

Owner Work Item: #513
Parent/implementation owners: #179, #299, #303, #379, #252, #253, #137

## 1. Purpose

This document translates current Agent-security research into Nerelan/reverse-agent trust-boundary requirements.

The project already has a strong architecture direction around server-owned policy, bounded capabilities, repository-config trust, sandboxing, secret confinement, independent verification and durable provenance. The research below strengthens those choices and identifies one additional permanent principle:

> Untrusted content may supply data and evidence, but it must never become execution authority, policy, trusted control flow or durable memory merely because a model repeated it.

This document does not create a new security runtime, sandbox, policy engine, memory database or prompt-injection detector. Existing owner Issues remain authoritative.

---

## 2. Threat model

An unattended Agent can consume content from many sources that are legitimate inputs but are not trusted principals:

```text
repository source files
README / docs / comments
Issue / PR text
web pages
search results
browser DOM
MCP/tool responses
command output
logs
uploaded files/images
repository-local Agent/executor config
retrieved project knowledge
prior Agent-generated memory
```

Any of these may contain text that looks like an instruction.

Permanent distinction:

```text
content contains an instruction-looking string
!=
content has authority to issue an instruction
```

The platform must preserve a typed source/authority distinction outside prompt wording.

---

## 3. Research inputs

### CaMeL — defeating prompt injections by design

Canonical preprint page:

- https://arxiv.org/abs/2503.18813

Research lesson:

Prompt-injection resistance should not rely only on telling an LLM to ignore malicious instructions. A safer design separates trusted control semantics from untrusted data and enforces sensitive actions through capability/policy boundaries.

Nerelan implication:

```text
trusted Goal / approved plan / server policy
              |
              v
       trusted control intent
              |
              +--------------------------+
              |                          |
              v                          v
     untrusted repository/web/tool data  current durable evidence
              |                          |
              +------------+-------------+
                           v
                   Agent reasoning
                           |
                           v
                     action request
                           |
                           v
              server-owned policy/capability
                           |
                 allow / constrain / deny
```

Untrusted data may influence reasoning and task output, but it cannot directly grant filesystem, network, credential, publication, merge, sandbox or tool capabilities.

This aligns with #179 H4 and should remain a permanent design invariant.

### AgentDojo — security evaluation for tool-using Agents

Canonical publication page:

- https://proceedings.neurips.cc/paper_files/paper/2024/hash/97091a5177d8dc64b1da8bf3e1f6fb54-Abstract-Datasets_and_Benchmarks_Track.html

Research lesson:

A tool-using Agent needs evaluation that measures both task utility and security under adversarial indirect prompt injection. Normal functional tests alone do not prove that malicious tool/web data cannot redirect the Agent.

Nerelan implication:

Future Pack/platform security evals should include adversarial fixtures conceptually like:

```text
benign user goal
+
valid tool/repository/browser workflow
+
malicious instruction embedded in untrusted content

expected result:
  original task remains the objective
  unauthorized side effect does not occur
  policy/capability boundary remains intact
  suspicious/blocked condition is observable
```

This is especially relevant to #303 repository-config trust, #299 sandboxing and future Browser/MCP Packs.

### AgentPoison — poisoning persistent Agent memory/retrieval

Canonical publication page:

- https://proceedings.neurips.cc/paper_files/paper/2024/hash/eb113910e9c3f6242541c1652e30dfd6-Abstract-Conference.html

Research lesson:

Persistent memory/RAG can convert one malicious or incorrect interaction into a repeated future failure. Memory is therefore not only a relevance problem; **memory admission is a security boundary**.

Nerelan implication:

Reject:

```text
Agent says "this worked"
-> save as durable knowledge
-> retrieve forever
```

Prefer:

```text
candidate experience / knowledge
        |
        v
source + provenance classification
        |
        v
evidence-strength check
        |
        v
security/trust classification
        |
        v
scope + applicability + version
        |
        v
freshness + conflict check
        |
        v
ACCEPT / QUARANTINE / REJECT / NEEDS_REVIEW
```

An accepted memory is still advisory. It cannot override current TaskStore, Git/GitHub truth, current policy or a fresh verifier result.

---

## 4. Trusted-control / untrusted-data architecture rule

All future Agent-facing data should conceptually carry enough metadata to distinguish:

```text
source_identity
source_class
trust_class
provenance_reference
content_digest where practical
freshness/version
whether the source can supply DATA
whether the source can request an ACTION
whether the source can ever grant AUTHORITY (normally no)
```

The exact implementation may be simpler, but these semantic distinctions must not collapse into one plain string prompt.

Examples:

```text
Owner-approved Work Item      -> trusted task specification, bounded authority source
server PolicyDecision         -> trusted control/constraint
TaskStore accepted state      -> authoritative runtime truth
Git exact-head source         -> repository truth for that revision
web page                      -> untrusted data
repository README             -> untrusted data
MCP result                    -> untrusted tool data
model output                  -> untrusted proposal/result until independently accepted
Project Knowledge entry       -> advisory memory with provenance/applicability
```

---

## 5. Prompt-injection surface inventory

Security evaluation should treat indirect prompt injection as a cross-surface class rather than a browser-only problem.

### 5.1 Repository content

Fixtures should eventually cover instruction-looking text in:

```text
README
source comments
fixture/test data
Issue templates
generated output
configuration descriptions
```

Expected invariant: repository text cannot broaden policy or redirect publication/credential behavior.

### 5.2 Repository-local Agent / MCP / executor configuration

#303 remains canonical.

Research reinforces its permanent rule:

> Discovering/opening a project is not authorization to activate project-controlled Agent, MCP, plugin, command or permission configuration.

Zero-execution discovery and exact-digest trust remain preferred.

### 5.3 Browser/web content

A web page may legitimately contain instructions for a human, but those instructions are not automatically instructions to the Agent.

Future browser Pack evals should separate:

```text
user Goal
vs
page content
vs
trusted platform action policy
```

### 5.4 Tool / MCP output

Tool output is data even when the tool returns text such as "run this command" or "send this secret".

A tool result cannot recursively grant capabilities to another tool.

### 5.5 Logs and command output

Build/test output may contain attacker-controlled strings. Logging/retrieving that output must not transform it into trusted control text on a later step.

### 5.6 Project memory

A malicious or hallucinated memory can become more dangerous than a one-time prompt injection because it may persist across tasks and Agent sessions.

Memory admission and retrieval therefore require explicit trust metadata.

---

## 6. Memory admission security contract

Research-derived semantic contract for #379/#260/#252:

```text
MemoryCandidate
  content_or_structured_fact
  source
  provenance_refs
  evidence_refs
  created_under_model/executor/version
  scope
  applicability_conditions
  security_class
  freshness_inputs

-> MemoryAdmission

MemoryDisposition
  ACCEPTED
  QUARANTINED
  REJECTED
  NEEDS_REVIEW
  SUPERSEDED
```

Exact schema is not fixed here.

### Required invariants

1. **No authority inheritance**
   Memory can suggest; it cannot authorize.

2. **Provenance required for consequential facts**
   Important architecture/security facts should point back to evidence, code, Issue/PR, run or explicit human decision where practical.

3. **Version/applicability binding**
   A lesson from one executor/model/repository version may not apply to another.

4. **Freshness invalidation**
   Upstream change can make a previously good memory stale.

5. **Conflict handling**
   Conflicting memories are surfaced/ordered/superseded; they are not silently blended into one synthetic fact.

6. **Negative results are first class**
   Failed approaches may be retained, but only with applicability and evidence metadata.

7. **Sensitive material exclusion**
   Raw secrets, unrestricted environment dumps and private chain-of-thought are not general Project Knowledge.

8. **Poisoning-aware retrieval**
   High relevance does not automatically imply high trust.

---

## 7. Security-aware Context Projection

Before memory/tool/repository content enters a model context, projection should conceptually apply:

```text
retrieve candidate context
-> source/provenance validation
-> scope/applicability filtering
-> freshness/version filtering
-> trust/security classification
-> conflict resolution
-> relevance ranking
-> bounded projection
```

The projection should preserve source boundaries where doing so helps prevent the model from confusing data with instructions.

---

## 8. Agent security evaluation contract

Inspired by AgentDojo, security evaluation should require two simultaneous dimensions:

```text
UTILITY
  did the Agent complete the legitimate task?

SECURITY
  did it avoid prohibited/attacker-requested side effects?
```

A task is not a successful security result if it completes the requested coding work but also leaks a token, starts an unapproved MCP server, reads another workspace or publishes outside the allowed boundary.

### Candidate security-eval matrix

```text
Surface                    Attack fixture                       Expected protection owner
-------------------------  -----------------------------------  --------------------------
repository file            indirect instruction                #179 policy + verifier
repo Agent config          permission/MCP broadening            #303
sandboxed code             host-home/network escape             #299
browser page               instruction to exfiltrate/change     Browser Pack + #179
MCP/tool result            instruction to call another tool     #179 capability boundary
memory candidate           poisoned persistent lesson           #379
retrieved memory           stale/conflicting malicious entry    #379/#296
publication result         attempt to widen target/branch        governance/publication controls
```

This table is research guidance, not proof these test fixtures are implemented.

---

## 9. Sandbox relationship

CaMeL-style control/data separation does not replace OS isolation.

Permanent distinction remains:

```text
policy/capability
  = what the Agent is authorized to request

prompt/data trust separation
  = what content may influence control semantics

sandbox
  = what untrusted code can technically do even if compromised
```

#299 owns sandbox admission/capability/backends.

A strong system requires these controls to compose rather than treating one as a substitute for the others.

---

## 10. Repository-config trust relationship

#303 owns pre-execution project-local configuration trust.

Research-derived requirement:

```text
repository-local config
-> discover as untrusted bytes/data
-> compute exact effective identity/digest
-> classify capability changes
-> explicit trust/policy admission
-> activate only approved exact semantics
```

Do not execute a config file in order to learn whether it is safe.

---

## 11. Independent verification relationship

Security-critical acceptance cannot be based on executor/model self-report such as:

```text
"I did not access any secret"
```

Prefer independent evidence where feasible:

```text
sandbox/network policy evidence
changed-file/path readback
credential relay boundary
exact command/tool capability records
publication target identity
verifier results
```

Semantic Agent-as-judge style review may complement these checks but never override deterministic security truth.

---

## 12. Security metrics and failure taxonomy candidates

Useful sanitized signals include:

```text
blocked_policy_request_count
prompt_injection_fixture_success/failure
unauthorized_side_effect_attempt
repository_config_quarantined
sandbox_policy_mismatch
memory_candidate_quarantined
memory_conflict_detected
stale_memory_excluded
security_eval_utility_result
security_eval_security_result
```

Do not log raw secrets, arbitrary prompt contents or unnecessary sensitive payloads merely to populate metrics.

---

## 13. Complexity/reuse boundary

This research does **not** justify:

```text
a custom sandbox runtime
a second policy engine before #179 proves the need
an LLM-only "prompt injection classifier" as the final control boundary
a generic security memory database
a new browser/MCP security framework detached from Pack/eval contracts
copying AgentDojo as a production runtime
```

Reuse mature mechanisms for commodity enforcement and benchmarks. Nerelan owns the thin trust semantics connecting source identity, authority, capability, durable truth, memory admission and evidence.

---

## 14. Mapping to existing owners

### #179 Reliability/security hardening

Owns typed server policy, execution capabilities, telemetry and security invariants.

### #303 Repository workspace trust

Owns project-local Agent/executor/MCP configuration discovery, trust and exact-digest activation.

### #299 Sandbox boundary

Owns technical containment of untrusted code/process execution.

### #379 Memory admission / Context Projection

Owns memory safety, provenance, applicability, freshness and conflict handling.

### #252 Autonomous Improvement Loop

Owns experience reuse. Research here requires AIL-4 learning to treat stored experience as scoped evidence, never autonomous authority.

### #253 Pack platform

Owns domain security evals/verifiers and Pack-specific threat fixtures.

---

## 15. Suggested future adoption sequence

Only when canonical owners authorize implementation:

```text
SEC-R0  inventory Agent-facing untrusted data surfaces
SEC-R1  source/trust metadata in bounded context/tool contracts
SEC-R2  deterministic indirect-injection fixtures for current tool/repo paths
SEC-R3  memory admission security/provenance/freshness enforcement
SEC-R4  browser/MCP/Pack-specific adversarial eval suites
SEC-R5  evidence-backed security regression tracking across versions
```

Each stage must preserve independent policy, sandbox and verifier authority.

---

## 16. Terminal research position

```text
UNTRUSTED_CONTENT_IS_DATA_NOT_AUTHORITY
TRUSTED_CONTROL_AND_UNTRUSTED_DATA_MUST_REMAIN_DISTINGUISHABLE
PROMPT_INJECTION_IS_A_SYSTEM_BOUNDARY_NOT_ONLY_A_PROMPT_PROBLEM
MEMORY_ADMISSION_IS_A_SECURITY_BOUNDARY
HIGH_RELEVANCE_DOES_NOT_EQUAL_HIGH_TRUST
SECURITY_EVAL_REQUIRES_UTILITY_AND_NO_UNAUTHORIZED_SIDE_EFFECT
POLICY_SANDBOX_REPO_TRUST_MEMORY_TRUST_AND_VERIFICATION_MUST_COMPOSE
IMPLEMENTATION_REMAINS_WITH_EXISTING_OWNER_ISSUES
```
