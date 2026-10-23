"""CustomOS: a simple Unix-like shell for Advanced Operating Systems, D1."""
import sys

from .commands import Commands, CommandError
from .parser import ParseError, parse_command
from .process_manager import ProcessManager

USAGE = """Available commands:
  cd [directory]    pwd                 exit
  echo [text]       clear               ls [directory]
  cat <file>        mkdir <directory>   rmdir <directory>
  rm <file>         touch <file>        kill <pid>
  jobs              fg <job_id>         bg <job_id>
  help
External commands may be run normally or in the background with a trailing '&'.
Example: sleep 20 &     Note: pipes and redirection come in Deliverable 4.
"""

BUILTINS = {"cd", "pwd", "echo", "clear", "ls", "cat", "mkdir",
            "rmdir", "rm", "touch"}


class Shell:
    def __init__(self) -> None:
        self.manager = ProcessManager()
        self.commands = Commands()
        self.exiting = False

    def execute_line(self, line: str) -> None:
        try:
            argv, background = parse_command(line)
        except ParseError as exc:
            print(f"Error: invalid command syntax: {exc}")
            return
        if not argv:
            return
        cmd, *args = argv
        if cmd in BUILTINS or cmd in {"exit", "kill", "jobs", "fg", "bg", "help"}:
            if background:
                print(f"Error: '{cmd}' is a built-in and cannot run in background")
                return
            try:
                if cmd in BUILTINS:
                    self.commands.execute(cmd, args)
                elif cmd == "exit":
                    if args:
                        raise CommandError("exit: does not accept arguments")
                    self.exiting = True
                elif cmd == "help":
                    if args:
                        raise CommandError("help: does not accept arguments")
                    print(USAGE)
                elif cmd == "jobs":
                    if args:
                        raise CommandError("jobs: does not accept arguments")
                    self.manager.list_jobs()
                else:
                    if len(args) != 1:
                        raise CommandError(f"{cmd}: exactly one PID or job ID is required")
                    if cmd == "kill":
                        self.manager.terminate_pid(args[0])
                    elif cmd == "fg":
                        self.manager.foreground(args[0])
                    elif cmd == "bg":
                        self.manager.background(args[0])
            except CommandError as exc:
                print(f"Error: {exc}")
        else:
            self.manager.launch(argv, background)

    def run(self) -> None:
        print("CustomOS Shell 1.0 | Advanced Operating Systems | type 'help'")
        try:
            while not self.exiting:
                self.manager.refresh()
                try:
                    line = input("CustomOS> ")
                except EOFError:
                    print()
                    break
                except KeyboardInterrupt:
                    print("\nPress Ctrl+D or type 'exit' to quit.")
                    continue
                try:
                    self.execute_line(line)
                except KeyboardInterrupt:
                    print()
        finally:
            self.manager.shutdown()
            print("Goodbye from CustomOS.")
