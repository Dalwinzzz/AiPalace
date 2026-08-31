#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent))
from paths import resolve_biz_rules_dir, resolve_project_sql_dir


IGNORE_LINE = "/sql/biz-rules/"


def is_within(path: Path, root: Path) -> bool:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=False))
    except ValueError:
        return False
    return True


def symlink_escapes(path: Path, root: Path) -> bool:
    return path.is_symlink()


def disabled(reason: str, project_dir: Path, **extra: Any) -> dict[str, Any]:
    result = {
        "status": "disabled",
        "reason": reason,
        "project_dir": str(project_dir),
        "ignore_status": "skipped",
        "tracked": False,
        "untrack_status": "skipped",
    }
    result.update(extra)
    return result


def check_symlink_escapes(project_dir: Path) -> dict[str, Any] | None:
    gitignore = project_dir / ".gitignore"
    sql_dir = resolve_project_sql_dir(project_dir)
    biz_dir = resolve_biz_rules_dir(project_dir)

    if symlink_escapes(gitignore, project_dir):
        return disabled(
            "gitignore_symlink_escape",
            project_dir,
            gitignore=str(gitignore),
            target=str(gitignore.resolve(strict=False)),
        )
    if symlink_escapes(sql_dir, project_dir):
        return disabled(
            "sql_dir_symlink_escape",
            project_dir,
            sql_dir=str(sql_dir),
            target=str(sql_dir.resolve(strict=False)),
        )
    if symlink_escapes(biz_dir, project_dir):
        return disabled(
            "biz_rules_dir_symlink_escape",
            project_dir,
            biz_rules_dir=str(biz_dir),
            target=str(biz_dir.resolve(strict=False)),
        )
    return None


def ensure_ignore(project_dir: Path) -> str:
    gitignore = project_dir / ".gitignore"
    existing = gitignore.read_text(encoding="utf-8") if gitignore.exists() else ""
    if IGNORE_LINE in existing.splitlines():
        return "present"

    suffix = "" if not existing or existing.endswith("\n") else "\n"
    gitignore.write_text(existing + suffix + IGNORE_LINE + "\n", encoding="utf-8")
    return "updated"


def git_result(project_dir: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git"] + args,
        cwd=project_dir,
        capture_output=True,
        text=True,
    )


def is_git_repo(project_dir: Path) -> bool:
    result = git_result(project_dir, ["rev-parse", "--is-inside-work-tree"])
    return result.returncode == 0 and result.stdout.strip() == "true"


def tracked_files(project_dir: Path) -> list[str]:
    result = git_result(project_dir, ["ls-files", "--", "sql/biz-rules"])
    if result.returncode != 0:
        return []
    return [line for line in result.stdout.splitlines() if line.strip()]


def untrack(project_dir: Path) -> tuple[str, str]:
    result = git_result(project_dir, ["rm", "--cached", "-r", "--", "sql/biz-rules"])
    if result.returncode != 0:
        return "failed", result.stderr.strip()
    return "untracked", result.stdout.strip()


def guard(project_dir: Path, args: argparse.Namespace) -> dict[str, Any]:
    if not project_dir.exists():
        return disabled("project_dir_missing", project_dir)

    safety_error = check_symlink_escapes(project_dir)
    if safety_error:
        return safety_error

    ignore_status = "skipped"
    if args.ensure_ignore:
        ignore_status = ensure_ignore(project_dir)

    git_repo = is_git_repo(project_dir)
    files = tracked_files(project_dir) if git_repo else []
    tracked = bool(files)
    untrack_status = "not_requested"
    untrack_output = ""

    if args.untrack:
        if not git_repo:
            untrack_status = "not_git_repo"
        elif not tracked:
            untrack_status = "nothing_to_untrack"
        else:
            untrack_status, untrack_output = untrack(project_dir)

    tracked_after = bool(tracked_files(project_dir)) if git_repo else False
    result: dict[str, Any] = {
        "status": "ok",
        "project_dir": str(project_dir),
        "ignore_status": ignore_status,
        "git_status": "ok" if git_repo else "not_git_repo",
        "tracked": tracked,
        "tracked_files": files,
        "tracked_after": tracked_after,
        "untrack_status": untrack_status,
    }
    if untrack_output:
        result["untrack_output"] = untrack_output
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply Git guard for project business rules")
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--ensure-ignore", action="store_true")
    parser.add_argument("--untrack", action="store_true")
    args = parser.parse_args()

    project_dir = args.project_dir.expanduser().resolve(strict=False)
    print(json.dumps(guard(project_dir, args), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
