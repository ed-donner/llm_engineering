# Env variable should beset: PIPENV_SHELL = "powershell"
# This file goes on: <Users-Root-Folder>\Documents\WindowsPowerShell\

if ($env:PIPENV_ACTIVE -eq 1) {& $env:VIRTUAL_ENV\Scripts\activate.ps1}
