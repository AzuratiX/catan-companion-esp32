param(
    [string]$Port = "",
    [switch]$TestLcd
)

$CoreFiles = @(
    "config.py",
    "lcd_api.py",
    "i2c_lcd.py",
    "hardware.py",
    "game.py",
    "main.py"
)

$AllFiles = $CoreFiles + @("debug_lcd.py", "debug_hw.py")
$Files = if ($TestLcd) { $AllFiles } else { $CoreFiles }

$Missing = $Files | Where-Object { -not (Test-Path $_) }
if ($Missing) {
    throw "Missing files: $($Missing -join ', ')"
}

if ($Port) {
    Write-Host "Deploying to $Port ..."
} else {
    Write-Host "Deploying (auto port) ..."
    $Port = "auto"
}

Write-Host "  -> $($Files -join ', ')"

# mpremote needs "+" between each command in one session
$MpArgs = @("connect", $Port)
for ($i = 0; $i -lt $Files.Count; $i++) {
    if ($i -gt 0) {
        $MpArgs += "+"
    }
    $MpArgs += "cp"
    $MpArgs += $Files[$i]
    $MpArgs += ":"
}
$MpArgs += "+"
$MpArgs += "reset"

& mpremote @MpArgs
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Deploy failed. Try:" -ForegroundColor Yellow
    Write-Host "  1. Unplug/replug USB" -ForegroundColor Yellow
    Write-Host "  2. Get-Process python* | Stop-Process -Force" -ForegroundColor Yellow
    Write-Host "  3. .\deploy.ps1 -Port COM7" -ForegroundColor Yellow
    exit 1
}

Write-Host "Done. Board reset - main.py should be running on the LCD."

if ($TestLcd) {
    Write-Host "Running LCD test..."
    $TestArgs = @(
        "connect", $Port,
        "+", "cp", "debug_lcd.py", ":",
        "+", "soft-reset",
        "+", "exec", 'exec(open("debug_lcd.py").read())',
        "+", "reset"
    )
    & mpremote @TestArgs
}
