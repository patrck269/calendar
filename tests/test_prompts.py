from datetime import date
from pathlib import Path

import pytest

from calendar_app.prompts import (
    InvalidDay,
    InvalidIndex,
    format_listing,
    parse_day,
    parse_delete_index,
    parse_menu,
    run,
)

DAY = date(2026, 9, 21)


def test_parse_menu_accepts_only_the_four_choices() -> None:
    assert parse_menu("1") == "add"
    assert parse_menu("2") == "lookup"
    assert parse_menu("3") == "delete"
    assert parse_menu("4") == "quit"
    assert parse_menu(" 1 ") == "add"
    assert parse_menu("add") is None
    assert parse_menu("") is None
    assert parse_menu("5") is None
    assert parse_menu("01") is None


def test_parse_day_accepts_a_real_zero_padded_date() -> None:
    assert parse_day("2026-09-21") == DAY
    assert parse_day(" 2026-09-21 ") == DAY
    assert parse_day("2024-02-29") == date(2024, 2, 29)
    assert parse_day("") is None
    assert parse_day("   ") is None


@pytest.mark.parametrize(
    "text",
    ["2026-02-29", "2026-9-21", "09/21/2026", "tomorrow", "2026-02-31", "2026-13-01"],
)
def test_parse_day_rejects_anything_else(text: str) -> None:
    with pytest.raises(InvalidDay):
        parse_day(text)


def test_parse_delete_index_accepts_positive_integers_without_leading_zero() -> None:
    assert parse_delete_index("1") == 1
    assert parse_delete_index("10") == 10
    assert parse_delete_index(" 2 ") == 2
    assert parse_delete_index("") is None
    assert parse_delete_index("   ") is None


@pytest.mark.parametrize("text", ["0", "01", "-1", "1.5", "a", "+1"])
def test_parse_delete_index_rejects_other_tokens(text: str) -> None:
    with pytest.raises(InvalidIndex):
        parse_delete_index(text)


def test_format_listing_numbers_from_one() -> None:
    assert format_listing(("Dentist at 2pm", "Lunch with Sam")) == (
        "1. Dentist at 2pm\n2. Lunch with Sam"
    )


def _drive(path: Path, lines: list[str]) -> list[str]:
    remaining = iter(lines)

    def input_fn(prompt: str) -> str:
        return next(remaining)

    outputs: list[str] = []
    run(path, input_fn, outputs.append)
    return outputs


def test_scripted_session_adds_looks_up_deletes_and_quits(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"
    outputs = _drive(
        path,
        [
            "1",
            "2026-09-21",
            "Dentist at 2pm",
            "1",
            "2026-09-21",
            "Lunch with Sam",
            "2",
            "2026-09-21",
            "3",
            "2026-09-21",
            "1",
            "2",
            "2026-09-21",
            "4",
        ],
    )
    text = "\n".join(outputs)

    assert text.count("Saved.") == 2
    assert "1. Dentist at 2pm\n2. Lunch with Sam" in text
    assert "Deleted." in text
    after_delete = text.split("Deleted.", 1)[1]
    assert "1. Lunch with Sam" in after_delete
    assert "Dentist" not in after_delete
    assert path.read_bytes() == "2026-09-21\tLunch with Sam\n".encode("utf-8")


def test_tomorrow_writes_nothing(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"

    outputs = _drive(path, ["1", "tomorrow", "4"])

    assert "Not a date. Use YYYY-MM-DD." in outputs
    assert not path.exists()


def test_unknown_menu_choice_does_not_write(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"

    outputs = _drive(path, ["add", "4"])

    assert "Choose 1, 2, 3, or 4." in outputs
    assert not path.exists()


def test_empty_appointment_text_does_not_write(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"

    outputs = _drive(path, ["1", "2026-09-21", "   ", "4"])

    assert "Appointment text is required." in outputs
    assert not path.exists()


def test_out_of_range_delete_leaves_the_file(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"
    outputs = _drive(
        path,
        ["1", "2026-09-21", "Dentist at 2pm", "3", "2026-09-21", "2", "4"],
    )

    assert "Not a line on that day." in outputs
    assert path.read_bytes() == "2026-09-21\tDentist at 2pm\n".encode("utf-8")


def test_quit_leaves_existing_bytes_unchanged(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"
    payload = b"2026-09-21\tDentist at 2pm\n"
    path.write_bytes(payload)

    _drive(path, ["4"])

    assert path.read_bytes() == payload


def test_lookup_reports_a_bad_line_and_delete_refuses(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"
    payload = b"2026-09-21\tDentist at 2pm\nnot a line\n"
    path.write_bytes(payload)

    outputs = _drive(path, ["2", "2026-09-21", "3", "2026-09-21", "4"])

    assert "1. Dentist at 2pm" in outputs
    assert "Ignored a bad line in calendar.txt." in outputs
    assert (
        "calendar.txt has a line I can't read. Fix or remove it, then try again."
        in outputs
    )
    assert path.read_bytes() == payload


def test_eof_exits_without_writing(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"

    def input_fn(prompt: str) -> str:
        raise EOFError

    outputs: list[str] = []
    run(path, input_fn, outputs.append)

    assert outputs == ["1. Add", "2. Look up", "3. Delete", "4. Quit"]
    assert not path.exists()
