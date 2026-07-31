import urandom
import utime

import config


class SetupPhase:
    PLAYERS = 0
    TIMER = 1


class GamePhase:
    WAIT_ROLL = 0
    DICE_ROLLING = 1
    DICE_RESULT = 2
    ROBBER = 3
    RESOURCE_GATHER = 4
    COUNTDOWN = 5


class CatanGame:
    def __init__(self, hw):
        self.hw = hw
        self.setup_step = SetupPhase.PLAYERS
        self.phase = None
        self.num_players = config.PLAYERS_DEFAULT
        self.turn_timer_s = config.TIMER_DEFAULT_S
        self.round_num = 1
        self.player_num = 1
        self.dice_a = 1
        self.dice_b = 1
        self.remaining_s = 0
        self._phase_start_ms = 0
        self._last_second = -1
        self._last_warn_second = -1
        self._roll_end_ms = 0
        self._roll_next_flash_ms = 0
        self._display_dirty = True
        self._line1 = ""
        self._line2 = ""
        self.in_setup = True

    def start(self):
        self.in_setup = True
        self.setup_step = SetupPhase.PLAYERS
        self._mark_display_dirty()
        self.hw.leds.all_off()
        self.hw.display.show("CATAN Companion", "Setup...")

    def update(self):
        self.hw.poll_buttons()
        if self.hw.btn_home.was_pressed():
            self._go_home()
        elif self.in_setup:
            self._update_setup()
        else:
            self._update_game()

        if self._display_dirty:
            self.hw.display.show(self._line1, self._line2)
            self._display_dirty = False

    def _mark_display_dirty(self):
        self._display_dirty = True

    def _set_lines(self, line1, line2=""):
        if line1 != self._line1 or line2 != self._line2:
            self._line1 = line1
            self._line2 = line2
            self._mark_display_dirty()

    def _drain_buttons(self):
        """Discard queued presses (e.g. during resource gather)."""
        self.hw.btn_main.was_pressed()
        self.hw.btn_select.was_pressed()
        self.hw.btn_back.was_pressed()

    def _go_home(self):
        """Force restart to setup from any game state."""
        self.in_setup = True
        self.setup_step = SetupPhase.PLAYERS
        self.phase = None
        self.num_players = config.PLAYERS_DEFAULT
        self.turn_timer_s = config.TIMER_DEFAULT_S
        self.round_num = 1
        self.player_num = 1
        self.remaining_s = 0
        self._last_second = -1
        self._last_warn_second = -1
        self.hw.leds.all_off()
        self.hw.buzzer.off()
        self._drain_buttons()
        self._set_lines("Players: %d" % self.num_players, "SEL chg MAIN nxt")

    def _update_setup(self):
        if self.setup_step == SetupPhase.PLAYERS:
            self._set_lines("Players: %d" % self.num_players, "SEL chg MAIN nxt")
            if self.hw.btn_select.was_pressed():
                self.num_players += 1
                if self.num_players > config.PLAYERS_MAX:
                    self.num_players = config.PLAYERS_MIN
            if self.hw.btn_back.was_pressed():
                self.num_players -= 1
                if self.num_players < config.PLAYERS_MIN:
                    self.num_players = config.PLAYERS_MAX
            if self.hw.btn_main.was_pressed():
                self.setup_step = SetupPhase.TIMER
                self._mark_display_dirty()
        elif self.setup_step == SetupPhase.TIMER:
            self._set_lines("Timer: %ds" % self.turn_timer_s, "SEL +15 MAIN go")
            if self.hw.btn_select.was_pressed():
                self.turn_timer_s += config.TIMER_STEP_S
                if self.turn_timer_s > config.TIMER_MAX_S:
                    self.turn_timer_s = config.TIMER_MIN_S
            if self.hw.btn_back.was_pressed():
                self.turn_timer_s -= config.TIMER_STEP_S
                if self.turn_timer_s < config.TIMER_MIN_S:
                    self.turn_timer_s = config.TIMER_MAX_S
            if self.hw.btn_main.was_pressed():
                self._begin_game()

    def _begin_game(self):
        self.in_setup = False
        self.round_num = 1
        self.player_num = 1
        self.phase = GamePhase.WAIT_ROLL
        self._phase_start_ms = utime.ticks_ms()
        self.hw.leds.all_off()
        self._enter_wait_roll()

    def _enter_wait_roll(self):
        self.phase = GamePhase.WAIT_ROLL
        self._set_lines(
            "R%d P%d: Roll" % (self.round_num, self.player_num),
            "Press MAIN",
        )
        self.hw.leds.all_off()

    def _update_game(self):
        now = utime.ticks_ms()
        if self.phase == GamePhase.WAIT_ROLL:
            if self.hw.btn_main.was_pressed():
                self._start_dice_roll(now)
        elif self.phase == GamePhase.DICE_ROLLING:
            self._update_dice_roll(now)
        elif self.phase == GamePhase.DICE_RESULT:
            self._update_dice_result(now)
        elif self.phase == GamePhase.ROBBER:
            if self.hw.btn_main.was_pressed():
                self._start_countdown(now)
        elif self.phase == GamePhase.RESOURCE_GATHER:
            self._update_resource_gather(now)
        elif self.phase == GamePhase.COUNTDOWN:
            self._update_countdown(now)

    def _start_dice_roll(self, now):
        self.phase = GamePhase.DICE_ROLLING
        self._phase_start_ms = now
        self._roll_end_ms = utime.ticks_add(now, config.DICE_ROLL_MS)
        self._roll_next_flash_ms = now
        self.dice_a = urandom.randint(1, 6)
        self.dice_b = urandom.randint(1, 6)
        self.hw.leds.all_off()

    def _update_dice_roll(self, now):
        if utime.ticks_diff(now, self._roll_next_flash_ms) >= 0:
            self.dice_a = urandom.randint(1, 6)
            self.dice_b = urandom.randint(1, 6)
            total = self.dice_a + self.dice_b
            self._set_lines(
                "Rolling dice...",
                "%d + %d = %2d" % (self.dice_a, self.dice_b, total),
            )
            self.hw.buzzer.play_roll_tick()
            self._roll_next_flash_ms = utime.ticks_add(now, config.DICE_FLASH_MS)

        if utime.ticks_diff(now, self._roll_end_ms) >= 0:
            self._finish_dice_roll()

    def _finish_dice_roll(self):
        total = self.dice_a + self.dice_b
        self.phase = GamePhase.DICE_RESULT
        self._phase_start_ms = utime.ticks_ms()
        self._set_lines(
            "R%d P%d Dice:%2d" % (self.round_num, self.player_num, total),
            "%d + %d = %2d" % (self.dice_a, self.dice_b, total),
        )
        self._drain_buttons()

    def _update_dice_result(self, now):
        self._drain_buttons()
        elapsed_ms = utime.ticks_diff(now, self._phase_start_ms)
        if elapsed_ms >= config.DICE_RESULT_S * 1000:
            total = self.dice_a + self.dice_b
            self._drain_buttons()
            if total == 7:
                self._enter_robber()
            else:
                self._enter_resource_gather()

    def _enter_robber(self):
        self.phase = GamePhase.ROBBER
        self._phase_start_ms = utime.ticks_ms()
        self.hw.leds.set_robber()
        self._drain_buttons()
        self._set_lines("ROBBER!", "Discard & move")
        self.hw.buzzer.play_robber_alarm()

    def _enter_resource_gather(self):
        self.phase = GamePhase.RESOURCE_GATHER
        self._phase_start_ms = utime.ticks_ms()
        self._last_second = -1
        self.hw.leds.set_turn()
        self._drain_buttons()
        self._set_lines(
            "Resources!",
            "Gather: %2ds" % config.RESOURCE_GATHER_S,
        )

    def _update_resource_gather(self, now):
        self._drain_buttons()
        elapsed_ms = utime.ticks_diff(now, self._phase_start_ms)
        remaining = config.RESOURCE_GATHER_S - (elapsed_ms // 1000)
        if remaining != self._last_second:
            self._last_second = remaining
            if remaining >= 0:
                self._set_lines("Resources!", "Gather: %2ds" % remaining)
        if remaining <= 0:
            self._drain_buttons()
            self._start_countdown(now)

    def _start_countdown(self, now):
        self.phase = GamePhase.COUNTDOWN
        self._phase_start_ms = now
        self.remaining_s = self.turn_timer_s
        self._last_second = self.remaining_s + 1
        self._last_warn_second = -1
        self.hw.leds.set_turn()
        self._drain_buttons()
        self._set_countdown_display()

    def _set_countdown_display(self):
        self._set_lines(
            "R%d P%d Turn" % (self.round_num, self.player_num),
            "Time: %3ds" % self.remaining_s,
        )

    def _update_countdown(self, now):
        elapsed_ms = utime.ticks_diff(now, self._phase_start_ms)
        new_remaining = self.turn_timer_s - (elapsed_ms // 1000)
        if new_remaining != self._last_second:
            self._last_second = new_remaining
            self.remaining_s = max(new_remaining, 0)
            self._set_countdown_display()

            if 0 < self.remaining_s <= config.LOW_TIME_WARN_S:
                if self.remaining_s != self._last_warn_second:
                    self._last_warn_second = self.remaining_s
                    self.hw.buzzer.play_warn()

        self.hw.leds.update_low_time_warning(self.remaining_s, utime.ticks_ms())

        if self.hw.btn_back.was_pressed():
            self._phase_start_ms = utime.ticks_sub(self._phase_start_ms, 30000)
            self.remaining_s = min(self.remaining_s + 30, config.TIMER_MAX_S)
            self._last_second = self.remaining_s + 1
            self._set_countdown_display()

        if self.hw.btn_main.was_pressed():
            self.hw.buzzer.play_success()
            self._pass_turn()
            return

        if self.remaining_s <= 0:
            self.hw.leds.set_timeup()
            self._set_lines(
                "R%d P%d TIME UP!" % (self.round_num, self.player_num),
                "Passing turn...",
            )
            self.hw.buzzer.play_timeup_alarm()
            self._pass_turn()

    def _pass_turn(self):
        self.player_num += 1
        if self.player_num > self.num_players:
            self.player_num = 1
            self.round_num += 1
        self._enter_wait_roll()
