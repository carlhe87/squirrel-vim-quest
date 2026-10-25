# Putting Squirrel Vim Quest on itch.io

Everything to upload is made by two commands:

```
powershell -ExecutionPolicy Bypass -File packaging\build.ps1   # dist\SquirrelVimQuest-<version>-windows.zip
.venv\Scripts\python packaging\itch_assets.py                  # dist\itch\*.png
```

## 1. Create the project

Sign in at itch.io, open the menu under your name, choose **Upload new project**,
and fill in the form:

| Field | Value |
| --- | --- |
| Title | Squirrel Vim Quest |
| Project URL | `squirrel-vim-quest` |
| Short description or tagline | Learn Vim keys with Pip the squirrel. A read-aloud keyboard game for kids 6+. |
| Classification | Games |
| Kind of project | Downloadable |
| Release status | Released |
| Pricing | No payments (or "$0 or donate" if you want a tip jar) |
| Uploads | Upload `dist\SquirrelVimQuest-1.0.0-windows.zip`, then tick **Windows** next to it |
| Description | Paste the text from section 2 |
| Genre | Educational |
| Tags | vim, keyboard, typing, kids, educational, ascii, terminal, text-based |
| Cover image (right side) | `dist\itch\cover.png` (630 x 500) |
| Screenshots (right side) | `dist\itch\screen-*.png`, in number order |
| Visibility & access | **Draft** while you check the page, then **Restricted** for friends only |

Click **Save & view page** to see it.

**Friends-only access:** with **Restricted**, itch.io offers a password or a
secret link for the page. Use whichever your project settings show, and send
that to your friends. Switch to **Public** whenever you are ready for everyone.

## 2. Page description (paste into Description)

> **Pip the squirrel lost all the acorns. Help Pip get them back, and learn the Vim keys on the way!**
>
> Squirrel Vim Quest is a keyboard game for young kids, about 6 and up. Pip says every
> instruction out loud, so the child does not need to read. Each new key is shown big,
> acted out by a ghost Pip, then tried three times. Puzzles count your key presses, and
> action levels train speed.
>
> **Three islands, 15 levels**
>
> - **Arrow Island:** `h j k l`. Eat acorns, dodge a snail, escape the Fox Maze.
> - **Word River:** `w b e`. Words are logs on a river. Jump from log to log before they sink.
> - **Line Bridge:** `0 $`. Run to the ends of bridges, catch balls, and beat the Storm Bridge.
>
> The arrow keys are switched off on purpose: Pip tells you which letter to press instead.
> Every jump lands exactly where the real Vim lands.
>
> **Install**
>
> 1. Download and unzip.
> 2. Double-click `install.cmd` for Desktop and Start Menu shortcuts, or just double-click
>    `SquirrelVimQuest.exe` to play right away.
> 3. If Windows says "Windows protected your PC": click **More info**, then **Run anyway**.
>    The game is not signed by a company, so Windows asks first.
>
> **Keys:** `Space` repeats what Pip said, `Tab` opens the menu (sound, map, quit).
>
> **Needs:** Windows 10 or 11. Looks best in Windows Terminal (free in the Microsoft Store).
> Uses Windows' built-in English voice. If there is no voice, add one in
> Settings > Time & language > Speech.
>
> Progress is saved on the computer, so stars stay after you close the game.

## 3. Make the page look like the game (optional)

On the project page, click **Edit theme**:

| Setting | Value |
| --- | --- |
| Banner | `dist\itch\banner.png` |
| Background | `#0f2416` |
| Text | `#dddddd` |
| Links | `#ffd84d` |
| Buttons | `#ff8c1a` |
| Font | a monospace font if offered, else the default |

## 4. Updating later

Change `__version__` in `squirrel_vim_quest/__init__.py`, run both commands
again, then on the project's **Edit** page upload the new zip (tick **Windows**)
and delete the old one. Friends who installed it run the new `install.cmd`.
Their stars are kept.
