# Photo gallery

Screenshots and build photos for the CATAN ESP32 Companion Box.

---

## 1. Full breadboard setup

*Whole wiring — ESP32, LCD, buttons, LEDs, buzzer.*

![Full breadboard setup](photos/01-fullbread.jpg)

<!-- Paste or save as: docs/photos/00-breadboard-full.jpg -->

---

## 2. Game states

### Starting

*Boot screen: "CATAN Companion" / "Starting..." or "Setup..."*

![Starting screen](photos/02-starting.jpg)

---

### Main — player count

*Setup: "Players: X" / "SEL chg MAIN nxt"*

![Player count setup (Default)](photos/03-1-mainplyrcount.jpg)
![Player count setup (Editted)](photos/03-mainplyrcount.jpg)

---

### Timer setup

*Setup: "Timer: XXs" / "SEL +15 MAIN go"*

![Timer setup (Default)](photos/04-2-timersetup.jpg)
![Timer setup (Add)](photos/04-1-timersetup.jpg)
![Timer setup (Sub)](photos/04-3-timersetup.jpg)

---

### Round N, Player N — wait for roll

*"R# P#: Roll" / "Press MAIN"*

![Wait for roll](photos/07-roundn.jpg)

---

### Dice sequence

#### Rolling animation

*"Rolling dice..." with changing numbers*

![Dice rolling](photos/05-diceani.jpg)

#### Result — dice total **7** (robber)

*Shows final dice, then robber flow — red LED*

![Dice result seven](photos/12-dice7.jpg)

![Robber screen](photos/13-robber.jpg)

#### Result — dice total **not 7**

*Shows final dice, then resource path — green LED*

![Dice result not seven](photos/05-1-dice.jpg)

---

### Resource gather

*"Resources!" / "Gather: Xs" (8 second countdown)*

![Resource gather](photos/06-resource.jpg)

---

### Player turn timer

#### Normal countdown

*"R# P# Turn" / "Time: XXs" — green LED on*

![Timer normal](photos/09-timerstart.jpg)

#### Low time warning

*≤10 s remaining — yellow LED flashing, warning beeps*

![Timer warning](photos/10-timeryellow.jpg)

#### Time finished

*Timer hit ≤1 s — red LED, time-up alarm*

![Timer finished](photos/11-timerfinish.jpg)

---
