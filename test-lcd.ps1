param(
    [string]$Port = "COM7"
)

Write-Host "LCD test on $Port"

$Args = @(
    "connect", $Port,
    "+", "cp", "debug_lcd.py", ":",
    "+", "soft-reset",
    "+", "exec", 'exec(open("debug_lcd.py").read())',
    "+", "reset"
)
& mpremote @Args

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed - close terminal with Ctrl+C if stuck, unplug USB, retry." -ForegroundColor Yellow
    exit 1
}
Write-Host "Done."
