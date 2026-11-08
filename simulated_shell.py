"""In-memory shell for the command-injection lab.

Command execution never calls the operating system and never reads the host
filesystem. All paths resolve against a fixed simulated tree.
"""

from __future__ import annotations

_RECOVERY_RECORD = "736563726574207661756c742070617373776f72642069732034353637"


def vault_password() -> str:
    """Decode the simulated recovery record into the vault password."""
    return bytes.fromhex(_RECOVERY_RECORD).decode("ascii")


class FileNode:
    def __init__(self, content: str) -> None:
        self.content = content


class DirNode:
    def __init__(self, children: dict[str, FileNode | DirNode] | None = None) -> None:
        self.children = {} if children is None else children


class SimulatedShell:
    """Small deterministic shell grammar over a fixed virtual filesystem."""

    USERNAME = "student"
    HOSTNAME = "IT-SERVER-01"
    HOME = "/"
    UNAME_A = "Linux IT-SERVER-01 6.8.0-45-generic #45-Ubuntu SMP x86_64 GNU/Linux"

    def __init__(self) -> None:
        self.root = self._build_filesystem()
        self.cwd = self.HOME

    def reset(self) -> None:
        self.cwd = self.HOME

    def execute(self, cmdline: str) -> str:
        outputs: list[str] = []
        last_code = 0
        for operator, raw in self._split_chain(cmdline):
            if operator == "|":
                outputs.append("bash: syntax error near unexpected token '|'")
                last_code = 2
                continue
            if operator == "&&" and last_code != 0:
                continue
            if operator == "||" and last_code == 0:
                continue
            command = raw.strip()
            if command == "":
                if operator in ("", ";", "&"):
                    last_code = 0
                continue
            text, last_code = self._run_simple(command)
            if text:
                outputs.append(text)
        return "\n".join(outputs)

    def _build_filesystem(self) -> DirNode:
        return DirNode(
            children={
                "app": DirNode(
                    children={
                        "README.md": FileNode(
                            "IT Support Assistant\n"
                            "====================\n"
                            "Runtime configuration is stored in ./config.\n"
                            "Operational logs are stored in ./logs.\n"
                            "Legacy recovery records are managed by the backup service."
                        ),
                        "config": DirNode(
                            children={
                                "assistant.ini": FileNode(
                                    "[assistant]\n"
                                    "hostname=IT-SERVER-01\n"
                                    "diagnostic_tool=system_status\n\n"
                                    "[backup]\n"
                                    "root=/var/backups/it-support\n"
                                    "retention=30d"
                                ),
                                "logging.ini": FileNode(
                                    "[logging]\n"
                                    "level=INFO\n"
                                    "path=/app/logs/application.log"
                                ),
                            }
                        ),
                        "logs": DirNode(
                            children={
                                "application.log": FileNode(
                                    "2026-11-08T08:00:00Z INFO assistant started\n"
                                    "2026-11-08T08:00:01Z INFO system_status registered\n"
                                    "2026-11-08T08:00:02Z INFO backup configuration loaded"
                                ),
                                "diagnostics.log": FileNode(
                                    "hostname: IT-SERVER-01\n"
                                    "status: operational\n"
                                    "last_check: 2026-11-08T12:55:00Z"
                                ),
                            }
                        ),
                        ".cache": DirNode(
                            children={
                                "session.dat": FileNode(
                                    "cache_version=2\n"
                                    "last_session=diagnostic-8841\n"
                                    "result=healthy"
                                )
                            }
                        ),
                    }
                ),
                "var": DirNode(
                    children={
                        "log": DirNode(
                            children={
                                "maintenance.log": FileNode(
                                    "2026-10-15 backup rotation completed\n"
                                    "2026-10-16 old recovery material moved to archive\n"
                                    "2026-11-01 integrity check passed"
                                )
                            }
                        ),
                        "backups": DirNode(
                            children={
                                "it-support": DirNode(
                                    children={
                                        "README": FileNode(
                                            "IT support backup area.\n"
                                            "Current diagnostic snapshots are stored here.\n"
                                            "Older recovery records are retained in a hidden archive."
                                        ),
                                        "config.old": FileNode(
                                            "hostname=IT-SERVER-OLD\n"
                                            "diagnostic_tool=legacy_status\n"
                                            "migration_complete=true"
                                        ),
                                        "diagnostic-2026-10.dat": FileNode(
                                            "host=IT-SERVER-01\n"
                                            "state=operational\n"
                                            "checksum=9f2c4b8a"
                                        ),
                                        ".archive": DirNode(
                                            children={
                                                "manifest.txt": FileNode(
                                                    "record=recovery.dat\n"
                                                    "encoding=hex\n"
                                                    "classification=confidential"
                                                ),
                                                "recovery.dat": FileNode(
                                                    _RECOVERY_RECORD
                                                ),
                                            }
                                        ),
                                    }
                                )
                            }
                        ),
                    }
                ),
            }
        )

    def _split_chain(self, cmdline: str) -> list[tuple[str, str]]:
        """Split on ;, &&, ||, &, |, and newlines. Quotes suppress separators."""
        parts: list[tuple[str, str]] = []
        buf: list[str] = []
        quote: str | None = None
        operator = ""
        index = 0
        length = len(cmdline)

        def flush() -> None:
            nonlocal buf
            parts.append((operator, "".join(buf)))
            buf = []

        while index < length:
            char = cmdline[index]
            if quote:
                if char == "\\" and quote == '"' and index + 1 < length:
                    buf.append(char)
                    buf.append(cmdline[index + 1])
                    index += 2
                    continue
                buf.append(char)
                if char == quote:
                    quote = None
                index += 1
                continue

            if char in ("'", '"'):
                quote = char
                buf.append(char)
                index += 1
                continue

            if char == "\\" and index + 1 < length and cmdline[index + 1] in "&|;\n":
                buf.append(cmdline[index + 1])
                index += 2
                continue

            if char == "\r":
                index += 2 if index + 1 < length and cmdline[index + 1] == "\n" else 1
                flush()
                operator = ";"
                continue

            if char == "\n":
                index += 1
                flush()
                operator = ";"
                continue

            if cmdline.startswith("&&", index):
                flush()
                operator = "&&"
                index += 2
                continue

            if cmdline.startswith("||", index):
                flush()
                operator = "||"
                index += 2
                continue

            if char == "&":
                flush()
                operator = "&"
                index += 1
                continue

            if char == "|":
                flush()
                operator = "|"
                index += 1
                continue

            if char == ";":
                flush()
                operator = ";"
                index += 1
                continue

            buf.append(char)
            index += 1

        flush()
        return parts

    def _tokenize(self, command: str) -> list[str] | None:
        tokens: list[str] = []
        buf: list[str] = []
        quote: str | None = None
        index = 0
        length = len(command)

        def flush_token() -> None:
            nonlocal buf
            if buf:
                tokens.append("".join(buf))
                buf = []

        while index < length:
            char = command[index]
            if quote == "'":
                if char == "'":
                    quote = None
                else:
                    buf.append(char)
                index += 1
                continue
            if quote == '"':
                if char == "\\" and index + 1 < length:
                    buf.append(command[index + 1])
                    index += 2
                    continue
                if char == '"':
                    quote = None
                    index += 1
                    continue
                buf.append(char)
                index += 1
                continue
            if char in ("'", '"'):
                quote = char
                index += 1
                continue
            if char == "\\" and index + 1 < length:
                buf.append(command[index + 1])
                index += 2
                continue
            if char.isspace():
                flush_token()
                index += 1
                continue
            buf.append(char)
            index += 1

        if quote:
            return None
        flush_token()
        return tokens

    def _run_simple(self, command: str) -> tuple[str, int]:
        argv = self._tokenize(command)
        if argv is None:
            return ("bash: syntax error: unterminated quoted string", 2)
        if not argv:
            return ("", 0)
        if any("<" in token or ">" in token for token in argv):
            return ("bash: redirection is not supported in this environment", 2)
        return self._dispatch(argv)

    def _dispatch(self, argv: list[str]) -> tuple[str, int]:
        name = argv[0]
        args = argv[1:]
        if "/" in name:
            return (f"bash: {name}: No such file or directory", 127)
        handlers = {
            "echo": self._cmd_echo,
            "pwd": self._cmd_pwd,
            "whoami": self._cmd_whoami,
            "hostname": self._cmd_hostname,
            "ls": self._cmd_ls,
            "uname": self._cmd_uname,
            "cat": self._cmd_cat,
            "cd": self._cmd_cd,
            "status": self._cmd_status,
        }
        handler = handlers.get(name)
        if handler is None:
            return (f"bash: {name}: command not found", 127)
        return handler(args)

    def _cmd_echo(self, args: list[str]) -> tuple[str, int]:
        return (" ".join(args), 0)

    def _cmd_pwd(self, _args: list[str]) -> tuple[str, int]:
        return (self.cwd, 0)

    def _cmd_whoami(self, _args: list[str]) -> tuple[str, int]:
        return (self.USERNAME, 0)

    def _cmd_hostname(self, _args: list[str]) -> tuple[str, int]:
        return (self.HOSTNAME, 0)

    def _cmd_status(self, _args: list[str]) -> tuple[str, int]:
        return (
            "System status: Operational.\nAll monitored services are running normally.",
            0,
        )

    def _cmd_cd(self, args: list[str]) -> tuple[str, int]:
        if len(args) > 1:
            return ("bash: cd: too many arguments", 1)
        target = self.HOME if not args else args[0]
        node, normalized = self._resolve(target)
        if node is None:
            return (f"bash: cd: {target}: No such file or directory", 1)
        if not isinstance(node, DirNode):
            return (f"bash: cd: {target}: Not a directory", 1)
        self.cwd = normalized
        return ("", 0)

    def _cmd_cat(self, args: list[str]) -> tuple[str, int]:
        if not args:
            return ("cat: missing operand", 1)
        parts: list[str] = []
        code = 0
        for arg in args:
            if arg.startswith("-") and arg != "-":
                flag = arg[1:2] or arg
                return (f"cat: invalid option -- '{flag}'", 1)
            node, _normalized = self._resolve(arg)
            if node is None:
                parts.append(f"cat: {arg}: No such file or directory")
                code = 1
                continue
            if isinstance(node, DirNode):
                parts.append(f"cat: {arg}: Is a directory")
                code = 1
                continue
            parts.append(node.content)
        return ("\n".join(parts), code)

    def _cmd_uname(self, args: list[str]) -> tuple[str, int]:
        if not args:
            return ("Linux", 0)
        flags: list[str] = []
        known = {
            "s": "Linux",
            "n": self.HOSTNAME,
            "r": "6.8.0-45-generic",
            "v": "#45-Ubuntu SMP",
            "m": "x86_64",
            "p": "x86_64",
            "i": "x86_64",
            "o": "GNU/Linux",
        }
        normalized: list[str] = []
        index = 0
        while index < len(args):
            arg = args[index]
            if (
                arg == "-"
                and index + 1 < len(args)
                and len(args[index + 1]) == 1
                and args[index + 1].isalpha()
            ):
                normalized.append("-" + args[index + 1])
                index += 2
                continue
            normalized.append(arg)
            index += 1
        for arg in normalized:
            if arg.startswith("--"):
                return (f"uname: unrecognized option '{arg}'", 1)
            if not arg.startswith("-") or arg == "-":
                return (f"uname: extra operand '{arg}'", 1)
            flags.extend(list(arg[1:]))
        if "a" in flags:
            return (self.UNAME_A, 0)
        parts: list[str] = []
        for flag in flags:
            if flag not in known:
                return (f"uname: invalid option -- '{flag}'", 1)
            parts.append(known[flag])
        return (" ".join(parts), 0)

    def _cmd_ls(self, args: list[str]) -> tuple[str, int]:
        flags: set[str] = set()
        paths: list[str] = []
        for arg in args:
            if arg.startswith("--"):
                if arg == "--":
                    continue
                return (f"ls: unrecognized option '{arg}'", 2)
            if arg.startswith("-") and arg != "-":
                for flag in arg[1:]:
                    if flag not in ("l", "a"):
                        return (f"ls: invalid option -- '{flag}'", 2)
                    flags.add(flag)
                continue
            paths.append(arg)
        if not paths:
            paths = ["."]

        chunks: list[str] = []
        code = 0
        show_headers = len(paths) > 1
        for path in paths:
            chunk, path_code = self._ls_path(path, flags, show_headers)
            if path_code != 0:
                code = path_code
            if chunk:
                chunks.append(chunk)
        return ("\n".join(chunks), code)

    def _ls_path(self, path: str, flags: set[str], show_header: bool) -> tuple[str, int]:
        node, normalized = self._resolve(path)
        if node is None:
            return (f"ls: cannot access '{path}': No such file or directory", 2)
        if isinstance(node, FileNode):
            line = self._long_line(node, path) if "l" in flags else path
            return (line, 0)

        rows = self._directory_rows(node, normalized, flags)
        lines: list[str] = []
        if show_header:
            lines.append(f"{path}:")
        if "l" in flags:
            total = sum(blocks for blocks, _line in rows)
            lines.append(f"total {total}")
        lines.extend(line for _blocks, line in rows)
        return ("\n".join(lines), 0)

    def _directory_rows(
        self, node: DirNode, normalized: str, flags: set[str]
    ) -> list[tuple[int, str]]:
        rows: list[tuple[int, str]] = []
        if "a" in flags:
            parent_path = "/" if normalized == "/" else (normalized.rsplit("/", 1)[0] or "/")
            parent, _normalized_parent = self._resolve(parent_path)
            parent_node = parent if isinstance(parent, DirNode) else node
            rows.append(self._entry(".", node, flags))
            rows.append(self._entry("..", parent_node, flags))
        for name in sorted(node.children):
            child = node.children[name]
            if name.startswith(".") and "a" not in flags:
                continue
            rows.append(self._entry(name, child, flags))
        return rows

    def _entry(self, name: str, node: FileNode | DirNode, flags: set[str]) -> tuple[int, str]:
        blocks = 4 if isinstance(node, DirNode) else max(1, (len(node.content) + 1023) // 1024)
        shown = f"{name}/" if isinstance(node, DirNode) and name not in (".", "..") else name
        if "l" not in flags:
            return (blocks, shown)
        return (blocks, self._long_line(node, shown))

    def _long_line(self, node: FileNode | DirNode, name: str) -> str:
        if isinstance(node, DirNode):
            perm = "drwxr-xr-x"
            links = 2 + sum(isinstance(child, DirNode) for child in node.children.values())
            size = 4096
        else:
            perm = "-rw-r--r--"
            links = 1
            size = len(node.content)
        return f"{perm} {links:>2} student student {size:>5} Nov  2 10:00 {name}"

    def _resolve(self, path: str) -> tuple[FileNode | DirNode | None, str]:
        if path == "~" or path.startswith("~/"):
            path = self.HOME + path[1:]
        normalized = self._normalize(path)
        if normalized == "/":
            return self.root, normalized
        node: FileNode | DirNode = self.root
        for part in normalized.strip("/").split("/"):
            if not isinstance(node, DirNode) or part not in node.children:
                return None, normalized
            node = node.children[part]
        return node, normalized

    def _normalize(self, path: str) -> str:
        if path.startswith("/"):
            combined = path
        else:
            base = self.cwd.rstrip("/")
            combined = f"{base}/{path}" if base else f"/{path}"
        parts: list[str] = []
        for part in combined.split("/"):
            if part in ("", "."):
                continue
            if part == "..":
                if parts:
                    parts.pop()
                continue
            parts.append(part)
        if not parts:
            return "/"
        return "/" + "/".join(parts)
