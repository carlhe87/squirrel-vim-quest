# Changelog

## 1.0.1 (2026-10-25)

**Fix:** starting the game from the Desktop or Start Menu shortcut, or by
double-clicking `SquirrelVimQuest.exe`, crashed with "No such file or directory
... strings\en.yaml". The game reopens itself in Windows Terminal, and that new
copy was looking for its files in the first copy's temporary folder, which
Windows had already removed. The new copy now starts fresh.

If you installed 1.0.0: download 1.0.1, unzip, and run `install.cmd` again.
Your stars are kept.

## 1.0.0 (2026-10-25)

First release. A keyboard game that teaches Vim motions to kids about 6 and up.
Pip the squirrel is the cursor, and every instruction is read aloud.

**Download:** `SquirrelVimQuest-1.0.0-windows.zip` below. Unzip, then
double-click `install.cmd` for shortcuts, or `SquirrelVimQuest.exe` to play
straight away. Windows 10 or 11, nothing else needed.

### Three islands, 15 levels

- **Arrow Island** (`h j k l`): meet the keys, two puzzles, Acorn Garden with a
  slow snail, and the Fox Maze boss.
- **Word River** (`w b e`): words are logs on a river. Frog River with sinking
  logs, a bonus `e` level, and the Fish Rapids boss.
- **Line Bridge** (`0 $`): Ping-Pong on two bridges, and the Storm Bridge boss
  where the wind clears a bridge.

### For kids

- Every line is spoken with Windows' built-in English voice; `Space` repeats it.
- Puzzles count key presses against a par, and show the faster way after a slow solve.
- Arrow keys are switched off on purpose, with a spoken hint for the right letter.
- No game over: bumps send Pip back, never lose progress. Stars are saved.

### Under the hood

- Word and line motions land exactly where real Vim lands (checked against Vim 9.1
  in the tests).
- One-file Windows exe (no Python needed), per-user installer and uninstaller.

### Known limits

- The exe is not code-signed: the first run shows "Windows protected your PC".
  Click **More info**, then **Run anyway**.
- English only for now. All text and speech is in `strings/en.yaml`, ready for
  translation.
