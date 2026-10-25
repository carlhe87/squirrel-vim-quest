"""Our text motions must land exactly where a real Vim lands.

Random texts (words, punctuation, runs of spaces, an empty line) and random key
sequences go to one headless Vim run; each case compares the final cursor.
Skipped when no vim is on PATH.
"""

import random
import shutil
import subprocess

import pytest

from squirrel_vim_quest.engine.text import text_move

VIM = shutil.which("vim")
WORDS = ["cat", "sun", "big", "dog", "a", "i", "red", "hat", "x_y", "go2"]
PUNCT = [".", ",", "!", "--", "?"]


def random_text(rng: random.Random) -> list[str]:
    lines = []
    for _ in range(rng.randint(1, 4)):
        if lines and rng.random() < 0.15:
            lines.append("")
            continue
        parts = []
        for _ in range(rng.randint(1, 6)):
            if rng.random() < 0.2:
                parts.append(rng.choice(PUNCT))
            else:
                parts.append(rng.choice(WORDS))
        line = (" " * rng.randint(0, 2)) + "".join(p + " " * rng.randint(0, 3) for p in parts)
        lines.append(line.rstrip() if rng.random() < 0.7 else line)
    return lines


def make_cases(n: int = 1500, seed: int = 7):
    rng = random.Random(seed)
    cases = []
    for _ in range(n):
        lines = random_text(rng)
        r = rng.randrange(len(lines))
        c = rng.randrange(max(1, len(lines[r])))
        keys = "".join(rng.choice("wbewbejkhl0$") for _ in range(rng.randint(1, 5)))
        cases.append((lines, r, c, keys))
    return cases


def vim_results(cases, tmp_path) -> list[tuple[int, int]]:
    script = ["let out = []"]
    for lines, r, c, keys in cases:
        items = ", ".join("'" + ln.replace("'", "''") + "'" for ln in lines)
        script += [
            "%delete _",
            f"call setline(1, [{items}])",
            f"call cursor({r + 1}, {c + 1})",
            # One normal! per key: in one sequence, a key that can't move
            # (k on the top line) makes Vim drop the keys after it.
            *[f"exe \"normal! {key}\"" for key in keys],
            "call add(out, (line('.') - 1) . ' ' . (col('.') - 1))",
        ]
    out_file = tmp_path / "out.txt"
    script += [f"call writefile(out, '{out_file.as_posix()}')", "qa!"]
    script_file = tmp_path / "cases.vim"
    script_file.write_text("\n".join(script), encoding="utf-8")
    subprocess.run(
        [VIM, "-N", "-u", "NONE", "-i", "NONE", "-n", "-es", "-S", script_file.as_posix()],
        check=False,
        timeout=60,
        stdin=subprocess.DEVNULL,
    )
    rows = out_file.read_text(encoding="utf-8").split()
    return [(int(rows[i]), int(rows[i + 1])) for i in range(0, len(rows), 2)]


@pytest.mark.skipif(VIM is None, reason="vim not installed")
def test_motions_match_real_vim(tmp_path):
    cases = make_cases()
    expected = vim_results(cases, tmp_path)
    assert len(expected) == len(cases)
    failures = []
    for (lines, r, c, keys), want in zip(cases, expected):
        cursor = (r, c, c)
        for key in keys:
            cursor = text_move(lines, cursor, key)
        if cursor[:2] != want:
            failures.append(f"{lines!r} from {(r, c)} keys {keys!r}: ours {cursor[:2]}, vim {want}")
    assert not failures, f"{len(failures)} mismatches, first: " + "\n".join(failures[:5])
