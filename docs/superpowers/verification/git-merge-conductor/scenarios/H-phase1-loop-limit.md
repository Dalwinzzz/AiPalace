# Scenario H — Phase 1 self-fix loop limit (N=3)

## Goal

Verify Phase 1's bounded self-fix behavior:
- Inject a deliberate compile error via a graft
- Stage 7.5 Phase 1 detects compile fail
- Model attempts fix iter 1 → still fails
- Iter 2 → still fails
- Iter 3 → still fails
- After iter 3, model surrenders and passes error to Phase 2 verbatim
- `state.json::iterations[]` shows 3 entries with `trigger: phase1-fix`
- User decides in Phase 2

## Setup

Reuse the F fixture but inject a compile-breaking source.

```bash
cd /tmp && rm -rf gmc-fixture-H
bash /Users/dalwin/Documents/AI/docs/superpowers/verification/git-merge-conductor/setup-fixture.sh   # ensures /tmp/gmc-fixture-F exists
cp -r /tmp/gmc-fixture-F /tmp/gmc-fixture-H
cd /tmp/gmc-fixture-H
git checkout refactor/micro-core-dev

# Inject syntax error in CareClassUtil. NOTE: we deliberately REMOVE the
# projectName == "JIASHAN" guard from the F-fixture source so NC-01 does NOT
# fire here — otherwise Stage 6.5 would rollback the graft before Phase 1
# ever sees the syntax error, and this scenario would just retrace F's
# NC-01 path instead of testing Phase 1's self-fix N=3 cap.
cat > plugins/care-class/src/main/java/com/example/care/CareClassUtil.java <<'JAVA'
package com.example.care;
public class CareClassUtil {
    public static String normalizeCareClassTeacherName(String raw)
        // intentionally missing return type + braces — compile will fail
        return raw.replace("老师", "");
    }
}
JAVA
git add . && git commit -q -m "intentional: introduce syntax error (no project guard)"
```

## Run

Start Claude Code in `/tmp/gmc-fixture-H` and invoke same as scenario F's instruction
prompt. When asked to extract requirements at Stage 2, the model should produce
something like REQ-01 with `scope_tag: 通用课堂功能` and `out_of_scope` listing
the standard NC-01 caveat — but since the source no longer carries the project
guard, the graft itself will not trigger NC-01.

## Expected pipeline behavior

Stages 0-7 proceed similarly to F. The graft applies (Stage 6t), Stage 6.5
passes (NC checks don't catch syntax errors). Stage 7 commits.

### Stage 7.5 Phase 1

- iter 1: `mvn compile` → BUILD FAILURE; model attempts fix:
  - rollback graft G-01
  - regenerate draft (may produce same or different syntax)
  - reapply
  - re-run compile → still FAIL
- iter 2: similar attempt → still FAIL
- iter 3: similar attempt → still FAIL
- After iter 3, model surrenders; phase1.result = "fail-with-errors";
  errors[] populated with compile output verbatim

### Stage 7.5 Phase 2

- Report includes "Phase 1 自修复轮次" table with 3 iter rows, all failed
- Report shows the compile error text in a fenced block

User responds (e.g.): "REQ-01 没做对——syntax error 是源端的，先回滚 REQ-01 让我手工修源端"

iter += 1 (now iter 4 overall), but `trigger: user-feedback` (not phase1-fix).
The loop budget for phase1-fix iters resets in the next Phase 2 round.

## Inspection commands

```bash
cat .git/merge-conductor/<task>/state.json | jq '.iterations | map({iter, trigger, ended_at})'
# Expected: at least 3 entries with trigger == "phase1-fix" in iter 1's life,
# plus initial entry. Total length ≥ 4 after user feedback.
```

## Pass criteria

- [ ] Phase 1 iter cap N=3 enforced (no iter 4 of phase1-fix)
- [ ] All 3 iter attempts logged in iterations[] with trigger: phase1-fix
- [ ] Phase 2 report shows the compile error
- [ ] User feedback in Phase 2 triggers a new outer iter (not phase1-fix)
