from __future__ import annotations

import os
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

import click

from .git import CommitLog

BUMP_VERSION = (("bump", ":bookmark:"),)  # 🔖 :bookmark:

BUMP_REGEX = (
    r"(?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)"
    r"(\.(?P<prekind>a|alpha|b|beta|d|dev|rc)(?P<pre>\d+))?"
    r"(\.(?P<postkind>post)(?P<post>\d+))?"
)

BUMP_VERSION_CONFIG = r"""[bumpversion]
current_version = {version}
commit = True
tag = False
parse = ^
    (?P<major>\d+)\.(?P<minor>\d+)\.(?P<patch>\d+)
    (\.(?P<prekind>a|alpha|b|beta|d|dev|rc)(?P<pre>\d+))?
    (\.(?P<postkind>post)(?P<post>\d+))?
serialize =
    {{major}}.{{minor}}.{{patch}}.{{prekind}}{{pre}}.{{postkind}}{{post}}
    {{major}}.{{minor}}.{{patch}}.{{prekind}}{{pre}}
    {{major}}.{{minor}}.{{patch}}.{{postkind}}{{post}}
    {{major}}.{{minor}}.{{patch}}
message = :bookmark: Bump up to version {{current_version}} -> {{new_version}}.

[bumpversion:part:prekind]
optional_value = _
values =
    _
    dev
    a
    b
    rc

[bumpversion:part:postkind]
optional_value = _
values =
    _
    post

[bumpversion:file:{file}]

[bumpversion:file:{changelog}]
search = ## Latest Changes
replace = ## {{new_version}}
"""

cli_vs: click.Command


def generate_group_commit_log() -> Dict[str, List[CommitLog]]:
    """Generate Group of the Commit Logs"""
    from .git import get_commit_logs

    group_logs: Dict[str, List[CommitLog]] = defaultdict(list)
    for log in get_commit_logs():
        group_logs[log.msg.mtype].append(log)
    return {
        k: sorted(v, key=lambda x: x.date, reverse=True)
        for k, v in group_logs.items()
    }


# TODO: add new style of changelog file
def writer_changelog(file: str):
    """Write Commit logs to the changelog file."""
    group_logs: Dict[str, List[CommitLog]] = generate_group_commit_log()

    with Path(file).open(encoding="utf-8") as f_changes:
        changes = f_changes.read().splitlines()

    writer = Path(file).open(mode="w", encoding="utf-8", newline="")
    skip_line: bool = True
    written: bool = False
    for line in changes:
        if line.startswith("## Latest Changes"):
            skip_line = False

        if re.match(rf"## {BUMP_REGEX}", line):
            if not written:
                writer.write(f"## Latest Changes{os.linesep}{os.linesep}")
                written = True
            skip_line = True

        if skip_line:
            writer.write(line + os.linesep)
        elif written:
            continue
        else:
            from .git import COMMIT_PREFIX_TYPE

            linesep = os.linesep
            if any(cpt[0] in group_logs for cpt in COMMIT_PREFIX_TYPE):
                linesep = f"{os.linesep}{os.linesep}"

            writer.write(f"## Latest Changes{linesep}")

            for cpt in COMMIT_PREFIX_TYPE:
                if cpt[0] in group_logs:
                    writer.write(f"### {cpt[0]}{os.linesep}{os.linesep}")
                    for log in group_logs[cpt[0]]:
                        writer.write(
                            f"- {log.msg.content} (_{log.date:%Y-%m-%d}_)"
                            f"{os.linesep}"
                        )
                    writer.write(os.linesep)
            written = True
    writer.close()


def bump2version(
    action: str,
    file: str,
    changelog_file: str,
    ignore_changelog: bool = False,
    dry_run: bool = False,
):
    from .git import merge2latest_commit

    with Path(".bumpversion.cfg").open(mode="w", encoding="utf-8") as f_bump:
        f_bump.write(
            BUMP_VERSION_CONFIG.format(
                file=file,
                version=current_version(file),
                changelog=changelog_file,
            )
        )
    if not ignore_changelog:
        writer_changelog(file=changelog_file)
    subprocess.run(["git", "add", "-A"])
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            "build: add bump2version config file",
            "--no-verify",
        ]
    )
    subprocess.run(
        [
            "bump2version",
            action,
            "--commit-args=--no-verify",
        ]
        + (["--list", "--dry-run"] if dry_run else [])
    )
    writer_changelog(file=changelog_file)
    Path(".bumpversion.cfg").unlink(missing_ok=False)
    merge2latest_commit(no_verify=True)
    subprocess.run(
        [
            "git",
            "reset",
            "--soft",
            "HEAD~1",
        ],
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )
    with Path(".git/COMMIT_EDITMSG").open(encoding="utf-8") as f_msg:
        raw_msg = f_msg.read().splitlines()
    subprocess.run(
        [
            "git",
            "commit",
            "--amend",
            "-m",
            raw_msg[0],
            "--no-verify",
        ],
        stderr=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
    )
    return 0


def current_version(file: str) -> str:
    with Path(file).open(encoding="utf-8") as f:
        if search := re.search(BUMP_REGEX, f.read()):
            return search[0]
    raise NotImplementedError(f"{file} does not implement version value.")


def load_project() -> Dict[str, Any]:
    from .utils import load_pyproject

    return load_pyproject().get("project", {})


def load_config() -> Dict[str, Any]:
    from .utils import load_pyproject

    return load_pyproject().get("tool", {}).get("utils", {}).get("version", {})


@click.group(name="vs")
def cli_vs():
    """Version commands"""
    pass


@cli_vs.command()
def conf():
    """Return Configuration for Bump version"""
    sys.exit(load_config())


@cli_vs.command()
@click.option("-f", "--file", type=click.Path(exists=True))
def changelog(file: Optional[str]):
    """Make Changelogs file"""
    if not file:
        file = load_config().get("changelog", None) or "CHANGELOG.md"
    writer_changelog(file)
    sys.exit(0)


@cli_vs.command()
@click.option("-f", "--file", type=click.Path(exists=True))
def current(file: str):
    """Return Current Version"""
    if not file:
        file = load_config().get("version", None) or (
            f"./{load_project().get('name', 'unknown')}/__about__.py"
        )
    sys.exit(current_version(file))


@cli_vs.command()
@click.argument("action", type=click.STRING)
@click.option("-f", "--file", type=click.Path(exists=True))
@click.option("-c", "--changelog-file", type=click.Path(exists=True))
@click.option("--ignore-changelog", is_flag=True)
@click.option("--dry-run", is_flag=True)
def bump(
    action: str,
    file: Optional[str],
    changelog_file: Optional[str],
    ignore_changelog: bool,
    dry_run: bool,
):
    """Bump Version"""
    if not file:
        file = load_config().get("version", None) or (
            f"./{load_project().get('name', 'unknown')}/__about__.py"
        )
    if not changelog_file:
        changelog_file = load_config().get("changelog", None) or "CHANGELOG.md"
    sys.exit(
        bump2version(action, file, changelog_file, ignore_changelog, dry_run)
    )


if __name__ == "__main__":
    cli_vs.main()
