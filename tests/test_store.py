from datetime import date
from pathlib import Path

import pytest

from calendar_app.store import (
    CalendarReadError,
    CalendarWriteError,
    DayView,
    EmptyText,
    NotOnDay,
    UnreadableLine,
    add_entry,
    delete_entry,
    entries_on,
)

DAY = date(2026, 9, 21)
OTHER = date(2026, 9, 22)


def test_missing_file_has_no_appointments(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"

    view = entries_on(path, DAY)

    assert view == DayView((), False)
    assert not path.exists()


def test_add_writes_exact_utf8_lf_line(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"

    add_entry(path, DAY, "Dentist at 2pm")

    assert path.read_bytes() == "2026-09-21\tDentist at 2pm\n".encode("utf-8")


def test_second_add_appends_and_lookup_keeps_day_order(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"
    add_entry(path, DAY, "Dentist at 2pm")
    first = path.read_bytes()

    add_entry(path, OTHER, "Call the bank")
    add_entry(path, DAY, "Lunch with Sam")

    data = path.read_bytes()
    assert data.startswith(first)
    assert entries_on(path, DAY) == DayView(
        ("Dentist at 2pm", "Lunch with Sam"), False
    )
    assert entries_on(path, OTHER).texts == ("Call the bank",)


def test_identical_lines_are_two_appointments_and_delete_removes_one(
    tmp_path: Path,
) -> None:
    path = tmp_path / "calendar.txt"
    add_entry(path, DAY, "Dentist at 2pm")
    add_entry(path, OTHER, "Call the bank")
    add_entry(path, DAY, "Dentist at 2pm")

    assert entries_on(path, DAY).texts == ("Dentist at 2pm", "Dentist at 2pm")

    delete_entry(path, DAY, 1)

    assert path.read_bytes() == (
        "2026-09-22\tCall the bank\n2026-09-21\tDentist at 2pm\n"
    ).encode("utf-8")
    assert entries_on(path, DAY).texts == ("Dentist at 2pm",)
    assert entries_on(path, OTHER).texts == ("Call the bank",)


def test_tab_and_non_ascii_text_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"

    add_entry(path, DAY, "Café\twith Sam")

    assert path.read_bytes() == "2026-09-21\tCafé\twith Sam\n".encode("utf-8")
    assert entries_on(path, DAY).texts == ("Café\twith Sam",)


def test_delete_number_two_leaves_earlier_line_and_other_day(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"
    add_entry(path, DAY, "Dentist at 2pm")
    add_entry(path, OTHER, "Call the bank")
    add_entry(path, DAY, "Lunch with Sam")

    delete_entry(path, DAY, 2)

    assert path.read_bytes() == (
        "2026-09-21\tDentist at 2pm\n2026-09-22\tCall the bank\n"
    ).encode("utf-8")


def test_delete_last_line_leaves_empty_file_and_no_temp(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"
    add_entry(path, DAY, "Dentist at 2pm")

    delete_entry(path, DAY, 1)

    assert path.exists()
    assert path.read_bytes() == b""
    assert not path.with_name(path.name + ".tmp").exists()


@pytest.mark.parametrize("index", [0, -1, 3])
def test_delete_out_of_range_leaves_bytes_unchanged(
    tmp_path: Path, index: int
) -> None:
    path = tmp_path / "calendar.txt"
    payload = b"2026-09-21\tDentist at 2pm\n2026-09-22\tCall the bank\n"
    path.write_bytes(payload)

    with pytest.raises(NotOnDay):
        delete_entry(path, DAY, index)

    assert path.read_bytes() == payload


def test_delete_missing_file_raises_not_on_day(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"

    with pytest.raises(NotOnDay):
        delete_entry(path, DAY, 1)

    assert not path.exists()


@pytest.mark.parametrize("text", ["", "   ", "\t"])
def test_empty_text_does_not_create_or_change_file(tmp_path: Path, text: str) -> None:
    path = tmp_path / "calendar.txt"
    path.write_bytes(b"2026-09-22\tCall the bank\n")
    before = path.read_bytes()

    with pytest.raises(EmptyText):
        add_entry(path, DAY, text)

    assert path.read_bytes() == before


def test_blank_lines_are_skipped_and_kept_when_another_line_is_deleted(
    tmp_path: Path,
) -> None:
    path = tmp_path / "calendar.txt"
    path.write_bytes(
        b"\n2026-09-21\tDentist at 2pm\n   \n2026-09-22\tCall the bank\n"
    )

    assert entries_on(path, DAY) == DayView(("Dentist at 2pm",), False)

    delete_entry(path, DAY, 1)

    assert path.read_bytes() == b"\n   \n2026-09-22\tCall the bank\n"


def test_bad_lines_are_omitted_and_flagged(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"
    path.write_bytes(
        "2026-09-21\tDentist at 2pm\n"
        "not a line\n"
        "2026-02-31\tNope\n"
        "2026-09-21\t\n"
        "2026-09-21\t   \n"
        "2026-09-22\tCall the bank\n".encode()
    )

    view = entries_on(path, DAY)

    assert view.texts == ("Dentist at 2pm",)
    assert view.ignored_bad_line is True
    assert entries_on(path, OTHER).texts == ("Call the bank",)


def test_delete_refuses_to_rewrite_when_a_bad_line_exists(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"
    payload = b"2026-09-21\tDentist at 2pm\nnot a line\n"
    path.write_bytes(payload)

    with pytest.raises(UnreadableLine):
        delete_entry(path, DAY, 1)

    assert path.read_bytes() == payload


def test_delete_refuses_when_bad_line_is_on_another_day(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"
    payload = b"2026-09-22\tCall the bank\nnot a line\n"
    path.write_bytes(payload)

    with pytest.raises(UnreadableLine):
        delete_entry(path, DAY, 1)

    assert path.read_bytes() == payload


def test_add_appends_and_leaves_an_existing_bad_line(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"
    path.write_bytes(b"not a line\n")

    add_entry(path, DAY, "Dentist at 2pm")

    assert path.read_bytes() == b"not a line\n2026-09-21\tDentist at 2pm\n"


def test_invalid_utf8_is_a_read_error_and_add_still_appends(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"
    payload = b"\xff\xfe not utf-8"
    path.write_bytes(payload)

    with pytest.raises(CalendarReadError):
        entries_on(path, DAY)
    assert path.read_bytes() == payload

    with pytest.raises(CalendarReadError):
        delete_entry(path, DAY, 1)
    assert path.read_bytes() == payload

    add_entry(path, DAY, "Dentist at 2pm")

    data = path.read_bytes()
    assert data.startswith(payload)
    assert data.endswith("2026-09-21\tDentist at 2pm\n".encode("utf-8"))


def test_crlf_file_is_read_and_a_rewrite_saves_lf(tmp_path: Path) -> None:
    path = tmp_path / "calendar.txt"
    path.write_bytes(b"2026-09-21\tDentist at 2pm\r\n2026-09-22\tCall the bank\r\n")

    assert entries_on(path, DAY) == DayView(("Dentist at 2pm",), False)

    delete_entry(path, OTHER, 1)

    assert path.read_bytes() == b"2026-09-21\tDentist at 2pm\n"
    assert not path.with_name(path.name + ".tmp").exists()


def test_add_raises_when_parent_directory_is_missing(tmp_path: Path) -> None:
    path = tmp_path / "missing" / "calendar.txt"

    with pytest.raises(CalendarWriteError):
        add_entry(path, DAY, "Dentist at 2pm")

    assert not path.exists()
