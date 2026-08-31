import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools", "hooks"))

def test_inject_index_reads_single_vault_index(tmp_path):
    import inject_index
    ctx = tmp_path / "vault" / "memory"
    ctx.mkdir(parents=True)
    (ctx / "INDEX.md").write_text("# vault INDEX\n- decision-tree\n")
    out = inject_index.inject_index(str(ctx))
    assert "vault INDEX" in out

def test_inject_index_missing_returns_empty(tmp_path):
    import inject_index
    out = inject_index.inject_index(str(tmp_path / "nope"))
    assert out == ""

def test_operating_rules_injected_before_index(tmp_path):
    import inject_index
    (tmp_path / "00-RULES").mkdir()
    (tmp_path / "00-RULES" / "operating-rules.md").write_text("[操作规则]-MARKER\n", encoding="utf-8")
    (tmp_path / "INDEX.md").write_text("# vault INDEX\n", encoding="utf-8")
    out = inject_index.inject_index(str(tmp_path))
    assert "[操作规则]-MARKER" in out
    assert out.index("[操作规则]-MARKER") < out.index("vault INDEX")
