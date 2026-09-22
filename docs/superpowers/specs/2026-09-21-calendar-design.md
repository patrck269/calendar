# Calendar — Design

**Date:** 2026-09-21
**Status:** Pending review

## Classification

This is **architectural**. There is no existing calendar flow. This is a new program in its own project folder, not a change to some other program.

## Purpose

An interactive Python program that stores appointments in one text file and can show or delete the appointments on a given day.

## Decisions already made

| Topic | Choice |
| --- | --- |
| How you use it | Interactive menu. Not command-line flags. Not a window. |
| What an appointment is | A real calendar day, plus one line of text. Time, if any, is inside that line. |
| Actions | Add, look up, delete, quit. The menu repeats until quit. |
| Language | Python, standard library only. |
| Shape | A store module that only touches the file, and a prompt module that only asks and prints. |
| Where it lives | Its own project folder, wherever that folder sits |

## Success criteria

1. Add asks for a day and one line of text, then appends that appointment to `calendar.txt`.
2. Look up asks for a day and prints every appointment stored for that day, in the order they were added.
3. Delete asks for a day, shows that day's appointments numbered, and removes exactly the line whose number you type.
4. Quit leaves the file alone.
5. A missing `calendar.txt` means there are no appointments. The first successful add creates it.
6. Failed typing and failed deletes do not change the file.
7. Automated tests cover the store and the prompt rules without anyone typing at a real console.

## Non-goals

Editing a line in place, renaming, recurring appointments, a separate time field, listing every saved day, search, more than one calendar file, reminders, a graphical window, natural-language dates (`today`, `tomorrow`, `9/21/2026`).

---

## Approaches

### 1. Store and prompts split (chosen)

`calendar_app/store.py` reads and writes the text file. `calendar_app/prompts.py` asks questions and prints answers. Tests call the store with a temporary file.

- Pros: add, look up, and delete are testable without stdin. The file format lives in one place.
- Cons: two modules instead of one script.

### 2. A single script (rejected)

Same menu and file format inside one file.

- Pros: shorter to write.
- Cons: prompts and file logic are tangled, so the save-and-read checks are harder to trust.

### 3. A text file grouped by day (rejected)

Date headings with appointment lines underneath, meant to be read in Notepad.

- Pros: easier to scan by hand.
- Cons: add and delete must rewrite sections, and blank lines are easy to mis-parse. It does not make lookup or delete more correct.

---

## Architecture

Two pieces and one data file.

**Store** (`calendar_app/store.py`). Adds a line, returns the lines for one day, and deletes one line on a day by number. It never calls `input` or `print`. Callers pass the file path. Tests pass a temporary path.

**Prompts** (`calendar_app/prompts.py`). Prints the menu, reads a choice, asks for a day and (when adding) one line of text, calls the store, and prints the result. It does not know the on-disk line format. `run(path, input_fn, output_fn)` is the loop. `calendar_app/__main__.py` calls `run` with the default path, `input`, and `print`.

**File.** `calendar.txt` in the project root. The default path is `Path(__file__).resolve().parent.parent / "calendar.txt"` from the package, so the current working directory does not matter. `calendar.txt` is gitignored user data. The program creates it on the first successful add.

No window, no network, no second data file.

---

## File format

UTF-8, no byte-order mark. One appointment per line. The line is the date, one tab, then the text, then `\n` (LF, not CRLF). Appends and the delete rewrite use `encoding="utf-8"` and `newline="\n"`, so new bytes are LF even on Windows. Reading uses `encoding="utf-8"` and `newline=None`, so an existing LF or CRLF file both parse. A rewrite then saves LF only.

```text
2026-09-21	Dentist at 2pm
2026-09-21	Lunch with Sam
2026-09-22	Call the bank
```

Rules:

- The date is `YYYY-MM-DD` for a real calendar day (`datetime.date.isoformat()`).
- Split on the first tab only. Tabs inside the text are part of the text.
- The text is required and may contain spaces. Two identical lines on the same day are two appointments.
- File order is add order. Later operations preserve the relative order of lines they do not remove.
- A missing file means no appointments.
- Reading accepts LF or CRLF. Writing always uses LF.
- A line that is empty, or only spaces, is **blank**. It is not an appointment and it is not a bad line. Delete keeps that raw line where it was.
- A **good line** is a real `YYYY-MM-DD` date, a tab, and text whose stripped form is non-empty. The stored text is everything after the first tab, unchanged (a hand-edited leading space stays). The program itself strips text before it writes, so lines it adds have no surrounding whitespace.
- Any other non-blank line is a **bad line**. That includes no tab, a tab with empty or whitespace-only text, and an impossible date such as `2026-02-31`.

A bad line is file-wide: one bad line marks the whole file, not just that day.

---

## Store interface

```python
@dataclass(frozen=True)
class DayView:
    texts: tuple[str, ...]      # good lines for that day, file order, text after the first tab
    ignored_bad_line: bool      # True if any bad line exists anywhere in the file

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

def add_entry(path: Path, day: date, text: str) -> None: ...
def entries_on(path: Path, day: date) -> DayView: ...
def delete_entry(path: Path, day: date, index: int) -> None: ...
```

The function bodies are the behavior in the next three subsections, not stubs.

`day` is a `datetime.date`. The store does not parse typed dates.

### Add

- Strip the text. If it is empty, raise `EmptyText` and do not create or change the file.
- Otherwise append one LF line. Do not read or rewrite existing bytes. A bad line already in the file stays as it is.
- Create the file if it is missing. Do not create parent directories. If the parent directory is missing, or the write fails, raise `CalendarWriteError`. The project directory exists when the program runs.
- Appending does not decode the bytes already in the file. Add still appends when the existing file is not valid UTF-8.

### Look up

- Missing file: `DayView((), False)`.
- If the file is not valid UTF-8, or cannot be read, raise `CalendarReadError` and leave the file unchanged.
- Return the good texts for `day` only, in file order. `ignored_bad_line` is true when any bad line exists anywhere in the file, even on another day.

### Delete

`index` is 1-based among that day's good lines, not a line number in the whole file.

- If any bad line exists anywhere in the file, raise `UnreadableLine` and leave every byte unchanged. Do this even when the requested day has no good lines.
- If the index is less than 1 or greater than that day's good-line count, raise `NotOnDay` and leave the file unchanged. This includes a missing file and a day with no appointments.
- Otherwise remove that one line. Keep every other line, including blank lines and other days, in the same order.
- Write the remaining raw lines to `path.with_name(path.name + ".tmp")` in the same directory (for the real calendar, `calendar.txt.tmp`). Terminate each line with `\n`. If no lines remain, the temporary file is empty. `os.replace` that temporary file onto `path` only after the write succeeds. If the write or the replace fails, delete the temporary file and leave `path` untouched.
- If the rewrite fails, raise `CalendarWriteError`.
- An empty result still leaves `path` in place (zero bytes), rather than deleting it.

---

## Prompt interface

```python
class InvalidDay(Exception):
    pass

class InvalidIndex(Exception):
    pass

def parse_menu(line: str) -> str | None: ...
def parse_day(line: str) -> date | None: ...
def parse_delete_index(line: str) -> int | None: ...
def format_listing(texts: Sequence[str]) -> str: ...
def run(path: Path, input_fn=input, output_fn=print) -> None: ...
```

`parse_menu` returns `"add"`, `"lookup"`, `"delete"`, `"quit"`, or `None` when the choice is not one of those four.

`parse_day` returns `None` when the stripped line is empty (cancel). It returns a `datetime.date` for a valid day. It raises `InvalidDay` for anything else.

`parse_delete_index` returns `None` when the stripped line is empty (cancel). It returns the integer when the line matches `^[1-9]\d*$`. It raises `InvalidIndex` otherwise.

`format_listing` joins `f"{n}. {text}"` with `\n`, starting at 1, with no trailing newline. It is only called when `texts` is non-empty.

`run` calls `input_fn` with the prompt string. It calls `output_fn` once per menu line and once per message. A listing is one `output_fn(format_listing(texts))` call. `output_fn` does not receive a trailing newline; `print` adds one. EOFError and KeyboardInterrupt from `input_fn` end the loop.

## Menu

Each pass prints these four lines, then waits for `input_fn("Choice: ")`. `Choice:` is the input prompt, not a fifth printed line.

```text
1. Add
2. Look up
3. Delete
4. Quit
```

`parse_menu` strips the answer. `"1"` add, `"2"` look up, `"3"` delete, `"4"` quit. Anything else, including `"add"`, `""`, and `"01"`, is invalid. The program prints `Choose 1, 2, 3, or 4.` and shows the menu again.

EOF or Ctrl+C while waiting for input exits like quit: no write, no error message.

After add, look up, or delete, the menu shows again.

### Day prompt

Prompt text: `Day (YYYY-MM-DD): `

`parse_day` strips the answer.

- Empty: cancel. Return to the menu. Print nothing. Do not call the store.
- Otherwise the text must match `^\d{4}-\d{2}-\d{2}$` and be a real day. `2024-02-29` is valid. `2026-02-29`, `2026-02-31`, `2026-9-21`, `09/21/2026`, and `tomorrow` are not.
- Invalid: print `Not a date. Use YYYY-MM-DD.` and return to the menu. Do not call the store.

### Add

1. Ask for the day. Cancel and invalid dates behave as above.
2. Prompt `Appointment: `. Strip the text. If it is empty, print `Appointment text is required.` and return to the menu without writing.
3. Call `add_entry`.
4. On `CalendarWriteError`, print `Could not write calendar.txt.`
5. On success, print `Saved.`

### Look up

1. Ask for the day.
2. Call `entries_on`.
3. On `CalendarReadError`, print `Could not read calendar.txt.` and return to the menu.
4. If `texts` is empty, print `No appointments.` Otherwise print `format_listing(texts)`.
5. If `ignored_bad_line` is true, print `Ignored a bad line in calendar.txt.` after the listing or after `No appointments.`

### Delete

1. Ask for the day.
2. Call `entries_on`.
3. On `CalendarReadError`, print `Could not read calendar.txt.` and return to the menu.
4. If `ignored_bad_line` is true, print `calendar.txt has a line I can't read. Fix or remove it, then try again.` and return to the menu. Do not print numbers and do not ask for one. This also wins over `No appointments.`
5. If `texts` is empty, print `No appointments.` and return to the menu.
6. Print `format_listing(texts)`.
7. Prompt `Number to delete: `. Strip the answer. Empty cancels back to the menu with no message and no write.
8. Otherwise the answer must match `^[1-9]\d*$` (no sign, no decimal point, no leading zero). `"01"` is invalid. If it does not match, or `delete_entry` raises `NotOnDay`, print `Not a line on that day.` and do not change the file.
9. On `UnreadableLine`, print `calendar.txt has a line I can't read. Fix or remove it, then try again.`
10. On `CalendarWriteError`, print `Could not write calendar.txt.`
11. On success, print `Deleted.`

Example. The file is Dentist, then Call the bank on the 22nd, then Lunch on the 21st. Delete on `2026-09-21`, number `2`, removes Lunch only. Dentist remains above Call the bank.

---

## Error handling

The store raises the exceptions above and does not print. The prompts turn them into the messages in the Menu section. Those message strings are exact.

A failed operation does not change the file. A successful add appends. A successful delete replaces the file as specified.

---

## Testing

Pytest. No third-party runtime dependency. `python -m pytest` from the project root.

**`tests/test_store.py`**, using a temporary directory:

- Missing file: look up returns no texts and `ignored_bad_line` is false.
- Add writes exactly `2026-09-21\tDentist at 2pm\n` in UTF-8 with LF.
- A second add appends. The first line's bytes stay put.
- Look up returns only that day, in add order. Another day is excluded.
- Two identical lines on one day both come back.
- Text with an embedded tab, and non-ASCII text such as `Café`, round-trip.
- Delete number 1 removes only the first good line of that day. Delete number 2 removes the second. Other days stay, in order.
- Delete of the last remaining line leaves a zero-byte file at that path and no `.tmp` file beside it.
- Index `0`, `-1`, or past the end raises `NotOnDay` and the file bytes are unchanged.
- Empty or whitespace-only text raises `EmptyText` and does not create or change the file.
- A blank line is skipped on look up and is still present after deleting a different line.
- A line with no tab, a line whose date is not real (`2026-02-31`), and a line with a tab but no text are bad lines. Look up omits them, still returns the good lines for the day, and sets `ignored_bad_line`.
- Delete while any bad line exists raises `UnreadableLine` and the file bytes are unchanged.
- Add while a bad line exists appends and leaves the bad line in place.
- A file that is not valid UTF-8: look up and delete raise `CalendarReadError` and the bytes are unchanged. Add still appends one line after those bytes.
- A path whose parent directory does not exist: add raises `CalendarWriteError`.
- After a successful delete, the temporary file is gone.

**`tests/test_prompts.py`:**

- `parse_menu`: `"1"` through `"4"` map to add, lookup, delete, and quit. `" 1 "` is add. `"add"`, `""`, `"5"`, and `"01"` are rejected.
- `parse_day`: a real zero-padded day returns that date. Blank returns `None`. `2024-02-29` is valid. `2026-02-29`, `2026-9-21`, `09/21/2026`, and `tomorrow` raise `InvalidDay`.
- `parse_delete_index`: `"1"` is 1, `"10"` is 10, blank returns `None`, and `"0"`, `"01"`, `"-1"`, `"1.5"`, and `"a"` raise `InvalidIndex`.
- The listing formatter produces `1. Dentist at 2pm` then `2. Lunch with Sam`.
- One scripted `run` against a temporary file, with stand-in input and output: add Dentist on `2026-09-21`, add Lunch on that day, look up the day, delete number 1, look up again, quit. The output contains both `Saved.` lines, the two-line listing, `Deleted.`, and a listing of Lunch only. The file's single line is Lunch. The run ends.
- One scripted add with the day `tomorrow` writes nothing and the output contains `Not a date. Use YYYY-MM-DD.`

The interactive console is not part of the test run.

---

## Project layout

```text
calendar/
  calendar_app/
    __init__.py
    __main__.py
    prompts.py
    store.py
  tests/
    test_store.py
    test_prompts.py
  docs/superpowers/specs/2026-09-21-calendar-design.md
  pyproject.toml
  .gitignore
```

`pyproject.toml` packages `calendar_app`, requires Python 3.11 or newer, and depends on nothing at runtime. Pytest is the test runner. `.gitignore` includes `__pycache__/`, `.pytest_cache/`, `*.pyc`, and `calendar.txt`.

Run the program with `python -m calendar_app` from the project, on an editable install or with the project root on `PYTHONPATH`.

---

## What this design does not decide

Nothing required to implement the program above is left open. Packaging an installer, a README beyond the run command, and editor tooling are out of scope.
