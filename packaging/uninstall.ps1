# Removes Squirrel Vim Quest: shortcuts, the PATH entry and the program folder.
# Saved stars stay in %APPDATA%\SquirrelVimQuest, so a reinstall keeps them.
$ErrorActionPreference = 'Stop'
$dest = Join-Path $env:LOCALAPPDATA 'Programs\SquirrelVimQuest'

foreach ($folder in [Environment]::GetFolderPath('Programs'), [Environment]::GetFolderPath('Desktop')) {
    Remove-Item (Join-Path $folder 'Squirrel Vim Quest.lnk') -ErrorAction SilentlyContinue
}

$userPath = [Environment]::GetEnvironmentVariable('Path', 'User')
if ($userPath) {
    $kept = $userPath -split ';' | Where-Object { $_ -and $_ -ne $dest }
    [Environment]::SetEnvironmentVariable('Path', ($kept -join ';'), 'User')
}

Remove-Item (Join-Path $dest 'SquirrelVimQuest.exe') -ErrorAction SilentlyContinue
# This script runs from inside the folder, so remove the folder just after it exits.
Start-Process cmd -WindowStyle Hidden -ArgumentList '/c', "ping -n 3 127.0.0.1 >nul & rmdir /s /q `"$dest`""

Write-Host 'Squirrel Vim Quest is removed. Saved stars are kept in' (Join-Path $env:APPDATA 'SquirrelVimQuest')
