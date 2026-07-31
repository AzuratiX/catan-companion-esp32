"""Hardware diagnostic for PCF8574 LCD backpack.

Run:
  mpremote connect COM7 run debug_hw.py

Watch the LCD and note what changes for each step.
"""

import time
from machine import I2C, Pin, SoftI2C

SDA = 21
SCL = 22
ADDR = 0x27


def scan(i2c):
    addrs = i2c.scan()
    print("I2C scan:", [hex(a) for a in addrs])
    return addrs


def blink_backlight(i2c, addr):
    print("\n[1] Backlight blink (5x) — backlight should flash on/off")
    for n in range(5):
        i2c.writeto(addr, bytes([0x08]))  # bit3 = backlight on most backpacks
        time.sleep_ms(400)
        i2c.writeto(addr, bytes([0x00]))
        time.sleep_ms(400)
    print("    done step 1")


def try_bl_bits(i2c, addr):
    print("\n[2] Trying backlight on each bit 0-7")
    for bit in range(8):
        val = 1 << bit
        print("    bit", bit, "val", hex(val))
        i2c.writeto(addr, bytes([val]))
        time.sleep_ms(800)
    i2c.writeto(addr, bytes([0x00]))


def port_sweep(i2c, addr):
    print("\n[3] Port sweep 0x00-0xFF — watch for ANY display change")
    for val in range(0, 256, 17):
        i2c.writeto(addr, bytes([val]))
        time.sleep_ms(120)
    i2c.writeto(addr, bytes([0x00]))
    print("    done step 3")


def slow_init_std(i2c, addr):
    print("\n[4] Slow init + 'HI' text (standard map, long EN pulse)")

    def pulse(byte, us=500):
        i2c.writeto(addr, bytes([byte | 0x04]))  # EN high
        time.sleep_us(us)
        i2c.writeto(addr, bytes([byte & ~0x04]))  # EN low
        time.sleep_ms(2)

    def nibble(n, rs):
        byte = 0x08 | (n << 4)  # backlight + data on P4-P7
        if rs:
            byte |= 0x01
        pulse(byte)

    def cmd(c):
        pulse(0x08 | ((c >> 4) << 4))
        pulse(0x08 | ((c & 0x0F) << 4))
        time.sleep_ms(5)

    def dat(c):
        hi = 0x09 | ((c >> 4) << 4)
        lo = 0x09 | ((c & 0x0F) << 4)
        pulse(hi)
        pulse(lo)

    i2c.writeto(addr, bytes([0x00]))
    time.sleep_ms(100)
    for _ in range(3):
        nibble(3, rs=0)
        time.sleep_ms(10)
    nibble(2, rs=0)
    time.sleep_ms(10)
    cmd(0x28)
    cmd(0x0C)
    cmd(0x06)
    cmd(0x01)
    time.sleep_ms(10)
    cmd(0x80)
    for ch in "Row1: HI":
        dat(ord(ch))
    cmd(0xC0)
    for ch in "Row2: OK":
        dat(ord(ch))
    print("    done step 4")


def power_only_instructions():
    print("\n" + "=" * 50)
    print("POWER-ONLY TEST (no ESP32 data wires needed)")
    print("=" * 50)
    print("1. Unplug ESP32 completely")
    print("2. Connect ONLY: LCD GND->GND, LCD VCC->5V")
    print("3. Adjust blue pot slowly")
    print("   NORMAL: blocks on ROW 1 ONLY (row 2 blank)")
    print("   BAD:    both rows blocks at all settings -> LCD/backpack fault")
    print("   BAD:    completely blank at all settings -> contrast path broken")


print("=== LCD hardware diagnostic ===")
i2c = I2C(0, scl=Pin(SCL), sda=Pin(SDA), freq=50000)
addrs = scan(i2c)
if not addrs:
    print("ERROR: no I2C devices. Check SDA=21, SCL=22, power, USB cable.")
    raise SystemExit

addr = ADDR if ADDR in addrs else addrs[0]
print("Using address", hex(addr))

blink_backlight(i2c, addr)
try_bl_bits(i2c, addr)
port_sweep(i2c, addr)
slow_init_std(i2c, addr)
power_only_instructions()
print("\nAll steps done.")

print("\nAlso trying SoftI2C at 10kHz...")
si2c = SoftI2C(scl=Pin(SCL), sda=Pin(SDA), freq=10000)
scan(si2c)
blink_backlight(si2c, addr)
