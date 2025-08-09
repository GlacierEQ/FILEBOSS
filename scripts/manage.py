#!/usr/bin/env python3
"""Project Management Utility

A single entry-point script that consolidates the typical development-and-ops
workflow for Mega CaseBuilder 3000.

Included commands
-----------------
build           ‑ Build *sdist* & *wheel* into ./dist
install         ‑ Install the project (editable) plus deps (use --dev for extras)
run             ‑ Start the FastAPI dev-server (delegates to scripts/start.py)
test            ‑ Run pytest (optionally --coverage)
lint            ‑ Static analysis (black --check, isort --check, flake8, mypy)
format          ‑ Auto-format (isort + black)
makemigration   ‑ Create an Alembic revision (wraps scripts/create_migration.py)
migrate         ‑ Upgrade / downgrade DB schema (alembic upgrade/downgrade)
db-reset        ‑ Drop database then re-apply latest migration
shell           ‑ Launch IPython shell with project context imported
docker          ‑ docker build / docker run helpers
docs            ‑ Build documentation (mkdocs > sphinx fallback)
"""
from __future__ import annotations

import argparse
import importlib
import logging
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import List

# ---------------------------------------------------------------------------
# Paths / constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
REQ_FILE = PROJECT_ROOT / "requirements.txt"
TESTS_DIR = PROJECT_ROOT / "tests"
ALEMBIC_INI = PROJECT_ROOT / "alembic.ini"
MKDOCS_FILE = PROJECT_ROOT / "mkdocs.yml"
DOCS_DIR = PROJECT_ROOT / "docs"

logging.basicConfig(
    level=os.environ.get("LOGLEVEL", "INFO"),
    format="%(asctime)s | %(levelname)8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("manage")


# ---------------------------------------------------------------------------
# Helper: run external commands transparently
# ---------------------------------------------------------------------------

def _run(cmd: List[str] | str, check: bool = True, **kw) -> None:  # noqa: ANN001
    """Run *cmd* printing it beforehand."""
    display = cmd if isinstance(cmd, str) else " ".join(cmd)
    logger.info("$ %s", display)
    completed = subprocess.run(cmd, text=True, shell=isinstance(cmd, str), **kw)
    if check and completed.returncode != 0:
        logger.error("Command failed (exit-code %s)", completed.returncode)
        sys.exit(completed.returncode)


# ---------------------------------------------------------------------------
# Core build / test / run / etc.
# ---------------------------------------------------------------------------

def cmd_build(_: argparse.Namespace) -> None:
    try:
        import build  # noqa: F401
    except ImportError:
        logger.warning("Installing missing 'build' package …")
        _run([sys.executable, "-m", "pip", "install", "build"])
    _run([sys.executable, "-m", "build", "--sdist", "--wheel"])


def cmd_test(args: argparse.Namespace) -> None:  # noqa: ANN001
    cmd = [sys.executable, "-m", "pytest", str(TESTS_DIR)]
    if args.coverage:
        cmd += ["--cov", "--cov-report", "term-missing"]
    _run(cmd)


def cmd_run(_: argparse.Namespace) -> None:
    start = SCRIPTS_DIR / "start.py"
    if not start.exists():
        logger.error("%s not found – cannot run server", start)
        sys.exit(1)
    _run([sys.executable, str(start)])


def cmd_install(args: argparse.Namespace) -> None:  # noqa: ANN001
    _run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
    pkg = f"{PROJECT_ROOT}[dev]" if args.dev else str(PROJECT_ROOT)
    _run([sys.executable, "-m", "pip", "install", "--editable", pkg])
    if REQ_FILE.exists():
        _run([sys.executable, "-m", "pip", "install", "-r", str(REQ_FILE)])


def cmd_lint(_: argparse.Namespace) -> None:
    _run([sys.executable, "-m", "black", "--check", "."])
    _run([sys.executable, "-m", "isort", "--check-only", "."])
    _run([sys.executable, "-m", "flake8", "."])
    _run([sys.executable, "-m", "mypy", "."])


def cmd_format(_: argparse.Namespace) -> None:
    _run([sys.executable, "-m", "isort", "."])
    _run([sys.executable, "-m", "black", "."])


# ---------------------------------------------------------------------------
# Alembic helpers (makemigration / migrate / db-reset)
# ---------------------------------------------------------------------------


def _alembic_config():  # noqa: D401
    from alembic.config import Config  # imported lazily

    if not ALEMBIC_INI.exists():
        logger.error("alembic.ini not found at project root – DB ops unavailable")
        sys.exit(1)
    return Config(str(ALEMBIC_INI))


def cmd_makemigration(args: argparse.Namespace) -> None:  # noqa: ANN001
    script = SCRIPTS_DIR / "create_migration.py"
    if not script.exists():
        logger.error("%s not found", script)
        sys.exit(1)
    cmd = [sys.executable, str(script), "-m", args.message]
    if args.empty:
        cmd.append("--no-autogenerate")
    _run(cmd)


def cmd_migrate(args: argparse.Namespace) -> None:  # noqa: ANN001
    from alembic import command

    cfg = _alembic_config()
    direction = "upgrade" if args.upgrade else "downgrade"
    target = args.revision or ("head" if direction == "upgrade" else "-1")
    if args.steps is not None:
        step_prefix = "+" if direction == "upgrade" else "-"
        target = f"{step_prefix}{args.steps}"
    logger.info("Running alembic %s %s", direction, target)
    getattr(command, direction)(cfg, target)


def cmd_db_reset(_: argparse.Namespace) -> None:
    from alembic import command

    cfg = _alembic_config()
    logger.info("Resetting database … (downgrade base -> upgrade head)")
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")


# ---------------------------------------------------------------------------
# Shell – IPython with imports
# ---------------------------------------------------------------------------


def cmd_shell(_: argparse.Namespace) -> None:
    try:
        from IPython import start_ipython  # pylint: disable=import-error
    except ImportError:
        logger.warning("IPython not installed – installing …")
        _run([sys.executable, "-m", "pip", "install", "ipython"])
        from IPython import start_ipython  # type: ignore

    banner = "📝  Interactive shell (project context pre-loaded)"
    context_code = (
        "from casebuilder.api.app import app\n"
        "from casebuilder.core.config import settings\n"
        "from casebuilder.db.session import async_session_factory as db_session\n"
        "print('Variables: app, settings, db_session')\n"
    )
    start_ipython(argv=["--no-banner"], user_ns={})
    # When IPython exits, control returns here.


# ---------------------------------------------------------------------------
# Docker helpers
# ---------------------------------------------------------------------------


def cmd_docker(args: argparse.Namespace) -> None:  # noqa: ANN001
    if args.subcommand == "build":
        tag = args.tag or "megacasebuilder"
        _run(["docker", "build", "-t", tag, "."])
    elif args.subcommand == "run":
        tag = args.tag or "megacasebuilder"
        port = args.port or "8000"
        _run(["docker", "run", "-p", f"{port}:8000", tag])
    else:
        logger.error("Unknown docker subcommand")
        sys.exit(1)


# ---------------------------------------------------------------------------
# Docs helpers
# ---------------------------------------------------------------------------


def cmd_docs(_: argparse.Namespace) -> None:
    if MKDOCS_FILE.exists():
        _run(["mkdocs", "build", "--clean"])
        logger.info("MkDocs site built under ./site")
    elif (DOCS_DIR / "conf.py").exists():
        build_dir = DOCS_DIR / "_build" / "html"
        _run(["sphinx-build", "-b", "html", str(DOCS_DIR), str(build_dir)])
        logger.info("Sphinx docs built under %s", build_dir)
    else:
        logger.error("No documentation config (mkdocs.yml or docs/conf.py) found")
        sys.exit(1)


# ---------------------------------------------------------------------------
# CLI PARSER
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:  # noqa: D401
    p = argparse.ArgumentParser(prog="manage", description="Project management commands")
    sub = p.add_subparsers(dest="command", required=True)

    # Core tasks
    sub_build = sub.add_parser("build", help="Package into ./dist (sdist & wheel)")
    sub_build.set_defaults(func=cmd_build)

    sub_test = sub.add_parser("test", help="Run pytest suite")
    sub_test.add_argument("--coverage", action="store_true", help="Coverage analysis")
    sub_test.set_defaults(func=cmd_test)

    sub_run = sub.add_parser("run", help="Run development server")
    sub_run.set_defaults(func=cmd_run)

    sub_install = sub.add_parser("install", help="pip install -e . (plus deps)")
    sub_install.add_argument("--dev", action="store_true", help="Include dev extras")
    sub_install.set_defaults(func=cmd_install)

    sub_lint = sub.add_parser("lint", help="Static analysis & style checks")
    sub_lint.set_defaults(func=cmd_lint)

    sub_fmt = sub.add_parser("format", help="Auto-format codebase (black + isort)")
    sub_fmt.set_defaults(func=cmd_format)

    # --- database / migrations ---
    sub_mkmig = sub.add_parser("makemigration", help="Create Alembic revision")
    sub_mkmig.add_argument("-m", "--message", required=True, help="Commit message")
    sub_mkmig.add_argument("--empty", action="store_true", help="Create empty revision")
    sub_mkmig.set_defaults(func=cmd_makemigration)

    sub_migrate = sub.add_parser("migrate", help="Upgrade / downgrade database")
    dir_group = sub_migrate.add_mutually_exclusive_group()
    dir_group.add_argument("--upgrade", action="store_true", default=True, help="Upgrade (default)")
    dir_group.add_argument("--downgrade", action="store_true", help="Downgrade")
    sub_migrate.add_argument("--revision", help="Target revision id (optional)")
    sub_migrate.add_argument("--steps", type=int, help="Relative +/- steps from current")
    sub_migrate.set_defaults(func=cmd_migrate)

    sub_reset = sub.add_parser("db-reset", help="Drop database & re-apply head migration")
    sub_reset.set_defaults(func=cmd_db_reset)

    # shell
    sub_shell = sub.add_parser("shell", help="Launch IPython with project context")
    sub_shell.set_defaults(func=cmd_shell)

    # docker
    sub_docker = sub.add_parser("docker", help="Docker helpers")
    docker_sub = sub_docker.add_subparsers(dest="subcommand", required=True)
    d_build = docker_sub.add_parser("build", help="docker build .")
    d_build.add_argument("--tag", help="Docker image tag (default megacasebuilder)")
    d_build.set_defaults(func=cmd_docker)

    d_run = docker_sub.add_parser("run", help="docker run -p 8000:8000 image")
    d_run.add_argument("--tag", help="Docker image tag (default megacasebuilder)")
    d_run.add_argument("--port", help="Host port to map to 8000", type=str)
    d_run.set_defaults(func=cmd_docker)

    # docs
    sub_docs = sub.add_parser("docs", help="Build project documentation")
    sub_docs.set_defaults(func=cmd_docs)

    return p


# ---------------------------------------------------------------------------
# Entry-point
# ---------------------------------------------------------------------------

def main() -> None:  # noqa: D401
    parser = build_parser()
    ns = parser.parse_args()
    ns.func(ns)


if __name__ == "__main__":
    if platform.system() == "Windows":
        try:
            import colorama  # type: ignore
            colorama.just_fix_windows_console()
        except ImportError:
            pass
    main()
