"""Run the calendar menu against calendar.txt in the project root."""

from pathlib import Path

from calendar_app.prompts import run


def main() -> None:
    run(Path(__file__).resolve().parent.parent / "calendar.txt")


if __name__ == "__main__":
    main()
