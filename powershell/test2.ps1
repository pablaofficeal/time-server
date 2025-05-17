$paths = @(
    "$env:TEMP\*",
    "$env:WINDIR\Temp\*",
    "$env:LOCALAPPDATA\Temp\*"
)
foreach ($path in $paths) {
    Remove-Item $path -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Output "Очистка завершена!"
