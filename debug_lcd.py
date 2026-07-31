"""Simple LCD test — standalone, safe to copy to the board.

Prefer (does not leave REPL open as long):
  .\test-lcd.ps1 -Port COM7
"""

import time
from machine import I2C, Pin

I2C_SDA = 21
I2C_SCL = 22
I2C_FREQ = 50000
LCD_ADDR = 0x27

MASK_RS = 0x01
MASK_E = 0x04
SHIFT_BL = 3
SHIFT_DATA = 4


class LcdApi:
    LCD_CLR = 0x01
    LCD_HOME = 0x02
    LCD_ENTRY_MODE = 0x04
    LCD_ENTRY_INC = 0x02
    LCD_ON_CTRL = 0x08
    LCD_ON_DISPLAY = 0x04
    LCD_FUNCTION = 0x20
    LCD_FUNCTION_2LINES = 0x08
    LCD_FUNCTION_RESET = 0x30
    LCD_DDRAM = 0x80

    def __init__(self, num_lines, num_columns):
        self.num_lines = num_lines
        self.num_columns = num_columns
        self.cursor_x = 0
        self.cursor_y = 0
        self.backlight = True
        self.clear()
        self.hal_write_command(self.LCD_ENTRY_MODE | self.LCD_ENTRY_INC)
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def clear(self):
        self.hal_write_command(self.LCD_CLR)
        self.cursor_x = 0
        self.cursor_y = 0
        time.sleep_ms(5)

    def move_to(self, col, row):
        self.cursor_x = col
        self.cursor_y = row
        addr = col & 0x3F
        if row:
            addr += 0x40
        self.hal_write_command(self.LCD_DDRAM | addr)

    def putstr(self, text):
        for ch in text:
            if self.cursor_x >= self.num_columns:
                break
            self.hal_write_data(ord(ch))
            self.cursor_x += 1

    def hal_write_command(self, cmd):
        raise NotImplementedError

    def hal_write_data(self, data):
        raise NotImplementedError


class I2cLcd(LcdApi):
    def __init__(self, i2c, addr, lines=2, cols=16):
        self.i2c = i2c
        self.addr = addr
        self.backlight = True
        self.i2c.writeto(addr, bytes([0]))
        time.sleep_ms(20)
        for delay in (5, 1, 1, 1):
            self._init_nibble(0x30)
            time.sleep_ms(delay)
        self._init_nibble(0x20)
        time.sleep_ms(1)
        LcdApi.__init__(self, lines, cols)
        self.hal_write_command(self.LCD_FUNCTION | self.LCD_FUNCTION_2LINES)

    def _bl(self):
        return (1 << SHIFT_BL) if self.backlight else 0

    def _init_nibble(self, nibble):
        byte = self._bl() | (((nibble >> 4) & 0x0F) << SHIFT_DATA)
        self.i2c.writeto(self.addr, bytes([byte | MASK_E]))
        self.i2c.writeto(self.addr, bytes([byte]))

    def hal_write_command(self, cmd):
        bl = self._bl()
        for nibble in ((cmd >> 4) & 0x0F, cmd & 0x0F):
            byte = bl | (nibble << SHIFT_DATA)
            self.i2c.writeto(self.addr, bytes([byte | MASK_E]))
            self.i2c.writeto(self.addr, bytes([byte]))
        if cmd <= 3:
            time.sleep_ms(5)

    def hal_write_data(self, data):
        bl = self._bl()
        for nibble in ((data >> 4) & 0x0F, data & 0x0F):
            byte = MASK_RS | bl | (nibble << SHIFT_DATA)
            self.i2c.writeto(self.addr, bytes([byte | MASK_E]))
            self.i2c.writeto(self.addr, bytes([byte]))


i2c = I2C(0, scl=Pin(I2C_SCL), sda=Pin(I2C_SDA), freq=I2C_FREQ)
addrs = i2c.scan()
if not addrs:
    time.sleep_ms(100)
    addrs = i2c.scan()
print("I2C:", [hex(a) for a in addrs])

if not addrs:
    print("ERROR: no I2C device at 0x27")
    print("Check: LCD VCC=5V, GND, SDA=21, SCL=22")
    print("If you just deployed, run:")
    print("  mpremote connect COM7 soft-reset run debug_lcd.py")
    raise SystemExit

addr = LCD_ADDR if LCD_ADDR in addrs else addrs[0]
lcd = I2cLcd(i2c, addr)
lcd.move_to(0, 0)
lcd.putstr("Row1: CATAN OK!")
lcd.move_to(0, 1)
lcd.putstr("Row2: working!")
print("done — both rows should show text")
