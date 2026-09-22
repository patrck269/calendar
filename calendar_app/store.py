"""Read and write the appointment text file. No prompts and no printing."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class DayView:
    texts: tuple[str, ...]
    ignored_bad_line: bool


class StoreError(Exception):
    pass


class EmptyText(StoreError):
    pass


class UnreadableLine(StoreError):
    pass


class NotOnDay(StoreError):
    pass


class CalendarReadError(StoreError):
    pass


class CalendarWriteError(StoreError):
    pass


def add_entry(path: Path, day: date, text: str) -> None:
    stripped = text.strip()
    if stripped == "":
        raise EmptyText
    if not path.parent.is_dir():
        raise CalendarWriteError(f"cannot create {path}")
    line = f"{day.isoformat()}\t{stripped}\n"
    try:
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line)
    except OSError as exc:
        raise CalendarWriteError(str(exc)) from exc


def entries_on(path: Path, day: date) -> DayView:
    if not path.exists():
        return DayView((), False)
    texts: list[str] = []
    bad = False
    for line in _read_lines(path):
        kind, line_day, body = _classify(line)
        if kind == "bad":
            bad = True
        elif kind == "good" and line_day == day:
            texts.append(body)
    return DayView(tuple(texts), bad)


def delete_entry(path: Path, day: date, index: int) -> None:
    if not path.exists():
        raise NotOnDay
    lines = _read_lines(path)
    classified = [_classify(line) for line in lines]
    if any(kind == "bad" for kind, _line_day, _body in classified):
        raise UnreadableLine
    if index < 1:
        raise NotOnDay
    remove_at: int | None = None
    seen = 0
    for position, (kind, line_day, _body) in enumerate(classified):
        if kind == "good" and line_day == day:
            seen += 1
            if seen == index:
                remove_at = position
                break
    if remove_at is None:
        raise NotOnDay
    kept = [line for position, line in enumerate(lines) if position != remove_at]
    _rewrite(path, kept)


def _classify(line: str) -> tuple[str, date | None, str]:
    if line.strip(" ") == "":
        return "blank", None, ""
    tab = line.find("\t")
    if tab < 0:
        return "bad", None, ""
    date_text = line[:tab]
    body = line[tab + 1 :]
    if _DATE.fullmatch(date_text) is None:
        return "bad", None, ""
    try:
        parsed = date.fromisoformat(date_text)
    except ValueError:
        return "bad", None, ""
    if body.strip() == "":
        return "bad", None, ""
    return "good", parsed, body


def _read_lines(path: Path) -> list[str]:
    try:
        raw = path.read_text(encoding="utf-8", newline=None)
    except (UnicodeDecodeError, OSError) as exc:
        raise CalendarReadError(str(exc)) from exc
    return raw.splitlines()


def _rewrite(path: Path, lines: list[str]) -> None:
    temporary = path.with_name(path.name + ".tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            for line in lines:
                handle.write(line + "\n")
        os.replace(temporary, path)
    except OSError as exc:
        if temporary.exists():
            try:
                temporary.unlink()
            except OSError:
                pass
        raise CalendarWriteError(str(exc)) from exc
