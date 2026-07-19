#!/usr/bin/env python3
"""Standalone test runner for binding validation tests — 29 tests, no pytest."""

import sys
import os
import subprocess
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from validate_binding import BindingValidator
import yaml


def make_binding(**overrides):
    """Build a minimal valid binding YAML string, with dotted-key overrides."""
    base = {
        'schema_version': '1',
        'adt_repository': 'test/test-repo',
        'adt_pin': 'a' * 40,
        'governance_base': {'branch': 'main', 'sha': 'b' * 40},
        'authoritative_fact_source': {
            'type': 'HUMAN_EXPLICIT', 'evidence': 'test',
            'branch': 'feature/candidate', 'sha': 'c' * 40,
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
        'visual_status': {'active_candidate': 'CANDIDATE_NOT_ACCEPTED'},
        'authorized_action': 'test action',
        'authorized_write_scope': ['AGENTS.md'],
        'counter_objectives': ['no competing sources'],
        'progress': {'completed': 1, 'total': 5, 'display': '[##--------] 20%'},
        'user_action_required': 'NO',
        'system_next_step': 'Run tests',
        'last_verified_at': '2026-07-20T00:00:00Z',
    }
    for dotted_key, value in overrides.items():
        parts = dotted_key.split('.')
        node = base
        for part in parts[:-1]:
            if part not in node or not isinstance(node[part], dict):
                node[part] = {}
            node = node[part]
        if value == '':
            node.pop(parts[-1], None)
        else:
            node[parts[-1]] = value
    return '```yaml\n' + yaml.dump(base, default_flow_style=False, allow_unicode=True) + '```'


results = []


def run(name, fn):
    try:
        fn()
        print(f'  PASS  {name}')
        results.append(('PASS', name))
    except AssertionError as e:
        print(f'  FAIL  {name}  — {e}')
        results.append(('FAIL', name, str(e)))
    except Exception as e:
        print(f'  ERROR {name}  — {type(e).__name__}: {e}')
        results.append(('ERROR', name, str(e)))


# ═══ Test 1: Missing authoritative_fact_source → FAIL ═══

def test_01a():
    b = make_binding(**{'authoritative_fact_source.type': ''})
    v = BindingValidator(b)
    v.validate()
    assert any('VALIDATION-1' in e for e in v.errors)

def test_01b():
    b = make_binding(**{'authoritative_fact_source.sha': ''})
    v = BindingValidator(b)
    v.validate()
    assert any('VALIDATION-1' in e for e in v.errors)

# ═══ Test 2: active_candidate duplicates invalidated → FAIL ═══

def test_02():
    b = make_binding(
        **{'active_candidate.branch': 'feature/old',
           'invalidated_candidates': [
               {'branch': 'feature/old', 'sha': 'x' * 40,
                'invalidation_reason': 'obsolete'}
           ]})
    v = BindingValidator(b)
    v.validate()
    assert any('VALIDATION-2' in e for e in v.errors)

# ═══ Test 3: main dual role without Human auth → FAIL ═══

def test_03a():
    b = make_binding(
        **{'governance_base.branch': 'main',
           'authoritative_fact_source.branch': 'main',
           'authoritative_fact_source.type': 'BINDING_RECORD'})
    v = BindingValidator(b)
    v.validate()
    assert any('VALIDATION-3' in e for e in v.errors)

def test_03b():
    b = make_binding(
        **{'governance_base.branch': 'main',
           'authoritative_fact_source.branch': 'main',
           'authoritative_fact_source.type': 'HUMAN_EXPLICIT'})
    v = BindingValidator(b)
    v.validate()
    assert not any('VALIDATION-3' in e for e in v.errors)

# ═══ Test 4: comparison candidate used as active → FAIL ═══

def test_04():
    b = make_binding(
        **{'active_candidate.branch': 'feature/a',
           'comparison_candidates': [
               {'branch': 'feature/a', 'resolved_head': 'y' * 40,
                'status': 'COMPARISON_ONLY', 'comparison_group': 'g1'}
           ]})
    v = BindingValidator(b)
    v.validate()
    assert any('VALIDATION-4' in e for e in v.errors)

# ═══ Test 5: VISUAL_STATUS auto HUMAN_ACCEPTED by CI → FAIL ═══

def test_05():
    b = make_binding(
        **{'visual_status.active_candidate': 'HUMAN_ACCEPTED',
           'authoritative_fact_source.type': 'PR_HEAD'})
    v = BindingValidator(b)
    v.validate()
    assert any('VALIDATION-5' in e for e in v.errors)

# ═══ Test 6: FACT_SOURCE_REBIND with write → FAIL ═══

def test_06():
    b = make_binding(
        **{'current_gate': 'FACT_SOURCE_REBIND',
           'authorized_action': 'write product code'})
    v = BindingValidator(b)
    v.validate()
    assert any('VALIDATION-6' in e for e in v.errors)

# ═══ Test 7: progress card missing fields → WARN ═══

def test_07():
    b = make_binding(**{'system_next_step': ''})
    v = BindingValidator(b)
    v.validate()
    assert any('VALIDATION-7' in w for w in v.warnings)

# ═══ Test 8: candidate Head live check skipped in non-live mode ═══

def test_08():
    b = make_binding()
    v = BindingValidator(b, live_mode=False)
    v.validate()
    assert not any('VALIDATION-8' in e for e in v.errors)

# ═══ Test 9: A/B incident replay ═══

def test_09a():
    b = make_binding(
        **{'active_candidate.branch': 'codex/version-a',
           'active_candidate.starting_head': 'd' * 40,
           'comparison_candidates': [
               {'branch': 'codex/version-b', 'resolved_head': 'e' * 40,
                'status': 'COMPARISON_ONLY', 'comparison_group': 'ab'}
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
           'authoritative_fact_source.evidence': 'Human bound Version A',
    })
    v = BindingValidator(b)
    v.validate()
    assert not any('VALIDATION-2' in e for e in v.errors), 'Version A in invalidated'
    assert not any('VALIDATION-4' in e for e in v.errors), 'Version A in comparison'
    assert not any('VALIDATION-3' in e for e in v.errors), 'base conflated'
    assert not v.errors, f'Unexpected errors: {v.errors}'

def test_09b():
    b = make_binding(
        **{'active_candidate.branch': 'codex/version-a',
           'authoritative_fact_source.branch': 'main',
           'authoritative_fact_source.type': 'BINDING_RECORD'})
    v = BindingValidator(b)
    v.validate()
    assert any('VALIDATION-3' in e for e in v.errors)

def test_09c():
    b = make_binding(
        **{'active_candidate.branch': 'codex/version-a',
           'historical_references': [
               {'branch': 'pr-35', 'sha': 'f' * 40, 'role': 'Historical'}
           ],
           'authoritative_fact_source.branch': 'codex/version-a',
           'authoritative_fact_source.type': 'HUMAN_EXPLICIT'})
    v = BindingValidator(b)
    v.validate()
    assert not v.errors, f'Errors: {v.errors}'

def test_09d():
    b = make_binding(
        **{'active_candidate.branch': 'codex/version-a',
           'invalidated_candidates': [
               {'branch': 'codex/r2', 'sha': 'g' * 40,
                'invalidation_reason': 'wrong baseline'}
           ],
           'authoritative_fact_source.branch': 'codex/version-a',
           'authoritative_fact_source.type': 'HUMAN_EXPLICIT'})
    v = BindingValidator(b)
    v.validate()
    assert not any('VALIDATION-2' in e for e in v.errors)

# ═══ Test 10: minimum context recovery ═══

def test_10a():
    b = make_binding()
    v = BindingValidator(b)
    v.validate()
    assert not any('VALIDATION-10' in w for w in v.warnings), \
        f'Warnings: {v.warnings}'

def test_10b():
    b = make_binding(
        **{'schema_version': '', 'adt_repository': '',
           'governance_base.branch': '', 'governance_base.sha': ''})
    v = BindingValidator(b)
    v.validate()
    assert any('VALIDATION-10' in w for w in v.warnings)


# ══════════════════════════════════════════════════════════════════
# NEW: Runtime-head binding semantics (VALIDATION-8,9)
# ══════════════════════════════════════════════════════════════════

# ── Test 11: resolved_head as historical anchor ──

def test_11a():
    """resolved_head absent → no VALIDATION-9 error."""
    b = make_binding()
    v = BindingValidator(b)
    v.validate()
    assert not any('VALIDATION-9' in e for e in v.errors)

def test_11b():
    """resolved_head valid commit → PASS."""
    try:
        head = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True, text=True, timeout=10
        ).stdout.strip()
    except Exception:
        head = None
    if head and len(head) == 40:
        b = make_binding(**{'active_candidate.resolved_head': head})
        v = BindingValidator(b)
        v.validate()
        assert not any('VALIDATION-9' in e and 'resolved_head' in e
                       for e in v.errors), \
            f"Valid resolved_head should pass. Errors: {v.errors}"

def test_11c():
    """resolved_head invalid commit → FAIL."""
    b = make_binding(**{'active_candidate.resolved_head': '0' * 40})
    v = BindingValidator(b)
    v.validate()
    assert any('VALIDATION-9' in e and 'not a valid commit' in e
               for e in v.errors)

def test_11d():
    """resolved_head mismatch NOT an error — historical anchor, not live."""
    b = make_binding(**{'active_candidate.resolved_head': 'a' * 40})
    v = BindingValidator(b)
    v.validate()
    errors_text = ' '.join(v.errors)
    assert 'does not match' not in errors_text.lower() or \
        'resolved_head' not in errors_text.lower(), \
        f"resolved_head mismatch should not error. Errors: {v.errors}"

# ── Test 12: runtime_head_binding ──

def test_12a():
    """runtime_head_binding: GIT_REF_DERIVED → no warning."""
    b = make_binding(**{'active_candidate.runtime_head_binding': 'GIT_REF_DERIVED'})
    v = BindingValidator(b, live_mode=True)
    v.validate()
    assert not any('VALIDATION-9' in w and 'runtime_head_binding' in w
                   for w in v.warnings), f"Warnings: {v.warnings}"

def test_12b():
    """Missing runtime_head_binding → warning in live mode."""
    b = make_binding(**{'active_candidate.runtime_head_binding': ''})
    v = BindingValidator(b, live_mode=True)
    v.validate()
    assert any('VALIDATION-9' in w and 'runtime_head_binding' in w
               for w in v.warnings), f"Should warn. Warnings: {v.warnings}"

# ── Test 13: chicken-egg resolved ──

def test_13():
    """PROJECT_STATE.md doesn't need own commit SHA pre-recorded."""
    b = make_binding(
        **{'active_candidate.starting_head': 's' * 40,
           'active_candidate.resolved_head': 'r' * 40})
    v = BindingValidator(b)
    v.validate()
    assert not any('VALIDATION-8' in e for e in v.errors), \
        f"Static mode: no self-referential SHA required. Errors: {v.errors}"

# ── Test 14: starting_head field ──

def test_14():
    """starting_head presence is valid."""
    b = make_binding()
    v = BindingValidator(b)
    v.validate()
    assert not any('starting_head' in e for e in v.errors), \
        f"Errors: {v.errors}"

# ── Test 15: Push ref branch binding ──

def test_15a():
    """_push_ref_branch with GITHUB_REF=refs/heads/main → 'main'."""
    import os as _os
    v = BindingValidator('', live_mode=False)
    old = _os.environ.get('GITHUB_REF', '')
    try:
        _os.environ['GITHUB_REF'] = 'refs/heads/main'
        assert v._push_ref_branch() == 'main'
    finally:
        if old: _os.environ['GITHUB_REF'] = old
        else: _os.environ.pop('GITHUB_REF', None)

def test_15b():
    """_push_ref_branch with GITHUB_REF=refs/heads/hermes/example → 'hermes/example'."""
    import os as _os
    v = BindingValidator('', live_mode=False)
    old = _os.environ.get('GITHUB_REF', '')
    try:
        _os.environ['GITHUB_REF'] = 'refs/heads/hermes/example'
        assert v._push_ref_branch() == 'hermes/example'
    finally:
        if old: _os.environ['GITHUB_REF'] = old
        else: _os.environ.pop('GITHUB_REF', None)

def test_15c():
    """Missing GITHUB_REF + push event → HARD_STOP."""
    import os as _os
    b = make_binding()
    v = BindingValidator(b, live_mode=True)
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
                   for e in v.errors), f'Errors: {v.errors}'
    finally:
        if old: _os.environ['GITHUB_REF'] = old
        if old_event: _os.environ['GITHUB_EVENT_NAME'] = old_event
        else: _os.environ.pop('GITHUB_EVENT_NAME', None)

def test_15d():
    """GITHUB_REF=refs/tags/v1 + push event → HARD_STOP."""
    import os as _os
    b = make_binding()
    v = BindingValidator(b, live_mode=True)
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
                   for e in v.errors), f'Errors: {v.errors}'
    finally:
        if old: _os.environ['GITHUB_REF'] = old
        else: _os.environ.pop('GITHUB_REF', None)
        if old_event: _os.environ['GITHUB_EVENT_NAME'] = old_event
        else: _os.environ.pop('GITHUB_EVENT_NAME', None)

def test_15e():
    """GITHUB_REF=refs/notes/example + push event → HARD_STOP."""
    import os as _os
    b = make_binding()
    v = BindingValidator(b, live_mode=True)
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
                   for e in v.errors), f'Errors: {v.errors}'
    finally:
        if old: _os.environ['GITHUB_REF'] = old
        else: _os.environ.pop('GITHUB_REF', None)
        if old_event: _os.environ['GITHUB_EVENT_NAME'] = old_event
        else: _os.environ.pop('GITHUB_EVENT_NAME', None)

def test_15f():
    """GITHUB_REF='' + push event → HARD_STOP."""
    import os as _os
    b = make_binding()
    v = BindingValidator(b, live_mode=True)
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
                   for e in v.errors), f'Errors: {v.errors}'
    finally:
        if old: _os.environ['GITHUB_REF'] = old
        else: _os.environ.pop('GITHUB_REF', None)
        if old_event: _os.environ['GITHUB_EVENT_NAME'] = old_event
        else: _os.environ.pop('GITHUB_EVENT_NAME', None)

def test_15g():
    """Static mode unaffected by push_ref changes."""
    b = make_binding()
    v = BindingValidator(b, live_mode=False)
    v.validate()
    assert not any('VALIDATION-8' in e for e in v.errors), f'Errors: {v.errors}'

def test_15h():
    """PR merge ref not used for candidate identity."""
    b = make_binding()
    v = BindingValidator(b)
    v.validate()
    assert not any('merge' in e.lower() for e in v.errors), f'Errors: {v.errors}'

def test_15i():
    """resolved_head stays historical anchor."""
    b = make_binding(**{'active_candidate.resolved_head': 'h' * 40})
    v = BindingValidator(b)
    v.validate()
    assert 'push' not in ' '.join(v.errors).lower(), f'Errors: {v.errors}'


# ═══ All-valid pass ═══

def test_all_valid():
    b = make_binding()
    v = BindingValidator(b)
    v.validate()
    assert not v.errors, f'Errors: {v.errors}'


if __name__ == '__main__':
    print('Running 34 binding validation tests...\n')

    tests = [
        ('1.1 缺afs.type → FAIL', test_01a),
        ('1.2 缺afs.sha → FAIL', test_01b),
        ('2   active在invalidated中 → FAIL', test_02),
        ('3.1 main双角色无HUMAN_EXPLICIT → FAIL', test_03a),
        ('3.2 main双角色有HUMAN_EXPLICIT → PASS', test_03b),
        ('4   comparison当active → FAIL', test_04),
        ('5   CI PASS→HUMAN_ACCEPTED → FAIL', test_05),
        ('6   REBIND+写权限 → FAIL', test_06),
        ('7   进度卡缺next_step → WARN', test_07),
        ('8   非live跳过live检查', test_08),
        ('9.1 A/B回放—Version A选中', test_09a),
        ('9.2 拒绝main为产品源', test_09b),
        ('9.3 PR#35不影响Version A', test_09c),
        ('9.4 R2不污染Version A', test_09d),
        ('10.1 完整字段可恢复上下文', test_10a),
        ('10.2 缺字段触发警告', test_10b),
        # ── New: runtime-head binding semantics ──
        ('11a resolved_head缺省无错', test_11a),
        ('11b resolved_head有效commit→PASS', test_11b),
        ('11c resolved_head无效commit→FAIL', test_11c),
        ('11d resolved_head≠当前Head不报错', test_11d),
        ('12a runtime_head_binding: GIT_REF_DERIVED→PASS', test_12a),
        ('12b runtime_head_binding缺失→WARN', test_12b),
        ('13  PROJECT_STATE不预写自身SHA', test_13),
        ('14  starting_head字段合法', test_14),
        # ── New: Push ref branch binding ──
        ('15a GITHUB_REF=main → main', test_15a),
        ('15b GITHUB_REF=hermes/… → hermes/…', test_15b),
        ('15c GITHUB_REF缺失 → HARD_STOP', test_15c),
        ('15d GITHUB_REF=refs/tags/* → HARD_STOP', test_15d),
        ('15e GITHUB_REF=refs/notes/* → HARD_STOP', test_15e),
        ('15f GITHUB_REF=空 → HARD_STOP', test_15f),
        ('15g static不受push_ref影响', test_15g),
        ('15h PR merge ref不用于身份', test_15h),
        ('15i resolved_head保持历史锚点', test_15i),
        ('ALL  完整有效绑定全通过', test_all_valid),
    ]

    for name, fn in tests:
        run(name, fn)

    passed = sum(1 for r in results if r[0] == 'PASS')
    failed = sum(1 for r in results if r[0] != 'PASS')
    total = len(results)

    print(f'\n{"=" * 55}')
    print(f'  {passed} passed, {failed} failed, {total} total')
    print(f'{"=" * 55}')

    if failed > 0:
        print('\nFAILURES:')
        for r in results:
            if r[0] != 'PASS':
                print(f'  [{r[0]}] {r[1]}: {r[2]}')
        sys.exit(1)
    else:
        print(f'\nAll {total} tests passed.')
        sys.exit(0)
