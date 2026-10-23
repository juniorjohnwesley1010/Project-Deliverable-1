"""POSIX process creation and one-process-per-job terminal job control.

This module manages actual OS child processes; it does not simulate CPU scheduling.
That is intentionally reserved for the next deliverable.
"""
from dataclasses import dataclass
from enum import Enum
import os
import signal
import subprocess
import sys
import time


class JobState(str, Enum):
    RUNNING = "Running"
    STOPPED = "Stopped"
    DONE = "Done"
    TERMINATED = "Terminated"


@dataclass
class Job:
    job_id: int
    pid: int
    pgid: int
    command: str
    background: bool
    state: JobState = JobState.RUNNING
    exit_code: int | None = None
    signum: int | None = None
    process: subprocess.Popen | None = None

    @property
    def active(self) -> bool:
        return self.state in (JobState.RUNNING, JobState.STOPPED)


class ProcessManager:
    def __init__(self) -> None:
        if os.name != "posix" or not hasattr(os, "tcsetpgrp"):
            raise RuntimeError("CustomOS requires a POSIX terminal (Linux, WSL2, or macOS)")
        self.jobs: dict[int, Job] = {}
        self.next_job_id = 1
        self.tty_fd = sys.stdin.fileno()
        self.interactive = sys.stdin.isatty() and sys.stdout.isatty()
        self.shell_pgid = os.getpgrp()
        if self.interactive:
            # When run by Bash, the process may already be its own process group.
            try:
                os.setpgid(0, 0)
            except PermissionError:
                pass  # A session leader is already the leader of its process group.
            self.shell_pgid = os.getpgrp()
            # The shell needs to reclaim the terminal without being suspended.
            for sig in (signal.SIGTTOU, signal.SIGTTIN):
                signal.signal(sig, signal.SIG_IGN)
            try:
                os.tcsetpgrp(self.tty_fd, self.shell_pgid)
            except OSError as exc:
                raise RuntimeError(f"unable to control terminal: {exc}") from exc
        # These caught handlers become default after exec in child processes.
        signal.signal(signal.SIGINT, self._signal_at_prompt)
        signal.signal(signal.SIGTSTP, self._signal_at_prompt)
        signal.signal(signal.SIGQUIT, self._signal_at_prompt)

    @staticmethod
    def _signal_at_prompt(signum: int, frame: object) -> None:
        if signum == signal.SIGINT:
            raise KeyboardInterrupt

    @staticmethod
    def _reset_child_signals() -> None:
        # subprocess.POpen doesn't reset ignored SIGTTIN/SIGTTOU by itself.
        for sig in (signal.SIGINT, signal.SIGQUIT, signal.SIGTSTP,
                    signal.SIGTTIN, signal.SIGTTOU):
            signal.signal(sig, signal.SIG_DFL)

    def launch(self, args: list[str], background: bool) -> None:
        cmd = " ".join(args)
        try:
            proc = subprocess.Popen(
                args, shell=False, process_group=0,
                preexec_fn=self._reset_child_signals,
            )
        except FileNotFoundError:
            print(f"Error: command not found: {args[0]}")
            return
        except (OSError, subprocess.SubprocessError) as exc:
            print(f"Error: could not start '{args[0]}': {exc}")
            return

        job = Job(self.next_job_id, proc.pid, proc.pid, cmd, background, process=proc)
        self.jobs[job.job_id] = job
        self.next_job_id += 1
        if background:
            print(f"[{job.job_id}] {job.pid}")
        else:
            self._foreground_wait(job, resume=False)

    def _apply_wait_status(self, job: Job, status: int) -> None:
        if os.WIFSTOPPED(status):
            job.state = JobState.STOPPED
            job.signum = os.WSTOPSIG(status)
        elif hasattr(os, "WIFCONTINUED") and os.WIFCONTINUED(status):
            job.state = JobState.RUNNING
            job.signum = None
        elif os.WIFSIGNALED(status):
            job.state = JobState.TERMINATED
            job.signum = os.WTERMSIG(status)
            job.exit_code = 128 + job.signum
        elif os.WIFEXITED(status):
            job.state = JobState.DONE
            job.exit_code = os.WEXITSTATUS(status)
        if not job.active and job.process is not None:
            job.process.returncode = (-job.signum if job.state == JobState.TERMINATED
                                      else job.exit_code)

    def _foreground_wait(self, job: Job, resume: bool) -> None:
        try:
            if self.interactive:
                os.tcsetpgrp(self.tty_fd, job.pgid)
            if resume:
                os.killpg(job.pgid, signal.SIGCONT)
                job.state = JobState.RUNNING
            while job.active:
                try:
                    _, status = os.waitpid(job.pid, os.WUNTRACED)
                except InterruptedError:
                    continue
                except ChildProcessError:
                    break
                self._apply_wait_status(job, status)
                if job.state == JobState.TERMINATED and job.signum == signal.SIGINT:
                    print()  # Keep the next prompt below the terminal's echoed ^C.
                if job.state == JobState.STOPPED:
                    job.background = True
                    print(f"\n[{job.job_id}] Stopped    {job.command}")
                    break
        except ProcessLookupError:
            print(f"Error: process no longer exists: {job.pid}")
        finally:
            if self.interactive:
                os.tcsetpgrp(self.tty_fd, self.shell_pgid)
            if not job.active:
                self.jobs.pop(job.job_id, None)

    def refresh(self) -> None:
        """Nonblocking status collection; only reaps our recorded children."""
        flags = os.WNOHANG | os.WUNTRACED
        if hasattr(os, "WCONTINUED"):
            flags |= os.WCONTINUED
        for job in list(self.jobs.values()):
            if not job.active:
                continue
            try:
                pid, status = os.waitpid(job.pid, flags)
            except ChildProcessError:
                continue
            if pid:
                self._apply_wait_status(job, status)

    def list_jobs(self) -> None:
        self.refresh()
        if not self.jobs:
            print("No jobs.")
            return
        for job in sorted(self.jobs.values(), key=lambda j: j.job_id):
            suffix = f" (exit {job.exit_code})" if job.state == JobState.DONE else ""
            print(f"[{job.job_id}] {job.state.value:<10} PID={job.pid:<8} {job.command}{suffix}")
        # Finished background jobs can be inspected once before removal.
        self.jobs = {i: j for i, j in self.jobs.items() if j.active}

    def _get_job(self, argument: str, operation: str) -> Job | None:
        try:
            job_id = int(argument.lstrip("%"))
            if job_id < 1:
                raise ValueError
        except ValueError:
            print(f"Error: {operation}: job ID must be a positive integer")
            return None
        self.refresh()
        job = self.jobs.get(job_id)
        if job is None or not job.active:
            print(f"Error: {operation}: no active job {job_id}")
            return None
        return job

    def foreground(self, argument: str) -> None:
        job = self._get_job(argument, "fg")
        if job is None:
            return
        resume = job.state == JobState.STOPPED
        job.background = False
        self._foreground_wait(job, resume=resume)

    def background(self, argument: str) -> None:
        job = self._get_job(argument, "bg")
        if job is None:
            return
        if job.state != JobState.STOPPED:
            print(f"Error: bg: job {job.job_id} is not stopped")
            return
        try:
            os.killpg(job.pgid, signal.SIGCONT)
        except ProcessLookupError:
            print(f"Error: bg: process group {job.pgid} no longer exists")
            return
        job.state = JobState.RUNNING
        job.background = True
        print(f"[{job.job_id}] Running    {job.command} &")

    def terminate_pid(self, pid_arg: str) -> None:
        try:
            pid = int(pid_arg)
            if pid <= 0:
                raise ValueError
        except ValueError:
            print("Error: kill: PID must be a positive integer")
            return
        if pid == os.getpid():
            print("Error: kill: refusing to terminate the shell itself")
            return
        try:
            os.kill(pid, signal.SIGTERM)
            print(f"Sent SIGTERM to PID {pid}")
        except ProcessLookupError:
            print(f"Error: kill: process {pid} does not exist")
        except PermissionError:
            print(f"Error: kill: permission denied for PID {pid}")

    def shutdown(self) -> None:
        """Clean up jobs created by the shell, avoiding abandoned children."""
        self.refresh()
        active = [j for j in self.jobs.values() if j.active]
        for job in active:
            try:
                os.killpg(job.pgid, signal.SIGCONT)
                os.killpg(job.pgid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        deadline = time.monotonic() + 0.5
        while time.monotonic() < deadline:
            self.refresh()
            if not any(j.active for j in self.jobs.values()):
                break
            time.sleep(0.02)
        for job in self.jobs.values():
            if job.active:
                try:
                    os.killpg(job.pgid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                try:
                    _, status = os.waitpid(job.pid, 0)
                    self._apply_wait_status(job, status)
                except ChildProcessError:
                    pass
