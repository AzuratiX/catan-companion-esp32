# CATAN ESP32 MicroPython Companion Box

Handheld game assistant for **3–6 player CATAN** sessions. Built on an ESP32 NodeMCU-32S with a 16×2 I2C LCD, four buttons, three status LEDs, and a buzzer.

Manages rounds, player turns, dice rolls (with animation), robber (7) events, resource-gather pauses, and per-turn countdown timers.

---

## Features

- **Setup:** player count (3–6) and turn timer (15–180 s, 15 s steps)
- **Dice roll:** animated random dice + 3 s result display
- **Robber (7):** red LED, alarm, confirm with MAIN
- **Resources (≠7):** 8 s gather countdown, then main turn timer
- **Turn timer:** yellow LED + warning beeps at ≤10 s; MAIN ends turn early; BACK adds +30 s
- **HOME:** force reset to setup from any state (GPIO 32)

---

## Hardware

| Component | Details |
|-----------|---------|
| MCU | ESP32 NodeMCU-32S (3.3 V logic) |
| Display | 16×2 LCD + PCF8574 I2C backpack (typ. address `0x27`) |
| Buttons | 4× tactile switches, active LOW, internal pull-ups |
| LEDs | Green / Yellow / Red + 220–330 Ω resistors |
| Buzzer | Active or passive on PWM GPIO 18 |

**State machine / workflow:** [docs/WORKFLOW.md](docs/WORKFLOW.md)

### Pin map (default)

| Function | GPIO | Notes |
|----------|------|--------|
| I2C SDA | 21 | LCD backpack |
| I2C SCL | 22 | LCD backpack |
| MAIN | 13 | Roll / confirm robber / end turn |
| SELECT | 14 | Setup increment / menu |
| BACK | 12 | Setup decrement / +30 s timer |
| HOME | 32 | Restart to setup |
| LED green | 25 | Active turn |
| LED yellow | 26 | Low time warning |
| LED red | 27 | Robber / time up |
| Buzzer | 18 | PWM tones |

LCD **VCC → 5 V (VIN)**, **GND → GND**. Adjust contrast on the blue potentiometer on the I2C module.

---

## Software structure

```
main.py          Entry point, 10 ms loop
game.py          Setup + game state machine
hardware.py      Buttons, LEDs, buzzer, LCD wrapper
config.py        Pins and timing constants
lcd_api.py       HD44780 API (dhylands/python_lcd)
i2c_lcd.py       PCF8574 I2C driver
deploy.ps1       Upload firmware to ESP32 (Windows)
test-lcd.ps1     Quick LCD test
debug_lcd.py     Standalone LCD test script
debug_hw.py      I2C / backlight hardware diagnostic
```

---

## Quick start

### 1. Flash MicroPython on ESP32

Download **ESP32 Generic** firmware from [micropython.org](https://micropython.org/download/ESP32_GENERIC/) and flash with esptool or Thonny.

### 2. Install mpremote (PC)

```powershell
pip install mpremote
```

### 3. Deploy

```powershell
cd D:\ESP32\Catan
.\deploy.ps1 -Port COM7
```

Replace `COM7` with your port (`[System.IO.Ports.SerialPort]::getportnames()`).

If the port is stuck after a test:

```powershell
Get-Process python* | Stop-Process -Force
```

### 4. LCD test only

```powershell
.\test-lcd.ps1 -Port COM7
```

---

## Controls

### Setup

| Button | Players screen | Timer screen |
|--------|----------------|--------------|
| SELECT | +1 player (3→6 wrap) | +15 s |
| BACK | −1 player | −15 s |
| MAIN | Next screen | Start game |
| HOME | Reset to setup | Reset to setup |

### In-game

| Button | Action |
|--------|--------|
| MAIN | Roll dice → confirm robber → **end turn** (countdown only) |
| BACK | +30 s (main countdown only) |
| HOME | Force return to setup (any phase) |

Buttons are ignored during dice-result pause and resource gather (except HOME).

---

## License

This project is provided as-is for personal and educational use. CATAN is a trademark of its respective owners; this device is an unofficial fan accessory.

---

## Acknowledgments

- LCD driver based on [dhylands/python_lcd](https://github.com/dhylands/python_lcd)
