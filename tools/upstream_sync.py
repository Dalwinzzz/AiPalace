#!/usr/bin/env python3
"""同步指定上游仓库并刷新 AiPalace 中可明确溯源的 skill 硬拷贝。

策略：
1. 先更新指定上游仓库到主分支。优先 `main`；若远端不存在 `origin/main`，则回落到
   `origin/HEAD` 指向的默认分支，并在结果中说明。
2. 仅同步 AiPalace 中来源明确、且能映射到本地上游仓库的 skill 目录。
3. 对于目标目录内“源里没有”的本地文件，全部保留，并在结果中汇报；不做删除。
4. 若 AiPalace 有实际变更且启用 `--commit`，自动提交：
   `chore: 同步上游 skills 硬拷贝（codex定时任务）`
"""

from __future__ import annotations

import argparse
import contextlib
import filecmp
import shutil
import subprocess
import sys
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


SCRIPT = Path(__file__).resolve()
AIPALACE_ROOT = SCRIPT.parents[1]
WORKSPACE_ROOT = AIPALACE_ROOT.parent
LOG_DIR = AIPALACE_ROOT / "logs"
RUN_LOG = LOG_DIR / "aipalace-upstream-sync.log"
ERR_LOG = LOG_DIR / "aipalace-upstream-sync.err.log"

COMMIT_MESSAGE = "chore: 同步上游 skills 硬拷贝（codex定时任务）"
IGNORED_NAMES = {".DS_Store", ".git"}


class TeeStream:
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data: str) -> int:
        for stream in self.streams:
            stream.write(data)
        return len(data)

    def flush(self) -> None:
        for stream in self.streams:
            stream.flush()


@dataclass
class RepoUpdateResult:
    repo: str
    branch: str | None = None
    previous_rev: str | None = None
    current_rev: str | None = None
    status: str = "pending"
    note: str = ""


@dataclass
class SyncResult:
    source: str
    target: str
    updated_files: list[str] = field(default_factory=list)
    added_files: list[str] = field(default_factory=list)
    preserved_files: list[str] = field(default_factory=list)
    status: str = "pending"
    note: str = ""


@dataclass(frozen=True)
class RepoConfig:
    path: str
    preferred_branch: str = "main"


REPOS = [
    RepoConfig("everything-claude-code"),
    RepoConfig("garveyhu/awesome-skills"),
    RepoConfig("get-shit-done"),
    RepoConfig("langchain"),
    RepoConfig("skillhub"),
    RepoConfig("skills"),
    RepoConfig("superpowers"),
]


EXPLICIT_SKILL_MAPS = [
    (
        WORKSPACE_ROOT / "skills/skills/productivity/grill-me",
        AIPALACE_ROOT / "skills/community/github-skills/grill-me",
        "skills/grill-me",
    ),
    (
        WORKSPACE_ROOT / "skills/skills/engineering/grill-with-docs",
        AIPALACE_ROOT / "skills/community/github-skills/grill-with-docs",
        "skills/grill-with-docs",
    ),
]

EXCLUDED_TARGETS = {
    "skills/community/garveyhu/method/skill-management": "该 skill 在 AiPalace 内已演进为本地版本，按约定跳过上游覆盖",
}


def run(
    args: list[str],
    *,
    cwd: Path,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd),
        check=check,
        capture_output=True,
        text=True,
    )


def git_output(repo: Path, *args: str) -> str:
    return run(["git", *args], cwd=repo).stdout.strip()


def git_ok(repo: Path, *args: str) -> bool:
    proc = run(["git", *args], cwd=repo, check=False)
    return proc.returncode == 0


def short_rev(repo: Path) -> str:
    return git_output(repo, "rev-parse", "--short", "HEAD")


def repo_is_dirty(repo: Path) -> bool:
    return bool(git_output(repo, "status", "--porcelain"))


def resolve_target_branch(repo: Path, preferred: str) -> tuple[str | None, str]:
    preferred_remote = f"refs/remotes/origin/{preferred}"
    if git_ok(repo, "show-ref", "--verify", "--quiet", preferred_remote):
        return preferred, ""

    head_ref = git_output(repo, "symbolic-ref", "refs/remotes/origin/HEAD")
    fallback = head_ref.rsplit("/", 1)[-1]
    if fallback == preferred:
        return preferred, ""
    return fallback, f"origin/{preferred} 不存在，按远端默认分支 {fallback} 拉取"


def ensure_local_branch(repo: Path, branch: str) -> None:
    current = git_output(repo, "branch", "--show-current")
    if current == branch:
        return
    if git_ok(repo, "show-ref", "--verify", "--quiet", f"refs/heads/{branch}"):
        run(["git", "switch", branch], cwd=repo)
    else:
        run(["git", "switch", "-c", branch, "--track", f"origin/{branch}"], cwd=repo)


def update_repo(config: RepoConfig, skip_pull: bool) -> RepoUpdateResult:
    repo = WORKSPACE_ROOT / config.path
    result = RepoUpdateResult(repo=config.path)

    if not repo.exists():
        result.status = "missing"
        result.note = "目录不存在"
        return result

    if repo_is_dirty(repo):
        result.status = "skipped-dirty"
        result.note = "存在未提交改动，保护跳过拉取"
        return result

    result.previous_rev = short_rev(repo)

    if skip_pull:
        branch, note = resolve_target_branch(repo, config.preferred_branch)
        result.branch = branch
        result.current_rev = result.previous_rev
        result.status = "skipped-pull"
        result.note = note or "按 --skip-pull 跳过上游拉取"
        return result

    run(["git", "fetch", "origin"], cwd=repo)
    branch, note = resolve_target_branch(repo, config.preferred_branch)
    result.branch = branch
    if branch is None:
        result.status = "skipped-no-branch"
        result.note = "无法确定拉取分支"
        result.current_rev = result.previous_rev
        return result

    ensure_local_branch(repo, branch)
    run(["git", "pull", "--ff-only", "origin", branch], cwd=repo)
    result.current_rev = short_rev(repo)
    result.status = "updated" if result.current_rev != result.previous_rev else "unchanged"
    result.note = note
    return result


def iter_files(root: Path) -> dict[str, Path]:
    files: dict[str, Path] = {}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORED_NAMES for part in path.parts):
            continue
        rel = path.relative_to(root).as_posix()
        files[rel] = path
    return files


def sync_directory(source: Path, target: Path, label: str) -> SyncResult:
    result = SyncResult(source=str(source.relative_to(WORKSPACE_ROOT)), target=str(target.relative_to(AIPALACE_ROOT)))

    if not source.exists():
        result.status = "skipped-missing-source"
        result.note = f"{label} 源目录不存在"
        return result
    if not (source / "SKILL.md").exists():
        result.status = "skipped-missing-skill"
        result.note = f"{label} 源目录缺少 SKILL.md"
        return result
    if not target.exists():
        result.status = "skipped-missing-target"
        result.note = f"{label} 目标目录不存在"
        return result

    source_files = iter_files(source)
    target_files = iter_files(target)

    for rel, src_file in sorted(source_files.items()):
        dst_file = target / rel
        dst_file.parent.mkdir(parents=True, exist_ok=True)
        if rel not in target_files:
            shutil.copy2(src_file, dst_file)
            result.added_files.append(rel)
            continue
        if not filecmp.cmp(src_file, dst_file, shallow=False):
            shutil.copy2(src_file, dst_file)
            result.updated_files.append(rel)

    for rel in sorted(set(target_files) - set(source_files)):
        result.preserved_files.append(rel)

    if result.updated_files or result.added_files:
        result.status = "synced"
        if result.preserved_files:
            result.note = "已覆盖来源明确文件，目标独有文件保留"
        else:
            result.note = "已与上游同步"
    else:
        result.status = "unchanged"
        if result.preserved_files:
            result.note = "来源文件无变化，目标独有文件保留"
        else:
            result.note = "无变化"
    return result


def collect_sync_jobs(
    repo_results: dict[str, RepoUpdateResult],
) -> tuple[list[tuple[Path, Path, str]], list[str]]:
    jobs: list[tuple[Path, Path, str]] = []
    unresolved: list[str] = []

    source_root = WORKSPACE_ROOT / "garveyhu/awesome-skills"
    target_root = AIPALACE_ROOT / "skills/community/garveyhu"
    garveyhu_result = repo_results["garveyhu/awesome-skills"]
    if garveyhu_result.status == "skipped-dirty":
        unresolved.append("skills/community/garveyhu/* -> garveyhu/awesome-skills 有未提交改动，整组保留不动")
    elif garveyhu_result.status == "missing":
        unresolved.append("skills/community/garveyhu/* -> garveyhu/awesome-skills 目录不存在，整组保留不动")
    else:
        for skill_md in sorted(target_root.rglob("SKILL.md")):
            target_dir = skill_md.parent
            rel = target_dir.relative_to(target_root)
            target_key = f"skills/community/garveyhu/{rel.as_posix()}"
            if target_key in EXCLUDED_TARGETS:
                unresolved.append(f"{target_key} -> {EXCLUDED_TARGETS[target_key]}")
                continue
            source_dir = source_root / rel
            if (source_dir / "SKILL.md").exists():
                jobs.append((source_dir, target_dir, f"garveyhu/{rel.as_posix()}"))
            else:
                unresolved.append(
                    f"{target_key} -> 本地上游缺少对应目录，保留不动"
                )

    skills_result = repo_results["skills"]
    if skills_result.status == "skipped-dirty":
        unresolved.append("skills/community/github-skills/grill-* -> skills 仓有未提交改动，保留不动")
    elif skills_result.status == "missing":
        unresolved.append("skills/community/github-skills/grill-* -> skills 仓目录不存在，保留不动")
    else:
        for source_dir, target_dir, label in EXPLICIT_SKILL_MAPS:
            jobs.append((source_dir, target_dir, label))

    superpowers_source_root = WORKSPACE_ROOT / "superpowers/skills"
    superpowers_target_root = AIPALACE_ROOT / "skills/community/superpowers"
    superpowers_result = repo_results["superpowers"]
    if superpowers_result.status == "skipped-dirty":
        unresolved.append("skills/community/superpowers/* -> superpowers 仓有未提交改动，整组保留不动")
    elif superpowers_result.status == "missing":
        unresolved.append("skills/community/superpowers/* -> superpowers 仓目录不存在，整组保留不动")
    else:
        for skill_md in sorted(superpowers_target_root.rglob("SKILL.md")):
            target_dir = skill_md.parent
            rel = target_dir.relative_to(superpowers_target_root)
            target_key = f"skills/community/superpowers/{rel.as_posix()}"
            if target_key in EXCLUDED_TARGETS:
                unresolved.append(f"{target_key} -> {EXCLUDED_TARGETS[target_key]}")
                continue
            source_dir = superpowers_source_root / rel
            if (source_dir / "SKILL.md").exists():
                jobs.append((source_dir, target_dir, f"superpowers/{rel.as_posix()}"))
            else:
                unresolved.append(f"{target_key} -> 本地上游缺少对应目录，保留不动")

    for repo_name in (
        "everything-claude-code",
        "get-shit-done",
        "langchain",
        "skillhub",
    ):
        if repo_results[repo_name].status != "missing":
            unresolved.append(f"{repo_name} -> 当前未发现 AiPalace 中有可明确映射的硬拷贝目录")

    return jobs, unresolved


def aipalace_changed_files() -> list[str]:
    output = git_output(AIPALACE_ROOT, "status", "--short")
    files: list[str] = []
    for line in output.splitlines():
        if not line:
            continue
        files.append(line[3:])
    return files


def commit_aipalace_changes() -> tuple[bool, str]:
    changed = aipalace_changed_files()
    if not changed:
        return False, "AiPalace 无变更，未提交"

    run(["git", "add", "-A"], cwd=AIPALACE_ROOT)
    status_after_add = git_output(AIPALACE_ROOT, "diff", "--cached", "--name-only")
    if not status_after_add:
        return False, "AiPalace 无可提交变更，未提交"

    run(["git", "commit", "-m", COMMIT_MESSAGE], cwd=AIPALACE_ROOT)
    commit_id = short_rev(AIPALACE_ROOT)
    return True, f"已提交 {commit_id}: {COMMIT_MESSAGE}"


def print_report(
    repo_results: list[RepoUpdateResult],
    sync_results: list[SyncResult],
    unresolved: list[str],
    commit_note: str,
) -> None:
    print("# 上游同步结果")
    for item in repo_results:
        branch = item.branch or "-"
        rev = f"{item.previous_rev or '-'} -> {item.current_rev or '-'}"
        note = f"；{item.note}" if item.note else ""
        print(f"- {item.repo}: {item.status}；分支 {branch}；提交 {rev}{note}")

    print("\n# 硬拷贝同步结果")
    for item in sync_results:
        detail = []
        if item.updated_files:
            detail.append(f"覆盖 {len(item.updated_files)}")
        if item.added_files:
            detail.append(f"新增 {len(item.added_files)}")
        if item.preserved_files:
            detail.append(f"保留 {len(item.preserved_files)}")
        detail_text = "，".join(detail) if detail else "无文件变化"
        note = f"；{item.note}" if item.note else ""
        print(f"- {item.target}: {item.status}；{detail_text}{note}")
        for rel in item.updated_files:
            print(f"  updated: {item.target}/{rel}")
        for rel in item.added_files:
            print(f"  added:   {item.target}/{rel}")
        for rel in item.preserved_files:
            print(f"  kept:    {item.target}/{rel}")

    print("\n# 保留不动")
    if unresolved:
        for item in unresolved:
            print(f"- {item}")
    else:
        print("- 无")

    print("\n# 策略")
    print("- 先更新上游仓库；优先拉取 origin/main，不存在时回落到 origin/HEAD 并回报。")
    print("- 仅覆盖来源明确、能映射到本地上游仓库的文件。")
    print("- `skills/community/garveyhu/method/skill-management` 视为 AiPalace 本地迭代版本，固定跳过上游覆盖。")
    print("- 目标目录中仅存在于 AiPalace 的文件一律保留，不自动删除。")
    print(f"- 提交结果：{commit_note}")


def run_main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip-pull", action="store_true", help="仅验证与同步，不执行 git fetch/pull")
    parser.add_argument("--commit", action="store_true", help="若 AiPalace 有变更则自动提交")
    args = parser.parse_args()

    repo_results = [update_repo(config, args.skip_pull) for config in REPOS]
    repo_results_by_name = {item.repo: item for item in repo_results}

    jobs, unresolved = collect_sync_jobs(repo_results_by_name)
    sync_results = [sync_directory(source, target, label) for source, target, label in jobs]

    commit_note = "未启用 --commit"
    if args.commit:
        committed, note = commit_aipalace_changes()
        commit_note = note if committed else note

    print_report(repo_results, sync_results, unresolved, commit_note)
    return 0


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with RUN_LOG.open("a", encoding="utf-8") as run_log, ERR_LOG.open("a", encoding="utf-8") as err_log:
        run_log.write(f"\n=== {started_at} ===\n")
        run_log.flush()
        err_log.write(f"\n=== {started_at} ===\n")
        err_log.flush()

        stdout_tee = TeeStream(sys.stdout, run_log)
        stderr_tee = TeeStream(sys.stderr, err_log)

        try:
            with contextlib.redirect_stdout(stdout_tee), contextlib.redirect_stderr(stderr_tee):
                return run_main()
        except Exception:
            traceback.print_exc()
            return 1


if __name__ == "__main__":
    sys.exit(main())
