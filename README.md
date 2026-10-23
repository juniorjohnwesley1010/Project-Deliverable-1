# CustomOS Shell — Deliverable 1

Advanced Operating Systems project: Basic shell implementation and process management.

## Requirements

- **Python 3.11+**
- Linux or **Ubuntu via WSL2** (recommended for Windows). macOS also supports POSIX job control.
- An **interactive terminal** for Ctrl+C, Ctrl+Z, `fg`, and `bg` terminal demonstrations.
- No third-party dependencies to run the shell.

The shell invokes real child processes through `subprocess.Popen` and `os.waitpid` and uses real process groups and terminal control. It is not an operating-system kernel. Deliverables 2–4 add simulated scheduling, virtual memory, synchronization, piping, and permissions.

## Run

```bash
cd CustomOS_GitHub_Ready
python3 main.py
```

On Ubuntu, check `python3 --version`. To install a suitable version if necessary, use your distro's supported Python installation path.

## Command examples

```
help
pwd
mkdir sample
cd sample
touch notes.txt
ls
echo "Shell works"
cd ..
rmdir sample      # only after removing notes.txt
sleep 30 &
jobs
fg 1             # waits; Ctrl+Z suspends; Ctrl+C interrupts
bg 1             # resume a stopped job
kill 12345       # replace with an actual PID from jobs
exit
```

`bg` is valid for **stopped** jobs. To test it: run `sleep 30` (foreground), press **Ctrl+Z**, then run `jobs`, `bg 1`, `jobs`, `fg 1`, and Ctrl+C. Job IDs increase as commands are executed.

## Built-in command limits

- `ls`, `cat`, `mkdir`, `rmdir`, `rm`, and `touch` implement their basic course-specified forms, not all GNU options. `ls` supports an optional path.
- `rm` removes files, **not directories**. `rmdir` removes empty directories only.
- `echo` prints arguments, but does not implement Bash variable expansion, `-n`, or output redirection.
- `kill` sends `SIGTERM` to a numeric PID; it does not accept arbitrary signal flags.
- A job contains one external process in Deliverable 1. Pipelines are deferred to Deliverable 4.
- Built-ins are executed inside the shell process because `cd` must update its working directory and `exit` must close the shell. They do not accept `&`.
- `jobs` shows recent completed jobs once, then clears those records. Stopped jobs stay in the table until resumed/terminated.
- On shell exit, tracked active child process groups are terminated to prevent orphaned demo processes.
- `cat <file>` in `help` is a placeholder for a filename, not supported input redirection.

## Tests

From the project root:

```bash
python3 -m unittest discover -s tests -v
```

Interactive job-control tests use `pexpect` if available, but the shell itself has no third-party requirements:

```bash
python3 -m pip install -r requirements-dev.txt
python3 -m unittest tests.test_interactive -v
```

## File structure

- `main.py`: entry point
- `customos/parser.py`: safe tokenizer and reserved D4 operators
- `customos/commands.py`: native Python built-ins
- `customos/process_manager.py`: subprocesses, signals, process groups, job control
- `customos/shell.py`: input loop and dispatch
- `tests/`: repeatable tests
- `.gitignore`: excludes caches and local development artifacts
- `requirements-dev.txt`: optional `pexpect` dependency for interactive tests

## Safety and scope

Run the project as a **normal user**, never with `sudo`. `kill` can affect any process that the current user has permission to signal, so only use PIDs created in your test session. Deleting files with `rm` is irreversible; use a dedicated test directory. Screenshots and the academic Word report are kept outside this GitHub source-code package. You can produce new demonstration screenshots by running the shell in your own terminal.

## Uploading to GitHub

To upload in the GitHub web interface, open your repository, choose **Add file → Upload files**, and drag **all the files and folders inside** this extracted directory (including the `.gitignore` file). Do not upload the ZIP file itself as the source: GitHub does not automatically extract it.

Alternatively, from inside this directory, run `git init`, `git add .`, and `git commit -m "Deliverable 1: Python shell and job control"`, then connect your GitHub repository remote and push.
