# Workflow & block diagrams

## System block diagram

High-level view of hardware and firmware layers.

```mermaid
flowchart TB
    subgraph Inputs
        B1[MAIN GPIO13]
        B2[SELECT GPIO14]
        B3[BACK GPIO12]
        B4[HOME GPIO32]
    end

    subgraph MCU["ESP32 NodeMCU-32S"]
        MP[MicroPython]
        MAIN[main.py loop]
        GAME[game.py state machine]
        HW[hardware.py]
        MAIN --> GAME
        GAME --> HW
        MP --> MAIN
    end

    subgraph Outputs
        LCD["16x2 LCD via I2C PCF8574 GPIO21/22"]
        LG[Green LED GPIO25]
        LY[Yellow LED GPIO26]
        LR[Red LED GPIO27]
        BZ[Buzzer PWM GPIO18]
    end

    B1 & B2 & B3 & B4 --> HW
    HW --> LCD & LG & LY & LR & BZ
```

---

## Game state machine

HOME can jump to **Setup (Players)** from any state (not drawn on every edge for clarity).

```mermaid
stateDiagram-v2
    direction TB

    [*] --> SetupPlayers

    state Setup {
        SetupPlayers --> SetupTimer: MAIN
        SetupTimer --> WaitRoll: MAIN
    }

    WaitRoll --> DiceRolling: MAIN
    DiceRolling --> DiceResult: animation done
    DiceResult --> Robber: total == 7
    DiceResult --> ResourceGather: total != 7

    Robber --> TurnCountdown: MAIN confirm
    ResourceGather --> TurnCountdown: 8 s elapsed

    TurnCountdown --> WaitRoll: MAIN early OR time == 0
    WaitRoll --> WaitRoll: next player / round++

    Setup --> SetupPlayers: HOME
    WaitRoll --> SetupPlayers: HOME
    DiceRolling --> SetupPlayers: HOME
    DiceResult --> SetupPlayers: HOME
    Robber --> SetupPlayers: HOME
    ResourceGather --> SetupPlayers: HOME
    TurnCountdown --> SetupPlayers: HOME
```

---

## Turn sequence (one player)

```mermaid
flowchart LR
    A["Wait roll\nR# P# Press MAIN"] --> B["Dice animation\n~1.8 s flash"]
    B --> C["Show result\n3 s hold"]
    C --> D{Total?}
    D -->|7| E["ROBBER\nRed LED + alarm"]
    D -->|not 7| F["Resources\n8 s gather"]
    E --> G["Turn timer\nGreen / Yellow warn"]
    F --> G
    G --> H["Next player"]
    H --> A
```

---

## Software loop (non-blocking)

```mermaid
flowchart TD
    START([Boot main.py]) --> INIT[Init Hardware + Game]
    INIT --> LOOP{Every 10 ms}
    LOOP --> POLL[Poll buttons]
    POLL --> HOME{HOME pressed?}
    HOME -->|yes| RESET[Go to setup defaults]
    HOME -->|no| PHASE{in_setup?}
    PHASE -->|yes| SETUP[Update setup screens]
    PHASE -->|no| GAME[Update game phase]
    SETUP --> DISP
    GAME --> DISP
    RESET --> DISP[Refresh LCD if changed]
    DISP --> LOOP
```

---

## Phase timing summary

| Phase | Duration | Buttons active |
|-------|----------|----------------|
| Dice rolling | ~1.8 s | HOME only |
| Dice result | 3 s | HOME only |
| Robber | Until MAIN | MAIN, HOME |
| Resource gather | 8 s | HOME only |
| Turn countdown | Configured timer | MAIN, BACK, HOME |

---

## LED & buzzer mapping

```mermaid
flowchart LR
    subgraph Phases
        P1[Wait / Resources / Turn]
        P2[Turn ≤10 s]
        P3[Robber]
        P4[Time up]
    end

    P1 --> G[Green ON]
    P2 --> Y[Yellow flash + warn beep]
    P3 --> R[Red ON + robber alarm]
    P4 --> R2[Red ON + time-up alarm]
```

Dice roll ticks use short buzzer pulses during animation only.
