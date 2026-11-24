"""Generate the Python modules and resources that are not versioned.

* Qt Designer `.ui` files -> `*_gui.py` modules (pyside6-uic)
* Qt resource `.qrc` files -> `*_rc.py` modules (pyside6-rcc)
* the master translation table -> `.qm` translation files (pyside6-lrelease)

Run it from anywhere, in the project environment: `mise run generate`, or
`uv run python scripts/generate.py`. Only the Python standard library and the
PySide6 command-line tools are used, so it works the same on every OS.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PYTHON_SRC = ROOT / "src" / "main" / "python" / "main" / "ayab"
TRANSLATIONS = ROOT / "src" / "main" / "resources" / "base" / "ayab" / "translations"
MASTER_TSV = TRANSLATIONS / "ayab-translation-master.tsv"

# pyside6-uic does not annotate setupUi(); mypy (strict) needs a return type
# (\r?): pyside6-uic writes CRLF line endings on Windows
SETUP_UI = re.compile(r"^([ \t]*def setupUi\([^)\n]*\)):(\r?)$", re.MULTILINE)


def run(tool: str, *args: str | Path) -> None:
    executable = shutil.which(tool)
    if executable is None:
        sys.exit(
            f"{tool} not found: run this script in the project environment"
            " (`mise run generate` or `uv run python scripts/generate.py`)"
        )
    subprocess.run([executable, *map(str, args)], check=True)


def generate_ui() -> None:
    for ui_file in sorted(PYTHON_SRC.rglob("*.ui")):
        py_file = ui_file.with_suffix(".py")
        run("pyside6-uic", ui_file, "-o", py_file)
        # newline="": keep the line endings written by pyside6-uic
        with open(py_file, encoding="utf-8", newline="") as f:
            code = f.read()
        with open(py_file, "w", encoding="utf-8", newline="") as f:
            f.write(SETUP_UI.sub(r"\1->None:\2", code))


def generate_resources() -> None:
    for qrc_file in sorted(PYTHON_SRC.rglob("*.qrc")):
        run("pyside6-rcc", qrc_file, "-o", qrc_file.with_suffix(".py"))


def ts_message(source: str, translation: str) -> list[str]:
    if translation:
        translation_line = f"        <translation>{translation}</translation>"
    else:
        translation_line = '        <translation type="unfinished"></translation>'
    return [
        "    <message>",
        f"        <source>{source}</source>",
        translation_line,
        "    </message>",
    ]


def ts_content(language: str, column: int, entries: list[list[str]]) -> str:
    """Qt Linguist `.ts` file for the language of the given table column.

    Consecutive entries with the same context are grouped in one <context>.
    """
    lines = [
        '<?xml version="1.0" encoding="utf-8"?>',
        "<!DOCTYPE TS>",
        f'<TS version="2.1" language="{language}">',
    ]
    last_context = ""
    for entry in entries:
        context, source = entry[0], entry[1]
        if context != last_context:
            if last_context:
                lines.append("</context>")
            lines += ["<context>", f"    <name>{context}</name>"]
            last_context = context
        translation = entry[column] if column < len(entry) else ""
        lines += ts_message(source, translation)
    lines += ["</context>", "</TS>"]
    return "\n".join(lines) + "\n"


def generate_translations() -> None:
    """Create one `.qm` file per language column of the master table.

    The table is tab-separated: a `Context` column, then one column per
    language, the first of which (en_US) is also the source text. Cells are
    already XML-escaped (e.g. `&lt;br&gt;`), so they are written as is.
    """
    with open(MASTER_TSV, encoding="utf-8") as f:
        rows = [line.rstrip("\r\n").split("\t") for line in f]
    headers, entries = rows[0], rows[1:]

    with tempfile.TemporaryDirectory() as tmp:
        for column, language in enumerate(headers[1:], start=1):
            ts_file = Path(tmp) / f"ayab_trans.{language}.ts"
            ts_file.write_text(ts_content(language, column, entries), encoding="utf-8")
            qm_file = TRANSLATIONS / f"ayab_trans.{language}.qm"
            run("pyside6-lrelease", "-silent", ts_file, "-qm", qm_file)


def main() -> None:
    generate_ui()
    generate_resources()
    generate_translations()


if __name__ == "__main__":
    main()
