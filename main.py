"""
CATAN ESP32 MicroPython Companion Box
Handheld game assistant for 3-6 player CATAN sessions.
"""

import utime

from hardware import Hardware
from game import CatanGame


def main():
    hw = Hardware()
    game = CatanGame(hw)

    hw.display.show("CATAN Companion", "Starting...")
    hw.startup_beep()
    utime.sleep_ms(400)
    game.start()

    while True:
        game.update()
        utime.sleep_ms(10)


if __name__ == "__main__":
    main()
