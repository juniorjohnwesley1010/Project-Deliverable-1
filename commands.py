"""Required built-in commands implemented using Python standard-library APIs."""
import os
from pathlib import Path
import sys


class CommandError(Exception):
    pass


class Commands:
    @staticmethod
    def _arity(args: list[str], command: str, min_args: int, max_args: int | None = None) -> None:
        count = len(args)
        if count < min_args or (max_args is not None and count > max_args):
            raise CommandError(f"{command}: incorrect arguments (type 'help' for usage)")

    def execute(self, cmd: str, args: list[str]) -> None:
        try:
            func = getattr(self, f"cmd_{cmd}")
            func(args)
        except (OSError, UnicodeError) as exc:
            raise CommandError(f"{cmd}: {exc.strerror if isinstance(exc, OSError) else exc}") from exc

    def cmd_cd(self, args: list[str]) -> None:
        self._arity(args, "cd", 0, 1)
        os.chdir(os.path.expanduser(args[0] if args else "~"))

    def cmd_pwd(self, args: list[str]) -> None:
        self._arity(args, "pwd", 0, 0)
        print(os.getcwd())

    def cmd_echo(self, args: list[str]) -> None:
        print(" ".join(args))

    def cmd_clear(self, args: list[str]) -> None:
        self._arity(args, "clear", 0, 0)
        print("\033[2J\033[H", end="", flush=True)

    def cmd_ls(self, args: list[str]) -> None:
        self._arity(args, "ls", 0, 1)
        path = Path(args[0] if args else ".").expanduser()
        if path.is_dir():
            for item in sorted(path.iterdir(), key=lambda p: p.name.lower()):
                print(item.name + ("/" if item.is_dir() else ""))
        else:
            if not path.exists():
                raise CommandError(f"ls: no such file or directory: {path}")
            print(path.name)

    def cmd_cat(self, args: list[str]) -> None:
        self._arity(args, "cat", 1, 1)
        with open(args[0], "r", encoding="utf-8", errors="replace") as file:
            sys.stdout.write(file.read())
            sys.stdout.flush()

    def cmd_mkdir(self, args: list[str]) -> None:
        self._arity(args, "mkdir", 1, 1)
        Path(args[0]).mkdir()

    def cmd_rmdir(self, args: list[str]) -> None:
        self._arity(args, "rmdir", 1, 1)
        Path(args[0]).rmdir()

    def cmd_rm(self, args: list[str]) -> None:
        self._arity(args, "rm", 1, 1)
        Path(args[0]).unlink()

    def cmd_touch(self, args: list[str]) -> None:
        self._arity(args, "touch", 1, 1)
        Path(args[0]).touch()
