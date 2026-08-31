# HTML Report Template

> Internal reference for the self-contained HTML mirror written alongside
> terminal interactions throughout the pipeline.

## Purpose

Define the structure of `merge-report.html` — a full-view mirror of the merge
session. Self-contained (no CDN, no fonts, no external resources). Openable
offline. Can be printed or archived.

## Constraints

- **Self-contained**: inline CSS + inline JS (or sibling `merge-report.js` if HTML grows > 200KB)
- **Vanilla JS only**: no jQuery, no framework. ≤ 100 lines of JS.
- **No external resources**: no CDN URLs, no external fonts/images
- **Offline-openable, printable**: should look reasonable in browser print preview
- **Append-mode writes**: each new decision point is appended as a new `<article>`. State updates (pending → resolved/skipped) rewrite the existing article in-place.

## Allowed JS Features

- Smooth scroll to anchor on TOC click
- Keyboard shortcuts: `j` / `k` jump to next/prev decision; `g` go to TOC
- Update sticky TOC counts as decision states change (when reloaded after append)
- Collapsible long diffs: auto-collapse hunks > 80 lines into a `<details>` element
- Highlight currently-focused decision article on hover

## Skeleton

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <title>合并报告 — {{task_name}}</title>
  <style>
    body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 1200px; margin: 2em auto; padding: 0 1em; color: #1f2328; }
    h1, h2, h3, h4 { font-weight: 600; }
    dl { display: grid; grid-template-columns: 8em 1fr; gap: 0.25em 1em; }
    dt { color: #57606a; }
    pre { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; background: #f6f8fa; padding: 1em; overflow-x: auto; border-radius: 6px; font-size: 0.9em; line-height: 1.4; }
    code.added { background: #e6ffec; color: #1a7f37; }
    code.removed { background: #ffebe9; color: #cf222e; }
    article.decision { border: 1px solid #d0d7de; border-radius: 6px; margin: 1.5em 0; padding: 1em 1.25em; }
    article.decision.pending { border-left: 4px solid #fb8500; }
    article.decision.resolved { border-left: 4px solid #2da44e; }
    article.decision.skipped { border-left: 4px solid #6e7781; opacity: 0.7; }
    article.decision .meta { color: #57606a; font-size: 0.9em; }
    .diff-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 1em; }
    .options { list-style: decimal inside; padding-left: 0; }
    .options li.selected { background: #ddf4ff; font-weight: 600; }
    nav.toc { position: sticky; top: 0; background: white; padding: 0.5em 0; border-bottom: 1px solid #eee; z-index: 10; }
    nav.toc a { margin-right: 1em; color: #0969da; text-decoration: none; }
    nav.toc a:hover { text-decoration: underline; }
    footer { margin-top: 3em; color: #57606a; font-size: 0.85em; border-top: 1px solid #eee; padding-top: 1em; }
    @media print { nav.toc { position: static; } article.decision { break-inside: avoid; } }
  </style>
</head>
<body>
  <header>
    <h1>合并报告 — {{task_name}}</h1>
    <dl>
      <dt>形态</dt><dd>{{mode}}</dd>
      <dt>源</dt><dd>{{source_ref}}@{{source_sha}}</dd>
      <dt>目标</dt><dd>{{target_ref}}@{{target_sha}}</dd>
      <dt>工作分支</dt><dd>merge/{{task_name}}（基于 {{base_sha}}）</dd>
      <dt>开始时间</dt><dd>{{started_at}}</dd>
      <dt>状态</dt><dd id="overall-status">{{status}}</dd>
    </dl>
  </header>

  <nav class="toc">
    <a href="#strategy">策略</a>
    <a href="#auto-resolved">自动处理</a>
    <a href="#decisions">决策点 (<span id="decisions-count">{{resolved}}/{{total}}</span>)</a>
  </nav>

  <section id="strategy">
    <h2>合并策略报告</h2>
    {{strategy_html}}
  </section>

  <section id="auto-resolved">
    <h2>A 类自动处理（{{a_count}} 处）</h2>
    <details>
      <summary>展开查看明细</summary>
      <table>
        <thead><tr><th>文件</th><th>方法/范围</th><th>规则</th></tr></thead>
        <tbody>{{auto_rows}}</tbody>
      </table>
    </details>
  </section>

  <section id="decisions">
    <h2>决策点</h2>

    <!-- Example article; one per decision -->
    <article id="decision-3" class="decision c-class resolved" data-decision-id="3">
      <h3>决策点 3 · src/service/OrderService.java::calcDiscount()</h3>
      <p class="meta">分类：C 类 · 状态：<span class="status">✅ 已解决</span></p>
      <div class="diff-pair">
        <div class="source-diff">
          <h4>源侧改动</h4>
          <pre><code class="lang-java">{{source_diff}}</code></pre>
        </div>
        <div class="target-diff">
          <h4>目标侧改动</h4>
          <pre><code class="lang-java">{{target_diff}}</code></pre>
        </div>
      </div>
      <div class="model-analysis">
        <h4>模型分析</h4>
        <ul>
          <li>源侧意图：{{source_intent}}</li>
          <li>目标侧意图：{{target_intent}}</li>
          <li>冲突点：{{conflict_summary}}</li>
        </ul>
      </div>
      <ol class="options">
        <li>take source</li>
        <li>take target</li>
        <li class="selected">source-first-then-target ★</li>
        <li>target-first-then-source</li>
        <li>自由输入</li>
      </ol>
      <div class="user-choice">用户选择：3</div>
      <div class="free-text-explanation" hidden>{{free_text_echo}}</div>
    </article>

  </section>

  <footer><p>报告生成于 {{generated_at}} · skill: git-merge-conductor v1</p></footer>

  <script>
    // Vanilla JS, ≤ 100 lines
    (function() {
      // Smooth scroll for TOC links
      document.querySelectorAll('nav.toc a').forEach(function(a) {
        a.addEventListener('click', function(e) {
          var href = a.getAttribute('href');
          if (href && href.startsWith('#')) {
            e.preventDefault();
            var el = document.querySelector(href);
            if (el) el.scrollIntoView({behavior: 'smooth', block: 'start'});
          }
        });
      });

      // Keyboard shortcuts: j/k jump decisions, g go to TOC
      var decisions = Array.from(document.querySelectorAll('article.decision'));
      var currentIdx = 0;
      document.addEventListener('keydown', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') return;
        if (e.key === 'j') {
          currentIdx = Math.min(currentIdx + 1, decisions.length - 1);
          if (decisions[currentIdx]) decisions[currentIdx].scrollIntoView({behavior: 'smooth', block: 'start'});
        } else if (e.key === 'k') {
          currentIdx = Math.max(currentIdx - 1, 0);
          if (decisions[currentIdx]) decisions[currentIdx].scrollIntoView({behavior: 'smooth', block: 'start'});
        } else if (e.key === 'g') {
          document.querySelector('nav.toc').scrollIntoView({behavior: 'smooth', block: 'start'});
        }
      });

      // Auto-collapse long diffs (> 80 lines)
      document.querySelectorAll('pre').forEach(function(pre) {
        var lineCount = pre.textContent.split('\n').length;
        if (lineCount > 80) {
          var details = document.createElement('details');
          var summary = document.createElement('summary');
          summary.textContent = '展开 ' + lineCount + ' 行';
          details.appendChild(summary);
          pre.parentNode.insertBefore(details, pre);
          details.appendChild(pre);
        }
      });
    })();
  </script>
</body>
</html>
```

## Write Semantics

| Pipeline Stage | What to Write to HTML |
|---|---|
| Stage 2 (strategy approved) | Write the full skeleton above with `<section id="strategy">` filled. Other sections are empty placeholders. |
| Stage 5 (auto-resolved) | Fill `<section id="auto-resolved">` with the A class details table. |
| Stage 6 (each decision) | Append a new `<article>` for the pending decision. On resolution, rewrite the same article's `class` and `<div class="user-choice">`. |
| Stage 6 (skipped) | Mark article class `skipped`. |
| Stage 8 (finalize) | Update `<dd id="overall-status">` to `finalized`, update `<span id="decisions-count">`. |

## Implementation Notes

- Each `<article id="decision-N">` lets the user jump directly via URL fragment (e.g., `merge-report.html#decision-3`).
- Keep the HTML idempotent: appending the same article twice should not double-render — check for existing `id="decision-N"` and replace instead.
- Code highlighting is class-based (`<code class="lang-java">`). No actual highlighter runs; this is just a hook for future enhancement.

## Verification Section (Stage 7.5 Phase 2)

Append this section to the HTML report when Phase 2 runs:

```html
<section id="verification">
  <h2>验证报告 — iter {{iter}}</h2>
  
  <h3>自动化校验</h3>
  <ul class="check-list">
    <li class="{{compile_class}}"><span class="label">compile</span>: {{compile_status}}</li>
    <li class="{{lint_class}}"><span class="label">lint</span>: {{lint_status}}</li>
    <li class="{{test_class}}"><span class="label">test</span>: {{test_status}}</li>
  </ul>

  <h3>需求清单兑现</h3>
  <table class="reqs">
    <thead><tr><th>REQ</th><th>标题</th><th>scope_tag</th><th>status</th><th>evidence</th><th>备注</th></tr></thead>
    <tbody>
      {{requirements_table_rows}}
    </tbody>
  </table>

  <h3>Self-Audit 拦截项</h3>
  {{audit_intercept_blocks_or_empty}}

  <h3>范围外尝试 (NC-05)</h3>
  {{nc05_blocks_or_empty}}

  <h3>未决项</h3>
  {{pending_blocks_or_empty}}

  <h3>用户决定</h3>
  <p class="user-decision">{{user_response}}{{ if echo: " — 我理解为: {{model_interpretation}}"}}</p>
</section>
```

Add minimal CSS to the existing `<style>` block:
```css
.check-list .pass { color: #1a7f37; }
.check-list .fail { color: #d1242f; }
.check-list .skip { color: #8b949e; }
.reqs tr.completed { background: #dafbe1; }
.reqs tr.partial { background: #fff8c5; }
.reqs tr.pending { background: #ffebe9; }
.reqs tr.abandoned { background: #d0d7de; }
```
