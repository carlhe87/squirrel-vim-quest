"""Vim motions on lines of text: h j k l w b e 0 $.

The word motions follow Vim's own fwd_word / bck_word / end_word (normal.c,
textobject.c): characters are blank, punctuation or word characters, the end
of a line counts as blank, and an empty line is a word of its own for w and b.
tests/test_text_vs_vim.py checks them against a real Vim.

A cursor is (row, col, want). want is the column j and k aim for, which Vim
calls curswant: it remembers where you were when you move through short lines.
"""

from __future__ import annotations

Cursor = tuple[int, int, int]
END = 10**9  # want after $: always the end of the line

TEXT_KEYS = "hjklwbe0$"


def char_class(ch: str) -> int:
    if ch in " \t":
        return 0
    if ch.isalnum() or ch == "_":
        return 2
    return 1


class _Walker:
    """A position that steps one character at a time, like Vim's inc()/dec()."""

    def __init__(self, lines: list[str], r: int, c: int) -> None:
        self.lines, self.r, self.c = lines, r, c

    def cls(self) -> int:
        line = self.lines[self.r]
        return 0 if self.c >= len(line) else char_class(line[self.c])

    def inc(self) -> int:
        """0: moved, 2: moved onto the end of the line, 1: to the next line, -1: stuck."""
        n = len(self.lines[self.r])
        if self.c < n:
            self.c += 1
            return 0 if self.c < n else 2
        if self.r < len(self.lines) - 1:
            self.r, self.c = self.r + 1, 0
            return 1
        return -1

    def dec(self) -> int:
        """0: moved, 1: to the end of the previous line, -1: stuck at the start."""
        if self.c > 0:
            self.c -= 1
            return 0
        if self.r > 0:
            self.r -= 1
            self.c = len(self.lines[self.r])
            return 1
        return -1

    def empty_line(self) -> bool:
        return self.c == 0 and self.lines[self.r] == ""

    def done(self) -> tuple[int, int]:
        """Normal mode never rests past the last character of a line."""
        n = len(self.lines[self.r])
        return self.r, min(self.c, max(0, n - 1))


def word_forward(lines: list[str], r: int, c: int) -> tuple[int, int]:
    w = _Walker(lines, r, c)
    start_class = w.cls()
    last_line = r == len(lines) - 1
    if w.inc() == -1:
        return w.done()
    if start_class != 0:
        while w.cls() == start_class:
            i = w.inc()
            if i == -1 or (i >= 1 and last_line):
                return w.done()
    while w.cls() == 0:
        if w.empty_line():
            break
        i = w.inc()
        if i == -1 or (i >= 1 and last_line):
            return w.done()
    return w.done()


def word_backward(lines: list[str], r: int, c: int) -> tuple[int, int]:
    w = _Walker(lines, r, c)
    if w.dec() == -1:
        return w.done()
    while w.cls() == 0:
        if w.empty_line():
            return w.done()
        if w.dec() == -1:
            return w.done()
    word_class = w.cls()
    while w.cls() == word_class:
        if w.dec() == -1:
            return w.done()
    w.inc()  # overshot: step forward onto the word's first character
    return w.done()


def word_end(lines: list[str], r: int, c: int) -> tuple[int, int]:
    w = _Walker(lines, r, c)
    start_class = w.cls()
    if w.inc() == -1:
        return w.done()
    if w.cls() == start_class and start_class != 0:
        # In the middle of a word: run to its end.
        while w.cls() == start_class:
            if w.inc() == -1:
                return w.done()
    else:
        # At the end of a word: skip blanks, then run to the end of the next word.
        while w.cls() == 0:
            if w.inc() == -1:
                return w.done()
        word_class = w.cls()
        while w.cls() == word_class:
            if w.inc() == -1:
                return w.done()
    w.dec()  # overshot: step back onto the word's last character
    return w.done()


def text_move(lines: list[str], cursor: Cursor, key: str) -> Cursor:
    r, c, want = cursor
    last = max(0, len(lines[r]) - 1)
    if key == "h":
        c = max(0, c - 1)
    elif key == "l":
        c = min(last, c + 1)
    elif key in "jk":
        r2 = r + (1 if key == "j" else -1)
        if 0 <= r2 < len(lines):
            return r2, min(want, max(0, len(lines[r2]) - 1)), want
        return cursor
    elif key == "0":
        c = 0
    elif key == "$":
        return r, last, END
    elif key == "w":
        r, c = word_forward(lines, r, c)
    elif key == "b":
        r, c = word_backward(lines, r, c)
    elif key == "e":
        r, c = word_end(lines, r, c)
    else:
        raise ValueError(f"not a text motion: {key!r}")
    return r, c, c


def word_spans(lines: list[str]) -> list[tuple[int, int, int]]:
    """Every run of word characters as (row, first col, last col), in reading order."""
    spans = []
    for r, line in enumerate(lines):
        c = 0
        while c < len(line):
            if char_class(line[c]) == 2:
                start = c
                while c < len(line) and char_class(line[c]) == 2:
                    c += 1
                spans.append((r, start, c - 1))
            else:
                c += 1
    return spans
