import subprocess

from project_health.models import CommandResult


def run_command(command: list[str], timeout: int = 5) -> CommandResult:
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return CommandResult(
            command=command,
            available=False,
            output="",
            error=str(error),
        )

    output = completed.stdout.strip() or completed.stderr.strip()
    error = None if completed.returncode == 0 else completed.stderr.strip()

    return CommandResult(
        command=command,
        available=completed.returncode == 0,
        output=output,
        error=error,
    )
