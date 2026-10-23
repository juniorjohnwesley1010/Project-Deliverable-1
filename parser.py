"""A deliberately small tokenizer for Deliverable 1 (no pipes/redirection yet)."""
import shlex


class ParseError(ValueError):
    """Raised for invalid shell input syntax."""


def parse_command(line: str) -> tuple[list[str], bool]:
    lexer = shlex.shlex(line, posix=True, punctuation_chars="&|<>")
    lexer.whitespace_split = True
    lexer.commenters = ""  # A '#' within a command is literal in this teaching shell.
    try:
        tokens = list(lexer)
    except ValueError as exc:
        raise ParseError(str(exc)) from exc
    if not tokens:
        return [], False
    if any(token in ("|", "<", ">", ">>", "<<") for token in tokens):
        raise ParseError("piping and redirection are reserved for Deliverable 4")
    background = tokens[-1] == "&"
    if background:
        tokens.pop()
    if "&" in tokens:
        raise ParseError("'&' is only supported at the end of a command")
    if not tokens:
        raise ParseError("a command is required before '&'")
    return tokens, background
