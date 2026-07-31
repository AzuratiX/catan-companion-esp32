import utime
from machine import I2C, Pin, PWM

import config
from i2c_lcd import I2cLcd


class DebouncedButton:
    """Active-LOW button with edge detection."""

    def __init__(self, pin_num, debounce_ms=config.DEBOUNCE_MS):
        self._pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self._debounce_ms = debounce_ms
        self._last_raw = 1
        self._stable = 1
        self._last_change_ms = utime.ticks_ms()
        self._pressed_event = False

    def update(self):
        now = utime.ticks_ms()
        raw = self._pin.value()
        if raw != self._last_raw:
            self._last_raw = raw
            self._last_change_ms = now
        if utime.ticks_diff(now, self._last_change_ms) >= self._debounce_ms:
            if raw != self._stable:
                self._stable = raw
                if raw == 0:
                    self._pressed_event = True

    def was_pressed(self):
        if self._pressed_event:
            self._pressed_event = False
            return True
        return False

    def is_held(self):
        return self._stable == 0


class Leds:
    def __init__(self):
        self.green = Pin(config.LED_GREEN, Pin.OUT, value=0)
        self.yellow = Pin(config.LED_YELLOW, Pin.OUT, value=0)
        self.red = Pin(config.LED_RED, Pin.OUT, value=0)
        self._yellow_on = False

    def all_off(self):
        self.green.off()
        self.yellow.off()
        self.red.off()
        self._yellow_on = False

    def set_turn(self):
        self.all_off()
        self.green.on()

    def set_robber(self):
        self.all_off()
        self.red.on()

    def set_timeup(self):
        self.all_off()
        self.red.on()

    def update_low_time_warning(self, remaining_s, now_ms):
        """Flash yellow LED when time is low."""
        if remaining_s <= config.LOW_TIME_WARN_S and remaining_s > 0:
            period = 500
            self._yellow_on = (now_ms // period) % 2 == 0
            if self._yellow_on:
                self.yellow.on()
            else:
                self.yellow.off()
            self.green.off()
        elif remaining_s > config.LOW_TIME_WARN_S:
            self.yellow.off()
            self.green.on()


class Buzzer:
    def __init__(self):
        self._pwm = PWM(Pin(config.BUZZER_PIN), freq=440, duty=0)

    def _tone(self, freq, duty=512):
        if freq <= 0:
            self._pwm.duty(0)
            return
        self._pwm.freq(freq)
        self._pwm.duty(duty)

    def off(self):
        self._pwm.duty(0)

    def beep(self, freq, duration_ms):
        self._tone(freq)
        utime.sleep_ms(duration_ms)
        self.off()

    def play_roll_tick(self):
        self.beep(config.TONE_ROLL, 30)

    def play_success(self):
        self.beep(config.TONE_SUCCESS, 120)
        utime.sleep_ms(40)
        self.beep(config.TONE_SUCCESS + 220, 120)

    def play_warn(self):
        self.beep(config.TONE_WARN, 60)

    def play_robber_alarm(self):
        for _ in range(4):
            self.beep(config.TONE_ROBBER, 180)
            utime.sleep_ms(80)

    def play_timeup_alarm(self):
        for _ in range(5):
            self.beep(config.TONE_TIMEUP, 200)
            utime.sleep_ms(100)


class Display:
    def __init__(self, lcd):
        self._lcd = lcd

    def show(self, line1, line2=""):
        self._lcd.clear()
        self._lcd.move_to(0, 0)
        self._lcd.putstr((line1 + " " * 16)[:16])
        self._lcd.move_to(0, 1)
        self._lcd.putstr((line2 + " " * 16)[:16])

    def show_line2(self, text):
        self._lcd.move_to(0, 1)
        self._lcd.putstr(" " * 16)
        self._lcd.move_to(0, 1)
        self._lcd.putstr(text[:16])


class Hardware:
    def __init__(self):
        i2c = I2C(0, scl=Pin(config.I2C_SCL), sda=Pin(config.I2C_SDA), freq=config.I2C_FREQ)
        addrs = i2c.scan()
        if not addrs:
            utime.sleep_ms(100)
            addrs = i2c.scan()
        addr = config.LCD_I2C_ADDR
        if addr not in addrs and addrs:
            addr = addrs[0]
        lcd = I2cLcd(i2c, addr, 2, 16)
        self.display = Display(lcd)
        self.btn_main = DebouncedButton(config.BTN_MAIN)
        self.btn_select = DebouncedButton(config.BTN_SELECT)
        self.btn_back = DebouncedButton(config.BTN_BACK)
        self.btn_home = DebouncedButton(config.BTN_HOME)
        self.leds = Leds()
        self.buzzer = Buzzer()

    def poll_buttons(self):
        self.btn_main.update()
        self.btn_select.update()
        self.btn_back.update()
        self.btn_home.update()

    def startup_beep(self):
        self.buzzer.beep(523, 80)
        utime.sleep_ms(40)
        self.buzzer.beep(784, 120)
