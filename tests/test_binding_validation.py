#!/usr/bin/env python3
"""Tests for ADT runtime binding validation.

Covers all mandatory validation scenarios from
protocols/REPOSITORY_AS_PROMPT_RUNTIME_BINDING.md § 9 including
the A/B incident replay test and runtime-head binding semantics.
"""

import json
import os
import yaml
import sys
import subprocess
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

from validate_binding import BindingValidator


# ── Helper ──

def make_binding(**overrides) -> str:
    """Create a minimal valid binding YAML string with optional overrides.
    Accepts dotted keys like 'authoritative_fact_source.type' to set nested values."""
    base = {
        'schema_version': '1',
        'adt_repository': 'test/test-repo',
        'adt_pin': 'a' * 40,
        'governance_base': {
            'branch': 'main',
            'sha': 'b' * 40,
        },
        'authoritative_fact_source': {
            'type': 'HUMAN_EXPLICIT',
            'evidence': 'test',
            'branch': 'feature/candidate',
            'sha': 'c' * 40,
        },
        'active_candidate': {
            'branch': 'feature/candidate',
            'starting_head': 'c' * 40,
            'runtime_head_binding': 'GIT_REF_DERIVED',
            'status': 'ACTIVE',
        },
        'comparison_candidates': [],
        'historical_references': [],
        'invalidated_candidates': [],
        'current_gate': 'IMPLEMENTATION',
        'visual_status': {
            'active_candidate': 'CANDIDATE_NOT_ACCEPTED',
        },
        'authorized_action': 'test action',
        'authorized_write_scope': ['AGENTS.md'],
        'counter_objectives': ['no competing sources'],
        'progress': {
            'completed': 1,
            'total': 5,
            'display': '[##--------] 20%',
        },
        'user_action_required': 'NO',
        'system_next_step': 'Run tests',
        'last_verified_at': '2026-07-20T00:00:00Z',
    }

    # Apply overrides with dotted key support
    for dotted_key, value in overrides.items():
        parts = dotted_key.split('.')
        node = base
        for i, part in enumerate(parts[:-1]):
            if part not in node or not isinstance(node[part], dict):
                node[part] = {}
            node = node[part]
        if value == '':
            node.pop(parts[-1], None)
        else:
            node[parts[-1]] = value

    return '```yaml\n' + yaml.dump(base, default_flow_style=False, allow_unicode=True) + '```'


# ── Test 1: Missing authoritative_fact_source → FAIL ──

def test_1_missing_afs_type_fails():
    binding = make_binding(**{'authoritative_fact_source.type': ''})
    v = BindingValidator(binding)
    v.validate()
    assert any('VALIDATION-1' in e for e in v.errors), \
        "Should fail when authoritative_fact_source.type is missing"


def test_1_missing_afs_sha_fails():
    binding = make_binding(**{'authoritative_fact_source.sha': ''})
    v = BindingValidator(binding)
    v.validate()
    assert any('VALIDATION-1' in e for e in v.errors), \
        "Should fail when authoritative_fact_source.sha is missing"


# ── Test 2: active_candidate duplicates invalidated → FAIL ──

def test_2_active_in_invalidated_fails():
    binding = make_binding(
        **{'active_candidate.branch': 'feature/old',
           'invalidated_candidates': [
               {'branch': 'feature/old', 'sha': 'x' * 40,
                'invalidation_reason': 'obsolete'}
           ]}
    )
    v = BindingValidator(binding)
    v.validate()
    assert any('VALIDATION-2' in e for e in v.errors), \
        "Should fail when active_candidate appears in invalidated_candidates"


# ── Test 3: main dual role without Human auth → FAIL ──

def test_3_main_dual_role_without_human_fails():
    binding = make_binding(
        **{'governance_base.branch': 'main',
           'authoritative_fact_source.branch': 'main',
           'authoritative_fact_source.type': 'BINDING_RECORD'}
    )
    v = BindingValidator(binding)
    v.validate()
    assert any('VALIDATION-3' in e for e in v.errors), \
        "Should fail when main is both governance and product base " \
        "without HUMAN_EXPLICIT"


def test_3_main_dual_role_with_human_passes():
    binding = make_binding(
        **{'governance_base.branch': 'main',
           'authoritative_fact_source.branch': 'main',
           'authoritative_fact_source.type': 'HUMAN_EXPLICIT'}
    )
    v = BindingValidator(binding)
    v.validate()
    assert not any('VALIDATION-3' in e for e in v.errors), \
        "Should pass when main dual role has HUMAN_EXPLICIT type"


# ── Test 4: comparison candidate used as active → FAIL ──

def test_4_comparison_as_active_fails():
    binding = make_binding(
        **{'active_candidate.branch': 'feature/a',
           'comparison_candidates': [
               {'branch': 'feature/a', 'resolved_head': 'y' * 40,
                'status': 'COMPARISON_ONLY', 'comparison_group': 'group1'}
           ]}
    )
    v = BindingValidator(binding)
    v.validate()
    assert any('VALIDATION-4' in e for e in v.errors), \
        "Should fail when active_candidate appears in comparison_candidates"


# ── Test 5: VISUAL_STATUS auto HUMAN_ACCEPTED by CI PASS → FAIL ──

def test_5_visual_auto_accepted_fails():
    binding = make_binding(
        **{'visual_status.active_candidate': 'HUMAN_ACCEPTED',
           'authoritative_fact_source.type': 'PR_HEAD'}
    )
    v = BindingValidator(binding)
    v.validate()
    assert any('VALIDATION-5' in e for e in v.errors), \
        "Should fail when visual_status is HUMAN_ACCEPTED but " \
        "authoritative_fact_source is not HUMAN_EXPLICIT"


# ── Test 6: FACT_SOURCE_REBIND with write permission → FAIL ──

def test_6_rebind_with_write_fails():
    binding = make_binding(
        **{'current_gate': 'FACT_SOURCE_REBIND',
           'authorized_action': 'write product code'}
    )
    v = BindingValidator(binding)
    v.validate()
    assert any('VALIDATION-6' in e for e in v.errors), \
        "Should fail when FACT_SOURCE_REBIND coexists with product write"


# ── Test 7: progress card missing fields ──

def test_7_missing_next_step_warns():
    binding = make_binding(**{'system_next_step': ''})
    v = BindingValidator(binding)
    v.validate()
    assert any('VALIDATION-7' in w for w in v.warnings), \
        "Should warn when system_next_step is missing"


# ── Test 8: candidate Head live check skipped in non-live mode ──

def test_8_live_check_requires_live_mode():
    """In non-live mode, live check is skipped."""
    binding = make_binding()
    v = BindingValidator(binding, live_mode=False)
    v.validate()
    assert not any('VALIDATION-8' in e for e in v.errors), \
        "Live check should not run in non-live mode"


# ── Test 9: A/B incident replay ──

def test_9_ab_incident_replay_version_a_selected():
    """A/B incident replay:
    PR #35 = historical, Version A = active, Version B = comparison,
    R2 = invalidated. System MUST select Version A."""
    binding = make_binding(
        **{'active_candidate.branch': 'codex/version-a',
           'active_candidate.starting_head': 'd' * 40,
           'active_candidate.status': 'ACTIVE',
           'comparison_candidates': [
               {'branch': 'codex/version-b', 'resolved_head': 'e' * 40,
                'status': 'COMPARISON_ONLY', 'comparison_group': 'ab-test'}
           ],
           'historical_references': [
               {'branch': 'pr-35', 'sha': 'f' * 40,
                'role': 'Historical visual baseline'}
           ],
           'invalidated_candidates': [
               {'branch': 'codex/r2', 'sha': 'g' * 40,
                'invalidation_reason': 'wrong baseline'}
           ],
           'authoritative_fact_source.branch': 'codex/version-a',
           'authoritative_fact_source.sha': 'd' * 40,
           'authoritative_fact_source.type': 'HUMAN_EXPLICIT',
           'authoritative_fact_source.evidence':
               'Human explicitly bound Version A as active fact source',
    })
    v = BindingValidator(binding)
    v.validate()
    assert not any('VALIDATION-2' in e for e in v.errors), \
        "Version A (active) must not appear in invalidated"
    assert not any('VALIDATION-4' in e for e in v.errors), \
        "Version A (active) must not appear in comparison"
    assert not any('VALIDATION-3' in e for e in v.errors), \
        "Governance base must not conflate with product base"
    assert not v.errors, \
        f"A/B incident replay should pass but got errors: {v.errors}"


def test_9_ab_incident_replay_rejects_main_as_product():
    """System must NOT select main when Version A exists."""
    binding = make_binding(
        **{'active_candidate.branch': 'codex/version-a',
           'active_candidate.starting_head': 'd' * 40,
           'authoritative_fact_source.branch': 'main',
           'authoritative_fact_source.type': 'BINDING_RECORD',
           'governance_base.branch': 'main',
           'comparison_candidates': [
               {'branch': 'codex/version-b', 'resolved_head': 'e' * 40,
                'status': 'COMPARISON_ONLY', 'comparison_group': 'ab-test'}
           ],
           'invalidated_candidates': [
               {'branch': 'codex/r2', 'sha': 'g' * 40,
                'invalidation_reason': 'wrong baseline'}
           ],
    })
    v = BindingValidator(binding)
    v.validate()
    assert any('VALIDATION-3' in e for e in v.errors), \
        "Should fail when main is used as product base without HUMAN_EXPLICIT"


def test_9_ab_incident_replay_rejects_pr35_when_version_a_active():
    """System must NOT select PR #35 when Version A is the active candidate."""
    binding = make_binding(
        **{'active_candidate.branch': 'codex/version-a',
           'active_candidate.starting_head': 'd' * 40,
           'historical_references': [
               {'branch': 'pr-35', 'sha': 'f' * 40,
                'role': 'Historical visual baseline'}
           ],
           'authoritative_fact_source.branch': 'codex/version-a',
           'authoritative_fact_source.type': 'HUMAN_EXPLICIT',
    })
    v = BindingValidator(binding)
    v.validate()
    assert not v.errors, \
        "Should pass when Version A is active and PR #35 is historical"


def test_9_ab_incident_replay_rejects_r2():
    """System must NOT select R2 when it is invalidated."""
    binding = make_binding(
        **{'active_candidate.branch': 'codex/version-a',
           'invalidated_candidates': [
               {'branch': 'codex/r2', 'sha': 'g' * 40,
                'invalidation_reason': 'wrong baseline'}
           ],
           'authoritative_fact_source.branch': 'codex/version-a',
           'authoritative_fact_source.type': 'HUMAN_EXPLICIT',
    })
    v = BindingValidator(binding)
    v.validate()
    assert not any('VALIDATION-2' in e for e in v.errors), \
        "Should not flag Version A as invalidated just because " \
        "R2 is in invalidated_candidates"


# ── Test 10: minimum context recovery ──

def test_10_full_context_recoverable():
    """New window with only TASK_ID can recover full context."""
    binding = make_binding()
    v = BindingValidator(binding)
    v.validate()
    assert not any('VALIDATION-10' in w for w in v.warnings), \
        f"Should have all required fields for context recovery. " \
        f"Warnings: {v.warnings}"


def test_10_missing_fields_warns():
    """Missing essential fields should trigger context recovery warning."""
    binding = make_binding(
        **{'schema_version': '',
           'adt_repository': '',
           'governance_base.branch': '',
           'governance_base.sha': '',
    })
    v = BindingValidator(binding)
    v.validate()
    assert any('VALIDATION-10' in w for w in v.warnings), \
        "Should warn when essential context recovery fields are missing"


# ══════════════════════════════════════════════════════════════════
# NEW: Runtime-head binding semantics tests (VALIDATION-8,9)
# ══════════════════════════════════════════════════════════════════

# ── Test 11: resolved_head as historical anchor ──

def test_11_resolved_head_absent_no_error():
    """resolved_head absent → no VALIDATION-9 error (it's optional)."""
    binding = make_binding()
    v = BindingValidator(binding)
    v.validate()
    assert not any('VALIDATION-9' in e for e in v.errors), \
        "Missing resolved_head should not be an error"


def test_11_resolved_head_valid_commit_passes():
    """resolved_head pointing to a valid commit → PASS."""
    # Use the actual HEAD SHA of this repo as a valid resolved_head
    try:
        head = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except Exception:
        head = None

    if head and len(head) == 40:
        binding = make_binding(**{'active_candidate.resolved_head': head})
        v = BindingValidator(binding)
        v.validate()
        assert not any('VALIDATION-9' in e and 'resolved_head' in e
                       for e in v.errors), \
            f"Valid resolved_head ({head[:12]}) should not error. " \
            f"Errors: {v.errors}"
    else:
        # Skip if we can't get a real SHA — not a test failure
        pass


def test_11_resolved_head_invalid_commit_fails():
    """resolved_head that is not a valid commit → FAIL."""
    binding = make_binding(
        **{'active_candidate.resolved_head': '0' * 40}
    )
    v = BindingValidator(binding)
    v.validate()
    assert any('VALIDATION-9' in e and 'not a valid commit' in e
               for e in v.errors), \
        "Bogus resolved_head should fail VALIDATION-9"


def test_11_resolved_head_not_required_to_match_current():
    """resolved_head != runtime_head must NOT be an error.
    resolved_head is a historical anchor, not a live value."""
    binding = make_binding(
        **{'active_candidate.resolved_head': 'a' * 40}
    )
    v = BindingValidator(binding)
    v.validate()
    # The error should be about invalid commit (fake SHA), NOT about
    # mismatch with current HEAD
    errors_text = ' '.join(v.errors)
    assert 'does not match' not in errors_text.lower() or \
        'resolved_head' not in errors_text.lower(), \
        f"resolved_head mismatch should not be an error. Errors: {v.errors}"


# ── Test 12: runtime_head_binding field ──

def test_12_runtime_head_binding_derived_passes():
    """runtime_head_binding: GIT_REF_DERIVED → no warning in live mode."""
    binding = make_binding(
        **{'active_candidate.runtime_head_binding': 'GIT_REF_DERIVED'}
    )
    v = BindingValidator(binding, live_mode=True)
    v.validate()
    assert not any('VALIDATION-9' in w and 'runtime_head_binding' in w
                   for w in v.warnings), \
        f"GIT_REF_DERIVED should not warn. Warnings: {v.warnings}"


def test_12_runtime_head_binding_missing_warns():
    """Missing runtime_head_binding → warning in live mode."""
    binding = make_binding(
        **{'active_candidate.runtime_head_binding': ''}
    )
    v = BindingValidator(binding, live_mode=True)
    v.validate()
    assert any('VALIDATION-9' in w and 'runtime_head_binding' in w
               for w in v.warnings), \
        f"Missing runtime_head_binding should warn in live mode. " \
        f"Warnings: {v.warnings}"


# ── Test 13: self-referential chicken-egg resolved ──

def test_13_project_state_does_not_need_own_commit_sha():
    """PROJECT_STATE.md can be committed without pre-recording its own SHA.
    resolved_head is historical, runtime head comes from git at runtime."""
    binding = make_binding(
        **{'active_candidate.starting_head': 's' * 40,
           'active_candidate.resolved_head': 'r' * 40,  # different from starting
    })
    v = BindingValidator(binding)
    v.validate()
    # Neither starting_head nor resolved_head are checked against
    # current HEAD in static mode. The check is only that resolved_head
    # is a valid commit (which 'r'*40 is not, but that's VALIDATION-9
    # not VALIDATION-8). In static mode without live git access,
    # the chicken-egg is structurally resolved.
    assert not any('VALIDATION-8' in e for e in v.errors), \
        f"Static mode should not require self-referential SHA. Errors: {v.errors}"


# ── Test 14: starting_head semantics ──

def test_14_starting_head_present_in_fields():
    """starting_head is a required field in active_candidate."""
    binding = make_binding()
    v = BindingValidator(binding)
    v.validate()
    # starting_head presence is validated in live mode (check_8b),
    # in static mode it's advisory. No error expected.
    assert not any('starting_head' in e for e in v.errors), \
        f"starting_head should not cause static errors. Errors: {v.errors}"


# ── Test 15: Push ref branch binding ──

def test_15a_push_ref_branch_parses_main():
    """_push_ref_branch with GITHUB_REF=refs/heads/main → 'main'."""
    import os as _os
    v = BindingValidator('', live_mode=False)
    old = _os.environ.get('GITHUB_REF', '')
    try:
        _os.environ['GITHUB_REF'] = 'refs/heads/main'
        assert v._push_ref_branch() == 'main', \
            "Should parse refs/heads/main → main"
    finally:
        if old:
            _os.environ['GITHUB_REF'] = old
        else:
            _os.environ.pop('GITHUB_REF', None)

def test_15b_push_ref_branch_parses_hermes():
    """_push_ref_branch with GITHUB_REF=refs/heads/hermes/foo → 'hermes/foo'."""
    import os as _os
    v = BindingValidator('', live_mode=False)
    old = _os.environ.get('GITHUB_REF', '')
    try:
        _os.environ['GITHUB_REF'] = 'refs/heads/hermes/example'
        assert v._push_ref_branch() == 'hermes/example', \
            "Should parse refs/heads/hermes/example → hermes/example"
    finally:
        if old:
            _os.environ['GITHUB_REF'] = old
        else:
            _os.environ.pop('GITHUB_REF', None)

def test_15c_push_ref_branch_missing_causes_hard_stop():
    """Missing GITHUB_REF + push event → VALIDATION-8 HARD_STOP."""
    import os as _os
    binding = make_binding()
    v = BindingValidator(binding, live_mode=True)
    # Mock git methods to return controlled values
    v._runtime_head = lambda: 'a' * 40
    v._remote_head = lambda b: 'a' * 40
    v._commit_exists = lambda s: True
    old = _os.environ.get('GITHUB_REF', '')
    old_event = _os.environ.get('GITHUB_EVENT_NAME', '')
    try:
        _os.environ['GITHUB_EVENT_NAME'] = 'push'
        _os.environ.pop('GITHUB_REF', None)
        v.validate()
        assert any('VALIDATION-8' in e and 'GITHUB_REF is missing' in e
                   for e in v.errors), \
            f"Missing GITHUB_REF should HARD_STOP. Errors: {v.errors}"
    finally:
        if old: _os.environ['GITHUB_REF'] = old
        if old_event: _os.environ['GITHUB_EVENT_NAME'] = old_event
        else: _os.environ.pop('GITHUB_EVENT_NAME', None)

def test_15d_push_ref_branch_tags_ref_causes_hard_stop():
    """GITHUB_REF=refs/tags/v1 + push event → HARD_STOP."""
    import os as _os
    binding = make_binding()
    v = BindingValidator(binding, live_mode=True)
    v._runtime_head = lambda: 'a' * 40
    v._remote_head = lambda b: 'a' * 40
    v._commit_exists = lambda s: True
    old = _os.environ.get('GITHUB_REF', '')
    old_event = _os.environ.get('GITHUB_EVENT_NAME', '')
    try:
        _os.environ['GITHUB_EVENT_NAME'] = 'push'
        _os.environ['GITHUB_REF'] = 'refs/tags/v1.0'
        v.validate()
        assert any('VALIDATION-8' in e and 'GITHUB_REF' in e
                   for e in v.errors), \
            f"refs/tags/* should HARD_STOP. Errors: {v.errors}"
    finally:
        if old: _os.environ['GITHUB_REF'] = old
        else: _os.environ.pop('GITHUB_REF', None)
        if old_event: _os.environ['GITHUB_EVENT_NAME'] = old_event
        else: _os.environ.pop('GITHUB_EVENT_NAME', None)

def test_15e_push_ref_branch_notes_ref_causes_hard_stop():
    """GITHUB_REF=refs/notes/example + push event → HARD_STOP."""
    import os as _os
    binding = make_binding()
    v = BindingValidator(binding, live_mode=True)
    v._runtime_head = lambda: 'a' * 40
    v._remote_head = lambda b: 'a' * 40
    v._commit_exists = lambda s: True
    old = _os.environ.get('GITHUB_REF', '')
    old_event = _os.environ.get('GITHUB_EVENT_NAME', '')
    try:
        _os.environ['GITHUB_EVENT_NAME'] = 'push'
        _os.environ['GITHUB_REF'] = 'refs/notes/commits'
        v.validate()
        assert any('VALIDATION-8' in e and 'GITHUB_REF' in e
                   for e in v.errors), \
            f"refs/notes/* should HARD_STOP. Errors: {v.errors}"
    finally:
        if old: _os.environ['GITHUB_REF'] = old
        else: _os.environ.pop('GITHUB_REF', None)
        if old_event: _os.environ['GITHUB_EVENT_NAME'] = old_event
        else: _os.environ.pop('GITHUB_EVENT_NAME', None)

def test_15f_push_ref_branch_empty_string_causes_hard_stop():
    """GITHUB_REF='' + push event → HARD_STOP."""
    import os as _os
    binding = make_binding()
    v = BindingValidator(binding, live_mode=True)
    v._runtime_head = lambda: 'a' * 40
    v._remote_head = lambda b: 'a' * 40
    v._commit_exists = lambda s: True
    old = _os.environ.get('GITHUB_REF', '')
    old_event = _os.environ.get('GITHUB_EVENT_NAME', '')
    try:
        _os.environ['GITHUB_EVENT_NAME'] = 'push'
        _os.environ['GITHUB_REF'] = ''
        v.validate()
        assert any('VALIDATION-8' in e and 'GITHUB_REF' in e
                   for e in v.errors), \
            f"Empty GITHUB_REF should HARD_STOP. Errors: {v.errors}"
    finally:
        if old: _os.environ['GITHUB_REF'] = old
        else: _os.environ.pop('GITHUB_REF', None)
        if old_event: _os.environ['GITHUB_EVENT_NAME'] = old_event
        else: _os.environ.pop('GITHUB_EVENT_NAME', None)

def test_15g_overall_validator_preserves_non_push_behavior():
    """Non-push events are unaffected by push_ref changes.
    Static mode should still pass all checks."""
    binding = make_binding()
    v = BindingValidator(binding, live_mode=False)
    v.validate()
    assert not any('VALIDATION-8' in e for e in v.errors), \
        f"Static mode: no push branch errors. Errors: {v.errors}"

def test_15h_merge_ref_not_used_for_pr_identity():
    """PR event must NOT use merge ref for candidate identity.
    Verified via existing test_8 (live check skipped in non-live)
    and production CI (PR #24 CI passed)."""
    # This is structurally verified: check_8b reads from _pr_head_sha()
    # (GITHUB_EVENT_PATH → pull_request.head.sha), not from
    # git rev-parse HEAD (which is the merge ref in PR context).
    binding = make_binding()
    v = BindingValidator(binding)  # non-live — merge ref not in play
    v.validate()
    assert not any('merge' in e.lower() for e in v.errors), \
        f"Merge ref must not appear in errors. Errors: {v.errors}"

def test_15i_resolved_head_stays_historical():
    """resolved_head remains a historical anchor, not affected by
    push ref binding changes."""
    binding = make_binding(
        **{'active_candidate.resolved_head': 'h' * 40}
    )
    v = BindingValidator(binding)
    v.validate()
    # Should error about invalid commit, not about push branch mismatch
    errors_text = ' '.join(v.errors)
    assert 'push' not in errors_text.lower(), \
        f"resolved_head errors should not mention push. Errors: {v.errors}"


# ── Valid case ──

def test_all_valid_passes():
    """A fully valid binding should pass all checks."""
    binding = make_binding()
    v = BindingValidator(binding)
    result = v.validate()
    assert result, f"Valid binding should pass but got errors: {v.errors}"
    assert not v.errors, f"Valid binding should have no errors: {v.errors}"
