from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.agents.router import ask
from app.core.config import get_config
from app.core.db import can_connect_admin_server, get_admin_engine
from app.etl.apply_schema import apply_default_schema
from app.etl.load_mysql import load_mysql_from_parsed_json
from app.etl.tankeng_pdf_parser import export_parsed_artifacts
from app.rag.knowledge_loader import load_knowledge


MYSQL_CONTAINER_NAME = "reservoir-mysql"
MYSQL_IMAGE = "mysql:8"
MYSQL_ROOT_PASSWORD = "password"
MYSQL_DATABASE = "tk_reservoir_ops"
MYSQL_PORT = "3306"
DOCKER_WAIT_SECONDS = 90
MYSQL_WAIT_SECONDS = 90
EXIT_COMMANDS = {"exit", "quit", "退出", "q"}


class InitializationError(RuntimeError):
    pass


def _run_command(args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, capture_output=True, text=True, check=check)


def _run_powershell(command: str) -> subprocess.CompletedProcess[str]:
    return _run_command(["powershell", "-Command", command])


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    result = _run_command(["docker", "version"])
    return result.returncode == 0


def _ensure_docker_running() -> str:
    if _docker_available():
        return "Docker is ready."

    if shutil.which("docker") is None:
        raise InitializationError("Docker CLI is not installed or not in PATH.")

    if sys.platform == "win32":
        _run_powershell("Start-Service -Name com.docker.service")
        docker_desktop = Path(r"C:\Program Files\Docker\Docker\Docker Desktop.exe")
        if docker_desktop.exists():
            _run_powershell(f"Start-Process -FilePath '{docker_desktop}'")

    deadline = time.time() + DOCKER_WAIT_SECONDS
    while time.time() < deadline:
        if _docker_available():
            return "Docker started."
        time.sleep(3)

    raise InitializationError("Docker did not become ready in time.")


def _inspect_container_running() -> str | None:
    result = _run_command(
        ["docker", "inspect", "-f", "{{.State.Running}}", MYSQL_CONTAINER_NAME]
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip().lower()


def _ensure_mysql_container_running() -> str:
    running = _inspect_container_running()
    if running == "true":
        return "MySQL container is already running."

    if running == "false":
        _run_command(["docker", "start", MYSQL_CONTAINER_NAME], check=True)
        return "MySQL container started."

    _run_command(
        [
            "docker",
            "run",
            "-d",
            "--name",
            MYSQL_CONTAINER_NAME,
            "-e",
            f"MYSQL_ROOT_PASSWORD={MYSQL_ROOT_PASSWORD}",
            "-e",
            f"MYSQL_DATABASE={MYSQL_DATABASE}",
            "-p",
            f"{MYSQL_PORT}:3306",
            MYSQL_IMAGE,
        ],
        check=True,
    )
    return "MySQL container created and started."


def _wait_for_mysql_server() -> str:
    deadline = time.time() + MYSQL_WAIT_SECONDS
    while time.time() < deadline:
        if can_connect_admin_server():
            return "MySQL server is ready."
        time.sleep(2)
    raise InitializationError("MySQL server did not become ready in time.")


def _ensure_parsed_artifacts() -> str:
    config = get_config()
    if config.parsed_json_path.exists():
        return "Parsed artifacts already exist."
    export_parsed_artifacts()
    return "Parsed artifacts generated."


def _resolve_lancedb_path() -> Path:
    config = get_config()
    path = Path(config.lancedb_uri)
    if not path.is_absolute():
        path = config.project_root / path
    return path


def _knowledge_ready() -> bool:
    path = _resolve_lancedb_path()
    return path.exists() and any(path.iterdir())


def _mysql_seed_data_ready() -> bool:
    try:
        with get_admin_engine().connect() as conn:
            basic_info_count = conn.execute(
                text("SELECT COUNT(*) FROM reservoir_basic_info")
            ).scalar()
            monthly_count = conn.execute(
                text("SELECT COUNT(*) FROM reservoir_monthly_operation_plan")
            ).scalar()
        return bool(basic_info_count) and bool(monthly_count)
    except SQLAlchemyError:
        return False


def initialize_runtime(force_reload_knowledge: bool = False) -> list[str]:
    messages: list[str] = []

    messages.append(_ensure_parsed_artifacts())

    if not can_connect_admin_server():
        messages.append(_ensure_docker_running())
        messages.append(_ensure_mysql_container_running())
        messages.append(_wait_for_mysql_server())
    else:
        messages.append("MySQL server is already reachable.")

    apply_default_schema()
    messages.append("Schema ensured.")

    if _mysql_seed_data_ready():
        messages.append("MySQL seed data already exists.")
    else:
        load_mysql_from_parsed_json()
        messages.append("MySQL seed data loaded.")

    knowledge_ready = _knowledge_ready()
    if force_reload_knowledge or not knowledge_ready:
        load_knowledge(recreate=force_reload_knowledge or not knowledge_ready)
        messages.append("Knowledge base loaded.")
    else:
        messages.append("Knowledge base already exists.")

    return messages


def run_interactive_qa() -> None:
    print("进入连续问答模式。输入问题后回车，输入 exit/quit/退出 结束。")
    while True:
        try:
            question = input("问> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return

        if not question:
            continue
        if question.lower() in EXIT_COMMANDS or question in EXIT_COMMANDS:
            return

        print(ask(question))
