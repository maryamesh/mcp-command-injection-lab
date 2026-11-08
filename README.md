# MCP Command Injection – The Secret Vault

Simulated security lab. Students assess an IT support assistant that calls a `system_status` tool. A mock assistant, a mock MCP server, and an in-memory shell run entirely in Python.

No live language model, MCP network connection, Docker container, or operating-system shell is used. Diagnostic text is interpreted by the simulator.

## Run on Windows

Open PowerShell in the `mcp-command-injection-lab` folder, then run:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

If activation is blocked, start the app with the virtual environment Python directly:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run streamlit_app.py
```

If `python` is not recognized, use `py` instead.

## Project layout

- `streamlit_app.py` — lab page
- `mock_agent.py` — deterministic IT support assistant
- `mock_mcp_server.py` — simulated `system_status` tool
- `simulated_shell.py` — in-memory shell and filesystem
- `requirements.txt` — Python dependencies

## Talking to the assistant

Ask in ordinary language about the system status, the hostname, or the operating system. For a simulated shell command, submit a tool call. The assistant passes the command text through unchanged.

```text
system_status(command: pwd)
```

Any other request receives a fixed refusal. The chat is an assistant transcript, not a host terminal.

Clearing the conversation resets the simulated working directory to `/`.

## Simulated shell

The shell starts in `/` as user `student` on host `IT-SERVER-01`, where `ls`
shows the `/app` and `/var` directories. The
simulated filesystem contains application configuration and logs under `/app`
and operational logs and backups under `/var`. It only understands this grammar:

- Commands: `status`, `pwd`, `whoami`, `hostname`, `ls`, `ls -la`, `uname`, `uname -a`, `cat`, `cd`, `echo`
- Separators: `;`, `&&`, `||`, `&`, and newlines
- Quotes group words and suppress separators inside the quoted text

`ls -l`, `ls -a`, and `ls -al` use the same listing rules as `ls -la`. Relative paths, `..`, and `~` resolve inside the simulated tree. Unsupported commands return a command-not-found message. Pipes and redirection are rejected. Results are deterministic.

## Objective

Retrieve the hidden secret from the simulated host, decode the hexadecimal text, and submit the decoded password in the Secret Vault Validation box.

## Safety

The simulator does not call `subprocess`, `os.system`, `eval`, or `exec`. It does not read arbitrary files on the computer running the lab. Command results come from the fixed in-memory filesystem.
