# Exact review records

`platform_v1.review_findings` implements the provider-free REVIEWAGENT-1 data
foundation of Issue #811. It adds no store, verifier, scanner, runtime endpoint,
Git invocation, model call, repair action or publication authority.

`normalize_review_target` binds repository/forge/change-request identity, exact
base/head commits and trees, patch digest, literal reviewed/excluded file paths,
review profile and an observation digest. SHA-1 and SHA-256 Git repositories are
supported; a target cannot mix their object-ID families. The digest is stable
under path ordering. These are supplied claims: a trusted collector must still
read the exact Git objects and validate their provenance. Canonicalization is
not evidence verification.

`normalize_review_finding` binds each rule/location to that target generation.
It rejects findings outside the effective file scope and malformed line ranges.
Summaries use the existing executor secret detector; a matching field is discarded
entirely as `[REDACTED]` to avoid retaining a partially redacted credential.
Evidence references are
digests, not raw logs, credentials or private reasoning. Redaction covers the
existing known patterns; callers must avoid supplying sensitive prose in the
first place.

`deduplicate_review_findings` combines only an explicit common rule/category and
location on the same exact target. The deterministic source is the representative
when both a scanner and a model supply that identity. All distinct contributions
and evidence references remain available. It does not infer semantic duplicates
from similar prose or claim that a source label authenticates scanner output.

`reconcile_review_findings` preserves prior records and marks them stale when any
target-generation field changes. A finding's disappearance is never proof that
the defect was fixed. A clean or empty report is never functional acceptance.

`record_review_feedback` retains explicit acknowledgement, not-reproducible or
dismissal with a reason, evidence digests, claimed adjudicator and timestamp.
It refuses a stale target. The original finding remains immutable. Historical
feedback can be retained, but `feedback_for_current_target` suppresses its current
projection after the target changes. Feedback is evaluation evidence; it does
not train a policy, authorize a repair or establish an independent audit.

Returned value objects expose `evidence_verified`, `independent_acceptance`,
`execution_authorized`, `repair_authorized` and `landing_authorized` as immutable
false flags. Record export includes these explicit limits. Raw input cannot
supply the flags to broaden authority.

The seeded tests are provider-free fixtures, including false-positive disposition
and stale-generation cases. They are not observations of a live reviewer or proof
of its detection/noise rate.

The following #811 work remains: trusted Git/analyzer collection; integration with
the existing TaskStore evidence path; review-only runtime/API orchestration;
context/instruction confinement; model review and real evaluation; forge advisory
projection; incremental impact analysis; and governed repair handoff. Human and
independent acceptance, required checks and landing remain separately controlled.
