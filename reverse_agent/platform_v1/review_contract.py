"""Bounded model-review output contract; no provider or publication authority.

Execution evidence should bind task_id, contract_digest, artifact_commit,
artifact_tree, reviewer_binding, response_digest, verdict and failure_classification.
Malformed output and rejection are agent failures; identity/transport failures are not.
"""
import json
import re

MAX_RESPONSE_BYTES = 65536
MAX_FINDINGS = 100
MAX_FILE = 512
MAX_SUMMARY = 2000
INVALID_RESPONSE = "model_review_invalid_response"
OVERSIZED_RESPONSE = "model_review_response_too_large"
REJECTED = "model_review_rejected"
IDENTITY_FAILURE = "model_review_contract_identity_invalid"
EVIDENCE_FIELDS = ("task_id", "contract_digest", "artifact_commit", "artifact_tree",
                   "reviewer_binding", "response_digest", "verdict", "failure_classification")


class ReviewContractError(ValueError):
    def __init__(self, classification=INVALID_RESPONSE):
        self.failure_classification = classification
        super().__init__(classification)


def verdict_schema():
    """Return a fresh strict JSON schema suitable for structured model output."""
    return {"type": "object", "additionalProperties": False,
            "required": ["verdict", "findings"], "properties": {
                "verdict": {"type": "string", "enum": ["ACCEPT", "REJECT"]},
                "findings": {"type": "array", "maxItems": MAX_FINDINGS, "items": {
                    "type": "object", "additionalProperties": False,
                    "required": ["file", "line", "severity", "summary"], "properties": {
                        "file": {"type": "string", "minLength": 1, "maxLength": MAX_FILE},
                        "line": {"type": "integer", "minimum": 1, "maximum": 2147483647},
                        "severity": {"type": "string", "enum": ["blocking", "non_blocking"]},
                        "summary": {"type": "string", "minLength": 1, "maxLength": MAX_SUMMARY}}}}}}


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReviewContractError()
        result[key] = value
    return result


def validate_verdict(value):
    """Validate JSON text or a decoded object, returning a detached JSON object."""
    try:
        text = value if isinstance(value, str) else json.dumps(value, allow_nan=False)
        if len(text.encode("utf-8")) > MAX_RESPONSE_BYTES:
            raise ReviewContractError(OVERSIZED_RESPONSE)
        obj = json.loads(text, object_pairs_hook=_pairs)
        if type(obj) is not dict or set(obj) != {"verdict", "findings"}:
            raise ReviewContractError()
        if obj["verdict"] not in ("ACCEPT", "REJECT") or type(obj["findings"]) is not list or len(obj["findings"]) > MAX_FINDINGS:
            raise ReviewContractError()
        for finding in obj["findings"]:
            if type(finding) is not dict or set(finding) != {"file", "line", "severity", "summary"}:
                raise ReviewContractError()
            path = finding["file"]
            if (not isinstance(path, str) or not 1 <= len(path) <= MAX_FILE
                    or path.startswith("/") or "\\" in path or ":" in path
                    or any(part in ("", ".", "..") for part in path.split("/"))
                    or re.search(r"[\x00-\x1f\x7f]", path)
                    or type(finding["line"]) is not int or not 1 <= finding["line"] <= 2147483647
                    or finding["severity"] not in ("blocking", "non_blocking")
                    or not isinstance(finding["summary"], str)
                    or not 1 <= len(finding["summary"]) <= MAX_SUMMARY or not finding["summary"].strip()):
                raise ReviewContractError()
        if obj["verdict"] == "ACCEPT" and any(f["severity"] == "blocking" for f in obj["findings"]):
            raise ReviewContractError()
        return obj
    except ReviewContractError:
        raise
    except (ValueError, TypeError, OverflowError, RecursionError, UnicodeError) as exc:
        raise ReviewContractError() from exc
