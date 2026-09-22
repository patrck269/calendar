# Calendar, the way Grug tell it

Grug make a calendar. Grug not make a window. Grug not make a phone. Grug make a program that sit in a terminal and talk with text. You type. Grug program answer. Appointments go in one text file. You come back later, you give a day, Grug program read that day back.

This document is long because you ask Grug for exhaustive detail. Grug put every rule Grug actually build. If a sentence here and the program disagree, the program win, and this page is wrong. Grug try not to be wrong.

The program live in the project folder, wherever you put that folder. GitHub get the code. GitHub not get `calendar.txt`. That file is the pile of appointments, and Grug leave it out of git on purpose. More on that later, when Grug talk about the cave and the remote.

---

## 1. What Grug build, and what Grug not build

Grug build four actions.

1. Add. You give a day and one line of text. Grug append that line to the file.
2. Look up. You give a day. Grug print every appointment stored for that day, in the order they were added. Then Grug print a blank line so the menu not sit on the last appointment.
3. Delete. You give a day. Grug print that day's lines with numbers. You type one number. Grug remove that one line and leave every other line where it was.
4. Quit. Grug stop. Grug not rewrite the file just because you quit.

That is the whole animal. Grug not build edit-in-place. Grug not build rename. Grug not build a repeating appointment. Grug not build a separate time field. If you care about a time, you put the time in the sentence, like `Dentist at 2pm`. Grug not build a list of every saved day. Grug not build search. Grug not build a second calendar file. Grug not build reminders. Grug not build a picture of a month. Grug not understand `today`, `tomorrow`, or `9/21/2026` as dates. Grug understand `2026-09-21` and other real days written the same way.

Grug not build an installer. This program remember days. It not share code with any other program.

---

## 2. The stones in the folder

Grug split the work into two stones so the file rules can be tested without a person typing.

`calendar_app/store.py` is the stone that touch the file. It add a line. It return the lines for one day. It delete one numbered line. It never call `input`. It never call `print`. It not know about menus. You hand it a path. Tests hand it a temporary path so tests not eat your real appointments.

`calendar_app/prompts.py` is the stone that talk. It print the menu. It read a choice. It ask for a day. When you add, it ask for one line of text. It call the store. It print the result. It not know how a line is spelled on disk, except that it trust the store. `run(path, input_fn, output_fn)` is the loop. Tests pass a fake input and a list that catch output. When you run the program for real, input is `input` and output is `print`.

`calendar_app/__main__.py` is the door. You run `python -m calendar_app`. Python open that door. The door call `run` with one path: the `calendar.txt` that sit in the project root, next to `calendar_app`, not next to whatever folder your shell happen to be in. The path is `Path(__file__).resolve().parent.parent / "calendar.txt"`. `__file__` is `__main__.py`. Parent is `calendar_app`. Parent of that is the project root. So the file is `calendar.txt` in the project root, next to the `calendar_app` folder, even if you start the program from some other directory, as long as Python can import `calendar_app`.

`tests/test_store.py` poke the file stone. `tests/test_prompts.py` poke the talking stone and one scripted session. `pyproject.toml` say the package is `calendar-app`, Python must be 3.11 or newer, and pytest look at `tests` with the project root on the path. Runtime dependencies: none. Grug use the standard library only. Pytest is a tool you install so you can run tests. The calendar itself not need it.

`.gitignore` hide `__pycache__/`, `.pytest_cache/`, `*.pyc`, and `calendar.txt`. The last one matter. Your appointments not get committed when Grug commit code.

`docs/superpowers/specs/2026-09-21-calendar-design.md` is the design Grug follow. This README tell the same rules in Grug voice. The design status line still say pending review. Grug build it anyway because you tell Grug to.

---

## 3. How you wake it

Open a terminal. Go to the project folder.

```powershell
python -m calendar_app
```

Run that from the project folder, the one that contain `calendar_app` and this README.

Python must be 3.11 or newer. On the machine Grug use, `python` is 3.13. If `python` not found, Grug not hide a copy inside the folder. You need Python on the path.

The first screen is the menu. Grug print four lines, then wait:

```text
1. Add
2. Look up
3. Delete
4. Quit
Choice:
```

`Choice:` is the input prompt. It is not a fifth printed line in the code. `input` write it, then wait. You type `1`, `2`, `3`, or `4`, then Enter.

Spaces around the number are fine. ` 1 ` is add. The word `add` is not add. `01` is not add. `5` is not a choice. Empty Enter is not a choice. Grug print exactly `Choose 1, 2, 3, or 4.` and show the menu again.

After add, look up, or delete, Grug show the menu again. Grug stay open until you quit, or until the input stream end, or until you hit Ctrl+C. End of file and Ctrl+C leave like quit: no error sentence, no rewrite. If the file was mid-write, that is a different story, and Grug talk about it in the disk section. A normal quit not start a write.

---

## 4. Add, from the first key to the last byte

You type `1`. Grug ask:

```text
Day (YYYY-MM-DD):
```

You type a day. Rules for the day are in section 7. If the day is blank after Grug strip spaces, Grug cancel. Grug print nothing about the cancel. Grug go back to the menu. Grug not ask for the appointment text. Grug not touch the file.

If the day is not a real `YYYY-MM-DD` day, Grug print exactly `Not a date. Use YYYY-MM-DD.` and go back to the menu. Same thing: no appointment prompt, no write.

If the day is good, Grug ask:

```text
Appointment:
```

Grug take one line. Grug strip spaces and tabs off both ends. If nothing is left, Grug print exactly `Appointment text is required.` and go back to the menu. The file not change. A string of spaces is empty. A tab by itself is empty. Grug not store a blank appointment.

If text remain, Grug call `add_entry`. On success Grug print exactly `Saved.`

Add does not read the old file. Add open the file in append mode, UTF-8, newline set to `\n`, and write one line. If the file not exist, the first successful add create it. Grug not create missing parent folders. The project folder exist when you run the program, so this only bite a caller who pass a path whose parent is gone. Then the store raise `CalendarWriteError`, and the menu print exactly `Could not write calendar.txt.`

Because add only append, a bad line already in the file stay where it is. Add not try to understand the old bytes. Add even append after bytes that are not valid UTF-8. The new line is valid UTF-8 stuck on the end. Lookup of that file still fail until the bad bytes are gone, because lookup must read the whole file as UTF-8. Grug talk about that in section 11.

A full add look like this.

```text
1. Add
2. Look up
3. Delete
4. Quit
Choice: 1
Day (YYYY-MM-DD): 2026-09-21
Appointment: Dentist at 2pm
Saved.
1. Add
2. Look up
3. Delete
4. Quit
Choice:
```

The file, if it was missing, is now this, and the end of the line is one LF byte, not Windows CRLF:

```text
2026-09-21	Dentist at 2pm
```

The gap between the date and the words is a tab character, not spaces. Grug show it as a gap because a tab is invisible in many fonts. On disk it is the byte `0x09`.

You add a second line for the same day, `Lunch with Sam`. The file is two lines. The first line's bytes are not rewritten. They stay the prefix. The second line is stuck on the end. That is what append mean.

You add `Call the bank` on `2026-09-22`. Lookup of the 21st not show the bank. Lookup of the 22nd show only the bank. Order on a day is the order of the lines in the file, which is the order you added them, including lines for other days sitting between them. If you add Dentist, then the bank, then Lunch, the 21st reads Dentist then Lunch. The bank stay between them in the file and not in the 21st readout.

---

## 5. Look up, and the blank line you ask for

You type `2`. Grug ask for a day with the same prompt and the same rules. Blank day cancel with no message. Bad day print `Not a date. Use YYYY-MM-DD.` and return to the menu.

If the file is missing, that day has no appointments. Grug not create the file just because you look. Grug print exactly `No appointments.` Then Grug print a blank line. Then the menu.

If the file exist, Grug read it. Grug keep every good line whose date is that day. Grug keep the text after the first tab, unchanged. A hand-edited leading space stay a leading space. Lines Grug itself wrote have no surrounding whitespace, because add strip before write.

Grug print them as one block. Numbers start at 1. A period and a space, then the text. No blank line between appointments. Two appointments look like this.

```text
1. Dentist at 2pm
2. Lunch with Sam
```

Then Grug print a blank line. Then the menu. Before that blank line, the last appointment and `1. Add` were glued together and your eye trip. You tell Grug to space the readout from the menu. Grug do that only after a lookup that got as far as a readout. A cancelled day print nothing, so Grug not invent a blank line. A bad date print the error and return, and that path not add the extra blank line. A read error print `Could not read calendar.txt.` and return without the extra blank line. The blank line belong to the day's list, or to `No appointments.`, and it also come after the bad-line warning when that warning is part of the readout.

If any bad line exist anywhere in the file, not only on this day, Grug still show the good lines for the day you asked, and then Grug print exactly `Ignored a bad line in calendar.txt.` once. Then the blank line. Then the menu. One bad line on the 22nd still warn you when you look up the 21st. The warning is about the file, not about the day. If the day you asked has no good lines, you see `No appointments.` and then the warning and then the blank line.

A lookup of Dentist and Lunch, then the menu, look like this.

```text
Choice: 2
Day (YYYY-MM-DD): 2026-09-21
1. Dentist at 2pm
2. Lunch with Sam

1. Add
2. Look up
3. Delete
4. Quit
Choice:
```

That empty row is the newline you ask for. It is `output_fn("")`. `print` turn an empty string into a blank line.

---

## 6. Delete, and why the number is not a line number in the whole file

You type `3`. Grug ask for a day. Same cancel rule. Same bad-date rule.

Then Grug read the file. If the file cannot be read as UTF-8, Grug print exactly `Could not read calendar.txt.` and go back to the menu. Nothing is deleted.

If any bad line exist anywhere, Grug refuse before Grug show numbers. Grug print exactly `calendar.txt has a line I can't read. Fix or remove it, then try again.` Grug not ask for a number. This message win over `No appointments.` Even if the day you named has no good lines, a bad line somewhere else still make delete refuse. Grug refuse because delete must rewrite the file, and Grug not rewrite a file Grug not fully understand. Add can append past a bad line. Delete cannot. You fix the bad line by hand, or you remove it by hand, then you try delete again.

If the day has no good appointments and the file has no bad line, Grug print exactly `No appointments.` and not ask for a number.

If the day has good lines, Grug print the same numbered list as lookup. Then Grug ask:

```text
Number to delete:
```

The number is 1-based among that day's good lines only. It is not the line number in Notepad for the whole file. Blank lines are not numbered. Other days are not numbered. Bad lines are not numbered, and if they exist Grug never get this far.

You type `1` to remove the first appointment Grug showed. You type `2` to remove the second. `10` is ten, if ten lines exist. Spaces around the number are stripped.

Empty Enter cancel. No message. No write. You are back at the menu and the file is the same bytes.

`0` is not a line. `01` is not a line, because of the leading zero. `-1` is not a line. `1.5` is not a line. `a` is not a line. `+1` is not a line. Grug print exactly `Not a line on that day.` The file bytes stay.

A number bigger than the count is the same message. The store raise `NotOnDay`. The menu print `Not a line on that day.` Grug check the bad-line rule before the number, so a bad file never become a `NotOnDay` by mistake. A missing file is `NotOnDay` inside the store if some other caller delete without looking first. The menu look first, so you see `No appointments.` instead.

On success Grug print exactly `Deleted.`

Example. The file is Dentist on the 21st, then Call the bank on the 22nd, then Lunch on the 21st. You delete on `2026-09-21`, number `2`. Lunch go away. Dentist stay above the bank. The file is:

```text
2026-09-21	Dentist at 2pm
2026-09-22	Call the bank
```

Number `1` on that same starting file would remove Dentist and leave the bank, then Lunch. Two identical sentences on the same day are two appointments. Delete number `1` remove the first copy only. The second copy stay. Grug not match by text. Grug match by count.

Delete of the last remaining line not delete the file. The file stay, with zero bytes. The temporary file Grug use for the rewrite is gone after success.

Delete not use the blank line after the list, because the next thing is `Number to delete:`, not the menu. After `Deleted.` the menu print on the next lines. You ask for space after the daily readout. The daily readout is lookup.

---

## 7. What a day is, and every shape Grug reject

Grug strip the day you type. Then Grug demand this shape and no other: four digits, hyphen, two digits, hyphen, two digits. The pattern is `^\d{4}-\d{2}-\d{2}$`. Then the date must be a real day on the calendar.

Accepted:

- `2026-09-21`
- ` 2026-09-21 ` because strip happen first
- `2024-02-29` because 2024 is a leap year

Rejected, and the message is always `Not a date. Use YYYY-MM-DD.`:

- `2026-02-29` because 2026 is not a leap year
- `2026-02-31` because February not have 31 days
- `2026-13-01` because there is no month 13
- `2026-9-21` because the month is not two digits
- `09/21/2026` because slashes are not hyphens and the order is wrong
- `tomorrow` because Grug not a poet about dates
- `today` for the same reason
- `20260921` because the hyphens are required

Empty and whitespace-only are not errors. They are cancel.

The store never parse what you typed. The prompts turn a good string into a `datetime.date`. The store receive that date and write `day.isoformat()`, which is the same `YYYY-MM-DD` shape.

---

## 8. Every exact sentence the menu can print

Grug list them so you can search this page when the program bark.

- `Choose 1, 2, 3, or 4.`
- `Not a date. Use YYYY-MM-DD.`
- `Appointment text is required.`
- `Saved.`
- `No appointments.`
- `Ignored a bad line in calendar.txt.`
- `Not a line on that day.`
- `calendar.txt has a line I can't read. Fix or remove it, then try again.`
- `Could not write calendar.txt.`
- `Could not read calendar.txt.`
- `Deleted.`

Prompts, which are asks, not barks:

- `Choice:`
- `Day (YYYY-MM-DD):`
- `Appointment:`
- `Number to delete:`

Menu lines:

- `1. Add`
- `2. Look up`
- `3. Delete`
- `4. Quit`

The store not print any of these. The store raise. The prompts catch and print. If you call the store from another program, you get exceptions, not sentences.

`EmptyText` mean the appointment was empty after strip. `InvalidDay` mean the typed day was not a real zero-padded date. `InvalidIndex` mean the delete token was not a positive integer without a leading zero. `NotOnDay` mean the number not point at a good line on that day, or the file is missing. `UnreadableLine` mean delete refuse because a bad line exist. `CalendarReadError` mean the file is not valid UTF-8 or the disk not let Grug read. `CalendarWriteError` mean the disk not let Grug write, or the parent folder not exist. They all inherit `StoreError` except `InvalidDay` and `InvalidIndex`, which belong to the prompts.

---

## 9. The file, byte by byte

Name: `calendar.txt`. Place: project root. Encoding: UTF-8. No byte-order mark. One appointment per line. Each line Grug write is the date, one tab, the text, then `\n`. Grug not write `\r\n` even on Windows. Append and the delete rewrite open with `encoding="utf-8"` and `newline="\n"`, so Python not translate `\n` into the Windows newline.

Reading is different. Lookup and delete open with `newline=None`. That is universal newlines. A file you edit in Notepad, which save CRLF, still parse. `\r\n` and `\n` both become logical lines. If delete then rewrite, the file become LF only. Grug normalize on the way out.

A missing file mean no appointments. Lookup not create it. The first successful add create it.

Grug not keep a second file, except a temporary file during delete. That temporary file is the same name plus `.tmp`. For `calendar.txt` it is `calendar.txt.tmp` in the same folder. Grug write the kept lines there, each ended by `\n`. If no lines remain, the temporary file is empty. Then `os.replace` put it on top of `calendar.txt`. Replace is the moment the real file change. If the write fail, or the replace fail, Grug try to delete the temporary file and leave the original `calendar.txt` alone, then raise `CalendarWriteError`. The menu say `Could not write calendar.txt.` After a good delete, the `.tmp` file is gone because replace move it.

An empty result still leave `calendar.txt` in place as a zero-byte file. Grug not unlink it. Next add append to that empty file and it is a normal one-line file again.

---

## 10. Good lines, blank lines, and bad lines

Grug classify every line when Grug read.

A line that is empty, or only space characters, is blank. Tabs are not spaces for this test. Grug use strip of the space character only. A blank line is not an appointment. A blank line is not a bad line. Lookup skip it. Delete keep the raw blank line where it was, including a line that is three spaces. A file that is a blank line, then Dentist, then three spaces, then the bank, still show only Dentist for the 21st, and `ignored_bad_line` is false. Delete Dentist and the blank lines stay, and the bank stay.

A good line is a real `YYYY-MM-DD` date, a tab, and text whose stripped form is not empty. The stored text is everything after the first tab. If the text contain another tab, that tab is part of the text. `Café` round-trip. `Café`, tab, `with Sam` is one appointment whose text is `Café`, tab, `with Sam`. Add strip the ends, so the program not write surrounding space, but a hand edit of `2026-09-21`, tab, two spaces, `Dentist`, two spaces, is still a good line and lookup show the spaces.

A bad line is any other non-blank line. No tab. A tab with nothing after it. A tab with only whitespace after it. A date that is not real, like `2026-02-31`, tab, `Nope`. A date with a space before the tab. `2026-9-21` without the zero. A sentence with no date.

One bad line mark the whole file. Lookup of any day set `ignored_bad_line` true, omit the bad line from the numbers, and still return the good lines for the day you asked. Delete raise `UnreadableLine` and not change one byte.

`\t` alone is not a blank line, because a tab is not a space. It is a bad line: a tab with empty text.

---

## 11. When the bytes are rotten

If the file contain a byte that is not UTF-8, lookup raise `CalendarReadError` and the menu say `Could not read calendar.txt.` Delete do the same and not change the bytes. Add still append, because add not decode the old bytes. You can end with rotten bytes, then a good new line. Lookup still fail until you remove the rotten prefix. Grug not try to guess the encoding. Grug not skip a bad byte and read the rest. The whole read fail.

If the parent directory of the path not exist, add raise `CalendarWriteError` and not create the directory and not create the file.

If the path exist but is a directory, read fail as an operating-system error and become `CalendarReadError`.

---

## 12. A long session, start to finish

Grug write the keys, then what you see, then what the file is. Start with no `calendar.txt`.

Keys: `1`, `2026-09-21`, `Dentist at 2pm`, `1`, `2026-09-21`, `Lunch with Sam`, `2`, `2026-09-21`, `3`, `2026-09-21`, `1`, `2`, `2026-09-21`, `4`.

You see `Saved.` twice. You see both lines numbered. You see `Deleted.` You see a later listing that is only `1. Lunch with Sam`. You not see Dentist after the delete. The file's single line is `2026-09-21`, tab, `Lunch with Sam`, LF.

Same keys a second time, from a missing file again, make the same output and the same bytes. Grug check that.

Keys: `1`, `tomorrow`, `4`. You see `Not a date. Use YYYY-MM-DD.` The file is not created.

Keys: `1`, `2026-09-21`, three spaces, `4`. You see `Appointment text is required.` The file is not created.

Keys: `add`, `4`. You see `Choose 1, 2, 3, or 4.` The file is not created.

Keys: `1`, `2026-09-21`, `Dentist at 2pm`, `3`, `2026-09-21`, `2`, `4`. You see `Not a line on that day.` The file is still the one Dentist line.

Quit on a file that already has bytes: the bytes after quit equal the bytes before quit.

---

## 13. What the tests hold down

Grug run `python -m pytest` from the project root. The tests call the real `add_entry`, `entries_on`, `delete_entry`, `parse_menu`, `parse_day`, `parse_delete_index`, `format_listing`, and `run`. They not copy the rules into the test and then grade the copy.

The store tests, on a temporary directory, hold these things down.

A missing file has no appointments and `ignored_bad_line` is false, and the file still not exist.

Add of Dentist on `2026-09-21` write exactly the UTF-8 LF bytes of that date, a tab, `Dentist at 2pm`, and a newline.

A second add append. The first line's bytes stay the prefix. Lookup return only that day, in add order. Another day is excluded.

Two identical lines are two appointments. Delete number 1 remove only the first. The other day stay in its place.

Text with an embedded tab, and `Café`, round-trip.

Delete number 2 leave the earlier line and the other day.

Delete of the last line leave a zero-byte file and no `.tmp` beside it.

Index `0`, `-1`, and past the end raise `NotOnDay` and the bytes are unchanged.

Delete on a missing file raise `NotOnDay`.

Empty text, spaces, and a tab raise `EmptyText` and not change an existing file.

A blank line is skipped on lookup and is still there after another line is deleted.

A line with no tab, a line dated `2026-02-31`, and a line with a tab but no text, are bad. Lookup omit them, still return the good lines, and set the flag. A tab and only spaces is bad too.

Delete while any bad line exist raise `UnreadableLine` and the bytes match, even when the bad line is on another day and the day you named has no entry you can delete.

Add while a bad line exist append and leave the bad line in place.

A file that start with `0xFF` is not UTF-8. Lookup and delete raise `CalendarReadError` and the bytes stay. Add still append a good line after those bytes.

A CRLF file is read. Dentist come back without a stray carriage return. Delete of the other day rewrite LF only.

Add whose parent folder is missing raise `CalendarWriteError` and not create the file.

The prompt tests hold the menu words, the day parser, the leap day, the rejected shapes, the delete-number parser, and the listing format `1. Dentist at 2pm` newline `2. Lunch with Sam` with no extra newline at the end of that string.

One scripted `run` do the Dentist, Lunch, lookup, delete 1, lookup, quit session and check the file.

One scripted add of `tomorrow` write nothing.

Unknown menu choice, empty appointment, out-of-range delete, and quit are checked against the file bytes.

Lookup of a bad file print the ignored-line sentence, and delete print the can't-read sentence, and the bytes stay.

EOF on the first `Choice:` print the four menu lines and not create a file.

The blank line after a real listing is checked: the output after `1. Dentist at 2pm` is an empty string, and the output after that is `1. Add`.

The interactive console is not part of the test run. Tests not wait for your keyboard.

---

## 14. How the two stones share work

You can call the store without the menu. That is what tests do, and what a script may do.

`add_entry(path, day, text)` want a `datetime.date` and a string. It strip. It append. It not return the new list.

`entries_on(path, day)` return a `DayView`. `texts` is a tuple of strings. `ignored_bad_line` is true or false. Missing file return an empty tuple and false.

`delete_entry(path, day, index)` return nothing. It raise when it refuse. Index is 1-based. It not print.

`format_listing` join `f"{n}. {text}"` with newlines, start at 1, no trailing newline. Grug only call it when the tuple is not empty.

`run` loop until quit, EOF, or Ctrl+C. Each pass print the four menu lines, then read `Choice:`. Unknown choice print the choose-sentence and continue. `4` return. `1` add. `2` lookup. `3` delete.

Grug not put file format in the prompts. If the tab rule change, it change in `_classify` and in the one line `add_entry` write. The menu keep printing sentences.

---

## 15. Hand edits Grug tolerate, and hand edits Grug not

You may open `calendar.txt` in an editor.

You may add a blank line. Grug skip it and, on delete of something else, keep it.

You may save CRLF. Grug read it. The next delete rewrite LF.

You may put tabs inside the appointment text. Grug split on the first tab only.

You may put `Café` or any other Unicode that is valid UTF-8.

You may put spaces in the text after the tab. Lookup show them.

You must not put a second appointment on the same physical line. One line, one appointment.

You must not forget the tab. That line become bad, lookup warn, delete refuse.

You must not write `2026-02-31`. That line is bad.

You must not leave a tab and no words. That line is bad.

If delete refuse, Grug not fix the file for you. You repair the bad line. Then delete work again. Add still work while the bad line sit there, which can make the file longer and still unreadable to delete. Grug accept that. Append is safe. Rewrite is not, until the file is clean.

---

## 16. The pile already in the cave, and why GitHub not have it

On the machine where Grug work, `calendar.txt` already hold appointments. Grug once add 800 lines on random days from `2026-01-01` through `2027-12-31`, with short labels. Grug later add 25000 sentences on `2026-09-22`. That day already had 2 lines, so that day hold 25002 after the add. The sentences are cringeworthy meme talk, each one a full sentence, each one different. They are not in git.

`.gitignore` say `calendar.txt` not get committed. `git add` not see it. `git push` not send it. A person who clone the GitHub repo get the program and not your pile. The first time they add, their own `calendar.txt` appear beside the code.

Grug do this so a later real appointment, a name, a place, not fly to GitHub because Grug push code. The meme pile is silly, not secret, but the rule is one rule for the whole file. Grug not split silly lines from serious lines. The file is local.

If you want the pile on GitHub, you must say so. Grug not force-add a gitignored file because a push of code feel like a push of everything.

---

## 17. Git, main, and the word fork

The code history on the machine is three commits when this README land, plus the commit that add this README.

The design spec commit come first. Then the program and the tests. Then the blank line after lookup, with the test that watch for that blank line. Then this document.

The branch is `main`. Grug rename `master` to `main` because you say Grug only work on main. Grug not make a side branch. Grug not know a fork as a thing Grug use. A fork, if some other human say the word, is their copy of a repo under their own name. Grug not copy someone else's repo. Grug push this repo to GitHub as its own repo, branch `main`.

Grug not push until you say push. The first time you ask why GitHub was empty, the reason was: no remote, no ask, and the appointment file ignored. Then you say push. Grug commit what is not ignored, and Grug push `main`.

---

## 18. Failure, and what the bytes are after

Grug want this list burned in, because it is the promise.

A bad day not write. An empty appointment not write. A bad menu choice not write. A delete number that is not on the list not write. Quit not write. Cancel on the day prompt not write. Cancel on the delete number not write. EOF not write. Ctrl+C not write.

A bad line not get deleted by the delete command, and the good lines not get rewritten either. The file bytes match what they were before the refuse.

A failed delete that die during the temporary write leave the original file intact if the replace not happen. Grug try to remove the `.tmp` file. Grug not promise a crash in the middle of `os.replace` on every operating system, but Grug not truncate `calendar.txt` first and hope. Grug write the new copy beside it, then replace.

A successful add only make the file longer by one LF line. Old bytes stay a prefix, unless the file was missing and this add create it.

A successful delete replace the file with the kept lines in the same order, blank lines included, the chosen good line gone, LF endings, no `.tmp` left behind.

---

## 19. Small things people ask, and the short answer

Can Grug show a month? No.

Can Grug search for Dentist? No. You look up the day.

Can two appointments say the same words? Yes. They are two lines.

Can the text be long? Yes, until the disk complain. It must be one line. A newline in the text would be a second line and would break the format. The menu use `input`, which stop at Enter, so the menu not put a newline inside the text.

Can you run two copies at once on the same file? Grug not lock the file. Two adds can interleave. Two deletes can lose a line. Grug assume one person, one program.

Does the current directory matter? The door in `__main__.py` not use the current directory for the data file. It use the folder above the package. Tests pass their own path. If you import `run` and pass a path, that path is the file.

Does Grug sort the day? No. File order is add order. Grug not sort by time because time is just words.

Does lookup print a blank line when the day is empty? Yes. `No appointments.` then a blank line, then the menu. If a bad line also exist, the warning sit between `No appointments.` and the blank line.

Does delete print that blank line? No.

Is `2026-09-21 ` with a trailing space a valid day? Yes, after strip.

Is `2026-09-21` with a trailing tab a valid day? Strip remove the tab too. It become the date. It is valid.

---

## 20. If you are Grug, reading this next year

Wake the program from the project folder with `python -m calendar_app`. Type `2`. Type the day as `YYYY-MM-DD`. Read the list. The blank line under the list is on purpose. Type `4` when you are done. If you need to throw one line away, type `3`, same day, then the number Grug showed. If Grug say the file has a line Grug can't read, open `calendar.txt`, find the line that is not a real date, a tab, and some text, and fix that line before you delete. Your appointments are in that file beside the code, and they are not on GitHub unless you later tell Grug to put them there.
