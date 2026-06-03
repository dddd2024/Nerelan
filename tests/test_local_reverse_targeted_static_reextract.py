"""Tests for reverse_agent.local_reverse_targeted_static_reextract."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from reverse_agent.local_reverse_targeted_static_reextract import (
    _extract_cpp2_sub_401005,
    _extract_input_range_check,
    _extract_length_constraints,
    _extract_post_increment_logic,
    _extract_scanf_context,
    _extract_sha256_input_domain,
    _extract_sub_401005_evidence,
    _find_decompiler_snippet,
    run_targeted_reextraction,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_SHA256_MAIN_PSEUDO = textwrap.dedent("""\
    int __cdecl main_0(int argc, const char **argv, const char **envp)
    {
      int v4; // eax
      int i; // [esp+70h] [ebp-450h]
      char Destination; // [esp+74h] [ebp-44Ch] BYREF
      int v7; // [esp+75h] [ebp-44Bh]
      char Source[1021]; // [esp+7Ch] [ebp-444h] BYREF
      __int16 v9; // [esp+479h] [ebp-47h]
      char v10; // [esp+47Bh] [ebp-45h]
      char Str1[68]; // [esp+47Ch] [ebp-44h] BYREF
      memset(Str1, 0, 65);
      memset(Source, 0, sizeof(Source));
      v9 = 0;
      v10 = 0;
      Destination = 0;
      v7 = 0;
      printf("Please input your flag:\\n");
      scanf("%s", Source);
      if ( strlen(Source) >= 5 )
      {
        strncpy(&Destination, Source, 4u);
        v4 = strlen(&Destination);
        sub_401005(Str1, (int)&Destination, v4);
        for ( i = 0; i < 64; ++i )
        {
          if ( ++Str1[i] == 103 )
            Str1[i] = 97;
          if ( Str1[i] == 58 )
            Str1[i] = 48;
        }
        if ( !strncmp(Str1, "493f877692ea8d507fa98355a054efede85e7c7", 0x40u) )
          printf("Well done!");
        else
          printf("Wrong!");
        system("pause");
        return 0;
      }
      else
      {
        printf("Wrong,try again!\\n");
        system("pause");
        return 0;
      }
    }
""")

_CPP2_MAIN_PSEUDO = textwrap.dedent("""\
    int __cdecl main_0(int argc, const char **argv, const char **envp)
    {
      int v4; // eax
      size_t v5; // [esp+4Ch] [ebp-454h]
      size_t i; // [esp+50h] [ebp-450h]
      int j; // [esp+50h] [ebp-450h]
      char Destination; // [esp+54h] [ebp-44Ch] BYREF
      int v9; // [esp+55h] [ebp-44Bh]
      char Source[1021]; // [esp+5Ch] [ebp-444h] BYREF
      __int16 v11; // [esp+459h] [ebp-47h]
      char v12; // [esp+45Bh] [ebp-45h]
      char Str1[68]; // [esp+45Ch] [ebp-44h] BYREF
      memset(Str1, 0, 65);
      memset(Source, 0, sizeof(Source));
      v11 = 0;
      v12 = 0;
      Destination = 0;
      v9 = 0;
      printf("Please input your flag:\\n");
      scanf("%s", Source);
      v5 = strlen(Source);
      if ( v5 >= 5 )
      {
        for ( i = 0; i < v5; ++i )
        {
          if ( Source[i] < 65 || Source[i] > 122 )
          {
            printf("The inputs are out of the scope!");
            system("pause");
          }
        }
        strncpy(&Destination, Source, 4u);
        v4 = strlen(&Destination);
        sub_401005(Str1, (int)&Destination, v4);
        for ( j = 0; j < 64; ++j )
          ++Str1[j];
        if ( !strncmp(Str1, "1f2e28649c4g:25:8bb:24c3D3EGF6GFg22dff:", 0x40u) )
          printf("Correct!\\n");
        else
          printf("Wrong,try again!\\n");
        system("pause");
        return 0;
      }
      else
      {
        printf("Wrong,try again!\\n");
        system("pause");
        return 0;
      }
    }
""")


def _make_raw_evidence(main_pseudo: str, has_sub_401005: bool = False) -> dict:
    snippets = [
        {"function": "_main_0", "entry_ea": "0x401CA0", "text": main_pseudo},
    ]
    if has_sub_401005:
        snippets.append({
            "function": "sub_401005",
            "entry_ea": "0x401005",
            "text": "void sub_401005(char *out, int in, int len) { /* hash */ }",
        })
    return {
        "decompiler_snippets": snippets,
        "functions": ["_main_0", "sub_401005", "sub_401B20"],
        "strings_summary": ["Please input your flag:\\n"],
        "compare_contexts_summary": [],
        "local_check_contexts_summary": [],
        "string_xrefs_summary": [],
        "validation_function_candidates": [],
    }


def _make_handoff() -> dict:
    return {
        "schema_version": 1,
        "status": "PARTIAL",
        "validated_candidates": [
            {
                "sample_id": "bcbd9979db015bfd",
                "candidate": "hookapi",
                "validation_status": "validated",
            }
        ],
        "unresolved_targets": [
            {
                "sample_id": "18019fca52b389fe",
                "relative_path": "逆向课程2024春01/sha_256.exe",
                "blocked_reason": "NO_BOUNDED_HASH_PREIMAGE_DOMAIN",
                "constraint_status": "blocked",
            },
            {
                "sample_id": "4c69f173f2bd0211",
                "relative_path": "逆向课程2022春02/CPP2.exe",
                "blocked_reason": "MISSING_UPSTREAM_TRANSFORM_FUNCTION:sub_401005",
                "constraint_status": "blocked",
            },
        ],
    }


def _make_artifact_index(tmp_path: Path, sha256_evidence: Path, cpp2_evidence: Path) -> dict:
    return {
        "latest_artifacts_v2": {
            "local_reverse_ida_evidence_18019fca52b389fe": {
                "kind": "local_reverse_ida_evidence_18019fca52b389fe",
                "path": str(sha256_evidence),
                "freshness": "current",
                "sample_id": "18019fca52b389fe",
            },
            "local_reverse_ida_evidence_4c69f173f2bd0211": {
                "kind": "local_reverse_ida_evidence_4c69f173f2bd0211",
                "path": str(cpp2_evidence),
                "freshness": "current",
                "sample_id": "4c69f173f2bd0211",
            },
        }
    }


def _make_ida_summary() -> dict:
    return {"schema_version": 1, "target_count": 3, "status": "SUCCESS"}


# ---------------------------------------------------------------------------
# Unit tests
# ---------------------------------------------------------------------------

class TestFindDecompilerSnippet:
    def test_found(self):
        snippets = [{"function": "_main_0", "text": "hello"}]
        assert _find_decompiler_snippet(snippets, "_main_0") == "hello"

    def test_not_found(self):
        assert _find_decompiler_snippet([], "sub_401005") is None


class TestExtractScanfContext:
    def test_scanf_with_source_buffer(self):
        ctx = _extract_scanf_context(_SHA256_MAIN_PSEUDO)
        assert ctx["input_api"] == "scanf"
        assert ctx["format_string"] == "%s"
        assert "1021" in ctx["buffer_size_hint"]

    def test_no_scanf(self):
        ctx = _extract_scanf_context("int main() { return 0; }")
        assert ctx["input_api"] == "unknown"


class TestExtractLengthConstraints:
    def test_sha256_length(self):
        ctx = _extract_length_constraints(_SHA256_MAIN_PSEUDO)
        assert ctx["min_length"] == 5
        assert ctx["prefix_copy_length"] == 4
        assert ctx["max_length"] is None

    def test_cpp2_length(self):
        ctx = _extract_length_constraints(_CPP2_MAIN_PSEUDO)
        assert ctx["min_length"] == 5
        assert ctx["prefix_copy_length"] == 4


class TestExtractPostIncrementLogic:
    def test_sha256_dual_wrap(self):
        logic = _extract_post_increment_logic(_SHA256_MAIN_PSEUDO, "18019fca52b389fe")
        assert logic["increment_type"] == "increment_with_dual_wrap"
        assert len(logic["wrap_rules"]) == 2

    def test_cpp2_simple(self):
        logic = _extract_post_increment_logic(_CPP2_MAIN_PSEUDO, "4c69f173f2bd0211")
        assert logic["increment_type"] == "simple_increment"
        assert logic["wrap_rules"] == []


class TestExtractInputRangeCheck:
    def test_cpp2_has_range(self):
        check = _extract_input_range_check(_CPP2_MAIN_PSEUDO)
        assert check["has_range_check"] is True
        assert check["min_char"] == 65
        assert check["max_char"] == 122

    def test_sha256_no_range(self):
        check = _extract_input_range_check(_SHA256_MAIN_PSEUDO)
        assert check["has_range_check"] is False


class TestExtractSub401005Evidence:
    def test_missing_pseudocode(self):
        raw = _make_raw_evidence(_SHA256_MAIN_PSEUDO, has_sub_401005=False)
        evidence = _extract_sub_401005_evidence(raw, "18019fca52b389fe")
        assert evidence["pseudocode_available"] is False
        assert len(evidence["missing_evidence"]) > 0
        assert "collect_evidence.py" in evidence["missing_evidence"][1]

    def test_with_pseudocode(self):
        raw = _make_raw_evidence(_SHA256_MAIN_PSEUDO, has_sub_401005=True)
        evidence = _extract_sub_401005_evidence(raw, "18019fca52b389fe")
        assert evidence["pseudocode_available"] is True


class TestExtractSha256InputDomain:
    def test_no_bounded_domain(self):
        raw = _make_raw_evidence(_SHA256_MAIN_PSEUDO)
        domain = _extract_sha256_input_domain(raw, _SHA256_MAIN_PSEUDO)
        assert domain["status"] == "not_found"
        assert "NO_BOUNDED_HASH_PREIMAGE_DOMAIN" in " ".join(domain["notes"])


class TestExtractCpp2Sub401005:
    def test_cpp2_evidence(self):
        raw = _make_raw_evidence(_CPP2_MAIN_PSEUDO)
        evidence = _extract_cpp2_sub_401005(raw, _CPP2_MAIN_PSEUDO)
        assert evidence["pseudocode_available"] is False
        assert "input_range_check" in evidence
        assert evidence["input_range_check"]["has_range_check"] is True


# ---------------------------------------------------------------------------
# Integration tests
# ---------------------------------------------------------------------------

class TestRunTargetedReextraction:
    def test_only_sha256_and_cpp2_selected(self, tmp_path: Path):
        """Only sha_256 and CPP2 are selected, not Cpp1."""
        sha256_ev = tmp_path / "sha256_ev.json"
        cpp2_ev = tmp_path / "cpp2_ev.json"
        handoff_path = tmp_path / "handoff.json"
        ai_path = tmp_path / "artifact_index.json"
        ida_path = tmp_path / "ida_summary.json"
        out_path = tmp_path / "out.json"

        sha256_ev.write_text(json.dumps(_make_raw_evidence(_SHA256_MAIN_PSEUDO)))
        cpp2_ev.write_text(json.dumps(_make_raw_evidence(_CPP2_MAIN_PSEUDO)))
        handoff_path.write_text(json.dumps(_make_handoff()))
        ai_path.write_text(json.dumps(_make_artifact_index(tmp_path, sha256_ev, cpp2_ev)))
        ida_path.write_text(json.dumps(_make_ida_summary()))

        result = run_targeted_reextraction(ai_path, ida_path, handoff_path, out_path)

        assert result["target_count"] == 2
        assert len(result["targets"]) == 2
        ids = {t["sample_id"] for t in result["targets"]}
        assert ids == {"18019fca52b389fe", "4c69f173f2bd0211"}

    def test_stale_evidence_blocked(self, tmp_path: Path):
        """Stale/missing evidence -> blocked."""
        handoff_path = tmp_path / "handoff.json"
        ai_path = tmp_path / "artifact_index.json"
        ida_path = tmp_path / "ida_summary.json"
        out_path = tmp_path / "out.json"

        handoff_path.write_text(json.dumps(_make_handoff()))
        ai_path.write_text(json.dumps({
            "latest_artifacts_v2": {
                "local_reverse_ida_evidence_18019fca52b389fe": {
                    "freshness": "stale",
                    "path": None,
                },
                "local_reverse_ida_evidence_4c69f173f2bd0211": {
                    "freshness": "current",
                    "path": str(tmp_path / "cpp2_ev.json"),
                },
            }
        }))
        ida_path.write_text(json.dumps(_make_ida_summary()))
        (tmp_path / "cpp2_ev.json").write_text(
            json.dumps(_make_raw_evidence(_CPP2_MAIN_PSEUDO))
        )

        result = run_targeted_reextraction(ai_path, ida_path, handoff_path, out_path)

        sha_target = next(t for t in result["targets"] if t["sample_id"] == "18019fca52b389fe")
        assert sha_target["extraction_status"] == "blocked"

    def test_sha256_no_bounded_domain_no_candidate(self, tmp_path: Path):
        """sha_256 without bounded domain must not generate preimage candidate."""
        sha256_ev = tmp_path / "sha256_ev.json"
        cpp2_ev = tmp_path / "cpp2_ev.json"
        handoff_path = tmp_path / "handoff.json"
        ai_path = tmp_path / "artifact_index.json"
        ida_path = tmp_path / "ida_summary.json"
        out_path = tmp_path / "out.json"

        sha256_ev.write_text(json.dumps(_make_raw_evidence(_SHA256_MAIN_PSEUDO)))
        cpp2_ev.write_text(json.dumps(_make_raw_evidence(_CPP2_MAIN_PSEUDO)))
        handoff_path.write_text(json.dumps(_make_handoff()))
        ai_path.write_text(json.dumps(_make_artifact_index(tmp_path, sha256_ev, cpp2_ev)))
        ida_path.write_text(json.dumps(_make_ida_summary()))

        result = run_targeted_reextraction(ai_path, ida_path, handoff_path, out_path)

        sha_target = next(t for t in result["targets"] if t["sample_id"] == "18019fca52b389fe")
        assert sha_target["bounded_input_domain"]["status"] == "not_found"
        assert sha_target["bounded_input_domain"]["candidate_source"] == ""
        assert sha_target["blocker_resolved"] is False

    def test_cpp2_sub_401005_blocker_documented(self, tmp_path: Path):
        """CPP2 target must include sub_401005_evidence or exact missing evidence."""
        sha256_ev = tmp_path / "sha256_ev.json"
        cpp2_ev = tmp_path / "cpp2_ev.json"
        handoff_path = tmp_path / "handoff.json"
        ai_path = tmp_path / "artifact_index.json"
        ida_path = tmp_path / "ida_summary.json"
        out_path = tmp_path / "out.json"

        sha256_ev.write_text(json.dumps(_make_raw_evidence(_SHA256_MAIN_PSEUDO)))
        cpp2_ev.write_text(json.dumps(_make_raw_evidence(_CPP2_MAIN_PSEUDO)))
        handoff_path.write_text(json.dumps(_make_handoff()))
        ai_path.write_text(json.dumps(_make_artifact_index(tmp_path, sha256_ev, cpp2_ev)))
        ida_path.write_text(json.dumps(_make_ida_summary()))

        result = run_targeted_reextraction(ai_path, ida_path, handoff_path, out_path)

        cpp2_target = next(t for t in result["targets"] if t["sample_id"] == "4c69f173f2bd0211")
        assert "sub_401005_evidence" in cpp2_target
        assert cpp2_target["sub_401005_evidence"]["pseudocode_available"] is False
        assert len(cpp2_target["sub_401005_evidence"]["missing_evidence"]) > 0
        assert cpp2_target["blocker_resolved"] is False

    def test_output_target_count_2(self, tmp_path: Path):
        """Output target_count must be 2."""
        sha256_ev = tmp_path / "sha256_ev.json"
        cpp2_ev = tmp_path / "cpp2_ev.json"
        handoff_path = tmp_path / "handoff.json"
        ai_path = tmp_path / "artifact_index.json"
        ida_path = tmp_path / "ida_summary.json"
        out_path = tmp_path / "out.json"

        sha256_ev.write_text(json.dumps(_make_raw_evidence(_SHA256_MAIN_PSEUDO)))
        cpp2_ev.write_text(json.dumps(_make_raw_evidence(_CPP2_MAIN_PSEUDO)))
        handoff_path.write_text(json.dumps(_make_handoff()))
        ai_path.write_text(json.dumps(_make_artifact_index(tmp_path, sha256_ev, cpp2_ev)))
        ida_path.write_text(json.dumps(_make_ida_summary()))

        result = run_targeted_reextraction(ai_path, ida_path, handoff_path, out_path)

        assert result["target_count"] == 2

    def test_hookapi_not_overridden(self, tmp_path: Path):
        """hookapi in handoff must not be overridden or re-validated."""
        sha256_ev = tmp_path / "sha256_ev.json"
        cpp2_ev = tmp_path / "cpp2_ev.json"
        handoff_path = tmp_path / "handoff.json"
        ai_path = tmp_path / "artifact_index.json"
        ida_path = tmp_path / "ida_summary.json"
        out_path = tmp_path / "out.json"

        sha256_ev.write_text(json.dumps(_make_raw_evidence(_SHA256_MAIN_PSEUDO)))
        cpp2_ev.write_text(json.dumps(_make_raw_evidence(_CPP2_MAIN_PSEUDO)))
        handoff_path.write_text(json.dumps(_make_handoff()))
        ai_path.write_text(json.dumps(_make_artifact_index(tmp_path, sha256_ev, cpp2_ev)))
        ida_path.write_text(json.dumps(_make_ida_summary()))

        result = run_targeted_reextraction(ai_path, ida_path, handoff_path, out_path)

        # Result should only contain sha_256 and CPP2, not Cpp1
        ids = {t["sample_id"] for t in result["targets"]}
        assert "bcbd9979db015bfd" not in ids
        # No target should have hookapi as a candidate or validated_candidate
        for t in result["targets"]:
            assert t.get("validated_candidate", "") != "hookapi"
            assert t.get("candidate", "") != "hookapi"
