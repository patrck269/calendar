"""Interactive menu. It asks, prints, and calls the store."""

from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path

from calendar_app.store import (
    CalendarReadError,
    CalendarWriteError,
    EmptyText,
    NotOnDay,
    UnreadableLine,
    add_entry,
    delete_entry,
    entries_on,
)

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_INDEX = re.compile(r"^[1-9]\d*$")
_MENU = {
    "1": "add",
    "2": "lookup",
    "3": "delete",
    "4": "quit",
}
_MENU_LINES = ("1. Add", "2. Look up", "3. Delete", "4. Quit")


class InvalidDay(Exception):
    pass


class InvalidIndex(Exception):
    pass


class _End(Exception):
    pass


def parse_menu(line: str) -> str | None:
    return _MENU.get(line.strip())


def parse_day(line: str) -> date | None:
    text = line.strip()
    if text == "":
        return None
    if _DATE.fullmatch(text) is None:
        raise InvalidDay
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise InvalidDay from None


def parse_delete_index(line: str) -> int | None:
    text = line.strip()
    if text == "":
        return None
    if _INDEX.fullmatch(text) is None:
        raise InvalidIndex
    return int(text)


def format_listing(texts: Sequence[str]) -> str:
    return "\n".join(f"{number}. {text}" for number, text in enumerate(texts, start=1))


def run(
    path: Path,
    input_fn: Callable[[str], str] = input,
    output_fn: Callable[[str], object] = print,
) -> None:
    try:
        while True:
            for line in _MENU_LINES:
                output_fn(line)
            choice = parse_menu(_read(input_fn, "Choice: "))
            if choice is None:
                output_fn("Choose 1, 2, 3, or 4.")
                continue
            if choice == "quit":
                return
            if choice == "add":
                _add(path, input_fn, output_fn)
            elif choice == "lookup":
                _lookup(path, input_fn, output_fn)
            else:
                _delete(path, input_fn, output_fn)
    except _End:
        return


def _read(input_fn: Callable[[str], str], prompt: str) -> str:
    try:
        return input_fn(prompt)
    except (EOFError, KeyboardInterrupt) as exc:
        raise _End from exc


def _ask_day(
    input_fn: Callable[[str], str], output_fn: Callable[[str], object]
) -> date | None:
    try:
        day = parse_day(_read(input_fn, "Day (YYYY-MM-DD): "))
    except InvalidDay:
        output_fn("Not a date. Use YYYY-MM-DD.")
        return None
    return day


def _add(
    path: Path,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], object],
) -> None:
    day = _ask_day(input_fn, output_fn)
    if day is None:
        return
    text = _read(input_fn, "Appointment: ")
    if text.strip() == "":
        output_fn("Appointment text is required.")
        return
    try:
        add_entry(path, day, text)
    except EmptyText:
        output_fn("Appointment text is required.")
        return
    except CalendarWriteError:
        output_fn("Could not write calendar.txt.")
        return
    output_fn("Saved.")


def _lookup(
    path: Path,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], object],
) -> None:
    day = _ask_day(input_fn, output_fn)
    if day is None:
        return
    try:
        view = entries_on(path, day)
    except CalendarReadError:
        output_fn("Could not read calendar.txt.")
        return
    if view.texts:
        output_fn(format_listing(view.texts))
    else:
        output_fn("No appointments.")
    if view.ignored_bad_line:
        output_fn("Ignored a bad line in calendar.txt.")
    output_fn("")


def _delete(
    path: Path,
    input_fn: Callable[[str], str],
    output_fn: Callable[[str], object],
) -> None:
    day = _ask_day(input_fn, output_fn)
    if day is None:
        return
    try:
        view = entries_on(path, day)
    except CalendarReadError:
        output_fn("Could not read calendar.txt.")
        return
    if view.ignored_bad_line:
        output_fn(
            "calendar.txt has a line I can't read. Fix or remove it, then try again."
        )
        return
    if not view.texts:
        output_fn("No appointments.")
        return
    output_fn(format_listing(view.texts))
    try:
        index = parse_delete_index(_read(input_fn, "Number to delete: "))
    except InvalidIndex:
        output_fn("Not a line on that day.")
        return
    if index is None:
        return
    try:
        delete_entry(path, day, index)
    except NotOnDay:
        output_fn("Not a line on that day.")
        return
    except UnreadableLine:
        output_fn(
            "calendar.txt has a line I can't read. Fix or remove it, then try again."
        )
        return
    except CalendarWriteError:
        output_fn("Could not write calendar.txt.")
        return
    output_fn("Deleted.")
