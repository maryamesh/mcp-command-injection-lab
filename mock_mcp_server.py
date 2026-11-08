"""Mock MCP server for the command-injection lab.

This is not an MCP protocol implementation. It exposes one simulated tool.
"""

from __future__ import annotations

from simulated_shell import SimulatedShell


class MockMCPServer:
    """Intentionally vulnerable system_status tool backed by the simulated shell."""

    def __init__(self, shell: SimulatedShell | None = None) -> None:
        self.shell = SimulatedShell() if shell is None else shell

    def system_status(self, command: str) -> str:
        """Return simulated output for the status tool.

        The command argument is interpolated without sanitizing shell separators.
        """
        if not isinstance(command, str):
            command = "" if command is None else str(command)
        # The argument is passed through unchanged, including shell separators.
        return self.shell.execute(command)

    def reset(self) -> None:
        self.shell.reset()
