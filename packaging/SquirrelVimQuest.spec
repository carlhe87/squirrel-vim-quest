# PyInstaller spec: one SquirrelVimQuest.exe with the level and string files inside.
# Build with packaging\build.ps1 (it runs: pyinstaller packaging\SquirrelVimQuest.spec).
import os

from PyInstaller.utils.hooks import collect_all

ROOT = os.path.abspath(os.path.join(SPECPATH, ".."))
PKG = os.path.join(ROOT, "squirrel_vim_quest")

datas = [
    (os.path.join(PKG, "levels"), "squirrel_vim_quest/levels"),
    (os.path.join(PKG, "strings"), "squirrel_vim_quest/strings"),
]
binaries = []
hiddenimports = ["comtypes.client"]
# Textual loads widgets and styles by name at run time; take all of it.
for package in ("textual", "rich"):
    d, b, h = collect_all(package)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    [os.path.join(SPECPATH, "launcher.py")],
    pathex=[ROOT],
    datas=datas,
    binaries=binaries,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "pytest", "PyInstaller"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="SquirrelVimQuest",
    icon=os.path.join(SPECPATH, "acorn.ico"),
    console=True,
    upx=False,
)
