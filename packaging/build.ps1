# Builds the game for sharing:
#   dist\SquirrelVimQuest.exe                     one file, no Python needed
#   dist\SquirrelVimQuest-<version>-windows.zip   exe + installer + PLAYERS.txt
# Run:  powershell -ExecutionPolicy Bypass -File packaging\build.ps1
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$py = Join-Path $root '.venv\Scripts\python.exe'

if (-not (Test-Path $py)) {
    python -m venv .venv
    & $py -m pip install -e '.[dev]'
}

Write-Host '== tests' -ForegroundColor Cyan
& $py -m pytest -q
if ($LASTEXITCODE) { throw 'tests failed' }

Write-Host '== exe' -ForegroundColor Cyan
& $py packaging\make_icon.py
& $py -m PyInstaller --noconfirm --clean --distpath dist --workpath build packaging\SquirrelVimQuest.spec
if ($LASTEXITCODE) { throw 'PyInstaller failed' }

Write-Host '== self-check of the exe' -ForegroundColor Cyan
& dist\SquirrelVimQuest.exe --check
if ($LASTEXITCODE) { throw 'self-check failed' }

Write-Host '== zip' -ForegroundColor Cyan
$version = & $py -c 'import squirrel_vim_quest as s; print(s.__version__)'
$stage = Join-Path 'dist' "SquirrelVimQuest-$version"
Remove-Item -Recurse -Force $stage -ErrorAction SilentlyContinue
New-Item -ItemType Directory $stage | Out-Null
Copy-Item dist\SquirrelVimQuest.exe, packaging\install.ps1, packaging\install.cmd, packaging\uninstall.ps1, packaging\uninstall.cmd, packaging\PLAYERS.txt $stage
$zip = Join-Path 'dist' "SquirrelVimQuest-$version-windows.zip"
Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip -Force
Write-Host "Done: $zip" -ForegroundColor Green
