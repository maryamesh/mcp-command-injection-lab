"""Deterministic IT support assistant.

The agent does not call a language model. It keeps a transcript and only handles
the accepted diagnostic questions and simulated system_status tool calls.
"""

from __future__ import annotations

import re

from mock_mcp_server import MockMCPServer

GREETING = (
    "Hello, I am the IT Support Assistant for IT-SERVER-01. "
    "I can request system diagnostics through the system_status tool."
)

FALLBACK = (
    "I'm sorry, but I can't help you with that request. "
    "I can only assist with the available system diagnostics functionality."
)

TOOL_USAGE_HINT = (
    "The **system_status** tool takes one argument named `command`. "
    "Use this exact format:\n\n"
    "`system_status(command: <command>)`\n\n"
    "For example, to request the hostname:\n\n"
    "`system_status(command: hostname)`"
)

_TOOL_EXPRESSION = re.compile(
    r"(?is)\bsystem_status\s*\(\s*command\s*[:=]\s*(.*?)\s*\)"
)
_OTHER_COMMAND_SYNTAX = re.compile(r"(?is)\b(?:command|cmd)\s*[:=]")
_TOOL_USAGE_REQUEST = re.compile(
    r"(?ix)("
    r"\b(?:exact\s+)?(?:tool\s+)?(?:syntax|format|argument|arguments|parameter|parameters)\b|"
    r"\b(?:how|what)\s+(?:do|should|can|would)\s+I\s+"
    r"(?:call|invoke|run|use|write)\b|"
    r"\b(?:show|give)\s+me\s+(?:an?\s+)?(?:example|tool\s+call)\b|"
    r"\bhow\s+(?:does|to)\s+(?:the\s+)?system_status\b"
    r")"
)
_HOSTNAME_REQUEST = re.compile(
    r"(?i)("
    r"\bhost\s*name\b|"
    r"\bhostname\b|"
    r"\bserver name\b|"
    r"\bname of (?:the |this )?(?:server|machine|host)\b|"
    r"\bmachine (?:is )?called\b|"
    r"\b(?:server|machine|host) called\b|"
    r"\bidentify the server\b|"
    r"\bwhich machine\b|"
    r"\bwhat is this machine\b"
    r")"
)
_OS_REQUEST = re.compile(
    r"(?i)("
    r"\boperating system\b|"
    r"\bos\b|"
    r"\blinux version\b|"
    r"\bwhich linux\b|"
    r"\bkernel\b|"
    r"\bsystem information\b"
    r")"
)
_STATUS_REQUEST = re.compile(
    r"(?i)("
    r"\bsystem status\b|"
    r"\bserver status\b|"
    r"\brunning normally\b|"
    r"\boperational\b|"
    r"\bworking correctly\b|"
    r"\beverything working\b|"
    r"\bcheck the system\b|"
    r"\bsystem health\b|"
    r"\bserver health\b"
    r")"
)


def _command_from_tool_expression(text: str) -> str | None:
    match = _TOOL_EXPRESSION.search(text)
    if not match:
        return None
    command = match.group(1).strip()
    if len(command) >= 2 and command[0] == command[-1] and command[0] in ("'", '"'):
        command = command[1:-1].strip()
    return command


def _natural_language_command(text: str) -> str | None:
    if _HOSTNAME_REQUEST.search(text):
        return "hostname"
    if _OS_REQUEST.search(text):
        return "uname -a"
    if _STATUS_REQUEST.search(text):
        return "status"
    return None


class MockAgent:
    def __init__(self) -> None:
        self.mcp = MockMCPServer()
        self.history: list[dict[str, str]] = []
        self._add_greeting()

    def reset(self) -> None:
        self.mcp.reset()
        self.history = []
        self._add_greeting()

    def chat(self, message: str) -> dict[str, str]:
        self.history.append({"role": "user", "kind": "text", "content": message})
        explicit_command = _command_from_tool_expression(message.strip())
        if explicit_command is None and _TOOL_USAGE_REQUEST.search(message):
            reply = {
                "role": "assistant",
                "kind": "text",
                "content": TOOL_USAGE_HINT,
            }
        else:
            command = self.extract_command(message)
            if command is not None:
                output = self.mcp.system_status(command)
                reply = {
                    "role": "assistant",
                    "kind": "tool",
                    "content": "",
                    "command": command,
                    "output": output,
                }
            else:
                reply = {
                    "role": "assistant",
                    "kind": "text",
                    "content": FALLBACK,
                }
        self.history.append(reply)
        return reply

    def extract_command(self, message: str) -> str | None:
        """Return a supported command argument, or None when the request is refused."""
        text = message.strip()
        if not text:
            return None

        tool_expression = _command_from_tool_expression(text)
        if tool_expression is not None:
            return tool_expression
        if _OTHER_COMMAND_SYNTAX.search(text):
            return None

        return _natural_language_command(text)

    def _add_greeting(self) -> None:
        self.history.append({"role": "assistant", "kind": "text", "content": GREETING})
