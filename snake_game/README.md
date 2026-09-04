# 🐍 Snake Game — Enhanced Edition v2

A polished, feature-rich Snake game written in Python using [pygame](https://www.pygame.org/) / [pygame-ce](https://pyga.me/). Grow your snake, dodge obstacles across multiple maps, collect power-ups, beat the high score, and challenge a friend!

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Pygame](https://img.shields.io/badge/pygame-required-green)

---

## ✨ Features

### 🎮 Core
- Smooth grid-based movement on a 600×400 playfield
- Arrow keys **and** WASD controls for player 1
- Pause / resume / restart from any state
- Persistent high score saved to `highscore.txt`

### 🪟 Particle Effects
- Colorful bursts when eating food (8-12 particles)
- Big golden burst when eating bonus food (20-25 particles)
- Dramatic red burst on game over (30 particles)
- Alpha fading and shrink-while-aging for clean visual feel
- All particles are pre-culled every frame so they never leak

### ⚡ Power-Ups (spawn occasionally after score ≥ 5)
| Icon | Name | Effect | Duration | Min score |
|------|------|--------|----------|-----------|
| 🍒 | **Cherry** | Halves game speed | 6 s | 8 |
| ❄ | **Ice** | Obstacles become non-lethal | 5 s | 12 |
| ★ | **Star** | Doubles points for food & bonus | 8 s | 5 |
| ♥ | **Heart** | Grants 1 extra life (consumed on crash) | one-time | 15 |

Each effect has its own icon and timer bar in the HUD. Star makes both normal (1→2) and bonus (3→6) food worth more. Ice visibly tints obstacles blue. Heart flash makes the snake flash white for 1.5s of invulnerability.

### 🔊 Sound Effects (procedurally generated — no asset files needed)
- Eat / bonus / game over / menu / **power-up collect** / **power-up end** / **extra life**
- Sound toggleable in **Options**

### ⚡ Increasing Difficulty
- Speed starts at **10 FPS** and ramps up with each point you eat
- Capped at **25 FPS** so it always stays playable
- Current speed is shown on the HUD

### 🗺️ Multiple Levels / Maps
When **Obstacles** is enabled, you can choose from 6 pre-defined maps:

| Map | Description |
|---|---|
| **Open Field** | No obstacles (default) |
| **Border Frame** | Thick obstacle border around the playfield |
| **Crossroads** | Horizontal + vertical walls with central gap |
| **Maze Lite** | Symmetric maze with corridors |
| **Quadrants** | Four obstacle islands in the corners |
| **Spiral** | Concentric rectangular rings |

All levels carve out a safe spawn area so you don't insta-die.

### 🌀 Wrap-Around Mode (toggle in Options)
- When **ON**, the snake passes through walls and appears on the opposite side

### 🎨 Four Color Schemes (selectable in Options)
- **Classic** — green snake, red food, black background
- **Neon** — vibrant cyberpunk colors
- **Retro** — old-school monochrome green
- **Dark** — soft muted tones

### 👥 Two-Player Mode (toggle in Options)
- Player 1: arrow keys / WASD
- Player 2: `I J K L`
- Cross-collision kills the snake that hit the other
- Power-ups apply to both players' effects

### 📊 Pause-Screen Stats
While paused you can see:
- Current score and high score
- Time played (seconds)
- Food eaten, bonus food eaten
- Current snake length
- Current effective speed (FPS) including slow effect
- **Extra lives remaining**

### 🏆 Game-Over Screen
Shows your final score, high score, time played, food counts, max snake length, and a "★ NEW HIGH SCORE ★" banner when you break the record.

---

## 📦 Installation

### 1. Prerequisites
- Python **3.8 or newer**
- `pip` (bundled with Python)

### 2. Install pygame
```bash
pip install pygame          # standard
# OR (if you're on Python 3.13+ and the build fails)
pip install pygame-ce       # community edition with pre-built wheels
```

### 3. Run the game
```bash
cd snake_game
python snake_game.py
```

---

## 🕹️ Controls

| Action                          | Key                                                |
|---------------------------------|----------------------------------------------------|
| Start the game                  | `Enter` / `Space`                                  |
| Open / close **Options** menu   | `O`                                                |
| Move (P1)                       | Arrow keys **or** `W A S D`                        |
| Move (P2, only in 2P mode)      | `I` `J` `K` `L`                                    |
| Pause / resume                  | `P` / `Space` (while paused)                       |
| Restart                         | `R` (from pause or game over)                      |
| Back to main menu               | `M` (from pause or game over)                      |
| Quit                            | `Q` / `Esc` / close window                         |

In the **Options** menu:
- `↑` / `↓` — move selection
- `←` / `→` / `Space` — change value
- `O` / `Esc` / `Enter` — return to main menu

---

## 🎯 Objective
- Eat red food to grow longer and gain **1 point** (2 if ★ Star active).
- Catch the pulsing **gold bonus food** when it appears for **3 points** (6 if Star active).
- Grab power-ups: 🍒 slows time, ❄ freezes obstacles, ★ doubles points, ♥ grants an extra life.
- Survive as long as possible — every 4 points roughly your snake speeds up another notch.
- Beat your high score; the best is remembered between sessions.

---

## 🗂️ Project Structure

```
snake_game/
├── snake_game.py     # The game (run this)
├── prompt.txt        # Original development spec
├── prompt_v2.md      # v2 feature spec (particles + power-ups + levels)
├── README.md         # This file
├── highscore.txt     # Created automatically when you score
└── settings.txt      # Created automatically when you change options
```

---

## ⚙️ Configuration

Tweak the constants at the top of `snake_game.py`:

| Constant            | Default | Description                                      |
|---------------------|---------|--------------------------------------------------|
| `CELL_SIZE`         | `20`    | Pixel size of a grid cell                        |
| `GRID_WIDTH`        | `30`    | Cells horizontally                               |
| `GRID_HEIGHT`       | `20`    | Cells vertically                                 |
| `FPS_BASE`          | `10`    | Starting speed                                   |
| `FPS_MAX`           | `25`    | Maximum speed                                    |
| `DIFFICULTY_RAMP`   | `0.25`  | FPS gained per point                             |

You can also:
- Add your own color scheme by appending an entry to `COLOR_SCHEMES` and adding its name to `SCHEME_NAMES`.
- Add your own map by writing a function that returns a `set` of `(x, y)` obstacles and registering it in `LEVELS`.

---

## 🧠 Architecture

- **`SoundManager`** — procedurally synthesizes square/sine wave tones into pygame `Sound` objects; no asset files needed.
- **`Particle` + `ParticleSystem`** — manage alpha-blended circular particles with lifetime, drag, and fade.
- **`PowerUpItem`** — represents a power-up on the field (kind, position, spawn time).
- **`Snake`** — encapsulates a single snake's body, direction, controls, growth queue, life state, and collision immunity timer.
- **`Game`** — owns the screen, fonts, settings, two `Snake` instances, food, obstacles, particles, and power-up state.
- **Persistence** — `load_highscore` / `save_highscore` and `load_settings` / `save_settings` use plain text files.
- **Game loop** — `handle_events()` → `update()` → `draw()` → `clock.tick(effective_fps)`. Frame rate adapts to the difficulty curve *and* the slow power-up.

---

## 🚀 Ideas for More Features
- Background music loop
- AI snake opponent
- Online leaderboard
- Replay system
- Particle trail behind the snake (already scaffolded, just enable)
- Animated background
- Power-up combinations (e.g., Star + Cherry = super slow + double points)

---

## 🧾 Credits

Built with ❤️ using pygame / pygame-ce.
All sound effects synthesized at runtime — no external audio assets required.
All graphics drawn programmatically — no image files needed.

Good luck chasing that high score! 🐍🏆✨