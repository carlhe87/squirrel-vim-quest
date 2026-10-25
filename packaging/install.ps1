# Installs Squirrel Vim Quest for this Windows user. No admin rights needed.
#  - copies SquirrelVimQuest.exe to %LOCALAPPDATA%\Programs\SquirrelVimQuest
#  - adds Start Menu and Desktop shortcuts
#  - adds that folder to this user's PATH, so `SquirrelVimQuest` runs in any terminal
$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$dest = Join-Path $env:LOCALAPPDATA 'Programs\SquirrelVimQuest'
$exe = Join-Path $dest 'SquirrelVimQuest.exe'

New-Item -ItemType Directory -Force $dest | Out-Null
foreach ($name in 'SquirrelVimQuest.exe', 'uninstall.ps1', 'uninstall.cmd') {
    $file = Join-Path $here $name
    Unblock-File $file -ErrorAction SilentlyContinue  # downloaded files are marked as "from the internet"
    Copy-Item $file $dest -Force
}

$shell = New-Object -ComObject WScript.Shell
foreach ($folder in [Environment]::GetFolderPath('Programs'), [Environment]::GetFolderPath('Desktop')) {
    $link = $shell.CreateShortcut((Join-Path $folder 'Squirrel Vim Quest.lnk'))
    $link.TargetPath = $exe
    $link.WorkingDirectory = $dest
    $link.IconLocation = "$exe,0"
    $link.Description = 'Learn Vim motions with Pip the squirrel'
    $link.Save()
}

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
$parts = @(if ($userPath) { $userPath -split ';' | Where-Object { $_ } })
if ($parts -notcontains $dest) {
    [Environment]::SetEnvironmentVariable('Path', (($parts + $dest) -join ';'), 'User')
}

Write-Host ''
Write-Host 'Squirrel Vim Quest is installed.' -ForegroundColor Green
Write-Host '  Play: the "Squirrel Vim Quest" icon on the Desktop or in the Start Menu,'
Write-Host '        or type SquirrelVimQuest in a new terminal window.'
Write-Host "  Installed in: $dest"
